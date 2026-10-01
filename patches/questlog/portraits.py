"""Portraits and locations for the Quest Log's info panel (Unbound-style: a picture, "Location:", a short text).

A portrait is ("t", trainer pic id), ("m", "Species name"), ("s", species number - for forms that share a
name), ("i", item id) or None (an empty box). Trainer pic ids
are indices into the trainer front-pic table (tools/romdata/dump_trainers.py gives each trainer's `pic`).
The no-spoiler rule of the Journal holds: a step whose text hides who waits there has no portrait.

JOURNAL: one (location, portrait) per Journal step, in steps.py order, then one for the closing row.
SIDE:    per Side Content flag. Key Items use their own item icon; Legends their own Pokemon (a silhouette until
         seen); their locations are taken from their texts (LOC_OVERRIDE fixes the few that need it).
"""

ANABEL, STEVEN, NANU, FABA = ("t", 82), ("t", 81), ("t", 149), ("t", 134)
AQUA, MAGMA, PLASMA, ROCKET = ("t", 6), ("t", 26), ("t", 234), ("t", 228)

JOURNAL = [
    ("Route 101", ("m", "Zigzagoon")),                   # 1 Help Prof. Birch
    ("Route 103", ("m", "Mudkip")),                      # 2 Get the Pokedex
    ("Rustboro City", ("t", 40)),                        # 3 Roxanne
    ("Rusturf Tunnel", AQUA),                            # 4 the Aqua grunt
    ("Rustboro City", ("i", 269)),                       # 5 Devon Goods
    ("Granite Cave", STEVEN),                            # 6 a letter for Steven
    ("Dewford Town", ("t", 41)),                         # 7 Brawly
    ("Slateport City", ("i", 269)),                      # 8 deliver the Devon Goods
    ("Mauville City", ("t", 42)),                        # 9 Wattson
    ("Meteor Falls", MAGMA),                             # 10 chase Team Magma
    ("Lavaridge Town", ("t", 43)),                       # 11 Flannery
    ("Petalburg City", ("t", 44)),                       # 12 Norman
    ("Weather Institute", ("m", "Castform")),            # 13
    ("Fortree City", ("t", 45)),                         # 14 Winona
    ("Mt. Pyre", ("m", "Duskull")),                      # 15
    ("Magma Hideout", ("t", 76)),                        # 16 Maxie
    ("Aqua Hideout", ("t", 13)),                         # 17 Archie
    ("Shoal Cave", PLASMA),                              # 18
    ("Mossdeep City", ("t", 46)),                        # 19 Tate & Liza
    ("Mossdeep City", MAGMA),                            # 20 the Space Center
    ("Seafloor Cavern", ("t", 13)),                      # 21
    ("Sootopolis City", ("m", "Rayquaza")),              # 22 (the text names Rayquaza)
    ("Sootopolis City", ("t", 47)),                      # 23 Juan
    ("Ever Grande City", ("t", 121)),                    # 24 the League
    ("Littleroot Town", NANU),                           # 25 Interpol
    ("Steven's Island", STEVEN),                         # 26
    ("Petalburg City", ("t", 70)),                       # 27 Wally
    ("Rustboro City", STEVEN),                           # 28
    ("Granite Cave", ("t", 100)),                        # 29 Zinnia
    ("Mossdeep City", ("i", 280)),                       # 30 the meteorite
    ("Meteor Falls", MAGMA),                             # 31
    ("Meteor Falls", ("t", 100)),                        # 32 Zinnia
    ("Sky Pillar", ("m", "Rayquaza")),                   # 33
    ("Sky Pillar", ("m", "Rayquaza")),                   # 34 (what waits beyond the sky stays hidden)
    ("Mossdeep City", ("t", 121)),                       # 35 Wallace
    ("Meteor Falls", ANABEL),                            # 36
    ("Pacifidlog Town", ANABEL),                         # 37
    ("Steven's Island", ANABEL),                         # 38
    ("Route 111", ("t", 139)),                           # 39 Gladion
    ("Strange Island", ("t", 157)),                      # 40 the Kahunas (Hala)
    ("Steven's Island", NANU),                           # 41
    ("Steven's Island", ("t", 31)),                      # 41b the Devon Scout (a Scientist): his report opens the wormhole
    ("Scorched Slab", FABA),                             # 42
    ("Steven's Island", ANABEL),                         # 43
    ("Steven's Island", STEVEN),                         # 44 train with the Champions
    ("Steven's Island", ANABEL),                         # 45
    ("Hoenn", ("m", "Castform")),                        # 46 the strange weather
    ("Steven's Island", ANABEL),                         # 47
    ("Mt. Pyre", ANABEL),                                # 48
    ("Steven's Island", ANABEL),                         # 49
    ("Shoal Cave", ANABEL),                              # 50
    ("Steven's Island", ANABEL),                         # 51
    ("Route 116", ANABEL),                               # 52
    ("Steven's Island", ANABEL),                         # 53
    ("Mirage Tower", FABA),                              # 54
    ("Steven's Island", ANABEL),                         # 55
    ("Meteor Falls", ("t", 94)),                         # 56 Red
    ("Steven's Island", ANABEL),                         # 57
    ("Pacifidlog Town", ROCKET),                         # 58 the Z-Crystals
    ("Rainbow Castle", ("t", 127)),                      # 59 Giovanni
    ("Steven's Island", STEVEN),                         # 60
    ("Battle Frontier", ANABEL),                         # 61 a Silver Symbol
    ("Lilycove City", ("i", 371)),                       # 62 the ferry ticket
    ("Canalave City", ("m", "Piplup")),                  # 63 sail to Sinnoh
    ("Sinnoh", ("t", 178)),                              # 64 the badges (Roark)
    ("Sinnoh League", ("t", 122)),                       # 65 Cynthia
    ("Spear Pillar", ("m", "Unown")),                    # 66 the Plates
    ("Spear Pillar", ("m", "Unown")),                    # 67
    ("Celestic Town", ("m", "Dialga")),                  # 68 (the text names Dialga and Palkia)
    ("Distortion World", None),                          # 69 the ruler of the reverse world: hidden
    ("Mountain Top", None),                              # 70 the Plates' owner: hidden
    ("Hearthome City", None),                            # 71 Cogita
    ("Hearthome City", None),                            # 72 the rift
    ("Hisui", ("m", "Wyrdeer")),                         # 73
    ("Alabaster Icelands", ("m", "Wyrdeer")),            # 74 the clan leaders
    ("Mt. Coronet", None),                               # 75 whoever is behind it: hidden
    ("Hisui", ("t", 142)),                               # 76 Volo (named by the text)
    ("Solaceon Town", ("m", "Munna")),                   # 77
    ("Solaceon Town", ("m", "Munna")),                   # 78
    ("Lost Tower", None),                                # 79 the phantom of nightmares: hidden
    ("Hisui", ("m", "Landorus")),                        # 80 (the text names the three)
    ("Steven's Island", ("i", 744)),                     # 81 Kitty's Dried Fish
    ("Hisui", None),                                     # 82 the summit: hidden
    ("Champion Island", None),                           # 83 Cogita
    ("Everywhere", ("m", "Arceus")),                     # the closing row
]

SIDE = {
    # the Hisuian forms share their names with the regular ones: by species number (checked on a sprite sheet)
    0x0099: ("s", 1017), 0x4327: ("s", 1021), 0x4328: ("s", 1019), 0x009B: ("s", 1062),
    0x009A: ("s", 1015), 0x4329: ("s", 989),
    0x4055: ("m", "Meloetta"), 0x40B9: ("m", "Glastrier"), 0x40CA: ("m", "Meltan"),
    0x40F2: ("m", "Kubfu"), 0x41BD: ("m", "Poipole"), 0x41B7: ("m", "Wimpod"), 0x4307: ("m", "Eevee"),
    0x408F: ("m", "Pikachu"), 0x010B: ("m", "Aerodactyl"), 0x42DE: ("m", "Drifloon"), 0x4118: ("m", "Magikarp"),
    0x012A: ("m", "Beldum"),
    0x045D: ("m", "Snivy"), 0x044D: ("m", "Oshawott"), 0x0415: ("m", "Litten"), 0x40B8: ("m", "Grookey"),
    0x40EA: ("m", "Scorbunny"), 0x4189: ("m", "Chespin"), 0x4321: ("m", "Chikorita"), 0x41C6: ("m", "Cyndaquil"),
    0x4088: ("m", "Totodile"),
    0x42A3: ("t", 94), 0x42B7: ("t", 46), 0x41DF: ("m", "Camerupt"), 0x41DE: ("m", "Sharpedo"),
    0x42B3: ("m", "Electrode"), 0x4165: ("t", 106), 0x42A7: ("m", "Skitty"), 0x4264: ("i", 259),
    0x40CE: ("m", "Piplup"), 0x4269: ("m", "Rotom"), 0x432D: ("m", "Gengar"),
    0x4301: ("s", 157), 0x42FF: ("t", 176), 0x4300: ("m", "Greninja"), 0x4302: ("t", 115),
    0x4303: None,
    # the Badges chapter: each Gym Leader's trainer picture
    0x42CD: ("t", 178), 0x42CE: ("t", 179), 0x42CF: ("t", 180), 0x42D0: ("t", 181),
    0x42D1: ("t", 182), 0x42D2: ("t", 183), 0x42D3: ("t", 184), 0x42D4: ("t", 185),
}

# locations the automatic place-name match gets wrong or too long (row name -> location)
LOC_OVERRIDE = {
    "Latias": "Southern Island", "Latios": "Southern Island", "Deoxys": "Birth Island",
    "Phione": "Day Care", "Silvally": "Evolution", "Cosmoem": "Evolution", "Solgaleo": "Evolution",
    "Lunala": "Evolution", "Melmetal": "Evolution", "Urshifu": "Evolution", "Naganadel": "Evolution",
    "Tornadus": "Valley Windworks", "Thundurus": "Valley Windworks",
    "Journal": "Anywhere", "Sinnoh Map": "Anywhere", "Eon Ticket": "Pokémon Center",
    "Raikou": "Bell Tower Ruins", "Entei": "Bell Tower Ruins", "Suicune": "Bell Tower Ruins",
    "Uxie": "Lake Acuity", "Mesprit": "Lake Verity", "Azelf": "Lake Valor", "Registeel": "Ancient Tomb",
    "Giratina": "Distortion World", "Darkrai": "Lost Tower", "Arceus": "Mountain Top", "Genesect": "New Mauville",
    "Hoopa": "Abandoned Ship", "Type: Null": "Devon Corp.", "Magearna": "Devon Corp.",
    "Regieleki": "Ruins of Decision", "Regidrago": "Ruins of Decision",
    "Storage Key": "Abandoned Ship", "Scanner": "Abandoned Ship", "Prison Bottle": "Abandoned Ship",
    "News Tracker": "Route 111", "Rotom Catalog": "New Mauville",
    "The chateau's TV": "Old Chateau", "The cursed statue": "Old Chateau",
}
