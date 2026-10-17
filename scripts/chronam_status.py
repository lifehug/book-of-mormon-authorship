#!/usr/bin/env python3
"""Which Chronicling America bulk batches are downloaded, and which are still missing (BOM-10).

The batches are downloaded by hand in a browser (``docs/chronam-bulk-download.md``), so this
reports progress against the full list derived from the catalog: what has landed, what has
been extracted already, and what is left, ranked so the most valuable missing batch is first.

Usage::

    python scripts/chronam_status.py              # summary plus the next few to fetch
    python scripts/chronam_status.py --missing    # every missing batch, with links
    python scripts/chronam_status.py --links 10   # links for the next 10 only
"""

from __future__ import annotations

import argparse
import collections
import gzip
import json
from pathlib import Path

CATALOG = Path("data/catalog/chronicling_america.jsonl.gz")
# Where the browser puts them, and where they go once Claude has filed them.
SEARCH_DIRS = [Path.home() / "Downloads", Path("/Volumes/bomdata/incoming/chronam")]
EXTRACTED = Path("data/corpus/chronicling_america/batches_done.txt")
URL = "https://chroniclingamerica.loc.gov/data/ocr/{batch}.tar.bz2"


def wanted_batches() -> collections.Counter:
    """Batch name -> how many of our 1800-1830 pages it holds."""
    counts: collections.Counter = collections.Counter()
    with gzip.open(CATALOG, "rt", encoding="utf-8") as fh:
        for line in fh:
            url = json.loads(line).get("ocr_url", "")
            if "batch_" in url:
                counts[url.split("batch_", 1)[1].split("/", 1)[0]] += 1
    return counts


def on_disk() -> set[str]:
    """Batches whose tarball is sitting in one of the download folders."""
    found = set()
    for d in SEARCH_DIRS:
        if d.is_dir():
            found |= {p.name[: -len(".tar.bz2")] for p in d.glob("*.tar.bz2")}
    return found


def extracted() -> set[str]:
    """Batches already extracted and deleted; recorded so they are not re-downloaded."""
    if not EXTRACTED.exists():
        return set()
    return {ln.strip() for ln in EXTRACTED.read_text().splitlines() if ln.strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--missing", action="store_true", help="list every missing batch")
    ap.add_argument("--links", type=int, default=0, help="print links for the next N")
    args = ap.parse_args()

    counts = wanted_batches()
    have_file, have_done = on_disk(), extracted()
    have = have_file | have_done
    total_pages = sum(counts.values())
    got_pages = sum(k for b, k in counts.items() if b in have)
    missing = [(b, k) for b, k in counts.most_common() if b not in have]

    where = f"{len(have_file)} on disk, {len(have_done)} extracted"
    print(f"batches : {len(have)}/{len(counts)} ({where})")
    print(f"pages   : {got_pages:,}/{total_pages:,} ({100 * got_pages / total_pages:.1f}%)")
    print(f"missing : {len(missing)} batches, {total_pages - got_pages:,} pages")

    unexpected = have_file - set(counts)
    if unexpected:
        print(f"\nnot in our list (safe to delete): {', '.join(sorted(unexpected))}")

    if not missing:
        print("\nAll batches accounted for.")
        return 0

    show = missing if args.missing else missing[: args.links or 5]
    print(f"\nnext {len(show)} by value:")
    for i, (b, k) in enumerate(show, 1):
        line = f"  {i:>2}. {b:<32} {k:>6,} pages"
        if args.links or args.missing:
            line += f"\n      {URL.format(batch=b)}"
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
