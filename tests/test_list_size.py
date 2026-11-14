from collections import Counter

import numpy as np
import pytest

from eval.list_size import lists, scale_scores, similar_order
from metadata.config import load as load_config


def _authors(k: int = 6) -> dict:
    rng = np.random.default_rng(0)
    words = [f"w{i}" for i in range(40)]
    out = {}
    for j in range(k):
        p = rng.dirichlet(np.ones(40))
        out[f"a{j}"] = {
            "task": "t",
            "tests": [],
            "blocks": [Counter(rng.choice(words, 300, p=p)) for _ in range(4)],
        }
    return out


def test_lists_shape_and_determinism():
    cfg = load_config()
    cfg["list_size"] = {
        **cfg["list_size"],
        "sizes": [2, 4, 6],
        "draws_per_author": 5,
        "similar_mfw": 30,
    }
    au = _authors()
    a, b = lists(au, cfg), lists(au, cfg)
    assert a == b
    for name, by in a.items():
        assert len(by["random"][2]) == 5 and len(by["random"][6]) == 1
        for typ in ("random", "similar"):
            for n, ls in by[typ].items():
                assert all(name in x and len(x) == n and x == sorted(x) for x in ls)


def test_similar_order_excludes_self_and_covers_all():
    cfg = load_config()
    cfg["list_size"] = {**cfg["list_size"], "similar_mfw": 30}
    au = _authors()
    near = similar_order(au, cfg)
    for name, order in near.items():
        assert name not in order and sorted(order) == sorted(set(au) - {name})


def test_window_losses_matches_window_loss():
    torch = pytest.importorskip("torch")  # the model extra; CI installs only the base packages

    from alm.benchmark import window_loss, window_losses
    from timelocked_lm.train import GPT

    torch.manual_seed(0)
    m = GPT(50, 16, 1, 16, 2).eval()
    g = torch.Generator().manual_seed(1)
    tests = [torch.randint(0, 50, (n,), generator=g).tolist() for n in (40, 17, 9, 33)]
    many = window_losses(m, tests, 8, "cpu", rows=3)
    for ids, got in zip(tests, many, strict=True):
        assert np.allclose(got, window_loss(m, ids, 8, "cpu"), atol=1e-5)


def test_alm_ranks():
    from eval.list_size import _alm_ranks

    s = [{"a": -0.3, "b": -0.5, "c": -0.1}, {"a": -0.9, "b": -0.5, "c": -0.1}]
    assert _alm_ranks(s, "a", ["a", "b", "c"]) == [2, 1]
    assert _alm_ranks(s, "a", ["a", "c"]) == [1, 1]


def test_disjoint_passages():
    from eval.list_size import _disjoint

    w = ["blocks 84-88 of 112", "blocks 85-89 of 112", "blocks 89-93 of 112", "x blocks 1-5"]
    assert sorted(_disjoint(w)) == [0, 2, 3]


def test_scale_scores_removes_a_model_that_wins_everywhere():
    cohort = np.array([[0.0, -1.0], [0.2, -0.8], [np.nan, -0.9]])  # model 1 low on everyone
    x = np.array([[-0.3, -1.0]])  # model 0 well below its usual; model 1 at its usual
    assert x.argmin(axis=1)[0] == 1
    assert scale_scores(x, cohort).argmin(axis=1)[0] == 0
