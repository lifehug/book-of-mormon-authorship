"""BOM-126: where the sources critics have named rank against the whole library.

Donofrio names histories of the American Revolution (Mercy Otis Warren, David Ramsay) for the war
chapters; Davis names Bunyan's *Pilgrim's Progress* for the Abinadi story. The study ranked *The
Late War*, *View of the Hebrews* and *The First Book of Napoleon* against every volume; this looks
the newly named books up in the same stored searches, with those three beside them for scale. No
new search of the library is run and no index is built or changed.

- **Rare shared phrases:** the stored scan (``data/reuse/bom/hits.parquet``) re-ranked for every
  volume with the study's own functions, because ``rare.json`` keeps only the top 100.
- **Meaning search (paraphrase, ideas):** ``data/semantic/corpus_bom.json``.
- **Exact reuse** and **story order:** listed in the stored results or not.
- **Passage level:** the study's stored Book of Mormon query vectors for the Abinadi story and the
  war chapters; which works fill the stored nearest passages, and where each claimed source's own
  passages fall, scored from the study's index vectors against a random sample of the gallery.

The test card, written first, is ``data/private/lab/owner/2026-11-20-claimed-sources/card.md``;
settings are ``lab.claimed_sources`` in the config. The output holds ids, titles, ranks and scores,
no passage text.

Usage::

    python -m lab.claimed_sources check     # the three known-answer checks only
    python -m lab.claimed_sources run       # -> data/lab/reruns/claimed_sources/result.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from lab import door, registry
from lab.paths import REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "claimed_sources"
CATALOG = Path("data/catalog/catalog.parquet")
BOM_HITS = Path("data/reuse/bom/hits.parquet")
LATE_WAR_HITS = Path("data/reuse/null_sizing/hits.parquet")
RARE = Path("data/reuse/bom/rare.json")
SEAL_CHECK = Path("data/reuse/bom/sealed_check.json")
CORPUS = Path("data/semantic/corpus_bom.json")
PARALLELS = Path("data/semantic/parallels_bom.parquet")
EXACT = Path("data/reuse/exact/sources/bom_full.json")
SKELETON = (Path("data/semantic/skeleton/top.json"), Path("data/semantic/skeleton/bom.json"))
GRUNDER = Path("data/semantic/grunder_ranks.json")
SEARCH = Path("data/corpus/semantic/search")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")


# ---- finding the copies -------------------------------------------------------------------


def find_copies(patterns: dict[str, list[str]], cat: list[dict]) -> dict[str, list[str]]:
    """key -> work ids whose catalogued author and title match the key's two patterns."""
    found: dict[str, list[str]] = {}
    for key, (author, title) in patterns.items():
        a, t = re.compile(author, re.I), re.compile(title, re.I)
        found[key] = sorted(
            r["work_id"]
            for r in cat
            if r["title"] and t.search(r["title"]) and a.search(r["author_norm"] or "")
        )
    return found


# ---- rare shared phrases ------------------------------------------------------------------


def rare_table(hits: Path, cfg: dict, sealed: set[str]) -> dict:
    """Every period volume's rare-phrase density and rank, as ``reuse.rare score`` computes them."""
    from metadata.dates import catalog_years, effective_year
    from reuse.rare import densities, doc_freq

    b = cfg["borrowing"]
    lo, hi = cfg["corpus"]["date_range"]
    years = catalog_years()
    recs, eff = [], {}
    for r in pq.read_table(hits).to_pylist():
        if not r["words"] or r["work_id"] in sealed:
            continue
        y = effective_year(r["work_id"], years.get(r["work_id"]))
        if y is not None and lo <= y <= hi:
            recs.append(r)
            eff[r["work_id"]] = y
    df = doc_freq(recs, b["df_by_text"])
    rare = {g for g, c in df.items() if c <= b["max_df"]}
    dens = densities(recs, rare, b["per_words"])
    order = sorted(dens, key=lambda w: -dens[w])
    return {
        "population": len(recs),
        "order": order,
        "rank": {w: i + 1 for i, w in enumerate(order)},
        "density": dens,
        "shared": {r["work_id"]: sum(g in rare for g in r["hits"]) for r in recs},
        "words": {r["work_id"]: r["words"] for r in recs},
        "year": eff,
        "null": np.sort(np.array(list(dens.values()))),
    }


def rare_row(w: str, t: dict) -> dict | None:
    """One volume's place in the rare-phrase population; None if it is not in the population."""
    if w not in t["rank"]:
        return None
    d = t["density"][w]
    above = len(t["null"]) - int(np.searchsorted(t["null"], d, side="left"))
    return {
        "rank": t["rank"][w],
        "of": t["population"],
        "top_share": round(t["rank"][w] / t["population"], 5),
        "shared_rare_phrases": t["shared"][w],
        "per_10000_words": round(d, 3),
        "tied_at_zero": t["shared"][w] == 0,  # the rank among volumes sharing none is arbitrary
        "p": round((above + 1) / (len(t["null"]) + 1), 5),  # ties against the source, as the study
        "words": t["words"][w],
    }


def sealed_ids_of_scan() -> set[str]:
    """Volumes the study's scan kept out as copies of the Book of Mormon (its cached check)."""
    from metadata.sealed import MIN_SHARED

    counts = json.loads(SEAL_CHECK.read_text())["counts"]
    return {w for w, c in counts.items() if c >= MIN_SHARED}


# ---- meaning search -----------------------------------------------------------------------

_MEANING = ("rank", "score", "percentile", "stands_out", "genre", "words", "parallels")


def meaning_row(w: str, ranking: dict[str, dict], gallery: set[str]) -> dict:
    if w in ranking:
        return {"status": "ranked", **{k: ranking[w][k] for k in _MEANING}}
    return {"status": "in the gallery, no parallel" if w in gallery else "not in the gallery"}


def best_meaning(ids: list[str], ranking: dict[str, dict]) -> str | None:
    """The copy that stands for the source: highest percentile, then best rank (as
    ``eval.grunder_ranks``)."""
    vols = [ranking[w] for w in ids if w in ranking]
    if not vols:
        return None
    return max(vols, key=lambda r: (r["percentile"] or 0, -r["rank"]))["work_id"]


# ---- known-answer checks ------------------------------------------------------------------


def check_late_war(cfg: dict) -> dict:
    """Known answer 1: with The Late War as the target, its other printings rank at the top."""
    from reuse.rare import STAND_IN

    c = cfg["lab"]["claimed_sources"]
    t = rare_table(LATE_WAR_HITS, cfg, set())
    cat = pq.read_table(CATALOG, columns=["work_id", "title", "author_norm"]).to_pylist()
    # Hunt's own printings only. The first form of this check took ``reuse.rare.target_copies``,
    # which also returns other histories of the same war (a list of volumes to leave out of the
    # frequencies, not a list of reprints); see the test card.
    printings = find_copies({"k": c["ka_late_war"]}, cat)["k"]
    copies = {w for w in printings if w in t["rank"]} - {STAND_IN}
    ranks = sorted(t["rank"][w] for w in copies)
    return {
        "population": t["population"],
        "other_printings": len(copies),
        "ranks": ranks,
        "other_histories_of_that_war_best_rank": min(
            (
                t["rank"][r["work_id"]]
                for r in cat
                if r["work_id"] in t["rank"]
                and r["work_id"] not in copies
                and re.search(r"late war.{0,80}(1812|britain)", r["title"] or "", re.I)
            ),
            default=None,
        ),
        "bar_rank": c["ka_top"],
        "passed": bool(ranks) and max(ranks) <= c["ka_top"],
    }


def check_published(t: dict, ranking: dict[str, dict], cat: list[dict], cfg: dict) -> dict:
    """Known answer 2: the re-ranking and the lookup reproduce the published numbers."""
    from eval.grunder_ranks import entries

    pub = json.loads(RARE.read_text())
    top_same = [r["work_id"] for r in pub["top"]] == t["order"][: len(pub["top"])]
    scale = find_copies(cfg["lab"]["claimed_sources"]["scale"], cat)
    named = {}
    for key, ids in scale.items():
        mine = min((t["rank"][w] for w in ids if w in t["rank"]), default=None)
        named[key] = {"published": pub["named"][key]["rank"], "here": mine}
    g = {e["entry"]: e for e in json.loads(GRUNDER.read_text())["entries"]}
    tried = same = 0
    for e in entries():
        if e["basis"] != "author+title":
            continue
        tried += 1
        best = best_meaning(e["work_ids"], ranking)
        theirs = g[e["entry"]]["best"]
        same += (best is None and theirs is None) or (
            best is not None
            and theirs is not None
            and best == theirs["work_id"]
            and ranking[best]["rank"] == theirs["rank"]
        )
    ok = (
        t["population"] == pub["population"]
        and top_same
        and all(v["published"] == v["here"] for v in named.values())
        and tried > 0
        and same == tried
    )
    return {
        "population": {"published": pub["population"], "here": t["population"]},
        "top_100_same_order": top_same,
        "named_ranks": named,
        "grunder_entries": tried,
        "grunder_entries_same": same,
        "passed": bool(ok),
    }


# ---- passage level ------------------------------------------------------------------------


def query_paragraphs(n: int) -> list[Counter]:
    """For each stored query passage (``n`` words, cut as ``semantic.search.bom_queries`` cuts
    them), how many of its words fall in each 1830 paragraph (``seq``)."""
    seqs: list[int] = []
    for ln in EDITION.read_text().splitlines():
        r = json.loads(ln)
        if r["book"]:
            seqs += [r["seq"]] * len(r["text"].split())
    return [Counter(seqs[i : i + n]) for i in range(0, len(seqs), n)]


def target_queries(paras: list[Counter], wanted: set[int]) -> list[int]:
    """Queries with more than half their words inside the wanted paragraphs."""
    return [
        i
        for i, c in enumerate(paras)
        if 2 * sum(k for s, k in c.items() if s in wanted) > sum(c.values())
    ]


def targets(cfg: dict) -> dict[str, set[int]]:
    """Target name -> its 1830 paragraph numbers."""
    c = cfg["lab"]["claimed_sources"]
    lo, hi = c["abinadi_seq"]
    war, single = set(), set()
    for ln in LABELS.read_text().splitlines():
        r = json.loads(ln)
        if r["book"] == c["war"]["book"] and r["kind"] == "body":
            if c["war"]["first"] <= r["chapter_1830"] <= c["war"]["last"]:
                war.add(r["seq"])
            if r["chapter_1830"] == c["war"]["single"]:
                single.add(r["seq"])
    return {"abinadi": set(range(lo, hi + 1)), "war_chapters": war, "war_one_chapter": single}


def place(score: float, sample_sorted: np.ndarray, gallery_passages: int) -> dict:
    """Where a score falls among all gallery passages, estimated from the sorted sample scores."""
    above = len(sample_sorted) - int(np.searchsorted(sample_sorted, score, side="right"))
    return {
        "sample_above": above,
        "share_above": round(above / len(sample_sorted), 6),
        "estimated_rank": 1 + round(above / len(sample_sorted) * gallery_passages),
    }


class Vectors:
    """The study's passage vectors, read through the lab's companion index (read only)."""

    def __init__(self) -> None:
        from lab.passages import Index
        from semantic.index import INDEX

        self.ix, self.dir = Index(), INDEX
        self.work_no = {w: i for i, w in enumerate(self.ix.works)}

    def rows_of(self, ids: set[str]) -> dict[str, np.ndarray]:
        """work id -> its passage rows in the index (first copy if a volume sits in two shards)."""
        nos = {self.work_no[w]: w for w in ids if w in self.work_no}
        if not nos:
            return {}
        wanted = np.fromiter(nos, dtype=np.int32)
        hit = np.flatnonzero(np.isin(self.ix.rows, wanted))
        by: dict[str, np.ndarray] = {}
        for no, w in nos.items():
            by[w] = hit[self.ix.rows[hit] == no]
        return by

    def get(self, rows: np.ndarray) -> np.ndarray:
        vec = np.empty((len(rows), 384), dtype=np.float32)
        which = np.searchsorted(self.ix.starts, rows, side="right") - 1
        for s in np.unique(which):
            sel = which == s
            m = np.load(self.dir / f"{self.ix.shards[s]['name']}.npy", mmap_mode="r")
            vec[sel] = np.asarray(m[rows[sel] - self.ix.starts[s]], dtype=np.float32)
        return vec

    def sample(self, gallery: set[str], n: int, seed: int) -> tuple[np.ndarray, int]:
        """``n`` gallery passages drawn at random (their vectors), and the gallery's passage
        count."""
        ok = self.ix.allowed(gallery)
        total = 0
        step = 20_000_000
        for a in range(0, len(self.ix.rows), step):
            total += int(ok[self.ix.rows[a : a + step]].sum())
        rng = np.random.default_rng(seed)
        draw = np.unique(rng.integers(0, len(self.ix.rows), int(n * 1.6)))
        draw = draw[ok[self.ix.rows[draw]]]
        if len(draw) < n:
            raise SystemExit(f"sample too small: {len(draw)} of {n}")
        return self.get(np.sort(rng.choice(draw, n, replace=False))), total


def trial_passages(row: dict, pattern: re.Pattern, cfg: dict) -> list[int] | None:
    """Passage numbers of a volume that hold the marker; None if the text cannot be read."""
    from semantic.index import spans

    s = cfg["semantic"]
    try:
        text = door.text_of(row)
    except OSError:
        return None  # unreadable: not attempted, never "no trial scene"
    sp = spans(text, s["passage_words"], s["min_passage_words"])
    return [i for i, (a, b, _n) in enumerate(sp) if pattern.search(text[a:b])]


def trial_rows(ids: list[str], vec: Vectors, cfg: dict) -> dict:
    """Index rows of Faithful's trial in each indexed copy that holds it."""
    c = cfg["lab"]["claimed_sources"]
    pattern = re.compile(c["trial_marker"], re.I)
    cat = door.catalog(set(ids))
    rows_of = vec.rows_of(set(ids))
    found, unreadable, mismatch = {}, [], []
    for w in sorted(rows_of):
        nums = trial_passages(cat[w], pattern, cfg)
        if nums is None:
            unreadable.append(w)
            continue
        rows = rows_of[w]
        if nums and max(nums) >= len(rows):
            mismatch.append(w)  # the text on disk is not the text that was indexed
            continue
        if nums:
            found[w] = {"passages": nums, "rows": rows[nums]}
    return {"found": found, "unreadable": unreadable, "mismatch": mismatch, "all": rows_of}


def check_reprint(trial: dict, vec: Vectors, sample: np.ndarray, cfg: dict) -> dict:
    """Known answer 3: one printing's trial passages as queries; every other printing that holds
    the trial must come out among the nearest passages in the library."""
    c = cfg["lab"]["claimed_sources"]
    copies = sorted(trial["found"])
    if len(copies) < 2:
        return {"copies_with_trial": len(copies), "passed": False, "reason": "fewer than 2 copies"}
    q = vec.get(trial["found"][copies[0]]["rows"])
    base = np.sort(q @ sample.T, axis=1)
    pairs = hit = 0
    for w in copies[1:]:
        best = (q @ vec.get(trial["all"][w]).T).max(axis=1)
        for i, s in enumerate(best):
            above = base.shape[1] - int(np.searchsorted(base[i], s, side="right"))
            pairs += 1
            hit += above / base.shape[1] <= c["ka_pair_share"]
    rate = hit / max(pairs, 1)
    return {
        "query_copy": copies[0],
        "query_passages": len(q),
        "other_copies": len(copies) - 1,
        "pairs": pairs,
        "found": hit,
        "rate": round(rate, 3),
        "bar": c["ka_pair_bar"],
        "passed": rate >= c["ka_pair_bar"],
    }


def passage_level(
    found: dict[str, list[str]],
    trial: dict,
    vec: Vectors,
    sample: np.ndarray,
    gallery_passages: int,
    gallery: set[str],
    cfg: dict,
) -> dict:
    c = cfg["lab"]["claimed_sources"]
    s = cfg["semantic"]
    z = np.load(SEARCH / "q_bom.npz")
    qv, kjv = z["q"].astype(np.float32), z["kjv_share"]
    cut = np.load(SEARCH / "scan_state.npz")["bom|bom:window|s"].min(axis=1)
    paras = query_paragraphs(s["passage_words"])
    if len(paras) != len(qv):
        raise SystemExit(f"{len(paras)} query passages rebuilt, {len(qv)} stored")
    par = pq.read_table(PARALLELS, columns=["query", "work_id", "score"]).to_pylist()
    by_query: dict[int, list[tuple[str, float]]] = {}
    for p in par:
        by_query.setdefault(p["query"], []).append((p["work_id"], p["score"]))
    reg = {r["work_id"]: r for r in registry.load().to_pylist() if r["work_id"] in gallery}
    in_gallery = {k: [w for w in ids if w in gallery] for k, ids in found.items()}
    rows_of = vec.rows_of({w for ids in in_gallery.values() for w in ids})
    owner = {w: k for k, ids in in_gallery.items() for w in ids}
    groups = {
        k: (np.concatenate([rows_of[w] for w in ids if w in rows_of] or [np.empty(0, np.int64)]))
        for k, ids in in_gallery.items()
    }
    groups["bunyan_trial_scene"] = np.concatenate(
        [v["rows"] for v in trial["found"].values()] or [np.empty(0, np.int64)]
    )
    vectors = {k: vec.get(r) for k, r in groups.items() if len(r)}
    res = {}
    for name, wanted in targets(cfg).items():
        qs_all = target_queries(paras, wanted)
        qs = [i for i in qs_all if kjv[i] <= s["max_query_kjv_share"]]
        q = qv[qs]
        base = np.sort(q @ sample.T, axis=1)
        places = [(w, sc) for i in qs for w, sc in by_query.get(i, [])]
        genres = Counter((reg[w]["genre"] or "uncertain").split(",")[0] for w, _ in places)
        works = Counter(w for w, _ in places)
        titles = door.catalog({w for w, _ in works.most_common(c["top_works"])})
        per = {}
        for k in list(in_gallery) + ["bunyan_trial_scene"]:
            n_pass = len(groups[k])
            if not n_pass:
                per[k] = {"status": "no passages in the gallery: not attempted"}
                continue
            sc = q @ vectors[k].T
            best = sc.max(axis=1)
            est = [place(float(b), base[i], gallery_passages) for i, b in enumerate(best)]
            top = int(best.argmax())
            row = {
                "passages": n_pass,
                "share_of_gallery_passages": round(n_pass / gallery_passages, 7),
                "best_score": round(float(best[top]), 4),
                "best_score_query": qs[top],
                "best_place": est[top],
                "median_estimated_rank_of_best_passage": int(
                    np.median([e["estimated_rank"] for e in est])
                ),
                "lowest_estimated_rank": min(e["estimated_rank"] for e in est),
                "queries_with_a_passage_at_or_above_the_100th_nearest": int(
                    (best >= cut[qs]).sum()
                ),
            }
            if k in in_gallery:
                mine = [sc for w, sc in places if owner.get(w) == k]
                share = len(mine) / max(len(places), 1)
                row |= {
                    "stored_nearest_places": len(mine),
                    "queries_with_a_stored_place": len(
                        {i for i in qs for w, _ in by_query.get(i, []) if owner.get(w) == k}
                    ),
                    "share_of_stored_places": round(share, 6),
                    "times_its_share_of_passages": round(share / (n_pass / gallery_passages), 2),
                }
                row["verdict"] = (
                    "no"
                    if not mine
                    else "yes"
                    if row["times_its_share_of_passages"] >= c["over_represented"]
                    else "present, not over-represented"
                )
            per[k] = row
        res[name] = {
            "paragraphs_1830": [min(wanted), max(wanted)],
            "queries": len(qs_all),
            "queries_scored": len(qs),
            "queries_left_out_as_king_james": len(qs_all) - len(qs),
            "stored_nearest_places": len(places),
            "stored_places_by_genre": dict(genres.most_common()),
            "works_with_most_stored_places": [
                {
                    "work_id": w,
                    "places": k,
                    "year": reg[w]["year"],
                    "author": titles[w]["author_norm"],
                    "title": " ".join((titles[w]["title"] or "").split())[:90],
                    "claimed": owner.get(w),
                }
                for w, k in works.most_common(c["top_works"])
            ],
            "distinct_works_in_stored_places": len(works),
            "sources": per,
        }
        if name == "abinadi" and "bunyan_trial_scene" in vectors and c["foxe_key"] in vectors:
            b = (q @ vectors["bunyan_trial_scene"].T).max(axis=1)
            fs = q @ vectors[c["foxe_key"]].T
            f = fs.max(axis=1)
            closer = (fs > b[:, None]).sum(axis=1)
            res[name]["bunyan_trial_against_foxe"] = {
                "queries": len(qs),
                "foxe_best_passage_closer": int((f > b).sum()),
                "bunyan_trial_closer": int((b > f).sum()),
                "trial_passages": int(vectors["bunyan_trial_scene"].shape[0]),
                "foxe_passages": int(fs.shape[1]),
                "foxe_passages_closer_than_the_best_trial_passage_median": int(np.median(closer)),
                "mean_best_score": {"bunyan_trial": round(float(b.mean()), 4),
                                    "foxe": round(float(f.mean()), 4)},
            }  # fmt: skip
    return res


# ---- the run ------------------------------------------------------------------------------


def source_rows(found: dict, t: dict, ranking: dict, gallery: set[str], cfg: dict) -> dict:
    c = cfg["lab"]["claimed_sources"]
    reg = {r["work_id"]: r for r in registry.load().to_pylist()}
    exact = {v["work_id"] for v in json.loads(EXACT.read_text())["volumes"]}
    skel: dict[str, float] = {}
    for p in SKELETON:
        for s in json.loads(p.read_text()).get("sources", []):
            if isinstance(s, dict) and "id" in s and "order_p" in s:
                skel[s["id"]] = s["order_p"]
    res = {}
    for key, ids in found.items():
        copies = []
        for w in ids:
            r = reg[w]
            copies.append({
                "work_id": w, "year": r["year"], "has_text": r["has_text"],
                "kept_copy": r["dup_keeper"], "rare": rare_row(w, t),
                "meaning": meaning_row(w, ranking, gallery),
            })  # fmt: skip
        rare = [x for x in copies if x["rare"]]
        best_r = min(rare, key=lambda x: x["rare"]["rank"]) if rare else None
        best_m = best_meaning(ids, ranking)
        row = {
            "copies_catalogued": len(ids),
            "copies_with_text": sum(x["has_text"] for x in copies),
            "copies_in_rare_population": len(rare),
            "copies_in_meaning_gallery": sum(w in gallery for w in ids),
            "copies_ranked_in_meaning_search": sum(w in ranking for w in ids),
            "rare_best": None if best_r is None else {"work_id": best_r["work_id"],
                                                      **best_r["rare"]},
            "rare_median_rank": int(np.median([x["rare"]["rank"] for x in rare])) if rare else None,
            "meaning_best": None if best_m is None else {"work_id": best_m,
                                                         **meaning_row(best_m, ranking, gallery)},
            "exact_reuse_listed": any(w in exact for w in ids),
            "story_order": (
                {"order_p": min(skel[w] for w in ids if w in skel)}
                if any(w in skel for w in ids)
                else "not scored"
            ),
            "copies": copies,
        }  # fmt: skip
        if best_r is None and best_m is None and not row["copies_in_meaning_gallery"]:
            row["verdict"] = "not in the searched library"
        else:
            near = (best_r is not None and best_r["rare"]["top_share"] <= c["near_top_share"]) or (
                best_m is not None and ranking[best_m]["stands_out"]
            )
            row["verdict"] = "near the top" if near else "in the crowd"
        res[key] = row
    return res


def by_decade(t: dict) -> dict:
    return dict(sorted(Counter(f"{y // 10 * 10}s" for y in t["year"].values()).items()))


def run(cfg: dict, only_check: bool = False) -> dict:
    from semantic.corpus import galleries

    c = cfg["lab"]["claimed_sources"]
    cols = ["work_id", "title", "author_norm"]
    cat = pq.read_table(CATALOG, columns=cols).to_pylist()
    res: dict = {"settings": c, "known_answer": {}}
    ka = res["known_answer"]
    ka["late_war_as_target"] = check_late_war(cfg)
    print("known answer 1:", {k: v for k, v in ka["late_war_as_target"].items()}, flush=True)
    if not ka["late_war_as_target"]["passed"]:
        res["stopped"] = "known answer 1 missed its bar; nothing was looked up"
        return res
    ranking = {r["work_id"]: r for r in json.loads(CORPUS.read_text())["ranking"]}
    t = rare_table(BOM_HITS, cfg, sealed_ids_of_scan())
    ka["published_numbers"] = check_published(t, ranking, cat, cfg)
    print("known answer 2:", ka["published_numbers"], flush=True)
    if not ka["published_numbers"]["passed"]:
        res["stopped"] = "known answer 2 missed its bar; nothing was looked up"
        return res
    gallery = galleries(cfg)[0]["bom:window"]
    found = find_copies({**c["sources"], **c["scale"]}, cat)
    vec = Vectors()
    sample, gallery_passages = vec.sample(gallery, c["sample_passages"], c["seed"])
    trial = trial_rows([w for w in found[c["bunyan_key"]] if w in gallery], vec, cfg)
    ka["reprint_pair"] = check_reprint(trial, vec, sample, cfg)
    print("known answer 3:", ka["reprint_pair"], flush=True)
    if only_check:
        return res
    res["populations"] = {
        "rare_phrases": t["population"],
        "rare_phrases_volumes_sharing_any": sum(v > 0 for v in t["shared"].values()),
        "rare_phrases_by_decade": by_decade(t),
        "passage_rank_resolution": round(gallery_passages / c["sample_passages"]),
        "meaning_gallery_volumes": len(gallery),
        "meaning_gallery_passages": gallery_passages,
        "meaning_ranked_volumes": len(ranking),
    }
    res["sources"] = source_rows(found, t, ranking, gallery, cfg)
    res["scale_keys"] = list(c["scale"])
    res["bunyan_trial_scene"] = {
        "copies_in_gallery": len(trial["all"]),
        "copies_with_trial": len(trial["found"]),
        "trial_passages": {w: v["passages"] for w, v in trial["found"].items()},
        "unreadable_not_attempted": trial["unreadable"],
        "text_differs_from_index_not_attempted": trial["mismatch"],
    }
    if ka["reprint_pair"]["passed"]:
        res["passage_level"] = passage_level(
            found, trial, vec, sample, gallery_passages, gallery, cfg
        )
    else:
        res["passage_level"] = "not run: known answer 3 missed its bar"
    res["not_done"] = [
        "story order for the claimed sources: needs a hosted AI model",
        "the published lists of Donofrio and Davis: not held",
        "the three controls as targets: the stored searches of other targets used matched samples",
    ]
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    res = run(cfg, only_check=a.cmd == "check")
    if a.cmd == "check":
        return 0
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    for key, row in res.get("sources", {}).items():
        print(key, row["verdict"], row["rare_best"], row["meaning_best"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
