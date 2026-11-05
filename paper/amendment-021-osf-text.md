# Amendment 21: the null for the named proposed sources in the semantic search

*Filed 2026-11-05. Correction after filing: *The Late War*'s label is from 4 of 6 Hunt printings, not 3 of 5 as filed; the label is the same. (OSF revision 6aec8dd3dd216354e1f383cc; the OSF form stripped `<source>` from the seed name as markup, so the filed text reads `bom25-null:named:`, which is the prefix to the source's key). Evidence: `data/semantic/named.json`, `docs/semantic-plan.md` ("Named sources
against their control groups"), `semantic/search.py`.*

---

**Amendment 21, filed 2026-11-05, after the named sources' direct scores and group ranks had been
seen (`named.json`, 2026-11-01) and before any null for them was computed.** It pins how the null
of Amendment 14 is built for a named proposed source. It changes no score, threshold or rule.

**Why.** Amendment 14 says a named source stands out when its bootstrap interval lies above the
99th percentile of 500 volumes from the same window, genre and length band, *scored the same way*,
and it ranks first in its control group. Named sources are scored directly (every passage pair,
no retrieval step), so their null must be scored directly too; the whole-corpus search's
retrieval scores are a different quantity and cannot stand in. The named sources are cleaned
candidate files rather than catalog volumes, so two inputs of the null are not yet fixed: their
genre label and which volumes count as their own copies. The direct null was planned for when the
index finished and had not been run; the whole-corpus write-up of 2026-11-04 wrongly said no named
source ranked first in its group (the 1825 *View of the Hebrews* does, `named.json`), and is
corrected.

**The rule.**
- *Pool:* the Book of Mormon's window gallery of the whole-corpus search (effective year
  1780-1830, or moved by BOM-64 from a catalog year in it), less Bibles, the Book of Mormon's
  sealed copies, and the source's own copies (the BOM-23 rule: same author or same first six
  title words as its catalog copies; for *The Late War*, every printing of it).
- *Genre:* the majority primary genre label (`data/catalog/genre.parquet`) of the source's catalog
  copies: *View of the Hebrews* (both editions) `sermon_devotional` (3 of 4 copies); *The Late
  War* `newspaper_periodical` (3 of 5 Hunt printings); *The First Book of Napoleon* its own label,
  `newspaper_periodical`.
- *Length:* the words in the scored text's passages, within a factor of 2
  (`semantic.null_length_factor`), against each volume's passage words in the index.
- *Draw:* 500 volumes (`semantic.null_volumes`) with seed `bom25-null:named:` followed by the source's key.
- *Scoring:* each null volume's normalised text is cut into passages and embedded fresh, exactly
  as the control-group members were in `named.json`, and scored against the same Book of Mormon
  query passages and per-query bars.
- *Decision:* as Amendment 14: stands out if the interval's lower end exceeds the null's 99th
  percentile and the source ranks first in its group. Spalding's *Manuscript Story* has no catalog
  copy (and so no genre label) and ranks 12th of 49, so it cannot stand out; no null is drawn for
  it.

**What this does not change.** The story-skeleton results (Amendment 15), the whole-corpus table
and the known-answer result (the semantic separation fails, Amendment 20) stand as reported. The
named sources are reported whatever the null shows.
