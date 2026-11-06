# Release plan (BOM-37)

Written 2026-11-06. Goal (issue): anyone can rerun every result and browse the findings. Done when
a fresh machine reproduces the headline results from the release and the explorer is live.
Publishing is the owner's call at each step below; nothing here has been published.

## What goes where

| What | Where | Licence | State |
| --- | --- | --- | --- |
| Code, config, pre-registration and amendments, catalogs, manifests, derived public tables, result JSON, paper | GitHub `lifehug/book-of-mormon-authorship`, a tagged release | code MIT (`LICENSE`), derived data CC BY 4.0 (`LICENSE-DATA`) | public now; tag at release |
| Archived snapshot of the tagged release (code + `data/` as tracked) | Zenodo, via its GitHub integration, one DOI per release | as above | to do: enable the integration, cut the tag |
| Time-locked models 125M, 297M, 1B (BOM-27) | Hugging Face `etherfuse/timelocked-1830-{125m,297m,1b}` with cards (sources and terms, Book of Mormon exclusion, training config, loss curves, limits) | CC BY-NC 4.0 (owner, BOM-66) | 125M public; 297M and 1B approved, upload by `timelocked_lm.release` (1B by `scripts/after_1b.sh`) |
| Style encoder (BOM-30), dating models (BOM-29), candidate and control models (BOM-28) | Hugging Face, same account | CC BY-NC 4.0 | **owner to decide**: the candidate models are fine-tuned on Joseph Smith Papers text (copyright Intellectual Reserve) and may need to stay private; the style encoder and dating models are trained on the same corpus as the published base models |
| Results explorer | GitHub Pages from `explorer/` (the repo root served, so the page reads the result files directly) | as the data | to do: enable Pages |

## What stays private, and how to obtain it

Exactly the three restricted sources of `docs/replication.md` (Harvard Institutional Books text,
HathiTrust text, Joseph Smith Papers transcripts and page images), the bulk corpora under
`data/corpus/` (checksummed in `data/manifests/`), the PAN data, and every artifact made of
their text in another form (token files, passage packs, encoded inputs, the sealed blind set).
The steps to obtain each source are in `docs/replication.md`; a release adds nothing to them.

## Pre-release checklist

Run `python scripts/release_check.py`; it checks 1-7 automatically and exits non-zero on a failure.

1. Result files hold names and numbers only (BOM-58's size guard in `tests/test_results_hold_no_text.py`,
   widened: no string over 400 characters except the project's own notes).
2. The explorer's panels all load from the current files and show no long text.
3. Nothing private is tracked: no file under `data/private/` or `data/corpus/`, no weights.
4. `LICENSE` and `LICENSE-DATA` exist.
5. Every tracked data directory has a `SOURCES.md`.
6. Manifests parse, and tracked files match their manifest checksums (a mismatch is a stale
   manifest: rebuild it with `metadata.manifest build`).
7. Everything is committed and pushed.

By hand:

8. **Clean-clone replication.** On a fresh machine: clone, `uv sync`, obtain the sources by
   `docs/replication.md`, verify them against the manifests, and rerun the headline results
   (the benchmark table, the borrowing searches' named-source ranks, the triage counts, the blind
   run's unblinded output and the synthesis). Record the time each took and any step that did not
   work from the docs alone.
9. Model cards: every published model's card names its sources, terms, exclusions and limits.
10. The paper's numbers each cite a file in the tagged release.

## The explorer

`explorer/index.html` is one static page with no build step. `explorer/panels.json` lists its
panels: each reads one public result file and shows it as a sortable table with a short plain
explanation (benchmark, prior work and head-to-head tests, candidate models, imitation, named
sources in the paraphrase search, triage, dating, manuscript corrections, access). The sweep,
the blind run and the synthesis are listed as pending until their files exist. The page never
holds or fetches corpus text, and `tests/test_release_check.py` checks every panel against the
current files.

To view it locally: `python -m http.server 8000` from the repository root, then open
`http://localhost:8000/explorer/`.

The issue also asks for clicking a Book of Mormon passage to see its parallels, scores and dating.
Showing the passage needs only the public-domain 1830 text, but its parallels are passages of the
licensed corpus, which cannot be shown; the page can show each parallel's source title, year and
score, with a link to the source where it is public (Internet Archive, TCP). That view waits for
the blind run's per-chunk outputs, which carry the dating and attribution scores per passage.
