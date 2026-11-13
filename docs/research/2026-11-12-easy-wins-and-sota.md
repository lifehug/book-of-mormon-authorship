# Easy wins, the "none of these" problem, and methods we have not used

Research note, 2026-11-12. Written by an AI model (Claude) at the owner's request. It is a
sanity check, not a result. Nothing here changes the registered tests. The project takes no
position on the book's origin, and neither does this note.

**How to read the labels.** Every claim below carries one of three tags:

- **[repo]** I checked it today in this repository's saved files.
- **[lit]** It comes from the published literature. The reference list at the end says which
  sources were opened and read, which were only confirmed in search results, and which are
  from memory.
- **[judgment]** My opinion. Treat it as an argument, not a fact.

**One disclosure first.** To answer "is there a better algorithm for none of these?" I ran
three small calculations on already-saved benchmark scores (no Book of Mormon text, no GPU, no
corpus text). They are an exploratory look, made before any rule was written down. If any of
them is adopted, its amendment has to say "post hoc, after an exploratory look on 2026-11-12".
The two scripts are reproduced at the end so the numbers can be rerun.

---

## 1. The short version

1. **The outline is enough for what the paper claims.** The claims are modest and the evidence
   under them is unusually well controlled. No method I found would turn "cannot say none of
   these" into "can". [judgment]
2. **Three things I found in the saved numbers should be fixed before the paper is written.**
   They are free, and a careful reader would find them:
   - The 430 tests come from **23 authors**. Counted by author, the head-to-head against the
     older methods still goes the same way, but the evidence is far weaker than "p < 0.0001".
   - The 168 Book of Mormon chunks are **the same text cut twice** (121 chunks of 2,000 words
     and 47 of 5,000). "159 of 168" counts every passage twice.
   - The "none of these" bar asks that 95% of true authors pass the threshold. Only 92-93% of
     true authors are even ranked first. So the bar measures the worst few tests, and almost
     no method could pass it. That is worth saying in the paper.
3. **The best cheap addition is a standard one: score normalisation.** It is how speaker
   recognition and forensic text comparison turn a ranker into a verifier. On our saved scores
   it raises the share of true authors confirmed at about 2% false matches from about one in
   five to about three in four (exploratory; split by test, not yet by author). It does not
   pass the registered bar.
4. **The best small new run (about $5-10) is a benchmark at the real dose and in the real
   register**: biblical-style writers, 3,039 tokens each. Today the scorecard is measured at
   9,000 to 430,000 tokens on ordinary prose, and the headline result is at 3,039 tokens on
   scripture-style text.
5. **Not worth doing:** a bigger model (Stage 1), modern LLM judges, function-word networks,
   translation detectors, dictation measures.

---

## 2. Three things found in the saved numbers

### 2.1 The 430 tests are 23 authors [repo]

`data/benchmark/alm_*_p2.json` holds 430 tests, but they are up to 20 windows each from 23
test authors (Federalist 2, pseudo-biblical 4, dictated 1, and 16 new). Windows from one
author are not independent. Amendment 52's McNemar test and the Wilson intervals treat them as
if they were.

Counted by author (from `alm_*_p2.json` and `prior_work_classic_tails_p2.json`):

| Comparison | Authors where ours is ahead | Theirs ahead | Tied | Sign test p | Accuracy gap, 95% range resampling authors |
| --- | --- | --- | --- | --- | --- |
| 125M vs Burrows | 11 | 3 | 9 | 0.057 | +0.10 (0.01 to 0.22) |
| 297M vs Burrows | 11 | 2 | 10 | 0.022 | +0.12 (0.03 to 0.24) |
| 590M vs Burrows | 10 | 2 | 11 | 0.039 | +0.12 (0.03 to 0.24) |
| 125M vs ENSC | 14 | 2 | 7 | 0.004 | +0.16 (0.06 to 0.27) |
| 297M vs ENSC | 14 | 1 | 8 | 0.001 | +0.17 (0.09 to 0.29) |
| 590M vs ENSC | 14 | 1 | 8 | 0.001 | +0.17 (0.09 to 0.28) |

One author, Samuel Spring, supplies 19 of the 297M's 59 wins over Burrows. Malthus and Mant
supply 17 more.

What this means: the direction holds at every size and the gap's range stays above zero. But
"all twelve at p < 0.0001" overstates it. Against Burrows the by-author p-values (0.02 to
0.06) would not all survive the Holm correction Amendment 52 uses. The honest sentence is
closer to: "ours is ahead on about half the authors, behind on two or three, tied on the
rest". I did not compute Cosine Delta or General Imposters by author; they should be.

This is standard practice [lit]: chunks from one work or author are resampled together, or
modelled with an author-level random effect (Dror et al. 2018; Benavoli et al. 2017).

### 2.2 The 168 chunks are the book twice [repo]

Amendment 32 sealed "121 chunks of 2,000 words, 47 of 5,000". Both sets cover the whole
text (Mormon is 84 chunks at 2,000 and 33 at 5,000). So every passage is scored twice.
The ranks are fine. The count is not a count of 168 separate passages.

The revelation model ranked first (`data/blind/a43/unblinded.json`, candidates only):

| Size | 2,000-word chunks | 5,000-word chunks |
| --- | --- | --- |
| 125M | 113 of 121 | 46 of 47 |
| 297M | 121 of 121 | 47 of 47 |
| 590M | 90 of 121 | 41 of 47 |

At 590M it also varies by narrator on the 2,000-word chunks: Mormon 71 of 84, Nephi 11 of 21,
Moroni 5 of 12, Jacob 3 of 4. That is a lean, not a finding. It is worth one descriptive
table in section 8, with no test, because neighbouring chunks are not independent either.

### 2.3 Why almost nothing could pass the "none of these" bar [repo]

Amendment 25 sets the match threshold where 95% of true authors pass, then counts strangers
above it. Two features of that rule matter:

- **It is decided by the weakest tests.** The threshold is the 5th percentile of true-author
  scores: about 11 tests per fold. Those are mostly the tests where the model does not even
  rank the true author first (7-8% of tests). A threshold low enough to admit them admits
  most strangers.
- **One raw threshold covers seven tasks.** The loss drop is not on a common scale across
  genres or models. The blog already notes this (sermons 39% false matches, history 71% at
  590M).

The usual way to report a verifier is the other way round [lit]: fix the false-match rate,
then report how many true authors are confirmed (plus the whole curve: AUC, equal-error rate).
`data/blind/thresholds.json` already holds a ladder of this kind. Read that way, the same
saved scores say (pooled, 430 tests):

| Size | AUC | Equal-error rate | True authors above threshold at 5% false matches | at 1% |
| --- | --- | --- | --- | --- |
| 125M | 0.89 | 17% | 64% | 20% |
| 297M | 0.89 | 16% | 59% | 24% |
| 590M | 0.89 | 17% | 41% | 19% |

So the models are a middling verifier, not a broken one. "63-75% false matches" and "confirms
about half of true authors at 5% false matches" are the same scores read at two operating
points. The paper should give both, and say the registered bar was the first.

---

## 3. Easy wins, ranked

All are Mac-only unless a cost is given. "Rule first" is what the dated amendment would need
to say before the numbers are produced.

| # | What | Answers | Paper section | Uses (already on disk) | Cost | Rule first |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Count by author, not by window** | Does the head-to-head survive when 430 tests are treated as 23 authors? | 5.1, 9 | `data/benchmark/alm_*_p2.json`, `prior_work_classic_tails_p2.json` | 1 hour | "Better" at a size needs the author-resampled 95% range of the accuracy gap to exclude zero; sign test by author reported beside; all 12 comparisons. Post hoc (see 2.1). |
| 2 | **Report chunk sizes separately** | Is "159 of 168" double-counted? | 6.1-6.3 | `data/blind/a43/unblinded.json`, `a44/people.json`, `a45/`, `part2/placebo_slices_*.json` | 1 hour | Every chunk count given as "x of 121" and "y of 47"; no pooled count. Reporting only. |
| 3 | **Score normalisation and the full verification curve** (section 4) | Is there a better "none of these" algorithm on scores we already have? | 5.4, 5.5 | `alm_*_p2.json` (`scores` per test), `part2/benchmark.json` (General Imposters) | half a day | Z-norm per model from a calibration half split **by author**; statistic and target rates fixed; registered bar reported unchanged beside. Post hoc. |
| 4 | **Dose- and register-matched benchmark** (section 3.1) | At 3,039 tokens, inside biblical style, how often is the right writer picked, and how often is a stranger matched? | 5.3, 6.2, 6.3 | Placebo and pseudo-biblical texts already used for A49/A51 (`data/benchmark/part2/placebo.json`), base models | about $5-10, 1-2 GPU hours | Writers, slices, train/test split and the reading written before any run. Not post hoc. |
| 5 | **A wider register reference group** (section 3.2) | Among many scripture-style writers who could not be the author, where do the revelations rank? | 6.3, 6.7 | 18 curated imitation-scripture works, the known-answer set of translations and presented-as-ancient texts, TCP early-modern texts | about $5-10 | Selection rule for writers; percentile of the revelation model with its range, per size. |
| 6 | **Calibrated likelihood ratios** | "A score like this is N times more likely from the same author than from a stranger", with a quality figure (Cllr) | 5.4 | Same as #3 | with #3 | Logistic calibration on one half of authors, Cllr on the other. |
| 7 | **Equivalence wording for ties** | "Sizes tie": is that shown, or just not disproved? | 5.5 | `alm_*_p2.json` | minutes | State the margin that counts as "the same" before testing (TOST). |
| 8 | **Register-word masking for the classical methods** | Does Burrows' ranking of the candidates survive when the biblical markers are masked? | 6.1, 7 | Candidate samples, sealed set, `classic/` | 1-2 hours | Marker list fixed first; checked on the pseudo-biblical task before the sealed set. |
| 9 | **Prompting instead of fine-tuning** (section 6) | Does a second route, with no training step, give the same ranking? | 6.1, 6.5 | Published base and candidate inputs | Mac, 1-2 days | Validated on the 430 tests first; same reading as Amendment 43. |

Notes on the smaller items:

- **#7.** On the 430 tests the sizes disagree like this [repo]: 125M vs 297M, 2 to 9 (exact
  p 0.065); 125M vs 590M, 4 to 11 (p 0.12); 297M vs 590M, 2 to 2. So "297M and 590M tie" is
  well supported. "125M ties" is a lean the other way that was not settled. By author it
  would be weaker still. The outline's wording "sizes tie" is fair if it says "no difference
  shown" for the 125M.
- **#8.** Burrows' Delta counts the commonest words. In scripture style the commonest words
  *are* the register (unto, yea, behold, thou, the -eth endings). Masking a fixed list of
  them and rerunning is cheap. It is standard in spirit [lit]: text distortion (Stamatatos
  2017) and POSNoise (Halvani and Graner 2021) mask topic words the same way. The caution
  from the literature review is that those tools remove topic, not register, so the marker
  list has to be ours and written down first.

### 3.1 The dose- and register-matched benchmark (the most useful new run) [judgment]

**What I was looking for:** a known-answer test that looks like the real question. **What I
found:** the scorecard in section 5 is measured on ordinary prose with 9,000 to 430,000
training tokens per author [repo: `training` block of `alm_mid_p2.json`]. The result the paper
leads with is a 3,039-token sample in scripture style. The imitation test has three authors and
cannot grow. Nothing on disk measures accuracy at that dose in that register.

**The run:** take the scripture-style writers already used as placebos and controls (Ilive,
Southcott, Brothers, Snowden, Stiles, Reader, Dowling, Hunt, and the other curated
pseudo-biblical authors with enough text). For each, fine-tune on one 3,039-token slice and
test on held-out slices of the same writer, against everyone else's models. Report: right
writer picked (closed set), and the verification curve of section 4.

**What it answers:** when everything is in biblical style and every sample is tiny, do the
models still tell writers apart, or only tell biblical from not? Either answer helps the
paper. A high score says the revelation result is not only register. A low score says the
method has no known-answer support at the size and style that matter, and section 6 should
say so.

**Its limit, stated now:** most of these writers have one work, so this tests "same book",
not "same person" (the cross-work result in BOM-76 shows those differ). Snowden and Reader
have two works and can be tested across them.

**Cost:** each model is a few seconds of training; Amendment 51's 80 slice models at three
sizes cost about $4. Scoring is the larger part. About $5-10.

### 3.2 A wider reference group for the register placebo [judgment]

Amendment 51 compared the revelations with six writers. Two findings rest on one of them
(Ilive at 590M). A reference group of 40 to 60 writers in archaic religious register, each at
3,039 tokens, would turn "one forger out-ranks them at one size" into "the revelations sit at
the Nth percentile of scripture-style writers who could not be the author", with a range, at
each size. Sources already held [repo: `docs/holdings.md`]: the curated imitation-scripture
list, the 27-text known-answer set (translations and texts presented as ancient), and the
61,315 hand-keyed early-modern texts (17th-century prophetic and devotional writing). Period
King James text itself (masked from the test chunks but not from the world) is a natural
member and would be the plainest register check of all.

This is also what a likelihood ratio needs in its denominator (section 4): a population of
"other writers in this register", not six.

It would describe; it cannot separate the paper's two readings (same man, or same medium).

---

## 4. "None of these": the state of the art, and what it can do for us

### 4.1 What the field does [lit]

| Family | Idea | Runs on our saved scores? | Likely to help? |
| --- | --- | --- | --- |
| **Score normalisation** (Z-norm, T-norm, S-norm; Auckenthaler et al. 2000; Matějka et al. 2017; speaker verification) | Put each model's score on a common scale using its scores on texts by other people (Z-norm), or the test text's scores under other models (T-norm). | **Z-norm yes**: each model is scored on 60+ tests by other authors in its task. **T-norm only weakly** on the benchmark (3-4 models per task, and the other fine-tunes were not kept); **yes on the Book of Mormon chunks**, where dozens of same-dose models are saved. | **Yes, clearly** (4.2). |
| **Reference-population likelihood ratio** (Ishihara 2014-2021; Nini et al. 2024, LambdaG; Brümmer and du Preez 2006; Morrison 2013) | Score = how much better the candidate's model fits than models of a reference population. Calibrate to a likelihood ratio; judge with Cllr. | Yes for calibration. Our "loss minus base model" is already a ratio against one reference model; the population version needs the reference group of 3.2. | Yes for honest reporting. Modest for accuracy. |
| **Impostors** (Koppel and Winter 2014; Kestemont et al. 2016) | Ask how often the candidate beats random impostor authors over random feature subsets. | Already run (General Imposters): 79% false matches on 430 tests. | No. Already the weakest here. |
| **Unknown-author class** (ENSC, Schaalje et al. 2011) | Add a latent "someone else" to a centroid classifier. | Already run: 76% false matches. | No. |
| **Extreme-value thresholds** (Scheirer et al. 2013; Bendale and Boult 2016, OpenMax) | Model the tail of each class's score distribution; reject what falls beyond it. | Technically yes. | No. It needs many training examples per class to fit a tail. We have 20 windows per author and one sample for the candidate that matters. |
| **Conformal prediction** (Bates et al. 2023; Angelopoulos and Bates) | Turn any score into a p-value for "this text is like the calibration texts", with a guaranteed false-alarm rate. | Yes. | Partly. It fixes the small overshoot in 4.2 (the guarantee holds on average at any calibration size; to be within one point of the target on a given calibration set takes about 2,500 calibration cases, within five points about 100). It gives **no** guarantee about power, and the guarantee assumes the test text is like the calibration texts. The Book of Mormon is not like the benchmark (register), so the guarantee does not carry over. |
| **Language-model perplexity verification** (Bagnall 2015; Barlas and Stamatatos 2020; Huang, Murakami and Grieve 2024; Miralles-González et al. 2025) | Our method. Huang et al. is closed-set only, with no threshold. The other three all found raw scores are not comparable across texts and added a normalisation step. | n/a | Their lesson is the first row. |
| **Style embeddings** (LUAR and successors) | Contrastive encoders; verify by cosine distance. | Already run (period-trained encoders). | No new gain expected. |
| **Modern LLM as judge** | Ask a large model whether two texts share an author. | No. | No. Any modern model has read the Book of Mormon and the Doctrine and Covenants. It breaks the time lock the whole study rests on. |

**What published systems achieve [lit].** AUC is the chance that a true author outscores a
stranger (1.0 perfect, 0.5 a coin toss).

| Setting | Best published result |
| --- | --- |
| Same genre, huge training sets (PAN 2020-21, fan fiction) | AUC 0.97-0.99 |
| Same genre, 150-2,300 tokens of known text (LambdaG, 12 corpora) | AUC 0.78-0.99 |
| Across topics or genres, a few thousand words (PAN 2014-15 winners) | AUC about 0.80 |
| Across registers: essay, email, text message, interview (PAN 2022-23) | AUC 0.60-0.62; a simple character-count baseline beat every 2022 entry |
| Ours, ordinary prose, raw score (section 2.3) | AUC 0.89 |

How good would a method need to be to pass our bar? Under a textbook assumption (both score
distributions bell-shaped with equal spread; my arithmetic, not from a paper), 5% false
matches at 95% true matches needs AUC of about 0.99. AUC 0.95 gives about 25% false matches
there, and AUC 0.90 about 45%. Our rule is stricter again, because a false match is *any* of
the remaining candidates clearing the threshold.

The literature survey found **no published method that reports 5% false matches at 90-95%
true matches** with a few thousand words of known text under a change of genre or register.
Where low false-match rates are reported, they are bought by declining to answer many cases
(generalised unmasking reaches perfect precision by answering 14% of cases). The PAN 2022
organisers wrote that the earlier high scores "may have given the false impression that
authorship verification is an almost solved problem". So the registered bar is beyond the
published state of the art for these conditions, and our figures are in line with what
others get. That is a fair sentence for the paper.

**Which fixes the literature points to.** Three, and they are the same three everywhere:

1. *Centre each text against other models* (T-norm; Bagnall 2015 did this to win PAN 2015).
   It removes "this passage is easy for every fine-tune".
2. *Centre each model against texts in the questioned text's own register* (Z-norm; Barlas
   and Stamatatos 2020 say the normalisation texts must come from the questioned document's
   domain). It removes "this model lowers loss on everything".
3. *Compare against a reference population trained on the same amount of text as the
   candidate* (LambdaG uses 100 size-matched reference models and reports that one is "not
   enough"). Our score, loss minus the base model's, is this idea with a single reference
   that is not size-matched. **Amendments 45 and 51 (equal-dose rivals and placebo slices)
   already are a size-matched reference population**, built for another reason. Section 3.2
   widens it.

Then calibrate to a likelihood ratio and allow "no answer" in a middle band.

### 4.2 What normalisation does on our saved scores [repo, exploratory]

Method: for each candidate model, take the mean and spread of its score on tests by *other*
authors in its task (Z-norm). Convert every score to "standard deviations above what this
model gives a stranger". Call a match when the top candidate's normalised score (or its lead
over the runner-up, "z-margin") clears a threshold. A true author counts only if ranked first
*and* above the threshold (the "raw" rows keep the registered definition, which does not
require first rank, so they are slightly flattered). Normalisation statistics and threshold
come from one random half of the tests; rates are measured on the other half; 50 repeats.

| Size | Statistic | Held-out false matches (target 5%) | True authors confirmed | Held-out false matches (target 1%) | True authors confirmed |
| --- | --- | --- | --- | --- | --- |
| 125M | raw (as now) | 5.5% | 63% | 1.3% | 22% |
| 125M | z-margin | 7.3% | 79% | 2.4% | 73% |
| 297M | raw | 5.4% | 58% | 1.4% | 25% |
| 297M | z-margin | 7.2% | 81% | 2.4% | 78% |
| 590M | raw | 5.3% | 48% | 1.4% | 19% |
| 590M | z-margin | 6.7% | 80% | 2.1% | 77% |

Reading: at about 2% false matches, normalisation confirms about three in four true authors
where the raw score confirms one in five. When the threshold is learned on six tasks and
applied to the seventh (z-margin), false matches stay at or under 5% on six of seven tasks
and reach 17-33% on fiction; true authors confirmed range from 55% (law and politics) to
100% (the dictated task). So the scale mostly carries across genres, not perfectly. (In that
check the normalisation statistics used all tests, so it is a little optimistic.)

**Caveats, all of which the amendment would need to fix:**

- The halves were split by test, not by author. The real version must split by author
  (section 2.1), and the numbers will get worse and wider.
- The held-out false-match rate lands above its target (7% for 5%). A conformal threshold
  corrects this.
- It still does not pass the registered bar. At 95% of true authors confirmed, false matches
  remain 40-100% under every statistic I tried. No statistic can confirm 95% when 93% are
  ranked first.
- I looked at six statistics. The table shows the best two families. That is a forking path,
  and why this is exploratory.

### 4.3 Can it be carried to the Book of Mormon? [judgment]

Only partly, and this is the candid part.

- **The mechanics carry over.** Every candidate model already has scores on the sealed
  decoys (strangers' text) and every sealed chunk already has scores under dozens of
  same-dose models (Amendments 45 and 51). Both normalisations can be computed from saved
  files (`data/blind/a43/`, `a45/`, `part2/`).
- **The guarantee does not.** A threshold learned on ordinary prose at 9,000+ tokens says
  little about a 3,039-token sample in another register. The benchmark of 3.1 is what would
  make a threshold meaningful there.
- **Recognition across works fails for most candidates** (BOM-76: only Ethan Smith). A
  verifier with a 2% false-match rate is still silent about a candidate whose own other book
  it does not recognise. Normalisation does not touch that.
- **So "none of these" stays out of reach.** With one 3,039-token sample, in a different
  register from the candidates' other writing, no algorithm can supply what the data does
  not hold. Better algorithms improve the benchmark figure and the honesty of the reporting.
  They do not let the paper exclude anyone.

What it *would* let the paper say, if the by-author version holds: "at a 2-5% false-match
rate our models confirm most true authors on ordinary prose; the Book of Mormon case lies
outside the conditions where that was measured." That is a fairer section 5.4 than "no method
passes" alone. General Imposters and ENSC should be put through the same curve before any
comparison with them is written; I did not do that.

---

## 5. Other methods we have not used

| Method | What it is | Text it needs | Relevant here? |
| --- | --- | --- | --- |
| **Unmasking** (Koppel, Schler and Bonchek-Dokow 2007; Bevendorff et al. 2019) | Remove the most telling features step by step. Same author: the difference collapses fast. Built for one author writing in two genres. | About 5,000+ words per side; the short-text version about 4,000. | **Partly.** The right idea for the register problem. Usable for Ethan Smith, Pratt, Rigdon, Cowdery, Phelps, Spalding, Hunt. Not for the 3,039-token revelations. Its judge must be trained on known cross-register pairs and we have three such authors, so expect "undecided" often. A day of Mac work; a side table at most. |
| **Topic masking** (Stamatatos 2017; POSNoise, Halvani and Graner 2021) | Replace content words with placeholders before any method runs. | Same as the method it feeds. | **Yes, cheap, as a control** (easy win #8). It removes topic, not register, so a register-word list is the version that matters here. |
| **LambdaG** (Nini et al. 2024) | A likelihood ratio between a small grammar model of the candidate and models of a reference population, on masked text. The closest published relative of our method. Reported AUC 0.78-0.99 on 12 corpora, ahead of Impostors on all twelve. | Small: tested with 139-2,306 tokens of known text. Register mismatch between known and questioned text was not tested. | **Yes, the best outside method to add** if one is added: independent, cheap (n-gram models on the Mac), built for small samples, outputs a likelihood ratio. Reference population should be scripture-style text (3.2). 1-2 days. |
| **Function-word adjacency networks** (Segarra, Eisen and Ribeiro 2015) | Networks of which common words follow which. | Profiles of 50,000+ words for good accuracy on 5,000-word texts. | **No.** Too much text needed, and the authors report it is genre-sensitive. |
| **Bayesian stylometry** (Mosteller and Wallace 1964; Airoldi et al. 2006; Ishihara's forensic work) | Count models with proper uncertainty; output a likelihood ratio. | Works at 500-2,500 tokens, with wide uncertainty. | **As a reporting frame, yes** (easy win #6). As new evidence, no: at 3,000 tokens it will mostly say "uninformative", which we know. |
| **Candidate-free decomposition** (Koppel et al. 2011; Akiva and Koppel 2013; rolling stylometry, Eder 2016) | Split a long text into stylistic components without any candidates. Shown on merged biblical books. | A long questioned text. We have one. | **Somewhat.** It avoids the tiny-sample problem entirely. But section 8 already tests narrators (0.744 against chance 0.277) and dictation order. It would add a second view of the same question, not a new one. Only worth it with a false-split baseline on single-author period books. |
| **Cross-genre attribution research** (Tyo et al. 2022; Altakrori et al. 2021; Barlas and Stamatatos 2020; PAN 2022-23) | Studies of how badly a change of genre hurts. | n/a | **As citations.** They say the confound is severe and unsolved, and that the fixes are masking, a register-matched reference group, and validation under the conditions of the case. That supports sections 5.3 and 12. One finding to cite: simple word and character counts beat neural models when text per author is small (Tyo et al.), which fits Burrows doing well on the imitation test. |
| **Imitation and pastiche detection** (Brennan, Afroz and Greenstadt 2012; Afroz et al. 2012; Somers and Tweedie 2003) | Whether deliberate imitation defeats stylometry, and whether it can be spotted. | Tested on short modern samples. | **As a citation for limitations.** Sustained imitation drives attribution toward chance. So "does not match a candidate's ordinary prose" is weak evidence in either direction. No tool to import. |
| **Translation detection** | Classifiers that tell translated from original prose. | Thousands of labelled period texts; we have them. | **No.** King James English is itself translated English. A text imitating it inherits the same marks. Our four known-answer checks already failed to separate translations from texts presented as ancient. A fifth would be uninterpretable in the same way. |
| **Dictation and orality measures** | Whether dictating changes style. | n/a | **No.** The literature (Hoover on Henry James and Scott) finds style barely changes with dictation. |
| **Modern style embeddings; outside time-locked models** | LUAR, LISA; MacBERTh and others. | n/a | **No.** Ours are period-trained and better matched. No published use of period-locked models for authorship turned up, so the study is ahead of this literature, not behind it. |

**Prior work on this text.** The literature search found no published neural or
language-model authorship study of the Book of Mormon. The peer-reviewed core is still Jockers,
Witten and Criddle (2008), Schaalje et al. (2011) and Jockers (2013). Absence in a search is
not proof; a Google Scholar check before submission is worth ten minutes. Carmack (2018) and
Davis (2025) on Early Modern English syntax bear on section 8 and should be cited there.

---

## 6. Bigger ideas (Part 2)

| Idea | What it is | Cost | Would it move anything? [judgment] |
| --- | --- | --- | --- |
| **Reference-population framing** | Stop asking "which candidate is first?" and ask "how unusual is this candidate's fit, among everyone who wrote in this register?". Sections 3.2 and 4 together. | $10-20 | **Yes, the framing of section 6.** It is the forensic standard and it makes the register question measurable instead of argued. It cannot settle the two readings. |
| **Prompting instead of fine-tuning** (compare Miralles-González et al. 2025) | Give the base model a candidate's text as context and measure how much better it predicts the test passage, against the same passage with no context. No training, no learning rate, no one-batch fragility. | Mac only; 1,024-token context limits it to about a third of the revelation sample per pass, so several passes | **Maybe.** It is a second instrument with different weak points. If it agrees with fine-tuning, section 6.5 (seeds; "one-batch models cannot vary") gets much stronger. If it disagrees, that is worth knowing before publication. Validate on the 430 tests first. |
| **Borrowing search over the early-modern texts already held** | The 61,315 TCP texts (1473-1700) are on disk and used for dating. Running the copied-wording and rare-phrase searches over them is a piece of Stage 3 at no cost. | Mac only, days | **For section 3, modestly.** It narrows "a source could be older" without the $1,500+ model. The copied-wording search looked at the 70 years before the book (1759-1829; `docs/reuse-plan.md`) [repo]; older held texts were outside that window. The plan's own caution applies: old spelling ("vnto") breaks matches, so a null there is weaker. |
| **Stage 1: a 1.3B model** | As planned. | ~$700 | **No.** From 297M to 590M, picking the author did not change (2 to 2 disagreements) and false matches fell 0.04. The limit is sample size and register, not model size. Normalisation gains more for free. |
| **Stages 2-3: more text, all pre-1830 English** | As planned. | $2,500-3,500 | **Not for authorship.** Possibly for borrowing and dating. Decide after the paper. |
| **More Joseph Smith text before 1830** | None exists beyond what is used. Amendment 54 (later revelations) is the only extension and is running. | - | Already in hand. |
| **Rewriting benchmark authors into biblical style by machine** | Make synthetic cross-register tests. | cheap | **No.** The rewriting model's own style would contaminate the test, and a modern model breaks the time lock. |

---

## 7. The verdict

**Is the outline enough?** Yes, for what it claims. The opening statement ("if the author is
among the candidates, the closest writing is Joseph Smith's revelations; whether the author
is among them, these tools cannot settle") is the right size for the evidence. Nothing in the
literature offers a method that would let the paper claim more. The limits (tiny sample,
register, recognition across works) are limits of the surviving evidence, not of the tools.

**Before writing, fix three things** (free, all in section 2):

1. Count the head-to-head by author as well as by window. Soften "p < 0.0001".
2. Report the 2,000-word and 5,000-word chunks separately.
3. Explain why the "none of these" bar is nearly unpassable, and give the standard view
   beside it.

**The one to three additions most worth making:**

1. **Score normalisation with the verification curve and calibrated likelihood ratios**
   (easy wins #3 and #6). Standard, free, and it changes section 5.4 from a flat failure to a
   measured, partly useful instrument.
2. **The dose- and register-matched benchmark** (#4, about $5-10). It is the only known-answer
   test that resembles the actual question.
3. **A wider register reference group** (#5, about $5-10), reported as a percentile. If only
   two are done, do the first two.

LambdaG is the best fourth: an independent, small-sample method from outside the project.

**Not worth doing:** Stage 1's larger model; any modern LLM as a judge; function-word
networks; translation or dictation detectors; extreme-value (OpenMax) thresholds; more seeds;
the register-shift sermon test already set aside (I agree with that decision: it tests a
shift between two ordinary registers, not into scripture style).

**What none of this changes.** No addition here can show that the author is or is not among
the candidates. The additions make the scorecard fairer and the Joseph Smith section better
anchored. They do not make it decisive.

---

## References

Verification: **[O]** opened and read (paper or abstract); **[S]** confirmed in search
results at the link given; **[M]** from memory, link not checked today.

**Verification and open-set methods**

- Angelopoulos, A., Bates, S. (2021/2023). A gentle introduction to conformal prediction. https://arxiv.org/abs/2107.07511 [O]
- Auckenthaler, R., Carey, M., Lloyd-Thomas, H. (2000). Score normalization for text-independent speaker verification systems. *Digital Signal Processing* 10:42-54. https://dblp.uni-trier.de/rec/journals/dsp/AuckenthalerCL00.html [S]
- Bagnall, D. (2015). Author identification using multi-headed recurrent neural networks. PAN at CLEF. https://arxiv.org/abs/1506.04891 [O]
- Barlas, G., Stamatatos, E. (2020). Cross-domain authorship attribution using pre-trained language models. AIAI. https://pmc.ncbi.nlm.nih.gov/articles/PMC7256385 [S]
- Barlow, Nini, Manino (2026). Normalisation-based likelihood ratio estimation for forensic authorship verification. https://arxiv.org/abs/2607.09501 [S, abstract only]
- Bates, S., Candès, E., Lei, L., Romano, Y., Sesia, M. (2023). Testing for outliers with conformal p-values. *Annals of Statistics* 51(1):149-178. https://arxiv.org/abs/2104.08279 [S]
- Bendale, A., Boult, T. (2016). Towards open set deep networks. CVPR. https://arxiv.org/abs/1511.06233 [S]
- Bevendorff, J., Stein, B., Hagen, M., Potthast, M. (2019). Generalizing unmasking for short texts. NAACL. https://aclanthology.org/N19-1068/ [O]
- Bevendorff, J., Hagen, M., Stein, B., Potthast, M. (2019). Bias analysis and mitigation in the evaluation of authorship verification. ACL. https://aclanthology.org/P19-1634/ [S]
- Brümmer, N., du Preez, J. (2006). Application-independent evaluation of speaker detection. *Computer Speech and Language* 20:230-275. https://dblp.org/rec/journals/csl/BrummerP06.html [S]
- Huang, W., Murakami, A., Grieve, J. (2024). ALMs: authorial language models for authorship attribution. https://arxiv.org/abs/2401.12005 [S]
- Huang, B., Chen, C., Shu, K. (2024). Can large language models identify authorship? Findings of EMNLP. https://arxiv.org/abs/2403.08213 [S]
- Ishihara, S. (2021). Score-based likelihood ratios for linguistic text evidence with a bag-of-words model. *Forensic Science International*, doi:10.1016/j.forsciint.2021.110980 [S]
- Ishihara, S., Kulkarni, Carne, Ehrhardt, Nini, A. (2024). Validation in forensic text comparison. *Languages* 9(2):47. https://doaj.org/article/001314fb2a6f451db8d5c6556cf8233a [S]
- Kestemont, M., Stover, J., Koppel, M., Karsdorp, F., Daelemans, W. (2016). Authenticating the writings of Julius Caesar. *Expert Systems with Applications* 63:86-96. https://www.clips.uantwerpen.be/~walter/papers/2016/kskkd16.pdf [O]
- Kestemont, M., et al. (2020, 2021). Overviews of the cross-domain authorship verification task at PAN. https://ceur-ws.org/Vol-2696/paper_264.pdf ; https://ceur-ws.org/Vol-2936/paper-147.pdf [S]
- Koppel, M., Winter, Y. (2014). Determining if two documents are written by the same author. *JASIST* 65(1):178-187. https://cris.iucc.ac.il/en/publications/determining-if-two-documents-are-written-by-the-same-author/ [S]
- Koppel, M., Schler, J., Argamon, S. (2011). Authorship attribution in the wild. *Language Resources and Evaluation* 45:83-94. https://cris.biu.ac.il/en/publications/authorship-attribution-in-the-wild-5/ [S]
- Matějka, P., et al. (2017). Analysis of score normalization in multilingual speaker recognition. Interspeech. https://www.isca-archive.org/interspeech_2017/matejka17_interspeech.html [S]
- Miralles-González, Huertas-Tato, Martín, Camacho (2025). LLM one-shot style transfer for authorship attribution and verification. https://arxiv.org/abs/2510.13302 [O]
- Morrison, G. (2013). Tutorial on logistic-regression calibration and fusion. *Australian Journal of Forensic Sciences* 45(2):173-197. https://arxiv.org/abs/2104.08846 [S]
- Nini, A., Halvani, O., Graner, L., Gherardi, V., Ishihara, S. (2024). Grammar as a behavioral biometric: using cognitively motivated grammar models for authorship verification (LambdaG). https://arxiv.org/abs/2403.08462 [O, version 1]
- Schaalje, G. B., Fields, P., Roper, M., Snow, G. (2011). Extended nearest shrunken centroid classification. *Literary and Linguistic Computing* 26(1):71-88. https://dblp.uni-trier.de/rec/journals/lalc/SchaaljeFRS11.html [S]
- Scheirer, W., et al. (2013). Toward open set recognition. *IEEE TPAMI* 35(7). https://dblp1.uni-trier.de/rec/journals/pami/ScheirerRSB13.html [S]
- Seidman, S. (2013). Authorship verification using the impostors method. PAN at CLEF. https://ceur-ws.org/Vol-1179/CLEF2013wn-PAN-Seidman2013.pdf [S]
- Stamatatos, E., et al. (2022, 2023). Overview of the authorship verification task at PAN 2022 / 2023. https://publications.aston.ac.uk/id/document/89399 ; https://ceur-ws.org/Vol-3497/paper-199.pdf [O]
- Tyo, J., Dhingra, B., Lipton, Z. (2022). On the state of the art in authorship attribution and authorship verification. https://arxiv.org/abs/2209.06869 [O]

**Other methods**

- Afroz, S., Brennan, M., Greenstadt, R. (2012). Detecting hoaxes, frauds, and deception in writing style online. IEEE S&P. https://www.ieee-security.org/TC/SP2012/papers/4681a461.pdf [S]
- Airoldi, E., Anderson, A., Fienberg, S., Skinner, K. (2006). Who wrote Ronald Reagan's radio addresses? *Bayesian Analysis* 1(2):289-319. https://projecteuclid.org/euclid.ba/1340371064 [S]
- Akiva, N., Koppel, M. (2013). A generic unsupervised method for decomposing multi-author documents. *JASIST* 64(11):2256-2264. https://dblp.org/rec/journals/jasis/AkivaK13 [S]
- Altakrori, M., Cheung, J., Fung, B. (2021). The topic confusion task. Findings of EMNLP. https://aclanthology.org/2021.findings-emnlp.359 [S]
- Brennan, M., Afroz, S., Greenstadt, R. (2012). Adversarial stylometry. *ACM TISSEC* 15(3). [S, bibliographic record only]
- Eder, M. (2016). Rolling stylometry. *Digital Scholarship in the Humanities* 31(3):457-469. https://computationalstylistics.github.io/projects/rolling-stylometry [S]
- Halvani, O., Graner, L. (2021). POSNoise: an effective countermeasure against topic biases in authorship analysis. https://arxiv.org/abs/2005.06605 [S]
- Hoover, D. (2021). *Modes of Composition and the Durability of Style in Literature*. Routledge. https://www.routledge.com/Modes-of-Composition-and-the-Durability-of-Style-in-Literature/Hoover/p/book/9780367366704 [S]
- Kestemont, M., Luyckx, K., Daelemans, W., Crombez, T. (2012). Cross-genre authorship verification using unmasking. *English Studies* 93(3):340-356. https://www.clips.uantwerpen.be/~walter/papers/2012/kldc12.pdf [S]
- Koppel, M., Schler, J., Bonchek-Dokow, E. (2007). Measuring differentiability: unmasking pseudonymous authors. *JMLR* 8:1261-1276. https://jmlr.org/papers/volume8/koppel07a/koppel07a.pdf [O]
- Koppel, M., Akiva, N., Dershowitz, I., Dershowitz, N. (2011). Unsupervised decomposition of a document into authorial components. ACL. https://aclanthology.org/P11-1136/ [S]
- Mosteller, F., Wallace, D. (1964). *Inference and Disputed Authorship: The Federalist*. [M]
- Segarra, S., Eisen, M., Ribeiro, A. (2015). Authorship attribution through function word adjacency networks. *IEEE Transactions on Signal Processing* 63(20):5464-5478. https://arxiv.org/abs/1406.4469 [O]
- Somers, H., Tweedie, F. (2003). Authorship attribution and pastiche. *Computers and the Humanities* 37:407-429. https://link.springer.com/article/10.1023/A:1025786724466 [S]
- Stamatatos, E. (2017). Authorship attribution using text distortion. EACL. https://aclanthology.org/E17-1107/ [S]

**Earlier work on this text**

- Jockers, M., Witten, D., Criddle, C. (2008). Reassessing authorship of the Book of Mormon using delta and nearest shrunken centroid classification. *Literary and Linguistic Computing* 23(4):465-491. https://purl.stanford.edu/rs276tc2764 [S]
- Jockers, M. (2013). Testing authorship in the personal writings of Joseph Smith using NSC classification. *Literary and Linguistic Computing* 28(3):371-381. https://dh-abstracts.library.virginia.edu/works/1004 [S, abstract; page range from a secondary source]
- Carmack, S. (2018). Is the Book of Mormon a pseudo-archaic text? *Interpreter* 28:177-232. https://scholarsarchive.byu.edu/interpreter/vol28/iss1/14 [S]
- Davis, W. L. (2025). Joseph Smith's spiritual language: the presence of Early Modern English in the Book of Mormon. *Dialogue* 58(2). https://www.dialoguejournal.com/articles/joseph-smiths-spiritual-language-the-presence-of-early-modern-english-in-the-book-of-Mormon/ [S]

**Reporting practice**

- Benavoli, A., Corani, G., Demšar, J., Zaffalon, M. (2017). Time for a change: a tutorial for comparing multiple classifiers through Bayesian analysis. *JMLR* 18(77). https://www.jmlr.org/papers/v18/16-305.html [S]
- Dror, R., Baumer, G., Shlomov, S., Reichart, R. (2018). The hitchhiker's guide to testing statistical significance in natural language processing. ACL. https://aclanthology.org/P18-1128/ [S]
- Lakens, D. (2017). Equivalence tests: a practical primer. *Social Psychological and Personality Science* 8(4):355-362. https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906 [S]

The literature was gathered by two AI search agents and checked against my own knowledge.
Anything marked [S] or [M] should be opened before it is cited in the paper.

---

## Appendix: the exploratory scripts

Run from the repository root with `uv run --no-sync python <file>`. They read only
`data/benchmark/alm_*_p2.json` and `data/benchmark/prior_work_classic_tails_p2.json`.

<details><summary><code>peek_open_set.py</code></summary>

```python
"""Exploratory peek (2026-11-12): can score normalisation on SAVED benchmark scores
improve the open-set false-match rate? Reads only data/benchmark/alm_*_p2.json. No text."""
import json, sys, random
import numpy as np
R = "/Users/ea/Workspace/book-of-mormon-authorship/data/benchmark/"

def load(size):
    d = json.load(open(R + f"alm_{size}_p2.json"))
    tests = []
    for task, rs in d["records"].items():
        for r in rs:
            tests.append((task, r["author"], {k: -v for k, v in r["scores"].items()}))
    return d, tests

def znorm_stats(tests):
    # per (task, model): mean/sd of its score on tests by OTHER authors (impostor trials)
    acc = {}
    for task, a, s in tests:
        for m, v in s.items():
            if m != a:
                acc.setdefault((task, m), []).append(v)
    out = {k: (np.mean(v), np.std(v) + 1e-9) for k, v in acc.items()}
    for task in {t for t, _, _ in tests}:  # models with no impostor trial: pooled task stats
        allv = [x for (t, m), v in acc.items() if t == task for x in v]
        for _, _, s in [x for x in tests if x[0] == task]:
            for m in s:
                out.setdefault((task, m), (np.mean(allv), np.std(allv) + 1e-9))
    return out

def stat(kind, task, s, zs):
    """decision statistic for the top candidate among the models in s"""
    if kind == "raw":
        return max(s.values())
    z = {m: (v - zs[(task, m)][0]) / zs[(task, m)][1] for m, v in s.items()}
    if kind == "znorm":
        return max(z.values())
    srt = sorted(s.values(), reverse=True)
    if kind == "margin":
        return srt[0] - srt[1]
    if kind == "ratio":
        return srt[0] / (abs(srt[1]) + 1e-9)
    zsrt = sorted(z.values(), reverse=True)
    if kind == "zmargin":
        return zsrt[0] - zsrt[1]
    if kind == "tnorm":  # top minus mean of the rest, over sd of the rest (needs >=2 rest)
        rest = srt[1:]
        return (srt[0] - np.mean(rest)) / (np.std(rest) + 0.01)
    raise ValueError(kind)

def trials(tests, kind):
    zs = znorm_stats(tests)
    pos, neg, tasks = [], [], []
    for task, a, s in tests:
        top = max(s, key=s.get)
        p = stat(kind, task, s, zs) if (top == a or not STRICT) else -np.inf
        s2 = {m: v for m, v in s.items() if m != a}
        if len(s2) < 2 and kind not in ("raw", "znorm"):
            continue
        n = stat(kind, task, s2, zs)
        pos.append(p); neg.append(n); tasks.append(task)
    return np.array(pos), np.array(neg), tasks

def auc(pos, neg):
    pos = np.where(np.isinf(pos), -1e18, pos)
    return float(np.mean([(p > neg).mean() + 0.5 * (p == neg).mean() for p in pos]))

def fpr_at_tpr(pos, neg, tpr=0.95):
    p = np.where(np.isinf(pos), -1e18, pos)
    t = np.quantile(p, 1 - tpr)
    return float((neg >= t).mean())

def tpr_at_fpr(pos, neg, fpr=0.05):
    t = np.quantile(neg, 1 - fpr)
    return float((pos > t).mean())

def eer(pos, neg):
    p = np.where(np.isinf(pos), -1e18, pos)
    best = 1
    for t in np.unique(np.concatenate([p, neg])):
        fr, fa = (p < t).mean(), (neg >= t).mean()
        best = min(best, max(fr, fa))
    return float(best)

def pertask_fpr(pos, neg, tasks, tpr=0.95):
    out = []
    for t in sorted(set(tasks)):
        i = [k for k, x in enumerate(tasks) if x == t]
        out.append(fpr_at_tpr(pos[i], neg[i], tpr) * len(i))
    return sum(out) / len(tasks)

import sys
STRICT = len(sys.argv) > 1
print('STRICT positives (wrong top counts as miss):', STRICT)
for size in ("pilot", "base", "mid"):
    d, tests = load(size)
    print(f"== {size}: {len(tests)} tests; registered FPR {d['verdict']['open_set_fpr']:.3f}")
    print(f"{'stat':8} {'n':>4} {'AUC':>6} {'EER':>6} {'FPR@95':>7} {'FPR@90':>7} {'FPR@80':>7} {'TPR@5%FPR':>9} {'TPR@1%':>7} {'FPR@95 per-task thr':>20}")
    for kind in ("raw", "znorm", "margin", "ratio", "zmargin", "tnorm"):
        pos, neg, tasks = trials(tests, kind)
        print(f"{kind:8} {len(pos):4d} {auc(pos,neg):6.3f} {eer(pos,neg):6.3f} {fpr_at_tpr(pos,neg):7.3f} {fpr_at_tpr(pos,neg,.9):7.3f} {fpr_at_tpr(pos,neg,.8):7.3f} {tpr_at_fpr(pos,neg):9.3f} {tpr_at_fpr(pos,neg,.01):7.3f} {pertask_fpr(pos,neg,tasks):20.3f}")
    # candidates per task and dose correlation
    tr = d["training"]
    xs, ys = [], []
    for task, a, s in tests:
        xs.append(np.log(tr[task][a]["train_tokens"])); ys.append(s[a])
    print("  corr(log train tokens, positive score) =", round(float(np.corrcoef(xs, ys)[0, 1]), 3),
          "| candidates per task:", {t: len(v) for t, v in tr.items()})
```

</details>

<details><summary><code>peek2.py</code></summary>

```python
"""Exploratory peek 2 (2026-11-12). (a) cross-validated z-norm verifier; (b) leave-one-task-out;
(c) author-clustered view of Amendment 52's head-to-head. Saved scores only, no text."""
import json, random, sys
import numpy as np
from math import comb
sys.path.insert(0, "<this folder>")
R = "/Users/ea/Workspace/book-of-mormon-authorship/data/benchmark/"
def load(size):
    d = json.load(open(R + f"alm_{size}_p2.json"))
    return [(task, r["author"], {k: -v for k, v in r["scores"].items()}, r["predicted"]) for task, rs in d["records"].items() for r in rs]
def zstats(tests):
    acc = {}
    for task, a, s, _ in tests:
        for m, v in s.items():
            if m != a: acc.setdefault((task, m), []).append(v)
    out = {k: (np.mean(v), np.std(v) + 1e-9) for k, v in acc.items() if len(v) >= 5}
    pool = {}
    for (t, m), v in acc.items(): pool.setdefault(t, []).extend(v)
    return out, {t: (np.mean(v), np.std(v) + 1e-9) for t, v in pool.items()}
def zm(task, s, zs, kind):
    st, pool = zs
    z = sorted(((v - st.get((task, m), pool[task])[0]) / st.get((task, m), pool[task])[1] for m, v in s.items()), reverse=True)
    return z[0] if kind == "znorm" else z[0] - z[1]
def trial(tests, zs, kind):
    pos, neg = [], []
    for task, a, s, _ in tests:
        if kind == "raw":
            pos.append(s[a]); neg.append(max(v for m, v in s.items() if m != a)); continue
        top = max(s, key=s.get)
        # positive: statistic of the top candidate if it is the true author, else a miss
        pos.append(zm(task, s, zs, kind) if top == a else -1e9)
        neg.append(zm(task, {m: v for m, v in s.items() if m != a}, zs, kind))
    return np.array(pos), np.array(neg)
for size in ("pilot", "base", "mid"):
    tests = load(size)
    print("==", size)
    for kind in ("raw", "znorm", "zmargin"):
        res = {0.05: [], 0.01: []}
        for rep in range(50):
            idx = list(range(len(tests))); random.Random(rep).shuffle(idx); h = len(idx) // 2
            for cal, ev in ((idx[:h], idx[h:]), (idx[h:], idx[:h])):
                C = [tests[i] for i in cal]; E = [tests[i] for i in ev]
                zs = zstats(C)
                _, cn = trial(C, zs, kind); ep, en = trial(E, zs, kind)
                for f in res:
                    t = np.quantile(cn, 1 - f)
                    res[f].append(((en > t).mean(), (ep > t).mean()))
        out = "  ".join(f"target FPR {f}: held-out FPR {np.mean([x[0] for x in v]):.3f}, correct-match rate {np.mean([x[1] for x in v]):.3f}" for f, v in res.items())
        print(f"  2-fold x50 {kind:8} {out}")
    # leave one task out: z-stats are within the held-out task (they need only impostor texts), threshold from other tasks
    for kind in ("znorm", "zmargin"):
        zs = zstats(tests)
        rows = []
        for task in sorted({t[0] for t in tests}):
            C = [t for t in tests if t[0] != task]; E = [t for t in tests if t[0] == task]
            _, cn = trial(C, zs, kind); ep, en = trial(E, zs, kind)
            t = np.quantile(cn, 0.95)
            rows.append(f"{task.replace('p2_','')[:10]} FPR {(en > t).mean():.2f} TPR {(ep > t).mean():.2f}")
        print(f"  leave-task-out {kind:8} | " + " | ".join(rows))
# (c) clustered head-to-head
c = json.load(open(R + "prior_work_classic_tails_p2.json"))["records"]
for size in ("pilot", "base", "mid"):
    tests = load(size)
    flat = [r for task, rs in c.items() for r in rs]
    assert len(flat) == len(tests) and all(f["author"] == t[1] for f, t in zip(flat, tests))
    for meth in ("burrows_delta", "ensc"):
        per = {}
        for f, t in zip(flat, tests):
            a = per.setdefault((t[0], t[1]), [0, 0, 0])
            ours, theirs = t[3] == t[1], f[meth] == f["author"]
            a[0] += ours and not theirs; a[1] += theirs and not ours; a[2] += 1
        w = sum(1 for v in per.values() if v[0] > v[1]); l = sum(1 for v in per.values() if v[1] > v[0]); n = w + l
        p = min(1.0, 2 * sum(comb(n, k) for k in range(0, min(w, l) + 1)) / 2 ** n)
        # author-cluster bootstrap of the accuracy difference
        keys = list(per); rng = random.Random(1); diffs = []
        for _ in range(5000):
            ks = [keys[rng.randrange(len(keys))] for _ in keys]
            diffs.append(sum(per[k][0] - per[k][1] for k in ks) / sum(per[k][2] for k in ks))
        lo, hi = np.quantile(diffs, [0.025, 0.975])
        top = sorted(per.items(), key=lambda kv: -(kv[1][0] - kv[1][1]))[:3]
        print(f"{size} vs {meth}: authors {len(per)}; ours ahead on {w}, theirs on {l}, tied {len(per)-n}; sign test p={p:.4f}; "
              f"accuracy gap {sum(v[0]-v[1] for v in per.values())/len(tests):.3f} author-bootstrap 95% [{lo:.3f}, {hi:.3f}]; biggest: "
              + ", ".join(f"{k[1].split(',')[0]} {v[0]}-{v[1]}" for k, v in top))
```

</details>
