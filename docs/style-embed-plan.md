# Style embeddings (BOM-30)

Written 2026-11-05, before any style-embedding model was trained. Registered as Amendment 24 (OSF
revision 6aed5e35c13cfd892df383af). Settings: `style_embed.*` in `config/preregistered.yaml`; code
in `style_embed/`.

**What it is.** A model that turns a stretch of text into a 512-number "style fingerprint", trained
so that two samples by the same author land close together and samples by different authors land
far apart (LUAR's approach). It is the second, independent authorship signal the plan asks for
(5.4), and the embedding half of the author sweep (5.6, BOM-39).

**How it is built.**

- Training authors: the 1830 model's training volumes grouped by catalog author; unnamed,
  corporate and pseudonymous authors left out ("subscriber, a"; record numbers; single letters;
  the registered list of corporate words); a work is an author's volumes sharing the first six
  title words; at least 2 works. 8,527 authors qualify; 10% are held out of training entirely and
  become the sweep's calibration pool.
- Passages: 128 tokens in the benchmark's word form (lowercased words), up to 16 works and 32
  passages per work, from random volumes and positions (`python -m style_embed.data build`).
- Encoder: the 297M 1830 model, mean-pooled; an episode is 8 passages of one work; a linear layer
  to 512 dimensions; unit length.
- Training: 64 authors a step, two episodes each from two different works, so that the model can
  only win by learning the author, not the book or its topic; symmetric InfoNCE at temperature
  0.05; 20,000 steps on a rented Secure Cloud H100 (`scripts/style_pod.py`, owner's cap about $50).
- Test: BOM-21's own benchmark trials with the fingerprints in place of word counts (cosine
  closed set, General Imposters verification); same pass bar as every method
  (`python -m style_embed.benchmark`).

**Known weaknesses.** Lowercased, unpunctuated text throws away some style signal, chosen so the
fingerprints work in the benchmark's and the sweep's existing trials. Catalog author names are
noisy (variants of one person's name count as different authors; a few pseudonyms remain).
Multi-volume works with differing titles may count as separate works.
