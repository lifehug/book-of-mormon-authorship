"""BOM-113: Roper's own item list, keyed from the held chapters (used by ``lab.anachronisms``).

Matthew Roper, "Anachronisms: Accidental Evidence in Book of Mormon Criticisms", *Interpreter*
65 (2025): an Introduction (pp. 1-8) and nine chapters (pp. 9-280), each a PDF fetched by
``python -m lab.sources fetch roper2025_anachronisms*.pdf`` into the private papers folder.

What is machine-read from the PDFs (``pdftotext -layout``): every item heading ("N. Label"), its
"Status:" line (confirmed / partially confirmed / unconfirmed, the era named in brackets, and any
"Loan Shift" note), its page (from the running heads), and the years named in its "Critics'
Claim" paragraph. What is **keyed by hand by the AI from images**: chapter 9's figures 64-67
(lists of items by era, which are pictures with no text layer), which give the era an item was
first raised and its status at 1844 and at 1965. The match of each figure label to an item
number is the AI's reading, listed below so it can be checked. What is the AI's own choice,
written before any count: the category of each item and the word forms ("things") counted for
it; and a rule that reads the kind of confirmation from Roper's own heading and status words.
No passage of the paper is copied into public files: labels are Roper's short headings.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

PAPERS = Path("data/private/lab/sources/papers")
CHAPTERS = {
    1: "Book of Mormon Animals", 2: "Warfare in the Book of Mormon", 3: "Metals and Metallurgy",
    4: "Ancient Culture", 5: "Book of Mormon Names", 6: "Old World Journeys by Land and Sea",
    7: "Records, Writing, and Language", 8: "Events in Third Nephi",
}  # fmt: skip
HELD_SOURCE = {
    "citation": "Matthew Roper, 'Anachronisms: Accidental Evidence in Book of Mormon Criticisms', "
    "Interpreter: A Journal of Latter-day Saint Faith and Scholarship 65 (2025): Introduction "
    "1-8, chapters 1-9 pp. 9-280",
    "addresses": ["https://cdn.interpreterfoundation.org/jnlpdf/roper-v65-2025-1-8-PDF.pdf"]
    + [
        f"https://cdn.interpreterfoundation.org/jnlpdf/roper-v65-2025-{r}-PDF.pdf"
        for r in (
            "9-50",
            "51-92",
            "93-112",
            "113-152",
            "153-180",
            "181-202",
            "203-222",
            "223-238",
            "239-280",
        )
    ],
    "held_as": "data/private/lab/sources/papers/roper2025_anachronisms*.pdf (private copies)",
    "terms": "CC BY-NC-ND 4.0",
}
STATED = {  # Roper, chapter 9, pp. 239-240 and figures 64, 66, 68 (confirmed, partial, unconfirmed)
    "1830-1844": {"confirmed": 7, "partial": 2, "unconfirmed": 93, "total": 102},
    "1845-1965": {"confirmed": 36, "partial": 10, "unconfirmed": 122, "total": 168},
    "1966-2024": {"confirmed": 174, "partial": 31, "unconfirmed": 21, "total": 226},
}  # fmt: skip

# ---- figures 64-67, keyed by hand by the AI from the images (item numbers as in the headings)
FIG_1844 = {  # figures 64 and 65: items listed for 1830-1844, by status shown
    "confirmed": [96, 97, 200, 211, 22, 23, 133],
    "partial": [196, 195],
    "unconfirmed": [1, 5, 8, 10, 4, 7, 11, 9, 13, 14, 29, 53, 33, 35, 38, 41, 42, 43, 47, 54, 55,
                    56, 59, 60, 66, 68, 76, 78, 80, 81, 85, 88, 87, 89, 91, 92, 98, 104, 71, 105,
                    95, 106, 109, 124, 134, 135, 138, 139, 140, 142, 143, 144, 145, 146, 147, 148,
                    149, 150, 151, 152, 154, 155, 158, 172, 173, 176, 178, 181, 175, 182, 183,
                    192, 190, 193, 194, 197, 199, 210, 212, 213, 214, 215, 216, 219, 220, 221,
                    222, 223, 224, 225, 226, 227],
}  # fmt: skip
FIG_1965 = {  # figures 66 and 67: items listed for 1845-1965 (cumulative), by status shown
    "confirmed": [2, 3, 1, 8, 10, 11, 17, 18, 21, 22, 23, 20, 12, 13, 14, 28, 72, 84, 96, 97, 105,
                  109, 156, 172, 173, 180, 181, 133, 175, 182, 196, 197, 200, 201, 210, 211],
    "partial": [73, 74, 79, 110, 91, 138, 155, 174, 183, 195],
    "unconfirmed": [5, 6, 7, 11, 9, 19, 15, 12, 20, 16, 29, 32, 33, 35, 36, 38, 37, 41, 42, 43,
                    45, 47, 54, 55, 56, 59, 60, 30, 31, 48, 49, 51, 52, 53, 58, 66, 67, 68, 76,
                    71, 75, 78, 81, 82, 85, 86, 88, 87, 89, 90, 92, 93, 98, 104, 95, 106, 108,
                    112, 113, 115, 116, 124, 134, 135, 139, 140, 142, 143, 144, 145, 146, 147,
                    148, 149, 150, 151, 152, 153, 154, 158, 160, 165, 166, 167, 168, 169, 170,
                    171, 176, 179, 177, 178, 186, 187, 191, 192, 190, 193, 194, 198, 199, 202,
                    203, 205, 206, 208, 209, 212, 213, 214, 215, 216, 217, 219, 220, 221, 222,
                    223, 224, 225, 227],
}  # fmt: skip
FIG_NOTES = {
    68: "figure 65 prints 'Steel (CW)'; read as item 68, Steel (OW)",
    33: "figures print 'Swords (NW)'; read as item 33, Pre-Columbian Swords",
    212: "figures print 'Destruction account implausible'; read as item 212",
    191: "figure 67 prints 'Ocean route'; read as item 191, Pacific Ocean Crossing",
    206: "figure 67 prints 'Hebrew transcription (NW)'; read as item 206, Hebrew Inscriptions (NW)",
}

# ---- the AI's choices, written before any count: categories and counted things
CATEGORY_OVERRIDES = {
    **{n: "plant" for n in (114, 115, 116, 117, 118, 119)},
    **{n: "textile" for n in (112, 113, 126)},
    **{n: "technology" for n in (104, 108, 110, 121, 122, 124, 125, 127, 128, 129, 130, 131,
                                 132, 135, 188)},
    **{n: "other" for n in (111, 120, 123, 134)},
}  # fmt: skip
CHAPTER_CATEGORY = {1: "animal", 2: "warfare", 3: "metal", 4: "custom", 5: "name", 6: "other",
                    7: "writing", 8: "other"}  # fmt: skip

# thing: (forms, plural, guard). A thing is a word group; several items may share one.
THINGS = {
    "horse": (["horse"], True, False), "ass": (["ass", "asses"], False, False),
    "cow": (["cow", "kine"], True, False), "ox": (["ox", "oxen"], False, False),
    "cattle": (["cattle"], False, False), "goat": (["goat"], True, False),
    "sheep": (["sheep"], False, False), "flock_herd": (["flock", "herd"], True, False),
    "elephant": (["elephant"], True, False), "swine": (["swine"], False, False),
    "bee": (["bee"], True, False), "lion": (["lion"], True, False),
    "moth": (["moth"], True, False), "dragon": (["dragon"], True, False),
    "chicken": (["chicken", "hen"], True, False), "dog": (["dog"], True, False),
    "serpent": (["serpent", "snake"], True, False),
    "fortification": (["fortification", "fort"], True, False),
    "armor": (["armor", "armour"], False, False), "sword": (["sword"], True, False),
    "scimitar": (["cimeter", "scimitar", "scimetar"], True, False),
    "dagger": (["dagger"], True, False), "ax": (["ax", "axe"], True, False),
    "javelin": (["javelin"], True, False), "spear": (["spear"], True, False),
    "arrow": (["arrow"], True, False), "quiver": (["quiver"], True, False),
    "fiery_dart": (["fiery dart", "firy dart"], True, False), "sling": (["sling"], True, False),
    "shield": (["shield"], True, False), "headplate": (["headplate", "head plate"], True, False),
    "breastplate": (["breastplate", "breast plate"], True, False), "army": (["army"], True, False),
    "trumpet": (["trumpet"], True, False), "cord": (["cord"], True, False),
    "ladder": (["ladder"], True, False), "tent": (["tent"], True, False),
    "steel": (["steel"], False, False), "brass": (["brass"], False, False),
    "iron": (["iron"], False, False), "ore": (["ore"], True, False),
    "furnace": (["furnace", "forge"], True, False), "copper": (["copper"], False, False),
    "chain": (["chain"], True, False), "jew": (["jew"], True, False),
    "temple": (["temple"], True, False), "synagogue": (["synagogue"], True, False),
    "city": (["city"], True, False), "king": (["king"], True, False),
    "palace": (["palace"], True, False), "prison": (["prison"], True, False),
    "barn": (["barn"], True, False), "glass": (["glass"], False, False),
    "cement": (["cement"], True, False), "chariot": (["chariot"], True, False),
    "pearl": (["pearl"], True, False), "silk": (["silk", "silks"], False, False),
    "linen": (["linen"], True, False), "grain": (["grain"], True, False),
    "wheat": (["wheat"], False, False), "barley": (["barley"], False, False),
    "corn": (["corn"], False, False), "grape": (["grape"], True, False),
    "wine": (["wine"], True, False), "salt": (["salt"], False, False),
    "highway": (["highway"], True, False), "road": (["road"], True, False),
    "leprosy": (["leprosy", "leprous"], False, False), "machinery": (["machinery"], False, False),
    "plow": (["plow", "plough"], True, False), "sickle": (["sickle"], True, False),
    "building": (["building"], True, False), "lawyer": (["lawyer"], True, False),
    "judge": (["judge"], True, False), "land_of_jerusalem": (["land of jerusalem"], False, False),
    "wild_honey": (["wild honey"], False, False), "timber": (["timber"], False, False),
    "bellows": (["bellows", "bellowses"], False, False), "plate": (["plate"], True, False),
    "reformed_egyptian": (["reformed egyptian"], False, False),
    "tempest": (["tempest"], True, False), "whirlwind": (["whirlwind"], True, False),
    "earthquake": (["earthquake"], True, False), "darkness": (["darkness"], False, False),
    **{n: ([n], False, False) for n in (
        "sam", "josh", "gid", "giddianhi", "gadianton", "sheum", "neas", "ziff", "onidah", "com",
        "kim", "nephi", "alma", "moroni", "mormon", "deseret", "liahona", "irreantum", "shazer",
        "jarom", "jonas", "timothy", "zarahemla", "zeniff", "omni", "mosiah", "helaman",
        "ether")},
    "rameumptom": (["rameumptom", "rameumptum"], False, False),
}  # fmt: skip

ITEM_THING = {
    1: "horse", 2: "horse", 3: "horse", 4: "horse", 5: "ass", 6: "ass", 7: "ass", 8: "cow",
    9: "cow", 10: "ox", 11: "ox", 12: "cattle", 13: "goat", 14: "goat", 15: "sheep",
    16: "flock_herd", 17: "elephant", 18: "elephant", 19: "elephant", 20: "swine", 21: "bee",
    22: "lion", 24: "moth", 25: "dragon", 26: "chicken", 27: "dog", 28: "serpent",
    29: "fortification", 32: "armor", 33: "sword", 34: "sword", 35: "steel", 36: "steel",
    37: "scimitar", 38: "scimitar", 39: "dagger", 40: "ax", 41: "javelin", 42: "spear",
    43: "arrow", 44: "quiver", 45: "steel", 46: "fiery_dart", 47: "sling", 48: "shield",
    49: "shield", 50: "headplate", 51: "breastplate", 52: "breastplate", 53: "army", 54: "army",
    62: "trumpet", 63: "cord", 64: "ladder", 65: "tent", 68: "steel", 69: "brass", 71: "brass",
    72: "iron", 73: "iron", 74: "iron", 75: "iron", 76: "steel", 77: "ore", 78: "furnace",
    82: "copper", 83: "chain", 84: "jew", 91: "temple", 93: "synagogue", 94: "synagogue",
    97: "city", 99: "temple", 100: "king", 101: "palace", 102: "prison", 103: "barn",
    104: "glass", 108: "cement", 110: "chariot", 111: "pearl", 112: "silk", 113: "linen",
    114: "grain", 115: "wheat", 116: "barley", 117: "corn", 118: "grape", 119: "wine",
    120: "salt", 121: "highway", 122: "road", 123: "leprosy", 124: "machinery", 125: "ax",
    131: "plow", 132: "sickle", 133: "building", 136: "lawyer", 137: "judge", 138: "sam",
    139: "josh", 140: "gid", 141: "giddianhi", 142: "gadianton", 144: "sheum", 145: "neas",
    146: "ziff", 148: "rameumptom", 149: "onidah", 150: "com", 151: "kim", 152: "nephi",
    153: "alma", 154: "moroni", 155: "mormon", 156: "deseret", 157: "liahona", 158: "irreantum",
    159: "shazer", 160: "jarom", 161: "jonas", 162: "timothy", 165: "zarahemla", 166: "zeniff",
    167: "omni", 168: "mosiah", 169: "helaman", 170: "ether", 172: "land_of_jerusalem",
    185: "wild_honey", 186: "timber", 187: "ore", 188: "bellows", 196: "plate", 199: "plate",
    202: "reformed_egyptian", 214: "tempest", 216: "whirlwind", 217: "earthquake",
    218: "earthquake", 220: "darkness", 221: "darkness", 222: "darkness",
}  # fmt: skip

HEAD = re.compile(r"^\s*(\d+)\.\s+(\S.*)$")
STATUS = re.compile(r"^\s*Status:\s*(.+)$")
RUNNING = re.compile(r"^\s*(\d+) • Interpreter 65|Roper, Anachronisms \(Chapter \d\) • (\d+)\s*$")
PAGES = re.compile(r"Pages\s+(\d+)\D+(\d+)")
YEAR = re.compile(r"\b(18[2-9]\d|19\d\d|20[0-2]\d)\b")


def chapter_text(ch: int) -> str | None:
    p = PAPERS / f"roper2025_anachronisms_ch{ch}.pdf"
    if not p.exists():
        return None
    got = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True)
    return got.stdout if got.returncode == 0 and got.stdout.strip() else None


def status_word(s: str) -> str:
    return ("partial" if s.startswith("Partially") else
            "unconfirmed" if s.startswith("Unconfirmed") else "confirmed")  # fmt: skip


def kind_from_wording(label: str, status: str) -> str:
    """The kind of confirmation as Roper's own heading and status words state it (a rule)."""
    if "Loan Shift" in status:
        return "linguistic_reading"
    if "(OW & NW)" in label:
        return "old_and_new_world"
    if "(OW)" in label:
        return "old_world"
    if "in Book of Mormon Times" in label or label.startswith("Early Pre-Columbian"):
        return "new_world_in_period"
    if "(NW)" in label or label.startswith("Pre-Columbian") or "Mesoamerica" in label:
        return "new_world_period_unstated"
    return "not_stated"


def parse_chapter(ch: int, text: str) -> list[dict]:
    lines = text.splitlines()
    m = PAGES.search(text)
    page = int(m.group(1)) if m else None
    rows = []
    claim_for = None
    for i, line in enumerate(lines):
        r = RUNNING.search(line)
        if r:
            page = int(r.group(1) or r.group(2))
            continue
        s = STATUS.match(line)
        if s:
            j, extra = i - 1, []
            while j >= 0 and not HEAD.match(lines[j]) and i - j < 4:
                extra.insert(0, lines[j].strip())
                j -= 1
            h = HEAD.match(lines[j]) if j >= 0 else None
            label = " ".join([h.group(2).strip()] + extra).strip() if h else None
            st = s.group(1).strip()
            era = re.search(r"\((\d{4})\D+(\d{4})\)", st)
            ls = re.search(r"Confirmed (\w+) Loan Shift", st)
            rows.append({"printed_number": int(h.group(1)) if h else None, "label": label,
                         "chapter": ch, "page": page, "status": status_word(st), "status_raw": st,
                         "era_confirmed": f"{era.group(1)}-{era.group(2)}" if era else None,
                         "loan_shift": ls.group(1) if ls else None,
                         "years_named_in_claim": []})  # fmt: skip
            claim_for = rows[-1]
            continue
        if claim_for is not None:
            if line.strip().startswith("Response:"):
                claim_for = None
            else:
                claim_for["years_named_in_claim"] += [int(y) for y in YEAR.findall(line)]
    return rows


def key_items() -> dict:
    """Roper's items keyed from the chapters, with the keying check against his stated totals."""
    items, missing = [], []
    for ch in CHAPTERS:
        t = chapter_text(ch)
        if t is None:
            missing.append(ch)
            continue
        items += parse_chapter(ch, t)
    if missing:
        return {"not_attempted": f"chapters not readable: {missing}", "items": []}
    era1 = {n: s for s, ns in FIG_1844.items() for n in ns}
    era2: dict[int, str] = {}
    for s, ns in FIG_1965.items():
        for n in ns:
            era2[n] = "conflict" if n in era2 and era2[n] != s else s
    for k, it in enumerate(items, 1):
        it["number"] = k  # Roper's numbering runs on through the book (chapter 2 reprints 1-39)
        thing = ITEM_THING.get(k)
        it.update(
            id=f"roper_{k:03d}", chapter_title=CHAPTERS[it["chapter"]],
            category=CATEGORY_OVERRIDES.get(k, CHAPTER_CATEGORY[it["chapter"]]),
            thing=thing, countable=thing is not None,
            roper_status=it.pop("status"),
            roper_confirmation_kind=kind_from_wording(it["label"] or "", it.pop("status_raw")),
            era_first_raised="1830-1844" if k in era1 else "1845-1965" if k in era2
            else "1966-2024 (by elimination: absent from figures 64-67)",
            status_1844=era1.get(k), status_1965=era2.get(k),
            raised_by=None, from_memory=False,
            year_first_named_in_claim=min(it["years_named_in_claim"])
            if it["years_named_in_claim"] else None,
        )  # fmt: skip
        it.pop("years_named_in_claim")
    return {"items": items, "keying_check": keying_check(items, era1, era2)}


def keying_check(items: list[dict], era1: dict, era2: dict) -> dict:
    """Totals from the keyed list against the totals Roper states."""
    from collections import Counter

    heads = Counter(it["roper_status"] for it in items)
    fig1 = Counter(era1.values())
    fig2 = Counter(v for v in era2.values() if v != "conflict")
    numbers_ok = all(it["printed_number"] in (it["number"], it["number"] - 28) for it in items)
    res = {
        "headings_2024": {**heads, "total": len(items)},
        "stated_2024": STATED["1966-2024"],
        "figure_1844_keyed": {**fig1, "total": len(era1)},
        "stated_1844": STATED["1830-1844"],
        "figure_1965_keyed": {**fig2, "conflicts": sum(v == "conflict" for v in era2.values()),
                              "total": len(era2)},
        "stated_1965": STATED["1845-1965"],
        "printed_numbers_continuous": numbers_ok,
        "raised_by_1844_but_absent_from_1965_figure": sorted(set(era1) - set(era2)),
        "figure_notes": FIG_NOTES,
    }  # fmt: skip
    res["matches_2024"] = all(heads[k] == STATED["1966-2024"][k]
                              for k in ("confirmed", "partial", "unconfirmed")) and \
        len(items) == STATED["1966-2024"]["total"]  # fmt: skip
    res["mismatch_2024"] = {k: heads[k] - STATED["1966-2024"][k]
                            for k in ("confirmed", "partial", "unconfirmed")}  # fmt: skip
    return res
