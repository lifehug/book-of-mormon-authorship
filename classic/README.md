# classic/

Classical stylometry: feature extraction, Burrows' Delta and variants, General Imposters,
extended nearest shrunken centroids (ENSC), and the decision rule that turns a score into
match / non-match / inconclusive. Pure Python plus numpy and scipy; no NLP models.

Issues: BOM-20 (this library), BOM-22 (replications of prior studies).
Pre-registration: sections 5.1 (methods) and 6.1 (decision rule).

## Modules

| Module | What |
| --- | --- |
| `features.py` | `tokenize` (same as `ingest.align.tokens`); per-document `Counter`s for words, function words, content words (1800s function-word stoplist `FUNCTION_WORDS`, incl. unto/thee/thou/ye/hath/doth), character n-grams, POS n-grams (injected tagger only); `build_vocabulary` (top N, cull features in < X% of docs); `relative_frequencies`, `frequency_matrix`, `mfw_matrix` |
| `delta.py` | `fit_zscore`/`zscore`; `burrows_delta`, `cosine_delta`, `eder_delta`; `nearest_authors` |
| `imposters.py` | `general_imposters` (Koppel & Winter 2014; Kestemont et al. 2016): share of trials the candidate beats every sampled imposter |
| `ensc.py` | `ENSC` (Tibshirani et al. 2002 shrunken centroids + open-set "none" rule after Fields, Schaalje & Roper 2011); exact rule in the module docstring |
| `decide.py` | `calibrate` thresholds at 5% FPR / 5% FNR from benchmark scores; `decide` a score |

## Usage

```python
import numpy as np
from classic import (
    ENSC,
    build_vocabulary,
    calibrate,
    decide,
    frequency_matrix,
    general_imposters,
    nearest_authors,
    tokenize,
    word_counts,
)

counts = [word_counts(tokenize(t)) for t in training_texts]
vocab = build_vocabulary(counts, top_n=300, min_doc_fraction=0.2)
X = frequency_matrix(counts, vocab)  # docs x features, relative freqs
test = frequency_matrix([word_counts(tokenize(test_text))], vocab)[0]

# Delta: rank authors (profiles = mean of each author's rows)
profiles = {a: X[[i for i, l in enumerate(labels) if l == a]].mean(axis=0) for a in set(labels)}
nearest_authors(test, profiles, method="cosine", reference=X)

# General Imposters: verification score in [0, 1]
score = general_imposters(
    test,
    profiles["A"],
    imposter_matrix,
    feature_fraction=0.5,
    n_imposters=10,
    trials=100,
    distance="cosine",
    seed=0,
)

# Decision (pre-registration 6.1), thresholds calibrated on the benchmark (BOM-21)
th = calibrate(same_author_scores, different_author_scores, fpr=0.05, fnr=0.05)
decide(score, th)  # "match" | "non-match" | "inconclusive"

# ENSC with open-set rejection
model = ENSC(shrinkage=1.0, alpha=0.05).fit(X, labels)
model.predict(test)  # a label, or "none"
```

POS n-grams need a tagger: `pos_ngram_counts(tokens, 2, tagger=my_tagger)`, where
`my_tagger(list[str]) -> list[str]`. Without one it raises `TaggerRequiredError`.

## Choices to revisit in BOM-21/22

- ENSC's open-set statistic compares the test document with each unshrunken class
  centroid against a chi-squared reference (unregularized within-class variance, times
  1 + 1/n_k), ignores feature correlation, and does not model text length; check against
  Fields et al. (2011) when replicating. The reference is anti-conservative on toy data,
  so `alpha` must be calibrated on the benchmark.
- Eder's Delta assumes columns in descending frequency order (what `build_vocabulary` gives).
- GI `"delta"` distance z-scores against candidate + full imposter pool, never the test doc.
