"""BOM-102: does it read like a translation? Translation marks and claimed Hebraisms.

Part A trains a classifier on topic-free features (function-word rates, sentence shape) to tell
books catalogued as translations into English from books written in English (HathiTrust MARC
041 and title phrases; matched by decade and genre; whole authors held out), checks it on known
answers (held-out AUC; the King James Bible, Sale's Koran and Whiston's Josephus must score as
translations; the English Bible-style imitations must not), and only then scores the Book of
Mormon by 1830 book and Joseph Smith's other texts. Part B counts each construction offered as a
Hebraism by a fixed rule per 10,000 words in the Book of Mormon, the King James Old and New
Testaments, other translations from Hebrew, non-Semitic translations, the imitations, ordinary
period prose and Joseph Smith's other texts; a rule must find planted examples and be clearly
more frequent in the King James Old Testament than in period prose, or it is dropped. The Book of
Mormon is never trained or tuned on. Card, written first:
``data/private/lab/owner/2026-11-21-translation-marks/card.md``; settings ``lab.translation``.
The result holds ids and numbers, no text.

Usage::

    python -m lab.translation labels    # labelled set + hand-check sample (card folder) (1 min)
    python -m lab.translation run       # checks, then scores -> data/lab/translation/ (15 min)
    python -m lab.translation run --marc-only   # post hoc: part A on 041 labels only (7 min)
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow.compute as pc

from lab import door, registry
from lab.paths import NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "translation"
CARD = NOTES / "owner" / "2026-11-21-translation-marks"
MARC = Path("data/corpus/lab/sources/translation_labels/hathitrust_marc.jsonl")
HT_CATALOG = Path("data/catalog/hathitrust.jsonl.gz")
KJV = Path("data/kjv/kjv.jsonl")
MASK = Path("data/kjv_mask/bom/spans.jsonl")

TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?|[.!?;:,()]")
STOP = frozenset(".!?")
PUNCT = frozenset(".!?;:,()")

# Long s read as f by OCR in 18th-century prints: the function words it damages most.
LONG_S = {
    "fo": "so",
    "fome": "some",
    "fuch": "such",
    "thofe": "those",
    "thefe": "these",
    "himfelf": "himself",
    "itfelf": "itself",
    "herfelf": "herself",
    "myfelf": "myself",
    "themfelves": "themselves",
    "yourfelves": "yourselves",
    "ourfelves": "ourselves",
    "fhall": "shall",
    "fhould": "should",
    "faid": "said",
    "firft": "first",
    "muft": "must",
    "alfo": "also",
    "becaufe": "because",
    "whofe": "whose",
    "juft": "just",
    "moft": "most",
    "leaft": "least",
    "againft": "against",
    "amongft": "amongst",
    "whilft": "whilst",
    "fince": "since",
    "fhe": "she",
    "felf": "self",
    "lefs": "less",
    "unlefs": "unless",
    "ftill": "still",
    "feveral": "several",
}

# Modern English function words (articles, pronouns, prepositions, conjunctions, auxiliaries,
# modals, quantifiers, common adverbs). King James register words are kept apart in ARCHAIC.
FUNCTION_WORDS = tuple(
    """a about above across after afterwards again against all almost alone along already also
    although always am among amongst an and another any anyone anything anywhere are around as at
    be became because become been before beforehand behind being below beside besides between
    beyond both but by can cannot could did do does doing done down during each either else
    enough even ever every everything except few first for former formerly from further had has
    have having he hence her here hereby herein hers herself him himself his how however i if in
    indeed into is it its itself last latter least less many may me meanwhile might mine more
    moreover most mostly much must my myself namely neither never nevertheless next no nobody
    none nor not nothing now nowhere of off often on once one only onto or other others otherwise
    our ours ourselves out over own perhaps rather same seem seemed seems several shall she should
    since so some somehow someone something sometimes somewhat still such than that the their
    theirs them themselves then thence there thereby therefore therein thereupon these they this
    those though through throughout thus till to together too toward towards under until up upon
    us very was we well were what whatever when whence whenever where whereas whereby wherein
    whereupon wherever whether which while whilst whither who whoever whole whom whose why will
    with within without would yet you your yours yourself yourselves said made like upon quite
    just ago soon almost far near yes nay o oh let make get go went come came""".split()
)
ARCHAIC = tuple(
    """thou thee thy thine ye hath doth dost hast art shalt wilt canst couldst wouldst shouldst
    unto behold yea lo verily wherefore saith spake thereof whereof hither thither ere
    nigh""".split()
)
SHAPE = (
    "sent_mean",
    "sent_sd",
    "and_start",
    "comma",
    "semicolon",
    "colon",
    "question",
    "exclaim",
    "paren",
    "word_len",
    "ttr",
    "eth",
)


# ----------------------------------------------------------------------------- text and features


def tokens(text: str) -> list[str]:
    return [LONG_S.get(t, t) for t in TOKEN.findall(text.lower())]


def chunks(toks: list[str], size: int, n: int | None, trim: float) -> list[list[str]]:
    """Up to ``n`` chunks of ``size`` words (punctuation rides along), evenly spaced after
    trimming ``trim`` of the words from each end; ``n`` None = every consecutive chunk."""
    starts = [i for i, t in enumerate(toks) if t not in PUNCT]
    if len(starts) < size:
        return []
    cut = int(len(starts) * trim) if n is not None else 0
    starts = starts[cut : len(starts) - cut] if len(starts) - 2 * cut >= size else starts
    whole = len(starts) // size
    picks = range(whole) if n is None else sorted({int(k * whole / n) for k in range(n)})
    out_ = []
    for k in picks:
        if k >= whole:
            continue
        a = starts[k * size]
        b = starts[(k + 1) * size] if (k + 1) * size < len(starts) else len(toks)
        out_.append(toks[a:b])
    return out_


def features(chunk: list[str], archaic: bool = False) -> list[float]:
    words = [t for t in chunk if t not in PUNCT]
    n = max(len(words), 1)
    c = Counter(words)
    vec = [c[w] / n for w in FUNCTION_WORDS]
    if archaic:
        vec += [c[w] / n for w in ARCHAIC]
    sents, cur = [], []
    for t in chunk:
        if t in STOP:
            if cur:
                sents.append(cur)
            cur = []
        elif t not in PUNCT:
            cur.append(t)
    if cur:
        sents.append(cur)
    lens = [len(s) for s in sents] or [n]
    p = Counter(t for t in chunk if t in PUNCT)
    vec += [
        statistics.fmean(lens),
        statistics.pstdev(lens),
        sum(1 for s in sents if s[0] == "and") / max(len(sents), 1),
        p[","] / n,
        p[";"] / n,
        p[":"] / n,
        p["?"] / n,
        p["!"] / n,
        p["("] / n,
        statistics.fmean(len(w) for w in words) if words else 0.0,
        len(c) / n,
        (sum(v for w, v in c.items() if w.endswith("eth") and len(w) > 4) / n) if archaic else 0.0,
    ]
    return vec


# ----------------------------------------------------------------------------- labels (A)

LANG_WORDS = {
    "french": "fre",
    "german": "ger",
    "latin": "lat",
    "greek": "grc",
    "spanish": "spa",
    "italian": "ita",
    "hebrew": "heb",
    "arabic": "ara",
    "dutch": "dut",
    "persian": "per",
    "portuguese": "por",
    "danish": "dan",
    "swedish": "swe",
}
LANG_NORM = {"gre": "grc", "und": None, "": None}


def marc_records() -> dict[str, list[dict]]:
    return {r["ht_bib_key"]: r["fields"] for r in map(json.loads, MARC.read_text().splitlines())}


def marc_status(fields: list[dict]) -> tuple[str, str | None]:
    """("T", lang) for 041 ind1 1; ("U", None) if 240/546/765 or 041 ind1 0 non-English;
    ("N", None) for no mark at all (or 041 ind1 0 English only)."""
    for f in fields:
        if f["tag"] == "041" and f["ind1"] == "1":
            hs = [s[1][:3] for s in f["subfields"] if s[0] == "h"]
            lang = hs[0] if hs else None
            return "T", LANG_NORM.get(lang, lang)
    if any(f["tag"] in ("240", "546", "765") for f in fields):
        return "U", None
    return "N", None


def title_lang(text: str) -> str | None:
    m = re.search(r"(?:from|out of) the (?:original )?([a-z]+)", text.lower())
    return LANG_WORDS.get(m.group(1)) if m else None


def _key(s: str | None) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())


def labelled(cfg: dict, marc_only: bool = False) -> list[dict]:
    """The matched set: translations (label 1) and originals (label 0), one row per book.
    ``marc_only`` (post hoc revision): translations only from MARC 041; title-phrase-only books
    are left out of both sides."""
    t = cfg["lab"]["translation"]
    trx, exc = re.compile(t["translation_title"], re.I), re.compile(t["exclude_title"], re.I)
    tab = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(tab["kind"], "work"), pc.equal(tab["has_text"], True)),
        pc.equal(tab["source"], "hathitrust"),
    )
    reg = {
        r["work_id"]: r
        for r in tab.filter(keep)
        .select(["work_id", "year", "words", "genre", "sealed", "ocr_excluded"])
        .to_pylist()
        if not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and t["year_min"] <= r["year"] <= t["year_max"]
        and (r["words"] or 0) >= t["min_words"]
    }
    ht = {}
    with gzip.open(HT_CATALOG, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            wid = "hathitrust:" + r["htid"]
            if wid in reg:
                ht[wid] = r
    marc = marc_records()
    cat = door.catalog(set(ht))
    rows, seen_bib, seen_title = [], set(), set()
    for wid in sorted(ht):
        h, g = ht[wid], reg[wid]
        if h["ht_bib_key"] in seen_bib:
            continue
        seen_bib.add(h["ht_bib_key"])
        title, author = h["title"] or "", h["author"] or ""
        if exc.search(title) or t["exclude_genre"] in (g["genre"] or ""):
            continue
        status, lang = marc_status(marc.get(h["ht_bib_key"], []))
        phrase = bool(trx.search(title) or trx.search(author))
        if marc_only and phrase and status != "T":
            continue
        if status == "T" or phrase:
            label, lang = 1, lang or title_lang(title)
        elif status == "N" and h["lang"] == "eng":
            label = 0
        else:
            continue
        akey = (cat.get(wid) or {}).get("author_norm") or _key(re.sub(r"[\d,.\-?]+", "", author))
        tkey = (akey, _key(title)[:30])
        if tkey in seen_title:
            continue
        seen_title.add(tkey)
        rows.append(
            {
                "work_id": wid,
                "label": label,
                "lang": lang if label else "eng",
                "marc_041": status == "T",
                "title_phrase": phrase,
                "year": g["year"],
                "genre": (g["genre"] or "none").split(",")[0],
                "group": akey or "anon:" + tkey[1],
                "words": g["words"],
            }
        )
    trans_authors = {r["group"] for r in rows if r["label"] == 1}
    tr = [r for r in rows if r["label"] == 1]
    orig = [r for r in rows if r["label"] == 0 and r["group"] not in trans_authors]
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for r in orig:
        cells[(r["year"] // 10, r["genre"])].append(r)
    need = Counter((r["year"] // 10, r["genre"]) for r in tr)
    rng = random.Random(t["seed"])
    picked = []
    for cell in sorted(need):
        pool = sorted(cells.get(cell, []), key=lambda r: r["work_id"])
        rng.shuffle(pool)
        picked += pool[: t["originals_ratio"] * need[cell]]
    return tr + picked


def hand_sample(cfg: dict, rows: list[dict]) -> list[dict]:
    t = cfg["lab"]["translation"]
    rng = random.Random(t["seed"] + 7)
    got = []
    for lab_ in (1, 0):
        side = sorted((r for r in rows if r["label"] == lab_), key=lambda r: r["work_id"])
        got += rng.sample(side, min(t["hand_check"], len(side)))
    return got


def hand_accuracy(rows: list[dict]) -> dict | None:
    p = CARD / "hand_check.json"
    if not p.exists():
        return None
    marks = json.loads(p.read_text())
    res = {}
    for lab_, name in ((1, "translations"), (0, "originals")):
        ids = [r["work_id"] for r in rows if r["label"] == lab_ and r["work_id"] in marks]
        ok = sum(1 for i in ids if marks[i])
        res[name] = {"read": len(ids), "correct": ok, "accuracy": round(ok / max(len(ids), 1), 3)}
    return res


# ----------------------------------------------------------------------------- texts


def _text_of_id(wid: str) -> str | None:
    row = door.catalog({wid}).get(wid)
    try:
        return door.text_of(row) if row else None
    except OSError:
        return None  # not attempted


def _book_feats(job: tuple[str, int, int, float, bool]) -> tuple[str, list[list[float]] | None]:
    wid, size, n, trim, archaic = job
    text = _text_of_id(wid)
    if text is None:
        return wid, None
    ch = chunks(tokens(text), size, n, trim)
    return wid, [features(c, archaic) for c in ch] if ch else None


def kjv_text(section: str | None = None) -> str:
    rows = map(json.loads, KJV.read_text().splitlines())
    return "\n".join(r["text"] for r in rows if section is None or r["section"] == section)


def bom_books(masked: bool = True) -> list[tuple[str, str]]:
    """(1830 book, body text) in printed order; King James passages cut out when ``masked``."""
    from kjv_mask.run import artifacts
    from lab.wherefore import EDITION

    spans = {}
    if masked:
        for r in map(json.loads, MASK.read_text().splitlines()):
            spans[r["id"]] = [(s["start"], s["end"]) for s in r["spans"]]
    books: dict[str, list[str]] = {}
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if not r.get("book") or r.get("kind") != "body":
            continue
        text = artifacts(r["text"])[0]
        for a, b in sorted(spans.get(f"bom:{r['seq']}", []), reverse=True):
            text = text[:a] + " . " + text[b:]
        books.setdefault(r["book"], []).append(text)
    return [(b, "\n".join(p)) for b, p in books.items()]


def read_files(spec: str | list[str]) -> str | None:
    parts = []
    for f in [spec] if isinstance(spec, str) else spec:
        try:
            parts.append(Path(f).read_text(errors="replace"))
        except OSError:
            return None  # not attempted
    return "\n".join(parts)


def known_texts(cfg: dict) -> dict[str, str]:
    got = {}
    for name, path in cfg["lab"]["translation"]["known_translations"].items():
        text = kjv_text() if path == str(KJV) else read_files(path)
        if text is not None:
            got[name] = text
    return got


def imitation_texts(cfg: dict) -> dict[str, str]:
    got = {}
    for name, spec in cfg["lab"]["translation"]["imitations"].items():
        text = read_files(spec)
        if text is not None:
            got[name] = text
    return got


def js_texts() -> dict[str, str]:
    from lab import emode

    return emode.js_texts()


# ----------------------------------------------------------------------------- classifier (A)


def _fit(X: np.ndarray, y: np.ndarray, c: float):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    m = make_pipeline(
        StandardScaler(), LogisticRegression(C=c, class_weight="balanced", max_iter=5000)
    )
    return m.fit(X, y)


def equal_error(pos: list[float], neg: list[float]) -> float:
    best = None
    for th in sorted(set(pos) | set(neg)):
        tpr = sum(p >= th for p in pos) / len(pos)
        tnr = sum(q < th for q in neg) / len(neg)
        if best is None or abs(tpr - tnr) < best[0]:
            best = (abs(tpr - tnr), th, tpr, tnr)
    return best[1]


def auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    from sklearn.metrics import roc_auc_score

    return round(float(roc_auc_score([1] * len(pos) + [0] * len(neg), pos + neg)), 4)


def crossval(rows: list[dict], feats: dict[str, list], t: dict) -> dict[str, float]:
    """Out-of-fold book scores (mean chunk probability), whole groups held out together."""
    from sklearn.model_selection import GroupKFold

    books = [r for r in rows if feats.get(r["work_id"])]
    groups = np.array([r["group"] for r in books])
    y_book = np.array([r["label"] for r in books])
    scores = {}
    for tr_i, te_i in GroupKFold(n_splits=t["folds"]).split(books, y_book, groups):
        X = [f for i in tr_i for f in feats[books[i]["work_id"]]]
        y = [books[i]["label"] for i in tr_i for _ in feats[books[i]["work_id"]]]
        m = _fit(np.array(X), np.array(y), t["c"])
        for i in te_i:
            wid = books[i]["work_id"]
            scores[wid] = float(m.predict_proba(np.array(feats[wid]))[:, 1].mean())
    return scores


def score_text(model, text: str, t: dict, archaic: bool) -> dict | None:
    ch = chunks(tokens(text), t["chunk_words"], None, 0.0)
    if not ch:
        return None
    p = model.predict_proba(np.array([features(c, archaic) for c in ch]))[:, 1]
    return {"chunks": len(ch), "mean": round(float(p.mean()), 4), "sd": round(float(p.std()), 4)}


def merged_bom_sections(t: dict) -> list[tuple[str, str]]:
    """1830 books; a book shorter than one chunk is joined to the books after it."""
    secs, name, buf = [], [], []
    for book, text in bom_books(masked=True):
        name.append(book)
        buf.append(text)
        if len(TOKEN.findall(" ".join(buf))) >= t["chunk_words"] * 1.2:
            secs.append((" + ".join(name), "\n".join(buf)))
            name, buf = [], []
    if buf:
        secs.append((" + ".join(name), "\n".join(buf)))
    return secs


def pct(x: float, xs: list[float]) -> float | None:
    return round(sum(v < x for v in xs) / len(xs), 3) if xs else None


def part_a(
    cfg: dict,
    archaic: bool = False,
    workers: int = 8,
    targets: bool = True,
    marc_only: bool = False,
) -> dict:
    t = cfg["lab"]["translation"]
    rows = labelled(cfg, marc_only)
    jobs = [
        (r["work_id"], t["chunk_words"], t["chunks_per_book"], t["trim_share"], archaic)
        for r in rows
    ]
    with ProcessPoolExecutor(workers) as ex:
        feats = dict(ex.map(_book_feats, jobs, chunksize=8))
    unread = [r["work_id"] for r in rows if not feats.get(r["work_id"])]
    rows = [r for r in rows if feats.get(r["work_id"])]
    oof = crossval(rows, feats, t)
    pos = [oof[r["work_id"]] for r in rows if r["label"] == 1]
    neg = [oof[r["work_id"]] for r in rows if r["label"] == 0]
    th = equal_error(pos, neg)
    res = {
        "features": {
            "function_words": len(FUNCTION_WORDS),
            "archaic": archaic,
            "archaic_words": len(ARCHAIC) if archaic else 0,
            "shape": list(SHAPE),
        },
        "books": {
            "translations": len(pos),
            "originals": len(neg),
            "not_attempted": len(unread),
            "translations_marc_041": sum(r["marc_041"] for r in rows if r["label"]),
            "translations_title_only": sum(not r["marc_041"] for r in rows if r["label"]),
        },
        "auc": auc(pos, neg),
        "threshold": round(th, 4),
        "held_out_sensitivity": round(sum(p >= th for p in pos) / len(pos), 3),
        "held_out_specificity": round(sum(q < th for q in neg) / len(neg), 3),
    }
    res["auc_marc_041_only"] = auc(
        [oof[r["work_id"]] for r in rows if r["label"] == 1 and r["marc_041"]], neg
    )
    by_genre = {}
    for g in ("sermon_devotional", "history_chronicle", "fiction_narrative"):
        gp = [oof[r["work_id"]] for r in rows if r["label"] == 1 and r["genre"] == g]
        gn = [oof[r["work_id"]] for r in rows if r["label"] == 0 and r["genre"] == g]
        by_genre[g] = {"translations": len(gp), "originals": len(gn), "auc": auc(gp, gn)}
    res["auc_by_genre"] = by_genre
    langs = Counter(r["lang"] for r in rows if r["label"] == 1)
    res["auc_by_source_language"] = {
        lang or "unknown": {
            "books": k,
            "auc": auc(
                [oof[r["work_id"]] for r in rows if r["label"] == 1 and r["lang"] == lang], neg
            ),
        }
        for lang, k in langs.most_common()
        if k >= t["min_lang_books"]
    }
    res["source_languages"] = {str(k): v for k, v in langs.most_common()}
    model = _fit(
        np.array([f for r in rows for f in feats[r["work_id"]]]),
        np.array([r["label"] for r in rows for _ in feats[r["work_id"]]]),
        t["c"],
    )
    known = {k: score_text(model, v, t, archaic) for k, v in known_texts(cfg).items()}
    known["kjv_old_testament"] = score_text(model, kjv_text("OT"), t, archaic)
    known["kjv_new_testament"] = score_text(model, kjv_text("NT"), t, archaic)
    imit = {k: score_text(model, v, t, archaic) for k, v in imitation_texts(cfg).items()}
    imit = {k: v for k, v in imit.items() if v}
    gate_imit = {k: v for k, v in imit.items() if v["chunks"] >= 2}
    below = [k for k, v in gate_imit.items() if v["mean"] < th]
    need = list(cfg["lab"]["translation"]["known_translations"])
    checks = {
        "auc": {
            "value": res["auc"],
            "bar": t["auc_bar"],
            "passed": res["auc"] is not None and res["auc"] >= t["auc_bar"],
        },
        "known_translations": {
            "passed": all(known.get(k) and known[k]["mean"] >= th for k in need),
            "above_threshold": [k for k in need if known.get(k) and known[k]["mean"] >= th],
        },
        "imitations": {
            "scored": len(gate_imit),
            "below_threshold": len(below),
            "share_below": round(len(below) / max(len(gate_imit), 1), 3),
            "bar": t["imitation_share_below"],
            "passed": bool(gate_imit) and len(below) / len(gate_imit) >= t["imitation_share_below"],
        },
    }
    checks["passed"] = all(v["passed"] for v in checks.values())
    res.update({"known_translations": known, "imitations": imit, "check": checks})
    res["held_out_quantiles"] = {
        "translations": _quant(pos),
        "originals": _quant(neg),
        "imitations": _quant([v["mean"] for v in imit.values()]),
    }
    res["labelled_ids"] = [
        [r["work_id"], r["label"], r["lang"], round(oof[r["work_id"]], 4)] for r in rows
    ]
    if not checks["passed"]:
        res["stopped"] = "the known-answer check missed; the Book of Mormon was not scored for A"
        return res
    if not targets:
        return res
    imv = [v["mean"] for v in imit.values()]

    def place(s: dict | None) -> dict | None:
        if not s:
            return None
        return {
            **s,
            "above_threshold": s["mean"] >= th,
            "pct_translations": pct(s["mean"], pos),
            "pct_originals": pct(s["mean"], neg),
            "pct_imitations": pct(s["mean"], imv),
        }

    whole = "\n".join(x for _, x in bom_books(masked=True))
    res["book_of_mormon"] = {
        "whole": place(score_text(model, whole, t, archaic)),
        "by_section": {
            n: place(score_text(model, x, t, archaic)) for n, x in merged_bom_sections(t)
        },
    }
    w = res["book_of_mormon"]["whole"]
    res["book_of_mormon"]["verdict"] = (
        "reads like a translation"
        if w["mean"] >= th and w["mean"] > max(imv)
        else "reads like the imitations"
        if min(imv) <= w["mean"] <= max(imv)
        else "reads like English originals"
        if w["mean"] < th and w["mean"] < statistics.median(imv)
        else "between: see percentiles"
    )
    res["joseph_smith"] = {
        k: place(score_text(model, v, t, archaic)) for k, v in js_texts().items()
    }
    res["joseph_smith"] = {k: v for k, v in res["joseph_smith"].items() if v}
    return res


def _quant(xs: list[float]) -> dict:
    if not xs:
        return {}
    xs = sorted(xs)
    return {q: round(xs[min(len(xs) - 1, int(len(xs) * q / 100))], 4) for q in (10, 25, 50, 75, 90)}


# ----------------------------------------------------------------------------- Hebraisms (B)

QUANT = frozenset(
    """piece pieces talent talents shekel shekels pound pounds ounce ounces grain grains ton tons
    lump lumps weight value price sum quantity quantities abundance plenty mine mines kind kinds
    sort sorts deal made formed composed built constructed cast full consisting worth age use
    out part much all none some most many instead a an the of in and or one two three ten
    hundred thousand""".split()
)
MATERIAL = r"(?:gold|silver|brass|iron|copper|steel|wood|stone|cedar|bronze|lead|tin|ivory|ebony)"
OF_MATERIAL = re.compile(
    r"\b([a-z]+) of (?:(?:pure|fine|beaten|molten|fine-twined) )?" + MATERIAL + r"\b"
)
COGNATE_PAIRS = (
    ("dream dreamed dreamt dreameth dreamest", "dream dreams"),
    ("vow vowed voweth vowedst", "vow vows"),
    ("sin sinned sinneth", "sin sins"),
    ("fear feared feareth", "fear fears"),
    ("judge judged judgeth judging", "judgment judgments judgement judgements"),
    ("sing sang sung singeth", "song songs"),
    ("work worked wrought worketh", "work works"),
    ("counsel counselled counseled", "counsel counsels"),
    ("mourn mourned mourneth", "mourning"),
    ("lament lamented lamenteth", "lamentation lamentations"),
    ("curse cursed curseth", "curse curses"),
    ("desire desired desireth", "desire desires"),
    ("weep wept weepeth", "weeping"),
    ("build built buildeth", "building buildings"),
    ("live lived liveth", "life"),
    ("die died dieth", "death"),
    ("fight fought fighteth", "fight fights"),
)
MODIFIERS = (
    r"(?:a|an|the|his|her|their|my|our|your|thy|this|that|these|those|great|sore|"
    r"grievous|mighty|strange|evil|good|righteous|wicked|heavy|bitter|terrible|"
    r"exceeding|fearful|holy|new|long|very)"
)
SUBJ = r"(?:i|he|she|it|we|ye|you|they|thou)"
MODAL = r"(?:shall|will|should|would|must|did|do|may|might|can|could|shalt|wilt)"
MANNER = (
    r"(?:joy|gladness|haste|diligence|boldness|patience|fury|speed|earnestness|sincerity|"
    r"sadness|rejoicing|mourning|weeping|zeal|fervency|vigour|vigor|courage|firmness|"
    r"cheerfulness|humility|meekness|thankfulness|reverence|eagerness|violence|wrath|anger)"
)
NOT_ADVERB = frozenset(
    """filled fill fills full fraught replete seized inspired moved endued endowed clothed mingled
    mixed kindled overcome overwhelmed struck smitten swollen burning inflamed burned burnt
    glowing beaming flushed""".split()
)
WITH_NOUN = re.compile(
    r"\b([a-z]+) with (?:(?:great|much|all|exceeding|exceedingly|utmost|"
    r"the|greatest|such) ){0,2}" + MANNER + r"\b"
)
RESUMPTIVE = re.compile(
    r"(?:^|[.;:!?] |\band |\bnow |\bfor )(?:the|this|that|my|his|her|our|"
    r"their|your|thy) [a-z]+ , (?:he|she|it|they) (?![,.;:])"
)
REPEATED_POSS = re.compile(r"\b(my|his|her|our|their|your|thy) ([a-z]+) ,? ?and \1 ([a-z]+)\b")
RULES = (
    "came_to_pass",
    "of_material",
    "cognate_accusative",
    "if_and",
    "compound_preposition",
    "polysyndeton",
    "resumptive_pronoun",
    "repeated_possessive",
    "with_noun_adverb",
    "because_that",
)


def _cognate(gap: int) -> re.Pattern:
    alts = [
        rf"\b(?:{'|'.join(v.split())}) (?:{MODIFIERS} ){{0,{gap}}}(?:{'|'.join(n.split())})\b"
        for v, n in COGNATE_PAIRS
    ]
    return re.compile("|".join(alts))


def count_rules(toks: list[str], b: dict) -> dict[str, int]:
    s = " ".join(toks)
    res = {
        "came_to_pass": len(re.findall(r"\b(?:came|come|cometh|coming) to pass\b", s)),
        "of_material": sum(1 for m in OF_MATERIAL.finditer(s) if m.group(1) not in QUANT),
        "cognate_accusative": len(_cognate(b["cognate_max_gap"]).findall(s)),
        "if_and": len(
            re.findall(
                rf"\bif (?:(?!then\b)[a-z']+ |, ){{1,{b['if_and_max_words']}}}?"
                rf", and {SUBJ} {MODAL}\b",
                s,
            )
        ),
        "compound_preposition": len(
            re.findall(
                r"\bby the hands? of\b|\bby the mouth of\b|"
                r"\bfrom before\b|\bout of the hands? of\b",
                s,
            )
        ),
        "polysyndeton": polysyndeton(toks, b["poly_min_ands"], b["poly_max_gap"]),
        "resumptive_pronoun": len(RESUMPTIVE.findall(s)),
        "repeated_possessive": len(REPEATED_POSS.findall(s)),
        "with_noun_adverb": sum(1 for m in WITH_NOUN.finditer(s) if m.group(1) not in NOT_ADVERB),
        "because_that": len(re.findall(r"\bbecause that\b", s)),
    }
    return res


def polysyndeton(toks: list[str], min_ands: int, max_gap: int) -> int:
    """Runs of at least ``min_ands`` "and" inside one sentence, consecutive ones at most
    ``max_gap`` words apart."""
    runs, n, gap, inrun = 0, 0, 0, False
    for t in toks:
        if t in STOP or t in (";", ":"):
            n, gap, inrun = 0, 0, False
        elif t == "and":
            n = n + 1 if gap <= max_gap or n == 0 else 1
            gap = 0
            if n >= min_ands and not inrun:
                runs, inrun = runs + 1, True
        elif t not in PUNCT:
            gap += 1
            if gap > max_gap:
                n, inrun = 0, False
    return runs


def word_count(toks: list[str]) -> int:
    return sum(1 for t in toks if t not in PUNCT)


def measure_text(text: str, b: dict, max_words: int | None = None) -> dict:
    toks = tokens(text)
    if max_words:
        w = [i for i, t in enumerate(toks) if t not in PUNCT]
        if len(w) > max_words:
            a = w[(len(w) - max_words) // 2]
            toks = toks[a : w[(len(w) - max_words) // 2 + max_words - 1] + 1]
    return {"words": word_count(toks), **count_rules(toks, b)}


def _measure_job(job: tuple[str, dict, int]) -> tuple[str, dict | None]:
    wid, b, mx = job
    text = _text_of_id(wid)
    return wid, (measure_text(text, b, mx) if text else None)


def pooled(ms: list[dict]) -> dict:
    tot = {"words": sum(m["words"] for m in ms), "texts": len(ms)}
    for r in RULES:
        tot[r] = sum(m[r] for m in ms)
    return tot


def rates(m: dict) -> dict:
    w = max(m["words"], 1)
    return {r: round(1e4 * m[r] / w, 3) for r in RULES}


# Planted examples: written for this test (no corpus text). Each positive must add exactly one hit
# of its rule; each near miss must add none.
PLANTED = {
    "came_to_pass": (
        [
            "and it came to pass that the men went up",
            "it shall come to pass in that day",
            "now it came to pass after many days",
        ],
        ["he came to the pass in the hills", "they passed the town and came home"],
    ),
    "of_material": (
        [
            "he made a rod of iron for the gate",
            "they found the plates of brass",
            "she wore a chain of gold",
        ],
        ["he paid a piece of gold", "it was made of iron", "an iron rod lay there"],
    ),
    "cognate_accusative": (
        [
            "he dreamed a dream in the night",
            "they vowed a vow unto the lord",
            "she sang a new song",
            "they judge righteous judgment",
        ],
        ["he dreamed of home", "they sang loudly", "she made a vow"],
    ),
    "if_and": (
        [
            "if ye will not repent of your sins , and ye shall surely perish",
            "if he come to the city , and they will slay him",
        ],
        ["if ye will repent then ye shall live", "if it rain we shall stay at home"],
    ),
    "compound_preposition": (
        [
            "he spake by the hand of moses",
            "they fled from before the enemy",
            "delivered out of the hands of the egyptians",
        ],
        ["he took her hand", "they fled before morning"],
    ),
    "polysyndeton": (
        [
            "and he rose and he went and he took the boy and he came back",
            "and they ate and drank and sang and slept and woke",
        ],
        ["and he rose . and he went . and he came", "bread and wine and oil"],
    ),
    "resumptive_pronoun": (
        ["and the king , he went out to battle", "now my father , he was a man"],
        ["said the king , he would go", "the king went out , and he fought"],
    ),
    "repeated_possessive": (
        ["he took his sons and his daughters", "with my house and my land"],
        ["his sons and daughters came", "my house and your land"],
    ),
    "with_noun_adverb": (
        [
            "they went with great haste",
            "he spake with boldness to them",
            "she wrote with much diligence",
        ],
        ["they were filled with joy", "he went in haste"],
    ),
    "because_that": (
        ["because that they had sinned", "and because that he was wise"],
        ["because they had sinned", "that because of this"],
    ),
}


def plant_check(host: str, b: dict, seed: int) -> dict:
    """Insert each rule's written examples at sentence breaks in ``host``; the count must rise
    by exactly the positives and not at all for the near misses."""
    base = count_rules(tokens(host), b)
    toks = tokens(host)
    breaks = [i + 1 for i, t in enumerate(toks) if t == "."]
    rng = random.Random(seed)
    res = {}
    for rule, (pos, neg) in PLANTED.items():
        ok = True
        for group, want in ((pos, len(pos)), (neg, 0)):
            t2 = list(toks)
            for ex in sorted(group, reverse=True):
                at = rng.choice(breaks)
                t2[at:at] = tokens(ex) + ["."]
            got = count_rules(t2, b)[rule] - base[rule]
            ok = ok and got == want
        res[rule] = ok
    return res


def prose_rows(cfg: dict) -> list[str]:
    t = cfg["lab"]["translation"]
    trx = re.compile(t["translation_title"], re.I)
    tab = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(tab["kind"], "work"), pc.equal(tab["has_text"], True)),
        pc.equal(tab["dup_keeper"], True),
    )
    rows = [
        r
        for r in tab.filter(keep)
        .select(["work_id", "year", "words", "genre", "sealed", "ocr_excluded"])
        .to_pylist()
        if not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and t["prose_year_min"] <= r["year"] <= t["prose_year_max"]
        and (r["words"] or 0) >= t["prose_min_words"]
        and t["exclude_genre"] not in (r["genre"] or "")
        and not (r["genre"] or "").startswith("newspaper")
    ]
    from lab import emode

    marked = emode.translations()
    rows = [r for r in rows if r["work_id"] not in marked]
    random.Random(t["seed"]).shuffle(rows)
    cat = door.catalog({r["work_id"] for r in rows[: t["prose_sample"] * 3]})
    got = []
    for r in rows[: t["prose_sample"] * 3]:
        c = cat.get(r["work_id"])
        if c and c["text_path"] and not trx.search((c["title"] or "") + " " + (c["author"] or "")):
            got.append(r["work_id"])
        if len(got) == t["prose_sample"]:
            break
    return got


def non_semitic(cfg: dict) -> list[str]:
    t = cfg["lab"]["translation"]
    rows = [
        r
        for r in labelled(cfg)
        if r["label"] == 1 and r["lang"] in ("fre", "ger", "lat", "grc", "ita", "spa")
    ]
    rows.sort(key=lambda r: r["work_id"])
    return [
        r["work_id"]
        for r in random.Random(t["seed"]).sample(rows, min(len(rows), t["non_semitic_sample"]))
    ]


def part_b(cfg: dict, workers: int = 8) -> dict:
    t = cfg["lab"]["translation"]
    b = t
    mx = t["max_words"]
    prose_ids = prose_rows(cfg)
    ns_ids = non_semitic(cfg)
    heb = t["hebrew_translations"]
    jobs = [(w, b, mx) for w in prose_ids + ns_ids] + [(w, b, None) for w in heb.values()]
    with ProcessPoolExecutor(workers) as ex:
        got = dict(ex.map(_measure_job, jobs, chunksize=4))
    prose = [got[w] for w in prose_ids if got.get(w)]
    groups: dict[str, dict] = {}
    groups["kjv_old_testament"] = measure_text(kjv_text("OT"), b)
    groups["kjv_new_testament"] = measure_text(kjv_text("NT"), b)
    groups["period_prose"] = pooled(prose)
    # Known answers first: the Old Testament against period prose, and planted examples.
    host = _text_of_id(prose_ids[0]) or ""
    plants = plant_check(" ".join(host.split()[:20000]), b, t["seed"])
    ot, pr = rates(groups["kjv_old_testament"]), rates(groups["period_prose"])
    check = {}
    for r in RULES:
        ratio = (ot[r] / pr[r]) if pr[r] else (float("inf") if ot[r] else 0.0)
        check[r] = {
            "ot_rate": ot[r],
            "prose_rate": pr[r],
            "ratio": round(ratio, 2) if ratio != float("inf") else "inf",
            "planted": plants[r],
            "kept": ratio >= t["ot_ratio_bar"] and plants[r],
        }
    kept = [r for r in RULES if check[r]["kept"]]
    res = {
        "check": check,
        "kept": kept,
        "dropped": [r for r in RULES if r not in kept],
        "prose_unreadable": len(prose_ids) - len(prose),
    }
    groups["book_of_mormon_masked"] = measure_text("\n".join(x for _, x in bom_books(True)), b)
    groups["book_of_mormon_unmasked"] = measure_text("\n".join(x for _, x in bom_books(False)), b)
    hebm = {k: got[w] for k, w in heb.items() if got.get(w)}
    groups["hebrew_translations_pooled"] = pooled(list(hebm.values()))
    kn = known_texts(cfg)
    groups["koran_sale_arabic"] = measure_text(kn["koran_sale"], b) if "koran_sale" in kn else None
    jos = [measure_text(kn[k], b) for k in kn if k.startswith("josephus")]
    nsm = [got[w] for w in ns_ids if got.get(w)]
    groups["non_semitic_translations_pooled"] = pooled(nsm + jos)
    imit = {k: measure_text(v, b) for k, v in imitation_texts(cfg).items()}
    groups["imitations_pooled"] = pooled(list(imit.values()))
    js = {k: measure_text(v, b) for k, v in js_texts().items()}
    js = {k: v for k, v in js.items() if v["words"] >= t["chunk_words"]}
    groups["joseph_smith_pooled"] = pooled(list(js.values()))
    groups = {k: v for k, v in groups.items() if v}
    res["groups"] = {
        k: {
            "words": v["words"],
            "texts": v.get("texts", 1),
            "counts": {r: v[r] for r in RULES},
            "per10k": rates(v),
        }
        for k, v in groups.items()
    }
    res["hebrew_translations"] = {
        k: {"words": v["words"], "per10k": rates(v)} for k, v in hebm.items()
    }
    res["imitations"] = {k: {"words": v["words"], "per10k": rates(v)} for k, v in imit.items()}
    res["joseph_smith"] = {k: {"words": v["words"], "per10k": rates(v)} for k, v in js.items()}
    res["prose_per_work_median"] = {
        r: round(statistics.median(rates(m)[r] for m in prose), 3) for r in RULES
    }
    bom = rates(groups["book_of_mormon_masked"])
    big = {k: v for k, v in imit.items() if v["words"] >= t["imitation_min_words"]}
    verdict = {}
    for r in RULES:
        at = sorted(k for k, v in big.items() if rates(v)[r] >= bom[r])
        pool_r = rates(groups["imitations_pooled"])[r]
        hb = rates(groups["hebrew_translations_pooled"])[r]
        verdict[r] = {
            "kept": r in kept,
            "bom": bom[r],
            "imitations_pooled": pool_r,
            "imitations_max": max((rates(v)[r] for v in big.values()), default=None),
            "imitations_at_or_above_bom": at,
            "imitations_counted": len(big),
            "imitations_reach_bom": bool(at) or pool_r >= bom[r],
            "hebrew_translations": hb,
            "non_semitic": rates(groups["non_semitic_translations_pooled"])[r],
            "hebrew_above_prose_and_non_semitic": hb > pr[r]
            and hb > rates(groups["non_semitic_translations_pooled"])[r],
        }
    res["verdict"] = verdict
    res["ids"] = {"period_prose": prose_ids, "non_semitic": ns_ids}
    return res


# ----------------------------------------------------------------------------- commands


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["labels", "run"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument(
        "--marc-only", action="store_true", help="post hoc: 041-marked translations only"
    )
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "labels":
        rows = labelled(cfg)
        cat = door.catalog({r["work_id"] for r in rows})
        sample = hand_sample(cfg, rows)
        with out(CARD / "hand_check_sample.jsonl").open("w") as fh:
            for r in sample:
                c = cat.get(r["work_id"], {})
                fh.write(
                    json.dumps({**r, "title": c.get("title"), "author": c.get("author")}) + "\n"
                )
        out(OUT / "labels.json").write_text(
            json.dumps(
                {
                    "config_sha256": config.sha256_of_config(),
                    "rows": [
                        [
                            r["work_id"],
                            r["label"],
                            r["lang"],
                            r["year"],
                            r["genre"],
                            r["marc_041"],
                            r["title_phrase"],
                        ]
                        for r in rows
                    ],
                }
            )
            + "\n"
        )
        print(Counter((r["label"], r["lang"]) for r in rows).most_common(12))
        print(
            "translations",
            sum(r["label"] for r in rows),
            "originals",
            sum(1 - r["label"] for r in rows),
        )
        return 0
    if a.marc_only:  # post hoc revision (see the card): part A only, 041-marked translations
        res = {
            "config_sha256": config.sha256_of_config(),
            "post_hoc": True,
            "revision": "translations limited to MARC 041 ind1 1; title-phrase-only books out",
            "A": part_a(cfg, workers=a.workers, marc_only=True),
        }
        out(OUT / "result_marc_only.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res["A"]["check"], indent=1))
        return 0
    rows = labelled(cfg)
    res = {
        "config_sha256": config.sha256_of_config(),
        "commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "settings": cfg["lab"]["translation"],
    }
    hand = hand_accuracy(rows)
    res["hand_check"] = hand
    bar = cfg["lab"]["translation"]["hand_check_bar"]
    if hand is None or any(v["accuracy"] < bar for v in hand.values()):
        res["A"] = {"stopped": "hand check of labels missing or below its bar"}
    else:
        res["A"] = part_a(cfg, workers=a.workers)
        res["A_sensitivity_with_archaic_forms"] = {
            k: v
            for k, v in part_a(
                cfg, archaic=True, workers=a.workers, targets=res["A"]["check"]["passed"]
            ).items()
            if k not in ("labelled_ids",)
        }
    res["B"] = part_b(cfg, workers=a.workers)
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({"A_check": res["A"].get("check"), "B_kept": res["B"]["kept"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
