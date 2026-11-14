## 12. Limitations

The first four limits bound every conclusion in the paper. The rest are narrower.

**The tests cannot separate translation from imitation.** Each borrowing and dating test was
first run on texts whose nature is known: genuine period translations of ancient works, and
period compositions presented as ancient (Amendment 9). None of the tests tells the two groups
apart. So "no borrowing found" and "the language dates early" describe the text. They do not say
what it is or how it came to be.

**No method can say "none of these".** This is stated once, here, for the whole paper. The
registered bar for a usable verdict was at most 5% false matches while still recognising 95% of
true authors. No method passes it. At that point the language models call a stranger's text a
match 51 to 57% of the time on the 430-test benchmark. Read the other way round, at a 5%
false-match target they confirm only 38 to 61% of true authors. The standard remedy from speaker
verification, score normalisation, does not carry over to authors it has not seen (17 to 26%
false matches against a 5% target). General Imposters and the style encoders cannot return
"match" at all at their registered thresholds, and the registered synthesis cannot recognise an
author's own text (section 9.3). It follows that "no match" cannot be read as "not this person",
for any candidate, and that the study can rank the candidates it has but cannot say whether the
author is among them.

**Most candidates are not recognised across their own works.** Only Ethan Smith's model
recognises him in a book it was not trained on (96 to 100% of passages). For Cowdery, Rigdon and
Phelps the rate is 0 to 23%, and for Pratt 52 to 87%, falling as the model grows; Hunt and
Spalding have a single work and cannot be tested. For those candidates the models learned a book
or a periodical, and a low rank is weak evidence about the person. Rigdon, Pratt and Phelps are
also represented only by writing from after 1830, by which time they had read the book, and the
registered check of whether later writing can stand in for earlier failed for every method.

**The pre-1830 revelation sample is small, and it is the only one of its kind.** Joseph Smith's
1828-29 revelations are 2,720 words, under the 10,000-word floor, and they are the whole of his
surviving writing from before 1830, so that side of every comparison is one fixed model that
cannot be resampled. Section 6.4 addresses part of this with his 1830-34 revelations, which
behave the same way at equal dose; but those were written after the book and could echo it. No
ordinary prose of his survives from before 1830. Cowdery's 1829 sample is 844 tokens once its
quotations are removed, too short to train on.

**Closest is confounded with register and channel.** The revelations are the only candidate
samples in the text's own scriptural register, and they share its channel: dictated by the same
man in the same years to the same circle of scribes, unedited. Nearly every other comparison text
is edited print. The methods cannot separate shared register or channel from shared authorship,
nor the person who dictated a text from the person who composed it. King James masking removes
aligned biblical passages only; formulae such as "it came to pass" and "behold" remain, and how
much each method rests on them has not been measured.

**The model sizes disagree where it matters most.** The register placebo is clean at 125M and
297M and fails at 590M. On known answers no size picks authors better than another, so there is
no ground for preferring one, and the split is reported as a split.

**Methods differ in stability.** The primary language-model method reproduces closely across
machines and its ranking is stable across seeds (section 6.5); variant V1's registered learning rate broke at 590M; variant V2 swings from 9% to 98%
false matches across seeds and carries no weight. Whether the model-based methods hold up under
deliberate imitation is not known: the imitation test has three authors.

**The 168 chunks are not 168 passages.** They are the text cut twice, and chunks from one book
are not independent of each other. Counts are given per length (section 6.4a) and should not be
read as 168 independent observations. Where a test was run on chunks (the dating comparison of
section 8.1), the result is also given with each book of the text as one unit.

**Single authors only.** Every test asks whether one known writer's style fits. Composite or
collaborative authorship is a common historical hypothesis that this design cannot test.

**The corpus.** OCR quality is uneven, and the wording searches miss an unmeasured but probably
large share of real shared phrasing in poor scans (a four-word phrase survives about 41% of the
time at 80% word accuracy). A negative from poor OCR is not evidence of absence: the 26 June 1829
*Wayne Sentinel* notice of the book's title page is present on the page image, and none of ten
search terms is found in its OCR. Training volumes holding 1 to 19 of the text's 12-token strings
(below the removal threshold of 20) were kept. Some catalog dates are wrong, and were corrected
where the text names later years. Author names conflate namesakes and split variants. About 72%
of the original manuscript is lost. Writers whose work did not survive in print, or who fall
outside the 23,872 swept authors, are not covered, and the registered sweep failed its own
usability test (section 7.8).

**The local print environment.** How much of what was printed and sold in western New York before
1830 survives in the corpus is not measured. The national newspaper set holds almost nothing from
the region, and the access scores centre on Joseph Smith's documented reach. Access is not use:
the access table records documented availability, not reading.

**The models.** The period models were trained on the period corpus, which includes volumes by
benchmark authors used later for calibration (as language-model training text, not with author
labels). The fine-tuning settings were fixed for all sizes in advance and may not suit the
largest. GPT-2 is used on the benchmark only, since it has read modern text that may include the
Book of Mormon.

**Registered features not run.** The classical methods used only most-frequent-word features. The
registered character n-grams, part-of-speech n-grams and content-word set were not run on the
benchmark or the Book of Mormon (`paper/deviations.md`, D3).

**Post hoc decisions.** A large share of sections 5 and 6 was decided after unblinding. Each step
is listed with its amendment and effect in section 9.1. The registered results are those of the
run tagged `blind-registered-2026-11-10`; everything later is a check on them, not a replacement.

**One person, simulated review and simulated blinding.** The study is designed and run by one
person with AI assistance. Every review step (adversarial review, draft review, peer review, the
research review of 2026-11-12) and the second triage pass are simulated by AI models. The blind
run's "fresh session" was a new AI session without the key, not an independent analyst. None of
this is independent scrutiny, and the paper has had none.

**Planned and not run.** The hand validation of the genre labels and the perturbation run that
would show whether label errors matter (BOM-53); thematic dating, whether the text's themes track
the 1820s (BOM-63); a larger test of register shift on 553 authors' sermons against their other
prose (section 5.3). Genre labels agree moderately between two model passes (84.9% on either
label, 50.8% exactly) and worst on early modern text.
