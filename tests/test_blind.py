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
    units = {"ux": "x", "uy": "y", "uz": "z"}
    per = {"a": {"ux": 0.1, "uy": 0.5}, "b": {"ux": 0.2, "uy": 0.3},
           "c": {"ux": 0.1, "uy": 0.2, "uz": 0.3}}  # fmt: skip
    norm = {i: U.by_candidate(s, True, None, units) for i, s in per.items()}
    d = U.decoy_accuracy(norm, key)
    assert d["closed_set"] == {"decoys": 2, "correct": 1, "accuracy": 0.5}
    assert d["verification"] is None
    loo = U.leave_one_out(norm, key)
    assert loo["x"] == {"y": 1} and loo["y"] == {"x": 1}
    json.dumps(loo)


def test_best_unit_speaks_for_its_candidate() -> None:
    units = {"x1": "x", "x2": "x", "y1": "y"}  # control units have no candidate
    r = U.by_candidate({"x1": 0.9, "x2": 0.3, "y1": 0.5, "ctrl": 0.0}, True,
                       {"x1": "non_match", "x2": "match", "y1": "inconclusive"}, units)  # fmt: skip
    assert r["first"] == "x" and r["scores"] == {"x": 0.3, "y": 0.5}
    assert r["calls"] == {"x": "match", "y": "inconclusive"}  # controls never become candidates


def test_candidates_keep_their_reference() -> None:
    pool = {"small": [("s", [str(j) for j in range(14_000)])],
            "big": [("b", [str(j) for j in range(200_000)])]}  # fmt: skip
    d = S.pick_decoys(pool, {2000: 12}, random.Random(5), keep=10_000)
    assert sum(x["words"] for x in d if x["author"] == "small") <= 4_000
    assert S.split_need({2000: 7, 5000: 2}, 0.5) == ({2000: 4, 5000: 1}, {2000: 3, 5000: 1})


def test_untrained_ranges_follow_the_held_out_tail() -> None:
    units = [
        {"kind": "candidate", "docs": ["cand:a", "cand:b", "cand:c"],
         "holdout": {"first_word": 15_000}},
        {"kind": "candidate", "docs": ["cand:short"], "holdout": None},
        {"kind": "control", "docs": ["vol1", "vol2"], "holdout": {"first_word": 10}},
    ]  # fmt: skip
    words = {"cand:a": 10_000, "cand:b": 8_000, "cand:c": 6_000, "cand:short": 4_000}
    assert S.untrained(units, words) == {"cand:b": (5_000, 8_000), "cand:c": (0, 6_000)}
    assert S.trained_volumes(units) == {"vol1", "vol2"}


def test_no_decoy_overlaps_any_training_span() -> None:
    # two candidates whose models trained on the first 20,000 words of each text
    pool = {a: [(f"{a}-src{k}", [f"{a}{k}x{j}" for j in range(30_000)]) for k in range(2)]
            for a in ("alpha", "beta")}  # fmt: skip
    allowed = {s: (20_000, 30_000) for t in pool.values() for s, _ in t}
    allowed.pop("beta-src1")  # a text with no held-out tail gives no decoys
    d = S.pick_decoys(pool, {5000: 3, 2000: 4}, random.Random(9), keep=10_000, allowed=allowed)
    assert len(d) == 7
    for x in d:
        lo, hi = allowed[x["source"]]
        assert lo <= x["start"] and x["start"] + x["words"] <= hi
    spans = sorted((x["source"], x["start"], x["start"] + x["words"]) for x in d)
    for (s1, _, e1), (s2, b2, _) in zip(spans, spans[1:], strict=False):
        assert s1 != s2 or e1 <= b2  # never overlapping each other either
    with pytest.raises(SystemExit):  # 10,000 untrained words per text cannot hold three 5,000s
        S.pick_decoys({"alpha": pool["alpha"][:1]}, {5000: 3}, random.Random(0),
                      allowed={"alpha-src0": (20_000, 30_000)})  # fmt: skip


def test_candidate_texts_follow_their_unit() -> None:
    units = [
        {"kind": "candidate", "candidate": "Parley P. Pratt", "docs": ["cand:oc-ma__1-2"]},
        {"kind": "candidate", "candidate": "Oliver Cowdery", "docs": ["cand:oc-ma__3-4"]},
    ]
    pool = {"Oliver Cowdery": [("candidates/clean/oc-ma__1-2.txt", ["a"]),
                               ("candidates/clean/oc-ma__3-4.txt", ["b"]),
                               ("candidates/clean/oc-ma__9-9.txt", ["c"])]}  # fmt: skip
    got = S.by_unit(pool, units)
    assert got == {"Parley P. Pratt": [("candidates/clean/oc-ma__1-2.txt", ["a"])],
                   "Oliver Cowdery": [("candidates/clean/oc-ma__3-4.txt", ["b"])]}  # fmt: skip
