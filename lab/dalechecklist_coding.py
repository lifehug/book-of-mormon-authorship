# ruff: noqa: E501  (the coding table keeps one item a line, for review)
"""BOM-112: fields added to the Dale and Dale checklist, and the keyword rule per item.

Everything here was written by the AI agent (Claude) on 2026-11-21 **from memory**, before any
control text or the Book of Mormon was searched with these rules, and without consulting a
handbook of the ancient Near East or of comparative history. It is labelled so in every output.

Written rules for the two added fields (positive items, Appendix A):

- ``near_east``: **yes** if the feature is stated or plainly shown in the King James Bible (Old or
  New Testament) or is a commonplace of the ancient Near East in the Bible's period (Israel,
  Egypt, Mesopotamia, Persia), so that a reader of the Bible could have met it; **no** if neither;
  **unclear** if only partly, or only under a loose reading.
- ``generic``: **yes** if the feature holds for most pre-modern agrarian states with cities and
  rulers, Old World or New (kings, nobles, taxes, slaves, temples, markets, walls, wars);
  **no** if it is distinctive of few; **unclear** otherwise. A fact of geography or nature counts
  as **unclear** unless it holds for most such states' lands.

Keyword rules (``KEYWORDS``, case-insensitive) pull candidate passages; a window ranks by the
number of distinct terms it holds. ``FEATURE`` restates each item in the agent's own words for the
judging question (no text from the paper or from Coe). Negative items (Appendix B) ask whether a
text asserts the thing existed; their ``NEG_GROUP`` puts items that stand or fall together in one
group (draft animals and chariots; metals; Old World crops and goods; other).

Table columns: id :: near_east :: generic :: keyword regex :: feature (B rows: group, not fields).
"""

from __future__ import annotations

_A = r"""
A:1.1 :: yes :: unclear :: \b(cit(y|ies)|kingdoms?|king of)\b :: Political organization is by independent cities, each with its own ruler and lands, rather than one nation-state.
A:1.2 :: yes :: yes :: \b(capital|chief city|great city|villages|cities round about|chief)\b :: One leading or capital city dominates a group of lesser towns and villages.
A:1.3 :: yes :: yes :: \b(revolt\w*|rebel\w*|went over|dissent\w*|allegiance|joined)\b :: Subordinate cities or groups switch their allegiance to a rival or former enemy.
A:1.4 :: yes :: yes :: \b(judges?|officers?|governors?|laws?|courts?|rulers?)\b :: The society has complex state institutions (judges, officials, laws, a standing army, rulers).
A:1.5 :: yes :: yes :: \bcit(y|ies)\b :: Many cities exist.
A:1.6 :: no :: no :: \blaman\w*\b :: A city whose name has the consonants L-M-N, occupied from early times.
A:1.7 :: unclear :: unclear :: \b(multitudes?|numerous|populous|crowded|thickly|covered the face|face of the (whole )?land)\b :: Parts of the land were very densely settled.
A:1.8 :: yes :: yes :: \b(buil(t|d|ding|dings)|walls?|towers?|palaces?|temples?|public works?)\b :: Large-scale public works were built.
A:1.9 :: yes :: yes :: \b(riches|luxur\w*|costly|precious|ornament\w*|gold|silver)\b :: Some rulers live in luxury.
A:1.10 :: yes :: yes :: \bthrones?\b :: Rulers have elaborate thrones.
A:1.11 :: yes :: yes :: \b(palaces?|courts?|nobles?|princes?|kings?)\b :: There is royalty, with palaces, courts and nobles.
A:1.12 :: yes :: yes :: \b(marr\w*|daughters?|wives|took to wife)\b :: Royal or elite marriages are made for political ends.
A:1.13 :: yes :: yes :: \b(feast\w*|banquet\w*|wine|drink\w*)\b :: Feasts are held for political ends.
A:1.14 :: yes :: yes :: \b(gifts?|presents?)\b :: Gifts are given to a king to gain political advantage.
A:1.15 :: yes :: yes :: \b(factions?|party|parties|followers|contentions?|usurp\w*)\b :: Political factions form around a member of the elite.
A:1.16 :: unclear :: unclear :: \b(strangers?|foreign\w*|usurp\w*|dynast\w*|seized|throne)\b :: Outsiders move in and take over the government, often as a family dynasty.
A:1.17 :: yes :: yes :: \b(officers?|scribes?|nobles?|rulers?|judges?|governors?)\b :: A city's administrative quarter holds officials and aristocrats.
A:1.18 :: yes :: unclear :: \b(records?|chronicles?|annals|reigns?|history)\b :: Records are kept specifically of the reigns of kings.
A:1.19 :: yes :: yes :: \b(tributar\w*|subjects?|vassals?|conquer\w*|bondage|appoint\w*)\b :: After conquest, native leaders are kept on inside the new power structure.
A:1.20 :: yes :: yes :: \b(tribute|tax\w*)\b :: Subjects are required to pay tribute.
A:1.21 :: yes :: unclear :: \b(lineages?|descendants?|tribes?|house of|famil(y|ies))\b :: A small number of important descent lines (patrilineages) dominate.
A:1.22 :: unclear :: unclear :: \b(successor|heir|conferred the kingdom|reign in his stead|appointed .{0,20}king)\b :: There is a king and a designated king-elect (successor) at the same time.
A:1.23 :: yes :: yes :: \b(captains?|generals?|chief captain)\b :: Captains serve kings.
A:1.24 :: yes :: yes :: \b(reign\w* in his stead|dynast\w*|house of|descendants?|son .{0,15}reign\w*)\b :: Political power is held by family dynasties.
A:1.25 :: yes :: yes :: \b(kings? over|under (him|the king)|vassals?|tributar\w*|provinces?|governors?)\b :: Kings rule over subordinate local rulers (subkings), some of noble blood.
A:1.26 :: unclear :: no :: \b(judgment.seat|seat|sat upon the throne|sit (on|upon) the throne)\b :: Taking a seat (being seated) is the term for coming to political power.
A:1.27 :: yes :: unclear :: \b(priests?|high priest|church|chief judge|judges?)\b :: Civil and religious authority are held separately.
A:1.28 :: yes :: yes :: \b(ambiti\w*|aspir\w*|power|seek\w* .{0,10}(power|throne)|desir\w* to be (a )?king)\b :: People of noble birth aspire to power.
A:1.29 :: unclear :: unclear :: \b(like (all )?the nations|after the manner|customs?|imitat\w*|manner of)\b :: Royal courts imitate their enemies.
A:1.30 :: yes :: yes :: \b(household|servants|house of the king|concubines)\b :: Royal courts function as great households.
A:1.31 :: unclear :: no :: \b(interpret\w*|myster\w*|secrets?|hidden|knowledge)\b :: Candidates for high office must hold hidden or secret knowledge.
A:1.32 :: yes :: yes :: \b(slew|murder\w*|conspir\w*|overthr\w*|usurp\w*|assassin\w*)\b :: Dynasties end abruptly.
A:1.33 :: yes :: no :: \bposse\w*\b :: Subject peoples are said to possess the land while ruled by a dominant power.
A:2.1 :: no :: unclear :: \b(ancient|origin|first inhabitants|forefathers|ancestors)\b :: The cultures of the land share a common origin far back in time.
A:2.2 :: yes :: yes :: \b(embass\w*|messengers?|visit\w*|exchang\w*|trade)\b :: Ideas and goods pass actively among the elites.
A:2.3 :: yes :: yes :: \b(strange (wives|women)|daughters? of|took to wife|married)\b :: Elites take foreign brides.
A:2.4 :: yes :: yes :: \b(slaves?|slavery|bondage|bondmen|servitude)\b :: Slavery is practised.
A:2.5 :: yes :: yes :: \b(languages?|tongues?|speech)\b :: Different languages are found in pockets.
A:2.6 :: yes :: no :: \b(flood|deluge|waters .{0,10}(covered|prevailed))\b :: A creation or early story tells of a great flood caused by human wickedness.
A:2.7 :: no :: no :: \b(ships?|vessels?|barges?|voyage|sail\w*|crossed the sea)\b :: The land was settled by people who came across the sea.
A:2.8 :: unclear :: no :: \b(destroyed|destruction|extinct|perished|no more|desolat\w*)\b :: An ancient culture of the land declined steeply and disappeared some centuries BC.
A:2.9 :: yes :: yes :: \b(ranks?|class\w*|nobl\w*|rich|poor|learning|distinctions?)\b :: Strong class distinctions rest on noble birth, wealth and specialised learning.
A:2.10 :: yes :: unclear :: \b(sacrific\w*|offered up|burnt offerings?|children|daughters|women)\b :: Children and others are sacrificed to gods.
A:2.11 :: yes :: no :: \begypt\w*\b :: There are links with Egyptian culture and ideas.
A:2.12 :: yes :: unclear :: \b(depart\w*|journey\w*|built a city|founded|settled|went forth)\b :: Populations move about and found new cities.
A:2.13 :: yes :: yes :: \b(oppress\w*|labou?r\w*|toil|burdens?|poor|ignoran\w*)\b :: There are menial workers, extreme inequality, ignorance and oppression.
A:2.14 :: yes :: yes :: \b(markets?|marketplace|merchandise|buy|sell|traffic)\b :: Marketplaces exist.
A:2.15 :: yes :: yes :: \b(driven|wander\w*|fled|flee|exiles?)\b :: People driven from their homes wander in search of a new home.
A:2.16 :: yes :: unclear :: \b(spacious|elegant|ornament\w*|costly|magnificen\w*|splendo\w*|fine work)\b :: Building is wastefully extravagant.
A:2.17 :: unclear :: no :: \bnorth\w*\b :: Large migrations toward the north are mentioned.
A:2.18 :: unclear :: unclear :: \b(migrat\w*|depart\w*|journey\w*|removed|went forth)\b :: Migrations are constant.
A:2.19 :: yes :: yes :: \b(called the name|after the name|named after|call\w* .{0,20}after)\b :: Cities and lands are named after their founder.
A:2.20 :: no :: no :: \b(west\w*|beyond the sea|across the sea|over the sea|setting sun)\b :: The people say their ancestors came from the west, beyond the sea.
A:2.21 :: yes :: no :: \b(psalms?|songs?|hymns?|sang|poems?|praise)\b :: The people's sacred writing uses poetic parallelism and repetition.
A:2.22 :: unclear :: no :: \b(corn|maize|grain)\b :: Corn (maize) is first among grains.
A:2.23 :: yes :: yes :: \b(wives|concubines|polygam\w*|harlots)\b :: Many wives or concubines are kept, especially by the rich.
A:2.24 :: yes :: yes :: \b(genealog\w*|descendants?|lineage|begat|son of)\b :: It matters to trace one's genealogy to a prominent ancestor.
A:2.25 :: yes :: unclear :: \b(genealog\w*|records?|registers?|priests?)\b :: Priests keep genealogies very carefully.
A:2.26 :: yes :: unclear :: \b(whoredoms?|abominations?|sodom\w*|lewd\w*|lascivious\w*)\b :: Homosexual practice is mentioned.
A:2.27 :: unclear :: unclear :: \b(languages?|tongues?|learning of|characters|interpret\w*)\b :: There is an arcane sacred or prestige language.
A:2.28 :: yes :: unclear :: \b(rebuil\w*|repair\w*|inhabit\w* again|desolate|deserted|abandon\w*)\b :: Old or abandoned cities are repopulated.
A:2.29 :: yes :: unclear :: \b(four (quarters|corners|winds|parts)|quarters of the (earth|land))\b :: The world is divided into four quarters.
A:2.30 :: no :: no :: \b(ancient (people|records|inhabitants|ruins)|ruins|bones|former inhabitants)\b :: People are fascinated by the remains and records of an earlier vanished people of the land.
A:2.31 :: yes :: unclear :: \b(genealog\w*|records?|account of (his|my|our) fathers|history|chronicles?)\b :: Lineage histories dominate the written records.
A:3.1 :: yes :: yes :: \b(temples?|sanctuar\w*|house of (god|the lord))\b :: Temples (ritual centres) are central to society.
A:3.2 :: unclear :: no :: \b(christ|messiah|redeemer|saviou?r|son of god)\b :: The religion holds strongly Christian elements.
A:3.3 :: no :: no :: \b(idolatr\w*|apostas\w*|forsook|new (religion|worship)|dissent\w*)\b :: Popular cults change, and a great highland city declines, around the late centuries BC.
A:3.4 :: yes :: unclear :: \b(mount\w*|hills?|high places?)\b :: Temples are closely tied to sacred mountains or hills.
A:3.5 :: yes :: no :: \b(seers?|stones?|interpreters|urim|thummim)\b :: There are seers and seer stones.
A:3.6 :: unclear :: unclear :: \b(blood|cut themselves|lancets?|gash\w*)\b :: Temple and other rites involve bloodletting.
A:3.7 :: yes :: no :: \b(resurrect\w*|rise (again|from the dead))\b :: People believe in resurrection.
A:3.8 :: yes :: no :: \b(bapti\w*|immers\w*)\b :: There is a baptismal rite.
A:3.9 :: yes :: no :: \b(straight|paths?|walk\w*)\b :: Walking a straight road is a ritual symbol of right living.
A:3.10 :: yes :: no :: \bcovenant\w*\b :: Humans must keep covenants, usually with God.
A:3.11 :: yes :: unclear :: \b(high priests?|chief priests?|priests?|priesthood|levites?)\b :: There are hereditary priests and chief priests.
A:3.12 :: unclear :: no :: \b(opposition|opposites?|contrar\w*|good and evil|light and darkness)\b :: The existence of opposites is an essential part of creation.
A:3.13 :: yes :: yes :: \b(idols?|gods|images?|idolatr\w*)\b :: The religion has many gods and idols.
A:3.14 :: yes :: yes :: \b(sorcer\w*|witch\w*|magic\w*|enchant\w*|soothsay\w*|diviners?)\b :: Sorcery, magic and witchcraft are practised.
A:3.15 :: yes :: no :: \b(sacred|plates|ark|holy things|records|covenant)\b :: A rite renews the community, with sacred objects handed on.
A:3.16 :: yes :: yes :: \b(priests?|kings?|high priest|chief judge|prophets?)\b :: Priestly and political roles are combined or blurred.
A:3.17 :: yes :: yes :: \b(inquir\w*|enquir\w*|oracles?|consult\w*|prophe\w*)\b :: Oracles are consulted for secular guidance and help.
A:3.18 :: unclear :: unclear :: \b(calendar|reckon\w*|computation|times and seasons)\b :: Holy men or priests keep the calendar.
A:3.19 :: yes :: unclear :: \bconfess\w*\b :: Virtuous people confess.
A:4.1 :: yes :: yes :: \b(prisoners?|captives?|tortur\w*|cruel\w*|put to death)\b :: Enemy captives are treated with extreme cruelty.
A:4.2 :: unclear :: unclear :: \b(ditch\w*|trench\w*|breastworks?|palisad\w*|pickets|banks? of earth|ridges? of earth|timbers|fortif\w*)\b :: Defences are earthworks with deep ditches, breastworks and palisades.
A:4.3 :: yes :: yes :: \b(walls?|walled|fenced cities)\b :: Cities are walled, especially in wartime.
A:4.4 :: no :: no :: \b(thick clothing|armou?r|breastplates?|shields?|coats? of mail)\b :: Thick clothing is worn as armour.
A:4.5 :: yes :: unclear :: \b(darts?|javelins?|spears?)\b :: Fighting is done with darts.
A:4.6 :: unclear :: unclear :: \b(wars?|extinct|utterly destroyed|slaughter\w*|exterminat\w*)\b :: Endemic warfare among related peoples destroys the societies.
A:4.7 :: yes :: yes :: \b(ambush\w*|lie in wait|decoy\w*|stratagem\w*|snares?|surround\w*)\b :: Warfare uses ambushes and traps.
A:4.8 :: yes :: yes :: \b(carried (away )?captive|captives?|prisoners?|slaves?)\b :: Raids are made to take captives or slaves.
A:4.9 :: unclear :: unclear :: \b(painted|paint|shorn|naked|skins?|frightful|terrible|mark)\b :: Warriors dress to inspire fear.
A:4.10 :: yes :: yes :: \b(slings?|stones)\b :: Stones and slings are used as weapons.
A:4.11 :: unclear :: no :: \b(cannibal\w*|flesh|devour\w*|eat\w*)\b :: Captives are eaten (cannibalism).
A:4.12 :: yes :: unclear :: \b(burn\w*|destroy\w*|records?|plates?|books?|monuments?)\b :: Records or monuments are deliberately destroyed.
A:5.1 :: yes :: unclear :: \b(highlands?|lowlands?|hill country|valleys?|mountains?|plains?|went (up|down))\b :: The land has highlands and lowlands.
A:5.2 :: unclear :: no :: \b(vapou?r of darkness|smoke|darkness|tempests?|melted|burning|mist)\b :: A volcanic eruption is described.
A:5.3 :: yes :: yes :: \b(famines?|drought|dearth|no rain)\b :: Terrible droughts with famines come at intervals of decades or centuries.
A:5.4 :: yes :: unclear :: \b(serpents?|snakes?|adders?|vipers?|poison\w*)\b :: Venomous, aggressive snakes are present.
A:5.5 :: unclear :: no :: \b(wilderness|lost|forests?|wander\w*)\b :: The wilderness is very thick, it is easy to get lost, and cities lie hidden in it.
A:5.6 :: yes :: unclear :: \b(great city|chief city|capital|highlands?|hill)\b :: A powerful, ancient central city stands in the highlands.
A:5.7 :: yes :: no :: \b(earthquakes?|quak\w*|trembl\w*)\b :: Earthquakes occur and matter.
A:5.8 :: unclear :: unclear :: \b(timber|trees|forests?|cut down|barren)\b :: Large areas are deforested.
A:5.9 :: yes :: unclear :: \b(timber|cedars?|wood|trees|shipping)\b :: Areas are left for forest regrowth, or timber is shipped in from far away.
A:5.10 :: yes :: yes :: \b(precious stones?|jewels?|gems?|jade)\b :: Precious stones exist.
A:5.11 :: no :: no :: \b(sunk|depths of the sea|buried|swallowed|waters .{0,15}(came|come) up)\b :: Cities are sunk under water.
A:5.12 :: yes :: yes :: \b(paper|parchment|bark|scrolls?|books?|perish\w*)\b :: Writing materials are perishable.
A:5.13 :: yes :: yes :: \b(gold|refin\w*|fine gold)\b :: Refined gold is present.
A:6.1 :: unclear :: unclear :: \b(millions?|thousands?|numerous|multitudes?)\b :: The area holds millions of inhabitants.
A:6.2 :: yes :: yes :: \b(day of the \w+ month|\w+ month|month of the \w+ year)\b :: The calendar is kept by day, month and year.
A:6.3 :: unclear :: unclear :: \b(reckon\w*|computation|calendar|from the time|commencement)\b :: Several calendars are kept.
A:6.4 :: yes :: unclear :: \b(bees?|honey)\b :: Bees are kept and honey is produced.
A:6.5 :: yes :: yes :: \b(carv\w*|engrav\w*|paint\w*|danc\w*|music\w*|workmanship)\b :: There is art: carving, painting, dancing, metalwork, music.
A:6.6 :: yes :: unclear :: \b(stars?|planets?|moon|heavens|sun)\b :: People know the movements of the stars, planets and moon.
A:6.7 :: unclear :: no :: \b(writ\w*|characters|letters|engrav\w*)\b :: Writing is present, and its origins are complicated.
A:6.8 :: yes :: unclear :: \b(engrav\w*|graven|inscri\w*|stone)\b :: Writing is engraved on stone.
A:6.9 :: unclear :: unclear :: \b(books?|records?|librar\w*|deposit\w*)\b :: Many books exist, some kept in repositories.
A:6.10 :: yes :: yes :: \b(trade|traffic|merchandise|goods|merchants?)\b :: A variety of goods is traded.
A:6.11 :: yes :: yes :: \b(merchants?|traders?|traffic\w*)\b :: There are many merchants.
A:6.12 :: yes :: yes :: \b(roads?|highways?|causeways?)\b :: Roads and causeways are built.
A:6.13 :: yes :: yes :: \bgardens?\b :: Houses have gardens attached.
A:6.14 :: unclear :: unclear :: \b(languages?|tongues?|letters|teach\w* .{0,20}(language|tongue))\b :: New rulers impose a new language or writing system on the native people.
A:6.15 :: unclear :: no :: \b(altered|changed|corrupt\w*|reformed|languages?)\b :: The writing system changes markedly over time.
A:6.16 :: unclear :: unclear :: \b(cement|mortar|plaster|plaister|lime)\b :: Buildings are made of cement.
A:6.17 :: unclear :: unclear :: \b(cement|mortar|plaster|plaister|stucco|lime)\b :: People are highly skilled in working cement (stucco).
A:6.18 :: yes :: yes :: \b(workmanship|curious|skill\w*|cunning work|exceedingly fine)\b :: Workmanship is excellent.
A:6.19 :: yes :: unclear :: \b(ships?|shipping|vessels?)\b :: Trade goods travel by sea.
A:6.20 :: no :: no :: \b(box|chest|hid up|buried|cave)\b :: Books are stored underground in lidded stone boxes.
A:6.21 :: yes :: yes :: \b(towers?|watch\w*)\b :: Towers are built, some very tall, possibly watchtowers.
A:6.22 :: yes :: yes :: \b(gates?|entrances?|entr(y|ies)|passes?)\b :: Settlements have several formal entrances.
A:6.23 :: yes :: yes :: \b(fine linen|linen|apparel|raiment|silks?|garments?|cloth\w*)\b :: There are fine fabrics and elaborate clothing.
"""

_B = r"""
B:1 :: animals :: \bhorses?\b :: Horses existed among the people.
B:2 :: animals :: \belephants?\b :: Elephants existed among the people.
B:3 :: metals :: \biron\b :: Iron existed among the people.
B:4 :: metals :: \bsteel\b :: Steel existed among the people.
B:5 :: metals :: \bcopper\b :: Copper existed among the people.
B:6 :: metals :: \b(gold|silver)\b :: Refined gold and silver existed among the people.
B:p1 :: metals :: \bbrass\b :: Brass existed among the people.
B:p2 :: animals :: \bchariots?\b :: Chariots existed among the people.
B:p3 :: animals :: \b(sheep|flocks?)\b :: Sheep existed among the people.
B:p4 :: animals :: \bgoats?\b :: Goats existed among the people.
B:p5 :: animals :: \b(swine|hogs?|pigs?)\b :: Swine existed among the people.
B:p6 :: crops :: \bwheat\b :: Wheat existed among the people.
B:p7 :: crops :: \bbarley\b :: Barley existed among the people.
B:p8 :: animals :: \b(cattle|oxen|ox|cows?|kine)\b :: Cattle (oxen, cows) existed among the people.
B:p9 :: crops :: \bsilks?\b :: Silk existed among the people.
B:p10 :: animals :: \b(ass|asses|donkeys?)\b :: Asses (donkeys) existed among the people.
B:p11 :: other :: \b(egyptian|hebrew|reformed|characters|language)\b :: The people wrote in a mixed Egyptian and Hebrew script or language.
B:p12 :: other :: \b(israel\w*|jews?|hebrews?|jerusalem|descend\w*|seed of)\b :: The native people descend from migrants from the Middle East (Israel).
"""


def _rows(table: str, n: int) -> list[list[str]]:
    rows = [[c.strip() for c in line.split(" :: ")] for line in table.strip().splitlines()]
    bad = [r[0] for r in rows if len(r) != n]
    if bad:
        raise ValueError(f"malformed coding rows: {bad}")
    return rows


ADDED: dict[str, dict] = {}
KEYWORDS: dict[str, str] = {}
FEATURE: dict[str, str] = {}
NEG_GROUP: dict[str, str] = {}
CATEGORY: dict[str, str] = {}
for _id, _ne, _gen, _kw, _feat in _rows(_A, 5):
    ADDED[_id] = {"near_east": _ne, "generic": _gen}
    KEYWORDS[_id] = _kw
    FEATURE[_id] = _feat
for _id, _grp, _kw, _feat in _rows(_B, 4):
    NEG_GROUP[_id] = _grp
    KEYWORDS[_id] = _kw
    FEATURE[_id] = _feat
VALUES = ("yes", "no", "unclear")
