# data/known_answer/: known-answer controls (BOM-61)

Plan: `docs/known-answer-plan.md`. Work ids, editions and provenance only; no text.

| File | What | Rebuild |
| --- | --- | --- |
| `set.jsonl` | 14 texts (12 primary, 2 secondary): group, edition, every volume's catalog id, why it is in, scholarly consensus | `uv run python -m eval.known_answer build` (seconds; reads `data/catalog/catalog.parquet`) |

The choices themselves are in `eval/known_answer.py` (`SET`). The texts are corpus volumes:
Internet Archive and HathiTrust items at `https://archive.org/details/<id>` and
`https://babel.hathitrust.org/cgi/pt?id=<id>` (HathiTrust refuses scripted requests; the links open in a browser); Whiston's Josephus is from Harvard's Institutional
Books (text never published; obtain under Harvard's terms, `docs/replication.md`).

| Text | Public copy |
| --- | --- |
| Testaments of the Twelve Patriarchs, 1791 | https://archive.org/details/bim_eighteenth-century_the-testament-of-the-twe_1791 |
| Book of Enoch, Laurence, 1821 | https://babel.hathitrust.org/cgi/pt?id=yale.39002005226072 |
| Apocryphal New Testament, Hone, 1820 | https://archive.org/details/apocryphalnewtes0000vari_l6a3 |
| Koran, Sale, 1800 | https://archive.org/details/korancommonlycal1800sale |
| Herodotus, Beloe, 1791 | https://archive.org/details/bim_eighteenth-century_histories-english-the_herodotus_1791_1 (and `_2`) |
| Homer, Pope, 1783 | https://archive.org/details/bim_eighteenth-century_the-iliad-and-odyssey-of_homer_1783_1 (and `_2` to `_4`) |
| Hesiod, Elton, 1815 | https://archive.org/details/remainsofhesioda00hesiuoft |
| Sacontala, Jones, 1792 | https://archive.org/details/sacontalaorfatal00kali_0 |
| Ossian, Macpherson, 1800 | https://archive.org/details/fingalotherpoems00macp |
| Rowley poems, Chatterton, 1794 | https://archive.org/details/poemssupposedtoh01chat |
| Book of Jasher, Ilive, 1829 reprint | https://archive.org/details/bookofjasherwith00iliv |
| Ireland's Shakespeare papers, 1796 | https://archive.org/details/bim_eighteenth-century_miscellaneous-papers-and_ireland-w-h-william-_1796 |
| Castle of Otranto, Walpole, 1782 | https://archive.org/details/bim_eighteenth-century_the-castle-of-otranto-a_walpole-horace_1782 |
