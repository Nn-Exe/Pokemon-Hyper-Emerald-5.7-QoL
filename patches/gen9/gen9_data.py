"""What gen9_patch.py adds: the hand-made half. The numbers (stats, types, level-up moves, what each can learn,
Pokedex text) are the official Scarlet/Violet ones in official.json; this file says which species, in which slot,
under which name, how each ability is carried over, which moves are new, and what Booster Energy is.

Slots follow the National Dex order. Hyper Emerald's own Pokedex stops at 905 and has room up to 959, so the
new ones are numbered 906 onward in the game: the flag arrays in the save cannot hold the official 984-1025.
"""
FIRST_SLOT, FIRST_DEX = 1200, 906

# official.json key, the name in the 10-character table, Crest species for pictures and cry, Crest species for the
# icon, True when it shares the previous entry's dex number (another form of the same Pokemon)
SPECIES = [
    ("great-tusk",               "Great Tusk", 984, 984, False),
    ("scream-tail",              "ScreamTail", 985, 985, False),
    ("brute-bonnet",             "BruteBonet", 986, 986, False),
    ("flutter-mane",             "FluttrMane", 987, 987, False),
    ("slither-wing",             "SlithrWing", 988, 988, False),
    ("sandy-shocks",             "SndyShocks", 989, 989, False),
    ("iron-treads",              "IronTreads", 990, 990, False),
    ("iron-bundle",              "IronBundle", 991, 991, False),
    ("iron-hands",               "Iron Hands", 992, 992, False),
    ("iron-jugulis",             "IronJuguls", 993, 993, False),
    ("iron-moth",                "Iron Moth", 994, 994, False),
    ("iron-thorns",              "IronThorns", 995, 995, False),
    ("frigibax",                 "Frigibax", 996, 996, False),
    ("arctibax",                 "Arctibax", 997, 997, False),
    ("baxcalibur",               "Baxcalibur", 998, 998, False),
    ("wo-chien",                 "Wo-Chien", 1001, 1001, False),
    ("chien-pao",                "Chien-Pao", 1002, 1002, False),
    ("ting-lu",                  "Ting-Lu", 1003, 1003, False),
    ("chi-yu",                   "Chi-Yu", 1004, 1004, False),
    ("roaring-moon",             "RoarngMoon", 1005, 1005, False),
    ("iron-valiant",             "IronVliant", 1006, 1006, False),
    ("koraidon",                 "Koraidon", 1007, 1007, False),
    ("miraidon",                 "Miraidon", 1008, 1008, False),
    ("walking-wake",             "WalkngWake", 1009, 1009, False),
    ("iron-leaves",              "IronLeaves", 1010, 1010, False),
    ("okidogi",                  "Okidogi", 1359, 1359, False),
    ("munkidori",                "Munkidori", 1360, 1360, False),
    ("fezandipiti",              "Fezndipiti", 1361, 1361, False),
    ("ogerpon",                  "Ogerpon", 1362, 1362, False),
    ("ogerpon-wellspring-mask",  "Ogerpon", 1363, 1363, True),
    ("ogerpon-hearthflame-mask", "Ogerpon", 1364, 1364, True),
    ("ogerpon-cornerstone-mask", "Ogerpon", 1365, 1365, True),
    ("gouging-fire",             "GouginFire", 1373, 1373, False),
    ("raging-bolt",              "RagingBolt", 1374, 1374, False),
    ("iron-boulder",             "IronBouldr", 1375, 1375, False),
    ("iron-crown",               "Iron Crown", 1376, 1376, False),
    # Terapagos is in its Terastal Form, the one it always takes in battle (the Normal and Stellar Forms need
    # Terastallizing); Crest has no icon for that form, so the Normal Form's is used, as in the official games
    ("terapagos-terastal",       "Terapagos", 1378, 1377, False),
    ("pecharunt",                "Pecharunt", 1380, 1380, False),
]
EVOLUTIONS = [("frigibax", 35, "arctibax"), ("arctibax", 54, "baxcalibur")]      # by level

TYPES = {"normal": 0, "fighting": 1, "flying": 2, "poison": 3, "ground": 4, "rock": 5, "bug": 6, "ghost": 7,
         "steel": 8, "fire": 10, "water": 11, "grass": 12, "electric": 13, "psychic": 14, "ice": 15, "dragon": 16,
         "dark": 17, "fairy": 23}
COLORS = {"red": 0, "blue": 1, "yellow": 2, "green": 3, "black": 4, "brown": 5, "purple": 6, "gray": 7,
          "white": 8, "pink": 9}
GROWTH = {"medium": 0, "slow-then-very-fast": 1, "fast-then-very-slow": 2, "medium-slow": 3, "fast": 4, "slow": 5}
EGG_GROUPS = {"monster": 1, "water1": 2, "bug": 3, "flying": 4, "ground": 5, "fairy": 6, "plant": 7,
              "humanshape": 8, "water3": 9, "mineral": 10, "indeterminate": 11, "water2": 12, "ditto": 13,
              "dragon": 14, "no-eggs": 15}

# ---------------------------------------------------------------------------------------------------------------
# Abilities. The engine keeps a battler's ability as a 16-bit id and knows 1-254 plus a few of its own above 255.
#
# ABILITY_EXISTING   the engine already has it: the species table gets that id.
# ABILITY_ALIAS      a name and text of its own (id = 256 + the ability it stands on, the hack's own convention
#                    for Shell Armor, White Smoke...), and gen9.s hands the engine the base ability when the
#                    Pokemon enters battle, so everything the base does, it does. Two of them get the rest of
#                    their real effect from gen9.s (the damage hook); for the others the text is the base's own,
#                    because that is what they do here.
# ABILITY_NEW        an id the engine does not know, so it does nothing by itself; gen9.s gives it its effect.
ABILITY_EXISTING = {"defiant": 128, "water-absorb": 11, "mold-breaker": 104, "sturdy": 5, "frisk": 119,
                    "technician": 101, "ice-body": 115}
# official name: (id, name in the 12-character table, base ability, text or None for the base's own)
ABILITY_ALIAS = {
    "orichalcum-pulse": (326, "Orich. Pulse", 70, "Turns the sunlight harsh.\nIn sun, Attack is up 33%."),
    "hadron-engine":    (420, "HadronEngine", 164, "Sets Electric Terrain.\nOn it, Sp. Atk is up 33%."),
    "toxic-chain":      (399, "Toxic Chain", 143, None),        # Poison Touch
    "guard-dog":        (295, "Guard Dog", 39, None),           # Inner Focus
    "tera-shell":       (487, "Tera Shell", 231, None),         # Shadow Shield
    "poison-puppeteer": (452, "P. Puppeteer", 196, None),       # Merciless
    "thermal-exchange": (297, "ThermalExch.", 41, None),        # Water Veil
}
# official name: (id, name, text). The low byte of each id is 0, "no ability", for the code that reads one byte.
ABILITY_NEW = {
    "tablets-of-ruin": (512, "Tablets Ruin", "Lowers the Attack of all\nother Pokémon by 25%."),
    "sword-of-ruin":   (768, "SwordOfRuin", "Lowers the Defense of all\nother Pokémon by 25%."),
    "vessel-of-ruin":  (1024, "VesselOfRuin", "Lowers the Sp. Atk of all\nother Pokémon by 25%."),
    "beads-of-ruin":   (1280, "BeadsOfRuin", "Lowers the Sp. Def of all\nother Pokémon by 25%."),
    "protosynthesis":  (1536, "Protosynth.", "Harsh sunlight or Booster\nEnergy ups its best stat."),
    "quark-drive":     (1792, "Quark Drive", "Electric Terrain or Booster\nEnergy ups its best stat."),
}
ABILITY_COUNT = 1793                 # the name and text tables after the patch: ids 0..1792

# ---------------------------------------------------------------------------------------------------------------
# Moves. Official name -> the name Hyper Emerald's 12-character table gives the same move, where the two differ
# by more than spaces, punctuation and case. Checked by hand: matching by likeness pairs Thousand Waves with
# Thunder Wave and Pounce with Bounce.
MOVE_NAMES = {
    "breaking-swipe": "Break. Swipe", "burning-jealousy": "B. Jealousy", "dazzling-gleam": "Dazzle Gleam",
    "disarming-voice": "Disarm Voice", "electric-terrain": "Elec Terrain", "expanding-force": "Expand.Force",
    "first-impression": "1st Impress.", "grassy-terrain": "GrassTerrain", "high-horsepower": "HiHorsepower",
    "misty-explosion": "M. Explosion", "parabolic-charge": "Para Charge", "psychic-fangs": "Psychic Fang",
    "psychic-terrain": "Psy Terrain", "rising-voltage": "Rising Volt.", "scorching-sands": "Scorch.Sands",
    "stomping-tantrum": "StompTantrum",
    "snowscape": "Hail",             # Snowscape replaced Hail in Scarlet/Violet; this engine has Hail
}
# Moves of Scarlet/Violet this engine does not have and this patch does not add. Nothing is put in their place:
# a Pokemon simply does not learn them here. The patcher stops if a move is missing from the game and is neither
# on this list nor among NEW_MOVES.
MOVES_NOT_IN_GAME = {
    "alluring-voice", "burning-bulwark", "chilling-water", "dragon-cheer", "hard-press", "ice-spinner",
    "malignant-chain", "mighty-cleave", "pounce", "psychic-noise", "supercell-slam", "tachyon-cutter",
    "temper-flare", "tera-blast", "tera-starstorm", "thunderclap", "trailblaze", "upper-hand",
}

# ---------------------------------------------------------------------------------------------------------------
# New moves: the signature moves Crest has too (seven of the thirteen; the other six are in neither game).
# The engine's move tables hold ids 0-937; the new ones are 938 onward. The numbers are Scarlet/Violet's.
#
# Ivy Cudgel is four moves, one for each of Ogerpon's masks: this engine picks a move's type by its id, and the
# four masks are four species here, so each learns the Ivy Cudgel of its own type.
#
# What each does beyond a plain hit:
#   Collision Course, Electro Drift   x 4/3 when super effective                                    gen9.s
#   Hydro Steam                       x 3 in harsh sunlight (the engine halves Water there: x 1.5)  gen9.s
#   Psyblade                          x 3/2 on Electric Terrain                                     gen9.s
#   Glaive Rush                       the user takes double damage until it next moves              gen9.s
#   Ruination                         half the target's HP. Its effect is the engine's "a set amount",
#                                     where the engine goes by the move's number: gen9.s names it   gen9.s
#   Ivy Cudgel                        high critical-hit ratio: a flag the engine has
FIRST_MOVE, MOVE_COUNT = 938, 1024
PLAIN_HIT, SET_DAMAGE = 0, 1                     # the engine's effect ids: Tackle's; Super Fang's, Seismic Toss's
CONTACT, PROTECT, MIRROR_MOVE, KINGS_ROCK, HIGH_CRIT = 0x01, 0x02, 0x10, 0x20, 0x40
HIT = PROTECT | MIRROR_MOVE | KINGS_ROCK
# key, name in the 12-character table, type, 0 physical / 1 special, power, accuracy, PP, effect, flags,
# the move whose animation it borrows, Z-Move power, Max Move power, description (two lines of 30 at most)
NEW_MOVES = [
    ("collision-course", "Coll. Course", "fighting", 0, 100, 100, 5, PLAIN_HIT, HIT | CONTACT, "Close Combat",
     180, 90, "A fierce prehistoric charge.\nStronger if super effective."),
    ("electro-drift", "ElectroDrift", "electric", 1, 100, 100, 5, PLAIN_HIT, HIT | CONTACT, "Volt Tackle",
     180, 130, "Pierces with electricity.\nStronger if super effective."),
    ("ruination", "Ruination", "dark", 1, 1, 90, 10, SET_DAMAGE, HIT, "Night Daze",
     100, 100, "Summons a ruinous disaster\nthat halves the foe’s HP."),
    ("ivy-cudgel", "Ivy Cudgel", "grass", 0, 100, 100, 10, PLAIN_HIT, HIT | HIGH_CRIT, "Wood Hammer",
     180, 130, "Strikes with an ivy cudgel.\nHas a high critical-hit ratio."),
    ("ivy-cudgel-water", "Ivy Cudgel", "water", 0, 100, 100, 10, PLAIN_HIT, HIT | HIGH_CRIT, "Crabhammer",
     180, 130, "Strikes with an ivy cudgel.\nHas a high critical-hit ratio."),
    ("ivy-cudgel-fire", "Ivy Cudgel", "fire", 0, 100, 100, 10, PLAIN_HIT, HIT | HIGH_CRIT, "Fire Punch",
     180, 130, "Strikes with an ivy cudgel.\nHas a high critical-hit ratio."),
    ("ivy-cudgel-rock", "Ivy Cudgel", "rock", 0, 100, 100, 10, PLAIN_HIT, HIT | HIGH_CRIT, "Stone Edge",
     180, 130, "Strikes with an ivy cudgel.\nHas a high critical-hit ratio."),
    ("hydro-steam", "Hydro Steam", "water", 1, 80, 100, 15, PLAIN_HIT, HIT, "Scald",
     160, 130, "Blasts boiling-hot water.\nStronger in harsh sunlight."),
    ("psyblade", "Psyblade", "psychic", 0, 80, 100, 15, PLAIN_HIT, HIT | CONTACT, "Psycho Cut",
     160, 130, "Rends with an ethereal blade.\nStronger on Electric Terrain."),
    ("glaive-rush", "Glaive Rush", "dragon", 0, 120, 100, 5, PLAIN_HIT, HIT | CONTACT, "Dragon Rush",
     190, 140, "A reckless charge. The user\nthen takes double damage."),
]
# (official move, species) -> the key above, where a species learns a variant of its own
MOVE_BY_SPECIES = {
    ("ivy-cudgel", "ogerpon-wellspring-mask"): "ivy-cudgel-water",
    ("ivy-cudgel", "ogerpon-hearthflame-mask"): "ivy-cudgel-fire",
    ("ivy-cudgel", "ogerpon-cornerstone-mask"): "ivy-cudgel-rock",
}

# ---------------------------------------------------------------------------------------------------------------
# Booster Energy: a held item that sets Protosynthesis or Quark Drive off once, without sun or Electric Terrain,
# and is used up. It takes the first of the game's unused item slots ("New Item", 769-799); its picture is read
# from the Crest ROM (item 771 there). gen9.s knows it by its id, so it needs no hold effect of its own.
BOOSTER_ENERGY, CREST_BOOSTER_ENERGY = 769, 771
BOOSTER_NAME = "BoosterEnergy"
BOOSTER_TEXT = "A hold item. Used up\nto start Protosynth.\nor Quark Drive."
