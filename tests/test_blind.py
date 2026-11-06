"""The blind run's sealing and unblinding (BOM-32; section 8)."""

import json
import random
from pathlib import Path

import pytest

from blind import seal as S
from blind import unblind as U


def _bom() -> list[dict]:
    return [{"chunk_id": f"narrator:{i:03d}:N:2000:000", "chunk_words": 2000,
             "text": " ".join(f"b{i}w{j}" for j in range(2000))} for i in range(8)] + [
            {"chunk_id": f"narrator:{i:03d}:N:5000:000", "chunk_words": 5000,
             "text": " ".join(f"c{i}w{j}" for j in range(5000))} for i in range(4)]  # fmt: skip


def _pool() -> dict:
    return {a: [(f"{a}-src{k}", [f"{a}{k}x{j}" for j in range(30_000)]) for k in range(2)]
            for a in ("alpha", "beta", "control:gamma")}  # fmt: skip


def test_round_trip_and_ratio(tmp_path: Path) -> None:
    bom = _bom()
    need = S.need_for(bom, 0.25)
    assert need == {2000: 2, 5000: 1}
    decoys = S.pick_decoys(_pool(), need, random.Random(3))
    assert len(decoys) == 3
    rows, key = S.seal(bom, decoys, random.Random(3))
    assert len(rows) == len(key) == 15 and {r["id"] for r in rows} == set(key)
    assert all(set(r) == {"id", "words", "text"} for r in rows)  # nothing says which kind
    by_id = {r["id"]: r["text"] for r in rows}
    for i, k in key.items():  # the key restores every chunk and decoy exactly
        if k["kind"] == "bom":
            assert by_id[i] == next(c["text"] for c in bom if c["chunk_id"] == k["chunk_id"])
        else:
            words = dict(_pool()[k["author"]])[k["source"]]
            assert by_id[i] == " ".join(words[k["start"] : k["start"] + k["words"]])


def test_decoys_never_overlap() -> None:
    pool = {"a": [("s", [str(j) for j in range(30_000)])]}
    d = S.pick_decoys(pool, {2000: 6}, random.Random(0))
    spans = sorted((x["start"], x["start"] + x["words"]) for x in d)
    assert all(e <= s2 for (_, e), (s2, _) in zip(spans, spans[1:], strict=False))
    with pytest.raises(SystemExit):
        S.pick_decoys(pool, {5000: 7}, random.Random(0))  # at most six fit


def test_key_outside_repo_and_hashes(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        S.outside_repo(S.ROOT / "data" / "key.json")
    bom = _bom()
    decoys = S.pick_decoys(_pool(), S.need_for(bom, 0.25), random.Random(1))
    rows, key = S.seal(bom, decoys, random.Random(1))
    kp, sealed, out = tmp_path / "k" / "key.json", tmp_path / "sealed.jsonl", tmp_path / "out"
    doc = S.write(rows, key, decoys, kp, sealed, out, {"config_sha256": "x"})
    assert kp.stat().st_mode & 0o777 == 0o600
    seal_text = (out / "seal.json").read_text() + (out / "withheld.json").read_text()
    assert not any(i in seal_text for i in key)  # committed files carry no ids
    assert U.verify(doc, kp, sealed, {"sha256": {}}) == []
    kp.write_text(kp.read_text() + " ")
    assert U.verify(doc, kp, sealed, {"sha256": {}}) == ["key does not match seal.json"]


def test_run_never_reads_the_key() -> None:
    src = (S.ROOT / "blind" / "run.py").read_text()
    assert "KEY" not in src and "key.json" not in src and ".bom-blind" not in src


def test_decoy_accuracy_and_leave_one_out() -> None:
    key = {"a": {"kind": "decoy", "author": "x"}, "b": {"kind": "decoy", "author": "y"},
           "c": {"kind": "bom", "chunk_id": "n:1"}}  # fmt: skip
    per = {"a": {"predicted": "x", "scores": {"x": 0.1, "y": 0.5}},
           "b": {"predicted": "x", "scores": {"x": 0.2, "y": 0.3}},
           "c": {"predicted": "x", "scores": {"x": 0.1, "y": 0.2, "z": 0.3}}}  # fmt: skip
    assert U.decoy_accuracy(per, key) == {"decoys": 2, "correct": 1, "accuracy": 0.5}
    loo = U.leave_one_out(per, key)
    assert loo["x"] == {"y": 1} and loo["y"] == {"x": 1}
    json.dumps(loo)


def test_candidates_keep_their_reference() -> None:
    pool = {"small": [("s", [str(j) for j in range(14_000)])],
            "big": [("b", [str(j) for j in range(200_000)])]}  # fmt: skip
    d = S.pick_decoys(pool, {2000: 12}, random.Random(5), keep=10_000)
    assert sum(x["words"] for x in d if x["author"] == "small") <= 4_000
    assert S.split_need({2000: 7, 5000: 2}, 0.5) == ({2000: 4, 5000: 1}, {2000: 3, 5000: 1})
