"""BOM-109 third design: the second design's features, Kirchhoff 1943 keyed, two traits added.

Written 2026-11-23 at finalisation of the third design, before any answer of that design existed.
The 45 features of ``lab.threeworlds2_features`` are kept unchanged (label, topic, kind, markers);
each Mesoamerica-only feature that Kirchhoff lists gets a ``kirchhoff:<group>`` provenance code;
two traits of his group I that no source of the second design covered are added (``ball_game``,
``chinampas``), because his list is the field's standard definition of Mesoamerica and the card
of the second design meant to use it.

Kirchhoff, Paul, "Mesoamérica: sus límites geográficos, composición étnica y caracteres
culturales" (1943), as reprinted in *Tlatoani* suplemento 3 (1960), private copy
``data/private/lab/sources/kirchhoff/kirchhoff1943_mesoamerica_tlatoani1960.pdf`` (pp. 7-12 of the
reprint). He gives three groups: I, traits exclusive to or typical of Mesoamerica; II, traits
Mesoamerica shares with other culture areas of America, in sub-groups a-m by which areas share
them; III, traits typical by their absence. ``KIRCHHOFF`` below keys his group I and the parts of
group II and III that bear on our features, **in our own English paraphrase** (the essay is in
copyright; no wording of it is kept), checked against the essay text on 2026-11-23 by the AI
agent (Claude), not by a person.
"""

from __future__ import annotations

from lab.threeworlds2_features import AM, ANCIENT, CT, DPLACE, DPLACE_SOCIETIES, MS, NE, WORLDS
from lab.threeworlds2_features import FEATURES as FEATURES2

__all__ = ["AM", "ANCIENT", "CT", "DPLACE", "DPLACE_SOCIETIES", "FEATURES", "KIRCHHOFF", "MS",
           "NE", "WORLDS", "ADDED"]  # fmt: skip

# Kirchhoff's traits, our paraphrase: code -> (trait, our feature or None when not keyed).
# Group I is listed whole (in his order); from II and III only what touches a feature.
KIRCHHOFF: dict[str, tuple[str, str | None]] = {
    "I.1": ("a digging stick of a particular shape (coa)", None),
    "I.2": ("gardens won from lakes (chinampas)", "chinampas"),
    "I.3": ("chia grown for drink and for an oil used in paint", None),
    "I.4": ("maguey grown for its sap, syrup, pulque and paper", "maguey_pulque"),
    "I.5": ("cacao grown", "cacao"),
    "I.6": ("maize ground after cooking with ash or lime", None),
    "I.7": ("clay pellets for blowguns, lip plugs and other small clay objects", None),
    "I.8": ("polished obsidian", "obsidian"),
    "I.9": ("pyrite mirrors", None),
    "I.10": ("copper tubes for drilling stone", None),
    "I.11": ("rabbit hair woven into cloth", None),
    "I.12": ("wooden swords edged with flint or obsidian blades (macuahuitl)", "obsidian"),
    "I.13": ("quilted cotton armour (ichcahuipilli)", "cotton"),
    "I.14": ("shields with two handles", None),
    "I.15": ("turbans; sandals with heels; one-piece suits for warriors", None),
    "I.16": ("stepped pyramids", "pyramids"),
    "I.17": ("stucco floors", "cement"),
    "I.18": ("ball courts with rings", "ball_game"),
    "I.19": ("hieroglyphic writing; number signs with place value", "codices"),
    "I.20": ("folding screen books; historical annals and maps", "codices"),
    "I.21": ("a year of 18 months of 20 days and 5 days more", "meso_calendar"),
    "I.22": ("a 260-day count of 20 signs and 13 numbers", "meso_calendar"),
    "I.23": ("the two combined into a 52-year cycle", "meso_calendar"),
    "I.24": (
        "feasts at the end of certain periods; lucky and unlucky days; people named by "
        "the day of birth",
        "meso_calendar",
    ),  # fmt: skip
    "I.25": ("ritual use of paper and rubber", None),
    "I.26": ("sacrifice of quails", None),
    "I.27": (
        "certain forms of human sacrifice (burning alive, dancing in the victim's skin)",
        "human_sacrifice",
    ),  # fmt: skip
    "I.28": (
        "certain forms of self-sacrifice (drawing blood from tongue, ears, legs, sex organs)",
        "bloodletting",
    ),  # fmt: skip
    "I.29": ("the volador rite", None),
    "I.30": ("13 as a ritual number", None),
    "I.31": ("a set of gods (Tlaloc among them)", None),
    "I.32": ("several other worlds of the dead and a hard journey to them", None),
    "I.33": ("drinking the water a dead kinsman was washed in", None),
    "I.34": ("markets divided by speciality", None),
    "I.35": ("merchants who are also spies", None),
    "I.36": ("military orders (eagle and jaguar knights)", None),
    "I.37": ("wars fought to take victims for sacrifice", "human_sacrifice"),
    "II.b": (
        "maize, beans and squash grown (shared with the Southeast, Southwest, Chibcha, "
        "Andes, north-west Amazonia)",
        "maize",
    ),  # fmt: skip
    "II.c": ("human sacrifice (shared with the Southeast, Chibcha, Andes)", "human_sacrifice"),
    "II.h": (
        "cotton grown (shared with the Southwest, Chibcha, Andes, north-west Amazonia)",
        "cotton",
    ),  # fmt: skip
    "II.j": (
        "chili, the fattened mute dog, paved roads, markets, metallurgy (shared with the "
        "Chibcha, Andes, north-west Amazonia)",
        None,
    ),  # fmt: skip
    "II.l": (
        "the rubber-ball game in which the ball may not be touched by hand (shared with Amazonia)",
        "ball_game",
    ),  # fmt: skip
}

# feature -> Kirchhoff codes (II.j split by its parts: beans_squash_chili, dogs_eaten, causeways)
_K = {
    "maize": ("kirchhoff:II.b",),
    "beans_squash_chili": ("kirchhoff:II.b", "kirchhoff:II.j"),
    "cacao": ("kirchhoff:I.5",),
    "maguey_pulque": ("kirchhoff:I.4",),
    "cotton": ("kirchhoff:I.13", "kirchhoff:II.h"),
    "obsidian": ("kirchhoff:I.8", "kirchhoff:I.12"),
    "dogs_eaten": ("kirchhoff:II.j",),
    "pyramids": ("kirchhoff:I.16",),
    "cement": ("kirchhoff:I.17",),
    "causeways": ("kirchhoff:II.j",),
    "human_sacrifice": ("kirchhoff:I.27", "kirchhoff:I.37", "kirchhoff:II.c"),
    "bloodletting": ("kirchhoff:I.28",),
    "meso_calendar": ("kirchhoff:I.21", "kirchhoff:I.22", "kirchhoff:I.23", "kirchhoff:I.24"),
    "codices": ("kirchhoff:I.19", "kirchhoff:I.20"),
}

ADDED: dict[str, tuple[str, str, str, str, tuple[str, ...]]] = {
    "ball_game": (
        "the ball game played in walled courts (tlachtli)",
        "buildings",
        MS,
        "tlachtli tlachco ball-court ball-courts ballcourt ballcourts game_of_ball games_of_ball "
        "ball_game",
        ("kirchhoff:I.18", "kirchhoff:II.l"),
    ),
    "chinampas": (
        "gardens built out on lakes (chinampas, floating gardens)",
        "crops",
        MS,
        "chinampa chinampas floating_garden floating_gardens",
        ("kirchhoff:I.2",),
    ),
}

# id: (label as the judge reads it, topic, kind, markers, provenance)
FEATURES: dict[str, tuple[str, str, str, str, tuple[str, ...]]] = {
    fid: (lab, topic, kind, markers, prov + _K.get(fid, ()))
    for fid, (lab, topic, kind, markers, prov) in FEATURES2.items()
}
FEATURES.update(ADDED)


def kirchhoff_coverage() -> dict:
    """His group I traits keyed to a feature, and those not keyed (no feature, or no English
    marker word fit to find them)."""
    group1 = {k: v for k, v in KIRCHHOFF.items() if k.startswith("I.")}
    keyed = sorted((k for k, v in group1.items() if v[1]), key=lambda k: int(k.split(".")[1]))
    return {"group_I_traits": len(group1), "group_I_keyed": len(keyed),
            "group_I_keyed_codes": keyed,
            "group_I_not_keyed": [group1[k][0] for k in group1 if not group1[k][1]],
            "features_with_kirchhoff": sorted(f for f, v in FEATURES.items()
                                              if any(p.startswith("kirchhoff:") for p in v[4])),
            "mesoamerica_features_without_kirchhoff": sorted(
                f for f, v in FEATURES.items()
                if v[2] == MS and not any(p.startswith("kirchhoff:") for p in v[4]))}  # fmt: skip
