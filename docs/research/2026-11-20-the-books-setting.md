# Tests of the book's setting: prior work, designs and sources

2026-11-20. The owner asked what could be measured about the Book of Mormon's setting: its peoples
are said to have lived in the ancient Americas, so do its names, things, places, numbers and wars
look like the ancient Americas, like the Bible and the ancient Near East, or like the United States
of the 1820s and what Americans then believed about Indians and "mound builders"? AI research
agents surveyed earlier work and located sources. Nothing here was checked by a person. Status
words: **opened** = the agent read it; **resolves** = the page or file answers, contents not read;
**unverified** = not reached. Issues: BOM-109 to BOM-117.

## Prior work (both sides)

| Work | Where | What it holds | Limits (critics', or the agent's where marked) | Status |
| --- | --- | --- | --- | --- |
| Dale and Dale 2019, "Joseph Smith: The World's Greatest Guesser", *Interpreter* 32:77-186 | https://cdn.interpreterfoundation.org/jnlpdf/dale-v32-2019-pp77-186-PDF.pdf | 131 positive correspondences with Coe's *The Maya* (weights 0.5, 0.1, 0.02), 18 negative (weight 50 each); result 1.03 x 10^-111. Controls: Spalding 19 positive and 21 negative; *View of the Hebrews* 15 and 9 | items multiplied as if independent; weights set by the authors; a ten-detail invented story scores about 1 in 625 billion (Wheat and Tares 2019); controls coded by the same authors, not blind (agent) | opened |
| Critique of the above | https://wheatandtares.org/2019/06/13/bad-book-of-mormon-apologetics/ | | a blog; no journal-published statistical critique was found | opened |
| Roper 2025, *Anachronisms: Accidental Evidence*, *Interpreter* 65 | https://cdn.interpreterfoundation.org/jnlpdf/roper-v65-2025-1-8-PDF.pdf | 226 claimed anachronisms; confirmed / partial / unconfirmed 7/2/93 of 102 by 1844, 36/10/122 of 168 by 1965, 174/31/21 of 226 by 2024 | one coder; "confirmed" means attested anywhere in the ancient record; no control text (agent) | opened (introduction and chapter 9) |
| Coe 1973, "Mormons and Archaeology", *Dialogue* 8(2) | https://www.dialoguejournal.com/articles/mormons-and-archaeology-an-outside-view/ | horse, chariot, wheat, barley, cattle, metallurgy | a short list | opened |
| Wikipedia, "Anachronisms in the Book of Mormon" | https://en.wikipedia.org/wiki/Anachronisms_in_the_Book_of_Mormon | 24 items in six groups | unsystematic | opened |
| Holley's place-name map, and a summary of the argument | https://wheatandtares.org/2017/05/18/want-to-attack-the-vernal-holley-maps-want-to-defend-the-vernal-holley-maps-weve-got-you-covered/ ; https://www.fairlatterdaysaints.org/answers/Book_of_Mormon_place_names_from_North_America | 29 modern names against the book's place names; 17 judged invalid, mostly named after 1829 | no chance baseline from either side | opened |
| Vogel 1986, *Indian Origins and the Book of Mormon* | https://user.xmission.com/~research/central/vogel1.htm (also vogel3.htm, vogel5.htm) | about 27 motifs with pre-1830 sources: picketed earth forts, burial mounds, iron and steel in mounds, a civilised race destroyed by a savage one, Hebrew customs, Egyptian-like writing | no base rates | opened |
| Stubbs 2015 (Uto-Aztecan with Semitic and Egyptian); his replies | https://archive.timesandseasons.org/2022/10/clarifications-on-uto-aztecan/index.html | 1,528 proposed sets | reviewers: many source languages and loose meanings make matches easy; Rogers 2019 (*JBMS* 28) known only through Stubbs's reply | opened |
| Alma 11 weights (after Welch 1999) | https://scripturecentral.org/evidence/book-of-mormon-evidence-near-eastern-weights-and-measures | ratios 1/8, 1/4, 1/2, 1, 1.5, 2, 4, 7; nine parallels across five Near Eastern systems | a look-elsewhere design; no Mesoamerican or 1820s money compared (agent) | opened |
| Wilcox et al. 2013, 2019 (names) | see `2026-11-19-name-lists-for-bom-108.md` | 124 names against census, Spalding, Tolkien | small, men only | held |

**Gaps the agent found:** no chance baseline for the place-name map; no quantitative fit of any
geography model; no count of the book's number words; no peer-reviewed statistical critique of
Dale and Dale.

## The tests (one issue each)

| Issue | Test | The fair comparison |
| --- | --- | --- |
| BOM-109 | Where the three worlds disagree, which does the book side with? | Spalding and *View of the Hebrews* must land on the 1820s side, the Popol Vuh on the Mesoamerican |
| BOM-110 | The place-name map against chance | the same rule on every other region and on control name sets |
| BOM-111 | The inventory of things, and what is absent | Bible, 1820s fiction, native texts, chronicles; the translators' allowance measured |
| BOM-112 | The Dale and Dale checklist made fair | three checklists, about ten texts, blind coding, weights from controls |
| BOM-113 | Roper's tally recoded by place and period | the same tally for Spalding |
| BOM-114 | Numbers, and the weights of Alma 11 | random small-ratio systems as the baseline |
| BOM-115 | Warfare | Bible, Josephus, American wars, conquest accounts |
| BOM-116 | Geography against placebo regions | texts with a known geography; Spalding's invented one |
| BOM-117 | Stubbs's sound rules on unrelated languages | control families; shuffled meanings |

Rules for all: lists and thresholds fixed before scoring; the three settings scored together; with
and without the Bible-quoting chapters; the number of places, languages or systems searched is
counted and reported.

## Already in the library (checked in `data/catalog/catalog.parquet`, 2026-11-20)

Clavigero's *History of Mexico* (1787, 1806, 1807); del Río on Palenque (1822); Juarros on
Guatemala (1823, 1825); Atwater in *Archaeologia Americana* (1820); *View of the Hebrews* (1823);
Boudinot (1816); Yates and Moulton (1824); Haywood (1823); Rafinesque (1824); Spafford's
gazetteers (1813, 1824); Acosta (1604); Garcilaso (1688); Heckewelder (1819). Not found by title:
Adair (1775). Robertson, Humboldt, Solís and Bernal Díaz matched loosely and need a closer look.

## Native American names (for BOM-108 and BOM-110)

No bulk, language-tagged dataset of Maya or Nahuatl names was found. Obtainable:

| Group | Source | Address | Size | Terms | Status |
| --- | --- | --- | --- | --- | --- |
| Maya | Wikipedia "Maya monarchs" | `https://en.wikipedia.org/w/api.php?action=parse&page=Maya_monarchs&prop=wikitext&format=json` | about 220 rulers | CC BY-SA | opened |
| Nahuatl | Visual Lexicon of Aztec Hieroglyphs | `https://aztecglyphs.wired-humanities.org/advsearch-all-grid?field_semantic_categories_new_ta_tid=129` (personal; `=128` places; `&page=N`) | about 3,500-4,000 personal and 1,000 place records, c. 1541-1570s | CC BY-NC-SA 3.0; robots.txt crawl delay 10 s | opened |
| Nahuatl | Wiktionary categories (Classical Nahuatl proper nouns 167, Central Nahuatl 245) | MediaWiki API | about 400 | CC BY-SA | opened |
| Nahuatl | Morelos census names, c. 1540-44 (Hansen, from Cline) | `https://nahuatlstudies.blogspot.com/2014/11/nahuatl-names-nahuatl-names-in-1544.html` | 199 | none stated | opened |
| Nahuatl | Peñafiel, *Nombres geográficos de México* (1885) | archive.org `pen-afiel-nombres-geograficos-de-mexico` | | public domain | resolves |
| Quechua | Guaman Poma (1615) OCR; González Holguín (1608); Wikipedia "Sapa Inca"; Wiktionary Quechua proper nouns (75) | archive.org `guaman-poma-de-ayala-felipe.-nueva-coronica.-tomo-i-ocr-1980`, `vocabulariodelal01gonz` | | public domain / CC BY-SA | opened / resolves |
| Iroquois, Delaware and others | Treaty signers: Oklahoma State tribal treaties database | `https://treaties.okstate.edu/search/site-map.xml` (562 treaties, about 151 before 1830; signers as "Name, his x mark") | thousands | no bar on general crawlers | opened |
| the same, in period print | *Treaties between the United States ... 1778 to 1837* | archive.org `treatiesbetweenu00unit_0` | about 3,300 signature lines | public domain | opened |
| Iroquois | Cusick 1827 | archive.org `Ayer_251_I611_C9_1827` | | free for any lawful purpose | opened |
| North America | Hodge, *Handbook of American Indians* (1907-10) | archive.org `handbookamindians01hodgrich`, `handbookamindians02hodgrich` | thousands of headwords | public domain | opened |
| what a New Yorker could read | Drake 1832 `drakechiefsbio00drakrich`; Adair 1775 `historyofamerica00adairich`; Seaver's Jemison narrative 1826 `narrativeoflifeo00seav`; Priest 1826 `wondersnaturean00priegoog`; Heckewelder's names `nameswhichlennil00heck`; Morgan 1851 `leagueofhodnos00inmorg`; Beauchamp 1893 `indiannamesinnew00beau`; Ruttenber 1906 `footprintsofredm00rutt` | archive.org | | public domain | resolves |

Not found: Roys's *Personal Names of the Maya of Yucatan* (1940); structured Mixtec, Zapotec or
Epi-Olmec names. Limit: Maya inscriptions date mostly from 250 to 900 CE and Nahuatl names from
the 1500s, later than most of the book's stated period (about 600 BCE to 400 CE).

**"Alma".** Behind the Name: the given name "became popular after the Battle of Alma (1854)", was
"in rare use before the battle", "probably inspired by Latin almus 'nourishing'" and "also
coincides with the Spanish word meaning 'the soul'" (https://www.behindthename.com/name/alma-1,
opened). No attestation as a Native American name was found in any list opened (absence in these
lists, not proof). For the United States before 1830 no frequency data was found; one figure, from
Rappleye and Hansen (*Interpreter* 62, 2024), counts 42 Almas born 1780 to 1820 connected with
Wayne County, New York, of whom four were male
(https://interpreterfoundation.org/journal/more-evidence-for-alma-as-a-semitic-name, opened). The
1850 census full count would settle the rate; not opened.
