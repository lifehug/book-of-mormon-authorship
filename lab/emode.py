"""BOM-119: Carmack's early modern syntax rates, measured by rule on every book in the library.

Carmack (Interpreter 2015, 2017, 2018; Skousen and Carmack 2018) reports that the Book of Mormon
uses affirmative periphrastic "did" ("they did go") in 20.2% of past-tense contexts, the King
James Bible in 1.7%, Bible-style books of the 1700s and 1800s in 2% or less, and lists other
features of 1500s-1600s English. This measures each feature by a stated rule (no parser), checks
the rules on known answers (the two published rates; early against late dated works; a hand
check of extracted hits), then places the Book of Mormon among every library work 1500-1830 and
among its controls (Bible-style books, marked translations, Joseph Smith's other texts). The
test card, written first, is ``data/private/lab/owner/2026-11-20-emode-syntax/card.md``;
settings are ``lab.emode`` in the config. Result files hold ids, years and numbers, no text.

The did-rate needs a count of simple past-tense verbs, which without a tagger is approximated:
strong past forms that are only past, past forms shared with the participle and -ed / -'d words
whose stem is a verb (a fixed lexicon of words seen after a modal), not after have, be or a
determiner. Forms identical to the present (put, set, cast) are not counted.

Usage::

    python -m lab.emode lexicon     # build the verb lexicon -> data/corpus/lab/emode/ (3 min)
    python -m lab.emode check       # known-answer checks (b) and (c); writes hits to read (5 min)
    python -m lab.emode pass        # every library work -> data/corpus/lab/emode/part_*.jsonl
    python -m lab.emode run         # -> data/lab/reruns/emode_syntax/result.json (2 min)
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.compute as pc

from lab import door, registry
from lab.paths import FAST, NOTES, REGISTRY, out
from lab.wherefore import EDITION, LABELS, QUOTED
from metadata import config

OUT = REGISTRY / "reruns" / "emode_syntax"
WORK = FAST / "emode"
LEXICON = WORK / "lexicon.json"
CARD = NOTES / "owner" / "2026-11-20-emode-syntax"
KJV = Path("data/kjv/kjv.jsonl")
CONTROLS = Path("data/controls/pseudo_biblical_primary.jsonl")
BIBLE_STYLE = FAST / "sources" / "bible_style"
MARC = FAST / "sources" / "translation_labels" / "hathitrust_marc.jsonl"
HT_CATALOG = Path("data/catalog/hathitrust.jsonl.gz")
JS = Path("data/private/candidates")
DICTATED = Path("data/private/lab/sources/dictated")

# ----------------------------------------------------------------------------- word lists

TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?|[.!?;:]")
STOPS = frozenset(".!?;:")
DID = frozenset("did didst dyd dyde didde dydde diddest didest".split())
NEG = frozenset("not never n't nought naught nat".split())
NEG_HEAD = frozenset("neither nor never not".split())
MODALS = frozenset(
    "shall will may might can could would should must shalt wilt canst mayest mayst mightest "
    "couldest wouldest shouldest".split()
)
PRONOUNS = frozenset("he she they we i ye thou it you".split())
WH = frozenset("why how what where when whom who whither whence".split())
DETS = frozenset(
    "the a an his her their my thy our your its this that these those every no some any whose "
    "such all many".split()
)
INV_TRIGGER = frozenset("so thus also then likewise therefore again now yea there here".split())
ADVERBS = frozenset(
    "also again then thus indeed verily likewise all both still yet even there therefore "
    "nevertheless now once ever oft often always first afterwards straightway forthwith "
    "immediately presently soon much greatly exceedingly truly surely really together "
    "thereby therein thereupon accordingly moreover further hereby".split()
)
HAVE_BE = frozenset(
    "have has had hath hast hadst having haue hath hauing be been being am is are art was were "
    "wast wert bin ben become became get got 's".split()
)
NON_VERBS = frozenset(
    "be have has had being been not never also all both the a an his her their my thy our your "
    "its this that these those every no some any he she they we i ye thou it you me him us them "
    "thee there here so then thus therefore yet still even now once ever always only well much "
    "more most very too again indeed surely truly verily certainly perhaps likewise rather soon "
    "first in on at by to of for from with without into unto upon up down out over under "
    "through before after about against among between and or but nor if as than when while "
    "whom who which what where why how whose one two three four five six seven ten hundred "
    "thousand none nothing something everything anything man men god lord however often next "
    "anon neuer sometimes always also do".split()
)
NOT_ED = frozenset(
    "seed speed deed creed steed weed reed bleed breed feed heed need indeed proceed exceed "
    "succeed red bed shed wed hundred kindred naked wicked sacred beloved shred sled fled led "
    "bred sped".split()
)
STRONG = frozenset(
    "came went saw spake spoke took gave knew began ran rose arose fell ate drank sang wrote "
    "smote slew drove rode grew threw flew drew chose forsook shook bare bore tare tore sware "
    "swore wore brake broke stole forgave became overcame blew strove strode sank sprang swam "
    "bade forbade gat clave crew awoke gaue tooke toke sawe wente knewe beganne ranne cam".split()
)
AMBIG = frozenset(
    "said made found heard brought sought taught thought told sold held stood understood "
    "withstood led fed fled felt kept slept wept left met sent spent built lost sat laid paid "
    "fought caught bought dwelt lent bent wrought beheld hid bound sayd sayde saide herd".split()
)
THOU = frozenset(
    {w + "est" for w in STRONG | AMBIG} | {w + "st" for w in STRONG | AMBIG if w.endswith("e")}
) | frozenset({"saidst", "madest", "camest", "wentest", "sawest", "gavest", "tookest"})
LEVELED = (
    "spake came went took gave ate bare brake began ran rose arose fell drank sang wrote smote "
    "slew drove rode grew knew saw chose forsook shook sware swore tore wore broke spoke stole "
    "forgave overcame did"
)

# "cause" / "command" as nouns: not counted after these words (checked on the token before).
DET_NOT = frozenset(
    "the a his her their our my thy your this that no good just its same own what which whose "
    "great first any every".split()
)
_FIN = r"(?P<fin>that)\s+(?:[a-z']+,?\s+){1,4}?(?:should|shall|might|may|would|will|could|can|"
_FIN += r"must|shouldst|shalt|mightest)\b"
_INF = r"(?P<inf>to)\s+(?!the\b|a\b|an\b|his\b|their\b|them\b|him\b|me\b|us\b)[a-z]+"
_GAP = r"(?:(?!that\b|to\b)[a-z']+,?\s+)"
CAUSE = re.compile(r"\bcaus(?:e|es|ed|eth|est|edst|ing)\b,?\s+")
COMMAND = re.compile(r"\bcommand(?:s|ed|eth|est|edst|ing)?\b,?\s+")
FIN_AT = re.compile(_GAP + r"{0,4}" + _FIN)
INF_AT = re.compile(_GAP + r"{1,4}" + _INF)
PATTERNS = {
    "more_part": re.compile(r"\b(?:the|a)\s+more\s+parts?\b"),
    "if_it_so_be": re.compile(r"\bif\s+it\s+so\s+be\b"),
    "impersonal": re.compile(
        r"\bit\s+(?:supposeth|sufficeth|repenteth|grieveth|pleaseth|irketh|behoveth|behooveth|"
        r"listeth|liketh|yearneth)\s+(?:me|him|us|them|thee|her|you)\b"
    ),
    "plural_was": re.compile(r"\b(?:they|we|ye)\s+was\b"),
    "leveled": re.compile(
        r"\b(?:have|has|had|hath|hast|hadst|having)\s+(?:not\s+|never\s+|also\s+|all\s+)?"
        r"(?:" + LEVELED.replace(" ", "|") + r")\b"
    ),
}
PERSONAL = re.compile(
    r"\b(?:man|men|people|those|person|persons|woman|women|child|children|brethren|brother|"
    r"brothers|king|kings|son|sons|daughter|daughters|father|fathers|servant|servants|prophet|"
    r"prophets|priest|priests|disciples|he|they|them|friends|friend|enemies|enemy|soldiers|wife|"
    r"wives|mother|mothers|angel|angels|people's)\s+(which|who|whom|that)\b"
)
# Feature name -> how it is read for "at or above the Book of Mormon" (all: higher = earlier).
FEATURES = ("did_rate", "did_per10k", "more_part", "cause_finite", "command_finite", "leveled",
            "plural_was", "personal_which", "if_it_so_be", "impersonal")  # fmt: skip


# ----------------------------------------------------------------------------- the extractors


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower().replace("’", "'").replace("ſ", "s"))


def _stems(w: str) -> list[str]:
    if w.endswith("edst"):
        w = w[:-2]
    if w.endswith("'d"):
        b = w[:-2]
        return [b, b + "e"]
    if not w.endswith("ed") or len(w) < 5:
        return []
    got = [w[:-1], w[:-2]]
    if w.endswith("ied"):
        got.append(w[:-3] + "y")
    if len(w) > 5 and w[-3] == w[-4]:
        got.append(w[:-3])
    return got


def _back(toks: list[str], i: int) -> str:
    """The word before position ``i``, skipping up to two adverbs or negatives."""
    j, skipped = i - 1, 0
    while j >= 0 and skipped < 2 and (toks[j] in ADVERBS or toks[j] in NEG):
        j, skipped = j - 1, skipped + 1
    return toks[j] if j >= 0 else "."


def _question(toks: list[str], i: int) -> bool:
    for t in toks[i : i + 80]:
        if t in STOPS:
            return t == "?"
    return False


def did_hits(toks: list[str], lex: frozenset, window: int) -> list[tuple[int, str]]:
    """(position, kind) of every periphrastic did; kind adjacent / adverbial / subject /
    neither (did after neither, nor, never, not: counted apart, not in the rate)."""
    hits = []
    n = len(toks)
    for i in [k for k, t in enumerate(toks) if t in DID]:
        nxt = toks[i + 1] if i + 1 < n else "."
        prev = toks[i - 1] if i else "."
        if nxt in NEG:
            continue
        j, kind = i + 1, "adjacent"
        if nxt in PRONOUNS:
            if prev in STOPS or prev in WH:
                continue
            j, kind = i + 2, "subject"
        elif nxt in DETS and nxt not in ("all",) and prev in INV_TRIGGER:
            k = i + 2
            while k < min(n, i + 4) and toks[k] not in lex and toks[k] not in STOPS:
                k += 1
            if k < n and toks[k] in lex and k > i + 2:
                j, kind = k, "subject"
        stop = i + 1 + window
        while j < min(n, stop) and (toks[j] in ADVERBS or toks[j].endswith("ly")):
            if toks[j] not in lex:
                kind = "adverbial" if kind == "adjacent" else kind
            j += 1
        if j >= n or j > stop or toks[j] in NEG or toks[j] not in lex:
            continue
        if _question(toks, i):
            continue
        hits.append((i, "neither" if prev in NEG_HEAD else kind))
    return hits


def past_count(toks: list[str], lex: frozenset) -> tuple[int, int]:
    """(simple past tokens, of which "came to pass")."""
    past = ctp = 0
    cand = STRONG | THOU | AMBIG
    for i in [k for k, t in enumerate(toks) if t in cand or t.endswith(("ed", "'d", "edst"))]:
        t = toks[i]
        if t in STRONG or t in THOU:
            pass
        elif t in AMBIG:
            pass
        elif (t.endswith("ed") or t.endswith("'d") or t.endswith("edst")) and t not in NOT_ED:
            if t in lex or not any(s in lex for s in _stems(t)):
                continue
        else:
            continue
        b = _back(toks, i)
        if b in HAVE_BE or b in DETS or b in MODALS:
            continue
        past += 1
        if t == "came" and toks[i + 1 : i + 3] == ["to", "pass"]:
            ctp += 1
    return past, ctp


def _choice(rx: re.Pattern, text: str) -> tuple[int, int]:
    fin = inf = 0
    for m in rx.finditer(text):
        before = text[max(0, m.start() - 12) : m.start()]
        if before.endswith(" ") and before[:-1].rsplit(" ", 1)[-1] in DET_NOT:
            continue
        f, g = FIN_AT.match(text, m.end()), INF_AT.match(text, m.end())
        if f and (not g or f.start("fin") < g.start("inf")):
            fin += 1
        elif g:
            inf += 1
    return fin, inf


def measure(text: str, lex: frozenset, window: int) -> dict:
    """Raw counts of every feature for one text (no rates, no text)."""
    toks = tokens(text)
    words = sum(1 for t in toks if t not in STOPS)
    kinds = Counter(k for _, k in did_hits(toks, lex, window))
    past, ctp = past_count(toks, lex)
    flat = " ".join(t for t in toks if t not in STOPS)
    flat_punct = " ".join(toks)
    res = {"words": words, "past": past, "came_to_pass": ctp}
    for k in ("adjacent", "adverbial", "subject", "neither"):
        res["did_" + k] = kinds.get(k, 0)
    for name, rx in PATTERNS.items():
        res[name] = len(rx.findall(flat))
    res["cause_fin"], res["cause_inf"] = _choice(CAUSE, flat_punct)
    res["cmd_fin"], res["cmd_inf"] = _choice(COMMAND, flat_punct)
    rel = Counter(m.group(1) for m in PERSONAL.finditer(flat_punct))
    res["rel_which"], res["rel_other"] = rel["which"], rel["who"] + rel["whom"] + rel["that"]
    return res


def did_n(c: dict) -> int:
    return c["did_adjacent"] + c["did_adverbial"] + c["did_subject"]


def rates(c: dict, min_past: int = 0, drop_ctp: bool = False) -> dict:
    """Rates from raw counts; None where a share has no frame or too few past contexts."""
    w = max(c["words"], 1)
    d = did_n(c)
    past = c["past"] - (c["came_to_pass"] if drop_ctp else 0)

    def share(a: int, b: int) -> float | None:
        return round(a / (a + b), 4) if a + b else None

    return {
        "did_rate": round(d / (d + past), 4) if d + past >= max(min_past, 1) else None,
        "did_per10k": round(1e4 * d / w, 3),
        "more_part": round(1e4 * c["more_part"] / w, 3),
        "cause_finite": share(c["cause_fin"], c["cause_inf"]),
        "command_finite": share(c["cmd_fin"], c["cmd_inf"]),
        "leveled": round(1e4 * c["leveled"] / w, 3),
        "plural_was": round(1e4 * c["plural_was"] / w, 3),
        "personal_which": share(c["rel_which"], c["rel_other"]),
        "if_it_so_be": round(1e4 * c["if_it_so_be"] / w, 3),
        "impersonal": round(1e4 * c["impersonal"] / w, 3),
    }


# ----------------------------------------------------------------------------- texts


def kjv_text() -> str:
    return "\n".join(json.loads(line)["text"] for line in KJV.read_text().splitlines())


def bom_text(drop_quotes: bool = False) -> str:
    labels = {
        r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines()) if r["kind"] == "body"
    }
    keep = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if lab is None or r.get("kind") != "body":
            continue
        if drop_quotes and (r["book"], lab["chapter_1830"]) in QUOTED:
            continue
        keep.append(r["text"])
    return "\n".join(keep)


def _jsonl_text(path: Path) -> str:
    return "\n".join(json.loads(line).get("text") or "" for line in path.read_text().splitlines())


def library_rows(cfg: dict) -> list[dict]:
    e = cfg["lab"]["emode"]
    t = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(t["kind"], "work"), pc.equal(t["has_text"], True)),
        pc.equal(t["dup_keeper"], True),
    )
    cols = ["work_id", "source", "year", "words", "genre", "sealed", "ocr_excluded"]
    return [
        r
        for r in t.filter(keep).select(cols).to_pylist()
        if not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and e["year_min"] <= r["year"] <= e["year_max"]
        and (r["words"] or 0) >= e["min_words"]
    ]


def load_lexicon() -> frozenset:
    return frozenset(json.loads(LEXICON.read_text())["verbs"])


def _inflected(w: str, after: Counter, n: int) -> bool:
    """An -ing, -ed, -'d or -ly form of a word that is itself seen as a verb (going, called),
    or an -ly adverb; "bring", "exceed", "multiply" are kept (first version dropped them)."""
    if w.endswith("'d"):
        return True
    if w.endswith("ing"):
        stems = (w[:-3], w[:-3] + "e", w[:-4])
    elif w.endswith("ed"):
        stems = (w[:-2], w[:-1], w[:-3])
    else:
        return w.endswith("ly") and w not in LY_VERBS
    return any(after[s] >= n for s in stems if len(s) > 2 or s in ("go", "do", "be"))


LY_VERBS = frozenset(
    "multiply reply apply supply fly rely ally comply imply sally rally dally tally bully".split()
)


def build_lexicon(cfg: dict) -> dict:
    """Words seen after a modal at least ``lexicon_min`` times and in at least
    ``lexicon_share`` of all their uses (King James + a library sample; no Book of Mormon)."""
    e = cfg["lab"]["emode"]
    rows = library_rows(cfg)
    random.Random(e["seed"]).shuffle(rows)
    rows = rows[: e["lexicon_sample"]]
    cat = door.catalog({r["work_id"] for r in rows})
    after: Counter = Counter()
    total: Counter = Counter()
    read = 0

    def add(text: str) -> None:
        toks = tokens(text)
        total.update(toks)
        after.update(b for a, b in zip(toks, toks[1:], strict=False) if a in MODALS)

    add(kjv_text())
    for r in rows:
        try:
            add(door.text_of({**cat[r["work_id"]], **r}))
            read += 1
        except (OSError, KeyError):
            continue
    verbs = sorted(
        w
        for w, n in after.items()
        if n >= e["lexicon_min"]
        and n >= e["lexicon_share"] * total[w]
        and (len(w) > 2 or w == "go")
        and w not in NON_VERBS
        and w not in MODALS
        and w not in DID
        and not _inflected(w, after, e["lexicon_min"])
    )
    res = {"works_read": read, "verbs": verbs, "seed": e["seed"], "min": e["lexicon_min"]}
    out(LEXICON).write_text(json.dumps(res) + "\n")
    return res


# ----------------------------------------------------------------------------- the library pass


def _one(job: tuple[dict, frozenset, int]) -> dict:
    row, lex, window = job
    base = {"work_id": row["work_id"], "year": row["year"], "source": row["source"]}
    try:
        text = door.text_of(row)
    except (OSError, KeyError) as exc:
        return {**base, "status": "not_attempted", "reason": type(exc).__name__}
    return {**base, "status": "ok", **measure(text, lex, window)}


def _part(job: tuple[int, list[dict], int]) -> int:
    idx, rows, window = job
    lex = load_lexicon()
    final = WORK / f"part_{idx:04d}.jsonl"
    if final.exists():
        return 0
    lines = [json.dumps(_one((r, lex, window))) for r in rows]
    tmp = WORK / f"part_{idx:04d}.tmp"
    out(tmp).write_text("\n".join(lines) + "\n")
    tmp.rename(final)
    return len(rows)


def library_pass(cfg: dict) -> int:
    e = cfg["lab"]["emode"]
    rows = sorted(library_rows(cfg), key=lambda r: r["work_id"])
    # Shuffled by seed, so that the parts finished at any moment are a random sample.
    random.Random(e["seed"]).shuffle(rows)
    cat = door.catalog({r["work_id"] for r in rows})
    rows = [{**cat[r["work_id"]], **r} for r in rows if r["work_id"] in cat]
    size = e["part_size"]
    jobs = [
        (i // size, rows[i : i + size], e["did_window"])
        for i in range(0, len(rows), size)
        if not (WORK / f"part_{i // size:04d}.jsonl").exists()
    ]
    print(f"{len(rows):,} works in {-(-len(rows) // size)} parts; {len(jobs)} to do", flush=True)
    t0, done = time.time(), 0
    with ProcessPoolExecutor(e["workers"]) as ex:
        for n in ex.map(_part, jobs):
            done += 1
            print(f"  part {done}/{len(jobs)} ({n} works) {time.time() - t0:.0f}s", flush=True)
    return 0


def read_parts() -> list[dict]:
    got = []
    for p in sorted(WORK.glob("part_*.jsonl")):
        got += [json.loads(line) for line in p.read_text().splitlines() if line]
    return got


# ----------------------------------------------------------------------------- known answers


def auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    wins = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return round(wins / (len(pos) * len(neg)), 4)


def pct_ranks(values: list[float | None]) -> list[float | None]:
    have = sorted(v for v in values if v is not None)
    if not have:
        return [None] * len(values)
    import bisect

    return [
        None
        if v is None
        else (bisect.bisect_left(have, v) + bisect.bisect_right(have, v)) / (2 * len(have))
        for v in values
    ]


def profile(rate_rows: list[dict]) -> list[float | None]:
    cols = {f: pct_ranks([r[f] for r in rate_rows]) for f in FEATURES}
    got = []
    for i in range(len(rate_rows)):
        xs = [cols[f][i] for f in FEATURES if cols[f][i] is not None]
        got.append(sum(xs) / len(xs) if xs else None)
    return got


def dated_sample(cfg: dict) -> tuple[list[dict], list[dict]]:
    e = cfg["lab"]["emode"]
    rows = library_rows(cfg)
    lo, hi = e["early_years"]
    early = [r for r in rows if r["source"] == "tcp" and lo <= r["year"] <= hi]
    lo, hi = e["late_years"]
    late = [r for r in rows if lo <= r["year"] <= hi]
    rng = random.Random(e["seed"])
    early, late = rng.sample(early, e["auc_sample"]), rng.sample(late, e["auc_sample"])
    cat = door.catalog({r["work_id"] for r in early + late})
    return [{**cat[r["work_id"]], **r} for r in early], [{**cat[r["work_id"]], **r} for r in late]


def check(cfg: dict) -> dict:
    """Known answers (b) and (c, drawing the hits). (a) needs the Book of Mormon: see ``run``."""
    e = cfg["lab"]["emode"]
    lex = load_lexicon()
    early, late = dated_sample(cfg)
    with ProcessPoolExecutor(e["workers"]) as ex:
        got = list(ex.map(_one, [(r, lex, e["did_window"]) for r in early + late], chunksize=4))
    ok = [g for g in got if g["status"] == "ok"]
    lo = e["early_years"][1]
    rr = [{**rates(g, e["min_past"]), "early": g["year"] <= lo} for g in ok]
    prof = profile(rr)
    res = {"not_attempted": len(got) - len(ok), "early": sum(r["early"] for r in rr)}
    res["late"] = len(rr) - res["early"]
    for f in FEATURES:
        res[f"auc_{f}"] = auc(
            [r[f] for r in rr if r["early"] and r[f] is not None],
            [r[f] for r in rr if not r["early"] and r[f] is not None],
        )
    res["auc_profile"] = auc(
        [p for p, r in zip(prof, rr, strict=True) if r["early"] and p is not None],
        [p for p, r in zip(prof, rr, strict=True) if not r["early"] and p is not None],
    )
    res["passed_b"] = (res["auc_did_rate"] or 0) >= e["auc_bar"] and (res["auc_profile"] or 0) >= e[
        "profile_auc_bar"
    ]
    res["median_did_rate"] = {
        side: _median(
            [r["did_rate"] for r in rr if r["early"] == flag and r["did_rate"] is not None]
        )
        for side, flag in (("early", True), ("late", False))
    }
    res["handcheck_drawn"] = draw_hits(cfg, early + late, lex)
    return res


def _median(xs: list[float]) -> float | None:
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def draw_hits(cfg: dict, rows: list[dict], lex: frozenset) -> int:
    """60 periphrastic hits from the King James Bible and the dated sample -> private file."""
    e = cfg["lab"]["emode"]
    pool = []
    sources = [("kjv", kjv_text())]
    for r in rows:
        try:
            sources.append((r["work_id"], door.text_of(r)))
        except (OSError, KeyError):
            continue
    for wid, text in sources:
        toks = tokens(text)
        pool += [(wid, toks, i, k) for i, k in did_hits(toks, lex, e["did_window"])]
    picked = random.Random(e["seed"]).sample(pool, min(e["handcheck"], len(pool)))
    lines = ["# Periphrastic did hits drawn for the hand check (private: quotes text)", ""]
    for n, (wid, toks, i, k) in enumerate(picked, 1):
        ctx = (
            " ".join(toks[max(0, i - 12) : i])
            + " ["
            + toks[i]
            + "] "
            + " ".join(toks[i + 1 : i + 10])
        )
        lines.append(f"{n}. `{wid}` ({k}): {ctx}")
    out(CARD / "handcheck_hits.md").write_text("\n".join(lines) + "\n")
    return len(picked)


def precision() -> dict | None:
    """The hand judgments (``handcheck.json`` in the card folder: number -> true/false)."""
    p = CARD / "handcheck.json"
    if not p.exists():
        return None
    marks = json.loads(p.read_text())
    good = sum(1 for v in marks.values() if v)
    return {"read": len(marks), "correct": good, "precision": round(good / max(len(marks), 1), 4)}


# ----------------------------------------------------------------------------- named texts


def js_texts() -> dict[str, str]:
    """Joseph Smith's other texts, by name (private sources; names only leave this function)."""
    got = {}
    for p in sorted(JS.glob("js-*.jsonl")):
        got[p.stem] = _jsonl_text(p)
    by_year: dict[str, list[str]] = {}
    for p in sorted((JS / "later").glob("*.txt")):
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\b(18[23]\d)\b", text[:200])
        by_year.setdefault(m.group(1) if m else "undated", []).append(text)
    for y, parts in by_year.items():
        got[f"revelations-later-{y}"] = "\n".join(parts)
    for d in sorted(DICTATED.iterdir()):
        if (d / "pages.jsonl").exists():
            got[f"dictated-{d.name}"] = _jsonl_text(d / "pages.jsonl")
    letters = [k for k in got if "letter" in k]
    got["js-letters-1829-1833-all"] = "\n".join(got[k] for k in letters)
    return got


def bible_style_texts() -> dict[str, str]:
    got = {}
    for d in sorted(BIBLE_STYLE.iterdir()):
        if (d / "text.txt").exists():
            got[f"bible_style/{d.name}"] = (d / "text.txt").read_text(errors="replace")
    for p in sorted((BIBLE_STYLE / "wordtree_books" / "pseudo_biblical").glob("*.md")):
        if "Book of Mormon" in p.name:
            continue  # the target itself, in another copy
        got[f"wordtree/{p.stem}"] = p.read_text(errors="replace")
    cat = door.catalog(set(ERI))
    for wid in ERI:  # every library copy of Chronicles of Eri (1822) with text
        try:
            got[f"eri/{wid}"] = door.text_of(cat[wid])
        except (OSError, KeyError):
            continue  # not attempted: left out, never a zero
    return got


# Chronicles of Eri (O'Connor 1822), the Bible-style book Carmack grants may exceed the rate: the
# library copies with text (catalog title search, 2026-11-20).
ERI = (
    "institutional_books:32044086799061",
    "institutional_books:32044090306911",
    "internet_archive:chronicleseri00ocogoog",
    "internet_archive:chronicleserior01ocogoog",
)


def translations() -> set[str]:
    """HathiTrust work ids whose catalogue record marks a translation (MARC 041 ind1 = 1)."""
    keys = set()
    for line in MARC.read_text().splitlines():
        r = json.loads(line)
        if any(f["tag"] == "041" and f["ind1"] == "1" for f in r["fields"]):
            keys.add(r["ht_bib_key"])
    ids = set()
    for line in gzip.open(HT_CATALOG, "rt"):
        r = json.loads(line)
        if r["ht_bib_key"] in keys:
            ids.add("hathitrust:" + r["htid"])
    return ids


AUTHOR_YEARS = re.compile(r"\b(1[0-9]{3})\??\s*-\s*(1[0-9]{3})?")
DIED = re.compile(r"\b(?:d\.|died)\s*(1[0-9]{3})")


def pre1700_author(author: str | None, cfg: dict) -> bool:
    """A reprint of an older text, as far as the author string tells (death or birth year)."""
    e = cfg["lab"]["emode"]
    if not author:
        return False
    m = AUTHOR_YEARS.search(author)
    if m:
        born, died = int(m.group(1)), int(m.group(2)) if m.group(2) else None
        if died and died < e["reprint_death_before"]:
            return True
        if born < e["reprint_birth_before"]:
            return True
    d = DIED.search(author)
    return bool(d and int(d.group(1)) < e["reprint_death_before"])


def reprint_judgments() -> dict:
    """My reading of the catalog title and author (not the text) of each work 1700-1830 that
    reaches the Book of Mormon's rate: work id -> {"reprint": bool, "kind": short label}. Kept in
    the card folder; a work not in it is reported as "not judged" and counted as a later text."""
    p = CARD / "reprints.json"
    return json.loads(p.read_text()) if p.exists() else {}


# ----------------------------------------------------------------------------- the run


def run(cfg: dict) -> dict:
    e = cfg["lab"]["emode"]
    lex = load_lexicon()
    w = e["did_window"]
    res: dict = {"settings": e, "lexicon_verbs": len(lex)}
    chk_path = WORK / "check.json"
    chk = json.loads(chk_path.read_text()) if chk_path.exists() else None
    res["known_answer_b"] = chk
    res["known_answer_c"] = precision()
    if not chk or not chk.get("passed_b") or not res["known_answer_c"]:
        res["stopped"] = "known-answer checks (b) or (c) missing or failed; not scored"
        return res
    if res["known_answer_c"]["precision"] < e["precision_bar"]:
        res["stopped"] = "hand-check precision below its bar; the Book of Mormon was not scored"
        return res
    named = {"kjv": measure(kjv_text(), lex, w)}
    named["book_of_mormon"] = measure(bom_text(), lex, w)
    named["book_of_mormon_without_quoted_chapters"] = measure(bom_text(True), lex, w)
    kj, bm = rates(named["kjv"]), rates(named["book_of_mormon"])
    pub = e["published"]
    res["known_answer_a"] = {
        "kjv_did_rate": kj["did_rate"],
        "kjv_published": pub["kjv"],
        "bom_did_rate": bm["did_rate"],
        "bom_published": pub["bom"],
        "kjv_ok": abs(kj["did_rate"] - pub["kjv"]) <= e["kjv_tolerance"],
        "bom_ok": abs(bm["did_rate"] - pub["bom"]) <= e["bom_tolerance"],
        "bom_did_count": did_n(named["book_of_mormon"]),
        "kjv_did_count": did_n(named["kjv"]),
        "without_came_to_pass": {
            "kjv": rates(named["kjv"], drop_ctp=True)["did_rate"],
            "bom": rates(named["book_of_mormon"], drop_ctp=True)["did_rate"],
        },
    }
    a_ok = res["known_answer_a"]["kjv_ok"] and res["known_answer_a"]["bom_ok"]
    res["did_rate_reproduced"] = a_ok
    key = "did_rate" if a_ok else "did_per10k"
    res["verdict_measure"] = key
    for name, text in {**js_texts(), **bible_style_texts()}.items():
        named[name] = measure(text, lex, w)
    res["named"] = {k: {"counts": c, "rates": rates(c, e["min_past"])} for k, c in named.items()}
    res["library"] = library(cfg, rates(named["book_of_mormon"]), key)
    return res


def library(cfg: dict, bom: dict, key: str) -> dict:
    e = cfg["lab"]["emode"]
    rows = read_parts()
    total = len(library_rows(cfg))
    ok = [r for r in rows if r.get("status") == "ok"]
    reg = {r["work_id"]: r for r in library_rows(cfg)}
    cat = door.catalog({r["work_id"] for r in ok})
    trans = translations()
    controls = {json.loads(x)["work_id"] for x in CONTROLS.read_text().splitlines()}
    for r in ok:
        r["rates"] = rates(r, e["min_past"])
        r["genre"] = (reg.get(r["work_id"]) or {}).get("genre")
    res = {
        "works_in_rule_set": total,
        "works_counted": len(ok),
        "not_attempted": len(rows) - len(ok),
        "not_yet_reached": total - len(rows),
        "coverage_by_decade": dict(sorted(Counter(r["year"] // 10 * 10 for r in ok).items())),
    }
    # Where the Book of Mormon falls in each half-century.
    halves = {}
    for lo in range(e["year_min"], e["year_max"] + 1, 50):
        grp = [r for r in ok if lo <= r["year"] < lo + 50]
        halves[f"{lo}-{min(lo + 49, e['year_max'])}"] = {
            f: _place(bom[f], [r["rates"][f] for r in grp]) for f in FEATURES
        }
    res["by_half_century"] = halves
    lo, hi = e["match_years"]
    late = [r for r in ok if lo <= r["year"] <= hi]
    res["match_1780_1830"] = {f: _at_or_above(bom, late, f) for f in FEATURES}
    every = [
        r
        for r in late
        if all(
            r["rates"][f] is not None and r["rates"][f] >= bom[f]
            for f in FEATURES
            if bom[f] is not None and bom[f] > 0
        )
    ]
    res["match_1780_1830"]["all_features"] = {"n": len(every), "ids": [r["work_id"] for r in every]}
    res["match_1780_1830"]["features_at_or_above_histogram"] = dict(
        sorted(
            Counter(
                sum(
                    1
                    for f in FEATURES
                    if bom[f] is not None and r["rates"][f] is not None and r["rates"][f] >= bom[f]
                )
                for r in late
            ).items()
        )
    )
    top = sorted(
        (r for r in late if r["rates"]["did_rate"] is not None),
        key=lambda r: -r["rates"]["did_rate"],
    )[:20]
    res["top20_1780_1830_did_rate"] = [
        {"work_id": r["work_id"], "year": r["year"], "did_rate": r["rates"]["did_rate"],
         "did_per10k": r["rates"]["did_per10k"], "did": did_n(r), "past": r["past"]}
        for r in top
    ]  # fmt: skip
    # Outside everything after 1700?
    lo, hi = e["after_years"]
    after = [r for r in ok if lo <= r["year"] <= hi and r["rates"][key] is not None]
    reach = [r for r in after if r["rates"][key] >= bom[key]]
    rows_out = []
    judged = reprint_judgments()
    for r in sorted(reach, key=lambda r: -r["rates"][key]):
        a = (cat.get(r["work_id"]) or {}).get("author")
        rows_out.append(
            {
                "work_id": r["work_id"],
                "year": r["year"],
                key: r["rates"][key],
                "did": did_n(r),
                "past": r["past"],
                "words": r["words"],
                "genre": r["genre"],
                "pre1700_author": pre1700_author(a, cfg),
                "title_judgment": judged.get(r["work_id"], {}).get("kind", "not judged"),
                "bible_style_list": r["work_id"] in controls,
                "translation_mark": r["work_id"] in trans,
            }  # fmt: skip
        )
    later = [
        x
        for x in rows_out
        if not x["pre1700_author"] and judged.get(x["work_id"], {}).get("reprint") is not True
    ]
    res["after_1700"] = {
        "measure": key,
        "works": len(after),
        "reach_bom": len(rows_out),
        "reach_bom_not_reprint": len(later),
        "by_genre": dict(Counter(x["genre"] for x in later).most_common()),
        "translation_marked": sum(x["translation_mark"] for x in later),
        "works_reaching": rows_out[:200],
    }
    res["after_1700"]["outside_everything_after_1700"] = len(later) == 0
    if key == "did_rate":  # the per-10,000 count beside it
        p10 = [
            r for r in ok if lo <= r["year"] <= hi and r["rates"]["did_per10k"] >= bom["did_per10k"]
        ]
        res["after_1700"]["reach_bom_per10k"] = len(p10)
    # Controls inside the library: the study's Bible-style list, translations, sermons.
    groups = {
        "bible_style_list": [r for r in ok if r["work_id"] in controls],
        "translation_marked_1780_1830": [r for r in late if r["work_id"] in trans],
        "sermons_1780_1830": [r for r in late if (r["genre"] or "").startswith("sermon")],
    }
    res["groups"] = {
        g: {
            "n": len(rs),
            **{f: _place(bom[f], [r["rates"][f] for r in rs]) for f in FEATURES},
            "at_or_above_did_rate": [
                r["work_id"] for r in rs if (r["rates"]["did_rate"] or 0) >= (bom["did_rate"] or 9)
            ],
        }
        for g, rs in groups.items()
    }  # fmt: skip
    res["groups"]["bible_style_list"]["works"] = [
        {"work_id": r["work_id"], "year": r["year"], **{f: r["rates"][f] for f in FEATURES[:2]}}
        for r in groups["bible_style_list"]
    ]
    return res


def _place(target: float | None, values: list[float | None]) -> dict:
    vs = [v for v in values if v is not None]
    if target is None or not vs:
        return {"n": len(vs), "at_or_above": None, "percentile": None}
    above = sum(1 for v in vs if v >= target)
    return {
        "n": len(vs),
        "at_or_above": above,
        "percentile": round(100 * sum(1 for v in vs if v < target) / len(vs), 2),
        "median": _median(vs),
    }


def _at_or_above(bom: dict, rows: list[dict], f: str) -> dict:
    vs = [r for r in rows if r["rates"][f] is not None]
    if bom[f] is None:
        return {"with_data": len(vs), "at_or_above": None}
    hit = [r for r in vs if r["rates"][f] >= bom[f]]
    return {"bom": bom[f], "with_data": len(vs), "at_or_above": len(hit)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["lexicon", "check", "pass", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "lexicon":
        r = build_lexicon(cfg)
        print({"works_read": r["works_read"], "verbs": len(r["verbs"])})
        return 0
    if a.cmd == "check":
        r = check(cfg)
        r["config_sha256"] = config.sha256_of_config()
        out(WORK / "check.json").write_text(json.dumps(r, indent=1) + "\n")
        print(json.dumps(r, indent=1))
        return 0
    if a.cmd == "pass":
        return library_pass(cfg)
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    short = {k: v for k, v in res.items() if k not in ("named", "library", "settings")}
    print(json.dumps(short, indent=1))
    if "library" in res:
        print(json.dumps({k: v for k, v in res["library"].items() if k != "after_1700"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
