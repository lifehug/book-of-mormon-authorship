# Setting up the Mac mini as the project's data machine

The Mac mini (M4, 10-core, 16 GB, 256 GB internal plus a 2 TB external SSD) is the single home
for `data/`, for every long-running job, and for the blind run's sealed key. The desktop and
this repo stay the source of truth for code; the mini is the source of truth for data. Do this
once when the machine arrives.

The external SSD is required: the 256 GB internal disk cannot hold the corpora. Until it is
mounted, Phase 1 pulls that fit in the free internal space may run against `data/` directly and
be moved afterwards. See `docs/budget.md` sections 1, 4b and 4c for the hardware decision and
for which jobs this machine cannot run on 16 GB.

## 1. Base tools

```sh
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git gh uv poppler
gh auth login
```

`poppler` provides `pdftotext`, which `scripts/fetch_1830.sh` needs.

## 2. Make it reachable and keep it awake

- System Settings, General, Sharing: turn on Remote Login (SSH). Add the desktop's public key
  to `~/.ssh/authorized_keys` on the mini.
- Give it a fixed name: System Settings, General, Sharing, Local hostname, for example
  `bom-mini`, and a static IP or DHCP reservation on the router.
- Prevent sleep so jobs run overnight: `sudo pmset -a sleep 0 disksleep 0` and, in Energy
  settings, "Start up automatically after a power failure".
- Optional: on the desktop, add to `~/.ssh/config`:

  ```
  Host bom-mini
      HostName bom-mini.local
      User dave
  ```

## 3. Clone and verify

```sh
mkdir -p ~/Workspace && cd ~/Workspace
git clone git@github.com:lifehug/book-of-mormon-authorship.git
cd book-of-mormon-authorship
uv sync --dev
uv run ruff check . && uv run pytest -q
```

## 4. Storage

The external SSD is `/Volumes/bomdata`, 2 TB, **APFS case-sensitive and journaled**. Format it
that way; exFAT as shipped is not journaled, which is a poor fit for multi-day ingests, and it
is case-insensitive, so volume IDs across corpora can collide:

```sh
diskutil eraseDisk APFSX bomdata GPT /dev/diskN   # check diskN with: diskutil list external
```

**Split the tree by what git tracks, not by data versus code.** Everything git tracks stays on
the internal disk; only large untracked artifacts go to the SSD, one symlink per directory:

```sh
mkdir -p /Volumes/bomdata/data
mv data/corpus /Volumes/bomdata/data/corpus
ln -s /Volumes/bomdata/data/corpus data/corpus
```

| Stays internal | Goes to the SSD |
| --- | --- |
| `.git`, all code, `docs/`, `paper/` | `data/corpus/` — raw corpora, about 88 GB for Institutional Books alone |
| `data/bom/`, `data/kjv/`, `data/catalog/`, `data/manifests/`, `data/candidates/` | Phase 2 cleaned, normalized and masked copies, 300-500 GB |
| `data/private/` — its own git clone, 253 MB | Phase 4-5 embeddings and FAISS index, 50-100 GB |
| | Models and checkpoints, 50 GB |

The whole repo without `data/corpus` is about 745 MB, so there is nothing to gain by moving it,
and two things to lose. First, 49 tracked files live under `data/`; if they sit on a removable
drive then every time it is unplugged git reports 49 deletions, and one `git commit -a` or
`git add -A` in that state commits the catalogs out of the repo. Second, with the SSD detached
you can still read manifests, inspect catalogs, run the tests and write code — only the bulk
text goes dark.

Repeat the `mv` plus `ln -s` for each new large output directory as later phases create them.
Check `git status` is clean afterwards; `.gitignore` already covers `data/*`, so the symlinks
are not committed.

Moving a directory back from the SSD to the internal disk can fail on a name collision that was
legal on a case-sensitive volume. That is the only direction the case-sensitivity difference
bites.

Backups: the SSD is a single point of failure. Raw corpora are re-fetchable, slowly; the Phase 2
derived copies are not, being days to weeks of CPU. Point the off-site copy budgeted in
`docs/budget.md` section 1 at the derived data first. The manifests stay in git on the internal
disk, so any copy anywhere can be verified.

## 5. Credentials

Credentials live outside the repo, one file each, mode 600. Create them on the mini the same
way they exist on the desktop (copy with `scp`, never commit, never paste into a chat):

```
~/.config/osf/token            OSF personal access token (amendments)
~/.config/huggingface/token    Hugging Face write token (account: etherfuse)
~/.config/runpod/token         RunPod API key (GPU rentals)
~/.codex/auth.json             Codex CLI, ChatGPT OAuth -- written by `codex login`, not by hand
```

```sh
mkdir -p ~/.config/osf ~/.config/huggingface ~/.config/runpod
chmod 700 ~/.config/osf ~/.config/huggingface ~/.config/runpod
printf '%s' 'PASTE_TOKEN_HERE' > ~/.config/<service>/token && chmod 600 ~/.config/<service>/token
```

**One standard, no exceptions.** Every credential is a single file at
`~/.config/<service>/token`, mode 600, outside the repo. Not a `.env`, not an environment
variable, not a line in a config file that might get committed. A repo `.env` was used briefly
on 2026-10-20 and its contents moved here; `.gitignore` now covers `.env` and `.env.*` so a
fresh clone on another machine is protected too, but the convention is the file, not the
ignore rule.

Status, verified 2026-10-20: OSF authenticates as David Taylor, Hugging Face as `etherfuse`,
RunPod as `user_3KkRO15NW` with a $0.00 balance -- **credit is needed before BOM-27**. Codex
authenticates through a ChatGPT subscription rather than an API key, so it has no token file;
`codex exec` works and is used as the adversarial labeller in BOM-12.

There is no general-purpose LLM API key on this machine. Labelling the whole 560k-row catalog
needs one (budget section 3 allows $100-200); Codex via the subscription is fine for validation
samples of a few hundred but would take ~45 days for the full corpus and is not the tool for it.

## 6. Get the data

Public data comes with the clone. Licensed data comes from the private data repo:

```sh
scripts/data_clone.sh          # clones lifehug/bom-authorship-data into data/private/
uv run python -m metadata.manifest verify data/bom data/manifests/bom.jsonl
uv run python -m metadata.manifest verify data/private/bom data/manifests/bom-private.jsonl
```

From then on, `git -C data/private pull` and `git -C data/private push` keep the two machines
in step; the public repo never sees that directory. Re-fetching from the sources is always
possible too (`scripts/fetch_1830.sh`, `uv run python -m ingest.jsp printers|original`).

`data/bom/SOURCES.md` lists every source and its rebuild command.

## 7. Running long jobs

Run anything that takes more than a few minutes under `nohup` or `tmux` so it survives the SSH
session:

```sh
brew install tmux
tmux new -s ingest
uv run python -m ingest.jsp printers 2>&1 | tee logs/jsp_printers.log
# detach with Ctrl-b d; reattach with: tmux attach -t ingest
```

Keep a `logs/` directory (gitignored) for job output.

## 8. Backup

Off-site copy of `data/` per `docs/budget.md`: a Hugging Face dataset repo for derived data
that is public, or object storage for the rest. Manifests make any copy verifiable.

## 9. Claude Code on the mini

Either drive the mini over SSH from a Claude Code session on the desktop, or install Claude
Code on the mini and run sessions there for the long jobs. Both work; the repo is the shared
state. The blind run (BOM-32) must be run on the mini in a fresh session that has never seen
the sealed key.

## 10. Corpus pulls queued for this machine

Run each under tmux. All are resumable; rerun the same command after any interruption.

Status, 2026-10-16: the BOM-07 pull is **done** — 9,831 shards, 31,958 volumes, 73 GiB, no
failures, 11h38m wall. `data/corpus/` lives on the SSD. BOM-09, BOM-10 (the remaining states)
and BOM-11 are still queued.

Disable Spotlight on the SSD before the next pull. Indexing 73 GiB of plain text built an
index of roughly 57 GiB — bigger than half the corpus — and competes for I/O with the ingest:

```sh
sudo mdutil -i off /Volumes/bomdata && sudo mdutil -E /Volumes/bomdata
```

```sh
# Harvard Institutional Books, 1780-1830 English slice (BOM-07): DONE 2026-10-16. 73 GiB on disk
# (37 GiB raw OCR + 37 GiB cleaned, both kept), ~700 GB of transfer, 31,958 volumes, 11h38m.
# First accept the dataset terms on huggingface.co with the account whose token is in
# ~/.config/huggingface/token (institutional/institutional-books-hl).
uv run python -m ingest.institutional_books pull 2>&1 | tee logs/ib_pull.log
# Two OCR versions are kept, one file per volume: text_src (Harvard's raw OCR) and
# text_gen (their cleaned OCR). There is no combined text/ directory; manifest each.
uv run python -m metadata.manifest build data/corpus/institutional_books/text_src -o data/manifests/institutional_books_src.jsonl
uv run python -m metadata.manifest build data/corpus/institutional_books/text_gen -o data/manifests/institutional_books_gen.jsonl

# Text Creation Partnership: EEBO, Evans, ECCO (BOM-11): ~25 GB, 61,315 texts, no account.
uv run python -m ingest.eebo_tcp pull 2>&1 | tee logs/tcp_pull.log
uv run python -m metadata.manifest build data/corpus/tcp/text -o data/manifests/tcp.jsonl

# Internet Archive OCR, 1780-1830 English, skipping titles already in Harvard (BOM-09): roughly 250,000 items, ~80 GB, no account. Polite: 1 request/second.
# Run it under the supervisor, not directly: the pull stops itself when it believes the
# Archive is rate-limiting, and that judgement has been wrong twice. The supervisor restarts
# after any exit while the work list is still shrinking, and gives up only when a restart
# makes no progress at all -- which is what a real rate limit looks like.
nohup sh scripts/ia_supervise.sh > logs/ia_supervise.log 2>&1 &
uv run python -m metadata.manifest build data/corpus/internet_archive/text -o data/manifests/internet_archive.jsonl
```

```sh
# Chronicling America newspapers 1800-1830 (BOM-10): 159,146 pages of OCR text (est. 2-5 GB), no account; ~1-2 days at the rate limit.
# Text service limit is 150 requests/minute; the default delay keeps under it. Failures go to
# data/corpus/chronicling_america/failed.txt. Add --states NY,PA,OH to do the priority states first.
uv run python -m ingest.chronicling_america pull 2>&1 | tee logs/ca_pull.log
uv run python -m metadata.manifest build data/corpus/chronicling_america/text -o data/manifests/chronicling_america.jsonl
```

Then commit the four manifests and close BOM-07, BOM-09, BOM-10 and BOM-11 with the counts.
