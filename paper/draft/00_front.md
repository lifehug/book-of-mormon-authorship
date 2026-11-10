# Authorship, borrowing and dating of the earliest Book of Mormon text: an open, pre-registered computational study

*Draft, 2026-11-10. Dave Taylor, with analysis by an AI model (Claude). Every review step is
simulated by an AI model and labelled so; the blinding was simulated (the scoring ran without the
key; the analyst is an AI model). Repository: https://github.com/lifehug/book-of-mormon-authorship;
pre-registration: https://osf.io/6ugxc/ (frozen 2026-10-15; 44 dated amendments, the post hoc ones
labelled).*

## Abstract

We ask three questions of the 1830 Book of Mormon text: whose writing it most resembles (Q1),
what it borrowed from earlier books (Q2), and when its English dates from (Q3). The study takes no
position on the book's origin or on inspiration; it reports which known writers or books, if any,
the text closely resembles, with measured error rates. Every threshold was fixed in a public
pre-registration before the text was scored. We built a corpus of about 200,000 English volumes
printed 1780-1830, trained GPT-style language models on that period only (125M, 297M and 590M
parameters), masked every King James Bible span, and validated every method on known-answer tasks
before a single blind run in which 168 Book of Mormon chunks were mixed with 43 decoys. The
right candidate was ranked first for most candidate decoys (15-21 of 22 by method); the candidate
models, the only family able to call a match at its registered threshold, matched none of the 21
control passages. No candidate author (Joseph Smith, Oliver Cowdery, Sidney Rigdon, Solomon
Spalding, Ethan Smith, Gilbert J. Hunt, Parley P. Pratt, W. W. Phelps) is matched under the
registered rule. The registered Bayesian synthesis, which covers only the three candidates with
adequate pre-1830 samples (Ethan Smith, Hunt, Spalding), gives "none of these three" 0.744 (prior
0.5); Joseph Smith's and Cowdery's pre-1830 samples are too small for it (2,702 and 1,309 words)
and are untested by it, not ruled out. A sweep of 23,872 period authors, which failed its own
usability test, finds no lead. *The Late War* (1816) and *The First Book of Napoleon* (1809) pass
the registered rare-phrase rule, as does the American pseudo-biblical genre generally; no proposed
source shares a copied passage, a plot sequence or a pair of passages judged specific. The grammar of the text dates mostly before 1700 (median
1661) and is more archaic than period imitations of biblical style (p 0.0001). No method passes
the registered open-set bar (5% false matches; the best stable rate is 22%), so all attribution
results are graded evidence. Where methods must rank someone first, they rank Joseph Smith's
1828-29 revelations closest, a sample in the text's own scriptural register; his ordinary prose of
1831-33 sits mid-pack. Code, data tables, every trained model and every decision are public and
rerunnable.

## 1. Introduction

The Book of Mormon was published in 1830. Its origin has been argued for two centuries, and
computational studies have reached opposite conclusions: wordprint studies found its narrators
distinct from each other and from nineteenth-century candidates (Larsen, Rencher and Layton
1980); nearest-shrunken-centroid classification pointed to Sidney Rigdon and Solomon Spalding
(Jockers, Witten and Criddle 2008); a reanalysis showed that result depended on a closed candidate
list (Fields, Schaalje and Roper 2011). Each was criticised for its setup more than its arithmetic:
closed candidate sets that force a pick, features that measure biblical register rather than
authorship, choices made after seeing the data, and models that had read the text.

This study is designed against those failures:

1. **Open-set evaluation.** Every attribution method may answer "none of these", and its rate of
   false matches is measured on known-answer tasks before it is used.
2. **King James masking.** Every span aligned to the King James Bible (6.8% of the text) is
   removed before attribution and dating.
3. **Pre-registration.** Thresholds, features, seeds and model choices were fixed publicly before
   scoring; every later change is a dated amendment, and those made after seeing results are
   labelled post hoc.
4. **No leakage.** The text was kept out of every model's training and calibration until one blind
   run. (A gap in this rule, found after unblinding, is reported in section 9.)
5. **Period-only language models** trained on 1780-1830 English, so "ordinary" means ordinary for
   the period.
6. **A whole-library sweep** of every author in the period corpus, not only named suspects.

What stylometry can see is the English on the page and whoever produced it; it cannot see how
that English came to be, and in particular cannot separate a composer from a dictator or a
translator. The study therefore makes no claim about translation, inspiration or the truth of the
book's contents. Everything is runnable from the repository; texts that cannot be redistributed
are replaced by derived tables and by the steps to obtain them (`docs/replication.md`).
