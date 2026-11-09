"""Amendment 23's secondary uses of the time-locked model on the validation benchmark (BOM-28).

V1 (stronger fine-tuning) is ``alm.benchmark --variant v1``. Here:

* **v2**, a classifier head: per task, one copy of the base model with a linear head over the
  task's authors on the mean final hidden state of a ``alm.v2_head_window``-token window, trained
  on Amendment 22's training text (3 epochs, ``timelocked_lm.finetune_lr``, classes weighted by
  inverse window counts); a test's score for an author is the mean over its windows of that
  author's log-probability.
* **v3**, hidden-state features: the unchanged base model maps each 1,000-word block of the
  benchmark's own trials (BOM-21's tasks, tests and imposter pools) to the mean of its final hidden
  states; cosine nearest centroid for the closed set, General Imposters with the registered
  settings for verification.

Both are judged by ``alm.benchmark.decide`` (Amendment 22's rule). Usage::

    python -m alm.variants v2|v3 <size>   # pilot|base|mid|large -> alm_<size>_<variant>.json
    python -m alm.variants v2 <size> --lr 3e-6 --tag <size>_v2_lrsel --save-weights
    python -m alm.variants v2 <size> --seed-index 1 --tag <size>_v2_seed1 --save-weights

``--seed-index k`` (Amendment 42) reruns V2 with a different seed for every task, to measure how
much its result moves between runs; 0 is the registered seed.
"""

from __future__ import annotations

import argparse
import json
import random
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from alm.benchmark import WORK, _base, _device, _encode, plan, write
from metadata.config import derive_seed
from metadata.config import load as load_config
from timelocked_lm.release import EOT, TOKENIZER
from timelocked_lm.train import GPT


def hidden(model: GPT, idx: torch.Tensor) -> torch.Tensor:
    """Final (normalised) hidden states, batch x tokens x width."""
    x = model.tok(idx) + model.pos(torch.arange(idx.shape[1], device=idx.device))
    for blk in model.blocks:
        x = blk(x)
    return model.ln(x)


def _windows(ids: list[int], w: int) -> torch.Tensor:
    n = max(1, len(ids) // w)
    ids = ids[: n * w] if len(ids) >= w else ids
    return torch.tensor(ids, dtype=torch.long).view(n, -1)


def v2(size: str, micro: int, lr: float | None = None, tag: str | None = None,
       save: bool = False, seed_index: int = 0) -> int:  # fmt: skip
    from tokenizers import Tokenizer

    cfg = load_config()
    a, t = cfg["alm"], cfg["timelocked_lm"]
    w = a["v2_head_window"]
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    lr = lr if lr is not None else t["finetune_lr"]
    tag = tag or f"{size}_v2"
    work = WORK / tag
    work.mkdir(parents=True, exist_ok=True)
    recs_by = {}
    for task, tp in plan(cfg).items():
        path = work / f"{task}.json"
        if path.exists():
            recs_by[task] = json.loads(path.read_text())
            continue
        authors = sorted(tp["train"])
        xs, ys = [], []
        for k, b in enumerate(authors):
            ids = [i for ws in tp["train"][b] for i in [*_encode(tok, ws), eot]]
            n = len(ids) // w
            xs += [ids[j * w : (j + 1) * w] for j in range(n)]
            ys += [k] * n
        X, y = torch.tensor(xs), torch.tensor(ys)
        counts = torch.bincount(y, minlength=len(authors)).float()
        weight = (counts.sum() / (len(authors) * counts)).to(dev)
        seed = derive_seed(f"{a['train_seed']}:v2:{task}" + (f":s{seed_index}" if seed_index
                                                              else ""), cfg)  # fmt: skip
        torch.manual_seed(seed)
        model = _base(size, cfg).to(dev)
        head = nn.Linear(model.ln.weight.shape[0], len(authors)).to(dev)
        params = [*model.parameters(), *head.parameters()]
        opt = torch.optim.AdamW(params, lr=lr, betas=tuple(t["adam_betas"]),
                                weight_decay=t["weight_decay"])  # fmt: skip
        rng = np.random.default_rng(seed)
        model.train()
        steps = 0
        for _ in range(t["finetune_epochs"]):
            order = rng.permutation(len(X))
            for i in range(0, len(order), a["batch"]):
                bi = order[i : i + a["batch"]]
                for j in range(0, len(bi), micro):
                    mb = torch.from_numpy(bi[j : j + micro])
                    logits = head(hidden(model, X[mb].to(dev)).mean(dim=1))
                    loss = F.cross_entropy(logits, y[mb].to(dev), weight=weight)
                    (loss * len(mb) / len(bi)).backward()
                torch.nn.utils.clip_grad_norm_(params, t["grad_clip"])
                opt.step()
                opt.zero_grad(set_to_none=True)
                steps += 1
        model.eval()
        if save:
            (work / "weights").mkdir(exist_ok=True)
            torch.save({"model": model.state_dict(), "head": head.state_dict(), "authors": authors,
                        "lr": lr, "seed": seed}, work / "weights" / f"{task}.pt")  # fmt: skip
        recs = []
        with torch.no_grad():
            for x in tp["tests"]:
                win = _windows(_encode(tok, x["words"]), w).to(dev)
                lp = F.log_softmax(head(hidden(model, win).mean(dim=1)), dim=-1).mean(dim=0)
                sc = dict(zip(authors, lp.tolist(), strict=True))
                others = [b for b in authors if b != x["author"]]
                recs.append({"author": x["author"], "where": x["where"], "windows": len(win),
                             "scores": sc, "predicted": max(sc, key=lambda b: (sc[b], b)),
                             "positive": sc[x["author"]],
                             "open_negative": max(sc[b] for b in others)})  # fmt: skip
        path.write_text(json.dumps(recs))
        recs_by[task] = recs
        print(f"  {size}_v2 {task}: {len(X):,} windows, {steps} steps", flush=True)
    return write(tag, recs_by, cfg, {"variant": "v2", "lr": lr, "seed_index": seed_index})


def v3(size: str) -> int:
    from tokenizers import Tokenizer

    from classic import general_imposters
    from classic.delta import cosine_delta
    from eval.benchmark import TASKS, imposter_pool, load_tasks
    from eval.power import blocks
    from metadata.config import classic_kwargs

    cfg = load_config()
    w = cfg["alm"]["score_window"]
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    model = _base(size, cfg).to(dev).eval()

    @torch.no_grad()
    def vec(words: list[str]) -> np.ndarray:
        win = _windows(_encode(tok, words), w).to(dev)
        return hidden(model, win).mean(dim=1).mean(dim=0).float().cpu().numpy().astype(np.float64)

    def sample(words: list[str]) -> np.ndarray:
        return np.mean([vec(b) for b in blocks(words)], axis=0)

    kw = classic_kwargs(cfg)
    rng = random.Random(derive_seed("benchmark", cfg))
    spec = json.loads(TASKS.read_text())
    recs_by = {}
    for name, task in load_tasks(cfg).items():
        pool = imposter_pool(task["pool_set"], set(spec[name].get("exclude_from_pool", [])), cfg,
                             task["pool_genre"], task["pool_exclude_authors"],
                             spec[name].get("imposter_fill"))  # fmt: skip
        P = np.stack([sample(s) for s in pool])
        bv = {a: [vec(b) for b in bl] for a, bl in task["authors"].items()}
        names = sorted(task["authors"])
        per_trial = cfg["classic"]["imposters"]["per_trial"]
        gi_args = {**kw["imposters"], "n_imposters": min(len(P), per_trial)}
        recs = []
        for a, test, span in task["tests"]:
            x = np.mean(bv[a][span[0] : span[1]], axis=0) if span else sample(test)
            prof = {b: np.mean([v for i, v in enumerate(bv[b])
                                if not (b == a and span and span[0] <= i < span[1])], axis=0)
                    for b in names}  # fmt: skip
            dist = {b: cosine_delta(x, prof[b]) for b in names}
            gs = {b: general_imposters(x, prof[b], P, seed=rng.randrange(2**31), **gi_args)
                  for b in names}  # fmt: skip
            others = [b for b in names if b != a]
            recs.append({"author": a, "scores": dist, "gi": gs,
                         "predicted": min(dist, key=lambda b: (dist[b], b)),
                         "positive": gs[a],
                         "open_negative": max(gs[b] for b in others)})  # fmt: skip
        recs_by[name] = recs
        print(f"  {size}_v3 {name}: {len(recs)} tests, pool {len(P)}", flush=True)
    return write(f"{size}_v3", recs_by, cfg, {"variant": "v3"})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("variant", choices=["v2", "v3"])
    ap.add_argument("size", choices=["pilot", "base", "mid", "large"])
    ap.add_argument("--micro-batch", type=int, default=2, help="memory only; same update")
    ap.add_argument("--lr", type=float, help="v2: Amendment 41's selected learning rate")
    ap.add_argument("--tag", help="v2: result name; default <size>_v2")
    ap.add_argument("--save-weights", action="store_true", help="v2: keep each task's model")
    ap.add_argument("--seed-index", type=int, default=0, help="v2: Amendment 42's reruns")
    ap.add_argument("--seed-runs", action="store_true",
                    help="v2: seeds 1..alm.v2_seed_runs in turn, as <size>_v2_seed<k>")  # fmt: skip
    a = ap.parse_args(argv)
    if a.variant == "v2" and a.seed_runs:
        for k in range(1, load_config()["alm"]["v2_seed_runs"] + 1):
            v2(a.size, a.micro_batch, None, f"{a.size}_v2_seed{k}", a.save_weights, k)
        return 0
    if a.variant == "v2":
        return v2(a.size, a.micro_batch, a.lr, a.tag, a.save_weights, a.seed_index)
    return v3(a.size)


if __name__ == "__main__":
    sys.exit(main())
