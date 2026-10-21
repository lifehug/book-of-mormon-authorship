"""Chronicling America newspapers, 1800-1830 (BOM-10).

The Library of Congress serves Chronicling America through the loc.gov JSON API (no key).
``https://www.loc.gov/collections/chronicling-america/?dates=1800/1830&fo=json`` reports
39,836 records, but those are 39,574 newspaper *issues* plus 262 title records; the
page-level ("Pages (Full Text)") records are not listable from the collection endpoint,
only one issue at a time. So the catalog lists issues (``fa=type:issue``, 160 per request)
and expands each into pages: an issue result carries its page count (``segments``) and the
first page's image URL, which embeds the batch path and the first scan number
(``.../1820040101:0035``). NDNP numbers an issue's scans consecutively, so page ``n`` is the
first number plus ``n - 1``; every derived URL is checked by ``pull`` (a bad one lands in
the failed list). Page text is served by the text service on ``tile.loc.gov`` as JSON
carrying the ALTO ``full_text``.

Rate limits (loc.gov "Working Within Limits"): JSON API 20 requests/minute, text and image
services 150/minute, one hour block when exceeded. Defaults here are 3.5 s between API
calls and 0.5 s between text calls, with exponential backoff on HTTP 429.

``catalog``
    Writes ``data/catalog/chronicling_america.jsonl.gz`` (one row per page: page url, lccn,
    title, date, state, city, edition, sequence, OCR url) and
    ``data/catalog/chronicling_america_summary.md``. About 250 API requests.

``pull``
    Fetches each page's OCR text into
    ``data/corpus/chronicling_america/text/<lccn>/<date>-ed<e>-seq<s>.txt``. Resumable;
    failures are listed in ``data/corpus/chronicling_america/failed.txt``.

    Slow, and not because of a rate limit: ``tile.loc.gov`` returns HTTP 500 often enough that
    most of each page's time is spent in backoff. Measured at 0.5-3 pages/min, which is about
    219 days for all 159,146. Prefer ``bulk``.

``bulk``
    Extracts the same pages from the batch tarballs the Library of Congress publishes for text
    and data mining, which is hours rather than months. The tarballs cannot be fetched by
    script -- Cloudflare answers with a challenge page -- so a person downloads them in a
    browser first; ``docs/chronam-bulk-download.md`` is the walkthrough and
    ``scripts/chronam_status.py`` tracks which are still missing.

    Each archive is verified against the ``sha256`` in
    ``data/catalog/chronicling_america_batches.json`` before anything is read out of it. Only
    pages named in the catalog are extracted; a batch also holds pages outside 1780-1830 and
    those are skipped. Finished batches are recorded in ``batches_done.txt`` and their tarballs
    deleted, so the 69 GB of archives does not have to be kept.

Usage::

    python -m ingest.chronicling_america catalog
    python -m ingest.chronicling_america pull [--limit N] [--states NY,PA,OH]
    python -m ingest.chronicling_america bulk [--incoming DIR] [--limit N] [--discard-tarball]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import tarfile
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

LIST_URL = (
    "https://www.loc.gov/collections/chronicling-america/"
    "?dates=1800/1830&fo=json&fa=type:issue&c=160&sp={sp}"
)
TEXT_URL = (
    "https://tile.loc.gov/text-services/word-coordinates-service"
    "?segment={segment}&format=alto_xml&full_text=1"
)
CATALOG = Path("data/catalog/chronicling_america.jsonl.gz")  # 159k rows; gzipped for GitHub
SUMMARY = Path("data/catalog/chronicling_america_summary.md")
# The 76 batches holding our pages, with the size and sha256 the Library of Congress publishes.
BATCHES = Path("data/catalog/chronicling_america_batches.json")
CORPUS = Path("data/corpus/chronicling_america")
# Where the hand-downloaded tarballs land (docs/chronam-bulk-download.md).
INCOMING = Path("/Volumes/bomdata/incoming/chronam")
USER_AGENT = "bom-authorship-research/0.1 (+https://github.com/lifehug/book-of-mormon-authorship)"
PRIORITY = {"New York": "NY", "Pennsylvania": "PA", "Ohio": "OH"}
STATE_CODES = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "district of columbia": "DC",
    "florida": "FL", "georgia": "GA", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "nebraska": "NE", "new hampshire": "NH", "new jersey": "NJ",
    "new york": "NY", "north carolina": "NC", "ohio": "OH", "oklahoma": "OK",
    "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "tennessee": "TN",
    "texas": "TX", "vermont": "VT", "virginia": "VA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY",
}  # fmt: skip
IMAGE_RE = re.compile(r"iiif/service:((?:ndnp|sgp):[^/]+?:data:[^/]+?):(\d+)/")
# Traditional (GPO) abbreviations, as in "Wilmington, Del." in place-of-publication fields.
ABBREV = {
    "ala": "Alabama", "ariz": "Arizona", "ark": "Arkansas", "calif": "California",
    "colo": "Colorado", "conn": "Connecticut", "del": "Delaware", "d.c": "District of Columbia",
    "fla": "Florida", "ga": "Georgia", "ill": "Illinois", "ind": "Indiana", "kan": "Kansas",
    "ky": "Kentucky", "la": "Louisiana", "me": "Maine", "md": "Maryland", "mass": "Massachusetts",
    "mich": "Michigan", "minn": "Minnesota", "miss": "Mississippi", "mo": "Missouri",
    "n.h": "New Hampshire", "n.j": "New Jersey", "n.y": "New York", "n.c": "North Carolina",
    "r.i": "Rhode Island", "s.c": "South Carolina", "tenn": "Tennessee", "tex": "Texas",
    "vt": "Vermont", "va": "Virginia", "w. va": "West Virginia", "w.va": "West Virginia",
    "wis": "Wisconsin", "pa": "Pennsylvania", "penn": "Pennsylvania",
}  # fmt: skip

ID_RE = re.compile(r"/item/([^/]+)/(\d{4}-\d{2}-\d{2})/ed-(\d+)/")


def fetch(url: str, retries: int = 6) -> bytes:
    """GET with the project User-Agent; exponential backoff, longer on 429."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404 or attempt == retries - 1:
                raise
            wait = 60 * 2**attempt if exc.code == 429 else 5 * 2**attempt
        except Exception:  # noqa: BLE001
            if attempt == retries - 1:
                raise
            wait = 5 * 2**attempt
        print(f"retry {attempt + 1} in {wait}s for {url}", file=sys.stderr)
        time.sleep(wait)
    raise RuntimeError("unreachable")


def state_code(name: str) -> str:
    return STATE_CODES.get(name.lower(), name.upper()[:2])


def segment_path(prefix: str, num: int, width: int) -> str:
    """The ALTO file path the text service expects. ``prefix`` is the image-service path
    with colons, e.g. ``ndnp:msar:batch_x:data:2018270507:00414212621:1820040101``."""
    return f"/service/{prefix.replace(':', '/')}/{num:0{width}d}.xml"


def proper(name: str) -> str:
    return name.title().replace(" Of ", " of ")


def guess_state(place: str) -> str:
    """State from a place-of-publication string such as 'Wilmington, Del.'."""
    tail = place.rsplit(",", 1)[-1].strip().strip("()[].").lower().rstrip(".")
    return ABBREV.get(tail, "")


def expand_issue(result: dict) -> list[dict]:
    """One catalog row per page of an issue result; [] if it is not a usable issue."""
    m = ID_RE.search(result.get("id", ""))
    if not m:
        return []
    lccn, date, ed = m.group(1), m.group(2), int(m.group(3))
    item = result.get("item", {})
    res = (result.get("resources") or [{}])[0]
    n_pages = int(res.get("segments") or 0)
    im = IMAGE_RE.search(res.get("image", ""))
    states = result.get("location_state") or [""]
    cities = result.get("location_city") or [""]
    titles = item.get("newspaper_title") or [result.get("title", "")]
    base = {
        "lccn": lccn,
        "title": titles[0].strip(),
        "date": date,
        "state": proper(states[0] or guess_state(item.get("place_of_publication", ""))),
        "city": proper(cities[0]),
        "edition": ed,
    }
    rows = []
    for seq in range(1, n_pages + 1):
        row = dict(
            base,
            sequence=seq,
            page_url=f"https://www.loc.gov/resource/{lccn}/{date}/ed-{ed}/?sp={seq}",
        )
        row["ocr_url"] = None
        if im:
            prefix, first = im.groups()
            seg = segment_path(prefix, int(first) + seq - 1, len(first))
            row["ocr_url"] = TEXT_URL.format(segment=seg)
        rows.append(row)
    return rows


def catalog(delay: float) -> int:
    rows: list[dict] = []
    skipped: list[str] = []
    sp, last = 1, None
    while last is None or sp <= last:
        d = json.loads(fetch(LIST_URL.format(sp=sp)))
        last = d["pagination"]["total"]
        for res in d["results"]:
            got = expand_issue(res)
            rows.extend(got)
            if not got:
                skipped.append(res.get("id", "?"))
        print(f"  list page {sp}/{last}: {len(rows):,} pages", flush=True)
        sp += 1
        time.sleep(delay)
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(CATALOG, "wt", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_summary(rows, skipped)
    print(SUMMARY.read_text())
    print(f"wrote {len(rows):,} records to {CATALOG}")
    return 0


def write_summary(rows: list[dict], skipped: list[str]) -> None:
    by_state = Counter(r["state"] for r in rows)
    by_decade = Counter(int(r["date"][:4]) // 10 * 10 for r in rows)
    by_title = Counter((r["title"], r["lccn"], r["state"]) for r in rows)
    issues = len({(r["lccn"], r["date"], r["edition"]) for r in rows})
    lines = [
        "# Chronicling America, 1800-1830",
        "",
        "Source: loc.gov JSON API, `fa=type:issue`, `dates=1800/1830`. Pages are derived from",
        "each issue's page count and first scan number (see `ingest/chronicling_america.py`).",
        "",
        f"- Pages: {len(rows):,}",
        f"- Issues: {issues:,}",
        f"- Titles (LCCNs): {len({r['lccn'] for r in rows}):,}",
        f"- Issue records skipped (no pages or unparseable id): {len(skipped):,}",
        f"- Pages without a derivable OCR url: {sum(1 for r in rows if not r['ocr_url']):,}",
        "",
        "Priority states (New York, Pennsylvania, Ohio):",
        "",
        "| State | Pages |",
        "| --- | --- |",
    ]
    for s in PRIORITY:
        lines.append(f"| {s} | {by_state.get(s, 0):,} |")
    lines += ["", "## By state", "", "| State | Pages |", "| --- | --- |"]
    lines += [f"| {s or '(none)'} | {n:,} |" for s, n in by_state.most_common()]
    lines += ["", "## By decade", "", "| Decade | Pages |", "| --- | --- |"]
    lines += [f"| {d}s | {by_decade[d]:,} |" for d in sorted(by_decade)]
    lines += [
        "",
        "## Top 20 titles",
        "",
        "| Title | LCCN | State | Pages |",
        "| --- | --- | --- | --- |",
    ]
    lines += [f"| {t} | {lc} | {st} | {n:,} |" for (t, lc, st), n in by_title.most_common(20)]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


def page_path(row: dict, ext: str = "txt") -> Path:
    name = f"{row['date']}-ed{row['edition']}-seq{row['sequence']}.{ext}"
    sub = "text" if ext == "txt" else "alto"
    return CORPUS / sub / row["lccn"] / name


# A batch member looks like ``sn84024011/1800/12/08/ed-1/seq-1/ocr.txt``; the same page is
# ``text/sn84024011/1800-12-08-ed1-seq1.txt`` on disk, so both routes agree.
# The LCCN segment is not always ``sn`` plus digits: a few catalog rows carry a bare numeric
# LCCN such as ``2018270507``, so match any non-slash run rather than a prefix shape.
# Both members are kept. An earlier version matched only ocr.txt and counted every ocr.xml as
# "skipped", discarding the ALTO for all 158,960 pages -- which is where the per-word confidence
# (WC), per-character confidence (CC) and word coordinates live. That is a direct OCR-quality
# measurement for the whole corpus and the only thing that gives column-aware reading order, and
# it was thrown away to save space on a disk with 1.6 TB free. See CLAUDE.md: keep originals and
# intermediate artifacts, flag rather than delete.
MEMBER = re.compile(
    r"(?:^|/)(?P<lccn>[^/]+)/(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2})/"
    r"ed-(?P<ed>\d+)/seq-(?P<seq>\d+)/ocr\.(?P<ext>txt|xml)$"
)


def member_ext(name: str) -> str | None:
    """``txt`` or ``xml`` for an OCR member, else None."""
    m = MEMBER.search(name)
    return m.group("ext") if m else None


def member_key(name: str) -> tuple[str, str, str, str] | None:
    """``(lccn, date, edition, sequence)`` for an OCR member, or None if it is not one."""
    m = MEMBER.search(name)
    if not m:
        return None
    return (
        m["lccn"],
        f"{m['y']}-{m['m']}-{m['d']}",
        str(int(m["ed"])),
        str(int(m["seq"])),
    )


def sha256_of(path: Path, chunk: int = 1 << 22) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def bulk(incoming: Path, limit: int | None, discard: bool = False) -> int:
    """Extract catalogued pages from downloaded batch tarballs."""
    if not BATCHES.exists():
        print(f"no batch manifest at {BATCHES}", file=sys.stderr)
        return 1
    expect = {b["batch"]: b for b in json.loads(BATCHES.read_text())}

    with gzip.open(CATALOG, "rt", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh]
    # Key every catalogued page so a tar member can be matched in one lookup.
    want = {
        (r["lccn"], r["date"], str(r["edition"]), str(r["sequence"])): r
        for r in rows
        if r.get("ocr_url")
    }

    done_file = CORPUS / "batches_done.txt"
    done = set(done_file.read_text().split()) if done_file.exists() else set()
    tarballs = sorted(p for p in incoming.glob("*.tar.bz2") if p.stem[:-4] not in done)
    if limit:
        tarballs = tarballs[:limit]
    print(f"{len(tarballs)} batch(es) to extract; {len(done)} already done")

    CORPUS.mkdir(parents=True, exist_ok=True)
    total_new = total_skip = 0
    for path in tarballs:
        batch = path.name[: -len(".tar.bz2")]
        rec = expect.get(batch)
        if rec and rec.get("sha256"):
            if sha256_of(path) != rec["sha256"]:
                print(f"  {batch}: SHA256 MISMATCH, leaving in place", file=sys.stderr)
                continue
        new = skip = 0
        # Streamed ("r|bz2"): the archives are up to 3.4 GB and only read once.
        with tarfile.open(path, "r|bz2") as tar:
            for member in tar:
                if not member.isfile():
                    continue
                key = member_key(member.name)
                ext = member_ext(member.name)
                if key is None or ext is None or key not in want:
                    skip += 1
                    continue
                out = page_path(want[key], ext)
                if out.exists():
                    skip += 1
                    continue
                handle = tar.extractfile(member)
                if handle is None:
                    continue
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(handle.read())
                new += 1
        total_new += new
        total_skip += skip
        done.add(batch)
        done_file.write_text("\n".join(sorted(done)) + "\n")
        # Deleting the source archive is opt-in. It used to be the default, which cost the
        # project the ALTO for every page it had already extracted.
        if discard:
            path.unlink()
        tail = ", tarball deleted" if discard else ""
        print(f"  {batch}: +{new:,} files (skipped {skip:,}){tail}")
    have = sum(1 for r in rows if r.get("ocr_url") and page_path(r).exists())
    print(f"extracted {total_new:,} new pages; {have:,}/{len(want):,} of the catalog on disk")
    return 0


def parse_text(payload: bytes) -> str:
    """Page text from the text-service JSON ({segment: {"full_text": ...}})."""
    data = json.loads(payload)
    return "\n".join(v.get("full_text", "") for v in data.values() if isinstance(v, dict))


_HEADLINE = re.compile(r"^[^a-z]*[A-Z]{3}[^a-z]*$")


def split_articles(text: str) -> list[str]:
    """Split page OCR into rough articles at blank lines and all-caps headline lines."""
    articles: list[list[str]] = []
    cur: list[str] = []
    prev_blank = True
    for line in text.splitlines():
        s = line.strip()
        if not s:
            prev_blank = True
            continue
        is_head = bool(_HEADLINE.match(s)) and len(s) <= 80
        if cur and (prev_blank or is_head) and (is_head or len(" ".join(cur)) > 200):
            articles.append(cur)
            cur = []
        cur.append(s)
        prev_blank = False
    if cur:
        articles.append(cur)
    return [" ".join(a) for a in articles]


def pull(limit: int | None, delay: float, states: set[str] | None) -> int:
    with gzip.open(CATALOG, "rt", encoding="utf-8") as fh:
        recs = [json.loads(line) for line in fh]
    if states:
        recs = [r for r in recs if state_code(r["state"]) in states]
    recs = [r for r in recs if r["ocr_url"]]
    todo = [r for r in recs if not page_path(r).exists()]
    print(f"{len(recs):,} pages in scope; {len(recs) - len(todo):,} done; {len(todo):,} to fetch")
    CORPUS.mkdir(parents=True, exist_ok=True)
    failed = CORPUS / "failed.txt"
    n = 0
    for r in todo:
        path = page_path(r)
        try:
            text = parse_text(fetch(r["ocr_url"]))
            if not text.strip():
                raise ValueError("empty text")
        except Exception as exc:  # noqa: BLE001
            with failed.open("a") as fh:
                fh.write(f"{r['page_url']}\t{exc}\n")
            time.sleep(delay)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        n += 1
        if n % 500 == 0:
            print(f"  fetched {n:,}/{len(todo):,}", flush=True)
        if limit and n >= limit:
            print(f"stopped at --limit {limit}")
            break
        time.sleep(delay)
    print(f"fetched {n:,} pages into {CORPUS}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("catalog")
    c.add_argument("--delay", type=float, default=3.5)
    p = sub.add_parser("pull")
    p.add_argument("--limit", type=int)
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--states", help="comma-separated codes, e.g. NY,PA,OH")
    b = sub.add_parser("bulk")
    b.add_argument("--incoming", type=Path, default=INCOMING)
    b.add_argument("--limit", type=int, help="only this many batches")
    b.add_argument(
        "--discard-tarball",
        action="store_true",
        help="delete each tarball after extracting it (off by default; it is the original)",
    )
    a = ap.parse_args(argv)
    if a.cmd == "catalog":
        return catalog(a.delay)
    if a.cmd == "bulk":
        return bulk(a.incoming, a.limit, a.discard_tarball)
    states = {s.strip().upper() for s in a.states.split(",")} if a.states else None
    return pull(a.limit, a.delay, states)


if __name__ == "__main__":
    sys.exit(main())
