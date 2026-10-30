# Sources for the fidelity check (BOM-57)

Is our code for the two methods that failed BOM-21 (General Imposters, `classic/imposters.py`;
ENSC, `classic/ensc.py`) faithful to the published methods? Each source below is listed with the
link it was obtained from. Paper texts are copyrighted and kept in the private data repo
(`data/private/fidelity/`), not here; the links let anyone fetch their own copy.

| Source | What it gives | Link | Obtained |
| --- | --- | --- | --- |
| Kestemont, Stover, Koppel, Karsdorp and Daelemans (2016), "Authenticating the writings of Julius Caesar", *Expert Systems with Applications* 63: 86-96. Authors' accepted manuscript. | General Imposters as our code implements it ("O2"); Table 1: test results on the six PAN 2014 verification corpora by distance and weighting | https://www.pure.ed.ac.uk/ws/files/38106536/Stover_et_al_2016_ESA_Authenticating_the_writings_of_Julius_Caesar_AM.pdf | downloaded 2026-10-30, `data/private/fidelity/kestemont2016_am.pdf` |
| Seidman (2013), "Authorship Verification Using the Impostors Method", PAN at CLEF 2013 notebook | the PAN 2013 winning impostors variant (symmetric similarity, web impostors); accuracy by language | https://ceur-ws.org/Vol-1179/CLEF2013wn-PAN-Seidman2013.pdf | downloaded 2026-10-30, `data/private/fidelity/seidman2013.pdf` |
| Funai (2010), *Extensions of Nearest Shrunken Centroid Method for Classification*, MS thesis, Brigham Young University (168 pp.) | ENSC's formulas (eqs. 2.14-2.16, after Schaalje et al.), **its R code** (Appendix C, p. 140 on), and a published open-set validation on the Federalist Papers (Table 3.1 and the second study) | record: https://scholarsarchive.byu.edu/etd/2402 ; PDF: https://scholarsarchive.byu.edu/cgi/viewcontent.cgi?article=3401&context=etd | downloaded by the owner in a browser 2026-10-30, `data/private/fidelity/funai2010.pdf` |
| Schaalje, Fields, Roper and Snow (2011), "Extended nearest shrunken centroid classification: a new method for open-set authorship attribution of texts of varying sizes", *Literary and Linguistic Computing* 26(1): 71-88 | ENSC's published definition and validation | DOI (paywalled, Oxford Academic): https://doi.org/10.1093/llc/fqq029 (found via Crossref, https://api.crossref.org) | not needed: Funai (2010) gives the formulas and code |
| Fields, Schaalje and Roper (2011), "Examining a misapplication of nearest shrunken centroid classification to investigate Book of Mormon authorship", *Mormon Studies Review* 23(1): 87-111 | the authors' plain description of ENSC (pp. 105-108) and its Book of Mormon results (figs. 9-10) | https://scholarsarchive.byu.edu/msr/vol23/iss1/8 (PDF via the page's Download button) | downloaded by the owner in a browser 2026-10-30, `data/private/fidelity/fields2011_msr.pdf` |
| Schaalje and Fields (2012), "Open-set nearest shrunken centroid classification", *Communications in Statistics - Theory and Methods* | the statistical definition of the open-set ("none of the above") rule | DOI (paywalled, Taylor & Francis): https://doi.org/10.1080/03610926.2010.529529 (found via Crossref; authors G. Bruce Schaalje and Paul J. Fields) | not needed: Funai (2010) gives the formulas and code |
| Larsen, Rencher and Layton (1980), "Who wrote the Book of Mormon? An analysis of wordprints", *BYU Studies* 20(3): 225-251 | the original design and word lists for the Larsen replication (BOM-22) | https://archive.bookofmormoncentral.org/sites/default/files/archive-files/pdf/larsen/2015-10-22/wayne_a._larsen_alvin_c._rencher_and_tim_layton_who_wrote_the_book_of_mormon_1980_0.pdf (also https://scholarsarchive.byu.edu/byusq/vol20/iss3/2) | downloaded 2026-10-30, `data/private/fidelity/larsen1980.pdf` |
| Stamatatos et al. (2014), "Overview of the author identification task at PAN 2014" | the PAN 2014 corpora, the AUC x c@1 measure and competitors' results | https://ceur-ws.org/Vol-1180/CLEF2014wn-Pan-StamatosEt2014.pdf | downloaded 2026-10-30, `data/private/fidelity/stamatatos2014_pan.pdf` |
| Holmes (1992), "A stylometric analysis of Mormon scripture and related texts", *JRSS A* 155(1): 91-120 | all nine tables (per-sample richness values; noun distributions and Sichel fits, Tables 3-4) and the fitting method (minimum chi-square on nouns, 10,000-word-equivalent alpha and theta) | https://doi.org/10.2307/2982671 (JSTOR) | supplied by the owner 2026-10-30 as a full-text conversion, `data/private/fidelity/holmes1992.md` |
| PAN 2014 author verification corpora (training and test) | the data Kestemont et al. report on | to be recorded when downloaded | |

## What the sources say so far

**ENSC's open-set rule (Fields, Schaalje and Roper 2011, p. 105).** "The open-set modification
allows for the existence of an unknown candidate author with a distribution of characteristic
features nominally consistent with the test text and incorporates this possibility into the
calculation of the probabilities", and "also accounts for differences in text sizes and for the
effect of multiple simultaneous comparisons". Our `classic/ensc.py` instead says "none" when every
candidate's likelihood is below alpha. **That is a structural difference, not a setting**, and the
formulas are needed (Funai 2010, or the 2011 paper) to rebuild it faithfully.

**ENSC as published (Funai 2010, eqs. 2.14-2.16 and Appendix C).** The posterior for candidate k is
`pi_k exp(-1/2 sum_j ((x_j - c_kj)/s_j)^2)` over the sum of the same terms for all m candidates
**plus a latent-author term** `pi_(m+1) exp(-1/2 sum_j a_j^2)`, with
`a_j = min(max_i |x_j - c_ij| / s_j, lambda)`; centroids `c` are shrunken with the fudge factor
`s0` (median `s_j`). The text is assigned to whichever of the m+1 classes has the highest
posterior. The code gives every class, latent included, prior `1/(m+1)`, and sets `lambda` per run
(1.5, 2 or 3). **Published validation:** 108 function words; candidates Joseph Smith, early and
late Rigdon, Spalding, Cowdery, Pratt; (1) Hamilton left out, all 51 Hamilton papers should go to
the latent author: 15.69% misclassified (43 of 51 correct); (2) 26 Hamilton papers in training, 25
tested: 16% misclassified.

**Their Book of Mormon results (figs. 9-10)**, 110 words and Jockers et al.'s chapters, early Rigdon
texts only, Joseph Smith added: ENSC gives 73% of chapters to "someone else" with the control
authors in (Spalding 1%, Rigdon 7%, Cowdery 1%, Pratt 0%, Isaiah-Malachi 15%, Joseph Smith 3%), and
93% with the controls removed (Rigdon 0%, Cowdery 4%, Joseph Smith 3%). Our reconstruction (BOM-22)
gave 98% "none". Their closed-set NSC with controls in: Spalding 22%, Rigdon 39%, Cowdery 8%,
Pratt 4%, Isaiah-Malachi 26%, Longfellow 1%.

## Still wanted

Ranked by how much each could change a conclusion. "Paywalled" needs a library login or purchase;
"browser only" is free but refuses scripted downloads (a JavaScript check), so it is fetched by
hand. DOIs checked against Crossref on 2026-10-30.

| # | Paper | Why | Link | Access |
| --- | --- | --- | --- | --- |
| 1 | Jockers, Witten and Criddle (2008), *LLC* 23(4) | Tables 1-2 and Appendix A list exactly which Rigdon, Pratt and Cowdery texts they used; our replication disagrees with theirs and the candidate samples are the likeliest reason | https://doi.org/10.1093/llc/fqn040 | paywalled |
| 2 | Koppel and Winter (2014), "Determining if two documents are written by the same author", *JASIST* 65(1) | General Imposters' original definition and settings | https://doi.org/10.1002/asi.22954 | paywalled |
| 3 | Kestemont et al. (2016), supplementary information | O2's exact iterations, feature share and imposter count for the PAN check | https://doi.org/10.1016/j.eswa.2016.06.029 (SI linked from the article page) | browser only, possibly paywalled |
| 4 | Schaalje, Fields, Roper and Snow (2011), *LLC* 26(1) | ENSC's per-chapter Book of Mormon results and its own validation, for an exact replication match | https://doi.org/10.1093/llc/fqq029 | paywalled |
| 6 | Jockers (2012), "Testing authorship in the personal writings of Joseph Smith using NSC classification", *LLC* | the Jockers side's answer to the open-set critique | https://doi.org/10.1093/llc/fqs041 | paywalled |
| 7 | Evert et al. (2017), "Understanding and explaining Delta measures for authorship attribution", *DSH* 32 | why and when Delta works; the best-practice variants (to improve the two Deltas) | https://doi.org/10.1093/llc/fqx023 | paywalled |
| 8 | Tibshirani, Hastie, Narasimhan and Chu (2002), *PNAS* 99(10) | NSC's original definition | https://doi.org/10.1073/pnas.082099299 ; free copy https://pmc.ncbi.nlm.nih.gov/articles/PMC124443/ | browser only |
| 9 | Burrows (2002), "'Delta': a measure of stylistic difference and a guide to likely authorship", *LLC* 17(3) | Delta's original definition | https://doi.org/10.1093/llc/17.3.267 | paywalled |
