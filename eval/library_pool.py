"""The author algorithm on long lists, on one shared pool of library authors (BOM-94; exploratory).

Fixed path step 3 (tracker BOM-92). The pool is the sweep's 200 known-book authors, each trained on
the profile rebuilt without the book (``calib_profile``), and ``library_pool.pool_size - 200``
seeded other swept authors (``profile``). Every author gets equal-dose models, as Amendment 45:

- **small**: ``small_slices`` slices of the 1828-29 revelation sample's training tokens
  (``alm_candidates_plan.json``), evenly spread over the author's text;
- **large**: one slice of ``large_sequences`` sequences of ``alm.seq`` tokens at a seeded start
  (the largest dose nearly every swept author has; an author with less gets no large model).

Tests are the 200 books: ``test_chunks`` query chunks each, the first ``test_tokens`` tokens of
each. Every model scores every test: mean window loss minus the base model's (5.2). Training and
test words are the sweep's (KJV-masked, benchmark word form; ``sweep.index._read``).

``prepare`` packs the words (licensed text, never in git); ``run`` trains and scores on the GPU,
one small file per model, resuming; ``--limit N`` stops after N models and prints the time per
model (the price check). The score table holds names and numbers only.

Usage::

    python -m eval.library_pool prepare               # Mac -> data/corpus/library_pool/plan.json.gz
    python -m eval.library_pool run pilot [--limit 20] [--micro-batch 8]   # GPU
        -> data/sweep/pool_<size>.npz
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, sha256_of_config
from metadata.config import load as load_config

WORK = Path("data/corpus/library_pool")
PLAN = WORK / "plan.json.gz"
OUT = Path("data/sweep")
CAND_PLAN = Path("data/benchmark/alm_candidates_plan.json")
REVELATION = "cand__joseph-smith__dictated__pre1830"


def small_tokens() -> int:
    """The 1828-29 revelation sample's training tokens (Amendment 45's dose)."""
    units = json.loads(CAND_PLAN.read_text())["units"]
    return next(u for u in units if u["key"] == REVELATION)["train_tokens"]


def slices(n_ids: int, n: int, k: int) -> list[int]:
    """``k`` starts of ``n``-token slices spread evenly over ``n_ids`` tokens (fewer if they
    would repeat; none if the text is shorter than one slice)."""
    if n_ids < n:
        return []
    if k == 1 or n_ids == n:
        return [(n_ids - n) // 2]
    return sorted({round(i * (n_ids - n) / (k - 1)) for i in range(k)})


def models(n_ids: int, author: str, cfg: dict) -> list[tuple[str, int, int]]:
    """(name, start, length) of an author's equal-dose models."""
    lp = cfg["library_pool"]
    n = small_tokens()
    out = [(f"{author}#small{i}", s, n) for i, s in enumerate(slices(n_ids, n, lp["small_slices"]))]
    big = lp["large_sequences"] * cfg["alm"]["seq"]
    if n_ids >= big:
        rng = random.Random(derive_seed(f"{lp['seed']}:large:{author}", cfg))
        out.append((f"{author}#large", rng.randrange(0, n_ids - big + 1), big))
    return out


def prepare() -> int:
    import pyarrow.parquet as pq

    from sweep.index import _read
    from sweep.units import OUT as SWEEP

    cfg = load_config()
    lp = cfg["library_pool"]
    authors = pq.read_table(SWEEP / "authors.parquet").to_pylist()
    known = sorted(a["author"] for a in authors if a["calibration_book"])
    rest = sorted(a["author"] for a in authors if not a["calibration_book"])
    rng = random.Random(derive_seed(f"{lp['seed']}:pool", cfg))
    extra = sorted(rng.sample(rest, lp["pool_size"] - len(known)))
    blocks = pq.read_table(SWEEP / "blocks.parquet", columns=["block_id", "author", "role"])
    chunks: dict[str, list[str]] = {}
    for b in blocks.to_pylist():
        if b["role"] == "calib_query":
            chunks.setdefault(b["author"], []).append(b["block_id"])
    train = {a: _read(f"calib_profile:{a}") for a in known}
    train.update({a: _read(f"profile:{a}") for a in extra})
    tests = []
    for a in known:
        ids = sorted(chunks[a], key=lambda u: int(u.rsplit(":", 1)[1]))[: lp["test_chunks"]]
        tests += [{"author": a, "where": u, "words": _read(u)} for u in ids]
    WORK.mkdir(parents=True, exist_ok=True)
    with gzip.open(PLAN, "wt") as fh:
        json.dump({"config_sha256": sha256_of_config(), "known": known, "train": train,
                   "tests": tests}, fh)  # fmt: skip
    print(f"{len(train)} authors ({len(known)} known books), {len(tests)} tests -> {PLAN} "
          f"({PLAN.stat().st_size / 1e6:.1f} MB)")  # fmt: skip
    return 0


def _path(work: Path, name: str) -> Path:
    return work / (hashlib.sha1(name.encode()).hexdigest() + ".npy")


def run(size: str, micro: int, limit: int | None) -> int:
    import torch
    from tokenizers import Tokenizer

    from alm.benchmark import _base, _device, finetune, window_losses
    from timelocked_lm.release import TOKENIZER

    cfg = load_config()
    a, lp = cfg["alm"], cfg["library_pool"]
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    with gzip.open(PLAN, "rt") as fh:
        p = json.load(fh)
    tests = [tok.encode(" ".join(x["words"])).ids[: lp["test_tokens"]] for x in p["tests"]]
    work = WORK / size
    work.mkdir(parents=True, exist_ok=True)
    base = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in base.state_dict().items()}
    score = lambda: np.array([np.mean(w) for w in window_losses(  # noqa: E731
        base, tests, a["score_window"], dev)], dtype=np.float32)  # fmt: skip
    if not (work / "base.npy").exists():
        np.save(work / "base.npy", score())
    names, done, t0 = [], 0, time.time()
    for author, words in sorted(p["train"].items()):
        ids = np.array(tok.encode(" ".join(words)).ids, dtype=np.int32)
        for name, start, n in models(len(ids), author, cfg):
            names.append(name)
            path = _path(work, name)
            if path.exists() or (limit is not None and done >= limit):
                continue
            base.load_state_dict(state)
            seed = derive_seed(f"{a['train_seed']}:library:{name}", cfg)
            torch.manual_seed(seed)
            finetune(base, ids[start : start + n], cfg, seed, micro, dev,
                     cfg["timelocked_lm"]["finetune_lr"])  # fmt: skip
            tmp = path.with_suffix(".tmp.npy")
            np.save(tmp, score())
            tmp.replace(path)
            done += 1
            if done % 100 == 0:
                print(f"  {size}: {done} models, {(time.time() - t0) / done:.2f} s each",
                      flush=True)  # fmt: skip
    if done:
        sec = time.time() - t0
        print(f"{size}: {done} models in {sec:.0f} s, {sec / done:.2f} s each; "
              f"{len(names)} in the plan", flush=True)  # fmt: skip
    have = [n for n in names if _path(work, n).exists()]
    if len(have) < len(names):
        print(f"{len(have)}/{len(names)} models scored; rerun to finish", flush=True)
        return 0
    bl = np.load(work / "base.npy")
    S = np.stack([np.load(_path(work, n)) - bl for n in names], axis=1)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"pool_{size}.npz"
    np.savez_compressed(out, scores=S, models=np.array(names),
                        test_author=np.array([x["author"] for x in p["tests"]]),
                        test_where=np.array([x["where"] for x in p["tests"]]),
                        known=np.array(p["known"]), config_sha256=sha256_of_config())  # fmt: skip
    print(f"{S.shape[0]} tests x {S.shape[1]} models -> {out}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["prepare", "run"])
    ap.add_argument("size", nargs="?", choices=["pilot", "base", "mid"])
    ap.add_argument("--limit", type=int, help="run: stop after this many new models (price check)")
    ap.add_argument("--micro-batch", type=int, default=8, help="memory only; same update")
    a = ap.parse_args(argv)
    if a.cmd == "prepare":
        return prepare()
    if not a.size:
        ap.error("run needs a size")
    return run(a.size, a.micro_batch, a.limit)


if __name__ == "__main__":
    sys.exit(main())
