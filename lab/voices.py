"""BOM-121: voice diversity among the book's speakers, against single-author multi-speaker works.

Rerun of the claim (Fields, Bassist and Roper, about 2021) that the Book of Mormon's speakers
differ from one another by function-word measures more than the characters of novels by single
authors. Every voice is one window of ``sample_words`` consecutive words of one speaker's
speech (equal sizes, so unequal word counts do not matter), measured on the ``mfw`` most frequent
words of a neutral library sample and z-scored against it. The spread of a set of K voices is the
mean pairwise Burrows's Delta, and the "volume" (product of the voices' standard deviations on the
first principal components of the background). Comparison sets, all drawn at random many times:
(a) the top K speakers of one play; (a2) the lead speakers of K plays by one author; (b) the
lead speakers of K plays by K different authors; floors that ignore speakers. The plays are the
Text Creation Partnership plays printed 1660-1700 (speaker prefixes parsed; one hand-keyed
spelling regime). The known-answer check (different authors against one author's characters,
held out: nothing is fitted on a play) comes first; the book is scored only if it passes. Controls:
Bible-style books of 1810-1829 (floor and between-book spread), translated plays, Joseph Smith's
dictations (floor) and one writer's two voices (the BOM-105 set). The book's speakers are the
study's labelling (``eval/speakers.py``; an AI labelling, simulated). No model, no GPU. The test
card, written first, is ``data/private/lab/owner/2026-11-21-voice-diversity/card.md``; settings
are ``lab.voices`` in the config. The result holds ids and numbers, no text.

Usage::

    python -m lab.voices set      # -> data/lab/reruns/voice_diversity/set.json (the plays)
    python -m lab.voices check    # known-answer check only (prints it)
    python -m lab.voices run      # -> data/lab/reruns/voice_diversity/result.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pyarrow.compute as pc

from lab import door, registry, twovoices
from lab.paths import FAST, REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "voice_diversity"
SPEAKER = re.compile(r"^ ([A-Z][A-Za-z]{0,14}(?: [A-Za-z]{1,10})?\.?)\s*$")
WORD = re.compile(r"[a-z]+")
JS = Path("data/private/candidates")


# ------------------------------------------------------------------------------ plays


def parse_play(text: str, cfg: dict) -> tuple[dict[str, list[str]], list[str]]:
    """({speaker: words of their speech}, all speech in play order), from a Text Creation
    Partnership play: a speaker line is ``" Abbrev."`` alone on a line, the speech follows on
    unindented lines until the next marker; stage directions (``stage_start``) are dropped."""
    t = cfg["lab"]["voices"]
    stage = re.compile(t["stage_start"])
    skip = set(t["not_speakers"])
    by: dict[str, list[str]] = defaultdict(list)
    ordered: list[str] = []
    cur = None
    for line in text.split("\n"):
        m = SPEAKER.match(line)
        if m:
            name = m.group(1).rstrip(".").lower()
            cur = None if name in skip else name
            continue
        if cur is None or line.startswith(" ") or not line.strip() or stage.match(line):
            continue
        words = WORD.findall(line.lower())
        by[cur].extend(words)
        ordered.extend(words)
    return dict(by), ordered


def genre_of(title: str) -> str:
    low = title.lower()
    if re.search(r"\bcomed(y|ie)\b", low) and not re.search(r"trag", low):
        return "comedy"
    if re.search(r"\btrag", low):
        return "tragedy"
    return "other"


def play_rows(cfg: dict) -> list[dict]:
    """Registry rows (with title and author) of the comparison plays, translated or not."""
    t = cfg["lab"]["voices"]
    tab = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(tab["kind"], "work"), pc.equal(tab["source"], t["play_source"])),
        pc.and_(pc.equal(tab["has_text"], True), pc.equal(tab["dup_keeper"], True)),
    )
    rows = [
        r
        for r in tab.filter(keep).to_pylist()
        if not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and t["play_year_min"] <= r["year"] <= t["play_year_max"]
        and (r["words"] or 0) >= t["play_min_words"]
    ]
    cat = door.catalog({r["work_id"] for r in rows})
    title = re.compile(t["play_title"], re.I)
    res = []
    for r in sorted(rows, key=lambda r: r["work_id"]):
        c = cat.get(r["work_id"])
        if not c or not c.get("text_path") or not title.search(c["title"] or ""):
            continue
        res.append({**r, "title": c["title"], "author": c["author"] or "", "_cat": c})
    return res


def load_plays(cfg: dict) -> tuple[list[dict], dict]:
    """Parsed plays; an unreadable text is "not attempted" (listed), never an empty play."""
    t = cfg["lab"]["voices"]
    trans = re.compile(t["translation_title"], re.I)
    plays, failed = [], {}
    for r in play_rows(cfg):
        try:
            text = door.text_of(r["_cat"])
        except OSError as e:
            failed[r["work_id"]] = str(e)
            continue
        by, ordered = parse_play(text, cfg)
        plays.append(
            {
                "id": r["work_id"],
                "year": r["year"],
                "author": r["author"].split(";")[0].strip(),
                "genre": genre_of(r["title"]),
                "translated": bool(trans.search(r["title"] or "")),
                "speech": by,
                "ordered": ordered,
            }
        )
    return plays, failed


# ------------------------------------------------------------------------------ measures


class Ctx:
    """Features, z-scores and background principal components for one window size."""

    def __init__(self, windows: list[list[str]], cfg: dict, size: int):
        t = cfg["lab"]["voices"]
        self.size = size
        self.feats = twovoices.features(windows, t["mfw"], set())
        self.index = {w: i for i, w in enumerate(self.feats)}
        self.nf = len(self.feats)
        mu, sd = twovoices.scaler(windows, self.feats, size)
        self.mu, self.sd = mu, sd
        m = np.array([(twovoices.relfreq(ch, self.feats) - mu) / sd
                      for w in windows for ch in twovoices.chunks(w, size)])  # fmt: skip
        _, _, vt = np.linalg.svd(m - m.mean(axis=0), full_matrices=False)
        self.pcs = vt[: t["pc_count"]]

    def ids(self, toks: list[str]) -> np.ndarray:
        return np.array([self.index.get(w, self.nf) for w in toks], dtype=np.int16)

    def z(self, arr: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        s = int(rng.integers(0, len(arr) - self.size + 1))
        counts = np.bincount(arr[s : s + self.size], minlength=self.nf + 1)[: self.nf]
        return (counts / self.size - self.mu) / self.sd

    def spread(self, zs: list[np.ndarray]) -> tuple[float, float]:
        """(mean pairwise Burrows's Delta, volume on the background principal components)."""
        z = np.array(zs)
        k = len(z)
        d = np.abs(z[:, None, :] - z[None, :, :]).mean(axis=2)
        delta = float(d[np.triu_indices(k, 1)].mean())
        vol = float(np.prod((z @ self.pcs.T).std(axis=0, ddof=1)))
        return delta, vol


def quantiles(xs) -> dict:
    a = np.array(xs, dtype=float)
    return {
        "n": int(len(a)),
        "mean": round(float(a.mean()), 4),
        "q2.5": round(float(np.percentile(a, 2.5)), 4),
        "median": round(float(np.median(a)), 4),
        "q97.5": round(float(np.percentile(a, 97.5)), 4),
    }


def share_below(ref, x: float) -> float:
    """Share of reference values at or below ``x`` (ties count half)."""
    a = np.sort(np.array(ref, dtype=float))
    lo, hi = np.searchsorted(a, x, "left"), np.searchsorted(a, x, "right")
    return round(float((lo + hi) / 2 / len(a)), 4)


def auc(high, low) -> float:
    """Share of (high, low) pairs where high is larger (ties count half)."""
    lo = np.sort(np.array(low, dtype=float))
    a, b = np.searchsorted(lo, high, "left"), np.searchsorted(lo, high, "right")
    return round(float(((a + b) / 2).sum() / (len(high) * len(lo))), 4)


# ------------------------------------------------------------------------------ pools


def pools(plays: list[dict], ctx: Ctx, k: int, cfg: dict, genre: str | None = None) -> dict:
    """Index arrays by play for plays that can give ``k`` voices of ``ctx.size`` words, and the
    authors with enough plays for same-author sets."""
    t = cfg["lab"]["voices"]
    size = ctx.size
    use = [p for p in plays if not p["translated"] and (genre is None or p["genre"] == genre)]
    tops, lead = [], {}
    for p in use:
        big = sorted(((len(v), n) for n, v in p["speech"].items() if len(v) >= size), reverse=True)
        if big:
            lead[p["id"]] = (p, big[0][1])
        if len(big) >= k:
            tops.append((p, [n for _, n in big[:k]]))
    by_author: dict[str, list[str]] = defaultdict(list)
    for pid, (p, _) in lead.items():
        by_author[p["author"]].append(pid)
    authors = {
        a: ids for a, ids in by_author.items() if a and len(ids) >= max(t["min_author_plays"], k)
    }
    return {"tops": tops, "lead": lead, "authors": authors}


def draw_sets(plays: list[dict], ctx: Ctx, k: int, cfg: dict, genre: str | None, seed: int):
    """Spreads (delta, volume) for each kind of comparison set; empty where the pool cannot
    give a set ("not attempted")."""
    t = cfg["lab"]["voices"]
    rng = np.random.default_rng(seed)
    pl = pools(plays, ctx, k, cfg, genre)
    cache: dict = {}

    def arr(p: dict, name: str) -> np.ndarray:
        key = (p["id"], name)
        if key not in cache:
            cache[key] = ctx.ids(p["speech"][name])
        return cache[key]

    def whole(p: dict) -> np.ndarray:
        key = (p["id"], None)
        if key not in cache:
            cache[key] = ctx.ids(p["ordered"])
        return cache[key]

    res: dict[str, list] = {"within_play": [], "same_author": [], "different_authors": [],
                            "floor_play": []}  # fmt: skip
    info = {"plays_with_k_voices": len(pl["tops"]), "authors_with_enough_plays": len(pl["authors"]),
            "plays_with_a_lead": len(pl["lead"])}  # fmt: skip
    if pl["tops"]:
        for _ in range(t["draws"]):
            p, names = pl["tops"][int(rng.integers(len(pl["tops"])))]
            res["within_play"].append(ctx.spread([ctx.z(arr(p, n), rng) for n in names]))
            res["floor_play"].append(ctx.spread([ctx.z(whole(p), rng) for _ in range(k)]))
    names_a = sorted(pl["authors"])
    if names_a:
        for _ in range(t["draws"]):
            a = names_a[int(rng.integers(len(names_a)))]
            ids = pl["authors"][a]
            pick = rng.choice(len(ids), size=k, replace=False)
            zs = []
            for j in pick:
                p, n = pl["lead"][ids[int(j)]]
                zs.append(ctx.z(arr(p, n), rng))
            res["same_author"].append(ctx.spread(zs))
    if len(names_a) >= k:
        for _ in range(t["draws"]):
            pick = rng.choice(len(names_a), size=k, replace=False)
            zs = []
            for j in pick:
                ids = pl["authors"][names_a[int(j)]]
                p, n = pl["lead"][ids[int(rng.integers(len(ids)))]]
                zs.append(ctx.z(arr(p, n), rng))
            res["different_authors"].append(ctx.spread(zs))
    return res, info


def column(draws: list, i: int) -> list[float]:
    return [d[i] for d in draws]


# ------------------------------------------------------------------------------ the book


def book_speakers() -> tuple[dict[str, list[str]], list[str]]:
    """({speaker: words}, all words in book order) from the study's labelling; ``other: ...``
    labels are not speakers here (each is a sliver of the text)."""
    from eval import speakers

    by = {s: [w for w in " ".join(ws).split()] for s, ws in speakers.speaker_words().items()}
    allw: list[str] = []
    for c in speakers.chapters():
        allw.extend(WORD.findall(c["text"].lower()))
    by = {
        s: WORD.findall(" ".join(ws).lower()) for s, ws in by.items() if not s.startswith("other")
    }
    return by, allw


def score_book(by: dict, allw: list[str], ctx: Ctx, k: int, cfg: dict, seed: int) -> dict:
    t = cfg["lab"]["voices"]
    rng = np.random.default_rng(seed)
    ranked = sorted(((len(v), s) for s, v in by.items() if len(v) >= ctx.size), reverse=True)
    names = [s for _, s in ranked[:k]]
    if len(names) < k:
        return {"not_attempted": f"only {len(names)} speakers with {ctx.size} words"}
    arrs = [ctx.ids(by[s]) for s in names]
    whole = ctx.ids(allw)
    sp = [ctx.spread([ctx.z(a, rng) for a in arrs]) for _ in range(t["draws"])]
    fl = [ctx.spread([ctx.z(whole, rng) for _ in range(k)]) for _ in range(t["draws"])]
    return {
        "speakers": {s: len(by[s]) for s in names},
        "delta": quantiles(column(sp, 0)),
        "volume": quantiles(column(sp, 1)),
        "floor_delta": quantiles(column(fl, 0)),
        "floor_volume": quantiles(column(fl, 1)),
        "_delta": column(sp, 0),
        "_volume": column(sp, 1),
    }


def mean_of(draws: list, i: int) -> float:
    return float(np.mean(column(draws, i)))


def verdict(book: dict, refs: dict, passed: dict, cfg: dict) -> dict:
    """Per measure that passed the known-answer check: where the book's median stands among the
    single-author sets (a) and (a2)."""
    t = cfg["lab"]["voices"]
    res = {}
    for i, m in enumerate(("delta", "volume")):
        if not passed.get(m):
            res[m] = "not scored (known-answer check missed)"
            continue
        x = book[m]["median"]
        shares = {kind: share_below(column(refs[kind], i), x)
                  for kind in ("within_play", "same_author") if refs.get(kind)}  # fmt: skip
        if len(shares) < 2:
            res[m] = {"verdict": "cannot tell (a reference pool is empty)", "shares": shares}
            continue
        if all(s > t["larger_share"] for s in shares.values()):
            v = "beyond"
        elif any(s <= t["typical_share"] for s in shares.values()):
            v = "within the range"
        else:
            v = "at the edge"
        diff = refs.get("different_authors")
        res[m] = {
            "verdict": v,
            "book_median": x,
            "share_of_single_author_sets_below_book": shares,
            "ratio_to_mean_within_play": round(x / mean_of(refs["within_play"], i), 3),
            "ratio_to_mean_same_author": round(x / mean_of(refs["same_author"], i), 3),
            "ratio_to_median_different_authors": round(
                x / float(np.median(column(diff, i))), 3) if diff else None,
            "ratio_to_book_floor": round(x / book["floor_" + m]["median"], 3),
        }  # fmt: skip
    return res


# ------------------------------------------------------------------------------ controls


def background_windows(cfg: dict, vocab: set, grams) -> list[list[str]]:
    shim = {"lab": {"two_voices": cfg["lab"]["voices"]}}
    return twovoices.background(shim, vocab, grams)


def bible_style(ctx: Ctx, cfg: dict, vocab: set, grams, seed: int) -> dict:
    """Control 1: floor (K windows of one book) and between-book spread (one window from each of
    the Bible-style books of 1810-1829); no speaker labels exist, so there is no within-book set."""
    t = cfg["lab"]["voices"]
    shim = {"lab": {"two_voices": cfg["lab"]["two_voices"]}}
    rng = np.random.default_rng(seed)
    books, missing = {}, {}
    for rel in t["bible_style_files"]:
        try:
            text, _ = twovoices.read_source(("file", str(FAST / rel), None, None), shim)
        except OSError as e:
            missing[rel] = str(e)
            continue
        toks, _ = twovoices.tokens(text, vocab)
        if grams is not None:
            toks = twovoices.drop_kjv(toks, grams, t["kjv_ngram"])
        if len(toks) >= max(t["bible_style_min_words"], ctx.size):
            p = Path(rel)
            books[p.parent.name if p.stem == "text" else p.stem] = ctx.ids(toks)
    res: dict = {"books": {b: len(a) for b, a in books.items()}, "not_attempted": missing}
    k = len(books)
    if k < 3:
        res["not_attempted_reason"] = "fewer than 3 books"
        return res
    floors = [ctx.spread([ctx.z(a, rng) for _ in range(k)]) for a in books.values()
              for _ in range(t["draws"] // k)]  # fmt: skip
    between = [ctx.spread([ctx.z(a, rng) for a in books.values()]) for _ in range(t["draws"])]
    res["k"] = k
    res["floor"] = {"delta": quantiles(column(floors, 0)), "volume": quantiles(column(floors, 1))}
    res["between_books"] = {"delta": quantiles(column(between, 0)),
                            "volume": quantiles(column(between, 1))}  # fmt: skip
    return res


def dictations(ctx: Ctx, cfg: dict, vocab: set, grams, k: int, seed: int) -> dict:
    """Control 3: floor among K windows of Joseph Smith's 1828-1833 revelation text (private
    samples; numbers only)."""
    t = cfg["lab"]["voices"]
    shim = {"lab": {"two_voices": cfg["lab"]["two_voices"]}}
    rng = np.random.default_rng(seed)
    srcs = [("file", str(JS / "samples" / "joseph-smith__dictated__pre1830.txt"), None, None),
            ("glob", str(JS / "later" / "*.txt"), None, None)]  # fmt: skip
    toks: list[str] = []
    try:
        for s in srcs:
            text, _ = twovoices.read_source(s, shim)
            toks.extend(twovoices.tokens(text, vocab)[0])
    except OSError as e:
        return {"not_attempted": str(e)}
    if grams is not None:
        toks = twovoices.drop_kjv(toks, grams, t["kjv_ngram"])
    if len(toks) < ctx.size * k:
        return {"not_attempted": f"only {len(toks)} words"}
    arr = ctx.ids(toks)
    fl = [ctx.spread([ctx.z(arr, rng) for _ in range(k)]) for _ in range(t["draws"])]
    return {"words": len(toks), "floor": {"delta": quantiles(column(fl, 0)),
                                           "volume": quantiles(column(fl, 1))}}  # fmt: skip


def two_voice_gaps(ctx: Ctx, cfg: dict, vocab: set, seed: int) -> dict:
    """The issue's cross-genre reference: for each writer of the BOM-105 set, the median Delta
    between one window of the prophetic voice and one of the ordinary voice (one pair, so
    the same units as the pairwise spread). Joseph Smith's dictations are the prophetic side."""
    t = cfg["lab"]["voices"]
    rng = np.random.default_rng(seed)
    record, texts = twovoices.build_set(cfg, vocab)
    res = {"not_attempted": record["not_attempted"], "too_little_text": record["too_little_text"]}
    gaps = {}
    for w, tv in texts.items():
        a, b = ctx.ids(tv["prophetic"]), ctx.ids(tv["ordinary"])
        if min(len(a), len(b)) < ctx.size:
            continue
        ds = [ctx.spread([ctx.z(a, rng), ctx.z(b, rng)])[0] for _ in range(t["draws"])]
        gaps[w] = {"group": record["writers"][w]["group"], **quantiles(ds)}
    res["writers"] = gaps
    return res


def coverage(cfg: dict, plays: list[dict]) -> dict:
    """Library works of the study's single-book rule set by decade, and the plays used."""
    tab = registry.view("work-search", cfg)
    dec = Counter((y // 10) * 10 for y in tab["year"].to_pylist() if y)
    used = Counter((p["year"] // 10) * 10 for p in plays if not p["translated"])
    return {"rule_set": "work-search", "works_by_decade": dict(sorted(dec.items())),
            "plays_by_decade": dict(sorted(used.items()))}  # fmt: skip


# ------------------------------------------------------------------------------ the run


def known_answer(refs: dict, refs_comedy: dict, cfg: dict) -> dict:
    t = cfg["lab"]["voices"]
    res: dict = {"bar_all_plays": t["known_bar"], "bar_comedies": t["known_bar_genre"]}
    passed = {}
    for i, m in enumerate(("delta", "volume")):
        row = {}
        for tag, r, bar in (("all_plays", refs, t["known_bar"]),
                            ("comedies", refs_comedy, t["known_bar_genre"])):  # fmt: skip
            if r.get("different_authors") and r.get("same_author"):
                a = auc(column(r["different_authors"], i), column(r["same_author"], i))
                row[tag] = {"auc": a, "passed": a >= bar}
            else:
                row[tag] = {"auc": None, "passed": False, "not_attempted": "pool too small"}
        res[m] = row
        passed[m] = all(v["passed"] for v in row.values())
    res["passed"] = passed
    return res


def setting(plays, windows, windows_kjv, grams, vocab, cfg, k, size, seed, full: bool) -> dict:
    """Everything for one (voices, words) setting; ``full`` adds the controls."""
    out_: dict = {"k": k, "words": size}
    ctx = Ctx(windows, cfg, size)
    refs, info = draw_sets(plays, ctx, k, cfg, None, seed)
    refs_c, info_c = draw_sets(plays, ctx, k, cfg, "comedy", seed + 1)
    out_["pools"] = {"all_plays": info, "comedies": info_c}
    out_["known_answer"] = known_answer(refs, refs_c, cfg)
    for name, r in (("within_play", refs["within_play"]), ("same_author", refs["same_author"]),
                    ("different_authors", refs["different_authors"]),
                    ("floor_play", refs["floor_play"])):  # fmt: skip
        if r:
            out_[name] = {"delta": quantiles(column(r, 0)), "volume": quantiles(column(r, 1))}
    for name in ("within_play", "same_author", "different_authors"):
        if refs_c[name]:
            out_[name + "_comedies"] = {"delta": quantiles(column(refs_c[name], 0)),
                                        "volume": quantiles(column(refs_c[name], 1))}  # fmt: skip
    out_["_refs"] = refs
    out_["_refs_comedy"] = refs_c
    out_["_ctx"] = ctx
    return out_


def run(cfg: dict, check_only: bool = False) -> dict:
    t = cfg["lab"]["voices"]
    vocab, grams = twovoices.kjv_vocab_and_grams(t["kjv_ngram"])
    plays, failed = load_plays(cfg)
    windows = background_windows(cfg, vocab, None)
    res: dict = {"settings": t, "rule_set": "plays: registry source tcp, kind work, kept copy, "
                 "OCR not excluded, years play_year_min-play_year_max, title match; background: "
                 "library works by one personal author, years year_min-year_max",
                 "plays_read": len(plays), "plays_not_attempted": failed,
                 "background_works": len(windows),
                 "plays_translated": sum(p["translated"] for p in plays)}  # fmt: skip
    k, size, seed = t["k_voices"], t["sample_words"], t["seed"]
    main = setting(plays, windows, None, grams, vocab, cfg, k, size, seed, True)
    res["known_answer"] = main["known_answer"]
    if check_only:
        return res
    passed = main["known_answer"]["passed"]
    if not any(passed.values()):
        res["stopped"] = (
            "the known-answer check missed its bar for every measure; the book was not scored"
        )
        return res
    by, allw = book_speakers()
    ranked = sorted(by.items(), key=lambda x: -len(x[1]))
    res["book_speakers_labelled"] = {s: len(v) for s, v in ranked if len(v) >= size}
    res["coverage"] = coverage(cfg, plays)
    ctx = main["_ctx"]
    book = score_book(by, allw, ctx, k, cfg, seed + 10)
    res["main"] = {k_: v for k_, v in main.items() if not k_.startswith("_")}
    res["main"]["book"] = {k_: v for k_, v in book.items() if not k_.startswith("_")}
    if "not_attempted" not in book:
        res["main"]["verdict"] = verdict(book, main["_refs"], passed, cfg)
        res["main"]["verdict_comedies"] = verdict(book, main["_refs_comedy"], passed, cfg)
    # Controls (at the main setting).
    rng_seed = seed + 20
    res["controls"] = {
        "bible_style_1810_1829": bible_style(ctx, cfg, vocab, None, rng_seed),
        "translated_plays": translated(plays, windows, cfg, rng_seed + 1),
        "joseph_smith_dictations": dictations(ctx, cfg, vocab, None, k, rng_seed + 2),
        "two_voices_one_writer": two_voice_gaps(ctx, cfg, vocab, rng_seed + 3),
    }
    # Variants: other (voices, words), and King James 5-grams dropped.
    res["variants"] = {}
    for kk, ss in t["variants"]:
        v = setting(plays, windows, None, grams, vocab, cfg, kk, ss, seed + 100 + kk + ss, False)
        vb = score_book(by, allw, v["_ctx"], kk, cfg, seed + 200 + kk + ss)
        row = {k_: x for k_, x in v.items() if not k_.startswith("_")}
        row["book"] = {k_: x for k_, x in vb.items() if not k_.startswith("_")}
        if "not_attempted" not in vb:
            row["verdict"] = verdict(vb, v["_refs"], v["known_answer"]["passed"], cfg)
        res["variants"][f"k{kk}_w{ss}"] = row
    res["variants"]["kjv_5grams_dropped"] = kjv_variant(plays, by, allw, grams, vocab, cfg, k, size)
    return res


def translated(plays: list[dict], windows: list, cfg: dict, seed: int) -> dict:
    """Control 2: spread among the top ``translated_k`` speakers of translated plays (one
    translator each) against original plays at the same setting. Few translated plays have five
    speakers with 2,000 words, so this control uses its own, smaller setting."""
    t = cfg["lab"]["voices"]
    k, size = t["translated_k"], t["translated_words"]
    ctx = Ctx(windows, cfg, size)
    rng = np.random.default_rng(seed)
    res: dict = {"k": k, "words": size, "translated_plays": sum(p["translated"] for p in plays)}
    tops = []
    for p in plays:
        if not p["translated"]:
            continue
        big = sorted(((len(v), n) for n, v in p["speech"].items() if len(v) >= size), reverse=True)
        if len(big) >= k:
            tops.append((p, [n for _, n in big[:k]]))
    res["translated_with_k_voices"] = len(tops)
    if not tops:
        res["not_attempted"] = "no translated play with enough speakers"
        return res
    sets = []
    for _ in range(t["draws"]):
        p, names = tops[int(rng.integers(len(tops)))]
        sets.append(ctx.spread([ctx.z(ctx.ids(p["speech"][n]), rng) for n in names]))
    res["translated_within_play"] = {"delta": quantiles(column(sets, 0)),
                                     "volume": quantiles(column(sets, 1))}  # fmt: skip
    refs, _ = draw_sets(plays, ctx, k, cfg, None, seed + 1)
    res["original_within_play"] = {"delta": quantiles(column(refs["within_play"], 0)),
                                   "volume": quantiles(column(refs["within_play"], 1))}  # fmt: skip
    return res


def kjv_variant(plays, by, allw, grams, vocab, cfg, k, size) -> dict:
    """Tokens covered by a King James word 5-gram dropped from the book, the plays and the
    background alike (the background is rebuilt the same way)."""
    t = cfg["lab"]["voices"]
    n = t["kjv_ngram"]
    kplays = [{**p, "speech": {s: twovoices.drop_kjv(w, grams, n) for s, w in p["speech"].items()},
               "ordered": twovoices.drop_kjv(p["ordered"], grams, n)} for p in plays]  # fmt: skip
    windows = background_windows(cfg, vocab, grams)
    ctx = Ctx(windows, cfg, size)
    seed = t["seed"] + 300
    refs, info = draw_sets(kplays, ctx, k, cfg, None, seed)
    refs_c, _ = draw_sets(kplays, ctx, k, cfg, "comedy", seed + 1)
    ka = known_answer(refs, refs_c, cfg)
    kby = {s: twovoices.drop_kjv(w, grams, n) for s, w in by.items()}
    kall = twovoices.drop_kjv(allw, grams, n)
    book = score_book(kby, kall, ctx, k, cfg, seed + 2)
    row = {"known_answer": ka, "pools": info,
           "book": {k_: v for k_, v in book.items() if not k_.startswith("_")}}  # fmt: skip
    for name in ("within_play", "same_author", "different_authors"):
        if refs[name]:
            row[name] = {"delta": quantiles(column(refs[name], 0)),
                         "volume": quantiles(column(refs[name], 1))}  # fmt: skip
    if "not_attempted" not in book:
        row["verdict"] = verdict(book, refs, ka["passed"], cfg)
    return row


def _strip(o):
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items() if not str(k).startswith("_")}
    return o


def build_set(cfg: dict) -> dict:
    plays, failed = load_plays(cfg)
    t = cfg["lab"]["voices"]
    rec = {
        "plays": {
            p["id"]: {
                "year": p["year"],
                "author": p["author"],
                "genre": p["genre"],
                "translated": p["translated"],
                "speakers_with_sample_words": sum(
                    len(v) >= t["sample_words"] for v in p["speech"].values()
                ),
                "lead_words": max((len(v) for v in p["speech"].values()), default=0),
                "speech_words": len(p["ordered"]),
            }
            for p in plays
        },
        "not_attempted": failed,
    }
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["set", "check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "set":
        rec = build_set(cfg)
        rec["config_sha256"] = config.sha256_of_config()
        out(OUT / "set.json").write_text(json.dumps(rec, indent=1) + "\n")
        print(len(rec["plays"]), "plays;", len(rec["not_attempted"]), "not attempted")
        return 0
    res = _strip(run(cfg, check_only=a.cmd == "check"))
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    if a.cmd == "check":
        print(json.dumps(res["known_answer"], indent=1))
        return 0
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res.get("main", {}).get("verdict", res.get("stopped")), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
