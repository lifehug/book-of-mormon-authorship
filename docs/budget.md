# Compute and budget plan (BOM-04)

Estimates as of 2026-10-15. Every number here is an order-of-magnitude plan, not a quote.
Each is re-checked when the corresponding issue starts, and the actuals are recorded in the
"Actuals" table at the end.

## 1. Storage

Assumptions: 1 token is roughly 4.5 bytes of English text; a volume averages about 250,000
tokens (Institutional Books: 242B tokens over 983,004 volumes); the 1780-1830 English slice is
5-8% of the Institutional Books collection, which is weighted to the 19th century.

| Dataset | Raw size kept | Notes |
| --- | --- | --- |
| Institutional Books 1.0, English 1780-1830 | **73 GiB measured on disk, 2026-10-16** (37 GiB raw OCR + 37 GiB cleaned OCR; the earlier 44 GB estimate counted one version) | 31,958 volumes, 10.5B tokens; about 700 GB of transfer because shards must be read whole; the public metadata dataset gives the exact slice before any text is pulled. Terms: noncommercial, no redistribution |
| HathiTrust public domain 1780-1830 | about 150 GB if full text is obtained | 135,035 volumes measured 2026-10-15, 107,178 not in Harvard (87,200 books, 18,317 serial volumes); four times the Harvard slice. Full text needs Research Center access; Extracted Features (word counts per page) are open |
| Internet Archive, 1780-1830 American imprints | 10-20 GB | OCR text plus metadata |
| Chronicling America, 1800-1830 | under 5 GB | pre-1830 coverage is thin; article-level split adds little |
| TCP texts (EEBO, Evans, ECCO) | about 25 GB XML | 61,315 TEI files, one per GitHub repo; includes Evans American imprints to 1800 and ECCO 18th century |
| Book of Mormon texts, KJV, candidate corpora | under 1 GB | |
| **Raw total** | **about 130-200 GB**, or 280-350 GB if HathiTrust full text is obtained | revised 2026-10-16 after measuring Institutional Books |
| Cleaned, normalized, masked copies (about 3x raw) | 300-500 GB | keep originals and every derived version |
| Passage embeddings and FAISS index | 50-100 GB | ~100M passages at 384 dims, fp16, plus a compressed index |
| Models and checkpoints | 50 GB | 300M-parameter base (~1.2 GB fp32) plus ~15 fine-tunes and training checkpoints |
| **Working total** | **about 0.5-0.8 TB** | plan for 1 TB of fast local disk plus off-site copy |

Storage cost: a **2 TB external SSD**, $150-200; off-site copy on object storage at roughly
$6/TB/month (Backblaze B2 class) or a Hugging Face dataset repo. Call it **$10/month**.

**Count OCR versions, not volumes.** Institutional Books ships two per volume — Harvard's raw
OCR and their cleaned OCR — and the pull keeps both, which is why it measured 73 GiB against a
44 GB estimate. Check the same before trusting the other rows: Internet Archive's `_djvu.txt`
is one version, but TCP ships TEI XML plus extracted text, and BOM-14's OCR correction adds a
third copy of whatever it touches. The 3x multiplier on the derived-copies row below assumes
one source version; with two it is 6x of a single version, which is the number that matters for
the external drive.

The external drive is required, not optional. The machine's internal disk is 256 GB (about
107 GB free as of 2026-10-15), which cannot hold even the 100-170 GB of raw corpora, let
alone the 300-500 GB of derived copies. 2 TB rather than 1 TB because the working total is
already 0.5-0.8 TB, leaving a 1 TB drive no headroom for staging the off-site copy; the price
difference is about $50. Mount it and point `data/` at it per `docs/mac-mini-setup.md`
section 4.

## 2. GPU hours

Assumptions: one H100 delivers about 4e14 useful FLOP/s at 40% utilization for a small model;
an A100 is about 2.5x slower; training cost is 6 x parameters x tokens FLOPs.

| Job | Issue | Core estimate | With 3x overhead for reruns, tuning, failures |
| --- | --- | --- | --- |
| Time-locked base model, 300M params on ~10B tokens (one pass after dedup) | BOM-27 | 15-25 H100-h | 50-75 H100-h |
| Smaller 125M pilot on 5B tokens first | BOM-27 | 3-5 H100-h | 10-15 H100-h |
| Authorial fine-tunes, ~15 models on under 1M tokens each, plus perplexity scoring | BOM-28 | 10-20 H100-h | 30-60 H100-h |
| Passage embeddings over the corpus (small sentence model) | BOM-25 | 10-20 H100-h | 20-40 H100-h |
| Style embedding model adaptation and author sweep index | BOM-30, BOM-39 | 10-20 H100-h | 30-60 H100-h |
| Dating classifier (transformer variant; the feature model is CPU) | BOM-29 | 5-10 H100-h | 15-30 H100-h |
| Benchmark, imitation, and blind runs across all models | BOM-21, BOM-31, BOM-32 | 10-20 H100-h | 30-60 H100-h |
| **Total** | | **about 70-120 H100-h** | **about 200-350 H100-h** |

At $2-4 per H100-hour (see section 4) that is **$400-1,400 of GPU time** for the whole
project, with the base model the largest single item. A100s are roughly cost-equivalent per
unit of work at current prices and are fine for everything here.

## 3. CPU-heavy and API work

| Job | Issue | Estimate | Cost |
| --- | --- | --- | --- |
| MinHash deduplication, OCR fixes, spelling normalization over ~20B tokens | BOM-12, BOM-14, BOM-15 | tens of core-hours per pass | local machine, or a 32-core cloud box at ~$1-2/h for a few days: $50-150 |
| passim text-reuse alignment over the corpus | BOM-23 | the heaviest CPU job; days on 32-64 cores with 128+ GB RAM | $100-300 cloud, or run locally over a week |
| LLM OCR correction on a sample of ~1,000 pages | BOM-14 | ~2-5M tokens | under $50 in API calls |
| LLM triage of parallel hits (~10k hits) | BOM-26 | ~10-20M tokens | $30-100 in API calls |
| Classical stylometry, dating features, Bayesian synthesis | BOM-20, BOM-29, BOM-35 | CPU | local |

## 4. GPU providers

Prices seen in October 2026 comparisons; they move monthly, so verify on the provider's page
before each training run.

| Provider | H100 per hour | A100 80GB per hour | Fit for this project |
| --- | --- | --- | --- |
| Lambda | about $2.50-4.00 (SXM, on-demand) | about $1.30-2.80 | simplest for the multi-hour base-model run; reliable, persistent storage, no marketplace variance |
| RunPod | $1.99 (Community) to $2.89 (Secure) | $1.19-1.39 | good middle ground; Secure Cloud for the base model, Community for cheap experiments |
| Vast.ai | from about $0.90-1.90 depending on host | from about $0.50 | cheapest; host quality varies, fine for short embedding and fine-tune jobs |

Recommendation: one reliable provider (Lambda or RunPod Secure) for the base-model training
and the blind run, where a lost job costs a day; a marketplace (Vast or RunPod Community) for
the short jobs. Budget line: **$1,000 for GPUs, $300 for CPU boxes, $200 for API calls, $120
for a year of storage, total about $1,600**, with the GPU line the one to watch.

## 4a. Local machine option: Mac mini (superseded — see 4b and 4c)

> This section evaluates a machine that was **not** bought. It is kept for the reasoning and
> for the Mac Studio comparison. For what actually runs on the hardware on hand, read section
> 4c; every "yes" below assumes 64 GB and does not transfer to a 16 GB machine.

A 2026 Mac mini with M5 Pro (18-core CPU, 20-core GPU, 64 GB unified memory, 1 TB SSD) plus
a 2 TB external SSD can run everything in this plan except the base-model training.

| Workload | On the Mac mini | Notes |
| --- | --- | --- |
| Ingest, dedup, OCR fixes, normalization, masking, segmentation, classical stylometry, synthesis | yes | CPU-bound; most of the project |
| passim text reuse | yes, days | run it over a week rather than renting a 64-core box |
| Passage embeddings over the corpus | yes, days | small sentence model via MLX or PyTorch MPS; overnight runs for about a week |
| Authorial fine-tunes (~15 small models) | yes, hours each | MLX |
| Sweep index, benchmark, imitation, blind runs | yes | inference only |
| 125M pilot base model on ~5B tokens | borderline, about a week | useful once to debug the pipeline |
| 300M base model on ~10B tokens | no, roughly 3-4 weeks continuous | rent an H100: 15-25 hours core, $150-300 with reruns |

Memory: 24 GB is too small once the FAISS index and a fine-tune are resident together; 64 GB
is the right configuration. With the Mac as the primary machine the cloud lines shrink to
roughly **$400-600**: the base-model run, a small reserve for a second run, and API calls.
Mac Studio comparison, scaled from the mini estimate by memory bandwidth (optimistic by up to
a third, since Apple GPUs do not scale linearly for training):

| Machine | Bandwidth | 300M model, 10B tokens | 125M pilot, 5B tokens |
| --- | --- | --- | --- |
| Mac mini M5 Pro, 20-core GPU | 307 GB/s | 25-40 days | about a week |
| Mac Studio M5 Max, 40-core GPU | 614 GB/s | 12-20 days | 3-4 days |
| Mac Studio M5 Ultra, 80-core GPU | 1.2 TB/s | 6-10 days | about 2 days |
| Rented H100 | 3.35 TB/s | 15-25 hours | 3-5 hours |

An Ultra makes the project fully self-contained with no cloud account; it is only worth it if
the machine has other uses. No benchmark exists for MLX training at this model size, so the base-model estimate is from
FLOPs and the M5 Pro's 307 GB/s memory bandwidth; re-check with the 125M pilot before deciding.

## 4b. Decision (2026-10-15): the existing Mac mini plus rented H100

Primary machine: the Mac mini already on hand — **M4, 10-core CPU (4P/6E), 16 GB unified
memory, 256 GB internal SSD** — plus a 2 TB external SSD for `data/`. Cloud GPU for the 300M
base model and for any job that does not fit in 16 GB. No new Mac.

**Revised the same day, 2026-10-15.** The first version of this section specified a Mac mini
M5 Pro (18-core CPU, 20-core GPU, 64 GB, 1 TB SSD) at about $3,199. That machine was never
bought. Measuring the actual hardware showed an M4 with 16 GB and a 256 GB internal disk, so
section 4a's "on the Mac mini" verdicts — all written for 64 GB — no longer hold as stated.
The decision is to proceed on the existing machine and rent compute for the jobs it cannot
hold, rather than spend $3,199 on a projection. Section 4c records what that costs us.

The only hardware purchase is the external SSD. The internal 256 GB disk cannot hold even the
raw corpora (100-170 GB) alongside macOS and the derived copies; `data/` moves to the external
drive per `docs/mac-mini-setup.md` section 4.

### Cash costs

| Item | Cost | When |
| --- | --- | --- |
| Mac mini | **$0** | already owned (M4, 16 GB, 256 GB) |
| 2 TB external SSD | $150-200 | now — the one purchase |
| Rented H100 for the base model, with one rerun in reserve | $150-300 | BOM-27 |
| Rented compute for jobs that exceed 16 GB (see 4c) | $250-600 | BOM-23, BOM-25, Phase 5 |
| LLM API calls (OCR sample, parallel triage) | $100-200 | BOM-14, BOM-26 |
| Off-site backup of working data, optional | about $10/month | Phase 1 onward |
| OSF, GitHub, Hugging Face, Zenodo | $0 | |
| Journal fees | $0 | no submission; peer review is simulated |
| **Total** | **about $650-1,300** | |

Against the superseded plan's $3,700-4,300, this saves roughly $2,400-3,600 up front and
moves part of it into rented compute, paid only as each job needs it.

## 4c. What 16 GB costs us

Section 4a's table assumed 64 GB and a 20-core GPU. On 16 GB and a 10-core M4, the verdicts
change for a minority of issues. Everything not listed here is unaffected: it is CPU- and
disk-bound, and runs locally as planned.

| Workload | Issue | 64 GB plan | On this machine |
| --- | --- | --- | --- |
| Phase 1 ingest, dedup | BOM-05 to BOM-13 | yes | yes — network- and disk-bound, not memory-bound |
| OCR fixes, normalization, masking, segmentation | BOM-14 to BOM-19 | yes | yes, slower on 10 cores; streams document-at-a-time |
| Classical stylometry | BOM-20 to BOM-22 | yes | yes — small feature matrices |
| passim text reuse | BOM-23 | yes, days | **rent, or chunk heavily**; already budgeted at $100-300 cloud in section 3 |
| Passage embeddings and FAISS index | BOM-25, BOM-30, BOM-39 | yes, days | **index does not fit in RAM**; use an on-disk or IVF-PQ compressed index, or rent |
| Authorial fine-tunes (~15 small models) | BOM-28 | yes, hours each | likely yes via MLX; re-measure on the first one |
| 125M pilot base model | BOM-27 | about a week | no — rent |
| 300M base model | BOM-27 | no, rent | no — rent, unchanged |
| Blind run, imitation tests, synthesis | BOM-31 to BOM-35 | yes | yes — inference and CPU |

The net effect is that BOM-23 and the index-building half of BOM-25/BOM-30/BOM-39 move from
"local, days" to "rented or redesigned". Both were already partly cloud lines, which is why
the cash total moves by only a few hundred dollars.

These are projections from the memory figures, not measurements. The first real datapoint is
whichever of BOM-23 or BOM-25 is reached first; record the actual in section 6 and revise this
table rather than trusting it.

### Effort and timeline

Effort is working days of focused time for one person using Claude Code, covering data
wrangling, review, writing, and runs. Wall-clock compute runs unattended on the Mac and
overlaps with the next issue's work. Phase 0 is done except for opening accounts.

| Phase | Issues | Effort (working days) | Unattended compute | Notes |
| --- | --- | --- | --- | --- |
| 1 Corpus | BOM-05 to BOM-13 | 25-40 | 1-2 weeks of downloads and dedup | HathiTrust access, if requested, can add weeks of waiting; proceed on Harvard, IA, and Chronicling America meanwhile |
| 2 Preparation | BOM-14 to BOM-19 | 20-30 | 1 week of OCR fixes, normalization, passim alignment to the KJV | ends with the Zenodo DOI |
| 3 Classical and validation | BOM-20 to BOM-22 | 20-32 | hours | replication of five prior studies is the long pole |
| 4 Borrowing | BOM-23 to BOM-26 | 16-27 | 2 weeks: passim over the corpus, passage embeddings on the Mac | human review of parallels is the owner's own time |
| 5 AI-era methods | BOM-27 to BOM-30, BOM-39 | 25-40 | 1 week local pilot, 1 day rented H100, days of fine-tunes and indexing | |
| 6 Verification | BOM-31 to BOM-35 | 21-36 | days | the blind run is sealed by script; access and manuscript evidence are archival work |
| 7 Publish | BOM-36 to BOM-38 | 16-26 | hours of AI review runs | no journal wait; peer review is simulated |
| **Total** | **35 issues remaining** | **143-231 working days** | **about 6-8 weeks, mostly overlapped** | |

Calendar time at three paces:

| Pace | Working days per week | Calendar to the end (BOM-38) |
| --- | --- | --- |
| Side project | 1 | 2.5-4 years |
| Half time | 2.5 | 12-20 months |
| Full time | 5 | 7-10 months |

Compute never sets the pace on this plan; the owner's working days do.

**Revised 2026-10-16: digitized sources only.** The project uses material that can be
downloaded; there are no visits to physical archives. That changes which items genuinely need
a person, because the original list assumed archive work that is not in scope:

| Item | Needs a person? | Why |
| --- | --- | --- |
| BOM-26, reviewing parallels | **Yes** | The deliverable is an LLM-human agreement statistic. A model triaging and a model adjudicating measures a model agreeing with itself. This is the only place in the project where a human checks the machine's judgment on the evidence itself — every other review step is a labeled simulation — so it should stay even though it is the largest remaining human cost |
| BOM-36, writing the paper | **Yes, as the author** | Claude can draft it. The owner's name is on it and every claim has to be one he can defend. Ownership, not capability |
| BOM-33, access evidence | No | Holdings lists, catalogues and bookseller ads in period newspapers are all downloadable. Material that exists only on paper is out of scope and the gap is reported |
| BOM-34, manuscript evidence | No | The Joseph Smith Papers transcriptions were pulled in BOM-05 and are on disk. Dictation errors, scribe changes and the production timeline are analysis of data already held |
| BOM-13, candidate texts | Mostly no | Sourcing is searching digitized collections. The owner decides what counts as a verified holograph |

So the irreducible human floor is BOM-26's review plus the owner's time reading, deciding, and
standing behind the drafted paper, not the 40-60 days the original list implied. The phase
estimates above are unrevised and should be treated as an upper bound until a phase actually
completes and its actual lands in section 6.

## 5. Accounts and access

| Service | Purpose | Status | Notes |
| --- | --- | --- | --- |
| OSF | pre-registration | done, https://osf.io/ebpcw/ | registration https://osf.io/6ugxc/ |
| GitHub | code and backlog | done | lifehug/book-of-mormon-authorship |
| Hugging Face | models (BOM-27 to BOM-30) and large derived datasets | done, account `etherfuse`, write token stored locally | public repos; chunk files to 20 GB or under; check the current storage quota before uploading |
| Zenodo | corpus v1.0 manifests and results with DOIs (BOM-19, BOM-37) | done, linked to GitHub; every tagged release gets a DOI automatically | 50 GB per record, 100 files; one-time increase to 200 GB on request. Cleaned corpus text goes to Hugging Face, Zenodo holds manifests, derived tables, and the datasheet |
| GPU cloud | the base-model run only | done, RunPod; restricted API key stored locally; no pods or endpoints running as of 2026-10-15 | see section 4 and 4b |
| HathiTrust Research Center | full text beyond Extracted Features | deferred: request only if BOM-08 measures a real gap after the Harvard pull | non-member accounts are available for researchers; public-domain-only Data Capsules are the route; in-copyright access is member-only and not needed here |
| Harvard Institutional Data Initiative | Institutional Books 1.0 | none; open on Hugging Face, non-commercial terms | |

Local credential files (never in the repo): `~/.config/osf/token`, `~/.config/huggingface/token`, `~/.config/runpod/token`, each mode 600.

## 6. Actuals

| Item | Planned | Actual | Issue | Date |
| --- | --- | --- | --- | --- |
| Primary machine | Mac mini M5 Pro, 64 GB, 1 TB, about $3,199 | Mac mini M4 (Mac16,10), 10-core, 16 GB, 256 GB internal — already owned, $0 | BOM-04 | 2026-10-15 |
| External SSD | 2 TB, $150-200 | on order | BOM-04 | 2026-10-15 |
| Internal disk free before Phase 1 | n/a | 107 GB, after reclaiming about 59 GB (dead Colima VM and its orphaned Lima datadisk, 53 GB; ollama install and one unused model, 5 GB) | BOM-07 | 2026-10-15 |
| Institutional Books 1780-1830 English slice | 5-8% of the collection | 31,958 volumes of 983,004 (3.3%), 10.47B tokens, about 44 GB of text; an independent 48-shard sample read 2.6% | BOM-07 | 2026-10-15 |
| Institutional Books metadata scan | n/a | about 1.3 min at 32 threads: `date1_src` and `language_gen` are separate columns, so the slice is identified by column-pruned Parquet reads before any text is pulled | BOM-07 | 2026-10-15 |
| Institutional Books transfer | about 700 GB | confirmed as the right order: each shard is one row group of 100 rows, so there is no row-level pushdown, and at a 3.3% hit rate about 96% of the 9,831 shards hold at least one wanted volume and must be read whole | BOM-07 | 2026-10-15 |
| Institutional Books on disk | about 44 GB | **73 GiB**: 37 GiB raw OCR + 37 GiB cleaned OCR, both kept, 31,958 volumes each. The estimate counted one version | BOM-07 | 2026-10-16 |
| Institutional Books pull, wall time | not estimated | 11h38m on the Mac mini (18:00 to 05:38, including a 2-minute stop to move `data/corpus` to the external SSD), about 12 shards/min, no failed shards | BOM-07 | 2026-10-16 |
| External SSD | 2 TB, $150-200 | Samsung T7 2 TB, APFS case-sensitive and journaled, mounted `/Volumes/bomdata`; 130 GiB of its 1.8 TiB used, of which 73 GiB is corpus and about 57 GiB is a Spotlight index that should be disabled | BOM-04 | 2026-10-16 |
| T7 read throughput | not estimated | about 470 MB/s: each 37 GiB manifest build hashed in 79s | BOM-07 | 2026-10-16 |

## Sources

- Institutional Books 1.0 technical report: https://arxiv.org/abs/2506.08300 (983,004 volumes, 242B tokens)
- GPU price comparisons, October 2026: https://www.spheron.network/blog/gpu-cloud-pricing-comparison-runpod-vs-vastai-2026/ , https://www.gpucloudlist.com/en/blog/lambda-labs-vs-runpod-vs-vast-ai , https://www.synpixcloud.com/blog/cloud-gpu-pricing-comparison-2026
- Zenodo limits: https://support.zenodo.org/help/en-gb/1-upload-deposit/80-what-are-the-size-limitations-of-zenodo
- HTRC access and Data Capsules: https://htrc.atlassian.net/wiki/spaces/COM/pages/43286644/Troubleshooting+and+FAQs
- EEBO-TCP downloads: https://textcreationpartnership.org/?p=50
