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

``body`` is the BOM-64 audit (Amendment 12, ``docs/date-audit-plan.md``): every other volume
dated 1830 or earlier has its full text's year mentions counted; one naming years later than its
own often enough moves to the latest year it names at least ``dates.min_year_mentions`` times
(``data/catalog/date_body.parquet``, counts only). ``effective_year`` applies both.

Usage::

    python -m metadata.dates check [--workers 8]
    python -m metadata.dates body [--workers 8]   # -> data/catalog/date_body.parquet
    python -m metadata.dates sample               # -> data/catalog/date_sample.jsonl (model)
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
BODY = Path("data/catalog/date_body.parquet")
_BODY_YEAR = re.compile(r"\b(1[6-9]\d\d)\b")
HEAD_CHARS = 4000
SOURCES = {"internet_archive", "hathitrust", "institutional_books"}
BODY_SOURCES = SOURCES | {"tcp"}
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


@lru_cache(maxsize=1)
def catalog_years() -> dict[str, int | None]:
    """work_id -> the catalog's own year, for callers holding only ids."""
    t = pq.read_table(CATALOG, columns=["work_id", "year"])
    return dict(zip(t["work_id"].to_pylist(), t["year"].to_pylist(), strict=True))


def effective_year(work_id: str, year: int | None) -> int | None:
    """The year date-window selections use: the title-page verdict where one exists (None for an
    undated or post-1830 placeholder, which then falls outside any window)."""
    v = _verdicts().get(work_id)
    if v is not None:
        kind, y = v
        year = y if kind in ("confirmed", "title_page") else None
    if year is not None and work_id in _body():
        return max(year, _body()[work_id])
    return year


def body_counts(text: str, year: int, cfg: dict) -> dict:
    """Amendment 12 on one text: year mentions, later ones, the flag and the corrected year."""
    d = cfg["dates"]
    counts: Counter = Counter()
    for m in _BODY_YEAR.finditer(text):
        y = int(m.group(1))
        if y <= d["latest_year"]:
            counts[y] += 1
    total = sum(counts.values())
    later = {y: n for y, n in counts.items() if y > year + d["slack_years"]}
    n_later = sum(later.values())
    flagged = n_later >= d["min_later_mentions"] and n_later >= d["min_later_share"] * total
    firm = [y for y, n in later.items() if n >= d["min_year_mentions"]]
    corrected = max(firm) if flagged and firm else None
    top = sorted(later.items(), key=lambda kv: -kv[1])[:3]
    return {"year_mentions": total, "later_mentions": n_later, "flagged": flagged,
            "corrected_year": corrected, "top_later": [[y, n] for y, n in top]}  # fmt: skip


def _body_one(job: tuple[str, str, int]) -> dict:
    wid, path, year = job
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"work_id": wid, "year": year, "error": True}
    return {"work_id": wid, "year": year, "error": False, **body_counts(text, year, _cfg())}


@lru_cache(maxsize=1)
def _cfg() -> dict:
    return load_config()


def body(workers: int) -> int:
    from ocr_fix.normalize import norm_path

    hi = load_config()["corpus"]["date_range"][1]
    cols = ["work_id", "source", "year", "text_path", "has_text"]
    jobs = []
    for r in pq.read_table(CATALOG, columns=cols).to_pylist():
        if not r["has_text"] or r["source"] not in BODY_SOURCES:
            continue
        y = effective_year(r["work_id"], r["year"])
        if y is not None and y <= hi:
            jobs.append((r["work_id"], str(norm_path(r)), y))
    start = time.time()
    print(f"{len(jobs):,} volumes to scan", flush=True)
    with ProcessPoolExecutor(workers) as pool:
        out = list(pool.map(_body_one, jobs, chunksize=256))
    schema = pa.schema([("work_id", pa.string()), ("year", pa.int32()), ("error", pa.bool_()),
                        ("year_mentions", pa.int32()), ("later_mentions", pa.int32()),
                        ("flagged", pa.bool_()), ("corrected_year", pa.int32()),
                        ("top_later", pa.list_(pa.list_(pa.int32())))])  # fmt: skip
    pq.write_table(pa.Table.from_pylist(out, schema=schema).replace_schema_metadata(
        {"config_sha256": stamp()["config_sha256"]}), BODY)  # fmt: skip
    flagged = [r for r in out if r.get("flagged")]
    moved = sum(1 for r in flagged if r["corrected_year"] and r["corrected_year"] > hi)
    bad = sum(r["error"] for r in out)
    print(f"{len(out):,} scanned in {time.time() - start:.0f}s: {len(flagged):,} flagged, "
          f"{moved:,} move past {hi}, {bad} unreadable -> {BODY}")  # fmt: skip
    return 0


@lru_cache(maxsize=1)
def _body() -> dict[str, int]:
    if not BODY.exists():
        return {}
    t = pq.read_table(BODY, columns=["work_id", "flagged", "corrected_year"]).to_pylist()
    return {r["work_id"]: r["corrected_year"] for r in t if r["flagged"] and r["corrected_year"]}


SAMPLE = Path("data/catalog/date_sample.jsonl")
SAMPLE_MODEL = "sonnet"
HEAD, TAIL = 6000, 2000  # characters of the opening and closing shown to the model (Amendment 12)


def _ask_year(prompt: str) -> str:
    """A four-digit year, UNKNOWN, or RETRY (an outage, never recorded as an answer)."""
    import subprocess

    from metadata.genre import _TRANSIENT, _log_parse_failure

    try:
        done = subprocess.run(["claude", "-p", "--model", SAMPLE_MODEL, prompt],
                              capture_output=True, text=True, timeout=300,
                              stdin=subprocess.DEVNULL)  # fmt: skip
    except Exception as exc:  # noqa: BLE001
        _log_parse_failure(SAMPLE_MODEL, f"<{type(exc).__name__}: {exc}>")
        return "RETRY"
    text = done.stdout.strip()
    if not text or _TRANSIENT.search(text) or done.returncode != 0:
        _log_parse_failure(SAMPLE_MODEL, text or f"<rc={done.returncode}>")
        return "RETRY"
    m = re.findall(r"\b(1[5-9]\d\d|UNKNOWN)\b", text.upper())
    if not m:
        _log_parse_failure(SAMPLE_MODEL, text)
        return "UNPARSED"
    return m[-1]


def sample() -> int:
    """Amendment 12's check of the flag: a seeded sample of flagged volumes and of unflagged
    volumes with a later mention, each read by a model (simulated) for its printing year."""
    import json
    import random

    from metadata.config import derive_seed
    from ocr_fix.normalize import norm_path

    cfg = load_config()
    d = cfg["dates"]
    rows = pq.read_table(BODY).to_pylist()
    rng = random.Random(derive_seed(d["check_seed"], cfg))
    flagged = sorted((r for r in rows if r["flagged"]), key=lambda r: r["work_id"])
    near = sorted((r for r in rows if not r["flagged"] and r["later_mentions"]),
                  key=lambda r: r["work_id"])  # fmt: skip
    picks = [("flagged", r) for r in rng.sample(flagged, d["check_size"])]
    picks += [("unflagged", r) for r in rng.sample(near, d["check_size"])]
    cols = ["work_id", "source", "text_path"]
    want = {r["work_id"] for _, r in picks}
    cat = {c["work_id"]: c for c in pq.read_table(CATALOG, columns=cols).to_pylist()
           if c["work_id"] in want}  # fmt: skip
    done = {}
    if SAMPLE.exists():
        for ln in SAMPLE.read_text().splitlines():
            x = json.loads(ln)
            done[x["work_id"]] = x
    for k, (group, r) in enumerate(picks, 1):
        if done.get(r["work_id"], {}).get("answer") not in (None, "RETRY"):
            continue
        text = norm_path(cat[r["work_id"]]).read_text(encoding="utf-8", errors="replace")
        prompt = (
            "Below are the opening and the closing of the OCR text of one scanned library "
            f"volume. Its catalog record dates it {r['year']}. From the text alone, in what year "
            "was this volume printed? For a periodical or a set, give the year of the latest "
            "issue or part it contains. Ignore library stamps and call numbers. Reply with a "
            "four-digit year, or UNKNOWN if the text does not show it.\n\n--- OPENING ---\n"
            f"{text[:HEAD]}\n\n--- CLOSING ---\n{text[-TAIL:]}"
        )
        answer = "RETRY"
        for wait in (0, 60, 300, 900):
            time.sleep(wait)
            answer = _ask_year(prompt)
            if answer != "RETRY":
                break
        rec = {"work_id": r["work_id"], "group": group, "catalog_year": r["year"],
               "corrected_year": r["corrected_year"], "later_mentions": r["later_mentions"],
               "answer": answer, "model": SAMPLE_MODEL}  # fmt: skip
        with SAMPLE.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"{k}/{len(picks)} {group} {r['work_id']} {r['year']}: {answer}", flush=True)
    last = {}
    for ln in SAMPLE.read_text().splitlines():
        x = json.loads(ln)
        last[x["work_id"]] = x
    for group in ("flagged", "unflagged"):
        got = [x for x in last.values() if x["group"] == group and x["answer"].isdigit()]
        later = sum(int(x["answer"]) > x["catalog_year"] + d["slack_years"] for x in got)
        unk = sum(x["group"] == group and x["answer"] == "UNKNOWN" for x in last.values())
        print(f"{group}: {later}/{len(got)} printed later than catalog by the model's reading "
              f"({unk} unknown)")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--workers", type=int, default=8)
    b = sub.add_parser("body")
    b.add_argument("--workers", type=int, default=8)
    sub.add_parser("sample")
    a = ap.parse_args(argv)
    if a.cmd == "sample":
        return sample()
    if a.cmd == "body":
        return body(a.workers)
    return check(a.workers)


if __name__ == "__main__":
    sys.exit(main())
