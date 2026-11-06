# Amendment 30: the candidate and control authorial models (BOM-28)

*Filed 2026-11-06. Evidence: `docs/alm-plan.md` ("Candidate models"), `alm/candidates.py`.*

---

**Amendment 30, filed 2026-11-06, before any candidate or control model is fine-tuned and before
any Book of Mormon text is scored.** Section 5.2 registers one fine-tuned copy of the base model
per candidate and per control group; Amendment 22 fixed the fine-tuning and scoring on the
benchmark. This fixes what remains open for the candidates and controls. Decision rules (6.1, 6.2)
are unchanged.

**Units.** A candidate model is trained per candidate, sample type and period, in Amendment 5's
admitted provenance tiers (handwritten, dictated, printed by the author, posthumous), King James
spans masked as in 4.4; Joseph Smith's dictated and handwritten samples are separate (section 3).
Pre-1830 units are confirmatory; post-1830 units are Amendment 5's secondary analysis, subject to
its time-split gate and its one-way reading for exposed candidates. Units under 10,000 masked words
carry the unreliable-sample flag (section 3).

**Control models.** One per registered control group (pseudo-biblical, curated list; 1820s sermons
and tracts; histories with Native American origin texts; general prose), each trained on a seeded
sample of 300,000 masked words: volumes in a seeded order, the middle of each, at least 5,000 words
from every volume used.

**Held-out text.** Amendment 22's rule: a unit of at least 10 blocks of 1,000 words holds out its
last max(5, ceil(n/4)) blocks, tested on the distinct 5,000-word windows there (up to 20); shorter
units train on everything and are untested. Held-out tails are never trained on and are the
source of section 8's decoy segments for candidates and controls.

**Training and scoring.** Amendment 22's fine-tuning settings, from the working model chosen by the
benchmark of the time-locked models (Amendment 26); weights are kept for the blind run. Validation:
closed-set accuracy among all units and among candidates on the held-out windows, and 6.1's
authorial-model score, the best control model's score minus the candidate model's, on every
held-out window. Its thresholds are calibrated before the blind run, not here.
