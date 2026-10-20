"""One catalog row per work, merged from every source (BOM-12).

Each ingest wrote its own catalog in its own shape. This folds them into a single table with
common columns, normalizes authors and dates, and records which text file on disk each row
points at. Deduplication, genre tagging and author aggregation run on top of it.

Analytic values come from ``config/preregistered.yaml``; nothing here hard-codes one.

Usage::

    python -m metadata.catalog merge                 # -> data/catalog/catalog.parquet
    python -m metadata.catalog merge --limit 1000    # a sample, for checking the mapping
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import unicodedata
from collections.abc import Iterator
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import sha256_of_config

CATALOG_DIR = Path("data/catalog")
CORPUS = Path("data/corpus")
OUT = CATALOG_DIR / "catalog.parquet"

# source -> (catalog file, directory holding the text, how a row names its text file)
SOURCES = {
    "institutional_books": (
        CATALOG_DIR / "institutional_books.jsonl",
        CORPUS / "institutional_books/text_gen",
    ),
    "internet_archive": (
        CATALOG_DIR / "internet_archive.jsonl.gz",
        CORPUS / "internet_archive/text",
    ),
    "tcp": (CATALOG_DIR / "tcp.jsonl", CORPUS / "tcp/text"),
    "chronicling_america": (
        CATALOG_DIR / "chronicling_america.jsonl.gz",
        CORPUS / "chronicling_america/text",
    ),
}

# Sources whose whole point is to sit outside the 1780-1830 window.
DATE_EXEMPT = {"tcp"}

SCHEMA = pa.schema(
    [
        ("work_id", pa.string()),  # source-prefixed, unique across the corpus
        ("source", pa.string()),
        ("source_id", pa.string()),  # the identifier in its own catalog
        ("title", pa.string()),
        ("title_norm", pa.string()),  # for matching: lowercased, punctuation stripped
        ("author", pa.string()),
        ("author_norm", pa.string()),  # "surname, forename" lowercased, initials collapsed
        ("year", pa.int32()),  # publication year, None when unparseable
        ("date_raw", pa.string()),
        ("language", pa.string()),
        ("genre_src", pa.string()),  # the source's own genre words, if any; BOM-18 assigns ours
        ("text_path", pa.string()),  # relative to the repo root; None when not on disk
        ("has_text", pa.bool_()),
    ]
)

_PUNCT = re.compile(r"[^\w\s]|_")
_WS = re.compile(r"\s+")
_YEAR = re.compile(r"(?<!\d)(1[4-9]\d{2})(?!\d)")


def norm_text(value: object) -> str:
    """Lowercase, strip accents and punctuation, collapse whitespace."""
    s = "" if value is None else str(value)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return _WS.sub(" ", _PUNCT.sub(" ", s.lower())).strip()


def norm_author(value: object) -> str:
    """A comparable author key: ``surname, forename`` lowercased, initials collapsed.

    Catalogues write the same person a dozen ways -- "Smith, John, 1780-1850", "John Smith",
    "SMITH (John)". Life dates and honorifics are dropped, order is normalised to surname
    first, and initials keep only their letter, so "Smith, J." and "Smith, J" agree while
    "Smith, John" stays distinct from both.
    """
    raw = "" if value is None else str(value)
    # "SMITH (John)" is surname-first like the comma form; rewrite it to one.
    paren = re.match(r"\s*([^(]+?)\s*\(([^)]+)\)\s*$", raw)
    if paren:
        raw = f"{paren.group(1)}, {paren.group(2)}"
    raw = re.sub(r"\b1[0-9]{3}\s*-?\s*(1[0-9]{3})?\b", " ", raw)  # life dates
    raw = re.sub(
        r"\b(sir|rev|dr|mr|mrs|miss|esq|jr|sr|ed|editor|compiler)\b\.?", " ", raw, flags=re.I
    )
    # Whether the source wrote it surname-first must be decided before normalising, because
    # norm_text strips the comma that says so.
    surname_first = "," in raw
    head, _, tail = raw.partition(",")
    if surname_first:
        surname, forenames = norm_text(head), norm_text(tail)
    else:
        parts = norm_text(raw).split()
        if not parts:
            return ""
        surname = parts[-1]
        forenames = " ".join(parts[:-1])
    if not surname:
        return ""
    forenames = " ".join(p[0] if len(p) == 1 else p for p in forenames.split())
    return f"{surname}, {forenames}".strip().rstrip(",")


def parse_year(*values: object) -> int | None:
    """First plausible 1400-1999 year in any of the given values."""
    for v in values:
        if v is None:
            continue
        m = _YEAR.search(str(v))
        if m:
            return int(m.group(1))
    return None


def read_rows(path: Path) -> Iterator[dict]:
    op = gzip.open if path.suffix == ".gz" else open
    with op(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def map_row(source: str, row: dict, text_dir: Path) -> dict | None:
    """One source row -> one catalog row, or None if it carries no usable identifier."""
    if source == "institutional_books":
        sid = str(row.get("barcode_src") or "")
        title, author = row.get("title_src"), row.get("author_src")
        year = parse_year(row.get("date1_src"), row.get("date2_src"))
        lang = row.get("language_gen") or row.get("language_src")
        genre = row.get("genre_or_form_src")
    elif source == "internet_archive":
        sid = str(row.get("identifier") or "")
        title, author = row.get("title"), row.get("creator")
        year = parse_year(row.get("year"), row.get("date"))
        lang, genre = row.get("language"), row.get("collection")
    elif source == "tcp":
        sid = str(row.get("id") or "")
        title, author = row.get("title"), row.get("author")
        year = parse_year(row.get("year"), row.get("date"))
        lang, genre = "eng", row.get("collection")
    elif source == "chronicling_america":
        lccn, date = row.get("lccn"), row.get("date")
        sid = f"{lccn}/{date}-ed{row.get('edition')}-seq{row.get('sequence')}"
        title, author = row.get("title"), None
        year = parse_year(date)
        lang, genre = "eng", "newspaper"
    else:  # pragma: no cover
        raise ValueError(source)

    if not sid:
        return None
    if source == "chronicling_america":
        rel = (
            text_dir
            / f"{row.get('lccn')}"
            / f"{row.get('date')}-ed{row.get('edition')}-seq{row.get('sequence')}.txt"
        )
    else:
        rel = text_dir / f"{sid}.txt"
    exists = rel.exists()
    if isinstance(title, list):
        title = title[0] if title else None
    if isinstance(author, list):
        author = author[0] if author else None
    return {
        "work_id": f"{source}:{sid}",
        "source": source,
        "source_id": sid,
        "title": None if title is None else str(title),
        "title_norm": norm_text(title),
        "author": None if author is None else str(author),
        "author_norm": norm_author(author),
        "year": year,
        "date_raw": str(row.get("date") or row.get("date1_src") or ""),
        "language": None if lang is None else str(lang),
        "genre_src": None if genre is None else str(genre)[:120],
        "text_path": str(rel) if exists else None,
        "has_text": exists,
    }  # fmt: skip


def merge(limit: int | None = None) -> int:
    cfg = load_config()
    lo, hi = cfg["corpus"]["date_range"]
    rows: list[dict] = []
    per_source: dict[str, dict[str, int]] = {}
    for source, (cat, text_dir) in SOURCES.items():
        if not cat.exists():
            print(f"  {source}: no catalog at {cat}, skipped", file=sys.stderr)
            continue
        seen = kept = with_text = 0
        for raw in read_rows(cat):
            seen += 1
            row = map_row(source, raw, text_dir)
            if row is None:
                continue
            # The 1780-1830 window is the *comparison* corpus (pre-registration 4.1). TCP is
            # deliberately outside it: EEBO/Evans/ECCO span 1473-1700 and are the early modern
            # reference for the dating question (5.3). Filtering them to 1780-1830 would throw
            # away 95% of that set and quietly remove the ability to answer Q3 at all.
            if source not in DATE_EXEMPT and row["year"] is not None:
                if not (lo <= row["year"] <= hi):
                    continue
            kept += 1
            with_text += bool(row["has_text"])
            rows.append(row)
            if limit and kept >= limit:
                break
        per_source[source] = {"seen": seen, "kept": kept, "with_text": with_text}
        print(f"  {source:<22} seen {seen:>7,}  kept {kept:>7,}  with text {with_text:>7,}")

    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        table.replace_schema_metadata(
            {"config_sha256": sha256_of_config(), "date_range": f"{lo}-{hi}"}
        ),
        OUT,
    )
    total_text = sum(v["with_text"] for v in per_source.values())
    print(f"\nwrote {len(rows):,} rows to {OUT} ({total_text:,} with text on disk)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--limit", type=int, help="stop after this many kept rows per source")
    a = ap.parse_args(argv)
    if a.cmd == "merge":
        return merge(a.limit)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
