"""BOM-32: one size's blind thresholds and outputs come home from its pod and merge in by size."""

import importlib.util
import json
from pathlib import Path

import pytest

from blind.thresholds import add_size, merge_doc

ROOT = Path(__file__).resolve().parents[1]


def _doc(alm: dict, sizes: list[str], gi: float = 1.0, commit: str = "aaa") -> dict:
    return {"git_commit": commit, "config_sha256": "c", "sizes": sizes, "rate": 0.05,
            "thresholds": {"general_imposters": {"match": gi}, "style": {"match": 1.0},
                           "ensc": {}, "alm": alm}}  # fmt: skip


def test_merge_doc_keeps_other_sizes_and_never_erases():
    old = _doc({"pilot": {"match": 0.03}, "base": {"match": 0.06}}, ["pilot", "base"])
    new = _doc({"mid": {"match": 0.05}}, ["mid"], commit="bbb")
    m = merge_doc(old, new)
    assert m["sizes"] == ["pilot", "base", "mid"]
    assert m["thresholds"]["alm"] == {"pilot": {"match": 0.03}, "base": {"match": 0.06},
                                      "mid": {"match": 0.05}}  # fmt: skip
    # a size the new run could not compute (null) leaves the old value alone
    m2 = merge_doc(m, _doc({"base": None}, ["base"]))
    assert m2["thresholds"]["alm"]["base"] == {"match": 0.06}
    assert merge_doc(None, new) is new


def test_add_size_takes_only_that_size_from_the_pod():
    local = _doc({"pilot": {"match": 0.03}, "base": {"match": 0.06}}, ["pilot", "base"], gi=1.0)
    pod = _doc({"pilot": {"match": 9.9}, "base": {"match": 9.9}, "mid": {"match": 0.05}},
               ["pilot", "base", "mid"], gi=0.5, commit="pod")  # fmt: skip
    m = add_size(local, pod, "mid")
    assert m["thresholds"]["general_imposters"] == {"match": 1.0}  # the Mac's own
    assert m["thresholds"]["alm"]["pilot"] == {"match": 0.03}
    assert m["thresholds"]["alm"]["mid"]["match"] == 0.05
    assert m["thresholds"]["alm"]["mid"]["computed"]["git_commit"] == "pod"
    assert m["git_commit"] == "aaa" and m["sizes"] == ["pilot", "base", "mid"]
    with pytest.raises(ValueError):
        add_size(local, _doc({}, []), "mid")


def test_blind_merge_adds_one_output_without_touching_the_rest(tmp_path):
    spec = importlib.util.spec_from_file_location("cp", ROOT / "scripts/candidates_pod.py")
    cp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cp)
    (tmp_path / "data/blind").mkdir(parents=True)
    local_th = _doc({"pilot": {"match": 0.03}, "base": {"match": 0.06}}, ["pilot", "base"])
    (tmp_path / cp.BLIND_TH).write_text(json.dumps(local_th))
    local_m = {"sizes": ["base", "pilot"], "methods": ["alm", "classic"],
               "sha256": {"data/blind/outputs/classic.json": "c1",
                          "data/blind/outputs/alm_base.json": "b1"}}  # fmt: skip
    (tmp_path / cp.BLIND_MANIFEST).write_text(json.dumps(local_m))
    out_rel = "data/blind/outputs/alm_mid.json"
    pod_m = {"sizes": ["base", "mid", "pilot"], "methods": ["alm", "classic"],
             "sha256": {"data/blind/outputs/classic.json": "STALE", out_rel: "m1"}}  # fmt: skip
    pod_th = _doc({"mid": {"match": 0.05}}, ["mid"], commit="pod")
    cp.blind_merge("mid", pod_th, pod_m, out_rel, root=tmp_path)
    m = json.loads((tmp_path / cp.BLIND_MANIFEST).read_text())
    assert m["sha256"] == {"data/blind/outputs/classic.json": "c1",
                           "data/blind/outputs/alm_base.json": "b1", out_rel: "m1"}  # fmt: skip
    assert m["sizes"] == ["base", "mid", "pilot"]
    th = json.loads((tmp_path / cp.BLIND_TH).read_text())
    assert set(th["thresholds"]["alm"]) == {"pilot", "base", "mid"}
