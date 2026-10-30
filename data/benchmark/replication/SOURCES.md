# Replication inputs (BOM-22)

The designs being replicated are in `docs/prior-studies.md`.

| File | Source | What it is |
| --- | --- | --- |
| `book-of-mormon-pg17.txt` | https://www.gutenberg.org/cache/epub/17/pg17.txt, fetched 2026-10-30 (public domain) | the 1920 edition with modern chapters and verses; used **only** for chapter boundaries |
| `longfellow-hiawatha-pg19.txt` | https://www.gutenberg.org/cache/epub/19/pg19.txt, fetched 2026-10-30 (public domain) | Longfellow, *The Song of Hiawatha* (1855), a control in Jockers et al. 2008; outside the 1780-1830 corpus |
| `chapters_1830.jsonl` | `python -m eval.replicate chapters` | the 239 modern chapters located in the **1830** text: each chapter's first 30 words found by fuzzy alignment in the 1830 text of the same book (the earliest match within 5 points of the best, at least 80), and the 1830 text cut there. Chapter lengths agree with the 1920 edition's (median ratio 1.00; all within 0.8-1.25 bar two last-chapters whose Gutenberg length runs into the next book). Each row: book, chapter, word offsets, first and last 1830 paragraph, anchor score, text |

Other inputs: Barlow's *The Columbiad* (1825) is in the corpus (`institutional_books:HXTAZ5`);
the 1835 *Doctrine and Covenants* (Lectures on Faith, revelations) is fetched from the Joseph
Smith Papers to the private repo (`python -m ingest.jsp dc1835 --out data/private/replication`).

## `jockers2008/` (BOM-22, 2026-10-30)

Supplementary data for Jockers, Witten and Criddle (2008), deposited by the authors in the
Stanford Digital Repository: https://purl.stanford.edu/rs276tc2764 (druid rs276tc2764), licence
CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/legalcode). Attribution: Matthew L.
Jockers, Daniela M. Witten and Craig S. Criddle.

| File | What | md5 (as published) |
| --- | --- | --- |
| `dataMatrix.txt` (not in git, 18,460,457 bytes) / `dataMatrix.txt.gz` (gzip -9 of it) | word counts: 456 samples (239 Book of Mormon chapters as "Unknown"; Barlow 12, Cowdrey 19, Isaiah 66, Malachi 4, Longfellow 23, Pratt 53, Rigdon 23, Spaulding 17) x 19,992 words | d18facd07eb4b8e100571da6711df974 |
| `bom.xml` | their 1830 Book of Mormon text with modern chapters | 9da7d28e630318f465a874deb20a97a3 |

Downloaded from `https://stacks.stanford.edu/file/druid:rs276tc2764/<file>`. The deposit notes a
tokenising error corrected by the authors on 2009-01-09 (one chapter's ranking changed); this is
the corrected data. Read by `python -m eval.replicate jockers-data`.

`python -m eval.replicate jockers-pamr` runs `eval/jockers_pamr.R` and needs R with the `pamr`
package (CRAN; used here: R 4.6.2, pamr 1.57, installed with `brew install r` and
`install.packages("pamr")` into `~/.R/library`).

## `larsen_speakers.jsonl`, `larsen_speakers_check.txt` (BOM-22, 2026-10-30)

Speaker labels for the 239 chapters of `chapters_1830.jsonl`, for the Larsen et al. (1980)
replication: `python -m eval.speakers label --model sonnet` (Claude Sonnet via `claude -p`;
**simulated labelling, not a human reading**). Append-only log: the last record per chapter
counts; earlier records keep the replies that failed to parse and the one chapter (Jacob 5)
relabelled after the parable rule was added. Three prompt formats were used in turn (change
points; one label per unit; labels keyed by unit number); the final labels of 133 chapters came
from the first two formats and passed their stricter checks. `larsen_speakers_check.txt` is
`python -m eval.speakers check`: per-speaker word totals against Larsen et al.'s Appendix B.
