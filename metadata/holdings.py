"""What we hold, and where: one index of every data folder and every candidate source.

Written 2026-11-12 after a miss: Revelation Book 1 (201 pages, 1828-1834) had been fetched whole
in October, but its folder is named for the part then used (``js-1828-1829-revelations``), and a
new fetch was proposed for revelations already on disk. The facts were recorded
(``data/candidates/units.csv`` lists every section, used or set aside), just not anywhere one
would look first. This builds ``docs/holdings.md``: every folder under ``data/private/`` and
``data/corpus/`` with what it holds and the code that reads or writes it, and every candidate
source with how much of it is held, how much is used, and what is set aside and why.
``tests/test_holdings.py`` fails the build when a folder has no entry here.

Usage::

    python -m metadata.holdings     # -> docs/holdings.md (seconds; sizes via du)
"""

# ruff: noqa: E501  (one-line folder descriptions)
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

OUT = Path("docs/holdings.md")
UNITS = Path("data/candidates/units.csv")
SOURCES = Path("data/candidates/sources.json")
ROOTS = ("data/private", "data/corpus")
SKIP = {".git"}

# One line per folder: what is in it. Keep it factual; the code column is found automatically.
DESCRIPTIONS = {
    "data/private/access": "Rick Grunder, *Mormon Parallels* (2014 PDF, 2,307 pp.; BOM-33 access evidence)",
    "data/private/bom": "Joseph Smith Papers: printer's manuscript (468 pp.) and original manuscript (231 pp.) page JSON and per-page records",
    "data/private/candidates": "Joseph Smith Papers transcripts of every candidate source: Revelation Book 1 *whole* (201 pp., revelations 1828-1834), letters, 1832 history, journals, Letterbook 1, 1838-56 history, Cowdery's 1829 Articles; raw page JSON under `raw/<source id>/`",
    "data/private/fidelity": "PDFs of the published studies BOM-57 checks our code against (Burrows 2002, Jockers 2008, Fields 2011, Funai 2010, Evert 2017, ...)",
    "data/private/js_time": "BOM-73 units: Joseph Smith's and other writers' prose by period, 1831-1844 (JSP text)",
    "data/private/manuscript": "hand-checked corrections to the manuscript transcription (BOM-05)",
    "data/private/pan14": "PAN 2014 authorship-verification corpus (zip and extracted), for BOM-57's fidelity check",
    "data/private/replication": "1835 *Doctrine and Covenants* from JSP (BOM-22 replication of Jockers 2008), raw pages and records",
    "data/private/skousen": "Skousen et al., *Uncovering the Original Text of the Book of Mormon* (FARMS 2002) chapter PDFs (BOM-34)",
    "data/private/validation": "BOM-12 hand-validation page and its 300-record sample (excerpts include Harvard text)",
    "data/corpus/advantage": "Advantage Preservation newspaper archives (BOM-41): W. W. Phelps's *Lake Light*, 1827-28",
    "data/corpus/alm": "language-model fine-tunes and their inputs: benchmark, candidates (Amendment 43 weights, encoded inputs), A44/A45",
    "data/corpus/library_bom": "BOM-95: per-episode style vectors of the sealed Book of Mormon chunks and the Phase 1 candidate units (second encoder)",
    "data/corpus/library_pool": "BOM-94 shared pool: 1,000 swept authors' training words and the 200 known books' test chunks (`plan.json.gz`), per-model scores",
    "data/corpus/list_size": "Amendment 58 list-size test: the 55 tested authors' blocks, 1,070 tests and imposter pools (`pool.pkl`), per-author older-method results",
    "data/corpus/blind": "the sealed Book of Mormon and decoy test set (`sealed.jsonl`) and sweep distances",
    "data/corpus/candidates": "Book of Mormon quotations found in candidate samples (Amendment 43 masking input)",
    "data/corpus/chronicling_america": "Chronicling America newspaper pages 1780-1830 (159,146 pages; OCR text)",
    "data/corpus/cleaned": "OCR-cleaned text of the whole corpus (ocr_fix.clean)",
    "data/corpus/dating": "dating-model features and checkpoints (BOM-26)",
    "data/corpus/derived": "derived tables safe to release: benchmark blocks, rare-phrase hits, target n-grams (BOM-44)",
    "data/corpus/grunder": "text extracted from Grunder's *Mormon Parallels* and its code",
    "data/corpus/hathitrust": "HathiTrust volumes, 1780-1830 (researcher agreement; private)",
    "data/corpus/hathitrust_ef": "HathiTrust Extracted Features files",
    "data/corpus/hathitrust_text": "HathiTrust full text, plain",
    "data/corpus/institutional_books": "Harvard Institutional Books 1.0 volumes, 1780-1830 (no redistribution)",
    "data/corpus/internet_archive": "Internet Archive volumes, 1780-1830",
    "data/corpus/js_time": "BOM-73 text: unexposed religious writers and readers of the book, 1831-1844",
    "data/corpus/jsp_images": "Joseph Smith Papers page images of the manuscripts",
    "data/corpus/kjv_mask_eval": "King James masking evaluation outputs",
    "data/corpus/kjv_mask_runs": "King James masking runs over the control corpus (1.55 billion words)",
    "data/corpus/kjv_mask_validate": "King James masking validation samples",
    "data/corpus/logs_archive": "archived long-job logs",
    "data/corpus/morphadorner": "MorphAdorner install and inputs (spelling normalization)",
    "data/corpus/morphadorner_adorned": "MorphAdorner-adorned corpus output",
    "data/corpus/morphadorner_tmp": "MorphAdorner scratch",
    "data/corpus/normalized": "spelling-normalized corpus text (ocr_fix.normalize)",
    "data/corpus/normalized_superseded_table": "superseded normalization table run, kept (never delete)",
    "data/corpus/nyshn": "NYS Historic Newspapers: Ontario County repository pulls",
    "data/corpus/publish": "staging for Hugging Face releases (model cards, configs)",
    "data/corpus/reuse_runs": "exact-reuse search runs (BOM-23)",
    "data/corpus/semantic": "paraphrase index: 163 million passage embeddings and triage (BOM-25)",
    "data/corpus/sweep": "author sweep index (23,872 authors)",
    "data/corpus/style_embed": "style-encoder data and checkpoints",
    "data/corpus/tcp": "EEBO-TCP early-modern texts 1473-1700 (dating)",
    "data/corpus/timelocked_lm": "time-locked base models (125M, 297M, 590M, 1B attempt): tokenizer, shards, runs",
}


def folders() -> list[str]:
    out = []
    for root in ROOTS:
        r = Path(root)
        if r.is_dir():
            out += [f"{root}/{d.name}" for d in sorted(r.iterdir())
                    if d.is_dir() and d.name not in SKIP]  # fmt: skip
    return out


def _code_refs() -> dict[str, list[str]]:
    py = [p for p in Path(".").rglob("*.py")
          if not str(p).startswith(("data/", ".venv", "tests/"))]  # fmt: skip
    src = {str(p): p.read_text(errors="ignore") for p in py}
    refs: dict[str, list[str]] = {}
    for f in folders():
        base, name = f.split("/")[1:]
        pat = re.compile(rf'{base}/{re.escape(name)}\b|"{base}"\)\s*/\s*"{re.escape(name)}"')
        refs[f] = sorted(p for p, t in src.items() if pat.search(t))
    return refs


def _size(path: str) -> str:
    try:
        r = subprocess.run(["du", "-sh", path], capture_output=True, text=True, timeout=600)
        return r.stdout.split("\t")[0] or "?"
    except (subprocess.TimeoutExpired, OSError):
        return "?"


def sources_table() -> list[str]:
    srcs = {s["id"]: s for s in json.loads(SOURCES.read_text())}
    held: dict[str, int] = defaultdict(int)
    used: dict[str, int] = defaultdict(int)
    aside: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with UNITS.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            w = int(r["words"] or 0)
            held[r["source"]] += w
            if r["sample"] == "excluded":
                aside[r["source"]][r["decision"]] += w
            else:
                used[r["source"]] += w
    rows = ["| Source id | What it is | Written | Words held | Used | Set aside (largest reason) |",
            "| --- | --- | --- | --- | --- | --- |"]  # fmt: skip
    for sid, s in srcs.items():
        a = aside.get(sid, {})
        big = max(a.items(), key=lambda kv: kv[1]) if a else None
        note = f"{sum(a.values()):,} ({big[0]}: {big[1]:,})" if big else "0"
        flag = " **holds far more than is used**" if sum(a.values()) > 2 * used.get(sid, 0) else ""
        rows.append(f"| `{sid}` | {s['title']}{flag} | {s.get('date_written', '')} | "
                    f"{held.get(sid, 0):,} | {used.get(sid, 0):,} | {note} |")  # fmt: skip
    return rows


def build() -> int:
    from datetime import date

    refs = _code_refs()
    missing = [f for f in folders() if f not in DESCRIPTIONS]
    lines = [
        "# What we hold, and where",
        "",
        f"Generated by `python -m metadata.holdings` on {date.today()}; do not edit by hand.",
        "",
        "**Look here before fetching anything.** Then, in order: `data/candidates/units.csv` (every",
        "section of every candidate source, used or set aside, with words and the reason),",
        "`data/candidates/sources.json` (each source's full extent and URL), `data/catalog/catalog.parquet`",
        "(every corpus work), and `data/manifests/` (checksums of every file, public and private).",
        "A folder's name can name only the part first used: `js-1828-1829-revelations` holds the whole",
        "of Revelation Book 1 (revelations through 1834).",
        "",
        "## Candidate and Joseph Smith sources",
        "",
        "Words are whitespace tokens as `ingest.candidate_words` counts them.",
        "",
        *sources_table(),
        "",
        "## Every data folder",
        "",
        "| Folder | Size | What it holds | Code that reads or writes it |",
        "| --- | --- | --- | --- |",
    ]
    for f in folders():
        code = ", ".join(f"`{c}`" for c in refs[f][:4]) or "-"
        lines.append(f"| `{f}/` | {_size(f)} | {DESCRIPTIONS.get(f, '**undescribed**')} | {code} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(folders())} folders, {len(missing)} undescribed -> {OUT}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(build())
