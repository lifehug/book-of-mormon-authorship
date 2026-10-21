"""Newspapers hosted on Advantage Preservation archives (BOM-41).

Small public libraries publish their digitized newspapers through Advantage Archives
("Community History Archives", ``<site>.advantage-preservation.com``). The first title this
project takes from one is the *Lake Light* (Trumansburg, N.Y., 1827-1828), W. W. Phelps's
first paper, from the Ulysses Philomathic Library's archive at
``trumansburg.advantage-preservation.com``: 168 pages in 42 issues, 10 Oct 1827 to 19 Nov 1828,
the run the New York State Library holds on microfilm. The site advertises 336 pages because it
holds the run twice: collection ``cid=3142`` (400 dpi, Tesseract 5 text layer; what we take)
and ``cid=2734`` (an older ABBYY FineReader 9 scan of the same pages, which files four issues
under the wrong date). Measured 2026-10-20 by probing every date under both ids.

How the site works (read from its scripts on 2026-10-20; nothing is Cloudflare-fronted):

* Every page is one PDF: a 400 dpi greyscale scan with a Tesseract 5 text layer, served by
  ``/viewer/GetPdfFile?<PubdateId>``.
* A page is named ``<title>_usa_new_york_<town>_<YYYYMMDD>_english_<n>``. The viewer
  (``/viewer/?t=<title ids>&i=t&fn=<name>&df=1&dt=10&cid=<collection>``) resolves that name
  to the PubdateId in its ``GetViewer`` link; a name that does not exist returns a short
  "PDF can't be displayed" shell. The ``cid`` is required and selects the digitization.
* The search endpoint pages through results in an unstable order, so the page list is built
  by probing instead: page 1 of every date in the run, then pages 2.. of each date that
  answers, until the first miss. For a weekly that is a few hundred cheap requests.

``pull`` writes PDFs to ``data/corpus/advantage/<site>/<name>.pdf`` (not in git), the PDF's
own text layer to ``data/newspapers/<slug>/text/<name>.txt`` (in git: a few MB for a title
this size), and ``data/newspapers/<slug>/pages.jsonl`` with one row per page (name, date,
page number, PubdateId, PDF sha256 and size, word count). Resumable: pages whose PDF is on
disk are not fetched again. One request per second.

Terms (``/termsof-use``): "made available to the community for the purpose of research,
study and to satisfy curiosity"; the 1827-1828 text is public domain.

Usage::

    python -m ingest.advantage_archive pull [--limit N] [--start 1827-10-01] [--end 1828-12-31]
    python -m ingest.advantage_archive pull --title "Lake Light"   # the default; see TITLES
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "bom-authorship-research/0.1 (+https://github.com/lifehug/book-of-mormon-authorship)"
TITLES = {
    "Lake Light": {
        "site": "trumansburg",
        "slug": "lake_light",
        "prefix": "lake_light_usa_new_york_trumansburg",
        "title_ids": "34773,47247",
        "cid": "3142",
        "start": "1827-10-01",
        "end": "1828-12-31",
        "max_pages": 8,
    },
}
CORPUS = Path("data/corpus/advantage")
OUT = Path("data/newspapers")
PUBDATE_RE = re.compile(r"PubdateId=(\d+)")
NAME_RE = re.compile(r"^(?P<prefix>.+)_(?P<date>\d{8})_english_(?P<page>\d+)$")


def page_name(prefix: str, date: dt.date, page: int) -> str:
    return f"{prefix}_{date:%Y%m%d}_english_{page}"


def parse_name(name: str) -> tuple[str, int]:
    """``(YYYY-MM-DD, page number)`` from a page name."""
    m = NAME_RE.match(name)
    if not m:
        raise ValueError(name)
    d = m.group("date")
    return f"{d[:4]}-{d[4:6]}-{d[6:]}", int(m.group("page"))


def pubdate_id(viewer_html: str) -> str | None:
    """The PubdateId in a viewer shell, or None when the page does not exist."""
    m = PUBDATE_RE.search(viewer_html)
    return m.group(1) if m else None


def viewer_url(site: str, title_ids: str, cid: str, name: str) -> str:
    return (
        f"https://{site}.advantage-preservation.com/viewer/?t={title_ids}&i=t&fn={name}"
        f"&df=1&dt=10&cid={cid}"
    )


def pdf_url(site: str, pid: str) -> str:
    return f"https://{site}.advantage-preservation.com/viewer/GetPdfFile?{pid}"


def fetch(url: str, timeout: int = 120, tries: int = 10) -> bytes:
    """GET with backoff. Ten tries span about 25 minutes, enough to ride out a dropped
    connection (DNS failures took the first run down after three tries and 30 s)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            if attempt == tries - 1:
                raise
            wait = min(300, 10 * 2**attempt)
            print(f"  retry {attempt + 1} in {wait}s: {exc}", file=sys.stderr, flush=True)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def pdf_text(pdf: Path) -> str:
    """The PDF's own text layer via poppler's pdftotext (empty string if unavailable)."""
    try:
        r = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return ""
    return r.stdout if r.returncode == 0 else ""


def load_rows(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if path.exists():
        for line in path.open(encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                rows[r["name"]] = r
    return rows


def pull(
    title: str, start: str | None, end: str | None, limit: int | None, delay: float = 1.0
) -> int:
    cfg = TITLES[title]
    site, prefix, slug = cfg["site"], cfg["prefix"], cfg["slug"]
    d0 = dt.date.fromisoformat(start or cfg["start"])
    d1 = dt.date.fromisoformat(end or cfg["end"])
    pdf_dir = CORPUS / site
    text_dir = OUT / slug / "text"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)
    rows_path = OUT / slug / "pages.jsonl"
    rows = load_rows(rows_path)
    misses_path = OUT / slug / "probed_misses.txt"
    misses = set(misses_path.read_text().split()) if misses_path.exists() else set()
    fetched = 0
    day = d0
    with rows_path.open("a", encoding="utf-8") as out, misses_path.open("a") as miss_out:
        while day <= d1:
            page = 1
            while page <= cfg["max_pages"]:
                name = page_name(prefix, day, page)
                if name in rows:
                    page += 1
                    continue
                if name in misses:
                    break
                if limit is not None and fetched >= limit:
                    print(f"limit {limit} reached")
                    return 0
                html = fetch(viewer_url(site, cfg["title_ids"], cfg["cid"], name)).decode(
                    "utf-8", "replace"
                )
                time.sleep(delay)
                pid = pubdate_id(html)
                if pid is None:
                    misses.add(name)
                    miss_out.write(name + "\n")
                    miss_out.flush()
                    break  # no such page: next date (page 1) or end of this issue
                pdf = pdf_dir / f"{name}.pdf"
                if not pdf.exists():
                    data = fetch(pdf_url(site, pid), timeout=300)
                    pdf.write_bytes(data)
                    time.sleep(delay)
                text = pdf_text(pdf)
                (text_dir / f"{name}.txt").write_text(text, encoding="utf-8")
                date_iso, _ = parse_name(name)
                row = {
                    "name": name,
                    "title": title,
                    "date": date_iso,
                    "page": page,
                    "pubdate_id": pid,
                    "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    "pdf_bytes": pdf.stat().st_size,
                    "words": len(text.split()),
                }
                out.write(json.dumps(row) + "\n")
                out.flush()
                rows[name] = row
                fetched += 1
                print(f"{name}: PubdateId {pid}, {row['pdf_bytes']:,} B, {row['words']} words")
                page += 1
            day += dt.timedelta(days=1)
    issues = {r["date"] for r in rows.values()}
    print(
        f"done: {len(rows):,} pages, {len(issues)} issues, "
        f"{sum(r['words'] for r in rows.values()):,} words of text layer -> {rows_path}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--title", default="Lake Light", choices=sorted(TITLES))
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--limit", type=int)
    p.add_argument("--delay", type=float, default=1.0)
    a = ap.parse_args(argv)
    return pull(a.title, a.start, a.end, a.limit, a.delay)


if __name__ == "__main__":
    sys.exit(main())
