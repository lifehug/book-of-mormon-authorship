"""BOM-125: the book's size and complexity against other long dictated or "received" texts (Hales).

Hales (2019) argues the Book of Mormon is out of reach for a dictated text. His table compares
only length and schooling; this measures a fixed set of simple, stated measures on the 1830 text,
on 23 long texts that were dictated or claimed as received (public domain: printed before 1930),
on three controls (Bible-style books of 1810-1829, genuine translations, Joseph Smith's other
dictations) and on a seeded sample of ordinary long library books of 1790-1829. Every text is
cut into windows of exactly ``sample_words`` words (a text shorter than the window is "too short
at this size", never a zero) and scored on: vocabulary (distinct words, a growth curve, MATTR),
named entities (capitalised words not at a sentence start, persons and places together), sentence
and clause length, Flesch-Kincaid grade, call-backs (second-half words covered by a six-word string
from the first half) and borrowing from the King James text. A known-answer check comes first
(graded readers and Gibbon for the vocabulary, sentence and reading measures; King James books
against Theographic's person and place counts for names; planted call-backs and planted King James
verses); a measure that misses its bar is dropped, and the run stops only if none pass. The test
card, written first, is ``data/private/lab/owner/2026-11-21-dictated-texts/card.md``; settings are
``lab.dictated`` in the config. The result holds names and numbers, no text.

Usage::

    python -m lab.dictated check    # known-answer check only (prints it)
    python -m lab.dictated run      # -> data/lab/reruns/dictated_texts/result.json
    python -m lab.dictated run-added  # with the texts added later -> result_added.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.compute as pc

from lab import door, registry, twovoices
from lab.paths import FAST, REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "dictated_texts"
EDITION = Path("data/bom/1830/edition_1830.jsonl")
KJV = Path("data/kjv/kjv.jsonl")
TOK = re.compile(r"[A-Za-z]+|[.!?;:]")
VOWELS = re.compile(r"[aeiouy]+")
BOILER = re.compile(r"project gutenberg|forgotten books|digitized by|www\.|archive\.org", re.I)
MEASURES = [
    "types_5000",
    "types_10000",
    "types_20000",
    "mattr",
    "names_all",
    "names_rep2",
    "sentence_len",
    "clause_len",
    "fk_grade",
    "callbacks",
    "kjv_share",
]


# ------------------------------------------------------------------------------ cleaning


def clean(text: str, cfg: dict, verse: bool = False) -> str:
    """The text between the Project Gutenberg markers, without running heads, page numbers,
    boilerplate lines or line-break hyphens; with ``verse`` a line that continues a sentence does
    not start with a capital (so line starts are not read as names)."""
    t = cfg["lab"]["dictated"]
    m = re.search(r"\*\*\* ?START OF [^\n]*\n", text)
    if m:
        text = text[m.end() :]
    m = re.search(r"\*\*\* ?END OF ", text)
    if m:
        text = text[: m.start()]
    keep: list[str] = []
    prev = ""
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.isdigit() or BOILER.search(s):
            continue
        letters = [c for c in s if c.isalpha()]
        if (
            letters
            and len(s.split()) <= t["header_max_words"]
            and sum(c.isupper() for c in letters) / len(letters) >= t["header_upper_share"]
        ):
            continue
        if verse and prev and prev[-1] not in ".!?" and s[0].isupper():
            s = s[0].lower() + s[1:]
        keep.append(s)
        prev = s
    joined = "\n".join(keep)
    joined = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", joined)
    return joined.replace("\n", " ")


class Doc:
    """One cleaned text as parallel lists: raw words, lower-case words (long-s repaired) and the
    sentence mark that follows each word (``s`` after ``. ! ?``, ``c`` after ``; :``, else '')."""

    def __init__(self, text: str, vocab: set[str]):
        raw: list[str] = []
        mark: list[str] = []
        for tok in TOK.findall(text):
            if tok[0].isalpha():
                raw.append(tok)
                mark.append("")
            elif raw:
                m = "s" if tok in ".!?" else "c"
                if mark[-1] != "s":
                    mark[-1] = m
        low, _ = twovoices.tokens(" ".join(raw), vocab)
        # ``tokens`` splits at non-letters only, so it is aligned with ``raw``
        if len(low) != len(raw):  # defensive: a mismatch is "not attempted", never a guess
            raise ValueError("tokenisers disagree")
        self.raw, self.low, self.mark = raw, low, mark

    def __len__(self) -> int:
        return len(self.raw)


# ------------------------------------------------------------------------------ measures


def syllables(w: str) -> int:
    n = len(VOWELS.findall(w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(n, 1)


def mattr_value(low: list[str], size: int) -> float:
    """Mean over every window of ``size`` consecutive words of distinct words / ``size``."""
    if len(low) < size:
        return float("nan")
    cnt: Counter = Counter(low[:size])
    distinct = len(cnt)
    acc, n = distinct, 1
    for i in range(size, len(low)):
        gone, new = low[i - size], low[i]
        cnt[gone] -= 1
        if cnt[gone] == 0:
            del cnt[gone]
            distinct -= 1
        if cnt[new] == 0:
            distinct += 1
        cnt[new] += 1
        acc += distinct
        n += 1
    return acc / (n * size)


def names(raw: list[str], mark: list[str], t: dict) -> tuple[int, int]:
    """(distinct names, names seen at least ``name_min_repeats`` times): capitalised words (rest
    lower-case, at least ``name_min_len`` letters) not at a sentence start and never seen lower
    case in the window."""
    cnt: Counter = Counter()
    seen_lower = {w for w in raw if w.islower()}
    for i, w in enumerate(raw):
        if (
            i > 0
            and mark[i - 1] != "s"
            and len(w) >= t["name_min_len"]
            and w[0].isupper()
            and w[1:].islower()
            and w.lower() not in seen_lower
        ):
            cnt[w] += 1
    return len(cnt), sum(1 for c in cnt.values() if c >= t["name_min_repeats"])


def covered(low: list[str], grams: set[str], n: int, lo: int = 0, hi: int | None = None) -> int:
    """Positions in ``low[lo:hi]`` covered by an n-word string that is in ``grams``."""
    hi = len(low) if hi is None else hi
    cover = bytearray(hi - lo)
    for i in range(lo, hi - n + 1):
        if " ".join(low[i : i + n]) in grams:
            for j in range(i - lo, i - lo + n):
                cover[j] = 1
    return sum(cover)


def callbacks(low: list[str], n: int) -> float:
    half = len(low) // 2
    first = {" ".join(low[i : i + n]) for i in range(0, half - n + 1)}
    return covered(low, first, n, half, len(low)) / (len(low) - half)


def window_scores(raw, low, mark, cfg: dict, grams: set[str]) -> dict:
    t = cfg["lab"]["dictated"]
    n = len(low)
    res: dict[str, float] = {}
    for k in t["types_at"]:
        res[f"types_{k}"] = float(len(set(low[:k]))) if k <= n else float("nan")
    res["mattr"] = mattr_value(low, t["mattr_window"])
    res["names_all"], res["names_rep2"] = (float(x) for x in names(raw, mark, t))
    ends = [i for i, m in enumerate(mark) if m == "s"]
    cl = [i for i, m in enumerate(mark) if m]
    res["sentence_len"] = _mean_gap(ends)
    res["clause_len"] = _mean_gap(cl)
    sent = max(len(ends), 1)
    syl = sum(syllables(w) for w in low)
    res["fk_grade"] = 0.39 * n / sent + 11.8 * syl / n - 15.59
    res["callbacks"] = callbacks(low, t["callback_gram"])
    res["kjv_share"] = covered(low, grams, t["kjv_ngram"]) / n
    return res


def _mean_gap(idx: list[int]) -> float:
    if len(idx) < 2:
        return float("nan")
    return (idx[-1] - idx[0]) / (len(idx) - 1)


def starts(length: int, size: int, head: float, tail: float, cap: int) -> list[int]:
    lo = int(length * head)
    hi = length - int(length * tail)
    room = hi - lo
    k = min(cap, room // size)
    if k < 1:
        return []
    if k == 1:
        return [lo + (room - size) // 2]
    return [lo + round(j * (room - size) / (k - 1)) for j in range(k)]


def score_doc(d: Doc, size: int, cfg: dict, grams: set[str], cap: int, trim: bool) -> dict:
    t = cfg["lab"]["dictated"]
    head, tail = (t["trim_head"], t["trim_tail"]) if trim else (0.0, 0.0)
    st = starts(len(d), size, head, tail, cap)
    if not st:
        return {"words": len(d), "too_short_at": size}
    rows = [
        window_scores(d.raw[a : a + size], d.low[a : a + size], d.mark[a : a + size], cfg, grams)
        for a in st
    ]
    means = {m: sum(r[m] for r in rows) / len(rows) for m in rows[0]}
    spread = {m: _sd([r[m] for r in rows]) for m in rows[0]}
    return {"words": len(d), "windows": len(rows), "mean": means, "sd": spread}


def _sd(xs: list[float]) -> float:
    if len(xs) < 2:
        return float("nan")
    mu = sum(xs) / len(xs)
    return (sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def ranks(xs: list[float]) -> list[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a: list[float], b: list[float]) -> float:
    ra, rb = ranks(a), ranks(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb, strict=True))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


def quantile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def percentile_of(xs: list[float], x: float) -> float:
    """Share of ``xs`` at or below ``x``, as a percentage."""
    return 100.0 * sum(1 for v in xs if v <= x) / len(xs)


# ------------------------------------------------------------------------------ texts


def read_files(files: list[str]) -> str:
    return "\n".join((FAST / f).read_text(errors="replace") for f in files)


def load_doc(files: list[str], cfg: dict, vocab: set[str], verse: bool = False) -> Doc:
    return Doc(clean(read_files(files), cfg, verse), vocab)


def book_doc(cfg: dict, vocab: set[str]) -> Doc:
    rows = [json.loads(x) for x in EDITION.read_text().splitlines()]
    text = " ".join(r["text"] for r in rows if r["kind"] == "body")
    return Doc(text, vocab)


def js_doc(cfg: dict, vocab: set[str]) -> Doc | None:
    """Joseph Smith's other dictations (private); None if unreadable (not attempted)."""
    parts: list[str] = []
    try:
        for pat in cfg["lab"]["dictated"]["js_files"]:
            p = Path(pat)
            for f in sorted(p.parent.glob(p.name)):
                for line in f.read_text(errors="replace").splitlines():
                    if not line.startswith("## "):
                        parts.append(line)
    except OSError:
        return None
    if not parts:
        return None
    return Doc(" ".join(parts), vocab)


def kjv_books() -> dict[str, str]:
    books: dict[str, list[str]] = defaultdict(list)
    for line in KJV.read_text().splitlines():
        r = json.loads(line)
        books[r["book_name"]].append(r["text"])
    return {b: " . ".join(v) for b, v in books.items()}


# ------------------------------------------------------------------------------ known answers


def check_order(cfg: dict, vocab: set[str], grams: set[str]) -> dict:
    t = cfg["lab"]["dictated"]
    size = t["check_size"]
    order = t["known_grade_order"]
    scores: dict[str, dict] = {}
    missing = {}
    for name in order:
        try:
            d = load_doc([t["known_files"][name]], cfg, vocab)
        except (OSError, ValueError) as e:
            missing[name] = str(e)
            continue
        s = score_doc(d, size, cfg, grams, t["max_windows"], True)
        if "mean" in s:
            scores[name] = s
        else:
            missing[name] = f"too short at {size} ({s['words']} words)"
    res: dict = {"texts": {k: {"words": v["words"], "mean": v["mean"]} for k, v in scores.items()}}
    res["not_attempted"] = missing
    res["spearman"] = {}
    names_ = [n for n in order if n in scores]
    grade = list(range(len(names_)))
    for m in ("types_5000", "mattr", "sentence_len", "clause_len", "fk_grade"):
        vals = [scores[n]["mean"][m] for n in names_]
        res["spearman"][m] = round(spearman(grade, vals), 4)
    res["passes"] = {m: v >= t["bar_order"] for m, v in res["spearman"].items()}
    return res


def theographic_counts(cfg: dict) -> dict[str, int]:
    d = Path(cfg["lab"]["dictated"]["theographic"])
    books = json.loads((d / "books.json").read_text())
    osis = {b["fields"]["osisName"]: b["fields"]["bookName"] for b in books}
    verses = json.loads((d / "verses.json").read_text())
    people = json.loads((d / "people.json").read_text())
    places = json.loads((d / "places.json").read_text())
    verse_book = {v["id"]: osis.get(v["fields"]["osisRef"].split(".")[0]) for v in verses}
    sets: dict[str, set] = defaultdict(set)
    for v in verses:
        b = verse_book[v["id"]]
        for pid in v["fields"].get("people", []):
            sets[b].add(("p", pid))
    for pl in places:
        for vid in pl["fields"].get("verses", []):
            b = verse_book.get(vid)
            if b:
                sets[b].add(("l", pl["id"]))
    del people
    return {b: len(s) for b, s in sets.items() if b}


def check_names(cfg: dict, vocab: set[str]) -> dict:
    t = cfg["lab"]["dictated"]
    theo = theographic_counts(cfg)
    ours: dict[str, tuple[int, int, int]] = {}
    for book, text in kjv_books().items():
        d = Doc(text, vocab)
        if len(d) < t["check_book_min_words"] or book not in theo:
            continue
        a, b = names(d.raw, d.mark, t)
        ours[book] = (len(d), a, b)
    keys = sorted(ours)
    lo, hi = t["bar_names_ratio"]
    res: dict = {"books": len(keys), "variants": {}}
    for i, v in ((1, "names_all"), (2, "names_rep2")):
        a = [ours[k][i] for k in keys]
        b = [theo[k] for k in keys]
        ratios = sorted(x / y for x, y in zip(a, b, strict=True) if y)
        rho = spearman(a, b)
        med = ratios[len(ratios) // 2]
        res["variants"][v] = {
            "spearman": round(rho, 4),
            "median_ratio": round(med, 4),
            "passes": rho >= t["bar_names_rho"] and lo <= med <= hi,
        }
    res["per_book"] = {k: {"words": ours[k][0], "ours_all": ours[k][1], "ours_rep2": ours[k][2],
                           "theographic": theo[k]} for k in keys}  # fmt: skip
    return res


def kjv_stream() -> list[str]:
    toks: list[str] = []
    for line in KJV.read_text().splitlines():
        toks.extend(re.findall(r"[a-z]+", json.loads(line)["text"].lower()))
    return toks


def plant(base: list[str], donor: list[str], t: dict, rng: random.Random, kind: str) -> list[str]:
    """``base`` with ``plant_spans`` stretches of ``plant_len`` words replaced: for "callback" by
    copies of stretches of its first half, put in the second half; for "kjv" by King James text,
    put anywhere. Stretches do not overlap."""
    n, ln = len(base), t["plant_len"]
    out_ = list(base)
    half = n // 2
    lo, hi = (half, n) if kind == "callback" else (0, n)
    slots = list(range(lo, hi - ln, ln * 2))
    rng.shuffle(slots)
    for pos in slots[: t["plant_spans"]]:
        src = rng.randrange(0, half - ln) if kind == "callback" else rng.randrange(len(donor) - ln)
        out_[pos : pos + ln] = (out_ if kind == "callback" else donor)[src : src + ln]
    return out_


def check_planted(cfg: dict, vocab: set[str], grams: set[str], seed: int) -> dict:
    t = cfg["lab"]["dictated"]
    size, rng = t["check_size"], random.Random(seed)
    donor = kjv_stream()
    lo, hi = t["bar_plant"]
    res: dict = {"hosts": {}}
    ok = {"callbacks": True, "kjv_share": True}
    for name in t["plant_hosts"]:
        d = load_doc([t["known_files"][name]], cfg, vocab)
        a = starts(len(d), size, t["trim_head"], t["trim_tail"], 1)
        if not a:
            res["hosts"][name] = {"not_attempted": "too short"}
            ok = dict.fromkeys(ok, False)
            continue
        base = d.low[a[0] : a[0] + size]
        rec = {}
        for kind, m in (("callback", "callbacks"), ("kjv", "kjv_share")):
            tries = []
            for _ in range(10):
                p = plant(base, donor, t, rng, kind)
                if m == "callbacks":
                    v0, v1 = callbacks(base, t["callback_gram"]), callbacks(p, t["callback_gram"])
                    got = (v1 - v0) * (size - size // 2) / (t["plant_spans"] * t["plant_len"])
                else:
                    c0 = covered(base, grams, t["kjv_ngram"])
                    c1 = covered(p, grams, t["kjv_ngram"])
                    got = (c1 - c0) / (t["plant_spans"] * t["plant_len"])
                tries.append(got)
            med = sorted(tries)[len(tries) // 2]
            rec[m] = {"recovered_median": round(med, 4), "runs": [round(x, 3) for x in tries]}
            if not lo <= med <= hi:
                ok[m] = False
        res["hosts"][name] = rec
    res["passes"] = ok
    return res


def known_answer(cfg: dict, vocab: set[str], grams: set[str]) -> dict:
    t = cfg["lab"]["dictated"]
    order = check_order(cfg, vocab, grams)
    nm = check_names(cfg, vocab)
    pl = check_planted(cfg, vocab, grams, t["seed"])
    keep = {
        "types_5000": order["passes"]["types_5000"],
        "types_10000": order["passes"]["types_5000"],
        "types_20000": order["passes"]["types_5000"],
        "mattr": order["passes"]["mattr"],
        "sentence_len": order["passes"]["sentence_len"],
        "clause_len": order["passes"]["clause_len"],
        "fk_grade": order["passes"]["fk_grade"],
        "names_all": nm["variants"]["names_all"]["passes"],
        "names_rep2": nm["variants"]["names_rep2"]["passes"],
        "callbacks": pl["passes"]["callbacks"],
        "kjv_share": pl["passes"]["kjv_share"],
    }
    return {"order": order, "names": nm, "planted": pl, "measure_passes": keep,
            "kept": [m for m, v in keep.items() if v],
            "dropped": [m for m, v in keep.items() if not v]}  # fmt: skip


# ------------------------------------------------------------------------------ library


def library_rows(cfg: dict) -> tuple[list[dict], dict]:
    t = cfg["lab"]["dictated"]
    tab = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(tab["kind"], "work"), pc.equal(tab["author_kind"], "person")),
        pc.and_(pc.equal(tab["has_text"], True), pc.equal(tab["dup_keeper"], True)),
    )
    rows = [
        r
        for r in tab.filter(keep).to_pylist()
        if not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and t["library_year_min"] <= r["year"] <= t["library_year_max"]
        and (r["words"] or 0) >= t["library_min_words"]
    ]
    cover: Counter = Counter((r["year"] // 10) * 10 for r in rows)
    rows.sort(key=lambda r: r["work_id"])
    random.Random(t["seed"]).shuffle(rows)
    return rows, {str(k): v for k, v in sorted(cover.items())}


def library_scores(cfg: dict, vocab: set[str], grams: set[str], size: int, rows: list[dict]):
    t = cfg["lab"]["dictated"]
    cat = door.catalog({r["work_id"] for r in rows[: t["library_sample"] * 3]})
    res: dict[str, dict] = {}
    failed: dict[str, str] = {}
    used = 0
    for r in rows[: t["library_sample"] * 3]:
        if used >= t["library_sample"]:
            break
        c = cat.get(r["work_id"])
        if not c or not c["text_path"]:
            continue
        try:
            d = Doc(clean(door.text_of({**c, **r}), cfg), vocab)
        except (OSError, ValueError) as e:
            failed[r["work_id"]] = str(e)  # unreadable: not attempted, never a result
            continue
        used += 1
        s = score_doc(d, size, cfg, grams, t["library_max_windows"], True)
        if "mean" in s:
            res[r["work_id"]] = {"year": r["year"], "words": s["words"], "mean": s["mean"]}
    return res, failed


# ------------------------------------------------------------------------------ the run


def position(book: dict, received: dict, measure: str) -> dict:
    vals = {k: v["mean"][measure] for k, v in received.items() if "mean" in v}
    b = book["mean"][measure]
    ordered = sorted(vals.values())
    return {
        "book": round(b, 4),
        "received_min": round(ordered[0], 4),
        "received_median": round(quantile(ordered, 0.5), 4),
        "received_max": round(ordered[-1], 4),
        "n_received": len(ordered),
        "rank_among_received_1_is_highest": 1 + sum(1 for v in vals.values() if v > b),
        "outside_received": b > ordered[-1] or b < ordered[0],
        "side": "above" if b > ordered[-1] else "below" if b < ordered[0] else "inside",
    }


def run(cfg: dict, check_only: bool = False, added: bool = False) -> dict:
    t = cfg["lab"]["dictated"]
    vocab, grams = twovoices.kjv_vocab_and_grams(t["kjv_ngram"])
    ka = known_answer(cfg, vocab, grams)
    if check_only or not ka["kept"]:
        return {"known_answer": ka, "scored": False}
    book = book_doc(cfg, vocab)
    bom_full = whole_book(book, cfg)
    docs, missing = {}, {}
    received = dict(t["received"])
    if added:
        received.update(t.get("received_added", {}))
    for name, (role, verse, files) in received.items():
        try:
            docs[name] = (role, load_doc(files, cfg, vocab, bool(verse)))
        except (OSError, ValueError) as e:
            missing[name] = str(e)
    ctrl_bible: dict[str, Doc] = {}
    for rel in cfg["lab"]["voices"]["bible_style_files"]:
        p = Path(rel)
        nm = p.parent.name if p.stem == "text" else p.stem
        try:
            ctrl_bible[nm] = load_doc([rel], cfg, vocab)
        except (OSError, ValueError) as e:
            missing[nm] = str(e)
    ctrl_trans: dict[str, Doc] = {}
    for nm, files in t["translations"].items():
        try:
            ctrl_trans[nm] = load_doc(files, cfg, vocab)
        except (OSError, ValueError) as e:
            missing[nm] = str(e)
    js = js_doc(cfg, vocab)
    rows, cover = library_rows(cfg)
    sizes: dict = {}
    for size in t["sample_sizes"]:
        S = {}
        S["book"] = score_doc(book, size, cfg, grams, t["max_windows"], False)
        S["received"] = {
            n: {**score_doc(d, size, cfg, grams, t["max_windows"], True), "role": role}
            for n, (role, d) in docs.items()
        }
        S["bible_style"] = {
            n: score_doc(d, size, cfg, grams, t["max_windows"], True) for n, d in ctrl_bible.items()
        }
        S["translations"] = {
            n: score_doc(d, size, cfg, grams, t["max_windows"], True) for n, d in ctrl_trans.items()
        }
        S["joseph_smith_dictations"] = (
            score_doc(js, size, cfg, grams, t["max_windows"], False)
            if js
            else {"not_attempted": "unreadable or absent"}
        )
        lib, failed = library_scores(cfg, vocab, grams, size, rows)
        S["library"] = {"scored": len(lib), "not_attempted": failed, "works": lib}
        S["positions"] = positions(S, ka["kept"]) if "mean" in S["book"] else {}
        sizes[str(size)] = S
    main = sizes[str(t["sample_sizes"][0])]
    return {
        "known_answer": ka,
        "scored": True,
        "hales_reproduction": bom_full,
        "sizes": sizes,
        "verdict": verdict(main, ka["kept"], cfg),
        "library_coverage_by_decade": cover,
        "not_attempted": missing,
        "lengths": lengths(docs, book, ctrl_bible, ctrl_trans, js),
    }


def lengths(docs, book, bible, trans, js) -> dict:
    return {
        "book": len(book),
        "received": {n: len(d) for n, (_r, d) in docs.items()},
        "bible_style": {n: len(d) for n, d in bible.items()},
        "translations": {n: len(d) for n, d in trans.items()},
        "joseph_smith_dictations": len(js) if js else None,
    }


def whole_book(book: Doc, cfg: dict) -> dict:
    """Hales's figures for the 1830 text under stated definitions (whole text, not windowed)."""
    t = cfg["lab"]["dictated"]
    a, b = names(book.raw, book.mark, t)
    ends = sum(1 for m in book.mark if m == "s")
    n = len(book)
    syl = sum(syllables(w) for w in book.low)
    return {
        "definitions": "1830 body text; words = letter strings; distinct words = lower-case "
        "types after long-s repair; names = capitalised words not at a sentence start, never "
        "seen lower case; grade = Flesch-Kincaid with 1830 punctuation",
        "words": n,
        "distinct_words": len(set(book.low)),
        "names_all": a,
        "names_seen_twice": b,
        "sentences": ends,
        "fk_grade": round(0.39 * n / max(ends, 1) + 11.8 * syl / n - 15.59, 2),
        "hales_reported": t["hales"],
    }


def positions(S: dict, kept: list[str]) -> dict:
    book = S["book"]
    res = {}
    for m in kept:
        pos = position(book, S["received"], m)
        lib = [v["mean"][m] for v in S["library"]["works"].values() if v["mean"][m] == v["mean"][m]]
        if lib:
            pos["library_n"] = len(lib)
            pos["library_percentile_of_book"] = round(percentile_of(lib, book["mean"][m]), 1)
            pos["library_p5_p50_p95"] = [round(quantile(lib, q), 4) for q in (0.05, 0.5, 0.95)]
        ctrl = {}
        for grp in ("bible_style", "translations"):
            ctrl[grp] = {k: round(v["mean"][m], 4) for k, v in S[grp].items() if "mean" in v}
        js = S["joseph_smith_dictations"]
        ctrl["joseph_smith_dictations"] = round(js["mean"][m], 4) if "mean" in js else None
        pos["controls"] = ctrl
        res[m] = pos
    return res


def verdict(S: dict, kept: list[str], cfg: dict) -> dict:
    t = cfg["lab"]["dictated"]
    book = S["book"]
    if "mean" not in book:
        return {"answer": "cannot tell", "why": "the book is too short at this size"}
    scored = {n: v for n, v in S["received"].items() if "mean" in v}
    judged = [m for m in kept if m in MEASURES]
    out_ = []
    for m in judged:
        pos = position(book, scored, m)
        out_.append((m, pos["outside_received"], pos["side"]))
    n_out = sum(1 for _m, o, _s in out_ if o)
    n = len(out_)
    if len(scored) < t["min_received"] or n == 0:
        ans = "cannot tell"
    elif n_out >= 3 and n_out / n >= t["outside_share"]:
        ans = "outside"
    elif n_out / n <= t["inside_share"]:
        ans = "inside"
    else:
        ans = "mixed"
    names_ = list(scored)
    log_len = [_log(scored[k]["words"]) for k in names_]
    corr = {}
    for m in judged:
        vals = [scored[k]["mean"][m] for k in names_]
        corr[m] = {
            "spearman_with_length": round(spearman(vals, log_len), 3),
            "spearman_with_kjv_share": round(
                spearman(vals, [scored[k]["mean"]["kjv_share"] for k in names_]), 3
            )
            if "kjv_share" in kept
            else None,
        }
    return {
        "answer": ans,
        "measures_judged": judged,
        "outside": {m: s for m, o, s in out_ if o},
        "inside": [m for m, o, _s in out_ if not o],
        "n_received_scored": len(scored),
        "tracking_across_received": corr,
    }


def _log(x: float) -> float:
    return math.log(x)


def _strip(o):
    if isinstance(o, float) and o != o:
        return None
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_strip(v) for v in o]
    return o


def _commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["check", "run", "run-added"])
    a = ap.parse_args(argv)
    cfg = config.load()
    res = run(cfg, check_only=a.command == "check", added=a.command == "run-added")
    res["config_sha256"] = config.sha256_of_config()
    res["git_commit"] = _commit()
    res["rule_set"] = "everything (named texts); library background by registry filter"
    text = json.dumps(_strip(res), indent=1, ensure_ascii=False)
    if a.command == "check":
        print(json.dumps(_strip(res["known_answer"]["measure_passes"]), indent=1))
        out(OUT / "check.json").write_text(text)
        return 0
    name = "result_added.json" if a.command == "run-added" else "result.json"
    if a.command == "run-added":
        res["added_texts"] = sorted(cfg["lab"]["dictated"].get("received_added", {}))
        res["added_note"] = (
            "texts added after the first result (owner, 2026-11-23); result.json unchanged"
        )
        text = json.dumps(_strip(res), indent=1, ensure_ascii=False)
    out(OUT / name).write_text(text)
    print(f"wrote {OUT / name}; verdict: {res.get('verdict', {}).get('answer')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
