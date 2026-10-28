"""Spelling and orthography normalisation (BOM-15).

``corpus.spelling_normalization`` registers two regimes:

``pre_1700: morphadorner_emod_lexicon``
    MorphAdorner 2.0.1's Early Modern English adorner (Northwestern University, NCSA-style
    licence), run as distributed by ``ocr_fix.morphadorner``: parts of speech tagged first,
    then each word's standard spelling (``vnto`` -> ``unto``, ``loue`` -> ``love``, and ``ye``
    -> ``the`` or ``you`` by its part of speech). Its standard spellings are put back into the
    original text token by token, so lines and paragraphs survive.
``post_1780: artifacts_only``
    Typographic artifacts only -- the long s and printers' ligatures -- with no lexical
    modernisation: ``publick`` and ``shew`` stay as printed.

The registration is silent on 1700-1779 (TCP's ECCO and Evans texts, the early modern
reference for dating). They get ``artifacts_only``, the reading that changes least, and the
choice is registered by Amendment 6 (``spelling_normalization.range_1700_1779``).

An earlier version applied MorphAdorner's merged spelling-pairs table token by token without
tagging. That is not what MorphAdorner does, and it got the part-of-speech-dependent forms wrong
(``part`` -> ``partly`` for about a million nouns); its outputs are kept under
``data/corpus/normalized_superseded_table/`` and ``normalization_table_superseded.parquet``.
Every replacement is counted, and the map of what was actually applied is published
(``data/normalization/``).

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
from ocr_fix import morphadorner

CATALOG = Path("data/catalog/catalog.parquet")
OUT_DIR = Path("data/corpus/normalized")
STATS = Path("data/normalization/normalization.parquet")
COUNTS = Path("data/normalization/applied_counts.jsonl")
MAP = Path("data/normalization/applied_map.tsv")

LIGATURES = {
    "ſ": "s", "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st",
}  # fmt: skip
_LIG = re.compile("|".join(map(re.escape, LIGATURES)))


def artifacts(text: str) -> tuple[str, int]:
    n = 0

    def sub(m: re.Match) -> str:
        nonlocal n
        n += 1
        return LIGATURES[m.group(0)]

    return _LIG.sub(sub, text), n


def regime(year: int | None, cfg: dict) -> str:
    """Which registered regime applies to a text printed in ``year``."""
    sn = cfg["corpus"]["spelling_normalization"]
    if year is not None and year < 1700:
        return sn["pre_1700"]
    return sn["post_1780"]  # 1700-1779 and undated: artifacts only (Amendment 6)


def normalize(
    text: str, mode: str, adorned: list[tuple[str, str]] | None = None
) -> tuple[str, dict]:
    """``adorned`` is MorphAdorner's (token, standard) list, required for the pre-1700 regime."""
    applied: Counter = Counter()
    unaligned = 0
    if mode == "morphadorner_emod_lexicon":
        if adorned is None:
            raise ValueError("pre-1700 text needs MorphAdorner output (ocr_fix.morphadorner)")
        keep = frozenset(
            load_config()["corpus"]["spelling_normalization"]["morphadorner_keep_printed"]
        )
        text, applied, unaligned = morphadorner.rebuild(text, adorned, keep)
    elif mode != "artifacts_only":
        raise ValueError(f"unregistered spelling regime: {mode}")
    text, n_art = artifacts(text)
    return text, {"artifacts": n_art, "standardized": sum(applied.values()),
                  "unaligned": unaligned, "applied": applied}  # fmt: skip


def _input_path(row: dict) -> Path:
    if row["source"] in cleaner.SKIP_SOURCES:  # keyed text was never cleaned
        return Path(row["text_path"])
    return cleaner.out_path(row)


def norm_path(row: dict) -> Path:
    """Where a catalog row's normalised text lives (mirrors the cleaned tree)."""
    return OUT_DIR / cleaner.out_path(row).relative_to(cleaner.OUT_DIR)


def _one(job: tuple[dict, str]) -> dict:
    row, mode = job
    src = _input_path(row)
    dst = norm_path(row)
    adorned = None
    if mode == "morphadorner_emod_lexicon":
        adorned = morphadorner.read_adorned(morphadorner.adorned_path(row))
    text, stats = normalize(src.read_text(encoding="utf-8", errors="replace"), mode, adorned)
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
        "unaligned": stats["unaligned"],
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
        ("unaligned", pa.int64()),
    ]
)


def _write(rows: list[dict]) -> None:
    STATS.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(
        [{k: r.get(k, 0) for k in SCHEMA.names} for r in rows], schema=SCHEMA
    )
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
    pre = cfg["corpus"]["spelling_normalization"]["pre_1700"]
    unadorned = [r for r, m in todo if m == pre and not morphadorner.adorned_path(r).exists()]
    if unadorned:
        raise SystemExit(f"{len(unadorned):,} pre-1700 texts not adorned yet "
                         "(run ocr_fix.morphadorner adorn first)")  # fmt: skip
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
