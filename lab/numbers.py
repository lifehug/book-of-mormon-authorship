"""BOM-114: number profiles (base ten or base twenty) and the weights of Alma 11.

Part 1 reads every number written in words or digits from each text, turns it into a value and
builds a profile of fifteen measures (round tens, hundreds and thousands, a base-twenty measure,
favoured numbers, units, ordinals, calendar years). A nearest-centre classifier over three
traditions (the Bible and the ancient Near East; native Mesoamerican texts in English; American
narrative of the 1810s and 1820s) is first checked on held-out texts, then the Book of Mormon and
Clavigero are placed. Part 2 writes the pieces of Alma 11 as ratios, scores their fit to a
catalogue of real weight and coin systems under one rule, and counts how often a random system of
the same size fits some real system as well. **The catalogue is written from memory and is
unverified: part 2 is a pilot until it is sourced.** The test card, written first, is
``data/private/lab/owner/2026-11-20-numbers/card.md``; settings are ``lab.numbers`` in the config.
The output holds names, ids, counts and ratios, no text.

Usage::

    python -m lab.numbers check     # known-answer checks only (held-out texts; base twenty)
    python -m lab.numbers run       # -> data/lab/setting/numbers/result.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import subprocess
from fractions import Fraction
from pathlib import Path

from lab import door, registry
from lab.paths import FAST, NOTES, REGISTRY, out
from lab.wherefore import QUOTED
from metadata import config

OUT = REGISTRY / "setting" / "numbers"
SRC = FAST / "sources"
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
KJV = Path("data/kjv/kjv.jsonl")
CAND = Path("data/candidates/text")
CHRISTENSON = NOTES / "sources" / "setting"

# ---------------------------------------------------------------------------- reading numbers

_U = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
_U += "fifteen sixteen seventeen eighteen nineteen"
_T = "twenty thirty forty fifty sixty seventy eighty ninety"
_UO = "zeroth first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth "
_UO += "thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth"
_TO = "twentieth thirtieth fortieth fiftieth sixtieth seventieth eightieth ninetieth"
WORDS: dict[str, tuple[str, int, bool]] = {}  # word -> (type, value, ordinal)
for _i, _w in enumerate(_U.split()):
    WORDS[_w] = ("U", _i, False)
for _i, _w in enumerate(_UO.split()):
    WORDS[_w] = ("U", _i, True)
for _i, _w in enumerate(_T.split()):
    WORDS[_w] = ("T", 20 + 10 * _i, False)
for _i, _w in enumerate(_TO.split()):
    WORDS[_w] = ("T", 20 + 10 * _i, True)
for _i, _w in enumerate(("twoscore", "threescore", "fourscore", "fivescore", "sixscore")):
    WORDS[_w] = ("S", 40 + 20 * _i, False)
WORDS.update(
    {
        "score": ("C", 20, False),
        "hundred": ("H", 100, False),
        "hundredth": ("H", 100, True),
        "thousand": ("K", 1000, False),
        "thousandth": ("K", 1000, True),
        "million": ("K", 1000000, False),
    }
)
del WORDS["zero"], WORDS["zeroth"]

TOKEN = re.compile(r"[a-z]+|\d{1,3}(?:,\d{3})+|\d+|[^\sa-z\d]")
# A number in digits counts only after a lower-case word that is not one of these.
REFERENCE = set("p pp vol vols chap ch lib cap fol page pages note notes sect sec book no".split())
REFERENCE |= set("chapter verse ver line lines tom tome plate fig figure".split())
UNITS = {
    "year": "year year years".split(),
    "time": "day days month months week weeks hour hours night nights moon moons generation "
    "generations katun katuns ahau season seasons age ages sabbath sabbaths watch".split(),
    "people": "man men woman women person persons people soul souls soldier soldiers warrior "
    "warriors son sons daughter daughters child children wife wives horsemen footmen brethren "
    "priest priests king kings prince princes captain captains chief chiefs lord lords servant "
    "servants tribe tribes family families nation nations elder elders disciple disciples "
    "prisoner prisoners indian indians troops militia regulars seamen sailors spaniards".split(),
    "measure": "cubit cubits mile miles league leagues furlong furlongs foot feet pace paces "
    "fathom fathoms talent talents shekel shekels pound pounds dollar dollars piece pieces "
    "measure measures gun guns acre acres yard yards inch inches ton tons bushel bushels "
    "drachmae drachmas penny pence span rod rods degree degrees stadia".split(),
}
UNIT_OF = {w: k for k, ws in UNITS.items() for w in ws}


def _sub100(t: list[str], i: int) -> tuple[int, int, bool, bool] | None:
    """A number below a hundred (or a count of scores) at ``i``: value, next, ordinal, score."""
    w = WORDS.get(t[i]) if i < len(t) else None
    if w is None or w[0] not in "UTS":
        return None
    kind, val, ordinal = w
    nxt = WORDS.get(t[i + 1]) if i + 1 < len(t) else None
    if ordinal:
        return val, i + 1, True, False
    score = kind == "S"
    if kind == "U" and nxt and nxt[0] == "C":  # three score
        val, i, kind, score = val * 20, i + 1, "S", True
    elif kind == "U":
        after = WORDS.get(t[i + 2]) if i + 2 < len(t) and t[i + 1] == "and" else None
        if val < 10 and after and after[0] == "T":  # two and twenty
            return val + after[1], i + 3, after[2], False
        return val, i + 1, False, False
    limit = 20 if score else 10  # threescore and fifteen; twenty and four
    j = i + 1
    if j < len(t) and t[j] in ("and", "-"):
        j += 1
    add = WORDS.get(t[j]) if j < len(t) else None
    if add and add[0] == "U" and add[1] < limit:
        return val + add[1], j + 1, add[2], score
    return val, i + 1, False, score


def _sub1000(t: list[str], i: int) -> tuple[int, int, bool, bool] | None:
    """A number below a thousand at ``i`` (an hundred and twenty; twelve hundred; six)."""
    head = _sub100(t, i)
    if head is None and i + 1 < len(t) and t[i] in ("a", "an"):
        if WORDS.get(t[i + 1], ("", 0, False))[0] in ("H", "K"):
            head = (1, i + 1, False, False)
    if head is None:
        if i < len(t) and WORDS.get(t[i], ("", 0, False))[0] == "H":
            head = (1, i, False, False)
        else:
            return None
    val, j, ordinal, score = head
    w = WORDS.get(t[j]) if j < len(t) else None
    if ordinal or w is None or w[0] != "H":
        return head
    val, j = val * 100, j + 1
    if w[2]:
        return val, j, True, score
    k = j + 1 if j < len(t) and t[j] == "and" else j
    tail = _sub100(t, k)
    if tail is not None:
        return val + tail[0], tail[1], tail[2], score or tail[3]
    return val, j, False, score


def _phrase(t: list[str], i: int) -> tuple[int, int, bool, bool] | None:
    """A whole number in words at ``i``: value, next index, ordinal, written with a score."""
    head = _sub1000(t, i)
    if head is None:
        return None
    val, j, ordinal, score = head
    total, mult = 0, None
    while not ordinal:
        w = WORDS.get(t[j]) if j < len(t) else None
        if w is None or w[0] != "K":
            break
        # forty thousand; then "and three thousand and five hundred" joins if it fits below
        val, j, ordinal, mult = val * w[1], j + 1, w[2], w[1]
        if j < len(t) and (WORDS.get(t[j]) or ("",))[0] == "K":
            continue  # a hundred thousand thousand
        k = j + 1 if j < len(t) and t[j] == "and" else j
        tail = None if ordinal else _sub1000(t, k)
        if tail is None:
            break
        after = WORDS.get(t[tail[1]]) if tail[1] < len(t) else None
        if after and after[0] == "K" and not tail[2]:
            if val % 10 ** len(str(tail[0] * after[1])) == 0:  # 600,000 and 3,000
                total, val, j, score = total + val, tail[0], tail[1], score or tail[3]
                continue
            break
        if tail[0] < mult:
            total, val, j, ordinal, score = total + val, tail[0], tail[1], tail[2], score or tail[3]
        break
    return total + val, j, ordinal, score


def numbers(text: str, cfg: dict) -> list[tuple[int, str, str]]:
    """Every number in ``text``: (value, kind, unit). Kind: cardinal, ordinal, calendar."""
    n = cfg["lab"]["numbers"]
    t = TOKEN.findall(text.lower().replace("—", " . "))
    found, i = [], 0
    while i < len(t):
        tok = t[i]
        if "0" <= tok[0] <= "9":  # ASCII digits only (not superscripts)
            prev = t[i - 1] if i else ""
            ok = prev.isalpha() and prev not in REFERENCE and len(tok.replace(",", "")) <= 9
            val, j = int(tok.replace(",", "")), i + 1
            ordinal = j < len(t) and t[j] in ("st", "nd", "rd", "th")
            j += ordinal
            unit = UNIT_OF.get(t[j], "other") if j < len(t) else "other"
            if ok and val > 1:
                year = "," not in tok and n["year_lo"] <= val <= n["year_hi"]
                if year and unit not in ("people", "measure"):
                    found.append((val, "calendar", unit))
                else:
                    found.append((val, "ordinal" if ordinal else "cardinal", unit))
            i = j
            continue
        got = _phrase(t, i) if tok in WORDS or tok in ("a", "an") else None
        if got is None:
            i += 1
            continue
        val, j, ordinal, score = got
        unit = UNIT_OF.get(t[j], "other") if j < len(t) else "other"
        if val > 1:
            found.append((val, ("ordinal" if ordinal else "cardinal") + ("+score" * score), unit))
        i = j
    return found


# ------------------------------------------------------------------------------- the profile

FEATURES = (
    "small", "big", "round10", "round100", "round1000", "base20", "fav_bible", "fav_meso",
    "ordinal", "unit_year", "unit_time", "unit_people", "unit_measure", "calendar", "score_form",
)  # fmt: skip
COUNTING = FEATURES[:8]


def _share(k: int, n: int, least: int = 5) -> float | None:
    return round(k / n, 4) if n >= least else None


def base20_counts(nums: list[tuple[int, str, str]], cfg: dict) -> tuple[int, int]:
    """(multiples of 20, other multiples of 10) among round values in range, hundreds left out."""
    n = cfg["lab"]["numbers"]
    vals = [v for v, k, _ in nums if k != "calendar" and n["base20_lo"] <= v <= n["base20_hi"]]
    vals = [v for v in vals if v % 10 == 0 and v % 100 != 0]
    twenty = sum(v % 20 == 0 for v in vals)
    return twenty, len(vals) - twenty


def profile(nums: list[tuple[int, str, str]], cfg: dict) -> dict:
    vals = [v for v, k, _ in nums if k != "calendar"]
    n, m = len(nums), len(vals)
    ge10 = [v for v in vals if v >= 10]
    ge100 = [v for v in vals if v >= 100]
    ge1000 = [v for v in vals if v >= 1000]
    twenty, ten = base20_counts(nums, cfg)
    h400 = [v for v in vals if v >= 400 and v % 100 == 0]
    return {
        "n": n,
        "small": _share(sum(v <= 10 for v in vals), m),
        "big": _share(len(ge100), m),
        "round10": _share(sum(v % 10 == 0 for v in ge10), len(ge10)),
        "round100": _share(sum(v % 100 == 0 for v in ge100), len(ge100)),
        "round1000": _share(sum(v % 1000 == 0 for v in ge1000), len(ge1000)),
        "base20": _share(twenty, twenty + ten),
        "base20_n": twenty + ten,
        "mult400": _share(sum(v % 400 == 0 for v in h400), len(h400)),
        "mult400_n": len(h400),
        "fav_bible": _share(sum(v in (7, 12, 40) for v in vals), m),
        "fav_meso": _share(sum(v in (13, 20, 52) for v in vals), m),
        "each_favoured": {str(f): sum(v == f for v in vals) for f in (7, 12, 40, 13, 20, 52)},
        "ordinal": _share(sum(k.startswith("ordinal") for _, k, _ in nums), n),
        "unit_year": _share(sum(u == "year" for _, _, u in nums), n),
        "unit_time": _share(sum(u == "time" for _, _, u in nums), n),
        "unit_people": _share(sum(u == "people" for _, _, u in nums), n),
        "unit_measure": _share(sum(u == "measure" for _, _, u in nums), n),
        "calendar": _share(sum(k == "calendar" for _, k, _ in nums), n),
        "score_form": _share(sum(k.endswith("+score") for _, k, _ in nums), n),
        "ordinal_years": sum(k.startswith("ordinal") and u == "year" for _, k, u in nums),
        "counted_years": sum(k.startswith("cardinal") and u == "year" for _, k, u in nums),
        "calendar_years": sum(k == "calendar" for _, k, _ in nums),
        "ordinal_months_days": sum(k.startswith("ordinal") and u == "time" for _, k, u in nums),
    }


def parts(nums: list, cfg: dict) -> list[list]:
    """Consecutive parts of ``part_numbers`` numbers; a short tail joins the last part."""
    n = cfg["lab"]["numbers"]
    size = n["part_numbers"]
    if len(nums) < n["min_part"]:
        return []
    cut = [nums[i : i + size] for i in range(0, len(nums), size)]
    if len(cut) > 1 and len(cut[-1]) < n["min_part"]:
        cut[-2:] = [cut[-2] + cut[-1]]
    return cut


def nearest(part: dict, centres: dict[str, dict], scale: dict, feats: tuple) -> str | None:
    """The tradition whose centre is nearest in mean squared scaled difference."""
    best = None
    for name, centre in centres.items():
        d = [
            ((part[f] - centre[f]) / scale[f]) ** 2
            for f in feats
            if part[f] is not None and centre.get(f) is not None and scale.get(f)
        ]
        if d and (best is None or sum(d) / len(d) < best[0]):
            best = (sum(d) / len(d), name)
    return best[1] if best else None


def fitted(texts: list[dict], cfg: dict, feats: tuple) -> tuple[dict, dict]:
    """Tradition centres (mean of whole-text profiles) and each measure's spread over parts."""
    centres: dict[str, dict] = {}
    for trad in sorted({t["tradition"] for t in texts}):
        own = [t["profile"] for t in texts if t["tradition"] == trad]
        centres[trad] = {}
        for f in feats:
            xs = [p[f] for p in own if p[f] is not None]
            centres[trad][f] = sum(xs) / len(xs) if xs else None
    scale = {}
    for f in feats:
        xs = [p[f] for t in texts for p in t["part_profiles"] if p[f] is not None]
        scale[f] = statistics.pstdev(xs) if len(xs) > 1 else 0.0
    return centres, scale


def held_out(texts: list[dict], cfg: dict, feats: tuple) -> dict:
    """Each text held out whole; its parts placed by centres built from the other texts."""
    n = cfg["lab"]["numbers"]
    by: dict[str, list[int]] = {}
    rows = []
    for t in texts:
        if not t["part_profiles"]:
            continue
        centres, scale = fitted([o for o in texts if o is not t], cfg, feats)
        got = [nearest(p, centres, scale, feats) for p in t["part_profiles"]]
        hit = sum(g == t["tradition"] for g in got)
        c = by.setdefault(t["tradition"], [0, 0])
        c[0], c[1] = c[0] + hit, c[1] + len(got)
        rows.append({"text": t["name"], "tradition": t["tradition"], "parts": len(got),
                     "placed": {g: got.count(g) for g in sorted(set(map(str, got)))}})  # fmt: skip
    rates = {k: round(h / m, 4) for k, (h, m) in by.items()}
    mean = round(sum(rates.values()) / len(rates), 4) if rates else 0.0
    passed = len(rates) == 3 and mean >= n["classifier_bar"]
    passed = passed and min(rates.values()) >= n["tradition_bar"]
    return {"by_tradition": {k: [*by[k], rates[k]] for k in by}, "hit_rate": mean,
            "passed": passed, "texts": rows}  # fmt: skip


def difference(a: tuple[int, int], b: tuple[int, int], cfg: dict) -> dict:
    """Base-twenty share of ``a`` minus that of ``b``, with a bootstrap 95% interval."""
    n = cfg["lab"]["numbers"]
    na, nb = sum(a), sum(b)
    if min(na, nb) < n["base20_min_n"]:
        return {"n": [na, nb], "enough": False, "above": False}
    rng = random.Random(n["seed"])
    pa, pb = a[0] / na, b[0] / nb
    draws = sorted(
        sum(rng.random() < pa for _ in range(na)) / na
        - sum(rng.random() < pb for _ in range(nb)) / nb
        for _ in range(n["bootstrap"])
    )
    lo, hi = draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1]
    return {"n": [na, nb], "enough": True, "shares": [round(pa, 4), round(pb, 4)],
            "difference": round(pa - pb, 4), "interval": [round(lo, 4), round(hi, 4)],
            "above": lo > 0}  # fmt: skip


# --------------------------------------------------------------------------------- the texts

FUNCTION = set(
    "the of and to in a was that he they it is were his their for with as by this which had "
    "from on when at not our we who i my be then there here all are thy thou".split()
)


def english(text: str, share: float) -> str:
    """Paragraphs of a bilingual edition in which enough of the words are English."""
    keep = []
    for para in re.split(r"\n\s*\n", text):
        words = re.findall(r"[a-z]+", para.lower())
        if len(words) >= 5 and sum(w in FUNCTION for w in words) / len(words) >= share:
            keep.append(para)
    return "\n\n".join(keep)


def between(text: str, start: str, stop: str, indented: bool = False) -> str:
    """Lines after a line matching ``start`` up to one matching ``stop`` (toggling)."""
    on, kept = False, []
    for line in text.split("\n"):
        s = line.strip()
        if re.fullmatch(stop, s):
            on = False
        elif re.fullmatch(start, s):
            on = True
        elif on and (not indented or not s or line.startswith("     ")):
            kept.append(line)
    return "\n".join(kept)


def gutenberg(text: str) -> str:
    a = re.search(r"\*\*\* ?START OF.*?\*\*\*", text)
    b = re.search(r"\*\*\* ?END OF", text)
    return text[a.end() if a else 0 : b.start() if b else len(text)]


def _file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None  # missing or unreadable: not attempted, never a result


def _kjv(section: str) -> str | None:
    raw = _file(KJV)
    if raw is None:
        return None
    rows = (json.loads(line) for line in raw.splitlines())
    return "\n".join(r["text"] for r in rows if r["section"] == section)


def _bilingual(name: str, start: str, stop: str, cfg: dict, indented: bool = False):
    raw = _file(SRC / "setting" / name)
    if raw is None:
        return None
    return english(
        between(gutenberg(raw), start, stop, indented), cfg["lab"]["numbers"]["english_share"]
    )


def _josephus(name: str) -> str | None:
    raw = _file(SRC / "names" / name)
    return None if raw is None else gutenberg(raw)


def _pdf(path: Path) -> str | None:
    if not path.exists():
        return None
    got = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True)
    return got.stdout if got.returncode == 0 and got.stdout.strip() else None


def modern_sample(cfg: dict) -> list[dict]:
    n = cfg["lab"]["numbers"]
    rows = [
        r
        for r in registry.load().to_pylist()
        if r["kind"] == "work"
        and r["has_text"]
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["genre"] in n["modern_genres"]
        and r["year"]
        and n["year_min"] <= r["year"] <= n["year_max"]
        and n["min_words"] <= (r["words"] or 0) <= n["max_words"]
    ]
    rows.sort(key=lambda r: r["work_id"])
    random.Random(n["seed"]).shuffle(rows)
    cat = door.catalog({r["work_id"] for r in rows[: n["modern_sample"] * 4]})
    picked = [{**cat[r["work_id"]], **r} for r in rows[: n["modern_sample"] * 4]
              if cat.get(r["work_id"], {}).get("text_path")]  # fmt: skip
    return picked[: n["modern_sample"]]


def _library(row: dict) -> str | None:
    try:
        return door.text_of(row)
    except OSError:
        return None


def tradition_texts(cfg: dict) -> list[tuple[str, str, str | None]]:
    """(name, tradition, text or None) for every text of the three traditions."""
    near, meso, modern = "near_east", "mesoamerica", "modern"
    spence = _file(SRC / "setting" / "popol_vuh_spence_1908.txt")
    pdfs = sorted(CHRISTENSON.glob("*hristenson*.pdf")) if CHRISTENSON.is_dir() else []
    rows = [
        ("kjv_old_testament", near, _kjv("OT")),
        ("kjv_new_testament", near, _kjv("NT")),
        ("kjv_apocrypha", near, _kjv("Apocrypha")),
        ("josephus_antiquities_whiston", near, _josephus("josephus_antiquities_whiston.txt")),
        ("josephus_wars_whiston", near, _josephus("josephus_wars_whiston.txt")),
        ("brinton_maya_chronicles_1882", meso, _bilingual(
            "brinton_maya_chronicles_1882.txt", r"TRANSLATION\.|CONQUEST AND MAP\.",
            r"NOTES\.|VOCABULARY\.", cfg)),
        ("brinton_annals_cakchiquels_1885", meso, _bilingual(
            "brinton_annals_cakchiquels_1885.txt", r"THE ANNALS", r"NOTES\.|VOCABULARY\.", cfg,
            indented=True)),
        ("brinton_rig_veda_americanus_1890", meso, _bilingual(
            "brinton_rig_veda_americanus_1890.txt",
            r"_Translation\._|_(The )?(Hymn|War Song|Song) .*\._", r"_Notes\._|GLOSSARY\.", cfg)),
        ("popol_vuh_spence_1908", meso, None if spence is None else gutenberg(spence)),
        ("popol_vuh_christenson", meso, _pdf(pdfs[0]) if pdfs else None),
        ("ss-manuscript-story-1885", modern, _file(CAND / "ss-manuscript-story-1885.txt")),
        ("gh-1816-late-war", modern, _file(CAND / "gh-1816-late-war.txt")),
        ("es-1825-view-of-the-hebrews", modern, _file(CAND / "es-1825-view-of-the-hebrews.txt")),
    ]  # fmt: skip
    rows += [(r["work_id"], modern, _library(r)) for r in modern_sample(cfg)]
    return rows


def measured(name: str, tradition: str | None, text: str, cfg: dict) -> dict:
    nums = numbers(text, cfg)
    return {
        "name": name,
        "tradition": tradition,
        "words": len(re.findall(r"[a-z]+", text.lower())),
        "profile": profile(nums, cfg),
        "part_profiles": [profile(p, cfg) for p in parts(nums, cfg)],
        "base20_counts": list(base20_counts(nums, cfg)),
    }


def traditions(cfg: dict) -> tuple[list[dict], list[str]]:
    texts, missing = [], []
    for name, trad, text in tradition_texts(cfg):
        if text is None:
            missing.append(name)
        else:
            texts.append(measured(name, trad, text, cfg))
    return texts, missing


def pooled(texts: list[dict], tradition: str) -> tuple[int, int]:
    own = [t["base20_counts"] for t in texts if t["tradition"] == tradition]
    return sum(c[0] for c in own), sum(c[1] for c in own)


def check(cfg: dict) -> dict:
    """Known answers: held-out texts land with their tradition; base twenty shows in Mesoamerica."""
    texts, missing = traditions(cfg)
    meso = pooled(texts, "mesoamerica")
    against = {t: difference(meso, pooled(texts, t), cfg) for t in ("near_east", "modern")}
    return {
        "texts": texts,
        "not_attempted": missing,
        "classifier": held_out(texts, cfg, FEATURES),
        "classifier_counting_measures_only": held_out(texts, cfg, COUNTING),
        "base20": {
            "pooled": {t: list(pooled(texts, t)) for t in ("near_east", "mesoamerica", "modern")},
            "mesoamerica_against": against,
            "detectable": all(d["above"] for d in against.values()),
        },
    }


def bom_text(drop_quotes: bool) -> str:
    labels = {r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines())}
    keep = []
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if r["kind"] != "body" or lab is None:
            continue
        if drop_quotes and (r["book"], lab["chapter_1830"]) in QUOTED:
            continue
        keep.append(r["text"])
    return "\n".join(keep)


def placed(row: dict, texts: list[dict], cfg: dict) -> dict:
    """Where a scored text's parts and whole profile land, and its base-twenty measure."""
    n = cfg["lab"]["numbers"]
    res = {}
    for label, feats in (("full_profile", FEATURES), ("counting_measures_only", COUNTING)):
        centres, scale = fitted(texts, cfg, feats)
        got = [nearest(p, centres, scale, feats) for p in row["part_profiles"]]
        count = {g: got.count(g) for g in sorted(set(map(str, got)))}
        top = max(count, key=count.get) if count else None
        res[label] = {
            "parts": len(got),
            "placed": count,
            "whole_text": nearest(row["profile"], centres, scale, feats),
            "sits_with": top if top and count[top] / len(got) >= n["bom_share"] else "mixed",
        }
    own = tuple(row["base20_counts"])
    res["base20_against"] = {
        t: difference(own, pooled(texts, t), cfg) for t in ("near_east", "modern", "mesoamerica")
    }
    res["base20_beyond_controls"] = all(
        res["base20_against"][t]["above"] for t in ("near_east", "modern")
    )
    return res


# ----------------------------------------------------------------------------------- Alma 11

# Values of the pieces as the 1830 text states them (Alma, 1830 chapter 8), in senines.
ALMA = {
    "senine": "1", "seon": "2", "shum": "4", "limnah": "7",
    "senum": "1", "amnor": "2", "ezrom": "4", "onti": "7",
    "shiblon": "1/2", "shiblum": "1/4", "leah": "1/8", "antion": "3/2",
}  # fmt: skip
# Each statement of value, as a pattern over the 1830 wording (its spellings: amner, shublons).
ALMA_STATED = {
    "senum = senine": r"senum of silver was equal to a senine of gold",
    "seon = 2 senines": r"seon of gold,? was twice the value of a senine",
    "shum = 2 seons": r"shum of gold was twice the value of a seon",
    "limnah = all of them": r"limnah of gold was the value of them all",
    "amnor = 2 senums": r"am[nm][eo]r of silver was as great as two senums",
    "ezrom = 4 senums": r"ezrom of silver was as great as four senums",
    "onti = all of them": r"onti was as great as them all",
    "shiblon = 1/2 senum": r"shiblon is half of a senum",
    "shiblum = 1/2 shiblon": r"shiblum is a half of (a )?shiblon",
    "leah = 1/2 shiblum": r"leah is the half of a shiblum",
    "antion = 3 shiblons": r"antion of gold is equal to three sh[iu]blons",
}

# FROM MEMORY, UNVERIFIED: every system below was written down without a source in hand, so
# units may be missing or wrong. Values are in the system's own smallest listed unit (or a middle
# one); only the ratios matter. Part 2 is a pilot until each entry carries a citation.
CATALOGUE = {
    "us_coins_1820s": ("united_states_1820s", {
        "half cent": "1/2", "cent": "1", "half dime": "5", "dime": "10", "quarter": "25",
        "half dollar": "50", "dollar": "100", "quarter eagle": "250", "half eagle": "500",
        "eagle": "1000"}, "coins of the 1792 Mint Act"),
    "spanish_reales": ("united_states_1820s", {
        "quarter real": "1/4", "half real": "1/2", "real": "1", "two reales": "2",
        "four reales": "4", "piece of eight": "8", "escudo": "16", "two escudos": "32",
        "four escudos": "64", "doubloon (eight escudos)": "128"},
        "Spanish silver and gold, legal tender in the United States until 1857"),
    "british_sterling": ("united_states_1820s", {
        "farthing": "1/4", "halfpenny": "1/2", "penny": "1", "sixpence": "6", "shilling": "12",
        "half crown": "30", "crown": "60", "half sovereign": "120", "sovereign": "240",
        "guinea": "252"}, "in pence; threepence and fourpence left out"),
    "english_dry_and_liquid_measure": ("united_states_1820s", {
        "gill": "1/4", "half pint": "1/2", "pint": "1", "quart": "2", "pottle": "4",
        "gallon": "8", "peck": "16", "bushel": "64"}, "in pints"),
    "avoirdupois": ("united_states_1820s", {
        "dram": "1/16", "ounce": "1", "pound": "16", "stone": "224", "quarter": "448",
        "hundredweight": "1792", "ton": "35840"}, "in ounces; British long hundredweight"),
    "troy": ("united_states_1820s", {
        "grain": "1", "pennyweight": "24", "ounce": "480", "pound": "5760"}, "in grains"),
    "hebrew_weights": ("near_east", {
        "gerah": "1", "quarter shekel": "5", "beka": "10", "pim": "40/3", "shekel": "20",
        "mina": "1000", "talent": "60000"}, "in gerahs; mina of 50 shekels (Ezekiel gives 60)"),
    "hebrew_capacity": ("near_east", {
        "log": "1", "kab": "4", "omer": "36/5", "seah": "24", "ephah": "72", "homer": "720"},
        "in logs"),
    "egyptian_deben": ("near_east", {"qedet": "1", "deben": "10"}, "New Kingdom"),
    "egyptian_grain_horus_eye": ("near_east", {
        "1/64 heqat": "1/64", "1/32 heqat": "1/32", "1/16 heqat": "1/16", "1/8 heqat": "1/8",
        "1/4 heqat": "1/4", "1/2 heqat": "1/2", "heqat": "1", "oipe": "4", "khar": "16"},
        "in heqats; khar of 16 heqats (earlier 10 or 20)"),
    "mesopotamian_weights": ("near_east", {
        "grain": "1", "shekel": "180", "mina": "10800", "talent": "648000"}, "in grains"),
    "mesopotamian_capacity": ("near_east", {
        "sila": "1", "ban": "10", "bariga": "60", "gur": "300"}, "in sila; Old Babylonian gur"),
    "greek_attic": ("near_east", {
        "chalkous": "1/8", "obol": "1", "drachma": "6", "didrachm": "12", "tetradrachm": "24",
        "mina": "600", "talent": "36000"}, "in obols; Mediterranean, grouped with the Near East"),
    "roman_coins": ("near_east", {
        "quadrans": "1/4", "semis": "1/2", "as": "1", "dupondius": "2", "sestertius": "4",
        "quinarius": "8", "denarius": "16", "aureus": "400"},
        "in asses, early Empire; Mediterranean, grouped with the Near East"),
    "roman_weights": ("near_east", {
        "scruple": "1/24", "sicilicus": "1/4", "semuncia": "1/2", "uncia": "1", "sextans": "2",
        "quadrans": "3", "triens": "4", "quincunx": "5", "semis": "6", "septunx": "7",
        "bes": "8", "dodrans": "9", "dextans": "10", "deunx": "11", "libra": "12"},
        "in ounces; Mediterranean, grouped with the Near East"),
    "indus_weights": ("near_east", {
        "1": "1", "2": "2", "4": "4", "8": "8", "16": "16", "32": "32", "64": "64",
        "160": "160", "320": "320", "640": "640"},
        "Harappan cubical weights, unnamed; South Asia, grouped with the ancient Old World"),
    "mesoamerican_cacao_counts": ("mesoamerica", {
        "cacao bean": "1", "twenty": "20", "tzontli": "400", "xiquipilli": "8000",
        "load (three xiquipilli)": "24000"}, "Aztec counts of cacao beans; base twenty"),
    "aztec_quachtli": ("mesoamerica", {
        "cacao bean": "1", "small mantle": "65", "mantle": "80", "fine mantle": "100",
        "twenty mantles": "2000"}, "cotton mantles priced in cacao; the prices are least sure"),
}  # fmt: skip


def values(units: dict[str, str]) -> set[Fraction]:
    return {Fraction(v) for v in units.values()}


def fit(a: set[Fraction], s: set[Fraction]) -> tuple[Fraction, int]:
    """Best alignment by one scale: (values in common / values in either, values in common)."""
    best = max(len({x * (y / z) for x in a} & s) for y in s for z in a)
    return Fraction(best, len(a) + len(s) - best), best


def best_fit(a: set[Fraction], catalogue: dict[str, set[Fraction]]) -> Fraction:
    return max(fit(a, s)[0] for s in catalogue.values())


def catalogue_steps(catalogue: dict[str, set[Fraction]]) -> list[Fraction]:
    """Every step between neighbouring units in the catalogue (repeats kept)."""
    steps = []
    for s in catalogue.values():
        xs = sorted(s)
        steps += [b / a for a, b in zip(xs, xs[1:], strict=False)]
    return steps


def free_steps(top: int) -> list[Fraction]:
    fr = {Fraction(p, q) for p in range(1, top + 1) for q in range(1, top + 1)}
    return sorted(f for f in fr if 1 < f <= top)


def random_system(rng: random.Random, steps: list[Fraction], size: int) -> set[Fraction]:
    vals, x = {Fraction(1)}, Fraction(1)
    for _ in range(size - 1):
        x *= rng.choice(steps)
        vals.add(x)
    return vals


def alma(cfg: dict) -> dict:
    n = cfg["lab"]["numbers"]
    body = " ".join(
        r["text"] for r in map(json.loads, EDITION.read_text().splitlines())
        if r["kind"] == "body" and r["book"] == "Alma"
    )  # fmt: skip
    stated = {k: bool(re.search(p, " ".join(body.split()))) for k, p in ALMA_STATED.items()}
    a = values(ALMA)
    cat = {k: values(u) for k, (_, u, _) in CATALOGUE.items()}
    rows = []
    for name, s in cat.items():
        score, common = fit(a, s)
        rows.append({"system": name, "setting": CATALOGUE[name][0], "units": len(s),
                     "in_common": common, "forward": round(common / len(a), 4),
                     "reverse": round(common / len(s), 4), "score": round(float(score), 4),
                     "note": CATALOGUE[name][2]})  # fmt: skip
    rows.sort(key=lambda r: -r["score"])
    top = best_fit(a, cat)
    most = max(r["in_common"] for r in rows)
    res = {
        "status": "pilot: the catalogue was written from memory and is unverified",
        "alma_values": sorted(str(v) for v in a),
        "alma_units": ALMA,
        "stated_in_1830_text": stated,
        "all_stated": all(stated.values()),
        "fits": rows,
        "best_score": round(float(top), 4),
        "best_by_setting": {
            s: max(r["score"] for r in rows if r["setting"] == s)
            for s in sorted({r["setting"] for r in rows})
        },
        "baseline": {},
    }
    for rule, steps in (("A_catalogue_steps", catalogue_steps(cat)),
                        ("B_free_small_ratios", free_steps(n["free_max"]))):  # fmt: skip
        rng, as_good, as_many, tried = random.Random(n["seed"]), 0, 0, 0
        while tried < n["random_systems"]:
            r = random_system(rng, steps, len(a))
            if len(r) != len(a):
                continue  # a repeated value: draw again
            tried += 1
            fits = [fit(r, s) for s in cat.values()]
            as_good += max(f[0] for f in fits) >= top
            as_many += max(f[1] for f in fits) >= most
        res["baseline"][rule] = {
            "random_systems": tried,
            "fit_as_well": as_good,
            "share": round(as_good / tried, 4),
            "share_with_as_many_values_in_common": round(as_many / tried, 4),
        }
    share = res["baseline"]["A_catalogue_steps"]["share"]
    res["closer_than_a_made_up_system"] = share < n["unusual_share"]
    return res


# ----------------------------------------------------------------------------------- running


def run(cfg: dict) -> dict:
    """Both checks, then only what each check allows: placement needs the classifier check to
    pass; the base-twenty comparison needs base twenty to show in the Mesoamerican texts."""
    n = cfg["lab"]["numbers"]
    chk = check(cfg)
    texts = chk.pop("texts")
    res = {"known_answer": chk, "settings": n, "texts": texts}
    res["feature_order"] = list(FEATURES)
    res["counting_measures"] = list(COUNTING)
    res["alma_11"] = alma(cfg)
    placing, base20 = chk["classifier"]["passed"], chk["base20"]["detectable"]
    if not placing:
        res["profile_not_scored"] = (
            "the held-out-text check missed its bar; the Book of Mormon's number profile was "
            "not computed or placed"
        )
    scored = {"book_of_mormon": bom_text(False),
              "book_of_mormon_without_quoted_chapters": bom_text(True)}  # fmt: skip
    cat = door.catalog(set(n["clavigero"]))
    clav = [_library(cat[i]) if i in cat else None for i in n["clavigero"]]
    if all(c is not None for c in clav):
        scored["clavigero_history_of_mexico_1787"] = "\n".join(clav)
    else:
        res["known_answer"]["not_attempted"].append("clavigero_history_of_mexico_1787")
    res["scored"] = {}
    for name, text in scored.items():
        row = measured(name, None, text, cfg)
        where = placed(row, texts, cfg)
        keep = {"name": name, "words": row["words"], "numbers": row["profile"]["n"]}
        if placing:
            keep.update(profile=row["profile"], full_profile=where["full_profile"],
                        counting_measures_only=where["counting_measures_only"])  # fmt: skip
        keep["base20_counts"] = row["base20_counts"]
        keep["base20"] = row["profile"]["base20"]
        keep["base20_against"] = where["base20_against"]
        keep["base20_beyond_controls"] = (
            where["base20_beyond_controls"] if base20 else "uninformative"
        )
        res["scored"][name] = keep
    for t in texts:
        t["parts"] = len(t.pop("part_profiles"))
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "check":
        chk = check(cfg)
        for t in chk.pop("texts"):
            p = t["profile"]
            print(t["tradition"], t["name"], t["words"], p["n"], len(t["part_profiles"]),
                  {f: p[f] for f in FEATURES}, p["base20_n"])  # fmt: skip
        print(json.dumps(chk, indent=1))
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k not in ("texts", "settings")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
