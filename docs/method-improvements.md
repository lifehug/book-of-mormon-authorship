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
| 15 | ENSC's code looped over classes (fine for 4 authors, hopeless for 23,875) | Same maths vectorised; tested equal to the original (`sweep/older.py`) | Older methods run as library sweeps on the 200 known books: true author first 20.5-27% (Burrows 25, Cosine 27, ENSC 23, GI 20.5), in the top 1,000 70-78%; none near the 70% bar. Any of the four first: 30%. Cosine reproduces the registered 27% exactly | yes (engineering); the methods themselves: **no** |
| 16 | Our author models were only tested on lists of 4 | Every list size from 2 to 55, all sizes, one score table (Amendment 58) | 86% from 55 at 125M and 297M, 82% at 590M; older methods 49-62%. Bigger models do not help. A few models score low on everyone's text (the cause of long-list errors) | yes (measurement) |
| 17 | The library search missed authors whose other writing is a different genre; its encoder had memorised its training authors (loss 0.03, held-out accuracy flat from step 1,000) | A second encoder: 8 times the passages per work, one-genre batches with positives from another genre, a validation split; scored on each author's closest episode; stopping rule set first (`style_embed/v2.py`, `sweep/episodes.py`) | Top 100: 71.5% to 80.5% of known books; top 1,000: 86% to 90% (cross genre 76% to 82%). Better at short lists (13 books gained, 4 lost at 100), no different at 1,000 | partly |
| 18 | "Could have written it" was not in the data | Life dates from the catalog, then a single plausible Library of Congress match, checked on 500 known answers (`sweep/people.py`) | 6,016 alive, 5,584 dead or too young, 12,275 unknown; the rule agrees with the catalog on 212 of 219. Dates only 13% of undated names | yes, with a large unknown group |
| 19 | The plan put the author models in charge of the shortlist without testing them there | One shared pool of 1,000 library authors, equal-dose models, tested on the 200 known books before any Book of Mormon run (`eval/library_pool.py`) | Author models first of 1,000: 42-44%; the style encoder on the same pool: 66% (ahead on 96 books, behind on 19). The plan was changed: the encoder ranks, the models are a second opinion | **no** for the author models on this task; yes for testing first |
| 20 | A top-of-library list could be a genre | The dead stay in the ranking as decoys; every ranking at equal profile sizes; the procedure frozen in one commit first (`eval/library_bom.py`) | Dead authors are 23% of the library and 30-45% of each top 20: the top is first-person religious testimony and revelation | yes, as a check |

## Lessons

- **A quick check that looks like a big win needs the strict version before it is believed**
  (#10: a split by test made normalisation look like 1 in 5 → 3 in 4; split by author it failed).
- **Count the right unit.** Passages from one author are not independent (#8). The fix was more
  authors (#9), not a different test.
- **Write the rule before the run, including when to stop** (#9). It is what makes "settled" mean
  something.
- **Our approach's cost grows with the number of people** (#2, #14). That is its real limit, and
  the reason for the labelled-model design.
- **Test the tool on the job before giving it the job** (#19). The author models were the best tool in
  Phase 1 and the weaker one here; one $17 run on known books showed it before the real run.
- **An equal-dose rule has a price.** Giving every author the same small amount of text is fair and
  makes every model weaker; measure how much (#19: 28% against 42-44%).
