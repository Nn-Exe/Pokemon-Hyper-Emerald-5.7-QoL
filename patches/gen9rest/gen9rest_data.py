"""What gen9rest_patch.py adds: the hand-made half. The numbers (stats, types, level-up moves, what each can learn,
Pokedex text, move data) are the official Scarlet/Violet ones in official.json and moves.json (make_official.py);
this file says which Pokemon, in which slot, under which name, how they evolve, how each new ability and move is
carried over, which items are new, and where each Pokemon lives in the wild.

The rest of Gen 9: the 85 Pokemon gen9 did not add, plus Paldean Wooper and the three Paldean Tauros, as forms of
the Wooper and Tauros the game has (their Pokedex numbers). Slots go on from gen9's last (1237); Pokedex numbers
from 941, in National Dex order among themselves (the 38 of gen9 keep 906-940).
"""
FIRST_SLOT, FIRST_DEX = 1238, 941
# Pokedex categories longer than the 11 letters the game has room for
GENUS = {"armarouge": "FireWarrior", "wattrel": "StormPetrel", "grafaiai": "ToxicMonkey",
         "capsakid": "SpicyPepper", "scovillain": "SpicyPepper"}
# Pokedex texts where neither the Scarlet nor the Violet one fits the game's 4 lines of 38: Scarlet's, shortened
DEX_TEXT = {
    "pawmi": "Its cheek sacs are underdeveloped. They can make electricity only if Pawmi rubs them "
             "furiously with its paw pads.",
    "pawmo": "When its group is attacked, Pawmo leaps into battle first, beating foes with a fighting "
             "style that uses electric shocks.",
    "nacli": "It was born in rock salt deep underground. It was treasured long ago, as it would share "
             "its precious salt.",
}

# key (official.json), species for PokeAPI, name (10 characters at most), Crest species (pictures, cry, icon),
# the hack's species whose Pokedex number a form shares (None: a number of its own)
SPECIES = [
    ("sprigatito", "sprigatito", "Sprigatito", 906, None),
    ("floragato", "floragato", "Floragato", 907, None),
    ("meowscarada", "meowscarada", "Meowscarda", 908, None),
    ("fuecoco", "fuecoco", "Fuecoco", 909, None),
    ("crocalor", "crocalor", "Crocalor", 910, None),
    ("skeledirge", "skeledirge", "Skeledirge", 911, None),
    ("quaxly", "quaxly", "Quaxly", 912, None),
    ("quaxwell", "quaxwell", "Quaxwell", 913, None),
    ("quaquaval", "quaquaval", "Quaquaval", 914, None),
    ("lechonk", "lechonk", "Lechonk", 915, None),
    ("oinkologne", "oinkologne", "Oinkologne", 916, None),
    ("tarountula", "tarountula", "Tarountula", 917, None),
    ("spidops", "spidops", "Spidops", 918, None),
    ("nymble", "nymble", "Nymble", 919, None),
    ("lokix", "lokix", "Lokix", 920, None),
    ("pawmi", "pawmi", "Pawmi", 921, None),
    ("pawmo", "pawmo", "Pawmo", 922, None),
    ("pawmot", "pawmot", "Pawmot", 923, None),
    ("tandemaus", "tandemaus", "Tandemaus", 924, None),
    ("maushold", "maushold", "Maushold", 925, None),
    ("fidough", "fidough", "Fidough", 926, None),
    ("dachsbun", "dachsbun", "Dachsbun", 927, None),
    ("smoliv", "smoliv", "Smoliv", 928, None),
    ("dolliv", "dolliv", "Dolliv", 929, None),
    ("arboliva", "arboliva", "Arboliva", 930, None),
    ("squawkabilly", "squawkabilly", "Squawkbily", 931, None),
    ("nacli", "nacli", "Nacli", 932, None),
    ("naclstack", "naclstack", "Naclstack", 933, None),
    ("garganacl", "garganacl", "Garganacl", 934, None),
    ("charcadet", "charcadet", "Charcadet", 935, None),
    ("armarouge", "armarouge", "Armarouge", 936, None),
    ("ceruledge", "ceruledge", "Ceruledge", 937, None),
    ("tadbulb", "tadbulb", "Tadbulb", 938, None),
    ("bellibolt", "bellibolt", "Bellibolt", 939, None),
    ("wattrel", "wattrel", "Wattrel", 940, None),
    ("kilowattrel", "kilowattrel", "Kilowatrel", 941, None),
    ("maschiff", "maschiff", "Maschiff", 942, None),
    ("mabosstiff", "mabosstiff", "Mabosstiff", 943, None),
    ("shroodle", "shroodle", "Shroodle", 944, None),
    ("grafaiai", "grafaiai", "Grafaiai", 945, None),
    ("bramblin", "bramblin", "Bramblin", 946, None),
    ("brambleghast", "brambleghast", "Bramblghst", 947, None),
    ("toedscool", "toedscool", "Toedscool", 948, None),
    ("toedscruel", "toedscruel", "Toedscruel", 949, None),
    ("klawf", "klawf", "Klawf", 950, None),
    ("capsakid", "capsakid", "Capsakid", 951, None),
    ("scovillain", "scovillain", "Scovillain", 952, None),
    ("rellor", "rellor", "Rellor", 953, None),
    ("rabsca", "rabsca", "Rabsca", 954, None),
    ("flittle", "flittle", "Flittle", 955, None),
    ("espathra", "espathra", "Espathra", 956, None),
    ("tinkatink", "tinkatink", "Tinkatink", 957, None),
    ("tinkatuff", "tinkatuff", "Tinkatuff", 958, None),
    ("tinkaton", "tinkaton", "Tinkaton", 959, None),
    ("wiglett", "wiglett", "Wiglett", 960, None),
    ("wugtrio", "wugtrio", "Wugtrio", 961, None),
    ("bombirdier", "bombirdier", "Bombirdier", 962, None),
    ("finizen", "finizen", "Finizen", 963, None),
    ("palafin", "palafin", "Palafin", 964, None),
    ("varoom", "varoom", "Varoom", 965, None),
    ("revavroom", "revavroom", "Revavroom", 966, None),
    ("cyclizar", "cyclizar", "Cyclizar", 967, None),
    ("orthworm", "orthworm", "Orthworm", 968, None),
    ("glimmet", "glimmet", "Glimmet", 969, None),
    ("glimmora", "glimmora", "Glimmora", 970, None),
    ("greavard", "greavard", "Greavard", 971, None),
    ("houndstone", "houndstone", "Houndstone", 972, None),
    ("flamigo", "flamigo", "Flamigo", 973, None),
    ("cetoddle", "cetoddle", "Cetoddle", 974, None),
    ("cetitan", "cetitan", "Cetitan", 975, None),
    ("veluza", "veluza", "Veluza", 976, None),
    ("dondozo", "dondozo", "Dondozo", 977, None),
    ("tatsugiri", "tatsugiri", "Tatsugiri", 978, None),
    ("annihilape", "annihilape", "Annihilape", 979, None),
    ("clodsire", "clodsire", "Clodsire", 980, None),
    ("farigiraf", "farigiraf", "Farigiraf", 981, None),
    ("dudunsparce", "dudunsparce", "Dudunsprce", 982, None),
    ("kingambit", "kingambit", "Kingambit", 983, None),
    ("gimmighoul", "gimmighoul", "Gimmighoul", 999, None),
    ("gholdengo", "gholdengo", "Gholdengo", 1000, None),
    ("dipplin", "dipplin", "Dipplin", 1354, None),
    ("poltchageist", "poltchageist", "Poltchgist", 1355, None),
    ("sinistcha", "sinistcha", "Sinistcha", 1357, None),
    ("archaludon", "archaludon", "Archaludon", 1371, None),
    ("hydrapple", "hydrapple", "Hydrapple", 1372, None),
    # forms of Pokemon the game has: they keep that Pokemon's name and Pokedex number, as the hack's own regional
    # forms do (its Galarian Zigzagoon is "Zigzagoon", number 263)
    ("wooper-paldea", "wooper", "Wooper", 1114, "Wooper"),
    ("tauros-paldea-combat-breed", "tauros", "Tauros", 1115, "Tauros"),
    ("tauros-paldea-blaze-breed", "tauros", "Tauros", 1352, "Tauros"),
    ("tauros-paldea-aqua-breed", "tauros", "Tauros", 1353, "Tauros"),
]
# Experience groups PokeAPI gives that would split an evolution line (the game works the level out again from
# the experience when a Pokemon evolves: test 1's Applin at 30 became a Dipplin at 31). PokeAPI has Dipplin as
# Slow; Applin (the hack's) and Hydrapple are Erratic, as the whole Applin line is in Scarlet/Violet.
GROWTH_FIX = {"dipplin": "slow-then-very-fast"}       # Erratic
# Pokemon the game has that get a new evolution (their moves are fetched too: the move each needs)
EVOLVE_FROM_OLD = ["primeape", "girafarig", "dunsparce", "bisharp", "applin", "duraludon"]

# Evolution methods of this game (its own table, read from the ROM): 4 level, 7 an item used on it, 16 level up
# knowing a move (Tangela -> Tangrowth), 18 / 19 level by day / by night (Tyrunt / Amaura), 20 / 21 level up
# holding an item by day / by night (Sneasel and Razor Claw).
# (from, method, what: a level, an item key of ITEMS or the game's own item name, or a move key; to)
EVOLUTIONS = [
    ("sprigatito", 4, 16, "floragato"), ("floragato", 4, 36, "meowscarada"),
    ("fuecoco", 4, 16, "crocalor"), ("crocalor", 4, 36, "skeledirge"),
    ("quaxly", 4, 16, "quaxwell"), ("quaxwell", 4, 35, "quaquaval"),
    ("lechonk", 4, 18, "oinkologne"),
    ("tarountula", 4, 15, "spidops"),
    ("nymble", 4, 24, "lokix"),
    ("pawmi", 4, 18, "pawmo"),
    ("pawmo", 4, 32, "pawmot"),               # Scarlet/Violet: 1,000 steps walked beside you; here level 32
    ("tandemaus", 4, 25, "maushold"),
    ("fidough", 4, 26, "dachsbun"),
    ("smoliv", 4, 25, "dolliv"), ("dolliv", 4, 35, "arboliva"),
    ("nacli", 4, 24, "naclstack"), ("naclstack", 4, 38, "garganacl"),
    ("charcadet", 7, "auspicious-armor", "armarouge"), ("charcadet", 7, "malicious-armor", "ceruledge"),
    ("tadbulb", 7, "Thunder Stone", "bellibolt"),
    ("wattrel", 4, 25, "kilowattrel"),
    ("maschiff", 4, 30, "mabosstiff"),
    ("shroodle", 4, 28, "grafaiai"),
    ("bramblin", 4, 30, "brambleghast"),       # Scarlet/Violet: 1,000 steps walked beside you; here level 30
    ("toedscool", 4, 30, "toedscruel"),
    ("capsakid", 7, "Fire Stone", "scovillain"),
    ("rellor", 4, 29, "rabsca"),               # Scarlet/Violet: 1,000 steps walked beside you; here level 29
    ("flittle", 4, 35, "espathra"),
    ("tinkatink", 4, 24, "tinkatuff"), ("tinkatuff", 4, 38, "tinkaton"),
    ("wiglett", 4, 26, "wugtrio"),
    ("finizen", 4, 38, "palafin"),             # Scarlet/Violet: level 38 with another player; here level 38
    ("varoom", 4, 40, "revavroom"),
    ("glimmet", 4, 35, "glimmora"),
    ("greavard", 19, 30, "houndstone"),        # at night, as in Scarlet/Violet
    ("cetoddle", 7, "Ice Stone", "cetitan"),
    ("wooper-paldea", 4, 20, "clodsire"),
    ("gimmighoul", 4, 40, "gholdengo"),        # Scarlet/Violet: 999 Gimmighoul Coins; here level 40
    ("poltchageist", 7, "unremarkable-teacup", "sinistcha"),
    ("dipplin", 16, "dragon-cheer", "hydrapple"),
    # Pokemon the game has
    ("primeape", 16, "rage-fist", "annihilape"),       # Scarlet/Violet: Rage Fist used 20 times
    ("girafarig", 16, "twin-beam", "farigiraf"),
    ("dunsparce", 16, "hyper-drill", "dudunsparce"),
    ("bisharp", 20, "leaders-crest", "kingambit"),     # Scarlet/Violet: beat three Bisharp that hold one
    ("bisharp", 21, "leaders-crest", "kingambit"),
    ("applin", 7, "syrupy-apple", "dipplin"),
    ("duraludon", 7, "metal-alloy", "archaludon"),
]
# The move an evolution asks for, taught to the Pokemon the game has at the level Scarlet/Violet teaches it
# (where Scarlet/Violet's own list has it, that is used; these are the ones it lacks or the game's own lists)
TEACH_OLD = [("primeape", 35, "rage-fist"), ("girafarig", 32, "twin-beam"), ("dunsparce", 32, "hyper-drill")]

# New items: the game's unused "New Item" slots from 770 (769 is gen9's Booster Energy). Pictures from Crest,
# found by Crest's own spelling; Crest has no Metal Alloy: it gets this game's picture of the Metal Coat.
# key: (item id, name (13 at most), the picture: Crest's item name, or "game:" and this game's item name; how it
#       works: "stone" an evolution item used on a Pokemon, "held" an item held to evolve; price; text (3 x 18))
ITEMS = {
    "auspicious-armor": (770, "AuspciousArmr", "AuspciousArmr", "stone", 3000,
                         "Armor that makes\nCharcadet evolve\ninto Armarouge."),
    "malicious-armor": (771, "MaliciousArmr", "MaliciousArmr", "stone", 3000,
                        "Armor that makes\nCharcadet evolve\ninto Ceruledge."),
    "syrupy-apple": (772, "Syrupy Apple", "Syrupy Apple", "stone", 2200,
                     "A syrupy apple.\nApplin evolves\ninto Dipplin."),
    "metal-alloy": (773, "Metal Alloy", "game:Metal Coat", "stone", 3000,
                    "A metal alloy.\nDuraludon evolves\ninto Archaludon."),
    "unremarkable-teacup": (774, "UnrmkblTeacup", "UnrmkblTeacup", "stone", 1600,
                            "A cracked teacup.\nPoltchageist\nbecomes Sinistcha."),
    "leaders-crest": (775, "Leader'sCrest", "Leader'sCrest", "held", 3000,
                      "Bisharp holding it\nevolves when it\nlevels up."),
}

# ---------------------------------------------------------------------------------------------------------------
# Abilities the game does not have. No new battle code: each is an alias (gen9's convention: a name of its own, an
# id whose low byte is the ability it stands on, the base's own text because that is what it does here), handed to
# the engine as its base through gen9.s's alias list. The base is the game's ability that does the same, or part of
# it; where nothing does, Run Away or Illuminate (no effect in battle).
# official name: (name in the 12-character table, the base ability's name in this game)
ABILITY_ALIAS = {
    "lingering-aroma": ("Lingr. Aroma", "Mummy"),            # the same: the attacker's ability is replaced
    "armor-tail": ("Armor Tail", "Que. Majesty"),            # the same: priority moves fail against it
    "well-baked-body": ("WellBakedBdy", "Flash Fire"),       # Fire moves do nothing (no Defense +2)
    "earth-eater": ("Earth Eater", "Levitate"),              # Ground moves do nothing (no healing)
    "wind-rider": ("Wind Rider", "Sap Sipper"),              # absorbs Grass moves for Attack, not wind moves
    "wind-power": ("Wind Power", "Transistor"),              # Electric moves always stronger, no charging
    "electromorphosis": ("Electromorph", "Transistor"),      # the same
    "anger-shell": ("Anger Shell", "Berserk"),               # below half HP: Sp. Atk up (Berserk's own)
    "cud-chew": ("Cud Chew", "Ripen"),                       # berries work twice as well, not twice
    "good-as-gold": ("Good as Gold", "Magic Bounce"),        # status moves bounce back instead of failing
    "hospitality": ("Hospitality", "Healer"),                # may cure an ally's status instead of healing it
    "mycelium-might": ("MyceliumMght", "Mold Breaker"),      # ignores abilities (all moves), never moves last
    "purifying-salt": ("PurifyngSalt", "Natural Cure"),      # status cured on switching out
    "rocky-payload": ("RockyPayload", "Sand Force"),         # Rock moves x1.3 in any weather (the engine's Sand Force
                                                             # does not look at it; measured 2026-10-15), no sand damage
    "seed-sower": ("Seed Sower", "Grassy Surge"),            # Grassy Terrain on entry, not when hit
    "toxic-debris": ("Toxic Debris", "Poison Point"),        # poisons on contact, no Toxic Spikes
    "commander": ("Commander", "Run Away"),                  # needs Dondozo in a double battle: nothing here
    "costar": ("Costar", "Illuminate"),                      # copies an ally's stat changes: nothing here
    "opportunist": ("Opportunist", "Run Away"),
    "supersweet-syrup": ("SuprswtSyrup", "Illuminate"),      # (Run Away has five free ids, Illuminate five more)
    "supreme-overlord": ("SupremeOvlrd", "Run Away"),
    "zero-to-hero": ("Zero to Hero", "Run Away"),            # Palafin stays in its Zero Form
}
# Official ability names this game spells differently
ABILITY_NAMES = {"queenly-majesty": "Que. Majesty"}

# ---------------------------------------------------------------------------------------------------------------
# New moves. No new battle code: each row is copied from a move the game has that works the same way (its effect,
# chance, target, stat change, flags), and gets the official type, power, accuracy, PP and category; then the
# changes listed. Ids go on from gen9's last (947). Where the template does less than the real move, it says so.
# key, name (12), template, changes {field: value}, the move whose animation it borrows, description (2 x 30)
# fields: chance, target (0 one, 8 both foes, 32 all others), priority, flags (0x01 contact, 0x02 Protect,
# 0x10 Mirror Move, 0x20 King's Rock, 0x40 high critical-hit ratio), stat (byte 9: 16+n raise 1, 32+n raise 2,
# 144+n lower 1, 160+n lower 2; n 1 Atk 2 Def 3 Spe 4 SpA 5 SpD), type (where it is not the official one), power
FIRST_MOVE = 948
PLAIN = "Tackle"                    # effect 0, a plain hit
NEW_MOVES = [
    ("petal-blizzard", "PetalBlizzrd", "Boomburst", {}, "Petal Dance",
     "A violent petal blizzard that\nstrikes all other Pokémon."),
    ("axe-kick", "Axe Kick", "Hi Jump Kick", {}, "Hi Jump Kick",
     "A kick from above. The user\nis hurt if it misses."),                       # no confusion
    ("last-respects", "LastRespects", PLAIN, {"flags": 0x32}, "Shadow Claw",
     "Avenges fallen allies. Here a\nplain hit."),                                # no growth per fainted ally
    ("lumina-crash", "LuminaCrash", "Acid Spray", {}, "Psybeam",
     "A strange light that harshly\nlowers the foe's Sp. Def."),
    ("order-up", "Order Up", PLAIN, {"flags": 0x32}, "Dragon Claw",
     "An attack with great\nfinesse."),                                           # no stat boost
    ("jet-punch", "Jet Punch", "Aqua Jet", {}, "Aqua Jet",
     "A punch too fast to see.\nAlways strikes first."),
    ("spin-out", "Spin Out", "Hammer Arm", {"stat": 160 + 3}, "Gyro Ball",
     "A spinning strike. Harshly\nlowers the user's Speed."),
    ("population-bomb", "PopulatnBomb", "Bullet Seed", {"flags": 0x33}, "Fury Swipes",
     "Its family attacks together.\nHits two to five times."),                   # 2-5 hits, not up to 10
    ("ice-spinner", "Ice Spinner", PLAIN, {}, "Ice Punch",
     "Spins with icy feet to\nattack the foe."),                                  # leaves the terrain
    ("salt-cure", "Salt Cure", "Sand Tomb", {}, "Rock Tomb",
     "Cures the foe in salt. It is\nhurt every turn and trapped."),              # traps; 1/8 a turn
    ("triple-dive", "Triple Dive", "Double Kick", {"power": 45}, "Waterfall",
     "A perfectly timed dive that\nsplashes the foe. Hits twice."),              # 2 x 45 for 3 x 30
    ("mortal-spin", "Mortal Spin", "Rapid Spin", {"target": 8, "stat": 0}, "Rapid Spin",
     "A spin that removes hazards\nand traps from its side."),                   # no poison
    ("doodle", "Doodle", "Role Play", {}, "Sketch",
     "Copies the foe's Ability.\n"),
    ("fillet-away", "Fillet Away", "Shell Smash", {}, "Shell Smash",
     "Ups Attack, Sp. Atk and Speed\nsharply, lowers defenses."),                # Shell Smash's cost, not HP
    ("kowtow-cleave", "KowtowCleave", "Aerial Ace", {}, "Night Slash",
     "Slashes after a false kowtow.\nIt never misses."),
    ("flower-trick", "Flower Trick", "Aerial Ace", {"flags": 0x32 | 0x40}, "Magical Leaf",
     "A rigged bouquet. Never\nmisses, often a critical hit."),                  # not always critical
    ("torch-song", "Torch Song", "Charge Beam", {"chance": 100}, "Flamethrower",
     "Scorching flames sung out.\nRaises the user's Sp. Atk."),
    ("aqua-step", "Aqua Step", "Flame Charge", {}, "Waterfall",
     "Light, fluid dance steps.\nRaises the user's Speed."),
    ("raging-bull", "Raging Bull", "Brick Break", {"type": "fighting"}, "Take Down",
     "A tackle like a raging bull.\nBreaks Reflect and screens."),
    ("raging-bull-fire", "Raging Bull", "Brick Break", {"type": "fire"}, "Take Down",
     "A tackle like a raging bull.\nBreaks Reflect and screens."),
    ("raging-bull-water", "Raging Bull", "Brick Break", {"type": "water"}, "Take Down",
     "A tackle like a raging bull.\nBreaks Reflect and screens."),
    ("make-it-rain", "Make It Rain", "Overheat", {"target": 8, "stat": 144 + 4}, "Pay Day",
     "Throws coins at the foes.\nLowers the user's Sp. Atk."),
    ("tidy-up", "Tidy Up", "Dragon Dance", {}, "Bulk Up",
     "Raises the user's Attack and\nSpeed."),                                     # leaves hazards
    ("hyper-drill", "Hyper Drill", PLAIN, {"flags": 0x31}, "Drill Run",
     "A spinning drill. It goes\nthrough Protect and Detect."),
    ("twin-beam", "Twin Beam", "Double Kick", {"flags": 0x32}, "Psybeam",
     "Mystical eye beams that hit\nthe foe twice."),
    ("rage-fist", "Rage Fist", PLAIN, {}, "Shadow Punch",
     "A punch of pure rage. Here a\nplain hit."),                                 # no growth when hit
    ("armor-cannon", "ArmorCannon", "Close Combat", {"flags": 0x32}, "Fire Blast",
     "Shoots its armor. Lowers the\nuser's Defense and Sp. Def."),
    ("bitter-blade", "Bitter Blade", "Drain Punch", {}, "Fire Punch",
     "Slashes with flames. Restores\nhalf the damage dealt."),
    ("double-shock", "Double Shock", "Wild Charge", {}, "Volt Tackle",
     "All its electricity at once.\nThe user is hurt too."),                     # recoil, not the type loss
    ("gigaton-hammer", "GigatonHammr", "Giga Impact", {"flags": 0x32}, "Iron Head",
     "Swings its huge hammer. The\nuser must rest next turn."),                  # recharge, not "not twice"
    ("comeuppance", "Comeuppance", "Metal Burst", {}, "Payback",
     "Strikes back harder at the\nlast foe that hit it."),
    ("aqua-cutter", "Aqua Cutter", "Psycho Cut", {}, "Razor Shell",
     "Pressurized water like a\nblade. Often a critical hit."),
    ("matcha-gotcha", "MatchaGotcha", "Giga Drain", {"target": 8}, "Giga Drain",
     "Tea fired at the foes. Heals\nhalf the damage dealt."),                    # no burn
    ("syrup-bomb", "Syrup Bomb", "Icy Wind", {"target": 0}, "Seed Bomb",
     "Sticky syrup that lowers the\nfoe's Speed."),                              # once, not for 3 turns
    ("electro-shot", "Electro Shot", "Meteor Beam", {}, "Thunder",
     "Charges and ups Sp. Atk, then\nfires a high-voltage shot."),               # charges in rain too
    ("fickle-beam", "Fickle Beam", PLAIN, {"flags": 0x32}, "Dragon Pulse",
     "Shoots a beam of light from\neach of its heads."),                         # never doubles
    ("dragon-cheer", "Dragon Cheer", "Focus Energy", {}, "Focus Energy",
     "A cheer that makes critical\nhits more likely."),                          # the user, not its allies
    ("silk-trap", "Silk Trap", "Protect", {}, "String Shot",
     "Spins a silken trap that\nprotects it from attacks."),                     # no Speed drop on contact
]
# (official move, Pokemon) -> the key above, where a Pokemon learns a variant of its own
MOVE_BY_SPECIES = {
    ("raging-bull", "tauros-paldea-blaze-breed"): "raging-bull-fire",
    ("raging-bull", "tauros-paldea-aqua-breed"): "raging-bull-water",
}
# Scarlet/Violet moves of theirs that this game does not get: a Pokemon simply does not learn them here. The three
# first have no move in the game that works like them; the rest are TMs this game's TM list does not have.
MOVES_LEFT_OUT = {"revival-blessing", "shed-tail", "spicy-extract",
                  "tera-blast", "pounce", "trailblaze", "chilling-water", "hard-press", "alluring-voice",
                  "temper-flare", "supercell-slam", "psychic-noise", "upper-hand"}
# Moves added to a Pokemon's level-up list: Dipplin learns Dragon Cheer (its evolution move; a TM in Scarlet/Violet)
EXTRA_LEVELUP = {"dipplin": [(1, "dragon-cheer"), (35, "dragon-cheer")]}

# Where each lives in the wild (gen9rest_patch.py checks each slot): the table (gWildMonHeaders index), kind, the
# rate wanted (the slot of the Pokemon named whose rate is nearest), and the Pokemon the slot holds now. Every slot
# taken is either a second slot of a Pokemon that stays in that table, or a Pokemon found in at least three other
# places. Worked out against the ROM's 257 tables (2026-10-14): no Pokemon leaves the game. The levels are the
# slot's own.
WILD = [
    # the start of the game
    ("lechonk", 2, "land", 10, "Hoppip"), ("squawkabilly", 2, "land", 5, "Wingull"),
    ("nymble", 1, "land", 5, "Yungoos"), ("fidough", 1, "land", 5, "Patrat"),
    ("smoliv", 10, "land", 20, "Surskit"),
    ("tarountula", 14, "land", 10, "Skwovet"),
    ("nacli", 15, "land", 10, "Rockruff"),
    ("tandemaus", 10, "land", 10, "Growlithe"),
    ("tinkatink", 17, "land", 4, "Sableye"),
    ("glimmet", 23, "land", 1, "Machop"),
    # the middle, on foot
    ("pawmi", 5, "land", 10, "Emolga"),
    ("tadbulb", 5, "water", 5, "Wingull"),
    ("wattrel", 4, "water", 5, "Shellos"),
    ("varoom", 71, "land", 1, "Voltorb"),
    ("wooper-paldea", 11, "water", 5, "Magikarp"),
    ("sprigatito", 31, "land", 5, "Comfey"),
    ("flittle", 6, "land", 10, "Diglett"),
    ("capsakid", 7, "land", 10, "Houndour"),
    ("charcadet", 24, "land", 1, "Numel"),
    ("fuecoco", 8, "land", 1, "Houndour"), ("maschiff", 8, "land", 10, "Houndour"),
    ("klawf", 26, "land", 10, "Gligar"),
    ("rellor", 110, "land", 10, "Sandshrew"),
    ("bramblin", 107, "land", 10, "Golett"),
    ("orthworm", 109, "land", 5, "Larvitar"),
    ("quaxly", 90, "water", 5, "Marill"),
    ("cyclizar", 12, "land", 10, "Pachirisu"),
    # after Surf
    ("shroodle", 33, "land", 1, "Gloom"),
    ("toedscool", 34, "land", 10, "Komala"),
    ("bombirdier", 37, "land", 10, "Slowpoke"), ("flamigo", 37, "land", 10, "Teddiursa"),
    ("greavard", 40, "land", 10, "Gastly"),
    ("poltchageist", 43, "land", 5, "Vulpix"),
    ("gimmighoul", 93, "land", 5, "Minior"),
    ("cetoddle", 80, "land", 10, "Golbat"),
    ("tauros-paldea-combat-breed", 74, "land", 4, "Foongus"),
    ("tauros-paldea-blaze-breed", 98, "land", 1, "Ledyba"),
    ("tauros-paldea-aqua-breed", 97, "land", 5, "Snorlax"),
    ("wiglett", 30, "water", 5, "Cramorant"),
    ("finizen", 13, "water", 5, "Tentacool"),
    # late
    ("veluza", 49, "fish", 15, "Swanna"),
    ("tatsugiri", 50, "fish", 15, "Pelipper"), ("dondozo", 50, "water", 1, "Mantine"),
    # after the story: Pal Park, where the hack keeps the other Fire and Water starters
    ("fuecoco", 202, "land", 4, "Scorbunny"), ("quaxly", 202, "fish", 15, "Sobble"),
]
