# Manuscript and dictation evidence (BOM-34)

Written 2026-11-06. Code: `manuscript/corrections.py` (the catalog), `eval/scribes.py` (6.3's
scribe and narrator comparison, run after the blind run). Data: `data/manuscript/`. Method choices
not fixed by the registration are in `paper/amendment-035-osf-text.md` (DRAFT).

## What this answers

How the text got onto paper. Two manuscripts survive in part: the **original manuscript**, written
as the text was dictated (April-June 1829), and the **printer's manuscript**, a copy of it made
for the typesetter (circa August 1829 to January 1830). If the first was taken down by ear and the
second copied by eye, their mistakes should differ in kind: mishearings in the first, misreadings
in the second. That is a test the transcripts let us run on every correction, not a few chosen
examples.

## The correction catalog

**Source.** The Joseph Smith Papers transcripts of both manuscripts (231 pages of the original,
about 28% of the text; 468 pages of the printer's, all of it), held privately because they are
copyrighted (`data/private/bom/`). Their markup shows what a scribe struck out, what was added
above the line, and where a new hand begins.

**Method.** Every struck word and every added word is an event:

| Event | What it is |
| --- | --- |
| substitution | a struck word replaced, by an added word or by the next word written on the line |
| false start | a struck fragment the next word completes ("migh" then "mightest") |
| deletion | a struck word with no replacement |
| insertion | an added word with no deletion (an omission restored) |

A substitution of one word for one word is typed: **homophone** (a listed same-sound pair:
where/were, there/their, are/our and 80 more), **sound-alike** (same Soundex code, different
spelling), **spelling** (close in letters), **other**. The homophone list is the primary measure;
Soundex also catches eye errors (hs/his, commander/commanded), so it is reported beside it, not
relied on. A struck word with a capital in mid-sentence is flagged as a likely name.

**Results** (`data/manuscript/summary.json`):

| | Original (dictated) | Printer's (copied) |
| --- | ---: | ---: |
| Pages / words transcribed | 231 / 96,346 | 468 / 255,848 |
| Corrections | 1,597 | 2,136 |
| Substitutions | 693 | 927 |
| **Homophone substitutions** | **36** | **8** |
| Sound-alike (Soundex) | 105 | 138 |
| False starts | 80 | 33 |
| Names flagged | 68 | 89 |

- **All pages:** homophone substitutions are 6.3 times as likely, as a share of substitutions, in
  the original (Fisher p = 1e-7).
- **Same passages only** (printer's pages whose text survives in the original): 36 against 2;
  odds ratio 12.5, p = 2e-6.
- **Same scribe** (Oliver Cowdery wrote most of both): 36 homophone corrections in 84,220 words of
  the original against 6 in 212,962 words of the printer's, about 0.43 against 0.03 per 1,000
  words; odds ratio 9.0 among his substitutions, p = 2e-9. Holding the hand fixed rules out "this
  scribe simply confused there and their".

| Scribe | Manuscript | Corrections | Substitutions | Homophones |
| --- | --- | ---: | ---: | ---: |
| Oliver Cowdery | original | 1,347 | 590 | 36 |
| John Whitmer | original | 81 | 43 | 0 |
| Scribe 3 | original | 157 | 58 | 0 |
| Joseph Smith Jr. | original | 12 | 2 | 0 |
| Oliver Cowdery | printer's | 1,814 | 837 | 6 |
| Scribe 2 | printer's | 290 | 83 | 2 |
| Hyrum Smith | printer's | 32 | 7 | 0 |

**Reading.** The original manuscript's corrections carry the signature of writing from speech, and
the printer's of copying, with the scribe held constant. This agrees with Skousen's reading of the
same manuscripts (1998, below) and with the Papers' introductions, here measured over every marked
correction. It says how the words reached the page. It does not say where they came from: a
dictated text could be composed, recited from memory, or read aloud from another document, and
this test cannot tell those apart.

## Scribe map

From the transcripts' hand notes (`data/manuscript/corrections.csv`, column `scribe`; page-level
hands in `data/bom/reports/original_extant.md`):

- **Original:** Oliver Cowdery (most of the surviving text, Alma through Ether), John Whitmer and
  an unidentified scribe 3 (in 1 Nephi; the Papers suggest scribe 3 may be Christian Whitmer),
  Joseph Smith (28 words in Alma 45). Martin Harris, Emma Smith, Reuben Hale and Samuel Smith are
  reported scribes whose hands are not in the surviving pages.
- **Printer's:** Cowdery about 84%, scribe 2 about 15%, Hyrum Smith under 1% (the Papers' figures).

Paragraph-level scribe labels, used by BOM-17's scribe segmentation, are in
`data/bom/segments/paragraph_labels.jsonl` (870 of 1,197 paragraphs have no surviving original).

## Production timeline

| Date | Event | Source |
| --- | --- | --- |
| c. 12 April 1828 | Dictation begins in Harmony, Pennsylvania (Martin Harris scribe) | JSP, Original Manuscript, source note |
| summer 1828 | The first portion (the "Book of Lehi", 116 pages) is lost | same |
| early (5-7) April 1829 | Oliver Cowdery arrives in Harmony and becomes scribe | same; Welch 2018 |
| 15 May 1829 | By Cowdery's account the translation has reached 3 Nephi | JSP source note |
| June 1829 | Joseph Smith and Cowdery move to the Whitmer home, Fayette, New York | JSP source note |
| 11 June 1829 | Title page deposited for copyright, Northern District of New York | JSP, Copyright, 11 June 1829 |
| c. 1 July 1829 | Translation finished; Cowdery asked to make the printer's manuscript | JSP source note |
| 25 August 1829 | Printing agreement; typesetting begins soon after | JSP, Printer's Manuscript, source note |
| c. Aug 1829 - Jan 1830 | Printer's manuscript copied (Cowdery, scribe 2, Hyrum Smith) | same |
| mid-March 1830 | Printing complete; offered for sale 26 March 1830 | same; Wayne Sentinel, 26 March 1830 (`docs/access-evidence.md`) |

The working time from Cowdery's arrival to the end of June is about 60-75 working days by Welch's
day-by-day estimates (2005, 2018), with Mosiah to Moroni dictated in April-May and the small plates
(1 Nephi to Words of Mormon) in June. This order is what BOM-17's dictation-order segmentation
encodes.

## The style test for after the blind run (6.3)

`eval/scribes.py` compares how well the classical method (Cosine Delta, leave-one-out nearest
centroid on the middle MFW count) sorts the 2,000-word chunks by **narrator**, by **scribe** and by
**dictation order**, each against a label-permutation null. Narrators are separable (6.3) if the
narrator accuracy reaches the benchmark's Cosine Delta accuracy at 2,000 words (from
`data/benchmark/power.json`) and neither other segmentation is more accurate. It refuses to run
until BOM-32 has unblinded, because the chunks are the sealed text. Tested on synthetic text only.

## Not established

- Most of the original manuscript is lost (72%); the catalog covers what survives, mostly Alma
  through Ether in Cowdery's hand. 1 Nephi survives in part, in three hands.
- The printer's manuscript also carries later hands (printer's marks, the 1837 revisions); the
  transcript markup does not separate them from Cowdery's own corrections, which inflates its
  counts of insertions and deletions but should not create homophone fixes.
- Page words are credited to the hand that opens each page, so per-scribe rates are approximate
  where a page changes hands.
- The event typing is automatic. A human check of a sample of events (not yet done) would give
  its error rate; the homophone list is narrow by design, so it undercounts mishearings rather
  than inventing them.
- Skousen's catalogue of evidence (spelled-out names, the "twenty words at a time" span, read-back
  corrections) is not reproduced here beyond the counts above.

## Worth buying

- **Royal Skousen, *The Original Manuscript of the Book of Mormon: Typographical Facsimile of the
  Entire Text in Two Parts* (FARMS, 2001)**, and the companion printer's-manuscript facsimile. The
  standard transcriptions with every correction typed by Skousen; would let the automatic typing be
  checked against an expert's, event by event. Useful, not essential: the Papers' transcripts
  already carry the markup.
- **Skousen, *Analysis of Textual Variants of the Book of Mormon* (6 vols)** is more than this
  issue needs.
