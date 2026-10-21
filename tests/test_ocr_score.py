"""OCR quality scoring (BOM-14)."""

from ocr_fix.score import score_text

LEX = frozenset({"the", "book", "mormon", "palmyra", "printed", "sale", "golden", "bible"})


def test_single_letters_stay_out_of_the_garbage_rate():
    """The regression that matters: a delivery artifact must not read as an OCR error.

    NYSHN's text view fragments words into lone characters. Folding those into garbage_rate
    made the Wayne Sentinel score 0.309 against Chronicling America's 0.047 and would have
    down-weighted the Palmyra paper for its HTML. Vowelless tokens -- the genuine garbling
    signal -- were 0.009 against 0.008, indistinguishable.
    """
    fragmented = score_text("t h e b o o k o f m o r m o n", LEX)
    assert fragmented["garbage_rate"] == 0.0
    assert fragmented["single_letter_rate"] > 0.5


def test_garbage_rate_catches_real_garbling():
    """Vowelless runs and letter-digit salad are what OCR failure actually looks like."""
    scored = score_text("tho bgtrn xkcdp the book m0rm0n", LEX)
    assert scored["garbage_rate"] > 0.3


def test_a_i_o_are_words_not_fragments():
    scored = score_text("a book i read o mormon", LEX)
    assert scored["single_letter_rate"] == 0.0


def test_empty_page_is_flagged_not_dropped():
    """Nine Wayne Sentinel pages have no OCR text on the site; they stay as zero-word rows."""
    scored = score_text("   \n\n  ", LEX)
    assert scored["empty"] is True
    assert scored["tokens"] == 0
    assert scored["lexicon_rate"] == 0.0


def test_lexicon_rate_counts_hits_over_alphabetic_tokens():
    scored = score_text("the book of mormon zzz", LEX)
    assert scored["tokens"] == 5
    assert scored["lexicon_rate"] == 3 / 5  # of, zzz not in LEX
    assert scored["empty"] is False
