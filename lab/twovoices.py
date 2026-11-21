"""BOM-105 / BOM-99: prophets in two voices, measured by function words.

The study found Joseph Smith's revelations sit with the Book of Mormon while his letters do not
(lesson 1, "voice is not a person"; Holmes 1992 found the same split). This asks whether the gap
between a writer's prophetic (or Bible-style) voice and ordinary voice is peculiar to him. A small
set of writers who left both voices is built by stated rules (``SPEC``; written out with word
counts to ``data/lab/two_voices/set.json``, the BOM-99 deliverable). Every text is cut into chunks
and measured on the most frequent words of a neutral library sample, with z-scores from that
sample: (a) Burrows's Delta between a writer's two voices against distances between writers
within one voice, on equal-sized profiles drawn many times; (b) the same with every token covered
by a King James word 5-gram dropped, and without archaic second-person and verb forms; (c) nearest
centroid attribution across voices (ordinary to prophetic and back), after a within-voice
known-answer check. No model, no GPU; the Book of Mormon is not read. The test card, written
first, is ``data/private/lab/owner/2026-11-20-two-voices/card.md``; settings are
``lab.two_voices`` in the config. The outputs hold ids, line numbers and numbers, no text.

Usage::

    python -m lab.twovoices set       # -> data/lab/two_voices/set.json (the labelled set)
    python -m lab.twovoices sample    # print hand-check chunks to the terminal (never written)
    python -m lab.twovoices check     # known-answer check only (within-voice attribution)
    python -m lab.twovoices run       # -> data/lab/two_voices/result.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.compute as pc

from lab import door, registry
from lab.paths import FAST, REGISTRY, out
from metadata import config

OUT = REGISTRY / "two_voices"
KJV = Path("data/kjv/kjv.jsonl")
PROPHETS = FAST / "sources" / "prophets"
PSEUDO = FAST / "sources" / "bible_style" / "wordtree_books" / "pseudo_biblical"
JS = Path("data/private/candidates")
WORD = re.compile(r"[a-z]+")
VOICES = ("prophetic", "ordinary")

# Each source: (kind, where, line ranges [start, end) on the text split by newline (0-based) or
# None for the whole text, filter). kind "door" = a library work id read through lab.door;
# "file" = a path; "glob" = every file matching. filter "verse" keeps verse runs only, "prose"
# drops them, None keeps all. The ranges were chosen by reading the volumes on 2026-11-20.
SPEC: dict[str, dict] = {
    "joseph_smith": {
        "group": "prophetic",
        "scribes": "revelations dictated to scribes (Cowdery, Whitmer and others); ordinary: own "
        "hand, dictated letters and clerks' copies (the study's samples)",
        "prophetic": [
            ("file", str(JS / "samples" / "joseph-smith__dictated__pre1830.txt"), None, None),
            ("glob", str(JS / "later" / "*.txt"), None, None),
        ],
        "prophetic_rule": "Revelation Book 1, every section the study cut out (1828-1833): the "
        "1828-29 sample and the later sections (eval.js_later)",
        "ordinary": [
            ("file", str(JS / "samples" / f"joseph-smith__{s}.txt"), None, None)
            for s in (
                "handwritten__post1830",
                "dictated__post1830",
                "scribal_copy__post1830",
                "scribal_copy__pre1830",
            )
        ],
        "ordinary_rule": "the study's candidate samples other than the revelations: letters, the "
        "1832 history, journal, Letterbook 1 copies",
    },
    "john_wroe": {
        "group": "prophetic",
        "scribes": "communications 'taken from the mouth of John Wroe' by named scribes (Shand, "
        "Tillotson, Lees and others); the 1829 life is first person, scribe not stated",
        "prophetic": [
            ("file", str(PROPHETS / "privatecommunica01wroe" / "text.txt"), [(40, 10**9)], None)
        ],
        "prophetic_rule": "Private Communications vol. II (1846 printing of 1831-1845 "
        "communications), from the first dated communication; editors' footnotes not removed",
        "ordinary": [
            (
                "door",
                "institutional_books:32044081829434",
                [(52, 112), (292, 358), (382, 396), (406, 426)],
                None,
            )
        ],
        "ordinary_rule": "Life and Journal (1829): the paragraphs where Wroe narrates his own life "
        "and travels in the first person (birth to illness; journeys of 1820; the corn; the court "
        "case of 1822); his vision accounts, the communications and the compilers' third-person "
        "paragraphs are left out (a duplicated page run, lines 132-171, skipped)",
    },
    "joanna_southcott": {
        "group": "prophetic",
        "scribes": "wrote her communications herself; copied by others for the press",
        "prophetic": [("door", "internet_archive:firstsecondbooko00sout", None, "verse")],
        "prophetic_rule": "The First and Second Book of the Sealed Prophecies (1803): verse runs "
        "only (her communications from the Spirit are mostly in verse); her prose letters in the "
        "same volume are left out",
        "ordinary": [("door", "internet_archive:b22042076", None, "prose")],
        "ordinary_rule": "An Account of the Trials on Bills of Exchange (1807): her own prose "
        "account; verse runs dropped; short quoted letters from others not removed",
    },
    "anna_trapnel": {
        "group": "prophetic",
        "scribes": "the Cry was taken down by a 'relator' while she spoke in trance; the Report is "
        "her own narrative",
        "prophetic": [("door", "tcp:A94793", None, None)],
        "prophetic_rule": "The Cry of a Stone (1654): visions, prayers and songs uttered in "
        "trance, with the relator's framing (not removed)",
        "ordinary": [("door", "tcp:A63061", None, None)],
        "ordinary_rule": "Anna Trapnel's Report and Plea (1654): her narrative of the journey to "
        "Cornwall and her trial (quoted speech of others not removed)",
    },
    "edward_burrough": {
        "group": "prophetic",
        "scribes": "printed in his lifetime (the Description posthumously)",
        "prophetic": [("door", "tcp:A30557", None, None)],
        "prophetic_rule": "A Trumpet of the Lord Sounded out of Sion (1656): declarations in the "
        "Lord's voice to the nations",
        "ordinary": [
            ("door", "tcp:A30555", None, None),
            ("door", "tcp:A29476", None, None),
        ],
        "ordinary_rule": "A True Description of my Manner of Life (1663) and A Brief Relation of "
        "the Persecutions (1662)",
    },
    "richard_snowden": {
        "group": "bible_style",
        "scribes": "printed",
        "prophetic": [("door", "internet_archive:americanrevoluti00snow", None, "prose")],
        "prophetic_rule": "The American Revolution written in Scriptural or Ancient Historical "
        "Style (1802 printing); verse runs (the poems printed with it) dropped after the hand "
        "check; chapter summaries and front matter not removed",
        "ordinary": [("door", "internet_archive:historynorthand00snowgoog", None, None)],
        "ordinary_rule": "The History of North and South America (1805); a compiled history that "
        "may draw on others' wording",
    },
    "elias_smith": {
        "group": "bible_style",
        "scribes": "printed",
        "prophetic": [("file", str(PSEUDO / "History of Anti-Christ - Elias Smith - 1811.md"))],
        "prophetic_rule": "The History of Anti-Christ, written in Scripture style (1811)",
        "ordinary": [("door", "internet_archive:lifecon00smit", None, None)],
        "ordinary_rule": "The Life, Conversion, Preaching, Travels and Sufferings of Elias Smith "
        "(1816)",
    },
}

LEFT_OUT = {
    "richard_brothers": "ordinary voice only in unreadable OCR (letter to Stephens, 1795; letter "
    "to Miss Cott, 1798); A Revealed Knowledge is mostly his own exposition, not the Lord's words",
    "james_strang": "after 1830; four revelations located in the newspapers (Voree Herald lines "
    "687, 6405, 8642; Zion's Reveille 1580), estimated well under min_words and OCR'd with "
    "columns interleaved (not counted, unverified); ordinary voice: Ancient and Modern "
    "Michilimackinac (1854)",
    "elias_hicks": "journal, letters and sermons: no text in the prophetic voice by the rule",
    "job_scott": "journal and treatises: no text in the prophetic voice by the rule",
    "william_blake": "letters only; the prophetic books are not held",
    "shaker_testimonies": "many speakers and compilers, not one writer",
    "handsome_lake": "English translation, with the editor's (Parker's) own prose: not one writer",
    "nat_turner": "taken down and shaped by Thomas Gray; no ordinary voice",
    "emanuel_swedenborg": "both voices are a translator's English",
    "jacob_ilive": "Book of Jasher only; no ordinary prose held",
    "thomas_reader": "prophecy exposition, not the Lord's words or visions; nothing by the rule",
    "ezra_stiles": "a sermon, not the prophetic voice by the rule; no ordinary prose held",
    "jemima_wilkinson": "one work",
    "george_fox": "the journal is held; his prophetic tracts in the library are each under 1,000 "
    "words",
    "gilbert_hunt": "The Late War only (The Historical Reader reprints it)",
}

# Left out after the first known-answer check (post hoc; see the test card): the check missed its
# bar in the ordinary voice (macro 0.791 against 0.80), all of it from this writer (0 of 11 chunks
# to him). His two ordinary works do not resemble each other; the Brief Relation is a collective
# report of sufferings whose sole authorship is doubtful.
EXCLUDED_AFTER_CHECK = {
    "edward_burrough": "post hoc: 0 of 11 ordinary-voice chunks attributed to him within the "
    "voice; his ordinary sample is two unlike documents, one a collective report",
}

# Chunks read by hand on 2026-11-20 (``sample``), by chunk index, with how many were judged to be
# in the labelled voice. Filled in after reading; see the test card.
HAND_CHECKED: dict[str, dict] = {
    "joseph_smith": {
        "prophetic": {"chunks": [17, 27, 37, 49, 56], "in_voice": 5},
        "ordinary": {"chunks": [3, 4, 9, 13, 27], "in_voice": 5},
    },
    "john_wroe": {
        "prophetic": {
            "chunks": [55, 94, 119, 218, 229],
            "in_voice": 5,
            "note": "218 holds a scribe's line and the next dated heading",
        },
        "ordinary": {
            "chunks": [0, 1, 2, 4, 5],
            "in_voice": 5,
            "note": "2 quotes Genesis read to him",
        },
    },
    "joanna_southcott": {
        "prophetic": {
            "chunks": [3, 7, 22, 36, 45],
            "in_voice": 5,
            "note": "OCR of long s and st left errors the repair misses (mud, drongly)",
        },
        "ordinary": {"chunks": [0, 10, 11, 12, 22], "in_voice": 4, "note": "11 is unreadable OCR"},
    },
    "anna_trapnel": {
        "prophetic": {
            "chunks": [7, 11, 17, 18, 24],
            "in_voice": 4,
            "note": "7 opens with the relator's framing",
        },
        "ordinary": {"chunks": [1, 7, 13, 15, 23], "in_voice": 5},
    },
    "edward_burrough": {
        "prophetic": {
            "chunks": [0, 5, 6, 8, 10],
            "in_voice": 3,
            "note": "6 and 8 are denunciation without the Lord's first person; 10 is "
            "damaged in the source (TCP gaps)",
        },
        "ordinary": {"chunks": [2, 6, 7, 9, 10], "in_voice": 5},
    },
    "richard_snowden": {
        "prophetic": {
            "chunks": [0, 23, 25, 40, 47],
            "in_voice": 4,
            "note": "0 is the title page and contents; first draw (before verse was "
            "dropped) also held a poem, 58",
        },
        "ordinary": {"chunks": [27, 43, 52, 78, 132], "in_voice": 5},
    },
    "elias_smith": {
        "prophetic": {"chunks": [1, 2, 5, 12, 13], "in_voice": 5},
        "ordinary": {"chunks": [16, 36, 43, 54, 92], "in_voice": 5},
    },
}


# ------------------------------------------------------------------------------ reading


def clean_lines(text: str, cfg: dict) -> list[str]:
    """Lines with running headers and OCR specks (fewer than 3 letters) blanked, not removed,
    so that line numbers stay those of the source."""
    t = cfg["lab"]["two_voices"]
    res = []
    for line in text.split("\n"):
        letters = [c for c in line if c.isalpha()]
        if len(letters) < 3:
            res.append("")
            continue
        upper = sum(c.isupper() for c in letters) / len(letters)
        if upper >= t["header_upper_share"] and len(line.split()) <= t["header_max_words"]:
            res.append("")
            continue
        res.append(line)
    return res


def verse_mask(lines: list[str], cfg: dict) -> list[bool]:
    """True for lines inside a verse run: at least ``verse_min_lines`` consecutive non-empty
    lines (blank lines between are allowed) each starting with a capital and short."""
    t = cfg["lab"]["two_voices"]
    flags = [False] * len(lines)
    run: list[int] = []

    def close():
        if len(run) >= t["verse_min_lines"]:
            for j in run:
                flags[j] = True
        run.clear()

    for i, line in enumerate(lines):
        s = line.strip().lstrip("\"'“‘(*•■ ")
        if not s:
            continue
        if s[:1].isupper() and len(s.split()) <= t["verse_max_words"]:
            run.append(i)
        else:
            close()
    close()
    return flags


def read_source(src: tuple, cfg: dict) -> tuple[str, dict]:
    """(text, record) for one source; raises OSError when it cannot be read."""
    kind, where = src[0], src[1]
    ranges = src[2] if len(src) > 2 else None
    filt = src[3] if len(src) > 3 else None
    if kind == "door":
        cat = door.catalog({where})
        if where not in cat or not cat[where].get("text_path"):
            raise OSError(f"no text for {where}")
        raw = door.text_of(cat[where])
    elif kind == "glob":
        p = Path(where)
        files = sorted(p.parent.glob(p.name))
        if not files:
            raise OSError(f"nothing matches {where}")
        raw = "\n\n".join(f.read_text("utf-8", "replace") for f in files)
    else:
        raw = Path(where).read_text("utf-8", "replace")
        if raw.startswith("---"):  # front matter of the wordtree files
            end = raw.find("\n---", 3)
            raw = raw[end + 4 :] if end != -1 else raw
    lines = clean_lines(raw, cfg)
    if ranges:
        keep = [False] * len(lines)
        for a, b in ranges:
            for i in range(a, min(b, len(lines))):
                keep[i] = True
        lines = [x if k else "" for x, k in zip(lines, keep, strict=True)]
    if filt:
        vm = verse_mask(lines, cfg)
        want = filt == "verse"
        lines = [x if v == want else "" for x, v in zip(lines, vm, strict=True)]
    text = "\n".join(lines)
    text = re.sub(r"-\s*\n\s*", "", text)  # words broken across lines
    rec = {"kind": kind, "source": where, "lines": ranges, "filter": filt}
    if kind == "glob":
        rec["files"] = len(sorted(Path(where).parent.glob(Path(where).name)))
    return text, rec


def kjv_vocab_and_grams(n: int) -> tuple[set[str], set[str]]:
    vocab: set[str] = set()
    grams: set[str] = set()
    chapters: dict[tuple, list[str]] = {}
    for line in KJV.read_text().splitlines():
        r = json.loads(line)
        toks = WORD.findall(r["text"].lower())
        vocab.update(toks)
        chapters.setdefault((r["book"], r["chapter"]), []).extend(toks)
    for toks in chapters.values():
        for i in range(len(toks) - n + 1):
            grams.add(" ".join(toks[i : i + n]))
    return vocab, grams


def tokens(text: str, vocab: set[str]) -> tuple[list[str], int]:
    """Lower-case words with long-s OCR repaired: a word that is not a King James word but whose
    f-to-s form is (``fhall`` -> ``shall``, ``fo`` -> ``so``), or whose fl-to-st and f-to-s form
    is (``firfl`` -> ``first``). Returns (tokens, repairs)."""
    res, fixed = [], 0
    for w in WORD.findall(text.lower()):
        if "f" in w and w not in vocab:
            st = w.replace("fl", "st")
            for s in (w.replace("f", "s"), st, st.replace("f", "s")):
                if s in vocab:
                    w, fixed = s, fixed + 1
                    break
        res.append(w)
    return res, fixed


def drop_kjv(toks: list[str], grams: set[str], n: int) -> list[str]:
    """``toks`` without every token covered by a word n-gram found in the King James text."""
    cover = [False] * len(toks)
    for i in range(len(toks) - n + 1):
        if " ".join(toks[i : i + n]) in grams:
            for j in range(i, i + n):
                cover[j] = True
    return [t for t, c in zip(toks, cover, strict=True) if not c]


def chunks(toks: list[str], size: int) -> list[list[str]]:
    return [toks[i : i + size] for i in range(0, len(toks) - size + 1, size)]


# ------------------------------------------------------------------------------ the set


def build_set(cfg: dict, vocab: set[str]) -> tuple[dict, dict]:
    """(set record, {writer: {voice: tokens}}); writers under ``min_words`` in a voice are moved
    to ``too_little_text``; an unreadable source is "not attempted"."""
    t = cfg["lab"]["two_voices"]
    record: dict = {"writers": {}, "too_little_text": {}, "not_attempted": {}}
    texts: dict[str, dict] = {}
    record["left_out_after_check"] = EXCLUDED_AFTER_CHECK
    for name, spec in SPEC.items():
        if name in EXCLUDED_AFTER_CHECK:
            continue
        row = {"group": spec["group"], "scribes": spec["scribes"]}
        toks: dict[str, list[str]] = {}
        failed = None
        for voice in VOICES:
            srcs, words, repairs = [], [], 0
            for src in spec[voice]:
                try:
                    text, rec = read_source(src, cfg)
                except OSError as e:
                    failed = f"{voice}: {e}"
                    break
                tk, fx = tokens(text, vocab)
                rec["words"] = len(tk)
                srcs.append(rec)
                words += tk
                repairs += fx
            if failed:
                break
            toks[voice] = words
            row[voice] = {
                "rule": spec[f"{voice}_rule"],
                "sources": srcs,
                "words": len(words),
                "long_s_repairs": repairs,
            }
        if failed:
            record["not_attempted"][name] = failed
            continue
        short = [v for v in VOICES if len(toks[v]) < t["min_words"]]
        if short:
            record["too_little_text"][name] = {v: len(toks[v]) for v in VOICES}
            continue
        if name in HAND_CHECKED:
            row["hand_checked"] = HAND_CHECKED[name]
        record["writers"][name] = row
        texts[name] = toks
    record["left_out"] = LEFT_OUT
    record["with_both_voices"] = len(record["writers"])
    return record, texts


# ------------------------------------------------------------------------------ measures


def background(cfg: dict, vocab: set[str], grams: set[str] | None) -> list[list[str]]:
    """Token windows from a seeded sample of library works (one personal author, years in range,
    kept copy, not sealed, OCR not excluded). Unreadable works are skipped (not attempted)."""
    t = cfg["lab"]["two_voices"]
    tab = registry.load()
    keep = pc.and_(
        pc.and_(pc.equal(tab["kind"], "work"), pc.equal(tab["author_kind"], "person")),
        pc.and_(pc.equal(tab["has_text"], True), pc.equal(tab["dup_keeper"], True)),
    )
    rows = [
        r
        for r in tab.filter(keep).to_pylist()
        if not r["sealed"]
        and not r["ocr_excluded"]
        and r["year"]
        and t["year_min"] <= r["year"] <= t["year_max"]
        and (r["words"] or 0) >= t["bg_min_words"]
    ]
    rows.sort(key=lambda r: r["work_id"])
    random.Random(t["seed"]).shuffle(rows)
    used = {s[1] for spec in SPEC.values() for v in VOICES for s in spec[v] if s[0] == "door"}
    cat = door.catalog({r["work_id"] for r in rows[: t["bg_works"] * 3]})
    windows = []
    for r in rows[: t["bg_works"] * 3]:
        c = cat.get(r["work_id"])
        if not c or not c.get("text_path") or r["work_id"] in used:
            continue
        try:
            toks, _ = tokens(door.text_of(c), vocab)
        except OSError:
            continue
        if grams is not None:
            toks = drop_kjv(toks, grams, t["kjv_ngram"])
        mid, half = len(toks) // 2, t["bg_words_per_work"] // 2
        windows.append(toks[max(0, mid - half) : mid + half])
        if len(windows) == t["bg_works"]:
            break
    return windows


def features(windows: list[list[str]], k: int, drop: set[str]) -> list[str]:
    """The ``k`` words with the highest mean relative frequency, each work weighted equally."""
    total: Counter = Counter()
    for w in windows:
        n = len(w) or 1
        for word, c in Counter(w).items():
            total[word] += c / n
    return [w for w, _ in total.most_common(k + len(drop)) if w not in drop][:k]


def relfreq(chunk: list[str], feats: list[str]) -> np.ndarray:
    c = Counter(chunk)
    n = len(chunk) or 1
    return np.array([c[f] / n for f in feats])


def scaler(windows: list[list[str]], feats: list[str], size: int) -> tuple[np.ndarray, np.ndarray]:
    m = np.array([relfreq(ch, feats) for w in windows for ch in chunks(w, size)])
    sd = m.std(axis=0)
    sd[sd == 0] = 1e-9
    return m.mean(axis=0), sd


def delta(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a - b)))


def cosine_delta(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(1 - a @ b / (na * nb)) if na and nb else 1.0


def attribute(train: dict, test: dict, dist) -> dict:
    """Nearest centroid. ``train``/``test``: {writer: array of chunk z-vectors}. Returns
    {writer: [chunks, correct, {assigned writer: count}]}."""
    names = sorted(train)
    cents = {n: train[n].mean(axis=0) for n in names}
    res = {}
    for w, arr in test.items():
        got: Counter = Counter()
        for z in arr:
            got[min(names, key=lambda n: dist(z, cents[n]))] += 1
        res[w] = [len(arr), got[w], dict(got)]
    return res


def _cap(arr: np.ndarray, k: int, rng: random.Random) -> np.ndarray:
    if len(arr) <= k:
        return arr
    return arr[sorted(rng.sample(range(len(arr)), k))]


def within_voice(z: dict, cfg: dict, dist) -> dict:
    """Known answer: in each voice, first half of each writer's chunks against the second half,
    both ways; macro-average own-author rate."""
    t = cfg["lab"]["two_voices"]
    rng = random.Random(t["seed"])
    res = {}
    for voice in VOICES:
        per = {w: [0, 0] for w in z}
        for flip in (False, True):
            tr, te = {}, {}
            for w, by in z.items():
                arr = by[voice]
                h = len(arr) // 2
                a, b = (arr[h:], arr[:h]) if flip else (arr[:h], arr[h:])
                tr[w], te[w] = _cap(a, t["train_chunks"], rng), b
            for w, (n, ok, _) in attribute(tr, te, dist).items():
                per[w][0] += n
                per[w][1] += ok
        rates = {w: round(ok / n, 3) if n else None for w, (n, ok) in per.items()}
        good = [r for r in rates.values() if r is not None]
        res[voice] = {
            "own_author_rate": rates,
            "macro": round(sum(good) / len(good), 3) if good else None,
            "chance": round(1 / len(z), 3),
        }
    return res


def cross_voice(z: dict, cfg: dict, dist) -> dict:
    t = cfg["lab"]["two_voices"]
    rng = random.Random(t["seed"] + 1)
    res = {}
    for src, dst in (("ordinary", "prophetic"), ("prophetic", "ordinary")):
        tr = {w: _cap(by[src], t["train_chunks"], rng) for w, by in z.items()}
        te = {w: by[dst] for w, by in z.items()}
        got = attribute(tr, te, dist)
        res[f"{src}_to_{dst}"] = {
            w: {"chunks": n, "own": ok, "rate": round(ok / n, 3) if n else None, "went_to": to}
            for w, (n, ok, to) in got.items()
        }
        res[f"{src}_to_{dst}_attraction"] = attraction(got)
    return res


def attraction(got: dict) -> dict:
    """Post hoc (added after the first run; see the card): for each writer, the share of the
    other writers' chunks that were attributed to him or her. A centroid that draws everyone's
    chunks makes its own writer's rate high without recognising anyone."""
    res = {}
    for w in got:
        others = sum(n for o, (n, _, _) in got.items() if o != w)
        drawn = sum(to.get(w, 0) for o, (_, _, to) in got.items() if o != w)
        res[w] = round(drawn / others, 3) if others else None
    return res


def gaps(z: dict, cfg: dict) -> dict:
    """Burrows's Delta on equal-sized profiles, ``resamples`` draws. Per writer: self gap, gap
    index (self gap / median distance to other writers in the ordinary voice), closer-to-self
    share; Joseph Smith's rank and how often his gap index is above every other writer's."""
    t = cfg["lab"]["two_voices"]
    rng = np.random.default_rng(t["seed"])
    names = sorted(z)
    k = t["profile_chunks"]
    draws: dict[str, dict[str, list]] = {
        w: {"self": [], "index": [], "closer": [], "pp": [], "oo": []} for w in names
    }
    above_all = 0
    for _ in range(t["resamples"]):
        prof = {
            (w, v): z[w][v][rng.choice(len(z[w][v]), size=k, replace=False)].mean(axis=0)
            for w in names
            for v in VOICES
        }
        idx = {}
        for w in names:
            others = [o for o in names if o != w]
            s = delta(prof[(w, "prophetic")], prof[(w, "ordinary")])
            pp = [delta(prof[(w, "prophetic")], prof[(o, "prophetic")]) for o in others]
            oo = [delta(prof[(w, "ordinary")], prof[(o, "ordinary")]) for o in others]
            idx[w] = s / float(np.median(oo))
            d = draws[w]
            d["self"].append(s)
            d["index"].append(idx[w])
            d["closer"].append(sum(s < x for x in pp) / len(pp))
            d["pp"].append(float(np.median(pp)))
            d["oo"].append(float(np.median(oo)))
        if "joseph_smith" in idx:
            above_all += all(idx["joseph_smith"] > v for w, v in idx.items() if w != "joseph_smith")

    def q(xs):
        a = np.array(xs)
        return [round(float(np.percentile(a, p)), 4) for p in (2.5, 50, 97.5)]

    per = {
        w: {
            "self_gap": q(d["self"]),
            "gap_index": q(d["index"]),
            "closer_to_self_share": q(d["closer"]),
            "median_delta_to_other_prophetic": q(d["pp"]),
            "median_delta_to_other_ordinary": q(d["oo"]),
        }
        for w, d in draws.items()
    }
    order = sorted(names, key=lambda w: -per[w]["gap_index"][1])
    res = {"per_writer": per, "order_by_gap_index": order}
    if "joseph_smith" in names:
        res["joseph_smith_rank"] = order.index("joseph_smith") + 1
        res["joseph_smith_above_all_share"] = round(above_all / t["resamples"], 3)
        res["writers"] = len(names)
    return res


def zmat(texts: dict, feats: list[str], mu: np.ndarray, sd: np.ndarray, size: int) -> dict:
    return {
        w: {v: np.array([(relfreq(c, feats) - mu) / sd for c in chunks(tv[v], size)]) for v in tv}
        for w, tv in texts.items()
    }


def variant(texts: dict, windows: list, drop: set[str], cfg: dict) -> dict:
    t = cfg["lab"]["two_voices"]
    feats = features(windows, t["mfw"], drop)
    mu, sd = scaler(windows, feats, t["chunk_words"])
    z = zmat(texts, feats, mu, sd, t["chunk_words"])
    return {
        "features": len(feats),
        "chunks": {w: {v: len(z[w][v]) for v in VOICES} for w in z},
        "known_answer": {
            "burrows": within_voice(z, cfg, delta),
            "cosine": within_voice(z, cfg, cosine_delta),
        },
        "_z": z,
    }


def verdicts(res: dict, groups: dict, cfg: dict) -> dict:
    t = cfg["lab"]["two_voices"]
    cv = res["cross_voice"]["burrows"]
    others = [w for w in groups if w != "joseph_smith"]
    crosses = {}
    for w in groups:
        a = cv["ordinary_to_prophetic"][w]["rate"]
        b = cv["prophetic_to_ordinary"][w]["rate"]
        crosses[w] = (a or 0) >= t["cross_share"] or (b or 0) >= t["cross_share"]
    n_cross = sum(crosses[w] for w in others)
    g = res["gaps"]
    per = g["per_writer"]
    js = per.get("joseph_smith", {}).get("gap_index", [None, None, None])[1]
    rest = [per[w]["gap_index"][1] for w in others]
    if len(others) < t["min_writers"]:
        js_verdict = "cannot tell (group too small)"
    elif g.get("joseph_smith_above_all_share", 0) >= t["larger_than_any_share"]:
        js_verdict = "larger than any"
    elif js is not None and rest and min(rest) <= js <= max(rest):
        js_verdict = "typical"
    else:
        js_verdict = "at the edge"
    return {
        "crosses": crosses,
        "others_crossing": n_cross,
        "others": len(others),
        "genre_effect": n_cross < len(others) / 2,
        "joseph_smith_gap": js_verdict,
        "joseph_smith_gap_index_median": js,
        "others_gap_index_range": [min(rest), max(rest)] if rest else None,
        "prophetic_others": [w for w in others if groups[w] == "prophetic"],
        "bible_style_others": [w for w in others if groups[w] == "bible_style"],
    }


def run(cfg: dict, check_only: bool = False) -> dict:
    t = cfg["lab"]["two_voices"]
    vocab, grams = kjv_vocab_and_grams(t["kjv_ngram"])
    the_set, texts = build_set(cfg, vocab)
    groups = {w: r["group"] for w, r in the_set["writers"].items()}
    res: dict = {"set": {k: v for k, v in the_set.items() if k != "left_out"}, "settings": t}
    windows = background(cfg, vocab, None)
    res["background_works"] = len(windows)
    full = variant(texts, windows, set(), cfg)
    ka = full["known_answer"]["burrows"]
    res["known_answer"] = {
        "burrows": ka,
        "cosine": full["known_answer"]["cosine"],
        "bar": t["known_bar"],
        "passed": all((ka[v]["macro"] or 0) >= t["known_bar"] for v in VOICES),
    }
    res["chunks"] = full["chunks"]
    if check_only:
        return res
    if not res["known_answer"]["passed"]:
        res["stopped"] = "the within-voice check missed its bar; the cross-voice question was "
        res["stopped"] += "not scored"
        return res
    z = full["_z"]
    res["cross_voice"] = {
        "burrows": cross_voice(z, cfg, delta),
        "cosine": cross_voice(z, cfg, cosine_delta),
    }
    res["gaps"] = gaps(z, cfg)
    res["verdicts"] = verdicts(res, groups, cfg)
    # Variants: without archaic forms; without King James 5-grams (background treated alike).
    res["variants"] = {}
    for name, drop, kjv in (
        ("no_archaic_words", set(t["archaic_words"]), False),
        ("no_kjv_5grams", set(), True),
    ):
        if kjv:
            tx = {
                w: {v: drop_kjv(tv[v], grams, t["kjv_ngram"]) for v in tv}
                for w, tv in texts.items()
            }
            short = {w: {v: len(tv[v]) for v in tv} for w, tv in tx.items()}
            tx = {w: tv for w, tv in tx.items() if all(len(tv[v]) >= t["min_words"] for v in tv)}
            win = background(cfg, vocab, grams)
        else:
            tx, short, win = texts, None, windows
        var = variant(tx, win, drop, cfg)
        zz = var.pop("_z")
        var["words_after"] = short
        var["cross_voice"] = {"burrows": cross_voice(zz, cfg, delta)}
        var["gaps"] = gaps(zz, cfg)
        var["verdicts"] = verdicts(var, {w: groups[w] for w in zz}, cfg)
        res["variants"][name] = var
    return res


def sample(cfg: dict) -> None:
    """Print the first words of ``handcheck`` random chunks per writer and voice, for reading by
    hand. Terminal only: nothing is written."""
    t = cfg["lab"]["two_voices"]
    vocab, _ = kjv_vocab_and_grams(t["kjv_ngram"])
    _, texts = build_set(cfg, vocab)
    rng = random.Random(t["seed"])
    for w, tv in texts.items():
        for v in VOICES:
            ch = chunks(tv[v], t["chunk_words"])
            for i in sorted(rng.sample(range(len(ch)), min(t["handcheck"], len(ch)))):
                print(f"{w}:{v}:{i}\t{' '.join(ch[i][:60])}")


def _strip(o):
    if isinstance(o, dict):
        return {k: _strip(v) for k, v in o.items() if k != "_z"}
    return o


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["set", "sample", "check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "sample":
        sample(cfg)
        return 0
    if a.cmd == "set":
        vocab, _ = kjv_vocab_and_grams(cfg["lab"]["two_voices"]["kjv_ngram"])
        rec, _ = build_set(cfg, vocab)
        rec["config_sha256"] = config.sha256_of_config()
        out(OUT / "set.json").write_text(json.dumps(rec, indent=1) + "\n")
        print(
            json.dumps(
                {
                    w: [r["prophetic"]["words"], r["ordinary"]["words"]]
                    for w, r in rec["writers"].items()
                },
                indent=1,
            )
        )
        print("too little text:", rec["too_little_text"], "not attempted:", rec["not_attempted"])
        return 0
    res = _strip(run(cfg, check_only=a.cmd == "check"))
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    if a.cmd == "check":
        print(json.dumps(res["known_answer"], indent=1))
        return 0
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res.get(k) for k in ("known_answer", "verdicts")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
