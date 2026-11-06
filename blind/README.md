# blind/

The blind analysis (BOM-32; pre-registration section 8, Amendment 1; plan in `docs/blind-run-plan.md`).

- `seal.py`: relabels the Book of Mormon chunks with opaque ids, mixes in decoys from known
  candidates and controls (at least 1 per 4), writes the key outside the repository, commits
  only hashes and counts
- `run.py`: scores every sealed id with every method and hashes the outputs (the "fresh session"
  step; it never reads the key)
- `unblind.py`: checks every hash, applies the key, scores the decoys, runs leave-one-candidate-out

Issues: BOM-32.
