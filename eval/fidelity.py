"""Fidelity checks: does our code reproduce the published results of the methods BOM-21 failed?
(BOM-57)

``ensc``: Funai (2010), section 3.3 and Appendix C, the published validation of extended NSC on
the Federalist Papers. Two studies, because the thesis's text and its code describe the
candidate set differently:

* **A, as the code runs it.** Training: 26 Hamilton papers, Madison's 14, Jay's 5; test: the
  other 25 Hamilton papers; should be Hamilton. Published misclassification: 16% (Table 3.2).
  R drew one split (``set.seed(698)``), which Python cannot reproduce, so we draw
  ``SPLITS`` seeded splits and report the range.
* **B, as the text describes it.** Training: the Book of Mormon candidates (our texts: Joseph
  Smith, Rigdon, Spalding, Cowdery, Pratt; Funai also split Rigdon into early and late, which
  we cannot); test: all 51 Hamilton papers; should be the latent author. Published: 15.69%
  (Table 3.1).

Both use Funai's 108 words as relative frequencies, the published code's settings
(``SHRINKAGE``, ``LAM``), and run beside our BOM-20 ENSC at its BOM-21 calibration for
comparison, and study B is repeated at several candidate sample lengths (Funai does not give his),
because the share sent to the latent author turns out to depend on them. Nothing here touches
the Book of Mormon or changes a registered result.

Usage::

    python -m eval.fidelity ensc      # -> data/benchmark/fidelity/ensc.json
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from classic import ENSC, frequency_matrix, tokenize, word_counts
from classic.ensc import NONE
from classic.ensc_published import LATENT, ENSCPublished
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

DIR = Path("data/benchmark/fidelity")
FEDERALIST = Path("data/benchmark/federalist/papers.jsonl")
# Funai (2010) Appendix C, first block ("extended NSC proposed by Schaalje et al."): thresh, lambda
SHRINKAGE = 1.0
LAM = 3.0
SPLITS = 100  # seeded 26/25 splits of Hamilton's papers, in place of R's single set.seed(698)
TRAIN_HAMILTON = 26
PUBLISHED = {"A": 0.16, "B": 0.1569}
# diagnostic, not a setting: study B at several candidate sample lengths (Funai does not give his)
SWEEP_WORDS = (1000, 2000, 3000, 5000, 10000)
# Funai (2010) Appendix C, the 108 non-contextual words
WORDS = (
    "a after again against all among an and are as at away be because been before but by came "
    "children come day did do down earth even every father for forth from go great had hand have "
    "he her him his i if in into is it king know land made man many may me men might more my no "
    "not now o of on one or our out over pass people power said say shall should so son that the "
    "their them then there therefore these they things this those thus time to up upon us was we "
    "were which who will with words would you your"
).split()


def _papers() -> dict[str, list[list[str]]]:
    by: dict[str, list[list[str]]] = {}
    for ln in FEDERALIST.read_text().splitlines():
        r = json.loads(ln)
        by.setdefault(r["author"], []).append(tokenize(r["text"]))
    return by


def _rel(texts: list[list[str]]) -> np.ndarray:
    return frequency_matrix([word_counts(t) for t in texts], WORDS)


def _ours() -> ENSC:
    th = json.loads(Path("data/benchmark/thresholds.json").read_text())["ensc"]
    return ENSC(shrinkage=th["shrinkage"], alpha=th["alpha"], priors="proportional")


def _run(train: dict[str, list[list[str]]], test: list[list[str]], truth: str) -> dict:
    labels = [a for a in train for _ in train[a]]
    X = _rel([t for a in train for t in train[a]])
    T = _rel(test)
    pub = ENSCPublished(shrinkage=SHRINKAGE, lam=LAM).fit(X, labels)
    p_pred = [pub.predict(x) for x in T]
    # ours works on standardised features, as in BOM-21
    allm = np.vstack([X, T])
    mu, sd = allm.mean(axis=0), allm.std(axis=0)
    sd[sd == 0] = 1
    ours = _ours().fit((X - mu) / sd, labels)
    o_pred = [ours.predict(x) for x in (T - mu) / sd]
    o_truth = NONE if truth == LATENT else truth
    return {
        "published_wrong": sum(p != truth for p in p_pred) / len(test),
        "ours_wrong": sum(p != o_truth for p in o_pred) / len(test),
        "published_assigned": dict(Counter(map(str, p_pred))),
        "ours_assigned": dict(Counter(map(str, o_pred))),
    }


def ensc() -> int:
    from eval.replicate import SAMPLE_WORDS, _candidate_tokens, _chunks

    cfg = load_config()
    fed = _papers()
    rng = random.Random(derive_seed("fidelity-ensc", cfg))
    runs = []
    for _ in range(SPLITS):
        idx = list(range(len(fed["hamilton"])))
        rng.shuffle(idx)
        tr, te = idx[:TRAIN_HAMILTON], idx[TRAIN_HAMILTON:]
        train = {
            "hamilton": [fed["hamilton"][i] for i in sorted(tr)],
            "madison": fed["madison"],
            "jay": fed["jay"],
        }
        runs.append(_run(train, [fed["hamilton"][i] for i in sorted(te)], "hamilton"))
    a = {
        k: {
            "mean": float(np.mean([r[k] for r in runs])),
            "min": min(r[k] for r in runs),
            "max": max(r[k] for r in runs),
        }
        for k in ("published_wrong", "ours_wrong")
    }
    cand = _candidate_tokens()
    names = {
        "joseph_smith": "Joseph Smith",
        "rigdon": "Sidney Rigdon",
        "spalding": "Solomon Spalding",
        "cowdery": "Oliver Cowdery",
        "pratt": "Parley P. Pratt",
    }
    train_b = {k: _chunks(cand[v], SAMPLE_WORDS) for k, v in names.items()}
    b = _run(train_b, fed["hamilton"], LATENT)
    sweep = {}
    for size in SWEEP_WORDS:
        tr = {k: _chunks(cand[v], size) for k, v in names.items()}
        labels = [k for k in tr for _ in tr[k]]
        model = ENSCPublished(shrinkage=SHRINKAGE, lam=LAM).fit(
            _rel([t for k in tr for t in tr[k]]), labels
        )
        got = Counter(str(model.predict(x)) for x in _rel(fed["hamilton"]))
        sweep[size] = {"texts": len(labels), "wrong": 1 - got[LATENT] / 51, "assigned": dict(got)}
    result = {
        **stamp(),
        "settings": {"shrinkage": SHRINKAGE, "lam": LAM, "words": len(WORDS), "splits": SPLITS},
        "published": PUBLISHED,
        "study_a_code": a,
        "study_b_text": b,
        "study_b_samples": {k: len(v) for k, v in train_b.items()},
        "study_b_by_sample_words": sweep,
    }
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "ensc.json").write_text(json.dumps(result, indent=1) + "\n")
    print(
        f"A (Hamilton+Madison+Jay, 25 Hamilton tests, {SPLITS} splits): published-rule wrong "
        f"{a['published_wrong']['mean']:.1%} [{a['published_wrong']['min']:.0%}-"
        f"{a['published_wrong']['max']:.0%}], ours {a['ours_wrong']['mean']:.1%}; "
        f"Funai {PUBLISHED['A']:.0%}"
    )
    print(
        f"B (BoM candidates, 51 Hamilton tests -> latent): published-rule wrong "
        f"{b['published_wrong']:.1%} {b['published_assigned']}, ours {b['ours_wrong']:.1%} "
        f"{b['ours_assigned']}; Funai {PUBLISHED['B']:.2%}"
    )
    for size, v in sweep.items():
        print(f"  B with {size:>5}-word candidate samples: wrong {v['wrong']:.1%} {v['assigned']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["ensc"]:
        return ensc()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
