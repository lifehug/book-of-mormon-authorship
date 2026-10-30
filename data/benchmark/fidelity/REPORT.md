# Are our versions of the failed methods faithful? (BOM-57)

Written 2026-10-30. BOM-21 failed General Imposters and ENSC. Before treating those failures as
facts about the methods, each of our implementations was run on data where the original authors
published results, and compared. Sources and links: `SOURCES.md`. Code: `eval/fidelity.py`,
`classic/ensc_published.py`. Results: `gi.json`, `ensc.json`.

## General Imposters: faithful

Our `classic/imposters.py` runs the rounds; the vectors, profiles, imposters, settings (100
rounds, half the features, 30 imposters) and score shifter follow Kestemont et al.'s published
code, on the six PAN 2014 verification corpora. Test AUC x c@1 (x 100), word unigrams:

| Corpus | cosine-tf ours | published | cosine-tf-std ours | published |
| --- | --- | --- | --- | --- |
| Dutch essays | 77.92 | 76.59 | 87.44 | 87.50 |
| Dutch reviews | 34.14 | 36.58 | 30.85 | 33.58 |
| English essays | 24.02 | 24.95 | 29.21 | 29.12 |
| English novels | 29.76 | 30.55 | 37.01 | 37.35 |
| Greek articles | 45.67 | 48.63 | 49.40 | 50.20 |
| Spanish articles | 65.54 | 69.52 | 72.78 | 63.41 |

Eleven of twelve within 4 points (median absolute difference about 1.5); the exception scores
higher than published. Known differences: their rounds sample features with replacement, ours
without; random draws differ. **The General Imposters that failed BOM-21 is the published
method.** Its saturating score is the method's (they also use 100 rounds), and its confusion of
two authors writing in the same imitation style is a property of the method on this problem.

## ENSC: our BOM-20 version was not faithful; the published method has a real sensitivity

`classic/ensc.py` (BOM-20) decided "none of the above" by a chi-square cutoff (alpha). The
published method (Funai 2010 code; Schaalje et al. 2011) instead adds a latent author as a
competing class with a capped distance (lambda). Ported line by line in
`classic/ensc_published.py` and checked on the Federalist Papers:

- Hamilton, Madison and Jay, 25 Hamilton papers tested over 100 splits: published method 29.2%
  wrong (range 12-48%; Funai 16%); our BOM-20 version 63.3%.
- Book of Mormon candidates, all 51 Hamilton papers should go to the latent author: the
  published method's error falls with candidate sample length (80% at 1,000 words to 0% at
  10,000); Funai's 15.69% lies between our 3,000- and 5,000-word rows, matching the published
  composites of 3,300-6,800 words. Our BOM-20 version said "none" to all 51.
- The 2011 text-size adjustment (eq. 12) narrows the swing (49% to 24%) but does not remove it,
  and the errors go to candidates whose samples are of a similar kind (Cowdery's 1830s newspaper
  prose against Hamilton's essays).

**The ENSC that failed BOM-21 was our reconstruction, not the published method.** The published
method reproduces where the conditions match, but its open-set answer depends on candidate
sample length and on the kind of candidate text.

## What follows

- BOM-58: General Imposters' failure stands. ENSC is rerun on the benchmark with the published
  method; replacing a wrong implementation is a correction, not a new choice.
- BOM-60: refit ENSC's size model on many authors; General Imposters' ceiling and same-register
  confusion.
- BOM-22: the ENSC replication is rerun with the published method.
