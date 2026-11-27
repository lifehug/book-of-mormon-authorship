"""BOM-132: English words the King James Old Testament never uses to render Hebrew.

Part 1, the concordance: each text's words (lower case, names left out) that never occur in the
King James Old Testament, per 10,000 words, with the subset found in the New Testament or
Apocrypha (Bible words that came through Greek). A word counts as found when it, a regular
inflection or a spelling variant is in the Old Testament, and only words in the period word list
are counted, so OCR misreads do not raise the scanned controls (card amendment 1). The
known-answer check: every Old Testament book, scored against the Old Testament without itself,
must fall below every New Testament and Apocrypha book. Part 2, the Hebrew: eBible's
Strong's-tagged King James text, checked against the Westminster Leningrad Codex (``morphhb``),
shows for each of the book's most frequent outside words which Hebrew lemmas carry that sense in
Strong's or the abridged BDB and how the King James rendered them. Part 3: "father and mother"
against "parents", "sons and daughters" against "children". Exact counts only: no model, no AI
judging. Card, written first: ``data/private/lab/owner/2026-11-27-hebrew-vocabulary/card.md``;
settings ``lab.hebrew_vocabulary``. The output holds single words, counts, rates and Strong's
numbers, no passages.

Usage::

    python -m lab.hebrewvocab check   # known-answer check, Hebrew alignment -> .../check.json
    python -m lab.hebrewvocab run     # -> data/lab/translation/hebrew_vocabulary/result.json
    python -m lab.hebrewvocab check2  # design 2 (5,000-word blocks) check -> .../check2.json
    python -m lab.hebrewvocab run2    # design 2, book and controls if it passes -> .../result2.json
    python -m lab.hebrewvocab check3  # design 3: King James and Young's NT vs OT -> .../check3.json
    python -m lab.hebrewvocab run3    # design 3, book and controls if it passes -> .../result3.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from lab import ntwording as NT
from lab.paths import REGISTRY, out
from metadata import config

OUT = REGISTRY / "translation" / "hebrew_vocabulary"
KJV = Path("data/kjv/kjv.jsonl")
LEX = Path("data/corpus/lab/sources/wordlists/hebrew_lexicon")
WORD = re.compile(r"[a-z]+")
INFLECTIONS = ("s", "es", "ed", "d", "ing", "eth", "th", "est", "st", "edst", "est")
SPELLING = (("our", "or"), ("or", "our"), ("re", "er"), ("er", "re"), ("ise", "ize"))
SPELLING += (("ize", "ise"), ("ised", "ized"), ("ized", "ised"))


# ----------------------------------------------------------------------------- words


def tokens(text: str) -> list[str]:
    """Lower-case words; a word broken over a line end with a hyphen is joined; long s read."""
    text = re.sub(r"-\s*\n\s*", "", text.replace("ſ", "s"))
    return WORD.findall(text.lower())


def keys(w: str, min_stem: int) -> set[str]:
    """The forms under which ``w`` is looked up: itself, its inflection bases, spelling variants."""
    res = {w}
    for end in INFLECTIONS:
        if w.endswith(end) and len(w) - len(end) >= min_stem:
            b = w[: -len(end)]
            res |= {b, b + "e"}
            if len(b) >= 2 and b[-1] == b[-2]:
                res.add(b[:-1])  # smitten -> smit, cutting -> cut
            if b.endswith("i"):
                res.add(b[:-1] + "y")  # carried -> carry
    for a, z in SPELLING:
        for x in list(res):
            if x.endswith(a) and len(x) - len(a) >= min_stem:
                res.add(x[: -len(a)] + z)
    return {x for x in res if len(x) >= min_stem or x == w}


def load_lexicon(path: str) -> set[str]:
    return {line.split("\t", 1)[0] for line in Path(path).read_text().splitlines() if line}


def text_names(text: str, webster: set[str]) -> set[str]:
    """Words capitalised wherever they occur in ``text`` and not in Webster's list."""
    from lab.names import cap_counts

    cap, _mid, low = cap_counts(text.replace("ſ", "s"))
    return {w for w in cap if w not in low and w not in webster}


class Concordance:
    """The King James text by book, and which Old Testament books hold each lookup form."""

    def __init__(self, rows: list[dict], min_stem: int):
        self.min_stem = min_stem
        self.section: dict[str, str] = {}
        self.codes: list[str] = []
        self.text: dict[str, list[str]] = defaultdict(list)
        for r in rows:
            if r["book"] not in self.section:
                self.codes.append(r["book"])
                self.section[r["book"]] = r["section"]
            self.text[r["book"]].append(r["text"])
        self.words = {c: tokens("\n".join(v)) for c, v in self.text.items()}
        self.forms: dict[str, set[str]] = defaultdict(set)  # word form -> OT books
        self.keyed: dict[str, set[str]] = defaultdict(set)  # lookup form -> OT books
        self.nt_ap: set[str] = set()  # word forms of the New Testament and Apocrypha
        for c in self.codes:
            if self.section[c] == "OT":
                for w in set(self.words[c]):
                    self.forms[w].add(c)
                    for k in keys(w, min_stem):
                        self.keyed[k].add(c)
            else:
                self.nt_ap |= set(self.words[c])
        self.nt_ap_keys = {k for w in self.nt_ap for k in keys(w, min_stem)}
        self._cache: dict[tuple[str, str | None], bool] = {}

    def in_ot(self, w: str, hold: str | None = None, fold: bool = True) -> bool:
        """``w`` (or, folded, one of its lookup forms) is in an Old Testament book other than
        ``hold``."""
        if not fold:
            books = self.forms.get(w)
            return bool(books and books - {hold})
        ck = (w, hold)
        if ck not in self._cache:
            self._cache[ck] = any(self.keyed.get(k, set()) - {hold} for k in keys(w, self.min_stem))
        return self._cache[ck]

    def in_nt_ap(self, w: str, fold: bool = True) -> bool:
        if not fold:
            return w in self.nt_ap
        return bool(keys(w, self.min_stem) & self.nt_ap_keys)


def marks(
    words: list[str],
    conc: Concordance,
    names: set[str],
    lexicon: set[str] | None,
    hold: str | None = None,
    fold: bool = True,
) -> tuple[list[str], list[int]]:
    """(the words with names left out, 1 for each one outside the Old Testament, else 0)."""
    kept = [w for w in words if w not in names]
    flag = [int((lexicon is None or w in lexicon) and not conc.in_ot(w, hold, fold)) for w in kept]
    return kept, flag


def interval(flag: list[int], block: int, boot: int, seed: int) -> list[float] | None:
    """95% interval of the rate per 10,000 words, resampling blocks of ``block`` words."""
    blocks = [
        (sum(flag[i : i + block]), len(flag[i : i + block])) for i in range(0, len(flag), block)
    ]
    if len(blocks) < 2:
        return None
    rng, draws = random.Random(seed), []
    for _ in range(boot):
        pick = [rng.choice(blocks) for _ in blocks]
        draws.append(sum(a for a, _ in pick) / sum(b for _, b in pick) * 10000)
    draws.sort()
    return [round(draws[int(0.025 * boot)], 2), round(draws[int(0.975 * boot) - 1], 2)]


def score(words: list[str], conc: Concordance, names: set[str], ctx: dict, top: int = 0) -> dict:
    """Rates for one text: primary (folded, lexicon) and the two unadjusted counts beside it."""
    w = ctx["w"]
    kept, flag = marks(words, conc, names, ctx["lexicon"])
    n, k = len(kept), sum(flag)
    outside = [x for x, f in zip(kept, flag, strict=True) if f]
    greek = sum(1 for x in outside if conc.in_nt_ap(x))
    _k2, f_nofilter = marks(words, conc, names, None)
    _k3, f_raw = marks(words, conc, names, None, fold=False)
    res = {
        "words": n,
        "names_left_out": len(words) - n,
        "outside_ot": k,
        "per_10k": round(k / n * 10000, 2) if n else None,
        "ci95": interval(flag, w["block_words"], w["boot"], w["boot_seed"]),
        "in_nt_or_apocrypha_per_10k": round(greek / n * 10000, 2) if n else None,
        "distinct_outside_words": len(set(outside)),
        "no_lexicon_filter_per_10k": round(sum(f_nofilter) / n * 10000, 2) if n else None,
        "word_forms_unfolded_per_10k": round(sum(f_raw) / n * 10000, 2) if n else None,
    }
    if top:
        res["top_outside_words"] = [
            {"word": x, "count": c, "in_nt_or_apocrypha": conc.in_nt_ap(x)}
            for x, c in Counter(outside).most_common(top)
        ]
    return res


# ----------------------------------------------------------------------------- pairings


def pairings(text: str, pairs: dict) -> dict:
    t = re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", text.replace("ſ", "s")).lower())
    res = {}
    for name, (pair, coll) in pairs.items():
        p, c = len(re.findall(pair, t)), len(re.findall(coll, t))
        res[name] = {
            "pair": p,
            "collective": c,
            "collective_share": round(c / (p + c), 3) if p + c else None,
        }
    return res


# ----------------------------------------------------------------------------- texts


def read_paths(paths: list[str]) -> str | None:
    try:
        return "\n".join(Path(p).read_text(encoding="utf-8", errors="replace") for p in paths)
    except OSError:
        return None  # not attempted


def bom_texts(w124: dict) -> dict[str, str]:
    """The 1830 text's body paragraphs: pre-Christian and 3 Nephi outside the quotation chapters,
    the quotation chapters, and each pre-Christian book; plus the whole body (for its names)."""
    labels = {
        r["seq"]: r
        for r in map(json.loads, NT.LABELS.read_text().splitlines())
        if r["kind"] == "body"
    }
    parts: dict[str, list[str]] = defaultdict(list)
    for r in map(json.loads, NT.EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if lab is None:
            continue
        parts["_all"].append(r["text"])
        quoted = (r["book"], lab["chapter_1830"]) in NT.QUOTED
        tg = NT.time_group(r["book"], w124)
        if quoted:
            parts["quotation_chapters"].append(r["text"])
        elif tg in ("before", "ether"):
            parts["pre_christian_outside_quotation"].append(r["text"])
            parts[f"book:{r['book']}"].append(r["text"])
        elif tg == "visit":
            parts["3_nephi_outside_quotation"].append(r["text"])
        elif tg == "after":
            parts["after_visit_outside_quotation"].append(r["text"])
    return {k: "\n".join(v) for k, v in parts.items()}


def bom_names(cfg: dict) -> set[str]:
    """The Book of Mormon's names by BOM-108's rule (confirmed and rule-only)."""
    from lab import names as N

    english = N.english_vocabulary(cfg["lab"]["names"]["english_min_count"])
    kjv = set(N.load_kjv())
    b = N.bom_names(cfg, english, kjv)
    return set(b["coined"]) | set(b["biblical"]) | set(b["rule_only"])


def control_texts(cfg: dict) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Group -> name -> text; and what could not be read (not attempted, never zero)."""
    w = cfg["lab"]["hebrew_vocabulary"]
    named = NT.named_texts(cfg)
    missing = list(named.pop("_missing")["not_attempted"])
    groups: dict[str, dict[str, str]] = {"translations": {}, "imitations": {}}
    for name, paths in w["texts"].items():
        t = read_paths(paths)
        if t is None:
            missing.append(name)
            continue
        group = "decoys" if name in w["decoys"] else "translations"
        groups.setdefault(group, {})[name] = t
    groups["translations"].update(named["translators"])
    for name, t in named["bible_style"].items():
        groups["decoys" if name in w["decoys"] else "imitations"].setdefault(name, t)
    groups["revelations"] = named["revelations"]
    groups["book_of_moses"] = named["moses"]
    return groups, missing


def sermon_rows(cfg: dict) -> list[dict]:
    w = cfg["lab"]["hebrew_vocabulary"]
    pool = NT.eligible(
        cfg,
        lambda r: (
            w["sermon_year_min"] <= r["year"] <= w["sermon_year_max"]
            and "sermon_devotional" in (r["genre"] or "")
            and (r["words"] or 0) >= w["sermon_min_words"]
        ),
    )
    return NT.draw(pool, w["sermon_sample"], w["sermon_seed"], set())


# ----------------------------------------------------------------------------- the check


def prepare(cfg: dict) -> dict:
    from lab import names as N

    w = cfg["lab"]["hebrew_vocabulary"]
    rows = [json.loads(line) for line in KJV.read_text().splitlines()]
    conc = Concordance(rows, w["min_stem"])
    return {
        "w": w,
        "conc": conc,
        "lexicon": load_lexicon(w["lexicon"]),
        "webster": set(Path(w["name_lexicon"]).read_text().split()),
        "kjv_names": set(N.load_kjv()),
    }


def known_answer(ctx: dict) -> dict:
    """Each Old Testament book against the Old Testament without itself; each New Testament and
    Apocrypha book against the whole Old Testament. Pass: every OT book below every other."""
    conc, rows = ctx["conc"], []
    for c in conc.codes:
        hold = c if conc.section[c] == "OT" else None
        kept, flag = marks(conc.words[c], conc, ctx["kjv_names"], ctx["lexicon"], hold)
        _k, raw = marks(conc.words[c], conc, ctx["kjv_names"], None, hold, fold=False)
        n = len(kept)
        rows.append(
            {
                "book": c,
                "section": conc.section[c],
                "words": n,
                "per_10k": round(sum(flag) / n * 10000, 2),
                "word_forms_unfolded_no_filter_per_10k": round(sum(raw) / n * 10000, 2),
            }
        )
    ot = [r for r in rows if r["section"] == "OT"]
    other = [r for r in rows if r["section"] != "OT"]
    ot_max = max(ot, key=lambda r: r["per_10k"])
    other_min = min(other, key=lambda r: r["per_10k"])
    raw_ot = max(r["word_forms_unfolded_no_filter_per_10k"] for r in ot)
    raw_other = min(r["word_forms_unfolded_no_filter_per_10k"] for r in other)
    return {
        "rule": "every Old Testament book (held out) below every New Testament and Apocrypha book",
        "ot_held_out_max": {"book": ot_max["book"], "per_10k": ot_max["per_10k"]},
        "nt_apocrypha_min": {"book": other_min["book"], "per_10k": other_min["per_10k"]},
        "passed": ot_max["per_10k"] < other_min["per_10k"],
        "overlapping_books": {
            "ot_above_lowest_other": [
                r["book"] for r in ot if r["per_10k"] >= other_min["per_10k"]
            ],
            "others_below_highest_ot": [
                r["book"] for r in other if r["per_10k"] <= ot_max["per_10k"]
            ],
        },
        "unadjusted_counts_would_pass": raw_ot < raw_other,
        "medians": {
            s: statistics.median(r["per_10k"] for r in rows if r["section"] == s)
            for s in ("OT", "NT", "Apocrypha")
        },
        "descriptive_auc_not_the_bar": {
            s: round(
                NT.auc(
                    [r["per_10k"] for r in other if r["section"] == s], [r["per_10k"] for r in ot]
                ),
                4,
            )
            for s in ("NT", "Apocrypha")
        },  # fmt: skip
        "books": rows,
    }


# ----------------------------------------------------------------------------- part 2: Hebrew


USFM_WORD = re.compile(r'\\\+?w ([^|\\]+)\|strong="([^"]+)"\\\+?w\*')


def tagged_kjv(path: str) -> dict[tuple[str, int, int], list[tuple[str, list[str]]]]:
    """(book, chapter, verse) -> [(English word(s), [Strong's numbers])] from eBible's USFM."""
    res: dict[tuple[str, int, int], list] = {}
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".usfm"):
                continue
            book, ch, last = None, 0, None
            for line in z.read(name).decode("utf-8", "replace").splitlines():
                if line.startswith("\\id "):
                    book = line.split()[1]
                elif line.startswith("\\c "):
                    ch = int(line.split()[1])
                m = re.match(r"\\v (\d+)", line)
                if m:
                    last = (book, ch, int(m.group(1)))
                    line = re.sub(r"\\f .*?\\f\*", "", line)
                    res[last] = [(e.lower(), s.split()) for e, s in USFM_WORD.findall(line)]
                elif last and "\\w " in line:  # a verse continued on a new line
                    line = re.sub(r"\\f .*?\\f\*", "", line)
                    res[last] += [(e.lower(), s.split()) for e, s in USFM_WORD.findall(line)]
    return res


def strong_num(s: str) -> int | None:
    m = re.match(r"H0*(\d+)", s)
    return int(m.group(1)) if m else None


def wlc_lemmas() -> dict[str, set[int]]:
    """King James reference "GEN.1.1" -> Strong's numbers of the Hebrew verse (verse map applied;
    verses mapped only in part are left out)."""
    from lab import translation2 as T2

    full, partial = T2.verse_map()
    res: dict[str, set[int]] = {}
    for osis, ws in T2.hebrew_verses().items():
        if osis in partial:
            continue
        ref = full.get(osis, osis)
        b, c, v = ref.split(".")
        key = f"{T2.KJV_CODE[b]}.{c}.{v}"
        nums = set()
        for lemma, _m in ws:
            for part in lemma.split("/"):
                m = re.match(r"\s*(\d+)", part)
                if m:
                    nums.add(int(m.group(1)))
        res.setdefault(key, set()).update(nums)
    return res


def alignment(tagged: dict, heb: dict[str, set[int]]) -> dict:
    """Share of the tagged King James's Hebrew numbers found among the WLC verse's lemmas."""
    found = total = verses = 0
    for (b, c, v), words in tagged.items():
        key = f"{b}.{c}.{v}"
        if key not in heb:
            continue
        verses += 1
        for _e, nums in words:
            for s in nums:
                n = strong_num(s)
                if n is not None:
                    total += 1
                    found += n in heb[key]
    return {"verses": verses, "tags": total, "found_in_wlc_verse": found,
            "share": round(found / total, 4) if total else None}  # fmt: skip


def renderings(tagged: dict) -> dict[int, Counter]:
    """Strong's Hebrew number -> Counter of the English words the King James tagged with it."""
    res: dict[int, Counter] = defaultdict(Counter)
    for _k, words in tagged.items():
        for e, nums in words:
            for s in nums:
                n = strong_num(s)
                if n is not None:
                    res[n][e] += 1
    return res


def lexicon_glosses() -> dict[int, dict[str, str]]:
    """Strong's number -> {"strong": meaning and usage, "bdb": definitions and senses}."""
    res: dict[int, dict[str, str]] = defaultdict(lambda: {"strong": "", "bdb": "", "pos": ""})
    text = (LEX / "HebrewStrong.xml").read_text(encoding="utf-8")
    for m in re.finditer(r'<entry id="H(\d+)">(.*?)</entry>', text, re.S):
        body = m.group(2)
        pos = re.search(r'<w pos="([^"]*)"', body)
        # Strong's own glosses (<def>) and King James usage; not the commentary around them,
        # which made words such as "perhaps" match dozens of entries (design 3, 2026-11-27).
        meaning = " ".join(re.findall(r"<meaning>(.*?)</meaning>", body, re.S))
        parts = re.findall(r"<def>(.*?)</def>", meaning) + re.findall(
            r"<usage>(.*?)</usage>", body, re.S
        )
        res[int(m.group(1))]["strong"] = " ".join(re.sub(r"<[^>]+>", " ", p) for p in parts)
        res[int(m.group(1))]["pos"] = pos.group(1) if pos else ""
    idx = (LEX / "LexicalIndex.xml").read_text(encoding="utf-8")
    bdb_of: dict[str, set[int]] = defaultdict(set)
    for m in re.finditer(r'<xref bdb="([^"]+)" strong="(\d+)"', idx):
        bdb_of[m.group(1)].add(int(m.group(2)))
    bdb = (LEX / "BrownDriverBriggs.xml").read_text(encoding="utf-8")
    for m in re.finditer(r'<entry id="([^"]+)"[^>]*>(.*?)</entry>', bdb, re.S):
        nums = bdb_of.get(m.group(1))
        if not nums:
            continue
        defs = re.findall(r"<def>(.*?)</def>", m.group(2), re.S)
        senses = re.findall(r"<sense[^>]*>([^<]*)", m.group(2))
        g = " ".join(re.sub(r"<[^>]+>", " ", x) for x in defs + senses)
        for n in nums:
            res[n]["bdb"] += " " + g
    return res


def carriers(word: str, glosses: dict, freq: dict[int, int], min_stem: int) -> list[dict]:
    """Hebrew lemmas (not proper names) whose Strong's or BDB gloss holds ``word`` or a base."""
    forms = {word} | {k for k in keys(word, min_stem) if len(k) > 3}
    rx = re.compile(r"\b(?:" + "|".join(sorted(map(re.escape, forms))) + r")\b", re.I)
    hits = []
    for n, g in glosses.items():
        if g["pos"].startswith("n-pr"):
            continue
        where = [src for src in ("strong", "bdb") if rx.search(g[src])]
        if where:
            hits.append(
                {"strong": f"H{n}", "found_in": where, "hebrew_bible_count": freq.get(n, 0)}
            )
    return sorted(hits, key=lambda h: -h["hebrew_bible_count"])


def part2(ctx: dict, top_words: list[str]) -> dict:
    w = ctx["w"]
    tagged = tagged_kjv(w["usfm"])
    heb = wlc_lemmas()
    rend = renderings(tagged)
    glosses = lexicon_glosses()
    freq: Counter = Counter()
    for nums in heb.values():
        freq.update(nums)  # verses holding the lemma (a count of verses, not of words)
    b, c, v, eng = w["check_verse"]
    verse = tagged.get((b, int(c), int(v)), [])
    tag = next((nums for e, nums in verse if e == eng), None)
    num = strong_num(tag[0]) if tag else None
    check = {
        "verse": f"{b} {c}:{v}",
        "english": eng,
        "strong": f"H{num}" if num else None,
        "in_wlc_verse": bool(num and num in heb.get(f"{b}.{c}.{v}", set())),
        "renderings": dict(rend[num].most_common(w["renderings_per_lemma"])) if num else {},
        "gloss_mentions_parent": bool(
            num and re.search(r"\bparents?\b", glosses[num]["strong"] + glosses[num]["bdb"], re.I)
        ),
    }
    per_word = []
    for word in top_words:
        found = carriers(word, glosses, freq, w["min_stem"])
        per_word.append(
            {
                "word": word,
                "kjv_renders_hebrew_with_it": sum(
                    rend[n][word] for n in rend
                ),  # 0 by construction unless the tagged text differs from ours
                "lemmas_with_this_gloss": len(found),
                "lemmas": [
                    {
                        **h,
                        "kjv_renderings": dict(
                            rend[int(h["strong"][1:])].most_common(w["renderings_per_lemma"])
                        ),
                    }
                    for h in found[: w["lemmas_per_word"]]
                ],
            }
        )
    return {
        "alignment": alignment(tagged, heb),
        "genesis_49_26": check,
        "words": per_word,
        "note": "hebrew_bible_count is the number of verses holding the lemma",
    }


# ----------------------------------------------------------------------------- the run


def run(cfg: dict) -> dict:
    ctx = prepare(cfg)
    w = ctx["w"]
    chk = known_answer(ctx)
    res: dict = {"known_answer": chk, "settings": w}
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
        return res
    conc, pairs = ctx["conc"], w["pairs"]
    base_names = ctx["kjv_names"] | bom_names(cfg)

    def one(text: str, top: int = 0, own_names: str | None = None) -> dict:
        names = base_names | text_names(own_names or text, ctx["webster"])
        r = score(tokens(text), conc, names, ctx, top)
        r["pairings"] = pairings(text, pairs)
        return r

    bom = bom_texts(cfg["lab"]["new_testament_wording"])
    every = bom.pop("_all")
    res["book_of_mormon"] = {
        k: one(t, w["top_words"] if not k.startswith("book:") else 10, every)
        for k, t in bom.items()
    }
    kjv_sec = {
        s: "\n".join("\n".join(conc.text[c]) for c in conc.codes if conc.section[c] == s)
        for s in ("OT", "NT", "Apocrypha")
    }
    res["king_james_pairings"] = {s: pairings(t, pairs) for s, t in kjv_sec.items()}
    groups, missing = control_texts(cfg)
    res["not_attempted"] = missing
    res["controls"] = {g: {n: one(t, 15) for n, t in items.items()} for g, items in groups.items()}
    rows = sermon_rows(cfg)
    ser, unreadable, ser_pairs = {}, 0, Counter()
    for r in rows:
        try:
            text = NT.door.text_of(r)
        except OSError:
            unreadable += 1  # not attempted, never a result
            continue
        words = tokens(text)[: w["max_words_per_work"]]
        names = base_names | text_names(text, ctx["webster"])
        s = score(words, conc, names, ctx)
        s.pop("ci95")
        ser[r["work_id"]] = {"year": r["year"], **s}
        for name, p in pairings(text, pairs).items():
            ser_pairs[f"{name}_pair"] += p["pair"]
            ser_pairs[f"{name}_collective"] += p["collective"]
    res["sermons"] = {
        "works": len(ser),
        "unreadable": unreadable,
        "rates": NT.quantiles([v["per_10k"] for v in ser.values()]),
        "pairings_pooled": dict(ser_pairs),
        "by_work": ser,
    }
    res["verdict"] = verdict(res, w, chk)
    top = [
        x["word"]
        for x in res["book_of_mormon"]["pre_christian_outside_quotation"]["top_outside_words"]
    ]
    res["hebrew"] = part2(ctx, top)
    return res


def verdict(res: dict, w: dict, chk: dict) -> dict:
    bom = res["book_of_mormon"]["pre_christian_outside_quotation"]
    tr = res["controls"]["translations"]
    rate = bom["per_10k"]
    jasher = tr.get("jasher_1840", {}).get("per_10k")
    thomson = tr.get("thomson_1808_ot", {}).get("per_10k")
    josephus = tr.get(w["josephus"], {}).get("per_10k")
    ot_max = chk["ot_held_out_max"]["per_10k"]
    if None in (jasher, thomson, josephus):
        answer = "not attempted (a bar text could not be read)"
    elif (
        rate > ot_max
        and rate > jasher
        and rate > thomson
        and bom["ci95"][0] > max(ot_max, jasher, thomson)
    ):
        answer = "more"
    elif rate <= max(jasher, thomson, josephus):
        answer = "within their range"
    else:
        answer = "cannot tell"
    within_top = max(x for x in (jasher, thomson, josephus) if x is not None)
    decoys = {n: v["per_10k"] for n, v in res["controls"].get("decoys", {}).items()}
    imit = {
        n: v["per_10k"]
        for n, v in res["controls"]["imitations"].items()
        if v["words"] >= w["bible_style_min_words"]
    }
    ser = [v["per_10k"] for v in res["sermons"]["by_work"].values()]
    return {
        "answer": answer,
        "book_pre_christian_per_10k": rate,
        "book_ci95": bom["ci95"],
        "ot_held_out_max": ot_max,
        "jasher": jasher,
        "thomson_ot": thomson,
        "josephus": josephus,
        "decoys": decoys,
        "decoys_among_translations": [n for n, x in decoys.items() if x <= within_top],
        "imitations_median": statistics.median(imit.values()) if imit else None,
        "imitations_below_book": sum(x < rate for x in imit.values()),
        "imitations_counted": len(imit),
        "percentile_among_sermons": NT.percentile_of(rate, ser),
    }


# ----------------------------------------------------------------------------- design 2: blocks


def block_rates(flag: list[int], size: int) -> list[float]:
    """Rate per 10,000 words in each whole block of ``size`` words; the remainder is dropped."""
    return [sum(flag[i : i + size]) / size * 10000 for i in range(0, len(flag) - size + 1, size)]


def share_below(xs: list[float], bar: float) -> float:
    return round(sum(x < bar for x in xs) / len(xs), 4) if xs else float("nan")


def check2(ctx: dict, d2: dict) -> dict:
    """Design 2 known-answer check: 5,000-word blocks of every King James book; an Old
    Testament block against the Old Testament without its whole book."""
    conc, size = ctx["conc"], d2["block_words"]
    blocks, dropped = [], []
    for c in conc.codes:
        hold = c if conc.section[c] == "OT" else None
        kept, flag = marks(conc.words[c], conc, ctx["kjv_names"], ctx["lexicon"], hold)
        rates = block_rates(flag, size)
        if not rates:
            dropped.append({"book": c, "section": conc.section[c], "words": len(kept)})
        for i, r in enumerate(rates):
            blocks.append(
                {"book": c, "section": conc.section[c], "block": i, "per_10k": round(r, 2)}
            )
    by = {s: [b["per_10k"] for b in blocks if b["section"] == s] for s in ("OT", "NT", "Apocrypha")}
    med = {s: statistics.median(v) for s, v in by.items()}
    auc = {s: round(NT.auc(by[s], by["OT"]), 4) for s in ("NT", "Apocrypha")}
    below = {s: share_below(by["OT"], med[s]) for s in ("NT", "Apocrypha")}
    groups = {}
    for g, codes in d2["ot_groups"].items():
        xs = [b["per_10k"] for b in blocks if b["book"] in codes]
        groups[g] = {
            "blocks": len(xs),
            "median": statistics.median(xs) if xs else None,
            "max": max(xs) if xs else None,
            "below_nt_median": share_below(xs, med["NT"]),
            "below_apocrypha_median": share_below(xs, med["Apocrypha"]),
            "auc_nt_over_these": round(NT.auc(by["NT"], xs), 4) if xs else None,
            "auc_apocrypha_over_these": round(NT.auc(by["Apocrypha"], xs), 4) if xs else None,
        }
    passed = all(auc[s] >= d2["auc_bar"] for s in auc) and all(
        below[s] >= d2["below_median_share"] for s in below
    )
    above = [
        b
        for b in blocks
        if b["section"] == "OT" and b["per_10k"] >= min(med["NT"], med["Apocrypha"])
    ]
    return {
        "rule": "OT blocks vs NT and vs Apocrypha blocks: AUC >= bar each, and the share of OT "
        "blocks below the NT and the Apocrypha block medians >= bar each",
        "bars": {"auc": d2["auc_bar"], "below_median_share": d2["below_median_share"]},
        "blocks": {s: len(v) for s, v in by.items()},
        "medians": med,
        "auc": auc,
        "ot_below_median": below,
        "passed": passed,
        "ot_groups_reported_not_the_bar": groups,
        "ot_blocks_at_or_above_lower_nt_apocrypha_median": sorted(
            Counter(b["book"] for b in above).items(), key=lambda kv: -kv[1]
        ),
        "dropped_under_block": dropped,
        "block_rates": blocks,
    }


def control_pieces(cfg: dict) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    """Group -> name -> the text's files (each blocked on its own)."""
    groups, missing = control_texts(cfg)
    w = cfg["lab"]["hebrew_vocabulary"]
    res = {g: {n: [t] for n, t in items.items()} for g, items in groups.items()}
    for name, paths in w["texts"].items():
        g = "decoys" if name in w["decoys"] else "translations"
        if name in res.get(g, {}):
            res[g][name] = [read_paths([p]) or "" for p in paths]
    later = sorted((NT.PRIVATE_CAND / "later").glob("*.txt"))
    if later and "js_later_revelations" in res["revelations"]:
        res["revelations"]["js_later_revelations"] = [
            p.read_text("utf-8", "replace") for p in later
        ]
    return res, missing


def blocks_of(
    pieces: list[str],
    ctx: dict,
    base_names: set[str],
    size: int,
    cap: int | None = None,
    names_from: str | None = None,
) -> tuple[list[float], Counter, int]:
    """Block rates over a text's pieces, its outside-word counts, and its words."""
    rates, outside, words = [], Counter(), 0
    names = base_names | text_names(names_from or "\n".join(pieces), ctx["webster"])
    for t in pieces:
        toks = tokens(t)[:cap] if cap else tokens(t)
        kept, flag = marks(toks, ctx["conc"], names, ctx["lexicon"])
        rates += block_rates(flag, size)
        outside.update(x for x, f in zip(kept, flag, strict=True) if f)
        words += len(kept)
    return rates, outside, words


def summary(rates: list[float], words: int) -> dict:
    return {
        "words": words,
        "blocks": len(rates),
        "median": round(statistics.median(rates), 2) if rates else None,
        "min": round(min(rates), 2) if rates else None,
        "max": round(max(rates), 2) if rates else None,
    }


def run2(cfg: dict, design: int = 2) -> dict:
    from scipy.stats import mannwhitneyu

    ctx = prepare(cfg)
    w = ctx["w"]
    d2 = w["design2"]
    size = d2["block_words"]
    chk = check3(ctx, w) if design == 3 else check2(ctx, d2)
    res: dict = {"design": design, "known_answer": chk, "settings": w}
    if not chk["passed"]:
        res["stopped"] = "the known-answer check missed its bar; the Book of Mormon was not scored"
        return res
    base = ctx["kjv_names"] | bom_names(cfg)
    bom = bom_texts(cfg["lab"]["new_testament_wording"])
    every = bom.pop("_all")
    pre_books = [k for k in bom if k.startswith("book:")]
    book_rates, book_out, book_words, by_book = [], Counter(), 0, {}
    for k in pre_books:
        r, o, n = blocks_of([bom[k]], ctx, base, size, names_from=every)
        by_book[k[5:]] = summary(r, n)
        book_rates += r
        book_out.update(o)
        book_words += n
    res["book_of_mormon"] = {
        "pre_christian_outside_quotation": summary(book_rates, book_words),
        "by_book": by_book,
        "book_block_rates": [round(x, 2) for x in book_rates],
    }
    for k in ("3_nephi_outside_quotation", "after_visit_outside_quotation", "quotation_chapters"):
        r, _o, n = blocks_of([bom[k]], ctx, base, size, names_from=every)
        res["book_of_mormon"][k] = summary(r, n)
    pieces, missing = control_pieces(cfg)
    res["not_attempted"] = missing
    ctrl_rates: dict[str, list[float]] = {}
    res["controls"] = {}
    for g, items in pieces.items():
        res["controls"][g] = {}
        for n, ps in items.items():
            r, o, nw = blocks_of(ps, ctx, base, size)
            ctrl_rates[n] = r
            res["controls"][g][n] = summary(r, nw) | {
                "top_outside_words": [
                    {"word": x, "count": c, "in_nt_or_apocrypha": ctx["conc"].in_nt_ap(x)}
                    for x, c in o.most_common(15)
                ]
            }
    ser_med, unreadable, ser_pairs, ser_blocks = {}, 0, Counter(), []
    for row in sermon_rows(cfg):
        try:
            text = NT.door.text_of(row)
        except OSError:
            unreadable += 1  # not attempted, never a result
            continue
        r, _o, _n = blocks_of([text], ctx, base, size, cap=w["max_words_per_work"])
        ser_blocks += r
        if r:
            ser_med[row["work_id"]] = round(statistics.median(r), 2)
        for name, p in pairings(text, w["pairs"]).items():
            ser_pairs[f"{name}_pair"] += p["pair"]
            ser_pairs[f"{name}_collective"] += p["collective"]
    res["sermons"] = {
        "works_with_a_block": len(ser_med),
        "unreadable": unreadable,
        "block_medians_by_work": NT.quantiles(list(ser_med.values())),
        "all_blocks": NT.quantiles(ser_blocks),
        "pairings_pooled": dict(ser_pairs),
        "by_work_median": ser_med,
    }
    # verdict
    bm = statistics.median(book_rates)
    bars = {"jasher": "jasher_1840", "thomson_ot": "thomson_1808_ot", "josephus": w["josephus"]}
    tests = {}
    for label, name in bars.items():
        xs = ctrl_rates.get(name, [])
        p = float(mannwhitneyu(book_rates, xs, alternative="greater").pvalue) if xs else None
        tests[label] = {
            "text": name,
            "median": round(statistics.median(xs), 2) if xs else None,
            "blocks": len(xs),
            "mann_whitney_one_sided_p": p,
        }
    meds = [t["median"] for t in tests.values()]
    if None in meds:
        answer = "not attempted (a bar text could not be read)"
    elif bm > max(meds) and all(
        t["mann_whitney_one_sided_p"] < d2["alpha"] for t in tests.values()
    ):
        answer = "more"
    elif bm <= max(meds):
        answer = "within their range"
    else:
        answer = "cannot tell"
    top_m = max(m for m in meds if m is not None) if any(m is not None for m in meds) else None

    def med(name):
        xs = ctrl_rates.get(name)
        return round(statistics.median(xs), 2) if xs else None

    res["verdict"] = {
        "answer": answer,
        "book_block_median": round(bm, 2),
        "book_blocks": len(book_rates),
        "bars": tests,
        "decoys": {n: med(n) for n in w["decoys"]},
        "decoys_among_translations": [
            n for n in w["decoys"] if med(n) is not None and top_m is not None and med(n) <= top_m
        ],
        "imitation_medians_below_book": sum(
            1 for n in res["controls"]["imitations"] if (med(n) or 0) < bm and med(n) is not None
        ),
        "imitations_with_a_block": sum(1 for n in res["controls"]["imitations"] if med(n)),
        "percentile_among_sermon_work_medians": NT.percentile_of(bm, list(ser_med.values())),
        "three_nephi_median": res["book_of_mormon"]["3_nephi_outside_quotation"]["median"],
    }
    res["top_outside_words"] = [
        {"word": x, "count": c, "in_nt_or_apocrypha": ctx["conc"].in_nt_ap(x)}
        for x, c in book_out.most_common(d2["top_words"])
    ]
    pre_text = "\n".join(bom[k] for k in pre_books)
    res["pairings"] = {
        "book_pre_christian": pairings(pre_text, w["pairs"]),
        "book_3_nephi": pairings(bom["3_nephi_outside_quotation"], w["pairs"]),
        "king_james": {
            s: pairings(
                "\n".join(
                    "\n".join(ctx["conc"].text[c])
                    for c in ctx["conc"].codes
                    if ctx["conc"].section[c] == s
                ),
                w["pairs"],
            )
            for s in ("OT", "NT", "Apocrypha")
        },  # fmt: skip
        "controls": {
            g: {n: pairings("\n".join(ps), w["pairs"]) for n, ps in items.items()}
            for g, items in pieces.items()
        },
    }
    res["hebrew"] = part2(ctx, [x["word"] for x in res["top_outside_words"]])
    return res


# ----------------------------------------------------------------------------- design 3


def ylt_books(path: str) -> dict[str, tuple[str, str]] | None:
    """Young's text by OSIS book: (section, text); None when the file cannot be read."""
    from lab import translation2 as T2

    v = T2.ylt_verses(Path(path))
    if v is None:
        return None
    res: dict[str, list[str]] = defaultdict(list)
    for ref, t in v.items():
        res[ref.split(".")[0]].append(t)
    return {b: ("OT" if b in T2.OT_OSIS else "NT", "\n".join(ts)) for b, ts in res.items()}


def two_sides(ot: list[float], nt: list[float], d2: dict) -> dict:
    med = statistics.median(nt) if nt else None
    auc = round(NT.auc(nt, ot), 4) if ot and nt else None
    below = share_below(ot, med) if med is not None else None
    return {
        "blocks": {"OT": len(ot), "NT": len(nt)},
        "medians": {"OT": statistics.median(ot) if ot else None, "NT": med},
        "auc_nt_over_ot": auc,
        "ot_below_nt_median": below,
        "passed": auc is not None and auc >= d2["auc_bar"] and below >= d2["below_median_share"],
    }


def check3(ctx: dict, w: dict) -> dict:
    """Design 3: the King James New Testament against its Old Testament (design 2's two
    conditions) and Young's New Testament against his Old Testament, same concordance."""
    d2, d3, size = w["design2"], w["design3"], w["design2"]["block_words"]
    k = check2(ctx, d2)
    rates = k["block_rates"]
    kjv = two_sides(
        [b["per_10k"] for b in rates if b["section"] == "OT"],
        [b["per_10k"] for b in rates if b["section"] == "NT"],
        d2,
    )
    books = ylt_books(d3["ylt"])
    if books is None:
        return {"passed": False, "stopped": "Young's text could not be read (not attempted)"}
    ylt = {"OT": [], "NT": []}
    raw = {"OT": [], "NT": []}
    section_text = {s: "\n".join(t for sec, t in books.values() if sec == s) for s in ylt}
    names = {s: ctx["kjv_names"] | text_names(section_text[s], ctx["webster"]) for s in ylt}
    dropped = []
    for b, (sec, t) in books.items():
        toks = tokens(t)
        kept, flag = marks(toks, ctx["conc"], names[sec], ctx["lexicon"])
        _k, f_raw = marks(toks, ctx["conc"], names[sec], None)
        r = block_rates(flag, size)
        if not r:
            dropped.append({"book": b, "section": sec, "words": len(kept)})
        ylt[sec] += r
        raw[sec] += block_rates(f_raw, size)
    y = two_sides(ylt["OT"], ylt["NT"], d2)
    y_raw = two_sides(raw["OT"], raw["NT"], d2)
    y_raw.pop("passed")
    apoc = {}
    kjv_ot = [b["per_10k"] for b in rates if b["section"] == "OT"]
    for lang, codes in d3["apocrypha_language"].items():
        xs = [b["per_10k"] for b in rates if b["book"] in codes]
        apoc[lang] = {
            "books_with_a_block": sorted({b["book"] for b in rates if b["book"] in codes}),
            "blocks": len(xs),
            "median": statistics.median(xs) if xs else None,
            "auc_over_kjv_ot": round(NT.auc(xs, kjv_ot), 4) if xs else None,
        }
    tho = {}
    for name in ("thomson_1808_ot", "thomson_1808_nt"):
        r, _o, n = blocks_of(
            [read_paths([p]) or "" for p in w["texts"][name]], ctx, ctx["kjv_names"], size
        )
        tho[name] = summary(r, n) | {"block_rates": [round(x, 2) for x in r]}
    tho_ot = tho["thomson_1808_ot"]["block_rates"]
    tho_nt = tho["thomson_1808_nt"]["block_rates"]
    return {
        "rule": "(a, b) King James NT blocks vs OT blocks and (c, d) Young's NT vs OT blocks: "
        "AUC >= bar and share of OT blocks below the NT median >= bar, each",
        "bars": {"auc": d2["auc_bar"], "below_median_share": d2["below_median_share"]},
        "king_james": kjv,
        "young": y,
        "passed": kjv["passed"] and y["passed"],
        "reported_not_the_bar": {
            "young_without_the_dictionary_filter": y_raw,
            "young_dropped_under_block": dropped,
            "apocrypha_by_language_of_composition": apoc,
            "thomson": {
                "ot": {k2: v for k2, v in tho["thomson_1808_ot"].items() if k2 != "block_rates"},
                "nt": {k2: v for k2, v in tho["thomson_1808_nt"].items() if k2 != "block_rates"},
                "auc_nt_over_ot": round(NT.auc(tho_nt, tho_ot), 4) if tho_ot and tho_nt else None,
            },
            "design2_king_james": {
                x: k[x] for x in ("blocks", "medians", "auc", "ot_below_median")
            },
        },
        "block_rates": rates,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run", "check2", "run2", "check3", "run3"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "check":
        ctx = prepare(cfg)
        res = known_answer(ctx)
        # The Hebrew instrument, read on the card's seed word only (no Book of Mormon words).
        res["hebrew_instrument"] = part2(ctx, ["parents"])
        res["stamp"] = config.stamp()
        out(OUT / "check.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "books"}, indent=1))
        return 0
    if a.cmd == "check2":
        res = check2(prepare(cfg), cfg["lab"]["hebrew_vocabulary"]["design2"])
        res["stamp"] = config.stamp()
        out(OUT / "check2.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "block_rates"}, indent=1))
        return 0
    if a.cmd == "check3":
        res = check3(prepare(cfg), cfg["lab"]["hebrew_vocabulary"])
        res["stamp"] = config.stamp()
        out(OUT / "check3.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "block_rates"}, indent=1))
        return 0
    if a.cmd == "run3":
        res = run2(cfg, design=3)
        res["stamp"] = config.stamp()
        out(OUT / "result3.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res.get("verdict", res.get("stopped")), indent=1))
        return 0
    if a.cmd == "run2":
        res = run2(cfg)
        res["stamp"] = config.stamp()
        out(OUT / "result2.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res.get("verdict", res.get("stopped")), indent=1))
        return 0
    res = run(cfg)
    res["stamp"] = config.stamp()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ("verdict",) if k in res}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
