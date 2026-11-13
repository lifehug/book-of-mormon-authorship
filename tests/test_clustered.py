"""Amendment 55's sign test and Holm correction (eval.clustered)."""

from eval.clustered import _stat, holm, sign_p


def test_sign_p() -> None:
    assert sign_p(0, 0) == 1.0
    assert abs(sign_p(11, 2) - 0.0225) < 1e-3
    assert sign_p(5, 5) == 1.0


def test_holm_is_monotone_and_capped() -> None:
    adj = holm([0.01, 0.04, 0.03, 0.5])
    assert adj == [0.04, 0.09, 0.09, 0.5]


def test_statistics() -> None:
    x = {"a": 3.0, "b": 1.0, "c": 0.0}
    zs = {"a": (1.0, 1.0), "b": (0.0, 1.0), "c": (0.0, 2.0)}
    assert _stat(x, "raw", None) == 3.0
    assert _stat(x, "znorm", zs) == 2.0
    assert _stat(x, "zmargin", zs) == 1.0


def test_extension_tasks_split_in_draw_order(tmp_path, monkeypatch) -> None:
    import json

    from eval import part2_benchmark as pb

    f = tmp_path / "ext.json"
    f.write_text(json.dumps({"drawn": {"g": [{"author": str(i)} for i in range(8)]}}))
    cfg = {"part2_benchmark": {"extension": {"authors_per_genre": 8, "tasks_per_genre": 2,
                                             "out": str(f)}}}  # fmt: skip
    t = pb.ext_tasks(cfg)
    assert [a["author"] for a in t["p3_g_1"]] == ["0", "1", "2", "3"]
    assert [a["author"] for a in t["p3_g_2"]] == ["4", "5", "6", "7"]
