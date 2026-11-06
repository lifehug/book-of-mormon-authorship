# Robustness to deliberate imitation (BOM-31)

Written 2026-11-06, before any imitation test is scored as a result (one smoke-test number was
seen; see "Disclosure" below). To be registered as Amendment 31. Code: `eval/imitation.py`;
settings `imitation.*` in `config/preregistered.yaml`.

## What is registered already

- **Section 9.** For known 1800s authors who wrote both imitation-biblical and ordinary prose,
  each method's accuracy at identifying the author *from the imitation sample* sets its weight:
  full at or above 80%, half from 60% to 80%, dropped below 60%.
- **Amendment 7, Change 7 (BOM-46).** Only three authors qualify (Snowden, Dodsley, Kenrick:
  a curated imitation work plus 10,000+ words of other writing, `data/benchmark/dual_register.json`),
  so each accuracy is reported with an exact (Clopper-Pearson) 95% interval and its n, and the
  synthesis (6.7) is also run at equal method weights, both published side by side.

## What exists (counts from the catalog; no text)

| Author | Imitation work(s) | Words | Ordinary writing used as reference | Words |
| --- | --- | ---: | --- | ---: |
| Richard Snowden | *The American Revolution*, vols 1-2 (1793, 1794) | 59,964 | *History of North and South America* | 142,929 |
| Robert Dodsley | *The Chronicle of the Kings of England* (1790 printing); *The Oeconomy of Human Life* (1780 printing) | 30,668 | his own plays, poems and fables (6 works) | 156,226 |
| William Kenrick | *The Whole Duty of Woman* (1788 printing) | 10,543 | *Falstaff's Wedding* (itself an imitation, of Shakespeare) | 23,916 |

Gilbert Hunt, Michael Linning, Nimrod Hughes, the two "Zerubbabel" chronicles and Jacob Ilive's
*Book of Jasher* have imitation text but no ordinary prose of adequate length in the corpus; they
serve only as reverse-direction candidates.

**Dodsley's reference, cleaned before scoring.** BOM-46's count credited Dodsley with 711,760 words,
but much of it is not his ordinary prose, and one item is his imitation work itself:

- *conomy of human life* is a copy of the curated *Oeconomy of Human Life*; the catalog title lost
  its "Œ", so `work_key` missed the match;
- *A Collection of Poems* (three keys), *A Select Collection of Old Plays* and *The Preceptor* are
  anthologies he edited;
- *Cleone a tragedy* and *Select fables of Aesop* are second copies of works kept under another
  key.

All of these are left out by title key (`imitation.exclude_reference_titles`). What remains is
his own writing (*Cleone*, *The King and the Miller of Mansfield*, *The Toy-Shop*, *Poetical
Works*, *Select Fables of Esop*): verse and drama as much as prose, which is reported as a limit.

## The test

**Forward: decides the weights.** Candidates are each dual-register author's ordinary writing,
plus 10 distractor authors: 5 drawn (seed `bom31-distractors`) from each of the history and
general-prose control lists. A distractor must:

- have a personal name, not a corporate one;
- not be a curated imitation author;
- have one non-newspaper volume of 10,000+ words, which is its reference.

The tests are every non-overlapping 5,000-word window of each imitation work, each tested once:
Snowden 11, Dodsley 5, Kenrick 2, so 18 in all. The question is whether the method still picks the
real author.

**Reverse: reported, not used for weights.** Candidates are the imitation texts: the three
dual-register authors' and every other curated imitation author with 10,000+ words, 9 candidates in
all. The tests are each dual-register author's ordinary writing in 5,000-word windows, at most 10 per author (seeded): Dodsley 10, Snowden 10, Kenrick 4, so 24 in all.

**Methods, all with their registered settings:**

- Burrows' Delta, Cosine Delta, General Imposters (pool: general prose, never a candidate's
  works) and ENSC, at the benchmark's own calibration (shrinkage 0.5, alpha 0.5; not refitted
  here);
- the style embeddings (BOM-30, cosine to each candidate's profile);
- the authorial language models (BOM-28) at the working size picked after the 1B benchmark:
  the primary, V1, and V3. V2, the classifier head, needs a per-task training loop not built
  here; it is added only if V2 is the working variant.

Dating is not here; its King James imitation shift is measured in BOM-29.

**Outputs, names and numbers only:**

- `data/benchmark/imitation.json`: per method, the forward accuracy with its 95% interval and n,
  per-author accuracy, how many authors are majority-right (with interval), section 9's weight,
  and the reverse accuracy;
- `data/benchmark/imitation_tasks.json`: the ids.

**Down-weighting.** Section 9's bands are applied to the forward accuracy pooled over the 18
tests. Amendment 7's equal-weight synthesis is run beside it, and if the two disagree on a
headline, the paper says so.

## Disclosure

While the code was being checked (2026-11-06), a smoke test printed one number before this plan
was registered: Cosine Delta without General Imposters, 0.72 forward and 0.29 reverse. No design
choice was changed after it. The distractor rule, the Dodsley clean-up and the bands were already
written. Amendment 31 states this.

## Cost

| Part | Where | Time |
| --- | --- | --- |
| `build` | CPU | about a minute |
| `classic`, General Imposters included | Mac CPU | about 10-20 minutes |
| `style` | Mac GPU | about 10 minutes |
| `alm` | rented GPU, at the working size | 21 fine-tunes, one per candidate in each direction; at 1B about 3-5 h on one H100, ~$15-20 |

## Limits

- Three authors.
- Dodsley's reference is mostly verse and drama.
- Kenrick's ordinary work is itself an imitation.
- Two distractors are English translations (Kotzebue, Chaptal), so their style is partly the
  translator's.
- Reference texts outside the masked control lists are unmasked, as in the benchmark.
