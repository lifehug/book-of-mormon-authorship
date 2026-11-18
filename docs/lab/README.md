# The lab: start here

The study is finished and its results are pinned (git tag `study-v1`). The lab is the place to
explore the same data and try new ideas without touching any of that.

## What you can do

| You want to | Use |
| --- | --- |
| See what we hold | `python -m lab.door works --author "wroe, john"` |
| Read a book or a passage | `python -m lab.door read WORK_ID --passage 40` |
| Find passages by meaning | `python -m lab.door find "a people led across the sea" --question` |
| Find an exact phrase | `python -m lab.door phrase "curious workmanship" --year 1800-1830` |
| See what a kind of test may use | `python -m lab.registry views` |

With Claude Code open in this repository you can also just ask. Four skills carry the steps:

| Say | Skill | What happens |
| --- | --- | --- |
| "What does the library say about ...?" | `lab-explore` | searches and reads through the door, cites every work |
| "Set up a test of ..." | `lab-new-test` | writes a one-page test card, checks the method on known answers first, then runs it |
| "Where does the paper's 59% come from?" | `lab-replicate` | traces a published number to its results file and reruns it |
| "This should go in the study" | `lab-promote` | opens an issue for the owner; merges nothing |

## The three pieces

1. **The registry** (`data/lab/registry.parquet`): one row for each of the 695,021 catalogued
   works, with the facts a test filters on. Nothing is left out: a work with no text, a reprint, a
   newspaper page, an anonymous pamphlet each has a row and a column that says so.
   [The data map](data-map.md) lists the columns.
2. **Rule sets** (`lab.views` in `config/preregistered.yaml`): named lists of conditions on the
   registry, one per kind of test. Every command takes `--view NAME`, and a result records the
   one it used. Add a rule set by adding a line to the config.
3. **The door** (`lab/door.py`): the one way lab work reads the corpus. It only reads.

## The rules

- **Read anything; write only to lab folders.** Lab code never writes to the study's results,
  config or paper. `lab.paths.out` enforces this and a test in the build checks it.
- **Text stays private.** Anything that quotes a passage goes in `data/private/lab/<you>/` (the
  private repository), never in this public one. Names, ids, counts and scores are public.
- **Known answers first.** A new method is run on books whose author or source is known before
  it is run on the Book of Mormon. A result with no measured hit rate is a lead, not a finding.
- **Say which rule set.** "Among which works?" must have a one-word answer.
- **Spending is the owner's call.** Estimate rented-GPU cost before asking; never run it unasked.
- Read [the lessons](lessons.md) before designing a test. Each one cost us a wrong turn.

## Setting up

1. Get access: [access.md](access.md).
2. `uv sync --dev`, then `scripts/data_clone.sh` (the private repository).
3. `scripts/lab_fetch.sh minimum` (about 290 GB), then `python -m lab.passages status`.
4. `uv run pytest -q` should pass.

What each data folder is: [`docs/holdings.md`](../holdings.md). Every command in the study:
[`eval/README.md`](../../eval/README.md). The findings: [`paper/paper.md`](../../paper/paper.md).
