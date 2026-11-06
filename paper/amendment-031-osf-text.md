# Amendment 31: the imitation-robustness test (BOM-31)

*Filed 2026-11-06. Evidence: `docs/imitation-plan.md`, `eval/imitation.py`.*

---

**Amendment 31, filed 2026-11-06, before the imitation test is scored.** Section 9 sets each
method's weight from its accuracy at identifying known authors from their imitation-biblical
writing; Amendment 7 found three such authors (Snowden, Dodsley, Kenrick) and added exact
intervals and an equal-weight synthesis. The bands are unchanged. This fixes the test itself.

**Candidates and tests (forward; sets the weights).** Each dual-register author's ordinary
writing is a candidate, beside 10 distractor authors drawn by seed (`bom31-distractors`), 5 from
each of the history and general-prose control lists: personal names, not curated imitation
authors, one non-newspaper volume of at least 10,000 words each. Dodsley's reference leaves out
a copy of his own *Oeconomy of Human Life* that the catalog title hid, three anthologies he
edited, and two second copies (listed in `imitation.exclude_reference_titles`). Tests are every
non-overlapping 5,000-word window of each imitation work (Snowden's two volumes, Dodsley's
*Chronicle of the Kings of England* and *Oeconomy of Human Life*, Kenrick's *Whole Duty of Woman*):
18 tests.

**Reverse (reported only).** Candidates are imitation texts (the three authors' and every other
curated imitation author with at least 10,000 words); tests are the three authors' ordinary
writing, at most 10 seeded 5,000-word windows each.

**Methods.** Burrows' and Cosine Delta, General Imposters (general-prose pool, no candidate's
works) and ENSC at the benchmark's own calibration (not refitted); the style embeddings; the
authorial language models at the working size chosen from the benchmark (primary, V1, V3; V2 only
if it is the working variant). Accuracy is pooled over the forward tests and reported with its
exact 95% interval and n, per author, and as the count of authors identified in most of their
tests; section 9's bands apply to the pooled forward accuracy.

**Disclosure.** While the code was being checked, before this filing, a smoke test displayed one
number: Cosine Delta without General Imposters, 0.72 forward and 0.29 reverse. No choice above was
changed after it was seen.
