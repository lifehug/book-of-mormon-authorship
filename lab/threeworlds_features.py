"""BOM-109: the feature list for the three-worlds test (lab/threeworlds.py).

Written by the AI on 2026-11-21 from the topics named in the issue and the brief (calendar and
number base, draft animals and wheels, crops, metals, money, writing, warfare, kingship, city form,
markets, religion, dress, seasons, reckoning of years), before any Book of Mormon value was
recorded. The marker words were chosen from the vocabulary of the source texts (the King James
Bible, the native Mesoamerican texts and Clavigero, the 1820s antiquities books), not from the
Book of Mormon; where a word is known to be the Book of Mormon's own coinage (``head-plates``,
``thick clothing``, ``title of liberty``, the unit names of Alma 11) it is deliberately left out, so
the book is read in the comparison texts' words.

Two kinds of feature:

* ``RULE``: countable. Each is a marker list (single words; ``a b`` is a two-word phrase; a
  trailing ``^`` means the word counts only when capitalised, ``_`` only when in lower case), or a
  ``special`` rule implemented in ``lab.threeworlds`` (``vigesimal``, ``ad_years``). A text states
  the feature *present* or *absent* by the thresholds in ``lab.three_worlds``. A world's value is
  measured: the majority of that world's source texts that state it. ``coded`` replaces the
  measured value for a world where a held source states it differently (the source and the kind
  of citation are recorded); ``memory`` marks a value written from memory.
* ``READING``: needs a reader (succession, markets, sacrifice ...). Each world's value is a short
  description with a citation: ``kjv`` (a King James verse, checked by the code to contain the
  check words), ``held`` (a held source that contains the check words; the statement itself was
  not read by a person), or ``memory``. These go to simulated judging by an AI model (prepared,
  not run in this task).
"""

from __future__ import annotations

NE, MS, AM = "near_east", "mesoamerica", "america_1820s"
WORLDS = (NE, MS, AM)

_CLAV1 = "Clavigero, History of Mexico (1787), vol. 1 (lab.three_worlds.library.clavigero_v1)"

# id: topic, short label, markers or special name, and
# coded {world: (value, citation, kind, check words)}
RULE: dict[str, dict] = {
    # animals and transport
    "horses": {"topic": "animals and transport", "label": "horses and horsemen",
               "markers": "horse horses horseman horsemen steed steeds",
               "coded": {MS: ("absent", _CLAV1 + ", book I: horses among the animals "
                              "'transported from the Canaries and Europe' in the sixteenth "
                              "century", "held", "transported from the Canaries")}},
    "wheeled_vehicles": {"topic": "animals and transport", "label": "chariots, wagons, carts",
                         "markers": "chariot chariots wagon wagons waggon waggons cart carts"},
    "asses_camels": {"topic": "animals and transport", "label": "asses, camels, mules",
                     "markers": "ass asses camel camels mule mules dromedary dromedaries"},
    "ow_livestock": {"topic": "animals and transport", "label": "Old World livestock",
                     "markers": "ox oxen cattle kine sheep goat goats swine bullock bullocks "
                                "heifer heifers cow cows"},
    "nw_animals": {"topic": "animals and transport", "label": "New World animals",
                   "markers": "turkey_ turkeys_ jaguar jaguars ocelot ocelots tapir tapirs peccary "
                              "peccaries opossum opossums raccoon raccoons racoon racoons quetzal "
                              "macaw macaws llama llamas bison buffalo buffaloes buffalos "
                              "alligator alligators armadillo armadillos coyote coyotes puma "
                              "pumas cougar cougars rattlesnake rattlesnakes hummingbird "
                              "hummingbirds humming-bird humming-birds"},
    "elephants": {"topic": "animals and transport", "label": "elephants, mammoths",
                  "markers": "elephant elephants mammoth mammoths mastodon mastodons"},
    # crops and food
    "ow_grains": {"topic": "crops", "label": "wheat, barley and other Old World grains",
                  "markers": "wheat barley rye spelt millet oats",
                  "coded": {MS: ("absent", _CLAV1 + ", book I: wheat and barley are among "
                                 "the grains 'that country had from Europe'", "held",
                                 "had from Europe")}},
    "maize": {"topic": "crops", "label": "maize named as such",
              "markers": "maize maiz mahiz indian_corn"},
    "nw_plants": {"topic": "crops", "label": "New World plants and foods",
                  "markers": "cacao cocoa chocolate tobacco maguey agave pulque squash squashes "
                             "potato potatoes tomato tomatoes chili chilli cassava manioc "
                             "pineapple pineapples vanilla nopal tortilla tortillas tamale "
                             "tamales copal"},
    "vine_olive_fig": {"topic": "crops", "label": "vineyards, olives, figs",
                       "markers": "vineyard vineyards olive olives fig figs"},
    # metals
    "iron_steel": {"topic": "metals", "label": "iron and steel", "markers": "iron steel"},
    "brass_bronze": {"topic": "metals", "label": "brass and bronze",
                     "markers": "brass brazen bronze"},
    "gold_silver": {"topic": "metals", "label": "gold and silver", "markers": "gold silver"},
    "copper": {"topic": "metals", "label": "copper", "markers": "copper"},
    # money
    "coins": {"topic": "money", "label": "coined money",
              "markers": "coin coins coined dollar dollars cent cents shilling shillings guinea "
                         "guineas ducat ducats"},
    "weighed_money": {"topic": "money", "label": "shekels and other weighed units",
                      "markers": "shekel shekels gerah gerahs bekah maneh"},
    # writing
    "hieroglyphs": {"topic": "writing", "label": "hieroglyphics",
                    "markers": "hieroglyph hieroglyphs hieroglyphic hieroglyphics hieroglyphical"},
    "scrolls": {"topic": "writing", "label": "scrolls and parchment",
                "markers": "scroll scrolls parchment parchments"},
    "printing": {"topic": "writing", "label": "printing and newspapers",
                 "markers": "printed printing printer printers newspaper newspapers"},
    "metal_plates": {"topic": "writing", "label": "plates of metal (engraved or not)",
                     "markers": "plates_of_brass plates_of_gold plates_of_copper plate_of_gold "
                                "brass_plates gold_plates golden_plates copper_plates"},
    # warfare
    "firearms": {"topic": "warfare", "label": "firearms",
                 "markers": "gun guns musket muskets rifle rifles cannon cannons gunpowder pistol "
                            "pistols bayonet bayonets artillery"},
    "swords": {"topic": "warfare", "label": "swords and scimitars",
               "markers": "sword swords cimeter cimeters scimitar scimitars"},
    "spears": {"topic": "warfare", "label": "spears, lances, javelins",
               "markers": "spear spears lance lances javelin javelins"},
    "native_weapons": {"topic": "warfare", "label": "obsidian blades, macuahuitl, atlatl",
                       "markers": "obsidian itztli macuahuitl maquahuitl macana macanas atlatl"},
    "metal_armour": {"topic": "warfare", "label": "helmets, breastplates, mail",
                     "markers": "helmet helmets breastplate breastplates coat_of_mail "
                                "coats_of_mail greaves brigandine brigandines habergeon "
                                "habergeons"},
    "quilted_armour": {"topic": "warfare", "label": "quilted cotton armour",
                       "markers": "quilted escaupil escaupiles ichcahuipilli cotton_armour "
                                  "cotton_armor armour_of_cotton armor_of_cotton"},
    "shields": {"topic": "warfare", "label": "shields and bucklers",
                "markers": "shield shields buckler bucklers"},
    "picket_forts": {"topic": "warfare", "label": "pickets, palisades, entrenchments",
                     "markers": "picket pickets palisade palisades palisadoes stockade stockades "
                                "entrenchment entrenchments intrenchment intrenchments embankment "
                                "embankments"},
    "mounds": {"topic": "warfare", "label": "mounds and tumuli",
               "markers": "mound mounds tumulus tumuli"},
    "indian_war_things": {"topic": "warfare", "label": "tomahawk, scalp, wampum, wigwam",
                          "markers": "tomahawk tomahawks scalp scalps scalped scalping wampum "
                                     "wigwam wigwams calumet war_whoop war-whoop"},
    # calendar and reckoning
    "roman_months": {"topic": "calendar", "label": "named Roman months",
                     "markers": "January^ February^ April^ June^ July^ August^ September^ "
                                "October^ November^ December^"},
    "ordinal_months": {"topic": "calendar", "label": "months counted by ordinal",
                       "markers": "first_month second_month third_month fourth_month "
                                  "fifth_month sixth_month seventh_month eighth_month "
                                  "ninth_month tenth_month eleventh_month twelfth_month"},
    "meso_calendar": {"topic": "calendar", "label": "katun, ahau, 52-year cycle",
                      "markers": "katun katuns ahau fifty_two_years fifty-two_years "
                                 "tonalamatl tonalpohualli uinal nemontemi"},
    "ad_years": {"topic": "calendar", "label": "years written as A.D. dates",
                 "special": "ad_years"},
    "regnal_years": {"topic": "calendar", "label": "years of a reign",
                     "markers": "year_of_his_reign year_of_the_reign year_of_king "
                                "year_of_the_king years_of_his_reign"},
    "vigesimal": {"topic": "calendar", "label": "round numbers in twenties",
                  "special": "vigesimal",
                  "coded": {MS: ("present", "data/lab/setting/numbers/result.json (BOM-114): "
                                 "native Mesoamerican texts pooled, 32 of 35 round numbers "
                                 "between 20 and 400 are multiples of twenty", "held", "")}},
    "sabbath": {"topic": "calendar", "label": "the sabbath", "markers": "sabbath sabbaths"},
    "new_moons": {"topic": "calendar", "label": "new moons as feasts",
                  "markers": "new_moon new_moons"},
    # religion
    "hebrew_gods": {"topic": "religion", "label": "Jehovah, Baal and their rivals",
                    "markers": "jehovah baal baalim ashtaroth dagon moloch molech chemosh "
                               "milcom"},
    "meso_gods": {"topic": "religion", "label": "Mesoamerican gods by name",
                  "markers": "quetzalcoatl quetzalcohuatl huitzilopochtli vitzilopochtli "
                             "mexitli tezcatlipoca tlaloc hurakan huracan gucumatz tepeu "
                             "kukulcan itzamna tohil xibalba"},
    "great_spirit": {"topic": "religion", "label": "the Great Spirit",
                     "markers": "great_spirit manitou manito manitto"},
    "burnt_offerings": {"topic": "religion", "label": "burnt offerings",
                        "markers": "burnt_offering burnt_offerings burnt_sacrifice "
                                   "burnt_sacrifices"},
    "human_sacrifice": {"topic": "religion", "label": "human sacrifice named",
                        "markers": "human_sacrifice human_sacrifices human_victim "
                                   "human_victims"},
    "synagogues": {"topic": "religion", "label": "synagogues",
                   "markers": "synagogue synagogues"},
    "idols": {"topic": "religion", "label": "idols", "markers": "idol idols idolatry"},
    "temples": {"topic": "religion", "label": "temples", "markers": "temple temples"},
    "pyramids": {"topic": "religion", "label": "pyramids, teocalli",
                 "markers": "pyramid pyramids teocalli teocallis"},
    # land, people, dress
    "snow_frost": {"topic": "seasons and land", "label": "snow and frost",
                   "markers": "snow snows frost frosts sleigh sleighs"},
    "canoes": {"topic": "seasons and land", "label": "canoes", "markers": "canoe canoes"},
    "causeways": {"topic": "seasons and land", "label": "causeways",
                  "markers": "causeway causeways"},
    "markets": {"topic": "seasons and land", "label": "markets",
                "markers": "market markets marketplace market_place"},
    "indians": {"topic": "seasons and land", "label": "Indians and savages",
                "markers": "indian indians savage savages"},
    "linen": {"topic": "dress", "label": "linen", "markers": "linen"},
    "cotton": {"topic": "dress", "label": "cotton", "markers": "cotton"},
    "silk": {"topic": "dress", "label": "silk", "markers": "silk silks"},
    "feathers": {"topic": "dress", "label": "feathers and plumes",
                 "markers": "feather feathers plume plumes plumage"},
}  # fmt: skip

_CLAV = "Clavigero 1787 vol. 1 (books I-VII, before the conquest)"
_MEM = "memory"

# id: topic, label, keywords that find candidate passages, the three descriptions with citations.
# A citation is (kind, where, check words); kind kjv = a King James verse whose text must contain
# every check word (verified by lab.threeworlds), held = a held source that must contain the check
# words (verified; the statement itself unread), memory = written from memory (no check).
READING: dict[str, dict] = {
    "succession": {
        "topic": "kingship", "label": "how a ruler is succeeded",
        "keywords": r"\b(reign(ed)? in his stead|succeed(ed)?|conferred the kingdom|elect(ed)?|"
                    r"appoint(ed)? .{0,20}king|chief judge|heir|his son .{0,20}(king|throne))\b",
        "values": {
            NE: ("a son succeeds his father on the throne",
                 ("kjv", "1 Chronicles 29:28", "Solomon his son reigned in his stead")),
            MS: ("a brother or nephew of the dead king is chosen by electors from the royal "
                 "lineage", ("held", _CLAV, "electors")),
            AM: ("leaders are elected (chiefs chosen by a council; republican offices)",
                 ("memory", _MEM, "")),
        }},
    "markets": {
        "topic": "markets", "label": "where and how goods are traded",
        "keywords": r"\b(market|traffic|merchant|trade|sold|buy|bought|barter|exchange)\w*\b",
        "values": {
            NE: ("traders and merchants deal at the city gate and with caravans",
                 ("kjv", "Ezekiel 27:12", "merchant")),
            MS: ("great daily or periodic markets in a public square, under judges, with goods "
                 "bartered or paid in cacao", ("held", _CLAV, "market")),
            AM: ("stores, shops and merchants paid in money", ("memory", _MEM, "")),
        }},
    "sacrifice": {
        "topic": "religion", "label": "what is offered in sacrifice",
        "keywords": r"\b(sacrific\w*|offering|altar\w*|victim\w*)\b",
        "values": {
            NE: ("animals (bulls, sheep, goats) burned on an altar",
                 ("kjv", "Leviticus 1:9", "burnt sacrifice")),
            MS: ("human victims, and the offerer's own blood", ("held", _CLAV, "human victims")),
            AM: ("no sacrifice by the writer's own people; the imagined ancients or Indians may "
                 "offer game or human captives", ("memory", _MEM, "")),
        }},
    "captives": {
        "topic": "warfare", "label": "what is done with prisoners of war",
        "keywords": r"\b(prisoners?|captives?|captivity|taken alive|bondage)\b",
        "values": {
            NE: ("carried away captive, enslaved, or put to forced labour",
                 ("kjv", "Jeremiah 52:28", "carried away captive")),
            MS: ("taken alive in battle to be sacrificed to the gods", ("held", _CLAV,
                                                                        "prisoners")),
            AM: ("tortured or burned, or adopted into the captors' nation; exchanged in a "
                 "civilised war", ("memory", _MEM, "")),
        }},
    "burial": {
        "topic": "religion", "label": "how the dead are buried",
        "keywords": r"\b(buri\w*|sepulch\w*|tomb\w*|grave\w*|mound\w*|heaps? of earth)\b",
        "values": {
            NE: ("in a cave or rock-cut sepulchre", ("kjv", "Genesis 23:19", "cave")),
            MS: ("cremation of lords, or burial under houses and temples with goods",
                 ("held", _CLAV, "burnt")),
            AM: ("in earth mounds raised over the dead", ("memory", _MEM, "")),
        }},
    "temple": {
        "topic": "religion", "label": "temples: one or many, and their form",
        "keywords": r"\b(temples?|sanctuary|house of the lord|tabernacle)\b",
        "values": {
            NE: ("one temple, at the place the Lord chooses", ("kjv", "Deuteronomy 12:5",
                                                              "shall choose")),
            MS: ("many temples on stepped pyramids in every town", ("held", _CLAV, "temples")),
            AM: ("churches and meeting-houses; ancient temples imagined on mounds",
                 ("memory", _MEM, "")),
        }},
    "writing_material": {
        "topic": "writing", "label": "what records are written on",
        "keywords": r"\b(plates?|records?|engrav\w*|written|writ|book|roll|scroll|"
                    r"paint\w*)\b",
        "values": {
            NE: ("rolls of a book (scrolls), and tablets of stone", ("kjv", "Jeremiah 36:2",
                                                                     "roll of a book")),
            MS: ("painted books of bark paper or deerskin", ("held", _CLAV, "paintings")),
            AM: ("inscribed plates or stones dug from mounds; printed books",
                 ("memory", _MEM, "")),
        }},
    "money": {
        "topic": "money", "label": "what serves as money",
        "keywords": r"\b(money|price|pieces? of (gold|silver)|weigh\w*|measure of|"
                    r"worth|value|cacao)\b",
        "values": {
            NE: ("silver weighed out by the shekel", ("kjv", "Genesis 23:16", "weighed")),
            MS: ("cacao beans, cotton cloths, quills of gold dust", ("held", _CLAV, "cacao")),
            AM: ("coined dollars and cents", ("memory", _MEM, "")),
        }},
    "dress": {
        "topic": "dress", "label": "what people wear",
        "keywords": r"\b(garments?|apparel|cloth\w*|robes?|girdle|naked|skins?|raiment)\b",
        "values": {
            NE: ("robes, coats, girdles of linen and wool", ("kjv", "Exodus 28:4",
                                                             "robe")),
            MS: ("loincloth and a cotton mantle knotted at the shoulder, with feather work",
                 ("held", _CLAV, "mantle")),
            AM: ("coats and breeches; the Indians in skins and blankets", ("memory", _MEM, "")),
        }},
    "city_form": {
        "topic": "city form", "label": "what a city looks like",
        "keywords": r"\b(cit(y|ies)|walls?|gates?|towers?|forts?|fortif\w*|buildings?)\b",
        "values": {
            NE: ("a walled city with gates and towers", ("kjv", "Deuteronomy 3:5",
                                                         "walls")),
            MS: ("a ceremonial centre of plazas, temple-pyramids and palaces, with houses spread "
                 "around it", ("held", _CLAV, "palaces")),
            AM: ("earthwork enclosures and forts of banked earth with pickets",
                 ("memory", _MEM, "")),
        }},
    "origins": {
        "topic": "origins", "label": "where the people came from",
        "keywords": r"\b(came (out )?from|forefathers?|fathers came|land of (our|their) "
                    r"(fathers|inheritance)|crossed|across the (sea|great waters))\b",
        "values": {
            NE: ("their fathers came from beyond the river (Abraham) or out of Egypt",
                 ("kjv", "Joshua 24:3", "other side of the flood")),
            MS: ("from a place of origin in the north or a cave (Aztlan, Tulan)",
                 ("held", _CLAV, "Aztlan")),
            AM: ("from Israel, across the sea or by way of the north (the lost tribes)",
                 ("memory", _MEM, "")),
        }},
    "war_aim": {
        "topic": "warfare", "label": "what wars are fought for",
        "keywords": r"\b(war|battle|fought|contend\w*|defend\w*|conquer\w*)\b",
        "values": {
            NE: ("to take and hold land and destroy the enemy", ("kjv", "Deuteronomy 20:16",
                                                                 "save alive nothing")),
            MS: ("to take captives and tribute", ("held", _CLAV, "tribute")),
            AM: ("for liberty and the defence of homes, or Indian raids for revenge",
                 ("memory", _MEM, "")),
        }},
}  # fmt: skip
