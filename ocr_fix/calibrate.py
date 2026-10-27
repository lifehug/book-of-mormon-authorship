"""Estimated CER for every volume, and the 4.3 exclusion flag (BOM-14).

``ocr_fix.groundtruth`` measures CER directly for about two thousand volumes that have a keyed
twin. Every other volume gets an *estimate*: a linear model of measured CER on the proxy
metrics the cleaning run records for every document (``ocr_fix.clean.proxies``), fitted on
the ground-truth pairs. Its accuracy is published with it, cross-validated by fold, including
how often it puts a volume on the wrong side of ``corpus.ocr_max_cer``.

The flag is set, never acted on here: ``ocr_excluded`` marks a volume whose estimated CER of
the *cleaned* text exceeds the cutoff. Nothing is deleted, and stages that want the comparison
corpus filter on it. Keyed TCP text is not OCR and is never flagged. Chronicling America has no
keyed twin, so its estimates extrapolate from books; that is stated in the report, not hidden.
Harvard's own score (``ocr_score_gen``) is reported beside ours for its volumes, since 4.3
names "the source's quality score" first.

Usage::

    python -m ocr_fix.calibrate fit      # cross-validated; -> data/ocr_quality/calibration.json
    python -m ocr_fix.calibrate apply    # -> data/ocr_quality/volumes.parquet
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from metadata.catalog import read_rows
from metadata.config import load as load_config
from metadata.config import sha256_of_config
from ocr_fix.clean import PROXY

GROUNDTRUTH = Path("data/ocr_quality/groundtruth.parquet")
CLEANING = Path("data/ocr_quality/cleaning.parquet")
CATALOG = Path("data/catalog/catalog.parquet")
HARVARD = Path("data/catalog/institutional_books.jsonl")
MODEL = Path("data/ocr_quality/calibration.json")
OUT = Path("data/ocr_quality/volumes.parquet")
FEATURES = [*PROXY, "period_lexicon_rate"]
TARGETS = ["cer_clean", "cer_raw", "letter_cer_clean"]
FOLDS = 5


def _design(rows: list[dict]) -> np.ndarray:
    x = np.array([[r[f] for f in FEATURES] for r in rows], dtype=float)
    return np.hstack([np.ones((len(rows), 1)), x])


def _fit(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    return coef


def fit() -> int:
    cfg = load_config()
    cut = cfg["corpus"]["ocr_max_cer"]
    rows = pq.read_table(GROUNDTRUTH).to_pylist()
    out: dict = {"features": FEATURES, "cutoff": cut, "config_sha256": sha256_of_config()}
    for target in TARGETS:
        ok = [r for r in rows if r[target] is not None]
        x, y = _design(ok), np.array([r[target] for r in ok])
        order = list(range(len(ok)))
        random.Random(cfg["seed"]).shuffle(order)
        pred = np.empty(len(ok))
        for k in range(FOLDS):
            test = order[k::FOLDS]
            train = sorted(set(order) - set(test))
            pred[test] = _design([ok[i] for i in test]) @ _fit(x[train], y[train])
        err = np.abs(pred - y)
        side = (pred > cut) != (y > cut)
        ss = float(((y - y.mean()) ** 2).sum())
        out[target] = {
            "n": len(ok),
            "coef": _fit(x, y).tolist(),
            "cv_mae": float(err.mean()),
            "cv_r2": 1 - float(((pred - y) ** 2).sum()) / ss if ss else None,
            "cv_wrong_side_of_cutoff": float(side.mean()),
            "measured_median": float(np.median(y)),
            "measured_share_over_cutoff": float((y > cut).mean()),
        }
        t = out[target]
        print(
            f"{target:<17} n={t['n']:,}  CV MAE {t['cv_mae']:.3f}  R2 {t['cv_r2']:.2f}  "
            f"wrong side of {cut} {t['cv_wrong_side_of_cutoff']:.1%}  "
            f"measured median {t['measured_median']:.3f}, over cutoff "
            f"{t['measured_share_over_cutoff']:.1%}"
        )
    MODEL.write_text(json.dumps(out, indent=1))
    print(f"-> {MODEL}")
    return 0


def apply() -> int:
    model = json.loads(MODEL.read_text())
    cut = load_config()["corpus"]["ocr_max_cer"]
    rows = pq.read_table(CLEANING).to_pylist()
    x = _design(rows)
    est = {t: np.clip(x @ np.array(model[t]["coef"]), 0, 1) for t in TARGETS}
    harvard = {
        f"institutional_books:{r.get('barcode_src')}": r.get("ocr_score_gen")
        for r in read_rows(HARVARD)
    }
    measured = {r["ocr_id"]: r for r in pq.read_table(GROUNDTRUTH).to_pylist()}
    out = []
    for i, r in enumerate(rows):
        m = measured.get(r["work_id"], {})
        cer = m.get("cer_clean")
        est_clean = float(est["cer_clean"][i])
        out.append(
            {
                "work_id": r["work_id"],
                "source": r["source"],
                "est_cer_raw": float(est["cer_raw"][i]),
                "est_cer_clean": est_clean,
                "est_letter_cer_clean": float(est["letter_cer_clean"][i]),
                "measured_cer_clean": cer,
                "harvard_ocr_score": harvard.get(r["work_id"]),
                "extrapolated": r["source"] == "chronicling_america",
                "ocr_excluded": (cer if cer is not None else est_clean) > cut,
            }
        )
    schema = pa.schema(
        [
            ("work_id", pa.string()),
            ("source", pa.string()),
            ("est_cer_raw", pa.float64()),
            ("est_cer_clean", pa.float64()),
            ("est_letter_cer_clean", pa.float64()),
            ("measured_cer_clean", pa.float64()),
            ("harvard_ocr_score", pa.float64()),
            ("extrapolated", pa.bool_()),
            ("ocr_excluded", pa.bool_()),
        ]
    )
    table = pa.Table.from_pylist(out, schema=schema)
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), OUT)
    by: dict[str, list[int]] = {}
    for r in out:
        by.setdefault(r["source"], [0, 0])
        by[r["source"]][0] += 1
        by[r["source"]][1] += r["ocr_excluded"]
    for s, (n, x_) in sorted(by.items()):
        print(f"  {s:<22} {n:>8,} volumes  {x_:>8,} over {cut} ({x_ / n:.1%})")
    print(f"-> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fit")
    sub.add_parser("apply")
    a = ap.parse_args(argv)
    return fit() if a.cmd == "fit" else apply()


if __name__ == "__main__":
    sys.exit(main())
