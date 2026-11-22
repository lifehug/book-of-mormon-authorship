"""BOM-116: do the book's directions and distances fit any real region better than chance?

One written rule pulls a text's geographic statements into a constraint table: which named place
is north, south, east or west of which; travel up or down from one named place to another; so many
days' journey between two; a place by the sea (and on which side); a narrow neck of land; two
places near each other. Every constraint keeps its references (1830 book, chapter and paragraph;
Bible verse; paragraph number of other texts) and no text.

Then (1) **internal consistency**: can all the direction and up/down statements hold at once on a
plane, and which statements make a cycle; how many places they tie together. (2) **Extractor
check**: the Bible's statements, scored with the places' coordinates from OpenBible.info's
geocoding (CC BY 4.0), against random assignments of the same places to real points in the same
window. (3) **Region fit**: in a window of the earth (sites from GeoNames, CC BY 4.0, with
elevation and nearness to the sea from GeoNames coastal features), an optimiser gives each of the
text's places its best site, and the share of statements satisfied is the window's score. Each
proposed setting is a window; the baseline is the same score in many windows centred on random
land points. A known-geography text (Bible narrative and Josephus for Palestine; Bernal Diaz for
Mexico; Hunt's *Late War* for the Great Lakes frontier) must place its own region above the
decoys before the Book of Mormon is scored.

Window centres are looked up in GeoNames by the names in ``lab.geography.anchors``; which name
stands for each proposed setting was chosen from memory of the models' general descriptions, not
from the authors' maps (no published placement is on disk). The test card, written first, is
``data/private/lab/owner/2026-11-21-geography/card.md``; settings are ``lab.geography``.

Usage::

    python -m lab.geography cache     # read GeoNames once -> data/corpus/lab/geography/ (10 s)
    python -m lab.geography extract   # constraint tables, known texts only; counts (10 s)
    python -m lab.geography check     # known-answer checks only (1 min)
    python -m lab.geography run       # -> data/lab/setting/geography/result.json (2 min)
"""

from __future__ import annotations

import argparse
import io
import json
import math
import random
import re
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from lab.paths import FAST, REGISTRY, out
from metadata import config

OUT = REGISTRY / "setting" / "geography"
CACHE = FAST / "geography"
SOURCES = FAST / "sources"
GEONAMES = SOURCES / "places" / "geonames_allCountries.zip"
OPENBIBLE = SOURCES / "names" / "bible_geocoding" / "data" / "ancient.jsonl"
KJV = Path("data/kjv/kjv.jsonl")
EARTH_KM = 6371.0
DIRS = ("north", "east", "south", "west")
BEARING = {"north": 0.0, "east": 90.0, "south": 180.0, "west": 270.0}
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}

# --------------------------------------------------------------------------- the written rule

# Phrases that name a part of the land rather than a place; each becomes one pseudo-place.
PSEUDO = [
    (r"\bnarrow\s+neck(?:\s+of\s+land)?\b|\bneck\s+of\s+land\b|\bisthmus\b|\bnarrow\s+pass\b",
     "Narrowneck"),
    (r"\bland\s+northward\b|\bnorth\s+country\b", "Landnorthward"),
    (r"\bland\s+southward\b|\bsouth\s+country\b", "Landsouthward"),
    (r"\bland\s+eastward\b|\beast\s+country\b", "Landeastward"),
    (r"\bland\s+westward\b|\bwest\s+country\b", "Landwestward"),
]  # fmt: skip
PLACE_WORD = (
    r"\b(?:land|lands|city|cities|country|province|town|village|river|mount|hill|valley|"
    r"wilderness|plains|borders|waters|sea|coasts|fort|lake|bay|island|isle|port|harbour|"
    r"harbor|creek|state|county|district|territory|kingdom|region|tribe)\s+(?:of\s+|called\s+)?"
    r"(?:the\s+)?"
)
MOTION = (
    r"\b(?:went|go|goeth|going|gone|came|come|cometh|coming|journeyed|travelled|traveled|"
    r"marched|fled|returned|departed|passed|removed|sailed|arrived|retreated|advanced)"
    r"(?:\s+(?:up|down|over|forth|back|away|again|out))?\s+(?:to|into|from|out\s+of|toward|"
    r"towards|unto\s+the\s+land\s+of|unto\s+the\s+city\s+of)\s+(?:the\s+)?"
)
LOC_PREP = r"\b(?:at|in|into|from|near|towards?|to)\s+(?:the\s+)?"
NAME = r"([A-Z][a-z]+(?:[- ][A-Z][a-z]+)*)"
NOT_PLACES = {
    "God", "Lord", "Christ", "Jesus", "Holy", "Ghost", "Spirit", "The", "And", "But", "For",
    "Then", "Now", "Behold", "Yea", "They", "Their", "There", "This", "That", "These", "When",
    "His", "Her", "Our", "Your", "Thou", "Thy", "Thee", "Lamanites", "Nephites", "Israel",
    "Father", "Son", "Heaven", "Indians", "Americans", "British", "English", "Spaniards",
    "Jews", "Romans", "General", "Captain", "Colonel", "King", "Sir", "Mr", "Chapter",
    "Mount", "Lake", "River", "City", "Land", "Fort", "Sea", "Bay", "Cape", "Point", "Island",
    "Isle", "Port", "Valley", "Mountain", "Mountains", "Hill", "Hills", "Book", "North", "South",
    "East", "West", "Great", "Little", "New", "Old", "Upper", "Lower", "St", "Saint", "Of",
}  # fmt: skip
UNITS = re.compile(
    r"\b([a-z]+(?:\s+hundred)?|\d+)(\s+and\s+a\s+half)?\s+(furlongs?|miles?|leagues?)\s+"
    r"(?:distant\s+from|off\s+from|from|of)\b"
)
CUE_DISTANT = re.compile(r"\bdistant\s+(?:about\s+)?from\b")
UNITS_AFTER = re.compile(
    r"^\W*(?:about\s+|above\s+|nearly\s+|near\s+)?([a-z]+(?:\s+hundred)?|\d+)"
    r"(\s+and\s+a\s+half)?\s+(furlongs?|miles?|leagues?)\b"
)
CUE_DIR = re.compile(
    r"\b(north|south|east|west)(?:ward)?(?:\s+(?:side|quarter|border|borders|part|parts|end))?"
    r"\s+of\b"
)
CUE_BORDER = re.compile(r"\bon\s+the\s+(north|south|east|west)(?:\s+(?:side|quarter))?\s+by\b")
CUE_UPDOWN = re.compile(
    r"\b(?:went|go|goeth|going|gone|came|come|cometh|coming|journeyed|travelled|traveled|"
    r"marched|fled|returned|departed|passed|carried|brought|led|took|sent|retreated)"
    r"(?:\s+(?:them|him|it|their\s+armies|his\s+army))?\s+(up|down)\b|\b(ascended|descended)\b"
)
CUE_DAYS = re.compile(
    r"\b([a-z]+|\d+)(\s+and\s+a\s+half)?\s+days?(?:'|’)?s?\s+journey\b"
    r"|\bjourney\s+of\s+([a-z]+|\d+)(\s+and\s+a\s+half)?\s+days?\b"
    r"|\b(a|one)\s+day\s+(and\s+a\s+half)(?:'|’)?s?\s+journey\b"
)
CUE_SEA = re.compile(
    r"\b(?:by|upon|on|near|unto|to|along|beside|toward|towards)\s+the\s+(?:great\s+|red\s+)?"
    r"(?:sea[-\s]?(?:shore|side|coast)|seashore|seaside|sea)\b(?!\s+of\b)"
    r"(?:\s+(north|south|east|west)\b)?"
)
CUE_TWO_SEAS = re.compile(
    r"\bfrom\s+the\s+(?:sea\s+(north|south|east|west)|(north|south|east|west)\s+sea)\b"
    r"[^.]{0,60}?\bto\s+the\s+(?:sea\s+(north|south|east|west)|(north|south|east|west)\s+sea)\b"
)
CUE_NEAR = re.compile(
    r"\b(?:near|nigh)(?:\s+(?:un)?to)?\b|\bbeside\b|\bover\s+against\b|\bbordering\s+(?:up)?on\b"
    r"|\badjoining\b"
)
# "from" / "to" before a place, allowing "the land of", "the city of" and the like between.
LEAD = (
    r"\s+(?:the\s+)?(?:(?:land|city|country|province|town|village|wilderness|valley|hill|mount)"
    r"s?\s+(?:of\s+)?(?:the\s+)?)?$"
)
FROM = re.compile(r"\b(?:from|out\s+of)" + LEAD)
TO = re.compile(r"\b(?:to|unto|into|towards?|against)" + LEAD)
NUMBERS = {
    "a": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
}  # fmt: skip


def normalise(text: str) -> str:
    """Rejoin broken words, fold spaces, and turn each pseudo-place phrase into one token."""
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    for pat, tok in PSEUDO:
        text = re.sub(pat, tok, text, flags=re.I)
    return text


def lexicon(units: list[tuple[str, str]], w: dict) -> list[str]:
    """The text's place names: capitalised words named at least ``min_mentions`` times after a
    place word or after a verb of motion and its preposition; never a name that is more often
    the subject of "said" or the object of "said unto"."""
    count: dict[str, int] = defaultdict(int)
    person: dict[str, int] = defaultdict(int)
    for _ref, t in units:
        for pat in (PLACE_WORD, MOTION, LOC_PREP):
            for m in re.finditer(pat + NAME, t):
                count[m.group(1)] += 1
        for m in re.finditer(NAME + r"\s+(?:said|saith|spake|answered)\b", t):
            person[m.group(1)] += 1
        kin = r"\b(?:said|spake)\s+unto\s+|\b(?:son|sons|daughter|wife|brother|father)\s+of\s+"
        for m in re.finditer(kin + NAME, t):
            person[m.group(1)] += 1
    names = {
        n
        for n, c in count.items()
        if c >= w["min_mentions"]
        and not all(x in NOT_PLACES for x in re.split(r"[- ]", n))
        and person[n] < c
    }
    names |= {tok for _p, tok in PSEUDO if any(tok in t for _r, t in units)}
    return sorted(names)


def sentences(text: str, max_chars: int) -> list[str]:
    return [s for s in re.split(r"(?<=[.?!])\s+", text) if s and len(s) <= max_chars]


def mentions(s: str, names_re: re.Pattern) -> list[tuple[int, int, str]]:
    return [(m.start(), m.end(), m.group(1)) for m in names_re.finditer(s)]


def before(ms, pos: int, gap: int):
    c = [m for m in ms if m[1] <= pos and pos - m[1] <= gap]
    return c[-1] if c else None


def after(ms, pos: int, gap: int):
    c = [m for m in ms if m[0] >= pos and m[0] - pos <= gap]
    return c[0] if c else None


def number(word: str) -> int | None:
    """A count written in digits or in one number word, or "<word> hundred"."""
    if word.isdigit():
        return int(word)
    parts = word.split()
    if len(parts) == 2 and parts[1] == "hundred" and parts[0] in NUMBERS:
        return NUMBERS[parts[0]] * 100
    return NUMBERS.get(word)


def extract(units: list[tuple[str, str]], w: dict) -> dict:
    """Constraint table of one text: ``units`` are (reference, text). Constraints are merged
    when identical and keep every reference."""
    units = [(r, normalise(t)) for r, t in units]
    names = lexicon(units, w)
    if not names:
        return {"places": [], "constraints": []}
    alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    names_re = re.compile(r"\b(" + alt + r")\b")
    gap = w["max_gap_chars"]
    found: dict[tuple, list[str]] = defaultdict(list)

    def add(kind, a, b, extra, ref):
        if a and (b is None or a != b):
            found[(kind, a, b, extra)].append(ref)

    for ref, t in units:
        for s in sentences(t, w["sentence_max_chars"]):
            ms = mentions(s, names_re)
            if not ms:
                continue
            for m in CUE_DIR.finditer(s):
                x, y = before(ms, m.start(), gap), after(ms, m.end(), gap)
                if x and y:
                    add("direction", x[2], y[2], m.group(1), ref)
            for m in CUE_BORDER.finditer(s):
                x, y = before(ms, m.start(), gap), after(ms, m.end(), gap)
                if x and y:
                    add("direction", y[2], x[2], m.group(1), ref)
            for m in CUE_UPDOWN.finditer(s):
                way = (m.group(1) or ("up" if m.group(2) == "ascended" else "down")).lower()
                lo, hi = max(0, m.start() - gap), min(len(s), m.end() + 2 * gap)
                origin = dest = None
                for x in ms:
                    if lo <= x[0] <= hi and FROM.search(s[max(0, x[0] - 30) : x[0]]):
                        origin = origin or x
                    if m.end() <= x[0] <= hi and TO.search(s[max(0, x[0] - 30) : x[0]]):
                        dest = dest or x
                if origin and dest:
                    hi_place, lo_place = (dest, origin) if way == "up" else (origin, dest)
                    add("higher", hi_place[2], lo_place[2], None, ref)
            for m in CUE_DAYS.finditer(s):
                n = number(m.group(1) or m.group(3) or m.group(5) or "")
                if not n:
                    continue
                half = 0.5 if (m.group(2) or m.group(4) or m.group(6)) else 0.0
                origin = dest = None
                for x in ms:
                    pre = s[max(0, x[0] - 30) : x[0]]
                    if FROM.search(pre):
                        origin = origin or x
                    elif TO.search(pre):
                        dest = dest or x
                if origin and dest:
                    a, b = sorted((origin[2], dest[2]))
                    add("days", a, b, n + half, ref)
            for m in UNITS.finditer(s):
                n = number(m.group(1))
                x, y = before(ms, m.start(), gap), after(ms, m.end(), gap)
                if n and x and y:
                    km = (n + (0.5 if m.group(2) else 0.0)) * w["unit_km"][m.group(3).rstrip("s")]
                    a, b = sorted((x[2], y[2]))
                    add("distance", a, b, round(km, 1), ref)
            for m in CUE_DISTANT.finditer(s):
                x, y = before(ms, m.start(), gap), after(ms, m.end(), 25)
                u = UNITS_AFTER.match(s[y[1] :]) if y else None
                n = number(u.group(1)) if u else None
                if n and x:
                    km = (n + (0.5 if u.group(2) else 0.0)) * w["unit_km"][u.group(3).rstrip("s")]
                    a, b = sorted((x[2], y[2]))
                    add("distance", a, b, round(km, 1), ref)
            for m in CUE_SEA.finditer(s):
                x = before(ms, m.start(), gap) or after(ms, m.end(), gap)
                if x:
                    add("sea", x[2], None, m.group(1), ref)
            for m in CUE_TWO_SEAS.finditer(s):
                x = before(ms, m.start(), gap)
                d1, d2 = m.group(1) or m.group(2), m.group(3) or m.group(4)
                if x and d1 != d2:
                    add("sea", x[2], None, d1, ref)
                    add("sea", x[2], None, d2, ref)
            for m in CUE_NEAR.finditer(s):
                x, y = before(ms, m.start(), gap), after(ms, m.end(), gap)
                if x and y:
                    a, b = sorted((x[2], y[2]))
                    add("near", a, b, None, ref)
    first = {}
    for ref, t in units:
        if "Narrowneck" in t and "Narrowneck" not in first:
            first["Narrowneck"] = ref
    if "Narrowneck" in first:
        add("isthmus", "Narrowneck", None, None, first["Narrowneck"])
    for d in ("north", "east"):
        a, b = f"Land{d}ward", f"Land{OPPOSITE[d]}ward"
        if a in names and b in names:
            add("direction", a, b, d, "implied by the two names")
    cons = [
        {"kind": k, "a": a, "b": b, "value": v, "refs": refs}
        for (k, a, b, v), refs in sorted(found.items(), key=lambda kv: str(kv[0]))
    ]
    used = sorted({c["a"] for c in cons} | {c["b"] for c in cons if c["b"]})
    return {"lexicon_size": len(names), "places": used, "constraints": cons}


def summary(table: dict) -> dict:
    by = defaultdict(int)
    for c in table["constraints"]:
        by[c["kind"]] += 1
    return {
        "lexicon_size": table.get("lexicon_size", 0),
        "places_in_constraints": len(table["places"]),
        "constraints": len(table["constraints"]),
        "by_kind": dict(sorted(by.items())),
    }


# --------------------------------------------------------------------------- the texts


def kjv_units(books: list[str]) -> list[tuple[str, str]]:
    keep = set(books)
    rows = map(json.loads, KJV.read_text().splitlines())
    return [(r["ref"], r["text"]) for r in rows if r["book"] in keep]


def paragraph_units(text: str) -> list[tuple[str, str]]:
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [(f"para {i + 1}", p) for i, p in enumerate(paras)]


def bom_units(without_quoted: bool) -> list[tuple[str, str]]:
    from lab.wherefore import EDITION, LABELS, QUOTED

    labels = {r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines())}
    got = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        if r["kind"] != "body":
            continue
        lab = labels.get(r["seq"], {})
        ch = lab.get("chapter_1830")
        if without_quoted and (r["book"], ch) in QUOTED:
            continue
        got.append((f"{r['book']} {ch} para {r['seq']}", r["text"]))
    return got


def text_units(spec: dict) -> list[tuple[str, str]] | None:
    """Units of one text in ``lab.geography.texts``; None when it cannot be read."""
    if spec["source"] == "kjv":
        return kjv_units(spec["books"])
    if spec["source"] == "file":
        f = Path(spec["path"])
        return paragraph_units(f.read_text(errors="replace")) if f.exists() else None
    if spec["source"] == "library":
        from lab.placenames import library_text

        t = library_text(spec["work_id"])
        return paragraph_units(t) if t else None
    if spec["source"] == "bom":
        return bom_units(spec.get("without_quoted", False))
    raise ValueError(spec["source"])


# --------------------------------------------------------------------------- internal consistency


def cycles(cons: list[dict]) -> dict:
    """Direction (north-south and east-west orders) and elevation statements as order graphs: the
    statements inside a cycle cannot all hold at once on a plane."""
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components

    orders: dict[str, list[tuple[str, str, dict]]] = {"north_south": [], "east_west": []}
    orders["elevation"] = []
    for c in cons:
        if c["kind"] == "direction":
            axis = "north_south" if c["value"] in ("north", "south") else "east_west"
            hi, lo = (c["a"], c["b"]) if c["value"] in ("north", "east") else (c["b"], c["a"])
            orders[axis].append((lo, hi, c))
        elif c["kind"] == "higher":
            orders["elevation"].append((c["b"], c["a"], c))
    res = {}
    for axis, edges in orders.items():
        nodes = sorted({x for e in edges for x in e[:2]})
        idx = {n: i for i, n in enumerate(nodes)}
        bad = []
        if edges:
            m = csr_matrix(
                ([1] * len(edges), ([idx[e[0]] for e in edges], [idx[e[1]] for e in edges])),
                shape=(len(nodes), len(nodes)),
            )
            _n, lab = connected_components(m, directed=True, connection="strong")
            bad = [e[2] for e in edges if lab[idx[e[0]]] == lab[idx[e[1]]]]
        res[axis] = {
            "statements": len(edges),
            "in_a_cycle": len(bad),
            "cycles": [{"a": c["a"], "b": c["b"], "value": c["value"], "refs": c["refs"]}
                       for c in bad],
        }  # fmt: skip
    places = sorted({c["a"] for c in cons} | {c["b"] for c in cons if c["b"]})
    idx = {n: i for i, n in enumerate(places)}
    pairs = [(idx[c["a"]], idx[c["b"]]) for c in cons if c["b"]]
    if pairs:
        rows, cols = [p[0] for p in pairs], [p[1] for p in pairs]
        m = csr_matrix(([1] * len(pairs), (rows, cols)), shape=(len(places),) * 2)
        _n, lab = connected_components(m, directed=False)
        sizes = sorted(np.bincount(lab).tolist(), reverse=True)
    else:
        sizes = [1] * len(places)
    res["places"] = len(places)
    res["groups_of_linked_places"] = len(sizes)
    res["largest_group"] = sizes[0] if sizes else 0
    res["places_with_one_statement"] = sum(
        1 for p in places if sum(p in (c["a"], c["b"]) for c in cons) == 1
    )
    return res


# --------------------------------------------------------------------------- GeoNames


def build_cache(cfg: dict) -> None:
    """Read GeoNames once: settlements (with elevation), coastal features, anchor entries."""
    w = cfg["lab"]["geography"]
    codes = set(w["coast_codes"])
    anchor_names = {a["name"] for a in w["anchors"].values()}
    s_lat, s_lon, s_dem, s_pop = [], [], [], []
    c_lat, c_lon = [], []
    anchors = []
    member = "allCountries.txt"  # read, not written
    with zipfile.ZipFile(GEONAMES) as z, z.open(member) as fh:
        for line in io.TextIOWrapper(fh, encoding="utf-8"):
            f = line.split("\t")
            if f[7] in codes:
                c_lat.append(float(f[4]))
                c_lon.append(float(f[5]))
            if f[6] == "P" and f[16] not in ("", "-9999"):
                s_lat.append(float(f[4]))
                s_lon.append(float(f[5]))
                s_dem.append(float(f[16]))
                s_pop.append(int(f[14] or 0))
            if f[2] in anchor_names:
                anchors.append(
                    {"geonameid": int(f[0]), "name": f[2], "lat": float(f[4]),
                     "lon": float(f[5]), "fclass": f[6], "code": f[7], "cc": f[8],
                     "admin1": f[10], "population": int(f[14] or 0)}
                )  # fmt: skip
    path = out(CACHE / "geonames.npz")
    np.savez(  # the path comes from out( above
        path,
        s_lat=np.array(s_lat, dtype=np.float32),
        s_lon=np.array(s_lon, dtype=np.float32),
        s_dem=np.array(s_dem, dtype=np.float32),
        s_pop=np.array(s_pop, dtype=np.int64),
        c_lat=np.array(c_lat, dtype=np.float32),
        c_lon=np.array(c_lon, dtype=np.float32),
    )
    meta = {"settlements": len(s_lat), "coastal_features": len(c_lat), "anchors": anchors}
    out(CACHE / "geonames.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: v for k, v in meta.items() if k != "anchors"}))


def unit(lat, lon) -> np.ndarray:
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


def chord(km: float) -> float:
    return 2 * math.sin(km / EARTH_KM / 2)


def dist_bearing(lat1, lon1, lat2, lon2) -> tuple[np.ndarray, np.ndarray]:
    """Great-circle km and initial bearing (degrees) from point 1 to point 2 (broadcasting)."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2) - np.radians(lon1)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    d = 2 * EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return d, (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0


def within(bearing: np.ndarray, d: str, cone: float) -> np.ndarray:
    diff = np.abs((bearing - BEARING[d] + 180.0) % 360.0 - 180.0)
    return diff <= cone


class Earth:
    """GeoNames settlements and coastal features, indexed for window queries."""

    def __init__(self, w: dict):
        z = np.load(CACHE / "geonames.npz")
        self.lat, self.lon = z["s_lat"].astype(float), z["s_lon"].astype(float)
        self.dem, self.pop = z["s_dem"].astype(float), z["s_pop"]
        self.c_lat, self.c_lon = z["c_lat"].astype(float), z["c_lon"].astype(float)
        self.tree = cKDTree(unit(self.lat, self.lon))
        self.ctree = cKDTree(unit(self.c_lat, self.c_lon))
        self.meta = json.loads((CACHE / "geonames.json").read_text())
        self.w = w

    def anchor(self, spec: dict) -> dict | None:
        c = [
            a
            for a in self.meta["anchors"]
            if a["name"] == spec["name"]
            and a["cc"] == spec["cc"]
            and ("admin1" not in spec or a["admin1"] == spec["admin1"])
        ]
        return max(c, key=lambda a: (a["fclass"] == "P", a["population"])) if c else None

    def coast_flags(self, lat: np.ndarray, lon: np.ndarray) -> dict:
        """For each point: a coastal feature within ``coast_km``; one in each quadrant within
        ``side_km``; a neck (coastal features in two opposite quadrants)."""
        w = self.w
        n = len(lat)
        near = np.zeros(n, dtype=bool)
        side = {d: np.zeros(n, dtype=bool) for d in DIRS}
        hits = self.ctree.query_ball_point(unit(lat, lon), chord(w["side_km"]))
        for i, h in enumerate(hits):
            if not h:
                continue
            h = np.asarray(h)
            d, b = dist_bearing(lat[i], lon[i], self.c_lat[h], self.c_lon[h])
            near[i] = bool((d <= w["coast_km"]).any())
            for q in DIRS:
                side[q][i] = bool(within(b, q, 45.0).any())
        neck = (side["north"] & side["south"]) | (side["east"] & side["west"])
        return {"near": near, "side": side, "neck": neck}

    def window(self, lat: float, lon: float, radius: float) -> dict | None:
        """The window's sites: the most populous settlement in each grid cell."""
        idx = np.asarray(self.tree.query_ball_point(unit(lat, lon), chord(radius)), dtype=int)
        if len(idx) == 0:
            return None
        d, b = dist_bearing(lat, lon, self.lat[idx], self.lon[idx])
        cell = radius / self.w["cells_per_radius"]
        x, y = d * np.sin(np.radians(b)), d * np.cos(np.radians(b))
        key = np.floor(x / cell).astype(int) * 100003 + np.floor(y / cell).astype(int)
        order = np.lexsort((-self.pop[idx], key))
        first = np.r_[True, key[order][1:] != key[order][:-1]]
        pick = idx[order[first]]
        slat, slon = self.lat[pick], self.lon[pick]
        return {"lat": slat, "lon": slon, "dem": self.dem[pick], **self.coast_flags(slat, slon)}

    def snap_dem(self, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
        d, i = self.tree.query(unit(lat, lon))
        km = 2 * EARTH_KM * np.arcsin(np.clip(d / 2, 0, 1))
        return np.where(km <= self.w["elevation_snap_km"], self.dem[i], np.nan)


# --------------------------------------------------------------------------- scoring


def compile_constraints(cons: list[dict], kinds: set[str] | None = None) -> tuple[list, list]:
    """(places, constraints as tuples of (kind, i, j, value)) for the optimiser."""
    cons = [c for c in cons if kinds is None or c["kind"] in kinds]
    places = sorted({c["a"] for c in cons} | {c["b"] for c in cons if c["b"]})
    idx = {p: i for i, p in enumerate(places)}
    return places, [
        (c["kind"], idx[c["a"]], idx[c["b"]] if c["b"] else -1, c["value"]) for c in cons
    ]


def with_pairs(win: dict) -> dict:
    """The window with its pairwise distances and bearings (computed when needed, not kept)."""
    if "dist" in win:
        return win
    lat, lon = win["lat"], win["lon"]
    d, b = dist_bearing(lat[:, None], lon[:, None], lat[None, :], lon[None, :])
    return {**win, "dist": d, "bearing": b}


def matrices(win: dict, w: dict) -> dict:
    """Pairwise truth tables of the window: m[kind][i, j] for a's site i and b's site j."""
    dist, bear = win["dist"], win["bearing"]
    off = ~np.eye(len(dist), dtype=bool)
    m = {("direction", d): within(bear.T, d, w["cone_deg"]) & off for d in DIRS}
    m["higher"] = (win["dem"][:, None] - win["dem"][None, :]) > w["higher_margin_m"]
    m["near"] = dist <= w["near_km"]
    return m


def pair_table(kind: str, value, m: dict, win: dict, w: dict) -> np.ndarray:
    if kind == "direction":
        return m[("direction", value)]
    if kind in ("higher", "near"):
        return m[kind]
    if kind == "days":
        lo, hi = w["km_per_day"]
        return (win["dist"] >= value * lo) & (win["dist"] <= value * hi)
    if kind == "distance":
        f = w["distance_factor"]
        return (win["dist"] >= value / f) & (win["dist"] <= value * f)
    raise ValueError(kind)


def unary_table(kind: str, value, win: dict) -> np.ndarray:
    if kind == "isthmus":
        return win["neck"]
    if kind == "sea":
        return win["side"][value] if value else win["near"]
    raise ValueError(kind)


def best_fit(places: list, cons: list, win: dict, w: dict, rng: np.random.Generator) -> dict:
    """The assignment of places to window sites that satisfies most statements (coordinate
    ascent from random starts). Returns the share satisfied and the count by kind."""
    k, n = len(win["dem"]), len(places)
    if not cons or k == 0:
        return {"share": None}
    win = with_pairs(win)
    m = matrices(win, w)
    unary = [[] for _ in range(n)]
    pairs = [[] for _ in range(n)]  # (table oriented so rows = this place's site, other place)
    tables = []
    for kind, i, j, v in cons:
        if j < 0:
            t = unary_table(kind, v, win)
            unary[i].append(t)
            tables.append((kind, t, i, -1))
        else:
            t = pair_table(kind, v, m, win, w)
            pairs[i].append((t, j))
            pairs[j].append((t.T, i))
            tables.append((kind, t, i, j))
    base = [np.sum(u, axis=0) if u else np.zeros(k) for u in unary]

    def satisfied(a: np.ndarray) -> list[bool]:
        return [bool(t[a[i]]) if j < 0 else bool(t[a[i], a[j]]) for _kd, t, i, j in tables]

    best = None
    for _ in range(w["restarts"]):
        a = rng.integers(0, k, size=n)
        for _s in range(w["max_sweeps"]):
            changed = False
            for p in rng.permutation(n):
                g = base[p].astype(float).copy()
                for t, q in pairs[p]:
                    g += t[:, a[q]]
                top = np.flatnonzero(g == g.max())
                if g[a[p]] < g.max():
                    a[p] = rng.choice(top)
                    changed = True
            if not changed:
                break
        ok = satisfied(a)
        if best is None or sum(ok) > sum(best[1]):
            best = (a.copy(), ok)
    ok = best[1]
    by = defaultdict(lambda: [0, 0])
    for (kd, *_r), o in zip(tables, ok, strict=True):
        by[kd][0] += o
        by[kd][1] += 1
    return {
        "share": round(sum(ok) / len(ok), 4),
        "satisfied": sum(ok),
        "statements": len(ok),
        "by_kind": {kd: f"{s}/{t}" for kd, (s, t) in sorted(by.items())},
    }


def percentile(x: float, xs: list[float]) -> float | None:
    xs = [v for v in xs if v is not None]
    if x is None or not xs:
        return None
    below = sum(v < x for v in xs)
    ties = sum(v == x for v in xs)
    return round(100.0 * (below + 0.5 * ties) / len(xs), 1)


def decoy_windows(earth: Earth, radius: float, w: dict, rng: random.Random) -> list[dict]:
    """``decoys`` windows centred on random land settlements, uniform over one-degree cells."""
    cells: dict[tuple[int, int], list[int]] = defaultdict(list)
    step = max(1, len(earth.lat) // 400_000)
    for i in range(0, len(earth.lat), step):
        cells[(int(math.floor(earth.lat[i])), int(math.floor(earth.lon[i])))].append(i)
    keys = sorted(cells)
    got, skipped = [], 0
    while len(got) < w["decoys"] and skipped < 20 * w["decoys"]:
        i = rng.choice(cells[rng.choice(keys)])
        win = earth.window(earth.lat[i], earth.lon[i], radius)
        if win is None or len(win["dem"]) < w["min_sites"]:
            skipped += 1
            continue
        win["centre"] = (round(float(earth.lat[i]), 3), round(float(earth.lon[i]), 3))
        got.append(win)
    return got, skipped


def region_score(table: dict, target: dict, decoys: list, w: dict, kinds, seed: int) -> dict:
    """The target window's best fit and its percentile among decoys more than one radius away."""
    places, cons = compile_constraints(table["constraints"], kinds)
    rng = np.random.default_rng(seed)
    t = best_fit(places, cons, target["win"], w, rng)
    far = [
        d
        for d in decoys
        if dist_bearing(target["lat"], target["lon"], *d["centre"])[0] > target["radius"]
    ]
    shares = [best_fit(places, cons, d, w, rng)["share"] for d in far]
    pct = percentile(t["share"], shares)
    return {
        **t,
        "decoys": len(far),
        "decoy_median_share": round(float(np.median(shares)), 4) if shares else None,
        "decoy_p95_share": round(float(np.percentile(shares, 95)), 4) if shares else None,
        "decoys_at_or_above": sum(s >= t["share"] for s in shares) if shares else None,
        "percentile": pct,
        "at_bar": pct is not None and pct >= w["percentile_bar"],
    }


# --------------------------------------------------------------------------- known answer (a)


def openbible() -> dict[str, tuple[float, float]]:
    """Ancient place name -> (lat, lon) of its best-scored identification (OpenBible.info)."""
    got = {}
    for line in OPENBIBLE.read_text().splitlines():
        r = json.loads(line)
        best = None
        for ident in r.get("identifications", []):
            score = ident.get("score", {}).get("vote_total", 0)
            for res in ident.get("resolutions", []):
                if res.get("lonlat") and (best is None or score > best[0]):
                    lon, lat = map(float, res["lonlat"].split(","))
                    best = (score, lat, lon)
        if best:
            got.setdefault(r["friendly_id"], (best[1], best[2]))
    return got


def true_placement(table: dict, earth: Earth, win: dict, w: dict, seed: int) -> dict:
    """The Bible's statements scored with OpenBible coordinates, against random placements of
    the same places among the Palestine window's sites."""
    coords = openbible()
    keep = [
        c for c in table["constraints"] if c["a"] in coords and (c["b"] is None or c["b"] in coords)
    ]
    places, cons = compile_constraints(keep)
    if not cons:
        return {"stopped": "not attempted: no statement has both places in OpenBible"}
    lat = np.array([coords[p][0] for p in places])
    lon = np.array([coords[p][1] for p in places])
    true = {"lat": lat, "lon": lon, "dem": earth.snap_dem(lat, lon)}
    true.update(earth.coast_flags(lat, lon))
    true["dist"], true["bearing"] = dist_bearing(lat[:, None], lon[:, None], lat[None], lon[None])
    mt = matrices(true, w)
    ok = []
    for kind, i, j, v in cons:
        if j < 0:
            ok.append(bool(unary_table(kind, v, true)[i]))
        else:
            if kind == "higher" and (np.isnan(true["dem"][i]) or np.isnan(true["dem"][j])):
                continue  # no elevation within the snap distance: not scored
            ok.append(bool(pair_table(kind, v, mt, true, w)[i, j]))
    share = sum(ok) / len(ok)
    win = with_pairs(win)
    m = matrices(win, w)
    rng = np.random.default_rng(seed)
    k = len(win["dem"])
    rand = []
    for _ in range(w["random_assignments"]):
        a = rng.integers(0, k, size=len(places))
        r = [
            bool(unary_table(kd, v, win)[a[i]])
            if j < 0
            else bool(pair_table(kd, v, m, win, w)[a[i], a[j]])
            for kd, i, j, v in cons
        ]
        rand.append(sum(r) / len(r))
    pct = percentile(share, rand)
    return {
        "places_with_coordinates": len(places),
        "statements_scored": len(ok),
        "true_share": round(share, 4),
        "random_median_share": round(float(np.median(rand)), 4),
        "random_p95_share": round(float(np.percentile(rand, 95)), 4),
        "percentile": pct,
        "passed": pct is not None and pct >= w["extractor_bar"],
    }


# --------------------------------------------------------------------------- the run


def tables_for(specs: dict, w: dict) -> tuple[dict, dict]:
    tables, missing = {}, {}
    for name, spec in specs.items():
        units = text_units(spec)
        if units is None:
            missing[name] = "not attempted: the text could not be read"
            continue
        tables[name] = extract(units, w)
    return tables, missing


def public_table(table: dict) -> list[dict]:
    """Constraints with names, values and references only (no text)."""
    return [
        {"kind": c["kind"], "a": c["a"], "b": c["b"], "value": c["value"], "refs": c["refs"]}
        for c in table["constraints"]
    ]


def run(cfg: dict, check_only: bool = False) -> dict:
    w = cfg["lab"]["geography"]
    res: dict = {"settings": w, "not_attempted": {}}
    if not (CACHE / "geonames.npz").exists():
        res["stopped"] = "not attempted: run `python -m lab.geography cache` first"
        return res
    earth = Earth(w)
    res["geonames"] = {k: v for k, v in earth.meta.items() if k != "anchors"}
    anchors = {}
    for name, spec in w["anchors"].items():
        a = earth.anchor(spec)
        if a is None:
            res["not_attempted"][f"anchor_{name}"] = "not attempted: no GeoNames entry"
            continue
        win = earth.window(a["lat"], a["lon"], spec["radius"])
        anchors[name] = {**a, "radius": spec["radius"], "win": win}
    res["anchors"] = {
        n: {k: v for k, v in a.items() if k != "win"} | {"sites": len(a["win"]["dem"])}
        for n, a in anchors.items()
    }

    tables, missing = tables_for(w["texts"], w)
    res["not_attempted"].update(missing)
    res["known_texts"] = {
        n: {"summary": summary(t), "consistency": cycles(t["constraints"]),
            "constraints": public_table(t)}
        for n, t in tables.items()
    }  # fmt: skip

    # Known answer (a): the extractor, with the Bible's true coordinates.
    pal = anchors.get("palestine")
    kjv = tables.get("kjv_ot_narrative")
    if pal is None or kjv is None:
        res["stopped"] = "known-answer check (a) not attempted: Palestine window or text missing"
        return res
    ka = true_placement(kjv, earth, pal["win"], w, w["seed"])
    jos = {
        n: true_placement(tables[n], earth, pal["win"], w, w["seed"])
        for n in ("josephus_wars", "josephus_antiquities")
        if n in tables
    }
    res["known_answer_extractor"] = {"kjv_ot_narrative": ka, "reported_not_counted": jos}

    # Decoy windows.
    rng = random.Random(w["seed"])
    radii = w["radii_km"] if not check_only else [w["radii_km"][0]]
    decoys = {}
    res["decoy_windows"] = {}
    for r in radii:
        decoys[r], skipped = decoy_windows(earth, r, w, rng)
        res["decoy_windows"][str(r)] = {
            "windows": len(decoys[r]),
            "skipped_too_few_sites": skipped,
            "median_sites": int(np.median([len(d["dem"]) for d in decoys[r]])),
            "share_with_a_coastal_site": round(
                float(np.mean([d["near"].any() for d in decoys[r]])), 3
            ),
        }

    # Known answer (b): each known text in its own region.
    readings = {"every_kind": None, "without_distance": None}
    kinds_all = {c["kind"] for t in tables.values() for c in t["constraints"]}
    readings["without_distance"] = kinds_all - {"distance"}
    kb: dict = {}
    for rname, kinds in readings.items():
        block, counted = {}, []
        for n, spec in w["texts"].items():
            t, anc = tables.get(n), spec.get("anchor")
            if t is None or anc is None or anc not in anchors:
                continue
            nk = len(compile_constraints(t["constraints"], kinds)[1])
            target = anchors[anc]
            sc = region_score(t, target, decoys[target["radius"]], w, kinds, w["seed"])
            sc["counted"] = nk >= w["min_constraints"]
            block[n] = sc
            if sc["counted"]:
                counted.append(sc["at_bar"])
        block["_check"] = {
            "texts_counted": len(counted),
            "at_bar": sum(counted),
            "passed": len(counted) >= w["min_known_texts"] and all(counted),
        }
        kb[rname] = block
    res["known_answer_region"] = kb
    passed_a = ka.get("passed", False)
    passed_b = kb["every_kind"]["_check"]["passed"]
    res["known_answer_passed"] = {"extractor": passed_a, "region_every_kind": passed_b,
                                  "region_without_distance": kb["without_distance"]["_check"][
                                      "passed"]}  # fmt: skip
    if check_only:
        return res
    if not (passed_a and passed_b):
        res["stopped"] = (
            "the known-answer check missed its bar; the Book of Mormon's statements were "
            "extracted and checked for internal consistency only, not scored against any region"
        )

    # The Book of Mormon.
    books, missing = tables_for(w["book"], w)
    res["not_attempted"].update(missing)
    res["book"] = {}
    for n, t in books.items():
        block = {"summary": summary(t), "consistency": cycles(t["constraints"]),
                 "constraints": public_table(t), "settings": {}}  # fmt: skip
        res["book"][n] = block
        if "stopped" in res:
            block["settings"] = "not scored: the known-answer region check missed its bar"
            continue
        for s in w["settings"]:
            if s not in anchors:
                continue
            target = anchors[s]
            sc = region_score(t, target, decoys[target["radius"]], w, None, w["seed"])
            if sc["at_bar"]:
                sc["verdict"] = (
                    "fits better than chance"
                    if res["known_answer_passed"]["region_without_distance"]
                    else "cannot tell"
                )
            else:
                sc["verdict"] = "no"
            block["settings"][s] = sc
        places, cons = compile_constraints(t["constraints"])
        rng2 = np.random.default_rng(w["seed"])
        top = []
        for d in decoys[w["radii_km"][0]]:
            top.append((best_fit(places, cons, d, w, rng2)["share"], d["centre"]))
        top.sort(key=lambda x: -(x[0] or 0))
        block["best_decoy_windows"] = [{"share": s, "centre": c} for s, c in top[:10]]
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["cache", "extract", "check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    w = cfg["lab"]["geography"]
    if a.cmd == "cache":
        build_cache(cfg)
        return 0
    if a.cmd == "extract":
        tables, missing = tables_for(w["texts"], w)
        print(json.dumps({n: summary(t) for n, t in tables.items()} | missing, indent=1))
        return 0
    res = run(cfg, check_only=a.cmd == "check")
    brief = {k: v for k, v in res.items() if k not in ("settings", "known_texts", "book")}
    if a.cmd == "check":
        print(json.dumps(brief, indent=1, default=str)[:8000])
        return 0
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps(brief, indent=1, default=str)[:8000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
