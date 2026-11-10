# Claims register: verdicts (BOM-42)

Drafted 2026-11-10, after unblinding, by applying each claim's `supported_if` / `contradicted_if`
rule in `data/claims/register.yaml` (written before any result) to the results; reviewed and
approved by the owner the same day and written into the register. Allowed verdicts: supported,
contradicted, mixed, not_addressed; four claims are untestable by design. The register takes no
side, and being unable to test a claim is not evidence against it.

Sources for the evidence: `paper/draft/results_so_far.md` 1 (borrowing), `docs/results-first-read.md`
(blind results), `data/dating/h3c.json`, `data/benchmark/scribes.json`.

| Claim | Source | Verdict | Why, by the claim's own rule |
| --- | --- | --- | --- |
| c01 *The Late War* shares unusual rare phrases | CES Letter, Johnson 2013 | **mixed** | It beats the 99th percentile of its null on rare phrases (22 phrases, p 0.0006, rank 131 of 204,520), which meets `supported_if`; but a control of the same genre and period scores higher (Ilive's *Book of Jasher*, 1829 reprint: 7.99 vs 3.86 per 10,000 words), which meets `contradicted_if`. Paraphrase is inside its null (80th percentile); no triaged pair is specific. |
| c02 *View of the Hebrews* shares themes closely enough to suggest dependence | CES Letter | **contradicted** | Its paraphrase score is inside the null (84.6th percentile; 77 of 500 matched religious volumes score higher), story order shares 2-3 events (p 0.97-1.0), and triage finds no specific pair. |
| c03 Cowdery's link to Ethan Smith's congregation | CES Letter | untestable | Biographical and access question (register's reason). |
| c04 About 80 early-modern word uses obsolete by 1830 | Skousen and Carmack | **not_addressed** | The rule tests the 80 forms one by one; this study dates the text as a whole and did not test that inventory. The aggregate dating (c05, c16) is reported beside it. |
| c05 Early-modern syntax that King James imitation cannot explain | Skousen and Carmack | **mixed** | The grammar model places the masked text in the early-modern window (78% of segments before 1700, H3b), and period pseudo-biblical controls do not get there at a similar rate (7 of 25 volumes; H3c rejected, p 0.0001): `supported_if`'s first half and its imitation half by that test. But the transformer cross-check, the one model imitation did not move in validation, dates the text to about 1755, outside the early-modern window. |
| c06 Dictation under "tight control" | Skousen and Carmack | untestable | Production mechanism (register's reason). |
| c07 Rigdon and Spalding contributed (Jockers 2008) | Jockers et al. | **contradicted** | Neither is supported under the pre-registered rule (no family returns *match* for either; the synthesis gives Spalding 0.085 among the primary candidates). |
| c08 Narrators distinct from each other and from 19th-century candidates | Larsen et al. 1980 | **contradicted** | Narrators separate above chance (0.744 vs 0.277) but below the 0.96 benchmark accuracy for distinct authors, and dictation order separates the chunks about as well (0.758). |
| c09 With "none of the above" allowed, no 19th-century candidate is the author | Fields 2011 | **supported** (by the rule; see caveat) | Caveat (BOM-38): the synthesis covers only Ethan Smith, Hunt and Spalding; Joseph Smith and Cowdery are untested by it, too little pre-1830 writing surviving. H1b's condition holds: no candidate is supported under the pre-registered rule, and the synthesis favours "not in set" (0.744). Caveat: no method passes the open-set bar, so "none supported" is graded evidence. |
| c10 The text belongs to the American pseudo-biblical genre, whose conventions explain much of its style | Shalev | **mixed** | It shares the genre's stock phrasing (*The Late War*, *Napoleon*, *Jasher* lead the rare-phrase list) but separates from the genre's controls on grammar features that survive KJV masking (H3c rejected), which meets `contradicted_if`. |
| c11 DNA cannot settle population questions | Gospel Topics | untestable | Genetics (register's reason). |
| c12 Dictated without notes or manuscripts | Gospel Topics | untestable | Production process; taken as a stated limit (register's reason). |
| c13 Spalding's manuscript supplied the story or text | Howe 1834 | **contradicted** | *Manuscript Story* ranks 12 of 49 in paraphrase, shares 1 rare phrase (p 0.068) and 4 events out of order (p 0.67), no triaged pair is specific, and Spalding is not supported under 6.2. Only the surviving 1884 manuscript is tested. |
| c14 *The First Book of Napoleon* shares wording closely enough to suggest dependence | named sources | **mixed** | Rare phrases beat its null (12 phrases, p 0.0003), but no triaged pair is specific under both passes (which `supported_if` requires) and paraphrase is inside its null (98.4th percentile, below the 99th). |
| c15 Cowdery or Rigdon wrote or substantially shaped the text | named sources | **contradicted**, with a caveat | Neither is supported under 6.2. Correction (2026-11-10): Cowdery's pre-1830 sample was 40% Book of Mormon quotation; without the quotations (Amendment 43) his sample no longer ranks high and neither he nor Rigdon is matched. Earlier caveat: Cowdery's pre-1830 sample (1,310 words) is under the 10,000-word floor; the candidate models rank that small sample first for many chunks at 590M, which is not support under the rule and is discussed in `docs/results-first-read.md` 2. |
| c16 The text reflects its 1820s environment in its language | Brodie 1945 | **contradicted** (language only) | The majority of segments fall in 1473-1700 (H3b), and period imitation does not produce that placement (H3c rejected). Thematic dating (BOM-63) is separate. Neither reading says how the text was produced. |
| c17 Narrators not distinct, and close to Joseph Smith's revelation texts (Holmes 1992) | Holmes 1992 | **supported** | Narrators are not separable under 6.3; Joseph Smith's dictated sample is the closest candidate by Cosine Delta (131 of 168 chunks) and Burrows' Delta (77), though General Imposters ranks Pratt first more often (74 vs 48); without Book of Mormon quotations in the samples (Amendment 43) all three classical methods rank Joseph Smith first (148, 91, 66 tied with Pratt). Closest is not a match, and his sample is the only one in the book's register. |

**Totals:** supported 2, contradicted 6, mixed 4, not addressed 1, untestable 4.

The verdicts are in `data/claims/register.yaml`; `python -m eval.claims table` writes the claims
table (`data/claims/claims.json`) for the paper's section 10.
