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
| Institutional Books 1.0, English 1780-1830 | 60-100 GB | 50-80k volumes, 12-20B tokens. Filter on the metadata parquet first; stream the text, do not mirror the full ~1 TB release |
| HathiTrust public domain 1780-1830 | 10-30 GB | Extracted Features for everything; full text only where the Data Capsule allows export |
| Internet Archive, 1780-1830 American imprints | 10-20 GB | OCR text plus metadata |
| Chronicling America, 1800-1830 | under 5 GB | pre-1830 coverage is thin; article-level split adds little |
| EEBO-TCP Phases I and II | 10 GB | 53,831 TEI XML texts, ~2 GB zipped |
| Book of Mormon texts, KJV, candidate corpora | under 1 GB | |
| **Raw total** | **about 100-170 GB** | |
| Cleaned, normalized, masked copies (about 3x raw) | 300-500 GB | keep originals and every derived version |
| Passage embeddings and FAISS index | 50-100 GB | ~100M passages at 384 dims, fp16, plus a compressed index |
| Models and checkpoints | 50 GB | 300M-parameter base (~1.2 GB fp32) plus ~15 fine-tunes and training checkpoints |
| **Working total** | **about 0.5-0.8 TB** | plan for 1 TB of fast local disk plus off-site copy |

Storage cost: a 1 TB external SSD or the existing machine for working data; off-site copy on
object storage at roughly $6/TB/month (Backblaze B2 class) or a Hugging Face dataset repo.
Call it **$10/month**.

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

## 5. Accounts and access

| Service | Purpose | Status | Notes |
| --- | --- | --- | --- |
| OSF | pre-registration | done, https://osf.io/ebpcw/ | registration https://osf.io/6ugxc/ |
| GitHub | code and backlog | done | lifehug/book-of-mormon-authorship |
| Hugging Face | models (BOM-27 to BOM-30) and large derived datasets | needed | public repos; chunk files to 20 GB or under; check the current storage quota for free accounts before uploading |
| Zenodo | corpus v1.0 manifests and results with DOIs (BOM-19, BOM-37) | needed | 50 GB per record, 100 files; one-time increase to 200 GB on request. Cleaned corpus text goes to Hugging Face, Zenodo holds manifests, derived tables, and the datasheet |
| GPU cloud | training | needed, provider to be chosen | see section 4 |
| HathiTrust Research Center | full text beyond Extracted Features | needed only if BOM-08 finds gaps Institutional Books does not cover | non-member accounts are available for researchers; public-domain-only Data Capsules are the route; in-copyright access is member-only and not needed here |
| Harvard Institutional Data Initiative | Institutional Books 1.0 | none; open on Hugging Face, non-commercial terms | |

## 6. Actuals

| Item | Planned | Actual | Issue | Date |
| --- | --- | --- | --- | --- |
| | | | | |

## Sources

- Institutional Books 1.0 technical report: https://arxiv.org/abs/2506.08300 (983,004 volumes, 242B tokens)
- GPU price comparisons, October 2026: https://www.spheron.network/blog/gpu-cloud-pricing-comparison-runpod-vs-vastai-2026/ , https://www.gpucloudlist.com/en/blog/lambda-labs-vs-runpod-vs-vast-ai , https://www.synpixcloud.com/blog/cloud-gpu-pricing-comparison-2026
- Zenodo limits: https://support.zenodo.org/help/en-gb/1-upload-deposit/80-what-are-the-size-limitations-of-zenodo
- HTRC access and Data Capsules: https://htrc.atlassian.net/wiki/spaces/COM/pages/43286644/Troubleshooting+and+FAQs
- EEBO-TCP downloads: https://textcreationpartnership.org/?p=50
