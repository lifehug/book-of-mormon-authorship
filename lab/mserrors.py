"""BOM-127: are the original manuscript's corrections errors of hearing or of copying?

Skousen (1998) reads the corrections in the original manuscript of the Book of Mormon as mishearings
(sound-alike words, names spelled by ear) and not as copying slips, which would show the text was
dictated. This takes every struck word and every added word recorded in the Joseph Smith Papers
transcripts, classifies each by a written rule (sound-alike, visual slip, anticipation or
perseveration, grammar, spelling, other), proves the classifier on the printer's manuscript (a
copy),
on planted errors in clean text and on the best known pair (Old Testament Revision 1, dictated, and
the pages of Revision 2 that copy it), and only then profiles the original manuscript by scribe
beside the dictated, copied and own-hand writing. A names sub-test follows each non-biblical name
from its first spelling in the original. The test card, written first, is
``data/private/lab/owner/2026-11-20-manuscript-errors/card.md``; settings are
``lab.manuscript_errors`` in the config. The markup is read by ``manuscript.corrections.tokens``
(BOM-34). The public output holds counts and rates, no manuscript words (the transcripts are
copyright Intellectual Reserve); the word-level events go to the private folder.

Rules, in the order applied (first match wins) to each event, with ``D`` the struck words and ``I``
the added words, letters only, lower case:

1. spelling: D and I are the same letters; or the one word struck or added is a single letter.
2. sound-alike: one word for one word, both attested words (King James text or the 1830 edition),
   different letters, equal ``key`` (below). Either form not a word: spelling.
3. visual slip: (a) one word for one word of equal length, differing only at letters that are
   similar in shape (config ``visual_pairs``); (b) a struck run equal to the run just before or just
   after it; (c) an inserted run whose last word equals the word before it, or whose first word
   equals the word after it (an omission between two copies of one word).
4. anticipation or perseveration: the first struck word (``anticipation_min_len`` letters or more)
   occurs within ``window`` words after the event and is not the replacement, or the last struck
   word occurs within ``window`` words before it.
5. grammar: both words are closed-class words (pronouns, auxiliaries, prepositions, determiners,
   conjunctions) or differ by an inflection ending (s es ed d eth th ing est).
6. spelling: one is the start of the other (a restart), or the difflib ratio is at least
   ``spelling_ratio``.
7. other.

``key`` is a metaphone-style rewrite: initial kn gn pn wr wh x; ph ck tch sch ch sh th qu x z; gh
silent (igh gives a long i); c and g softened before e i y; silent final e that lengthens the vowel
before it; vowel digraph classes (ai ay ei ey; ea ee ie; oa oe ow ou; oo ew ue ui); r-coloured
vowels (er ir ur, ear before a consonant, ar or or at the end of a long word) one symbol; ere eir
air
are ear (final) one symbol; o is u before n m v th after a consonant; double consonants single (ff
kept apart: of is not off); a few whole-word respellings (``RESPELL``).

Usage::

    python -m lab.mserrors check     # the four known-answer checks; no Book of Mormon scoring
    python -m lab.mserrors run       # -> data/lab/reruns/manuscript_errors/result.json
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from lab.paths import NOTES, REGISTRY, out
from manuscript.corrections import _PAIRS, _words, tokens
from metadata import config

OUT = REGISTRY / "reruns" / "manuscript_errors"
PRIVATE = NOTES / "owner" / "2026-11-20-manuscript-errors"
ORIGINAL = Path("data/private/bom/jsp_original.jsonl")
PRINTERS = Path("data/private/bom/jsp_printers.jsonl")
DICTATED = Path("data/private/lab/sources/dictated")
CANDIDATES = Path("data/private/candidates")
KJV = Path("data/kjv/kjv.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
CLASSES = ["sound_alike", "visual", "anticipation", "grammar", "spelling", "other"]

# Whole-word respellings applied before the key (spellings the rewrite rules cannot reach).
RESPELL = {
    "to": "too",
    "two": "too",
    "one": "won",
    "through": "threw",
    "great": "grate",
    "break": "brake",
    "steak": "stake",
    "hour": "our",
    "buy": "by",
    "bye": "by",
    "four": "for",
    "passed": "past",
    "tied": "tide",
    "would": "wood",
    "could": "cood",
    "should": "shood",
}
CLOSED = set(
    "a an the this these that those he she it they them their his her my thy me thee we us our ye "
    "you your was were is are am be been has hath have had do doth does did shall will would "
    "should which who whom whose what and but or nor for of to unto in into on upon by with from "
    "at as if then than not no".split()
)
ENDS = {"", "s", "es", "ed", "d", "eth", "th", "ing", "est", "st"}


def letters(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


def key(word: str) -> str:
    """The phonetic key (module docstring)."""
    s = RESPELL.get(letters(word), letters(word))
    if not s:
        return ""
    s = re.sub(r"^(kn|gn|pn)", "n", s)
    s = re.sub(r"^wr", "r", s)
    s = re.sub(r"^wh(?=o)", "h", s)
    s = re.sub(r"^wh", "w", s)
    s = re.sub(r"^x", "s", s)
    s = re.sub(r"^([^aeiouy]+)o(n|m|v|th)(e|er)?$", r"\1u\2\3", s)
    s = s.replace("igh", "I").replace("tch", "C").replace("sch", "sk")
    s = s.replace("ph", "f").replace("ck", "k").replace("dg", "j").replace("qu", "kw")
    s = s.replace("sh", "S").replace("th", "T").replace("ch", "C").replace("gh", "")
    s = s.replace("q", "k").replace("x", "ks").replace("z", "s")
    s = re.sub(r"c(?=[eiy])", "s", s)
    s = s.replace("c", "k")
    s = re.sub(r"g(?=[eiy])", "j", s)
    s = re.sub(r"gn$", "n", s)
    s = re.sub(r"ould", "ud", s)
    s = re.sub(r"ear(?=[^aeiouy])", "R", s)
    s = re.sub(r"(ere|eir|air|are|ear)", "AR", s)
    s = re.sub(r"[eiu]r", "R", s)
    if len(s) > 4:
        s = re.sub(r"(ar|or)$", "R", s)
    s = re.sub(r"y(?![aeiou])(?<!^y)", "i", s)
    s = re.sub(r"(?<=[^aeiouAEIOUy])y$", "I", s)
    s = re.sub(r"(?<=[^aeiou])o$", "O", s)
    long = {"a": "A", "e": "E", "i": "I", "o": "O", "u": "U"}
    s = re.sub(
        r"(?<![aeiou])([aeiou])([^aeiou]{1,2})e$", lambda m: long[m.group(1)] + m.group(2), s
    )
    for a, b in (
        ("ai", "A"),
        ("ay", "A"),
        ("ei", "A"),
        ("ey", "A"),
        ("ea", "E"),
        ("ee", "E"),
        ("ie", "E"),
        ("oa", "O"),
        ("oe", "O"),
        ("ow", "O"),
        ("ou", "O"),
        ("oo", "U"),
        ("ew", "U"),
        ("ue", "U"),
        ("ui", "U"),
        ("oi", "Y"),
        ("oy", "Y"),
        ("au", "W"),
        ("aw", "W"),
    ):
        s = s.replace(a, b)
    s = re.sub(r"(?<=[^aeiou])e$", "", s) if len(s) > 2 else s
    s = s.replace("ff", "F")
    s = re.sub(r"([a-z])\1+", r"\1", s)
    return s


# ----------------------------------------------------------------------------- classification


def wilson(k: int, n: int, z: float) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


class Judge:
    """The classifier, with the vocabulary and the settings from the config."""

    def __init__(self, cfg: dict, vocab: set[str]):
        self.c = cfg["lab"]["manuscript_errors"]
        self.vocab = vocab
        self.pairs = {frozenset(p) for p in self.c["visual_pairs"]}

    def _visual_letters(self, d: str, i: str) -> bool:
        if len(d) != len(i) or d == i:
            return False
        diff = [(a, b) for a, b in zip(d, i, strict=True) if a != b]
        return bool(diff) and all(frozenset(p) in self.pairs for p in diff)

    def _grammar(self, d: str, i: str) -> bool:
        if d in CLOSED and i in CLOSED:
            return True
        stem = 0
        while stem < min(len(d), len(i)) and d[stem] == i[stem]:
            stem += 1
        return stem >= 3 and d[stem:] in ENDS and i[stem:] in ENDS

    def sound(self, d: str, i: str) -> bool:
        return d != i and d in self.vocab and i in self.vocab and key(d) == key(i) != ""

    def near(self, e: dict, order: str = "sound_first") -> str:
        """The class of one event."""
        D, I, bef, aft = e["D"], e["I"], e["before"], e["after"]  # noqa: E741
        w, m = self.c["window"], self.c["anticipation_min_len"]
        one = len(D) == 1 and len(I) == 1
        if e["event"] == "false_start":
            return "spelling"
        if one:
            d, i = D[0], I[0]
            if d == i or len(d) == 1 or len(i) == 1:
                return "spelling"
        if e["event"] == "deletion" and len(D) == 1 and len(D[0]) == 1:
            return "spelling"
        if e["event"] == "insertion" and len(I) == 1 and len(I[0]) == 1:
            return "spelling"

        def anticip() -> bool:
            if not D:
                return False
            d0, d1 = D[0], D[-1]
            ahead = len(d0) >= m and d0 in aft[:w] and not (I and d0 == I[0])
            back = len(d1) >= m and d1 in bef[-w:] and not (I and d1 == I[-1])
            return ahead or back

        if order == "anticipation_first" and anticip():
            return "anticipation"
        if one and self.sound(D[0], I[0]):
            return "sound_alike"
        if one and self._visual_letters(D[0], I[0]):
            return "visual"
        if D and not I:
            n = len(D)
            if (len(bef) >= n and bef[-n:] == D) or (len(aft) >= n and aft[:n] == D):
                return "visual"
        if I and not D:
            if (bef and I[-1] == bef[-1]) or (aft and I[0] == aft[0]):
                return "visual"
        if anticip():
            return "anticipation"
        if one:
            d, i = D[0], I[0]
            if self._grammar(d, i):
                return "grammar"
            if d.startswith(i) or i.startswith(d):
                return "spelling"
            if difflib.SequenceMatcher(None, d, i).ratio() >= self.c["spelling_ratio"]:
                return "spelling"
        return "other"


# ----------------------------------------------------------------------------- extraction


def walk(page: dict, start: str, ctx: int) -> tuple[list[dict], dict[str, int], str]:
    """A page's events (struck words and added words, with context), its words per hand and the
    hand at its end. The hand logic is that of ``manuscript.corrections.events``."""
    hands = [s["name"].replace("  ", " ") for s in page.get("scribes") or []] or [start]
    toks = tokens(page.get("expanded_html") or "")
    notes = sum(k == "scribe" for k, _ in toks)
    seq = [start, *hands] if notes >= len(hands) else hands
    clean: list[str] = []
    nb: list[int] = []
    for kind, txt in toks:
        nb.append(len(clean))
        if kind == "word":
            clean.append(letters(txt))
        elif kind == "ins":
            clean += [letters(w) for w in _words(txt)]
    cur, k_note, js = seq[0], 0, False
    evs: list[dict] = []
    words: Counter = Counter()
    prev_word = ""
    i = 0

    def ev(kind, D, I, hand, at, skip, extra=None):  # noqa: E741
        b = clean[max(0, at - ctx) : at]
        a = clean[at + skip : at + skip + ctx]
        evs.append(
            {"event": kind, "D": D, "I": I, "before": b, "after": a, "hand": hand, **(extra or {})}
        )

    while i < len(toks):
        kind, txt = toks[i]
        hand = "Joseph Smith Jr." if js else cur
        at = nb[i]
        if kind == "scribe":
            k_note += 1
            cur = seq[min(k_note, len(seq) - 1)]
        elif kind == "js":
            js = True
        elif kind == "del":
            d = [letters(w) for w in _words(txt) if letters(w)]
            nxt = toks[i + 1] if i + 1 < len(toks) else ("", "")
            if not d:
                pass
            elif nxt[0] == "ins":
                ins = [letters(w) for w in _words(nxt[1]) if letters(w)]
                ev("substitution", d, ins, hand, at, len(ins))
                i += 1
            elif nxt[0] == "word" and len(d) == 1:
                w = letters(nxt[1])
                if w.startswith(d[0]) and w != d[0]:
                    ev("false_start", d, [w], hand, at, 1)
                elif (
                    difflib.SequenceMatcher(None, d[0], w).ratio() >= 0.5
                    or frozenset((d[0], w)) in _PAIRS
                ):
                    ev("substitution", d, [w], hand, at, 1, {"immediate": True})
                else:
                    ev("deletion", d, [], hand, at, 0)
            else:
                ev("deletion", d, [], hand, at, 0)
        elif kind == "ins":
            ins = [letters(w) for w in _words(txt) if letters(w)]
            words[hand] += len(ins)
            if ins:
                ev("insertion", [], ins, hand, at, len(ins))
        elif kind == "word":
            words[hand] += 1
            prev_word = txt
            js = False if js and txt[-1:] in ".?!" else js
        i += 1
    _ = prev_word
    return evs, dict(words), cur


def read_pages(path: Path) -> list[dict] | None:
    try:
        return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
    except OSError:
        return None  # not attempted


def events_of(pages: list[dict], ctx: int, start: str = "Oliver Cowdery") -> dict:
    """Events and words per hand for a manuscript, in page order."""
    evs, words = [], Counter()
    cur = start
    for p in pages:
        e, w, cur = walk(p, cur, ctx)
        for x in e:
            x["page"] = p["page"]
            evs.append(x)
        words.update(w)
    return {"events": evs, "words": dict(words), "pages": len(pages)}


def vocabulary() -> set[str]:
    v = set()
    for ln in KJV.read_text().splitlines():
        v.update(letters(w) for w in re.findall(r"[A-Za-z]+", json.loads(ln)["text"]))
    for ln in EDITION.read_text().splitlines():
        r = json.loads(ln)
        if r.get("kind") == "body":
            v.update(letters(w) for w in re.findall(r"[A-Za-z]+", r["text"]))
    v.discard("")
    return v


# ----------------------------------------------------------------------------- profiles


def profile(evs: list[dict], words: int, j: Judge, z: float, min_events: int) -> dict:
    cls = Counter()
    alt = Counter()
    subs = Counter()
    subs_alt = Counter()
    by_event = Counter()
    there_their = 0
    for e in evs:
        c = j.near(e)
        if c == "sound_alike" and len(e["D"]) == len(e["I"]) == 1:
            there_their += {e["D"][0], e["I"][0]} == {"there", "their"}
        cls[c] += 1
        by_event[e["event"]] += 1
        a = j.near(e, "anticipation_first")
        alt[a] += 1
        if len(e["D"]) == 1 and len(e["I"]) == 1:
            subs[c] += 1
            subs_alt[a] += 1
    n = sum(subs.values())

    def share(c: Counter, name: str, n_: int) -> dict:
        k = c[name]
        return {
            "k": k,
            "n": n_,
            "share": round(k / n_, 4) if n_ else None,
            "ci": wilson(k, n_, z),
        }

    return {
        "events": len(evs),
        "words": words,
        "events_per_1000_words": round(1000 * len(evs) / words, 2) if words else None,
        "by_event": dict(by_event),
        "classes_all_events": {c: cls[c] for c in CLASSES},
        "one_word_substitutions": n,
        "classes_one_word_substitutions": {c: subs[c] for c in CLASSES},
        "sound_alike": share(subs, "sound_alike", n),
        "visual": share(subs, "visual", n),
        "sound_alike_there_their": there_their,
        "sound_alike_other_pairs": subs["sound_alike"] - there_their,
        "sound_alike_per_1000_words": round(1000 * subs["sound_alike"] / words, 3)
        if words
        else None,
        "visual_events_per_1000_words": round(1000 * cls["visual"] / words, 3) if words else None,
        "sound_alike_anticipation_first": share(subs_alt, "sound_alike", n),
        "enough": n >= min_events,
    }


def fisher_one_sided(a: tuple[int, int], b: tuple[int, int]) -> float | None:
    """P(share in a >= share in b), a and b as (events of the kind, others)."""
    from scipy.stats import fisher_exact

    if sum(a) == 0 or sum(b) == 0:
        return None
    return float(fisher_exact([list(a), list(b)], alternative="greater")[1])


# ----------------------------------------------------------------------------- known answers


def check_key(cfg: dict) -> dict:
    c = cfg["lab"]["manuscript_errors"]
    pos = [tuple(p) for p in c["known_homophones"]]
    neg = [tuple(p) for p in c["known_not_homophones"]]
    hit = [p for p in pos if key(p[0]) == key(p[1])]
    false = [p for p in neg if key(p[0]) == key(p[1])]
    return {
        "homophone_pairs": len(pos),
        "joined": len(hit),
        "recall": round(len(hit) / len(pos), 3),
        "not_joined": [list(p) for p in pos if p not in hit],
        "non_homophone_pairs": len(neg),
        "falsely_joined": len(false),
        "false_rate": round(len(false) / len(neg), 3),
        "falsely_joined_pairs": [list(p) for p in false],
        "passed": len(hit) / len(pos) >= c["key_recall_bar"]
        and len(false) / len(neg) <= c["key_false_bar"],
    }


def plant(cfg: dict, j: Judge) -> dict:
    """Planted errors in clean text (the King James text), by rule; recovery per type."""
    c = cfg["lab"]["manuscript_errors"]
    rng = random.Random(c["seed"])
    base: list[str] = []
    for ln in KJV.read_text().splitlines():
        base += [letters(w) for w in re.findall(r"[A-Za-z]+", json.loads(ln)["text"]) if letters(w)]
    n, W, ctx = c["plants"], c["window"], c["context_words"]
    pos_words: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for a, b in c["known_homophones"]:
        pos_words[a].append((b, a))
        pos_words[b].append((a, b))
    at_pair = [i for i, w in enumerate(base) if w in pos_words]
    vpairs = [tuple(p) for p in c["visual_pairs"]]

    def ctx_of(i: int, k_after: int = 0) -> tuple[list[str], list[str]]:
        return base[max(0, i - ctx) : i], base[i + 1 + k_after : i + 1 + k_after + ctx]

    plants: dict[str, list[dict]] = defaultdict(list)
    for i in rng.sample(at_pair, min(n, len(at_pair))):
        wrong = rng.choice(pos_words[base[i]])[0]
        b, a = ctx_of(i)
        plants["sound_alike"].append(
            {"event": "substitution", "D": [wrong], "I": [base[i]], "before": b, "after": a}
        )
    tries = 0
    while len(plants["omission"]) < n and tries < 200000:
        tries += 1
        i, k = rng.randrange(len(base) - 40), rng.randint(2, 8)
        if base[i] == base[i + k] and len(set(base[i + 1 : i + k + 1])) > 1:
            run = base[i + 1 : i + k + 1]
            plants["omission"].append(
                {
                    "event": "insertion",
                    "D": [],
                    "I": run,
                    "before": base[max(0, i + 1 - ctx) : i + 1],
                    "after": base[i + k + 1 : i + k + 1 + ctx],
                }
            )
    while len(plants["doubled"]) < n:
        i, m = rng.randrange(ctx, len(base) - 40), rng.randint(1, 3)
        run = base[i : i + m]
        plants["doubled"].append(
            {
                "event": "deletion",
                "D": list(run),
                "I": [],
                "before": base[max(0, i + m - ctx) : i + m],
                "after": base[i + m : i + m + ctx],
            }
        )
    vocab = j.vocab
    tries = 0
    while len(plants["letter_confusion"]) < n and tries < 200000:
        tries += 1
        i = rng.randrange(ctx, len(base) - 40)
        w = base[i]
        p = rng.choice(vpairs)
        spots = [k for k, ch in enumerate(w) if ch in p]
        if len(w) < 4 or not spots:
            continue
        k = rng.choice(spots)
        wrong = w[:k] + (p[1] if w[k] == p[0] else p[0]) + w[k + 1 :]
        if wrong in vocab:
            continue
        b, a = ctx_of(i)
        plants["letter_confusion"].append(
            {"event": "substitution", "D": [wrong], "I": [w], "before": b, "after": a}
        )
    tries = 0
    while len(plants["anticipation"]) < n and tries < 200000:
        tries += 1
        i, k = rng.randrange(ctx, len(base) - 40), rng.randint(2, W)
        wrong = base[i + k]
        if len(wrong) < c["anticipation_min_len"] or wrong == base[i]:
            continue
        b, a = ctx_of(i)
        plants["anticipation"].append(
            {"event": "substitution", "D": [wrong], "I": [base[i]], "before": b, "after": a}
        )
    tries = 0
    while len(plants["perseveration"]) < n and tries < 200000:
        tries += 1
        i, k = rng.randrange(ctx, len(base) - 40), rng.randint(1, W)
        wrong = base[i - k]
        if len(wrong) < c["anticipation_min_len"] or wrong == base[i]:
            continue
        b, a = ctx_of(i)
        plants["perseveration"].append(
            {"event": "substitution", "D": [wrong], "I": [base[i]], "before": b, "after": a}
        )
    expected = {
        "sound_alike": "sound_alike",
        "omission": "visual",
        "doubled": "visual",
        "letter_confusion": "visual",
        "anticipation": "anticipation",
        "perseveration": "anticipation",
    }
    res, contamination = {}, {}
    for t, items in plants.items():
        got = Counter(j.near(e) for e in items)
        res[t] = {
            "planted": len(items),
            "expected": expected[t],
            "recovered": got[expected[t]],
            "rate": round(got[expected[t]] / len(items), 3),
            "labelled": dict(got),
        }
        if t != "sound_alike":
            contamination[t] = round(got["sound_alike"] / len(items), 3)
    ok = all(r["rate"] >= c["plant_recovery_bar"] for r in res.values()) and all(
        v <= c["plant_contamination_bar"] for v in contamination.values()
    )
    return {"types": res, "labelled_sound_alike": contamination, "passed": ok}


# ----------------------------------------------------------------------------- the sources


def sources(ctx: int, with_original: bool = True) -> dict[str, dict]:
    """Every manuscript read: events and words per hand; None where a file is missing. The
    original manuscript is read only when ``with_original`` (after the known answers pass)."""
    out_: dict[str, dict] = {}

    def load(name: str, path: Path, start: str = "Oliver Cowdery") -> None:
        pages = read_pages(path)
        out_[name] = events_of(pages, ctx, start) if pages is not None else None

    if with_original:
        load("original", ORIGINAL)
    load("printers", PRINTERS)
    for d in ("ot_revision_1", "ot_revision_2", "abraham_ms_a", "abraham_ms_b", "abraham_ms_c"):
        load(d, DICTATED / d / "pages.jsonl", "Oliver Cowdery" if d == "ot_revision_1" else "")
    load("revelation_book_1", CANDIDATES / "js-1828-1829-revelations.jsonl", "John Whitmer")
    for f in sorted(CANDIDATES.glob("js-*.jsonl")) + sorted(CANDIDATES.glob("t73-*.jsonl")):
        if f.stem == "js-1828-1829-revelations":
            continue
        load(f.stem, f, "Joseph Smith Jr.")
    return out_


def assemble(src: dict[str, dict], cfg: dict) -> dict[str, dict]:
    """Groups of events: each {events, words, by_hand: {hand: {events, words}}}."""
    c = cfg["lab"]["manuscript_errors"]
    copy_hands = set(c["ot_copy_hands"])
    groups: dict[str, dict] = {}

    def add(g: str, s: str, pick=lambda hand: True, tag: str | None = None) -> None:
        d = src.get(s)
        if d is None:
            groups.setdefault(g, {"not_attempted": []})["not_attempted"].append(s)
            return
        G = groups.setdefault(g, {"events": [], "words": 0, "by_hand": {}, "sources": []})
        if "events" not in G:
            return
        G["sources"].append(s)
        for e in d["events"]:
            if pick(e["hand"]):
                G["events"].append({**e, "src": s})
                G["by_hand"].setdefault(e["hand"], {"events": [], "words": 0})["events"].append(e)
        for h, n in d["words"].items():
            if pick(h):
                G["words"] += n
                G["by_hand"].setdefault(h, {"events": [], "words": 0})["words"] += n

    if "original" in src:
        add("original", "original")
    add("printers", "printers")
    add("ot1_dictated", "ot_revision_1")
    add("ot2_copy", "ot_revision_2", lambda h: h in copy_hands)
    add("ot2_other_hands", "ot_revision_2", lambda h: h not in copy_hands)
    own = [s for s in src if s.startswith(("js-", "t73-"))]
    own = [s for s in own if not s.startswith(("js-letterbook", "t73-history", "js-1832-history"))]
    for s in own:
        add("js_own_hand", s, lambda h: h == "Joseph Smith Jr.")
        add("scribe_hands_letters_journals", s, lambda h: h != "Joseph Smith Jr.")
    add("letterbook_1", "js-letterbook-1")
    add("histories_in_scribe_hands", "js-1832-history")
    add(
        "histories_in_scribe_hands",
        "t73-history-1838-1856-volume-a-1-23-december-1805-30-august-1834",
    )
    add("revelation_book_1", "revelation_book_1")
    for k in "abc":
        add(f"abraham_ms_{k}", f"abraham_ms_{k}")
    return groups


def group_profile(G: dict, j: Judge, c: dict) -> dict:
    if "events" not in G:
        return {"not_attempted": G["not_attempted"]}
    res = profile(G["events"], G["words"], j, c["ci_z"], c["min_events"])
    res["sources"] = G["sources"]
    res["by_hand"] = {
        h: profile(v["events"], v["words"], j, c["ci_z"], c["min_events"])
        for h, v in sorted(G["by_hand"].items())
        if v["events"] or v["words"]
    }
    return res


def pooled(groups: dict[str, dict], names: list[str]) -> dict:
    ev, w = [], 0
    for n in names:
        if "events" in groups.get(n, {}):
            ev += groups[n]["events"]
            w += groups[n]["words"]
    return {"events": ev, "words": w}


# ----------------------------------------------------------------------------- names


def printed_names(cfg: dict, vocab_kjv: set[str]) -> dict[str, str]:
    """Printed names of the 1830 text that are not in the King James text: lower -> printed."""
    c = cfg["lab"]["manuscript_errors"]
    caps, lowers = Counter(), set()
    for ln in EDITION.read_text().splitlines():
        r = json.loads(ln)
        if r.get("kind") != "body":
            continue
        for w in re.findall(r"[A-Za-z]+", r["text"]):
            if w[0].isupper():
                caps[w] += 1
            else:
                lowers.add(w.lower())
    names = {}
    for w, n in caps.items():
        lw = w.lower()
        if n >= c["names_min_count"] and lw not in vocab_kjv and lw not in lowers and len(w) > 2:
            names[lw] = w
    return names


def skeleton(w: str) -> str:
    """Consonants only (c as k, ph as f): two spellings with one skeleton differ only in vowels."""
    return re.sub(r"[aeiouy]", "", w.replace("ph", "f").replace("c", "k"))


def name_events(cfg: dict, pages: list[dict], vocab: set[str]) -> dict:
    """Every spelling in a manuscript of a printed non-biblical name, in page order, and the
    struck-for-kept name pairs. A spelling is a word not in the vocabulary, written with a capital
    (or exactly a printed name), within ``names_similarity`` of a printed name; a fragment (the
    start
    of a printed name) is set aside, counted."""
    from rapidfuzz import fuzz, process

    c = cfg["lab"]["manuscript_errors"]
    kjv = set()
    for ln in KJV.read_text().splitlines():
        kjv.update(letters(w) for w in re.findall(r"[A-Za-z]+", json.loads(ln)["text"]))
    names = printed_names(cfg, kjv)
    plain = vocab - set(names)
    keys = list(names)
    cut = c["names_similarity"] * 100
    cache: dict[str, str | None] = {}
    fragments = 0

    def which(lw: str) -> str | None:
        nonlocal fragments
        if lw in names:
            return lw
        if lw not in cache:
            best = process.extractOne(lw, keys, scorer=fuzz.ratio, score_cutoff=cut)
            if any(k.startswith(lw) for k in keys):
                cache[lw] = "fragment"
            else:
                cache[lw] = best[0] if best else None
        return cache[lw]

    seqs: dict[str, list[tuple[str, str]]] = defaultdict(list)
    pairs = []
    for p in pages:
        toks = tokens(p.get("expanded_html") or "")
        for idx, (kind, txt) in enumerate(toks):
            if kind not in ("word", "del", "ins"):
                continue
            status = {"word": "kept", "ins": "kept", "del": "struck"}[kind]
            for w in _words(txt):
                lw = letters(w)
                if not lw or lw in plain or (not w[0].isupper() and lw not in names):
                    continue
                nm = which(lw)
                if nm == "fragment":
                    fragments += 1
                elif nm:
                    seqs[nm].append((lw, status))
            if kind == "del":
                nxt = toks[idx + 1] if idx + 1 < len(toks) else ("", "")
                dw = [letters(w) for w in _words(txt) if letters(w)]
                iw = [letters(w) for w in _words(nxt[1]) if letters(w)] if nxt[0] == "ins" else []
                if nxt[0] == "word":
                    iw = [letters(nxt[1])]
                if len(dw) == 1 and len(iw) == 1:
                    a, b = which(dw[0]), which(iw[0])
                    if a and b and "fragment" not in (a, b) and dw[0] != iw[0]:
                        pairs.append((dw[0], iw[0]))
    return {
        "names": names,
        "seqs": seqs,
        "pairs": pairs,
        "fragments": fragments,
        "excluded": [n for n in c.get("names_exclude", []) if n in names],
    }


def names_test(cfg: dict, pages: list[dict], vocab: set[str], j: Judge) -> dict:
    ne = name_events(cfg, pages, vocab)
    names, seqs, pairs = ne["names"], ne["seqs"], ne["pairs"]
    drop = set(cfg["lab"]["manuscript_errors"].get("names_exclude", []))
    seqs = {n: s for n, s in seqs.items() if n not in drop}

    def kind_of(a: str, b: str) -> str:
        if skeleton(a) == skeleton(b):
            return "vowels_only"
        if j._visual_letters(a, b):
            return "similar_shape_letters"
        return "consonants_differ"

    first_same = first_var = var_later = var_struck = 0
    by_order, by_order_var = Counter(), Counter()
    first_kinds = Counter()
    for nm, seq in seqs.items():
        for k, (s, _st) in enumerate(seq):
            by_order[min(k, 3)] += 1
            by_order_var[min(k, 3)] += s != nm
        s0, st0 = seq[0]
        if s0 == nm:
            first_same += 1
            continue
        first_var += 1
        first_kinds[kind_of(s0, nm)] += 1
        var_later += any(s == nm and st == "kept" for s, st in seq[1:])
        var_struck += st0 == "struck"
    pair_kinds = Counter(kind_of(a, b) for a, b in pairs)
    return {
        "printed_names_not_in_king_james": len(names),
        "names_set_aside_not_names": ne["excluded"],
        "fragments_set_aside": ne["fragments"],
        "names_found": len(seqs),
        "spellings_seen": sum(len(v) for v in seqs.values()),
        "first_spelling_equals_printed": first_same,
        "first_spelling_variant": first_var,
        "first_variant_kinds": dict(first_kinds),
        "of_variant_first_later_kept_as_printed": var_later,
        "of_variant_first_struck_at_once": var_struck,
        "struck_for_kept_name_pairs": len(pairs),
        "struck_for_kept_kinds": dict(pair_kinds),
        "struck_for_kept_equal_phonetic_key": sum(key(a) == key(b) != "" for a, b in pairs),
        "by_order_of_appearance": {
            ["first", "second", "third", "fourth_and_later"][o]: {
                "spellings": by_order[o],
                "not_printed_spelling": by_order_var[o],
                "share": round(by_order_var[o] / by_order[o], 4) if by_order[o] else None,
            }
            for o in range(4)
        },
    }


# ----------------------------------------------------------------------------- the run


def checks(cfg: dict, j: Judge, groups: dict[str, dict]) -> dict:
    c = cfg["lab"]["manuscript_errors"]
    key_chk = check_key(cfg)
    pl = plant(cfg, j)
    pr = group_profile(groups["printers"], j, c)
    a = pr["sound_alike"]
    chk_a = {
        "printers_sound_alike": a,
        "bar": c["printers_sound_max"],
        "passed": a["share"] is not None and a["share"] <= c["printers_sound_max"],
        "printers_classes_one_word_substitutions": pr["classes_one_word_substitutions"],
    }
    d, k = groups["ot1_dictated"], groups["ot2_copy"]
    pd_ = profile(d["events"], d["words"], j, c["ci_z"], c["min_events"])
    pk = profile(k["events"], k["words"], j, c["ci_z"], c["min_events"])
    sd, sk = pd_["sound_alike"], pk["sound_alike"]
    ratio = sd["share"] / sk["share"] if sd["share"] is not None and sk["share"] else None
    p = fisher_one_sided((sd["k"], sd["n"] - sd["k"]), (sk["k"], sk["n"] - sk["k"]))
    few = sd["k"] < c["pair_min_sound"]
    chk_c = {
        "dictated_ot_revision_1": sd,
        "copied_ot_revision_2_pages": sk,
        "ratio_of_shares": None if ratio is None else round(ratio, 2),
        "fisher_p_one_sided": None if p is None else round(p, 5),
        "sound_alike_per_1000_words": {
            "dictated": pd_["sound_alike_per_1000_words"],
            "copied": pk["sound_alike_per_1000_words"],
        },
        "result": "too few"
        if few
        else "met"
        if (ratio is None or ratio >= c["pair_ratio_min"]) and p is not None and p <= c["pair_p"]
        else "missed",
    }
    chk_c["ratio_unavailable_because_copied_has_none"] = ratio is None and sk["k"] == 0
    chk_c["passed"] = chk_c["result"] in ("met", "too few")
    return {
        "key": key_chk,
        "a_printers_manuscript": chk_a,
        "b_planted_errors": pl,
        "c_old_testament_revision_pair": chk_c,
        "all_passed": key_chk["passed"] and chk_a["passed"] and pl["passed"] and chk_c["passed"],
        "pair_validated": chk_c["result"] == "met",
    }


def verdict(groups: dict[str, dict], j: Judge, c: dict) -> dict:
    z, me = c["ci_z"], c["min_events"]
    o = profile(groups["original"]["events"], groups["original"]["words"], j, z, me)
    cop = pooled(groups, ["printers", "ot2_copy", "letterbook_1"])
    dic = pooled(groups, ["ot1_dictated"])
    pc_ = profile(cop["events"], cop["words"], j, z, me)
    pd_ = profile(dic["events"], dic["words"], j, z, me)
    so, sc, sd = o["sound_alike"], pc_["sound_alike"], pd_["sound_alike"]
    if not (o["enough"] and pc_["enough"] and pd_["enough"]):
        v = "cannot tell (a group has too few classified substitutions)"
    elif so["ci"][0] > sc["ci"][1] and so["share"] >= sd["ci"][0]:
        v = "yes: heard-like"
    elif so["ci"][1] < sd["ci"][0] and so["ci"][0] <= sc["ci"][1]:
        v = "no: copy-like"
    else:
        v = "cannot tell"

    def hand(g: str, h: str) -> dict | None:
        d = groups[g]["by_hand"].get(h)
        return profile(d["events"], d["words"], j, z, me) if d else None

    oc, pcw = hand("original", "Oliver Cowdery"), hand("printers", "Oliver Cowdery")
    same = None
    if oc and pcw:
        a_, b_ = oc["sound_alike"], pcw["sound_alike"]
        same = {
            "original": a_,
            "printers": b_,
            "fisher_p_one_sided": fisher_one_sided(
                (a_["k"], a_["n"] - a_["k"]), (b_["k"], b_["n"] - b_["k"])
            ),
            "per_1000_words": {
                "original": oc["sound_alike_per_1000_words"],
                "printers": pcw["sound_alike_per_1000_words"],
            },
            "without_there_their": {
                "original": [oc["sound_alike_other_pairs"], a_["n"]],
                "printers": [pcw["sound_alike_other_pairs"], b_["n"]],
            },
            "note": "added after the first run (not on the card); reported, not part of the rule",
        }

    def narrow(pr: dict) -> dict:
        n_, k_ = pr["one_word_substitutions"], pr["sound_alike_other_pairs"]
        return {
            "k": k_,
            "n": n_,
            "share": round(k_ / n_, 4) if n_ else None,
            "ci": wilson(k_, n_, z),
        }

    so2, sc2, sd2 = narrow(o), narrow(pc_), narrow(pd_)
    if not (o["enough"] and pc_["enough"] and pd_["enough"]):
        v2 = "cannot tell (a group has too few classified substitutions)"
    elif so2["ci"][0] > sc2["ci"][1] and so2["share"] >= sd2["ci"][0]:
        v2 = "yes: heard-like"
    elif so2["ci"][1] < sd2["ci"][0] and so2["ci"][0] <= sc2["ci"][1]:
        v2 = "no: copy-like"
    else:
        v2 = "cannot tell"
    return {
        "verdict": v,
        "post_hoc_verdict_without_there_their": {
            "verdict": v2,
            "original": so2,
            "copied_pool": sc2,
            "dictated_pool": sd2,
            "note": "post hoc: the same rule, there/their left out of the sound-alike count",
        },
        "same_scribe_cowdery_original_against_printers": same,
        "original_without_there_their": [o["sound_alike_other_pairs"], o["one_word_substitutions"]],
        "copied_pool_without_there_their": [
            pc_["sound_alike_other_pairs"],
            pc_["one_word_substitutions"],
        ],
        "original": so,
        "copied_pool": sc,
        "dictated_pool": sd,
        "copied_pool_members": ["printers", "ot2_copy", "letterbook_1"],
        "dictated_pool_members": ["ot1_dictated"],
        "visual_share": {
            "original": o["visual"],
            "copied_pool": pc_["visual"],
            "dictated": pd_["visual"],
        },
        "sound_alike_anticipation_first": {
            "original": o["sound_alike_anticipation_first"],
            "copied_pool": pc_["sound_alike_anticipation_first"],
            "dictated_pool": pd_["sound_alike_anticipation_first"],
        },
    }


def run(cfg: dict, score: bool = True) -> dict:
    c = cfg["lab"]["manuscript_errors"]
    vocab = vocabulary()
    j = Judge(cfg, vocab)
    src = sources(c["context_words"], with_original=False)
    groups = assemble(src, cfg)
    missing = [g for g, v in groups.items() if "events" not in v]
    res: dict = {
        "settings": c,
        "not_attempted": missing,
        "markup_check": {
            s: {"events": len(d["events"]), "words": sum(d["words"].values()), "pages": d["pages"]}
            for s, d in src.items()
            if d and not s.startswith(("js-", "t73-"))
        },
    }
    if missing:
        res["stopped"] = f"sources missing: {missing}"
        return res
    res["known_answers"] = checks(cfg, j, groups)
    res["groups_known"] = {
        g: group_profile(groups[g], j, c) for g in ("printers", "ot1_dictated", "ot2_copy")
    }
    if not score:
        return res
    if not res["known_answers"]["all_passed"]:
        res["stopped"] = "a known-answer check missed its bar; the original was not scored"
        return res
    src.update(sources(c["context_words"], with_original=True))
    groups = assemble(src, cfg)
    res["markup_check"]["original"] = {
        "events": len(src["original"]["events"]),
        "words": sum(src["original"]["words"].values()),
        "pages": src["original"]["pages"],
    }
    private_events(groups, j)
    res["groups"] = {g: group_profile(v, j, c) for g, v in groups.items()}
    res["verdict"] = verdict(groups, j, c)
    ko, kc = (
        res["groups"]["ot2_other_hands"]["sound_alike"],
        res["groups"]["ot2_copy"]["sound_alike"],
    )
    res["post_hoc_ot2_other_hands_against_ot2_copy"] = {
        "note": "post hoc: OT Revision 2 pages not in the copying hand (mode not established "
        "here), against the copy pages",
        "other_hands": ko,
        "copy_pages": kc,
        "fisher_p_one_sided": fisher_one_sided(
            (ko["k"], ko["n"] - ko["k"]), (kc["k"], kc["n"] - kc["k"])
        ),
    }
    res["names"] = names_test(cfg, read_pages(ORIGINAL) or [], vocab, j)
    pm = read_pages(PRINTERS)
    res["names_printers_manuscript_control"] = (
        names_test(cfg, pm, vocab, j) if pm is not None else "not attempted"
    )
    return res


def private_events(groups: dict[str, dict], j: Judge) -> None:
    rows = []
    for g in ("original", "printers", "ot1_dictated", "ot2_copy"):
        for e in groups[g]["events"]:
            rows.append({"group": g, "class": j.near(e), **e})
    out(PRIVATE / "events.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    res = run(cfg, score=a.cmd == "run")
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    if a.cmd == "check":
        print(json.dumps(res.get("known_answers", res), indent=1))
        return 0
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k not in ("groups", "settings")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
