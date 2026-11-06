"""Calibration of the author sweep and its expected false leads (BOM-39, BOM-47; Amendment 28).

For each of the 200 calibration books, every swept author's distance to the book under each
signal: Cosine Delta on the MFW frequencies (z-scored on the author profiles) and cosine distance
between style vectors, each the mean over the book's query chunks. The book's author is
represented by their profile rebuilt without the book. Recorded per book and signal: the true
author's rank and the best false-match distance.

- **Usable** (6.6): the true author first in at least ``sweep.usable_top1`` of books under each
  signal separately; the either-signal reading is reported beside it.
- **Lead threshold**: the ``sweep.lead_percentile``-th percentile of best-false-match distances
  per signal; a lead is closer than both.
- **Expected false leads** (BOM-47): leave-one-out, thresholds from the other books, the count of
  non-true authors closer than both; mean, median and ``sweep.unremarkable_percentile``-th
  percentile.
- Spearman correlation of the two signals over authors (mean over books) and over best-false
  distances; the 100 authors (seed ``sweep.gate_seed``) for the blind plausibility gate.

Writes names and numbers only: ``data/sweep/calibration.json``.

Usage::

    python -m sweep.calibrate
"""

from __future__ import annotations

import json
import random
import sys

import numpy as np
import pyarrow.parquet as pq
from scipy.stats import spearmanr

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from sweep.index import WORK
from sweep.units import OUT


def _load(name: str, key: str) -> dict[str, np.ndarray]:
    z = np.load(WORK / name)
    return dict(zip(z["units"].tolist(), z[key], strict=True))


def distances(gallery: np.ndarray, queries: np.ndarray, kind: str, mean: np.ndarray | None = None,
              std: np.ndarray | None = None) -> np.ndarray:  # fmt: skip
    """Authors' mean distance over the query chunks: Cosine Delta (z-scored) or cosine."""
    if kind == "mfw":
        gallery, queries = (gallery - mean) / std, (queries - mean) / std
    g = gallery / np.maximum(np.linalg.norm(gallery, axis=1, keepdims=True), 1e-12)
    q = queries / np.maximum(np.linalg.norm(queries, axis=1, keepdims=True), 1e-12)
    return (1.0 - g @ q.T).mean(axis=1)


def loo_counts(d: dict[str, list[np.ndarray]], true: list[int], best: dict[str, np.ndarray],
               pct: float) -> list[int]:  # fmt: skip
    """Per book, non-true authors closer than both thresholds set from the other books."""
    out = []
    for i, t in enumerate(true):
        thr = {k: np.percentile(np.delete(best[k], i), pct) for k in best}
        hit = np.ones_like(d["mfw"][i], dtype=bool)
        for k in best:
            hit &= d[k][i] < thr[k]
        hit[t] = False
        out.append(int(hit.sum()))
    return out


def run() -> int:
    cfg = load_config()
    s = cfg["sweep"]
    mfw, sty = _load("mfw.npz", "X"), _load("style.npz", "V")
    authors = pq.read_table(OUT / "authors.parquet").to_pylist()
    swept = [a["author"] for a in authors if f"profile:{a['author']}" in mfw]
    pos = {a: i for i, a in enumerate(swept)}
    gal = {"mfw": np.stack([mfw[f"profile:{a}"] for a in swept]).astype(np.float64),
           "style": np.stack([sty[f"profile:{a}"] for a in swept]).astype(np.float64)}  # fmt: skip
    mean = gal["mfw"].mean(axis=0)
    std = gal["mfw"].std(axis=0, ddof=1)
    std[std == 0] = 1.0
    books = [a for a in authors if a["calibration_book"] and a["author"] in pos]
    d: dict[str, list[np.ndarray]] = {"mfw": [], "style": []}
    recs, true = [], []
    for a in books:
        name = a["author"]
        qs = sorted(u for u in mfw if u.startswith(f"calib_query:{name}:"))
        rec = {"author": name, "book": a["calibration_book"], "chunks": len(qs)}
        for kind, vecs, g in (("mfw", mfw, gal["mfw"]), ("style", sty, gal["style"])):
            g = g.copy()
            g[pos[name]] = vecs[f"calib_profile:{name}"]
            dist = distances(g, np.stack([vecs[u] for u in qs]).astype(np.float64), kind,
                             mean, std)  # fmt: skip
            others = np.delete(dist, pos[name])
            rec[f"{kind}_rank"] = int((others < dist[pos[name]]).sum()) + 1
            rec[f"{kind}_true"] = float(dist[pos[name]])
            rec[f"{kind}_best_false"] = float(others.min())
            d[kind].append(dist)
        recs.append(rec)
        true.append(pos[name])
    n = len(recs)
    top1 = {k: sum(r[f"{k}_rank"] == 1 for r in recs) / n for k in ("mfw", "style")}
    either = sum(r["mfw_rank"] == 1 or r["style_rank"] == 1 for r in recs) / n
    best = {k: np.array([r[f"{k}_best_false"] for r in recs]) for k in ("mfw", "style")}
    pct = s["lead_percentile"]
    counts = loo_counts(d, true, best, pct)
    rho_auth = [spearmanr(d["mfw"][i], d["style"][i])[0] for i in range(n)]
    rng = random.Random(derive_seed(s["gate_seed"], cfg))
    doc = {**stamp(), "swept_authors": len(swept), "books": n,
           "top1": top1, "top1_either": either,
           "usable": {"each_signal": all(v >= s["usable_top1"] for v in top1.values()),
                      "either_signal": either >= s["usable_top1"],
                      "rule": s["usable_top1"]},
           "median_rank": {k: float(np.median([r[f"{k}_rank"] for r in recs]))
                           for k in ("mfw", "style")},
           "lead_threshold": {k: float(np.percentile(best[k], pct)) for k in best},
           "expected_false_leads": {"mean": float(np.mean(counts)),
                                    "median": float(np.median(counts)),
                                    f"p{s['unremarkable_percentile']}": float(
                                        np.percentile(counts, s["unremarkable_percentile"])),
                                    "max": int(max(counts)), "per_book": counts},
           "spearman": {"over_authors_mean": float(np.mean(rho_auth)),
                        "over_best_false": float(spearmanr(best["mfw"], best["style"])[0])},
           "gate_sample": sorted(rng.sample(swept, s["gate_sample"])),
           "records": recs}  # fmt: skip
    out = OUT / "calibration.json"
    out.write_text(json.dumps(doc, indent=1) + "\n")
    e = doc["expected_false_leads"]
    print(f"{n} books, {len(swept):,} authors; top-1 MFW {top1['mfw']:.3f}, style "
          f"{top1['style']:.3f}, either {either:.3f}; usable {doc['usable']}; expected false "
          f"leads mean {e['mean']:.2f} median {e['median']:.0f}; -> {out}")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
