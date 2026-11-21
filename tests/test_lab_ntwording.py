"""BOM-124: the New Testament-only phrase sets, hit counting and the leave-one-out hold."""

from lab.ntwording import (
    Kjv,
    Stream,
    Universe,
    auc,
    build_grams,
    measure,
    merge_runs,
    scan,
    tokens,
)

ROWS = [
    {"book": "GEN", "section": "OT", "text": "In the beginning God created the heaven."},
    {"book": "EXO", "section": "OT", "text": "In the beginning God created the heaven again."},
    {"book": "MAT", "section": "NT", "text": "Verily I say unto you that he shall live."},
    {"book": "JOH", "section": "NT", "text": "Verily I say unto you that light came."},
    {"book": "TOB", "section": "Apocrypha", "text": "Verily I say unto you that tobit wept."},
]


def _setup():
    kjv = Kjv(ROWS)
    uni = Universe(kjv, build_grams(kjv, [4]))
    return kjv, uni


def test_tokens_lower_and_letters_only():
    assert tokens("And God said, Let there be!") == ["and", "god", "said", "let", "there", "be"]


def test_apocrypha_removes_a_phrase_from_the_new_testament_set():
    _kjv, uni = _setup()
    # "verily i say unto" is in the Apocrypha here, so it is distinctive of neither side.
    assert "verily i say unto" not in uni.ids
    assert "in the beginning god" in uni.ids


def test_merge_runs_joins_overlaps_only():
    runs = merge_runs([(0, 4, 1), (2, 6, 2), (6, 10, 3)])
    assert [(s, e) for s, e, _ in runs] == [(0, 6), (6, 10)]


def test_old_testament_phrase_is_ot_distinctive_and_leave_one_out_holds_the_book():
    kjv, uni = _setup()
    words = tokens("in the beginning god created")
    st = Stream()
    st.add(len(words), scan(words, uni, [4]))
    allowed = [True] * len(uni.grams)
    full = measure(st, allowed, uni)
    assert full["ot_hits"] == 1 and full["nt_hits"] == 0
    # With Genesis held out the phrase is still in Exodus, so it stays OT-distinctive.
    assert measure(st, allowed, uni, hold=kjv.bit["GEN"])["ot_hits"] == 1


def test_allowed_filter_drops_a_phrase():
    _kjv, uni = _setup()
    words = tokens("in the beginning god created")
    st = Stream()
    st.add(len(words), scan(words, uni, [4]))
    assert measure(st, [False] * len(uni.grams), uni)["ot_hits"] == 0


def test_auc_perfect_and_tied():
    assert auc([3, 4], [1, 2]) == 1.0
    assert auc([1, 1], [1, 1]) == 0.5
