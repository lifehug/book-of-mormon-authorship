"""Replications of the published Book of Mormon stylometry (BOM-22).

The designs are fixed in ``docs/prior-studies.md``, written before anything here ran. This runs
each *published* method on the 1830 text, the one exception 4.2 makes to the seal; none of the
project's own methods is used, and nothing here feeds a calibration or a threshold.

This module so far holds the shared units:

* ``modern_chapters``: the 239 modern chapters (the units of Jockers, Witten and Criddle 2008),
  located in the 1830 text. Project Gutenberg's public-domain text (ebook 17, the 1920 edition)
  supplies the chapter divisions only; each chapter's first words are found in the 1830 text of
  the same book by fuzzy alignment (the later edition corrected the grammar), and the 1830 text is
  cut there.

Usage::

    python -m eval.replicate chapters     # -> data/benchmark/replication/chapters_1830.jsonl
    python -m eval.replicate jockers      # -> data/benchmark/replication_jockers.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from rapidfuzz import fuzz

from classic import tokenize

DIR = Path("data/benchmark/replication")
GUTENBERG = DIR / "book-of-mormon-pg17.txt"
EDITION = Path("data/bom/1830/edition_1830.jsonl")
CHAPTERS = DIR / "chapters_1830.jsonl"
# long enough that formula openings ("in the commencement of the ... year") differ
ANCHOR_WORDS = 30
NEAR_BEST = 5  # points below the best that still count as a match
MIN_ANCHOR = 80
BOOKS = [
    "1 Nephi",
    "2 Nephi",
    "Jacob",
    "Enos",
    "Jarom",
    "Omni",
    "Words of Mormon",
    "Mosiah",
    "Alma",
    "Helaman",
    "3 Nephi",
    "4 Nephi",
    "Mormon",
    "Ether",
    "Moroni",
]
_TITLES = {  # Gutenberg's book title lines, for the books without chapter headings too
    "Enos": "THE BOOK OF ENOS",
    "Jarom": "THE BOOK OF JAROM",
    "Omni": "THE BOOK OF OMNI",
    "Words of Mormon": "THE WORDS OF MORMON",
    "4 Nephi": "FOURTH NEPHI",
}


def modern_openings() -> list[tuple[str, int, str]]:
    """(book, chapter, first verse text) for every modern chapter, in order."""
    t = GUTENBERG.read_text(encoding="utf-8")
    t = t[t.find("*** START") : t.find("*** END")]
    verse = re.compile(r"(?m)^(\d+):1 (.+(?:\n(?!\d+:\d+ ).+)*)")
    out = []
    for book in BOOKS:
        if book in _TITLES:
            i = t.find(_TITLES[book], t.find("Contents") + 2000)
            m = verse.search(t, i)
            out.append((book, 1, " ".join(m.group(2).split())))
            continue
        for h in re.finditer(rf"(?m)^{re.escape(book)} Chapter (\d+)\s*$", t):
            m = verse.search(t, h.end())
            out.append((book, int(h.group(1)), " ".join(m.group(2).split())))
    return out


def edition_by_book() -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for ln in EDITION.read_text().splitlines():
        r = json.loads(ln)
        if r["book"]:
            by.setdefault(r["book"], []).append(r)
    return by


def locate(opening: str, windows: list[str]) -> tuple[int, float]:
    """The earliest window that matches ``opening``'s first words nearly as well as the best.

    Taking the best alone fails on the book's formulas: Alma 2's "And it came to pass in the
    commencement of the fifth year" scored a hair lower than "... of the ninth year" much later,
    and the later match swallowed the chapters between. Chapters run in order, so the true
    opening is the earliest strong match.
    """
    from rapidfuzz import process

    probe = " ".join(tokenize(opening)[:ANCHOR_WORDS])
    scores = process.cdist([probe], windows, scorer=fuzz.ratio)[0]
    best = float(scores.max())
    good = [k for k, v in enumerate(scores) if v >= max(best - NEAR_BEST, MIN_ANCHOR)]
    k = good[0] if good else int(scores.argmax())
    return k, float(scores[k])


def chapters() -> int:
    from ocr_fix.normalize import artifacts

    openings = modern_openings()
    by = edition_by_book()
    out = []
    for book in BOOKS:
        paras = by[book]
        words, owner = [], []
        for p in paras:
            toks = tokenize(artifacts(p["text"])[0])
            words += toks
            owner += [p["seq"]] * len(toks)
        chs = [(c, o) for b, c, o in openings if b == book]
        windows = [
            " ".join(words[i : i + ANCHOR_WORDS])
            for i in range(max(1, len(words) - ANCHOR_WORDS + 1))
        ]
        starts = []
        for k, (c, o) in enumerate(chs):
            if c == 1:
                starts.append((c, 0, 100.0))
                continue
            # after the previous chapter's anchor, leaving room for the chapters still to come
            lo = starts[-1][1] + 1
            hi = len(windows) - (len(chs) - k - 1)
            j, s = locate(o, windows[lo:hi])
            starts.append((c, lo + j, s))
        for k, (c, i, s) in enumerate(starts):
            j = starts[k + 1][1] if k + 1 < len(starts) else len(words)
            out.append(
                {
                    "book": book,
                    "chapter": c,
                    "start_word": i,
                    "end_word": j,
                    "seq_first": owner[i],
                    "seq_last": owner[j - 1],
                    "words": j - i,
                    "anchor_score": round(s, 1),
                    "text": " ".join(words[i:j]),
                }
            )
    DIR.mkdir(parents=True, exist_ok=True)
    with CHAPTERS.open("w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    weak = [r for r in out if r["anchor_score"] < 80]
    print(
        f"{len(out)} chapters, {sum(r['words'] for r in out):,} words; "
        f"anchors under 80: {[(r['book'], r['chapter'], r['anchor_score']) for r in weak]}"
    )
    return 0


# ---------------------------------------------------------------- Jockers, Witten and Criddle

HIAWATHA = DIR / "longfellow-hiawatha-pg19.txt"
COLUMBIAD = "institutional_books:HXTAZ5"
JOCKERS_OUT = DIR.parent / "replication_jockers.json"
SAMPLE_WORDS = 2000  # our candidates' texts are cut to about the published average sample size
MIN_MEAN_FREQ = 0.001  # Jockers et al.: mean relative frequency of at least 0.1%
DROPPED = {"god", "ye", "thy", "behold"}  # removed by Jockers et al.


def _chunks(tokens: list[str], n: int) -> list[list[str]]:
    k = max(1, round(len(tokens) / n))
    size = -(-len(tokens) // k)
    return [tokens[i : i + size] for i in range(0, len(tokens), size)]


def _kjv(books: set[str]) -> list[tuple[str, list[str]]]:
    by: dict[str, list[str]] = {}
    for ln in Path("data/kjv/kjv.jsonl").read_text().splitlines():
        r = json.loads(ln)
        if r["book"] in books:
            by.setdefault(f"{r['book']} {r['chapter']}", []).append(r["text"])
    return [(k, tokenize(" ".join(v))) for k, v in by.items()]


def _hiawatha() -> list[tuple[str, list[str]]]:
    t = HIAWATHA.read_text(encoding="utf-8")
    t = t[t.find("Should you ask me") : t.find("\nVOCABULARY")]
    parts = re.split(r"(?m)^(?:[IVX]+)\s*$", t)
    return [(f"Hiawatha {i}", tokenize(p)) for i, p in enumerate(parts) if tokenize(p)]


def _candidate_tokens() -> dict[str, list[str]]:
    """Unmasked text per candidate, as Jockers et al. used it: our candidate units by author."""
    from eval.timesplit import ADMITTED  # noqa: F401  (provenance is not Jockers' concern)
    from kjv_mask.run import _docs
    from ocr_fix.candidates import units

    meta = {"cand:" + u["unit"].replace(":", "__"): u["author"] for u in units()}
    out: dict[str, list[str]] = {}
    for d in _docs("candidates"):
        who = meta.get(d["id"])
        if who is None:
            person = d["id"].removeprefix("cand:").split("__")[0]
            who = person.replace("-", " ").title()
        out.setdefault(who, []).extend(tokenize(d["load"]()))
    return out


def jockers_known() -> dict[str, list[tuple[str, list[str]]]]:
    """The seven-author design: four candidates, Isaiah-Malachi, and the two controls."""
    from eval.benchmark import _masked_tokens

    cand = _candidate_tokens()
    known = {
        a: [(f"{a} {i}", c) for i, c in enumerate(_chunks(cand[name], SAMPLE_WORDS))]
        for a, name in (
            ("cowdery", "Oliver Cowdery"),
            ("pratt", "Parley P. Pratt"),
            ("rigdon", "Sidney Rigdon"),
            ("spalding", "Solomon Spalding"),
        )
    }
    known["isaiah_malachi"] = _kjv({"ISA", "MAL"})
    columbiad = list(_masked_tokens([COLUMBIAD]).values())[0]
    known["barlow"] = [
        (f"Columbiad {i}", c) for i, c in enumerate(_chunks(columbiad, len(columbiad) // 12))
    ]
    known["longfellow"] = _hiawatha()
    return known


def jockers_features(known: dict, chapters: list[list[str]]) -> list[str]:
    """Words in every author's samples and in the Book of Mormon, mean relative frequency at
    least 0.1% across all samples, minus god, ye, thy and behold (Jockers et al. 2008)."""
    from collections import Counter

    docs = [t for v in known.values() for _, t in v] + chapters
    in_all = set.intersection(
        *[{w for _, t in v for w in t} for v in known.values()], {w for t in chapters for w in t}
    )
    rel: Counter = Counter()
    for t in docs:
        c = Counter(t)
        for w in in_all:
            rel[w] += c[w] / max(1, len(t))
    return sorted(w for w in in_all if rel[w] / len(docs) >= MIN_MEAN_FREQ and w not in DROPPED)


def jockers_methods(
    known: dict,
    chapters: list[list[str]],
    features: list[str],
    shrinkage_grid: list[float],
    seed: int,
) -> dict:
    """Delta and closed-set nearest shrunken centroids, each chapter's first and second author.

    As published: relative frequencies over the selected words, each column centred and scaled
    over all samples (known and Book of Mormon). Delta ranks authors by mean absolute difference
    of z-scores from each author's mean profile. NSC uses the centroid shrinkage with the lowest
    cross-validated error on the known samples (Jockers et al. tuned pamr the same way) and
    ranks by posterior; its "none of the above" rule is switched off, as theirs had none.
    """
    import random

    import numpy as np

    from classic import ENSC, frequency_matrix, word_counts

    authors = sorted(known)
    docs = [t for a in authors for _, t in known[a]]
    labels = [a for a in authors for _ in known[a]]
    X = frequency_matrix([word_counts(t) for t in docs], features)
    C = frequency_matrix([word_counts(t) for t in chapters], features)
    allm = np.vstack([X, C])
    mu, sd = allm.mean(axis=0), allm.std(axis=0)
    sd[sd == 0] = 1
    Xz, Cz = (X - mu) / sd, (C - mu) / sd
    prof = {a: Xz[[i for i, y in enumerate(labels) if y == a]].mean(axis=0) for a in authors}

    def delta_rank(z):
        d = {a: float(np.mean(np.abs(z - prof[a]))) for a in authors}
        return sorted(authors, key=lambda a: d[a])

    # shrinkage by 5-fold cross-validation on the known samples
    rng = random.Random(seed)
    idx = list(range(len(docs)))
    rng.shuffle(idx)
    cv = {}
    for s_ in shrinkage_grid:
        err = 0
        for f in range(5):
            test = set(idx[f::5])
            tr = [i for i in idx if i not in test]
            m = ENSC(shrinkage=s_, alpha=0.0, priors="proportional").fit(
                Xz[tr], [labels[i] for i in tr]
            )
            err += sum(
                max(m.posteriors(Xz[i]).items(), key=lambda kv: kv[1])[0] != labels[i] for i in test
            )
        cv[s_] = err / len(docs)
    best = min(shrinkage_grid, key=lambda s_: (cv[s_], s_))
    nsc = ENSC(shrinkage=best, alpha=0.0, priors="proportional").fit(Xz, labels)

    def nsc_rank(z):
        post = nsc.posteriors(z)
        return sorted(post, key=lambda a: -post[a])

    rows = []
    for z in Cz:
        d, n = delta_rank(z), nsc_rank(z)
        rows.append({"delta": d[:2], "nsc": n[:2]})
    return {"cv_error_by_shrinkage": cv, "shrinkage": best, "chapters": rows}


# published first-or-second counts over 239 chapters, NSC, seven-author case (docs/prior-studies.md)
JOCKERS_PUBLISHED = {
    "rigdon": 197,
    "spalding": 110,
    "isaiah_malachi": 101,
    "cowdery": 37,
    "pratt": 24,
}


def jockers() -> int:
    from collections import Counter

    from metadata.config import derive_seed, stamp
    from metadata.config import load as load_config

    cfg = load_config()
    chapters = [json.loads(ln) for ln in CHAPTERS.read_text().splitlines()]
    texts = [c["text"].split() for c in chapters]
    known = jockers_known()
    features = jockers_features(known, texts)
    out = jockers_methods(
        known,
        texts,
        features,
        cfg["classic"]["ensc"]["shrinkage_grid"],
        derive_seed("replicate-jockers", cfg),
    )
    summary = {}
    for m in ("delta", "nsc"):
        first = Counter(r[m][0] for r in out["chapters"])
        top2 = Counter(a for r in out["chapters"] for a in r[m])
        summary[m] = {"first": dict(first), "first_or_second": dict(top2)}
    result = {
        **stamp(),
        "features": features,
        "samples": {a: len(v) for a, v in known.items()},
        "published_first_or_second_nsc": JOCKERS_PUBLISHED,
        "summary": summary,
        "cv_error_by_shrinkage": out["cv_error_by_shrinkage"],
        "shrinkage": out["shrinkage"],
        "chapters": [
            {"book": c["book"], "chapter": c["chapter"], **r}
            for c, r in zip(chapters, out["chapters"], strict=True)
        ],
    }
    JOCKERS_OUT.write_text(json.dumps(result, indent=1) + "\n")
    for m, v in summary.items():
        print(m, "first:", dict(sorted(v["first"].items(), key=lambda kv: -kv[1])))
        print(
            m, "first or second:", dict(sorted(v["first_or_second"].items(), key=lambda kv: -kv[1]))
        )
    print("published (NSC, first or second):", JOCKERS_PUBLISHED)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["chapters"]:
        return chapters()
    if args[:1] == ["jockers"]:
        return jockers()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
