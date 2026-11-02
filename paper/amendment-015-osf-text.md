# Amendment 15: story skeletons

*Filed 2026-11-01. Evidence: `docs/skeleton-plan.md`, `data/semantic/skeleton/check.json`.*

---

**Amendment 15, filed 2026-11-01, before any event has been extracted from the Book of Mormon, a
proposed source, a control or a retelling.** It adds a story-level comparison to 5.5's semantic
parallels, registered separately in Amendment 14. No hypothesis, decision rule or threshold of
section 6 changes.

**Events.** Every compared text is cut into consecutive blocks of at most 2,000 words. A hosted
model (claude-sonnet-5-5) lists, in order, at most 12 events of each block as short sentences with
personal and place names replaced by roles, or NONE for a block with no story. Model-assisted
extraction, simulated. The extractor was checked first on 20 seeded King James narrative chapters
extracted twice (pass marks set before the run: median agreement between runs at least 0.6, at
least 90% of events found in the chapter by a second model reading): median agreement 0.92, 233
of 238 events supported.

**Alignment.** Events are embedded with bge-small-en-v1.5 and match at cosine 0.700 or above (the
99th percentile of cosines between events of unrelated check chapters). Two texts are compared by
Smith-Waterman local alignment of their event sequences (match +1, mismatch and gap -0.5); order
is tested by shuffling the source's events within the aligned span 1,000 times.

**Comparisons.** The 1830 Book of Mormon against the named proposed sources (*View of the
Hebrews*, *The Late War*, Spalding's *Manuscript Story*, *The First Book of Napoleon*), each
ranked within its Amendment 14 control group, and against the 20 strongest sources of the
whole-corpus passage search. A source stands out when it scores highest in its group with an order
p-value at most 0.01.

**Positive control.** Whiston's Josephus (Antiquities I-V) against King James Genesis-Judges, the
*Testaments of the Twelve Patriarchs* against Genesis 37-50, and Ilive's *Jasher* against
Genesis-Joshua, each also aligned with 20 unrelated narrative books (fiction or history, not religious) of similar length from
its date window. The test is shown to work if Josephus and the *Twelve Patriarchs* each align
with their biblical source above all 20, with order p-value at most 0.01; otherwise the Book of
Mormon comparisons are reported without interpretation. Amendment 9's separation is not
computable for this test (2,000 volumes per draw is too many to read) and is reported as such.
