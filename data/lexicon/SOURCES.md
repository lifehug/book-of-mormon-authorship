# Lexicon

| File | What | Rebuild |
| --- | --- | --- |
| `english_words.txt` | 234,454 lowercase alphabetic English words, one per line | see below |

Committed rather than read from the host so an OCR score does not depend on which machine ran
it. Derived from the Unix word list shipped at `/usr/share/dict/words` (macOS 15, itself derived
from the public-domain Webster's Second International word list):

```
LC_ALL=C tr 'A-Z' 'a-z' < /usr/share/dict/words | grep -E '^[a-z]+$' | sort -u \
    > data/lexicon/english_words.txt
```

**What it is not.** A modern general word list, not a period one. It misses 1820s proper nouns,
place names, and period spellings, so `lexicon_rate` understates quality in absolute terms for
every source. That is tolerable because the metric is only ever read comparatively: the same
lexicon scores the Chronicling America reference and the title being judged, so the bias
cancels. Any absolute claim about OCR accuracy needs the hand-corrected sample BOM-14 still owes.

## period_words.tsv (BOM-14)

Built by `python -m ocr_fix.lexicon build` from the catalog and the TCP text on the data
machine: every lowercase word in Webster (`english_words.txt`) plus every word occurring in at
least 2 hand-keyed TCP ECCO or Evans texts dated 1700 or later (6,817 texts), each with the
number of those texts it occurs in. 419,156 words. `ſ` is read as `s`. Used by OCR repair
(`ocr_fix.clean`), which compares frequencies rather than trusting membership: keyed text has
slips too (`firft` in 2 texts against 6,446 for `first`). Thresholds are in `pending_amendment`.
