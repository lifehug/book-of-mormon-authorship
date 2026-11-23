"""BOM-109 third design: settings overlay, features, the made-up passages and the judge check's
grading (lab.threeworlds3). No corpus text and no judge: every case is built by hand."""

import copy

import pytest

from lab import threeworlds2 as tw
from lab import threeworlds2_features as feat2
from lab import threeworlds3 as t3
from lab import threeworlds3_features as feat3
from metadata import config


@pytest.fixture(scope="module")
def cfg():
    return copy.deepcopy(config.load())


def test_every_analytic_value_is_in_the_config(cfg):
    s3 = t3.settings3(cfg)
    for k in ("check_seed", "second_reader", "synthetic_things", "real_check_n",
              "judge_bar_whose", "judge_bar_what", "judge_bar_place", "real_bar_whose",
              "real_kappa_whose", "real_bar_what", "real_min_both_s"):  # fmt: skip
        assert k in s3
    assert s3["judge_bar_whose"] == 0.85 and s3["real_bar_whose"] == 0.8
    assert s3["check_seed"] != cfg["lab"]["three_worlds2"]["seed"]


def test_overlay_keeps_second_design_values_and_adds_texts(cfg):
    before = copy.deepcopy(cfg)
    c3 = t3.cfg3(cfg)
    assert cfg == before  # not mutated
    s = tw.settings(c3)
    assert s["seed"] == cfg["lab"]["three_worlds2"]["seed"]  # same mention samples
    assert s["judge_bar_place"] == 0.85
    assert "roys_chumayel_1933" in s["texts"]
    assert set(cfg["lab"]["three_worlds2"]["texts"]) < set(s["texts"])


def test_features_keep_the_second_design_and_add_kirchhoff():
    assert set(feat2.FEATURES) < set(feat3.FEATURES)
    assert set(feat3.FEATURES) - set(feat2.FEATURES) == {"ball_game", "chinampas"}
    for fid, spec in feat2.FEATURES.items():
        assert feat3.FEATURES[fid][:4] == spec[:4]  # label, topic, kind, markers unchanged
    assert t3.provenance()["unresolved"] == []
    cov = feat3.kirchhoff_coverage()
    assert cov["group_I_traits"] == 37 and "pyramids" in cov["features_with_kirchhoff"]


def test_feature_swap_restores_the_second_design():
    n = len(tw.MARKERS)
    with t3.features3():
        assert tw.feat is feat3 and "ball_game" in tw.MARKERS
        _sp, hits = tw.find_markers("they played tlachtli in the ball-court")
        assert [f for f, _a, _b in hits].count("ball_game") == 2
    assert tw.feat is feat2 and len(tw.MARKERS) == n
    _sp, hits = tw.find_markers("they played tlachtli")
    assert not hits


def test_made_up_passages_are_fresh(cfg):
    syn = t3.synthetic(cfg)
    assert len(syn) == 130 and len({r["id"] for r in syn}) == 130
    old = {r["passage"] for r in tw.synthetic(cfg)}
    assert not old & {r["passage"] for r in syn}
    assert sum(r["key"]["whose"][0] == "S" for r in syn) == 80
    assert all("[[" in r["passage"] for r in syn)


def _meta(cfg, real=()):
    return {"synthetic": t3.synthetic(cfg), "real_check": list(real)}


def _key(r):
    return f"{r['key']['whose'][0]},{r['key']['what'][0]},{r['key']['where'][0]}"


def test_grading_as_the_score_reads(cfg):
    meta = _meta(cfg)
    key = {r["id"]: _key(r) for r in meta["synthetic"]}
    g = t3.judge_check(meta, key, cfg, log=False)["synthetic"]
    assert g["whose_binary_share"] == g["what_fair_share"] == g["place_share"] == 1.0
    naive = {r["id"]: "S,H,M" for r in meta["synthetic"]}
    g = t3.judge_check(meta, naive, cfg, log=False)["synthetic"]
    assert g["whose_binary_share"] < 0.85 and g["what_fair_share"] < 0.85
    # the second design's misses: fair answers off the primary key do not count against
    fair = dict(key)
    for r in meta["synthetic"]:
        if r["frame"] == "n_future":
            fair[r["id"]] = "P,B,M"
        elif r["frame"] == "n_quoted":
            fair[r["id"]] = "O,H,E"
        elif r["frame"] == "e_author_own":
            fair[r["id"]] = "A,H,U"
        elif r["frame"] == "n_have":
            fair[r["id"]] = "S,H,U"  # cannot tell counts as main
    g = t3.judge_check(meta, fair, cfg, log=False)["synthetic"]
    assert g["whose_binary_share"] == g["what_fair_share"] == g["place_share"] == 1.0
    assert g["full_what_five_way_share"] < 1.0  # the full figure is still reported
    # S against A on an essay frame is a miss
    sa = dict(key)
    for r in meta["synthetic"]:
        if r["frame"] in ("e_have", "e_compare_have"):
            sa[r["id"]] = "A,X,M"
    g = t3.judge_check(meta, sa, cfg, log=False)["synthetic"]
    assert g["whose_binary_right"] == 110


def test_kappa():
    assert t3.kappa([(True, True), (False, False)]) == 1.0
    assert t3.kappa([(True, False), (False, True)]) == -1.0
    assert t3.kappa([]) is None
    pairs = [(True, True)] * 18 + [(True, False), (False, True)]
    assert t3.kappa(pairs) < 0.6  # nearly all S: raw agreement 0.9, kappa about -0.05


def test_real_bars(cfg):
    meta = _meta(cfg, [f"t|horses|{i}" for i in range(40)])
    key = {r["id"]: _key(r) for r in meta["synthetic"]}
    ans = dict(key)
    for i, rid in enumerate(meta["real_check"]):
        a = "S,H,M" if i < 25 else "A,X,M"
        ans[rid] = a
        ans[rid + "#opus"] = a
    res = t3.judge_check(meta, ans, cfg, log=False)
    assert res["passed"] and res["real"]["whose_binary_kappa"] == 1.0
    # a second reader who calls every essay mention A misses whose
    for rid in meta["real_check"][:12]:
        ans[rid + "#opus"] = "A,X,M"
    res = t3.judge_check(meta, ans, cfg, log=False)
    assert not res["passed"] and not res["bars"]["real_whose"]
    # one open answer: not complete, never passed
    ans2 = {k: v for k, v in ans.items() if k != meta["real_check"][0] + "#opus"}
    assert t3.judge_check(meta, ans2, cfg, log=False)["state"] in ("open",)


def test_too_few_both_s_counts_as_missed(cfg):
    meta = _meta(cfg, [f"t|horses|{i}" for i in range(40)])
    ans = {r["id"]: _key(r) for r in meta["synthetic"]}
    for i, rid in enumerate(meta["real_check"]):
        a = "S,H,M" if i < 5 else "O,H,M"
        ans[rid] = ans[rid + "#opus"] = a
    res = t3.judge_check(meta, ans, cfg, log=False)
    assert res["real"]["both_s"] == 5 and not res["bars"]["real_what"] and not res["passed"]


def test_roys_cut(tmp_path, monkeypatch, cfg):
    s3 = t3.settings3(cfg)
    (tmp_path / "r.txt").write_text(
        f"PREFACE by Roys\n{s3['roys_start']}\nThe translation.\n{s3['roys_end']}\nNotes."
    )
    monkeypatch.setattr(t3, "FAST", tmp_path)
    got = t3.roys_text("r.txt", cfg)
    assert "translation" in got and "PREFACE" not in got and "Notes" not in got
    assert t3.roys_text("missing.txt", cfg) is None


def test_prompt_rule_and_parse():
    p = t3.prompt3("horses", "the Quenari", "they had [[horses]]")
    assert "The line between S and A" in p and "simulated judging" in p
    assert tw.parse_first("S,H,M") == ("S", "H", "M")


def test_parts_ways():
    ours = {"book_whole": "present", "agrees_with": ["near_east"],
            "world_values": {"mesoamerica": "absent"}}  # fmt: skip
    pub = [{"source": "Dale and Dale", "item": "A:1", "direction": "positive"},
           {"source": "Roper", "thing": "horse", "status": ["confirmed"]}]  # fmt: skip
    notes = t3.parts_ways(pub, ours)
    assert len(notes) == 2
    assert t3.parts_ways(pub, {**ours, "agrees_with": ["mesoamerica"],
                               "world_values": {}}) == []  # fmt: skip
