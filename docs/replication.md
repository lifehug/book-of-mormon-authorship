# How to replicate this corpus

Every text this project uses is obtainable by anyone. None of it is redistributed from this
repository, because three of the sources forbid that — but no source is closed, and the access
path for each is written down below and in the per-source documents it links to.

This is the normal arrangement for research on restricted data. Clinical trials, census
microdata, UK Biobank and dbGaP all work this way: the protocol, the code and the *access
procedure* are published, and a qualified researcher applies for the data themselves. What
makes a study checkable is that the path exists and is open, not that the bytes are in the
repository.

What is committed here: every catalog (695,021 works catalogued, 533,328 with text on disk — the
second figure is the corpus any analysis sees; `data/catalog/`), a checksum manifest for
every file ever pulled (`data/manifests/`), the public-domain base texts, all ingest code, the
analytic config, and the pre-registration with its amendments. A replicator uses the manifests
to prove they obtained the same bytes we did.

## The sources

| Source | Access | Turnaround | Rebuild |
| --- | --- | --- | --- |
| Internet Archive | open, no account | immediate | `python -m ingest.internet_archive pull` |
| EEBO/Evans/ECCO (TCP) | open, no account | immediate | `python -m ingest.eebo_tcp pull` |
| Chronicling America | open, no account | immediate | `docs/chronam-bulk-download.md` |
| KJV | public domain, committed | — | in `data/kjv/` |
| Harvard Institutional Books | free Hugging Face account, accept dataset terms | minutes | `python -m ingest.institutional_books pull` |
| Joseph Smith Papers | open website, transcripts under copyright | immediate | `python -m ingest.jsp printers` and see `data/bom/SOURCES.md` |
| HathiTrust | signed researcher agreement, approved proposal, allow-listed IP | days | `docs/hathitrust-request.md` |
| New York newspapers | per-title, mostly open archives | varies | `docs/new-york-newspapers.md` |

Five of the eight need no permission at all. One needs a free account and a click. One is a
public website whose text is copyrighted, so we publish the fetcher rather than the text. Only
HathiTrust requires an application, and `docs/hathitrust-request.md` records exactly what to
send, to whom, and what obligations come back with it.

## The only three things you must obtain yourself

Everything else in this project is published. These three are not, and for each one the steps
below are the whole procedure. None of them is discretionary on our side: we hold these back
because of a signed agreement, accepted terms, or copyright — not by preference.

### 1. HathiTrust public-domain volumes

A signed researcher agreement. Days, not minutes, and the only item here with a wait.

1. Email `support@hathitrust.org` with a short proposal: researchers (name, affiliation,
   country), which dataset you want, the research you intend, what outputs you will produce,
   how those outputs will be used, and permission to share the proposal.
   Ours is committed verbatim at `docs/hathitrust-email-thread-GS-17502.md`, so you can copy
   the shape of one that worked.
2. Sign and return the researcher agreement they send. We wanted the **non-Google** dataset,
   `ht_text_pd_open_access`; obligations summarised in
   `docs/hathitrust-researcher-agreement.md`.
3. On approval, give them a static IP. A dynamic one can be allow-listed instead if you ask.
4. Pull with `python3 ingest/hathitrust_rsync/ht_pull.py`. Transfer details in
   `docs/hathitrust-rsync-instructions.md`. Exit code 23 is expected: roughly 76,000 of the ids
   are Google-digitized and absent from this dataset.

Note the obligation that comes with it: deletion notices must be honoured, and the text may not
be redistributed. Ours expires 2026-11-30; yours will have its own window.

### 2. Harvard Institutional Books 1.0

A free account and a click. Minutes.

1. Create a Hugging Face account.
2. Open https://huggingface.co/datasets/institutional/institutional-books-hl and accept the
   dataset terms — noncommercial use, no redistribution, attribution required.
3. Put the token in `~/.config/huggingface/token`.
4. `python -m ingest.institutional_books pull`. About 73 GiB on disk and ~700 GB of transfer,
   because each shard is one row group so there is no row-level pushdown.

### 3. Joseph Smith Papers transcripts

No permission needed, no account, no wait. The site is open; the transcripts are simply
copyrighted by Intellectual Reserve, so we publish the fetcher rather than the text.

1. `python -m ingest.jsp printers` and `python -m ingest.jsp original`.
2. They land in `data/private/bom/`, and `data/bom/SOURCES.md` documents what each file holds.
3. Verify against `data/manifests/bom-private.jsonl`, which is public, so you can confirm you
   obtained the same bytes we did without access to anything of ours.

## The scripts and the paperwork are both committed

A fetcher is committed for every source, so nothing has to be reconstructed from a description:

| Source | Fetcher |
| --- | --- |
| Internet Archive | `ingest/internet_archive.py` (plus `scripts/ia_supervise.sh`) |
| HathiTrust | `ingest/hathitrust.py` (catalog), `ingest/hathitrust_rsync/ht_pull.py` (rsync pull) |
| Harvard Institutional Books | `ingest/institutional_books.py` |
| TCP | `ingest/eebo_tcp.py` |
| Chronicling America | `ingest/chronicling_america.py`, `scripts/chronam_status.py`, `scripts/chronam_move.sh` |
| Joseph Smith Papers | `ingest/jsp.py` |
| KJV, 1830 edition | `ingest/kjv.py`, `ingest/edition_1830.py` |
| New York newspapers | `ingest/advantage_archive.py`, `scripts/nyshn_browser_pull.py` |

The HathiTrust application is committed too, not just described: `docs/hathitrust-request.md`
(the process), `docs/hathitrust-email-thread-GS-17502.md` (the actual correspondence, so the
shape of a successful proposal can be copied), `docs/hathitrust-researcher-agreement.md` and
`-summary.md` (the obligations that come back with approval), and
`docs/hathitrust-rsync-instructions.md` (the transfer itself). The requester's own email address
and IP are withheld; the institutional contacts are public-facing and are kept, because a
replicator needs to know who to write to.

## What each one costs you

Transfer and disk, from our own run (`docs/budget.md` has the full accounting):

| Source | On disk | Notes |
| --- | --- | --- |
| Internet Archive | 99 GiB | 249,906 items, 99.48% of those catalogued |
| HathiTrust | 19 GiB | 31,194 volumes; 21,810 duplicate the Archive pull |
| Harvard Institutional Books | 73 GiB | 31,958 volumes, two OCR versions, ~700 GB of transfer |
| TCP | 22 GiB | 61,310 texts, XML and extracted text |
| Chronicling America | 4.4 GiB | 158,960 pages, from bulk batches not the per-page API |
| **Total** | **~241 GB** | |

Every fetcher resumes from what is on disk, identifies itself, and respects rate limits.

## Verifying you got the same thing

```
python -m metadata.manifest verify data/corpus/<source> \
    --manifest data/manifests/<source>.jsonl
```

The manifests are the point of the whole arrangement: they let a replicator prove byte-level
agreement with our corpus without anyone having to ship 241 GB, and they make divergence
visible rather than silent.

Divergence will happen over time, and that is expected rather than a defect. Internet Archive
items are withdrawn, bulk endpoints move, and our own HathiTrust rsync access ends 2026-11-30
(a replicator applies for their own, which is the point). A manifest mismatch tells you a
volume has gone, so a replication can report what it could not obtain instead of quietly
analysing a different corpus.

## Checking results without obtaining anything

A second, lower bar: `BOM-44` publishes the derived tables the analyses actually consume —
n-gram document frequencies, feature matrices, genre labels, OCR scores. These are not
reconstructable back into readable text, so the licences that forbid redistributing the corpus
do not reach them. With those published, the statistical claims can be re-run by anyone at all,
with no application and no 241 GB.

That is a convenience, not the basis of the replicability claim. The claim rests on the access
paths above.

## The honest residual

A replicator whose HathiTrust application is refused cannot check the HathiTrust-derived
results. This is true of all gated-data research and is not disqualifying, but it is real, and
it is why `BOM-44` matters: the derived tables are the only artifact that depends on no
gatekeeper and does not decay.
