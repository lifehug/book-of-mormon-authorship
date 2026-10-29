# Classical stylometry outputs (Phase 3)

## `corpus_run.json` (BOM-20)

Built by `python -m classic.corpus_run` (seconds). The classical methods of `classic/` run on
corpus v1.0 to show they work at scale on real authors. A demonstration only: it sets no
threshold and feeds no decision (that is BOM-21), and the Book of Mormon is not touched.

1,890 personal authors have 4+ distinct works of 15,000+ words in 1780-1830 that pass the OCR
cutoff and are duplicate keepers; 30 are drawn with the root seed. Each work contributes one
5,000-word sample from its middle; one work per author is held out and attributed among all 30
from the rest. Chance is 1 in 30 (3%). With 30 tests, each accuracy is uncertain by about +/-15
points.

Holds: the authors drawn, each one's held-out work, and per method its accuracy (Delta on 100,
300 and 1,000 most frequent words, Burrows and Cosine; Cosine Delta on character 3- and
4-grams), General Imposters scores for the true author and for one wrong author per test, and
ENSC accuracy and "none of the above" count at every shrinkage value in the registered grid.

Main finding: ENSC's open-set rule at its default alpha said "none of these" for 11 of 30 works
whose author was in the set, so its alpha must be calibrated on the benchmark (BOM-21), as the
library's own notes say. Shrinkage above 1 lowers accuracy here.
