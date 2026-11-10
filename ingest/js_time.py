"""Fetch the comparison texts for BOM-73 listed in ``data/js_time/controls.json``.

BOM-73 measures whether writing after 1830 moved toward the Book of Mormon's style
(``docs/js-over-time-plan.md``). Joseph Smith's documents come from the Joseph Smith Papers through
``ingest.candidates`` (``data/js_time/sources.json``); this module fetches the comparison writers
from the Internet Archive: the unexposed group (religious writers with no documented reading of the
book) and Alexander Campbell, who read and reviewed it, reported as a line of his own.

Each manifest entry names one Internet Archive item, its group, the writer or periodical, and the
year its contents were written, checked against the item's own volume and issue data (the
Archive's ``year`` field is often a series' start year). The OCR text (``<identifier>_djvu.txt``)
goes to ``data/corpus/js_time/text/<id>.txt``; all items are public domain and anyone can fetch
them again, so the text stays out of git and is covered by a checksum manifest.

The fetcher identifies itself, sleeps between requests, and skips any output already on disk. A
failed request writes nothing, so a rerun picks it up.

Usage::

    python -m ingest.js_time --check
    python -m ingest.js_time [--limit N] [--delay 1.0]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ingest import jsp
from ingest.candidates import IA_RE, ID_RE, ia_text_url

MANIFEST = Path("data/js_time/controls.json")
OUT_DIR = Path("data/corpus/js_time/text")
GROUPS = ("unexposed", "campbell")
REQUIRED = ("id", "group", "writer", "title", "url", "year")


def validate(entries: list[dict]) -> list[str]:
    errs, seen = [], set()
    for e in entries:
        eid = e.get("id", "?")
        errs += [f"{eid}: missing {k}" for k in REQUIRED if k not in e]
        if any(k not in e for k in REQUIRED):
            continue
        if not ID_RE.match(eid):
            errs.append(f"{eid}: id must be lowercase words joined by hyphens")
        if e["group"] not in GROUPS:
            errs.append(f"{eid}: unknown group {e['group']!r}")
        if not IA_RE.match(e["url"]):
            errs.append(f"{eid}: url must be https://archive.org/details/<identifier>")
        if not isinstance(e["year"], int) or not 1829 <= e["year"] <= 1844:
            errs.append(f"{eid}: year must be an integer from 1829 to 1844")
        if eid in seen:
            errs.append(f"{eid}: duplicate id")
        seen.add(eid)
    return errs


def load(path: Path = MANIFEST) -> list[dict]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    errs = validate(entries)
    if errs:
        raise ValueError("invalid manifest:\n" + "\n".join(errs))
    return entries


def run(entries: list[dict], delay: float, limit: int | None, root: Path = Path(".")) -> int:
    done = 0
    for e in entries:
        out = root / OUT_DIR / f"{e['id']}.txt"
        if out.exists():
            continue
        if limit is not None and done >= limit:
            break
        print(f"fetch {e['id']} ({e['year']}, {e['writer']})", flush=True)
        try:
            text = jsp.fetch(ia_text_url(e))
        except Exception as exc:  # noqa: BLE001 - transient: nothing written, a rerun retries
            print(f"failed {e['id']}: {exc}", file=sys.stderr, flush=True)
            jsp.pause(delay)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".part")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(out)
        done += 1
        jsp.pause(delay)
    return done


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    ap.add_argument("--check", action="store_true", help="validate the manifest and exit")
    ap.add_argument("--limit", type=int, help="fetch at most N new items")
    ap.add_argument("--delay", type=float, default=1.0, help="mean seconds between requests")
    a = ap.parse_args(argv)
    entries = load(a.manifest)
    if a.check:
        print(f"{len(entries)} items ok")
        return 0
    print(f"wrote {run(entries, a.delay, a.limit)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
