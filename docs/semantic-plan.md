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

## Named sources against their control groups (provisional, 2026-11-01; `python -m semantic.search named`, `data/semantic/named.json`)

The Book of Mormon's 2,158 passages (2,022 with King James share at most 0.5, scored) against
each named source and each member of its registered group, every passage pair compared; each
query's bar is its best match among 10,000 random 1780-1830 passages. Hunt's own copy on the
curated list is left out of his group (his cleaned 1816 text is scored instead), so each source is
ranked among the other works.

| Source | Group | Rank | Book of Mormon passages with a parallel | Score (95% interval) |
| --- | --- | --- | --- | --- |
| *View of the Hebrews* (1825) | origins of the American Indians (49) | **1** | 767 | 29.6 (28.0-31.3) |
| *View of the Hebrews* (1823) | same | **2** | 763 | 29.5 (27.9-31.1) |
| *The Life of David Brainerd* (next in that group) | same | 3 | 642 | 24.8 (23.2-26.4) |
| Spalding, *Manuscript Story* | same | 12 | 143 | 5.5 |
| *Antediluvian Antiquities* (first in its group) | curated pseudo-biblical (18) | 1 | 1,054 | 40.7 (39.1-42.4) |
| *The Book of Jasher* (1829 printing) | same | 2 | 378 | 14.6 |
| *The First Book of Napoleon* | same | 3 | 205 | 7.9 (6.9-9.0) |
| *The Late War* (1816) | same | 6 | 49 | 1.9 |

Checked before writing this down: *View of the Hebrews*' interval does not overlap Brainerd's;
the 1823 edition is the shortest of the three (443 passages to Brainerd's 801), so length does
not explain its place; and about 90% of its 50 strongest pairs come from Book of Mormon passages
with no King James wording, so its Isaiah quotations do not either.

**Not yet a verdict.** The registered rule says a named source stands out when it ranks first in
its group **and** its interval lies above the 99th percentile of 500 same-genre, same-length
volumes. That second check reads those volumes' vectors from the index and is run when the build
finishes. A score here is not small by chance alone: a book of 800 passages beats a query's bar
by luck for roughly 8% of queries, so scores of a few per 10,000 words are near chance and the null
decides.

## Whole-corpus results (2026-11-04; `python -m semantic.corpus`, `data/semantic/corpus_*.json`)

Searched once over the finished index (280 shards, 163,121,310 passages): 55 searches (the Book
of Mormon's window and three matched draws for each of 15 texts), 100 nearest passages per query,
rescored in full precision. The Book of Mormon's window holds 221,373 volumes, 16,823 of them
moved past 1830 by BOM-64 and kept with a flag.

**Positive controls (the gate).** Josephus: the King James Bible is the strongest source in all
three draws (51.9, 51.0, 51.8 against the best other 43.8, 44.2, 35.8): passes. *Twelve
Patriarchs*: strongest in draws 0 and 1 (53.8 against 47.2); in draw 2 the strongest is
`tcp:A09151`, the 1576 printing of the same English translation (69.9), which the author/title
rule misses and which BOM-23 already listed in `MISSED_OWN_COPIES` (2026-10-31). As registered
the control **fails**; with that known own copy left out, as the plan's own-copies rule intends,
it passes. *Jasher* (no pass mark): the King James Bible strongest in all three draws. Owner
owner chose the own-copy-out verdict: **Amendment 20** (post hoc, OSF revision 6aeb6364388d19d44e80bc2f). The test is taken as shown to find paraphrase; both computations stay reported.

**Known-answer score (Amendment 9).** Strongest period source per draw, mean over draws: genuine
translations 36.7-59.5, texts presented as ancient 31.1-58.6, the Book of Mormon 44.3.
U = 14/27, p = 0.50 (own copies out: 15/27, p = 0.43): **no separation**, so the semantic table
is uninformative on the translation question, as exact reuse (BOM-23) and rare phrases (BOM-24)
were.

**The Book of Mormon's table.** Every query passage has at least one parallel (214,549 in all,
30,994 source volumes). The leaders are biblical retellings and commentary: editions of Whiston's
Josephus take 14 of the top 20 places (first counted as 11; three editions catalogued as "Works ..." were missed, corrected 2026-11-04) (first: `institutional_books:HN33GK`, 19.05 per 10,000
words, 95% interval 17.6-20.6), with Blake's *Biblical Reader*, Simpson's *Sacred Literature*,
George Fox's *Journal* and James Nayler's collected writings among the rest. **622 sources stand
out by the registered rule**, which is too many to read as findings: a short volume whose
genre-and-length null is all zeros stands out with a single parallel (*The First Book of
Napoleon*, rank 4,706, score 0.31). The null does not control for biblical register, so
standing out here mostly means sounding biblical. The named sources do not lead: the 1823 *View
of the Hebrews* is 700th (1.28), Napoleon 4,706th. None ranked first in its control group in the
direct test (`named.json`), which the rule for a named source also requires.

**Story skeleton of the top 20 (`python -m semantic.skeleton top`, `data/semantic/skeleton/top.json`).**
The 20 leading sources were put through the story-skeleton test (4,234 blocks read by the hosted
model, 2026-11-04, paced at 500 calls an hour). **None shares the Book of Mormon's order of events
at the registered level** (`max_order_p` 0.01). The longest shared run is 9 of the Book of
Mormon's 1,421 events (the Harvard Josephus `HN33GK`, score 5.5, order p 0.24); no source shares more than 3% of the shorter text's events. Three runs have order p under 0.05 (Josephus `worksofflaviusjo01jose`
0.019, `collectionofsund00innayl` 0.026, `HW2J64` 0.028), none under 0.01. For scale, the positive
control, Josephus against Genesis-Judges, shares 108 events in order (score 25.5, p 0.001). The
Josephus editions' runs fall mostly on the same two short stretches of the Book of Mormon (blocks
41-44 and 131-133; two editions at blocks 20-29), so they are largely one small overlap seen in
edition after edition, not separate findings.

| Search rank | Source | Score | Events in order | Order p |
| --- | --- | --- | --- | --- |
| 1 | The genuine works of Flavius Josephus (`institutional_books:HN33GK`) | 5.5 | 9 | 0.242 |
| 2 | The works of Flavius Josephus (`institutional_books:HXQ2K3`) | 5 | 6 | 0.080 |
| 3 | The works of Flavius Josephus (`institutional_books:HW2J64`) | 5 | 7 | 0.028 |
| 4 | The works of Flavius Josephus (`internet_archive:worksofflaviusjo00jose`) | 5 | 7 | 0.091 |
| 5 | The genuine works of Flavius Josephus, the Jewish historian (`internet_archive:genuineworksoffl18251jose`) | 5 | 8 | 0.133 |
| 6 | The works of Flavius Josephus (`internet_archive:worksofflaviusjo01jose`) | 5 | 6 | 0.019 |
| 7 | The works of Flavius Josephus (`internet_archive:worksofflaviusjo00injose`) | 4.5 | 6 | 1.000 |
| 8 | The Biblical reader; or, Interesting extracts from the Sacred Scriptures; with practical observation (`internet_archive:biblicalreaderor00blak`) | 4.5 | 5 | 0.430 |
| 9 | The genuine works of Flavius Josephus, the Jewish historian (`institutional_books:HW3CRW`) | 4.5 | 6 | 0.366 |
| 10 | Sacred literature (`internet_archive:bim_eighteenth-century_sacred-literature-shewi_simpson-david_1788_4`) | 5 | 8 | 0.840 |
| 11 | The works of Flavius Josephus (`institutional_books:HW2JS4`) | 4.5 | 5 | 0.286 |
| 12 | A journal or historical account of the life, travels, sufferings, Christian experiences, and labour (`tcp:N28090`) | 3 | 3 | 0.172 |
| 13 | The Works of Flavius Josephus, the Learned and Authentic Jewish Historian and celebrated Warrior. To (`institutional_books:HXJ9AU`) | 4.5 | 5 | 0.341 |
| 14 | A collection of the several writings of that true prophet faithful servant of God, and sufferer for (`institutional_books:HWJN6I`) | 2.5 | 3 | 1.000 |
| 15 | The genuine works of Flavius Josephus (`institutional_books:HN26TR`) | 5 | 7 | 0.120 |
| 16 | A collection of sundry books, epistles and papers (`internet_archive:collectionofsund00innayl`) | 4 | 5 | 0.026 |
| 17 | Whole genuine works (`internet_archive:wholegenuinework01joseuoft`) | 4 | 4 | 1.000 |
| 18 | Works (`institutional_books:HXIH8Y`) | 4 | 5 | 1.000 |
| 19 | Works (`institutional_books:HXIH8X`) | 4.5 | 7 | 0.146 |
| 20 | A collection of sundry books, epistles and papers (`internet_archive:collectionofsund00nayl_0`) | 2.5 | 3 | 1.000 |
