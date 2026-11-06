# Amendment 28: the author sweep's units, index, calibration and expected false leads (BOM-39, BOM-47)

*Filed 2026-11-06. Evidence: `docs/sweep-plan.md`.*

---

**Amendment 28, filed 2026-11-06, before any author is indexed or any calibration query is
scored.** It fixes what sections 5.6 and 6.6 leave open for the corpus-wide author sweep (BOM-39)
and commits, before the sweep, how its expected false-lead count is measured (BOM-47). The lead
rule of 6.6 is unchanged.

**Units.** Every normalised catalog author in the 1780-1830 window with text, a personal name and
no corporate term (the style-embedding rules of Amendment 24), with at least 10,000 words in
non-duplicate volumes (the section 7 floor). Each author's profile is a sample of up to 20
blocks of 1,000 words, spread round-robin over the author's works (title groups) at seeded
positions, BOM-15 normalised, with KJV quotation masked by BOM-16's frozen settings.

**Signals.** Classical: Cosine Delta on the 300 most frequent words of the author profiles (present
in at least 20% of them), z-scored on the profiles. Embedding: the BOM-30 encoder's vector of the
text as one episode, cosine distance. Each is a separate signal.

**Query.** The Book of Mormon's discovery-half 5,000-word chunks (BOM-17; 22 chunks); an author's
distance is the mean over chunks. Calibration queries are cut and averaged the same way, using at
most 22 chunks.

**Calibration.** 200 books by 200 different authors drawn (seed `bom39-calibration`) from the
authors held out of the style encoder's training who are swept and keep 10,000 words outside the
book; a book is one title group of at least 5,000 words, and its author's profile is rebuilt from
their other works. Recorded per signal: the true author's rank among all swept authors, and the
best false-match distance with the true author removed. The sweep is usable if the true author
ranks first in at least 70% of queries under each signal separately (the reading under either
signal is also reported). The lead threshold under each signal is the 5th percentile of
best-false-match distances.

**Expected false leads (BOM-47).** Leave-one-out over the 200 queries: thresholds from the other
199, count of non-true authors beating both. Its mean is the expected false-lead count for a query
whose author is absent; a lead count at or below the counts' 95th percentile is unremarkable,
above it surprising, and observed leads are reported against this. The signals' Spearman
correlation (over authors, and over best-false scores) is reported; independence is not assumed.
The section 3 plausibility gate is applied, blind to scores, to 100 random swept authors (seed
`bom47-gate`); their pass rate times the expected count is the number of leads expected to
survive the gate by chance.
