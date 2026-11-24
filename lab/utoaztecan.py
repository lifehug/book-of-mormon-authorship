"""BOM-117: do Uto-Aztecan word lists match Hebrew, Aramaic and Egyptian above chance?

Brian Stubbs (2015) pairs about 1,528 Uto-Aztecan words with Hebrew, Aramaic and Egyptian words
under a table of sound correspondences (his Appendix A) and reads them as a large loan layer. The
test card, written first, is ``data/private/lab/owner/2026-11-22-uto-aztecan-redesign/card.md``;
settings are ``lab.utoaztecan`` in the config. No Book of Mormon text is read.

Step 1, his way (``his-way``): a seeded sample of his sets, read by rule from the private copy of
his book (``data/private/lab/sources/stubbs/``). For each set: does it obey his own table at the
consonant positions he cites, and how many other Hebrew (Strong's) or Coptic lexicon entries
would pass the same table with a meaning at least as close (the size of the search). His wording
and his forms stay in the private tree; the public result holds set numbers and counts.

Step 2, ours (``check``, ``run``): a Kessler permutation test. Every word is reduced to broad
consonant classes (Dolgopolsky's ten); the score is the chi-square of the contingency table of
first-consonant classes across shared meanings (and, second, first plus second consonant); the
null is the same score with one list's meanings shuffled. A known-answer check (an inherited
pair, six contact pairs, eight unrelated pairs, two hard decoys, planted loans) must pass at each
list size before any target pair is scored there.

Usage::

    python -m lab.utoaztecan his-way    # step 1 -> private sample file and public counts
    python -m lab.utoaztecan his-way-judged  # step 1 with the model's readings (simulated)
    python -m lab.utoaztecan check      # known-answer check at every target list size
    python -m lab.utoaztecan run        # both, then targets -> data/lab/setting/uto_aztecan
    python -m lab.utoaztecan vocabulary # his Comparative Vocabulary (lab.utoaztecan_vocab)
    python -m lab.utoaztecan vocabulary-rerun  # one pair per meaning, multi-branch sets
"""

from __future__ import annotations

import argparse
import csv
import functools
import hashlib
import io
import json
import re
import subprocess
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from lab.paths import FAST, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "setting" / "uto_aztecan"
PRIV = NOTES / "owner" / "2026-11-22-uto-aztecan-redesign"
SRC = FAST / "sources" / "wordlists"
STUBBS_PDF = NOTES / "sources" / "stubbs" / "stubbs2015_exploring.pdf"
STUBBS_TXT = PRIV / "stubbs2015.txt"
WOLD = SRC / "lexibank_wold" / "cldf"
NEL = SRC / "lexibank_northeuralex" / "cldf"
GH = SRC / "lexibank_utoaztecan" / "cldf"
ASJP = SRC / "asjp_v21" / "lexibank" / "asjp-v21.zip"
STRONG = SRC / "hebrew_lexicon" / "HebrewStrong.xml"
COPTIC = SRC / "coptic_lexicon_v1.2_2020.xml"
CLICS = SRC / "clics3_network.gml.zip"
WLC = FAST / "sources" / "translation" / "morphhb" / "wlc"

# ---------------------------------------------------------------------------------------------
# Sound classes (Dolgopolsky 1964; the ten used by Turchin, Peiros and Gell-Mann 2010)

CLASSES = ["P", "T", "S", "K", "M", "N", "R", "W", "J", "0"]
NONE = len(CLASSES)  # no second consonant
_IPA = {}
for _cls, _chars in {
    "P": "pbfvɸβɓ",
    "T": "tdθðʈɖɗ",
    "S": "szʃʒɕʑʂʐ",
    "K": "kgqɢxɣχʁcɟçʝɠ",
    "M": "mɱ",
    "N": "nɲŋɳɴ",
    "R": "rlɾɹɻʀɭʎɽɫɬɮʟ",
    "W": "wʋɥʍɰ",
    "J": "j",
    "0": "hɦʔʕħʜʡ",
}.items():
    for _c in _chars:
        _IPA[_c] = _cls
_IPA_VOWELS = set("aeiouyɑɐæɛəɜɪɨʉɔøœɒʊʏɯɤɵɘɞʌɶɚäëïöüı")
_SIBILANT = set("szʃʒɕʑʂʐ")


def ipa_class(segment: str) -> str | None:
    """Class of one IPA segment: a letter of ``CLASSES``, "V" for a vowel, None if unreadable."""
    base = unicodedata.normalize("NFD", segment)
    for i, ch in enumerate(base):
        low = ch.lower()
        if low in _IPA_VOWELS:
            return "V"
        if low in _IPA:
            cls = _IPA[low]
            if cls == "T" and any(c in _SIBILANT for c in base[i + 1 :]):
                return "S"  # affricates (ts, tʃ, dʒ) go with the sibilants
            return cls
    return None


def first_two(classes: list[str]) -> tuple[int, int] | None:
    """(first, second) consonant class indexes; an initial vowel counts as class 0 (laryngeal)."""
    seq = [c for c in classes if c is not None]
    if not seq:
        return None
    if seq[0] == "V":
        c1 = CLASSES.index("0")
        rest = seq[1:]
    else:
        c1 = CLASSES.index(seq[0])
        rest = seq[1:]
    c2 = next((CLASSES.index(c) for c in rest if c != "V"), NONE)
    return c1, c2


def ipa_word(segments: str) -> tuple[int, int] | None:
    return first_two([ipa_class(s) for s in segments.split() if s not in ("+", "_", "#")])


# Stubbs-style symbols (his transliteration of Semitic and Egyptian) to classes.
SYMBOL_CLASS = {
    "’": "0", "ʕ": "0", "ġ": "0", "h": "0", "ђ": "0", "x": "K",
    "b": "P", "p": "P", "f": "P",
    "t": "T", "d": "T", "ṭ": "T", "θ": "S", "đ": "T",
    "s": "S", "š": "S", "ś": "S", "ṣ": "S", "z": "S", "c": "S",
    "k": "K", "g": "K", "q": "K",
    "m": "M", "n": "N", "ŋ": "N", "l": "R", "r": "R", "w": "W", "y": "J",
}  # fmt: skip


def symbols_class(symbols: list[str]) -> tuple[int, int] | None:
    return first_two([SYMBOL_CLASS.get(s) for s in symbols]) if symbols else None


# Hebrew letters to symbols. Shin and sin are told apart by their dots; a vav or yod that only
# carries a vowel (holam, shuruq, or yod after i/e vowels) is a vowel letter, not a consonant.
_HEB = {
    "א": "’", "ב": "b", "ג": "g", "ד": "d", "ה": "h", "ו": "w", "ז": "z", "ח": "ђ", "ט": "ṭ",
    "י": "y", "כ": "k", "ך": "k", "ל": "l", "מ": "m", "ם": "m", "נ": "n", "ן": "n", "ס": "s",
    "ע": "ʕ", "פ": "p", "ף": "p", "צ": "ṣ", "ץ": "ṣ", "ק": "q", "ר": "r", "ש": "š", "ת": "t",
}  # fmt: skip
_SHIN, _SIN, _HOLAM, _DAGESH = "ׁ", "ׂ", "ֹ", "ּ"
_I_E = {"ִ", "ֵ", "ֶ"}  # hiriq, tsere, segol
_POINTS = re.compile(r"[֑-ׇ]")


def hebrew_symbols(word: str) -> list[str]:
    """Consonant symbols of a pointed Hebrew word, in order."""
    units: list[tuple[str, str]] = []
    for ch in word:
        if ch in _HEB:
            units.append((ch, ""))
        elif _POINTS.match(ch) and units:
            units[-1] = (units[-1][0], units[-1][1] + ch)
    out_: list[str] = []
    for i, (letter, marks) in enumerate(units):
        own_vowel = any(m not in (_SHIN, _SIN, _DAGESH, "ֽ") for m in marks)
        if i > 0 and letter == "ו" and (_HOLAM in marks or (_DAGESH in marks and not own_vowel)):
            continue
        prev = units[i - 1][1] if i > 0 else ""
        if i > 0 and letter == "י" and not own_vowel and any(v in prev for v in _I_E):
            continue
        sym = _HEB[letter]
        if letter == "ש" and _SIN in marks:
            sym = "ś"
        out_.append(sym)
    return out_


# Coptic letters to symbols (Sahidic values).
_COP = {
    "ⲃ": "b", "ⲅ": "g", "ⲇ": "d", "ⲍ": "z", "ⲑ": "t", "ⲕ": "k", "ⲗ": "l", "ⲙ": "m", "ⲛ": "n",
    "ⲝ": "k", "ⲡ": "p", "ⲣ": "r", "ⲥ": "s", "ⲧ": "t", "ⲫ": "p", "ⲭ": "k", "ⲯ": "p", "ϣ": "š",
    "ϥ": "f", "ϧ": "x", "ϩ": "h", "ϫ": "c", "ϭ": "q", "ϯ": "t",
}  # fmt: skip
_COP_V = set("ⲁⲉⲏⲓⲟⲩⲱ")


def coptic_symbols(word: str) -> list[str]:
    """Consonant symbols of a Coptic word; ⲟⲩ and ⲓ before a vowel are w and y."""
    w = "".join(c for c in unicodedata.normalize("NFD", word.lower()) if c in _COP or c in _COP_V)
    syms, i = [], 0
    while i < len(w):
        ch = w[i]
        if ch == "ⲟ" and w[i + 1 : i + 2] == "ⲩ":
            if w[i + 2 : i + 3] and w[i + 2] in _COP_V:
                syms.append("w")
            i += 2
            continue
        if ch == "ⲓ" and i == 0 and w[1:2] and w[1] in _COP_V:
            syms.append("y")
        elif ch in _COP:
            syms.append(_COP[ch])
        i += 1
    return syms


# ---------------------------------------------------------------------------------------------
# The permutation test


def _chi2_rows(a: np.ndarray, bp: np.ndarray, ka: int, kb: int) -> np.ndarray:
    """Chi-square of the a-by-b contingency table for each row of ``bp`` (rows of b classes)."""
    s, n = bp.shape
    codes = (np.arange(s)[:, None] * (ka * kb) + a[None, :] * kb + bp).ravel()
    obs = np.bincount(codes, minlength=s * ka * kb).reshape(s, ka, kb).astype(float)
    ra = obs.sum(axis=2)  # (s, ka)
    cb = obs.sum(axis=1)  # (s, kb)
    exp = ra[:, :, None] * cb[:, None, :] / n
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(exp > 0, obs * obs / exp, 0.0)
    return terms.sum(axis=(1, 2)) - n


def chi2(a, b, ka: int = NONE + 1, kb: int = NONE + 1) -> float:
    return float(_chi2_rows(np.asarray(a), np.asarray(b)[None, :], ka, kb)[0])


def perm_test(a, b, shuffles: int, rng: np.random.Generator, second=None, chunk: int = 1000):
    """Kessler's test: observed chi-square and its permutation p (b's meanings shuffled).

    ``a`` and ``b`` are class indexes of the first consonant over shared meanings; ``second``,
    if given, is a pair of second-consonant arrays, and the second score (first plus second
    consonant) uses the same permutations. Returns a dict of scores, p-values and null moments.
    """
    a, b = np.asarray(a), np.asarray(b)
    k = NONE + 1
    obs1 = chi2(a, b, k, k)
    obs2 = None
    if second is not None:
        a2, b2 = np.asarray(second[0]), np.asarray(second[1])
        obs2 = obs1 + chi2(a2, b2, k, k)
    ge1 = ge2 = 0
    null = []
    done = 0
    while done < shuffles:
        s = min(chunk, shuffles - done)
        idx = rng.permuted(np.broadcast_to(np.arange(len(b)), (s, len(b))), axis=1)
        n1 = _chi2_rows(a, b[idx], k, k)
        ge1 += int((n1 >= obs1 - 1e-9).sum())
        null.append(n1)
        if obs2 is not None:
            n2 = n1 + _chi2_rows(a2, b2[idx], k, k)
            ge2 += int((n2 >= obs2 - 1e-9).sum())
        done += s
    null = np.concatenate(null)
    res = {
        "n": int(len(a)),
        "score": round(obs1, 3),
        "p": (ge1 + 1) / (shuffles + 1),
        "null_mean": round(float(null.mean()), 3),
        "null_sd": round(float(null.std()), 3),
        "z": round(float((obs1 - null.mean()) / null.std()) if null.std() > 0 else 0.0, 3),
    }
    if obs2 is not None:
        res |= {"score_two": round(obs2, 3), "p_two": (ge2 + 1) / (shuffles + 1)}
    return res


def multi_perm_test(varieties: list[tuple[np.ndarray, np.ndarray]], donor: np.ndarray,
                    shuffles: int, rng: np.random.Generator, chunk: int = 500) -> dict:  # fmt: skip
    """Kessler and Lehtonen's sum: one donor list against many varieties at once.

    ``donor`` holds the donor's first-consonant class for every meaning of the shared frame;
    each variety is (mask over the frame, its classes on the masked meanings). The donor is
    permuted over the frame once per shuffle, the same permutation for every variety.
    """
    k = NONE + 1

    def score(dperm: np.ndarray) -> np.ndarray:
        total = np.zeros(dperm.shape[0])
        for mask, cls in varieties:
            total += _chi2_rows(cls, dperm[:, mask], k, k)
        return total

    obs = float(score(donor[None, :])[0])
    ge, null, done = 0, [], 0
    while done < shuffles:
        s = min(chunk, shuffles - done)
        idx = rng.permuted(np.broadcast_to(np.arange(len(donor)), (s, len(donor))), axis=1)
        n = score(donor[idx])
        ge += int((n >= obs - 1e-9).sum())
        null.append(n)
        done += s
    null = np.concatenate(null)
    return {
        "n": int(len(donor)),
        "varieties": len(varieties),
        "score": round(obs, 3),
        "p": (ge + 1) / (shuffles + 1),
        "null_mean": round(float(null.mean()), 3),
        "null_sd": round(float(null.std()), 3),
        "z": round(float((obs - null.mean()) / null.std()) if null.std() > 0 else 0.0, 3),
    }


def holm(ps: dict[str, float]) -> dict[str, float]:
    """Holm-adjusted p-values (step-down, monotone)."""
    order = sorted(ps, key=ps.get)
    m, adj, run = len(order), {}, 0.0
    for i, key in enumerate(order):
        run = max(run, min(1.0, (m - i) * ps[key]))
        adj[key] = run
    return adj


def plant(a1, a2, b1, b2, k: int, rng: np.random.Generator):
    """Copies of b's classes with k meanings replaced by a regular non-identical correspondence.

    A random permutation of the classes with no fixed point maps each planted word's first and
    second consonant classes from list a: every planted "loan" changes its sounds, but always
    the same way (Latin p to English f, not p to p).
    """
    n = len(a1)
    while True:
        sigma = rng.permutation(len(CLASSES))
        if not np.any(sigma == np.arange(len(CLASSES))):
            break
    sigma = np.append(sigma, NONE)  # "no second consonant" stays itself
    pick = rng.choice(n, size=min(k, n), replace=False)
    nb1, nb2 = np.array(b1).copy(), np.array(b2).copy()
    nb1[pick] = sigma[np.asarray(a1)[pick]]
    nb2[pick] = sigma[np.asarray(a2)[pick]]
    return nb1, nb2


# ---------------------------------------------------------------------------------------------
# Word lists. A list is {concepticon_id: (c1, c2)}; meaning keys are Concepticon IDs throughout.


def _csv(path: Path | io.TextIOBase) -> list[dict]:
    if isinstance(path, Path):
        with path.open(encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))
    return list(csv.DictReader(path))


def _params(rows: list[dict]) -> dict[str, str]:
    return {r["ID"]: r["Concepticon_ID"] for r in rows if r.get("Concepticon_ID")}


def _cldf_lists(forms: list[dict], params: dict[str, str], lang: str,
                drop=None) -> dict[str, tuple[int, int]]:  # fmt: skip
    """First usable form per Concepticon meaning, in the dataset's own order."""
    res: dict[str, tuple[int, int]] = {}
    for r in forms:
        if r["Language_ID"] != lang or r["Parameter_ID"] not in params:
            continue
        cid = params[r["Parameter_ID"]]
        if cid in res or (drop and drop(r)):
            continue
        cls = ipa_word(r.get("Segments") or "")
        if cls is not None:
            res[cid] = cls
    return res


class Data:
    """Every list the test uses, loaded once; a missing source is recorded, never a zero."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.missing: list[str] = []
        self.cache: dict[str, dict] = {}
        self._wold = self._nel = self._asjp = self._gh = None
        self.concept_keys, self.concept_names = self._concept_index()

    # -- sources --
    def wold(self):
        if self._wold is None:
            params = _csv(WOLD / "parameters.csv")
            self._wold = (_csv(WOLD / "forms.csv"), _params(params), params)
        return self._wold

    def nel(self):
        if self._nel is None:
            self._nel = (_csv(NEL / "forms.csv"), _params(_csv(NEL / "parameters.csv")))
        return self._nel

    def asjp(self):
        if self._asjp is None:
            with zipfile.ZipFile(ASJP) as z:
                root = next(n for n in z.namelist() if n.endswith("cldf/forms.csv"))[
                    : -len("forms.csv")
                ]
                read = lambda n: _csv(io.TextIOWrapper(z.open(root + n), encoding="utf-8"))  # noqa: E731
                forms = [r for r in read("forms.csv") if r["Language_ID"] in self._asjp_langs()]
                self._asjp = (forms, _params(read("parameters.csv")))
        return self._asjp

    def _asjp_langs(self) -> set[str]:
        u = self.cfg["lab"]["utoaztecan"]
        specs = [s for pair in u["targets"].values() for s in pair]
        return {s.split(":", 1)[1] for s in specs if s.startswith("asjp:")}

    def gh(self):
        if self._gh is None:
            self._gh = (_csv(GH / "forms.csv"), _params(_csv(GH / "parameters.csv")))
        return self._gh

    def borrowed_score(self) -> dict[str, float]:
        """WOLD's borrowing score per Concepticon meaning (Tadmor, Haspelmath and Taylor 2010)."""
        return {
            r["Concepticon_ID"]: float(r["Borrowed_score"])
            for r in self.wold()[2]
            if r.get("Concepticon_ID") and r.get("Borrowed_score")
        }

    # -- the meaning index used to map lexicon glosses --
    def _concept_index(self) -> tuple[dict[str, str], dict[str, str]]:
        names: dict[str, set[str]] = defaultdict(set)
        label: dict[str, str] = {}
        tables = [WOLD / "parameters.csv", NEL / "parameters.csv", GH / "parameters.csv"]
        for path in tables:
            if not path.exists():
                continue
            for r in _csv(path):
                cid = r.get("Concepticon_ID")
                if not cid:
                    continue
                label.setdefault(cid, r.get("Concepticon_Gloss", ""))
                for text in (r.get("Name", ""), r.get("Concepticon_Gloss", "")):
                    for key in gloss_keys(text):
                        names[key].add(cid)
        keys = {k: next(iter(v)) for k, v in names.items() if len(v) == 1}
        return keys, label

    # -- one list --
    def get(self, spec: str) -> dict[str, tuple[int, int]] | None:
        """The list named ``spec`` ("nel:fin", "wold:Yaqui+loans", "oshl:heb" ...), or None."""
        if spec in self.cache:
            return self.cache[spec]
        src, _, lang = spec.partition(":")
        try:
            res = self._get(src, lang)
        except (OSError, KeyError, StopIteration, zipfile.BadZipFile) as exc:
            self.missing.append(f"{spec}: {type(exc).__name__}")
            res = None
        self.cache[spec] = res
        return res

    def _get(self, src: str, lang: str):
        u = self.cfg["lab"]["utoaztecan"]
        if src == "wold":
            forms, params, _ = self.wold()
            keep_loans = lang.endswith("+loans")
            lang = lang.removesuffix("+loans")
            loans = set(u["loan_values"])
            drop = None if keep_loans else (lambda r: r.get("Borrowed") in loans)
            return _cldf_lists(forms, params, lang, drop)
        if src == "nel":
            return _cldf_lists(*self.nel(), lang)
        if src == "asjp":
            return _cldf_lists(*self.asjp(), lang)
        if src in ("oshl", "cdo"):
            pairs = ((cid, symbols_class(e["symbols"])) for cid, e in self.lexicon_map(src).items())
            return {cid: cls for cid, cls in pairs if cls is not None}
        raise KeyError(src)

    def greenhill(self) -> dict[str, dict[str, tuple[int, int]]]:
        forms, params = self.gh()
        langs = sorted({r["Language_ID"] for r in forms})
        return {lang: _cldf_lists(forms, params, lang) for lang in langs}

    # -- lexicons mapped to meanings by rule (gloss equals a meaning's name) --
    def lexicon_map(self, which: str) -> dict[str, dict]:
        key = f"_map_{which}"
        if key not in self.cache:
            entries = strong_entries() if which == "oshl" else coptic_entries()
            self.cache[key] = map_lexicon(entries, self.concept_keys)
        return self.cache[key]


# ---------------------------------------------------------------------------------------------
# Glosses

_STOP = set(
    "a an the to of or and be is as in on at by for with from into s.th s.o one's oneself "
    "something someone it its his her their that this which who vi vt n v adj adv pl sg".split()
)


def gloss_keys(text: str) -> list[str]:
    """Normalised names of a meaning or gloss: lower case, no article or "to", split on "or"."""
    t = re.sub(r"\([^)]*\)", " ", (text or "").lower())
    keys = []
    for part in re.split(r"\s+or\s+|[,;/]", t):
        part = re.sub(r"[^a-z' -]", " ", part)
        part = re.sub(r"^\s*(the|to|a|an|be)\s+", "", part.strip())
        part = re.sub(r"\s+", " ", part).strip(" '-")
        if part:
            keys.append(part)
    return keys


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > 4 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z]+", re.sub(r"\[[^]]*\]", " ", (text or "").lower()))
    return {_stem(w) for w in words if w not in _STOP and len(w) > 1}


def strong_entries() -> list[dict]:
    """Strong's Hebrew entries (no proper names, Hebrew only): number, symbols, glosses, use."""
    text = STRONG.read_text(encoding="utf-8")
    freq = wlc_frequency()
    rows = []
    for m in re.finditer(r'<entry id="H(\d+)">(.*?)</entry>', text, re.S):
        num, body = int(m.group(1)), m.group(2)
        w = re.search(r'<w pos="([^"]*)"[^>]*xml:lang="heb"[^>]*>([^<]+)</w>', body)
        if not w or w.group(1).startswith("n-pr"):
            continue
        defs = [re.sub(r"<[^>]+>", "", d).strip() for d in re.findall(r"<def>(.*?)</def>", body)]
        if not defs:
            continue
        rows.append(
            {
                "id": f"H{num}",
                "symbols": hebrew_symbols(w.group(2)),
                "glosses": defs,
                "rank": -freq.get(num, 0),
            }
        )
    return rows


def wlc_frequency() -> dict[int, int]:
    """Occurrences of each Strong's number in the Westminster Leningrad Codex (morphhb)."""
    counts: Counter = Counter()
    if not WLC.exists():
        return {}
    for path in sorted(WLC.glob("*.xml")):
        for lemma in re.findall(r'lemma="([^"]+)"', path.read_text(encoding="utf-8")):
            for part in lemma.split("/"):
                num = re.match(r"\s*(\d+)", part)
                if num:
                    counts[int(num.group(1))] += 1
    return dict(counts)


def coptic_entries() -> list[dict]:
    """Coptic Dictionary Online entries: Sahidic lemma symbols and English glosses."""
    text = COPTIC.read_text(encoding="utf-8")
    rows = []
    for n, m in enumerate(
        re.finditer(r'<entry[^>]*xml:id="(C\d+)"[^>]*>(.*?)</entry>', text, re.S)
    ):
        body = m.group(2)
        lemma = re.search(r'<form type="lemma"[^>]*>(.*?)</form>', body, re.S)
        if not lemma:
            continue
        orth = re.search(r"<orth>([^<]+)</orth>", lemma.group(1))
        if not orth or orth.group(1).strip().endswith("-") or orth.group(1).startswith("-"):
            continue
        senses = re.findall(r"<sense[^>]*>(.*?)</sense>", body, re.S)
        glosses = []
        for s in senses:
            glosses += [q.strip() for q in re.findall(r'<quote xml:lang="en">([^<]*)</quote>', s)]
        glosses = [g for g in glosses if g]
        if not glosses:
            continue
        rows.append(
            {
                "id": m.group(1),
                "symbols": coptic_symbols(orth.group(1)),
                "glosses": glosses,
                "rank": n,
            }
        )
    return rows


def map_lexicon(entries: list[dict], keys: dict[str, str]) -> dict[str, dict]:
    """One lexicon entry per meaning: a gloss must equal the meaning's name exactly.

    Among entries that qualify, one whose first gloss matches is preferred, then the more
    frequent (Hebrew: occurrences in the Hebrew Bible; Coptic: dictionary order).
    """
    best: dict[str, tuple] = {}
    for e in entries:
        if not e["symbols"]:
            continue
        for gi, g in enumerate(e["glosses"]):
            for key in gloss_keys(g):
                cid = keys.get(key)
                if cid is None:
                    continue
                rank = (gi > 0, e["rank"], e["id"])
                if cid not in best or rank < best[cid][0]:
                    best[cid] = (rank, e, g)
    return {cid: {**e, "matched": g} for cid, (_, e, g) in best.items()}


# ---------------------------------------------------------------------------------------------
# CLICS: meanings expressed by one word in several families (colexification)


def clics_graph(min_families: int) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(gloss key -> concept ids, concept id -> linked concept ids) from the CLICS3 network."""
    with zipfile.ZipFile(CLICS) as z:
        name = next(n for n in z.namelist() if n.endswith(".gml"))
        text = z.read(name).decode("utf-8")
    nodes, keyed = {}, defaultdict(set)
    for m in re.finditer(r'node \[\s*id (\d+)\s*label "(\d+)"\s*ID "\d+"\s*Gloss "([^"]*)"', text):
        nodes[m.group(1)] = m.group(2)
        for key in gloss_keys(m.group(3)):
            keyed[key].add(m.group(2))
    links = defaultdict(set)
    for m in re.finditer(r"edge \[\s*source (\d+)\s*target (\d+)(.*?)\n  \]", text, re.S):
        fam = re.search(r"FamilyWeight (\d+)", m.group(3))
        if fam and int(fam.group(1)) >= min_families:
            a, b = nodes.get(m.group(1)), nodes.get(m.group(2))
            if a and b:
                links[a].add(b)
                links[b].add(a)
    return dict(keyed), dict(links)


def concepts_of(gloss: str, keyed: dict[str, set[str]]) -> set[str]:
    """CLICS concepts a gloss names: a whole gloss phrase, or one of its words, equals a concept."""
    res: set[str] = set()
    for key in gloss_keys(gloss):
        res |= keyed.get(key, set())
        for w in key.split():
            if w not in _STOP:
                res |= keyed.get(w, set())
    return res


def closeness(g1: str, g2: str, keyed, links) -> int:
    """0 = the glosses share a content word; 1 = colexified in CLICS; 2 = neither (looser)."""
    if content_words(g1) & content_words(g2):
        return 0
    c1, c2 = concepts_of(g1, keyed), concepts_of(g2, keyed)
    if c1 & c2 or any(links.get(c, set()) & c2 for c in c1):
        return 1
    return 2


# ---------------------------------------------------------------------------------------------
# Step 1: Stubbs's sets, his way


def stubbs_text() -> list[str]:
    """The private plain text of Stubbs 2015 (made from the PDF on first use)."""
    if not STUBBS_TXT.exists():
        subprocess.run(["pdftotext", "-layout", str(STUBBS_PDF), str(out(STUBBS_TXT))], check=True)
    return STUBBS_TXT.read_text(encoding="utf-8").replace("\f", "").split("\n")


_HEAD = re.compile(r"^\s{0,12}(\d{1,4}) +[A-Za-z(*’ʕђ]")
_CHAPTERS = [
    (2, "kw", r"^2 The Semitic-kw Contribution into Uto-Aztecan\s*$"),
    (3, None, r"^3 The Pronouns of Uto-Aztecan\s*$"),
    (4, "e", r"^4 The Egyptian in Uto-Aztecan\s*$"),
    (5, "p", r"^5 The Semitic-p Contribution in Uto-Aztecan\s*$"),
    (6, None, r"^6 Seven Uto-Aztecan Puzzles"),
]


def _find(lines: list[str], pattern: str, start: int = 0) -> int:
    rx = re.compile(pattern)
    return next(i for i in range(start, len(lines)) if rx.search(lines[i]))


def parse_sets(lines: list[str]) -> dict[int, dict]:
    """Every numbered set: its chapter and lines. Numbers must run in order (gaps up to 3)."""
    bounds = []
    for ch, stratum, pat in _CHAPTERS:
        try:
            bounds.append((_find(lines, pat, 1000), ch, stratum))
        except StopIteration:
            continue
    start, end = bounds[0][0], bounds[-1][0]
    heads, last = [], 0
    for i in range(start, end):
        m = _HEAD.match(lines[i])
        if m and last < int(m.group(1)) <= last + 3:
            last = int(m.group(1))
            heads.append((i, last))
    sets = {}
    for j, (i, num) in enumerate(heads):
        stop = heads[j + 1][0] if j + 1 < len(heads) else end
        ch = max((b for b in bounds if b[0] <= i), key=lambda b: b[0])
        sets[num] = {"set": num, "chapter": ch[1], "chapter_stratum": ch[2], "lines": lines[i:stop]}
    return sets


_TAG = re.compile(r"\[([^\]]*\d[^\]]*)\]")
_CODE = re.compile(r"^(kw|p|e)-?(\d)-?(.+)$")


def codes_of(body: str) -> tuple[str | None, dict[int, str]]:
    """His consonant tags ([p1b,p2r,p3q]): the stratum and Near Eastern consonant per position."""
    strata, pos = Counter(), {}
    for tag in _TAG.findall(body):
        for item in tag.split(","):
            m = _CODE.match(item.strip())
            if not m:
                continue
            strata[m.group(1)] += 1
            pos.setdefault(int(m.group(2)), m.group(3).strip())
    return (strata.most_common(1)[0][0] if strata else None), pos


def parse_table(lines: list[str]) -> dict[str, dict[str, dict[str, set[str]]]]:
    """His Appendix A as {stratum: {Near Eastern consonant: {"initial": set, "medial": set}}}."""
    i = _find(lines, r"^APPENDIX A: Sound Correspondences")
    j = _find(lines, r"^APPENDIX B", i)
    table: dict[str, dict] = {"kw": {}, "p": {}, "e": {}}
    for line in lines[i + 2 : j]:
        cols = [c.strip() for c in re.split(r"\s{2,}", line.strip()) if c.strip()]
        if len(cols) != 4 or cols[0].startswith(("Semitic", "UA terms")):
            continue
        heads = re.sub(r"\(.*?\)", "", cols[0]).replace(" ", "").split("/")
        for stratum, cell in zip(("kw", "p", "e"), cols[1:], strict=True):
            refl = _reflexes(cell)
            if refl is None:
                continue
            for h in heads:
                table[stratum][h] = refl
    return table


def _reflexes(cell: str) -> dict[str, set[str]] | None:
    if cell.startswith("--"):
        return None
    cell = cell.replace("medially", "").replace("but Tak", ",")
    res = {"initial": set(), "medial": set()}
    for tok in re.split(r"[/,]", cell):
        tok = tok.strip()
        if not tok:
            continue
        where = ("initial",) if tok.endswith("-") and not tok.startswith("-") else None
        if tok.startswith("-"):
            where = ("medial",)
        sym = tok.strip("-").strip()
        if sym in ("o", "u", "i", "ø"):
            sym = "ø"  # became a vowel or was lost: no consonant in the Uto-Aztecan word
        elif sym == "hu":
            sym = "h"
        for w in where or ("initial", "medial"):
            res[w].add(sym)
    return res


# Near Eastern symbols as tagged by Stubbs, normalised to the rows of his table.
_ROW = {"ʔ": "’", "'": "’", "š": "s1", "ś": "s2", "s": "s3", "i": "y", "ḍ": "ṣ", "ẓ": "ṭ",
        "f": "p", "ḫ": "x", "ǧ": "g", "j": "g", "ḥ": "ђ", "ħ": "ђ", "ḏ": "d", "ṯ": "θ",
        "ꜥ": "ʕ", "ꜣ": "’", "č": "c"}  # fmt: skip


# His numbered tags: a second glottal is ʕayn, h2 is ḥ, h3 and h4 are ḫ and ẖ, s4 is ṣ, t2 ṭ, g2 ġ.
_NUMBERED = {"’2": "ʕ", "h1": "h", "h2": "ђ", "h3": "x", "h4": "x", "s4": "ṣ", "t2": "ṭ",
             "g2": "ġ", "z2": "đ"}  # fmt: skip


def table_row(sym: str, table: dict) -> str | None:
    sym = re.split(r"[>/]", sym.strip())[0].strip()
    if sym[:2] in _NUMBERED:
        sym = _NUMBERED[sym[:2]]
    elif len(sym) == 2 and sym[0] == sym[1]:
        sym = sym[0]  # a geminate (bb, pp) is one consonant
    if sym in table:
        return sym
    if sym[:2] in table:
        return sym[:2]
    s = _ROW.get(sym[:1], sym[:1])
    if s in table:
        return s
    if s == "s3" and "s3" not in table and "s" in table:
        return "s"
    return None


# Uto-Aztecan orthography (his) to the consonant symbols of his table.
_UA_MAP = {"č": "c", "š": "s", "ṣ": "s", "ŕ": "r", "ʔ": "’", "'": "’", "v": "b", "g": "k",
           "f": "p", "d": "t", "z": "s", "x": "h", "ɨ": "ï", "ł": "l"}  # fmt: skip
_UA_V = set("aeiouïöüäəɨ")


def ua_symbols(form: str) -> list[str]:
    """Consonants of a Uto-Aztecan form in his spelling: kw, ts as units; C and N wildcards."""
    f = form.split("/")[0].strip().lstrip("*").split()[0] if form.strip() else ""
    f = "".join(c for c in unicodedata.normalize("NFD", f) if unicodedata.category(c) != "Mn")
    f = unicodedata.normalize("NFC", f)
    out_: list[str] = []
    i, prev = 0, ""
    while i < len(f):
        two = f[i : i + 2]
        if two in ("kw", "gw", "bw", "hw"):
            out_.append("kw" if two != "hw" else "w")
            i += 2
            continue
        if two == "ts":
            out_.append("c")
            i += 2
            continue
        ch = f[i]
        if ch in ("C", "N"):
            out_.append(ch)
        elif ch.lower() in _UA_V or not ch.isalpha() and ch not in "’'ʔ":
            pass
        else:
            sym = _UA_MAP.get(ch.lower(), ch.lower())
            if ch.lower() != prev:  # a doubled consonant (pp) is one
                out_.append(sym)
            prev = ch.lower()
            i += 1
            continue
        prev = ch.lower()
        i += 1
    return out_


def obeys(ne_rows: list[str], ua: list[str], column: dict, final_loss: bool = False) -> bool:
    """Whether a Near Eastern consonant sequence goes to the Uto-Aztecan one under his table.

    Each Near Eastern consonant either becomes the next Uto-Aztecan consonant (one his table
    allows in that position: the first is "initial", the rest "medial") or is lost where the
    table allows loss (ø, or a vowel). Uto-Aztecan consonants left over at the end (suffixes)
    are allowed; C matches any consonant and N any nasal. ``final_loss`` (added after the first
    read of his sets, reported beside the strict count) also lets the last of two or more Near
    Eastern consonants go missing at the end of the word, as his prose often allows.
    """

    def ok(row: str, sym: str, initial: bool) -> bool:
        refl = column.get(row)
        if refl is None:
            return False
        allowed = (
            refl["initial" if initial else "medial"] or refl["medial" if initial else "initial"]
        )
        if sym == "C":
            return True
        if sym == "N":
            return bool(allowed & {"m", "n", "ŋ"})
        return sym in allowed

    def lost(row: str, initial: bool) -> bool:
        refl = column.get(row)
        return bool(refl) and "ø" in refl["initial" if initial else "medial"]

    @functools.cache
    def go(i: int, j: int) -> bool:
        if i == len(ne_rows):
            return True
        if final_loss and len(ne_rows) >= 2 and i == len(ne_rows) - 1 and j == len(ua):
            return True
        initial = i == 0
        if j < len(ua) and ok(ne_rows[i], ua[j], initial and j == 0) and go(i + 1, j + 1):
            return True
        return lost(ne_rows[i], initial) and go(i + 1, j)

    return go(0, 0)


_APPB = re.compile(r"^([A-Z][^:]{0,60}): (\d+|XX);? (.+?) > (.+)$")
_QUOTE = re.compile(r"[‘'](.+?)[’']")


def appendix_b(lines: list[str]) -> dict[int, list[dict]]:
    """His English index: set number -> [{headword, ne, ne_gloss, ua, ua_gloss}]."""
    i = _find(lines, r"^APPENDIX B: English Index")
    j = _find(lines, r"^(APPENDIX|Appendix) C", i)
    joined: list[str] = []
    for line in lines[i + 1 : j]:
        s = line.strip()
        if not s or re.fullmatch(r"\d{1,3}", s):
            continue
        if _APPB.match(s) or not joined:
            joined.append(s)
        else:
            joined[-1] += " " + s
    res: dict[int, list[dict]] = defaultdict(list)
    for s in joined:
        m = _APPB.match(s)
        if not m or m.group(2) == "XX":
            continue
        ne, ua = m.group(3), m.group(4)
        qn, qu = _QUOTE.search(ne), _QUOTE.search(ua)
        ne_head = ne[: qn.start()] if qn else ne
        ua_head = ua[: qu.start()] if qu else ua
        res[int(m.group(2))].append(
            {
                "headword": m.group(1).strip(),
                "ne_language": ne_head.split()[0] if ne_head.split() else "",
                "ne": " ".join(ne_head.split()[1:]),
                "ne_gloss": qn.group(1) if qn else "",
                "ua": _ua_form(ua_head),
                "ua_gloss": qu.group(1) if qu else "",
            }
        )
    return dict(res)


def _ua_form(head: str) -> str:
    """The form from "UACV-1280 *yikar" or "Tr gamea": a starred form first, else the last word."""
    head = re.sub(r"UACV-\d+[a-z]?", " ", head)
    star = re.findall(r"\*[^\s,;/]+", head)
    if star:
        return star[0]
    words = [w for w in head.replace("/", " ").split() if w not in ("UA", "PUA", "in", "of")]
    return words[-1] if words else ""


def ne_symbols(form: str) -> list[str]:
    """Consonants of his transliteration of a Semitic or Egyptian form (first variant)."""
    f = re.split(r"[/,;(]", form)[0].strip().split()
    f = f[0] if f else ""
    f = unicodedata.normalize("NFC", f)
    vowels = set("aeiouəǝɛɔâêîôûāēīōūăĕĭŏŭáéíóúàèìòùAEIOU")
    out_ = []
    for ch in f:
        if ch in vowels or not (ch.isalpha() or ch in "’ʕ'ʔђ"):
            continue
        sym = "’" if ch in "'ʔ" else ch
        if not out_ or out_[-1] != sym:
            out_.append(sym)
    return out_


def alternatives(rows, ua, column, level, ua_gloss, entries, keyed, links) -> Counter:
    """Other lexicon entries passing his table for this UA form with a meaning at least as close.

    ``sound``: strict table only; ``both``: strict and the meaning bar; the ``_final_loss`` pair
    the same with a missing last consonant allowed. Level 2 (neither) lets any gloss count.
    """
    counts: Counter = Counter()
    for e in entries:
        erows = [table_row(c, column) for c in e["symbols"]][: len(rows)]
        if len(erows) < len(rows) or None in erows or erows == rows:
            continue  # too short to test at his positions, unreadable, or his own root
        strict = obeys(erows, ua, column)
        loose = strict or obeys(erows, ua, column, final_loss=True)
        if not loose:
            continue
        near = (
            level == 2 or min(closeness(g, ua_gloss, keyed, links) for g in e["glosses"]) <= level
        )
        counts["sound"] += strict
        counts["both"] += strict and near
        counts["sound_final_loss"] += 1
        counts["both_final_loss"] += near
    return counts


def his_way(cfg: dict) -> tuple[dict, list[dict], list[dict]]:
    """Step 1: (public counts, private per-set records, private judge questions)."""
    u = cfg["lab"]["utoaztecan"]
    h = u["his_way"]
    lines = stubbs_text()
    sets = parse_sets(lines)
    table = parse_table(lines)
    index = appendix_b(lines)
    out(PRIV / "appendix_a.json").write_text(
        json.dumps(
            {
                k: {r: {w: sorted(s) for w, s in v.items()} for r, v in col.items()}
                for k, col in table.items()
            },
            ensure_ascii=False,
            indent=1,
        )  # fmt: skip
    )
    rng = np.random.default_rng(u["seed"])
    frame = sorted(sets)
    pick = sorted(
        int(x) for x in rng.choice(frame, size=min(h["sample_sets"], len(frame)), replace=False)
    )
    keyed, links = clics_graph(h["clics_min_families"])
    lex = {"oshl": strong_entries(), "cdo": coptic_entries()}
    records, jobs = [], []
    for num in pick:
        s = sets[num]
        body = "\n".join(s["lines"])
        stratum, codes = codes_of(body)
        idx = index.get(num, [{}])[0]
        if stratum is None:
            lang = idx.get("ne_language", "")
            if lang.startswith("Sem-kw"):
                stratum = "kw"
            elif lang.startswith("Sem-p"):
                stratum = "p"
            elif lang.startswith(("Egyptian", "Coptic")):
                stratum = "e"
            elif s["chapter_stratum"] in ("kw", "e"):
                stratum = s["chapter_stratum"]
        rec = {
            "set": num,
            "chapter": s["chapter"],
            "stratum": stratum,
            "codes": codes,
            "ne_language": idx.get("ne_language"),
            "ne": idx.get("ne"),
            "ne_gloss": idx.get("ne_gloss"),
            "ua": idx.get("ua"),
            "ua_gloss": idx.get("ua_gloss"),
            "in_index": bool(idx),
        }
        column = table.get(stratum or "", {})
        ua = ua_symbols(rec["ua"] or "")
        if codes:
            positions = sorted(p for p in codes if p <= h["max_positions"])
            rows = [table_row(codes[p], column) for p in positions]
            rec["skeleton_from"] = "his tags"
        else:
            rows = [table_row(c, column) for c in ne_symbols(rec["ne"] or "")][: h["max_positions"]]
            rec["skeleton_from"] = "his form"
        rec["ne_rows"], rec["ua_symbols"] = rows, ua
        readable = bool(stratum and column and rows and ua and rec["ne_gloss"] and rec["ua_gloss"])
        readable = readable and None not in rows
        rec["machine_readable"] = readable
        if not readable:
            jobs.append(_set_job(num, body))
            records.append(rec)
            continue
        rec["obeys_table"] = obeys(rows, ua, column)
        rec["obeys_first"] = obeys(rows[:1], ua, column)
        rec["obeys_final_loss"] = obeys(rows, ua, column, final_loss=True)
        level = closeness(rec["ne_gloss"], rec["ua_gloss"], keyed, links)
        rec["meaning_level"] = level
        jobs.append(_gloss_job(num, rec["ne_gloss"], rec["ua_gloss"]))
        source = "cdo" if stratum == "e" else "oshl"
        counts = alternatives(rows, ua, column, level, rec["ua_gloss"], lex[source], keyed, links)
        rec["alternatives_lexicon"] = source
        rec["alternatives_sound"] = counts["sound"]
        rec["alternatives"] = counts["both"]
        rec["alternatives_final_loss"] = counts["both_final_loss"]
        rec["alternatives_sound_final_loss"] = counts["sound_final_loss"]
        records.append(rec)
    public = _his_way_summary(records, len(sets), len(frame), lex)
    return public, records, jobs


def _set_job(num: int, body: str) -> dict:
    prompt = (
        "Below is one numbered set from a book that compares Uto-Aztecan words with Semitic or "
        "Egyptian words. Read it and answer with one JSON object, no other text: "
        '{"ne_language": ..., "ne_form": ..., "ne_gloss": ..., "ua_form": ..., "ua_gloss": ..., '
        '"stratum": "Semitic-kw" | "Semitic-p" | "Egyptian" | "unclear"}. Use the first '
        "Near Eastern form and the main Uto-Aztecan form the set proposes. Do not judge whether "
        "the comparison is right.\n\n" + body[:4000]
    )
    return {"id": f"set-{num}", "prompt": prompt}


def _gloss_job(num: int, g1: str, g2: str) -> dict:
    prompt = (
        "Two word meanings, from two different languages. How close are they? Answer with one "
        "word: SAME (the same meaning, or one is a plain sub-sense of the other), RELATED (a "
        "speaker could use one word for both: part and whole, cause and effect, a common "
        "metaphor), or DISTANT (a link needs a story).\n"
        f"Meaning A: {g1}\nMeaning B: {g2}"
    )
    return {"id": f"gloss-{num}", "prompt": prompt}


def _his_way_summary(records: list[dict], found: int, frame: int, lex: dict) -> dict:
    readable = [r for r in records if r["machine_readable"]]
    alts = sorted(r["alternatives"] for r in readable)
    sound = sorted(r["alternatives_sound"] for r in readable)

    def med(xs):
        return xs[len(xs) // 2] if xs else None

    by = Counter((r["stratum"] or "none") for r in records)
    return {
        "sets_found": found,
        "sample": len(records),
        "sample_set_numbers": [r["set"] for r in records],
        "by_stratum": dict(by),
        "in_english_index": sum(r["in_index"] for r in records),
        "with_his_tags": sum(bool(r["codes"]) for r in records),
        "machine_readable": len(readable),
        "machine_readable_from_tags": sum(r["skeleton_from"] == "his tags" for r in readable),
        "obey_table_all_positions": sum(r["obeys_table"] for r in readable),
        "obey_table_first_consonant": sum(r["obeys_first"] for r in readable),
        "obey_table_final_loss_allowed": sum(r["obeys_final_loss"] for r in readable),
        "obey_by_source": {
            src: [
                sum(r["obeys_table"] for r in readable if r["skeleton_from"] == src),
                sum(r["skeleton_from"] == src for r in readable),
            ]
            for src in ("his tags", "his form")
        },  # fmt: skip
        "meaning_levels": dict(Counter(r["meaning_level"] for r in readable)),
        "alternatives_median": med(alts),
        "alternatives_quartiles": [alts[len(alts) // 4], alts[3 * len(alts) // 4]]
        if alts
        else None,
        "alternatives_sound_only_median": med(sound),
        "sets_with_no_alternative": sum(a == 0 for a in alts),
        "sets_with_10_or_more": sum(a >= 10 for a in alts),
        "final_loss_allowed": {
            "alternatives_median": med(sorted(r["alternatives_final_loss"] for r in readable)),
            "alternatives_sound_only_median": med(
                sorted(r["alternatives_sound_final_loss"] for r in readable)
            ),
        },
        "alternatives_median_where_his_obeys": med(
            sorted(r["alternatives"] for r in readable if r["obeys_table"])
        ),
        "lexicon_entries": {k: len(v) for k, v in lex.items()},
        "per_set": [
            {
                k: r.get(k)
                for k in (
                    "set",
                    "stratum",
                    "machine_readable",
                    "skeleton_from",
                    "obeys_table",
                    "obeys_first",
                    "obeys_final_loss",
                    "meaning_level",
                    "alternatives_lexicon",
                    "alternatives_sound",
                    "alternatives",
                    "alternatives_final_loss",
                )
            }
            for r in records
        ],  # fmt: skip
    }


# ---------------------------------------------------------------------------------------------
# Step 1 with the judged readings (card section 2026-11-23; simulated judging)

_MODEL_STRATUM = {"semitic-kw": "kw", "semitic-p": "p", "egyptian": "e"}
_RATINGS = ("SAME", "RELATED", "DISTANT")


def parse_answer(row: dict) -> dict | str | None:
    """A judge reply: a set reading (dict), a rating (str), or None when it cannot be read."""
    text = (row.get("reply") or "").strip()
    if row["id"].startswith("gloss-"):
        word = re.sub(r"[^A-Z]", "", text.upper())
        return word if word in _RATINGS else None
    m = re.search(r"\{.*\}", text, re.S)
    try:
        obj = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None
    keys = ("ne_language", "ne_form", "ne_gloss", "ua_form", "ua_gloss", "stratum")
    if not isinstance(obj, dict) or not all(k in obj for k in keys):
        return None
    return obj


def judged_record(rec: dict, reading: dict, table: dict, max_positions: int) -> dict:
    """Step 1's rule check on a set as the model read it (his tags and rule stratum first)."""
    said = str(reading.get("stratum") or "").strip().lower()
    model_stratum = _MODEL_STRATUM.get(said)
    stratum = rec.get("stratum") or model_stratum
    res = {
        "set": rec["set"],
        "rule_stratum": rec.get("stratum"),
        "model_stratum": model_stratum,
        "stratum": stratum,
        "ne_gloss": reading.get("ne_gloss") or "",
        "ua_gloss": reading.get("ua_gloss") or "",
    }
    codes = {int(k): v for k, v in (rec.get("codes") or {}).items()}

    def skeleton(column: dict) -> list[str | None]:
        if codes:
            return [table_row(codes[q], column) for q in sorted(codes) if q <= max_positions]
        syms = ne_symbols(str(reading.get("ne_form") or ""))
        return [table_row(c, column) for c in syms][:max_positions]

    column = table.get(stratum or "", {})
    rows = skeleton(column)
    res["skeleton_from"] = "his tags" if codes else "model form"
    ua = ua_symbols(str(reading.get("ua_form") or ""))
    res["ne_rows"], res["ua_symbols"] = rows, ua
    readable = bool(stratum and column and rows and ua and res["ne_gloss"] and res["ua_gloss"])
    res["readable"] = readable and None not in rows
    if res["readable"]:
        res["obeys_table"] = obeys(rows, ua, column)
        res["obeys_first"] = obeys(rows[:1], ua, column)
    elif stratum is None and said == "unclear" and ua:
        # Beside, the reading most generous to him: either Semitic column.
        either = [
            obeys(r, ua, table[col])
            for col in ("kw", "p")
            if (r := skeleton(table[col])) and None not in r
        ]
        res["unclear_checkable_semitic"] = bool(either)
        res["unclear_obeys_either_semitic"] = any(either)
    return res


def _spread(xs: list[int]) -> dict:
    xs = sorted(xs)
    if not xs:
        return {"n": 0}
    return {
        "n": len(xs),
        "median": xs[len(xs) // 2],
        "quartiles": [xs[len(xs) // 4], xs[3 * len(xs) // 4]],
        "none": sum(x == 0 for x in xs),
        "ten_or_more": sum(x >= 10 for x in xs),
    }


def judged_summary(records, answers, table, lex, keyed, links, h) -> tuple[dict, list[dict]]:
    """Public counts and private per-set rows for the judged readings (card 2026-11-23)."""
    level_of = h["judged"]["rating_level"]
    parsed = {a["id"]: parse_answer(a) for a in answers}
    unparsed = sorted(k for k, v in parsed.items() if v is None)
    rule = [r for r in records if r["machine_readable"]]
    judged, private = [], []
    for rec in records:
        if rec["machine_readable"]:
            continue
        reading = parsed.get(f"set-{rec['set']}")
        if not isinstance(reading, dict):
            continue
        j = judged_record(rec, reading, table, h["max_positions"])
        if j["readable"]:
            column = table[j["stratum"]]
            j["meaning_level"] = closeness(j["ne_gloss"], j["ua_gloss"], keyed, links)
            source = "cdo" if j["stratum"] == "e" else "oshl"
            c = alternatives(
                j["ne_rows"], j["ua_symbols"], column, j["meaning_level"], j["ua_gloss"],
                lex[source], keyed, links,
            )  # fmt: skip
            j["alternatives_lexicon"], j["alternatives"] = source, c["both"]
        judged.append(j)
        private.append(j)
    read = [j for j in judged if j["readable"]]
    both = rule + read

    def obey(rs):
        return {
            "sets": len(rs),
            "obey_every_position": sum(bool(r["obeys_table"]) for r in rs),
            "obey_first_consonant": sum(bool(r["obeys_first"]) for r in rs),
        }

    agree = [j for j in judged if j["rule_stratum"] and j["model_stratum"]]
    unclear = [j for j in judged if "unclear_checkable_semitic" in j]
    why = Counter()
    for j in judged:
        if j["readable"]:
            continue
        if not j["stratum"]:
            why["no stratum (model: unclear or none)"] += 1
        elif not j["ne_rows"] or None in j["ne_rows"]:
            why["Near Eastern consonants not in his table"] += 1
        elif not j["ua_symbols"]:
            why["no Uto-Aztecan consonants"] += 1
        else:
            why["a gloss missing"] += 1
    # The 71 gloss ratings against the rule's levels.
    cross: dict[str, dict[str, int]] = {str(lv): dict.fromkeys(_RATINGS, 0) for lv in (0, 1, 2)}
    closer = same = looser = 0
    tightened, tightened_rows = [], []
    for r in rule:
        rating = parsed.get(f"gloss-{r['set']}")
        if not isinstance(rating, str):
            continue
        cross[str(r["meaning_level"])][rating] += 1
        mapped = level_of[rating]
        closer += mapped < r["meaning_level"]
        same += mapped == r["meaning_level"]
        looser += mapped > r["meaning_level"]
        level = min(mapped, r["meaning_level"])
        if level == r["meaning_level"]:
            tightened.append(r["alternatives"])
            continue
        column = table[r["stratum"]]
        source = "cdo" if r["stratum"] == "e" else "oshl"
        c = alternatives(
            r["ne_rows"], r["ua_symbols"], column, level, r["ua_gloss"], lex[source], keyed, links
        )
        tightened.append(c["both"])
        tightened_rows.append({"set": r["set"], "level": level, "alternatives": c["both"]})
    ratings = Counter(v for k, v in parsed.items() if k.startswith("gloss-") and isinstance(v, str))
    public = {
        "label": "simulated judging: a model (sonnet, lab.judge) read the sets, not a person",
        "answers": len(answers),
        "unparsed": unparsed,
        "judged_sets": {
            "asked": sum(1 for r in records if not r["machine_readable"]),
            "answered": len(judged),
            "read": len(read),
            "not_read": dict(why),
            "model_stratum": dict(Counter(j["model_stratum"] or "unclear" for j in judged)),
            "stratum_used": dict(Counter(j["stratum"] or "none" for j in judged)),
            "skeleton_from": dict(Counter(j["skeleton_from"] for j in read)),
            "rule_and_model_stratum_both": len(agree),
            "rule_and_model_stratum_agree": sum(
                j["rule_stratum"] == j["model_stratum"] for j in agree
            ),
            **obey(read),
            "meaning_levels": dict(Counter(j["meaning_level"] for j in read)),
            "alternatives": _spread([j["alternatives"] for j in read]),
            "per_set": [
                {
                    k: j.get(k)
                    for k in (
                        "set",
                        "stratum",
                        "readable",
                        "skeleton_from",
                        "obeys_table",
                        "obeys_first",
                        "meaning_level",
                        "alternatives",
                    )
                }
                for j in judged
            ],  # fmt: skip
        },
        "by_rule": obey(rule) | {"alternatives": _spread([r["alternatives"] for r in rule])},
        "all_readable": obey(both) | {"alternatives": _spread([r["alternatives"] for r in both])},
        "unclear_beside": {
            "sets": len(unclear),
            "checkable_under_a_semitic_column": sum(
                j["unclear_checkable_semitic"] for j in unclear
            ),
            "obey_under_either_semitic_column": sum(
                j["unclear_obeys_either_semitic"] for j in unclear
            ),
        },
        "gloss_ratings": {
            "counts": {k: ratings.get(k, 0) for k in _RATINGS},
            "rating_level": level_of,
            "rule_level_by_rating": cross,
            "model_closer_than_rule": closer,
            "model_same_as_rule": same,
            "model_looser_than_rule": looser,
            "alternatives_with_closer_of_rule_and_model": _spread(tightened),
            "sets_tightened": [t["set"] for t in tightened_rows],
        },
    }
    return public, private


def his_way_judged(cfg: dict) -> tuple[dict, list[dict]]:
    """Load the step-1 records, the judge answers and the lexicons; summarise (card 2026-11-23)."""
    h = cfg["lab"]["utoaztecan"]["his_way"]
    records = [json.loads(x) for x in (PRIV / "his_way_sample.jsonl").read_text().splitlines() if x]
    answers = [
        json.loads(x)
        for x in (PRIV / "answers_his_way.jsonl").read_text().splitlines()
        if x.strip()
    ]
    table = parse_table(stubbs_text())
    keyed, links = clics_graph(h["clics_min_families"])
    lex = {"oshl": strong_entries(), "cdo": coptic_entries()}
    return judged_summary(records, answers, table, lex, keyed, links, h)


def claimed_meanings(lines: list[str], data: Data) -> set[str]:
    """Concepticon meanings his English index (Appendix B) gives a Semitic or Egyptian source."""
    res = set()
    for entries in appendix_b(lines).values():
        for e in entries:
            hw = e["headword"].lower()
            cands = [hw]
            if ", " in hw:
                a, b = hw.split(", ", 1)
                cands.append(f"{b} {a}")
            for c in cands:
                for key in gloss_keys(c):
                    if key in data.concept_keys:
                        res.add(data.concept_keys[key])
    return res


# ---------------------------------------------------------------------------------------------
# Step 2: pairs, the known-answer check, targets


def _seed(*parts) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def pair_arrays(la: dict, lb: dict, meanings: list[str]):
    a1 = np.array([la[m][0] for m in meanings])
    a2 = np.array([la[m][1] for m in meanings])
    b1 = np.array([lb[m][0] for m in meanings])
    b2 = np.array([lb[m][1] for m in meanings])
    return a1, a2, b1, b2


def shared(la: dict, lb: dict) -> list[str]:
    return sorted(set(la) & set(lb), key=lambda m: int(m) if m.isdigit() else m)


def score_pair(la, lb, meanings, cfg, tag, borrow) -> dict:
    u = cfg["lab"]["utoaztecan"]
    a1, a2, b1, b2 = pair_arrays(la, lb, meanings)
    rng = np.random.default_rng(_seed(u["seed"], tag, len(meanings)))
    res = perm_test(a1, b1, u["shuffles"], rng, second=(a2, b2))
    res["skew"] = skew(la, lb, meanings, borrow, cfg, tag)
    return res


def skew(la, lb, meanings, borrow, cfg, tag) -> dict:
    """z of the most borrowable third minus z of the least borrowable third (WOLD scores)."""
    u = cfg["lab"]["utoaztecan"]
    scored = sorted((m for m in meanings if m in borrow), key=lambda m: (borrow[m], m))
    part = len(scored) // u["borrow_parts"]
    if part < 5:
        return {"scored": len(scored), "skew": None}
    low, high = scored[:part], scored[-part:]
    zs = {}
    for name, ms in (("least", low), ("most", high)):
        a1, _, b1, _ = pair_arrays(la, lb, ms)
        rng = np.random.default_rng(_seed(u["seed"], tag, name, len(ms)))
        zs[name] = perm_test(a1, b1, u["shuffles"], rng)["z"]
    d = round(zs["most"] - zs["least"], 3)
    return {"scored": len(scored), "per_third": part, "z_most": zs["most"],
            "z_least": zs["least"], "skew": d, "borrowable_end": d > u["skew_margin"]}  # fmt: skip


def subsample(meanings: list[str], n: int, tag: str, seed: int) -> list[str]:
    if len(meanings) <= n:
        return meanings
    rng = np.random.default_rng(_seed(seed, tag, n))
    return sorted(rng.choice(meanings, size=n, replace=False).tolist())


def check_at(n: int, k: int, data: Data, cfg: dict, borrow: dict) -> dict:
    """The known-answer check with every pair cut to n meanings; k loans planted for power."""
    u = cfg["lab"]["utoaztecan"]
    ka = u["known_answer"]
    alpha = u["alpha"]
    res: dict = {"n": n, "k_planted": k}

    def run(group: str) -> list[dict]:
        rows = []
        for sa, sb in ka[group]:
            la, lb = data.get(sa), data.get(sb)
            tag = f"{group}:{sa}:{sb}"
            if la is None or lb is None:
                rows.append({"pair": [sa, sb], "state": "not attempted (list missing)"})
                continue
            ms = shared(la, lb)
            if len(ms) < u["min_meanings"]:
                rows.append({"pair": [sa, sb], "state": "not attempted (too few meanings)",
                             "shared": len(ms)})  # fmt: skip
                continue
            ms = subsample(ms, n, tag, u["seed"])
            rows.append({"pair": [sa, sb], "shared_used": len(ms),
                         **score_pair(la, lb, ms, cfg, tag, borrow)})  # fmt: skip
        return rows

    for group in ("inherited", "contact", "negative", "decoys"):
        res[group] = run(group)
    hit = lambda r: "p" in r and r["p"] < alpha  # noqa: E731
    inh = res["inherited"]
    res["inherited_ok"] = bool(inh) and all(hit(r) for r in inh)
    con = res["contact"]
    passing = [i for i, r in enumerate(con) if hit(r) and r["skew"].get("borrowable_end")]
    res["contact_passing"] = len(passing)
    res["contact_detected_without_skew"] = sum(hit(r) for r in con)
    res["contact_ok"] = len(passing) >= ka["contact_needed"] and any(
        i in passing for i in ka["finnish"]
    )
    res["finnish_ok"] = any(i in passing for i in ka["finnish"])
    neg = res["negative"]
    res["negative_hits"] = sum(hit(r) for r in neg)
    res["negative_ok"] = all("p" in r for r in neg) and res["negative_hits"] <= ka["negative_max"]
    dec = res["decoys"]
    res["decoys_ok"] = all("p" in r and r["p"] > u["decoy_alpha"] for r in dec)
    res["planted"] = planted(n, k, data, cfg)
    res["passed"] = all(res[x] for x in ("inherited_ok", "contact_ok", "negative_ok", "decoys_ok"))
    return res


def planted(n: int, k: int, data: Data, cfg: dict) -> dict:
    u = cfg["lab"]["utoaztecan"]
    p = u["planted"]
    res = {}
    for frac in p["fractions"]:
        kk = max(1, round(k * frac))
        hits = tried = 0
        for sa, sb in u["known_answer"]["negative"]:
            la, lb = data.get(sa), data.get(sb)
            if la is None or lb is None:
                continue
            ms = subsample(shared(la, lb), n, f"negative:{sa}:{sb}", u["seed"])
            if len(ms) < u["min_meanings"]:
                continue
            a1, a2, b1, b2 = pair_arrays(la, lb, ms)
            rng = np.random.default_rng(_seed(u["seed"], "plant", sa, sb, n, kk))
            for _ in range(p["plantings"]):
                nb1, nb2 = plant(a1, a2, b1, b2, kk, rng)
                r = perm_test(a1, nb1, p["shuffles"], rng)
                hits += r["p"] < u["alpha"]
                tried += 1
        res[str(frac)] = {"k": kk, "plantings": tried, "detected": hits,
                          "rate": round(hits / tried, 3) if tried else None}  # fmt: skip
    first = res[str(p["fractions"][0])]
    res["power_ok"] = first["rate"] is not None and first["rate"] >= p["bar"]
    return res


def target_frames(data: Data, cfg: dict) -> dict[str, dict]:
    """For each target: its lists, shared meanings and size."""
    u = cfg["lab"]["utoaztecan"]
    frames = {}
    gh = None
    for name, (sa, sb) in u["targets"].items():
        donor = data.get(sb)
        if donor is None:
            frames[name] = {"state": "not attempted (list missing)", "pair": [sa, sb]}
            continue
        if sa == "gh:*":
            gh = gh if gh is not None else data.greenhill()
            ms = sorted({m for lst in gh.values() for m in lst} & set(donor), key=_mkey)
            frames[name] = {"pair": [sa, sb], "multi": True, "meanings": ms, "n": len(ms)}
            continue
        la = data.get(sa)
        if la is None:
            frames[name] = {"state": "not attempted (list missing)", "pair": [sa, sb]}
            continue
        ms = shared(la, donor)
        frames[name] = {"pair": [sa, sb], "multi": False, "meanings": ms, "n": len(ms)}
    for f in frames.values():
        if "n" in f and f["n"] < u["min_meanings"]:
            f["state"] = "not attempted (too few meanings)"
    return frames


def _mkey(m: str):
    return int(m) if m.isdigit() else m


def score_target(name: str, frame: dict, data: Data, cfg: dict, borrow: dict) -> dict:
    u = cfg["lab"]["utoaztecan"]
    sa, sb = frame["pair"]
    donor = data.get(sb)
    ms = frame["meanings"]
    if not frame["multi"]:
        return score_pair(data.get(sa), donor, ms, cfg, f"target:{name}", borrow)
    gh = data.greenhill()
    d = np.array([donor[m][0] for m in ms])
    vars_ = []
    for lst in gh.values():
        mask = np.array([m in lst for m in ms])
        if mask.sum() >= u["min_meanings"]:
            vars_.append((mask, np.array([lst[m][0] for m, k in zip(ms, mask, strict=True) if k])))
    rng = np.random.default_rng(_seed(u["seed"], "target", name, len(ms)))
    return multi_perm_test(vars_, d, u["shuffles"], rng)


def check(cfg: dict, data: Data | None = None) -> dict:
    """The known-answer check at the size of every target list (sizes shared are run once)."""
    data = data or Data(cfg)
    borrow = data.borrowed_score()
    frames = target_frames(data, cfg)
    try:
        claims = claimed_meanings(stubbs_text(), data)
    except (OSError, StopIteration, subprocess.CalledProcessError):
        claims = None
    sizes: dict[int, int] = {}
    for f in frames.values():
        if "state" in f:
            continue
        k = len(set(f["meanings"]) & claims) if claims is not None else None
        f["k_claimed"] = k
        sizes[f["n"]] = max(sizes.get(f["n"], 0), k or 0)
    by_size = {str(n): check_at(n, k, data, cfg, borrow) for n, k in sorted(sizes.items())}
    return {
        "frames": {k: {x: v for x, v in f.items() if x != "meanings"} for k, f in frames.items()},
        "claims_read": claims is not None,
        "by_size": by_size,
        "missing": data.missing,
    }


def run(cfg: dict) -> dict:
    u = cfg["lab"]["utoaztecan"]
    data = Data(cfg)
    res: dict = {"settings": u}
    try:
        public, records, jobs = his_way(cfg)
        res["his_way"] = public
        _write_private(records, jobs)
    except (OSError, StopIteration, subprocess.CalledProcessError) as exc:
        res["his_way"] = {"state": f"not attempted ({type(exc).__name__})"}
    chk = check(cfg, data)
    res["known_answer"] = chk
    _write_mapping_jobs(data)
    passed = {n for n, c in chk["by_size"].items() if c["passed"]}
    if not passed:
        res["stopped"] = (
            "the known-answer check missed its bar at every list size; no target scored"
        )
        return res
    borrow = data.borrowed_score()
    frames = target_frames(data, cfg)
    scored, skipped = {}, {}
    for name, f in frames.items():
        if "state" in f:
            skipped[name] = f["state"]
        elif str(f["n"]) not in passed:
            skipped[name] = "cannot tell (check missed at this list size)"
        else:
            scored[name] = {"pair": f["pair"], **score_target(name, f, data, cfg, borrow)}
    # Holm across all the card's targets: one not scored counts as p = 1 (it cannot lower others).
    adj = holm({k: scored[k]["p"] if k in scored else 1.0 for k in frames})
    for name, r in scored.items():
        r["p_holm"] = adj[name]
        size = chk["by_size"][str(frames[name]["n"])]
        skew_ok = (r.get("skew") or {}).get("borrowable_end")
        if r["p_holm"] < u["alpha"]:
            r["verdict"] = "yes" if skew_ok else "signal without the skew (no verdict)"
            if r.get("multi") or "skew" not in r:
                r["verdict"] = "signal (multilateral; skew not computed)"
        elif size["finnish_ok"] and size["planted"]["power_ok"]:
            r["verdict"] = "no layer of the size claimed in these lists"
        else:
            r["verdict"] = "cannot tell (no power or no Finnish calibrator)"
    res["targets"] = scored
    res["targets_not_scored"] = skipped
    trap = u["trap"]
    la, lb = data.get(trap[0]), data.get(trap[1])
    if la is not None and lb is not None and str(len(shared(la, lb))) in passed:
        res["trap"] = {"pair": trap, **score_pair(la, lb, shared(la, lb), cfg, "trap", borrow)}
    elif la is not None and lb is not None:
        res["trap"] = {
            "pair": trap,
            "n": len(shared(la, lb)),
            "state": "not scored (no check at its size)",
        }
    return res


def _write_private(records: list[dict], jobs: list[dict]) -> None:
    lines = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    out(PRIV / "his_way_sample.jsonl").write_text(lines, encoding="utf-8")
    js = "".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs)
    out(PRIV / "judge_his_way.jsonl").write_text(js, encoding="utf-8")


def _write_mapping_jobs(data: Data) -> None:
    """Questions for the paced judge (simulated): is each lexicon-to-meaning mapping right?"""
    jobs = []
    for which, lang in (("oshl", "Biblical Hebrew"), ("cdo", "Coptic")):
        try:
            mapped = data.lexicon_map(which)
        except OSError:
            continue
        for cid, e in sorted(mapped.items(), key=lambda kv: _mkey(kv[0])):
            prompt = (
                f"A {lang} dictionary entry has these English glosses: "
                f"{'; '.join(e['glosses'][:8])}. "
                f"Is the ordinary, everyday meaning of this word the concept "
                f"'{data.concept_names.get(cid, cid)}' (as in a basic word list)? Answer YES or NO."
            )
            jobs.append({"id": f"map-{which}-{cid}-{e['id']}", "prompt": prompt})
    js = "".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs)
    out(PRIV / "judge_mappings.jsonl").write_text(js, encoding="utf-8")


def _stamp(res: dict) -> dict:
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "cmd",
        choices=["his-way", "his-way-judged", "check", "run", "vocabulary", "vocabulary-rerun"],
    )
    a = ap.parse_args(argv)
    if a.cmd == "vocabulary":
        from lab import utoaztecan_vocab

        return utoaztecan_vocab.main()
    if a.cmd == "vocabulary-rerun":
        from lab import utoaztecan_vocab

        return utoaztecan_vocab.main_rerun()
    cfg = config.load()
    if a.cmd == "his-way":
        public, records, jobs = his_way(cfg)
        _write_private(records, jobs)
        out(OUT / "his_way.json").write_text(json.dumps(_stamp(public), indent=1) + "\n")
        print(json.dumps({k: v for k, v in public.items() if k not in ("per_set",)}, indent=1))
        return 0
    if a.cmd == "his-way-judged":
        public, private = his_way_judged(cfg)
        lines = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in private)
        out(PRIV / "his_way_judged.jsonl").write_text(lines, encoding="utf-8")
        out(OUT / "his_way_judged.json").write_text(json.dumps(_stamp(public), indent=1) + "\n")
        brief = {k: v for k, v in public.items() if k != "judged_sets"}
        print(json.dumps(brief | {"judged": {k: v for k, v in public["judged_sets"].items()
                                             if k != "per_set"}}, indent=1))  # fmt: skip
        return 0
    if a.cmd == "check":
        res = _stamp(check(cfg))
        out(OUT / "check.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(_brief(res), indent=1))
        return 0
    res = _stamp(run(cfg))
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(_brief(res.get("known_answer", {})), indent=1))
    print(json.dumps({k: res.get(k) for k in ("stopped", "targets_not_scored")}, indent=1))
    for name, r in (res.get("targets") or {}).items():
        print(name, r.get("n"), r.get("p"), r.get("p_holm"), r.get("verdict"))
    return 0


def _brief(chk: dict) -> dict:
    keys = ("inherited_ok", "contact_passing", "contact_detected_without_skew", "finnish_ok",
            "contact_ok", "negative_hits", "negative_ok", "decoys_ok", "passed")  # fmt: skip
    res = {}
    for n, c in (chk.get("by_size") or {}).items():
        res[n] = {k: c[k] for k in keys} | {
            "planted": {f: v.get("rate") for f, v in c["planted"].items() if isinstance(v, dict)}
        }
    return res


if __name__ == "__main__":
    raise SystemExit(main())
