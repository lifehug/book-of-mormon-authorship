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
because the share sent to the latent author turns out to depend on them, with and without the
2011 paper's text-size adjustment (eq. 12). Nothing here touches
the Book of Mormon or changes a registered result.

``gi``: Kestemont et al. (2016), Table 1, General Imposters ("O2") on the six PAN 2014
verification corpora (test set 2), word unigrams, cosine distance on "tf" and "tf-std" vectors.
Vectors are built exactly as their code builds them (``github.com/mikekestemont/ruzicka``,
``code/01pan_experiments.py``: whitespace tokens, case kept, full vocabulary, L2-normalised
term frequencies; tf-std divides by each feature's standard deviation over the known texts, then
L2-normalises; each problem's known texts averaged into a profile; imposters are the other
problems' profiles, 30 per round, 100 rounds, half the features per round). The rounds are run
by *our* ``classic.imposters.general_imposters``, so the check isolates our algorithm. Their
score shifter is refitted on the training set and applied to the test set; the measure is
AUC x c@1 (x 100). Known difference: their rounds sample features with replacement, ours
without. Data: PAN 2014 (Zenodo 10.5281/zenodo.3716033), held in the private repo.

Usage::

    python -m eval.fidelity ensc      # -> data/benchmark/fidelity/ensc.json
    python -m eval.fidelity gi        # -> data/benchmark/fidelity/gi.json
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
    tests, lengths = _rel(fed["hamilton"]), [len(t) for t in fed["hamilton"]]
    for size in SWEEP_WORDS:
        tr = {k: _chunks(cand[v], size) for k, v in names.items()}
        labels = [k for k in tr for _ in tr[k]]
        X = _rel([t for k in tr for t in tr[k]])
        row = {"texts": len(labels)}
        for name, adj in (("pooled", False), ("size_adjusted", True)):
            model = ENSCPublished(shrinkage=SHRINKAGE, lam=LAM, size_adjust=adj).fit(X, labels)
            got = Counter(str(model.predict(x, w)) for x, w in zip(tests, lengths, strict=True))
            row[name] = {"wrong": 1 - got[LATENT] / len(lengths), "assigned": dict(got)}
        sweep[size] = row
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
        print(
            f"  B, {size:>5}-word samples: pooled sd wrong {v['pooled']['wrong']:.1%}, "
            f"size-adjusted (2011 eq. 12) wrong {v['size_adjusted']['wrong']:.1%}"
        )
    return 0


PAN = Path("data/private/pan14/extracted")
PAN_CORPORA = {  # Kestemont et al. Table 1 column -> PAN 2014 corpus name
    "Dutch essays": "dutch-essays",
    "Dutch reviews": "dutch-reviews",
    "English essays": "english-essays",
    "English novels": "english-novels",
    "Greek articles": "greek-articles",
    "Spanish articles": "spanish-articles",
}
# Kestemont et al. (2016) Table 1, O2, word unigrams, test AUC x c@1
KESTEMONT_O2 = {
    "cosine - tf": [76.59, 36.58, 24.95, 30.55, 48.63, 69.52],
    "cosine - tf-std": [87.50, 33.58, 29.12, 37.35, 50.20, 63.41],
}
GI_ROUNDS, GI_FEATURES, GI_IMPOSTERS = 100, 0.5, 30  # ruzicka 01pan_experiments.py


def _pan_dir(split: str, corpus: str) -> Path:
    tag = "training-corpus" if split == "train" else "test-corpus2"
    hits = [d for d in PAN.rglob(f"pan14-author-verification-{tag}-{corpus}-*") if d.is_dir()]
    if not hits:
        raise SystemExit(f"PAN 2014 {split} {corpus} not found under {PAN} (private repo)")
    return hits[0]


def _pan_problems(d: Path) -> tuple[list[str], dict[str, list[str]], dict[str, str], dict]:
    truth = dict(
        ln.split()
        for ln in (d / "truth.txt").read_text(encoding="utf-8-sig").splitlines()
        if ln.strip()
    )
    ids, known, unknown = [], {}, {}
    for prob in sorted(p for p in d.iterdir() if p.is_dir()):
        texts = [f.read_text(encoding="utf-8", errors="ignore") for f in sorted(prob.glob("*.txt"))]
        names = [f.stem for f in sorted(prob.glob("*.txt"))]
        known[prob.name] = [t for t, n in zip(texts, names, strict=True) if n != "unknown"]
        unknown[prob.name] = texts[names.index("unknown")]
        ids.append(prob.name)
    return ids, known, unknown, truth


def _vectors(known: dict, unknown: dict, ids: list[str], space: str):
    vocab = sorted({w for k in ids for t in known[k] for w in t.split()})
    col = {w: i for i, w in enumerate(vocab)}

    def tf(texts: list[str]) -> np.ndarray:
        m = np.zeros((len(texts), len(vocab)))
        for r, t in enumerate(texts):
            for w in t.split():
                if w in col:
                    m[r, col[w]] += 1
        n = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.where(n == 0, 1, n)

    K = tf([t for k in ids for t in known[k]])
    U = tf([unknown[k] for k in ids])
    if space == "tf-std":
        sd = K.std(axis=0)
        sd[sd == 0] = 1
        K, U = K / sd, U / sd
        K /= np.where((n := np.linalg.norm(K, axis=1, keepdims=True)) == 0, 1, n)
        U /= np.where((n := np.linalg.norm(U, axis=1, keepdims=True)) == 0, 1, n)
    owner = [k for k in ids for _ in known[k]]
    P = np.vstack([K[[i for i, o in enumerate(owner) if o == k]].mean(axis=0) for k in ids])
    return P, U


def _gi_scores(P: np.ndarray, U: np.ndarray, seed: int) -> list[float]:
    from classic.imposters import general_imposters

    out = []
    for i in range(len(P)):
        others = np.delete(P, i, axis=0)
        out.append(
            general_imposters(
                U[i],
                P[i],
                others,
                feature_fraction=GI_FEATURES,
                trials=GI_ROUNDS,
                distance="cosine",
                seed=seed + i,
                n_imposters=min(GI_IMPOSTERS, len(others)),
            )
        )
    return out


def _shift(scores: list[float], p1: float, p2: float) -> list[float]:
    lo, hi = min(scores), max(scores)
    span = (hi - lo) or 1e-6

    def resc(v: float, a: float, b: float) -> float:
        return a + (v - lo) / span * (b - a)

    return [resc(v, 0.0, p1) if v <= p1 else resc(v, p2, 1.0) if v >= p2 else 0.5 for v in scores]


def _auc(scores: list[float], truth: list[int]) -> float:
    """Area under the ROC curve as the Mann-Whitney statistic; ties count half."""
    pos = [s for s, t in zip(scores, truth, strict=True) if t == 1]
    neg = [s for s, t in zip(scores, truth, strict=True) if t == 0]
    wins = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def _auc_c1(scores: list[float], truth: list[int]) -> float:
    n = len(truth)
    nu = sum(s == 0.5 for s in scores)
    pairs = zip(scores, truth, strict=True)
    nc = sum((s > 0.5 and t == 1) or (s < 0.5 and t == 0) for s, t in pairs)
    return _auc(scores, truth) * (nc + nu * nc / n) / n


def _fit_shift(scores: list[float], truth: list[int]) -> tuple[float, float]:
    grid = np.round(np.arange(0.0, 1.0001, 0.01), 2)
    best = (-1.0, 0.25, 0.75)
    for p1 in grid:
        for p2 in grid[grid >= p1]:
            v = _auc_c1(_shift(scores, p1, p2), truth)
            if v > best[0]:
                best = (v, float(p1), float(p2))
    return best[1], best[2]


def gi() -> int:
    cfg = load_config()
    seed = derive_seed("fidelity-gi", cfg)
    rows = {}
    for space, published in KESTEMONT_O2.items():
        vs = space.split(" - ")[1]
        row = {}
        for (label, corpus), pub in zip(PAN_CORPORA.items(), published, strict=True):
            res = {}
            for split in ("train", "test"):
                ids, known, unknown, truth = _pan_problems(_pan_dir(split, corpus))
                P, U = _vectors(known, unknown, ids, vs)
                res[split] = (_gi_scores(P, U, seed), [int(truth[k] == "Y") for k in ids])
            p1, p2 = _fit_shift(*res["train"])
            ours = 100 * _auc_c1(_shift(res["test"][0], p1, p2), res["test"][1])
            row[label] = {"ours": round(ours, 2), "published": pub, "p1": p1, "p2": p2}
            print(f"{space:16s} {label:17s} ours {ours:6.2f}  published {pub:6.2f}", flush=True)
        rows[space] = row
    result = {
        **stamp(),
        "settings": {"rounds": GI_ROUNDS, "feature_share": GI_FEATURES, "imposters": GI_IMPOSTERS},
        "source": "Kestemont et al. 2016 Table 1 (O2, word unigrams, test, AUC x c@1)",
        "results": rows,
    }
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "gi.json").write_text(json.dumps(result, indent=1) + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["ensc"]:
        return ensc()
    if args[:1] == ["gi"]:
        return gi()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
