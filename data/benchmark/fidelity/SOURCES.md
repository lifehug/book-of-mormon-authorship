# Sources for the fidelity check (BOM-57)

Is our code for the two methods that failed BOM-21 (General Imposters, `classic/imposters.py`;
ENSC, `classic/ensc.py`) faithful to the published methods? Each source below is listed with the
link it was obtained from. Paper texts are copyrighted and kept in the private data repo
(`data/private/fidelity/`), not here; the links let anyone fetch their own copy.

| Source | What it gives | Link | Obtained |
| --- | --- | --- | --- |
| Kestemont, Stover, Koppel, Karsdorp and Daelemans (2016), "Authenticating the writings of Julius Caesar", *Expert Systems with Applications* 63: 86-96. Authors' accepted manuscript. | General Imposters as our code implements it ("O2"); Table 1: test results on the six PAN 2014 verification corpora by distance and weighting | https://www.pure.ed.ac.uk/ws/files/38106536/Stover_et_al_2016_ESA_Authenticating_the_writings_of_Julius_Caesar_AM.pdf | downloaded 2026-10-30, `data/private/fidelity/kestemont2016_am.pdf` |
| Seidman (2013), "Authorship Verification Using the Impostors Method", PAN at CLEF 2013 notebook | the PAN 2013 winning impostors variant (symmetric similarity, web impostors); accuracy by language | https://ceur-ws.org/Vol-1179/CLEF2013wn-PAN-Seidman2013.pdf | downloaded 2026-10-30, `data/private/fidelity/seidman2013.pdf` |
| Funai (2010), *Extensions of Nearest Shrunken Centroid Method for Classification*, MS thesis, Brigham Young University | NSC variants, including the open-set extension, compared on the Federalist Papers and Book of Mormon blocks | record: https://scholarsarchive.byu.edu/etd/2402 ; PDF: https://scholarsarchive.byu.edu/cgi/viewcontent.cgi?article=3401&context=etd | **not yet**: ScholarsArchive refuses scripted downloads; to be fetched by hand in a browser |
| Schaalje, Fields, Roper and Snow (2011), "Extended nearest shrunken centroid classification: a new method for open-set authorship attribution of texts of varying sizes", *Literary and Linguistic Computing* 26(1): 71-88 | ENSC's published definition and validation | DOI (paywalled, Oxford Academic): https://doi.org/10.1093/llc/fqq029 (found via Crossref, https://api.crossref.org) | **not obtained**; only if Funai (2010) does not define the open-set rule |
| Fields, Schaalje and Roper (2011), "Examining a misapplication of nearest shrunken centroid classification to investigate Book of Mormon authorship", *Mormon Studies Review* 23(1): 87-111 | the authors' plain description of ENSC (pp. 105-108) and its Book of Mormon results (figs. 9-10) | https://scholarsarchive.byu.edu/msr/vol23/iss1/8 (PDF via the page's Download button) | downloaded by the owner in a browser 2026-10-30, `data/private/fidelity/fields2011_msr.pdf` |
| Schaalje and Fields (2012), "Open-set nearest shrunken centroid classification", *Communications in Statistics - Theory and Methods* | the statistical definition of the open-set ("none of the above") rule | DOI (paywalled, Taylor & Francis): https://doi.org/10.1080/03610926.2010.529529 (found via Crossref; authors G. Bruce Schaalje and Paul J. Fields) | **not obtained** |
| PAN 2014 author verification corpora (training and test) | the data Kestemont et al. report on | to be recorded when downloaded | |

## What the sources say so far

**ENSC's open-set rule (Fields, Schaalje and Roper 2011, p. 105).** "The open-set modification
allows for the existence of an unknown candidate author with a distribution of characteristic
features nominally consistent with the test text and incorporates this possibility into the
calculation of the probabilities", and "also accounts for differences in text sizes and for the
effect of multiple simultaneous comparisons". Our `classic/ensc.py` instead says "none" when every
candidate's likelihood is below alpha. **That is a structural difference, not a setting**, and the
formulas are needed (Funai 2010, or the 2011 paper) to rebuild it faithfully.

**Their Book of Mormon results (figs. 9-10)**, 110 words and Jockers et al.'s chapters, early Rigdon
texts only, Joseph Smith added: ENSC gives 73% of chapters to "someone else" with the control
authors in (Spalding 1%, Rigdon 7%, Cowdery 1%, Pratt 0%, Isaiah-Malachi 15%, Joseph Smith 3%), and
93% with the controls removed (Rigdon 0%, Cowdery 4%, Joseph Smith 3%). Our reconstruction (BOM-22)
gave 98% "none". Their closed-set NSC with controls in: Spalding 22%, Rigdon 39%, Cowdery 8%,
Pratt 4%, Isaiah-Malachi 26%, Longfellow 1%.
