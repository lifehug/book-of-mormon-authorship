"""BOM-116, second design: how constraining is the book's map, and does its consistency look real?

The first design (``lab.geography``) pulled statements with one written rule and let an optimiser
place towns; its region check missed. This design reads every passage with a place cue (windows of
about 400 words) with the paced model judge (``lab.judge``; **simulated** reading) into typed
relations with references and no free text, and a blind second reading of a fifth of the windows
in another format. From the coded tables:

- **Step 2, their way:** Clark's ten points (``data/lab/setting/geography2/clark_key.json``) are
  looked for in the book's table, and each proposed setting is graded pass / fail on each point at
  its public placements (``placements.json``) and its authors' orientation, on real geography.
- **Part A, specificity:** a text's strong features (directions in 8 sectors, up and down, days
  of travel, the sea on a stated side, water, a narrow neck, a river's head, bank, mouth and
  course) are tested on open physical data (``lab.geography2_earth``) in discs of the earth at
  six sizes, centred on a land grid; a disc passes when some layout of the places meets every
  feature at once. Specificity = share of discs that pass. Readings: literal, Clark's key as
  published, orientation free.
- **Part B, consistency:** contradictions per opportunity in the direction, elevation and
  travel-time networks, real-land against invented-land texts, subsampled to the book's size.
- **Part C, radiocarbon:** date coverage per region (p3k14c, NERD) counted before anything else.

Known-answer checks come first; the book is scored on a part only if its check passed. The card
is ``data/private/lab/owner/2026-11-22-geography-redesign/card.md``; settings are
``lab.geography2``. Results hold names, references and numbers, never text; judge jobs (which
quote passages) are private.

Usage::

    python -m lab.geography2 earth        # global rasters from the open physical data (1 min)
    python -m lab.geography2 windows      # coding windows of every text; counts (5 min)
    python -m lab.geography2 jobs         # judge jobs, check texts first (private folder) (5 min)
    python -m lab.geography2 dev          # Part A counter on hand-built tables, no judge (10-40 min)
    python -m lab.geography2 coverage     # Part C: radiocarbon dates per region (1 min)
    python -m lab.geography2 check        # coded check texts: extractor, kappa, Part A, step-2 check (hours)
    python -m lab.geography2 run          # check, then (if passed) the book and Part B (hours)
"""  # noqa: E501

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import subprocess
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np

from lab import geography as g1
from lab import geography2_earth as ge
from lab.paths import FAST, LOGS, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "setting" / "geography2"
CARD = NOTES / "owner" / "2026-11-22-geography-redesign"
CACHE = FAST / "geography2"
PARSE_LOG = LOGS / "geography2_parse_failures.jsonl"
CLARK_KEY = OUT / "clark_key.json"
PLACEMENTS = OUT / "placements.json"
PLEIADES = FAST / "sources" / "physical" / "pleiades-places-latest.csv.gz"
P3K14C = FAST / "sources" / "radiocarbon" / "p3k14c" / "people3k" / "p3k14c-1.0.0.zip"
NERD = FAST / "sources" / "radiocarbon" / "nerd_v6" / "apalmisano82" / "NERD-v6.0.zip"
DIRS = ge.DIRS
KINDS = ("direction", "higher", "days", "sea", "water", "neck", "river", "flows", "strip", "near")
TRAVELLERS = ("walker", "group_with_flocks", "army", "messenger", "unknown")
ROLES = ("source", "bank", "mouth")
AXES = ("N-S", "NE-SW", "E-W", "SE-NW")
JOB_FILES = {"check": "jobs_check.jsonl", "panel": "jobs_panel.jsonl", "book": "jobs_book.jsonl"}


def settings(cfg: dict) -> dict:
    return cfg["lab"]["geography2"]


# --------------------------------------------------------------------------- texts and windows


def library_units(work_id: str) -> list[tuple[str, str]] | None:
    from lab.placenames import library_text

    t = library_text(work_id)
    return g1.paragraph_units(t) if t else None


def jsp_units(path: Path) -> list[tuple[str, str]] | None:
    from lab.dictations import strip_editorial

    if not path.exists():
        return None
    got = []
    for line in path.read_text().splitlines():
        r = json.loads(line)
        for i, p in enumerate(re.split(r"\n\s*\n", strip_editorial(r["text"]))):
            if p.strip():
                got.append((f"page {r['page']} para {i + 1}", p))
    return got


def bom_units() -> list[tuple[str, str, bool]]:
    """(reference, text, in a Bible-quoting chapter) for every body paragraph of the 1830 text."""
    from lab.wherefore import EDITION, LABELS, QUOTED

    labels = {r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines())}
    got = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if r["kind"] != "body":
            continue
        ch = labels.get(r["seq"], {}).get("chapter_1830")
        got.append((f"{r['book']} {ch} para {r['seq']}", r["text"], (r["book"], ch) in QUOTED))
    return got


def text_units(spec: dict) -> list[tuple[str, str, bool]] | None:
    """(reference, text, quoted flag) units of one text; None when it cannot be read."""
    src = spec["source"]
    if src == "bom":
        return bom_units()
    if src == "library":
        ids = spec.get("work_ids") or [spec["work_id"]]
        units = []
        for k, wid in enumerate(ids):
            u = library_units(wid)
            if u is None:
                return None
            units += [(f"vol {k + 1} {r}" if len(ids) > 1 else r, t) for r, t in u]
    elif src == "jsp":
        units = jsp_units(Path(spec["path"]))
    else:
        units = g1.text_units(spec)
    return None if units is None else [(r, t, False) for r, t in units]


def windows_of(units: list[tuple[str, str, bool]], n_words: int) -> list[dict]:
    """Consecutive units up to ``n_words`` words; a window never mixes quoted and other units;
    a unit longer than the window is cut into pieces (``ref`` + ``#k``)."""
    pieces = []
    for ref, text, quoted in units:
        words = re.sub(r"-\s*\n\s*", "", text).split()
        if not words:
            continue
        for k in range(0, len(words), n_words):
            r = ref if len(words) <= n_words else f"{ref} #{k // n_words + 1}"
            pieces.append((r, " ".join(words[k : k + n_words]), quoted))
    wins, cur, size = [], [], 0
    for p in pieces:
        n = len(p[1].split())
        if cur and (size + n > n_words or p[2] != cur[-1][2]):
            wins.append(cur)
            cur, size = [], 0
        cur.append(p)
        size += n
    if cur:
        wins.append(cur)
    return [
        {
            "refs": [p[0] for p in w],
            "text": "\n".join(f"[{p[0]}] {p[1]}" for p in w),
            "quoted": w[0][2],
            "words": sum(len(p[1].split()) for p in w),
        }
        for w in wins
    ]


def cue_count(text: str, cues: list[re.Pattern]) -> int:
    return sum(len(c.findall(text)) for c in cues)


def place_list(units: list[tuple[str, str, bool]], cfg: dict) -> list[str]:
    """The fixed place list given to the reader: ``lab.geography``'s written lexicon rule."""
    w = {"min_mentions": settings(cfg)["lexicon_min_mentions"]}
    names = g1.lexicon([(r, g1.normalise(t)) for r, t, _q in units], w)
    rename = {
        "Narrowneck": "narrow neck",
        "Landnorthward": "land northward",
        "Landsouthward": "land southward",
        "Landeastward": "land eastward",
        "Landwestward": "land westward",
    }
    return sorted({rename.get(n, n) for n in names})


def all_windows(cfg: dict, names: list[str] | None = None) -> tuple[dict, dict]:
    """({text: {"windows": [...], "places": [...]}}, {text: reason not attempted})."""
    s = settings(cfg)
    cues = [re.compile(c, re.I) for c in s["cues"]]
    got, missing = {}, {}
    for name, spec in s["texts"].items():
        if names and name not in names:
            continue
        units = text_units(spec)
        if not units:
            missing[name] = "not attempted: the text could not be read"
            continue
        wins = windows_of(units, s["window_words"])
        for k, w in enumerate(wins):
            w["id"] = f"{name}:{k:05d}"
            w["cues"] = cue_count(w["text"], cues)
        got[name] = {
            "windows": [w for w in wins if w["cues"] >= s["min_cues"]],
            "all_windows": len(wins),
            "places": place_list(units, cfg),
            "words": sum(w["words"] for w in wins),
        }
    return got, missing


def second_sample(ids: list[str], share: float, seed: int) -> set[str]:
    """A seeded share of window ids for the blind second reading (at least one)."""
    if not ids:
        return set()
    k = max(1, round(share * len(ids)))
    rng = np.random.default_rng(
        seed + int(hashlib.sha256("".join(ids[:3]).encode()).hexdigest()[:6], 16)
    )
    return set(rng.choice(ids, size=min(k, len(ids)), replace=False).tolist())


# --------------------------------------------------------------------------- prompts and parsing

VOCAB = """Kinds (use only these; places must be named in the passage itself):
- direction: a lies in direction dir (N, NE, E, SE, S, SW, W, NW) from b. Fields a, b, dir.
- higher: a is higher ground than b (e.g. "went up from b to a", "came down from a to b"). Fields a, b.
- days: a stated number of days' travel between a and b. Fields a, b, days (a number), traveller (walker, group_with_flocks, army, messenger, unknown).
- sea: a lies by the sea; side = the direction from a in which the sea lies, if stated, else null. Fields a, side.
- water: a is itself a sea, lake or body of water. Field a.
- neck: a is a narrow neck of land or isthmus; water_sides = the axis on which water lies on both sides of it (N-S, NE-SW, E-W, SE-NW) if stated, else null; crossing_days = days to cross it if stated, else null; traveller as above. Fields a, water_sides, crossing_days, traveller.
- river: place a lies at the river's source (head), on its bank, or at its mouth. Fields river, a, role (source, bank, mouth).
- flows: the river runs toward direction toward. Fields river, toward.
- strip: a strip of wilderness or border lies between a and b. Fields a, b.
- near: a is near, next to or borders on b. Fields a, b."""  # noqa: E501


def judge_prompt(window: dict, places: list[str]) -> str:
    here = [p for p in places if p.lower() in window["text"].lower()]
    return (
        "You are coding the geography that a passage states, for a research test. Use only what "
        "this passage itself says; do not use anything you know about where any place is. List "
        "every statement it makes about where named places lie relative to each other or to "
        "water.\n\n" + VOCAB + "\n\nEvery item also has ref: the bracketed reference of the "
        "sentence it comes from. Use the place names as the passage spells them; a person's name "
        'is a place only when the passage uses it as one ("the land of", "the city of").\n'
        f"Place names on the fixed list for this text that occur here: {', '.join(here) or 'none'}"
        ".\n\nReply with a JSON array of objects and nothing else; [] if the passage states no "
        "such relation.\n\nPassage:\n" + window["text"]
    )


def judge_prompt_second(window: dict, places: list[str]) -> str:
    here = [p for p in places if p.lower() in window["text"].lower()]
    return (
        "Read the passage below and write down, one per line, each geographic relation it "
        "states between places it names, or between a named place and water. Rely on the passage "
        "alone, never on outside knowledge of the places.\n\nLine format, fields separated by "
        "' | ': KIND | A | B | VALUE | REF\n"
        "KIND is one of direction, higher, days, sea, water, neck, river, flows, strip, near.\n"
        "- direction: A lies VALUE (N, NE, E, SE, S, SW, W, NW) of B.\n"
        "- higher: A is higher ground than B; VALUE -.\n"
        "- days: VALUE = number of days' travel between A and B, then a space and who travelled "
        "(walker, group_with_flocks, army, messenger, unknown).\n"
        "- sea: A lies by the sea; B -; VALUE = direction of the sea from A, or -.\n"
        "- water: A is a sea or lake; B -, VALUE -.\n"
        "- neck: A is a narrow neck of land; B -; VALUE = axis with water on both sides (N-S, "
        "NE-SW, E-W, SE-NW) or -, then a space and the days to cross it or -.\n"
        "- river: A is the river's name, B the place; VALUE = source, bank or mouth.\n"
        "- flows: A is the river; B -; VALUE = the direction it runs toward.\n"
        "- strip: a strip of wilderness or border lies between A and B; VALUE -.\n"
        "- near: A is near or borders on B; VALUE -.\n"
        "REF is the bracketed reference of the sentence. Write NONE if there are no relations.\n"
        f"Places on this text's fixed list that occur here: {', '.join(here) or 'none'}.\n\n"
        "Passage:\n" + window["text"]
    )


def _dir(x) -> str | None:
    x = (str(x or "")).strip().upper()
    full = {
        "NORTH": "N",
        "SOUTH": "S",
        "EAST": "E",
        "WEST": "W",
        "NORTHEAST": "NE",
        "NORTHWEST": "NW",
        "SOUTHEAST": "SE",
        "SOUTHWEST": "SW",
    }
    x = full.get(x.replace("-", "").replace(" ", ""), x)
    return x if x in DIRS else None


def _axis(x) -> str | None:
    x = (str(x or "")).strip().upper().replace(" ", "")
    if x in AXES:
        return x
    parts = x.split("-")
    if len(parts) == 2 and all(p in DIRS for p in parts):
        for a in AXES:
            if set(a.split("-")) == set(parts):
                return a
    return None


def _num(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def clean_item(it: dict) -> dict | None:
    """One coded relation checked against the vocabulary; None when it does not fit."""
    if not isinstance(it, dict):
        return None
    k = str(it.get("kind", "")).strip().lower()
    a = str(it.get("a") or "").strip()
    b = str(it.get("b") or "").strip()
    ref = str(it.get("ref") or "").strip().strip("[]")
    river = str(it.get("river") or "").strip()
    if k not in KINDS:
        return None
    r = {"kind": k, "ref": ref}
    if k in ("direction", "higher", "days", "strip", "near"):
        if not a or not b:
            return None
        r |= {"a": a, "b": b}
    if k == "direction":
        d = _dir(it.get("dir"))
        if d is None:
            return None
        r["dir"] = d
    elif k == "days":
        n = _num(it.get("days"))
        if n is None:
            return None
        t = str(it.get("traveller") or "unknown").strip().lower()
        r |= {"days": n, "traveller": t if t in TRAVELLERS else "unknown"}
    elif k in ("sea", "water"):
        if not a:
            return None
        r["a"] = a
        if k == "sea":
            r["side"] = _dir(it.get("side"))
    elif k == "neck":
        if not a:
            return None
        t = str(it.get("traveller") or "unknown").strip().lower()
        r |= {
            "a": a,
            "water_sides": _axis(it.get("water_sides")),
            "crossing_days": _num(it.get("crossing_days")),
            "traveller": t if t in TRAVELLERS else "unknown",
        }
    elif k == "river":
        role = str(it.get("role") or "").strip().lower()
        if not river or not a or role not in ROLES:
            return None
        r |= {"river": river, "a": a, "role": role}
    elif k == "flows":
        d = _dir(it.get("toward"))
        if not river or d is None:
            return None
        r |= {"river": river, "toward": d}
    return r


def parse_reply(reply: str) -> list[dict] | None:
    """The first reading's JSON array; None when no array can be read."""
    s = reply.strip()
    i, j = s.find("["), s.rfind("]")
    if i < 0 or j < i:
        return None
    try:
        items = json.loads(s[i : j + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(items, list):
        return None
    return [c for c in (clean_item(x) for x in items) if c]


def parse_reply_second(reply: str) -> list[dict] | None:
    """The second reading's lines; None when nothing in the reply has the line format."""
    lines = [ln.strip().strip("-* ") for ln in reply.strip().splitlines() if ln.strip()]
    if any(ln.upper() == "NONE" for ln in lines) and not any("|" in ln for ln in lines):
        return []
    got, seen = [], False
    for ln in lines:
        f = [x.strip() for x in ln.split("|")]
        if len(f) < 5:
            continue
        seen = True
        k, a, b, value, ref = f[0].lower(), f[1], f[2], f[3], f[4]
        b = "" if b in ("-", "") else b
        v = value.split()
        it: dict = {"kind": k, "a": a, "b": b, "ref": ref}
        if k == "direction":
            it["dir"] = value
        elif k == "days":
            it["days"] = v[0] if v else None
            it["traveller"] = v[1] if len(v) > 1 else "unknown"
        elif k == "sea":
            it["side"] = None if value == "-" else value
        elif k == "neck":
            it["water_sides"] = None if not v or v[0] == "-" else v[0]
            it["crossing_days"] = v[1] if len(v) > 1 and v[1] != "-" else None
        elif k == "river":
            it = {"kind": k, "river": a, "a": b, "role": value, "ref": ref}
        elif k == "flows":
            it = {"kind": k, "river": a, "toward": value, "ref": ref}
        c = clean_item(it)
        if c:
            got.append(c)
    return got if seen else None


# --------------------------------------------------------------------------- names and tables

_HEADS = re.compile(
    r"^(?:the\s+)?(?:(?:land|city|town|country|province|plains?|valley|vale|wilderness|hill|mount|"
    r"mountain|river|borders?|coasts?|camp|fort|village|kingdom)\s+(?:of\s+)?(?:the\s+)?)?"
)


def norm(name: str) -> str:
    """A place name folded for matching: lower case, no article or "land of" / "city of" head
    (so the land and the city of one name are one place), seas as "<dir> sea"."""
    x = re.sub(r"[^\w\s'-]", " ", name.lower())
    x = re.sub(r"\s+", " ", x).strip()
    m = re.fullmatch(r"(?:the\s+)?sea\s+(north|south|east|west)", x)
    if m:
        return f"{m.group(1)} sea"
    if re.fullmatch(r"(?:the\s+)?land\s+(northward|southward|eastward|westward)", x):
        return x.removeprefix("the ")
    if x.startswith(("the narrow neck", "narrow neck", "small neck", "the small neck")):
        return "narrow neck"
    y = _HEADS.sub("", x).strip()
    return y or x


def in_window(name: str, text: str) -> bool:
    """The name (its last word, at least) appears in the window: a guard against reading from
    memory."""
    words = [w for w in re.findall(r"[a-z']+", name.lower()) if len(w) > 2]
    t = text.lower()
    return bool(words) and words[-1] in t


def window_relations(items: list[dict], window: dict) -> tuple[list[dict], dict]:
    """Relations kept from one window (names folded; reference in the window; names in the
    text) and counts of what was dropped."""
    drop = defaultdict(int)
    kept = []
    refs = set(window["refs"])
    for it in items:
        if it["ref"] not in refs:
            near_ref = next((r for r in window["refs"] if it["ref"] and it["ref"] in r), None)
            if near_ref is None:
                drop["reference not in the window"] += 1
                continue
            it = {**it, "ref": near_ref}
        names = [it[k] for k in ("a", "b", "river") if it.get(k)]
        if not all(in_window(n, window["text"]) for n in names):
            drop["name not in the passage"] += 1
            continue
        r = dict(it)
        for k in ("a", "b", "river"):
            if r.get(k):
                r[k] = norm(r[k])
        kept.append(r)
    return kept, dict(drop)


def rel_key(r: dict) -> tuple:
    vals = tuple(
        r.get(k)
        for k in (
            "kind",
            "a",
            "b",
            "river",
            "dir",
            "days",
            "traveller",
            "side",
            "water_sides",
            "crossing_days",
            "role",
            "toward",
        )
    )
    return vals


def build_table(rels: list[dict], generic: set[str]) -> list[dict]:
    """Identical relations merged, each with all its references; generic words ("the sea",
    "wilderness") are never places; relations of a place with itself dropped."""
    merged: dict[tuple, dict] = {}
    for r in rels:
        if any(r.get(k) in generic for k in ("a", "b", "river")):
            continue
        if r.get("b") and r.get("a") == r.get("b"):
            continue
        k = rel_key(r)
        if k not in merged:
            merged[k] = {x: v for x, v in r.items() if x != "ref"} | {"refs": []}
        if r["ref"] not in merged[k]["refs"]:
            merged[k]["refs"].append(r["ref"])
    return list(merged.values())


def load_answers(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    got = {}
    for line in path.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            got[r["id"]] = r["reply"]
    return got


def coded_tables(wins: dict, answers: dict[str, str], cfg: dict, second: bool = False) -> dict:
    """Per text: the table, counts of windows answered / unparseable / open, drops. Unparseable
    replies are logged raw and their windows stay open (never counted as "no relations")."""
    generic = set(settings(cfg)["generic_places"])
    res = {}
    for name, rec in wins.items():
        rels, drops = [], defaultdict(int)
        n_ok = n_bad = n_open = 0
        for w in rec["windows"]:
            jid = w["id"] + ("#2" if second else "")
            if jid not in answers:
                n_open += 1
                continue
            items = (parse_reply_second if second else parse_reply)(answers[jid])
            if items is None:
                n_bad += 1
                with out(PARSE_LOG).open("a") as fh:
                    fh.write(json.dumps({"id": jid, "reply": answers[jid]}) + "\n")
                continue
            n_ok += 1
            kept, d = window_relations(items, w)
            rels += [r | {"window": w["id"]} for r in kept]
            for k, v in d.items():
                drops[k] += v
        res[name] = {
            "windows_answered": n_ok,
            "unparseable": n_bad,
            "open": n_open,
            "dropped": dict(drops),
            "relations": rels,
            "table": build_table(rels, generic),
        }
    return res


# --------------------------------------------------------------------------- agreement (kappa)


def item_label(r: dict) -> tuple[tuple, str]:
    k = r["kind"]
    if k in ("direction", "higher", "days", "strip", "near"):
        a, b = sorted((r["a"], r["b"]))
        flip = a != r["a"]
        key = (k, a, b)
        if k == "direction":
            d = DIRS[(DIRS.index(r["dir"]) + 4) % 8] if flip else r["dir"]
            return key, d
        if k == "higher":
            return key, "b" if flip else "a"
        if k == "days":
            return key, f"{r['days']:g}"
        return key, "yes"
    if k == "sea":
        return (k, r["a"]), r.get("side") or "any"
    if k in ("water", "neck"):
        return (k, r["a"]), "yes"
    if k == "river":
        return (k, r["river"], r["a"]), r["role"]
    return (k, r["river"]), r["toward"]


def kappa(first: list[dict], second: list[dict]) -> dict:
    """Cohen's kappa over the union of items both readings could have coded in the shared
    windows; an item one reading lacks is labelled "none" for it."""
    by: dict[tuple, list[str]] = defaultdict(lambda: ["none", "none"])
    for i, rels in enumerate((first, second)):
        for r in rels:
            key, lab = item_label(r)
            by[(r["window"], *key)][i] = lab
    pairs = list(by.values())
    if not pairs:
        return {"items": 0, "kappa": None}
    labs = sorted({x for p in pairs for x in p})
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pe = sum(
        (sum(a == x for a, _ in pairs) / n) * (sum(b == x for _, b in pairs) / n) for x in labs
    )
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return {"items": n, "observed_agreement": round(po, 4), "kappa": round(k, 4)}


# --------------------------------------------------------------------------- features (Part A)


def km_range(days: float, traveller: str, s: dict) -> list[float]:
    lo, hi = s["traveller_km_per_day"].get(traveller, s["traveller_km_per_day"]["unknown"])
    return [days * lo, days * hi]


def resolve_conflicts(table: list[dict]) -> tuple[list[dict], int]:
    """Opposed statements about one pair (directions more than 90 degrees apart; higher both
    ways; differing day counts) keep the one with more references; a tie drops both (days: a
    tie keeps the union of the ranges as one statement)."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    rest = []
    for r in table:
        if r["kind"] in ("direction", "higher", "days"):
            groups[(r["kind"], *sorted((r["a"], r["b"])))].append(r)
        else:
            rest.append(r)
    kept, dropped = [], 0
    for (kind, _a, _b), rs in groups.items():
        if len(rs) == 1:
            kept += rs
            continue
        rs = sorted(rs, key=lambda r: -len(r["refs"]))

        def clash(x: dict, y: dict, kind: str = kind, _a: str = _a) -> bool:
            if kind == "higher":
                return x["a"] != y["a"]
            if kind == "days":
                return x["days"] != y["days"]
            dx = DIRS.index(x["dir"]) if x["a"] == _a else (DIRS.index(x["dir"]) + 4) % 8
            dy = DIRS.index(y["dir"]) if y["a"] == _a else (DIRS.index(y["dir"]) + 4) % 8
            return min((dx - dy) % 8, (dy - dx) % 8) > 2

        top = rs[0]
        rivals = [r for r in rs[1:] if clash(top, r)]
        tied = [r for r in rivals if len(r["refs"]) == len(top["refs"])]
        if tied and kind == "days":
            kept.append(
                top | {"km_union": True, "union_of": [top["days"]] + [r["days"] for r in tied]}
            )
            dropped += len(rivals) - len(tied)
        elif tied:
            dropped += len(rivals) + 1
        else:
            kept.append(top)
            dropped += len(rivals)
        kept += [r for r in rs[1:] if not clash(top, r)]
    return rest + kept, dropped


def features(table: list[dict], s: dict, reading: str = "strong", min_refs: int = 1) -> list[dict]:
    """Coded relations as features for the window counter. ``reading``: strong (every strong
    kind), weak (near, by the sea without a side, half-plane directions only)."""
    a = s["part_a"]
    rows = [r for r in table if len(r["refs"]) >= min_refs]
    if reading == "strong":
        rows, _ = resolve_conflicts(rows)
    got = []
    for r in rows:
        k = r["kind"]
        if reading == "weak":
            if k == "near":
                got.append({"kind": "near", "a": r["a"], "b": r["b"]})
            elif k == "sea":
                got.append({"kind": "sea", "a": r["a"], "side": None})
            elif k == "direction":
                got.append(
                    {
                        "kind": "direction",
                        "a": r["a"],
                        "b": r["b"],
                        "dir": r["dir"],
                        "cone": a["dir_cone_weak"],
                    }
                )
            continue
        if k == "direction":
            got.append(
                {"kind": k, "a": r["a"], "b": r["b"], "dir": r["dir"], "cone": a["dir_cone_strong"]}
            )
        elif k == "higher":
            got.append({"kind": k, "a": r["a"], "b": r["b"]})
        elif k == "days":
            ds = r.get("union_of") or [r["days"]]
            lo = min(km_range(d, r["traveller"], s)[0] for d in ds)
            hi = max(km_range(d, r["traveller"], s)[1] for d in ds)
            got.append({"kind": k, "a": r["a"], "b": r["b"], "km": [lo, hi]})
        elif k == "sea" and r.get("side"):
            got.append({"kind": "sea", "a": r["a"], "side": r["side"]})
        elif k == "water":
            got.append({"kind": "water", "a": r["a"]})
        elif k == "neck":
            width = (
                km_range(r["crossing_days"], r.get("traveller", "unknown"), s)[1]
                if r.get("crossing_days")
                else None
            )
            got.append(
                {
                    "kind": "neck",
                    "a": r["a"],
                    "water_sides": r.get("water_sides"),
                    "width_km": width,
                }
            )
        elif k == "river":
            got.append({"kind": "river", "river": r["river"], "a": r["a"], "role": r["role"]})
        elif k == "flows":
            got.append(
                {
                    "kind": "flows",
                    "river": r["river"],
                    "toward": r["toward"],
                    "cone": a["flow_cone"],
                }
            )
    # a place cannot be both water and land: water wins (it is a statement about the place)
    return dedupe(got)


def dedupe(feats: list[dict]) -> list[dict]:
    seen, got = set(), []
    for f in feats:
        k = json.dumps(f, sort_keys=True)
        if k not in seen:
            seen.add(k)
            got.append(f)
    return got


def rotate(feats: list[dict], steps: int) -> list[dict]:
    """Every direction in the features turned by ``steps`` x 45 degrees (the rotation decoy)."""

    def turn(d):
        return DIRS[(DIRS.index(d) + steps) % 8] if d else d

    got = []
    for f in feats:
        f = dict(f)
        for k in ("dir", "side", "toward"):
            if f.get(k):
                f[k] = turn(f[k])
        if f.get("water_sides"):
            f["water_sides"] = AXES[(AXES.index(f["water_sides"]) + steps) % 4]
        got.append(f)
    return got


def clark_features(s: dict, key: dict | None = None) -> list[dict]:
    """Clark's ten points as features (km from his units), each tagged with its point."""
    key = key or json.loads(CLARK_KEY.read_text())
    lo, hi = s["clark_unit_km"]
    a = s["part_a"]
    got = []
    for point, rec in key["points"].items():
        for f in rec["features"]:
            f = dict(f) | {"point": point}
            if "width_usd" in f:
                f["width_km"] = f.pop("width_usd") * hi
            if "usd" in f:
                u0, u1 = f.pop("usd")
                if f["kind"] == "direction":
                    got.append(
                        {
                            "kind": "days",
                            "a": f["a"],
                            "b": f["b"],
                            "km": [u0 * lo, u1 * hi],
                            "point": point,
                        }
                    )
                else:
                    f["km"] = [u0 * lo, u1 * hi]
            if "usd_max" in f:
                f["max_km"] = f.pop("usd_max") * hi
            if f["kind"] == "direction":
                f["cone"] = a["dir_cone_strong"]
            if f["kind"] == "flows":
                f["cone"] = a["flow_cone"]
            got.append(f)
    return got


# --------------------------------------------------------------------------- Part A counting


def land_centres(earth: ge.Earth, diameter: float, s: dict) -> list[tuple[float, float]]:
    """Window centres on land, about ``centre_spacing`` x diameter apart."""
    lo_lat, hi_lat = s["lat_range"]
    step = diameter * s["part_a"]["centre_spacing"]
    got = []
    lat = lo_lat + step / ge.KM_DEG / 2
    while lat <= hi_lat:
        dlon = step / (ge.KM_DEG * max(math.cos(math.radians(lat)), 0.05))
        n = max(1, int(360 // dlon))
        lons = -180 + (np.arange(n) + 0.5) * 360 / n
        land = ~earth.is_water(np.full(n, lat), lons)
        got += [(round(float(lat), 4), round(float(lo), 4)) for lo in lons[land]]
        lat += step / ge.KM_DEG
    return got


def window_verdict(
    feats: list[dict], win: dict, rotations: list[int], a: dict
) -> tuple[str, int | None]:
    """'pass' (and the first rotation that passes), 'fail', or 'undecided'."""
    undecided = False
    for rot in rotations:
        comp = ge.compile_features(feats, win, rot % 8, a)
        if comp is None:
            continue
        r = ge.solve(*comp, a["node_limit"])
        if r == "pass":
            return "pass", rot
        undecided |= r == "undecided"
    return ("undecided" if undecided else "fail"), None


def count_windows(
    earth: ge.Earth,
    readings: dict[str, tuple[list[dict], list[int]]],
    diameter: float,
    s: dict,
    regions: dict | None = None,
) -> dict:
    """For each reading (features, rotations): passes, fails and undecided discs over the land
    grid at one diameter, and the verdict of each named region's disc."""
    a = s["part_a"] | {"sea_km": s["part_a"]["sea_km"]}
    centres = land_centres(earth, diameter, s)
    res = {r: {"windows": 0, "pass": 0, "fail": 0, "undecided": 0, "passing": []} for r in readings}
    t0 = time.time()
    for lat, lon in centres:
        win = ge.window(earth, lat, lon, diameter, a)
        for name, (feats, rots) in readings.items():
            v, rot = window_verdict(feats, win, rots, a)
            r = res[name]
            r["windows"] += 1
            r[v] += 1
            if v == "pass":
                r["passing"].append([lat, lon, rot])
    for r in res.values():
        n = r["windows"] or 1
        r["specificity"] = round(r["pass"] / n, 5)
        r["specificity_upper"] = round((r["pass"] + r["undecided"]) / n, 5)
    out_regions = {}
    for rname, reg in (regions or {}).items():
        win = ge.window(earth, reg["lat"], reg["lon"], diameter, a)
        per = {}
        for name, (feats, rots) in readings.items():
            rots_r = reg.get("rotations", {}).get(name, rots)
            v, rot = window_verdict(feats, win, rots_r, a)
            tol = diameter * a["region_tolerance"]
            nearby = [
                p
                for p in res[name]["passing"]
                if ge.dist_bearing(reg["lat"], reg["lon"], p[0], p[1])[0] <= tol and p[2] in rots_r
            ]
            per[name] = {
                "centred": v,
                "rotation": rot,
                "passing_discs_nearby": len(nearby),
                "passes": v == "pass" or bool(nearby),
            }
        out_regions[rname] = per | {"recently_drowned_pixels": win["recent_drowned"]}
    for r in res.values():
        r["passing"] = r["passing"][:200]
    return {
        "diameter_km": diameter,
        "centres": len(centres),
        "seconds": round(time.time() - t0),
        "readings": res,
        "regions": out_regions,
    }


def part_a_verdict(spec: float, spec_upper: float, inside: bool, a: dict) -> str:
    """The card's rule, per reading and size."""
    lo_bar, hi_bar = a["specific_bar"], a["unspecific_bar"]
    if (spec <= lo_bar) != (spec_upper <= lo_bar) or (spec > hi_bar) != (spec_upper > hi_bar):
        return "cannot tell (undecided discs straddle a bar)"
    if spec_upper == 0:
        return "fits nowhere under this reading"
    if spec_upper <= lo_bar:
        return (
            "constraining, and the setting meets it"
            if inside
            else "constraining; the setting does not meet it"
        )
    if spec > hi_bar:
        return "does not pick out a region"
    return "weak constraint, no verdict"


# --------------------------------------------------------------------------- true coordinates


def openbible_coords() -> dict[str, tuple[float, float]]:
    return {norm(k): v for k, v in g1.openbible().items()}


def pleiades_coords() -> dict[str, tuple[float, float]]:
    """Pleiades place titles and their other names, folded, to the representative point."""
    got: dict[str, tuple[float, float]] = {}
    with gzip.open(PLEIADES, "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                lat, lon = float(r["reprLat"]), float(r["reprLong"])
            except (KeyError, TypeError, ValueError):
                continue
            for nm in [r.get("title", "")] + (r.get("names") or "").split(","):
                nm = norm(nm.split("/")[0])
                if nm and nm not in got:
                    got[nm] = (lat, lon)
    return got


def true_region(name: str, table: list[dict], s: dict, coords: dict | None) -> dict | None:
    """Centre and diameter of a known text's own region: the median of its placed places and the
    smallest size that holds ``true_cover`` of them (config regions for texts without a source)."""
    spec = s["texts"][name]
    if spec.get("region") == "config":
        r = s["known_regions"][name]
        return {
            "lat": r["lat"],
            "lon": r["lon"],
            "diameter": r["diameter"],
            "from": "config: " + r["note"],
        }
    if not coords:
        return None
    names = {p for r in table for p in (r.get("a"), r.get("b")) if p} & set(coords)
    if len(names) < 3:
        return None
    pts = np.array([coords[p] for p in sorted(names)])
    lat, lon = float(np.median(pts[:, 0])), float(np.median(pts[:, 1]))
    d, _ = ge.dist_bearing(lat, lon, pts[:, 0], pts[:, 1])
    need = float(np.quantile(d, s["part_a"]["true_cover"])) * 2
    size = next((x for x in s["part_a"]["sizes_km"] if x >= need), s["part_a"]["sizes_km"][-1])
    return {
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "diameter": size,
        "places_with_coordinates": len(names),
        "from": spec.get("region"),
    }


def holds(f: dict, pos: dict[str, tuple[float, float]], earth: ge.Earth, s: dict) -> bool | None:
    """Whether one feature holds at given coordinates (None: a place is not placed or the kind is
    not scored pointwise)."""
    a = s["part_a"]
    places = [f.get("a"), f.get("b")]
    if any(p and p not in pos for p in places):
        return None
    k = f["kind"]
    if k in ("direction", "days", "near", "higher"):
        (la1, lo1), (la2, lo2) = pos[f["a"]], pos[f["b"]]
        d, b = ge.dist_bearing(la2, lo2, la1, lo1)  # from b to a
        if k == "direction":
            return bool(ge.in_cone(b, ge.BEARING[f["dir"]], f["cone"]))
        if k == "days":
            return bool(f["km"][0] <= d <= f["km"][1])
        if k == "near":
            return bool(d <= a["near_km"])
        z1, z2 = earth.elevation([la1], [lo1])[0], earth.elevation([la2], [lo2])[0]
        return bool(z1 - z2 > a["higher_margin_m"])
    la, lo = pos[f["a"]]
    if k == "water":
        return bool(earth.is_water([la], [lo])[0])
    if k == "sea":
        dist = earth.water_dist([la], [lo])[:, 0]
        lim = f.get("max_km", a["sea_km"])
        return bool((dist[DIRS.index(f["side"])] if f.get("side") else dist.min()) <= lim)
    return None


def extractor_check(
    table: list[dict], coords: dict, region: dict, earth: ge.Earth, s: dict, seed: int
) -> dict:
    """Share of the text's strong statements that hold at true coordinates, against random
    placements of the same places in the same disc."""
    feats = [
        f
        for f in features(table, s)
        if f["kind"] in ("direction", "days", "higher", "sea", "water")
    ]
    feats += [f for f in features(table, s, "weak") if f["kind"] == "near"]
    placed = {p for f in feats for p in (f.get("a"), f.get("b")) if p} & set(coords)
    true = {p: coords[p] for p in placed}
    ok = [h for f in feats if (h := holds(f, true, earth, s)) is not None]
    if len(ok) < 5:
        return {
            "stopped": "not attempted: fewer than 5 statements with both places placed",
            "statements_scored": len(ok),
        }
    share = sum(ok) / len(ok)
    rng = np.random.default_rng(seed)
    names = sorted(placed)
    shares = []
    for _ in range(s["extractor"]["random_placements"]):
        rho = region["diameter"] / 2 * np.sqrt(rng.random(len(names)))
        lat, lon = ge.destination(region["lat"], region["lon"], rng.random(len(names)) * 360, rho)
        rnd = {p: (float(la), float(lo)) for p, la, lo in zip(names, lat, lon, strict=True)}
        r = [h for f in feats if (h := holds(f, rnd, earth, s)) is not None]
        shares.append(sum(r) / len(r) if r else 0.0)
    pct = g1.percentile(share, shares)
    ex = s["extractor"]
    return {
        "places_placed": len(names),
        "statements_scored": len(ok),
        "true_share": round(share, 4),
        "random_median_share": round(float(np.median(shares)), 4),
        "random_p99_share": round(float(np.percentile(shares, 99)), 4),
        "percentile": pct,
        "passed": share >= ex["hold_bar"] and pct is not None and pct >= ex["percentile_bar"],
    }


# --------------------------------------------------------------------------- step 2: their way


def clark_rebuilt(table: list[dict]) -> dict:
    """Which of Clark's ten points the coded table states, and the statements under each.
    A point is rebuilt when, for every feature of the point, the table has a relation of the same
    kind on the same places (directions within 45 degrees; any day count for a distance)."""
    key = json.loads(CLARK_KEY.read_text())
    res = {}
    for point, rec in key["points"].items():
        found, missing = [], []
        for f in rec["features"]:
            hit = [r for r in table if matches(f, r)]
            (found if hit else missing).append(
                {
                    "feature": {k: v for k, v in f.items() if k != "point"},
                    "refs": sorted({x for r in hit for x in r["refs"]})[:20],
                }
            )
        res[point] = {
            "rebuilt": not missing,
            "features_found": len(found),
            "features": len(rec["features"]),
            "found": found,
            "missing": missing,
        }
    return {"points_rebuilt": sum(v["rebuilt"] for v in res.values()), "points": res}


def matches(f: dict, r: dict) -> bool:
    k = f["kind"]
    if k == "direction":
        if r["kind"] == "direction" and {r["a"], r["b"]} == {norm(f["a"]), norm(f["b"])}:
            d = DIRS.index(r["dir"]) if r["a"] == norm(f["a"]) else (DIRS.index(r["dir"]) + 4) % 8
            return min((d - DIRS.index(f["dir"])) % 8, (DIRS.index(f["dir"]) - d) % 8) <= 1
        return False
    if k in ("days", "near"):
        return r["kind"] in ("days",) and {r["a"], r["b"]} == {norm(f["a"]), norm(f["b"])}
    if k == "higher":
        return r["kind"] == "higher" and (r["a"], r["b"]) == (norm(f["a"]), norm(f["b"]))
    if k in ("water", "neck"):
        return r["kind"] == k and r["a"] == norm(f["a"])
    if k == "sea":
        return (
            r["kind"] == "sea" and r["a"] == norm(f["a"]) and r.get("side") in (f.get("side"), None)
        )
    if k == "river":
        return r["kind"] == "river" and r["river"] == norm(f["river"]) and r["a"] == norm(f["a"])
    if k == "flows":
        return (
            r["kind"] == "flows" and r["river"] == norm(f["river"]) and r["toward"] == f["toward"]
        )
    return False


def grade_setting(setting: dict, rotation: int, earth: ge.Earth, s: dict) -> dict:
    """Clark's ten points at one setting's public placements and one rotation, on real geography:
    pass / fail per feature, 'cannot grade' where a place has no public placement."""
    key = json.loads(CLARK_KEY.read_text())
    feats = clark_features(s, key)
    pos = {
        p: (v["lat"], v["lon"]) for p, v in setting.items() if not p.startswith("_") and "lat" in v
    }
    rivers = {p: v["river"] for p, v in setting.items() if not p.startswith("_") and "river" in v}
    tw = s["their_way"]
    theta = 45 * rotation
    res = {}
    for point in key["points"]:
        rows = []
        for f in [x for x in feats if x["point"] == point]:
            g = grade_feature(f, pos, rivers, theta, earth, s, tw)
            rows.append(
                {"kind": f["kind"], "a": f.get("a") or f.get("river"), "b": f.get("b"), "grade": g}
            )
        graded = [r["grade"] for r in rows if r["grade"] in ("pass", "fail")]
        if not graded:
            verdict = "cannot grade"
        elif "fail" in graded:
            verdict = "fail"
        elif len(graded) < len(rows):
            verdict = "pass on what can be graded"
        else:
            verdict = "pass"
        res[point] = {"verdict": verdict, "features": rows}
    return res


def grade_feature(f, pos, rivers, theta, earth, s, tw) -> str:
    a = s["part_a"]
    k = f["kind"]
    if k in ("river", "flows"):
        rname = rivers.get(f["river"])
        if rname is None:
            return "cannot grade"
        r = next((x for x in earth.rivers if x["name"] == rname), None)
        if r is None:
            return "cannot grade: river not in Natural Earth"
        if k == "flows":
            _d, b = ge.dist_bearing(r["head"][1], r["head"][0], r["mouth"][1], r["mouth"][0])
            return "pass" if ge.in_cone(b, theta + ge.BEARING[f["toward"]], f["cone"]) else "fail"
        if f["a"] not in pos:
            return "cannot grade"
        la, lo = pos[f["a"]]
        if f["role"] == "bank":
            d = ge.dist_bearing(la, lo, np.asarray(r["lat"]), np.asarray(r["lon"]))[0].min()
            return "pass" if d <= tw["sea_km"] else "fail"
        end = r["head"] if f["role"] == "source" else r["mouth"]
        d = ge.dist_bearing(la, lo, end[1], end[0])[0]
        return "pass" if d <= tw["sea_km"] else "fail"
    places = [p for p in (f.get("a"), f.get("b")) if p]
    if any(p not in pos for p in places):
        return "cannot grade"
    if k == "neck":
        la, lo = pos[f["a"]]
        dist = earth.water_dist([la], [lo])[:, 0]
        ax = (DIRS.index(f["water_sides"].split("-")[0]) + round(theta / 45)) % 4
        width = dist[ax] + dist[ax + 4]
        return "pass" if width <= f["width_km"] else "fail"
    if k == "sea":
        la, lo = pos[f["a"]]
        dist = earth.water_dist([la], [lo])[:, 0]
        e = (DIRS.index(f["side"]) + round(theta / 45)) % 8
        return "pass" if dist[e] <= f.get("max_km", tw["sea_km"]) else "fail"
    if k == "direction":
        (la1, lo1), (la2, lo2) = pos[f["a"]], pos[f["b"]]
        _d, b = ge.dist_bearing(la2, lo2, la1, lo1)
        return "pass" if ge.in_cone(b, theta + ge.BEARING[f["dir"]], f["cone"]) else "fail"
    h = holds(f, pos, earth, s | {"part_a": a})
    return "cannot grade" if h is None else ("pass" if h else "fail")


# --------------------------------------------------------------------------- Part B


def order_edges(table: list[dict]) -> dict[str, list[tuple[str, str]]]:
    """Strict orders implied by each statement: north-south, east-west and elevation (lo, hi)."""
    e: dict[str, list[tuple[str, str]]] = {"ns": [], "ew": [], "up": []}
    for r in table:
        if r["kind"] == "direction":
            d = r["dir"]
            if "N" in d:
                e["ns"].append((r["b"], r["a"]))
            if "S" in d:
                e["ns"].append((r["a"], r["b"]))
            if "E" in d:
                e["ew"].append((r["b"], r["a"]))
            if "W" in d:
                e["ew"].append((r["a"], r["b"]))
        elif r["kind"] == "higher":
            e["up"].append((r["b"], r["a"]))
    return e


def reach(edges: list[tuple[str, str]], skip: int | None = None) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for i, (u, v) in enumerate(edges):
        if i != skip:
            adj[u].add(v)
    memo: dict[str, set[str]] = {}
    for start in list(adj):
        seen, stack = set(), [start]
        while stack:
            x = stack.pop()
            for y in adj.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        memo[start] = seen
    return memo


def consistency(table: list[dict], s: dict) -> dict:
    """Opportunities (a stated relation also implied, or contradicted, by the others),
    contradictions per opportunity, and rigidity (share of place pairs with a fixed order)."""
    opp = con = 0
    edges = order_edges(table)
    for es in edges.values():
        for i, (u, v) in enumerate(es):
            r = reach(es, skip=i)
            fwd = v in r.get(u, set())
            back = u in r.get(v, set())
            if fwd or back:
                opp += 1
                con += back
    days = {}
    for r in table:
        if r["kind"] == "days":
            lo, hi = km_range(r["days"], r["traveller"], s)
            days[frozenset((r["a"], r["b"]))] = (lo + hi) / 2
    places = sorted({p for k in days for p in k})
    slack = s["part_b"]["triangle_slack"]
    for i, x in enumerate(places):
        for j in range(i + 1, len(places)):
            y = places[j]
            for z in places[j + 1 :]:
                sides = [days.get(frozenset(p)) for p in ((x, y), (y, z), (x, z))]
                if None in sides:
                    continue
                opp += 1
                m = max(sides)
                con += m > slack * (sum(sides) - m)
    fixed = total = 0
    for axis in ("ns", "ew"):
        es = edges[axis]
        pl = sorted({p for e in es for p in e})
        r = reach(es)
        for i, x in enumerate(pl):
            for y in pl[i + 1 :]:
                total += 1
                fixed += y in r.get(x, set()) or x in r.get(y, set())
    return {
        "statements": sum(len(v) for v in edges.values()) + len(days),
        "opportunities": opp,
        "contradictions": con,
        "rate": (con / opp) if opp else None,
        "rigidity": (fixed / total) if total else None,
    }


def consistency_statements(table: list[dict]) -> list[dict]:
    return [r for r in table if r["kind"] in ("direction", "higher", "days")]


def subsampled(table: list[dict], n: int, s: dict, seed: int) -> dict:
    st = consistency_statements(table)
    if len(st) <= n:
        c = consistency(st, s)
        return {
            "statements": len(st),
            "rate": c["rate"],
            "rigidity": c["rigidity"],
            "opportunities": c["opportunities"],
            "subsampled": False,
        }
    rng = np.random.default_rng(seed)
    rates, rig, opps = [], [], []
    for _ in range(s["part_b"]["reps"]):
        pick = [st[i] for i in rng.choice(len(st), size=n, replace=False)]
        c = consistency(pick, s)
        opps.append(c["opportunities"])
        if c["rate"] is not None:
            rates.append(c["rate"])
        if c["rigidity"] is not None:
            rig.append(c["rigidity"])
    return {
        "statements": len(st),
        "rate": float(np.mean(rates)) if rates else None,
        "rigidity": float(np.mean(rig)) if rig else None,
        "opportunities": float(np.mean(opps)),
        "subsampled": True,
    }


def auc(real: list[float], invented: list[float]) -> float | None:
    """Chance that a random real text has fewer contradictions per opportunity than a random
    invented one (ties count half)."""
    if not real or not invented:
        return None
    w = sum((r < i) + 0.5 * (r == i) for r in real for i in invented)
    return w / (len(real) * len(invented))


def place_book(book: float, real: list[float], invented: list[float]) -> str:
    mid = (float(np.median(real)) + float(np.median(invented))) / 2
    if book < mid and min(real) <= book <= max(real):
        return "more like real"
    if book > mid and min(invented) <= book <= max(invented):
        return "more like invented"
    return "between"


# --------------------------------------------------------------------------- Part C coverage


def p3k14c_rows() -> list[tuple[float, float, float]]:
    """(lat, lon, 14C age BP) of every p3k14c date with coordinates (the archive is read in
    memory, never unpacked)."""
    with zipfile.ZipFile(P3K14C) as z:
        name = next(n for n in z.namelist() if n.endswith("p3k14c_scrubbed_fuzzed.csv"))
        text = z.read(name).decode("utf-8", "replace")
    got = []
    for r in csv.DictReader(io.StringIO(text)):
        try:
            got.append((float(r["Lat"]), float(r["Long"]), float(r["Age"])))
        except (KeyError, TypeError, ValueError):
            continue
    return got


def nerd_rows() -> list[tuple[float, float, float]]:
    with zipfile.ZipFile(NERD) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        got = []
        for n in names:
            text = z.read(n).decode("utf-8", "replace")
            rd = csv.DictReader(io.StringIO(text))
            cols = {c.lower(): c for c in (rd.fieldnames or [])}
            la = cols.get("latitude") or cols.get("lat")
            lo = cols.get("longitude") or cols.get("long") or cols.get("lon")
            ag = cols.get("cra") or cols.get("age") or cols.get("bp")
            if not (la and lo and ag):
                continue
            for r in rd:
                try:
                    got.append((float(r[la]), float(r[lo]), float(r[ag])))
                except (TypeError, ValueError):
                    continue
    return got


def coverage(cfg: dict) -> dict:
    s = settings(cfg)
    c = s["part_c"]
    lo, hi = c["age_window_bp"]
    regions = {k: (v["lat"], v["lon"]) for k, v in s["settings"].items()}
    regions["levant"] = (c["levant"]["lat"], c["levant"]["lon"])
    res = {"age_window_bp": [lo, hi], "region_km": c["region_km"], "min_dates": c["min_dates"]}
    for src, rows in (("p3k14c", p3k14c_rows()), ("nerd_v6", nerd_rows())):
        arr = np.array(rows) if rows else np.zeros((0, 3))
        inwin = arr[(arr[:, 2] >= lo) & (arr[:, 2] <= hi)] if len(arr) else arr
        per = {}
        for name, (la, lo_) in regions.items():
            if len(inwin):
                d, _ = ge.dist_bearing(la, lo_, inwin[:, 0], inwin[:, 1])
                n = int((d <= c["region_km"] / 2).sum())
            else:
                n = 0
            per[name] = {"dates": n, "enough": n >= c["min_dates"]}
        res[src] = {"dates_total": len(arr), "dates_in_age_window": len(inwin), "regions": per}
    return res


# --------------------------------------------------------------------------- hand-built tables


def dev_tables() -> dict[str, list[dict]]:
    """Hand-built tables for testing the counter before any reading exists (not the check):
    the Bible's Palestine read by hand from the verses cited (two directions inferred from
    a border's course, marked), references only."""

    def r(kind, refs, **k):
        return {"kind": kind, "refs": refs, **k}

    bible = [
        r("water", ["Numbers 34:6"], a="great sea"),
        r("direction", ["Numbers 34:6"], a="great sea", b="canaan", dir="W"),
        r("water", ["Genesis 14:3"], a="salt sea"),
        r("river", ["Joshua 15:5", "Numbers 34:12"], river="jordan", a="salt sea", role="mouth"),
        r("water", ["Numbers 34:11"], a="chinnereth"),
        r("river", ["Numbers 34:12"], river="jordan", a="chinnereth", role="bank"),
        # inferred: the border "goes down" from Chinnereth along Jordan to the salt sea
        r("direction", ["Numbers 34:11", "Numbers 34:12"], a="salt sea", b="chinnereth", dir="S"),
        r("flows", ["Numbers 34:12"], river="jordan", toward="S"),
        r("higher", ["Joshua 7:2"], a="ai", b="jericho"),
        r("direction", ["Joshua 7:2"], a="ai", b="bethel", dir="E"),
        r("near", ["Joshua 7:2"], a="ai", b="beth-aven"),
        r("river", ["Joshua 2:7", "Joshua 4:19"], river="jordan", a="jericho", role="bank"),
        r("direction", ["Judges 21:19"], a="shiloh", b="bethel", dir="N"),
        r("direction", ["Judges 21:19"], a="lebonah", b="shiloh", dir="N"),
        r("higher", ["2 Kings 2:23"], a="bethel", b="jericho"),
        r("higher", ["Genesis 13:1", "Genesis 12:10"], a="canaan", b="egypt"),
        r("sea", ["Joshua 19:29"], a="tyre", side=None),
        r("sea", ["Judges 5:17"], a="asher", side=None),
        r(
            "days",
            ["Deuteronomy 1:2"],
            a="horeb",
            b="kadesh-barnea",
            days=11.0,
            traveller="group_with_flocks",
        ),
    ]
    return {"bible_hand": bible}


# --------------------------------------------------------------------------- commands


def stamp(res: dict) -> dict:
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    res["date"] = time.strftime("%Y-%m-%d")
    return res


def write(path: Path, res: dict) -> None:
    out(path).write_text(json.dumps(stamp(res), indent=1, default=str) + "\n")


def cmd_windows(cfg: dict) -> dict:
    wins, missing = all_windows(cfg)
    s = settings(cfg)
    res = {"texts": {}, "not_attempted": missing}
    for name, rec in wins.items():
        res["texts"][name] = {
            "groups": s["texts"][name]["groups"],
            "words": rec["words"],
            "windows": rec["all_windows"],
            "coded_windows": len(rec["windows"]),
            "fixed_place_list": len(rec["places"]),
        }
        if name == "book_of_mormon":
            res["texts"][name]["coded_windows_not_quoted"] = sum(
                not w["quoted"] for w in rec["windows"]
            )
    out(CACHE / "windows.json").write_text(json.dumps(wins))
    return res


def load_windows() -> dict:
    return json.loads((CACHE / "windows.json").read_text())


def file_of(name: str, s: dict) -> str:
    groups = s["texts"][name]["groups"]
    if "known" in groups:
        return "check"
    return "book" if "book" in groups else "panel"


def cmd_jobs(cfg: dict) -> dict:
    """Judge jobs, private (they quote the passages): check texts, the panel, the book."""
    s = settings(cfg)
    wins = load_windows()
    files: dict[str, list[dict]] = {k: [] for k in JOB_FILES}
    counts: dict[str, dict] = {}
    for name, rec in wins.items():
        ids = [w["id"] for w in rec["windows"]]
        second = second_sample(ids, s["second_share"], s["seed"])
        f = file_of(name, s)
        for w in rec["windows"]:
            files[f].append({"id": w["id"], "prompt": judge_prompt(w, rec["places"])})
        for w in rec["windows"]:
            if w["id"] in second:
                files[f].append(
                    {"id": w["id"] + "#2", "prompt": judge_prompt_second(w, rec["places"])}
                )
        counts[name] = {"file": JOB_FILES[f], "first": len(ids), "second": len(second)}
    for f, jobs in files.items():
        out(CARD / JOB_FILES[f]).write_text("".join(json.dumps(j) + "\n" for j in jobs))
    per_hour = cfg["lab"]["judge"]["per_hour"]
    totals = {JOB_FILES[f]: len(j) for f, j in files.items()}
    return {
        "per_text": counts,
        "questions": totals,
        "hours_at_per_hour": {k: round(v / per_hour, 1) for k, v in totals.items()},
        "per_hour": per_hour,
        "model": s["judge_model"],
    }


def cmd_dev(cfg: dict, sizes: list[int] | None = None) -> dict:
    """The counter on hand-built tables (not the check): the Bible's strong features, its weak
    kinds only, and its layout turned 90 degrees, around Palestine."""
    s = settings(cfg)
    earth = ge.Earth(cfg)
    hand = dev_tables()["bible_hand"]
    strong = features(hand, s)
    readings = {
        "strong_literal": (strong, [0]),
        "weak_literal": (features(hand, s, "weak"), [0]),
        "rotated_literal": (rotate(strong, 2), [0]),
        "rotated_free": (rotate(strong, 2), list(range(8))),
    }
    regions = {"palestine": {"lat": 31.78, "lon": 35.22}}
    res = {
        "label": "development run on a hand-built table (19 statements from verses); "
        "not the known-answer check, which uses the coded tables",
        "features": len(strong),
        "sizes": {},
    }
    for size in sizes or [600, 1200]:
        res["sizes"][str(size)] = count_windows(earth, readings, size, s, regions)
        print(
            size,
            json.dumps(
                {
                    k: (v["pass"], v["windows"], v["undecided"])
                    for k, v in res["sizes"][str(size)]["readings"].items()
                }
            ),
            json.dumps(res["sizes"][str(size)]["regions"]),
            flush=True,
        )
    return res


def tables_from_answers(cfg: dict, which: str) -> tuple[dict, dict]:
    """Coded tables (first and second reading) for the texts whose jobs are in ``which``."""
    s = settings(cfg)
    wins = {n: r for n, r in load_windows().items() if file_of(n, s) == which}
    ans = load_answers(CARD / JOB_FILES[which].replace("jobs_", "answers_"))
    return coded_tables(wins, ans, cfg), coded_tables(wins, ans, cfg, second=True)


def known_answer(cfg: dict) -> dict:
    """Every known-answer bar, from the coded check texts. Returns the result with 'passed'."""
    s = settings(cfg)
    a = s["part_a"]
    first, second = tables_from_answers(cfg, "check")
    res: dict = {"label": "coded by the model judge (simulated reading)", "tables": {}}
    open_ = {n: t["open"] for n, t in first.items() if t["open"]}
    if open_:
        return res | {"passed": False, "stopped": f"not attempted: windows still open {open_}"}
    for n, t in first.items():
        res["tables"][n] = {
            "windows_answered": t["windows_answered"],
            "unparseable": t["unparseable"],
            "dropped": t["dropped"],
            "relations": len(t["table"]),
        }
    # agreement
    f_rel = [r for t in first.values() for r in t["relations"]]
    s_rel = [r for t in second.values() for r in t["relations"]]
    sec_windows = {
        k.removesuffix("#2") for k in load_answers(CARD / "answers_check.jsonl") if k.endswith("#2")
    }
    kp = kappa([r for r in f_rel if r["window"] in sec_windows], s_rel)
    res["agreement"] = kp | {
        "bar": s["kappa_bar"],
        "passed": kp["kappa"] is not None and kp["kappa"] >= s["kappa_bar"],
    }
    earth = ge.Earth(cfg)
    coords = {"openbible": openbible_coords(), "pleiades": pleiades_coords()}
    # extractor
    ex = {}
    for n in ("kjv_narrative", "xenophon_1813"):
        tab = first[n]["table"]
        c = coords[s["texts"][n]["region"]]
        reg = true_region(n, tab, s, c)
        ex[n] = (
            extractor_check(tab, c, reg, earth, s, s["seed"])
            if reg
            else {"stopped": "not attempted: too few placed places"}
        )
        ex[n]["region"] = reg
    res["extractor"] = ex
    ext_pass = all(v.get("passed") for v in ex.values()) and res["agreement"]["passed"]
    # Part A
    pa = {}
    for n in (
        "kjv_narrative",
        "josephus_war",
        "xenophon_1813",
        "lewis_clark_1814",
        "hunt_late_war_1816",
    ):
        tab = first[n]["table"]
        spec = s["texts"][n]
        reg = true_region(n, tab, s, coords.get(spec.get("region")))
        if reg is None:
            pa[n] = {"stopped": "not attempted: no region"}
            continue
        strong = features(tab, s)
        readings = {"literal": (strong, [0])}
        if n == "kjv_narrative":
            readings |= {
                "weak_only": (features(tab, s, "weak"), [0]),
                "rotated_literal": (rotate(strong, 2), [0]),
                "rotated_free": (rotate(strong, 2), list(range(8))),
            }
        c = count_windows(earth, readings, reg["diameter"], s, {"own": reg})
        lit = c["readings"]["literal"]
        own = c["regions"]["own"]["literal"]["passes"]
        pa[n] = {
            "region": reg,
            "features": len(strong),
            "count": c,
            "passes": own and lit["specificity_upper"] <= a["specific_bar"],
        }
    res["part_a"] = pa
    bible = pa.get("kjv_narrative", {})
    weak_ok = rot_ok = False
    if "count" in bible:
        rd = bible["count"]["readings"]
        weak_ok = rd["weak_only"]["specificity"] > a["unspecific_bar"]
        regs = bible["count"]["regions"]["own"]
        rot_ok = (not regs["rotated_literal"]["passes"]) and regs["rotated_free"]["passes"]
    n_pass = sum(bool(v.get("passes")) for v in pa.values())
    res["part_a_check"] = {
        "bible_passes": bool(bible.get("passes")),
        "known_texts_passing": n_pass,
        "weak_only_unspecific": weak_ok,
        "rotation_check": rot_ok,
        "passed": bool(bible.get("passes"))
        and n_pass >= a["known_min_pass"]
        and weak_ok
        and rot_ok,
    }
    if bible and "count" in bible and not weak_ok:
        res["part_a_check"]["stop"] = (
            "the weak-only table came out specific: the counter is wrong; the run stops"
        )
    # step 2's own check: the Bible's basic layout rebuilt and Palestine graded
    res["their_way_check"] = bible_layout_check(
        first["kjv_narrative"]["table"], coords["openbible"], earth, s
    )
    res["passed"] = {
        "extractor": ext_pass,
        "part_a": res["part_a_check"]["passed"],
        "their_way": res["their_way_check"]["passed"],
    }
    return res


BIBLE_LAYOUT = {
    "sea_west": [
        {"kind": "sea", "a": "jerusalem", "side": "W"},
        {"kind": "direction", "a": "great sea", "b": "jerusalem", "dir": "W"},
    ],
    "jordan_south_into_salt_sea": [
        {"kind": "flows", "river": "jordan", "toward": "S"},
        {"kind": "river", "river": "jordan", "a": "salt sea", "role": "mouth"},
    ],
    "hill_country_up_from_jericho": [
        {"kind": "higher", "a": "jerusalem", "b": "jericho"},
        {"kind": "higher", "a": "bethel", "b": "jericho"},
        {"kind": "higher", "a": "ai", "b": "jericho"},
    ],
}


def bible_layout_check(table: list[dict], coords: dict, earth: ge.Earth, s: dict) -> dict:
    """Step 2's known answer: each part of Palestine's basic layout is rebuilt when the table
    states any of its forms; Palestine is graded on the forms found, at true coordinates."""
    res = {}
    for part, forms in BIBLE_LAYOUT.items():
        found = [f for f in forms if any(matches(f, r) for r in table)]
        graded = []
        for f in found:
            if f["kind"] in ("river", "flows"):
                r = next((x for x in earth.rivers if x["name"] == "Jordan"), None)
                pos = {k: v for k, v in coords.items()}
                g = (
                    grade_feature(
                        f | {"cone": s["part_a"]["flow_cone"]},
                        pos,
                        {"jordan": "Jordan"},
                        0,
                        earth,
                        s,
                        s["their_way"],
                    )
                    if r
                    else "cannot grade"
                )
            else:
                f2 = f | {"cone": s["part_a"]["dir_cone_strong"]}
                h = holds(f2, coords, earth, s)
                g = "cannot grade" if h is None else ("pass" if h else "fail")
            graded.append({"form": f, "grade": g})
        res[part] = {
            "rebuilt": bool(found),
            "graded": graded,
            "palestine_meets": any(x["grade"] == "pass" for x in graded),
        }
    res["passed"] = all(
        v["rebuilt"] and v["palestine_meets"] for v in res.values() if isinstance(v, dict)
    )
    return res


def cmd_check(cfg: dict) -> dict:
    res = known_answer(cfg)
    write(OUT / "check.json", res)
    return res


def cmd_run(cfg: dict) -> dict:
    """The check, then the book on each part whose check passed, Part B, and step 2."""
    s = settings(cfg)
    a = s["part_a"]
    chk = known_answer(cfg)
    res: dict = {"check": {k: chk.get(k) for k in ("passed", "agreement", "part_a_check")}}
    if "stopped" in chk:
        res["stopped"] = chk["stopped"]
        write(OUT / "result.json", res)
        return res
    earth = ge.Earth(cfg)
    book_first, _ = tables_from_answers(cfg, "book")
    panel_first, _ = tables_from_answers(cfg, "panel")
    check_first, _ = tables_from_answers(cfg, "check")
    wins = load_windows()
    quoted = {w["id"] for w in wins.get("book_of_mormon", {}).get("windows", []) if w["quoted"]}
    btab = book_first.get("book_of_mormon")
    if btab is None or btab["open"]:
        res["stopped"] = "not attempted: the book's windows are not all answered"
        write(OUT / "result.json", res)
        return res
    generic = set(s["generic_places"])
    tables = {
        "book_of_mormon": btab["table"],
        "book_of_mormon_without_quoted": build_table(
            [r for r in btab["relations"] if r["window"] not in quoted], generic
        ),
    }
    # step 2: their way (reported in any case, labelled with its own check)
    placements = json.loads(PLACEMENTS.read_text())
    res["their_way"] = {
        "own_check_passed": chk["passed"]["their_way"],
        "rebuilt_from_book": clark_rebuilt(tables["book_of_mormon"]),
        "grades": {
            name: {
                str(r): grade_setting(placements[name], r, earth, s)
                for r in s["settings"][name]["rotations"]
            }
            for name in s["settings"]
        },
    }
    # Part A
    if chk["passed"]["extractor"] and chk["passed"]["part_a"]:
        regions = {
            k: {
                "lat": v["lat"],
                "lon": v["lon"],
                "rotations": {"literal": [0], "free": v["rotations"], "clark": v["rotations"]},
            }
            for k, v in s["settings"].items()
        }
        part_a = {}
        for tname, tab in tables.items():
            strong = features(tab, s)
            readings = {
                "literal": (strong, [0]),
                "free": (strong, list(range(8))),
                "clark": (clark_features(s), list(range(8))),
                "repeated_literal": (features(tab, s, min_refs=2), [0]),
            }
            sizes = {}
            for size in a["sizes_km"]:
                c = count_windows(earth, readings, size, s, regions)
                for rd, v in c["readings"].items():
                    v["verdicts"] = {
                        st: part_a_verdict(
                            v["specificity"],
                            v["specificity_upper"],
                            c["regions"][st][rd]["passes"],
                            a,
                        )
                        for st in regions
                    }
                sizes[str(size)] = c
            part_a[tname] = {"features": len(strong), "sizes": sizes}
        res["part_a"] = part_a
        res["part_a_invented"] = invented_part_a(cfg, earth, panel_first)
    else:
        res["part_a"] = "not scored: the extractor or Part A known-answer check missed its bar"
    # Part B
    res["part_b"] = part_b(
        cfg,
        {
            **{n: t["table"] for n, t in check_first.items()},
            **{n: t["table"] for n, t in panel_first.items()},
        },
        tables,
    )
    write(OUT / "result.json", res)
    return res


def invented_part_a(cfg: dict, earth: ge.Earth, panel: dict) -> dict:
    """Invented maps' chance fits at every size, literal reading (reported, no bar); Spalding's
    also at the Ohio mounds (the hard decoy for every physical fit)."""
    s = settings(cfg)
    res = {}
    for name in s["invented_part_a"]:
        if name not in panel:
            res[name] = "not attempted: no coded table"
            continue
        strong = features(panel[name]["table"], s)
        regions = {"ohio": s["spalding_region"]} if name == "spalding_manuscript" else {}
        res[name] = {
            "features": len(strong),
            "sizes": {
                str(z): count_windows(earth, {"literal": (strong, [0])}, z, s, regions)
                for z in s["part_a"]["sizes_km"]
            },
        }
    return res


def part_b(cfg: dict, panel: dict[str, list[dict]], book: dict[str, list[dict]]) -> dict:
    s = settings(cfg)
    n = len(consistency_statements(book["book_of_mormon"]))
    rows = {}
    for name, tab in panel.items():
        rows[name] = subsampled(tab, n, s, s["seed"]) | {"groups": s["texts"][name]["groups"]}
    real = [
        v["rate"]
        for v in rows.values()
        if "real" in v["groups"]
        and v["rate"] is not None
        and v["statements"] >= s["part_b_min_statements"]
    ]
    inv = [
        v["rate"]
        for v in rows.values()
        if "invented" in v["groups"]
        and v["rate"] is not None
        and v["statements"] >= s["part_b_min_statements"]
    ]
    a_ = auc(real, inv)
    res = {
        "book_statements": n,
        "texts": rows,
        "real_texts": len(real),
        "invented_texts": len(inv),
        "auc": a_,
    }
    enough = len(real) >= s["part_b"]["min_texts"] and len(inv) >= s["part_b"]["min_texts"]
    res["discriminates"] = bool(enough and a_ is not None and a_ >= s["part_b"]["auc_bar"])
    res["book"] = {}
    for bname, tab in book.items():
        c = consistency(consistency_statements(tab), s)
        res["book"][bname] = c | {
            "placed": place_book(c["rate"], real, inv)
            if res["discriminates"] and c["rate"] is not None
            else "no verdict: Part B does not discriminate in this panel"
        }
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["earth", "windows", "jobs", "dev", "coverage", "check", "run"])
    ap.add_argument("--sizes", type=int, nargs="*")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "earth":
        print(json.dumps(ge.build(cfg), indent=1))
    elif a.cmd == "windows":
        res = cmd_windows(cfg)
        write(OUT / "windows.json", res)
        print(json.dumps(res, indent=1))
    elif a.cmd == "jobs":
        res = cmd_jobs(cfg)
        write(OUT / "jobs.json", res)
        print(json.dumps(res, indent=1))
    elif a.cmd == "dev":
        res = cmd_dev(cfg, a.sizes)
        write(OUT / "dev_hand_tables.json", res)
    elif a.cmd == "coverage":
        res = coverage(cfg)
        write(OUT / "coverage.json", res)
        print(json.dumps(res, indent=1))
    elif a.cmd == "check":
        res = cmd_check(cfg)
        print(json.dumps({k: res.get(k) for k in ("passed", "stopped")}, indent=1, default=str))
    else:
        res = cmd_run(cfg)
        print(json.dumps({k: res.get(k) for k in ("check", "stopped")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
