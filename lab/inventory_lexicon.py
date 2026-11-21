"""BOM-111: the category word lists for the inventory test (lab/inventory.py).

Written from memory by the AI, before any Book of Mormon count was taken, then extended from the
Wikipedia lists and from a frequency pass over the comparison texts only (see the test card, which
records both steps and the date). Nothing here was chosen by looking at the Book of Mormon.

Syntax of the strings (words separated by spaces):

* ``name``            a lemma; plural forms (s, es, ies, ves) are generated;
* ``name:a,b``        the lemma with extra spellings (also pluralised);
* ``name!``           counted only when written in lower case (a capitalised homonym exists);
* ``name?``           counted only when the word before it is a determiner, number or "of/with"
                      (the word is often a verb: bow, ring, plant, bear);
* ``two_words``       a two-word item (an underscore stands for the space).

ORIGIN marks lemmas known to be Old World (OW), New World (NW) or typical of the northern
colonies and tribes (NE); an unmarked lemma is ``general``. ALLOWANCE names Old World words
that translators and chroniclers used for New World things (step 5 of the card).
"""

from __future__ import annotations

ANIMALS = """
horse mare stallion colt foal steed ass:asses,she-ass,he-ass donkey mule camel dromedary
ox:oxen bull cow calf:calves heifer cattle kine bullock buffalo bison sheep ram ewe lamb goat
he-goat swine pig hog boar sow piglet dog hound mastiff greyhound cat kitten lion lioness
leopard panther tiger jaguar ocelot puma cougar lynx wildcat wolf:wolves fox:foxes jackal hyena
bear? elephant rhinoceros unicorn hippopotamus behemoth giraffe deer stag hart hind roe roebuck
gazelle antelope elk moose caribou reindeer buck doe fawn rabbit hare coney squirrel mouse:mice
rat mole? bat hedgehog porcupine badger otter beaver muskrat raccoon:racoon,racoons opossum:possum
skunk weasel marten sable ermine armadillo sloth anteater tapir peccary monkey ape baboon
marmoset llama alpaca vicuna guanaco coyote agouti manatee seal? whale dolphin porpoise walrus
catamount woodchuck coati kinkajou capybara
eagle hawk falcon kite vulture owl raven crow dove pigeon partridge quail sparrow swallow?
stork heron crane? peacock peafowl cock hen chicken fowl rooster duck goose:geese swan turkey!
pheasant ostrich pelican cormorant bittern lapwing nightingale lark robin! wren thrush
mockingbird hummingbird humming-bird macaw parrot parakeet quetzal toucan flamingo condor gull
cuckoo woodpecker bluebird whippoorwill jay grouse bird
serpent snake viper adder asp cockatrice dragon rattlesnake crocodile alligator caiman cayman
lizard iguana turtle tortoise toad frog
fish shark salmon trout cod herring eel oyster shellfish shrimp lobster crab mackerel shad bass
clam sturgeon
bee locust grasshopper ant fly:flies gnat flea louse:lice moth worm caterpillar scorpion spider
hornet wasp cricket mosquito silkworm cochineal
beast flock herd
"""

PLANTS_FOODS = """
wheat barley rye oat millet spelt fitches rice flax hemp
maize:maiz,mahiz,indian_corn,indian_wheat bean lentil pea
chickpea pulse onion garlic leek cucumber melon gourd pumpkin
squash radish cabbage lettuce herb cress turnip parsnip carrot beet spinach potato yam
sweet_potato cassava manioc yucca tomato chili:chilli,chile pepper capsicum avocado papaya
pineapple guava plantain banana cacao cocoa chocolate vanilla tobacco maguey agave pulque aloe
cactus nopal prickly_pear sapote sapodilla chicle copal rubber balsam incense frankincense myrrh
spice cinnamon cassia saffron cumin coriander dill mint anise mustard hyssop rue wormwood
galbanum calamus spikenard camphire mandrake roses lily:lilies narcissus tulip violet jasmine
marigold sunflower amaranth chia jicama chayote tomatillo mamey annatto achiote calabash tuna?
oak cedar fir pine cypress palm olive fig vine vineyard grape raisin pomegranate apple pear
plum cherry peach apricot orange lemon lime? citron date? almond walnut chestnut hazel!
filbert pistachio mulberry sycamore sycamine poplar willow elm ash? maple beech birch hickory
juniper acacia shittim algum almug ebony teak mahogany brazil! logwood mesquite ceiba bamboo
reed rush bulrush papyrus thorn thistle brier bramble nettle tare cockle hemlock gall tree
grass flower fruit grain seed plant? bush shrub orchard garden forest
bread cake meal flour honey milk butter cheese oil wine vinegar beer ale cider rum brandy
venison salt sugar molasses tea coffee tortilla tamale atole pozole pinole mush hominy
succotash pemmican johnnycake pone manna acorn hay straw stubble chaff sheaf harvest
meat flesh fat suet broth porridge pottage parched_corn
"""

METALS_MATERIALS = """
gold silver copper brass bronze iron steel tin lead? zinc quicksilver mercury platinum electrum
pewter solder ore metal dross amber coral crystal ivory marble alabaster jasper onyx sapphire
emerald ruby diamond topaz beryl carbuncle chalcedony chrysolite chrysoprase sardius sardonyx
agate amethyst jacinth ligure pearl gem jewel precious_stone jade jadeite chalchihuitl obsidian
itztli flint chert turquoise malachite pyrite mica cinnabar cement mortar plaster brick clay
stone rock slime? pitch tar bitumen wax resin glass timber wood bark leather hide parchment
fleece feather horn shell tortoiseshell bone copper-plate
"""

TOOLS_WEAPONS = """
sword spear lance javelin dart arrow bow? quiver shield buckler helmet breastplate armour:armor
habergeon coat_of_mail sling club mace battleaxe axe hatchet tomahawk dagger knife cimeter:scimitar
cutlass musket gun cannon pistol rifle gunpowder bayonet firelock macuahuitl atlatl
chariot wagon:waggon cart plough:plow ploughshare coulter sickle scythe hoe spade shovel mattock
pickaxe adze saw? hammer anvil tongs forge bellows chisel nail needle loom spindle distaff
shuttle rope cord cable net snare trap hook fishhook boat ship canoe raft barge vessel oar sail
mast rudder anchor helm compass balance scale? bed couch chair stool table lamp candle
candlestick lantern torch censer basin bowl cup goblet pot kettle caldron pan dish jar pitcher
bottle flagon urn basket sack bag box chest coffer key lock bolt chain fetter yoke bridle saddle
halter harness stirrup whip goad rod staff crook hammock broom pestle metate millstone grindstone
quern sieve fan? drum trumpet harp pipe cymbal psaltery tabret timbrel sackbut dulcimer organ
flute whistle teponaztli huehuetl conch rattle sled snowshoe wheel plow-share tool weapon armour
"""

BUILDINGS = """
house temple tabernacle synagogue palace tower wall gate city town village fortress fort castle
citadel stockade palisade ditch moat trench bulwark rampart embankment mound pyramid obelisk pillar
column arch vault dome porch portico courtyard chamber roof door window stair staircase floor
foundation cellar prison dungeon pit cistern pool fountain aqueduct canal bridge road highway
causeway street market marketplace plaza sanctuary altar shrine idol statue sepulchre:sepulcher
tomb grave cave hut cabin wigwam tent booth lodge cottage barn granary storehouse stable inn mill
church meeting-house steeple school college hospital mansion hall gallery terrace balcony chimney
hearth fireplace oven furnace kiln observatory lighthouse garrison camp blockhouse teocalli
adobe thatch pueblo kiva hamlet pavement monument ruin
"""

CLOTHING = """
garment robe coat cloak mantle tunic shirt breeches trousers girdle belt sash loincloth
breechcloth apron cap hat turban mitre crown diadem veil headdress hood shoe sandal buskin
moccasin stocking glove ring? bracelet anklet earring necklace collar ornament plume fringe
ribband:ribbon lace embroidery needlework tapestry carpet blanket sackcloth cloth linen
fine_linen silk cotton! wool woollen velvet satin scarlet crimson dye indigo tassel buckskin fur
raiment apparel vesture clothing clothes wampum huipil maxtlatl tilma feather-work
"""

ORIGIN_OW = """
horse mare stallion steed ass donkey mule camel dromedary ox bull cow calf heifer cattle kine
bullock sheep ram ewe lamb goat swine pig hog boar sow lion lioness leopard elephant rhinoceros
unicorn hippopotamus giraffe stag hart hind roe roebuck gazelle antelope cock hen chicken
peacock peafowl ostrich pelican stork nightingale pheasant cockatrice dragon viper adder asp
wheat barley rye oat millet spelt fitches rice flax lentil chickpea onion garlic leek cucumber
melon cabbage lettuce turnip parsnip carrot beet olive fig vine vineyard grape raisin pomegranate
apple pear plum cherry peach apricot orange lemon citron almond walnut mulberry sycamore
cedar cypress mandrake hyssop wormwood frankincense myrrh cinnamon cassia saffron cumin coriander
dill mint anise mustard rue wine vinegar beer ale cheese butter oil bread cake
iron steel tin lead brass bronze zinc electrum pewter pearl onyx sapphire emerald ruby diamond
topaz beryl carbuncle chalcedony chrysolite chrysoprase sardius sardonyx agate amethyst jacinth
alabaster marble ivory glass parchment wool silk linen fine_linen velvet satin
sword spear lance javelin buckler helmet breastplate habergeon coat_of_mail cimeter dagger
cutlass musket gun cannon pistol rifle gunpowder bayonet chariot wagon cart plough ploughshare
coulter sickle scythe hoe spade shovel mattock pickaxe anvil tongs bellows loom spindle distaff
shuttle compass balance candlestick lantern censer goblet flagon harp cymbal psaltery tabret
timbrel sackbut dulcimer organ trumpet saddle stirrup bridle halter yoke
synagogue tabernacle temple palace tower castle citadel moat obelisk portico mansion steeple
turban mitre diadem sandal buskin tunic girdle breeches trousers stocking glove
"""

ORIGIN_NW = """
maize indian_corn indian_wheat cacao cocoa chocolate tomato potato sweet_potato cassava manioc
yucca chili pepper capsicum avocado papaya pineapple guava plantain? tobacco maguey agave pulque
nopal prickly_pear sapote sapodilla chicle copal rubber vanilla squash gourd calabash bean
jicama chayote tomatillo mamey annatto achiote amaranth chia sunflower mesquite ceiba mahogany
logwood tuna turkey jaguar ocelot puma cougar tapir peccary armadillo opossum sloth anteater
llama alpaca vicuna guanaco coyote agouti manatee coati kinkajou capybara quetzal toucan macaw
parrot parakeet hummingbird humming-bird condor iguana caiman cayman alligator rattlesnake
cochineal jade jadeite chalchihuitl obsidian itztli turquoise malachite macuahuitl atlatl hammock
canoe tortilla tamale atole pozole pinole metate teponaztli huehuetl teocalli adobe pueblo kiva
huipil maxtlatl tilma feather-work plume cotton indigo
"""

ORIGIN_NE = """
beaver moose raccoon muskrat woodchuck skunk catamount caribou elk bison buffalo whippoorwill
bluebird mackerel shad clam lobster sturgeon wampum wigwam tomahawk musket moccasin sled
snowshoe blockhouse stockade palisade garrison meeting-house steeple cider rum molasses hominy
succotash pemmican johnnycake pone maple pumpkin buckskin fur hickory birch
"""

# Old World words the chroniclers and translators put on New World things (card, step 5).
ALLOWANCE = """
tiger lion sheep corn bread sword hen peacock wine brass linen silk fig swine hog wolf ox horse
ass cattle cow fine_linen steel iron
"""

# Words that are counted apart and left out of every score (card, step 1).
APART = {"corn"}

# Added from the Wikipedia lists and from the frequency pass over the comparison texts only
# (filled by the maintainer after reading the printed candidates; see the card).
ADDED_FROM_MEMORY = {
    "animals": """
mastiff spaniel terrier bloodhound lap-dog whelp cub lambkin sheepdog bullock steer oxen
palfrey charger courser nag pony gelding jennet colt filly camelopard dromedaries
kid? goatling wether yearling sucking-pig farrow brood-mare mongrel cur
ibex chamois marmot lemming gopher prairie-dog chipmunk vole shrew dormouse polecat mink
fisher wolverine panther lynxes bobcat sea-lion sea-cow dugong narwhal grampus
vampire sparrow-hawk buzzard osprey merlin goshawk harrier raven rook jackdaw magpie starling
finch linnet canary goldfinch bullfinch chaffinch titmouse nuthatch oriole tanager cardinal
mourning-dove plover snipe woodcock sandpiper curlew ibis egret spoonbill albatross petrel
penguin auk puffin booby frigate-bird kingfisher hoopoe bustard capon pullet cockerel gander
drake teal widgeon mallard cygnet eaglet nest
asp cobra krait boa anaconda copperhead moccasin-snake garter-snake coral-snake rattler
salamander newt chameleon gecko basilisk leviathan
carp perch roach tench minnow sprat anchovy sardine pilchard haddock halibut flounder
sole turbot skate ray lamprey whiting smelt bream mullet tunny dorado swordfish stingray
mussel scallop limpet periwinkle winkle snail slug leech sponge
butterfly dragonfly beetle cicada earwig weevil maggot grub bumblebee drone queen-bee
tarantula centipede millipede termite aphid ladybird glowworm firefly sandfly tick
cassowary ferret hamster caracal cheetah axolotl budgerigar zebu mastodon mammoth quadruped
animal creature cerastes polypus
""",
    "plants_foods": """
oats rye-grass bran grits groats barleycorn malt yeast leaven dough
broad-bean kidney-bean haricot lima-bean string-bean vetch tares darnel
shallot chive scallion celery parsley sage thyme basil fennel marjoram rosemary savory
tarragon lavender chervil borage sorrel dandelion plantain? clover alfalfa sedge moss fern
mushroom truffle lichen seaweed ivy mistletoe heather gorse bracken
artichoke asparagus beetroot endive kale kohlrabi rhubarb pimpernel horseradish
raspberry strawberry gooseberry currant blackberry cranberry blueberry huckleberry elderberry
mulberry quince medlar damson greengage nectarine tamarind coconut cocoa-nut date-palm
breadfruit mango lychee persimmon pawpaw soursop pitaya cherimoya guanabana pecan peanut
allspice arrowroot quinoa coca cashew goosefoot opuntia
nutmeg clove ginger turmeric cardamom liquorice galingale cassia-bark storax stacte onycha
camphor sandalwood aloe-wood gum-arabic mastic turpentine myrtle laurel bay oleander
hawthorn blackthorn sloe holly yew larch spruce hemlock-tree sequoia redwood cottonwood
sassafras sumac linden lime-tree alder aspen buttonwood plane-tree locust-tree sycamore-fig
terebinth tamarisk shittah-tree gopher-wood cane sugar-cane sorghum teff
tulip crocus hyacinth anemone lotus violets rosebud honeysuckle primrose daisy buttercup
poppy cowslip foxglove snowdrop columbine sweetbrier
maple-sugar maple-syrup treacle jelly jam pudding pie tart biscuit cracker bun roll loaf
dumpling sausage bacon ham pork beef mutton veal lard tallow marrow gravy soup
cheese curds whey cream buttermilk egg yolk
mead metheglin porter perry whiskey gin claret sherry champagne malmsey
cassava-bread tamales tortillas posole pinole chicha cacao-beans chocolatl
""",
    "metals_materials": """
quicksilver cinnabar lead-ore tinstone pig-iron cast-iron wrought-iron bar-iron sheet-iron
steel-plate latten tombac nickel cobalt bismuth antimony arsenic alloy tumbaga
gold-dust gold-leaf silver-plate bullion ingot nugget coin
diamonds rubies pearls opal garnet lapis lazuli bloodstone cornelian carnelian beryl-stone
moonstone obsidian-blade serpentine soapstone steatite greenstone basalt granite sandstone
limestone slate flagstone gypsum chalk lime-stone quartz feldspar porphyry marl loam gravel
coal charcoal peat sulphur brimstone saltpetre nitre alum vitriol ochre umber vermilion
verdigris copperas red-lead white-lead salt-petre natron soda potash lye
cement-work earthenware porcelain pottery potsherd brick-work tile tiles stucco
rope-yard hemp-rope twine thread yarn
hide hides pelt pelts fell tanned leather-work vellum papyrus-roll
ivory-work horn-work tusk tusks antler antlers whalebone sinew gut catgut
log logs plank planks beam beams rafter rafters lath laths stave staves
bamboo-cane rattan osier withe withes bast rush-mat
cotton-cloth cotton-thread feathers plumage down
""",
    "tools_weapons": """
crossbow longbow catapult battering-ram ram-engine engine artillery culverin mortar-gun
blunderbuss carbine fowling-piece matchlock flintlock cartridge bullet shot-gun grenade
bomb petard rapier sabre broadsword halberd pike partisan poleaxe truncheon cudgel bludgeon
war-club tomahawk-axe scalping-knife stiletto poniard bodkin
gauntlet greave greaves cuirass corselet vambrace visor morion coat-of-mail mail-coat
pavilion standard banner ensign flag? drumstick
plowshare ploughman harrow rake pitchfork flail winnowing-fan threshing-floor mattock
grubbing-hoe digging-stick axe-head wedge maul crowbar lever pulley windlass capstan jack
auger gimlet awl plane-tool rasp file? whetstone grindstone lathe vice bench
trowel plumb-line level square-rule compasses
spindle-whorl weaving-frame comb card hackle reel skein bobbin
fishing-line fishing-net seine weir harpoon fish-spear gaff
rowboat longboat pinnace sloop brig schooner frigate galley ship-of-war merchantman
cutter ferry-boat flatboat keelboat dugout catamaran paddle punt skiff wherry
yard-arm sail-yard topsail mainsail cordage shroud halyard
carriage coach chaise gig sleigh sledge litter palanquin wheelbarrow tumbril dray
saddle-bag saddle-cloth spur curb snaffle blinker trace traces hames
cradle cot hammock-bed bedstead mattress pallet couch-bed settle bench-seat footstool
cupboard chest-of-drawers wardrobe trunk casket cabinet shelf
candle-stick taper rushlight wick tinder flint-and-steel firebrand brand
cauldron skillet griddle spit gridiron tripod trivet ladle spoon fork platter trencher
tankard mug jug pitcher-jar bucket pail tub barrel cask keg hogshead vat churn firkin
gourd-cup calabash-cup tecomate earthen-vessel potter's-wheel
penknife razor shears scissors thimble pincers pliers tweezers
lyre lute viol violin fiddle fife bagpipe bugle horn-pipe clarion shawm tambourine gong bell
mirror looking-glass spectacles telescope quadrant astrolabe sundial hourglass clock watch
barometer thermometer microscope
quipu abacus yardstick measuring-rod plummet
shackle manacle handcuff gyve stocks pillory gallows gibbet scaffold rack
bier coffin shroud-cloth urn-burial
amulet talisman censer-bowl incense-burner offering-bowl
""",
    "buildings": """
cathedral chapel abbey monastery convent nunnery cloister mosque pagoda minaret
pyramids ziggurat mausoleum catacomb crypt vault-tomb barrow tumulus tumuli cairn
palisades breastwork earthwork redoubt bastion battlement parapet turret keep dungeon-tower
drawbridge portcullis postern sally-port watchtower beacon lookout guard-house
courthouse townhouse guildhall exchange custom-house arsenal magazine armory barracks
theatre theater amphitheatre amphitheater circus stadium hippodrome gymnasium bath baths
forum basilica senate-house prytaneum treasury treasure-house
parsonage manse vicarage rectory farmhouse homestead plantation settlement dwelling
shed outhouse smokehouse springhouse dairy washhouse bakehouse brewhouse woodshed sty pen-fold
fold sheepfold cowhouse henhouse dovecote pigeon-house haystack rick
tavern alehouse coffee-house ordinary warehouse shop shops counting-house factory forge-house
sawmill gristmill grist-mill windmill watermill millrace millpond dam weir-dam sluice
lighthouse pier wharf quay dock harbour harbor port jetty breakwater
ball-court ballcourt teocalli-temple temple-mound platform pyramid-temple stela stelae altar-stone
sweat-house sweat-lodge longhouse council-house town-house kiva-chamber pit-house earth-lodge
wattle daub plaster-wall whitewash shingle shingles clapboard clapboards
gateway doorway threshold lintel doorpost hinge latch porch-roof veranda piazza loggia
stairway ladder landing attic garret loft closet pantry kitchen parlour parlor bedchamber
dining-room upper-room guest-chamber inner-court outer-court holy-place most-holy-place
well-head winepress oil-press threshingfloor wine-vat watchtower-vineyard
walls-of-the-city city-gate city-wall fortification fortifications fortified
tombstone gravestone headstone monument-stone obelisk-stone milestone landmark boundary-stone
causey pavement-stone ford ferry turnpike tollgate lane alley thoroughfare avenue boulevard
ditches reservoirs aqueducts canals bridges roads highways streets markets squares
suburb suburbs quarter district metropolis capital
""",
    "clothing": """
doublet jerkin waistcoat vest petticoat gown frock kirtle smock bodice stays corset habit
surcoat cassock cope chasuble alb stole surplice ephod breastplate-of-judgment
greatcoat overcoat pelisse mantlet cape tippet shawl scarf wrap plaid kilt
hose stockings garter garters slipper slippers boot boots clog clogs galosh spats pump
wig peruke periwig bonnet coif cowl wimple kerchief handkerchief neckcloth cravat ruff
bandage fillet frontlet phylactery tiara coronet circlet garland wreath chaplet
brooch buckle clasp button buttons pin-brooch fibula pendant locket signet seal-ring
armlet bangle nose-ring nose-jewel ear-ring ear-ring-gold medallion amulet-necklace
bead beads shell-beads wampum-belt strings-of-beads
leggings gaiters breechclout loin-cloth skirt cape-cloth poncho serape blanket-robe
buffalo-robe bearskin deerskin fox-skin wolfskin lambskin goatskin sheepskin calfskin
moccasins snowshoes mittens mitten muff
broadcloth calico muslin cambric lawn gauze damask brocade taffeta tabby crape crepe
camlet serge flannel fustian corduroy canvas sailcloth tow homespun kersey frieze baize
worsted lace-work fine-twined-linen byssus sendal tissue purple-cloth blue-cloth scarlet-cloth
nankeen dimity gingham chintz cashmere
embroidered needle-work fringes tassels plumes feather-cloak feather-mantle featherwork
quilted-cotton cotton-armour cotton-mantle
mourning-cloth sack-cloth ashes-and-sackcloth robe-of-state royal-apparel
dyestuff dyes madder woad saffron-dye annotto logwood-dye cochineal-dye
""",
}
ADDED = ADDED_FROM_MEMORY

# Variants of lemmas already listed (old and American spellings met in the comparison texts).
VARIANTS = {
    "metals_materials": "brass:brasen,brazen platinum:platina",
    "tools_weapons": "tomahawk:tomohawk",
    "plants_foods": "hickory:hiccory maguey:maguei",
    "clothing": "clothes:cloaths",
}

# Removed from the lists above before any counting: mostly another part of speech, a proper name
# or a general word (stole, watch, down, roll, fell, steer, keep, vice ...).
EXCLUDE = set(
    """kid sole ray skate tick bath exchange port capital district quarter level card trace
    traces brand jack bay sage cardinal fisher nest creature smelt wrap stays habit cope stole
    mittens doe loft fort fat cape cap crown settlement settlements rod pump lawn tissue tow down
    fell gut standard flag curb vice stocks watch settle keep fold
    ordinary dam daub gin roll tart porter steer grub perch """.split()
)

CATEGORIES = {
    "animals": ANIMALS,
    "plants_foods": PLANTS_FOODS,
    "metals_materials": METALS_MATERIALS,
    "tools_weapons": TOOLS_WEAPONS,
    "buildings": BUILDINGS,
    "clothing": CLOTHING,
}

# Words of the Book of Mormon that no dictionary classifies; reported apart, never scored.
NOT_CLASSIFIABLE = {
    "animals": ["cureloms", "cumoms"],
    "plants_foods": ["neas", "sheum"],
    "metals_materials": ["ziff"],
}
