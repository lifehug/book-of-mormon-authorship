# Working rules for this repository

Read this first in every session. It is the handoff between machines and sessions.

## What this is

An open, pre-registered computational study of the authorship, borrowing, and dating of the
earliest Book of Mormon text. One person (Dave Taylor, GitHub `lifehug`) plus AI. The plan is
39 GitHub issues, `BOM-01` to `BOM-39`, worked strictly one at a time. `README.md` explains
the project; `docs/backlog.md` is the plan; `paper/preregistration.md` is frozen on OSF at
https://osf.io/6ugxc/ and changes only by dated amendment in its section 11.

## Framing (do not drift)

- The project does not argue for or against divine inspiration. It identifies close
  candidates or their absence, with the evidence. Keep that language out of every file.
- Every review step (adversarial review, draft review, peer review) is simulated by an AI
  model and must be labeled as simulated wherever it is mentioned.
- The Book of Mormon text is sealed from all model training and tuning until BOM-32, except
  the published-method replications in BOM-22.

## How to find the next task

```
gh issue list --state open --limit 100 --json number,title --jq '.[] | "\(.number) \(.title)"'
```

Work the lowest-numbered open `BOM-NN` issue whose "Depends on" issues are all closed. Read
the issue body (it holds the goal, checklist, and done-when). If an issue is half done, its
comments say what remains. "Continue" or "move forward" means: pick that issue and do it.

## How to finish a task

1. Code goes in the pipeline package that owns the stage (`ingest/`, `metadata/`, ...). Each
   package README names its issues.
2. `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` must pass before
   any commit. Never commit with failing tests.
3. Every dataset gets a checksum manifest: `uv run python -m metadata.manifest build <dir> -o
   data/manifests/<name>.jsonl`. Every data directory gets a `SOURCES.md` saying where each
   file came from and how to rebuild it.
4. Commit with a message that names the issue (`BOM-NN: ...`) and push to `master`.
5. Tick the issue's checkboxes, close it with a comment carrying the evidence (counts, paths,
   commit), and append to `paper/blog.md` (see below).
6. Nothing public or irreversible beyond that without asking: no force-push, no publishing
   data or models, no OSF amendments, no spending on GPUs.

## Where data lives

| Path | What | In git? |
| --- | --- | --- |
| `data/<dataset>/` | public source texts and derived tables | yes |
| `data/catalog/` | small indexes of the big corpora | yes |
| `data/manifests/` | checksums for everything, public and private | yes |
| `data/private/` | licensed texts that cannot be redistributed | separate private repo `lifehug/bom-authorship-data`, cloned by `scripts/data_clone.sh`; never add to this repo |
| `data/corpus/` | large corpora (Harvard Institutional Books, TCP) | no git at all; local disk, tracked by manifests |

Harvard's Institutional Books text may never be published (terms: noncommercial, no
redistribution, attribution required). Joseph Smith Papers transcripts are copyrighted.

## Machines

The Mac mini is the data machine: `data/corpus/` and long jobs live there, run under tmux
(`docs/mac-mini-setup.md`). Credentials are files, never in git or chat:
`~/.config/osf/token`, `~/.config/huggingface/token` (account `etherfuse`, terms accepted for
`institutional/institutional-books-hl`), `~/.config/runpod/token`. A rented H100 (RunPod)
is used only for the BOM-27 base-model run.

## The blog

`paper/blog.md` is a long, informal, first-person post in Dave's voice that explains what is
being done and why. Update it whenever an issue closes or a decision is made, with one to
three concrete examples pulled from the real data (a paragraph diff, a catalog row, an OCR
snippet, a number), including wrong turns. Add a dated line to its Log section. Voice: plain,
conversational, short sentences, concrete, no jargon.

## Conventions

- Issue references are `BOM-NN`, never `#N` (GitHub #1-#10 are the old 2016 items).
- Fetchers identify themselves, rate-limit, and resume from what is on disk.
- Commit messages end with the Claude co-author line the harness supplies.
