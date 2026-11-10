# What the paper left out: audit of 2026-11-10 (owner's request)

Method: a separate agent swept every GitHub issue (BOM-01 to BOM-86, with comments), the docs, the
blog, the replication report, the amendments and the simulated reviews, and listed every measured
result (`docs/results-inventory.md`, about 170 entries), without seeing the paper. Each entry was
then checked against `paper/paper.md`.

## Corrected (the paper was wrong)

- **Story structure:** the paper said no source meets the registered level; Church's *History of
  Philip's War* does (p 0.008, six generic military-letter events, about 4 in 10 chance among 49
  books). Sections 5.3 and 9.
- **King James italics:** the paper listed the CES Letter's italics argument as untested; BOM-62
  tested it. New section 6.5.

## Added

| Result | Where |
| --- | --- |
| Date audit scale and precision (19,463 moved; 81 of 100 truly later); placeholder 1800 dates | 2.2 |
| Duplicates across sources invisible to the text method; metadata pass | 2.2 |
| OCR error by source; 4-gram survival ~41%, so wording searches miss real matches | 2.2, 11 |
| No western New York papers in the national set; *Ontario Phoenix* not digitized | 2.1, 10.8 |
| King James mask precision and recall; Phinney 1828 Bible consistent with the 1769 text | 2.4 |
| Power analysis (~10,000 words); time-split validation failed for every method | 2.6, 10.1 |
| Burrows' Delta and ENSC rank as well as the models on the same 110 tests (gain is in matching) | 4.1 |
| Classical methods fall to 55-60% on 30 fresh authors; GI fidelity; ENSC not as published at first; multiverse | 4.1 |
| Decoy accuracy below benchmark for Cosine Delta and the 297M style encoder | 5.1 |
| Grunder's proposed parallels (exploratory); Josephus on sale in Palmyra and in Grandin's stock | 5.2 |
| 7 of 25 period imitations dated early modern; keyed text dates earlier than OCR text | 5.5 |
| Narrator vs dictation order corrected for chance (0.645 vs 0.514); page dependence in the manuscript tests | 5.6 |
| *The Late War*'s 183 phrases by how many other books use them; rarity by text, not volume | 6.2 |
| Synthesis sensitivity (equal weights ~0.99; drop GI = prior) | 7.3 |
| Amendments 8, 20-21, 31 (disclosed leak) in the post hoc table | 7.4 |
| Process failures: ALTO deletion, near-publication of licensed text, discarded models, corrected wrong results | 7.5 |
| Training volumes with 1-19 shared strings unreported; planned-and-not-run list; genre label agreement | 11 |

## Left out on purpose (in the inventory and the repository)

Ingest mechanics (pull rates, filename recovery, field-name bugs), cleaning counts, embedding-model
selection details, style-encoder training figures, the sweep's plausibility gate, index integrity
and backup checks, corpus freeze DOIs, the secondary synthesis (post-1830 candidates; their samples
cannot stand in for earlier writing, section 2.6), and manuscript alignment statistics. None
changes a result or its reading.

## Inconsistencies found in the record

Joseph Smith's pre-1830 sample appears as 2,844, 3,082, 2,741, 2,720, 2,710 and 2,702 words at
different stages; the paper now states 2,844 before masking, 2,720 after, 3,039 model tokens.
Cowdery's Articles: 40.4% shared (the analysis) against 41.9% (a commit message); the paper uses
40%. ENSC "none" share 94% (report) against 98% (an issue comment); the paper uses the report's
225 of 239.
