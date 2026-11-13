"""Step 0 of the library-wide search: the older methods as sweeps (Amendment 57, Part 2).

On the sweep's 200 calibration books (Amendment 28; each book's author represented by a profile
rebuilt without the book) and its 300-word MFW frequencies, rank every one of the swept authors
for each book by:

- **Burrows' Delta**: mean absolute difference of z-scores (z from the author profiles), averaged
  over the book's query chunks;
- **ENSC** (closed set): nearest shrunken centroids fitted on per-block frequencies, BOM-75's
  calibrated shrinkage, proportional priors; a book's score is the mean discriminant over its
  query chunks. A profile's blocks are recovered by cutting its masked tokens into as many equal
  consecutive pieces as it has 1,000-word blocks (masking shortens blocks unevenly, so the cut is
  approximate). ``fit`` is ``classic.ensc.ENSC.fit`` vectorised for 23,875 classes (tested equal);
- **General Imposters** (100 trials, half the features, cosine) on each book's 100 closest
  authors by Cosine Delta, against 500 seeded random profiles (the candidate excluded); authors
  outside the 100 keep their Cosine Delta order after them.

Reported per method: top-1 and top-10 shares, median rank, and the 70% bar (``sweep.usable_top1``),
beside the sweep's Cosine Delta and style-encoder results. Names and numbers only:
``data/sweep/older_methods.json``.

Usage::

    python -m sweep.older            # Mac; GI is the slow part (a few hours)
"""

from __future__ import annotations

import gzip
import json
import random
import sys

import numpy as np
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from sweep.calibrate import _load, distances
from sweep.index import WORK, path_of
from sweep.units import OUT

RESULT = OUT / "older_methods.json"


def ensc_fit(X: np.ndarray, y: np.ndarray, K: int, shrinkage: float, priors: str) -> dict:
    """``classic.ensc.ENSC.fit`` for integer labels ``0..K-1``, vectorised."""
    n, _ = X.shape
    counts = np.bincount(y, minlength=K).astype(float)
    sums = np.zeros((K, X.shape[1]))
    np.add.at(sums, y, X)
    centroids = sums / counts[:, None]
    overall = X.mean(axis=0)
    resid = X - centroids[y]
    s = np.sqrt((resid**2).sum(axis=0) / (n - K))
    s0 = float(np.median(s))
    if s0 == 0:
        s0 = float(s[s > 0].mean()) if np.any(s > 0) else 1.0
    m = np.sqrt(1.0 / counts - 1.0 / n)
    scale = m[:, None] * (s + s0)[None, :]
    d = (centroids - overall) / scale
    d = np.sign(d) * np.maximum(np.abs(d) - shrinkage, 0.0)
    prior = np.full(K, 1.0 / K) if priors == "uniform" else counts / n
    return {"shrunk": overall + scale * d, "sd": s + s0, "log_prior": np.log(prior)}


def ensc_discriminants(f: dict, Q: np.ndarray) -> np.ndarray:
    """(queries x classes) ``classic.ensc.ENSC.discriminants``."""
    a = f["shrunk"] / f["sd"]
    b = Q / f["sd"]
    d = (b**2).sum(1)[:, None] + (a**2).sum(1)[None, :] - 2 * b @ a.T
    return d - 2.0 * f["log_prior"][None, :]


def _blocks(unit: str, n: int, vocab: list[str]) -> np.ndarray:
    from collections import Counter

    from classic.features import relative_frequencies

    with gzip.open(path_of(unit), "rt", encoding="utf-8") as fh:
        toks = fh.read().split()
    n = max(1, min(n, len(toks)))
    cuts = np.linspace(0, len(toks), n + 1).astype(int)
    return np.stack([relative_frequencies(Counter(toks[a:b]), vocab)
                     for a, b in zip(cuts[:-1], cuts[1:], strict=True)])  # fmt: skip


def _rank(score: np.ndarray, true: int, lower: bool) -> int:
    s = score if lower else -score
    return int((s < s[true]).sum()) + 1


def run() -> int:
    from classic.imposters import general_imposters
    from metadata.config import classic_kwargs

    cfg = load_config()
    ss, sw = cfg["sweep_search"], cfg["sweep"]
    gi = classic_kwargs(cfg)["imposters"]
    ens = json.loads((OUT.parent / "benchmark" / "part2" / "benchmark.json").read_text())["ensc"]
    z = np.load(WORK / "mfw.npz")
    vocab = z["vocab"].tolist()
    mfw = _load("mfw.npz", "X")
    authors = pq.read_table(OUT / "authors.parquet").to_pylist()
    swept = [a["author"] for a in authors if f"profile:{a['author']}" in mfw]
    pos = {a: i for i, a in enumerate(swept)}
    nblk = {a["author"]: int(a["blocks"]) for a in authors}
    books = [a for a in authors if a["calibration_book"] and a["author"] in pos]
    gal = np.stack([mfw[f"profile:{a}"] for a in swept]).astype(np.float64)
    mean, std = gal.mean(axis=0), gal.std(axis=0, ddof=1)
    std[std == 0] = 1.0

    print(f"per-block frequencies for {len(swept):,} profiles ...", flush=True)
    rows, labels = [], []
    for i, a in enumerate(swept):
        b = _blocks(f"profile:{a}", nblk[a], vocab)
        rows.append(b)
        labels += [i] * len(b)
        if (i + 1) % 2000 == 0:
            print(f"  {i + 1:,}/{len(swept):,}", flush=True)
    Xb, yb = np.vstack(rows), np.array(labels)
    calib = {a["author"]: _blocks(f"calib_profile:{a['author']}", nblk[a["author"]], vocab)
             for a in books}  # fmt: skip

    rng = random.Random(derive_seed(ss["gi_pool_seed"], cfg))
    pool_ids = rng.sample(range(len(swept)), ss["gi_pool"] + 1)
    recs = []
    for k, a in enumerate(books):
        name, t = a["author"], pos[a["author"]]
        qs = sorted(u for u in mfw if u.startswith(f"calib_query:{name}:"))
        Q = np.stack([mfw[u] for u in qs]).astype(np.float64)
        g = gal.copy()
        g[t] = mfw[f"calib_profile:{name}"]
        zq, zg = (Q - mean) / std, (g - mean) / std
        burrows = np.stack([np.abs(zg - q).mean(axis=1) for q in zq]).mean(axis=0)
        cosine = distances(g, Q, "mfw", mean, std)
        keep = yb != t
        f = ensc_fit(np.vstack([Xb[keep], calib[name]]),
                     np.concatenate([yb[keep], np.full(len(calib[name]), t)]), len(swept),
                     ens["shrinkage"], "proportional")  # fmt: skip
        ensc = ensc_discriminants(f, Q).mean(axis=0)
        short = np.argsort(cosine)[: ss["gi_shortlist"]]
        gis = {}
        for c in short:
            imp = g[[p for p in pool_ids if p != c][: ss["gi_pool"]]]
            gis[int(c)] = float(np.mean([general_imposters(
                q, g[c], imp, feature_fraction=gi["feature_fraction"], trials=gi["trials"],
                distance=gi["distance"], seed=derive_seed(f"a57-gi:{name}:{j}:{c}", cfg))
                for j, q in enumerate(Q)]))  # fmt: skip
        order = sorted(gis, key=lambda c: (-gis[c], cosine[c]))
        if t in gis:
            gi_rank = order.index(t) + 1
        else:
            gi_rank = _rank(cosine, t, True)
        recs.append({"author": name, "book": a["calibration_book"], "chunks": len(qs),
                     "burrows_rank": _rank(burrows, t, True),
                     "cosine_rank": _rank(cosine, t, True),
                     "ensc_rank": _rank(ensc, t, True), "gi_rank": gi_rank,
                     "in_gi_shortlist": t in gis})  # fmt: skip
        r = recs[-1]
        print(
            f"  {k + 1}/{len(books)} {name[:30]}: Burrows {r['burrows_rank']}, Cosine "
            f"{r['cosine_rank']}, ENSC {r['ensc_rank']}, GI {r['gi_rank']}",
            flush=True,
        )
    n = len(recs)
    cal = json.loads((OUT / "calibration.json").read_text())
    summary = {}
    for m in ("burrows", "cosine", "ensc", "gi"):
        rk = [r[f"{m}_rank"] for r in recs]
        summary[m] = {"top1": sum(x == 1 for x in rk) / n, "top10": sum(x <= 10 for x in rk) / n,
                      "median_rank": float(np.median(rk)),
                      "usable": sum(x == 1 for x in rk) / n >= sw["usable_top1"]}  # fmt: skip
    summary["gi"]["shortlist_recall"] = sum(r["in_gi_shortlist"] for r in recs) / n
    summary["sweep_registered"] = {
        "mfw_cosine": {"top1": cal["top1"]["mfw"], "median_rank": cal["median_rank"]["mfw"]},
        "style_encoder": {"top1": cal["top1"]["style"], "median_rank": cal["median_rank"]["style"]},
    }
    RESULT.write_text(json.dumps({**stamp(), "swept_authors": len(swept), "books": n,
                                  "bar_top1": sw["usable_top1"], "summary": summary,
                                  "records": recs}, indent=1) + "\n")  # fmt: skip
    for m, v in summary.items():
        print(m, v)
    print(f"-> {RESULT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
