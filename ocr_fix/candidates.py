"""Clean and normalise the printed candidate texts (BOM-14/15 applied to BOM-13's units).

The candidates' printed works are Internet Archive OCR fetched by ``ingest.candidates`` outside
the corpus catalog, so the corpus cleaning pass never saw them. BOM-13 counted them but
assembled sample files only for the Joseph Smith Papers transcripts; rule-10 units (whole
printed works) and rule-11 units (signed items in the two periodical runs, by line range in
``signed_items.json``) have no text of their own yet. This gives them one, put through the
same steps as the corpus: ``ocr_fix.clean`` (headers, hyphens, long s) and the artifact-only
spelling regime (the texts are all after 1780).

Public sources go to ``data/candidates/clean/<unit>.txt``; the two Internet Archive items with
a rights claim go to ``data/private/candidates/clean/`` (see ``data/candidates/SOURCES.md``).
The Joseph Smith Papers samples are transcripts, not OCR, and are not touched here.

Usage::

    python -m ocr_fix.candidates      # writes the cleaned units and lists them
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from ocr_fix.clean import clean
from ocr_fix.normalize import artifacts

UNITS = Path("data/candidates/units.csv")
SIGNED = Path("data/candidates/signed_items.json")
SOURCES = Path("data/candidates/sources.json")
PUBLIC_TEXT = Path("data/candidates/text")
PRIVATE_TEXT = Path("data/private/candidates")
PUBLIC_OUT = Path("data/candidates/clean")
PRIVATE_OUT = Path("data/private/candidates/clean")


def _private() -> set[str]:
    return {s["id"] for s in json.loads(SOURCES.read_text()) if s.get("private")}


def _source_text(source: str, private: set[str]) -> str:
    base = PRIVATE_TEXT if source in private else PUBLIC_TEXT
    return (base / f"{source}.txt").read_text(encoding="utf-8", errors="replace")


def units() -> list[dict]:
    """(unit id, author, sample, period, source, raw text) for every printed unit."""
    private = _private()
    out = []
    for u in csv.DictReader(UNITS.open(encoding="utf-8")):
        if u["author"] and u["decision"].startswith("rule 10"):
            out.append({"unit": u["source"], "author": u["author"], "sample": u["sample"],
                        "period": u["period"], "source": u["source"],
                        "text": _source_text(u["source"], private)})  # fmt: skip
    signers = {}
    for u in csv.DictReader(UNITS.open(encoding="utf-8")):
        if u["decision"].startswith("rule 11"):
            signers[u["source"], u["link_id"]] = u
    for item in json.loads(SIGNED.read_text()):
        if not item["admit"]:
            continue
        lines = _source_text(item["source"], private).split("\n")
        uid = f"{item['source']}:{item['start']}-{item['end']}"
        out.append({"unit": uid, "author": item["signer"], "sample": "printed_by_author",
                    "period": "post1830", "source": item["source"],
                    "text": "\n".join(lines[item["start"] - 1 : item["end"]])})  # fmt: skip
    return out


def build() -> int:
    private = _private()
    n = 0
    for u in units():
        text, _ = clean(u["text"])
        text, _ = artifacts(text)
        out_dir = PRIVATE_OUT if u["source"] in private else PUBLIC_OUT
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{u['unit'].replace(':', '__')}.txt").write_text(text, encoding="utf-8")
        n += 1
    print(f"{n} printed candidate units cleaned -> {PUBLIC_OUT}, {PRIVATE_OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return build()


if __name__ == "__main__":
    sys.exit(main())
