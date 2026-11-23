"""BOM-112: the Dale and Dale checklist is keyed by rule and its arithmetic reproduced."""

import json
import math
import re
from pathlib import Path

import pytest

from lab import dalechecklist as d
from lab import dalechecklist_coding as coding
from metadata import config


def test_toy_product_and_their_example():
    assert math.isclose(10 ** d.log10_product([0.5, 0.1, 0.02]), 0.001)
    assert d.sci(131 * math.log10(0.5)) == "3.67e-40"
    assert d.matches(math.log10(2.69e-151), 2.69e-151, 0.005)
    assert not d.matches(math.log10(2.0e-13), 4.0e-14, 0.005)


def test_posterior_is_prior_times_ratios():
    lg = d.posterior([0.1, 0.1], [10.0], 1e9)
    assert math.isclose(lg, 9 - 2 + 1)


FRAGMENT = """1. Political Correspondences
1.1 First feature of the
city
  Coe's standard: quoted words (p. 1).
  Analysis of correspondence: Specific. Likelihood = 0.02.
1.2 Second feature
  Coe's standard: words.
  Analysis: we do not think this merits a likelihood of 0.02, but Likelihood = 0.1.
Calculation of overall likelihood for political correspondences
Nine have a likelihood of 0.5.
"""


def test_items_split_label_ratio_and_stop_at_summary():
    rows = d._lines_with_pages(FRAGMENT, 99)
    head = re.compile(r"^\s{0,4}(?P<num>\d\.\d{1,2})\.?\s+(?P<label>[A-Z].*)$")
    got = d._items(rows[1:], head)
    assert [g["num"] for g in got] == ["1.1", "1.2"]
    assert got[0]["label_full"] == "First feature of the city"
    assert got[0]["ratio"] == 0.02
    assert got[1]["ratio"] == 0.1  # the last stated ratio, not the section summary's
    assert got[0]["page"] == 99


def test_footnote_numbers_do_not_start_items():
    text = "1. Horses existed\n Likelihood = 50.0.\n 42. A footnote line\n"
    text += "2. Wheat existed\n weight of 2.0\n"
    rows = d._lines_with_pages(text, 1)
    head = re.compile(r"^\s{0,4}(?P<num>\d{1,2})\.\s+(?P<label>[A-Z].*)$")
    got = d._items(rows, head, sequential=True)
    assert [g["num"] for g in got] == ["1", "2"]
    assert [g["ratio"] for g in got] == [50.0, 2.0]


def test_short_label_cuts_at_a_word():
    assert (
        d.short("“Capital” or leading city-state dominates a cluster", 20)
        == "Capital or leading ..."
    )


def test_coding_table_is_complete_and_valid():
    assert len(coding.ADDED) == 131
    assert len(coding.NEG_GROUP) == 18
    for v in coding.ADDED.values():
        assert v["near_east"] in coding.VALUES and v["generic"] in coding.VALUES
    for pat in coding.KEYWORDS.values():
        re.compile(pat)
    assert set(coding.FEATURE) == set(coding.KEYWORDS)


def test_candidates_rank_by_distinct_terms_without_overlap():
    text = " ".join(["filler"] * 50 + ["king", "throne", "palace"] + ["filler"] * 50 + ["king"])
    got = d.candidates(text, re.compile(r"\b(king|throne|palace)\b"), 10, 5, 2)
    assert len(got) == 2
    assert "throne" in got[0] or "throne" in got[1]


@pytest.mark.skipif(not (d.PDF.exists() or d.TEXT.exists()), reason="private paper not held")
def test_known_answer_on_the_paper():
    cfg = config.load()
    k = d.keyed(cfg)
    ka = d.known_answer(k["items"], cfg)
    assert ka["passed"]
    assert all(ka["counts_ok"].values())
    assert set(ka["discrepancies_in_the_paper"]) == {"military"}


# ------------------------------------------------------------------------------ second design


def _cfg(meaning=2, keyword=1):
    cfg = config.load()
    st = cfg["lab"]["dale_checklist"]
    st = {**st, "window_words": 10, "window_step": 5,
          "second_design": {**st["second_design"], "meaning_passages": meaning,
                            "keyword_passages": keyword}}  # fmt: skip
    return {**cfg, "lab": {**cfg["lab"], "dale_checklist": st}}


def test_second_design_settings_are_in_the_config():
    s2 = config.load()["lab"]["dale_checklist"]["second_design"]
    assert s2["keyword_passages"] == config.load()["lab"]["dale_checklist"]["passages_per_question"]
    assert s2["meaning_passages"] > 0 and 0 < s2["retrieval_bar"] <= 1
    assert set(s2["retrieval_markers"]) <= set(coding.FEATURE)


def test_meaning_picks_skip_overlaps_and_the_keyword_windows():
    scores = [0.9, 0.95, 0.1, 0.8, 0.2, 0.7]
    # size 10, step 5: neighbours overlap, two apart do not
    got = d.meaning_picks(scores, 10, 5, 2, taken=[3])
    assert got == [1, 5]  # 1 best; 0 and 2 overlap 1; 3 taken; 4 overlaps 3 and 5
    assert d.meaning_picks(scores, 10, 5, 5, taken=[]) == [1, 3, 5]


def test_retrieve_keeps_keyword_windows_and_adds_meaning_in_text_order():
    import numpy as np

    wins = [f"w{i} king" if i == 4 else f"w{i}" for i in range(8)]
    vecs = np.eye(8, dtype=np.float32)
    q = np.zeros(8, dtype=np.float32)
    q[0], q[7] = 1.0, 0.5
    got = d.retrieve(wins, vecs, q, re.compile(r"\bking\b"), _cfg())
    assert [(p["window"], p["how"]) for p in got] == [(0, "meaning"), (4, "keyword"),
                                                      (7, "meaning")]  # fmt: skip
    # no keyword rule: meaning alone
    assert [p["how"] for p in d.retrieve(wins, vecs, q, None, _cfg())] == ["meaning", "meaning"]


def test_retrieval_check_counts_marked_passages():
    cfg = _cfg()
    marks = cfg["lab"]["dale_checklist"]["second_design"]["retrieval_markers"]
    first, second_ = list(marks)[:2]
    shown = {first: [{"how": "meaning", "text": "x " + marks[first].upper() + " y"}],
             second_: [{"how": "keyword", "text": "nothing here"}]}  # fmt: skip
    r = d.retrieval_check(shown, cfg)
    assert r["shown"] == 1 and r["shown_by_keyword"] == 0 and r["items"] == len(marks)


def test_parse_reply():
    assert d.parse_reply("SUPPORTS\nSPECIFIC\n3") == {"verdict": "SUPPORTS", "passage": 3}
    assert d.parse_reply("**NOT_ADDRESSED**\nNONE\n0")["verdict"] == "NOT_ADDRESSED"
    assert d.parse_reply("CONTRADICTS") == {"verdict": "CONTRADICTS", "passage": 0}
    assert d.parse_reply("I think it supports") is None
    assert d.parse_reply("") is None


def _write(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _fake_out(tmp_path, monkeypatch):
    def fake(p):
        p = tmp_path / Path(p).name
        return p

    monkeypatch.setattr(d, "out", fake)


def test_check_c_scored_from_hand_made_answers(tmp_path, monkeypatch):
    _fake_out(tmp_path, monkeypatch)
    pos = [f"book_of_mormon|A:1.{i}" for i in range(1, 5)]
    neg = ["book_of_mormon|B:1", "book_of_mormon|B:2"]
    jobs, ans = tmp_path / "jobs.jsonl", tmp_path / "answers.jsonl"
    _write(jobs, [{"id": i, "prompt": "q"} for i in pos + neg])
    monkeypatch.setitem(d.ANSWERS, "second", (jobs, ans))
    replies = ["SUPPORTS\nSPECIFIC\n1"] * 3 + ["NOT_ADDRESSED\nNONE\n0"]
    _write(ans, [{"id": i, "reply": r} for i, r in zip(pos, replies, strict=True)])
    r = d.score_check(config.load(), "second")
    assert "refused" in r and r["open"] == 2  # negatives not answered yet
    with ans.open("a") as fh:
        fh.write(json.dumps({"id": neg[0], "reply": "SUPPORTS\nNONE\n2"}) + "\n")
        fh.write(json.dumps({"id": neg[1], "reply": "garbled"}) + "\n")
    r = d.score_check(config.load(), "second")
    assert "refused" in r and r["unreadable"] == [neg[1]]  # never counted as an answer
    assert (tmp_path / "dalechecklist_unparsed_check_second.jsonl").exists()
    with ans.open("a") as fh:  # the rerun's readable answer supersedes the logged one
        fh.write(json.dumps({"id": neg[1], "reply": "NOT_ADDRESSED\nNONE\n0"}) + "\n")
    r = d.score_check(config.load(), "second")
    assert r["positive"]["supports"] == 3 and r["positive"]["share"] == 0.75
    assert r["positive"]["met"] and not r["negative"]["met"] and not r["passed"]
    assert r["positive"]["not_supported"] == ["A:1.4"]


def test_controls_refused_until_check_c_passes(tmp_path, monkeypatch):
    _fake_out(tmp_path, monkeypatch)
    jobs = tmp_path / "jobs.jsonl"
    _write(jobs, [{"id": "book_of_mormon|A:1.1", "prompt": "q"}])
    monkeypatch.setitem(d.ANSWERS, "second", (jobs, tmp_path / "none.jsonl"))
    r = d.score_controls(config.load())
    assert r["refused"].startswith("check C")


# ------------------------------------------------------------------ third design (whole-book)


def test_third_design_settings_are_in_the_config():
    s3 = config.load()["lab"]["dale_checklist"]["third_design"]
    for key in ("section_words", "section_overlap_words", "max_items_per_question", "seed",
                "decoy_bar", "second_reader_kappa_bar", "reader_model", "second_reader_model",
                "location_words", "rule"):  # fmt: skip
        assert key in s3


def test_decoys_match_their_own_rule_and_are_not_checklist_items():
    assert len(coding.DECOY_FEATURE) == 20
    for i, feat in coding.DECOY_FEATURE.items():
        assert re.search(coding.DECOY_KEYWORDS[i], feat, re.I), i
        assert feat not in coding.FEATURE.values()


def test_sections_cover_the_text_with_overlap():
    text = " ".join(f"w{i}" for i in range(25_001))
    cut = d.sections(text, 10_000, 500)
    assert len(cut) == 3 and cut[0][0] == 0 and cut[-1][1] == 25_001
    for (_a0, b0), (a1, b1) in zip(cut, cut[1:], strict=False):
        assert a1 == b0 - 500 and b1 - a1 <= 10_500
    assert d.sections("a b c", 10, 2) == [(0, 3)]


def test_batches_hold_every_item_once_with_decoys_spread():
    real = [f"A:{i}" for i in range(149)]
    dec = [f"D:{i}" for i in range(20)]
    g = d.batches(real, dec, 45, 7)
    assert sorted(sum(g, [])) == sorted(real + dec) and len(g) == 4
    assert all(len(b) <= 45 for b in g)
    assert [sum(i.startswith("D:") for i in b) for b in g] == [5, 5, 5, 5]
    assert g == d.batches(real, dec, 45, 7)  # fixed by the seed


def test_parse_reply3():
    ok = "F01 | SUPPORTS | and they did build ships\nF02 | NOT_ADDRESSED |\nF03|contradicts|x y"
    p = d.parse_reply3(ok, 3)
    assert [v["verdict"] for v in p] == ["SUPPORTS", "NOT_ADDRESSED", "CONTRADICTS"]
    assert p[0]["location"] == "and they did build ships"
    assert d.parse_reply3("**F1** | **NOT ADDRESSED**", 1)[0]["verdict"] == "NOT_ADDRESSED"
    assert d.parse_reply3("F01 | SUPPORTS | x", 2) is None  # a feature left out
    assert d.parse_reply3("F01 | SUPPORTS | x\nF01 | NOT_ADDRESSED |", 1) is None
    assert d.parse_reply3("", 1) is None


def test_kappa():
    assert d.kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert d.kappa([True, True, False, False], [True, False, True, False]) == 0.0
    assert d.kappa([], []) is None


def _third_files(tmp_path, monkeypatch):
    _fake_out(tmp_path, monkeypatch)
    paths = {}
    for name in ("JOBS3_CHECK", "JOBS3_CHECK_SECOND", "JOBS3_CONTROLS", "JOBS3_CONTROLS_SECOND"):
        paths[name] = tmp_path / (name.lower() + ".jsonl")
        monkeypatch.setattr(d, name, paths[name])
    items = [{"id": "A:1.1", "ratio": 0.1, "appendix": "A"},
             {"id": "A:1.2", "ratio": 0.5, "appendix": "A"},
             {"id": "B:1", "ratio": 50, "appendix": "B"}]  # fmt: skip
    monkeypatch.setattr(d, "keyed", lambda cfg: {"items": items})
    return paths


def _reply(verdicts):
    return "\n".join(f"F{n:02d} | {v} | {'some words' if v != 'NOT_ADDRESSED' else ''}"
                     for n, v in enumerate(verdicts, 1))  # fmt: skip


def test_check_c_third_design_rule_and_guards(tmp_path, monkeypatch):
    p = _third_files(tmp_path, monkeypatch)
    batch = ["A:1.1", "D:1", "A:1.2", "B:1"]
    jobs = [{"id": f"book_of_mormon|s0{s}|b1", "prompt": "q", "items": batch} for s in (1, 2)]
    _write(p["JOBS3_CHECK"], jobs)
    _write(p["JOBS3_CHECK_SECOND"], jobs[:1])
    cfg = config.load()
    r = d.score_check3(cfg)
    assert "refused" in r and r["open"] == 2
    S, N, C = "SUPPORTS", "NOT_ADDRESSED", "CONTRADICTS"
    # section 1: A:1.1 yes, decoy no, A:1.2 no, B:1 contradicts; section 2: A:1.2 yes, B:1 yes
    _write(d.answers_for(p["JOBS3_CHECK"]),
           [{"id": jobs[0]["id"], "reply": _reply([S, N, N, C])},
            {"id": jobs[1]["id"], "reply": "garbled"}])  # fmt: skip
    r = d.score_check3(cfg)
    assert r["unreadable"] == [jobs[1]["id"]]
    assert d.write_retry3("check")["jobs3_check.retry1.jsonl"]["questions"] == 1
    _write(d.answers_for(p["JOBS3_CHECK"]).with_suffix(".retry1.jsonl"),
           [{"id": jobs[1]["id"], "reply": _reply([N, N, S, S])}])  # fmt: skip
    _write(d.answers_for(p["JOBS3_CHECK_SECOND"]),
           [{"id": jobs[0]["id"], "reply": _reply([S, N, N, N])}])  # fmt: skip
    r = d.score_check3(cfg)
    assert r["positive"]["supports"] == 2 and r["positive"]["met"]  # any section
    assert r["negative"]["supports"] == 1 and r["supported_and_contradicted"] == ["B:1"]
    assert r["decoys"]["rejection"] == 1.0 and r["decoys"]["met"]
    assert r["second_reader"]["kappa"] == 1.0 and r["passed"]
    # a reader who says yes to the decoy misses guard 1
    _write(d.answers_for(p["JOBS3_CHECK"]).with_suffix(".retry1.jsonl"),
           [{"id": jobs[1]["id"], "reply": _reply([N, S, S, S])}])  # fmt: skip
    r = d.score_check3(cfg)
    assert not r["decoys"]["met"] and not r["passed"]
    assert d.score_controls3(cfg)["refused"].startswith("check C")
