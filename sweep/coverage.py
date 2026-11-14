"""Shortlist coverage of the sweep on its 200 known books (BOM-89, BOM-91; exploratory).

The sweep's job in Part 2 is to narrow the library to a shortlist the author algorithm can pick
from, so the measure is coverage: the share of known books whose true author is among the K
closest of all swept authors, for each K in ``sweep.coverage.ks`` and each signal (the style
encoder and Cosine Delta from ``sweep.calibrate``; Burrows' Delta, ENSC and General Imposters
from ``sweep.older``).

Each book is tagged, from the catalog only:

- **identity**: the catalog's raw ``author`` field often carries life dates ("1766-1834"). With the
  dates of the book's volumes and of the profile's volumes: ``verified`` (all dated, one pair of
  dates), ``same_dates_some_undated``, ``conflict`` (two pairs: two people under one name),
  ``one_side_dated``, ``undated``. ``sweep.coverage.confirmed`` names the classes counted as a
  confirmed identity.
- **genre**: the share of the author's profile blocks whose volume has the book's primary genre
  (``data/catalog/genre.parquet``, the first label). ``same`` at ``sweep.coverage.same_share`` or
  more, ``cross`` at zero, ``mixed`` between, ``unknown`` when the book's genre is uncertain.
  ``cross`` is the Book of Mormon's situation: nothing of that kind in the author's other writing.
- **profile_works**: the number of works the profile is drawn from.

Writes names and numbers only: ``data/sweep/coverage.json``.

Usage::

    python -m sweep.coverage
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict

import numpy as np
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import stamp
from sweep.units import CATALOG, OUT

GENRE = "data/catalog/genre.parquet"
SIGNALS = {"style": "style_rank", "cosine": "mfw_rank", "burrows": "burrows_rank",
           "ensc": "ensc_rank", "gi": "gi_rank"}  # fmt: skip
_LIFE = re.compile(r"\b(1[4-8]\d\d)\??\s*-\s*(1[4-8]\d\d)?")


def life(raw: str | None) -> tuple[str, str] | None:
    """(born, died or '') from a catalog author string, or None."""
    m = _LIFE.search(raw or "")
    return (m.group(1), m.group(2) or "") if m else None


def identity(query: list[tuple[str, str] | None], profile: list[tuple[str, str] | None]) -> str:
    """The identity class from the life dates of the book's and the profile's volumes."""
    qs, ps = {x for x in query if x}, {x for x in profile if x}
    if len(qs | ps) > 1:
        return "conflict"
    if qs and ps:
        return (
            "verified" if None not in query and None not in profile else "same_dates_some_undated"
        )
    return "one_side_dated" if qs or ps else "undated"


def primary(label: str | None) -> str:
    return (label or "uncertain").split(",")[0]


def genre_class(book: str, profile: list[str], same_share: float) -> tuple[str, float]:
    """same / mixed / cross / unknown, and the share of profile blocks in the book's genre."""
    if book == "uncertain" or not profile:
        return "unknown", float("nan")
    share = sum(g == book for g in profile) / len(profile)
    return ("same" if share >= same_share else "cross" if share == 0 else "mixed"), share


def coverage(ranks: list[int], ks: list[int]) -> dict[str, float]:
    r = np.array(ranks)
    return {str(k): float(np.mean(r <= k)) for k in ks} if len(r) else {}


def table(recs: list[dict], ks: list[int]) -> dict:
    return {"n": len(recs),
            **{s: coverage([r[s] for r in recs], ks) for s in SIGNALS if recs and s in recs[0]},
            "median_rank": {s: float(np.median([r[s] for r in recs]))
                            for s in SIGNALS if recs and s in recs[0]}}  # fmt: skip


def run() -> int:
    cfg = load_config()
    c = cfg["sweep"]["coverage"]
    ks = c["ks"]
    cat = {r["work_id"]: r["author"]
           for r in pq.read_table(CATALOG, columns=["work_id", "author"]).to_pylist()}  # fmt: skip
    blocks = pq.read_table(OUT / "blocks.parquet").to_pylist()
    need = {b["work_id"] for b in blocks if b["role"] != "profile"}
    genre = {r["work_id"]: primary(r["genre"])
             for r in pq.read_table(GENRE, columns=["work_id", "genre"]).to_pylist()
             if r["work_id"] in need}  # fmt: skip
    q: dict[str, list[str]] = defaultdict(list)
    p: dict[str, list[str]] = defaultdict(list)
    for b in blocks:
        if b["role"] == "calib_query":
            q[b["author"]].append(b["work_id"])
        elif b["role"] == "calib_profile":
            p[b["author"]].append(b["work_id"])
    ranks = {r["author"]: r for r in json.loads((OUT / "calibration.json").read_text())["records"]}
    older = OUT / "older_methods.json"
    if older.exists():
        for r in json.loads(older.read_text())["records"]:
            ranks[r["author"]].update(r)
    recs = []
    for a, r in sorted(ranks.items()):
        qg = Counter(genre.get(w, "uncertain") for w in q[a]).most_common(1)[0][0]
        gc, share = genre_class(qg, [genre.get(w, "uncertain") for w in p[a]], c["same_share"])
        recs.append({"author": a, "book": r["book"],
                     "identity": identity([life(cat[w]) for w in sorted(set(q[a]))],
                                          [life(cat[w]) for w in sorted(set(p[a]))]),
                     "book_genre": qg, "genre": gc,
                     "profile_share_in_genre": None if np.isnan(share) else round(share, 3),
                     "profile_works": len(set(p[a])),
                     **{s: r[k] for s, k in SIGNALS.items() if k in r}})  # fmt: skip
    conf = [r for r in recs if r["identity"] in c["confirmed"]]
    groups = {"all": recs, "confirmed": conf}
    for g in ("same", "mixed", "cross", "unknown"):
        groups[f"genre_{g}"] = [r for r in recs if r["genre"] == g]
        groups[f"confirmed_genre_{g}"] = [r for r in conf if r["genre"] == g]
    for i in sorted({r["identity"] for r in recs}):
        groups[f"identity_{i}"] = [r for r in recs if r["identity"] == i]
    one = c["few_works"]
    groups[f"profile_works_le_{one}"] = [r for r in recs if r["profile_works"] <= one]
    groups[f"profile_works_gt_{one}"] = [r for r in recs if r["profile_works"] > one]
    doc = {**stamp(), "exploratory": True, "ks": ks, "confirmed_classes": c["confirmed"],
           "same_share": c["same_share"],
           "groups": {k: table(v, ks) for k, v in groups.items()}, "records": recs}  # fmt: skip
    out = OUT / "coverage.json"
    out.write_text(json.dumps(doc, indent=1) + "\n")
    show = [k for k in ks if k in c["show"]]
    print(f"{'group':34s} {'n':>4s}  " + "  ".join(f"{'style@' + str(k):>10s}" for k in show)
          + "  " + "  ".join(f"{'cos@' + str(k):>8s}" for k in show))  # fmt: skip
    for k, t in doc["groups"].items():
        if t["n"]:
            print(f"{k:34s} {t['n']:4d}  "
                  + "  ".join(f"{100 * t['style'][str(x)]:10.1f}" for x in show) + "  "
                  + "  ".join(f"{100 * t['cosine'][str(x)]:8.1f}" for x in show))  # fmt: skip
    print(f"-> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
