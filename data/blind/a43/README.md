# Amendment 43 rerun (post hoc)

The blind run repeated with Book of Mormon quotations dropped from candidate samples
(`docs/bom-overlap-analysis.md`): candidate models retrained at 125M, 297M and 590M, and the sealed
set rescored by every method that reads candidate samples (classical, style 297M and 590M,
candidate models). Reported beside the registered run, never in place of it: the registered files
stay in `data/blind/`, `data/benchmark/` and `data/synthesis/` (also git tag
`blind-registered-2026-11-10`).

- `unblinded.json`, `outputs.json` (hashes as scored; the files themselves are in `outputs/`
  here), `thresholds.json`: this rerun's.
- `../../benchmark/a43/`: the retrained candidate models' validation and the masked plan.
- `../../synthesis/a43/`: the synthesis on this rerun.
