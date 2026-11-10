# Amendment 43: Book of Mormon quotations dropped from candidate samples (BOM-28, BOM-32)

*Filed 2026-11-10. Post hoc. Evidence and decision record: `docs/bom-overlap-analysis.md`.*

---

**Amendment 43, filed 2026-11-10, post hoc: found after unblinding, decided after seeing which
samples were affected.** The sealing rule (4.2) was enforced on the training corpus but not on
candidate samples. Oliver Cowdery's pre-1830 sample ("Articles of the Church of Christ", June
1829) is 40% word-for-word Book of Mormon text and Parley P. Pratt's books quote it; the candidate
models ranked Cowdery's sample closest to most chunks, which is leakage. Every run a candidate
sample shares with the Book of Mormon's narrative was classed (biblical; period stock phrasing;
written before the matching passage was dictated; in the same weeks; or after it), and only
quotations are dropped: passages of shared runs (each at least 8 words, gaps of at most 5 words
merged) at least 20 words long, written after the matching passage was dictated
(`candidates.bom_quotation`). Masking every shared run was rejected because it would remove
genuine shared idiom, above all from Joseph Smith's 1828-29 revelations, which contain no
quotation by this rule and are unchanged. Masked: Cowdery's Articles 494 words, Pratt 1,696,
Cowdery's Messenger and Advocate 151, one Joseph Smith letter of 1833 24. The candidate models are
retrained and the sealed set rescored by every method that reads candidate samples; results are
reported beside the registered run (git tag blind-registered-2026-11-10), not in place of it.
