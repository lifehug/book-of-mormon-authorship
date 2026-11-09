"""The style embeddings on the validation benchmark (BOM-30; Amendment 24).

BOM-21's own trials (tasks, tests, references with each test's span left out, imposter pools), with
the trained encoder's vectors in place of word frequencies: a text (a 1,000-word block, a sample,
an author's references) is cut into ``style_embed.passage_tokens``-token passages and embedded as
one episode. Closed set by cosine distance to each author's profile; verification by General
Imposters on the vectors with the registered settings; judged by Amendment 22's rule
(``alm.benchmark.decide``).

Usage::

    python -m style_embed.benchmark [--size base|mid] [--model <style.pt>]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

from alm.benchmark import OUT, decide
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from style_embed.train import bench_name, load_encoder, run_dir

MODEL = run_dir("base") / "style.pt"


def embedder(model: Path, cfg: dict, size: str = "base"):
    """words -> unit vector (numpy), for texts in the benchmark's word form."""
    from tokenizers import Tokenizer

    from timelocked_lm.release import TOKENIZER

    s = cfg["style_embed"]
    dev = ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available()
           else "cpu")  # fmt: skip
    enc = load_encoder(model, cfg, size).to(dev)
    tok = Tokenizer.from_file(str(TOKENIZER))
    n = s["passage_tokens"]

    @torch.no_grad()
    def embed(words: list[str]) -> np.ndarray:
        """One episode of all the text's passages; passages run 64 at a time (the same mean)."""
        ids = tok.encode(" ".join(words)).ids
        k = max(1, len(ids) // n)
        x = torch.tensor((ids + [0] * n)[: k * n], dtype=torch.long, device=dev).view(k, n)
        v = torch.cat([enc.passages(x[i : i + 64]) for i in range(0, k, 64)]).mean(dim=0)
        z = torch.nn.functional.normalize(enc.head(v).float(), dim=-1)
        return z.cpu().numpy().astype(np.float64)

    return embed


def run(model: Path, size: str = "base") -> int:
    from classic import general_imposters
    from classic.delta import cosine_delta
    from eval.benchmark import TASKS, imposter_pool, load_tasks
    from metadata.config import classic_kwargs

    cfg = load_config()
    embed = embedder(model, cfg, size)
    kw = classic_kwargs(cfg)
    rng = random.Random(derive_seed("benchmark", cfg))
    spec = json.loads(TASKS.read_text())
    recs_by = {}
    for name, task in load_tasks(cfg).items():
        pool = imposter_pool(task["pool_set"], set(spec[name].get("exclude_from_pool", [])), cfg,
                             task["pool_genre"], task["pool_exclude_authors"],
                             spec[name].get("imposter_fill"))  # fmt: skip
        P = np.stack([embed(x) for x in pool])
        names = sorted(task["authors"])
        per_trial = cfg["classic"]["imposters"]["per_trial"]
        gi_args = {**kw["imposters"], "n_imposters": min(len(P), per_trial)}
        recs, cache = [], {}
        for a, test, span in task["tests"]:
            x = embed(test)
            prof = {}
            for b in names:
                key = (b, tuple(span) if (b == a and span) else None)
                if key not in cache:
                    bl = task["authors"][b]
                    if key[1]:
                        bl = bl[: span[0]] + bl[span[1] :]
                    cache[key] = embed([w for blk in bl for w in blk])
                prof[b] = cache[key]
            dist = {b: cosine_delta(x, prof[b]) for b in names}
            gs = {b: general_imposters(x, prof[b], P, seed=rng.randrange(2**31), **gi_args)
                  for b in names}  # fmt: skip
            others = [b for b in names if b != a]
            recs.append({"author": a, "scores": dist, "gi": gs,
                         "predicted": min(dist, key=lambda b: (dist[b], b)), "positive": gs[a],
                         "open_negative": max(gs[b] for b in others)})  # fmt: skip
        recs_by[name] = recs
        print(f"  style {name}: {len(recs)} tests, pool {len(P)}", flush=True)
    d = decide(recs_by, cfg)
    out = OUT / f"{bench_name(size)}.json"
    out.write_text(json.dumps({**stamp(), "model": str(model), "size": size, **d,
                               "records": recs_by}, indent=1) + "\n")  # fmt: skip
    v = d["verdict"]
    print(f"{bench_name(size)}: closed set {v['closed_set']:.3f} {d['closed_set_by_task']}; "
          f"open-set FPR {v['open_set_fpr']:.3f}; passes {v['passes']} -> {out}",
          flush=True)  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "--size", choices=("base", "mid"), default="base", help="the encoder's backbone"
    )
    ap.add_argument("--model", type=Path, help="default: that size's run_dir/style.pt")
    a = ap.parse_args(argv)
    return run(a.model or run_dir(a.size) / "style.pt", a.size)


if __name__ == "__main__":
    sys.exit(main())
