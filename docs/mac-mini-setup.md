# Setting up the Mac mini as the project's data machine

The Mac mini (M5 Pro, 64 GB, 1 TB plus a 2 TB external SSD) is the single home for `data/`,
for every long-running job, and for the blind run's sealed key. The desktop and this repo stay
the source of truth for code; the mini is the source of truth for data. Do this once when the
machine arrives.

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

Mount the external SSD and point `data/` at it, so the internal disk stays free:

```sh
mkdir -p /Volumes/bomdata/data
rm -rf data && ln -s /Volumes/bomdata/data data
mkdir -p data/manifests
git checkout -- data   # restores the committed files (manifests, SOURCES.md, 1830/)
```

Check that `git status` is clean afterwards; the symlink itself must not be committed.

## 5. Credentials

Credentials live outside the repo, one file each, mode 600. Create them on the mini the same
way they exist on the desktop (copy with `scp`, never commit, never paste into a chat):

```
~/.config/osf/token            OSF personal access token (only needed for amendments)
~/.config/huggingface/token    Hugging Face write token (account: etherfuse)
~/.config/runpod/token         RunPod restricted API key (base-model run only)
```

```sh
mkdir -p ~/.config/osf ~/.config/huggingface ~/.config/runpod
chmod 700 ~/.config/osf ~/.config/huggingface ~/.config/runpod
# then scp each token file from the desktop and chmod 600 it
```

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

```sh
# Harvard Institutional Books, 1780-1830 English slice (BOM-07): ~44 GB on disk per OCR version (raw and cleaned, both kept), ~700 GB of transfer, 31,958 volumes.
# First accept the dataset terms on huggingface.co with the account whose token is in
# ~/.config/huggingface/token (institutional/institutional-books-hl).
uv run python -m ingest.institutional_books pull 2>&1 | tee logs/ib_pull.log
uv run python -m metadata.manifest build data/corpus/institutional_books/text -o data/manifests/institutional_books.jsonl

# Text Creation Partnership: EEBO, Evans, ECCO (BOM-11): ~25 GB, 61,315 texts, no account.
uv run python -m ingest.eebo_tcp pull 2>&1 | tee logs/tcp_pull.log
uv run python -m metadata.manifest build data/corpus/tcp/text -o data/manifests/tcp.jsonl

# Chronicling America newspapers 1800-1830 (BOM-10): 159,146 pages of OCR text (est. 2-5 GB), no account; ~1-2 days at the rate limit.
# Text service limit is 150 requests/minute; the default delay keeps under it. Failures go to
# data/corpus/chronicling_america/failed.txt. Add --states NY,PA,OH to do the priority states first.
uv run python -m ingest.chronicling_america pull 2>&1 | tee logs/ca_pull.log
uv run python -m metadata.manifest build data/corpus/chronicling_america/text -o data/manifests/chronicling_america.jsonl
```

Then commit the three manifests and close BOM-07, BOM-10 and BOM-11 with the counts.
