"""BOM-108: which naming tradition do the Book of Mormon's coined names sit closest to?

One small character model per name list (King James, Hebrew inscriptions, cuneiform records,
Sumerian, Egyptian, classical names as printed in English, the 1790 census, native American
place names and treaty signers, Nahuatl, Maya). A name is assigned to the list whose model gives
it the highest log-likelihood per character. Every list is cut to the same number of names and
redrawn many times. Before the Book of Mormon is scored the method must (a) put held-out names
back in their own list and (b) show how much of that is spelling convention, by scoring King
James names in scholarly transcription. Three designs: every list in its own spelling; the
English-spelled lists only; every list reduced to a coarse consonant skeleton. The invented
names of Spalding, Swift, Ossian and Spenser are scored exactly as the Book of Mormon's. The test
card, written first, is ``data/private/lab/owner/2026-11-20-names/card.md``; settings are
``lab.names`` in the config. The output holds names, counts and scores, no passages.

Usage::

    python -m lab.names lists     # parse every name list; sizes and what was not attempted
    python -m lab.names check     # known-answer checks only (held-out names; spelling)
    python -m lab.names run       # -> data/lab/names/result.json
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np

from lab.paths import FAST, REGISTRY, out
from metadata import config

OUT = REGISTRY / "names"
SRC = FAST / "sources"
N, NN, ST = SRC / "names", SRC / "native_names", SRC / "setting"
EDITION = Path("data/bom/1830/edition_1830.jsonl")
KJV = Path("data/kjv/kjv.jsonl")
TOKEN = re.compile(r"[A-Za-z]+")
TAG = re.compile(r"<[^>]+>")
# Signs with no Latin letter are dropped (aleph, ayin, Egyptian aleph and ayin, glottal marks);
# the rest are folded to their base letter by Unicode decomposition.
FOLD = str.maketrans(
    {
        "ß": "ss",
        "æ": "ae",
        "œ": "oe",
        "ø": "o",
        "đ": "d",
        "ł": "l",
        "ı": "i",
        "ꞽ": "i",
        "ỉ": "i",
        "þ": "th",
        "ð": "d",
        "ŋ": "ng",
    }
)
HEBREW = dict(
    zip(
        "אבגדהוזחטיכךלמםנןסעפףצץקרשת",
        [
            "",
            "b",
            "g",
            "d",
            "h",
            "w",
            "z",
            "h",
            "t",
            "y",
            "k",
            "k",
            "l",
            "m",
            "m",
            "n",
            "n",
            "s",
            "",
            "p",
            "p",
            "s",
            "s",
            "k",
            "r",
            "s",
            "t",
        ],
        strict=True,
    )
)
SKELETON = str.maketrans(
    {
        **dict.fromkeys("aeiouhwyj", None),
        **dict.fromkeys("bfv", "p"),
        **dict.fromkeys("cqgx", "k"),
        "d": "t",
        "z": "s",
    }
)
ENGLISH_DESIGN = ("kjv", "classical", "census_1790", "native_places", "treaty_signers")
ASIDE = ("hebrew_inscr_golub", "census_given")  # held, but not reference sets of their own
INVENTED = ("spalding", "swift", "ossian", "spenser")
CONVENTIONS = {
    "kjv": "English Bible spelling of 1611/1769 (Hebrew, Aramaic and Greek names anglicised)",
    "hebrew_inscr": "DAHPN vocalised scholarly transcription; diacritics folded, aleph/ayin "
    "dropped, morpheme marks dropped",
    "cuneiform_ctij": "ORACC normalised Akkadian-style citation forms; diacritics folded "
    "(Judean and Babylonian names mixed; no language tag)",
    "sumerian": "ORACC ePSD2 citation forms; diacritics and index digits dropped",
    "egyptian": "Egyptological transliteration: consonants only, no vowels written",
    "classical": "Greek and Latin names in Latinised English print (Lempriere 1818, OCR)",
    "census_1790": "surnames and given names in the 1790 census returns (reprint of 1907-08, "
    "OCR), King James names removed",
    "native_places": "Algonquian and Iroquoian place names as spelled by English and Dutch "
    "writers (Beauchamp 1907, Trumbull 1881, OCR)",
    "treaty_signers": "native personal names as spelled by US treaty clerks (Kappler's text)",
    "nahuatl": "Nahuatl personal names in Spanish-based colonial spelling",
    "maya": "Classic Maya ruler names in modern epigraphers' spelling",
    "hebrew_inscr_golub": "Hebrew script mapped letter for letter to consonants (skeleton only)",
}


def norm(s: str) -> str:
    """Lower-case a-z only: diacritics folded, everything else dropped."""
    s = unicodedata.normalize("NFKD", s.lower().translate(FOLD))
    return "".join(c for c in s if "a" <= c <= "z")


def skeleton(s: str) -> str:
    """Coarse consonant skeleton of a normalised name."""
    return s.translate(SKELETON)


def words(names) -> list[str]:
    """Distinct normalised words of a list of raw names (multi-word names are split)."""
    seen = {}
    for raw in names:
        for w in re.split(r"[\s/,;]+", raw):
            w = norm(w)
            if w:
                seen[w] = None
    return list(seen)


# --------------------------------------------------------------------------- running text


def cap_counts(text: str) -> tuple[Counter, Counter, Counter]:
    """(capitalised anywhere, capitalised inside a sentence, lower-case) counts of word tokens."""
    cap, mid, low = Counter(), Counter(), Counter()
    for line in text.split("\n"):
        prev_end = 0
        for i, m in enumerate(TOKEN.finditer(line)):
            w = m.group()
            gap = line[prev_end : m.start()]
            prev_end = m.end()
            if w[0].isupper() and w[1:].islower():
                cap[w.lower()] += 1
                if i > 0 and not re.search(r"[.!?:;\"“”‘(\[_]", gap):
                    mid[w.lower()] += 1
            elif w.islower() and not gap.endswith("-"):  # the tail of Kedesh-naphtali is no word
                low[w] += 1
    return cap, mid, low


def names_by_rule(text: str, english: set[str], min_count: int, min_len: int) -> list[str]:
    """Words capitalised inside a sentence ``min_count`` times, never lower-case, not English."""
    _cap, mid, low = cap_counts(text)
    return sorted(
        w
        for w, c in mid.items()
        if c >= min_count and w not in low and w not in english and len(w) >= min_len
    )


def english_vocabulary(min_count: int) -> set[str]:
    """Lower-case word types of the English texts we hold (King James, Josephus, Swift, Scott)."""
    low = Counter()
    low.update(cap_counts(_kjv_text())[2])
    for f in (
        "josephus_antiquities_whiston.txt",
        "josephus_wars_whiston.txt",
        "swift_gulliver.txt",
        "arabian_nights_scott.txt",
        "koran_sale.txt",
    ):
        if (N / f).exists():
            low.update(cap_counts((N / f).read_text(errors="replace"))[2])
    return {w for w, c in low.items() if c >= min_count}


def _kjv_text() -> str:
    return "\n".join(json.loads(line)["text"] for line in KJV.read_text().splitlines())


# --------------------------------------------------------------------------- the name lists


def load_kjv() -> list[str]:
    names = set()
    cap, _mid, low = cap_counts(_kjv_text())
    names |= {w for w in cap if w not in low}
    joined = re.findall(r"\b[A-Z][a-z]+(?:-[a-z]+)+\b", _kjv_text())  # Shear-jashub as one word
    names |= {j.replace("-", "").lower() for j in joined}
    acap, _m, alow = cap_counts((N / "apocrypha_kjv.txt").read_text(errors="replace"))
    names |= {w for w in acap if w not in alow and w not in low and acap[w] >= 2}
    for f, col in (
        ("bible_data/BibleData-Person.csv", "person_name"),
        ("bible_data/BibleData-Place.csv", "place_name"),
        ("bible_data/HitchcocksBibleNamesDictionary.csv", "Name"),
        ("theographic/CSV/People.csv", "name"),
        ("theographic/CSV/Places.csv", "kjvName"),
    ):
        with (N / f).open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                for w in TOKEN.findall(row.get(col) or ""):
                    if w[0].isupper() and w.lower() not in low:
                        names.add(w.lower())
    return sorted(names)


def _dahpn(path: Path, kind: str, field: str) -> list[str]:
    rows = json.loads(path.read_text())
    return [html.unescape(TAG.sub("", r[field])) for r in rows if r["type"] == kind and r[field]]


def load_hebrew_inscr() -> list[str]:
    return _dahpn(N / "dahpn_epigraphic.json", "epi", "transkription")


def load_golub() -> list[str]:
    rows = json.loads((N / "golub_onomasticon_2025-04.json").read_text())
    return sorted({"".join(HEBREW.get(c, "") for c in r["Name"]) for r in rows if r.get("Name")})


def load_ctij() -> list[str]:
    h = (N / "oracc_ctij_names.html").read_text()
    pat = r'<span class="cf qpn">([^<]+)</span><span class="gw">[^<]*</span> <span class="pos">\(PN'
    return [x for x in re.findall(pat, h) if "x" not in x.lower().split("-")]


def load_sumerian() -> list[str]:
    with zipfile.ZipFile(N / "epsd2_names.zip") as z:
        d = json.loads(z.read("epsd2/names/gloss-qpn.json"))
    return [e["cf"] for e in d["entries"] if e.get("pos") == "PN" and "X" not in e["cf"]]


def load_egyptian() -> list[str]:
    sql = max((N / "pnm_middle_kingdom").glob("*Ver 6*.sql")).read_text()
    part = sql[sql.index("INSERT INTO `personal_names`") :]
    part = part[: part.index("CREATE TABLE") if "CREATE TABLE" in part else len(part)]
    names = re.findall(r"^\t\(\d+, (?:'[^']*'|NULL), (?:'[^']*'|NULL), '([^']+)'", part, re.M)
    xml = (N / "aed_tei/files/dictionary.xml").read_text()
    for entry in re.findall(r"<entry .*?</entry>", xml, re.S):
        if "entity_name/person_name" in entry:
            m = re.search(r"<orth>([^<]+)</orth>", entry)
            if m:
                names.append(m.group(1))
    return [n.replace("-", "").replace(" ", "") for n in names]


def load_classical() -> list[str]:
    text = (N / "classicaldiction00lemp/text.txt").read_text(errors="replace")
    seen = Counter(w.lower() for w in TOKEN.findall(text))
    heads = re.findall(r"^([A-Z][A-Za-z]{2,}),\s+(?:an?|the|now|one|[a-z]+)\b", text, re.M)
    return sorted({h.lower() for h in heads if seen[h.lower()] >= 2})


def load_census(min_count: int, given_min: int) -> tuple[list[str], list[str]]:
    sur, given = Counter(), Counter()
    dirs = sorted(N.glob("headsoffamiliesa*unit"))
    if not dirs:
        raise FileNotFoundError("headsoffamiliesa*unit")
    for d in dirs:
        text = (d / "text.txt").read_text(errors="replace")
        for s, g in re.findall(r"^([A-Z][a-z]{2,})[,.]\s+([A-Z][a-z]{2,})\b", text, re.M):
            sur[s.lower()] += 1
            given[g.lower()] += 1
    return (
        sorted(w for w, c in sur.items() if c >= min_count),
        sorted(w for w, c in given.items() if c >= given_min),
    )


def load_native_places() -> list[str]:
    b = (N / "aboriginalplacen00beau/text.txt").read_text(errors="replace")
    names = [x.replace("-", "") for x in re.findall(r"^([A-Z][a-z]+(?:-[a-z]+)+)\b", b, re.M)]
    t = (N / "indiannamesofpla00trumiala/text.txt").read_text(errors="replace")
    names += re.findall(r"^([A-Z][a-z]{3,})(?:\s+\([^)]*\))?\s*:", t, re.M)
    return names


def load_treaty(english: set[str], year_max: int) -> list[str]:
    files = sorted((NN / "treaties_okstate").glob("*.html"))
    if not files:
        raise FileNotFoundError("treaties_okstate")
    names = []
    for f in files:
        m = re.search(r"-(1[78]\d\d)-\d+\.html$", f.name)
        if not m or int(m.group(1)) > year_max:
            continue
        text = TAG.sub("\n", f.read_text(errors="replace"))
        for raw in re.findall(r"([A-Z][A-Za-z' -]{2,40}?),? \(?his x mark", text):
            raw = raw.split(",")[0]
            names += [w for w in re.split(r"\s+", raw.replace("-", "")) if w]
    return [w for w in names if norm(w) not in english]


def load_nahuatl() -> list[str]:
    h = (NN / "morelos_census_names_hansen.html").read_text(errors="replace")
    names = [TAG.sub("", x).strip() for x in re.findall(r'<td width="33%">(.*?)\n', h)]
    for f in sorted((NN / "aztec_glyphs_personal").glob("*.html")):
        page = f.read_text(errors="replace")
        names += re.findall(r"field-name-title[^>]*>([A-Z][a-z]+) \(", page)
    return [n for n in names if n and " " not in n]


def load_maya(english: set[str]) -> list[str]:
    d = json.loads((NN / "wp_maya_monarchs.json").read_text())["parse"]["wikitext"]["*"]
    raw = re.findall(r"^\*[^\[\n]*\[\[([^\]]+)\]\]", d, re.M)
    raw += re.findall(r"^\*\s*[^:\n]{0,30}:\s*([^\[\n<–(]+)", d, re.M)
    raw += re.findall(r"'''\[\[([^\]]+)\]\]'''", d)
    names = []
    for r in raw:
        r = r.split("|")[-1]
        names += [w for w in re.split(r"[\s-]+", r) if w[:1].isupper()]
    return [w for w in names if norm(w) not in english and not re.search(r"\d", w)]


def reference_sets(cfg: dict) -> tuple[dict[str, list[str]], dict[str, str], set[str]]:
    """Every list as distinct normalised names; what could not be read is named, not zeroed."""
    w = cfg["lab"]["names"]
    english = english_vocabulary(w["english_min_count"])
    sets, missing = {}, {}

    def attempt(name, fn):
        try:
            got = words(fn())
        except (OSError, KeyError, ValueError, zipfile.BadZipFile) as e:
            missing[name] = f"not attempted: {type(e).__name__}: {e}"
            return
        sets[name] = [x for x in got if len(x) >= w["len_min_any"]]

    attempt("kjv", load_kjv)
    attempt("hebrew_inscr", load_hebrew_inscr)
    attempt("cuneiform_ctij", load_ctij)
    attempt("sumerian", load_sumerian)
    attempt("egyptian", load_egyptian)
    attempt("classical", load_classical)
    census = (w["census_min_count"], w["census_given_min_count"])
    attempt("census_1790", lambda: sum(load_census(*census), []))
    attempt("census_given", lambda: load_census(*census)[1])
    if "census_1790" in sets and "kjv" in sets:
        # A biblical name borne by an American in 1790 is a King James name: it has no single
        # right answer between the two lists, so it stays in the King James list only.
        kjv = set(sets["kjv"])
        sets["census_1790"] = [x for x in sets["census_1790"] if x not in kjv]
    attempt("native_places", load_native_places)
    attempt("treaty_signers", lambda: load_treaty(english, w["treaty_year_max"]))
    attempt("nahuatl", load_nahuatl)
    attempt("maya", lambda: load_maya(english))
    try:
        sets["hebrew_inscr_golub"] = [x for x in load_golub() if len(x) >= 2]
    except (OSError, KeyError, ValueError) as e:
        missing["hebrew_inscr_golub"] = f"not attempted: {type(e).__name__}: {e}"
    return sets, missing, english


def invented_sets(cfg: dict, english: set[str], real: set[str]) -> dict[str, list[str]]:
    """Names found by the capitalisation rule in four single-author works, real names removed."""
    w = cfg["lab"]["names"]
    texts = {}
    sp = N / "themanuscriptsto00spauuoft/text.txt"
    if sp.exists():
        t = sp.read_text(errors="replace")
        texts["spalding"] = t[t.index("INTRODUCTION.") :] if "INTRODUCTION." in t else t
    for name, files in (
        ("swift", ["swift_gulliver.txt"]),
        (
            "ossian",
            [
                "ossian_fragments_1760.txt",
                "poemsofossiantra10macp/text.txt",
                "poemsofossiantra11macp/text.txt",
            ],
        ),
        ("spenser", ["spenser_faerie_queene_1.txt"]),
    ):
        got = [(N / f).read_text(errors="replace") for f in files if (N / f).exists()]
        if got:
            texts[name] = "\n".join(got)
    for f in (
        "josephus_antiquities_whiston.txt",
        "koran_sale.txt",
        "arabian_nights_scott.txt",
        "morgan_freemasonry.txt",
        "americangazettee00mors/text.txt",
        "classicaldiction00lemp/text.txt",
    ):
        if (N / f).exists():
            texts["_" + f] = (N / f).read_text(errors="replace")
    tokens = {k: {t.lower() for t in TOKEN.findall(v)} for k, v in texts.items()}
    res = {}
    for name, text in texts.items():
        if name.startswith("_"):
            continue
        text = re.sub(r"-\s*\n\s*", "", text)  # rejoin words the printer broke across lines
        found = set(names_by_rule(text, english, w["invented_min_count"][name], w["len_min_any"]))
        # A name another book also prints is not this author's invention.
        elsewhere = set().union(*(v for k, v in tokens.items() if k != name))
        found = {x for x in found if x not in real and x not in elsewhere}
        res[name] = sorted(x for x in found if not _inflected(x, found))
    return res


def _inflected(x: str, found: set[str]) -> bool:
    """A plural or people-form of another found name (Sciotans beside Sciota)."""
    return any(x.endswith(e) and x[: -len(e)] in found for e in ("s", "ns", "n", "ians", "ian"))


# --------------------------------------------------------------------------- Book of Mormon


def bom_names(cfg: dict, english: set[str], kjv: set[str]) -> dict:
    """The 1830 text's names by rule, checked against the Onomasticon and the Wikipedia lists."""
    w = cfg["lab"]["names"]
    rows = [json.loads(x) for x in EDITION.read_text().splitlines()]
    body = [r for r in rows if r["kind"] == "body"]
    cap, _mid, low = cap_counts("\n".join(r["text"] for r in body))
    kjv_low = cap_counts(_kjv_text())[2]
    cand = {x for x in cap if x not in low and x not in kjv_low and len(x) >= w["len_min_any"]}
    for x in sorted(cand):  # fold group forms to their stem when the stem is itself a name
        for end in ("itish", "ites", "ite", "ies", "s"):
            if x.endswith(end) and ({x[: -len(end)], x[: -len(end)] + "i"} & cand):
                cand.discard(x)
    ono = set(
        words(
            n.lstrip("*").replace("-", " ")
            for n in json.loads((N / "onomasticon_names.json").read_text())
        )
    )
    wp_people = _wp_bullets(ST / "wp_bom_people.json")
    wp_places = _wp_bullets(ST / "wp_bom_places.json")
    listed = ono | set(wp_people) | set(wp_places)
    confirmed = sorted(cand & listed)
    in_ether = Counter()
    for r in body:
        for t in set(TOKEN.findall(r["text"])):
            in_ether[(t.lower(), r["book"] == "Ether")] += 1
    groups = {}
    for x in confirmed:
        g = []
        if in_ether[(x, True)] and not in_ether[(x, False)]:
            g.append("jaredite")
        desc = wp_people.get(x, "")
        first = re.search(r"Jaredite|Lamanite|Nephite", desc)
        if first and not g:
            g.append(first.group().lower())
        if x in wp_places:
            g.append("place")
        groups[x] = g or ["ungrouped"]
    coined = [x for x in confirmed if x not in kjv]
    return {
        "by_rule": len(cand),
        "confirmed": len(confirmed),
        "rule_only": sorted(cand - listed),
        "onomasticon_only": sorted(
            x
            for x in ono - cand
            if x not in kjv and x not in english and not x.endswith(("ites", "ite", "ies"))
        ),
        "biblical": sorted(x for x in confirmed if x in kjv),
        "coined": coined,
        "groups": {x: groups[x] for x in coined},
    }


def _wp_bullets(path: Path) -> dict[str, str]:
    """First capitalised words of each bullet in a Wikipedia list -> the bullet's description."""
    text = json.loads(path.read_text())["parse"]["wikitext"]["*"]
    got = {}
    for line in re.findall(r"^\*+\s*(.+)$", text, re.M):
        line = re.sub(r"<ref.*?(</ref>|/>)", "", line)
        line = re.sub(r"<sup>.*?</sup>", "", line)
        line = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", line)
        line = re.sub(r"['<>/u]{2,}|<u>|</u>", "", line)
        head, _, desc = line.partition(",")
        for t in TOKEN.findall(head.replace("-", " ")):
            if t[0].isupper() and t.lower() not in (
                "city",
                "land",
                "hill",
                "river",
                "valley",
                "mount",
                "plains",
                "waters",
                "wilderness",
                "the",
                "sea",
                "king",
                "brother",
            ):
                got.setdefault(norm(t), desc)
    return got


# --------------------------------------------------------------------------- the model

V = 27  # a-z and the word boundary


def encode(name: str) -> np.ndarray:
    """Flat trigram indices of a name padded with boundaries (one per letter, plus the end)."""
    x = [26, 26] + [ord(c) - 97 for c in name] + [26]
    return np.array([x[i] * V * V + x[i + 1] * V + x[i + 2] for i in range(len(x) - 2)])


def fit(names: list[str], k: float, lam: list[float]) -> np.ndarray:
    """Interpolated trigram, bigram and letter model: a table of log-probabilities."""
    c3 = np.zeros(V**3)
    if names:
        np.add.at(c3, np.concatenate([encode(n) for n in names]), 1)
    c3 = c3.reshape(V, V, V)
    c2 = c3.sum(0)  # (previous, next)
    c1 = c2.sum(0)
    p3 = (c3 + k) / (c3.sum(2, keepdims=True) + k * V)
    p2 = (c2 + k) / (c2.sum(1, keepdims=True) + k * V)
    p1 = (c1 + k) / (c1.sum() + k * V)
    return np.log(lam[0] * p3 + lam[1] * p2[None, :, :] + lam[2] * p1[None, None, :]).ravel()


def score(models: np.ndarray, names: list[str]) -> np.ndarray:
    """(names x models) mean log-likelihood per character."""
    enc = [encode(n) for n in names]
    flat = np.concatenate(enc)
    starts = np.cumsum([0] + [len(e) for e in enc[:-1]])
    sums = np.add.reduceat(models[:, flat], starts, axis=1)
    return (sums / np.array([len(e) for e in enc])).T


def design(sets: dict[str, list[str]], targets: dict[str, list[str]], w: dict, seed: int) -> dict:
    """Size-matched repeats: held-out confusion, and each target list's share per set."""
    rng = np.random.default_rng(seed)
    labels = sorted(sets)
    k = len(labels)
    pool = {s: [n for n in sets[s] if w["len_min"] <= len(n) <= w["len_max"]] for s in labels}
    need = w["match_n"] + w["test_n"]
    short = {s: len(pool[s]) for s in labels if len(pool[s]) < need}
    if short:
        raise ValueError(f"sets smaller than match_n + test_n: {short}")
    confusion = np.zeros((k, k))
    tnames = {t: [n for n in v if n] for t, v in targets.items() if v}
    shares = {t: [] for t in tnames}
    votes = {t: np.zeros((len(v), k)) for t, v in tnames.items()}
    for _ in range(w["repeats"]):
        train, test = [], []
        for s in labels:
            order = rng.permutation(len(pool[s]))
            test.append([pool[s][i] for i in order[: w["test_n"]]])
            train.append([pool[s][i] for i in order[w["test_n"] : need]])
        models = np.stack([fit(t, w["smoothing"], w["interpolation"]) for t in train])
        for i, held in enumerate(test):
            best = score(models, held).argmax(1)
            confusion[i] += np.bincount(best, minlength=k)
        for t, names in tnames.items():
            best = score(models, names).argmax(1)
            votes[t][np.arange(len(names)), best] += 1
            pick = rng.integers(0, len(names), len(names))  # the names are resampled too
            shares[t].append(np.bincount(best[pick], minlength=k) / len(names))
    confusion /= confusion.sum(1, keepdims=True)
    recall = {s: round(float(confusion[i, i]), 3) for i, s in enumerate(labels)}
    res = {
        "sets": {s: len(pool[s]) for s in labels},
        "chance": round(1 / k, 3),
        "held_out_recall": recall,
        "mean_recall": round(float(np.mean(list(recall.values()))), 3),
        "confusion_rows_true_cols_assigned": {
            s: {labels[j]: round(float(confusion[i, j]), 3) for j in range(k)}
            for i, s in enumerate(labels)
        },
        "targets": {},
    }
    for t, names in tnames.items():
        arr = np.array(shares[t])
        res["targets"][t] = {
            "names": len(names),
            "share": {
                s: [
                    round(float(arr[:, j].mean()), 3),
                    round(float(np.percentile(arr[:, j], 2.5)), 3),
                    round(float(np.percentile(arr[:, j], 97.5)), 3),
                ]
                for j, s in enumerate(labels)
            },
            "usual_set": {n: labels[int(votes[t][i].argmax())] for i, n in enumerate(names)},
        }
    return res


def passed(res: dict, w: dict) -> bool:
    k = len(res["sets"])
    return res["mean_recall"] >= max(w["bar_mean"], 3 / k) and min(
        res["held_out_recall"].values()
    ) >= min(2 / k, 1.0)


def lead(shares: dict[str, list[float]]) -> str | None:
    """The set whose lower bound is above every other set's upper bound, if there is one."""
    top = max(shares, key=lambda s: shares[s][0])
    return top if all(shares[top][1] > v[2] for s, v in shares.items() if s != top) else None


# --------------------------------------------------------------------------- recombination


def one_edit(name: str, base: set[str]) -> bool:
    """Is ``name`` one letter (changed, added or dropped) from a different name in ``base``?"""
    abc = "abcdefghijklmnopqrstuvwxyz"
    for i in range(len(name) + 1):
        for c in abc:
            if name[:i] + c + name[i:] in base:
                return True
        if i < len(name):
            if name[:i] + name[i + 1 :] in base:
                return True
            for c in abc:
                if c != name[i] and name[:i] + c + name[i + 1 :] in base:
                    return True
    return False


def splice_tables(base: set[str], part: int) -> tuple[Counter, Counter]:
    pre, suf = Counter(), Counter()
    for n in base:
        for i in range(part, len(n)):
            pre[n[:i]] += 1
        for i in range(1, len(n) - part + 1):
            suf[n[i:]] += 1
    return pre, suf


def splice(name: str, pre: Counter, suf: Counter, part: int, own: int = 0) -> bool:
    """Start of one base name joined to the end of another, each part ``part`` letters or more.

    ``own`` = 1 when ``name`` is itself in the base, so that its own parts do not count.
    """
    return any(
        pre[name[:i]] > own and suf[name[i:]] > own for i in range(part, len(name) - part + 1)
    )


def recombination(lists: dict[str, list[str]], kjv: set[str], w: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    pre, suf = splice_tables(kjv, w["splice_min"])
    res = {}

    def rates(names: list[str], own: int) -> np.ndarray:
        e = np.array([one_edit(n, kjv) for n in names])
        s = np.array([splice(n, pre, suf, w["splice_min"], own) for n in names])
        return np.stack([e, s, e | s]).astype(float)

    for label, names in lists.items():
        own = 1 if label == "kjv" else 0
        names = [n for n in names if (own or n not in kjv) and len(n) >= w["len_min_any"]]
        if len(names) > w["recombination_sample"]:
            names = [names[i] for i in rng.permutation(len(names))[: w["recombination_sample"]]]
        if not names:
            continue
        r = rates(names, own)
        boot = np.array(
            [r[:, rng.integers(0, len(names), len(names))].mean(1) for _ in range(w["repeats"])]
        )
        res[label] = {
            "names": len(names),
            "mean_length": round(float(np.mean([len(n) for n in names])), 2),
            **{
                key: [
                    round(float(r[j].mean()), 3),
                    round(float(np.percentile(boot[:, j], 2.5)), 3),
                    round(float(np.percentile(boot[:, j], 97.5)), 3),
                ]
                for j, key in enumerate(("one_edit", "splice", "either"))
            },
        }
    return res


# Names that Tvedtnes, Gee and Roper (2000) report as attested in Hebrew inscriptions.
TVEDTNES_2000 = (
    "sariah",
    "alma",
    "abish",
    "aha",
    "ammonihah",
    "chemish",
    "hagoth",
    "himni",
    "isabel",
    "jarom",
    "josh",
    "luram",
    "mathoni",
    "mathonihah",
    "muloki",
    "sam",
)


def attestation(lists: dict[str, list[str]], hebrew: set[str], w: dict) -> dict:
    """Share of each list whose consonant skeleton equals that of a Hebrew-inscription name."""
    res = {}
    for label, names in lists.items():
        sk = [skeleton(n) for n in names]
        sk = [x for x in sk if len(x) >= w["skeleton_len_min"]]
        if sk:
            res[label] = {
                "names": len(sk),
                "share": round(sum(x in hebrew for x in sk) / len(sk), 3),
            }
    return res


def shuffled(names: list[str], seed: int) -> list[str]:
    """Each name's own letters in random order: same letters and length, no pattern."""
    rng = np.random.default_rng(seed)
    return ["".join(rng.permutation(list(n))) for n in names]


# --------------------------------------------------------------------------- Wilcox analogue


def positional(names: list[str], english: list[str], positions: int) -> dict:
    """Mean position-specific letter and letter-pair probability (English word types as base)."""
    letter = [Counter() for _ in range(positions)]
    pair = [Counter() for _ in range(positions - 1)]
    for word in english:
        for i in range(min(positions, len(word))):
            letter[i][word[i]] += 1
            if i < positions - 1 and i + 1 < len(word):
                pair[i][word[i : i + 2]] += 1
    lt = [sum(c.values()) for c in letter]
    pt = [sum(c.values()) for c in pair]
    vec, per_name = [], []
    for i in range(positions):
        vals = [letter[i][n[i]] / lt[i] for n in names if len(n) > i]
        vec.append(float(np.mean(vals)) if vals else 0.0)
    for i in range(positions - 1):
        vals = [pair[i][n[i : i + 2]] / pt[i] for n in names if len(n) > i + 1]
        vec.append(float(np.mean(vals)) if vals else 0.0)
    for n in names:
        ps = [letter[i][n[i]] / lt[i] for i in range(min(positions, len(n)))]
        per_name.append(float(np.mean(ps)))
    return {
        "vector": [round(v, 5) for v in vec],
        "names": len(names),
        "variance_of_name_means": round(float(np.var(per_name)), 7),
        "mean_length": round(float(np.mean([len(n) for n in names])), 2),
    }


def wilcox_analogue(groups: dict[str, list[str]], english: set[str], w: dict) -> dict:
    base = sorted(x for x in english if len(x) >= 2)
    prof = {g: positional(n, base, w["wilcox_positions"]) for g, n in groups.items() if n}
    dist = {}
    for a in prof:
        for b in prof:
            if a < b:
                d = math.dist(prof[a]["vector"], prof[b]["vector"])
                dist[f"{a} ~ {b}"] = round(d, 5)
    return {
        "profiles": prof,
        "distances": dist,
        "note": "letters, not phonemes; an analogue of Wilcox et al., not a reproduction",
    }


# --------------------------------------------------------------------------- commands


def check(cfg: dict, sets: dict, extra_targets: dict | None = None) -> dict:
    """The known-answer checks; with ``extra_targets`` the same repeats also score those lists."""
    w = cfg["lab"]["names"]
    big = {s: v for s, v in sets.items() if s not in ASIDE}
    usable = {
        s: v
        for s, v in big.items()
        if sum(w["len_min"] <= len(n) <= w["len_max"] for n in v) >= w["min_set"]
    }
    left_out = {s: len(v) for s, v in big.items() if s not in usable}
    spelling = {}
    try:
        spelling["kjv_names_scholarly"] = words(
            _dahpn(N / "dahpn_all.json", "bib", "transkription")
        )
        spelling["kjv_names_german_bible"] = words(
            _dahpn(N / "dahpn_all.json", "bib", "elberfelder")
        )
    except (OSError, KeyError, ValueError) as e:
        spelling = {}
        left_out["spelling_check"] = f"not attempted: {e}"
    extra = extra_targets or {}
    res = {"left_out_too_small": left_out}
    res["all"] = design(usable, {**spelling, **extra}, w, w["seed"])
    eng = {s: v for s, v in usable.items() if s in ENGLISH_DESIGN}
    we = {**w, "match_n": w["english_match_n"], "test_n": w["english_test_n"]}
    res["english"] = design(eng, extra, we, w["seed"] + 1)
    skel = {s: sorted({skeleton(n) for n in v} - {""}) for s, v in usable.items()}
    if "hebrew_inscr_golub" in sets:
        skel["hebrew_inscr_golub"] = sorted({skeleton(n) for n in sets["hebrew_inscr_golub"]})
    ws = {
        **w,
        "len_min": w["skeleton_len_min"],
        "len_max": w["skeleton_len_max"],
        "match_n": w["skeleton_match_n"],
        "test_n": w["skeleton_test_n"],
    }
    need = ws["match_n"] + ws["test_n"]
    skel = {
        s: v
        for s, v in skel.items()
        if sum(ws["len_min"] <= len(n) <= ws["len_max"] for n in v) >= need
    }
    sk_targets = {
        t: [skeleton(n) for n in v if len(skeleton(n)) >= ws["len_min"]]
        for t, v in {**spelling, **extra}.items()
    }
    res["skeleton"] = design(skel, sk_targets, ws, w["seed"] + 2)
    for d in ("all", "english"):
        res[d]["passed"] = passed(res[d], w)
    if spelling:
        sh = res["all"]["targets"]["kjv_names_scholarly"]["share"]
        res["spelling_check"] = {
            "kjv_names_in_scholarly_dress_sent_to_kjv": sh.get("kjv"),
            "sent_to_hebrew_inscr": sh.get("hebrew_inscr"),
            "same_names_in_german_bible_spelling_sent_to_kjv": res["all"]["targets"][
                "kjv_names_german_bible"
            ]["share"].get("kjv"),
            "design_all_is_a_test_of_spelling": sh["kjv"][0] < 0.5,
        }
    return res


def run(cfg: dict) -> dict:
    w = cfg["lab"]["names"]
    sets, missing, english = reference_sets(cfg)
    res = {
        "settings": w,
        "conventions": CONVENTIONS,
        "not_attempted": missing,
        "list_sizes": {s: len(v) for s, v in sets.items()},
    }
    first = check(cfg, sets)
    if not (first["all"]["passed"] or first["english"]["passed"]):
        res["known_answer"] = first
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
        return res
    kjv = set(sets["kjv"])
    real = kjv | set(sets.get("classical", [])) | set(sets.get("census_1790", []))
    invented = invented_sets(cfg, english, real)
    bom = bom_names(cfg, english, kjv)
    coined = bom["coined"]
    targets = {"book_of_mormon": coined, **invented}
    targets["invented_pooled"] = sorted(
        {n for k in ("spalding", "swift", "ossian") for n in invented.get(k, [])}
    )
    for g in ("jaredite", "lamanite", "nephite", "place", "ungrouped"):
        targets[f"book_of_mormon_{g}"] = [n for n in coined if g in bom["groups"][n]]
    targets["book_of_mormon_letters_shuffled"] = shuffled(coined, w["seed"])
    full = check(cfg, sets, targets)
    res["known_answer"] = {
        d: {k: v for k, v in full[d].items() if k != "targets"}
        for d in ("all", "english", "skeleton")
    }
    res["known_answer"]["left_out_too_small"] = full["left_out_too_small"]
    res["spelling_check"] = full.get("spelling_check")
    res["book_of_mormon_list"] = bom
    res["invented_lists"] = invented
    res["designs"] = {}
    for d in ("all", "english", "skeleton"):
        if d != "skeleton" and not full[d]["passed"]:
            res["designs"][d] = {"stopped": "known-answer bar missed; not scored"}
            continue
        t = full[d]["targets"]
        block = {
            "shares": {k: {"names": v["names"], "share": v["share"]} for k, v in t.items()},
            "usual_set": t["book_of_mormon"]["usual_set"],
        }
        b, p = t["book_of_mormon"]["share"], t["invented_pooled"]["share"]
        top = lead(b)
        block["verdict"] = {
            "closest_set": top,
            "invented_names_closest_set": lead(p),
            "distinct_from_invention": bool(top)
            and (b[top][1] > p[top][2] or b[top][2] < p[top][1]),
        }
        res["designs"][d] = block
    lists = {
        "book_of_mormon": coined,
        **invented,
        "book_of_mormon_letters_shuffled": targets["book_of_mormon_letters_shuffled"],
        **{s: v for s, v in sets.items() if s not in ASIDE},
    }
    res["recombination"] = recombination(lists, kjv, w, w["seed"] + 3)
    bom_r = res["recombination"]["book_of_mormon"]["either"][0]
    res["recombination"]["more_recombined_than_invention"] = all(
        bom_r > res["recombination"][k]["either"][2] for k in INVENTED if k in res["recombination"]
    )
    hebrew = {skeleton(n) for k in ("hebrew_inscr", "hebrew_inscr_golub") for n in sets.get(k, [])}
    res["skeleton_match_with_hebrew_inscriptions"] = {
        "note": "added after the card was written (Tvedtnes, Gee and Roper 2000 arrived mid-run); "
        "a coarse consonant skeleton matches often by chance, which the other rows measure",
        **attestation(
            {
                **{k: v for k, v in lists.items() if k not in ("hebrew_inscr",)},
                "tvedtnes_2000_names": list(TVEDTNES_2000),
            },
            hebrew,
            w,
        ),
        "tvedtnes_names_matching": sorted(
            n
            for n in TVEDTNES_2000
            if len(skeleton(n)) >= w["skeleton_len_min"] and skeleton(n) in hebrew
        ),
    }
    res["wilcox_analogue"] = wilcox_analogue(
        {
            "book_of_mormon": coined,
            "census_given": sets.get("census_given", []),
            "spalding": invented.get("spalding", []),
        },
        english,
        w,
    )
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["lists", "check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "lists":
        sets, missing, english = reference_sets(cfg)
        w = cfg["lab"]["names"]
        for s, v in sets.items():
            fit_n = sum(w["len_min"] <= len(n) <= w["len_max"] for n in v)
            print(
                f"{s:20} {len(v):6} names, {fit_n:6} of matched length; "
                f"e.g. {v[:: max(1, len(v) // 8)][:8]}"
            )
        print("not attempted:", missing)
        real = set(sets["kjv"]) | set(sets.get("classical", [])) | set(sets.get("census_1790", []))
        for s, v in invented_sets(cfg, english, real).items():
            print(f"{s:20} {len(v):6} invented by rule: {v}")
        return 0
    if a.cmd == "check":
        res = check(cfg, reference_sets(cfg)[0])
        json.dump(res, sys.stdout, indent=1)
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    brief = {k: res.get(k) for k in ("stopped", "spelling_check", "not_attempted", "list_sizes")}
    print(json.dumps(brief, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
