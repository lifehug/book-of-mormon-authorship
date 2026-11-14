"""A second style encoder, trained for cross-genre retrieval (BOM-89, step 3; exploratory).

What the first encoder's log showed (``data/corpus/style_embed/runs/style/log.jsonl``): accuracy on
held-out authors was flat from step 1,000 while training loss fell to 0.03, so it memorised its
authors' 32 fixed passages per work; and the sweep's misses are authors whose other writing is in a
different genre (``python -m sweep.coverage``). Three changes, each from ``style_embed_v2`` in the
config; everything else is BOM-30's:

- **More text**: ``passages_per_work`` passages per work instead of 32, freshly drawn.
- **Harder pairs** (after Sadiri, arXiv 2408.05192): on ``hard_step_share`` of steps every author in
  the batch has a work in one genre (so the in-batch decoys are that genre), one episode comes from
  it and the author's other episode from a work in a different genre when there is one. The other
  steps are BOM-30's random pairs (mixed decoys, after arXiv 2510.16819).
- **A validation split**: ``validation_share`` of the training authors are set aside, their
  retrieval accuracy is logged every ``validate_every`` steps, and the best step's weights are kept
  as ``style.pt``. BOM-30's held-out authors (the sweep's 200 known books among them) stay held
  out and are never used to choose anything; their accuracy is logged for comparison only.

A work's genre is the commonest primary label of its volumes (``data/catalog/genre.parquet``).

Usage::

    python -m style_embed.v2 build [--workers 6]
    python -m style_embed.v2 train --out runs/style_v2            # on the rented H100
    python -m style_embed.v2 train --out /tmp/t --tiny --max-steps 3   # CPU smoke test
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from style_embed import data as d1

OUT = Path("data/style_embed")
WORK = Path("data/corpus/style_embed/v2")
GENRE = Path("data/catalog/genre.parquet")
UNKNOWN = "uncertain"


def splits(first: dict[str, str], salt: int, share: float) -> dict[str, str]:
    """BOM-30's held-out authors stay held out; ``share`` of the rest become validation."""
    return {a: s if s == "heldout" else "validation" if d1._held_out(a, salt, share) else "train"
            for a, s in first.items()}  # fmt: skip


def work_genre(volumes: list[str], genre: dict[str, str]) -> str:
    """The commonest known primary genre of a work's volumes, or ``uncertain``."""
    known = Counter(g for v in volumes if (g := genre.get(v, UNKNOWN)) != UNKNOWN)
    return sorted(known.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if known else UNKNOWN


def build(workers: int) -> int:
    cfg = load_config()
    s, v = cfg["style_embed"], cfg["style_embed_v2"]
    auth = d1.authors(cfg)
    first = dict(zip(*pq.read_table(OUT / "authors.parquet", columns=["author", "split"])
                     .to_pydict().values(), strict=True))  # fmt: skip
    if set(first) != set(auth):
        raise SystemExit("the qualifying authors differ from BOM-30's; stop")
    split = splits(first, derive_seed(v["validation_seed"], cfg), v["validation_share"])
    need = {r["work_id"] for ws in auth.values() for vols in ws.values() for r in vols}
    genre = {r["work_id"]: (r["genre"] or UNKNOWN).split(",")[0]
             for r in pq.read_table(GENRE, columns=["work_id", "genre"]).to_pylist()
             if r["work_id"] in need}  # fmt: skip
    sv = {**s, "passages_per_work": v["passages_per_work"]}
    jobs = [(a, ws, sv, derive_seed(f"{v['passage_seed']}:{a}", cfg)) for a, ws in auth.items()]
    WORK.mkdir(parents=True, exist_ok=True)
    index = {"author": [], "work": [], "volume": []}
    with (WORK / "passages.bin").open("wb") as f, Pool(workers, initializer=d1._init) as pool:
        for k, (a, rows) in enumerate(pool.imap(d1._author_passages, jobs, chunksize=8), 1):
            for key, vol, ids in rows:
                f.write(np.asarray(ids, dtype=np.uint16).tobytes())
                index["author"].append(a)
                index["work"].append(key)
                index["volume"].append(vol)
            if k % 500 == 0:
                print(f"  {k:,}/{len(jobs):,} authors, {len(index['author']):,} passages",
                      flush=True)  # fmt: skip
    pq.write_table(pa.table(index), WORK / "passages.parquet")
    works = [{"author": a, "split": split[a], "work": k,
              "genre": work_genre([r["work_id"] for r in vols], genre)}
             for a, ws in auth.items() for k, vols in ws.items()]  # fmt: skip
    pq.write_table(pa.Table.from_pylist(works), OUT / "v2_works.parquet")
    n = Counter(split.values())
    by: dict[str, set] = defaultdict(set)
    for w in works:
        by[w["author"]].add(w["genre"])
    cross = sum(len(g - {UNKNOWN}) > 1 for g in by.values())
    (OUT / "v2_build.json").write_text(json.dumps(
        {**stamp(), "exploratory": True, "authors": len(auth), "splits": dict(n),
         "authors_with_two_genres": cross, "passages": len(index["author"]),
         "work_genres": dict(Counter(w["genre"] for w in works))}, indent=1) + "\n")  # fmt: skip
    print(f"{len(auth):,} authors {dict(n)}; {cross:,} with works in two genres; "
          f"{len(index['author']):,} passages -> {WORK / 'passages.bin'}", flush=True)  # fmt: skip
    return 0


class Episodes:
    """Passage rows by author and work, with each work's genre; a step's draw depends only on
    (seed, step)."""

    def __init__(self, cfg: dict, rows: np.ndarray | None = None, index: dict | None = None,
                 works: list[dict] | None = None):  # fmt: skip
        s, v = cfg["style_embed"], cfg["style_embed_v2"]
        self.p, self.hard = s["episode_passages"], v["hard_step_share"]
        if rows is None:
            rows = np.memmap(WORK / "passages.bin", dtype=np.uint16, mode="r")
        self.rows = rows.reshape(-1, s["passage_tokens"])
        idx = index or pq.read_table(WORK / "passages.parquet").to_pydict()
        meta = {(w["author"], w["work"]): w
                for w in works or pq.read_table(OUT / "v2_works.parquet").to_pylist()}  # fmt: skip
        by: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
        for i, (a, w) in enumerate(zip(idx["author"], idx["work"], strict=True)):
            by[a][w].append(i)
        # per split: authors as [(genre, rows)], works with a full episode only, two or more
        self.pool: dict[str, list[list[tuple[str, np.ndarray]]]] = defaultdict(list)
        for a, ws in sorted(by.items()):
            ok = [(meta[a, w]["genre"], np.array(r)) for w, r in sorted(ws.items())
                  if len(r) >= self.p]  # fmt: skip
            if len(ok) >= 2:
                self.pool[meta[a, next(iter(ws))]["split"]].append(ok)
        self.in_genre: dict[str, list[int]] = defaultdict(list)
        for i, ws in enumerate(self.pool["train"]):
            for g in {g for g, _ in ws} - {UNKNOWN}:
                self.in_genre[g].append(i)
        self.seed = derive_seed(v["train_seed"], cfg)

    def _episode(self, rng, rows: np.ndarray) -> np.ndarray:
        return self.rows[np.sort(rng.choice(rows, self.p, replace=False))]

    def pairs(self, split: str, n: int, step: int) -> list[tuple[int, int, int]]:
        """(author, first work, second work) for the step; the rule in the module docstring."""
        rng = np.random.default_rng([self.seed, step, {"train": 0, "validation": 1}.get(split, 2)])
        pool = self.pool[split]
        if split == "train" and rng.random() < self.hard:
            genres = sorted(g for g, a in self.in_genre.items() if len(a) >= n)
            sizes = np.array([len(self.in_genre[g]) for g in genres], dtype=float)
            g = genres[rng.choice(len(genres), p=sizes / sizes.sum())]
            out = []
            for a in rng.choice(self.in_genre[g], size=n, replace=False):
                here = [i for i, (wg, _) in enumerate(pool[a]) if wg == g]
                away = [i for i, (wg, _) in enumerate(pool[a]) if wg != g]
                w1 = int(rng.choice(here))
                rest = away or [i for i in here if i != w1]
                out.append((int(a), w1, int(rng.choice(rest))))
            return out
        out = []
        for a in rng.choice(len(pool), size=min(n, len(pool)), replace=False):
            w1, w2 = rng.choice(len(pool[a]), size=2, replace=False)
            out.append((int(a), int(w1), int(w2)))
        return out

    def draw(self, split: str, n: int, step: int):
        import torch

        rng = np.random.default_rng([self.seed, step, 9])
        out = []
        for a, w1, w2 in self.pairs(split, n, step):
            for w in (w1, w2):
                out.append(self._episode(rng, self.pool[split][a][w][1]))
        return torch.from_numpy(np.stack(out).astype(np.int64))


def train(out: Path, tiny: bool, max_steps: int | None, ckpt_minutes: float) -> int:
    import torch

    from style_embed import train as t1
    from timelocked_lm.train import GPT, TINY

    cfg = load_config()
    s, v, t = cfg["style_embed"], cfg["style_embed_v2"], cfg["timelocked_lm"]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(derive_seed(v["train_seed"], cfg))
    if tiny:
        backbone, n_auth = GPT(t["vocab_size"], t["context_length"], **TINY), 4
    else:
        backbone = t1.backbone_for(cfg, "base")
        backbone.load_state_dict(torch.load(t1.RUNS / "base" / "model.pt", map_location="cpu"))
        n_auth = s["authors_per_step"]
    enc = t1.StyleEncoder(backbone, s["dim"], ckpt=dev == "cuda").to(dev)
    opt = torch.optim.AdamW([
        {"params": enc.backbone.parameters(), "lr": s["lr_encoder"], "base": s["lr_encoder"]},
        {"params": enc.head.parameters(), "lr": s["lr_head"], "base": s["lr_head"]}],
        weight_decay=s["weight_decay"])  # fmt: skip
    eps = Episodes(cfg)
    sizes = {k: len(p) for k, p in eps.pool.items()}
    print(f"authors {sizes}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    ck, step, best = out / "checkpoint.pt", 0, -1.0
    if ck.exists():
        st = torch.load(ck, map_location=dev)
        enc.load_state_dict(st["model"])
        opt.load_state_dict(st["optimizer"])
        step, best = st["step"], st["best"]
        print(f"resumed at step {step}", flush=True)
    run = {**stamp(), "exploratory": True, "tiny": tiny, "device": dev, "authors": sizes}
    (out / "run.json").write_text(json.dumps(run, indent=1) + "\n")
    sched = {**s, "steps": v["steps"]}
    steps = max_steps or v["steps"]
    ctx = (torch.autocast("cuda", dtype=torch.bfloat16) if dev == "cuda"
           else torch.autocast("cpu", enabled=False))  # fmt: skip
    nval = 4 if tiny else v["validation_authors"]

    class _Split:  # style_embed.train.retrieval draws "heldout"; point it at one of our splits
        def __init__(self, split: str):
            self.split = split

        def draw(self, _name: str, n: int, at: int):
            return eps.draw(self.split, n, at)

    log = (out / "log.jsonl").open("a")
    last, t0 = time.time(), time.time()
    enc.train()
    while step < steps:
        for g in opt.param_groups:
            g["lr"] = g["base"] * t1.lr_scale(step, sched)
        x = eps.draw("train", n_auth, step).to(dev)
        with ctx:
            loss = t1.info_nce(enc(x), s["temperature"])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(enc.parameters(), t["grad_clip"])
        opt.step()
        opt.zero_grad(set_to_none=True)
        step += 1
        rec = {"step": step, "loss": float(loss.detach()), "sec": round(time.time() - t0, 1)}
        if step % v["validate_every"] == 0 or step == steps:
            # the same validation draw every time (step 0), so the curve is comparable
            rec["validation_top1"] = t1.retrieval(enc, _Split("validation"), nval, 0, dev, ctx)
            rec["heldout_top1"] = t1.retrieval(enc, _Split("heldout"), nval, 0, dev, ctx)
            if rec["validation_top1"] > best:
                best = rec["validation_top1"]
                rec["kept"] = True
                torch.save(enc.state_dict(), out / "style.tmp")
                (out / "style.tmp").replace(out / "style.pt")
            print(json.dumps(rec), flush=True)
        log.write(json.dumps(rec) + "\n")
        log.flush()
        if time.time() - last > ckpt_minutes * 60 or step == steps:
            t1._save(ck, {"model": enc.state_dict(), "optimizer": opt.state_dict(), "step": step,
                          "best": best})  # fmt: skip
            last = time.time()
    print(f"done: {steps:,} steps, best validation {best:.3f} -> {out / 'style.pt'}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["build", "train"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--tiny", action="store_true", help="random tiny backbone; smoke test")
    ap.add_argument("--max-steps", type=int)
    ap.add_argument("--checkpoint-minutes", type=float, default=20)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        return build(a.workers)
    if not a.out:
        ap.error("train needs --out")
    return train(a.out, a.tiny, a.max_steps, a.checkpoint_minutes)


if __name__ == "__main__":
    sys.exit(main())
