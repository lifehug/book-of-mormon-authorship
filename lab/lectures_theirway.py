"""BOM-104, their way first: the three published Lectures on Faith studies rerun approximately.

Larsen, Rencher and Layton (1980, Appendix E: stepwise discriminant analysis on 2,000-word blocks),
Phipps (1977: Mosteller and Wallace's simplified median-split odds) and Reynolds (2005: 38
"Rigdonisms" counted), each on samples rebuilt from held text after Phipps's Tables 2-6, plus the
checks they did not run: leave-one-block-out and held-back blocks of known authorship, and for
Reynolds the same phrases counted in three other doctrinal writers of 1832-37. Local CPU only; no
model reads anything. Card, written first: ``data/private/lab/owner/2026-11-21-other-dictations-2/
card.md`` (section "Their way, rerun (2026-11-23)"); page-cited notes on the three studies:
``docs/research/2026-11-23-lectures-on-faith-originals.md``; settings ``lab.lectures_theirway``.
The result holds names and numbers, no text.

Texts: the Lectures as ``lab.dictations.lectures`` cuts them; the church-paper items from the
centerplace.org issue transcriptions (``lab.sources`` group ``church_papers``), cut by heading and
signature (``ITEMS``); Rigdon's "Gospel" and "Millennium" from the held sidneyrigdon.com pages
(``lab.dictations_v2.series_text``); Smith's journal and letters from the Joseph Smith Papers
files; Pratt's *A Voice of Warning* (1837) from the held OCR.

Usage::

    python -m lab.lectures_theirway plan   # words per sample and item, substitutions (seconds)
    python -m lab.lectures_theirway run    # -> data/lab/reruns/lectures_theirway/result.json
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
from itertools import combinations
from pathlib import Path

import numpy as np

from lab import dictations as dc
from lab import dictations_v2 as d2
from lab import twovoices as tv
from lab.paths import REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "lectures_theirway" / "result.json"
CP = Path("data/private/lab/sources/church_papers")
JSP = Path("data/private/candidates")
VOW = Path("data/candidates/text/ppp-1837-voice-of-warning.txt")
VOW_FROM = 84  # 0-based line of the preface heading (p. iii); the title pages come before
MEN = ("joseph_smith", "sidney_rigdon", "parley_pratt", "oliver_cowdery", "ww_phelps")
SHORT = {"joseph_smith": "JS", "sidney_rigdon": "SR", "parley_pratt": "PP",
         "oliver_cowdery": "OC", "ww_phelps": "WP"}  # fmt: skip

# Church-paper items: (issue page, paragraph that opens it, paragraph that ends it). The item is
# the paragraphs strictly between the two. Read off the pages on 2026-11-23.
ITEMS: dict[str, tuple[str, str, str]] = {
    # Joseph Smith's signed Messenger and Advocate articles (Phipps Table 2)
    "js_youth_1834_12": ("ma_v1n03", r"^BROTHER O\. Cowdery:", r"^JOSEPH SMITH jr\."),
    "js_elders_1835_09": ("ma_v1n12", r"^To the elders of the church of Latter",
                          r"^In the bonds of the new and$"),
    "js_elders_1835_11": ("ma_v2n02", r"^To the elders of the church of the",
                          r"^In the bonds of the new$"),
    "js_elders_1835_12": ("ma_v2n03", r"^To the Elders of the Church",
                          r"^In the bonds of the new and ever"),
    "js_abolition_1836_04": ("ma_v2n07", r"^Brother O\. Cowdery:", r"^Joseph Smith, jr\."),
    # Rigdon's "Faith of the Church of Christ in These Last Days" (unsigned; Reynolds App. 1)
    "fc01": ("ems_v2n17", r"^FAITH OF THE CHURCH OF CHRIST", r"^TO BE CONTINUED"),
    "fc02": ("ems_v2n19", r"^FAITH OF THE CHURCH OF CHRIST", r"^TO BE CONTINUED"),
    "fc03": ("ems_v2n20", r"^FAITH OF THE CHURCH OF CHRIST", r"^TO BE CONTINUED"),
    "fc04": ("ems_v2n21", r"^FAITH OF THE CHURCH OF CHRIST", r"^THE EVENING AND THE MORNING STAR"),
    "fc05": ("ems_v2n22", r"^FAITH OF THE CHURCH OF CHRIST", r"^THE EVENING AND THE MORNING STAR"),
    "fc06": ("ems_v2n23", r"^FAITH OF THE CHURCH OF CHRIST", r"^TO BE CONTINUED"),
    "fc07": ("ems_v2n24", r"^FAITH OF THE CHURCH OF CHRIST", r"^TO BE CONTINUED"),
    "fc08": ("ma_v1n02", r"^FAITH OF THE CHURCH\. No\. VIII", r"^TO BE CONTINUED"),
    "fc09": ("ma_v1n03", r"^FAITH OF THE CHURCH\. NO\. IX", r"^THE GOSPEL\. No\. III"),
    "fc10": ("ma_v1n04", r"^FAITH OF THE CHURCH\. NO\. X\.", r"^Millennium\. No\. XI"),
    "fc11": ("ma_v1n05", r"^FAITH OF THE CHURCH\. No\. XI\.", r"^THE GOSPEL\. No\. V"),
    "fc12": ("ma_v1n06", r"^FAITH OF THE CHURCH\. No\. XII", r"^Millennium\. No\. XIII"),
    "fc13": ("ma_v1n08", r"^Faith of the Church\.$", r"^The elders in the south and west"),
    "fc14": ("ma_v1n09", r"^Faith of the Church\.$", r"^EXTRACT OF A LETTER"),
    "fc15": ("ma_v1n11", r"^Faith of the Church\.$", r"^LO, THE DAYS COME"),
    # Oliver Cowdery's letters to W. W. Phelps (Phipps Table 5 used I-IV, VI, VII)
    "oc01": ("ma_v1n01", r"^Norton, Medina co\. Ohio", r"^O\. Cowdery\.$"),
    "oc02": ("ma_v1n02", r"^LETTER II\.$", r"IS EDITED BY"),
    "oc03": ("ma_v1n03", r"^LETTER III\.$", r"^A SUMMARY$"),
    "oc04": ("ma_v1n05", r"^LETTER IV\.$", r"^OLIVER COWDERY\.$"),
    "oc05": ("ma_v1n06", r"^LETTER V\.-TO W\. W\. PHELPS", r"The weather begins to look"),
    "oc06": ("ma_v1n07", r"^LETTER VI\.$", r"^In consequence of the notices"),
    "oc07": ("ma_v1n10", r"^Letter VII\.$", r"^OLIVER COWDERY\.$"),
    "oc08": ("ma_v2n01", r"^LETTER VIII\.$", r"^As ever your brother in the Lord"),
    # W. W. Phelps (Phipps Table 6 used To Man, 4, 8, To the Saints, 9-12, 2nd series 1)
    "wp_to_man": ("ems_v1n01", r"^TO MAN$", r"^June, 1832\. W\. W\. PHELPS"),
    "wp01": ("ma_v1n02", r"^LETTER NO\. 1\.$", r"^As ever\.$"),
    "wp02": ("ma_v1n03", r"^LETTER NO\. II\.$", r"^As ever, W\. W\. PHELPS"),
    "wp03": ("ma_v1n04", r"^LETTER NO\. III\.$", r"^As ever,$"),
    "wp04": ("ma_v1n05", r"^LETTER No\. 4\.$", r"^Millenium \[Millennium\]\. No\. XII"),
    "wp05": ("ma_v1n06", r"^LETTER No\. V\.$", r"^W\. W\. PHELPS\.$"),
    "wp06": ("ma_v1n07", r"^LETTER NO\. 6\.$", r"^As ever, W\. W\. PHELPS"),
    "wp07": ("ma_v1n08", r"^Letter No\. 7\.$", r"^As ever,$"),
    "wp08": ("ma_v1n09", r"^LETTER NO\. 8\.$", r"^W\. W\. Phelps\.$"),
    "wp_saints": ("ma_v1n09", r"^TO THE SAINTS SCATTERED", r"^BISHOP PARTRIDGE\.$"),
    "wp09": ("ma_v1n10", r"^LETTER NO\. 9\.$", r"^As ever\.$"),
    "wp10": ("ma_v1n12", r"^Letter No\. 10\.$", r"^As ever,$"),
    "wp11": ("ma_v2n01", r"^Letter No\. 11\.$", r"^As ever,$"),
    "wp12": ("ma_v2n02", r"^Letter No\. 12\.$", r"^As ever,$"),
    "wp2s01": ("ma_v2n10", r"^2d\. Series-Letter No\. I\.$", r"^As ever\.$"),
}  # fmt: skip

# Phipps's samples in his tables' order, and each man's held text outside them (held-back blocks).
SMITH_ARTICLES = ["js_youth_1834_12", "js_elders_1835_09", "js_elders_1835_11",
                  "js_elders_1835_12", "js_abolition_1836_04"]  # fmt: skip
SMITH_JOURNAL = ["js-journal-1832-1834.jsonl"]
SMITH_LETTERS = [  # Table 2's letters that are held, in its order
    "js-1831-03-letter-hyrum.jsonl",
    "t73-letter-to-church-leaders-in-jackson-county-missouri-18-augus.jsonl",
    "t73-letter-to-emma-smith-18-may-1834.jsonl",
    "t73-letters-to-john-burk-sally-waterman-phelps-and-almira-mack-s.jsonl",
    "t73-letter-to-sally-waterman-phelps-20-july-1835.jsonl",
    "t73-letter-to-emma-smith-4-november-1838.jsonl",
    "t73-letter-to-emma-smith-12-november-1838.jsonl",
    "t73-letter-to-the-church-and-edward-partridge-20-march-1839.jsonl",
    "t73-letter-to-emma-smith-21-march-1839.jsonl",
    "t73-letter-to-emma-smith-9-november-1839.jsonl",
    "t73-reflections-and-blessings-16-and-23-august-1842.jsonl",
    "t73-letter-to-emma-smith-26-27-june-1844.jsonl",
]
SMITH_EXTRA = ["js-1829-10-22-letter-cowdery.jsonl", "js-1832-06-06-letter-emma.jsonl",
               "js-1832-07-31-letter-phelps.jsonl", "js-1832-10-13-letter-emma.jsonl",
               "js-1832-11-27-letter-phelps.jsonl", "js-1833-01-04-letter-saxton.jsonl",
               "js-1833-01-11-letter-phelps.jsonl"]  # fmt: skip
SUBSTITUTED = {
    "joseph_smith": "not held: Harris 22 Feb 1831, Partridge 1 May 1833, 'Sister' 4 Sep 1833, the "
    "church 16 Dec 1838, Emma 23 Jun 1844, Browning 27 Jun 1844; the 20 Mar 1839 letter to the "
    "church and Partridge stands in for 16 Dec 1838; the Burk/Phelps/Scobey file and the 16 and "
    "23 Aug 1842 file are taken whole (Phipps took the postscripts and 16 Aug only)",
    "parley_pratt": "Shameful Outrage (1835, 3,058 words) not held; A Voice of Warning after "
    "p. 61 stands in for it",
    "all": "quotations: King James 5-gram and scripture 8-gram drops in place of Phipps's hand "
    "removal; quotations from other sources stay in; Phelps's letter poems not removed",
}
RIGDON_SAMPLE = "gospel 1 (Star), fc08, gospel 2-8 (date order of Table 3)"
COWDERY_SAMPLE = ["oc01", "oc02", "oc03", "oc04", "oc06", "oc07"]
COWDERY_EXTRA = ["oc05", "oc08"]
PHELPS_SAMPLE = ["wp_to_man", "wp04", "wp08", "wp_saints", "wp09", "wp10", "wp11", "wp12",
                 "wp2s01"]  # fmt: skip
PHELPS_EXTRA = ["wp01", "wp02", "wp03", "wp05", "wp06", "wp07"]
FC = [f"fc{i:02d}" for i in range(1, 16)]

# Reynolds's Joseph Smith: letters 1829-34 and diaries 1832-36 (p. 28 n. 84).
REYNOLDS_SMITH = [
    "js-1829-10-22-letter-cowdery.jsonl", "js-1831-03-letter-hyrum.jsonl",
    "js-1832-06-06-letter-emma.jsonl", "js-1832-07-31-letter-phelps.jsonl",
    "js-1832-10-13-letter-emma.jsonl", "js-1832-11-27-letter-phelps.jsonl",
    "js-1833-01-04-letter-saxton.jsonl", "js-1833-01-11-letter-phelps.jsonl",
    "t73-letter-to-church-leaders-in-jackson-county-missouri-18-augus.jsonl",
    "t73-note-to-newel-k-whitney-circa-october-1833-early-1834.jsonl",
    "t73-letter-to-emma-smith-18-may-1834.jsonl", "js-letterbook-1.jsonl",
    "js-journal-1832-1834.jsonl", "t73-journal-1835-1836.jsonl",
]  # fmt: skip

# The published numbers compared against.
PUBLISHED = {
    "larsen_1980_appendix_e": {
        1: ("sidney_rigdon", 1.0, None, None),
        2: ("joseph_smith", 0.524, "sidney_rigdon", 0.339),
        3: ("sidney_rigdon", 1.0, None, None),
        4: ("sidney_rigdon", 0.988, "joseph_smith", 0.005),
        5: ("ww_phelps", 0.461, "parley_pratt", 0.367),
        6: ("sidney_rigdon", 1.0, None, None),
        7: ("sidney_rigdon", 0.995, "joseph_smith", 0.005),
        "resubstitution": 0.889,
    },
    "phipps_1977": {
        "test1_table13": {"SR>JS": 291, "SR>PP": 174883, "SR>OC": 1694, "SR>WP": 37154},
        "test4_table16": {"SR>JS": 206, "SR>PP": 3158452, "SR>OC": 16991, "SR>WP": 85357},
        "test8_table20": {1: ("sidney_rigdon", 2623830), 2: ("joseph_smith", 14),
                          3: ("sidney_rigdon", 10), 4: ("joseph_smith", 13),
                          5: ("joseph_smith", 556700), 6: ("joseph_smith", 31),
                          7: ("sidney_rigdon", 7413299)},
        "final_table28": {1: "sidney_rigdon", 2: "sidney_rigdon", 3: "sidney_rigdon",
                          4: "sidney_rigdon", 5: "joseph_smith", 6: "sidney_rigdon",
                          7: "sidney_rigdon"},
    },
    "reynolds_2005": {"rigdon": {"count": 163, "words": 77013, "rate": 2.1},
                      "lectures": {"count": 98, "words": 23750, "rate": 4.1},
                      "joseph_smith": {"count": 0, "words": 78587, "rate": 0.0}},
}  # fmt: skip


# ------------------------------------------------------------------------------ texts


def paragraphs(raw: str) -> list[str]:
    """The paragraphs of a centerplace.org issue page, tags removed, whitespace collapsed."""
    raw = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", raw)
    parts = re.split(r"(?i)<p\b[^>]*>|<br\s*/?>|</h\d>|<h\d[^>]*>|<center>|</center>|<hr[^>]*>",
                     raw)  # fmt: skip
    res = []
    for p in parts:
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p))).strip()
        if t:
            res.append(t)
    return res


def _heading(p: str) -> bool:
    letters = [c for c in p if c.isalpha()]
    return bool(letters) and sum(c.isupper() for c in letters) / len(letters) >= 0.7


def cut(paras: list[str], start: str, end: str) -> str:
    """The paragraphs strictly between the first match of ``start`` and the next of ``end``,
    without page markers, headings, "continued" lines and the editors' bracketed matter."""
    i = next((k for k, p in enumerate(paras) if re.search(start, p)), None)
    if i is None:
        raise OSError(f"start not found: {start}")
    j = next((k for k in range(i + 1, len(paras)) if re.search(end, paras[k])), None)
    if j is None:
        raise OSError(f"end not found: {end}")
    keep = []
    for p in paras[i + 1 : j]:
        if re.match(r"^\(page \d+\)$", p) or _heading(p):
            continue
        if re.match(r"(?i)^[\[(]?\s*(continued|to be continued)", p):
            continue
        keep.append(re.sub(r"\[[^\]]*\]", " ", p))
    return "\n".join(keep)


def item_text(name: str, root: Path = CP) -> str:
    page, start, end = ITEMS[name]
    return cut(paragraphs((root / f"{page}.htm").read_text(encoding="latin-1")), start, end)


def jsp_text(name: str) -> str:
    return dc.strip_editorial("\n".join(r["text"] for r in dc._pages(JSP / name)))


def series_parts(path: Path) -> list[str]:
    """Each ``<blockquote>`` of a sidneyrigdon.com series page, cleaned by v2's rule."""
    raw = path.read_text(encoding="latin-1")
    return [d2.series_text(f"<blockquote>{b}</blockquote>")
            for b in re.findall(r"(?is)<blockquote>(.*?)</blockquote>", raw)]  # fmt: skip


def vow_text(cfg: dict) -> str:
    return tv.read_source(("file", str(VOW), [(VOW_FROM, 10**9)], None), cfg)[0]


def lecture_raw(cfg: dict) -> str:
    """The whole Lectures, catechisms included, as printed in 1835 (pages of ``lab.dictations``)."""
    a, b = cfg["lab"]["dictations"]["lectures_pages"]
    rows = [r for r in dc._pages(dc.DC1835) if dc._page_no(r) is not None
            and a <= dc._page_no(r) <= b]  # fmt: skip
    return dc.strip_editorial("\n".join(r["text"] for r in rows))


def raw_texts(cfg: dict) -> dict[str, dict[str, list[tuple[str, str]]]]:
    """{man: {"sample": [(name, text)], "extra": [(name, text)]}} in Phipps's order."""
    rig = d2.RIGDON
    gospel = series_parts(rig / "gospel_1833_35.htm")
    mill = series_parts(rig / "millennium_1833_35.htm")
    gs = [(f"gospel{i + 1}", t) for i, t in enumerate(gospel)]
    smith_articles = [(n, item_text(n)) for n in SMITH_ARTICLES]
    return {
        "joseph_smith": {
            "articles": smith_articles,
            "letters": [(n, jsp_text(n)) for n in SMITH_LETTERS],
            "journal": [(n, jsp_text(n)) for n in SMITH_JOURNAL],
            "extra": [(n, jsp_text(n)) for n in SMITH_EXTRA],
        },
        "sidney_rigdon": {
            "sample": gs[:1] + [("fc08", item_text("fc08"))] + gs[1:],
            "extra": [(n, item_text(n)) for n in FC if n != "fc08"]
            + [(f"millennium{i + 1}", t) for i, t in enumerate(mill)],
        },
        "parley_pratt": {
            "sample": [("voice_of_warning_1837_from_p_iii", vow_text(cfg))],
            "extra": [],
        },
        "oliver_cowdery": {
            "sample": [(n, item_text(n)) for n in COWDERY_SAMPLE],
            "extra": [(n, item_text(n)) for n in COWDERY_EXTRA],
        },
        "ww_phelps": {
            "sample": [(n, item_text(n)) for n in PHELPS_SAMPLE],
            "extra": [(n, item_text(n)) for n in PHELPS_EXTRA],
        },
    }


# ------------------------------------------------------------------------------ blocks


def masker(cfg: dict):
    """A function text -> tokens: lower-case words, long-s repaired, King James 5-grams and the
    scripture targets' 8-grams dropped (``lab.dictations_v2``)."""
    n = cfg["lab"]["two_voices"]["kjv_ngram"]
    q = d2.settings(cfg)["quote_ngram"]
    vocab, kjv = tv.kjv_vocab_and_grams(n)
    scr = d2.scripture_grams(cfg, vocab, kjv, q)

    def mask(text: str) -> list[str]:
        return tv.drop_kjv(tv.drop_kjv(tv.tokens(text, vocab)[0], kjv, n), scr, q)

    return mask


def blocks_of(toks: list[str], size: int) -> list[list[str]]:
    return [toks[i : i + size] for i in range(0, len(toks) - size + 1, size)]


def build(cfg: dict, texts: dict | None = None, mask=None) -> dict:
    """{"blocks": {man: [6 or 12 token blocks]}, "heldout": {man: [blocks]}, "lectures": {n:
    tokens}, "meta": counts}. Smith's twelve are articles, letters, journal per
    ``smith_class_blocks``; a short class passes its deficit to the next."""
    t = cfg["lab"]["lectures_theirway"]
    size, k, h = t["block_words"], t["blocks"], t["heldout_blocks"]
    if mask is None:
        mask = masker(cfg)
    texts = texts if texts is not None else raw_texts(cfg)
    blocks: dict[str, list[list[str]]] = {}
    held: dict[str, list[list[str]]] = {}
    meta: dict = {"items": {}, "substituted": SUBSTITUTED, "rigdon_sample_order": RIGDON_SAMPLE}
    for man, parts in texts.items():
        streams = {}
        for cls, items in parts.items():
            toks: list[str] = []
            for name, text in items:
                m = mask(text)
                meta["items"][name] = {"man": man, "class": cls, "words_raw": len(text.split()),
                                       "words_masked": len(m)}  # fmt: skip
                toks += m
            streams[cls] = toks
        rest: list[str] = []
        if man == "joseph_smith":
            got, carry = [], 0
            for cls, want in t["smith_class_blocks"].items():
                b = blocks_of(streams[cls], size)
                take = min(len(b), want + carry)
                carry = want + carry - take
                got += b[:take]
                meta.setdefault("smith_blocks_by_class", {})[cls] = take
                rest += streams[cls][take * size :]
            blocks[man] = got
        else:
            b = blocks_of(streams["sample"], size)
            blocks[man] = b[:k]
            rest = streams["sample"][k * size :]
        held[man] = blocks_of(rest + streams.get("extra", []), size)[:h]
        meta.setdefault("men", {})[man] = {
            "masked_words": {c: len(s) for c, s in streams.items()},
            "blocks": len(blocks[man]),
            "heldout_blocks": len(held[man]),
        }
    try:
        lec = dc.lectures(cfg, *tv.kjv_vocab_and_grams(cfg["lab"]["two_voices"]["kjv_ngram"]))
        lectures = {n: d["body"] for n, d in lec.items()}
        meta["lectures_masked_words"] = {n: len(v) for n, v in lectures.items()}
    except OSError as e:
        lectures = {}
        meta["not_attempted_lectures"] = str(e)
    return {"blocks": blocks, "heldout": held, "lectures": lectures, "meta": meta}


# ------------------------------------------------------------------------------ Larsen's way


def arcsine_rates(toks: list[str], words: list[str]) -> np.ndarray:
    n = max(len(toks), 1)
    c = {w: 0 for w in words}
    for w in toks:
        if w in c:
            c[w] += 1
    return np.array([math.asin(math.sqrt(c[w] / n)) for w in words])


def _sscp(X: np.ndarray, y: list[str]) -> tuple[np.ndarray, np.ndarray]:
    T = (X - X.mean(0)).T @ (X - X.mean(0))
    W = np.zeros_like(T)
    for g in set(y):
        Xg = X[[i for i, v in enumerate(y) if v == g]]
        W += (Xg - Xg.mean(0)).T @ (Xg - Xg.mean(0))
    return W, T


def stepwise(X: np.ndarray, y: list[str], k: int) -> list[int]:
    """Forward selection: at each step the variable giving the smallest Wilks's lambda."""
    W, T = _sscp(X, y)
    chosen: list[int] = []
    for _ in range(min(k, X.shape[1])):
        best, lam = None, math.inf
        for j in range(X.shape[1]):
            if j in chosen:
                continue
            s = chosen + [j]
            dt = np.linalg.det(T[np.ix_(s, s)])
            if dt <= 1e-300:
                continue
            v = np.linalg.det(W[np.ix_(s, s)]) / dt
            if v < lam - 1e-15:
                best, lam = j, v
        if best is None:
            break
        chosen.append(best)
    return chosen


class LDA:
    """Linear discriminant classification, pooled covariance, equal priors."""

    def __init__(self, X: np.ndarray, y: list[str]):
        self.groups = sorted(set(y))
        self.mu = np.array([X[[i for i, v in enumerate(y) if v == g]].mean(0)
                            for g in self.groups])  # fmt: skip
        W, _ = _sscp(X, y)
        self.inv = np.linalg.pinv(W / max(len(y) - len(self.groups), 1))

    def posterior(self, x: np.ndarray) -> dict[str, float]:
        s = np.array([x @ self.inv @ m - 0.5 * m @ self.inv @ m for m in self.mu])
        p = np.exp(s - s.max())
        p /= p.sum()
        return dict(zip(self.groups, p.tolist(), strict=True))


def _first_two(post: dict[str, float]) -> tuple[str, float, str, float]:
    r = sorted(post.items(), key=lambda kv: -kv[1])
    return r[0][0], round(r[0][1], 3), r[1][0], round(r[1][1], 3)


def larsen(cfg: dict, b: dict) -> dict:
    t = cfg["lab"]["lectures_theirway"]
    words, k = t["larsen_words"], t["larsen_select"]
    X, y = [], []
    for man, bl in b["blocks"].items():
        for blk in bl:
            X.append(arcsine_rates(blk, words))
            y.append(man)
    X = np.array(X)
    sel = stepwise(X, y, k)
    model = LDA(X[:, sel], y)
    resub = sum(max(model.posterior(x).items(), key=lambda kv: kv[1])[0] == g
                for x, g in zip(X[:, sel], y, strict=True))  # fmt: skip
    loo_hits, loo_fixed = 0, 0
    for i in range(len(y)):
        keep = [j for j in range(len(y)) if j != i]
        yk = [y[j] for j in keep]
        s = stepwise(X[keep], yk, k)
        m = LDA(X[keep][:, s], yk)
        loo_hits += max(m.posterior(X[i, s]).items(), key=lambda kv: kv[1])[0] == y[i]
        m2 = LDA(X[keep][:, sel], yk)
        loo_fixed += max(m2.posterior(X[i, sel]).items(), key=lambda kv: kv[1])[0] == y[i]
    held = {}
    for man, bl in b["heldout"].items():
        got = [max(model.posterior(arcsine_rates(blk, words)[sel]).items(),
                   key=lambda kv: kv[1])[0] for blk in bl]  # fmt: skip
        held[man] = {"blocks": len(bl), "correct": sum(g == man for g in got),
                     "assigned": got}  # fmt: skip
    nh = sum(v["blocks"] for v in held.values())
    lectures, agree = {}, 0
    for n, toks in b["lectures"].items():
        f, p, s, q = _first_two(model.posterior(arcsine_rates(toks, words)[sel]))
        pub = PUBLISHED["larsen_1980_appendix_e"][n]
        agree += f == pub[0]
        lectures[n] = {"first": f, "p": p, "second": s, "p2": q, "published_first": pub[0],
                       "published_p": pub[1], "agree": f == pub[0]}  # fmt: skip
    return {
        "blocks": {m: len(v) for m, v in b["blocks"].items()},
        "selected_words": [words[j] for j in sel],
        "resubstitution": round(resub / len(y), 3),
        "resubstitution_published": PUBLISHED["larsen_1980_appendix_e"]["resubstitution"],
        "leave_one_block_out": round(loo_hits / len(y), 3),
        "leave_one_block_out_fixed_words": round(loo_fixed / len(y), 3),
        "heldout": held,
        "heldout_accuracy": round(sum(v["correct"] for v in held.values()) / nh, 3) if nh else None,
        "chance": round(1 / len(set(y)), 3),
        "lectures": lectures,
        "agree_of_7": agree,
        "reproduced": agree >= t["larsen_min_agree"],
    }


# ------------------------------------------------------------------------------ Phipps's way


def rate(toks: list[str], w: str) -> float:
    return 1000 * sum(x == w for x in toks) / max(len(toks), 1)


def split_counts(a: list[int], b: list[int]) -> tuple[float, tuple[float, float, float, float]]:
    """(median, (a above, b above, a below, b below)) of the pooled block rates; blocks on the
    median are shared out so that half of all blocks lie above it (Phipps p. 29)."""
    v = sorted(a + b)
    n = len(v)
    med = (v[n // 2 - 1] + v[n // 2]) / 2
    if v[n // 2 - 1] < v[n // 2]:
        share = {x: (1.0 if x > med else 0.0) for x in v}
    else:
        tie = v[n // 2]
        above, eq = sum(x > tie for x in v), sum(x == tie for x in v)
        s = (n / 2 - above) / eq
        share = {x: (1.0 if x > tie else s if x == tie else 0.0) for x in v}
    ah, bh = sum(share[x] for x in a), sum(share[x] for x in b)
    return med, (ah, bh, len(a) - ah, len(b) - bh)


def word_odds(a: list[int], b: list[int], target: int, t: dict) -> float | None:
    """Odds that A rather than B wrote the target, from one word; None when skipped."""
    med, (ah, bh, al, bl) = split_counts(a, b)
    if abs(target - med) < t["phipps_skip_within"]:
        return None
    x, y = (ah, bh) if target > med else (al, bl)
    f = t["phipps_floor_cell"]
    return max(x, f) / max(y, f)


def six(man: str, blocks: list[list[str]], w: str) -> list[int]:
    """Six block rates rounded down; Smith's twelve averaged in adjacent pairs first."""
    r = [rate(blk, w) for blk in blocks]
    if len(r) > 6:
        r = [(r[i] + r[i + 1]) / 2 for i in range(0, len(r) - 1, 2)]
    return [math.floor(x) for x in r]


def _target(toks_list: list[list[str]], w: str) -> int:
    return math.floor(sum(rate(x, w) for x in toks_list) / len(toks_list))


def pair_odds(
    b: dict,
    x: str,
    y: str,
    targets: list[list[str]],
    words: list[str],
    t: dict,
    only: set[str] | None = None,
) -> dict:
    """Product of the single-word odds that ``x`` rather than ``y`` wrote the target text(s)."""
    prod, used, per = 1.0, 0, {}
    for w in words:
        if only is not None and w not in only:
            continue
        o = word_odds(six(x, b["blocks"][x], w), six(y, b["blocks"][y], w), _target(targets, w), t)
        if o is None:
            continue
        per[w] = round(o, 3)
        prod *= o
        used += 1
    return {"odds": prod, "words_used": used, "per_word": per}


def _fmt(x: str, y: str, odds: float) -> dict:
    win, lose, o = (x, y, odds) if odds >= 1 else (y, x, 1 / odds)
    return {"favours": win, "over": lose, "odds": round(o, 2)}


def phipps(cfg: dict, b: dict) -> dict:
    t = cfg["lab"]["lectures_theirway"]
    words, strong = t["phipps_words"], t["phipps_strong"]
    lec = [b["lectures"][n] for n in sorted(b["lectures"])]
    res: dict = {"words": words, "test1": {}, "test4": {}}
    for x, y in combinations(MEN, 2):
        key = f"{SHORT[x]}-{SHORT[y]}"
        r1 = pair_odds(b, x, y, lec, words, t)
        res["test1"][key] = _fmt(x, y, r1["odds"]) | {"words_used": r1["words_used"]}
        good = {w for w, o in r1["per_word"].items() if o > strong or o < 1 / strong}
        r4 = pair_odds(b, x, y, lec, words, t, good)
        res["test4"][key] = _fmt(x, y, r4["odds"]) | {"words_used": r4["words_used"]}
    sj = res["test1"]["JS-SR"]
    sr_js = sj["odds"] if sj["favours"] == "sidney_rigdon" else 1 / sj["odds"]
    res["rigdon_over_smith_test1"] = round(sr_js, 2)
    res["rigdon_dominates_all_test1"] = all(
        v["favours"] == "sidney_rigdon" for k, v in res["test1"].items() if "SR" in k
    )
    # Test 8: Smith against Rigdon per lecture, on the words strong for at least one lecture.
    per = {n: pair_odds(b, "joseph_smith", "sidney_rigdon", [b["lectures"][n]], words, t)
           for n in sorted(b["lectures"])}  # fmt: skip
    strong8 = {w for r in per.values() for w, o in r["per_word"].items()
               if o > strong or o < 1 / strong}  # fmt: skip
    res["test8_words"] = sorted(strong8, key=words.index)
    t8, agree = {}, 0
    for n in sorted(b["lectures"]):
        r = pair_odds(b, "joseph_smith", "sidney_rigdon", [b["lectures"][n]], words, t, strong8)
        f = _fmt("joseph_smith", "sidney_rigdon", r["odds"])
        pub = PUBLISHED["phipps_1977"]["test8_table20"][n]
        agree += f["favours"] == pub[0]
        t8[n] = f | {"words_used": r["words_used"], "table20": {"favours": pub[0], "odds": pub[1]},
                     "same_direction": f["favours"] == pub[0]}  # fmt: skip
    res["test8"] = t8
    res["test8_same_direction_of_7"] = agree
    res["reproduced_test1"] = sj["favours"] == "sidney_rigdon" and sr_js > t["phipps_min_odds"]
    res["published"] = {k: v for k, v in PUBLISHED["phipps_1977"].items() if k != "test8_table20"}
    res["known_answer"] = phipps_known(b, words, t)
    return res


def phipps_known(b: dict, words: list[str], t: dict) -> dict:
    """Test-1 odds on each held-back block, for every pair that includes its author."""
    per_man, js_sr = {}, {"blocks": 0, "correct": 0}
    for man, bl in b["heldout"].items():
        wins = tot = 0
        for blk in bl:
            for other in MEN:
                if other == man:
                    continue
                o = pair_odds(b, man, other, [blk], words, t)["odds"]
                wins += o > 1
                tot += 1
                if {man, other} == {"joseph_smith", "sidney_rigdon"}:
                    js_sr["blocks"] += 1
                    js_sr["correct"] += o > 1
        per_man[man] = {"blocks": len(bl), "pairs": tot, "true_author_wins": wins,
                        "share": round(wins / tot, 3) if tot else None}  # fmt: skip
    pairs = sum(v["pairs"] for v in per_man.values())
    won = sum(v["true_author_wins"] for v in per_man.values())
    return {"per_man": per_man, "share_all": round(won / pairs, 3) if pairs else None,
            "smith_vs_rigdon": js_sr}  # fmt: skip


# ------------------------------------------------------------------------------ Reynolds's way


def phrase_stream(text: str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)
    return " ".join(tv.WORD.findall(text.lower()))


def count_phrases(text: str, phrases: dict[str, str]) -> tuple[int, dict[str, int]]:
    s = phrase_stream(text)
    return len(s.split()), {k: len(re.findall(p, s)) for k, p in phrases.items()}


def reynolds_texts(cfg: dict) -> dict[str, list[tuple[str, str]]]:
    rig = d2.RIGDON
    vow = vow_text(cfg)
    return {
        "rigdon": [(n, item_text(n)) for n in FC]
        + [("millennium", "\n".join(series_parts(rig / "millennium_1833_35.htm"))),
           ("gospel", "\n".join(series_parts(rig / "gospel_1833_35.htm")))],
        "joseph_smith": [(n, jsp_text(n)) for n in REYNOLDS_SMITH],
        "lectures": [("lectures_1835_with_catechism", lecture_raw(cfg))],
        "oliver_cowdery": [(n, item_text(n)) for n in COWDERY_SAMPLE + COWDERY_EXTRA],
        "ww_phelps": [(n, item_text(n)) for n in PHELPS_SAMPLE + PHELPS_EXTRA],
        "parley_pratt": [("voice_of_warning_1837", vow)],
    }  # fmt: skip


def reynolds(cfg: dict, texts: dict | None = None) -> dict:
    t = cfg["lab"]["lectures_theirway"]
    phrases, broad = t["reynolds_phrases"], set(t["reynolds_broad"])
    texts = texts if texts is not None else reynolds_texts(cfg)
    corp = {}
    for name, items in texts.items():
        words, per = 0, dict.fromkeys(phrases, 0)
        for _, text in items:
            n, c = count_phrases(text, phrases)
            words += n
            for k, v in c.items():
                per[k] += v
        total = sum(per.values())
        narrow = sum(v for k, v in per.items() if k not in broad)
        corp[name] = {
            "items": [n for n, _ in items],
            "words": words,
            "count": total,
            "rate_per_1000": round(1000 * total / words, 2) if words else None,
            "count_without_broad": narrow,
            "rate_without_broad": round(1000 * narrow / words, 2) if words else None,
            "phrases_found": sum(v > 0 for v in per.values()),
            "per_phrase": per,
        }
    pub, f = PUBLISHED["reynolds_2005"], t["reynolds_factor"]

    def near(x: float | None, target: float) -> bool:
        return x is not None and target / f <= x <= target * f

    rr = {k: corp[k]["rate_per_1000"] for k in corp}
    reproduced = (near(rr.get("rigdon"), pub["rigdon"]["rate"])
                  and near(rr.get("lectures"), pub["lectures"]["rate"])
                  and (rr.get("joseph_smith") or 0) < t["reynolds_smith_max"])  # fmt: skip
    ctrl = {}
    for c in ("oliver_cowdery", "ww_phelps", "parley_pratt"):
        if c in corp and rr.get("rigdon"):
            ctrl[c] = {
                "share_of_rigdon_rate": round(rr[c] / rr["rigdon"], 2),
                "share_of_rigdon_rate_without_broad": round(
                    corp[c]["rate_without_broad"] / corp["rigdon"]["rate_without_broad"], 2
                )
                if corp["rigdon"]["rate_without_broad"]
                else None,
            }
    marks_period = any(v["share_of_rigdon_rate"] >= t["reynolds_control_share"]
                       for v in ctrl.values())  # fmt: skip
    return {"corpora": corp, "published": pub, "reproduced": reproduced, "control": ctrl,
            "control_reaches_share": marks_period,
            "broad_phrases": sorted(broad)}  # fmt: skip


# ------------------------------------------------------------------------------ run


def run(cfg: dict) -> dict:
    b = build(cfg)
    return {
        "exploratory": True,
        "settings": {
            k: v for k, v in cfg["lab"]["lectures_theirway"].items() if k != "reynolds_phrases"
        },
        "samples": b["meta"],
        "larsen": larsen(cfg, b),
        "phipps": phipps(cfg, b),
        "reynolds": reynolds(cfg),
    }


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["plan", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "plan":
        print(json.dumps(build(cfg)["meta"], indent=1))
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = _commit()
    out(OUT).write_text(json.dumps(res, indent=1) + "\n")
    lz, ph, rn = res["larsen"], res["phipps"], res["reynolds"]
    print(
        "Larsen: agree",
        lz["agree_of_7"],
        "of 7; resub",
        lz["resubstitution"],
        "LOO",
        lz["leave_one_block_out"],
        "held-back",
        lz["heldout_accuracy"],
    )
    print(
        "Phipps: SR over JS",
        ph["rigdon_over_smith_test1"],
        "test 8 same direction",
        ph["test8_same_direction_of_7"],
        "known",
        ph["known_answer"]["share_all"],
    )
    print("Reynolds:", {k: v["rate_per_1000"] for k, v in rn["corpora"].items()})
    print("->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
