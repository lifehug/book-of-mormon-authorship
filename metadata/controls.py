"""The control sets (BOM-18).

Section 3 registers four control groups: pseudo-biblical texts (Leacock, Snowden, Linning, Hunt,
and every other example found in the catalog), 1820s sermons and tracts, histories and Native
American origin texts, and a general prose baseline of fiction and periodicals. Amendment 2
requires membership to be published as an explicit list of identifiers with its SHA-256 before
the benchmark runs. Amendment 3: genre-matched control sets match a work on *either* of its two
labels.

Every set draws on the same eligible pool:

* has text, published 1780-1830 (``corpus.date_range``; TCP's earlier texts are out),
* a dedup keeper (``duplicates_normalized.parquet``, BOM-15's run on cleaned and normalised
  text, the order 4.3 lists; reprints count once),
* not flagged ``ocr_excluded`` by BOM-14 (``data/ocr_quality/volumes.parquet``),
* not a candidate's work, so candidates and controls stay disjoint -- except where section 3
  names a candidate's work as a control (Hunt's *The Late War*), which stays and is flagged,
* not sealed: no title naming the Book of Mormon and no 12-token string shared with it (4.2,
  ``metadata.sealed``), checked on every member's text.

Genre comes from pass 1 (``genre.parquet``); ``uncertain`` and ``PARSE_FAIL`` match nothing.

Native American origin texts are a named subset of the history set, picked by title words
(``ORIGINS``); the history set itself is genre-defined. The named pseudo-biblical works are found
by title (``NAMED``) whatever their genre label says, and whatever their date: Leacock's
*First Book of the American Chronicles* (1774) is named by section 3 though it predates 1780.

Two departures from taking every match, both registered by Amendment 6:

* ``pseudo_biblical_primary``: a second pseudo-biblical list holding only works whose *primary*
  label is pseudo-biblical, plus the named works. Amendment 3's "match on either" puts about
  5,300 volumes in the registered list, and read by title most of them are ordinary religious
  prose about scripture (the model used the label as a second label freely); 23 have it as
  primary. Both lists are published; which one the confirmatory test reads is the owner's call.
* ``POOL_SAMPLE``: the history and general-prose pools hold 40,000 and 340,000 volumes, some
  20 billion words with sermons, which passim cannot mask on one machine in under a month at the
  validated batch size. They are drawn down to a seeded sample, stratified by source and decade
  in proportion, which still supplies Amendment 2's 100-imposter draws many times over.

Usage::

    python -m metadata.controls build      # -> data/controls/
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.parquet as pq

from metadata import sealed
from metadata.config import load as load_config
from metadata.config import sha256_of_config
from metadata.dates import effective_year

CATALOG = Path("data/catalog/catalog.parquet")
GENRE = Path("data/catalog/genre.parquet")
DUPES = Path("data/catalog/duplicates_normalized.parquet")
VOLUMES = Path("data/ocr_quality/volumes.parquet")
COMBINED = Path("data/catalog/duplicates_combined.parquet")
SIGS = Path("data/catalog/signatures_normalized")  # word counts of the normalised text
OUT = Path("data/controls")

NAMED = {
    "leacock": r"first book of the american chronicles of the times",
    "snowden": r"american revolution.{0,60}(style of ancient history|scripture style)",
    "linning": r"first book of napoleon",
    "hunt": r"late war.{0,160}ancient historical style",
}
ORIGINS = re.compile(
    r"\b(indians?|aborigin\w*|lost tribes|ten tribes|israelites? in america|"
    r"american antiquities|origin of the (american|indian)|hebrews)\b",
    re.IGNORECASE,
)
SCAN_WORKERS = 6
POOL_SAMPLE = {"history": 3000, "general_prose": 5000}  # registered, Amendment 6
SETS = {
    "pseudo_biblical": {"pseudo_biblical"},
    "sermons_1820s": {"sermon_devotional"},
    "history": {"history_chronicle"},
    "general_prose": {"fiction_narrative", "newspaper_periodical"},
}


def _labels(g: str | None) -> set[str]:
    return {x.strip() for x in (g or "").split(",")} - {"", "uncertain", "PARSE_FAIL"}


def _candidate_authors() -> set[str]:
    """Surnames of the registered candidates, for keeping their works out of the pools."""
    return {"smith, joseph", "cowdery", "rigdon", "pratt, parley", "phelps", "spalding",
            "spaulding", "smith, ethan", "hunt, gilbert"}  # fmt: skip


def _is_candidate(author_norm: str) -> bool:
    return any(author_norm.startswith(a) for a in _candidate_authors())


def _scan(path: str) -> bool:
    return sealed.contaminated(Path(path).read_text(encoding="utf-8", errors="replace"))


def _stratified_sample(ms: list[dict], cap: int, seed: int) -> list[dict]:
    """``cap`` members drawn in proportion from source x decade strata, seeded."""
    if len(ms) <= cap:
        return ms
    strata: dict[tuple, list[dict]] = {}
    for m in sorted(ms, key=lambda m: m["work_id"]):
        strata.setdefault((m["source"], m["year_catalog"] // 10 * 10), []).append(m)
    rng = random.Random(f"{seed}:controls")
    out = []
    for key in sorted(strata):
        group = strata[key]
        take = round(cap * len(group) / len(ms))
        out += rng.sample(group, min(take, len(group)))
    return out


def build() -> int:
    cfg = load_config()
    lo, hi = cfg["corpus"]["date_range"]
    cat = pq.read_table(CATALOG).to_pylist()
    genre = {r["work_id"]: r["genre"] for r in pq.read_table(GENRE).to_pylist()}
    nonkeeper = {r["work_id"] for r in pq.read_table(DUPES).to_pylist() if not r["is_keeper"]}
    excluded = set()
    if VOLUMES.exists():
        excluded = {
            r["work_id"]
            for r in pq.read_table(VOLUMES, columns=["work_id", "ocr_excluded"]).to_pylist()
            if r["ocr_excluded"]
        }
    else:
        print(f"warning: {VOLUMES} missing; OCR exclusion not applied", file=sys.stderr)
    words = {}
    for f in sorted(SIGS.glob("*.parquet")):
        for r in pq.read_table(f, columns=["work_id", "words"]).to_pylist():
            words[r["work_id"]] = r["words"]
    seal = sealed.sealed_ids()

    drops: Counter = Counter()
    members: dict[str, list[dict]] = {k: [] for k in [*SETS, "pseudo_biblical_primary"]}
    for r in cat:
        wid = r["work_id"]
        # BOM-56: placeholder dates. Membership and the pool samples use the catalog's year, so
        # v1.0's draw (and its KJV masks) is reproduced; members whose corrected year falls
        # outside the window are removed after sampling.
        year_eff = effective_year(wid, r["year"])
        title = r["title"] or ""
        named = next((k for k, p in NAMED.items() if re.search(p, title, re.I)), None)
        labels = _labels(genre.get(wid))
        sets = [k for k, want in SETS.items() if labels & want]
        primary = (genre.get(wid) or "").split(",")[0]
        if primary == "pseudo_biblical" or named:
            sets.append("pseudo_biblical_primary")
        if named:
            sets = sorted(set(sets) | {"pseudo_biblical", "pseudo_biblical_primary"})
        if not sets:
            continue
        reason = None
        if not r["has_text"]:
            reason = "no_text"
        elif not named and (r["year"] is None or not lo <= r["year"] <= hi):
            reason = "out_of_window"
        elif wid in nonkeeper:
            reason = "duplicate"
        elif wid in excluded:
            reason = "ocr_excluded"
        elif wid in seal:
            reason = "sealed_title"
        elif _is_candidate(r["author_norm"] or "") and not named:
            reason = "candidate_work"
        if reason:
            drops[reason] += 1
            continue
        for k in sets:
            if k == "sermons_1820s" and not (year_eff and 1820 <= year_eff <= 1829):
                continue
            members[k].append(
                {
                    "work_id": wid,
                    "source": r["source"],
                    "year": year_eff,
                    "year_catalog": r["year"],
                    "words": words.get(wid),
                    "named": named,
                    "origins": k == "history" and bool(ORIGINS.search(title)),
                    "candidate_overlap": _is_candidate(r["author_norm"] or ""),
                }
            )

    full_sizes = {k: len(v) for k, v in members.items()}
    for k, cap in POOL_SAMPLE.items():
        members[k] = _stratified_sample(members[k], cap, cfg["seed"])
    for k, ms in members.items():
        kept = [m for m in ms if m["named"] or (m["year"] and lo <= m["year"] <= hi)]
        drops["placeholder_date"] += len(ms) - len(kept)
        members[k] = kept

    # 4.2's registered check on every member's text, after the cheap filters and the sampling
    paths = {r["work_id"]: r["text_path"] for r in cat}
    ids = sorted({m["work_id"] for ms in members.values() for m in ms})
    with ProcessPoolExecutor(SCAN_WORKERS) as pool:
        flags = pool.map(_scan, [paths[w] for w in ids], chunksize=8)
        contaminated = {w for w, bad in zip(ids, flags, strict=True) if bad}
    for k in members:
        members[k] = [m for m in members[k] if m["work_id"] not in contaminated]

    # Amendment 6's second dedup pass (BOM-55): a work held by two sources counts once. Applied
    # to each set as drawn, so the pool samples (and their KJV masks) are unchanged: within a
    # set, one member per combined duplicate group, the earliest (year, then catalog order).
    group = {r["work_id"]: r["group_id"] for r in pq.read_table(COMBINED).to_pylist()}
    order = {r["work_id"]: i for i, r in enumerate(cat)}
    once_dropped = {}
    for k, ms in members.items():
        seen: set[int] = set()
        kept = []
        for m in sorted(ms, key=lambda m: (m["year"] or 9999, order[m["work_id"]])):
            g = group.get(m["work_id"])
            if g is not None and g in seen:
                continue
            if g is not None:
                seen.add(g)
            kept.append(m)
        once_dropped[k] = len(ms) - len(kept)
        members[k] = kept

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"config_sha256": sha256_of_config(), "dropped": dict(drops),
               "eligible_before_sampling": full_sizes,
               "contaminated_12_token": sorted(contaminated),
               "dropped_as_cross_source_copies": once_dropped, "sets": {}}  # fmt: skip
    for k, ms in members.items():
        ms.sort(key=lambda m: m["work_id"])
        ids = "".join(m["work_id"] + "\n" for m in ms)
        (OUT / f"{k}.txt").write_text(ids)
        with (OUT / f"{k}.jsonl").open("w") as fh:
            fh.writelines(json.dumps(m) + "\n" for m in ms)
        summary["sets"][k] = {
            "volumes": len(ms),
            "words": sum(m["words"] or 0 for m in ms),
            "by_source": dict(Counter(m["source"] for m in ms)),
            "named": dict(Counter(m["named"] for m in ms if m["named"])),
            "origins_subset": sum(m["origins"] for m in ms),
            "sha256_of_id_list": hashlib.sha256(ids.encode()).hexdigest(),
        }
    (OUT / "controls.json").write_text(json.dumps(summary, indent=1) + "\n")
    for k, s in summary["sets"].items():
        print(f"{k:<16} {s['volumes']:>7,} volumes {s['words']:>14,} words  {s['by_source']}")
    print(f"dropped: {dict(drops)}; contaminated (12-token): {len(contaminated)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    return build() if args[:1] == ["build"] else 1


if __name__ == "__main__":
    sys.exit(main())
