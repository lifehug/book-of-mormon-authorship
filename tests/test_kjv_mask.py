"""KJV span classification under 4.4 (BOM-16)."""

from kjv_mask.align import _longest_run, classify

CFG = {
    "kjv_mask": {
        "verbatim": {"min_identity": 0.90, "min_tokens": 8},
        "paraphrase": {"min_identity": 0.60, "max_identity": 0.90, "min_tokens": 8},
    }
}
KJV = "and the spirit of god moved upon the face of the waters and god said let there be light"


def _run(target: str, seed: int = 4):
    return classify(target, 0, len(target), KJV, 0, len(KJV), "kjv:GEN.1", CFG, seed)


def test_verbatim() -> None:
    spans = _run("intro words then the spirit of god moved upon the face of the waters and more")
    assert [s.kind for s in spans] == ["verbatim"] and spans[0].identity == 1.0


def test_paraphrase() -> None:
    t = "the spirit of god moved over all the face of those waters and god spake let there be"
    assert {s.kind for s in _run(t)} == {"paraphrase"}


def test_function_words_alone_are_not_a_span() -> None:
    assert _run("and the cat of the king sat on the face of the mat and the dog") == []


def test_longest_run() -> None:
    assert _longest_run([1, 1, 0, 1, 1, 1, 0]) == 3
