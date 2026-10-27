"""CER calibration (BOM-14): the fitted model recovers a known relation."""

import json
import random
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ocr_fix import calibrate


def test_fit_recovers_relation(tmp_path: Path, monkeypatch) -> None:
    rng = random.Random(1)
    rows = []
    for i in range(300):
        f = {k: rng.random() for k in calibrate.FEATURES}
        cer = float(np.exp(-4 + 2 * f["single_letter_rate"]) - calibrate.OFFSET)
        rows.append({"ocr_id": str(i), **f, **{t: cer for t in calibrate.TARGETS}})
    gt = tmp_path / "gt.parquet"
    pq.write_table(pa.Table.from_pylist(rows), gt)
    monkeypatch.setattr(calibrate, "GROUNDTRUTH", gt)
    monkeypatch.setattr(calibrate, "MODEL", tmp_path / "m.json")
    calibrate.fit()
    m = json.loads((tmp_path / "m.json").read_text())["cer_clean"]
    assert m["cv_mae"] < 1e-6 and m["cv_spearman"] > 0.99
