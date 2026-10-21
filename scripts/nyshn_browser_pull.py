#!/usr/bin/env python3
"""Pull a title from NYS Historic Newspapers through a browser you have already unlocked.

nyshistoricnewspapers.org (Veridian, since 2023) sits behind Cloudflare: curl and WebFetch get
a 403 "Just a moment" page. A real browser passes the challenge once per session. This script
does not try to beat Cloudflare; it drives *your* browser after you have passed it, over the
Chrome DevTools Protocol, so every request the site sees is the browser's own.

Setup (one time):

    uv run --with playwright python -c "print('ok')"       # fetches the playwright package

Run (every session):

    1. Quit Brave, then start it with remote debugging on and a throwaway profile:

         "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \\
             --remote-debugging-port=9222 --user-data-dir=/tmp/brave-nyshn &

       (Google Chrome works the same; swap the path.)
    2. In that window open https://nyshistoricnewspapers.org/ and wait until the site shows
       normally (pass the Cloudflare check if it appears).
    3. In this terminal, from the repo root:

         uv run --with playwright python scripts/nyshn_browser_pull.py probe \\
             "https://nyshistoricnewspapers.org/?a=cl&cl=CL1"
         uv run --with playwright python scripts/nyshn_browser_pull.py pull \\
             --title "Wayne Sentinel" --start 1823-01-01 --end 1830-12-31

``probe URL`` opens the URL in the unlocked browser, saves the page's HTML to
``logs/nyshn_probe.html`` and prints every link grouped by Veridian action code, so the
title code, issue and page URL shapes can be read off before a pull. Use it first: the
Veridian URL layout below was written from other Veridian sites and from the search page
Dave pasted on 2026-10-20, not from a live session, so ``pull`` may need its two regexes
(``ISSUE_LINK`` and ``PAGE_LINK``) adjusted after one probe.

``pull`` walks: the title's browse-by-date page -> each issue in the date range -> each page
of the issue, and for each page saves the OCR text the site shows in its "Text" view (the
Veridian ``f=TXT`` rendering of a page, falling back to the page's text pane in the DOM) to
``data/corpus/nyshn/<slug>/text/<YYYY-MM-DD>-p<n>.txt`` and, with ``--pdf``, the page PDF
from the site's download link to ``data/corpus/nyshn/<slug>/pdf/``. Resumable; one page per
``--delay`` seconds (default 2). Progress and failures go to ``data/corpus/nyshn/<slug>/pull.log``.

Veridian URL shapes assumed (each is a plain GET the browser performs):

    title list        /?a=cl&cl=CL1
    title, by date    /?a=cl&cl=CL1&sp=<TITLECODE>
    issue             /?a=d&d=<TITLECODE><YYYYMMDD>-01
    page n            /?a=d&d=<TITLECODE><YYYYMMDD>-01.1.<n>
    page text         same URL with &f=TXT   (falls back to the DOM's text pane)
    page PDF          link whose href contains "type=pdf" or ends in ".pdf" on the page view

Nothing here runs without the browser; if the connection fails the script says so and stops.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

SITE = "https://nyshistoricnewspapers.org/"
CDP = "http://127.0.0.1:9222"
OUT = Path("data/corpus/nyshn")
ISSUE_LINK = re.compile(r"[?&]a=d&d=(?P<code>[A-Za-z]+)(?P<date>\d{8})-(?P<ed>\d{2})(?![.\d])")
PAGE_LINK = re.compile(
    r"[?&]a=d&d=(?P<code>[A-Za-z]+)(?P<date>\d{8})-(?P<ed>\d{2})\.1\.(?P<page>\d+)"
)


def connect():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright is not installed: run with `uv run --with playwright python ...`")
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(CDP)
    except Exception as exc:  # noqa: BLE001
        pw.stop()
        sys.exit(
            f"could not reach a browser at {CDP}: {exc}\n"
            "start Brave/Chrome with --remote-debugging-port=9222 first (see the docstring)"
        )
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return pw, browser, page


def goto(page, url: str, delay: float) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    time.sleep(delay)
    html = page.content()
    if "Just a moment" in html[:3000] or "cf-chl" in html[:5000]:
        raise RuntimeError(
            "Cloudflare challenge page: pass it in the browser window, then rerun (resumes)"
        )
    return html


def links(html: str, base: str) -> list[str]:
    return [urljoin(base, h) for h in re.findall(r'href="([^"#]+)"', html)]


def probe(url: str, delay: float) -> int:
    pw, browser, page = connect()
    try:
        html = goto(page, url, delay)
    except RuntimeError as exc:
        print(exc)
        return 1
    finally:
        pw.stop()
    Path("logs").mkdir(exist_ok=True)
    Path("logs/nyshn_probe.html").write_text(html, encoding="utf-8")
    groups: dict[str, set[str]] = defaultdict(set)
    for link in links(html, url):
        q = parse_qs(urlparse(link).query)
        groups[q.get("a", ["(no a=)"])[0]].add(link)
    print(f"title: {re.findall(r'<title>(.*?)</title>', html, re.S)[:1]}  ({len(html):,} bytes)")
    for a, ls in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"\n[a={a}] {len(ls)} links, e.g.")
        for link in sorted(ls)[:6]:
            print("   ", link)
    hits = [m.group(0) for m in ISSUE_LINK.finditer(html)]
    print(
        f"\nISSUE_LINK matches: {len(set(hits))}; PAGE_LINK matches: "
        f"{len(set(m.group(0) for m in PAGE_LINK.finditer(html)))}"
    )
    print("saved logs/nyshn_probe.html")
    return 0


def page_text(page, url: str, delay: float) -> str:
    """The OCR text for a page view: try the f=TXT rendering, then the DOM's text pane."""
    sep = "&" if "?" in url else "?"
    html = goto(page, f"{url}{sep}f=TXT", delay)
    body = re.sub(r"<[^>]+>", " ", html)
    if len(body.split()) > 50 and "<html" not in html[:200].lower():
        return body
    html = goto(page, url, delay)
    for sel in (
        "#documenttext",
        ".documenttext",
        "#documentdisplayleftpanesectiontextcontainer",
        "div.textcontainer",
        "#textpane",
    ):  # Veridian text-pane ids seen on other sites
        try:
            el = page.query_selector(sel)
        except Exception:  # noqa: BLE001
            el = None
        if el:
            t = el.inner_text()
            if t.strip():
                return t
    return ""


def pull(
    title: str,
    code: str | None,
    start: str,
    end: str,
    delay: float,
    want_pdf: bool,
    limit: int | None,
) -> int:
    d0, d1 = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    out = OUT / slug
    (out / "text").mkdir(parents=True, exist_ok=True)
    if want_pdf:
        (out / "pdf").mkdir(exist_ok=True)
    log = (out / "pull.log").open("a", encoding="utf-8")
    pw, browser, page = connect()
    done = 0
    try:
        # 1. title browse page -> issue links
        if code is None:
            html = goto(page, f"{SITE}?a=cl&cl=CL1", delay)
            pat = r'href="([^"]*sp=(?P<code>[A-Za-z0-9]+)[^"]*)"[^>]*>\s*' + re.escape(title)
            m = re.search(pat, html, re.I)
            if not m:
                sys.exit(f"title {title!r} not found on the title list; pass --code")
            code = m.group("code")
        print(f"title code: {code}")
        html = goto(page, f"{SITE}?a=cl&cl=CL1&sp={code}", delay)
        issues = sorted(
            {
                (mm.group("date"), mm.group("ed"))
                for mm in ISSUE_LINK.finditer(html)
                if mm.group("code").lower() == code.lower()
            }
        )
        issues = [
            (d, e)
            for d, e in issues
            if d0 <= dt.date.fromisoformat(f"{d[:4]}-{d[4:6]}-{d[6:]}") <= d1
        ]
        print(
            f"{len(issues)} issues in {start}..{end} on the browse page "
            f"(if 0, run probe on that URL and fix ISSUE_LINK)"
        )
        # 2. each issue -> pages
        for date, ed in issues:
            iso = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            issue_url = f"{SITE}?a=d&d={code}{date}-{ed}"
            html = goto(page, issue_url, delay)
            pages = sorted(
                {
                    int(mm.group("page"))
                    for mm in PAGE_LINK.finditer(html)
                    if mm.group("date") == date
                }
            ) or [1]
            for n in pages:
                if limit is not None and done >= limit:
                    print("limit reached")
                    return 0
                txt_path = out / "text" / f"{iso}-ed{int(ed)}-p{n}.txt"
                if txt_path.exists():
                    continue
                purl = f"{issue_url}.1.{n}"
                try:
                    text = page_text(page, purl, delay)
                except RuntimeError as exc:
                    print(exc)
                    return 1
                txt_path.write_text(text, encoding="utf-8")
                rec = {"date": iso, "ed": int(ed), "page": n, "url": purl}
                rec["words"] = len(text.split())
                if want_pdf:
                    html = goto(page, purl, delay)
                    pdfs = [
                        link
                        for link in links(html, purl)
                        if "type=pdf" in link or link.lower().endswith(".pdf")
                    ]
                    if pdfs:
                        resp = page.request.get(pdfs[0])
                        if resp.ok:
                            (out / "pdf" / f"{iso}-ed{int(ed)}-p{n}.pdf").write_bytes(resp.body())
                            rec["pdf"] = pdfs[0]
                log.write(json.dumps(rec) + "\n")
                log.flush()
                done += 1
                print(f"{iso} p{n}: {rec['words']} words")
    finally:
        pw.stop()
    print(f"done: {done} pages this run -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe")
    p.add_argument("url")
    p.add_argument("--delay", type=float, default=2.0)
    q = sub.add_parser("pull")
    q.add_argument("--title", required=True)
    q.add_argument("--code", help="Veridian title code if the title list lookup fails")
    q.add_argument("--start", default="1800-01-01")
    q.add_argument("--end", default="1830-12-31")
    q.add_argument("--delay", type=float, default=2.0)
    q.add_argument("--pdf", action="store_true", help="also save each page's PDF")
    q.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    if a.cmd == "probe":
        return probe(a.url, a.delay)
    return pull(a.title, a.code, a.start, a.end, a.delay, a.pdf, a.limit)


if __name__ == "__main__":
    sys.exit(main())
