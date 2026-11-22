"""BOM-122: the Book of Mormon's Isaiah variants against every work printed before 1830.

Each 1830 paragraph that the study's King James mask ties to an Isaiah chapter is aligned word by
word to that chapter (and its neighbours); the gaps inside a quoted segment are the variants
(changed, added, dropped words), each on its King James verse, with the italic flag of every King
James word changed or dropped (eBible 1769 brackets). A variant short enough and distinctive
enough (its Book of Mormon wording, with a few aligned words either side, nowhere in the King James
Bible) is searched for in every work of the library printed up to 1829, in the context of its
verse: the string must occur with at least ``min_context`` of the verse's own content words nearby.
Decoys are the same edits made at other places in Isaiah where the quoting text keeps the King
James words; a work's share of readings matched is set beside its share of decoys matched. The
known-answer check runs the same steps with Lowth's 1795 translation of Isaiah as the query and
asks that other printings of Lowth come out on top; if it misses, the Book of Mormon is not
scored. The test card, written first, is
``data/private/lab/owner/2026-11-21-isaiah-variants/card.md``; settings are ``lab.isaiah``. Public
outputs hold verse references, words of the public-domain 1830 and King James texts, work ids,
years and counts; no library text. No model is called.

Usage::

    python -m lab.isaiah variants   # variant list -> data/lab/reruns/isaiah_variants/variants.json
    python -m lab.isaiah check      # known answer (Lowth) -> .../isaiah_variants/check.json
    python -m lab.isaiah run        # check, then the Book of Mormon -> .../result.json
    python -m lab.isaiah judge      # judge jobs (prepared, not run) -> data/private/lab/owner/...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from difflib import SequenceMatcher
from pathlib import Path

from lab import door, registry
from lab.paths import FAST, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "isaiah_variants"
CACHE = FAST / "isaiah"
CARD = NOTES / "owner" / "2026-11-21-isaiah-variants"
KJV = Path("data/kjv/kjv.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
MASK = Path("data/kjv_mask/bom/spans.jsonl")
RANGES = Path("data/italics/translation_ranges.json")
TOWNSEND = OUT / "townsend_items.json"
WORD = re.compile(r"[a-z]+")
OUR = re.compile(r"\b([a-z]{2,})our(s?)\b")  # honour/honor, labour/labor: spelling, not a variant


# ------------------------------------------------------------------------------------ words
def norm(text: str) -> str:
    return OUR.sub(r"\1or\2", text.lower().replace("ſ", "s"))


def tokens(text: str) -> list[str]:
    return WORD.findall(norm(text))


class Isaiah:
    """King James Isaiah as one word list, with each word's chapter, verse and italic flag, and the
    whole King James Bible as one string for the "found elsewhere in the King James" test."""

    def __init__(self, path: Path = KJV) -> None:
        self.words: list[str] = []
        self.where: list[tuple[int, int]] = []
        self.italic: list[bool] = []
        self.chapter_start: dict[int, int] = {}
        self.verse_words: dict[tuple[int, int], list[str]] = {}
        bible, freq = [], Counter()
        for line in path.read_text(encoding="utf-8").splitlines():
            v = json.loads(line)
            toks = tokens(v["text"])
            bible += toks
            freq.update(toks)
            if v["book"] != "ISA":
                continue
            ch, vs = v["chapter"], v["verse"]
            self.chapter_start.setdefault(ch, len(self.words))
            self.verse_words[(ch, vs)] = toks
            for k, part in enumerate(re.split(r"[\[\]]", v["text_marked"])):
                for w in tokens(part):
                    self.words.append(w)
                    self.where.append((ch, vs))
                    self.italic.append(k % 2 == 1)
        self.bible = " " + " ".join(bible) + " "
        self.freq = freq
        self.chapters = sorted(self.chapter_start)

    def span(self, chapters: list[int]) -> tuple[int, int]:
        """Global word range of a run of consecutive chapters."""
        a = self.chapter_start[chapters[0]]
        nxt = chapters[-1] + 1
        b = self.chapter_start.get(nxt, len(self.words))
        return a, b

    def in_bible(self, toks: list[str]) -> bool:
        return (" " + " ".join(toks) + " ") in self.bible

    def context(self, ch: int, vs: int, d: dict, exclude: set[str]) -> set[str]:
        stop = set(d["stop_words"])
        words = set()
        for v in (vs - 1, vs, vs + 1):
            for w in self.verse_words.get((ch, v), []):
                if len(w) >= d["content_min_len"] and w not in stop and w not in exclude:
                    words.add(w)
        return words


# ------------------------------------------------------------------------------------ alignment
def segments(k: list[str], q: list[str], d: dict) -> list[list[tuple[str, int, int, int, int]]]:
    """Quoted segments of ``q`` against ``k``: lists of difflib opcodes (op, i1, i2, j1, j2) with
    ``i`` into ``k`` and ``j`` into ``q``. Anchors are matching runs of at least ``seed`` words;
    consecutive anchors with small gaps form one segment; gaps inside a segment are diffed again."""
    sm = SequenceMatcher(a=k, b=q, autojunk=False)
    anchors = [b for b in sm.get_matching_blocks() if b.size >= d["seed"]]
    chains: list[list] = []
    for b in anchors:
        if chains:
            p = chains[-1][-1]
            ga, gb = b.a - (p.a + p.size), b.b - (p.b + p.size)
            joined = (ga <= d["max_gap"] and gb <= d["max_gap"]) or (
                min(ga, gb) == 0 and max(ga, gb) <= d["max_gap_one_side"]
            )
            if joined:
                chains[-1].append(b)
                continue
        chains.append([b])
    segs = []
    for chain in chains:
        if sum(b.size for b in chain) < d["min_segment"]:
            continue
        ops = []
        for n, b in enumerate(chain):
            if n:
                p = chain[n - 1]
                i0, j0 = p.a + p.size, p.b + p.size
                sub = SequenceMatcher(a=k[i0 : b.a], b=q[j0 : b.b], autojunk=False)
                for op, i1, i2, j1, j2 in sub.get_opcodes():
                    ops.append((op, i0 + i1, i0 + i2, j0 + j1, j0 + j2))
            ops.append(("equal", b.a, b.a + b.size, b.b, b.b + b.size))
        segs.append(ops)
    return segs


KIND = {"replace": "changed", "delete": "dropped", "insert": "added"}


def variants_of(
    query: str, q: list[str], chapters: list[int], isa: Isaiah, d: dict
) -> tuple[list[dict], set[int], set[int]]:
    """Variants of one query text against a run of chapters; also the King James positions it
    keeps (inside equal runs) and touches (changed, dropped, or beside an addition)."""
    a, b = isa.span(chapters)
    k = isa.words[a:b]
    found, kept, touched = [], set(), set()
    for ops in segments(k, q, d):
        si0, si1 = ops[0][1], ops[-1][2]
        sj0, sj1 = ops[0][3], ops[-1][4]
        for op, i1, i2, j1, j2 in ops:
            if op == "equal":
                kept.update(range(a + i1, a + i2))
                continue
            g1, g2 = a + i1, a + i2
            touched.update(range(g1, g2) if g2 > g1 else (g1 - 1, g1))
            if op == "insert":
                ch, vs = isa.where[g1 - 1] if g1 > a else isa.where[g1]
                nxt = isa.where[g1] if g1 < len(isa.words) else (ch, vs)
                also = list(nxt) if nxt != (ch, vs) else None
            else:
                ch, vs = isa.where[g1]
                also = None
            v = {
                "query": query,
                "ref": f"{ch}:{vs}",
                "chapter": ch,
                "verse": vs,
                "also_ref": f"{also[0]}:{also[1]}" if also else None,
                "kind": KIND[op],
                "kjv": " ".join(isa.words[g1:g2]),
                "new": " ".join(q[j1:j2]),
                "kjv_italic": [isa.italic[x] for x in range(g1, g2)],
                "kjv_pos": g1,
                "long": max(i2 - i1, j2 - j1) > d["max_edit_words"],
            }
            v.update(reading_of(q, j1, j2, (sj0, sj1), k, i1, i2, (si0, si1), isa, d, ch, vs))
            found.append(v)
    return found, kept, touched


def reading_of(q, j1, j2, qb, k, i1, i2, kb, isa: Isaiah, d: dict, ch: int, vs: int) -> dict:
    """The searchable reading of a variant: the quoting text's words with ``ctx`` aligned words a
    side, widened while found in the King James Bible; and the King James form at the same place."""
    for c in range(d["ctx"], d["ctx_max"] + 1):
        r = q[max(qb[0], j1 - c) : min(qb[1], j2 + c)]
        if len(r) < d["min_ngram"] or isa.in_bible(r):
            continue
        kf = k[max(kb[0], i1 - c) : min(kb[1], i2 + c)]
        ctx = isa.context(ch, vs, d, set(r) | set(kf))
        if len(ctx) < d["min_context"]:
            return {"searchable": False, "why_not": "too few context words in the verse"}
        return {"searchable": True, "reading": r, "kjv_form": kf, "context": sorted(ctx)}
    why = "reading occurs elsewhere in the King James Bible"
    if len(q[max(qb[0], j1 - d["ctx_max"]) : min(qb[1], j2 + d["ctx_max"])]) < d["min_ngram"]:
        why = "reading too short"
    return {"searchable": False, "why_not": why}


def unique_readings(found: list[dict], d: dict) -> list[dict]:
    """One entry per distinct reading at one verse (a verse quoted twice with the same change
    counts once); the instances keep their query ids."""
    by: dict[tuple, dict] = {}
    for v in found:
        if v["long"] or not v.get("searchable"):
            continue
        key = (v["ref"], tuple(v["reading"]))
        if key in by:
            by[key]["queries"].append(v["query"])
            continue
        by[key] = {**v, "queries": [v["query"]]}
    out_ = list(by.values())
    for n, r in enumerate(out_):
        r["rid"] = n
    return out_


# ------------------------------------------------------------------------------------ decoys
def decoys(
    readings: list[dict], kept: set[int], touched: set[int], isa: Isaiah, d: dict
) -> list[dict]:
    """The same edits at other places where the query keeps the King James words."""
    rng = random.Random(d["random_seed"])
    safe = kept - touched
    W = isa.words
    by_word: dict[str, list[int]] = defaultdict(list)
    for p, w in enumerate(W):
        by_word[w].append(p)
    pad = d["ctx_max"]
    made, seen = [], set()
    for r in readings:
        K = r["kjv"].split() if r["kjv"] else []
        new = r["new"].split() if r["new"] else []
        if K:
            sites = [p for p in by_word[K[0]] if W[p : p + len(K)] == K]
            span = len(K)
        else:
            left = W[r["kjv_pos"] - 1] if r["kjv_pos"] > 0 else None
            sites = [p + 1 for p in by_word.get(left, [])]
            span = 0
        ok = [
            p
            for p in sites
            if all(x in safe for x in range(p - pad, p + span + pad))
            and isa.where[p] != (r["chapter"], r["verse"])
        ]
        rng.shuffle(ok)
        n = 0
        for p in ok:
            if n >= d["decoys_per_variant"]:
                break
            res = None
            for c in range(d["ctx"], d["ctx_max"] + 1):
                rd = W[p - c : p] + new + W[p + span : p + span + c]
                if len(rd) < d["min_ngram"] or isa.in_bible(rd):
                    continue
                res = rd
                break
            if res is None or (p, tuple(res)) in seen:
                continue
            ch, vs = isa.where[p]
            ctx = isa.context(ch, vs, d, set(res) | set(W[p - c : p + span + c]))
            if len(ctx) < d["min_context"]:
                continue
            seen.add((p, tuple(res)))
            made.append({"rid": r["rid"], "ref": f"{ch}:{vs}", "reading": res,
                         "context": sorted(ctx)})  # fmt: skip
            n += 1
    return made


# ------------------------------------------------------------------------------------ queries
def bom_queries(isa: Isaiah, d: dict) -> list[tuple[str, list[str], list[list[int]]]]:
    """(id, words, chapter runs) for every 1830 paragraph the mask ties to Isaiah."""
    from kjv_mask.run import _docs

    refs: dict[str, set[int]] = {}
    for line in MASK.read_text().splitlines():
        r = json.loads(line)
        chs = {int(s["ref"][8:]) for s in r["spans"] if s["ref"].startswith("kjv:ISA.")}
        if chs:
            refs[r["id"]] = chs
    qs = []
    for doc in _docs("bom"):
        if doc["id"] not in refs:
            continue
        chs = set()
        for c in refs[doc["id"]]:
            chs.update(x for x in range(c - d["neighbours"], c + d["neighbours"] + 1)
                       if x in isa.chapter_start)  # fmt: skip
        qs.append((doc["id"], tokens(doc["load"]()), runs(sorted(chs))))
    return qs


def runs(chs: list[int]) -> list[list[int]]:
    """Consecutive chapters grouped: [1,2,3,52,53] -> [[1,2,3],[52,53]]."""
    out_: list[list[int]] = []
    for c in chs:
        if out_ and c == out_[-1][-1] + 1:
            out_[-1].append(c)
        else:
            out_.append([c])
    return out_


def lowth_queries(isa: Isaiah, d: dict) -> list[tuple[str, list[str], list[list[int]]]]:
    """Lowth's translation (1795, translation range only) in pieces, each with its chapter."""
    wid = d["query_ka"]
    rng = json.loads(RANGES.read_text())["volumes"][wid]["ranges"]
    text = door.text_of(door.catalog({wid})[wid])
    words = [w for a, b in rng for w in tokens(text[a:b])]
    grams = {}
    for ch in isa.chapters:
        a, b = isa.span([ch])
        w = isa.words[a:b]
        grams[ch] = {tuple(w[i : i + 4]) for i in range(len(w) - 3)}
    qs = []
    n = d["ka_chunk_words"]
    for i in range(0, len(words), n):
        piece = words[i : i + n]
        g = {tuple(piece[x : x + 4]) for x in range(len(piece) - 3)}
        best = max(isa.chapters, key=lambda c: len(g & grams[c]))
        if len(g & grams[best]) < d["ka_min_shared"]:
            continue
        chs = [c for c in range(best - d["neighbours"], best + d["neighbours"] + 1)
               if c in isa.chapter_start]  # fmt: skip
        qs.append((f"lowth:{i // n}", piece, runs(chs)))
    return qs


def build(queries, isa: Isaiah, d: dict) -> dict:
    found, kept, touched = [], set(), set()
    for qid, q, chruns in queries:
        for chs in chruns:
            f, k, t = variants_of(qid, q, chs, isa, d)
            found += f
            kept |= k
            touched |= t
    # one variant per query and King James place (a paragraph aligned to overlapping chapter runs)
    uniq = {}
    for v in found:
        uniq.setdefault((v["query"], v["kjv_pos"], v["kind"], v["new"]), v)
    found = list(uniq.values())
    readings = unique_readings(found, d)
    return {"variants": found, "readings": readings, "kept": kept, "touched": touched,
            "decoys": decoys(readings, kept, touched, isa, d)}  # fmt: skip


# ------------------------------------------------------------------------------------ scan
_P: dict = {}


def patterns(readings: list[dict], dec: list[dict], d: dict) -> dict:
    """Search patterns: ``r<rid>`` readings, ``k<rid>`` King James forms, ``d<n>`` decoys."""
    items = []
    for r in readings:
        items.append((f"r{r['rid']}", r["reading"], r["context"]))
        items.append((f"k{r['rid']}", r["kjv_form"], r["context"]))
    for n, x in enumerate(dec):
        items.append((f"d{n}", x["reading"], x["context"]))
    return {"items": items, "window": d["window"], "min_context": d["min_context"]}


def _init(p: dict, freq: dict) -> None:
    keys: dict[str, list] = defaultdict(list)
    for n, (_pid, toks, _ctx) in enumerate(p["items"]):
        off = min(range(len(toks)), key=lambda i: (freq.get(toks[i], 0), -len(toks[i])))
        keys[toks[off]].append((n, off))
    _P.clear()
    _P.update(p, keys=dict(keys), ctx=[set(c) for _, _, c in p["items"]])


def match(toks: list[str], first: bool = False) -> dict[int, int]:
    """Pattern index -> token position of its first hit in context."""
    keys, items, ctxs = _P["keys"], _P["items"], _P["ctx"]
    W, need = _P["window"], _P["min_context"]
    found: dict[int, int] = {}
    for i, t in enumerate(toks):
        if t not in keys:
            continue
        for n, off in keys[t]:
            if n in found:
                continue
            s = i - off
            pat = items[n][1]
            if s < 0 or toks[s : s + len(pat)] != pat:
                continue
            if len(ctxs[n] & set(toks[max(0, s - W) : s + len(pat) + W])) >= need:
                found[n] = s
    return found


def _scan_one(row: dict) -> tuple[str, list[int] | None]:
    try:
        toks = tokens(door.text_of(row))
    except OSError:
        return row["work_id"], None  # unreadable: not attempted, never a zero
    return row["work_id"], sorted(match(toks))


def library(d: dict, hold_out: set[str] = frozenset()) -> list[dict]:
    t = registry.load().to_pylist()
    rows = [
        r
        for r in t
        if r["kind"] == "work"
        and r["has_text"]
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and r["year"] <= d["year_max"]
        and r["work_id"] not in hold_out
    ]
    cat = door.catalog({r["work_id"] for r in rows})
    return [{**cat[r["work_id"]], **r} for r in rows if r["work_id"] in cat]


def scan(rows: list[dict], p: dict, freq: Counter, d: dict, label: str) -> dict:
    """Matched pattern ids per work, cached on local disk by pattern and library hash."""
    key = hashlib.sha256(json.dumps([p, sorted(r["work_id"] for r in rows)]).encode())
    path = CACHE / f"scan_{label}_{key.hexdigest()[:16]}.json"
    if path.exists():
        print(f"scan reused from {path}", flush=True)
        return json.loads(path.read_text())
    small = {w: freq[w] for _, toks, _ in p["items"] for w in toks}
    hits, unreadable, t0 = {}, [], time.time()
    rows = sorted(rows, key=lambda r: -(r["words"] or 0))  # big texts first: even finish
    with ProcessPoolExecutor(d["workers"], initializer=_init, initargs=(p, small)) as pool:
        for n, (wid, found) in enumerate(pool.map(_scan_one, rows, chunksize=8)):
            if found is None:
                unreadable.append(wid)
            elif found:
                hits[wid] = [p["items"][i][0] for i in found]
            if n % 20000 == 0:
                print(f"  {label}: {n:,}/{len(rows):,} works, {time.time() - t0:.0f} s",
                      flush=True)  # fmt: skip
    res = {"works": len(rows), "unreadable": unreadable, "hits": hits,
           "seconds": round(time.time() - t0)}  # fmt: skip
    out(path).write_text(json.dumps(res) + "\n")
    return res


# ------------------------------------------------------------------------------------ scoring
def fisher_greater(a: int, n: int, b: int, m: int) -> float:
    from scipy.stats import fisher_exact

    return float(fisher_exact([[a, n - a], [b, m - b]], alternative="greater")[1])


def score(sc: dict, readings: list[dict], dec: list[dict], rows: list[dict], d: dict) -> dict:
    N, M = len(readings), len(dec)
    by = {r["work_id"]: r for r in rows}
    lowth = re.compile(d["lowth_title"], re.I)
    com = [re.compile(x, re.I) for x in d["commentary_title"]]
    tra = [re.compile(x, re.I) for x in d["translation_title"]]

    def title(w: str) -> str:
        return " ".join((by[w]["title"] or "").split())

    memo: dict[str, list[str]] = {}

    def klass(w: str) -> list[str]:
        if w not in memo:
            memo[w] = _klass(w)
        return memo[w]

    def _klass(w: str) -> list[str]:
        t = title(w)
        c = []
        if w == d["clarke_isaiah"]:
            c.append("clarke_isaiah")
        if lowth.search(t):
            c.append("lowth")
        if all(x.search(t) for x in com):
            c.append("commentary")
        if all(x.search(t) for x in tra):
            c.append("translation")
        return c

    works = []
    per_r: dict[int, list[str]] = defaultdict(list)
    per_k: dict[int, int] = Counter()
    per_d: dict[int, list[str]] = defaultdict(list)
    for w, ids in sc["hits"].items():
        r = [int(x[1:]) for x in ids if x[0] == "r"]
        k = [int(x[1:]) for x in ids if x[0] == "k"]
        dd = [int(x[1:]) for x in ids if x[0] == "d"]
        for x in r:
            per_r[x].append(w)
        for x in k:
            per_k[x] += 1
        for x in dd:
            per_d[x].append(w)
        if r or dd:
            works.append({"work_id": w, "year": by[w]["year"], "readings": len(r),
                          "decoys": len(dd), "kjv_forms": len(k), "class": klass(w)})  # fmt: skip
    for x in works:
        x["reading_share"] = round(x["readings"] / N, 4) if N else None
        x["decoy_share"] = round(x["decoys"] / M, 4) if M else None
        x["excess"] = round(x["readings"] - N * x["decoys"] / M, 2) if M else None
    works.sort(key=lambda x: (-x["readings"], x["decoys"], x["work_id"]))
    for n, x in enumerate(works):
        same = n and works[n - 1]["readings"] == x["readings"]
        x["rank"] = works[n - 1]["rank"] if same else n + 1
        x["title"] = title(x["work_id"])[:90]

    def found_in(cls: str | None, table: dict) -> int:
        n = 0
        for _rid, ws in table.items():
            if any(cls is None or cls in klass(w) for w in ws):
                n += 1
        return n

    groups = {}
    for cls in ("clarke_isaiah", "lowth", "commentary", "translation", None):
        name = cls or "any_work"
        a, b = found_in(cls, per_r), found_in(cls, per_d)
        groups[name] = {"readings_found": a, "of_readings": N, "decoys_found": b, "of_decoys": M,
                        "reading_share": round(a / N, 4) if N else None,
                        "decoy_share": round(b / M, 4) if M else None}  # fmt: skip
    groups["none"] = {"readings_found": N - groups["any_work"]["readings_found"], "of": N}
    return {"works": works, "per_reading": per_r, "per_kjv": per_k, "per_decoy": per_d,
            "groups": groups, "klass": klass}  # fmt: skip


def stats_for(works: list[dict], wid: str, N: int, M: int) -> dict:
    x = next((w for w in works if w["work_id"] == wid), None)
    a, b = (x["readings"], x["decoys"]) if x else (0, 0)
    ratio = (a / N) / (b / M) if b and N and M else None
    return {"work_id": wid, "readings": a, "decoys": b, "of_readings": N, "of_decoys": M,
            "rank": x["rank"] if x else None, "works_ranked": len(works),
            "ratio": round(ratio, 3) if ratio else ("inf" if a else None),
            "fisher_p_greater": fisher_greater(a, N, b, M) if N and M else None}  # fmt: skip


# ------------------------------------------------------------------------------------ check
def check(cfg: dict, isa: Isaiah) -> dict:
    d = cfg["lab"]["isaiah"]
    built = build(lowth_queries(isa, d), isa, d)
    rd, dec = built["readings"], built["decoys"]
    rows = library(d, {d["query_ka"]})
    sc = scan(rows, patterns(rd, dec, d), isa.freq, d, "lowth")
    s = score(sc, rd, dec, rows, d)
    top = s["works"][: d["ka_top"]]
    lowth = [w for w in s["works"] if "lowth" in w["class"]]
    best = lowth[0] if lowth else None
    ratio = None
    if best and best["decoys"]:
        ratio = (best["readings"] / len(rd)) / (best["decoys"] / len(dec))
    elif best and best["readings"]:
        ratio = float("inf")
    a = sum("lowth" in w["class"] for w in top) >= d["ka_min_lowth"]
    b = ratio is not None and ratio >= d["ka_ratio_bar"]
    c = s["groups"]["any_work"]["decoy_share"] <= d["ka_decoy_any_bar"]
    return {
        "query": d["query_ka"],
        "variants": len(built["variants"]),
        "long": sum(v["long"] for v in built["variants"]),
        "searchable_readings": len(rd),
        "decoys": len(dec),
        "library_works": sc["works"],
        "unreadable_not_attempted": len(sc["unreadable"]),
        "scan_seconds": sc.get("seconds"),
        "top": [
            {k: w[k] for k in ("work_id", "year", "readings", "decoys", "class", "title")}
            for w in s["works"][:10]
        ],  # fmt: skip
        "lowth_printings": [
            {k: w[k] for k in ("work_id", "year", "readings", "decoys", "rank")} for w in lowth
        ],  # fmt: skip
        "best_lowth_ratio": round(ratio, 3) if ratio not in (None, float("inf")) else ratio,
        "groups": s["groups"],
        "bars": {"a_lowth_in_top": a, "b_ratio": b, "c_decoys_low": c},
        "passed": a and b and c,
    }


# ------------------------------------------------------------------------------------ run
def townsend(found: list[dict], readings: list[dict], s: dict, d: dict) -> list[dict]:
    items = json.loads(TOWNSEND.read_text())["items"]
    book_ch = {
        r["seq"]: (r["book"], r["chapter_1830"])
        for r in map(json.loads, LABELS.read_text().splitlines())
    }
    rid_of = {(r["ref"], " ".join(r["reading"])): r["rid"] for r in readings}
    rows = []
    for it in items:
        m = re.match(r"Isaiah (\d+):(\d+)(?:-(\d+))?", it["isaiah"])
        ch, v1, v2 = int(m[1]), int(m[2]), int(m[3] or m[2])
        refs = {f"{ch}:{v}" for v in range(v1, v2 + 1)}
        want = tuple(d["townsend_1830"][it["n"]])
        vs = [
            v
            for v in found
            if (v["ref"] in refs or v["also_ref"] in refs)
            and book_ch.get(int(v["query"].split(":")[1])) == want
        ]
        row = {"n": it["n"], "isaiah": it["isaiah"], "kind": it["kind"], "variants": len(vs),
               "searchable": 0, "in_clarke": 0, "in_lowth": 0, "in_commentary": 0,
               "in_any_work": 0, "detail": []}  # fmt: skip
        for v in vs:
            rid = (
                rid_of.get((v["ref"], " ".join(v.get("reading") or [])))
                if v.get("searchable") and not v["long"]
                else None
            )
            ws = s["per_reading"].get(rid, []) if rid is not None else []
            cls = {c for w in ws for c in s["klass"](w)}
            det = {"ref": v["ref"], "kind": v["kind"], "kjv": v["kjv"], "new": v["new"],
                   "long": v["long"], "searchable": rid is not None,
                   "why_not": v.get("why_not"), "works": len(ws),
                   "in_clarke": "clarke_isaiah" in cls, "in_lowth": "lowth" in cls,
                   "in_commentary": "commentary" in cls}  # fmt: skip
            row["detail"].append(det)
            row["searchable"] += rid is not None
            row["in_clarke"] += det["in_clarke"]
            row["in_lowth"] += det["in_lowth"]
            row["in_commentary"] += det["in_commentary"]
            row["in_any_work"] += bool(ws)
        rows.append(row)
    return rows


def italics(found: list[dict], kept: set[int], isa: Isaiah) -> dict:
    """Changed and dropped King James words that were italic, against the italic share of the
    words the Book of Mormon quotes (eBible 1769 brackets; not checked against an 1820s print)."""
    ch = [x for v in found if v["kind"] != "added" for x in v["kjv_italic"]]
    base = [isa.italic[p] for p in kept]
    return {"changed_or_dropped_words": len(ch), "italic": sum(ch),
            "italic_share": round(sum(ch) / len(ch), 4) if ch else None,
            "kept_words": len(base), "kept_italic": sum(base),
            "kept_italic_share": round(sum(base) / len(base), 4) if base else None,
            "source": "eBible 1769 text_marked brackets (data/kjv/kjv.jsonl); not checked "
                      "against an 1820s printing"}  # fmt: skip


def variant_rows(found: list[dict]) -> list[dict]:
    keep = ("query", "ref", "also_ref", "kind", "kjv", "new", "kjv_italic", "long",
            "searchable", "why_not")  # fmt: skip
    rows = []
    for v in sorted(found, key=lambda v: (v["chapter"], v["verse"], v["query"], v["kjv_pos"])):
        r = {k: v.get(k) for k in keep}
        if v.get("searchable"):
            r["reading"] = " ".join(v["reading"])
            r["kjv_form"] = " ".join(v["kjv_form"])
        rows.append(r)
    return rows


def summary(found: list[dict]) -> dict:
    verses_q = {(v["chapter"], v["verse"]) for v in found}
    return {
        "variant_instances": len(found),
        "by_kind": dict(Counter(v["kind"] for v in found)),
        "long": sum(v["long"] for v in found),
        "searchable": sum(bool(v.get("searchable")) and not v["long"] for v in found),
        "not_searchable_reasons": dict(
            Counter(v.get("why_not") for v in found if not v["long"] and not v.get("searchable"))
        ),
        "isaiah_verses_with_a_variant": len(verses_q),
    }


def run(cfg: dict, isa: Isaiah, chk: dict) -> dict:
    d = cfg["lab"]["isaiah"]
    built = build(bom_queries(isa, d), isa, d)
    rd, dec, found = built["readings"], built["decoys"], built["variants"]
    quoted = {isa.where[p] for p in built["kept"]}
    res = {"variant_list": summary(found) | {"isaiah_verses_quoted": len(quoted)},
           "italics": italics(found, built["kept"], isa),
           "searchable_readings": len(rd), "decoys": len(dec)}  # fmt: skip
    rows = library(d)
    sc = scan(rows, patterns(rd, dec, d), isa.freq, d, "bom")
    s = score(sc, rd, dec, rows, d)
    N, M = len(rd), len(dec)
    clarke = stats_for(s["works"], d["clarke_isaiah"], N, M)
    first = s["works"][0] if s["works"] else None
    if clarke["fisher_p_greater"] is None or clarke["fisher_p_greater"] >= d["special_p"]:
        verdict = "Clarke at chance"
    elif (
        clarke["rank"] == 1
        and sum(w["readings"] >= clarke["readings"] for w in s["works"]) == 1
        and clarke["ratio"] not in (None,)
        and (clarke["ratio"] == "inf" or clarke["ratio"] >= d["special_ratio"])
    ):
        verdict = "Clarke stands out"
    else:
        verdict = "Clarke one of many"
    lowth_ids = [w["work_id"] for w in s["works"] if "lowth" in w["class"]]
    cap = d["list_cap"]
    per = []
    for r in rd:
        ws = sorted(s["per_reading"].get(r["rid"], []), key=lambda w: (s_year(rows, w), w))
        per.append({"rid": r["rid"], "ref": r["ref"], "kind": r["kind"], "kjv": r["kjv"],
                    "new": r["new"], "reading": " ".join(r["reading"]),
                    "queries": r["queries"], "works": len(ws),
                    "works_quoting_kjv_form": s["per_kjv"].get(r["rid"], 0),
                    "earliest_year": s_year(rows, ws[0]) if ws else None,
                    "in_clarke": d["clarke_isaiah"] in ws,
                    "in_lowth": any(w in lowth_ids for w in ws),
                    "in_commentary": any("commentary" in s["klass"](w) for w in ws),
                    "work_ids": [[w, s_year(rows, w)] for w in ws[:cap]]})  # fmt: skip
    res.update({
        "library_works": sc["works"],
        "unreadable_not_attempted": len(sc["unreadable"]),
        "unreadable_ids": sc["unreadable"][:200],
        "scan_seconds": sc.get("seconds"),
        "groups": s["groups"],
        "clarke": clarke,
        "clarke_kjv_forms_found": next((w["kjv_forms"] for w in s["works"]
                                        if w["work_id"] == d["clarke_isaiah"]), 0),
        "top_by_readings": [{k: w[k] for k in ("work_id", "year", "readings", "decoys",
                             "excess", "class", "title", "rank")} for w in s["works"][:30]],
        "top_by_excess": [{k: w[k] for k in ("work_id", "year", "readings", "decoys", "excess",
                           "class", "title")}
                          for w in sorted(s["works"], key=lambda w: -(w["excess"] or 0))[:30]],
        "first_work": first["work_id"] if first else None,
        "lowth_printings": [stats_for(s["works"], w, N, M) for w in lowth_ids],
        "commentaries": [{k: w[k] for k in ("work_id", "year", "readings", "decoys", "rank",
                          "title")} for w in s["works"] if "commentary" in w["class"]][:40],
        "townsend": townsend(found, rd, s, d),
        "readings": per,
        "verdict": verdict,
        "known_answer_passed": chk["passed"],
    })  # fmt: skip
    return res


def s_year(rows: list[dict], w: str) -> int | None:
    global _YEARS
    if not _YEARS:
        _YEARS = {r["work_id"]: r["year"] for r in rows}
    return _YEARS.get(w)


_YEARS: dict[str, int] = {}


# ------------------------------------------------------------------------------------ judge
def judge(cfg: dict, isa: Isaiah) -> dict:
    """Questions for ``lab/judge.py`` (simulated judging by an AI model), prepared, not run: for
    each searchable reading and each of the commentaries and translations that quote most of the
    verses, the work's words around its quotation of the verse, and whether they propose the Book
    of Mormon's reading in the same sense. Written to the private repository (it quotes text)."""
    d = cfg["lab"]["isaiah"]
    res = json.loads((OUT / "result.json").read_text())
    if "book_of_mormon" not in res:
        raise SystemExit("result.json has no scored readings (check missed or not run)")
    built = build(bom_queries(isa, d), isa, d)
    rd = built["readings"]
    rows = library(d)
    by = {r["work_id"]: r for r in rows}
    sc = scan(rows, patterns(rd, built["decoys"], d), isa.freq, d, "bom")
    s = score(sc, rd, built["decoys"], rows, d)
    cand = [w for w in s["works"] if {"commentary", "translation", "lowth",
                                       "clarke_isaiah"} & set(w["class"])]  # fmt: skip
    cand.sort(key=lambda w: (w["work_id"] != d["clarke_isaiah"], -w["kjv_forms"]))
    chosen = cand[: d["judge_top_works"]]
    _init(patterns(rd, [], d), {w: isa.freq[w] for r in rd for w in r["reading"] + r["kjv_form"]})
    jobs = []
    for w in chosen:
        toks = tokens(door.text_of(by[w["work_id"]]))
        hit = match(toks)
        for n, pos in hit.items():
            pid = _P["items"][n][0]
            rid = int(pid[1:])
            if pid[0] == "k" and f"r{rid}" in {_P["items"][m][0] for m in hit}:
                continue  # the reading itself was found: one question, about the reading
            r = rd[rid]
            win = " ".join(toks[max(0, pos - d["judge_window"]) : pos + d["judge_window"]])
            jobs.append({
                "id": f"{w['work_id']}|{rid}",
                "prompt": (
                    "Simulated judging by an AI model (lab test BOM-122). Isaiah "
                    f"{r['ref']} in the King James Bible reads '{' '.join(r['kjv_form'])}'. "
                    f"The 1830 Book of Mormon reads '{' '.join(r['reading'])}' (King James "
                    f"'{r['kjv']}' -> '{r['new']}', {r['kind']}). Below are words from a work "
                    "printed before 1830 around its quotation of that verse (lower-cased, "
                    "punctuation removed). Does the passage propose, print or explain the Book "
                    "of Mormon's reading, in the same sense, as a reading of this verse? Answer "
                    "on the first line YES, NO or UNCLEAR, then one sentence.\n\n" + win
                ),
            })  # fmt: skip
    path = CARD / "judge_jobs.jsonl"
    out(path).write_text("".join(json.dumps(j) + "\n" for j in jobs))
    return {"jobs": len(jobs), "works": [w["work_id"] for w in chosen], "path": str(path)}


# ------------------------------------------------------------------------------------ driver
def settings_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg["lab"]["isaiah"], sort_keys=True).encode()).hexdigest()


def stamp(res: dict, cfg: dict) -> dict:
    res["settings_sha256"] = settings_hash(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["variants", "check", "run", "judge"])
    a = ap.parse_args(argv)
    cfg = config.load()
    d = cfg["lab"]["isaiah"]
    isa = Isaiah()
    if a.cmd == "variants":
        built = build(bom_queries(isa, d), isa, d)
        res = {"summary": summary(built["variants"]),
               "italics": italics(built["variants"], built["kept"], isa),
               "isaiah_verses_quoted": len({isa.where[p] for p in built["kept"]}),
               "searchable_readings": len(built["readings"]), "decoys": len(built["decoys"]),
               "variants": variant_rows(built["variants"])}  # fmt: skip
        out(OUT / "variants.json").write_text(json.dumps(stamp(res, cfg), indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "variants"}, indent=1))
        return 0
    if a.cmd == "judge":
        print(json.dumps(judge(cfg, isa), indent=1))
        return 0
    path = OUT / "check.json"
    chk = None
    if a.cmd == "run" and path.exists():
        old = json.loads(path.read_text())
        if old.get("settings_sha256") == settings_hash(cfg):
            chk = old["known_answer"]
            print("known-answer check reused from check.json (same settings)", flush=True)
    if chk is None:
        chk = check(cfg, isa)
        out(path).write_text(json.dumps(stamp({"known_answer": chk}, cfg), indent=1) + "\n")
    shown = ("searchable_readings", "decoys", "lowth_printings", "best_lowth_ratio", "bars",
             "passed")  # fmt: skip
    print(json.dumps({k: chk[k] for k in shown}, indent=1))
    if a.cmd == "check":
        return 0
    res = {"settings": d, "known_answer": chk}
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
    else:
        res["book_of_mormon"] = run(cfg, isa, chk)
        b = res["book_of_mormon"]
        print(json.dumps({"verdict": b["verdict"], "clarke": b["clarke"], "groups": b["groups"],
                          "top": b["top_by_readings"][:8]}, indent=1))  # fmt: skip
    out(OUT / "result.json").write_text(json.dumps(stamp(res, cfg), indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
