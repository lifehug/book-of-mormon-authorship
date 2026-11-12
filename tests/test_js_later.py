"""Amendment 54's quotation rule and slice dating (eval.js_later)."""

from eval.js_later import quotation_passages, span_years, year_of

Q = {"ngram": 3, "min_words": 5, "max_gap": 1}


def _grams(words: list[str]) -> set:
    return {tuple(words[i : i + 3]) for i in range(len(words) - 2)}


def test_quotation_needs_length_and_a_non_stock_run() -> None:
    book = "and it came to pass that nephi went forth into the wilderness".split()
    text = "lo it came to pass that nephi went forth said he".split()
    bom = _grams(book)
    # an 8-word shared run, not biblical, not stock: a quotation
    assert quotation_passages(text, bom, set(), set(), Q) == [
        "it came to pass that nephi went forth".split()
    ]
    # the same run as stock phrasing is kept
    assert quotation_passages(text, bom, set(), bom, Q) == []
    # biblical runs are never quotations
    assert quotation_passages(text, bom, bom, set(), Q) == []
    # a run shorter than min_words is kept
    assert quotation_passages("x that nephi went y".split(), bom, set(), set(), Q) == []


def test_slice_years_and_titles() -> None:
    assert year_of("Revelation, 1 November 1831-B [D&C 1]") == 1831
    assert year_of("Revelation, circa Summer 1832") == 1832
    secs = [{"token_start": 0, "tokens": 10, "year": 1830},
            {"token_start": 10, "tokens": 10, "year": 1831},
            {"token_start": 20, "tokens": 10, "year": 1834}]  # fmt: skip
    assert span_years(5, 10, secs) == [1830, 1831]
    assert span_years(20, 5, secs) == [1834, 1834]
