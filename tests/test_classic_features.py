import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from classic.features import (
    FUNCTION_WORDS,
    TaggerRequiredError,
    build_vocabulary,
    char_ngram_counts,
    content_word_counts,
    frequency_matrix,
    function_word_counts,
    mfw_matrix,
    pos_ngram_counts,
    relative_frequencies,
    tokenize,
    word_counts,
)
from ingest.align import tokens as align_tokens

KJV = Path(__file__).resolve().parents[1] / "data" / "kjv" / "kjv.jsonl"


def test_tokenize_matches_align() -> None:
    s = "And it came to pass, [sic] that THOU & thy 2 sons went Unto the land."
    assert tokenize(s) == align_tokens(s)
    assert tokenize("Hath he; doth she?") == ["hath", "he", "doth", "she"]


def test_build_vocabulary_ranks_and_culls() -> None:
    docs = [
        Counter({"the": 10, "and": 5, "rare": 1}),
        Counter({"the": 8, "and": 6}),
        Counter({"the": 9, "and": 2, "of": 3}),
        Counter({"the": 7, "of": 1}),
        Counter({"the": 5, "and": 1}),
    ]
    vocab = build_vocabulary(docs, min_doc_fraction=0.0)
    assert vocab[0] == "the" and vocab[1] == "and"
    # "rare" is in 1 of 5 docs (20%): kept at 0.2, culled at 0.3
    assert "rare" in build_vocabulary(docs, min_doc_fraction=0.2)
    assert "rare" not in build_vocabulary(docs, min_doc_fraction=0.3)
    assert build_vocabulary(docs, top_n=2) == ["the", "and"]
    with pytest.raises(ValueError):
        build_vocabulary([])


def test_relative_frequencies_use_whole_document() -> None:
    c = Counter({"a": 2, "b": 1, "c": 1})
    np.testing.assert_allclose(relative_frequencies(c, ["a", "z"]), [0.5, 0.0])
    assert relative_frequencies(Counter(), ["a"]).tolist() == [0.0]
    m = frequency_matrix([c, Counter({"z": 4})], ["a", "z"])
    assert m.shape == (2, 2) and m[1, 1] == 1.0


def test_char_ngrams_span_word_boundaries() -> None:
    c = char_ngram_counts(["ab", "cd"], 3)
    assert c == Counter({"ab ": 1, "b c": 1, " cd": 1})
    assert sum(char_ngram_counts(["hello"], 4).values()) == 2
    with pytest.raises(ValueError):
        char_ngram_counts(["x"], 0)


def test_pos_ngrams_need_tagger() -> None:
    toks = ["the", "lord", "spake"]
    with pytest.raises(TaggerRequiredError):
        pos_ngram_counts(toks, 2)

    def toy_tagger(ts: list[str]) -> list[str]:
        return ["DET" if t == "the" else "N" if t == "lord" else "V" for t in ts]

    assert pos_ngram_counts(toks, 2, tagger=toy_tagger) == Counter({("DET", "N"): 1, ("N", "V"): 1})
    with pytest.raises(ValueError):
        pos_ngram_counts(toks, 2, tagger=lambda ts: ["X"])


def test_function_word_list_covers_archaic_forms() -> None:
    for w in ["unto", "thee", "thou", "ye", "hath", "doth", "thy", "shalt", "the", "and"]:
        assert w in FUNCTION_WORDS
    toks = tokenize("And thou shalt say unto them, the lord hath spoken 3 times")
    assert content_word_counts(toks) == Counter({"say": 1, "lord": 1, "spoken": 1, "times": 1})
    assert function_word_counts(toks)["unto"] == 1
    assert "lord" not in function_word_counts(toks)


def test_kjv_smoke() -> None:
    """Real-text smoke test on public-domain KJV verses (not the sealed text)."""
    if not KJV.exists():
        pytest.skip("KJV data not present")
    books: dict[str, list[str]] = {}
    with KJV.open() as f:
        for line in f:
            r = json.loads(line)
            if r["book"] in ("GEN", "EXO", "MAT", "ROM"):
                books.setdefault(r["book"], []).append(r["text"])
    texts = [" ".join(v) for v in books.values()]
    X, vocab = mfw_matrix(texts, top_n=100, min_doc_fraction=0.2)
    assert X.shape == (4, 100)
    assert vocab[0] == "the"
    assert "unto" in vocab[:30]
    assert np.all(X.sum(axis=1) < 1) and np.all(X >= 0) and np.all(X[:, :20] > 0)
    c4 = char_ngram_counts(tokenize(texts[0]), 4)
    assert c4["the "] > 1000
    assert content_word_counts(word_counts(tokenize(texts[0])).elements())["lord"] > 100
