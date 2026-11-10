"""blind.unblind reads the sweep's output as blind.run writes it (2026-11-10: its "ids" is a count,
and the unwrap meant for the other scorers' per-id tables crashed the real unblinding)."""

import json

from blind import unblind as U


def test_sweep_output_shape_is_handled(tmp_path, monkeypatch):
    f = tmp_path / "sweep.json"
    f.write_text(
        json.dumps(
            {
                "method": "sweep",
                "size": None,
                "scores": {"file": "x.npz", "ids": 211, "authors": 23872},
            }
        )
    )
    seen = {}
    monkeypatch.setattr(U, "sweep_result", lambda path, key, split, cal: seen.setdefault("p", path))
    out = U.unblind([str(f)], {}, {"units": []}, {}, {"some": "calibration"}, {})
    assert str(seen["p"]) == "x.npz" and out["sweep"] == seen["p"]
    assert U.unblind([str(f)], {}, {"units": []}, {}, None, {}) == {}
