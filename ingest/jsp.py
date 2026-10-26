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
from html.parser import HTMLParser
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
KEEP = [
    "uri", "editorialPageNumber", "requestedPageNumber", "numberOfPages", "editorialTitle",
    "date", "handwriting", "scribes", "footnotes", "classification", "accessionNumber",
    "printVolumeLocation", "imageCredit",
]  # fmt: skip


class TransientError(RuntimeError):
    """The site answered, but without the transcript; retry later, never save."""


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
    props = json.loads(m.group(1))["props"]["pageProps"]
    # On 2026-10-25 the site served its page shell with summary {"status": 500, "error": true}
    # and no transcript; saving that would record an outage as the page (BOM-13).
    sm = props.get("summary") or {}
    if sm.get("error") or "clearText" not in sm:
        raise TransientError(f"transcript unavailable: summary {str(sm)[:80]}")
    return props


# Elements whose text is the editors', not the writer's: popup notes, hidden glosses
# ("hide-this", biographies), "Editorial Note" essays ("note-data"), note letters ("toe-note"),
# and popup anchors that hold a footnote number or a scribe-change icon. A "reference" popup
# anchor is transcript (a glossed word, e.g. "Kees") and is kept (BOM-13). An inline
# "editorial-comment" ("[2 pages not extant]") is kept: JSP prints it inside square brackets,
# ingest.extant reads the gaps from it, and transcript_words drops bracketed text.
EDITORIAL_CLASSES = {"popup-content", "hide-this", "note-data", "toe-note"}
KEPT_CLASSES = {"editorial-comment"}
EDITORIAL_ANCHORS = {"editorial-note-static", "new-scribe-note"}
BLOCK_TAGS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
VOID_TAGS = {"br", "img", "hr", "input", "meta", "link", "wbr"}


class _TranscriptParser(HTMLParser):
    """Characters of a JSP transcript fragment, each tagged True when in Joseph Smith's hand
    (JSP's ``<span class="josephswriting">``), with editorial elements skipped."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool, bool]] = []  # (tag, in JS's hand, editorial)
        self.chars: list[tuple[str, bool]] = []

    def _state(self) -> tuple[bool, bool]:
        return (self.stack[-1][1], self.stack[-1][2]) if self.stack else (False, False)

    def handle_starttag(self, tag, attrs):
        js, skip = self._state()
        if tag in VOID_TAGS:
            if tag == "br" and not skip:
                self.chars.append(("\n", js))
            return
        classes = set((dict(attrs).get("class") or "").split())
        skip = skip or bool(classes & EDITORIAL_CLASSES and not classes & KEPT_CLASSES)
        skip = skip or (tag == "a" and bool(classes & EDITORIAL_ANCHORS))
        js = js or (tag == "span" and "josephswriting" in classes)
        self.stack.append((tag, js, skip))

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        js, skip = self._state()
        if tag in BLOCK_TAGS and not skip:
            self.chars.append(("\n", js))

    def handle_data(self, data):
        js, skip = self._state()
        if not skip:
            self.chars.extend((c, js) for c in data)


def transcript_chars(fragment: str) -> list[tuple[str, bool]]:
    p = _TranscriptParser()
    p.feed(fragment)
    p.close()
    return p.chars


def transcript_text(fragment: str) -> str:
    """The writer's text of a JSP transcript fragment, as JSP presents it (its square-bracketed
    insertions kept). Inline tags never split a word: JSP opens a new span mid-word
    ("instruct</span><span>ing")."""
    body = "".join(c for c, _ in transcript_chars(fragment))
    body = re.sub(r"[ \t]+", " ", body)
    return re.sub(r"\s*\n\s*", "\n", body).strip()


def _drop_brackets(chars: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    """Remove square-bracketed spans; an unmatched bracket is kept as text."""
    keep = [True] * len(chars)
    opens: list[int] = []
    for i, (c, _) in enumerate(chars):
        if c == "[":
            opens.append(i)
        elif c == "]" and opens:
            start = opens.pop()
            if not opens:
                keep[start : i + 1] = [False] * (i + 1 - start)
    return [ch for ch, k in zip(chars, keep, strict=True) if k]


def transcript_words(fragment: str, drop_brackets: bool = True) -> list[tuple[str, bool]]:
    """Words of a fragment, each with True if in JS's hand. Square-bracketed spans are JSP's
    editorial insertions (``[p. 4]``, supplied letters) and are dropped unless told otherwise.
    A word that straddles a change of hand takes the hand of most of its characters."""
    chars = transcript_chars(fragment)
    if drop_brackets:
        chars = _drop_brackets(chars)
    out: list[tuple[str, bool]] = []
    word: list[tuple[str, bool]] = []
    for c, js in [*chars, (" ", False)]:
        if not c.isspace():
            word.append((c, js))
        elif word:
            out.append(("".join(ch for ch, _ in word), sum(j for _, j in word) * 2 > len(word)))
            word = []
    return out


def clean_text(fragment: str) -> str:
    """Text of an editorial note (tags stripped). Transcripts use ``transcript_text``."""
    body = re.sub(r"</(p|div|br|li|h\d)>", "\n", fragment)
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
    rec["text"] = transcript_text(sm.get("clearText", ""))
    asides = re.findall(r"<aside[^>]*>(.*?)</aside>", sm.get("expandedText", ""), re.S)
    rec["editorial_notes"] = [clean_text(a) for a in asides]
    toc = [t for t in props.get("tableOfContents", []) if str(t.get("pageNumber")) == str(page)]
    rec["toc"] = toc[0] if toc else None
    return rec


def sections(records: list[dict], toc: list[dict]) -> list[dict]:
    """Cut a document into its table-of-contents entries at their anchors (BOM-13).

    Each TOC entry's ``linkID`` appears as ``<a name="...">`` in the page markup where the
    entry begins; a section runs from its anchor to the next one, across page breaks. Text
    before the first anchor is returned with ``link_id`` None. ``html`` is the cut markup, for
    callers that need more than the text (the hand split in ``ingest.candidate_words``). An
    entry whose anchor is not found is returned with ``anchor_found`` False and no text, never
    dropped. The TOC ``date`` is only the start of the entry's period ("circa Early 1830" is
    ``1830-01-01``), so it is passed through and never used to decide anything here.
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
        fragment = "\n".join(p for p in parts if p)
        text = transcript_text(fragment)
        if t is None and not text:
            continue
        out.append(
            {
                "link_id": t["linkID"] if t else None,
                "title": html.unescape(t["pageTitle"]) if t else None,
                "toc_date": t.get("date") if t else None,
                "first_page": pages[i0]["page"] if i0 < len(pages) else None,
                "anchor_found": True,
                "html": fragment,
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
                "html": None,
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
