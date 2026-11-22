# Prior art: a census of testable studies of the Book of Mormon

2026-11-22. This is the first fill of the "Prior art" table the owner wants for his website: one
row per earlier study, with what it claimed, whether we reproduced it, how we tested the same
claim, and what still holds. The records are in `data/lab/prior_art/studies.json` (183 records,
field meanings below). This is research and writing only. No test was run and no AI judge was
called, nothing was committed, and no licensed full text was fetched.

The census takes no side. A study is in it if it makes a claim that evidence could check, on any
side. Pure theology and devotional writing are left out.

## How the census was made

1. **What we hold.** I read `paper/blog-tests.md`, `paper/replication-report.md`,
   `docs/claims-verdicts.md`, `docs/results-inventory.md`, `docs/prior-studies.md`,
   `docs/italics-plan.md`, the research notes of 2026-11-18, 11-20 and 11-22 (redesigns for
   debates, geography, translation and three worlds), `data/lab/SOURCES.md`,
   `docs/holdings.md`, the issue list for BOM-99 to BOM-127, and the lab result files where a
   number was needed (`emode_syntax`, `chiasmus`, `names`, `dictated_texts`, `dictations`,
   `dale_checklist`, `anachronisms`, `claimed_sources`, `mosiah_priority`).
2. **The literature.** Four AI research agents searched the web in parallel, one topic group
   each: authorship and production; sources, Bible dependence and context; language and names;
   setting. Each was told to give numbers only from a page it had opened, and to say for every
   record whether it read the paper, only an abstract or record page, or only someone else's
   description. They returned 192 records. Duplicates of each other and of our own records were
   merged by hand, leaving 183. Two records were dropped as not being studies: a blog summary of
   other people's stylometry, and a chapter that argues logic without a checkable claim. None of
   this was checked by a person.
3. **Merge rule.** Where our files and a web record describe the same study, our numbers win.
   The web record supplied the citation, URL and their method. A `their_method` not read in the
   original carries "(from abstract: URL)" or "(from secondary source: URL)". The web check found
   errors in our own notes, and those are corrected in the records (see "What our write-ups claim
   beyond the files", and the Skousen 1994, Tvedtnes, Gee and Roper 2000, Clark 1989 and Edwards
   2004 records).
4. **Reproduced against tested.** These are kept strictly apart.
   - `replicated` asks one thing: did we reproduce **their number, their way**? "yes" means their
     method on their kind of data gave their figures. "partly" means some of their figures came
     back, or only the conclusion did, or their arithmetic reproduced but their coding was not
     redone. Everything else is "not attempted", "not possible: no method to rerun" or "not
     replicated until the source is bought".
   - `our_approach` and `our_result` record a test of the **same claim our own way**, usually
     with a comparison set the original never had. That is not replication, and the table counts
     it separately.
   - A study whose topic has a lab issue, but whose own claim that issue did not test, is marked
     "related only".

## Fields in `studies.json`

`id`, `topic` (authorship, production, language, sources, context, setting, other),
`citation`, `year`, `url`, `side` (the side the study itself argues), `claim`, `their_method`,
`kind` (statistical, list of examples, argument), `replicable_with`, `our_issue`, `replicated`,
`replication_note`, `strengths`, `weaknesses`, `our_approach`, `our_result`, `what_holds`,
`todo`. Where a web record gave no specific strength or weakness, a short default by kind is
used, followed by the replies the agent found. Those defaults are the weakest text in the file
and should be rewritten as each study is read.

## Counts

| | Studies |
| --- | --- |
| In the census | 183 |
| Reproduced their way: yes | 4 (Larsen 1980; Holmes 1992; Wright 1998 and Spencer 2020 italics counts) |
| Reproduced their way: partly | 12 (Jockers 2008, Schaalje 2011, Johnson and Johnson 2013, Metcalfe 1993, Hales 2019, Carmack 2015, Carmack 2017, Edwards and Edwards 2004, Tvedtnes, Gee and Roper 2000, Holley 1983, Dale and Dale 2019, Roper 2025) |
| Tested the same claim our own way only | 61 |
| Related lab issue, but the study's own claim not tested | 37 |
| Not touched at all | 69 |
| No method to rerun (argument or unpublished method) | 6 |
| Waiting on a source to buy | 4 |

By side, the census holds 113 studies arguing an ancient or translated origin, 46 arguing a
nineteenth-century one and 24 neutral or methodological. Of the 77 we reproduced or tested, 42,
28 and 7. The tilt toward the first side mostly reflects where the literature is: one side
publishes many short evidence notes (single names, single sites). It is not a judgement.

By kind: 93 lists of examples, 47 arguments, 43 statistical studies. Most "lists of examples"
lack a control, and that is the single most common weakness in the table: a count with nothing
to compare it to.

## The table, by topic

"Reproduced their way?" is the strict column. "Tested our way?" means a lab or study test
addressed the same claim with our own method. "What holds" is the first clause of the record's
`what_holds`; the full sentence is in the JSON.

### Authorship (23)

| Study | Side | Kind | Reproduced their way? | Our test | Tested our way? | What holds |
| --- | --- | --- | --- | --- | --- | --- |
| Bush 1977 | neutral | argument | no |  |  | Cannot tell yet |
| Cowdrey 1977 | 19th c. | list of examples | no |  |  | Does not hold on the record as summarised: two of the three examiners withdrew; not tested here |
| Phipps 1977 | neutral | statistical | no | BOM-104 | yes | Cannot tell yet |
| Larsen 1980 | ancient | statistical | yes | BOM-22 | yes | Holds in part |
| Croft 1981 | neutral | argument | no |  |  | Cannot tell yet |
| Roberts 1983 | ancient | statistical | no |  |  | Cannot tell yet |
| Hilton 1990 | ancient | statistical | no |  |  | Cannot tell yet |
| Holmes 1992 | 19th c. | statistical | yes | BOM-22 | yes | Holds |
| Archer 1997 | ancient | statistical | no |  |  | Cannot tell yet |
| Cowdrey 2005 | 19th c. | argument | no | BOM-24 | related only | Cannot tell |
| Reynolds 2005 | neutral | argument | no | BOM-104 | yes | Cannot tell yet |
| Roper 2005 | ancient | list of examples | no | BOM-24 | yes | Holds in part |
| Moon, Howland and Gunther 2006 | ancient | statistical | no |  |  | Cannot tell yet |
| Jockers 2008 | 19th c. | statistical | partly | BOM-22 | yes | Does not hold |
| Fields 2011 | ancient | statistical | no | BOM-22 | related only | Holds in part, as for schaalje2011 |
| Roper and Fields 2011 | ancient | argument | no |  |  | Cannot tell yet |
| Schaalje 2011 | ancient | statistical | partly | BOM-22 | yes | Holds in part |
| Roper 2012 | ancient | statistical | no |  |  | Cannot tell yet |
| Jockers 2013 | neutral | statistical | no |  |  | Cannot tell yet |
| Fields, Bassist and Roper (voices) | ancient | statistical | no method | BOM-121 | yes | Holds in part |
| Rasmussen ep. 11 (stylometry) | ancient | statistical | no |  |  | Cannot tell yet |
| Hilton III 2024 | ancient | list of examples | no | BOM-121 | yes | Holds in part |
| "Machine Learning Redux" (Substack 2026) | neutral | statistical | no |  |  | Cannot tell yet; its own decoy result agrees with the study's finding that the revelation register, not the person, drives closeness |

### Production (9)

| Study | Side | Kind | Reproduced their way? | Our test | Tested our way? | What holds |
| --- | --- | --- | --- | --- | --- | --- |
| Metcalfe 1993 | 19th c. | statistical | partly | BOM-120 | yes | Holds |
| Roper 1994 | ancient | list of examples | no | BOM-120 | related only | Not addressed by BOM-120, which tested the word switch, not prophecy wording |
| Skousen 1998 | ancient | list of examples | no | BOM-127 | yes | Holds in part |
| Dunn 2002 | 19th c. | list of examples | no | BOM-125 | yes | Holds in part |
| Rees 2006 | ancient | argument | no | BOM-125 | yes | Holds in part on what was measured; his Near Eastern and Mesoamerican features were not counted |
| Welch 2018 | ancient | argument | no |  |  | Cannot tell yet |
| Hales 2019 | ancient | list of examples | partly | BOM-125 | yes | Does not hold on the measures counted |
| Davis 2020 | 19th c. | list of examples | no | BOM-106 | yes | Holds in part |
| Rasmussen ep. 3 (dictation) | ancient | statistical | no |  |  | Cannot tell yet |

### Language and names (49)

| Study | Side | Kind | Reproduced their way? | Our test | Tested our way? | What holds |
| --- | --- | --- | --- | --- | --- | --- |
| Brookbank 1909 | ancient | list of examples | no | BOM-102 | related only | Does not hold as evidence of Hebrew for the constructions BOM-102 could count (see tvedtnes1970) |
| Nibley 1952 | ancient | list of examples | no | BOM-108 | yes | Cannot tell yet |
| Sperry 1935, 1954 | ancient | list of examples | no | BOM-102 | related only | As for tvedtnes1970 |
| Welch 1969 | ancient | list of examples | no | BOM-107 | yes | Cannot tell for idea-level chiasmus |
| Tvedtnes 1970 | ancient | list of examples | no | BOM-102 | yes | Does not hold as evidence of Hebrew |
| Gee 1992 | ancient | list of examples | no | BOM-108 | related only | Cannot tell |
| Ashment 1993 | 19th c. | argument | no | BOM-102 | yes | Holds for the constructions counted |
| Chadwick 1993 | ancient | list of examples | no | BOM-108 | related only | Cannot tell |
| Skousen 1993 | ancient | list of examples | no | BOM-102 | related only | Cannot tell yet |
| Skousen 1994 | ancient | list of examples | no | BOM-102 | related only | Cannot tell yet |
| Welch 1995 | neutral | argument | no | BOM-107 | related only | Cannot tell yet |
| Ricks and Tvedtnes 1997 | ancient | list of examples | no | BOM-108 | related only | Cannot tell |
| Skousen 1997 | ancient | list of examples | no | BOM-102 | related only | Cannot tell yet (see skousen1994_ifand) |
| Hoskisson 1998 | ancient | list of examples | no | BOM-108 | related only | Cannot tell |
| Tvedtnes, Gee and Roper 2000 | ancient | list of examples | partly | BOM-108 | yes | Cannot tell yet |
| Vogel 2001 | 19th c. | argument | no | BOM-107 | related only | Cannot tell yet |
| Parry 2002 | ancient | list of examples | no | BOM-102 | yes | Does not hold as evidence of Hebrew for the categories counted |
| Edwards and Edwards 2004 | neutral | statistical | partly | BOM-107 | yes | Cannot tell yet |
| Wunderli 2005 | 19th c. | argument | no | BOM-107 | yes | Holds in part |
| Edwards and Edwards 2006 | neutral | statistical | no | BOM-107 | related only | Cannot tell yet |
| Parry 2007 | ancient | list of examples | no | BOM-107 | related only | Cannot tell yet |
| Edwards and Edwards 2010 | neutral | statistical | no | BOM-107 | yes | Cannot tell yet |
| Black and Wilcox 2011 | ancient | argument | no | BOM-108 | yes | Does not hold as stated |
| Wilcox 2013 | neutral | statistical | no | BOM-108 | related only | Cannot tell yet |
| Wunderli 2013 | 19th c. | statistical | no | BOM-120 | yes | Holds for the therefore/wherefore switch (BOM-120) |
| Carmack 2014 | ancient | list of examples | no | BOM-119 | related only | Cannot tell yet |
| Carmack 2015 (did) | ancient | statistical | partly | BOM-119 | yes | Holds in part |
| Grover 2015 | ancient | list of examples | no |  |  | Cannot tell yet |
| Book of Mormon Onomasticon | ancient | list of examples | no | BOM-108 | related only | Cannot tell |
| Stubbs 2015 | ancient | list of examples | source to buy | BOM-117 | related only | Cannot tell yet |
| Carmack 2016 | ancient | list of examples | no | BOM-119 | yes | Cannot tell |
| Skousen 2016 | ancient | list of examples | no | BOM-119 | related only | Cannot tell yet |
| Carmack 2017 (Barlow) | ancient | list of examples | no |  |  | Cannot tell yet |
| Carmack 2017 (1832 History) | ancient | statistical | partly | BOM-119 | yes | Holds |
| Robertson 2017 | neutral | argument | no | BOM-117 | related only | Cannot tell yet |
| Carmack 2018 (pseudo-archaic) | ancient | statistical | no | BOM-119 | yes | Cannot tell yet for the bundle |
| Hardy 2018 | neutral | argument | no |  |  | Cannot tell yet |
| Skousen and Carmack 2018 (vocabulary) | ancient | list of examples | no | BOM-118 | yes | Holds in part |
| Wilcox 2018 | ancient | statistical | no | BOM-108 | related only | Cannot tell yet |
| Green 2019 | neutral | argument | no |  |  | Holds in part |
| Rappleye 2019 | ancient | list of examples | no | BOM-108 | related only | Cannot tell |
| Rogers 2019 | neutral | argument | no | BOM-117 | related only | Cannot tell yet |
| Wilcox and others 2019 | ancient | statistical | no method | BOM-108 | yes | Cannot tell |
| Parry 2020 | ancient | list of examples | no | BOM-102 | yes | Does not hold for the categories counted; most of its thirty structures were not counted |
| Skousen and Carmack 2020 | ancient | list of examples | no | BOM-118 | yes | Holds in part |
| Carmack 2021 (finite cause) | ancient | statistical | no | BOM-119 | yes | Cannot tell yet |
| Carmack 2021 (relative pronouns) | ancient | statistical | no | BOM-119 | yes | Cannot tell yet |
| Carmack 2024 | ancient | list of examples | no |  |  | Cannot tell yet |
| Davis 2025 | 19th c. | argument | no | BOM-118 | yes | Holds in part |

### Sources and Bible dependence (30)

| Study | Side | Kind | Reproduced their way? | Our test | Tested our way? | What holds |
| --- | --- | --- | --- | --- | --- | --- |
| Howe 1834 (Spalding theory) | 19th c. | argument | no method | BOM-24 | yes | Does not hold for the surviving manuscript; cannot tell for the lost one |
| Roberts 1922 | neutral | list of examples | no | BOM-25 | yes | Does not hold at the level of wording, passages or plot; the shared themes are common to the period's writing on Indian origins |
| Lehi's dream and Joseph Smith Sr.'s dream | 19th c. | list of examples | no |  |  | Cannot tell yet |
| Stendahl 1978 | neutral | list of examples | no |  |  | Cannot tell yet |
| Deutero-Isaiah argument | neutral | argument | no |  |  | Cannot tell yet |
| Tvedtnes 1981 | ancient | list of examples | no | BOM-122 | yes | Cannot tell yet |
| Persuitte 1985 | 19th c. | list of examples | no | BOM-25 | yes | Does not hold for wording, passages or plot |
| Welch 1985 | ancient | list of examples | no | BOM-25 | yes | Holds |
| Larson 1986 | 19th c. | list of examples | no |  |  | Cannot tell yet |
| Priest as a source (Tanner 1987) | 19th c. | list of examples | no | BOM-115 | yes | Holds in part |
| Welch 1990 | ancient | list of examples | no |  |  | Cannot tell yet |
| Huggins 1997 | 19th c. | list of examples | no |  |  | Cannot tell yet |
| Wright 1998 | 19th c. | statistical | yes | BOM-62 | yes | Holds as a description |
| Davis 2012 | 19th c. | list of examples | no | BOM-126 | yes | Does not hold at passage level; a borrowed plot outline was not tested |
| Donofrio 2012 | 19th c. | list of examples | no | BOM-126 | yes | Does not hold |
| Johnson and Johnson 2013 | 19th c. | statistical | partly | BOM-22 | yes | Holds in part |
| McGuire 2013 | ancient | statistical | no | BOM-24 | yes | Holds |
| First Book of Napoleon claim (CES Letter) | 19th c. | list of examples | no | BOM-24 | yes | Holds in part |
| Runnells, 1769 KJV errors | 19th c. | list of examples | no |  |  | Cannot tell yet |
| Schaalje 2013 | ancient | statistical | no | BOM-24 | related only | Cannot tell yet |
| Grunder 2014 | 19th c. | list of examples | no | BOM-33 | yes | Holds in part |
| Frederick 2015 | neutral | argument | no | BOM-124 | yes | Holds as a description |
| Townsend 2018 | 19th c. | statistical | no |  |  | Cannot tell yet |
| Skousen 2019 | ancient | statistical | no | BOM-62 | related only | Cannot tell yet |
| Spencer 2020 | ancient | statistical | yes | BOM-62 | yes | Holds as a count; the explanation cannot be told apart from Wright's by this test |
| Townsend 2022 | 19th c. | list of examples | no |  |  | Cannot tell yet |
| Jackson 2025 | ancient | argument | no | BOM-122 | yes | Holds by wording; the argued-reading cases remain open |
| Townsend 2025 | 19th c. | list of examples | source to buy | BOM-122 | yes | Does not hold by wording; the argued-reading part is untested |
| Camora / Moroni map claim | 19th c. | list of examples | no |  |  | Cannot tell yet |
| Gibson, KJV word count | ancient | statistical | no |  |  | Cannot tell yet |

### Nineteenth-century context (12)

| Study | Side | Kind | Reproduced their way? | Our test | Tested our way? | What holds |
| --- | --- | --- | --- | --- | --- | --- |
| Campbell 1831 | 19th c. | argument | no method | BOM-103 | yes | Cannot tell yet |
| Brodie 1945 | 19th c. | argument | no method | BOM-29 | yes | Does not hold for the language on these models; the environment of ideas is untested |
| Bushman 1976 | ancient | list of examples | no |  |  | Cannot tell yet |
| Vogel 1989 | 19th c. | list of examples | no | BOM-123 | yes | Cannot tell yet |
| Peterson 1990 | ancient | list of examples | no | BOM-123 | yes | Cannot tell yet |
| Peterson 1992 | ancient | list of examples | no | BOM-123 | yes | Holds for 'not new'; meaning unscored |
| Vogel 1993 | 19th c. | list of examples | no | BOM-103 | yes | Cannot tell yet |
| Thomas 1999 | 19th c. | argument | no |  |  | Cannot tell yet |
| Huggins 2003 | 19th c. | argument | no |  |  | Cannot tell yet |
| Mouritsen 2003 | ancient | list of examples | no | BOM-123 | yes | Cannot tell yet |
| Forsberg 2004 | 19th c. | argument | no |  |  | Cannot tell yet |
| Shalev 2013 | 19th c. | argument | no method | BOM-31 | yes | Holds in part |

### Setting (51)

| Study | Side | Kind | Reproduced their way? | Our test | Tested our way? | What holds |
| --- | --- | --- | --- | --- | --- | --- |
| Ferguson 1958 | ancient | list of examples | no |  |  | Cannot tell yet |
| Jakeman 1958 | ancient | list of examples | no |  |  | Does not hold on the record (Clark 1999); not tested here |
| Coe 1973 | 19th c. | list of examples | no | BOM-111 | yes | Holds as a description of the vocabulary: the book names the Bible's things, not Mesoamerica's; this compares words, not archaeology |
| Ferguson 1975 | 19th c. | list of examples | no | BOM-111 | yes | Holds as a description of the vocabulary; archaeology not tested here |
| Hilton and Hilton 1976 | ancient | list of examples | no |  |  | Cannot tell yet |
| Palmer 1981 | ancient | list of examples | no |  |  | Cannot tell yet |
| Holley 1983 | 19th c. | list of examples | partly | BOM-110 | yes | Does not hold |
| Sorenson 1985 | ancient | list of examples | source to buy | BOM-116 | yes | Cannot tell yet |
| Vogel 1986 | 19th c. | list of examples | no | BOM-115 | yes | Holds in part |
| Clark 1989 | ancient | argument | no | BOM-116 | yes | Cannot tell yet |
| Hamblin and Merrill 1990 | ancient | list of examples | no | BOM-115 | yes | Cannot tell |
| Kunich 1990 | neutral | statistical | no |  |  | Cannot tell yet |
| Sorenson 1990 (source book) | neutral | list of examples | no | BOM-116 | related only | Cannot tell yet |
| Sorenson 1992 | ancient | list of examples | no | BOM-111 | related only | Cannot tell yet |
| Sorenson and Smith 1992 | ancient | list of examples | no | BOM-113 | related only | Cannot tell yet |
| Matheny 1993 | 19th c. | argument | no | BOM-116 | related only | Cannot tell yet |
| Aston and Aston 1994 | ancient | list of examples | no |  |  | Cannot tell yet |
| Smith 1997 | ancient | statistical | no |  |  | Cannot tell yet |
| Brown 1999 | ancient | list of examples | no |  |  | Cannot tell yet |
| Clark 1999 | neutral | argument | no |  |  | Cannot tell yet |
| Potter 1999 | ancient | list of examples | no |  |  | Cannot tell yet |
| Roper 1999 | ancient | list of examples | no | BOM-115 | related only | Cannot tell (as for hamblin_merrill1990) |
| Welch 1999 | ancient | list of examples | no | BOM-114 | yes | Cannot tell yet |
| Aston 2001 | ancient | list of examples | no |  |  | Cannot tell yet |
| Murphy 2002 | 19th c. | argument | no |  |  | Cannot tell here |
| Wunderli 2002 | 19th c. | argument | no | BOM-116 | related only | Cannot tell yet |
| Butler 2003 | ancient | argument | no |  |  | Cannot tell here |
| Jordan 2003 | ancient | argument | no |  |  | Cannot tell yet |
| Meldrum and Stephens 2003 | ancient | argument | no |  |  | Cannot tell here |
| Whiting 2003 | ancient | argument | no |  |  | Cannot tell here |
| Olsen 2004 | ancient | list of examples | no | BOM-116 | related only | Cannot tell yet |
| Southerton 2004 | 19th c. | argument | no |  |  | Cannot tell here |
| Clark 2005 | ancient | list of examples | no | BOM-113 | yes | Cannot tell yet |
| Stewart 2006 | ancient | argument | no |  |  | Cannot tell here |
| Aston 2008 | ancient | list of examples | no |  |  | Cannot tell yet |
| Meldrum 2009 | ancient | argument | no |  |  | Cannot tell yet |
| Porter and Meldrum 2009 | ancient | argument | no | BOM-116 | related only | Cannot tell yet |
| Potter 2009 | ancient | list of examples | no | BOM-116 | related only | Cannot tell yet |
| Sorenson and Johannessen 2009 | ancient | list of examples | no |  |  | Cannot tell yet |
| Perego 2010 | ancient | argument | no |  |  | Cannot tell here |
| Aston 2012 | ancient | list of examples | no |  |  | Cannot tell yet |
| Sorenson 2013 | ancient | list of examples | source to buy | BOM-111 | yes | Cannot tell yet for his list; the vocabulary does not lean Mesoamerican |
| Church essay on DNA 2014 | ancient | argument | no |  |  | Cannot tell here |
| Rappleye and Smoot 2014 | ancient | argument | no |  |  | Cannot tell yet |
| Jenkins 2015 | 19th c. | argument | no |  |  | Cannot tell yet |
| Miller and Roper 2017 | ancient | list of examples | no | BOM-113 | related only | Cannot tell yet |
| Wheat and Tares on Holley 2017 | neutral | list of examples | no | BOM-110 | yes | Holds in part |
| Dale and Dale 2019 | ancient | statistical | partly | BOM-112 | yes | Does not hold as stated |
| Rasmussen, Estimating the Evidence (series) | ancient | statistical | no |  |  | Cannot tell yet |
| Roper 2025 | ancient | list of examples | partly | BOM-113 | yes | Holds in part |
| FAIR on the Holley map | ancient | list of examples | no | BOM-110 | yes | Holds |

### Other (9)

| Study | Side | Kind | Reproduced their way? | Our test | Tested our way? | What holds |
| --- | --- | --- | --- | --- | --- | --- |
| Ostler 1987 | neutral | argument | no |  |  | Cannot tell yet |
| Ricks and Hamblin 1990 | ancient | list of examples | no | BOM-115 | yes | Cannot tell |
| Sorenson 1990 (war seasons) | ancient | statistical | no |  |  | Cannot tell yet |
| Spackman 1993 | ancient | argument | no |  |  | Cannot tell yet |
| Hess 1994 | ancient | list of examples | no |  |  | Cannot tell yet |
| Szink and Welch 1998 | ancient | list of examples | no |  |  | Cannot tell yet |
| Welch 2008 | ancient | list of examples | no |  |  | Cannot tell yet |
| Chadwick 2018 | ancient | argument | no |  |  | Cannot tell yet |
| Rasmussen ep. 5 (witnesses) | ancient | statistical | no |  |  | Cannot tell yet |

## Studies not yet touched, ranked by how testable they are with what we hold

Ranked by what a rerun needs, not by which side the study takes. The list covers studies marked
"not touched", plus "related only" studies whose own claim is untested.

**Tier 1: the text and what we already hold are enough.**

1. **Hilton 1990, the "Berkeley" wordprint.** 65 word-pattern ratios with built-in controls (26
   texts by 9 authors). The patterns are in his appendix, and the 1830 text and the controls are
   held. The obvious extra test is the lab's six two-voice writers: does Hilton's measure call
   one writer's sermon and letter two authors, as common words did in BOM-105?
2. **Kunich 1990 against Smith 1997, population growth.** Both work only from the text's own
   figures plus arithmetic or published life tables. Run both side by side and report what
   growth rate each population figure needs.
3. **3 Nephi and the Sermon on the Mount: Larson 1986, Huggins 1997, Welch 1990, Stendahl
   1978.** The KJV is held and an open Greek apparatus is available. Count where 3 Nephi follows
   the KJV against the earliest Greek text, and run the study's story-order test on Matthew's
   order (Huggins's 44 sayings).
4. **The KJV text the book quotes: Skousen 2019, Runnells (1769 errors), Townsend 2018
   (Malachi).** Skousen's rule (identical runs of 16+ words: 36 quotations, 712 differences, 163
   at italics) and Townsend's count (735 of 740 Malachi words shared with the 1769 KJV) can be
   reproduced in minutes. The library's dated KJV printings could test which edition the book
   follows.
5. **Sorenson 1990, the seasons of war.** Count the book's dated military actions by month, then
   test them against an even spread before any calendar correlation is applied.
6. **Edwards and Edwards 2010, chiasms in control texts.** Their element codings are in an open
   appendix. Recompute their P values first, then have blind readers code the same passages.
7. **Bushman 1976, Revolutionary politics absent.** Score his list of present-or-absent features
   in the Bible-style histories of the Revolution (Snowden, The Late War) and in Josephus.
8. **Carmack 2021, relative pronouns and finite "cause".** Run both across the library and the 25
   pseudo-archaic texts, and find the one text he says matches. BOM-119 already shows both
   features date books poorly (AUC 0.70 and 0.56).
9. **Davis 2012, Abinadi and Faithful.** The census has now read his list of 14 elements. Score
   each one in the Abinadi story, in Faithful's trial and in Foxe's martyrs, the control he did
   not run.
10. **Townsend 2022, Third Isaiah.** Count phrases found only in Isaiah 56-66, section by
    section, as BOM-124 did for New Testament phrases.
11. **Jockers 2013, Joseph Smith's scribes,** with the Joseph Smith Papers transcripts we hold;
    **Archer, Hilton and Schaalje 1997**, translated controls; and **"Machine Learning Redux"
    (2026)** once its code is posted (it uses Jockers's deposited data, which we hold).
12. **Lehi's dream against Joseph Smith Sr.'s dream:** the story-order test, if Lucy Mack Smith's
    history is fetched from the Joseph Smith Papers under the existing decision. **Huggins 2003:**
    date the first written "Moroni" and "Cumorah" from transcripts we hold. **Jenkins 2015:** look
    for NHM or Nehem in pre-1830 American print in the library.
13. **Hess 1994 (Jacob 5 horticulture)** against period orchard manuals, and **Szink and Welch
    1998 (festival features)** scored on a control sermon. Both are cheap, and both are weakly
    specified.
14. **Vogel 1993, anti-Universalist rhetoric:** add it to the redesigned topic-mix test
    (BOM-103).

**Tier 2: needs a purchase, or the authors' data.** Roberts 1922 parallels and Persuitte 1985
(buy the books; score each parallel against Boudinot and Adair as control books). Sorenson 2013
correspondences (buy; apply them to control texts as BOM-112 does). Matheny 1993 and Wunderli
2002 constraints (feed them to the redesigned geography test). Wunderli 2013 counts (buy).
Wilcox 2013, 2018 and 2019 name lists (ask the authors). Fields and others on voices (ask for
their word list and novels). Stubbs 2015 (buy; BOM-117). Phipps 1977 (held privately; read it
and rerun its 738-word method).

**Tier 3: outside this project's methods.** DNA (Murphy, Southerton, Meldrum and Stephens,
Whiting, Butler, Stewart, Perego, the 2014 essay, Meldrum 2009); field geography in Arabia
(Hilton and Hilton, the Astons, Potter, Brown on NHM); archaeology and paleontology (barley,
horses, metals, swords); handwriting (Cowdrey 1977); Bayesian scorecards whose likelihoods are
judgement (Rasmussen). Jordan 2003 (ice cores) could be checked with open data, but it is not a
text test.

## Sources to buy or request (to-dos)

- B. H. Roberts, *Studies of the Book of Mormon*, ed. Madsen (1985): his parallels.
- Skousen and Carmack, *The Nature of the Original Language* (2018): the 16 archaic items not
  held, and Carmack's per-feature syntax numbers. Skousen's *Analysis of Textual Variants*: the
  if-and list.
- The Skousen and Carmack 2020 pre-print ("Revisions"): its host did not resolve.
- Townsend 2025 (*Journal of the Bible and its Reception*): appendix pp. 77-83, to check the 11
  passages keyed from Jackson.
- Davis, *Visions in a Seer Stone* (2020): the "laying down heads" passages.
- Sorenson, *Mormon's Codex* (2013) and *An Ancient American Setting* (1985).
- Metcalfe, ed., *New Approaches to the Book of Mormon* (1993): Metcalfe, Matheny, Vogel,
  Ashment, Kunich expanded.
- Vogel and Metcalfe, eds., *American Apocrypha* (2002): Dunn, Murphy, Wright 2002.
- Eccel, *Mormon Genesis* (2018), pp. 351-356: normalised therefore and wherefore counts.
- Wunderli, *An Imperfect Book* (2013).
- Stubbs, *Exploring the Explanatory Power...* (2015).
- Coe, *The Maya*, the edition Dale and Dale used.
- Holley, *Book of Mormon Authorship: A Closer Look* (1983/1989): his own 29 pairs.
- Persuitte, *Joseph Smith and the Origins of the Book of Mormon* (2000 ed.).
- Requests: Hales's table of 16 texts; Fields's word list and novel set; Wilcox's name lists;
  the "Machine Learning Redux" code; Hilton III's speaker database.

## What our write-ups claim beyond the files

These came out of reading our write-ups against the result files and the web records. None
changes a number in a result file. Each is a wording problem to fix in the write-up.

1. **Dictation by ear (BOM-34, `paper/blog.md`).** The blog says the correction counts show the
   words came in by ear ("It shows the words came in by ear"), and `docs/results-inventory.md`
   says the result "agrees with Skousen". The lab rerun (BOM-127) found that 23 of the 28
   sound-alike corrections are one pair, there/their, all in Cowdery's hand. Without that pair
   the original has 5 in 720 and the copies 6 in 1,114: no difference. The study's own photo
   check had already found there/their in 23 of 30. The counts also differ between write-ups:
   30 of 590 against 5 of 837 (blog), 36 against 8 (inventory), 28 of 720 against 5 of 854
   (lab).
2. **Carmack's "did" rate (BOM-119, `paper/blog-tests.md`).** "First I reproduced his numbers.
   Book of Mormon: 19.4% (he reports 20.2%)". The 20.2% is from a Scripture Central summary. The
   2015 article's abstract says 27% of past-tense contexts, and Davis 2025 quotes 27.2%. Our
   figure matches the summary, not the article's headline. The KJV and 1832 History figures do
   reproduce. The record is marked "partly" until the definition is checked in the article.
3. **"No book matches on all ten" (BOM-119).** True as counted. But the result file's own
   known-answer check shows that only the "did" rate separates early books from late ones well
   (AUC 0.89). The other nine features score AUC 0.43 to 0.70, so matching on them says little
   about date. The blog does not say this.
4. **The voice-diversity novelists (BOM-121).** `paper/blog-tests.md` ("four novelists after
   1830") and `docs/research/2026-11-20-studies-to-rerun.md` ("all four novelists wrote after
   1830") are wrong. The four are Austen, Dickens, Cooper and Twain, and Austen and Cooper
   published before 1830. Our test's own point, plays of 1660 to 1700, stands.
5. **Schaalje 2011 in the replication summary (`paper/replication-report.md`).** The summary
   table says "yes", but the chapter counts differ (225 against 175 to an unobserved author) and
   so do the candidate texts. The body says "at the level of the conclusion". The census marks
   it "partly".
6. **Smaller points.** Our records gave Skousen's JBMS 3:1 (1994) article the title "Hebraic
   Conditionals", but that is a different piece (in *Pressing Forward*, 1999). Edwards and
   Edwards argue that design does not show ancient origin, so they are neutral, not on the
   ancient side. Grunder's catalogue first appeared on CD-ROM in 2008; our copy is the 2014 PDF.
   Holmes 1992 reads his result as consistent with a single author, so his record is now on the
   nineteenth-century side; confirm that in the paper, which we hold privately.

## Gaps in the census itself

- **The web search ran out.** All four agents hit the session's shared search limit before they
  finished. Known missing: Jonathan Neville and other Heartland and Great Lakes authors, Duane
  Aston, Phyllis Olive, Baja models, Brant Gardner, cement and elephant studies, Sorenson and
  Roper's "Before DNA", Brown's DNA article, Raff and Bolnick 2015, Dan Vogel's own Nahom
  critique, Hullinger 1980/1992, Grant Palmer 2002, Riley 1902, the Tanners' plagiarism
  compilations, Reynolds's "Nephi's Outline", Welch's later chiasmus work, MacKay and Dirkmaat
  2015, Hiatt and Hilton's voice-control studies, Croft 1981 itself, Larsen and Rencher 1982 (not
  found as a separate paper), Hauck 1988, Givens (not searched).
- **Many records rest on abstracts or secondary descriptions,** and their `todo` says so. Some
  agents' figures came from search snippets and are flagged as unverified (Rasmussen's 69, the
  Schaalje 2011 chapter counts from summaries, Wunderli's counts).
- **No person has checked any record.** Sides and kinds were assigned by AI agents and by me.
  Several are judgement calls (Holmes 1992, Kunich 1990, Ostler 1987).
- **Clusters are compressed.** The Hebraism and name literature has dozens more single-item
  notes, and the anachronism literature is represented through Roper 2025's 227 items rather
  than item by item.
- **Ordering is by topic and year, not importance.** The ranking above is the first attempt at
  importance.
