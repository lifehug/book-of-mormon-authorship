"""BOM-109 second design: the feature list, each with its kind, topic, marker words and provenance.

Written 2026-11-22 at finalisation, before any mention was read. A feature is a thing, practice
or belief that a text can give to the people it is about. Its *kind* is fixed here, before
scoring: the world whose profile it was listed to tell apart (``near_east``, ``mesoamerica``,
``america_1820s`` for beliefs neither real world supports, ``contemporary`` for the European and
American things of the writers' own day, the grid's fourth column). The kind is used only to
report sole agreements; every world's value is measured from attributed mentions.

Marker words find candidate mentions only; the judge decides whose each mention is. Syntax as
``lab.threeworlds_features``: a token is a word, ``_`` joins the words of a phrase, a trailing
``_`` means lower case only (so "Turkey" the country is not "turkey" the bird).

Provenance codes (checked by ``lab.threeworlds2.check_provenance``):

- ``coe1973``: Coe, "Mormons and Archaeology: An Outside View", *Dialogue* 8/2 (1973): the short
  list of missing things (horse, chariot, wheat, barley, cattle, the metallurgy described), as
  summarised in ``docs/research/2026-11-20-the-books-setting.md``.
- ``dale:<id>``: an item of Dale and Dale 2019 (``data/lab/setting/dale_checklist/items.json``).
- ``roper:<thing>``: Roper 2025's items with that thing
  (``data/lab/setting/anachronisms/items.json``).
- ``vogel:ch2`` / ``ch3`` / ``ch4``: Vogel 1986, chapters "New World Antiquities", "The Origin of
  the American Indians", "Indians and Mound Builders" (private copies; the book prints no
  numbered motif list).
- ``dplace:<var>``: a D-PLACE Standard Cross-Cultural Sample variable coded for the Aztec
  (SCCS153) and the Hebrews (SCCS44); see ``DPLACE``.
- ``v1:<id>``: the first design's feature (``lab.threeworlds_features``), used only where none of
  the above covers the topic.
- ``bom111:<file>``: the BOM-111 inventory's sourced lists (Wikipedia pages fetched 2026-11-20).

Kirchhoff 1943 is not used: no copy of the essay could be reached on 2026-11-22, and the card
requires his trait list to be checked against the essay first.
"""

from __future__ import annotations

NE, MS, AM, CT = "near_east", "mesoamerica", "america_1820s", "contemporary"
WORLDS = (NE, MS, AM, CT)
ANCIENT = (NE, MS, AM)

# id: (label as the judge reads it, topic, kind, markers, provenance)
FEATURES: dict[str, tuple[str, str, str, str, tuple[str, ...]]] = {
    # ---- Near East only
    "horses": (
        "horses (kept, ridden or driven)",
        "animals",
        NE,
        "horse horses horseman horsemen steed steeds",
        ("coe1973", "roper:horse", "dale:B:1", "v1:horses"),
    ),
    "chariots": (
        "chariots, carts or other wheeled vehicles",
        "transport",
        NE,
        "chariot chariots wagon wagons waggon waggons cart carts",
        ("coe1973", "roper:chariot", "dale:B:p2", "v1:wheeled_vehicles"),
    ),
    "asses_camels": (
        "asses, mules or camels",
        "animals",
        NE,
        "ass asses camel camels mule mules dromedary dromedaries",
        ("roper:ass", "dale:B:p10", "v1:asses_camels"),
    ),
    "cattle": (
        "cattle (oxen, cows, bullocks)",
        "animals",
        NE,
        "ox oxen cattle kine bullock bullocks heifer heifers cow cows",
        ("coe1973", "roper:cattle", "roper:cow", "roper:ox", "dale:B:p8", "dplace:SCCS244"),
    ),
    "sheep_goats": (
        "sheep or goats",
        "animals",
        NE,
        "sheep goat goats ewe ewes ram_ rams_ lamb lambs",
        ("roper:sheep", "roper:goat", "dale:B:p3", "dale:B:p4", "dplace:SCCS6"),
    ),
    "swine": (
        "swine (hogs, pigs)",
        "animals",
        NE,
        "swine hog hogs pig pigs",
        ("roper:swine", "dale:B:p5"),
    ),
    "wheat_barley": (
        "wheat, barley or other Old World grain",
        "crops",
        NE,
        "wheat barley rye spelt",
        (
            "coe1973",
            "roper:wheat",
            "roper:barley",
            "dale:B:p6",
            "dale:B:p7",
            "dale:C_neg:5",
            "dplace:SCCS1123",
        ),
    ),
    "vine_olive_fig": (
        "grapevines and wine, olives or figs",
        "crops",
        NE,
        "vine vines vineyard vineyards grape grapes olive olives fig figs",
        ("roper:grape", "roper:wine", "v1:vine_olive_fig"),
    ),
    "iron_steel": (
        "iron or steel (tools, weapons, working it)",
        "metals",
        NE,
        "iron steel",
        (
            "coe1973",
            "roper:iron",
            "roper:steel",
            "dale:B:3",
            "dale:B:4",
            "dale:C_neg:7",
            "vogel:ch2",
        ),
    ),
    "brass_bronze": (
        "brass or bronze",
        "metals",
        NE,
        "brass brazen bronze",
        ("roper:brass", "dale:B:p1", "v1:brass_bronze"),
    ),
    "silk_linen": (
        "silk or linen cloth",
        "dress",
        NE,
        "silk silks silken linen flax",
        ("roper:silk", "roper:linen", "dale:B:p9"),
    ),
    "coins": (
        "coined money",
        "money",
        NE,
        "coin coins coined shekel shekels pence penny farthing farthings",
        ("dale:C_neg:15", "dplace:SCCS17", "v1:coins"),
    ),
    "plough": (
        "the plough, drawn by animals",
        "crops",
        NE,
        "plough ploughs plow plows ploughshare ploughshares plowshare plowshares "
        "ploughed plowed ploughing plowing ploughman",
        ("roper:plow", "dale:C_neg:6", "dplace:SCCS243"),
    ),
    "hebrew_rites": (
        "Hebrew rites (sabbath, circumcision, passover, new moons)",
        "religion",
        NE,
        "sabbath sabbaths circumcision circumcised circumcise passover new_moon new_moons",
        ("dale:D_neg:1", "dale:D_neg:3", "vogel:ch3", "v1:sabbath", "v1:new_moons"),
    ),
    "tents": ("tents as dwellings", "buildings", NE, "tent tents", ("roper:tent",)),
    "synagogues": (
        "synagogues",
        "religion",
        NE,
        "synagogue synagogues",
        ("roper:synagogue", "v1:synagogues"),
    ),
    # ---- Mesoamerica only
    "maize": (
        "maize (Indian corn)",
        "crops",
        MS,
        "maize maiz mahiz indian_corn tortilla tortillas",
        ("dale:A:2.22", "dale:C_pos:7", "dale:D_pos:5", "v1:maize"),
    ),
    "beans_squash_chili": (
        "beans, squash or chili peppers",
        "crops",
        MS,
        "beans squash squashes pumpkin pumpkins chili chilli chile frijoles",
        ("dale:C_pos:7", "bom111:wp_mesoamerica_plants"),
    ),
    "cacao": (
        "cacao (chocolate)",
        "crops",
        MS,
        "cacao cocoa chocolate",
        ("bom111:wp_mesoamerica_plants", "v1:nw_plants"),
    ),
    "maguey_pulque": (
        "maguey (agave) and pulque",
        "crops",
        MS,
        "maguey agave pulque octli",
        ("bom111:wp_mesoamerica_plants", "v1:nw_plants"),
    ),
    "cotton": (
        "cotton (cloth, mantles, quilted armour)",
        "dress",
        MS,
        "cotton cottons escaupil escaupiles ichcahuipilli quilted",
        ("dale:C_pos:9", "dale:D_pos:5", "dale:A:4.4", "v1:cotton", "v1:quilted_armour"),
    ),
    "feathers": (
        "feathers and featherwork as dress or ornament",
        "dress",
        MS,
        "feather feathers plume plumes plumage quetzal",
        ("dale:C_pos:6", "v1:feathers"),
    ),
    "jade_greenstone": (
        "jade or green stones prized as jewels",
        "materials",
        MS,
        "jade chalchihuitl chalchihuites chalchiuite chalchiuites greenstone green_stones",
        ("dale:A:5.10",),
    ),
    "obsidian": (
        "obsidian blades or obsidian-edged weapons",
        "warfare",
        MS,
        "obsidian itztli macuahuitl maquahuitl macana macanas",
        ("v1:native_weapons",),
    ),
    "turkeys": (
        "domestic turkeys",
        "animals",
        MS,
        "turkey_ turkeys_",
        ("dale:C_pos:8", "v1:nw_animals"),
    ),
    "dogs_eaten": (
        "dogs raised to be eaten or sacrificed",
        "animals",
        MS,
        "dog dogs",
        ("dale:C_pos:2", "dale:C_pos:3"),
    ),
    "pyramids": (
        "pyramids (stepped temple mounds of stone)",
        "buildings",
        MS,
        "pyramid pyramids teocalli teocallis",
        ("dale:A:3.4", "dale:D_pos:15", "vogel:ch2", "v1:pyramids"),
    ),
    "cement": (
        "cement, lime plaster or stucco in building",
        "buildings",
        MS,
        "cement cemented stucco plaster plaister",
        ("dale:A:6.16", "dale:A:6.17", "roper:cement"),
    ),
    "causeways": (
        "causeways or paved roads",
        "buildings",
        MS,
        "causeway causeways highway highways",
        ("dale:A:6.12", "dale:D_pos:6", "roper:highway", "v1:causeways"),
    ),
    "human_sacrifice": (
        "human sacrifice",
        "religion",
        MS,
        "sacrifice sacrifices sacrificed sacrificing victim victims",
        ("dale:A:2.10", "dplace:SCCS913", "v1:human_sacrifice"),
    ),
    "bloodletting": (
        "drawing one's own blood as an offering",
        "religion",
        MS,
        "bloodletting blood-letting drew_blood drawing_blood their_own_blood pierced_their",
        ("dale:A:3.6",),
    ),
    "meso_calendar": (
        "the native calendar (the 260-day count, katuns, the 52-year cycle)",
        "calendar",
        MS,
        "katun katuns ahau tonalamatl tonalpohualli uinal nemontemi "
        "fifty_two_years fifty-two_years",
        ("dale:A:6.2", "dale:A:6.3", "dale:A:3.18", "v1:meso_calendar"),
    ),
    "codices": (
        "folding books or painted records (codices, picture writing)",
        "writing",
        MS,
        "codex codices painted_books picture_writing hieroglyphical_paintings paintings",
        ("dale:A:5.12", "dale:A:6.9"),
    ),
    "canoes": (
        "canoes",
        "transport",
        MS,
        "canoe canoes periagua periaguas pirogue pirogues",
        ("v1:canoes",),
    ),
    # ---- the 1820s picture of ancient America (beliefs neither real world supports)
    "mounds": (
        "earthen mounds or barrows raised over the dead or as works",
        "buildings",
        AM,
        "mound mounds tumulus tumuli barrow barrows",
        ("vogel:ch2", "v1:mounds"),
    ),
    "picket_forts": (
        "earthwork forts with ditches, banks and pickets",
        "warfare",
        AM,
        "picket pickets palisade palisades palisadoes stockade stockades "
        "breastwork breastworks entrenchment entrenchments intrenchment "
        "intrenchments rampart ramparts",
        (
            "dale:A:4.2",
            "dale:C_pos:17",
            "dale:D_pos:8",
            "vogel:ch2",
            "roper:fortification",
            "v1:picket_forts",
        ),
    ),
    "elephants": (
        "elephants or mammoths known to the people",
        "animals",
        AM,
        "elephant elephants mammoth mammoths mastodon mastodons",
        ("dale:B:2", "roper:elephant", "v1:elephants"),
    ),
    "vanished_race": (
        "an earlier civilised people destroyed or replaced by a later savage one",
        "origins",
        AM,
        "exterminated extermination extinct extirpated annihilated destroyed_by swept_away",
        ("vogel:ch4", "dale:A:2.8", "dale:A:4.6"),
    ),
    "israelite_descent": (
        "descent from the tribes of Israel",
        "origins",
        AM,
        "ten_tribes lost_tribes tribes_of_israel israelites israelite hebrews",
        ("vogel:ch3", "dale:D_neg:1", "dale:D_neg:2"),
    ),
    "metal_plates": (
        "records engraved on metal plates",
        "writing",
        AM,
        "plates plate brass_plates copper_plates",
        ("roper:plate", "v1:metal_plates"),
    ),
    "hebrew_language": (
        "a language that is Hebrew or comes from Hebrew",
        "origins",
        AM,
        "hebrew",
        ("dale:D_neg:2", "dale:B:p11", "vogel:ch3"),
    ),
    "egyptian_script": (
        "writing in Egyptian or Egyptian-like characters",
        "writing",
        AM,
        "egyptian hieroglyph hieroglyphs hieroglyphic hieroglyphics",
        ("dale:B:p11", "dale:A:2.11", "vogel:ch2", "v1:hieroglyphs"),
    ),
    # ---- the writers' own day (the grid's fourth column)
    "firearms": (
        "firearms and gunpowder",
        "warfare",
        CT,
        "gun guns musket muskets firelock firelocks rifle rifles cannon cannons "
        "gunpowder pistol pistols bayonet bayonets artillery",
        ("v1:firearms",),
    ),
    "printing": (
        "printing and printed papers",
        "writing",
        CT,
        "printed printing printer printers newspaper newspapers",
        ("v1:printing",),
    ),
    "modern_money": (
        "dollars, shillings or other modern coin",
        "money",
        CT,
        "dollar dollars cent cents shilling shillings guinea guineas",
        ("v1:coins",),
    ),
}

# D-PLACE (SCCS) codes used as an outside check on the measured world values (not as values).
# feature: (variable, {society: (value as coded, present/absent)}). Read from the data at run time;
# the table here only says how a code maps to present or absent.
DPLACE = {
    "cattle": ("SCCS244", {"Bovine": "present", "Absence or near absence": "absent"}),
    "sheep_goats": ("SCCS6", {"Ovides": "present", "Small Species": "absent"}),
    "coins": ("SCCS17", {"Indigenous coinage/paper currency": "present",
                         "Tokens of conventional value": "absent"}),
    "plough": ("SCCS243", {"Present": "present", "Absent": "absent"}),
    "human_sacrifice": ("SCCS913", {"Present": "present", "Absent or not mentioned": "absent"}),
    "wheat_barley": ("SCCS1123", {"Wheat": "present", "Sorghum": "absent"}),
}  # fmt: skip
DPLACE_SOCIETIES = {"SCCS44": NE, "SCCS153": MS}
