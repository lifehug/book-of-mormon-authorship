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
    python -m eval.replicate jockers-data # their published counts -> replication_jockers_data.json
    python -m eval.replicate johnson      # after `reuse.rare scan --target bom`
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
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


# samples left out because they quote the Book of Mormon (4.2's 12-token check), per author
CONTAMINATED: dict[str, int] = {}


def _clean(author: str, samples: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    """Drop candidate samples that quote the Book of Mormon: matching it to them is circular
    (4.2). Pratt and Cowdery quoted it after 1830; the count dropped goes in ``CONTAMINATED``."""
    from metadata.sealed import contaminated

    keep = [(n, t) for n, t in samples if not contaminated(" ".join(t))]
    CONTAMINATED[author] = len(samples) - len(keep)
    return keep


def jockers_known() -> dict[str, list[tuple[str, list[str]]]]:
    """The seven-author design: four candidates, Isaiah-Malachi, and the two controls. Candidate
    samples that quote the Book of Mormon are left out (``_clean``)."""
    from eval.benchmark import _masked_tokens

    cand = _candidate_tokens()
    known = {
        a: _clean(a, [(f"{a} {i}", c) for i, c in enumerate(_chunks(cand[name], SAMPLE_WORDS))])
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

    from classic import frequency_matrix, word_counts

    authors = sorted(known)
    docs = [t for a in authors for _, t in known[a]]
    labels = [a for a in authors for _ in known[a]]
    X = frequency_matrix([word_counts(t) for t in docs], features)
    C = frequency_matrix([word_counts(t) for t in chapters], features)
    return jockers_rank(X, labels, C, shrinkage_grid, seed)


def jockers_rank(
    X: np.ndarray,
    labels: list[str],
    C: np.ndarray,
    shrinkage_grid: list[float],
    seed: int,
    delta_words: int | None = None,
    delta_scale_known: bool = False,
) -> dict:
    """The matrix core of ``jockers_methods``: relative frequencies of the selected words for the
    known samples (``X``, author ``labels``) and the chapters (``C``).

    Delta's options, both off by default (BOM-22's first run): ``delta_words`` keeps only that
    many of the most frequent selected words (Jockers et al. report 90, chosen by
    cross-validation); ``delta_scale_known`` takes each word's mean and sd from the known samples
    only, as Burrows (2002) does, instead of from known samples and chapters together."""
    import random

    from classic import ENSC

    authors = sorted(set(labels))
    allm = np.vstack([X, C])
    mu, sd = allm.mean(axis=0), allm.std(axis=0)
    sd[sd == 0] = 1
    Xz, Cz = (X - mu) / sd, (C - mu) / sd
    dcols = np.arange(X.shape[1])
    if delta_words:
        dcols = np.argsort(-np.vstack([X, C]).mean(axis=0))[:delta_words]
    dbase = X if delta_scale_known else allm
    dmu, dsd = dbase[:, dcols].mean(axis=0), dbase[:, dcols].std(axis=0)
    dsd[dsd == 0] = 1
    dprof = {
        a: ((X[[i for i, y in enumerate(labels) if y == a]][:, dcols] - dmu) / dsd).mean(axis=0)
        for a in authors
    }

    def delta_rank(row):
        zz = (row[dcols] - dmu) / dsd
        d = {a: float(np.mean(np.abs(zz - dprof[a]))) for a in authors}
        return sorted(authors, key=lambda a: d[a])

    # shrinkage by 5-fold cross-validation on the known samples
    rng = random.Random(seed)
    idx = list(range(len(labels)))
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
        cv[s_] = err / len(labels)
    best = min(shrinkage_grid, key=lambda s_: (cv[s_], s_))
    nsc = ENSC(shrinkage=best, alpha=0.0, priors="proportional").fit(Xz, labels)

    def nsc_rank(z):
        post = nsc.posteriors(z)
        return sorted(post, key=lambda a: -post[a])

    rows = []
    for z, row in zip(Cz, C, strict=True):
        d, n = delta_rank(row), nsc_rank(z)
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


# Jockers et al. 2008, Tables 1 (NSC) and 2 (delta): chapters per author as 1st and 2nd choice
JOCKERS_TABLES = {
    "nsc": {
        "first": {"cowdery": 20, "pratt": 9, "rigdon": 93, "spalding": 52, "isaiah_malachi": 63,
                  "barlow": 0, "longfellow": 2},
        "second": {"cowdery": 17, "pratt": 15, "rigdon": 104, "spalding": 58,
                   "isaiah_malachi": 38, "barlow": 1, "longfellow": 6},
    },
    "delta": {
        "first": {"cowdery": 5, "pratt": 7, "rigdon": 63, "spalding": 47, "isaiah_malachi": 112,
                  "barlow": 0, "longfellow": 5},
        "second": {"cowdery": 19, "pratt": 22, "rigdon": 92, "spalding": 23,
                   "isaiah_malachi": 54, "barlow": 9, "longfellow": 20},
    },
}  # fmt: skip
JOCKERS_DATA = DIR / "jockers2008" / "dataMatrix.txt.gz"
JOCKERS_DELTA_WORDS = 90  # "the lowest delta error rate of 11.1% was obtained using ninety words"
JOCKERS_DATA_OUT = DIR.parent / "replication_jockers_data.json"
# their sample-name prefixes -> our author keys (Isaiah and Malachi are one author, as published)
JOCKERS_PREFIX = {
    "Barlow": "barlow", "Cowdrey": "cowdery", "Isaiah": "isaiah_malachi",
    "Malachi": "isaiah_malachi", "Longfellow": "longfellow", "Pratt": "pratt",
    "Rigdon": "rigdon", "Spaulding": "spalding", "Unknown": None,
}  # fmt: skip


def jockers_matrix() -> tuple[list[str], list[str], np.ndarray]:
    """Their published counts (Stanford Digital Repository, druid rs276tc2764, CC BY 3.0):
    sample names, the 19,992-word vocabulary, and a samples x words count matrix."""
    import gzip

    with gzip.open(JOCKERS_DATA, "rt", encoding="utf-8") as fh:
        vocab = [w.strip('"') for w in fh.readline().rstrip("\n").split("\t")]
        names, rows = [], []
        for ln in fh:
            parts = ln.rstrip("\n").split("\t")
            names.append(parts[0].strip('"'))
            rows.append(np.array(parts[1:], dtype=float))
    return names, vocab, np.vstack(rows)


def jockers_data() -> int:
    """Our Delta and NSC on *their* data: does our implementation reproduce Tables 1 and 2?"""
    from collections import Counter

    from metadata.config import derive_seed, stamp
    from metadata.config import load as load_config

    cfg = load_config()
    names, vocab, M = jockers_matrix()
    rel = M / M.sum(axis=1, keepdims=True)  # share of each text's words
    who = [JOCKERS_PREFIX[re.match(r"[A-Za-z]+", n).group(0)] for n in names]
    known = [i for i, w in enumerate(who) if w]
    chap = [i for i, w in enumerate(who) if w is None]
    # the published selection rule, on their data: in every author's samples and the chapters,
    # mean relative frequency at least 0.1%, minus god, ye, thy, behold
    present = [
        set(np.flatnonzero(M[[i for i in known if who[i] == a]].sum(axis=0)))
        for a in sorted(set(who[i] for i in known))
    ] + [set(np.flatnonzero(M[chap].sum(axis=0)))]
    shared = set.intersection(*present)
    feats = sorted(j for j in shared if rel[:, j].mean() >= MIN_MEAN_FREQ
                   and vocab[j] not in DROPPED)  # fmt: skip
    out = jockers_rank(
        rel[known][:, feats],
        [who[i] for i in known],
        rel[chap][:, feats],
        cfg["classic"]["ensc"]["shrinkage_grid"],
        derive_seed("replicate-jockers-data", cfg),
        delta_words=JOCKERS_DELTA_WORDS,
        delta_scale_known=True,  # Burrows (2002): z-scores from the known texts
    )
    summary = {
        m: {
            "first": dict(Counter(r[m][0] for r in out["chapters"])),
            "second": dict(Counter(r[m][1] for r in out["chapters"])),
        }
        for m in ("delta", "nsc")
    }
    # which candidate's texts move the answer: replace one author's samples with ours
    ours = jockers_known()
    swaps = {}
    for a in ("rigdon", "pratt", "cowdery", "spalding"):
        keep = [i for i in known if who[i] != a]
        mine = np.vstack([
            np.array([sum(1 for w in t if w == vocab[j]) for j in feats]) / len(t)
            for _, t in ours[a]
        ])  # fmt: skip
        sw = jockers_rank(
            np.vstack([rel[keep][:, feats], mine]),
            [who[i] for i in keep] + [a] * len(mine),
            rel[chap][:, feats],
            cfg["classic"]["ensc"]["shrinkage_grid"],
            derive_seed("replicate-jockers-data", cfg),
            delta_words=JOCKERS_DELTA_WORDS,
            delta_scale_known=True,
        )
        swaps[a] = dict(Counter(x for r in sw["chapters"] for x in r["nsc"]))
    result = {
        **stamp(),
        "source": "Jockers, Witten and Criddle 2008 supplementary data, "
        "https://purl.stanford.edu/rs276tc2764 (CC BY 3.0)",
        "features": [vocab[j] for j in feats],
        "samples": dict(Counter(who[i] for i in known)),
        "published": JOCKERS_TABLES,
        "ours": summary,
        "cv_error_by_shrinkage": out["cv_error_by_shrinkage"],
        "shrinkage": out["shrinkage"],
        "nsc_first_or_second_with_our_texts_for": swaps,
        "contaminated_samples_dropped": dict(CONTAMINATED),
    }
    JOCKERS_DATA_OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"{len(feats)} words; samples {result['samples']}")
    for m in ("nsc", "delta"):
        for rank in ("first", "second"):
            pub, got = JOCKERS_TABLES[m][rank], summary[m][rank]
            print(f"{m:5s} {rank:6s} " + "  ".join(f"{a} {got.get(a, 0)}/{pub[a]}" for a in pub))
    base = Counter(x for r in out["chapters"] for x in r["nsc"])
    print("NSC first-or-second, their data:", dict(base.most_common()))
    for a, c in swaps.items():
        print(f"  with our {a} texts:", dict(Counter(c).most_common()))
    return 0


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
        "contaminated_samples_dropped": dict(CONTAMINATED),
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


# ------------------------------------------------------------- Chris and Duane Johnson (2013)

JOHNSON_OUT = DIR.parent / "replication_johnson.json"
JOHNSON_RATE = 1000  # rare: in fewer than one book per thousand (their rule)
NAMED_SOURCES = {
    "the_late_war": r"late war.{0,80}(1812|britain)",
    "first_book_of_napoleon": r"first book of napoleon",
}


def johnson() -> int:
    """Rank every period book by its density of rare 4-grams shared with the Book of Mormon."""
    from collections import Counter

    import numpy as np
    import pyarrow.parquet as pq

    from metadata.config import load as load_config
    from metadata.config import stamp
    from metadata.dates import effective_year

    cfg = load_config()
    lo, hi = cfg["corpus"]["date_range"]
    recs = [r for r in pq.read_table("data/reuse/bom/hits.parquet").to_pylist() if r["words"] > 0]
    cat = {
        r["work_id"]: r
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "title", "author_norm", "year"]
        ).to_pylist()
    }
    df: Counter = Counter()
    for r in recs:
        df.update(r["hits"])
    n = len(recs)
    rules = {
        "johnson_lt_1_per_1000": n / JOHNSON_RATE,
        "preregistered_df_le": cfg["borrowing"]["max_df"],
    }
    per = cfg["borrowing"]["per_words"]
    out = {}
    for name, cut in rules.items():
        rare = {g for g, c in df.items() if (c < cut if name.startswith("johnson") else c <= cut)}
        dens = {r["work_id"]: per * sum(g in rare for g in r["hits"]) / r["words"] for r in recs}
        shared = {r["work_id"]: sum(g in rare for g in r["hits"]) for r in recs}
        order = sorted(dens, key=lambda w: -dens[w])
        rank = {w: i + 1 for i, w in enumerate(order)}
        null = np.array(
            [dens[w] for w in dens if (y := effective_year(w, cat[w]["year"])) and lo <= y <= hi]
        )

        def p_of(w, null=null, dens=dens):
            return float(((null >= dens[w]).sum() + 1) / (len(null) + 1))

        named = {}
        for key, pat in NAMED_SOURCES.items():
            hits = [w for w in dens if re.search(pat, cat[w]["title"] or "", re.I)]
            best = min(hits, key=lambda w: rank[w]) if hits else None
            named[key] = (
                None
                if best is None
                else {
                    "work_id": best,
                    "rank": rank[best],
                    "density": dens[best],
                    "shared": shared[best],
                    "p_value": p_of(best),
                    "copies_found": len(hits),
                }
            )
        out[name] = {
            "rare_cut": cut,
            "rare_grams": len(rare),
            "named": named,
            "top": [
                {
                    "rank": rank[w],
                    "work_id": w,
                    "title": (cat[w]["title"] or "")[:90],
                    "author": cat[w]["author_norm"],
                    "year": cat[w]["year"],
                    "density": round(dens[w], 3),
                    "shared": shared[w],
                    "p_value": p_of(w),
                }
                for w in order[:25]
            ],
        }
    JOHNSON_OUT.write_text(json.dumps({**stamp(), "volumes": n, **out}, indent=1) + "\n")
    for name, v in out.items():
        print(name, f"(rare grams {v['rare_grams']:,})")
        for k, x in v["named"].items():
            print(
                f"  {k}: rank {x['rank']:,} of {n:,}, {x['shared']} shared, p = {x['p_value']:.2g}"
                if x
                else f"  {k}: not found"
            )
        for t in v["top"][:8]:
            line = f"{t['rank']:>3} {t['density']:>7.2f} {t['shared']:>4} {t['year']}"
            print(f"    {line} {t['title'][:60]}")
    return 0


# --------------------------------------------------------------- Larsen, Rencher and Layton

LARSEN_OUT = DIR.parent / "replication_larsen.json"
LARSEN_10 = ["and", "the", "of", "that", "to", "unto", "in", "it", "for", "be"]
LARSEN_BLOCK = 1000


def narrator_blocks(min_blocks: int = 2) -> dict[str, list[list[str]]]:
    """1,000-word blocks of KJV-masked original text per narrator (BOM-17 labels)."""
    from segment.build import original_words

    spans = {}
    for ln in Path("data/kjv_mask/bom/spans.jsonl").read_text().splitlines():
        r = json.loads(ln)
        spans[r["id"]] = r["spans"]
    text = {
        json.loads(ln)["seq"]: json.loads(ln)["text"] for ln in EDITION.read_text().splitlines()
    }
    by: dict[str, list[str]] = {}
    for ln in Path("data/bom/segments/paragraph_labels.jsonl").read_text().splitlines():
        r = json.loads(ln)
        words = tokenize(" ".join(original_words(text[r["seq"]], spans.get(f"bom:{r['seq']}", []))))
        by.setdefault(r["narrator"], []).extend(words)
    out = {
        a: [w[i : i + LARSEN_BLOCK] for i in range(0, len(w) - LARSEN_BLOCK + 1, LARSEN_BLOCK)]
        for a, w in by.items()
    }
    return {a: b for a, b in out.items() if len(b) >= min_blocks}


def _arcsine(blocks: list[list[str]], words: list[str]):
    import numpy as np

    from classic import frequency_matrix, word_counts

    return np.arcsin(np.sqrt(frequency_matrix([word_counts(b) for b in blocks], words)))


def manova(groups: dict[str, np.ndarray]) -> dict:
    """One-way MANOVA: Wilks' lambda and Rao's F approximation."""
    import numpy as np
    from scipy import stats

    X = np.vstack(list(groups.values()))
    n, p = X.shape
    g = len(groups)
    grand = X.mean(axis=0)
    W = sum(((v - v.mean(axis=0)).T @ (v - v.mean(axis=0))) for v in groups.values())
    B = sum(
        len(v) * np.outer(v.mean(axis=0) - grand, v.mean(axis=0) - grand) for v in groups.values()
    )
    lam = float(np.linalg.det(W) / np.linalg.det(W + B))
    q = g - 1
    t = np.sqrt((p * p * q * q - 4) / (p * p + q * q - 5)) if p * p + q * q > 5 else 1.0
    w = n - 1 - (p + q + 1) / 2
    df1 = p * q
    df2 = w * t - (p * q - 2) / 2
    f = (1 - lam ** (1 / t)) / (lam ** (1 / t)) * df2 / df1
    return {
        "wilks_lambda": lam,
        "F": float(f),
        "df1": df1,
        "df2": float(df2),
        "p_value": float(stats.f.sf(f, df1, df2)),
        "groups": g,
        "blocks": n,
    }


def lda_loo(groups: dict[str, np.ndarray]) -> dict[str, dict[str, int]]:
    """Leave-one-out linear discriminant classification (pooled covariance, equal priors):
    for each group, how its blocks are classified."""
    import numpy as np

    names = sorted(groups)
    X = np.vstack([groups[a] for a in names])
    y = [a for a in names for _ in range(len(groups[a]))]
    out = {a: {} for a in names}
    for i in range(len(X)):
        keep = [j for j in range(len(X)) if j != i]
        Xk = X[keep]
        yk = [y[j] for j in keep]
        means = {a: Xk[[j for j, b in enumerate(yk) if b == a]].mean(axis=0) for a in names}
        S = sum(
            np.cov(Xk[[j for j, b in enumerate(yk) if b == a]].T) * (sum(b == a for b in yk) - 1)
            for a in names
            if sum(b == a for b in yk) > 1
        )
        Si = np.linalg.pinv(S / (len(Xk) - len(names)))
        d = {a: float((X[i] - means[a]) @ Si @ (X[i] - means[a])) for a in names}
        pred = min(d, key=d.get)
        out[y[i]][pred] = out[y[i]].get(pred, 0) + 1
    return out


def larsen() -> int:
    from metadata.config import stamp

    bom = narrator_blocks()
    cand = _candidate_tokens()
    cands = {
        k: [w[i : i + LARSEN_BLOCK] for i in range(0, len(w) - LARSEN_BLOCK + 1, LARSEN_BLOCK)]
        for k, w in cand.items()
    }
    lectures = dc1835_parts().get("lectures", [])
    if lectures:  # Larsen et al. compared the Lectures on Faith too
        cand["Lectures on Faith"] = lectures
        cands["Lectures on Faith"] = [
            lectures[i : i + LARSEN_BLOCK]
            for i in range(0, len(lectures) - LARSEN_BLOCK + 1, LARSEN_BLOCK)
        ]
    cands = {k: v for k, v in cands.items() if len(v) >= 2}
    within = manova({a: _arcsine(b, LARSEN_10) for a, b in bom.items()})
    allg = {
        **{f"BoM {a}": _arcsine(b, LARSEN_10) for a, b in bom.items()},
        **{a: _arcsine(b, LARSEN_10) for a, b in cands.items()},
    }
    classified = lda_loo(allg)
    bom_to_cand = sum(
        n
        for g, d in classified.items()
        if g.startswith("BoM")
        for pred, n in d.items()
        if not pred.startswith("BoM")
    )
    bom_total = sum(sum(d.values()) for g, d in classified.items() if g.startswith("BoM"))
    result = {
        **stamp(),
        "words": LARSEN_10,
        "blocks": {a: len(b) for a, b in bom.items()},
        "candidate_blocks": {a: len(b) for a, b in cands.items()},
        "manova_book_of_mormon_narrators": within,
        "lda_leave_one_out": classified,
        "bom_blocks_classified_to_a_candidate": bom_to_cand,
        "bom_blocks": bom_total,
    }
    LARSEN_OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(
        f"MANOVA over {within['groups']} narrators, {within['blocks']} blocks: "
        f"Wilks {within['wilks_lambda']:.3f}, p = {within['p_value']:.2g}"
    )
    print(f"BoM blocks classified to a 19th-century candidate: {bom_to_cand} of {bom_total}")
    return 0


# ----------------------------------------------------------------------------- Holmes (1992)

HOLMES_OUT = DIR.parent / "replication_holmes.json"
HOLMES_SAMPLE = 10000


def richness(tokens: list[str]) -> dict[str, float]:
    """Holmes's variables that can be computed exactly: Honore's R, V2/V and Yule's K. (The two
    Sichel parameters need a model fit Holmes describes only by reference; they are left out.)"""
    import math
    from collections import Counter

    n = len(tokens)
    freq = Counter(tokens)
    v = len(freq)
    spectrum = Counter(freq.values())
    v1, v2 = spectrum.get(1, 0), spectrum.get(2, 0)
    r = 100 * math.log(n) / (1 - v1 / v) if v1 < v else float("inf")
    k = 1e4 * (sum(i * i * vi for i, vi in spectrum.items()) - n) / (n * n)
    return {"honore_r": r, "v2_over_v": v2 / v, "yule_k": k}


def holmes_samples() -> dict[str, list[str]]:
    """About 10,000-word samples: each narrator's masked text in order, plus controls."""
    samples: dict[str, list[str]] = {}
    for a, blocks in narrator_blocks(min_blocks=HOLMES_SAMPLE // LARSEN_BLOCK).items():
        words = [w for b in blocks for w in b]
        for i in range(0, len(words) - HOLMES_SAMPLE + 1, HOLMES_SAMPLE):
            samples[f"BoM {a} {i // HOLMES_SAMPLE + 1}"] = words[i : i + HOLMES_SAMPLE]
    cand = _candidate_tokens()
    js = cand.get("Joseph Smith", [])
    for i in range(0, len(js) - HOLMES_SAMPLE + 1, HOLMES_SAMPLE):
        samples[f"Joseph Smith {i // HOLMES_SAMPLE + 1}"] = js[i : i + HOLMES_SAMPLE]
    isa = [w for _, t in _kjv({"ISA"}) for w in t]
    for i in range(0, len(isa) - HOLMES_SAMPLE + 1, HOLMES_SAMPLE):
        samples[f"Isaiah {i // HOLMES_SAMPLE + 1}"] = isa[i : i + HOLMES_SAMPLE]
    revelations = dc1835_parts().get("revelations", [])
    for i in range(0, min(len(revelations), 3 * HOLMES_SAMPLE) - HOLMES_SAMPLE + 1, HOLMES_SAMPLE):
        samples[f"D&C 1835 {i // HOLMES_SAMPLE + 1}"] = revelations[i : i + HOLMES_SAMPLE]
    return samples


DC1835 = Path("data/private/replication/jsp_dc1835.jsonl")


def dc1835_parts() -> dict[str, list[str]]:
    """The 1835 Doctrine and Covenants split by its own table of contents: the Lectures on Faith
    (Lectures 1-7) and the revelations (Sections 1-100; Sections 101-102 are a statement and a
    declaration, not revelations, and are left out with the minutes and index)."""
    if not DC1835.exists():
        return {}
    parts: dict[str, list[str]] = {"lectures": [], "revelations": []}
    current = None
    for ln in DC1835.read_text().splitlines():
        r = json.loads(ln)
        title = (r.get("toc") or {}).get("pageTitle")
        if title:
            m = re.match(r"Section (\d+)", title)
            current = (
                "lectures"
                if title.startswith("Lecture")
                else "revelations"
                if m and int(m.group(1)) <= 100
                else None
            )
        if current:
            parts[current] += tokenize(r.get("text") or "")
    return parts


def holmes() -> int:
    from scipy.cluster.hierarchy import fcluster, linkage

    from metadata.config import stamp

    samples = holmes_samples()
    names = sorted(samples)
    vals = {nm: richness(samples[nm]) for nm in names}
    keys = ["honore_r", "v2_over_v", "yule_k"]
    X = np.array([[vals[nm][k] for k in keys] for nm in names])
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    link = linkage(Z, method="average", metric="euclidean")
    groups = fcluster(link, t=3, criterion="maxclust")
    u, sv, vt = np.linalg.svd(Z, full_matrices=False)
    pcs = Z @ vt.T[:, :2]
    result = {
        **stamp(),
        "variables": keys,
        "omitted": "Sichel alpha and theta (fit not specified)",
        "samples": {
            nm: {**vals[nm], "cluster_of_3": int(g), "pc1": float(pc[0]), "pc2": float(pc[1])}
            for nm, g, pc in zip(names, groups, pcs, strict=True)
        },
        "pc_variance": (sv**2 / (sv**2).sum()).tolist(),
    }
    HOLMES_OUT.write_text(json.dumps(result, indent=1) + "\n")
    for nm, g in zip(names, groups, strict=True):
        print(f"  cluster {g}  {nm:<22} " + "  ".join(f"{k} {vals[nm][k]:.3f}" for k in keys))
    return 0


# ----------------------------------------------------- Schaalje, Fields, Roper and Snow (2011)

ENSC_OUT = DIR.parent / "replication_ensc.json"


def ensc_open_set() -> int:
    """Jockers' design with Joseph Smith added and ENSC's "none of the above" switched on at the
    alpha BOM-21 calibrated (``data/benchmark/thresholds.json``)."""
    from collections import Counter

    from classic import ENSC, frequency_matrix, word_counts
    from metadata.config import stamp

    th = json.loads(Path("data/benchmark/thresholds.json").read_text())["ensc"]
    if th.get("alpha") is None:
        raise SystemExit("BOM-21 has not calibrated ENSC's alpha yet")
    chapters = [json.loads(ln) for ln in CHAPTERS.read_text().splitlines()]
    texts = [c["text"].split() for c in chapters]
    known = jockers_known()
    js = _candidate_tokens().get("Joseph Smith", [])
    known["joseph_smith"] = _clean(
        "joseph_smith", [(f"js {i}", c) for i, c in enumerate(_chunks(js, SAMPLE_WORDS))]
    )
    features = jockers_features(known, texts)
    authors = sorted(known)
    docs = [t for a in authors for _, t in known[a]]
    labels = [a for a in authors for _ in known[a]]
    X = frequency_matrix([word_counts(t) for t in docs], features)
    C = frequency_matrix([word_counts(t) for t in texts], features)
    allm = np.vstack([X, C])
    mu, sd = allm.mean(axis=0), allm.std(axis=0)
    sd[sd == 0] = 1
    model = ENSC(shrinkage=th["shrinkage"], alpha=th["alpha"], priors="proportional")
    model.fit((X - mu) / sd, labels)
    preds = [model.classify(z).label for z in (C - mu) / sd]
    counts = Counter(preds)
    result = {
        **stamp(),
        "alpha": th["alpha"],
        "shrinkage": th["shrinkage"],
        "features": features,
        "samples": {a: len(v) for a, v in known.items()},
        "contaminated_samples_dropped": dict(CONTAMINATED),
        "assigned": dict(counts),
        "chapters": [
            {"book": c["book"], "chapter": c["chapter"], "assigned": pr}
            for c, pr in zip(chapters, preds, strict=True)
        ],
    }
    ENSC_OUT.write_text(json.dumps(result, indent=1) + "\n")
    print("ENSC open set, chapters assigned:", dict(counts.most_common()))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["chapters"]:
        return chapters()
    if args[:1] == ["jockers"]:
        return jockers()
    if args[:1] == ["jockers-data"]:
        return jockers_data()
    if args[:1] == ["johnson"]:
        return johnson()
    if args[:1] == ["larsen"]:
        return larsen()
    if args[:1] == ["holmes"]:
        return holmes()
    if args[:1] == ["ensc"]:
        return ensc_open_set()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
