"""BOM-102: the chunker, features, MARC reading and Hebraism rules behave as the card says."""

from lab import translation as T

B = {"cognate_max_gap": 3, "if_and_max_words": 25, "poly_min_ands": 4, "poly_max_gap": 10}


def test_long_s_is_repaired_in_function_words():
    assert T.tokens("He fhall fay fo, himfelf.") == [
        "he",
        "shall",
        "fay",
        "so",
        ",",
        "himself",
        ".",
    ]


def test_chunks_are_even_and_full_size():
    toks = ("word " * 10000).split()
    ch = T.chunks(toks, 1000, 5, 0.1)
    assert len(ch) == 5 and all(len(c) == 1000 for c in ch)
    assert len(T.chunks(toks, 1000, None, 0.0)) == 10
    assert T.chunks(toks[:500], 1000, 5, 0.1) == []


def test_features_have_a_fixed_length():
    toks = T.tokens("And the man went , and he said : why ? " * 50)
    plain, arch = T.features(toks), T.features(toks, archaic=True)
    assert len(plain) == len(T.FUNCTION_WORDS) + len(T.SHAPE)
    assert len(arch) == len(plain) + len(T.ARCHAIC)
    assert not set(T.ARCHAIC) & set(T.FUNCTION_WORDS)


def test_marc_status_reads_041():
    f041 = {"tag": "041", "ind1": "1", "subfields": [["a", "eng"], ["h", "fre"]]}
    assert T.marc_status([f041]) == ("T", "fre")
    assert T.marc_status([{"tag": "240", "ind1": "1", "subfields": []}]) == ("U", None)
    assert T.marc_status([]) == ("N", None)
    assert T.title_lang("Paul and Virginia, translated from the French") == "fre"


def test_planted_examples_are_found_and_near_misses_are_not():
    host = "the day was fair . the men walked to the town . they bought bread . " * 300
    assert all(T.plant_check(host, B, 3).values())


def test_polysyndeton_counts_runs_within_a_sentence():
    assert T.polysyndeton(T.tokens("and a and b and c and d"), 4, 10) == 1
    assert T.polysyndeton(T.tokens("and a . and b and c and d"), 4, 10) == 0


def test_rates_are_per_ten_thousand_words():
    m = {"words": 20000, **{r: 0 for r in T.RULES}}
    m["came_to_pass"] = 10
    assert T.rates(m)["came_to_pass"] == 5.0


def test_equal_error_and_auc():
    assert T.auc([0.9, 0.8], [0.1, 0.2]) == 1.0
    assert 0.2 < T.equal_error([0.9, 0.8, 0.7], [0.1, 0.2, 0.3]) <= 0.7
