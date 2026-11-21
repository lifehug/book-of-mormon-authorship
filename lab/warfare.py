"""BOM-115: weapons, armour, fortifications, organisation and the size of armies in war narrative.

War passages are found by one rule in every text (fixed windows of words whose share of seed war
words reaches a threshold set on known war and non-war texts). A fixed term list by class is then
counted inside those windows, per 10,000 war words. Each text is placed with the tradition whose
profile (built without it) it is nearest: the Bible and Josephus; the American wars of 1775-1815;
1810s-1820s writing on mound-builder earthworks; accounts of the conquest of Mexico; native annals
in English. The known-answer check (held-out texts land with their own tradition) comes first and
the Book of Mormon is not scored if it misses its bar. The fortification passage of the 1830 text
(found by its words) and a five-word fortification cluster are then looked up in every text and in
a seeded library sample. The test card, written first, is
``data/private/lab/owner/2026-11-20-warfare/card.md``; settings are ``lab.warfare`` in the config.
The output holds term names, counts and rates, no text. The meaning-index step of the issue is
not done here.

Usage::

    python -m lab.warfare check     # window rule and held-out placement only (no Book of Mormon)
    python -m lab.warfare run       # everything -> data/lab/setting/warfare/result.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import subprocess
from bisect import bisect_right
from collections import Counter
from pathlib import Path

import numpy as np

from lab import door, registry
from lab.numbers import (
    EDITION,
    LABELS,
    REFERENCE,
    TOKEN,
    UNIT_OF,
    WORDS,
    _bilingual,
    _file,
    _josephus,
    _library,
    _phrase,
)
from lab.paths import REGISTRY, out
from lab.wherefore import QUOTED
from metadata import config

OUT = REGISTRY / "setting" / "warfare"
KJV = Path("data/kjv/kjv.jsonl")
CAND = Path("data/candidates/text")
SETTING = Path("data/corpus/lab/sources/setting")

# ------------------------------------------------------------------------------------ term list
# Whole-word regexes on the lower-cased text, words joined by single spaces (hyphens are gone).
_EARTH = r"(?:earth|dirt)"
TERMS: dict[str, dict[str, str]] = {
    "weapons": {
        "sword": r"\bswords?\b",
        "cimeter": r"\b(?:cimeters?|scimitars?|scimeters?|scymitars?|simitars?|cimiters?)\b",
        "bow": r"\bbows?\b(?! (?:down|before|the knee|themselves|himself|ourselves|myself|thy))",
        "arrow": r"\barrows?\b",
        "sling": r"\b(?:slings?|slingers?)\b",
        "stone": r"\bstones?\b",
        "spear": r"\bspears?\b",
        "javelin": r"\bjavelins?\b",
        "dart": r"\bdarts?\b",
        "club": r"\bclubs?\b",
        "axe": r"\baxes?\b",
        "dagger": r"\bdaggers?\b",
        "musket": r"\b(?:muskets?|musketry|firelocks?|fusils?)\b",
        "cannon": r"\b(?:cannons?|cannonade|cannon balls?)\b",
        "gun": r"\bguns?\b",
        "bayonet": r"\bbayonets?\b",
        "tomahawk": r"\btomahawks?\b",
        "macana": r"\b(?:macanas?|maquahuitl)\b",
        "lance": r"\blances?\b",
        "pike": r"\bpikes?\b",
        "weapon": r"\b(?:weapons?|instruments? of war|implements? of war)\b",
    },
    "armour": {
        "breastplate": r"\bbreast plates?\b|\bbreastplates?\b",
        "shield": r"\b(?<!arm )shields?\b",
        "arm_shield": r"\barm shields?\b",
        "buckler": r"\bbucklers?\b",
        "helmet": r"\b(?:helmets?|helms?)\b",
        "head_plate": r"\b(?:head plates?|headplates?|headpieces?|head pieces?)\b",
        "thick_clothing": r"\bthick (?:clothing|garments?|clothes)\b",
        "quilted_or_cotton_armour": r"\b(?:quilted|cotton armou?r|escaupil\w*)\b",
        "coat_of_mail": r"\b(?:coats? of mail|habergeons?|cuirass(?:es)?|corslets?|brigandines?)\b",
        "armour": r"\b(?:armou?rs?|armou?red)\b",
    },
    "fortification": {
        "ditch": r"\bditch(?:es)?\b",
        "trench": r"\btrench(?:es)?\b",
        "intrenchment": r"\b(?:intrenchments?|entrenchments?|intrenched|entrenched)\b",
        "bank_or_ridge_of_earth": rf"\b(?:banks?|ridges?) of {_EARTH}\b|\bembankments?\b",
        "heap_of_earth": rf"\bheaps? of {_EARTH}\b",
        "wall_of_earth": r"\bwalls? of (?:earth|dirt|clay|turf|sod)\b",
        "wall_of_stone": r"\bwalls? of (?:stones?|rock|brick)\b|\bstone walls?\b",
        "timbers": r"\btimbers?\b",
        "picket": r"\b(?:pickets?|picketed)\b",
        "palisade": r"\b(?:palisades?|palisadoe?s?|palisaded|stockades?|stockaded)\b",
        "breastwork": r"\bbreast works?\b|\bbreastworks?\b",
        "tower": r"\btowers?\b",
        "gate": r"\bgates?\b",
        "place_of_entrance": r"\bplaces? of entrance\b",
        "fort": r"\b(?:forts?|fortress(?:es)?)\b",
        "fortification": r"\bfortif(?:y|ied|ies|ication|ications|ying)\b",
        "garrison": r"\bgarrisons?\b|\bgarrisoned\b",
        "stronghold": r"\bstrong holds?\b|\bstrongholds?\b",
        "rampart": r"\bramparts?\b",
        "parapet": r"\bparapets?\b",
        "bulwark": r"\bbulwarks?\b",
        "moat": r"\b(?:moats?|fosse)\b",
        "mound": r"\b(?:mounds?|tumulus|tumuli)\b",
        "wall": r"\bwalls?\b",
        "place_of_security": r"\bplaces? of (?:security|safety|refuge|retreat|defen[cs]e)\b",
    },
    "organisation": {
        "captain": r"\b(?<!chief )captains?\b",
        "chief_captain": r"\bchief captains?\b",
        "commander": r"\bcommanders?\b",
        "standard": r"\bstandards?\b",
        "ensign": r"\bensigns?\b",
        "banner": r"\bbanners?\b",
        "title_of_liberty": r"\btitles? of liberty\b",
        "flag": r"\b(?<!white )flags?\b(?! of truce)",
        "flag_of_truce": r"\b(?:flags? of truce|white flags?)\b",
        "trumpet": r"\b(?:trumpets?|trumpeters?)\b",
        "spy": r"\b(?:spy|spies)\b",
        "stratagem": r"\bstratagems?\b",
        "decoy": r"\bdecoy(?:s|ed)?\b",
        "ambush": r"\b(?:ambush(?:es|ed|ment)?|ambuscades?|ambuscaded?|lying in wait)\b",
        "epistle": r"\bepistles?\b",
        "treaty": r"\b(?:treaty|treaties)\b",
        "tribute": r"\btribute\b",
        "horse": r"\b(?:horses?|horsemen|cavalry)\b",
        "chariot": r"\bchariots?\b",
        "footmen": r"\bfootmen\b",
        "modern_unit": r"\b(?:regiments?|battalions?|brigades?|militia|regulars|infantry"
        r"|artillery)\b",
        "legion": r"\b(?:legions?|cohorts?)\b",
    },
    "prisoners": {
        "prisoner": r"\bprisoners?\b",
        "captive": r"\b(?:captives?|captivity)\b",
        "ransom": r"\bransom(?:ed|s)?\b",
        "spared": r"\b(?:spare|spared|sparing)\b",
        "put_to_death": r"\b(?:put to death|put to the sword|massacred?)\b",
        "sacrificed": r"\bsacrific\w*\b",
        "slave": r"\b(?:slaves?|slavery|bondage|servitude)\b",
    },
    "time": {
        "month_named": r"\b(?:january|february|april|june|july|august|september|october"
        r"|november|december)\b",
        "ordinal_month": r"\b(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth"
        r"|tenth|eleventh|twelfth) months?\b",
        "season": r"\b(?:spring|summer|autumn|winter|harvest|seed time)\b",
        "regnal_year": r"\b(?:\w+ )?years? of (?:the )?(?:reign|king|judges)\b",
    },
}
CLASSES = list(TERMS)
NAMES = [(c, n) for c in CLASSES for n in TERMS[c]]
TERM_INDEX = {n: i for i, (_, n) in enumerate(NAMES)}
RX = {n: re.compile(rx) for c in CLASSES for n, rx in TERMS[c].items()}

# The cluster of the fortification passage: five groups, all within one window.
CLUSTER = {
    "ditch": r"\b(?:ditch(?:es)?|trench(?:es)?)\b",
    "bank": rf"\b(?:banks?|ridges?|heaps?|mounds?) of {_EARTH}\b|\bembankments?\b",
    "timbers": r"\btimbers?\b",
    "pickets": r"\b(?:pickets?|picketed|palisad\w*|stockad\w*)\b",
    "towers": r"\btowers?\b",
}
CRX = {n: re.compile(rx) for n, rx in CLUSTER.items()}
# The words that find the passage in the 1830 text.
PASSAGE = [r"\bheaps of earth\b", r"\btimbers\b", r"\bpickets\b", r"\btowers\b"]
ARMY_WORDS = {"army", "armies", "forces", "troops", "host"}
TRADITIONS = ["near_east", "american_wars", "mound_builder", "conquest_mexico", "native_annals"]
KNOWN_PEACE = ("kjv_new_testament", "kjv_job_to_song")
KNOWN_WAR = ("josephus_wars_whiston", "ramsay_revolution_v1", "ramsay_revolution_v2")


# ------------------------------------------------------------------------------------ the texts


def _kjv_books(codes: tuple[str, ...] | None, section: str | None = None) -> str | None:
    raw = _file(KJV)
    if raw is None:
        return None
    rows = [json.loads(x) for x in raw.splitlines()]
    keep = [r["text"] for r in rows if (codes and r["book"] in codes) or r["section"] == section]
    return "\n".join(keep) or None


def _kjv_range(first: str, last: str) -> str | None:
    """Every verse from the first verse of ``first`` to the last verse of ``last``."""
    raw = _file(KJV)
    if raw is None:
        return None
    rows = [json.loads(x) for x in raw.splitlines()]
    books = [r["book"] for r in rows]
    a, b = books.index(first), len(books) - 1 - books[::-1].index(last)
    return "\n".join(r["text"] for r in rows[a : b + 1])


def _setting(name: str) -> str | None:
    return _file(SETTING / name / "text.txt")


def _atwater() -> str | None:
    raw = door_text("institutional_books:32044011019148")
    if raw is None:
        return None
    a = re.search(r"DESCRIPTION,? &c\.?\s+OUR\s+Antiquities", raw)
    b = re.search(r"Drawings of Ornaments and\s+Domestick Utensils", raw)
    return raw[a.start() : b.start()] if a and b and a.start() < b.start() else None


_CAT: dict[str, dict] = {}
_IA = "internet_archive:bim_eighteenth-century_"
LIBRARY_IDS = {
    "ramsay_revolution_v1": _IA + "the-history-of-the-ameri_ramsay-david_1789_1",
    "ramsay_revolution_v2": _IA + "the-history-of-the-ameri_ramsay-david_1789_2",
    "warren_history_v1": "institutional_books:HW3C2P",
    "warren_history_v2": "institutional_books:HXJ2KP",
    "warren_history_v3": "institutional_books:HXJ2KN",
    "wilson_military_naval_heroes_1817": "institutional_books:HWB41W",
    "eaton_life_of_jackson_1817": "institutional_books:HX66LU",
    "naval_temple_1816": "institutional_books:HX4VD4",
    "haywood_tennessee_1823": "internet_archive:naturalaborigina00hayw",
    "yates_moulton_new_york_1824": "institutional_books:HX4MJF",
    "clavigero_mexico_1787_v1": _IA + "the-history-of-mexico-c_clavigero-francesco-sav_1787_1",
    "clavigero_mexico_1787_v2": _IA + "the-history-of-mexico-c_clavigero-francesco-sav_1787_2",
    "archaeologia_americana_v1": "institutional_books:32044011019148",
}


def door_text(work_id: str) -> str | None:
    """A library work's text by id; None (not attempted) if it is not catalogued or unreadable."""
    if not _CAT:
        _CAT.update(door.catalog(set(LIBRARY_IDS.values())))
    row = _CAT.get(work_id)
    return None if row is None else _library(row)


def lib(key: str) -> str | None:
    return door_text(LIBRARY_IDS[key])


def tradition_texts(cfg: dict) -> list[tuple[str, str | None, str | None]]:
    """(name, tradition or None for a control, raw text or None if not attempted)."""
    near, amer, mound, conq, native = TRADITIONS
    rows = [
        ("kjv_joshua_judges", near, _kjv_books(("JOS", "JDG"))),
        ("kjv_samuel", near, _kjv_books(("1SA", "2SA"))),
        ("kjv_kings", near, _kjv_books(("1KI", "2KI"))),
        ("kjv_chronicles", near, _kjv_books(("1CH", "2CH"))),
        ("kjv_maccabees", near, _kjv_books(("1MA", "2MA"))),
        ("josephus_antiquities_whiston", near, _josephus("josephus_antiquities_whiston.txt")),
        ("josephus_wars_whiston", near, _josephus("josephus_wars_whiston.txt")),
        ("ramsay_revolution_v1", amer, lib("ramsay_revolution_v1")),
        ("ramsay_revolution_v2", amer, lib("ramsay_revolution_v2")),
        ("warren_history_v1", amer, lib("warren_history_v1")),
        ("warren_history_v2", amer, lib("warren_history_v2")),
        ("warren_history_v3", amer, lib("warren_history_v3")),
        ("wilson_military_naval_heroes_1817", amer, lib("wilson_military_naval_heroes_1817")),
        ("eaton_life_of_jackson_1817", amer, lib("eaton_life_of_jackson_1817")),
        ("naval_temple_1816", amer, lib("naval_temple_1816")),
        ("atwater_archaeologia_americana_1820", mound, _atwater()),
        ("priest_american_antiquities_1833", mound, _setting("americanantiquit01prie")),
        ("priest_wonders_1826", mound, _setting("wondersnaturean00priegoog")),
        ("clinton_discourse_1811", mound, _setting("discoursedel00clinton")),
        ("clinton_memoir_western_new_york", mound, _setting("westernpartsstate00clinrich")),
        ("haywood_tennessee_1823", mound, lib("haywood_tennessee_1823")),
        ("yates_moulton_new_york_1824", mound, lib("yates_moulton_new_york_1824")),
        ("view_of_the_hebrews_1825", mound, _file(CAND / "es-1825-view-of-the-hebrews.txt")),
        ("diaz_conquest_keatinge_1800", conq, _setting("truehistoryofcon00dauoft")),
        ("solis_conquest_1724", conq, _setting("historyofconques00sols")),
        ("clavigero_mexico_1787_v1", conq, lib("clavigero_mexico_1787_v1")),
        ("clavigero_mexico_1787_v2", conq, lib("clavigero_mexico_1787_v2")),
        ("robertson_america_1812_v1", conq, _setting("historyofamerica01roberich")),
        ("robertson_america_1812_v2", conq, _setting("historyofamerica02roberich")),
        ("brinton_annals_cakchiquels_1885", native, _bilingual(
            "brinton_annals_cakchiquels_1885.txt", r"THE ANNALS", r"NOTES\.|VOCABULARY\.", cfg,
            indented=True)),
        ("brinton_maya_chronicles_1882", native, _bilingual(
            "brinton_maya_chronicles_1882.txt", r"TRANSLATION\.|CONQUEST AND MAP\.",
            r"NOTES\.|VOCABULARY\.", cfg)),
        ("cusick_sketches_1827", native, _setting("Ayer_251_I611_C9_1827")),
        ("spalding_manuscript_story_1885", None, _file(CAND / "ss-manuscript-story-1885.txt")),
        ("late_war_1816", None, _file(CAND / "gh-1816-late-war.txt")),
        # known-answer sets for the window rule only (in no tradition)
        ("kjv_new_testament", "peace", _kjv_books(None, "NT")),
        ("kjv_job_to_song", "peace", _kjv_range("JOB", "SOL")),
    ]  # fmt: skip
    return rows


# ------------------------------------------------------------------------------- preparing a text


def vocabulary(cfg: dict) -> Counter:
    """Words of the King James text and Josephus, for the long-s repair."""
    w = cfg["lab"]["warfare"]
    c: Counter = Counter()
    sources = [_kjv_books(None, "OT"), _kjv_books(None, "NT")]
    sources += [_josephus(f"josephus_{k}_whiston.txt") for k in ("wars", "antiquities")]
    for raw in sources:
        if raw:
            c.update(re.findall(r"[a-z]+", raw.lower()))
    return Counter({k: v for k, v in c.items() if v >= w["vocab_min_count"]})


def repair_long_s(raw: str, vocab: Counter) -> str:
    """Turn a long-s misread (f for s) into the vocabulary word it stands for; real words stay."""
    memo: dict[str, str] = {}

    def fix(m: re.Match) -> str:
        w = m.group(0).lower()
        if w in memo:
            return memo[w]
        got = w
        if "f" in w and w not in vocab and w.count("f") <= 6:
            at = [i for i, ch in enumerate(w) if ch == "f"]
            best = 0
            for mask in range(1, 1 << len(at)):
                v = list(w)
                for k, i in enumerate(at):
                    if mask >> k & 1:
                        v[i] = "s"
                v = "".join(v)
                if vocab.get(v, 0) > best:
                    best, got = vocab[v], v
        memo[w] = got
        return got

    return re.sub(r"[A-Za-z]+", fix, raw.replace("ſ", "s"))


class Prep:
    """One text ready for counting: words, the joined string, and where each word starts."""

    def __init__(self, name: str, raw: str, cfg: dict, vocab: Counter) -> None:
        w = cfg["lab"]["warfare"]
        words = re.findall(r"[a-z]+", raw.lower())
        marks = sum(words.count(m) for m in w["long_s_markers"])
        self.repaired = marks * 10000 >= w["long_s_per_10k"] * max(len(words), 1)
        if self.repaired:
            raw = repair_long_s(raw, vocab)
            words = re.findall(r"[a-z]+", raw.lower())
        self.name, self.raw, self.words = name, raw, words
        self.joined = " ".join(words)
        starts, pos = [], 0
        for x in words:
            starts.append(pos)
            pos += len(x) + 1
        self.starts = starts

    def positions(self, rx: re.Pattern) -> list[int]:
        return [bisect_right(self.starts, m.start()) - 1 for m in rx.finditer(self.joined)]


def window_matrix(prep: Prep, rxs: dict[str, re.Pattern], size: int) -> np.ndarray:
    """Rows: patterns in order; columns: whole windows; cells: matches in that window."""
    n = len(prep.words) // size
    mat = np.zeros((len(rxs), n), dtype=int)
    for i, rx in enumerate(rxs.values()):
        pos = np.array(prep.positions(rx), dtype=int)
        pos = pos[pos < n * size] // size
        if len(pos):
            mat[i] = np.bincount(pos, minlength=n)
    return mat


def seed_density(prep: Prep, cfg: dict) -> np.ndarray:
    """Share of seed war words in each whole window."""
    w = cfg["lab"]["warfare"]
    size = w["window_words"]
    seeds = set(w["seed_words"])
    n = len(prep.words) // size
    hit = np.array([x in seeds for x in prep.words[: n * size]], dtype=int)
    return hit.reshape(n, size).sum(axis=1) / size if n else np.zeros(0)


# ------------------------------------------------------------------------------------ the rule


def pick_threshold(dens: dict[str, np.ndarray], cfg: dict) -> dict:
    """Smallest grid value with at most ``fpr_max`` of non-war windows; war windows then checked."""
    w = cfg["lab"]["warfare"]
    peace = np.concatenate([dens[k] for k in KNOWN_PEACE if k in dens] or [np.zeros(0)])
    war = np.concatenate([dens[k] for k in KNOWN_WAR if k in dens] or [np.zeros(0)])
    table = []

    def share(x: np.ndarray, t: float) -> float | None:
        return round(float((x >= t).mean()), 4) if len(x) else None

    for t in w["density_grid"]:
        table.append(
            {
                "threshold": t,
                "non_war_windows_qualifying": share(peace, t),
                "war_windows_qualifying": share(war, t),
            }
        )
    ok = [r for r in table if r["non_war_windows_qualifying"] is not None
          and r["non_war_windows_qualifying"] <= w["fpr_max"]]  # fmt: skip
    chosen = ok[0] if ok else None
    return {
        "table": table,
        "non_war_windows": int(len(peace)),
        "war_windows": int(len(war)),
        "chosen": None if chosen is None else chosen["threshold"],
        "passed": chosen is not None and chosen["war_windows_qualifying"] >= w["tpr_min"],
    }


# -------------------------------------------------------------------------------------- figures


def figures(raw: str, cfg: dict) -> list[tuple[int, str, int, bool, bool]]:
    """Numbers in ``raw``: (value, unit, word index, near a casualty word, near an army word).

    The reading of numbers is ``lab.numbers``'; this version keeps the word position so that a
    figure can be placed in a war window and tied to the words around it.
    """
    w = cfg["lab"]["warfare"]
    n = cfg["lab"]["numbers"]
    t = TOKEN.findall(raw.lower().replace("—", " . "))
    alpha = [i for i, x in enumerate(t) if x[0].isalpha()]
    ahead = np.cumsum([x[0].isalpha() for x in t]) - 1  # word index of the last word at or before i
    words = [t[i] for i in alpha]
    cas, army = set(w["casualty_words"]), ARMY_WORDS
    span = w["figure_span"]
    found, i = [], 0

    def near(j: int, k: int) -> tuple[bool, bool]:
        ctx = set(words[max(0, j - span) : k + span])
        return bool(ctx & cas), bool(ctx & army)

    while i < len(t):
        tok = t[i]
        j = i + 1
        val, unit = None, "other"
        if "0" <= tok[0] <= "9":
            prev = t[i - 1] if i else ""
            ok = prev.isalpha() and prev not in REFERENCE and len(tok.replace(",", "")) <= 9
            val = int(tok.replace(",", "")) if ok else None
            if j < len(t) and t[j] in ("st", "nd", "rd", "th"):
                val, j = None, j + 1
            if val is not None:
                unit = UNIT_OF.get(t[j], "other") if j < len(t) else "other"
                if n["year_lo"] <= val <= n["year_hi"] and "," not in tok and unit not in (
                    "people", "measure"):  # fmt: skip
                    val = None
        else:
            got = _phrase(t, i) if tok in WORDS or tok in ("a", "an") else None
            if got is not None:
                v, j, ordinal, _score = got
                val = None if ordinal else v
                unit = UNIT_OF.get(t[j], "other") if j < len(t) else "other"
        if val is not None and val >= w["figure_min"]:
            wi = int(ahead[i]) + (0 if t[i][0].isalpha() else 1)
            kj = int(ahead[min(j, len(t) - 1)])
            c, a = near(max(wi, 0), max(kj, wi))
            found.append((val, unit, max(wi, 0), c, a))
        i = max(j, i + 1)
    return found


def figure_stats(vals: list[int]) -> dict:
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    big = [v for v in s if v >= 1000]
    q = lambda p: s[min(len(s) - 1, int(len(s) * p))]  # noqa: E731
    return {
        "n": len(s),
        "median": statistics.median(s),
        "p10": q(0.1),
        "p90": q(0.9),
        "max": s[-1],
        "share_1000_or_more": round(len(big) / len(s), 3),
        "share_round_thousands_of_those": round(sum(v % 1000 == 0 for v in big) / len(big), 3)
        if big
        else None,
    }


# --------------------------------------------------------------------------------- measuring


def measure(prep: Prep, cfg: dict, threshold: float, part_windows: int | None = None) -> dict:
    """War windows, term counts per window, parts, whole-text counts, figures and the cluster."""
    w = cfg["lab"]["warfare"]
    size = w["window_words"]
    dens = seed_density(prep, cfg)
    war = dens >= threshold
    mat = window_matrix(prep, RX, size)
    nwin = len(dens)
    war_idx = np.flatnonzero(war)
    step = part_windows or w["part_windows"]
    least = min(w["min_part_windows"], step)
    parts = [war_idx[i : i + step] for i in range(0, len(war_idx), step)]
    if len(parts) > 1 and len(parts[-1]) < least:
        tail = parts.pop()
        parts[-1] = np.concatenate([parts[-1], tail])
    parts = [p for p in parts if len(p) >= least]
    figs = figures(prep.raw, cfg)
    warset = set(war_idx.tolist())
    inwar = [f for f in figs if f[2] // size in warset]
    casualty = [f[0] for f in inwar if f[3]]
    armies = [f[0] for f in inwar if not f[3] and (f[1] == "people" or (f[1] == "other" and f[4]))]
    whole = {n: len(prep.positions(RX[n])) for _, n in NAMES}
    return {
        "name": prep.name,
        "words": len(prep.words),
        "long_s_repaired": prep.repaired,
        "windows": nwin,
        "war_windows": int(war.sum()),
        "war_share": round(float(war.mean()), 4) if nwin else None,
        "war_words": int(war.sum()) * size,
        "counts": mat[:, war].sum(axis=1) if nwin else np.zeros(len(NAMES), dtype=int),
        "part_counts": [mat[:, p].sum(axis=1) for p in parts],
        "part_words": [len(p) * size for p in parts],
        "whole_counts": whole,
        "army_figures": armies,
        "casualty_figures": casualty,
    }


def rates(counts: np.ndarray, words: int) -> np.ndarray:
    return counts / max(words, 1) * 10000


def profile(counts: np.ndarray, words: int) -> np.ndarray:
    return np.sqrt(rates(counts, words))


def class_rates(counts: np.ndarray, words: int) -> np.ndarray:
    r = rates(counts, words)
    return np.array([sum(r[i] for i, (c, _) in enumerate(NAMES) if c == k) for k in CLASSES])


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    d = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(a @ b / d) if d else 0.0


# --------------------------------------------------------------------------------- placement


def formed(ms: list[dict], trad: dict[str, str | None], cfg: dict) -> dict[str, dict]:
    """Which traditions hold enough text: texts with enough war words, three, and pooled words."""
    w = cfg["lab"]["warfare"]
    out_: dict[str, dict] = {}
    for t in TRADITIONS:
        own = [m for m in ms if trad[m["name"]] == t]
        big = [m for m in own if m["war_words"] >= w["min_text_war_words"]]
        pooled = sum(m["war_words"] for m in big)
        out_[t] = {
            "texts": [m["name"] for m in own],
            "texts_big_enough": [m["name"] for m in big],
            "war_words_pooled": pooled,
            "forms": len(big) >= 3 and pooled >= w["min_tradition_war_words"],
        }
    return out_


def centres(ms: list[dict], trad: dict[str, str | None], forms: dict, skip: str | None):
    """Term-level and class-level centres of each formed tradition, leaving ``skip`` out."""
    term, cls = {}, {}
    for t in TRADITIONS:
        if not forms[t]["forms"]:
            continue
        own = [m for m in ms if m["name"] in forms[t]["texts_big_enough"] and m["name"] != skip]
        if own:
            term[t] = np.mean([profile(m["counts"], m["war_words"]) for m in own], axis=0)
            cls[t] = np.mean([class_rates(m["counts"], m["war_words"]) for m in own], axis=0)
    return term, cls


def class_scale(ms: list[dict], forms: dict) -> np.ndarray:
    rows = [
        class_rates(m["counts"], m["war_words"])
        for m in ms
        if any(m["name"] in forms[t]["texts_big_enough"] for t in TRADITIONS if forms[t]["forms"])
    ]
    return np.std(rows, axis=0) + 1e-9 if rows else np.ones(len(CLASSES))


def place(counts: np.ndarray, words: int, term: dict, cls: dict, scale: np.ndarray) -> dict:
    sims = {t: cosine(profile(counts, words), c) for t, c in term.items()}
    r = class_rates(counts, words)
    dist = {t: float(np.mean(((r - c) / scale) ** 2)) for t, c in cls.items()}
    return {
        "similarity": sims,
        "nearest": max(sims, key=sims.get) if sims else None,
        "class_distance": dist,
        "class_nearest": min(dist, key=dist.get) if dist else None,
    }


def held_out(ms: list[dict], trad: dict[str, str | None], forms: dict, cfg: dict) -> dict:
    """Leave-one-text-out placement of the parts and of the whole of each tradition's texts."""
    w = cfg["lab"]["warfare"]
    scale = class_scale(ms, forms)
    live = [t for t in TRADITIONS if forms[t]["forms"]]
    conf = {t: Counter() for t in live}  # parts
    conf_whole = {t: Counter() for t in live}
    conf_class = {t: Counter() for t in live}
    per_text = {}
    for t in live:
        for m in ms:
            if m["name"] not in forms[t]["texts_big_enough"]:
                continue
            term, cls = centres(ms, trad, forms, m["name"])
            for pc, pw in zip(m["part_counts"], m["part_words"], strict=True):
                p = place(pc, pw, term, cls, scale)
                conf[t][p["nearest"]] += 1
                conf_class[t][p["class_nearest"]] += 1
            whole = place(m["counts"], m["war_words"], term, cls, scale)
            conf_whole[t][whole["nearest"]] += 1
            own_sim = whole["similarity"][t]
            rival = max(v for k, v in whole["similarity"].items() if k != t)
            per_text[m["name"]] = {
                "tradition": t,
                "placed": whole["nearest"],
                "margin_over_best_other": round(own_sim - rival, 4),
                "similarity": {k: round(v, 4) for k, v in whole["similarity"].items()},
            }

    def rate(c: Counter, t: str) -> float | None:
        n = sum(c.values())
        return round(c[t] / n, 4) if n else None

    hit = {t: rate(conf[t], t) for t in live}
    res = {
        "traditions_formed": live,
        "chance": round(1 / len(live), 3) if live else None,
        "parts_hit_rate": hit,
        "parts_confusion": {t: dict(conf[t]) for t in live},
        "whole_text_hit_rate": {t: rate(conf_whole[t], t) for t in live},
        "whole_text_confusion": {t: dict(conf_whole[t]) for t in live},
        "class_level_parts_hit_rate": {t: rate(conf_class[t], t) for t in live},
        "per_text": per_text,
    }
    res["own_similarity_range"] = {}
    for t in live:
        mine = [v for v in per_text.values() if v["tradition"] == t]
        res["own_similarity_range"][t] = {
            "similarity_to_own": [round(min(v["similarity"][t] for v in mine), 4),
                                  round(max(v["similarity"][t] for v in mine), 4)],
            "margin_over_best_other": [round(min(v["margin_over_best_other"] for v in mine), 4),
                                       round(max(v["margin_over_best_other"] for v in mine), 4)],
        }  # fmt: skip
    vals = [v for v in hit.values() if v is not None]
    res["mean_hit_rate"] = round(sum(vals) / len(vals), 4) if vals else None
    res["passed"] = bool(
        len(live) >= 2
        and vals
        and sum(vals) / len(vals) >= w["classifier_bar"]
        and min(vals) >= w["tradition_bar"]
    )
    return res


# ---------------------------------------------------------------------- the Book of Mormon


def bom_paragraphs(drop_quotes: bool) -> list[tuple[str, int, str]]:
    labels = {r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines())}
    rows = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if r["kind"] != "body" or lab is None:
            continue
        if drop_quotes and (r["book"], lab["chapter_1830"]) in QUOTED:
            continue
        rows.append((r["book"], lab["chapter_1830"], r["text"]))
    return rows


def chapter_map(paras: list[tuple[str, int, str]]) -> tuple[list[int], list[tuple[str, int]]]:
    """Word index where each paragraph starts, and its (book, 1830 chapter)."""
    starts, at = [], 0
    for _b, _c, text in paras:
        starts.append(at)
        at += len(re.findall(r"[a-z]+", text.lower()))
    return starts, [(b, c) for b, c, _ in paras]


def passage_chapters(paras: list[tuple[str, int, str]]) -> list[tuple[str, int]]:
    """1830 chapters whose text holds all of the passage words."""
    by: dict[tuple[str, int], list[str]] = {}
    for b, c, text in paras:
        by.setdefault((b, c), []).append(" ".join(re.findall(r"[a-z]+", text.lower())))
    keep = []
    for key, texts in by.items():
        joined = " ".join(texts)
        if all(re.search(p, joined) for p in PASSAGE):
            keep.append(key)
    return keep


def min_span(pos: dict[str, np.ndarray], groups: list[str]) -> tuple[int, int] | None:
    """(words, start) of the smallest stretch holding at least one match of every group."""
    if any(len(pos[g]) == 0 for g in groups):
        return None
    events = sorted((int(p), g) for g in groups for p in pos[g])
    seen: Counter = Counter()
    have, left, best = 0, 0, None
    for p, g in events:
        seen[g] += 1
        have += seen[g] == 1
        while have == len(groups):
            span = p - events[left][0] + 1
            if best is None or span < best[0]:
                best = (span, events[left][0])
            lg = events[left][1]
            seen[lg] -= 1
            have -= seen[lg] == 0
            left += 1
    return best


def cluster_windows(prep: Prep, cfg: dict) -> dict:
    """Windows (stepping ``cluster_stride``) holding all five groups, and at least four."""
    w = cfg["lab"]["warfare"]
    size, stride = w["window_words"], w["cluster_stride"]
    n = len(prep.words)
    pos = {g: np.array(prep.positions(rx), dtype=int) for g, rx in CRX.items()}
    starts = np.arange(0, max(n - size, 0) + 1, stride)
    have = np.zeros((len(CRX), len(starts)), dtype=bool)
    for i, g in enumerate(CRX):
        p = pos[g]
        if len(p):
            have[i] = np.searchsorted(p, starts + size, side="left") > np.searchsorted(
                p, starts, side="left"
            )
    got = have.sum(axis=0)
    five = min_span(pos, list(CRX))
    fours = [min_span(pos, [g for g in CRX if g != x]) for x in CRX]
    fours = [f for f in fours if f is not None]
    return {
        "min_span_all_five": None if five is None else five[0],
        "min_span_all_five_start": None if five is None else five[1],
        "min_span_best_four": min((f[0] for f in fours), default=None),
        "windows": int(len(starts)),
        "all_five": int((got == len(CRX)).sum()),
        "at_least_four": int((got >= len(CRX) - 1).sum()),
        "at_least_three": int((got >= len(CRX) - 2).sum()),
        "starts_all_five": starts[got == len(CRX)].tolist(),
        "groups_present_anywhere": {g: int(len(pos[g])) for g in CRX},
    }


def library_baseline(cfg: dict, vocab: Counter) -> dict:
    """The five-word cluster in a seeded sample of period works."""
    w = cfg["lab"]["warfare"]
    rows = [
        r
        for r in registry.load().to_pylist()
        if r["kind"] == "work"
        and r["has_text"]
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and w["year_min"] <= r["year"] <= w["year_max"]
        and (r["words"] or 0) >= w["min_words"]
    ]
    rows.sort(key=lambda r: r["work_id"])
    random.Random(w["seed"]).shuffle(rows)
    cat = door.catalog({r["work_id"] for r in rows[: w["library_sample"] * 3]})
    picked = [cat[r["work_id"]] | r for r in rows[: w["library_sample"] * 3]
              if cat.get(r["work_id"], {}).get("text_path")][: w["library_sample"]]  # fmt: skip
    five, four, unreadable, done, windows = [], [], 0, 0, 0
    spans: list[int] = []
    for row in picked:
        raw = _library(row)
        if raw is None:
            unreadable += 1
            continue
        res = cluster_windows(Prep(row["work_id"], raw, cfg, vocab), cfg)
        done += 1
        windows += res["windows"]
        if res["all_five"]:
            five.append(row["work_id"])
        if res["at_least_four"]:
            four.append(row["work_id"])
        if res["min_span_all_five"] is not None:
            spans.append(res["min_span_all_five"])
    return {
        "works_with_all_five_groups_anywhere": len(spans),
        "min_span_all_five_works_at_or_under": {
            str(k): sum(x <= k for x in spans) for k in w["span_levels"]
        },
        "min_span_all_five_smallest": sorted(spans)[:5],
        "min_span_all_five_median": statistics.median(spans) if spans else None,
        "sampled": len(picked),
        "unreadable_not_attempted": unreadable,
        "read": done,
        "windows": windows,
        "works_with_a_window_holding_all_five": len(five),
        "works_with_a_window_holding_four": len(four),
        "share_all_five": round(len(five) / max(done, 1), 4),
        "share_four": round(len(four) / max(done, 1), 4),
        "work_ids_all_five": five,
    }


# ----------------------------------------------------------------------------------- the report


def term_table(m: dict) -> dict:
    r = rates(m["counts"], m["war_words"])
    return {
        n: {"count": int(m["counts"][i]), "per_10000": round(float(r[i]), 3)}
        for i, (_, n) in enumerate(NAMES)
        if m["counts"][i]
    }


def text_report(m: dict, trad: str | None) -> dict:
    cr = class_rates(m["counts"], m["war_words"])
    fort = [n for c, n in NAMES if c == "fortification"]
    whole_fort = sum(m["whole_counts"][n] for n in fort if n not in ("wall", "gate", "stone"))
    return {
        "tradition": trad,
        "words": m["words"],
        "long_s_repaired": m["long_s_repaired"],
        "windows": m["windows"],
        "war_windows": m["war_windows"],
        "war_share": m["war_share"],
        "war_words": m["war_words"],
        "parts": len(m["part_counts"]),
        "class_per_10000_war_words": {
            c: round(float(x), 2) for c, x in zip(CLASSES, cr, strict=True)
        },
        "terms": term_table(m),
        "fortification_terms_per_10000_whole_text_words": round(
            whole_fort / max(m["words"], 1) * 10000, 3
        ),
        "army_figures": figure_stats(m["army_figures"]),
        "casualty_figures": figure_stats(m["casualty_figures"]),
    }


def pooled(ms: list[dict]) -> dict:
    words = sum(m["war_words"] for m in ms)
    counts = sum((m["counts"] for m in ms), np.zeros(len(NAMES), dtype=int))
    return {"war_words": words, "counts": counts}


def tradition_report(ms: list[dict], names: list[str]) -> dict:
    own = [m for m in ms if m["name"] in names and m["war_words"] > 0]
    if not own:
        return {"not_attempted": True}
    p = pooled(own)
    r = rates(p["counts"], p["war_words"])
    per = [rates(m["counts"], m["war_words"]) for m in own]
    terms = {}
    for i, (c, n) in enumerate(NAMES):
        if p["counts"][i]:
            terms[n] = {
                "class": c,
                "count": int(p["counts"][i]),
                "per_10000": round(float(r[i]), 3),
                "range_over_texts": [round(float(min(x[i] for x in per)), 3),
                                     round(float(max(x[i] for x in per)), 3)],
                "texts_using": sum(1 for x in per if x[i] > 0),
            }  # fmt: skip
    cr = class_rates(p["counts"], p["war_words"])
    cper = [class_rates(m["counts"], m["war_words"]) for m in own]
    return {
        "texts": len(own),
        "war_words": p["war_words"],
        "class_per_10000": {c: round(float(x), 2) for c, x in zip(CLASSES, cr, strict=True)},
        "class_range_over_texts": {
            c: [round(float(min(x[k] for x in cper)), 2), round(float(max(x[k] for x in cper)), 2)]
            for k, c in enumerate(CLASSES)
        },
        "terms": terms,
        "army_figures": figure_stats([v for m in own for v in m["army_figures"]]),
        "casualty_figures": figure_stats([v for m in own for v in m["casualty_figures"]]),
    }


def distinguishing(bom: dict, trad_ms: list[dict], cfg: dict) -> dict:
    """Terms in the Book of Mormon and absent from a tradition, and the reverse."""
    w = cfg["lab"]["warfare"]
    p = pooled(trad_ms)
    br = rates(bom["counts"], bom["war_words"])
    tr = rates(p["counts"], p["war_words"])
    only_bom, only_trad = [], []
    for i, (c, n) in enumerate(NAMES):
        if bom["counts"][i] and not p["counts"][i]:
            only_bom.append({"term": n, "class": c, "bom_count": int(bom["counts"][i]),
                             "bom_per_10000": round(float(br[i]), 3)})  # fmt: skip
        if p["counts"][i] >= w["min_term_count"] and not bom["counts"][i]:
            only_trad.append({"term": n, "class": c, "tradition_count": int(p["counts"][i]),
                              "tradition_per_10000": round(float(tr[i]), 3)})  # fmt: skip
    shared = sum(1 for i in range(len(NAMES)) if bom["counts"][i] and p["counts"][i])
    union = sum(1 for i in range(len(NAMES)) if bom["counts"][i] or p["counts"][i])
    return {
        "in_book_of_mormon_absent_there": only_bom,
        "present_there_absent_in_book_of_mormon": only_trad,
        "terms_in_common": shared,
        "overlap_jaccard": round(shared / union, 3) if union else None,
        "pooled_profile_cosine": round(
            cosine(profile(bom["counts"], bom["war_words"]), profile(p["counts"], p["war_words"])),
            4,
        ),
    }


def verdict(sub: dict, forms: dict, cfg: dict, controls: dict) -> dict:
    """Nearest tradition by the card's rule, and the Bible-style control comparison."""
    w = cfg["lab"]["warfare"]
    n = sum(sub["parts_placed"].values())
    top = max(sub["parts_placed"], key=sub["parts_placed"].get) if n else None
    share = sub["parts_placed"][top] / n if n else 0
    whole = sub["whole"]["nearest"]
    nearest = whole if top == whole and share >= w["bom_share"] else None
    res = {"whole_text_nearest": whole, "parts_top": top, "parts_top_share": round(share, 3)}
    if nearest is None:
        res["verdict"] = "mixed"
        return res
    same = {k: v for k, v in controls.items() if v["whole"]["nearest"] == nearest}
    res["nearest"] = nearest
    res["similarity_to_nearest"] = round(sub["whole"]["similarity"][nearest], 4)
    res["controls_similarity_to_nearest"] = {
        k: v["whole"]["similarity"][nearest] for k, v in controls.items()
    }
    res["controls_placed_with_it"] = sorted(same)
    if not same:
        res["verdict"] = f"nearer {nearest}"
    else:
        spread = forms[nearest].get("similarity_spread", 0.0)
        ahead = sub["whole"]["similarity"][nearest] - max(
            v["whole"]["similarity"][nearest] for v in same.values()
        )
        res["margin_over_controls"] = round(ahead, 4)
        res["spread_of_members"] = round(spread, 4)
        res["verdict"] = (
            f"nearer {nearest}, beyond the Bible-style controls"
            if ahead > spread
            else "cannot tell: Bible-style controls are placed the same way"
        )
    return res


def place_text(m: dict, ms: list[dict], trad: dict, forms: dict, cfg: dict) -> dict:
    scale = class_scale(ms, forms)
    term, cls = centres(ms, trad, forms, m["name"])
    whole = place(m["counts"], m["war_words"], term, cls, scale)
    parts = [
        place(c, w, term, cls, scale)
        for c, w in zip(m["part_counts"], m["part_words"], strict=True)
    ]
    placed = Counter(p["nearest"] for p in parts)
    sims = {t: [p["similarity"][t] for p in parts] for t in term}
    return {
        "whole": {**whole, "similarity": {k: round(v, 4) for k, v in whole["similarity"].items()}},
        "parts": len(parts),
        "parts_placed": dict(placed),
        "parts_similarity_range": {
            t: [round(min(v), 4), round(max(v), 4)] for t, v in sims.items() if v
        },  # fmt: skip
        "class_level_nearest_whole": whole["class_nearest"],
    }


def bom_report(
    ms: list[dict], trad: dict, forms: dict, cfg: dict, label: str, drop: bool, prep: Prep,
    threshold: float
) -> dict:  # fmt: skip
    m = measure(prep, cfg, threshold)
    m["name"] = label
    controls = {
        c["name"]: place_text(c, ms, trad, forms, cfg) for c in ms if trad[c["name"]] is None
    }
    res = {"text": text_report(m, None), "placement": place_text(m, ms, trad, forms, cfg)}
    res["verdict"] = verdict(res["placement"], forms, cfg, controls)
    res["controls_placement"] = controls
    res["distinguishing"] = {
        t: distinguishing(m, [x for x in ms if x["name"] in forms[t]["texts"]], cfg)
        for t in TRADITIONS
    }
    res["army_figures_by_tradition"] = {}
    return res | {"_m": m}


def run(cfg: dict) -> dict:
    w = cfg["lab"]["warfare"]
    vocab = vocabulary(cfg)
    texts, missing, preps, trad = [], [], {}, {}
    for name, t, raw in tradition_texts(cfg):
        if raw is None:
            missing.append(name)
            continue
        preps[name] = Prep(name, raw, cfg, vocab)
        trad[name] = t
        texts.append(name)
    dens = {n: seed_density(preps[n], cfg) for n in texts}
    rule = pick_threshold(dens, cfg)
    res: dict = {"settings": w, "not_attempted": missing, "window_rule": rule}
    if not rule["passed"]:
        res["stopped"] = "the window rule missed its bar; nothing was placed"
        return res
    thr = rule["chosen"]
    ms = [measure(preps[n], cfg, thr) for n in texts if trad[n] not in ("peace",)]
    forms = formed(ms, trad, cfg)
    check = held_out(ms, trad, forms, cfg)
    res["traditions"] = forms
    res["known_answer"] = check
    res["texts"] = {m["name"]: text_report(m, trad[m["name"]]) for m in ms}
    res["traditions_profile"] = {t: tradition_report(ms, forms[t]["texts"]) for t in TRADITIONS}
    if not check["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
        return res
    # spread of member similarity (placed leave-one-out): the range a member text shows
    for t in check["traditions_formed"]:
        sims = [v["similarity"][t] for v in check["per_text"].values() if v["tradition"] == t]
        forms[t]["similarity_spread"] = max(sims) - min(sims)
    res["traditions"] = forms
    paras = bom_paragraphs(False)
    raw_all = "\n".join(p[2] for p in paras)
    raw_nq = "\n".join(p[2] for p in bom_paragraphs(True))
    bom_all = bom_report(
        ms, trad, forms, cfg, "bom_1830_all", False, Prep("bom", raw_all, cfg, vocab), thr
    )
    bom_nq = bom_report(ms, trad, forms, cfg, "bom_1830_without_quoted", True,
                        Prep("bomq", raw_nq, cfg, vocab), thr)  # fmt: skip
    m_all, m_nq = bom_all.pop("_m"), bom_nq.pop("_m")
    res["book_of_mormon"] = bom_all
    res["book_of_mormon_without_quoted_chapters"] = bom_nq
    # cluster and passage
    bom_prep = Prep("bom", raw_all, cfg, vocab)
    starts, chap = chapter_map(paras)
    cl = cluster_windows(bom_prep, cfg)
    where = []
    for s in cl["starts_all_five"]:
        lo = bisect_right(starts, s) - 1
        hi = bisect_right(starts, s + w["window_words"] - 1) - 1
        where.append(sorted({f"{chap[k][0]} 1830 ch {chap[k][1]}" for k in range(lo, hi + 1)}))
    cl["chapters_of_all_five_windows"] = where
    cl.pop("starts_all_five")
    span_at = cl["min_span_all_five_start"]
    if span_at is not None:
        lo = bisect_right(starts, span_at) - 1
        hi = bisect_right(starts, span_at + cl["min_span_all_five"] - 1) - 1
        cl["min_span_all_five_chapters"] = sorted(
            {f"{chap[k][0]} 1830 ch {chap[k][1]}" for k in range(lo, hi + 1)}
        )
    passage = passage_chapters(paras)
    res["fortification"] = {
        "passage_chapters_1830": [f"{b} 1830 ch {c}" for b, c in passage],
        "book_of_mormon_cluster": cl,
        "comparison_texts_cluster": {},
        "library_baseline": library_baseline(cfg, vocab),
        "passage_terms": {},
    }
    ptxt = " ".join(
        " ".join(re.findall(r"[a-z]+", t.lower())) for b, c, t in paras if (b, c) in passage
    )
    fort = [n for c, n in NAMES if c == "fortification"]
    used = {n: len(RX[n].findall(ptxt)) for n in fort}
    used = {n: k for n, k in used.items() if k}
    pw = len(ptxt.split())
    for n, k in used.items():
        row = {"passage_count": k, "passage_per_10000_words": round(k / max(pw, 1) * 10000, 2),
               "texts": {}}  # fmt: skip
        for m in ms:
            if m["counts"][TERM_INDEX[n]]:
                row["texts"][m["name"]] = round(
                    float(rates(m["counts"], m["war_words"])[TERM_INDEX[n]]), 3
                )
        row["texts_whole_text_per_10000_words"] = {
            m["name"]: round(m["whole_counts"][n] / m["words"] * 10000, 3)
            for m in ms
            if m["whole_counts"][n]
        }
        row["book_of_mormon_whole_text_per_10000_words"] = round(
            m_all["whole_counts"][n] / m_all["words"] * 10000, 3
        )
        row["texts_using"] = len(row["texts"])
        row["of_texts"] = len([m for m in ms if m["war_words"]])
        row["book_of_mormon_war_windows_per_10000"] = round(
            float(rates(m_all["counts"], m_all["war_words"])[TERM_INDEX[n]]), 3
        )
        res["fortification"]["passage_terms"][n] = row
    res["fortification"]["passage_words"] = pw
    pcl = cluster_windows(
        Prep("passage", "\n".join(t for b, c, t in paras if (b, c) in passage), cfg, vocab), cfg
    )
    pcl.pop("starts_all_five")
    res["fortification"]["passage_cluster"] = pcl
    for n in texts:
        if trad[n] != "peace":
            res["fortification"]["comparison_texts_cluster"][n] = {
                k: v for k, v in cluster_windows(preps[n], cfg).items() if k != "starts_all_five"
            }
    res["army_figures"] = {
        "book_of_mormon": res["book_of_mormon"]["text"]["army_figures"],
        "book_of_mormon_without_quoted": res["book_of_mormon_without_quoted_chapters"]["text"][
            "army_figures"
        ],
        "casualty_book_of_mormon": res["book_of_mormon"]["text"]["casualty_figures"],
        "traditions": {t: {k: res["traditions_profile"][t].get(k) for k in
                           ("army_figures", "casualty_figures")} for t in TRADITIONS},
    }  # fmt: skip
    del m_nq
    res["sensitivity_part_size"] = {}
    bom_prep2 = Prep("bom", raw_all, cfg, vocab)
    for step in w["part_windows_sensitivity"]:
        ms2 = [measure(preps[n], cfg, thr, step) for n in texts if trad[n] != "peace"]
        m2 = measure(bom_prep2, cfg, thr, step)
        m2["name"] = "bom_1830_all"
        ho = held_out(ms2, trad, forms, cfg)
        res["sensitivity_part_size"][str(step)] = {
            "known_answer_parts_hit_rate": ho["parts_hit_rate"],
            "known_answer_mean": ho["mean_hit_rate"],
            "book_of_mormon": {
                k: v for k, v in place_text(m2, ms2, trad, forms, cfg).items() if k != "whole"
            },
        }
    return res


def check_only(cfg: dict) -> dict:
    """The window rule and the held-out placement, without the Book of Mormon."""
    vocab = vocabulary(cfg)
    preps, trad = {}, {}
    missing = []
    for name, t, raw in tradition_texts(cfg):
        if raw is None:
            missing.append(name)
            continue
        preps[name], trad[name] = Prep(name, raw, cfg, vocab), t
    rule = pick_threshold({n: seed_density(p, cfg) for n, p in preps.items()}, cfg)
    res = {"not_attempted": missing, "window_rule": rule}
    if rule["passed"]:
        ms = [measure(preps[n], cfg, rule["chosen"]) for n in preps if trad[n] != "peace"]
        forms = formed(ms, trad, cfg)
        res["traditions"] = forms
        res["known_answer"] = held_out(ms, trad, forms, cfg)
        res["war_words"] = {m["name"]: m["war_words"] for m in ms}
        res["repaired"] = [n for n, p in preps.items() if p.repaired]
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "check":
        print(json.dumps(check_only(cfg), indent=1, default=_plain))
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1, default=_plain) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k in ("window_rule", "stopped")}, indent=1,
                     default=_plain))  # fmt: skip
    return 0


def _plain(x):
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    raise TypeError(type(x))


if __name__ == "__main__":
    raise SystemExit(main())
