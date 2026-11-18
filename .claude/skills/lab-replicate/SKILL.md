---
name: lab-replicate
description: Trace a number or claim in the paper, blog or README to the results file and command behind it, and rerun it when asked. Use for "where does this number come from", "can you reproduce", "check this figure".
---

# Replicate a published number

1. **Find the claim** in `paper/paper.md` (or `paper/blog-phase1.html`, `README.md`) and quote
   the sentence.
2. **Find its results file.** The text usually names it; otherwise search `data/` for the value
   and `eval/README.md` for the command that writes the file. Give: file, the key inside it, the
   command, and the git commit and config hash stamped in the file.
3. **Compare** the published figure with the file's value, to the precision printed. Say plainly
   if they differ.
4. **Rerun only if asked**, and say first what it needs (texts, a model, time). Write the rerun's
   output under `data/private/lab/<user>/replicate/`, never over the study's file; then compare.
5. **A mismatch is a finding.** Report it, do not fix it: open an issue titled
   `Replication: <claim>` with both numbers and the commands, or use `lab-promote`.
