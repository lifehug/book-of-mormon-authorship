# Amendment 18: a known limit on replication, and the derived tables that lower it

*Filed 2026-11-01. Evidence: `docs/derived-data-terms.md`, `eval/derived.py`, `data/derived/export.json`.*

---

**Amendment 18, filed 2026-11-01.** It adds a known limit to section 10 and records what is
published to reduce it. No hypothesis, decision rule or threshold changes, and no analysis
changes.

**The limit.** The corpus cannot be redistributed from this project: Harvard's Institutional Books
terms forbid sharing the text in whole or in part, the HathiTrust researcher agreement forbids
distributing the dataset, and the Joseph Smith Papers transcriptions are copyrighted. So nobody
can rebuild the corpus from the project's own files. They can obtain the same sources under their
own agreements (`docs/replication.md` gives the steps), and the checksum manifests prove they hold
the same bytes.

**What is published instead.** Derived tables the analyses read, which cannot be assembled back
into text: for the validation benchmark (6.1), every 1,000-token reference block, test sample and
imposter-pool sample as counts over its task's 1,000 most frequent words; for the rare-phrase
borrowing test (5.5, 6.5) and its known-answer scans, every scanned volume's word count and the
hashes of the target's 4-grams it contains; the catalog with genre, date, OCR-quality and
deduplication labels; the dating segments' grammatical rates. A complete list of one text's 4-gram hashes can be unrolled back into that text, so hashes are published only for targets whose own text is from an open source (the Book of Mormon and the known-answer texts from the Internet Archive); the two known-answer targets whose copies came from HathiTrust and Harvard (Enoch, Josephus) are withheld. Harvard-derived rows carry Harvard's
attribution (its terms allow summary statistics that cannot substitute for the original); rows
derived from Joseph Smith Papers transcripts are not published.

**What an outsider can and cannot reproduce from these alone.** Can: the benchmark accuracies and
thresholds of the classical methods; the rare-phrase source list, its null and percentiles; the
known-answer separation of that test, less the two withheld targets; the dating classifier's grammar model. Cannot, without
obtaining the sources: anything that reads running text, namely passim alignment, the
semantic-parallel and story-skeleton tests, the language models, style embeddings, the lexical
dating model and the corpus-wide author sweep; and anything on the Joseph Smith Papers samples.
