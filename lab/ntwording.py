"""BOM-124: exact New Testament wording in the parts of the Book of Mormon set before Christ.

Takes the King James text, finds the word 4-grams and 5-grams that occur in the New Testament and
not in the Old Testament or Apocrypha ("NT-distinctive", and the reverse "OT-distinctive"), drops
those found in more than a stated share of a background sample of period works, and counts hits
(maximal runs of words covered by matching n-grams) per 10,000 words in any text. The Book of
Mormon is scored by book and by narrative time with the formal quotation chapters apart, and the
same measure is taken on sermons, non-religious books, Bible-style books, period translations
(Josephus by Whiston, the Koran by Sale), Joseph Smith's revelations and the Book of Moses
manuscripts. Exact phrases only: no model, no AI judging. The test card, written first, is
``data/private/lab/owner/2026-11-20-new-testament-wording/card.md``; settings are
``lab.new_testament_wording`` in the config. The output holds ids, counts and rates, no text.

Usage::

    python -m lab.ntwording check     # known-answer checks only (leave-one-book-out; sermons)
    python -m lab.ntwording run       # -> data/lab/reruns/new_testament_wording/result.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import subprocess
import time
from pathlib import Path

import pyarrow.compute as pc

from lab import door, registry
from lab.paths import FAST, NOTES, REGISTRY, out
from lab.wherefore import QUOTED
from metadata import config

OUT = REGISTRY / "reruns" / "new_testament_wording"
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
KJV = Path("data/kjv/kjv.jsonl")
CAND = Path("data/candidates/text")
PRIVATE_CAND = Path("data/private/candidates")
NAMES = FAST / "sources" / "names"
BIBLE_STYLE = FAST / "sources" / "bible_style"
DICTATED = NOTES / "sources" / "dictated"
WORD = re.compile(r"[a-z]+")
GAP = 10  # words between pieces joined into one stream, so a run cannot bridge them
GROUPS = {
    "gospels_and_acts": {"MAT", "MAR", "LUK", "JOH", "ACT"},
    "paul": {"ROM", "1CO", "2CO", "GAL", "EPH", "PHI", "COL", "1TH", "2TH", "1TI", "2TI"}
    | {"TIT", "PHM"},
    "hebrews": {"HEB"},
    "general_epistles": {"JAM", "1PE", "2PE", "1JO", "2JO", "3JO", "JUD"},
    "revelation": {"REV"},
}


def tokens(text: str) -> list[str]:
    return WORD.findall(text.lower())


# ------------------------------------------------------------------------ the King James sets


class Kjv:
    """The King James text by book: section, tokenised verses, a bit for each book."""

    def __init__(self, rows: list[dict]):
        self.codes: list[str] = []
        self.section: dict[str, str] = {}
        self.verses: dict[str, list[list[str]]] = {}
        for r in rows:
            c = r["book"]
            if c not in self.section:
                self.codes.append(c)
                self.section[c] = r["section"]
                self.verses[c] = []
            self.verses[c].append(tokens(r["text"]))
        self.bit = {c: 1 << i for i, c in enumerate(self.codes)}
        self.NT = sum(self.bit[c] for c in self.codes if self.section[c] == "NT")
        self.OT = sum(self.bit[c] for c in self.codes if self.section[c] == "OT")
        self.AP = sum(self.bit[c] for c in self.codes if self.section[c] == "Apocrypha")

    def words(self, code: str) -> int:
        return sum(len(v) for v in self.verses[code])


def build_grams(kjv: Kjv, sizes: list[int]) -> dict[str, int]:
    """Every n-gram of the King James verses -> bitmask of the books that hold it."""
    d: dict[str, int] = {}
    for c in kjv.codes:
        bit = kjv.bit[c]
        for v in kjv.verses[c]:
            for n in sizes:
                for i in range(len(v) - n + 1):
                    g = " ".join(v[i : i + n])
                    d[g] = d.get(g, 0) | bit
    return d


class Universe:
    """The n-grams that could be distinctive in some leave-one-out form (or in the full form)."""

    def __init__(self, kjv: Kjv, grams: dict[str, int]):
        self.kjv = kjv
        self.NT, self.OT, self.AP = kjv.NT, kjv.OT, kjv.AP
        self.grams: list[str] = []
        self.masks: list[int] = []
        for g, m in grams.items():
            if m & self.AP:
                continue
            other_ot = (m & self.OT).bit_count()
            other_nt = (m & self.NT).bit_count()
            if (m & self.NT and other_ot <= 1) or (m & self.OT and other_nt <= 1):
                self.grams.append(g)
                self.masks.append(m)
        self.ids = {g: i for i, g in enumerate(self.grams)}
        self.ot5 = {g for g, m in grams.items() if m & self.OT and g.count(" ") == 4}


def scan(words: list[str], uni: Universe, sizes: list[int]) -> list[tuple[int, int, int]]:
    """(position, n, gram id) for every universe n-gram in ``words``."""
    res, ids, ln = [], uni.ids, len(words)
    for i in range(ln):
        for n in sizes:
            if i + n <= ln:
                gid = ids.get(" ".join(words[i : i + n]))
                if gid is not None:
                    res.append((i, n, gid))
    return res


class Stream:
    """Several pieces of text read as one: words and matches, pieces kept apart by a gap."""

    def __init__(self) -> None:
        self.words = 0
        self.off = 0
        self.matches: list[tuple[int, int, int]] = []

    def add(self, nwords: int, matches: list[tuple[int, int, int]]) -> None:
        self.matches.extend((p + self.off, n, g) for p, n, g in matches)
        self.words += nwords
        self.off += nwords + GAP


def merge_runs(items: list[tuple[int, int, int]]) -> list[tuple[int, int, list[int]]]:
    """Overlapping (start, end, gid) intervals -> maximal runs (start, end, gids)."""
    runs: list[list] = []
    for s, e, g in sorted(items):
        if runs and s < runs[-1][1]:
            runs[-1][1] = max(runs[-1][1], e)
            runs[-1][2].append(g)
        else:
            runs.append([s, e, [g]])
    return [(s, e, g) for s, e, g in runs]


def measure(st: Stream, allowed: list[bool], uni: Universe, hold: int = 0) -> dict:
    """Hits of each kind in a stream; ``hold`` is the bit of a book left out of the sets."""
    nts, ots = [], []
    for pos, n, gid in st.matches:
        if not allowed[gid]:
            continue
        m = uni.masks[gid]
        nt, ot = m & uni.NT & ~hold, m & uni.OT & ~hold
        if nt and not ot:
            nts.append((pos, pos + n, gid))
        elif ot and not nt:
            ots.append((pos, pos + n, gid))
    nr, orr = merge_runs(nts), merge_runs(ots)
    credit: dict[int, float] = {}
    for _s, _e, gids in nr:
        bits = 0
        for g in gids:
            bits |= uni.masks[g] & uni.NT & ~hold
        idx = [i for i in range(bits.bit_length()) if bits >> i & 1]
        for i in idx:
            credit[i] = credit.get(i, 0.0) + 1 / len(idx)
    return {
        "words": st.words,
        "nt_hits": len(nr),
        "nt_covered": sum(e - s for s, e, _ in nr),
        "ot_hits": len(orr),
        "ot_covered": sum(e - s for s, e, _ in orr),
        "credit": credit,
    }


def add_stats(a: dict, b: dict) -> dict:
    c = {k: a[k] + b[k] for k in ("words", "nt_hits", "nt_covered", "ot_hits", "ot_covered")}
    c["credit"] = dict(a["credit"])
    for k, v in b["credit"].items():
        c["credit"][k] = c["credit"].get(k, 0.0) + v
    return c


EMPTY = {"words": 0, "nt_hits": 0, "nt_covered": 0, "ot_hits": 0, "ot_covered": 0, "credit": {}}


def rate(s: dict, key: str = "nt_hits") -> float | None:
    return round(s[key] / s["words"] * 10000, 3) if s["words"] else None


def rates(s: dict) -> dict:
    return {
        "words": s["words"],
        "nt_hits": s["nt_hits"],
        "nt_per_10k": rate(s),
        "nt_words_covered_share": round(s["nt_covered"] / s["words"], 5) if s["words"] else None,
        "ot_hits": s["ot_hits"],
        "ot_per_10k": rate(s, "ot_hits"),
    }


def auc(pos: list[float], neg: list[float]) -> float:
    """Chance that a random positive scores above a random negative (ties count half)."""
    if not pos or not neg:
        return float("nan")
    wins = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def quantiles(xs: list[float]) -> dict:
    xs = sorted(xs)
    if not xs:
        return {}
    q = {f"p{p}": xs[min(len(xs) - 1, int(len(xs) * p / 100))] for p in (5, 25, 50, 75, 95)}
    return {"n": len(xs), **q}


def percentile_of(x: float, xs: list[float]) -> float | None:
    return round(100 * sum(v <= x for v in xs) / len(xs), 1) if xs else None


# ------------------------------------------------------------------------ library samples


def eligible(cfg: dict, pred) -> list[dict]:
    t = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(t["kind"], "work"), pc.equal(t["has_text"], True)),
        pc.equal(t["dup_keeper"], True),
    )
    return [
        r
        for r in t.filter(keep).to_pylist()
        if not r["sealed"] and not r["ocr_excluded"] and r["year"] and pred(r)
    ]


def draw(rows: list[dict], n: int, seed: int, exclude: set[str]) -> list[dict]:
    rows = [r for r in rows if r["work_id"] not in exclude]
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


def read_words(row: dict, cap: int | None) -> list[str] | None:
    try:
        w = tokens(door.text_of(row))
    except OSError:
        return None  # unreadable: not attempted, never a result
    return w[:cap] if cap else w


def scan_rows(rows: list[dict], uni: Universe, sizes: list[int], cap: int, label: str) -> dict:
    """work_id -> (words, matches) for the readable works; unreadable ones are counted apart."""
    done, bad, t0 = {}, 0, time.time()
    for k, r in enumerate(rows):
        w = read_words(r, cap)
        if w is None:
            bad += 1
            continue
        done[r["work_id"]] = (len(w), scan(w, uni, sizes), r["year"])
        if k % 100 == 99:
            print(f"  {label}: {k + 1}/{len(rows)} ({time.time() - t0:.0f}s)", flush=True)
    return {"done": done, "unreadable": bad}


def stream_of(nwords: int, matches: list) -> Stream:
    s = Stream()
    s.add(nwords, matches)
    return s


# ------------------------------------------------------------------------ named texts


def body_of_gutenberg(text: str) -> str:
    m = re.search(r"\*\*\* START OF [^\n]*\*\*\*", text)
    e = re.search(r"\*\*\* END OF [^\n]*\*\*\*", text)
    return text[m.end() if m else 0 : e.start() if e else len(text)]


def josephus_parts(text: str, split: str) -> dict[str, str]:
    """Antiquities: body from the last 'BOOK I.' heading; split at the last 'BOOK <split>.'"""
    text = body_of_gutenberg(text)
    first = [m.start() for m in re.finditer(r"^BOOK I\.", text, re.M)]
    cut = [m.start() for m in re.finditer(rf"^BOOK {split}\.", text, re.M)]
    if not first or not cut:
        raise ValueError("Josephus book headings not found")
    a, c = first[-1], cut[-1]
    return {"old_testament_times": text[a:c], "later_times": text[c:]}


def strip_front_matter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4 :]
    return text


def named_texts(cfg: dict) -> dict[str, dict]:
    """Group -> {name: text}; a missing file is left out and reported, never scored as zero."""
    w = cfg["lab"]["new_testament_wording"]
    res: dict[str, dict] = {k: {} for k in ("translators", "bible_style", "revelations", "moses")}
    missing: list[str] = []

    def put(group: str, name: str, getter) -> None:
        try:
            res[group][name] = getter()
        except (OSError, ValueError):
            missing.append(f"{group}/{name}")

    ant = NAMES / "josephus_antiquities_whiston.txt"
    try:
        for k, v in josephus_parts(
            ant.read_text(encoding="utf-8", errors="replace"), w["josephus_split"]
        ).items():
            res["translators"][f"josephus_antiquities_{k}"] = v
    except (OSError, ValueError):
        missing.append("translators/josephus_antiquities")
    put(
        "translators",
        "josephus_wars",
        lambda: body_of_gutenberg(
            (NAMES / "josephus_wars_whiston.txt").read_text("utf-8", "replace")
        ),
    )
    put(
        "translators",
        "koran_sale",
        lambda: body_of_gutenberg((NAMES / "koran_sale.txt").read_text("utf-8", "replace")),
    )
    for d in sorted(BIBLE_STYLE.iterdir()) if BIBLE_STYLE.exists() else []:
        if (d / "text.txt").exists():
            put("bible_style", d.name, lambda d=d: (d / "text.txt").read_text("utf-8", "replace"))
    put(
        "bible_style",
        "late_war_1816",
        lambda: (CAND / "gh-1816-late-war.txt").read_text("utf-8", "replace"),
    )
    wt = BIBLE_STYLE / "wordtree_books" / "pseudo_biblical"
    for f in sorted(wt.glob("*.md")) if wt.exists() else []:
        if any(x in f.name for x in w["bible_style_exclude"]):
            continue
        put("bible_style", f.stem, lambda f=f: strip_front_matter(f.read_text("utf-8", "replace")))
    put(
        "revelations",
        "js_revelation_book_1",
        lambda: " ".join(
            json.loads(line)["text"]
            for line in (PRIVATE_CAND / "js-1828-1829-revelations.jsonl").read_text().splitlines()
        ),
    )
    later = sorted((PRIVATE_CAND / "later").glob("*.txt"))
    if later:
        res["revelations"]["js_later_revelations"] = "\n".join(
            p.read_text("utf-8", "replace") for p in later
        )
    else:
        missing.append("revelations/js_later_revelations")
    for name in ("visions_of_moses_1830", "ot_revision_1", "ot_revision_2"):
        put(
            "moses",
            name,
            lambda name=name: " ".join(
                json.loads(line)["text"]
                for line in (DICTATED / name / "pages.jsonl").read_text().splitlines()
            ),
        )
    res["_missing"] = {"not_attempted": missing}
    return res


# ------------------------------------------------------------------------ the Book of Mormon


def bom_units(uni: Universe, sizes: list[int]) -> dict[tuple[str, int, bool], Stream]:
    """(book, 1830 chapter, is formal quotation chapter) -> stream of its body paragraphs."""
    labels = {
        r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines()) if r["kind"] == "body"
    }
    units: dict[tuple[str, int, bool], Stream] = {}
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if lab is None:
            continue
        key = (r["book"], lab["chapter_1830"], (r["book"], lab["chapter_1830"]) in QUOTED)
        w = tokens(r["text"])
        units.setdefault(key, Stream()).add(len(w), scan(w, uni, sizes))
    return units


def time_group(book: str, w: dict) -> str | None:
    for name, key in (
        ("before", "before_books"),
        ("ether", "ether_books"),
        ("visit", "visit_books"),
        ("after", "after_books"),
    ):
        if book in w[key]:
            return name
    return None


def bootstrap_ratio(pre: list[tuple[int, int]], post: list[tuple[int, int]], w: dict) -> dict:
    """Rate in ``post`` over rate in ``pre``; units are (words, hits) per 1830 chapter."""

    def r(units):
        words = sum(u[0] for u in units)
        return sum(u[1] for u in units) / words if words else 0.0

    base = r(pre)
    point = r(post) / base if base else float("inf")
    rng, draws = random.Random(w["boot_seed"]), []
    for _ in range(w["boot"]):
        a = r([rng.choice(pre) for _ in pre])
        b = r([rng.choice(post) for _ in post])
        draws.append(b / a if a else float("inf"))
    draws.sort()
    lo, hi = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
    return {
        "ratio": round(point, 3),
        "ci95": [round(lo, 3), round(hi, 3)],
        "pre_per_10k": round(base * 10000, 3),
        "post_per_10k": round(r(post) * 10000, 3),
    }


def step_verdict(b: dict, w: dict) -> str:
    lo, hi = b["ci95"]
    if b["ratio"] >= w["step_ratio_bar"] and lo > 1:
        return "step up"
    if lo <= 1 <= hi:
        return "no step"
    if hi < 1:
        return "step down"
    return "cannot tell"


def bom_section(units: dict, allowed: list[bool], uni: Universe, w: dict, detail: bool) -> dict:
    per_unit = {k: measure(s, allowed, uni) for k, s in units.items()}
    groups: dict[str, dict] = {}
    by_book: dict[str, dict] = {}
    for (book, _ch, quoted), s in per_unit.items():
        tg = time_group(book, w)
        gname = f"{tg}_{'quotation_chapters' if quoted else 'outside_quotation'}"
        groups[gname] = add_stats(groups.get(gname, EMPTY), s)
        for part in ("all", "quotation" if quoted else "outside_quotation"):
            d = by_book.setdefault(book, {})
            d[part] = add_stats(d.get(part, EMPTY), s)
    pre = add_stats(groups["before_outside_quotation"], groups["ether_outside_quotation"])
    post = add_stats(groups["visit_outside_quotation"], groups["after_outside_quotation"])
    groups["pre_christian_outside_quotation"] = pre
    groups["visit_and_after_outside_quotation"] = post

    def chap_units(books: list[str]) -> list[tuple[int, int]]:
        return [
            (s["words"], s["nt_hits"]) for (b, _c, q), s in per_unit.items() if b in books and not q
        ]

    before_b = w["before_books"]
    step_pre = chap_units(before_b)
    step_post = chap_units(w["visit_books"] + w["after_books"])
    step = bootstrap_ratio(step_pre, step_post, w)
    step["verdict"] = step_verdict(step, w)
    step_with_ether = bootstrap_ratio(
        chap_units(before_b + w["ether_books"]), step_post, w
    )  # Ether counted with the earlier narrative
    step_with_ether["verdict"] = step_verdict(step_with_ether, w)
    res = {
        "step_3_nephi_onward": step,
        "step_with_ether_in_before": step_with_ether,
        "headline": {k: rates(v) for k, v in groups.items()},
    }
    if detail:
        res["by_book"] = {
            b: {p: rates(s) for p, s in d.items()}
            for b, d in sorted(by_book.items(), key=lambda kv: kv[0])
        }
        res["by_chapter_outside_quotation"] = [
            {"book": b, "chapter_1830": c, "words": s["words"], "nt_hits": s["nt_hits"]}
            for (b, c, q), s in sorted(per_unit.items())
            if not q
        ]
        res["_groups_raw"] = groups
    else:
        res["_groups_raw"] = groups
    return res


def supplier_table(stat: dict, uni: Universe, w: dict) -> dict:
    """Credit by New Testament book against the book's share of the New Testament's words."""
    kjv = uni.kjv
    nt_codes = [c for c in kjv.codes if kjv.section[c] == "NT"]
    nt_words = sum(kjv.words(c) for c in nt_codes)
    total = sum(stat["credit"].values()) or 1.0
    rows = []
    for c in nt_codes:
        cred = stat["credit"].get(kjv.codes.index(c), 0.0)
        share_w = kjv.words(c) / nt_words
        rows.append(
            {
                "book": c,
                "credit": round(cred, 2),
                "share_of_hits": round(cred / total, 4),
                "share_of_nt_words": round(share_w, 4),
                "enrichment": round(cred / total / share_w, 2),
            }
        )
    groups = {}
    for g, codes in GROUPS.items():
        cred = sum(r["credit"] for r in rows if r["book"] in codes)
        share_w = sum(r["share_of_nt_words"] for r in rows if r["book"] in codes)
        groups[g] = {
            "credit": round(cred, 2),
            "share_of_hits": round(cred / total, 4),
            "share_of_nt_words": round(share_w, 4),
            "enrichment": round(cred / total / share_w, 2) if share_w else None,
        }
    top = sorted(rows, key=lambda r: -r["credit"])[: w["top_books"]]
    return {"hits": stat["nt_hits"], "top_by_credit": top, "groups": groups, "all": rows}


# ------------------------------------------------------------------------ the checks


def loo_scores(kjv: Kjv, uni: Universe, allowed, sizes, w) -> list[dict]:
    rows = []
    for c in kjv.codes:
        if kjv.section[c] == "Apocrypha" or kjv.words(c) < w["loo_min_words"]:
            continue
        st = Stream()
        for v in kjv.verses[c]:
            st.add(len(v), scan(v, uni, sizes))
        m = measure(st, allowed, uni, hold=kjv.bit[c])
        rows.append(
            {
                "book": c,
                "section": kjv.section[c],
                "words": m["words"],
                "nt_per_10k": rate(m),
                "ot_per_10k": rate(m, "ot_hits"),
            }
        )
    return rows


def loo_auc(rows: list[dict]) -> dict:
    nt = [r for r in rows if r["section"] == "NT"]
    ot = [r for r in rows if r["section"] == "OT"]
    return {
        "nt_books": len(nt),
        "ot_books": len(ot),
        "auc_nt_distinctive_nt_over_ot": round(
            auc([r["nt_per_10k"] for r in nt], [r["nt_per_10k"] for r in ot]), 4
        ),
        "auc_ot_distinctive_ot_over_nt": round(
            auc([r["ot_per_10k"] for r in ot], [r["ot_per_10k"] for r in nt]), 4
        ),
        "nt_median_nt_per_10k": round(statistics.median(r["nt_per_10k"] for r in nt), 2),
        "ot_median_nt_per_10k": round(statistics.median(r["nt_per_10k"] for r in ot), 2),
    }


def rates_of(scanned: dict, allowed, uni) -> dict[str, dict]:
    return {
        wid: measure(stream_of(n, m), allowed, uni) for wid, (n, m, _y) in scanned["done"].items()
    }


def prepare(cfg: dict) -> dict:
    """Everything that does not touch the Book of Mormon: sets, background, library samples."""
    w = cfg["lab"]["new_testament_wording"]
    sizes = w["ngram_sizes"]
    t0 = time.time()
    kjv = Kjv([json.loads(line) for line in KJV.read_text().splitlines()])
    uni = Universe(kjv, build_grams(kjv, sizes))
    print(f"King James: {len(uni.grams):,} candidate n-grams ({time.time() - t0:.0f}s)", flush=True)
    sermon_rows = draw(
        eligible(
            cfg,
            lambda r: (
                w["sermon_year_min"] <= r["year"] <= w["sermon_year_max"]
                and "sermon_devotional" in (r["genre"] or "")
                and (r["words"] or 0) >= w["baseline_min_words"]
            ),
        ),
        w["sermon_sample"],
        w["sermon_seed"],
        set(),
    )
    non_rows = draw(
        eligible(
            cfg,
            lambda r: (
                w["sermon_year_min"] <= r["year"] <= w["sermon_year_max"]
                and (r["genre"] or "") in ("history_chronicle", "scientific_medical")
                and (r["words"] or 0) >= w["baseline_min_words"]
            ),
        ),
        w["nonreligious_sample"],
        w["nonreligious_seed"],
        set(),
    )
    used = {r["work_id"] for r in sermon_rows + non_rows}
    bg_rows = draw(
        eligible(
            cfg,
            lambda r: (
                w["bg_year_min"] <= r["year"] <= w["bg_year_max"]
                and (r["words"] or 0) >= w["bg_min_words"]
            ),
        ),
        w["bg_sample"],
        w["bg_seed"],
        used,
    )
    cap = w["max_words_per_work"]
    bg = scan_rows(bg_rows, uni, sizes, cap, "background")
    df = [0] * len(uni.grams)
    for _n, matches, _y in bg["done"].values():
        for gid in {g for _p, _n2, g in matches}:
            df[gid] += 1
    n_bg = max(len(bg["done"]), 1)
    allowed = {
        thr: [d / n_bg <= thr for d in df]
        for thr in sorted({w["bg_max_share"], *w["bg_max_share_sensitivity"]})
    }
    sermons = scan_rows(sermon_rows, uni, sizes, cap, "sermons")
    non = scan_rows(non_rows, uni, sizes, cap, "non-religious")
    return {
        "w": w,
        "sizes": sizes,
        "kjv": kjv,
        "uni": uni,
        "bg": bg,
        "df": df,
        "allowed": allowed,
        "sermons": sermons,
        "non": non,
        "cap": cap,
    }


def known_answers(p: dict) -> dict:
    w, kjv, uni, sizes = p["w"], p["kjv"], p["uni"], p["sizes"]
    res = {"by_threshold": {}}
    for thr, allowed in p["allowed"].items():
        rows = loo_scores(kjv, uni, allowed, sizes, w)
        s = rates_of(p["sermons"], allowed, uni)
        n = rates_of(p["non"], allowed, uni)
        s_r = [rate(m) for m in s.values()]
        n_r = [rate(m) for m in n.values()]
        entry = {
            "leave_one_book_out": loo_auc(rows),
            "sermons_over_non_religious_auc": round(auc(s_r, n_r), 4),
            "sermons": quantiles(s_r),
            "non_religious": quantiles(n_r),
        }
        if thr == w["bg_max_share"]:
            entry["leave_one_book_out"]["books"] = rows
        res["by_threshold"][str(thr)] = entry
    prim = res["by_threshold"][str(w["bg_max_share"])]
    res["bars"] = {"loo_auc": w["loo_auc_bar"], "sermon_auc": w["sermon_auc_bar"]}
    res["loo_passed"] = (
        prim["leave_one_book_out"]["auc_nt_distinctive_nt_over_ot"] >= w["loo_auc_bar"]
    )
    res["sermons_passed"] = prim["sermons_over_non_religious_auc"] >= w["sermon_auc_bar"]
    res["passed"] = res["loo_passed"] and res["sermons_passed"]
    res["samples"] = {
        "background": {"works": len(p["bg"]["done"]), "unreadable": p["bg"]["unreadable"]},
        "sermons": {"works": len(p["sermons"]["done"]), "unreadable": p["sermons"]["unreadable"]},
        "non_religious": {"works": len(p["non"]["done"]), "unreadable": p["non"]["unreadable"]},
    }
    return res


def decades(cfg: dict) -> dict:
    """Coverage of the library by decade: eligible works, and sermon works, for 1700-1830."""
    rows = eligible(cfg, lambda r: 1700 <= r["year"] <= 1839)
    tot: dict[str, int] = {}
    ser: dict[str, int] = {}
    for r in rows:
        d = str(r["year"] // 10 * 10)
        tot[d] = tot.get(d, 0) + 1
        if "sermon_devotional" in (r["genre"] or ""):
            ser[d] = ser.get(d, 0) + 1
    return {"works_with_text": dict(sorted(tot.items())), "sermon_works": dict(sorted(ser.items()))}


# ------------------------------------------------------------------------ the run


def named_scans(p: dict, named: dict) -> dict:
    """Group -> name -> (stream, words outside any exact Old Testament 5-gram or None)."""
    uni, sizes = p["uni"], p["sizes"]
    res: dict[str, dict] = {}
    for group in ("translators", "bible_style", "revelations", "moses"):
        res[group] = {}
        for name, text in named[group].items():
            words = tokens(text)
            added = None
            if group == "moses":  # the manuscripts copy Genesis: count words outside any OT 5-gram
                covered = [False] * len(words)
                for i in range(len(words) - 4):
                    if " ".join(words[i : i + 5]) in uni.ot5:
                        for j in range(i, i + 5):
                            covered[j] = True
                added = covered.count(False)
            res[group][name] = (stream_of(len(words), scan(words, uni, sizes)), added)
    return res


def named_stats(p: dict, scans: dict, allowed: list[bool]) -> dict:
    res: dict[str, dict] = {}
    for group, items in scans.items():
        res[group] = {}
        for name, (st, added) in items.items():
            m = measure(st, allowed, p["uni"])
            r = rates(m)
            if added is not None:
                r["words_outside_any_old_testament_5gram"] = added
                r["nt_per_10k_outside_old_testament_5grams"] = (
                    round(m["nt_hits"] / added * 10000, 3) if added else None
                )
            res[group][name] = r
    return res


def headline(p: dict, scans: dict, units: dict, thr: float, detail: bool) -> dict:
    w, uni = p["w"], p["uni"]
    allowed = p["allowed"][thr]
    bom = bom_section(units, allowed, uni, w, detail)
    pre = bom["_groups_raw"]["pre_christian_outside_quotation"]
    pre_rate = rate(pre)
    named_r = named_stats(p, scans, allowed)
    ser = rates_of(p["sermons"], allowed, uni)
    ser_r = [rate(m) for m in ser.values()]
    non = rates_of(p["non"], allowed, uni)
    f = w["translator_factor"]
    jos = named_r["translators"].get("josephus_antiquities_old_testament_times", {})
    sale = named_r["translators"].get("koran_sale", {})
    moses = named_r["moses"]
    styles = {
        k: v for k, v in named_r["bible_style"].items() if v["words"] >= w["bible_style_min_words"]
    }
    style_med = statistics.median([v["nt_per_10k"] for v in styles.values()]) if styles else None

    def ratio(x):
        return round(pre_rate / x, 2) if x else None

    ot1 = moses.get("ot_revision_1", {})
    refs = [
        jos.get("nt_per_10k"),
        ot1.get("nt_per_10k"),
        ot1.get("nt_per_10k_outside_old_testament_5grams"),
    ]
    refs = [x for x in refs if x is not None]
    pct = percentile_of(pre_rate, ser_r)
    sermon_verdict = (
        "above sermons"
        if pct is not None and pct > w["sermon_percentile_bar"]
        else "within sermon range"
    )
    if not refs:
        translator_verdict = "not attempted"
    elif pre_rate > f * max(refs):
        translator_verdict = "above translators"
    elif any(x / f <= pre_rate <= x * f for x in refs):
        translator_verdict = "like a translator's"
    else:
        translator_verdict = "below or between translators"
    res = {
        "bom_pre_christian_outside_quotation": rates(pre),
        "bom_headline": bom["headline"],
        "step_3_nephi_onward": bom["step_3_nephi_onward"],
        "step_with_ether_in_before": bom["step_with_ether_in_before"],
        "placement": {
            "pre_christian_nt_per_10k": pre_rate,
            "percentile_among_sermons": pct,
            "sermons": quantiles(ser_r),
            "non_religious": quantiles([rate(m) for m in non.values()]),
            "ratio_to_josephus_old_testament_times": ratio(jos.get("nt_per_10k")),
            "ratio_to_sale_koran": ratio(sale.get("nt_per_10k")),
            "ratio_to_bible_style_median": ratio(style_med),
            "bible_style_median": style_med,
            "ratio_to_book_of_moses_ot_revision_1": ratio(ot1.get("nt_per_10k")),
            "ratio_to_book_of_moses_outside_old_testament_5grams": ratio(
                ot1.get("nt_per_10k_outside_old_testament_5grams")
            ),
            "sermon_verdict": sermon_verdict,
            "translator_verdict": translator_verdict,
        },
        "step_verdict": bom["step_3_nephi_onward"]["verdict"],
    }
    if detail:
        raw = bom["_groups_raw"]
        res["bom_by_book"] = bom["by_book"]
        res["bom_by_chapter_outside_quotation"] = bom["by_chapter_outside_quotation"]
        res["baselines"] = named_r
        res["sermon_works"] = [
            {"work_id": k, "year": p["sermons"]["done"][k][2], **rates(v)} for k, v in ser.items()
        ]
        res["non_religious_works"] = [
            {"work_id": k, "year": p["non"]["done"][k][2], **rates(v)} for k, v in non.items()
        ]
        res["nt_book_suppliers"] = {
            "pre_christian_outside_quotation": supplier_table(
                raw["pre_christian_outside_quotation"], uni, w
            ),
            "visit_and_after_outside_quotation": supplier_table(
                raw["visit_and_after_outside_quotation"], uni, w
            ),
            "quotation_chapters_before": supplier_table(raw["before_quotation_chapters"], uni, w),
        }
        res["bible_style_counted_in_median"] = sorted(styles)
    return res


def run(cfg: dict) -> dict:
    w = cfg["lab"]["new_testament_wording"]
    p = prepare(cfg)
    chk = known_answers(p)
    res = {"known_answer": chk, "settings": w}
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
        return res
    res["library_coverage_by_decade"] = decades(cfg)
    named = named_texts(cfg)
    res["not_attempted"] = named.pop("_missing")
    scans = named_scans(p, named)
    units = bom_units(p["uni"], p["sizes"])
    res["results"] = {}
    for thr in p["allowed"]:
        detail = thr == w["bg_max_share"]
        res["results"][str(thr)] = headline(p, scans, units, thr, detail)
    res["primary_threshold"] = w["bg_max_share"]
    res["candidate_ngrams"] = len(p["uni"].grams)
    res["background_works"] = len(p["bg"]["done"])
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "check":
        res = known_answers(prepare(cfg))
        res["by_threshold"] = {
            k: {a2: b for a2, b in v.items() if a2 != "leave_one_book_out"}
            | {
                "leave_one_book_out": {
                    x: y for x, y in v["leave_one_book_out"].items() if x != "books"
                }
            }
            for k, v in res["by_threshold"].items()
        }
        print(json.dumps(res, indent=1))
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    summary = {k: v for k, v in res.items() if k not in ("settings", "results")}
    print(json.dumps(summary, indent=1)[:3000])
    for thr, r in res.get("results", {}).items():
        print(thr, json.dumps({k: r[k] for k in ("placement", "step_3_nephi_onward")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
