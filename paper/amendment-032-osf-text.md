# Amendment 32: the blind run's sealed set and decoys (BOM-32)

*Filed 2026-11-06. Evidence: `docs/blind-run-plan.md`, `blind/`.*

---

**Amendment 32, filed 2026-11-06, before anything is sealed or any Book of Mormon text is scored.**
Section 8 (as amended by Amendment 1) is fixed as follows; its rules are unchanged.

**Sealed set.** The narrator segmentation's whole chunks, 121 of 2,000 words and 47 of 5,000 words
(4.5). The dictation-order and scribe segmentations serve only H1c's internal comparison, which has
no candidate to bias toward; they are scored after unblinding with the same frozen code.

**Decoys.** For each chunk size, one decoy per four Book of Mormon chunks, rounded up (31 and 12).
Half, rounded up, come from candidates with public texts (Ethan Smith, Gilbert J. Hunt, Oliver
Cowdery, Sidney Rigdon, Parley P. Pratt, W. W. Phelps, Solomon Spalding), each keeping at least
10,000 masked words out of the decoys as its reference; the rest from authors of the pseudo-biblical,
history and general-prose control sets. A decoy is a run of the chunk's length of KJV-masked text;
author uniform among those able to give one, position seeded (`bom32-seal`), no overlaps. Every
decoy's source span is published and left out of every method's references. Ids are random; the key
is written outside the repository with its SHA-256 and the sealed set's committed.

**Identification.** A candidate decoy is identified when attributed to its candidate; a control
decoy when the method returns no candidate (and, for the sweep, ranks its author first where swept).
Each method's decoy accuracy is compared with its benchmark accuracy as section 8 requires.

**Fresh session.** The scoring step runs in a new AI session given only the repository and the
scoring script; the key is outside the repository at mode 600 and never referenced by that script.
This is simulated blinding and is labelled so (section 10).

**Sweep.** Each sealed id is scored against every swept author; the discovery half's mean
distances and leads (6.6, Amendment 28) are formed only after unblinding.
