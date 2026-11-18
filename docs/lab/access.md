# Getting access to the data

> **Status: approved by HathiTrust, 2026-11-18** (ticket GS-17502): the data may be shared
> directly with additional researchers, provided each one reads and signs the researcher
> agreement and is added to the one the owner signed. No key is issued before that signature.
> The agreement's wording: `docs/hathitrust-researcher-agreement.md`.

The code and results are public. The books themselves are not: they are about 914 GB on the
owner's machine, with a private copy on Backblaze B2. A researcher works from their own copy,
fetched with a key that can read the bucket and do nothing else.

## What you ask for

Write to the owner (Dave Taylor) with:

1. your name and GitHub username;
2. what you want to look at, in a sentence or two;
3. how much disk you have (the minimum set is about 290 GB; everything is 914 GB);
4. your country and your institution, if you have one. The agreement asks for both, and
   HathiTrust must be told if either changes.

## What you sign first

Read `docs/hathitrust-researcher-agreement.md` (the eight points, then "What it means in plain
words"). The owner sends you the form he signed, with a slot for you: name, signature, date,
institution, title, email and phone. Sign it and send it back to him; he returns it to HathiTrust
on ticket GS-17502. Your key is made after that.

## What you get

1. **Write access to the public repository** `lifehug/book-of-mormon-authorship`, to open pull
   requests. `master` is protected: changes land by pull request with the owner's approval.
2. **Access to the private repository** `lifehug/bom-authorship-data` (cloned into
   `data/private/`). It holds the licensed texts and the lab's notes. Your notes go in
   `data/private/lab/<you>/`.
3. **A read-only B2 key** for the bucket `bom-authorship-index`, sent to you through a password
   manager's share link, never by email or chat. It is made once your signed agreement is back.

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

- The HathiTrust researcher agreement you signed, in full. The points below restate the parts
  that touch daily work and extend them to the other licensed sources.
- The texts are for this project. Do not pass the files, the key or passages of licensed books
  to anyone else, and do not put them in a public repository, a paper's supplement or a chat
  with a hosted AI service that keeps what it is sent.
- If the owner tells you a volume must be deleted (HathiTrust can require this), delete it and
  confirm.
- When your part in the project ends, delete your copy and tell the owner; the key is revoked.
- Never commit the key. Never paste it into a conversation.
