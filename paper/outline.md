# Paper outline, version 3 (owner and Claude, 2026-11-12)

A living document: saved every time the outline changes (owner, 2026-11-12). Items marked
**\*TBD** are being run now. Version 2 (2026-11-10) is in git history.

Principles: report every model and method objectively, side by side, then say which is best at
what (judged on known answers, never on the Book of Mormon); no averaging across methods; prior
methods are baselines, not votes; every post hoc step labelled; no position on the book's origin
or on inspiration. Each test is preceded by how it was prepared.

**Opening statement (section 1, said once, not repeated):** if the author is among the
candidates, the closest writing is Joseph Smith's revelations; whether the author is among them,
these tools cannot settle.

## 1. Introduction
The questions (who, what was borrowed, when); why two centuries of argument and four decades of
computer studies disagree; what is new here: models trained only on text printed before 1830, the
largest corpus and candidate set, every method tested on known answers first, a plan written in
advance, everything public and rerunnable. Then the opening statement.

## 2. The scale and preparation of the test
- **2.0 At a glance:** comparison table against every prior study (corpus size, candidates,
  controls, blind or not, "none of these" allowed or not, error rates measured or not).
- **2.1 Gathering:** 695,021 items catalogued 1780-1830 from five sources (Internet Archive
  307,567; HathiTrust 135,035; Harvard Institutional Books 31,958; Chronicling America 159,146
  newspaper pages) and 61,315 early-modern texts (1473-1700) for dating; what can and cannot be
  redistributed (`docs/holdings.md`).
- **2.2 Cleaning:** date audit, duplicate detection, OCR quality measured.
- **2.3 Labelling:** a genre label for every item, and its validation.
- **2.4 Sealing and masking:** the text kept from every model; King James masking; the quotation
  rule for candidate samples (Amendment 43).
- **2.5 Segmentation:** narrator, dictation order, scribe.
- **2.6 Candidate samples:** eight candidates, provenance tiers, sample sizes and their limits.
- **2.7 Controls and the benchmark:** control groups; known-author tasks (110 tests; 430 in BOM-75).
- **2.8 The time-locked language models:** 25.7 billion tokens, three sizes (125M, 297M, 590M;
  the 1B failure); all published.

## 3. Borrowing: the CES Letter's books, and everything else (lead section)
- **3.1 Copied wording:** 0.16% of the Book of Mormon matches earlier books (King James set
  aside), all stock religious phrasing; *The Late War* 8.9%.
- **3.2 Rare shared phrases:** *The Late War* and *Napoleon* pass the registered rule, but a
  reprint of Ilive's *Jasher* shares more: genre, not source.
- **3.3 Paraphrase:** *View of the Hebrews* first of 49 on its subject, but 85th percentile
  against 500 equally religious books, short of the top-1% bar.
- **3.4 Story order:** no book shares the plot; the test checked first on Josephus retelling
  Genesis-Judges (108 events in order).
- **3.5 The Letter's three books one by one** (`docs/ces-letter-books.md`): claim, every test,
  access, verdict; Spalding beside them, labelled as not from the Letter; the King James and
  place-name arguments listed as not tested.
- **3.6 Limit:** none of these tests can tell a real translation from a period book written to
  sound ancient (known-answer checks), so "no borrowing found" describes the text, not its origin.

## 4. Earlier authorship studies, re-run
Five studies reproduced with their own methods and data; their answers follow untested choices
(the 2008 study's Rigdon falls from 169 chapters to 92 with other genuine Rigdon text; the "none of
the candidates" study's error swings 80% to 0% with sample length).

## 5. How good is each method? A scorecard on known answers
- **5.1 Picking the right author from a list:** on BOM-75's 430 tests, every size beats every
  older method head to head (297M vs Burrows 59-9, vs ENSC 77-3; all 12 comparisons Holm p <
  0.0001; Amendment 52). On Part 1's 110 tests the disagreements were too few to call (4-0).
- **5.2 Period training matters:** GPT-2 86-92% false matches against ours 22-47%.
- **5.3 Writing in biblical style:** the imitation test is three authors (by author Burrows 1 of 3,
  297M 2 of 3; by passage 13/18 vs 7/17), too small either way; the 430 exam's pseudo-biblical
  task 2-0 on 24 tests. The ceiling is real: the corpus-wide curation (1,349 works judged, BOM-54)
  finds 18 imitation-scripture works by about 10 authors, of whom only 3 left enough other prose;
  outside 1780-1830 most imitation scripture is anonymous satire. Reported as too small to judge
  either way. A larger register-shift test (553 authors' sermons vs their other prose) was
  considered and not run (owner, 2026-11-12): the worry it addresses, that models follow biblical
  style rather than the person, is tested directly on the Book of Mormon in 6.2 and 6.3.
- **5.4 "None of these":** no method passes; 63-75% false matches on 430 tests. Why the opening
  statement is limited; said here once.
- **5.5 Model size:** sizes tie on picking the author; bigger is better only at "none of these",
  and not good enough there.

## 6. Joseph Smith, the deep dive
- **6.1 With and without revelations** (Amendments 44 and 53): with them, the 1828-29 revelations
  rank first at every size (159, 168, 131 of 168 chunks). Without them it depends on the method:
  Burrows and Cosine put his ordinary prose first; the language models put it mid-pack (Cowdery,
  his own letters or Phelps first by size); the style encoders Cowdery's 1829 sample; General
  Imposters Pratt.
- **6.2 Equal training dose** (Amendment 45): the revelations beat every same-sized sample at 125M
  and 297M; at 590M a slice of *The Late War* is ahead on 63% of chunks.
- **6.3 Writers who could not have written it** (Amendment 51): at 125M and 297M none of 67 slices
  reaches the revelations; at 590M Ilive does on 8 of 12, Dowling (born 1844) 9 of 12.
- **6.4 \*TBD: his later revelations** (Revelation Book 1, 1830-34, about 64,000 words, on disk):
  do they also rank near the top? 12 slices, like the placebo writers. Post hoc; written after he
  had dictated the book (influence possible); the pre-1830 test unchanged.
- **6.5 Seeds:** stable, with the caveat that one-batch models cannot vary.
- **6.6 His prose over time** (BOM-73): no drift toward the book's style.
- **6.7 Two readings, not decided:** same man, or same revelatory medium; these tools cannot tell.

## 7. The other candidates, one by one
Samples, ranks, cross-work recognition. Only Ethan Smith is recognized across his books (77/77),
and he is not closest; for Cowdery, Rigdon, Phelps and Pratt the models learned a book, not the
person. 7.1 Cowdery (the quotation leak), 7.2 Rigdon, 7.3 Spalding, 7.4 Ethan Smith, 7.5 Hunt,
7.6 Pratt, 7.7 Phelps.

## 8. Dating and internal voices
Language earlier than its period and than period imitations; narrators, dictation order, scribes.

## 9. Corrections and robustness
Every post hoc step in one table: the quotation leak (A43), equal dose (A45), seeds (A50), slices
(A51), the 430-test head-to-head (A52), the whole ranking with and without revelations (A53), the
V2 seed fluke, the imitation-test correction (2026-11-12).

## 10. Public claims
Seventeen claims, from every side, judged by rules written before any result.

## 11. What held
No copying and no borrowed plot; the named books do not stand out; earlier studies are fragile; at
picking the author from a list our models beat the older methods; the closest writing is the
revelation voice.

## 12. Limitations
The tests cannot separate translation from imitation; most candidates are not recognized across
works; no method can say "none of these"; the pre-1830 revelation sample is small (6.4 addresses
part of this).

## 13. Everything is public
Data tables, base and candidate models (Hugging Face), code, the pre-registration and every
amendment, the simulated reviews; how to obtain the licensed sources.

## 14. What comes next (Part 2)
Stage 0's result (still no method under 5% false matches on 430 tests); Stage 1 on hold.
