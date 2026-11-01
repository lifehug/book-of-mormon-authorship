# Semantic parallels: the plan, written before any search (BOM-25)

Committed 2026-11-01, before any Book of Mormon or known-answer passage has been searched against
the corpus. 5.5 registers "semantic parallels by sentence embeddings and FAISS nearest-neighbor
search at the passage level". It does not fix the model, the passage, what counts as a parallel,
the null, or the known-answer score Amendment 9 needs. Those are fixed here.

The story-skeleton test (ordered event lists aligned chapter by chapter, owner decision
2026-11-01) is part of BOM-25 but is a different instrument; it gets its own plan and amendment
before it runs.

## The question

Exact matching (BOM-23) finds shared wording. This test looks for passages that say the same
thing in different words: paraphrase, retold episodes, shared sermon arguments. The issue's
named proposed sources are tested at this level against fair control groups, so the question is
whether a source stands out from books of its kind, not from all books (owner, 2026-10-30).

## The index (built once, reused)

- **Scope:** every volume the corpus searches use (`reuse.exact.eligible_any_year`: text, a date,
  deduplication keepers, OCR exclusions applied, no newspapers): 278,796 volumes, all years.
  Date windows, own copies and every other selection are applied when the index is searched, so
  BOM-64's corrections (and any later one) never force a rebuild. New volumes are added to it
  without re-embedding the rest (`semantic/index.py`).
- **Passages:** consecutive `semantic.passage_words` (128) whitespace words of the normalised text
  (BOM-15), not overlapping; a last passage shorter than `semantic.min_passage_words` (32) is
  dropped. Stored per passage: work id, number, character span, word count; no text.
- **Model:** `semantic.index_model`, BAAI/bge-small-en-v1.5 (384 dimensions), half precision,
  vectors normalised. Chosen by the test below. The build takes about a week on the M4 and is
  checkpointed per shard.
- **Search:** exact inner product over every indexed passage (FAISS `IndexFlatIP` semantics, shard
  by shard, no compression or approximation), restricted to the target's window.

## Choosing the model (a known answer, before any build; `python -m semantic.choose`)

The 1807 *New Translation of the Book of Psalms* (`institutional_books:AH5KIN`) renders each psalm
afresh from the Hebrew: 443 of its passages are queries, the King James Bible's 7,970 passages the
gallery, and a query is right when the King James psalm with its number is ranked first (R@1) or
in the top 10 (R@10). `data/semantic/model_choice.json`:

| Model | R@1 | R@10 | Passages/s on the M4 | Full index |
| --- | --- | --- | --- | --- |
| all-MiniLM-L6-v2 | 0.587 | 0.804 | 483 | ~4 days |
| bge-small-en-v1.5 | 0.688 | 0.835 | 301 (half precision) | ~6.5 days |
| all-mpnet-base-v2 | 0.492 | 0.725 | 67 | ~29 days |
| bge-base-en-v1.5 | 0.695 | 0.813 | 79 | ~24 days |
| e5-base-v2 | 0.731 | 0.867 | 88 (half precision) | ~22 days |

E5-base is the most accurate here but would take about three weeks to index everything (Apple's
MLX runtime gave identical vectors more slowly, 62/s). The first plan was to index with bge-small
and re-score each query's best bge-small passages with E5. **The clean test misleads**, so the
same test was run again with a million corpus passages added to the gallery, which is what the
full index looks like to a query (`python -m semantic.choose distractors`;
`data/semantic/distractors_*.json`):

| With 1,000,000 corpus passages | R@1 | R@10 | R@100 | R@1000 |
| --- | --- | --- | --- | --- |
| bge-small-en-v1.5 alone | **0.594** | **0.777** | 0.853 | 0.919 |
| bge-small, its top 10 re-scored by e5-base | 0.616 | 0.777 | - | - |
| bge-small, its top 100 re-scored by e5-base | 0.540 | 0.781 | - | - |
| bge-small, its top 1,000 re-scored by e5-base | 0.508 | 0.718 | - | - |
| all-MiniLM-L6-v2 alone | 0.447 | 0.621 | 0.801 | 0.916 |

Among real period passages E5 ranks unrelated text above the right psalm more often than bge-small
does, and the deeper it re-scores the worse it gets. So **there is no re-scoring: every score is
the bge-small cosine**, and bge-small (the only candidate that fits a week) is also the better
of the two fast models with distractors. In 277 of 443 queries no distractor outscored the right
psalm; in 69, fifty or more did (`distractors_above_true_match`): a passage of this test is
found among a million in about three cases of five, and the full index is 150 times larger, so a
parallel this loose will often be missed. The test finds close paraphrase, not every retelling.

## A parallel

- **Query passages:** the target's full text (4.4: borrowing runs on the full text with King
  James spans labelled), cut as the index is; each carries `kjv_share`, the share of its words
  inside BOM-16's King James spans.
- **Retrieval:** the `semantic.keep` (100) nearest passages by bge-small cosine in the window,
  the target's own copies left out (`reuse.exact.own_copies`), stored (ids, spans, scores; no
  text).
- **The query's own null:** similarity of the query to `semantic.null_passages` (10,000)
  passages drawn at random, with a seed derived from the target's key, from its window. A
  retrieved passage is a **parallel** when its score is above the highest of those 10,000.
  This sets the bar per query: a generic passage ("and it came to pass that the people were
  gathered") is close to everything and needs a closer match to count.
- **Labels, not exclusions:** each parallel carries its source's King James share (word 5-grams
  shared with the King James text, as BOM-23's `kjv_share`) and whether its volume is a Bible or
  New Testament (Amendment 10's title rule). A parallel to a corrected-date volume (BOM-64)
  is listed in its own column with both dates, not dropped.

## Scores

- **Source score** `s(T, v)`: the number of target T's query passages with `kjv_share` at most
  `semantic.max_query_kjv_share` (0.5) that have at least one parallel in volume v, per 10,000
  words of those passages. Bible volumes are not scored as sources (listed only).
- **Distinctiveness** (the null of BOM-24): each source's `s(T, v)` placed as a percentile among
  `semantic.null_volumes` (500) volumes from the same window with the same primary genre label
  (`data/catalog/genre.parquet`) and a length within a factor of 2, drawn with a derived seed and
  scored the same way. 95% intervals by bootstrap over query passages (`semantic.bootstrap`,
  10,000, seed `bom25-boot`).
- **Named proposed sources:** *View of the Hebrews* (1823, 1825), *The Late War* (1816, 1819),
  Spalding's *Manuscript Story*, and *The First Book of Napoleon* (1809). Each is scored against
  the Book of Mormon directly (every passage pair embedded, no retrieval step, so nothing is lost
  to the candidate cut) and placed against its control group scored the same way: *The Late War*
  and *Napoleon* against the curated pseudo-biblical list (Amendment 6, 18 works); *View of the
  Hebrews* and Spalding against the history control's 46 works on the origins of the American
  Indians (`data/controls/history.jsonl`, `origins`). Reported: its score, its rank in its group,
  and the passages behind it.

## The known-answer score (Amendment 9)

Committed now to `docs/known-answer-plan.md`: **the strongest period source's score**,
`max over v of s(T, v)`, with v ranging over the volumes of each of BOM-23's three matched-window
draws (the same 2,000-volume samples in `data/reuse/exact/searches.json`, re-read through
`effective_year`), mean over the draws. Higher means drawing on its own time. Every text is
processed exactly as the Book of Mormon is. Separation by Amendment 9's rule (exact Mann-Whitney,
p <= 0.01, the Rowley check); if it fails, the semantic table is reported as uninformative on the
translation question.

## Positive controls: retellings with a known source

A test that is meant to find paraphrase must find it where it is known to be. Three texts retell
the Bible in their own words: Whiston's Josephus (*Antiquities*, 1737 English), the *Testaments
of the Twelve Patriarchs* (Golding's English, 1581) and Ilive's *Book of Jasher* (1751). Each
text's passages (King James spans masked, so quotation cannot carry the result) are searched
against its three matched draws with the King James Bible (`data/kjv/kjv.jsonl`, passages cut
the same way) added as one more volume. **The test is shown to find paraphrase** if the King
James Bible is the strongest source in every draw for Josephus and the *Twelve Patriarchs*;
*Jasher*, which retells loosely, is reported without a pass mark. Also reported: the share of
each text's passages whose best parallel is in the right biblical book. If the check fails, the
semantic table is reported as unable to find known paraphrase and is not interpreted.

## Reading the result

- The table lists every parallel, its scores and labels; the named sources are reported whatever
  they score.
- A source **stands out** when its distinctiveness interval lies above the 99th percentile of its
  null and, for a named source, it ranks first in its control group.
- No single passage pair is read as evidence; the source score counts many.
- The project draws no conclusion about inspiration from any result.

## Known weaknesses, stated now

- **OCR noise** lowers similarity for poorly scanned volumes, so a real parallel in a bad scan
  can be missed. Reported by source with BOM-14's estimated character error rate.
- **Loose paraphrase is missed.** With a million distractors, the right psalm is first for 59% of
  queries; at 150 times that size, looser parallels fall out of the top 100. The named sources are
  scored without the cut (every passage pair), and the retelling controls measure what is found.
- **Passage boundaries** fall at fixed word counts, so a parallel split across two passages scores
  lower in each. Not corrected.
- **Biblical register.** Pseudo-biblical prose resembles the Book of Mormon in style, and
  embeddings mix style with content. The control groups are chosen to share the register, so
  standing out means more than sounding biblical.

## Registration

Registered as Amendment 14 (OSF revision 6ae7bc3c227eb64c6abde258, 2026-11-01), before any search. The index build started under the same settings a few hours earlier; an index is not a result.
