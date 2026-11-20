# Where the name lists for BOM-108 would come from

2026-11-19. Three AI research agents looked for name lists the names test (BOM-108) could compare
the Book of Mormon's coined names against. Nothing here was checked by a person, and the main
session did not re-open the addresses. Status words: **opened** = the agent fetched the data and
saw names; **resolves** = the page or file answers, contents not read; **unverified** = not
reached. Nothing has been fetched into the repository. Already held: Bible names, Neo-Assyrian
names (ORACC PNAO), the Book of Mormon Onomasticon, Morse's 1797 gazetteer
(`docs/research/2026-11-18-sources-for-new-tests.md`).

## Hebrew and neighbouring names from inscriptions

| Source | Address | Form and size | Terms | Status |
| --- | --- | --- | --- | --- |
| DAHPN (Munich; Rechenmacher, Golinets, Frank). Cite https://doi.org/10.24344/bht-dahpn | `https://www.dahpn.gwi.uni-muenchen.de/wp-content/themes/bootscore-5-child/api/index.php/getData?db=261&column=2` (`column=0` both, `1` biblical, `2` epigraphic); the site's own search backend, not a documented API; the site also has an Export button | JSON; 2,287 name entries, 874 from inscriptions down to the 6th century BCE; transliteration, root, syntax type, century and reference for each attestation | CC BY-SA 4.0 | opened |
| Golub, onomasticon.net | `https://www.onomasticon.net/assets/data/data-2025-04.json` | JSON; 1,081 records, 524 distinct names, 542 artifacts; Hebrew script, find site, kingdom (Judah 816, Israel 126, Ammon 69, Philistia 48, Edom 12, Moab 4, Phoenicia 4), theophoric element; no dates | CC BY-NC-SA | opened |
| ORACC CTIJ (Judeans in cuneiform records, 744-330 BCE) | `https://oracc.museum.upenn.edu/ctij/cbd/qpn/onebigfile.html` | HTML glossary; 1,549 personal-name entries, mixed with Babylonian names, no language tag | CC BY-SA 3.0 | opened |
| Prosobab (Babylonia 620-330 BCE) | `https://zenodo.org/api/records/17244668/files/ProsobabData.zip/content` | TSV and XLSX; 21,693 people, of whom 173 West Semitic, 43 Aramaic, 4 Hebrew by name language | CC BY-NC 4.0 | opened |
| Inscriptions of Israel/Palestine (Brown; Persian period to about 650 CE) | `https://github.com/Brown-University-Library/iip-texts` | EpiDoc XML, 5,536 files; names not tagged in the file sampled | CC BY-NC 4.0 | resolves |
| Marcato, names in the Aramaic inscriptions of Hatra | Zenodo record 21391494 | PDF, 376 names | CC BY 4.0 | resolves |
| OCIANA (Ancient North Arabian) | `https://ora.ox.ac.uk/objects/uuid:08a60ae8-e61d-486e-9ef1-836ca71d904c/files/mc562d7869379fa3570db57cd9ed0c28c` | XML, 42.9 MB, 37,955 inscriptions; names to be parsed out | Oxford University Research Archive terms | resolves |

**Gap.** Jewish names from Elephantine and the Second Temple period. Tal Ilan's *Lexicon of Jewish
Names in Late Antiquity* is a copyrighted book with no dataset. The Berlin Elephantine persons
page returned an error. Trismegistos covers Elephantine (see below). Printed standard works
(Benz, Huffmon, Fowler; Avigad and Sass; Renz and Röllig) are in copyright or not scanned; DAHPN
and Golub draw on several of them. Not checked: KAI, Maraqten, the Al-Yahudu texts as a separate
source. DASI (South Arabian) sits behind a bot challenge.

## Egyptian names

| Source | Address | Form and size | Terms | Status |
| --- | --- | --- | --- | --- |
| Persons and Names of the Middle Kingdom (Mainz), Mentuhotep II to Amenhotep III | `https://zenodo.org/records/15806808` (version 6); SPARQL at `https://pnm.uni-mainz.de/sparql` | MySQL dump 58.9 MB; 7,933 names with period, region, gender, Ranke numbers | CC BY 4.0 | opened |
| AED-TEI (extract of the Thesaurus Linguae Aegyptiae, January 2018) | `https://raw.githubusercontent.com/simondschweitzer/aed-tei/master/files/dictionary.xml` | TEI XML; 2,865 personal names, 415 kings' names; all periods, undated in the lemma list | CC BY-SA 4.0 | opened |
| TLA text sets on Hugging Face | `https://huggingface.co/datasets/thesaurus-linguae-aegyptiae/<name>/resolve/main/train.jsonl` for `tla-demotic-v18-premium`, `tla-late_egyptian-v19-premium`, `tla-Earlier_Egyptian_original-v18-premium` | JSONL sentences with dates; distinct proper-noun lemmas 1,681 Demotic, 334 Late Egyptian, 1,644 Earlier Egyptian; people mixed with gods and places | CC BY-SA 4.0 | opened |
| Hasitzka, *Namen in koptischen dokumentarischen Texten* | `http://web.archive.org/web/20160214175224id_/http://www.onb.ac.at/files/kopt_namen.pdf` | PDF with text, 120 pages; legacy font to remap; no dates | no licence stated | opened |
| AGÉA (IFAO) | `https://www.ifao.egnet.net/bases/agea/` | HTML, 1,772 names; believed Old Kingdom | terms not found | opened |
| Trismegistos People and Names (Leuven); Egypt about 800 BCE to 800 CE | name pages return 403 "Security Check"; open per-person service `https://www.trismegistos.org/dataservices/rdf/per/?id=N&format=json` | about 40,000 names, 240,000 variants (from a search snippet, not opened) | data services "CC BY-SA 4.0"; terms limit use to research; robots.txt `Request-rate: 1/3` | service opened; name tables unverified |
| Ranke, *Die ägyptischen Personennamen* | scans linked from `giza.fas.harvard.edu/pubdocs/309`, `/310`, `/311` | image-only PDF | volume 3 (1977) in copyright | volume 1 opened |

**Gap.** The Late Period (about 700-300 BCE) in bulk. It is in Trismegistos. Routes: ask Leuven
for an export of the name tables (owner sends the email), or the per-person service at their
stated rate (about 17 days for roughly 500,000 ids; the three replies seen carried a Latinised
name, not an Egyptian transliteration). **No crawl of Trismegistos without the owner's word.**
The Demotisches Namenbuch is print only.

## Names an American of the 1820s could have met in print, and other traditions

Most of these are running text or OCR; the names have to be pulled out. gutenberg.org was down,
so Gutenberg items were opened on its mirror aleph.pglaf.org.

| Source | Address | Status |
| --- | --- | --- |
| Walker, *Key to the Classical Pronunciation of Greek, Latin and Scripture Proper Names* (1823): headword lists | `https://archive.org/download/akeytoclassical01walkgoog/akeytoclassical01walkgoog_djvu.txt` | resolves |
| Lemprière, *Classical Dictionary* (1818) | `https://archive.org/download/classicaldiction00lemp/classicaldiction00lemp_djvu.txt` | resolves |
| Apocrypha (KJV) | `https://aleph.pglaf.org/1/2/124/124-0.txt` | opened |
| Josephus (Whiston), *Antiquities* and *Wars* | `https://aleph.pglaf.org/2/8/4/2848/2848-0.txt`; `https://aleph.pglaf.org/2/8/5/2850/2850.txt` | opened |
| Sale's Koran; *Arabian Nights* (Scott) | `https://aleph.pglaf.org/7/4/4/7440/7440.txt`; `https://aleph.pglaf.org/5/6/6/5668/5668.txt` | opened |
| US place names (GNIS), New York and national | `https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/DomesticNames_NY_Text.zip`; `..._National_Text.zip` | resolves |
| Beauchamp, *Aboriginal Place Names of New York* (1907); Trumbull, *Indian Names of Places in Connecticut* (1881) | `https://archive.org/download/aboriginalplacen00beau/aboriginalplacen00beau_djvu.txt`; `https://archive.org/details/indiannamesofpla00trumiala` | resolves |
| 1790 census, *Heads of Families* (12 states) | `https://www2.census.gov/library/publications/decennial/1790/heads-of-families-new-york.pdf` (same pattern per state); OCR on archive.org | resolves |
| Morgan; Bernard, *Light on Masonry* (1829) | `https://aleph.pglaf.org/1/8/1/3/18136/18136.txt`; `https://archive.org/download/lightonmasonrya00berngoog/lightonmasonrya00berngoog_djvu.txt` | opened / resolves |
| One author inventing names, before 1830: Spalding's *Manuscript Story*; Swift's *Gulliver*; Spenser; Macpherson's Ossian | `https://archive.org/download/themanuscriptsto00spauuoft/themanuscriptsto00spauuoft_djvu.txt`; `https://aleph.pglaf.org/8/2/829/829-0.txt`; `https://aleph.pglaf.org/6/9/3/6930/6930.txt`; `https://archive.org/download/poemsofossiantra11macp/poemsofossiantra11macp_djvu.txt` | resolves / opened |
| Sumerian names (ORACC ePSD2) | `https://oracc.museum.upenn.edu/json/epsd2-names.zip`; CC0; 4,848 entries, 1,222 personal | opened |

No bulk download confirmed: Greek personal names (LGPN; server timed out), Maya (Maya Hieroglyphic
Database, Classic Mayan portal), Nahuatl, BDTNS, DASI. The pseudo-biblical books are already held;
their names need extracting, not fetching.

## Earlier counts-based studies of the names

- Wilcox, Brown, Baker-Smemoe, Black and Bray 2013, "Identifying Authors by Phonoprints in Their
  Characters' Names", *Names* 61(2): `https://ans-names.pitt.edu/ans/article/download/1980/1979/3980`
  (resolves). 55 Spalding names, 197 Tolkien names, 100 nineteenth-century census names, men only.
- Wilcox, Brown, Baker-Smemoe, Black and Eggett 2019, *Interpreter* 33:105-122 (opened and read by
  the agent):
  `https://archive.bookofmormoncentral.org/sites/default/files/archive-files/pdf/wilcox/2019-08-12/brad_wilcox_et_al_comparing_phonemic_patterns_2019.pdf`.
  Adds 124 single-word male Book of Mormon names; hand transcription into phonemes, scored with an
  English phonotactic calculator. Reports that the Book of Mormon names pattern with the census
  names, not with Spalding's or Tolkien's. Limits as the agent read them: small samples, men only,
  an English-based scorer, two invented-name authors, one of them twentieth-century.
- Tvedtnes, Gee and Roper 2000: `https://scholarsarchive.byu.edu/jbms/vol9/iss1/11` (resolves);
  attestations in Hebrew inscriptions, no statistics. Hoskisson 1990: no online copy found.
- No independent replication or critical quantitative study was found.

## What to fetch first

1. DAHPN (both calls) and Golub's JSON: the inscription names the test lacked.
2. Persons and Names of the Middle Kingdom, AED-TEI `dictionary.xml`, the three TLA sets, Hasitzka.
3. Walker's Key and Lemprière; Apocrypha, Josephus, Sale, *Arabian Nights*.
4. GNIS with Beauchamp and Trumbull as the key to native names; the 1790 census volumes.
5. The single-author baselines (Spalding, Swift, Spenser, Ossian); ePSD2; ORACC CTIJ and Prosobab.

All of group 1 to 5 is open or public domain except two non-commercial licences (Golub, Prosobab):
usable, recorded in SOURCES.md, text not republished. Trismegistos waits on the owner.
