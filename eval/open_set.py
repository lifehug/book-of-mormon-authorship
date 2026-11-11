"""The open-set check, corrected (BOM-69, Amendment 25, post hoc).

7's open-set criterion asks how often a method confidently names a candidate when the true author
is absent. The original computation (6.1 as built in ``eval.benchmark``) set the match threshold
at the 95th percentile of open-set negatives and counted negatives above it on held-out trials,
which is about 5% by construction for any method with continuous scores. The corrected check fixes
the threshold from the **positives**: the score that ``benchmark.open_set_accept`` (95%) of true
authors reach; a negative at or above it is a false match. Measured on two held-out folds of the
tests (threshold from one fold's positives, rate on the other fold's negatives), seed
``benchmark-open-set-fold``. A method passes with closed-set accuracy at least
``benchmark.pass_closed_set`` and this rate at most ``benchmark.max_open_set_fpr``. The original
number is reported beside it.

``rescore`` applies the corrected check to every result file with verification scores (General
Imposters in ``benchmark.json``; the ALM runs; the style embeddings) and writes one table. ENSC
keeps its own "none" answer, which already measures the intended rate; the Deltas have no
verification score.

Usage::

    python -m eval.open_set rescore   # -> data/benchmark/open_set.json
    python -m eval.open_set rescore --part2   # BOM-75 -> data/benchmark/part2/open_set.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

DIR = Path("data/benchmark")


def original_fpr(neg: list[float], rate: float, seed: int) -> float:
    """The 6.1 computation as built (threshold from negatives), for reporting beside."""
    idx = list(range(len(neg)))
    random.Random(seed).shuffle(idx)
    half = len(idx) // 2
    out = []
    for cal, ev in ((idx[:half], idx[half:]), (idx[half:], idx[:half])):
        t = np.quantile([neg[i] for i in cal], 1 - rate)
        out.append(float(np.mean([neg[i] > t for i in ev])))
    return float(np.mean(out))


def corrected(pos: list[float], neg: list[float | None], cfg: dict) -> dict:
    """Paired by test (``neg`` may hold None where a test has no other candidate)."""
    bm = cfg["benchmark"]
    accept = bm["open_set_accept"]
    pairs = [(p, n) for p, n in zip(pos, neg, strict=True) if n is not None]
    idx = list(range(len(pairs)))
    random.Random(derive_seed("benchmark-open-set-fold", cfg)).shuffle(idx)
    half = len(idx) // 2
    rates = []
    for cal, ev in ((idx[:half], idx[half:]), (idx[half:], idx[:half])):
        t = np.quantile([pairs[i][0] for i in cal], 1 - accept)
        rates.append(float(np.mean([pairs[i][1] >= t for i in ev])))
    return {"threshold": float(np.quantile([p for p, _ in pairs], 1 - accept)),
            "open_set_fpr": float(np.mean(rates)), "tests": len(pairs)}  # fmt: skip


def wilson(k: float, n: int, z: float = 1.959964) -> list[float] | None:
    """95% Wilson score interval for k successes in n trials (Amendment 47)."""
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def with_intervals(row: dict, n_closed: int) -> dict:
    """Amendment 47: every rate with its 95% Wilson interval (FPR over the paired tests)."""
    out = dict(row)
    out["closed_set_ci95"] = wilson(row["closed_set"] * n_closed, n_closed)
    if row.get("open_set_fpr") is not None and row.get("tests"):
        out["open_set_fpr_ci95"] = wilson(row["open_set_fpr"] * row["tests"], row["tests"])
    out["n_closed"] = n_closed
    return out


def verdict(closed: float, pos: list, neg: list, cfg: dict, orig_seed: int) -> dict:
    bm = cfg["benchmark"]
    c = corrected(pos, neg, cfg)
    return {"closed_set": closed, **c,
            "open_set_fpr_original": original_fpr([n for n in neg if n is not None],
                                                  bm["max_open_set_fpr"], orig_seed),
            "passes": closed >= bm["pass_closed_set"]
            and c["open_set_fpr"] <= bm["max_open_set_fpr"]}  # fmt: skip


def rescore(part2: bool = False) -> int:
    """Part 1's files, or with ``part2`` BOM-75's seven-task results (``part2/benchmark.json``,
    ``alm_*_p2.json``) with 95% Wilson intervals on every rate."""
    cfg = load_config()
    rows: dict[str, dict] = {}
    src = DIR / "part2" if part2 else DIR
    b = json.loads((src / "benchmark.json").read_text())
    recs = [r for rs in b["records"].values() for r in rs]
    closed = sum(r["general_imposters"] == r["author"] for r in recs) / len(recs)
    rows["general_imposters"] = verdict(closed, [r["gi_positive"] for r in recs],
                                        [r["gi_open_negative"] for r in recs], cfg,
                                        derive_seed("benchmark-gi-fold", cfg))  # fmt: skip
    for name in ("burrows_delta", "cosine_delta"):
        rows[name] = {"closed_set": b["verdict"][name]["closed_set"], "open_set_fpr": None,
                      "passes": None, "note": "no verification score (6.1)"}  # fmt: skip
    rows["ensc"] = {**b["verdict"]["ensc"], "note": "its own 'none' answer; unchanged"}
    n_gi = len(recs)
    part1 = sorted(DIR.glob("alm_*.json")) + sorted(DIR.glob("style_embed*.json"))
    files = sorted(DIR.glob("alm_*_p2.json")) if part2 else part1
    sizes = {"general_imposters": n_gi}
    for f in files:
        d = json.loads(f.read_text())
        if not isinstance(d.get("records"), dict):  # alm_candidates_*: not benchmark trials
            continue
        recs = [r for rs in d["records"].values() for r in rs]
        closed = sum(r["predicted"] == r["author"] for r in recs) / len(recs)
        rows[f.stem] = verdict(closed, [r["positive"] for r in recs],
                               [r["open_negative"] for r in recs], cfg,
                               derive_seed(cfg["alm"]["fold_seed"], cfg))  # fmt: skip
        sizes[f.stem] = len(recs)
    if part2:
        rows = {k: with_intervals(v, sizes.get(k, n_gi)) for k, v in rows.items()}
    out = src / "open_set.json"
    out.write_text(json.dumps({**stamp(), "methods": rows}, indent=1) + "\n")
    for k, v in rows.items():
        fpr, orig = v.get("open_set_fpr"), v.get("open_set_fpr_original")
        show = "-" if fpr is None else f"{fpr:.3f}"
        print(f"  {k:<22} closed {v['closed_set']:.3f}  FPR {show}  (original {orig})  "
              f"passes {v['passes']}")  # fmt: skip
    print(f"-> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["rescore"])
    ap.add_argument("--part2", action="store_true", help="BOM-75: seven-task results, intervals")
    a = ap.parse_args(argv)
    return rescore(a.part2)


if __name__ == "__main__":
    sys.exit(main())
