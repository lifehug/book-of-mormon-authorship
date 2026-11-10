"""Amendment 43: Book of Mormon quotations are dropped from candidate samples, nothing else."""

from alm.candidates import drop_quotations


def test_a_quoted_passage_is_dropped_and_the_rest_kept():
    passage = "and it came to pass that he".split()
    words = "Behold, and it came to pass that he wrote this".split()
    assert drop_quotations(words, [passage], 4) == ["Behold,", "wrote", "this"]
    assert drop_quotations(words, [], 4) == words
