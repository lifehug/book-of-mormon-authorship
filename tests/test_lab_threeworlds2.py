"""BOM-109 second design: markers, parsing, stated values, worlds, siding, the gates
(lab.threeworlds2). No corpus text is needed: every case is built by hand."""

import copy
import json

import pytest

from lab import threeworlds2 as tw
from lab import threeworlds2_features as feat
from metadata import config


@pytest.fixture(scope="module")
def cfg():
    return copy.deepcopy(config.load())


def s_of(cfg):
    return tw.settings(cfg)


# ------------------------------------------------------------------ features and markers


def test_every_analytic_value_is_in_the_config(cfg):
    s = s_of(cfg)
    for k in ("sample_per_feature", "seed", "present_min_attr", "absent_min_words", "topic_min",
              "margin", "bootstrap", "composite_min", "judge_bar_whose", "judge_bar_what",
              "judge_bar_real", "known_resample_share"):  # fmt: skip
        assert k in s
    assert s["judge_bar_whose"] == 0.85 and s["judge_bar_what"] == 0.85
    assert s["judge_bar_real"] == 0.8 and s["known_resample_share"] == 0.9


def test_provenance_resolves_and_kinds_are_fixed():
    p = tw.check_provenance()
    assert p["unresolved"] == []
    assert set(p["by_kind"]) == set(feat.WORLDS)
    for fid, spec in feat.FEATURES.items():
        assert spec[2] in feat.WORLDS and spec[4], fid


def test_markers_phrases_case_and_long_s():
    text = (
        "The Mexicans had no horfes, but they grew Indian corn; the Turkey merchants sold turkeys."
    )
    _spans, hits = tw.find_markers(tw.clean(text))
    found = [f for f, _a, _b in hits]
    assert "maize" in found  # the phrase "Indian corn"
    assert found.count("turkeys") == 1  # "Turkey" the country is not the bird
    tw.inv.VOCAB.setdefault("horses", 10)
    tw.inv._MEMO.clear()
    _spans, hits = tw.find_markers(tw.clean(text))
    assert "horses" in [f for f, _a, _b in hits]  # long s read as s


def test_passage_marks_the_mention():
    text = "one two three horse four five six"
    spans, hits = tw.find_markers(text)
    (fid, a, b) = hits[0]
    p = tw.passage(text, spans, a, b, 2)
    assert p == "two three [[horse]] four five" and fid == "horses"


# ------------------------------------------------------------------ parsing


def test_parse_first_and_second_and_letters():
    assert tw.parse_first("S,H,M") == ("S", "H", "M")
    assert tw.parse_first("Answer: o , b , e") == ("O", "B", "E")
    assert tw.parse_first("I think the people have it") is None
    assert tw.parse_second("others has main") == ("O", "H", "M")
    assert tw.parse_second("OWNER: people STATE: other sense PLACE: unclear") == ("S", "W", "U")
    assert tw.parse_letter("B", "ABCDE") == "B" and tw.parse_letter("maybe", "YN") is None


def test_unanswered_and_unparseable_stay_open():
    got, st = tw.readings(["a", "b", "c"], {"a": "S,H,M", "b": "no idea"}, log=False)
    assert got == {"a": ("S", "H", "M")}
    assert st == {"asked": 3, "answered": 1, "open": 1, "unparseable": 1}


# ------------------------------------------------------------------ stated values


def _ment(fid, n, reads):
    return [{"id": f"t|{fid}|{i}", "feature": fid, "ref": None} for i in range(n)], {
        f"t|{fid}|{i}": r for i, r in enumerate(reads)
    }


def test_stated_present_needs_own_people_have_main(cfg):
    s = s_of(cfg)
    m, parsed = _ment("horses", 5, [("O", "H", "M")] * 4 + [("S", "H", "M")])
    assert tw.stated(m, parsed, 1000, s)["horses"] == "not stated"  # one own mention only
    m, parsed = _ment("horses", 3, [("S", "H", "M"), ("S", "H", "U"), ("S", "H", "E")])
    assert tw.stated(m, parsed, 1000, s)["horses"] == "present"  # unclear counts as main
    assert tw.stated(m, parsed, 1000, s, "elsewhere")["horses"] == "not stated"


def test_stated_absent_by_lack_or_by_long_topical_silence(cfg):
    s = s_of(cfg)
    m, parsed = _ment("horses", 1, [("S", "L", "M")])
    assert tw.stated(m, parsed, 1000, s)["horses"] == "absent"
    # long text, topic animals discussed (cattle given to the people 3 times), horses never
    m2, p2 = _ment("cattle", 3, [("S", "H", "M")] * 3)
    m3, p3 = _ment("horses", 4, [("O", "H", "M")] * 4)
    st = tw.stated(m2 + m3, {**p2, **p3}, s["absent_min_words"], s)
    assert st["horses"] == "absent" and st["cattle"] == "present"
    st = tw.stated(m2 + m3, {**p2, **p3}, s["absent_min_words"] - 1, s)
    assert st["horses"] == "not stated"  # too short to read silence


def test_brought_is_not_have(cfg):
    s = s_of(cfg)
    m, parsed = _ment("horses", 3, [("S", "B", "M")] * 3)
    assert tw.stated(m, parsed, 1000, s)["horses"] == "not stated"


# ------------------------------------------------------------------ worlds and siding


def test_row_value_and_equal_weight_pooling(cfg):
    s = s_of(cfg)
    assert tw.row_value(["present", "present", "absent"], s)[0] == "present"
    assert tw.row_value(["present", "absent"], s)[0] == "unsettled"
    assert tw.row_value(["present", "not stated"], s)[0] == "unsettled"
    c = copy.deepcopy(cfg)
    c["lab"]["three_worlds2"]["rows_pooled"] = {feat.NE: ["a", "b"], feat.MS: ["m"],
                                                feat.AM: ["x"], feat.CT: ["c"]}  # fmt: skip
    # row a: 3 texts present; row b: 1 present 1 absent -> shares 1.0 and 0.5 -> 0.75 present
    states = {f"a{i}": {"horses": "present"} for i in range(3)}
    states.update({"b0": {"horses": "present"}, "b1": {"horses": "absent"}})
    rows = {**{f"a{i}": (feat.NE, "a") for i in range(3)}, "b0": (feat.NE, "b"),
            "b1": (feat.NE, "b")}  # fmt: skip
    states = {n: {f: v.get(f, "not stated") for f in feat.FEATURES} for n, v in states.items()}
    v = tw.world_values(states, rows, c)["horses"][feat.NE]
    assert v["value"] == "present" and v["rows"]["b"]["value"] == "unsettled"


def test_toy_grid_attribution_sends_the_chronicle_home(cfg):
    toy = tw.toy_grid(s_of(cfg))
    assert toy["texts"]["chronicle"]["sides_with"] == feat.MS
    assert toy["texts"]["chronicle_word_count"]["sides_with"] != feat.MS
    assert toy["texts"]["bible_book"]["sides_with"] == feat.NE
    assert "firearms" in toy["kept"]  # a contemporary-only feature is kept


def test_known_passes_gage_rule_and_margin(cfg):
    s = s_of(cfg)
    sd = {"agree": {feat.NE: 3, feat.MS: 6, feat.AM: 5, feat.CT: 7}, "sides_with": feat.CT,
          "lead": 1, "resample_lead_share": {feat.CT: 0.6}}  # fmt: skip
    assert tw.known_passes("gage_english_american_1648", feat.MS, sd, s)
    assert not tw.known_passes("bernal_diaz_keatinge_1800", feat.MS, sd, s)
    sd = {"agree": {feat.NE: 1, feat.MS: 8, feat.AM: 7, feat.CT: 2}, "sides_with": feat.MS,
          "lead": 1, "resample_lead_share": {feat.MS: 0.95}}  # fmt: skip
    assert not tw.known_passes("bernal_diaz_keatinge_1800", feat.MS, sd, s)  # lead below margin


# ------------------------------------------------------------------ the judge check and the gate


def test_judge_check_key_passes_naive_fails(cfg):
    syn = tw.synthetic(cfg)
    assert len(syn) == s_of(cfg)["synthetic_n"] == 150
    meta = {"synthetic": syn, "real_check": ["r1", "r2"]}
    key = {r["id"]: ",".join(r["key"][k] for k in ("whose", "what", "where")) for r in syn}
    real = {"r1": "S,H,M", "r1#2": "people has main", "r2": "O,H,M", "r2#2": "others has main"}
    assert tw.judge_check(meta, {**key, **real}, cfg)["passed"]
    naive = {r["id"]: "S,H,M" for r in syn}
    assert not tw.judge_check(meta, {**naive, **real}, cfg)["passed"]
    assert not tw.judge_check(meta, key, cfg)["passed"]  # real mentions not read: incomplete


def _world_texts():
    """A hand-made grid: two references per world and one known text per world."""
    own = "S,H,M"
    lack = "S,L,M"
    refs = {
        feat.NE: {"horses": [own] * 2, "maize": [lack], "mounds": [lack], "firearms": [lack]},
        feat.MS: {"horses": [lack], "maize": [own] * 2, "mounds": [lack], "firearms": [lack]},
        feat.AM: {"horses": [lack], "maize": [own] * 2, "mounds": [own] * 2, "firearms": [lack]},
        feat.CT: {"horses": [own] * 2, "maize": [own] * 2, "mounds": [lack],
                  "firearms": [own] * 2},
    }  # fmt: skip
    texts, ments, answers = [], {}, {}

    def add(name, role, world, row, reads):
        texts.append({"name": name, "role": role, "world": world, "row": row,
                      "subject": "x"})  # fmt: skip
        sample = []
        for fid, rs in reads.items():
            for i, r in enumerate(rs):
                sample.append({"id": f"{name}|{fid}|{i}", "feature": fid, "ref": None})
                answers[f"{name}|{fid}|{i}"] = r
        ments[name] = {"words": 1000, "sample": sample}

    rows = {feat.NE: "native", feat.MS: "native", feat.AM: "s_antiquities", feat.CT: "sample"}
    for w, reads in refs.items():
        for k in range(2):
            add(f"ref_{w}_{k}", "reference", w, rows[w], reads)
    return texts, ments, answers, refs, add


def test_book_is_not_scored_when_diaz_misses(cfg, monkeypatch, tmp_path):
    c = copy.deepcopy(cfg)
    c["lab"]["three_worlds2"]["rows_pooled"] = {feat.NE: ["native"], feat.MS: ["native"],
                                                feat.AM: ["s_antiquities"],
                                                feat.CT: ["sample"]}  # fmt: skip
    c["lab"]["three_worlds2"]["margin"] = 1
    c["lab"]["three_worlds2"]["known_resample_share"] = 0.0
    texts, ments, answers, refs, add = _world_texts()
    # Diaz read the first design's way: the Spaniards' horses and guns credited to the natives
    add(
        "bernal_diaz_keatinge_1800",
        "known",
        feat.MS,
        None,
        {
            "horses": ["S,H,M"] * 2,
            "maize": ["S,H,M"] * 2,
            "firearms": ["S,H,M"] * 2,
            "mounds": ["S,L,M"],
        },
    )
    add("book_of_mormon", "book", None, None, {"horses": ["S,H,M"] * 2})
    syn = tw.synthetic(c)
    for r in syn:
        answers[r["id"]] = ",".join(r["key"][k] for k in ("whose", "what", "where"))
    meta = {"synthetic": syn, "real_check": ["r1"]}
    answers.update({"r1": "O,H,M", "r1#2": "others has main"})
    (tmp_path / "jobs_meta.json").write_text(json.dumps(meta))
    monkeypatch.setattr(tw, "CARD", tmp_path)
    monkeypatch.setattr(tw, "collect", lambda _cfg: (texts, ments))
    monkeypatch.setattr(tw, "all_answers", lambda: answers)
    res = tw.cmd_run(c)
    assert res["check"]["judge_check"]["passed"]
    assert res["check"]["diaz_passes"] is False and not res["check"]["passed"]
    assert isinstance(res["book_of_mormon"], str) and res["book_of_mormon"].startswith("not")
    # read with attribution, the same chronicle passes and the book is scored
    for f, reads in (("horses", ["O,H,M", "S,L,M"]), ("firearms", ["O,H,M", "S,L,M"])):
        ments["bernal_diaz_keatinge_1800"]["sample"] = [
            x for x in ments["bernal_diaz_keatinge_1800"]["sample"] if x["feature"] != f
        ]
        for i, r in enumerate(reads):
            ments["bernal_diaz_keatinge_1800"]["sample"].append(
                {"id": f"diaz2|{f}|{i}", "feature": f, "ref": None}
            )
            answers[f"diaz2|{f}|{i}"] = r
    res = tw.cmd_run(c)
    assert res["check"]["diaz_passes"] is True and res["check"]["passed"]
    assert isinstance(res["book_of_mormon"], dict) and "verdict" in res["book_of_mormon"]


def test_open_answers_block_the_book(cfg, monkeypatch, tmp_path):
    texts, ments, answers, _refs, add = _world_texts()
    add("bernal_diaz_keatinge_1800", "known", feat.MS, None, {"maize": ["S,H,M"] * 2})
    del answers["ref_mesoamerica_0|maize|0"]
    (tmp_path / "jobs_meta.json").write_text(json.dumps({"synthetic": [], "real_check": []}))
    monkeypatch.setattr(tw, "CARD", tmp_path)
    monkeypatch.setattr(tw, "collect", lambda _cfg: (texts, ments))
    monkeypatch.setattr(tw, "all_answers", lambda: answers)
    res = tw.cmd_run(cfg)
    assert res["check"]["references_open"] == ["ref_mesoamerica_0"]
    assert res["book_of_mormon"].startswith("not scored")
