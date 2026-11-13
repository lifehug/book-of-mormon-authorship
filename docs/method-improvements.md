# How the method was improved, step by step

A running record (owner, 2026-11-12: "document how we improve the algorithm for this type of
work"). One entry per change to how authorship is measured: what was wrong or missing, what
changed, what it did to the results, and whether it worked. Failures stay in. Each entry names
the amendment (`paper/preregistration.md`, section 11) and the files. Add to it whenever the
method changes.

| # | Problem | Change | Effect | Worked? |
| --- | --- | --- | --- | --- |
| 1 | Modern language models have read the Book of Mormon and everything after it | Train our own models only on text printed 1780-1830 (25.7 billion tokens; 125M, 297M, 590M) | GPT-2 in the same setup: 86-92% false matches; ours 22-47% (5.2) | yes |
| 2 | Word counts throw away word order and phrasing | One fine-tuned copy of the period model per candidate; score = how much better it predicts a passage than the untuned model (loss minus base) (Amendment 22) | Better than every older method at picking the author (#9) | yes |
| 3 | King James quotation would read as shared style | Mask King James spans in every text before any method sees it (BOM-16) | 3.7% of candidate words masked; the Book of Mormon's biblical passages do not drive matches | yes |
| 4 | Candidate samples quoted the Book of Mormon (Cowdery's 1829 Articles 40% verbatim) | Drop passages of 20+ shared words written after the passage was dictated; keep shared idiom (Amendment 43) | Cowdery's false closeness removed; results re-run beside the registered ones | yes |
| 5 | Bigger samples win just by being bigger | Equal-dose check: every model trained on exactly the revelation sample's 3,039 tokens (Amendment 45) | Revelations still first at 125M and 297M; at 590M a *Late War* slice ahead | yes, as a check |
| 6 | Closeness might be biblical register, not the person | Placebo writers who could not have written it, on 12 slices each (Amendments 49, 51) | Register reaches the revelations at 590M only | yes, as a check |
| 7 | One random slice can mislead | Grid of up to 12 evenly spread slices per writer instead of 1-2 random ones (Amendment 51) | "Slice-stable" reading defined and measured | yes |
| 8 | Window-level counts overstate certainty (one author's 20 windows move together) | Count by author; sign test, Holm correction, author-resampled intervals (Amendment 55) | p < 0.0001 by window became p 0.13-0.15 against Burrows on 23 authors: an honest correction | yes |
| 9 | 23 authors too few to decide | 32 more authors by the same rules, decided first, with a stopping rule (Amendment 56) | Ours better than all four older methods at every size on 55 authors (Holm p <= 0.0014); the 32 new alone repeat it | yes |
| 10 | "None of these" threshold fails (63-75% false matches) | Score normalisation from speaker verification (z-norm, z-margin), tested leaving each author out (Amendment 55) | Held-out false matches 17-26% at a 5% target: does not carry to new authors. An exploratory split by test had suggested it worked; that split leaked | **no** |
| 11 | Reporting one failed bar hides how good a verifier is | Report the whole trade-off curve (area under it, equal-error rate, true authors confirmed at 1/2/5/10% false matches) (Amendment 55) | At a 5% target our models confirm 38-61% of true authors; AUC 0.89-0.91 | yes (reporting) |
| 12 | The 168 sealed chunks are the book cut twice | Report every count per chunk length (Amendment 55) | The two lengths agree | yes (reporting) |
| 13 | Only a 3,039-token pre-1830 revelation sample | His 1830-34 revelations as a deep dive, on the same slices (Amendment 54) | Every later slice ranks right behind the 1828-29 sample at 125M and 297M | yes, as a check |
| 14 | Our best method needs one model per candidate, so it cannot search a library (23,875 authors) | One period model trained on every author's profile with an author label; score = loss under the label minus under "unknown" (Amendment 57) | *running* | *pending* |
| 15 | ENSC's code looped over classes (fine for 4 authors, hopeless for 23,875) | Same maths vectorised; tested equal to the original (`sweep/older.py`) | Older methods can run as library sweeps | yes (engineering) |

## Lessons

- **A quick check that looks like a big win needs the strict version before it is believed**
  (#10: a split by test made normalisation look like 1 in 5 → 3 in 4; split by author it failed).
- **Count the right unit.** Passages from one author are not independent (#8). The fix was more
  authors (#9), not a different test.
- **Write the rule before the run, including when to stop** (#9). It is what makes "settled" mean
  something.
- **Our approach's cost grows with the number of people** (#2, #14). That is its real limit, and
  the reason for the labelled-model design.
