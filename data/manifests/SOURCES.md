# Checksum manifests

Every dataset in the project, public or not, is described here by file: path, size and SHA-256.
Built by `python -m metadata.manifest build <dir> -o data/manifests/<name>.jsonl` and checked by
`python -m metadata.manifest verify <dir> data/manifests/<name>.jsonl`. A manifest carries no
text, so the ones covering restricted corpora (Harvard Institutional Books, HathiTrust, the
Joseph Smith Papers transcripts) are public; how to obtain those sources is in
`docs/replication.md`.

The name of each manifest says what it covers: a source pull (`internet_archive.jsonl`,
`hathitrust.jsonl`, `tcp.jsonl`, ...), a derived corpus held on the data machine
(`corpus_cleaned.jsonl`, BOM-14; `corpus_normalized.jsonl`, BOM-15; `morphadorner_adorned.jsonl`),
or a tracked data directory (`catalog.jsonl`, `ocr_quality.jsonl`, `kjv_mask.jsonl`,
`bom_segments.jsonl`, `controls.jsonl`, ...).

## The frozen corpus

`corpus_v1.0.json` (BOM-19) pins corpus v1.0: every manifest here plus every derived table the
analysis stages read -- catalog, genre labels, duplicate flags, OCR estimates, spelling map, KJV
masks, Book of Mormon segments and split, candidate units, control lists and the config -- each
with SHA-256 and size, the config hash, and the git commit it was made at. Built by
`python -m metadata.freeze v1.0`, which refuses to run with any listed file uncommitted;
`python -m metadata.freeze v1.0 --check` verifies a copy against it. Later stages cite the
version. Frozen 2026-10-28 at commit 31be2a2: 70 files, 0.47 GB; index SHA-256
`15858aff9c0b89d8b0fce74583ace87616b0ddf42db1e127ce7589be9bcf96d0`.
