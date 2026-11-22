"""BOM-109 second design, step 1: Vogel 1986, with **our coding of his prose, not his list**.

Dan Vogel, *Indian Origins and the Book of Mormon* (Signature Books, 1986), prints no list of
motifs: his chapters are prose with endnotes. With the owner's yes (2026-11-22, card amendment 1,
made before any three-worlds answer existed) we keyed from his prose the 1820s-era ideas about
Indian origins and American antiquities that he says the Book of Mormon shares. Each motif keeps
his chapter, the endnotes that carry his evidence, the Book of Mormon references he gives, and the
pre-1830 printed sources he cites (author, short title, year: references only; no wording of his
is kept). The web edition (``lab.sources``, ``vogel1986_vogel1..6.html``, private copies) has no
page numbers, so a motif is located by chapter and endnote, not by page. Motifs he ties only to
Joseph Smith's later accounts, not to the 1830 text, are listed in ``EXCLUDED`` and not tested.

The replication, as the card's step 1 asks: for each motif, (1) is it in the 1830 text, and (2) is
it in print before 1830 in one of the sources he names, found in our library. Both are read the
same way: marker words find candidate passages (the three-worlds machinery: long-s repair,
``context_words`` either side, draws by ``seed``); the model judge (``lab.judge``; **simulated
judging by an AI model**) answers one yes/no question per passage, "does this passage state the
idea?". At most ``vogel_book_sample`` passages of the 1830 text and ``vogel_source_max`` passages
of his sources (spread over the sources, earliest first) are asked per motif. A motif is found
with ``vogel_min_yes`` "yes" answers; with none among the passages judged the state is "not found
among the passages judged" (later passages were not read), never "absent". Spalding's manuscript
(printed 1885) is reported apart: it was not in print before 1830.

Sources are found in the library by author surname, a title pattern and print year (any edition
to ``vogel_year_max``); copies of one work (same author, same matched title) are one source; a
source whose pattern matches works by more than one author is "ambiguous" and not used.

Usage::

    python -m lab.threeworlds2_vogel match    # his named sources found in the library (2 min)
    python -m lab.threeworlds2_vogel jobs     # judge questions, private jobs_vogel.jsonl (5 min)
    python -m lab.threeworlds2_vogel report   # the replication from answers_vogel.jsonl (2 min)
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict

from lab import door
from lab import inventory as inv
from lab import threeworlds2 as tw
from lab.paths import out
from metadata import config

OUT = tw.OUT
CARD = tw.CARD
LABEL = "our coding of Vogel's prose, not his list"
SIMULATED = "SIMULATED JUDGING BY AN AI MODEL (lab.judge; BOM-109 second design, Vogel step 1)"
MISS = "not found among the passages judged"

# id: (author surname pattern or None, title pattern, year Vogel cites, kind, config text or None)
# kind: book / periodical / newspaper / manuscript. A config text (``lab.three_worlds2.texts``)
# is the copy the three-worlds run already reads; the rest are found in the library by rule.
SOURCES: dict[str, tuple[str | None, str, int, str, str | None]] = {
    "adair1775": ("adair", r"history of the american indians", 1775, "book",
                  "adair_american_indians_1775"),
    "ashe1806": ("ashe", r"memoirs of mammoth", 1806, "book", None),
    "ashe1808": ("ashe", r"travels in america", 1808, "book", None),
    "atwater1820": ("atwater", r"antiquities", 1820, "book", "atwater_archaeologia_1820"),
    "beatty1768": ("beatty", r"journal of a two months", 1768, "book", None),
    "beaufoy1828": ("beaufoy", r"mexican illustrations", 1828, "book", None),
    "beck1823": ("beck", r"gazetteer of the states? of illinois", 1823, "book", None),
    "belknap1792": ("belknap", r"discourse.{0,40}discovery of america", 1792, "book", None),
    "boudinot1816": ("boudinot", r"star in the west", 1816, "book", "boudinot_star_1816"),
    "buchanan1824": ("buchanan", r"history,? manners,? and customs", 1824, "book", None),
    "bullock1824": ("bullock", r"six months", 1824, "book", None),
    "burke1758": ("burke", r"european settlements in america", 1758, "book", None),
    "carver1796": ("carver", r"travels through the interior", 1778, "book", None),
    "charlevoix1761": ("charlevoix", r"voyage to north.america", 1761, "book", None),
    "clavigero1787": ("clavigero", r"history of mexico", 1787, "book", None),
    "clinton1812": ("clinton", r"discourse", 1812, "book",
                    "clinton_discourse_and_western_new_york"),
    "clinton_memoir": ("clinton", r"antiquities of the western", 1818, "book",
                       "clinton_discourse_and_western_new_york"),
    "cmather1702": ("mather", r"magnalia", 1702, "book", None),
    "cmather1721": ("mather", r"india christiana", 1721, "book", None),
    "cotton1630": ("cotton", r"god'?s promise to his plantation", 1630, "book", None),
    "delrio1822": ("rio", r"ruins of an ancient city", 1822, "book", "del_rio_palenque_1822"),
    "dupratz1774": ("pratz|le page", r"history of louisiana", 1763, "book", None),
    "dwight1821": ("dwight", r"travels in new.england", 1821, "book", None),
    "edwards1788": ("edwards", r"muhhekaneew|mahhekaneew", 1788, "book", None),
    "esmith1825": ("smith", r"view of the hebrews", 1823, "book", "view_of_the_hebrews_1825"),
    "gordon1820": ("gordon", r"north.american continent", 1820, "book", None),
    "harris1805": ("harris", r"journal of a tour", 1805, "book", "harris_tour_1805"),
    "haywood1823": ("haywood", r"natural and aboriginal history", 1823, "book",
                    "haywood_tennessee_1823"),
    "humboldt1811": ("humboldt", r"political essay", 1811, "book", None),
    "humboldt_narrative": ("humboldt", r"personal narrative", 1814, "book", None),
    "james1823": ("james", r"expedition from pittsburgh", 1823, "book", None),
    "jefferson1787": ("jefferson", r"notes on the state of virginia", 1787, "book", None),
    "juarros1823": ("juarros", r"guatemala", 1823, "book", None),
    "kames1774": ("home|kames", r"sketches of the history of man", 1774, "book", None),
    "ker1816": ("ker", r"travels through the western interior", 1816, "book", None),
    "kilbourn1819": ("kilbourn", r"ohio gazetteer", 1819, "book", None),
    "lestrange1652": ("l.estrange", r"americans no jewes", 1652, "book", None),
    "manasseh1650": ("manasseh|israel, manasseh|menasseh", r"hope of israel", 1650, "book", None),
    "mcculloh1817": ("mcculloh", r"researches", 1817, "book", "mcculloh_researches_1817"),
    "morse1793": ("morse", r"american universal geography|american geography", 1789, "book",
                  None),
    "morse1808": ("morse", r"history of america", 1808, "book", None),
    "moulton1804": ("moulton", r"sea journal", 1804, "book", None),
    "parish1810": ("parish", r"system of modern geography", 1810, "book", None),
    "peale1803": ("peale", r"mammoth", 1802, "book", None),
    "penn1683": ("penn", r"letter from william penn", 1683, "book", None),
    "priest1825": ("priest", r"wonders of nature", 1825, "book", None),
    "ranking1827": ("ranking", r"historical researches", 1827, "book", None),
    "rees_cyclopaedia": ("rees", r"cyclop", 1805, "book", None),
    "rwilliams1643": ("williams", r"key into the language", 1643, "book", None),
    "sewall1697": ("sewall", r"ph(a|ae|æ)nomena", 1697, "book", None),
    "smather1773": ("mather", r"known to the ancients", 1773, "book", None),
    "ssmith1787": ("smith", r"variety of complexion", 1787, "book", None),
    "sullivan1795": ("sullivan", r"district of main", 1795, "book", None),
    "swilliams1794": ("williams", r"history of vermont", 1794, "book", None),
    "thorowgood1650": ("thorowgood", r"[ij][ew]?[uvw]+es in america", 1650, "book", None),
    "worsley1828": ("worsley", r"view of the american indians", 1828, "book", None),
    "yates1824": ("yates|moulton", r"history of the state of new.york", 1824, "book", None),
    # periodicals and newspapers: the issue Vogel cites (found only if the library holds it)
    "american_journal_science1818": (None, r"american journal of science", 1818, "periodical",
                                     None),
    "american_monthly1829": (None, r"american monthly magazine", 1829, "periodical", None),
    "belles_lettres1819": (None, r"belles.lettres repository", 1819, "periodical", None),
    "columbian_historian1824": (None, r"columbian historian", 1824, "newspaper", None),
    "columbian_magazine1786": (None, r"columbian magazine", 1786, "periodical", None),
    "columbian_magazine1788": (None, r"columbian magazine", 1788, "periodical", None),
    "niles1818": (None, r"niles'? weekly register", 1818, "periodical", None),
    "niles1819": (None, r"niles'? weekly register", 1819, "periodical", None),
    "north_american_review1817": (None, r"north american review", 1817, "periodical", None),
    "nashville_whig1818": (None, r"nashville whig", 1818, "newspaper", None),
    "oxford_gazette1823": (None, r"oxford gazette", 1823, "newspaper", None),
    "palmyra_herald1822": (None, r"palmyra herald", 1822, "newspaper", None),
    "palmyra_herald1823": (None, r"palmyra herald", 1823, "newspaper", None),
    "palmyra_register1818": (None, r"palmyra register", 1818, "newspaper", None),
    "port_folio1807": (None, r"port.folio", 1807, "periodical", None),
    "port_folio1816": (None, r"port.folio", 1816, "periodical", None),
    "port_folio1819": (None, r"port.folio", 1819, "periodical", None),
    "royal_american1774": (None, r"royal american magazine", 1774, "periodical", None),
    "susquehanna_register1826": (None, r"susquehanna register", 1826, "newspaper", None),
    "us_literary_gazette1824": (None, r"united states literary gazette", 1824, "periodical",
                                None),
    "utica_repository1825": (None, r"christian repository", 1825, "periodical", None),
    "wayne_sentinel1825": (None, r"wayne sentinel", 1825, "newspaper", None),
    "wayne_sentinel1829": (None, r"wayne sentinel", 1829, "newspaper", None),
    # not in print before 1830
    "spalding_ms": ("spalding", r"manuscript", 1812, "manuscript", "spalding_manuscript_story"),
}  # fmt: skip

# id: (the idea as the judge reads it, markers, chapter, endnotes, Book of Mormon references as
# Vogel gives them, source ids). Chapter numbers are the book's: 1 "The Coming Forth of the Book
# of Mormon", 2 "New World Antiquities", 3 "The Origin of the American Indians", 4 "Indians and
# Mound Builders". The idea is our wording; markers use the syntax of
# ``lab.threeworlds2_features`` (``_`` joins a phrase, a trailing ``_`` means lower case only).
MOTIFS: dict[str, tuple[str, str, int, tuple[int, ...], tuple[str, ...], tuple[str, ...]]] = {
    "metal_plates": (
        "ancient people of America had plates of metal (brass, copper or gold) with writing or "
        "characters engraved on them",
        "plates plate engraved engravings engraven engraving",
        1, (40, 41, 42, 43, 44), (),
        ("adair1775", "harris1805", "port_folio1816", "haywood1823"),
    ),
    "lost_book": (
        "the forefathers of the American natives once had a book or record (a sacred book) that "
        "was lost, buried or hidden, and that will be found or had again",
        "book books record records phylactery phylacteries parchment parchments hid_up",
        1, (46, 47, 48), ("ch3 n86-89",),
        ("esmith1825", "boudinot1816", "beatty1768", "worsley1828", "yates1824",
         "us_literary_gazette1824", "cmather1702", "wayne_sentinel1829"),
    ),
    "stone_buildings": (
        "the ancient people of America built great buildings: temples, palaces or towers of "
        "stone or of fine work",
        "temple temples palace palaces tower towers pyramid pyramids edifice edifices "
        "buildings",
        2, (1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15), ("2 Ne. 5:16", "Mos. 11:8-12"),
        ("manasseh1650", "thorowgood1650", "moulton1804", "parish1810", "humboldt1811",
         "delrio1822", "yates1824", "beaufoy1828", "bullock1824", "juarros1823", "haywood1823",
         "american_monthly1829", "esmith1825"),
    ),
    "temple_like_solomon": (
        "a temple or great building of ancient America was like Solomon's temple, or was an "
        "Israelite temple or synagogue",
        "solomon solomon's synagogue synagogues",
        2, (2, 3), ("2 Ne. 5:16",),
        ("manasseh1650", "thorowgood1650", "columbian_magazine1788", "dupratz1774"),
    ),
    "battle_burials": (
        "the bodies of people slain in a great battle in ancient America were heaped up and "
        "covered with earth (burial mounds of the slain)",
        "bones skeletons slain heaped heaps heap mound mounds barrow barrows tumuli tumulus",
        2, (21, 22, 23, 24, 25), ("Al. 16:11", "Al. 2:38", "Al. 28:11"),
        ("belles_lettres1819", "niles1819", "clinton_memoir", "atwater1820", "harris1805",
         "palmyra_register1818", "north_american_review1817"),
    ),
    "earthwork_forts": (
        "ancient people of America fortified their towns with banks, walls or ridges of earth "
        "(or walls of stone), with ditches dug round them",
        "fort forts fortification fortifications fortified rampart ramparts ditch ditches "
        "entrenchment entrenchments trench trenches breastwork breastworks embankment "
        "embankments",
        2, (26, 27, 31, 32), ("Al. 48:8", "Al. 49:4", "Al. 53:3-4"),
        ("atwater1820", "clinton1812", "clinton_memoir", "yates1824", "harris1805",
         "spalding_ms"),
    ),
    "picket_walls": (
        "earthen walls of ancient American fortifications were topped with timber, pickets or "
        "a palisade, with towers over them",
        "pickets picket picketed picketing palisade palisades palisadoes stockade timbers "
        "towers",
        2, (28, 29, 30, 41, 42), ("Al. 50:1-5",),
        ("atwater1820", "harris1805", "clinton_memoir", "oxford_gazette1823", "spalding_ms"),
    ),
    "one_chain_of_works": (
        "the ancient works from the northern lakes to Mexico and Peru were made by one people "
        "who spread or moved along them, from south to north or north to south",
        "mexico peru mexicans peruvians southward northward",
        2, (44, 45, 46, 47, 48, 49), ("Al. 22:28", "Morm. 2-5", "He. 3:4"),
        ("sullivan1795", "harris1805", "yates1824", "columbian_historian1824",
         "american_monthly1829", "kilbourn1819"),
    ),
    "last_stand_north": (
        "the civilised ancient people of America were finally destroyed in the north, in a land "
        "of lakes and many waters (the region of the Great Lakes or western New York)",
        "lakes many_waters bodies_of_water exterminated annihilated last_stand",
        2, (48, 49, 73, 74), ("Morm. 6:4", "He. 3:4"),
        ("kilbourn1819", "american_monthly1829", "clinton1812", "yates1824"),
    ),
    "iron_and_steel": (
        "ancient people of America made or used iron or steel: swords, knives, bows or tools",
        "iron steel sword swords knife knives tools sabre",
        2, (51, 52, 53, 54, 55, 56, 57, 58),
        ("2 Ne. 5:14-15", "1 Ne. 16:18", "Jar. 8", "Eth. 7:9", "Eth. 10:23-27"),
        ("clinton1812", "esmith1825", "port_folio1819", "haywood1823", "atwater1820",
         "harris1805"),
    ),
    "copper_armour": (
        "ancient people of America wore plates or breastplates of copper or brass as armour",
        "breastplate breastplates armour armor copper brass",
        2, (57,), ("Mos. 8:10",),
        ("harris1805",),
    ),
    "cleared_forests": (
        "the ancient inhabitants cleared the land of its forests (the bare prairies, or a land "
        "left without timber, are their work)",
        "prairies prairie timber forests barrens desolate",
        2, (69, 70, 71), ("Al. 22:30-31", "He. 3:3-6"),
        ("american_journal_science1818",),
    ),
    "narrow_neck": (
        "the land of America has two great parts joined by a narrow neck of land (an isthmus)",
        "isthmus narrow_neck neck_of_land darien",
        2, (72,), ("Al. 22:32", "Morm. 2-5"),
        ("burke1758",),
    ),
    "descent_from_adam": (
        "the first peoples of America descend from Adam (and from Noah), not from a separate "
        "creation",
        "adam noah pre-adamites preadamites",
        3, (3, 13, 15, 21, 22, 23), ("2 Ne. 2:20", "2 Ne. 9:21", "Morm. 3:20"),
        ("morse1793", "clavigero1787", "cmather1721", "dwight1821", "ssmith1787"),
    ),
    "flood_over_america": (
        "the Flood covered America too (or its natives kept a memory of the Flood)",
        "flood deluge",
        3, (15, 17, 22, 23), ("Eth. 13:2",),
        ("clavigero1787", "delrio1822", "morse1793", "dwight1821"),
    ),
    "from_babel": (
        "the first settlers of America came from the tower of Babel at the confusion of "
        "languages",
        "babel tower confusion_of_languages confounded dispersion",
        3, (47, 50, 51, 52, 91), ("Eth. 1:33-37",),
        ("lestrange1652", "smather1773", "palmyra_herald1823", "charlevoix1761"),
    ),
    "israelite_origin": (
        "the natives of America (or their ancestors) descend from the Israelites: the lost ten "
        "tribes or other Hebrews who came from the land of Israel",
        "israel israelites israelitish hebrews hebrew jews ten_tribes lost_tribes "
        "house_of_israel jerusalem",
        3, (31, 33, 35, 36, 37, 38, 40, 41, 42, 44, 45), ("1 Ne. 1:4",),
        ("manasseh1650", "thorowgood1650", "sewall1697", "edwards1788", "rwilliams1643",
         "penn1683", "adair1775", "boudinot1816", "esmith1825", "priest1825",
         "wayne_sentinel1825", "susquehanna_register1826", "utica_repository1825"),
    ),
    "two_migrations": (
        "America was peopled by two (or more) separate migrations from the Old World at "
        "different times",
        "migration migrations colony colonies settlers emigrants",
        3, (50, 51, 52), ("Eth. 1-6", "1 Ne. 18"),
        ("smather1773", "palmyra_herald1823"),
    ),
    "land_never_inhabited": (
        "the migrants went to a land where no man had ever dwelt",
        "never_mankind_dwelt never_had_man no_man_dwelt arsareth",
        3, (49, 92), ("Eth. 2:5",),
        ("esmith1825",),
    ),
    "crossed_by_ship": (
        "the first settlers came to America across the ocean in ships or vessels (not by land or "
        "over the ice)",
        "ship ships vessel vessels barges sailed sailing voyage navigation",
        3, (57, 58, 59, 60, 61), ("1 Ne. 17-18", "Eth. 6:4-11"),
        ("charlevoix1761", "carver1796", "palmyra_herald1823", "dupratz1774", "smather1773"),
    ),
    "landed_in_south": (
        "the first civilised settlers of America landed in the south (South or Central America) "
        "and spread northward later",
        "south_america land_southward southward northward",
        3, (61, 63, 64), ("Al. 22:28",),
        ("dupratz1774", "american_monthly1829"),
    ),
    "old_world_beasts": (
        "horses, cattle or other Old World domestic animals lived among the ancient people of "
        "America",
        "horse horses cattle oxen ox cows sheep swine goats asses",
        3, (66, 67), ("Eth. 9:18-19",),
        ("rees_cyclopaedia", "gordon1820", "beck1823", "spalding_ms"),
    ),
    "mammoth_elephant": (
        "elephants or mammoths lived in America within the memory of its peoples, or were used "
        "by its ancient people",
        "elephant elephants mammoth mammoths mammoon mammoons",
        3, (68, 69, 70, 71, 72, 73, 75, 76, 77, 78), ("Eth. 9:19",),
        ("ashe1806", "peale1803", "port_folio1807", "swilliams1794", "jefferson1787",
         "royal_american1774", "palmyra_herald1823", "ranking1827", "spalding_ms"),
    ),
    "honey_bee": (
        "the honey bee was brought to America from the Old World (it was not native)",
        "bee bees honey_bee honey-bee",
        3, (93,), ("Eth. 2:3",),
        ("belknap1792", "jefferson1787"),
    ),
    "civilised_destroyed": (
        "a civilised people who built the ancient works of America was destroyed by a more "
        "savage people (the forefathers of the present natives)",
        "savage savages civilized civilised exterminated annihilated extinct barbarous "
        "destroyed",
        4, (67, 68, 69, 70, 71, 72, 73, 74, 75, 78), ("Morm. 6",),
        ("esmith1825", "belknap1792", "clinton1812", "yates1824", "palmyra_register1818",
         "north_american_review1817", "palmyra_herald1823", "port_folio1816", "spalding_ms"),
    ),
    "savages_were_kin": (
        "the savage people who destroyed the civilised one were of the same family (brethren "
        "who fell into hunting and a savage life)",
        "brethren brothers hunting hunters same_family",
        4, (67, 68, 69), ("2 Ne. 5:21-24", "Enos 20"),
        ("esmith1825",),
    ),
    "white_ancestors": (
        "the ancient civilised people of America, or the forefathers of its natives, were white",
        "white whites fair complexion",
        4, (76, 77, 78, 79, 80, 81), ("2 Ne. 5:21", "3 Ne. 2:15", "2 Ne. 30:6"),
        ("esmith1825", "adair1775", "port_folio1816", "yates1824"),
    ),
    "skin_changed": (
        "the dark skin of the natives of America came about by a change (their way of life, the "
        "climate, or a curse) and is not their first colour; it can change again",
        "skin complexion colour color tawny blackness dark",
        4, (82, 83, 84, 85, 92), ("2 Ne. 5:21", "3 Ne. 2:15", "2 Ne. 30:6"),
        ("adair1775", "ssmith1787", "kames1774", "penn1683", "charlevoix1761"),
    ),
    "savage_ways": (
        "a native people of America was idle, wild, naked, bloodthirsty and lived by hunting "
        "(eating raw flesh, dwelling in tents)",
        "idle idleness indolence indolent naked nakedness wild ferocious bloodthirsty "
        "blood-thirsty loathsome filthy",
        4, (3, 4, 5, 13, 14, 16, 19), ("Enos 20", "1 Ne. 12:23"),
        ("cmather1702", "cmather1721", "columbian_magazine1786", "burke1758", "niles1818",
         "buchanan1824"),
    ),
    "human_sacrifice": (
        "a native people of America offered human beings as sacrifices to idols or gods",
        "sacrifice sacrifices sacrificed sacrificing idol idols",
        4, (7, 8, 9, 10), ("Morm. 4:14", "Morm. 4:21"),
        ("adair1775", "priest1825", "bullock1824", "humboldt1811", "clavigero1787"),
    ),
    "law_of_moses": (
        "the forefathers of the American natives kept the law of Moses or Hebrew rites "
        "(sacrifices, feasts, the sabbath, purifications)",
        "law_of_moses mosaic sabbath firstlings burnt_offerings offerings feasts",
        4, (33, 39, 41), ("2 Ne. 25:24-30", "Jar. 5", "Mos. 2:3"),
        ("esmith1825", "beatty1768", "ker1816", "adair1775", "boudinot1816"),
    ),
    "hebrew_scriptures": (
        "the forefathers of the American natives once had the Hebrew scriptures (the books of "
        "Moses, the Old Testament)",
        "scriptures scripture books_of_moses old_testament",
        4, (34,), ("1 Ne. 5:10-22",),
        ("esmith1825", "beatty1768"),
    ),
    "bible_traditions": (
        "the natives of America kept traditions of the Creation, the Fall, Cain and Abel, the "
        "Flood or the tower of Babel",
        "creation cain abel fall_of eve tradition traditions",
        4, (35, 36, 37, 38), ("1 Ne. 5:11", "2 Ne. 2", "Al. 10:22", "Eth. 1:3", "Eth. 1:33"),
        ("esmith1825", "ker1816", "boudinot1816", "worsley1828", "beatty1768"),
    ),
    "hebrew_language": (
        "the language of the natives of America (or of their forefathers) was Hebrew or like "
        "Hebrew",
        "hebrew language languages tongue dialect",
        4, (39, 40, 41), ("Morm. 9:32-34",),
        ("adair1775", "penn1683", "edwards1788", "rwilliams1643", "boudinot1816",
         "esmith1825"),
    ),
    "egyptian_writing": (
        "the writing of ancient America (its characters, pictures or hieroglyphs) was Egyptian "
        "or like Egyptian",
        "egyptian egyptians hieroglyphics hieroglyphic hieroglyphs characters",
        4, (42,), ("1 Ne. 1:2", "Morm. 9:32"),
        ("esmith1825", "humboldt1811", "humboldt_narrative", "delrio1822"),
    ),
    "gospel_in_america": (
        "the gospel (Christianity) was preached in America in ancient times, before the "
        "Europeans came (by Christ, an apostle or St Thomas)",
        "gospel christianity apostle apostles cross crosses preached",
        4, (43, 44, 53, 54, 55, 57, 58, 59, 60), ("3 Ne. 11-26",),
        ("esmith1825", "yates1824", "worsley1828", "clavigero1787", "delrio1822",
         "belknap1792", "smather1773", "beaufoy1828"),
    ),
    "christian_beliefs": (
        "the natives of America believed in one God (a Great Spirit), an evil spirit or devil, "
        "an immortal soul, and a heaven and hell of rewards and punishments",
        "great_spirit evil_spirit devil immortality immortal heaven hell soul souls one_god",
        4, (45, 46, 47, 48, 49, 50, 51), ("Al. 11:28-29", "Al. 14:5"),
        ("boudinot1816", "palmyra_herald1822", "esmith1825", "beatty1768", "james1823"),
    ),
    "triune_god": (
        "a people of ancient America knew God as three in one (a triune God, Father and Son in "
        "one)",
        "triune trinity three_persons",
        4, (52,), ("Mos. 15:1-5", "3 Ne. 11:36"),
        ("esmith1825",),
    ),
    "white_bearded_teacher": (
        "a white, bearded man (Quetzalcoatl), a priest and lawgiver, taught the ancient people "
        "of America, left, and promised to return",
        "quetzalcoatl quetzalcohuatl bearded beard high_priest lawgiver gave_the_law",
        4, (59, 60, 61, 62, 63), ("Al. 13", "3 Ne. 15:5", "3 Ne. 15:21-24"),
        ("clavigero1787", "delrio1822", "beaufoy1828", "esmith1825"),
    ),
    "other_sheep": (
        "the peoples of America are the 'other sheep' of another fold that Jesus spoke of "
        "(John 10:16)",
        "other_sheep one_fold one_shepherd",
        4, (65,), ("3 Ne. 15:21-24",),
        ("sewall1697",),
    ),
    "new_jerusalem_in_america": (
        "a New Jerusalem is to be built in America",
        "new_jerusalem",
        4, (66,), ("3 Ne. 20:15-22", "3 Ne. 21:22-25", "Eth. 13:1-12"),
        ("sewall1697",),
    ),
    "land_given_to_others": (
        "God takes the land from its native people (for their sins or because they do not use "
        "it) and gives it to other nations who come",
        "land lands possession possessions inheritance vacant",
        4, (17, 18), ("2 Ne. 1:10-11", "1 Ne. 13"),
        ("cotton1630",),
    ),
}  # fmt: skip

# Ideas Vogel ties to Joseph Smith's own accounts or to later Mormon readings, not to the 1830
# text: keyed, not tested (the 1830 text is the question).
EXCLUDED = {
    "stone_box": "chapter 1, endnotes 37-39 and 49: a stone box in a mound; in Joseph Smith's "
                 "accounts of finding the plates, not in the 1830 text",
    "seer_stones_money_digging": "chapter 1, endnotes 3-28: treasure seeking and seer stones; "
                                 "his biography, not the 1830 text",
    "geography_of_landing": "chapter 2, endnotes 67-68: Lehi landing in Chile; a later Mormon "
                            "reading, not the 1830 text",
}  # fmt: skip


def settings(cfg: dict) -> dict:
    return tw.settings(cfg)


# ------------------------------------------------------------------------------ markers


def compile_markers(table: dict[str, str]) -> dict[str, list[tuple[str, tuple[str, ...], str]]]:
    """first word -> [(id, lower-case word tuple, case rule)] (syntax of the features file)."""
    by_first: dict[str, list[tuple[str, tuple[str, ...], str]]] = defaultdict(list)
    for mid, markers in table.items():
        for tok in markers.split():
            case = ""
            if tok.endswith("_"):
                case, tok = "_", tok[:-1]
            words = tuple(p.lower() for p in re.split("[_-]", tok) if p)
            by_first[words[0]].append((mid, words, case))
    return by_first


BY_FIRST = compile_markers({m: v[1] for m, v in MOTIFS.items()})


def find(text: str) -> tuple[list[tuple[int, int]], list[tuple[str, int, int]]]:
    """As ``threeworlds2.find_markers``, for the motifs' markers (a cleaned text)."""
    spans, low, raw = [], [], []
    for m in inv.TOKEN.finditer(text):
        spans.append((m.start(), m.end()))
        w = inv.repair(m.group())
        raw.append(w)
        low.append(w.lower())
    hits = []
    for i, w in enumerate(low):
        for mid, words, case in BY_FIRST.get(w, ()):
            if tuple(low[i : i + len(words)]) != words:
                continue
            if case == "_" and not raw[i].islower():
                continue
            hits.append((mid, i, i + len(words)))
    return spans, hits


# ------------------------------------------------------------------------------ library matching


def _surname(author_norm: str | None) -> str:
    return re.sub(r"\s*\(.*|\s*\d.*", "", (author_norm or "anon").split(",")[0]).strip()


def match_works(sur: str | None, title: str, year_max: int, reg: list[dict], cat: dict,
                kinds: tuple[str, ...] = ("work",)) -> dict:  # fmt: skip
    """Works in the library whose author begins with ``sur`` (a pattern; None: any author),
    whose title matches ``title`` and printed by ``year_max``. Copies and volumes of one work
    (the same author and the same matched title words) form one cluster. Returns {state:
    matched / ambiguous / unmatched, clusters: {key: [work ids]}, earliest: year}."""
    t_re = re.compile(title, re.I)
    a_re = re.compile(rf"^(?:{sur})", re.I) if sur else None
    clusters: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for r in reg:
        if r["kind"] not in kinds or not (r["year"] and r["year"] <= year_max):
            continue
        c = cat.get(r["work_id"])
        if c is None or not c.get("text_path"):
            continue
        an = (c.get("author_norm") or c.get("author") or "").lower()
        if a_re and not (a_re.search(an) or a_re.search((c.get("author") or "").lower())):
            continue
        m = t_re.search(" ".join((c.get("title") or "").split()))
        if not m:
            continue
        who = sur.split("|")[0] if sur else _surname(an)
        clusters[f"{who}|{m.group(0).lower()}"].append((r["year"], r["work_id"]))
    # a surname pattern names one person (its alternatives are that person's catalogue forms);
    # a title-only key is ambiguous when works by more than one author match it
    n_auth = len({k.split("|")[0] for k in clusters})
    state = "unmatched" if not clusters else ("matched" if n_auth == 1 else "ambiguous")
    years = [y for v in clusters.values() for y, _w in v]
    return {"state": state,
            "clusters": {k: [w for _y, w in sorted(v)] for k, v in sorted(clusters.items())},
            "earliest": min(years) if years else None}  # fmt: skip


def library_rows() -> tuple[list[dict], dict]:
    """Registry rows that can be read (text held, the kept copy, not sealed, OCR not excluded)
    and their catalog rows."""
    reg = [r for r in tw._registry() if r["has_text"] and r["dup_keeper"] and not r["sealed"]
           and not r["ocr_excluded"]]  # fmt: skip
    return reg, door.catalog({r["work_id"] for r in reg})


def cmd_match(cfg: dict) -> dict:
    """Vogel's named sources found in the library (or as a three-worlds config text)."""
    s = settings(cfg)
    reg, cat = library_rows()
    cat_year("", reg)
    res: dict = {"label": LABEL, "sources": {}}
    for sid, (sur, title, year, kind, text) in SOURCES.items():
        row: dict = {"cited_year": year, "kind": kind}
        if text:
            row.update({"state": "matched", "via": "config text " + text})
        else:
            kinds = ("newspaper_page",) if kind == "newspaper" else ("work",)
            m = match_works(sur, title, s["vogel_year_max"], reg, cat, kinds)
            if kind in ("periodical", "newspaper") and m["state"] != "unmatched":
                keep = {k: [w for w in v if (cat_year(w, reg) == year)]
                        for k, v in m["clusters"].items()}  # fmt: skip
                keep = {k: v for k, v in keep.items() if v}
                m = {"state": "matched" if keep else "unmatched", "clusters": keep,
                     "earliest": year if keep else None}  # fmt: skip
            row.update(m)
        res["sources"][sid] = row
    counts: dict[str, int] = defaultdict(int)
    for v in res["sources"].values():
        counts[v["state"]] += 1
    res["counts"] = dict(counts)
    res["used_by_motifs"] = {m: [x for x in v[5] if res["sources"][x]["state"] == "matched"]
                             for m, v in MOTIFS.items()}  # fmt: skip
    return res


_YEARS: dict[str, int | None] = {}


def cat_year(wid: str, reg: list[dict]) -> int | None:
    if not _YEARS:
        _YEARS.update({r["work_id"]: r["year"] for r in reg})
    return _YEARS.get(wid)


# ------------------------------------------------------------------------------ jobs

PROMPT = """You are helping a study check where ideas appeared. Your answer is recorded as \
simulated judging by an AI model.

Passage{when}:
{passage}

Does this passage state the following idea (as a fact, a belief, a report or part of a story)?
Idea: {claim}.
Y = yes, the passage states this idea
N = no (it denies it, or it is about something else, or the bracketed words are used another way)

Reply with one letter."""


def prompt(mid: str, passage: str, year: int | None) -> str:
    when = f" (printed in {year})" if year else ""
    return PROMPT.format(when=when, passage=passage, claim=MOTIFS[mid][0])


def scan(segs: list[tuple[str | None, str]]) -> tuple[str, list, dict[str, list], list, list]:
    """(cleaned text, token spans, motif -> [(first token, last token + 1)] in text order,
    segment starts, segment references)."""
    parts, starts, refs, pos = [], [], [], 0
    for ref, t in segs:
        c = tw.clean(t)
        starts.append(pos)
        refs.append(ref)
        parts.append(c)
        pos += len(c) + 1
    text = "\n".join(parts)
    spans, hits = find(text)
    by: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for mid, a, b in hits:
        by[mid].append((a, b))
    return text, spans, by, starts, refs


def passages(segs: list[tuple[str | None, str]], want: dict[str, list[int]],
             cfg: dict) -> dict[tuple[str, int], dict]:  # fmt: skip
    """(motif, hit index) -> {ref, char, passage}, only for the hits wanted (big sources are
    never held in memory as passages)."""
    import bisect

    s = settings(cfg)
    text, spans, by, starts, refs = scan(segs)
    got = {}
    for mid, idx in want.items():
        for i in idx:
            a, b = by[mid][i]
            seg = bisect.bisect_right(starts, spans[a][0]) - 1
            p = tw.passage(text, spans, a, b, s["context_words"])
            got[(mid, i)] = {"ref": refs[seg], "char": spans[a][0], "passage": p}
    return got


def source_units(cfg: dict, matched: dict) -> dict[str, list[tuple[str, int, str]]]:
    """source id -> [(unit name, print year, how to load it)] for every matched source."""
    s = settings(cfg)
    units: dict[str, list[tuple[str, int, str]]] = {}
    for sid, row in matched.items():
        if row["state"] != "matched":
            continue
        if row.get("via", "").startswith("config text "):
            name = row["via"][len("config text ") :]
            units[sid] = [(name, SOURCES[sid][2], s["texts"][name][3])]
            continue
        units[sid] = [(w, _YEARS.get(w) or SOURCES[sid][2], "lib:" + w)
                      for wids in row["clusters"].values() for w in wids]  # fmt: skip
    return units


def cmd_jobs(cfg: dict) -> dict:
    """The private jobs file: per motif, the 1830 text (``vogel_book_sample`` passages drawn by
    seed) and Vogel's matched sources (``vogel_source_max`` passages, one source at a time,
    earliest first, each source's passages in an order drawn by seed). Two passes: hits are
    counted per text, the draws planned from the counts, then only the drawn passages cut."""
    s = settings(cfg)
    tw._named(cfg)  # fixes the long-s vocabulary before any text is read
    matched = cmd_match(cfg)["sources"]
    units = source_units(cfg, matched)
    loads = {name: src for us in units.values() for name, _y, src in us}
    counts: dict[str, dict[str, int]] = {}
    for name, src in loads.items():
        segs = tw.load(src, cfg)
        counts[name] = {} if segs is None else {m: len(v) for m, v in scan(segs)[2].items()}
    book_segs = tw.bom_units()
    book_by = scan(book_segs)[2]
    jobs_plan: list[tuple[str, str, str, int, int | None]] = []  # (job id, motif, unit, idx, year)
    meta: dict = {"book": {}, "sources": {}}
    for mid, spec in MOTIFS.items():
        n_book = len(book_by.get(mid, []))
        rng = random.Random(f"{s['seed']}|vogel|book|{mid}")
        pick = sorted(rng.sample(range(n_book), min(n_book, s["vogel_book_sample"])))
        meta["book"][mid] = {"hits": n_book, "asked": []}
        for n, i in enumerate(pick):
            jobs_plan.append((f"vogel|{mid}|book|{n}", mid, "book_of_mormon", i, None))
        queues, seen = [], set()
        for sid in spec[5]:
            for name, year, _src in units.get(sid, []):
                if name in seen:
                    continue  # one text serving two of his citations (Clinton) is read once
                seen.add(name)
                order = list(range(counts[name].get(mid, 0)))
                random.Random(f"{s['seed']}|vogel|{mid}|{sid}|{name}").shuffle(order)
                queues.append((year, sid, name, order))
        queues.sort(key=lambda q: (q[0], q[1], q[2]))
        meta["sources"][mid] = {"hits": {f"{q[1]}|{q[2]}": len(q[3]) for q in queues},
                                "asked": []}  # fmt: skip
        k, rnd = 0, 0
        while k < s["vogel_source_max"] and any(rnd < len(q[3]) for q in queues):
            for year, sid, name, order in queues:
                if rnd < len(order) and k < s["vogel_source_max"]:
                    jid = f"vogel|{mid}|src|{k}"
                    jobs_plan.append((jid, mid, name, order[rnd], year))
                    meta["sources"][mid]["asked"].append({"id": jid, "source": sid,
                                                          "unit": name, "year": year})  # fmt: skip
                    k += 1
            rnd += 1
    want: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for _jid, mid, name, i, _y in jobs_plan:
        want[name][mid].append(i)
    cut: dict[str, dict] = {}
    for name, w in want.items():
        segs = book_segs if name == "book_of_mormon" else tw.load(loads[name], cfg)
        cut[name] = passages(segs, w, cfg)
    jobs = []
    for jid, mid, name, i, year in jobs_plan:
        x = cut[name][(mid, i)]
        jobs.append({"id": jid, "prompt": prompt(mid, x["passage"], year)})
        if name == "book_of_mormon":
            meta["book"][mid]["asked"].append({"id": jid, "ref": x["ref"]})
    out(CARD / "jobs_vogel.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs))
    out(CARD / "jobs_vogel_meta.json").write_text(json.dumps(meta))
    per_hour = cfg["lab"]["judge"]["per_hour"]
    return {"label": LABEL, "simulated": SIMULATED + "; prepared, not run",
            "questions": len(jobs), "hours_at_per_hour": round(len(jobs) / per_hour, 1),
            "per_hour": per_hour, "model": s["judge_model"],
            "book_questions": sum(len(v["asked"]) for v in meta["book"].values()),
            "source_questions": sum(len(v["asked"]) for v in meta["sources"].values()),
            "motifs": len(MOTIFS), "units_read": len(loads),
            "motifs_without_book_hits": [m for m, v in meta["book"].items() if not v["hits"]],
            "motifs_without_source_hits": [m for m, v in meta["sources"].items()
                                           if not sum(v["hits"].values())]}  # fmt: skip


# ------------------------------------------------------------------------------ report


def verdict(ids: list[str], answers: dict[str, str], s: dict) -> tuple[str, int, int]:
    """found / not found among the passages judged / open / no passage; (yes, answered)."""
    if not ids:
        return "no passage to judge", 0, 0
    yes, n = 0, 0
    for i in ids:
        a = answers.get(i)
        if a is None:
            continue
        p = tw.parse_letter(a, "YN")
        if p is None:
            tw.log_unparsed(i, a)
            continue
        n += 1
        yes += p == "Y"
    if yes >= s["vogel_min_yes"]:
        return "found", yes, n
    if n < len(ids):
        return "open", yes, n
    return MISS, yes, n


def report(meta: dict, answers: dict[str, str], cfg: dict) -> dict:
    s = settings(cfg)
    res: dict = {"label": LABEL, "simulated": SIMULATED, "motifs": {}}
    for mid, spec in MOTIFS.items():
        b = meta["book"][mid]
        bv, by, bn = verdict([x["id"] for x in b["asked"]], answers, s)
        src = meta["sources"][mid]
        per: dict[str, dict] = {}
        for x in src["asked"]:
            per.setdefault(x["source"], {"ids": [], "year": x["year"]})["ids"].append(x["id"])
            per[x["source"]]["year"] = min(per[x["source"]]["year"], x["year"])
        found_print, found_ms, rows = [], [], {}
        for sid, v in per.items():
            st, y, n = verdict(v["ids"], answers, s)
            rows[sid] = {"state": st, "yes": y, "answered": n, "asked": len(v["ids"]),
                         "year": v["year"]}  # fmt: skip
            if st == "found":
                (found_ms if SOURCES[sid][3] == "manuscript" else found_print).append(
                    (v["year"], sid)
                )
        held_print = [x for x in spec[5] if x in per and SOURCES[x][3] != "manuscript"]
        if found_print:
            pv = "found"
        elif any(r["state"] == "open" for r in rows.values()):
            pv = "open"
        elif not held_print:
            pv = "no named printed source held"
        else:
            pv = MISS
        res["motifs"][mid] = {
            "chapter": spec[2], "endnotes": list(spec[3]), "bom_refs_vogel": list(spec[4]),
            "in_1830_text": {"state": bv, "yes": by, "answered": bn,
                             "asked": len(b["asked"]), "marker_hits": b["hits"]},
            "in_print_before_1830": {"state": pv,
                                     "earliest": min(found_print) if found_print else None,
                                     "sources": rows},
            "in_spalding_manuscript": (rows.get("spalding_ms") or {}).get("state"),
        }  # fmt: skip
    counts: dict[str, int] = defaultdict(int)
    for v in res["motifs"].values():
        counts[f"1830 text: {v['in_1830_text']['state']}"] += 1
        counts[f"in print: {v['in_print_before_1830']['state']}"] += 1
        if v["in_1830_text"]["state"] == "found" and v["in_print_before_1830"]["state"] == "found":
            counts["both found"] += 1
    res["counts"] = dict(sorted(counts.items()))
    return res


def cmd_report(cfg: dict) -> dict:
    meta = json.loads((CARD / "jobs_vogel_meta.json").read_text())
    answers = tw.load_answers([CARD / "answers_vogel.jsonl"])
    return report(meta, answers, cfg)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["match", "jobs", "report"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "match":
        res = cmd_match(cfg)
        tw.write(OUT / "vogel_sources.json", res)
        print(json.dumps(res["counts"]))
        for sid, v in res["sources"].items():
            print(f"  {sid:30s} {v['state']:10s} {v.get('via') or list(v.get('clusters', {}))}")
    elif a.cmd == "jobs":
        res = cmd_jobs(cfg)
        tw.write(OUT / "vogel_jobs.json", res)
        print(json.dumps(res, indent=1))
    else:
        res = cmd_report(cfg)
        tw.write(OUT / "replication_vogel.json", res)
        print(json.dumps(res["counts"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
