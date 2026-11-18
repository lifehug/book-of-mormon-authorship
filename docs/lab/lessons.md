# Lessons already paid for

Each of these cost the study a wrong turn. Check a new test against them before running it.

1. **Voice is not a person.** The closest writing to the Book of Mormon is revelation and
   religious testimony, whoever wrote it. Writers who could not have written the book (dead before
   1829) score as close as living ones. A method must be shown to separate *people* within one
   kind of writing before its answer names anyone. (Paper 6, 14.)
2. **Count the dead.** 23% of library authors were dead by 1829. If the top of a ranking holds
   more dead authors than chance, it is ranking a kind of writing. Keep them in as decoys
   (rule set `author-search-all-lives`) and report the count.
3. **No tool says "none of these".** Every verifier we ran, ours and the published ones, accepts
   far too many wrong authors when set to confirm 95% of true ones. A top-ranked name is the
   closest on the list, not a match. (Paper 5.4; `data/sweep/nobody.json`.)
4. **Short texts are unreliable.** With two episodes of text the true author comes first 19% of
   the time; with a full profile 34%. State how much text each side had.
5. **A book unlike its author's other writing is hard to place.** Same-genre books: true author
   in the top ten 71% of the time. Cross-genre: 38%. Report the two separately.
6. **Mask the King James Bible first.** Shared biblical quotation looks like borrowing and like
   shared authorship. Every comparison in the study runs on text with it set aside (`kjv_mask/`).
7. **A match needs a baseline.** A count of shared phrases means nothing until the same count is
   taken for hundreds of ordinary books of the period. *The Late War* passes the rare-phrase rule
   and so does other imitation scripture. (Paper 3.)
8. **One book is not one vote per copy.** Reprints are grouped; use `dup_keeper`. Without it a
   popular book wins by being counted twenty times.
9. **Catalog dates are claims.** Some are wrong by decades. Use the registry's `year` (corrected),
   not `year_catalog`.
10. **A model has read what it was trained on.** Do not test a model on a book in its training
    set: check `training` and `author_style_split` in the registry, or use `known-answer`.
11. **The Book of Mormon was sealed from every model.** Keep it that way: never train or tune on
    it, and leave its copies (`sealed`) out of every search gallery.
12. **Model size did not help; more text did.** Bigger language models were no better at picking
    authors. Do not reach for a bigger model first. (Paper 5; `data/benchmark/list_size.json`.)
13. **Fix the rule before the result.** Write what would count as yes and as no on the test card
    before running. Anything decided after seeing numbers is labelled so.
14. **A transient failure is not an answer.** An outage, a timeout or an unreadable file is
    recorded as "not attempted", never as a negative.

The full record of what was tried and whether it worked: `docs/method-improvements.md`.
