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
import random
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
# Since October 2026 josephsmithpapers.org answers 404 to a self-identified research agent and
# 200 to a browser, and its footer links the Church terms of use, which bar automated access.
# On 2026-10-25 the owner chose to fetch with a browser User-Agent, requests a random 2.5 to
# 7.5 s apart (BOM-13); the decision and the terms are recorded in docs/candidates.md. Other
# hosts keep USER_AGENT. At a 1 s average the site began refusing pages with a 404 that cleared
# minutes later, so JSP retries back off by minutes, not seconds.
JSP_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
)
JSP_DELAY = 5.0
JSP_BACKOFF = 60.0
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
TAG_RE = re.compile(r"<[^>]+>")
POPUP_RE = re.compile(r"<aside[^>]*>.*?</aside>", re.S)
KEEP = [
    "uri", "editorialPageNumber", "requestedPageNumber", "numberOfPages", "editorialTitle",
    "date", "handwriting", "scribes", "footnotes", "classification", "accessionNumber",
    "printVolumeLocation", "imageCredit",
]  # fmt: skip


def fetch(url: str, retries: int = 4, user_agent: str = USER_AGENT, backoff: float = 5.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            time.sleep(backoff * (attempt + 1))
            print(f"retry {attempt + 1} for {url}: {exc}", file=sys.stderr)
    raise RuntimeError("unreachable")


def pause(delay: float) -> None:
    """Sleep a random 0.5x to 1.5x ``delay``, so requests average ``delay`` apart."""
    time.sleep(random.uniform(0.5 * delay, 1.5 * delay))


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


def sections(records: list[dict], toc: list[dict]) -> list[dict]:
    """Cut a document into its table-of-contents entries at their anchors (BOM-13).

    Each TOC entry's ``linkID`` appears as ``<a name="...">`` in the page markup where the
    entry begins; a section runs from its anchor to the next one, across page breaks. Text
    before the first anchor is returned with ``link_id`` None. An entry whose anchor is not
    found is returned with ``anchor_found`` False and no text, never dropped. The TOC ``date`` is
    only the
    start of the entry's period ("circa Early 1830" is ``1830-01-01``), so it is passed through
    and never used to decide anything here.
    """
    pages = sorted(records, key=lambda r: r["page"])
    starts = []  # (page index, offset, toc entry)
    missing = []
    for t in toc:
        tag = f'<a name="{t["linkID"]}"'
        for i, r in enumerate(pages):
            off = r["clear_html"].find(tag)
            if off >= 0:
                starts.append((i, off, t))
                break
        else:
            missing.append(t)
    starts.sort(key=lambda s: (s[0], s[1]))
    bounds = [(0, 0, None)] + starts + [(len(pages), 0, None)]
    out = []
    for (i0, o0, t), (i1, o1, _) in zip(bounds, bounds[1:], strict=False):
        parts = []
        for i in range(i0, min(i1, len(pages) - 1) + 1):
            h = pages[i]["clear_html"]
            lo = o0 if i == i0 else 0
            hi = o1 if i == i1 else len(h)
            parts.append(h[lo:hi])
        text = clean_text("\n".join(p for p in parts if p))
        if t is None and not text:
            continue
        out.append(
            {
                "link_id": t["linkID"] if t else None,
                "title": html.unescape(t["pageTitle"]) if t else None,
                "toc_date": t.get("date") if t else None,
                "first_page": pages[i0]["page"] if i0 < len(pages) else None,
                "anchor_found": True,
                "text": text,
                "words": len(text.split()),
            }
        )
    for t in missing:
        out.append(
            {
                "link_id": t["linkID"],
                "title": html.unescape(t["pageTitle"]),
                "toc_date": t.get("date"),
                "first_page": None,
                "anchor_found": False,
                "text": None,
                "words": None,
            }
        )
    return out


def run(doc: str, out_dir: Path, delay: float, limit: int | None) -> Path:
    slug = DOCS[doc]
    raw_dir = out_dir / "raw" / "jsp" / doc
    raw_dir.mkdir(parents=True, exist_ok=True)
    first = raw_dir / "0001.json"
    if first.exists():
        props = json.load(open(first, encoding="utf-8"))
    else:
        props = page_props(fetch(f"{BASE}{slug}/1", user_agent=JSP_USER_AGENT, backoff=JSP_BACKOFF))
        json.dump(props, open(first, "w", encoding="utf-8"))
        pause(delay)
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
        props = page_props(
            fetch(f"{BASE}{slug}/{page}", user_agent=JSP_USER_AGENT, backoff=JSP_BACKOFF)
        )
        json.dump(props, open(path, "w", encoding="utf-8"))
        if page % 25 == 0:
            print(f"  {doc} page {page}/{total}", flush=True)
        pause(delay)
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
    ap.add_argument("--delay", type=float, default=JSP_DELAY, help="seconds between requests")
    ap.add_argument("--limit", type=int, help="fetch only the first N pages (testing)")
    a = ap.parse_args(argv)
    run(a.doc, a.out, a.delay, a.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
