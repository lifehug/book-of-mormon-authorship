# First read of the blind results (BOM-32, BOM-35)

Written 2026-11-10, the morning of unblinding, from `data/blind/unblinded.json`,
`data/synthesis/posterior_<size>.json` and `data/benchmark/imitation.json`. Read in the order of
trust set out before unblinding (`docs/method-reliability.md`). Blinding was simulated (the
scoring ran without the key; the analyst is an AI model). This is a first read for the owner, not
the paper; every number comes from the committed files and can be recomputed.

The project does not argue for or against divine inspiration. It asks which known writers, if any,
the text resembles closely, by methods whose error rates are measured, and reports the answer with
its uncertainty.

## 1. The sanity check passed: the decoys

The sealed set held 43 decoys beside the 168 Book of Mormon chunks: 22 held-out passages by the
candidates themselves and 21 control passages by nobody in the set.

| Method | Decoys: right candidate ranked first | Control decoys wrongly called a match | Candidate decoys correctly called a match |
| --- | --- | --- | --- |
| Burrows' Delta | 20 / 22 | (no match call) | |
| Cosine Delta | 15 / 22 | (no match call) | |
| General Imposters | 19 / 22 | 0 / 21 | 0 / 22 (cannot reach "match" at its registered threshold) |
| Style encoder 297M / 590M | 16 / 22, 18 / 22 | 0 / 21 | 0 / 22 (registered); 10 / 22 (achievable rule) |
| Candidate models 125M / 297M / 590M | 20, 21, 19 of 22 | **0 / 21 at every size** | 20, 14, 11 of 22 |

Every method ranks real candidate text correctly most of the time, and **no method called any
control passage a match**. The machinery works on text whose answer is known.

## 2. Who the Book of Mormon chunks rank closest to

Of the 168 chunks, how many rank each candidate first (all candidates, including the post-1830
samples):

| Method | Ranked first most often |
| --- | --- |
| Burrows' Delta | Joseph Smith 77, Gilbert J. Hunt 47, Parley P. Pratt 37 |
| Cosine Delta | Joseph Smith 131, Hunt 31 |
| General Imposters | Pratt 74, Joseph Smith 48, Hunt 39 |
| Style encoder 297M | Joseph Smith 150, Oliver Cowdery 14 |
| Style encoder 590M | Cowdery 102, Joseph Smith 58, Hunt 8 |
| Candidate models 125M | the pseudo-biblical control texts 126 (no candidate) |
| Candidate models 297M | Joseph Smith 106, the pseudo-biblical controls 36, Cowdery 26 |
| Candidate models 590M | Cowdery 109, Joseph Smith 45, pseudo-biblical controls 11 |

The candidates ranked closest are, across methods, **Joseph Smith and Oliver Cowdery**, the
documented dictator and principal scribe of the text, and, for some methods, Pratt and Hunt.

**Caveats that bear directly on this:**

- **The Joseph Smith and Cowdery samples that rank first are tiny and flagged "unreliable
  sample"** in the plan before any scoring: Joseph Smith's pre-1830 dictated sample is 2,720 words,
  Cowdery's pre-1830 handwritten sample 1,310 words. A model fine-tuned on that little text barely
  differs from the base model, which can push it to the top of a ranking for reasons unrelated to
  authorship.
- **Their pre-1830 texts are the revelations and letters of 1828-30**, written in the same
  scriptural register as the Book of Mormon and partly recorded by the same scribes. Resemblance
  to them is resemblance to the text's own production circle, not evidence about an outside
  source.
- **Pratt's, Rigdon's, Phelps's and Cowdery's printed samples are post-1830**, written after the
  Book of Mormon by readers of it; the pre-registration keeps them in a secondary set for that
  reason (Amendment 5).
- **Ranking first is not a match.** Every method must rank someone first.
- **The answer moves with model size** (125M: the pseudo-biblical controls; 297M: Joseph Smith;
  590M: Cowdery), which by the reliability rules counts against reading much into any one size.

## 3. Match calls: almost none

| Method | Chunks with any "match" call (of 168) |
| --- | --- |
| General Imposters (registered and achievable rules) | 0 |
| Style encoders (registered rule) | 0 |
| Style encoders (achievable rule, 50% false-match rate) | 297M: Joseph Smith 76, Cowdery 12; 590M: Cowdery 103, Joseph Smith 87, Hunt 9 |
| Candidate models 125M | 10 (Pratt 4, Cowdery 4, Joseph Smith 2) |
| Candidate models 297M | 5 (Cowdery 3, Joseph Smith 2) |
| Candidate models 590M | 3 (Cowdery 3) |

The candidate models' benchmark false-match rates are 22-47% (the share of tests by someone else
on which some wrong candidate still reached "match"), so 3-10 matches among 168 chunks (2-6%) is
fewer than those rates would predict for text by nobody in the set; it is not evidence of a match. The style
encoders' achievable rule matches often, but that rule's measured false-match rate on the
benchmark is 50%: it says "match" to the wrong author half the time.

## 4. The synthesis: "not in set" most probable, from classical evidence only

The registered synthesis weights each family by benchmark accuracy times its imitation weight
(section 9). **Both model-based families (candidate models and style encoders) earned an
imitation weight of zero at every size**: they were fooled by deliberate imitation (BOM-31). So
only the classical family (General Imposters) enters the posterior, and the posterior is the same
at every size.

| Primary candidates (pre-1830, confirmatory samples), both halves | Posterior |
| --- | --- |
| Not in set | **0.744** (prior 0.5) |
| Gilbert J. Hunt | 0.089 |
| Solomon Spalding | 0.085 |
| Ethan Smith | 0.082 |

With the prior on "not in set" anywhere from 0.2 to 0.8, "not in set" goes to 0.42-0.92. The
evidence moves toward "none of these" from any prior, but by a modest amount, and from one family.

## 5. The whole-library sweep: no lead

The sweep compared the text with 23,872 authors of 1780-1830 English. **No author passed both
lead thresholds** (expected by chance: 0.035). The nearest by both measures are writers in the
scriptural or prophetic register (John Wroe, George Fox, William Sewel, among others), none near the
lead thresholds.

## 6. Dating (H3)

| Model | Median date of the 168 chunks | Middle half |
| --- | --- | --- |
| Grammar (decides H3) | 1661 | 1600-1696 |
| Lexical | 1736 | 1705-1775 |
| Transformer cross-check (not moved by King James imitation in validation) | 1755 | 1699-1765 |

The grammar model is known to date King James imitation about 53 years early; the transformer was
not moved by imitation in validation (+0.8 years), and it still dates the text earlier than the
1780-1830 pseudo-biblical controls (1805). The registered H3 decision is the grammar model's and is
computed in BOM-29's report; this table is the first read only.

## 7. Narrators, scribe and dictation order (6.3; `data/benchmark/scribes.json`)

| Grouping of the chunks | Accuracy telling the groups apart | By chance | p |
| --- | --- | --- | --- |
| Narrator (Nephi, Jacob, Mormon, Moroni; 121 chunks) | 0.744 | 0.277 | 0.001 |
| Dictation order (first or last dictated; 124 chunks) | 0.758 | 0.502 | 0.001 |
| Scribe | not testable: every scribed chunk is Cowdery's (11) | | |

The narrators differ in style well above chance, but below the 0.96 the same method reaches on
real authors in the benchmark, so the registered verdict is **not separable as different
authors**; and the order of dictation separates the chunks about as well, so the differences may
follow when a passage was dictated as much as who narrates it.

## Plain summary

The checks on known text all passed: every method found real authors among the decoys and none
called a stranger's text a match. On the Book of Mormon, no method makes a confident match to any
candidate, the whole-library sweep finds no lead, and the registered synthesis leans to "none of
these candidates" (0.74), on classical evidence only, because the model-based methods were
disqualified by their weakness on imitation. Where methods rank someone closest, it is mostly Joseph
Smith or Oliver Cowdery, through samples too small to trust and written in the same circle and
register as the text itself. The language-based dating places the text's language well before
1780-1830, by every model, including the one that imitation did not fool in validation.

The narrator voices differ above chance but not as much as different real authors do, and the
order of dictation explains the differences about as well as the narrator.

Still to come: BOM-29's formal H3 report, the claims table's reading (`data/claims/claims.json`),
and the paper's discussion, which must weigh each of these caveats.
