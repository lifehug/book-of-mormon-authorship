"""CER against keyed text (BOM-14)."""

from ocr_fix.groundtruth import _index, letters, norm_keyed, window_cer

KEYED = (
    "It was the best of times, it was the worst of times, it was the age of wisdom, "
    "it was the age of foolishness, it was the epoch of belief, it was the epoch of "
    "incredulity, it was the season of Light, it was the season of Darkness."
)


def test_exact_copy_scores_zero() -> None:
    target = "PREFACE " + KEYED + " THE END"
    win = KEYED[40:160]
    cer, lcer = window_cer(win, target, _index(target))
    assert cer == 0 and lcer == 0


def test_errors_counted_against_reference_length() -> None:
    noisy = KEYED.replace("wisdom", "wifdom").replace("belief", "bel1ef")
    win = KEYED[60:180]
    cer, _ = window_cer(win, noisy, _index(noisy))
    assert 0 < cer < 0.05


def test_no_anchor_is_unaligned() -> None:
    other = "Entirely different words share nothing whatever with that famous opening at all."
    assert window_cer(KEYED[:120], other, _index(other)) is None


def test_normalisation() -> None:
    assert norm_keyed("firſt  〈◊〉 line\nnext") == "first line next"
    assert letters("It's 12 o'Clock!") == "its oclock"
