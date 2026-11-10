# SIMULATED review: stylometrist

> **SIMULATED.** Written by an AI model (claude-opus-5-5) acting as a stylometrist referee, 2026-11-10. No human reviewed this work. Shown: the draft and the pre-registration, SHA-256 `753deba893c96bfb08e7ddfaa15be64c81a3f89f7a138c86fe1d3eb4b8309368`.

## Summary
The paper asks whose writing the 1830 Book of Mormon most resembles (Q1), what it borrowed (Q2), and when its English dates from (Q3). It uses a pre-registered pipeline: a deduplicated 1780–1830 corpus, King James spans masked, classical stylometry, authorial language models fine-tuned from period-only GPT-style base models (125M/297M/590M), a style-embedding encoder, a whole-corpus author sweep, and a simulated-blind run with decoys. It concludes that no candidate is matched and that a Bayesian synthesis favours "none of these candidates" (0.744). It also finds that no proposed source is borrowed from beyond genre-level sharing, that the grammar dates mostly before 1700, and that the methods' closeness to Joseph Smith runs through the revelatory register. The transparency is unusual and commendable: amendments are labelled, failures are disclosed, and all weights are released. However, several headline sentences say more than the registered results permit. Several design choices also bias toward the reported null or toward register-driven rankings.

## Major points

1. **The "none of these candidates" posterior excludes the candidate the methods rank closest.**
   - The problem: the 0.744 posterior is over Hunt, Spalding and Ethan Smith only. Joseph Smith, Cowdery (pre-1830), and the post-1830 samples are outside it, as unreliable or secondary samples, so they fall into "not in set." Yet the abstract lists eight candidates and then reports "none of these candidates" 0.744. The same section says every method ranks Joseph Smith's pre-1830 sample closest after Amendment 43.
   - Why it matters: a reader will take 0.744 as evidence against all eight. In fact it is silent on the person every method ranks first.
   - Fix: state the candidate set beside every occurrence of the posterior, in the abstract, results and discussion. Drop the phrase "none of these candidates" for anyone outside that set.

2. **The synthesis rests on one family that cannot return *match*, chosen by one imitation window.**
   - The problem: the posterior is driven entirely by General Imposters. GI has an open-set false-match rate of 0.617, and its calibrated match threshold is 1.0, so it can never return *match*. It entered at half weight because it scored 11/18 = 0.61 on the imitation test, against a 0.60 cutoff, from three authors (95% CI 0.36–0.83). One window fewer and the synthesis returns the prior.
   - Why it matters: the posterior's movement away from 0.5 may be largely built into the likelihood design. A method that can only say "inconclusive" or "non-match" feeds the "not in set" hypothesis.
   - Fix:
     - Report what posterior GI produces on the 22 candidate decoys and the 21 control decoys.
     - Report the posterior's sensitivity to GI's weight across the imitation test's confidence interval.
     - State plainly in the abstract that the 0.744 rests on one failed method.
     - The chunk-dependence assumption also needs spelling out: "treating chunks as independent" gives 1.00, so what does the main analysis assume?

3. **"No method called any control passage a match" is uninformative as written, and it conflicts with the benchmark.**
   - The problem: GI and the style encoders cannot call a match at all. The candidate models have benchmark false-match rates of 22–47%. At 22%, the chance of 0 false matches in 21 control decoys is about 0.78²¹ ≈ 0.006.
   - Why it matters: either the blind-run thresholds or score distributions differ from the benchmark's, or the control decoys are easier than benchmark negatives. In either case the benchmark error rates the paper relies on do not describe the blind run. The Discussion's "none called a stranger's text a match" reads as validation, but the benchmark contradicts it.
   - Two further issues:
     - The candidate decoys come from held-out tails of the same works used for reference. That is an in-work task, much easier than the cross-genre problem the Book of Mormon poses.
     - Candidate-decoy true matches fall with size (20/14/11) while false matches also fall. That is a threshold trade-off, not evidence that larger models are better. The Discussion's "larger models would sharpen it" claim needs threshold-free comparison (ROC/AUC) on the benchmark.
   - Fix:
     - Reconcile the blind-run and benchmark operating points.
     - Use cross-work decoys.
     - Report ROC/AUC by size.
     - Remove the control-decoy claim for methods that cannot reach *match*.

4. **Size comparisons are confounded, and fine-tuning dose varies roughly 100-fold across candidates.**
   - The size confound: the 590M differs from the other sizes in architecture (QK-norm), peak learning rate, and GPU count. So "false matches fall with size" is not a size effect.
   - The dose problem: with 3 epochs at a fixed rate, the number of optimizer updates scales with sample size. That runs from 2,720 words (Joseph Smith) to 277,391 (Ethan Smith). A tiny sample barely moves its model, so its score stays near the base model's, while a large sample adapts the model strongly to one work's topic and genre.
   - Why it matters: the ranking of Joseph Smith's 2.7k-word revelations as closest to 159–168 of 168 chunks could be partly a sample-size artifact of the log-loss-margin statistic. The section 7 minimum-sample analysis is not reported for the authorial language models (ALMs).
   - Fix:
     - Rerun the candidate models with every sample subsampled to 2,720 words, several seeded draws each, and a matched number of steps.
     - Report each method's minimum sample size per section 7.
     - Add a QK-norm 297M, or say plainly that the size series is not a controlled comparison.

5. **The register confound is mis-stated, and the Amendment 44 reasoning is asymmetric.**
   - The problem: the paper says Joseph Smith's revelations are "the only sample in the text's own register," and that every other sample is "sermon, treatise, history, romance or newspaper prose." But Hunt's *The Late War* is pseudo-biblical and is a candidate, and the pseudo-biblical control model also exists. The methods still rank Joseph Smith above both.
   - Why it matters:
     - Register alone therefore does not obviously explain the ranking. Either the paper's register explanation is too generous, or something else is driving the result, such as the sample-size effect in point 4 or the contemporaneity issue below.
     - Separately, the claim that his ordinary prose's "distance is the informative direction" does not follow. If register dominates the features, distance from out-of-register prose is expected whoever the author is. Neither direction is informative.
   - Contemporaneity: Amendment 43 keeps shared runs from "the same weeks." For revelations dictated alongside the text, by the same speaker, to the same scribe, this is a channel of shared wording, not independent style. A sensitivity run masking those runs should be reported beside the main one, even if the masking is not adopted.
   - Fix:
     - Add size-matched pseudo-biblical samples, from Hunt, Snowden and the curated control authors, as register-matched competitors to the revelations.
     - Report the same-weeks-masked sensitivity run.
     - Revise the asymmetric claim.

6. **Registered features are missing, and the King James masking does not remove register.**
   - The missing features: section 5.1 registers character 3-/4-grams, POS 2-/3-grams and a content-word set. The paper reports only most-frequent-word features. Section 12 commits to reporting every deviation, and none is stated.
   - The masking: passim removes aligned spans (6.82%). It does not remove pervasive non-aligned King James idiom ("and it came to pass," "behold," -eth/-est forms). That idiom dominates MFW vectors and Delta.
   - The validation: the masking check on 200 alignments appears to measure precision. Recall against known quotations, for example the Isaiah and Matthew blocks and the shorter embedded quotations, is not reported.
   - Fix:
     - Report the registered feature sets, or a dated amendment explaining their omission.
     - Report passim recall on a seeded set of known King James quotations.
     - Add a register-neutralised sensitivity run, for example with words of high King James-to-period frequency ratio removed from the feature set, for Delta, GI and the ALM inputs.

7. **The source text differs in medium from the corpus.**
   - The problem: the Book of Mormon comes from Joseph Smith Papers transcriptions; candidates and controls are largely OCR. The paper does not say which of the original manuscript, printer's manuscript or 1830 edition was scored, or how manuscript spelling and missing punctuation were handled. OCR noise, spelling and punctuation affect tokenisation, language-model loss, character n-grams, the grammar fold and the dating models.
   - Why it matters: this alone could move the transformer dating (1755 vs 1805), which the King James register did not move in validation. It could also move language-model margins.
   - Fix: score an OCR of an 1830-edition scan through the identical pipeline, or degrade the transcription with matched OCR noise, and report how the results change.

8. **Q2: the registered result is replaced by an interpretation in the abstract.**
   - The problem: under H2's registered rule, *The Late War* and *The First Book of Napoleon* are significant parallels. The abstract and the Q2 reading instead say no source shares wording "beyond what its genre shares." That comparison comes from a post hoc within-genre check (Amendment 13) and the fact that Ilive's *Jasher* exceeds them.
   - The triage design also cannot add SPECIFIC labels, only remove them:
     - the second pass sees every SPECIFIC but only 10% of the rest;
     - a pair needs both passes to count as specific;
     - both passes use one model family, with κ = 0.505.
   - Calling 100% of pairs "explained" by King James or stock phrasing overstates such a filter.
   - Fix:
     - Say in the abstract that H2 is met for these two works under the registered rule, then give the genre caveat.
     - Have the second review read a larger random share of COMMON labels.
     - Report how many pairs would be specific under either pass.

9. **Q3: the registered dating rule is replaced, and the H3c comparison ignores how strongly each text imitates.**
   - The rule change: Amendment 19 (post hoc) replaced the interval rule. The result under the registered rule, presumably "neither window," should appear in the abstract beside H3b.
   - The comparison: "More archaic than period imitations" (1661 vs 1734) does not account for how heavily each text imitates. The Book of Mormon's density of King James grammatical forms is very likely higher than most of the 25 controls'. Since imitation alone moves the grammar model about 53 years, a dose-response explanation is unexamined.
   - Fix: across the pseudo-biblical controls, regress predicted year on an imitation-intensity index built from features outside the dating model. Then test whether the Book of Mormon sits on the line. Only a residual below the line supports "more archaic than imitation explains."

10. **The prior-study replications (BOM-22) are not reported.**
    - The problem: the claims table "contradicts" Jockers et al. (2008) and Larsen et al. (1980) and "supports" Fields et al. (2011). It shows no replication of their numbers on their own data and settings.
    - Why it matters: without reproducing the original nearest-shrunken-centroid (NSC) result first, a reader cannot tell whether the divergence comes from the open-set design, from corpus differences, or from implementation.
    - Fix:
      - Add a replication table giving each study's published result, the reproduction under its own setup, and the result under this study's masking and open set.
      - Change one factor at a time.

11. **H1c's test cannot tell narrators from dictation order, and the verdicts go further than the test.**
    - The problem: narrators are contiguous blocks of the dictation, so dictation order will explain narrator differences almost by construction. The 0.96 benchmark accuracy for distinct authors needs a stated sample size and register match, as rule 6.3 requires.
    - Why it matters: "not separable at benchmark level" is a power-limited non-result. It does not show the narrators are "not distinct," yet Larsen is marked contradicted and Holmes supported.
    - Fix:
      - Report a positive control: multiple known authors writing in one shared pseudo-biblical register, at matched chunk sizes.
      - Report a negative control: one author writing in several voices.
      - Reword the claim verdicts accordingly.

12. **The sweep is reported as evidence although it failed its usability rule.**
    - The problem: section 6.6 makes the sweep usable only at 70% top-1, and it reached 27–35%. The abstract still presents "finds no lead" as a result.
    - Fix: present the sweep as unusable under the registered rule, with the no-lead outcome uninterpretable, and remove it from the abstract's evidence list.

## Minor points
1. Several counts disagree within the paper:
   - Joseph Smith's revelations: 2,702 vs 2,720 words.
   - His ordinary prose: 11,300 words vs about 11,600 tokens.
   - Swept authors: 23,872 vs 23,875.
   - Expected false leads per query: 0.035 vs Amendment 40's ~0.0035.
2. In the imitation test, the ALMs are scored on 17 windows while other methods use 18. Explain the dropped window.
3. The Part II §4 imitation table is broken by a blank row.
4. The 1B narrative is inconsistent:
   - Amendment 38 says the loss recovered within about 230 steps.
   - Amendment 39 says the run was unstable "at every rate tried."
   - Amendment 26 says 8 H100s, then 4.
   - Amendment 37 registered the 1B as a reported size, so its replacement is a deviation and should be named as one.
5. The post hoc list in the Limitations omits Amendments 38 and 41–44. The Discussion's "three decisions were made after results existed" undercounts against the labelled post hoc amendments (8, 13, 19, 20, 21, 25, 26, 38, 41–44).
6. Section numbering restarts in Part I, so there are two "section 1"s. There is also a dangling reference to `results_so_far.md` §1.5.
7. The contamination rule removes volumes with 20 or more shared 12-token strings, against 4.2's single string. Report how many volumes holding 1–19 strings remain in base-model training.
8. Report the OCR-exclusion counts under 4.3's 10% character-error-rate rule, and character error rate by control group and candidate. OCR quality probably correlates with genre.
9. V1 at the chosen rate is identical to the primary method (1e-5 at every size). Report it once rather than as a separate row.
10. ENSC reaches 1.000 closed-set accuracy with 0.661 false matches. Explain why it was retired rather than reported at its own operating point.
11. The Federalist closed-set accuracy at 125M (0.769) suggests the benchmark is small. Give the number of tests per task in the benchmark table.
12. The manuscript section's statement that "every scribed chunk is Cowdery's" should be reconciled with the other known scribes of the original manuscript. Explain whether that comes from segmentation or from survival (72% lost).
13. The claims register counts Hunt both as a candidate and inside the pseudo-biblical control group. State whether *The Late War* was excluded from the control models and from GI's imposter pool.
14. Give Cohen's κ for the story-order event extraction as well as median agreement. The extraction was validated on King James chapters only, not on period prose.

## Recommendation
Major revision. The infrastructure and disclosure are strong, but several headline claims are worded more strongly than the registered results support:
- a posterior that excludes the top-ranked candidate and rests on one match-incapable method;
- control-decoy "validation" that the benchmark contradicts;
- H2 re-read away from its registered outcome;
- registered features and replications that are missing.

The fine-tuning-dose and source-medium confounds need controlled reruns before the Joseph Smith ranking or the dating comparison can be interpreted.
