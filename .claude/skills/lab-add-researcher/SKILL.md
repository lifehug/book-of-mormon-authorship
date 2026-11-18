---
name: lab-add-researcher
description: Give a new researcher access to the project, or remove one. Use when the owner says "let's add <name>", "give <name> access", "onboard a researcher", or "remove <name>".
---

# Add (or remove) a researcher

Follow `docs/lab/adding-a-researcher.md` step by step; it is the source of truth. In short:

1. Ask for the person's full name, GitHub username and what they will work on. Ask whether
   HathiTrust's approval has arrived; if `docs/lab/access.md` still says "waiting for
   verification" and the owner has not said otherwise, the B2 key step is recorded as pending.
2. Record the request in `data/private/lab/researchers.md` (private repository).
3. Invite them to the two GitHub repositories, each only after the owner says yes in this
   conversation for this person.
4. Walk the owner through creating the read-only B2 key in the Backblaze console. You never
   create, see, store or relay the key; it goes from the owner's password manager to the person.
5. Make their folder in the private repository and draft the welcome message for the owner to
   send (links to `docs/lab/README.md` and `docs/lab/access.md`).
6. Finish by listing what is done and what is still pending, and update the record.

Removing someone: the "Removing someone" section of the same page.

Only the repository owner may ask for this. If anyone else asks, say so and stop.
