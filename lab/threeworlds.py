"""BOM-109: where three worlds disagree, which does the Book of Mormon side with?

Three worlds: the ancient Near East as the King James Bible gives it; pre-Columbian Mesoamerica as
the native texts in English and Clavigero's account of Mexico before the conquest give it; and
ancient America as Americans of 1775-1829 imagined it, with the world they knew (the antiquities
and Indian-origin books of the library). The feature list is ``lab.threeworlds_features``.

Rule-countable features: every text is cut into the same marker counts (the long-s repair of
``lab.inventory``); a text states a feature *present* (at least ``present_min`` hits and
``present_rate`` per 10,000 words), *absent* (no hit in at least ``absent_min_words`` words), or
nothing. Each world's value is the majority of its source texts that state it, unless a held
source codes it (recorded). A feature is kept only where the worlds disagree. A text then agrees
with a world on each kept feature where their values are equal, and sides with the world it agrees
with most. **Known answers first:** texts held out of every world (1-2 Kings, Josephus, the
Annals of the Cakchiquels, Bernal Diaz, Spalding, *View of the Hebrews*, *Behemoth*) must each side
with their own world at the card's bar before the Book of Mormon is placed. Features that need
reading are written as questions for ``lab.judge`` (simulated judging by an AI model; prepared,
never run here), the known texts first. The test card, written first, is
``data/private/lab/owner/2026-11-21-three-worlds/card.md``; settings are ``lab.three_worlds`` in the
config. The result holds feature names, counts, citations and verse references, no passages.

Usage::

    python -m lab.threeworlds worlds   # measure the three worlds' values (source texts only)
    python -m lab.threeworlds check    # known-answer check (no Book of Mormon)
    python -m lab.threeworlds run      # -> data/lab/setting/three_worlds/result.json
    python -m lab.threeworlds jobs     # judging questions for the reading features (not run)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
from collections import Counter
from pathlib import Path

from lab import door
from lab import inventory as inv
from lab import threeworlds_features as feat
from lab import warfare as war
from lab.numbers import CAND, KJV, _file, _library, base20_counts, numbers
from lab.paths import FAST, NOTES, REGISTRY, out
from lab.wherefore import QUOTED
from metadata import config

OUT = REGISTRY / "setting" / "three_worlds"
CACHE = FAST / "three_worlds"
PRIVATE = NOTES / "owner" / "2026-11-21-three-worlds"
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
NE, MS, AM = feat.WORLDS
SIMULATED = "SIMULATED JUDGING BY AN AI MODEL (lab.judge; BOM-109). "
ROMAN = "I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX".split()


def settings(cfg: dict) -> dict:
    return cfg["lab"]["three_worlds"]


# ------------------------------------------------------------------------------ the markers


def compile_markers() -> dict[str, list[tuple[tuple[str, ...], str]]]:
    """feature -> [(lower-case word tuple, case rule)]; case rule '' any, '^' capital, '_' lower."""
    res = {}
    for fid, spec in feat.RULE.items():
        if "markers" not in spec:
            continue
        rows = []
        for tok in spec["markers"].split():
            case = ""
            if tok[-1] in "^":
                case, tok = "^", tok[:-1]
            if tok.endswith("_"):  # a trailing underscore: lower case only
                case, tok = "_", tok[:-1]
            parts = re.split("[_-]", tok)
            rows.append((tuple(p.lower() for p in parts if p), case))
        res[fid] = rows
    return res


MARKERS = compile_markers()
_BY_FIRST: dict[str, list[tuple[str, tuple[str, ...], str]]] = {}
for _fid, _rows in MARKERS.items():
    for _words, _case in _rows:
        _BY_FIRST.setdefault(_words[0], []).append((_fid, _words, _case))
AD = re.compile(r"(?<![\d,.])1[0-8]\d\d(?!\d|,\d)")  # not 1,812 nor 18123


def markers_sha() -> str:
    body = json.dumps({k: v.get("markers", v.get("special")) for k, v in feat.RULE.items()},
                      sort_keys=True)  # fmt: skip
    return hashlib.sha256(body.encode()).hexdigest()


def tokens(text: str) -> list[str]:
    """Words, hyphenated words split as the markers expect, long s repaired (lab.inventory)."""
    return inv.words_of(text)


def count_segment(text: str) -> Counter:
    """Marker hits per feature in one stretch of text (``ad_years`` included; words under '#')."""
    toks = tokens(text)
    low = [t.lower() for t in toks]
    c: Counter = Counter()
    for i, w in enumerate(low):
        for fid, words, case in _BY_FIRST.get(w, ()):
            if tuple(low[i : i + len(words)]) != words:
                continue
            if case == "^" and not toks[i][:1].isupper():
                continue
            if case == "_" and not toks[i].islower():
                continue
            c[fid] += 1
    c["ad_years"] += len(AD.findall(text))
    c["ad_years"] += sum(low[i : i + 4] == ["year", "of", "our", "lord"] for i in range(len(low)))
    c["#"] = len(toks)
    return c


# ------------------------------------------------------------------------------ the texts


def _kjv_rows() -> list[dict]:
    raw = _file(KJV)
    return [] if raw is None else [json.loads(x) for x in raw.splitlines()]


def kjv_unit(codes: list[str]) -> list[tuple[str | None, str]] | None:
    rows = [(r["ref"], r["text"]) for r in _kjv_rows() if r["book"] in set(codes)]
    return rows or None


def _one(text: str | None) -> list[tuple[str | None, str]] | None:
    return None if text is None else [(None, text)]


def bom_segments(drop_quotes: bool) -> list[tuple[str, str]]:
    """(reference, text) per body paragraph: book, 1830 chapter in roman numerals, paragraph."""
    labels = {r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines())}
    res = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if r["kind"] != "body" or lab is None:
            continue
        if drop_quotes and (r["book"], lab["chapter_1830"]) in QUOTED:
            continue
        ch = lab["chapter_1830"]
        roman = ROMAN[ch - 1] if 0 < ch <= len(ROMAN) else str(ch)
        res.append((f"{r['book']} {roman} para {r['seq']}", r["text"]))
    return res


def texts(cfg: dict) -> list[dict]:
    """Every text of the test: name, role (source / known / decoy / extra), world, segments.

    Segments are (reference or None, text); None segments mean the text is not held (not
    attempted). Called once: it loads the inventory's texts and fixes its long-s vocabulary."""
    st = settings(cfg)
    named = {n: t for n, _w, _r, t in inv.prepare(cfg)}
    cat = door.catalog(set(st["library"].values()))

    def lib(key: str) -> str | None:
        row = cat.get(st["library"][key])
        return None if row is None else _library(row)

    rows: list[tuple[str, str, str | None, list | None]] = []
    for unit, codes in st["kjv_units"].items():
        rows.append((unit, "source", NE, kjv_unit(codes)))
    for name in (
        "brinton_maya_chronicles_and_rig_veda",
        "brinton_nahuatl_poetry_1887",
        "popol_vuh_spence_1908",
        "popol_vuh_christenson",
    ):
        rows.append((name, "source", MS, _one(named.get(name))))
    rows.append(("clavigero_1787_vol1_before_conquest", "source", MS, _one(lib("clavigero_v1"))))
    for name in (
        "priest_wonders_1826",
        "clinton_discourse_and_western_new_york",
        "cusick_1827",
        "adair_american_indians_1775",
        "seaver_jemison_1826",
    ):
        rows.append((name, "source", AM, _one(named.get(name))))
    rows.append(("atwater_archaeologia_americana_1820", "source", AM, _one(war._atwater())))
    for key in (
        "haywood_tennessee_1823",
        "yates_moulton_new_york_1824",
        "boudinot_star_1816",
        "rafinesque_annals_kentucky_1824",
        "mcculloh_researches_1829",
    ):
        rows.append((key, "source", AM, _one(lib(key))))
    # known answers: in no world's sources
    rows.append(("kjv_kings", "known", NE, kjv_unit(st["known_kjv"])))
    rows.append(
        (
            "josephus_antiquities_whiston",
            "known",
            NE,
            _one(named.get("josephus_antiquities_whiston")),
        )
    )
    rows.append(("josephus_wars_whiston", "known", NE, _one(named.get("josephus_wars_whiston"))))
    rows.append(
        (
            "brinton_annals_cakchiquels_1885",
            "known",
            MS,
            _one(named.get("brinton_annals_cakchiquels_1885")),
        )
    )
    rows.append(
        ("bernal_diaz_keatinge_1800", "known", MS, _one(named.get("bernal_diaz_keatinge_1800")))
    )
    rows.append(
        (
            "spalding_manuscript_story",
            "known",
            AM,
            _one(_file(CAND / "ss-manuscript-story-1885.txt")),
        )
    )
    rows.append(
        (
            "view_of_the_hebrews_1825",
            "known",
            AM,
            _one(_file(CAND / "es-1825-view-of-the-hebrews.txt")),
        )
    )
    rows.append(("mathews_behemoth_1839", "known", AM, _one(named.get("mathews_behemoth_1839"))))
    rows.append(("late_war_1816", "decoy", AM, _one(_file(CAND / "gh-1816-late-war.txt"))))
    rows.append(
        (
            "solis_conquest_of_mexico_1724",
            "extra",
            None,
            _one(named.get("solis_conquest_of_mexico_1724")),
        )
    )
    rows.append(
        (
            "priest_american_antiquities_1833",
            "extra",
            None,
            _one(named.get("priest_american_antiquities_1833")),
        )
    )
    return [{"name": n, "role": r, "world": w, "segments": s} for n, r, w, s in rows]


# ------------------------------------------------------------------------------ counting


def counted(name: str, segments: list[tuple[str | None, str]] | None, cfg: dict,
            refs: bool = False) -> dict | None:  # fmt: skip
    """Counts per feature, words, base-twenty counts and (if ``refs``) up to ``refs_per_feature``
    references per feature. Cached by markers and text; None if the text is not held."""
    if segments is None:
        return None
    st = settings(cfg)
    h = hashlib.sha256()
    for ref, t in segments:
        h.update(f"{ref}\x00{t}\x01".encode())
    key = hashlib.sha256((markers_sha() + h.hexdigest() + str(len(inv.VOCAB)) + str(refs)
                          + str(st["refs_per_feature"])).encode()).hexdigest()[:20]  # fmt: skip
    path = CACHE / f"{re.sub('[^A-Za-z0-9_.-]', '_', name)[:80]}-{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    total: Counter = Counter()
    where: dict[str, list[str]] = {}
    for ref, t in segments:
        c = count_segment(t)
        total.update(c)
        if refs and ref is not None:
            for fid, k in c.items():
                if fid != "#" and k and len(where.setdefault(fid, [])) < st["refs_per_feature"]:
                    where[fid].append(ref)
    whole = "\n".join(t for _, t in segments)
    tw, other = base20_counts(numbers(whole, cfg), cfg)
    words = total.pop("#", 0)
    res = {"words": words, "counts": dict(total), "base20": [tw, other]}
    if refs:
        res["refs"] = where
    out(path).write_text(json.dumps(res))
    return res


def state(c: dict, fid: str, st: dict) -> str:
    """present / absent / not stated, for one counted text and one rule feature."""
    if feat.RULE[fid].get("special") == "vigesimal":
        tw, other = c["base20"]
        n = tw + other
        if n < st["vig_min_n"]:
            return "not stated"
        return "present" if tw / n >= st["vig_share"] else "absent"
    k, w = c["counts"].get(fid, 0), c["words"]
    if w == 0:
        return "not stated"
    if k >= st["present_min"] and k * 10000 / w >= st["present_rate"]:
        return "present"
    if k == 0 and w >= st["absent_min_words"]:
        return "absent"
    return "not stated"


# ------------------------------------------------------------------------------ the worlds


def world_values(counts: dict[str, dict], roles: dict[str, tuple[str, str | None]],
                 cfg: dict) -> dict[str, dict]:  # fmt: skip
    """feature -> world -> value, how it was set, and the source tally."""
    st = settings(cfg)
    res: dict[str, dict] = {}
    for fid, spec in feat.RULE.items():
        res[fid] = {}
        for world in feat.WORLDS:
            srcs = [n for n, (r, w) in roles.items() if r == "source" and w == world]
            held = [n for n in srcs if counts.get(n) is not None]
            got = Counter(state(counts[n], fid, st) for n in held)
            stating = got["present"] + got["absent"]
            measured = "unsettled"
            if stating >= st["world_min_stating"]:
                top = "present" if got["present"] >= got["absent"] else "absent"
                if got[top] / stating >= st["world_majority"] and got["present"] != got["absent"]:
                    measured = top
            row = {"measured": measured, "present": got["present"], "absent": got["absent"],
                   "not_stated": got["not stated"], "sources_held": len(held),
                   "sources_not_held": len(srcs) - len(held), "value": measured,
                   "how": "measured: majority of the source texts that state it"}  # fmt: skip
            coded = spec.get("coded", {}).get(world)
            if coded:
                row.update(value=coded[0], how=f"coded ({coded[2]}): {coded[1]}",
                           kind=coded[2])  # fmt: skip
            res[fid][world] = row
    return res


def discordant(values: dict[str, dict], with_memory: bool = True) -> tuple[list[str], dict]:
    """Kept features (worlds settled and not all equal) and why the others were dropped."""
    keep, dropped = [], {"concordant": [], "unsettled": [], "from_memory": []}
    for fid, row in values.items():
        vals = [row[w]["value"] for w in feat.WORLDS]
        if any(v == "unsettled" for v in vals):
            dropped["unsettled"].append(fid)
        elif len(set(vals)) == 1:
            dropped["concordant"].append(fid)
        elif not with_memory and any(row[w].get("kind") == "memory" for w in feat.WORLDS):
            dropped["from_memory"].append(fid)
        else:
            keep.append(fid)
    return keep, dropped


def from_memory(values: dict[str, dict]) -> list[str]:
    return [f for f, row in values.items() if any(row[w].get("kind") == "memory"
                                                  for w in feat.WORLDS)]  # fmt: skip


# ------------------------------------------------------------------------------ siding


def side(c: dict, keep: list[str], values: dict[str, dict], cfg: dict) -> dict:
    """Agreements of one text with each world over the kept features."""
    st = settings(cfg)
    agree = {w: 0 for w in feat.WORLDS}
    sole = {w: 0 for w in feat.WORLDS}
    per: dict[str, dict] = {}
    stated = 0
    for fid in keep:
        v = state(c, fid, st)
        if v == "not stated":
            per[fid] = {"value": v}
            continue
        stated += 1
        match = [w for w in feat.WORLDS if values[fid][w]["value"] == v]
        for w in match:
            agree[w] += 1
        if len(match) == 1:
            sole[match[0]] += 1
        per[fid] = {"value": v, "agrees_with": match}
    top = max(agree.values()) if stated else 0
    leaders = [w for w in feat.WORLDS if agree[w] == top] if stated else []
    return {"stated": stated, "agree": agree, "sole": sole,
            "share": {w: round(agree[w] / stated, 4) if stated else None for w in feat.WORLDS},
            "sides_with": leaders[0] if len(leaders) == 1 else "tie: " + "+".join(leaders),
            "features": per}  # fmt: skip


def passes(s: dict, own: str, cfg: dict) -> bool:
    st = settings(cfg)
    if not s["stated"]:
        return False
    others = [w for w in feat.WORLDS if w != own]
    return s["share"][own] >= st["known_bar_share"] and all(
        s["agree"][own] > s["agree"][w] for w in others
    )


def bootstrap(per: dict[str, dict], cfg: dict) -> dict:
    """Share of feature resamples in which each world leads alone (ties counted apart)."""
    st = settings(cfg)
    rows = [v["agrees_with"] for v in per.values() if v["value"] != "not stated"]
    if not rows:
        return {}
    rng = random.Random(st["seed"])
    lead: Counter = Counter()
    for _ in range(st["bootstrap"]):
        agree = Counter()
        for _k in range(len(rows)):
            agree.update(rng.choice(rows))
        top = max(agree[w] for w in feat.WORLDS)
        leaders = [w for w in feat.WORLDS if agree[w] == top]
        lead[leaders[0] if len(leaders) == 1 else "tie"] += 1
    return {k: round(v / st["bootstrap"], 4) for k, v in sorted(lead.items())}


def by_topic(per: dict[str, dict]) -> dict[str, dict]:
    res: dict[str, dict] = {}
    for fid, v in per.items():
        if v["value"] == "not stated":
            continue
        row = res.setdefault(feat.RULE[fid]["topic"], {"stated": 0, **{w: 0 for w in feat.WORLDS}})
        row["stated"] += 1
        for w in v["agrees_with"]:
            row[w] += 1
    return res


# ------------------------------------------------------------------------------ the steps


def gather(cfg: dict, with_bom: bool) -> tuple[dict, dict, dict]:
    """Counts of every text (and the Book of Mormon, whole and without the quoted chapters)."""
    rows = texts(cfg)
    counts: dict[str, dict | None] = {}
    roles: dict[str, tuple[str, str | None]] = {}
    for r in rows:
        counts[r["name"]] = counted(r["name"], r["segments"], cfg, refs=r["name"].startswith("kjv"))
        roles[r["name"]] = (r["role"], r["world"])
    if with_bom:
        for label, drop in (("book_of_mormon", False), ("book_of_mormon_without_quoted", True)):
            counts[label] = counted(label, bom_segments(drop), cfg, refs=True)
            roles[label] = ("target", None)
    return counts, roles, {r["name"]: r["segments"] is not None for r in rows}


def citations(values: dict, counts: dict, roles: dict) -> dict[str, dict]:
    """Where each measured world value can be checked: source texts and their counts; for the
    Near East, the first King James verse references holding a marker."""
    res: dict[str, dict] = {}
    for fid in values:
        res[fid] = {}
        for world in feat.WORLDS:
            srcs = sorted(n for n, (r, w) in roles.items() if r == "source" and w == world)
            row = {n: (counts[n]["counts"].get(fid, 0) if counts.get(n) else "not held")
                   for n in srcs}  # fmt: skip
            if world == NE:
                refs = [x for n in srcs if counts.get(n)
                        for x in counts[n].get("refs", {}).get(fid, [])][:5]  # fmt: skip
                res[fid][world] = {"counts": row, "kjv_refs": refs}
            else:
                res[fid][world] = {"counts": row}
    return res


def known_answer(counts: dict, roles: dict, values: dict, cfg: dict) -> dict:
    st = settings(cfg)
    res = {}
    for label, with_mem in (("all_features", True), ("without_from_memory", False)):
        keep, dropped = discordant(values, with_mem)
        texts_ = {}
        for name, (role, world) in roles.items():
            if role not in ("known", "decoy", "extra"):
                continue
            c = counts.get(name)
            if c is None:
                texts_[name] = {"role": role, "own_world": world, "state": "not attempted"}
                continue
            s = side(c, keep, values, cfg)
            s.pop("features")
            ok = passes(s, world, cfg) if role == "known" else None
            texts_[name] = {"role": role, "own_world": world, "words": c["words"], **s,
                            "passes": ok}  # fmt: skip
        known = [t for t in texts_.values() if t["role"] == "known"]
        held = [t for t in known if "passes" in t]
        n_pass = sum(bool(t.get("passes")) for t in held)
        res[label] = {
            "features_kept": len(keep),
            "dropped": {k: len(v) for k, v in dropped.items()},
            "texts": texts_,
            "known_held": len(held),
            "known_not_held": len(known) - len(held),
            "known_passing": n_pass,
            "passed": bool(held)
            and len(held) == len(known)
            and n_pass / len(held) >= st["known_pass_share"],
        }
    res["passed"] = res["all_features"]["passed"]
    return res


def stamp(res: dict) -> dict:
    res["config_sha256"] = config.sha256_of_config()
    res["markers_sha256"] = markers_sha()
    try:
        res["git_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                           text=True, check=True).stdout.strip()  # fmt: skip
    except (OSError, subprocess.CalledProcessError):
        res["git_commit"] = None
    return res


def check(cfg: dict) -> dict:
    counts, roles, held = gather(cfg, with_bom=False)
    values = world_values(counts, roles, cfg)
    return {"values": values, "known_answer": known_answer(counts, roles, values, cfg),
            "not_held": sorted(n for n, h in held.items() if not h)}  # fmt: skip


def run(cfg: dict) -> dict:
    st = settings(cfg)
    counts, roles, held = gather(cfg, with_bom=False)  # the book is counted only after the check
    values = world_values(counts, roles, cfg)
    ka = known_answer(counts, roles, values, cfg)
    keep_all, dropped_all = discordant(values, True)
    res: dict = {
        "test": "BOM-109 three worlds (lab; exploratory)",
        "card": str(PRIVATE / "card.md"),
        "rule_set": "named texts (no lab.views rule set: the comparison texts are listed by name)",
        "worlds": {NE: "King James Bible (Old Testament, Apocrypha, New Testament), less 1-2 Kings",
                   MS: "native Mesoamerican texts in English and Clavigero vol. 1 (before the "
                       "conquest)",
                   AM: "American antiquities and Indian-origin books, 1775-1829"},
        "features": {
            "rule_countable": len(feat.RULE), "needs_reading": len(feat.READING),
            "rule_kept_discordant": len(keep_all),
            "rule_dropped": {k: sorted(v) for k, v in dropped_all.items()},
            "rule_from_memory": from_memory(values),
            "reading_from_memory": sorted(f for f, s in feat.READING.items()
                                          if any(v[1][0] == "memory"
                                                 for v in s["values"].values())),
        },
        "settings": st,
        "not_held": sorted(n for n, h in held.items() if not h),
        "world_values": values,
        "world_citations": citations(values, counts, roles),
        "known_answer": ka,
        "citations_verified": verify_citations(cfg),
    }  # fmt: skip
    if not ka["passed"]:
        res["book_of_mormon"] = "not recorded: the known-answer check missed (see known_answer)"
        return stamp(res)
    bom: dict = {}
    for label, drop in (("book_of_mormon", False), ("book_of_mormon_without_quoted", True)):
        c = counted(label, bom_segments(drop), cfg, refs=True)
        row: dict = {"words": c["words"]}
        for vlabel, with_mem in (("all_features", True), ("without_from_memory", False)):
            keep, _ = discordant(values, with_mem)
            s = side(c, keep, values, cfg)
            for fid, v in s["features"].items():
                v["count"] = c["counts"].get(fid, 0)
                if v["value"] == "present":
                    v["refs"] = c["refs"].get(fid, [])
            s["bootstrap_lead_share"] = bootstrap(s["features"], cfg)
            s["by_topic"] = by_topic(s["features"])
            row[vlabel] = s
        bom[label] = row
    res["book_of_mormon"] = bom
    res["book_of_mormon_refs_note"] = (
        "references are book, 1830 chapter (roman) and the paragraph number of "
        "data/bom/1830/edition_1830.jsonl"
    )
    return stamp(res)


# ------------------------------------------------------------------------------ reading features


def verify_citations(cfg: dict) -> dict[str, dict]:
    """Check every King James and held citation (reading features, coded rule values) against
    the held text: a King James verse must contain the check words; a held source must contain
    them somewhere (the statement itself is not read by the code). Check words are not output."""
    kjv = {r["ref"]: " ".join(r["text"].lower().split()) for r in _kjv_rows()}
    st = settings(cfg)
    cat = door.catalog({st["library"]["clavigero_v1"]})
    row = cat.get(st["library"]["clavigero_v1"])
    clav = None if row is None else " ".join(_library(row).lower().split())

    def held(words: str) -> bool | None:
        return None if clav is None else " ".join(words.lower().split()) in clav

    res: dict[str, dict] = {"reading": {}, "coded": {}}
    for fid, spec in feat.READING.items():
        res["reading"][fid] = {}
        for world, (_desc, (kind, where, words)) in spec["values"].items():
            if kind == "kjv":
                ok = words.lower() in kjv[where] if where in kjv else None
            elif kind == "held":
                ok = held(words)
            else:
                ok = None
            res["reading"][fid][world] = {"kind": kind, "where": where, "verified": ok}
    for fid, spec in feat.RULE.items():
        for world, (value, where, kind, words) in spec.get("coded", {}).items():
            ok = held(words) if kind == "held" and words and "Clavigero" in where else None
            res["coded"][f"{fid}|{world}"] = {"value": value, "kind": kind, "where": where,
                                              "verified": ok}  # fmt: skip
    return res


PROMPT = """You are reading passages from one book to answer one question about the world the \
book describes. This is part of a study; your answer is recorded as simulated judging by an AI \
model.

Question: {question}

Three descriptions:
A. {a}
B. {b}
C. {c}

Standard: choose a description only if the passages state or plainly describe it as a fact \
about the people the book is about. Silence, a vague hint, a figure of speech, or a statement \
about some other people does not count. If none of A, B, C fits what is stated, or the passages \
do not say, answer D.

Passages (found by keyword search; they may be irrelevant):
{passages}

Answer on the first line with exactly one letter: A, B, C or D. On the second line, the number \
of the passage you relied on (or 0)."""


def jobs(cfg: dict) -> dict:
    """Judging questions for the reading features: the known texts and the decoy first (the
    judge's own known-answer check), then the Book of Mormon. Passages and the option key are
    private; nothing is run."""
    st = settings(cfg)
    from lab.dalechecklist import candidates

    rows = [r for r in texts(cfg) if r["role"] in ("known", "decoy")]
    rows.append({"name": "book_of_mormon", "role": "target", "world": None,
                 "segments": bom_segments(False)})  # fmt: skip
    out_jobs, key, per_text = [], [], {}
    for r in rows:
        if r["segments"] is None:
            per_text[r["name"]] = {"state": "not attempted (text not held)"}
            continue
        text = "\n".join(t for _, t in r["segments"])
        n_q = 0
        for fid, spec in feat.READING.items():
            got = candidates(text, re.compile(spec["keywords"], re.I), st["window_words"],
                             st["window_step"], st["passages_per_question"])  # fmt: skip
            if not got:
                continue
            qid = f"{r['name']}|{fid}"
            order = list(feat.WORLDS)
            random.Random(f"{st['seed']}-{qid}").shuffle(order)
            descs = [spec["values"][w][0] for w in order]
            body = "\n\n".join(f"[{n}] {p}" for n, p in enumerate(got, 1))
            question = f"What does this book say about {spec['label']}?"
            out_jobs.append({"id": qid, "prompt": PROMPT.format(
                question=question, a=descs[0], b=descs[1], c=descs[2], passages=body)})  # fmt: skip
            key.append({"id": qid, "A": order[0], "B": order[1], "C": order[2], "D": "not stated",
                        "role": r["role"], "own_world": r["world"]})  # fmt: skip
            n_q += 1
        per_text[r["name"]] = {"role": r["role"], "questions": n_q}
    rank = {"known": 0, "decoy": 1, "target": 2}
    order_ = sorted(range(len(out_jobs)), key=lambda i: rank[key[i]["role"]])
    with out(PRIVATE / "jobs.jsonl").open("w", encoding="utf-8") as fh:
        for i in order_:
            fh.write(json.dumps(out_jobs[i], ensure_ascii=False) + "\n")
    with out(PRIVATE / "jobs_key.jsonl").open("w", encoding="utf-8") as fh:
        for i in order_:
            fh.write(json.dumps(key[i]) + "\n")
    return {"questions": len(out_jobs), "per_text": per_text,
            "known_answer_questions": sum(k["role"] != "target" for k in key),
            "book_of_mormon_questions": sum(k["role"] == "target" for k in key),
            "jobs_file": str(PRIVATE / "jobs.jsonl"),
            "labelled": SIMULATED + "Prepared, not run.",
            "citations": verify_citations(cfg)}  # fmt: skip


# ------------------------------------------------------------------------------ command line


def _merge(update: dict) -> Path:
    path = OUT / "result.json"
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update(update)
    out(path).write_text(json.dumps(old, indent=1, ensure_ascii=False) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["worlds", "check", "run", "jobs"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "worlds":
        counts, roles, _held = gather(cfg, with_bom=False)
        values = world_values(counts, roles, cfg)
        for fid, row in values.items():
            print(
                f"{fid:20s}",
                "  ".join(
                    f"{w}={row[w]['value']}({row[w]['present']}/{row[w]['absent']})"
                    for w in feat.WORLDS
                ),
            )
        return 0
    if a.cmd == "check":
        res = check(cfg)
        ka = res["known_answer"]
        for label in ("all_features", "without_from_memory"):
            k = ka[label]
            print(label, "kept", k["features_kept"], "dropped", k["dropped"])
            for name, t in k["texts"].items():
                print(
                    f"  {name:40s} {t.get('role'):6s} own={t.get('own_world')} "
                    f"stated={t.get('stated')} agree={t.get('agree')} sole={t.get('sole')} "
                    f"-> {t.get('sides_with')} passes={t.get('passes')}"
                )
        print("passed:", ka["passed"])
        out(OUT / "known_answer.json").write_text(json.dumps(stamp(res), indent=1) + "\n")
        return 0
    if a.cmd == "run":
        res = run(cfg)
        path = _merge(res)
        print("known answer passed:", res["known_answer"]["passed"], "->", path)
        bom = res["book_of_mormon"]
        if isinstance(bom, dict):
            for label, row in bom.items():
                for v in ("all_features", "without_from_memory"):
                    s = row[v]
                    print(
                        label,
                        v,
                        "stated",
                        s["stated"],
                        "agree",
                        s["agree"],
                        "sole",
                        s["sole"],
                        "->",
                        s["sides_with"],
                        s["bootstrap_lead_share"],
                    )
        return 0
    res = jobs(cfg)
    path = _merge({"judging_jobs": res})
    print(json.dumps({k: v for k, v in res.items() if k != "citations"}, indent=1), "->", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
