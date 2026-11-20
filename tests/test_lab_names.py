"""BOM-108: the name models put a name with its own list; the helpers do what they say."""

from lab.names import (
    cap_counts,
    design,
    lead,
    names_by_rule,
    norm,
    one_edit,
    skeleton,
    splice,
    splice_tables,
)


def test_norm_folds_diacritics_and_drops_signs():
    assert norm("ʾūr-Y⁺ahū") == "uryahu"
    assert norm("sꜣ-sbk") == "ssbk"
    assert norm("Kʼinich") == "kinich"


def test_skeleton_drops_vowels_and_merges_classes():
    assert skeleton("zarahemla") == "srml"
    assert skeleton("jacob") == skeleton("yakov") == "kp"


def test_names_by_rule_wants_capitals_inside_a_sentence_and_never_lower_case():
    text = "He met Lobaska there. Then Lobaska spoke of the Ohio and the ohio. Kedesh-naphtali."
    assert names_by_rule(text, {"then"}, 2, 3) == ["lobaska"]
    assert "naphtali" not in cap_counts(text)[2]


def test_design_puts_held_out_names_with_their_own_list():
    a = [x + y + z for x in ("ka", "ko", "ku") for y in ("ta", "to", "tu") for z in "aou"]
    b = [x + y + z for x in ("el", "il", "em") for y in ("is", "es", "ir") for z in "ei"]
    w = {"len_min": 3, "len_max": 9, "match_n": 10, "test_n": 5, "repeats": 5,
         "smoothing": 0.1, "interpolation": [0.6, 0.3, 0.1]}  # fmt: skip
    res = design({"a": a, "b": b}, {"t": ["kotu", "elis"]}, w, 1)
    assert res["mean_recall"] > 0.9
    assert res["targets"]["t"]["usual_set"] == {"kotu": "a", "elis": "b"}


def test_lead_needs_a_clear_gap():
    assert lead({"x": [0.6, 0.5, 0.7], "y": [0.2, 0.1, 0.3]}) == "x"
    assert lead({"x": [0.6, 0.3, 0.7], "y": [0.3, 0.1, 0.4]}) is None


def test_one_edit_and_splice():
    base = {"nephthalim", "lehabim", "moriah"}
    assert one_edit("morian", base)
    assert not one_edit("moriah", {"moriah"})
    pre, suf = splice_tables(base, 3)
    assert splice("nephabim", pre, suf, 3)
    assert not splice("zzzabim", pre, suf, 3)
    assert not splice("moriah", pre, suf, 3, own=1)
