# Book of Mormon text inside the candidate samples: quotation or shared idiom?

Read-only analysis, 2026-11-10, after unblinding, for the owner's review of the proposed
Amendment 43 (branch `amendment-43-bom-overlap`). Nothing in the registered results is changed by
it. Code: `eval/bom_overlap.py`; numbers: `data/candidates/bom_overlap.json`.

## Why

After unblinding, the 590M candidate models ranked Oliver Cowdery's pre-1830 sample closest to
most Book of Mormon chunks. That sample turned out to be 40% word-for-word Book of Mormon text.
The question then became: which candidate samples contain Book of Mormon text, and is it
**quotation** (which would let a model recognise the book) or **shared idiom** (which is genuine
style evidence)? Joseph Smith, who dictated both the Book of Mormon and the early revelations,
needs particular care: his own phrasing in both is exactly what an authorship test should see.

## The rule (fixed before reading any match)

For every run of 8 or more words a sample shares with the Book of Mormon's narrative books:

1. **Biblical:** the whole run is King James wording (already masked).
2. **Stock:** half or more of it occurs in ordinary period writing (the control texts).
3. Otherwise, by date, against when that Book of Mormon passage was dictated (Mosiah to Moroni
   April-May 1829; 1 Nephi to Words of Mormon June 1829):
   - written **before** the passage existed → **predates the passage** (cannot be a quotation);
   - written in **the same weeks** → **same weeks** (neither before nor clearly after);
   - written **after** → **quotation** if 20 or more words, else **short phrase, ambiguous**.

## Joseph Smith

| Sample | Words | Shared with the Book of Mormon | Of which: quotation | Predates the passage | Same weeks | Stock / biblical | Short, ambiguous |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Revelations, July 1828 - summer 1829** (the pre-1830 sample) | 2,710 | 69 words (2.5%) | **0** | 9 | 51 | 9 | 0 |
| Dictated letters, 1832-33 | 5,266 | 67 (1.3%) | 24 (one passage) | 0 | 0 | 43 | 0 |
| Handwritten, 1831-32 | 6,068 | 29 (0.5%) | 0 | 0 | 0 | 10 | 19 |

**Every shared run in his pre-1830 revelations, in full:**

| Revelation | Dated | Words | Class | Book of Mormon passage (dictated) | Shared wording |
| --- | --- | --- | --- | --- | --- |
| D&C 3 | July 1828 | 9 | predates the passage | Mosiah (Apr-May 1829) | "doth vary from that which he hath said therefore" |
| D&C 10 | spring 1829 | 12 | same weeks | 3 Nephi (Apr-May 1829) | "I will shew unto them that my wisdom is greater than the" |
| D&C 10 | spring 1829 | 11 | same weeks | 3 Nephi | "harden not their hearts I will establish my church among them" |
| D&C 10 | spring 1829 | 10 | same weeks | 3 Nephi | "Behold I am Jesus Christ the Son of God I" |
| D&C 10 | spring 1829 | 9 | stock | 3 Nephi | "the gates of hell shall not prevail against them" |
| D&C 9 | April 1829 | 8 | same weeks | Alma (Apr-May 1829) | "even so I would that ye should continue" |
| D&C 9 | April 1829 | 10 | same weeks | Alma | "me but behold I say unto you that by small" |

(Book of Mormon wording shown; the 1830 edition is in the public domain. One 27-word match of D&C
10 is to the 1830 *preface*, which retells the loss of the 116 pages; the preface is not part of
the narrative text that was scored, so it is excluded.)

**Reading.** None of it is quotation. One phrase predates the Book of Mormon text altogether
(D&C 3, July 1828). The rest are short phrases from revelations dictated in the same weeks as the
matching passages, in the same voice. D&C 10's date is itself debated (summer 1828 or April-May
1829). This is what one person dictating two texts at once looks like, which is exactly the
signal an authorship test is meant to measure. **Masking it would remove genuine style evidence,
and the analysis gives no reason to.**

## The other affected samples

| Sample | Words | Shared | Quotation | Short, ambiguous | Predates / same weeks | Biblical / stock | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Cowdery, "Articles of the Church of Christ", June 1829** | 1,355 | 548 (40.4%) | **295** | 245 | 8 | 0 | **Quotation.** It copies the sacrament prayers and baptism instructions (Moroni, 3 Nephi) |
| Cowdery, *Messenger and Advocate*, 1834-36 | 85,723 | 731 (0.9%) | 111 | 175 | 0 | 445 | Mostly biblical; some quotation |
| Cowdery, scribal copies (letters) | 2,778 | 27 (1.0%) | 0 | 27 | 0 | 0 | Short phrases |
| **Pratt, *A Voice of Warning*, 1837** | 51,820 | 2,472 (4.8%) | **997** | 557 | 0 | 918 | **Quotation**: he quotes the Book of Mormon at length |
| Pratt, *Mormonism Unveiled*, 1838 | 16,659 | 512 (3.1%) | 280 | 207 | 0 | 25 | Quotation |
| Ethan Smith (1809-1824) | 287,603 | 1,519 (0.5%) | 0 | 0 | 124 | 1,395 | Biblical; a few phrases predate it |
| Hunt, *The Late War*, 1816 | 55,546 | 135 (0.2%) | 0 | 0 | 93 | 42 | Predates it |
| Rigdon, 1838 | 5,569 | 28 (0.5%) | 0 | 0 | 0 | 28 | Biblical only |

## What this suggests for the proposed fix

The proposed Amendment 43 masks every shared run in every sample. This analysis suggests a
narrower rule, to be decided by the owner:

- **Mask quotations** (a run of 20+ words written after the passage existed): Cowdery's 1829
  Articles, Pratt's books, the quoted passages in Cowdery's *Messenger and Advocate* and one in a
  Joseph Smith letter of 1833.
- **Keep** runs that predate the passage, runs from the same weeks, stock and biblical phrasing
  (the last is masked already), so Joseph Smith's early revelations stay as they are.
- **Report both**: results with the narrow rule and with the broad one, side by side.

Short ambiguous phrases (under 20 words, after the passage) are the open question: masking them
is safe against leakage but removes some genuine shared idiom. Their volume is small except in
Cowdery's Articles and Pratt.

## The decision (owner, 2026-11-10) — Amendment 43

**The problem.** The registered sealing rule kept the Book of Mormon out of every model's
training and calibration, but it was enforced on the training corpus, not on the candidate
samples. Two candidates' samples quote the book: Oliver Cowdery's "Articles of the Church of
Christ" (June 1829, 40% shared) and Parley P. Pratt's books (1837-38). A model fine-tuned on a
sample that quotes the text will recognise the text, which is leakage, not resemblance; that is
why Cowdery's pre-1830 sample ranked first after unblinding.

**The options considered.**

| Option | What it removes | Problem |
| --- | --- | --- |
| Leave the samples as they are | nothing | The leakage stays; Cowdery's ranking is void |
| Mask every shared run, from everyone (first proposal) | quotations and shared idiom alike | Removes genuine style evidence, above all Joseph Smith's: he dictated both texts, and his revelations of 1828-29 share phrasing with passages dictated in the same weeks or later |
| Drop the affected samples entirely | Cowdery's and Pratt's samples | Throws away their own writing along with the quotations |
| **Mask quotations only (chosen)** | passages of 20+ words written after the matching Book of Mormon passage existed | Short later phrases stay (Cowdery's sample still shares 7.8%, mostly short phrases and text from the same weeks) |

**The rule chosen.** A quotation is a passage of runs shared with the Book of Mormon's narrative
(each run at least 8 words; runs no more than 5 words apart merged, so a copy with small edits
counts as one passage), at least 20 words long, in a text written after the matching Book of
Mormon passage was dictated. Quotations are dropped from the sample, as King James spans are;
nothing else is. Settings: `candidates.bom_quotation` in `config/preregistered.yaml`.

**Why.** It removes exactly what causes leakage (copied passages) and keeps what an authorship
test should see (each writer's own phrasing). It treats every candidate by one rule, decided
before the masked results exist. And it protects the evidence from the person at the centre of
the question: Joseph Smith's pre-1830 revelations contain no quotation by this rule (one phrase
predates the passage it matches, the rest were dictated in the same weeks), so none of his text
is removed. The owner's reasoning: "Joseph Smith revelations should only be excluded if they
were written after the Book of Mormon."

**What it changes.** Masked as quotation: Cowdery's Articles 494 words (36.5%), Pratt's *Voice of
Warning* 1,321 (2.5%) and *Mormonism Unveiled* 375 (2.3%), Cowdery's *Messenger and Advocate* 151
(0.2%), one passage in a Joseph Smith letter of 1833, 24 words (0.5%); Joseph Smith's pre-1830
revelations, 0. After masking, Cowdery's pre-1830 sample is 798 words and shares 7.8%; Pratt's
shares 1.0%; every other sample 0-0.5% (Joseph Smith's revelations 2.2%, unchanged by decision).

**How it is reported.** Post hoc: found after unblinding and decided after seeing which samples
were affected. The candidate models are retrained on the masked samples and the sealed set is
rescored by every method that reads candidate samples; the results are reported beside the
registered run (tag `blind-registered-2026-11-10`), never in place of it.
