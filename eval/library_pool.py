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

``report``: for each dose (``small`` the median of an author's small slices, ``small0`` one slice,
``large``), how often the true author is first and among the closest ``top_n`` of a random list of
each size in ``sizes``, exactly (from the number of pool authors scoring closer; hypergeometric),
counted by author; by passage and with a book's chunks averaged; raw scores and each model's
scores on its own scale (set on the other half of the books); all books and by genre group.

Usage::

    python -m eval.library_pool prepare               # Mac -> data/corpus/library_pool/plan.json.gz
    python -m eval.library_pool run pilot [--limit 20] [--micro-batch 8]   # GPU
        -> data/sweep/pool_<size>.npz
    python -m eval.library_pool report pilot          # -> data/sweep/pool_report_<size>.json
    python -m eval.library_pool prepare-bom           # BOM-95 second opinion: plan_bom.json.gz
    python -m eval.library_pool run pilot --name _bom # GPU -> data/sweep/pool_bom_<size>.npz
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


def prepare_bom() -> int:
    """BOM-95's second opinion: the encoder's top library authors (full-profile ranking) and the
    Phase 1 candidate units as training text, the sealed Book of Mormon chunks as tests, all in
    the sweep's word form (``classic.features.tokenize``)."""
    from classic.features import tokenize
    from eval.js_later import _refs
    from eval.library_bom import KEY, SEALED
    from eval.library_bom import OUT as RANKING
    from sweep.index import _read

    top = json.loads(RANKING.read_text())["rankings"]["full"]["second_opinion"]
    train = {a: _read(f"profile:{a}") for a in top}
    train.update({u: r["tokens"] for u, r in sorted(_refs().items()) if r["tokens"]})
    key = json.loads(KEY.read_text())
    rows = [json.loads(ln) for ln in SEALED.read_text().splitlines()]
    tests = [
        {"author": "bom", "where": r["id"], "words": tokenize(r["text"])}
        for r in sorted(rows, key=lambda r: r["id"])
        if key[r["id"]]["kind"] == "bom"
    ]
    WORK.mkdir(parents=True, exist_ok=True)
    with gzip.open(WORK / "plan_bom.json.gz", "wt") as fh:
        json.dump({"config_sha256": sha256_of_config(), "known": [], "train": train,
                   "tests": tests, "test_tokens": None}, fh)  # fmt: skip
    print(f"{len(train)} units ({len(top)} library authors), {len(tests)} tests -> "
          f"{WORK / 'plan_bom.json.gz'}")  # fmt: skip
    return 0


def run(size: str, micro: int, limit: int | None, name: str = "") -> int:
    import torch
    from tokenizers import Tokenizer

    from alm.benchmark import _base, _device, finetune, window_losses
    from timelocked_lm.release import TOKENIZER

    cfg = load_config()
    a, lp = cfg["alm"], cfg["library_pool"]
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    with gzip.open(WORK / f"plan{name}.json.gz", "rt") as fh:
        p = json.load(fh)
    cap = p.get("test_tokens", lp["test_tokens"])  # None: the whole chunk
    tests = [tok.encode(" ".join(x["words"])).ids[:cap] for x in p["tests"]]
    work = WORK / f"{size}{name}"
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
    out = OUT / f"pool{name}_{size}.npz"
    np.savez_compressed(out, scores=S, models=np.array(names),
                        test_author=np.array([x["author"] for x in p["tests"]]),
                        test_where=np.array([x["where"] for x in p["tests"]]),
                        known=np.array(p["known"]), config_sha256=sha256_of_config())  # fmt: skip
    print(f"{S.shape[0]} tests x {S.shape[1]} models -> {out}", flush=True)
    return 0


def dose_tables(S: np.ndarray, names: list[str]) -> dict[str, tuple[list[str], np.ndarray]]:
    """dose -> (authors, tests x authors scores): ``small`` is the median over an author's small
    slices, ``small0`` the first slice alone, ``large`` the large model."""
    by: dict[str, dict[str, list[int]]] = {"small": {}, "small0": {}, "large": {}}
    for j, n in enumerate(names):
        a, _, kind = n.rpartition("#")
        if kind == "large":
            by["large"].setdefault(a, []).append(j)
        else:
            by["small"].setdefault(a, []).append(j)
            if kind == "small0":
                by["small0"].setdefault(a, []).append(j)
    return {d: (sorted(m), np.stack([np.median(S[:, m[a]], axis=1) for a in sorted(m)], axis=1))
            for d, m in by.items() if m}  # fmt: skip


def scaled(X: np.ndarray, half: np.ndarray) -> np.ndarray:
    """Each model's scores on its own scale (z-norm), the scale for a test taken from the tests
    of the other half of the books, so no test sets its own scale."""
    out = np.empty_like(X, dtype=np.float64)
    for h in (False, True):
        ref = X[half != h]
        out[half == h] = (X[half == h] - ref.mean(axis=0)) / ref.std(axis=0)
    return out


def in_top(better: np.ndarray, others: int, size: int, n: int) -> np.ndarray:
    """The chance the true author is among the closest ``n`` of a random list of ``size`` drawn
    with the true author from ``others`` + 1, when ``better`` of the others score closer."""
    from scipy.stats import hypergeom

    return hypergeom.cdf(
        n - 1, others, better, np.minimum(size - 1, others)
    )  # the whole pool at most


def report(size: str) -> int:
    cfg = load_config()
    lp = cfg["library_pool"]
    z = np.load(OUT / f"pool_{size}.npz")
    S, names = z["scores"].astype(np.float64), z["models"].tolist()
    t_auth = z["test_author"].tolist()
    books = sorted(set(t_auth))
    groups = {r["author"]: r for r in json.loads((OUT / "coverage.json").read_text())["records"]}
    half_of = {a: int(hashlib.sha256(f"{lp['seed']}:half:{a}".encode()).hexdigest(), 16) % 2 == 1
               for a in books}  # fmt: skip
    half = np.array([half_of[a] for a in t_auth])
    rows = np.array([books.index(a) for a in t_auth])
    doc = {"config_sha256": sha256_of_config(), "exploratory": True, "size": size,
           "tests": len(t_auth), "books": len(books), "doses": {}}  # fmt: skip
    for dose, (authors, X) in dose_tables(S, names).items():
        col = {a: j for j, a in enumerate(authors)}
        res = {"pool_authors": len(authors)}
        for label, M in (("raw", X), ("scaled", scaled(X, half))):
            # by passage: each test alone; by book: its chunks averaged
            B = np.stack([M[rows == i].mean(axis=0) for i in range(len(books))])
            for unit, T, who in (("passage", M, t_auth), ("book", B, books)):
                ok = [i for i, a in enumerate(who) if a in col]
                better = np.array([(np.delete(T[i], col[who[i]]) < T[i, col[who[i]]]).sum()
                                   for i in ok])  # fmt: skip
                others = len(authors) - 1
                tab: dict[str, dict] = {}
                sel = {"all": np.ones(len(ok), dtype=bool)}
                for g in ("same", "mixed", "cross"):
                    sel[f"genre_{g}"] = np.array([groups[who[i]]["genre"] == g for i in ok])
                for g, mask in sel.items():
                    tab[g] = {
                        "n": int(mask.sum()),
                        "median_rank": float(np.median(better[mask]) + 1),
                    }
                    for n in lp["top_n"]:
                        # by author: a book's passages first averaged, then the books
                        per = in_top(better[:, None], others, np.array(lp["sizes"])[None, :], n)
                        owners = np.array([books.index(who[i]) for i in ok])[mask]
                        by_author = np.stack([per[mask][owners == b].mean(axis=0)
                                              for b in sorted(set(owners))])  # fmt: skip
                        means = by_author.mean(axis=0)
                        pairs = zip(lp["sizes"], means, strict=True)
                        tab[g][f"top{n}"] = {str(s_): round(float(v), 4) for s_, v in pairs}
                res[f"{label}_{unit}"] = tab
        doc["doses"][dose] = res
    out = OUT / f"pool_report_{size}.json"
    out.write_text(json.dumps(doc, indent=1) + "\n")
    show = [s_ for s_ in lp["sizes"] if s_ in lp["show"]]
    for dose, res in doc["doses"].items():
        print(f"{dose} ({res['pool_authors']} authors); true author first / in top 10, "
              f"by list size {show} (%)")  # fmt: skip
        for key in ("raw_passage", "scaled_passage", "raw_book", "scaled_book"):
            for g in ("all", "genre_cross"):
                t = res[key][g]
                print(f"  {key:15s} {g:12s} n={t['n']:3d}  top1 "
                      + " ".join(f"{100 * t['top1'][str(s_)]:5.1f}" for s_ in show) + "   top10 "
                      + " ".join(f"{100 * t['top10'][str(s_)]:5.1f}" for s_ in show))  # fmt: skip
    print(f"-> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["prepare", "prepare-bom", "run", "report"])
    ap.add_argument("--name", default="", help="run: another plan, e.g. _bom (plan_bom.json.gz)")
    ap.add_argument("size", nargs="?", choices=["pilot", "base", "mid"])
    ap.add_argument("--limit", type=int, help="run: stop after this many new models (price check)")
    ap.add_argument("--micro-batch", type=int, default=8, help="memory only; same update")
    a = ap.parse_args(argv)
    if a.cmd == "prepare":
        return prepare()
    if a.cmd == "prepare-bom":
        return prepare_bom()
    if not a.size:
        ap.error("run and report need a size")
    if a.cmd == "report":
        return report(a.size)
    return run(a.size, a.micro_batch, a.limit, a.name)


if __name__ == "__main__":
    sys.exit(main())
