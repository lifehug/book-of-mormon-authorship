"""Amendment 43: candidate samples lose every word inside a run shared with the Book of Mormon."""

from alm.candidates import drop_bom_overlap


def test_shared_runs_are_dropped_and_the_rest_kept():
    grams = {("and", "it", "came", "to")}
    words = "Behold, and it came to pass that I wrote".split()
    assert drop_bom_overlap(words, grams, 4) == ["Behold,", "pass", "that", "I", "wrote"]
    assert drop_bom_overlap(words, set(), 4) == words
