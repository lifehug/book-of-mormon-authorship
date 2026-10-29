"""BOM-43: the power analysis's floor rule and blocks."""

from eval import power


def test_floor_is_smallest_size_from_which_all_larger_pass():
    c = {"points": {"1000": {"m": 0.9}, "2000": {"m": 0.7}, "5000": {"m": 0.85},
                    "10000": {"m": 0.95}}}  # fmt: skip
    assert power.floor(c, "m", 0.8) == 5000  # 1000 passes, but 2000 dips below
    assert power.floor({"points": {"1000": {"m": 0.5}}}, "m", 0.8) is None
    assert power.floor({"points": {"1000": {"m": None}, "2000": {"m": 0.9}}}, "m", 0.8) == 2000


def test_blocks_are_whole_thousands():
    toks = [str(i) for i in range(2500)]
    bs = power.blocks(toks)
    assert [len(b) for b in bs] == [1000, 1000] and bs[1][0] == "1000"


def test_timesplit_baseline_needs_a_gap(monkeypatch):
    from eval import timesplit

    works = [{"year": 1790}, {"year": 1792}, {"year": 1801}, {"year": 1803}]
    monkeypatch.setattr("classic.corpus_run.eligible", lambda cfg: {"a": works, "b": works[:2]})
    out = timesplit.baseline_authors({"timesplit": {"min_gap_years": 7}})
    assert list(out) == ["a"]  # b has no 7-year gap
    assert [w["year"] for w in out["a"]["early"]] == [1790, 1792]
