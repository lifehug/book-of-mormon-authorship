"""BOM-125: the cleaner, the measures and the known-answer arithmetic on small inputs."""

import random

from lab import dictated as D
from metadata import config

CFG = config.load()
T = CFG["lab"]["dictated"]
VOCAB = {"and", "the", "of", "it", "came", "to", "pass", "that", "in", "he", "went", "with"}


def doc(text: str) -> D.Doc:
    return D.Doc(text, VOCAB)


def test_clean_drops_gutenberg_frame_heads_and_hyphens() -> None:
    raw = (
        "Title\n*** START OF THE PROJECT GUTENBERG EBOOK X ***\n"
        "CHAPTER ONE\n12\nthe man went to the sea-\nside and came back.\n"
        "*** END OF THE PROJECT GUTENBERG EBOOK X ***\nlicense text\n"
    )
    out = D.clean(raw, CFG)
    assert "CHAPTER" not in out and "license" not in out and "Title" not in out
    assert "seaside and came back." in out


def test_clean_verse_lowercases_continuing_line_starts_only() -> None:
    out = D.clean("Of man's first\nDisobedience, and the fruit.\nSing Heavenly Muse", CFG, True)
    assert "disobedience" in out and "Sing" in out


def test_doc_marks_sentence_ends_and_clauses() -> None:
    d = doc("It came to pass; and he went. In the end!")
    assert d.raw == ["It", "came", "to", "pass", "and", "he", "went", "In", "the", "end"]
    assert d.mark[3] == "c" and d.mark[6] == "s" and d.mark[9] == "s"


def test_names_skip_sentence_starts_and_words_seen_lower_case() -> None:
    d = doc("Nephi went with Lehi. Went the king. Lehi came with nephi and the king King Lehi.")
    # Nephi is a sentence start in one place and lower case ("nephi") elsewhere: not counted
    assert D.names(d.raw, d.mark, T) == (1, 1)  # only Lehi (twice; its first use is mid-sentence)


def test_syllables_and_fk_direction() -> None:
    assert D.syllables("the") == 1 and D.syllables("beautiful") >= 3
    assert D.syllables("made") == 1


def test_mattr_value_is_one_for_all_distinct_and_low_for_repeats() -> None:
    assert D.mattr_value(list("abcdefgh"), 4) == 1.0
    assert D.mattr_value(["a", "b"] * 8, 4) == 0.5
    assert D.mattr_value(["a"], 4) != D.mattr_value(["a"], 4)  # nan: window longer than text


def test_callbacks_find_a_copied_stretch() -> None:
    rng = random.Random(1)
    base = [f"w{rng.randrange(10**6)}" for _ in range(200)]
    assert D.callbacks(base, 6) == 0.0
    copy = list(base)
    copy[120:132] = base[10:22]
    assert abs(D.callbacks(copy, 6) - 12 / 100) < 1e-9


def test_starts_are_even_and_short_text_has_none() -> None:
    assert D.starts(1000, 100, 0.0, 0.0, 3) == [0, 450, 900]
    assert D.starts(150, 100, 0.0, 0.0, 3) == [25]
    assert D.starts(90, 100, 0.0, 0.0, 3) == []


def test_ranks_spearman_and_quantile() -> None:
    assert D.ranks([10, 20, 20, 5]) == [2.0, 3.5, 3.5, 1.0]
    assert D.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert D.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    assert D.quantile([1, 2, 3, 4, 5], 0.5) == 3
    assert D.percentile_of([1, 2, 3, 4], 2) == 50.0


def test_plant_changes_exactly_the_planted_stretches() -> None:
    rng = random.Random(3)
    base = [f"b{i}" for i in range(1000)]
    donor = [f"k{i}" for i in range(500)]
    p = D.plant(base, donor, T, rng, "kjv")
    assert (
        sum(1 for a, b in zip(base, p, strict=True) if a != b) == T["plant_spans"] * T["plant_len"]
    )
    q = D.plant(base, donor, T, random.Random(3), "callback")
    assert q[: len(q) // 2] == base[: len(q) // 2]


def test_settings_are_in_the_config_and_not_in_the_code() -> None:
    assert T["bar_order"] > 0.5 and T["bar_names_rho"] > 0.5
    assert T["bar_names_ratio"][0] < 1 < T["bar_names_ratio"][1]
    assert T["outside_share"] > T["inside_share"]
    assert len(T["received"]) >= T["min_received"]
    assert set(T["known_grade_order"]) <= set(T["known_files"])
