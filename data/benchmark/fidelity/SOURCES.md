# Sources for the fidelity check (BOM-57)

Is our code for the two methods that failed BOM-21 (General Imposters, `classic/imposters.py`;
ENSC, `classic/ensc.py`) faithful to the published methods? Each source below is listed with the
link it was obtained from. **Rule (owner, 2026-10-30):** paper files are kept in the private data
repo (`data/private/fidelity/`) and never published here, since we may not have the right to;
this file references each one by link instead, and where a paper is already freely available the
public link is the reference.

| Source | What it gives | Link | Obtained |
| --- | --- | --- | --- |
| Kestemont, Stover, Koppel, Karsdorp and Daelemans (2016), "Authenticating the writings of Julius Caesar", *Expert Systems with Applications* 63: 86-96. Authors' accepted manuscript. | General Imposters as our code implements it ("O2"); Table 1: test results on the six PAN 2014 verification corpora by distance and weighting | https://www.pure.ed.ac.uk/ws/files/38106536/Stover_et_al_2016_ESA_Authenticating_the_writings_of_Julius_Caesar_AM.pdf ; peer-reviewed version also at https://pure.knaw.nl/portal/en/publications/authenticating-the-writings-of-julius-caesar/ | downloaded 2026-10-30, `data/private/fidelity/kestemont2016_am.pdf`; KNAW copy supplied by the owner, `kestemont2016_knaw.pdf` (neither includes the supplement) |
| Seidman (2013), "Authorship Verification Using the Impostors Method", PAN at CLEF 2013 notebook | the PAN 2013 winning impostors variant (symmetric similarity, web impostors); accuracy by language | https://ceur-ws.org/Vol-1179/CLEF2013wn-PAN-Seidman2013.pdf | downloaded 2026-10-30, `data/private/fidelity/seidman2013.pdf` |
| Funai (2010), *Extensions of Nearest Shrunken Centroid Method for Classification*, MS thesis, Brigham Young University (168 pp.) | ENSC's formulas (eqs. 2.14-2.16, after Schaalje et al.), **its R code** (Appendix C, p. 140 on), and a published open-set validation on the Federalist Papers (Table 3.1 and the second study) | record: https://scholarsarchive.byu.edu/etd/2402 ; PDF: https://scholarsarchive.byu.edu/cgi/viewcontent.cgi?article=3401&context=etd | downloaded by the owner in a browser 2026-10-30, `data/private/fidelity/funai2010.pdf` |
| Schaalje, Fields, Roper and Snow (2011), "Extended nearest shrunken centroid classification: a new method for open-set authorship attribution of texts of varying sizes", *Literary and Linguistic Computing* 26(1): 71-88 | ENSC's published definition and validation | DOI (paywalled, Oxford Academic): https://doi.org/10.1093/llc/fqq029 (found via Crossref, https://api.crossref.org) | not needed: Funai (2010) gives the formulas and code |
| Fields, Schaalje and Roper (2011), "Examining a misapplication of nearest shrunken centroid classification to investigate Book of Mormon authorship", *Mormon Studies Review* 23(1): 87-111 | the authors' plain description of ENSC (pp. 105-108) and its Book of Mormon results (figs. 9-10) | https://scholarsarchive.byu.edu/msr/vol23/iss1/8 (PDF via the page's Download button) | downloaded by the owner in a browser 2026-10-30, `data/private/fidelity/fields2011_msr.pdf` |
| Schaalje and Fields (2012), "Open-set nearest shrunken centroid classification", *Communications in Statistics - Theory and Methods* | the statistical definition of the open-set ("none of the above") rule | DOI (paywalled, Taylor & Francis): https://doi.org/10.1080/03610926.2010.529529 (found via Crossref; authors G. Bruce Schaalje and Paul J. Fields) | not needed: Funai (2010) gives the formulas and code |
| Larsen, Rencher and Layton (1980), "Who wrote the Book of Mormon? An analysis of wordprints", *BYU Studies* 20(3): 225-251 | the original design and word lists for the Larsen replication (BOM-22) | https://archive.bookofmormoncentral.org/sites/default/files/archive-files/pdf/larsen/2015-10-22/wayne_a._larsen_alvin_c._rencher_and_tim_layton_who_wrote_the_book_of_mormon_1980_0.pdf (also https://scholarsarchive.byu.edu/byusq/vol20/iss3/2) | downloaded 2026-10-30, `data/private/fidelity/larsen1980.pdf` |
| Stamatatos et al. (2014), "Overview of the author identification task at PAN 2014" | the PAN 2014 corpora, the AUC x c@1 measure and competitors' results | https://ceur-ws.org/Vol-1180/CLEF2014wn-Pan-StamatosEt2014.pdf | downloaded 2026-10-30, `data/private/fidelity/stamatatos2014_pan.pdf` |
| Holmes (1992), "A stylometric analysis of Mormon scripture and related texts", *JRSS A* 155(1): 91-120 | all nine tables (per-sample richness values; noun distributions and Sichel fits, Tables 3-4) and the fitting method (minimum chi-square on nouns, 10,000-word-equivalent alpha and theta) | https://doi.org/10.2307/2982671 (JSTOR) | supplied by the owner 2026-10-30 as a full-text conversion, `data/private/fidelity/holmes1992.md` |
| Koppel and Winter, "Determining if two documents are by the same author", lecture slides (26) | the impostors method step by step; not the paper | https://cs.cornell.edu/courses/cs6740/2016sp/classes/Determining%20If%20Two%20Documents%20Are%20by%20the%20Same.pdf | downloaded 2026-10-30, `data/private/fidelity/koppel_winter_slides.pdf` |
| Jockers, Witten and Criddle (2008), "Reassessing authorship of the Book of Mormon using delta and nearest shrunken centroid classification", *LLC* 23(4): 465-491 | Appendix A: exact candidate source texts (Bible passages removed from all); Appendix B: the exact 110 words (seven-author case) and 108 (five-author case) | https://doi.org/10.1093/llc/fqn040 | bought by the owner 2026-10-30 (BOM-59), `data/private/fidelity/jockers2008.pdf` |
| Schaalje, Fields, Roper and Snow (2011), "Extended nearest shrunken centroid classification: a new method for open-set authorship attribution of texts of varying sizes", *LLC* 26(1): 71-88 | ENSC as published: open-set term (eqs. 10-11, lambda at least 3), the text-size adjustment (eq. 12), the Hamilton validation (Fig. 5), and the candidate texts (Appendix B: composites of about 3,300-6,800 words) | https://doi.org/10.1093/llc/fqq029 | bought by the owner 2026-10-30 (BOM-59), `data/private/fidelity/schaalje2011.pdf` |
| Evert, Proisl, Jannidis, Reger, Pielström, Schöch and Vitt (2017), "Understanding and explaining Delta measures for authorship attribution", *DSH* 32(suppl. 2) | why and when the Delta measures work; the best-performing variants | https://doi.org/10.1093/llc/fqx023 | supplied by the owner 2026-10-30, `data/private/fidelity/evert2017.pdf` |
| Burrows (2002), "'Delta': a measure of stylistic difference and a guide to likely authorship", *LLC* 17(3): 267-287 | Delta's original definition | https://doi.org/10.1093/llc/17.3.267 | supplied by the owner 2026-10-30, `data/private/fidelity/burrows2002.pdf` |
| Tibshirani, Hastie, Narasimhan and Chu (2002), "Diagnosis of multiple cancer types by shrunken centroids of gene expression", *PNAS* 99(10): 6567-6572 | NSC's original definition | https://doi.org/10.1073/pnas.082099299 ; free at https://pmc.ncbi.nlm.nih.gov/articles/PMC124443/ | supplied by the owner 2026-10-30, `data/private/fidelity/tibshirani2002.pdf` |
| Jockers (2012), "Testing authorship in the personal writings of Joseph Smith using NSC classification", *LLC* | the Jockers side's follow-up on Joseph Smith's own writing | https://doi.org/10.1093/llc/fqs041 | supplied by the owner 2026-10-30, `data/private/fidelity/jockers2012.pdf` |
| PAN 2014 author verification corpora (training, test 1, test 2; six corpora) | the data Kestemont et al. report on; open access, no licence stated, modern texts by living authors, so kept private | https://doi.org/10.5281/zenodo.3716033 (file `pan14-authorship-verification-test-and-training.zip`, 24,818,707 bytes, md5 f7c504fd27f3c6e1f92b526fd15bc942) | downloaded 2026-10-30, `data/private/pan14/`; extracted copy rebuilt by unzipping (not in git) |
| Kestemont et al., `ruzicka` code (commit 69871e2fd098c64abf0be6eec2f17ebb8a6122a1, 2023-06-27) | O2's settings for the PAN runs (`code/01pan_experiments.py`: profiles, 100 rounds, half the features, 30 imposters, score shifter) | https://github.com/mikekestemont/ruzicka | read only, not run, not copied |

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

None of these blocks any result. Each is worth buying only if the condition in the last column
comes true; the owner has asked to be told when one would strengthen the final product. DOIs
checked against Crossref on 2026-10-30.

| Paper | Why it might matter | Link | Get it if |
| --- | --- | --- | --- |
| Koppel and Winter (2014), "Determining if two documents are written by the same author", *JASIST* 65(1) | General Imposters' original definition and settings | https://doi.org/10.1002/asi.22954 (Wiley) | the General Imposters fidelity check against Kestemont et al. is ambiguous, or the paper discusses GI's origin |
| Hoover (2003), "Another perspective on vocabulary richness", *Computers and the Humanities* 37 | the usual citation for the critique of vocabulary richness (Holmes replication) | https://doi.org/10.1023/a:1022673822140 (Springer) | the final paper cites it; until read, it is cited only as "usually cited for", never as a source we checked |
| Kestemont et al. (2016), supplementary information | O2's exact iterations, feature share and imposter count | https://doi.org/10.1016/j.eswa.2016.06.029 | their public code (https://github.com/mikekestemont/ruzicka) does not settle the settings |
