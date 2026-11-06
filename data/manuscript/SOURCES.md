# data/manuscript

BOM-34: corrections in the original and printer's manuscripts (`docs/manuscript-evidence.md`).
Ids, pages, hands, categories and counts only; no manuscript words.

| File | What | Rebuild |
| --- | --- | --- |
| `corrections.csv` | one row per correction: manuscript, page, editorial page, scribe, event (substitution, false start, deletion, insertion), type (homophone, sound-alike, spelling, other), immediate, name flag, words struck and added, paragraph range | `python -m manuscript.corrections build` |
| `summary.json` | counts by manuscript and scribe; dictated against copied, on all pages, on the same passages, and with the scribe held fixed (Fisher tests) | the same |

The word pairs themselves are the Joseph Smith Papers' transcription (copyright Intellectual
Reserve) and stay in the private data repository, `data/private/manuscript/corrections.jsonl`.
Inputs: `data/private/bom/jsp_original.jsonl`, `jsp_printers.jsonl` (see `data/bom/SOURCES.md` and
`docs/replication.md` for how to obtain them); page-to-paragraph alignment
`data/bom/align_original.jsonl`, `align_printers.jsonl`.

## Sources cited in docs/manuscript-evidence.md

- Joseph Smith Papers, Original Manuscript of the Book of Mormon, circa 12 April 1828-circa 1 July 1829, source note and historical introduction: https://www.josephsmithpapers.org/paper-summary/original-manuscript-of-the-book-of-mormon-circa-12-april-1828-circa-1-july-1829/1
- Joseph Smith Papers, Printer's Manuscript of the Book of Mormon, circa August 1829-circa January 1830, source note: https://www.josephsmithpapers.org/paper-summary/printers-manuscript-of-the-book-of-mormon-circa-august-1829-circa-january-1830/1
- Joseph Smith Papers, Copyright for Book of Mormon, 11 June 1829: https://www.josephsmithpapers.org/paper-summary/copyright-for-book-of-mormon-11-june-1829/1
- Royal Skousen, "How Joseph Smith Translated the Book of Mormon: Evidence from the Original Manuscript", Journal of Book of Mormon Studies 7/1 (1998): 22-31: https://scholarsarchive.byu.edu/jbms/vol7/iss1/4
- John W. Welch, "Timing the Translation of the Book of Mormon: 'Days [and Hours] Never to Be Forgotten'", BYU Studies Quarterly 57/4 (2018): https://scholarsarchive.byu.edu/byusq/vol57/iss4/3 ; the day-by-day chronology in Welch, "The Miraculous Timing of the Translation of the Book of Mormon", in *Opening the Heavens* (2nd ed. 2017), pp. 78-125: https://archive.bookofmormoncentral.org/sites/default/files/archive-files/pdf/welch/2021-07-09/03_john_w._welch_the_miraculous_timing_of_the_translation_of_the_book_of_mormon_78-125.pdf
