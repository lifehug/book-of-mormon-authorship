"""Feature extraction for classical stylometry (BOM-20; pre-registration section 5.1).

Every feature family is reduced to the same shape: one ``Counter`` of feature counts per
document. A shared vocabulary is then chosen across documents (most frequent first, with
culling of features that occur in too few documents) and each document becomes a vector of
relative frequencies over that vocabulary. The columns of a matrix are always ordered by
descending corpus frequency, which Eder's Delta relies on.

Feature families:

- words: lowercase word tokens, the same tokenizer as ``ingest.align.tokens``;
- character n-grams (n = 3, 4) over the normalized token stream joined by single spaces, so
  n-grams can span word boundaries but punctuation and case never enter;
- POS n-grams from an injected tagger (``Callable[[list[str]], list[str]]``); no tagger ships
  with this package, and calling without one raises ``TaggerRequiredError``;
- content words: word tokens with an 1800s-register English function-word stoplist removed.

Typical use::

    docs = [tokenize(t) for t in texts]
    counts = [word_counts(d) for d in docs]
    vocab = build_vocabulary(counts, top_n=300, min_doc_fraction=0.2)
    X = frequency_matrix(counts, vocab)   # rows: documents, columns: relative frequencies
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Hashable, Iterable, Sequence

import numpy as np

from ingest.align import tokens as _align_tokens

Tagger = Callable[[list[str]], list[str]]


class TaggerRequiredError(RuntimeError):
    """Raised when POS features are requested without an injected tagger."""


# English function words, extended with the archaic and biblical forms common in 1800s
# religious prose. Used to build the content-word profile (words NOT in this list) and as a
# ready-made function-word feature set.
FUNCTION_WORDS: frozenset[str] = frozenset(
    """
    a about above after again against all also am an and another any are as at
    be because been before being below between both but by
    can cannot could did do does doing done down during
    each either neither nor else ever every except
    few for from further had has have having he her here hers herself him himself his how
    i if in into is it its itself just least less let like
    may me might mine more most much must my myself
    no not now o of off oft often on once one only or other others ought our ours ourselves
    out over own
    same shall she should since so some such than that the their theirs them themselves
    then there these they this those though through thus till to too
    under until up upon us very
    was we were what whatever when whence where whereas whereby wherefore wherein whereof
    whereupon whether which while whilst who whoever whom whomsoever whose why will with
    within without would yet you your yours yourself yourselves
    unto thee thou thy thine ye hath doth dost hast art wast wert shalt wilt canst couldst
    wouldst shouldst mayest mightest didst hadst hither thither yonder ere nay yea lo behold
    thereof therein thereby thereto thereunto therefore hence herein hereof hereby
    amongst among toward towards against beside besides beneath betwixt nigh save
    also even yet verily insomuch inasmuch forasmuch notwithstanding albeit
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens (``[a-z0-9]+``), identical to ``ingest.align.tokens``."""
    return _align_tokens(text)


def word_counts(tokens: Sequence[str]) -> Counter[str]:
    return Counter(tokens)


def content_word_counts(
    tokens: Sequence[str], stoplist: Iterable[str] = FUNCTION_WORDS
) -> Counter[str]:
    """Counts of tokens not in the function-word stoplist (and not purely numeric)."""
    stop = stoplist if isinstance(stoplist, frozenset | set) else frozenset(stoplist)
    return Counter(t for t in tokens if t not in stop and not t.isdigit())


def function_word_counts(
    tokens: Sequence[str], words: Iterable[str] = FUNCTION_WORDS
) -> Counter[str]:
    """Counts of tokens that are in the function-word list."""
    keep = words if isinstance(words, frozenset | set) else frozenset(words)
    return Counter(t for t in tokens if t in keep)


def char_ngram_counts(tokens: Sequence[str], n: int) -> Counter[str]:
    """Character n-grams over the tokens joined by single spaces (spans word boundaries)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    s = " ".join(tokens)
    return Counter(s[i : i + n] for i in range(len(s) - n + 1))


def pos_ngram_counts(
    tokens: Sequence[str], n: int, tagger: Tagger | None = None
) -> Counter[tuple[str, ...]]:
    """POS-tag n-grams. ``tagger`` maps a token list to an equal-length tag list.

    No tagger is bundled (to keep heavy NLP dependencies out); pass one explicitly, e.g. a
    wrapper around a period-trained tagger.
    """
    if tagger is None:
        raise TaggerRequiredError(
            "POS n-grams need a tagger: pass tagger=callable(list[str]) -> list[str]. "
            "classic/ does not bundle one."
        )
    if n < 1:
        raise ValueError("n must be >= 1")
    tags = list(tagger(list(tokens)))
    if len(tags) != len(tokens):
        raise ValueError(f"tagger returned {len(tags)} tags for {len(tokens)} tokens")
    return Counter(tuple(tags[i : i + n]) for i in range(len(tags) - n + 1))


def build_vocabulary(
    doc_counts: Sequence[Counter],
    *,
    top_n: int | None,
    min_doc_fraction: float,
) -> list[Hashable]:
    """Most-frequent features across documents, with culling.

    A feature is culled if it appears in fewer than ``min_doc_fraction`` of the documents
    (the pre-registration uses 0.2). Survivors are ranked by their mean relative frequency
    across documents (so long documents do not dominate), ties broken by the feature itself
    for determinism, and the first ``top_n`` are returned (all if ``top_n`` is None).
    """
    if not doc_counts:
        raise ValueError("no documents")
    if not 0.0 <= min_doc_fraction <= 1.0:
        raise ValueError("min_doc_fraction must be in [0, 1]")
    n_docs = len(doc_counts)
    doc_freq: Counter = Counter()
    mean_rel: dict = {}
    for c in doc_counts:
        total = sum(c.values())
        doc_freq.update(k for k, v in c.items() if v > 0)
        if total:
            for k, v in c.items():
                mean_rel[k] = mean_rel.get(k, 0.0) + v / total / n_docs
    min_docs = min_doc_fraction * n_docs
    kept = [k for k in mean_rel if doc_freq[k] >= min_docs]
    kept.sort(key=lambda k: (-mean_rel[k], str(k)))
    return kept if top_n is None else kept[:top_n]


def relative_frequencies(counts: Counter, vocabulary: Sequence[Hashable]) -> np.ndarray:
    """Vector of count / total-tokens-in-document for each vocabulary item.

    The denominator is the document's total count over all its features, not just the
    vocabulary, so a word's value is its share of the whole text.
    """
    total = sum(counts.values())
    if total == 0:
        return np.zeros(len(vocabulary))
    return np.array([counts.get(f, 0) / total for f in vocabulary], dtype=float)


def frequency_matrix(doc_counts: Sequence[Counter], vocabulary: Sequence[Hashable]) -> np.ndarray:
    """Documents x features matrix of relative frequencies."""
    return np.vstack([relative_frequencies(c, vocabulary) for c in doc_counts])


def mfw_matrix(
    texts: Sequence[str], *, top_n: int | None, min_doc_fraction: float
) -> tuple[np.ndarray, list[str]]:
    """Convenience: tokenize texts, pick the MFW vocabulary, return (matrix, vocabulary)."""
    counts = [word_counts(tokenize(t)) for t in texts]
    vocab = build_vocabulary(counts, top_n=top_n, min_doc_fraction=min_doc_fraction)
    return frequency_matrix(counts, vocab), vocab
