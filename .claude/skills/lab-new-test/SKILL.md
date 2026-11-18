---
name: lab-new-test
description: Turn an idea into a properly set-up test on the corpus - a one-page test card, a known-answer check, then the run. Use when someone says "set up a test", "can we check whether", "test the idea that", or proposes a new method or comparison.
---

# Set up a test

The aim is that a new idea is tested the way the study's own tests were: the rule fixed first,
the method proved on known answers, the result reported with its hit rate.

1. **Read** `docs/lab/lessons.md` and `docs/lab/test-card.md`. Check `docs/method-improvements.md`
   and `eval/README.md` for whether this was already tried; if it was, say so and show the result
   before doing anything new.
2. **Write the test card** with the person, at `data/private/lab/<user>/<date>-<slug>/card.md`.
   Do not start code until every line is filled, above all: the rule set, the known-answer
   check, and what counts as yes and as no. Ask at most the two or three questions the card
   cannot be filled without; propose defaults for the rest.
3. **Say the cost** before running: your minutes, machine time, rented GPU. Rented GPU needs the
   owner's approval of an amount, every time.
4. **Build small.** Put code in `data/private/lab/<user>/<date>-<slug>/` or, if it is reusable and
   quotes no text, in `lab/` with a test in `tests/`. Reuse the study's modules by importing
   them; never edit them, `config/preregistered.yaml`'s existing values, or any file under
   `data/` outside `data/lab/` and `data/private/lab/`. New settings go under `lab:` in the
   config. All writes go through `lab.paths.out`.
5. **Known answers first.** Run the method on the card's known cases. If it misses the bar,
   stop and report that; do not run the real target "to see".
6. **Run the real target** under the named rule set. Keep the Book of Mormon out of any
   training or tuning. Record the rule set, the config hash (`metadata.config.stamp()`) and the
   git commit in the output.
7. **Report** in this order: the answer in one sentence; the numbers beside the known-answer hit
   rate; the decoy check; what it does not show; the next step that would settle a lean.
   Complete the card's Result section. Commit the private repository.
8. If the result deserves a place in the study, offer `lab-promote`. Do not edit the paper,
   the blog or the study's results yourself.
