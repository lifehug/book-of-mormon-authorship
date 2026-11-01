from eval.italics import _kjv_marked, span_counts


def test_supplied_word_dropped_is_counted_as_italic():
    ch = _kjv_marked()
    # Genesis 1:2 with the translators' "was" left out of "darkness [was] upon"
    t = "And the earth was without form and void and darkness upon the face of the deep"
    c = span_counts(t, "kjv:GEN.1", ch, 5)
    assert c["italic_dropped"] == 1 and c["italic_kept"] == 0
    assert c["roman_kept"] == 16 and c["roman_changed"] == c["roman_dropped"] == 0
