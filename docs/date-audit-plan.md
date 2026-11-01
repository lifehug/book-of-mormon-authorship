# The catalog date audit: the plan, written before the scan (BOM-64)

Committed 2026-11-01, before any volume's text has been scanned for later years.

## The problem

BOM-23 found later texts quoting the Book of Mormon catalogued decades early: Congressional
serial set volumes dated 1817 whose text names 1865 and 1868 hundreds of times, a *Millennial
Harbinger* dated 1830 (1831), a *Monthly Review* dated 1826 (1842), *Herald of Gospel Liberty*
dated 1808 (1909-1918). Serials and multi-volume sets seem to carry their first volume's date.
BOM-56 (`metadata/dates.py`) already corrects the 1800 placeholder; this audit checks every
other volume the same way, from its own text, and writes to the same `effective_year` that every
date-window selection reads. Nothing is deleted and the frozen catalog is not edited.

## The rule (fixed now)

- **Scope.** Every volume with text from Internet Archive, HathiTrust, Harvard Institutional
  Books and TCP whose effective year (after BOM-56) is 1830 or earlier. Chronicling America is
  left out: each issue is dated from its masthead.
- **Count.** Four-digit years from 1600 to `dates.latest_year` (1949) anywhere in the text; later
  numbers are library stamps, call numbers and OCR noise (an "1817" serial-set volume holds a
  "1998"). A mention is **later** if the year exceeds the volume's year by more than
  `dates.slack_years` (2): a preface dated a year after the title page is not a misdating.
- **Flag.** A volume is flagged when it has at least `dates.min_later_mentions` (10) later
  mentions and they are at least `dates.min_later_share` (0.20) of all its year mentions.
  Counts, not the single latest year.
- **Corrected year.** The latest year mentioned at least `dates.min_year_mentions` (3) times: a
  lower bound on the printing date. A flagged volume moves to that year (out of any window it no
  longer fits); verdict `body_later`, written to `data/catalog/date_body.parquet` with its counts.

## How good the flag is (measured, not assumed)

A seeded sample (`dates.check_seed`, `dates.check_size` = 100 each) of flagged volumes and of
unflagged volumes with at least one later mention: a model reads the opening 6,000 and closing
2,000 characters and gives the printing year it finds, or UNKNOWN (model-assisted, simulated,
Amendment 1). Precision: share of flagged volumes whose found year is later than catalog year +
slack. Miss rate: the same share among the unflagged sample. Both reported with the counts by
source and kind (serial, multi-volume, monograph).

## What it changes

Every reader of `metadata.dates.effective_year` (reuse, rare phrases, controls, pools, the
pseudo-biblical list, the classic corpus runs). Results already reported (BOM-21 to BOM-23,
BOM-62) are not recomputed silently: BOM-23's tables are rechecked and any change is reported.
The registered seal (4.2) is unchanged and still applies to every volume whatever its date.

## Registration

Registered as Amendment 12 (OSF revision 6ae768b9883b4fc0e7bde25d, 2026-11-01), before any
volume was scanned.

## Result (2026-11-01; `python -m metadata.dates body`, `sample`)

**The scan.** 366,580 volumes dated 1830 or earlier were scanned (308 s, no read errors);
23,859 are flagged, and 19,463 of those move past 1830.

| Source | Scanned | Flagged | Moved past 1830 |
| --- | --- | --- | --- |
| Internet Archive | 243,864 | 11,045 (4.5%) | 8,418 |
| TCP | 61,304 | 259 (0.4%) | 48 |
| Harvard Institutional Books | 31,252 | 12,155 (38.9%) | 10,769 |
| HathiTrust | 30,160 | 400 (1.3%) | 228 |

By kind (from title words, a rule chosen after the scan, so post hoc: serial if the title names
a journal, magazine, review, register, report, gazette and the like; multi-volume if it names a
volume, part or works; otherwise monograph): serials 84,255 scanned, 16,341 flagged (19.4%);
multi-volume 55,008, 903 (1.6%); monographs 227,317, 6,615 (2.9%). Serials catalogued under their
first volume's date are most of the problem, as BOM-23 suggested. Harvard's catalog dates are the
weakest: nearly two in five of its volumes dated 1830 or earlier name later years often enough to
be flagged.

**How good the flag is** (model-assisted, simulated; `data/catalog/date_sample.jsonl`):

| Sample | Printed later than catalog + 2 by the model's reading | Unknown |
| --- | --- | --- |
| 100 flagged | **81** (Harvard 51 of 57, Internet Archive 30 of 39, HathiTrust 0 of 3, TCP 0 of 1) | 0 |
| 100 unflagged, at least one later mention | **5** of 97 | 3 |

So the flag is right about four times in five (serials 58 of 66, monographs 20 of 29), and it
misses about one in twenty of the volumes that mention a later year without being flagged. In 56
of the 100 flagged the model's year is no more than two years before the corrected year; the
corrected year is a lower bound, as intended. Across the corpus 1,275 flagged volumes have no
later year mentioned three times, so they have no corrected year and keep their catalog date (5
of them in the sample): flagged, but still inside the windows.

**Moved too far.** Of the 80 sampled volumes the rule moves past 1830, the model reads a printing
year of 1830 or earlier for 18. Some of those readings are the model's error (an "1817" serial-set
volume naming 1901 759 times, read as 1817 from its series title page), but some are the rule's:
the corrected year is the latest year named three times, so an 1823 *Edinburgh Magazine* holding
three library-stamp "1923"s moves to 1923. About one moved volume in five may truly belong before
1830.

**The cost of the 19 in 100 that are wrong.** A wrongly flagged volume is a genuine pre-1830 book
moved out of the date windows. For contamination tests that is the safe side (nothing later gets
in), but for the borrowing searches it could hide a real source. Decided now, before BOM-24 or
BOM-25 has any result: **those searches report matches from moved volumes in a separate column,
with the volume's catalog and corrected years**, rather than dropping them, so a real source is
never lost to this audit.

**BOM-23 rechecked** (`python -m reuse.exact redate`, `data/reuse/exact/redated.json`; the
known-answer score in `known_answer.json`, field `score_redated`):

| Table | Reported | Under corrected dates | Volumes now past the window |
| --- | --- | --- | --- |
| Book of Mormon | 0.52% | 0.26% (0.16% with the seal) | 16 |
| 1820s sermons | 2.47% | 2.28% | 56 |
| *The Late War* | 8.92% | 8.74% | 115 |

The 16 Book of Mormon volumes are all among the 17 BOM-23 sorted as later quotations; the
seventeenth (a *Millennial Harbinger* dated 1830 whose text runs into 1831) is within the slack and
is caught by the seal. None of the 30 shared period phrases moved. The known-answer test is
unchanged: U = 4 of 27, p = 0.964, still not separating. The conclusions of BOM-23 stand.

**Known limit.** A volume straddling the cutoff (an 1830 serial running into 1831-32) sits inside
the two-year slack and is not flagged; the seal remains the guard for the Book of Mormon's own
text.
