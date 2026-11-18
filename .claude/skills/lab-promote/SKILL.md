---
name: lab-promote
description: Propose that a lab result, correction or new rule set be taken into the study itself. Use when someone says a finding "should go in the paper", wants to correct a published number, or wants a lab tool made part of the pipeline. Opens an issue; changes nothing in the study.
---

# Propose something for the study

Lab work never changes the study directly. This skill writes the proposal for the owner.

1. **Check it is ready:** a completed test card with a known-answer hit rate; outputs that hold
   no licensed text; the rule set, config hash and commit recorded.
2. **Open a GitHub issue** on `lifehug/book-of-mormon-authorship` titled `Lab: <one line>` with:
   the question; the result in two sentences; the known-answer hit rate; what it would change
   (which section of the paper, which results file); what it does not show; where the card and
   outputs are (path in the private repository, no quoted text in the issue).
3. **If code is involved,** open a pull request from a branch; never push to `master`. The build
   must pass (`uv run ruff check . && uv run ruff format --check . && uv run pytest -q`).
4. **Stop there.** The owner decides. A change of method in the study is recorded as a dated
   amendment in `paper/preregistration.md` section 11, by the owner's say only.
