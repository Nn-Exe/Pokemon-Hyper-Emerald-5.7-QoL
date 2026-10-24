"""What gen9abil gives the game: the Gen 9 abilities at ids of their own, their names and texts, and the battle
messages its code prints.

The engine numbers abilities with 16 bits and leaves most ids from 0x101 to 0x14C free (it has five of its own
there: Shell Armor 0x104, Air Lock 0x10D, Burning Soul 0x112, White Smoke 0x11D, Pure Power 0x125). The Gen 9
abilities take the free ones. Sharpness (0x4F) the engine already has.
"""

# official name: (id, name in the 12-character table, the summary screen's text: two lines)
ABILITIES = {
    "lingering-aroma":  (0x101, "Lingr. Aroma", "Contact changes the\nattacker's Ability."),
    "seed-sower":       (0x102, "Seed Sower", "Turns the ground into\nGrassy Terrain when hit."),
    "thermal-exchange": (0x103, "ThermalExch.", "Fire moves up Attack.\nCannot be burned."),
    "anger-shell":      (0x105, "Anger Shell", "Below half HP: offense up,\ndefense down."),
    "purifying-salt":   (0x106, "PurifyngSalt", "Prevents status. Halves\nGhost-type damage."),
    "well-baked-body":  (0x107, "WellBakedBdy", "Fire moves boost its\nDefense instead."),
    "wind-rider":       (0x108, "Wind Rider", "Wind moves and Tailwind\nboost its Attack."),
    "guard-dog":        (0x109, "Guard Dog", "Intimidate ups its Attack.\nCannot be forced out."),
    "rocky-payload":    (0x10A, "RockyPayload", "Powers up Rock-type\nmoves."),
    "wind-power":       (0x10B, "Wind Power", "A wind move charges it:\nits next Electric move."),
    "zero-to-hero":     (0x10C, "Zero to Hero", "Turns into its Hero Form\nwhen switched out."),
    "commander":        (0x10E, "Commander", "Goes inside an ally\nDondozo's mouth."),
    "electromorphosis": (0x10F, "Electromorph", "Getting hit charges it:\nits next Electric move."),
    "protosynthesis":   (0x110, "Protosynth.", "Harsh sunlight or Booster\nEnergy ups its best stat."),
    "quark-drive":      (0x111, "Quark Drive", "Electric Terrain or Booster\nEnergy ups its best stat."),
    "good-as-gold":     (0x113, "Good as Gold", "Not affected by other\nPokémon's status moves."),
    "vessel-of-ruin":   (0x114, "VesselOfRuin", "Lowers the Sp. Atk of all\nother Pokémon."),
    "sword-of-ruin":    (0x115, "SwordOfRuin", "Lowers the Defense of all\nother Pokémon."),
    "tablets-of-ruin":  (0x116, "Tablets Ruin", "Lowers the Attack of all\nother Pokémon."),
    "beads-of-ruin":    (0x117, "BeadsOfRuin", "Lowers the Sp. Def of all\nother Pokémon."),
    "orichalcum-pulse": (0x118, "Orich. Pulse", "Turns the sunlight harsh.\nIn sun, its moves hit harder."),
    "hadron-engine":    (0x119, "HadronEngine", "Sets Electric Terrain. On\nit, its moves hit harder."),
    "opportunist":      (0x11A, "Opportunist", "Copies the stat boosts\nits foes get."),
    "cud-chew":         (0x11B, "Cud Chew", "Eats a used Berry again\nat the next turn's end."),
    "supreme-overlord": (0x11C, "SupremeOvlrd", "Stronger for each ally\nthat has fainted."),
    "costar":           (0x11E, "Costar", "Copies its ally's stat\nchanges on entering."),
    "toxic-debris":     (0x11F, "Toxic Debris", "Physical hits scatter\nToxic Spikes."),
    "armor-tail":       (0x120, "Armor Tail", "Foes cannot use priority\nmoves on its side."),
    "earth-eater":      (0x121, "Earth Eater", "Ground moves restore\nits HP instead."),
    "mycelium-might":   (0x122, "MyceliumMght", "Status moves go last but\nignore Abilities."),
    "toxic-chain":      (0x123, "Toxic Chain", "Its hits may badly\npoison the target."),
    "supersweet-syrup": (0x124, "SuprswtSyrup", "Lowers the foes' evasion\nthe first time it enters."),
    "hospitality":      (0x126, "Hospitality", "Restores its ally's HP\nwhen it enters."),
    "minds-eye":        (0x127, "Mind's Eye", "Ignores evasion. Hits\nGhosts with Normal/Fighting."),
    "embody-aspect":    (0x128, "EmbodyAspect", "The mask's power ups\none of its stats."),
    "tera-shift":       (0x129, "Tera Shift", "Turns into its Terastal\nForm on entering."),
    "tera-shell":       (0x12A, "Tera Shell", "At full HP, every hit is\nnot very effective."),
    "teraform-zero":    (0x12B, "TeraformZero", "Removes all weather and\nterrain."),
    "poison-puppeteer": (0x12C, "P. Puppeteer", "Those it poisons become\nconfused as well."),
}

# the free ids gen9abil may take: every id above must be one of them, and blank in the name table today
FREE_IDS = [i for i in range(0x101, 0x14D) if i not in (0x104, 0x10D, 0x112, 0x11D, 0x125)]
# Gen 9 abilities the engine already has, by official name
EXISTING = {"sharpness": 0x4F}

# Booster Energy (item 769) gets a hold effect of its own, one the engine has no case for (its last is 0xA7), so
# that Klutz, Embargo and Magic Room stop it the way they stop every held item (get_item_effect)
BOOSTER_ENERGY, BOOSTER_EFFECT = 769, 0xAB

# Battle messages, at the engine's string ids from FIRST_STRING on (its own table ends at 0x2B6). Placeholders as
# the engine has them: {ATK} {DEF} {SCR} the attacker's, target's, scripting battler's name with its prefix;
# {ATK_ABIL} {DEF_ABIL} {SCR_ABIL} their abilities; {BUFF1} gBattleTextBuff1. Two lines at most.
FIRST_STRING = 0x2B7
STRINGS = [
    ("S_TABLETS", "{SCR}'s {SCR_ABIL} weakened\nthe Attack of all around it!"),
    ("S_SWORD", "{SCR}'s {SCR_ABIL} weakened\nthe Defense of all around it!"),
    ("S_VESSEL", "{SCR}'s {SCR_ABIL} weakened\nthe Sp. Atk of all around it!"),
    ("S_BEADS", "{SCR}'s {SCR_ABIL} weakened\nthe Sp. Def of all around it!"),
    ("S_PARADOX_ATK", "{SCR}'s Attack\nwas heightened!"),
    ("S_PARADOX_DEF", "{SCR}'s Defense\nwas heightened!"),
    ("S_PARADOX_SPEED", "{SCR}'s Speed\nwas heightened!"),
    ("S_PARADOX_SPATK", "{SCR}'s Sp. Atk\nwas heightened!"),
    ("S_PARADOX_SPDEF", "{SCR}'s Sp. Def\nwas heightened!"),
    ("S_PROTO_SUN", "The harsh sunlight activated\n{SCR}'s Protosynthesis!"),
    ("S_QUARK_TERRAIN", "The Electric Terrain activated\n{SCR}'s Quark Drive!"),
    ("S_BOOSTER_PROTO", "{SCR} used its Booster Energy\nto activate Protosynthesis!"),
    ("S_BOOSTER_QUARK", "{SCR} used its Booster Energy\nto activate Quark Drive!"),
    ("S_END_PROTO", "The effects of {SCR}'s\nProtosynthesis wore off!"),
    ("S_END_QUARK", "The effects of {SCR}'s\nQuark Drive wore off!"),
    ("S_ORICHALCUM", "{SCR} turned the sunlight harsh,\nsending its ancient pulse into a frenzy!"),
    ("S_ORICHALCUM_ON", "{SCR} basked in the sunlight,\nsending its ancient pulse into a frenzy!"),
    ("S_HADRON", "{SCR} made Electric Terrain,\nenergizing its futuristic engine!"),
    ("S_HADRON_ON", "{SCR} used the Electric Terrain\nto energize its futuristic engine!"),
    ("S_OVERLORD", "{SCR} gained strength\nfrom the fallen!"),
    ("S_CHARGE", "Being hit by {MOVE} charged\n{DEF} with power!"),
    ("S_TOXIC_DEBRIS", "Poison spikes were scattered all\naround the opposing team's feet!"),
    ("S_CHARGE_ATK", "Being hit by {MOVE} charged\n{ATK} with power!"),
    ("S_SYRUP", "A supersweet aroma is wafting from\nthe syrup covering {ATK}!"),
    ("S_HOSPITALITY", "{DEF} drank down all the\nmatcha that {ATK} made!"),
    ("S_TERA_SHELL", "{DEF} made its shell gleam!\nIt's distorting type matchups!"),
    ("S_COMMANDER", "{SCR} was swallowed by\n{DEF} and became its commander!"),
]

# Sharpness (x1.5 for slicing moves): the engine's list of slicing moves ends at Ceaseless Edge. These are the
# Gen 9 slicing moves the game has, by their names in its move name table (header 0x148); Mighty Cleave and
# Tachyon Cutter are not in the game.
SLICING_NEW = ["Psyblade", "PopulatnBomb", "KowtowCleave", "Bitter Blade", "Aqua Cutter"]

# The engine's lists of abilities that moves and abilities cannot touch, each ending in 0xFFFF (first entries as a
# check), and the Gen 9 abilities each gets (by ABILITIES' keys). The engine reads each from a few literals; the
# patcher writes longer copies and points every literal at them.
FORBIDDEN = [
    # cannot be swapped (Skill Swap, Wandering Spirit)
    (0x09D79E36, (25, 176, 149, 121), 16,
     ["zero-to-hero", "protosynthesis", "quark-drive", "embody-aspect", "tera-shift", "tera-shell", "teraform-zero",
      "poison-puppeteer", "commander"]),
    # cannot be suppressed (Gastro Acid, Neutralizing Gas)
    (0x09D79E1A, (121, 176, 208), 13, ["zero-to-hero", "tera-shift"]),
    # cannot be copied (Role Play, Trace, Receiver, Power of Alchemy)
    (0x09D79E74, (25, 176, 121, 149), 23,
     ["zero-to-hero", "protosynthesis", "quark-drive", "embody-aspect", "tera-shift", "tera-shell", "teraform-zero",
      "poison-puppeteer", "commander"]),
    # cannot be replaced (Entrainment, Simple Beam, Worry Seed, Mummy, Lingering Aroma)
    (0x09D79E58, (121, 54, 176), 13, ["zero-to-hero", "embody-aspect", "tera-shift"]),
]

# Routines battle scripts call by number (the engine's callasm command): its table of 220 gets a longer copy, and
# these are numbers 220 on, in this order (build.py writes callasm.inc for scripts.s)
CALLASM_FIRST = 220
CALLASM = ["g9_asm_tailwind", "g9_asm_opportunist"]
