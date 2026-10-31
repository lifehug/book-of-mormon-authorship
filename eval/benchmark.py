"""The validation benchmark (BOM-21; pre-registration 6.1 and 7).

Before any Book of Mormon scoring, every method runs on known authors: the Federalist Papers,
pseudo-biblical works with known authors, dictated texts with known authors, and open-set cases
where the true author is removed. A method **passes** if its closed-set accuracy on 5,000-word
samples is at least ``benchmark.pass_closed_set`` (90%) and, at its calibrated threshold, its
open-set false-positive rate is at most ``benchmark.max_open_set_fpr`` (5%). The thresholds are
calibrated here, on benchmark data only (6.1), and committed before the blind run.

Tasks (``data/benchmark/tasks.json``, hand-curated and documented there):

* **federalist**: Hamilton, Madison and Jay (BOM-43's papers).
* **pseudo_biblical**: known-author imitation-scripture works (``pseudo_biblical_known.json``).
* **dictated**: Walter Scott's two dictated novels of 1819 tested against his hand-written novels
  and other novelists of 1810-1830.

Per test sample: (a) closed set -- each method's attribution among the task's authors; (b) General
Imposters' verification score for the true author (a positive) and, with the true author
removed, for the best remaining author (an open-set negative). Imposters for GI are resampled per
trial from a pool of genre-matched control samples (5.1, Amendment 2: 100 per trial from a pool
twice that size). ENSC's shrinkage is selected by 10-fold cross-validation over the registered
grid (Amendment 2) on open-set accuracy, and its alpha is the largest giving at most a 5%
false-"none" rate on in-set tests (pending ``classic.ensc.alpha``). Delta has no verification
score in 6.1 and is judged closed-set only.

GI's thresholds: *match* above the score with a 5% false-positive rate on open-set negatives,
*non-match* below the score with a 5% false-negative rate on positives (6.1). The open-set
false-positive rate that decides the pass is measured on held-out trials (two-fold, seeded), not
on the trials that set the threshold.

Usage::

    python -m eval.benchmark      # -> data/benchmark/benchmark.json, thresholds.json
"""

from __future__ import annotations

import gzip
import json
import random
import sys
import time
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
from eval.power import BLOCK, blocks, federalist, pseudo_biblical
from metadata.config import classic_kwargs, derive_seed, stamp
from metadata.config import load as load_config

DIR = Path("data/benchmark")
TASKS = DIR / "tasks.json"
OUT = DIR / "benchmark.json"
THRESHOLDS = DIR / "thresholds.json"
CLOSED = ("burrows_delta", "cosine_delta", "general_imposters", "ensc")


def _masked_tokens(work_ids: list[str]) -> dict[str, list[str]]:
    """Normalised text with KJV spans removed where masks exist (controls, known-answer texts),
    else as is."""
    from ocr_fix.normalize import norm_path
    from segment.build import original_words

    want = set(work_ids)
    spans = {}
    for group in ("controls", "known_answer"):
        path = Path(f"data/kjv_mask/{group}/spans.jsonl")
        if not path.exists():  # a fresh clone has only the committed .gz
            path = path.with_suffix(".jsonl.gz")
        if path.exists():
            text = gzip.open(path, "rt").read() if path.suffix == ".gz" else path.read_text()
            for ln in text.splitlines():
                r = json.loads(ln)
                if r["id"] in want:
                    spans[r["id"]] = r["spans"]
    cols = ["work_id", "source", "text_path"]
    rows = {
        r["work_id"]: r
        for r in pq.read_table("data/catalog/catalog.parquet", columns=cols).to_pylist()
        if r["work_id"] in want
    }
    out = {}
    for w in work_ids:
        text = norm_path(rows[w]).read_text(encoding="utf-8", errors="replace")
        out[w] = tokenize(" ".join(original_words(text, spans.get(w, []))))
    return out


def _middle(toks: list[str], n: int) -> list[str]:
    s = max(0, len(toks) // 2 - n // 2)
    return toks[s : s + n]


def load_tasks(cfg: dict) -> dict[str, dict]:
    """{task: {"authors": {author: [blocks]}, "tests": [(author, tokens)], "pool": [tokens]}}."""
    bm = cfg["benchmark"]
    n = bm["test_words"]
    rng = random.Random(derive_seed("benchmark-tasks", cfg))
    spec = json.loads(TASKS.read_text())
    tasks: dict[str, dict] = {}

    def held_out(by: dict[str, list[str]]) -> tuple[dict, list]:
        refs, tests = {}, []
        for a, toks in sorted(by.items()):
            bl = blocks(toks)
            k = n // BLOCK
            if len(bl) < k + bm["min_reference_blocks"]:
                refs[a] = bl  # too short to test; still a candidate
                continue
            for _ in range(bm["trials"]):
                s = rng.randrange(len(bl) - k + 1)
                tests.append((a, [w for b in bl[s : s + k] for w in b], (s, s + k)))
            refs[a] = bl
        return refs, tests

    for name, by in (("federalist", federalist()), ("pseudo_biblical", pseudo_biblical())):
        refs, tests = held_out(by)
        tasks[name] = {
            "authors": refs,
            "tests": tests,
            "pool_set": spec[name]["imposter_pool"],
            "pool_genre": None,
            "pool_exclude_authors": (),
        }
    d = spec["dictated"]
    ref_ids = [w for ws in d["reference"].values() for w in ws]
    toks = _masked_tokens(ref_ids + d["tests"])
    refs = {a: blocks([t for w in ws for t in toks[w]]) for a, ws in d["reference"].items()}
    tests = []
    for w in d["tests"]:
        bl = blocks(toks[w])
        for _ in range(bm["trials"]):
            s = rng.randrange(len(bl) - n // BLOCK + 1)
            tests.append((d["author"], [t for b in bl[s : s + n // BLOCK] for t in b], None))
    tasks["dictated"] = {
        "authors": refs,
        "tests": tests,
        "pool_set": d["imposter_pool"],
        "pool_genre": d.get("imposter_genre"),
        "pool_exclude_authors": tuple(d.get("exclude_authors_from_pool", [])),
    }
    return tasks


def imposter_pool(
    set_name: str,
    exclude: set[str],
    cfg: dict,
    genre: str | None = None,
    exclude_authors: tuple[str, ...] = (),
    fill: str | None = None,
) -> list[list[str]]:
    """Genre-matched control samples for GI (5.1): ``per_trial / imposter_fraction`` of them,
    never the task authors' own works.

    A work is left out when it is excluded by id *or* is another copy of an excluded work
    (``metadata.pseudo_biblical.work_key``): the curated list's copy of *The Late War* is not the
    one the task tests, and run 1 let it in. Sealed copies are always left out. When the set is
    too small for the registered size (the curated pseudo-biblical list has 18 works), every
    eligible work is used and the rest is drawn, seeded, from ``fill``, one copy per work
    (pending ``benchmark.imposter_fill``).
    """
    from metadata.pseudo_biblical import work_key
    from metadata.sealed import sealed_ids

    gi = cfg["classic"]["imposters"]
    size = round(gi["per_trial"] / gi["imposter_fraction"])
    n = cfg["benchmark"]["test_words"]
    meta = {
        r["work_id"]: r
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "author_norm", "title"]
        ).to_pylist()
    }
    labels = (
        {
            r["work_id"]: (r["genre"] or "").split(",")[0]
            for r in pq.read_table("data/catalog/genre.parquet").to_pylist()
        }
        if genre
        else {}
    )
    keys = {work_key(meta[w]["title"]) for w in exclude if w in meta}
    seal = sealed_ids()

    def listed(name: str) -> list[str]:
        path = Path(f"data/controls/{name}.txt")
        if not path.exists():
            raise SystemExit(f"{path} does not exist yet (the curated list is BOM-54's output)")
        return path.read_text().split()

    def ok(w: str) -> bool:
        return (
            w not in exclude
            and w not in seal
            and work_key(meta[w]["title"]) not in keys
            and (not genre or labels.get(w) == genre)
            and not (meta[w]["author_norm"] or "").startswith(exclude_authors)
        )

    ids = [w for w in listed(set_name) if ok(w)]
    rng = random.Random(derive_seed(f"benchmark-pool:{set_name}", cfg))
    pick = sorted(rng.sample(ids, min(size, len(ids))))
    toks = _masked_tokens(pick)
    pool = [_middle(toks[w], n) for w in pick if len(toks[w]) >= n]
    if fill and len(pool) < size:
        seen = {work_key(meta[w]["title"]) for w in pick}
        extra = [w for w in listed(fill) if ok(w) and w not in pick]
        random.Random(derive_seed(f"benchmark-pool-fill:{fill}", cfg)).shuffle(extra)
        queue = []
        for w in extra:
            k = work_key(meta[w]["title"])
            if k not in seen:
                seen.add(k)
                queue.append(w)
        while len(pool) < size and queue:
            batch, queue = queue[: size - len(pool)], queue[size - len(pool) :]
            toks = _masked_tokens(batch)
            pool += [_middle(toks[w], n) for w in batch if len(toks[w]) >= n]
    return pool


def _vec(docs: list[list[str]], vocab: list[str]) -> np.ndarray:
    return frequency_matrix([word_counts(d) for d in docs], vocab)


def run_task(
    task: dict,
    pool: list[list[str]],
    cfg: dict,
    rng: random.Random,
    gi: bool = True,
    progress: str | None = None,
) -> list[dict]:
    """One record per test: closed-set predictions, GI positive and open-set negative scores,
    the ENSC fits needed for selection, and both Deltas' distances to every author (BOM-60).
    ``gi=False`` skips General Imposters, the slow part, when only the other methods are needed."""
    kw = classic_kwargs(cfg)
    top_n = sorted(cfg["classic"]["mfw"])[len(cfg["classic"]["mfw"]) // 2]
    names = sorted(task["authors"])
    recs = []
    start = time.time()
    for k, (a, test, span) in enumerate(task["tests"], 1):
        if progress and (k % 25 == 0 or k == len(task["tests"])):
            done = (time.time() - start) / 60
            print(f"  {progress}: {k}/{len(task['tests'])} tests, {done:.0f} min", flush=True)
        refs = {
            b: (
                task["authors"][b]
                if b != a or span is None
                else task["authors"][b][: span[0]] + task["authors"][b][span[1] :]
            )
            for b in names
        }
        docs = [word_counts(b) for x in names for b in refs[x]]
        labels = [x for x in names for _ in refs[x]]
        vocab = build_vocabulary(docs, top_n=top_n, min_doc_fraction=kw["mfw_min_doc_fraction"])
        X = frequency_matrix(docs, vocab)
        x = _vec([test], vocab)[0]
        prof = {b: X[[i for i, y in enumerate(labels) if y == b]].mean(axis=0) for b in names}
        others = [b for b in names if b != a]
        if gi:
            P = _vec(pool, vocab)
            gi_args = {
                **kw["imposters"],
                "n_imposters": min(len(P), cfg["classic"]["imposters"]["per_trial"]),
            }
            gs = {
                b: general_imposters(x, prof[b], P, seed=rng.randrange(2**31), **gi_args)
                for b in names
            }
        burrows = nearest_authors(x, prof, method="burrows", reference=X)
        cosine = nearest_authors(x, prof, method="cosine", reference=X)
        recs.append(
            {
                "author": a,
                "burrows_delta": burrows[0][0],
                "cosine_delta": cosine[0][0],
                "_delta_dist": {"burrows": dict(burrows), "cosine": dict(cosine)},
                "general_imposters": max(names, key=lambda b: (gs[b], b)) if gi else None,
                "gi_positive": gs[a] if gi else None,
                "gi_open_negative": (max(gs[b] for b in others) if others else None)
                if gi
                else None,
                "_ensc": (X, labels, x),
                "_n": len(test),
            }
        )
    return recs


def _ensc_predict(rec: dict, shrinkage: float, alpha: float, priors: str, drop: str | None):
    X, labels, x = rec["_ensc"]
    if drop is not None:
        keep = [i for i, y in enumerate(labels) if y != drop]
        X, labels = X[keep], [labels[i] for i in keep]
    if len(set(labels)) < 2 or len(labels) <= len(set(labels)):
        return None
    return ENSC(shrinkage=shrinkage, alpha=alpha, priors=priors).fit(X, labels).classify(x).label


def calibrate_ensc(recs: list[dict], cfg: dict) -> dict:
    """Shrinkage by 10-fold CV on open-set accuracy (Amendment 2); alpha at <= 5% false-'none'."""
    en = cfg["classic"]["ensc"]
    priors = classic_kwargs(cfg)["ensc"]["priors"]
    alphas = cfg["benchmark"]["ensc_alpha_grid"]
    folds = 10
    order = list(range(len(recs)))
    random.Random(derive_seed("benchmark-ensc-cv", cfg)).shuffle(order)
    table = {}
    for s in en["shrinkage_grid"]:
        for al in alphas:
            right = total = 0
            for f in range(folds):
                for i in order[f::folds]:
                    r = recs[i]
                    p_in = _ensc_predict(r, s, al, priors, None)
                    p_out = _ensc_predict(r, s, al, priors, r["author"])
                    for p, want in ((p_in, r["author"]), (p_out, NONE)):
                        if p is not None:
                            total += 1
                            right += p == want
            table[f"{s}|{al}"] = right / max(1, total)
    best_s = max(en["shrinkage_grid"], key=lambda s: max(table[f"{s}|{a}"] for a in alphas))
    # alpha: the largest (most willing to say "none") whose false-'none' rate on in-set tests is
    # at most the registered 5%; a larger alpha catches more absent authors
    chosen_alpha = None
    for al in sorted(alphas, reverse=True):
        preds = [_ensc_predict(r, best_s, al, priors, None) for r in recs]
        made = [p for p in preds if p is not None]
        false_none = sum(p == NONE for p in made) / max(1, len(made))
        if false_none <= cfg["benchmark"]["max_open_set_fpr"]:
            chosen_alpha = al
            break
    return {"cv_open_set_accuracy": table, "shrinkage": best_s, "alpha": chosen_alpha}


def calibrate_gi(pos: list[float], neg: list[float], rate: float) -> dict:
    """6.1: match above the 5%-FPR score on negatives; non-match below the 5%-FNR score."""
    return {"match": float(np.quantile(neg, 1 - rate)), "non_match": float(np.quantile(pos, rate))}


def run(only: list[str] | None = None, out_dir: Path | None = None) -> int:
    cfg = load_config()
    bm = cfg["benchmark"]
    rng = random.Random(derive_seed("benchmark", cfg))
    tasks = load_tasks(cfg)
    if only:
        tasks = {k: v for k, v in tasks.items() if k in only}
    spec = json.loads(TASKS.read_text())
    recs_by: dict[str, list[dict]] = {}
    for name, task in tasks.items():
        exclude = set(spec[name].get("exclude_from_pool", []))
        pool = imposter_pool(
            task["pool_set"],
            exclude,
            cfg,
            task["pool_genre"],
            task["pool_exclude_authors"],
            spec[name].get("imposter_fill"),
        )
        print(
            f"{name}: {len(task['authors'])} authors, {len(task['tests'])} tests, "
            f"pool {len(pool)} from {task['pool_set']}",
            flush=True,
        )
        recs_by[name] = run_task(task, pool, cfg, rng)
    allrecs = [r for rs in recs_by.values() for r in rs]
    closed = {
        name: {m: sum(r[m] == r["author"] for r in rs) / len(rs) for m in CLOSED[:3]}
        for name, rs in recs_by.items()
    }
    overall = {m: sum(r[m] == r["author"] for r in allrecs) / len(allrecs) for m in CLOSED[:3]}

    # GI thresholds, and the open-set FPR on held-out trials (two folds)
    pos = [r["gi_positive"] for r in allrecs]
    neg = [r["gi_open_negative"] for r in allrecs if r["gi_open_negative"] is not None]
    rate = bm["max_open_set_fpr"]
    th = calibrate_gi(pos, neg, rate)
    idx = list(range(len(neg)))
    random.Random(derive_seed("benchmark-gi-fold", cfg)).shuffle(idx)
    half = len(idx) // 2
    fprs = []
    for cal, ev in ((idx[:half], idx[half:]), (idx[half:], idx[:half])):
        t = np.quantile([neg[i] for i in cal], 1 - rate)
        fprs.append(float(np.mean([neg[i] > t for i in ev])))
    gi_fpr = float(np.mean(fprs))

    ens = calibrate_ensc(allrecs, cfg)
    priors = classic_kwargs(cfg)["ensc"]["priors"]
    ens_closed = {}
    ens_open_fpr = None
    if ens["alpha"] is not None:
        for name, rs in recs_by.items():
            ps = [_ensc_predict(r, ens["shrinkage"], ens["alpha"], priors, None) for r in rs]
            ens_closed[name] = sum(p == r["author"] for p, r in zip(ps, rs, strict=True)) / len(rs)
        outs = [
            _ensc_predict(r, ens["shrinkage"], ens["alpha"], priors, r["author"]) for r in allrecs
        ]
        outs = [p for p in outs if p is not None]
        ens_open_fpr = sum(p != NONE for p in outs) / max(1, len(outs))
    ens_overall = (
        sum(v * len(recs_by[k]) for k, v in ens_closed.items()) / len(allrecs)
        if ens_closed
        else None
    )

    pass_cs, max_fpr = bm["pass_closed_set"], bm["max_open_set_fpr"]
    verdict = {
        "burrows_delta": {
            "closed_set": overall["burrows_delta"],
            "open_set_fpr": None,
            "passes": None,
            "note": "no verification score in 6.1; closed set only",
        },
        "cosine_delta": {
            "closed_set": overall["cosine_delta"],
            "open_set_fpr": None,
            "passes": None,
            "note": "no verification score in 6.1; closed set only",
        },
        "general_imposters": {
            "closed_set": overall["general_imposters"],
            "open_set_fpr": gi_fpr,
            "passes": overall["general_imposters"] >= pass_cs and gi_fpr <= max_fpr,
        },
        "ensc": {
            "closed_set": ens_overall,
            "open_set_fpr": ens_open_fpr,
            "passes": (
                ens_overall is not None
                and ens_overall >= pass_cs
                and ens_open_fpr is not None
                and ens_open_fpr <= max_fpr
            ),
        },
    }
    if th["match"] >= 1.0:
        verdict["general_imposters"]["note"] = (
            "match threshold is the maximum score: GI can never return 'match' at 5% FPR"
        )
    for r in allrecs:
        r.pop("_ensc")
        r.pop("_delta_dist", None)
    # yes/no findings for the specification curve (pipeline.cli.conclusions)
    per_test = {
        m: {
            "closed_set_pass": v["closed_set"] is not None and v["closed_set"] >= pass_cs,
            **({"passes": v["passes"]} if v["passes"] is not None else {}),
        }
        for m, v in verdict.items()
    }
    result = {
        **stamp(),
        "closed_set_by_task": closed,
        "ensc_closed_set_by_task": ens_closed,
        "verdict": verdict,
        "per_test": per_test,
        "gi_thresholds": th,
        "ensc": ens,
        "records": recs_by,
    }
    out, thresholds = (
        (out_dir / OUT.name, out_dir / THRESHOLDS.name) if out_dir else (OUT, THRESHOLDS)
    )
    out.write_text(json.dumps(result, indent=1) + "\n")
    thresholds.write_text(
        json.dumps(
            {
                **stamp(),
                "general_imposters": th,
                "ensc": {"shrinkage": ens["shrinkage"], "alpha": ens["alpha"]},
            },
            indent=1,
        )
        + "\n"
    )
    for m, v in verdict.items():
        cs = v["closed_set"] if v["closed_set"] is None else round(v["closed_set"], 3)
        print(f"  {m:<18} closed {cs}  open FPR {v['open_set_fpr']}  passes {v['passes']}")
    print(f"GI thresholds {th}; ENSC shrinkage {ens['shrinkage']} alpha {ens['alpha']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--tasks", nargs="*", help="run only these tasks (a dry run; not a result)")
    a = ap.parse_args(argv)
    return run(a.tasks)


if __name__ == "__main__":
    sys.exit(main())
