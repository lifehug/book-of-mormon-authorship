"""The constants the code runs with equal the values Amendment 6 registered."""

from kjv_mask import run as kjv_run
from metadata import controls, sealed
from metadata.config import load
from ocr_fix import clean, defragment, lexicon


def test_code_constants_match_the_registration():
    cfg = load()
    oc = cfg["corpus"]["ocr_cleaning"]
    pm = cfg["kjv_mask"]["passim"]
    assert lexicon.MIN_DOCS == oc["lexicon_min_docs"]
    assert clean.LONG_S_RATIO == oc["long_s_ratio"]
    assert clean.EDGE_LINES == oc["edge_lines"]
    assert clean.HEADER_MIN_LETTERS == oc["header_min_letters"]
    assert clean.HEADER_MIN_PAGES == oc["header_min_pages"]
    assert clean.HEADER_MIN_SHARE == oc["header_min_share"]
    assert clean.SHORT_LINE == oc["short_line"]
    assert clean.CHARS_PER_PAGE == oc["chars_per_page"]
    assert defragment.FRAGMENT_SHARE == oc["defragment_fragment_share"]
    assert defragment.FRAGMENT_LEN == oc["defragment_fragment_len"]
    assert defragment.MAX_WORD == oc["defragment_max_word"]
    assert defragment.UNKNOWN_PER_LETTER == oc["defragment_unknown_per_letter"]
    assert sealed.MIN_SHARED == cfg["sealing"]["contamination_min_shared"]
    assert controls.POOL_SAMPLE == cfg["controls"]["pool_sample"]
    assert kjv_run.BATCH_WORDS == pm["batch_words"]
    assert kjv_run.PIECE_WORDS == pm["piece_words"]
    assert kjv_run.PIECE_OVERLAP == pm["piece_overlap"]
    assert (kjv_run.SPLIT_PARTS, kjv_run.SPLIT_DEPTH) == (pm["split_parts"], pm["split_depth"])
