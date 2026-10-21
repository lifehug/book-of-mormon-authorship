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
             --remote-debugging-port=9222 --user-data-dir=/tmp/brave-nyshn

       It prints "DevTools listening on ws://127.0.0.1:9222/..." (the STUN/DNS errors after it
       are noise). Google Chrome works the same; swap the path.
    2. In that window open https://nyshistoricnewspapers.org/ and wait until the site shows
       normally (pass the Cloudflare check if it appears).
    3. In another terminal, from the repo root:

         uv run --with playwright python scripts/nyshn_browser_pull.py probe \\
             "https://nyshistoricnewspapers.org/?a=cl&cl=CL1"
         uv run --with playwright python scripts/nyshn_browser_pull.py pull \\
             --title "Wayne Sentinel" --start 1823-10-01 --end 1830-12-31

``probe URL`` opens the URL in the unlocked browser, saves the page's HTML to
``logs/nyshn_probe.html`` and prints every link grouped by Veridian action code, plus how many
month / issue / page links the regexes below recognise.

``pull`` walks: title list -> the title's browse page (one link per month) -> each month page
(one link per issue) -> each issue page (one link per page) -> each page's text view, and saves
the OCR text to ``data/newspapers/<slug>/text/<name>.txt`` with a row per page in
``data/newspapers/<slug>/pages.jsonl`` (same layout as the Lake Light pull in
``ingest/advantage_archive.py``). With ``--pdf`` it also saves each page's PDF to
``data/corpus/nyshn/<slug>/<name>.pdf`` (about 0.5 MB a page; not in git). Resumable: pages
whose text file exists are skipped. Progress and failures also go to
``data/corpus/nyshn/<slug>/pull.log``.

Veridian URL shapes on this site, confirmed live on 2026-10-20 (Wayne Sentinel = code ``ws``):

    title list        /?a=cl&cl=CL1                      anchor per title, href has sp=<code>
    title, by month   /?a=cl&cl=CL1&sp=<code>            links cl=CL2.<YYYY>.<M>&sp=<code>
    month             /?a=cl&cl=CL2.<YYYY>.<M>&sp=<code> links d=<code><YYYYMMDD>-<ed>
    issue             /?a=d&d=<code><YYYYMMDD>-<ed>      links d=<code><YYYYMMDD>-<ed>.1.<n>
    page view         /?a=d&d=<code><YYYYMMDD>-<ed>.1.<n>
    page OCR text     page view + &dliv=none&st=1        <p dir="auto"> paragraphs after
                                                         <div id="ocrdisclaimer">
    page PDF          /?a=is&oid=<page id>&type=staticpdf
                      -> "Download PDF" page with a Cloudflare Turnstile. In a real browser
                      the widget sometimes solves itself within seconds and submits the form,
                      and the browser then navigates to the PDF; often it just sits there.
                      ``--pdf`` is therefore best-effort: it captures the PDF when the widget
                      solves and otherwise logs "pdf not received" and moves on (rerun to
                      retry). Playwright's own request API gets a Cloudflare 403. The text
                      view needs no Turnstile, so a text-only pull is reliable.

Nothing here runs without the browser; if the connection fails the script says so and stops.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html as htmllib
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

SITE = "https://nyshistoricnewspapers.org/"
# Veridian's environment param; harmless, keeps URLs canonical.
E = "-------en-20--1--txt-txIN----------"
CDP = "http://127.0.0.1:9222"
CORPUS = Path("data/corpus/nyshn")
OUT = Path("data/newspapers")

# Hrefs in the HTML carry "&amp;", so a parameter may be preceded by "&", "&amp;" or "?":
# "[?&;]name=" matches all three.
MONTH_LINK = re.compile(r"cl=CL2\.(?P<y>\d{4})\.(?P<m>\d{1,2})&(?:amp;)?sp=(?P<code>[a-z0-9]+)")
ISSUE_LINK = re.compile(r"[?&;]d=(?P<code>[a-z0-9]+?)(?P<date>\d{8})-(?P<ed>\d{2})(?![.\d])")
PAGE_LINK = re.compile(
    r"[?&;]d=(?P<code>[a-z0-9]+?)(?P<date>\d{8})-(?P<ed>\d{2})\.1\.(?P<page>\d+)"
)
TITLE_ANCHOR = re.compile(r"<a[^>]+sp=(?P<code>[a-z0-9]+)[^>]*>(?P<text>.*?)</a>", re.S)
CHALLENGE = ("<title>Just a moment", 'id="challenge-running"', 'id="challenge-error-text"')


def iso(date8: str) -> str:
    return f"{date8[:4]}-{date8[4:6]}-{date8[6:]}"


def page_name(slug: str, date8: str, ed: str, page: int) -> str:
    ed_part = "" if int(ed) == 1 else f"_ed{int(ed)}"
    return f"{slug}_{date8}{ed_part}_p{page}"


def text_from_view(view_html: str) -> str:
    """OCR text of a page's text view: the <p dir="auto"> paragraphs after the OCR disclaimer."""
    i = view_html.find('id="ocrdisclaimer"')
    if i < 0:
        return ""
    seg = view_html[i:]
    j = seg.find("<footer")
    if j > 0:
        seg = seg[:j]
    paras = re.findall(r'<p dir="auto">(.*?)</p>', seg, re.S)
    lines = [htmllib.unescape(re.sub(r"<[^>]+>", " ", p)) for p in paras]
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in lines]
    return "\n".join(ln for ln in lines if ln) + ("\n" if lines else "")


def title_codes(list_html: str) -> dict[str, list[str]]:
    """title text (lowercased, whitespace-collapsed) -> Veridian codes, from the title list page."""
    out: dict[str, list[str]] = defaultdict(list)
    for m in TITLE_ANCHOR.finditer(list_html):
        text = htmllib.unescape(
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group("text")))
        ).strip()
        if text:
            out[text.lower()].append(m.group("code"))
    return out


def connect():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright missing: run with `uv run --with playwright python scripts/...`")
    pw = sync_playwright().start()
    try:
        browser = pw.chromium.connect_over_cdp(CDP, timeout=5_000)
    except Exception as exc:  # noqa: BLE001
        pw.stop()
        sys.exit(
            f"no browser on {CDP} ({type(exc).__name__}). Start Brave/Chrome with "
            "--remote-debugging-port=9222 (see the docstring) and open the site first."
        )
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.new_page()
    return pw, browser, page


def is_challenge(html: str) -> bool:
    """A Cloudflare interstitial, not a normal page (those also embed a Turnstile widget)."""
    head = html[:8000]
    return any(s in head for s in CHALLENGE)


def goto(page, url: str, delay: float, wait_challenge: int = 600) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    time.sleep(delay)
    html = page.content()
    waited = 0
    while is_challenge(html) and waited < wait_challenge:
        if waited == 0:
            print("Cloudflare challenge: pass it in the browser window (waiting up to 10 min)")
        time.sleep(15)
        waited += 15
        html = page.content()
    if is_challenge(html):
        raise RuntimeError("Cloudflare challenge not cleared; rerun after passing it (resumes)")
    return html


def links(html: str, base: str) -> list[str]:
    return [urljoin(base, htmllib.unescape(h)) for h in re.findall(r'href="([^"#]+)"', html)]


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
    months = {m.group(0) for m in MONTH_LINK.finditer(html)}
    issues = {m.group(0) for m in ISSUE_LINK.finditer(html)}
    pages = {m.group(0) for m in PAGE_LINK.finditer(html)}
    print(f"\nMONTH_LINK {len(months)}; ISSUE_LINK {len(issues)}; PAGE_LINK {len(pages)}")
    text = text_from_view(html)
    if text:
        print(f"text view: {len(text.split())} words, starts: {text[:80]!r}")
    print("saved logs/nyshn_probe.html")
    return 0


def fetch_pdf(page, oid: str, timeout: float = 45.0) -> bytes | None:
    """Open the page's "Download PDF" link and capture the PDF the browser receives.

    The Turnstile on that page usually solves itself within seconds and submits the form; the
    browser then navigates to the same URL plus ``pdfaccesscode=...`` and gets the PDF. Some
    attempts never solve (the widget stays idle); those return None and the page is retried on
    the next run.
    """
    got: dict[str, bytes] = {}

    def on_response(resp):
        if got or "pdfaccesscode=" not in resp.url:
            return
        try:
            body = resp.body()
        except Exception:  # noqa: BLE001  (body may be gone for navigation responses)
            return
        if body[:4] == b"%PDF":
            got["body"] = body

    page.on("response", on_response)
    try:
        page.goto(
            f"{SITE}?a=is&oid={oid}&type=staticpdf&e={E}",
            wait_until="domcontentloaded",
            timeout=90_000,
        )
        t0 = time.time()
        while not got and time.time() - t0 < timeout:
            time.sleep(0.5)
            if "pdfaccesscode=" in page.url and time.time() - t0 > 5:
                # navigation happened but the response body was not captured: refetch from
                # inside the page with the browser's own cookies and the same access code
                try:
                    b64 = page.evaluate(
                        "async (u) => { const r = await fetch(u, {credentials: 'include'});"
                        " const a = new Uint8Array(await r.arrayBuffer()); let s = '';"
                        " for (let i = 0; i < a.length; i += 0x8000)"
                        "   s += String.fromCharCode.apply(null, a.subarray(i, i + 0x8000));"
                        " return btoa(s); }",
                        page.url,
                    )
                    import base64

                    body = base64.b64decode(b64)
                    if body[:4] == b"%PDF":
                        got["body"] = body
                except Exception as exc:  # noqa: BLE001
                    print(f"  pdf refetch failed: {str(exc)[:80]}")
                if not got:
                    break
    finally:
        page.remove_listener("response", on_response)
    return got.get("body")


def month_in_range(y: int, m: int, d0: dt.date, d1: dt.date) -> bool:
    first = dt.date(y, m, 1)
    last = dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
    return first <= d1 and last >= d0


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
    text_dir = out / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    corpus = CORPUS / slug
    corpus.mkdir(parents=True, exist_ok=True)
    rows_path = out / "pages.jsonl"
    have = set()
    if rows_path.exists():
        for ln in rows_path.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                have.add(json.loads(ln)["name"])
    log = (corpus / "pull.log").open("a", encoding="utf-8")

    def note(msg: str) -> None:
        print(msg, flush=True)
        log.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
        log.flush()

    pw, browser, page = connect()
    done = 0
    try:
        if code is None:
            html = goto(page, f"{SITE}?a=cl&cl=CL1&e={E}", delay)
            codes = title_codes(html).get(title.lower(), [])
            if not codes:
                sys.exit(f"title {title!r} not found on the title list; pass --code")
            if len(codes) > 1:
                sys.exit(f"title {title!r} has several codes {codes}; pass --code")
            code = codes[0]
        note(f"title {title!r} code {code}; {start}..{end}")

        html = goto(page, f"{SITE}?a=cl&cl=CL1&sp={code}&e={E}", delay)
        months = sorted(
            {
                (int(m.group("y")), int(m.group("m")))
                for m in MONTH_LINK.finditer(html)
                if m.group("code") == code
            }
        )
        months = [(y, m) for y, m in months if month_in_range(y, m, d0, d1)]
        note(f"{len(months)} months in range on the browse page")

        issues: list[tuple[str, str]] = []
        for y, m in months:
            html = goto(page, f"{SITE}?a=cl&cl=CL2.{y}.{m:02d}&sp={code}&e={E}", delay)
            found = {
                (mm.group("date"), mm.group("ed"))
                for mm in ISSUE_LINK.finditer(html)
                if mm.group("code") == code
            }
            if not found:
                vt = re.findall(r"<title>(.*?)</title>", html, re.S)[:1]
                note(f"month {y}-{m:02d}: no issue links (title {vt})")
            issues.extend((d, e) for d, e in found if d0 <= dt.date.fromisoformat(iso(d)) <= d1)
        issues = sorted(set(issues))
        note(f"{len(issues)} issues in {start}..{end}")

        for date8, ed in issues:
            issue_id = f"{code}{date8}-{ed}"
            html = goto(page, f"{SITE}?a=d&d={issue_id}&e={E}", delay)
            pages = sorted(
                {
                    int(mm.group("page"))
                    for mm in PAGE_LINK.finditer(html)
                    if mm.group("date") == date8 and mm.group("ed") == ed
                }
            ) or [1]
            for n in pages:
                if limit is not None and done >= limit:
                    note("limit reached")
                    return 0
                name = page_name(slug, date8, ed, n)
                oid = f"{issue_id}.1.{n}"
                txt_path = text_dir / f"{name}.txt"
                pdf_path = corpus / f"{name}.pdf"
                need_text = name not in have
                need_pdf = want_pdf and not pdf_path.exists()
                if not need_text and not need_pdf:
                    continue
                rec = {
                    "name": name,
                    "title": title,
                    "date": iso(date8),
                    "ed": int(ed),
                    "page": n,
                    "oid": oid,
                }
                if need_text:
                    view = goto(page, f"{SITE}?a=d&d={oid}&dliv=none&st=1&e={E}", delay)
                    text = text_from_view(view)
                    if not text:
                        vt = re.findall(r"<title>(.*?)</title>", view, re.S)[:1]
                        note(f"{name}: no text in view (title {vt})")
                    txt_path.write_text(text, encoding="utf-8")
                    rec["words"] = len(text.split())
                if need_pdf:
                    body = fetch_pdf(page, oid)
                    if body:
                        pdf_path.write_bytes(body)
                        rec["pdf_sha256"] = hashlib.sha256(body).hexdigest()
                        rec["pdf_bytes"] = len(body)
                    else:
                        note(f"{name}: pdf not received")
                    time.sleep(delay)
                if need_text:
                    with rows_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(rec) + "\n")
                    have.add(name)
                done += 1
                extra = f", pdf {rec['pdf_bytes']:,} B" if "pdf_bytes" in rec else ""
                note(f"{name}: {rec.get('words', '-')} words{extra}")
    finally:
        pw.stop()
        log.close()
    print(f"done: {done} pages this run -> {out} (text) / {corpus} (pdf, log)")
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
    q.add_argument("--delay", type=float, default=1.5)
    q.add_argument("--pdf", action="store_true", help="also save each page's PDF")
    q.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    if a.cmd == "probe":
        return probe(a.url, a.delay)
    return pull(a.title, a.code, a.start, a.end, a.delay, a.pdf, a.limit)


if __name__ == "__main__":
    sys.exit(main())
