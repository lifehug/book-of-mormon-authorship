"""BOM-110: the Book of Mormon's place names against chance (Holley's Great Lakes map).

Holley's map pairs about 29 place names around the Great Lakes with Book of Mormon names. This
asks what chance gives. The book's non-biblical place names (the list of ``lab.names``, BOM-108,
narrowed to places) are reduced to a sound key and matched by one rule, fixed first, against
(1) modern names with coordinates (GeoNames): the entries within a radius of Palmyra against the
same number of entries around every other centre; (2) names as printed before 1830 (Worcester's
1823 world gazetteer and Morse's of 1821 and 1823, grouped by the state or country each entry
names): New York against every other group at equal sample size. Control name sets (Spalding's,
Swift's, Ossian's and Spenser's coinages, names drawn from a character model of King James
names, King James place names) are scored the same way. Only regions and groups in English
spelling count toward the verdict: letter matching mostly detects spelling convention (BOM-108).
Then Holley's published pairs one by one. The test card, written first, is
``data/private/lab/owner/2026-11-20-place-names/card.md``; settings are ``lab.placenames`` in the
config. The output holds names, counts and scores, no passages.

Holley's pairs are taken from FAIR's page "Book of Mormon place names from North America"
(https://www.fairlatterdaysaints.org/answers/Book_of_Mormon_place_names_from_North_America),
read on 2026-11-20 through an AI summary of the page; not checked by a person.

Usage::

    python -m lab.placenames cache    # read GeoNames once -> data/corpus/lab/placenames/ (30 s)
    python -m lab.placenames check    # known-answer checks only (3 min)
    python -m lab.placenames run      # -> data/lab/setting/placenames/result.json (4 min)
"""

from __future__ import annotations

import argparse
import copy
import csv
import io
import json
import math
import random
import re
import subprocess
import zipfile
from collections import Counter

import numpy as np
import pyarrow.compute as pc
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein

from lab import door, names, registry
from lab.paths import FAST, REGISTRY, out
from metadata import config

OUT = REGISTRY / "setting" / "placenames"
CACHE = FAST / "placenames"
PLACES = names.SRC / "places"
GEONAMES = PLACES / "geonames_allCountries.zip"
EARTH_KM = 6371.0
BIBLE_LANDS = {"IL", "PS", "JO", "LB", "SY", "EG"}
PLACE_WORD = (
    r"\b(?:land|lands|city|cities|village|hill|mount|valley|plains|wilderness|river|waters|sea|"
    r"place|borders)\s+(?:which\s+(?:was|they|is)\s+called\s+|called\s+|of\s+)?(?:the\s+)?"
    r"((?:[A-Z][a-z]+)(?:-[A-Z][a-z]+)*)"
)
# (modern name, Book of Mormon name, FAIR's reading of whether the modern name predates 1830).
HOLLEY = [
    ("Tecumseh", "Teancum", "no (1912)"),
    ("Rama", "Ramah", "yes (1820)"),
    ("Morin", "Moron", "no (1852)"),
    ("Sainte-Agathe-des-Monts", "Ogath", "not stated"),
    ("Moraviantown", "Morianton", "yes (about 1782)"),
    ("Angola", "Angola", "no (about 1854)"),
    ("Oneida", "Onidah", "yes"),
    ("Kiskiminetas", "Kishkumen", "township no (1832); river name yes (1776)"),
    ("Jacobsburg", "Jacobugath", "yes (laid out 1815)"),
    ("Jerusalem", "Jerusalem", "no (Ohio); New York town 1789"),
    ("Alma", "Alma", "no"),
    ("Lehigh", "Lehi", "yes"),
    ("Ripple Lake", "Ripliancum", "not established"),
    ("Shiloh", "Shilom", "no"),
    ("Antrim", "Antum", "yes (1741)"),
    ("Antioch", "Ani-Anti", "no (1837, 1880)"),
    ("Boaz", "Boaz", "no (1878)"),
    ("Connor", "Comnor", "no (1865)"),
    ("Saint-Ephrem", "Ephraim", "no (1866)"),
    ("Hellam", "Helam", "yes (1739)"),
    ("Jordan", "Jordan", "yes (before 1819)"),
    ("Mantua", "Manti", "no (1898)"),
    ("Monroe", "Moroni", "named 1808; absent from 1822 and 1831 maps"),
    ("Minoa", "Minon", "no (1895)"),
    ("Oneida Castle", "Onidah", "yes"),
    ("Noah Lakes", "Noah", "no"),
    ("Omer", "Omner", "none found"),
    ("Sodom", "Sidom", "not applicable"),
    ("Midian", "Midian", "none found"),
]


# --------------------------------------------------------------------------- the matching rule


def key(name: str) -> str:
    """Sound key of one word. C, S, T stand for ch, sh, th (one sound, one symbol)."""
    s = names.norm(name)
    s = s.replace("ph", "f").replace("ck", "k")
    s = s.replace("ch", "C").replace("sh", "S").replace("th", "T")
    s = re.sub(r"c(?=[eiy])", "s", s).replace("c", "k")
    s = s.replace("q", "k").replace("x", "ks").replace("z", "s").replace("y", "i")
    s = s[:1] + s[1:].replace("h", "")
    s = re.sub(r"(.)\1+", r"\1", s)
    if len(s) > 3 and s.endswith("e"):
        s = s[:-1]
    return s


def entry_keys(name: str, generic: set[str], min_len: int) -> list[str]:
    """One key for each word of a place name that is long enough and not a generic word."""
    got = []
    for w in re.findall(r"[^\W\d_]+", name):
        w = names.norm(w)
        if len(w) >= min_len and w not in generic:
            got.append(key(w))
    return [k for k in got if k]


def close(a: str, b: str, t: float) -> bool:
    return Levenshtein.distance(a, b) <= t * max(len(a), len(b)) + 1e-9


def match_ids(queries: list[str], keys: list[str], t: float, chunk: int = 150_000) -> list:
    """For each query key, the indices of ``keys`` within the threshold (arrays of int)."""
    by_len: dict[int, list[int]] = {}
    for i, k in enumerate(keys):
        by_len.setdefault(len(k), []).append(i)
    q_by_len: dict[int, list[int]] = {}
    for i, q in enumerate(queries):
        q_by_len.setdefault(len(q), []).append(i)
    res = [[] for _ in queries]
    for ql, qidx in q_by_len.items():
        qs = [queries[i] for i in qidx]
        for kl, kidx in by_len.items():
            cut = int(t * max(ql, kl) + 1e-9)
            if abs(ql - kl) > cut:
                continue
            for s in range(0, len(kidx), chunk):
                part = kidx[s : s + chunk]
                d = process.cdist(
                    qs,
                    [keys[i] for i in part],
                    scorer=Levenshtein.distance,
                    score_cutoff=cut,
                    dtype=np.uint8,
                    workers=-1,
                )
                qi, ki = np.nonzero(d <= cut)
                arr = np.asarray(part, dtype=np.int64)[ki]
                for j in np.unique(qi):
                    res[qidx[j]].append(arr[qi == j])
    return [np.concatenate(r) if r else np.zeros(0, dtype=np.int64) for r in res]


# --------------------------------------------------------------------------- GeoNames


def build_cache(cfg: dict) -> None:
    """Read GeoNames once: coordinates, country and word keys of every entry of the classes."""
    w = cfg["lab"]["placenames"]
    classes, generic = set(w["feature_classes"]), set(w["generic_words"])
    english = set(w["english_countries"])
    lat, lon, cc, ent, kid = [], [], [], [], []
    key_id: dict[str, int] = {}
    word_key: dict[str, int | None] = {}
    countries: dict[str, int] = {}
    alt_pairs = []
    member = "allCountries.txt"  # read, not written
    with zipfile.ZipFile(GEONAMES) as z, z.open(member) as fh:
        for line in io.TextIOWrapper(fh, encoding="utf-8"):
            f = line.split("\t")
            if f[6] not in classes:
                continue
            ids = []
            for word in re.findall(r"[A-Za-z]+", f[2]):
                word = word.lower()
                if word not in word_key:
                    k = key(word) if len(word) >= w["min_word_len"] and word not in generic else ""
                    word_key[word] = key_id.setdefault(k, len(key_id)) if k else None
                if word_key[word] is not None:
                    ids.append(word_key[word])
            if not ids:
                continue
            n = len(lat)
            lat.append(float(f[4]))
            lon.append(float(f[5]))
            cc.append(countries.setdefault(f[8], len(countries)))
            ent.extend([n] * len(ids))
            kid.extend(ids)
            # Known-answer pairs without a bar: a one-word name and its one-word other names.
            if f[8] in english and f[6] == "P" and f[3] and f[2].isalpha() and n % 7 == 0:
                for alt in f[3].split(","):
                    if alt.isascii() and alt.isalpha() and names.norm(alt) != names.norm(f[2]):
                        alt_pairs.append([f[2], alt])
    arrays = out(CACHE / "geonames.npz")
    np.savez(  # the path comes from out( above
        arrays,
        lat=np.asarray(lat, dtype=np.float32),
        lon=np.asarray(lon, dtype=np.float32),
        cc=np.asarray(cc, dtype=np.int16),
        ent=np.asarray(ent, dtype=np.int32),
        kid=np.asarray(kid, dtype=np.int32),
    )
    meta = {
        "keys": list(key_id),
        "countries": list(countries),
        "alt_pairs": alt_pairs[:50000],
        "classes": sorted(classes),
        "generic": sorted(generic),
        "min_word_len": w["min_word_len"],
    }
    out(CACHE / "geonames.json").write_text(json.dumps(meta))


class Geo:
    def __init__(self, cfg: dict):
        w = cfg["lab"]["placenames"]
        meta_path = CACHE / "geonames.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            stale = (
                meta["classes"] != sorted(w["feature_classes"])
                or meta["generic"] != sorted(w["generic_words"])
                or meta["min_word_len"] != w["min_word_len"]
            )
        if not meta_path.exists() or stale:
            build_cache(cfg)
            meta = json.loads(meta_path.read_text())
        a = np.load(CACHE / "geonames.npz")
        self.keys, self.countries = meta["keys"], meta["countries"]
        self.alt_pairs = meta["alt_pairs"]
        self.lat, self.lon, self.cc = a["lat"], a["lon"], a["cc"]
        self.ent, self.kid = a["ent"], a["kid"]
        la, lo = np.radians(self.lat), np.radians(self.lon)
        self.xyz = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=1)
        eng = {self.countries.index(c) for c in w["english_countries"] if c in self.countries}
        self.english = np.isin(self.cc, list(eng))

    def dots(self, lat: float, lon: float) -> np.ndarray:
        return self.xyz @ unit(lat, lon)

    def key_mask(self, entries: np.ndarray) -> np.ndarray:
        """Boolean over the keys: which occur in the given entries (a boolean over entries)."""
        m = np.zeros(len(self.keys), dtype=bool)
        m[self.kid[entries[self.ent]]] = True
        return m


def unit(lat: float, lon: float) -> np.ndarray:
    la, lo = math.radians(lat), math.radians(lon)
    return np.array(
        [math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)], dtype=np.float32
    )


def km_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    return EARTH_KM * math.acos(max(-1.0, min(1.0, float(unit(*a) @ unit(*b)))))


def centres(geo: Geo, w: dict) -> list[dict]:
    """Grid points on land: a fine grid where the nearest entry is in an English-spelling
    country, a coarse one elsewhere, and the named centres."""
    from scipy.spatial import cKDTree

    tree = cKDTree(geo.xyz[::5])  # every fifth entry is enough to tell land from sea
    step_la, step_lo = w["grid_deg"]
    pts = [
        (la, lo)
        for la in np.arange(-56.0, 72.01, step_la)
        for lo in np.arange(-180.0, 179.99, step_lo)
    ]
    d, i = tree.query(np.stack([unit(*p) for p in pts]))
    near = 2 * np.arcsin(np.clip(d / 2, 0, 1)) * EARTH_KM <= w["centre_max_km"]
    eng = geo.english[::5][i]
    got = []
    coarse = w["world_grid_deg"]
    for p, ok, e in zip(pts, near, eng, strict=True):
        if not ok:
            continue
        on_coarse = p[0] % coarse == 0 and p[1] % coarse == 0
        if e or on_coarse:
            got.append({"name": f"{p[0]:+.1f},{p[1]:+.1f}", "lat": float(p[0]), "lon": float(p[1])})
    for name, (la, lo) in w["named_centres"].items():
        got.append({"name": name, "lat": la, "lon": lo})
    return got


def region_group(code: str, english: set[str]) -> str:
    if code == "US":
        return "united_states"
    if code in english:
        return "other_english"
    if code in ("MX", "GT"):
        return "mexico_guatemala"
    if code in BIBLE_LANDS:
        return "bible_lands"
    return "rest"


def regions(geo: Geo, w: dict, radius: float, flat: np.ndarray, owner: np.ndarray, nq: int):
    """The Palmyra region and every other region of the same number of entries.

    Returns (local, others): each a dict with the region's facts and ``hit``, a boolean per query
    key (does any key of the region match it). ``flat``/``owner`` are the matching key ids of
    all queries laid end to end and the query each belongs to."""
    home = tuple(w["palmyra"])
    cos_r = math.cos(radius / EARTH_KM)
    cos_max = math.cos(min(math.pi, w["max_region_factor"] * radius / EARTH_KM))
    english = set(w["english_countries"])

    def facts(entries: np.ndarray, reach_km: float, c: dict) -> dict:
        codes = np.bincount(geo.cc[entries], minlength=len(geo.countries))
        mask = geo.key_mask(entries)
        hit = np.bincount(owner[mask[flat]], minlength=nq) > 0
        top = geo.countries[int(codes.argmax())]
        return {
            **c,
            "km_from_palmyra": round(km_between(home, (c["lat"], c["lon"]))),
            "reach_km": round(reach_km),
            "country": top,
            "group": region_group(top, english),
            "english_share": round(float(geo.english[entries].mean()), 3),
            "distinct_keys": int(mask.sum()),
            "hit": hit,
        }

    inside = geo.dots(*home) >= cos_r
    n = int(inside.sum())
    local = facts(inside, radius, {"name": "palmyra", "lat": home[0], "lon": home[1]})
    local["entries"] = n
    others, dropped = [], 0
    for c in centres(geo, w):
        d = geo.dots(c["lat"], c["lon"])
        if int((d >= cos_max).sum()) < n:
            dropped += 1
            continue
        cut = np.partition(d, len(d) - n)[len(d) - n]
        entries = d >= cut
        reach = EARTH_KM * math.acos(max(-1.0, min(1.0, float(cut))))
        others.append(facts(entries, reach, c))
    return local, others, dropped


# --------------------------------------------------------------------------- period gazetteers

HEAD = re.compile(
    r"^([A-Z][A-Za-z'’]+(?:[ -][A-Z][a-z'’]+){0,2}),? (?:\([^)]{1,40}\),? )?"
    r"(?:or [A-Z][a-z]+,? )?"
    r"(?:p-t|t|v|r|co|mt|isl|city|s-p|p-v|lake|cape|district|prov|settlement|bay|fort)\b\.?"
)
VARIANT = re.compile(r"^([A-Z][a-z]+),? or ([A-Z][a-z]+),")
HEAD_PLAIN = re.compile(r"^([A-Z][A-Za-z'’]+(?:[ -][A-Z][A-Za-z'’]+){0,2}),\s")


def paragraphs(text: str) -> list[str]:
    text = re.sub(r"-\s*\n\s*", "", text)  # rejoin words broken across lines
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]


def world_entries(text: str, groups: dict, window: int) -> list[tuple[str, str | None]]:
    """(headword, group) for each entry of a world gazetteer; the group is the first of the
    config's marks printed in the ``window`` characters after the headword and its kind."""
    got = []
    for p in paragraphs(text):
        m = HEAD.match(p)
        if not m:
            continue
        rest = p[m.end() : m.end() + window]
        best = (len(rest) + 1, None)
        for g, spec in groups.items():
            for mark in spec["marks"]:
                i = rest.find(mark)
                while i >= 0:
                    before = rest[i - 1] if i else " "
                    after = rest[i + len(mark) : i + len(mark) + 1]
                    if not before.isalpha() and not after.isalpha():
                        best = min(best, (i, g))
                        break
                    i = rest.find(mark, i + 1)
        got.append((m.group(1), best[1]))
    return got


def plain_heads(text: str) -> list[str]:
    """Headwords of a one-region gazetteer: a paragraph opening with a capitalised name and a
    comma."""
    return [m.group(1) for p in paragraphs(text) if (m := HEAD_PLAIN.match(p))]


def library_text(work_id: str) -> str | None:
    t = registry.load()
    rows = t.filter(pc.equal(t["work_id"], work_id)).to_pylist()
    cat = door.catalog({work_id}).get(work_id)
    if not rows or not cat or not rows[0]["has_text"] or rows[0]["sealed"]:
        return None
    try:
        return door.text_of({**cat, **rows[0]})
    except OSError:
        return None  # unreadable: not attempted


def period_sources(cfg: dict) -> tuple[dict, dict, dict]:
    """(world gazetteers' entries, New York headwords by source, what was not attempted)."""
    w = cfg["lab"]["placenames"]
    world, ny, missing = {}, {}, {}
    for name, items in w["period_world"].items():
        texts = []
        for item in items:
            f = PLACES / item / "text.txt"
            if not f.exists():
                missing[name] = f"not attempted: {item} not on disk"
                break
            texts.append(f.read_text(errors="replace"))
        else:
            world[name] = world_entries("\n\n".join(texts), w["period_groups"], w["period_window"])
            ny[name] = [h for h, g in world[name] if g == w["period_local_group"]]
    for name, work_id in w["period"].items():
        text = library_text(work_id)
        if text is None:
            missing[name] = f"not attempted: {work_id} could not be read"
        elif name.startswith("spafford"):
            ny[name] = plain_heads(text)
        else:  # Morse 1798: entries whose opening names New York
            ny[name] = [
                m.group(1)
                for p in paragraphs(text)
                if (m := HEAD_PLAIN.match(p))
                and re.search(r"New[- ]York", p[: 2 * w["period_window"]])
            ]
    return world, ny, missing


# --------------------------------------------------------------------------- name sets


def bom_places(cfg: dict, english: set[str], kjv: set[str]) -> dict:
    """The coined names of ``lab.names`` that Wikipedia lists as places and that follow a place
    word in the 1830 text; with and without the long Bible-quoting chapters."""
    from lab.wherefore import LABELS, QUOTED

    bom = names.bom_names(cfg, english, kjv)
    listed = [n for n in bom["coined"] if "place" in bom["groups"][n]]
    labels = {r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines())}
    after, after_unquoted = set(), set()
    for r in map(json.loads, names.EDITION.read_text().splitlines()):
        if r["kind"] != "body":
            continue
        lab = labels.get(r["seq"])
        quoted = lab is not None and (r["book"], lab["chapter_1830"]) in QUOTED
        for m in re.finditer(PLACE_WORD, r["text"]):
            parts = {names.norm(x) for x in m.group(1).split("-")}
            after |= parts
            if not quoted:
                after_unquoted |= parts
    return {
        "places": sorted(n for n in listed if n in after),
        "places_without_quoted_chapters": sorted(n for n in listed if n in after_unquoted),
        "listed_but_never_after_a_place_word": sorted(n for n in listed if n not in after),
        "after_a_place_word_but_not_listed_as_place": sorted(
            n for n in bom["coined"] if n in after and n not in listed
        ),
        "biblical_names_set_aside": len(bom["biblical"]),
    }


def ngram_names(train: list[str], w: dict, rng: random.Random) -> list[str]:
    """Distinct new names sampled from a character model of the training names."""
    order, k = w["ngram_order"], w["ngram_smoothing"]
    counts: dict[str, Counter] = {}
    for n in train:
        s = "^" * (order - 1) + n + "$"
        for i in range(order - 1, len(s)):
            counts.setdefault(s[i - order + 1 : i], Counter())[s[i]] += 1
    alphabet = "abcdefghijklmnopqrstuvwxyz$"
    seen, got, tries = set(train), [], 0
    while len(got) < w["ngram_pool"] and tries < w["ngram_pool"] * 200:
        tries += 1
        s = "^" * (order - 1)
        while not s.endswith("$") and len(s) < 20:
            c = counts.get(s[-(order - 1) :], Counter())
            s += rng.choices(alphabet, [c[a] + k for a in alphabet])[0]
        name = s.strip("^$")
        if s.endswith("$") and len(name) >= w["min_word_len"] and name not in seen:
            seen.add(name)
            got.append(name)
    return got


def kjv_places(english: set[str]) -> list[str]:
    got = set()
    with (names.N / "theographic/CSV/Places.csv").open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            n = (row.get("kjvName") or "").strip()
            if n.isalpha() and names.norm(n) not in english:
                got.add(names.norm(n))
    return sorted(got)


def kjv_variants() -> list[tuple[str, str]]:
    """Two spellings of one Bible place: King James against a modern translation."""
    got = set()
    with (names.N / "theographic/CSV/Places.csv").open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            a, b = (row.get("kjvName") or "").strip(), (row.get("esvName") or "").strip()
            if a.isalpha() and b.isalpha() and names.norm(a) != names.norm(b):
                got.add((a, b))
    return sorted(got)


def one_edit(k: str, rng: random.Random) -> str:
    """A key changed by one random edit (a letter replaced, dropped or added)."""
    letters = "abdefgiklmnoprstuvw"
    i, kind = rng.randrange(len(k)), rng.choice("rda")
    if kind == "r":
        return k[:i] + rng.choice([c for c in letters if c != k[i]]) + k[i + 1 :]
    if kind == "d":
        return k[:i] + k[i + 1 :]
    return k[:i] + rng.choice(letters) + k[i:]


def length_matched(pool: list[str], lengths: list[int], rng: random.Random) -> list[str]:
    """One key from the pool for each wanted length (the nearest length when none is equal)."""
    by: dict[int, list[str]] = {}
    for k in pool:
        by.setdefault(len(k), []).append(k)
    got, used = [], set()
    for n in lengths:
        for d in sorted(by, key=lambda x: abs(x - n)):
            free = [k for k in by[d] if k not in used]
            if free:
                pick = rng.choice(free)
                used.add(pick)
                got.append(pick)
                break
    return got


# --------------------------------------------------------------------------- scoring


def percentile(x: float, xs: list[float]) -> float | None:
    """Mid-rank percentile of ``x`` among ``xs``."""
    if not xs:
        return None
    return round(100 * (sum(v < x for v in xs) + 0.5 * sum(v == x for v in xs)) / len(xs), 1)


def printed_variants() -> list[tuple[str, str]]:
    """Two spellings of one place as Worcester (1823) prints them: "Delfino, or Delvino, ..."."""
    got = []
    for item in ("geographicaldict01worc", "geographicaldict02worc"):
        f = PLACES / item / "text.txt"
        if not f.exists():
            continue
        for p in paragraphs(f.read_text(errors="replace")):
            m = VARIANT.match(p)
            if m and names.norm(m.group(1)) != names.norm(m.group(2)):
                got.append((m.group(1), m.group(2)))
    return got


def _norms(pairs: list[tuple[str, str]]) -> np.ndarray:
    ks = [(key(x), key(y)) for x, y in pairs]
    return np.array([Levenshtein.distance(x, y) / max(len(x), len(y)) for x, y in ks if x and y])


def threshold(geo: Geo, w: dict, rng: random.Random) -> dict:
    """Known answer (a): how often each threshold matches random pairs of keys and printed
    variant spellings of one place. Two thresholds come out: ``strict``, the loosest whose
    random-pair rate is within the limit, and ``loose``, the tightest that finds the bar's share
    of printed variants. The card's first form asked one threshold to do both; none does."""
    occ = geo.kid[geo.english[geo.ent]]
    a = rng.choices(range(len(occ)), k=w["random_pairs"])
    b = rng.choices(range(len(occ)), k=w["random_pairs"])
    pairs = [(geo.keys[occ[i]], geo.keys[occ[j]]) for i, j in zip(a, b, strict=True)]
    pairs = [(x, y) for x, y in pairs if x != y]
    norm = np.array([Levenshtein.distance(x, y) / max(len(x), len(y)) for x, y in pairs])
    sets = {
        "printed_variant_recall": _norms(printed_variants()),
        "bible_variant_recall": _norms(kjv_variants()),
        "geonames_alternate_recall": _norms(geo.alt_pairs),
    }
    grid = []
    for t in w["thresholds"]:
        row = {"threshold": t, "random_pair_rate": float((norm <= t + 1e-9).mean())}
        for name, d in sets.items():
            row[name] = round(float((d <= t + 1e-9).mean()), 4) if len(d) else None
        grid.append(row)
    ok = [g["threshold"] for g in grid if g["random_pair_rate"] <= w["max_false_rate"]]
    found = [g["threshold"] for g in grid if (g["printed_variant_recall"] or 0) >= w["recall_bar"]]
    first_form = bool(ok) and bool(found) and max(ok) >= min(found)
    thresholds = {}
    if ok:
        thresholds["strict"] = max(ok)
    if found and (not ok or min(found) != max(ok)):
        thresholds["loose"] = min(found)
    return {
        "grid": grid,
        "random_pairs": len(pairs),
        "pairs": {k.replace("_recall", "_pairs"): len(v) for k, v in sets.items()},
        "one_threshold_meets_both_bars": first_form,
        "thresholds": thresholds,
    }


def share(hit: np.ndarray, idx: list[int]) -> float:
    return float(hit[idx].mean()) if idx else float("nan")


def summarise(local: dict, others: list[dict], idx: list[int], w: dict, radius: float) -> dict:
    """Where the local share of one name set falls among the regions."""
    far = [r for r in others if r["km_from_palmyra"] > w["far_factor"] * radius]
    eng = [r for r in far if r["english_share"] >= w["english_share"]]
    loc = share(local["hit"], idx)
    eng_shares = [share(r["hit"], idx) for r in eng]
    med = float(np.median(eng_shares)) if eng_shares else float("nan")
    by_group: dict[str, list[float]] = {}
    for r in far:
        g = (
            r["group"]
            if r["english_share"] >= w["english_share"]
            or r["group"]
            not in (
                "united_states",
                "other_english",
            )
            else "mixed"
        )
        by_group.setdefault(g, []).append(share(r["hit"], idx))
    return {
        "names": len(idx),
        "local_share": round(loc, 4),
        "local_count": int(local["hit"][idx].sum()),
        "regions_compared": len(eng),
        "median_region_share": round(med, 4),
        "percentile_among_far_english_regions": percentile(loc, eng_shares),
        "regions_at_or_above_local": sum(v >= loc for v in eng_shares),
        "excess": round(loc - med, 4),
        "median_share_by_group": {
            g: [len(v), round(float(np.median(v)), 4)] for g, v in sorted(by_group.items())
        },
    }


def period_scores(world: dict, sets: dict[str, list[str]], t: float, w: dict, rng) -> dict:
    """Each name set against equal-sized draws of each group's entries, per world gazetteer."""
    generic = set(w["generic_words"])
    res = {}
    queries = sorted({k for ks in sets.values() for k in ks})
    for gaz, entries in world.items():
        ekeys = [entry_keys(h, generic, w["min_word_len"]) for h, _g in entries]
        uniq = sorted({k for ks in ekeys for k in ks})
        pos = {k: i for i, k in enumerate(uniq)}
        m = match_ids(queries, uniq, t)
        # matched[q] = the entry indices whose keys match query q
        by_key: dict[int, list[int]] = {}
        for e, ks in enumerate(ekeys):
            for k in ks:
                by_key.setdefault(pos[k], []).append(e)
        qhit = {
            q: np.unique([e for i in ids for e in by_key.get(int(i), [])]).astype(np.int64)
            for q, ids in zip(queries, m, strict=True)
        }
        groups: dict[str, list[int]] = {}
        for e, (_h, g) in enumerate(entries):
            if g is not None and ekeys[e]:
                groups.setdefault(g, []).append(e)
        table, sizes = {}, {g: len(v) for g, v in groups.items()}
        for g, members in groups.items():
            if len(members) < w["period_sample"]:
                continue
            acc = {s: [] for s in sets}
            for _ in range(w["period_draws"]):
                chosen = np.zeros(len(entries), dtype=bool)
                chosen[rng.sample(members, w["period_sample"])] = True
                for s, ks in sets.items():
                    acc[s].append(float(np.mean([chosen[qhit[k]].any() for k in ks])) if ks else 0)
            table[g] = {s: round(float(np.mean(v)), 4) for s, v in acc.items()}
        res[gaz] = {"entries": len(entries), "group_sizes": sizes, "share_by_group": table}
    return res


def period_rank(table: dict, s: str, w: dict) -> dict | None:
    """The local group's place among the English-spelling groups for one name set."""
    local = w["period_local_group"]
    if local not in table:
        return None
    eng = [g for g in table if g != local and w["period_groups"][g]["english"]]
    other = [g for g in table if g != local and not w["period_groups"][g]["english"]]
    loc = table[local][s]
    return {
        "local_share": loc,
        "english_groups": {g: table[g][s] for g in eng},
        "other_spelling_groups": {g: table[g][s] for g in other},
        "english_groups_at_or_above_local": sum(table[g][s] >= loc for g in eng),
        "excess": round(loc - float(np.median([table[g][s] for g in eng])), 4) if eng else None,
        "first_among_english_groups": all(table[g][s] < loc for g in eng),
    }


def run(cfg: dict, check_only: bool = False) -> dict:
    w = cfg["lab"]["placenames"]
    rng = random.Random(w["seed"])
    res: dict = {"settings": w, "not_attempted": {}}
    if not GEONAMES.exists():
        res["stopped"] = "not attempted: GeoNames is not on disk"
        return res
    geo = Geo(cfg)
    res["geonames"] = {"entries": len(geo.lat), "distinct_keys": len(geo.keys)}

    # Known answer (a): the threshold and what it finds.
    ka = threshold(geo, w, rng)
    res["known_answer"] = {"variant_spellings": ka}
    if not ka["thresholds"]:
        res["stopped"] = "known-answer check (a) gave no threshold; nothing was scored"
        return res

    # Name sets other than the Book of Mormon's.
    ncfg = copy.deepcopy(cfg)
    ncfg["lab"]["names"]["invented_min_count"].update(w["invented_min_count"])
    ref, missing, english = names.reference_sets(ncfg)
    res["not_attempted"].update(missing)
    kjv = set(ref["kjv"])
    real = kjv | set(ref.get("classical", [])) | set(ref.get("census_1790", []))
    world, ny, missing = period_sources(cfg)
    res["not_attempted"].update(missing)
    generic = set(w["generic_words"])
    ny_keys = {
        src: sorted({k for h in heads for k in entry_keys(h, generic, w["min_word_len"])})
        for src, heads in ny.items()
    }
    res["period_new_york_keys"] = {src: len(v) for src, v in ny_keys.items()}

    # Known answer (b): a planted local set (Spafford headwords in both editions, one edit each).
    both = set(ny_keys.get("spafford_1813", [])) & set(ny_keys.get("spafford_1824", []))
    one_word = {key(h) for h in ny.get("spafford_1824", []) if h.isalpha()}
    pool = sorted(k for k in both & one_word if len(k) >= w["planted_min_len"] and k not in english)
    planted = []
    if len(pool) >= w["planted_size"]:
        for _ in range(w["planted_draws"]):
            planted.append([one_edit(k, rng) for k in rng.sample(pool, w["planted_size"])])
    else:
        res["not_attempted"]["planted_check"] = "not attempted: too few Spafford headwords read"

    sets: dict[str, list[str]] = {}
    if not check_only:
        inv = names.invented_sets(ncfg, english, real)
        for name, lst in inv.items():
            sets[name] = sorted({key(n) for n in lst})
        res["control_lists"] = inv
        bom = bom_places(cfg, english, kjv)
        res["book_of_mormon_list"] = bom
        sets["book_of_mormon"] = sorted({key(n) for n in bom["places"]})
        sets["book_of_mormon_without_quoted_chapters"] = sorted(
            {key(n) for n in bom["places_without_quoted_chapters"]}
        )
        lengths = [len(k) for k in sets["book_of_mormon"]]
        pools = {
            "ngram_kjv": sorted({key(n) for n in ngram_names(ref["kjv"], w, rng)}),
            "kjv_places": sorted({key(n) for n in kjv_places(english)}),
        }
        res["control_pool_sizes"] = {k: len(v) for k, v in pools.items()}
        draws = {
            name: [length_matched(p, lengths, rng) for _ in range(w["control_draws"])]
            for name, p in pools.items()
        }
    else:
        draws = {}
    draws["planted"] = planted

    def at(t: float) -> dict:
        r: dict = {"threshold": t}
        queries = sorted(
            {k for ks in sets.values() for k in ks}
            | {k for ds in draws.values() for d in ds for k in d}
        )
        qpos = {k: i for i, k in enumerate(queries)}
        m = match_ids(queries, geo.keys, t)
        flat = np.concatenate(m) if m else np.zeros(0, dtype=np.int64)
        owner = np.repeat(np.arange(len(queries)), [len(x) for x in m])

        r["modern"] = {}
        passed_any = False
        for radius in w["radii_km"]:
            local, others, dropped = regions(geo, w, radius, flat, owner, len(queries))
            block = {
                "local_entries": local["entries"],
                "local_distinct_keys": local["distinct_keys"],
                "centres_scored": len(others),
                "centres_dropped_too_sparse": dropped,
            }
            pl = [
                summarise(local, others, [qpos[k] for k in d], w, radius) for d in draws["planted"]
            ]
            top = [p["percentile_among_far_english_regions"] >= w["planted_percentile"] for p in pl]
            block["known_answer_planted"] = {
                "draws": len(pl),
                "at_or_above_percentile": sum(top),
                "rate": round(sum(top) / len(pl), 3) if pl else None,
                "mean_local_share": round(float(np.mean([p["local_share"] for p in pl])), 4)
                if pl
                else None,
                "mean_median_region_share": round(
                    float(np.mean([p["median_region_share"] for p in pl])), 4
                )
                if pl
                else None,
                "passed": bool(pl) and sum(top) / len(pl) >= w["planted_bar"],
            }
            r["modern"][str(radius)] = block
            if check_only or not block["known_answer_planted"]["passed"]:
                if not check_only:
                    block["stopped"] = "planted check missed its bar at this radius; not scored"
                continue
            passed_any = True
            block["sets"] = {s: summarise(local, others, [qpos[k] for k in ks], w, radius)
                             for s, ks in sets.items()}  # fmt: skip
            b = block["sets"]["book_of_mormon"]
            block["drawn_controls"] = {}
            for name in ("ngram_kjv", "kjv_places"):
                ds = [
                    summarise(local, others, [qpos[k] for k in d], w, radius) for d in draws[name]
                ]
                ex = [d["excess"] for d in ds]
                block["drawn_controls"][name] = {
                    "draws": len(ds),
                    "mean_local_share": round(float(np.mean([d["local_share"] for d in ds])), 4),
                    "mean_median_region_share": round(
                        float(np.mean([d["median_region_share"] for d in ds])), 4
                    ),
                    "mean_excess": round(float(np.mean(ex)), 4),
                    "mean_percentile": round(
                        float(np.mean([d["percentile_among_far_english_regions"] for d in ds])), 1
                    ),
                    "draws_in_top_5_percent": sum(
                        d["percentile_among_far_english_regions"] >= w["percentile_bar"] for d in ds
                    ),
                    "share_of_draws_with_excess_below_the_books": round(
                        sum(e < b["excess"] for e in ex) / len(ex), 3
                    ),
                }
            above = b["percentile_among_far_english_regions"] >= w["percentile_bar"]
            beats = all(
                block["drawn_controls"][n]["share_of_draws_with_excess_below_the_books"]
                >= w["control_bar"]
                for n in ("ngram_kjv", "kjv_places")
            ) and all(b["excess"] > block["sets"][n]["excess"] for n in ("spalding", "swift"))
            block["verdict"] = (
                "local excess" if above and beats else "cannot tell" if above else "no"
            )
            block["named_regions"] = {
                r["name"]: {
                    "reach_km": r["reach_km"],
                    "english_share": r["english_share"],
                    "book_of_mormon_share": round(share(r["hit"], [qpos[k] for k in
                                                                   sets["book_of_mormon"]]), 4),
                }
                for r in others
                if r["name"] in w["named_centres"]
            }  # fmt: skip
            # Which of the book's names match locally, what they match, and whether a matching New
            # York name was in print before 1830.
            in_region = geo.key_mask(geo.dots(*w["palmyra"]) >= math.cos(radius / EARTH_KM))
            detail = {}
            all_ny = sorted({k for v in ny_keys.values() for k in v})
            for k in sets["book_of_mormon"]:
                ids = [int(i) for i in m[qpos[k]] if in_region[i]]
                if not ids:
                    continue
                printed = {
                    src: sorted(x for x in v if close(k, x, t))[:5] for src, v in ny_keys.items()
                }
                detail[k] = {
                    "modern_keys": sorted(geo.keys[i] for i in ids)[:8],
                    "new_york_before_1830": {s: v for s, v in printed.items() if v},
                    "any_new_york_before_1830": any(close(k, x, t) for x in all_ny),
                }
            block["local_matches"] = detail
            block["local_matches_in_print_in_new_york_before_1830"] = sum(
                d["any_new_york_before_1830"] for d in detail.values()
            )
        # Period names: New York against the other groups, in each world gazetteer.
        psets = {**sets}
        for i, d in enumerate(draws["planted"]):
            psets[f"_planted_{i}"] = d
        for name in ("ngram_kjv", "kjv_places"):
            for i, d in enumerate(draws.get(name, [])[: w["planted_draws"]]):
                psets[f"_{name}_{i}"] = d
        period = period_scores(world, psets, t, w, rng)
        r["period"] = {}
        for gaz, p in period.items():
            table = p["share_by_group"]
            planted_first = [
                period_rank(table, s, w)["first_among_english_groups"]
                for s in psets
                if s.startswith("_planted_") and period_rank(table, s, w)
            ]
            block = {
                "entries": p["entries"],
                "group_sizes": p["group_sizes"],
                "known_answer_planted": {
                    "draws": len(planted_first),
                    "new_york_first": sum(planted_first),
                    "passed": bool(planted_first)
                    and sum(planted_first) / len(planted_first) >= w["planted_bar"],
                },
            }
            if check_only:
                pass
            elif block["known_answer_planted"]["passed"]:
                block["sets"] = {s: period_rank(table, s, w) for s in sets}
                for name in ("ngram_kjv", "kjv_places"):
                    rs = [period_rank(table, s, w) for s in psets if s.startswith(f"_{name}_")]
                    block["sets"][name + "_drawn"] = {
                        "draws": len(rs),
                        "mean_local_share": round(
                            float(np.mean([x["local_share"] for x in rs])), 4
                        ),
                        "first_among_english_groups": sum(
                            x["first_among_english_groups"] for x in rs
                        ),
                        "mean_excess": round(float(np.mean([x["excess"] for x in rs])), 4),
                        "draws_with_excess_below_the_books": sum(
                            x["excess"] < block["sets"]["book_of_mormon"]["excess"] for x in rs
                        ),
                    }
            else:
                block["stopped"] = "planted check missed its bar in this gazetteer; not scored"
            r["period"][gaz] = block
        if check_only:
            return r

        # Holley's pairs, one by one.
        period_all = {
            src: {k for h, _g in entries for k in entry_keys(h, generic, w["min_word_len"])}
            for src, entries in world.items()
        }
        for src, v in ny_keys.items():
            period_all.setdefault(src, set()).update(v)
        pairs = []
        for modern, book, fair in HOLLEY:
            mk = entry_keys(modern, generic, w["min_word_len"])
            bk = {key(p) for p in book.split("-")} | {key(book.replace("-", ""))}
            found = sorted(src for src, v in period_all.items() if any(k in v for k in mk))
            pairs.append(
                {
                    "modern": modern,
                    "book_of_mormon": book,
                    "passes_rule": any(close(a, b, t) for a in mk for b in bk),
                    "book_name_is_biblical": names.norm(book.split("-")[0]) in kjv,
                    "modern_name_found_in_period_gazetteers": found,
                    "modern_name_among_new_york_headwords": sorted(
                        src for src, v in ny_keys.items() if any(k in v for k in mk)
                    ),
                    "fair_before_1830": fair,
                }
            )
        r["holley_pairs"] = {
            "source": "FAIR, Book of Mormon place names from North America; read through an AI "
            "summary of the page on 2026-11-20, not checked by a person",
            "pairs": pairs,
            "passing_rule": sum(p["passes_rule"] for p in pairs),
            "found_in_period_gazetteers": sum(
                bool(p["modern_name_found_in_period_gazetteers"]) for p in pairs
            ),
            "among_new_york_headwords": sum(
                bool(p["modern_name_among_new_york_headwords"]) for p in pairs
            ),
            "passing_rule_and_found_and_not_biblical": sum(
                p["passes_rule"]
                and bool(p["modern_name_found_in_period_gazetteers"])
                and not p["book_name_is_biblical"]
                for p in pairs
            ),
        }
        if not passed_any:
            r["stopped"] = "the planted check passed at no radius; modern regions were not scored"
        return r

    res["by_threshold"] = {label: at(t) for label, t in ka["thresholds"].items()}
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["cache", "check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "cache":
        build_cache(cfg)
        return 0
    res = run(cfg, check_only=a.cmd == "check")
    if a.cmd == "check":
        print(json.dumps({k: v for k, v in res.items() if k != "settings"}, indent=1))
        return 0
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    brief = {k: v for k, v in res.items() if k not in ("settings", "control_lists")}
    print(json.dumps(brief, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
