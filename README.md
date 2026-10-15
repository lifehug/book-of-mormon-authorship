# Book of Mormon Authorship

Who wrote the English text of the Book of Mormon, what earlier books does it echo, and
what era does its language belong to? This project tries to answer those three questions
with an open, pre-registered, reproducible computational study, built so that it can return
any answer, including "we can't tell."

The repository is the whole project: the plan, the code, the data manifests, the models, and
eventually the paper. Everything is public as it is produced.

## The three questions

1. **Attribution.** Does the text resemble the writing of any named candidate? The
   pre-registered list is Joseph Smith, Oliver Cowdery, Sidney Rigdon, Parley P. Pratt,
   W. W. Phelps, Solomon Spalding, Ethan Smith, and Gilbert Hunt. The test is open-set, so
   "none of the above" is always an allowed result. A corpus-wide search for stylistically
   similar authors runs alongside as an exploratory step; anyone it surfaces can be added to
   the list only by dated public amendment and then tested on data not used to find them.
2. **Borrowing.** Which earlier texts share wording or ideas with it, and is each overlap more
   than you would expect by chance from two books in the same genre and period?
3. **Dating.** When does its grammar and vocabulary come from? Some argue for early modern
   English features that had died out by 1830; others see 18th and 19th century imitation of
   the King James Bible.

## Why this is still open

People have run the numbers before, and each study was criticized on grounds the next one
didn't fully fix.

- **Larsen, Rencher and Layton (1980)** used function-word "wordprints" and found the book's
  internal narrators distinct from each other and from 19th-century candidates. Critics pointed
  out that biblical-register words like *unto*, *behold* and *yea* dominated the features. That
  is genre, not authorship.
- **Holmes (1992)** measured vocabulary richness and reached different conclusions.
- **Jockers, Witten and Criddle (2008)** used nearest shrunken centroids and pointed to Rigdon
  and Spalding. The method was closed-set (it had to pick someone from the list) and the list
  left out Joseph Smith.
- **Fields, Schaalje and Roper (2011)** extended that method to allow "nobody on the list" and
  got a different answer.
- **Johnson and Johnson (2013)** searched rare four-word phrases across about 110,000
  pre-1830 books and found *The Late War* (1816) as the closest match. The rebuttal: the same
  score rates the Gospel of Luke even higher, which means the method had no proper baseline
  for what "unusually similar" looks like.
- **Skousen and Carmack** catalog early modern English features in the text; **Shalev** places
  it in an American pseudo-biblical genre. Carmack's comparison set was four pseudo-biblical
  texts.

The pattern: small comparison sets, no baseline for chance, closed candidate lists, and
features that measure the biblical style rather than the person behind it. Every one of
these is a design problem, and design problems can be fixed in advance.

## What is different now

Three things are possible today that were not in 2013.

- **Corpus scale.** Harvard's Institutional Books release (983,004 public-domain volumes with
  cleaned OCR), plus HathiTrust, the Internet Archive, Chronicling America newspapers, and
  EEBO-TCP, make it realistic to compare against most of what was printed in English
  between 1780 and 1830, with a dated early modern English set for the dating question.
- **A language model that has never read the Book of Mormon.** Commercial models have
  memorized the Book of Mormon and the King James Bible, which contaminates any test based on
  how "surprised" a model is by the text. We will train a small model from scratch on
  1780-1830 text only, with the Book of Mormon held out, and then fine-tune one copy per
  candidate author. Attribution then becomes a measurable question: which author's model finds
  the text least surprising? This follows Huang, Murakami and Grieve's authorial language
  model work and the 2025 Dartmouth study that confirmed the authorship of the 15th Oz book
  the same way. As far as we can find, nobody has applied it to the Book of Mormon.
- **Semantic search.** Sentence embeddings over the whole corpus can find paraphrase and
  shared story structure, not just identical strings.

## How we intend to do it

The work is 39 issues in eight phases. Each issue has one deliverable and closes only when
that deliverable is published. The full backlog is in `docs/backlog.md` and mirrored as
GitHub issues `BOM-01` to `BOM-39`.

**Phase 0, Foundations.** Before touching any data, we write down the questions, the
methods, and the thresholds that will count as a match, a non-match, or inconclusive, and
register that plan on OSF with a timestamp. Then we write out the strongest objections a
sympathetic stylometrist, a critical historian, and a neutral computational linguist would
raise, answer them, and revise the plan with every change on record. That review is simulated,
not external, and is labeled as such; real objections are welcome by pull request. Any change after registration is a dated public amendment.

**Phase 1, Build the corpus.** Ingest the earliest Book of Mormon texts (original manuscript,
printer's manuscript, 1830 edition) from the Joseph Smith Papers, a period King James Bible,
the big book collections, period newspapers near Palmyra, the early modern English corpus,
and verified writing samples for each candidate author. Every source gets a manifest with
checksums. Reprints are deduplicated so one popular book doesn't count twenty times.

**Phase 2, Clean and prepare.** Fix OCR errors and measure how well we fixed them. Normalize
spelling. Align the Book of Mormon against the King James Bible and mask the quoted and
closely paraphrased spans, so later tests measure original composition. Segment the text by
narrator, by dictation order, and by scribe. Build genre-matched control sets, especially
other pseudo-biblical books, so biblical style can't masquerade as authorship. Freeze the
whole thing as corpus v1.0 with a DOI.

**Phase 3, Prove the tools work.** Implement the classical methods (Burrows' Delta, General
Imposters, extended nearest shrunken centroids) and run them on cases with known answers:
the Federalist Papers, pseudo-biblical texts with known authors, dictated texts, and
open-set cases where the true author is deliberately left out. Each method gets a pass or
fail against the pre-registered threshold. Then reproduce every prior Book of Mormon study
with its original method, so we know where we stand before adding anything new.

**Phase 4, Borrowing.** Run exact and near-exact reuse detection over the masked text against
the whole corpus. Score rare phrases against a real null distribution built from hundreds of
random period books, so we can say where Luke and *The Late War* actually fall. Run the
semantic search the same way. Have a model triage the hits and a human review every
"specific" one, and report how often they agree.

**Phase 5, New methods.** Train the time-locked language model, with a contamination check
that searches the training data for Book of Mormon strings. Fine-tune one model per
candidate and per control group. Build a dating classifier on dated text from 1473 to 1830
and test whether mere King James imitation shifts its estimate. Build style embeddings as an
independent cross-check. Build the corpus-wide author sweep: a book this long is rarely its
author's only writing, so we index every author in the 1780-1830 record to find the closest
matches, if any, and calibrate how close a false match can look by chance. Every model is
validated on the Phase 3 benchmark before it ever sees the Book of Mormon.

**Phase 6, Verification and synthesis.** Test whether a writer imitating biblical style can
fool each method, and down-weight the ones that are fooled. Then run the blind analysis: a
sealing script relabels the Book of Mormon segments, mixes in decoys from known authors, and
keeps the key outside the repository; the analysis runs in a fresh session that never sees
the key, and only after every output is saved and hashed do we unblind. The author sweep runs on a
pre-designated half of the segments and produces ranked leads; a lead can enter the candidate
list only by dated amendment, and is then tested on the other half. Add the historical evidence: what
books were available near Palmyra before 1829, and what the manuscript's dictation errors
and scribe changes show. Combine every line of evidence in a Bayesian model with sensitivity
analysis, and report where the methods agree and where they conflict.

**Phase 7, Publish.** Write the paper against the pre-registration, listing every deviation,
with the simulated reviewers' responses alongside. Post a preprint. Release code, data, and
models with a one-command reproduction, plus a web explorer where anyone can click a passage
and see its parallels, scores, and dating estimate. Then put the paper through a simulated
peer review by an AI model that sees only the released materials, and answer it in public.

## What this can and cannot settle

- Stylometry measures whoever produced the English text. It cannot decide the theological
  question of translation in either direction, and we will not claim that it does.
- Joseph Smith's undisputed pre-1830 writing is very small, and attribution gets unreliable
  below roughly 5,000 to 10,000 words. The pre-registration states this up front.
- Dictation and multiple scribes sit between any author and the page.
- Any method that fails the validation benchmark or the imitation test is down-weighted or
  dropped, whatever answer it would have given.

The design commits us to reporting nulls, conflicts, and "inconclusive" as readily as any
positive result. The analysis plan itself is `paper/preregistration.md`.

## Rules we have bound ourselves to

- **Pre-register first.** The analysis plan is frozen on OSF before analysis begins.
  Registration: https://osf.io/6ugxc/ (submitted 2026-10-15, public and frozen after OSF's
  48-hour approval window). OSF project: https://osf.io/ebpcw/.
- **Adversarial review, simulated.** The protocol is attacked from both sides in writing
  before results exist (`paper/adversarial-review.md`). No external scholar has approved it;
  the file says so and stays open to real dissent.
- **The text is sealed.** The Book of Mormon is excluded from all model training and tuning
  until the blind run in Phase 6. The one exception is the replication of prior studies, which
  uses their published methods.
- **Publish as you go.** Code here, data manifests and models on Hugging Face or Zenodo
  with DOIs.

## Who is doing this

One person with AI assistance. There are no external advisors, no second analyst, and no
journal submission. Every review step in the plan is simulated by an AI model and is labeled
as such wherever it appears. That is a real limit on the independence of the review, and the
project states it rather than implying otherwise. Anyone who wants to supply the missing
independent scrutiny can do so by pull request, and their critique will be recorded unchanged.

## Following along

Watch the issues. Each one is titled `BOM-NN`, labeled by phase, and closes with a link to
its published output. Issues #1 to #10 are from the repository's 2016 incarnation and are
closed. `docs/background.md` has the prior studies, sources, and limits in more detail.

## Repository layout

Each top-level package owns one stage of the pipeline and its README names the issues it
serves: `ingest/`, `metadata/`, `ocr_fix/`, `kjv_mask/`, `segment/`, `classic/`,
`reuse/`, `semantic/`, `timelocked_lm/`, `alm/`, `dating/`, `style_embed/`, `eval/`, `paper/`.

- `data/` holds raw and derived data (gitignored). Only checksum manifests under
  `data/manifests/` are tracked. See `docs/data-versioning.md`.
- `docs/` holds the backlog, background, and design notes.
- `scripts/` holds one-off tooling such as the backlog importer.
- `tests/` holds the test suite.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

CI runs the same three checks on every push and pull request.

## License

Code: MIT (`LICENSE`). Derived data: CC BY 4.0 (`LICENSE-DATA`). Source texts keep their
original licenses.

## History

This repository began in 2016 as a Java frequency-analysis experiment on the 1830 text and
Joseph Smith's journals (David Taylor and John McConnell). That code is in the git history
before the October 2026 reset and is not used by the current project.
