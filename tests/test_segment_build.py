"""Chunking and the seeded, narrator-stratified split (BOM-17)."""

from segment.build import chunk, original_words, split


def test_masked_spans_removed() -> None:
    text = "keep these words BIBLE QUOTE HERE and these"
    spans = [{"start": 17, "end": 34}]
    assert original_words(text, spans) == ["keep", "these", "words", "and", "these"]


def test_chunk_keeps_partial_remainder() -> None:
    ws = [(i // 3, f"w{i}") for i in range(7)]
    cs = chunk(ws, 3)
    assert [c["words"] for c in cs] == [3, 3, 1]
    assert [c["partial"] for c in cs] == [False, False, True]


def test_split_is_seeded_stratified_and_spares_singletons() -> None:
    cs = [{"chunk_id": f"n:{lab}:{i}", "label": lab, "seq_first": i, "partial": False}
          for lab, k in (("Mormon", 10), ("Jacob", 1)) for i in range(k)]  # fmt: skip
    a, b = split(cs, 20261017), split(cs, 20261017)
    assert a == b
    assert sum(v == "discovery" for k, v in a.items() if ":Mormon:" in k) == 5
    assert a["n:Jacob:0"] == "confirmation"
