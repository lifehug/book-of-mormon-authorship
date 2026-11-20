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


def bom(size: int, drop_quotes: bool) -> dict:
    labels = {
        r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines()) if r["kind"] == "body"
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


def _quantiles(xs: list[float]) -> dict:
    xs = sorted(xs)
    return {q: xs[min(len(xs) - 1, int(len(xs) * q / 100))] for q in (50, 90, 95, 99)} if xs else {}


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
    print(json.dumps({k: v for k, v in res.items() if k not in ("library", "settings")}, indent=1))
    if "library" in res:
        print({k: v for k, v in res["library"].items() if k != "works"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
