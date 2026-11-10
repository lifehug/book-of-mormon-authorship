# Paper outline, version 2 (owner and Claude, 2026-11-10)

Principles: report every model and method objectively, side by side, then say which is best at
what (judged on known answers, never on the Book of Mormon); no averaging across methods; prior
methods are baselines, not votes; every post hoc step labelled; no position on the book's origin
or on inspiration. Each test is preceded by how it was prepared.

## 1. Introduction
The question (who, what was borrowed, when), why two centuries of argument and four decades of
computer studies disagree, and what is different here.

## 2. The scale and preparation of the test
- **2.0 At a glance:** comparison table against every prior study (corpus size, candidates,
  controls, blind or not, "none of these" allowed or not, error rates measured or not).
- **2.1 Gathering:** 695,021 items catalogued 1780-1830 from five sources (Internet Archive
  307,567; HathiTrust 135,035; Harvard Institutional Books 31,958, released 2025 and new to this
  question; Chronicling America 159,146 newspaper pages) and 61,315 early-modern texts (1473-1700)
  for dating; 1.1 TB; what can and cannot be redistributed.
- **2.2 Cleaning:** date audit, duplicate detection (MinHash), OCR quality measured.
- **2.3 Labelling:** a genre label for every item, and its validation.
- **2.4 Sealing and masking:** the text kept away from every model; King James masking (6.8% of
  the text; 1.55 billion words of controls); the quotation rule for candidate samples (Amendment 43).
- **2.5 Segmentation:** narrator, dictation order, scribe; discovery and confirmation halves.
- **2.6 Candidate samples:** eight candidates, provenance tiers, the Joseph Smith Papers
  manuscripts, sample sizes and their limits.
- **2.7 Controls and the benchmark:** four control groups; known-author tasks.
- **2.8 The time-locked language models:** 202,816 volumes, 25.7 billion tokens, three sizes, the
  1B failure and the 590M with QK-norm; all published.

## 3. Prior work, replicated
Five published studies rerun with their own methods: what reproduces, and their limits (forced
choice, register mistaken for style, answers that follow the texts chosen).

## 4. Measuring every method on known answers
Two questions, reported per method and model: **ranking** ("who is closest?") and **matching**
("is it confidently this person?"). Prior methods beside ours; GPT-2 against period-trained
models (false matches 86-92% to 22%); imitation robustness; unstable variants (V1, V2). "Best at":
ranking, the 297M (99%); matching with fewest false matches, the 590M (22%); confirming true
authors, the 125M (91%, at 47% false matches).

## 5. The tests on the Book of Mormon (each with its preparation first)
- 5.1 The blind procedure and its decoys.
- 5.2 **Wording:** exact reuse; rare phrases against 204,520 volumes; paraphrase across 163
  million passages; triage of every surfaced pair (biblical, common, specific).
- 5.3 **Story structure:** the text's 1,421 events in order against every named source and the 20
  leading sources; the positive control (Josephus retelling Genesis-Judges: 108 events in order,
  p 0.001); no source shares the text's order at the registered level.
- 5.4 **Authorship:** ranking and matching by our models, style encoders, classical baselines; the
  23,872-author sweep (descriptive).
- 5.5 **Dating:** three models; H3b; H3c by chunk and by book.
- 5.6 **Internal voices:** narrators, dictation order, scribe.

## 6. Corrections and robustness
The quotation leak found and fixed (Amendment 43); equal training dose (Amendment 45); the
registered combined score and the placebo showing it cannot distinguish an author's own text; every
post hoc decision in one table.

## 7. The books in the CES Letter, one by one
For each book the CES Letter names (to be confirmed from the Letter: *View of the Hebrews*, *The
Late War*, *The First Book of Napoleon*, Spalding's *Manuscript Story*, and any others it cites):
what the claim is; every wording test with each shared phrase listed and triaged; story structure;
the book's own dating; access evidence (who could have had it, where, when); the verdict under the
claim's pre-written rule.

## 8. Public claims
Seventeen claims, from every side, judged by rules written before any result.

## 9. What held
Ranking is the models' strength, matching their weakness. If the author is one of the candidates,
the strongest ranking points to Joseph Smith; whether the author is one of them, the tools cannot
settle. No copied passage or plot; rare-phrase overlap genre-wide; language earlier than its
period and than period imitations.

## 10. The people, one by one
For each candidate: samples; rankings; "match" calls (pre- and post-1830, every model); context
(borrowing links, access, public claims); caveats.
- **10.1 Joseph Smith:** revelations rank first, also at equal training dose; a same-sized slice of
  *The Late War* competes (register); his ordinary prose mid-pack, never matched; dictation; and
  **his prose over time** (BOM-73): his line 1831-44 against the exposed writers' and the
  unexposed controls', with what it can and cannot show (no pre-1830 baseline).
- 10.2 Oliver Cowdery (the quotation leak; post-1830 sample, never matched), 10.3 Sidney Rigdon,
  10.4 Solomon Spalding, 10.5 Ethan Smith, 10.6 Gilbert J. Hunt, 10.7 Parley P. Pratt, 10.8 W. W.
  Phelps.

## 11. Limitations

## 12. Everything is public
Data tables, every model (Hugging Face), code, the pre-registration and every amendment, the
simulated reviews and responses; how to obtain the licensed sources.
