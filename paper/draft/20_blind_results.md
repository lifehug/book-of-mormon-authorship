# Results of the blind run (BOM-32, BOM-35)

Unblinded 2026-11-10 (`data/blind/unblinded.json`; first read in `docs/results-first-read.md`).
Read in the order of trust fixed before unblinding (`docs/method-reliability.md`): the primary
language-model method and the classical methods first; every other method beside them; V2 carries
no weight.

## Decoys

| Method | Right candidate ranked first (of 22 candidate decoys) | Control decoys called a match (of 21) | Candidate decoys matched to their author |
| --- | --- | --- | --- |
| Burrows' / Cosine Delta | 20 / 15 | (no match call) | |
| General Imposters | 19 | 0 | 0 (cannot reach *match* at its registered threshold) |
| Style encoders 297M / 590M | 16 / 18 | 0 | 0 (registered rule) |
| Candidate models 125M / 297M / 590M | 20 / 21 / 19 | 0 | 20 / 14 / 11 |

The run is valid by section 8's rule: decoys are identified at about benchmark accuracy, and no
method calls a passage by a non-candidate a match.

## Attribution (Q1)

**Match calls.** General Imposters and the style encoders return no *match* for any of the 168
chunks under the registered thresholds. The candidate models return 10, 5 and 3 matches by size
(125M, 297M, 590M), fewer than their benchmark false-match rates (22-47%) would produce for text by
no candidate. **H1a (a candidate matched by two independent families on both halves) is not
supported for any candidate.**

**The author sweep.** No author of the 23,872 swept passes both lead thresholds on the discovery
half (expected by chance 0.035 per query; `data/sweep/calibration.json`). The nearest by both
signals are writers in the scriptural and prophetic register (John Wroe, George Fox, William
Sewel), none near a threshold.

**Synthesis (6.7).** Posterior over the primary candidates (pre-1830 confirmatory samples), both
halves: **not in set 0.744** (prior 0.5); Gilbert J. Hunt 0.089, Solomon Spalding 0.085, Ethan
Smith 0.082. Both model-based families carry an imitation weight of zero (section 9 of the
pre-registration; they were misled by deliberate imitation, BOM-31), so only General Imposters
enters and the posterior is identical at every model size. Across the prior grid (0.2-0.8) "not in
set" runs 0.42-0.92; under equal family weights or treating chunks as independent, 1.00; dropping
General Imposters returns the prior. Secondary set (post-1830 samples, Amendment 5): not in set
0.715, Pratt 0.122. **H1b ("none of these") is favoured for the three candidates the synthesis can
test, but not established**, since no method passes the open-set bar. The synthesis excludes, by
the registered rule (3: samples under 10,000 words), the two candidates the methods rank closest:
Joseph Smith (2,702 pre-1830 words) and Cowdery (1,309). They are untested by it, not ruled out.

**Narrators, scribes and dictation order (6.3, H1c).** The four principal narrators separate at
0.744 (chance 0.277, p 0.001) and the first and last parts of the dictation at 0.758 (chance
0.502, p 0.001); every scribed chunk is Oliver Cowdery's, so scribes cannot be compared. Both are
below the 0.96 the same method reaches on distinct authors: narrators are **not separable as
different authors**, and dictation order explains the differences about as well.

## A leakage found after unblinding, and the rerun (Amendment 43, post hoc)

After unblinding, the 590M candidate models ranked Oliver Cowdery's pre-1830 sample closest to 119
of 168 chunks. That sample, his "Articles of the Church of Christ" (June 1829), is 40% word-for-word
Book of Mormon text: it copies the sacrament prayers and baptismal instructions. Parley P. Pratt's
books also quote the text. The sealing rule had been enforced on the training corpus but not on
candidate samples.

Every run a candidate sample shares with the text was classed by a rule fixed before the matches
were read: biblical; period stock phrasing; written before the matching passage was dictated; in
the same weeks; or after it (`docs/bom-overlap-analysis.md`). Only **quotations** were dropped:
passages of 20 or more words written after the matching passage existed. Masking every shared run
was rejected because it would also remove genuine shared idiom, above all from Joseph Smith's
1828-29 revelations, which contain no quotation (one shared phrase predates the passage it
matches; the rest were dictated in the same weeks) and are unchanged. The candidate models were
retrained and the sealed set rescored by every method that reads candidate samples.

| Method | Registered run: ranked closest (of 168) | Without quotations | Matches |
| --- | --- | --- | --- |
| Cosine Delta | Joseph Smith 131, Hunt 31 | Joseph Smith 148, Hunt 20 | 0 -> 0 |
| Burrows' Delta | Joseph Smith 77, Hunt 47, Pratt 37 | Joseph Smith 91, Hunt 49, Pratt 25 | 0 -> 0 |
| General Imposters | Pratt 74, Joseph Smith 48 | Joseph Smith 66, Pratt 66 | 0 -> 0 |
| Candidate models 125M / 297M / 590M | Joseph Smith 82 / 133 / 46; Cowdery 29 / 34 / 119 | Joseph Smith 159 / 168 / 131 | 10 / 5 / 3 -> 2 / 2 / 0 |
| Synthesis, not in set | 0.744 | 0.744 | |

The Cowdery ranking was leakage and disappears. Match calls fall, the synthesis is unchanged, and
every method ranks Joseph Smith's pre-1830 sample closest. The registered run stays the main
record (git tag `blind-registered-2026-11-10`); the rerun is reported beside it (`data/*/a43/`).

## Register: Joseph Smith's revelatory and ordinary prose (Amendment 44, post hoc)

Joseph Smith's only pre-1830 sample is revelation (1828-29, 2,702 words), written in a scriptural
voice like the text's; every other candidate sample is a sermon, treatise, history, romance or
newspaper prose. His non-revelatory writing of 1831-33 (letters and the 1832 history, about 11,600
tokens) was pooled into one unit and scored beside it. Mean rank among 12 candidate samples on the
168 chunks (1 = closest):

| Method | Revelations, 1828-29 | Ordinary prose, 1831-33 |
| --- | --- | --- |
| Candidate models 125M / 297M / 590M | 1.1 / 1.0 / 1.3 | 6.1 / 6.3 / 5.4 |
| Style encoders 297M / 590M | 1.1 / 1.5 | 4.7 / 5.7 |
| Cosine Delta | 1.2 | 3.3 |
| General Imposters | 3.6 | 6.1 |
| Burrows' Delta | 7.7 | 2.7 |

Seven of eight methods place his revelations closest and his ordinary prose in the middle;
Burrows' Delta, which rests most on function words, reverses them. The closeness to Joseph Smith
runs mainly through the revelatory register, which is the register of the text. His ordinary prose
is all post-1830: its closeness would be uninformative (he had read the book) and its distance is
the informative direction. No ordinary prose of his survives from before 1830, so his style before
the book cannot be tested.

## Dating the text (Q3)

Of the 215 segments of the 168 chunks, the grammar model (which decides H3) places 78% of segment
medians before 1700 and 7% in 1780-1830 (median of medians 1661): **H3b**. The lexical model (1736)
and the transformer cross-check (1755) place the majority in neither window. **H3c is rejected**:
the text dates earlier than the 1780-1830 pseudo-biblical control volumes (grammar 1661 vs 1734,
lexical 1738 vs 1794; permutation p 0.0001; `data/dating/h3c.json`). The grammar model dates King
James imitation about 53 years early in validation, so part of the early date is the biblical
register; the text is nevertheless more archaic by these measures than the period's other biblical
imitations, and the transformer, which imitation did not move in validation, still dates it before
them (1755 vs 1805).

## Public claims (BOM-42)

Seventeen public claims from critical, apologetic and academic sources were registered with their
decision rules before any result (`data/claims/register.yaml`). Verdicts: supported 2, contradicted
6, mixed 4, not addressed 1, untestable 4 (`docs/claims-verdicts.md`). Supported: with "none of the
above" allowed, no nineteenth-century candidate is the author (Fields 2011); the narrators are not
distinct and sit close to Joseph Smith's revelations (Holmes 1992). Contradicted: dependence on
*View of the Hebrews*; Rigdon and Spalding as contributors (Jockers 2008); distinct narrators
(Larsen 1980); Spalding's manuscript as source; Cowdery or Rigdon as author; an 1820s environment
in the language (Brodie 1945; language only). Mixed: *The Late War*; early-modern syntax that
imitation cannot explain (Skousen and Carmack); the American pseudo-biblical genre (Shalev); *The
First Book of Napoleon*. An untestable claim is not a contradicted one.
