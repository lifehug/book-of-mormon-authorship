"""The registered grammatical feature list for linguistic dating (BOM-29; 5.3, Amendment 2, 17).

Amendment 2 registers the list as a procedure: drawn from features named in the early modern
English literature, fixed and published before the benchmark, never selected on performance.
This module is that list. Each feature is a count per 1,000 word tokens of a segment; groups and
sources are in ``docs/dating-plan.md``.

**Read the printed text, not the normalised one.** MorphAdorner's standard spellings, applied to
pre-1700 text only (4.3), replace grammatical forms as well as spellings: ``doth`` -> ``does``
1.27 million times, ``saith`` -> ``says``, ``ye`` -> ``you``, ``maketh`` -> ``makes``
(``data/normalization/applied_map.tsv``), while 1780-1830 text keeps them as printed. A grammar
model on the normalised text would see Tudor prose as more modern than it is. So these features
read every period's text with the same orthographic fold and nothing else: lower case, the long s
and ligatures (``ocr_fix.normalize.artifacts``), ``v``/``u`` and ``j``/``i`` merged, ``vv`` ->
``w``. The fold changes letters, never words, and is the same for every date.

No part-of-speech tagger: none is uniform across 1473-1830 print and OCR, so every feature is a
closed word list or a two- or three-word pattern over plain tokens.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

import numpy as np

_TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")


def fold(text: str) -> str:
    """The orthographic fold, identical for every period (letters only, never words)."""
    from ocr_fix.normalize import artifacts

    t = artifacts(text)[0].lower().replace("’", "'")
    return t.replace("vv", "w").replace("v", "u").replace("j", "i")


def tokens(text: str) -> list[str]:
    return _TOKEN.findall(fold(text))


def _f(*words: str) -> frozenset[str]:
    """Word lists are written in modern spelling and folded like the text."""
    return frozenset(fold(w) for w in words)


AUX = _f("am", "is", "are", "was", "were", "be", "been", "being", "art", "wast", "wert",
         "have", "has", "hath", "had", "hast", "hadst", "do", "does", "doth", "did", "dost",
         "didst", "shall", "will", "should", "would", "may", "might", "must", "can", "could",
         "cannot", "shalt", "wilt", "canst", "couldst", "wouldst", "shouldst", "mayest",
         "mayst", "mightest", "mightst", "need", "dare", "ought")  # fmt: skip
PRONOUNS = _f("i", "thou", "he", "she", "it", "we", "ye", "you", "they", "me", "thee", "him",
              "her", "us", "them", "there", "this", "that")  # fmt: skip
BE = _f("am", "is", "are", "was", "were", "be", "been", "art", "wast", "wert")
HAVE = _f("have", "has", "hath", "had", "hast", "hadst")
MUTATIVE = _f("come", "gone", "become", "arrived", "returned", "fallen", "risen", "departed",
              "grown", "passed", "entered", "escaped")  # fmt: skip
SUBORD = _f("if", "though", "although", "lest", "unless", "except", "whether")
ETH_NOT_VERB = _f("teeth", "seth", "beth", "elizabeth", "iapheth", "nazareth", "heth", "kenneth",
                  "lilith", "ashtoreth", "meth", "seueneth")  # fmt: skip
CONTRACTED_NOT = re.compile(r"^[a-z]+n't$")

# (name, group, word set). Single-word features: occurrences per 1,000 tokens.
WORDS: list[tuple[str, str, frozenset[str]]] = [
    ("hath", "verb inflection", _f("hath")),
    ("has", "verb inflection", _f("has")),
    ("doth", "verb inflection", _f("doth")),
    ("does", "verb inflection", _f("does")),
    ("saith", "verb inflection", _f("saith")),
    ("says", "verb inflection", _f("says")),
    (
        "second_person_verb",
        "verb inflection",
        _f(
            "art",
            "wast",
            "wert",
            "hast",
            "hadst",
            "dost",
            "didst",
            "shalt",
            "wilt",
            "canst",
            "couldst",
            "wouldst",
            "shouldst",
            "mayest",
            "mayst",
            "mightest",
            "mightst",
        ),
    ),
    ("thou", "pronoun forms", _f("thou")),
    ("thee", "pronoun forms", _f("thee")),
    ("thy", "pronoun forms", _f("thy")),
    ("thine", "pronoun forms", _f("thine")),
    ("ye", "pronoun forms", _f("ye")),
    ("you", "pronoun forms", _f("you")),
    ("your", "pronoun forms", _f("your")),
    ("its", "pronoun forms", _f("its")),
    ("thereof", "pronoun forms", _f("thereof")),
    (
        "there_adverbs",
        "pronoun forms",
        _f("therein", "thereby", "thereto", "thereunto", "therewith", "thereon", "thereupon"),
    ),
    (
        "where_adverbs",
        "relative clauses",
        _f("whereof", "wherein", "whereby", "whereunto", "wherewith", "whereon", "whereupon"),
    ),
    ("here_adverbs", "pronoun forms", _f("hereof", "herein", "hereby", "hereunto", "herewith")),
    ("wherefore", "relative clauses", _f("wherefore")),
    ("which", "relative clauses", _f("which")),
    ("who", "relative clauses", _f("who")),
    ("whom", "relative clauses", _f("whom")),
    ("whose", "relative clauses", _f("whose")),
    ("that", "relative clauses", _f("that")),
    ("do", "auxiliary patterns", _f("do")),
    ("did", "auxiliary patterns", _f("did")),
    ("shall", "auxiliary patterns", _f("shall")),
    ("will", "auxiliary patterns", _f("will")),
    ("should", "auxiliary patterns", _f("should")),
    ("would", "auxiliary patterns", _f("would")),
    ("may", "auxiliary patterns", _f("may")),
    ("might", "auxiliary patterns", _f("might")),
    ("must", "auxiliary patterns", _f("must")),
    ("can", "auxiliary patterns", _f("can", "cannot")),
    ("could", "auxiliary patterns", _f("could")),
    ("lest", "auxiliary patterns", _f("lest")),
    ("tis_twas", "auxiliary patterns", _f("'tis", "'twas", "tis", "twas")),
    ("unto", "function-word forms", _f("unto")),
    ("upon", "function-word forms", _f("upon")),
    ("amongst", "function-word forms", _f("amongst")),
    ("among", "function-word forms", _f("among")),
    ("whilst", "function-word forms", _f("whilst")),
    ("while", "function-word forms", _f("while")),
    ("betwixt", "function-word forms", _f("betwixt")),
    ("between", "function-word forms", _f("between")),
    ("ere", "function-word forms", _f("ere")),
    ("nor", "function-word forms", _f("nor")),
]
PATTERNS = [
    ("eth_verb", "verb inflection"),             # any other word in -eth: loveth, cometh
    ("thou_st_verb", "verb inflection"),         # thou + word in -st/-est: thou knowest
    ("mine_thine_vowel", "pronoun forms"),       # mine eyes, thine own
    ("my_thy_vowel", "pronoun forms"),           # my eyes, thy own
    ("the_which", "relative clauses"),           # the which
    ("do_not", "auxiliary patterns"),            # do/does/doth/did + not
    ("verb_not", "auxiliary patterns"),          # lexical verb + not: I know not
    ("contracted_not", "auxiliary patterns"),    # don't, can't
    ("be_perfect", "auxiliary patterns"),        # is come, are gone
    ("have_perfect", "auxiliary patterns"),      # has come, have gone
    ("progressive", "auxiliary patterns"),       # is/was + -ing
    ("subjunctive_be", "auxiliary patterns"),    # if it be, though he be
    ("an_h", "function-word forms"),             # an hundred, an house
]  # fmt: skip
NAMES = [n for n, _, _ in WORDS] + [n for n, _ in PATTERNS]
GROUPS = {n: g for n, g, _ in WORDS} | dict(PATTERNS)
# every word a feature reads, so the lexical model can leave them all to this one
GRAMMAR_WORDS = frozenset().union(*(s for _, _, s in WORDS), AUX, BE, HAVE, _f("not", "an"))

_VOWEL = tuple("aeiou")


def counts(toks: Sequence[str]) -> np.ndarray:
    """Raw counts of every feature, in ``NAMES`` order."""
    index = {w: i for i, (_, _, s) in enumerate(WORDS) for w in s}
    out = np.zeros(len(NAMES))
    base = len(WORDS)
    p = {n: base + i for i, (n, _) in enumerate(PATTERNS)}
    prev2, prev = "", ""
    for t in toks:
        i = index.get(t)
        if i is not None:
            out[i] += 1
        if t.endswith("eth") and len(t) >= 5 and t not in ETH_NOT_VERB and t not in index \
                and not t.endswith("ieth"):  # fmt: skip
            out[p["eth_verb"]] += 1
        if prev == "thou" and len(t) >= 4 and t.endswith("st") and t not in index:
            out[p["thou_st_verb"]] += 1
        if t.startswith(_VOWEL):
            if prev in ("mine", "thine"):
                out[p["mine_thine_vowel"]] += 1
            elif prev in ("my", "thy"):
                out[p["my_thy_vowel"]] += 1
        if t == "which" and prev == "the":
            out[p["the_which"]] += 1
        if t == "not":
            if prev in ("do", "does", "doth", "did"):
                out[p["do_not"]] += 1
            elif prev and prev not in AUX and prev not in PRONOUNS:
                out[p["verb_not"]] += 1
        if CONTRACTED_NOT.match(t):
            out[p["contracted_not"]] += 1
        if t in MUTATIVE:
            if prev in BE:
                out[p["be_perfect"]] += 1
            elif prev in HAVE:
                out[p["have_perfect"]] += 1
        if prev in BE and len(t) >= 5 and t.endswith("ing"):
            out[p["progressive"]] += 1
        if t == "be" and prev2 in SUBORD:
            out[p["subjunctive_be"]] += 1
        if prev == "an" and t.startswith("h"):
            out[p["an_h"]] += 1
        prev2, prev = prev, t
    return out


def rates(toks: Sequence[str]) -> np.ndarray:
    """Per 1,000 tokens."""
    return counts(toks) * 1000.0 / max(1, len(toks))
