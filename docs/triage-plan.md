# Triage of the parallels (BOM-26)

Written 2026-11-06, before any parallel was triaged. Registered as Amendment 27 (OSF revision
6aedf2246bb1339361f385b5). Code: `semantic/triage.py`.

**What it does.** The borrowing searches (BOM-23 exact, BOM-24 rare phrases, BOM-25 paraphrase)
ran over the whole corpus and found many hits: a Book of Mormon passage and a passage of another
book that resemble each other. Most are innocent. This sorts a registered selection of them into
BIBLICAL (both echo the King James Bible), COMMON (stock period phrasing) and SPECIFIC (a particular
shared detail that neither explains), with a one-sentence reason each.

**Selection (1,069 pairs).** Paraphrase: the named sources' strongest pairs from the direct test
(249), the 20 leading sources' 25 strongest parallels (500), 250 at random from all non-Bible
parallels; rare phrases: every shared rare 4-gram of the named sources (33) and up to 10 from each
of the 20 highest-density volumes (37), each with 40 words of context. Exact reuse was sorted by
hand in BOM-23 and is not repeated.

**Passes.** First: `claude-sonnet-5-5` on every pair. Second, simulated review (section 9): an
independent `claude-opus-5-5` call, blind to the first label, on every first-pass SPECIFIC and a
seeded 10% of the rest. Reported: counts by search and label, Cohen's kappa, the confusion table,
and the pairs both passes call SPECIFIC. Paced at 500 calls an hour, 2 at a time, on the owner's
Claude subscription.

**Weaknesses, stated now.** Labels are a model's judgment; the second pass is a model too (labelled
simulated). The random sample is 250 of about 214,500 non-Bible parallels, enough to say whether
specific hits are common, not to find every one. Pairs and replies stay private (corpus text); the
report holds ids, labels and counts.

## Result (2026-11-06)

All 1,069 pairs labelled by the first pass; the simulated second review (a different model, blind
to the first label) re-labelled 104: both first-pass SPECIFIC pairs and a seeded 10% of the rest.
Report: `data/semantic/triage.json`; replies and reasons (corpus text) stay in
`data/corpus/semantic/triage/`.

| Search | Biblical | Common | Specific (first pass) |
| --- | ---: | ---: | ---: |
| Paraphrase, named sources | 104 | 144 | 1 |
| Paraphrase, 20 leading sources | 149 | 350 | 1 |
| Paraphrase, random sample | 104 | 146 | 0 |
| Rare phrases, named sources | 10 | 23 | 0 |
| Rare phrases, 20 densest volumes | 15 | 22 | 0 |
| **All** | **382** | **685** | **2** |

**Pairs specific under both passes: 0.** The two first-pass SPECIFIC pairs:

- Spalding's *Manuscript Story*: tamed elephant-like beasts in ancient America (the Book of
  Mormon's elephants, cureloms and cumoms; Spalding's "Mammoons"). Second review: COMMON, no
  shared wording beyond "elephant"; the period's interest in mammoth and mastodon remains.
- A collected *Works* (Harvard `HXIH8X`, 1820): soldiers' survival as proof of a just war under
  God's protection. Second review: COMMON, a stock providential theme with no shared wording.

Agreement on the 104 doubly labelled pairs 0.740, Cohen's kappa 0.505 (moderate). Every
disagreement but those two is COMMON against BIBLICAL (25 pairs); the passes never disagree about
a pair being specific except the two above. Because the second pass sees every first-pass
SPECIFIC, a missed specific pair would need the first pass to have called it biblical or common.

**Reading.** Across the four borrowing tests' strongest and random hits, the similarities are
explained by shared King James wording (36%) or by period stock phrasing and ideas (64%). Nothing
the model triage could find needs a specific connection to any one text, the named sources
included. Limit: model-assisted labels, with the human reviews of section 9 simulated.
