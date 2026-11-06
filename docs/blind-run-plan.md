# The blind run (BOM-32)

Pre-registration section 8 (amended by Amendment 1: a sealing script instead of a second person;
a fresh session without the key) and the open points fixed by draft Amendment 32
(`paper/amendment-032-osf-text.md`, not yet filed). Code: `blind/`. Written 2026-11-06, before
anything is sealed or scored.

## What is registered already

- A sealing script relabels the Book of Mormon segments with opaque ids and mixes in decoys from
  known candidates and controls, **at least 1 decoy per 4 segments**; it writes the key outside the
  repository and commits the SHA-256 of the key and of the relabeled set (8).
- The analysis runs in a fresh session with no access to the key; every method runs on the mixed
  set; outputs are saved and their hashes committed before the key is revealed (8).
- Decoys must be identified at the benchmark accuracy, or the run is repeated with the fault
  documented (8). Leave-one-candidate-out runs follow (8).
- The author sweep uses the discovery half only (4.5, 6.6); confirmatory methods report on each
  half and the whole (4.5); a candidate is supported only if two method families match on both
  halves (6.2).
- `config/multiverse.yaml` and its SHA-256 are committed before the blind run (BOM-40); the
  multiverse runs inside the blind session after the registered run, its outputs hashed with the
  rest (backlog, BOM-32).

## Procedure

1. **Before sealing.** All of BOM-26 to BOM-31 and BOM-39 closed; the 6.1 thresholds of every
   method that passes, the multiverse file and the sweep calibration committed. Amendment 32 filed;
   the `blind:` config block added.
2. **Seal** (`python -m blind.seal`). Takes the whole chunks of the registered schemes and sizes,
   draws the decoys (seeded, `blind.seal_seed`), gives every item a random 16-hex id, shuffles.
   Writes the key to `~/.bom-blind/key.json` (directory 700, file 600; refused inside the repo),
   the sealed set (id, words, text) to `data/corpus/blind/sealed.jsonl` (not in git: licensed
   and copyrighted text), and commits `data/blind/seal.json` (hashes, counts, seed, config hash;
   no mapping) and `data/blind/withheld.json` (the decoys' source spans, which every method must
   leave out of its references, so a decoy is never scored against its own words; it names spans,
   not ids). Commit and push before anything else.
3. **Run** (`python -m blind.run`, all three model sizes by default) in a fresh session. Every
   method scores every sealed id; the authorial models once per size (pilot 125M, base 297M,
   large 1B: every size runs every test, owner 2026-11-06, Amendment 37), as `alm_<size>.json`,
   side by side; outputs (numbers only) go to `data/blind/outputs/`, large arrays to
   `data/corpus/blind/`; every file's SHA-256 to `data/blind/outputs.json`. Then the multiverse
   (`python -m eval.multiverse`, inside the same session). Commit and push the outputs and hashes.
   `run.py` never opens the key (a test checks its source).
4. **Unblind** (`python -m blind.unblind`). Refuses unless `seal.json` and `outputs.json` are
   committed and unchanged and every hash matches; then applies the key: decoy accuracy per method
   against its benchmark accuracy, per-chunk results for the Book of Mormon by half and whole, the
   sweep's discovery-half mean distances, leads and the expected false-lead count beside them, and
   leave-one-candidate-out for every method that scores candidates. Writes
   `data/blind/unblinded.json`.

   Each scorer's records are keyed by candidate unit; unblinding reads them through one *view* per
   statistic (`blind.unblind.VIEWS`): Burrows and Cosine Delta, General Imposters (with 6.1's
   call) and ENSC from the classical output; cosine distance with the call from the style
   embeddings; the margin over the best control model with the call from each size's authorial
   models. A candidate's score is its best unit's (BOM-28's plan maps units to candidates; control
   models never stand for a candidate), its call that unit's call, as the synthesis reads them.
   Decoy accuracy is reported two ways: **closed set** (candidate decoys, first pick correct) and,
   for methods with 6.1's call, **verification** (a candidate decoy needs *match* for its candidate
   and no other; a control decoy needs no *match* at all: Amendment 32's "no candidate"). The raw
   Book of Mormon records stay by chunk for `synth.model`. `tests/test_blind_e2e.py` runs seal,
   scorer-format outputs, unblinding and the synthesis end to end on synthetic data.

## The fresh session (honest label)

The project is one person and AI, so "an analyst without the key" is simulated: the run step is
given to a new agent session started with only the repository, an instruction that names
`blind/run.py` as its whole task, and the statement that the key exists at a path it must not
read. The key lives outside the repository (mode 600), `run.py` never references it, and its hash
is committed before the run, so any later change to it shows. What this cannot guarantee is that
the session could not have read the file; that limit is stated in section 10 with Amendment 1's.

## Decoys

- **Ratio:** at least 1 per 4 Book of Mormon chunks, per chunk size, rounded up.
- **From candidates** (half, rounded up): Ethan Smith, Gilbert J. Hunt, Oliver Cowdery, Sidney
  Rigdon, Parley P. Pratt, W. W. Phelps, Solomon Spalding, from the public candidate texts
  (`data/candidates/clean/`) with their KJV masks. Each candidate keeps at least 10,000 masked
  words out of the decoys (the reliable-sample floor), so their references survive. Joseph Smith's
  samples are too small to spare (all under or near 10,000 words) and give no decoys.
- **From controls** (the rest): authors of the pseudo-biblical, history and general-prose control
  sets, KJV-masked.
- **Only from text no authorial model trained on** (Amendment 33, draft). A candidate decoy is
  drawn only from its unit's held-out tail in BOM-28's plan (`data/benchmark/alm_candidates_plan.json`,
  the words from `holdout.first_word` on, mapped onto the unit's documents in the plan's order:
  `blind.seal.untrained`); a unit with no held-out tail gives none. A control decoy is drawn only
  from a volume no control model sampled (`blind.seal.trained_volumes`). Candidate texts are
  grouped by the plan's units, not by file name (`blind.seal.by_unit`): a *Messenger and Advocate*
  article is filed by issue, and the writer is whoever the unit says. Checked on the real plan,
  without Book of Mormon text: untrained candidate words are Ethan Smith 70,391, Hunt 14,956,
  Spalding 11,833, Cowdery 11,338, Phelps 7,479, Rigdon 6,516, Pratt 0 (his tail lies outside
  the public texts); the 22 candidate decoys (16 of 2,000 words, 6 of 5,000) all place.
- **"Identified"** means: a candidate decoy attributed to its candidate (closed set) and matched at
  6.1's threshold; a control decoy given "no candidate" (open set), and for the sweep its author
  ranked first where swept. Accuracy is compared with each method's benchmark accuracy.

## What is sealed: the open question

Section 8 says "the Book of Mormon segments". The segmentation has 756 chunks (three schemes, two
sizes, 120 of them partial). At 1:4 over all of them that is 189 decoys, about 580,000 words, half
from candidates whose public texts total about 600,000 words (Ethan Smith alone half of it): Hunt,
Rigdon, Phelps and Spalding could give only a few decoys each before falling under the 10,000-word
floor. Amendment 32 therefore seals the **narrator scheme's whole chunks at both sizes** (121 of
2,000 words and 47 of 5,000 words; 31 + 12 = 43 decoys), which are what the attribution, dating
and sweep results are reported on. The dictation-order and scribe schemes serve only H1c, an
internal comparison with no candidate to bias toward, and are scored after unblinding with the same
frozen code. This needs the owner's agreement before it is filed.

## What each method needs before the run (gaps)

| Method | Scorer for sealed ids | State |
| --- | --- | --- |
| Classical (BOM-20/21) | per id: Burrows and Cosine Delta distances and ranking, GI per unit with 6.1's call, ENSC label and posteriors; references Amendment 30's units with withheld spans cut, pool the pseudo-biblical task's less candidates' works and withheld volumes | written (`classic.blind_score`) |
| Authorial models (BOM-28) | per id: every unit model's score, closed set, each candidate's margin over the best control model with 6.1's call | written (`alm.blind_score`); needs the trained weights and `blind.thresholds` |
| Style embeddings (BOM-30) | per id: cosine to each unit's profile, GI on the vectors with 6.1's call | written (`style_embed.blind_score`) |
| Dating (BOM-29) | per id: median and 90% interval per segment, grammar (decides H3), lexical, transformer | written (`blind.run.dating`) |
| Author sweep (BOM-39) | per id: distance to every swept author, both signals; discovery mean after unblinding | written (`blind.run.sweep`), needs BOM-39's index |
| Multiverse (BOM-40) | the registered ranges re-run inside the session | `config/multiverse.yaml` committed (BOM-40 closed); its stages are benchmark-only today |

6.1's thresholds come from `python -m blind.thresholds` (benchmark data only:
GI from `thresholds.json`, style from `style_embed.json`, ALM margins from the candidates' held-out
windows at each size, `alm_candidates_<size>.json`), committed before the run. Draft Amendment 33 records the scorers' unregistered choices.

## Every size, side by side (owner, 2026-11-06; Amendment 37)

Every model size runs every model-based test and the sizes are reported side by side; none is
the "working" or headline size. In the blind run that means the candidate and control models of
all three sizes (`alm.candidates train pilot|base|large`: the 125M on the Mac GPU, the 297M and 1B
on rented H100s) each score the sealed set, each with its own 6.1 thresholds, and the unblinded
results carry `alm_pilot`, `alm_base` and `alm_large`. The style embeddings, dating's transformer
cross-check and the sweep use the single model each was registered with, so they run once.

## Cost

Sealing: minutes. The run, once the scorers exist: dating about 30 minutes on the Mac GPU (the
transformer at about 0.55 s a segment); the sweep about 15 minutes; classical methods about an
hour on the CPU (GI's 100 trials per candidate per id); authorial models one to two hours on an
H100 (every candidate and control model over every id). Unblinding: minutes.
