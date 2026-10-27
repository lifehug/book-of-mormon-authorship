"""Book of Mormon text inside the corpus, kept out of every pool (4.2).

Pre-registration 4.2 seals the Book of Mormon from training, tuning, threshold setting and
feature selection until the blind run, and registers a contamination check: drop any volume
holding a Book of Mormon string of ``sealing.contamination_min_tokens`` (12) tokens or more.

The corpus holds copies of it. On 2026-10-27, six catalog rows with text are editions: three
Internet Archive scans of the 1830 printing, a HathiTrust one, a periodical's reprint, and a
modern edition whose catalogue date (1800) puts it inside the 1780-1830 window. Nothing had read
them for any sealed purpose -- they had been labelled by genre, cleaned and hashed -- but the
function-word list, the control pools and the time-locked model's training set are all drawn
from the comparison corpus, so they are listed here and every pool excludes them.

Two layers:

``titles``   rows whose catalogue title names the book (``sealed.json``), a fast first line
``contaminated(text)``  the registered check itself, on a text: True if it shares any 12-token
             string with the 1830 edition. Pools run it on every member, which also catches
             extracts quoted inside other works.

Tokens follow Amendment 2's registered tokenisation (``kjv_mask.align.norm_token``).

Usage::

    python -m metadata.sealed titles      # -> data/catalog/sealed.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

from kjv_mask.align import _WORD, norm_token
from metadata.config import load as load_config
from metadata.config import sha256_of_config

CATALOG = Path("data/catalog/catalog.parquet")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
OUT = Path("data/catalog/sealed.json")
TITLE = re.compile(r"\bbook of mormon\b|\bgolden bible\b", re.IGNORECASE)

_GRAMS: set[int] | None = None


def _tokens(text: str) -> list[str]:
    return [norm_token(m.group(0)) for m in _WORD.finditer(text)]


def _bom_grams(n: int) -> set[int]:
    global _GRAMS
    if _GRAMS is None:
        toks = []
        for line in EDITION.read_text(encoding="utf-8").splitlines():
            toks += _tokens(json.loads(line)["text"])
        _GRAMS = {hash(tuple(toks[i : i + n])) for i in range(len(toks) - n + 1)}
    return _GRAMS


def contaminated(text: str) -> bool:
    """4.2's check: does ``text`` share a string of 12+ tokens with the 1830 edition?

    Hashes stand in for the tuples to keep memory small; a collision can only make the check
    stricter (a false exclusion), never let Book of Mormon text through."""
    n = load_config()["sealing"]["contamination_min_tokens"]
    grams = _bom_grams(n)
    toks = _tokens(text)
    return any(hash(tuple(toks[i : i + n])) in grams for i in range(len(toks) - n + 1))


def titles() -> int:
    rows = pq.read_table(CATALOG, columns=["work_id", "title", "year", "has_text"]).to_pylist()
    hits = [r for r in rows if TITLE.search(r["title"] or "")]
    out = {
        "rule": "catalogue title names the Book of Mormon; see metadata/sealed.py",
        "config_sha256": sha256_of_config(),
        "works": [
            {
                "work_id": r["work_id"],
                "year": r["year"],
                "has_text": r["has_text"],
                "title": (r["title"] or "")[:200],
            }
            for r in hits
        ],  # fmt: skip
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(
        f"{len(hits)} titled works sealed ({sum(r['has_text'] for r in hits)} with text) -> {OUT}"
    )
    return 0


def sealed_ids() -> set[str]:
    return {w["work_id"] for w in json.loads(OUT.read_text())["works"]}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["titles"]:
        return titles()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
