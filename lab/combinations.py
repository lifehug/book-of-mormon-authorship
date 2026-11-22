"""BOM-123: "secret combinations" in print year by year, and what the phrase referred to.

Vogel (1993) held that around 1830 the phrase was used almost exclusively of Freemasonry; Peterson,
Mouritsen, Oman and G. Smith answered that it had legal, political and trade uses with no Masonic
reference. Both sides collect examples; this counts every use. The phrase and its close variants
(``lab.combinations.phrase``: up to two words between "secret" and "combination(s)") are found in
every readable work of the library printed 1700-1830 (all genres, kept copies, OCR not excluded) and
in every readable Chronicling America newspaper page, on lower-cased, whitespace-normalised text.
Rates are per million words of the text read, by year and by fixed period. Each use keeps 30 words
each side, and a fixed written rule sorts it by what it refers to: Freemasonry if any Masonic term
lies in the window, otherwise the category whose nearest term is nearest (other society,
commercial, political, crime, religious), else other. Newspaper pages carry state and exact date
(before and after the Morgan affair, 12 September 1826); books carry no place in the catalogue.
The Book of Mormon (1830 body text), Bible-style books of 1810-1829, marked translations in the
library and Joseph Smith's other texts go through the same code.

The known-answer check comes first and has two parts: the classifier on hits in works whose titles
settle the subject (Masonic, trade, politics), and the yearly counter on a curve known in advance
("anti-masonic" near zero before 1826, rising after; two steady phrases staying steady). If either
misses, the report is counts by year only, a jobs file for ``lab/judge.py`` (simulated judging by an
AI model) is prepared and *not* run, and the Book of Mormon is not scored. The test card, written
first, is ``data/private/lab/owner/2026-11-21-secret-combinations/card.md``; settings are
``lab.combinations`` in the config. The result holds ids, years and counts; the words around each
use are kept only in the private folder.

Usage::

    python -m lab.combinations scan     # the whole-library scan -> scan.json (+ private hits.jsonl)
    python -m lab.combinations check    # known-answer check from the scan (prints it)
    python -m lab.combinations run      # check, then the report -> result.json
    python -m lab.combinations jobs     # prepare (not run) the judging jobs file
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import re
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from lab import door, registry
from lab.paths import REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "secret_combinations"
PRIVATE = Path("data/private/lab/owner/2026-11-21-secret-combinations")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
CHRON = Path("data/catalog/chronicling_america.jsonl.gz")
CATEGORIES = ["freemasonry", "other_society", "commercial", "political", "crime", "religious"]
SKIP_TOKEN = re.compile(r"\s+")


def settings(cfg: dict) -> dict:
    return cfg["lab"]["combinations"]


def settings_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(settings(cfg), sort_keys=True).encode()).hexdigest()


def normalise(text: str) -> str:
    return " ".join(text.lower().split())


# ------------------------------------------------------------------------------ finding uses


def find_uses(low: str, d: dict) -> list[dict]:
    """Every use of the phrase in normalised lower-case text, with the words each side."""
    if "ombinat" not in low:
        return []
    rx, exact, w = re.compile(d["phrase"]), re.compile(d["exact"]), d["window_words"]
    hits = []
    for m in rx.finditer(low):
        left = low[max(0, m.start() - 12 * w) : m.start()].split()[-w:]
        right = low[m.end() : m.end() + 12 * w].split()[:w]
        hits.append(
            {
                "exact": bool(exact.fullmatch(m.group(0))),
                "left": " ".join(left),
                "mid": m.group(0),
                "right": " ".join(right),
            }
        )
    return hits


def count_literals(low: str, d: dict) -> dict[str, int]:
    return {n: sum(low.count(p) for p in ps) for n, ps in d["count_phrases"].items()}


# ------------------------------------------------------------------------------ classifier


def compile_categories(d: dict) -> dict[str, re.Pattern]:
    return {n: re.compile(d["categories"][n]) for n in CATEGORIES}


def _nearest(rx: re.Pattern, left: str, right: str) -> int | None:
    """Words between the phrase and the nearest match of ``rx`` (0 = next to the phrase)."""
    best = None
    m = rx.search(right)
    if m:
        k = len(right[: m.start()].split())
        best = k - 1 if m.start() > 0 and right[m.start() - 1] != " " else k
    for m in rx.finditer(left):
        k = len(left[m.end() :].split())
        k = k - 1 if m.end() < len(left) and left[m.end()] != " " else k
        best = k if best is None else min(best, k)
    return None if best is None else max(best, 0)


def classify(left: str, right: str, cats: dict[str, re.Pattern], near: int) -> tuple[str, bool]:
    """(label, a Masonic term within ``near`` words). Masonic anywhere in the window = Freemasonry;
    otherwise the nearest category's term wins, ties in the order of CATEGORIES; else 'other'."""
    mason = _nearest(cats["freemasonry"], left, right)
    near_mason = mason is not None and mason < near
    if mason is not None:
        return "freemasonry", near_mason
    best, label = None, "other"
    for name in CATEGORIES[1:]:
        k = _nearest(cats[name], left, right)
        if k is not None and (best is None or k < best):
            best, label = k, name
    return label, near_mason


# ------------------------------------------------------------------------------ the scan


def chron_places() -> dict[str, tuple[str, str]]:
    places = {}
    with gzip.open(CHRON, "rt") as f:
        for line in f:
            r = json.loads(line)
            places.setdefault(r["lccn"], (r["state"], r["city"]))
    return places


def _scan_row(job: tuple[dict, dict]) -> dict:
    row, d = job
    try:
        text = door.text_of(row)
    except OSError:
        return {"work_id": row["work_id"], "unreadable": True}
    low = normalise(text)
    return {
        "work_id": row["work_id"],
        "literals": count_literals(low, d),
        "hits": find_uses(low, d),
    }


def library_rows(cfg: dict) -> list[dict]:
    d = settings(cfg)
    from lab import emode

    trans = emode.translations()
    reg = [
        r
        for r in registry.load().to_pylist()
        if r["has_text"]
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and d["year_min"] <= r["year"] <= d["year_max"]
        and r["kind"] in ("work", "newspaper_page")
    ]
    cat = door.catalog({r["work_id"] for r in reg})
    places = chron_places()
    rows = []
    for r in reg:
        c = cat.get(r["work_id"])
        if c is None or not c["text_path"]:
            continue
        row = {**c, **r, "translation": r["work_id"] in trans}
        row["group"] = "newspapers" if r["kind"] == "newspaper_page" else "works"
        if row["group"] == "newspapers":
            lccn, rest = c["source_id"].split("/", 1)
            row["date"] = rest[:10]
            row["state"], row["city"] = places.get(lccn, (None, None))
        rows.append(row)
    return rows


def new_stats() -> dict:
    return defaultdict(lambda: defaultdict(lambda: {"works": 0, "words": 0, "all": 0, "exact": 0}))


def add_stat(stats: dict, group: str, year: int, words: int, hits: list[dict]) -> None:
    s = stats[group][year]
    s["works"] += 1
    s["words"] += words
    s["all"] += len(hits)
    s["exact"] += sum(h["exact"] for h in hits)


def scan(cfg: dict) -> dict:
    from lab import emode

    d = settings(cfg)
    t0 = time.time()
    rows = library_rows(cfg)
    print(f"{len(rows):,} works and pages to read", flush=True)
    stats, lits = new_stats(), defaultdict(lambda: defaultdict(Counter))
    by = {r["work_id"]: r for r in rows}
    hits_out, unreadable = [], Counter()
    with ProcessPoolExecutor(d["workers"]) as pool:
        for i, got in enumerate(pool.map(_scan_row, [(r, d) for r in rows], chunksize=8)):
            r = by[got["work_id"]]
            if got.get("unreadable"):
                unreadable[r["group"]] += 1  # not attempted, never a zero
                continue
            groups = [r["group"]] + (["translations"] if r["translation"] else [])
            for g in groups:
                add_stat(stats, g, r["year"], r["words"] or 0, got["hits"])
                for n, c in got["literals"].items():
                    lits[g][n][r["year"]] += c
            for h in got["hits"]:
                hits_out.append(
                    {
                        "group": r["group"],
                        "work_id": r["work_id"],
                        "year": r["year"],
                        "date": r.get("date"),
                        "genre": r["genre"],
                        "translation": r["translation"],
                        "state": r.get("state"),
                        "title": " ".join((r["title"] or "").split())[:200],
                        **h,
                    }
                )
            if i % 20000 == 0:
                print(f"  {i:,} read, {len(hits_out):,} uses, {time.time() - t0:.0f}s", flush=True)
    # controls read by the same code
    controls = {}
    for name, texts in (
        ("control_bible_style", emode.bible_style_texts()),
        ("control_js", emode.js_texts()),
    ):
        per = {}
        for k, text in sorted(texts.items()):
            words = len(text.split())
            if words < d["controls_min_words"]:
                continue  # too short to count: not attempted
            low = normalise(text)
            hs = find_uses(low, d)
            per[k] = {"words": words, "all": len(hs), "exact": sum(h["exact"] for h in hs)}
            for h in hs:
                hits_out.append({"group": name, "work_id": k, "year": None, "date": None,
                                 "genre": None, "translation": False, "state": None,
                                 "title": k, **h})  # fmt: skip
        controls[name] = per
    res = {
        "settings_sha256": settings_hash(cfg),
        "config_sha256": config.sha256_of_config(),
        "commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "read": {g: sum(v["works"] for v in ys.values()) for g, ys in stats.items()},
        "unreadable_not_attempted": dict(unreadable),
        "by_year": {g: {str(y): v for y, v in sorted(ys.items())} for g, ys in stats.items()},
        "literals_by_year": {
            g: {n: {str(y): c for y, c in sorted(cs.items())} for n, cs in ns.items()}
            for g, ns in lits.items()
        },
        "controls": controls,
        "uses_total": sum(1 for h in hits_out if h["group"] in ("works", "newspapers")),
        "seconds": round(time.time() - t0),
    }
    out(PRIVATE / "hits.jsonl").write_text("".join(json.dumps(h) + "\n" for h in hits_out))
    out(OUT / "scan.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def load_scan(cfg: dict) -> dict:
    p = OUT / "scan.json"
    if not p.exists():
        raise SystemExit("no scan.json: run `python -m lab.combinations scan` first")
    res = json.loads(p.read_text())
    if res["settings_sha256"] != settings_hash(cfg):
        raise SystemExit("scan.json was made with other settings: run scan again")
    return res


def load_hits() -> list[dict]:
    return [json.loads(x) for x in (PRIVATE / "hits.jsonl").read_text().splitlines()]


# ------------------------------------------------------------------------------ the check


def rate(occ: int, words: int) -> float | None:
    return occ / words * 1e6 if words else None


def pooled(scan_res: dict, groups: tuple[str, ...], y0: int, y1: int, key: str) -> tuple[int, int]:
    """(occurrences, words) summed over the groups and years y0..y1; ``key`` is a literal name or
    'all'/'exact'."""
    occ = words = 0
    for g in groups:
        for y, v in scan_res["by_year"].get(g, {}).items():
            if y0 <= int(y) <= y1:
                words += v["words"]
                if key in ("all", "exact"):
                    occ += v[key]
        if key not in ("all", "exact"):
            for y, c in scan_res["literals_by_year"].get(g, {}).get(key, {}).items():
                if y0 <= int(y) <= y1:
                    occ += c
    return occ, words


def counter_check(scan_res: dict, d: dict) -> dict:
    groups = ("works", "newspapers")
    b0, b1 = d["anti_before"]
    a0, a1 = d["anti_after"]
    ob, wb = pooled(scan_res, groups, b0, b1, "anti_masonic")
    oa, wa = pooled(scan_res, groups, a0, a1, "anti_masonic")
    rb, ra = rate(ob, wb), rate(oa, wa)
    anti = {
        "before": {"years": [b0, b1], "occurrences": ob, "words": wb, "per_million": rb},
        "after": {"years": [a0, a1], "occurrences": oa, "words": wa, "per_million": ra},
        "ratio": (rb / ra) if rb is not None and ra else None,
    }
    anti["passed"] = bool(
        ra and oa >= d["anti_min_after"] and rb is not None and rb < d["anti_ratio"] * ra
    )
    by_year = {}
    for y in range(d["year_min"], d["year_max"] + 1):
        o, w = pooled(scan_res, groups, y, y, "anti_masonic")
        if w:
            by_year[str(y)] = {"occurrences": o, "per_million": round(rate(o, w), 3)}
    anti["by_year"] = by_year
    steady = {}
    step = d["steady_period"]
    for name in ("steady_of_the", "steady_in_the_course_of"):
        rates = {}
        for y0 in range(1780, 1830, step):
            o, w = pooled(scan_res, groups, y0, y0 + step - 1, name)
            if w >= d["steady_min_words"]:
                rates[f"{y0}-{y0 + step - 1}"] = round(rate(o, w), 1)
        med = statistics.median(rates.values()) if rates else None
        worst = (
            max(max(v / med, med / v) for v in rates.values())
            if rates and med and min(rates.values()) > 0
            else None
        )
        steady[name] = {
            "per_million_by_period": rates,
            "median": med,
            "worst_factor": round(worst, 3) if worst else None,
            "passed": bool(worst and worst <= d["steady_band"]),
        }
    return {
        "anti_masonic": anti,
        "steady": steady,
        "passed": anti["passed"] and all(s["passed"] for s in steady.values()),
    }


def ka_sample(hits: list[dict], d: dict) -> dict[str, list[dict]]:
    pats = {k: re.compile(v) for k, v in d["ka_titles"].items()}
    classes: dict[str, list[dict]] = {"masonic": [], "trade": [], "politics": []}
    for h in hits:
        if h["group"] not in ("works", "newspapers"):
            continue
        title = h["title"].lower()
        if pats["masonic"].search(title):
            classes["masonic"].append(h)
            continue
        t, p = bool(pats["trade"].search(title)), bool(pats["politics"].search(title))
        if t != p:
            classes["trade" if t else "politics"].append(h)
    rng = random.Random(d["seed"])
    sample = {}
    for name, hs in classes.items():
        per: Counter = Counter()
        rng.shuffle(hs)
        keep = []
        for h in hs:
            if per[h["work_id"]] < d["ka_per_work"]:
                per[h["work_id"]] += 1
                keep.append(h)
        sample[name] = keep[: d["ka_max"]]
    return sample


def classifier_check(hits: list[dict], d: dict) -> dict:
    cats = compile_categories(d)
    sample = ka_sample(hits, d)
    res: dict = {"classes": {}}
    for name, hs in sample.items():
        labels = Counter(classify(h["left"], h["right"], cats, d["near_words"])[0] for h in hs)
        n = len(hs)
        res["classes"][name] = {
            "n": n,
            "works": len({h["work_id"] for h in hs}),
            "labels": dict(labels),
            "share_freemasonry": round(labels["freemasonry"] / n, 4) if n else None,
        }
    c = res["classes"]
    attempted = all(c[k]["n"] >= d["ka_min"] for k in c)
    res["attempted"] = attempted
    if not attempted:
        res["passed"] = False
        return res

    def share(k: str, label: str) -> float:
        return c[k]["labels"].get(label, 0) / c[k]["n"]

    nm_n = c["trade"]["n"] + c["politics"]["n"]
    nm_fm = c["trade"]["labels"].get("freemasonry", 0) + c["politics"]["labels"].get(
        "freemasonry", 0
    )
    res["measures"] = {
        "masonic_titled_labelled_freemasonry": round(share("masonic", "freemasonry"), 4),
        "non_masonic_titled_not_freemasonry": round(1 - nm_fm / nm_n, 4),
        "trade_titled_labelled_commercial": round(share("trade", "commercial"), 4),
        "politics_titled_labelled_political": round(share("politics", "political"), 4),
    }
    m = res["measures"]
    res["bars"] = {
        "masonic_titled_labelled_freemasonry": d["ka_bar_masonic"],
        "non_masonic_titled_not_freemasonry": d["ka_bar_not_masonic"],
        "trade_titled_labelled_commercial": d["ka_bar_trade"],
        "politics_titled_labelled_political": d["ka_bar_politics"],
    }
    res["met"] = {k: m[k] >= res["bars"][k] for k in m}
    res["passed"] = all(res["met"].values())
    return res


def check(cfg: dict) -> dict:
    d = settings(cfg)
    sc = load_scan(cfg)
    counter = counter_check(sc, d)
    clf = classifier_check(load_hits(), d)
    return {"counter": counter, "classifier": clf, "passed": counter["passed"] and clf["passed"]}


# ------------------------------------------------------------------------------ the report


def period_of(year: int, d: dict) -> str | None:
    for a, b in d["periods"]:
        if a <= year <= b:
            return f"{a}" if a == b else f"{a}-{b}"
    return None


def tally(hs: list[dict], cats: dict, d: dict) -> dict:
    labels: Counter = Counter()
    near = 0
    for h in hs:
        lab, nm = classify(h["left"], h["right"], cats, d["near_words"])
        labels[lab] += 1
        near += nm
    n = len(hs)
    return {
        "uses": n,
        "labels": {k: labels.get(k, 0) for k in [*CATEGORIES, "other"]},
        "share_freemasonry": round(labels["freemasonry"] / n, 4) if n else None,
        "share_freemasonry_near": round(near / n, 4) if n else None,
    }


def yearly(sc: dict, hits: list[dict], cats: dict, d: dict, group: str) -> dict:
    by_y: dict[int, list[dict]] = defaultdict(list)
    for h in hits:
        if h["group"] == group or (group == "translations" and h["translation"]):
            by_y[h["year"]].append(h)
    table = {}
    for y, v in sc["by_year"].get(group, {}).items():
        t = tally(by_y.get(int(y), []), cats, d)
        pm = round(rate(v["all"], v["words"]), 4) if v["words"] else None
        t.update(works=v["works"], words=v["words"], exact=v["exact"], per_million=pm)
        table[y] = t
    return table


def periods(sc: dict, hits: list[dict], cats: dict, d: dict, groups: tuple[str, ...]) -> dict:
    by_p: dict[str, list[dict]] = defaultdict(list)
    for h in hits:
        if h["group"] in groups and h["year"]:
            p = period_of(h["year"], d)
            if p:
                by_p[p].append(h)
    table = {}
    for a, b in d["periods"]:
        p = f"{a}" if a == b else f"{a}-{b}"
        o, w = pooled(sc, groups, a, b, "all")
        t = tally(by_p.get(p, []), cats, d)
        t.update(words=w, per_million=round(rate(o, w), 4) if w else None)
        table[p] = t
    return table


def morgan_split(hits: list[dict], cats: dict, d: dict) -> dict:
    news = [h for h in hits if h["group"] == "newspapers" and h["date"]]
    before = [h for h in news if h["date"] < d["morgan_date"]]
    after = [h for h in news if h["date"] >= d["morgan_date"]]
    return {
        "date": d["morgan_date"],
        "before": tally(before, cats, d),
        "after": tally(after, cats, d),
    }


def by_state(hits: list[dict], cats: dict, d: dict) -> dict:
    st: dict[str, list[dict]] = defaultdict(list)
    for h in hits:
        if h["group"] == "newspapers":
            st[h["state"] or "unknown"].append(h)
    return {
        s: {**tally(hs, cats, d), "before_morgan": sum(h["date"] < d["morgan_date"] for h in hs)}
        for s, hs in sorted(st.items(), key=lambda kv: -len(kv[1]))
    }


def genre_table(hits: list[dict], cats: dict, d: dict) -> dict:
    g: dict[str, list[dict]] = defaultdict(list)
    for h in hits:
        if h["group"] == "works" and h["year"] and 1826 <= h["year"] <= 1830:
            g[h["genre"] or "none"].append(h)
    return {k: tally(v, cats, d) for k, v in sorted(g.items(), key=lambda kv: -len(kv[1]))}


def bom_uses(d: dict) -> dict:
    cats = compile_categories(d)
    hs, words, by_book = [], 0, Counter()
    for line in EDITION.read_text().splitlines():
        r = json.loads(line)
        if r.get("kind") != "body":
            continue
        low = normalise(r["text"])
        words += len(low.split())
        for h in find_uses(low, d):
            h["book"] = r["book"]
            h["seq"] = r["seq"]
            hs.append(h)
            by_book[r["book"]] += 1
    out(PRIVATE / "bom_hits.jsonl").write_text("".join(json.dumps(h) + "\n" for h in hs))
    res = tally(hs, cats, d)
    res.update(
        words=words,
        exact=sum(h["exact"] for h in hs),
        per_million=round(rate(len(hs), words), 2) if words else None,
        by_book=dict(by_book),
        paragraph_seq=sorted(h["seq"] for h in hs),
    )
    # which categories' terms stand beside the uses, by the nearest-term rule alone (no Masonic
    # override), so a reader sees what the book's own wording points to
    nearest: Counter = Counter()
    for h in hs:
        best, label = None, "other"
        for name in CATEGORIES:
            k = _nearest(cats[name], h["left"], h["right"])
            if k is not None and (best is None or k < best):
                best, label = k, name
        nearest[label] += 1
    res["nearest_term_only"] = dict(nearest)
    return res


def control_tables(sc: dict, hits: list[dict], cats: dict, d: dict) -> dict:
    res = {}
    for g in ("control_bible_style", "control_js"):
        hs = [h for h in hits if h["group"] == g]
        per = sc["controls"][g]
        words = sum(v["words"] for v in per.values())
        t = tally(hs, cats, d)
        t.update(
            texts=len(per),
            words=words,
            exact=sum(v["exact"] for v in per.values()),
            per_million=round(rate(len(hs), words), 3) if words else None,
            texts_with_uses={k: v["all"] for k, v in per.items() if v["all"]},
        )
        res[g] = t
    tr = yearly(sc, hits, cats, d, "translations")
    th = [h for h in hits if h["translation"] and h["group"] == "works"]
    words = sum(v["words"] for v in tr.values())
    pm = round(rate(len(th), words), 4) if words else None
    res["translations"] = {**tally(th, cats, d), "words": words, "per_million": pm}
    return res


def verdict(per: dict, d: dict) -> dict:
    """Vogel's claim on the pooled (books and newspapers) uses: 1827-1830 against 1800-1825."""

    def share(y0: int, y1: int) -> tuple[int, float | None]:
        n = fm = 0
        for p, t in per.items():
            a = int(p.split("-")[0])
            b = int(p.split("-")[-1])
            if y0 <= a and b <= y1:
                n += t["uses"]
                fm += t["labels"]["freemasonry"]
        return n, (fm / n if n else None)

    n_late, s_late = share(1827, 1830)
    n_mid, s_mid = share(1800, 1825)
    n_old, s_old = share(1700, 1799)
    v = {"uses_1827_1830": n_late, "share_1827_1830": s_late, "uses_1800_1825": n_mid,
         "share_1800_1825": s_mid, "uses_1700_1799": n_old, "share_1700_1799": s_old}  # fmt: skip
    if n_late < 20 or s_late is None:
        v["answer"] = "cannot tell (fewer than 20 uses in 1827-1830)"
    elif s_late >= 0.9 and s_mid is not None and s_late - s_mid >= 0.4:
        v["answer"] = "yes (Vogel): almost all Masonic after the rise"
    elif s_late <= 0.5:
        v["answer"] = "no (general term): the Masonic share stays at or below half"
    else:
        v["answer"] = "mixed"
    return v


def judge_jobs(cfg: dict) -> dict:
    """Prepare, never run, the judging jobs: simulated judging by an AI model, one question per
    use, a seeded sample of up to ``judge_per_year`` uses a year (books and newspapers pooled)."""
    d = settings(cfg)
    hits = [h for h in load_hits() if h["group"] in ("works", "newspapers")]
    by_y: dict[int, list[dict]] = defaultdict(list)
    for i, h in enumerate(hits):
        by_y[h["year"]].append({**h, "i": i})
    rng, jobs = random.Random(d["seed"]), []
    for y in sorted(by_y):
        pool = by_y[y]
        rng.shuffle(pool)
        for h in pool[: d["judge_per_year"]]:
            passage = f"{h['left']} [{h['mid']}] {h['right']}"
            prompt = (
                "A printed text of about "
                f"{y} uses the phrase marked in square brackets. What does the phrase refer to "
                "in this passage? Answer with exactly one label: freemasonry; other_society (a "
                "named or described secret society other than the Freemasons); political "
                "(a faction, party or conspiracy against a government); trade (a combination of "
                "merchants, masters or workmen); crime (robbers, murderers, a criminal band); "
                "religious; other; unclear.\n\nPassage:\n" + passage + "\n\nReply with the "
                "label only."
            )
            jobs.append({"id": f"{h['work_id']}|{h['i']}", "prompt": prompt})
    path = out(PRIVATE / "jobs_referent.jsonl")
    path.write_text("".join(json.dumps(j) + "\n" for j in jobs))
    return {"jobs_file": str(path), "questions": len(jobs), "run": False}


def unclassified_counts(sc: dict, hits: list[dict], d: dict) -> dict:
    """What can be said without the classifier: counts only. ``masonic_term_in_window`` is a plain
    co-occurrence count (a Masonic word within the window of a use), not a label of the referent."""
    mason = re.compile(d["categories"]["freemasonry"])

    def co(hs: list[dict], near: int) -> int:
        n = 0
        for h in hs:
            k = _nearest(mason, h["left"], h["right"])
            n += k is not None and k < near
        return n

    table = {}
    for a, b in d["periods"]:
        p = f"{a}" if a == b else f"{a}-{b}"
        for g in ("works", "newspapers"):
            hs = [h for h in hits if h["group"] == g and a <= h["year"] <= b]
            o, w = pooled(sc, (g,), a, b, "all")
            table.setdefault(p, {})[g] = {
                "uses": len(hs),
                "words": w,
                "per_million": round(rate(o, w), 4) if w else None,
                "masonic_term_in_window": co(hs, d["window_words"] + 1),
                "masonic_term_within_near": co(hs, d["near_words"]),
            }
    news = [h for h in hits if h["group"] == "newspapers" and h["date"]]
    states = Counter(h["state"] or "unknown" for h in news)
    return {
        "counts_by_period": table,
        "newspaper_uses_before_after_morgan": {
            "date": d["morgan_date"],
            "before": sum(h["date"] < d["morgan_date"] for h in news),
            "after": sum(h["date"] >= d["morgan_date"] for h in news),
        },
        "newspaper_uses_by_state": dict(states.most_common()),
        "controls_counts": sc["controls"],
        "translations_counts_by_year": {
            y: {"uses": v["all"], "exact": v["exact"], "words": v["words"]}
            for y, v in sc["by_year"].get("translations", {}).items()
        },
    }


def run(cfg: dict) -> dict:
    d = settings(cfg)
    sc = load_scan(cfg)
    chk = check(cfg)
    res: dict = {
        "settings_sha256": settings_hash(cfg),
        "config_sha256": config.sha256_of_config(),
        "commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "known_answer": chk,
        "scan": {
            "read": sc["read"],
            "unreadable_not_attempted": sc["unreadable_not_attempted"],
            "uses_total": sc["uses_total"],
        },
    }
    hits = [h for h in load_hits() if h["group"] in ("works", "newspapers")]
    if not chk["passed"]:
        res["stopped"] = (
            "the known-answer check missed its bar: counts by year only, no classification, "
            "the Book of Mormon was not scored"
        )
        counts = {}
        for g, ys in sc["by_year"].items():
            counts[g] = {
                y: {"uses": v["all"], "exact": v["exact"], "words": v["words"],
                    "per_million": round(rate(v["all"], v["words"]), 4) if v["words"] else None}
                for y, v in ys.items()
            }  # fmt: skip
        res["counts_by_year"] = counts
        res.update(unclassified_counts(sc, hits, d))
        res["judge_jobs"] = judge_jobs(cfg)
        return res
    allhits = load_hits()
    cats = compile_categories(d)
    res["books_by_year"] = yearly(sc, hits, cats, d, "works")
    res["newspapers_by_year"] = yearly(sc, hits, cats, d, "newspapers")
    res["by_period"] = {
        "books": periods(sc, hits, cats, d, ("works",)),
        "newspapers": periods(sc, hits, cats, d, ("newspapers",)),
        "pooled": periods(sc, hits, cats, d, ("works", "newspapers")),
    }
    res["newspapers_before_after_morgan"] = morgan_split(hits, cats, d)
    res["newspapers_by_state"] = by_state(hits, cats, d)
    res["books_by_genre_1826_1830"] = genre_table(hits, cats, d)
    res["verdict"] = verdict(res["by_period"]["pooled"], d)
    res["controls"] = control_tables(sc, allhits, cats, d)
    res["book_of_mormon"] = bom_uses(d)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["scan", "check", "run", "jobs"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "scan":
        res = scan(cfg)
        print(json.dumps({k: res[k] for k in ("read", "unreadable_not_attempted", "uses_total",
                                                "seconds")}))  # fmt: skip
    elif a.cmd == "check":
        print(json.dumps(check(cfg), indent=1))
    elif a.cmd == "jobs":
        print(judge_jobs(cfg))
    else:
        res = run(cfg)
        out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: res[k] for k in ("known_answer", "verdict") if k in res}, indent=1))
        if "stopped" in res:
            print(res["stopped"], res["judge_jobs"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
