# Amendment 9: known-answer controls for texts that claim to be ancient

*Filed 2026-10-31. Evidence: `docs/known-answer-plan.md`, `data/known_answer/set.jsonl`,
`eval/known_answer.py`.*

---

**Amendment 9, filed 2026-10-31, before any Phase 4-6 test has been run on the texts it names
and before any such test is run on the Book of Mormon.** It adds a validation step; no
hypothesis, decision rule or threshold of section 6 changes.

**What prompted this.** The Book of Mormon presents itself as an English translation of an ancient
record. The borrowing, dating, language-model and style tests measure what its English draws on.
A genuine translation made in the period is also written in period English by a period writer, so
a test that detects only period English cannot bear on the translation question. Each test must
first show, on texts whose answer is known, that it can tell the two cases apart.

**Change 1: the known-answer set.** Nine genuine period English translations of texts composed in
antiquity: the *Testaments of the Twelve Patriarchs* (1791), Laurence's *Book of Enoch* (1821),
Hone's *Apocryphal New Testament* (1820), Whiston's Josephus (1794), Sale's Koran (1800), Beloe's
Herodotus (1791), Pope's Homer (1783), Elton's Hesiod (1815) and Jones's *Sacontala* (1792).
Three compositions of their own century presented as ancient or old records: Macpherson's
*Ossian* (1800 edition), Chatterton's "Rowley" poems (1794) and Ilive's *Book of Jasher* (1751, the
1829 reprint). Secondary, reported but outside the verdict: W. H. Ireland's Shakespeare papers
(1796) and Walpole's *Castle of Otranto* (1782). One edition per text, every volume of it; the
volume ids are in `data/known_answer/set.jsonl`. The Apocrypha is excluded because the
registered King James mask (4.4) covers it. Each text is processed exactly as the Book of Mormon
is for the test in question (normalisation, King James mask, samples, null, exclusion of its own
copies).

**Change 2: what counts as separating the groups.** Before a test runs on the set, it commits the
score it gives each text and which direction means "draws on its own time". Separation is the
one-sided Mann-Whitney statistic of the three presented-as-ancient texts against the nine genuine
ones in that direction, with its exact permutation p-value over all 220 assignments; **a test
separates the groups when p is at most 0.01**, which allows at most one of the 27 pairs to fall
the wrong way. Because the Rowley poems are written in invented old spelling, each test also
reports whether it separates with Rowley's score set to the genuine median; if not, its result
carries the caveat "possibly on spelling alone".

**Change 3: what follows.** A test that separates the groups has its Book of Mormon result read in
the declared direction. A test that does not is reported as uninformative on whether the Book of
Mormon is a translation of an ancient record, whatever it says about the Book of Mormon; its
result may still bear on other questions (which candidate is closest, which source is borrowed),
and the report says which. Each test's known-answer result is written up before its Book of
Mormon result is interpreted, and every score for every text is published. With three texts in
the presented-as-ancient group, a test can show that it separates these texts, not every such
text; the paper says so.
