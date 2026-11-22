"""BOM-106: spoken or written? Marks of language composed aloud, counted by rule.

The historical accounts say the Book of Mormon was dictated aloud. Speech taken down as spoken
differs measurably from prose composed on paper. This counts a fixed list of 25 marks (chaining
with "and", subordinators, relatives, nominal style, pronouns of involvement, restarts and
repairs, repetition of recent phrasing, formula density, the rate of new words, laying down
heads) on windows of exactly ``window_words`` words, with all punctuation removed first (the
original manuscript has none and editors punctuated everything else). A standardised logistic
regression on the marks is fitted to separate speech taken down verbatim (Old Bailey testimony
1780-1830 from the Old Bailey Corpus 2.0; sermons, trials and debates "taken in short-hand" from
the library) from composed prose (printed sermons, half hand-keyed and half scanned; other
composed prose of 1780-1830), held out by speaker or author. The known-answer check (all spoken
against all written, and short-hand sermons against printed sermons) comes first; the book is
scored only if it passes. Then dictated compositions (the ``received`` set of ``lab.dictated``),
the Book of Mormon by narrator, book, narration and direct speech, the original and printer's
manuscripts, Joseph Smith's other dictations and his own hand, the King James Bible by part, the
Bible-style imitations and genuine translations, and a variant without the "and" marks. The test
card, written first, is ``data/private/lab/owner/2026-11-21-spoken-or-written/card.md``; settings
are ``lab.spoken`` in the config. The result holds names, ids and numbers, no text.

Usage::

    python -m lab.spoken parse    # Old Bailey Corpus 2.0, every session -> data/corpus/lab/spoken/
    python -m lab.spoken check    # known-answer check only -> data/lab/spoken/check.json
    python -m lab.spoken run      # -> data/lab/spoken/result.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from lab import dictated, door, registry, twovoices
from lab.paths import FAST, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "spoken"
PRIVATE = NOTES / "owner" / "2026-11-21-spoken-or-written"
OB_ZIP = FAST / "sources" / "speech" / "oldbailey_corpus_2" / "OldBaileyCorpus2.zip"
OB_TABLE = FAST / "spoken" / "oldbailey_utterances.parquet"
EDITION = Path("data/bom/1830/edition_1830.jsonl")
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
KJV = Path("data/kjv/kjv.jsonl")
ORIGINAL = Path("data/private/bom/jsp_original.jsonl")
PRINTERS = Path("data/private/bom/jsp_printers.jsonl")
ALIGN_OM = Path("data/bom/align_original.jsonl")
CANDIDATES = Path("data/private/candidates")
OT1 = Path("data/private/lab/sources/dictated/ot_revision_1/pages.jsonl")
LETTERS = re.compile(r"[a-z]+")
APOS = re.compile(r"(?<=[a-z])['’](?=[a-z])")
AMP_C = re.compile(r"&\s?c\b\.?")

FEATURES = [
    "and_rate", "and_clause", "and_then", "then_so", "but", "subord", "rel_wh", "that",
    "nominal", "word_len", "prep", "passive", "first_sg", "second", "private_v", "it_rate",
    "do_rate", "repeat_word", "repair", "i_say", "recent_3gram", "formula_4gram", "mattr",
    "interj", "heads",
]  # fmt: skip
AFTER_AND = set("i he she it we they ye you thou the there then so when thus".split())
SUBORD = set(
    "because although though whereas unless whilst while whether since lest till until if when "
    "whenever where wherever".split()
)
REL_WH = set("which whom whose wherein whereby whereof whereupon".split())
NOMINAL = ("tion", "sion", "ment", "ness", "ity", "ance", "ence")
PREP = set(
    "against amid amidst among amongst at by during for from in into of off on onto over "
    "through throughout toward towards under upon with within without".split()
)
BE = set("am is are was were be been being".split())
NOT_PARTICIPLE = set(
    "then when even often children women heaven heavens eden garden ten seven eleven golden "
    "hidden linen chicken kitchen".split()
)
FIRST_SG = set("i me my mine myself".split())
SECOND = set("you your yours yourself yourselves ye thou thee thy thine".split())
PRIVATE_V = set("think thought believe believed suppose supposed know knew guess reckon mean meant"
                .split())  # fmt: skip
DO = set("do did does dont didnt".split())
INTERJ = set("well oh aye ay yes".split())
HEADS = set("firstly secondly thirdly fourthly fifthly lastly".split())
REPAIRS = [
    ("or", "rather"),
    ("i", "mean"),
    ("that", "is", "to", "say"),
    ("in", "other", "words"),
    ("i", "should", "say"),
    ("as", "i", "said"),
    ("as", "i", "was", "saying"),
]
HEAD_PHRASES = [("in", "the", "first", "place"), ("in", "the", "next", "place"),
                ("in", "the", "second", "place"), ("in", "the", "third", "place")]  # fmt: skip


# ------------------------------------------------------------------------------ words, marks


def words(text: str, vocab: set[str]) -> list[str]:
    """Lower-case letter words, punctuation gone, apostrophes inside a word joined ("dont"),
    "&" read as "and" ("&c" as "etc"), long-s OCR repaired against the King James vocabulary
    (``twovoices.tokens``)."""
    text = AMP_C.sub(" etc ", text).replace("&", " and ")  # scribes' "&" is the word "and"
    return twovoices.tokens(APOS.sub("", text.lower()), vocab)[0]


def _phrases(w: list[str], phrases: list[tuple[str, ...]]) -> int:
    n = 0
    for p in phrases:
        k = len(p)
        n += sum(1 for i in range(len(w) - k + 1) if tuple(w[i : i + k]) == p)
    return n


def marks(w: list[str], t: dict) -> dict[str, float]:
    """The 25 marks of the card for one window of words."""
    n = len(w)
    per = 1000.0 / n
    c = Counter(w)
    pairs = list(zip(w, w[1:], strict=False))
    and_clause = sum(1 for a, b in pairs if a == "and" and b in AFTER_AND)
    and_then = sum(1 for a, b in pairs if a == "and" and b in ("then", "so"))
    passive = sum(
        1
        for a, b in pairs
        if a in BE and len(b) > 3 and b.endswith(("ed", "en")) and b not in NOT_PARTICIPLE
    )
    repeat = sum(1 for a, b in pairs if a == b)
    i_say = sum(1 for a, b in pairs if a == "i" and b == "say")
    # repetition of recent phrasing: a 3-word string already seen, not overlapping, within window
    last: dict[tuple, int] = {}
    recent = 0
    for i in range(n - 2):
        g = (w[i], w[i + 1], w[i + 2])
        j = last.get(g)
        if j is not None and 3 <= i - j <= t["recent_window"]:
            recent += 1
        last[g] = i
    grams = Counter(tuple(w[i : i + 4]) for i in range(n - 3))
    cover = bytearray(n)
    for i in range(n - 3):
        if grams[tuple(w[i : i + 4])] >= t["formula_min"]:
            cover[i : i + 4] = b"\x01\x01\x01\x01"
    return {
        "and_rate": c["and"] * per,
        "and_clause": and_clause * per,
        "and_then": and_then * per,
        "then_so": (c["then"] + c["so"]) * per,
        "but": c["but"] * per,
        "subord": sum(c[x] for x in SUBORD) * per,
        "rel_wh": sum(c[x] for x in REL_WH) * per,
        "that": c["that"] * per,
        "nominal": sum(v for k, v in c.items() if len(k) >= 7 and k.endswith(NOMINAL)) * per,
        "word_len": sum(len(x) for x in w) / n,
        "prep": sum(c[x] for x in PREP) * per,
        "passive": passive * per,
        "first_sg": sum(c[x] for x in FIRST_SG) * per,
        "second": sum(c[x] for x in SECOND) * per,
        "private_v": sum(c[x] for x in PRIVATE_V) * per,
        "it_rate": c["it"] * per,
        "do_rate": sum(c[x] for x in DO) * per,
        "repeat_word": repeat * per,
        "repair": _phrases(w, REPAIRS) * per,
        "i_say": i_say * per,
        "recent_3gram": recent / max(n - 2, 1),
        "formula_4gram": sum(cover) / n,
        "mattr": dictated.mattr_value(w, t["mattr_window"]),
        "interj": sum(c[x] for x in INTERJ) * per,
        "heads": (sum(c[x] for x in HEADS) + _phrases(w, HEAD_PHRASES)) * per,
    }


def windows(w: list[str], t: dict, cap: int, trim: bool) -> list[list[str]]:
    """Evenly spaced, non-overlapping windows of exactly ``window_words`` words."""
    size = t["window_words"]
    head, tail = (t["trim_head"], t["trim_tail"]) if trim else (0.0, 0.0)
    return [w[a : a + size] for a in dictated.starts(len(w), size, head, tail, cap)]


def contiguous(w: list[str], size: int) -> list[tuple[int, list[str]]]:
    """(start, window) for consecutive windows from the start (dictation-order measure)."""
    return [(i, w[i : i + size]) for i in range(0, len(w) - size + 1, size)]


# ------------------------------------------------------------------------------ Old Bailey


def _utter_text(u: ET.Element) -> str:
    """An utterance's words without the reporter's bracketed actions (``<activity>``)."""
    parts = [u.text or ""]
    for ch in u:
        if ch.tag != "activity":
            parts.append("".join(ch.itertext()))
        parts.append(ch.tail or "")
    return " ".join("".join(parts).replace("\\", "").split())


def parse_oldbailey() -> dict:
    """Every utterance of every session of the Old Bailey Corpus 2.0, read inside the archive
    (nothing extracted, nothing deleted) -> ``OB_TABLE``."""
    cols: dict[str, list] = defaultdict(list)
    failed: dict[str, str] = {}
    with zipfile.ZipFile(OB_ZIP) as z:
        names = sorted(n for n in z.namelist() if n.endswith(".xml"))
        for name in names:
            try:
                root = ET.fromstring(z.read(name))
            except ET.ParseError as e:
                failed[name] = str(e)  # not attempted, never a zero
                continue
            session = Path(name).stem.replace("OBC2-", "")
            for k, u in enumerate(root.iter("u")):
                a = u.attrib
                cols["session"].append(session)
                cols["n"].append(k)
                cols["year"].append(int(a.get("year") or session[:4]))
                cols["trial"].append(a.get("trial", ""))
                cols["speaker"].append(a.get("speaker", ""))
                cols["role"].append(a.get("role", ""))
                cols["sex"].append(a.get("sex", ""))
                cols["text"].append(_utter_text(u))
    out(OB_TABLE)
    pq.write_table(pa.table(dict(cols)), OB_TABLE)
    roles = Counter(cols["role"])
    return {
        "sessions": len(names) - len(failed),
        "utterances": len(cols["text"]),
        "not_attempted": failed,
        "roles": dict(roles),
        "table": str(OB_TABLE),
    }


def oldbailey_sessions(t: dict) -> dict[str, str] | None:
    """{session: testimony text in order} for the card's years and roles; None if unparsed."""
    if not OB_TABLE.exists():
        return None
    tab = pq.read_table(OB_TABLE).to_pylist()
    lo, hi = t["oldbailey_years"]
    roles = set(t["oldbailey_roles"])
    by: dict[str, list[str]] = defaultdict(list)
    for r in sorted(tab, key=lambda r: (r["session"], r["n"])):
        if lo <= r["year"] <= hi and r["role"] in roles:
            by[r["session"]].append(r["text"])
    return {s: " ".join(v) for s, v in by.items()}


# ------------------------------------------------------------------------------ labelled sets


def _eligible(lo: int, hi: int) -> list[dict]:
    tab = registry.load().to_pylist()
    return [
        r
        for r in tab
        if r["kind"] == "work"
        and r["has_text"]
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and lo <= r["year"] <= hi
    ]


def group_key(row: dict) -> str:
    """Held-out group: the author; with no author, the title's first six words (volumes and
    editions of one trial stay together)."""
    a = (row.get("author_norm") or "").strip()
    if a:
        m = re.match(r"[^,]+, \S+", a)  # "savery, william dillwyn george" -> "savery, william"
        return "author:" + (m.group(0) if m else a)
    title = " ".join(LETTERS.findall((row.get("title") or "").lower())[:6])
    return "title:" + (title or row["work_id"])


def library_sets(t: dict) -> tuple[dict[str, list[dict]], dict]:
    """{set name: catalog rows} for the spoken library sets (S2, S3) and the written ones (W1,
    W2), all by the card's title rules, drawn by seed."""
    import random

    lo = min(t["shorthand_years"][0], t["written_sermon_years"][0], t["written_prose_years"][0])
    hi = max(t["shorthand_years"][1], t["written_sermon_years"][1], t["written_prose_years"][1])
    rows = _eligible(lo, hi)
    cat = door.catalog({r["work_id"] for r in rows})
    rows = [{**cat[r["work_id"]], **r} for r in rows if r["work_id"] in cat]
    rows.sort(key=lambda r: r["work_id"])
    sh, shx = re.compile(t["shorthand_title"], re.I), re.compile(t["shorthand_exclude"], re.I)
    reply = re.compile(t["shorthand_not_speech"], re.I)
    serm, trial = re.compile(t["sermon_title"], re.I), re.compile(t["trial_title"], re.I)
    s_lo, s_hi = t["shorthand_years"]
    sets: dict[str, list[dict]] = {"S2_shorthand_sermons": [], "S3_shorthand_trials": []}
    other_shorthand = []
    spoken_ids = set()
    for r in rows:
        title = " ".join((r["title"] or "").split())
        if not (s_lo <= r["year"] <= s_hi) or not sh.search(title) or shx.search(title):
            continue
        spoken_ids.add(r["work_id"])
        if reply.search(title):
            other_shorthand.append(r)
        elif serm.search(title) and not trial.search(title):
            sets["S2_shorthand_sermons"].append(r)
        elif trial.search(title):
            sets["S3_shorthand_trials"].append(r)
        else:
            other_shorthand.append(r)
    rng = random.Random(t["seed"])
    ws_lo, ws_hi = t["written_sermon_years"]
    sx = re.compile(t["written_sermon_exclude"], re.I)
    pool_tcp, pool_scan = [], []
    for r in rows:
        title = " ".join((r["title"] or "").split())
        if (
            r["work_id"] not in spoken_ids
            and ws_lo <= r["year"] <= ws_hi
            and (r["genre"] or "").split(",")[0] == "sermon_devotional"
            and re.search(r"\bsermons?\b", title, re.I)
            and not sx.search(title)
            and r["author_kind"] == "person"
            and (r["words"] or 0) >= t["written_sermon_min_words"]
        ):
            (pool_tcp if r["source"] == "tcp" else pool_scan).append(r)
    taken: set[str] = {group_key(r) for r in sets["S2_shorthand_sermons"]}

    def draw(pool: list[dict], n: int) -> list[dict]:
        pool = list(pool)
        rng.shuffle(pool)
        got = []
        for r in pool:
            g = group_key(r)
            if g in taken:
                continue  # one work per author, and never a short-hand preacher's own
            taken.add(g)
            got.append(r)
            if len(got) == n:
                break
        return got

    sets["W1_printed_sermons"] = draw(pool_tcp, t["written_sermons_tcp"]) + draw(
        pool_scan, t["written_sermons_scanned"]
    )
    wp_lo, wp_hi = t["written_prose_years"]
    mark = re.compile(t["speech_marker_title"], re.I)
    genres = set(t["written_prose_genres"])
    pool = [
        r
        for r in rows
        if r["work_id"] not in spoken_ids
        and wp_lo <= r["year"] <= wp_hi
        and (r["genre"] or "").split(",")[0] in genres
        and r["author_kind"] == "person"
        and (r["words"] or 0) >= t["written_prose_min_words"]
        and not mark.search(" ".join((r["title"] or "").split()))
    ]
    sets["W2_written_prose"] = draw(pool, t["written_prose"])
    info = {"shorthand_matched_neither": [r["work_id"] for r in other_shorthand]}
    return sets, info


def _lib_windows(args: tuple) -> tuple[str, list[dict] | str]:
    row, t, cfg = args
    try:
        text = door.text_of(row)
    except OSError as e:
        return row["work_id"], f"unreadable: {e}"  # not attempted
    w = words(dictated.clean(text, cfg), _VOCAB)
    ws = windows(w, t, t["max_windows_group"], True)
    if not ws:
        return row["work_id"], f"too short ({len(w)} words)"
    return row["work_id"], [{"words_total": len(w), **marks(x, t)} for x in ws]


_VOCAB: set[str] = set()


def _init(vocab: set[str]) -> None:
    global _VOCAB
    _VOCAB = vocab


def labelled_windows(cfg: dict, vocab: set[str], workers: int) -> tuple[list[dict], dict]:
    """Every labelled window as {set, label, group, unit, marks...}; plus a record of the sets."""
    t = cfg["lab"]["spoken"]
    rows: list[dict] = []
    rec: dict = {"sets": {}, "not_attempted": {}}
    ob = oldbailey_sessions(t)
    if ob is None:
        rec["not_attempted"]["S1_oldbailey"] = "Old Bailey table missing: run `parse` first"
    else:
        n_s = 0
        for s, text in sorted(ob.items()):
            w = words(text, vocab)
            if len(w) < t["oldbailey_min_session_words"]:
                continue
            ws = windows(w, t, t["max_windows_group"], False)
            for x in ws:
                rows.append({"set": "S1_oldbailey", "label": 1, "group": "ob:" + s, "unit": s,
                             **marks(x, t)})  # fmt: skip
            n_s += bool(ws)
        rec["sets"]["S1_oldbailey"] = {"sessions": n_s}
    sets, info = library_sets(t)
    rec["shorthand_matched_neither"] = info["shorthand_matched_neither"]
    jobs = [(r, t, cfg) for v in sets.values() for r in v]
    by_id = {r["work_id"]: r for v in sets.values() for r in v}
    set_of = {r["work_id"]: k for k, v in sets.items() for r in v}
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(vocab,)) as ex:
        results = list(ex.map(_lib_windows, jobs, chunksize=4))
    used: dict[str, list[str]] = defaultdict(list)
    for wid, res in results:
        if isinstance(res, str):
            rec["not_attempted"][wid] = res
            continue
        s = set_of[wid]
        used[s].append(wid)
        for m in res:
            m.pop("words_total")
            rows.append({"set": s, "label": int(s.startswith("S")), "unit": wid,
                         "group": group_key(by_id[wid]), **m})  # fmt: skip
    for s, v in sets.items():
        rec["sets"][s] = {
            "drawn": len(v),
            "scored": len(used[s]),
            "groups": len({group_key(by_id[w]) for w in used[s]}),
            "work_ids": sorted(used[s]),
            "sources": dict(Counter(by_id[w]["source"] for w in used[s])),
        }
    rows = cap_groups(rows, t["max_windows_group"])
    for s in rec["sets"]:
        sub = [r for r in rows if r["set"] == s]
        rec["sets"][s]["windows"] = len(sub)
        rec["sets"][s]["groups_with_windows"] = len({r["group"] for r in sub})
    write_labels(sets, info, by_id)
    return rows, rec


def cap_groups(rows: list[dict], cap: int) -> list[dict]:
    """At most ``cap`` windows per held-out group, evenly spaced over the group's windows in
    reading order (volumes of one trial, works of one author)."""
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["group"]].append(r)
    keep = []
    for g in sorted(by):
        v = by[g]
        if len(v) <= cap:
            keep += v
        else:
            keep += [v[round(i * (len(v) - 1) / (cap - 1))] for i in range(cap)]
    return keep


def write_labels(sets: dict, info: dict, by_id: dict) -> None:
    """The title rules' matches, for a person to check (titles only, private folder)."""
    head = "Titles only, for a person to check the rule. Written by `python -m lab.spoken`."
    lines = ["# Labelled sets by title rule (BOM-106)", "", head, ""]
    cat = door.catalog(set(info["shorthand_matched_neither"]))
    for s, v in sets.items():
        lines += [f"## {s} ({len(v)})", ""]
        for r in v:
            title = " ".join((r["title"] or "").split())[:160]
            lines.append(f"- {r['work_id']} {r['year']} {title}")
        lines.append("")
    lines += ["## short-hand titles matching neither the sermon nor the trial rule (left out)", ""]
    for w in info["shorthand_matched_neither"]:
        c = cat.get(w, {})
        lines.append(f"- {w} {' '.join((c.get('title') or '').split())[:160]}")
    out(PRIVATE / "labels.md").write_text("\n".join(lines) + "\n")


# ------------------------------------------------------------------------------ the score


def matrix(rows: list[dict], feats: list[str]) -> np.ndarray:
    return np.array([[r[f] for f in feats] for r in rows], dtype=float)


def _model(c: float):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(
        StandardScaler(), LogisticRegression(C=c, class_weight="balanced", max_iter=5000)
    )


def auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    from sklearn.metrics import roc_auc_score

    return float(roc_auc_score([1] * len(pos) + [0] * len(neg), list(pos) + list(neg)))


def cross_validate(rows: list[dict], feats: list[str], t: dict) -> tuple[np.ndarray, list]:
    """Held-out log-odds for every labelled window (grouped folds) and the fold models."""
    from sklearn.model_selection import StratifiedGroupKFold

    X, y = matrix(rows, feats), np.array([r["label"] for r in rows])
    g = np.array([r["group"] for r in rows])
    held = np.zeros(len(rows))
    models = []
    cv = StratifiedGroupKFold(n_splits=t["folds"], shuffle=True, random_state=t["seed"] % 2**31)
    for tr, te in cv.split(X, y, g):
        m = _model(t["c"]).fit(X[tr], y[tr])
        held[te] = m.decision_function(X[te])
        models.append(m)
    return held, models


def check(rows: list[dict], feats: list[str], t: dict) -> dict:
    held, models = cross_validate(rows, feats, t)
    for r, s in zip(rows, held, strict=True):
        r["_held"] = float(s)
    sp = [s for r, s in zip(rows, held, strict=True) if r["label"] == 1]
    wr = [s for r, s in zip(rows, held, strict=True) if r["label"] == 0]
    s2 = [r for r in rows if r["set"] == "S2_shorthand_sermons"]
    w1 = [r for r in rows if r["set"] == "W1_printed_sermons"]
    a_all = auc(sp, wr)
    a_ser = auc([r["_held"] for r in s2], [r["_held"] for r in w1])
    g2, g1 = len({r["group"] for r in s2}), len({r["group"] for r in w1})
    res = {
        "features": feats,
        "windows": {"spoken": len(sp), "written": len(wr)},
        "auc_all": _r(a_all),
        "auc_sermons": _r(a_ser),
        "sermon_groups": {"shorthand": g2, "printed": g1},
        "auc_by_pair": {},
        "set_medians_logodds": {},
    }
    sets = sorted({r["set"] for r in rows})
    for a in [s for s in sets if s.startswith("S")]:
        for b in [s for s in sets if s.startswith("W")]:
            res["auc_by_pair"][f"{a}~{b}"] = _r(
                auc(
                    [r["_held"] for r in rows if r["set"] == a],
                    [r["_held"] for r in rows if r["set"] == b],
                )  # fmt: skip
            )
    for s in sets:
        res["set_medians_logodds"][s] = summary([r["_held"] for r in rows if r["set"] == s])
    # TCP-only sermon pair: both sides hand-keyed (an OCR-matched view; reported, not a bar)
    tcp = [r for r in w1 if r["unit"].startswith("tcp:")]
    s2t = [r for r in s2 if r["unit"].startswith("tcp:")]
    res["auc_sermons_tcp_only"] = _r(auc([r["_held"] for r in s2t], [r["_held"] for r in tcp]))
    res["passes"] = {
        "A_all": a_all is not None and a_all >= t["bar_auc_all"],
        "B_sermons": a_ser is not None and a_ser >= t["bar_auc_sermons"],
        "C_groups": min(g2, g1) >= t["min_spoken_groups"],
    }
    res["passed"] = all(res["passes"].values())
    # threshold balancing the two error rates on held-out scores (for false-positive rates)
    from sklearn.metrics import roc_curve

    fpr, tpr, thr = roc_curve([1] * len(sp) + [0] * len(wr), sp + wr)
    k = int(np.argmin(np.abs(fpr - (1 - tpr))))
    res["balanced_threshold"] = _r(float(thr[k]))
    res["balanced_error"] = _r(float(fpr[k]))
    res["centres"] = {"spoken_median": _r(float(np.median(sp))),
                      "written_median": _r(float(np.median(wr)))}  # fmt: skip
    if s2 and w1:
        res["centres"]["sermons_shorthand_median"] = _r(float(np.median([r["_held"] for r in s2])))
        res["centres"]["sermons_printed_median"] = _r(float(np.median([r["_held"] for r in w1])))
    full = _model(t["c"]).fit(matrix(rows, feats), np.array([r["label"] for r in rows]))
    coef = full[-1].coef_[0]
    res["standardised_coefficients"] = {f: _r(float(v)) for f, v in zip(feats, coef, strict=True)}
    return {"result": res, "models": models, "rows": rows, "full": full}


def contributions(full, feats: list[str], ms: list[dict], written: list[dict]) -> dict:
    """Each mark's share of a target's mean log-odds above the written windows' mean, in the
    model fitted on all labelled windows: coefficient x (target mean - written mean) / scale.
    A reading aid added after the first run (post hoc); it changes no number above it."""
    if not ms:
        return {}
    sc, lr = full[0], full[-1]
    a, b = matrix(ms, feats).mean(axis=0), matrix(written, feats).mean(axis=0)
    c = lr.coef_[0] * (a - b) / sc.scale_
    order = np.argsort(-np.abs(c))
    return {"total": _r(float(c.sum())),
            "by_mark": {feats[i]: _r(float(c[i]), 3) for i in order}}  # fmt: skip


def summary(xs: list[float]) -> dict:
    if not xs:
        return {"n": 0}
    a = np.array(xs)
    return {
        "n": len(xs),
        "median": _r(float(np.median(a))),
        "p10": _r(float(np.percentile(a, 10))),
        "p90": _r(float(np.percentile(a, 90))),
        "min": _r(float(a.min())),
        "max": _r(float(a.max())),
    }


def _r(x: float | None, k: int = 4) -> float | None:
    return None if x is None else round(x, k)


def score(models: list, feats: list[str], ms: list[dict]) -> list[float]:
    """Mean log-odds of the fold models (the held-out scale of the check)."""
    if not ms:
        return []
    X = matrix(ms, feats)
    return list(np.mean([m.decision_function(X) for m in models], axis=0))


def place(scores: list[float], centres: dict, thr: float) -> dict:
    """Median, range and position p (0 = written centre, 1 = spoken centre); ``p_sermons`` is
    the same on the sermon pair's scale (0 = printed sermons, 1 = short-hand sermons), added
    after the check showed the pooled spoken centre is mostly Old Bailey testimony (post hoc,
    reported beside the card's rule, not in place of it)."""
    if not scores:
        return {"n": 0, "not_attempted": "no window"}
    s = summary(scores)
    w, sp = centres["written_median"], centres["spoken_median"]
    s["p"] = _r((s["median"] - w) / (sp - w))
    if "sermons_printed_median" in centres:
        a, b = centres["sermons_printed_median"], centres["sermons_shorthand_median"]
        s["p_sermons"] = _r((s["median"] - a) / (b - a))
    s["p10_p"] = _r((s["p10"] - w) / (sp - w))
    s["p90_p"] = _r((s["p90"] - w) / (sp - w))
    s["share_scored_spoken"] = _r(sum(1 for x in scores if x >= thr) / len(scores))
    return s


# ------------------------------------------------------------------------------ targets


def _strip_front(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            return text[end + 4 :]
    return text


def _read(paths: list[str], base: Path | None = None) -> str | None:
    parts = []
    for p in paths:
        try:
            f = (base / p) if base else Path(p)
            parts.append(_strip_front(f.read_text(errors="replace")))
        except OSError:
            return None  # not attempted
    return "\n".join(parts)


def named_texts(cfg: dict) -> dict[str, dict[str, tuple[str, bool]]]:
    """{group: {name: (raw text, verse)}} for the received set, the Bible-style imitations and
    the genuine translations; an unreadable text is left out and listed."""
    d, tr = cfg["lab"]["dictated"], cfg["lab"]["translation"]
    res: dict[str, dict] = {"received": {}, "bible_style": {}, "translations": {}}
    missing: dict[str, str] = {}
    for name, (role, verse, files) in d["received"].items():
        x = _read(files, FAST)
        if x is None:
            missing[name] = "unreadable"
        else:
            res["received"][name] = (x, bool(verse), role)
    for name, spec in tr["imitations"].items():
        if name == "short_pieces":
            continue
        x = _read([spec] if isinstance(spec, str) else spec)
        if x is None:
            missing[name] = "unreadable"
        else:
            res["bible_style"][name] = (x, False, "imitation")
    for name, files in d["translations"].items():
        x = _read(files, FAST)
        if x is None:
            missing[name] = "unreadable"
        else:
            res["translations"][name] = (x, False, "translation")
    res["_missing"] = missing
    return res


def bom_paragraphs() -> list[dict]:
    labels = {
        r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines()) if r["kind"] == "body"
    }
    rows = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if lab is not None and r["kind"] == "body":
            rows.append({**lab, "text": r["text"], "book": r["book"]})
    return rows


def kjv_parts(cfg: dict) -> dict[str, str]:
    order: list[str] = []
    text: dict[str, list[str]] = defaultdict(list)
    for line in KJV.read_text().splitlines():
        r = json.loads(line)
        if r["book_name"] not in text:
            order.append(r["book_name"])
        text[r["book_name"]].append(r["text"])
    res = {}
    for part, (a, b) in cfg["lab"]["spoken"]["kjv_parts"].items():
        books = order[order.index(a) : order.index(b) + 1]
        res[part] = " ".join(" ".join(text[k]) for k in books)
    return res


def _clean_ms_html(h: str) -> str:
    """Editors' headings and comments removed; the scribes' "&" (an HTML entity here, which the
    manuscript tokenizer would drop) written out as "and" ("&c" as "etc")."""
    h = re.sub(r"&amp;\s?c\b\.?", " etc ", h).replace("&amp;", " and ")
    h = re.sub(r'<span[^>]*class="anonymous-block"[^>]*>.*?</span>', " ", h, flags=re.S)
    h = re.sub(r"<span[^>]*editorial-comment[^>]*>.*?</span>", " ", h, flags=re.S)
    return h


def manuscript_words(path: Path, vocab: set[str], pages: set[int] | None = None) -> list | None:
    """A manuscript's final reading (struck words dropped, insertions kept), page order."""
    from manuscript.corrections import tokens

    try:
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    except OSError:
        return None
    parts = []
    for p in rows:
        if pages is not None and p["page"] not in pages:
            continue
        toks = tokens(_clean_ms_html(p.get("expanded_html") or p.get("clear_html") or ""))
        parts.append(" ".join(x for k, x in toks if k in ("word", "ins")))
    return words(re.sub(r"\[[^\]]{0,80}\]", " ", " ".join(parts)), vocab)


def own_hand_words(cfg: dict, vocab: set[str]) -> tuple[list[str], list[str]] | None:
    """Words in Joseph Smith's own hand in his letters and journals (hand logic of
    ``lab.mserrors.walk``); the files read."""
    from manuscript.corrections import tokens

    skip = tuple(cfg["lab"]["spoken"]["js_own_hand_skip"])
    files = sorted(CANDIDATES.glob("js-*.jsonl")) + sorted(CANDIDATES.glob("t73-*.jsonl"))
    files = [f for f in files if not f.stem.startswith(skip) and "revelations" not in f.stem]
    got: list[str] = []
    used = []
    for f in files:
        try:
            pages = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
        except OSError:
            continue
        cur, n0 = "Joseph Smith Jr.", len(got)
        for page in pages:
            hands = [s["name"].replace("  ", " ") for s in page.get("scribes") or []] or [cur]
            toks = tokens(_clean_ms_html(page.get("expanded_html") or ""))
            notes = sum(k == "scribe" for k, _ in toks)
            seq = [cur, *hands] if notes >= len(hands) else hands
            cur, k_note, js = seq[0], 0, False
            for kind, txt in toks:
                if kind == "scribe":
                    k_note += 1
                    cur = seq[min(k_note, len(seq) - 1)]
                elif kind == "js":
                    js = True
                elif kind in ("word", "ins"):
                    if js or cur == "Joseph Smith Jr.":
                        got.append(txt)
                    if kind == "word" and js and txt[-1:] in ".?!":
                        js = False
        if len(got) > n0:
            used.append(f.stem)
    if not got:
        return None
    return words(" ".join(got), vocab), used


def js_revelations(cfg: dict, vocab: set[str]) -> list[str] | None:
    parts: list[str] = []
    try:
        for pat in cfg["lab"]["dictated"]["js_files"]:
            p = Path(pat)
            for f in sorted(p.parent.glob(p.name)):
                parts += [x for x in f.read_text(errors="replace").splitlines()
                          if not x.startswith("## ")]  # fmt: skip
    except OSError:
        return None
    return words(" ".join(parts), vocab) if parts else None


def moses_words(cfg: dict, vocab: set[str]) -> list[str] | None:
    from lab.dictations import _page_no, strip_editorial

    a, b = cfg["lab"]["spoken"]["moses_pages"]
    try:
        rows = [json.loads(x) for x in OT1.read_text().splitlines()]
    except OSError:
        return None
    rows = [r for r in rows if _page_no(r) is not None and a <= _page_no(r) <= b]
    return words(strip_editorial("\n".join(r["text"] for r in rows)), vocab)


def speech_segments(cfg: dict) -> dict[str, list[str]]:
    """The book's words as narration, direct speech, sermons and quoted Isaiah, by the study's
    speaker labelling (simulated): narration is a book's own narrator labels."""
    from eval import speakers

    t = cfg["lab"]["spoken"]
    narr = {b: set(v) for b, v in t["narrators"].items()}
    serm, quoted = set(t["sermon_speakers"]), set(t["not_speech_labels"])
    done = speakers._done()
    res: dict[str, list[str]] = defaultdict(list)
    for c in speakers.chapters():
        r = done.get(speakers._key(c))
        if not r or r["state"] != "DONE":
            continue
        us = speakers.units(c["text"])
        segs = r["segments"]
        for s, nxt in zip(segs, [*segs[1:], {"from": len(us) + 1}], strict=True):
            ws = [w for u in us[s["from"] - 1 : nxt["from"] - 1] for w in u]
            spk = s["speaker"]
            if spk in narr.get(c["book"], set()):
                res["narration"] += ws
            elif spk in quoted:
                res["quoted_isaiah"] += ws
            else:
                res["direct_speech"] += ws
                if spk in serm:
                    res["sermons"] += ws
                else:
                    res["other_speech"] += ws
    return res


def target_marks(w: list[str] | None, t: dict, trim: bool = False) -> list[dict] | str:
    if w is None:
        return "not attempted (unreadable or absent)"
    ws = windows(w, t, t["max_windows_target"], trim)
    if not ws:
        return f"too short ({len(w)} words)"
    return [marks(x, t) for x in ws]


def targets(cfg: dict, vocab: set[str]) -> dict[str, dict[str, list[dict] | str]]:
    """{group: {name: window marks or a reason}} for everything scored after the check."""
    t = cfg["lab"]["spoken"]
    T: dict[str, dict] = defaultdict(dict)
    nt = named_texts(cfg)
    words_of: dict[str, int] = {}
    for grp in ("received", "bible_style", "translations"):
        for name, (raw, verse, _role) in nt[grp].items():
            w = words(dictated.clean(raw, cfg, verse), vocab)
            words_of[name] = len(w)
            T[grp][name] = target_marks(w, t, trim=True)
    paras = bom_paragraphs()
    from lab.wherefore import QUOTED, SMALL

    def ws_of(sel) -> list[str]:
        return words(" ".join(p["text"] for p in paras if sel(p)), vocab)

    T["bom"]["whole_1830"] = target_marks(ws_of(lambda p: True), t)
    T["bom"]["without_quoted_chapters"] = target_marks(
        ws_of(lambda p: (p["book"], p["chapter_1830"]) not in QUOTED), t
    )
    for nm in ("Nephi", "Jacob", "Mormon", "Moroni"):
        T["bom_narrator"][nm] = target_marks(ws_of(lambda p, nm=nm: p["narrator"] == nm), t)
    T["bom_narrator"]["small plates others"] = target_marks(
        ws_of(lambda p: p["narrator"] in SMALL and p["narrator"] not in ("Nephi", "Jacob")), t
    )
    for b in dict.fromkeys(p["book"] for p in paras):
        T["bom_book"][b] = target_marks(ws_of(lambda p, b=b: p["book"] == b), t)
    seg = speech_segments(cfg)
    for k in ("narration", "direct_speech", "sermons", "other_speech", "quoted_isaiah"):
        T["bom_speech"][k] = target_marks(words(" ".join(seg.get(k, [])), vocab), t)
    om_pages: set[int] = set()
    om_paras: set[int] = set()
    try:
        for x in ALIGN_OM.read_text().splitlines():
            a = json.loads(x)
            om_pages.add(a["page"])
            if a.get("para_first") is not None:
                om_paras.update(range(a["para_first"], a["para_last"] + 1))
    except OSError:
        pass
    T["bom_manuscripts"]["original_manuscript"] = target_marks(manuscript_words(ORIGINAL, vocab), t)
    T["bom_manuscripts"]["printers_manuscript"] = target_marks(manuscript_words(PRINTERS, vocab), t)
    T["bom_manuscripts"]["1830_where_original_extant"] = target_marks(
        ws_of(lambda p: p["seq"] in om_paras) if om_paras else None, t
    )
    T["joseph_smith"]["revelations_1828_1833"] = target_marks(js_revelations(cfg, vocab), t)
    T["joseph_smith"]["moses_ot_revision_1"] = target_marks(moses_words(cfg, vocab), t)
    oh = own_hand_words(cfg, vocab)
    T["joseph_smith"]["own_hand_letters_journals"] = target_marks(oh[0] if oh else None, t)
    for part, text in kjv_parts(cfg).items():
        T["kjv"][part] = target_marks(words(text, vocab), t)
    T["_meta"] = {
        "missing": nt["_missing"],
        "words": words_of,
        "own_hand_files": oh[1] if oh else [],
        "roles": {n: v[2] for n, v in nt["received"].items()},
    }
    return T


def dictation_order(cfg: dict, vocab: set[str], models: list, feats: list[str]) -> dict:
    """Rank correlation of window score with dictation position (1830 text in dictation order)."""
    from scipy.stats import spearmanr

    t = cfg["lab"]["spoken"]
    paras = sorted(bom_paragraphs(), key=lambda p: (p["dictation_position"], p["seq"]))
    w, pos = [], []
    for p in paras:
        x = words(p["text"], vocab)
        w += x
        pos += [p["dictation_position"]] * len(x)
    wins = contiguous(w, t["window_words"])
    ms = [marks(x, t) for _i, x in wins]
    sc = score(models, feats, ms)
    mid = [pos[i + t["window_words"] // 2] for i, _x in wins]
    rho, pval = spearmanr(mid, sc)
    return {"windows": len(wins), "spearman": _r(float(rho)), "p_value": _r(float(pval), 6)}


# ------------------------------------------------------------------------------ the run


def verdict(places: dict, t: dict) -> dict:
    book = places["bom"]["whole_1830"]
    kjv = [v["p"] for v in places["kjv"].values() if "p" in v]
    imit = [v["p"] for v in places["bible_style"].values() if "p" in v]
    kjv_all = places["kjv_all"]["p"]
    imit_med = float(np.median(imit)) if imit else None
    bible = kjv_all >= t["bible_reading"] or (imit_med is not None
                                               and imit_med >= t["bible_reading"])  # fmt: skip
    p = book["p"]
    if bible:
        ans = "cannot tell"
    elif p >= t["like_speech"]:
        ans = "like speech"
    elif p <= t["like_writing"]:
        ans = "like writing"
    else:
        ans = "between"
    return {"answer": ans, "book_p": p, "kjv_all_p": kjv_all, "kjv_parts_p": kjv,
            "imitations_median_p": _r(imit_med), "score_reads_bible_manner": bible}  # fmt: skip


def evaluate(cfg: dict, rows: list[dict], T: dict, feats: list[str], vocab: set[str]) -> dict:
    t = cfg["lab"]["spoken"]
    ck = check([dict(r) for r in rows], feats, t)
    res = {"known_answer": ck["result"]}
    if not ck["result"]["passed"]:
        res["stopped"] = "the known-answer check missed its bar; nothing else was scored"
        return res
    models, cen = ck["models"], ck["result"]["centres"]
    thr = ck["result"]["balanced_threshold"]
    places: dict[str, dict] = {}
    for grp, items in T.items():
        if grp.startswith("_"):
            continue
        places[grp] = {}
        for name, ms in items.items():
            places[grp][name] = (
                {"not_attempted": ms}
                if isinstance(ms, str)
                else place(score(models, feats, ms), cen, thr)  # fmt: skip
            )
    kjv_ms = [m for v in T["kjv"].values() if not isinstance(v, str) for m in v]
    places["kjv_all"] = place(score(models, feats, kjv_ms), cen, thr)
    places["labelled_sets_heldout"] = {
        s: place([r["_held"] for r in ck["rows"] if r["set"] == s], cen, thr)
        for s in sorted({r["set"] for r in rows})
    }
    res["places"] = places
    written = [r for r in rows if r["label"] == 0]
    picks = {"book_of_mormon_1830": T["bom"]["whole_1830"], "kjv_all": kjv_ms,
             "original_manuscript": T["bom_manuscripts"]["original_manuscript"],
             "joseph_smith_revelations": T["joseph_smith"]["revelations_1828_1833"],
             **{s: [r for r in rows if r["set"] == s]
                for s in ("S1_oldbailey", "S2_shorthand_sermons")}}  # fmt: skip
    res["contributions_post_hoc"] = {
        k: contributions(ck["full"], feats, v, written) if isinstance(v, list) else {}
        for k, v in picks.items()
    }
    res["kjv_false_positive_rate"] = places["kjv_all"]["share_scored_spoken"]
    res["dictation_order"] = dictation_order(cfg, vocab, models, feats)
    res["verdict"] = verdict(places, t)
    return res


def mark_means(rows: list[dict], T: dict) -> dict:
    """Mean of each mark per labelled set and per main target (the plain-numbers table)."""
    res = {}
    for s in sorted({r["set"] for r in rows}):
        sub = [r for r in rows if r["set"] == s]
        res[s] = {f: _r(float(np.mean([r[f] for r in sub])), 3) for f in FEATURES}
    picks = [("bom", "whole_1830"), ("bom_speech", "narration"), ("bom_speech", "sermons"),
             ("kjv", "law_history"), ("kjv", "gospels_acts"),
             ("joseph_smith", "revelations_1828_1833"),
             ("joseph_smith", "own_hand_letters_journals"),
             ("bom_manuscripts", "original_manuscript")]  # fmt: skip
    for g, n in picks:
        ms = T.get(g, {}).get(n)
        if isinstance(ms, list) and ms:
            res[f"{g}/{n}"] = {f: _r(float(np.mean([m[f] for m in ms])), 3) for f in FEATURES}
    imit = [m for v in T.get("bible_style", {}).values() if isinstance(v, list) for m in v]
    if imit:
        res["bible_style/all"] = {f: _r(float(np.mean([m[f] for m in imit])), 3) for f in FEATURES}
    return res


def run(cfg: dict, check_only: bool = False, workers: int = 4) -> dict:
    t = cfg["lab"]["spoken"]
    vocab, _ = twovoices.kjv_vocab_and_grams(5)
    rows, rec = labelled_windows(cfg, vocab, workers)
    free = [f for f in FEATURES if f not in set(t["and_family"])]
    if check_only:
        main = check([dict(r) for r in rows], FEATURES, t)["result"]
        var = check([dict(r) for r in rows], free, t)["result"]
        return {"sets": rec, "known_answer": main, "known_answer_and_free": var}
    main = check([dict(r) for r in rows], FEATURES, t)["result"]
    res: dict = {"sets": rec, "known_answer": main}
    if not main["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
        res["known_answer_and_free"] = check([dict(r) for r in rows], free, t)["result"]
        return res
    T = targets(cfg, vocab)
    res["text_words"] = T["_meta"]
    res["main"] = evaluate(cfg, rows, T, FEATURES, vocab)
    res["and_free"] = evaluate(cfg, rows, T, free, vocab)
    res["mark_means"] = mark_means(rows, T)
    return res


def _strip(o):
    if isinstance(o, float) and o != o:
        return None
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_strip(v) for v in o]
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
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
    ap.add_argument("command", choices=["parse", "check", "run"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    if a.command == "parse":
        print(json.dumps(parse_oldbailey(), indent=1))
        return 0
    cfg = config.load()
    res = run(cfg, check_only=a.command == "check", workers=a.workers)
    res["config_sha256"] = config.sha256_of_config()
    res["git_commit"] = _commit()
    res["rule_set"] = "everything (registry filter: work, text, dup_keeper, not sealed, OCR kept)"
    name = "check.json" if a.command == "check" else "result.json"
    out(OUT / name).write_text(json.dumps(_strip(res), indent=1) + "\n")
    ka = res["known_answer"]
    print(json.dumps({k: ka[k] for k in ("auc_all", "auc_sermons", "sermon_groups", "passes")}))
    if "main" in res:
        print(json.dumps(res["main"].get("verdict"), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
