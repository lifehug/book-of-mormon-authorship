"""Story skeletons (BOM-25): parsing, blocks, alignment and resuming."""

import json

import numpy as np

from metadata.config import load
from semantic import skeleton


def test_parse_events():
    assert skeleton.parse_events("NONE", 12) == []
    assert skeleton.parse_events("None.", 12) == []
    assert skeleton.parse_events("- a king dies\n- a son rules\nnote", 12) == [
        "a king dies",
        "a son rules",
    ]
    assert skeleton.parse_events("- a\n- b\n- c", 2) == ["a", "b"]
    assert skeleton.parse_events("I cannot read this", 12) is None


def test_cut_is_even_and_complete():
    words = [str(i) for i in range(4500)]
    blocks = skeleton.cut(words, 2000)
    assert len(blocks) == 3
    assert " ".join(blocks).split() == words
    assert max(len(b.split()) for b in blocks) <= 2000


def test_fast_score_equals_traceback():
    cfg = load()
    rng = np.random.default_rng(1)
    for _ in range(50):
        m = rng.random((rng.integers(1, 20), rng.integers(1, 20))) < 0.3
        assert abs(skeleton.sw_score(m, cfg) - skeleton.sw_align(m, cfg)["score"]) < 1e-9


def test_order_matters():
    cfg = load()
    cfg["skeleton"]["shuffles"] = 200
    eye = np.eye(30, dtype=np.float32)
    al = skeleton.compare((eye, eye, 0.9, 0, cfg))
    assert al["matched"] == 30 and al["order_p"] < 0.01


def test_resume_reads_only_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(skeleton, "EVENTS", tmp_path)
    rows = [
        {"block": 0, "blocks": 3, "status": "ok", "events": ["x"]},
        {"block": 1, "blocks": 3, "status": "retry"},
        *[{"block": 2, "blocks": 3, "status": "unparsed"}] * (skeleton.MAX_UNPARSED - 1),
    ]
    (tmp_path / "t.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    assert sorted(skeleton._rows("t")) == [0]  # a transient failure is not an answer
    with (tmp_path / "t.jsonl").open("a") as fh:
        fh.write(json.dumps({"block": 2, "blocks": 3, "status": "unparsed"}) + "\n")
    got = skeleton._rows("t")
    assert sorted(got) == [0, 2] and got[2]["unreadable"] and got[2]["events"] == []
