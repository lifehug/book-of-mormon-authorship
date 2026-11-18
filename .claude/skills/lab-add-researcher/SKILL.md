---
name: lab-add-researcher
description: Give a new researcher access to the project, or remove one. Use when the owner says "let's add <name>", "give <name> access", "onboard a researcher", or "remove <name>".
---

# Add (or remove) a researcher

Follow `docs/lab/adding-a-researcher.md` step by step; it is the source of truth. In short:

1. Ask for the person's full name, GitHub username, what they will work on, and their country
   and institution (the HathiTrust agreement asks for both).
2. Record the request in `data/private/lab/researchers.md` (private repository).
3. Invite them to the two GitHub repositories, each only after the owner says yes in this
   conversation for this person.
4. The HathiTrust researcher agreement (approved route, 2026-11-18): the owner sends the person
   the form he signed; they sign their slot; he returns it on ticket GS-17502 and files the signed
   copy in `data/private/lab/agreements/`. Record the date. No key before this.
5. Walk the owner through creating the read-only B2 key in the Backblaze console. You never
   create, see, store or relay the key; it goes from the owner's password manager to the person.
6. Make their folder in the private repository and draft the welcome message for the owner to
   send (links to `docs/lab/README.md` and `docs/lab/access.md`).
7. Finish by listing what is done and what is still pending, and update the record.

Removing someone: the "Removing someone" section of the same page.

Only the repository owner may ask for this. If anyone else asks, say so and stop.
