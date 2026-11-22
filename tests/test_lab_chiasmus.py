"""BOM-107: the chiasmus detector finds a planted inverted repetition, counts nothing in a flat
text, and Edwards's chance formula matches his published values."""

import random

from lab.chiasmus import (
    candidates,
    edwards_l,
    edwards_p,
    resolve,
    shuffled,
    stem,
    units_of,
)
from metadata.config import load

CFG = load()


def filler(n: int, seed: int = 1) -> list[str]:
    rng = random.Random(seed)
    return [f"w{rng.randrange(10**6)}" for _ in range(n)]


def test_planted_chiasm_is_found_with_its_depth() -> None:
    s = filler(60)
    keys = ["alpha", "bravo", "charlie", "delta"]
    for p, k in zip([10, 12, 14, 16], keys, strict=True):
        s[p] = k
    for p, k in zip([22, 24, 27, 29], reversed(keys), strict=True):
        s[p] = k
    found = resolve(candidates(s, 15, 1, 3, 2))
    assert len(found) == 1
    assert found[0][0] == 4
    assert (found[0][2], found[0][3]) == (10, 29)


def test_parallel_order_is_not_a_chiasm() -> None:
    s = filler(60)
    keys = ["alpha", "bravo", "charlie"]
    for p, k in zip([10, 12, 14], keys, strict=True):
        s[p] = k
    for p, k in zip([22, 24, 27], keys, strict=True):  # same order: A B C ... A B C
        s[p] = k
    assert not candidates(s, 15, 1, 3, 2)


def test_a_flat_text_has_no_chiasm() -> None:
    assert not candidates(filler(500, 2), 40, 1, 3, 2)


def test_stem_joins_inflections() -> None:
    assert stem("loseth", CFG) == stem("lose", CFG)
    assert stem("findeth", CFG) == stem("find", CFG)
    assert stem("eyes", CFG) == stem("eye", CFG)


def test_units_drop_stopwords_and_split_on_punctuation() -> None:
    units, words = units_of("The blood of man; by man shall his blood be shed.", CFG)
    assert units == [["blood", "man"], ["man", "blood", "shed"]]
    assert words == 11


def test_shuffle_keeps_every_unit() -> None:
    units = [[f"a{i}"] for i in range(50)]
    out = shuffled(units, 10, random.Random(3))
    assert sorted(map(tuple, out)) == sorted(map(tuple, units))
    assert out != units


def test_edwards_chance_matches_the_published_values() -> None:
    assert edwards_l(1) == 1.0
    assert edwards_l(3) == 1 / 15
    # P = 1 - (1-L)^N: one N (about 350 opportunities) gives both of his published values
    assert abs(edwards_p(8, 365) - 0.00018) < 0.00002
    assert abs(edwards_p(7, 338) - 0.0025) < 0.0001


def test_parallel_mode_counts_the_same_order_not_the_inverted() -> None:
    s = filler(60)
    keys = ["alpha", "bravo", "charlie"]
    for p, k in zip([10, 12, 14], keys, strict=True):
        s[p] = k
    for p, k in zip([22, 24, 27], keys, strict=True):  # A B C ... A B C
        s[p] = k
    assert candidates(s, 15, 1, 3, 2, parallel=True)
    assert not candidates(s, 15, 1, 3, 2)
    t = filler(60)
    for p, k in zip([10, 12, 14], keys, strict=True):
        t[p] = k
    for p, k in zip([22, 24, 27], reversed(keys), strict=True):  # A B C ... C B A
        t[p] = k
    assert candidates(t, 15, 1, 3, 2) and not candidates(t, 15, 1, 3, 2, parallel=True)
