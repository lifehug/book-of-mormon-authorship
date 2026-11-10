# Authorship, borrowing and dating of the earliest Book of Mormon text: an open, pre-registered computational study

*Draft, 2026-11-10. Dave Taylor, with analysis by an AI model (Claude). Every review step is
simulated by an AI model and labelled so; the blinding was simulated (the scoring ran without the
key; the analyst is an AI model). Repository: https://github.com/lifehug/book-of-mormon-authorship;
pre-registration: https://osf.io/6ugxc/ (frozen 2026-10-15; 45 dated amendments, the post hoc ones
labelled).*

## Abstract

We ask three questions of the 1830 Book of Mormon text: whose writing it most resembles (Q1), what
it borrowed from earlier books (Q2), and when its English dates from (Q3). The study takes no
position on the book's origin or on inspiration; it reports which known writers or books, if any,
the text closely resembles, with each method's error rate measured on known answers.

The test is larger than any before it. We catalogued 695,021 items from five sources (633,706
from the period's books and newspapers, 61,315 early modern texts for dating), including Harvard's Institutional Books (released 2025, new to this question), and trained
GPT-style language models on that period alone (125M, 297M and 590M parameters; 202,816 volumes,
25.7 billion tokens), so that "ordinary" means ordinary for 1830. Every King James span was masked,
every threshold was fixed in a public pre-registration, and the text was scored once, blind, mixed
with 43 decoys. All models are public.

We separate two questions that earlier studies merged. **Ranking** ("whose sample is closest?")
works well: on held-out known-author tests the candidate models put the true author first 94-99%
of the time. **Matching** ("is it confidently this person?") does not yet work: the same models
also say "match" to a wrong author on 22-47% of tests, falling with model size, against a
registered bar of 5%. Prior methods rerun on the same tests do worse (78-92%).

Results. No candidate (Joseph Smith, Oliver Cowdery, Sidney Rigdon, Solomon Spalding, Ethan Smith,
Gilbert J. Hunt, Parley P. Pratt, W. W. Phelps) is matched under the
registered rule: 3-10 of 168 chunks reach "match" in the registered run and 0-2 once Book of Mormon
quotations are removed from the candidate samples. Where the methods must rank, they rank Joseph Smith's 1828-29
revelations closest, also when every candidate model is trained on the same amount of text (at
125M and 297M; at 590M a slice of *The Late War* competes); that
sample is the only one in the text's own scriptural register, and his ordinary prose of 1831-33
sits mid-pack. No proposed source shares a copied passage, a plot sequence or a passage judged
specific; *The Late War* and *The First Book of Napoleon* pass the registered rare-phrase rule, as
the pseudo-biblical genre generally does. The text's grammar dates mostly before 1700 (median
1661) and is more archaic than period imitations of biblical style (p 0.0001). Seventeen public
claims were judged by rules written before any result: 2 supported, 6 contradicted, 4 mixed, 1
not addressed, 4 untestable. Code, data tables, every trained model and every decision are public
and rerunnable.

## 1. Introduction

The Book of Mormon was published in 1830. Its origin has been argued for two centuries, and
computational studies have reached opposite conclusions: wordprint studies found its narrators
distinct from each other and from nineteenth-century candidates (Larsen, Rencher and Layton
1980); nearest-shrunken-centroid classification pointed to Sidney Rigdon and Solomon Spalding
(Jockers, Witten and Criddle 2008); a reanalysis allowing "none of these" sent most chapters to an
unobserved author (Schaalje, Fields, Roper and Snow 2011); a rare-phrase study singled out *The Late
War* (Johnson and Johnson 2013). Each was criticised more for its setup than for its arithmetic:
closed candidate lists that force a pick, features that measure biblical register rather than
authorship, choices made after seeing the data, and comparison libraries too small to say what is
unusual.

This study is designed against those failures:

1. **Scale.** The comparison library is the surviving printed English of 1780-1830 (section 2), not
   a hand-picked set, and the language models are trained on that period only.
2. **Ranking and matching measured separately.** Every method may answer "none of these", and its
   rate of false matches is measured on known-answer tasks before it is used (section 4).
3. **King James masking.** Every span aligned to the King James Bible (6.8% of the text) is
   removed before attribution and dating.
4. **Pre-registration.** Thresholds, features, seeds and model choices were fixed publicly before
   scoring; every later change is a dated amendment, and those made after seeing results are
   labelled post hoc (section 7).
5. **No leakage, one blind run.** The text was kept out of every model's training and calibration
   until a single blind run (a gap in this rule, found after unblinding, is reported and corrected
   in section 7).
6. **A whole-library sweep** of every author in the period corpus, not only named suspects.

What stylometry can see is the English on the page and whoever produced it; it cannot see how that
English came to be, and in particular cannot separate a composer from a dictator or a translator.
The study therefore makes no claim about translation, inspiration or the truth of the book's
contents.

**How the paper is ordered.** Section 2 describes the scale of the test and how the text and
library were prepared; section 3 reruns the five earlier studies; section 4 measures every method
on known answers, including how large the models should be; section 5 gives each test on the Book
of Mormon with its preparation first; section 6 takes the books named in the CES Letter one by
one; section 7 lists what was corrected along the way; section 8 judges seventeen public claims;
section 9 says what held; section 10 takes the candidates one by one; sections 11-13 give the
limitations, what is public, and what comes next. The detailed methods are in Appendix A.
