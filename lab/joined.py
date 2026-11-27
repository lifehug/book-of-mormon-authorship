"""BOM-128: King James phrases the Book of Mormon joins, dated by first appearance in print.

Where the 1830 text puts two King James phrases side by side that the Bible keeps apart ("eat,
drink, and be merry" from Luke 12:19 with "for to morrow we die" from 1 Corinthians 15:32, in
2 Nephi 28), was the joined form already in print before 1830, and from when? Step 1 finds the
joins in a text: runs of rare King James word 4- and 5-grams (rare as in BOM-124: in at most a set
share of a 400-work background sample) that share a verse, at least 4 words long, two of them
within 25 words of each other, from different verses, and never within 25 words of each other
anywhere in the King James Bible (Old and New Testaments). Step 2 reads every library work of
1640-1829 (kept copies, corrected years, sealed copies out) and records which works hold both
phrases of a join within 25 words; a join is *current by decade D* once two works hold it by D,
the book's own copies left out. The same steps run on 60 religious books of the 1650s, 1740s and
1820s (the known-answer check) and on decoys (*The Late War*, *View of the Hebrews*, a 1650s book
reprinted in the 1820s). No model, no AI judging. The test card, written first, is
``data/private/lab/owner/2026-11-27-joined-phrases/card.md``; settings are ``lab.joined_phrases``
in the config. Results hold ids, years, counts and King James phrases (public domain); the prose
of the planted check stays in the private folder.

Usage::

    python -m lab.joined tune       # design 2: choose the cutoff on a tuning draw -> tune_v2.json
    python -m lab.joined check      # check (a) planted joins, then (b) the 60 books (library pass)
    python -m lab.joined run        # the check, then the Book of Mormon (second library pass)
    python -m lab.joined seed       # step 1 only: the joins in 1830 2 Nephi XII, one by one
    python -m lab.joined table      # counting only: the listed 2 Nephi 28 pairs by decade
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import random
import re
import statistics
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from lab import door, ntwording, registry
from lab.paths import FAST, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "joined_phrases"
WORK = FAST / "joined_phrases"
CARD = NOTES / "owner" / "2026-11-27-joined-phrases"
KJV = Path("data/kjv/kjv.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
WORD = re.compile(r"[a-z]+")
BREAK = 100  # words between pieces of a stream, more than any window, so nothing spans them


def settings(cfg: dict) -> dict:
    """The settings in force: design 3's values over design 2's over the first design's."""
    base = cfg["lab"]["joined_phrases"]
    keep = {k: v for k, v in base.items() if k not in ("design2", "design3")}
    keep = {k: v for k, v in keep.items() if k != "design4"}
    return keep | base.get("design2", {}) | base.get("design3", {}) | base.get("design4", {})


def tokens(text: str) -> list[str]:
    return WORD.findall(text.lower())


# ------------------------------------------------------------------------ the King James side


class Bible:
    """The Old and New Testaments as one stream of words (a break between books), each position
    with its verse; every 4-gram's positions; and every 4- and 5-gram's verses."""

    def __init__(self, rows: list[dict], sizes: list[int]):
        self.words: list[str] = []
        self.verse_at: list[int] = []
        self.refs: list[str] = []
        book = None
        for r in rows:
            if r["section"] == "Apocrypha":
                continue
            if r["book"] != book:
                if book is not None:
                    self.words += [""] * BREAK
                    self.verse_at += [-1] * BREAK
                book = r["book"]
            v = len(self.refs)
            self.refs.append(r["ref"])
            t = tokens(r["text"])
            self.words += t
            self.verse_at += [v] * len(t)
        self.verse_words: dict[int, list[str]] = defaultdict(list)
        for w, v in zip(self.words, self.verse_at, strict=True):
            if v >= 0:
                self.verse_words[v].append(w)
        self.grams: dict[tuple, set[int]] = {}  # n-gram inside one verse -> verses holding it
        for v, ws in self.verse_words.items():
            for n in sizes:
                for i in range(len(ws) - n + 1):
                    self.grams.setdefault(tuple(ws[i : i + n]), set()).add(v)
        self.first4: dict[tuple, list[int]] = defaultdict(list)
        w = self.words
        for i in range(len(w) - 3):
            if w[i] and w[i + 3]:
                self.first4[(w[i], w[i + 1], w[i + 2], w[i + 3])].append(i)
        self._occ: dict[tuple, list[int]] = {}

    def occurrences(self, phrase: tuple) -> list[int]:
        """Start positions of ``phrase`` in the stream (memoised)."""
        if phrase not in self._occ:
            n = len(phrase)
            self._occ[phrase] = [
                p for p in self.first4.get(phrase[:4], []) if tuple(self.words[p : p + n]) == phrase
            ]
        return self._occ[phrase]

    def verses(self, phrase: tuple) -> set[int]:
        return {self.verse_at[p] for p in self.occurrences(phrase)}


def distance(a: int, la: int, b: int, lb: int) -> int:
    """Words between two spans (0 when they touch or overlap)."""
    return max(0, b - (a + la), a - (b + lb))


def near(pa: list[int], la: int, pb: list[int], lb: int, window: int) -> bool:
    """Is some occurrence of one span within ``window`` words of some occurrence of the other?"""
    if not pa or not pb:
        return False
    pb = sorted(pb)
    for a in pa:
        lo = bisect.bisect_left(pb, a - lb - window)
        hi = bisect.bisect_right(pb, a + la + window)
        if lo < hi:
            for b in pb[lo:hi]:
                if distance(a, la, b, lb) <= window:
                    return True
    return False


def rare_grams(bible: Bible, cfg: dict) -> dict[tuple, set[int]]:
    """The King James n-grams found in at most BOM-124's share of its background works."""
    w = cfg["lab"]["new_testament_wording"]
    rows = ntwording.draw(
        ntwording.eligible(
            cfg,
            lambda r: (
                w["bg_year_min"] <= r["year"] <= w["bg_year_max"]
                and (r["words"] or 0) >= w["bg_min_words"]
            ),
        ),
        w["bg_sample"],
        w["bg_seed"],
        set(),
    )
    df: dict[tuple, int] = defaultdict(int)
    read = 0
    sizes = sorted({len(g) for g in bible.grams})
    for r in rows:
        t = ntwording.read_words(r, w["max_words_per_work"])
        if t is None:
            continue  # unreadable: not attempted
        read += 1
        seen = set()
        for n in sizes:
            for g in zip(*(t[i:] for i in range(n)), strict=False):
                if g in bible.grams:
                    seen.add(g)
        for g in seen:
            df[g] += 1
    cut = w["bg_max_share"] * max(read, 1)
    return {g: v for g, v in bible.grams.items() if df.get(g, 0) <= cut}


# ------------------------------------------------------------------------ step 1: joins


def phrases_in(words: list[str], rare: dict[tuple, set[int]], sizes: list[int], min_words: int):
    """Runs of rare King James n-grams that overlap and share a verse: (start, end, words)."""
    items = []
    for n in sizes:
        for i, g in enumerate(zip(*(words[k:] for k in range(n)), strict=False)):
            v = rare.get(g)
            if v is not None:
                items.append((i, i + n, v))
    items.sort(key=lambda x: (x[0], -x[1]))
    runs: list[list] = []
    for s, e, v in items:
        if runs and s < runs[-1][1]:
            common = runs[-1][2] & v
            if common:
                runs[-1][1] = max(runs[-1][1], e)
                runs[-1][2] = common
                continue
            if e <= runs[-1][1]:
                continue  # inside the current run but from another verse: not a new phrase
        runs.append([s, e, set(v)])
    return [(s, e, tuple(words[s:e])) for s, e, _v in runs if e - s >= min_words]


def joins_in(words: list[str], bible: Bible, rare: dict, d: dict) -> list[dict]:
    """The joins of one text: pairs of phrases within the window, from different verses, that
    the King James Bible never has within the window. Deduplicated by the pair of phrases."""
    window, sizes = d["window"], d["ngram_sizes"]
    ph = phrases_in(words, rare, sizes, d["min_phrase_words"])
    found: dict[tuple, dict] = {}
    for i, (sa, ea, a) in enumerate(ph):
        for sb, eb, b in ph[i + 1 :]:
            if sb - ea > window:
                break
            if sb < ea or a == b:
                continue
            key = tuple(sorted((a, b)))
            if key in found:
                found[key]["times"] += 1
                continue
            va, vb = bible.verses(a), bible.verses(b)
            if not va or not vb or va & vb:
                continue
            if near(bible.occurrences(a), len(a), bible.occurrences(b), len(b), window):
                continue
            found[key] = {"a": key[0], "b": key[1], "at": sa, "end": eb, "times": 1}
    return list(found.values())


def join_key(a: tuple, b: tuple) -> str:
    return " ".join(a) + " | " + " ".join(b)


# ------------------------------------------------------------------------ the library


def author_key(author: str | None) -> str:
    """Surname and first given name, letters only ('' when anonymous)."""
    parts = [re.sub(r"[^a-z ]", "", p.lower()).strip() for p in (author or "").split(",")]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return " ".join([parts[0]] + ([parts[1].split()[0]] if len(parts) > 1 else []))


def title_key(title: str | None, n: int) -> str:
    w = tokens(title or "")
    while w and w[0] in ("the", "a", "an"):
        w = w[1:]
    return " ".join(w[:n])


def same_title(a: str, b: str) -> bool:
    """Two title openings agree on their common length, of at least three words."""
    x, y = a.split(), b.split()
    k = min(len(x), len(y))
    return k >= 3 and x[:k] == y[:k]


def library_rows(d: dict) -> list[dict]:
    """The card's ``default`` set: works with text, kept copies, OCR not excluded, sealed copies
    out, corrected year in range; each with its catalog fields and duplicate group."""
    import pyarrow.parquet as pq

    from metadata.pseudo_biblical import DUPES

    t = pq.read_table(DUPES, columns=["work_id", "group_id"]).to_pydict()
    groups = dict(zip(t["work_id"], t["group_id"], strict=True))
    reg = [
        r
        for r in registry.load().to_pylist()
        if r["kind"] == "work"
        and r["has_text"]
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and d["year_min"] <= r["year"] <= d["year_max"]
    ]
    cat = door.catalog({r["work_id"] for r in reg})
    rows = []
    for r in reg:
        c = cat.get(r["work_id"])
        if c and c["text_path"]:
            rows.append({**c, **r, "group": groups.get(r["work_id"])})
    return rows


def own_copies(book: dict, rows: list[dict], d: dict) -> set[str]:
    """Work ids that are the book itself or a copy or edition of it: its duplicate group, and
    works with the same author key and title opening (anonymous: title opening alone), or
    matching the book's stated author / title patterns (decoys)."""
    n = d["title_key_words"]
    ak, tk = author_key(book.get("author")), title_key(book.get("title"), n)
    pa = re.compile(book["exclude_author"], re.I) if book.get("exclude_author") else None
    pt = re.compile(book["exclude_title"], re.I) if book.get("exclude_title") else None
    got = {book["work_id"]} if book.get("work_id") else set()
    for r in rows:
        if book.get("group") is not None and r["group"] == book["group"]:
            got.add(r["work_id"])
        elif tk and same_title(title_key(r["title"], n), tk) and author_key(r["author"]) == ak:
            got.add(r["work_id"])
        elif pa and pa.search(r["author"] or "") and (not pt or pt.search(r["title"] or "")):
            got.add(r["work_id"])
        elif pt and not pa and pt.search(" ".join((r["title"] or "").split())):
            got.add(r["work_id"])
    return got


_PH: dict = {}
_JOINS: list = []
_WINDOW = 25
_LENS: dict = {}


def _init(phrases: dict, joins: list, window: int) -> None:
    global _PH, _JOINS, _WINDOW, _LENS
    _PH, _JOINS, _WINDOW = phrases, joins, window
    _LENS = {pid: len(p) for ps in phrases.values() for pid, p in ps}


def holds(words: list[str], phrases: dict, joins: list, window: int,
          lens: dict | None = None) -> list[int]:  # fmt: skip
    """Indices of the joins whose two phrases sit within the window somewhere in ``words``.
    ``phrases``: first 4-gram -> [(phrase id, phrase)]; ``joins``: [(id of a, id of b)]."""
    pos: dict[int, list[int]] = defaultdict(list)
    for i, g in enumerate(zip(words, words[1:], words[2:], words[3:], strict=False)):
        for pid, p in phrases.get(g, ()):
            if len(p) == 4 or tuple(words[i : i + len(p)]) == p:
                pos[pid].append(i)
    if len(pos) < 2:
        return []
    if lens is None:
        lens = {pid: len(p) for ps in phrases.values() for pid, p in ps}
    return [
        k
        for k, (a, b) in enumerate(joins)
        if a in pos and b in pos and near(pos[a], lens[a], pos[b], lens[b], window)
    ]


def _scan(row: dict) -> tuple[str, list[int] | None]:
    try:
        words = tokens(door.text_of(row))
    except OSError:
        return row["work_id"], None  # unreadable: not attempted, never a zero
    return row["work_id"], holds(words, _PH, _JOINS, _WINDOW, _LENS)


def phrase_table(joins: list[tuple[tuple, tuple]]) -> tuple[dict, list[tuple[int, int]]]:
    ids: dict[tuple, int] = {}
    for a, b in joins:
        for p in (a, b):
            ids.setdefault(p, len(ids))
    table: dict[tuple, list] = defaultdict(list)
    for p, i in ids.items():
        table[p[:4]].append((i, p))
    return dict(table), [(ids[a], ids[b]) for a, b in joins]


def library_pass(name: str, joins: list[tuple[tuple, tuple]], rows: list[dict], d: dict) -> dict:
    """work id -> [join index] for every library work, in resumable parts on local disk."""
    keys = sorted(join_key(a, b) for a, b in joins)
    digest = hashlib.sha256(json.dumps([keys, d["window"], len(rows)]).encode()).hexdigest()[:12]
    folder = WORK / f"{name}_{digest}"
    order = {join_key(a, b): k for k, (a, b) in enumerate(joins)}
    srt = [joins[order[k]] for k in keys]
    phrases, pairs = phrase_table(srt)
    rows = sorted(rows, key=lambda r: r["work_id"])
    parts = [rows[i : i + d["part_size"]] for i in range(0, len(rows), d["part_size"])]
    t0 = time.time()
    print(f"library pass {name}: {len(joins):,} joins, {len(rows):,} works, {len(parts)} parts")
    with ProcessPoolExecutor(d["workers"], initializer=_init,
                             initargs=(phrases, pairs, d["window"])) as pool:  # fmt: skip
        for k, part in enumerate(parts):
            f = folder / f"part_{k:04d}.jsonl"
            if f.exists():
                continue
            lines = []
            for wid, got in pool.map(_scan, part, chunksize=16):
                if got is None:
                    lines.append(json.dumps({"work_id": wid, "state": "unreadable"}))
                elif got:
                    lines.append(json.dumps({"work_id": wid, "joins": [keys[j] for j in got]}))
            tmp = out(folder / f".part_{k:04d}.tmp")
            tmp.write_text("".join(x + "\n" for x in lines))
            tmp.rename(f)
            print(f"  part {k + 1}/{len(parts)} ({time.time() - t0:.0f} s)", flush=True)
    held: dict[str, list[str]] = {}
    unreadable = []
    for f in sorted(folder.glob("part_*.jsonl")):
        for line in f.read_text().splitlines():
            r = json.loads(line)
            if r.get("state") == "unreadable":
                unreadable.append(r["work_id"])
            else:
                held[r["work_id"]] = r["joins"]
    return {"held": held, "unreadable": unreadable, "folder": str(folder), "works": len(rows)}


# ------------------------------------------------------------------------ dating


def holders_by_join(held: dict[str, list[str]]) -> dict[str, list[str]]:
    by: dict[str, list[str]] = defaultdict(list)
    for wid, ks in held.items():
        for k in ks:
            by[k].append(wid)
    return by


def first_current(years: list[int], need: int) -> int | None:
    """The decade by which ``need`` works hold the join (None: never by the library's end)."""
    ys = sorted(years)
    return ys[need - 1] // 10 * 10 if len(ys) >= need else None


def date_join(key: str, holders: list[str], skip: set[str], meta: dict, d: dict) -> dict:
    ws = [w for w in holders if w not in skip]
    years = [meta[w]["year"] for w in ws]
    by_author: dict[str, int] = {}
    for w in ws:  # sensitivity: one vote per author (anonymous works by title opening)
        m = meta[w]
        a = author_key(m["author"]) or "title:" + title_key(m["title"], d["title_key_words"])
        by_author[a] = min(by_author.get(a, 9999), m["year"])
    dec: dict[str, int] = defaultdict(int)
    for y in years:
        dec[str(y // 10 * 10)] += 1
    return {
        "join": key,
        "works": len(ws),
        "works_by_decade": dict(sorted(dec.items())),
        "first_current": first_current(years, d["independent_works"]),
        "first_current_distinct_authors": first_current(
            list(by_author.values()), d["independent_works"]
        ),
    }


DECADES = list(range(1640, 1830, 10))


def decade_totals(rows: list[dict]) -> dict[int, int]:
    tot: dict[int, int] = defaultdict(int)
    for r in rows:
        tot[r["year"] // 10 * 10] += 1
    return dict(tot)


def onset(counts: dict[int, float], totals: dict[int, float], d: dict) -> tuple:
    """Design 4: holders per 1,000 works in each decade; the onset is the first decade whose
    rate reaches ``onset_share`` of the join's peak rate. None when fewer than
    ``independent_works`` works hold the join in all."""
    rates = {x: 1000 * counts.get(x, 0) / totals[x] for x in DECADES if totals.get(x)}
    if sum(counts.values()) < d["independent_works"] or not any(rates.values()):
        return None, None, rates
    peak = max(rates, key=lambda x: (rates[x], -x))
    first = next(x for x in DECADES if rates.get(x, 0) >= d["onset_share"] * rates[peak])
    return first, peak, rates


def rate_dating(holders: list[str], skip: set[str], meta: dict, totals: dict, d: dict,
                samples: dict | None) -> dict:  # fmt: skip
    """Onset by rate over the whole library, by distinct authors, and over equal samples."""
    ws = [w for w in holders if w not in skip and w in meta]
    own: dict[int, int] = defaultdict(int)
    for w in skip:
        if w in meta:
            own[meta[w]["year"] // 10 * 10] += 1
    tot = {x: totals[x] - own.get(x, 0) for x in totals}
    c: dict[int, int] = defaultdict(int)
    authors: dict[int, set] = defaultdict(set)
    for w in ws:
        m = meta[w]
        x = m["year"] // 10 * 10
        c[x] += 1
        authors[x].add(author_key(m["author"]) or "title:" + title_key(m["title"], 4))
    first, peak, rates = onset(c, tot, d)
    first_a, _p, _r = onset({x: len(v) for x, v in authors.items()}, tot, d)
    res = {"onset": first, "peak": peak, "onset_authors": first_a,
           "per_1000": {str(x): round(v, 4) for x, v in rates.items() if v}}  # fmt: skip
    if samples is not None:
        avg: dict[int, float] = defaultdict(float)
        for s in samples["draws"]:
            for w in ws:
                if w in s:
                    avg[meta[w]["year"] // 10 * 10] += 1 / len(samples["draws"])
        n = samples["per_decade"]
        res["onset_equal_samples"], _p, _r = onset(avg, {x: n for x in DECADES}, d)
    return res


def decade_samples(rows: list[dict], d: dict) -> dict:
    """Design 3: ``draws`` seeded samples with the same number of works from every decade (the
    thinnest decade's count, or periods merged to reach ``min_per_decade``)."""
    by: dict[int, list[str]] = defaultdict(list)
    for r in rows:
        by[r["year"] // 10 * 10].append(r["work_id"])
    decs = sorted(by)
    n = min(len(by[x]) for x in decs)
    if d.get("per_decade"):
        n = min(n, d["per_decade"])
    if n < d["min_per_decade"]:
        raise SystemExit(f"thinnest decade has {n} works, under {d['min_per_decade']}: merge "
                         "decades into periods (not built)")  # fmt: skip
    draws = []
    for k in range(d["draws"]):
        rng = random.Random(d["sample_seed"] + k)
        s: set[str] = set()
        for x in decs:
            s.update(rng.sample(sorted(by[x]), n))
        draws.append(s)
    return {"per_decade": n, "decades": {str(x): len(by[x]) for x in decs}, "draws": draws}


def sampled_first(holders: list[str], skip: set[str], meta: dict, draws: list[set], d: dict,
                  authors: bool = False) -> tuple[int | None, float]:  # fmt: skip
    """The first decade by which the join is current (``independent_works`` sampled holders,
    own copies left out) in more than ``majority`` of the draws; and the share of draws in which
    it is current at all by 1829."""
    firsts = []
    for s in draws:
        ws = [w for w in holders if w in s and w not in skip]
        if authors:
            by_a: dict[str, int] = {}
            for w in ws:
                m = meta[w]
                a = author_key(m["author"]) or "title:" + title_key(
                    m["title"], d["title_key_words"]
                )
                by_a[a] = min(by_a.get(a, 9999), m["year"])
            ys = list(by_a.values())
        else:
            ys = [meta[w]["year"] for w in ws]
        firsts.append(first_current(ys, d["independent_works"]))
    got = [f for f in firsts if f is not None]
    for dec in range(d["year_min"] // 10 * 10, d["year_max"] + 1, 10):
        if sum(f <= dec for f in got) > d["majority"] * len(draws):
            return dec, round(len(got) / len(draws), 3)
    return None, round(len(got) / len(draws), 3)


def book_shares(dated: list[dict], own_decade: int | None, d: dict, field: str) -> dict:
    cur = [j[field] for j in dated if j[field] is not None]
    res = {"joins": len(dated), "current": len(cur)}
    if not cur:
        return res | {"share_late": None, "share_by_own_decade": None}
    res["share_late"] = round(sum(c >= d["late_from"] for c in cur) / len(cur), 4)
    if own_decade is not None:
        res["share_by_own_decade"] = round(sum(c <= own_decade for c in cur) / len(cur), 4)
    res["usable"] = len(cur) >= d["min_current_joins"]
    return res


def percentile(xs: list[float], p: float) -> float | None:
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def verdict(share: float | None, early: list[float], late: list[float], d: dict) -> str:
    """Late / old / cannot tell, by the card's rule on the share first current after 1750."""
    if share is None or not early or not late:
        return "cannot tell"
    if share > percentile(early, d["late_percentile"]) and share >= statistics.median(late):
        return "late"
    if share <= percentile(early, d["old_percentile"]):
        return "old"
    return "cannot tell"


# ------------------------------------------------------------------------ the check


def prose_passages(cfg: dict, seed: int, exclude: set[str],
                   rng: random.Random | None = None) -> list[tuple[str, list[str]]]:  # fmt: skip
    """2 x ``planted`` passages of non-religious period prose (``known-answer`` works), seeded."""
    d = settings(cfg)
    rng = rng or random.Random(seed)
    ka = registry.view("known-answer", cfg).to_pylist()
    pool = [
        r
        for r in ka
        if r["work_id"] not in exclude
        and r["kind"] == "work"
        and r["year"]
        and d["prose_years"][0] <= r["year"] <= d["prose_years"][1]
        and set((r["genre"] or "").split(",")) & set(d["prose_genres"])
        and "sermon_devotional" not in (r["genre"] or "")
        and (r["words"] or 0) >= d["prose_min_words"]
        and not r["sealed"]
        and not r["ocr_excluded"]
    ]
    rng.shuffle(pool)
    cat = door.catalog({r["work_id"] for r in pool[: d["planted"] * 4]})
    passages: list[tuple[str, list[str]]] = []
    for r in pool[: d["planted"] * 4]:
        c = cat.get(r["work_id"])
        if not c or not c["text_path"]:
            continue
        try:
            w = tokens(door.text_of({**c, **r}))
        except OSError:
            continue
        if len(w) < 3 * d["prose_words"]:
            continue
        s = rng.randrange(len(w) // 3, len(w) - d["prose_words"])
        passages.append((r["work_id"], w[s : s + d["prose_words"]]))
        if len(passages) == 2 * d["planted"]:
            break
    return passages


def planted_check(bible: Bible, rare: dict, cfg: dict, seed: int | None = None,
                  passages: list | None = None) -> dict:  # fmt: skip
    """(a) Random King James phrase pairs put into period prose; other prose for false joins.
    The phrases are drawn from those the finder looks for (every 4-gram in ``rare``)."""
    d = settings(cfg)
    seed = d["seed"] if seed is None else seed
    if passages is None:  # the first design: passages and phrases from one random stream
        rng = random.Random(seed)
        passages = prose_passages(cfg, seed, set(), rng)
    else:
        rng = random.Random(seed + 7)
    vids = list(bible.verse_words)

    def phrase() -> tuple:
        while True:
            ws = bible.verse_words[rng.choice(vids)]
            n = rng.randint(*d["planted_len"])
            if len(ws) < n:
                continue
            s = rng.randrange(len(ws) - n + 1)
            p = tuple(ws[s : s + n])
            if all(g in rare for g in zip(p, p[1:], p[2:], p[3:], strict=False)):
                return p

    hits, rows = 0, []
    planted = passages[: d["planted"]]
    for wid, prose in planted:
        while True:
            a, b = phrase(), phrase()
            if bible.verses(a) & bible.verses(b):
                continue
            if not near(bible.occurrences(a), len(a), bible.occurrences(b), len(b), d["window"]):
                break
        gap = rng.randint(0, d["window"])
        at = rng.randrange(0, len(prose) - gap)
        text = prose[:at] + list(a) + prose[at : at + gap] + list(b) + prose[at + gap :]
        sa, sb = at, at + len(a) + gap
        found = joins_in(text, bible, rare, d)
        ok = any(j["at"] < sa + len(a) and j["end"] > sb for j in found)
        hits += ok
        rows.append({"work_id": wid, "a": " ".join(a), "b": " ".join(b), "gap": gap,
                     "found": ok, "joins_found": len(found)})  # fmt: skip
    false = []
    for wid, prose in passages[d["planted"] :]:
        found = joins_in(prose, bible, rare, d)
        false.append({"work_id": wid, "joins_found": len(found),
                      "joins": [join_key(j["a"], j["b"]) for j in found]})  # fmt: skip
    n_false = sum(1 for f in false if f["joins_found"])
    recall = hits / len(planted) if planted else 0.0
    fp = n_false / len(false) if false else 1.0
    return {
        "planted": len(planted),
        "found": hits,
        "recall": round(recall, 4),
        "unplanted": len(false),
        "unplanted_with_a_join": n_false,
        "false_share": round(fp, 4),
        "bars": {"recall": d["recall_bar"], "false_share": d["false_bar"]},
        "passed": recall >= d["recall_bar"] and fp <= d["false_bar"],
        "planted_rows": rows,
        "unplanted_rows": false,
    }


def check_books(rows: list[dict], d: dict) -> list[dict]:
    rng = random.Random(d["seed"] + 1)
    picked = []
    for dec in d["check_decades"]:
        pool = [
            r
            for r in rows
            if r["year"] // 10 * 10 == dec
            and d["check_genre"] in (r["genre"] or "").split(",")
            and (r["words"] or 0) >= d["check_min_words"]
        ]
        pool.sort(key=lambda r: r["work_id"])
        rng.shuffle(pool)
        picked += [{**r, "check_decade": dec} for r in pool[: d["check_books"]]]
    return picked


def book_joins(name: str, words: list[str], bible: Bible, rare: dict, d: dict) -> list[dict]:
    t0 = time.time()
    j = joins_in(words, bible, rare, d)
    print(f"  {name}: {len(words):,} words, {len(j)} joins ({time.time() - t0:.0f} s)", flush=True)
    return j


def decoy_books(rows: list[dict], d: dict) -> list[dict]:
    by = {r["work_id"]: r for r in rows}
    res = []
    for name, spec in d["decoys"].items():
        b = {"name": name, **spec}
        if spec.get("work_id"):
            r = by.get(spec["work_id"])
            if r is None:
                continue
            b |= {k: r[k] for k in ("work_id", "author", "title", "group", "year", "text_path")}
            b |= {k: r[k] for k in r if k not in b}
        res.append(b)
    return res


def text_words(book: dict) -> list[str] | None:
    try:
        if book.get("file"):
            return tokens(Path(book["file"]).read_text(encoding="utf-8", errors="replace"))
        return tokens(door.text_of(book))
    except OSError:
        return None


def summarise(books: list[dict], meta: dict, by_join: dict, rows: list[dict], d: dict,
              samples=None) -> list:  # fmt: skip
    """Each book's joins dated. ``samples``: design 3's draws (a list of sets) or design 4's
    decade_samples result (a dict, the cross-check)."""
    res = []
    totals = decade_totals(rows)
    for b in books:
        skip = own_copies(b, rows, d)
        dated = [date_join(join_key(j["a"], j["b"]), by_join.get(join_key(j["a"], j["b"]), []),
                           skip, meta, d) for j in b["joins"]]  # fmt: skip
        if d.get("design") == 4:  # design 4: onset by rate per 1,000 works in each decade
            for x in dated:
                rd = rate_dating(by_join.get(x["join"], []), skip, meta, totals, d, samples)
                x["first_current_two_works"] = x["first_current"]
                x["first_current"] = rd["onset"]
                x["first_current_distinct_authors"] = rd["onset_authors"]
                x["onset_equal_samples"] = rd.get("onset_equal_samples")
                x["peak"], x["per_1000"] = rd["peak"], rd["per_1000"]
        elif samples is not None:  # design 3: dated against the equal-size decade samples
            for x in dated:
                hs = by_join.get(x["join"], [])
                x["first_current_full_library"] = x["first_current"]
                x["first_current_distinct_authors_full_library"] = x[
                    "first_current_distinct_authors"
                ]
                x["first_current"], x["draws_current"] = sampled_first(hs, skip, meta, samples, d)
                x["first_current_distinct_authors"], _ = sampled_first(
                    hs, skip, meta, samples, d, authors=True
                )
        own = b.get("check_decade")
        res.append({
            "name": b.get("name") or b["work_id"], "work_id": b.get("work_id"),
            "year": b.get("year"), "check_decade": own, "words": b["words_read"],
            "own_copies_left_out": len(skip),
            "shares": book_shares(dated, own, d, "first_current"),
            "shares_distinct_authors": book_shares(dated, own, d, "first_current_distinct_authors"),
            "shares_equal_samples": book_shares(dated, own, d, "onset_equal_samples")
            if d.get("design") == 4
            else None,
            "joins": dated,
        })  # fmt: skip
    return res


def group_check(books: list[dict], d: dict, field: str = "shares") -> dict:
    groups = {}
    for dec in d["check_decades"]:
        bs = [b for b in books if b["check_decade"] == dec]
        jf = {
            "shares": "first_current",
            "shares_distinct_authors": "first_current_distinct_authors",
            "shares_equal_samples": "onset_equal_samples",
        }[field]
        cur = [j.get(jf) for b in bs for j in b["joins"]]
        cur = [c for c in cur if c is not None]
        usable = [b[field] for b in bs if b[field].get("usable")]
        groups[str(dec)] = {
            "books": len(bs),
            "books_usable": len(usable),
            "joins": sum(b[field]["joins"] for b in bs),
            "current": len(cur),
            "pooled_share_by_own_decade": round(sum(c <= dec for c in cur) / len(cur), 4)
            if cur else None,
            "pooled_share_late": round(sum(c >= d["late_from"] for c in cur) / len(cur), 4)
            if cur else None,
            "median_book_share_by_own_decade": statistics.median(
                [u["share_by_own_decade"] for u in usable]) if usable else None,
            "median_book_share_late": statistics.median([u["share_late"] for u in usable])
            if usable else None,
            "book_shares_late": sorted(u["share_late"] for u in usable),
        }  # fmt: skip
    own_ok = all(
        g["pooled_share_by_own_decade"] is not None
        and g["pooled_share_by_own_decade"] >= d["own_decade_bar"]
        for g in groups.values()
    )
    first = groups[str(d["check_decades"][0])]["pooled_share_late"]
    early_ok = first is not None and first < d["early_late_bar"]
    return {"groups": groups, "own_decade_passed": own_ok, "early_late_passed": early_ok,
            "passed": own_ok and early_ok,
            "bars": {"own_decade": d["own_decade_bar"],
                     "early_late": d["early_late_bar"]}}  # fmt: skip


FUNCTION_WORDS = frozenset(
    "a an the and or but nor for so yet of in on at to by with from into unto upon over under "
    "out up down off about after before through against among between within without i me my "
    "mine we us our ye you your thou thee thy thine he him his she her it its they them their "
    "this that these those there here which who whom whose what when where whereby wherein "
    "is are was were be been being am art hast hath have has had do doth did done shall shalt "
    "will wilt would should could might may must can not no nay yea all any some every each "
    "as than then if also even more most such very own same other one let".split()
)


def nonreligious_sample(cfg: dict) -> list[dict]:
    """Design 2's fixed sample of non-religious period books (default set, seeded)."""
    d = settings(cfg)
    rows = [
        r
        for r in library_rows(d)
        if d["nonrel_years"][0] <= r["year"] <= d["nonrel_years"][1]
        and set((r["genre"] or "").split(",")) & set(d["nonrel_genres"])
        and "sermon_devotional" not in (r["genre"] or "")
        and "pseudo_biblical" not in (r["genre"] or "")
        and (r["words"] or 0) >= d["nonrel_min_words"]
    ]
    rows.sort(key=lambda r: r["work_id"])
    random.Random(d["nonrel_seed"]).shuffle(rows)
    return rows[: d["nonrel_sample"]]


def nonreligious_df(bible: Bible, cfg: dict) -> tuple[dict[tuple, int], int, list[str]]:
    """How many sample books hold each King James 4- and 5-gram; books read; their ids."""
    d = settings(cfg)
    df: dict[tuple, int] = defaultdict(int)
    read, ids = 0, []
    sizes = d["ngram_sizes"]
    for r in nonreligious_sample(cfg):
        try:
            t = tokens(door.text_of(r))[: d["max_words_per_work"]]
        except OSError:
            continue  # unreadable: not attempted
        read += 1
        ids.append(r["work_id"])
        seen = set()
        for n in sizes:
            for g in zip(*(t[i:] for i in range(n)), strict=False):
                if g in bible.grams:
                    seen.add(g)
        for g in seen:
            df[g] += 1
    return dict(df), read, ids


def distinctive(bible: Bible, df: dict, read: int, share: float, d: dict) -> dict:
    """King James n-grams in at most ``share`` of the non-religious books; with the function-word
    rule, an n-gram made only of function words and at most one other word is dropped too."""
    cut = share * read
    keep = {}
    for g, v in bible.grams.items():
        if df.get(g, 0) > cut:
            continue
        if d.get("function_rule") and sum(w not in FUNCTION_WORDS for w in g) <= 1:
            continue
        keep[g] = v
    return keep


def prepare(cfg: dict) -> dict:
    d = settings(cfg)
    t0 = time.time()
    bible = Bible([json.loads(x) for x in KJV.read_text().splitlines()], d["ngram_sizes"])
    p = {"d": d, "bible": bible, "exclude": set()}
    if d.get("design", 1) >= 2:
        df, read, ids = nonreligious_df(bible, cfg)
        p |= {"df": df, "read": read, "exclude": set(ids)}
        if d.get("share") is None:
            p["rare"] = None
            return p
        p["rare"] = distinctive(bible, df, read, d["share"], d)
    else:
        p["rare"] = rare_grams(bible, cfg)
    print(f"King James: {len(bible.grams):,} n-grams, {len(p['rare']):,} kept "
          f"({time.time() - t0:.0f} s)", flush=True)  # fmt: skip
    return p


def tune(cfg: dict) -> dict:
    """Design 2: the cutoff, chosen on a tuning draw of planted and unplanted passages."""
    d = settings(cfg)
    p = prepare(cfg)
    passages = prose_passages(cfg, d["tune_seed"], p["exclude"])
    rows = []
    for share in d["share_grid"]:
        for rule in (False, True):
            dd = d | {"function_rule": rule}
            kept = distinctive(p["bible"], p["df"], p["read"], share, dd)
            got = planted_check(p["bible"], kept, cfg, d["tune_seed"], passages)
            fj = sum(x["joins_found"] for x in got["unplanted_rows"])
            rows.append({"share": share, "function_rule": rule, "kept_ngrams": len(kept),
                         "recall": got["recall"], "false_share": got["false_share"],
                         "false_joins": fj})  # fmt: skip
            print(json.dumps(rows[-1]), flush=True)
    ok = [r for r in rows if r["false_share"] <= d["tune_false_target"]
          and r["recall"] >= d["recall_bar"]]  # fmt: skip
    # the most permissive passing cutoff; without the function-word rule when that passes too
    best = max(ok, key=lambda r: (r["share"], not r["function_rule"])) if ok else None
    return {"nonreligious_books_read": p["read"], "tuning_passages": len(passages),
            "tuning_works": [w for w, _ in passages], "grid": rows, "chosen": best,
            "rule": f"largest share with tuning false share <= {d['tune_false_target']} and "
                    f"recall >= {d['recall_bar']}; function-word rule only if needed"}  # fmt: skip


def run_check(cfg: dict, p: dict) -> dict:
    d, bible, rare = p["d"], p["bible"], p["rare"]
    if d.get("design", 1) >= 2:  # a fresh draw: none of the tuning works or the rarity sample
        tuned = {w for w, _ in prose_passages(cfg, d["tune_seed"], p["exclude"])}
        passages = prose_passages(cfg, d["check_seed"], p["exclude"] | tuned)
        res: dict = {"planted": planted_check(bible, rare, cfg, d["check_seed"], passages)}
    else:
        res = {"planted": planted_check(bible, rare, cfg)}
    print(json.dumps({k: v for k, v in res["planted"].items() if not k.endswith("_rows")}))
    if not res["planted"]["passed"]:
        res["passed"] = False
        res["stopped"] = "check (a) missed its bar: the 60 books and the Book of Mormon not dated"
        return res
    rows = library_rows(d)
    p["rows"] = rows
    books = check_books(rows, d) + decoy_books(rows, d)
    for b in books:
        w = text_words(b)
        b["words_read"] = len(w) if w else 0
        b["joins"] = [] if w is None else book_joins(b.get("name") or b["work_id"], w, bible,
                                                     rare, d)  # fmt: skip
        b["unreadable"] = w is None
    allj = {join_key(j["a"], j["b"]): (j["a"], j["b"]) for b in books for j in b["joins"]}
    lp = library_pass("check", list(allj.values()), rows, d)
    meta = {r["work_id"]: r for r in rows}
    by_join = holders_by_join(lp["held"])
    samples = None
    if d.get("design", 1) >= 3:
        ds = decade_samples(rows, d)
        p["samples"] = samples = ds if d["design"] == 4 else ds["draws"]
        res["decade_samples"] = {k: v for k, v in ds.items() if k != "draws"} | {
            "draws": len(ds["draws"]),
            "majority": d["majority"],
        }
    summ = summarise(books, meta, by_join, rows, d, samples)
    checks = [b for b in summ if b["check_decade"] is not None]
    res["books"] = group_check(checks, d)
    res["books_distinct_authors"] = group_check(checks, d, "shares_distinct_authors")
    if d.get("design") == 4:
        res["books_equal_samples"] = group_check(checks, d, "shares_equal_samples")
    res["passed"] = res["books"]["passed"]
    res["library"] = {"works": lp["works"], "unreadable_not_attempted": len(lp["unreadable"]),
                      "pass_folder": lp["folder"]}  # fmt: skip
    res["check_books"] = checks
    res["decoys_raw"] = [b for b in summ if b["check_decade"] is None]
    return res


def bom_words() -> list[str]:
    """The 1830 body text in order, chapters kept apart by a break."""
    words: list[str] = []
    last = None
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if r.get("kind") != "body":
            continue
        key = (r["book"], r["chapter"])
        if last is not None and key != last:
            words += [""] * BREAK
        last = key
        words += tokens(r["text"])
    return words


def chapter_spans() -> dict[tuple, tuple[int, int]]:
    spans: dict[tuple, list[int]] = {}
    pos, last = 0, None
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if r.get("kind") != "body":
            continue
        key = (r["book"], r["chapter"])
        if last is not None and key != last:
            pos += BREAK
        last = key
        n = len(tokens(r["text"]))
        spans.setdefault(key, [pos, pos])[1] = pos + n
        pos += n
    return {k: (a, b) for k, (a, b) in spans.items()}


def refs(bible: Bible, phrase: tuple) -> list[str]:
    return sorted({bible.refs[v] for v in bible.verses(phrase)})


def run(cfg: dict) -> dict:
    p = prepare(cfg)
    d = p["d"]
    res: dict = {"card": str(CARD / "card.md"), "settings": d, **config.stamp()}
    chk = run_check(cfg, p)
    cb = [b for b in chk.get("check_books", []) if b["shares"].get("usable")]
    early = [b["shares"]["share_late"] for b in cb if b["check_decade"] in d["early_decades"]]
    late = [b["shares"]["share_late"] for b in cb if b["check_decade"] == d["check_decades"][-1]]
    for b in chk.get("decoys_raw", []):
        b["verdict"] = verdict(b["shares"].get("share_late"), early, late, d)
    if d.get("design", 1) >= 3 and "decoys_raw" in chk:  # design 3's two decoy bars
        v = {b["name"]: b["verdict"] for b in chk["decoys_raw"]}
        bars = {
            "reprint_dates_old": v.get(d["reprint_decoy"]) == "old",
            "late_war_not_old": v.get(d["late_decoy"]) not in (None, "old"),
        }
        chk["decoy_bars"] = bars
        chk["passed"] = chk["passed"] and all(bars.values())
    res["known_answer"] = chk
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not dated"
        return res
    bible, rare, rows = p["bible"], p["rare"], p["rows"]
    words = bom_words()
    joins = book_joins("Book of Mormon 1830", words, bible, rare, d)
    lp = library_pass("bom", [(j["a"], j["b"]) for j in joins], rows, d)
    meta = {r["work_id"]: r for r in rows}
    book = {"name": "Book of Mormon 1830", "work_id": None, "year": 1830, "joins": joins,
            "words_read": sum(1 for w in words if w),
            "exclude_title": d["bom_exclude_title"]}  # fmt: skip
    s = summarise([book], meta, holders_by_join(lp["held"]), rows, d, p.get("samples"))[0]
    by_key = {join_key(j["a"], j["b"]): j for j in joins}
    spans = chapter_spans()
    lo, hi = spans[tuple(d["seed_chapter"])]
    for j in s["joins"]:
        raw = by_key[j["join"]]
        j["a_refs"], j["b_refs"] = refs(bible, raw["a"]), refs(bible, raw["b"])
        j["chapter_1830"] = next(
            f"{k[0]} {k[1]}" for k, (x, y) in spans.items() if x <= raw["at"] < y
        )
    seed = [j for j in s["joins"] if lo <= by_key[j["join"]]["at"] < hi]
    seed.sort(key=lambda j: (j["join"] != d.get("seed_pair"), by_key[j["join"]]["at"]))
    sh = s["shares"]["share_late"]
    res["book_of_mormon"] = {
        "shares": s["shares"],
        "shares_distinct_authors": s["shares_distinct_authors"],
        "verdict": verdict(sh, early, late, d),
        "verdict_distinct_authors": verdict(
            s["shares_distinct_authors"]["share_late"],
            [b["shares_distinct_authors"]["share_late"] for b in chk["check_books"]
             if b["check_decade"] in d["early_decades"]
             and b["shares_distinct_authors"].get("usable")],
            [b["shares_distinct_authors"]["share_late"] for b in chk["check_books"]
             if b["check_decade"] == d["check_decades"][-1]
             and b["shares_distinct_authors"].get("usable")], d),
        "early_books_p90": percentile(early, d["late_percentile"]),
        "early_books_p75": percentile(early, d["old_percentile"]),
        "late_books_median": statistics.median(late) if late else None,
        "seed_chapter_joins": seed,
        "joins": s["joins"],
        "library": {"works": lp["works"], "unreadable_not_attempted": len(lp["unreadable"])},
    }  # fmt: skip
    return res


def seed_joins(cfg: dict) -> dict:
    """Step 1 only (no dating): the joins found in the seed chapter, one by one, with verses."""
    p = prepare(cfg)
    d, bible, rare = p["d"], p["bible"], p["rare"]
    words = bom_words()
    lo, hi = chapter_spans()[tuple(d["seed_chapter"])]
    joins = joins_in(words, bible, rare, d)
    seed = [j for j in joins if lo <= j["at"] < hi]
    return {
        "what": "joins found by step 1 in 1830 2 Nephi XII (modern 2 Nephi 28); not dated",
        "book_joins_all_chapters": len(joins),
        "seed_chapter": " ".join(map(str, d["seed_chapter"])),
        "joins": [{"a": " ".join(j["a"]), "a_refs": refs(bible, j["a"]), "b": " ".join(j["b"]),
                   "b_refs": refs(bible, j["b"]), "times": j["times"]} for j in seed],
    }  # fmt: skip


def pair_table(cfg: dict) -> dict:
    """Counting only, no verdict: library works holding each listed 2 Nephi 28 pair within the
    window, by decade, as a count and per 1,000 works, with the earliest holder."""
    d = settings(cfg)
    rows = library_rows(d)
    meta = {r["work_id"]: r for r in rows}
    totals = decade_totals(rows)
    pairs = [(tuple(a.split()), tuple(b.split())) for a, b in d["table_pairs"]]
    lp = library_pass("table", pairs, rows, d)
    by = holders_by_join(lp["held"])
    skip = own_copies({"exclude_title": d["bom_exclude_title"]}, rows, d)
    out_rows = []
    for a, b in pairs:
        k = join_key(a, b) if join_key(a, b) in by else join_key(b, a)
        ws = sorted((meta[w]["year"], w) for w in by.get(k, []) if w not in skip)
        c: dict[int, int] = defaultdict(int)
        for y, _w in ws:
            c[y // 10 * 10] += 1
        out_rows.append({
            "a": " ".join(a), "b": " ".join(b), "works": len(ws),
            "by_decade": {str(x): {"works": c.get(x, 0),
                                   "per_1000": round(1000 * c.get(x, 0) / totals[x], 3)}
                          for x in DECADES},
            "earliest": {"work_id": ws[0][1], "year": ws[0][0]} if ws else None,
        })  # fmt: skip
    return {"what": "counting only, no verdict: works holding both phrases within "
            f"{d['window']} words (default set 1640-1829, Book of Mormon copies out)",
            "works_by_decade": {str(x): totals.get(x, 0) for x in DECADES},
            "library_works": lp["works"], "unreadable_not_attempted": len(lp["unreadable"]),
            "pairs": out_rows}  # fmt: skip


def write(res: dict, name: str) -> None:
    out(OUT / name).write_text(json.dumps(res, indent=1, default=list) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["tune", "check", "run", "seed", "table"])
    a = ap.parse_args(argv)
    cfg = config.load()
    sfx = f"_v{settings(cfg)['design']}" if settings(cfg).get("design", 1) >= 2 else ""
    if a.cmd == "table":
        res = {**config.stamp(), **pair_table(cfg)}
        write(res, "pair_table.json")
        print(json.dumps(res["pairs"], indent=1)[:4000])
        return 0
    if a.cmd == "seed":
        res = {"settings": settings(cfg), **config.stamp(), **seed_joins(cfg)}
        write(res, f"seed_joins{sfx}.json")
        print(json.dumps({k: v for k, v in res.items() if k != "settings"}, indent=1))
        return 0
    if a.cmd == "tune":
        res = {"settings": settings(cfg), **config.stamp(), **tune(cfg)}
        write(res, "tune_v2.json")
        print(json.dumps(res["chosen"], indent=1))
        return 0
    if a.cmd == "check":
        p = prepare(cfg)
        res = {"settings": settings(cfg), **config.stamp(), "known_answer": run_check(cfg, p)}
        write(res, f"check{sfx}.json")
    else:
        res = run(cfg)
        write(res, f"result{sfx}.json")
    ka = res["known_answer"]
    planted = {k: v for k, v in ka["planted"].items() if not k.endswith("_rows")}
    print(json.dumps({"planted": planted, "books": ka.get("books"), "passed": ka["passed"]},
                     indent=1))  # fmt: skip
    if "book_of_mormon" in res:
        b = res["book_of_mormon"]
        print(json.dumps({k: b[k] for k in b if k not in ("joins",)}, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
