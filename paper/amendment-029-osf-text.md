# Amendment 29: the dating classifier's transformer cross-check (BOM-29)

*Filed 2026-11-06. Evidence: `docs/dating-plan.md`, `dating/transformer.py`.*

---

**Amendment 29, filed 2026-11-06, before any transformer feature is computed or fitted.** Amendment
2 registers "a transformer variant reported alongside as a cross-check" of the dating classifier
without saying which transformer or how. It is fixed as follows; the grammar model alone still
decides 6.4 and H3 (Amendment 19), and nothing here changes it.

**Transformer.** The time-locked 297M base model (BOM-27), the only transformer available to the
study whose training never included the Book of Mormon (a general modern model would have read
it, which 4.2 forbids). It reads each segment as the grammar model does (folded tokens of the
printed text), in 512-token windows; the segment's features are its final hidden states
mean-pooled over all windows and tokens (960 numbers).

**Classifier and validation.** The same segments, 31 bins, author-grouped split, regularised
multinomial logistic regression with its penalty chosen by author-grouped cross-validation, and
the same validation as the registered models: held-out authors by era, 6.4 as amended per volume,
King James imitation (pseudo-biblical controls and the King James text), and Amendment 9's
known-answer separation. Added, because the language model was trained on 1780-1830 volumes:
held-out 1780-1830 volumes in its training split are reported separately from those that were not,
so any advantage from having seen a text shows.
