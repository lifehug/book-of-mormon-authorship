# data/blind

BOM-32's sealing record (Amendment 32). `seal.json`: hashes of the key and of the sealed set, and
counts (211 ids: 168 Book of Mormon chunks, 43 decoys); no id mapping. `withheld.json`: the decoys'
source spans, which every method leaves out of its references. Made by `python -m blind.seal`; the
key itself is outside the repository (`~/.bom-blind/key.json`, mode 600) until unblinding, and the
sealed text is in `data/corpus/blind/` (not in git).
