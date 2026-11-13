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

``classic-tails [--part2]`` runs the classical methods (Burrows and Cosine Delta, General Imposters,
ENSC at the benchmark's calibrated shrinkage and alpha; registered settings, as
``eval.benchmark.run_task``) on Amendment 22's held-out tails, the very tests the fine-tuned
language models are scored on: references are each author's training words, the tests its held-out
windows in the same order, so ``table`` pairs them with the language models test by test. With
``--part2`` (Amendment 52) the same is done on the enlarged benchmark's 430 held-out tails (BOM-75),
the tests the ``alm_*_p2`` models took, and ``table`` adds the registered head-to-head: every size
against every classical method, exact McNemar, Holm-corrected over those comparisons
(``prior_work.head_to_head``).

``ablation`` (designed; run on a GPU) repeats Amendment 22's ALM pipeline with an off-the-shelf
GPT-2 in place of the time-locked base, on the benchmark only: GPT-2 read modern web text, which
may include the Book of Mormon, so it is never applied to it. It writes ``alm_gpt2*.json`` in the
ALM format, so ``eval.open_set rescore`` and ``table`` pick it up.

Usage::

    python -m eval.prior_work table                   # -> data/benchmark/prior_work.json
    python -m eval.prior_work classic-tails           # -> prior_work_classic_tails.json
    python -m eval.prior_work classic-tails --part2   # -> prior_work_classic_tails_p2.json
    python -m eval.prior_work classic-tails --ext     # Amendment 56 -> ..._tails_p3.json
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
P2_TAILS = "prior_work_classic_tails_p2.json"
P3_TAILS = "prior_work_classic_tails_p3.json"  # Amendment 56's eight new tasks
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
    for ct, pre, tset in (
        (DIR / "prior_work_classic_tails.json", "tails_", "tails"),
        (DIR / P2_TAILS, "tails_p2_", "tails_p2"),
    ):
        if ct.exists():  # the classical methods on the language models' own tests
            d = json.loads(ct.read_text())
            for m in (*CLASSIC, "ensc"):
                out[f"{pre}{m}"] = (tset, {t: [(r["author"], r[m] == r["author"]) for r in rs]
                                           for t, rs in d["records"].items()})  # fmt: skip
    for f in sorted(DIR.glob("alm_*.json")) + sorted(DIR.glob("style_embed*.json")):
        if not f.exists() or "candidates" in f.stem:
            continue
        d = json.loads(f.read_text())
        if "records" not in d:
            continue
        tails = any("where" in r for rs in d["records"].values() for r in rs)
        tset = ("tails_p2" if f.stem.endswith("_p2") else "tails") if tails else "trials"
        out[f.stem] = (tset,
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


def head_to_head(recs: dict, cfg: dict) -> dict:
    """Amendment 52: every time-locked size against every classical method on BOM-75's 430
    held-out tails, exact McNemar (two-sided) on the tests only one got right, Holm-corrected over
    all these comparisons. "better" / "worse" needs the Holm p under ``alpha`` and more wins on
    that side; otherwise "no difference shown". Per task, the same counts, descriptive only."""
    hh = cfg["prior_work"]["head_to_head"]
    pairs = [(f"alm_{z}_p2", f"tails_p2_{m}") for z in SIZES for m in hh["methods"]]
    pairs = [(a, b) for a, b in pairs if a in recs and b in recs]
    if not pairs:
        return {}
    rows = []
    for a, b in pairs:
        ka, ca = _flat(recs[a][1])
        kb, cb = _flat(recs[b][1])
        if ka != kb:
            raise SystemExit(f"{a} and {b} are not the same tests in the same order")
        r = mcnemar(ca, cb)
        tasks = {t: mcnemar(np.array([c for _, c in recs[a][1][t]], dtype=bool),
                            np.array([c for _, c in recs[b][1][t]], dtype=bool))
                 for t in sorted(recs[a][1])}  # fmt: skip
        rows.append({"ours": a, "theirs": b.removeprefix("tails_p2_"), "tests": len(ca),
                     "ours_right": int(ca.sum()), "theirs_right": int(cb.sum()),
                     "ours_only": r["only_first"], "theirs_only": r["only_second"], "p": r["p"],
                     "by_task": {t: {"ours_only": v["only_first"], "theirs_only": v["only_second"]}
                                 for t, v in tasks.items()}})  # fmt: skip
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p"])  # Holm step-down
    running = 0.0
    for k, i in enumerate(order):
        running = max(running, min(1.0, (len(rows) - k) * rows[i]["p"]))
        rows[i]["p_holm"] = running
    for r in rows:
        sig = r["p_holm"] < hh["alpha"]
        r["reading"] = ("no difference shown" if not sig or r["ours_only"] == r["theirs_only"]
                        else "ours better" if r["ours_only"] > r["theirs_only"]
                        else "theirs better")  # fmt: skip
    return {"rule": "Amendment 52", "alpha": hh["alpha"], "correction": "holm", "comparisons": rows}


def table() -> int:
    cfg = load_config()
    pw = cfg["prior_work"]
    recs = records()
    open_set = json.loads((DIR / "open_set.json").read_text())["methods"]
    b = json.loads((DIR / "benchmark.json").read_text())
    rows = {}
    ct, ct2 = DIR / "prior_work_classic_tails.json", DIR / P2_TAILS
    tails = json.loads(ct.read_text())["summary"] if ct.exists() else {}
    tails_p2 = json.loads(ct2.read_text())["summary"] if ct2.exists() else {}
    for m, (tset, by_task) in recs.items():
        keys, c = _flat(by_task)
        if m.startswith("tails_p2_"):
            v = tails_p2.get(m.removeprefix("tails_p2_"), {})
        elif m.startswith("tails_"):
            v = tails.get(m.removeprefix("tails_"), {})
        else:
            v = open_set.get(m, {})
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
           "head_to_head_p2": head_to_head(recs, cfg),
           "published_vs_ours": published,
           "sets": {"trials": "BOM-21's trials (classical, style embeddings, V3)",
                    "tails": "Amendment 22's held-out tails (fine-tuned models)",
                    "tails_p2": "BOM-75's 430 held-out tails (Amendment 52)"}}  # fmt: skip
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
    for c in doc["head_to_head_p2"].get("comparisons", []):
        print(f"  A52 {c['ours']} vs {c['theirs']}: {c['ours_only']}-{c['theirs_only']} "
              f"p {c['p']:.4f} Holm {c['p_holm']:.4f} -> {c['reading']}")  # fmt: skip
    sig = {k: v for k, v in paired.items() if v["p"] < 0.05}
    print(f"{len(paired)} paired comparisons, {len(sig)} at p < 0.05 -> {out}")
    return 0


def classic_tails(part2: bool = False, ext: bool = False) -> int:
    """The classical methods on Amendment 22's held-out tails, or with ``part2`` on BOM-75's
    (Amendment 52; see the module docstring)."""
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
    bench = DIR / "part2" / "benchmark.json" if part2 or ext else DIR / "benchmark.json"
    ens = json.loads(bench.read_text())["ensc"]  # its calibrated settings
    priors = classic_kwargs(cfg)["ensc"]["priors"]
    tag = "bom68-classic-tails" + ("-p3" if ext else "-p2" if part2 else "")
    rng = random.Random(derive_seed(tag, cfg))
    recs_by: dict[str, list[dict]] = {}
    for name, tp in plan(cfg, part2, ext).items():
        task = {"authors": {a: blocks(tokenize(" ".join(w for ws in works for w in ws)))
                            for a, works in tp["train"].items()},
                "tests": [(x["author"], tokenize(" ".join(x["words"])), None)
                          for x in tp["tests"]]}  # fmt: skip
        if name.startswith(("p2_", "p3_")):  # Amendment 48's registered pairings by genre
            g = name.removeprefix("p2_") if name.startswith("p2_") else name[3:].rsplit("_", 1)[0]
            pool_set, pool_genre = cfg["part2_benchmark"]["pools"][g]
            pool = imposter_pool(pool_set, set(), cfg, pool_genre, tuple(sorted(tp["train"])))
        else:
            sp = spec[name]
            pool = imposter_pool(sp["imposter_pool"], set(sp.get("exclude_from_pool", [])), cfg,
                                 sp.get("imposter_genre"),
                                 tuple(sp.get("exclude_authors_from_pool", [])),
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
    fold = derive_seed(f"{tag}-gi-fold", cfg)
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
    path = DIR / (P3_TAILS if ext else P2_TAILS if part2 else "prior_work_classic_tails.json")
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
    ap.add_argument("--part2", action="store_true", help="classic-tails on BOM-75's tests")
    ap.add_argument("--ext", action="store_true", help="classic-tails on Amendment 56's tests")
    a = ap.parse_args(argv)
    return {"table": table, "classic-tails": lambda: classic_tails(a.part2, a.ext),
            "files": ablation_files,
            "ablation": lambda: ablation(a.model, a.micro_batch)}[a.cmd]()  # fmt: skip


if __name__ == "__main__":
    sys.exit(main())
