"""BOM-107: chiasmus with a real baseline: the Book of Mormon rate against the period library.

A fixed automatic rule counts nested inverted repetitions of key words (A B C ... C' B' A'), with
the levels counted, in the Book of Mormon (1830 text) and, by the identical rule, in the King James
Bible, a sample of library works of 1650-1830, marked translations, the Bible-style books and
Joseph Smith's other dictations. Text becomes content tokens (stemmed, stoplist); for every centre
and a window of W tokens each side an *element* is a stem that occurs on both sides and at most
``max_count`` times in the window (Edwards and Edwards 2004: each element twice; the setting is 2);
the depth is the longest run of elements that mirrors outward from the centre. Chiasms of at least
``min_depth`` levels are counted once each, per 10,000 words, by depth. A shuffle of each text
(sentence units shuffled inside blocks) gives the chance rate for that text's own repetitiveness;
observed over shuffled is reported. The shuffle turned out not to be a clean null (it also
destroys the topical locality of ordinary prose, see the card), so the figure compared is observed
over *parallel order*: the same elements at the same distances counted in the other order
(A B C ... A B C), which keeps repetitiveness and locality exactly. The known-answer check
(famous King James chiasms, planted chiasms, plain prose against parallel order) comes first;
the book is scored only if it passes. Famous Book of Mormon cases are reported only as what the
fixed rule finds. The test card, written first, is
``data/private/lab/owner/2026-11-21-chiasmus/card.md``; settings are
``lab.chiasmus`` in the config. The result holds ids and numbers, no text.

Usage::

    python -m lab.chiasmus check    # known-answer check only (prints it)
    python -m lab.chiasmus run      # -> data/lab/reruns/chiasmus/result.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import subprocess
from bisect import bisect_left
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow.compute as pc

from lab import door, registry
from lab.paths import REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "chiasmus"
KJV = Path("data/kjv/kjv.jsonl")
TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?|[.;:?!]")
STOPS = frozenset(".;:?!")


# ------------------------------------------------------------------------------ tokens


def stem(w: str, cfg: dict) -> str:
    t = cfg["lab"]["chiasmus"]
    if len(w) >= t["stem_min"]:
        for suf in t["suffixes"]:
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                w = w[: -len(suf)]
                break
    if w.endswith("e") and len(w) > 3:
        w = w[:-1]
    if len(w) > 3 and w[-1] == w[-2] and w[-1] not in "aeiou":
        w = w[:-1]
    return w


def units_of(text: str, cfg: dict, ends: tuple[str, ...] = ()) -> tuple[list[list[str]], int]:
    """(sentence units of content stems, number of words). ``ends`` is unused text boundaries."""
    t = cfg["lab"]["chiasmus"]
    stop = frozenset(t["stopwords"])
    units: list[list[str]] = [[]]
    words = 0
    for m in TOKEN.findall(text):
        if m in STOPS:
            if units[-1]:
                units.append([])
            continue
        w = m.lower().replace("’", "'")
        if w.endswith("'s"):
            w = w[:-2]
        w = w.replace("'", "")
        words += 1
        if len(w) >= t["min_len"] and w not in stop:
            units[-1].append(stem(w, cfg))
    return [u for u in units if u], words


def join_units(parts: list[list[list[str]]]) -> list[list[str]]:
    return [u for p in parts for u in p]


def flat(units: list[list[str]]) -> list[str]:
    return [t for u in units for t in u]


def shuffled(units: list[list[str]], block: int, rng: random.Random) -> list[list[str]]:
    """Sentence units shuffled inside consecutive blocks of about ``block`` content tokens."""
    res: list[list[str]] = []
    cur: list[list[str]] = []
    n = 0
    for u in units:
        cur.append(u)
        n += len(u)
        if n >= block:
            rng.shuffle(cur)
            res += cur
            cur, n = [], 0
    rng.shuffle(cur)
    return res + cur


# ------------------------------------------------------------------------------ the detector


def candidates(
    s: list[str],
    w: int,
    stride: int,
    dmin: int,
    max_count: int | None = None,
    parallel: bool = False,
) -> list[tuple[int, int, int, int]]:
    """(depth, centre, first element index, last element index) for centres with depth >= dmin.

    An element is a stem on both sides of the centre that occurs at most ``max_count`` times in
    the window (two: exactly once each side); its nearest occurrence on each side is the pair.
    With ``parallel`` the run must keep the same order on both sides (A B C ... A B C): the same
    elements and distances, the other order, which is the control for repetitiveness."""
    if max_count is None:
        max_count = config.load()["lab"]["chiasmus"]["max_count"]
    n = len(s)
    if n < 2 * dmin:
        return []
    last: dict[str, int] = {}
    diff = np.zeros(n + 2, dtype=np.int32)
    for j, tok in enumerate(s):
        i = last.get(tok)
        if i is not None and j - i < 2 * w:
            lo, hi = max(i + 1, j - w + 1), min(j, i + w)
            if lo <= hi:
                diff[lo] += 1
                diff[hi + 1] -= 1
        last[tok] = j
    active = np.cumsum(diff)
    found = []
    for c in np.nonzero(active[: n + 1] >= dmin)[0]:
        c = int(c)
        if c % stride:
            continue
        a, b = max(0, c - w), min(n, c + w)
        cnt = Counter(s[a:b])
        left: dict[str, int] = {}
        order = []
        for k in range(c - 1, a - 1, -1):
            tok = s[k]
            if 2 <= cnt[tok] <= max_count and tok not in left:
                left[tok] = len(order)
                order.append(k)
        if len(order) < dmin:
            continue
        seq, right, seen = [], [], set()
        for k in range(c, b):
            tok = s[k]
            if tok in left and tok not in seen:
                seen.add(tok)
                seq.append(left[tok])
                right.append(k)
        if len(seq) < dmin:
            continue
        tails: list[int] = []  # smallest tail value of an increasing run of each length
        tail_at: list[int] = []  # the position in ``seq`` that holds that tail
        back = [-1] * len(seq)
        for q, v0 in enumerate(seq):
            v = -v0 if parallel else v0
            p = bisect_left(tails, v)
            if p == len(tails):
                tails.append(v)
                tail_at.append(q)
            else:
                tails[p] = v
                tail_at[p] = q
            back[q] = tail_at[p - 1] if p else -1
        depth = len(tails)
        if depth >= dmin:
            q, used = tail_at[-1], []
            while q >= 0:
                used.append(q)
                q = back[q]
            lo = min(order[seq[q]] for q in used)
            found.append((depth, c, lo, right[used[0]]))
    return found


def resolve(cands: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    """Each structure once: deepest first, then shortest span, skipping any that overlaps."""
    taken: list[tuple[int, int, int, int]] = []
    spans: list[tuple[int, int]] = []
    for c in sorted(cands, key=lambda x: (-x[0], x[3] - x[2], x[1])):
        if any(c[2] <= hi and lo <= c[3] for lo, hi in spans):
            continue
        spans.append((c[2], c[3]))
        taken.append(c)
    return taken


def depth_bins(taken: list[tuple[int, int, int, int]], cfg: dict) -> dict[str, int]:
    """Counts of chiasms by depth: exact for the shallow levels, and the top bin open-ended."""
    top = cfg["lab"]["chiasmus"]["min_depth"] + 3
    c = Counter(min(t[0], top) for t in taken)
    return {(f"{d}" if d < top else f"{top}+"): c.get(d, 0) for d in range(3, top + 1)}


def scan(s: list[str], cfg: dict, keep: bool = False, parallel: bool = False) -> dict:
    """Counts by depth at every scale; with ``keep`` the resolved chiasms too (positions only)."""
    t = cfg["lab"]["chiasmus"]
    res: dict = {}
    for w, stride in zip(t["scales"], t["strides"], strict=True):
        taken = resolve(candidates(s, w, stride, t["min_depth"], parallel=parallel))
        res[str(w)] = {"bins": depth_bins(taken, cfg), "n": len(taken)}
        if keep:
            res[str(w)]["chiasms"] = taken
    return res


def edwards_l(n: int) -> float:
    """Edwards and Edwards: chance of one given order of n elements each appearing twice."""
    return 1 / math.prod(range(1, 2 * n, 2))


def edwards_p(n: int, opportunities: float) -> float:
    return 1 - (1 - edwards_l(n)) ** opportunities


def edwards_check(cfg: dict) -> dict:
    """L by depth, and the number of opportunities N each published P implies (P = 1-(1-L)^N)."""
    pub = cfg["lab"]["chiasmus"]["edwards"]
    res: dict = {"L": {str(n): edwards_l(n) for n in range(2, 11)}}
    for name, (n, p) in pub.items():
        implied = math.log(1 - p) / math.log(1 - edwards_l(n))
        res[name] = {"n": n, "published_P": p, "implied_N": round(implied, 1)}
    names = list(pub)
    if len(names) == 2:
        a, b = names
        n_b, p_b = pub[b]
        res["P_for_second_with_first_N"] = round(edwards_p(n_b, res[a]["implied_N"]), 5)
    return res


# ------------------------------------------------------------------------------ one text


def measure(job: tuple[str, list[list[str]], int, int, int, bool]) -> dict:
    """Observed and shuffled counts for one text: (name, units, words, seed, shuffles)."""
    name, units, words, seed, shuffles = job
    cfg = config.load()
    t = cfg["lab"]["chiasmus"]
    s = flat(units)
    obs = scan(s, cfg, keep=True)
    res: dict = {"name": name, "words": words, "tokens": len(s)}
    res["observed"] = {w: {"bins": v["bins"], "n": v["n"]} for w, v in obs.items()}
    par = scan(s, cfg, parallel=True)
    res["parallel"] = {w: {"bins": v["bins"], "n": v["n"]} for w, v in par.items()}
    rng = random.Random(seed)
    sh = []
    for _ in range(shuffles):
        sh.append(scan(flat(shuffled(units, t["shuffle_block"], rng)), cfg))
    res["shuffled"] = [{w: {"bins": v["bins"], "n": v["n"]} for w, v in x.items()} for x in sh]
    return res


def rate(n: float, words: int) -> float:
    return round(n / max(words, 1) * 10000, 4)


def summarise(m: dict) -> dict:
    """Rates per 10,000 words (observed, shuffled mean, ratio) by scale and depth."""
    out_: dict = {"words": m["words"], "tokens": m["tokens"]}
    for w, o in m["observed"].items():
        sh = [x[w] for x in m["shuffled"]]
        mean_n = sum(x["n"] for x in sh) / max(len(sh), 1)
        pn = m["parallel"][w]["n"]
        row = {
            "observed_per_10k": rate(o["n"], m["words"]),
            "shuffled_per_10k": rate(mean_n, m["words"]),
            "ratio": round(o["n"] / mean_n, 3) if mean_n else None,
            "parallel_per_10k": rate(pn, m["words"]),
            "ratio_to_parallel": round(o["n"] / pn, 3) if pn else None,
            "observed_by_depth": o["bins"],
            "observed_by_depth_per_10k": {d: rate(n, m["words"]) for d, n in o["bins"].items()},
            "parallel_by_depth": m["parallel"][w]["bins"],
            "parallel_by_depth_per_10k": {
                d: rate(n, m["words"]) for d, n in m["parallel"][w]["bins"].items()
            },
            "shuffled_by_depth": {
                d: round(sum(x["bins"][d] for x in sh) / max(len(sh), 1), 2) for d in o["bins"]
            },
        }
        out_[w] = row
    return out_


# ------------------------------------------------------------------------------ the texts


def kjv_verses() -> list[dict]:
    return [json.loads(line) for line in KJV.read_text().splitlines()]


def kjv_units(rows: list[dict], cfg: dict) -> tuple[list[list[str]], int]:
    parts, words = [], 0
    for r in rows:
        u, n = units_of(r["text"] + " .", cfg)
        parts.append(u)
        words += n
    return join_units(parts), words


def bom_paragraphs() -> list[dict]:
    from lab.wherefore import EDITION, LABELS

    labels = {
        r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines()) if r["kind"] == "body"
    }
    rows = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if r["seq"] in labels:
            rows.append(
                {
                    "seq": r["seq"],
                    "book": r["book"],
                    "text": r["text"],
                    "chapter_1830": labels[r["seq"]]["chapter_1830"],
                }
            )
    return rows


def bom_units(rows: list[dict], cfg: dict) -> tuple[list[list[str]], int]:
    parts, words = [], 0
    for r in rows:
        u, n = units_of(r["text"] + " .", cfg)
        parts.append(u)
        words += n
    return join_units(parts), words


def library_sample(cfg: dict, n: int, seed: int, translations: bool) -> list[dict]:
    from lab import emode

    t = cfg["lab"]["chiasmus"]
    tab = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(tab["kind"], "work"), pc.equal(tab["has_text"], True)),
        pc.equal(tab["dup_keeper"], True),
    )
    trans = emode.translations() if translations else set()
    rows = [
        r
        for r in tab.filter(keep).to_pylist()
        if not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and t["year_min"] <= r["year"] <= t["year_max"]
        and (r["words"] or 0) >= t["window_words"]
        and ((r["work_id"] in trans) == translations)
    ]
    random.Random(seed).shuffle(rows)
    cat = door.catalog({r["work_id"] for r in rows[: n * 3]})
    picked = []
    for r in rows[: n * 3]:
        c = cat.get(r["work_id"])
        if c and c["text_path"]:
            picked.append({**c, **r})
        if len(picked) == n:
            break
    return picked


def window_of(row: dict, size: int) -> str | None:
    """``size`` consecutive words from the middle of a library work; None if unreadable."""
    try:
        text = door.text_of(row)
    except OSError:
        return None  # not attempted, never a zero
    toks = text.split()
    if len(toks) < size:
        return None
    a = (len(toks) - size) // 2
    return " ".join(toks[a : a + size])


def library_job(job: tuple[dict, int, int, int]) -> dict:
    row, size, seed, shuffles = job
    cfg = config.load()
    text = window_of(row, size)
    if text is None:
        return {"name": row["work_id"], "not_attempted": "unreadable or too short"}
    units, words = units_of(text, cfg)
    r = measure((row["work_id"], units, words, seed, shuffles))
    r["year"] = row["year"]
    return r


def named_texts(cfg: dict) -> dict[str, dict[str, str]]:
    from lab import emode

    t = cfg["lab"]["chiasmus"]
    js = {k: v for k, v in emode.js_texts().items() if len(v.split()) >= t["min_text_words"]}
    bs = {
        k: v for k, v in emode.bible_style_texts().items() if len(v.split()) >= t["min_text_words"]
    }
    return {"joseph_smith": js, "bible_style": bs}


# ------------------------------------------------------------------------------ check


def plant(s: list[str], depth: int, gap: int, rng: random.Random) -> tuple[list[str], int, int]:
    """Overwrite a stretch of ``s`` with a mirrored chiasm of nonce elements; (stream, lo, hi)."""
    left, right = [], []
    idx = rng.randrange(0, max(len(s) - 6 * (depth * (gap + 1)) - 20, 1))
    out_ = list(s)
    pos = idx
    keys = [f"zq{rng.randrange(10**6)}x{k}" for k in range(depth)]
    for _k in keys:
        left.append(pos)
        pos += 1 + rng.randint(0, gap)
    pos += rng.randint(1, gap + 1)
    for _k in range(depth):
        right.append(pos)
        pos += 1 + rng.randint(0, gap)
    for p, k in zip(left, keys, strict=True):
        out_[p] = k
    for p, k in zip(right, reversed(keys), strict=True):
        out_[p] = k
    return out_, left[0], right[-1]


def famous_kjv(cfg: dict, rows: list[dict]) -> dict:
    t = cfg["lab"]["chiasmus"]
    res = {}
    for name, (book, chap, v1, v2, need) in t["famous_kjv"].items():
        verses = [r for r in rows if r["book"] == book and r["chapter"] == chap]
        stream: list[str] = []
        lo = hi = None
        for r in verses:
            u, _ = units_of(r["text"] + " .", cfg)
            a = len(stream)
            stream += flat(u)
            if r["verse"] == v1:
                lo = a
            if r["verse"] == v2:
                hi = len(stream) - 1
        if lo is None or hi is None:
            res[name] = {"not_attempted": "passage not found"}
            continue
        best = {}
        found = False
        for w in t["scales"]:
            deepest = 0
            for depth, _c, a, b in candidates(stream, w, 1, t["check_min_depth"]):
                inside = max(0, min(b, hi) - max(a, lo) + 1) / (b - a + 1)
                if inside >= t["check_overlap"]:
                    deepest = max(deepest, depth)
            best[str(w)] = deepest
            found |= deepest >= need
        res[name] = {"expected_depth": need, "deepest_inside_by_scale": best, "found": found}
    res["found"] = sum(1 for v in res.values() if isinstance(v, dict) and v.get("found"))
    res["of"] = len(t["famous_kjv"])
    return res


def planted(cfg: dict, pool: list[list[str]]) -> dict:
    t = cfg["lab"]["chiasmus"]
    rng = random.Random(t["seed"] + 7)
    res = {}
    total = hit = 0
    for depth in t["plant_depths"]:
        h = 0
        for i in range(t["plants"]):
            base = pool[i % len(pool)]
            s, lo, hi = plant(base, depth, t["plant_gap"], rng)
            ok = False
            for w, _stride in zip(t["scales"], t["strides"], strict=True):
                for d, _c, a, b in candidates(s, w, 1, t["min_depth"]):
                    if d >= depth and a <= hi and lo <= b:
                        ok = True
                        break
                if ok:
                    break
            h += ok
        res[str(depth)] = {"planted": t["plants"], "found": h, "rate": round(h / t["plants"], 3)}
        total += t["plants"]
        hit += h
    res["overall"] = round(hit / total, 3)
    res["passed"] = res["overall"] >= t["plant_bar"]
    return res


def check(cfg: dict, plain: list[dict] | None = None) -> dict:
    """Known-answer check. ``plain`` is the library measures (for part 3) when already taken."""
    t = cfg["lab"]["chiasmus"]
    res: dict = {}
    fam = famous_kjv(cfg, kjv_verses())
    fam["passed"] = fam["found"] >= t["check_bar_famous"]
    res["famous_kjv"] = fam
    rows = library_sample(cfg, t["plants"], t["seed"] + 3, False)
    pool = []
    for r in rows:
        text = window_of(r, t["block_tokens"] * 3)
        if text:
            pool.append(flat(units_of(text, cfg)[0]))
    pool = [p for p in pool if len(p) > 1000]
    res["planted"] = planted(cfg, pool)
    if plain is not None:
        p = str(t["primary_scale"])
        ob = sum(x["observed"][p]["n"] for x in plain)
        sh = sum(sum(y[p]["n"] for y in x["shuffled"]) / len(x["shuffled"]) for x in plain)
        par = sum(x["parallel"][p]["n"] for x in plain)
        ratio = ob / par if par else None
        res["plain_prose"] = {
            "observed": ob,
            "parallel_order": par,
            "ratio_to_parallel": round(ratio, 3) if ratio else None,
            "shuffled_mean": round(sh, 1),
            "ratio_to_shuffled": round(ob / sh, 3) if sh else None,
            "passed": ratio is not None and ratio <= t["plain_ratio_bar"],
        }
    res["passed"] = (
        fam["passed"]
        and res["planted"]["passed"]
        and (plain is None or res["plain_prose"]["passed"])  # part 3 needs the library sample
    )
    return res


# ------------------------------------------------------------------------------ the run


def pct_of(x: float, ref: list[float]) -> float:
    """Share of ``ref`` values below ``x`` (ties half), in percent."""
    if not ref:
        return float("nan")
    lo = sum(1 for v in ref if v < x)
    eq = sum(1 for v in ref if v == x)
    return round(100 * (lo + eq / 2) / len(ref), 1)


def quant(xs: list[float]) -> dict:
    xs = sorted(v for v in xs if v is not None)
    if not xs:
        return {}
    return {str(q): xs[min(len(xs) - 1, int(len(xs) * q / 100))] for q in (5, 25, 50, 75, 90, 97.5)}


def group_table(ms: list[dict], cfg: dict) -> dict:
    """Pooled and per-work distributions of the rate and the ratio, at every scale."""
    res: dict = {"n": len(ms)}
    for w in cfg["lab"]["chiasmus"]["scales"]:
        w = str(w)
        sums = [summarise(m)[w] for m in ms]
        obs = sum(m["observed"][w]["n"] for m in ms)
        shuf = sum(sum(y[w]["n"] for y in m["shuffled"]) / len(m["shuffled"]) for m in ms)
        words = sum(m["words"] for m in ms)
        par = sum(m["parallel"][w]["n"] for m in ms)
        bins = list(ms[0]["observed"][w]["bins"])
        res[w] = {
            "pooled_observed_by_depth_per_10k": {
                d: rate(sum(m["observed"][w]["bins"][d] for m in ms), words) for d in bins
            },
            "pooled_parallel_by_depth_per_10k": {
                d: rate(sum(m["parallel"][w]["bins"][d] for m in ms), words) for d in bins
            },
            "pooled_parallel_per_10k": rate(par, words),
            "pooled_ratio_to_parallel": round(obs / par, 3) if par else None,
            "ratio_to_parallel_quantiles": quant([s["ratio_to_parallel"] for s in sums]),
            "pooled_observed_per_10k": rate(obs, words),
            "pooled_shuffled_per_10k": rate(shuf, words),
            "pooled_ratio": round(obs / shuf, 3) if shuf else None,
            "rate_quantiles": quant([s["observed_per_10k"] for s in sums]),
            "ratio_quantiles": quant([s["ratio"] for s in sums]),
        }
    return res


def split_blocks(units: list[list[str]], size: int) -> list[list[list[str]]]:
    out_, cur, n = [], [], 0
    for u in units:
        cur.append(u)
        n += len(u)
        if n >= size:
            out_.append(cur)
            cur, n = [], 0
    return out_


def verdict(bom: dict, lib: list[dict], cfg: dict) -> dict:
    t = cfg["lab"]["chiasmus"]
    p = str(t["primary_scale"])
    sb = summarise(bom)[p]
    sl = [summarise(m)[p] for m in lib]
    rate_ref = [s["observed_per_10k"] for s in sl]
    ratio_ref = [s["ratio_to_parallel"] for s in sl if s["ratio_to_parallel"] is not None]
    pr = pct_of(sb["observed_per_10k"], rate_ref)
    pq = pct_of(sb["ratio_to_parallel"] or 0, ratio_ref)
    shuf_ref = [s["ratio"] for s in sl if s["ratio"] is not None]
    hi, lo = t["yes_percentile"], t["no_percentile"]
    answer = (
        "yes (more than the library)"
        if pr > hi and pq > hi
        else "no (within the library)"
        if pr <= lo and pq <= lo
        else "cannot tell"
    )
    return {
        "scale": p,
        "depth": t["primary_depth"],
        "book_rate_per_10k": sb["observed_per_10k"],
        "book_ratio_to_parallel": sb["ratio_to_parallel"],
        "book_ratio_to_shuffled": sb["ratio"],
        "percentile_of_rate_in_library": pr,
        "percentile_of_ratio_to_parallel_in_library": pq,
        "percentile_of_ratio_to_shuffled_in_library": pct_of(sb["ratio"] or 0, shuf_ref),
        "answer": answer,
    }


def deepest(s: list[str], w: int, parallel: bool = False) -> int:
    return max((x[0] for x in candidates(s, w, 1, 2, parallel=parallel)), default=0)


def isolated_blocks(cfg: dict, lib_rows: list[dict], kjv: list[str], size: int) -> dict:
    """Streams of ``size`` content tokens cut at random from library windows and from the Bible."""
    t = cfg["lab"]["chiasmus"]
    rng = random.Random(t["seed"] + size)
    res: dict[str, list[list[str]]] = {"library": [], "king_james": []}
    for row in lib_rows[: t["famous_blocks"]]:
        text = window_of(row, t["window_words"])
        if text is None:
            continue
        s = flat(units_of(text, cfg)[0])
        if len(s) > size:
            a = rng.randrange(len(s) - size)
            res["library"].append(s[a : a + size])
    for _ in range(t["famous_blocks"]):
        a = rng.randrange(len(kjv) - size)
        res["king_james"].append(kjv[a : a + size])
    return res


def famous_bom(cfg: dict, rows: list[dict], lib_rows: list[dict], kjv: list[str]) -> dict:
    """What the fixed rule finds in each famous chapter, run on the chapter alone, beside the
    same call on blocks of equal length cut from the library and the Bible. No tuning."""
    t = cfg["lab"]["chiasmus"]
    res = {}
    for name, (first, last) in t["famous_bom"].items():
        sel = [r for r in rows if first <= r["seq"] <= last]
        units, words = bom_units(sel, cfg)
        s = flat(units)
        blocks = isolated_blocks(cfg, lib_rows, kjv, len(s))
        by_scale = {}
        for w in t["scales"]:
            inv, par = deepest(s, w), deepest(s, w, True)
            row = {"deepest_inverted": inv, "deepest_parallel": par}
            for gname, g in blocks.items():
                di = [deepest(b, w) for b in g]
                dp = [deepest(b, w, True) for b in g]
                row[gname] = {
                    "blocks": len(g),
                    "inverted_at_least_as_deep": round(sum(d >= inv for d in di) / len(g), 4),
                    "parallel_at_least_as_deep_as_the_chapter_inverted": round(
                        sum(d >= inv for d in dp) / len(g), 4
                    ),
                    "median_deepest_inverted": sorted(di)[len(di) // 2],
                    "max_deepest_inverted": max(di),
                }
            by_scale[str(w)] = row
        res[name] = {"words": words, "tokens": len(s), "by_scale": by_scale}
    return res


def run(cfg: dict) -> dict:
    t = cfg["lab"]["chiasmus"]
    res: dict = {"settings": t}
    workers = t["workers"]
    # The library sample and its shuffles are measured first: part 3 of the check needs them.
    lib_rows = library_sample(cfg, t["library_n"], t["seed"], False)
    tr_rows = library_sample(cfg, t["translations_n"], t["seed"] + 1, True)
    with ProcessPoolExecutor(workers) as ex:
        lib = list(
            ex.map(
                library_job,
                [
                    (r, t["window_words"], t["seed"] + i, t["shuffles"])
                    for i, r in enumerate(lib_rows)
                ],
                chunksize=4,
            )
        )
        trn = list(
            ex.map(
                library_job,
                [
                    (r, t["window_words"], t["seed"] + 1000 + i, t["shuffles"])
                    for i, r in enumerate(tr_rows)
                ],
                chunksize=4,
            )
        )
    lib_ok = [m for m in lib if "observed" in m]
    trn_ok = [m for m in trn if "observed" in m]
    res["library"] = {
        "drawn": len(lib_rows),
        "measured": len(lib_ok),
        "not_attempted": [m["name"] for m in lib if "observed" not in m],
    }
    res["translations"] = {
        "drawn": len(tr_rows),
        "measured": len(trn_ok),
        "not_attempted": [m["name"] for m in trn if "observed" not in m],
    }
    chk = check(cfg, lib_ok)
    res["known_answer"] = chk
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
        res["library"]["groups"] = group_table(lib_ok, cfg)
        return res
    # Named texts, the King James Bible and the Book of Mormon.
    rows = kjv_verses()
    ot = [r for r in rows if r["section"] == "OT"]
    nt = [r for r in rows if r["section"] == "NT"]
    bom_rows = bom_paragraphs()
    from lab.wherefore import QUOTED

    bom_free = [r for r in bom_rows if (r["book"], r["chapter_1830"]) not in QUOTED]
    jobs = []
    for name, rs, fn in (
        ("king_james_ot", ot, kjv_units),
        ("king_james_nt", nt, kjv_units),
        ("king_james_all", ot + nt, kjv_units),
        ("book_of_mormon", bom_rows, bom_units),
        ("book_of_mormon_without_quoted_chapters", bom_free, bom_units),
    ):
        u, w = fn(rs, cfg)
        jobs.append((name, u, w, t["seed"] + len(jobs), t["shuffles"]))
    named = named_texts(cfg)
    for grp, texts in named.items():
        for name, text in texts.items():
            u, w = units_of(text, cfg)
            jobs.append((f"{grp}/{name}", u, w, t["seed"] + len(jobs), t["shuffles"]))
    with ProcessPoolExecutor(workers) as ex:
        done = list(ex.map(measure, jobs, chunksize=1))
    by = {m["name"]: m for m in done}
    res["named"] = {k: summarise(m) for k, m in by.items()}
    res["edwards"] = edwards_check(cfg)
    res["verdict"] = verdict(by["book_of_mormon"], lib_ok, cfg)
    res["verdict_without_quoted_chapters"] = verdict(
        by["book_of_mormon_without_quoted_chapters"], lib_ok, cfg
    )
    # Each long text in blocks, to show the spread of the rate inside one text.
    spread = {}
    for name in ("king_james_all", "book_of_mormon"):
        u = next(j[1] for j in jobs if j[0] == name)
        blocks = split_blocks(u, t["block_tokens"])
        bj = [
            (f"{name}#{i}", b, sum(len(x) for x in b), t["seed"] + 500 + i, t["shuffles"])
            for i, b in enumerate(blocks)
        ]
        with ProcessPoolExecutor(workers) as ex:
            ms = list(ex.map(measure, bj, chunksize=1))
        p = str(t["primary_scale"])
        spread[name] = {
            "blocks": len(ms),
            "block_tokens": t["block_tokens"],
            "rate_primary": quant([summarise(m)[p]["observed_per_10k"] for m in ms]),
            "ratio_primary": quant([summarise(m)[p]["ratio"] for m in ms]),
        }
    res["blocks_of_long_texts"] = spread
    # Groups.
    named_groups = {
        g: [by[f"{g}/{k}"] for k in texts if f"{g}/{k}" in by] for g, texts in named.items()
    }
    res["groups"] = {
        "library": group_table(lib_ok, cfg),
        "translations": group_table(trn_ok, cfg),
        **{g: group_table(ms, cfg) for g, ms in named_groups.items() if ms},
    }
    kjv_stream = flat(kjv_units(ot + nt, cfg)[0])
    res["famous_cases"] = famous_bom(cfg, bom_rows, lib_rows, kjv_stream)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "check":
        print(json.dumps(check(cfg), indent=1))
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(
        json.dumps(
            {k: v for k, v in res.items() if k in ("known_answer", "verdict", "stopped")}, indent=1
        )[:6000]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
