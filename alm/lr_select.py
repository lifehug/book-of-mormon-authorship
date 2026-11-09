"""Choose each size's V1 and V2 learning rate on held-out training text (Amendment 41, BOM-28).

Post hoc, 2026-11-09: at 590M, V1 (Amendment 22 at ten times the learning rate) raised the
fine-tuned models' loss on new text by 0.81 nats and fell to 63% closed-set accuracy, and V2
(classifier head) to 76%: rates registered for the 297M did not carry to a larger model. Here
each rate in ``alm.lr_select_grid`` is tried on the benchmark authors' *training* text only, the
tail ``alm.lr_select_val_share`` of each author's training tokens (V1) or windows (V2) held out;
the rate with the lowest held-out loss is chosen. The 110 benchmark tests are never read. The
reruns at the chosen rates (``alm_<size>_v1_lrsel``, ``alm_<size>_v2_lrsel``) are reported beside
the registered runs, never instead of them.

- **V1:** per author, fine-tune Amendment 22's way on the first 90% of the training tokens;
  score = mean token log-loss on the last 10% (``score_window`` windows). Rate score = the mean
  over all authors of all tasks.
- **V2:** per task, train the head and model on the first 90% of each author's windows; score =
  the class-weighted cross-entropy on the last 10%. Rate score = the mean over tasks, weighted by
  held-out windows.

Writes ``data/benchmark/lr_select_<size>.json`` (every rate's score and the chosen one).

Usage::

    python -m alm.lr_select <size> [--micro-batch 8]   # then the reruns at the chosen rates
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from alm.benchmark import OUT, _base, _device, _encode, finetune, plan, window_loss
from alm.variants import hidden
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from timelocked_lm.release import EOT, TOKENIZER


def split(n: int, share: float) -> int:
    """The index where the held-out tail starts (at least one item held out)."""
    return max(1, n - max(1, round(n * share)))


def v1_score(size: str, lr: float, micro: int, cfg: dict, p: dict, tok, dev: str) -> dict:
    a = cfg["alm"]
    eot = tok.token_to_id(EOT)
    base = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in base.state_dict().items()}
    per = {}
    for task, tp in p.items():
        for author, works in tp["train"].items():
            ids = np.array([i for ws in works for i in [*_encode(tok, ws), eot]], dtype=np.int32)
            cut = split(len(ids), a["lr_select_val_share"])
            base.load_state_dict(state)
            seed = derive_seed(f"{a['train_seed']}:lrsel:{task}:{author}", cfg)
            torch.manual_seed(seed)
            finetune(base, ids[:cut], cfg, seed, micro, dev, lr)
            held = window_loss(base, ids[cut:].tolist(), a["score_window"], dev)
            per[f"{task}:{author}"] = float(np.mean(held)) if held else None
    vals = [v for v in per.values() if v is not None]
    return {"score": float(np.mean(vals)), "per_author": per}


def v2_score(size: str, lr: float, micro: int, cfg: dict, p: dict, tok, dev: str) -> dict:
    a, t = cfg["alm"], cfg["timelocked_lm"]
    w, eot = a["v2_head_window"], tok.token_to_id(EOT)
    per, total, n_all = {}, 0.0, 0
    for task, tp in p.items():
        authors = sorted(tp["train"])
        tr_x, tr_y, va_x, va_y = [], [], [], []
        for k, b in enumerate(authors):
            ids = [i for ws in tp["train"][b] for i in [*_encode(tok, ws), eot]]
            wins = [ids[j * w : (j + 1) * w] for j in range(len(ids) // w)]
            cut = split(len(wins), a["lr_select_val_share"])
            tr_x += wins[:cut]
            tr_y += [k] * cut
            va_x += wins[cut:]
            va_y += [k] * (len(wins) - cut)
        X, y = torch.tensor(tr_x), torch.tensor(tr_y)
        counts = torch.bincount(y, minlength=len(authors)).float()
        weight = (counts.sum() / (len(authors) * counts.clamp(min=1))).to(dev)
        seed = derive_seed(f"{a['train_seed']}:lrsel:v2:{task}", cfg)
        torch.manual_seed(seed)
        model = _base(size, cfg).to(dev)
        head = nn.Linear(model.ln.weight.shape[0], len(authors)).to(dev)
        params = [*model.parameters(), *head.parameters()]
        opt = torch.optim.AdamW(params, lr=lr, betas=tuple(t["adam_betas"]),
                                weight_decay=t["weight_decay"])  # fmt: skip
        rng = np.random.default_rng(seed)
        model.train()
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
        model.eval()
        losses = []
        with torch.no_grad():
            for i in range(0, len(va_x), 16):
                xb = torch.tensor(va_x[i : i + 16]).to(dev)
                yb = torch.tensor(va_y[i : i + 16]).to(dev)
                logits = head(hidden(model, xb).mean(dim=1))
                losses += F.cross_entropy(logits, yb, weight=weight, reduction="none").tolist()
        per[task] = float(np.mean(losses))
        total += float(np.sum(losses))
        n_all += len(losses)
        del model, head, opt
        if dev.startswith("cuda"):
            torch.cuda.empty_cache()
    return {"score": total / n_all, "per_task": per}


def run(size: str, micro: int) -> int:
    from tokenizers import Tokenizer

    cfg = load_config()
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    p = plan(cfg)
    out = OUT / f"lr_select_{size}.json"
    doc = json.loads(out.read_text()) if out.exists() else {"v1": {}, "v2": {}}  # resumes
    for variant, fn in (("v1", v1_score), ("v2", v2_score)):
        for lr in cfg["alm"]["lr_select_grid"]:
            if str(lr) in doc[variant]:
                continue
            doc[variant][str(lr)] = fn(size, lr, micro, cfg, p, tok, dev)
            out.write_text(json.dumps({**doc, **stamp()}, indent=1) + "\n")
            print(f"  {size} {variant} lr {lr:g}: held-out {doc[variant][str(lr)]['score']:.4f}",
                  flush=True)  # fmt: skip
        doc[f"{variant}_chosen"] = float(min(doc[variant], key=lambda r: doc[variant][r]["score"]))
    out.write_text(json.dumps({**doc, **stamp(), "size": size}, indent=1) + "\n")
    print(f"{size}: V1 {doc['v1_chosen']:g}, V2 {doc['v2_chosen']:g} -> {out}", flush=True)
    return 0


def chosen(size: str) -> tuple[float, float]:
    d = json.loads((OUT / f"lr_select_{size}.json").read_text())
    return d["v1_chosen"], d["v2_chosen"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("size", choices=["pilot", "base", "mid", "large"])
    ap.add_argument("--micro-batch", type=int, default=2, help="memory only; same update")
    ap.add_argument("--print", action="store_true", help="print the chosen rates: v1 v2")
    a = ap.parse_args(argv)
    if a.print:
        print(*chosen(a.size))
        return 0
    return run(a.size, a.micro_batch)


if __name__ == "__main__":
    sys.exit(main())
