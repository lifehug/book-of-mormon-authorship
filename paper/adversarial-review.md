# Adversarial review of the pre-registration (simulated)

**This review is simulated.** No external scholar has read or approved the protocol. The
objections below were generated on 2026-10-15 by writing out, as strongly as possible, what
three kinds of reviewer would say about `preregistration.md` v0.1, and the responses record
what changed in v0.2. The project claims nothing more than that. The original plan called for
real advisors (BOM-03); the owner chose to proceed without them, and this document exists so
the omission is visible rather than hidden.

The three simulated reviewers:

- **R1**, a stylometrist sympathetic to the text's own account of itself, in the tradition of
  Larsen et al. and Fields et al.
- **R2**, a critical historian of early Mormonism familiar with the Spalding-Rigdon and
  Late War arguments.
- **R3**, a computational linguist with no stake in the debate.

## R1: sympathetic stylometrist

**R1.1 Function words are genre, not author.** "Your most-frequent-word lists will be
dominated by *unto*, *behold*, *yea*, *it came to pass*. You will measure the biblical register
and call it authorship, the same error made against the 1980 study."
*Response:* KJV spans are masked before any attribution feature is computed (section 4.4), all
candidate and control texts get the same masking, the pseudo-biblical control set is the
imposter pool for General Imposters, and a content-word feature set is added alongside function
words (section 5.1). *Changed in v0.2:* content-word features; genre-matched imposters.

**R1.2 The internal narrators are a live hypothesis, not a nuisance.** "The 1980 finding was
that Nephi, Alma, and Mormon differ from each other. If you only test eight 19th-century
names you have prejudged the question."
*Response:* H1c is now a stated hypothesis with its own decision rule (sections 2 and 6.3),
and narrator separability is compared against dictation-order and scribe segmentations so
that a style shift is not attributed to a narrator when a scribe change explains it as well.
*Changed in v0.2:* H1c and section 6.3 added.

**R1.3 Joseph Smith's sample is too small and you will report a null as evidence.** "Below
5,000 words every method fails. 'No match to Joseph Smith' will be read as 'Joseph Smith did
not write it' when it means 'we could not test'."
*Response:* Candidates under the method's minimum sample size carry an unreliable flag, are
excluded from the synthesis, and section 10 states that this is reported as untestable, not as
a non-match. Dictated and handwritten Smith texts are separate samples so the dictated register
can be compared to a dictated book. *Changed in v0.2:* explicit sample floor per method and
the "not a non-match" wording.

**R1.4 Thresholds calibrated after seeing results.** "Who sets the match threshold, and when?"
*Response:* Every threshold is either fixed in section 6 or produced by a calibration procedure
on benchmark data only, committed to the repository before the blind run. No threshold moves
after the Book of Mormon is scored. *Changed in v0.2:* section 6 preamble.

## R2: critical historian

**R2.1 ENSC is not neutral.** "Fields, Schaalje, and Roper's extended method was built to
produce an open-set null. Running it as your sole open-set method imports their framing."
*Response:* ENSC is one of three method families. General Imposters and the authorial models
are independent open-set methods, and a candidate is supported only if two families agree
(section 6.2). ENSC is also replicated as published in BOM-22 so its behavior on this text is
documented separately. *No change needed beyond section 6.2, which already requires two
families.*

**R2.2 The candidate list is the believers' list plus the usual suspects.** "Where are the
Cowdery-as-author and Rigdon-as-editor hypotheses tested as such, not as whole-book
attributions?"
*Response:* Segment-level results by narrator, dictation order, and scribe (section 4.5) let a
partial-authorship pattern appear without being pre-specified. The author sweep (section 6.6)
is the mechanism for candidates nobody has proposed. Whole-book-only attribution is not
assumed anywhere. *Changed in v0.2:* the sweep and promotion rule written into section 3.

**R2.3 The borrowing analysis will be swamped by biblical overlap.** "Every 1820s religious
book shares phrases with every other through the KJV. Your 'significant parallel' list will be
Bibles."
*Response:* Borrowing runs on full text but with KJV spans labeled, so a parallel that is
itself KJV-derived is reported as such, and the null distribution is stratified by genre so
religious sources are compared against religious nulls (section 6.5). Luke is always reported
with its percentile, precisely because the 2013 study's critics used it. *Changed in v0.2:*
genre stratification of the null; Luke, Late War, View of the Hebrews, Manuscript Story always
reported.

**R2.4 Access evidence is being used to launder a stylometric lead.** "Promoting a sweep lead
only if 'historically plausible' lets you filter out inconvenient matches."
*Response:* The plausibility criterion gates promotion to the confirmatory list, not reporting.
Every lead above threshold is published in the lead table with its score whether or not it is
promoted (BOM-39 report format). *Changed in v0.2:* section 3 wording that plausibility gates
promotion only.

## R3: computational linguist

**R3.1 Perplexity is length- and topic-sensitive.** "A fine-tuned model prefers text about its
training topics. Rigdon's sermons will make the Rigdon model like any sermon."
*Response:* Scores are log-perplexity ratios against the base model over fixed 512-token
windows (section 5.2), which removes length effects, and the match criterion is a margin over
the best control-group model, so a candidate must beat the sermon control to count. *Changed
in v0.2:* fixed windows, ratio scoring, margin over controls.

**R3.2 Multiple comparisons in the sweep.** "Querying tens of thousands of authors guarantees
a nearest neighbor. Your 'lead' is a maximum of noise."
*Response:* The lead threshold is calibrated on the distribution of best-false-match scores,
which is exactly the maximum-of-noise distribution, and a lead must clear it under two
independent signals (section 6.6). The sweep is labeled exploratory and cannot itself support
a candidate. *Changed in v0.2:* two-signal requirement; usability criterion for the sweep.

**R3.3 Discovery and confirmation halves from the same book are not independent.** "If the
author is one person, both halves share the signal. Confirmation on the other half is weaker
than you imply."
*Response:* Correct, and the split is not claimed to give independence from the author. It
gives independence from the *selection*: the lead was chosen on data the confirmation never
touched, which removes the selection bias, not the shared authorship signal. Section 3 and
4.5 are worded to that effect. *Changed in v0.2:* wording.

**R3.4 A 100-300M model trained on a few billion tokens is weak.** "Its perplexities will be
noisy and the fine-tunes will overfit small candidates."
*Response:* The authorial models are one of three families, must pass the benchmark like any
other (section 7), and are dropped if they fail. Small candidates are flagged by the sample
floor. The point of the time-locked model is cleanliness, not capability. *No change.*

**R3.5 OCR noise differs by source and will leak into features.** "Character n-grams will
cluster by scanner, not author."
*Response:* A 10% character-error cutoff (section 4.3), measured correction accuracy (BOM-14),
and the benchmark's held-out books drawn from the same sources mean OCR effects are inside the
validation, not outside it. Candidate corpora are from edited transcriptions, which is itself a
confound and is listed in section 10. *Changed in v0.2:* provenance limit added to section 10.

**R3.6 The 0.5 prior on "not in set" is arbitrary.** *Response:* It is, and the sensitivity
analysis sweeps it from 0.2 to 0.8 (section 6.7). *No change.*

## Disposition

Fourteen objections; eleven produced changes in v0.2, three were already answered by the
draft. Any real reviewer is invited to add to this file by pull request; a dissent that the
owner does not accept is recorded here unchanged.
