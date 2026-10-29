# Expanded candidate corpora: tiers, gates and refusals (BOM-49; Amendment 5)

Amendment 5 (OSF revision `6ad8cc455301b781d55b34dc`, approved 2026-10-21) allows a candidate's
later writing as a **secondary** analysis only, never in place of the primary one, under fixed
rules. This file publishes the tiers and the gate results before any Book of Mormon scoring.
Values: `config/preregistered.yaml`, `candidates.expanded_corpora`.

## Exposure tiers (from the historical record, fixed in advance)

| Tier | Candidates | Rule |
| --- | --- | --- |
| No later writing | Solomon Spalding (died 1816) | no expansion possible |
| Exposed | Joseph Smith, Oliver Cowdery, Sidney Rigdon, Parley P. Pratt, W. W. Phelps | read, preached or published on the Book of Mormon for years after 1830: a **non-match is evidence, a match is uninformative** |
| Unexposed | Ethan Smith, Gilbert Hunt, corpus authors | expanded corpus used in both directions |

## Provenance tiers of the later samples (masked words, BOM-13 and BOM-16)

| Candidate | Holograph | Dictated | Printed under own name | Copied by a scribe | Admitted (strict) |
| --- | --- | --- | --- | --- | --- |
| Joseph Smith | 6,362 | 5,038 | -- | 17,534 | 11,400 |
| Oliver Cowdery | -- | -- | 44,335 | 1,345 | 0 |
| Parley P. Pratt | -- | -- | 91,436 | -- | 0 |
| Sidney Rigdon | -- | -- | 21,510 | -- | 0 |
| W. W. Phelps | -- | -- | 28,476 | -- | 0 |
| Ethan Smith, Gilbert Hunt | no post-1830 writing in the candidate corpora | | | | 0 |

Amendment 5 admits holograph and dictated text and excludes reported speech and text composed or
edited by others. It does not name print. Printed work under the author's own name is his
composition but passed through typesetters and, in a newspaper, an editor; the **strict** reading
used here does not admit it. A copy made by a scribe is not admitted either. Whether print should
count is a question for the owner if the gate below ever opens; it does not change anything now.

## The gate (Amendment 5, Change 4): time-split accuracy at the section 7 floor

A candidate gets an expanded corpus only if a profile from one side of 1830 recognises their
writing on the other at 80% or better (BOM-48, `data/benchmark/timesplit.json`).

| Candidate | Time-split measurable? | Result | Expansion |
| --- | --- | --- | --- |
| Joseph Smith | one test; pre-1830 sample 2,741 words, below the 10,000-word floor | later profile named him with all four methods (one test, not a rate) | **refused**: no accuracy at the floor can be measured |
| Oliver Cowdery | one test; pre-1830 sample 1,313 words | not named by any method | **refused** |
| Rigdon, Pratt, Phelps | no pre-1830 text | cannot be measured | **refused** |
| Ethan Smith, Hunt | no post-1830 text | not applicable | none to grant |

For context, the drift baseline on 30 corpus authors over a gap of seven or more years is 37-60%
by method (chance 3%), so no candidate would be expected to clear 80% even with more text.

**Result: no expanded corpus is granted.** Amendment 5's secondary analysis therefore reports
these refusals rather than results, as its own expected-outcome statement anticipated. The
sweep-lead expansions (at most ten, Change 5) are decided when the author sweep runs (BOM-39),
under the same gate.
