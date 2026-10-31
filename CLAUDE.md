# Working rules for this repository

Read this first in every session. It is the handoff between machines and sessions.

## What this is

An open, pre-registered computational study of the authorship, borrowing, and dating of the
earliest Book of Mormon text. One person (Dave Taylor, GitHub `lifehug`) plus AI. The plan is
49 GitHub issues, `BOM-01` to `BOM-49`, worked strictly one at a time. `README.md` explains
the project; `docs/backlog.md` is the plan; `paper/preregistration.md` is frozen on OSF at
https://osf.io/6ugxc/ and changes only by dated amendment in its section 11.
`docs/audit.md` is the 2026-10-20 design review of the whole plan and the source of
`BOM-43` to `BOM-49`; read it before changing method or scope.

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

## Say what you are doing and why (read this before starting anything)

**Show the reasoning, not a label.** Any of these is fine with the owner — a better method, an
assumption on the way to one, or a turn down a different path — provided the logic can be
followed *while it happens*. Explaining it afterwards is worth little: by then the time has
already been spent.

So at every change of direction, say these four things in a breath, in plain language:

1. what I was doing,
2. what I hit,
3. what I am doing instead,
4. why that still answers the same question — or that it does not.

Worked example, which is how 2026-10-21 should have read: *"Page images are blocked by
Cloudflare. The bulk archives carry ALTO XML, which has the OCR engine's own per-word confidence.
That would give a quality figure for all 158,960 pages without reading any images, so it answers
the same question more cheaply. Trying that."* Two sentences, and the owner can agree or redirect
before any time is spent. None of it was said.

**The test is therefore: can I state in one line what I am doing and how it serves the task?** If
that line cannot be written, stop. If it can, write it down before doing the work, not in the
summary afterwards.

A better method is welcome and should be raised. If a cheaper or stronger route to the *same
answer* appears, say what it is, why it is better, and what it costs — then take it. That is not a
detour. What is not welcome is changing route without saying so.

When something turns up mid-task, say which of these it is, out loud, before acting:

1. **A better route to the same answer.** Name it and proceed. (Reading OCR confidence out of the
   ALTO instead of reading page images: a legitimate attempt to answer the same question without
   the expensive step.)
2. **It blocks the task.** Fix it and carry on.
3. **A different problem.** Stop. Say that the task is now paused and why, and let the owner
   choose. Data at risk or a rule broken belongs here: report it, do not quietly fix it and
   continue. (The extractor deleting source archives was a real and serious find — and it was a
   different problem from the question being asked.)
4. **Merely interesting.** Say plainly *"this does not serve the task"*, write it down as an
   issue, and ask before doing any of it. Explicit permission, never inferred from an earlier
   related yes or from the work being cheap.

**Announce every change of route.** The failure to avoid is not deviation, it is a silent switch:
the owner watching the work cannot tell whether they are seeing a better method or a wandering
one, and that is the thing that wastes their attention.

**Answer the asked question first**, and prefer the route that answers it soonest. A method that
promises more but has not yet produced the answer is not yet better.

**What this looked like when it went wrong, 2026-10-21.** Asked whether the Chronicling America
OCR was good enough, the route went: page images blocked, so ALTO instead (category 1, and
reasonable, but never said aloud), ALTO found deleted (category 3, and a genuine problem, but
treated as a continuation rather than a stop), then a code fix, a guard test, a memory, a new
issue, docs and a blog entry — all before the question had any answer. The answer in the end took
one page image and twenty minutes, and it also showed ALTO had been the wrong instrument. Then,
with the question answered, a Tesseract benchmark got started that nobody had asked for
(category 4, no permission). Real work throughout; almost none of it narrated.

**One issue per concern.** BOM-50 ended up carrying ALTO recovery, OCR verification and a re-OCR
decision. Split them.

## How to finish a task

1. Code goes in the pipeline package that owns the stage (`ingest/`, `metadata/`, ...). Each
   package README names its issues.
2. `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` must pass before
   any commit. Never commit with failing tests.
   A new command goes into the run guide, `eval/README.md` (what it does, needs, writes, time);
   `tests/test_run_guide.py` fails the build if a module's Usage lists a command the guide lacks.
3. Every dataset gets a checksum manifest: `uv run python -m metadata.manifest build <dir> -o
   data/manifests/<name>.jsonl`. Every data directory gets a `SOURCES.md` saying where each
   file came from and how to rebuild it.
4. Commit with a message that names the issue (`BOM-NN: ...`) and push to `master`.
5. Tick the issue's checkboxes, close it with a comment carrying the evidence (counts, paths,
   commit), and append to `paper/blog.md` (see below).
6. Nothing public or irreversible beyond that without asking: no force-push, no publishing
   data or models, no spending on GPUs. **OSF amendments are the exception: file them without
   asking** (owner, 2026-10-31). Write the text to `paper/amendment-NNN-osf-text.md`, file it with
   `scripts/osf_amend.py`, record the revision in section 11 of `paper/preregistration.md` and in
   the config, and tell the owner afterwards. File before the results the amendment governs
   exist, and label anything decided after seeing results as post hoc.

## Where data lives

| Path | What | In git? |
| --- | --- | --- |
| `data/<dataset>/` | public source texts and derived tables | yes |
| `data/catalog/` | small indexes of the big corpora | yes |
| `data/manifests/` | checksums for everything, public and private | yes |
| `data/private/` | licensed texts that cannot be redistributed | separate private repo `lifehug/bom-authorship-data`, cloned by `scripts/data_clone.sh`; never add to this repo |
| `data/corpus/` | large corpora (Harvard Institutional Books, TCP) | no git at all; local disk, tracked by manifests |

**Everything is tracked somewhere; nothing lives in one place. Public by default.** Assume a
file may be published unless something says otherwise, and "otherwise" means a signed agreement
or an explicit request — not a guess about what a provider might prefer. Today that is exactly
three things: the HathiTrust researcher agreement, Harvard's accepted dataset terms, and the
Joseph Smith Papers transcripts, which are copyrighted by Intellectual Reserve. Those live in
the private repo, committed and pushed there rather than left on local disk. Everything else is
public, including page scans of public-domain material: a digitiser who asked for nothing has
not restricted anything. **Anything held back ships with the steps to obtain it** — numbered,
followable, naming who to write to and what to say. `docs/replication.md` carries those steps
for all three; a new restriction is not recorded until its procedure is written there too. Only the bulk corpora under `data/corpus/` stay out of both, because they
are hundreds of gigabytes and licensed; those are covered by checksum manifests, which are
public. `.gitignore` blanket-ignores `data/*` and re-includes per directory, so **a new data
directory is invisible to git until it is added to that list** — and `git status` will look
clean while it is missing, because ignored files do not appear there. Check `git ls-files` on a
new directory before believing it is committed.

Derived tables are kept, not regenerated on demand. The test is cost to reproduce, not whether a
file is derived: `genre.parquet` is tracked because it is about 40 hours of local model time, and
`catalog.parquet` is tracked because it is the join key every other published table needs. A
replicator who obtains the sources under their own agreements must be able to apply our labels
without re-running the pipeline (BOM-44).

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
- **A transient failure is never recorded as an answer, and every long job resumes itself.**
  Checkpointing to disk is not enough on its own: pass 2 checkpointed every 250 rows and did
  resume, but it wrote `PARSE_FAIL` for 3,027 records lost to a usage limit, and a resume then
  treated those as finished work. Keep the states distinct — not attempted, answered,
  genuinely unanswerable, and *failed transiently* — so a rerun picks the last one up with no
  flag and no human noticing. `metadata.genre._TRANSIENT` is the pattern for recognising an
  outage reply. Log the raw text of anything unparseable (`logs/parse_failures.jsonl`); a
  failure with no evidence cannot be diagnosed, and that run left none.
- **Long jobs commit their output as they go**, on a timer rather than per checkpoint, so a
  disk failure cannot cost days of model time and the history stays readable.
- **A finding that exists only in a chat window does not exist.** Before any pause — a restart, a
  context limit, the end of a sitting — the state goes into the repo and onto the issue: what is
  done, what remains, and anything measured along the way that would otherwise be lost. The issue
  comment is what a later session reads when told to keep going, so it carries the next action
  explicitly, not a summary of the past. `data/catalog/DEDUP.md` is the pattern: the dedup numbers
  are the lesser half, the limitation they revealed is the result.
- Commit messages end with the Claude co-author line the harness supplies.
- **Local compute and disk are cheap; rented GPU is not.** Up to about a week of wall time for
  a job on the mini is acceptable, and the SSD has 1.6 TB free. Prefer the accurate approach
  over the fast one, keep originals and intermediate artifacts, and flag rather than delete.
  Trade rented GPU hours into local hours wherever the job allows. See `docs/budget.md` 4b-i.
- **Never delete a source, and never extract only part of one.** No ingest deletes the archive,
  dump or download it read; deletion is opt-in and never the default. When an archive holds more
  than you need, take all of it — the Chronicling America extractor matched only `ocr.txt`,
  skipped every `ocr.xml`, and deleted the tarball, discarding the ALTO (per-word confidence and
  word coordinates) for 158,960 pages with no backup and 1.6 TB free. Re-obtaining it is 76
  manual downloads through Cloudflare. `tests/test_no_source_deletion.py` fails the build if a
  destructive call appears in the pipeline outside its allowlist; extend the allowlist with a
  reason rather than working around the test.
- **Never hard-code an analytic value.** Thresholds, cutoffs, chunk sizes, seeds and model
  choices come from `config/preregistered.yaml` via `metadata.config.load()`, and every output
  is stamped with `metadata.config.sha256_of_config()`. The file holds only choices already
  pinned in the pre-registration; its `pending_amendment` list names those still needing a
  dated OSF amendment, filed as in step 6 of "How to finish a task". A value not in the config and not in that
  list means you are about to invent one: add it to `pending_amendment` instead. BOM-40 extends
  the file to the remaining stages and adds the multiverse runner.
