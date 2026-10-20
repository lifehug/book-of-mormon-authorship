# HathiTrust researcher agreement, non-Google-digitized (BOM-08)

This is the form HathiTrust asks a researcher to sign before it opens rsync access to the
`ht_text_pd_open_access` dataset. It is kept here so anyone repeating this study can see what
they will be asked to agree to. The signed copy is not in the repository (it carries personal
contact details); the wording below is HathiTrust's standard form as received on ticket
GS-17502, "Research dataset request: public domain English text, 1780-1830
(ht_text_pd_open_access)".

Companion file: `docs/hathitrust-request.md` (the request process and the proposal as sent).

## Timeline

| Date | Step |
| --- | --- |
| 2026-10-15 | Proposal emailed to support@hathitrust.org from <requester address, withheld> |
| 2026-10-15/16 | HathiTrust opened ticket GS-17502 and sent the non-Google-digitized researcher agreement |
| 2026-10-16 | Agreement signed (David James Taylor, independent, United States) and returned |
| pending | Approval, static IP registration, rsync of the volume list |

## What the form says

Title: "Researcher Agreement for HathiTrust Dataset". Each participating researcher signs.
By signing, the researcher acknowledges and confirms eight points:

1. The texts come from HathiTrust at the University of Michigan.
2. The data will be used only as described in the research proposal submitted with the
   agreement.
3. rsync access covers only volumes HathiTrust has determined to be public domain, plus
   volumes licensed under Creative Commons. Some may later be found to be in copyright; the
   researcher agrees to delete those on notice and to confirm the deletion to
   support@hathitrust.org.
4. Because deletions may be requested later, the researcher may not distribute the dataset
   to others. HathiTrust welcomes other researchers requesting the same dataset themselves.
5. rsync access lasts only for the duration of the project in the proposal, and the dataset
   must be deleted before that period ends.
6. The dataset must be deleted at any time on HathiTrust's specific request.
7. If the primary researcher (Researcher 1) is entitled to broader access than the others,
   the data goes only to computers under Researcher 1's control at the primary institution;
   the other researchers get no rsync access and the data is not moved or copied elsewhere.
   The example given: a US-affiliated Researcher 1 with a non-US collaborator means only
   Researcher 1 receives and holds the data.
8. If the scope or nature of the research changes, or any researcher's physical address or
   institutional affiliation changes, HathiTrust must be notified, and the terms may change.

Signature block: Researcher 1 is "the responsible permanent full-time faculty or staff
member", with name, signature, date, institution, title, institutional email, and phone.
Slots for Researchers 2-4 are optional.

## What it means in plain words

- The text is a loan for this project, not a gift. When the project ends, it gets deleted.
- Do not share the files. Point people at HathiTrust and they can ask for the same set.
- HathiTrust may later say "that volume turned out to be in copyright"; the file is deleted
  and the deletion is confirmed by email.
- The agreement is tied to the proposal: the 1780-1830 authorship study. A different study
  needs a new notice to HathiTrust, as does a move or a change of affiliation.
- The data lives on the machines of the person who signed. Here that is the Mac mini (and
  the laptop while the mini is busy), with a static IP registered with HathiTrust.
- The form assumes a university employee. This project filled in "Independent" as the
  institution and left the title blank; whether that is accepted is what the ticket will
  tell us.

## How this project complies

- Downloaded text stays in `data/corpus/hathitrust/`, which is outside git and listed as
  non-redistributable in `CLAUDE.md`. Only manifests (checksums and volume IDs) are
  published.
- Deletion notices are handled by removing the volume files and the matching manifest rows,
  with the deletion confirmed to support@hathitrust.org and logged in `data/catalog/SOURCES.md`.
- Models trained on the corpus must not reproduce text (already a condition of the
  preregistration and of the Harvard Institutional Books terms).
- The dataset is deleted at the end of the study (the OSF registration gives the window).
