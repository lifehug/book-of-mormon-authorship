"""The exploratory check of Grunder's proposed sources against our searches."""

import csv

from eval.grunder_ranks import compare, entries


def test_entries_keeps_only_matched_rows(tmp_path) -> None:
    p = tmp_path / "g.csv"
    cols = ["entry", "author", "title", "edition_year", "catalog_match", "match_basis",
            "catalog_work_ids"]  # fmt: skip
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerow(dict(zip(cols, ["1", "A", "T", "1820", "same_year", "author+title", "x y"],
                            strict=True)))  # fmt: skip
        w.writerow(dict(zip(cols, ["2", "B", "U", "1900", "none", "", ""], strict=True)))
    got = entries(p)
    assert [e["entry"] for e in got] == ["1"] and got[0]["work_ids"] == ["x", "y"]


def test_compare_finds_a_higher_proposed_set() -> None:
    hi = [{"percentile": 90.0 + i, "stands_out": i > 7} for i in range(10)]
    lo = [{"percentile": 10.0 + i, "stands_out": False} for i in range(50)]
    c = compare(hi, lo)
    assert c["auc"] == 1.0 and c["rank_sum_greater_p"] < 0.001
    assert c["stand_out"] == {"proposed": [2, 10], "others": [0, 50]}
    assert compare(lo, hi)["auc"] == 0.0
