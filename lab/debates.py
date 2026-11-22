"""BOM-103: print dates of the library passages nearest the Book of Mormon's doctrinal debates.

Passages on each of a fixed list of debate topics (Campbell's 1831 list and the issue's, found by
written term rules) are looked up in the study's meaning index among religious works printed
1640-1829 (the "gallery"). For each set of passages the print decades of the 100 nearest gallery
passages are counted against what each decade's share of gallery passages would give, and the
peak decade is read off. The known-answer check comes first: control works printed in the 1650s,
1740s, 1780s and 1820s, and keyed (TCP) works of 1780-1799, each searched with its own author left
out, must peak within a decade of their own print decade; if any group misses its bar, the Book of
Mormon is not scored. Works written long before but printed 1780-1829 are run as a descriptive
decoy. The test card, written first, is ``data/private/lab/owner/2026-11-21-debates/card.md``;
settings are ``lab.debates`` in the config. The output holds ids, decades, counts and ratios; no
text.

Usage::

    python -m lab.debates check     # known-answer controls only -> data/lab/debates/check.json
    python -m lab.debates run       # check, then the Book of Mormon -> data/lab/debates/result.json

Second design (post hoc, after the first check missed; ``lab.debates.v2``; card
``data/private/lab/owner/2026-11-21-debates-2/card.md``): OCR religious works of 1780-1829 only,
balanced so every decade gives the same number of passages, controls kept apart by text kind::

    python -m lab.debates check2    # -> data/lab/debates/check_v2.json
    python -m lab.debates run2      # check2, then the book -> data/lab/debates/result_v2.json
    python -m lab.debates phrases   # phrase counts by decade -> data/lab/debates/phrases_v2.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import statistics
import subprocess
import time

import numpy as np

from lab import door, registry
from lab.paths import REGISTRY, out
from metadata import config

OUT = REGISTRY / "debates"
DEATH = re.compile(r"\b1[0-9]{3}\??\s*-\s*(1[0-9]{3})\b|\bd\.\s*(1[0-9]{3})\b")


# ------------------------------------------------------------------------------------ topics
def compile_topics(d: dict) -> dict[str, list[re.Pattern]]:
    return {t: [re.compile(g) for g in groups] for t, groups in d["topics"].items()}


def topics_of(text: str, topics: dict[str, list[re.Pattern]], min_hits: int) -> list[str]:
    """The topics a passage is on: every term group matches, and the terms match ``min_hits``
    times in all."""
    low = " ".join(text.lower().split())
    found = []
    for name, groups in topics.items():
        counts = [len(g.findall(low)) for g in groups]
        if all(counts) and sum(counts) >= min_hits:
            found.append(name)
    return found


# ------------------------------------------------------------------------------------ profiles
def decades(d: dict) -> list[int]:
    return list(range(d["year_min"] // 10 * 10, d["year_max"] // 10 * 10 + 1, 10))


def profile(counts: np.ndarray, base: np.ndarray, decs: list[int], smooth: int) -> dict:
    """Neighbour counts by decade against the gallery's passage shares: windowed ratio and peak."""
    n = int(counts.sum())
    if n == 0:
        return {"neighbours": 0}
    expected = base * n
    ratio = []
    for i in range(len(decs)):
        lo, hi = max(0, i - smooth), min(len(decs), i + smooth + 1)
        ratio.append(float(counts[lo:hi].sum() / expected[lo:hi].sum()))
    peak = int(np.argmax(ratio))
    cum = np.cumsum(counts)
    return {
        "neighbours": n,
        "peak_decade": decs[peak],
        "peak_ratio": round(ratio[peak], 3),
        "ratio": {str(d): round(r, 3) for d, r in zip(decs, ratio, strict=True)},
        "share": {str(d): round(float(c) / n, 4) for d, c in zip(decs, counts, strict=True)},
        "median_decade": decs[int(np.searchsorted(cum, n / 2))],
        "share_1820s": round(float(counts[decs.index(1820)]) / n, 4) if 1820 in decs else None,
        "ratio_1820s_unsmoothed": round(
            float(counts[decs.index(1820)] / expected[decs.index(1820)]), 3
        )
        if 1820 in decs
        else None,
    }


def l1(a: dict, b: dict) -> float:
    return round(sum(abs(a["share"][k] - b["share"][k]) for k in a["share"]), 4)


def hit(peak: int, own: int, tolerance: int) -> bool:
    return abs(peak - own) <= 10 * tolerance


# ------------------------------------------------------------------------------------ gallery
def gallery_rows(cfg: dict, d: dict | None = None) -> list[dict]:
    """Registry rows (with catalog fields) of the religious works searched."""
    d = d or cfg["lab"]["debates"]
    bible = re.compile(d["bible_title"], re.IGNORECASE)
    t = registry.load().to_pylist()
    rows = [
        r
        for r in t
        if r["kind"] == "work"
        and r["has_text"]
        and r["dup_keeper"]
        and r["in_passage_index"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and d["year_min"] <= r["year"] <= d["year_max"]
        and d["gallery_genre"] in (r["genre"] or "").split(",")
        and r["source"] != d.get("gallery_exclude_source")
    ]
    cat = door.catalog({r["work_id"] for r in rows})
    keep = []
    for r in rows:
        c = cat.get(r["work_id"])
        if c is None or bible.search(" ".join((c["title"] or "").split())):
            continue
        keep.append({**c, **r})
    return keep


class Gallery:
    """The gallery's sign codes in memory, with each passage's work, decade and source."""

    def __init__(self, rows: list[dict], cfg: dict, d: dict | None = None) -> None:
        from lab.passages import Index

        d = d or cfg["lab"]["debates"]
        self.cfg, self.d, self.decs = cfg, d, decades(d)
        self.ix = Index()
        by_id = {r["work_id"]: r for r in rows}
        widx = {w: i for i, w in enumerate(self.ix.works)}
        ok = np.zeros(len(self.ix.works), dtype=bool)
        dec = np.full(len(self.ix.works), -1, dtype=np.int16)
        keyed = np.zeros(len(self.ix.works), dtype=bool)
        for w, r in by_id.items():
            i = widx.get(w)
            if i is None:
                continue
            ok[i] = True
            dec[i] = self.decs.index(r["year"] // 10 * 10)
            keyed[i] = r["source"] == d["keyed_source"]
        self.widx = widx
        t0 = time.time()
        work_of_row = np.asarray(self.ix.rows)
        self.pos = np.flatnonzero(ok[work_of_row])
        self.work = work_of_row[self.pos]
        del work_of_row
        self.dec = dec[self.work]
        self.keyed = keyed[self.work]
        self.codes = np.ascontiguousarray(self.ix.codes[self.pos]).view(np.uint64)
        counts = np.bincount(self.dec, minlength=len(self.decs)).astype(float)
        self.base = counts / counts.sum()
        self.passages_by_decade = {str(x): int(c) for x, c in zip(self.decs, counts, strict=True)}
        self._vec: dict[int, np.ndarray] = {}
        print(f"gallery: {len(by_id):,} works, {len(self.pos):,} passages "
              f"({time.time() - t0:.0f} s)", flush=True)  # fmt: skip

    def excluded(self, work_ids: set[str]) -> np.ndarray | None:
        idx = [self.widx[w] for w in work_ids if w in self.widx]
        return np.isin(self.work, idx) if idx else None

    def _shard(self, s: int) -> np.ndarray:
        from semantic.index import INDEX

        if s not in self._vec:
            self._vec[s] = np.load(INDEX / f"{self.ix.shards[s]['name']}.npy", mmap_mode="r")
        return self._vec[s]

    def exact(self, q: np.ndarray, rows: np.ndarray) -> np.ndarray:
        """The study's own score (inner product of unit vectors) for gallery positions ``rows``."""
        glob = self.pos[rows]
        scores = np.empty(len(rows), dtype=np.float32)
        which = np.searchsorted(self.ix.starts, glob, side="right") - 1
        for s in np.unique(which):
            sel = which == s
            local = np.sort(glob[sel] - self.ix.starts[s])
            order = np.argsort(np.argsort(glob[sel] - self.ix.starts[s]))
            vec = np.asarray(self._shard(int(s))[local], dtype=np.float32)
            scores[sel] = (vec @ q)[order]
        return scores

    def balanced_draws(self, n: int, seed: int) -> None:
        """``n`` balanced galleries: each decade gives the smallest decade's passage count."""
        size = int(np.bincount(self.dec, minlength=len(self.decs)).min())
        self.draws = []
        for k in range(n):
            rng = np.random.default_rng([seed, k])
            parts = [rng.choice(np.flatnonzero(self.dec == i), size, replace=False)
                     for i in range(len(self.decs))]  # fmt: skip
            idx = np.sort(np.concatenate(parts))
            self.draws.append((idx, np.ascontiguousarray(self.codes[idx])))
        self.draw_size = size

    def search(self, q: np.ndarray, skip: np.ndarray | None, draw: tuple | None = None) -> dict:
        """Decade counts of the ``neighbours`` nearest gallery passages, top score, keyed share.
        With ``draw`` (positions, codes), only that balanced gallery is searched."""
        d = self.d
        codes = self.codes if draw is None else draw[1]
        code = np.packbits(q > 0).view(np.uint64)
        dist = np.bitwise_count(codes ^ code).sum(axis=1, dtype=np.uint16)
        if skip is not None:
            dist[skip if draw is None else skip[draw[0]]] = np.iinfo(np.uint16).max
        cand = np.argpartition(dist, d["candidates"])[: d["candidates"]]
        cand = cand[dist[cand] < np.iinfo(np.uint16).max]
        if draw is not None:
            cand = draw[0][cand]
        scores = self.exact(q, cand)
        top = cand[np.argsort(-scores)[: d["neighbours"]]]
        return {
            "decades": np.bincount(self.dec[top], minlength=len(self.decs)),
            "top1": float(scores.max()) if len(scores) else 0.0,
            "keyed": int(self.keyed[top].sum()),
            "n": len(top),
        }


def embedder(cfg: dict):
    from semantic.index import _model

    model = _model(cfg)

    def embed(texts: list[str]) -> np.ndarray:
        v = model.encode([" ".join(t.split()) for t in texts],
                         batch_size=cfg["semantic"]["batch_size"], normalize_embeddings=True,
                         convert_to_numpy=True, show_progress_bar=False)  # fmt: skip
        return v.astype(np.float32)

    return embed


# ------------------------------------------------------------------------------------ controls
def death_year(author: str | None) -> int | None:
    m = DEATH.search(author or "")
    return int(m.group(1) or m.group(2)) if m else None


def control_pools(rows: list[dict], cfg: dict) -> dict[str, list[dict]]:
    """Candidate works per control group, shuffled with the seed (drawn from in order)."""
    d = cfg["lab"]["debates"]
    base = [r for r in rows if r["author_kind"] == "person" and (r["words"] or 0) >= d[
        "control_min_words"]]  # fmt: skip
    pools: dict[str, list[dict]] = {}
    for dec in d["control_decades"]:
        pools[f"{dec}s"] = [dict(r, own=dec) for r in base if dec <= r["year"] <= dec + 9]
    lo, hi = d["keyed_years"]
    pools[f"keyed_{lo}_{hi}"] = [
        dict(r, own=r["year"] // 10 * 10)
        for r in base
        if lo <= r["year"] <= hi and r["source"] == d["keyed_source"]
    ]
    lo, hi = d["old_reprint_years"]
    pools["old_reprints"] = [
        dict(r, own=r["year"] // 10 * 10, died=death_year(r["author"]))
        for r in base
        if lo <= r["year"] <= hi and (death_year(r["author"]) or 9999) < d["old_died_before"]
    ]
    for name, pool in pools.items():
        random.Random(f"{d['seed']}:{name}").shuffle(pool)
    return pools


def control_queries(
    row: dict, cfg: dict, topics: dict, d: dict | None = None
) -> list[tuple[str, list[str]]] | None:
    """(passage text, topics) for a control work's topic passages; None if unreadable."""
    from semantic.index import spans

    d, s = d or cfg["lab"]["debates"], cfg["semantic"]
    try:
        text = door.text_of(row)
    except OSError:
        return None
    found = []
    for a, b, _ in spans(text, s["passage_words"], s["min_passage_words"]):
        p = text[a:b]
        on = topics_of(p, topics, d["min_hits"])
        if on:
            found.append((p, on))
    if len(found) > d["control_max_queries"]:
        found = random.Random(f"{d['seed']}:{row['work_id']}").sample(
            found, d["control_max_queries"]
        )
    return found


def run_controls(g: Gallery, rows: list[dict], embed, cfg: dict) -> dict:
    d = cfg["lab"]["debates"]
    topics = compile_topics(d)
    by_author: dict[str, set[str]] = {}
    for r in rows:
        if r["author_norm"]:
            by_author.setdefault(r["author_norm"], set()).add(r["work_id"])
    groups: dict[str, dict] = {}
    top1_all: list[float] = []
    for name, pool in control_pools(rows, cfg).items():
        works, unreadable, too_few, t0 = [], 0, 0, time.time()
        topic_counts: dict[str, np.ndarray] = {}
        topic_n: dict[str, int] = {}
        all_counts = np.zeros(len(g.decs), dtype=np.int64)
        for row in pool:
            if len(works) == d["control_works"]:
                break
            qs = control_queries(row, cfg, topics)
            if qs is None:
                unreadable += 1  # not attempted, never a result
                continue
            if len(qs) < d["control_min_passages"]:
                too_few += 1
                continue
            leave = {row["work_id"]} | by_author.get(row["author_norm"] or "", set())
            skip = g.excluded(leave)
            vecs = embed([p for p, _ in qs])
            counts = np.zeros(len(g.decs), dtype=np.int64)
            keyed = top1 = 0.0
            for (_, on), v in zip(qs, vecs, strict=True):
                r = g.search(v, skip)
                counts += r["decades"]
                keyed += r["keyed"]
                top1_all.append(r["top1"])
                top1 += r["top1"]
                for t in on:
                    topic_counts.setdefault(t, np.zeros(len(g.decs), dtype=np.int64))
                    topic_counts[t] += r["decades"]
                    topic_n[t] = topic_n.get(t, 0) + 1
            all_counts += counts
            prof = profile(counts, g.base, g.decs, d["smooth"])
            works.append({
                "work_id": row["work_id"],
                "year": row["year"],
                "source": row["source"],
                "died": row.get("died"),
                "queries": len(qs),
                "left_out_works": len(leave),
                "peak_decade": prof["peak_decade"],
                "median_decade": prof["median_decade"],
                "share_1820s": prof["share_1820s"],
                "keyed_share": round(keyed / max(prof["neighbours"], 1), 4),
                "mean_top1": round(top1 / len(qs), 4),
                "hit": hit(prof["peak_decade"], row["own"], d["tolerance"]),
            })  # fmt: skip
        hits = sum(w["hit"] for w in works)
        groups[name] = {
            "works": works,
            "drawn": len(works),
            "unreadable_not_attempted": unreadable,
            "too_few_topic_passages": too_few,
            "hits": hits,
            "hit_rate": round(hits / max(len(works), 1), 3),
            "pooled": profile(all_counts, g.base, g.decs, d["smooth"]),
            "by_topic": {
                t: profile(c, g.base, g.decs, d["smooth"]) | {"passages": topic_n[t]}
                for t, c in sorted(topic_counts.items())
            },
        }
        print(f"{name}: {hits}/{len(works)} hit ({time.time() - t0:.0f} s)", flush=True)
    bar_groups = [n for n in groups if n != "old_reprints"]
    passed = all(
        groups[n]["drawn"] >= d["control_works"] // 2 and groups[n]["hit_rate"] >= d["group_bar"]
        for n in bar_groups
    )
    close = float(np.percentile(top1_all, d["close_percentile"])) if top1_all else None
    return {"groups": groups, "bar_groups": bar_groups, "passed": passed,
            "close_top1_bar": round(close, 4) if close else None}  # fmt: skip


# ------------------------------------------------------------------------------------ the book
def run_bom(g: Gallery, embed, cfg: dict, controls: dict) -> dict:
    from semantic.search import bom_queries

    d, s = cfg["lab"]["debates"], cfg["semantic"]
    topics = compile_topics(d)
    qs = [q for q in bom_queries(s["passage_words"]) if q["words"] >= s["min_passage_words"]]
    scored = [q for q in qs if q["kjv_share"] <= s["max_query_kjv_share"]]
    vecs = embed([q["text"] for q in scored])
    per = []
    for q, v in zip(scored, vecs, strict=True):
        r = g.search(v, None)
        r["topics"] = topics_of(q["text"], topics, d["min_hits"])
        per.append(r)
    sets = {"all_passages": per} | {t: [r for r in per if t in r["topics"]] for t in d["topics"]}
    cands = {n: grp for n, grp in controls["groups"].items()}
    res = {}
    for name, rs in sets.items():
        entry = {"passages": len(rs)}
        if len(rs) < d["bom_min_passages"]:
            entry["scored"] = False
            res[name] = entry
            continue
        counts = sum(r["decades"] for r in rs)
        prof = profile(counts, g.base, g.decs, d["smooth"])
        top1 = [r["top1"] for r in rs]
        nearest = {}
        for n, grp in cands.items():
            ref = grp["by_topic"].get(name)
            if ref is None or ref.get("passages", 0) < d["bom_min_passages"]:
                ref = grp["pooled"]
            if ref.get("neighbours"):
                nearest[n] = l1(prof, ref)
        entry.update({
            "scored": True,
            **prof,
            "peaks_1810s_1820s": prof["peak_decade"] in (1810, 1820),
            "keyed_share": round(sum(r["keyed"] for r in rs) / prof["neighbours"], 4),
            "median_top1": round(statistics.median(top1), 4),
            "no_close_neighbours": controls["close_top1_bar"] is not None
            and statistics.median(top1) < controls["close_top1_bar"],
            "distance_to_controls": nearest,
            "nearest_control": min(nearest, key=nearest.get) if nearest else None,
        })  # fmt: skip
        res[name] = entry
    topical = [n for n in d["topics"] if res[n].get("scored")]
    late = [n for n in topical if res[n]["peaks_1810s_1820s"]]
    share = len(late) / max(len(topical), 1)
    allp = res["all_passages"].get("peaks_1810s_1820s", False)
    verdict = ("yes" if share >= d["yes_share"] and allp
               else "no" if share <= 1 - d["yes_share"] else "cannot tell")  # fmt: skip
    return {
        "passages": len(qs),
        "scored_passages": len(scored),
        "dropped_king_james": len(qs) - len(scored),
        "sets": res,
        "verdict": {
            "answer": verdict,
            "topics_scored": len(topical),
            "topics_peaking_1810s_1820s": late,
            "share": round(share, 3),
            "all_passages_peak": res["all_passages"].get("peak_decade"),
            "topics_not_scored": [n for n in d["topics"] if not res[n].get("scored")],
            "topics_no_close_neighbours": [n for n in topical if res[n]["no_close_neighbours"]],
        },
    }


# ------------------------------------------------------------------------------------ second design
def v2_settings(cfg: dict) -> dict:
    """The first design's settings with the second design's (``lab.debates.v2``) over them."""
    d = {k: v for k, v in cfg["lab"]["debates"].items() if k != "v2"}
    return d | cfg["lab"]["debates"]["v2"]


def flat_profile(counts: np.ndarray, decs: list[int]) -> dict:
    """Decade shares of neighbours in balanced galleries (chance: equal shares) and the peak."""
    n = float(counts.sum())
    if n == 0:
        return {"neighbours": 0}
    share = counts / n
    return {
        "neighbours": round(n, 1),
        "peak_decade": decs[int(np.argmax(share))],
        "share": {str(x): round(float(c), 4) for x, c in zip(decs, share, strict=True)},
    }


def chance_adjacent(own: int, decs: list[int]) -> float:
    """Share of decades that are ``own`` or next to it: a random peak's chance of a hit."""
    return sum(abs(x - own) <= 10 for x in decs) / len(decs)


def control_pools_v2(rows: list[dict], d: dict) -> dict[str, list[dict]]:
    """OCR groups by decade, the keyed group and the decoy, each shuffled with the seed."""
    base = [r for r in rows if r["author_kind"] == "person"
            and (r["words"] or 0) >= d["control_min_words"]]  # fmt: skip
    keyed = d["gallery_exclude_source"]
    pools: dict[str, list[dict]] = {}
    for dec in d["control_decades"]:
        pools[f"ocr_{dec}s"] = [
            dict(r, own=dec) for r in base if dec <= r["year"] <= dec + 9 and r["source"] != keyed
        ]
    lo, hi = d["keyed_years"]
    pools[f"keyed_{lo}_{hi}"] = [dict(r, own=r["year"] // 10 * 10) for r in base
                                 if lo <= r["year"] <= hi and r["source"] == keyed]  # fmt: skip
    lo, hi = d["old_reprint_years"]
    pools["old_reprints"] = [
        dict(r, own=r["year"] // 10 * 10, died=death_year(r["author"]))
        for r in base
        if lo <= r["year"] <= hi and (death_year(r["author"]) or 9999) < d["old_died_before"]
    ]
    for name, pool in pools.items():
        random.Random(f"{d['seed']}:{name}").shuffle(pool)
    return pools


def search_balanced(g: Gallery, v: np.ndarray, skip: np.ndarray | None) -> dict:
    """Decade counts averaged over the balanced draws; top-1 score over all draws."""
    rs = [g.search(v, skip, draw) for draw in g.draws]
    return {"decades": sum(r["decades"] for r in rs) / len(rs),
            "top1": max(r["top1"] for r in rs)}  # fmt: skip


def run_controls_v2(g: Gallery, everyone: list[dict], embed, cfg: dict, d: dict) -> dict:
    topics = compile_topics(d)
    by_author: dict[str, set[str]] = {}
    for r in everyone:
        if r["author_norm"]:
            by_author.setdefault(r["author_norm"], set()).add(r["work_id"])
    groups: dict[str, dict] = {}
    top1_all: list[float] = []
    for name, pool in control_pools_v2(everyone, d).items():
        works, unreadable, too_few, t0 = [], 0, 0, time.time()
        topic_counts: dict[str, np.ndarray] = {}
        topic_n: dict[str, int] = {}
        all_counts = np.zeros(len(g.decs))
        for row in pool:
            if len(works) == d["control_works"]:
                break
            qs = control_queries(row, cfg, topics, d)
            if qs is None:
                unreadable += 1  # not attempted, never a result
                continue
            if len(qs) < d["control_min_passages"]:
                too_few += 1
                continue
            leave = {row["work_id"]} | by_author.get(row["author_norm"] or "", set())
            skip = g.excluded(leave)
            counts = np.zeros(len(g.decs))
            top1 = 0.0
            for (_, on), v in zip(qs, embed([p for p, _ in qs]), strict=True):
                r = search_balanced(g, v, skip)
                counts += r["decades"]
                top1 += r["top1"]
                top1_all.append(r["top1"])
                for t in on:
                    topic_counts.setdefault(t, np.zeros(len(g.decs)))
                    topic_counts[t] += r["decades"]
                    topic_n[t] = topic_n.get(t, 0) + 1
            all_counts += counts
            prof = flat_profile(counts, g.decs)
            works.append({
                "work_id": row["work_id"], "year": row["year"], "source": row["source"],
                "died": row.get("died"), "queries": len(qs), "left_out_works": len(leave),
                "peak_decade": prof["peak_decade"], "share": prof["share"],
                "mean_top1": round(top1 / len(qs), 4),
                "exact": prof["peak_decade"] == row["own"],
                "adjacent": hit(prof["peak_decade"], row["own"], d["tolerance"]),
                "chance_adjacent": chance_adjacent(row["own"], g.decs),
            })  # fmt: skip
        n = max(len(works), 1)
        adj, exact = sum(w["adjacent"] for w in works), sum(w["exact"] for w in works)
        groups[name] = {
            "works": works,
            "drawn": len(works),
            "unreadable_not_attempted": unreadable,
            "too_few_topic_passages": too_few,
            "adjacent_hits": adj,
            "adjacent_rate": round(adj / n, 3),
            "exact_hits": exact,
            "exact_rate": round(exact / n, 3),
            "chance_adjacent": round(sum(w["chance_adjacent"] for w in works) / n, 3),
            "chance_exact": round(1 / len(g.decs), 3),
            "pooled": flat_profile(all_counts, g.decs),
            "by_topic": {
                t: flat_profile(c, g.decs) | {"passages": topic_n[t]}
                for t, c in sorted(topic_counts.items())
            },  # fmt: skip
        }
        print(f"{name}: adjacent {adj}/{len(works)}, exact {exact}/{len(works)} "
              f"({time.time() - t0:.0f} s)", flush=True)  # fmt: skip
    bar_groups = [n for n in groups if n != "old_reprints"]
    passed = all(
        groups[n]["drawn"] >= d["control_works"] // 2
        and groups[n]["adjacent_rate"] >= d["adjacent_bar"]
        and groups[n]["exact_rate"] >= d["exact_bar"]
        for n in bar_groups
    )
    close = float(np.percentile(top1_all, d["close_percentile"])) if top1_all else None
    return {"groups": groups, "bar_groups": bar_groups, "passed": passed,
            "close_top1_bar": round(close, 4) if close else None}  # fmt: skip


def run_bom_v2(g: Gallery, embed, cfg: dict, d: dict, controls: dict) -> dict:
    from semantic.search import bom_queries

    s = cfg["semantic"]
    topics = compile_topics(d)
    qs = [q for q in bom_queries(s["passage_words"]) if q["words"] >= s["min_passage_words"]]
    scored = [q for q in qs if q["kjv_share"] <= s["max_query_kjv_share"]]
    per = []
    for q, v in zip(scored, embed([q["text"] for q in scored]), strict=True):
        r = search_balanced(g, v, None)
        r["topics"] = topics_of(q["text"], topics, d["min_hits"])
        per.append(r)
    sets = {"all_passages": per} | {t: [r for r in per if t in r["topics"]] for t in d["topics"]}
    res = {}
    for name, rs in sets.items():
        entry: dict = {"passages": len(rs)}
        if len(rs) < d["bom_min_passages"]:
            res[name] = entry | {"scored": False}
            continue
        prof = flat_profile(sum(r["decades"] for r in rs), g.decs)
        med = statistics.median(r["top1"] for r in rs)
        nearest = {}
        for n, grp in controls["groups"].items():
            ref = grp["by_topic"].get(name)
            if ref is None or ref.get("passages", 0) < d["bom_min_passages"]:
                ref = grp["pooled"]
            if ref.get("neighbours"):
                nearest[n] = l1(prof, ref)
        entry.update({
            "scored": True, **prof,
            "late": prof["peak_decade"] in d["late_decades"],
            "median_top1": round(med, 4),
            "no_close_neighbours": controls["close_top1_bar"] is not None
            and med < controls["close_top1_bar"],
            "distance_to_controls": nearest,
            "nearest_control": min(nearest, key=nearest.get) if nearest else None,
        })  # fmt: skip
        res[name] = entry
    topical = [n for n in d["topics"] if res[n].get("scored")]
    late = [n for n in topical if res[n]["late"]]
    share = len(late) / max(len(topical), 1)
    allp = res["all_passages"].get("late", False)
    verdict = ("yes" if share >= d["yes_share"] and allp
               else "no" if share <= 1 - d["yes_share"] else "cannot tell")  # fmt: skip
    return {
        "passages": len(qs),
        "scored_passages": len(scored),
        "dropped_king_james": len(qs) - len(scored),
        "sets": res,
        "verdict": {
            "answer": verdict,
            "topics_scored": len(topical),
            "topics_late": late,
            "share_late": round(share, 3),
            "chance_late": round(len(d["late_decades"]) / len(g.decs), 3),
            "all_passages_peak": res["all_passages"].get("peak_decade"),
            "topics_not_scored": [n for n in d["topics"] if not res[n].get("scored")],
            "topics_no_close_neighbours": [n for n in topical if res[n]["no_close_neighbours"]],
        },
    }


def _count_phrases(job: tuple[dict, list[str]]) -> tuple[str, list[int] | None]:
    row, patterns = job
    try:
        low = " ".join(door.text_of(row).lower().split())
    except OSError:
        return row["work_id"], None  # unreadable: not attempted
    return row["work_id"], [len(re.findall(p, low)) for p in patterns]


def phrase_patterns(phrases: list[str]) -> list[str]:
    return [r"\b" + r"\s+".join(p.split()) + r"\b" for p in phrases]


def run_phrases(cfg: dict, d: dict) -> dict:
    """Each phrase per decade in the religious works of 1640-1829, and in the 1830 text."""
    from concurrent.futures import ProcessPoolExecutor

    from semantic.search import bom_queries

    span = {"year_min": d["phrase_year_min"], "year_max": d["phrase_year_max"],
            "gallery_exclude_source": None}  # fmt: skip
    rows = gallery_rows(cfg, d | span)
    pats = phrase_patterns(d["phrases"])
    decs = decades(span)
    occ = {p: [0] * len(decs) for p in d["phrases"]}
    works_with = {p: [0] * len(decs) for p in d["phrases"]}
    words, works, unreadable = [0] * len(decs), [0] * len(decs), 0
    by = {r["work_id"]: r for r in rows}
    with ProcessPoolExecutor(d["phrase_workers"]) as pool:
        jobs = [(r, pats) for r in rows]
        for wid, counts in pool.map(_count_phrases, jobs, chunksize=32):
            if counts is None:
                unreadable += 1
                continue
            i = decs.index(by[wid]["year"] // 10 * 10)
            words[i] += by[wid]["words"] or 0
            works[i] += 1
            for p, c in zip(d["phrases"], counts, strict=True):
                occ[p][i] += c
                works_with[p][i] += c > 0
    bom = " ".join(q["text"] for q in bom_queries(cfg["semantic"]["passage_words"])).lower()
    bom = " ".join(bom.split())
    curves = {}
    for p, pat in zip(d["phrases"], pats, strict=True):
        curves[p] = {
            "book_of_mormon_count": len(re.findall(pat, bom)),
            "per_million_words": {str(x): round(o / w * 1e6, 3) if w else None
                                  for x, o, w in zip(decs, occ[p], words, strict=True)},
            "share_of_works": {str(x): round(k / n, 4) if n else None
                               for x, k, n in zip(decs, works_with[p], works, strict=True)},
            "occurrences": dict(zip(map(str, decs), occ[p], strict=True)),
        }  # fmt: skip
    return {"works": sum(works), "unreadable_not_attempted": unreadable,
            "works_by_decade": dict(zip(map(str, decs), works, strict=True)),
            "words_by_decade": dict(zip(map(str, decs), words, strict=True)),
            "book_of_mormon_words": len(bom.split()), "phrases": curves}  # fmt: skip


def main_v2(cmd: str, cfg: dict) -> int:
    d = v2_settings(cfg)
    if cmd == "phrases":
        res = stamp(run_phrases(cfg, d), cfg) | {"settings_sha256_v2": settings_hash_v2(cfg)}
        out(OUT / "phrases_v2.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({p: [c["book_of_mormon_count"], c["per_million_words"]]
                          for p, c in res["phrases"].items()}, indent=1))  # fmt: skip
        return 0
    rows = gallery_rows(cfg, d)
    everyone = gallery_rows(cfg, d | {"gallery_exclude_source": None})
    g = Gallery(rows, cfg, d)
    g.balanced_draws(d["draws"], d["seed"])
    embed = embedder(cfg)
    gallery = {"works": len(rows), "passages": len(g.pos),
               "passages_by_decade": g.passages_by_decade,
               "balanced_passages_per_decade": g.draw_size, "draws": d["draws"]}  # fmt: skip
    path = OUT / "check_v2.json"
    chk = None
    if cmd == "run2" and path.exists():
        old = json.loads(path.read_text())
        if old.get("settings_sha256_v2") == settings_hash_v2(cfg):
            chk = old["known_answer"]
            print("known-answer check reused from check_v2.json (same settings)", flush=True)
    if chk is None:
        chk = run_controls_v2(g, everyone, embed, cfg, d)
        res = stamp({"gallery": gallery, "known_answer": chk}, cfg)
        res["settings_sha256_v2"] = settings_hash_v2(cfg)
        out(path).write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({n: [x["adjacent_hits"], x["exact_hits"], x["drawn"]]
                      for n, x in chk["groups"].items()}))  # fmt: skip
    print("passed" if chk["passed"] else "MISSED: the Book of Mormon is not scored")
    if cmd == "check2":
        return 0
    res = {"gallery": gallery, "settings": d, "known_answer": chk}
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
    else:
        res["book_of_mormon"] = run_bom_v2(g, embed, cfg, d, chk)
        print(json.dumps(res["book_of_mormon"]["verdict"], indent=1))
    res = stamp(res, cfg) | {"settings_sha256_v2": settings_hash_v2(cfg)}
    out(OUT / "result_v2.json").write_text(json.dumps(res, indent=1) + "\n")
    return 0


# ------------------------------------------------------------------------------------ driver
def settings_hash(cfg: dict) -> str:
    """The first design's settings (without the ``v2`` key, so its check stays reusable)."""
    first = {k: v for k, v in cfg["lab"]["debates"].items() if k != "v2"}
    keys = {"debates": first, "semantic": cfg["semantic"]}
    return hashlib.sha256(json.dumps(keys, sort_keys=True).encode()).hexdigest()


def settings_hash_v2(cfg: dict) -> str:
    keys = {"debates": v2_settings(cfg), "semantic": cfg["semantic"]}
    return hashlib.sha256(json.dumps(keys, sort_keys=True).encode()).hexdigest()


def stamp(res: dict, cfg: dict) -> dict:
    res["settings_sha256"] = settings_hash(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run", "check2", "run2", "phrases"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd in ("check2", "run2", "phrases"):
        return main_v2(a.cmd, cfg)
    rows = gallery_rows(cfg)
    g = Gallery(rows, cfg)
    embed = embedder(cfg)
    gallery = {"works": len(rows), "passages": len(g.pos),
               "passages_by_decade": g.passages_by_decade}  # fmt: skip
    path = OUT / "check.json"
    chk = None
    if a.cmd == "run" and path.exists():
        old = json.loads(path.read_text())
        if old.get("settings_sha256") == settings_hash(cfg):
            chk = old["known_answer"]
            print("known-answer check reused from check.json (same settings)", flush=True)
    if chk is None:
        chk = run_controls(g, rows, embed, cfg)
        out(path).write_text(json.dumps(stamp(
            {"gallery": gallery, "known_answer": chk}, cfg), indent=1) + "\n")  # fmt: skip
    print(json.dumps({n: [x["hits"], x["drawn"]] for n, x in chk["groups"].items()}))
    print("passed" if chk["passed"] else "MISSED: the Book of Mormon is not scored")
    if a.cmd == "check":
        return 0
    first = {k: v for k, v in cfg["lab"]["debates"].items() if k != "v2"}
    res = {"gallery": gallery, "settings": first, "known_answer": chk}
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
    else:
        res["book_of_mormon"] = run_bom(g, embed, cfg, chk)
        print(json.dumps(res["book_of_mormon"]["verdict"], indent=1))
    out(OUT / "result.json").write_text(json.dumps(stamp(res, cfg), indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
