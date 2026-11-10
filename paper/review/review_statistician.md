# SIMULATED review: statistician

> **SIMULATED.** Written by an AI model (claude-opus-5-5) acting as a statistician referee, 2026-11-10. No human reviewed this work. Shown: the draft and the pre-registration, SHA-256 `753deba893c96bfb08e7ddfaa15be64c81a3f89f7a138c86fe1d3eb4b8309368`.

## Summary
The paper applies stylometric, language-model, borrowing and dating methods to the 1830 Book of Mormon text under a public pre-registration with 44 amendments. It asks three questions: whose writing the text resembles (Q1), what it borrowed (Q2), and when its English dates from (Q3). The headline claims are:
- No candidate author is matched.
- A Bayesian synthesis favours "none of these candidates" at 0.744.
- A sweep of 23,872 period authors finds no lead.
- No proposed source shares wording or plot beyond its genre.
- The text's grammar dates mostly before 1700 and is more archaic than period biblical imitations.

The authors openly report that no attribution method passes the registered open-set bar. They therefore present the attribution results as "graded evidence." The documentation and candour are well above the norm for this literature. My concern is that several headline sentences go beyond what the registered decision rules and the error rates allow, and some do not follow from the numbers at all.

## Major points

1. **The synthesis contradicts the registered exclusion rule.**
   - **The problem.** Section 7 of the pre-registration states: "A method that fails is reported and excluded from the synthesis." No method passes, so the registered synthesis has no admissible input, and the registered answer is the prior or undefined. The paper instead reports 0.744 from General Imposters (GI) alone, and GI failed the benchmark with a 0.617 false-match rate. GI also cannot return *match* at all, because its calibrated threshold is 1.0, the maximum possible score.
   - **Why it matters.** A family that can only emit "inconclusive" or "non-match" will push the posterior mechanically toward "not in set" whatever the truth. The 0.744 is therefore largely a property of GI's threshold, not of the text.
   - **What would fix it.**
     - Report the registered result: no admissible family, posterior equal to the prior.
     - Label the GI-only posterior as a post hoc deviation.
     - Show what posterior GI's band structure produces when a candidate's own held-out text is the query. If that posterior also favours "not in set," the 0.744 is uninformative.

2. **"None of these candidates" silently excludes the candidate the methods rank first.**
   - **The problem.** The prior is shared only among candidates with reliable samples. Joseph Smith (2,720 words) and Cowdery's pre-1830 sample (1,310 words) are therefore not in the set, and "not in set" absorbs them. The abstract nonetheless lists Joseph Smith among candidates "not matched" and then reports "none of these candidates 0.744."
   - **Why it matters.** A reader will take 0.744 as evidence against Joseph Smith. By construction it is not, and Joseph Smith is the sample nearly every method ranks closest.
   - **What would fix it.**
     - State explicitly, in the abstract, which candidates enter the posterior. The paper also lists posteriors only for Hunt, Spalding and Ethan Smith; Rigdon and Phelps are above the 10,000-word floor, so their absence needs explaining.
     - Rename the quantity to something accurate, such as "not among Hunt, Spalding, E. Smith, Rigdon, Phelps."

3. **The sensitivity analysis shows the independence assumption drives the posterior.**
   - **The problem.** The 168 sealed chunks are 121 chunks of 2,000 words and 47 chunks of 5,000 words cut from the same text, so the same words are scored twice. The paper does not state how chunk-level observations are combined in the main analysis. "Treating chunks as independent" yields 1.00, and the prior grid runs 0.42-0.92.
   - **Why it matters.** When the result swings from 0.42 to 1.00 across reasonable modelling choices, the data are not determining it. The method-family weights (accuracy × imitation weight) are also ad hoc tempering, not a likelihood.
   - **What would fix it.**
     - State the dependence model explicitly.
     - Use a single non-overlapping chunk scheme in the posterior.
     - Report the effective number of independent observations, for example from between-chunk correlation of scores.
     - Give the posterior as a range over the dependence assumption, not a point value.

4. **The decoy results reveal calibration shift, and that undermines the inference drawn from match counts.**
   - **The problem.** On the benchmark, the candidate models falsely match non-authors at 22-47%. On the 21 control decoys they falsely match 0. At p = 0.218, P(0/21) ≈ 0.78²¹ ≈ 0.005; at p = 0.47 it is about 10⁻⁶.
   - **Why it matters.**
     - The benchmark false-match rates do not transfer to this distribution; the decoys are a different genre and drawn from different pools.
     - The paper argues that 10/5/3 Book of Mormon matches are "fewer than their benchmark false-match rates would produce for text by no candidate." That argument is invalid when the threshold behaves differently on the target distribution.
     - The abstract's "no method called any of the 21 control passages a match" is vacuous for GI and the style encoders, which cannot return *match* at all.
     - The candidate decoys are held-out tails of the very documents used as references. Within-document identification is much easier than the Book of Mormon task, so 20/22 overstates real-world sensitivity.
   - **What would fix it.**
     - Drop the comparison of match counts to benchmark rates.
     - Report exact binomial intervals on decoy rates and say which methods could not have produced a false call.
     - Add cross-work candidate decoys: a different work by the candidate from the one used as reference.

5. **The run was declared valid without the registered accuracy criterion being met.**
   - **The problem.** Section 8 requires decoys to be "identified at the benchmark accuracy or the run is repeated." Cosine Delta ranked the right candidate first for 15/22 decoys (0.68) and the 297M encoder for 16/22 (0.73). Both are below their benchmark closed-set figures, yet the paper declares the run "valid... at about benchmark accuracy."
   - **What would fix it.** Specify, ideally in advance, a tolerance such as non-inferiority against the benchmark with an interval. Report per method whether that tolerance was met, and either repeat the run or document the fault, as section 8 requires.

6. **The Joseph Smith ranking is confounded by sample size and by contemporaneous production, as well as by register.**
   - **The problem.** The register confound is acknowledged, but two others are not addressed.
     - *Sample size.* The 2,720-word sample sits far below every other candidate's (21k-277k). Delta-family distances computed from small profiles, and language models fine-tuned on very little text, behave differently from those built on large samples. Rank comparisons across such unequal samples are not like-for-like.
     - *Shared production circumstances.* The revelations were dictated in the same weeks as the text, and Amendment 43 explicitly kept contemporaneous shared runs. Shared phrasing from the same dictation sessions is a form of overlap the leakage rule chose not to treat as leakage.
   - **The register argument does not support the asymmetry claimed.** The paper says the post-1830 prose's distance "is the informative direction." But a register mismatch predicts that distance regardless of authorship, so the distance is not informative either.
   - **What would fix it.** Run a placebo analysis:
     - Add equal-size (about 2,700-word) scriptural-register samples from non-candidates, such as Wroe, Snowden's imitation, Shaker or Southcottian revelations, or the pseudo-biblical controls, as pseudo-candidates.
     - Subsample every candidate to 2,700 words and re-rank.
     - Report rankings with the contemporaneous shared runs masked as a sensitivity analysis.

     If any scriptural-register sample of this size ranks first, the Joseph Smith ranking carries no authorship information.

7. **The dating test (H3c) uses pseudo-replication, and H3b is not diagnostic.**
   - **The problem.**
     - The permutation test (p = 0.0001) compares 215 segments of a single text against control volumes. Segments of one book are not exchangeable with segments of different books. The correct unit is the volume: the Book of Mormon's median against the distribution of the 25 control volumes' medians, which gives at best p ≈ 1/26.
     - In validation, 7 of the 25 genuine 1780-1830 pseudo-biblical controls were themselves called H3b. H3b therefore occurs routinely for period imitations.
     - The grammar model's 53-year shift under King James imitation is measured on controls whose King James density may differ from the Book of Mormon's. Only aligned spans (6.8%) are masked, and unaligned scriptural style remains.
     - The lexical model (1736) and the transformer (1755) both put the text in neither window. The transformer comparison (1755 vs 1805) has no reported test.
   - **What would fix it.**
     - Test at the volume level.
     - Adjust the comparison for scriptural density, for example by regressing predicted year on King James-likeness across the controls and reporting the Book of Mormon's residual.
     - Report the 7/25 base rate beside the H3b call in the abstract.
     - Soften "more archaic than period imitations" to what one text against 25 volumes can support.

8. **The borrowing conclusions overstate what was found.**
   - **The problem.**
     - By the registered H2 rule, *The Late War* and *Napoleon* are significant parallels, at p = 0.0006 and 0.0003; both survive Holm correction over the four named sources. The abstract nonetheless says no proposed source shares "specific wording beyond what its genre shares." That rests on the post hoc within-genre comparison with Jasher, which is a single comparator with no interval.
     - The whole-corpus rule flags 2,044 volumes, roughly 1% of 204,520, which is what chance alone predicts. That shows the rule has no corpus-level multiplicity control. It does not discredit the named-source results.
     - The triage step that "explains" every similarity has these weaknesses:
       - Its first-to-second-pass agreement is moderate (κ = 0.505).
       - It is asymmetric: every SPECIFIC label is re-reviewed but only 10% of the others, and a pair counts as specific only if both passes agree. The design is biased toward zero.
       - It has no known-borrowing positive control.
     - "36% biblical / 64% stock" describes the registered pairs, not "every surfaced similarity."
   - **What would fix it.**
     - Report H2 as met for the two sources under the registered rule.
     - Present the genre comparison as post hoc, with a genre-level null distribution rather than a single comparator.
     - Validate the triage on pairs with known borrowing, such as Jasher against Genesis or the *Late War* against the King James Bible.
     - Apply the second review symmetrically.

9. **Several failed instruments are presented as evidence.**
   - **The sweep.** It reaches 27-35% top-1 accuracy against the registered usability bar of 70%, so it is unusable by its own rule. "Finds no lead" from an unusable instrument has very low power and should not appear in the abstract as a finding.
   - **The narrators (H1c).**
     - The comparison of 0.744 accuracy against the 0.96 achieved on distinct authors is not made "at the same sample size" and number of classes, as 6.3 requires.
     - Narrator and dictation order are largely collinear, so similar accuracies are expected whichever factor drives style.
     - "Not separable" is a failure to reject, yet the claims register converts it into "supported" (Holmes) and "contradicted" (Larsen).
   - **The Discussion's opening sentence, "Every check on known text passed,"** is false:
     - no method passed the benchmark;
     - the model-based methods failed the imitation test;
     - every Amendment 9 known-answer test failed;
     - the sweep failed its usability bar.
   - **What would fix it.**
     - Remove the sweep from the abstract's findings.
     - Run a matched-size, matched-class benchmark for H1c, and use a variance-partitioning model (for example narrator and dictation order jointly) as 6.3 requires.
     - Rewrite the claims verdicts that rest on non-rejection as "not supported" rather than "contradicted" or "supported."
     - Correct the Discussion.

10. **The garden of forking paths is not quantified.**
    - **The problem.** Results are reported across 3 model sizes, 4 language-model variants, 2 threshold readings (Amendment 33), several reruns, and numerous post hoc amendments. Some of these amendments change decision rules: 19 (H3), 25 (the open-set threshold) and 8 (the Delta family). The Limitations list of post hoc decisions omits 38 and 41-44.
    - **Why it matters.** Without a count of the tests run, readers cannot judge selective emphasis. For example, the Joseph Smith ranking is presented through the Amendment 43 rerun, while the registered run had Cowdery first at 590M.
    - **What would fix it.**
      - Publish one table of every hypothesis × method × size × variant test, marking which are confirmatory.
      - Apply family-wise or FDR control to the confirmatory set.
      - Complete the post hoc list.

## Minor points
1. **Internal inconsistencies to correct:**
   - Authors swept: 23,872 vs 23,875.
   - Joseph Smith pre-1830 sample: 2,720 vs 2,702 words.
   - Joseph Smith's ordinary prose: 11,600 tokens vs 11,300 words.
   - Model sizes: the abstract says 125M/297M/590M, while Amendment 37 says 1B.
   - Imitation windows: "of 17" vs 18.
   - Amendment 26's GPU count.
2. **Empty and broken tables.** The benchmark table has empty cells for the per-task accuracy of GI, ENSC and the style embeddings; fill them or explain. The imitation table is broken by a blank line.
3. **Missing intervals.** Give exact binomial or bootstrap intervals for:
   - every decoy rate;
   - the candidate-model held-out accuracies (Rigdon rests on 2 tests and Phelps on 3);
   - the posterior.
4. **Delta disclaimer.** Amendment 8 commits to stating, beside every Delta result, that Delta failed section 7 (62-63% on fresh authors). The blind-run tables omit this.
5. **Reproducibility.** The V2 discrepancy between the Mac and H100 runs at the same seed signals a nondeterminism problem. Report whether the primary method's results are bit-identical across hardware, and give the evidence.
6. **Manuscript evidence.** Corrections cluster by page and passage, so the Fisher tests treat dependent events as independent. Use a page-level model, for example a mixed model or a permutation over pages.
7. **Synthesis weights.** The imitation weights rest on 18 windows from 3 authors, with intervals spanning roughly 0.4 to 0.9. Applied as hard full/half/zero weights, these zero out two families on very thin evidence. Report the synthesis under the interval endpoints.
8. **Numbering and cross-references.**
   - Section numbering collides between the Introduction and Part I.
   - "Section 1.5 of `results_so_far.md`" refers to a file outside the paper.
   - Part IV says the scribe/narrator comparison "runs only after unblinding," which is stale now that it has run.
9. **Amendment 40.** The literal plausibility gate passes 94% of authors. Note that the amended gate was set after the gate's pass rate was seen, even though no lead had been seen.
10. **Posterior table.** Report the full secondary posterior and give each candidate's posterior beside its sample size.

## Recommendation
Major revision. The study is unusually transparent and its core negative findings may well hold, but its headline sentences rest on four things that do not support them:
- a synthesis that the registered rules exclude;
- a "none of these" that silently omits the top-ranked writer;
- a segment-level test that inflates the dating significance;
- validity claims for decoys and benchmarks that the reported numbers contradict.
