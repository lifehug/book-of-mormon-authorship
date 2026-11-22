# Redesign: the geography test (BOM-116)

2026-11-22. Research and design only, asked for by the owner. Nothing here was run on the Book of
Mormon. Counts marked "feasibility" were taken on the real files in a few minutes. Web sources were
read by an AI research agent and not checked by a person; "to verify" marks what was not reached.

## The claim and where it comes from

Two claims are tangled together, and the camps disagree on both.

1. **The book has one consistent internal map.** John Sorenson (*Mormon's Map*, FARMS 2000) and
   John Clark ("A Key for Evaluating Nephite Geographies", 1989; revisited 2011) built a map from
   the text alone, before putting it on any real ground. Clark reduced it to ten points: a narrow
   neck with an east sea and a west sea, between a land northward and a land southward; a long
   west coast; wildernesses of stated widths; Zarahemla in a river basin and Nephi in a highland
   valley; the river Sidon running from a southern wilderness near Manti; a highland lake (the
   waters of Mormon) a day or two from Nephi; Nephi about three weeks' travel south of
   Zarahemla; Bountiful several days north of Zarahemla near the neck; Cumorah in the land
   northward near the east sea. He measures distance in "units of standard distance", one day's
   normal travel over flat land, with rules for wilderness and army speed. Their point is that
   hundreds of passages, scattered across a long dictated text, never contradict this map.
2. **The map fits a real region.** Sorenson places it in southern Mexico and Guatemala, with the
   Isthmus of Tehuantepec as the narrow neck (*An Ancient American Setting*, 1985; *Mormon's
   Codex*, 2013). Others place it around the Great Lakes, or in the Mississippi valley (the
   "Heartland"), or across the whole hemisphere with Panama as the neck. Critics answer in two
   ways: a consistent invented map is easy for a careful storyteller, and the Mesoamerican fit
   needs the book's "north" to be turned by roughly 45 to 90 degrees (Deanne Matheny, "Does the
   Shoe Fit?", 1993; Sorenson's reply "Vive Zapato!", 1994).

What the world would look like if each were right:

- If the map is consistent *and constraining*, it should rule out most of the earth's land: only
  a few places would have two seas, a neck, a river basin below a highland, at the stated scale.
  A region that satisfies it would then be worth something.
- If it is consistent but loose, many places satisfy it and a fit is cheap. Both camps could
  then be right about "it fits" and the fit would mean little.
- If consistency is what any careful author produces, real-land texts and invented-land texts
  should look the same on it, and consistency alone would say nothing about which kind the book
  is.

No one, on either side, has measured how many regions of the earth satisfy the internal map, or
how real and invented geographies compare on consistency. That is the gap.

## What we did and how it failed

The first design (`lab/geography.py`; result `data/lab/setting/geography/result.json`; card in
the private repository under `lab/owner/2026-11-21-geography/`) pulled statements out of each
text with one written rule (A north of B, up from A to B, N days' journey, by the sea, near, a
narrow neck), then for a region let an optimiser give each named place its best real site from a
few hundred GeoNames towns, and scored the share of statements satisfied against 400 random
windows of the earth.

- The extractor worked: with the Bible's true coordinates (OpenBible.info) 71% of its statements
  hold, against 29% for random placements (99.7th percentile).
- The region step failed its known answer. The Bible's narrative put Palestine at the 70th
  percentile of decoy windows (bar 95); Josephus 44 and 77; Clavigero's Mexico 94; Ramsay's
  Philadelphia 59; Thomson's Niagara 55. The decoy median score was almost the same as the true
  region's in every text. The Book of Mormon was not scored against any region.
- What was measured on the book: 33 statements over 23 places (14 directions, 12 by the sea,
  6 near, 1 narrow neck); none in a contradiction; 7 unlinked groups. The rule read only
  sentences naming both places, so Alma 22's long description was missed, and Teancum, Moroni
  and Lehi were counted as places.

## Replicating their approach

**There is no statistical method to rerun.** On both sides the claim is argued by reading. Each
author reads the text, lists the passages that give directions or distances, infers a map, and
then compares the map with a real region, point by point. Nothing is counted against chance.

- **Clark (1989, revisited 2011).** Data: the Book of Mormon text, chiefly the passages that give
  relative directions and distances. Method: read them; turn travel reports into "units of
  standard distance" (one day's normal travel on flat land; wilderness travel counts at half;
  armies at 150-200% of normal speed; about 1.5 units between neighbouring forts); draw an
  internal map; reduce it to ten points; then grade proposed real-world geographies against the
  ten points. In 1989 he graded Sorenson's and Hauck's. His numbers include: neck about 4 units
  wide; Nephi to Zarahemla about 9 units (reduced from the reported 21 days of travel with
  flocks); Bountiful to Moroni about 5; Manti to the west sea about 6.5; the southern wilderness
  at least 9 wide; Cumorah about 6 from Bountiful. Verdict: a coherent internal map, which
  Sorenson's model meets better than Hauck's.
- **Sorenson, *Mormon's Map* (2000).** The same kind of reading at book length, internal map
  first, no real region in that book (to verify in the PDF). The real-world placements are in
  *An Ancient American Setting* (1985) and *Mormon's Codex* (2013), argued by matching features
  (the Tehuantepec isthmus, the Grijalva basin, the Guatemalan highlands) and by explaining the
  turned directions.
- **The Heartland and Great Lakes authors.** Argued from a few named features (the Mississippi as
  the Sidon, the New York hill as Cumorah) and from statements by early church leaders. No
  internal-map method to rerun.
- **Matheny (1993).** Checked Sorenson's model against the text's directions and found it needs a
  turned "north". Also by reading.

**Can it be reproduced with what we hold?** Yes, faithfully, without buying anything. Clark's
key and its rules are free to read; the 1830 text is held; each setting's region and orientation
is in public summaries. The faithful replication is two steps, done his way:

1. **Rebuild Clark's internal map from the text by his rules.** Our coded statement table
   (design step 2 below) is read the way Clark read it: travel times turned into his units with
   his allowances, the ten points derived from the statements. Reported: which of Clark's ten
   points our table reproduces, which it does not, and every statement that bears on each, with
   references. This checks the consistency claim the way its authors made it, and shows whether a
   second reader arrives at the same map.
2. **Grade each proposed setting against the ten points, as Clark graded Sorenson and Hauck.**
   Pass / fail per point for Mesoamerica (Tehuantepec), the Great Lakes, the Heartland and the
   hemispheric model, each at its authors' orientation, using the real coastline, relief and
   rivers. Reported as Clark would: points met, points missed. Hauck's model (1988) is not held
   and is graded only if a public summary of its placements is found.

**Did we do this?** No. The first design went straight to our own instrument and never
reproduced Clark's map or his grading. The redesign does it first.

What the replication cannot give: a chance baseline. Clark's grading says whether a region meets
the points, not how many other regions would. That is the step our own instrument (Part A) adds.

## What the failure says

**About the published claims and their method (a).** The published fits work the way our
optimiser did: choose a region, then choose a site in it for each place. Our failure shows that
with that freedom, statements of the common kinds (a direction within a wide cone, "near", "by
the sea") can be met almost anywhere. That is a finding about the *method of arguing from a fit*,
on any side: a good fit to one region is not evidence until someone shows how badly the same
statements fit everywhere else under the same freedom. No published geography we found reports
that comparison. The failure does **not** show that the book's map is loose or that no region
fits; we never built the book's strong statements (the neck's width, two seas, the river's
course, highland and lowland, the scale in days).

**About our instrument only (b).** Nearly all of the blame is here. (1) Wrong unit: single
sentences naming both places, so the book gave only 33 statements, none of up/down or days;
the Bible gave 75, mostly weak. (2) Weak predicates: "near" (50 km) and "by the sea" (a GeoNames
cape or bay within 25 km; 93% of decoy windows had one) carry almost no information. (3) No
real coastline, no elevation surface, no river courses: coasts were points, rivers were points,
heights were town elevations. (4) The optimiser had a few hundred sites per place, which is far
more freedom than the statements could pay for. (5) Setting windows were placed from memory.

**Unknown (c).** Whether a full, hand-checked table of the book's strong statements picks out
few regions or many; whether it fits any region at all under a literal reading of its
directions; and whether internal consistency differs at all between real and invented
geographies. Sorenson's and Clark's statement that the map is consistent across "several hundred"
references has not been checked by us: we extracted 33.

## Angles considered

1. **Score each published model's placements against random placements** (the first card's
   "Next" step). Cheap if the placements are in hand, but circular as evidence about the region:
   placements chosen to fit the text will always beat random ones, in any region. It is a fair
   *audit* (how many statements each model breaks, on one common table) and is kept as an add-on,
   not as the test.
2. **Count how many regions of the earth satisfy the map's strong features** ("specificity").
   Code the features that cannot be met just anywhere (a neck of a stated width between two
   seas; seas on stated sides; a river with a stated course; up and down; distances in days),
   and test them against a real coastline, an elevation surface and river courses, in windows
   at the text's own scale, over the whole land surface. The share of windows that pass is how
   constraining the map is; whether a proposed region is among them is a separate yes / no.
   This answers "how constrained is the map" and "does a region fit" in one measure, and has a
   clean known answer: the Bible's features must pick out Palestine and few other places.
   **Chosen.**
3. **Consistency per opportunity, against real and invented geographies.** Count how many times
   a text's statements *could* have contradicted each other (a relation implied by two others,
   a travel time that must obey the triangle rule), how often they do, and how much of the map
   is fixed. Compare real travel narratives and histories with invented-land fiction. This tests
   the consistency claim directly, and the critics' "consistent invented maps are easy". The
   known answer is the separation itself: if real and invented do not differ, consistency is
   not evidence either way and we say so. Research on mental maps predicts real-land writers
   err too: people distort directions toward the larger unit (Stevens and Coupe 1978; Tversky
   1992), and the Bible's own table has a small cycle (the Gihon), while an author who draws a
   map first (Stevenson with *Treasure Island*) can be perfectly consistent; Baum's Oz shows the
   opposite, with east and west swapped between text and map. **Chosen as the second part,**
   using the same coded tables.
4. **Known-land versus imagined-land style.** Do real-land writers use more absolute bearings,
   more distances, more landmarks independent of the plot, more stated travel times? Feasible
   with counts (see feasibility below), but the counts mostly measure genre (journal against
   romance), not whether the land is real. Folded into part 3 as description only.
5. **The one anchored stretch: 1 Nephi's journey from Jerusalem** (south-southeast, then nearly
   eastward to a coast). The only part with real anchors, but it has about five statements, and
   whether such a route was knowable in 1829 is a different question (sources, as in BOM-110).
   Not chosen.
6. **Lost-city location models.** Barjamovic, Chaney, Coşar and Hortaçsu (2019) located lost
   Bronze Age cities from Old Assyrian merchant records with a gravity model, checked on cities
   whose sites are known; Ptolemy's coordinates have been rectified to modern places by fitting
   systematic distortions (Kleineberg, Marx, Knobloch and Lelgemann 2010; Marx 2012). Both need
   known anchor places to tie the text to the ground. The book's New World has none, so these
   cannot locate it; they do supply the right check (hold out known places, predict them) and
   the right warning (fits without anchors are under-determined). Not chosen.

The narrative-cartography literature (Moretti's *Atlas of the European Novel*; Piatti's
*Literary Atlas of Europe*; Caquard 2013 and Caquard and Cartwright 2014; Ryan, Foote and
Azaryahu 2016, where readers drew different maps of the same novel) maps stories onto known
places or studies readers' mental maps. It offers vocabulary (setting, zone of action, route,
projected place) but no test of whether an unnamed map is real. Qualitative spatial reasoning
(Frank 1991; Ligozat 1998) supplies the machinery for part 3: cardinal-direction relations as a
constraint network, with standard checks for contradiction and for what the network implies.

## The proposed design

**Question (one sentence).** How many regions of the earth satisfy the strong geographic
features the 1830 text states, at the text's own scale; is each proposed setting among them; and
does the book's internal consistency look more like real-land or invented-land writing, if those
two differ at all?

### Step 1: reproduce their result their way

Before our own instrument: rebuild Clark's internal map from the coded 1830 table by his rules
(his day units and allowances), report which of his ten points it reproduces, and grade each
proposed setting against the ten points, pass / fail, as he graded Sorenson and Hauck (see
"Replicating their approach"). Its known answer: the same procedure, applied to the Bible
narrative's coded table, must yield Palestine's basic layout (the great sea west, the Jordan
running south into the salt sea, the hill country up from Jericho) and grade Palestine as
meeting it. Reported in full whatever Parts A and B later show.

### Part A: specificity (how constraining the map is)

1. **Coded statement tables, one per text, from the text only.** Every passage with a place cue
   (feasibility: 328 of the 1830 text's 1,165 paragraphs, about 100,000 words) is read in windows
   of about 400 words by the paced model judge (`lab/judge.py`, simulated reading), which returns
   typed relations with references and no free text: direction (8 sectors), up/down, days of
   travel between named places (with who travelled: group with flocks, army, messenger), by
   which sea and on which side, a narrow neck and what lies on each side, a river's head and
   where it runs, a wilderness strip and what it runs between. A second, independent reading
   (a different prompt, or the assistant, as in BOM-118) covers at least 20% of windows; their
   agreement is reported. Places are names fixed by a list made before reading (people's names
   that double as place names, like Moroni, are resolved by "land of / city of").
2. **Readings, fixed before any geography is computed.** The camps differ on interpretation,
   so each is coded as its own feature set and all are reported: (i) *literal*: north means
   north, "sea north" and "sea south" (Helaman 3:8) are real seas; (ii) *Clark's key as
   published* (1989/2011), taken from his ten points and his day units, which is a proponent's
   reading fixed decades before this test; (iii) *orientation free*: the same features with the
   map allowed to rotate (this is the reading the Mesoamerican model needs, per Matheny's
   critique), so the cost of rotation in specificity is measured rather than argued.
3. **Features to geometry.** Each feature becomes a test on real geography: a land neck with
   water on two opposite sides narrower than its stated crossing allows; sea within a stated
   distance in a stated sector; a river course with its head in the stated direction; one area
   higher than another; two areas a stated number of days apart (with a range of kilometres per
   day fixed in advance, for each kind of traveller). Data: Natural Earth 1:10m coastline, land,
   rivers and lakes; the ETOPO 2022 relief surface; optionally HydroRIVERS for flow direction.
4. **Windows.** Square windows at the text's own scale (set from its day counts and the
   kilometres-per-day range), centred on a grid over all land, at 8 rotations where a reading
   allows rotation (one where it does not). **Specificity** = share of windows in which every
   feature can be met. Places are not optimised one by one over towns: a feature is met if
   *some* layout meeting all features at once exists in the window, found by a small search over
   a coarse grid of points with the full set of constraints. This is the step the first design
   lacked: freedom is counted, and the count is the result.
5. **Settings.** Each proposed setting is read as a window centred where its authors put the
   centre of the map, at the rotation they use. Only the region and its orientation are needed,
   which are public in summaries; no per-place table is needed for Part A.

### Part B: consistency per opportunity

From the same tables: (1) *opportunities*: each stated relation that is also implied by others
(a cardinal-direction network closed under composition, Ligozat 1998), and each triangle of
stated travel times; (2) *contradictions* per opportunity; (3) *rigidity*: share of place pairs
whose north-south or east-west order the table fixes. Subsampled to the book's number of
statements, so long texts do not win by size.

Panel (feasibility counts of compass words per 10,000 words in brackets; the book has 8.4):

- *Real land, first-hand:* Bible narrative books; Josephus, *War* (a translation); Xenophon's
  *Expedition of Cyrus*, 1813 translation (7.6; a translation; held); Carver 1781 (36.5); Pike
  1810 (29.7); Lewis and Clark, *History of the Expedition* (22.7); Mackenzie 1801; Park 1799.
- *Real land in Bible style:* Hunt, *The Late War* (1816); *The First Book of Napoleon* (1809).
  Both held.
- *Invented land:* Spalding's manuscript (4.7); *Gulliver's Travels* (7.4); *Peter Wilkins*
  (3.9); Holberg's *Niels Klim*, 1828 (1.9); More's *Utopia* (0.4); *Treasure Island* (held in
  Institutional Books; map drawn first, by Stevenson's own account). Pre-1830 invented fiction
  is thin in directions, so add public-domain later texts with dense invented geography:
  Verne's *Mysterious Island*, Baum's first two Oz books, Burroughs's *A Princess of Mars*
  (Project Gutenberg; to fetch).
- *Real land, never visited by the author (hard case):* Defoe's *Captain Singleton* crossing of
  Africa (21.1; held); Fénelon's *Telemachus* (0.6; too thin, report only).

Joseph Smith's other dictations hold almost no geography (the Book of Abraham's opening is the
one stretch); report if it yields at least the minimum number of statements, otherwise "does not
apply".

## Known-answer check

Bars fixed here, before anything is computed for any text.

**Extractor (both parts).** The coded tables for the Bible narrative and Xenophon, scored with
true coordinates (OpenBible.info for the Bible; the standard route for Xenophon from a
public-domain atlas or Wikipedia's route list, to verify), must hold for at least 80% of
statements and beat 1,000 random placements at the 99th percentile. Agreement between the two
readings on a shared sample at least 0.7 (Cohen's kappa on relation type and value).

**Part A, specificity.** Known texts: Bible narrative (Palestine), Josephus *War* (Palestine;
the translation control), Xenophon (the route from Sardis to the Black Sea), Lewis and Clark
(the Missouri to the Pacific), Hunt's *Late War* (the Niagara and Lake Erie frontier; the
Bible-style control). Each passes if its own region satisfies its features **and** at most 5%
of land windows at its scale do. The check passes if the Bible passes and at least 4 of the 5
do.

- **Hard decoy that the first design got wrong.** The first design put Palestine at the 70th
  percentile from the Bible. The same Bible table restricted to the *weak* kinds only (near, by
  the sea, wide-cone directions) must come out *unspecific* (more than 25% of windows satisfy
  it). Passing on strong features while failing on weak ones is the evidence that specificity
  comes from features we can name, not from a quirk of the counting. If the weak table also
  comes out specific, the counter is wrong and the run stops.
- **Rotation check.** The Bible's true layout rotated by 90 degrees must fail Palestine under
  the literal reading and pass under the orientation-free reading.
- **Invented maps, reported, no bar.** Spalding, *Gulliver* (Lilliput and Blefuscu), *Treasure
  Island*, *Mysterious Island*: their share of satisfying windows shows what chance fits of
  invented maps look like at their scale. If invented maps routinely fit 1-5% of the earth, a
  real-region fit at that level cannot tell real from invented.

**Part B, consistency.** Real (first-hand, at least 6 texts) against invented (at least 6
texts), on contradictions per opportunity: the measure counts as discriminating if the two
groups separate with a rank AUC of at least 0.8 (the chance that a random real text has fewer
contradictions per opportunity than a random invented one). Below 0.8, Part B gives no verdict
on the book; its figures are printed as description, and the write-up says that consistency did
not tell real from invented in this panel.

If the extractor check or Part A's check misses, the book is not scored on Part A. The two parts
stand or fall separately.

## What each outcome would mean

Part A, for each reading:

- **Specific, and a setting is among the satisfying windows** (at most 5% of windows; setting
  inside): the map is constraining and that setting meets it. The fit is worth about as much as
  the rarity (1 in 20 or rarer). Several settings at once would mean the text does not choose
  among them.
- **Specific, and no proposed setting satisfies it:** each setting breaks at least one strong
  feature under that reading; the features broken are listed.
- **Satisfied nowhere:** the reading fits no real land at this scale. Compared with the invented
  maps' rates, this could mean an impossible literal reading, an invented map, or a coding
  error; the write-up lists which features no window meets.
- **Unspecific** (more than 25% of windows): the map does not pick out a region; arguments from
  fit under that reading carry little force, on any side.
- **Between 5% and 25%:** a weak constraint; reported as such, no verdict.
- **Cannot tell:** the check missed, or the readings disagree so that the answer depends on
  interpretation; the latter is itself reported as the finding.

Part B: if the measure discriminates, the book's contradictions per opportunity and rigidity are
placed against both groups, with "more like real", "more like invented" or "between". If it does
not discriminate, the answer to the consistency claim is that consistency is not evidence either
way, which is what the critics' "easy" argument predicts and what the proponents' argument needs
to rule out.

## Risks

- **The reader knows the answer.** The model judge knows Palestine and knows the published
  Book of Mormon maps; it may code from memory. Mitigation: every relation must cite its
  reference; a sample is checked against the verse; the second reading is blind to the first;
  coding prompts never name a region.
- **Interpretation is the dispute.** The camps differ mainly on readings (rotated directions,
  "sea north"). Coding several fixed readings shows how much the answer depends on reading; it
  cannot say which reading is right.
- **Tuning on known texts.** Feature tolerances (kilometres per day, neck width, "near the sea")
  are fixed before any window is counted; if the check misses, a revision is allowed only from
  the known texts and is recorded as made after seeing them.
- **Modern geography for an ancient text.** Coastlines are close to modern for the last 2,500
  years, but rivers move (the Grijalva, the Usumacinta, the Mississippi). Rivers are tested by
  basin and general course, not channel.
- **Scale.** The day counts are few and depend on who travelled; scale is a range, and results
  are shown across it.
- **Many comparisons.** Three readings, five settings, two parts. All are reported in one table;
  none is picked as the headline.
- **The panel is uneven.** Invented geography before 1830 is thin (feasibility below), so later
  fiction is used; it differs in era and genre from the book.

## Feasibility (measured 2026-11-22, minutes of Mac time)

- The 1830 body text: 272,220 words, 230 compass words (8.4 per 10,000), 328 of 1,165 paragraphs
  with a place cue (about 100,000 words). 33 sentences link a stretch of travel to a number of
  days; none names both ends as "N days' journey".
- Compass words per 10,000 words in candidate texts: Carver 36.5, Pike 29.7, Lewis and Clark
  22.7, *Captain Singleton* 21.1, Xenophon 7.6, *Gulliver* 7.4, Spalding 4.7, *Peter Wilkins*
  3.9, *Last of the Mohicans* 3.4, *Niels Klim* 1.9, *Telemachus* 0.6, *Pilgrim's Progress* 0.4,
  *Utopia* 0.4. Real travel writing is three to five times as dense as the book; pre-1830
  invented fiction is at or below it.
- Held in the library: all of the above, plus *Treasure Island*, *The First Book of Napoleon*,
  Hunt's *Late War*, Josephus. Not held: Verne, Baum, Burroughs (Project Gutenberg, public
  domain in the United States).
- On disk: GeoNames only. No coastline, elevation surface or river courses.

## Open physical data: what could be tested exhaustively

Added 2026-11-22 at the owner's request: can open elevation, lidar, map, site and radiocarbon data
test the geographic claims across the whole earth, beyond reading the text? Research only;
nothing downloaded. Licences are as the providers state them; "verify" marks what the agent
could not confirm from the provider's own page.

**The short answer.** Three things can be tested exhaustively, on a Mac, in days: the terrain
(Part A above, with better data), the settlement record over time from open radiocarbon dates
(a new Part C), and a known-answer case in the Near East where an open, dated gazetteer exists.
Two things cannot be tested that way with open data: finding mounds and forts ourselves from
lidar across whole regions (a research programme, and the open lidar is very uneven between the
United States and Mexico/Guatemala), and matching the book's places to particular sites (the
book names no place that survives on the ground, and the site files that would be needed are
closed to protect the sites). One principle runs through all of it: physical data can say whether
a region *had* the kind of land, people and works the text describes, at the stated time. It
cannot say whether the text was *about* that region, because a writer living among the Ohio
mounds would also produce a text that "fits" Ohio. Spalding's manuscript, set among those mounds,
is the hard decoy for every test in this section.

### 1. Elevation and lidar

| Data | Coverage | Open? | Licence |
| --- | --- | --- | --- |
| Copernicus DEM GLO-30 / GLO-90 | global, 30 m / 90 m | yes, anonymous download (AWS `copernicus-dem-30m`) | Copernicus DEM licence, free for any use with attribution; a few tiles withheld; check the current licence text |
| SRTM (NASA) | 60°N-56°S, 30 m | yes | public domain (US government) |
| ETOPO 2022 (NOAA) | global land and sea floor, 15-60 arc-seconds | yes | public domain |
| USGS 3DEP lidar | most of the conterminous US, point clouds and 1 m DEMs | yes, AWS `usgs-lidar-public` (no account) and The National Map | public domain |
| INEGI LiDAR DEM | parts of Mexico (5 m terrain and surface models; Tabasco, Chiapas and others) | downloadable from INEGI | INEGI's free-use terms (verify the product's terms) |
| NASA G-LiHT | flight transects in the US, Puerto Rico and Mexico (Yucatán peninsula, 2013) | yes, glihtdata.gsfc.nasa.gov | NASA open data; acknowledge funders |
| PACUNAM lidar (northern Guatemala, about 2,144 km²) | Maya Biosphere Reserve | **no**: published as results and figures, not as open data | restricted |

**What it would test.** Clark's features (a highland valley above a river basin; "up" from
Zarahemla to Nephi; a neck between two seas) and every Part A elevation feature. Global DEMs at
30-90 m are more than enough at the book's scale of days of travel. This is a straight upgrade of
Part A's data: GLO-90 for relief (about 15 GB for the land surface at 90 m, or ETOPO at 30
arc-seconds, a few GB). Feasible on the Mac in days.

**Detecting mounds ourselves.** Realistic only as a pilot. Mounds and earthworks show clearly in
1 m 3DEP lidar (the Newark and Chillicothe earthworks are standard examples), and automated
detection has been published in the US, Scandinavia and the Maya lowlands, always with many false
positives that need checking by eye or on the ground. An exhaustive scan of the Ohio and
Mississippi valleys is terabytes of point clouds and months of validation; it would also give
shape without date, while every claim here is about a date. In Mexico and Guatemala the open
lidar is transects (G-LiHT; Golden and colleagues found pre-Columbian features in them in 2016)
and patches (INEGI), not wall-to-wall, so any count compared between regions would measure lidar
coverage, not ancient people. **Derived site inventories and published syntheses are the right
resource; our own lidar detection is not.** A pilot (detect the known Newark and High Bank
enclosures from 3DEP tiles; count false positives in a nearby window with no recorded works) is
a few days and would only show what such a scan could do.

### 2. Site and earthwork inventories

| Source | What | Open? |
| --- | --- | --- |
| DINAA (Digital Index of North American Archaeology, on Open Context) | state site-file records for much of the eastern US, with site types and periods | **counts and types yes, locations no**: precise coordinates are withheld; records are tied to counties or coarse areas. Per-state licences on Open Context (Georgia: public domain; others to check) |
| State site files (SHPOs) | exact locations | **no**: restricted to qualified archaeologists by law, to protect sites from looting |
| Squier and Davis, *Ancient Monuments of the Mississippi Valley* (1848) | over a hundred surveyed works with plans (count to verify), many in Ohio; walls, ditches, gateways | public domain (Project Gutenberg 49668; Smithsonian repository). After 1830, but a full survey of what stood |
| Cyrus Thomas, *Catalogue of Prehistoric Works East of the Rocky Mountains* (Bureau of Ethnology, 1891) and his 1894 mound report | a county-by-county list of known mounds and enclosures | public domain (archive.org; to locate) |
| Before 1830, held in our library | Atwater in *Archaeologia Americana* (1820); Haywood (1823); Yates and Moulton (1824) | held; these show what a reader in 1829 could know |
| Electronic Atlas of Ancient Maya Sites (Witschey and Brown) | about 6,000 Maya-area sites with coordinates and rank | KML at mayagis.smv.org; a copy on Data Basin says CC BY 3.0 (verify with the authors). Undated: rank, not period |
| INAH | Mexico's official register of archaeological zones | the public list is only the zones open to visitors (about 190); the full register is not open |
| Wikidata / OpenStreetMap archaeological sites | global, uneven | open (CC0 / ODbL); biased to famous and tourist sites |
| Pleiades | about 40,000 ancient places of the Greek and Roman world and the Near East, with periods of attestation | yes, CC BY, full dumps on Zenodo and GitHub |

**What it would test.** Not the book's places one by one (none can be tied to a site). Only
aggregate statements: the region held many cities and fortified places in the book's period, in
a pattern with the land northward and southward and a neck between. The Heartland and Great Lakes
authors (Meldrum, May, Neville; Olive, Aston) point to the eastern mounds and earthworks as the
book's peoples' works; Sorenson and Clark point to Preclassic Mesoamerican cities; critics answer
that the mound-builder story and descriptions of the Ohio and New York "forts" were in print
before 1830 (Vogel 1986, in the earlier research note), and that many Hopewell enclosures are
read by archaeologists as ceremonial, not defensive.

**Known-answer check.** Pleiades is the only open, dated, coordinate-bearing gazetteer of
comparable quality, so the check is in its world: code the Bible's settlement statements (walled
cities, their number, their period, their layout against the sea and the Jordan) and ask whether,
among windows across Pleiades's coverage, the Levant in the Iron Age is among the few that match.
A text with an invented geography (Gulliver; Spalding) coded the same way should match no more
windows than chance. If the Levant does not stand out, aggregate site matching cannot work and
is dropped.

**Honest limits.** Site records map where people have looked: roads, dams, universities,
tourism, and lidar campaigns. Mexico's and Guatemala's records are far less complete than Ohio's,
and the Maya atlas is undated. Absence of recorded sites is not absence of sites. Exact
coordinates of US sites must not be published even if obtained; any result here is at county or
window scale. The site lists cannot be compared across regions without a model of how hard each
region has been searched, which we do not have. **Verdict: the Pleiades check is days of work;
the US and Mesoamerican site comparison is a research programme with an unremovable search bias,
and is not proposed beyond description.**

### 3. Dated evidence: settlement over time from radiocarbon

| Source | Size and coverage | Open? |
| --- | --- | --- |
| p3k14c (Bird and others, *Scientific Data* 2022) | 180,070 cleaned dates, global, with site coordinates | yes: data CC0 (attribution requested), via GitHub, tDAR, Open Context; dates on ancestral human remains from the US, Canada and Australia redacted in the Open Context version |
| MesoRAD, "Lowland Maya Dates" (Hoggarth, Ebert, Castelazo-Calva, *Journal of Open Archaeology Data* 2021) | 1,846 dates from 132 Maya lowland sites | open-access journal; data licence to verify |
| Palmisano and others 2021 (Near East) | 10,606 dates and 1,884 survey sites, seven regions including the Levant, with R scripts | yes, Zenodo (licence on the record; verify) |
| CARD 2.0 and Kelly and others 2022 (104,027 US dates) | North America | **restricted**: full access and locations only to vetted researchers; public view is location-fuzzed |
| IntCal20 calibration curve | global standard | open |

**What it would test.** The book's own timeline: a people arriving about 600 BC; growth and
cities over the next centuries; widespread destruction about AD 34 (3 Nephi 8); the end of the
Nephites about AD 385-421; and an earlier Jaredite span ending before the Nephites met its last
survivor. Proponents of each region point to occupation in the right centuries (Hopewell, about
100 BC to AD 400, for the Heartland; the Preclassic for Mesoamerica). The test: a summed curve of
dates (with standard corrections for the calibration curve and for sampling intensity) for every
window on earth with enough dates, and the share of windows whose curve shows occupation and
growth across 600 BC to AD 400. That share is how constraining the timeline is.

**What it will probably show, said in advance.** People lived nearly everywhere in those
centuries, so "occupied 600 BC to AD 400" will pick out most windows that have dates at all. The
book does not say the land emptied in AD 400 (the Lamanites remain), so there is no clean
collapse to look for. And the calibration curve is nearly flat from about 800 to 400 BC (the
"Hallstatt plateau"), so radiocarbon cannot date anything to "about 600 BC" more closely than a
few centuries. The timeline is likely to be weakly constraining; that is worth measuring, because
both sides cite timing as support.

**Known-answer check.** The Levant with the Palmisano data: the Bible's datable events that should
leave a mark (the Assyrian conquest of the north in 722 BC, the Babylonian destruction of Judah in
586 BC, the return and Persian-period low) must be visible as features in the Levant's curve that
random windows of the Near East do not share. Because those events fall on the Hallstatt plateau,
this check may well fail, and that would show radiocarbon cannot test a 600 BC arrival anywhere.
Hard decoy: an invented timeline (random dates of the same number and spacing) must fit no better
than the book's timeline does.

**Verdict:** feasible on the Mac in days (p3k14c is a single table; calibration in Python against
IntCal20). Coverage of Mexico and Guatemala in p3k14c, and of the eastern US after the redaction,
must be counted before anything else; if a candidate region has too few dates, it is "not
attempted".

### 4. Rivers, coasts and past shorelines

| Data | Open? |
| --- | --- |
| HydroRIVERS / HydroSHEDS (rivers with flow direction, basins) | yes; current releases CC BY 4.0 per the HydroSHEDS pages; older v1 materials were CC BY-NC 3.0, so check the version downloaded |
| Natural Earth 1:10m coastline, rivers, lakes | yes, public domain |
| Historic coastline age raster (University of Amsterdam, AGE 2019 and 2021) | for each pixel, how recently it was land, at 500-year steps since the last glacial maximum, from GEBCO bathymetry and a sea-level curve; downloadable (licence on the record; verify) |
| GEBCO bathymetry | open, with attribution |

**What it would test.** Clark's points 5 and 6 (the Sidon's head in a southern wilderness, its
course through the Zarahemla basin; a highland lake near Nephi); a sea on stated sides; a neck
between seas, measured on the coastline of about 2,000 years ago rather than today's. Sea level
has changed little in 2,500 years, but deltas and coastal plains (the Grijalva-Usumacinta,
Tabasco, the Mississippi) have moved; the age raster flags those. The Matheny-Sorenson dispute
about direction becomes a number here: the angle between the book's "north" and the real axis
of each proposed neck and river. **Verdict:** part of Part A; feasible in days.

### 5. Fortifications

The book describes cities ringed by a dug ditch, with the earth thrown up into a bank, timbers
and pickets on the bank, and towers (Alma 48-53, esp. 49-50). Who claimed what: Sorenson pointed
to Mesoamerican earthworks such as the ditch and parapet at Becan (Campeche) and Preclassic walls
in the Petén; Heartland authors point to Ohio hilltop enclosures such as Fort Ancient; critics
point out that Ohio and New York "ancient forts", with ditch, bank and palisade, were described in
print before 1830 (Atwater 1820, held; DeWitt Clinton 1818, not found in our library) and that
palisaded Iroquoian villages of western New York, much later than AD 400, were visible to
settlers.

**Open data.** No downloadable inventory of dated earthen fortifications exists for either
region. Lidar results (PACUNAM's 59 km of fortifications; Muralla de León) are published as papers,
not data. US enclosures are listed in Squier and Davis and Thomas (undated, public domain); dates
for particular sites come from the literature and p3k14c. **A dated table by hand from the
literature** (site, region, type of work, palisade evidence, dated span, reference) for each
candidate region is possible, perhaps a few dozen sites per region, but it is weeks of reading,
some of it behind paywalls, and it would be biased by which sites have been dug and dated. It
would show presence or absence of ditch-bank-palisade works in AD 1-400 in each region. Both
regions very likely have some, so it is unlikely to discriminate.

**The cheaper and sharper question is in our own library**, and it is a different one: how often,
and how early, did books printed before 1830 describe ditch-and-bank forts with pickets? We hold
Atwater, Haywood, Yates and Moulton and about 250,000 other works. That tests the critics'
"available in 1829" claim, not geography, so it is proposed as a separate issue, not part of
BOM-116.

### Feasible in days, or a research programme

| Idea | Verdict |
| --- | --- |
| Part A with GLO-90 / ETOPO relief, HydroRIVERS, Natural Earth, coastline age | days on the Mac |
| Part C: radiocarbon timeline specificity (p3k14c, MesoRAD, Palmisano), with the Levant check | days on the Mac |
| Pleiades known-answer for aggregate site matching | days |
| Lidar pilot on known Ohio earthworks (3DEP) | days; shows feasibility only |
| Exhaustive lidar detection of mounds and forts in the US | research programme (months; terabytes; field checks) |
| Wall-to-wall lidar for Mexico and Guatemala | not possible with open data |
| US against Mesoamerican site-density comparison | research programme; search bias cannot be removed with open data |
| Dated fortification table from the literature | weeks; unlikely to discriminate |
| Matching the book's named places to particular sites | not possible (no surviving names); Sorenson's place-by-place correlations: **not replicated until the book is bought (to-do)** |

## What to fetch or buy

- **Fetch (free, public):** Natural Earth 1:10m physical vectors (coastline, land, rivers and
  lake centrelines, lakes; public domain); ETOPO 2022 at 60 arc-seconds or coarser (NOAA; US
  government work, public domain); HydroRIVERS (HydroSHEDS; licence to verify before use);
  Project Gutenberg texts of *The Mysterious Island*, *The Wonderful Wizard of Oz*, *The
  Marvelous Land of Oz*, *A Princess of Mars* (public domain in the US).
- **Free to read, not to store in this repo:** Sorenson, *Mormon's Map* (2000; the whole book is
  hosted by Book of Mormon Central, archived by the author's permission; chapters also on BYU
  ScholarsArchive) and Clark's "Key" (1989) and "Revisiting" (2011), full text on Scripture
  Central. These give the internal map and Clark's reading; cite, and code our own features from
  the 1830 text. Whether *Mormon's Map* tabulates every statement with references is to verify
  (the PDF was too large for the agent's reader).
- **Not bought (owner, 2026-11-22: no purchases now):** Sorenson, *An Ancient American Setting
  for the Book of Mormon* (1985) and *Mormon's Codex* (2013), which hold his place-by-place
  real-world placements and his archaeological correlations; neither is free online. Everything
  that needs them (the angle-1 audit; checking his site correlations one by one) is **not
  replicated until the book is bought (to-do)**. Part A needs only each setting's region and
  orientation, which public summaries give, so the main test does not need the purchase.
- **Fetch for the physical-data parts (free):** Copernicus GLO-90 (or ETOPO 2022 at 30
  arc-seconds); HydroRIVERS (check the version's licence); the Amsterdam coastline-age raster;
  p3k14c (CC0); MesoRAD; Palmisano and others 2021 (Zenodo); Pleiades (CC BY); IntCal20.
  Optional pilot: a handful of 3DEP lidar tiles over the Newark and High Bank earthworks.

## Cost

- Building: Part A geometry and window counter, Part B network checks, tables and tests: a few
  hours of assistant time.
- Coding by the paced judge: about 3,800 windows of 400 words across the book and the panel
  (about 13 hours at 300 an hour), plus a 20% second reading (about 3 hours). Free; overnight.
- Window counting: about 30,000 land windows at one scale, 8 rotations, three readings, with a
  small layout search in each: estimated 1-3 hours of Mac CPU per text at its scale. No GPU.
- Fetches: Natural Earth (tens of MB), ETOPO coarse grid (hundreds of MB), four Gutenberg texts.

## Sources (URLs)

- Clark, "A Key for Evaluating Nephite Geographies" (1989): https://scripturecentral.org/archive/periodicals/journal-article/key-evaluating-nephite-geographies ; https://scholarsarchive.byu.edu/msr/vol1/iss1/7
- Clark, "Revisiting 'A Key for Evaluating Nephite Geographies'" (2011): https://scripturecentral.org/archive/periodicals/journal-article/revisiting-key-evaluating-nephite-geographies ; https://scholarsarchive.byu.edu/msr/vol23/iss1/4
- Sorenson, *Mormon's Map* (2000): https://archive.bookofmormoncentral.org/sites/default/files/archive-files/pdf/sorenson/2024-04-18/john_l._sorenson_mormons_map_2000.pdf ; https://scholarsarchive.byu.edu/mi/54 ; https://scripturecentral.org/archive/books/book/mormons-map-0
- Sorenson, *An Ancient American Setting* (1985), catalogue record: https://libcat.library.tamu.edu/Record/in00000424855 ; review: https://www.dialoguejournal.com/articles/disciplined-geography-an-ancient-american-setting-for-the-book-of-mormon-by-john-l-sorensen/
- Matheny, "Does the Shoe Fit?" (1993), summary of the direction argument: https://bhroberts.org/records/SrcFhj-HFS47g/deanne_g_matheny_critiques_john_sorensons_geography_model_on_the_issue_of_directionality ; Sorenson's reply (1994): https://scripturecentral.org/archive/periodicals/journal-article/vive-zapato-hurray-shoe ; https://scholarsarchive.byu.edu/msr/vol6/iss1/11
- A critique of a limited geography, *Dialogue* 35(3): https://www.dialoguejournal.com/articles/critique-of-a-limited-geography-for-book-of-mormon-events/
- Overview of proposed settings: https://en.wikipedia.org/wiki/Proposed_Book_of_Mormon_geographical_setting
- Barjamovic, Chaney, Coşar, Hortaçsu (2019), *QJE* 134(3): https://www.nber.org/papers/w23992 ; https://keremcosar.uvacreate.virginia.edu/publications/BCCH-BronzeAgeTrade-qje.pdf
- Ptolemy's Germania rectified: https://bmcr.brynmawr.edu/?p=30306 ; https://hgss.copernicus.org/articles/3/99/2012/ ; https://mail.geodaesie.info/images/zfv/136-jahrgang-2011/downloads/zfv_2011_2_Kleineberg_et-al.pdf
- Stevens and Coupe (1978), *Cognitive Psychology* 10: https://www.scilit.net/publications/a19fdbb368a6432e60f9769a52811ab8 ; Tversky (1992), "Distortions in cognitive maps": https://www.tc.columbia.edu/faculty/bt2158/faculty-profile/files/1992_Tversky_Distortionsincognitivemaps.pdf
- Ligozat (1998), "Reasoning about cardinal directions", *JVLC* 9(1): https://sfbtr8.spatial-cognition.de/aigaion/index.php/publications/show/1724.html ; Frank, cardinal directions (Auto-Carto 10): https://cartogis.org/docs/proceedings/archive/auto-carto-10/pdf/qualitative-spatial-reasoning-about-cardinal-directions.pdf
- Ryan (2003), "Cognitive maps and the construction of narrative space": https://narrativestudies.lib.unb.ca/bibcite/reference/18339 ; Ryan, Foote, Azaryahu (2016): https://www.jstor.org/stable/j.ctv2t46rcp
- Caquard and Cartwright, narrative cartography: https://gistbok-ltb.ucgis.org/current/concept/CV-04-033
- Oz map reversal: https://www.wikipedia.org/wiki/Tik-Tok_of_Oz ; https://bigthink.com/strange-maps/69-not-kansas-but-just-as-rectangular-the-land-of-oz/
- *Treasure Island* map: https://www.lancaster.ac.uk/chronotopic-cartographies/visualisations/treasure-island ; https://digital.nls.uk/rlstevenson/pics/picture-e2.html
- Natural Earth 1:10m physical vectors: https://www.naturalearthdata.com/downloads/10m-physical-vectors/
- ETOPO 2022: https://www.ncei.noaa.gov/products/etopo-global-relief-model
- HydroRIVERS: https://www.hydrosheds.org/products/hydrorivers
- OpenBible.info geocoding (held): https://www.openbible.info/geo/
- Copernicus DEM: https://registry.opendata.aws/copernicus-dem/ ; https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM ; licence: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf
- USGS 3DEP lidar: https://registry.opendata.aws/usgs-lidar/ ; https://www.usgs.gov/3d-elevation-program/about-3dep-products-services ; https://catalog.data.gov/dataset/lidar-point-cloud-usgs-national-map-3dep-downloadable-data-collection
- INEGI LiDAR DEM: https://inegi.org.mx/contenidos/temas/relieve/continental/doc/lidar_alta_resolucion.pdf ; https://inegi.org.mx/contenidos/temas/relieve/continental/doc/lidar_terreno.pdf
- NASA G-LiHT: https://gliht.gsfc.nasa.gov/index.php?section=34 ; https://glihtdata.gsfc.nasa.gov ; https://www.earthdata.nasa.gov/data/projects/g-liht/data-access-tools ; Golden and others 2016: https://ntrs.nasa.gov/citations/20170003271 ; follow-up inventory: https://par.nsf.gov/servlets/purl/10212620
- PACUNAM lidar results (not open data): https://www.nationalgeographic.com/culture/article/lasers-reveal-maya-war-ruins ; Muralla de León: https://resolve.cambridge.org/core/journals/ancient-mesoamerica/article/abs/preclassic-maya-fortification-at-muralla-de-leon-peten-deducing-assets-military-strategies-and-specific-threats-through-analysis-of-defensive-systems/2F8649B8B64BC2C3343E59750172CC08
- DINAA: https://opencontext.org/projects/0cea2f4a-84cb-4083-8c66-5191628abe67 ; location-sharing practice: https://www.cambridge.org/core/product/A7338404A56B73BB282C4A28B3B7264A ; example state licence (Georgia): https://opencontext.org/projects/64013c33-4039-46c9-609a-a758ce51ca49
- Squier and Davis 1848: https://gutenberg.org/ebooks/49668 ; https://repository.si.edu/handle/10088/7486
- Electronic Atlas of Ancient Maya Sites: https://mayagis.smv.org ; https://www.famsi.org/research/MayaGIS/index.html ; Data Basin copy: https://databasin.org/datasets/3aa6b24c882144d6a4197bd277ae753d/
- Pleiades: https://pleiades.stoa.org/downloads ; https://zenodo.org/records/8206033/latest
- p3k14c: https://github.com/people3k/p3k14c ; https://doi.org/10.1038/s41597-022-01118-7 ; https://doi.org/10.48512/XCV8459173 ; https://opencontext.org/projects/cdd78c10-e6da-42ef-9829-e792ce55bdd6
- MesoRAD: https://doaj.org/article/1c41de70cdb040018a689cfe6e4d7e9b
- Palmisano and others 2021 data: https://zenodo.org/record/4322979
- CARD (restricted): https://canadianarchaeology.ca ; Kelly and others 2022: https://www.cambridge.org/core/product/4F38C33D197363BF2E6952E5AC4AD195/core-reader
- HydroSHEDS terms: https://hydrosheds.org/terms-of-use ; https://www.hydrosheds.org/products/hydrosheds-v2
- Historic coastline age raster (AGE 2021): https://dare.uva.nl/id/5cbc34b4-96e0-4f90-a750-86fa9dc7bcd2
- Heartland and Great Lakes models: https://www.fairlatterdaysaints.org/answers/Book_of_Mormon/Geography/Models/Limited/Meldrum_2003 ; https://sltrib.com/religion/2022/03/30/who-are-heartlanders-why ; https://www.fairlatterdaysaints.org/answers/Great_Lakes_Model_of_Book_of_Mormon_geography ; https://scholarsarchive.byu.edu/msr/vol14/iss1/4 ; https://scholarsarchive.byu.edu/facpub/4321
- The first design: `lab/geography.py`; `data/lab/setting/geography/result.json`; BOM-116 (GitHub issue 127).
