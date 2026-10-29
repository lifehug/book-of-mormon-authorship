"""Placeholder publication dates (BOM-56).

Undated reprints reach the catalog as 1800: the Internet Archive stores year-only dates as
``YYYY-01-01T00:00:00Z`` and uses 1800 for "nineteenth century", and HathiTrust and Harvard carry
a bare "1800" for the same. 11,896 Archive volumes are dated 1800 against 3,400-5,500 in each
neighbouring year, and they include Cooper's novels of the 1840s, an 1885 festival programme and
1898 court reports. The date field cannot tell a placeholder from a real 1800 imprint, so the
volume's own title page decides: every 1800-dated volume's opening (``HEAD_CHARS``) is read for
four-digit and roman-numeral years.

* a year after 1830: ``post1830`` -- out of the period;
* 1800 itself: ``confirmed`` -- keeps 1800;
* other years inside 1780-1830 only: ``title_page`` -- the latest such year;
* no year, or only years before 1780: ``undated`` -- cannot be placed in the window.

Nothing is deleted and the frozen catalog is not edited: verdicts go to
``data/catalog/date_check.parquet``, and ``effective_year`` is what every date-window selection
reads. ``post1830`` and ``undated`` volumes fall out of the window; ``title_page`` ones move to
their year.

Usage::

    python -m metadata.dates check [--workers 8]
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import stamp

CATALOG = Path("data/catalog/catalog.parquet")
OUT = Path("data/catalog/date_check.parquet")
HEAD_CHARS = 4000
SOURCES = {"internet_archive", "hathitrust", "institutional_books"}
_YEAR = re.compile(r"\b(1[6-9]\d\d)\b")
_ROMAN = re.compile(r"\bM\.?\s?D\.?\s?C\.?\s?C\.?\s?[CLXVI.\s]{1,14}\b")
_VAL = {"M": 1000, "D": 500, "C": 100, "L": 50, "X": 10, "V": 5, "I": 1}


def roman(s: str) -> int:
    s = re.sub(r"[^MDCLXVI]", "", s.upper())
    total = 0
    for a, b in zip(s, s[1:] + " ", strict=True):
        total += -_VAL[a] if b in _VAL and _VAL[b] > _VAL[a] else _VAL[a]
    return total


def years_in(text: str) -> list[int]:
    ys = [int(y) for y in _YEAR.findall(text)]
    ys += [roman(m.group(0)) for m in _ROMAN.finditer(text)]
    return sorted({y for y in ys if 1600 <= y <= 1899})


def verdict(years: list[int], lo: int, hi: int) -> tuple[str, int | None]:
    if any(y > hi for y in years):
        return "post1830", max(years)
    if 1800 in years:
        return "confirmed", 1800
    inside = [y for y in years if lo <= y <= hi]
    if inside:
        return "title_page", max(inside)
    return "undated", None


def suspect(r: dict) -> bool:
    raw = r["date_raw"] or ""
    return (
        r["year"] == 1800
        and r["source"] in SOURCES
        and (raw.endswith("-01-01T00:00:00Z") or raw.strip() == "1800")
    )


def _one(job: tuple[str, str, int, int]) -> dict:
    wid, path, lo, hi = job
    try:
        head = Path(path).read_text(encoding="utf-8", errors="replace")[:HEAD_CHARS]
    except OSError:
        head = ""
    ys = years_in(head)
    v, y = verdict(ys, lo, hi)
    return {"work_id": wid, "verdict": v, "year": y, "years_found": ys}


def check(workers: int) -> int:
    lo, hi = load_config()["corpus"]["date_range"]
    cols = ["work_id", "source", "year", "date_raw", "text_path", "has_text"]
    rows = [r for r in pq.read_table(CATALOG, columns=cols).to_pylist()
            if r["has_text"] and suspect(r)]  # fmt: skip
    jobs = [(r["work_id"], r["text_path"], lo, hi) for r in rows]
    start = time.time()
    with ProcessPoolExecutor(workers) as pool:
        out = list(pool.map(_one, jobs, chunksize=64))
    schema = pa.schema([("work_id", pa.string()), ("verdict", pa.string()), ("year", pa.int32()),
                        ("years_found", pa.list_(pa.int32()))])  # fmt: skip
    pq.write_table(pa.Table.from_pylist(out, schema=schema).replace_schema_metadata(
        {"config_sha256": stamp()["config_sha256"]}), OUT)  # fmt: skip
    src = {r["work_id"]: r["source"] for r in rows}
    by = Counter((src[r["work_id"]], r["verdict"]) for r in out)
    print(f"{len(out):,} 1800-dated volumes checked in {time.time() - start:.0f}s -> {OUT}")
    for s in sorted(SOURCES):
        kinds = ("confirmed", "title_page", "post1830", "undated")
        print(f"  {s}: " + ", ".join(f"{v} {by[s, v]:,}" for v in kinds))
    return 0


@lru_cache(maxsize=1)
def _verdicts() -> dict[str, tuple[str, int | None]]:
    if not OUT.exists():
        return {}
    return {r["work_id"]: (r["verdict"], r["year"]) for r in pq.read_table(OUT).to_pylist()}


def effective_year(work_id: str, year: int | None) -> int | None:
    """The year date-window selections use: the title-page verdict where one exists (None for an
    undated or post-1830 placeholder, which then falls outside any window)."""
    v = _verdicts().get(work_id)
    if v is None:
        return year
    kind, y = v
    return y if kind in ("confirmed", "title_page") else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    return check(a.workers)


if __name__ == "__main__":
    sys.exit(main())
