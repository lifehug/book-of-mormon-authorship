# Adding a researcher (for the owner and the AI)

Say "let's add Steve" in Claude Code and the `lab-add-researcher` skill walks through this page.
The AI does the steps marked **AI**; the ones marked **Owner** need the owner's hands, because
they create a credential or change who can see private material.

> **HathiTrust approved adding researchers on 2026-11-18** (ticket GS-17502,
> `docs/hathitrust-email-thread-GS-17502.md`): the data may be shared directly with them, and each
> one reads and signs the researcher agreement and is added to the one the owner signed. So the
> order is fixed: **agreement signed (step 4) before the key (step 5).**

## Before starting, the AI asks for

- the researcher's full name and GitHub username;
- what they will work on (one line, for the record);
- their country and their institution, if any (the agreement asks for both; see the note under
  step 4).

## Steps

1. **AI: record the request.** Add a row to `data/private/lab/researchers.md` (private): name,
   GitHub username, date, what for, and a status column for each step below. Commit and push the
   private repository.
2. **AI, after the owner says yes in this conversation: public repository.**
   `gh api -X PUT repos/lifehug/book-of-mormon-authorship/collaborators/<user> -f permission=push`
   The researcher gets an email invitation. `master` is protected, so they work by pull request.
3. **AI, after the owner says yes: private repository.**
   `gh api -X PUT repos/lifehug/bom-authorship-data/collaborators/<user> -f permission=push`
   This shows them the licensed texts held there. Confirm with the owner each time; an earlier
   yes for another person does not carry over.
4. **Owner: the HathiTrust researcher agreement.** Send the researcher the form you signed on
   2026-10-16 (it has slots for Researchers 2 to 4) and point them at
   `docs/hathitrust-researcher-agreement.md`. They fill in their slot and sign; you return the
   form to HathiTrust by replying on ticket GS-17502. File the signed copy in the private
   repository at `data/private/lab/agreements/` (never in the public one: it carries contact details).
   The AI records the date in the researcher's row. Two things in the form to check with the
   person first:
   - it has three more slots. A fourth added researcher needs a word with HathiTrust;
   - its point 7 says that if the first researcher is entitled to broader access than another
     (the form's example is a collaborator outside the United States), the data stays on the first
     researcher's machines. If the person is outside the United States, ask HathiTrust on the
     ticket before sending any data.
5. **Owner, after step 4: the read-only B2 key.** In the Backblaze console,
   https://secure.backblaze.com/app_keys.htm, choose **Add a New Application Key**:
   - Name: `lab-<user>` (one key per person, so one can be revoked alone)
   - Allow access to bucket: `bom-authorship-index`
   - Type of access: **Read Only**
   - Leave file-name prefix empty; set a duration if the access is for a fixed time
   Copy the key ID and the key (shown once) into a password manager and send the researcher a
   share link from there. Do not paste either into this conversation, email or chat. The AI
   never sees the key.
6. **AI: send the researcher the start page.** Give the owner a short message to forward: the
   links to `docs/lab/README.md` and `docs/lab/access.md`, and their folder
   `data/private/lab/<user>/`.
7. **AI: make their folder.** Create `data/private/lab/<user>/README.md` (name, date, what for)
   in the private repository; commit and push. Update the row from step 1.

## Checking it worked

Ask the researcher to run, and send back the last line of each:

```
uv run pytest -q
python -m lab.registry views
python -m lab.passages status
python -m lab.door find "a people led across the sea" --question --top 3
```

## Removing someone

1. **Owner:** delete their key `lab-<user>` in the Backblaze console.
2. **AI, after the owner says yes:**
   `gh api -X DELETE repos/lifehug/bom-authorship-data/collaborators/<user>` and the same for the
   public repository if wanted.
3. **Owner:** ask them to delete their copy of the corpus and confirm, and tell HathiTrust on
   ticket GS-17502 that they have left the project.
4. **AI:** mark the row in `data/private/lab/researchers.md` with the date removed.
