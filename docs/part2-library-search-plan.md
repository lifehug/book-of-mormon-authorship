# A library-wide author search with our own models (scope, 2026-11-12)

Status: **scoped, not approved, nothing run.** Part 2 work, separate from the paper. Every step
below needs a dated amendment before it runs (no OSF; repo only).

## The question

Can our period-trained language models search the whole 1780-1830 library (23,875 authors) for the
author of a text, well enough to name names? If so, does anyone in the library stand out for the
Book of Mormon who has not been proposed?

## Why a new design is needed

Our best method trains one model per candidate. That beat every older method on 55 known authors
(Amendment 56), but a model for each of 23,875 authors would cost about $10,000. The older methods
and our style encoder already sweep the library cheaply, but on 200 books of known authorship
they put the true author first only 27% (Cosine Delta) and 30% (style encoder) of the time, under
the registered 70% bar (`data/sweep/calibration.json`). The style encoder's median rank for the true
author is 4 of 23,875: a good search engine, not sure enough to name anyone.

## Design: one model that knows every author

Continue training our 297M period model on the sweep's author profiles, each block preceded by
its author's label (one new token per author). Train a share of blocks under an "unknown author"
label too. To score a passage for author A: its loss under A's label minus its loss under
"unknown". This is the same signal as our fine-tuned models (loss minus the base model's), from
one model instead of 23,875.

| Item | What we have | Source |
| --- | --- | --- |
| Training text | 458,208 profile blocks of 1,000 words (up to 20 per author), King James masked | `data/sweep/blocks.parquet`, `sweep.index` |
| Held-out test | 200 calibration books (2,433 query blocks); their authors' profiles rebuilt without the book (3,869 blocks) | same |
| Shortlist for scoring | style encoder and Cosine Delta distances to every author | `sweep.calibrate` |
| Plausibility gate for leads | period AND (place OR access), Amendment 40 | registered |
| Base models | 297M and 590M | `data/corpus/timelocked_lm/runs/` |

## Steps

0. **Free, on the Mac: the older methods as a sweep.** Burrows' Delta and ENSC over all 23,875
   authors on the 200 books (minutes to an hour); General Imposters on each book's top 1,000
   (hours). This fills the "prior work as a sweep" row: today only Cosine Delta (27%) and the
   style encoder (30%) have been measured.
1. **Build the labelled training set** (Mac): ~460 million words, ~600 million tokens.
2. **Continued training, 297M** (H100): about 0.6 billion tokens an epoch at the measured 196,000
   tokens/s (BOM-27's base run: 25.65 billion tokens in 36.4 hours) is ~50 minutes; two epochs.
3. **Known answers** (H100): each of the 2,433 query blocks scored against a shortlist of 1,000
   authors (union of the style encoder's and Cosine Delta's closest), ~2.4 billion tokens forward,
   about an hour. Report the shortlist's own recall (true author in it or not) separately.
4. **Decide usable or not** by the registered sweep bar (true author first in 70% of the 200
   books), beside top-10, median rank, and every older method from step 0.
5. **Only then the Book of Mormon**: its sealed chunks as 1,000-word blocks (~350), the same
   shortlist rule, the registered lead threshold, every lead through the plausibility gate, and a
   register check (scripture-style writers rank high for sounding biblical; the BOM-76 placebo
   logic applies).

## Cost (297M)

| Step | H100 time | Cost |
| --- | --- | --- |
| 0, 1 | none (Mac) | free |
| 2 training | ~1.7 h | ~$5 |
| 3 known answers | ~1.2 h | ~$4 |
| 5 Book of Mormon | ~0.2 h | ~$1 |
| setup, uploads, one retry | | ~$5-10 |
| **Total** | | **~$15-20** |

The 590M roughly doubles it (~$30-40 more), and would follow only if the 297M is promising. The
balance is about $31.

## What it can and cannot show

- **If it passes 70% on the 200 books:** the first library-wide authorship search good enough to
  name names, built on period-trained models. Its Book of Mormon list would be a real candidate
  list.
- **If it does not:** how far our approach moves the needle from 27-30%, and a better-ranked
  shortlist that can point, not name.
- **Never:** "none of these". A search ranks the library; it cannot say the author is outside it.
- **Register:** writers who imitate scripture will rank high for sounding biblical; any such lead
  needs the placebo check before it means anything.

## Risks to settle in the amendment

- **Catalog names:** one label per catalog author inherits the catalog's merges (the Amendment 56
  screen found three John Brands and two Samuel Butlers under one name each). Small, but it caps
  accuracy for those labels.
- **Leakage:** a calibration book reprinted under another name (an editor, a firm) would sit in
  someone else's profile. Check the 200 books' n-gram overlap with every other profile first.
- **Thin authors:** authors with few blocks get weak labels; report accuracy by profile size.
- **Shortlist misses:** the true author outside the 1,000 is a miss by construction; reported.
