"""Spelling and orthography normalisation (BOM-15).

``corpus.spelling_normalization`` registers two regimes:

``pre_1700: morphadorner_emod_lexicon``
    Early modern spelling mapped to standard forms with MorphAdorner's Early Modern English
    spelling table (``ememergedspellingpairs.tab``, MorphAdorner 2.0.1, Northwestern
    University, NCSA-style licence): ``vnto`` -> ``unto``, ``loue`` -> ``love``.
``post_1780: artifacts_only``
    Typographic artifacts only -- the long s and printers' ligatures -- with no lexical
    modernisation: ``publick`` and ``shew`` stay as printed.

The registration is silent on 1700-1779 (TCP's ECCO and Evans texts, the early modern
reference for dating). They get ``artifacts_only``, the reading that changes least, and the
choice is listed in ``pending_amendment`` (``spelling_normalization.1700_1779``).

The table is applied token by token, case-preserving: the exact token is looked up first, then
its lowercase form, and the replacement takes the original's case pattern (``Loue`` ->
``Love``). Entries that only change case are dropped (case is not spelling), and so are 8 lines
of the distributed file where two pairs run together. Every replacement is counted, and the
map of what was actually applied is published (``data/normalization/``).

Both versions are kept: input text is read, never written; normalised text goes to
``data/corpus/normalized/<source>/``. OCR sources are read from their BOM-14 cleaned text.

Usage::

    python -m ocr_fix.normalize run [--workers N] [--source tcp]   # resumable
    python -m ocr_fix.normalize map                    # -> data/normalization/applied_map.tsv
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import sha256_of_config
from ocr_fix import clean as cleaner

CATALOG = Path("data/catalog/catalog.parquet")
EME_PAIRS = Path("data/corpus/morphadorner/data/ememergedspellingpairs.tab")
OUT_DIR = Path("data/corpus/normalized")
STATS = Path("data/normalization/normalization.parquet")
COUNTS = Path("data/normalization/applied_counts.jsonl")
MAP = Path("data/normalization/applied_map.tsv")

LIGATURES = {
    "ſ": "s", "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st",
}  # fmt: skip
_LIG = re.compile("|".join(map(re.escape, LIGATURES)))
_TOKEN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")

_EME: dict[str, str] | None = None


def load_eme(path: Path = EME_PAIRS) -> dict[str, str]:
    """variant -> standard, from MorphAdorner's table, minus malformed and case-only lines."""
    out = {}
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        a, b = parts[0].strip("﻿"), parts[1]
        if a and b and a.lower() != b.lower():
            out[a] = b
    return out


def _eme() -> dict[str, str]:
    global _EME
    if _EME is None:
        _EME = load_eme()
    return _EME


def artifacts(text: str) -> tuple[str, int]:
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        n += 1
        return LIGATURES[m.group(0)]

    return _LIG.sub(sub, text), n


def _case_like(src: str, word: str) -> str:
    if src.isupper() and len(src) > 1:
        return word.upper()
    if src[:1].isupper():
        return word[:1].upper() + word[1:]
    return word


def standardize(text: str, table: dict[str, str]) -> tuple[str, Counter]:
    applied: Counter = Counter()

    def sub(m: re.Match) -> str:
        tok = m.group(0)
        std = table.get(tok)
        if std is None:
            low = table.get(tok.lower())
            std = None if low is None else _case_like(tok, low)
        if std is None or std == tok:
            return tok
        applied[(tok.lower(), std.lower())] += 1
        return std

    return _TOKEN.sub(sub, text), applied


def regime(year: int | None, cfg: dict) -> str:
    """Which registered regime applies to a text printed in ``year``."""
    sn = cfg["corpus"]["spelling_normalization"]
    if year is not None and year < 1700:
        return sn["pre_1700"]
    return sn["post_1780"]  # 1700-1779 and undated: pending_amendment, artifacts only


def normalize(text: str, mode: str, table: dict[str, str] | None = None) -> tuple[str, dict]:
    text, n_art = artifacts(text)
    applied: Counter = Counter()
    if mode == "morphadorner_emod_lexicon":
        text, applied = standardize(text, _eme() if table is None else table)
    elif mode != "artifacts_only":
        raise ValueError(f"unregistered spelling regime: {mode}")
    return text, {"artifacts": n_art, "standardized": sum(applied.values()), "applied": applied}


def _input_path(row: dict) -> Path:
    if row["source"] in cleaner.SKIP_SOURCES:  # keyed text was never cleaned
        return Path(row["text_path"])
    return cleaner.out_path(row)


def _one(job: tuple[dict, str]) -> dict:
    row, mode = job
    src = _input_path(row)
    dst = OUT_DIR / cleaner.out_path(row).relative_to(cleaner.OUT_DIR)
    text, stats = normalize(src.read_text(encoding="utf-8", errors="replace"), mode)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_name(dst.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(dst)
    return {
        "work_id": row["work_id"],
        "source": row["source"],
        "regime": mode,
        "norm_path": str(dst),
        "artifacts": stats["artifacts"],
        "standardized": stats["standardized"],
        "applied": [[a, b, n] for (a, b), n in stats["applied"].items()],
    }


SCHEMA = pa.schema(
    [
        ("work_id", pa.string()),
        ("source", pa.string()),
        ("regime", pa.string()),
        ("norm_path", pa.string()),
        ("artifacts", pa.int64()),
        ("standardized", pa.int64()),
    ]
)


def _write(rows: list[dict]) -> None:
    STATS.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist([{k: r[k] for k in SCHEMA.names} for r in rows], schema=SCHEMA)
    tmp = STATS.with_suffix(".parquet.tmp")
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), tmp)
    tmp.replace(STATS)


def run(workers: int, limit: int | None, sources: list[str] | None = None) -> int:
    cfg = load_config()
    cols = ["work_id", "source", "text_path", "year"]
    rows = [
        r
        for r in pq.read_table(CATALOG, columns=cols).to_pylist()
        if r["text_path"] and (not sources or r["source"] in sources)
    ]
    done = pq.read_table(STATS).to_pylist() if STATS.exists() else []
    have = {r["work_id"] for r in done}
    todo = [(r, regime(r["year"], cfg)) for r in rows if r["work_id"] not in have]
    missing = [r for r, _ in todo if not _input_path(r).exists()]
    if missing:
        raise SystemExit(f"{len(missing):,} inputs not on disk (run ocr_fix.clean first)")
    todo = todo[:limit] if limit else todo
    print(f"{len(todo):,} to normalise ({len(done):,} done)", flush=True)
    start, n = time.time(), 0
    COUNTS.parent.mkdir(parents=True, exist_ok=True)
    with COUNTS.open("a") as counts, ProcessPoolExecutor(workers) as pool:
        for rec in pool.map(_one, todo, chunksize=16):
            if rec["applied"]:
                counts.write(json.dumps({"work_id": rec["work_id"], "applied": rec["applied"]}))
                counts.write("\n")
            done.append(rec)
            n += 1
            if n % 20000 == 0:
                counts.flush()
                _write(done)
                print(f"  {n:,}/{len(todo):,}  {n / (time.time() - start):.0f} docs/s", flush=True)
    _write(done)
    by = Counter(r["regime"] for r in done)
    print(f"normalised {n:,} in {time.time() - start:.0f}s; by regime {dict(by)}")
    return 0


def build_map() -> int:
    """What was actually applied, variant -> standard with token and text counts."""
    tokens: Counter = Counter()
    texts: Counter = Counter()
    # last record per work: a resumed run may have logged a text twice before a crash
    per_work = {}
    for line in COUNTS.read_text().splitlines():
        rec = json.loads(line)
        per_work[rec["work_id"]] = rec["applied"]
    for applied in per_work.values():
        for a, b, n in applied:
            tokens[(a, b)] += n
            texts[(a, b)] += 1
    with MAP.open("w") as fh:
        fh.write("variant\tstandard\ttokens\ttexts\n")
        for (a, b), n in tokens.most_common():
            fh.write(f"{a}\t{b}\t{n}\t{texts[(a, b)]}\n")
    print(f"{len(tokens):,} distinct mappings applied, {sum(tokens.values()):,} tokens -> {MAP}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--workers", type=int, default=6)
    r.add_argument("--limit", type=int)
    r.add_argument("--source", action="append", help="only these sources (repeatable)")
    sub.add_parser("map")
    a = ap.parse_args(argv)
    return run(a.workers, a.limit, a.source) if a.cmd == "run" else build_map()


if __name__ == "__main__":
    sys.exit(main())
