## 5. How good is each method? A scorecard on known answers

A method's answer about the Book of Mormon is worth what the method scores on texts whose authors
are known. This section gives that score for every method and every model size, side by side. The
methods are judged here only on known answers, never on the Book of Mormon.

**The methods.**

- *Our models:* one copy of a time-locked model trained further on each author's sample, scored by
  how much better it predicts a passage than the untouched model does (section 2.8), at 125M, 297M
  and 590M.
- *Burrows' Delta* and *Cosine Delta:* distances between texts in the frequencies of their most
  common words (Burrows 2002; the family used by Jockers et al. 2008).
- *General Imposters:* asks whether a text is closer to a candidate than to a crowd of other
  writers, over many random subsets of words (Koppel and Winter 2014).
- *ENSC:* the classifier of Schaalje et al. (2011), which may answer "none of the candidates".

The older methods are baselines. They are not combined with ours or with each other.

**Two questions, scored separately.** *Picking:* with the true author on the list, how often is he
ranked first? *"None of these":* with the true author taken off the list, how often does the method
still declare a match (a false match)? A method can be good at the first and poor at the second,
and the second is the one a claim of authorship needs. The benchmark, its three steps (110, 430 and
1,070 held-out tests) and the registered bar are described in section 2.7.

### 5.1 Picking the right author from a list

**Preparation.** Every method takes exactly the same held-out tests: 5,000-word passages from the
last quarter of each author's text, attributed among the roughly four authors of the passage's
task. For the 430 tests the older methods were first scored on their own draws of test passages;
to make paired comparison possible they were rerun on the very passages our models took (Amendment
52, post hoc). All figures below are on those shared tests.

**Right author, share of tests** (`data/benchmark/prior_work.json`, `alm_*_p2.json`,
`alm_*_p3.json`, `prior_work_classic_tails_p3.json`):

| Method | Part 1: 110 tests, 7 authors | BOM-75: 430 tests, 23 authors | The 32 new authors: 640 tests | All 55 authors: 1,070 tests |
| --- | --- | --- | --- | --- |
| Our models, 125M | 93.6% | 91.6% | 93.6% | 92.8% |
| Our models, 297M | 99.1% | 93.3% | 92.5% | 92.8% |
| Our models, 590M | 98.2% | 93.3% | 90.6% | 91.7% |
| Burrows' Delta | 95.5% | 81.6% | 76.3% | 78.4% |
| Cosine Delta | 81.8% | 80.0% | 78.4% | 79.1% |
| General Imposters | 74.5% | 63.0% | 77.2% | 71.5% |
| ENSC | 96.4% | 76.0% | 76.9% | 76.5% |

The 430 include Part 1's 110, and the 1,070 are the 430 and the 640 together. On their own draws of
passages from the same 23 authors, which may come from anywhere in an author's text, the older
methods score higher (Burrows 93.0%, Cosine 93.6%, General Imposters 79.8%, ENSC 92.8%;
`data/benchmark/part2/open_set.json`). The shared tests are harder because they are held apart from
everything a method learns from, and both sides took them.

**The unit is the author, not the passage.** Up to 20 passages come from each author, and passages
by one author tend to go right or wrong together, so 430 tests are not 430 independent trials. The
first comparison we ran (Amendment 52) counted passages, and every one of its twelve head-to-heads
came out in our models' favour with a corrected p below 0.0001. That overstated the certainty. A
simulated research check (an AI agent reading the whole project) raised the point, and we recounted
by author (Amendment 55, post hoc): an author counts for a side when that side wins more of the
passages on which the two methods disagree; the test is an exact sign test over authors who are not
tied, with Holm's correction for making twelve comparisons; beside it stands the gap in accuracy
with a 95% range from resampling authors. One author shows why this matters: the sermon writer
Samuel Spring alone supplies 19 of the 297M's 59 passage-level wins over Burrows' Delta.

**23 authors were not enough.** Counted by author on BOM-75's 23, our models were clearly better
than General Imposters and ENSC, and ahead of the two Delta methods without that being shown
(`data/benchmark/clustered.json`; cells are authors where ours is ahead - authors where the older
method is ahead, at 125M / 297M / 590M):

| Our models against | Authors ahead - behind | Holm p | Reading by the rule |
| --- | --- | --- | --- |
| Burrows' Delta | 11-3 / 11-2 / 10-2 | 0.15 / 0.13 / 0.15 | no difference shown |
| Cosine Delta | 11-3 / 11-2 / 10-2 | 0.15 / 0.13 / 0.15 | no difference shown |
| General Imposters | 16-1 / 16-0 / 15-0 | 0.003 / 0.0004 / 0.0007 | ours better |
| ENSC | 14-2 / 14-1 / 14-1 | 0.03 / 0.009 / 0.009 | ours better |

**32 more authors, with a stopping rule (Amendment 56, post hoc).** A lead of 11 authors to 2 that
is not significant needs more authors, not a different test. Before any further author was drawn,
the rule was written down: continue down the same seeded order in each genre, by the same
selection rules, until eight more authors per genre are kept; apply the same by-author test to all
55 authors; and add no authors after that, whatever the result. The stopping rule is what prevents
drawing until the answer comes out one way. The screen turned down 17 authors on the way
(translations, two people under one name, anthologies, a state government).

**All 55 authors** (`data/benchmark/clustered.json`):

| Our models against | Authors ahead - behind (tied), 125M | 297M | 590M | Holm p, 125M / 297M / 590M | Accuracy gap in points (95% range), 125M / 297M / 590M |
| --- | --- | --- | --- | --- | --- |
| Burrows' Delta | 25-4 (26) | 25-3 (27) | 24-4 (27) | 0.0004 / 0.0002 / 0.0005 | +14 (8-22) / +14 (8-21) / +13 (7-20) |
| Cosine Delta | 26-5 (24) | 26-4 (25) | 24-6 (25) | 0.0005 / 0.0003 / 0.0014 | +14 (7-22) / +14 (7-21) / +13 (6-20) |
| General Imposters | 33-3 (19) | 32-2 (21) | 30-4 (21) | 0.000002 / 0.000001 / 0.00006 | +21 (14-29) / +21 (14-29) / +20 (13-27) |
| ENSC | 30-4 (21) | 30-3 (22) | 29-4 (22) | 0.00006 / 0.00001 / 0.00008 | +16 (9-24) / +16 (9-24) / +15 (8-23) |

All twelve comparisons read "ours better". The largest corrected p is 0.0014, and every accuracy
range lies above zero.

**The 32 new authors alone repeat it.** Nobody had looked at these authors before the rule was
written, so they are an independent check. On them alone all twelve comparisons are again "ours
better" (Holm p from 0.009 to 0.038): against Burrows' Delta 14 authors to 1-2, Cosine Delta 14-15
to 2-4, General Imposters 15-17 to 2-4, ENSC 15-16 to 2-3. On their 640 tests our models are right
91-94% of the time and the older methods 76-78%.

**Passage counts, reported beside** (Amendment 52's unit, not the test). On the 430 tests the
passages only one side got right split, ours to theirs: against Burrows' Delta 58-15 / 59-9 / 59-9
at 125M / 297M / 590M; Cosine Delta 66-16 / 67-10 / 67-10; General Imposters 130-7 / 131-1 / 132-2;
ENSC 76-9 / 77-3 / 77-3. Most of the gap comes from the new genres: on 1820s sermons the 297M wins
28 passages to 0 against Burrows' Delta, on fiction 8 to 0, while on the Federalist papers and the
dictated task the two barely disagree.

**Part 1's 110 tests could not decide it.** There the methods disagreed too rarely. The 297M was
right on 4 tests that Burrows' Delta missed and wrong on none that Delta got (p 0.13); the 590M, 3
to 0; the 125M, 4 to 6. Against ENSC: 3-0, 2-0 and 3-6. This is where the earlier draft of this
paper said our models "tie with the best older methods". On more authors that reading does not
hold.

**Variants and other methods on Part 1.** Three registered variants of our method and the style
encoders (models that turn a passage into a vector meant to capture its style) were scored on Part
1 only (`data/benchmark/prior_work.json`, `open_set.json`):

| Method | Right author, 125M / 297M / 590M | False matches |
| --- | --- | --- |
| V1 (a ten times larger learning rate, as registered) | 93.6% / 93.6% / 62.7% | 45% / 47% / 82% |
| V2 (a classifier on top of the model), registered seed | 90.0% / 90.9% / 76.4% | 28% / 14% / 39% |
| V2, five further seeds, range (Amendment 42, post hoc) | 66-93% / 51-76% / 40-78% | 9-93% / 53-98% / 32-93% |
| V3 (the untouched model's internal states fed to the older methods), on 180 trials | 83.9% / 84.4% / 84.4% | 69% / 72% / 71% |
| Style encoders, 297M / 590M backbone, on 180 trials | 83.9% / 83.9% | 50% / 63% |

V1's registered setting damaged the 590M; at a rate chosen on held-out training text it is the main
method again (Amendment 41, post hoc). V2's registered figures were one lucky seed: the same
settings give false-match rates from 9% to 98% depending only on the random seed, so V2 carries no
weight anywhere in this paper. V3 and the style encoders were scored on a different draw of 180
trials and are compared within that set, not with the rows above.

**Summary of 5.1.** At picking the right author from a short list, period-trained language models
are better than every older method tested, at every size, counted by author on 55 authors, and
again on 32 authors nobody had examined beforehand.

### 5.2 Period training matters

**Preparation.** Is the gain from training on the period's English, or would any language model do?
The same procedure was run with GPT-2, a public model of similar size trained on modern internet
text, in place of our base models: same samples, same settings, same 110 tests
(`data/benchmark/alm_gpt2.json`, `alm_gpt2_medium.json`).

| Base model | Trained on | Right author | False matches |
| --- | --- | --- | --- |
| GPT-2, 124M | modern text | 90.0% | 92% |
| GPT-2, 355M | modern text | 94.5% | 86% |
| Ours, 125M | 1780-1830 only | 93.6% | 47% |
| Ours, 297M | 1780-1830 only | 99.1% | 38% |
| Ours, 590M | 1780-1830 only | 98.2% | 22% |

GPT-2 picks the right author nearly as often. The difference is in false matches: 86-92% for GPT-2
against 22-47% for the period models. A modern model fine-tuned on any early nineteenth-century
author learns, first of all, what early nineteenth-century English looks like, and then finds that
every period text fits. A model that already knows the period's English has only the author left
to learn. This comparison was run on Part 1's 110 tests only; as 5.4 shows, the period models'
own false-match rates are higher on the wider benchmark.

### 5.3 Writing in biblical style

The Book of Mormon is written in a biblical register, so the test that matters most is whether a
method still recognises a writer when he puts that register on.

**Preparation.** The imitation test takes authors who wrote both imitation scripture and ordinary
prose, trains each method on the ordinary prose only, and asks it to find the author of the
imitation scripture among 13 candidates (the authors themselves and 10 others). Three authors
qualify: Richard Snowden, Robert Dodsley and William Kenrick (`data/benchmark/imitation.json`).

**Result, by passage and by author.**

| Method | Passages right | Dodsley | Kenrick | Snowden | Authors with most passages right |
| --- | --- | --- | --- | --- | --- |
| Burrows' Delta | 13 of 18 | 2 of 5 | 0 of 2 | 11 of 11 | 1 of 3 |
| Cosine Delta | 13 of 18 | 2 of 5 | 0 of 2 | 11 of 11 | 1 of 3 |
| General Imposters | 11 of 18 | 0 of 5 | 0 of 2 | 11 of 11 | 1 of 3 |
| ENSC | 7 of 18 | 2 of 5 | 0 of 2 | 5 of 11 | 0 of 3 |
| Our models, 125M | 5 of 17 | 5 of 5 | 0 of 2 | 0 of 10 | 1 of 3 |
| Our models, 297M | 7 of 17 | 5 of 5 | 2 of 2 | 0 of 10 | 2 of 3 |
| Our models, 590M | 6 of 17 | 4 of 5 | 2 of 2 | 0 of 10 | 2 of 3 |
| Style encoders, 297M / 590M | 7 / 10 of 18 | 5 / 4 of 5 | 1 / 2 of 2 | 1 / 4 of 11 | 1 / 2 of 3 |

(The language models' text preparation yields one passage fewer of Snowden.)

By passage the Delta methods lead, 13 of 18 against the 297M's 7 of 17. By author the order
reverses: Burrows' Delta 1 of 3, the 297M 2 of 3. Both figures describe the same data. Snowden
supplies 11 of the 18 passages; the word-count methods recognise him every time and the language
models never, while on the other two authors it is the other way round. Each family is fooled by a
different writer. An earlier draft read the passage count as "the older methods see through
imitation better"; counted by author there is no such finding (corrected 2026-11-12, section 9).

On the 430-test benchmark, the imitation-scripture task (24 tests, four authors, same-register
training and test) gives a few disagreements, all in our models' favour: against Burrows' Delta 2-0,
2-0 and 1-0 at 125M, 297M and 590M; against ENSC 3-0, 3-0 and 2-0. That is too few to weigh.

**The ceiling is real.** More authors would settle it, and the library does not hold them. The
corpus-wide search for imitation scripture judged 1,349 candidate works (by two AI models with a
third breaking ties; a simulated reading) and found 18 works under 10 author names. Only 3 of those
authors left 10,000 words or more of other prose in the library: the three above
(`data/benchmark/dual_register.json`). Outside 1780-1830 most imitation scripture is anonymous
satire [CHECK: no results file found for the search outside the period; stated as in the outline].

**Reading.** Three authors are too few to judge either way. This paper makes no claim that our
models, or the older methods, can or cannot see through biblical style on the strength of this
test. A larger test of the same worry, on 553 authors [CHECK: count as given in the outline; no
results file] who left both sermons and other prose, was considered and not run (owner's decision,
2026-11-12). The worry it addresses, that a model follows the biblical style and not the person, is
instead tested directly on the Book of Mormon in sections 6.2 and 6.3, with samples of equal size
and with writers who could not have written the book.

### 5.4 "None of these"

**Preparation.** Remove the true author from the list and score the same passages. A method with a
match score declares a match when its best candidate scores above a threshold. The registered bar
sets that threshold where 95% of true authors clear it, and allows at most 5% false matches there
(section 2.7). Burrows' and Cosine Delta produce a ranking only and have no match score.

**No method passes.** False matches at the registered threshold:

| Method | Part 1, 110 tests | BOM-75, 430 tests | 32 new authors, 640 tests | BOM-75, each author held out in turn (Amendment 55, post hoc) |
| --- | --- | --- | --- | --- |
| Our models, 125M | 47% | 75% | 56% | 57% |
| Our models, 297M | 38% | 67% | 58% | 52% |
| Our models, 590M | 22% | 63% | 62% | 51% |
| General Imposters | 83% | 79% | | |
| ENSC (its own "none") | 78% | 76% | | |

(`data/benchmark/open_set.json`, `part2/open_set.json`, `alm_*_p3.json`, `clustered.json`. The
older methods' BOM-75 figures are on their own draw of passages.) In the first three columns the
threshold is set on one half of the tests and applied to the other. In the last, the threshold for
each author's tests is set only from other authors, which is the stricter version: 51-57%.

The bar is 5%. The best figure anywhere in the table is 22%, on the narrowest benchmark, and on the
wider ones every method wrongly declares a match for more than half of the passages whose author is
absent.

**The whole trade-off, not one failed bar.** A threshold can be moved: stricter, and fewer strangers
are matched but fewer true authors are confirmed. Reporting only the registered point hides how
good or bad the method is elsewhere, so the full curve was computed, each author held out in turn
(Amendment 55, post hoc; 430 tests, 23 authors; `data/benchmark/clustered.json`):

| | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Area under the curve (1.0 is perfect, 0.5 is chance) | 0.91 | 0.91 | 0.89 |
| Equal-error rate (where the two kinds of error are equal) | 16% | 14% | 16% |
| Aiming at 5% false matches: false matches actually obtained on held-out authors | 5.6% | 5.8% | 6.0% |
| ... and true authors confirmed there | 61% | 53% | 38% |
| Aiming at 10%: true authors confirmed | 74% | 74% | 73% |
| At the registered threshold: true authors confirmed | 86% | 87% | 87% |

Read the other way round from the registered bar: if false matches are held to about 5%, our models
confirm between 38% and 61% of true authors and miss the rest. A "match" at that setting would mean
something; a "no match" would not, because a true author is missed about half the time.

**The standard fix was tried and failed.** Speaker verification, the field that decides whether a
voice belongs to a claimed speaker, has a standard remedy for exactly this: score normalisation.
Each model's score is put on a common scale by how that model scores other people (z-norm), or the
top candidate's normalised score is compared with the runner-up's (z-margin). An exploratory look
by the simulated research agent, splitting the data by test passage, suggested a large gain: about
three in four true authors confirmed at about 2% false matches
(`docs/research/2026-11-12-easy-wins-and-sota.md`). We then ran it with the rule written down first and the
split made by author, so that no passage by a tested author informs his own threshold (Amendment
55, post hoc). It covers 344 tests from 20 authors: the dictated task has one test author and so nothing to
normalise on, as the amendment says, and the Federalist task, with two, dropped out by the same
rule, which the amendment had not named.

| Aiming at 5% false matches | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Plain score (all 430 tests): false matches on held-out authors | 5.6% | 5.8% | 6.0% |
| z-norm: false matches on held-out authors | 21% | 17% | 19% |
| z-margin: false matches on held-out authors | 22% | 20% | 26% |

Normalisation does not carry over to authors it has not seen: aimed at 5%, it delivers 17-26%. The
split by passage had let each author's quirks leak into his own threshold. The plain score at least
holds the rate it aims for. Normalisation is therefore not a better algorithm here, and it is not
used.

**What this means for the rest of the paper.** Every method can rank candidates. None can say
"none of these" with a known, low error. This is why the opening statement of section 1 has two
halves. The rankings of sections 6 and 7 say whose writing is closest among those tested. They
cannot say that the author is among those tested, and no result in this paper should be read as
doing so.

### 5.5 Model size

**Preparation.** The three sizes were trained on the same text and take the same tests, so the
only difference is the number of parameters. The 1B that would have extended the series failed in
training (section 2.8).

| Measure | 125M | 297M | 590M |
| --- | --- | --- | --- |
| Right author, 110 tests | 93.6% | 99.1% | 98.2% |
| Right author, 430 tests | 91.6% | 93.3% | 93.3% |
| Right author, 640 tests (32 new authors) | 93.6% | 92.5% | 90.6% |
| Right author from a list of all 55 authors (Amendment 58, post hoc) | 86% | 86% | 82% |
| False matches, 110 tests | 47% | 38% | 22% |
| False matches, 430 tests | 75% | 67% | 63% |
| False matches, 430 tests, each author held out | 57% | 52% | 51% |
| False matches, 640 tests (32 new authors) | 56% | 58% | 62% |

**Picking the author: the sizes tie.** On 110 tests the 297M is ahead of the 125M (6 tests to 0, p
0.03) and level with the 590M. On the larger sets no size leads consistently, and on the 32 new
authors the order is the reverse of the order of size. The by-author comparisons of 5.1 come out the
same at every size.

**Longer lists (Amendment 58, post hoc).** The benchmark's lists have about four authors. To see
whether a bigger model holds up better as the list grows, each of the 55 authors' tests was
attributed among lists of 2 to 55 authors (`data/benchmark/list_size.json`). Accuracy, averaged by
author, on random lists:

| List size | 2 | 4 | 12 | 30 | 55 |
| --- | --- | --- | --- | --- | --- |
| Our models, 125M | 98% | 95% | 91% | 88% | 86% |
| Our models, 297M | 97% | 95% | 91% | 88% | 86% |
| Our models, 590M | 96% | 93% | 87% | 84% | 82% |
| Burrows' Delta | 93% | 85% | 75% | 67% | 62% |
| Cosine Delta | 91% | 85% | 73% | 66% | 59% |
| ENSC | 91% | 83% | 70% | 61% | 54% |
| General Imposters | 89% | 80% | 68% | 56% | 49% |

Our models lose about 10 points between a list of 4 and a list of 55; the older methods lose 23 to
31. A bigger model does not extend the list: the 590M is the weakest of the three at every length.

**"None of these": bigger was better on two benchmarks and not on the third.** On Part 1's tests
false matches fall with size, from 47% to 38% to 22%. On BOM-75's 430 they fall from 75% to 67% to
63%, and the ranges of the 125M (71-79%) and the 590M (59-68%) do not overlap; nearly all of that
gain is in the first step. On the 32 new authors the order reverses (56%, 58%, 62%), with
overlapping ranges. So the evidence that size helps at "none of these" is real on the first two
sets and is not repeated on the newest and largest one. At every size and on every set the rate is
many times the 5% bar.

**Summary of the scorecard.** Judged on known answers:

| Job | Best | How good |
| --- | --- | --- |
| Picking the author from a short list | our models, any size | 92-93% of 1,070 tests on 55 authors, against 72-79% for the older methods; better than each of them counted by author (5.1) |
| Picking from a list of 55 | our models, 125M or 297M | 86% |
| Not mistaking period English for a person | period-trained models over a modern one | 22-47% false matches against 86-92% on the same 110 tests (5.2) |
| Recognising a writer in biblical style | not known | three authors; too small to judge (5.3) |
| Saying "none of these" | no method | no method near the 5% bar; normalisation did not help (5.4) |
