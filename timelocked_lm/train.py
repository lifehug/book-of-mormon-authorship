"""Train the time-locked base model (BOM-27; pre-registration 5.2, Amendment 2).

A GPT-style decoder (pre-norm blocks, learned positions, tied embeddings, no biases) of the
registered shape (``timelocked_lm.pilot_shape`` / ``base_shape``), trained for one pass over the
encoded training split: the split is cut into ``context_length + 1``-token windows taken in a
seeded random order, every window once. AdamW, cosine schedule to ``min_lr_share`` of the peak,
``warmup_share`` linear warmup, ``batch_tokens`` per step, bf16 on CUDA.

Recoverable: a checkpoint (model, optimizer, step) is written every ``--checkpoint-minutes`` and
at the end, atomically; a rerun with the same arguments resumes from it, and the window order is
a pure function of the seed, so a resumed run sees exactly the windows an uninterrupted one would.
Validation loss on the held-out volumes every ``eval_every_steps`` goes to ``log.jsonl``.

Usage::

    python -m timelocked_lm.train pilot --out runs/pilot [--micro-batch 32]
    python -m timelocked_lm.train base --out runs/base
    python -m timelocked_lm.train tiny --out runs/tiny --max-steps 20   # a local smoke test
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

TOKENS = Path("data/corpus/timelocked_lm/tokens")
TINY = {"layers": 2, "width": 128, "heads": 4}


class Block(nn.Module):
    def __init__(self, width: int, heads: int, qk_norm: bool = False):
        super().__init__()
        self.heads = heads
        self.ln1 = nn.LayerNorm(width, bias=False)
        # QK-norm (optional; off for the 125M and 297M): layer-normalise each head's queries and
        # keys so attention logits cannot grow without bound, the usual cause of late loss spikes
        # at ~1B parameters (the 1B's run, 2026-11-06/07)
        self.qn = nn.LayerNorm(width // heads, bias=False) if qk_norm else None
        self.kn = nn.LayerNorm(width // heads, bias=False) if qk_norm else None
        self.qkv = nn.Linear(width, 3 * width, bias=False)
        self.proj = nn.Linear(width, width, bias=False)
        self.ln2 = nn.LayerNorm(width, bias=False)
        self.fc = nn.Linear(width, 4 * width, bias=False)
        self.out = nn.Linear(4 * width, width, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, c = x.shape
        q, k, v = self.qkv(self.ln1(x)).split(c, dim=2)
        q, k, v = (z.view(b, t, self.heads, c // self.heads).transpose(1, 2) for z in (q, k, v))
        if self.qn is not None:
            q, k = self.qn(q), self.kn(k)
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.proj(y.transpose(1, 2).reshape(b, t, c))
        return x + self.out(F.gelu(self.fc(self.ln2(x))))


class GPT(nn.Module):
    def __init__(self, vocab: int, context: int, layers: int, width: int, heads: int,
                 qk_norm: bool = False):  # fmt: skip
        super().__init__()
        self.tok = nn.Embedding(vocab, width)
        self.pos = nn.Embedding(context, width)
        self.blocks = nn.ModuleList(Block(width, heads, qk_norm) for _ in range(layers))
        self.ln = nn.LayerNorm(width, bias=False)
        self.head = nn.Linear(width, vocab, bias=False)
        self.head.weight = self.tok.weight  # tied
        self.apply(self._init)
        for n, p in self.named_parameters():  # GPT-2's scaled init of residual projections
            if n.endswith(("proj.weight", "out.weight")):
                nn.init.normal_(p, 0.0, 0.02 / math.sqrt(2 * layers))

    @staticmethod
    def _init(m: nn.Module) -> None:
        if isinstance(m, (nn.Linear, nn.Embedding)):
            nn.init.normal_(m.weight, 0.0, 0.02)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        x = self.tok(idx) + self.pos(torch.arange(idx.shape[1], device=idx.device))
        for blk in self.blocks:
            x = blk(x)
        logits = self.head(self.ln(x))
        if targets is None:
            return logits
        return F.cross_entropy(logits.flatten(0, 1).float(), targets.flatten())


def params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())


class Windows:
    """Every ``context + 1``-token window of a split, in a seeded order; window i of the order
    is fixed by the seed alone."""

    def __init__(self, split: str, context: int, seed: int):
        files = sorted(TOKENS.glob(f"{split}_*.bin"))
        if not files:
            raise SystemExit(f"no {split} tokens under {TOKENS}; run timelocked_lm.tokenize")
        self.maps = [np.memmap(f, dtype=np.uint16, mode="r") for f in files]
        self.n = context + 1
        counts = [len(m) // self.n for m in self.maps]
        self.starts = np.cumsum([0, *counts])
        self.order = np.random.default_rng(seed).permutation(int(self.starts[-1]))

    def __len__(self) -> int:
        return len(self.order)

    def batch(self, first: int, size: int) -> torch.Tensor:
        rows = []
        for w in self.order[first : first + size]:
            f = int(np.searchsorted(self.starts, w, side="right")) - 1
            j = (int(w) - int(self.starts[f])) * self.n
            rows.append(np.asarray(self.maps[f][j : j + self.n], dtype=np.int64))
        return torch.from_numpy(np.stack(rows))


def lr_at(step: int, steps: int, t: dict) -> float:
    warm = max(1, int(steps * t["warmup_share"]))
    if step < warm:
        return t["peak_lr"] * (step + 1) / warm
    p = (step - warm) / max(1, steps - warm)
    floor = t["peak_lr"] * t["min_lr_share"]
    return floor + 0.5 * (t["peak_lr"] - floor) * (1 + math.cos(math.pi * min(1.0, p)))


@torch.no_grad()
def evaluate(model, val: Windows, tokens: int, micro: int, device: str, ctx, rank: int = 0,
             world: int = 1) -> float:  # fmt: skip
    """Mean loss over the first ``tokens`` validation tokens; with several GPUs each takes every
    ``world``-th batch and the sums are combined."""
    model.eval()
    n = min(len(val), max(1, tokens // (val.n - 1)))
    total = torch.zeros(2, device=device)
    for i in range(rank * micro, n, world * micro):
        xy = val.batch(i, min(micro, n - i)).to(device)
        with ctx:
            loss = model(xy[:, :-1], xy[:, 1:]).float()
        total += torch.stack([loss, torch.ones((), device=device)])
    if world > 1:
        torch.distributed.all_reduce(total)
    model.train()
    return float(total[0] / total[1])


def _save(path: Path, state: dict) -> None:
    """Write atomically, keeping the previous checkpoint beside it: a loss spike can corrupt the
    run between two saves, and the 1B's only clean checkpoint was overwritten (2026-11-06)."""
    tmp = path.with_suffix(".tmp")
    torch.save(state, tmp)
    if path.exists():
        os.replace(path, path.with_name(path.stem + "_prev" + path.suffix))
    os.replace(tmp, path)


def train(size: str, out: Path, micro: int, max_steps: int | None, ckpt_minutes: float,
          lr_scale: float = 1.0, reset_optimizer: bool = False) -> int:  # fmt: skip
    cfg = load_config()
    t = cfg["timelocked_lm"]
    from tokenizers import Tokenizer

    vocab = Tokenizer.from_file("data/timelocked_lm/tokenizer.json").get_vocab_size()
    shape = {"pilot": t["pilot_shape"], "base": t["base_shape"], "tiny": TINY,
             "mid": t.get("mid_shape"), "large": t.get("large_shape")}[size]  # fmt: skip
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.mps.is_available() else "cpu"
    device = os.environ.get("TRAIN_DEVICE", device)  # smoke tests: force "cpu"
    # several GPUs under torchrun (Amendment 26): the same global batch and window order, split
    world, rank = int(os.environ.get("WORLD_SIZE", 1)), int(os.environ.get("RANK", 0))
    if world > 1:
        torch.distributed.init_process_group("nccl" if device == "cuda" else "gloo")
        if device == "cuda":
            device = f"cuda:{int(os.environ['LOCAL_RANK'])}"
            torch.cuda.set_device(device)
    lead = rank == 0
    torch.manual_seed(derive_seed(f"{t['train_seed']}:{size}", cfg) % 2**31)
    model = GPT(vocab, t["context_length"], **shape).to(device)
    # "cuda:N" under torchrun: a test of == "cuda" left the 1B's first run in fp32, 10x slower
    ctx = (torch.autocast("cuda", dtype=torch.bfloat16) if device.startswith("cuda")
           else torch.autocast("cpu", enabled=False))  # fmt: skip
    seq = t["context_length"]
    per_step = t["batch_tokens"] // seq if size != "tiny" else 8
    per_rank = per_step // world
    accum = max(1, per_rank // micro)
    # the smoke test trains on the validation split, so it can run before the full encode
    train_w = Windows(
        "validation" if size == "tiny" else "train",
        seq,
        derive_seed(f"{t['train_seed']}:order", cfg),
    )
    val = Windows("validation", seq, derive_seed(f"{t['train_seed']}:validation", cfg))
    steps = len(train_w) // per_step * t["epochs"]
    if max_steps:
        steps = min(steps, max_steps)
    decay = [p for p in model.parameters() if p.dim() >= 2]
    other = [p for p in model.parameters() if p.dim() < 2]
    opt = torch.optim.AdamW([{"params": decay, "weight_decay": t["weight_decay"]},
                             {"params": other, "weight_decay": 0.0}],
                            lr=t["peak_lr"], betas=tuple(t["adam_betas"]),
                            fused=device.startswith("cuda"))  # fmt: skip
    out.mkdir(parents=True, exist_ok=True)
    ck = out / "checkpoint.pt"
    step = 0
    if ck.exists():
        state = torch.load(ck, map_location=device)
        model.load_state_dict(state["model"])
        if reset_optimizer:  # recovery from a loss spike: fresh Adam moments
            print("optimizer state reset on resume", flush=True)
        else:
            opt.load_state_dict(state["optimizer"])
        step = state["step"]
        print(f"resumed at step {step:,}", flush=True)
    meta = {**stamp(), "size": size, "shape": shape, "params": params(model), "vocab": vocab,
            "steps": steps, "micro_batch": micro, "accum": accum, "seq": seq,
            "train_windows": len(train_w), "device": device, "gpus": world}  # fmt: skip
    if lead:
        (out / "run.json").write_text(json.dumps(meta, indent=1) + "\n")
        print(json.dumps({k: v for k, v in meta.items() if "sha" not in k}), flush=True)
    # several GPUs: no DistributedDataParallel. Each rank runs the compiled model as one GPU does
    # and the gradients are averaged once per step. DDP gives the same average, but with
    # torch.compile it ran 40 s a step on 2 H100s against 8.4 s on one (logs/large_pod/).
    fwd = torch.compile(model) if device.startswith("cuda") else model
    log = (out / "log.jsonl").open("a") if lead else None
    last_ck, t0 = time.time(), time.time()
    while step < steps:
        for g in opt.param_groups:
            g["lr"] = lr_at(step, steps, t) * lr_scale * t.get(f"{size}_lr_scale", 1.0)
        loss_sum = 0.0
        for a in range(accum):
            first = step * per_step + rank * per_rank + a * micro
            xy = train_w.batch(first, micro).to(device, non_blocking=True)
            with ctx:
                loss = fwd(xy[:, :-1], xy[:, 1:]) / accum
                loss.backward()
            loss_sum += loss.item()
        if world > 1:
            for p in model.parameters():
                if p.grad is not None:
                    torch.distributed.all_reduce(p.grad)
                    p.grad.div_(world)
            ls = torch.tensor(loss_sum, device=device)
            torch.distributed.all_reduce(ls)
            loss_sum = float(ls) / world
        norm = torch.nn.utils.clip_grad_norm_(model.parameters(), t["grad_clip"])
        opt.step()
        opt.zero_grad(set_to_none=True)
        step += 1
        rec = {"step": step, "loss": loss_sum, "lr": opt.param_groups[0]["lr"],
               "grad_norm": float(norm), "sec": round(time.time() - t0, 1)}  # fmt: skip
        if device.startswith("cuda"):
            rec["mem_gb"] = round(torch.cuda.max_memory_allocated() / 2**30, 1)
        if step % t["eval_every_steps"] == 0 or step == steps or (size == "tiny" and step % 5 == 0):
            rec["val_loss"] = evaluate(model, val, t["eval_tokens"] if size != "tiny" else 20000,
                                       micro, device, ctx, rank, world)  # fmt: skip
            if lead:
                print(json.dumps(rec), flush=True)
        if lead:
            log.write(json.dumps(rec) + "\n")
            log.flush()
        due = time.time() - last_ck > ckpt_minutes * 60 or step == steps
        if world > 1:  # every rank decides alike (rank 0's clock)
            flag = torch.tensor(int(due), device=device)
            torch.distributed.broadcast(flag, 0)
            due = bool(flag)
        if due:
            if lead:
                _save(ck, {"model": model.state_dict(), "optimizer": opt.state_dict(),
                           "step": step})  # fmt: skip
            last_ck = time.time()
    if lead:
        torch.save(model.state_dict(), out / "model.pt")
        print(f"done: {steps:,} steps -> {out / 'model.pt'}", flush=True)
    if world > 1:
        torch.distributed.barrier()
        torch.distributed.destroy_process_group()
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("size", choices=("pilot", "base", "mid", "large", "tiny"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--micro-batch", type=int, default=32, help="sequences per forward pass")
    ap.add_argument("--max-steps", type=int, default=None, help="smoke tests only")
    ap.add_argument("--checkpoint-minutes", type=float, default=20)
    ap.add_argument("--lr-scale", type=float, default=1.0, help="recovery only; documented if used")
    ap.add_argument("--reset-optimizer", action="store_true", help="recovery: fresh Adam state")
    a = ap.parse_args(argv)
    return train(
        a.size,
        a.out,
        a.micro_batch,
        a.max_steps,
        a.checkpoint_minutes,
        a.lr_scale,
        a.reset_optimizer,
    )


if __name__ == "__main__":
    sys.exit(main())
