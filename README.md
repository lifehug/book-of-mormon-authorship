# Book of Mormon Authorship

Who wrote the English text of the Book of Mormon, what earlier books does it echo, and what era
does its language belong to? This repository is a finished, open study of those three questions.
It holds the plan, the code, the result tables and the write-ups. Everything can be checked and
rerun.

The study does not argue for or against divine inspiration. A computer cannot answer that. It can
say whether the text looks like a particular person's writing, whether it borrows from particular
books, and how far the tools that say so can be trusted.

## Start here

| If you want | Read |
| --- | --- |
| The findings in plain words, with live charts (about 30 minutes) | https://lifehug.com/book-of-mormon (source: [`paper/blog-phase1.html`](paper/blog-phase1.html)) |
| The full paper, with every method and table | [`paper/paper.md`](paper/paper.md) |
| To rerun something | [`eval/README.md`](eval/README.md): every command, what it needs, what it writes, how long it takes |
| To get the texts we could not republish | [`docs/replication.md`](docs/replication.md) |
| The story of how it went, wrong turns included | [`paper/blog.md`](paper/blog.md) |

## What we found

Each line names the results file behind it. The paper gives the detail and the limits.

1. **The book copies almost nothing.** With King James Bible quotation set aside, 0.16% of it
   matches earlier print, all stock religious phrasing. The books usually named as sources
   (*The Late War*, *The First Book of Napoleon*, *View of the Hebrews*) do not stand out from
   other books of their kind, and no book in the library shares its plot
   (`data/reuse/`, `data/semantic/`).
2. **Among the eight people usually proposed, the closest writing is Joseph Smith's
   revelations.** Six of eight rankings put them first, including all three of our model sizes.
   His letters and journals do not stand out the same way (`data/blind/`).
3. **No tool can reliably say "it is none of these people."** We ran the published methods built
   for that job beside our own. Set to confirm 95% of true authors, the best one (ours) still
   accepts one wrong author in three; the bar was one in twenty (`data/sweep/nobody.json`).
4. **So we searched everyone: 23,872 authors of 1780-1830.** Joseph Smith's revelations come
   out first or second at every setting. The one author ahead of them, at one setting, is
   John Wroe, an English prophet who also published revelations. The rest of the top is
   religious testimony, and it holds more long-dead authors than chance would give
   (`data/sweep/bom_ranking.json`).
5. **The closest writing is a voice, not proof of a person.** Writers who could not have written
   the book score as close when they write in that voice. No tool we found, ours included, can
   separate a person from the voice they are writing in.
6. **The language dates early.** A grammar model places most of the text before 1700 (median
   1661); two other models say 1736 and 1755. Imitating the King James Bible pulls the grammar
   model about 53 years early, but the text still dates earlier than the period's other
   imitation scripture (`data/blind/unblinded.json`, `data/dating/h3c.json`).

## How far to trust it

- **Every tool was tested first on books whose author is known.** On 55 known authors our models
  pick the right one more often than each of the four older methods, at every model size
  (`data/benchmark/`).
- **The library search is not a lie detector.** On 727 known books it puts the true author first
  34% of the time and in its top ten 59% of the time. For a book unlike its author's other
  writing, those fall to 17% and 38% (`data/sweep/coverage_episodes_v2.json`).
- **Joseph Smith's writing from before 1830 is small**, and dictation and scribes sit between any
  author and the page.
- **One person did this with AI assistance.** There were no outside advisors and no journal
  review. Every review in the repository was written by an AI model and is labelled simulated.
  Mistakes are possible. The guarantee is that anyone can check and redo all of it; corrections
  by issue or pull request are welcome and will be recorded unchanged.

## Check it yourself

There are three levels, from least effort to most.

1. **Read the numbers.** Every chart and table in the write-ups names its results file under
   `data/`. Results files hold names and numbers only.
2. **Rerun the Book of Mormon ranking without training anything.** Download the candidate models
   below and follow the model sections of [`eval/README.md`](eval/README.md). No restricted text
   is needed.
3. **Rebuild everything.** The base models rebuild every other model from the code and config.
   Tests that read the books themselves need your own copy of the sources;
   [`docs/replication.md`](docs/replication.md) gives the steps for each.

```
uv sync --dev
uv run pytest -q
```

Requires [uv](https://docs.astral.sh/uv/). Every analytic choice (threshold, seed, model) lives in
`config/preregistered.yaml`, and every results file is stamped with that file's hash and the git
commit that made it.

## The models

On Hugging Face, CC BY-NC 4.0. Weights and the numbers they produced, never corpus text. Each
file's SHA-256 is in `data/manifests/hf_<repo>.jsonl`.

| Repository | What it holds | Use it for |
| --- | --- | --- |
| [`etherfuse/timelocked-1830-125m`](https://huggingface.co/etherfuse/timelocked-1830-125m), [`-300m`](https://huggingface.co/etherfuse/timelocked-1830-300m), [`-590m`](https://huggingface.co/etherfuse/timelocked-1830-590m) | three language models trained only on English printed 1780-1830, the Book of Mormon left out | rebuilding every other model |
| [`etherfuse/bom-authorship-candidate-models`](https://huggingface.co/etherfuse/bom-authorship-candidate-models) | one model per candidate's writing sample, at all three sizes | checking the candidate ranking (finding 2) |
| [`etherfuse/bom-authorship-dating-models`](https://huggingface.co/etherfuse/bom-authorship-dating-models) | the dating models | checking the dating result (finding 6) |
| [`etherfuse/bom-authorship-style-encoder`](https://huggingface.co/etherfuse/bom-authorship-style-encoder) | both style models: the first (`297m/`, `590m/`) and the second (`v2/`), which ran the library search | the candidate ranking's style scores; the library search (finding 4) and the "none of these" comparison (finding 3) |
| [`etherfuse/bom-authorship-benchmark-finetunes`](https://huggingface.co/etherfuse/bom-authorship-benchmark-finetunes) | an earlier set of known-author test models | checking the benchmark tables |

## The texts

The library is 695,021 catalogued works of 1780-1830, 533,328 with text, from the Internet
Archive, Harvard's Institutional Books, HathiTrust, the Text Creation Partnership and period
newspapers. Anyone can obtain all of it, but four sources cannot be republished from here:
HathiTrust, Harvard's collection, the Joseph Smith Papers transcripts, and one purchased book.
For each, [`docs/replication.md`](docs/replication.md) gives numbered steps to get the same
access we had, and the public checksums in `data/manifests/` let you confirm you hold the same
files. The tables the statistics read are published outright in `data/`.

**Corpus v1.1** (frozen 2026-10-30), the snapshot every analysis from BOM-21 on runs against: [doi:10.5281/zenodo.23819273](https://doi.org/10.5281/zenodo.23819273). It corrects placeholder dates (BOM-56) and adds the curated pseudo-biblical control (BOM-54); index `data/manifests/corpus_v1.1.json`. Corpus v1.0 (frozen 2026-10-28), still citable: [doi:10.5281/zenodo.23740903](https://doi.org/10.5281/zenodo.23740903) (all versions: [10.5281/zenodo.23740902](https://doi.org/10.5281/zenodo.23740902)). Index `data/manifests/corpus_v1.0.json`; coverage and gaps in `docs/datasheet.md`.

## The plan and its changes

The analysis plan was written and frozen before the results (https://osf.io/6ugxc/, 2026-10-15;
mirrored in [`paper/preregistration.md`](paper/preregistration.md)). Every later change is a dated
amendment in its section 11, and the ones made after seeing a result are labelled so. The library
search (finding 4) and the "none of these" comparison (finding 3) were added after the plan and
are labelled exploratory in the paper. [`paper/deviations.md`](paper/deviations.md) lists every
decision made after a result was seen.

## Repository layout

Each top-level package owns one stage and its README says what it does: `ingest/`, `metadata/`,
`ocr_fix/`, `kjv_mask/`, `segment/`, `classic/`, `reuse/`, `semantic/`, `timelocked_lm/`, `alm/`,
`dating/`, `style_embed/`, `sweep/`, `eval/`, `paper/`.

- `data/` holds public source texts, result tables and checksum manifests.
- `docs/` holds the background ([`docs/background.md`](docs/background.md)), the earlier studies
  ([`docs/prior-studies.md`](docs/prior-studies.md)), the record of what changed in the method
  ([`docs/method-improvements.md`](docs/method-improvements.md)) and design notes.
- GitHub issues titled `BOM-NN` are the working record; each closed one carries its evidence.

## License

Code: MIT (`LICENSE`). Derived data: CC BY 4.0 (`LICENSE-DATA`). Models: CC BY-NC 4.0. Source
texts keep their original licenses.

## History

This repository began in 2016 as a Java word-counting experiment on the 1830 text and Joseph
Smith's journals (David Taylor and John McConnell). That code is in the git history before the
October 2026 reset and is not used by the current project.
