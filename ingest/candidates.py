"""Fetch candidate-author texts listed in ``data/candidates/sources.json`` (BOM-13).

The manifest names every source for the eight candidate authors (see ``docs/candidates.md``).
Two kinds are fetched here:

- ``ia_djvu``: an Internet Archive item's OCR text (``<identifier>_djvu.txt`` unless the entry
  gives ``file``). Public-domain items go to ``data/candidates/text/<id>.txt``; items whose
  Internet Archive rights field claims a copyright on the scan are marked ``private`` and go
  to ``data/private/candidates/<id>.txt``.
- ``jsp_page``: a Joseph Smith Papers document, every page pulled through
  ``ingest.jsp.page_props`` and ``ingest.jsp.extract``. JSP transcripts are copyright
  Intellectual Reserve, so these are always private: raw page JSON under
  ``data/private/candidates/raw/<id>/`` and one record per page in
  ``data/private/candidates/<id>.jsonl``.

``wikisource`` and ``other`` entries are inventory only for now and are skipped.

The fetcher identifies itself, sleeps between requests, and skips any output already on disk.

Usage::

    python -m ingest.candidates --check            # validate the manifest only
    python -m ingest.candidates --public-only --limit 2
    python -m ingest.candidates --id js-1832-history
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

from ingest import jsp

MANIFEST = Path("data/candidates/sources.json")
PUBLIC_DIR = Path("data/candidates/text")
PRIVATE_DIR = Path("data/private/candidates")

REQUIRED = ("id", "candidate", "title", "url", "kind", "provenance", "license", "private")
KINDS = ("ia_djvu", "jsp_page", "wikisource", "other")
FETCHABLE = ("ia_djvu", "jsp_page")
PROVENANCE = (
    "handwritten",  # in the candidate's own hand
    "dictated",  # spoken by the candidate, written by a scribe
    "scribal_copy",  # a later copy by someone else of a lost original
    "mixed",  # several hands in one document; split by hand notes before use
    "printed_by_author",  # published in the candidate's lifetime under their name
    "edited",  # a periodical or work where others shaped or added the text
    "posthumous",  # published after the candidate's death
)
CANDIDATES = (
    "Joseph Smith",
    "Oliver Cowdery",
    "Sidney Rigdon",
    "Parley P. Pratt",
    "W. W. Phelps",
    "Solomon Spalding",
    "Ethan Smith",
    "Gilbert J. Hunt",
)
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IA_RE = re.compile(r"^https://archive\.org/details/([A-Za-z0-9._-]+)$")
JSP_RE = re.compile(r"^https://www\.josephsmithpapers\.org/paper-summary/([a-z0-9-]+)$")


def validate_entry(e: dict) -> list[str]:
    """Problems with one manifest entry (empty list if it is valid)."""
    eid = e.get("id", "?")
    errs = [f"{eid}: missing {k}" for k in REQUIRED if k not in e]
    if errs:
        return errs
    if not ID_RE.match(e["id"]):
        errs.append(f"{eid}: id must be lowercase words joined by hyphens")
    if e["candidate"] not in CANDIDATES:
        errs.append(f"{eid}: unknown candidate {e['candidate']!r}")
    if e["kind"] not in KINDS:
        errs.append(f"{eid}: unknown kind {e['kind']!r}")
    if e["provenance"] not in PROVENANCE:
        errs.append(f"{eid}: unknown provenance {e['provenance']!r}")
    if not isinstance(e["private"], bool):
        errs.append(f"{eid}: private must be true or false")
    if e["kind"] == "ia_djvu" and not IA_RE.match(e["url"]):
        errs.append(f"{eid}: ia_djvu url must be https://archive.org/details/<identifier>")
    if "edition_of" in e and e["edition_of"] == e["id"]:
        errs.append(f"{eid}: edition_of must name a different source")
    if e["kind"] == "jsp_page":
        if not JSP_RE.match(e["url"]):
            errs.append(f"{eid}: jsp_page url must be .../paper-summary/<slug> with no page")
        if e["private"] is not True:
            errs.append(
                f"{eid}: Joseph Smith Papers transcripts are copyrighted; private must be true"
            )
    return errs


def validate_manifest(entries: list[dict]) -> list[str]:
    errs: list[str] = []
    seen: set[str] = set()
    for e in entries:
        errs.extend(validate_entry(e))
        eid = e.get("id")
        if eid in seen:
            errs.append(f"{eid}: duplicate id")
        seen.add(eid)
    return errs


def load_manifest(path: Path = MANIFEST) -> list[dict]:
    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    errs = validate_manifest(entries)
    if errs:
        raise ValueError("invalid manifest:\n" + "\n".join(errs))
    return entries


def ia_identifier(url: str) -> str:
    m = IA_RE.match(url)
    if not m:
        raise ValueError(f"not an Internet Archive details url: {url}")
    return m.group(1)


def ia_text_url(entry: dict) -> str:
    ident = ia_identifier(entry["url"])
    name = entry.get("file") or f"{ident}_djvu.txt"
    return f"https://archive.org/download/{ident}/{urllib.parse.quote(name)}"


def jsp_slug(url: str) -> str:
    m = JSP_RE.match(url)
    if not m:
        raise ValueError(f"not a Joseph Smith Papers paper-summary url: {url}")
    return m.group(1)


def output_path(entry: dict, root: Path = Path(".")) -> Path | None:
    """Where a fetched source is written, or None if this kind is not fetched."""
    kind = entry["kind"]
    if kind == "ia_djvu":
        base = PRIVATE_DIR if entry["private"] else PUBLIC_DIR
        return root / base / f"{entry['id']}.txt"
    if kind == "jsp_page":
        return root / PRIVATE_DIR / f"{entry['id']}.jsonl"
    return None


def raw_dir(entry: dict, root: Path = Path(".")) -> Path:
    return root / PRIVATE_DIR / "raw" / entry["id"]


def fetch_ia(entry: dict, out: Path) -> None:
    text = jsp.fetch(ia_text_url(entry))
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(out)


def fetch_jsp(
    entry: dict, out: Path, delay: float, max_pages: int | None, root: Path, offline: bool = False
) -> None:
    slug = jsp_slug(entry["url"])
    rdir = raw_dir(entry, root)
    rdir.mkdir(parents=True, exist_ok=True)

    def page(n: int) -> dict:
        path = rdir / f"{n:04d}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        if offline:
            raise FileNotFoundError(f"{path}: not on disk and --rebuild never fetches")
        props = jsp.page_props(
            jsp.fetch(
                f"{jsp.BASE}{slug}/{n}", user_agent=jsp.JSP_USER_AGENT, backoff=jsp.JSP_BACKOFF
            )
        )
        path.write_text(json.dumps(props), encoding="utf-8")
        jsp.pause(delay)
        return props

    total = int(page(1)["summary"]["numberOfPages"])
    if max_pages:
        total = min(total, max_pages)
    records = [jsp.extract(page(n), n) for n in range(1, total + 1)]
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def select(
    entries: list[dict], ids: list[str] | None = None, public_only: bool = False
) -> list[dict]:
    """Fetchable entries, filtered by id and privacy, in manifest order."""
    chosen = [e for e in entries if e["kind"] in FETCHABLE]
    if ids:
        unknown = set(ids) - {e["id"] for e in entries}
        if unknown:
            raise ValueError(f"unknown ids: {sorted(unknown)}")
        chosen = [e for e in chosen if e["id"] in ids]
    if public_only:
        chosen = [e for e in chosen if not e["private"]]
    return chosen


def run(
    entries: list[dict],
    root: Path = Path("."),
    delay: float = jsp.JSP_DELAY,
    limit: int | None = None,
    max_pages: int | None = None,
    rebuild: bool = False,
) -> list[Path]:
    """Fetch up to ``limit`` sources not already on disk; return the files written.

    With ``rebuild``, rewrite each JSP output from its raw pages on disk instead (after a change
    to ``jsp.extract``); nothing is fetched and IA files are left alone.
    """
    written: list[Path] = []
    for e in entries:
        if limit is not None and len(written) >= limit:
            break
        out = output_path(e, root)
        if out is None:
            continue
        if rebuild:
            if e["kind"] == "ia_djvu":
                continue
            print(f"rebuild {e['id']} from {raw_dir(e, root)}", flush=True)
            fetch_jsp(e, out, delay, max_pages, root, offline=True)
            written.append(out)
            continue
        if out.exists():
            print(f"skip {e['id']}: {out} exists", flush=True)
            continue
        print(f"fetch {e['id']} ({e['kind']}) -> {out}", flush=True)
        if e["kind"] == "ia_djvu":
            fetch_ia(e, out)
            time.sleep(delay)
        else:
            fetch_jsp(e, out, delay, max_pages, root)
        written.append(out)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--id", action="append", dest="ids", help="fetch only this id (repeatable)")
    ap.add_argument("--public-only", action="store_true", help="skip private sources")
    ap.add_argument("--limit", type=int, help="fetch at most N new sources")
    ap.add_argument("--max-pages", type=int, help="JSP: fetch only the first N pages (testing)")
    ap.add_argument("--delay", type=float, default=jsp.JSP_DELAY, help="seconds between requests")
    ap.add_argument("--check", action="store_true", help="validate the manifest and exit")
    ap.add_argument(
        "--rebuild", action="store_true", help="JSP: rewrite outputs from raw pages, no fetching"
    )
    a = ap.parse_args(argv)
    entries = load_manifest(a.manifest)
    if a.check:
        n_priv = sum(e["private"] for e in entries)
        print(f"{len(entries)} sources ok ({n_priv} private, {len(entries) - n_priv} public)")
        return 0
    todo = select(entries, a.ids, a.public_only)
    written = run(todo, delay=a.delay, limit=a.limit, max_pages=a.max_pages, rebuild=a.rebuild)
    print(f"wrote {len(written)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
