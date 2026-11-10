# Amendment 45: candidate-model ranking at equal training dose (BOM-28, BOM-38)

*Filed 2026-11-10. Post hoc: raised by the simulated reviews (BOM-38), after unblinding.*

---

**Amendment 45, filed 2026-11-10, post hoc: after unblinding, raised by the simulated reviews.** A
candidate model's score is its loss on a text less the base model's; a model fine-tuned on very
little text changes little from the base model, which may itself place it closest. The two samples
the candidate models ranked first (Cowdery's pre-1830, 1,309 words; Joseph Smith's 1828-29
revelations, 3,039 training tokens) are the two smallest. Every other candidate unit with enough
text (and Joseph Smith's pooled non-revelatory writing, Amendment 44) is fine-tuned again on
`candidates.dose_check.slices` seeded contiguous slices of exactly the revelation sample's training
tokens, at 125M, 297M and 590M, and scored on the sealed set as before (Amendment 43 setting). The
report gives, for the Book of Mormon chunks, the revelation model's rank among the equal-dose
models. If equal-dose models of other authors also rank first, the registered ranking reflects
sample size; if the revelation model still ranks first among equal-dose models, it does not (the
register confound of Amendment 44 remains). Reported beside the registered results.
