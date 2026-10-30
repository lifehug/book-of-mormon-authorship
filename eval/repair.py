"""Repair or retire the methods that failed the benchmark (BOM-58).

Runs the plan in ``docs/repair-plan.md``, which was committed before this ran. Two candidate
repairs:

* **General Imposters** with ``repair.gi_feature_fraction_provisional`` of the features sampled
  per round (registered: ``classic.imposters.feature_fraction``);
* **ENSC as published** (``classic/ensc_published.py``: latent author, the 2011 text-size
  adjustment), shrinkage by cross-validation over the registered grid, lambda the smallest on
  ``repair.ensc_lambda_grid_provisional`` with at most 5% false "none" on in-set tests.

Each is tested on the BOM-21 tasks and on a **fresh** set of corpus authors that no earlier step
used. Every threshold and setting is calibrated on the BOM-21 tasks only and applied unchanged
to the fresh authors, so the fresh result says whether the repair generalises. A method is
repaired only if it meets both section 7 bars on both sets; the registered settings are
reported beside it.

Usage::

    python -m eval.repair      # -> data/benchmark/repair.json
"""

from __future__ import annotations

import copy
import json
import random
import re
import sys
from pathlib import Path

import numpy as np

from classic.ensc_published import LATENT, ENSCPublished
from eval.benchmark import (
    TASKS,
    _masked_tokens,
    calibrate_gi,
    imposter_pool,
    load_tasks,
    run_task,
)
from eval.power import blocks
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/benchmark/repair.json")


def used_authors() -> set[str]:
    """Authors already used by BOM-20 (corpus demo) and BOM-48 (time-split baseline)."""
    a = set(json.loads(Path("data/classic/corpus_run.json").read_text())["authors"])
    a |= set(json.loads(Path("data/benchmark/timesplit.json").read_text())["baseline"]["authors"])
    return a


def fresh_task(cfg: dict) -> dict:
    """``repair.fresh_authors_provisional`` corpus authors not used before; each held-out work
    gives ``benchmark.trials`` tests, the author's other works the reference."""
    from classic.corpus_run import eligible

    spec = json.loads(TASKS.read_text())
    bm = cfg["benchmark"]
    n = bm["test_words"]
    used = used_authors()
    task_prefixes = tuple(spec["dictated"].get("exclude_authors_from_pool", []))
    # the plan's "personal authors": eligible() lets through collective attributions
    collective = re.compile(r"\b(various|anonymous|unknown|several)\b")
    pool = {
        a: w
        for a, w in eligible(cfg).items()
        if a not in used and not a.startswith(task_prefixes) and not collective.search(a)
    }
    rng = random.Random(derive_seed("bom58-fresh", cfg))
    k = cfg["repair"]["fresh_authors_provisional"]
    authors = sorted(rng.sample(sorted(pool), min(k, len(pool))))
    refs, tests, held = {}, [], {}
    for a in authors:
        works = pool[a]
        h = rng.choice(works)
        held[a] = h["work_id"]
        toks = _masked_tokens([w["work_id"] for w in works])
        refs[a] = blocks([t for w in works if w is not h for t in toks[w["work_id"]]])
        ht = toks[h["work_id"]]
        for _ in range(bm["trials"]):
            s = rng.randrange(len(ht) - n + 1)
            tests.append((a, ht[s : s + n], None))
    return {"authors": refs, "tests": tests, "held_out": held, "eligible": len(pool)}


def _pub(rec: dict, shrinkage: float, lam: float, drop: str | None):
    X, labels, x = rec["_ensc"]
    if drop is not None:
        keep = [i for i, y in enumerate(labels) if y != drop]
        X, labels = X[keep], [labels[i] for i in keep]
    if len(set(labels)) < 2 or len(labels) <= len(set(labels)):
        return None
    model = ENSCPublished(shrinkage=shrinkage, lam=lam, size_adjust=True).fit(X, labels)
    return model.predict(x, rec["_n"])


def calibrate_ensc_published(recs: list[dict], cfg: dict) -> dict:
    """Shrinkage with the best open-set accuracy over the registered grid (Amendment 2); lambda
    the smallest (most willing to say "none") with at most 5% false "none" on in-set tests."""
    grid = cfg["classic"]["ensc"]["shrinkage_grid"]
    lams = sorted(cfg["repair"]["ensc_lambda_grid_provisional"])
    table = {}
    for s in grid:
        for lam in lams:
            right = total = 0
            for r in recs:
                for p, want in ((_pub(r, s, lam, None), r["author"]),
                                (_pub(r, s, lam, r["author"]), LATENT)):  # fmt: skip
                    if p is not None:
                        total += 1
                        right += p == want
            table[f"{s}|{lam}"] = right / max(1, total)
    best_s = max(grid, key=lambda s: max(table[f"{s}|{lam}"] for lam in lams))
    chosen = None
    for lam in lams:
        made = [p for p in (_pub(r, best_s, lam, None) for r in recs) if p is not None]
        if (
            sum(p == LATENT for p in made) / max(1, len(made))
            <= cfg["benchmark"]["max_open_set_fpr"]
        ):
            chosen = lam
            break
    return {"cv_open_set_accuracy": table, "shrinkage": best_s, "lambda": chosen}


def ensc_verdict(recs: list[dict], cal: dict) -> dict:
    if cal["lambda"] is None:
        return {"closed_set": None, "open_set_fpr": None}
    s, lam = cal["shrinkage"], cal["lambda"]
    ins = [(_pub(r, s, lam, None), r["author"]) for r in recs]
    outs = [p for p in (_pub(r, s, lam, r["author"]) for r in recs) if p is not None]
    return {
        "closed_set": sum(p == a for p, a in ins) / len(ins),
        "open_set_fpr": sum(p != LATENT for p in outs) / max(1, len(outs)),
        "false_none": sum(p == LATENT for p, _ in ins) / len(ins),
    }


def gi_verdict(recs: list[dict], match: float) -> dict:
    neg = [r["gi_open_negative"] for r in recs if r["gi_open_negative"] is not None]
    return {
        "closed_set": sum(r["general_imposters"] == r["author"] for r in recs) / len(recs),
        "open_set_fpr": float(np.mean([v > match for v in neg])),
    }


def _passes(v: dict, cfg: dict) -> bool:
    bm = cfg["benchmark"]
    return (
        v["closed_set"] is not None
        and v["closed_set"] >= bm["pass_closed_set"]
        and v["open_set_fpr"] <= bm["max_open_set_fpr"]
    )


def run() -> int:
    cfg = load_config()
    spec = json.loads(TASKS.read_text())
    variants = {"registered": cfg, "repair": copy.deepcopy(cfg)}
    ff = cfg["repair"]["gi_feature_fraction_provisional"]
    variants["repair"]["classic"]["imposters"]["feature_fraction"] = ff

    bench_tasks = load_tasks(cfg)
    pools = {
        name: imposter_pool(task["pool_set"], set(spec[name].get("exclude_from_pool", [])), cfg,
                            task["pool_genre"], task["pool_exclude_authors"],
                            spec[name].get("imposter_fill"))
        for name, task in bench_tasks.items()
    }  # fmt: skip
    fresh = fresh_task(cfg)
    fresh_pool = imposter_pool("general_prose", set(), cfg, None, tuple(fresh["authors"]))
    print(f"fresh: {len(fresh['authors'])} authors of {fresh['eligible']:,} eligible, "
          f"{len(fresh['tests'])} tests, pool {len(fresh_pool)}", flush=True)  # fmt: skip

    recs: dict[str, dict[str, list[dict]]] = {}
    for vname, vcfg in variants.items():
        rng = random.Random(derive_seed(f"repair:{vname}", cfg))
        b = [r for name, t in bench_tasks.items() for r in run_task(t, pools[name], vcfg, rng)]
        f = run_task(fresh, fresh_pool, vcfg, rng)
        recs[vname] = {"bom21": b, "fresh": f}
        print(f"{vname}: {len(b)} BOM-21 and {len(f)} fresh records", flush=True)

    result: dict = {**stamp(), "plan": "docs/repair-plan.md", "fresh_authors": fresh["authors"],
                    "fresh_held_out": fresh["held_out"]}  # fmt: skip
    rate = cfg["benchmark"]["max_open_set_fpr"]
    for vname, rs in recs.items():
        b, f = rs["bom21"], rs["fresh"]
        th = calibrate_gi([r["gi_positive"] for r in b],
                          [r["gi_open_negative"] for r in b if r["gi_open_negative"] is not None],
                          rate)  # fmt: skip
        gi = {"threshold_from_bom21": th, "bom21": gi_verdict(b, th["match"]),
              "fresh": gi_verdict(f, th["match"])}  # fmt: skip
        gi["repaired"] = _passes(gi["bom21"], cfg) and _passes(gi["fresh"], cfg)
        result[f"general_imposters_{vname}"] = gi
        delta = {
            m: {"bom21": sum(r[m] == r["author"] for r in b) / len(b),
                "fresh": sum(r[m] == r["author"] for r in f) / len(f)}
            for m in ("burrows_delta", "cosine_delta")
        }  # fmt: skip
        result[f"deltas_closed_set_{vname}"] = delta
    cal = calibrate_ensc_published(recs["registered"]["bom21"], cfg)
    ens = {"calibration_from_bom21": {k: v for k, v in cal.items() if k != "cv_open_set_accuracy"},
           "cv_open_set_accuracy": cal["cv_open_set_accuracy"],
           "bom21": ensc_verdict(recs["registered"]["bom21"], cal),
           "fresh": ensc_verdict(recs["registered"]["fresh"], cal)}  # fmt: skip
    ens["repaired"] = (ens["bom21"]["closed_set"] is not None and _passes(ens["bom21"], cfg)
                       and _passes(ens["fresh"], cfg))  # fmt: skip
    result["ensc_published"] = ens
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    for k in ("general_imposters_registered", "general_imposters_repair"):
        v = result[k]
        print(f"{k}: BOM-21 {v['bom21']}, fresh {v['fresh']}, repaired {v['repaired']}")
    print(f"ensc_published: {ens['calibration_from_bom21']}, BOM-21 {ens['bom21']}, "
          f"fresh {ens['fresh']}, repaired {ens['repaired']}")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
