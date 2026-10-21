# Design audit, 2026-10-20

A review of the whole plan against its own goal: the most robust, open, replicable and
defensible look at Book of Mormon authorship that one person and an AI can produce. Written at
the end of Phase 1, with `BOM-01` to `BOM-11` closed and `BOM-12` running, so that the findings
land before any analytical code is written and long before the blind run.

This is a self-audit. Like every other review in this project it is not independent scrutiny,
and section 10 of the pre-registration says so.

## Where the project stands

11 of 42 issues closed. All of them are setup and ingest; every analytical issue is still open.
`docs/budget.md` puts the remainder at 143-231 working days. Phase 1 was estimated at 25-40
working days and took five calendar days of elapsed time, but it is the phase that automates
best, and it is the phase whose estimates were already wrong once (see `docs/budget.md` 5a).

## What the design gets right

Two things are worth naming because they are the reason to run this study at all rather than
re-run an existing one.

**The open-set framing.** Jockers, Witten and Criddle (2008) reported a Rigdon/Spalding signal
and were answered by Fields, Schaalje and Roper (2011) on one central point: a closed-set
method was applied to an open-set problem, so it was obliged to choose among the candidates it
was offered. Here H1b ("none of the above") is a first-class hypothesis (section 2), the
synthesis puts prior mass 0.5 on "author not in set" (6.7), and the benchmark measures open-set
false-positive rate directly (section 7). The main critique of the prior literature is designed
out rather than rebutted.

**Imitation weighting.** Pseudo-biblical register is the confound that can swamp authorial
signal in this text. Section 9 weights each method by its measured accuracy at identifying
authors from their *imitation-biblical* samples. No published Book of Mormon study known to this
project does this.

Also sound: sealing the text from training (4.2), the discovery/confirmation split (4.5), the
blind run with decoys and committed hashes (section 8), and the commitment to report every
hypothesis, failure and deviation (section 12).

## Findings

Five gaps, each now a tracked issue. They are ordered by how much they change the study.

### 1. No power analysis (BOM-43)

Section 10 already concedes that Joseph Smith's undisputed pre-1830 writing is small and that
"he will likely fall under the sample floor for most methods". Section 3 puts it under 10,000
words. If that is right, the study's most-asked question is structurally unanswerable — and
under the current plan that becomes apparent at BOM-21, after the corpus, the models and the
benchmark have all been built.

It can be known now. Section 7 already defines the minimum sample size as the smallest at which
closed-set accuracy holds at 80%. Measuring that curve on *known* authors — the Federalist
papers, the held-out pseudo-biblical set — uses no Book of Mormon text and breaks no seal. Put
the curve beside the candidate word counts from BOM-13 and each candidate is either testable or
flagged in advance.

This also decides what the paper is. If Smith cannot be tested at his sample size, the honest
result is about the open-set outcome, the dating question, and the candidates who *can* be
tested. That is still a contribution. It is a much weaker one if it is discovered late and
reads as a retreat.

Three details make the exercise more than a single go/no-go number.

The floor is **per method**, and 6.2 needs two. A candidate is *supported* only when two
independent method families agree, so clearing one floor is not enough to be concludable — and a
method below its floor still returns a confident-looking score, which is the quiet failure here.

The same curve sizes the **Book of Mormon side**. 4.5 cuts the text into 2,000- and 5,000-word
chunks, and a chunk is a sample with its own requirement. If 2,000 words falls below a method's
floor, those runs are exploratory for that method. Nothing in the plan currently anticipates
this.

The count that matters is **masked** words, not raw. 4.4 strips KJV verbatim and close-paraphrase
spans before attribution runs, and the early revelations are heavily KJV-inflected, so Smith's
effective sample may be far smaller than his raw word count suggests.

### 2. "Replicable" is overstated (BOM-44)

Harvard Institutional Books forbids redistribution. HathiTrust forbids it, and this project's
rsync access ends 2026-11-30. Joseph Smith Papers transcriptions are copyrighted. The
consequence is plain: **nobody can rebuild this corpus from this repository**, and section 10's
known limits do not say so.

**Corrected 2026-10-20, after the owner pushed back on this framing.** The finding above set
the bar at "downloadable by anyone", which is not the bar. Research on restricted data —
clinical trials, census microdata, UK Biobank, dbGaP — is considered replicable when the
protocol, the code and the *access procedure* are published and open to any qualified
researcher. That standard this project already meets: `docs/hathitrust-request.md` records the
whole application, five of the eight sources need no permission at all, and the manifests let a
replicator prove byte-level agreement. `docs/replication.md` now consolidates the paths. The
study is replicable; what BOM-44 adds is a *lower bar* — letting someone check the statistics
with no application at all — not the basis of the claim. The original framing is left above
rather than deleted, because the correction is the more useful record.

The derived artifacts are still worth publishing — 4-gram document-frequency tables, feature matrices,
the genre catalog, OCR quality scores, the dedup graph. These are not reconstructable back to
source text, which is what the licences restrict, and they are what sections 5.1, 5.5 and 6.5
read. Publishing them lets an outsider re-run most of the pipeline without the corpus, which
converts the bulk of the study from "trust me" to "check me".

Each source's terms must be checked individually before anything is published; the finding here
is that this has not been examined at all, not that it is already permitted.

### 3. The borrowing null is underpowered (BOM-45)

Section 6.5 builds a 99th-percentile threshold from "at least 500 randomly chosen period
volumes". A 99th percentile estimated from 500 draws rests on about five observations in the
tail, and the resulting threshold carries more sampling noise than the comparisons made against
it.

The corpus holds roughly 560,000 volumes and local compute is free (`CLAUDE.md`). Scoring
5,000-10,000 costs hours. "At least 500" is a floor, so using more needs a recorded decision and
a config value, not an amendment.

### 4. Imitation weights may rest on four authors (BOM-46)

Section 9 sets each method's weight from its accuracy on authors who wrote both
imitation-biblical and ordinary prose, in bands at 80% and 60%. The named pseudo-biblical set is
Leacock, Snowden, Linning and Hunt. If that is the whole population of dual-register authors,
the weights are being set by four measurements and the 60-80% half-weight band cannot be
distinguished from noise.

Either BOM-18's search of the catalog finds more such authors, or the weights are reported with
their uncertainty and the synthesis is run at equal weights as a registered sensitivity.

### 5. The sweep's false-lead rate is unstated (BOM-47)

Section 6.6 calls an author a *lead* when the score beats the 95th percentile of best-false-match
scores under both the embedding and the classical signal. If those signals are even partly
independent, the expected false-lead rate is on the order of 0.25% of swept authors, which over
tens of thousands of authors is hundreds of leads.

That is not a flaw in the rule; it is what an exploratory sweep is for. The flaw is that the
number is not written down in advance, so a large lead count can be mistaken for a finding, and
so the historical-plausibility gate in section 3 — which is subjective and applied after the
leads are seen — has no prior to be judged against.

## What to cut first, if anything has to be

Nothing in the plan is unnecessary, but one component is far more expensive than the rest and
should be named now as the first thing to drop, while that is a methodological judgment rather
than a capitulation.

**BOM-27 and BOM-28** — training a 300M model from scratch and fine-tuning one copy per
candidate — carry the only rented-GPU line in the budget, the longest unattended compute, and
the least precedent for this task. Section 6.2 requires agreement from two independent method
families, and classical stylometry plus style embeddings already satisfies it.

The recommendation is to keep them: the perplexity-ratio score is genuinely independent of the
classical features, and it is a large part of what makes this more than a well-run replication.
But if the project stalls, this is what goes, and the study still answers Q1 under its own
decision rule.

The corpus itself is not too large. For Q2 and the sweep, more volumes is strictly better.

## The limit that none of this fixes

Every review here — adversarial, draft, peer — is simulated by an AI model and run by the person
running the analysis. Section 10 states it plainly, which is right, and no amount of
pre-registration, blinding or multiverse analysis answers it.

The one cheap mitigation is exposure. The pre-registration is already public on OSF. Inviting
comment on it now, from technically literate readers on both the critical and the apologetic
side, would put some real scrutiny in front of the blind run. Criticism that arrives before
BOM-32 can still change the method; criticism that arrives after the preprint can only be
answered.

This is an owner decision and is not tracked as an issue.

## Verdict

On design, this is ahead of the published literature on Book of Mormon authorship, principally
for the open-set framing and the imitation weighting. On replicability it is not yet what it
claims, and finding 2 is the fix. Finding 1 is the one that could change what the paper is
about, and it should be settled before BOM-21 rather than discovered there.
