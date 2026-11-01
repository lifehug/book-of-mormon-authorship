# Amendment 12: the catalog date audit

*Filed 2026-11-01. Evidence: `docs/date-audit-plan.md`.*

---

**Amendment 12, filed 2026-11-01, before any volume's text has been scanned for later years.** It
adds a data-quality step; no hypothesis, decision rule or threshold of section 6 changes.

**What prompted this.** BOM-23's reuse table found later texts quoting the Book of Mormon whose
catalog dates are decades too early (Congressional serial set volumes catalogued 1817 that name
1865 and 1868 hundreds of times; periodicals catalogued 1808-1830 that name 1831-1918 most).
Every date-window selection (sources, phrase rarity, controls, pools, dating) depends on these
dates. The registered seal (4.2) still excludes any volume quoting the Book of Mormon whatever its
date; this amendment concerns dates themselves.

**The rule.** For every volume with text from Internet Archive, HathiTrust, Harvard Institutional
Books and TCP whose year (after the BOM-56 placeholder correction) is 1830 or earlier, four-digit
years from 1600 to 1949 are counted in its full text. A mention is later if it exceeds the
volume's year by more than 2. A volume is flagged when it has at least 10 later mentions forming
at least 20% of its year mentions. Its corrected year is the latest year mentioned at least 3
times, a lower bound on its printing date, and every date-window selection uses it. Nothing is
deleted and the frozen catalog is not edited; corrections are published in a separate table with
their counts.

**How good the flag is.** A seeded sample (seed "bom64-dates") of 100 flagged volumes and 100
unflagged volumes with at least one later mention is read by an AI model (opening 6,000 and
closing 2,000 characters; model-assisted, simulated) for the printing year. Precision and miss
rate are reported with counts by source and kind. Results already reported are rechecked under
the corrected dates and any change is reported.
