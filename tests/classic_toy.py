"""Synthetic authors for classic/ tests: each author is a distinct word distribution."""

from __future__ import annotations

import numpy as np

from classic.features import build_vocabulary, frequency_matrix, tokenize, word_counts

WORDS = [f"w{i}" for i in range(60)]


def author_distributions(n_authors: int, seed: int = 1, concentration: float = 0.5):
    rng = np.random.default_rng(seed)
    base = rng.dirichlet(np.full(len(WORDS), 5.0))
    out = []
    for _ in range(n_authors):
        # each author perturbs a shared base distribution (realistic: shared function words)
        p = 0.5 * base + 0.5 * rng.dirichlet(np.full(len(WORDS), concentration))
        out.append(p / p.sum())
    return out


def sample_text(p: np.ndarray, n_tokens: int, rng: np.random.Generator) -> str:
    return " ".join(rng.choice(WORDS, size=n_tokens, p=p))


def corpus(n_authors=5, docs_per_author=4, n_tokens=1500, seed=2):
    dists = author_distributions(n_authors)
    rng = np.random.default_rng(seed)
    texts, labels = [], []
    for a, p in enumerate(dists):
        for _ in range(docs_per_author):
            texts.append(sample_text(p, n_tokens, rng))
            labels.append(f"A{a}")
    return dists, texts, labels, rng


def matrix(texts, vocab=None):
    counts = [word_counts(tokenize(t)) for t in texts]
    if vocab is None:
        vocab = build_vocabulary(counts, top_n=None, min_doc_fraction=0.2)
    return frequency_matrix(counts, vocab), vocab
