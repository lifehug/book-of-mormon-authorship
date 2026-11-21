"""BOM-111: the inventory of things, whose world do the animals, plants, metals and tools belong to?

Six category word lists (animals, plants and foods, metals and materials, tools and weapons,
buildings, clothing) are compiled from ``lab.inventory_lexicon``. Each text gets a count per item
and a vector (item rarity in a background sample of library books times the log of its rate per
10,000 words). Four worlds are compared by cosine to each world's centroid: the Bible and the
ancient Near East; Mesoamerica (native texts and Spanish chronicles in English); American
writing of the 1810s and 1820s about antiquities and the frontier; and a background sample of
period library books. The known-answer check holds every text out in turn (whole, and in
10,000-word chunks). Only if it passes bar is the Book of Mormon placed, with and without the
long King James chapters and with and without the translator's allowance (Old World words that
chroniclers put on New World things, read as ambiguous). Also reported: absences per world, the
untranslated words, and how often the chroniclers gloss. **The lists are written from memory.**
The test card, written first, is ``data/private/lab/owner/2026-11-20-inventory/card.md``;
settings are ``lab.inventory`` in the config. The result holds names and counts, no passages.

Usage::

    python -m lab.inventory lexicon   # compile the lists, print sizes and collisions (no texts)
    python -m lab.inventory counts    # count every comparison text (cached; no Book of Mormon)
    python -m lab.inventory check     # known-answer checks only (held-out texts)
    python -m lab.inventory run       # -> data/lab/setting/inventory/result.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import subprocess
from collections import Counter

import numpy as np

from lab import door, registry
from lab import inventory_lexicon as lex
from lab.numbers import (
    CAND,
    CHRISTENSON,
    _file,
    _josephus,
    _kjv,
    _library,
    _pdf,
    between,
    bom_text,
    english,
    gutenberg,
)
from lab.paths import FAST, REGISTRY, out
from lab.wherefore import QUOTED  # noqa: F401  (used through bom_text; named for the card)
from metadata import config

OUT = REGISTRY / "setting" / "inventory"
CACHE = FAST / "inventory"
SETTING = FAST / "sources" / "setting"
WORLDS = ("near_east", "mesoamerica", "american", "background")
CATEGORIES = tuple(lex.CATEGORIES)

# ------------------------------------------------------------------------------ the lexicon

DET = set(
    "a an the his her their my thy thine our your its this that these those of with by many two "
    "three four five six seven eight nine ten twelve twenty hundred thousand some no every each "
    "such other another any more much little great good golden silver iron brazen wild".split()
)


def _norm(form: str) -> str:
    return form.replace("-", " ").replace("_", " ")


def _plurals(w: str) -> set[str]:
    out_ = {w, w + "s"}
    if w.endswith(("s", "x", "z", "ch", "sh", "o")):
        out_.add(w + "es")
    if w.endswith("y") and len(w) > 2:
        out_.add(w[:-1] + "ies")
    if w.endswith("fe"):
        out_.add(w[:-2] + "ves")
    elif w.endswith("f"):
        out_.add(w[:-1] + "ves")
    return out_


def compile_lexicon() -> dict:
    """Items by lemma, the form -> lemma tables, and any form claimed by two lemmas."""
    items: dict[str, dict] = {}
    forms: dict[str, str] = {}
    collisions: list[tuple[str, str, str]] = []
    for cat, raw in lex.CATEGORIES.items():
        for tok in (raw + " " + lex.ADDED.get(cat, "") + " " + lex.VARIANTS.get(cat, "")).split():
            lc = guard = False
            while tok[-1] in "!?":
                lc, guard = lc or tok[-1] == "!", guard or tok[-1] == "?"
                tok = tok[:-1]
            head, _, extra = tok.partition(":")
            lemma = _norm(head)
            if lemma in lex.EXCLUDE:
                continue
            if lemma in forms and forms[lemma] != lemma:
                continue  # a plural already generated for another entry
            spell = [lemma] + [_norm(x) for x in extra.split(",") if x]
            if lemma in items:
                if items[lemma]["category"] != cat:
                    collisions.append((lemma, items[lemma]["category"], cat))
                    continue
                spell = spell[1:]  # more spellings of an item already listed
            else:
                items[lemma] = {"category": cat, "lc": lc, "guard": guard, "forms": set()}
            for sp in spell:
                for f in _plurals(sp):
                    if f in forms and forms[f] != lemma:
                        collisions.append((f, forms[f], lemma))
                        continue
                    forms[f] = lemma
                    items[lemma]["forms"].add(f)
    for tag, raw in (("OW", lex.ORIGIN_OW), ("NW", lex.ORIGIN_NW), ("NE", lex.ORIGIN_NE)):
        for tok in raw.split():
            lemma = _norm(tok.rstrip("?!"))
            if lemma in items:
                items[lemma].setdefault("origin", set()).add(tag)
    for tok in lex.ALLOWANCE.split():
        lemma = _norm(tok)
        if lemma in items:
            items[lemma]["allowance"] = True
    return {
        "items": items,
        "forms": forms,
        "multi": {f: lm for f, lm in forms.items() if " " in f},
        "collisions": collisions,
    }


LEX = compile_lexicon()
LEMMAS = sorted(LEX["items"])
INDEX = {lm: i for i, lm in enumerate(LEMMAS)}
APART = set(lex.APART)


def lexicon_sha() -> str:
    body = json.dumps(
        {k: sorted(v["forms"]) + [v["category"], v["lc"], v["guard"]]
         for k, v in LEX["items"].items()}, sort_keys=True)  # fmt: skip
    return hashlib.sha256(body.encode()).hexdigest()


# ------------------------------------------------------------------------------ counting

TOKEN = re.compile(r"[A-Za-z]+")
JOINED = re.compile(r"([a-z])-[ \t]*\n[ \t]*([a-z])")


VOCAB: dict[str, int] = {}  # words of the clean-spelling texts (King James, Josephus)
_MEMO: dict[str, str] = {}


def set_vocab(texts: list[str | None]) -> None:
    """Words met at least three times in clean-spelling texts: the test for a long-s misreading."""
    count: Counter = Counter()
    for t in texts:
        if t:
            count.update(w.lower() for w in TOKEN.findall(t))
    VOCAB.clear()
    VOCAB.update({w: c for w, c in count.items() if c >= 3})
    VOCAB.update({f: 3 for f in LEX["forms"] if " " not in f})  # an item word is a word
    _MEMO.clear()


def repair(w: str) -> str:
    """A word not in the vocabulary that becomes one when some f is read as a long s
    ("fword" -> "sword", "himfelf" -> "himself"); otherwise unchanged."""
    lw = w.lower()
    if not VOCAB or "f" not in lw or lw in VOCAB or len(lw) > 14:
        return w
    got = _MEMO.get(lw)
    if got is None:
        spots = [i for i, ch in enumerate(lw) if ch == "f"][:4]
        best, best_n = lw, 0
        for mask in range(1, 2 ** len(spots)):
            cand = list(lw)
            for j, i in enumerate(spots):
                if mask >> j & 1:
                    cand[i] = "s"
            cand = "".join(cand)
            if VOCAB.get(cand, 0) > best_n:
                best, best_n = cand, VOCAB[cand]
        got = _MEMO[lw] = best
    if got == lw:
        return w
    return got.capitalize() if w[:1].isupper() else got


def words_of(text: str) -> list[str]:
    text = JOINED.sub(r"\1\2", text.replace(chr(0x17F), "s"))  # words broken at a line end
    return [repair(w) for w in TOKEN.findall(text)]


def occurrences(words: list[str]) -> list[tuple[int, str]]:
    """(position, lemma) of every item occurrence; a two-word item uses both words."""
    items, forms, multi = LEX["items"], LEX["forms"], LEX["multi"]
    low = [w.lower() for w in words]
    found, i, n = [], 0, len(words)
    while i < n:
        if i + 1 < n:
            two = low[i] + " " + low[i + 1]
            if two in multi:
                found.append((i, multi[two]))
                i += 2
                continue
        lemma = forms.get(low[i])
        if lemma is not None:
            spec = items[lemma]
            if spec["lc"] and not words[i].islower():
                lemma = None
            elif spec["guard"] and (i == 0 or low[i - 1] not in DET):
                lemma = None
        if lemma is not None:
            found.append((i, lemma))
        elif low[i] in APART:
            found.append((i, "corn"))
        i += 1
    return found


def count_text(text: str, chunk: int, keep_positions: bool = False) -> dict:
    """Counts per item for the whole text and per full chunk; ``corn`` is counted apart."""
    words = words_of(text)
    found = occurrences(words)
    whole: Counter = Counter(lm for _, lm in found)
    chunks: list[Counter] = [Counter() for _ in range(len(words) // chunk)]
    for pos, lm in found:
        if pos // chunk < len(chunks):
            chunks[pos // chunk][lm] += 1
    res = {"words": len(words), "whole": dict(whole), "chunks": [dict(c) for c in chunks]}
    if keep_positions:
        res["found"] = found
        res["tokens"] = words
    return res


# ------------------------------------------------------------------------------ the texts


def _setting(name: str) -> str | None:
    return _file(SETTING / name / "text.txt")


def _join(*parts: str | None) -> str | None:
    return None if any(p is None for p in parts) else "\n".join(parts)  # type: ignore[arg-type]


def _poems(cfg: dict) -> str | None:
    raw = _file(SETTING / "brinton_nahuatl_poetry_1887.txt")
    if raw is None:
        return None
    a = raw.find("ANCIENT NAHUATL POEMS.")
    b = raw.find("NOTES FOR SONG I.")
    if a < 0 or b < a:
        return None
    return english(raw[a:b], cfg["lab"]["inventory"]["english_share"])


def _bilingual(name: str, start: str, stop: str, cfg: dict, indented: bool = False):
    raw = _file(SETTING / name)
    if raw is None:
        return None
    share = cfg["lab"]["inventory"]["english_share"]
    return english(between(gutenberg(raw), start, stop, indented), share)


def _christenson(cfg: dict) -> str | None:
    pdfs = sorted(CHRISTENSON.glob("*hristenson*.pdf")) if CHRISTENSON.is_dir() else []
    raw = _pdf(pdfs[0]) if pdfs else None
    return None if raw is None else english(raw, cfg["lab"]["inventory"]["english_share"])


def named_texts(cfg: dict) -> list[tuple[str, str | None, str | None, str | None]]:
    """(name, world, register, text or None); a world of None is scored, not trained on."""
    spence = _file(SETTING / "popol_vuh_spence_1908.txt")
    ne, ms, am = "near_east", "mesoamerica", "american"
    rows = [
        ("kjv_old_testament", ne, "bible", _kjv("OT")),
        ("kjv_new_testament", ne, "bible", _kjv("NT")),
        ("kjv_apocrypha", ne, "bible", _kjv("Apocrypha")),
        ("josephus_antiquities_whiston", ne, "josephus",
         _josephus("josephus_antiquities_whiston.txt")),
        ("josephus_wars_whiston", ne, "josephus", _josephus("josephus_wars_whiston.txt")),
        ("brinton_maya_chronicles_and_rig_veda", ms, "native", _join(_bilingual(
            "brinton_maya_chronicles_1882.txt", r"TRANSLATION\.|CONQUEST AND MAP\.",
            r"NOTES\.|VOCABULARY\.", cfg), _bilingual(
            "brinton_rig_veda_americanus_1890.txt",
            r"_Translation\._|_(The )?(Hymn|War Song|Song) .*\._", r"_Notes\._|GLOSSARY\.",
            cfg))),
        ("brinton_annals_cakchiquels_1885", ms, "native", _bilingual(
            "brinton_annals_cakchiquels_1885.txt", r"THE ANNALS", r"NOTES\.|VOCABULARY\.", cfg,
            indented=True)),
        ("brinton_nahuatl_poetry_1887", ms, "native", _poems(cfg)),
        ("popol_vuh_spence_1908", ms, "native", None if spence is None else gutenberg(spence)),
        ("popol_vuh_christenson", ms, "native", _christenson(cfg)),
        ("bernal_diaz_keatinge_1800", ms, "chronicle", _setting("truehistoryofcon00dauoft")),
        ("solis_conquest_of_mexico_1724", ms, "chronicle", _setting("historyofconques00sols")),
        ("cusick_1827", am, "antiquities", _setting("Ayer_251_I611_C9_1827")),
        ("priest_american_antiquities_1833", am, "antiquities", _setting("americanantiquit01prie")),
        ("priest_wonders_1826", am, "antiquities", _setting("wondersnaturean00priegoog")),
        ("clinton_discourse_and_western_new_york", am, "antiquities",
         _join(_setting("discoursedel00clinton"), _setting("westernpartsstate00clinrich"))),
        ("adair_american_indians_1775", am, "antiquities", _setting("historyofamerica00adairich")),
        ("seaver_jemison_1826", am, "narrative", _setting("narrativeoflifeo00seav")),
        ("hale_genius_of_oblivion_1823", am, "narrative", _setting("geniusofoblivion00hale")),
        ("ss-manuscript-story-1885", am, "narrative", _file(CAND / "ss-manuscript-story-1885.txt")),
        ("gh-1816-late-war", am, "narrative", _file(CAND / "gh-1816-late-war.txt")),
        ("es-1825-view-of-the-hebrews", am, "antiquities",
         _file(CAND / "es-1825-view-of-the-hebrews.txt")),
        # scored beside the Book of Mormon, never trained on
        ("robertson_history_of_america", None, "extra",
         _join(_setting("historyofamerica01roberich"), _setting("historyofamerica02roberich"))),
        ("humboldt_researches_1814", None, "extra",
         _join(_setting("researchesconcer01humb"), _setting("researchesconcer02humb"))),
        ("acosta_natural_moral_history", None, "extra",
         _join(_setting("naturalmoralhist60acosrich"), _setting("naturalmoralhist61acosrich"))),
        ("drake_indian_biography_1832", None, "extra", _setting("drakechiefsbio00drakrich")),
        ("mathews_behemoth_1839", None, "extra", _setting("behemothlegend00mathrich")),
    ]  # fmt: skip
    cat = door.catalog(set(cfg["lab"]["inventory"]["clavigero"]))
    clav = [_library(cat[i]) if i in cat else None for i in cfg["lab"]["inventory"]["clavigero"]]
    rows.append(("clavigero_history_of_mexico_1787", ms, "chronicle",
                 "\n".join(clav) if all(c is not None for c in clav) else None))  # fmt: skip
    return rows


def library_samples(cfg: dict) -> tuple[list[dict], list[dict]]:
    """Two disjoint seeded samples of period library books: rarity weights, and background."""
    n = cfg["lab"]["inventory"]
    skip = set(n["clavigero"])
    rows = [
        r
        for r in registry.load().to_pylist()
        if r["kind"] == "work"
        and r["has_text"]
        and r["dup_keeper"]
        and not r["sealed"]
        and not r["ocr_excluded"]
        and r["work_id"] not in skip
        and "newspaper" not in (r["genre"] or "")
        and r["year"]
        and n["year_min"] <= r["year"] <= n["year_max"]
        and n["min_words"] <= (r["words"] or 0) <= n["max_words"]
    ]
    rows.sort(key=lambda r: r["work_id"])
    random.Random(n["seed"]).shuffle(rows)
    need = n["background_weight_n"] + n["background_world_n"]
    pool = rows[: need * 2]
    cat = door.catalog({r["work_id"] for r in pool})
    pool = [{**cat[r["work_id"]], **r} for r in pool if cat.get(r["work_id"], {}).get("text_path")]
    a = pool[: n["background_weight_n"]]
    b = pool[n["background_weight_n"] : need]
    return a, b


def prepare(cfg: dict) -> list[tuple[str, str | None, str | None, str | None]]:
    """Load the named texts and fix the clean-spelling vocabulary used to read long s."""
    rows = named_texts(cfg)
    clean = {n: t for n, _, _, t in rows}
    set_vocab(
        [
            clean[n]
            for n in (
                "kjv_old_testament",
                "kjv_new_testament",
                "josephus_antiquities_whiston",
                "josephus_wars_whiston",
            )
        ]
    )
    return rows


def counted(name: str, text: str | None, cfg: dict) -> dict | None:
    """Counts for one text, cached by lexicon and chunk size; None if the text is not held."""
    if text is None:
        return None
    n = cfg["lab"]["inventory"]
    key = hashlib.sha256(
        (lexicon_sha() + str(n["chunk_words"]) + "long-s-v1" + str(len(VOCAB))
         + hashlib.sha256(text.encode()).hexdigest()).encode()
    ).hexdigest()[:20]  # fmt: skip
    path = CACHE / f"{re.sub('[^A-Za-z0-9_.:-]', '_', name)[:80]}-{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    res = count_text(text, n["chunk_words"])
    out(path).write_text(json.dumps(res))
    return res


# ------------------------------------------------------------------------------ vectors


def rarity_weights(sample: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Rarity weight per item from the weight sample's whole-text counts; and the df itself."""
    df = np.zeros(len(LEMMAS))
    for c in sample:
        for lm, k in c["whole"].items():
            if k > 0 and lm in INDEX:
                df[INDEX[lm]] += 1
    n = len(sample)
    return np.log((n + 1) / (df + 1)), df


def dense(counts: dict, words: int) -> np.ndarray:
    """Rate per 10,000 words as a vector over the items (``corn`` is not an item)."""
    v = np.zeros(len(LEMMAS))
    for lm, k in counts.items():
        if lm in INDEX:
            v[INDEX[lm]] = k * 10000.0 / words
    return v


def allowance_mask() -> np.ndarray:
    m = np.ones(len(LEMMAS))
    for i, lm in enumerate(LEMMAS):
        if LEX["items"][lm].get("allowance"):
            m[i] = 0.0
    return m


def category_mask(cat: str) -> np.ndarray:
    return np.array([1.0 if LEX["items"][lm]["category"] == cat else 0.0 for lm in LEMMAS])


class Space:
    """Unit vectors of every counted text and chunk under one weight vector and item mask."""

    def __init__(self, texts: dict[str, dict], w: np.ndarray, mask: np.ndarray, cfg: dict):
        n = cfg["lab"]["inventory"]
        self.w, self.mask, self.texts = w * mask, mask, texts
        self.whole: dict[str, np.ndarray] = {}
        self.chunks: dict[str, np.ndarray] = {}
        for name, t in texts.items():
            self.whole[name] = self.unit(dense(t["whole"], t["words"]))
            picks = list(range(len(t["chunks"])))
            if len(picks) > n["max_chunks"]:
                picks = sorted(random.Random(f"{n['seed']}-{name}").sample(picks, n["max_chunks"]))
            if picks:
                rows = [self.unit(dense(t["chunks"][i], n["chunk_words"])) for i in picks]
                self.chunks[name] = np.array(rows)

    def unit(self, rate: np.ndarray) -> np.ndarray:
        v = self.w * np.log1p(rate)
        nrm = np.linalg.norm(v)
        return v / nrm if nrm > 0 else v

    def vector(self, counts: dict, words: int) -> np.ndarray:
        return self.unit(dense(counts, words))

    def profiles(self, members: dict[str, list[str]], skip: str | None = None,
                 only: set[str] | None = None) -> dict[str, np.ndarray]:  # fmt: skip
        """World profile: mean of the member texts' unit vectors, leaving out ``skip``."""
        res = {}
        for world, names in members.items():
            use = [n for n in names if n != skip and (only is None or n in only)]
            res[world] = np.mean([self.whole[n] for n in use], axis=0) if use else None
        return res


def cosines(x: np.ndarray, prof: dict[str, np.ndarray | None]) -> dict[str, float | None]:
    res = {}
    for world, p in prof.items():
        nrm = None if p is None else np.linalg.norm(p)
        res[world] = None if p is None or nrm == 0 else float(x @ p / nrm)
    return res


def best(sc: dict[str, float | None]) -> str | None:
    ok = {k: v for k, v in sc.items() if v is not None}
    return max(ok, key=ok.get) if ok else None


# ------------------------------------------------------------------------------ the check


def members(texts: dict[str, dict], include=None) -> dict[str, list[str]]:
    res: dict[str, list[str]] = {w: [] for w in WORLDS}
    for name, t in texts.items():
        if t["world"] in res and (include is None or include(name, t)):
            res[t["world"]].append(name)
    return res


def confusion(rows: list[tuple[str, str | None]]) -> dict[str, dict[str, int]]:
    tab: dict[str, dict[str, int]] = {w: {v: 0 for v in WORLDS} for w in WORLDS}
    for true, got in rows:
        if got is not None:
            tab[true][got] += 1
    return tab


def held_out(sp: Space, cfg: dict) -> dict:
    """Every text of the four worlds is placed by profiles built without it."""
    n = cfg["lab"]["inventory"]
    mem = members(sp.texts)
    whole, chunk, per_text = [], [], {}
    for world, names in mem.items():
        for name in names:
            prof = sp.profiles(mem, skip=name)
            sc = cosines(sp.whole[name], prof)
            got = best(sc)
            whole.append((world, got))
            own = None
            if name in sp.chunks:
                picks = [best(cosines(x, prof)) for x in sp.chunks[name]]
                chunk += [(world, g) for g in picks]
                own = sum(g == world for g in picks) / len(picks)
            per_text[name] = {"world": world, "register": sp.texts[name]["register"],
                              "words": sp.texts[name]["words"], "placed": got,
                              "scores": sc, "chunks": len(sp.chunks.get(name, [])),
                              "chunk_own_rate": own}  # fmt: skip
    tab = confusion(whole)
    rate = {w: tab[w][w] / sum(tab[w].values()) for w in WORLDS if sum(tab[w].values())}
    pooled = sum(tab[w][w] for w in WORLDS) / sum(sum(tab[w].values()) for w in WORLDS)
    ctab = confusion(chunk)
    crate = {w: ctab[w][w] / sum(ctab[w].values()) for w in WORLDS if sum(ctab[w].values())}
    # chunk rates are the mean of the texts' own rates, so a long text does not outweigh a short one
    by_text = {
        w: [
            t["chunk_own_rate"]
            for t in per_text.values()
            if t["world"] == w and t["chunk_own_rate"] is not None
        ]
        for w in WORLDS
    }
    crate_text = {w: float(np.mean(v)) for w, v in by_text.items() if v}
    return {
        "whole": {"confusion": tab, "rate": rate, "pooled": pooled,
                  "mean_over_worlds": float(np.mean(list(rate.values()))),
                  "passed": pooled >= n["bar_texts"]
                  and all(r >= n["bar_world"] for r in rate.values())
                  and len(rate) == len(WORLDS)},
        "chunks": {"confusion": ctab, "rate_pooled": crate, "rate": crate_text,
                   "mean_over_worlds": float(np.mean(list(crate_text.values()))),
                   "passed": len(crate_text) == len(WORLDS)
                   and float(np.mean(list(crate_text.values()))) >= n["bar_chunks"]
                   and all(r >= n["bar_chunks_world"] for r in crate_text.values())},
        "per_text": per_text,
    }  # fmt: skip


def register_check(sp: Space, cfg: dict) -> dict:
    """The genre confound: build Mesoamerica from one register, place the other."""
    n = cfg["lab"]["inventory"]
    res = {}
    for held, built in (("chronicle", "native"), ("native", "chronicle")):
        mem = members(sp.texts)
        mem["mesoamerica"] = [m for m in mem["mesoamerica"] if sp.texts[m]["register"] == built]
        rows = {}
        for name in members(sp.texts)["mesoamerica"]:
            if sp.texts[name]["register"] != held:
                continue
            sc = cosines(sp.whole[name], sp.profiles(mem))
            chunks = [best(cosines(x, sp.profiles(mem))) for x in sp.chunks.get(name, [])]
            rows[name] = {"placed": best(sc), "scores": sc,
                          "chunks_in_mesoamerica": [sum(c == "mesoamerica" for c in chunks),
                                                    len(chunks)]}  # fmt: skip
        hit = sum(r["placed"] == "mesoamerica" for r in rows.values())
        res[f"{held}_placed_by_{built}_profile"] = {
            "texts": rows,
            "in_mesoamerica": [hit, len(rows)],
            "passed": bool(rows) and hit / len(rows) >= n["bar_register"],
        }
    res["passed"] = all(v["passed"] for v in res.values() if isinstance(v, dict))
    return res


# ------------------------------------------------------------------------------ assembling


def load_counts(cfg: dict) -> dict:
    """Counts for every comparison text: trained, scored-only, and the two library samples."""
    rows = prepare(cfg)
    texts: dict[str, dict] = {}
    extras: dict[str, dict] = {}
    missing: list[str] = []
    for name, world, register, text in rows:
        c = counted(name, text, cfg)
        if c is None:
            missing.append(name)
            continue
        c.update(world=world, register=register)
        (texts if world else extras)[name] = c
    a, b = library_samples(cfg)
    weight_sample = []
    for r in a:
        c = counted(r["work_id"], _library(r), cfg)
        if c is None:
            missing.append(r["work_id"])
        else:
            weight_sample.append(c)
    background = []
    for r in b:
        c = counted(r["work_id"], _library(r), cfg)
        if c is None:
            missing.append(r["work_id"])
            continue
        c.update(world="background", register="library")
        texts[r["work_id"]] = c
        background.append(r["work_id"])
    return {"texts": texts, "extras": extras, "weight_sample": weight_sample, "missing": missing,
            "weight_ids": [r["work_id"] for r in a], "background_ids": background}  # fmt: skip


def rates(c: dict) -> dict:
    """Category rates and origin rates per 10,000 words for one count table."""
    per_cat = {cat: 0 for cat in CATEGORIES}
    per_tag = {"OW": 0, "NW": 0, "NE": 0}
    for lm, k in c["whole"].items():
        if lm not in INDEX:
            continue
        spec = LEX["items"][lm]
        per_cat[spec["category"]] += k
        for tag in spec.get("origin", ()):
            per_tag[tag] += k
    scale = 10000.0 / c["words"]
    return {"category_per_10k": {k: round(v * scale, 2) for k, v in per_cat.items()},
            "origin_per_10k": {k: round(v * scale, 2) for k, v in per_tag.items()},
            "corn_per_10k": round(c["whole"].get("corn", 0) * scale, 2),
            "items_named": sum(1 for lm in c["whole"] if lm in INDEX)}  # fmt: skip


# ------------------------------------------------------------------------------ allowance

CUES = set("call called calls calling name named names termed denominated".split())


def gloss_counts(words: list[str], cfg: dict) -> dict:
    """Old World words of the allowance list used as glossed names, in one text."""
    n = cfg["lab"]["inventory"]
    g, nr = n["gloss_window"], n["near_window"]
    low = [w.lower() for w in words]
    occ = occurrences(words)
    allow = {lm for lm in LEMMAS if LEX["items"][lm].get("allowance")} | {"corn"}
    nw = [p for p, lm in occ if "NW" in LEX["items"].get(lm, {}).get("origin", ())]
    cue = [i for i, w in enumerate(low) if w in CUES]
    res = {"uses": 0, "glossed": 0, "near_new_world_item": 0, "both": 0, "by_item": {}}
    for p, lm in occ:
        if lm not in allow:
            continue
        gl = any(abs(i - p) <= g for i in cue)
        nn = any(abs(q - p) <= nr for q in nw)
        res["uses"] += 1
        res["glossed"] += gl
        res["near_new_world_item"] += nn
        res["both"] += gl and nn
        slot = res["by_item"].setdefault(lm, [0, 0])
        slot[0] += 1
        slot[1] += gl
    res["words"] = len(words)
    return res


def allowance_report(cfg: dict, rows: list) -> dict:
    res: dict = {"texts": {}, "pooled": {}}
    pool: dict[str, dict] = {}
    for name, world, register, text in rows:
        if text is None or world is None:
            continue
        gc = gloss_counts(words_of(text), cfg)
        key = register if world == "mesoamerica" else world
        res["texts"][name] = {"group": key, **{k: v for k, v in gc.items() if k != "by_item"},
                              "glossed_per_10k": round(gc["glossed"] * 1e4 / gc["words"], 3),
                              "uses_per_10k": round(gc["uses"] * 1e4 / gc["words"], 3),
                              "by_item": gc["by_item"]}  # fmt: skip
        p = pool.setdefault(key, {"uses": 0, "glossed": 0, "near": 0, "both": 0, "words": 0})
        p["uses"] += gc["uses"]
        p["glossed"] += gc["glossed"]
        p["near"] += gc["near_new_world_item"]
        p["both"] += gc["both"]
        p["words"] += gc["words"]
    for key, p in pool.items():
        w = p["words"]
        res["pooled"][key] = {
            **p,
            "uses_per_10k": round(p["uses"] * 1e4 / w, 3),
            "glossed_per_10k": round(p["glossed"] * 1e4 / w, 3),
            "glossed_share": round(p["glossed"] / p["uses"], 4) if p["uses"] else None,
            "near_nw_per_10k": round(p["near"] * 1e4 / w, 3),
            "glossed_and_near_nw_per_10k": round(p["both"] * 1e4 / w, 3),
        }
    return res


# ------------------------------------------------------------------------------ absences


def absences(texts: dict[str, dict], bom: dict, bom_words: int, cfg: dict) -> dict:
    n = cfg["lab"]["inventory"]
    mem = members(texts)
    res = {}
    for world, names in mem.items():
        k = len(names)
        absent, only_bom = [], []
        for lm in LEMMAS:
            have = [texts[nm]["whole"].get(lm, 0) > 0 for nm in names]
            share = sum(have) / k
            rate = [texts[nm]["whole"].get(lm, 0) * 1e4 / texts[nm]["words"] for nm in names]
            spec = LEX["items"][lm]
            b = bom["whole"].get(lm, 0)
            if share >= n["absence_share"] and b == 0:
                exp = float(np.median(rate)) * bom_words / 1e4
                absent.append({"item": lm, "category": spec["category"],
                               "origin": sorted(spec.get("origin", [])),
                               "share_of_texts": round(share, 3),
                               "median_rate_per_10k": round(float(np.median(rate)), 3),
                               "expected_in_book": round(exp, 2),
                               "informative": exp >= n["expected_min"]})  # fmt: skip
            if b > 0 and not any(have):
                only_bom.append({"item": lm, "category": spec["category"], "count_in_book": b})
        absent.sort(key=lambda r: -r["expected_in_book"])
        only_bom.sort(key=lambda r: -r["count_in_book"])
        res[world] = {
            "texts": k,
            "common_items": sum(
                1
                for lm in LEMMAS
                if sum(texts[nm]["whole"].get(lm, 0) > 0 for nm in names) / k >= n["absence_share"]
            ),  # fmt: skip
            "absent_from_book": absent,
            "absent_informative": sum(a["informative"] for a in absent),
            "in_book_absent_from_every_text": only_bom,
        }
    return res


# ------------------------------------------------------------------------------ resampling


def resample(sp: Space, x: np.ndarray, prof: dict[str, np.ndarray], cfg: dict,
             items: np.ndarray | None = None) -> dict:  # fmt: skip
    """Item bootstrap: share of draws in which each world is closest, and cosine percentiles."""
    n = cfg["lab"]["inventory"]
    rng = np.random.default_rng(n["seed"])
    idx = np.flatnonzero(sp.mask if items is None else sp.mask * items)
    worlds = list(prof)
    X = x[idx]
    P = np.array([prof[w][idx] for w in worlds])
    draws = rng.integers(0, len(idx), size=(n["bootstrap"], len(idx)))
    M = np.zeros((n["bootstrap"], len(idx)))
    for b in range(n["bootstrap"]):
        M[b] = np.bincount(draws[b], minlength=len(idx))
    num = M @ (P * X).T
    den = np.sqrt(M @ (X**2))[:, None] * np.sqrt(M @ (P**2).T)
    cos = num / np.where(den == 0, 1, den)
    win = cos.argmax(axis=1)
    return {
        "items": int(len(idx)),
        "closest_share": {w: float((win == i).mean()) for i, w in enumerate(worlds)},
        "cosine_2.5_97.5": {
            w: [float(np.percentile(cos[:, i], 2.5)), float(np.percentile(cos[:, i], 97.5))]
            for i, w in enumerate(worlds)
        },  # fmt: skip
    }


# ------------------------------------------------------------------------------ the book


def restricted(x: np.ndarray, prof: dict[str, np.ndarray], keep: np.ndarray) -> dict:
    """Cosines to each world using only the items in ``keep`` (one category)."""
    nrm = np.linalg.norm(x * keep)
    res = {}
    for w, p in prof.items():
        d = np.linalg.norm(p * keep)
        res[w] = float((x * p * keep).sum() / (nrm * d)) if nrm > 0 and d > 0 else None
    return res


def place(sp: Space, name: str, c: dict, texts: dict[str, dict], cfg: dict,
          chunk_ok: bool) -> dict:  # fmt: skip
    """One scored text against every world's profile, whole and by category and by chunk."""
    n = cfg["lab"]["inventory"]
    prof = sp.profiles(members(texts))
    x = sp.vector(c["whole"], c["words"])
    sc = cosines(x, prof)
    got = best(sc)
    boot = resample(sp, x, prof, cfg)
    res = {"name": name, "words": c["words"], "scores": sc, "closest": got,
           "resampled": boot,
           "clear": bool(got and boot["closest_share"][got] >= n["clear_share"])}  # fmt: skip
    cats = {}
    for cat in CATEGORIES:
        km = category_mask(cat)
        s = restricted(x, prof, km)
        b = best(s)
        r = resample(sp, x, prof, cfg, km)
        cats[cat] = {"scores": s, "closest": b, "items_in_list": r["items"],
                     "closest_share": r["closest_share"],
                     "clear": bool(b and r["closest_share"][b] >= n["clear_share"])}  # fmt: skip
    res["by_category"] = cats
    if chunk_ok and c["chunks"]:
        picks = list(range(len(c["chunks"])))
        if len(picks) > n["max_chunks"]:
            picks = sorted(random.Random(f"{n['seed']}-{name}").sample(picks, n["max_chunks"]))
        got_c = [best(cosines(sp.vector(c["chunks"][i], n["chunk_words"]), prof)) for i in picks]
        res["chunks"] = {"n": len(got_c), "placed": {w: got_c.count(w) for w in WORLDS}}
    return res


def item_table(c: dict) -> list[dict]:
    rows = []
    for lm, k in sorted(c["whole"].items(), key=lambda kv: -kv[1]):
        if lm in INDEX:
            spec = LEX["items"][lm]
            rows.append({"item": lm, "category": spec["category"], "count": k,
                         "origin": sorted(spec.get("origin", [])),
                         "allowance": bool(spec.get("allowance"))})  # fmt: skip
        elif lm == "corn":
            rows.append({"item": "corn", "category": "apart", "count": k})
    return rows


def not_classifiable(text: str) -> dict:
    low = [w.lower() for w in TOKEN.findall(text)]
    cnt = Counter(low)
    return {cat: {w: cnt[w] + cnt[w[:-1]] for w in ws}
            for cat, ws in lex.NOT_CLASSIFIABLE.items()}  # fmt: skip


def new_world_check(bom: dict, texts: dict[str, dict]) -> dict:
    """The Book of Mormon's New World-tagged rate against the highest in the other two worlds."""
    res = {"book_per_10k": rates(bom)["origin_per_10k"], "worlds": {}}
    for world in ("near_east", "american", "mesoamerica"):
        r = {nm: rates(t)["origin_per_10k"] for nm, t in texts.items() if t["world"] == world}
        res["worlds"][world] = {tag: {"min": min(v[tag] for v in r.values()),
                                      "max": max(v[tag] for v in r.values()),
                                      "median": float(np.median([v[tag] for v in r.values()]))}
                                for tag in ("OW", "NW", "NE")}  # fmt: skip
    nw = res["book_per_10k"]["NW"]
    res["exceeds_every_near_east_text"] = nw > res["worlds"]["near_east"]["NW"]["max"]
    res["exceeds_every_american_text"] = nw > res["worlds"]["american"]["NW"]["max"]
    res["beyond_both"] = res["exceeds_every_near_east_text"] and res["exceeds_every_american_text"]
    return res


def known_answer(data: dict, cfg: dict) -> dict:
    texts = data["texts"]
    w, df = rarity_weights(data["weight_sample"])
    spaces = {"as_is": Space(texts, w, np.ones(len(LEMMAS)), cfg),
              "with_allowance": Space(texts, w, allowance_mask(), cfg)}  # fmt: skip
    res = {}
    for key, sp in spaces.items():
        res[key] = {"held_out": held_out(sp, cfg), "register": register_check(sp, cfg)}
    return {"spaces": spaces, "weights": w, "df": df, "result": res}


def summary_rows(data: dict, ka: dict, cfg: dict) -> dict:
    """Per-text table of counts and rates for the named texts, plus summaries of the samples."""
    out_: dict = {"named": {}, "background": {}, "scored_only": {}}
    for name, t in data["texts"].items():
        if t["world"] == "background":
            out_["background"][name] = {"words": t["words"], **rates(t)}
            continue
        out_["named"][name] = {"world": t["world"], "register": t["register"],
                               "words": t["words"], **rates(t), "items": item_table(t),
                               "placed_as_is": ka["result"]["as_is"]["held_out"]["per_text"]
                               [name]["placed"]}  # fmt: skip
    for name, t in data["extras"].items():
        out_["scored_only"][name] = {"words": t["words"], **rates(t), "items": item_table(t)}
    return out_


# ------------------------------------------------------------------------------ commands


def lexicon_report() -> dict:
    cats = {c: sum(1 for v in LEX["items"].values() if v["category"] == c) for c in CATEGORIES}
    tags = {t: sum(1 for v in LEX["items"].values() if t in v.get("origin", ())) for t in
            ("OW", "NW", "NE")}  # fmt: skip
    return {
        "items": len(LEMMAS),
        "per_category": cats,
        "forms": len(LEX["forms"]),
        "origin_tagged": tags,
        "allowance_items": [lm for lm in LEMMAS if LEX["items"][lm].get("allowance")],
        "counted_apart": sorted(APART),
        "collisions": LEX["collisions"],
        "removed_before_counting": sorted(lex.EXCLUDE),
        "sha256": lexicon_sha(),
    }


def known_part(data: dict, ka: dict, cfg: dict) -> dict:
    res = {}
    for key, r in ka["result"].items():
        ho = r["held_out"]
        res[key] = {"whole_texts": {k: v for k, v in ho["whole"].items()},
                    "chunks": {k: v for k, v in ho["chunks"].items()},
                    "register": r["register"],
                    "per_text": {nm: t for nm, t in ho["per_text"].items()
                                 if data["texts"][nm]["world"] != "background"}}  # fmt: skip
    return res


def check(cfg: dict) -> dict:
    data = load_counts(cfg)
    ka = known_answer(data, cfg)
    return {"lexicon": lexicon_report(), "not_attempted": data["missing"],
            "known_answer": known_part(data, ka, cfg)}  # fmt: skip


def dropped(names: list[str]) -> np.ndarray:
    m = np.ones(len(LEMMAS))
    for nm in names:
        if nm in INDEX:
            m[INDEX[nm]] = 0.0
    return m


def post_hoc(texts: dict[str, dict], w: np.ndarray, counts: dict[str, dict], cfg: dict) -> dict:
    """POST HOC, chosen after the Book of Mormon's counts were seen: two sensitivity runs in
    which items are dropped from every vector of every text, each with its own check."""
    n = cfg["lab"]["inventory"]
    top = [r["item"] for r in sorted(
        (r for r in item_table(counts["all_text"]) if r["category"] != "apart"),
        key=lambda r: -r["count"])[: n["post_hoc_drop_top"]]]  # fmt: skip
    masks = {"drop_the_books_top_items": top, "drop_polysemous_words": n["post_hoc_polysemous"]}
    res: dict = {"label": "post hoc: item lists chosen after the Book of Mormon was counted"}
    for key, names in masks.items():
        sp = Space(texts, w, dropped(names), cfg)
        ho = held_out(sp, cfg)
        entry = {"dropped_items": names,
                 "known_answer": {"whole_rate": ho["whole"]["rate"],
                                  "whole_pooled": ho["whole"]["pooled"],
                                  "whole_passed": ho["whole"]["passed"],
                                  "chunk_rate": ho["chunks"]["rate"],
                                  "chunks_passed": ho["chunks"]["passed"]},
                 "placed": {}}  # fmt: skip
        for variant, c in counts.items():
            if ho["whole"]["passed"]:
                entry["placed"][variant] = place(
                    sp, "book_of_mormon", c, texts, cfg, ho["chunks"]["passed"]
                )
            else:
                entry["placed"][variant] = "not scored: check missed"
        res[key] = entry
    return res


def run(cfg: dict) -> dict:
    """Known-answer checks first; the Book of Mormon is counted only for the spaces that pass."""
    n = cfg["lab"]["inventory"]
    data = load_counts(cfg)
    ka = known_answer(data, cfg)
    texts = data["texts"]
    res: dict = {"settings": n, "lexicon": lexicon_report(), "not_attempted": data["missing"],
                 "weight_sample_ids": data["weight_ids"],
                 "background_ids": data["background_ids"],
                 "rarity_df": {LEMMAS[i]: int(d) for i, d in enumerate(ka["df"]) if d > 0},
                 "known_answer": known_part(data, ka, cfg),
                 "texts": summary_rows(data, ka, cfg)}  # fmt: skip
    res["translators_allowance"] = allowance_report(cfg, prepare(cfg))
    gate = {k: ka["result"][k]["held_out"]["whole"]["passed"] for k in ka["spaces"]}
    chunk_gate = {k: ka["result"][k]["held_out"]["chunks"]["passed"] for k in ka["spaces"]}
    res["gates"] = {
        "whole_texts_passed": gate,
        "chunks_passed": chunk_gate,
        "register_passed": {k: ka["result"][k]["register"]["passed"] for k in gate},
    }
    if not any(gate.values()):
        res["book_of_mormon"] = "not scored: the held-out check missed its bar"
        return res
    book_all, book_free = bom_text(False), bom_text(True)
    counts = {
        "all_text": counted("book_of_mormon", book_all, cfg),
        "without_quoted_chapters": counted("book_of_mormon_without_quoted", book_free, cfg),
    }
    res["book_of_mormon"] = {
        "words": {k: c["words"] for k, c in counts.items()},
        "inventory": {k: item_table(c) for k, c in counts.items()},
        "rates": {k: rates(c) for k, c in counts.items()},
        "not_classifiable": {
            "all_text": not_classifiable(book_all),
            "without_quoted_chapters": not_classifiable(book_free),
        },
        "placed": {},
        "new_world_check": {},
        "absences": {},
    }
    for variant, c in counts.items():
        res["book_of_mormon"]["new_world_check"][variant] = new_world_check(c, texts)
        res["book_of_mormon"]["absences"][variant] = absences(texts, c, c["words"], cfg)
        for key, sp in ka["spaces"].items():
            if not gate[key]:
                res["book_of_mormon"]["placed"][f"{variant}/{key}"] = "not scored: check missed"
                continue
            res["book_of_mormon"]["placed"][f"{variant}/{key}"] = place(
                sp, "book_of_mormon", c, texts, cfg, chunk_gate[key]
            )
    res["post_hoc"] = post_hoc(texts, ka["weights"], counts, cfg)
    res["scored_only"] = {}
    for name, c in data["extras"].items():
        if gate["as_is"]:
            res["scored_only"][name] = place(
                ka["spaces"]["as_is"], name, c, texts, cfg, chunk_gate["as_is"]
            )
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["lexicon", "counts", "check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "lexicon":
        print(json.dumps(lexicon_report(), indent=1))
        return 0
    if a.cmd == "counts":
        data = load_counts(cfg)
        for k in ("texts", "extras"):
            for name, t in data[k].items():
                print(k, name, t["world"], t["words"], len(t["chunks"]))
        print("not attempted:", data["missing"])
        return 0
    if a.cmd == "check":
        res = check(cfg)
        res["config_sha256"] = config.sha256_of_config()
        out(OUT / "known_answer.json").write_text(json.dumps(res, indent=1) + "\n")
        for key, r in res["known_answer"].items():
            print(key, "whole", {k: r["whole_texts"][k] for k in ("rate", "pooled", "passed")})
            print(key, "chunks", {k: r["chunks"][k] for k in ("rate", "mean_over_worlds",
                                                              "passed")})  # fmt: skip
            print(key, "confusion", json.dumps(r["whole_texts"]["confusion"]))
            print(key, "register", {k: v["in_mesoamerica"] for k, v in r["register"].items()
                                    if isinstance(v, dict)}, r["register"]["passed"])  # fmt: skip
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print("wrote", OUT / "result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
