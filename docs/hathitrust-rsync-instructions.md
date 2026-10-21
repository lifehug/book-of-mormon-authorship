# HathiTrust dataset rsync instructions

Source: https://github.com/hathitrust/datasets/wiki/Dataset-rsync-instructions (read 2026-10-20).
Linked from Janet Swatscheno's approval email on ticket GS-17502.

## Prerequisites

Works in bash on Linux and macOS (PowerShell on Windows). Needs a working rsync. On macOS use
Homebrew rsync (`brew install rsync`, binary at /opt/homebrew/bin/rsync); Apple's bundled
openrsync mishandles `--files-from` against this server.

## Syncing a full dataset (not what we do; ours is a subset)

```
rsync --copy-links --delete --ignore-errors --recursive --times --verbose datasets.hathitrust.org::$TREE $LOCAL_PATH
```

`$TREE` is the dataset name. Ours is `ht_text_pd_open_access`.

## Syncing a list of IDs (our case)

### Step 1: turn volume IDs into pairtree paths

`id_list.txt`: one HathiTrust volume ID per line, plain text, Unix line endings, no URL
escaping or quotes.

With Python (`pip install pairtree`), save as `ids_to_ppath.py`. Quoted verbatim from
HathiTrust's wiki, including its own formatting -- `ingest/hathitrust_rsync/ht_pull.py`
reimplements it and was verified against the `pairtree` library on all 107,178 ids:

```text
import sys, pairtree;
for line in sys.stdin:
  (n,i) = line.strip().split('.',1);
  print("/".join([n, 'pairtree_root', pairtree.id2path(i), pairtree.id_encode(i)]))
```

```
python ids_to_ppath.py < id_list.txt > path_list.txt
```

Ruby and Perl one-liners exist too (`gem install pairtree` / CPAN `File::Pairtree`).

`ht_pull.py` in this folder does this step without the package; its output was checked
against the `pairtree` library for every one of the 107,178 ids with zero differences.
Examples:

```
nyp.33433074917927        -> nyp/pairtree_root/33/43/30/74/91/79/27/33433074917927
uc2.ark:/13960/t1zc7t220  -> uc2/pairtree_root/ar/k+/=1/39/60/=t/1z/c7/t2/20/ark+=13960=t1zc7t220
uc1.$b627059              -> uc1/pairtree_root/$b/62/70/59/$b627059
```

### Step 2: sync

```
rsync --copy-links --delete --ignore-errors --recursive --times --verbose --files-from=path_list.txt datasets.hathitrust.org::ht_text_pd_open_access $LOCAL_PATH
```

`ht_pull.py` runs the same command without `--delete` (nothing to delete on a first pull, and
it protects a partial tree) and with `--partial`, timeouts and a log file instead of
`--verbose`.

## What arrives

Per volume, inside its pairtree directory: `<encoded id>.mets.xml` (structure and page
metadata) and `<encoded id>.zip` (one plain-text OCR file per page). HathiTrust's
`ht-text-prep` library (https://github.com/htrc/ht-text-prep) strips running headers and
footers from the page files if we want that later.

## Access notes

- rsync access is tied to the public IP HathiTrust allow-listed (<your allow-listed IP>). From any
  other address the daemon connection just times out: `rsync error: timeout waiting for daemon
  connection (code 35)`. That is the symptom of a non-allow-listed IP, not a server outage.
- Access is granted for about a month and is removed on 2026-11-30.
- IDs that are not in the dataset (for us: all Google-digitized volumes) produce
  `link_stat ... failed: No such file or directory` lines and a final exit code 23. Expected.
