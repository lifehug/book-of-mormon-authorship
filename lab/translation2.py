"""BOM-102, second design: Hebrew constructions the King James Bible removed.

The first design (``lab.translation``) missed its known-answer check: a source-blind translation
detector called *The Late War* a translation, and the claimed Hebraisms the King James Bible
carries are reached by imitators. This design asks a narrower question. Step 1 redoes the
claimants' own approach: each verse cited by Tvedtnes, Parry, Peterson and Skousen is looked up in
the 1830 text (and the if-and cases in the manuscripts), and their few counts are recounted.
Step 2 builds an inventory of Hebrew constructions from the Open Scriptures Hebrew Bible by rule,
measures how often the King James Bible keeps each one's literal English shape (retention), and
keeps the suppressed ones. Each has a fixed English rule; the rules are counted in literal
translations from Hebrew, the King James Bible, imitations, pseudo-translations, other
translations, period prose, Old Bailey testimony, Early Modern English prose and Joseph Smith's
other texts. The known-answer check (K1-K4 on the card) comes first; K3 needs the owner's hand
check and the simulated AI judge, so a rule-only run stops before the Book of Mormon. The Book of
Mormon is never trained or tuned on (nothing here is trained). Card, written first:
``data/private/lab/owner/2026-11-22-translation-redesign/card.md``; settings
``lab.translation2``. Public outputs hold ids and numbers, no text; judge questions, hand-check
sheets and quoted wording stay in the card folder.

Usage::

    python -m lab.translation2 step1     # their way: cited verses, counts -> step1_v2.json (1 min)
    python -m lab.translation2 run       # inventory, controls, check K1 K2 K4, judge jobs (15 min)
    python -m lab.translation2 answers   # judge check, verified counts, hand checks (1 min)
    python -m lab.translation2 score     # only after the full check passes: the Book of Mormon
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from bisect import bisect_right
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.compute as pc
from rapidfuzz import fuzz

from lab import door, registry
from lab import translation as T1
from lab.paths import NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "translation"
CARD = NOTES / "owner" / "2026-11-22-translation-redesign"
CITATIONS = CARD / "citations.json"
SRC = Path("data/corpus/lab/sources/translation")
MORPHHB = SRC / "morphhb" / "wlc"
GUTENBERG = SRC / "bom_gutenberg_versified.txt"
TCP_XML = Path("data/corpus/tcp/xml")
JSP_OM = Path("data/private/bom/jsp_original.jsonl")
JSP_PM = Path("data/private/bom/jsp_printers.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
MASK = Path("data/kjv_mask/bom/spans.jsonl")

PUNCT = T1.PUNCT
CLAUSE_END = frozenset(".!?;:")

# ----------------------------------------------------------------------------- tokens


def tokens(text: str) -> list[str]:
    """Lower-case words and punctuation (the first design's tokens, long s repaired)."""
    return [OLD.get(t, t) for t in T1.tokens(text)]


OLD = {"yf": "if", "yt": "it", "vnto": "unto", "vpon": "upon", "vp": "up"}


def norm(w: str) -> str:
    """Spelling-blind form for comparing two words: u/v and i/j merged."""
    return w.replace("v", "u").replace("j", "i")


def words(text: str) -> list[str]:
    return [t for t in tokens(text.replace("ſ", "s")) if t not in PUNCT]


def word_count(toks: list[str]) -> int:
    return sum(1 for t in toks if t not in PUNCT)


# ----------------------------------------------------------------------------- English rules

SUBJ = frozenset("i thou he she it we ye you they".split())
AUX = frozenset(
    """shall shalt will wilt doth dost do did didst hath hast have had may mayest maist mayst
    might must can canst could would should shouldest wouldest art is are was were be""".split()
)
GAP_OK = SUBJ | AUX | {"not"}
NOT_ING = frozenset(
    """thing things king nothing something anything everything evening morning during according
    concerning notwithstanding saying being having spring string ring wing sling bring sing
    offspring""".split()
)
SUFFIXES = frozenset(["", "e", "s", "es", "ed", "d", "eth", "th", "est", "st", "edst", "n", "en"])


def _stems(w1: str) -> set[str]:
    s = norm(w1)[:-3]
    out_ = {s}
    if len(s) >= 3 and s[-1] == s[-2]:
        out_.add(s[:-1])  # cutting -> cut
    if s.endswith("y") and len(s) >= 2:
        out_.add(s[:-1] + "i")  # dying -> die
    return {x for x in out_ if len(x) >= 2}


def same_verb(w1: str, w2: str) -> bool:
    """``w1`` an -ing form and ``w2`` a finite form of the same verb (blessing ... bless)."""
    if not w1.endswith("ing") or w1 in NOT_ING or w2.endswith("ing") or w1 == w2:
        return False
    n2 = norm(w2)
    return any(n2.startswith(s) and n2[len(s) :] in SUFFIXES for s in _stems(w1))


def doubled_verb(toks: list[str], gap: int) -> list[tuple[int, int]]:
    """An -ing form next to a finite form of the same verb, at most ``gap`` pronoun or
    auxiliary words between, no punctuation: "dying thou shalt die", "blessing I will bless",
    and the reverse order ("hear ye hearing")."""
    hits, used = [], set()
    for i, w in enumerate(toks):
        if not w.endswith("ing") or i in used:
            continue
        for step in (1, -1):
            found = None
            j = i + step
            while 0 <= j < len(toks) and abs(j - i) <= gap + 1:
                t = toks[j]
                if t in PUNCT:
                    break
                if same_verb(w, t) and j not in used:
                    found = j
                    break
                if t not in GAP_OK:
                    break
                j += step
            if found is not None:
                hits.append((min(i, found), max(i, found)))
                used |= {i, found}
                break
    return hits


SPEECH = frozenset("say saith sayeth said sayest command commanded".split())
APOD = AUX | frozenset("getteth".split())


def if_and(toks: list[str], max_words: int) -> list[tuple[int, int]]:
    """A conditional whose main clause opens with "and": "if ye shall ask ..., and he will
    manifest". The "if" clause runs at most ``max_words`` words with no clause end and no
    "then"; after ", and" (optionally "behold") come a subject and an auxiliary. Rejected when a
    comma segment inside the "if" clause is itself a main clause (subject + auxiliary, not after a
    verb of saying), or when "then" follows before the clause ends (a second condition)."""
    hits = []
    n = len(toks)
    for i, t in enumerate(toks):
        if t != "if":
            continue
        count, j, ok = 0, i + 1, False
        while j < n - 2 and count <= max_words:
            w = toks[j]
            if w in CLAUSE_END or w in ("then", "if"):
                break
            if w == "," and toks[j + 1] == "and":
                k = j + 2
                if k < n and toks[k] == "behold":
                    k += 1
                    if k < n and toks[k] == ",":
                        k += 1
                if k + 1 < n and toks[k] == "no" and toks[k + 1] == "man":
                    k += 1
                if k + 1 < n and (toks[k] in SUBJ or toks[k] == "man") and toks[k + 1] in APOD:
                    ok = count > 0 and not _main_inside(toks, i, j)
                    if ok and not _then_after(toks, k + 2, 12):
                        hits.append((i, k + 1))
                break
            if w not in PUNCT:
                count += 1
            j += 1
    return hits


OPENS_CLAUSE = frozenset(
    "that which who whom when as because lest before after till until and or if".split()
)


def _main_inside(toks: list[str], i: int, j: int) -> bool:
    """A main clause inside the "if" clause: a subject and an auxiliary after a comma (not after
    a verb of saying), or straight after another word that does not open a clause ("if it rain
    we shall stay"); the subject right after "if" is the condition's own."""
    for c in range(i + 2, j - 1):
        if toks[c] in SUBJ and toks[c + 1] in AUX:
            before = toks[c - 1]
            if before == ",":
                if toks[c - 2] not in SPEECH:
                    return True
            elif before not in OPENS_CLAUSE and before not in SPEECH and before not in PUNCT:
                return True
    return False


def _then_after(toks: list[str], k: int, span: int) -> bool:
    for t in toks[k : k + span]:
        if t in CLAUSE_END:
            return False
        if t == "then":
            return True
    return False


POSS = frozenset("my thy thine his her its our your their".split())
POSS_PREP = frozenset("in at by after before until till upon on".split())
NOUN_ING = NOT_ING | frozenset(
    """understanding beginning dwelling building blessing offering clothing feeling learning
    writing teaching preaching meaning wedding bedding lodging covering dealing hearing sight
    proceeding suffering reckoning inheritance lightning""".split()
)


def possessive_infinitive(toks: list[str]) -> list[tuple[int, int]]:
    """A preposition, a possessive and an -ing form: "in thine eating", "at his coming", "in the
    day of thy going" (Hebrew b-/k- + infinitive construct + pronoun suffix)."""
    hits = []
    for i, t in enumerate(toks):
        if t not in POSS_PREP:
            continue
        k = i + 1
        if toks[k : k + 3] in (["the", "day", "of"], ["the", "time", "of"]):
            k += 3
        if k + 1 < len(toks) and toks[k] in POSS:
            w = toks[k + 1]
            if w.endswith("ing") and len(w) >= 5 and w not in NOUN_ING:
                hits.append((i, k + 1))
    return hits


def _phrase_rule(rx: str):
    pat = re.compile(rx)

    def rule(toks: list[str]) -> list[tuple[int, int]]:
        s, starts, pos = "", [], 0
        for t in toks:
            starts.append(pos)
            pos += len(t) + 1
        s = " ".join(toks)
        res = []
        for m in pat.finditer(s):
            a = bisect_right(starts, m.start()) - 1
            b = bisect_right(starts, max(m.end() - 1, m.start())) - 1
            res.append((a, b))
        return res

    return rule


came_to_pass = _phrase_rule(r"\b(?:came|come|cometh|coming) to pass\b")
by_the_hand_of = _phrase_rule(r"\bby the hands? of\b")
from_before = _phrase_rule(r"\bfrom before\b")
called_the_name = _phrase_rule(r"\bcall(?:ed|eth|est|edst)? (?:the|his|her|their|its) names?\b")


def of_material(toks: list[str]) -> list[tuple[int, int]]:
    s = " ".join(toks)
    starts, pos = [], 0
    for t in toks:
        starts.append(pos)
        pos += len(t) + 1
    return [
        (bisect_right(starts, m.start()) - 1, bisect_right(starts, m.end() - 1) - 1)
        for m in T1.OF_MATERIAL.finditer(s)
        if m.group(1) not in T1.QUANT
    ]


# name: (rule, claimed by the authors, tested or carried, Hebrew construction)
FEATURES = {
    "doubled_verb": (False, "test"),
    "if_and": (True, "test"),
    "possessive_infinitive": (False, "test"),
    "came_to_pass": (True, "carried"),
    "by_the_hand_of": (True, "carried"),
    "from_before": (True, "carried"),
    "of_material": (True, "carried"),
    "called_the_name": (True, "carried"),
}
TESTED = [f for f, (_, k) in FEATURES.items() if k == "test"]


def find(feature: str, toks: list[str], s: dict) -> list[tuple[int, int]]:
    if feature == "doubled_verb":
        return doubled_verb(toks, s["doubled_gap"])
    if feature == "if_and":
        return if_and(toks, s["if_and_max_words"])
    return {
        "possessive_infinitive": possessive_infinitive,
        "came_to_pass": came_to_pass,
        "by_the_hand_of": by_the_hand_of,
        "from_before": from_before,
        "of_material": of_material,
        "called_the_name": called_the_name,
    }[feature](toks)


# Planted examples, written for this test (no corpus text). Each positive must add exactly one
# hit of its rule and each near miss none.
PLANTED = {
    "doubled_verb": (
        [
            "dying thou shalt die",
            "in blessing i will bless thee",
            "eating thou mayest eat of every tree",
            "multiplying i will multiply thy seed",
            "hear ye hearing but understand not",
        ],
        [
            "saying , say unto them",
            "he was dying and he died",
            "the king will bless the people",
            "singing and singing all day",
        ],
    ),
    "if_and": (
        [
            "if ye shall ask with a sincere heart , and he will manifest it",
            "if he saith unto the earth , move , and it is moved",
            "if you like , and i will go with you",
        ],
        [
            "if ye do this , ye shall live , and ye shall prosper",
            "if ye will hearken , and ye will keep my law , then ye shall live",
            "if it rain we shall stay at home , and they will come",
            "if he come , and if he see",
        ],
    ),
    "possessive_infinitive": (
        [
            "in the day of thine eating of it",
            "at his coming the men rose",
            "after their going out the gate was shut",
        ],
        [
            "in his understanding he was wise",
            "at his dwelling there was bread",
            "in going out he fell",
        ],
    ),
    "came_to_pass": (["and it came to pass that he went"], ["he came to the pass"]),
    "by_the_hand_of": (["sent by the hand of moses"], ["he took her by the hand"]),
    "from_before": (["they fled from before the enemy"], ["they fled before morning"]),
    "of_material": (["a rod of iron lay there"], ["a piece of gold lay there"]),
    "called_the_name": (["he called the name of the place bethel"], ["he called the man"]),
}


def plant_check(host: str, s: dict, seed: int) -> dict[str, bool]:
    toks = tokens(host)
    base = {f: len(find(f, toks, s)) for f in FEATURES}
    breaks = [i + 1 for i, t in enumerate(toks) if t == "."]
    rng = random.Random(seed)
    res = {}
    for f, (pos, neg) in PLANTED.items():
        ok = True
        for group, want in ((pos, len(pos)), (neg, 0)):
            t2 = list(toks)
            for ex in sorted(group, reverse=True):
                at = rng.choice(breaks)
                t2[at:at] = tokens(ex) + ["."]
            ok = ok and len(find(f, t2, s)) - base[f] == want
        res[f] = ok
    return res


# ----------------------------------------------------------------------------- rates


def poisson_ci(k: int, words_: int) -> tuple[float, float]:
    """Exact 95% interval for a rate per 10,000 words."""
    from scipy.stats import chi2

    lo = chi2.ppf(0.025, 2 * k) / 2 if k else 0.0
    hi = chi2.ppf(0.975, 2 * k + 2) / 2
    w = max(words_, 1)
    return round(float(1e4 * lo / w), 4), round(float(1e4 * hi / w), 4)


def measure(toks: list[str], s: dict, keep_hits: bool = False) -> dict:
    m: dict = {"words": word_count(toks)}
    for f in FEATURES:
        h = find(f, toks, s)
        m[f] = len(h)
        if keep_hits and f in TESTED:
            m.setdefault("hits", {})[f] = h
    return m


def rate_row(m: dict) -> dict:
    w = m["words"]
    res = {"words": w, "texts": m.get("texts", 1)}
    for f in FEATURES:
        k = m[f]
        res[f] = {"n": k, "per10k": round(1e4 * k / max(w, 1), 4), "ci": poisson_ci(k, w)}
    return res


def pooled(ms: list[dict]) -> dict:
    tot = {"words": sum(m["words"] for m in ms), "texts": len(ms)}
    for f in FEATURES:
        tot[f] = sum(m[f] for m in ms)
    return tot


def composite(m: dict, kept: list[str], ot: dict, floor: float) -> float | None:
    if not kept or not m["words"]:
        return None
    vals = [(1e4 * m[f] / m["words"]) / max(ot[f], floor) for f in kept]
    return round(statistics.fmean(vals), 4)


def composite_ci(m: dict, kept: list[str], ot: dict, floor: float) -> tuple[float, float] | None:
    """Mean of each feature's exact interval ends, scaled like the composite."""
    if not kept or not m["words"]:
        return None
    los, his = [], []
    for f in kept:
        lo, hi = poisson_ci(m[f], m["words"])
        los.append(lo / max(ot[f], floor))
        his.append(hi / max(ot[f], floor))
    return round(statistics.fmean(los), 4), round(statistics.fmean(his), 4)


def auc(pos: list[float], neg: list[float]) -> float | None:
    """Mann-Whitney AUC (ties count half)."""
    if not pos or not neg:
        return None
    wins = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return round(wins / (len(pos) * len(neg)), 4)


def units(toks: list[str], size: int) -> list[list[str]]:
    """Consecutive units of exactly ``size`` words (punctuation rides along); the rest dropped."""
    res, cur, n = [], [], 0
    for t in toks:
        cur.append(t)
        if t not in PUNCT:
            n += 1
            if n == size:
                res.append(cur)
                cur, n = [], 0
    return res


# ----------------------------------------------------------------------------- texts


def read_paths(spec) -> str | None:
    return T1.read_files(spec)


def tcp_divs(path: Path, types: tuple[str, ...]) -> str | None:
    """Text of the TEI divs of the given types, leaving out nested annotation divs, notes and
    gaps (Ainsworth's translation without his commentary)."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return None
    ns = "{http://www.tei-c.org/ns/1.0}"
    skip = {ns + "note", ns + "gap", ns + "head", ns + "argument"}
    parts: list[str] = []

    def walk(el: ET.Element, inside: bool) -> None:
        here = inside or (el.tag == ns + "div" and el.get("type") in types)
        if el.tag == ns + "div" and el.get("type") == "annotations":
            here = False
        if el.tag in skip:
            if inside and el.tail:
                parts.append(el.tail)
            return
        if here and el.text:
            parts.append(el.text)
        for c in el:
            walk(c, here)
        if inside and el.tail:
            parts.append(el.tail)

    walk(root, False)
    return " ".join("".join(parts).split())


def ylt_verses(path: Path) -> dict[str, str] | None:
    """Young's text by OSIS-style reference ("Gen.2.17"); bracketed supplied words kept."""
    try:
        with tarfile.open(path) as tf:
            raw = tf.extractfile("YLT.txt").read().decode("utf-8", "replace")
    except (OSError, KeyError, tarfile.TarError):
        return None
    res = {}
    for line in raw.splitlines():
        m = re.match(r"^([1-3]?[A-Za-z]+)\.(\d+):(\d+) (.*)$", line)
        if m:
            text = m.group(4).replace("[", "").replace("]", "").replace("`", "")
            res[f"{m.group(1)}.{m.group(2)}.{m.group(3)}"] = text
    return res


OT_OSIS = (
    "Gen Exod Lev Num Deut Josh Judg Ruth 1Sam 2Sam 1Kgs 2Kgs 1Chr 2Chr Ezra Neh Esth Job Ps Prov "
    "Eccl Song Isa Jer Lam Ezek Dan Hos Joel Amos Obad Jonah Mic Nah Hab Zeph Hag Zech Mal"
).split()
KJV_CODE = dict(
    zip(
        OT_OSIS,
        (
            "GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH EST JOB PSA PRO "
            "ECC SOL ISA JER LAM EZE DAN HOS JOE AMO OBA JON MIC NAH HAB ZEP HAG ZEC MAL"
        ).split(),
        strict=True,
    )
)


def kjv_verses() -> dict[str, str]:
    """King James Old Testament by OSIS-style reference."""
    back = {v: k for k, v in KJV_CODE.items()}
    res = {}
    for line in T1.KJV.read_text().splitlines():
        r = json.loads(line)
        if r["section"] == "OT":
            res[f"{back[r['book']]}.{r['chapter']}.{r['verse']}"] = r["text"]
    return res


def named_text(spec, s: dict) -> str | None:
    """A named text: a library id, a path, a list of paths, Ainsworth's translation divs or the
    Old Testament of Young's text."""
    if spec == s["texts"]["ainsworth_1627"]:
        return tcp_divs(TCP_XML / "A11649.xml", ("chapter", "prose_version_of_psalm"))
    if isinstance(spec, str) and spec.endswith(".tar"):
        v = ylt_verses(Path(spec))
        return (
            None if v is None else "\n".join(t for r, t in v.items() if r.split(".")[0] in OT_OSIS)
        )
    if isinstance(spec, str) and ":" in spec and not spec.startswith("data/"):
        return T1._text_of_id(spec)
    return read_paths(spec)


def ylt_nt(s: dict) -> str | None:
    v = ylt_verses(Path(s["texts"]["young_literal"]))
    return (
        None if v is None else "\n".join(t for r, t in v.items() if r.split(".")[0] not in OT_OSIS)
    )


def emode_rows(cfg: dict) -> list[str]:
    """Early Modern English prose: TCP works in the card's years, long enough, not scripture."""
    s = cfg["lab"]["translation2"]
    excl = re.compile(cfg["lab"]["translation"]["exclude_title"], re.I)
    tab = registry.load()
    keep = pc.and_(pc.equal(tab["kind"], "work"), pc.equal(tab["has_text"], True))
    lo, hi = s["emode_years"]
    rows = [
        r
        for r in tab.filter(keep)
        .select(["work_id", "year", "words", "dup_keeper", "sealed", "ocr_excluded"])
        .to_pylist()
        if r["work_id"].startswith("tcp:")
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and lo <= r["year"] <= hi
        and (r["words"] or 0) >= s["emode_min_words"]
    ]
    rows.sort(key=lambda r: r["work_id"])
    random.Random(s["seed"]).shuffle(rows)
    cat = door.catalog({r["work_id"] for r in rows[: s["emode_sample"] * 3]})
    got = []
    for r in rows[: s["emode_sample"] * 3]:
        c = cat.get(r["work_id"])
        if c and c["text_path"] and not excl.search(c["title"] or ""):
            got.append(r["work_id"])
        if len(got) == s["emode_sample"]:
            break
    return got


def _lib_job(job: tuple[str, dict, int]) -> tuple[str, dict | None]:
    wid, s, mx = job
    text = T1._text_of_id(wid)
    if text is None:
        return wid, None  # not attempted
    toks = tokens(text)
    if mx:
        idx = [i for i, t in enumerate(toks) if t not in PUNCT]
        if len(idx) > mx:
            a = idx[(len(idx) - mx) // 2]
            toks = toks[a : idx[(len(idx) - mx) // 2 + mx - 1] + 1]
    return wid, measure(toks, s)


# ----------------------------------------------------------------------------- Hebrew inventory


def hebrew_verses() -> dict[str, list[tuple[str, str]]]:
    """OSIS reference -> [(lemma, morph)] from the Open Scriptures Hebrew Bible."""
    res = {}
    ns = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
    for book in OT_OSIS:
        root = ET.parse(MORPHHB / f"{book}.xml").getroot()
        for v in root.iter(ns + "verse"):
            res[v.get("osisID")] = [
                (w.get("lemma") or "", w.get("morph") or "") for w in v.iter(ns + "w")
            ]
    return res


def verse_map() -> tuple[dict[str, str], set[str]]:
    """WLC -> KJV references where they differ (full verses), and WLC verses that map in part."""
    root = ET.parse(MORPHHB / "VerseMap.xml").getroot()
    full, partial = {}, set()
    for v in root.iter():
        if v.tag.endswith("verse") and v.get("wlc"):
            if v.get("type") == "full":
                full[v.get("wlc")] = v.get("kjv")
            else:
                partial.add(v.get("wlc"))
    return full, partial


def parse_word(lemma: str, morph: str) -> dict:
    """Prefixes, main lemma number and segments of one morphhb word."""
    lp = lemma.split("/")
    main = lp[-1].split()[0] if lp[-1] else ""
    segs = morph[1:].split("/") if morph else []
    verb = next((g for g in segs if g.startswith("V") and len(g) >= 3), None)
    noun = next((g for g in segs if g.startswith("N") and len(g) >= 2), None)
    return {
        "prefixes": set(lp[:-1]),
        "main": main,
        "verb_type": verb[2] if verb else None,
        "verb": verb,
        "noun_construct": bool(noun and noun.startswith("Nc") and noun.endswith("c")),
        "suffix": any(g.startswith("S") for g in segs[1:]),
        "conj": bool(segs) and segs[0] == "C",
    }


FINITE = frozenset("pqiwhjv")
MATERIAL_LEMMAS = frozenset({"2091", "3701", "5178", "1270", "6086", "68", "730"})


def hebrew_instances(words_: list[tuple[str, str]]) -> dict[str, int]:
    """How many instances of each construction one verse holds (rules on the card)."""
    w = [parse_word(lemma, m) for lemma, m in words_]
    c: Counter = Counter()
    for i, x in enumerate(w):
        if x["verb_type"] == "a":
            near = w[max(0, i - 3) : i] + w[i + 1 : i + 4]
            if any(y["verb_type"] in FINITE and y["main"] == x["main"] for y in near):
                c["doubled_verb"] += 1
        if x["main"] == "518" and not x["verb"]:
            rest = w[i + 1 :]
            first = next((k for k, y in enumerate(rest) if y["verb_type"] in FINITE), None)
            if first is not None and any(
                y["conj"] and y["verb_type"] == "q" for y in rest[first + 1 :]
            ):
                c["if_and"] += 1
        if x["verb_type"] == "c" and x["suffix"] and x["prefixes"] & {"b", "k"}:
            c["possessive_infinitive"] += 1
        if x["main"] == "1961" and x["verb"] == "Vqw3ms":
            c["came_to_pass"] += 1
        if x["main"] == "3027" and "b" in x["prefixes"] and x["noun_construct"]:
            c["by_the_hand_of"] += 1
        if x["main"] == "6440" and {"m", "l"} <= x["prefixes"]:
            c["from_before"] += 1
        if x["noun_construct"] and i + 1 < len(w) and w[i + 1]["main"] in MATERIAL_LEMMAS:
            c["of_material"] += 1
        if x["main"] == "7121" and x["verb"] and any(y["main"] == "8034" for y in w[i + 1 : i + 4]):
            c["called_the_name"] += 1
    return dict(c)


SEEDS = ["Gen.18.26", "Gen.24.8", "Gen.24.41", "Gen.28.20", "Gen.31.8", "Gen.34.17", "Gen.44.26"]
SEEDS += ["Gen.47.6"]  # Peterson 2002, note 58 (31:8 and 34:17 hold two each)


def inventory(cfg: dict) -> tuple[dict, list[dict]]:
    """Retention of each construction in the King James Bible (and in Young's text), by rule."""
    s = cfg["lab"]["translation2"]
    heb = hebrew_verses()
    full, partial = verse_map()
    kjv = kjv_verses()
    ylt = ylt_verses(Path(s["texts"]["young_literal"])) or {}
    inst: dict[str, list[str]] = defaultdict(list)
    for ref, ws in heb.items():
        for f, k in hebrew_instances(ws).items():
            inst[f].extend([ref] * k)
    for ref in SEEDS:
        if ref not in inst["if_and"]:
            inst["if_and"].append(ref)
    rng = random.Random(s["seed"])
    res, sheet = {}, []
    for f in FEATURES:
        refs = sorted(inst.get(f, []))
        skipped = sum(1 for r in refs if r in partial)
        usable = [r for r in refs if r not in partial]
        pick = (
            usable
            if len(usable) <= s["retention_sample"]
            else rng.sample(usable, s["retention_sample"])
        )
        kept = kept_y = read_y = 0
        rows = []
        for r in sorted(pick):
            kr = full.get(r, r)
            verse = kjv.get(kr)
            if verse is None:
                continue
            hit = bool(find(f, tokens(verse), s))
            kept += hit
            if kr in ylt:
                read_y += 1
                kept_y += bool(find(f, tokens(ylt[kr]), s))
            rows.append({"feature": f, "wlc": r, "kjv": kr, "rule_kept": hit, "kjv_text": verse})
        n = len(rows)
        ret = round(kept / n, 4) if n else None
        res[f] = {
            "claimed": FEATURES[f][0],
            "hebrew_instances": len(refs),
            "partial_verse_skipped": skipped,
            "sampled": n,
            "kjv_kept": kept,
            "retention_kjv": ret,
            "retention_young": round(kept_y / read_y, 4) if read_y else None,
            "young_read": read_y,
            "class": None
            if ret is None
            else "suppressed"
            if ret <= s["suppressed_max"]
            else "carried"
            if ret >= s["carried_max"]
            else "between",
        }
        sheet += random.Random(s["seed"]).sample(rows, min(len(rows), s["retention_hand"]))
    return res, sheet


# ----------------------------------------------------------------------------- the check


def gather(cfg: dict, workers: int) -> tuple[dict[str, dict], dict[str, list[str]], dict]:
    """Every control text measured: name -> counts (gating texts keep their hits and tokens)."""
    s = cfg["lab"]["translation2"]
    t1 = cfg["lab"]["translation"]
    meas: dict[str, dict] = {}
    toks_of: dict[str, list[str]] = {}
    info: dict = {"not_attempted": []}

    def add(name: str, text: str | None, gating: bool = False) -> None:
        if text is None:
            info["not_attempted"].append(name)
            return
        tk = tokens(text)
        meas[name] = measure(tk, s, keep_hits=gating)
        if gating:
            toks_of[name] = tk

    add("kjv_ot", T1.kjv_text("OT"), True)
    add("kjv_nt", T1.kjv_text("NT"))
    for name, spec in s["texts"].items():
        if name == "young_literal":
            add("young_ot", named_text(spec, s), True)
            add("young_nt", ylt_nt(s))
        else:
            add(
                name,
                named_text(spec, s),
                name in ("ainsworth_1627",) or name in s["pseudo_translations"],
            )
    for name, spec in t1["imitations"].items():
        add("imit:" + name, read_paths(spec), True)
        if name in s["pseudo_translations"] and "imit:" + name in meas:
            meas[name] = meas["imit:" + name]  # the same counts under its pseudo-translation name
    from lab import emode, spoken

    js = emode.js_texts()
    for name in s["js_dictated"] + s["js_own_hand"]:
        add("js:" + name, js.get(name))
    ob = spoken.oldbailey_sessions(
        {**cfg["lab"]["spoken"], "oldbailey_years": s["oldbailey_years"]}
    )
    add("old_bailey", None if ob is None else " ".join(ob.values()))
    prose_ids = T1.prose_rows(cfg)
    emode_ids = emode_rows(cfg)
    ns_ids = T1.non_semitic(cfg)
    heb = t1["hebrew_translations"]
    jobs = [(w, s, s["max_words"]) for w in prose_ids + emode_ids + ns_ids]
    jobs += [(w, s, None) for w in heb.values()]
    with ProcessPoolExecutor(workers) as ex:
        got = dict(ex.map(_lib_job, jobs, chunksize=4))
    for key, ids in (("prose", prose_ids), ("emode", emode_ids), ("non_semitic", ns_ids)):
        ok = [got[w] for w in ids if got.get(w)]
        meas[key + "_pooled"] = pooled(ok)
        info[key] = {"ids": ids, "unreadable": len(ids) - len(ok)}
        if key == "prose":
            info["prose_median"] = {
                f: round(statistics.median(1e4 * m[f] / m["words"] for m in ok if m["words"]), 4)
                for f in FEATURES
            }
    for k, w in heb.items():
        if got.get(w):
            meas["heb:" + k] = got[w]
        else:
            info["not_attempted"].append("heb:" + k)
    return meas, toks_of, info


def imitation_names(meas: dict) -> list[str]:
    return sorted(k for k in meas if k.startswith("imit:"))


def check(cfg: dict, meas: dict, inv: dict, counts_key: str = "raw") -> dict:
    """K1, K2 and K4 on the given counts (K3 is the hand check and is never decided here)."""
    s = cfg["lab"]["translation2"]
    ot = {f: 1e4 * meas["kjv_ot"][f] / meas["kjv_ot"]["words"] for f in FEATURES}
    k1 = {}
    for f in TESTED:
        ret = inv[f]["retention_kjv"]
        ot_ci = poisson_ci(meas["kjv_ot"][f], meas["kjv_ot"]["words"])
        lits = {}
        for name in ("ainsworth_1627", "young_ot"):
            m = meas.get(name)
            if not m:
                continue
            r = 1e4 * m[f] / m["words"]
            ci = poisson_ci(m[f], m["words"])
            lits[name] = {
                "per10k": round(r, 4),
                "ci": ci,
                "ratio": round(r / max(ot[f], s["ot_floor"]), 3),
                "passes": r >= s["literal_ratio"] * max(ot[f], s["ot_floor"]) and ci[0] > ot_ci[1],
            }
        k1[f] = {
            "claimed": FEATURES[f][0],
            "retention_kjv": ret,
            "suppressed": ret is not None and ret <= s["suppressed_max"],
            "kjv_ot_per10k": round(ot[f], 4),
            "kjv_ot_ci": ot_ci,
            "literal": lits,
            "kept": ret is not None
            and ret <= s["suppressed_max"]
            and any(v["passes"] for v in lits.values()),
        }
    kept = [f for f in TESTED if k1[f]["kept"]]
    k1_pass = len(kept) >= s["min_features"] and any(not FEATURES[f][0] for f in kept)
    imits = imitation_names(meas)
    groups = {"imitations_pooled": pooled([meas[k] for k in imits])}
    for p in s["pseudo_translations"]:
        if p in meas:
            groups[p] = meas[p]
    groups["late_war"] = meas.get("imit:late_war_1816")
    k2 = {}
    for name, m in groups.items():
        if not m:
            k2[name] = {"not_attempted": True}
            continue
        alone = (
            name in ("imitations_pooled", "late_war", "ossian_1819") or m["words"] >= s["min_words"]
        )
        c = composite(m, kept, ot, s["ot_floor"]) if kept else None
        k2[name] = {
            "words": m["words"],
            "composite": c,
            "checked": alone,
            "passes": (c is not None and c <= s["floor_ratio"]) if alone else None,
        }
    k2_pass = (
        bool(kept)
        and all(v.get("passes") is not False for v in k2.values())
        and all(
            k2[n].get("passes") for n in ("imitations_pooled", "late_war", "ossian_1819") if n in k2
        )
    )
    return {
        "counts": counts_key,
        "kjv_ot_rates": {f: round(v, 4) for f, v in ot.items()},
        "K1": {"features": k1, "kept": kept, "passes": k1_pass},
        "K2": {"groups": k2, "passes": k2_pass},
    }


def k4(cfg: dict, toks_of: dict, kept: list[str], ot: dict) -> dict:
    s = cfg["lab"]["translation2"]
    if not kept:
        return {"passes": False, "reason": "no kept feature"}

    def scores(names: list[str]) -> list[float]:
        res = []
        for n in names:
            for u in units(toks_of.get(n, []), s["unit_words"]):
                res.append(composite(measure(u, s), kept, ot, s["ot_floor"]))
        return res

    pos = scores(["ainsworth_1627", "young_ot"])
    neg = scores(
        sorted(k for k in toks_of if k.startswith("imit:") or k in s["pseudo_translations"])
    )
    a = auc(pos, neg)
    return {
        "literal_units": len(pos),
        "decoy_units": len(neg),
        "auc": a,
        "passes": a is not None and a >= s["auc_bar"],
    }


# ----------------------------------------------------------------------------- judge jobs

DEFINITIONS = {
    "doubled_verb": (
        "a DOUBLED VERB: the same verb said twice in a row for emphasis, once as an -ing form and "
        "once as an ordinary verb, with at most a pronoun or helping verb between (Hebrew "
        "'infinitive absolute'). Yes: 'dying thou shalt die'; 'in blessing I will bless thee'; "
        "'hear ye hearing'. No: 'saying, Say unto them' (two different acts); 'he was dying and "
        "he died' (two clauses); a noun and a verb ('the offering he offered')."
    ),
    "if_and": (
        "an IF-AND CONDITIONAL: a sentence where the result of an 'if' clause is introduced by "
        "'and' instead of 'then' or nothing, so that 'and' could be replaced by 'then'. Yes: 'if "
        "ye shall ask with a sincere heart, and he will manifest it unto you'; 'if he saith unto "
        "the earth, Move, and it is moved'. No: 'if ye do this, ye shall live, and ye shall "
        "prosper' (the result already came before 'and'); 'if ye hearken, and ye keep my law, "
        "then ye shall live' (the 'and' adds a second condition)."
    ),
    "possessive_infinitive": (
        "a POSSESSIVE INFINITIVE OF TIME: a preposition plus a possessive word plus an -ing verb "
        "that says WHEN something happens, as in Hebrew 'in his going' = 'when he went'. Yes: 'in "
        "the day of thine eating of it' (= when you eat it); 'at his coming the men rose'; 'after "
        "their going out the gate was shut'. No: 'in his understanding' (a noun, not a time); "
        "'at his dwelling' (a place); 'by their having money' (a cause, not a time)."
    ),
}
PROMPT = """You are helping a study of English grammar. Below is a short passage from a printed \
text (spelling may be old, and there may be scanning errors). The words marked [[like this]] were \
found by a pattern search.

Question: do the marked words (with the words right around them) form {definition}

Passage:
{passage}

Reply with one word and nothing else: YES, NO or UNCLEAR."""

# The judge's own known-answer items: written for this test, never from a corpus text.
JUDGE_CHECK = {
    "doubled_verb": (
        [
            "and he said unto them , [[ dying ye shall die ]] in the wilderness .",
            "[[ returning i will return ]] unto this place at the set time .",
            "[[ cursing they shall curse ]] him that sent them .",
            "[[ knowing thou shalt know ]] that thy seed shall be a stranger .",
            "[[ smiting he smote ]] the gate and it fell .",
            "for [[ visiting i will visit ]] you and bring you up .",
            "[[ remembering i do remember ]] my faults this day .",
            "[[ hearing they heard ]] and did not understand .",
            "[[ breaking i will break ]] the bands of their yoke .",
            "and [[ eating ye shall eat ]] and be satisfied .",
        ],
        [
            "and the men were [[ eating ; they ate ]] the bread in haste .",
            "he spake unto them , [[ saying say ]] unto the people that i come .",
            "she was [[ singing and she sang ]] all the night .",
            "the [[ offering he offered ]] was a lamb without blemish .",
            "the [[ building they built ]] stood a hundred years .",
            "and [[ going home he went ]] by the river .",
            "they were [[ weeping . they wept ]] for their father .",
            "the [[ blessing he blessed ]] them with was long remembered .",
            "the [[ dwelling they dwelt ]] in was made of stone .",
            "he was [[ reading , and read ]] it again in the morning .",
        ],
    ),
    "if_and": (
        [
            "[[ if thou wilt go with me , and i will go ]] ; but if not , i will stay .",
            "[[ if ye will hearken unto my voice , and ye shall eat ]] the good of the land .",
            "[[ if he find the stone , and he shall keep it ]] for his house .",
            "[[ if the people repent , and the lord will turn ]] away his anger .",
            "[[ if ye say unto the hill , depart , and it shall depart ]] .",
            "[[ if they come against us , and we will smite ]] them .",
            "[[ if she bear a son , and they shall call ]] his name after his father .",
            "[[ if i find there forty , and i will spare ]] the place .",
            "[[ if thou ask of me , and i will give thee ]] the land .",
            "[[ if the rain fall in its season , and the ground shall yield ]] her fruit .",
        ],
        [
            "[[ if ye do this , ye shall live , and ye shall ]] prosper in the land .",
            "[[ if he come , and if he see ]] the city , he will weep .",
            "[[ if ye repent , and ye keep my words ]] , then shall ye be blessed .",
            "[[ if it be so , then they will ]] go up to the mountain .",
            "they asked [[ if he would come , and he would ]] not answer them .",
            "[[ if he be willing , he will come , and they will ]] rejoice .",
            "[[ if the king hear it , he will be angry , and we shall ]] be slain .",
            "he wondered [[ if they were near , and they were ]] near indeed .",
            "[[ if thou wilt , thou canst , and i will ]] help thee besides .",
            "[[ if they fight , and we fight , then we shall ]] all perish .",
        ],
    ),
    "possessive_infinitive": (
        [
            "[[ in his going ]] down to the city he met the prophet .",
            "[[ at thy coming ]] the gates shall be opened .",
            "[[ after their returning ]] from the field they ate .",
            "[[ in the day of thy dying ]] thy sons shall mourn .",
            "[[ before his entering ]] into the house he washed .",
            "[[ upon her hearing ]] of the news she wept .",
            "[[ in our fleeing ]] from the enemy we lost the ark .",
            "[[ until thy departing ]] the people shall wait .",
            "[[ in the time of their sowing ]] the rain came .",
            "[[ by his rising ]] early he escaped the robbers .",
        ],
        [
            "[[ in his understanding ]] there was great wisdom .",
            "[[ at their dwelling ]] there was a well of water .",
            "[[ in her clothing ]] there was gold and silver .",
            "[[ by their having ]] much money they bought the field .",
            "[[ in his writing ]] the letters were large .",
            "[[ on their painting ]] the colours were bright .",
            "[[ by his drawing ]] the picture was improved .",
            "[[ in thy keeping ]] are the keys of the house .",
            "[[ at his pleasing ]] the king gave gifts .",
            "[[ in my learning ]] the books are many .",
        ],
    ),
}


def context(toks: list[str], a: int, b: int, width: int = 30) -> str:
    left = toks[max(0, a - width) : a]
    right = toks[b + 1 : b + 1 + width]
    return " ".join([*left, "[[", *toks[a : b + 1], "]]", *right])


def judge_jobs(cfg: dict, meas: dict, toks_of: dict, prefix: str = "") -> tuple[list[dict], dict]:
    """Questions for every candidate of the tested features in the given texts (seeded sample
    above the cap), plus the judge's known-answer items; and the key to the latter."""
    s = cfg["lab"]["translation2"]
    rng = random.Random(s["seed"])
    jobs, key = [], {}
    for f in TESTED:
        pos, neg = JUDGE_CHECK[f]
        for n, ex in enumerate(pos + neg):
            jid = f"check:{f}:{n}"
            key[jid] = "YES" if n < len(pos) else "NO"
            jobs.append({"id": jid, "prompt": PROMPT.format(definition=DEFINITIONS[f], passage=ex)})
        for name in sorted(toks_of):
            hits = meas[name].get("hits", {}).get(f, [])
            if len(hits) > s["judge_cap_per_text"]:
                hits = sorted(rng.sample(hits, s["judge_cap_per_text"]))
            for a, b in hits:
                passage = context(toks_of[name], a, b)
                jobs.append(
                    {
                        "id": f"{prefix}{f}|{name}|{a}",
                        "prompt": PROMPT.format(definition=DEFINITIONS[f], passage=passage),
                    }
                )
    rng.shuffle(jobs)
    return jobs, key


def parse_reply(reply: str) -> str | None:
    m = re.match(r"\W*(YES|NO|UNCLEAR)\b", (reply or "").strip(), re.I)
    return m.group(1).upper() if m else None


def judge_check(answers: dict[str, str | None], key: dict[str, str], bar: float) -> dict:
    res = {}
    for f in TESTED:
        ids = [i for i in key if i.startswith(f"check:{f}:")]
        got = [i for i in ids if answers.get(i) is not None]
        right = sum(answers[i] == key[i] for i in got)
        res[f] = {
            "items": len(ids),
            "answered": len(got),
            "right": right,
            "passes": len(got) == len(ids) and bool(ids) and right / len(ids) >= bar,
        }
    return res


# ----------------------------------------------------------------------------- step 1


def gutenberg_verses() -> dict[tuple[str, int, int], str]:
    heads = {
        "THE FIRST BOOK OF NEPHI": "1 Nephi", "THE SECOND BOOK OF NEPHI": "2 Nephi",
        "THE BOOK OF JACOB": "Jacob", "THE BOOK OF ENOS": "Enos", "THE BOOK OF JAROM": "Jarom",
        "THE BOOK OF OMNI": "Omni", "THE WORDS OF MORMON": "Words of Mormon",
        "THE BOOK OF MOSIAH": "Mosiah", "THE BOOK OF ALMA": "Alma",
        "THE BOOK OF HELAMAN": "Helaman", "THIRD BOOK OF NEPHI": "3 Nephi",
        "FOURTH NEPHI": "4 Nephi", "THE BOOK OF MORMON": "Mormon", "THE BOOK OF ETHER": "Ether",
        "THE BOOK OF MORONI": "Moroni",
    }  # fmt: skip
    res: dict[tuple[str, int, int], str] = {}
    book, cur, started = None, None, False
    for line in GUTENBERG.read_text(encoding="utf-8", errors="replace").splitlines():
        st = line.strip()
        m = re.match(r"^(.+) Chapter (\d+)$", st)
        if m:
            book, started = m.group(1), True
            continue
        if started or st.startswith("THE FIRST BOOK OF NEPHI HIS REIGN"):
            for h, b in heads.items():
                if st.startswith(h) and (started or b == "1 Nephi"):
                    book, started = b, True
        v = re.match(r"^(\d+):(\d+) (.*)$", st)
        if v and book:
            cur = (book, int(v.group(1)), int(v.group(2)))
            res[cur] = v.group(3)
        elif st and cur and not st.isupper() and not m:
            res[cur] += " " + st
        elif not st:
            cur = None
    return res


def parse_ref(ref: str) -> tuple[str, int, list[int]]:
    m = re.match(r"^(.+) (\d+):(\d+)(?:-(\d+))?$", ref)
    book, ch, v1 = m.group(1), int(m.group(2)), int(m.group(3))
    v2 = int(m.group(4)) if m.group(4) else v1
    return book, ch, list(range(v1, v2 + 1))


def books_1830() -> dict[str, tuple[list[str], list[bool], list[str], list[int]]]:
    """1830 body text by book: words, whether each lies in a King James passage, the tokens
    with punctuation, and each word's token index."""
    from kjv_mask.run import artifacts

    spans = {}
    for r in map(json.loads, MASK.read_text().splitlines()):
        spans[r["id"]] = sorted((sp["start"], sp["end"]) for sp in r["spans"])
    res: dict[str, tuple[list[str], list[bool], list[str], list[int]]] = {}
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if not r.get("book") or r.get("kind") != "body":
            continue
        text = artifacts(r["text"])[0]
        w, k, tk, wi = res.setdefault(r["book"], ([], [], [], []))
        pos = 0
        for a, b in spans.get(f"bom:{r['seq']}", []) + [(len(text), len(text))]:
            for seg, flag in ((text[pos:a], False), (text[a:b], True)):
                for t in tokens(seg):
                    if t not in PUNCT:
                        w.append(t)
                        k.append(flag)
                        wi.append(len(tk))
                    tk.append(t)
            pos = b
        tk.append(".")
    return res


def grams(ws: list[str], n: int) -> dict[tuple[str, ...], list[int]]:
    idx: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for i in range(len(ws) - n + 1):
        idx[tuple(ws[i : i + n])].append(i)
    return idx


def locate(vw: list[str], idx: dict, n: int) -> tuple[float, int, int]:
    """Where a verse sits in a text: (share of its n-grams in one place, start, end)."""
    gs = [tuple(vw[i : i + n]) for i in range(len(vw) - n + 1)]
    if not gs:
        return 0.0, -1, -1
    votes: Counter = Counter()
    for i, g in enumerate(gs):
        for p in idx.get(g, ()):
            votes[(p - i) // 8] += 1
    if not votes:
        return 0.0, -1, -1
    best = max(votes, key=lambda o: votes[o] + votes.get(o - 1, 0) + votes.get(o + 1, 0))
    near = {best - 1, best, best + 1}
    pos = [p for i, g in enumerate(gs) for p in idx.get(g, ()) if (p - i) // 8 in near]
    score = min(1.0, sum(votes[o] for o in near) / len(gs))
    return round(score, 3), min(pos), max(pos) + n


def contains(hay: list[str], needle: list[str]) -> bool:
    k = len(needle)
    return k > 0 and any(hay[i : i + k] == needle for i in range(len(hay) - k + 1))


def ms_words(path: Path) -> list[str] | None:
    try:
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    except OSError:
        return None
    text = " ".join(r.get("text") or "" for r in sorted(rows, key=lambda r: r["page"]))
    return words(text.replace("&amp;", " and ").replace("&", " and "))


def if_then_count(ws: list[str], window: int) -> int:
    return sum(1 for i, w in enumerate(ws) if w == "if" and "then" in ws[i + 1 : i + 1 + window])


def bible_reading(verse: str, s: dict) -> str:
    tk = tokens(verse)
    if "if" not in tk:
        return "no_if"
    after = tk[tk.index("if") :]
    if "then" in after:
        return "then"
    return "and" if if_and(tk, s["if_and_max_words"]) else "neither"


def step1(cfg: dict) -> tuple[dict, dict]:
    s = cfg["lab"]["translation2"]
    cites = json.loads(CITATIONS.read_text())
    gut = gutenberg_verses()
    b30 = books_1830()
    n = s["verse_ngram"]
    idx = {b: grams(v[0], n) for b, v in b30.items()}
    om, pm = ms_words(JSP_OM), ms_words(JSP_PM)
    ms_idx = {k: grams(v, n) for k, v in (("original", om), ("printers", pm)) if v}
    items, public = [], []
    for it in cites["items"]:
        pub = {k: v for k, v in it.items() if k not in ("phrase",)}
        public.append(pub)
        row = {k: it.get(k) for k in ("id", "source", "feature", "kind", "ref")}
        held = cites["sources"][it["source"]]["held"]
        if not held or it["kind"] == "not_held":
            row["status"] = "source_not_held"
            items.append(row)
            continue
        if it["kind"] in ("phrase", "count", "if_and"):
            book, ch, vs = parse_ref(it["ref"])
            mod = " ".join(gut.get((book, ch, v), "") for v in vs)
            mw = words(mod)
            if not mw or book not in b30:
                row["status"] = "verse_not_found"
                items.append(row)
                continue
            score, a, b = locate(mw, idx[book], n)
            row["match"] = score
            if score < s["verse_match_min"]:
                row["status"] = "verse_not_found"
                items.append(row)
                continue
            w30, k30, tk30, wi30 = b30[book]
            a2, b2 = max(0, a - 5), min(len(w30), b + 5)
            span = w30[a2:b2]
            row["in_kjv_passage"] = sum(k30[a:b]) > (b - a) / 2
            if it["kind"] == "count":
                row["claimed"] = it["claimed"]
                row["modern_count"] = mw.count(it["word"])
                row["count_1830"] = w30[a:b].count(it["word"])
                row["status"] = (
                    "reproduced" if row["modern_count"] == it["claimed"] else "not_reproduced"
                )
            else:
                ph = words(it["phrase"])
                in30, inmod = contains(span, ph), contains(mw, ph)
                row["status"] = (
                    "reproduced" if in30 else "differs_in_1830" if inmod else "not_reproduced"
                )
                if not in30:  # how close the 1830 verse comes to the wording (0-100), no bar
                    row["closest_1830"] = round(fuzz.partial_ratio(" ".join(ph), " ".join(span)), 1)
            if it["kind"] == "if_and":
                ph = words(it["phrase"])
                row["expected_in_1830"] = it["in_1830"]
                row["in_1830"] = contains(span, ph)
                ta, tb = wi30[a2], wi30[min(b2, len(wi30)) - 1] + 1
                row["rule_finds_1830"] = bool(if_and(tk30[ta:tb], s["if_and_max_words"]))
                # Manuscript spelling differs ("a cursed", "geteth"): look for the "and" that opens
                # the result clause with its next three words only.
                last = max(i for i, w in enumerate(ph) if w == "and")
                tail = ph[last : last + 4]
                for msn, ws in (("original", om), ("printers", pm)):
                    if not ws:
                        row[msn] = "not_attempted"
                        continue
                    sc, ma, mb = locate(mw, ms_idx[msn], n)
                    if sc < s["verse_match_min"]:
                        row[msn] = "verse_not_found"
                    else:
                        row[msn] = (
                            "has_and" if contains(ws[max(0, ma - 8) : mb + 8], tail) else "no_and"
                        )
                ok = row["in_1830"] == it["in_1830"]
                row["status"] = "reproduced" if ok else "not_reproduced"
        elif it["kind"] == "book_count":
            all30 = [w for b in b30.values() for w in b[0]]
            allmod = words(" ".join(gut.values()))
            row["claimed"] = it["claimed"]
            row["count_1830"] = {k: _count(all30, words(k)) for k in it["claimed"]}
            row["modern_count"] = {k: _count(allmod, words(k)) for k in it["claimed"]}
            row["status"] = (
                "reproduced"
                if row["count_1830"] == it["claimed"] or row["modern_count"] == it["claimed"]
                else "not_reproduced"
            )
        elif it["kind"] == "manuscript_count":
            all30 = [w for b in b30.values() for w in b[0]]
            row["claimed"] = it["claimed"]
            row["if_then"] = {
                "original": if_then_count(om, s["if_then_window"]) if om else None,
                "printers": if_then_count(pm, s["if_then_window"]) if pm else None,
                "edition_1830": if_then_count(all30, s["if_then_window"]),
            }
            row["status"] = "counted (critic's figure unconfirmed: source not held)"
        elif it["kind"] == "bible_if_and":
            kjv = kjv_verses()
            ylt = ylt_verses(Path(s["texts"]["young_literal"])) or {}
            reads = {"kjv": Counter(), "young": Counter()}
            for ref in it["refs"]:
                book, ch, vs = parse_ref(ref)
                key = f"Gen.{ch}.{vs[0]}"
                reads["kjv"][bible_reading(kjv.get(key, ""), s)] += 1
                reads["young"][bible_reading(ylt.get(key, ""), s)] += 1
            row["claimed"] = it["claimed"]
            row["readings"] = {k: dict(v) for k, v in reads.items()}
            row["status"] = (
                "reproduced"
                if all(v.get("and", 0) == 0 for v in reads.values())
                else "not_reproduced"
            )
        items.append(row)
    summary: dict = defaultdict(Counter)
    for r in items:
        summary[r["source"]][r["status"]] += 1
    res = {
        "config_sha256": config.sha256_of_config(),
        "commit": _commit(),
        "settings": {k: s[k] for k in ("verse_ngram", "verse_match_min", "if_then_window")},
        "summary": {k: dict(v) for k, v in summary.items()},
        "items": items,
    }
    return res, {"note": cites["note"].split(" 'phrase'")[0], "sources": cites["sources"],
                 "items": public}  # fmt: skip


def _count(ws: list[str], ph: list[str]) -> int:
    k = len(ph)
    return sum(1 for i in range(len(ws) - k + 1) if ws[i : i + k] == ph)


def _commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()


# ----------------------------------------------------------------------------- commands


def run(cfg: dict, workers: int) -> dict:
    s = cfg["lab"]["translation2"]
    inv, sheet = inventory(cfg)
    with out(CARD / "retention_hand_check.jsonl").open("w") as fh:
        for r in sheet:
            fh.write(json.dumps({**r, "hand_kept": None}, ensure_ascii=False) + "\n")
    meas, toks_of, info = gather(cfg, workers)
    plants = plant_check(" ".join(T1.kjv_text("NT").split()[:20000]), s, s["seed"])
    chk = check(cfg, meas, inv)
    ot = {f: 1e4 * meas["kjv_ot"][f] / meas["kjv_ot"]["words"] for f in FEATURES}
    chk["K4"] = k4(cfg, toks_of, chk["K1"]["kept"], ot)
    chk["K3"] = {"decided": False, "reason": "hand check of precision and the judge are pending"}
    chk["planted"] = plants
    chk["rule_check_passes_K1_K2_K4"] = all(
        [chk["K1"]["passes"], chk["K2"]["passes"], chk["K4"]["passes"], all(plants.values())]
    )
    jobs, key = judge_jobs(cfg, meas, toks_of)
    with out(CARD / "judge_jobs_v2.jsonl").open("w") as fh:
        for j in jobs:
            fh.write(json.dumps(j, ensure_ascii=False) + "\n")
    out(CARD / "judge_check_key_v2.json").write_text(json.dumps(key, indent=1) + "\n")
    hand = []
    rng = random.Random(s["seed"])
    for f in TESTED:
        cands = [j for j in jobs if j["id"].startswith(f + "|")]
        for j in sorted(
            rng.sample(cands, min(len(cands), s["precision_hand"])), key=lambda x: x["id"]
        ):
            passage = j["prompt"].split("Passage:\n")[1].split("\n\n")[0]
            hand.append({"id": j["id"], "passage": passage, "hand": None})
    with out(CARD / "precision_hand_check.jsonl").open("w") as fh:
        for h in hand:
            fh.write(json.dumps(h, ensure_ascii=False) + "\n")
    kept = chk["K1"]["kept"]
    groups = {}
    for name, m in sorted(meas.items()):
        row = rate_row(m)
        row["composite"] = composite(m, kept, ot, s["ot_floor"])
        row["composite_ci"] = composite_ci(m, kept, ot, s["ot_floor"])
        groups[name] = row
    groups["imitations_pooled"] = rate_row(pooled([meas[k] for k in imitation_names(meas)]))
    groups["js_dictated_pooled"] = rate_row(
        pooled([meas["js:" + k] for k in s["js_dictated"] if "js:" + k in meas])
    )
    groups["js_own_hand_pooled"] = rate_row(
        pooled([meas["js:" + k] for k in s["js_own_hand"] if "js:" + k in meas])
    )
    for g in ("imitations_pooled", "js_dictated_pooled", "js_own_hand_pooled"):
        mm = {"words": groups[g]["words"], **{f: groups[g][f]["n"] for f in FEATURES}}
        groups[g]["composite"] = composite(mm, kept, ot, s["ot_floor"])
        groups[g]["composite_ci"] = composite_ci(mm, kept, ot, s["ot_floor"])
    res = {
        "config_sha256": config.sha256_of_config(),
        "commit": _commit(),
        "settings": {k: v for k, v in s.items() if k != "texts"},
        "book_of_mormon": "not scored: K3 (hand check, judge) is pending; see the card",
        "inventory": inv,
        "check": chk,
        "groups": groups,
        "prose_per_work_median": info.get("prose_median"),
        "ids": {k: info[k]["ids"] for k in ("prose", "emode", "non_semitic")},
        "unreadable": {k: info[k]["unreadable"] for k in ("prose", "emode", "non_semitic")},
        "not_attempted": info["not_attempted"],
        "judge_jobs": {
            "questions": len(jobs),
            "check_items": len(key),
            "by_feature": dict(Counter(_feature_of(j["id"]) for j in jobs)),
        },
        "hand_sheets": {"retention": len(sheet), "precision": len(hand)},
    }
    out(OUT / "inventory_v2.json").write_text(json.dumps(inv, indent=1) + "\n")
    out(OUT / "check_v2.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def _feature_of(jid: str) -> str:
    return jid.split(":")[1] if jid.startswith("check:") else jid.split("|")[0]


def answers(cfg: dict) -> dict:
    """The judge's check, precision by feature and text, and the hand checks as far as filled."""
    s = cfg["lab"]["translation2"]
    ans_path = CARD / "judge_answers_v2.jsonl"
    key = json.loads((CARD / "judge_check_key_v2.json").read_text())
    got: dict[str, str | None] = {}
    if ans_path.exists():
        for line in ans_path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                got[r["id"]] = parse_reply(r["reply"])
    jc = judge_check(got, key, s["judge_check_bar"])
    prec: dict = defaultdict(lambda: {"asked": 0, "yes": 0, "no": 0, "unclear": 0})
    for jid, a in got.items():
        if "|" not in jid or a is None:
            continue
        f, name, _ = jid.split("|")
        p = prec[f"{f}|{name}"]
        p["asked"] += 1
        p[a.lower()] += 1
    hand = {}
    hp = CARD / "precision_hand_check.jsonl"
    if hp.exists():
        rows = [json.loads(x) for x in hp.read_text().splitlines() if x.strip()]
        for f in TESTED:
            done = [r for r in rows if r["id"].startswith(f + "|") and r["hand"] is not None]
            hand[f] = {
                "read": len(done),
                "precision": round(sum(bool(r["hand"]) for r in done) / len(done), 4)
                if done
                else None,
                "passes": len(done) >= s["precision_hand"]
                and sum(bool(r["hand"]) for r in done) / len(done) >= s["precision_bar"],
            }
    res = {
        "config_sha256": config.sha256_of_config(),
        "simulated_judging": "every judge answer is simulated judging by an AI model",
        "judge_check": jc,
        "judge_check_passes": all(v["passes"] for v in jc.values()),
        "precision_by_text": dict(prec),
        "hand_precision": hand,
        "K3_passes": bool(hand) and all(v["passes"] for v in hand.values()),
    }
    out(OUT / "answers_v2.json").write_text(json.dumps(res, indent=1) + "\n")
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["step1", "run", "answers", "score"])
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "step1":
        res, public = step1(cfg)
        out(OUT / "citations_v2.json").write_text(json.dumps(public, indent=1) + "\n")
        out(OUT / "step1_v2.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res["summary"], indent=1))
        return 0
    if a.cmd == "run":
        res = run(cfg, a.workers)
        print(json.dumps({k: res["check"][k] for k in ("K1", "K2", "K4", "planted")}, indent=1))
        return 0
    if a.cmd == "answers":
        print(json.dumps(answers(cfg), indent=1)[:4000])
        return 0
    # score: refuses unless the binding check (judge check, K3, and K1 K2 K4) has passed.
    ans = OUT / "answers_v2.json"
    chk = OUT / "check_v2.json"
    ok = (
        ans.exists()
        and chk.exists()
        and json.loads(ans.read_text()).get("judge_check_passes")
        and json.loads(ans.read_text()).get("K3_passes")
        and json.loads(chk.read_text())["check"].get("rule_check_passes_K1_K2_K4")
    )
    if not ok:
        print("not scored: the known-answer check (K1-K4, judge check) has not passed")
        return 1
    print(
        "check passed: the verified recount of K1, K2 and K4 and the Book of Mormon jobs are next"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
