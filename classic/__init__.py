"""Classical stylometry: features, Burrows' Delta, General Imposters, ENSC, and replications."""

from classic.decide import INCONCLUSIVE, MATCH, NON_MATCH, Thresholds, calibrate, decide
from classic.delta import (
    burrows_delta,
    cosine_delta,
    eder_delta,
    fit_zscore,
    nearest_authors,
    zscore,
)
from classic.ensc import ENSC, NONE, ENSCResult
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
from classic.imposters import general_imposters

__all__ = [
    "ENSC",
    "ENSCResult",
    "FUNCTION_WORDS",
    "INCONCLUSIVE",
    "MATCH",
    "NONE",
    "NON_MATCH",
    "TaggerRequiredError",
    "Thresholds",
    "build_vocabulary",
    "burrows_delta",
    "calibrate",
    "char_ngram_counts",
    "content_word_counts",
    "cosine_delta",
    "decide",
    "eder_delta",
    "fit_zscore",
    "frequency_matrix",
    "function_word_counts",
    "general_imposters",
    "mfw_matrix",
    "nearest_authors",
    "pos_ngram_counts",
    "relative_frequencies",
    "tokenize",
    "word_counts",
    "zscore",
]
