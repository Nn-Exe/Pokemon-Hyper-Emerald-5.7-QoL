"""The Journal's objective list: every story step, the flag(s) that mark it done, and what to tell the player.

Every flag here was traced in the ROM's own scripts (tools/romdata/scripts.py, prereq.py) and checked against
real saves; docs/NOTES.md (JOURNAL) records where each one is set. The game picks the objective like this:

  1. find the LAST step marked ANCHOR that is done;
  2. from the step after it, show the first step that is not done.

Anchors are steps that can only happen in order. Steps that can be done early or skipped are not anchors, so
doing one out of order never makes the Journal jump ahead. Example: Giratina (0x4081) can be battled during
the Hoenn post-game, so it is not an anchor. Arceus (0x42FB) needs every Plate and Giratina first, so it is.

A step is one of
  ANY(flags...)   done when any of the flags is set
  ALL(flags...)   done when all of them are set
  GROUP           a set of parallel tasks (gyms, Plates, Tapu trials). Done when every member is set, or when
                  any of its `done_any` flags is (a later event that proves the set was finished).
                  The message adds a progress line and the missing members: all of them (`list_all`), or
                  only the first one missing, in the order given (Plates, which follow Waji's hint order).
"""

# Wording rule (the user's): say where to go and what to do, never who or what waits there before the story
# reveals it - "face the phantom of nightmares", not Darkrai. Keep names the player already knows at that
# point, and names that are the requirement itself (catch Tornadus...).
W = 34          # the field and bag message boxes both fit 34 characters of the normal font (translation/inserter.py)

HOENN = "Hoenn - Next objective:"
POST = "Post-game - Next objective:"
SINNOH = "Sinnoh - Next objective:"
LOST = "Lost Artifacts - Next objective:"


def ANY(*flags, anchor=True):
    return dict(mode=0, flags=flags, anchor=anchor)


def ALL(*flags, anchor=True):
    return dict(mode=1, flags=flags, anchor=anchor)


def GROUP(label, members, done_any=(), list_all=False, anchor=True):
    """members: (flag, weight, text). weight counts a flag twice when it stands for two things (one flag
    covers both the Iron and Dread Plates)."""
    return dict(mode=2, flags=done_any, anchor=anchor, label=label, members=members, list_all=list_all)


STEPS = [
    # ---------------------------------------------------------------- Part 1: Hoenn
    (HOENN, ANY(0x860), "Go north of Littleroot Town to Route 101 and help Prof. Birch. You will get your "
                        "first Pokémon."),
    (HOENN, ANY(0x861), "Find Birch's kid on Route 103, north of Oldale Town, then return to the lab in "
                        "Littleroot for your Pokédex."),
    (HOENN, ANY(0x867), "Go through Petalburg Woods to Rustboro City and beat Roxanne, the Gym Leader."),
    (HOENN, ANY(0x08F), "A Team Aqua grunt stole the Devon Goods! Chase him east of Rustboro into Rusturf "
                        "Tunnel and get them back."),
    (HOENN, ANY(0x0BC), "Take the Devon Goods back to Devon Corp. in Rustboro. The President has a letter "
                        "and a delivery for you."),
    (HOENN, ANY(0x0BD), "Ask Mr. Briney, in his cottage on Route 104, to sail you to Dewford Town. Deliver "
                        "the letter to Steven deep in Granite Cave."),
    (HOENN, ANY(0x868), "Beat Brawly, the Gym Leader of Dewford Town."),
    (HOENN, ANY(0x095), "Sail on to Slateport City and deliver the Devon Goods to Capt. Stern at the "
                        "Oceanic Museum."),
    (HOENN, ANY(0x869), "Go north along Route 110 to Mauville City and beat Wattson, the Gym Leader."),
    (HOENN, ANY(0x08B), "Chase Team Magma: from Route 111 go through the Fiery Path to Fallarbor Town and "
                        "Meteor Falls, then ride the Route 112 cable car up Mt. Chimney."),
    (HOENN, ANY(0x86A), "Walk down Jagged Pass to Lavaridge Town and beat Flannery, the Gym Leader."),
    (HOENN, ANY(0x86B), "Go home to Petalburg City and beat your father Norman, the Gym Leader."),
    (HOENN, ANY(0x097), "Surf east from Route 118 and go north up Route 119: Team Aqua has taken over the "
                        "Weather Institute."),
    (HOENN, ANY(0x86C), "Beat Winona, the Gym Leader of Fortree City. If something invisible blocks the "
                        "way, Steven's Devon Scope on Route 120 reveals it."),
    (HOENN, ANY(0x0D4), "Head east toward Lilycove City. Teams Magma and Aqua are after the orbs on Mt. "
                        "Pyre (Route 122): climb to the summit."),
    (HOENN, ANY(0x06F), "Take the Magma Emblem from Mt. Pyre to Jagged Pass. It opens Team Magma's hideout: "
                        "stop Maxie inside."),
    (HOENN, ANY(0x070), "Raid Team Aqua's Hideout on the coast east of Lilycove City before Archie gets "
                        "away."),
    (HOENN, ANY(0x42B6, anchor=False),
                        "Team Plasma is blocking Mossdeep's Gym. Find them in the icy room of Shoal Cave, "
                        "north of Mossdeep City, and drive them off."),
    (HOENN, ANY(0x86D), "Beat Tate & Liza, the Gym Leaders of Mossdeep City."),
    (HOENN, ANY(0x0CD), "Team Magma is attacking the Mossdeep Space Center! Stop them, then talk to Steven."),
    (HOENN, ANY(0x081), "Dive on Route 128 to reach the Seafloor Cavern and stop Team Aqua."),
    (HOENN, ANY(0x138), "Groudon and Kyogre are clashing over Sootopolis City. Help Wallace: wake Rayquaza "
                        "at the Sky Pillar (Route 131). He gives you HM Waterfall after."),
    (HOENN, ANY(0x86E), "Beat Juan, the Gym Leader of Sootopolis City."),
    (HOENN, ANY(0x864), "Surf to Ever Grande City, cross Victory Road and beat the Elite Four and the "
                        "Champion."),

    # ---------------------------------------------------------------- Part 2: the post-game story
    # 0x40C3 is also set long before the Hall of Fame (it hides the Interpol agent) and the Hall of Fame
    # clears it, so on its own it would read as done before the game even starts: pair it with 0x864.
    (POST, ALL(0x864, 0x40C3), "Go home to Littleroot Town: Interpol agents Nanu and Anabel are waiting for "
                               "the new Champion."),
    (POST, ANY(0x4153), "In Ever Grande City the guard now lets you through. Follow the passage to Steven's "
                        "Island, where Interpol waits."),
    (POST, ANY(0x414B), "Wally called from Petalburg City. Hurry: someone is trying to steal his Mega "
                        "Bracelet!"),
    (POST, ANY(0x4156), "Steven called with an emergency. Go to Devon Corp. in Rustboro City."),
    (POST, ANY(0x415C), "Find a meteorite fragment in Granite Cave, near Dewford Town. Zinnia is there too."),
    (POST, ANY(0x4158), "Bring the meteorite to Prof. Cozmo at the Mossdeep Space Center."),
    (POST, ANY(0x4159), "Team Magma took your Mega Bracelet. Go to Meteor Falls and stop them."),
    (POST, ANY(0x40C6), "Beat Zinnia in Meteor Falls to get your Mega Bracelet back."),
    (POST, ANY(0x1C0), "Climb the Sky Pillar (Route 131) and face Rayquaza."),
    (POST, ANY(0x1AD), "Ride Rayquaza into space to stop the meteor. Something is waiting beyond the sky."),
    (POST, ANY(0x411D), "Back on the ground, talk to Wallace in Mossdeep City."),
    (POST, ANY(0x411E), "Return to Steven's Island. Anabel reports trouble deep inside Meteor Falls: find "
                        "Steven there."),
    (POST, ANY(0x407C), "Anabel found a new Ultra Wormhole near Pacifidlog Town. Go through it."),
    (POST, ANY(0x419D), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x41A2), "Gladion needs you at the Secret Base on Route 111: defeat the Totem Pokémon."),
    (POST, GROUP("Tapus that know you:", [
        (0x406D, 1, "Tapu Bulu: talk to Nanu on Steven's Island."),
        (0x406B, 1, "Tapu Koko: find Hala in Dewford Town."),
        (0x406C, 1, "Tapu Fini: find Hapu in Slateport City."),
        (0x406A, 1, "Tapu Lele: find Olivia in Mossdeep City."),
    ], done_any=(0x41BC,), list_all=True, anchor=False),
        "Nanu found strange islands. Pass the four Tapus' trials with the Island Kahunas."),
    (POST, ANY(0x41BC), "All four Tapus recognise you. Report to Nanu on Steven's Island."),
    (POST, ANY(0x40A0), "The Devon Scout on Steven's Island tracked Faba to the Ultra Wormhole in the "
                        "Scorched Slab (Route 120). Bring a way past whirlpools."),
    (POST, ANY(0x41CD), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x41AF), "Anabel says Steven and the former Champions are waiting in the lobby. Train with "
                        "them."),
    (POST, ANY(0x41CE), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x4161, 0x40DC), "The Devon Scout says the Ultra Wormhole fluctuations follow abnormal "
                                "weather. Find the drought (Terra Cave) or the downpour (Marine Cave)."),
    (POST, ANY(0x41CF), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x42BC), "The Devon Scout detected an Ultra Wormhole at the top of Mt. Pyre. Go through it."),
    (POST, ANY(0x41D0), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x4131), "Next fluctuation: the icy room of Shoal Cave, where Team Plasma was. Go through "
                        "the Ultra Wormhole there."),
    (POST, ANY(0x41D1), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x42C4), "Next fluctuation: the Ultra Wormhole on Route 116."),
    (POST, ANY(0x41D2), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x42C7), "Faba was seen alone near the Mirage Tower in the Route 111 desert. Go and catch "
                        "him."),
    (POST, ANY(0x41D3), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x40B0), "Find Red. The last Ultra Wormholes are deep in Meteor Falls and Granite Cave."),
    (POST, ANY(0x41D4), "Report to Anabel on Steven's Island."),
    (POST, ANY(0x419F), "Collect all 18 Z-Crystals, then go to Pacifidlog Town. The crystals open the way "
                        "to Team Rainbow Rocket's castle."),
    (POST, ANY(0x41D5), "Storm Team Rainbow Rocket's castle and defeat them at the Mountain Top."),
    (POST, ANY(0x42F1), "Return to Steven's Island: Steven is waiting."),
    # The way to Champion Island is the Lilycove ferry, which lists it only with flag 0x08D5 AND item 371 (the
    # ticket; vanilla's Aurora Ticket slot). Scott gives both in his Frontier house (0x082636A8) on your first
    # Silver Symbol from any facility, with the PWT invitation, and sets 0x005C - which nothing else sets.
    # Yanshan on Steven's Island also sets 0x08D5 but gives no ticket (tested in game), so 0x08D5 would read
    # as done too early: the step uses 0x005C. Can be earned early: not an anchor.
    (POST, ANY(0x005C, anchor=False),
                        "Earn a Silver Symbol at the Battle Frontier - for one, beat Salon Maiden Anabel, "
                        "the 35th battle of a Battle Tower Singles streak. Then see Scott in his Frontier "
                        "house for a ferry ticket to the World Championships."),
    # 0x08E0 is set when you arrive (Paul's trigger, 0x098712EA); beating Lyra sets it too, so not an anchor
    (POST, ANY(0x08E0, anchor=False),
                        "Take the ferry from Lilycove City to Champion Island for the World Championships. "
                        "Familiar faces are waiting."),

    # ---------------------------------------------------------------- Chapter: Sinnoh
    (SINNOH, ANY(0x42CD, 0x42CE, 0x42CF, 0x42D0, 0x42D1, 0x42D2, 0x42D3, 0x42D4, 0x42D5, anchor=False),
                        "Show Waji's boat ticket to the sailor at Lilycove City's harbor and sail to "
                        "Canalave City in Sinnoh."),
    (SINNOH, GROUP("Sinnoh Badges:", [
        (0x42CD, 1, "Roark - Oreburgh City"),
        (0x42CE, 1, "Gardenia - Eterna City"),
        (0x42CF, 1, "Maylene - Veilstone City"),
        (0x42D0, 1, "Crasher Wake - Pastoria City"),
        (0x42D1, 1, "Fantina - Hearthome City"),
        (0x42D2, 1, "Byron - Canalave City"),
        (0x42D3, 1, "Candice - Snowpoint City"),
        (0x42D4, 1, "Volkner - Sunyshore City"),
    ], done_any=(0x42D5,), list_all=True),
        "Earn the eight Sinnoh Gym Badges. Still to beat:"),
    (SINNOH, ANY(0x42D5), "Take Victory Road to the Sinnoh League and beat the Elite Four and Cynthia."),

    # ---------------------------------------------------------------- Part 3: Lost Artifacts
    # Members in Waji's hint order. The altar (0x40F0), Arceus (0x42FB) and Cogita (0x4313) all check every
    # Plate, so any of them proves the set.
    (LOST, GROUP("Plates found:", [
        (0x4104, 1, "Fist Plate: the Sealed Chamber, the ruin under the sea of Route 134 (Dive)."),
        (0x4102, 1, "Sky Plate: the house full of Wingull on Route 119."),
        (0x4107, 1, "Toxic Plate: a little hill in the marsh on Route 212, toward Pastoria City."),
        (0x410B, 1, "Earth Plate: Granite Cave near Dewford, in the room at the back of the first floor."),
        (0x4105, 1, "Stone Plate: Oreburgh Mine, next to Oreburgh City."),
        (0x410E, 1, "Insect Plate: the Solaceon Ruins, in one of the large chambers."),
        (0x4106, 1, "Spooky Plate: the Lost Tower on Route 209, near the Solaceon Ruins."),
        (0x4109, 2, "Iron and Dread Plates: the Team Rocket hideout under the Mauville Game Corner."),
        (0x40FF, 1, "Flame Plate: the summit of Mt. Chimney."),
        (0x40FE, 1, "Splash Plate: underwater on Route 126, around Sootopolis (Dive)."),
        (0x4100, 1, "Meadow Plate: in the shade of the trees on rainy Route 120."),
        (0x4101, 1, "Zap Plate: a hidden corner of New Mauville."),
        (0x410C, 1, "Mind Plate: the Solaceon Ruins, away from the Insect Plate."),
        (0x42AC, 1, "Icicle Plate: the mountain man's hut on snowy Route 217. He gives it to you."),
        (0x4103, 1, "Draco Plate: the Meteor Temple, reached from Meteor Falls."),
        (0x4108, 1, "Pixie Plate: deep inside Mt. Coronet."),
    ], done_any=(0x40F0, 0x42FB, 0x4313)),
        "Collect the 17 Plates hidden in Hoenn and Sinnoh. Waji, at the Spear Pillar on top of Mt. Coronet, "
        "gives hints."),
    # Only Giratina and the Plates are needed for Arceus. The rift and Celestic steps are how Waji leads you
    # to Giratina, so they count as done once Giratina is.
    (LOST, ANY(0x40F0, 0x42D8, 0x4081, anchor=False),
                        "Step onto the altar at the Spear Pillar with all 17 Plates. The rift that opens will "
                        "test everything you have."),
    (LOST, ANY(0x42D8, 0x4081, anchor=False),
                        "Waji senses the rift's energy in Celestic Town. Visit its ruins with Dialga and "
                        "Palkia both caught to open a way into the Distortion World, or go in from the islet "
                        "on Route 129."),
    (LOST, ANY(0x4081, anchor=False),
                        "Enter the Distortion World and face the ruler of the reverse world. Ways in: the new "
                        "passage at the Spear Pillar or Sendoff Spring, or the islet on Route 129 in Hoenn."),
    (LOST, ANY(0x42FB), "Keep all 17 Plates in your Bag and return to the Mountain Top above Team Rainbow "
                        "Rocket's castle. The Plates' true owner is waiting."),
    (LOST, ANY(0x4313), "Arceus sent you to Hearthome City. Find Cogita in a house on the west side of town, "
                        "with all 17 Plates in your Bag."),
    (LOST, ANY(0x4316), "Step through the space-time rift in Cogita's house. It leads to the Hisui region."),
    (LOST, ANY(0x4318), "Find Cogita in Hisui. Rei (Mingyao) at the Deertrack Heights base camp flies you "
                        "around: look on Firespit Island."),
    (LOST, GROUP("Clan leaders met:", [
        (0x431A, 1, "Adaman, Diamond Clan"),
        (0x431B, 1, "Irida, Pearl Clan"),
    ], done_any=(0x4315,), list_all=True),
        "Visit the clan leaders at the hot spring in the Alabaster Icelands."),
    (LOST, ANY(0x4315), "Diamond and Pearl point to the foot of Mt. Coronet. Enter the Primeval Cave: whoever is "
                        "behind the rifts is inside."),

    # ---------------------------------------------------------------- After Volo: the God of Forms
    # Traced 2026-09-22 with tools/romdata (scripts.py, prereq.py). 0x431E: Rei and Cogita's report, a trigger
    # at base camp (37/104). 0x4319: Cogita on Firespit Island (37/105, 0x0989D84D), after Volo, once the
    # Pokedex has Tornadus, Thundurus and Landorus (species 899-901) - she tells you of Enamorus. 0x4322: the
    # hide flag of the Dried Fish item ball on Prelude Beach (37/104, 13,40), the game's only Dried Fish (item
    # 744); Kitty in the developer house (35/8, 0x098B1F85) eats it and gives the nameless stone (item 745).
    # The summit guard (37/106, 0x098B201D) needs item 745 AND 0x4319 AND not 0x4323, and warps to the Moonbow
    # Dome (35/10): the God of Forms (trainers 1304, 1340, 1341; the stone crumbles its clay figures) and a
    # Lv 70 Enamorus (species 1025) -> 0x4323. 0x4325: Cogita on Champion Island (35/28, needs 0x4319; or the
    # 35/6 trigger after 0x431E), which opens her Ancient Retreat (37/119) and the Griseous Core (37/121).
    # Only 0x431E and 0x4319 must happen in order; the rest can come in any order after 0x4319.
    (LOST, ANY(0x431E), "Volo is beaten. Return to base camp in Hisui: Rei and Cogita have news."),
    # The Solaceon nightmare (placed here at the user's request; it has no link to Volo, so every step is
    # "any order" and doing it early never moves the Journal). 0x4117: the husband in Solaceon (37/22,
    # 0x0980DF8C) tells his story - set on first talk. 0x412F: Dawn on Route 210 (35/16, 0x0980977C) hands over
    # the Lunar Wing (item 647). 0x412D: the Lunar Wing wakes the woman (0x0980E243); the husband then gives
    # Berries. 0x4060: Darkrai's hide flag in the Lost Tower (35/29): shown once 0x412D is set, set by the
    # shared legendary handler's removeobject (0x08FE38F0) after the battle, cleared again if it flees.
    (LOST, ANY(0x4117, anchor=False),
                        "In Solaceon Town in Sinnoh, a woman has slept in a nightmare since her offerings "
                        "at the Lost Tower. Hear her husband out."),
    (LOST, ANY(0x412F, anchor=False),
                        "Dawn, on Route 210, carries a feather said to dispel any nightmare. Tell her about the "
                        "sleeping woman."),
    (LOST, ANY(0x412D, anchor=False),
                        "Bring the Lunar Wing to the sleeping woman in Solaceon Town and wake her."),
    (LOST, ANY(0x4060, anchor=False),
                        "The oppressive presence in the Lost Tower has lifted. Something pitch-black stirs deep "
                        "inside: face the phantom of nightmares."),
    (LOST, ANY(0x4319), "Catch Tornadus, Thundurus and Landorus, then show Cogita on Firespit Island in Hisui. "
                        "She has one more legend to tell."),
    (LOST, ANY(0x4322, anchor=False),
                        "Kitty in the three-floor house on Steven's Island wants dried fish. Find the "
                        "Dried Fish on Prelude Beach in Hisui and bring it to her for a nameless stone."),
    (LOST, ANY(0x4323, anchor=False),
                        "With Kitty's nameless stone in your Bag, climb toward the Sacred Temple in Hisui's "
                        "highlands. A dread of unknown origin hangs over the summit."),
    (LOST, ANY(0x4325, anchor=False),
                        "Cogita waits on Champion Island with more to tell."),
]

FINAL = (LOST, "Every story objective is complete! Still out there: a trial of six battles at Cogita's retreat "
               "off Sootopolis, and Adaman and Irida's clan treasures for a trainer who brings Dialga or Palkia.")

# Short titles for the Quest Log, one per step in order (<= 24 characters, the same no-spoiler rule).
TITLES = [
    'Help Prof. Birch',
    'Get the Pokédex',
    'Beat Roxanne',
    'Chase the Aqua grunt',
    'Back to Devon Corp.',
    'A letter for Steven',
    'Beat Brawly',
    'Deliver the Devon Goods',
    'Beat Wattson',
    'Chase Team Magma',
    'Beat Flannery',
    'Beat Norman',
    'The Weather Institute',
    'Beat Winona',
    'Climb Mt. Pyre',
    "Team Magma's hideout",
    "Team Aqua's hideout",
    "Team Plasma's blockade",
    'Beat Tate & Liza',
    'The Space Center',
    'The Seafloor Cavern',
    'Crisis in Sootopolis',
    'Beat Juan',
    'The Pokémon League',
    'Interpol at home',
    "Steven's Island",
    "Wally's Mega Bracelet",
    'Emergency at Devon',
    'A meteorite fragment',
    'Prof. Cozmo',
    'The stolen bracelet',
    'Face Zinnia',
    'Climb the Sky Pillar',
    'Beyond the sky',
    'Wallace in Mossdeep',
    'Trouble in Meteor Falls',
    'The first wormhole',
    'Report to Anabel',
    'The Totem Pokémon',
    'The four trials',
    'Report to Nanu',
    'Chase Faba',
    'Report to Anabel',
    'Train with Champions',
    'Report to Anabel',
    'The strange weather',
    'Report to Anabel',
    "Mt. Pyre's wormhole",
    'Report to Anabel',
    "Shoal Cave's wormhole",
    'Report to Anabel',
    "Route 116's wormhole",
    'Report to Anabel',
    'Catch Faba',
    'Report to Anabel',
    'Find Red',
    'Report to Anabel',
    'The 18 Z-Crystals',
    'Storm the castle',
    'Steven is waiting',
    'A Silver Symbol',
    'To Champion Island',
    'Sail to Sinnoh',
    'The Sinnoh Badges',
    'The Sinnoh League',
    'The 17 Plates',
    'The Spear Pillar altar',
    'A way through',
    'The reverse world',
    "The Plates' owner",
    'Cogita in Hearthome',
    'Through the rift',
    'Find Cogita in Hisui',
    'The clan leaders',
    'The Primeval Cave',
    'Back to base camp',
    'A sleeping woman',
    'A feather for dreams',
    'Wake the sleeper',
    'The Lost Tower',
    'One more legend',
    "Kitty's dried fish",
    'The summit',
    "Cogita's invitation",
]
FINAL_TITLE = 'Beyond the story'

