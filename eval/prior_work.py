"""The gain over prior work, on equal terms (BOM-68; Amendment 36, ``docs/prior-work-plan.md``).

``table`` puts every method, prior and ours, on the benchmark's own tests in one table, with every
time-locked model size beside the others (``by_size``; none singled out, owner 2026-11-06):
closed-set accuracy overall and by task with a bootstrap interval over tests, Amendment 25's
open-set false-match rate and the pass verdict (from ``data/benchmark/open_set.json``), and which
test set it was measured on. Methods share a test set when their records line up test by test (the
classical methods, the style embeddings and V3 on BOM-21's trials; the fine-tuned language models on
Amendment 22's held-out tails); within a set every pair of methods gets McNemar's exact test on the
tests one gets right and the other wrong. The published Book of Mormon attributions (BOM-22's
replications) are listed beside our replications of them, as counts. Names and numbers only.

``classic-tails`` runs the classical methods (Burrows and Cosine Delta, General Imposters, ENSC at
the benchmark's calibrated shrinkage and alpha; registered settings, as ``eval.benchmark.run_task``)
on Amendment 22's held-out tails, the very tests the fine-tuned language models are scored on:
references are each author's training words, the tests its held-out windows in the same order, so
``table`` pairs them with the language models test by test.

``ablation`` (designed; run on a GPU) repeats Amendment 22's ALM pipeline with an off-the-shelf
GPT-2 in place of the time-locked base, on the benchmark only: GPT-2 read modern web text, which
may include the Book of Mormon, so it is never applied to it. It writes ``alm_gpt2*.json`` in the
ALM format, so ``eval.open_set rescore`` and ``table`` pick it up.

Usage::

    python -m eval.prior_work table                   # -> data/benchmark/prior_work.json
    python -m eval.prior_work classic-tails           # -> prior_work_classic_tails.json
    python -m eval.prior_work ablation gpt2|gpt2-medium [--micro-batch 8]
    python -m eval.prior_work files                   # the ablation's input files, for a pod
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

DIR = Path("data/benchmark")
CLASSIC = ("burrows_delta", "cosine_delta", "general_imposters")
REPLICATIONS = {  # file -> keys holding the published counts and ours
    "replication_jockers_data": ("published", "ours"),
    "replication_jockers_pamr": ("published", "cv_line"),
    "replication_jockers": ("published_first_or_second_nsc", "summary"),
    "replication_ensc": ("published_method", "assigned"),
}


def records() -> dict[str, tuple[str, dict[str, list[tuple[str, bool]]]]]:
    """method -> (test set, {task: [(true author, correct)]})."""
    out: dict[str, tuple[str, dict]] = {}
    b = json.loads((DIR / "benchmark.json").read_text())
    for m in CLASSIC:
        out[m] = ("trials", {t: [(r["author"], r[m] == r["author"]) for r in rs]
                             for t, rs in b["records"].items()})  # fmt: skip
    ct = DIR / "prior_work_classic_tails.json"
    if ct.exists():  # the classical methods on the language models' own tests
        d = json.loads(ct.read_text())
        for m in (*CLASSIC, "ensc"):
            out[f"tails_{m}"] = ("tails", {t: [(r["author"], r[m] == r["author"]) for r in rs]
                                           for t, rs in d["records"].items()})  # fmt: skip
    for f in sorted(DIR.glob("alm_*.json")) + [DIR / "style_embed.json"]:
        if not f.exists() or "candidates" in f.stem:
            continue
        d = json.loads(f.read_text())
        if "records" not in d:
            continue
        tails = any("where" in r for rs in d["records"].values() for r in rs)
        out[f.stem] = ("tails" if tails else "trials",
                       {t: [(r["author"], r["predicted"] == r["author"]) for r in rs]
                        for t, rs in d["records"].items()})  # fmt: skip
    return out


def bootstrap(correct: np.ndarray, n: int, seed: int) -> list[float]:
    """95% percentile interval of accuracy, resampling tests."""
    rng = np.random.default_rng(seed)
    acc = correct[rng.integers(0, len(correct), size=(n, len(correct)))].mean(axis=1)
    return [float(np.percentile(acc, 2.5)), float(np.percentile(acc, 97.5))]


def mcnemar(a: np.ndarray, b: np.ndarray) -> dict:
    """Exact McNemar test on paired correctness: tests only a got right, only b got right, p."""
    from scipy.stats import binomtest

    only_a, only_b = int((a & ~b).sum()), int((~a & b).sum())
    p = binomtest(only_a, only_a + only_b, 0.5).pvalue if only_a + only_b else 1.0
    return {"only_first": only_a, "only_second": only_b, "p": float(p)}


def _flat(by_task: dict[str, list[tuple[str, bool]]]) -> tuple[list[str], np.ndarray]:
    keys = [f"{t}:{i}:{a}" for t in sorted(by_task) for i, (a, _) in enumerate(by_task[t])]
    return keys, np.array([c for t in sorted(by_task) for _, c in by_task[t]], dtype=bool)


SIZES = ("pilot", "base", "mid")  # the 1B was dropped for a 590M (Amendment 39)


def size_of(method: str) -> tuple[str, str] | None:
    """(size, variant) of a time-locked model's result (``alm_<size>[_<variant>]``), else None."""
    parts = method.split("_")
    if len(parts) < 2 or parts[0] != "alm" or parts[1] not in SIZES:
        return None
    return parts[1], "_".join(parts[2:]) or "primary"


def by_size(rows: dict[str, dict]) -> dict[str, dict[str, dict]]:
    """Every size side by side (owner, 2026-11-06: no headline size): variant -> size ->
    closed-set accuracy, its interval and the false-match rate."""
    out: dict[str, dict[str, dict]] = {}
    for m, r in rows.items():
        sv = size_of(m)
        if sv:
            out.setdefault(sv[1], {})[sv[0]] = {
                "closed_set": r["closed_set"], "closed_set_95": r["closed_set_95"],
                "open_set_fpr": r["open_set_fpr"], "passes": r["passes"],
                "test_set": r["test_set"]}  # fmt: skip
    return {v: {z: out[v][z] for z in SIZES if z in out[v]} for v in sorted(out)}


def table() -> int:
    cfg = load_config()
    pw = cfg["prior_work"]
    recs = records()
    open_set = json.loads((DIR / "open_set.json").read_text())["methods"]
    b = json.loads((DIR / "benchmark.json").read_text())
    rows = {}
    ct = DIR / "prior_work_classic_tails.json"
    tails = json.loads(ct.read_text())["summary"] if ct.exists() else {}
    for m, (tset, by_task) in recs.items():
        keys, c = _flat(by_task)
        v = (
            tails.get(m.removeprefix("tails_"), {})
            if m.startswith("tails_")
            else open_set.get(m, {})
        )
        rows[m] = {"test_set": tset, "tests": len(c), "closed_set": float(c.mean()),
                   "closed_set_95": bootstrap(c, pw["bootstrap"],
                                              derive_seed(f"{pw['bootstrap_seed']}:{m}", cfg)),
                   "by_task": {t: float(np.mean([x for _, x in rs])) for t, rs in by_task.items()},
                   "open_set_fpr": v.get("open_set_fpr"), "passes": v.get("passes")}  # fmt: skip
    # ENSC has no per-test record in benchmark.json: aggregate numbers only
    rows["ensc"] = {"test_set": "trials", "tests": open_set["ensc"].get("tests"),
                    "closed_set": open_set["ensc"]["closed_set"], "closed_set_95": None,
                    "by_task": b.get("ensc_closed_set_by_task"),
                    "open_set_fpr": open_set["ensc"].get("open_set_fpr"),
                    "passes": open_set["ensc"].get("passes")}  # fmt: skip
    paired = {}
    for m1, m2 in combinations(sorted(recs), 2):
        if recs[m1][0] != recs[m2][0]:
            continue
        k1, c1 = _flat(recs[m1][1])
        k2, c2 = _flat(recs[m2][1])
        if k1 != k2:  # not the same tests in the same order: not paired
            continue
        paired[f"{m1} vs {m2}"] = mcnemar(c1, c2)
    published = {}
    for f, (pk, ok) in REPLICATIONS.items():
        p = DIR / f"{f}.json"
        if p.exists():
            d = json.loads(p.read_text())
            published[f] = {"published": d.get(pk), "ours": d.get(ok)}
    doc = {**stamp(), "methods": rows, "by_size": by_size(rows), "paired": paired,
           "published_vs_ours": published,
           "sets": {"trials": "BOM-21's trials (classical, style embeddings, V3)",
                    "tails": "Amendment 22's held-out tails (fine-tuned models)"}}  # fmt: skip
    out = DIR / "prior_work.json"
    out.write_text(json.dumps(doc, indent=1) + "\n")
    for m, r in sorted(rows.items(), key=lambda kv: (kv[1]["test_set"], kv[0])):
        ci = r["closed_set_95"]
        ci_s = f"[{ci[0]:.3f}, {ci[1]:.3f}]" if ci else "-"
        fpr = "-" if r["open_set_fpr"] is None else f"{r['open_set_fpr']:.3f}"
        print(f"  {r['test_set']:<6} {m:<18} n={r['tests'] or '-':<4} closed {r['closed_set']:.3f} "
              f"{ci_s:<17} FPR {fpr:<6} passes {r['passes']}")  # fmt: skip
    for v, sz in doc["by_size"].items():
        cells = [
            f"{z} {r['closed_set']:.3f}/FPR {r['open_set_fpr'] or 0:.3f}" for z, r in sz.items()
        ]
        print(f"  {v:<8} " + "  ".join(cells))
    sig = {k: v for k, v in paired.items() if v["p"] < 0.05}
    print(f"{len(paired)} paired comparisons, {len(sig)} at p < 0.05 -> {out}")
    return 0


def classic_tails() -> int:
    """The classical methods on Amendment 22's held-out tails (see the module docstring)."""
    import random

    from alm.benchmark import plan
    from classic.ensc import NONE
    from classic.features import tokenize
    from eval.benchmark import TASKS, _ensc_predict, imposter_pool, run_task
    from eval.open_set import verdict
    from eval.power import blocks
    from metadata.config import classic_kwargs

    cfg = load_config()
    spec = json.loads(TASKS.read_text())
    ens = json.loads((DIR / "benchmark.json").read_text())["ensc"]  # its calibrated settings
    priors = classic_kwargs(cfg)["ensc"]["priors"]
    rng = random.Random(derive_seed("bom68-classic-tails", cfg))
    recs_by: dict[str, list[dict]] = {}
    for name, tp in plan(cfg).items():
        sp = spec[name]
        task = {"authors": {a: blocks(tokenize(" ".join(w for ws in works for w in ws)))
                            for a, works in tp["train"].items()},
                "tests": [(x["author"], tokenize(" ".join(x["words"])), None)
                          for x in tp["tests"]]}  # fmt: skip
        pool = imposter_pool(sp["imposter_pool"], set(sp.get("exclude_from_pool", [])), cfg,
                             sp.get("imposter_genre"), tuple(sp.get("exclude_authors_from_pool",
                                                                    [])),
                             sp.get("imposter_fill"))  # fmt: skip
        out = []
        for x, r in zip(tp["tests"], run_task(task, pool, cfg, rng, progress=name), strict=True):
            closed = _ensc_predict(r, ens["shrinkage"], ens["alpha"], priors, None)
            opened = _ensc_predict(r, ens["shrinkage"], ens["alpha"], priors, r["author"])
            out.append({"author": r["author"], "where": x["where"],
                        **{m: r[m] for m in CLASSIC}, "ensc": closed,
                        "ensc_open_false_match": opened not in (None, NONE),
                        "gi_positive": r["gi_positive"],
                        "gi_open_negative": r["gi_open_negative"]})  # fmt: skip
        recs_by[name] = out
        print(f"  {name}: {len(out)} tests", flush=True)
    recs = [r for rs in recs_by.values() for r in rs]
    n = len(recs)
    summary = {m: {"closed_set": sum(r[m] == r["author"] for r in recs) / n} for m in CLASSIC}
    fold = derive_seed("bom68-classic-tails-gi-fold", cfg)
    summary["general_imposters"] = verdict(summary["general_imposters"]["closed_set"],
                                           [r["gi_positive"] for r in recs],
                                           [r["gi_open_negative"] for r in recs], cfg,
                                           fold)  # fmt: skip
    fm = sum(r["ensc_open_false_match"] for r in recs) / n
    summary["ensc"] = {"closed_set": sum(r["ensc"] == r["author"] for r in recs) / n,
                       "open_set_fpr": fm,
                       "passes": (sum(r["ensc"] == r["author"] for r in recs) / n
                                  >= cfg["benchmark"]["pass_closed_set"]
                                  and fm <= cfg["benchmark"]["max_open_set_fpr"])}  # fmt: skip
    path = DIR / "prior_work_classic_tails.json"
    path.write_text(json.dumps({**stamp(), "tests": n, "ensc_settings": {
        "shrinkage": ens["shrinkage"], "alpha": ens["alpha"]}, "summary": summary,
        "records": recs_by}, indent=1) + "\n")  # fmt: skip
    for m, v in summary.items():
        fpr = v.get("open_set_fpr")
        print(f"  tails {m:<18} closed {v['closed_set']:.3f}"
              + ("" if fpr is None else f"  FPR {fpr:.3f}"))  # fmt: skip
    print(f"{n} held-out tests -> {path}")
    return 0


def ablation_files() -> int:
    """Every repository file ``ablation`` reads (the benchmark texts and masks), one per line, for
    a pod upload (``scripts/pod_jobs.py --files``)."""
    import pyarrow.parquet as pq

    from alm.benchmark import FEDERALIST, PSEUDO, SPANS, TASKS
    from ocr_fix.normalize import norm_path

    spec = json.loads(PSEUDO.read_text())["authors"]
    d = json.loads(TASKS.read_text())["dictated"]
    ids = {w for a in spec.values() for w in a["works"]}
    ids |= {w for ws in d["reference"].values() for w in ws} | set(d["tests"])
    cols = ["work_id", "source", "text_path"]
    rows = [r for r in pq.read_table("data/catalog/catalog.parquet", columns=cols).to_pylist()
            if r["work_id"] in ids]  # fmt: skip
    files = {
        str(FEDERALIST),
        str(PSEUDO),
        str(TASKS),
        str(SPANS),
        "data/kjv_mask/controls/spans.jsonl",
        "data/kjv_mask/known_answer/spans.jsonl",
    }
    files |= {str(norm_path(r)) for r in rows}
    for f in sorted(files):
        p = Path(f)
        if not p.exists() and p.with_suffix(".jsonl.gz").exists():
            f = str(p.with_suffix(".jsonl.gz"))
        print(f)
    return 0


def hf_causal_lm(name: str, revision: str):
    """A Hugging Face GPT-2 behind the time-locked GPT's interface: ``model(idx)`` gives logits,
    ``model(idx, targets)`` the mean token cross-entropy, as ``alm.benchmark`` expects."""
    import torch
    import torch.nn.functional as F
    from transformers import GPT2LMHeadModel

    class Wrapped(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.m = GPT2LMHeadModel.from_pretrained(name, revision=revision)
            self.commit = getattr(self.m.config, "_commit_hash", None)

        def forward(self, idx, targets=None):
            logits = self.m(idx).logits
            if targets is None:
                return logits
            return F.cross_entropy(logits.flatten(0, 1).float(), targets.flatten())

    return Wrapped()


def ablation(name: str, micro: int) -> int:
    """Amendment 22's ALMs with GPT-2 as the base (Amendment 36); benchmark only."""
    import torch
    from transformers import GPT2TokenizerFast

    from alm.benchmark import WORK, _device, finetune, plan, score, window_loss

    cfg = load_config()
    a, pw = cfg["alm"], cfg["prior_work"]
    if name not in pw["gpt2_models"]:
        raise SystemExit(f"{name} is not one of prior_work.gpt2_models {pw['gpt2_models']}")
    dev = _device()
    tok = GPT2TokenizerFast.from_pretrained(name, revision=pw["gpt2_revision"])
    tag = name.replace("-", "_")
    work = WORK / tag
    work.mkdir(parents=True, exist_ok=True)
    p = plan(cfg)
    base = hf_causal_lm(name, pw["gpt2_revision"]).to(dev).eval()
    state = {k: v.clone() for k, v in base.state_dict().items()}

    def enc(words: list[str]) -> list[int]:
        return tok(" ".join(words))["input_ids"]

    for task, tp in p.items():
        for x in tp["tests"]:
            x["ids"] = enc(x["words"])
        path = work / f"{task}__base.json"
        if not path.exists():
            path.write_text(json.dumps([window_loss(base, x["ids"], a["score_window"], dev)
                                        for x in tp["tests"]]))  # fmt: skip
    for task, tp in p.items():
        for author, works in tp["train"].items():
            path = work / f"{task}__{author}.json"
            if path.exists():
                continue
            ids = np.array([i for ws in works for i in [*enc(ws), tok.eos_token_id]],
                           dtype=np.int32)  # fmt: skip
            base.load_state_dict(state)
            seed = derive_seed(f"{a['train_seed']}:{task}:{author}", cfg)
            torch.manual_seed(seed)
            info = finetune(base, ids, cfg, seed, micro, dev, cfg["timelocked_lm"]["finetune_lr"])
            losses = [window_loss(base, x["ids"], a["score_window"], dev) for x in tp["tests"]]
            path.write_text(json.dumps({"train_tokens": len(ids), **info, "losses": losses,
                                        "hf_commit": base.commit}))  # fmt: skip
            print(f"  {tag} {task} {author}: {len(ids):,} tokens", flush=True)
    return score(tag, p, cfg)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["table", "classic-tails", "ablation", "files"])
    ap.add_argument("model", nargs="?", default="gpt2")
    ap.add_argument("--micro-batch", type=int, default=8, help="memory only; same update")
    a = ap.parse_args(argv)
    return {"table": table, "classic-tails": classic_tails, "files": ablation_files,
            "ablation": lambda: ablation(a.model, a.micro_batch)}[a.cmd]()  # fmt: skip


if __name__ == "__main__":
    sys.exit(main())
