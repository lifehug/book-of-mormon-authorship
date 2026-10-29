"""BOM-54: the curated pseudo-biblical control's selection rule and helpers."""

from metadata import pseudo_biblical as pb


def test_rules_admit_every_named_edition():
    marks = {
        "hunt": {"came_to_pass": 0.0, "eth_est": 2.0, "thou": 1.1, "verse_marks": 35.0},
        "snowden": {"came_to_pass": 1.0, "eth_est": 1.6, "thou": 5.0, "verse_marks": 22.0},
        "linning": {"came_to_pass": 0.2, "eth_est": 7.5, "thou": 9.3, "verse_marks": 3.5},
    }
    th = pb.thresholds(marks, list(marks))
    assert th["verse_marks"] == 22.0 and th["diction"] == 3.1
    assert (th["thou"], th["eth_est"]) == (9.3, 7.5)
    for m in marks.values():
        assert pb.qualifies(m, th)
    hymnal = {"came_to_pass": 0.0, "eth_est": 0.5, "thou": 2.0, "verse_marks": 40.0}
    sermon = {"came_to_pass": 0.0, "eth_est": 3.0, "thou": 12.0, "verse_marks": 0.5}
    assert pb.qualifies(hymnal, th) == [] and pb.qualifies(sermon, th) == []


def test_score_reads_markers_and_kjv_share():
    grams = {hash("in the beginning god created the heaven and")}
    s = pb.score("And it came to pass that thou goest.\nIn the beginning God created the heaven "
                 "and the earth.", grams)  # fmt: skip
    assert s["came_to_pass"] > 0 and s["thou"] > 0 and s["eth_est"] > 0
    assert 0 < s["kjv_share"] < 1


def test_passages_skip_front_matter_and_spread():
    text = "x" * 100 + "".join(f"{i:05d}" for i in range(4000))
    ps = pb.passages(text, n=3, chars=50)
    assert len(ps) == 3 and not ps[0].startswith("x" * 50)
