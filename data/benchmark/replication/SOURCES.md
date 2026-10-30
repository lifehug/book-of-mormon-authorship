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
