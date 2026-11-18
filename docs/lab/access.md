# Getting access to the data

> **Status: waiting for verification.** The owner has asked HathiTrust to approve adding
> researchers to the project. Until he confirms that approval, no read-only key is issued and
> step 3 below is not carried out. Steps 1 and 2 can be done now. (Recorded 2026-11-18.)

The code and results are public. The books themselves are not: they are about 914 GB on the
owner's machine, with a private copy on Backblaze B2. A researcher works from their own copy,
fetched with a key that can read the bucket and do nothing else.

## What you ask for

Write to the owner (Dave Taylor) with:

1. your name and GitHub username;
2. what you want to look at, in a sentence or two;
3. how much disk you have (the minimum set is about 290 GB; everything is 914 GB).

## What you get

1. **Write access to the public repository** `lifehug/book-of-mormon-authorship`, to open pull
   requests. `master` is protected: changes land by pull request with the owner's approval.
2. **Access to the private repository** `lifehug/bom-authorship-data` (cloned into
   `data/private/`). It holds the licensed texts and the lab's notes. Your notes go in
   `data/private/lab/<you>/`.
3. **A read-only B2 key** for the bucket `bom-authorship-index`, sent to you through a password
   manager's share link, never by email or chat. *(Waiting for verification, see above.)*

## Using the key

Save it as `~/.config/backblaze/credentials`, readable only by you (`chmod 600`):

```
B2_KEY_ID=...
B2_APP_KEY=...
B2_BUCKET=bom-authorship-index
```

Then, from the repository:

```
brew install rclone            # or your system's package manager
scripts/lab_fetch.sh minimum   # every text, the meaning index, the fast index: about 290 GB
python -m lab.passages status
```

`scripts/lab_fetch.sh <folder>` fetches anything else; `docs/holdings.md` lists the folders.

## What you agree to

- The texts are for this project. Do not pass the files, the key or passages of licensed books
  to anyone else, and do not put them in a public repository, a paper's supplement or a chat
  with a hosted AI service that keeps what it is sent.
- If the owner tells you a volume must be deleted (HathiTrust can require this), delete it and
  confirm.
- When your part in the project ends, delete your copy and tell the owner; the key is revoked.
- Never commit the key. Never paste it into a conversation.
