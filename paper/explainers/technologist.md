# We trained language models on 50 years of 1800s books to ask who wrote the Book of Mormon. Here's how it works.

*Draft 1, 2026-11-10. For curious, technical readers. Everything here is open: code, config,
results and models at https://github.com/lifehug/book-of-mormon-authorship. The project takes no
position on whether the book is inspired; it asks a narrower, testable question: whose writing does
it resemble, what did it borrow, and when does its language come from?*

## The problem, as an engineering problem

The Book of Mormon was published in 1830. People have argued for two centuries about where it came
from. The critical theories name specific writers (Solomon Spalding, Sidney Rigdon, Oliver Cowdery,
Ethan Smith, Joseph Smith himself) or specific books (*View of the Hebrews*, *The Late War*). Earlier
computer studies came out on every side, and each one was attacked for its setup rather than its
math.

So we treated it like a system we wanted to be hard to fool, ourselves included:

- **Write the rules down first.** Every threshold, model size, random seed and decision rule went
  into one config file, published on OSF before the text was scored. When we changed something,
  we filed a dated amendment saying why, and labelled the ones made after seeing results. There are
  42.
- **Never let the model see the answer.** The Book of Mormon was kept out of all training data.
  We even scrubbed any book that quoted 20 or more of its distinctive 12-word strings.
- **Test on known answers before the real one.** Every method had to prove itself on cases where we
  know the author, including tricky ones like people deliberately imitating scripture.
- **Allow "none of these."** A classifier forced to pick from a list always picks someone. Ours
  could say nobody, and we measured how often it wrongly said somebody.

## The data

About 695,000 catalogued books, mainly from Harvard's Institutional Books dataset, HathiTrust and
the Internet Archive, plus early modern English (1473-1700) from the Text Creation Partnership for
dating. Lots of unglamorous work: fixing wrong catalog dates, removing duplicate editions with
MinHash, measuring OCR quality.

One trick matters a lot: about 7% of the Book of Mormon is King James Bible wording. Any style
detector would find "Bible-ish" and stop there. So we aligned the text to the KJV and **masked**
every matching span before measuring style or date.

## The models

**Time-locked language models.** We trained GPT-style models from scratch on **only** books
printed 1780-1830: 25.7 billion tokens, nothing modern, nothing after 1830. Three sizes (125M,
297M, 590M parameters) on rented H100s. A 1B model diverged mid-training (a classic loss spike),
so we added QK-norm, verified it with a stress test, and trained the 590M instead. These models
"think" in 1820s English, which makes them good judges of what was ordinary for the period.

**Authorship via fine-tuning.** For each candidate author, we fine-tune a copy of the model on
that person's writing. Then for any passage we ask: does this copy find the passage *less
surprising* than the base model does, and more so than copies tuned on control groups (sermons,
histories, biblical imitations)? Lower surprise means closer style.

**Classical stylometry.** The workhorses of the field since the 1960s: count the most common words
(the, of, and, which...), which people use unconsciously, and compare frequency profiles. We use
Burrows' and Cosine Delta for ranking and General Imposters (repeatedly testing the candidate
against random "imposter" authors) to decide whether a match is real.

**Style embeddings.** We also trained the model to map passages to vectors, so passages by the same
author land close together (contrastive learning, like face recognition but for prose).

**A whole-library sweep.** Instead of only testing named suspects, we indexed 23,872 authors of the
period and asked whether any of them comes close.

**Borrowing detectors.** Exact copying, rare shared four-word phrases (against a baseline of
204,520 books), semantic paraphrase search across 163 million passages, and plot-order matching.
Every hit was then sorted into "biblical", "common stock phrase" or "specific".

**Dating.** Classifiers that guess when a piece of English was written, from grammar (61 early
modern features such as "-eth" endings and "did go"), vocabulary, and the language model's
internal representations.

## The exam before the exam

Before touching the Book of Mormon, every method sat an exam: 110 to 180 held-out tests where we
knew the author. Two scores matter: does it **pick the right author**, and how often does it
**say "match" for someone who didn't write it** (false matches)?

| Method | Picks the right author | False matches |
| --- | --- | --- |
| Our 590M model | 98% | 22% |
| Our 297M model | 99% | 38% |
| GPT-2 (same size, modern data) | 90-95% | 86-92% |
| Classical (General Imposters) | 83% | 62% |

Training on period text halves the false matches compared with GPT-2, and bigger helps. But
**nothing hit our pre-set bar of 5% false matches**, so every result is evidence, not proof.

We also checked our own variants and found two of them unreliable: one used a learning rate that
damaged the bigger model, and another gave false-match rates anywhere from 9% to 98% depending only
on the random seed. We wrote that down **before** looking at the Book of Mormon answer, so we
couldn't cherry-pick the variant that said something exciting.

## The blind run

The Book of Mormon was cut into 168 chunks of 5,000 words and shuffled together with 43 decoys:
passages by the candidates themselves, and passages by nobody on the list. Every method scored all
211 without knowing which was which; the outputs were hashed and committed, then the key was
opened. (The blinding is simulated: the scoring ran without access to the key, and the analyst is
an AI model.)

## What came out

- **The decoy check passed.** Methods found the real author in most candidate decoys, and **not one
  method called a control decoy a match.** The machinery works on known text.
- **No confident match to any candidate.** Classical methods made zero match calls; the model-based
  ones made 3 to 10 out of 168 chunks, fewer than their false-match rates would produce by chance.
- **The 23,872-author sweep found no lead.**
- **The combined (Bayesian) verdict leans "none of these candidates": 74%**, starting from 50/50.
  Only the classical methods count in it, because the model-based ones were fooled by imitation in
  testing and get zero weight.
- **Closest-ranked names**, where a method has to rank someone: Joseph Smith, through a sample
  too small to trust (2,700 words). It's also the only sample in the book's own register
  (revelations dictated in scriptural voice, in the same months), and he dictated the book, so
  "closest" here can't separate style from register or composer from dictator.
- **A data bug, caught and fixed.** At first Oliver Cowdery also ranked high. His early sample turned
  out to be 40% word-for-word Book of Mormon text (he copied passages into an 1829 church
  document), so the models were recognising the book itself. We wrote a rule (drop passages of 20+
  words copied after the matching Book of Mormon passage existed; keep everything else), applied it
  to every author, retrained and reran. Cowdery's ranking vanished, match calls fell to 0-2 of
  168, and the combined verdict stayed at 74% "none of these". Both runs are published side by
  side.
- **No borrowed passages.** Proposed sources such as *View of the Hebrews* and the Spalding
  manuscript score like ordinary books. *The Late War* and *The First Book of Napoleon* share rare
  phrases, but so does the whole genre of 1800s Bible imitations; none of the 1,069 flagged
  similarities was judged specific.
- **The language dates early.** The grammar model puts most of the text before 1700 (median 1661),
  and it reads as more archaic than other Bible imitations written in its own time (p 0.0001).

## What this can't tell you

It can't tell you how the text was produced, whether it was translated, or whether it is inspired.
Our checks show these tests can't tell real ancient translations from texts presented as ancient.
It can tell you which surviving writers it resembles: on this evidence, none of the proposed ones
confidently.

## Try it yourself

Everything is public: the pre-registration and amendments, code, config, every result file, and
every trained model on Hugging Face (`etherfuse/timelocked-1830-*`, `etherfuse/bom-authorship-*`).
Three licensed sources can't be redistributed; `docs/replication.md` says exactly how to get them.
Mistakes are possible. The point is that every one of them can be found and fixed.
