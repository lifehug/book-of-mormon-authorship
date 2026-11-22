"""BOM-109, second design: where three worlds disagree, read as attributed mentions.

The first design (``lab.threeworlds``) credited a feature when its word occurred; its known-answer
check missed because Bernal Diaz's horses, guns and coins are the Spaniards', not the Aztecs'.
Here a reader ties each mention to a people. Marker words (``lab.threeworlds2_features``, with
the long-s repair of ``lab.inventory``) find candidate mentions; at most ``sample_per_feature`` per
feature and text are drawn by seed; the model judge (``lab.judge``; **simulated judging by an AI
model**) answers for each: *whose* (the text's own people / outsiders in the story / the author's
or translator's world / a figure or a quotation / a prophecy / nobody), *what* (have / lack /
brought from outside / says neither / the word means something else) and *where* (main setting /
elsewhere / cannot tell). A text states a feature present with ``present_min_attr`` own-people
"have" mentions in the main setting; absent when it says they lack it, or when it is long, talks
about the topic and never gives this item. Each world's value is the majority of each standpoint
row (native, outsider eyewitness, outsider from books; for the 1820s picture four strata, one of
them drawn by rule from the library and one from newspapers), rows pooled with equal weight.
Texts side with the world they agree with most on the features where the three ancient worlds
disagree (a fourth column, the writers' own day, catches modern things).

Known answers first: the judge on 150 made-up passages and 100 real mentions read twice; then
eight known texts, **Bernal Diaz among them**. The Book of Mormon is scored only if every check
passes. Part B dates, in the library, the earliest print of each Mesoamerican and 1820s feature
said of ancient Americans. Card: ``data/private/lab/owner/2026-11-22-three-worlds-redesign/
card.md``; settings ``lab.three_worlds2``. Results hold names, references and numbers; jobs and
mentions (which quote passages) are private or local.

Usage::

    python -m lab.threeworlds2 texts        # load every text; rule-drawn sets; word counts (10 min)
    python -m lab.threeworlds2 mentions     # candidate mentions and samples per text (5 min)
    python -m lab.threeworlds2 partb-scan   # Part B: earliest library hits per feature (1-2 h)
    python -m lab.threeworlds2 jobs         # judge jobs, check first (private); sizes (1 min)
    python -m lab.threeworlds2 dev          # the scoring on hand-made answers (seconds)
    python -m lab.threeworlds2 check        # judge check, then the known texts (from answers)
    python -m lab.threeworlds2 run          # the checks, then (only if passed) the book and Part B
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq

from lab import door
from lab import inventory as inv
from lab import threeworlds2_features as feat
from lab.numbers import CAND, KJV, SRC, _file, _library, gutenberg
from lab.paths import FAST, LOGS, NOTES, REGISTRY, out
from lab.wherefore import QUOTED
from metadata import config

OUT = REGISTRY / "setting" / "three_worlds2"
CARD = NOTES / "owner" / "2026-11-22-three-worlds-redesign"
CACHE = FAST / "three_worlds2"
PARSE_LOG = LOGS / "threeworlds2_parse_failures.jsonl"
DPLACE_DIR = SRC / "setting" / "dplace_sccs" / "cldf"
DALE_ITEMS = REGISTRY / "setting" / "dale_checklist" / "items.json"
ROPER_ITEMS = REGISTRY / "setting" / "anachronisms" / "items.json"
EDITION = Path("data/bom/1830/edition_1830.jsonl")
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
NE, MS, AM, CT = feat.WORLDS
ANCIENT = feat.ANCIENT
SIMULATED = "SIMULATED JUDGING BY AN AI MODEL (lab.judge; BOM-109 second design)"
JOB_FILES = ("check", "subject", "known", "reference", "rule", "control", "book", "partb")
WHOSE = {"S": "own", "O": "outsiders", "A": "author", "F": "figure", "P": "future", "N": "nobody"}
WHAT = {"H": "have", "L": "lack", "B": "brought", "X": "neither", "W": "other_sense"}
WHERE = {"M": "main", "E": "elsewhere", "U": "unclear"}
STRATA = {"A": "s_antiquities", "B": "s_origins", "C": "s_fiction", "D": "s_contemporary_indians",
          "E": None}  # fmt: skip


def settings(cfg: dict) -> dict:
    return cfg["lab"]["three_worlds2"]


# ------------------------------------------------------------------------------ markers


def compile_markers() -> dict[str, list[tuple[tuple[str, ...], str]]]:
    """feature -> [(lower-case word tuple, case rule)]; '_' lower case only."""
    res = {}
    for fid, (_l, _t, _k, markers, _p) in feat.FEATURES.items():
        rows = []
        for tok in markers.split():
            case = ""
            if tok.endswith("_"):
                case, tok = "_", tok[:-1]
            parts = [p for p in re.split("[_-]", tok) if p]
            rows.append((tuple(p.lower() for p in parts), case))
        res[fid] = rows
    return res


MARKERS = compile_markers()
_BY_FIRST: dict[str, list[tuple[str, tuple[str, ...], str]]] = defaultdict(list)
for _fid, _rows in MARKERS.items():
    for _w, _c in _rows:
        _BY_FIRST[_w[0]].append((_fid, _w, _c))


def markers_sha() -> str:
    body = json.dumps({k: v[3] for k, v in feat.FEATURES.items()}, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def clean(text: str) -> str:
    """Long s read as s and words broken at a line end joined (as ``lab.inventory``)."""
    return inv.JOINED.sub(r"\1\2", text.replace(chr(0x17F), "s"))


def find_markers(text: str) -> tuple[list[tuple[int, int]], list[tuple[str, int, int]]]:
    """(token spans, [(feature, first token, last token + 1)]) on a cleaned text; tokens are read
    through the long-s repair; a phrase matches whole."""
    spans, low, raw = [], [], []
    for m in inv.TOKEN.finditer(text):
        spans.append((m.start(), m.end()))
        w = inv.repair(m.group())
        raw.append(w)
        low.append(w.lower())
    hits = []
    for i, w in enumerate(low):
        for fid, words, case in _BY_FIRST.get(w, ()):
            if tuple(low[i : i + len(words)]) != words:
                continue
            if case == "_" and not raw[i].islower():
                continue
            hits.append((fid, i, i + len(words)))
    return spans, hits


def passage(text: str, spans: list[tuple[int, int]], a: int, b: int, k: int) -> str:
    """The words ``k`` either side of tokens a..b, the mention marked with brackets, long s
    repaired, whitespace collapsed."""
    lo = spans[max(0, a - k)][0]
    hi = spans[min(len(spans) - 1, b - 1 + k)][1]
    s0, s1 = spans[a][0], spans[b - 1][1]

    def fix(s: str) -> str:
        return " ".join(inv.TOKEN.sub(lambda m: inv.repair(m.group()), s).split())

    return f"{fix(text[lo:s0])} [[{fix(text[s0:s1])}]] {fix(text[s1:hi])}".strip()


# ------------------------------------------------------------------------------ texts

ROMAN = "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII".split()


def bom_units() -> list[tuple[str, str]]:
    """(reference, text) per body paragraph; the reference is "book chapter(1830) para seq" and
    a trailing " Q" marks the chapters that quote the Bible (``lab.wherefore.QUOTED``)."""
    labels = {r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines())}
    res = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if r["kind"] != "body" or lab is None:
            continue
        ch = lab["chapter_1830"]
        roman = ROMAN[ch - 1] if 0 < ch <= len(ROMAN) else str(ch)
        q = " Q" if (r["book"], ch) in QUOTED else ""
        res.append((f"{r['book']} {roman} para {r['seq']}{q}", r["text"]))
    return res


def _kjv(codes: list[str]) -> list[tuple[str, str]] | None:
    raw = _file(KJV)
    if raw is None:
        return None
    rows = [json.loads(x) for x in raw.splitlines()]
    got = [(r["ref"], r["text"]) for r in rows if r["book"] in set(codes)]
    return got or None


def _dictated(which: str, cfg: dict) -> str | None:
    from lab import dictations as dic

    try:
        if which == "abraham":
            rows = dic._pages(dic.DICTATED / "abraham_1842" / "pages.jsonl")
        else:
            a, b = cfg["lab"]["dictations"]["moses_pages"]
            rows = [r for r in dic._pages(dic.DICTATED / "ot_revision_1" / "pages.jsonl")
                    if dic._page_no(r) is not None and a <= dic._page_no(r) <= b]  # fmt: skip
    except OSError:
        return None
    return dic.strip_editorial("\n".join(r["text"] for r in rows)) or None


_NAMED: dict[str, str | None] = {}


def _named(cfg: dict) -> dict[str, str | None]:
    if not _NAMED:
        _NAMED.update({n: t for n, _w, _r, t in inv.prepare(cfg)})
    return _NAMED


def _lib(work_id: str) -> str | None:
    row = door.catalog({work_id}).get(work_id)
    return None if row is None or not row.get("text_path") else _library(row)


def load(source: str, cfg: dict) -> list[tuple[str | None, str]] | None:
    """Segments (reference or None, text) of one source string from the config; None if not
    held (never an empty text)."""
    kind, _, arg = source.partition(":")
    one: str | None
    if kind == "kjv":
        return _kjv(arg.split(","))
    if kind == "bom":
        return bom_units()  # type: ignore[return-value]
    if kind == "inv":
        one = _named(cfg).get(arg)
    elif kind == "bilingual":
        _named(cfg)
        if arg == "maya":
            one = inv._bilingual(
                "brinton_maya_chronicles_1882.txt",
                r"TRANSLATION\.|CONQUEST AND MAP\.",
                r"NOTES\.|VOCABULARY\.",
                cfg,
            )
        else:
            one = inv._bilingual("brinton_rig_veda_americanus_1890.txt",
                                 r"_Translation\._|_(The )?(Hymn|War Song|Song) .*\._",
                                 r"_Notes\._|GLOSSARY\.", cfg)  # fmt: skip
    elif kind == "lib":
        one = _lib(arg)
    elif kind == "cand":
        one = _file(CAND / arg)
    elif kind == "pg":
        raw = _file(SRC / arg)
        one = None if raw is None else gutenberg(raw)
    elif kind == "lab":
        one = _file(FAST / arg)
    elif kind == "atwater":
        from lab import warfare

        one = warfare._atwater()
    elif kind in ("abraham", "moses"):
        one = _dictated(kind, cfg)
    elif kind == "page":
        return None  # newspaper windows are built by ``newspaper_set``
    else:
        raise ValueError(f"unknown source {source}")
    return None if not one or not one.strip() else [(None, one)]


def _registry() -> list[dict]:
    return pq.read_table(REGISTRY / "registry.parquet").to_pylist()


def copy_key(author: str | None, title: str | None) -> str:
    """Copies collapse on the author's surname and the first four title words."""
    sur = re.sub("[^a-z]", "", (author or "anon").split(",")[0].lower())[:20]
    words = re.findall("[a-z]+", (title or "").lower())
    words = [w for w in words if w not in {"the", "a", "an", "of", "or", "and", "on"}][:4]
    return sur + "|" + " ".join(words)


# Named texts loaded from the setting sources (not by library id) and known texts: their library
# copies are left out of the rule-drawn set. (author surname, title word)
NAMED_ELSEWHERE = (("clinton", "discourse"), ("clinton", "western"), ("adair", "indians"),
                   ("hale", "oblivion"), ("seaver", "jemison"), ("smith", "hebrews"),
                   ("mathews", "behemoth"), ("humboldt", "researches"), ("atwater", "antiquities"),
                   ("robertson", "america"), ("priest", "antiquities"))  # fmt: skip


def rule_candidates(cfg: dict, reg: list[dict] | None = None) -> list[dict]:
    """Library works 1775-1829 whose title names America (or its natives) and an ancient or
    origins topic; one copy (the longest) per author and title; the card's named works, the
    known texts and copies of them left out. Each still needs the subject question."""
    s = settings(cfg)
    reg = reg if reg is not None else _registry()
    lo, hi = s["rule_years"]
    place = re.compile(s["rule_title_place"], re.I)
    topic = re.compile(s["rule_title_topic"], re.I)
    rows = [r for r in reg if r["kind"] == "work" and r["has_text"] and r["dup_keeper"]
            and not r["sealed"] and not r["ocr_excluded"] and r["year"] and lo <= r["year"] <= hi
            and (r["words"] or 0) >= s["rule_min_words"]
            and "newspaper" not in (r["genre"] or "")]  # fmt: skip
    cat = door.catalog({r["work_id"] for r in rows})
    named_ids = {v[3][4:] for v in s["texts"].values() if v[3].startswith("lib:")}
    named_keys = {copy_key(cat[i]["author"], cat[i]["title"]) for i in named_ids if i in cat}
    best: dict[str, dict] = {}
    for r in rows:
        c = cat.get(r["work_id"])
        if c is None or not c.get("text_path"):
            continue
        t = c["title"] or ""
        if not (place.search(t) and topic.search(t)):
            continue
        key = copy_key(c["author"], t)
        sur = key.split("|")[0]
        if r["work_id"] in named_ids or key in named_keys:
            continue
        if any(sur == a and w in t.lower() for a, w in NAMED_ELSEWHERE):
            continue  # a named text held outside the library ids, or a known text
        if key not in best or (r["words"] or 0) > (best[key]["words"] or 0):
            best[key] = {**r, "title": t, "author": c["author"], "key": key}
    return sorted(best.values(), key=lambda r: (r["year"], r["work_id"]))


def newspaper_set(cfg: dict, reg: list[dict] | None = None) -> list[dict]:
    """Chronicling America pages of the years with at least ``newspaper_min_terms`` antiquities
    terms; ``newspaper_pages`` drawn by seed; each keeps the stretch of words around its hits."""
    s = settings(cfg)
    path = CACHE / "newspapers.json"
    key = hashlib.sha256(json.dumps([s["newspaper_years"], s["newspaper_terms"],
                                     s["newspaper_min_terms"], s["newspaper_pages"],
                                     s["newspaper_window_words"], s["seed"]]).encode()
                         ).hexdigest()[:16]  # fmt: skip
    if path.exists():
        got = json.loads(path.read_text())
        if got.get("key") == key:
            return got["pages"]
    reg = reg if reg is not None else _registry()
    lo, hi = s["newspaper_years"]
    rows = [r for r in reg if r["kind"] == "newspaper_page" and r["has_text"] and r["year"]
            and lo <= r["year"] <= hi and not r["ocr_excluded"]]  # fmt: skip
    cat = door.catalog({r["work_id"] for r in rows})
    terms = re.compile(s["newspaper_terms"], re.I)
    qualify = []
    for r in rows:
        c = cat.get(r["work_id"])
        if c is None or not c.get("text_path"):
            continue
        t = _library({**c, **r})
        if t and len(terms.findall(t)) >= s["newspaper_min_terms"]:
            qualify.append(r["work_id"])
    qualify.sort()
    pick = sorted(random.Random(s["seed"]).sample(qualify, min(s["newspaper_pages"],
                                                               len(qualify))))  # fmt: skip
    pages = []
    half = s["newspaper_window_words"] // 2
    for wid in pick:
        c = cat[wid]
        t = clean(_library(c) or "")
        toks = list(re.finditer(r"\S+", t))
        hits = [i for i, m in enumerate(toks) if terms.search(m.group())]
        mid = hits[len(hits) // 2] if hits else len(toks) // 2
        a, b = max(0, mid - half), min(len(toks), mid + half)
        pages.append(
            {
                "work_id": wid,
                "year": next(r["year"] for r in rows if r["work_id"] == wid),
                "char": [toks[a].start(), toks[b - 1].end()] if toks else [0, 0],
            }
        )
    out(path).write_text(json.dumps({"key": key, "qualifying": len(qualify), "pages": pages}))
    return pages


def contemporary_set(cfg: dict, reg: list[dict] | None = None,
                     exclude: set[str] | None = None) -> list[dict]:  # fmt: skip
    """The contemporary column: history works 1800-1829 whose title names an American place and
    no ancient topic; one copy per author and title; ``contemporary_n`` drawn by seed."""
    s = settings(cfg)
    reg = reg if reg is not None else _registry()
    lo, hi = s["contemporary_years"]
    wlo, whi = s["contemporary_words"]
    place = re.compile(s["contemporary_title_place"], re.I)
    topic = re.compile(s["rule_title_topic"], re.I)
    rows = [r for r in reg if r["kind"] == "work" and r["has_text"] and r["dup_keeper"]
            and not r["sealed"] and not r["ocr_excluded"] and r["year"] and lo <= r["year"] <= hi
            and wlo <= (r["words"] or 0) <= whi
            and (r["genre"] or "").split(",")[0] == s["contemporary_genre"]]  # fmt: skip
    cat = door.catalog({r["work_id"] for r in rows})
    best: dict[str, dict] = {}
    for r in rows:
        c = cat.get(r["work_id"])
        if c is None or not c.get("text_path") or r["work_id"] in (exclude or set()):
            continue
        t = c["title"] or ""
        if not place.search(t) or topic.search(t):
            continue
        key = copy_key(c["author"], t)
        if any(key.split("|")[0] == a and w in t.lower() for a, w in NAMED_ELSEWHERE):
            continue  # a reference text of another world (Robertson)
        if key not in best or r["work_id"] < best[key]["work_id"]:
            best[key] = {**r, "title": t, "author": c["author"], "key": key}
    pool = sorted(best.values(), key=lambda r: r["work_id"])
    rng = random.Random(f"{s['seed']}-contemporary")
    return sorted(rng.sample(pool, min(s["contemporary_n"], len(pool))),
                  key=lambda r: r["work_id"])  # fmt: skip


def all_texts(cfg: dict, subject_answers: dict[str, str] | None = None) -> list[dict]:
    """Every text: name, role, world, row, source, subject label. The rule-drawn 1820s works
    enter only once their subject question is answered (A-D); the newspaper pages and the
    contemporary sample enter by rule."""
    s = settings(cfg)
    rows = [{"name": n, "role": v[0], "world": v[1], "row": v[2], "source": v[3],
             "subject": s["subjects"][v[4]]} for n, v in s["texts"].items()]  # fmt: skip
    for unit, codes in s["kjv_units"].items():
        rows.append(
            {
                "name": unit,
                "role": "reference",
                "world": NE,
                "row": "native",
                "source": "kjv:" + ",".join(codes),
                "subject": s["subjects"]["israel"],
            }
        )
    reg = _registry()
    for p in newspaper_set(cfg, reg):
        rows.append({"name": f"news|{p['work_id']}", "role": "reference", "world": AM,
                     "row": "s_newspapers", "source": "page:" + p["work_id"],
                     "subject": s["subjects"]["ancient_america"], "char": p["char"]})  # fmt: skip
    cands = rule_candidates(cfg, reg)
    for c in contemporary_set(cfg, reg, {c["work_id"] for c in cands}):
        rows.append({"name": f"contemp|{c['work_id']}", "role": "reference", "world": CT,
                     "row": "sample", "source": "lib:" + c["work_id"],
                     "subject": s["subjects"]["contemporary"]})  # fmt: skip
    for c in cands:
        ans = (subject_answers or {}).get(f"subject|{c['work_id']}")
        stratum = STRATA.get(ans) if ans else None
        rows.append({"name": f"rule|{c['work_id']}", "role": "rule", "world": AM,
                     "row": stratum, "source": "lib:" + c["work_id"],
                     "subject": s["subjects"]["indians_now" if ans == "D" else "ancient_america"],
                     "subject_answer": ans})  # fmt: skip
    return rows


def segments_of(t: dict, cfg: dict) -> list[tuple[str | None, str]] | None:
    if t["source"].startswith("page:"):
        wid = t["source"][5:]
        raw = _lib(wid)
        if raw is None:
            return None
        a, b = t["char"]
        return [(None, clean(raw)[a:b])]
    return load(t["source"], cfg)


# ------------------------------------------------------------------------------ mentions


def mentions_of(name: str, segs: list[tuple[str | None, str]], cfg: dict) -> dict:
    """Every marker hit of a text and a seeded sample of at most ``sample_per_feature`` per
    feature, each with its passage. Cached by markers, text and settings (local disk)."""
    s = settings(cfg)
    h = hashlib.sha256()
    for ref, t in segs:
        h.update(f"{ref}\x00{t}\x01".encode())
    key = hashlib.sha256((markers_sha() + h.hexdigest() + str(len(inv.VOCAB))
                          + str([s["sample_per_feature"], s["context_words"], s["seed"]])
                          ).encode()).hexdigest()[:20]  # fmt: skip
    path = CACHE / "mentions" / f"{re.sub('[^A-Za-z0-9_.-]', '_', name)[:90]}-{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    text_parts, starts, refs = [], [], []
    pos = 0
    for ref, t in segs:
        c = clean(t)
        starts.append(pos)
        refs.append(ref)
        text_parts.append(c)
        pos += len(c) + 1
    text = "\n".join(text_parts)
    spans, hits = find_markers(text)
    by: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for fid, a, b in hits:
        by[fid].append((a, b))
    import bisect

    sample = []
    for fid in feat.FEATURES:
        occ = by.get(fid, [])
        rng = random.Random(f"{s['seed']}|{name}|{fid}")
        pick = sorted(rng.sample(range(len(occ)), min(len(occ), s["sample_per_feature"])))
        for n, i in enumerate(pick):
            a, b = occ[i]
            seg = bisect.bisect_right(starts, spans[a][0]) - 1
            sample.append({"id": f"{name}|{fid}|{n}", "feature": fid, "ref": refs[seg],
                           "char": spans[a][0],
                           "passage": passage(text, spans, a, b, s["context_words"])})  # fmt: skip
    res = {"name": name, "words": len(spans), "hits": {f: len(v) for f, v in by.items()},
           "sample": sample}  # fmt: skip
    out(path).write_text(json.dumps(res))
    return res


# ------------------------------------------------------------------------------ prompts

PROMPT = """You are helping a study read old books. Your answer is recorded as simulated judging \
by an AI model.

The book is about: {subject}.
Feature: {label}.
In the passage below, the words in double brackets [[like this]] are the mention to judge.

Passage:
{passage}

Answer three questions about the bracketed mention only.
1. WHOSE is it in this passage?
   S = the people the book is about (as named above)
   O = other people in the story (strangers, invaders, conquerors, neighbours, traders)
   A = the author's, translator's or reader's own world (a comparison, an explanation, a note)
   F = a figure of speech, or words quoted from another book
   P = a prophecy, a promise, a wish, or something in the future
   N = nobody: the passage does not give it to any people
2. WHAT does the passage say about it?
   H = they have, make or use it
   L = they lack it (the passage says they had none, or did not know it)
   B = it was brought to them from outside (by others, from another land)
   X = the passage says none of these
   W = the bracketed word does not mean the feature here (another sense of the word)
3. WHERE is the scene?
   M = in the land where the book's main story takes place
   E = somewhere else (another land, or before a journey to the main land)
   U = cannot tell

Reply with one line and nothing else: the three letters separated by commas, for example S,H,M"""

PROMPT_2 = """A study of old books needs a second, independent reading of one passage. Your \
answer is recorded as simulated judging by an AI model.

The passage marks one word or phrase between double brackets [[ ]]. The study wants to know \
whether the book gives the thing it names ({label}) to its own people, who are: {subject}.

{passage}

Give three words, in this order, separated by spaces:
- OWNER: people (the book's own people have it), others (other people in the story), author \
(the writer's or translator's own world, a comparison or explanation), figure (a figure of \
speech or a quotation), future (a prophecy or something to come), nobody
- STATE: has (they have or use it), lacks (they do not have it), brought (brought to them from \
outside), neither, othersense (the word means something else here)
- PLACE: main (the main land of the story), elsewhere, unclear

Example answer: others has main"""

SUBJECT_PROMPT = """You are sorting books for a study. Your answer is recorded as simulated \
judging by an AI model.

Title: {title}
Opening words:
{opening}

What is this book mainly about?
A = the ancient inhabitants of America: antiquities, mounds, old forts, ruins, ancient nations
B = where the American Indians came from (the Lost Tribes of Israel, migrations from the Old \
World)
C = a story or a poem about ancient America or its first peoples
D = the Indians of the author's own time (manners, missions, wars, treaties, captivity, travel)
E = something else

Reply with one letter."""

PARTB_PROMPT = """You are helping a study date when ideas first appeared in print. Your answer is \
recorded as simulated judging by an AI model.

Passage (printed in {year}; the bracketed words are the place to look):
{passage}

Does this passage say that the ancient inhabitants of America (before Europeans came) had, made \
or used {label}?
Y = yes, it says so of the ancient or native inhabitants of America
N = no (it says they lacked it, or it is about other people, or it does not say)

Reply with one letter."""


# ------------------------------------------------------------------------------ the judge check

SYN_THINGS = [
    ("horses", "horses"), ("iron_steel", "iron tools"), ("maize", "maize"),
    ("cotton", "cotton cloth"), ("canoes", "canoes"), ("feathers", "feathered cloaks"),
    ("wheat_barley", "wheat"), ("coins", "coined money"), ("firearms", "muskets"),
    ("mounds", "great earthen mounds"), ("chariots", "chariots"), ("cacao", "cacao"),
    ("swine", "swine"), ("plough", "ploughs"), ("silk_linen", "silk"),
]  # fmt: skip
SYN_PEOPLE = ["the Ondari", "the people of Kesh", "the Tuvani", "the children of Amrel",
              "the Halosi"]  # fmt: skip
SYN_OUTSIDERS = ["the Velish strangers", "the men of the eastern ships",
                 "the soldiers of the foreign captain"]  # fmt: skip
# frame: (template, whose, what, where)
SYN_FRAMES = {
    "have": ("In those days {P} had [[{T}]] in all their towns, and they made great use of "
             "them, and every family counted them among its goods.", "S", "H", "M"),
    "lack": ("Now {P} had no [[{T}]] at all; such a thing was never known among them in all "
             "the land, from the mountains to the sea.", "S", "L", "M"),
    "outsiders": ("Then {O} marched into the land of {P}, bringing with them [[{T}]], and "
                  "{P} fled from their towns at the sight of the strangers.", "O", "H", "M"),
    "brought": ("After the coming of {O}, [[{T}]] were given to {P}, who had never had any "
                "before, and within a few years {P} used them in every town.", "S", "B", "M"),
    "figure": ("The singer of {P} said that the stars of the night were scattered over the "
               "heavens like [[{T}]] over a market floor, as the old saying goes.", "F", "X",
               "M"),
    "author": ("Their great house of council was larger than any building in our own country "
               "where we keep [[{T}]], says the writer of this history in a note.", "A", "X",
               "M"),
    "future": ("Their seer foretold that in a later age strangers would come over the sea and "
               "bring [[{T}]] into the land of {P}.", "P", "X", "M"),
    "elsewhere": ("Long before they crossed the great water, while they still dwelt in the old "
                  "land far to the east, the fathers of {P} kept [[{T}]] in their fields.",
                  "S", "H", "E"),
    "quoted": ("And the priest of {P} read to them from the book of another nation, which "
               "says: 'the king of that country gathered [[{T}]] without number.'", "F", "X",
               "M"),
    "nobody": ("A list of words in an unknown tongue was found carved on a stone near the "
               "river, and one of the words is thought to mean [[{T}]].", "N", "X", "M"),
}  # fmt: skip


def synthetic(cfg: dict) -> list[dict]:
    """The made-up passages: every thing in every frame, people drawn by seed; known answers."""
    s = settings(cfg)
    rng = random.Random(f"{s['seed']}-synthetic")
    rows = []
    for fid, thing in SYN_THINGS:
        for frame, (tpl, whose, what, where) in SYN_FRAMES.items():
            p = rng.choice(SYN_PEOPLE)
            o = rng.choice(SYN_OUTSIDERS)
            text = tpl.format(P=p, O=o, T=thing)
            text = text[0].upper() + text[1:]
            rows.append({"id": f"syn|{fid}|{frame}", "feature": fid, "frame": frame,
                         "subject": p, "passage": text,
                         "key": {"whose": whose, "what": what, "where": where}})  # fmt: skip
    return rows[: s["synthetic_n"]]


def prompt_first(label: str, subject: str, text: str) -> str:
    return PROMPT.format(subject=subject, label=label, passage=text)


def prompt_second(label: str, subject: str, text: str) -> str:
    return PROMPT_2.format(subject=subject, label=label, passage=text)


# ------------------------------------------------------------------------------ parsing

_W2 = {"people": "S", "others": "O", "author": "A", "figure": "F", "future": "P", "nobody": "N"}
_S2 = {"has": "H", "lacks": "L", "brought": "B", "neither": "X", "othersense": "W"}
_P2 = {"main": "M", "elsewhere": "E", "unclear": "U"}


def parse_first(reply: str) -> tuple[str, str, str] | None:
    m = re.search(r"\b([SOAFPN])\s*,\s*([HLBXW])\s*,\s*([MEU])\b", reply.upper())
    return (m.group(1), m.group(2), m.group(3)) if m else None


def parse_second(reply: str) -> tuple[str, str, str] | None:
    words = [w for w in re.findall(r"[a-z]+", reply.lower().replace("other sense", "othersense"))
             if w not in ("owner", "state", "place")]  # fmt: skip
    for i in range(len(words) - 2):
        a, b, c = words[i : i + 3]
        if a in _W2 and b in _S2 and c in _P2:
            return _W2[a], _S2[b], _P2[c]
    return None


def parse_letter(reply: str, allowed: str) -> str | None:
    m = re.match(rf"\s*\**\s*([{allowed}])\b", reply.strip().upper())
    return m.group(1) if m else None


def load_answers(paths: list[Path]) -> dict[str, str]:
    got: dict[str, str] = {}
    for p in paths:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    got[r["id"]] = r["reply"]
    return got


def log_unparsed(job_id: str, reply: str) -> None:
    with out(PARSE_LOG).open("a") as fh:
        fh.write(json.dumps({"id": job_id, "reply": reply}) + "\n")


def readings(ids: list[str], answers: dict[str, str], second: bool = False,
             log: bool = True) -> tuple[dict[str, tuple[str, str, str]], dict]:  # fmt: skip
    """Parsed answers for the ids; unanswered and unparseable stay open (never read as "no")."""
    got, n_open, n_bad = {}, 0, 0
    for i in ids:
        key = i + "#2" if second else i
        if key not in answers:
            n_open += 1
            continue
        p = (parse_second if second else parse_first)(answers[key])
        if p is None:
            n_bad += 1
            if log:
                log_unparsed(key, answers[key])
            continue
        got[i] = p
    return got, {"asked": len(ids), "answered": len(got), "open": n_open, "unparseable": n_bad}


# ------------------------------------------------------------------------------ scoring


def counts_main(p: tuple[str, str, str], s: dict) -> bool:
    return p[2] == "M" or (p[2] == "U" and s["count_unclear_place"])


def stated(mentions: list[dict], parsed: dict[str, tuple[str, str, str]], words: int,
           s: dict, place: str = "main") -> dict[str, str]:  # fmt: skip
    """present / absent / not stated per feature, from the parsed answers of one text's mentions.
    ``place`` "main" counts main-setting (and, by setting, unclear) mentions; "elsewhere" only
    those the judge put elsewhere (the Old World scenes, scored apart)."""
    have: Counter = Counter()
    lack: Counter = Counter()
    for m in mentions:
        p = parsed.get(m["id"])
        if p is None or p[0] != "S":
            continue
        here = counts_main(p, s) if place == "main" else p[2] == "E"
        if not here:
            continue
        if p[1] == "H":
            have[m["feature"]] += 1
        elif p[1] == "L":
            lack[m["feature"]] += 1
    topic_have: Counter = Counter()
    for fid, k in have.items():
        topic_have[feat.FEATURES[fid][1]] += k
    res = {}
    for fid, spec in feat.FEATURES.items():
        if have[fid] >= s["present_min_attr"]:
            res[fid] = "present"
        elif lack[fid] and not have[fid]:
            res[fid] = "absent"
        elif (have[fid] == 0 and words >= s["absent_min_words"]
              and topic_have[spec[1]] - have[fid] >= s["topic_min"]):  # fmt: skip
            res[fid] = "absent"
        else:
            res[fid] = "not stated"
    return res


def signature(mentions: list[dict], parsed: dict[str, tuple[str, str, str]]) -> dict:
    """Standpoint signature (description only): shares of the answered mentions by whose, and
    the share said to be brought from outside."""
    got = [parsed[m["id"]] for m in mentions if m["id"] in parsed]
    n = len(got)
    if not n:
        return {"answered": 0}
    whose = Counter(WHOSE[p[0]] for p in got)
    return {"answered": n, **{f"share_{k}": round(v / n, 4) for k, v in sorted(whose.items())},
            "share_brought": round(sum(p[1] == "B" for p in got) / n, 4),
            "share_other_sense": round(sum(p[1] == "W" for p in got) / n, 4),
            "share_elsewhere": round(sum(p[2] == "E" for p in got) / n, 4)}  # fmt: skip


def row_value(states: list[str], s: dict) -> tuple[str, int, int]:
    p, a = states.count("present"), states.count("absent")
    if p + a < s["world_min_stating"] or p == a:
        return "unsettled", p, a
    top, k = ("present", p) if p > a else ("absent", a)
    return (top if k / (p + a) >= s["world_majority"] else "unsettled"), p, a


def world_values(text_states: dict[str, dict[str, str]], rows: dict[str, tuple[str, str]],
                 cfg: dict) -> dict[str, dict]:  # fmt: skip
    """feature -> world -> {rows: {row: value, present, absent}, value (pooled)}. Rows of a world
    pool with equal weight: each row's share of present among its stating texts, averaged over
    the rows with any stating text; settled with ``world_min_stating`` texts in all and that
    average at ``world_majority`` or more either way."""
    s = settings(cfg)
    res: dict[str, dict] = {}
    for fid in feat.FEATURES:
        res[fid] = {}
        for world, pooled_rows in s["rows_pooled"].items():
            per = {}
            shares, total = [], 0
            all_rows = sorted({r for _n, (w, r) in rows.items() if w == world and r})
            for row in all_rows:
                sts = [text_states[n][fid] for n, (w, r) in rows.items()
                       if w == world and r == row and n in text_states]  # fmt: skip
                v, p, a = row_value(sts, s)
                per[row] = {"value": v, "present": p, "absent": a, "texts": len(sts),
                            "pooled": row in pooled_rows}  # fmt: skip
                if row in pooled_rows and p + a:
                    shares.append(p / (p + a))
                    total += p + a
            value = "unsettled"
            if total >= s["world_min_stating"] and shares:
                m = sum(shares) / len(shares)
                if m >= s["world_majority"] and m != 0.5:
                    value = "present"
                elif 1 - m >= s["world_majority"]:
                    value = "absent"
            res[fid][world] = {"value": value, "rows": per}
    return res


def kept_features(values: dict[str, dict]) -> tuple[list[str], dict[str, list[str]]]:
    """Features on which the three ancient worlds are settled and the settled worlds (the
    contemporary column included when settled) do not all agree. A feature only the writers' own
    day has (firearms) is kept when the contemporary column is settled on it."""
    keep, dropped = [], {"concordant": [], "unsettled": []}
    for fid, row in values.items():
        vals = [row[w]["value"] for w in ANCIENT]
        if row[CT]["value"] != "unsettled" and "unsettled" not in vals:
            vals.append(row[CT]["value"])
        if "unsettled" in vals:
            dropped["unsettled"].append(fid)
        elif len(set(vals)) == 1:
            dropped["concordant"].append(fid)
        else:
            keep.append(fid)
    return keep, dropped


def side(states: dict[str, str], keep: list[str], values: dict[str, dict], cfg: dict) -> dict:
    """Agreements of one text with each world over the kept features it states; sole agreements
    by the feature's kind; the leader; resample shares."""
    s = settings(cfg)
    agree = dict.fromkeys(feat.WORLDS, 0)
    sole = dict.fromkeys(feat.WORLDS, 0)
    sole_by_kind: dict[str, Counter] = defaultdict(Counter)
    per = {}
    for fid in keep:
        v = states.get(fid, "not stated")
        if v == "not stated":
            continue
        match = [w for w in feat.WORLDS if values[fid][w]["value"] == v]
        for w in match:
            agree[w] += 1
        if len(match) == 1:
            sole[match[0]] += 1
            sole_by_kind[match[0]][feat.FEATURES[fid][2]] += 1
        per[fid] = {"value": v, "agrees_with": match}
    top = max(agree.values()) if per else 0
    leaders = [w for w in feat.WORLDS if agree[w] == top] if per else []
    ranked = sorted(agree.values(), reverse=True)
    return {"stated": len(per), "agree": agree, "sole": sole,
            "sole_by_kind": {w: dict(c) for w, c in sole_by_kind.items()},
            "sides_with": leaders[0] if len(leaders) == 1 else "tie: " + "+".join(leaders),
            "lead": ranked[0] - ranked[1] if per else 0,
            "resample_lead_share": resample(per, s), "features": per}  # fmt: skip


def resample(per: dict[str, dict], s: dict) -> dict[str, float]:
    rows = [v["agrees_with"] for v in per.values()]
    if not rows:
        return {}
    rng = random.Random(s["seed"])
    lead: Counter = Counter()
    for _ in range(s["bootstrap"]):
        agree: Counter = Counter()
        for _k in range(len(rows)):
            agree.update(rng.choice(rows))
        top = max(agree[w] for w in feat.WORLDS)
        leaders = [w for w in feat.WORLDS if agree[w] == top]
        lead[leaders[0] if len(leaders) == 1 else "tie"] += 1
    return {k: round(v / s["bootstrap"], 4) for k, v in sorted(lead.items())}


def known_passes(name: str, own: str, sd: dict, s: dict) -> bool:
    if name == "gage_english_american_1648":  # later and mixed: it must beat the 1820s picture
        return sd["agree"][MS] > sd["agree"][AM]
    return (sd["sides_with"] == own and sd["lead"] >= s["margin"]
            and sd["resample_lead_share"].get(own, 0) >= s["known_resample_share"])  # fmt: skip


def composite(sd: dict, s: dict) -> list[str] | None:
    big = [w for w in feat.WORLDS if sd["sole"][w] >= s["composite_min"]]
    return big if len(big) >= 2 else None


def judge_check(jobs_meta: dict, answers: dict[str, str], cfg: dict) -> dict:
    """Bar (i): made-up passages right on whose and on what; real mentions, first and second
    reading agreeing on whose and on what."""
    s = settings(cfg)
    syn = jobs_meta["synthetic"]
    got, st = readings([r["id"] for r in syn], answers)
    right_whose = sum(got[r["id"]][0] == r["key"]["whose"] for r in syn if r["id"] in got)
    right_what = sum(got[r["id"]][1] == r["key"]["what"] for r in syn if r["id"] in got)
    by_frame: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in syn:
        if r["id"] in got:
            by_frame[r["frame"]][0] += got[r["id"]][0] == r["key"]["whose"]
            by_frame[r["frame"]][1] += 1
    real = jobs_meta["real_check"]
    first, st1 = readings(real, answers)
    second, st2 = readings(real, answers, second=True)
    both = [i for i in real if i in first and i in second]
    agree_whose = sum(first[i][0] == second[i][0] for i in both)
    agree_what = sum(first[i][1] == second[i][1] for i in both)
    complete = st["answered"] == len(syn) and len(both) == len(real)
    res = {
        "label": SIMULATED,
        "synthetic": {**st, "whose_right": right_whose, "what_right": right_what,
                      "whose_share": round(right_whose / st["answered"], 4) if st["answered"]
                      else None,
                      "what_share": round(right_what / st["answered"], 4) if st["answered"]
                      else None,
                      "whose_by_frame": {k: f"{a}/{b}" for k, (a, b) in sorted(by_frame.items())}},
        "real": {"first": st1, "second": st2, "both": len(both),
                 "whose_agree": round(agree_whose / len(both), 4) if both else None,
                 "what_agree": round(agree_what / len(both), 4) if both else None},
        "complete": complete,
    }  # fmt: skip
    syn_ok = (res["synthetic"]["whose_share"] or 0) >= s["judge_bar_whose"] and (
        res["synthetic"]["what_share"] or 0
    ) >= s["judge_bar_what"]
    real_ok = (res["real"]["whose_agree"] or 0) >= s["judge_bar_real"] and (
        res["real"]["what_agree"] or 0
    ) >= s["judge_bar_real"]
    res["passed"] = bool(complete and syn_ok and real_ok)
    return res


def score_texts(texts: list[dict], mentions: dict[str, dict], answers: dict[str, str],
                cfg: dict, log: bool = True) -> tuple[dict, dict, dict]:  # fmt: skip
    """(states per complete text, reading status per text, signature per text)."""
    s = settings(cfg)
    states, status, sig = {}, {}, {}
    for t in texts:
        m = mentions.get(t["name"])
        if m is None:
            status[t["name"]] = {"state": "not attempted (text not held)"}
            continue
        ids = [x["id"] for x in m["sample"]]
        parsed, st = readings(ids, answers, log=log)
        status[t["name"]] = st
        sig[t["name"]] = signature(m["sample"], parsed)
        if st["answered"] == st["asked"]:
            states[t["name"]] = stated(m["sample"], parsed, m["words"], s)
    return states, status, sig


def dplace_check(values: dict[str, dict]) -> dict:
    """Our pooled values for the Near East and Mesoamerica against D-PLACE's codes for the
    Hebrews and the Aztec where both exist; a mismatch is flagged, not changed."""
    path = DPLACE_DIR / "data.csv"
    if not path.exists():
        return {"state": "not attempted (D-PLACE SCCS not fetched)"}
    coded: dict[tuple[str, str], str] = {}
    with path.open() as fh:
        for r in csv.DictReader(fh):
            if r["Soc_ID"] in feat.DPLACE_SOCIETIES:
                coded[(r["Soc_ID"], r["Var_ID"])] = r["Value"]
    res = {}
    for fid, (var, mapping) in feat.DPLACE.items():
        for soc, world in feat.DPLACE_SOCIETIES.items():
            raw = coded.get((soc, var))
            want = mapping.get(raw or "")
            ours = values.get(fid, {}).get(world, {}).get("value")
            res[f"{fid}|{world}"] = {"variable": var, "society": soc, "coded": raw,
                                     "dplace": want, "ours": ours,
                                     "flag": bool(want and ours in ("present", "absent")
                                                  and want != ours)}  # fmt: skip
    return res


# ------------------------------------------------------------------------------ provenance


def check_provenance() -> dict:
    """Every provenance code resolves: Dale ids and Roper things exist in the keyed lists."""
    dale = {i["id"] for i in json.loads(DALE_ITEMS.read_text())["items"]}
    roper = {i.get("thing") for i in json.loads(ROPER_ITEMS.read_text())["items"]}
    from lab import threeworlds_features as v1

    bad = []
    for fid, spec in feat.FEATURES.items():
        for p in spec[4]:
            kind, _, arg = p.partition(":")
            ok = {"dale": arg in dale, "roper": arg in roper, "v1": arg in v1.RULE,
                  "coe1973": True, "vogel": arg in ("ch2", "ch3", "ch4"),
                  "dplace": fid in feat.DPLACE and feat.DPLACE[fid][0] == arg,
                  "bom111": arg.startswith("wp_")}.get(kind, False)  # fmt: skip
            if not ok:
                bad.append(f"{fid}:{p}")
    by_source = Counter(p.split(":")[0] for spec in feat.FEATURES.values() for p in spec[4])
    return {"features": len(feat.FEATURES), "unresolved": bad, "codes_by_source": dict(by_source),
            "by_kind": dict(Counter(v[2] for v in feat.FEATURES.values())),
            "by_topic": dict(Counter(v[1] for v in feat.FEATURES.values()))}  # fmt: skip


# ------------------------------------------------------------------------------ commands


def stamp(res: dict) -> dict:
    res["config_sha256"] = config.sha256_of_config()
    res["markers_sha256"] = markers_sha()
    try:
        res["git_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                           text=True, check=True).stdout.strip()  # fmt: skip
    except (OSError, subprocess.CalledProcessError):
        res["git_commit"] = None
    return res


def write(path: Path, res: dict) -> None:
    out(path).write_text(json.dumps(stamp(res), indent=1, default=str) + "\n")


def subject_answers() -> dict[str, str]:
    raw = load_answers([CARD / "answers_subject.jsonl"])
    got = {}
    for k, v in raw.items():
        p = parse_letter(v, "ABCDE")
        if p is None:
            log_unparsed(k, v)
        else:
            got[k] = p
    return got


def collect(cfg: dict) -> tuple[list[dict], dict[str, dict]]:
    """Every text (rule-drawn works with their subject answers) and its mentions (cached)."""
    texts = all_texts(cfg, subject_answers())
    _named(cfg)  # fixes the long-s vocabulary before any text is read
    ments: dict[str, dict] = {}
    for t in texts:
        segs = segments_of(t, cfg)
        if segs is not None:
            ments[t["name"]] = mentions_of(t["name"], segs, cfg)
    return texts, ments


def cmd_texts(cfg: dict) -> dict:
    texts, ments = collect(cfg)
    reg = {r["work_id"]: r for r in _registry()}
    res: dict = {"texts": {}, "not_attempted": []}
    for t in texts:
        m = ments.get(t["name"])
        if m is None:
            res["not_attempted"].append(t["name"])
            continue
        wid = t["source"].split(":", 1)[1] if t["source"][:4] in ("lib:", "page") else None
        res["texts"][t["name"]] = {
            "role": t["role"], "world": t["world"], "row": t["row"], "source": t["source"],
            "year": reg.get(wid, {}).get("year") if wid else None, "words": m["words"],
            "marker_hits": sum(m["hits"].values()), "sampled": len(m["sample"])}  # fmt: skip
    res["rule_drawn"] = {
        "candidates": sum(t["role"] == "rule" for t in texts),
        "candidate_words": sum(res["texts"][t["name"]]["words"] for t in texts
                               if t["role"] == "rule" and t["name"] in res["texts"]),
        "subject_answered": sum(bool(t.get("subject_answer")) for t in texts),
    }  # fmt: skip
    res["newspapers"] = json.loads((CACHE / "newspapers.json").read_text())["qualifying"]
    res["provenance"] = check_provenance()
    return res


def cmd_mentions(cfg: dict) -> dict:
    texts, ments = collect(cfg)
    per_feature: dict[str, dict] = {}
    for fid in feat.FEATURES:
        per_feature[fid] = {
            "texts_with_hits": sum(1 for m in ments.values() if m["hits"].get(fid)),
            "hits": sum(m["hits"].get(fid, 0) for n, m in ments.items() if n != "book_of_mormon"),
            "sampled": sum(1 for m in ments.values() for x in m["sample"] if x["feature"] == fid),
        }  # fmt: skip
    by_role: Counter = Counter()
    for t in texts:
        if t["name"] in ments:
            by_role[t["role"]] += len(ments[t["name"]]["sample"])
    return {"per_feature": per_feature, "sampled_by_role": dict(by_role),
            "note": "hits are counted for every text except the Book of Mormon, whose mentions "
                    "are only sampled for the judge (its counts are not scores)"}  # fmt: skip


def cmd_jobs(cfg: dict) -> dict:
    """Private jobs files. check: the judge's own check (made-up passages; real mentions of the
    known texts read in two formats); subject: the rule-drawn candidates; known; reference;
    rule (the candidates already answered A-D; the rest wait); control; book; partb (after
    ``partb-scan``). Sizes and hours at the queue's pace."""
    s = settings(cfg)
    texts, ments = collect(cfg)
    files: dict[str, list[dict]] = {k: [] for k in JOB_FILES}
    labels = {f: v[0] for f, v in feat.FEATURES.items()}
    syn = synthetic(cfg)
    for r in syn:
        files["check"].append({"id": r["id"], "prompt": prompt_first(labels[r["feature"]],
                                                                       r["subject"],
                                                                       r["passage"])})  # fmt: skip
    known_ids = [x["id"] for t in texts if t["role"] == "known" and t["name"] in ments
                 for x in ments[t["name"]]["sample"]]  # fmt: skip
    rng = random.Random(f"{s['seed']}-real")
    real = sorted(rng.sample(known_ids, min(s["real_check_n"], len(known_ids))))
    real_set = set(real)
    by_id = {x["id"]: (t, x) for t in texts if t["name"] in ments
             for x in ments[t["name"]]["sample"]}  # fmt: skip
    for i in real:
        t, x = by_id[i]
        files["check"].append(
            {"id": i, "prompt": prompt_first(labels[x["feature"]], t["subject"], x["passage"])}
        )
        files["check"].append(
            {
                "id": i + "#2",
                "prompt": prompt_second(labels[x["feature"]], t["subject"], x["passage"]),
            }
        )
    rule_upper = 0
    for t in texts:
        if t["role"] == "rule" and not t.get("subject_answer"):
            segs = segments_of(t, cfg)
            if segs is None:
                continue
            words = " ".join(segs[0][1].split()[: s["subject_words"]])
            row = door.catalog({t["source"][4:]}).get(t["source"][4:], {})
            files["subject"].append({"id": "subject|" + t["source"][4:], "prompt":
                                     SUBJECT_PROMPT.format(title=" ".join((row.get("title") or
                                                                           "").split()),
                                                           opening=words)})  # fmt: skip
            rule_upper += len(ments.get(t["name"], {}).get("sample", []))
        if t["name"] not in ments:
            continue
        if t["role"] == "rule" and t["row"] is None:
            continue  # not yet answered, or answered E (something else)
        f = {"known": "known", "reference": "reference", "rule": "rule", "control": "control",
             "book": "book"}[t["role"]]  # fmt: skip
        for x in ments[t["name"]]["sample"]:
            if x["id"] in real_set:
                continue
            files[f].append(
                {
                    "id": x["id"],
                    "prompt": prompt_first(labels[x["feature"]], t["subject"], x["passage"]),
                }
            )
    pb = CACHE / "partb_hits.json"
    if pb.exists():
        hits = json.loads(pb.read_text())["hits"]
        for fid, rows in hits.items():
            for h in rows:
                files["partb"].append(
                    {
                        "id": f"partb|{fid}|{h['work_id']}",
                        "prompt": PARTB_PROMPT.format(
                            year=h["year"], passage=h["passage"], label=labels[fid]
                        ),
                    }
                )
    for k, rows in files.items():
        out(CARD / f"jobs_{k}.jsonl").write_text("".join(json.dumps(j) + "\n" for j in rows))
    meta = {"synthetic": [{k: v for k, v in r.items() if k != "passage"} for r in syn],
            "real_check": real}  # fmt: skip
    out(CARD / "jobs_meta.json").write_text(json.dumps(meta))
    per_hour = cfg["lab"]["judge"]["per_hour"]
    sizes = {f"jobs_{k}.jsonl": len(v) for k, v in files.items()}
    return {"questions": sizes,
            "hours_at_per_hour": {k: round(v / per_hour, 1) for k, v in sizes.items()},
            "rule_upper_bound_if_all_candidates_qualify": rule_upper,
            "partb_scan_done": pb.exists(), "per_hour": per_hour, "model": s["judge_model"],
            "order": "check, subject, known + reference + rule, control, book, partb",
            "labelled": SIMULATED + "; prepared, not run"}  # fmt: skip


# ------------------------------------------------------------------------------ Part B


def _partb_scan(job: tuple[dict, list[str], str, int, int]) -> list[tuple[str, str, int, int]]:
    """(feature, work id, year, char) of the first marker near an America term, per feature."""
    row, fids, america, ctx, year = job
    try:
        text = clean(door.text_of(row))
    except OSError:
        return []
    low = text.lower()
    if not re.search(america, low):
        return []
    spans, hits = find_markers(text)
    am = re.compile(america)
    near = [i for i, (a, _b) in enumerate(spans) if am.match(low, a)]
    if not near:
        return []
    import bisect

    got, seen = [], set()
    for fid, a, _b in hits:
        if fid not in fids or fid in seen:
            continue
        j = bisect.bisect_left(near, a - ctx)
        if j < len(near) and near[j] <= a + ctx:
            got.append((fid, row["work_id"], year, spans[a][0]))
            seen.add(fid)
    return got


def cmd_partb_scan(cfg: dict, workers: int = 8) -> dict:
    """Every library text up to ``partb_year_max`` read once; for each Mesoamerica-only and
    1820s-only feature the earliest works holding a marker near an America term (one hit a
    work, ``partb_max_hits`` a feature, earliest year first). Passages kept locally."""
    from concurrent.futures import ProcessPoolExecutor

    s = settings(cfg)
    _named(cfg)
    fids = [f for f, v in feat.FEATURES.items() if v[2] in (MS, AM)]
    reg = [r for r in _registry() if r["has_text"] and r["dup_keeper"] and not r["ocr_excluded"]
           and not r["sealed"] and r["year"] and r["year"] <= s["partb_year_max"]
           and (r["words"] or 0) >= s["partb_min_words"]]  # fmt: skip
    cat = door.catalog({r["work_id"] for r in reg})
    jobs = [({**cat[r["work_id"]], **r}, fids, s["partb_america"], s["partb_context"], r["year"])
            for r in reg if cat.get(r["work_id"], {}).get("text_path")]  # fmt: skip
    found: dict[str, list[tuple[int, str, int]]] = defaultdict(list)
    with ProcessPoolExecutor(workers, initializer=_init_vocab, initargs=(dict(inv.VOCAB),)) as ex:
        for got in ex.map(_partb_scan, jobs, chunksize=64):
            for fid, wid, year, ch in got:
                found[fid].append((year, wid, ch))
    hits: dict[str, list[dict]] = {}
    for fid in fids:
        rows = sorted(found.get(fid, []))[: s["partb_max_hits"]]
        hits[fid] = []
        for year, wid, ch in rows:
            text = clean(door.text_of(cat[wid]))
            spans, mk = find_markers(text[max(0, ch - 3000) : ch + 3000])
            off = max(0, ch - 3000)
            idx = next((i for i, (a, _b) in enumerate(spans) if a + off == ch), None)
            if idx is None:
                continue
            end = next((b for f, a, b in mk if a == idx and f == fid), idx + 1)
            hits[fid].append({"work_id": wid, "year": year, "char": ch,
                              "passage": passage(text[off : ch + 3000], spans, idx, end,
                                                 s["context_words"])})  # fmt: skip
    out(CACHE / "partb_hits.json").write_text(json.dumps({"hits": hits, "works_read": len(jobs)}))
    return {"works_read": len(jobs),
            "works_with_hit": {f: len(found.get(f, [])) for f in fids},
            "earliest": {f: [(h["year"], h["work_id"]) for h in hits[f][:3]] for f in fids},
            "questions": sum(len(v) for v in hits.values())}  # fmt: skip


def _init_vocab(vocab: dict) -> None:
    inv.VOCAB.clear()
    inv.VOCAB.update(vocab)


def partb_dates(answers: dict[str, str]) -> dict[str, dict]:
    """Per feature: the earliest print year of a passage the judge says states it of ancient
    Americans; "not found" if no hit says so (not found in the library, never "unknown")."""
    pb = CACHE / "partb_hits.json"
    if not pb.exists():
        return {}
    res = {}
    for fid, rows in json.loads(pb.read_text())["hits"].items():
        yes, n_open = [], 0
        for h in rows:
            a = answers.get(f"partb|{fid}|{h['work_id']}")
            if a is None:
                n_open += 1
                continue
            p = parse_letter(a, "YN")
            if p is None:
                log_unparsed(f"partb|{fid}|{h['work_id']}", a)
                n_open += 1
            elif p == "Y":
                yes.append((h["year"], h["work_id"]))
        res[fid] = {"hits": len(rows), "open": n_open,
                    "earliest": min(yes) if yes else None,
                    "state": "open" if n_open else ("found" if yes else
                                                    "not found in the library")}  # fmt: skip
    return res


# ------------------------------------------------------------------------------ check and run


def all_answers() -> dict[str, str]:
    return load_answers([CARD / f"answers_{k}.jsonl" for k in JOB_FILES])


def world_rows(texts: list[dict]) -> dict[str, tuple[str, str]]:
    return {t["name"]: (t["world"], t["row"]) for t in texts
            if t["role"] in ("reference", "rule") and t["row"]}  # fmt: skip


def evaluate(texts: list[dict], ments: dict[str, dict], answers: dict[str, str],
             meta: dict, cfg: dict, log: bool = True) -> dict:  # fmt: skip
    """The judge check and the known-answer check from answers. Never scores the book."""
    s = settings(cfg)
    jc = judge_check(meta, answers, cfg)
    ref_texts = [t for t in texts if t["role"] in ("reference", "rule") and t["row"]]
    known = [t for t in texts if t["role"] in ("known", "control")]
    states, status, sig = score_texts(ref_texts + known, ments, answers, cfg, log)
    open_refs = [t["name"] for t in ref_texts if t["name"] in ments and t["name"] not in states]
    values = world_values({n: v for n, v in states.items()}, world_rows(texts), cfg)
    keep, dropped = kept_features(values)
    res_known = {}
    for t in known:
        n = t["name"]
        if n not in ments:
            res_known[n] = {"role": t["role"], "state": "not attempted (text not held)"}
            continue
        if n not in states:
            res_known[n] = {"role": t["role"], "state": "open", **status[n]}
            continue
        sd = side(states[n], keep, values, cfg)
        sd.pop("features")
        row = {"role": t["role"], "own_world": t["world"], "words": ments[n]["words"], **sd,
               "signature": sig[n]}  # fmt: skip
        if t["role"] == "known":
            row["passes"] = known_passes(n, t["world"], sd, s)
        res_known[n] = row
    kn = [t["name"] for t in texts if t["role"] == "known"]
    complete = not open_refs and all("passes" in res_known.get(n, {}) for n in kn)
    diaz = res_known.get("bernal_diaz_keatinge_1800", {}).get("passes")
    passed = bool(complete and jc["passed"] and all(res_known[n]["passes"] for n in kn))
    return {"judge_check": jc, "references_open": open_refs, "features_kept": keep,
            "dropped": dropped, "world_values": values, "dplace_check": dplace_check(values),
            "known": res_known, "diaz_passes": diaz, "complete": complete,
            "reference_signatures": {n: sig[n] for n in sig if n not in res_known},
            "passed": passed}  # fmt: skip


def score_book(ments: dict[str, dict], answers: dict[str, str], values: dict, keep: list[str],
               cfg: dict) -> dict:  # fmt: skip
    """The Book of Mormon: whole text, without the Bible-quoting chapters, and the Old World
    scenes (mentions the judge puts elsewhere) apart."""
    s = settings(cfg)
    m = ments["book_of_mormon"]
    parsed, st = readings([x["id"] for x in m["sample"]], answers)
    if st["answered"] != st["asked"]:
        return {"state": "open", **st}
    res: dict = {"reading": st, "signature": signature(m["sample"], parsed)}
    noq = [x for x in m["sample"] if not (x["ref"] or "").endswith(" Q")]
    words_noq = sum(len(t.split()) for r, t in bom_units() if not r.endswith(" Q"))
    for label, sample, words, place in (("whole", m["sample"], m["words"], "main"),
                                        ("without_quoted", noq, words_noq, "main"),
                                        ("old_world_scenes", m["sample"], m["words"],
                                         "elsewhere")):  # fmt: skip
        sts = stated(sample, parsed, words, s, place)
        sd = side(sts, keep, values, cfg)
        for fid, v in sd["features"].items():
            v["refs"] = [
                x["ref"]
                for x in sample
                if x["feature"] == fid and parsed[x["id"]][0] == "S" and parsed[x["id"]][1] == "H"
            ][:5]
        sd["composite"] = composite(sd, s)
        res[label] = sd
    w, q = res["whole"], res["without_quoted"]
    lead = w["sides_with"]
    if (lead == q["sides_with"] and lead in feat.WORLDS
            and w["resample_lead_share"].get(lead, 0) >= s["known_resample_share"]):  # fmt: skip
        res["verdict"] = f"sides with {lead}"
    elif w["composite"]:
        res["verdict"] = "composite: " + "+".join(w["composite"])
    else:
        res["verdict"] = "cannot tell"
    return res


def cmd_check(cfg: dict) -> dict:
    texts, ments = collect(cfg)
    meta = json.loads((CARD / "jobs_meta.json").read_text())
    return evaluate(texts, ments, all_answers(), meta, cfg)


def cmd_run(cfg: dict) -> dict:
    texts, ments = collect(cfg)
    meta = json.loads((CARD / "jobs_meta.json").read_text())
    answers = all_answers()
    ev = evaluate(texts, ments, answers, meta, cfg)
    res = {"test": "BOM-109 second design (lab; exploratory)", "card": str(CARD / "card.md"),
           "label": SIMULATED, "check": ev}  # fmt: skip
    if not ev["passed"]:
        why = (
            "the checks are not complete (open answers)"
            if not ev["complete"] or not ev["judge_check"]["complete"]
            else "a known-answer check missed"
        )
        res["book_of_mormon"] = f"not scored: {why}"
        return res
    book = score_book(ments, answers, ev["world_values"], ev["features_kept"], cfg)
    res["book_of_mormon"] = book
    dates = partb_dates(answers)
    if isinstance(book, dict) and "whole" in book:
        ms_sole = [f for f, v in book["whole"]["features"].items() if v["agrees_with"] == [MS]]
        res["part_b"] = {f: dates.get(f, {"state": "not attempted"}) for f in ms_sole}
        res["part_b_1820s_features"] = {
            f: dates.get(f, {"state": "not attempted"})
            for f, v in feat.FEATURES.items()
            if v[2] == AM
        }
    return res


# ------------------------------------------------------------------------------ development run


def dev_case(cfg: dict) -> dict:
    """The scoring on hand-made answers (no judge): the made-up passages answered with their
    key and with every answer "own people, have" (the first must pass, the second must not);
    and a toy grid of three worlds and four known texts with answers written by hand, one of
    them a conquest chronicle whose guns belong to outsiders."""
    s = settings(cfg)
    syn = synthetic(cfg)
    key_answers = {r["id"]: ",".join(r["key"][k] for k in ("whose", "what", "where"))
                   for r in syn}  # fmt: skip
    naive = {r["id"]: "S,H,M" for r in syn}
    meta = {"synthetic": syn, "real_check": []}
    toy = toy_grid(s)
    return {"label": "development run on hand-made answers; not the check",
            "judge_check_with_key": judge_check(meta, key_answers, cfg)["synthetic"],
            "judge_check_naive": judge_check(meta, naive, cfg)["synthetic"],
            "toy_grid": toy}  # fmt: skip


def toy_grid(s: dict) -> dict:
    """Hand-made worlds: each text's answers written as {feature: [(whose, what, where), ...]}."""
    cfg = {"lab": {"three_worlds2": {**s, "rows_pooled": {NE: ["native"], MS: ["native"],
                                                          AM: ["s_antiquities"],
                                                          CT: ["sample"]}}}}  # fmt: skip
    own_have = ("S", "H", "M")
    spec = {
        # references: two per world
        ("ne1", NE, "native"): {"horses": [own_have] * 3, "iron_steel": [own_have] * 3,
                                "wheat_barley": [own_have] * 3, "maize": [("S", "L", "M")],
                                "mounds": [("S", "L", "M")], "firearms": [("S", "L", "M")]},
        ("ne2", NE, "native"): {"horses": [own_have] * 2, "iron_steel": [own_have] * 2,
                                "wheat_barley": [own_have] * 2, "maize": [("S", "L", "M")],
                                "mounds": [("S", "L", "M")], "firearms": [("S", "L", "M")]},
        ("ms1", MS, "native"): {"maize": [own_have] * 3, "horses": [("S", "L", "M")],
                                "iron_steel": [("S", "L", "M")], "wheat_barley": [("S", "L", "M")],
                                "mounds": [("S", "L", "M")], "firearms": [("S", "L", "M")]},
        ("ms2", MS, "native"): {"maize": [own_have] * 2, "horses": [("S", "L", "M")],
                                "iron_steel": [("S", "L", "M")], "wheat_barley": [("S", "L", "M")],
                                "mounds": [("S", "L", "M")], "firearms": [("S", "L", "M")]},
        ("am1", AM, "s_antiquities"): {"mounds": [own_have] * 3, "iron_steel": [own_have] * 2,
                                       "horses": [("S", "L", "M")], "maize": [own_have] * 2,
                                       "wheat_barley": [("S", "L", "M")],
                                       "firearms": [("S", "L", "M")]},
        ("am2", AM, "s_antiquities"): {"mounds": [own_have] * 2, "iron_steel": [own_have] * 2,
                                       "horses": [("S", "L", "M")], "maize": [own_have] * 2,
                                       "wheat_barley": [("S", "L", "M")],
                                       "firearms": [("S", "L", "M")]},
        ("ct1", CT, "sample"): {"firearms": [own_have] * 3, "horses": [own_have] * 2,
                                "iron_steel": [own_have] * 2, "wheat_barley": [own_have] * 2,
                                "maize": [own_have] * 2, "mounds": [("S", "L", "M")]},
        ("ct2", CT, "sample"): {"firearms": [own_have] * 2, "horses": [own_have] * 2,
                                "iron_steel": [own_have] * 2, "wheat_barley": [own_have] * 2,
                                "maize": [own_have] * 2, "mounds": [("S", "L", "M")]},
        # a conquest chronicle: guns and horses are the outsiders'; the natives lack them
        ("chronicle", MS, None): {"horses": [("O", "H", "M")] * 5 + [("S", "L", "M")],
                                  "firearms": [("O", "H", "M")] * 5 + [("S", "L", "M")],
                                  "iron_steel": [("O", "H", "M")] * 3 + [("S", "L", "M")],
                                  "maize": [own_have] * 4, "mounds": [("S", "L", "M")],
                                  "wheat_barley": [("O", "B", "M")] * 2 + [("S", "L", "M")]},
        # the same chronicle read the first design's way (every mention credited)
        ("chronicle_word_count", MS, None): {"horses": [own_have] * 6, "firearms": [own_have] * 6,
                                             "iron_steel": [own_have] * 4, "maize": [own_have] * 4,
                                             "mounds": [("S", "L", "M")],
                                             "wheat_barley": [own_have] * 3},
        ("bible_book", NE, None): {"horses": [own_have] * 4, "iron_steel": [own_have] * 3,
                                   "wheat_barley": [own_have] * 3, "maize": [("S", "L", "M")],
                                   "mounds": [("S", "L", "M")], "firearms": [("S", "L", "M")],
                                   "cotton": [("F", "X", "M")] * 3},
    }  # fmt: skip
    mentions, answers, rows = {}, {}, {}
    for (name, world, row), feats in spec.items():
        sample = []
        for fid, reads in feats.items():
            for n, r in enumerate(reads):
                i = f"{name}|{fid}|{n}"
                sample.append({"id": i, "feature": fid, "ref": None})
                answers[i] = ",".join(r)
        mentions[name] = {"words": 50000, "sample": sample}
        if row:
            rows[name] = (world, row)
    states = {n: stated(m["sample"], readings([x["id"] for x in m["sample"]], answers,
                                                log=False)[0], m["words"], s)
              for n, m in mentions.items()}  # fmt: skip
    values = world_values({n: states[n] for n in rows}, rows, cfg)
    keep, dropped = kept_features(values)
    sided = {}
    for n in ("chronicle", "chronicle_word_count", "bible_book"):
        sd = side(states[n], keep, values, cfg)
        sided[n] = {k: sd[k] for k in ("agree", "sole", "sides_with", "lead",
                                       "resample_lead_share")}  # fmt: skip
    return {"kept": keep, "dropped": {k: len(v) for k, v in dropped.items()},
            "values": {f: {w: values[f][w]["value"] for w in feat.WORLDS} for f in keep},
            "texts": sided}  # fmt: skip


# ------------------------------------------------------------------------------ command line


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["texts", "mentions", "partb-scan", "jobs", "dev", "check",
                                    "run"])  # fmt: skip
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "texts":
        res = cmd_texts(cfg)
        write(OUT / "texts.json", res)
        print(json.dumps({k: v for k, v in res.items() if k != "texts"}, indent=1))
        for n, t in res["texts"].items():
            if not n.startswith(("rule|", "news|")):
                print(
                    f"  {n:45s} {t['role']:9s} {t['row'] or '':24s} {t['words']:>9,} "
                    f"hits {t['marker_hits']:>6,} sampled {t['sampled']:>4}"
                )
    elif a.cmd == "mentions":
        res = cmd_mentions(cfg)
        write(OUT / "mentions.json", res)
        print(json.dumps(res["sampled_by_role"]))
        for f, v in res["per_feature"].items():
            print(
                f"  {f:22s} texts {v['texts_with_hits']:>4} hits {v['hits']:>7,} "
                f"sampled {v['sampled']:>5}"
            )
    elif a.cmd == "partb-scan":
        res = cmd_partb_scan(cfg, a.workers)
        write(OUT / "partb_scan.json", res)
        print(json.dumps(res, indent=1))
    elif a.cmd == "jobs":
        res = cmd_jobs(cfg)
        write(OUT / "jobs.json", res)
        print(json.dumps(res, indent=1))
    elif a.cmd == "dev":
        res = dev_case(cfg)
        write(OUT / "dev_hand_answers.json", res)
        print(json.dumps(res, indent=1))
    elif a.cmd == "check":
        res = cmd_check(cfg)
        write(OUT / "check.json", res)
        print(
            "judge check:",
            json.dumps(res["judge_check"]["synthetic"]),
            json.dumps(res["judge_check"]["real"]),
            "passed",
            res["judge_check"]["passed"],
        )
        print("references still open:", len(res["references_open"]))
        print("kept features:", len(res["features_kept"]))
        for n, t in res["known"].items():
            print(
                f"  {n:40s} {t.get('role')} {t.get('agree')} -> {t.get('sides_with')} "
                f"lead {t.get('lead')} {t.get('resample_lead_share')} passes {t.get('passes')}"
            )
        print("Diaz passes:", res["diaz_passes"], " passed:", res["passed"])
    else:
        res = cmd_run(cfg)
        write(OUT / "result.json", res)
        print("checks passed:", res["check"]["passed"], "| book:",
              res["book_of_mormon"] if isinstance(res["book_of_mormon"], str)
              else res["book_of_mormon"].get("verdict"))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
