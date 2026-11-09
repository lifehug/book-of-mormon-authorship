"""Train the style embeddings (BOM-30; pre-registration 5.4, Amendment 24).

Encoder: the time-locked base model (BOM-27); a passage's vector is the mean of its final hidden
states, an episode of ``style_embed.episode_passages`` passages from one work is the mean of its
passages' vectors, mapped to ``style_embed.dim`` and normalised. Each step draws
``authors_per_step`` training authors, two episodes each from two different works, and minimises
symmetric InfoNCE (each episode's positive is its author's other episode). Held-out authors'
retrieval accuracy is logged every ``validate_every`` steps; it never selects the model.

Recoverable as BOM-27's training is: a checkpoint every ``--checkpoint-minutes`` and at the end,
atomically; a rerun resumes, and the step's draw is a pure function of the seed and the step.

Usage::

    python -m style_embed.train --out runs/style                  # on the rented H100
    python -m style_embed.train --out runs/style_mid --size mid   # the 590M backbone (Amendment 37)
    python -m style_embed.train --out runs/style_tiny --tiny --max-steps 3   # CPU smoke test
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from style_embed.names import SIZES, bench_name, run_dir, tag  # noqa: F401 -- re-exported
from timelocked_lm.train import GPT, TINY

DATA = Path("data/corpus/style_embed")
AUTHORS = Path("data/style_embed/authors.parquet")
RUNS = Path("data/corpus/timelocked_lm/runs")


def backbone_for(cfg: dict, size: str) -> GPT:
    """An untrained backbone of the time-locked model's shape at ``size``."""
    t = cfg["timelocked_lm"]
    sh = t[f"{size}_shape"]
    return GPT(t["vocab_size"], t["context_length"], sh["layers"], sh["width"], sh["heads"],
               sh.get("qk_norm", False))  # fmt: skip


class StyleEncoder(nn.Module):
    def __init__(self, backbone: GPT, dim: int, ckpt: bool):
        super().__init__()
        self.backbone, self.ckpt = backbone, ckpt
        self.head = nn.Linear(backbone.ln.weight.shape[0], dim)

    def passages(self, idx: torch.Tensor) -> torch.Tensor:
        """Mean final hidden state per passage: (n, tokens) -> (n, width)."""
        b = self.backbone
        x = b.tok(idx) + b.pos(torch.arange(idx.shape[1], device=idx.device))
        for blk in b.blocks:
            x = checkpoint(blk, x, use_reentrant=False) if self.ckpt and self.training else blk(x)
        return b.ln(x).mean(dim=1)

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        """(episodes, passages, tokens) -> unit vectors (episodes, dim)."""
        e, p, t = idx.shape
        v = self.passages(idx.view(e * p, t)).view(e, p, -1).mean(dim=1)
        return F.normalize(self.head(v).float(), dim=-1)


def load_encoder(path: Path, cfg: dict, size: str = "base") -> StyleEncoder:
    """A trained encoder (``style.pt``) for scoring."""
    enc = StyleEncoder(backbone_for(cfg, size), cfg["style_embed"]["dim"], ckpt=False)
    enc.load_state_dict(torch.load(path, map_location="cpu"))
    return enc.eval()


class Episodes:
    """Passage rows grouped by author and work; a step's draw depends only on (seed, step)."""

    def __init__(self, cfg: dict):
        s = cfg["style_embed"]
        self.p = s["episode_passages"]
        self.rows = np.memmap(DATA / "passages.bin", dtype=np.uint16, mode="r").reshape(
            -1, s["passage_tokens"])  # fmt: skip
        idx = pq.read_table(DATA / "passages.parquet").to_pydict()
        split = dict(zip(*pq.read_table(AUTHORS, columns=["author", "split"]).to_pydict().values(),
                         strict=True))  # fmt: skip
        by: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
        for i, (a, w) in enumerate(zip(idx["author"], idx["work"], strict=True)):
            by[a][w].append(i)
        self.works = {"train": [], "heldout": []}
        for a, ws in sorted(by.items()):
            ok = [rows for _, rows in sorted(ws.items()) if len(rows) >= self.p]
            if len(ok) >= 2:
                self.works[split[a]].append(ok)
        self.seed = derive_seed(s["train_seed"], cfg)

    def draw(self, split: str, n: int, step: int) -> torch.Tensor:
        """(2n, passages, tokens): two episodes from two different works for each of n authors."""
        rng = np.random.default_rng([self.seed, step, 0 if split == "train" else 1])
        pool = self.works[split]
        out = []
        for a in rng.choice(len(pool), size=min(n, len(pool)), replace=False):
            w1, w2 = rng.choice(len(pool[a]), size=2, replace=False)
            for w in (w1, w2):
                out.append(self.rows[np.sort(rng.choice(pool[a][w], self.p, replace=False))])
        return torch.from_numpy(np.stack(out).astype(np.int64))


def info_nce(z: torch.Tensor, temperature: float) -> torch.Tensor:
    """Episodes 2i and 2i+1 are positives; every other episode in the batch is a negative."""
    sim = z @ z.T / temperature
    sim.fill_diagonal_(float("-inf"))
    target = torch.arange(len(z), device=z.device) ^ 1
    return F.cross_entropy(sim, target)


@torch.no_grad()
def retrieval(enc: StyleEncoder, eps: Episodes, n: int, step: int, dev: str, ctx) -> float:
    """Share of held-out episodes whose nearest other episode is by the same author."""
    enc.eval()
    x = eps.draw("heldout", n, step).to(dev)
    with ctx:
        z = torch.cat([enc(x[i : i + 64]) for i in range(0, len(x), 64)])
    sim = z @ z.T
    sim.fill_diagonal_(float("-inf"))
    acc = float((sim.argmax(dim=1) == (torch.arange(len(z), device=dev) ^ 1)).float().mean())
    enc.train()
    return acc


def lr_scale(step: int, s: dict) -> float:
    if step < s["warmup_steps"]:
        return (step + 1) / s["warmup_steps"]
    prog = (step - s["warmup_steps"]) / max(1, s["steps"] - s["warmup_steps"])
    return s["min_lr_share"] + (1 - s["min_lr_share"]) * 0.5 * (1 + math.cos(math.pi * prog))


def _save(path: Path, state: dict) -> None:
    tmp = path.with_suffix(".tmp")
    torch.save(state, tmp)
    os.replace(tmp, path)


def train(
    out: Path, tiny: bool, max_steps: int | None, ckpt_minutes: float, size: str = "base"
) -> int:
    cfg = load_config()
    s, t = cfg["style_embed"], cfg["timelocked_lm"]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(derive_seed(s["train_seed"], cfg))
    if tiny:
        backbone = GPT(t["vocab_size"], t["context_length"], **TINY)
        n_auth = 4
    else:
        backbone = backbone_for(cfg, size)
        backbone.load_state_dict(torch.load(RUNS / size / "model.pt", map_location="cpu"))
        n_auth = s["authors_per_step"]
    enc = StyleEncoder(backbone, s["dim"], ckpt=dev == "cuda").to(dev)
    opt = torch.optim.AdamW([
        {"params": enc.backbone.parameters(), "lr": s["lr_encoder"], "base": s["lr_encoder"]},
        {"params": enc.head.parameters(), "lr": s["lr_head"], "base": s["lr_head"]}],
        weight_decay=s["weight_decay"])  # fmt: skip
    eps = Episodes(cfg)
    print(f"train authors {len(eps.works['train']):,}, held out {len(eps.works['heldout']):,}",
          flush=True)  # fmt: skip
    out.mkdir(parents=True, exist_ok=True)
    ck = out / "checkpoint.pt"
    step = 0
    if ck.exists():
        st = torch.load(ck, map_location=dev)
        enc.load_state_dict(st["model"])
        opt.load_state_dict(st["optimizer"])
        step = st["step"]
        print(f"resumed at step {step}", flush=True)
    (out / "run.json").write_text(json.dumps({**stamp(), "tiny": tiny, "device": dev, "size": size,
                                              "train_authors": len(eps.works["train"]),
                                              "heldout_authors": len(eps.works["heldout"])},
                                             indent=1) + "\n")  # fmt: skip
    steps = max_steps or s["steps"]
    ctx = (torch.autocast("cuda", dtype=torch.bfloat16) if dev == "cuda"
           else torch.autocast("cpu", enabled=False))  # fmt: skip
    log = (out / "log.jsonl").open("a")
    last, t0 = time.time(), time.time()
    enc.train()
    while step < steps:
        for g in opt.param_groups:
            g["lr"] = g["base"] * lr_scale(step, s)
        x = eps.draw("train", n_auth, step).to(dev)
        with ctx:
            loss = info_nce(enc(x), s["temperature"])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(enc.parameters(), t["grad_clip"])
        opt.step()
        opt.zero_grad(set_to_none=True)
        step += 1
        rec = {"step": step, "loss": float(loss.detach()), "sec": round(time.time() - t0, 1)}
        if step % s["validate_every"] == 0 or step == steps:
            rec["heldout_top1"] = retrieval(enc, eps, 256 if not tiny else 4, step, dev, ctx)
            print(json.dumps(rec), flush=True)
        log.write(json.dumps(rec) + "\n")
        log.flush()
        if time.time() - last > ckpt_minutes * 60 or step == steps:
            _save(ck, {"model": enc.state_dict(), "optimizer": opt.state_dict(), "step": step})
            last = time.time()
    torch.save(enc.state_dict(), out / "style.pt")
    print(f"done: {steps:,} steps -> {out / 'style.pt'}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--tiny", action="store_true", help="random tiny backbone; smoke test")
    ap.add_argument("--max-steps", type=int)
    ap.add_argument("--checkpoint-minutes", type=float, default=20)
    ap.add_argument("--size", choices=SIZES, default="base", help="the time-locked backbone")
    a = ap.parse_args(argv)
    return train(a.out, a.tiny, a.max_steps, a.checkpoint_minutes, a.size)


if __name__ == "__main__":
    sys.exit(main())
