"""BOM-120: "therefore" and "wherefore" through the Book of Mormon, in two orders, with a baseline.

Metcalfe (1993) observed that "therefore" dominates from Mosiah to Moroni and "wherefore" from
Ether through the small plates, which follows the proposed order of dictation. This counts the
two words in consecutive blocks, fits one break (two binomial rates) in printed and in dictation
order, compares that with one rate per narrator, and runs the same one-break fit on a sample of
long single-author works in the library to learn how common so sharp a switch is. The test card,
written first, is ``data/private/lab/owner/2026-11-20-therefore-wherefore/card.md``; settings are
``lab.wherefore`` in the config. The output holds counts and statistics, no text.

Usage::

    python -m lab.wherefore check     # known-answer check: planted breaks in spliced works
    python -m lab.wherefore run       # -> data/lab/reruns/mosiah_priority/result.json
    python -m lab.wherefore metcalfe  # his tables recounted -> .../mosiah_priority/metcalfe.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import subprocess
from pathlib import Path

import pyarrow.compute as pc

from lab import door, registry
from lab.paths import REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "mosiah_priority"
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
WORD = re.compile(r"[a-z]+")
SMALL = {"Nephi", "Jacob", "Enos", "Jarom", "Omni", "Amaron", "Chemish", "Abinadom", "Amaleki"}


def blocks(words: list[str], size: int) -> list[tuple[int, int]]:
    """(wherefore, therefore) counts in consecutive blocks of ``size`` words."""
    rows = []
    for i in range(0, len(words), size):
        part = words[i : i + size]
        rows.append((part.count("wherefore"), part.count("therefore")))
    return rows


def _ll(w: int, t: int) -> float:
    n = w + t
    if n == 0 or w == 0 or t == 0:
        return 0.0
    return w * math.log(w / n) + t * math.log(t / n)


def one_break(rows: list[tuple[int, int]]) -> dict:
    """The split maximising the two-rate binomial likelihood; deviance against one rate."""
    tw, tt = sum(r[0] for r in rows), sum(r[1] for r in rows)
    base, best, w, t = _ll(tw, tt), None, 0, 0
    for k in range(1, len(rows)):
        w, t = w + rows[k - 1][0], t + rows[k - 1][1]
        if w + t == 0 or (tw - w) + (tt - t) == 0:
            continue
        ll = _ll(w, t) + _ll(tw - w, tt - t)
        if best is None or ll > best[0]:
            best = (ll, k, w / (w + t), (tw - w) / ((tw - w) + (tt - t)))
    if best is None:
        return {"n": tw + tt, "wherefore": tw, "therefore": tt, "deviance": 0.0, "sharpness": 0.0}
    dev = 2 * (best[0] - base)
    return {
        "n": tw + tt,
        "wherefore": tw,
        "therefore": tt,
        "break_block": best[1],
        "blocks": len(rows),
        "share_before": round(best[2], 4),
        "share_after": round(best[3], 4),
        "sharpness": round(abs(best[2] - best[3]), 4),
        "deviance": round(dev, 2),
        "deviance_per_occurrence": round(dev / (tw + tt), 4) if tw + tt else 0.0,
        "bic": round(-2 * best[0] + 3 * math.log(max(tw + tt, 1)), 2),  # two rates and a place
    }


def grouped(groups: dict[str, tuple[int, int]]) -> dict:
    """One rate per group: log-likelihood and BIC."""
    n = sum(w + t for w, t in groups.values())
    ll = sum(_ll(w, t) for w, t in groups.values())
    shares = {g: [w, t, round(w / (w + t), 4) if w + t else None] for g, (w, t) in groups.items()}
    return {"groups": shares, "bic": round(-2 * ll + len(groups) * math.log(max(n, 1)), 2)}


def bom(size: int, drop_quotes: bool, kinds: tuple[str, ...] = ("body",)) -> dict:
    labels = {
        r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines()) if r["kind"] in kinds
    }
    paras = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if lab is None:
            continue
        words = WORD.findall(r["text"].lower())
        if drop_quotes and (r["book"], lab["chapter_1830"]) in QUOTED:
            continue
        paras.append((r["seq"], lab["dictation_position"], lab["narrator"], r["book"], words))

    def seq(key) -> list[str]:
        return [w for p in sorted(paras, key=key) for w in p[4]]

    by_narr: dict[str, list[int]] = {}
    by_book: dict[str, list[int]] = {}
    for _s, _d, narr, book, words in paras:
        g = "small plates writers" if narr in SMALL else narr
        for key, table in ((g, by_narr), (book, by_book)):
            c = table.setdefault(key, [0, 0])
            c[0] += words.count("wherefore")
            c[1] += words.count("therefore")
    # Moroni's own writing and Mormon's last words are where the two explanations part.
    return {
        "words": sum(len(p[4]) for p in paras),
        "printed_order": one_break(blocks(seq(lambda p: p[0]), size)),
        "dictation_order": one_break(blocks(seq(lambda p: (p[1], p[0])), size)),
        "by_narrator": grouped({k: tuple(v) for k, v in by_narr.items()}),
        "by_book": {k: v for k, v in by_book.items()},
    }


# 1830 chapters that reproduce King James chapters at length (Isaiah, Malachi, Matthew 5-7); the
# 1830 chapter numbers are those of ``paragraph_labels`` (the larger 1830 chapters).
QUOTED = {
    ("1 Nephi", 6),
    ("2 Nephi", 5),
    ("2 Nephi", 8),
    ("2 Nephi", 9),
    ("2 Nephi", 10),
    ("Mosiah", 8),
    ("3 Nephi", 5),
    ("3 Nephi", 6),
    ("3 Nephi", 10),
    ("3 Nephi", 11),
}


def sample(cfg: dict, n: int, seed: int) -> list[dict]:
    w = cfg["lab"]["wherefore"]
    t = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(t["kind"], "work"), pc.equal(t["author_kind"], "person")),
        pc.and_(pc.equal(t["has_text"], True), pc.equal(t["dup_keeper"], True)),
    )
    rows = [
        r
        for r in t.filter(keep).to_pylist()
        if not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and w["year_min"] <= r["year"] <= w["year_max"]
        and (r["words"] or 0) >= w["min_words"]
    ]
    random.Random(seed).shuffle(rows)
    cat = door.catalog({r["work_id"] for r in rows[: n * 4]})
    picked = []
    for r in rows[: n * 4]:
        c = cat.get(r["work_id"])
        if c and c["text_path"]:
            picked.append({**c, **r})
        if len(picked) == n:
            break
    return picked


def counted(row: dict, size: int) -> list[tuple[int, int]] | None:
    try:
        text = door.text_of(row)
    except OSError:
        return None  # unreadable: not attempted, never a result
    return blocks(WORD.findall(text.lower()), size)


def check(cfg: dict) -> dict:
    """Planted breaks: two works with different shares, each shuffled, joined; is the join found?"""
    w = cfg["lab"]["wherefore"]
    pool = []
    for row in sample(cfg, w["sample"], w["seed"] + 1):
        rows = counted(row, w["block_words"])
        if rows is None:
            continue
        tw, tt = sum(r[0] for r in rows), sum(r[1] for r in rows)
        if tw + tt >= w["min_pair"]:
            pool.append((tw / (tw + tt), rows))
    rng, tried, hit = random.Random(w["seed"]), 0, 0
    pairs = [(a, b) for a in pool for b in pool if abs(a[0] - b[0]) >= w["splice_min_gap"]]
    rng.shuffle(pairs)
    for a, b in pairs[: w["splices"]]:
        # Blocks are shuffled within each work first, so the join is the only break present: a
        # work's own internal switch would otherwise be found in place of the planted one (the
        # first form of this check failed for that reason, 147 of 200; see the test card).
        left, right = rng.sample(a[1], len(a[1])), rng.sample(b[1], len(b[1]))
        found = one_break(left + right).get("break_block")
        tried += 1
        hit += found is not None and abs(found - len(left)) <= w["splice_tolerance"]
    res = {"pool": len(pool), "pairs": tried, "found": hit, "rate": round(hit / max(tried, 1), 3)}
    res["passed"] = tried >= 20 and res["rate"] >= w["splice_bar"]
    return res


def run(cfg: dict) -> dict:
    w = cfg["lab"]["wherefore"]
    chk = check(cfg)
    res = {"known_answer": chk, "settings": w}
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
        return res
    res["book_of_mormon"] = bom(w["block_words"], False)
    res["book_of_mormon_without_quoted_chapters"] = bom(w["block_words"], True)
    target = res["book_of_mormon"]["dictation_order"]
    base, unreadable = [], 0
    for row in sample(cfg, w["sample"], w["seed"]):
        rows = counted(row, w["block_words"])
        if rows is None:
            unreadable += 1
            continue
        fit = one_break(rows)
        if fit["n"] >= w["min_pair"]:
            base.append({"work_id": row["work_id"], "year": row["year"], **fit})
    as_sharp = [
        b
        for b in base
        if b["sharpness"] >= target["sharpness"]
        and b["deviance_per_occurrence"] >= target["deviance_per_occurrence"]
    ]
    res["library"] = {
        "sampled": w["sample"],
        "unreadable": unreadable,
        "with_enough_occurrences": len(base),
        "as_sharp_and_strong": len(as_sharp),
        "share": round(len(as_sharp) / max(len(base), 1), 4),
        "as_sharp_work_ids": [b["work_id"] for b in as_sharp],
        "sharpness_quantiles": _quantiles([b["sharpness"] for b in base]),
        "works": base,
    }
    d, n = target["bic"], res["book_of_mormon"]["by_narrator"]["bic"]
    res["verdicts"] = {
        "order_against_narrator": "order"
        if n - d >= 10
        else "narrator"
        if d - n >= 10
        else "cannot tell",
        "bic_dictation_break": d,
        "bic_narrator": n,
        "bic_printed_break": res["book_of_mormon"]["printed_order"]["bic"],
        "unusual": res["library"]["share"] < w["unusual_share"],
    }
    return res


# --- Metcalfe 1993, "The Priority of Mosiah", in New Approaches to the Book of Mormon, 395-444.
# His numbers, transcribed from the page images (book page in each comment); (therefore,
# wherefore), the order he prints them in.
MOSIAH_FIRST = [
    "Mosiah", "Alma", "Helaman", "3 Nephi", "4 Nephi", "Mormon", "Ether", "Title Page", "Moroni",
    "1 Nephi", "2 Nephi", "Jacob", "Enos", "Jarom", "Omni", "Words of Mormon",
]  # fmt: skip
TABLE1 = {  # p. 410, Tables 1 and 2 (the same counts in two orders)
    "1 Nephi": (13, 98), "2 Nephi": (28, 138), "Jacob": (1, 52), "Enos": (0, 6), "Jarom": (0, 3),
    "Omni": (0, 6), "Words of Mormon": (0, 4), "Mosiah": (123, 1), "Alma": (286, 3),
    "Helaman": (63, 0), "3 Nephi": (98, 3), "4 Nephi": (5, 0), "Mormon": (22, 0),
    "Ether": (24, 63), "Moroni": (0, 38), "Title Page": (0, 2),
}  # fmt: skip
TABLE3 = {  # p. 413, Table 3 (KJV occurrences out, O and P readings restored)
    "Mosiah": (122, 0), "Alma": (289, 3), "Helaman": (63, 0), "3 Nephi": (86, 1),
    "4 Nephi": (5, 0), "Mormon": (22, 0), "Ether": (25, 63), "Title Page": (0, 2),
    "Moroni": (0, 38), "1 Nephi": (13, 101), "2 Nephi": (5, 137), "Jacob": (1, 52),
    "Enos": (0, 6), "Jarom": (0, 3), "Omni": (0, 6), "Words of Mormon": (0, 4),
    "Three Witnesses": (0, 2), "Preface": (0, 1),
}  # fmt: skip
TOTALS = (668, 420)  # p. 409, the 1830 text, from Hilton and Jenkins
ETHER_THIRDS = {(1, 5): (15, 8), (6, 10): (8, 23), (11, 15): (2, 32)}  # p. 412, incl. Ether 3:1
# p. 411 n. 22: KJV-derived occurrences removed, (book, chapter, verse, word, times).
DEDUCTED = [
    ("Mosiah", 14, 12, "therefore", 1), ("Mosiah", 13, 19, "wherefore", 1),
    *[("3 Nephi", c, v, "therefore", 1) for c, v in (
        (12, 23), (13, 2), (13, 8), (13, 9), (13, 22), (13, 23), (13, 25), (13, 31), (13, 34),
        (14, 12), (14, 24), (24, 6))],
    ("3 Nephi", 13, 30, "wherefore", 1), ("3 Nephi", 14, 20, "wherefore", 1),
    ("2 Nephi", 7, 7, "therefore", 2),
    *[("2 Nephi", c, v, "therefore", 1) for c, v in (
        (8, 11), (8, 21), (12, 6), (12, 9), (13, 17), (15, 13), (14, 14), (15, 24), (15, 25),
        (17, 14), (18, 7), (19, 11), (19, 14), (19, 17), (20, 16), (20, 24), (22, 3), (23, 7),
        (23, 13), (27, 26), (27, 33))],
    *[("2 Nephi", c, v, "wherefore", 1) for c, v in ((7, 2), (15, 4), (20, 12))],
]  # fmt: skip
PREFACE_DROPPED = 1  # p. 411 n. 22: the 1830 Preface's "therefore", which quotes D&C 10:41
# "Isa. 5:14//14:14" as printed; 2 Nephi 14 has six verses, and Isaiah 5:14 is 2 Nephi 15:14.
MISPRINTS = {("2 Nephi", 14, 14): (15, 14)}
# pp. 411-412 n. 22: readings of O or P restored (absent from the 1830 text).
RESTORED = [
    ("1 Nephi", 11, 1, "wherefore", 1), ("1 Nephi", 13, 34, "wherefore", 1),
    ("1 Nephi", 19, 23, "wherefore", 1), ("2 Nephi", 6, 11, "wherefore", 1),
    ("2 Nephi", 9, 28, "wherefore", 1), ("Alma", 42, 6, "therefore", 1),
    ("Alma", 42, 9, "therefore", 1), ("Ether", 3, 1, "therefore", 1),
]  # fmt: skip
FIGURE2 = [  # p. 415, Figure 2: passages he takes as Mormon's, (book, from, to, his counts)
    ("Moroni", (7, 2), (7, 48), (0, 21)), ("Mosiah", (1, 15), (2, 9), (3, 0)),
    ("Alma", (1, 1), (1, 12), (3, 0)), ("Helaman", (1, 1), (2, 8), (15, 0)),
    ("3 Nephi", (1, 15), (3, 1), (4, 0)), ("4 Nephi", (1, 1), (1, 999), (5, 0)),
    ("Moroni", (8, 2), (8, 30), (0, 9)), ("Mormon", (1, 1), (5, 999), (15, 0)),
    ("Moroni", (9, 1), (9, 999), (0, 2)), ("Mormon", (6, 1), (7, 999), (3, 0)),
    ("Words of Mormon", (1, 1), (1, 999), (0, 4)),
]  # fmt: skip
JENSON = Path("data/bom/1830/jenson-reproduction-1830.txt")
FRONT_BACK = {  # 1830 matter outside the books: (first marker, end marker) in the Jenson text
    "Title Page": ("BOOK OF MORMON :", "AUTHOR AND PROPRIETOR"),
    "Three Witnesses": ("THE TESTIMONY OF THREE WITNESSES", "AND ALSO THE TESTIMONY OF EIGHT"),
}
CHAPTERS_1830 = Path("data/benchmark/replication/chapters_1830.jsonl")


def tw(words: list[str]) -> list[int]:
    """[therefore, wherefore] in a list of lower-case words (Metcalfe's order)."""
    return [words.count("therefore"), words.count("wherefore")]


def add(a: list[int], b: list[int]) -> list[int]:
    return [a[0] + b[0], a[1] + b[1]]


def agrees(ours: int, his: int, m: dict) -> bool:
    return abs(ours - his) <= max(m["tol_abs"], m["tol_rel"] * his)


def compare(ours: dict, his: dict, m: dict) -> dict:
    """Cell by cell: ours, his, and whether they agree; the cells that do not, named."""
    rows, off = {}, []
    for k, h in his.items():
        o = ours.get(k)
        if o is None:
            rows[k] = {"his": list(h), "ours": None}
            off.append(f"{k}: not counted")
            continue
        ok = [agrees(o[i], h[i], m) for i in (0, 1)]
        rows[k] = {"his": list(h), "ours": list(o), "agree": all(ok)}
        off += [f"{k} {w}: {o[i]} vs {h[i]}" for i, w in enumerate(TW) if not ok[i]]
    return {"rows": rows, "reproduced": not off, "disagree": off}


TW = ("therefore", "wherefore")


def switch(table: dict) -> dict:
    """Mosiah-first: a 'therefore' majority from Mosiah to Mormon, 'wherefore' from Ether on."""
    order = [b for b in MOSIAH_FIRST if b in table]
    k = order.index("Ether")
    early = all(table[b][0] > table[b][1] for b in order[:k])
    late = all(table[b][1] > table[b][0] for b in order[k:])
    return {"first_wherefore_book": next(b for b in order if table[b][1] > table[b][0]),
            "holds": early and late}  # fmt: skip


def edition_books(kinds: tuple[str, ...]) -> dict:
    by: dict[str, list[int]] = {}
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if r["book"] and r["kind"] in kinds:
            c = by.setdefault(r["book"], [0, 0])
            for i, n in enumerate(tw(WORD.findall(r["text"].lower()))):
                c[i] += n
    return by


def outside_books() -> dict:
    """Title Page and Three Witnesses from the Jenson text; the Preface from the 1830 table."""
    t = re.sub(r"\u00ad\s*", "", JENSON.read_text(encoding="utf-8"))
    res = {}
    for name, (a, b) in FRONT_BACK.items():
        i = t.find(a)
        j = t.find(b, i)
        res[name] = tw(WORD.findall(t[i:j].lower())) if i >= 0 and j > i else None
    pre = [0, 0]
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if r["book"] is None:
            pre = add(pre, tw(WORD.findall(r["text"].lower())))
    res["Preface"] = pre
    return res


def verses_1920(text: str | None = None) -> list[tuple[str, int, int, list[str]]]:
    """(book, chapter, verse, words) from Project Gutenberg's 1920 text (ebook 17)."""
    from eval.replicate import _TITLES, BOOKS, GUTENBERG

    t = text if text is not None else GUTENBERG.read_text(encoding="utf-8")
    if "*** START" in t:
        t = t[t.find("*** START") : t.find("*** END")]
    after = t.find("Contents") + 2000 if "Contents" in t else 0
    starts = []
    for book in BOOKS:
        if book in _TITLES:
            i = t.find(_TITLES[book], after)
        else:
            m = re.search(rf"(?m)^{re.escape(book)} Chapter 1\s*$", t)
            i = m.start() if m else -1
        if i >= 0:
            starts.append((i, book))
    starts.sort()
    # Gutenberg prints 4 Nephi's verses as "4 Nephi 1:1 ...", every other book's as "1:1 ...".
    verse = re.compile(r"(?m)^(?:4 Nephi )?(\d+):(\d+) (.+(?:\n(?!(?:4 Nephi )?\d+:\d+ ).+)*)")
    out_, k = [], -1
    for m in verse.finditer(t):
        while k + 1 < len(starts) and starts[k + 1][0] <= m.start():
            k += 1
        if k >= 0:
            words = WORD.findall(m.group(3).lower())
            out_.append((starts[k][1], int(m.group(1)), int(m.group(2)), words))
    return out_


def in_range(c: int, v: int, a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a <= (c, v) <= b


def metcalfe(cfg: dict) -> dict:
    """Metcalfe's Tables 1 and 3, Ether by thirds and Figure 2, recounted; see the test card."""
    m = cfg["lab"]["wherefore"]["metcalfe"]
    extra = outside_books()
    body = edition_books(("body",))
    whole = edition_books(("body", "synopsis"))
    tp = {"Title Page": extra["Title Page"]}
    vs = verses_1920()
    by1920: dict[str, list[int]] = {}
    where: dict[tuple[str, int, int], list[int]] = {}
    for b, c, v, words in vs:
        n = tw(words)
        by1920[b] = add(by1920.get(b, [0, 0]), n)
        where[(b, c, v)] = n
    # Chapter counts in both editions: where the 1830 holds a word the 1920 text lacks.
    ch1830: dict[tuple[str, int], list[int]] = {}
    for ln in CHAPTERS_1830.read_text().splitlines():
        r = json.loads(ln)
        ch1830[(r["book"], int(r["chapter"]))] = tw(r["text"].split())
    ch1920: dict[tuple[str, int], list[int]] = {}
    for b, c, _v, words in vs:
        ch1920[(b, c)] = add(ch1920.get((b, c), [0, 0]), tw(words))
    edition_diff = [
        {"chapter": f"{b} {c}", "1830": n, "1920": ch1920.get((b, c))}
        for (b, c), n in ch1830.items()
        if n != ch1920.get((b, c))
    ]
    # Table 3 by his own steps: his KJV occurrences out, his O and P readings back in. He worked
    # from a modern text (Table 1 matches the 1920 text cell for cell), so his steps apply to it.
    # On the 1830 text a restoration is added only where the 1830 chapter lacks it, since the
    # 1830 already prints most of the words later editions dropped.
    t3_1920 = {b: list(v) for b, v in by1920.items()} | {k: list(v) for k, v in extra.items()}
    t3_1830 = {b: list(v) for b, v in whole.items()} | {k: list(v) for k, v in extra.items()}
    for t3 in (t3_1920, t3_1830):
        t3["Preface"][0] -= PREFACE_DROPPED
    lookups, already = [], []
    for sign, rows in ((-1, DEDUCTED), (1, RESTORED)):
        for b, c, v, word, times in rows:
            i = TW.index(word)
            t3_1920[b][i] += sign * times
            gap = ch1830.get((b, c), [0, 0])[i] - ch1920.get((b, c), [0, 0])[i]
            if sign > 0 and gap >= times:
                already.append(f"{b} {c}:{v}")
            else:
                t3_1830[b][i] += sign * times
            found = where.get((b, c, v), [None, None])[i]
            alt = MISPRINTS.get((b, c, v))
            lookups.append({
                "verse": f"{b} {c}:{v}", "word": word, "listed": times, "in_1920_text": found,
                "kind": "removed" if sign < 0 else "restored",
                **({"parallel": f"{b} {alt[0]}:{alt[1]}",
                    "in_1920_text_at_parallel": where.get((b, *alt), [None, None])[i]}
                   if alt else {}),
            })  # fmt: skip
    removed = [x for x in lookups if x["kind"] == "removed"]
    ether: dict[str, list[int]] = {}
    ether1920: dict[str, list[int]] = {}
    chs = [json.loads(ln) for ln in CHAPTERS_1830.read_text().splitlines()]
    for (a, b), _his in ETHER_THIRDS.items():
        key = f"{a}-{b}"
        ether[key] = [0, 0]
        for r in chs:
            if r["book"] == "Ether" and a <= int(r["chapter"]) <= b:
                ether[key] = add(ether[key], tw(r["text"].split()))
        ether1920[key] = [0, 0]
        for bk, c, _v, words in vs:
            if bk == "Ether" and a <= c <= b:
                ether1920[key] = add(ether1920[key], tw(words))
    # His thirds include the Ether 3:1 restoration; the 1830 text lacks it.
    ether_his_1830 = {
        f"{a}-{b}": (h[0] - (a <= 3 <= b), h[1]) for (a, b), h in ETHER_THIRDS.items()
    }
    fig2 = {}
    for b, a, z, his in FIGURE2:
        n = [0, 0]
        for bk, c, v, words in vs:
            if bk == b and in_range(c, v, a, z):
                n = add(n, tw(words))
        fig2[f"{b} {a[0]}:{a[1]}-{z[0]}:{z[1] if z[1] < 999 else 'end'}"] = (n, his)
    # The 2026-11-20 fit counted body paragraphs only; the same fit on all book text, and the
    # stored library fits (result.json) held against it.
    whole_fit = bom(cfg["lab"]["wherefore"]["block_words"], False, ("body", "synopsis"))
    whole_fit = whole_fit["dictation_order"]
    as_sharp = None
    if (OUT / "result.json").exists():
        lib = json.loads((OUT / "result.json").read_text()).get("library", {}).get("works", [])
        as_sharp = {
            "of": len(lib),
            "count": sum(
                1
                for b in lib
                if b["sharpness"] >= whole_fit["sharpness"]
                and b["deviance_per_occurrence"] >= whole_fit["deviance_per_occurrence"]
            ),
        }
    total = [sum(v[i] for v in whole.values()) for i in (0, 1)]
    total_all = [total[i] + sum(v[i] for v in extra.values()) for i in (0, 1)]
    return {
        "source": "Metcalfe 1993, New Approaches to the Book of Mormon, 395-444",
        "settings": m,
        "table1_1830_whole_books": compare(whole | tp, TABLE1, m),
        "table1_1830_body_only": compare(body | tp, TABLE1, m),
        "table1_1920_verses": compare(by1920 | tp, TABLE1, m),
        "switch": {
            "his_table1": switch(TABLE1),
            "his_table3": switch(TABLE3),
            "ours_1830_whole_books": switch(whole | tp),
            "ours_1830_body_only": switch(body | tp),
        },
        "totals": {
            "his": list(TOTALS),
            "ours_1830_books": total,
            "ours_1830_with_title_preface_witnesses": total_all,
            "agree": [abs(total_all[i] - TOTALS[i]) <= m["total_tol"] * TOTALS[i] for i in (0, 1)],
            "his_table1_sum": [sum(v[i] for v in TABLE1.values()) for i in (0, 1)],
        },
        "table3_1920_his_steps": compare(t3_1920, TABLE3, m),
        "table3_1830_his_steps": compare(t3_1830, TABLE3, m),
        "restorations_already_in_1830": already,
        "edition_differences_by_modern_chapter": edition_diff,
        "his_lists_checked_in_1920_text": {
            "removed_listed": sum(x["listed"] for x in removed),
            "removed_found_at_listed_verse": sum(
                min(x["listed"], x["in_1920_text"] or 0) for x in removed
            ),
            "not_found": [x for x in removed if (x["in_1920_text"] or 0) < x["listed"]],
        },
        "ether_thirds_1830": compare(ether, ether_his_1830, m),
        "ether_thirds_1920": compare(ether1920, ether_his_1830, m),
        "ether_thirds_his_as_printed": {
            k: list(v) for k, v in zip(ether_his_1830, ETHER_THIRDS.values(), strict=True)
        },  # fmt: skip
        "figure2_1920_verses": compare(
            {k: v[0] for k, v in fig2.items()}, {k: v[1] for k, v in fig2.items()}, m
        ),
        "one_break_1830_whole_books": whole_fit,
        "library_as_sharp_and_strong_against_whole_books_fit": as_sharp,
        "edition_note": (
            "1830 = data/bom/1830/edition_1830.jsonl (Jenson reproduction); body-only leaves out "
            "seq 1316 (Mormon ch. IV, 3,152 words) because it is labelled synopsis. "
            "1920 = Project Gutenberg 17, verses only."
        ),
    }


def _quantiles(xs: list[float]) -> dict:
    xs = sorted(xs)
    return {q: xs[min(len(xs) - 1, int(len(xs) * q / 100))] for q in (50, 90, 95, 99)} if xs else {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run", "metcalfe"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "metcalfe":
        res = metcalfe(cfg)
        res["config_sha256"] = config.sha256_of_config()
        out(OUT / "metcalfe.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "settings"}, indent=1))
        return 0
    if a.cmd == "check":
        print(json.dumps(check(cfg), indent=1))
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k not in ("library", "settings")}, indent=1))
    if "library" in res:
        print({k: v for k, v in res["library"].items() if k != "works"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
