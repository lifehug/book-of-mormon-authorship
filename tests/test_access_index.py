"""Access-evidence indexing over fragmented newspaper OCR (BOM-33)."""

from ingest.access_index import TERMS, page_date, snippet, squeeze


def test_squeeze_defeats_the_nyshn_fragmentation():
    """NYSHN delivers words as lone characters; the index has to see through that."""
    assert "bookofmormon" in squeeze("T H E B O O K O F M O R M O N")
    assert "bookofmormon" in squeeze("The Book of Mormon")


def test_a_spurious_character_defeats_even_a_squeezed_phrase():
    """Why single distinctive words stay in the term list beside the phrases.

    The real 1830-03-26 page reads "by the hand Tof Moroni" -- the OCR has invented a T. So
    the phrase `handofmoroni` does not match, and that date was caught by `moroni` alone.
    Squeezing survives missing spaces; it does not survive inserted letters.
    """
    page = squeeze("by the hand Tof Moroni")
    assert "handofmoroni" not in page
    assert "moroni" in page
    assert "moroni" in TERMS["book_of_mormon"]


def test_bare_nephi_is_not_a_term():
    """Squeezed, "ne Philadelphia" becomes "nephiladelphia".

    Five of eight hits for bare `nephi` were that word, so only the genitive forms are
    searched. This pins the reason so the term is not helpfully restored later.
    """
    assert "nephi" in squeeze("ne Philadelphia Gazette")
    assert "ofnephi" not in squeeze("ne Philadelphia Gazette")
    assert "nephi" not in TERMS["book_of_mormon"]
    assert "ofnephi" in TERMS["book_of_mormon"]


def test_bare_mormon_is_not_a_term():
    """Its only 1829 hit was inside a garbled apothecary advertisement."""
    assert "mormon" not in TERMS["book_of_mormon"]


def test_genitive_forms_still_match_the_real_title_page():
    page = squeeze("of^he P eople of Nephi., and also.of tbe La-manites")
    assert "ofnephi" in page


def test_snippet_maps_a_squeezed_offset_back_into_the_raw_page():
    raw = "ready for sale: T h e B o o k o f M o r m o n, price"
    sq = squeeze(raw)
    out = snippet(raw, sq, sq.find("bookofmormon"))
    assert "B o o k" in out


def test_page_date_reads_the_nyshn_filename():
    assert page_date("wayne_sentinel_18300326_p2") == "1830-03-26"
    assert page_date("no_date_here") is None
