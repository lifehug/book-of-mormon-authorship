"""BOM-133: what translators from Hebrew wrote at the Bible's "father and mother" places.

A fixed list of Hebrew places (``lab.hebrew_translators.places``): verses naming father and
mother together, the parallel-line pairs, the participles of *yalad* and *harah* used of parents
and Gen 49:26 *horay*. Each is checked against the Westminster Leningrad Codex (``morphhb``).
For each Bible translator the verse is located in his text (clean texts by reference; OCR texts
by the verse's rarer content words and its neighbours') and its rendering classified by rule:
FATHER_AND_MOTHER, PARENTS, PARTICIPLE, OTHER or NOT_FOUND. Whole texts, biblical and
post-biblical, are counted for "parents" against "father and mother" with BOM-132's rules, beside
the Book of Mormon's numbers from ``hebrew_vocabulary/result3.json``. Exact counts; no model.
Card: ``data/private/lab/owner/2026-11-27-hebrew-translators/card.md``. The output holds
references, classes, counts and the one-to-six-word renderings at these verses (public-domain
Bible translations); no other text.

Usage::

    python -m lab.hebrewtranslators check   # places, King James and Young's checks -> check.json
    python -m lab.hebrewtranslators run     # every translator, if the check passes -> result.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from lab.paths import REGISTRY, out
from metadata import config

OUT = REGISTRY / "translation" / "hebrew_translators"
RESULT3 = REGISTRY / "translation" / "hebrew_vocabulary" / "result3.json"
YLT = Path("data/corpus/lab/sources/translation/ylt_txt.tar")
TOKEN = re.compile(r"[a-z]+|\d+")
CLASSES = ("FATHER_AND_MOTHER", "PARENTS", "PARTICIPLE", "OTHER", "NOT_FOUND")
PAIR_KINDS = ("pair", "parallel")

# Words that carry no locating power, and the parent words themselves (left out so the search
# does not favour any rendering of the thing being measured).
STOP = frozenset(
    """a an and the of to in into unto upon on at by for from with without as that this these those
    which who whom whose what when then than there their them they he him his she her hers it its
    i me my mine thou thee thy thine ye you your we us our be is are was were been being am art hath
    have has had having shall shalt will wilt would should may might must do doth did dost not no
    nor or but if so yet all any every also even let said say saith says one o oh lo behold
    child born""".split()
)
# The parent words count as one word class in locating, so a verse about parents is preferred
# over a look-alike verse without them, and no rendering is favoured over another.
PARENT_WORDS = frozenset(
    """father fathers mother mothers parent parents begat begot begotten beget begetteth begetting
    begetter bare bore borne bear beareth bearing bearer conceived conceive conceiver conceiving
    progenitors""".split()
)
PARENT_CLASS = "=parent"
FATHER = re.compile(r"\bfathers?\b")
MOTHER = re.compile(r"\bmothers?\b")
PARENT = re.compile(r"\bparents?\b")
BEARING = re.compile(
    r"\b(?:begat|begot|begotten|beget\w*|bare|bore|borne|bear(?:eth|ing|er|est)?|conceiv\w*|"
    r"(?:brought|bringing|bringeth|bring)\s+\w+\s+forth|gave\s+\w+\s+birth|"
    r"(?:hath|had|have|has)\s+borne?)\b"
)


# ----------------------------------------------------------------------------- places


def lemma_nums(lemma: str) -> list[int]:
    res = []
    for part in lemma.split("/"):
        m = re.match(r"\s*(\d+)", part)
        if m:
            res.append(int(m.group(1)))
    return res


def candidates(heb: dict[str, list[tuple[str, str]]], window: int) -> list[str]:
    """WLC verses where Hebrew (not Aramaic) H1 'av and H517 'em fall within ``window`` words."""
    res = []
    for ref, ws in heb.items():
        pos: dict[int, list[int]] = {1: [], 517: []}
        for i, (lemma, morph) in enumerate(ws):
            if morph[:1] != "H":
                continue
            for n in lemma_nums(lemma):
                if n in pos:
                    pos[n].append(i)
        if pos[1] and pos[517] and min(abs(a - b) for a in pos[1] for b in pos[517]) <= window:
            res.append(ref)
    return res


def places(w: dict) -> list[dict]:
    """The fixed places: id ``REF:kind``, the WLC reference and the kind."""
    return [
        {"id": f"{ref}:{kind}", "wlc": ref, "kind": kind}
        for kind, refs in w["places"].items()
        for ref in refs
    ]


def check_places(pl: list[dict], heb: dict, full: dict, w: dict) -> tuple[dict, dict[str, str]]:
    """Every pair and parallel place among the lemma-rule candidates; every participle place
    carrying its lemma; the King James reference of each place."""
    cand = set(candidates(heb, w["lemma_window"]))
    pairs = {p["wlc"] for p in pl if p["kind"] in PAIR_KINDS}
    missing_pair = sorted(pairs - cand)
    missing_lemma = [
        p["id"]
        for p in pl
        if p["kind"] in w["lemmas"]
        and not any(
            w["lemmas"][p["kind"]] in lemma_nums(lemma) for lemma, _m in heb.get(p["wlc"], [])
        )
    ]
    kjv_ref = {p["id"]: full.get(p["wlc"], p["wlc"]) for p in pl}
    res = {
        "candidates": len(cand),
        "pair_places": len({p["wlc"] for p in pl if p["kind"] == "pair"}),
        "parallel_places": len({p["wlc"] for p in pl if p["kind"] == "parallel"}),
        "participle_places": sum(p["kind"] not in PAIR_KINDS for p in pl),
        "set_aside": sorted(cand - pairs),
        "pair_places_not_candidates": missing_pair,
        "participle_places_without_lemma": missing_lemma,
        "english_numbering_differs": {k: v for k, v in kjv_ref.items() if v != k.split(":")[0]},
        "pass": not missing_pair and not missing_lemma,
    }
    return res, kjv_ref


# ----------------------------------------------------------------------------- classes

TARGETS = ("father", "fathers", "mother", "mothers", "parent", "parents", "born")
# First letters an OCR engine confuses with each target's (the long s read as f; rn as m).
FIRST = {"f": "fitls", "m": "mnr", "p": "p", "b": "bh"}


def edit(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


class Reader:
    """Reads OCR variants of the parent words as the words: a token that is not a target, is in
    fewer than ``max_texts`` period texts (or none), and, after "li" is read as "h", is within
    ``max_edit`` of a target (one edit for words under six letters), is no shorter, ends in the
    same two letters
    and begins with the target's letter or an OCR look-alike ("iatlier", "fiither", "bom"). Two
    tokens are joined when the join is such a variant ("fa ther")."""

    def __init__(self, counts: dict[str, int], max_texts: int, max_edit: int):
        self.counts, self.max_texts, self.max_edit = counts, max_texts, max_edit
        self._cache: dict[str, str | None] = {}

    def variant(self, w: str) -> str | None:
        if w in TARGETS:
            return w
        if w in self._cache:
            return self._cache[w]
        res = None
        if self.counts.get(w, 0) < self.max_texts and 3 <= len(w) <= 9:
            v = w.replace("li", "h")
            for t in TARGETS:
                lim = self.max_edit if len(t) >= 6 else 1
                if v[0] in FIRST[t[0]] and any(
                    v[-2:] == f[-2:] and 0 <= len(v) - len(f) <= lim and edit(v, f) <= lim
                    for f in {t, t.replace("rn", "m")}
                ):
                    res = t
                    break
        self._cache[w] = res
        return res

    def read(self, toks: list[str]) -> list[str]:
        res, i = [], 0
        while i < len(toks):
            v = self.variant(toks[i])
            joined = toks[i] + toks[i + 1] if i + 1 < len(toks) else ""
            if v is None and joined and (joined in TARGETS or min(
                self.counts.get(toks[i], 0), self.counts.get(toks[i + 1], 0)
            ) < self.max_texts):  # fmt: skip
                j = self.variant(joined)
                if j is not None:
                    res.append(j)
                    i += 2
                    continue
            res.append(v or toks[i])
            i += 1
        return res


def load_reader(w: dict) -> Reader:
    counts = {}
    for line in Path(w["lexicon"]).read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            counts[parts[0]] = int(parts[1])
    return Reader(counts, w["ocr"]["max_texts"], w["ocr"]["max_edit"])


def classify(words: str, kind: str) -> tuple[str, str | None]:
    """(class, the matched rendering of one to six words) for a located verse's words."""
    t = " ".join(words.split())
    f, m, p, b = FATHER.search(t), MOTHER.search(t), PARENT.search(t), BEARING.search(t)
    if kind in PAIR_KINDS:
        order = (("FATHER_AND_MOTHER", f and m), ("PARENTS", p), ("PARTICIPLE", b))
    else:
        order = (("PARENTS", p), ("PARTICIPLE", b), ("FATHER_AND_MOTHER", f and m))
    for cls, hit in order:
        if hit:
            return cls, rendering(t, cls)
    return "OTHER", None


def rendering(t: str, cls: str) -> str:
    toks = t.split()

    def at(rx: re.Pattern) -> int:
        n = len(t[: rx.search(t).start()].split())
        return n

    if cls == "FATHER_AND_MOTHER":
        i, j = sorted((at(FATHER), at(MOTHER)))
        if j - i <= 5:
            return " ".join(toks[i : j + 1])
        return f"{toks[i]} ... {toks[j]}"
    if cls == "PARENTS":
        i = at(PARENT)
        return " ".join(toks[max(0, i - 2) : i + 1])
    i = at(BEARING)
    return " ".join(toks[max(0, i - 2) : i + 2])


# ----------------------------------------------------------------------------- locating


def tokens(text: str) -> list[str]:
    text = re.sub(r"-\s*\n\s*", "", text.replace("ſ", "s").replace("’", "'")).lower()
    return TOKEN.findall(text)


def stem(w: str, n: int) -> str:
    if w in PARENT_WORDS:
        return PARENT_CLASS
    w = w.replace("our", "or")  # honour, honor
    for suf in ("eth", "est", "ed", "ing", "es", "s", "th"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            w = w[: -len(suf)]
            break
    return w[:n]


def content(words: list[str], n: int) -> list[str]:
    return [stem(x, n) for x in words if x not in STOP and not x.isdigit() and len(x) > 1]


class Text:
    """One translator's text as tokens, their stems, and where each stem occurs."""

    def __init__(self, text: str, stem_len: int, fix=None):
        self.toks = tokens(text)
        if fix is not None:
            self.toks = [fix(x) for x in self.toks]
        self.n = stem_len
        self.stems = [stem(x, stem_len) for x in self.toks]
        self.where: dict[str, list[int]] = defaultdict(list)
        for i, s in enumerate(self.stems):
            self.where[s].append(i)
        self.size = max(len(self.toks), 1)

    def weight(self, s: str) -> float:
        return math.log(self.size / (1 + len(self.where.get(s, ()))))

    def cover(self, want: set[str], denom: set[str], lo: int, hi: int) -> float:
        have = set(self.stems[max(0, lo) : max(0, hi)])
        d = sum(self.weight(s) for s in denom)
        return min(1.0, sum(self.weight(s) for s in want & have) / d) if d else 0.0


def pads(words: list[str], loc: dict) -> tuple[int, int]:
    """Words to add before and after the matched span: the King James verse's own leading and
    trailing words outside the content words, plus a margin."""
    idx = [i for i, x in enumerate(words) if x not in STOP and not x.isdigit() and len(x) > 1]
    if not idx:
        return loc["pad_cap"], loc["pad_cap"]
    lead, trail = idx[0], len(words) - 1 - idx[-1]
    return (min(loc["pad_cap"], lead + loc["pad_extra"]),
            min(loc["pad_cap"], trail + loc["pad_extra"]))  # fmt: skip


def anchors(tx: Text, words: list[str], loc: dict) -> dict[int, float]:
    """Window centres from one version of the verse: every occurrence of its rarest content
    stems, each with that stem's place in the verse (0 at the start, 1 at the end)."""
    n, size = tx.n, max(len(words), 1)
    rel: dict[str, float] = {}
    for i, x in enumerate(words):
        if x not in STOP and not x.isdigit() and len(x) > 1:
            rel.setdefault(stem(x, n), i / size)
    res: dict[int, float] = {}
    for s in sorted((s for s in rel if s in tx.where), key=lambda s: len(tx.where[s]))[
        : loc["anchors"]
    ]:  # rarest first; stop before the positions run over the cap
        if res and len(res) + len(tx.where[s]) > loc["max_candidates"]:
            break
        for i in tx.where[s]:
            res.setdefault(i, rel[s])
    return res


def extend(tx: Text, a: int, b: int, want: set[str], gap: int, limit: int) -> tuple[int, int]:
    """Widen [a, b) over the verse's words found within ``gap`` words of either edge, by at most
    ``limit`` words on each side (a translator's verse may be longer than the King James)."""
    a0, b0 = a, b
    while True:
        prev = [i for i in range(max(0, a - gap), a) if tx.stems[i] in want and a0 - i <= limit]
        if not prev:
            break
        a = prev[0]
    while True:
        nxt = [i for i in range(b, min(tx.size, b + gap)) if tx.stems[i] in want and i - b0 < limit]
        if not nxt:
            break
        b = nxt[-1] + 1
    return a, b


def long_s(counts: dict[str, int], ratio: float):
    """OCR of the long s as f: a word read with s instead of f when that form is at least
    ``ratio`` times as common in the period word list ("fay" -> "say", "thruft" -> "thrust")."""
    cache: dict[str, str] = {}

    def fix(w: str) -> str:
        if "f" not in w:
            return w
        if w not in cache:
            alt = w.replace("f", "s")
            cache[w] = alt if counts.get(alt, 0) >= ratio * max(counts.get(w, 0), 1) else w
        return cache[w]

    return fix


def numbers(tx: Text, verse: dict, a: int, b: int, reach: int) -> tuple[int | None, int | None]:
    """Where the verse's number is printed just before ``a`` (the last such) and the next
    verse's number just after ``b`` (the first such), if they are."""
    v, nxt = str(verse["number"]), str(verse["next_number"])
    lo = next((i for i in range(a - 1, max(-1, a - reach - 1), -1) if tx.toks[i] == v), None)
    hi = next((i for i in range(b, min(tx.size, b + reach)) if tx.toks[i] == nxt), None)
    return lo, hi


def locate(tx: Text, verse: dict, loc: dict) -> dict:
    """Best window for one verse. ``verse``: King James words, Young's words, the neighbours'
    content stems, the verse number. Around each occurrence of the verse's rarest words (in
    either version) a window of about the King James verse's length is placed where that word
    sits in the verse; the neighbours' words are looked for just outside it. Found when the
    cover and context bars are met."""
    n = tx.n
    kw = verse["kjv"]
    denom = set(content(kw, n))
    want = denom | set(content(verse["ylt"], n))
    total = sum(tx.weight(s) for s in denom) or 1.0
    width = max(int(len(kw) * loc["span_factor"]), 8)
    slack = (width - len(kw)) // 2
    centres = anchors(tx, verse["ylt"], loc) | anchors(tx, kw, loc)
    best = None
    for c, rel in sorted(centres.items()):
        st = max(0, c - int(rel * len(kw)) - slack)
        hits = [i for i in range(st, min(tx.size, st + width)) if tx.stems[i] in want]
        cov = min(1.0, sum(tx.weight(s) for s in {tx.stems[i] for i in hits}) / total)
        if best is not None and cov + loc["context_weight"] + loc["number_bonus"] <= best["score"]:
            continue
        a, b = (hits[0], hits[-1] + 1) if hits else (c, c + 1)
        ctx = []
        for side, stems in (("prev", verse["prev"]), ("next", verse["next"])):
            if stems:
                span = (
                    (a - loc["context_words"], a)
                    if side == "prev"
                    else (b, b + loc["context_words"])
                )
                ctx.append(tx.cover(stems, stems, *span))
        context = sum(ctx) / len(ctx) if ctx else 0.0
        lo, hi = numbers(tx, verse, a, b, loc["number_reach"])
        bonus = loc["number_bonus"] * ((lo is not None) + (hi is not None))
        score = cov + loc["context_weight"] * context + bonus
        if best is None or score > best["score"]:
            best = {"score": score, "cover": cov, "context": context, "span": (a, b),
                    "numbers": (lo, hi)}  # fmt: skip
    if best is None:
        return {"found": False, "cover": 0.0, "context": 0.0}
    pl, pr = pads(kw, loc)
    a, b = extend(tx, *best["span"], want, loc["pad_cap"], len(kw) // 2)
    lo, hi = best.pop("numbers")
    start, end = max(0, a - pl), min(tx.size, b + pr)
    # A printed number only widens the span (some print them in the margin, inside the verse).
    best["span"] = (min(start, lo + 1) if lo is not None else start,
                    max(end, hi) if hi is not None else end)  # fmt: skip
    best["printed_numbers"] = [lo is not None, hi is not None]
    best["found"] = best["cover"] >= loc["min_cover"] and best["context"] >= loc["min_context"]
    return best


# ----------------------------------------------------------------------------- texts


def bible_verses() -> tuple[dict[str, str], dict[str, str], list[str]]:
    """King James and Young's Old Testament by OSIS reference, and the King James order."""
    from lab import translation2 as T2

    kjv = T2.kjv_verses()
    ylt = T2.ylt_verses(YLT) or {}
    return kjv, {k: v for k, v in ylt.items() if k.split(".")[0] in T2.OT_OSIS}, list(kjv)


def verse_specs(pl: list[dict], kjv_ref: dict, kjv: dict, ylt: dict, order: list[str], n: int):
    pos = {r: i for i, r in enumerate(order)}
    res = {}
    for p in pl:
        ref = kjv_ref[p["id"]]
        i = pos[ref]
        prev = set(content(tokens(kjv[order[i - 1]]), n)) if i > 0 else set()
        nxt = set(content(tokens(kjv[order[i + 1]]), n)) if i + 1 < len(order) else set()
        res[p["id"]] = {
            "ref": ref,
            "kjv": tokens(kjv[ref]),
            "ylt": tokens(ylt.get(ref, "")),
            "prev": prev,
            "next": nxt,
            "number": int(ref.split(".")[2]),
            "next_number": int(order[i + 1].split(".")[2]) if i + 1 < len(order) else 0,
        }
    return res


def read_text(spec: dict) -> str | None:
    try:
        t = "\n".join(Path(p).read_text("utf-8", "replace") for p in spec["paths"])
    except OSError:
        return None  # not attempted, never zero
    if spec.get("ot_end"):
        m = re.search(spec["ot_end"], t, flags=re.M)
        if m:
            t = t[: m.start()]
    return t


def in_books(p: dict, books, kjv_ref: dict) -> bool:
    return books == "OT" or kjv_ref[p["id"]].split(".")[0] in books


def score_text(tx: Text, pl, specs, kjv_ref, books, loc, order: list[str], reader) -> dict:
    """Each place in the volume's books: located, classified; a located place whose position
    breaks the canonical order of the others is flagged (a sign it may have been misplaced)."""
    rows, at = {}, {}
    for p in pl:
        if not in_books(p, books, kjv_ref):
            continue
        hit = locate(tx, specs[p["id"]], loc)
        row = {"cover": round(hit["cover"], 3), "context": round(hit["context"], 3)}
        if hit["found"]:
            a, b = hit["span"]
            words = " ".join(reader.read(tx.toks[a:b]))
            cls, rend = classify(words, p["kind"])
            row |= {"class": cls, "rendering": rend}
            if cls == "OTHER":
                row["one_parent_word"] = bool(FATHER.search(words)) != bool(MOTHER.search(words))
            at[p["id"]] = a
        else:
            row |= {"class": "NOT_FOUND", "rendering": None}
        rows[p["id"]] = row
    pos = {r: i for i, r in enumerate(order)}
    by_book: dict[str, list[str]] = defaultdict(list)
    for k in sorted(at, key=lambda k: (pos[kjv_ref[k]], k)):
        by_book[kjv_ref[k].split(".")[0]].append(k)
    for seq in by_book.values():  # books may be printed in another order; verses within one may not
        keep = set(increasing(seq, at))
        for k in seq:
            if k not in keep:
                rows[k] |= {"placed_class": rows[k]["class"], "class": "NOT_FOUND",
                            "reason": "out of order within its book"}  # fmt: skip
    return rows


def recheck(tx: Text, rows: dict, specs: dict, reader, loc: dict) -> list[dict]:
    """Each "parent(s)" in the volume set against the places left NOT_FOUND or OTHER: the share
    of that verse's content found within ``recheck_reach`` words of it. A share at or above
    ``recheck_cover`` means a PARENTS rendering there cannot be ruled out."""
    hits = [i for i, x in enumerate(tx.toks) if reader.variant(x) in ("parent", "parents")]
    res = []
    for pid, r in rows.items():
        if r["class"] not in ("NOT_FOUND", "OTHER"):
            continue
        v = specs[pid]
        denom = set(content(v["kjv"], tx.n))
        want = denom | set(content(v["ylt"], tx.n))
        best = max((tx.cover(want, denom, i - loc["recheck_reach"], i + loc["recheck_reach"])
                    for i in hits), default=0.0)  # fmt: skip
        if best >= loc["recheck_cover"]:
            res.append({"place": pid, "cover": round(best, 3)})
    return res


def increasing(seq: list[str], at: dict[str, int]) -> list[str]:
    """The longest run of ``seq`` (canonical order) whose text positions do not decrease."""
    best: list[list[str]] = []
    for k in seq:
        chain = max((c for c in best if at[c[-1]] <= at[k]), key=lambda c: (len(c), -at[c[-1]]),
                    default=[])  # fmt: skip
        best.append([*chain, k])
    return max(best, key=lambda c: (len(c), -at[c[-1]]), default=[])


def summary(rows: dict) -> dict:
    by = Counter(r["class"] for r in rows.values())
    pair = Counter(r["class"] for k, r in rows.items() if k.split(":")[1] in PAIR_KINDS)
    part = Counter(r["class"] for k, r in rows.items() if k.split(":")[1] not in PAIR_KINDS)
    found = len(rows) - by["NOT_FOUND"]
    return {
        "places_in_volume": len(rows),
        "located": found,
        "coverage": round(found / len(rows), 3) if rows else None,
        "classes": dict(by),
        "pair_and_parallel": dict(pair),
        "participle_places": dict(part),
        "parents_at_places": by["PARENTS"],
        "out_of_order": sum("placed_class" in r for r in rows.values()),
        "other_with_one_parent_word": sum(bool(r.get("one_parent_word")) for r in rows.values()),
    }


def read_whole(text: str, ctx: dict) -> str:
    """The text with OCR variants of the parent words and long-s misreadings read as words."""

    def word(m: re.Match) -> str:
        x = ctx["long_s"](m.group(0).lower())
        return ctx["reader"].variant(x) or x

    return re.sub(r"[A-Za-z]+", word, re.sub(r"-\s*\n\s*", "", text.replace("ſ", "s")))


def pair_counts(text: str, pairs: dict) -> dict:
    from lab.hebrewvocab import pairings

    return pairings(text, {"parents": pairs["parents"]})["parents"] | {"words": len(tokens(text))}


# ----------------------------------------------------------------------------- check and run


def prepare(cfg: dict) -> dict:
    from lab import translation2 as T2

    w = cfg["lab"]["hebrew_translators"]
    heb = T2.hebrew_verses()
    full, _partial = T2.verse_map()
    pl = places(w)
    pcheck, kjv_ref = check_places(pl, heb, full, w)
    kjv, ylt, order = bible_verses()
    specs = verse_specs(pl, kjv_ref, kjv, ylt, order, w["locator"]["stem_len"])
    return {"w": w, "pl": pl, "pcheck": pcheck, "kjv_ref": kjv_ref, "kjv": kjv, "ylt": ylt,
            "order": order, "specs": specs, "reader": (r := load_reader(w)),
            "long_s": long_s(r.counts, w["ocr"]["long_s_ratio"])}  # fmt: skip


def hand_class(pid: str, w: dict) -> str:
    for cls, ids in w["kjv_hand"].items():
        if pid in ids:
            return cls
    return "FATHER_AND_MOTHER" if pid.split(":")[1] in PAIR_KINDS else "PARTICIPLE"


def clean_rows(ctx: dict, which: str) -> dict:
    """Classes at every place read from a clean, verse-numbered text."""
    src = ctx["kjv"] if which == "kjv" else ctx["ylt"]
    rows = {}
    for p in ctx["pl"]:
        t = src.get(ctx["kjv_ref"][p["id"]])
        if t is None:
            rows[p["id"]] = {"class": "NOT_FOUND", "rendering": None}
            continue
        cls, rend = classify(" ".join(ctx["reader"].read(tokens(t))), p["kind"])
        rows[p["id"]] = {"class": cls, "rendering": rend}
    return rows


def stream_check(ctx: dict, which: str, words_from: str = "both") -> dict:
    """The locator on a clean Old Testament flattened to one stream with no verse numbers: is
    every place found inside its true verse?"""
    src = ctx["kjv"] if which == "kjv" else ctx["ylt"]
    loc = ctx["w"]["locator"]
    toks, starts = [], {}
    for ref in ctx["order"]:
        if ref in src:
            a = len(toks)
            toks += [x for x in tokens(src[ref]) if not x.isdigit()]
            starts[ref] = (a, len(toks))
    tx = Text(" ".join(toks), loc["stem_len"])
    bad, found, elsewhere = [], 0, 0
    for p in ctx["pl"]:
        spec = dict(ctx["specs"][p["id"]])
        if words_from == "ylt":
            spec["kjv"] = spec["ylt"] or spec["kjv"]
            spec["ylt"] = []
        elif words_from == "kjv":
            spec["ylt"] = []
        hit = locate(tx, spec, loc)
        a, b = starts.get(ctx["kjv_ref"][p["id"]], (0, 0))
        ok = hit["found"] and hit["span"][0] < b and hit["span"][1] > a and _centre_in(hit, a, b)
        found += ok
        elsewhere += hit["found"] and not ok
        if not ok:
            bad.append(
                {
                    "place": p["id"],
                    "found_elsewhere": hit["found"],
                    "cover": round(hit["cover"], 3),
                    "context": round(hit["context"], 3),
                }
            )
    return {"places": len(ctx["pl"]), "found_in_true_verse": found,
            "found_in_wrong_verse": elsewhere, "missed": bad}  # fmt: skip


def _centre_in(hit: dict, a: int, b: int) -> bool:
    lo, hi = hit["span"]
    return a <= (lo + hi) // 2 < b


def check(cfg: dict) -> tuple[dict, dict]:
    ctx = prepare(cfg)
    w = ctx["w"]
    kj = clean_rows(ctx, "kjv")
    wrong = [
        {"place": k, "rule": r["class"], "hand": hand_class(k, w)}
        for k, r in kj.items()
        if r["class"] != hand_class(k, w)
    ]
    yid, ywant = w["young_check"]
    yl = clean_rows(ctx, "ylt")
    s_kjv, s_ylt = stream_check(ctx, "kjv"), stream_check(ctx, "ylt")
    res = {
        "places": ctx["pcheck"],
        "king_james_rule_vs_hand": {
            "places": len(kj),
            "agree": len(kj) - len(wrong),
            "disagree": wrong,
        },  # fmt: skip
        "young_zech_13_3": {
            "place": yid,
            "want": ywant,
            "got": yl[yid]["class"],
            "rendering": yl[yid]["rendering"],
        },  # fmt: skip
        "locator_king_james_stream": s_kjv,
        "locator_young_stream": s_ylt,
        "reported_not_bars": {
            "locator_king_james_stream_young_words_only": stream_check(ctx, "kjv", "ylt"),
            "locator_young_stream_king_james_words_only": stream_check(ctx, "ylt", "kjv"),
        },
    }
    res["pass"] = bool(
        ctx["pcheck"]["pass"]
        and not wrong
        and yl[yid]["class"] == ywant
        and s_kjv["found_in_true_verse"] == s_kjv["places"]
        and s_ylt["found_in_true_verse"] == s_ylt["places"]
    )
    return res, ctx


def book_numbers() -> dict | None:
    try:
        p = json.loads(RESULT3.read_text())["pairings"]
    except (OSError, KeyError, ValueError):
        return None
    return {"pre_christian": p["book_pre_christian"]["parents"],
            "3_nephi": p["book_3_nephi"]["parents"], "source": str(RESULT3)}  # fmt: skip


def run(cfg: dict) -> dict:
    chk, ctx = check(cfg)
    if not chk["pass"]:
        return {"check": chk, "stopped": "the known-answer check missed; nothing scored"}
    w = ctx["w"]
    pairs = cfg["lab"]["hebrew_vocabulary"]["pairs"]
    loc = w["locator"]
    translators, missing = {}, []
    for name, spec in w["texts"].items():
        meta = {k: spec[k] for k in ("translator", "year", "source")}
        if spec.get("clean"):
            rows = clean_rows(ctx, spec["clean"])
            src = ctx["kjv"] if spec["clean"] == "kjv" else ctx["ylt"]
            text = "\n".join(src.values())
            meta["text"] = "clean, verse-numbered (Old Testament only)"
        else:
            text = read_text(spec)
            if text is None:
                missing.append(name)
                continue
            meta["text"] = "OCR volume(s), notes and prefaces included in the whole-text count"
            rows = None
            if spec["source"] != "post_biblical":
                tx = Text(text, loc["stem_len"], ctx["long_s"])
                rows = score_text(
                    tx,
                    ctx["pl"],
                    ctx["specs"],
                    ctx["kjv_ref"],
                    spec["books"],
                    loc,
                    ctx["order"],
                    ctx["reader"],
                )
                meta["parents_near_unresolved_places"] = recheck(
                    tx, rows, ctx["specs"], ctx["reader"], loc
                )
        entry = meta | {
            "whole_text": pair_counts(text, pairs),
            "whole_text_ocr_read": pair_counts(read_whole(text, ctx), pairs),
        }
        if rows is not None:
            entry |= {"books": spec["books"], "summary": summary(rows), "places": rows}
        translators[name] = entry
    return {
        "check": chk,
        "translators": translators,
        "not_attempted": missing,
        "not_fetched": w.get("not_fetched", {}),
        "recheck_read_by_hand": w.get("recheck_read_by_hand", {}),
        "book_of_mormon": book_numbers(),
        "rules": {
            "pair_place": "FATHER_AND_MOTHER > PARENTS > PARTICIPLE > OTHER",
            "participle_place": "PARENTS > PARTICIPLE > FATHER_AND_MOTHER > OTHER",
            "whole_text_pairs": pairs["parents"],
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "check":
        res, _ctx = check(cfg)
        res["stamp"] = config.stamp()
        out(OUT / "check.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res, indent=1)[:4000])
        return 0
    res = run(cfg)
    res["stamp"] = config.stamp()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    for name, t in res.get("translators", {}).items():
        print(name, json.dumps(t.get("summary", {}).get("classes")), json.dumps(t["whole_text"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
