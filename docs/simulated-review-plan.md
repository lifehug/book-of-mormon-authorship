# Simulated peer review (BOM-38)

Decision 2026-10-15: no journal submission; peer review is simulated by AI models and labelled
so everywhere. Code: `review/simulate.py`. Written 2026-11-06, before the paper is final; run once
BOM-36's draft is complete (all result slots filled) and BOM-37's release exists.

**What a reviewer sees.** Only the paper draft (`paper/draft/*.md`) and the pre-registration with
all amendments, passed in the prompt to a fresh hosted-model call with no tools, no repository
access and no memory of the working sessions. The SHA-256 of exactly what it saw is recorded in
each review's header.

**Three independent reviews**, one call each: a statistician (decision rules, calibration,
multiple comparisons, the open-set rate, the synthesis's assumptions), a historian of early
Mormonism and the book trade (candidates, sources, access, manuscripts, fairness to every side),
and a computational stylometrist (corpus, normalisation, masking, features, the time-locked
models, imitation, replication). Each must answer in a fixed shape (summary, numbered major and
minor points, a recommendation); a reply without it is logged and retried, never saved.

**Outputs.** `paper/review/review_<role>.md`, verbatim, each headed **SIMULATED** with the model and
date; `paper/review/response_plan.md`, every point listed for a dated answer: a revision (commit)
or a recorded disagreement with its reason. Real critiques and replication attempts that arrive in
the repository are logged beside them (BOM-38's last checkbox) and are never labelled simulated.

**Limits.** A model reviewer can miss what a specialist would catch and can be confidently wrong;
its review is a stress test, not validation, and the paper says so.

Run: `python -m review.simulate run --draft paper/draft` (three paced calls, minutes).
