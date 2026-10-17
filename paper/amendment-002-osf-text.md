# Amendment 2: operational analytic choices

*Paste-ready text for https://osf.io/6ugxc/. Reasoning for each choice is in
`paper/amendment-002-draft.md` in the project repository; this is the registration text itself.*

---

**Amendment 2, [DATE], before any calibration or analysis.**

The original registration fixed the questions, the methods and the decision thresholds, but left
a number of operational values unspecified. Several others existed only as defaults in the
project's code and were never registered. This amendment pins them. It is filed before the
validation benchmark (BOM-21) calibrates any threshold, and before the Book of Mormon is scored
by any method.

No hypothesis, decision rule or threshold in the original registration is changed.

**Corpus.** Language filter: source metadata English, confirmed by automatic language
identification on a 2,000-character sample at probability 0.90 or above. Genre tagging: a fixed
eight-label set (sermon/devotional, pseudo-biblical, history/chronicle, fiction/narrative,
newspaper/periodical, legal/political, scientific/medical, other), assigned by a language model
with reasoning logged, validated against 300 hand-labelled volumes with the agreement rate
published. Spelling normalisation: MorphAdorner's standardiser with the Early Modern English
lexicon for pre-1700 text; for 1780-1830 text, long-s, ligature and OCR-artefact correction
only, with no lexical modernisation.

**Controls and imposters.** Imposter count 100 per trial, resampled from the genre-matched
control pool. Control set membership is published as an explicit list of volume identifiers with
its SHA-256 before the benchmark runs.

**King James masking.** Baseline text: the 1769 Oxford (Blayney) King James Bible. Alignment by
passim with word 5-grams, minimum alignment 8 tokens, maximum gap 100 characters, relative
overlap 0.5; these alignment parameters are validated against a hand-checked sample of 200
alignments and frozen before any Book of Mormon text is masked.

**Segmentation.** The narrator, dictation-order and scribe boundary file is published with its
SHA-256 before any segmented analysis. The discovery/confirmation split uses seed 20261017.

**Features.** Part-of-speech tagging: MorphAdorner with the NUPOS tag set for pre-1700 text,
spaCy en_core_web_trf for 1780-1830. The function-word list is fixed and published before the
benchmark, derived from the comparison corpus and never from the Book of Mormon. Content words
are nouns, verbs, adjectives and adverbs by the tagger's tags. Tokenisation: Unicode NFKC,
lowercased, long-s folded, split on non-alphanumerics except intra-word apostrophes and hyphens.

**Classical methods.** General Imposters: 100 trials, feature fraction 0.5, imposter fraction
0.5, cosine delta distance. Extended nearest shrunken centroid: the shrinkage parameter is
selected by 10-fold cross-validation on the Phase 3 benchmark over the grid {0, 0.5, 1, 2, 4, 8},
choosing the value with the highest open-set accuracy; the selected value is published before
the Book of Mormon is scored. Alpha 0.05 with proportional priors. All randomness derives from
root seed 20261017 by a documented function, recorded in each run log.

**Language models.** Base model 300 million parameters, preceded by a 125 million parameter
pilot. The pilot is a registered decision point and not only a debugging step: the Phase 3
validation benchmark is run at both sizes and both accuracies are published, so that the choice
of 300 million is reported as a measured result rather than asserted. If benchmark accuracy is
still rising steeply between the two sizes, a further dated amendment may raise the registered
range before the base model is trained; if it has flattened, the published figures stand as the
justification. The registered 100-300 million range in section 5.2 is unchanged by this
amendment. Tokeniser: byte-level BPE, vocabulary 32,000, trained on the 1780-1830 corpus only, so
that no modern text enters the model at any layer. Training: context length 1024, one pass over
the deduplicated corpus, AdamW, cosine schedule, peak learning rate 3e-4, 2% warmup.
Fine-tuning: full fine-tune per candidate, 3 epochs, learning rate 1e-5, with identical settings
and token budget for every candidate and every control group.

**Dating.** Classifier: regularised multinomial logistic regression over the grammatical feature
set, with a transformer variant reported alongside as a cross-check. The grammatical feature
list is fixed and published before the benchmark, drawn from features named in the early modern
English literature rather than selected on performance. Permutation tests use 10,000
permutations.

**Style embeddings.** A content-disentangled style representation, adapted to the period corpus
by contrastive training on same-author, different-topic pairs, with LUAR reported as a baseline.
Content-disentangled rather than semantic representations are specified because every text in
the comparison set shares a religious or pseudo-biblical register, and a topic-sensitive
representation would recover genre rather than authorship.

**Borrowing.** Shared n-gram counts are normalised by the geometric mean of the two texts' token
counts and reported as a percentile of the genre-matched null distribution. Semantic search uses
256-word passages with a 64-word stride.

**Blind run.** The decoy selection seed derives from root seed 20261017 by the documented
function; the sealing script records the derivation and not the key.

**Values registered as selection rules rather than fixed numbers.** Three values depend on data
not yet observed, and are registered as the procedure that will choose them: the ENSC shrinkage
parameter, the passim alignment parameters, and the grammatical feature list. Each procedure
runs on benchmark or control data only, never on the Book of Mormon, and the chosen value is
published before the Book of Mormon is scored. If a procedure proves unworkable, that is a
further dated amendment.
