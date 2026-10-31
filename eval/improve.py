"""Improving the prior methods (BOM-60), following ``docs/improvement-plan.md``.

Development uses data already seen: the BOM-21 tasks and BOM-58's 30 fresh authors. Every
threshold is calibrated on the BOM-21 tasks and applied unchanged to the other set.

``delta``: a verification score for Burrows' and Cosine Delta. The distance to the nearest
author's profile; "none of these" when even the nearest is farther than a threshold set at a
5% false-"none" rate on in-set tests (the rule of Amendment 7, Change 4). In-set: the true author
is among the profiles; open set: the true author removed, and the method should say "none".

``ensc-size``: ENSC's text-size model (Schaalje et al. 2011, eq. 12, ``s^2 = a c^p / w^q``) was
fitted on two authors. Refit on BOM-58's 30 authors at Schaalje et al.'s block sizes and
Funai's 108 words, then rerun BOM-57's sample-length test (study B) with both models.

``gi-rounds``: General Imposters with ``repair.gi_trials_provisional`` rounds (registered 100),
so the score cannot pin at its maximum, on the BOM-21 tasks (whose imposters are already
genre-matched), against the registered settings; thresholds and the held-out false-positive rate
as in BOM-21 (two folds).

Usage::

    python -m eval.improve delta      # -> data/benchmark/improve_delta.json
    python -m eval.improve ensc-size  # -> data/benchmark/improve_ensc_size.json
    python -m eval.improve gi-rounds  # -> data/benchmark/improve_gi_rounds.json
    python -m eval.improve evaluate   # once, on the second fresh set -> improve_evaluation.json

``evaluate`` draws the evaluation set (seed "bom60-eval", excluding every author used before,
BOM-58's included) and runs every method as registered and with each change, with every threshold
and setting read from the committed development results, never recomputed here.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np

from eval.benchmark import load_tasks, run_task
from eval.repair import fresh_task
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

DIR = Path("data/benchmark")


def _scores(recs: list[dict], method: str) -> tuple[list[float], list[float]]:
    """(in-set nearest distance, open-set nearest distance with the true author removed)."""
    ins, outs = [], []
    for r in recs:
        d = r["_delta_dist"][method]
        ins.append(min(d.values()))
        others = [v for k, v in d.items() if k != r["author"]]
        if others:
            outs.append(min(others))
    return ins, outs


def _verdict(recs: list[dict], method: str, t: float) -> dict:
    ins, outs = _scores(recs, method)
    return {
        "closed_set": sum(r[f"{method}_delta"] == r["author"] for r in recs) / len(recs),
        "false_none": float(np.mean([v > t for v in ins])),
        "open_set_fpr": float(np.mean([v <= t for v in outs])),
    }


def delta() -> int:
    cfg = load_config()
    rate = cfg["benchmark"]["max_open_set_fpr"]
    rng = random.Random(derive_seed("improve-delta", cfg))
    bench = [r for t in load_tasks(cfg).values() for r in run_task(t, [], cfg, rng, gi=False)]
    fresh = run_task(fresh_task(cfg), [], cfg, rng, gi=False)
    result: dict = {**stamp(), "plan": "docs/improvement-plan.md, improvement 2"}
    for m in ("burrows", "cosine"):
        ins, _ = _scores(bench, m)
        t = float(np.quantile(ins, 1 - rate))  # at most 5% of in-set tests answered "none"
        result[m] = {
            "threshold_from_bom21": t,
            "bom21": _verdict(bench, m, t),
            "bom58_fresh": _verdict(fresh, m, t),
        }
        print(f"{m}: threshold {t:.4f}; BOM-21 {result[m]['bom21']}; "
              f"BOM-58 fresh {result[m]['bom58_fresh']}")  # fmt: skip
    (DIR / "improve_delta.json").write_text(json.dumps(result, indent=1) + "\n")
    return 0


# Schaalje et al. (2011), section 4: the block sizes their variance model was measured at
SIZE_BLOCKS = (100, 200, 500, 1000, 2000, 3000, 4000, 5000)


def fit_size_model(texts: dict[str, list[str]], words: list[str]) -> dict:
    """Least squares on ``log v = log a + p log c - q log w`` over every author, block size and
    word with at least three blocks and a non-zero mean and variance."""
    rows = []
    for toks in texts.values():
        for w in SIZE_BLOCKS:
            blocks = [toks[i : i + w] for i in range(0, len(toks) - w + 1, w)]
            if len(blocks) < 3:
                continue
            rel = np.array([[b.count(x) / w for x in words] for b in blocks])
            c, v = rel.mean(axis=0), rel.var(axis=0, ddof=1)
            for cj, vj in zip(c, v, strict=True):
                if cj > 0 and vj > 0:
                    rows.append((np.log(cj), np.log(w), np.log(vj)))
    A = np.array([[1.0, r[0], -r[1]] for r in rows])
    y = np.array([r[2] for r in rows])
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ coef
    return {"a": float(np.exp(coef[0])), "p": float(coef[1]), "q": float(coef[2]),
            "points": len(rows), "r2": float(1 - resid.var() / y.var())}  # fmt: skip


def ensc_size() -> int:
    from collections import Counter

    from classic.ensc_published import LATENT, SIZE_A, SIZE_POWER, SIZE_W, ENSCPublished
    from eval.fidelity import LAM, SHRINKAGE, SWEEP_WORDS, WORDS, _papers, _rel
    from eval.replicate import _candidate_tokens, _chunks

    cfg = load_config()
    fresh = fresh_task(cfg)
    texts = {a: [t for b in bl for t in b] for a, bl in fresh["authors"].items()}
    fit = fit_size_model(texts, WORDS)
    models = {"published": (SIZE_A, SIZE_POWER, SIZE_W), "refit": (fit["a"], fit["p"], fit["q"])}
    print(
        f"refit on {len(texts)} authors, {fit['points']:,} points (R2 {fit['r2']:.2f}): a "
        f"{fit['a']:.4g}, p {fit['p']:.4f}, q {fit['q']:.4f}; published 0.259, 1.1147, 0.661"
    )
    fed = _papers()
    cand = _candidate_tokens()
    names = {"joseph_smith": "Joseph Smith", "rigdon": "Sidney Rigdon",
             "spalding": "Solomon Spalding", "cowdery": "Oliver Cowdery",
             "pratt": "Parley P. Pratt"}  # fmt: skip
    tests, lengths = _rel(fed["hamilton"]), [len(t) for t in fed["hamilton"]]
    sweep = {}
    for size in SWEEP_WORDS:
        tr = {k: _chunks(cand[v], size) for k, v in names.items()}
        labels = [k for k in tr for _ in tr[k]]
        X = _rel([t for k in tr for t in tr[k]])
        sweep[size] = {}
        for mname, sm in models.items():
            m = ENSCPublished(shrinkage=SHRINKAGE, lam=LAM, size_adjust=True, size_model=sm)
            m.fit(X, labels)
            got = Counter(str(m.predict(x, w)) for x, w in zip(tests, lengths, strict=True))
            sweep[size][mname] = 1 - got[LATENT] / len(lengths)
        print(f"  {size:>5}-word samples: wrong, published model {sweep[size]['published']:.1%}, "
              f"refit {sweep[size]['refit']:.1%}")  # fmt: skip
    spread = {k: max(v[k] for v in sweep.values()) - min(v[k] for v in sweep.values())
              for k in models}  # fmt: skip
    result = {**stamp(), "plan": "docs/improvement-plan.md, improvement 3", "fit": fit,
              "models": models, "study_b_wrong_by_sample_words": sweep,
              "swing_across_sample_lengths": spread}  # fmt: skip
    (DIR / "improve_ensc_size.json").write_text(json.dumps(result, indent=1) + "\n")
    print("swing across sample lengths:", {k: f"{v:.1%}" for k, v in spread.items()})
    return 0


def _gi_bom21(recs: list[dict], cfg: dict) -> dict:
    """BOM-21's General Imposters verdict: thresholds on all records, false positives on held-out
    halves (two folds, seeded as in BOM-21)."""
    from eval.benchmark import calibrate_gi

    rate = cfg["benchmark"]["max_open_set_fpr"]
    pos = [r["gi_positive"] for r in recs]
    neg = [r["gi_open_negative"] for r in recs if r["gi_open_negative"] is not None]
    th = calibrate_gi(pos, neg, rate)
    idx = list(range(len(neg)))
    random.Random(derive_seed("benchmark-gi-fold", cfg)).shuffle(idx)
    half = len(idx) // 2
    fprs = []
    for cal, ev in ((idx[:half], idx[half:]), (idx[half:], idx[:half])):
        t = np.quantile([neg[i] for i in cal], 1 - rate)
        fprs.append(float(np.mean([neg[i] > t for i in ev])))
    closed = sum(r["general_imposters"] == r["author"] for r in recs) / len(recs)
    fpr = float(np.mean(fprs))
    return {"thresholds": th, "closed_set": closed, "open_set_fpr": fpr,
            "passes": closed >= cfg["benchmark"]["pass_closed_set"] and fpr <= rate,
            "match_at_maximum": th["match"] >= 1.0}  # fmt: skip


def gi_rounds() -> int:
    import copy

    from eval.benchmark import TASKS, imposter_pool

    cfg = load_config()
    spec = json.loads(TASKS.read_text())
    tasks = load_tasks(cfg)
    pools = {
        name: imposter_pool(t["pool_set"], set(spec[name].get("exclude_from_pool", [])), cfg,
                            t["pool_genre"], t["pool_exclude_authors"],
                            spec[name].get("imposter_fill"))
        for name, t in tasks.items()
    }  # fmt: skip
    more = copy.deepcopy(cfg)
    more["classic"]["imposters"]["trials"] = cfg["repair"]["gi_trials_provisional"]
    result: dict = {**stamp(), "plan": "docs/improvement-plan.md, improvement 4"}
    for vname, vcfg in (("registered", cfg), ("more_rounds", more)):
        rng = random.Random(derive_seed("improve-gi", cfg))
        recs = [r for n, t in tasks.items() for r in run_task(t, pools[n], vcfg, rng)]
        result[vname] = _gi_bom21(recs, cfg)
        result[vname]["trials"] = vcfg["classic"]["imposters"]["trials"]
        print(f"{vname}: {result[vname]}", flush=True)
    (DIR / "improve_gi_rounds.json").write_text(json.dumps(result, indent=1) + "\n")
    return 0


def evaluate() -> int:
    import copy

    from classic.ensc_published import LATENT, ENSCPublished
    from eval.benchmark import imposter_pool

    cfg = load_config()
    rate = cfg["benchmark"]["max_open_set_fpr"]
    names = ("repair", "improve_delta", "improve_ensc_size", "improve_gi_rounds")
    dev = {n: json.loads((DIR / f"{n}.json").read_text()) for n in names}
    seen = frozenset(dev["repair"]["fresh_authors"])
    task = fresh_task(cfg, seed="bom60-eval", exclude=seen)
    assert not set(task["authors"]) & seen
    pool = imposter_pool("general_prose", set(), cfg, None, tuple(task["authors"]))
    print(f"evaluation: {len(task['authors'])} authors, {len(task['tests'])} tests, "
          f"pool {len(pool)}", flush=True)  # fmt: skip
    more = copy.deepcopy(cfg)
    more["classic"]["imposters"]["trials"] = cfg["repair"]["gi_trials_provisional"]
    runs = {}
    for vname, vcfg in (("registered", cfg), ("more_rounds", more)):
        rng = random.Random(derive_seed(f"improve-eval:{vname}", cfg))
        runs[vname] = run_task(task, pool, vcfg, rng, progress=vname)
        print(f"{vname}: {len(runs[vname])} records", flush=True)
    recs = runs["registered"]
    result: dict = {**stamp(), "plan": "docs/improvement-plan.md, evaluation",
                    "authors": sorted(task["authors"]), "held_out": task["held_out"]}  # fmt: skip

    # General Imposters: thresholds from BOM-21 (registered from BOM-58, 1,000 rounds from 4)
    for vname, th in (
        ("registered", dev["repair"]["general_imposters_registered"]["threshold_from_bom21"]),
        ("more_rounds", dev["improve_gi_rounds"]["more_rounds"]["thresholds"]),
    ):
        rs = runs[vname]
        neg = [r["gi_open_negative"] for r in rs if r["gi_open_negative"] is not None]
        closed = sum(r["general_imposters"] == r["author"] for r in rs) / len(rs)
        fpr = float(np.mean([v > th["match"] for v in neg]))
        result[f"general_imposters_{vname}"] = {
            "closed_set": closed, "open_set_fpr": fpr,
            "passes": closed >= cfg["benchmark"]["pass_closed_set"] and fpr <= rate,
        }  # fmt: skip

    # Delta: closed set as registered; the verification score with the development threshold
    for m in ("burrows", "cosine"):
        result[f"{m}_delta"] = _verdict(recs, m, dev["improve_delta"][m]["threshold_from_bom21"])

    # ENSC as published, with the published and the refitted size model; settings from BOM-58
    cal = dev["repair"]["ensc_published"]["calibration_from_bom21"]
    for mname, sm in dev["improve_ensc_size"]["models"].items():

        def pred(r: dict, drop: str | None, sm: list = sm):
            X, labels, x = r["_ensc"]
            if drop is not None:
                keep = [i for i, y in enumerate(labels) if y != drop]
                X, labels = X[keep], [labels[i] for i in keep]
            m = ENSCPublished(shrinkage=cal["shrinkage"], lam=cal["lambda"], size_adjust=True,
                              size_model=tuple(sm)).fit(X, labels)  # fmt: skip
            return m.predict(x, r["_n"])

        ins = [(pred(r, None), r["author"]) for r in recs]
        outs = [pred(r, r["author"]) for r in recs]
        result[f"ensc_published_{mname}_size_model"] = {
            "closed_set": sum(p == a for p, a in ins) / len(ins),
            "false_none": sum(p == LATENT for p, _ in ins) / len(ins),
            "open_set_fpr": sum(p != LATENT for p in outs) / len(outs),
        }
    (DIR / "improve_evaluation.json").write_text(json.dumps(result, indent=1) + "\n")
    for k, v in result.items():
        if isinstance(v, dict) and "closed_set" in v:
            print(f"{k}: {v}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["delta"]:
        return delta()
    if args[:1] == ["ensc-size"]:
        return ensc_size()
    if args[:1] == ["gi-rounds"]:
        return gi_rounds()
    if args[:1] == ["evaluate"]:
        return evaluate()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
