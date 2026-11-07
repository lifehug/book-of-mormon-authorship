"""Time-locked model (BOM-27): registered sizes, schedule, selection helpers."""

import pytest

torch = pytest.importorskip("torch")  # the model extra; CI installs only the base packages

from metadata.config import load  # noqa: E402
from timelocked_lm.data import _author_key, _held_out  # noqa: E402
from timelocked_lm.train import GPT, TINY, lr_at, params  # noqa: E402


def test_registered_sizes():
    t = load()["timelocked_lm"]
    pilot = params(GPT(t["vocab_size"], t["context_length"], **t["pilot_shape"]))
    base = params(GPT(t["vocab_size"], t["context_length"], **t["base_shape"]))
    assert 120e6 <= pilot <= 130e6  # the 125M pilot
    assert 100e6 <= base <= 300e6  # 5.2's registered range


def test_forward_and_loss():
    m = GPT(100, 16, **TINY)
    x = torch.randint(0, 100, (2, 9))
    assert m(x[:, :-1]).shape == (2, 8, 100)
    assert 3 < m(x[:, :-1], x[:, 1:]).item() < 6  # about ln(100) at initialisation


def test_schedule():
    t = load()["timelocked_lm"]
    steps = 1000
    warm = int(steps * t["warmup_share"])
    assert lr_at(0, steps, t) < lr_at(warm - 1, steps, t) <= t["peak_lr"]
    assert abs(lr_at(steps, steps, t) - t["peak_lr"] * t["min_lr_share"]) < 1e-12


def test_helpers():
    assert _author_key("Gilbert J. Hunt") == "hunt, gilbert"
    assert _held_out("x:1", 7, 0.5) == _held_out("x:1", 7, 0.5)
    share = sum(_held_out(f"x:{i}", 7, 0.005) for i in range(100000)) / 100000
    assert 0.004 < share < 0.006
