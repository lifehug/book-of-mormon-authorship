# data/claims/

`register.yaml` — public claims about Book of Mormon authorship, from every side, written down
before this study has results. Issue: BOM-42.

Not source text and not derived data: a list of other people's assertions, each with the
decision rule that will settle it, fixed in advance. After BOM-35 each gets a verdict.

The register is frozen before the blind run (BOM-32) by setting `frozen: true` and committing
its SHA-256, the same way the analysis thresholds are. Nothing about it feeds the analysis; it
only governs what gets reported afterwards.

Rebuild: hand-maintained. Adding a claim after freezing is allowed and must be recorded as a
dated addition with its own decision rule, written before the verdict is filled in.
