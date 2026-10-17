# Amendment 2 (DRAFT): pinning the remaining analytic choices

**Status: approved by the owner 2026-10-17, awaiting OSF filing.** Every value below is agreed.
Nothing here is *registered* until Dave submits it to https://osf.io/6ugxc/ with a date and
section 11 of `paper/preregistration.md` records it. Until then `config/preregistered.yaml`
carries only the previously pinned values and these stay in its `pending_amendment` list — an
agreed value is not a registered one, and the distinction is the whole point of the exercise.

Paste-ready submission text: `paper/amendment-002-osf-text.md`. On filing, see
"After filing" at the end of this document.

**Why this exists.** The pre-registration fixed the questions, the methods and the decision
thresholds, but left about 28 operational choices open — some unstated, some sitting as code
defaults nobody registered. Either way the analysis will use *some* value. Choosing them now,
in public, before the benchmark calibrates anything, is the difference between a decision and
an accident. BOM-40 holds the inventory; this proposes the values.

**One rule used throughout.** Where a value can be read off the literature or the period, it is
fixed here. Where it genuinely depends on data we have not seen, the *rule for choosing it* is
fixed instead, and the rule is what gets registered. A registered selection rule is honest; a
number chosen after seeing results is not.

---

## A. Corpus

**`corpus.language_filter` — source metadata language is English, confirmed by automatic
language identification on a 2,000-character sample, keep at probability ≥ 0.90.**
Catalogue metadata is unreliable at this period and several collections mark everything
English. One cheap check removes the Latin and German volumes that would otherwise widen every
null distribution.

**`corpus.genre_tagging` — a fixed eight-label set (sermon/devotional, pseudo-biblical,
history/chronicle, fiction/narrative, newspaper/periodical, legal/political, scientific/medical,
other), assigned by an LLM with its reasoning logged, validated against 300 hand-labelled
volumes, and the agreement rate published.**
Genre matching is the control that stops biblical *register* masquerading as authorship, so it
has to be auditable rather than a black box. The hand-labelled sample is what makes the
agreement rate reportable; without it the labels are an assertion.

**`corpus.spelling_normalization` — MorphAdorner's spelling standardiser with the Early Modern
English lexicon for pre-1700 text (the TCP material used in dating); for 1780–1830 text,
normalise long-s, ligatures and OCR artefacts only, no lexical modernisation.**
English spelling was substantially standardised by the late eighteenth century, so normalising
the 1780–1830 corpus would erase real variation while fixing almost nothing. The early modern
set genuinely needs it. VARD2 is the better-known tool but requires manual work per corpus;
MorphAdorner was built for EEBO-TCP, which is exactly our pre-1700 source.

## B. Candidates, controls, imposters

**`imposters.count` — 100, drawn from the genre-matched control pool, resampled each trial.**
The `stylo` implementation's defaults and Koppel and Winter's own experiments sit in this range;
they used roughly 200 gathered by web search, which does not apply to a closed period corpus.
100 from a fixed pool is comparable and reproducible.

**`controls.sets_file` — an explicit list of volume IDs per control set, committed with its
SHA-256 before BOM-21.**
"Genre-matched controls" is not a specification. The IDs are.

## C. KJV masking

**`kjv_mask.edition` — the 1769 Oxford (Blayney) text, which is what an 1829 American KJV was.**
The pre-registration says "a period King James Bible"; this names it. Any later critical text
would import revisions that did not exist when the Book of Mormon was dictated.

**`kjv_mask.passim` — word 5-grams, minimum alignment 8 tokens (matching the already-registered
span rule at 4.4), maximum gap 100 characters, relative overlap 0.5.** The parameters are then
validated against a hand-checked sample of 200 alignments, and *frozen before any Book of Mormon
text is masked*.
The 8-token minimum is already registered, so the others are chosen to serve it. Validating
first and freezing before use is what keeps this from becoming a tuning knob.

## D. Segmentation

**`segmentation.boundaries_file` — `data/bom/segments.json`, committed with its SHA-256 before
any segmented analysis.** The narrator, dictation-order and scribe boundaries are editorial
judgements; publishing the file is what makes them checkable.

**`segmentation.split.seed` — `20261017`.**
Arbitrary by design. What matters is that it is fixed and public *before* the split is drawn,
because this split decides which half produces sweep leads and which half tests them.

## E. Features

**`features.pos_tagger` — MorphAdorner with the NUPOS tag set for pre-1700 text; spaCy
`en_core_web_trf` for 1780–1830.**
Modern taggers degrade badly on early modern English: CLAWS drops from about 97% on present-day
English to about 82%. MorphAdorner was built for this material. The 1780–1830 corpus is close
enough to modern English that a current tagger is the better choice there.

**`features.function_words_file` — a fixed, committed list, frozen before BOM-21 and never
derived from the Book of Mormon.**
The 1980 "wordprint" study failed because its features were dominated by *unto*, *behold* and
*yea* — biblical register, not authorship. Freezing the list in advance, from the comparison
corpus rather than from the questioned text, is the structural fix.

**`features.content_words` — nouns, verbs, adjectives and adverbs by the tagger's own tags.**

**Tokenizer rules — Unicode NFKC, lowercase, long-s folded to `s`, split on non-alphanumerics
except intra-word apostrophes and hyphens.** Currently a code default in
`classic/features.py`; stated so it is reproducible.

## F. Classical methods

**General Imposters: `trials` 100, `feature_fraction` 0.5, `imposter_fraction` 0.5, distance
cosine delta.** These are the `stylo` defaults and sit where the method's own literature puts
them. Registering them changes nothing about the code; it just stops them being accidental.

**ENSC `shrinkage` — chosen by 10-fold cross-validation on the Phase 3 benchmark over the grid
{0, 0.5, 1, 2, 4, 8}, selecting the value with the highest open-set accuracy; the chosen value
is published before the Book of Mormon is scored.**
This is the most consequential item in the amendment. The code currently defaults to `0.0`,
which means *no shrinkage* — nearest shrunken centroids running as plain nearest centroids. Our
own BOM-22 replicates Fields, Schaalje and Roper (2011), whose ENSC method is defined by that
shrinkage, so an unregistered zero would not be a tuning detail but a different method wearing
the same name. Cross-validated selection is how NSC's shrinkage is chosen in its own literature,
so the rule is registered rather than a number guessed in advance.

**ENSC `alpha` 0.05, priors proportional.** Matches the published method.

**Seeds — one root seed, `20261017`; every component seed derived from it by a documented
function and printed in the run log.**
`seed=0` currently sits in the imposters code. A single documented root makes every run
reproducible without scattering magic numbers.

## G. Time-locked and authorial language models

**Base model — 300M parameters, preceded by the 125M pilot, and the pilot is a registered
decision point: the Phase 3 benchmark is run at both sizes and both accuracies are published.**

300M is well supported rather than merely affordable. The method's own precedent — Huang,
Murakami and Grieve's authorial language models — used GPT-2, whose base size is 124M, so this
is about 2.4 times the published size. Against a corpus of roughly 15B tokens after dedup it
trains at about 50 tokens per parameter, well past Chinchilla's compute-optimal 20 and in line
with current practice, which routinely trains small models far longer than compute-optimal.

Bigger is not obviously better here, which is why the range is not being raised. The signal is
the *difference* in perplexity between fine-tuned candidate models, and a stronger base model
assigns more uniform probability to fluent text in general, which can compress the very
differences the method measures. Nobody has established the direction of that effect for this
task.

So the size is justified by measurement instead of assertion. Reporting benchmark accuracy at
125M and at 300M shows whether accuracy was still climbing with scale. If it has flattened,
300M was enough and the published numbers say so. If it is still rising steeply, that is
evidence for a further dated amendment to train larger — argued from a result rather than from
a preference. The pilot was already in the budget, so this costs nothing beyond publishing a
number we will have anyway.

**Tokenizer — byte-level BPE, vocabulary 32,000, trained on the 1780–1830 corpus only.**
A modern off-the-shelf tokenizer is itself trained on modern text, including the Book of Mormon.
Training the tokenizer on period text keeps the seal intact at every layer.

**Training — context length 1024, one pass over the deduplicated corpus, AdamW, cosine schedule,
peak learning rate 3e-4, warmup 2%.** Conventional for this scale; no claim to novelty.

**Fine-tuning — full fine-tune per candidate, 3 epochs, learning rate 1e-5, identical settings
and token budget for every candidate and control group.**
Identical settings across candidates is the part that matters: different budgets per author
would make the perplexity comparison meaningless.

## H. Dating

**`dating.classifier` — regularised multinomial logistic regression on the grammatical feature
set, with a transformer variant as a declared cross-check.**
The regression is interpretable: you can say which features moved an estimate, which a
transformer cannot. The transformer runs alongside so the choice is testable rather than
assumed.

**`dating.permutation.n` — 10,000.** Enough to resolve the registered p > 0.05 threshold without
being compute-bound.

**Grammatical feature list — fixed and committed before BOM-21**, built from the Early Modern
English features named in the literature (periphrastic *do*, relative pronoun choice, verb
inflection, negation, subjunctive) rather than selected on performance.

## I. Style embeddings

**`embeddings.model` — a content-disentangled style representation, adapted to the period corpus
by contrastive training on same-author/different-topic pairs; LUAR as the declared baseline.**
The STEB benchmark finding is directly relevant: embeddings retaining semantic signal win where
author and topic correlate, while content-disentangled ones win where topic shortcuts are
removed. Ours is the second case — every text in the comparison set is religious or
pseudo-biblical, so a topic-sensitive embedding would rediscover the genre, which is the exact
failure of the 1980 study in a modern costume.

## J. Borrowing

**`borrowing.normalization` — raw shared-n-gram counts divided by the geometric mean of the two
texts' token counts, then expressed as a percentile of the genre-matched null.**
Length normalisation stops long books dominating; the percentile against the null is what makes
"unusually similar" mean something. Without it we reproduce the 2013 result where Luke scores
higher than *The Late War*.

**`borrowing.semantic` — a sentence-embedding model over 256-word passages with 64-word stride.**
Long enough to carry an argument, short enough to localise a parallel.

## M. Blind run

**`blind.decoy_seed` — derived from the root seed `20261017` by the documented function; the
sealing script prints the derivation but not the key.**

---

## What this does not fix

Three values are deliberately left as rules rather than numbers, because fixing them now would
be guessing: ENSC shrinkage, the passim parameters, and the grammatical feature list. In each
case the selection procedure is registered, runs on benchmark data only, and the chosen value is
published before the Book of Mormon is touched.

If any of these rules turns out to be unworkable, that is a further dated amendment, not a quiet
edit.

---

## Before filing: the OSF token

**Owner action, one-time, on the Mac mini.** Claude can file the amendment through the OSF API
but has no credential: `~/.config/osf/token` does not exist. `CLAUDE.md` bars public or
irreversible acts *without asking*, which is a condition rather than a prohibition — the owner
has asked, so the only thing missing is the token.

1. https://osf.io/settings/tokens → Create token
2. Scope **`osf.full_write`** (read-only will not do), name it `bom-authorship-amendments`
3. Save it, mode 600:

   ```sh
   mkdir -p ~/.config/osf && chmod 700 ~/.config/osf
   printf '%s' 'PASTE_TOKEN_HERE' > ~/.config/osf/token && chmod 600 ~/.config/osf/token
   ```

   Or copy it to the clipboard and tell Claude, which writes it to the file without the token
   passing through the conversation.

Then say "file the amendment". Claude verifies the schema-response endpoints against
developer.osf.io, reads the registration's schema blocks, builds the revision payload, and
**shows the exact payload and endpoint before submitting**. Filing only happens on an explicit
go-ahead: this is public, permanent, attached to the owner's name, and a malformed amendment on
a scientific registration stays visible to anyone who later reads the paper.

## After filing

In order, once the amendment is public on OSF:

1. Add the dated entry to section 11 of `paper/preregistration.md`, with the OSF revision link.
2. Move each value from `pending_amendment` into the body of `config/preregistered.yaml`, each
   citing this amendment rather than a pre-registration section.
3. Extend `metadata/config.py`'s `PINNED` map with the newly registered values, so editing one
   fails loudly the same way the originals do.
4. Tick the amendment box on BOM-40 and note the OSF link in the issue.
5. Record the date in `paper/blog.md`.

Steps 1–5 are Claude's to do; only the filing itself is not. The three values registered as
rules rather than numbers stay in `pending_amendment` until their selection procedure runs on
benchmark data, at which point the chosen value is published and moved across.
