## 10. Public claims

Seventeen public claims about the Book of Mormon's text, taken from critical, apologetic and
academic sources, were written into a register together with the rule that would decide each one,
before any result existed (`data/claims/register.yaml`). The verdicts below apply those rules
(`docs/claims-verdicts.md`). Four verdicts are allowed: supported, contradicted, mixed, and not
addressed. Four claims were marked untestable by text analysis from the start. The register takes
no side, and an untestable claim is not a contradicted one.

| Claim | Source | Verdict |
| --- | --- | --- |
| c01 *The Late War* shares unusual rare phrases | CES Letter; Johnson and Johnson 2013 | mixed: it passes its null, but a control of the same genre scores higher |
| c02 *View of the Hebrews* shares themes closely enough to suggest dependence | CES Letter | contradicted |
| c03 Cowdery's link to Ethan Smith's congregation | CES Letter | untestable (biography) |
| c04 About 80 early modern word uses that were obsolete by 1830 | Skousen and Carmack | not addressed (the forms were not tested one by one) |
| c05 Early modern syntax that King James imitation cannot explain | Skousen and Carmack | mixed: the grammar model agrees; the transformer cross-check dates the text to about 1755 |
| c06 Dictation under "tight control" | Skousen and Carmack | untestable (production) |
| c07 Rigdon and Spalding contributed | Jockers et al. 2008 | contradicted |
| c08 Narrators distinct from each other and from the candidates | Larsen et al. 1980 | contradicted |
| c09 With "none of the above" allowed, no nineteenth-century candidate is the author | Fields et al. 2011 | supported by the rule as written, with caveats (below) |
| c10 The text belongs to the American pseudo-biblical genre | Shalev | mixed: it shares the genre's stock phrasing and separates from it on grammar |
| c11 DNA cannot settle population questions | Gospel Topics essays | untestable (genetics) |
| c12 Dictated without notes or manuscripts | Gospel Topics essays | untestable (production) |
| c13 Spalding's manuscript supplied the story or text | Howe 1834 | contradicted (for the surviving manuscript) |
| c14 *The First Book of Napoleon* suggests dependence | named sources | mixed |
| c15 Cowdery or Rigdon wrote or shaped the text | named sources | contradicted, with a caveat (below) |
| c16 The language reflects its 1820s environment | Brodie 1945 | contradicted (language only; themes were not tested) |
| c17 Narrators not distinct, and close to Joseph Smith's revelations | Holmes 1992 | supported |

**Totals:** supported 2, contradicted 6, mixed 4, not addressed 1, untestable 4.

**When the verdicts were set, and what has changed since.** The owner set the verdicts from the
pre-written rules on 2026-11-10, the day of unblinding. They have not been re-graded. Several
later results bear on them, and are stated here so that no verdict reads as stronger than its
evidence.

- **c09.** The rule asks whether any candidate is supported under the registered procedure, and
  none is. But the registered synthesis it leans on covers three candidates and cannot recognise
  an author's own text (section 9.3), and no method can say "none of these" at the registered
  error rate (section 5.4). "Supported" here means the registered condition was met, not that
  the candidates are excluded. Whether to re-grade c09 is open and is the owner's decision before
  release.
- **c07 and c15.** "Contradicted" means neither Rigdon, Spalding nor Cowdery is supported under
  the registered rule, and that Cowdery's high ranking in the registered run was quotation
  (section 7.1). It does not mean excluded. The language models do not recognise Rigdon or
  Cowdery across their own works (section 7), and both are represented mainly by writing from
  after 1830.
- **c17.** The verdict cited the classical methods' rankings. The later checks sharpen what
  "close to Joseph Smith's revelations" means: it holds for his revelations of 1828-29 and of
  1830-34, not for his ordinary prose under the language models and style encoders, and at the
  590M size other writers of imitation scripture rank as high (section 6). Closest is not a
  match.
- **c05 and c16.** The dating results carry the cautions of section 8.1: an early date is
  predicted by an early source, by imitation, and by the King James register alike, and the text
  is hand-keyed where most comparison text is scanned.
