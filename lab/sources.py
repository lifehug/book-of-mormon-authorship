"""Fetch the outside sources the lab's new tests need (BOM-99, BOM-102 to BOM-108).

What each source is, where it comes from and its terms are in ``SOURCES`` below and in
``docs/research/2026-11-18-sources-for-new-tests.md``. Open material goes to
``data/corpus/lab/sources/<group>/`` (local disk, backed up, not in git); copyrighted material
(Joseph Smith Papers transcripts, papers, editors' transcriptions) to
``data/private/lab/sources/<group>/`` (the private repository). ``data/lab/sources.json`` records
every source with its address, terms, size, SHA-256 and state: names and numbers, no text.

Every fetch resumes: a file already on disk is skipped, a download is written to ``.part`` and
renamed when complete, and a failure is recorded as ``failed`` with its reason and tried again on
the next run, never stored as content. One stream, about a second between requests to a host;
josephsmithpapers.org as the owner decided on 2026-10-25 (``docs/candidates.md``), which he
confirmed for this material on 2026-11-18.

Usage::

    python -m lab.sources list              # every source: group, test, terms, state
    python -m lab.sources fetch [NAME ...]   # fetch all, or the named sources or groups
    python -m lab.sources marc               # catalog records that mark translations (HathiTrust)
    python -m lab.sources tm [--last N]      # Trismegistos People, one person a request
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ingest import jsp
from lab.paths import FAST, NOTES, REGISTRY, out

OPEN = FAST / "sources"
PRIVATE = NOTES / "sources"
RECORD = REGISTRY / "sources.json"
UA = jsp.USER_AGENT
PAUSE = 1.0
IA = "https://archive.org"
ACL = "https://aclanthology.org/"
GH = "https://github.com/"
JSPB = "https://www.josephsmithpapers.org/paper-summary/"
BMC = "https://archive.bookofmormoncentral.org/sites/default/files/"
PD = "public domain"

# (name, group, tests, kind, address, terms). Kinds: file, git, ia (Internet Archive full text),
# jsp (Joseph Smith Papers document), figshare, zenodo, links (every archive linked from a
# page), wiki.
_IA = {
    "prophets": {
        "BOM-99 BOM-105": [
            "strangeeffectsof00sout",
            "trueexplanationo00soutiala",
            "mrssouthcottswor01soutiala",
            "lifeandworksaco00soutgoog",
            "privatecommunica01wroe",
            "abridgmentofjohn00wroe",
            "abridgementofjoh01wroe",
            "ARevealedKnowledgeOfThePropheciesAndTimes",
            "journaloflifetra00scotiala",
            "journalofliferel00hick",
            "lettersofeliashi00hick",
            "testimoniesoflif00bish",
            "VoreeHerald1846",
            "GospelHerald18471850",
            "ZionsReveille18461847",
            "ancientmodernmic00stra",
            "lettersofwilliam00blak",
            "codeofhandsomela01hand",
        ],
    },
    "bible_style": {
        "BOM-102 BOM-106 BOM-107": [
            "bim_eighteenth-century_the-chronicle-of-the-kin_dodsley-robert_1741",
            "bib_fict_4103140",
            "firstbookofameri00unse",
            "americanrevoluti00snow",
            "firstbooknapole00gruagoog",
            "chroniclesoferib02ocon",
            "bookofnullificat00char",
        ],
    },
    "debates": {"BOM-103": ["millennialharbinger1831", "delusionsanalysi00camp"]},
    "names": {"BOM-108": ["americangazettee00mors"]},
    "speech": {"BOM-106": ["eighteensermonsp00whit"]},
    "rigdon": {"BOM-104": ["orationdelivered01rigd"]},
}
_JSP = {
    "ot_revision_1": "old-testament-revision-1",
    "ot_revision_2": "old-testament-revision-2",
    "visions_of_moses_1830": "visions-of-moses-june-1830-moses-1",
    "abraham_ms_a": "book-of-abraham-manuscript-circa-july-circa-november-1835-a-abraham-14-26",
    "abraham_ms_b": "book-of-abraham-manuscript-circa-july-circa-november-1835-b-abraham-14-22",
    "abraham_ms_c": "book-of-abraham-manuscript-circa-july-circa-november-1835-c-abraham-11-218",
    "abraham_1842": "book-of-abraham-and-facsimiles-1-march-16-may-1842",
    "rigdon_oration_1838": "appendix-3-discourse-circa-4-july-1838",
    "rigdon_appeal_1840": "sidney-rigdon-appeal-to-the-american-people-1840",
}
_PAPERS = {
    "BOM-102": {
        "koppel_ordan_2011.pdf": ACL + "P11-1132.pdf",
        "rabinovich_wintner_2015.pdf": ACL + "Q15-1030.pdf",
        "rabinovich_ordan_wintner_2017.pdf": ACL + "P17-1049.pdf",
        "pylypenko_2021.pdf": ACL + "2021.emnlp-main.676.pdf",
        "amponsah_kaakyire_2022.pdf": "https://arxiv.org/pdf/2210.13391",
        "tvedtnes_1991.pdf": BMC + "archive-files/pdf/tvedtnes/2017-08-02/"
        "08_john_a._tvedtnes_the_hebrew_background_of_the_book_of_mormon_1991.pdf",
        "tvedtnes_1970.pdf": BMC
        + "John%20A.%20Tvedtnes%2C%20Hebraisms%20in%20the%20Book%20of%20Mormon%2C%201970.pdf",
        "echoes_and_evidences_2002.pdf": BMC
        + "archive-files/pdf/parry/2019-09-18/echoes_and_evidences_of_the_book_of_mormon.pdf",
    },
    "BOM-103": {
        "hamilton_2016.pdf": ACL + "P16-1141.pdf",
        "niculae_2014.pdf": ACL + "E14-4004.pdf",
        "popescu_strapparava_2015.pdf": ACL + "S15-2147.pdf",
    },
    "BOM-105": {
        "holmes_1992.pdf": "https://www.physics.smu.edu/pseudo/ScienceReligion/"
        "MormonStylometric.pdf",
    },
    "BOM-107": {
        "dubremetz_nivre_2015.pdf": ACL + "W15-0703.pdf",
        "dubremetz_nivre_2017.pdf": ACL + "W17-0205.pdf",
        "schneider_2021.pdf": ACL + "2021.latechclfl-1.11.pdf",
        "figures_survey_2024.pdf": "https://arxiv.org/pdf/2406.16674",
    },
}
_RIGDON = {
    "index.htm": "http://sidneyrigdon.com/RigWrit1.htm",
    "millennium_1833_35.htm": "http://www.SidneyRigdon.com/RigWrit/RigWrit3.htm",
    "gospel_1833_35.htm": "http://www.SidneyRigdon.com/RigWrit/RigWrit3b.htm",
    "misc_1834_38.htm": "http://www.SidneyRigdon.com/RigWrit/RigWrit3d.htm",
}
# BOM-104 "their way first": the 1832-36 church papers' issues that carry the Phipps (1977) and
# Reynolds (2005) samples, in the centerplace.org transcription (one page an issue). The held OCR
# of the same runs interleaves columns, which breaks the phrases Reynolds counted.
_CP = "http://centerplace.org/history/"
_PAPERS_1830S = {
    f"{paper}_{issue}.htm": f"{_CP}{paper}/{issue}.htm"
    for paper, issues in {
        "ems": ["v1n01", "v2n17", "v2n19", "v2n20", "v2n21", "v2n22", "v2n23", "v2n24"],
        "ma": ["v1n01", "v1n02", "v1n03", "v1n04", "v1n05", "v1n06", "v1n07", "v1n08", "v1n09",
               "v1n10", "v1n11", "v1n12", "v2n01", "v2n02", "v2n03", "v2n07", "v2n10"],
    }.items()
    for issue in issues
}  # fmt: skip
_GIT = {
    "wordtree_books": (
        "bible_style",
        "BOM-102 BOM-106 BOM-107",
        "wordtreefoundation/books",
        "no licence stated; transcriptions of public-domain books",
    ),
    "bible_data": ("names", "BOM-108", "BradyStephenson/bible-data", "CC BY 4.0"),
    "bible_geocoding": ("names", "BOM-108", "openbibleinfo/Bible-Geocoding-Data", "CC BY 4.0"),
    "theographic": ("names", "BOM-108", "robertrouse/theographic-bible-metadata", "CC BY-SA 4.0"),
    "chiasmus_detector_dubremetz": (
        "chiasmus",
        "BOM-107",
        "mardub1635/chiasmusDetector",
        "GPL-3.0 (code)",
    ),
    "chiasmus_detector_schneider": (
        "chiasmus",
        "BOM-107",
        "cvjena/chiasmus-detector",
        "no licence stated (code)",
    ),
}
# Evans TCP texts whose titles say they were taken in short-hand (hand-keyed, free).
_TCP = ["N25065", "N09159", "N27848", "N27958", "N28782", "N08994", "N15885", "N24754"]

# Name lists for BOM-108, located 2026-11-19 (docs/research/2026-11-19-name-lists-for-bom-108.md).
# name: (kind, address, terms)
PG = "https://aleph.pglaf.org/"  # Project Gutenberg's mirror
TLA = "https://huggingface.co/datasets/thesaurus-linguae-aegyptiae/"
DAHPN = (
    "https://www.dahpn.gwi.uni-muenchen.de/wp-content/themes/bootscore-5-child/api/index.php/"
    "getData?db=261&column="
)
GNIS = "https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/DomesticNames/"
_NAMES = {
    "dahpn_epigraphic.json": ("file", DAHPN + "2", "CC BY-SA 4.0; doi:10.24344/bht-dahpn"),
    "dahpn_all.json": ("file", DAHPN + "0", "CC BY-SA 4.0; doi:10.24344/bht-dahpn"),
    "golub_onomasticon_2025-04.json": (
        "file",
        "https://www.onomasticon.net/assets/data/data-2025-04.json",
        "CC BY-NC-SA",
    ),
    "oracc_ctij_names.html": (
        "file",
        "https://oracc.museum.upenn.edu/ctij/cbd/qpn/onebigfile.html",
        "CC BY-SA 3.0",
    ),
    "prosobab": ("zenodo", "https://zenodo.org/api/records/17244668", "CC BY-NC 4.0"),
    "hatra_names_marcato": ("zenodo", "https://zenodo.org/api/records/21391494", "CC BY 4.0"),
    "iip_texts": ("git", GH + "Brown-University-Library/iip-texts", "CC BY-NC 4.0"),
    "ociana.xml": (
        "file",
        "https://ora.ox.ac.uk/objects/uuid:08a60ae8-e61d-486e-9ef1-836ca71d904c/files/"
        "mc562d7869379fa3570db57cd9ed0c28c",
        "Oxford University Research Archive terms",
    ),
    "pnm_middle_kingdom": ("zenodo", "https://zenodo.org/api/records/15806808", "CC BY 4.0"),
    "aed_tei": ("git", GH + "simondschweitzer/aed-tei", "CC BY-SA 4.0"),
    "tla_demotic.jsonl": (
        "file",
        TLA + "tla-demotic-v18-premium/resolve/main/train.jsonl",
        "CC BY-SA 4.0",
    ),
    "tla_late_egyptian.jsonl": (
        "file",
        TLA + "tla-late_egyptian-v19-premium/resolve/main/train.jsonl",
        "CC BY-SA 4.0",
    ),
    "tla_earlier_egyptian.jsonl": (
        "file",
        TLA + "tla-Earlier_Egyptian_original-v18-premium/resolve/main/train.jsonl",
        "CC BY-SA 4.0",
    ),
    "hasitzka_coptic_names.pdf": (
        "file",
        "http://web.archive.org/web/20160214175224id_/http://www.onb.ac.at/files/kopt_namen.pdf",
        "no licence stated; made available by the author through the Austrian National Library",
    ),
    "epsd2_names.zip": ("file", "https://oracc.museum.upenn.edu/json/epsd2-names.zip", "CC0"),
    "gnis_new_york.zip": ("file", GNIS + "DomesticNames_NY_Text.zip", "US government work"),
    "gnis_national.zip": ("file", GNIS + "DomesticNames_National_Text.zip", "US government work"),
    "apocrypha_kjv.txt": ("file", PG + "1/2/124/124-0.txt", PD),
    "josephus_antiquities_whiston.txt": ("file", PG + "2/8/4/2848/2848-0.txt", PD),
    "josephus_wars_whiston.txt": ("file", PG + "2/8/5/2850/2850.txt", PD),
    "koran_sale.txt": ("file", PG + "7/4/4/7440/7440.txt", PD),
    "arabian_nights_scott.txt": ("file", PG + "5/6/6/5668/5668.txt", PD),
    "morgan_freemasonry.txt": ("file", PG + "1/8/1/3/18136/18136.txt", PD),
    "swift_gulliver.txt": ("file", PG + "8/2/829/829-0.txt", PD),
    "spenser_faerie_queene_1.txt": ("file", PG + "6/9/3/6930/6930.txt", PD),
    "ossian_fragments_1760.txt": ("file", PG + "8/1/6/8161/8161.txt", PD),
}
# Internet Archive scans for the same test: period name dictionaries, native place names,
# single-author invented names, and the twelve volumes of the 1790 census.
_NAMES_IA = [
    "akeytoclassical01walkgoog",
    "classicaldiction00lemp",
    "aboriginalplacen00beau",
    "indiannamesofpla00trumiala",
    "themanuscriptsto00spauuoft",
    "poemsofossiantra10macp",
    "poemsofossiantra11macp",
    "lightonmasonrya00berngoog",
    "centuryofpopulat00unit",
    *[f"headsoffamiliesa{n:02d}unit" for n in range(1, 13)],
]
_NAMES_PAPERS = {
    "wilcox2013_phonoprints.pdf": "https://ans-names.pitt.edu/ans/article/download/1980/1979/3980",
    "wilcox2019_phonemic_patterns.pdf": BMC
    + "archive-files/pdf/wilcox/2019-08-12/brad_wilcox_et_al_comparing_phonemic_patterns_2019.pdf",
}

# The book's setting (BOM-109 to BOM-117) and Native American names (BOM-108, BOM-110), located
# 2026-11-20 (docs/research/2026-11-20-the-books-setting.md). Books the library already holds
# (Clavigero, del Rio, Juarros, Atwater, Boudinot, Spafford ...) are not fetched again.
WP = "https://en.wikipedia.org/w/api.php?action=parse&prop=wikitext&format=json&page="
WKT = "https://en.wiktionary.org/w/api.php#Category:"
GEO = "https://download.geonames.org/export/dump/"
GLYPHS = (
    "https://aztecglyphs.wired-humanities.org/advsearch-all-grid"
    "?field_semantic_categories_new_ta_tid={tid}&page={{n}}|{pages}"
)
SETTING = "BOM-109 BOM-111 BOM-112 BOM-114 BOM-115"
_SETTING = {  # name: (group, tests, kind, address, terms)
    "brinton_maya_chronicles_1882.txt": (
        "setting",
        SETTING,
        "file",
        PG + "2/0/2/0/20205/20205-0.txt",
        PD,
    ),
    "brinton_annals_cakchiquels_1885.txt": (
        "setting",
        SETTING,
        "file",
        PG + "2/0/7/7/20775/20775-0.txt",
        PD,
    ),
    "brinton_rig_veda_americanus_1890.txt": (
        "setting",
        SETTING,
        "file",
        PG + "1/4/9/9/14993/14993.txt",
        PD,
    ),
    "brinton_nahuatl_poetry_1887.txt": (
        "setting",
        SETTING,
        "file",
        PG + "1/2/2/1/12219/12219-0.txt",
        PD,
    ),
    "popol_vuh_spence_1908.txt": (
        "setting",
        SETTING,
        "file",
        PG + "5/6/5/5/56550/56550-8.txt",
        PD + "; a summary",
    ),
    "adair_1775_williams_ed.txt": (
        "setting",
        SETTING,
        "file",
        PG + "6/7/6/9/67699/67699-0.txt",
        PD,
    ),
    "geonames_US.zip": ("places", "BOM-110 BOM-116", "file", GEO + "US.zip", "CC BY 4.0"),
    "geonames_MX.zip": ("places", "BOM-110 BOM-116", "file", GEO + "MX.zip", "CC BY 4.0"),
    "geonames_GT.zip": ("places", "BOM-110 BOM-116", "file", GEO + "GT.zip", "CC BY 4.0"),
    "geonames_allCountries.zip": (
        "places",
        "BOM-110 BOM-116",
        "file",
        GEO + "allCountries.zip",
        "CC BY 4.0",
    ),
    "geonames_featureCodes_en.txt": (
        "places",
        "BOM-110 BOM-116",
        "file",
        GEO + "featureCodes_en.txt",
        "CC BY 4.0",
    ),
    "asjp_v21": (
        "wordlists",
        "BOM-117",
        "zenodo",
        "https://zenodo.org/api/records/16736409",
        "CC BY 4.0",
    ),
    "lexibank_wichmannmixezoquean": (
        "wordlists",
        "BOM-117",
        "git",
        GH + "lexibank/wichmannmixezoquean",
        "CC BY 4.0",
    ),
    "lexibank_davletshinaztecan": (
        "wordlists",
        "BOM-117",
        "git",
        GH + "lexibank/davletshinaztecan",
        "CC BY 4.0",
    ),
    "lexibank_utoaztecan": ("wordlists", "BOM-117", "git", GH + "lexibank/utoaztecan", "CC BY 4.0"),
    "lexibank_felekesemitic": (
        "wordlists",
        "BOM-117",
        "git",
        GH + "lexibank/felekesemitic",
        "CC BY 4.0",
    ),
    "wp_anachronisms.json": (
        "setting",
        "BOM-111 BOM-113",
        "file",
        WP + "Anachronisms_in_the_Book_of_Mormon",
        "CC BY-SA",
    ),
    "wp_bom_places.json": (
        "setting",
        "BOM-110 BOM-116",
        "file",
        WP + "List_of_Book_of_Mormon_places",
        "CC BY-SA",
    ),
    "wp_bom_people.json": (
        "setting",
        "BOM-108",
        "file",
        WP + "List_of_people_in_the_Book_of_Mormon",
        "CC BY-SA",
    ),
    "wp_mesoamerica_plants.json": (
        "setting",
        "BOM-111",
        "file",
        WP + "Domesticated_plants_of_Mesoamerica",
        "CC BY-SA",
    ),
    "wp_new_world_crops.json": ("setting", "BOM-111", "file", WP + "New_World_crops", "CC BY-SA"),
    "wp_mesoamerica_metallurgy.json": (
        "setting",
        "BOM-111",
        "file",
        WP + "Metallurgy_in_pre-Columbian_Mesoamerica",
        "CC BY-SA",
    ),
    "wp_columbian_exchange.json": (
        "setting",
        "BOM-111",
        "file",
        WP + "Columbian_exchange",
        "CC BY-SA",
    ),
    "wp_domesticated_animals.json": (
        "setting",
        "BOM-111",
        "file",
        WP + "List_of_domesticated_animals",
        "CC BY-SA",
    ),
    "wp_maya_monarchs.json": ("native_names", "BOM-108", "file", WP + "Maya_monarchs", "CC BY-SA"),
    "wp_sapa_inca.json": ("native_names", "BOM-108", "file", WP + "Sapa_Inca", "CC BY-SA"),
    "wkt_classical_nahuatl.json": (
        "native_names",
        "BOM-108",
        "wiki",
        WKT + "Classical_Nahuatl_proper_nouns",
        "CC BY-SA",
    ),
    "wkt_central_nahuatl.json": (
        "native_names",
        "BOM-108",
        "wiki",
        WKT + "Central_Nahuatl_proper_nouns",
        "CC BY-SA",
    ),
    "wkt_quechua.json": (
        "native_names",
        "BOM-108",
        "wiki",
        WKT + "Quechua_proper_nouns",
        "CC BY-SA",
    ),
    "wkt_yucatec_maya.json": (
        "native_names",
        "BOM-108",
        "wiki",
        WKT + "Yucatec_Maya_proper_nouns",
        "CC BY-SA",
    ),
    "morelos_census_names_hansen.html": (
        "native_names",
        "BOM-108",
        "file",
        "https://nahuatlstudies.blogspot.com/2014/11/nahuatl-names-nahuatl-names-in-1544.html",
        "no licence stated; a list of names",
    ),
    "aztec_glyphs_personal": (
        "native_names",
        "BOM-108",
        "pages",
        GLYPHS.format(tid=129, pages=101),
        "CC BY-NC-SA 3.0",
    ),
    "aztec_glyphs_places": (
        "native_names",
        "BOM-108 BOM-110",
        "pages",
        GLYPHS.format(tid=128, pages=29),
        "CC BY-NC-SA 3.0",
    ),
    "treaties_okstate": (
        "native_names",
        "BOM-108",
        "sitemap",
        "https://treaties.okstate.edu/search/site-map.xml#/treaties/",
        "no licence stated; texts of US treaties (public domain)",
    ),
}
_SETTING_IA = {
    "setting": (
        SETTING,
        [
            "historyofamerica01roberich",
            "historyofamerica02roberich",
            "researchesconcer01humb",
            "researchesconcer02humb",
            "truehistoryofcon00dauoft",
            "historyofconques00sols",
            "naturalmoralhist60acosrich",
            "naturalmoralhist61acosrich",
            "historyofamerica00adairich",
            "wondersnaturean00priegoog",
            "americanantiquit01prie",
            "discoursedel00clinton",
            "westernpartsstate00clinrich",
            "Ayer_251_I611_C9_1827",
            "geniusofoblivion00hale",
            "behemothlegend00mathrich",
            "manuscriptfoundo00spau",
            "drakechiefsbio00drakrich",
            "narrativeoflifeo00seav",
        ],
    ),
    "places": (
        "BOM-110",
        [
            "geographicaldict01worc",
            "geographicaldict02worc",
            "geographdictionary00morsrich",
            "newuniversalgaze00morsrich",
        ],
    ),
    "native_names": (
        "BOM-108 BOM-110",
        [
            "pen-afiel-nombres-geograficos-de-mexico",
            "guaman-poma-de-ayala-felipe.-nueva-coronica.-tomo-i-ocr-1980",
            "vocabulariodelal01gonz",
            "treatiesbetweenu00unit_0",
            "handbookamindians01hodgrich",
            "handbookamindians02hodgrich",
            "leagueofhodnos00inmorg",
            "indiannamesinnew00beau",
            "footprintsofredm00rutt",
            "nameswhichlennil00heck",
        ],
    ),
}


# Long texts dictated, spoken or claimed as received, and their controls, for BOM-125 (located
# 2026-11-21; Project Gutenberg catalogue and Internet Archive search). Printed before 1930, so
# public domain in the United States. name: (kind, address)
def _pg(i: int, suffix: str) -> str:
    digits = str(i)
    return f"{PG}{'/'.join(digits[:-1]) if len(digits) > 1 else '0'}/{digits}/{digits}{suffix}"


_RECEIVED = {
    "milton_paradise_lost.txt": ("file", _pg(26, "-0.txt")),
    "swedenborg_heaven_and_hell.txt": ("file", _pg(17368, ".txt")),
    "swedenborg_divine_love_wisdom.txt": ("file", _pg(16627, ".txt")),
    "swedenborg_divine_providence.txt": ("file", _pg(18507, ".txt")),
    "swedenborg_conjugial_love.txt": ("file", _pg(11248, "-0.txt")),
    "swedenborg_earths_in_the_universe.txt": ("file", _pg(16044, ".txt")),
    "aquarian_gospel_levi_1908.txt": ("file", _pg(44073, "-0.txt")),
    "eddy_science_and_health.txt": ("file", _pg(3458, ".txt")),
    "horn_strange_visitors_1869.txt": ("file", _pg(13237, "-0.txt")),
    "james_ambassadors.txt": ("file", _pg(432, "-0.txt")),
    "james_golden_bowl.txt": ("file", _pg(4264, "-0.txt")),
    "james_wings_of_the_dove_1.txt": ("file", _pg(29452, ".txt")),
    "james_wings_of_the_dove_2.txt": ("file", _pg(30059, "-0.txt")),
    "scott_bride_of_lammermoor.txt": ("file", _pg(471, "-0.txt")),
    "gibbon_decline_and_fall_1.txt": ("file", _pg(731, "-0.txt")),
    "mcguffey_first_reader.txt": ("file", _pg(14640, "-0.txt")),
    "mcguffey_second_reader.txt": ("file", _pg(14668, "-0.txt")),
    "mcguffey_third_reader.txt": ("file", _pg(14766, "-0.txt")),
    "mcguffey_fourth_reader.txt": ("file", _pg(14880, ".txt")),
    "mcguffey_fifth_reader.txt": ("file", _pg(15040, "-0.txt")),
    "mcguffey_sixth_reader.txt": ("file", _pg(16751, ".txt")),
    "oahspe0001john": ("ia", f"{IA}/details/oahspe0001john"),
    "principlesofnatu00davi": ("ia", f"{IA}/details/principlesofnatu00davi"),
    "spiritteachings00moseiala": ("ia", f"{IA}/details/spiritteachings00moseiala"),
    "sorrytaleastory00currgoog": ("ia", f"{IA}/details/sorrytaleastory00currgoog"),
    "hopetrueblood00wort": ("ia", f"{IA}/details/hopetrueblood00wort"),
}


def _sources() -> list[dict]:
    rows = []

    def add(name, group, tests, kind, url, terms, private=False):
        rows.append(
            {
                "name": name,
                "group": group,
                "tests": tests,
                "kind": kind,
                "url": url,
                "terms": terms,
                "private": private,
            }
        )

    for group, by_test in _IA.items():
        for tests, items in by_test.items():
            for item in items:
                add(item, group, tests, "ia", f"{IA}/details/{item}", PD + " (scan and OCR text)")
    for name, slug in _JSP.items():
        group = "rigdon" if name.startswith("rigdon") else "dictated"
        add(
            name,
            group,
            "BOM-104",
            "jsp",
            JSPB + slug + "/1",
            "copyright Intellectual Reserve; private, not redistributed",
            True,
        )
    for tests, papers in _PAPERS.items():
        for name, url in papers.items():
            add(name, "papers", tests, "file", url, "copyright the authors; private copy", True)
    for name, url in _RIGDON.items():
        add(
            name,
            "rigdon",
            "BOM-104",
            "file",
            url,
            "public-domain texts in an editor's transcription with his notes; private",
            True,
        )
    for name, url in _PAPERS_1830S.items():
        add(
            name,
            "church_papers",
            "BOM-104",
            "file",
            url,
            "public-domain newspapers (1832-36) in the centerplace.org transcription; private",
            True,
        )
    for name, (group, tests, repo, terms) in _GIT.items():
        add(name, group, tests, "git", GH + repo, terms)
    for tcp in _TCP:
        add(
            tcp + ".xml",
            "speech",
            "BOM-106",
            "file",
            f"https://raw.githubusercontent.com/textcreationpartnership/{tcp}/master/{tcp}.xml",
            "Text Creation Partnership, free",
        )
    add(
        "oldbailey_online_xml",
        "speech",
        "BOM-106",
        "figshare",
        "https://api.figshare.com/v2/articles/4775434",
        "CC BY-NC 4.0",
    )
    add(
        "oldbailey_corpus_2",
        "speech",
        "BOM-106",
        "links",
        "https://fedora.clarin-d.uni-saarland.de/oldbailey/downloads.html",
        "CC BY-NC-SA 4.0",
    )
    add(
        "turner_confessions_1831.html",
        "prophets",
        "BOM-99 BOM-105",
        "file",
        "https://docsouth.unc.edu/neh/turner/turner.html",
        PD + " text; DocSouth edition",
    )
    add(
        "pnao.zip",
        "names",
        "BOM-108",
        "file",
        "https://oracc.museum.upenn.edu/json/pnao.zip",
        "CC BY-SA 3.0",
    )
    add(
        "onomasticon_names.json",
        "names",
        "BOM-108",
        "wiki",
        "https://onoma.lib.byu.edu/api.php",
        "no licence stated; a list of names only",
    )
    for name, (kind, url, terms) in _NAMES.items():
        add(name, "names", "BOM-108", kind, url, terms)
    for item in _NAMES_IA:
        add(item, "names", "BOM-108", "ia", f"{IA}/details/{item}", PD + " (scan and OCR text)")
    for name, (group, tests, kind, url, terms) in _SETTING.items():
        add(name, group, tests, kind, url, terms)
    for group, (tests, items) in _SETTING_IA.items():
        for item in items:
            add(item, group, tests, "ia", f"{IA}/details/{item}", PD + " (scan and OCR text)")
    add(
        "popol_vuh_christenson_2007.pdf",
        "setting",
        SETTING,
        "file",
        "https://www.mesoweb.com/publications/Christenson/PopolVuh.pdf",
        "copyright the translator; free to read; private copy for analysis",
        True,
    )
    # BOM-102 second design (docs/research/2026-11-22-redesign-translation.md).
    for name, kind, url, terms in (
        ("morphhb", "git", GH + "openscriptures/morphhb",
         "CC BY 4.0 (Open Scriptures Hebrew Bible: WLC text, lemma, morphology)"),
        ("ylt_txt.tar", "file", f"{IA}/download/ylt_20220401/YLT_txt.tar",
         PD + " (Young's Literal Translation; digital text from bible4u.net, likely the 1898 "
         "revision, not the 1862 first edition)"),
        ("bookofjasherrefe00sefe", "ia", f"{IA}/details/bookofjasherrefe00sefe",
         PD + " (scan and OCR text; Noah and Gould, New York 1840)"),
        *[(f"holybiblecontain0{v}thom", "ia", f"{IA}/details/holybiblecontain0{v}thom",
           PD + " (scan and OCR text; Thomson 1808, from the Septuagint)") for v in (1, 2, 3, 4)],
        ("bom_gutenberg_versified.txt", "file", _pg(17, "-0.txt"),
         PD + "; Project Gutenberg #17 (modern chapters and verses: a lookup index only)"),
    ):  # fmt: skip
        add(name, "translation", "BOM-102", kind, url, terms)
    # BOM-132: the King James text of 1769 with Strong's numbers on each word (USFM, strong=).
    add("eng-kjv2006_usfm.zip", "translation", "BOM-132", "file",
        "https://ebible.org/Scriptures/eng-kjv2006_usfm.zip",
        PD + " (eBible.org, King James 1769 text, protocanon, Strong's numbers)")  # fmt: skip
    # BOM-133: translators from Hebrew (docs/research/2026-11-27-hebrew-parents.md, section 4).
    # Bellamy 1818 is on Google Books only, which answers programs with a bot check: not fetched.
    for item, kind, what in (
        ("bim_eighteenth-century_isaiah-a-new-translatio_1778", "ia", "Lowth, Isaiah, 1778"),
        ("ENGNFB_DBS_HS", "ia_all", "Boothroyd, A New Family Bible, 1824, vols 1-3"),
        ("cu31924029268617", "ia", "Boothroyd's version, one-volume reprint, 1853"),
        ("twentyfourbookso1853lees", "ia", "Leeser, The Twenty-Four Books, 1853"),
        ("hebrewscriptures00shar", "ia", "Sharpe, The Hebrew Scriptures, 1865"),
        ("holybiblecon00smit", "ia", "Julia E. Smith, The Holy Bible, 1876"),
        ("bim_eighteenth-century_miscellaneous-discourses_wotton-william_1718_1", "ia",
         "Wotton, Miscellaneous Discourses (Mishnah tracts), 1718, vol. 1"),
        ("bim_eighteenth-century_miscellaneous-discourses_wotton-william_1718_2", "ia",
         "Wotton, Miscellaneous Discourses (Mishnah tracts), 1718, vol. 2"),
        ("mainprinciplesof00maim", "ia", "Bernard, Maimonides' Creed and Ethics, 1832"),
        ("bim_eighteenth-century_prayers-for-shabbath-ro_1766", "ia",
         "Pinto (attributed), Prayers for Shabbath, Rosh-Hashanah, and Kippur, 1766"),
    ):  # fmt: skip
        add(item, "translation", "BOM-133", kind, f"{IA}/details/{item}",
            PD + f" (scan and OCR text; {what})")  # fmt: skip
    for name, url in (
        ("fair_if_and_conditionals.html", "https://www.fairlatterdaysaints.org/answers/"
         "Book_of_Mormon/Evidences/Hebraisms/If-and_conditionals"),
        ("rsc_conditional_clauses.html", "https://rsc.byu.edu/preserved-translation/"
         "conditional-clauses"),
    ):  # fmt: skip
        add(name, "papers", "BOM-102", "file", url, "copyright the authors; private copy", True)
    add(
        "jackson2025_reply_to_townsend.pdf",
        "papers",
        "BOM-122",
        "file",
        "https://cdn.interpreterfoundation.org/jnlpdf/jackson-v66-2025-131-150-PDF.pdf",
        "copyright the author; open access; private copy",
        True,
    )
    interpreter = "https://cdn.interpreterfoundation.org/jnlpdf/"
    for name, url in {
        "carmack2015_past_tense_syntax.pdf": "carmack-v14-2015-pp119-186-PDF.pdf",
        "carmack2017_1832_history.pdf": "carmack-v25-2017-pp239-259-PDF.pdf",
        "carmack2018_pseudo_archaic.pdf": "carmack-v28-2018-pp177-232-PDF.pdf",
    }.items():
        terms = "copyright the author; open access; private copy"
        add(name, "papers", "BOM-119", "file", interpreter + url, terms, True)
    add("roper2025_anachronisms.pdf", "papers", "BOM-113", "file",
        interpreter + "roper-v65-2025-1-8-PDF.pdf",
        "copyright the author; open access (CC BY-NC-ND); private copy", True)  # fmt: skip
    for ch, pages in enumerate(("9-50", "51-92", "93-112", "113-152", "153-180", "181-202",
                                "203-222", "223-238", "239-280"), 1):  # fmt: skip
        add(f"roper2025_anachronisms_ch{ch}.pdf", "papers", "BOM-113", "file",
            interpreter + f"roper-v65-2025-{pages}-PDF.pdf",
            "copyright the author; open access (CC BY-NC-ND); private copy", True)  # fmt: skip
    for name, url in _NAMES_PAPERS.items():
        add(name, "papers", "BOM-108", "file", url, "copyright the authors; private copy", True)
    for name, (kind, url) in _RECEIVED.items():
        terms = PD + (" (scan and OCR text)" if kind == "ia" else "; Project Gutenberg")
        add(name, "received", "BOM-125", kind, url, terms)
    add("urantia_book_1955_v1.22_txt.zip", "received", "BOM-125", "file",
        "https://www.urantia.org/sites/default/files/book/en/uf-eng-001-1955-1.22-txt.zip",
        "Urantia Foundation, offered free; the US copyright was held invalid (Michael Foundation, "
        "2001); local copy only, not redistributed (owner's yes, 2026-11-23)")  # fmt: skip
    # BOM-117 redesign (docs/research/2026-11-22-redesign-uto-aztecan.md): open word lists and
    # lexicons, and Stubbs 2015, free for non-commercial private use (owner, 2026-11-22).
    raw = "https://raw.githubusercontent.com/"
    for name, kind, url, terms in (
        ("lexibank_wold", "git", GH + "lexibank/wold", "CC BY 4.0"),
        ("lexibank_northeuralex", "git", GH + "lexibank/northeuralex", "CC BY 4.0"),
        ("hebrew_lexicon", "git", GH + "openscriptures/HebrewLexicon",
         "CC BY 4.0 (files); BDB and Strong's text public domain"),
        ("coptic_lexicon_v1.2_2020.xml", "file",
         raw + "KELLIA/dictionary/master/xml/Comprehensive_Coptic_Lexicon-v1.2-2020.xml",
         "CC BY-SA 4.0 (BBAW / Coptic SCRIPTORIUM, doi:10.17169/refubium-2333)"),
        ("clics3_network.gml.zip", "file", raw + "clics/clics3/master/clics3-network.gml.zip",
         "CC BY 4.0"),
    ):  # fmt: skip
        add(name, "wordlists", "BOM-117", kind, url, terms)
    # BOM-109: Kirchhoff's 1943 essay, 1960 Tlatoani reprint, as posted by UNAM's CCH portal
    add("kirchhoff1943_mesoamerica_tlatoani1960.pdf", "kirchhoff", "BOM-109", "file",
        "https://portalacademico.cch.unam.mx/materiales/al/cont/hist/mex/mex1/histMexU2OA01/"
        "docs/paulKirchhoff_mesoamerica.pdf",
        "copyright the author's estate (Kirchhoff d. 1972); posted free by UNAM for teaching; "
        "private copy, never redistributed", True)  # fmt: skip
    # BOM-109: copyright-renewal check for Roys's Chumayel (1933) and other 1926-1963 sources
    add(
        "stanford_copyright_renewals_20170427.csv.zip",
        "copyright",
        "BOM-109",
        "file",
        "https://web.stanford.edu/dept/SUL/collections/copyrightrenewals/files/"
        "20170427-copyright-renewals-records.csv.zip",
        "Stanford University Libraries; offered for reuse (Copyright Renewal Database page)",
    )
    add("sorenson2000_mormons_map.pdf", "sorenson", "BOM-116", "file",
        "https://storage.googleapis.com/scripturecentral-prod-strapi-uploads/"
        "john_l_sorenson_mormons_map_2000_3cfee21d8b/john_l_sorenson_mormons_map_2000_3cfee21d8b.pdf",
        "copyright FARMS / the author; posted free on the Scripture Central archive for "
        "non-commercial, private use; private copy, never redistributed", True)  # fmt: skip
    add("stubbs2015_exploring.pdf", "stubbs", "BOM-117", "file",
        "https://storage.googleapis.com/scripturecentral-prod-strapi-uploads/"
        "er_of_semitic_and_egyptian_in_uto_aztecan_2015_0b7be82eba/"
        "er_of_semitic_and_egyptian_in_uto_aztecan_2015_0b7be82eba.pdf",
        "copyright the author; posted free on the Book of Mormon Central archive for "
        "non-commercial, private use; private copy, never redistributed", True)  # fmt: skip
    # BOM-116 second design (docs/research/2026-11-22-redesign-geography.md): open physical data,
    # radiocarbon dates, Clark's key (private copy) and four later invented-land novels.
    # HydroRIVERS is not fetched: its HydroSHEDS v1 licence forbids redistribution as a
    # stand-alone product, so it is not open; river direction comes from relief instead.
    ne = raw + "nvkelso/natural-earth-vector/master/geojson/"
    zen = "https://zenodo.org/api/records/"
    g116 = "BOM-116"
    for name, group, kind, url, terms in (
        *[(f"{f}.geojson", "physical", "file", ne + f"{f}.geojson",
           PD + " (Natural Earth 1:10m, v5)")
          for f in ("ne_10m_land", "ne_10m_lakes", "ne_10m_rivers_lake_centerlines",
                    "ne_10m_coastline")],
        ("ETOPO_2022_v1_60s_N90W180_surface.tif", "physical", "file",
         "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/60s_surface_elev_gtif/"
         "ETOPO_2022_v1_60s_N90W180_surface.tif",
         PD + " (NOAA NCEI, US government work; cite doi:10.25921/fd45-gt74)"),
        ("age_2021_coastline_age", "physical", "figshare",
         "https://api.figshare.com/v2/articles/20029304",
         "CC BY 4.0 (De Groeve and others 2022, University of Amsterdam, AGE 2021)"),
        ("pleiades-places-latest.csv.gz", "physical", "file",
         "https://atlantides.org/downloads/pleiades/dumps/pleiades-places-latest.csv.gz",
         "CC BY 3.0 (Pleiades gazetteer)"),
        ("p3k14c", "radiocarbon", "zenodo", zen + "5597795",
         "open (data CC0 per Bird and others 2022, Scientific Data; code MIT)"),
        ("nerd_v6", "radiocarbon", "zenodo", zen + "7107507",
         "CC BY 4.0 (NERD, Near East Radiocarbon Dates, Palmisano and others)"),
        ("palmisano_2021", "radiocarbon", "zenodo", zen + "4322979",
         "CC BY 4.0 (Palmisano and others 2021, Quaternary Science Reviews 252)"),
        ("intcal20.14c", "radiocarbon", "file", "https://intcal.org/curves/intcal20.14c",
         "open (IntCal20 calibration curve, Reimer and others 2020)"),
        ("verne_mysterious_island.txt", "geography2", "file", _pg(1268, "-0.txt"), PD),
        ("baum_wonderful_wizard_of_oz.txt", "geography2", "file", _pg(55, "-0.txt"), PD),
        ("baum_marvelous_land_of_oz.txt", "geography2", "file", _pg(54, "-0.txt"), PD),
        ("burroughs_princess_of_mars.txt", "geography2", "file", _pg(62, "-0.txt"), PD),
        ("defoe_captain_singleton.txt", "geography2", "file", _pg(6422, ".txt"), PD),
        ("wp_bom_hypothetical_setting.json", "setting", "file",
         WP + "Hypothetical_setting_of_the_Book_of_Mormon", "CC BY-SA"),
    ):  # fmt: skip
        add(name, group, g116, kind, url, terms)
    # BYU ScholarsArchive refuses programs (403); Scripture Central serves the full text as a page.
    sc = "https://scripturecentral.org/archive/periodicals/journal-article/"
    for name, slug in (("clark1989_key.html", "key-evaluating-nephite-geographies"),
                       ("clark2011_revisiting_key.html",
                        "revisiting-key-evaluating-nephite-geographies")):  # fmt: skip
        add(name, "papers", g116, "file", sc + slug,
            "copyright the author; free to read; private copy", True)  # fmt: skip
    # BOM-109 second design (docs/research/2026-11-22-redesign-three-worlds.md). Kirchhoff 1943
    # is not fetched (no reachable copy on 2026-11-22); Roys's Chumayel is not fetched (its
    # public-domain status rests on the hosting site's notice; the renewal database refuses
    # programs). Vogel's chapters and Paul 1982 are copyrighted and free to read: private copies.
    g109 = "BOM-109"
    vogel = "https://user.xmission.com/~research/central/"
    for name, group, kind, url, terms, private in (
        ("spinden_ancient_civilizations_1917.txt", "setting", "file", _pg(54550, "-0.txt"),
         PD, False),
        ("dplace_sccs", "setting", "git", GH + "D-PLACE/dplace-dataset-sccs",
         "CC BY-NC 4.0 (D-PLACE; Standard Cross-Cultural Sample codes, Murdock and White)",
         False),
        *[(f"vogel1986_{p}.html", "papers", "file", vogel + f"{p}.htm",
           "copyright 1986 Signature Books, posted with the author's permission; free to read; "
           "private copy", True) for p in [f"vogel{i}" for i in range(1, 7)]],
        ("paul1982_manchester_library.pdf", "papers", "file",
         "https://storage.googleapis.com/scripturecentral-prod-strapi-uploads/"
         "th_and_the_Manchester_New_York_Library_1982_76ea519637/"
         "th_and_the_Manchester_New_York_Library_1982_76ea519637.pdf",
         "copyright BYU Studies; free to read; private copy", True),
    ):  # fmt: skip
        add(name, group, g109, kind, url, terms, private)
    # BOM-109 third design: Roys's Chumayel (Carnegie Institution, 1933), not renewed (Stanford
    # renewal data, checked 2026-11-23), so public domain. sacred-texts.com answers programs with
    # a Cloudflare check (403, 2026-11-23); the same sacred-texts edition (J.B. Hare, 2003,
    # footnotes excluded) is mirrored on the Internet Archive, which accepts identified fetchers.
    add("book-of-chilam-balam-the-of-chumayel", "setting", g109, "ia",
        f"{IA}/details/book-of-chilam-balam-the-of-chumayel",
        PD + " (Roys 1933, copyright not renewed; sacred-texts edition, J.B. Hare 2003, "
        "mirrored on the Internet Archive)")  # fmt: skip
    return rows


def _dest(s: dict) -> Path:
    return (PRIVATE if s["private"] else OPEN) / s["group"] / s["name"]


def _get(url: str, agent: str = UA, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _download(url: str, dest: Path, agent: str = UA) -> None:
    """Stream ``url`` to ``dest`` through a ``.part`` file; an empty reply is an error."""
    part = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": agent})
    try:
        with urllib.request.urlopen(req, timeout=300) as r, out(part).open("wb") as fh:
            while chunk := r.read(1 << 20):
                fh.write(chunk)
    except urllib.error.URLError as exc:
        # Python's certificate bundle lacks some hosts' issuers; curl checks against the
        # system's. Verification stays on either way.
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        cmd = ["curl", "--fail", "-sSL", "-A", agent, "-o", str(out(part)), url]
        subprocess.run(cmd, check=True)
    if part.stat().st_size == 0:
        part.unlink()
        raise OSError("empty reply")
    part.rename(dest)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def _size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _ia(s: dict, dest: Path) -> None:
    """The item's OCR full text, and its metadata record (title, year, creator)."""
    out(dest / "x")
    meta = json.loads(_get(f"{IA}/metadata/{s['name']}"))
    names = [f["name"] for f in meta.get("files", [])]
    text = next((n for n in names if n.endswith("_djvu.txt")), None)
    if text is None:
        raise OSError("no OCR text file in the item")
    _download(f"{IA}/download/{s['name']}/{urllib.parse.quote(text)}", dest / "text.txt")
    out(dest / "metadata.json").write_text(json.dumps(meta.get("metadata", {}), indent=1))


def _ia_all(s: dict, dest: Path) -> None:
    """Every OCR full text of an item holding several volumes, in the item's order, as
    ``text_1.txt`` ... and then ``text.txt`` (all of them joined), and the metadata record."""
    out(dest / "x")
    meta = json.loads(_get(f"{IA}/metadata/{s['name']}"))
    names = sorted(f["name"] for f in meta.get("files", []) if f["name"].endswith("_djvu.txt"))
    if not names:
        raise OSError("no OCR text file in the item")
    for i, n in enumerate(names, 1):
        part = dest / f"text_{i}.txt"
        if not part.exists():
            _download(f"{IA}/download/{s['name']}/{urllib.parse.quote(n)}", part)
            time.sleep(PAUSE)
    out(dest / "metadata.json").write_text(
        json.dumps(meta.get("metadata", {}) | {"ocr_files": names}, indent=1)
    )
    joined = "\n".join((dest / f"text_{i}.txt").read_text("utf-8", "replace") for i in
                       range(1, len(names) + 1))  # fmt: skip
    out(dest / "text.txt").write_text(joined)


def _jsp(s: dict, dest: Path) -> None:
    """Every page of a Joseph Smith Papers document: raw page JSON, then one record a page."""
    slug = s["url"].removeprefix(JSPB).removesuffix("/1")
    raw = dest / "raw"
    out(raw / "x")

    def page(n: int) -> dict:
        path = raw / f"{n:04d}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        props = jsp.page_props(
            jsp.fetch(f"{JSPB}{slug}/{n}", user_agent=jsp.JSP_USER_AGENT, backoff=jsp.JSP_BACKOFF)
        )
        out(path).write_text(json.dumps(props), encoding="utf-8")
        jsp.pause(jsp.JSP_DELAY)
        return props

    total = int(page(1)["summary"]["numberOfPages"])
    records = [jsp.extract(page(n), n) for n in range(1, total + 1)]
    lines = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    out(dest / "pages.jsonl").write_text(lines, encoding="utf-8")


def _git(s: dict, dest: Path) -> None:
    out(dest.parent / "x")
    subprocess.run(["git", "clone", "--quiet", "--depth", "1", s["url"], str(dest)], check=True)


def _figshare(s: dict, dest: Path) -> None:
    for f in json.loads(_get(s["url"]))["files"]:
        if not (dest / f["name"]).exists():
            _download(f["download_url"], out(dest / f["name"]))


def _zenodo(s: dict, dest: Path) -> None:
    """Every file of a Zenodo record."""
    for f in json.loads(_get(s["url"]))["files"]:
        if not (dest / f["key"]).exists():
            _download(f["links"]["self"], out(dest / f["key"]))
            time.sleep(PAUSE)


def _pages(s: dict, dest: Path) -> None:
    """Numbered result pages: the address holds ``{n}`` and ends ``|<count>``; 10 s apart."""
    template, _, count = s["url"].rpartition("|")
    for n in range(int(count)):
        page = dest / f"page_{n:03d}.html"
        if not page.exists():
            _download(template.format(n=n), out(page))
            time.sleep(10)


def _sitemap(s: dict, dest: Path) -> None:
    """Every page a site map lists whose address contains the fragment after ``#``."""
    address, _, part = s["url"].partition("#")
    locs = re.findall(r"<loc>([^<]+)</loc>", _get(address).decode("utf-8", "replace"))
    locs = [u for u in locs if part in u]
    if not locs:
        raise OSError("no matching addresses in the site map")
    for u in locs:
        page = dest / (u.rstrip("/").rsplit("/", 1)[-1] + ".html")
        if not page.exists():
            _download(u, out(page))
            time.sleep(PAUSE)


def _links(s: dict, dest: Path) -> None:
    """Every archive (.zip, .gz, .tgz, .xz) linked from the page."""
    page = _get(s["url"]).decode("utf-8", "replace")
    hrefs = re.findall(r'href="([^"]+\.(?:zip|gz|tgz|xz|bz2))"', page)
    if not hrefs:
        raise OSError("no archive links on the page")
    for href in dict.fromkeys(hrefs):
        name = href.rsplit("/", 1)[-1]
        if not (dest / name).exists():
            _download(urllib.parse.urljoin(s["url"], href), out(dest / name))
            time.sleep(PAUSE)


def _wiki(s: dict, dest: Path) -> None:
    """Page titles of a MediaWiki category (the Onomasticon's names), following continuation."""
    api, _, category = s["url"].partition("#")
    titles, cont = [], {}
    while True:
        q = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category or "Category:Names",
            "cmlimit": "500",
            "format": "json",
            **cont,
        }
        reply = json.loads(_get(api + "?" + urllib.parse.urlencode(q)))
        titles += [m["title"] for m in reply["query"]["categorymembers"]]
        cont = reply.get("continue", {})
        if not cont:
            break
        time.sleep(PAUSE)
    out(dest).write_text(json.dumps(sorted(set(titles)), ensure_ascii=False, indent=1))


KINDS = {
    "ia": _ia,
    "ia_all": _ia_all,
    "jsp": _jsp,
    "git": _git,
    "figshare": _figshare,
    "links": _links,
    "zenodo": _zenodo,
    "pages": _pages,
    "sitemap": _sitemap,
    "wiki": _wiki,
    "file": lambda s, dest: _download(s["url"], out(dest)),
}
# A folder kind is complete only when its last file exists; a half-fetched folder is resumed.
DONE = {"ia": "text.txt", "ia_all": "text.txt", "jsp": "pages.jsonl", "git": ".git"}


def _complete(s: dict, dest: Path) -> bool:
    if s["kind"] in DONE:
        return (dest / DONE[s["kind"]]).exists()
    if s["kind"] in ("figshare", "links", "zenodo", "pages", "sitemap"):
        return False  # the fetcher itself skips files already held
    return dest.is_file() and dest.stat().st_size > 0


BY_HAND = REGISTRY / "sources_by_hand.json"


def _load() -> dict:
    """The record, with the files the owner saved by hand (sites that refuse programs)."""
    record = json.loads(RECORD.read_text()) if RECORD.exists() else {}
    if BY_HAND.exists():
        record |= json.loads(BY_HAND.read_text())
    return record


def _save(record: dict) -> None:
    out(RECORD).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")


def fetch(names: list[str]) -> int:
    record, failed = _load(), 0
    for s in _sources():
        if names and s["name"] not in names and s["group"] not in names:
            continue
        dest, held = _dest(s), record.get(s["name"], {})
        if _complete(s, dest) and held.get("state") == "fetched":
            continue
        entry = {k: s[k] for k in ("group", "tests", "url", "terms")} | {"path": str(dest)}
        try:
            if not _complete(s, dest):
                KINDS[s["kind"]](s, dest)
                time.sleep(PAUSE)
            entry |= {"state": "fetched", "bytes": _size(dest), "date": time.strftime("%Y-%m-%d")}
            if dest.is_file():
                entry["sha256"] = _sha(dest)
            print(f"fetched {s['name']} ({entry['bytes']:,} bytes)", flush=True)
        except Exception as exc:  # noqa: BLE001  a failure is recorded and retried, never content
            failed += 1
            entry |= {"state": "failed", "reason": f"{type(exc).__name__}: {exc}"[:200]}
            print(f"FAILED {s['name']}: {entry['reason']}", file=sys.stderr, flush=True)
        record[s["name"]] = entry
        _save(record)
    return failed


def marc(batch: int = 20) -> int:
    """For every HathiTrust record we hold: the catalog fields that mark a translation.

    MARC 041 (indicator 1 = is a translation; subfield h = language of the original; k =
    intermediate language), 240 subfield l, 765 and 546. One line a record; resumes from the file.
    """
    keys = sorted(
        {
            json.loads(line)["ht_bib_key"]
            for line in gzip.open("data/catalog/hathitrust.jsonl.gz", "rt")
        }
    )
    path = OPEN / "translation_labels" / "hathitrust_marc.jsonl"
    done = set()
    if path.exists():
        done = {json.loads(line)["ht_bib_key"] for line in path.read_text().splitlines()}
    todo = [k for k in keys if k not in done]
    print(f"{len(keys):,} records, {len(done):,} held, {len(todo):,} to fetch", flush=True)
    field = re.compile(
        r'<datafield tag="(041|240|765|546)" ind1="(.)" ind2="(.)">(.*?)</datafield>', re.S
    )
    sub = re.compile(r'<subfield code="(.)">(.*?)</subfield>', re.S)
    with out(path).open("a", encoding="utf-8") as fh:
        for i in range(0, len(todo), batch):
            part = todo[i : i + batch]
            spec = "|".join(f"id:{n};recordnumber:{k}" for n, k in enumerate(part))
            url = "https://catalog.hathitrust.org/api/volumes/full/json/" + spec
            reply = json.loads(_get(url))
            for item in reply if isinstance(reply, list) else reply.values():
                for key, rec in item.get("records", {}).items():
                    fields = [
                        {"tag": t, "ind1": a, "subfields": sub.findall(body)}
                        for t, a, _b, body in field.findall(rec.get("marc-xml", ""))
                    ]
                    fh.write(json.dumps({"ht_bib_key": key, "fields": fields}) + "\n")
            fh.flush()
            if (i // batch) % 100 == 0:
                print(f"  {i + len(part):,}/{len(todo):,}", flush=True)
            time.sleep(PAUSE)
    return 0


TM_PER = "https://www.trismegistos.org/dataservices/rdf/per/?format=json&id="
TM_PAUSE = 3.2  # the site's robots.txt asks for at most one request every 3 seconds


def tm(last: int, part_size: int = 1000) -> int:
    """Trismegistos People through its open per-person service (CC BY-SA 4.0), ids 1 to ``last``.

    One line an id in ``names/trismegistos_people/part_<n>.jsonl``: the whole reply, or null where
    the service answers with an empty body (no such person). Anything else (an error status, a
    reply that is not JSON) is retried with a growing wait and never written, so a rerun resumes
    at the first id not on disk. The name pages of the site sit behind a browser check and are
    not touched.
    """
    folder = OPEN / "names" / "trismegistos_people"
    for start in range(1, last + 1, part_size):
        path = folder / f"part_{start // part_size:04d}.jsonl"
        have = len(path.read_text().splitlines()) if path.exists() else 0
        if have >= min(part_size, last - start + 1):
            continue
        with out(path).open("a", encoding="utf-8") as fh:
            for n in range(start + have, min(start + part_size, last + 1)):
                for attempt in range(8):
                    try:
                        body = _get(TM_PER + str(n)).strip()
                        reply = json.loads(body) if body else None
                        break
                    except (OSError, ValueError) as exc:
                        print(f"  id {n}: {type(exc).__name__}: {exc}; waiting", flush=True)
                        time.sleep(60 * 2**attempt)
                else:
                    print(f"stopped at id {n}: the service kept failing", file=sys.stderr)
                    return 1
                fh.write(json.dumps({"id": n, "reply": reply}, ensure_ascii=False) + "\n")
                fh.flush()
                time.sleep(TM_PAUSE)
        print(f"  through id {min(start + part_size - 1, last):,}/{last:,}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list")
    sp.add_parser("fetch").add_argument("names", nargs="*")
    sp.add_parser("marc")
    sp.add_parser("tm").add_argument("--last", type=int, default=500_000)
    a = ap.parse_args(argv)
    if a.cmd == "tm":
        return tm(a.last)
    if a.cmd == "fetch":
        return 1 if fetch(a.names) else 0
    if a.cmd == "marc":
        return marc()
    record = _load()
    for s in _sources():
        state = record.get(s["name"], {}).get("state", "not fetched")
        print(f"{s['group']:<12} {s['tests']:<24} {state:<12} {s['name']}  [{s['terms']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
