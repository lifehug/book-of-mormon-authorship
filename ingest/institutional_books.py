"""Harvard Institutional Books 1.0: catalog the 1780-1830 English slice and pull its text (BOM-07).

Two steps, because the metadata is public and small while the text is gated and large:

``catalog``
    Downloads the public metadata-only dataset (``institutional/institutional-books-hl-metadata``,
    about 300 MB, 983,004 rows), filters to English volumes dated 1780-1830, and writes
    ``data/catalog/institutional_books.jsonl`` plus a year-by-year summary. No terms acceptance
    needed. Runs anywhere.

``pull``
    Reads the gated full dataset (``institutional/institutional-books-hl``) shard by shard,
    keeps only the barcodes in the catalog, and writes one text file per volume under
    ``data/corpus/institutional_books/text/``. Needs a Hugging Face token whose account has
    accepted the dataset's terms. Resumable. Meant for the data machine.

The dataset's terms forbid redistribution: the text stays on local disk, and only the
catalog and checksum manifest are committed.

Usage::

    python -m ingest.institutional_books catalog
    python -m ingest.institutional_books pull [--limit N]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

META_REPO = "institutional/institutional-books-hl-metadata"
FULL_REPO = "institutional/institutional-books-hl"
CATALOG = Path("data/catalog/institutional_books.jsonl")
SUMMARY = Path("data/catalog/institutional_books_summary.md")
CORPUS = Path("data/corpus/institutional_books")
YEAR_MIN, YEAR_MAX = 1780, 1830
KEEP = [
    "barcode_src", "title_src", "author_src", "date1_src", "date2_src", "date_types_src",
    "page_count_src", "token_count_o200k_base_gen", "language_src", "language_gen",
    "topic_or_subject_src", "topic_or_subject_gen", "genre_or_form_src",
    "ocr_score_src", "ocr_score_gen", "likely_duplicates_barcodes_gen",
    "identifiers_src", "hathitrust_data_ext",
]  # fmt: skip


def hf_token() -> str | None:
    p = Path(os.path.expanduser("~/.config/huggingface/token"))
    return p.read_text().strip() if p.exists() else os.environ.get("HF_TOKEN")


def parse_year(s: str | None) -> int | None:
    """MARC dates: '1812', '181u', '18--', '[1815]'. An int only when all four digits are known."""
    if not s:
        return None
    m = re.search(r"(\d{4})", s)
    return int(m.group(1)) if m else None


def in_window(rec: dict) -> bool:
    y1, y2 = parse_year(rec.get("date1_src")), parse_year(rec.get("date2_src"))
    years = [y for y in (y1, y2) if y]
    if not years:
        return False
    # date1 is the publication date for single-date records; for ranges, use the earliest
    return YEAR_MIN <= min(years) <= YEAR_MAX


def is_english(rec: dict) -> bool:
    return (rec.get("language_gen") or rec.get("language_src")) == "eng"


def catalog(out: Path = CATALOG, summary: Path = SUMMARY) -> int:
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(
        META_REPO, "data/train-00000-of-00001.parquet", repo_type="dataset", token=hf_token(),
        cache_dir=str(CORPUS / "hf-cache"),
    )  # fmt: skip
    pf = pq.ParquetFile(path)
    cols = [c for c in KEEP if c in pf.schema_arrow.names]
    kept: list[dict] = []
    total = 0
    for rg in range(pf.metadata.num_row_groups):
        for rec in pf.read_row_group(rg, columns=cols).to_pylist():
            total += 1
            if is_english(rec) and in_window(rec):
                rec["year"] = min(
                    y for y in (parse_year(rec["date1_src"]), parse_year(rec["date2_src"])) if y
                )
                kept.append(rec)
    kept.sort(key=lambda r: (r["year"], r["barcode_src"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for r in kept:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    summary.write_text(summarize(kept, total), encoding="utf-8")
    print(summary.read_text())
    print(f"wrote {len(kept):,} records to {out}")
    return 0


def summarize(kept: list[dict], total: int) -> str:
    tokens = sum(r.get("token_count_o200k_base_gen") or 0 for r in kept)
    by_year = Counter(r["year"] for r in kept)
    tok_year = Counter()
    for r in kept:
        tok_year[r["year"]] += r.get("token_count_o200k_base_gen") or 0
    dup = sum(1 for r in kept if r.get("likely_duplicates_barcodes_gen"))
    ocr = [r["ocr_score_gen"] for r in kept if r.get("ocr_score_gen") is not None]
    lines = [
        "# Institutional Books 1.0: English volumes dated 1780-1830",
        "",
        f"- Source rows scanned: {total:,}; kept: {len(kept):,}",
        f"- Tokens (o200k_base): {tokens:,} "
        f"(about {tokens * 4.2 / 1e9:.1f} GB of text at ~4.2 bytes per token)",
        f"- Volumes flagged as likely duplicates of another volume: {dup:,}",
        f"- OCR score (generated), median: {sorted(ocr)[len(ocr) // 2] if ocr else 'n/a'}",
        "",
        "Filter: `language_gen` (or `language_src`) is `eng`, and the earliest four-digit year in "
        "`date1_src`/`date2_src` falls in 1780-1830. Records whose dates have placeholder digits "
        "(for example `18uu`) are excluded.",
        "",
        "| Year | Volumes | Tokens |",
        "| --- | --- | --- |",
    ]
    for y in sorted(by_year):
        lines.append(f"| {y} | {by_year[y]:,} | {tok_year[y]:,} |")
    return "\n".join(lines) + "\n"


def pull(limit: int | None, delay: float) -> int:
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    from huggingface_hub import HfApi, HfFileSystem

    tok = hf_token()
    if not tok:
        raise SystemExit("no Hugging Face token at ~/.config/huggingface/token")
    wanted = {json.loads(line)["barcode_src"] for line in CATALOG.open(encoding="utf-8")}
    text_dir = CORPUS / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    done = {p.stem for p in text_dir.glob("*.txt")}
    todo = wanted - done
    print(
        f"catalog: {len(wanted):,} volumes; already on disk: {len(done):,}; to fetch: {len(todo):,}"
    )
    if not todo:
        return 0
    api = HfApi(token=tok)
    shards = sorted(
        f for f in api.list_repo_files(FULL_REPO, repo_type="dataset") if f.endswith(".parquet")
    )
    fs = HfFileSystem(token=tok)
    progress = CORPUS / "pull_progress.json"
    seen_shards = set(json.load(progress.open())) if progress.exists() else set()
    fetched = 0
    text_col = None
    for shard in shards:
        if shard in seen_shards:
            continue
        with fs.open(f"datasets/{FULL_REPO}/{shard}", "rb") as fh:
            pf = pq.ParquetFile(fh)
            if text_col is None:
                names = pf.schema_arrow.names
                text_col = next((n for n in names if "text_by_page" in n), None) or next(
                    n for n in names if n.startswith("text")
                )
                print("text column:", text_col)
            codes = pf.read(columns=["barcode_src"]).column(0).to_pylist()
            hits = [i for i, c in enumerate(codes) if c in todo]
            if hits:
                tbl = pf.read(columns=["barcode_src", text_col])
                mask = pc.is_in(
                    tbl.column("barcode_src"), value_set=__import__("pyarrow").array(list(todo))
                )
                for row in tbl.filter(mask).to_pylist():
                    pages = row[text_col]
                    text = "\n\f\n".join(pages) if isinstance(pages, list) else str(pages)
                    (text_dir / f"{row['barcode_src']}.txt").write_text(text, encoding="utf-8")
                    fetched += 1
                    if limit and fetched >= limit:
                        print(f"stopped at --limit {limit}")
                        return 0
        seen_shards.add(shard)
        json.dump(sorted(seen_shards), progress.open("w"))
        if len(seen_shards) % 100 == 0:
            print(
                f"  shards {len(seen_shards)}/{len(shards)}, volumes fetched {fetched:,}",
                flush=True,
            )
        time.sleep(delay)
    print(f"done: fetched {fetched:,} volumes into {text_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("catalog")
    p = sub.add_parser("pull")
    p.add_argument("--limit", type=int)
    p.add_argument("--delay", type=float, default=0.0)
    a = ap.parse_args(argv)
    return catalog() if a.cmd == "catalog" else pull(a.limit, a.delay)


if __name__ == "__main__":
    sys.exit(main())
