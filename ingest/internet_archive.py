"""Internet Archive texts printed 1780-1830, English, especially American imprints (BOM-09).

``catalog``
    Pages through the IA scrape API (cursor based) for ``mediatype:texts`` items dated
    1780-1830 in English and writes ``data/catalog/internet_archive.jsonl.gz`` plus a summary
    (counts by year, top collections, likely-OCR count, overlap with the Harvard slice).
    Public, no account. Runs anywhere.

``pull``
    Downloads each item's ``<identifier>_djvu.txt`` OCR into
    ``data/corpus/internet_archive/text/<identifier>.txt``. Resumable, polite (one request
    per ``--delay`` seconds, backoff on 429/503), failures logged to ``failed.txt``.
    ``--skip-harvard-overlap`` skips items whose title and year match a Harvard row.

Usage::

    python -m ingest.internet_archive catalog
    python -m ingest.internet_archive pull [--limit N] [--delay S] [--skip-harvard-overlap]
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

SCRAPE_URL = "https://archive.org/services/search/v1/scrape"
DOWNLOAD_URL = "https://archive.org/download/{id}/{id}_djvu.txt"
QUERY = "mediatype:texts AND date:[1780-01-01 TO 1830-12-31] AND language:(eng OR English)"
FIELDS = (
    "identifier,title,creator,date,year,publisher,language,subject,collection,imagecount,downloads"
)
# Gzipped: the plain JSONL is ~170 MB, over GitHub's 100 MB file limit.
CATALOG = Path("data/catalog/internet_archive.jsonl.gz")
SUMMARY = Path("data/catalog/internet_archive_summary.md")
HARVARD = Path("data/catalog/institutional_books.jsonl")
CORPUS = Path("data/corpus/internet_archive")
USER_AGENT = "bom-authorship-research/0.1 (+https://github.com/lifehug/book-of-mormon-authorship)"
YEAR_MIN, YEAR_MAX = 1780, 1830
# Collections that are not scanned books with OCR text (audio/video/web/data dumps).
NO_OCR_COLLECTIONS = {"etree", "audio", "movies", "podcasts", "web", "tvarchive"}


def fetch(url: str, retries: int = 6) -> bytes:
    """GET with the project User-Agent; exponential backoff on 429/503 and transient errors.
    A 404 raises immediately (the item has no such file)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 403, 401):
                raise
            wait = 15 * 2**attempt if exc.code in (429, 503) else 5 * (attempt + 1)
            ra = exc.headers.get("Retry-After") if exc.headers else None
            if ra and ra.isdigit():
                wait = max(wait, int(ra))
            if attempt == retries - 1:
                raise
            print(f"HTTP {exc.code} for {url}; sleeping {wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            print(f"retry {attempt + 1} for {url}: {exc}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def norm_title(title: str | None) -> str:
    """Lowercase, punctuation stripped, whitespace collapsed, first 60 characters."""
    t = re.sub(r"[^\w\s]|_", " ", (title or "").lower())
    return re.sub(r"\s+", " ", t).strip()[:60].strip()


def parse_year(value: object) -> int | None:
    """First four-digit year in a string or int; None when absent."""
    if value is None:
        return None
    m = re.search(r"(?<!\d)(\d{4})(?!\d)", str(value))
    return int(m.group(1)) if m else None


def first(value: object) -> object:
    """IA fields are sometimes lists; take the first element."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def item_year(rec: dict) -> int | None:
    return parse_year(first(rec.get("year"))) or parse_year(first(rec.get("date")))


def in_window(year: int | None) -> bool:
    return year is not None and YEAR_MIN <= year <= YEAR_MAX


def harvard_keys(path: Path = HARVARD) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()
    if not path.exists():
        return keys
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            y = r.get("year") or parse_year(r.get("date1_src"))
            k = norm_title(r.get("title_src"))
            if k and y:
                keys.add((k, int(y)))
    return keys


def overlaps_harvard(rec: dict, keys: set[tuple[str, int]]) -> bool:
    y = item_year(rec)
    k = norm_title(str(first(rec.get("title")) or ""))
    return bool(k and y and (k, y) in keys)


def likely_has_text(rec: dict) -> bool:
    """Heuristic: scanned books carry an imagecount and are not in a non-text collection."""
    cols = rec.get("collection") or []
    if isinstance(cols, str):
        cols = [cols]
    if NO_OCR_COLLECTIONS & set(cols):
        return False
    return bool(rec.get("imagecount"))


def scrape(delay: float) -> list[dict]:
    rows: list[dict] = []
    cursor = None
    while True:
        params = {"q": QUERY, "fields": FIELDS, "count": "10000"}
        if cursor:
            params["cursor"] = cursor
        url = SCRAPE_URL + "?" + urllib.parse.urlencode(params)
        data = json.loads(fetch(url))
        rows.extend(data.get("items", []))
        print(f"  {len(rows):,}/{data.get('total', '?'):,}", flush=True)
        cursor = data.get("cursor")
        if not cursor:
            return rows
        time.sleep(delay)


def catalog(delay: float = 2.0) -> int:
    raw = scrape(delay)
    keys = harvard_keys()
    seen: set[str] = set()
    recs = []
    for r in raw:
        if r["identifier"] in seen:
            continue
        seen.add(r["identifier"])
        y = item_year(r)
        if not in_window(y):
            continue
        r["year"] = y
        if isinstance(r.get("subject"), list):
            r["subject"] = r["subject"][:8]
        r["has_text_likely"] = likely_has_text(r)
        r["harvard_overlap"] = overlaps_harvard(r, keys)
        recs.append(r)
    recs.sort(key=lambda r: (r["year"], r["identifier"]))
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(CATALOG, "wt", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    SUMMARY.write_text(summarize(recs, len(raw), len(keys)), encoding="utf-8")
    print(SUMMARY.read_text())
    print(f"wrote {len(recs):,} records to {CATALOG}")
    return 0


def summarize(recs: list[dict], scraped: int, harvard_rows: int) -> str:
    by_year = Counter(r["year"] for r in recs)
    cols = Counter()
    for r in recs:
        c = r.get("collection") or []
        cols.update([c] if isinstance(c, str) else c)
    text = sum(1 for r in recs if r["has_text_likely"])
    over = sum(1 for r in recs if r["harvard_overlap"])
    new_text = sum(1 for r in recs if r["has_text_likely"] and not r["harvard_overlap"])
    images = sum(r.get("imagecount") or 0 for r in recs if not r["harvard_overlap"])
    lines = [
        "# Internet Archive: English texts dated 1780-1830",
        "",
        f"- Query: `{QUERY}`",
        f"- Scraped: {scraped:,}; kept (unique, year in window): {len(recs):,}",
        f"- Likely to have a `_djvu.txt` (has imagecount, scanned-book collection): {text:,}",
        f"- Overlap with Harvard slice ({harvard_rows:,} distinct title/year keys; normalized "
        f"title first 60 chars + year): {over:,}",
        f"- Likely text and not in Harvard: {new_text:,} "
        f"(about {images:,} page images in non-overlapping items)",
        "",
        "## Top collections",
        "",
        "| Collection | Items |",
        "| --- | --- |",
    ]
    for c, n in cols.most_common(25):
        lines.append(f"| {c} | {n:,} |")
    lines += ["", "## By year", "", "| Year | Items |", "| --- | --- |"]
    for y in sorted(by_year):
        lines.append(f"| {y} | {by_year[y]:,} |")
    return "\n".join(lines) + "\n"


def pull(limit: int | None, delay: float, skip_overlap: bool) -> int:
    with gzip.open(CATALOG, "rt", encoding="utf-8") as fh:
        recs = [json.loads(line) for line in fh]
    recs = [r for r in recs if r["has_text_likely"]]
    if skip_overlap:
        recs = [r for r in recs if not r["harvard_overlap"]]
    txt_dir = CORPUS / "text"
    txt_dir.mkdir(parents=True, exist_ok=True)
    failed = CORPUS / "failed.txt"
    skip = set()
    if failed.exists():
        skip = {ln.split("\t")[0] for ln in failed.read_text().splitlines() if "\t404" in ln}
    todo = [
        r for r in recs if not (txt_dir / f"{r['identifier']}.txt").exists()
        and r["identifier"] not in skip
    ]  # fmt: skip
    print(f"{len(recs):,} items in scope; {len(todo):,} to fetch")
    n = 0
    for r in todo:
        ident = r["identifier"]
        try:
            data = fetch(DOWNLOAD_URL.format(id=urllib.parse.quote(ident)))
        except urllib.error.HTTPError as exc:
            with failed.open("a") as fh:
                fh.write(f"{ident}\t{exc.code}\n")
            time.sleep(delay)
            continue
        except Exception as exc:  # noqa: BLE001
            with failed.open("a") as fh:
                fh.write(f"{ident}\terror {exc}\n")
            continue
        (txt_dir / f"{ident}.txt").write_bytes(data)
        n += 1
        if n % 200 == 0:
            print(f"  fetched {n:,}/{len(todo):,}", flush=True)
        if limit and n >= limit:
            print(f"stopped at --limit {limit}")
            break
        time.sleep(delay)
    print(f"fetched {n:,} texts into {CORPUS}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("catalog")
    c.add_argument("--delay", type=float, default=2.0)
    p = sub.add_parser("pull")
    p.add_argument("--limit", type=int)
    p.add_argument("--delay", type=float, default=1.0)
    p.add_argument("--skip-harvard-overlap", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "catalog":
        return catalog(a.delay)
    return pull(a.limit, a.delay, a.skip_harvard_overlap)


if __name__ == "__main__":
    sys.exit(main())
