# Story skeletons: the plan, written before any compared text is read (BOM-25)

Written 2026-11-01. Registered as Amendment 15 (below) after the extractor check and before any
event was extracted from the Book of Mormon, a proposed source, a control or a retelling. The only
texts read so far are the 20 King James chapters of the check. Settings: `skeleton.*` in
`config/preregistered.yaml`. Code: `semantic/skeleton.py`.

## The question

Passage search (`docs/semantic-plan.md`) finds two passages that say the same thing. A borrowed
*story* can be retold with every sentence new: the same events in the same order, under other
names. That is the claim made for some proposed sources (a lost record found and translated, a
migration by sea, a final battle that destroys a people). This test asks whether the Book of
Mormon's sequence of events follows another book's sequence more closely than books of the same
kind do.

## Units and events

- **Blocks:** every text, the Book of Mormon and the King James ranges included, is cut into
  consecutive blocks of at most `skeleton.block_words` (2,000) words, as equal as possible. One
  rule for every text, so no text is cut more finely than another, and no chapter headings need
  to be found in OCR.
- **Events:** a model (`skeleton.extract_model`, claude-sonnet-5-5, hosted; owner's choice
  2026-11-01, so the GPU stays with the index) reads one block and lists, in order, at most
  `skeleton.max_events` (12) things that happen, each as one short plain sentence with **names
  replaced by roles** ("a prophet warns the king", "a family leaves the city for the
  wilderness"), so that plot is compared, not wording or names. A block with no story (sermon,
  law, genealogy) returns NONE. The prompt is fixed in `semantic/skeleton.py` (`PROMPT`).
  Model-assisted extraction, simulated (Amendment 1). A call that fails transiently is retried
  and never recorded as an answer.
- **Event lists are not published for licensed volumes** (they paraphrase them); they are kept
  under `data/corpus/semantic/skeleton/`. Results hold ids, spans and numbers.

## The extractor check (run 2026-11-01, `python -m semantic.skeleton check`)

Twenty King James chapters drawn with seed `bom25-skeleton-check` from books that are story
throughout (Genesis, Joshua, Judges, Ruth, 1-2 Samuel, 1-2 Kings, Esther, Acts), each extracted
twice. Pass marks fixed before the run: the two runs' event lists align (below) at a median of at
least 0.6 of events, and a second model call, shown the chapter and the run-1 list, finds at
least 90% of events in the chapter (simulated reading).

**Result (`data/semantic/skeleton/check.json`): passes.** Median agreement 0.92 (range 0.75-1.0);
233 of 238 events supported (98%). The event-match threshold the check sets (99th percentile of
cosines between events of chapters from different books, 23,809 pairs) is **0.700**.

## Alignment

- Each event is embedded with the index model (bge-small) and two events **match** when their
  cosine is at least the check's threshold (0.700, `skeleton.event_match_quantile` 0.99).
- Two texts are compared by **local alignment** of their whole event sequences (Smith-Waterman:
  match +1, mismatch and gap -0.5 each), which finds the stretch of events in the same order,
  allowing omissions. Reported: the alignment score, matched events, both spans, and the share of
  the shorter sequence matched.
- **Order matters.** The source's events within the aligned span are shuffled
  (`skeleton.shuffles`, 1,000, seed `bom25-skeleton`) and the alignment recomputed; the order
  p-value is (shuffles scoring at least as high + 1) / 1,001. Shared events in a different order
  are not a skeleton.

## Comparisons

- **The Book of Mormon (1830 text) against:** the named proposed sources (*View of the Hebrews*
  1823 and 1825, *The Late War* 1816, Spalding's *Manuscript Story*, *The First Book of
  Napoleon*), each against every member of its registered control group, as in the passage test
  (the curated pseudo-biblical list; the history control's works on the origins of the American
  Indians); and, once the index is searched, the top `skeleton.top_search_sources` (20) sources
  of the whole-corpus passage search.
- **A source stands out** when its alignment score is the highest in its group and its order
  p-value is at most `skeleton.max_order_p` (0.01). Top search sources are reported with their
  scores and order p-values, without a group rank.
- **Positive controls (retellings with known sources):**
  - Whiston's Josephus, volume 1 of the 1794 *Genuine Works* (`institutional_books:HN26TQ`: the
    Life, then *Antiquities* I-V, Creation to the Judges), against King James Genesis-Judges;
  - the *Testaments of the Twelve Patriarchs* (1791) against Genesis 37-50;
  - Ilive's *Jasher* (1829 reprint) against Genesis-Joshua.

  Each retelling is also aligned with `skeleton.control_unrelated` (20) unrelated books drawn
  with a derived seed from its own date window (Amendment 10's 70 years), whose word count is
  within a factor of 2 of the biblical range, whose primary genre label is `fiction_narrative` or
  `history_chronicle` (books that tell stories, none religious), and which are not Bibles (Amendment 10's title rule). **The test is shown to work** if Josephus and the *Twelve
  Patriarchs* each align with their biblical range above all 20 unrelated books, with an order
  p-value at most 0.01. *Jasher*, which retells loosely, is reported without a pass mark. If the
  check fails, the Book of Mormon comparisons are reported without interpretation.
- **Amendment 9.** The matched-window draws hold 2,000 volumes per text, too many to extract events
  from, so Amendment 9's separation is not computed for this test; it is stated as not
  computable, and the retellings carry the known answer.

## Size

About 7,000 model calls before the top search sources (Book of Mormon ~135 blocks, the named
sources and control groups ~3,400, the retellings, biblical ranges and 60 unrelated books
~3,500), and about 1,000 more after the index.

## Known weaknesses, stated now

- An event list is a model's reading; two readings of the same chapter agreed on 92% of events
  at the median, not 100%.
- Two thousand words with at most 12 events is a coarse reading: the main turns of a story, not
  its detail. A source that borrows small episodes may be missed.
- Common story shapes (a journey, a war, a prophet rejected) occur everywhere. Ranking within
  groups of the same kind, and the order test, are the guards.
- A long source has more chances to align; scores are reported with each text's event count.
- The threshold is set on King James narrative; on period prose with OCR noise, events are
  written by the model, not copied, so OCR matters less than in the passage test, but not nothing.
- The project draws no conclusion about inspiration from any result.

## Registration

Amendment 15 (OSF revision 6ae7dbb60fa5f3ec4abde26d, `paper/amendment-015-osf-text.md`), filed
2026-11-01 before any compared text was read.
