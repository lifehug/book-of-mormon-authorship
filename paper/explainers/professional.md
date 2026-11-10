# Authorship, borrowing and dating of the earliest Book of Mormon text: methods and findings for specialists

*Draft 1, 2026-11-10. Written for statisticians, stylometrists and computational linguists. Every
number is read from a committed file in https://github.com/lifehug/book-of-mormon-authorship;
settings come from `config/preregistered.yaml`, pre-registered on OSF (https://osf.io/6ugxc/) with
42 dated amendments, the post hoc ones labelled. The analyst is an AI model working with one
person; the blinding and every review step are simulated, and labelled so. The study takes no
position on divine inspiration; it asks which known writers, if any, the text closely resembles.*

## The questions and the design constraints

Three questions: who wrote the text (Q1), what it borrowed (Q2), and when its language dates from
(Q3). Prior computational work split along predictable lines: wordprint studies (Larsen, Rencher
and Layton 1980) found the narrators distinct; nearest shrunken centroids (Jockers, Witten and
Criddle 2008) pointed to Rigdon and Spalding; Fields, Schaalje and Roper (2011) showed that the
2008 result depended on a closed candidate set. The design responds to four recurring failures:

1. **Closed sets.** Every attribution method must be able to say "none of these", and its
   false-match rate on open-set negatives is measured before use.
2. **Register confounds.** The text is about 7% King James wording. Every KJV-aligned span is
   masked (passim at frozen settings, validated on 200 alignments) before attribution and dating.
3. **Garden of forking paths.** Thresholds, feature sets, seeds and model choices are fixed in a
   pre-registered config before the text is scored; deviations are dated amendments.
4. **Leakage.** The Book of Mormon is excluded from every model's training, tuning and calibration
   until a single blind scoring run, and any volume sharing 20+ of its original 12-token strings is
   removed from training data.

## Data

A catalog of 695,021 records (Harvard Institutional Books 1.0, HathiTrust public domain, Internet
Archive, Chronicling America, EEBO-TCP) with corrected dates and MinHash deduplication. The
time-locked language models train on 202,816 volumes printed 1780-1830 (25.7B tokens). Candidate
samples have provenance tiers (handwritten, dictated, printed by the author, posthumous); samples
under 10,000 masked words are flagged unreliable before scoring, and post-1830 samples form a
secondary analysis because their authors had read the text. Four genre-matched control groups:
pseudo-biblical imitations, 1820s sermons, histories with Native American origin narratives,
general prose.

## Methods

**Classical stylometry (5.1).** Burrows' Delta and Cosine Delta on z-scored most-frequent-word
frequencies (300 MFW registered); General Imposters (100 trials, half the features per trial,
genre-matched imposters) as the verification score; extended nearest shrunken centroids (ENSC)
with its own "none" answer.

**Time-locked language models (5.2).** GPT-style decoders trained from scratch on 1780-1830 text
only, at 125M, 297M and 590M parameters (a 1B diverged at step ~15,800 and was replaced by a 590M
with QK-norm, Amendments 38-39), one epoch, 524,288-token batches, cosine schedule. Attribution by
authorial language models (ALM): one fine-tuned copy per candidate sample and per control group;
a text's score for a candidate is the mean window log-loss under that candidate's model minus the
base model's; the verification score is the margin between the best control model and the
candidate model. Variants: V1 (tenfold learning rate), V2 (a classifier head over a task's authors),
V3 (base-model hidden states with General Imposters).

**Style embeddings (5.4).** The time-locked model fine-tuned contrastively (symmetric InfoNCE over
two episodes of passages from different works of the same author) so same-author passages
cluster; scored by cosine distance and General Imposters on the vectors, at 297M and 590M
backbones.

**Borrowing (5.5).** Exact aligned reuse; rare shared 4-grams against a null of 204,520 period
volumes; semantic paraphrase search over 163 million passages with genre-matched nulls; story
order (event skeletons aligned, order permutation test); and a triage of every surfaced pair into
biblical, common or specific, by two passes (the second simulated).

**Dating (5.3).** A grammar model (61 early-modern grammatical features, L2 multinomial logistic
regression over 31 date bins from 1473 to 1830, fitted on held-out authors) decides; a lexical
model and a transformer cross-check (a classifier on the 297M model's hidden states) are reported
beside it. H3a: more than half of segment medians in 1780-1830; H3b: more than half in 1473-1700
(Amendment 19). H3c: the text's predicted dates are indistinguishable from the 1780-1830
pseudo-biblical controls' (permutation p > 0.05).

**The benchmark and the decision rule (section 7, 6.1).** Before any Book of Mormon scoring, every
method is run on known-answer tasks: Federalist papers, period imitation scripture and dictated
fiction (180 trials for the classical methods; 110 held-out tests for the language models). A
method may return *match* only where its benchmark false-match rate is at most 5%; 6.2 requires
two independent families to return *match* on both halves of the text. A false-match ladder
(Amendment 33) reports, for each call, the rung at which it would count, with the real benchmark
rates beside it.

**The blind run (section 8).** 211 sealed ids: 168 Book of Mormon chunks of 5,000 words and 43
decoys (22 held-out candidate passages, 21 control passages), shuffled and keyed; each method's
outputs hashed and committed before the key was read (simulated blinding).

**Synthesis (6.7).** A Bayesian combination over hypotheses (each primary candidate, and "not in
set"), each family's likelihood built from its benchmark call rates and closed-set accuracy, its
weight the product of that accuracy and its section 9 imitation weight (from a forward test on 17
deliberate imitations); sensitivity over the prior on "not in set" (0.2-0.8), equal weights,
chunk independence and drop-one-family.

**The whole-library sweep (BOM-39, BOM-47).** 23,872 authors indexed by MFW and style vectors;
calibration on 200 held-out books (true author first 27-35%, so not usable as attribution); lead
thresholds and an expected false-lead count of 0.035 per query fixed before scoring.

## What the checks showed before unblinding

| Method | Right author (benchmark) | Open-set false matches | Stable? |
| --- | --- | --- | --- |
| ALM primary, 125M / 297M / 590M | 0.936 / 0.991 / 0.982 | 0.473 / 0.382 / 0.218 | Yes: reproduced to the decimal on other hardware |
| V1 | 0.936 / 0.936 / 0.627 | 0.455 / 0.473 / 0.818 | No: its rate damaged the 590M (loss +0.81 nats); at a rate chosen on held-out training text it equals the primary (Amendment 41) |
| V2 | 0.900 / 0.909 / 0.764 registered | 0.09-0.98 across six seeds | No (Amendment 42) |
| General Imposters | 0.833 | 0.617 | Deterministic |
| Style embeddings 297M / 590M | 0.839 / 0.839 | 0.500 / 0.628 | One run each |
| GPT-2 124M / 355M, ALM | 0.900 / 0.945 | 0.918 / 0.855 | (ablation) |

**No method passes the registered bar.** Time-locked pre-training halves false matches relative
to GPT-2 at matched size, and false matches fall with size, but the best stable rate is 21.8%. On
imitation, the model-based methods are weaker than the classical ones (ALM 5-7 of 17; Delta 13 of
18), so their section 9 weight is zero. These readings were written down before unblinding
(`docs/method-reliability.md`).

## Results

**Decoys.** The right candidate is ranked first on 15-21 of 22 candidate decoys depending on the
method; no method returns *match* on any of the 21 control decoys.

**Attribution (Q1).** General Imposters and the style encoders return no *match* on any chunk
under the registered thresholds; the candidate models return 10, 5 and 3 matches of 168 by size,
below what their false-match rates would produce for text by no candidate. The sweep produces no
lead. H1a (two families agree on a candidate) is not supported. The registered synthesis, in which
only General Imposters carries weight and only the three candidates with pre-1830 samples over the
registered 10,000-word floor enter (Joseph Smith and Cowdery are excluded, untested rather than
ruled out), gives "not in set" 0.744 on both halves (Hunt 0.089,
Spalding 0.085, Ethan Smith 0.082; prior 0.5), 0.42-0.92 across the prior grid, 1.00 under equal
weights. Where methods rank someone first, it is mostly Joseph Smith (Cosine Delta 131 of 168) or
Cowdery (590M ALM 109), through pre-1830 samples of 2,720 and 1,310 words flagged unreliable before
scoring. The Cowdery ranking was leakage (below). In the rerun without Book of Mormon quotations
(Amendment 43), every method ranks Joseph Smith's sample closest (Cosine Delta 148, ALM 297M 168,
590M 131), match calls fall to 0-2 of 168, and the synthesis is unchanged (0.744). His is the only
sample in the text's register (revelations dictated in scriptural voice in the same months), and he
dictated the text, so the ranking confounds register with authorship and dictator with composer.

**Narrators (6.3).** Narrators separate at 0.744 (chance 0.277, p 0.001) and dictation order at
0.758 (chance 0.502), both below the 0.96 benchmark accuracy for distinct authors: not separable as
different authors.

**Borrowing (Q2).** No named source stands out under its null in paraphrase or story order; *The
Late War* and *The First Book of Napoleon* pass the rare-phrase rule (p 0.0006, 0.0003) that the
pseudo-biblical genre as a whole also passes (*Book of Jasher*, 1829, scores higher). Of 1,069
triaged pairs, none is specific under both passes: 36% are explained by King James wording, 64% by
period stock phrasing.

**Dating (Q3).** Grammar model: H3b (78% of 215 segment medians before 1700; median 1661); lexical
1736 and transformer 1755 (neither window). H3c rejected: the text dates earlier than the
pseudo-biblical controls (1661 vs 1734 grammar, 1738 vs 1794 lexical; p 0.0001).

**Public claims (BOM-42).** Seventeen claims, from critical, apologetic and academic sources, with
decision rules written before any result: 2 supported, 6 contradicted, 4 mixed, 1 not addressed,
4 untestable (`docs/claims-verdicts.md`).

## Threats to validity

- **A sealing failure, found after unblinding:** Cowdery's pre-1830 sample ("Articles of the
  Church of Christ", 1829) is 40% word-for-word Book of Mormon text, and Pratt's books quote it; the
  sealing check ran on the training corpus, not on candidate samples. Amendment 43 (post hoc)
  drops quotations only (passages of 20+ words copied after the matching passage was dictated),
  keeping shared idiom, so Joseph Smith's 1828-29 revelations are unchanged; the rerun is reported
  beside the registered run (`docs/bom-overlap-analysis.md`).

- **No method meets the 5% bar**, so every attribution result is graded evidence.
- **Candidate samples are small and uneven**; the two that rank closest are the smallest and come
  from the text's own production circle and register.
- **Dictation and scribes sit between any author and the page**; no stylometric result separates
  composer from dictator or scribe.
- **Known-answer controls** (Amendment 9) show the borrowing and dating tests do not separate
  genuine translations from texts presented as ancient, so none of them bears on translation.
- **Imitation:** the model-based methods are the more easily misled, which is why they carry no
  weight in the synthesis.
- **Coverage:** the sweep covers surviving printed authors only.
- **Post hoc steps** (Amendments 19, 33, 38-42) are labelled as such, filed before the results they
  govern where possible.

## Reproducing it

Code, config, every result file and the pre-registration are public. Every model is published on
Hugging Face (`etherfuse/timelocked-1830-*`, `etherfuse/bom-authorship-*`), with SHA-256 lists in
`data/manifests/`. Three sources are licensed and cannot be redistributed; `docs/replication.md`
gives the steps to obtain the same access. The run guide is `eval/README.md`.
