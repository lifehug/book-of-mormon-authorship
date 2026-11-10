## 4. Measuring every method on known answers

Every method answers two different questions, and they are measured separately:

- **Ranking:** "whose sample is closest?" With the true author among the candidates, how often is
  the true author ranked first (closed-set accuracy)?
- **Matching:** "is it confidently this person?" With the true author removed, how often does the
  method still say "match" to someone (the false-match rate)? The registered bar is 5%.

A method can be excellent at the first and poor at the second. Section 6.1 of the pre-registration
calls a match only on the second.

### 4.1 The benchmark (110 held-out tests; `data/benchmark/open_set.json`)

The candidate models (one copy of a time-locked model fine-tuned per author, scored by how much
better it predicts a text than the base model) were tested on held-out text of known authors:
Federalist papers, imitation scripture with known authors, and dictated text.

| Method | Size | Ranking (true author first) | False matches | Passes (>= 0.90 and <= 0.05) |
| --- | --- | --- | --- | --- |
| Candidate models (primary) | 125M | 0.936 (0.873-0.974) | 0.473 (0.377-0.570) | no |
| Candidate models (primary) | 297M | **0.991** (0.950-1.000) | 0.382 (0.291-0.479) | no |
| Candidate models (primary) | 590M | 0.982 (0.936-0.998) | **0.218** (0.145-0.307) | no |
| Burrows' Delta, same held-out tests | - | 0.955 | (no match score) | no |
| Cosine Delta, same tests | - | 0.818 | (no match score) | no |
| General Imposters, same tests | - | 0.745 | 0.827 | no |
| ENSC (Schaalje et al.), same tests | - | 0.964 | 0.782 | no |
| GPT-2 (modern training), primary method | 124M / 355M | 0.900 / 0.945 | 0.918 / 0.855 | no |
| V1 (learning rate 1e-4, registered) | 125M / 297M / 590M | 0.936 / 0.936 / 0.627 | 0.455 / 0.473 / 0.818 | no |
| V2 (classifier head, registered seed) | 125M / 297M / 590M | 0.900 / 0.909 / 0.764 | 0.282 / 0.136 / 0.391 | no |
| V2, five further seeds (range) | 125M / 297M / 590M | 0.66-0.93 / 0.51-0.76 / 0.40-0.78 | 0.09-0.93 / 0.53-0.98 / 0.32-0.93 | no |
| V3 (hidden states into classical trials) | 125M / 297M / 590M | 0.839 / 0.844 / 0.844 | 0.689 / 0.717 / 0.706 | no |

Intervals are exact 95% binomial intervals over the 110 tests (52, 42 and 24 false matches); the
benchmark has three tasks (Federalist papers, imitation scripture, dictated text), so these rates
are measured on a narrow range of genres. The classical methods and style encoders were also scored on the 180 classical trials (General
Imposters 0.833 / 0.617; ENSC 1.000 / 0.661; style encoder 0.839 / 0.500), compared within that
set, not across.

On the same 110 tests the 297M model ranks better than General Imposters (27 tests to 0) and
Cosine Delta (19 to 0), but not significantly better than Burrows' Delta (4 to 0, p 0.13) or ENSC
(paired exact McNemar tests): the language models' gain is mainly in matching, not in ranking.

**Benchmark accuracy overstates accuracy on a wider field.** On 30 fresh period authors, every
classical method falls to about 55-60% (Burrows' Delta 57.0%, Cosine 60.3%, General Imposters
56.5%, ENSC 54-55%), and none of three attempted repairs helped (BOM-58, BOM-60). Our General
Imposters reproduces the published method's results on its own benchmark (11 of 12 rows within 4
points), so its failure is the method's, not an implementation slip; our first ENSC was not the
published method and was replaced. ENSC ranks perfectly on the classical trials (1.000) but says
"match" to a wrong author 66% of the time, and its "none of these" answer moves with candidate
sample length (from 80% wrong to 0% between 1,000- and 10,000-word samples), so it was retired as an
attribution method and kept as a replication (section 3). The classical verdicts are stable across 54 alternative
settings, except General Imposters' (BOM-40).

**Three findings.**

1. **Period training matters for matching.** The same method with GPT-2, trained on modern text,
   ranks nearly as well but says "match" to the wrong author 86-92% of the time; the period models
   do so 22-47%.
2. **False matches fall with size** (47%, 38%, 22%) while ranking was already at its ceiling.
3. **Some variants are unstable.** V1's registered learning rate broke the 590M (its fine-tuned
   models raised the loss on new text); at a rate chosen on held-out training text it equals the
   primary method (Amendment 41, post hoc). V2's single registered numbers were one lucky seed:
   five more seeds range from 9% to 98% false matches (Amendment 42), so V2 carries no weight.

### 4.2 Robustness to deliberate imitation (`data/benchmark/imitation.json`)

Three authors who wrote both imitation scripture and ordinary prose (Snowden, Dodsley, Kenrick):
can a method trained on their ordinary prose recognise their imitation scripture among 13
candidates?

| Method | Imitation text to its real author | Weight in the synthesis |
| --- | --- | --- |
| Burrows' / Cosine Delta | 13 of 18 each (0.72) | half |
| General Imposters | 11 of 18 (0.61) | half |
| ENSC | 7 of 18 (0.39) | none |
| Style encoders 297M / 590M | 7 / 10 of 18 | none |
| Candidate models 125M / 297M / 590M | 5 / 7 / 6 of 17 | none |

Writing in a biblical register hides the author from the model-based methods more than from the
classical ones, and size does not help. This is why the registered synthesis rests on the
classical family alone (section 5.4).

### 4.3 Which method is best at what

Judged on known answers only, never on the Book of Mormon:

| Task | Best | Its figure | Next |
| --- | --- | --- | --- |
| Ranking the true author first | candidate models, 297M | 99.1% | 590M 98.2% |
| Fewest false matches | candidate models, 590M | 21.8% | 297M 38.2% |
| Recognising candidates' own held-out text in the blind run (decoys called "match") | candidate models, 125M | 20 of 22 (91%), at 47% false matches | 297M 15 of 22, 590M 11 of 22 |
| Seeing through deliberate imitation | Burrows' and Cosine Delta | 72% | General Imposters 61% |
| Reproducible across machines and seeds | candidate models (primary), classical methods | identical reruns | V2 unstable |

No method passes the registered bar, so every attribution in this paper is graded evidence: a
ranking can say who is closest; no method can yet say "not this person" with a known error below
5%.

### 4.4 How big should the model be?

**Why size matters.** From 125M to 297M to 590M parameters, false matches fell from 47% to 38% to
22%; ranking was already 94-99%. Matching is the weak half, and size is the one lever that has
moved it.

**What limits size is the data.** The training text is 25.7 billion tokens of 1780-1830 English,
close to all that survives digitally. A common rule of thumb from modern large-model research is
about 20 training tokens per parameter for the best use of a fixed compute budget (a guideline,
not a law). By it the best fit for this data is about 1.3B parameters. The 590M had 43 tokens per
parameter, the 297M 86, the 125M 205. Beyond about 1.3B the text must be repeated; up to about four
passes still helps a little, so 2-4B is the practical outer limit, with sharply diminishing
returns.

**Ways to more data, and their costs.** The period's newspapers (catalogued, not yet used for
training); Google-digitized volumes not in the public sets (BOM-71); or a wider window (for example
1700-1830), which weakens the time lock that makes "ordinary" mean ordinary for 1830. With the
Google volumes the period text would be about 32-33 billion tokens, a best fit near 1.6B.

**When to stop.** Grow only while the last step cut false matches meaningfully and the data
supports the next size at about 20 tokens per parameter or more; stop when gains flatten or the
data would have to repeat. By that rule a model of about 1.3B with QK-norm is justified and is the
logical last step on the present data; beyond about 2B is not. Whether any size reaches 5% false
matches is unknown: a straight extension of the trend would reach it only around 1.6-2B, and
trends of this kind usually flatten. Section 13 gives the staged plan.
