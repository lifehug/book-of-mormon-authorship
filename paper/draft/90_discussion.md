# Discussion

**What the evidence supports.** The methods rank real authors correctly on most decoys, and the
candidate models, which can call a match, called none of the control passages one. On the Book of
Mormon, no method makes a confident match to any proposed author. The registered synthesis leans
against the three candidates it can test (Ethan Smith, Hunt, Spalding; "none of these three"
0.744 from a prior of 0.5); it cannot test Joseph Smith or Cowdery, whose pre-1830 samples are too
small, and says nothing for or against them. *The Late War* and *The First Book of Napoleon* pass
the registered rare-phrase rule, as the pseudo-biblical genre does generally; no proposed source
shares a copied passage or a plot sequence, and no surfaced pair of passages was judged specific
(each is explained by King James wording or period stock phrasing).
The text's grammar dates earlier than its period and earlier than the period's other imitations of
biblical style.

**Decisions made after results existed.** The registered analysis stands as the main record; each
of the following was added later, is labelled post hoc, and is reported beside it:

| Amendment | Decided after | What it changed | Effect on the headline |
| --- | --- | --- | --- |
| 19 | dating validation | H3a/H3b decided on segment medians | none on Book of Mormon results (before scoring) |
| 33 | benchmark | both 6.1 readings and a false-match ladder reported | none (both shown) |
| 38-39 | the 1B's loss spike | 590M replaces 1B | one model size |
| 41-42 | the 590M benchmark | V1/V2 learning rate, V2 seeds | V2 given no weight |
| 43 | unblinding | Book of Mormon quotations dropped from candidate samples | Cowdery ranking removed; synthesis unchanged |
| 44 | unblinding | Joseph Smith's ordinary prose scored | register confound stated |
| 45 | the simulated reviews | ranking rechecked at equal training dose | see section on dose |

**What it does not support.** No method passes the registered open-set bar, so "none of these" is
graded evidence, not a verdict; the synthesis rests on the classical family alone, because the
model-based methods were misled by deliberate imitation; and the candidate samples are uneven and,
for the writers closest to the text, small. Where methods must rank someone first they rank Joseph
Smith's 1828-29 revelations, which share the text's register and were dictated by the same person
in the same months; his ordinary prose does not stand out. These methods cannot separate register
from authorship, nor the person who dictated a text from the person who composed it, and none of
the borrowing or dating tests separates a genuine translation from a text presented as ancient
(Amendment 9). The study therefore says nothing about how the text was produced, whether it is a
translation, or whether it is inspired.

**What changed along the way.** Three decisions were made after results existed and are labelled
so: the learning rate of two benchmark variants, which the larger model exposed (Amendments 41-42);
the removal of Book of Mormon quotations from candidate samples, after unblinding revealed that one
candidate's sample was 40% quotation (Amendment 43); and the comparison of Joseph Smith's
revelatory and ordinary prose (Amendment 44). Each is reported beside the registered result, not
in place of it.

**What would sharpen it.** Larger models (the false-match rate fell from 47% to 22% between 125M
and 590M parameters); more and larger candidate samples, especially pre-1830 writing outside the
scriptural register, which does not survive for Joseph Smith; more benchmark tasks, to narrow the
error rates; and the time series of Joseph Smith's and his contemporaries' prose after 1830 (BOM-73,
`docs/js-over-time-research.md`).

**Reproducing it.** The pre-registration and its amendments, the code, the configuration file
every number is stamped with, every result file and every trained model are public
(`etherfuse/timelocked-1830-*` and `etherfuse/bom-authorship-*` on Hugging Face, with SHA-256
lists in `data/manifests/`). Three sources are licensed and cannot be redistributed; the steps to
obtain them are in `docs/replication.md`. Mistakes are possible; every one can be found and redone.
