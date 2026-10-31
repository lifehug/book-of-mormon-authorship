# Amendment 10: how exact text reuse is searched, and its known-answer score

*Filed 2026-10-31. Evidence: `docs/reuse-plan.md`.*

---

**Amendment 10, filed 2026-10-31, before passim has been run for reuse on any text** (Book of
Mormon, controls or known-answer texts). No hypothesis, decision rule or threshold of section 6
changes.

**What prompted this.** 5.5 registers exact and near-exact reuse by passim over the masked text
against the deduplicated corpus, but not how a corpus of about 221,000 volumes is searched, nor the
score each text receives under Amendment 9's known-answer test.

**Change 1: the reuse table.** The KJV-masked 1830 text is aligned against every eligible period
volume (1780-1830, deduplicated, OCR exclusions applied, its sealed copies left out), with
Amendment 2's passim settings (word 5-grams, at least 8 tokens, gaps of at most 100 characters,
relative overlap 0.5, document-frequency cap 100, at least 4 shared 5-grams to seed). Every
aligned passage is published with source, offsets, length and token identity, without text.
Reference tables are built the same way for Hunt's *The Late War* (against volumes printed before
1816) and for one 1820s sermon collection drawn with seed "bom23-sermon" from the registered
sermons control.

**Change 2: two implementation steps that do not change what is found.** (a) A prefilter: one
pass records which of each target's 5-grams every volume contains, and volumes sharing fewer than
4 are not aligned, since passim cannot align them. (b) Document frequency at the scale of the
search: passim is run in batches with its own cap off, and an alignment is kept only if it holds
at least 4 distinct 5-grams whose document frequency across the whole search is at most 100,
which are the alignments one passim run over the whole search would have seeded.

**Change 3: the known-answer score.** A whole-corpus search cannot be compared across texts,
because the corpus holds far more volumes before 1830 than before 1760 and a text with more
earlier books to search finds more matches whatever its origin. So every text, the Book of Mormon
included, is searched against 2,000 English volumes drawn from those printed in the 70 years
before its English was written (deduplication keepers, OCR exclusions applied, newspapers,
Bibles and New Testaments and the text's own copies left out), in 3 seeded draws. The score is
the mean share of the text's masked tokens covered by an aligned passage; higher means it draws
more on writing of its own time. The years: Book of Mormon 1829; *Testaments of the Twelve
Patriarchs* 1581 (Golding's English); *Enoch* 1821; *Apocryphal New Testament* 1726 (Jones's and
Wake's translations); Josephus 1737; Koran 1734; Herodotus 1791; Homer 1715; Hesiod 1812;
*Sacontala* 1789; *Ossian* 1760; Rowley poems 1768; *Jasher* 1751; Ireland papers 1795;
*Otranto* 1764.

**Known confound, stated before any result.** Volumes before 1700 keep old spelling, which breaks
matches and lowers a score. Five of the nine genuine translations have 90-100% of their window
before 1700; the three presented-as-ancient texts have 27-84%. A separation by this score can
therefore reflect spelling era rather than origin. Each score is published beside its window's
pre-1700 share. A separation under Amendment 9 counts only if it also holds among the texts whose
windows are mostly before 1700: *Ossian* and *Jasher* must each score above the median of the
*Twelve Patriarchs*, *Apocryphal New Testament*, Josephus, Koran and Homer. Otherwise the test is
reported as not shown to separate the groups.
