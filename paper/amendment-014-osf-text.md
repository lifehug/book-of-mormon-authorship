# Amendment 14: semantic parallels

*Filed 2026-11-01. Evidence: `docs/semantic-plan.md`, `data/semantic/model_choice.json`,
`data/semantic/distractors_*.json`.*

---

**Amendment 14, filed 2026-11-01, before any Book of Mormon, candidate or known-answer passage
has been searched for semantic parallels.** It fixes how 5.5's "semantic parallels by sentence
embeddings and FAISS nearest-neighbor search at the passage level" is carried out. No hypothesis,
decision rule or threshold of section 6 changes.

**The index.** Every volume the corpus searches use (text, a date, deduplication keepers, OCR
exclusions applied, no newspapers; 278,796 volumes) is cut into consecutive 128-word passages of
its normalised text (a last passage under 32 words dropped) and embedded with
BAAI/bge-small-en-v1.5 in half precision. Date windows and exclusions are applied at search time,
so later date corrections need no rebuild. Search is exact inner product (no approximation).

**Model choice, on a known answer.** Five models were compared on the 1807 *New Translation of
the Book of Psalms* against the King James Psalms (443 queries, 7,970 passages): e5-base-v2 was
most accurate (right psalm first 73%) but would take about three weeks to index the corpus on the
project's machine; bge-small-en-v1.5 (69%) about a week. The test was repeated with one million
corpus passages added as distractors: bge-small found the right psalm first for 59% of queries
and in the top ten for 78%; re-scoring its candidates with e5-base made results worse the deeper
it went (51% first when re-scoring the top 1,000), and all-MiniLM-L6-v2 reached 45%. Every score
is therefore the bge-small cosine, with no second model.

**A parallel.** Query passages come from the full text, each labelled with its share of King
James wording (4.4). Each query's 100 nearest passages in its date window are retrieved; one is a parallel when its score exceeds the query's
highest score against 10,000 random passages from the same date window. Parallels to Bibles,
to King James wording, and to volumes whose dates were corrected under Amendment 12 are labelled
and listed, not dropped.

**Scores.** A source volume's score is the number of the target's query passages (King James
share at most 0.5) with a parallel in it, per 10,000 words. Its distinctiveness is its percentile
among 500 volumes from the same window, genre and length band (within a factor of 2), scored the
same way, with bootstrap intervals over query passages (10,000 resamples). The named proposed
sources (*View of the Hebrews*, *The Late War*, Spalding's *Manuscript Story*, *The First Book of
Napoleon*) are scored against the Book of Mormon directly, with no retrieval cut, and ranked
within their registered control groups (the curated pseudo-biblical list of Amendment 6; the
history control's works on the origins of the American Indians). A source stands out when its
interval lies above the 99th percentile of its null and, for a named source, it ranks first in
its group.

**Known answers.** For Amendment 9 the per-text score is the strongest source's score in each of
the three matched-window draws of Amendment 10, averaged. As a positive control, Josephus
(Whiston), the *Testaments of the Twelve Patriarchs* (Golding) and Ilive's *Book of Jasher*,
King James spans masked, are searched against their draws with the King James Bible added; the
test is shown to find paraphrase if the King James Bible is the strongest source in every draw
for Josephus and the *Twelve Patriarchs*. If either check fails, the semantic table is reported
without interpretation.

**Not covered.** The story-skeleton comparison (ordered event lists aligned between texts) will
be registered separately before it runs.
