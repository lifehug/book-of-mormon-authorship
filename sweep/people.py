"""Who among the swept authors could have written a book dictated in 1828-29 (BOM-91; exploratory).

Life dates per swept author, from two places:

- **catalog**: the raw ``author`` field of any catalog row under the author's name
  ("Smith, Ethan, 1762-1849"). Two different pairs under one name is ``conflict`` (two people).
- **loc**: for authors the catalog leaves undated, the Library of Congress name authority file
  (``id.loc.gov/authorities/names/suggest2``, personal names, left-anchored on surname and first
  forename). A hit is a candidate when its surname is ours, its forenames match ours one for one
  (an initial matches a name) and its birth year is at least ``sweep.people.min_age_at_print``
  before the author's earliest volume here. Exactly one candidate: its dates are taken. Several:
  ``ambiguous``. None: ``none``. Every reply is cached (``data/sweep/loc_cache.jsonl``); a failed
  request is not recorded and is asked again on the next run.

The lookup is checked on known answers first: the same rule on a seeded sample of
``sweep.people.check_sample`` authors the catalog does date (``check`` in the summary: how many
the rule dates, and how many of those agree with the catalog).

``status`` in ``sweep.people.year``: ``alive`` (born at least ``min_age`` years before, not dead
before ``year - 1``), ``dead``, ``too_young``, ``unknown``; with a birth year only, ``dead`` when
older than ``max_age``.

Writes names, years and counts only: ``data/sweep/people.parquet``, ``people.json``.

Usage::

    python -m sweep.people lookup     # the outside requests (resumes; about 2 h)
    python -m sweep.people build
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from sweep.units import CATALOG, OUT

CACHE = OUT / "loc_cache.jsonl"
URL = "https://id.loc.gov/authorities/names/suggest2"
UA = "catalog-date-lookup/1.0"
_CAT = re.compile(r"\b(1[4-8]\d\d)\??\s*-\s*(1[4-8]\d\d)?")
_LOC = re.compile(
    r",\s*(?:approximately\s+)?(\d{4})?\??\s*-\s*(?:approximately\s+)?(\d{4})?\??\s*$"
)
_DROP = {"dd", "esq", "bart", "rev", "sir", "mrs", "mr", "dr", "the", "younger", "elder", "jr",
         "sen", "am", "ma", "md", "lld", "of"}  # fmt: skip
_DEGREES = {("d", "d"), ("a", "m"), ("m", "d"), ("m", "a"), ("ll", "d"), ("a", "b"), ("b", "d")}


def cat_life(raw: str | None) -> tuple[int, int | None] | None:
    m = _CAT.search(raw or "")
    return (int(m.group(1)), int(m.group(2)) if m.group(2) else None) if m else None


def name_parts(name: str) -> tuple[str, list[str]]:
    """(surname, forename tokens) of "surname, forenames ...", lowercase letters only."""
    sur, _, rest = name.lower().partition(",")
    toks = re.findall(r"[a-z]+", re.sub(r"\(.*?\)", " ", rest))
    return re.sub(r"[^a-z]", "", sur), toks


def ours(author: str) -> tuple[str, list[str]]:
    """Our catalog name with titles and degrees dropped after the first forename."""
    sur, toks = name_parts(author)
    while len(toks) > 2 and tuple(toks[-2:]) in _DEGREES:  # "tatham, edward d d"
        toks = toks[:-2]
    k = len(toks) // 2  # "j g john gustavus": initials, then the names they stand for
    pairs = list(zip(toks[:k], toks[k:], strict=False))
    if k and len(toks) == 2 * k and all(len(a) == 1 and b[0] == a and len(b) > 1 for a, b in pairs):
        return sur, toks[k:]
    return sur, toks[:1] + [t for t in toks[1:] if t not in _DROP]


def same_name(mine: tuple[str, list[str]], label: str) -> bool:
    """The label's surname is ours and its forenames match ours one for one (initials allowed)."""
    head = _LOC.sub("", label)
    sur, toks = name_parts(head)
    full = re.search(r"\((.*?)\)", head)  # "Lemaistre, J. G. (John Gustavus)"
    forms = [toks] + ([re.findall(r"[a-z]+", full.group(1).lower())] if full else [])
    if sur != mine[0] or not mine[1]:
        return False
    return any(len(f) == len(mine[1]) and all(a == b or (min(len(a), len(b)) == 1 and a[0] == b[0])
                                              for a, b in zip(mine[1], f, strict=True))
               for f in forms)  # fmt: skip


def loc_life(label: str) -> tuple[int | None, int | None] | None:
    m = _LOC.search(label)
    if not m or not (m.group(1) or m.group(2)):
        return None
    return (int(m.group(1)) if m.group(1) else None, int(m.group(2)) if m.group(2) else None)


def decide(author: str, labels: list[str], first_year: int | None, gap: int):
    """("loc", born, died), ("ambiguous", n) or ("none",) from a reply's labels."""
    mine = ours(author)
    cands = set()
    for lab in labels:
        d = loc_life(lab)
        if d and same_name(mine, lab):
            born = d[0]
            if born is None or first_year is None or born + gap <= first_year:
                cands.add(d)
    if len(cands) == 1:
        return ("loc", *next(iter(cands)))
    return ("ambiguous", len(cands)) if cands else ("none",)


def status(born: int | None, died: int | None, p: dict) -> str:
    if born is None and died is None:
        return "unknown"
    if died is not None and died < p["year"] - 1:
        return "dead"
    if born is not None and born > p["year"] - p["min_age"]:
        return "too_young"
    if died is None and born is not None and born < p["year"] - p["max_age"]:
        return "dead"
    return "alive"


def table() -> dict[str, dict]:
    """Swept author -> catalog date pairs and earliest volume year, over every catalog row."""
    swept = set(pq.read_table(OUT / "authors.parquet", columns=["author"]).column(0).to_pylist())
    out = {a: {"pairs": set(), "first": None} for a in swept}
    for r in pq.read_table(CATALOG, columns=["author", "author_norm", "year"]).to_pylist():
        a = (r["author_norm"] or "").strip()
        if a not in out:
            continue
        d = cat_life(r["author"])
        if d:
            out[a]["pairs"].add(d)
        y = int(r["year"]) if str(r["year"] or "").isdigit() else None
        if y and (out[a]["first"] is None or y < out[a]["first"]):
            out[a]["first"] = y
    return out


def cache() -> dict[str, list[str]]:
    if not CACHE.exists():
        return {}
    return {r["author"]: r["labels"] for r in map(json.loads, CACHE.read_text().splitlines())}


def check_sample(t: dict[str, dict], cfg: dict) -> list[str]:
    p = cfg["sweep"]["people"]
    dated = sorted(a for a, v in t.items() if len(v["pairs"]) == 1)
    rng = random.Random(derive_seed(p["check_seed"], cfg))
    return sorted(rng.sample(dated, min(p["check_sample"], len(dated))))


def lookup() -> int:
    cfg = load_config()
    p = cfg["sweep"]["people"]
    t, have = table(), cache()
    todo = [a for a in check_sample(t, cfg) + sorted(a for a, v in t.items() if not v["pairs"])
            if a not in have and ours(a)[1]]  # fmt: skip
    print(f"{len(todo):,} authors to ask ({len(have):,} cached)", flush=True)
    failed = 0
    with CACHE.open("a") as f:
        for k, a in enumerate(todo, 1):
            sur, toks = ours(a)
            ask = {
                "q": f"{sur}, {toks[0][0] if len(toks[0]) == 1 else toks[0]}",
                "rdftype": "PersonalName",
                "count": p["hits"],
                "searchtype": "leftanchored",
            }
            q = urllib.parse.urlencode(ask)
            try:
                req = urllib.request.Request(f"{URL}?{q}", headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=60) as r:
                    hits = json.loads(r.read())["hits"]
            except Exception as e:  # noqa: BLE001 -- transient: not recorded, asked again next run
                failed += 1
                print(f"  failed {a!r}: {e}", flush=True)
                time.sleep(p["pause"] * 10)
                continue
            f.write(json.dumps({"author": a, "labels": [h["aLabel"] for h in hits]}) + "\n")
            f.flush()
            if k % 500 == 0:
                print(f"  {k:,}/{len(todo):,}", flush=True)
            time.sleep(p["pause"])
    print(f"done; {failed} failed (rerun to ask them again)", flush=True)
    return 0


def build() -> int:
    cfg = load_config()
    p = cfg["sweep"]["people"]
    t, have = table(), cache()
    rows = []
    for a, v in sorted(t.items()):
        born = died = None
        if len(v["pairs"]) == 1:
            src, (born, died) = "catalog", next(iter(v["pairs"]))
        elif len(v["pairs"]) > 1:
            src = "conflict"
        elif a in have:
            got = decide(a, have[a], v["first"], p["min_age_at_print"])
            src = got[0]
            if src == "loc":
                born, died = got[1], got[2]
        else:
            src = "not_asked"
        rows.append({"author": a, "born": born, "died": died, "date_source": src,
                     "first_volume_year": v["first"], "status": status(born, died, p)})  # fmt: skip
    chk = {"asked": 0, "dated": 0, "agree": 0, "ambiguous": 0, "none": 0}
    for a in check_sample(t, cfg):
        if a not in have:
            continue
        chk["asked"] += 1
        got = decide(a, have[a], t[a]["first"], p["min_age_at_print"])
        if got[0] == "loc":
            chk["dated"] += 1
            cb, cd = next(iter(t[a]["pairs"]))
            # the same person: birth years equal, or (birth unknown there) death years equal
            chk["agree"] += (got[1] == cb) if got[1] is not None else (got[2] == cd)
        else:
            chk[got[0]] += 1
    meta = {**stamp(), "exploratory": True, "swept_authors": len(rows),
            "date_source": dict(Counter(r["date_source"] for r in rows)),
            "status": dict(Counter(r["status"] for r in rows)),
            "status_by_source": {
                s: dict(Counter(r["status"] for r in rows if r["date_source"] == s))
                for s in ("catalog", "loc")},
            "rule": {k: p[k] for k in ("year", "min_age", "max_age", "min_age_at_print")},
            "check": chk}  # fmt: skip
    pq.write_table(pa.Table.from_pylist(rows), OUT / "people.parquet")
    (OUT / "people.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps({k: meta[k] for k in ("date_source", "status", "check")}, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["lookup", "build"])
    return {"lookup": lookup, "build": build}[ap.parse_args(argv).cmd]()


if __name__ == "__main__":
    sys.exit(main())
