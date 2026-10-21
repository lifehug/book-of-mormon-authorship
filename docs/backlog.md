<!-- Source of truth for the work plan. Issue numbers here (#N) map to GitHub issues titled BOM-NN. -->
# Issue Backlog (exported from the planning doc)

## How to use this backlog

The project is finished when all 39 issues below are closed, in dependency order, with their outputs published. Each `###` heading is one issue. Numbers are stable IDs: #1-#38 were numbered so dependencies point backwards, and issues added later (#39 onward) keep their number and state where they sit in the sequence.

Every issue has the same four parts:

- **Goal:** the one outcome the issue delivers.
- **Tasks:** checkboxes to tick as you go.
- **Done when:** the test that closes the issue, usually a published artifact (code, dataset, model, report).
- **Depends on:** issues that must be closed first.

To load these into GitHub, split this section on `### ` headings, and create one issue per chunk with `gh issue create --title ... --body ... --label phase-N`. Use the phase number as the label and one GitHub milestone per phase.

Ground rules for every issue:

- Publish as you go: code to the repo, data manifests and models to Hugging Face or Zenodo with a DOI.
- Never change the pre-registered analysis plan (issue #2) without a dated, public amendment.
- The Book of Mormon text stays sealed from all model training and tuning until Phase 6, except where an issue says otherwise.

## Phase 0 — Foundations

Phase 0 locks the questions and the method before any data is touched, so neither side can say the result was steered.

### #1 Set up the repository and project structure

**Goal:** a public repo with the skeleton every later issue plugs into.

- [ ] Use the original 2016 repo, lifehug/book-of-mormon-1830-frequency-analysis, as the project's home: clear out its old contents and start fresh, with MIT for code and CC-BY for derived data
- [ ] Create folders: `ingest/`, `metadata/`, `ocr_fix/`, `kjv_mask/`, `segment/`, `classic/`, `reuse/`, `semantic/`, `timelocked_lm/`, `alm/`, `dating/`, `style_embed/`, `eval/`, `paper/`
- [ ] Set up Python environment (uv or poetry), linting, tests, and CI
- [ ] Add a data-versioning approach (DVC or manifests with checksums)
- [ ] Create phase labels and milestones; import this backlog as issues

**Done when:** CI passes on an empty skeleton and all 38 issues exist in GitHub.
**Depends on:** none.

### #2 Write and publish the pre-registration

**Goal:** a timestamped analysis plan that fixes questions, methods, and decision thresholds in advance.

- [ ] State the three questions: Q1 attribution (open-set), Q2 textual borrowing, Q3 linguistic dating
- [ ] List candidate authors and control groups, plus the rule for adding new ones later
- [ ] State the purpose of the author sweep (#39): a book this long is rarely its author's only writing, so the sweep checks whether anyone in the 1780-1830 record matches. Say what each outcome means: a strong, historically plausible match is a lead; no match means no author in the corpus resembles the text, which is reported as-is and not interpreted further
- [ ] Define the candidate promotion rule: the sweep runs only on a pre-designated discovery half of the Book of Mormon segments; a lead that beats the null threshold and has historical plausibility is added by dated public amendment and then tested with the confirmatory methods on the other half only
- [ ] Define each method, its features, and what result counts as a match, a non-match, or inconclusive
- [ ] Define the validation benchmark the methods must pass before the Book of Mormon is run
- [ ] State known limits: dictation, scribes, small Joseph Smith sample
- [ ] Register on OSF (osf.io) and link from the README

**Done when:** the OSF registration is public and frozen.
**Depends on:** #1.

### #3 Simulated adversarial review of the protocol

**Goal:** the strongest objections a sympathetic stylometrist, a critical historian, and a neutral computational linguist would raise, written out and answered before results exist.

Decision 2026-10-15: the owner is not recruiting external advisors. The review is simulated and labeled as such everywhere it is cited. Real reviewers remain welcome by pull request.

- [ ] Write each simulated reviewer's objections against the draft pre-registration, as strongly as possible
- [ ] Answer each objection and revise #2, logging every change
- [ ] Label the review as simulated in the review file, the README, and the pre-registration
- [ ] Keep the file open for real objections and dissent by pull request

**Done when:** `paper/adversarial-review.md` is in the repo with objections, responses, and the resulting changes, clearly labeled as simulated.
**Depends on:** #2 draft (finalize #2 after this issue).

### #4 Set the compute and budget plan

**Goal:** a known cost and set of accounts so nothing stalls mid-project.

- [ ] Estimate storage for raw and cleaned corpora
- [ ] Estimate GPU hours for #27 (time-locked model) and #28 (authorial models)
- [ ] Open accounts: Hugging Face, a GPU cloud, Zenodo, OSF
- [ ] Request HathiTrust Research Center access if needed

**Done when:** a budget table and active accounts are documented in the repo.
**Depends on:** #1.

## Phase 1 — Build the corpus

Phase 1 collects every usable English text from 1780-1830, plus the Book of Mormon base texts and an early modern comparison set. Each ingest issue outputs a manifest (ID, title, author, date, source URL, checksum) and raw text.

### #5 Ingest the Book of Mormon base texts

**Goal:** clean, verse-aligned digital copies of the earliest texts.

- [ ] Pull transcriptions of the original manuscript, printer's manuscript, and 1830 edition from the Joseph Smith Papers
- [ ] Record which portions of the original manuscript survive and use the printer's manuscript for the gaps
- [ ] Align all three at the verse/paragraph level
- [ ] Store scribe attribution per passage where known

**Done when:** `data/bom/` holds three aligned texts with a manifest and a diff report.
**Depends on:** #1.

### #6 Ingest the KJV and other biblical baselines

**Goal:** the exact Bible text that would have been in Smith's hands.

- [ ] Pull an early 19th-century American printing of the KJV, including the Apocrypha
- [ ] Store it verse-indexed for alignment in #16

**Done when:** a verse-indexed KJV with manifest is committed.
**Depends on:** #1.

### #7 Ingest Harvard Institutional Books 1.0

**Goal:** the largest clean public-domain book source, filtered to the period.

- [ ] Download the dataset from the Institutional Data Initiative's Hugging Face release
- [ ] Filter to English volumes dated 1780-1830 and keep OCR quality scores
- [ ] Write the manifest and raw text

**Done when:** filtered volumes and manifest are stored, with counts by year.
**Depends on:** #4.

### #8 Ingest HathiTrust public-domain volumes

**Goal:** fill gaps not covered by Harvard's collection.

- [ ] Query HathiTrust for English, public domain, 1780-1830
- [ ] Pull full text through the Research Center or Extracted Features where full text is restricted
- [ ] Write the manifest

**Done when:** manifest and text stored, with overlap against #7 measured.
**Depends on:** #4.

### #9 Ingest Internet Archive texts

**Goal:** capture American imprints and pamphlets missing from #7 and #8.

- [ ] Use the Internet Archive API to search by date range and language
- [ ] Download OCR text and metadata, respecting rate limits

**Done when:** manifest and text stored.
**Depends on:** #4.

### #10 Ingest Chronicling America newspapers

**Goal:** period newspaper prose, especially New York, Pennsylvania, and Ohio papers.

- [ ] Pull OCR text via the Library of Congress API for 1800-1830
- [ ] Prioritize papers circulating near Palmyra and Manchester, NY (for example the *Wayne Sentinel*)
- [ ] Split pages into articles where feasible

**Done when:** article-level text with manifest is stored.
**Depends on:** #4.

### #11 Ingest the early modern English corpus (EEBO-TCP)

**Goal:** a dated 1473-1700 comparison set for the dating classifier.

- [ ] Download EEBO-TCP Phase I and II public texts
- [ ] Keep dates and genre metadata

**Done when:** EEBO-TCP texts and manifest are stored.
**Depends on:** #4.

### #12 Normalize metadata and deduplicate

**Goal:** one record per work, so reprints don't inflate counts.

- [ ] Read `corpus.dedup` (method, shingle, threshold, keep) from `config/preregistered.yaml` via `metadata.config.load()`; stamp outputs with `sha256_of_config()`. `corpus.language_filter` is unregistered: use `pending_amendment`, do not invent a value (BOM-40)
- [ ] Merge manifests from #7-#11 into one catalog
- [ ] Normalize author names and dates
- [ ] Detect duplicate editions with MinHash or similar, keeping the earliest
- [ ] Tag genre (sermon, history, fiction, periodical, pseudo-biblical, other)
- [ ] Aggregate word counts per normalized author across all their works, so the author sweep (#39) has author-level units with known sample sizes

**Done when:** `catalog.parquet` exists with a dedup report.
**Depends on:** #7-#11.

### #13 Assemble the candidate author corpora

**Goal:** verified writing samples for each named candidate.

- [ ] Joseph Smith: pre-1830 letters, 1832 history, early revelations, with dictated and handwritten texts flagged separately
- [ ] Oliver Cowdery, Sidney Rigdon, Parley P. Pratt, W. W. Phelps
- [ ] Solomon Spalding's *Manuscript Story* (Oberlin)
- [ ] Ethan Smith (*View of the Hebrews*) and Gilbert Hunt (*The Late War*)
- [ ] Record word count per author and flag any below 10,000 words

**Done when:** a candidate table with sources and word counts is published.
**Depends on:** #12.

## Phase 2 — Clean and prepare the text

Phase 2 turns raw OCR into analysis-ready text and ends with a frozen, citable corpus release.

### #14 Clean OCR and score quality

**Goal:** readable text with a measured error rate per volume.

- [ ] Read `corpus.ocr_max_cer` (0.10) from `config/preregistered.yaml` via `metadata.config.load()`; stamp outputs with `sha256_of_config()`. Do not hard-code the cutoff (BOM-40)
- [ ] Fix the long 'ſ' misread as 'f', rejoin end-of-line hyphens, strip running headers and page numbers
- [ ] Use an LLM to correct OCR on a sample, and measure its error rate against hand-corrected pages
- [ ] Score each volume and set a minimum quality cutoff in the pre-registration

**Done when:** cleaned text plus a quality score per volume, with the measured correction accuracy published.
**Depends on:** #12.

### #15 Normalize spelling and orthography

**Goal:** consistent tokens across 1500-1830 spelling variation.

- [ ] `corpus.spelling_normalization` is unregistered. Pin the method and variant map by dated amendment before using it, then read it from `config/preregistered.yaml`; it is listed in `pending_amendment` until then (BOM-40)
- [ ] Build a variant-spelling map (for example VARD-style normalization)
- [ ] Keep both original and normalized versions so features can use either

**Done when:** normalized text exists alongside originals, with the mapping table published.
**Depends on:** #14.

### #16 Align and mask KJV quotations

**Goal:** separate biblical quotation from original composition in the Book of Mormon and in every control text.

- [ ] Read `kjv_mask.verbatim` and `kjv_mask.paraphrase` thresholds from `config/preregistered.yaml` via `metadata.config.load()`; stamp outputs with `sha256_of_config()`. `kjv_mask.edition` and the passim parameters are unregistered and sit in `pending_amendment` (BOM-40)
- [ ] Align Book of Mormon text against the KJV from #6 using passim or local alignment
- [ ] Tag spans as verbatim quote, close paraphrase, or original
- [ ] Apply the same masking to candidate and control texts

**Done when:** masked versions exist and a report gives the percentage of Book of Mormon text removed.
**Depends on:** #5, #6, #15.

### #17 Segment the Book of Mormon

**Goal:** analysis units that can test internal-narrator and dictation-order hypotheses.

- [ ] Read `segmentation.ways`, `chunk_words` and `split.stratify_by` from `config/preregistered.yaml` via `metadata.config.load()`; stamp outputs with `sha256_of_config()`. The split **seed** and the boundary file are unregistered and sit in `pending_amendment`: pin the seed by dated amendment before any split is drawn, or the split is unreproducible (BOM-40)
- [ ] Segment by internal narrator (Nephi, Jacob, Mormon, Moroni, and so on)
- [ ] Segment by dictation order and by scribe
- [ ] Produce fixed-length chunks (for example 2,000 and 5,000 words) for each scheme

**Done when:** segment files and a segment table are published.
**Depends on:** #16.

### #18 Build the control sets

**Goal:** genre-matched comparison groups so style isn't confused with genre.

- [ ] Pseudo-biblical texts (Leacock, Snowden, Linning, Hunt, plus every other example found in the catalog)
- [ ] Sermons and religious tracts from the 1820s
- [ ] Histories and Native American origin texts
- [ ] General prose baseline (fiction and periodicals)

**Done when:** each control set is listed with size and sources.
**Depends on:** #12, #15.

### #19 Freeze and publish corpus v1.0

**Goal:** a citable snapshot everything later is run against.

- [ ] Freeze catalog, cleaned text, masks, segments, candidate and control sets
- [ ] Publish manifests and derived data on Zenodo with a DOI, linking to sources rather than re-hosting where licenses require
- [ ] Write a datasheet describing coverage and known gaps

**Done when:** the DOI is live and referenced in the README.
**Depends on:** #13-#18.

## Phase 3 — Classical stylometry and validation

Phase 3 proves the toolkit works on known answers and reproduces earlier studies before it touches the questioned text.

### #20 Build the classical stylometry library

**Goal:** tested implementations of the standard methods in `classic/`.

- [ ] Feature extraction: most-frequent words, function words, character n-grams, POS n-grams
- [ ] Burrows' Delta and its variants (Cosine Delta, Eder's Delta)
- [ ] General Imposters method for open-set verification
- [ ] Extended nearest shrunken centroid (ENSC) to match Fields et al. (2011)
- [ ] Unit tests on toy data

**Done when:** all methods pass tests and run on the frozen corpus.
**Depends on:** #19.

### #43 Power analysis: which candidates can actually be tested

**Goal:** know before the analytical build-out which candidates have enough text for each method to say anything, and say so in advance rather than discovering it at #21.

Section 10 already concedes Joseph Smith will likely fall under the sample floor. Measuring the accuracy-vs-sample-size curve uses known authors only and breaks no seal.

- [ ] Sample-size curve per method on the Federalist papers and held-out pseudo-biblical texts, at 1k/2k/5k/10k/20k masked words
- [ ] Publish candidate x method x testable / unreliable / untestable, using #13's word counts
- [ ] Put the minimum detectable sample per method in the config, so #21 confirms rather than discovers it
- [ ] Record any all-method-untestable candidate as a pre-registered expectation now
- [ ] Report a floor per method, not one number: 6.2 needs two agreeing families, so a candidate must clear two floors to be concludable
- [ ] Apply the curve to the Book of Mormon side too: if 2,000 words is below a method's floor, #17's 2,000-word runs are exploratory for that method
- [ ] Measure floors on masked word counts, not raw — 4.4 strips KJV spans, and the early revelations are heavily KJV-inflected

**Done when:** the table is published and the expectation is on the record before #21.
**Depends on:** #13. **Gates:** #21.

### #44 Publish derived artifacts so the pipeline replicates without the licensed corpus

**Goal:** an outsider can re-run most of the analysis without holding the corpus.

Harvard, HathiTrust and the Joseph Smith Papers all forbid redistribution, so nobody can rebuild this corpus from this repository. Derived artifacts are not reconstructable back to source text, which is what the licences restrict.

- [ ] Check each source's terms individually and record what derived form may be redistributed — the gating step, not yet examined
- [ ] Publish 4-gram document-frequency tables, feature matrices, the genre catalog, OCR scores, the dedup graph
- [ ] Verify and document non-reconstructability
- [ ] Amend the pre-registration's known limits to state what a replicator can and cannot reproduce

**Done when:** a replicator without a HathiTrust or Harvard agreement reproduces the 5.5/6.5 results and the classical features.
**Depends on:** #19.

### #45 Size the borrowing null properly

**Goal:** a 99th-percentile threshold that is not dominated by its own sampling noise.

6.5 says "at least 500" volumes; a 99th percentile from 500 draws rests on about five tail observations. The floor permits more, so this is a config decision, not an amendment.

- [ ] Estimate the sampling variance of the 99th percentile against n, on real scores
- [ ] Choose n from that curve (expected range 5,000-10,000) and add `borrowing.null_sample` to `pending_amendment`
- [ ] Publish the threshold's confidence interval beside it

**Done when:** the null is built at the chosen n and the choice is recorded.
**Depends on:** #12, #18. **Part of:** #24.

### #46 Imitation weights: check the dual-register author sample

**Goal:** method weights that are not set by four measurements.

Section 9 weights each method by its accuracy on imitation-biblical samples, in bands at 80% and 60%. If Leacock, Snowden, Linning and Hunt are the whole dual-register population, the bands cannot be told from noise — and these weights feed 6.7.

- [ ] Count dual-register authors actually available after #18's search
- [ ] Report section 9 accuracies with confidence intervals if the count is small
- [ ] Register an equal-weight sensitivity run of 6.7 alongside the section 9 weights

**Done when:** the count is published and either the bands are justified at that n or the sensitivity is registered.
**Depends on:** #18. **Feeds:** #31, #35.

### #47 State the sweep's expected false-lead count before running it

**Goal:** nobody mistakes a pile of leads for a finding, including us.

6.6 gates leads at the 95th percentile under both signals. Partly independent signals imply on the order of 0.25% of swept authors — hundreds of leads. That is what a sweep is for; the flaw is not writing the number down first.

- [ ] Measure the correlation between the embedding and classical signals on #39's 200 calibration books; do not assume independence
- [ ] Publish the expected false-lead count before the sweep runs, and what count would be surprising
- [ ] Report observed leads against that expectation, and how many survived the section 3 gate versus how many were expected to by chance

**Done when:** the expectation is committed before the sweep runs and results are reported against it.
**Depends on:** #30, #39. **Gates:** the sweep run in #39.

### #48 Time-split validation: is authorial signal stable across the 1830 gap

**Goal:** measure per candidate whether a profile built from later writing attributes earlier writing — the assumption any expanded corpus rests on.

Known authors only; no Book of Mormon text, no seal broken. Produces a per-candidate reliability number the plan does not currently have, useful whether or not #49 happens.

- [ ] Profile from post-1830, attribute pre-1830, for every candidate with text on both sides
- [ ] Run the reverse direction too and report both; they are not the same test
- [ ] Baseline the normal amount of temporal drift on corpus authors spanning a comparable gap
- [ ] Publish accuracy per candidate per method against the section 7 floor, whether or not it supports using later text

**Done when:** the table is published with the drift baseline beside it.
**Depends on:** #13, #20. **Gates:** #49.

### #49 Expanded candidate corpora as a registered secondary analysis

**Goal:** use each candidate's larger later corpus where it carries information, in addition to the pre-registered primary and never in place of it.

Section 3's corpora and section 6's rules are unchanged and stay confirmatory. Needs Amendment 5 (`paper/amendment-005-osf-text.md`), filed before any calibration. **Owner action: not yet filed.**

- [ ] Publish exposure tiers from the historical record: no later writing (Spalding), exposed (Joseph Smith, Cowdery, Rigdon, Pratt, Phelps), unexposed (Ethan Smith, Hunt, corpus authors)
- [ ] Exposed candidates get the one-directional rule: non-match is evidence, match is uninformative
- [ ] Tier every later sample by provenance; admit only holograph and dictated into attribution, catalogue and exclude reported speech and material composed by others
- [ ] Gate on #48: no expansion for a candidate whose signal is not stable across the gap, and publish the refusals
- [ ] Cap sweep-lead expansions at ten, in rank order among leads passing section 3's plausibility rule; the confirmation-half rule still applies
- [ ] Publish the total count of candidate x method combinations, primary and secondary separately

**Done when:** Amendment 5 is filed and the secondary analysis is reported in its own section beside the unchanged primary.
**Depends on:** #43, #48. **Related:** #39, #47.

### #42 Apply the results to the public claims

**Goal:** take every public claim about Book of Mormon authorship, fix the list and the decision rules before any result exists, and afterwards say which our evidence supports, contradicts, or does not address.

The claims come from all sides: the CES Letter and the Johnson rare-phrase search on one, Skousen and Carmack's early modern English work and the Gospel Topics essays on the other, plus the academic studies in `docs/background.md`. The register is `data/claims/register.yaml`.

Two halves, deliberately separated in time. The inventory is built **now**, before results exist; the verdicts are filled in **after** BOM-35. Once results are known, the temptation is to answer the claims one happens to have something interesting to say about, so the list and the rules are frozen first.

- [ ] Extend `data/claims/register.yaml` to full coverage, with `supported_if` and `contradicted_if` written for every testable claim before any result is known
- [ ] Mark untestable claims `testable: none` with a reason; report them as untestable rather than dropping them
- [ ] Freeze the register before the blind run: set `frozen: true`, commit its SHA-256 alongside the analysis thresholds
- [ ] After BOM-35, fill in each verdict from the pre-registered rule and publish the table
- [ ] Report the untestable claims as a group, so the document is not read as a scorecard
- [ ] State in the output that the register took no side and that inability to test a claim is not evidence against it

**Done when:** the frozen register is committed with its hash before #32, and the completed verdict table is published alongside the paper.
**Depends on:** #35 for the verdicts; the inventory itself depends on nothing and is built first.

### #41 Ingest the New York newspapers Chronicling America lacks

**Goal:** the Palmyra paper and the two papers a candidate edited, neither of which is in the national collection.

Chronicling America holds 47 New York pages for all of 1800-1830, but that is a gap in Chronicling America, not in digitization (BOM-10's reading, corrected 2026-10-20): NYS Historic Newspapers holds the *Wayne Sentinel* (Palmyra, LCCN `sn84024337`, which printed the Book of Mormon title page on 26 June 1829 and the sale advertisement on 26 March 1830) and dozens of other 1800-1830 New York titles, including the Palmyra papers of 1817-1823 and the Canandaigua *Ontario Repository* 1824-1829. Of W. W. Phelps's two papers, the *Lake Light* (Trumansburg, `sn84031024`, 1827-1828) is digitized by the Ulysses Philomathic Library and pulled; the *Ontario Phoenix* (Canandaigua, `sn84031006`, 1828-1832) is not digitized anywhere and its surviving pre-1830 run is about twenty paper issues, so it is recorded as unavailable. Full analysis in `docs/new-york-newspapers.md`.

- [x] **Owner action:** browser check done 2026-10-20. NYSHN title index: *Wayne Sentinel* yes, *Ontario Phoenix* no, *Lake Light* no. The *Lake Light* is at `trumansburg.advantage-preservation.com` (168 pages, 42 issues, 1827-10-10 to 1828-11-19); the *Ontario Phoenix* is not digitized anywhere
- [x] Pull the *Lake Light* (`ingest.advantage_archive`; text layer and page index in `data/newspapers/lake_light/`, PDFs in `data/corpus/advantage/`)
- [ ] Pull the *Wayne Sentinel* 1823-1830 with `scripts/nyshn_browser_pull.py` (browser-driven; NYSHN blocks scripts). First `probe` a title page and fix the two Veridian link regexes if needed
- [ ] **Owner decision:** whether to add the other NYSHN period titles (Palmyra Register 1817-1821, Palmyra Herald 1822-1823, Ontario Repository 1824-1829, Rochester Antimasonic Inquirer 1828-1830, and the rest listed in `docs/new-york-newspapers.md`) to this pull
- [x] Record which titles were found and which were not (`docs/new-york-newspapers.md`, `docs/candidates.md`)
- [ ] Add the Phelps text to the candidate corpus (#13) with an attribution rule: two named publishers and heavy reprinting mean unsigned editorial matter is not automatically his
- [ ] Feed the *Wayne Sentinel* into the access evidence (#33)

**Done when:** the available titles are stored with manifests, and any title that could not be obtained is recorded with the reason.
**Depends on:** #10.
**Feeds:** #13 (Phelps's pre-1830 sample), #33 (what was printed and advertised near Palmyra).

### #40 Central configuration file and multiverse runner

**Goal:** every analytic choice lives in one versioned config file, the whole pipeline reads only from it, and anyone can rerun everything with different choices and compare outcomes.

Rerunning the code reproduces our choices, including the bad ones. A single config file lets anyone change a choice and rerun the pipeline to see whether the conclusion holds. Running many reasonable configurations at once is a multiverse analysis (Steegen et al., 2016) or specification-curve analysis (Simonsohn, Simmons and Nelson, 2020).

- [ ] Create `config/preregistered.yaml` holding every analytic choice, with values copied from the pre-registration; each entry cites its pre-registration section
- [ ] **Owner action, not Claude's:** pin every choice currently UNPINNED or CODE ONLY by dated amendment to the pre-registration, before #21 calibration starts. Claude cannot file OSF amendments (see the working rules), so this box only ever gets ticked by Dave. The inventory is in the issue body on GitHub; roughly 25 choices. `uv run python -m metadata.config pending` lists the seven Phase 2 ones
- [ ] Register ENSC `shrinkage` first and by name. `classic/ensc.py` defaults it to `0.0`, so nearest *shrunken* centroids currently runs as plain nearest centroids. #22 replicates Jockers, Witten and Criddle (2008), who used NSC, so an unregistered zero here is not a tuning detail
- [ ] Refactor so no module hard-codes an analytic value; code defaults must match the config or be removed. Known gaps: General Imposters trials, feature fraction and distance (`classic/imposters.py`); ENSC shrinkage and alpha (`classic/ensc.py`); and `classic/features.py`, which uses `top_n=300` at line 22 but defaults to `100` at line 174
- [ ] Define the seed hierarchy explicitly: either one root seed derives `segmentation.split.seed`, `blind.decoy_seed` and the imposters seed, or each is pinned separately. Reproducibility is undefined until this is stated
- [ ] Tag every config key with its recompute tier: `feature` (rerun from cached features, CPU-minutes), `corpus` (re-runs OCR fixes, normalization, masking and segmentation, about a week of compute per value), `model` (retrain, 15-25 H100-hours per value)
- [ ] Add a single entry point, e.g. `uv run bom run --config config/preregistered.yaml --out results/<config-hash>/`
- [ ] Stamp every output with the SHA-256 of the config file and the git commit
- [ ] Add `config/multiverse.yaml` listing a plausible range per choice. Range over the `feature` tier by default (for example MFW 100/300/1000, ENSC shrinkage values, distances); `corpus` and `model` tier sweeps are opt-in and must carry their cost estimate in the file
- [ ] Add a multiverse runner that enumerates or samples combinations, runs them, and draws a specification curve: for each conclusion (each candidate supported or not, each significant parallel, the dating window), the share of configurations that agree
- [ ] Commit `config/multiverse.yaml` and its hash before the blind run (#32), same as the thresholds, so the ranges can't be chosen after seeing results
- [ ] Document in the README: the official result is the pre-registered config; the multiverse is a robustness check; anyone can add a config file by pull request and post their result

**Done when:** a fresh clone reproduces the benchmark results from `preregistered.yaml`, an alternate config produces a different results folder with its own hash, and the multiverse runner produces a specification curve on benchmark data.
**Depends on:** #2, #20.
**Blocks:** #21, #23, #25, #27, #29, and everything downstream of those; all read their analytic choices from the config.

Note on ordering: this issue's number is higher than the issues it blocks, so the "work the lowest-numbered open issue" rule would otherwise route around it and leave it until last, after the analyses it governs. The blocked issues carry `#40` in their own **Depends on** lines to prevent that.

### #21 Build and pass the validation benchmark

**Goal:** show each method recovers known authorship in conditions like the Book of Mormon's.

- [ ] Federalist Papers (classic sanity check)
- [ ] Pseudo-biblical texts with known authors, held out
- [ ] Dictated texts with known authors
- [ ] Open-set cases where the true author is deliberately left out, checking that methods answer 'none of the above'
- [ ] Report accuracy, false positives, and minimum sample sizes per method

**Done when:** the benchmark report is published and each method's pass/fail against the pre-registered threshold is recorded.
**Depends on:** #20, #40.

### #22 Replicate prior Book of Mormon studies

**Goal:** reproduce the published results before adding new ones.

- [ ] Larsen, Rencher and Layton (1980) word-frequency analysis
- [ ] Holmes (1992) vocabulary-richness analysis
- [ ] Jockers, Witten and Criddle (2008) nearest shrunken centroids, including the closed-set flaw
- [ ] Fields, Schaalje and Roper (2011) ENSC
- [ ] Johnson and Johnson (2013) rare 4-grams against *The Late War*
- [ ] Note where results match, differ, and why

**Done when:** a replication report is published. This issue runs on the Book of Mormon only with the published methods, not the new ones.
**Depends on:** #21.

## Phase 4 — Borrowing and parallels

Phase 4 maps which earlier texts share wording or ideas with the Book of Mormon, and measures whether each overlap beats chance.

### #23 Run exact text-reuse detection

**Goal:** every verbatim or near-verbatim passage shared with the corpus.

- [ ] Run passim over the KJV-masked Book of Mormon against the frozen corpus
- [ ] Store each alignment with source, location, length, and similarity
- [ ] Run the same against 3-5 control books (for example Luke, *The Late War*, a sermon collection) to see typical overlap levels

**Done when:** an alignment table for the Book of Mormon and controls is published.
**Depends on:** #19, #40.

### #24 Score rare phrases against a proper null model

**Goal:** fix the main weakness of the 2013 rare 4-gram study.

- [ ] Compute phrase rarity across the whole deduplicated corpus
- [ ] Normalize for book length and genre
- [ ] Build a null distribution by scoring hundreds of random period books the same way
- [ ] Report each source's score as a percentile against that null, with confidence intervals

**Done when:** a ranked source list with percentiles is published, including where Luke and *The Late War* fall.
**Depends on:** #23.

### #25 Search for semantic parallels

**Goal:** find paraphrase, shared story patterns, and sermon structure that exact matching misses.

- [ ] Embed every sentence/passage in the corpus with a sentence-embedding model
- [ ] Build a FAISS index and query it with each Book of Mormon passage
- [ ] Use the same null-model approach as #24 to set significance thresholds

**Done when:** a semantic-parallel table with scores and thresholds is published.
**Depends on:** #19, #40.

### #26 Triage and human review of parallels

**Goal:** separate meaningful parallels from biblical or generic ones.

- [ ] Use an LLM to sort hits into biblical, generic idiom, or specific, with its reasoning logged
- [ ] Have a human review every 'specific' hit and a random sample of the rest
- [ ] Measure LLM-human agreement and report it

**Done when:** a reviewed parallel list and agreement statistic are published.
**Depends on:** #24, #25.

## Phase 5 — AI-era methods

Phase 5 builds the new tools: a language model that has never seen the Book of Mormon, per-author models on top of it, a dating classifier, and style embeddings. Every model is validated on the #21 benchmark before the Book of Mormon is scored.

### #27 Train the time-locked language model

**Goal:** a model trained only on 1780-1830 English, with no exposure to the Book of Mormon or modern text.

- [ ] Build the training set from corpus v1.0, excluding the Book of Mormon and all post-1830 text
- [ ] Run a contamination check: search the training set for long Book of Mormon strings and remove hits
- [ ] Train a tokenizer on period text
- [ ] Train a small GPT-style model (roughly 100-300M parameters) with held-out validation
- [ ] Publish the model card, training config, and loss curves

**Done when:** the model and its card are on Hugging Face and the contamination report is clean.
**Depends on:** #19, #4, #40.

### #28 Fine-tune authorial language models

**Goal:** one model per candidate author, following Huang, Murakami and Grieve's ALM method.

- [ ] Fine-tune a copy of #27 on each candidate's corpus from #13, plus each control group
- [ ] Validate on held-out text from each author and on the #21 benchmark
- [ ] Record per-author sample size and flag unreliable models

**Done when:** all authorial models pass the benchmark threshold or are marked as failed.
**Depends on:** #27, #21.

### #29 Build the linguistic dating classifier

**Goal:** estimate when a passage's grammar and vocabulary come from.

- [ ] Train on dated text: EEBO-TCP (1473-1700), 18th-century texts, and 1780-1830 texts
- [ ] Use grammatical features (verb forms, pronouns, syntax) separately from vocabulary
- [ ] Validate on held-out dated texts and on pseudo-biblical texts with known dates
- [ ] Test whether KJV imitation alone shifts the predicted date

**Done when:** the classifier's accuracy on held-out dated text is published.
**Depends on:** #11, #18, #19, #40.

### #30 Build style embeddings as a cross-check

**Goal:** an independent authorship signal from a different model family.

- [ ] Train or adapt an authorship-embedding model (for example LUAR-style) on period text
- [ ] Validate on the #21 benchmark

**Done when:** benchmark results are published.
**Depends on:** #19, #21.

### #39 Build and validate the corpus-wide author sweep

**Goal:** a tested way to search every author in the 1780-1830 corpus for the closest stylistic match, so candidates nobody has proposed can surface as leads.

Reasoning: a work of this length is rarely its author's only writing, so if the author published anything else in the period, it should be findable. The sweep either identifies close candidates with the evidence behind them, or shows that nobody in the corpus is close. It is exploratory by design: it produces leads for a later pre-registered iteration, never an attribution on its own, and it makes no claim beyond the corpus.

- [ ] Build author-level units from the catalog (#12): every normalized author with at least the minimum word count set in #2, with KJV masking (#16) and spelling normalization (#15) applied
- [ ] Index every author with the style embeddings (#30) and at least one classical method (#20), so a lead has to show up under two independent signals
- [ ] Calibrate a null distribution: query held-out books by known corpus authors and record the rank of the true author; then remove the true author and record how close the best false match looks
- [ ] Set the lead threshold from that null (for example: the true author ranks first in at least X% of held-out queries, and a lead must beat the Y-th percentile of best-false-match scores)
- [ ] Define the discovery/confirmation split of Book of Mormon segments (#17) and record it before the blind run
- [ ] Define the lead report format: author, works, word count, score, null percentile, genre, and an access and plausibility column to be filled from #33

**Done when:** the author index and calibration report are published, and the sweep passes the null test on held-out known authors. The sweep is run on the sealed text only in #32.
**Depends on:** #12, #15, #16, #17, #20, #21, #30.

## Phase 6 — Verification and synthesis

Phase 6 stress-tests the methods, runs the sealed analysis blind, and combines textual results with historical evidence.

### #31 Test robustness to deliberate imitation

**Goal:** know whether a writer imitating KJV style can fool each method.

- [ ] Assemble texts where known 1800s authors wrote in imitation biblical style alongside their normal prose
- [ ] Check whether each method still identifies the real author
- [ ] Report which methods are robust and which are fooled

**Done when:** an imitation-robustness table is published and weak methods are down-weighted per the pre-registration.
**Depends on:** #21, #28, #30.

### #32 Run the blind analysis on the Book of Mormon

**Goal:** score the sealed text with every validated method, without the analyst knowing which segments are which.

- [ ] A sealing script relabels Book of Mormon segments with opaque identifiers and mixes in decoy segments from known authors; it writes the key outside the repository and commits the SHA-256 hashes of the key and of the relabeled set
- [ ] Run the analysis in a fresh session with no access to the key or to the sealing script's output log
- [ ] Run classical methods (#20), authorial models (#28), dating (#29), and embeddings (#30)
- [ ] Run the author sweep (#39) on the discovery half only; save the ranked lead list with null percentiles and sample sizes, hashed with the other outputs
- [ ] Unblind only after all outputs are saved and hashed
- [ ] Run leave-one-candidate-out tests
- [ ] Run the multiverse (#40) inside the blind session, after the official pre-registered run and before unblinding, using the `config/multiverse.yaml` committed and hashed beforehand; hash its outputs with the rest

**Done when:** hashed blind outputs and the unblinded results are published, decoys correctly identified.
**Depends on:** #22, #26, #28-#31, #39.

### #33 Gather access evidence

**Goal:** establish which candidate sources Joseph Smith could plausibly have read before 1829.

Digitized sources only (decision 2026-10-16): holdings lists, catalogues and newspapers that can
be downloaded. No visits to physical archives.

For this period and this material that is close to no restriction at all. Pre-1830 American
imprints are covered by HathiTrust, Google Books and the Internet Archive; the newspapers are in
Chronicling America; the Joseph Smith Papers is complete online. What limits the access evidence
is not digitization but the historical record itself: nobody wrote down what Joseph Smith
borrowed, and lending registers for a village rental library are unlikely to survive anywhere, in
any format. The ceiling is "this book was demonstrably available in the area", never "he read
it", and that ceiling is the same whether the work is done on a screen or in a reading room. The
paper states the limit in those terms rather than blaming the medium.

- [ ] Compile the Manchester rental library holdings list
- [ ] List local newspapers and what they printed or advertised (including bookseller ads)
- [ ] Score each candidate source from #26 for documented availability

**Done when:** an access table with sources is published.
**Depends on:** #26.

### #34 Gather manuscript and dictation evidence

**Goal:** bring the physical evidence of how the text was produced into the analysis.

"Physical" means the evidence the manuscripts carry, not handling them. The Joseph Smith Papers
transcriptions pulled in BOM-05 are the source, and they are already on disk, so this is
analysis rather than archival work.

- [ ] Catalog dictation-type errors in the original manuscript (misheard words, spelling corrections)
- [ ] Map scribe changes and check whether style shifts track scribes or narrators
- [ ] Summarize the production timeline (roughly April-June 1829)

**Done when:** a manuscript-evidence report is published.
**Depends on:** #5, #32.

### #35 Combine everything in a Bayesian model

**Goal:** one transparent estimate that weighs all lines of evidence.

- [ ] Define hypotheses: each candidate, the internal narrators, and 'author not in set'
- [ ] Turn each result (#24, #26, #29, #32, #33, #34) into a likelihood with stated uncertainty
- [ ] Run sensitivity analysis on priors and on each evidence weight
- [ ] Report where the methods agree and where they conflict

**Done when:** posterior results, code, and sensitivity tables are published.
**Depends on:** #32-#34.

## Phase 7 — Publish

Phase 7 writes up the results, releases everything, and puts the work through outside review. Closing #38 closes the project.

### #36 Write the paper and post a preprint

**Goal:** a full write-up that reports results against the pre-registration, including null and conflicting findings.

- [ ] Draft methods, validation, results, and limitations sections
- [ ] List every deviation from the pre-registration
- [ ] Report the specification curve from #40 beside the official result: for each conclusion, the share of configurations that agree, and name any conclusion that holds only under the pre-registered configuration
- [ ] Report the author sweep's leads as exploratory, with the historical plausibility check, and state what a second pre-registered iteration would test
- [ ] Run the three simulated reviewers from #3 against the full draft with an AI model, and publish their objections and the responses alongside it, labeled simulated
- [ ] Post to a preprint server (arXiv cs.CL, or SocArXiv/OSF)

**Done when:** the preprint is live.
**Depends on:** #35.

### #37 Release code, data, models, and an explorer

**Goal:** anyone can rerun every result and browse the findings.

- [ ] Tag a release of the repo with a one-command reproduction script
- [ ] Publish all models (#27, #28, #29, #30) on Hugging Face
- [ ] Publish results data on Zenodo with a DOI
- [ ] Build a web explorer where readers can click a Book of Mormon passage and see its parallels, scores, and dating estimate

**Done when:** a fresh machine reproduces the headline results from the release and the explorer is live.
**Depends on:** #36.

### #38 Simulated peer review and response

**Goal:** the strongest critique an AI reviewer can produce, answered on the record.

Decision 2026-10-15: no journal submission. Peer review is simulated by an AI model acting as reviewer and labeled as such; the project is one person with AI assistance.

- [ ] Build a reviewer setup that sees only the preprint, the pre-registration, and the released code and data, not the working sessions that produced them
- [ ] Run at least three independent review passes (methods, statistics, historical claims) and publish the reviews verbatim
- [ ] Respond to every point with public, dated revisions or a recorded disagreement
- [ ] Log any real critiques and replication attempts that arrive in the repo

**Done when:** the reviews, responses, and final revision are published, all labeled as simulated review.
**Depends on:** #36, #37.
