"""Page images of the Book of Mormon's original manuscript from the Joseph Smith Papers (BOM-34).

The transcripts came in BOM-05 (``ingest.jsp``); the page photographs let the automatic typing of
the manuscript's corrections (``manuscript.corrections``) be checked by eye. One page of the
document lists every page's image in order; each full image (about 2,700 x 5,550 pixels, ~25 MB)
is fetched one at a time with a pause between, backing off on any error and stopping after five
in a row, so the site carries no load to speak of (owner, 2026-11-06: go slowly). Resumes from
what is on disk.

The images are copyright Intellectual Reserve, Inc.: they stay under ``data/corpus/jsp_images/``
(no git); only their checksum manifest is public.

Usage::

    python -m ingest.jsp_images original [--pause 15]
"""

from __future__ import annotations

import argparse
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from ingest.jsp import BASE, DOCS, USER_AGENT

IMAGES = "https://www.josephsmithpapers.org/bc-jsp/content/jsp/images"
OUT = Path("data/corpus/jsp_images")


def _get(url: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def gallery(doc: str) -> list[str]:
    """Every page's full-size image path, in page order, from one page's gallery."""
    html = _get(f"{BASE}{DOCS[doc]}/1").decode("utf-8", "replace")
    seen, out = set(), []
    for m in re.finditer(r'"image":"(/\d+/[^"]+)_thumb\.jpg"', html):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(m.group(1) + ".jpg")
    return out


def fetch(doc: str, pause: float) -> int:
    paths = gallery(doc)
    out = OUT / doc
    out.mkdir(parents=True, exist_ok=True)
    print(f"{len(paths)} pages in the gallery", flush=True)
    errors = 0
    for i, p in enumerate(paths, 1):
        dst = out / f"{i:04d}.jpg"
        if dst.exists() and dst.stat().st_size > 0:
            continue
        time.sleep(pause + random.uniform(0, pause / 3))
        try:
            data = _get(IMAGES + p)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            errors += 1
            print(f"  page {i}: {e}; backing off ({errors}/5)", flush=True)
            if errors >= 5:
                print("five errors in a row; stopping (rerun resumes)", flush=True)
                return 1
            time.sleep(60 * errors)
            continue
        errors = 0
        tmp = dst.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(dst)
        if i % 10 == 0 or i == len(paths):
            print(f"  {i}/{len(paths)}", flush=True)
    missing = [i for i in range(1, len(paths) + 1) if not (out / f"{i:04d}.jpg").exists()]
    print(f"done: {len(paths) - len(missing)} of {len(paths)} images in {out}", flush=True)
    return 1 if missing else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("doc", choices=["original"])
    ap.add_argument("--pause", type=float, default=15.0)
    a = ap.parse_args(argv)
    return fetch(a.doc, a.pause)


if __name__ == "__main__":
    sys.exit(main())
