## 5. The tests on the Book of Mormon

Each test is preceded by how it was prepared. The registered run is the main record (git tag
`blind-registered-2026-11-10`); where a later correction changes a number, both are shown
(section 7).

### 5.1 The blind procedure and its decoys

**Preparation.** The 168 whole chunks of the narrator scheme (121 of 2,000 words, 47 of 5,000) were
sealed with 43 decoys: 22 held-out passages by the candidates themselves and 21 control passages
by nobody in the set, which no model trained on. Ids were opaque, the key was written outside the
repository, and hashes of key and sealed set were committed before scoring. The scoring was run by
a new AI session given only the scoring script, without the key: this is **simulated blinding**,
since one person designed and runs the study. Outputs were hashed and committed before unblinding
on 2026-11-10.

**The sanity check.**

| Method | Candidate decoys: right candidate first (of 22) | Control decoys called a match (of 21) | Candidate decoys called a match to their author (of 22) |
| --- | --- | --- | --- |
| Burrows' / Cosine Delta | 20 / 15 | (no match call) | |
| General Imposters | 19 | 0 | 0 (cannot reach "match" at its registered threshold) |
| Style encoders 297M / 590M | 16 / 18 | 0 | 0 |
| Candidate models 125M / 297M / 590M | 20 / 21 / 19 | **0 at every size** | 20 / 14 / 11 |

Every method found real candidate text most of the time, and no method called a stranger's text
a match. The run is valid by section 8's rule. Two methods did worse on the decoys than on the
benchmark (Cosine Delta 15 of 22, the 297M style encoder 16 of 22): accuracy measured on the
benchmark does not fully carry over to new text.

### 5.2 Wording

**Preparation.** Four searches, each against the period library with the text's King James spans
labelled: exact reuse (passim alignment against every volume printed before it); rare phrases
(4-grams found in at most 5 period texts, scored per 10,000 words against 204,520 volumes); paraphrase
(163 million 128-word passages embedded and searched, each source compared with 500 genre- and
length-matched volumes); and triage of every surfaced pair as biblical, common or specific by one
model with a blind second pass by another (simulated review).

**Results.**

- **Exact reuse.** 58 short passages in 47 earlier-catalogued volumes, 0.52% of the text; 17 of the
  volumes are later texts quoting it under wrong early dates, and without them 0.16% remains, all
  loose stock phrasing (9-46 tokens). For comparison, *The Late War* shares 8.92% with earlier
  books.
- **Rare phrases.** *The First Book of Napoleon* (rank 63 of 204,520, p 0.0003) and *The Late War*
  (rank 131, p 0.0006) pass the registered rule; *View of the Hebrews* (rank 9,496) and Spalding do
  not. The 1829 reprint of Ilive's *Book of Jasher*, another imitation scripture, shares more than
  either; the shared phrases are battle and chronicle formulas, and 2,044 volumes pass the rule.
- **Paraphrase.** No named source stands out from its genre: *View of the Hebrews* leads the
  Indian-origins group but 77 of 500 matched religious volumes score higher. In the whole-library
  search editions of Josephus take 14 of the top 20 places, and the registered rule flags 622
  sources, which mostly measures biblical register.
- **Proposed parallels (exploratory).** Of the 500 parallels proposed in Rick Grunder's *Mormon
  Parallels*, 139 are in the catalog; their sources score slightly closer than matched volumes
  (median percentile 91.0 against 87.4, p 0.087), as expected from how they were chosen, and only
  Josephus stands out. Josephus, the leading paraphrase source, was on sale in Palmyra and nearby
  from 1822 and in E. B. Grandin's own stock from late 1828 into spring 1829 (Appendix B).
- **Triage.** Of 1,069 surfaced pairs, 382 are King James wording, 685 period stock phrasing, and 2
  were called specific on the first pass; the second pass called both common. **No pair is
  specific under both passes** (agreement 0.74, kappa 0.51).

**Known-answer check.** None of these searches separates genuine translations of ancient texts from
compositions presented as ancient (Amendment 9; exact reuse p 0.96, rare phrases 0.93, paraphrase
0.50). They describe which period books share the text's wording; they cannot speak to the
translation question.

### 5.3 Story structure

**Preparation.** Each 2,000-word block of the text, and of each source, was reduced by a hosted
model to at most 12 role-named events (checked on 20 King James chapters read twice: median
agreement 0.92), giving 1,421 events for the Book of Mormon. Sequences were aligned
(Smith-Waterman) and each alignment tested against 1,000 shuffles of the source's order.

**Positive control.** Josephus retelling Genesis-Judges shares 108 events in order with the Bible
(p 0.001): the test finds a retold story when there is one.

**Results.** One book meets the registered level (order p at most 0.01): Benjamin Church's *History
of Philip's War*, first of 49 in its group, p 0.008. The shared run is six events from one stretch of
each book (Alma 60-61: a commander writes angrily to the governor, the governor replies that rebels
have driven him out, the commander marches to help; in Church, a governor sends a captain with a
letter to raise troops): the common shape of military correspondence, not a shared episode. With 49
books tested, one such p-value arises by chance about 4 times in 10, so it is reported as it came
out and read as chance. Among the 20 leading sources of the paraphrase search the longest shared run
is 9 events (Josephus, p 0.24). Named sources: *View of the Hebrews* 1823, 3 events (p 0.97) and 1825, 2 (p
1.0); Spalding, 4 (p 0.67); *The Late War*, 2 (p 1.0); *Napoleon*, 3 (p 1.0).

### 5.4 Authorship

**Preparation.** Every method in section 4 scored every chunk against every candidate sample:
the classical methods (Burrows' and Cosine Delta, General Imposters), the style encoders (297M and
590M), and the candidate models (125M, 297M, 590M). Each method's "match" threshold was fixed on
the benchmark before the run.

**Matches.** Under the registered rule, General Imposters and the style encoders call no chunk a
match; the candidate models call 10, 5 and 3 of 168 (125M, 297M, 590M), and 2, 2 and 0 after Book of
Mormon quotations were removed from the candidate samples (Amendment 43). These counts are below
what the models' false-match rates would give for text by no candidate. **No candidate is matched
by two independent families on both halves (H1a not supported).**

**Ranking.** After Amendment 43, every method ranks a Joseph Smith sample first at least as often
as any other candidate: Cosine Delta 148 of 168 chunks, Burrows' Delta 91, General Imposters 66 (tied
with Pratt), style encoders 151 and 99, candidate models 159, 168 and 131. In seven of eight
methods it is his 1828-29 revelations; Burrows' Delta prefers his later ordinary prose (section
10.1). The full table per candidate, method and size is in section 10 and
`data/blind/a43/per_candidate.json`.

**The synthesis (6.7).** The registered Bayesian synthesis weights each family by its benchmark
accuracy times its imitation weight. Both model-based families earned zero imitation weight
(section 4.2), so only General Imposters enters, and the posterior is the same at every size. It
covers only the three candidates with pre-1830 samples of at least 10,000 words: "not in set" 0.744
(prior 0.5), Hunt 0.089, Spalding 0.085, Ethan Smith 0.082; across priors 0.2-0.8, 0.42-0.92.
A placebo run after unblinding showed the synthesis leans to "not in set" even on these
candidates' own held-out passages (Ethan Smith 0.59, Hunt 0.56, Spalding 0.51; controls 0.63), so
**0.744 carries little information**: General Imposters cannot say "match" at its registered
threshold, and the synthesis inherits that (section 7). Joseph Smith and Cowdery are outside it,
untested by it rather than ruled out.

**The whole-library sweep (descriptive).** 23,872 period authors were compared with the text. The
sweep failed its own usability test (true author first for 27-35% of 200 held-out books against a
required 70%), so its result is descriptive. No author passed both lead thresholds (0.035
expected by chance); the nearest are writers in the scriptural and prophetic register (John Wroe,
George Fox, William Sewel), none near a threshold.

### 5.5 Dating

**Preparation.** Three models placed each segment on a scale from 1473 to 1830: a grammar model on
61 grammatical features from the early modern English literature (decides H3), a lexical model on
word frequencies with grammar words removed, and a transformer cross-check on the 297M model's
hidden states. Validated on held-out authors: mean errors 23, 13 and 10 years. King James imitation
moves the grammar model about 53 years early and the transformer not at all.

**Results.** The grammar model places 78% of the 215 segments' median years before 1700 and 7% in
1780-1830 (median 1661): **H3b**. The lexical model (median 1736) and transformer (1755) place the
majority in neither window. **H3c is rejected:** the text dates earlier than the 25 pseudo-biblical
control volumes of 1780-1830 (grammar 1661 vs 1734; lexical 1738 vs 1794; p 0.0001), and with each
book of the text as one unit (12 books) the result stands (p 0.0025 and 0.0001). Part of the early
date is the biblical register, but the text is more archaic than the period's other biblical
imitations, and the transformer, which imitation did not move, still dates it before them (1755
vs 1805). Seven of the 25 period imitations are themselves placed in the
early modern window by the grammar model, so the genre can reach it. Three cautions: an
early-modern placement is predicted by an early-modern source, by imitation of one, and by the King
James register alike; the models learned 1780-1830 English from edited print, so unedited New York
and New England vernacular may read to them as archaic; and hand-keyed text reaches the period
window less often than OCR text of the same years (55% against 83% of 1780-1809 segments), and the
Book of Mormon text is keyed, which alone could pull its dates earlier.

### 5.6 Internal voices

**Preparation.** The same classical classifier that separates real authors at 0.96 on the benchmark
was asked to separate the chunks by narrator, by dictation order, and by scribe.

| Grouping | Accuracy | By chance | p |
| --- | --- | --- | --- |
| Narrator (Nephi, Jacob, Mormon, Moroni; 121 chunks) | 0.744 | 0.277 | 0.001 |
| Dictation order (first or last dictated; 124 chunks) | 0.758 | 0.502 | 0.001 |
| Scribe | not testable: only Oliver Cowdery's hand fills three or more continuous chunks | | |

The narrators differ above chance but well below the level that separates different real
authors: **not separable as different authors**. Raw accuracy is about the same for dictation
order; corrected for chance, narrator separates somewhat better (0.645 against 0.514), so the
differences follow both who narrates and when a passage was dictated. The manuscript evidence (Appendix B) shows the original was taken down by ear:
sound-alike corrections are 6 to 12 times more common in the dictated original than in the copied
printer's manuscript, with the same scribe in both (Fisher p 2e-9; a simulated check of the page photographs confirms the ratio, and the tests
treat corrections on one page as independent, which overstates certainty). That bears on how the words
reached the page, not on whether they were composed, recited or read aloud.
