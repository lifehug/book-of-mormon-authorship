"""BOM-103, third design: the book's agenda of controversy, as a bundle, against eras of print.

Campbell (1831) said the Book of Mormon "decides all the great controversies" of New York in the
1820s and listed twenty. Each topic is old, so only the mix and the silences could date an
agenda. Step 1 replicates Campbell his way (is each of his twenty in the 1830 text, by a written
rule?) and adds the comparison he left out (are the same twenty present in religious print of
1640-1659, 1740-1769, Evans's American imprints of 1770-1799 and OCR print of 1815-1829?). Part A
then fixes a topic list from Campbell, the period surveys of sects (Pagitt 1645, Edwards 1646,
Hannah Adams 1801 and 1817, Evans 1807) and the issue, and gives every text a profile: the share
of its topic passages on each topic, silences included. Each text is compared with six eras of
religious print (reprints left out) by Jensen-Shannon distance, on equal seeded subsamples. The
known-answer check (era groups, old works reprinted late, the 1640s heresy catalogues, Joseph
Smith's revelations as a register control) comes first; the Book of Mormon is scored only if
every bar is met. The test card is ``data/private/lab/owner/2026-11-22-debates-redesign/card.md``;
settings are ``lab.debates3``. Outputs hold ids, topic names and numbers; no text (precision
samples and Part B questions, which quote passages, go to the private folder).

Usage::

    python -m lab.debates3 topics       # topic list, Campbell's twenty, survey support -> data/lab/debates/topics_v3.json
    python -m lab.debates3 scan         # every religious work 1640-1829: topic passages (resumes) -> data/corpus/lab/debates3/
    python -m lab.debates3 replicate    # step 1, Campbell his way -> data/lab/debates/replication_v3.json
    python -m lab.debates3 check        # Part A known-answer check -> data/lab/debates/check_v3.json
    python -m lab.debates3 run          # check, then (if passed) the book and controls -> data/lab/debates/result_v3.json
    python -m lab.debates3 precision    # rule-precision samples and judge jobs (not run) -> private folder
    python -m lab.debates3 partb        # Part B judge jobs (only after the check passed; not run) -> private folder
    python -m lab.debates3 partb-score  # read Part B answers, if any -> data/lab/debates/partb_v3.json
"""  # noqa: E501

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import subprocess
import time
import zlib
from collections import Counter
from pathlib import Path

import numpy as np

from lab import door, registry
from lab.debates import death_year
from lab.paths import FAST, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "debates"
SCAN = FAST / "debates3"
CARD = NOTES / "owner" / "2026-11-22-debates-redesign"
DELUSIONS = Path("data/corpus/lab/sources/debates/delusionsanalysi00camp/text.txt")
DELUSIONS_URL = "https://archive.org/details/delusionsanalysi00camp"
REVELATION_BOOK_1 = Path("data/private/candidates/js-1828-1829-revelations.jsonl")
TCP = Path("data/catalog/tcp.jsonl")
VOGEL = "not replicated until the source is bought (Metcalfe, ed., New Approaches, 1993)"


def settings(cfg: dict) -> dict:
    return cfg["lab"]["debates3"]


def settings_hash(cfg: dict) -> str:
    keys = {"debates3": settings(cfg), "semantic": cfg["semantic"],
            "bible_title": cfg["lab"]["debates"]["bible_title"],
            "genre": cfg["lab"]["debates"]["gallery_genre"]}  # fmt: skip
    return hashlib.sha256(json.dumps(keys, sort_keys=True).encode()).hexdigest()


def rules_hash(cfg: dict) -> str:
    """What the scan depends on: topic rules, min_hits and passage cutting."""
    d, s = settings(cfg), cfg["semantic"]
    keys = {"topics": d["topics"], "min_hits": d["min_hits"], "n": s["passage_words"],
            "min": s["min_passage_words"]}  # fmt: skip
    return hashlib.sha256(json.dumps(keys, sort_keys=True).encode()).hexdigest()[:12]


# ------------------------------------------------------------------------------------ topics
def compile_topics(topics: dict) -> list[tuple[str, list[re.Pattern]]]:
    return [(t, [re.compile(g) for g in groups]) for t, groups in topics.items()]


def norm(text: str) -> str:
    return " ".join(text.lower().split())


def topics_of(low: str, compiled: list, min_hits: int) -> list[int]:
    """Indices of the topics a normalised passage is on: every term group matches, and the terms
    match ``min_hits`` times in all."""
    found = []
    for i, (_, groups) in enumerate(compiled):
        total = 0
        for g in groups:
            c = len(g.findall(low))
            if c == 0:
                break
            total += c
        else:
            if total >= min_hits:
                found.append(i)
    return found


def passages(text: str, n: int, min_words: int) -> list[str]:
    from semantic.index import spans

    return [norm(text[a:b]) for a, b, _ in spans(text, n, min_words)]


def scan_text(text: str, compiled: list, min_hits: int, n: int, min_words: int) -> dict:
    """Words, passage count and, for each topic passage, [position, topic indices...]."""
    ps = passages(text, n, min_words)
    hits = []
    for i, p in enumerate(ps):
        on = topics_of(p, compiled, min_hits)
        if on:
            hits.append([i, *on])
    return {"words": len(text.split()), "passages": len(ps), "hits": hits}


# ------------------------------------------------------------------------------------ pure numbers
def era_of(year: int | None, eras: dict) -> str | None:
    if year is None:
        return None
    for name, (lo, hi) in eras.items():
        if lo <= year <= hi:
            return name
    return None


def is_reprint(died: int | None, year: int | None, gap: int) -> bool:
    return died is not None and year is not None and died < year - gap


def life_eras(died: int, eras: dict, writing_years: int) -> set[str]:
    """Eras overlapping an author's writing life (the ``writing_years`` up to death); an author
    dead before the first era is given the first era."""
    lo = died - writing_years
    got = {e for e, (a, b) in eras.items() if a <= died and b >= lo}
    if not got and died < min(a for a, _ in eras.values()):
        got = {min(eras, key=lambda e: eras[e][0])}
    return got


def counts_of(topic_lists: list[list[int]], k: int) -> np.ndarray:
    c = np.zeros(k, dtype=np.int64)
    for ts in topic_lists:
        for t in ts:
            c[t] += 1
    return c


def shares(counts: np.ndarray, alpha: float) -> np.ndarray:
    x = counts.astype(float) + alpha
    return x / x.sum()


def jsd(p: np.ndarray, q: np.ndarray) -> float:
    """Jensen-Shannon distance (square root of the divergence, base 2; 0 same, 1 disjoint)."""
    m = (p + q) / 2

    def kl(a: np.ndarray) -> float:
        nz = a > 0
        return float((a[nz] * np.log2(a[nz] / m[nz])).sum())

    return float(np.sqrt(max(0.0, (kl(p) + kl(q)) / 2)))


def draw(n: int, k: int, rng: np.random.Generator) -> tuple[np.ndarray, bool]:
    """``k`` indices of ``n`` items: without replacement if there are enough, else with (flag)."""
    if n >= k:
        return rng.choice(n, k, replace=False), False
    return rng.choice(n, k, replace=True), True


def adjacent(a: str, b: str, order: list[str]) -> bool:
    return abs(order.index(a) - order.index(b)) <= 1


def placed_era(nearest: list[str], med: dict[str, float]) -> str:
    """The era nearest in most repeats; a tie goes to the smaller median distance."""
    c = Counter(nearest)
    top = max(c.values())
    return min((e for e in c if c[e] == top), key=lambda e: med[e])


def key_seed(key: str) -> int:
    return zlib.crc32(key.encode())


def verdict(nearest_share: dict, gap_share: float, rank_e6: int, fits_none: bool, d: dict) -> str:
    """The card's yes / no / cannot tell for the book."""
    if fits_none:
        return "cannot tell"
    if nearest_share.get("E6", 0) >= d["yes_share"] and gap_share >= d["yes_gap_share"]:
        return "yes"
    early = sum(nearest_share.get(e, 0) for e in ("E1", "E2", "E3", "E4"))
    if early >= d["no_share"] or rank_e6 >= d["no_rank"]:
        return "no"
    return "cannot tell"


# ------------------------------------------------------------------------------------ library
def tcp_collections() -> dict[str, str]:
    got = {}
    for line in TCP.read_text().splitlines():
        r = json.loads(line)
        got[r["id"]] = r.get("collection")
    return got


def library_rows(cfg: dict) -> list[dict]:
    """Religious works 1640-1829 (lab.debates genre and Bible rule), with era, death year and
    reprint flag."""
    d, old = settings(cfg), cfg["lab"]["debates"]
    bible = re.compile(old["bible_title"], re.IGNORECASE)
    rows = [
        r
        for r in registry.load().to_pylist()
        if r["kind"] == "work"
        and r["has_text"]
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and d["year_min"] <= r["year"] <= d["year_max"]
        and old["gallery_genre"] in (r["genre"] or "").split(",")
    ]
    cat = door.catalog({r["work_id"] for r in rows})
    coll = tcp_collections()
    keep = []
    for r in rows:
        c = cat.get(r["work_id"])
        if c is None or not c["text_path"] or bible.search(" ".join((c["title"] or "").split())):
            continue
        died = death_year(c["author"])
        tcp = coll.get(c["source_id"]) if r["source"] == "tcp" else None
        keep.append({**c, **r, "died": died, "era": era_of(r["year"], d["eras"]),
                     "reprint": is_reprint(died, r["year"], d["reprint_gap"]),
                     "collection": tcp})  # fmt: skip
    return keep


_COMPILED: list = []
_ARGS: tuple = ()


def _init(topics: dict, min_hits: int, n: int, min_words: int) -> None:
    global _COMPILED, _ARGS
    _COMPILED = compile_topics(topics)
    _ARGS = (min_hits, n, min_words)


def _scan_job(row: dict) -> tuple[str, dict | None]:
    try:
        text = door.text_of(row)
    except OSError:
        return row["work_id"], None  # unreadable: not attempted, never a zero
    return row["work_id"], scan_text(text, _COMPILED, *_ARGS)


def scan_path(cfg: dict) -> Path:
    return SCAN / f"scan_{rules_hash(cfg)}.jsonl"


def load_scan(cfg: dict) -> dict[str, dict]:
    path = scan_path(cfg)
    got: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                got[r["work_id"]] = r
    return got


def scan_library(cfg: dict, rows: list[dict]) -> dict[str, dict]:
    """Topic passages of every work, appended to the scan file as they come (resumes; an
    unreadable work is recorded as such and tried again on the next run)."""
    from concurrent.futures import ProcessPoolExecutor

    d, s = settings(cfg), cfg["semantic"]
    have = load_scan(cfg)
    todo = [r for r in rows if have.get(r["work_id"], {}).get("state") != "done"]
    print(f"scan: {len(rows):,} works, {len(todo):,} to read", flush=True)
    t0, n = time.time(), 0
    args = (d["topics"], d["min_hits"], s["passage_words"], s["min_passage_words"])
    with (
        ProcessPoolExecutor(d["workers"], initializer=_init, initargs=args) as ex,
        out(scan_path(cfg)).open("a") as fh,
    ):
        for wid, res in ex.map(_scan_job, todo, chunksize=8):
            rec = {"work_id": wid, "state": "unreadable"} if res is None else {
                "work_id": wid, "state": "done", **res}  # fmt: skip
            fh.write(json.dumps(rec) + "\n")
            have[wid] = rec
            n += 1
            if n % 2000 == 0:
                fh.flush()
                print(f"  {n:,}/{len(todo):,} ({time.time() - t0:.0f} s)", flush=True)
    return have


def hits_of(rec: dict) -> list[list[int]]:
    return [h[1:] for h in rec.get("hits", [])]


# ------------------------------------------------------------------------------------ eras
class Eras:
    """Per era and repeat: eligible reference works in a seeded order, each with its seeded
    subsample of ``ref_passages`` topic passages counted by topic."""

    def __init__(self, rows: list[dict], scan: dict, d: dict, k: int) -> None:
        self.d, self.k, self.order = d, k, list(d["eras"])
        self.eligible: dict[str, list[dict]] = {}
        for e in self.order:
            self.eligible[e] = [
                r
                for r in rows
                if r["era"] == e
                and not r["reprint"]
                and scan.get(r["work_id"], {}).get("state") == "done"
                and len(scan[r["work_id"]]["hits"]) >= d["ref_min_passages"]
            ]
        barred = [e for e in self.order if e not in d["unbarred_eras"]]
        self.n_ref = min(d["ref_works_max"], *(len(self.eligible[e]) for e in barred))
        self.ids: dict[tuple[str, int], np.ndarray] = {}
        self.auth: dict[tuple[str, int], np.ndarray] = {}
        self.mat: dict[tuple[str, int], np.ndarray] = {}
        for ei, e in enumerate(self.order):
            works = self.eligible[e]
            hl = [hits_of(scan[r["work_id"]]) for r in works]
            for rep in range(d["repeats"]):
                rng = np.random.default_rng([d["seed"], ei, rep])
                perm = rng.permutation(len(works))
                m = np.zeros((len(works), k), dtype=np.int32)
                for j, w in enumerate(perm):
                    idx = rng.choice(len(hl[w]), d["ref_passages"], replace=False)
                    m[j] = counts_of([hl[w][i] for i in idx], k)
                self.mat[(e, rep)] = m
                self.ids[(e, rep)] = np.array([works[w]["work_id"] for w in perm])
                self.auth[(e, rep)] = np.array([works[w]["author_norm"] or "" for w in perm])

    def profile(self, e: str, rep: int, leave_ids: set, leave_authors: set) -> np.ndarray:
        ids, auth = self.ids[(e, rep)], self.auth[(e, rep)]
        ok = ~np.isin(ids, list(leave_ids)) if leave_ids else np.ones(len(ids), dtype=bool)
        if leave_authors:
            ok &= ~np.isin(auth, [a for a in leave_authors if a])
        take = np.flatnonzero(ok)[: self.n_ref]
        return self.mat[(e, rep)][take].sum(axis=0)

    def summary(self) -> dict:
        return {"works_per_reference": self.n_ref,
                "eligible_works": {e: len(v) for e, v in self.eligible.items()},
                "reference_works_used": {e: min(self.n_ref, len(v))
                                         for e, v in self.eligible.items()}}  # fmt: skip


def place(hl: list[list[int]], eras: Eras, d: dict, key: str, leave_ids: set = frozenset(),
          leave_authors: set = frozenset()) -> dict | None:  # fmt: skip
    """Distances from a text's topic profile to every era, over the repeats."""
    if not hl:
        return None
    order, k = eras.order, eras.k
    dist = {e: [] for e in order}
    nearest, gaps, replaced = [], [], False
    for rep in range(d["repeats"]):
        rng = np.random.default_rng([d["seed"], key_seed(key), rep])
        idx, rep_flag = draw(len(hl), d["unit_passages"], rng)
        replaced |= rep_flag
        p = shares(counts_of([hl[i] for i in idx], k), d["alpha"])
        row = {e: jsd(p, shares(eras.profile(e, rep, set(leave_ids), set(leave_authors)),
                                d["alpha"])) for e in order}  # fmt: skip
        for e in order:
            dist[e].append(row[e])
        nearest.append(min(row, key=row.get))
        if "E6" in row:
            gaps.append(min(v for e, v in row.items() if e not in ("E5", "E6")) - row["E6"])
    med = {e: statistics.median(v) for e, v in dist.items()}
    ranked = sorted(order, key=lambda e: med[e])
    share = {e: round(nearest.count(e) / len(nearest), 3) for e in order}
    pl = placed_era(nearest, med)
    return {
        "topic_passages": len(hl),
        "with_replacement": replaced,
        "placed": pl,
        "placed_share": share[pl],
        "nearest_share": share,
        "median_distance": {e: round(v, 4) for e, v in med.items()},
        "rank_e6": ranked.index("E6") + 1 if "E6" in ranked else None,
        "gap_e6_share": round(sum(g > 0 for g in gaps) / len(gaps), 3) if gaps else None,
        "gap_e6_median": round(statistics.median(gaps), 4) if gaps else None,
        "gap_e6_range": [round(min(gaps), 4), round(max(gaps), 4)] if gaps else None,
    }


# ------------------------------------------------------------------------------------ named texts
def revelation_book_1() -> str | None:
    if not REVELATION_BOOK_1.exists():
        return None
    pages = [json.loads(x) for x in REVELATION_BOOK_1.read_text().splitlines() if x.strip()]
    pages.sort(key=lambda p: int(p.get("page") or 0))
    return "\n".join(p.get("text") or "" for p in pages)


def blocks(text: str, n: int) -> list[str]:
    words = text.split()
    size = -(-len(words) // n)
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)][:n]


def text_hits(text: str, cfg: dict, compiled: list) -> list[list[int]]:
    d, s = settings(cfg), cfg["semantic"]
    rec = scan_text(text, compiled, d["min_hits"], s["passage_words"], s["min_passage_words"])
    return hits_of(rec)


def bom_hits(cfg: dict, compiled: list, drop_kjv: bool) -> tuple[list[list[int]], int, int]:
    """Topic lists of the 1830 text's passages (King James passages dropped if asked), words,
    and passages."""
    from semantic.search import bom_queries

    s = cfg["semantic"]
    qs = [q for q in bom_queries(s["passage_words"]) if q["words"] >= s["min_passage_words"]]
    if drop_kjv:
        qs = [q for q in qs if q["kjv_share"] <= s["max_query_kjv_share"]]
    hl = [topics_of(norm(q["text"]), compiled, settings(cfg)["min_hits"]) for q in qs]
    return [h for h in hl if h], sum(q["words"] for q in qs), len(qs)


def read_paths(spec) -> str | None:
    paths = spec if isinstance(spec, list) else [spec]
    try:
        return "\n".join(Path(p).read_text(encoding="utf-8", errors="replace") for p in paths)
    except OSError:
        return None


# ------------------------------------------------------------------------------------ topics file
def campbell_check(d: dict) -> dict:
    """Is each of Campbell's labels in the held copy of Delusions, near "decides all the great
    controversies"? (Every word of four letters or more in the window.)"""
    if not DELUSIONS.exists():
        return {"state": "not attempted: Delusions not on disk"}
    low = norm(DELUSIONS.read_text(errors="replace")).replace("- ", "")
    at = low.find("decides all the great")
    if at < 0:
        return {"state": "not attempted: list not found in the OCR"}
    win = low[at : at + 700]
    found = {lab: all(w in win for w in re.findall(r"[a-z]{4,}", lab)) for lab in d["campbell"]}
    return {"state": "checked", "char_offset": at, "labels_found_in_ocr": found}


def survey_support(cfg: dict) -> dict:
    d = settings(cfg)
    cat = door.catalog(set(d["surveys"].values()))
    got = {}
    for name, wid in d["surveys"].items():
        try:
            low = norm(door.text_of(cat[wid]))
        except (OSError, KeyError):
            got[name] = None  # not attempted
            continue
        got[name] = {t: len(re.findall(p, low)) for t, p in d["survey_terms"].items()}
    return got


def topics_file(cfg: dict) -> tuple[dict, dict]:
    d = settings(cfg)
    sup = survey_support(cfg)
    lab_topics = cfg["lab"]["debates"]["topics"]
    copied = {t for t, g in d["topics"].items() if g in lab_topics.values()}
    topics = {}
    for t, groups in d["topics"].items():
        named = {s: c[t] for s, c in sup.items() if c is not None and c[t] > 0}
        topics[t] = {"rule": groups, "survey_term": d["survey_terms"][t],
                     "survey_counts": {s: (c[t] if c else None) for s, c in sup.items()},
                     "named_by_surveys": sorted(named),
                     "campbell": t in d["campbell"].values(),
                     "marker_1820s": t in d["markers"],
                     "copied_from_lab_debates": t in copied}  # fmt: skip
    cat = door.catalog(set(d["surveys"].values()))
    surveys = {n: {"work_id": w, "year": None, "author": (cat.get(w) or {}).get("author"),
                   "read": sup[n] is not None} for n, w in d["surveys"].items()}  # fmt: skip
    for n in d["surveys"]:
        surveys[n]["year"] = int(re.search(r"(1[678]\d\d)", n).group(1))
    allt = {"topics": topics, "count": len(topics), "surveys": surveys,
            "min_hits": d["min_hits"],
            "how_built": "union of Campbell's twenty (Delusions, 1831, point 7), the controversies "
                         "named in the surveys' headings and the issue's list; rules written "
                         "before any count; survey counts record support only"}  # fmt: skip
    camp = {"source": DELUSIONS_URL, "where": "point 7 of the review", "ocr_check":
            campbell_check(d), "topics": {lab: {"topic": t, "rule": d["topics"][t]}
                                          for lab, t in d["campbell"].items()},
            "vogel_1993": VOGEL}  # fmt: skip
    return allt, camp


# ------------------------------------------------------------------------------------ step 1
def window_counts(rec: dict, start: int, w: int, k: int) -> np.ndarray:
    return counts_of([h[1:] for h in rec["hits"] if start <= h[0] < start + w], k)


def replicate(cfg: dict, rows: list[dict], scan: dict) -> dict:
    d, s = settings(cfg), cfg["semantic"]
    names = list(d["topics"])
    k = len(names)
    camp = {lab: names.index(t) for lab, t in d["campbell"].items()}
    compiled = compile_topics(d["topics"])

    def rates(c: np.ndarray, words: int) -> dict:
        return {lab: round(float(c[i]) / words * 1e5, 2) for lab, i in camp.items()}

    book = {}
    for name, drop in (("whole_1830_text", False), ("king_james_passages_dropped", True)):
        hl, words, n = bom_hits(cfg, compiled, drop)
        r = rates(counts_of(hl, k), words)
        book[name] = {"words": words, "passages": n, "per_100k_words": r,
                      "present": {lab: v >= d["present_min"] for lab, v in r.items()}}  # fmt: skip
    bodies = {}
    for bname, spec in d["replication_bodies"].items():
        lo, hi = spec["years"]
        pool = [
            r
            for r in rows
            if lo <= r["year"] <= hi
            and not r["reprint"]
            and scan.get(r["work_id"], {}).get("state") == "done"
            and scan[r["work_id"]]["passages"] > 0
            and (spec.get("tcp_collection") is None or r["collection"] == spec["tcp_collection"])
            and (spec.get("not_source") is None or r["source"] != spec["not_source"])
        ]
        draws = []
        for j in range(d["replication_draws"]):
            rng = np.random.default_rng([d["seed"], key_seed(bname), j])
            c, words, used = np.zeros(k, dtype=np.int64), 0, 0
            for wi in rng.permutation(len(pool)):
                rec = scan[pool[wi]["work_id"]]
                w = d["replication_window_passages"]
                start = int(rng.integers(0, max(1, rec["passages"] - w + 1)))
                c += window_counts(rec, start, w, k)
                words += min(w, rec["passages"] - start) * s["passage_words"]
                used += 1
                if words >= d["replication_words"]:
                    break
            r = rates(c, max(words, 1))
            draws.append({"works": used, "words": words, "per_100k_words": r,
                          "present": sum(v >= d["present_min"] for v in r.values())})  # fmt: skip
        bodies[bname] = {"pool_works": len(pool), "draws": draws}
    per_topic = {}
    for lab in camp:
        row = {
            "topic": d["campbell"][lab],
            "book_per_100k": book["whole_1830_text"]["per_100k_words"][lab],
            "in_book": book["whole_1830_text"]["present"][lab],
            "in_book_without_king_james": book["king_james_passages_dropped"]["present"][lab],
        }
        for bname, b in bodies.items():
            v = [x["per_100k_words"][lab] for x in b["draws"]]
            row[bname] = {
                "present_in_draws": sum(x >= d["present_min"] for x in v),
                "of": len(v),
                "median_per_100k": round(statistics.median(v), 2),
            }
        row["reproduced"] = "yes" if row["in_book"] else "no"
        per_topic[lab] = row  # fmt: skip
    summary = {"topics_in_book": sum(r["in_book"] for r in per_topic.values()),
               "of": len(per_topic),
               "present_per_body_median": {b: statistics.median(x["present"] for x in v["draws"])
                                           for b, v in bodies.items()},
               "topics_present_in_every_draw_of_every_body": sum(
                   all(r[b]["present_in_draws"] == r[b]["of"] for b in bodies)
                   for r in per_topic.values())}  # fmt: skip
    return {"campbell": {"per_topic": per_topic, "summary": summary, "book": book,
                         "bodies": bodies, "present_min_per_100k": d["present_min"]},
            "vogel_1993": VOGEL}  # fmt: skip


# ------------------------------------------------------------------------------------ check
def present_count(rec: dict, idx: list[int], k: int, present_min: float) -> int:
    c = counts_of(hits_of(rec), k)
    words = max(rec["words"], 1)
    return sum(c[i] / words * 1e5 >= present_min for i in idx)


def pools(rows: list[dict], scan: dict, d: dict, k: int, names: list[str]) -> dict:
    """Candidate texts per known-answer group, seeded order, before drawing."""
    ok = [r for r in rows if scan.get(r["work_id"], {}).get("state") == "done"
          and len(scan[r["work_id"]]["hits"]) >= d["unit_passages"]]  # fmt: skip
    camp = [names.index(t) for t in d["campbell"].values()]
    out_pools: dict[str, list[dict]] = {}
    named = [r for r in rows if r["work_id"] in d["decoy2_named"]]
    named.sort(key=lambda r: d["decoy2_named"].index(r["work_id"]))
    rest = [r for r in ok if r["era"] == "E1" and r["work_id"] not in d["decoy2_named"]
            and not r["reprint"]
            and present_count(scan[r["work_id"]], camp, k, d["present_min"])
            >= d["decoy2_min_campbell"]]  # fmt: skip
    _shuffle(rest, d, "decoy2")
    out_pools["decoy2_heresy_catalogues"] = named + rest
    taken = {r["work_id"] for r in out_pools["decoy2_heresy_catalogues"][: d["group_works"]]}
    for e in d["eras"]:
        p = [r for r in ok if r["era"] == e and not r["reprint"] and r["work_id"] not in taken]
        _shuffle(p, d, e)
        out_pools[e] = p
    lo, hi = d["decoy1_years"]
    p = [r for r in ok if lo <= r["year"] <= hi and r["died"] is not None
         and r["died"] < d["decoy1_died_before"]]  # fmt: skip
    _shuffle(p, d, "decoy1")
    out_pools["decoy1_old_reprints"] = p
    return out_pools


def _shuffle(rows: list, d: dict, name: str) -> None:
    rng = np.random.default_rng([d["seed"], key_seed(name)])
    perm = rng.permutation(len(rows))
    rows[:] = [rows[i] for i in perm]


def run_check(cfg: dict, rows: list[dict], scan: dict, eras: Eras, compiled: list) -> dict:
    d = settings(cfg)
    names, order = list(d["topics"]), eras.order
    by_author: dict[str, set[str]] = {}
    for r in rows:
        if r["author_norm"]:
            by_author.setdefault(r["author_norm"], set()).add(r["work_id"])
    groups = {}
    own_dist: list[float] = []
    for gname, pool in pools(rows, scan, d, len(names), names).items():
        texts = []
        for r in pool[: d["group_works"]]:
            rec = scan.get(r["work_id"], {})
            hl = hits_of(rec) if rec.get("state") == "done" else []
            leave = {r["work_id"]} | by_author.get(r["author_norm"] or "", set())
            pl = place(hl, eras, d, r["work_id"], leave, {r["author_norm"] or ""})
            if pl is None:
                texts.append(
                    {"work_id": r["work_id"], "state": "not attempted (no topic passages)"}
                )
                continue
            row = {"work_id": r["work_id"], "year": r["year"], "era": r["era"],
                   "source": r["source"], "died": r["died"], **pl}  # fmt: skip
            if gname in order:
                row["own"] = pl["placed"] == gname
                row["own_or_adjacent"] = adjacent(pl["placed"], gname, order)
                own_dist.append(pl["median_distance"][gname])
            elif gname == "decoy1_old_reprints":
                life = life_eras(r["died"], d["eras"], d["writing_years"])
                row["life_eras"] = sorted(life)
                row["in_life_era"] = pl["placed"] in life
            texts.append(row)
        groups[gname] = summarise(gname, texts, d, order)
    # register control: Revelation Book 1, four blocks
    rb = revelation_book_1()
    if rb is None:
        groups["register_revelation_book_1"] = {"state": "not attempted: source not on disk"}
    else:
        bl = []
        for i, b in enumerate(blocks(rb, d["register_blocks"])):
            pl = place(text_hits(b, cfg, compiled), eras, d, f"revelation_book_1:{i}")
            bl.append({"block": i + 1, "words": len(b.split()), **(pl or {"placed": None})})
        n_ok = sum(x["placed"] in d["register_eras"] for x in bl)
        groups["register_revelation_book_1"] = {
            "blocks": bl, "in_register_eras": n_ok,
            "passed": n_ok >= d["register_min_blocks"]}  # fmt: skip
    barred = [g for g in groups if g in order and g not in d["unbarred_eras"]]
    passed = all(groups[g].get("passed") for g in barred) and all(
        groups[g].get("passed")
        for g in ("decoy1_old_reprints", "decoy2_heresy_catalogues", "register_revelation_book_1")
    )
    thr = float(np.percentile(own_dist, d["fits_no_era_percentile"])) if own_dist else None
    return {"groups": groups, "barred_groups": barred + ["decoy1_old_reprints",
            "decoy2_heresy_catalogues", "register_revelation_book_1"],
            "passed": passed, "fits_no_era_distance": round(thr, 4) if thr else None,
            "reference": eras.summary()}  # fmt: skip


def summarise(gname: str, texts: list[dict], d: dict, order: list[str]) -> dict:
    ok = [t for t in texts if "placed" in t]
    n = len(ok)
    res: dict = {"texts": texts, "scored": n, "drawn": len(texts),
                 "placed": dict(Counter(t["placed"] for t in ok))}  # fmt: skip
    if gname in order:
        own = sum(t["own"] for t in ok)
        adj = sum(t["own_or_adjacent"] for t in ok)
        res |= {"own": own, "own_rate": round(own / max(n, 1), 3), "own_or_adjacent": adj,
                "own_or_adjacent_rate": round(adj / max(n, 1), 3),
                "chance_own": round(1 / len(order), 3)}  # fmt: skip
        if gname in d["unbarred_eras"] and n < d["group_works"]:
            res["bar"] = f"none ({n} of {d['group_works']} qualify)"
        res["passed"] = (n >= d["group_works"] and res["own_rate"] >= d["own_bar"]
                         and res["own_or_adjacent_rate"] >= d["adjacent_bar"])  # fmt: skip
    elif gname == "decoy1_old_reprints":
        e6 = sum(t["placed"] == "E6" for t in ok)
        life = sum(t["in_life_era"] for t in ok)
        res |= {"in_e6": e6, "e6_rate": round(e6 / max(n, 1), 3), "in_life_era": life,
                "life_rate": round(life / max(n, 1), 3)}  # fmt: skip
        res["passed"] = (n >= d["group_works"] and res["e6_rate"] <= d["decoy1_e6_max"]
                         and res["life_rate"] >= d["decoy1_life_min"])  # fmt: skip
    elif gname == "decoy2_heresy_catalogues":
        early = sum(t["placed"] in d["decoy2_early_eras"] for t in ok)
        e6 = sum(t["placed"] == "E6" for t in ok)
        res |= {"early": early, "early_rate": round(early / max(n, 1), 3), "in_e6": e6}
        res["passed"] = (n >= d["group_works"] and res["early_rate"] >= d["decoy2_early_min"]
                         and e6 <= d["decoy2_e6_max"])  # fmt: skip
    return res


# ------------------------------------------------------------------------------------ the book
def marker_rates(hl: list[list[int]], words: int, idx: dict[str, int]) -> dict:
    c = Counter(t for h in hl for t in h)
    return {m: round(c[i] / max(words, 1) * 1e5, 2) for m, i in idx.items()}


def run_book(cfg: dict, rows: list[dict], scan: dict, eras: Eras, compiled: list,
             chk: dict) -> dict:  # fmt: skip
    d = settings(cfg)
    names = list(d["topics"])
    hl, words, n = bom_hits(cfg, compiled, True)
    pl = place(hl, eras, d, "book_of_mormon_1830")
    fits_none = (
        chk["fits_no_era_distance"] is not None
        and min(pl["median_distance"].values()) > chk["fits_no_era_distance"]
    )
    ans = verdict(pl["nearest_share"], pl["gap_e6_share"], pl["rank_e6"], fits_none, d)
    midx = {m: names.index(m) for m in d["markers"]}
    e6 = [t for t in chk["groups"]["E6"]["texts"] if "placed" in t]
    e6_rates = []
    for t in e6:
        rec = scan[t["work_id"]]
        e6_rates.append(marker_rates(hits_of(rec), rec["words"], midx))
    rb = revelation_book_1()
    reg = marker_rates(text_hits(rb, cfg, compiled), len(rb.split()), midx) if rb else None
    c = counts_of(hl, len(names))
    book = {
        "passages": n, "words": words, "topic_passages": len(hl), **pl,
        "fits_no_era": fits_none, "verdict": ans,
        "topic_shares_all_passages": {t: round(float(c[i]) / max(len(hl), 1), 4)
                                      for i, t in enumerate(names)},
        "silent_topics": [t for i, t in enumerate(names) if c[i] == 0],
        "markers_per_100k": {
            "book": marker_rates(hl, words, midx),
            "e6_controls_range": {m: [min(r[m] for r in e6_rates), statistics.median(
                r[m] for r in e6_rates), max(r[m] for r in e6_rates)] for m in midx}
            if e6_rates else None,
            "register_control_revelation_book_1": reg,
        },
    }  # fmt: skip
    controls = {"bible_style": {}, "translations": {}, "joseph_smith_dictations": {}}
    for name, spec in cfg["lab"]["translation"]["imitations"].items():
        if name == "short_pieces":
            continue
        text = read_paths(spec)
        if text is None:
            controls["bible_style"][name] = {"state": "not attempted"}
            continue
        pl2 = place(text_hits(text, cfg, compiled), eras, d, "bible:" + name)
        controls["bible_style"][name] = pl2 or {"state": "no topic passages"}
    tr = re.compile(cfg["lab"]["translation"]["translation_title"], re.IGNORECASE)
    lo, hi = d["translation_years"]
    cand = [r for r in rows if lo <= r["year"] <= hi and r["died"] is not None
            and r["died"] < d["translation_written_before"]
            and tr.search(" ".join(f"{r['title'] or ''} {r['author'] or ''}".split()))
            and scan.get(r["work_id"], {}).get("state") == "done"]  # fmt: skip
    _shuffle(cand, d, "translations")
    for r in cand[: d["translations_n"]]:
        pl2 = place(hits_of(scan[r["work_id"]]), eras, d, r["work_id"], {r["work_id"]})
        life = life_eras(r["died"], d["eras"], d["writing_years"])
        controls["translations"][r["work_id"]] = (
            {**pl2, "year": r["year"], "died": r["died"], "life_eras": sorted(life),
             "placed_by_first_writing": pl2["placed"] in life, "placed_e6": pl2["placed"] == "E6"}
            if pl2 else {"state": "no topic passages"})  # fmt: skip
    controls["translations_candidates"] = len(cand)
    from lab import emode

    js = emode.js_texts()
    for name in ("js-1828-1829-revelations", "revelations-later-1830", "revelations-later-1831",
                 "dictated-visions_of_moses_1830"):  # fmt: skip
        text = js.get(name)
        pl2 = place(text_hits(text, cfg, compiled), eras, d, "js:" + name) if text else None
        controls["joseph_smith_dictations"][name] = pl2 or {"state": "not attempted"}
    return {"book_of_mormon": book, "controls": controls}


# ------------------------------------------------------------------------------------ precision
DESCRIBE = {
    "infant_baptism": "whether infants or young children should be baptized",
    "ordination": "ordaining ministers, priests or elders (laying on of hands, holy orders)",
    "trinity": "the Trinity or the Godhead (Father, Son and Spirit as one God)",
    "regeneration": "regeneration: being born again, a change of heart, a new creature",
    "repentance": "repentance from sin",
    "justification": "justification (by faith, works or grace; or antinomianism)",
    "fall_of_man": "the fall of Adam or of man, original sin, fallen human nature",
    "atonement": "the atonement: Christ's death as a sacrifice, ransom or satisfaction for sin",
    "transubstantiation": "the Lord's Supper or sacrament (bread and wine, real presence)",
    "fasting": "fasting (with prayer)",
    "penance": "penance, confession to a priest, absolution, purgatory or acts of mortification",
    "church_government": "church government or discipline (episcopacy, presbytery, "
                         "independency, casting out members)",
    "religious_experience": "religious experience: conversion, felt joy or pardon, visions, "
                            "being overcome by the Spirit",
    "call_to_ministry": "a call to the ministry or to preach",
    "general_resurrection": "the resurrection of the dead",
    "eternal_punishment": "eternal or endless punishment, hell, torment",
    "who_may_baptize": "who has authority to baptize",
    "freemasonry": "freemasonry or secret societies and their oaths",
    "republican_government": "kings against judges or republican government; liberty, tyranny",
    "rights_of_man": "rights, liberty, freedom of conscience, toleration",
    "universal_salvation": "universal salvation (that all will be saved) or its denial",
    "free_will_predestination": "free will against predestination or election",
    "paid_clergy": "paid clergy, priestcraft, preaching for gain, tithes",
    "revelation_ceased": "whether revelation, miracles or spiritual gifts have ceased",
    "gathering_israel": "the gathering or restoration of Israel or the Jews",
    "millennium": "the millennium or the second coming of Christ",
    "antitrinitarian": "the divinity of Christ (Arian, Socinian or Unitarian views)",
    "inner_light": "the inner light or the Spirit of Christ given to every man (Quakers)",
    "popery": "popery, the church of Rome, Antichrist, idolatry",
    "sabbath": "keeping or profaning the Sabbath",
    "oaths_war": "whether a Christian may swear oaths or bear arms (non-resistance)",
    "soul_state": "the state of the soul between death and resurrection (soul sleep, paradise)",
    "deism_infidelity": "deism, atheism or infidelity, denying God or revelation",
    "temperance": "drunkenness, strong drink or temperance",
    "missions_bible_societies": "missions: preaching to the heathen or other peoples, "
                                "missionary or Bible societies",
    "revivals": "revivals, awakenings, many being converted or added to the church",
    "slavery": "slavery, slaves or the slave trade",
    "marriage_divorce": "divorce, polygamy, many wives or concubines",
    "lay_preaching": "lay or unlearned preachers, women preaching, whether a learned ministry is "
                     "needed",
}  # fmt: skip


def precision_samples(cfg: dict, rows: list[dict], scan: dict) -> tuple[list[dict], dict]:
    """``precision_sample`` hits per topic per era (seeded), with their passages (private)."""
    d, s = settings(cfg), cfg["semantic"]
    names = list(d["topics"])
    by_id = {r["work_id"]: r for r in rows}
    want: dict[str, list[tuple[str, int, str]]] = {}
    counts = {}
    for e in d["eras"]:
        works = [r["work_id"] for r in rows if r["era"] == e and not r["reprint"]
                 and scan.get(r["work_id"], {}).get("state") == "done"]  # fmt: skip
        for ti, t in enumerate(names):
            hits = [(w, h[0]) for w in works for h in scan[w]["hits"] if ti in h[1:]]
            counts[f"{t}:{e}"] = len(hits)
            rng = np.random.default_rng([d["seed"], key_seed(f"{t}:{e}")])
            pick = rng.choice(len(hits), min(d["precision_sample"], len(hits)), replace=False) \
                if hits else []  # fmt: skip
            for i in pick:
                w, pos = hits[int(i)]
                want.setdefault(w, []).append((t, pos, e))
    samples = []
    for w, items in want.items():
        try:
            ps = passages(door.text_of(by_id[w]), s["passage_words"], s["min_passage_words"])
        except OSError:
            continue  # unreadable now: left out, counted below
        for t, pos, e in items:
            samples.append({"id": f"{t}|{e}|{w}|{pos}", "topic": t, "era": e, "work_id": w,
                            "passage": pos, "text": ps[pos]})  # fmt: skip
    return samples, counts


def judge_prompt(topic: str, text: str) -> str:
    return (
        "You are checking a word-search rule for a study of religious print, 1640-1829. Read "
        "the passage and answer with one word, YES or NO: is this passage about "
        f"{DESCRIBE[topic]}? A passing mention that is about something else is NO.\n\n{text}"
    )


def parse_yes_no(reply: str) -> str | None:
    m = re.match(r"\W*(YES|NO)\b", (reply or "").strip(), re.I)
    return m.group(1).upper() if m else None


def precision_from_answers(jobs: list[dict], answers: list[dict], d: dict) -> dict:
    """Per topic: share of judged hits answered YES, overall and per era; below the bar is
    flagged (simulated judging)."""
    got = {a["id"]: parse_yes_no(a["reply"]) for a in answers}
    per: dict[str, dict] = {}
    for j in jobs:
        t, e = j["id"].split("|")[:2]
        a = got.get(j["id"])
        if a is None:
            continue
        p = per.setdefault(t, {"yes": 0, "n": 0, "by_era": {}})
        p["n"] += 1
        p["yes"] += a == "YES"
        pe = p["by_era"].setdefault(e, [0, 0])
        pe[0] += a == "YES"
        pe[1] += 1
    for p in per.values():
        p["precision"] = round(p["yes"] / p["n"], 3) if p["n"] else None
        p["below_bar"] = p["precision"] is not None and p["precision"] < d["precision_min"]
    return per


# ------------------------------------------------------------------------------------ part B
PART_B_QUESTIONS = {
    "infant_baptism": ("Which side does this passage take on baptizing infants?",
                       ["FOR infant baptism", "AGAINST infant baptism", "NONE"]),
    "universal_salvation": ("Which side does it take on universal salvation?",
                            ["ALL will be saved", "NOT all will be saved", "NONE"]),
    "free_will_predestination": ("Which side does it take on salvation and the will?",
                                 ["FREE will (Arminian)", "PREDESTINATION (Calvinist)", "NONE"]),
    "paid_clergy": ("Which side does it take on paying ministers?",
                    ["AGAINST paid clergy", "FOR a maintained ministry", "NONE"]),
    "revelation_ceased": ("Which side does it take on revelation and spiritual gifts today?",
                          ["CONTINUE", "CEASED", "NONE"]),
    "trinity": ("Which view of the Godhead does it express?",
                ["TRINITARIAN", "ANTITRINITARIAN", "NONE"]),
    "church_government": ("Which church government does it favour?",
                          ["EPISCOPAL", "PRESBYTERIAN", "CONGREGATIONAL", "NONE"]),
    "republican_government": ("Which civil government does it favour?",
                              ["KINGS", "JUDGES or REPUBLIC", "NONE"]),
}  # fmt: skip


def part_b_prompt(topic: str, text: str) -> str:
    q, opts = PART_B_QUESTIONS[topic]
    first = [o.split()[0] for o in opts]
    return (f"{q} Answer with one word from: {', '.join(first)} (meaning: "
            f"{'; '.join(opts)}). If the passage only reports or quotes an opponent's view, answer "
            f"for the passage's own side. NONE if it takes no side.\n\n{text}")  # fmt: skip


def part_b_parse(reply: str, topic: str) -> str | None:
    first = [o.split()[0].upper() for o in PART_B_QUESTIONS[topic][1]]
    m = re.match(r"\W*([A-Z]+)\b", (reply or "").strip().upper())
    return m.group(1) if m and m.group(1) in first else None


# ------------------------------------------------------------------------------------ driver
def stamp(res: dict, cfg: dict) -> dict:
    res["settings_sha256"] = settings_hash(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    return res


def write(path: Path, res: dict) -> None:
    out(path).write_text(json.dumps(res, indent=1) + "\n")
    print(f"-> {path}", flush=True)


def scan_state(rows: list[dict], scan: dict) -> dict:
    st = Counter(scan.get(r["work_id"], {}).get("state", "not attempted") for r in rows)
    return {"works": len(rows), **dict(st)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["topics", "scan", "replicate", "check", "run", "precision",
                                    "partb", "partb-score"])  # fmt: skip
    a = ap.parse_args(argv)
    cfg = config.load()
    d = settings(cfg)
    if a.cmd == "topics":
        allt, camp = topics_file(cfg)
        write(OUT / "topics_v3.json", stamp(allt, cfg))
        write(OUT / "campbell_topics_v3.json", stamp(camp, cfg))
        return 0
    rows = library_rows(cfg)
    if a.cmd == "scan":
        scan = scan_library(cfg, rows)
        print(json.dumps(scan_state(rows, scan)))
        return 0
    scan = load_scan(cfg)
    st = scan_state(rows, scan)
    if st.get("done", 0) < len(rows) - st.get("unreadable", 0):
        raise SystemExit(f"the scan is not finished ({st}); run `python -m lab.debates3 scan`")
    compiled = compile_topics(d["topics"])
    if a.cmd == "replicate":
        write(OUT / "replication_v3.json", stamp({"scan": st, **replicate(cfg, rows, scan)}, cfg))
        return 0
    if a.cmd == "precision":
        samples, counts = precision_samples(cfg, rows, scan)
        path = CARD / "precision_samples_v3.jsonl"
        out(path).write_text("".join(json.dumps(x) + "\n" for x in samples))
        jobs = [{"id": x["id"], "prompt": judge_prompt(x["topic"], x["text"])} for x in samples]
        out(CARD / "precision_jobs_v3.jsonl").write_text(
            "".join(json.dumps(j) + "\n" for j in jobs))  # fmt: skip
        write(OUT / "precision_v3.json", stamp({"samples": len(samples), "hits_by_topic_era":
                                                counts, "judged": "not run"}, cfg))  # fmt: skip
        return 0
    if a.cmd in ("partb", "partb-score"):
        chk_path = OUT / "check_v3.json"
        if not chk_path.exists() or not json.loads(chk_path.read_text())["known_answer"]["passed"]:
            raise SystemExit("Part B waits for Part A's known-answer check to pass")
        raise SystemExit("Part B's reference writers are fixed on its own card first")
    eras = Eras(rows, scan, d, len(d["topics"]))
    path = OUT / "check_v3.json"
    chk = None
    if a.cmd == "run" and path.exists():
        old = json.loads(path.read_text())
        if old.get("settings_sha256") == settings_hash(cfg):
            chk = old["known_answer"]
            print("known-answer check reused from check_v3.json (same settings)", flush=True)
    if chk is None:
        chk = run_check(cfg, rows, scan, eras, compiled)
        write(path, stamp({"scan": st, "known_answer": chk}, cfg))
    print(json.dumps({g: {k: v for k, v in x.items() if k not in ("texts", "blocks")}
                      for g, x in chk["groups"].items()}, indent=1))  # fmt: skip
    print("passed" if chk["passed"] else "MISSED: the Book of Mormon is not scored")
    if a.cmd == "check":
        return 0
    res = {"scan": st, "known_answer_passed": chk["passed"], "reference": chk["reference"]}
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
    else:
        res |= run_book(cfg, rows, scan, eras, compiled, chk)
        b = res["book_of_mormon"]
        print(
            json.dumps(
                {
                    k: b[k]
                    for k in (
                        "placed",
                        "nearest_share",
                        "median_distance",
                        "rank_e6",
                        "gap_e6_share",
                        "verdict",
                    )
                },
                indent=1,
            )
        )
    write(OUT / "result_v3.json", stamp(res, cfg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
