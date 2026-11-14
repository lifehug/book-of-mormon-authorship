# sweep/

The corpus-wide author sweep and its calibration (BOM-39, BOM-47; Amendment 28, `docs/sweep-plan.md`).

- `units.py`: swept authors, their 1,000-word profile blocks, the 200 calibration books
- `index.py`: masked tokens, MFW frequencies and style vectors per unit
- `calibrate.py`: the calibration, usable verdict, lead thresholds and expected false leads
- `older.py`: Burrows' Delta, ENSC and General Imposters as library sweeps (Amendment 57, step 0)
- `coverage.py`: shortlist coverage at K on the 200 known books, by identity class and genre (BOM-89, BOM-91)

Issues: BOM-39, BOM-47, BOM-89, BOM-91.
