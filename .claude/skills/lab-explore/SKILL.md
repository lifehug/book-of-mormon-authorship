---
name: lab-explore
description: Answer a question about the 1780-1830 library by searching and reading it through the lab's door. Use when someone asks what the corpus holds or says about a topic, author, book, phrase or idea, or wants to browse for ideas.
---

# Explore the library

Read `docs/lab/README.md` once per session if you have not. Then:

1. **Restate the question in one line** and say which rule set you will search and why
   (`python -m lab.registry views` lists them; default `borrowing` for meaning search,
   `readable` for exact phrases, `everything` for "do we hold it?").
2. **Search through the door only** (`python -m lab.door ...`). Never open files under
   `data/corpus/` directly, and never write there.
   - an idea or theme: `find "<text>" --question` (add `--year`, `--genre`, `--author`)
   - a passage someone pasted: `find --file <file>` (no `--question`)
   - exact wording or a rare name: `phrase "<words>"` with a narrowing filter
   - what we hold by a person or title: `works --author "surname, forename"` / `--title`
   - to read around a hit: `read WORK_ID --passage N --count 3`
3. **Try more than one wording.** Meaning search misses exact names; phrase search misses
   paraphrase. Use both when it matters, and say which found what.
4. **Report** in plain words: what was found, each work cited as *author, title, year,
   work id, passage number*; how many works were searched; what was not searched (works with no
   text, newspapers under `borrowing`, anything outside the rule set).
5. **Be honest about strength.** A score near 1.0 is the same wording; about 0.6 is the same
   topic. A hit is a lead to read, not a finding. Point to `docs/lab/lessons.md` when a lead
   looks like one of them (for example a match that is only shared biblical language).
6. **Quoting text:** short quotations in the conversation are fine. Anything saved that quotes a
   passage goes to `data/private/lab/<user>/` (use `--save NAME`), never to a public file.

If the question is really "is this true?" or "who wrote this?", it is a test, not a search:
offer `lab-new-test`.
