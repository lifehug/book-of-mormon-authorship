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
