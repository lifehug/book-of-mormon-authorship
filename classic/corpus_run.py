"""The classical methods on the frozen corpus: a demonstration on known authors (BOM-20).

BOM-20 is done when every method runs on corpus v1.0. This shows they do, at scale, and how well
they tell apart real 1780-1830 authors. It is **not** the validation benchmark (BOM-21, which
sets thresholds and decides pass or fail) and feeds no decision. The Book of Mormon is sealed and
not touched.

Design, with every number from ``classic`` in the config:

* *Authors.* Personal authors (``surname, forenames``; institutions and periodicals left out),
  not a registered candidate, with at least ``corpus_run.min_works`` distinct works of 15,000+
  words in 1780-1830 that pass BOM-14's OCR cutoff and are duplicate keepers. One work per
  distinct title (first five words of the normalised title), so a reprint of a training work is
  never the held-out one. ``corpus_run.authors`` are drawn with the root seed.
* *Samples.* One ``corpus_run.sample_words`` chunk from the middle of each work's normalised text.
* *Test.* Each author's held-out work (seeded) is attributed among all the sampled authors from
  the rest of their works.
* *Methods.* Burrows' and Cosine Delta on the most frequent words (each of ``classic.mfw``,
  culled at ``mfw_min_doc_fraction``) and on character 3- and 4-grams; General Imposters with the
  registered trials and fractions, scored for the true author and for one wrong author per test;
  ENSC at every shrinkage value in the registered grid, since choosing one is BOM-21's job.

Output: ``data/classic/corpus_run.json``.

Usage::

    python -m classic.corpus_run
"""

from __future__ import annotations

import json
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from classic import (
    ENSC,
    build_vocabulary,
    frequency_matrix,
    general_imposters,
    nearest_authors,
    tokenize,
    word_counts,
)
from classic.ensc import NONE
from classic.features import char_ngram_counts
from metadata.config import classic_kwargs, stamp
from metadata.config import load as load_config
from metadata.dates import effective_year

OUT = Path("data/classic/corpus_run.json")
CATALOG = Path("data/catalog/catalog.parquet")
VOLUMES = Path("data/ocr_quality/volumes.parquet")
DUPES = Path("data/catalog/duplicates_combined.parquet")
SIGS = Path("data/catalog/signatures_normalized")
MIN_WORK_WORDS = 15000  # a work must hold several samples' worth of text
_INSTITUTION = re.compile(
    r"\b(society|states|britain|gazette|board|committee|church|congress|company|association|"
    r"university|college|parliament|court|commissioners|missions|council|assembly|legislature|"
    r"convention|department|office|bank|library|academy|institution|union|county|city|town|"
    r"commonwealth|kingdom|england|ireland|scotland|france|massachusetts|york|virginia)\b"
)


def eligible(cfg: dict) -> dict[str, list[dict]]:
    from metadata.controls import _is_candidate

    lo, hi = cfg["corpus"]["date_range"]
    excluded = {r["work_id"] for r in pq.read_table(VOLUMES).to_pylist() if r["ocr_excluded"]}
    nonkeeper = {r["work_id"] for r in pq.read_table(DUPES).to_pylist() if not r["is_keeper"]}
    words = {}
    for f in SIGS.glob("*.parquet"):
        for r in pq.read_table(f, columns=["work_id", "words"]).to_pylist():
            words[r["work_id"]] = r["words"]
    cols = ["work_id", "source", "author_norm", "year", "has_text", "title_norm", "text_path"]
    by: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in pq.read_table(CATALOG, columns=cols).to_pylist():
        a = r["author_norm"] or ""
        r["year"] = effective_year(r["work_id"], r["year"])  # BOM-56: placeholder dates
        if not (r["has_text"] and r["year"] and lo <= r["year"] <= hi):
            continue
        if r["source"] == "chronicling_america" or "," not in a or _INSTITUTION.search(a):
            continue
        if _is_candidate(a) or r["work_id"] in excluded or r["work_id"] in nonkeeper:
            continue
        if (words.get(r["work_id"]) or 0) < MIN_WORK_WORDS:
            continue
        title = " ".join((r["title_norm"] or "").split()[:5])
        by[a].setdefault(title, r)  # one work per distinct title
    n = cfg["classic"]["corpus_run"]["min_works"]
    return {a: sorted(t.values(), key=lambda r: r["work_id"]) for a, t in by.items() if len(t) >= n}


def sample(row: dict, n_words: int) -> list[str]:
    from ocr_fix.normalize import norm_path

    tokens = tokenize(norm_path(row).read_text(encoding="utf-8", errors="replace"))
    mid = max(0, len(tokens) // 2 - n_words // 2)
    return tokens[mid : mid + n_words]


def _delta_accuracy(train, test, labels, test_labels, vocab_counts_train, vocab_counts_test,
                    top_n, min_frac, method):  # fmt: skip
    vocab = build_vocabulary(vocab_counts_train, top_n=top_n, min_doc_fraction=min_frac)
    Xtr = frequency_matrix(vocab_counts_train, vocab)
    Xte = frequency_matrix(vocab_counts_test, vocab)
    profiles = {a: Xtr[[i for i, y in enumerate(labels) if y == a]].mean(axis=0)
                for a in sorted(set(labels))}  # fmt: skip
    correct = [nearest_authors(x, profiles, method=method, reference=Xtr)[0][0] == y
               for x, y in zip(Xte, test_labels, strict=True)]  # fmt: skip
    return sum(correct) / len(test_labels), len(vocab), Xtr, Xte, profiles, correct


def run(out: Path = OUT) -> int:
    start = time.time()
    cfg = load_config()
    cc = cfg["classic"]
    kw = classic_kwargs(cfg)
    cr = cc["corpus_run"]
    pool = eligible(cfg)
    rng = random.Random(f"{cfg['seed']}:classic-corpus-run")
    authors = sorted(rng.sample(sorted(pool), min(cr["authors"], len(pool))))
    train_tok, train_lab, test_tok, test_lab, held = [], [], [], [], {}
    for a in authors:
        works = pool[a]
        pick = rng.randrange(len(works))
        held[a] = works[pick]["work_id"]
        for i, w in enumerate(works):
            toks = sample(w, cr["sample_words"])
            (test_tok if i == pick else train_tok).append(toks)
            (test_lab if i == pick else train_lab).append(a)
    print(f"{len(pool):,} eligible authors; {len(authors)} drawn; "
          f"{len(train_tok)} training and {len(test_tok)} test samples", flush=True)  # fmt: skip

    wtr = [word_counts(t) for t in train_tok]
    wte = [word_counts(t) for t in test_tok]
    results: dict = {"delta": {}, "char_ngram_delta": {}, "imposters": {}, "ensc": {}}
    per_test: dict = {a: {} for a in test_lab}
    mid_mfw, top_mfw = sorted(cc["mfw"])[len(cc["mfw"]) // 2], max(cc["mfw"])
    for top_n in cc["mfw"]:
        for method in ("burrows", "cosine"):
            acc, nv, Xtr, Xte, prof, ok = _delta_accuracy(
                wtr, wte, train_lab, test_lab, wtr, wte, top_n, cc["mfw_min_doc_fraction"], method
            )
            results["delta"][f"mfw{top_n}_{method}"] = {"accuracy": acc, "features": nv}
            for a, hit in zip(test_lab, ok, strict=True):
                per_test[a][f"delta_mfw{top_n}_{method}"] = hit
    for n in cc["char_ngrams"]:
        ctr = [char_ngram_counts(t, n) for t in train_tok]
        cte = [char_ngram_counts(t, n) for t in test_tok]
        acc, nv, *_, ok = _delta_accuracy(ctr, cte, train_lab, test_lab, ctr, cte, top_mfw,
                                          cc["mfw_min_doc_fraction"], "cosine")  # fmt: skip
        results["char_ngram_delta"][f"char{n}_top{top_mfw}_cosine"] = {"accuracy": acc,
                                                                      "features": nv}  # fmt: skip
        for a, hit in zip(test_lab, ok, strict=True):
            per_test[a][f"delta_char{n}_cosine"] = hit

    # General Imposters at the middle registered MFW size: the true author against the other
    # authors' profiles, and one seeded wrong author, for every held-out work
    _, _, Xtr, Xte, prof, _ = _delta_accuracy(wtr, wte, train_lab, test_lab, wtr, wte, mid_mfw,
                                              cc["mfw_min_doc_fraction"], "cosine")  # fmt: skip
    gi = cc["imposters"]
    true_s, false_s = [], []
    for x, y in zip(Xte, test_lab, strict=True):
        for cand, bucket in ((y, true_s), (rng.choice([a for a in authors if a != y]), false_s)):
            imps = np.vstack([prof[a] for a in authors if a != cand])
            bucket.append(general_imposters(
                x, prof[cand], imps, feature_fraction=gi["feature_fraction"],
                n_imposters=max(1, int(round(gi["imposter_fraction"] * len(imps)))),
                trials=gi["trials"], distance="cosine", seed=rng.randrange(2**31)))  # fmt: skip
    auc = np.mean([[t > f for f in false_s] for t in true_s]) + 0.5 * np.mean(
        [[t == f for f in false_s] for t in true_s]
    )
    for a, t, f in zip(test_lab, true_s, false_s, strict=True):
        per_test[a]["imposters_true_beats_wrong"] = t > f
    results["imposters"] = {"features": f"mfw{mid_mfw}", "mean_true": float(np.mean(true_s)),
                            "mean_wrong": float(np.mean(false_s)), "auc": float(auc),
                            "true_scores": true_s, "wrong_scores": false_s}  # fmt: skip

    for s in cc["ensc"]["shrinkage_grid"]:
        model = ENSC(shrinkage=s, **kw["ensc"]).fit(Xtr, train_lab)
        preds = [model.classify(x) for x in Xte]
        hits = sum(p.label == y for p, y in zip(preds, test_lab, strict=True))
        none = sum(p.label == NONE for p in preds)
        for a, p in zip(test_lab, preds, strict=True):
            per_test[a][f"ensc_{s}"] = p.label == a
        results["ensc"][str(s)] = {"accuracy": hits / len(test_lab), "said_none": none}

    out.parent.mkdir(parents=True, exist_ok=True)
    summary = {**stamp(), "eligible_authors": len(pool),
               "authors": authors, "held_out": held, "train_samples": len(train_tok),
               "chance": 1 / len(authors), "seconds": round(time.time() - start),
               "results": results, "per_test": per_test}  # fmt: skip
    out.write_text(json.dumps(summary, indent=1) + "\n")
    for k, v in results["delta"].items():
        print(f"  Delta {k:<22} {v['accuracy']:.0%}  ({v['features']} features)")
    for k, v in results["char_ngram_delta"].items():
        print(f"  Delta {k:<22} {v['accuracy']:.0%}")
    im = results["imposters"]
    print(f"  Imposters  true {im['mean_true']:.2f}  wrong {im['mean_wrong']:.2f}", end="")
    print(f"  AUC {im['auc']:.2f}")
    for k, v in results["ensc"].items():
        print(f"  ENSC shrinkage {k:<4} {v['accuracy']:.0%}  said none {v['said_none']}")
    print(f"chance {summary['chance']:.0%}; {summary['seconds']}s -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
