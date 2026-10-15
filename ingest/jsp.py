"""Fetch Book of Mormon manuscript transcripts from the Joseph Smith Papers (BOM-05).

Each page on josephsmithpapers.org embeds its data as JSON in a ``__NEXT_DATA__`` script.
This module pulls every page of a document, stores the raw per-page JSON, and writes one
JSON Lines file with the fields the project uses: transcript (original inscriptions only,
as the site presents them), editorial page number, handwriting and scribe notes, footnotes,
and table-of-contents entry.

The transcripts are copyright Intellectual Reserve, Inc. They are stored under
``data/private/`` (the private data repo, see ``scripts/data_clone.sh``) and are not
redistributed; the public repo commits only their checksum manifest.

Usage::

    python -m ingest.jsp printers   # 468 pages
    python -m ingest.jsp original   # 231 pages
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://www.josephsmithpapers.org/paper-summary/"
DOCS = {
    "printers": "printers-manuscript-of-the-book-of-mormon-circa-august-1829-circa-january-1830",
    "original": "original-manuscript-of-the-book-of-mormon-circa-12-april-1828-circa-1-july-1829",
}
USER_AGENT = "bom-authorship-research/0.1 (+https://github.com/lifehug/book-of-mormon-authorship)"
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
POPUP_RE = re.compile(r"<aside[^>]*>.*?</aside>", re.S)
KEEP = [
    "uri", "editorialPageNumber", "requestedPageNumber", "numberOfPages", "editorialTitle",
    "date", "handwriting", "scribes", "footnotes", "classification", "accessionNumber",
    "printVolumeLocation", "imageCredit",
]  # fmt: skip


def fetch(url: str, retries: int = 4) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
            print(f"retry {attempt + 1} for {url}: {exc}", file=sys.stderr)
    raise RuntimeError("unreachable")


def page_props(page_html: str) -> dict:
    m = NEXT_DATA_RE.search(page_html)
    if not m:
        raise ValueError("no __NEXT_DATA__ in page")
    return json.loads(m.group(1))["props"]["pageProps"]


def clean_text(fragment: str) -> str:
    """Transcript text with editorial popups removed and tags stripped."""
    body = POPUP_RE.sub(" ", fragment)
    body = re.sub(r"</(p|div|br|li|h\d)>", "\n", body)
    body = TAG_RE.sub(" ", body)
    body = html.unescape(body)
    body = re.sub(r"[ \t]+", " ", body)
    return re.sub(r"\n\s*\n+", "\n", body).strip()


def extract(props: dict, page: int) -> dict:
    sm = props["summary"]
    rec = {"page": page}
    for k in KEEP:
        if k in sm:
            rec[k] = sm[k]
    rec["clear_html"] = sm.get("clearText", "")
    rec["expanded_html"] = sm.get("expandedText", "")
    rec["text"] = clean_text(sm.get("clearText", ""))
    asides = re.findall(r"<aside[^>]*>(.*?)</aside>", sm.get("expandedText", ""), re.S)
    rec["editorial_notes"] = [clean_text(a) for a in asides]
    toc = [t for t in props.get("tableOfContents", []) if str(t.get("pageNumber")) == str(page)]
    rec["toc"] = toc[0] if toc else None
    return rec


def run(doc: str, out_dir: Path, delay: float, limit: int | None) -> Path:
    slug = DOCS[doc]
    raw_dir = out_dir / "raw" / "jsp" / doc
    raw_dir.mkdir(parents=True, exist_ok=True)
    first = raw_dir / "0001.json"
    if first.exists():
        props = json.load(open(first, encoding="utf-8"))
    else:
        props = page_props(fetch(f"{BASE}{slug}/1"))
        json.dump(props, open(first, "w", encoding="utf-8"))
        time.sleep(delay)
    total = int(props["summary"]["numberOfPages"])
    toc_path = Path("data/bom") / f"jsp_{doc}_toc.json"
    toc_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(props.get("tableOfContents", []), open(toc_path, "w", encoding="utf-8"), indent=1)
    if limit:
        total = min(total, limit)
    print(f"{doc}: {total} pages -> {raw_dir}", flush=True)
    for page in range(1, total + 1):
        path = raw_dir / f"{page:04d}.json"
        if path.exists():
            continue
        props = page_props(fetch(f"{BASE}{slug}/{page}"))
        json.dump(props, open(path, "w", encoding="utf-8"))
        if page % 25 == 0:
            print(f"  {doc} page {page}/{total}", flush=True)
        time.sleep(delay)
    out = out_dir / f"jsp_{doc}.jsonl"
    with open(out, "w", encoding="utf-8") as fh:
        for page in range(1, total + 1):
            props = json.load(open(raw_dir / f"{page:04d}.json", encoding="utf-8"))
            fh.write(json.dumps(extract(props, page), ensure_ascii=False) + "\n")
    print(f"wrote {out}", flush=True)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("doc", choices=sorted(DOCS))
    ap.add_argument("--out", type=Path, default=Path("data/private/bom"))
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between requests")
    ap.add_argument("--limit", type=int, help="fetch only the first N pages (testing)")
    a = ap.parse_args(argv)
    run(a.doc, a.out, a.delay, a.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
