"""The linguistic dating classifier (BOM-29): features, bins, intervals."""

import numpy as np

from dating import classifier as C
from dating import features as F
from metadata.config import load


def _n(text: str) -> dict[str, int]:
    return {n: int(v) for n, v in zip(F.NAMES, F.counts(F.tokens(text)), strict=True) if v}


def test_fold_changes_letters_not_words():
    assert F.tokens("Hee ſaith vnto Iohn, VVhat doth") == ["hee", "saith", "unto", "iohn",
                                                         "what", "doth"]  # fmt: skip
    # one fold for every date: a modern spelling folds the same way
    assert F.tokens("very ivory") == F.tokens("uery iuory")


def test_grammatical_features():
    c = _n(
        "Thou knowest that he loveth thee. I know not; they do not. If it be so, he is come. "
        "An hundred men were walking. Mine eyes; they don't, the which doth seventieth teeth"
    )
    assert c["thou_st_verb"] == 1 and c["eth_verb"] == 1  # not "seventieth" or "teeth"
    assert c["verb_not"] == 1 and c["do_not"] == 1
    assert c["subjunctive_be"] == 1 and c["be_perfect"] == 1 and c["progressive"] == 1
    assert c["an_h"] == 1 and c["mine_thine_vowel"] == 1 and c["contracted_not"] == 1
    assert c["the_which"] == 1 and c["doth"] == 1


def test_feature_list_is_registered_size():
    assert len(F.NAMES) == len(set(F.NAMES)) == 61
    assert set(F.GROUPS.values()) == {"verb inflection", "pronoun forms", "auxiliary patterns",
                                      "relative clauses", "function-word forms"}  # fmt: skip


def test_bins():
    d = load()["dating"]
    e = C.bin_edges(d)
    assert e[0] == 1473 and e[1] == 1530 and e[-2] == 1820 and e[-1] == 1831
    assert len(e) - 1 == 31
    assert C.bin_of(1473, e) == 0 and C.bin_of(1830, e) == 30 and C.bin_of(1825, e) == 30


def test_interval_from_distribution():
    e = [1700, 1710, 1720, 1730]
    p = np.array([0.0, 1.0, 0.0])
    med, lo, hi = C.summary(p, e, 0.9)
    assert (med, lo, hi) == (1715.0, 1710.5, 1719.5)
    med, lo, hi = C.summary(np.array([0.5, 0.0, 0.5]), e, 0.9)
    assert lo < 1710 and hi > 1720


def test_segments_skip_ends_and_need_prose():
    assert C.chunks(9000, 2000) == [1, 2]
    assert C.chunks(5000, 2000) == [0, 1]
    d = {"min_function_share": 0.2}
    assert C.is_prose("the man and the king of a land".split(), d)
    assert not C.is_prose("m d h a s 12 m d".split(), d)


def test_lexical_model_cannot_read_grammar():
    ex = C.lexical_excluded()
    assert {"doth", "does", "unto", "which"} <= ex
    assert "makes" in ex  # MorphAdorner's spelling for "maketh"


def test_h3_call_on_segment_medians():
    d = load()["dating"]
    assert C.h3_call(np.array([1790.0, 1810.0, 1650.0]), d) == "H3a"
    assert C.h3_call(np.array([1600.0, 1700.5, 1820.0]), d) == "H3b"  # 1700 is in the early window
    assert C.h3_call(np.array([1790.0, 1650.0, 1750.0, 1745.0]), d) == "neither"
    assert C.h3_call(np.array([1790.0, 1650.0]), d) == "neither"  # half is not a majority
