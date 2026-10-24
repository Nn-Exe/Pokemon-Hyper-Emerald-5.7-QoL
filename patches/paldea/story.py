"""Area Zero: what people say, who battles with what, and the flags and var the area keeps its state in.

Lines are wrapped to the message box by lib.box(); a speaker's name starts the line, as the hack's own lines do
("Nanu: ..."). {PLAYER} is the player's name.

The story is the one the user approved (revision 2, 2026-10-08): Jacq's students Arven, Nemona and Penny were
pulled into Area Zero. Penny hides in Research Station No. 1 and decodes the stations' logs; Arven, the
professors' child, nurses a worn-out Koraidon (past) and Miraidon (future) by his picnic and needs Sour Herba
Mystica that the Quaking Earth Titans guard (Great Tusk, Iron Treads: battled twice); Nemona battles every Iron
Paradox in the future. The four logs open the Zero Lab; Arven and Nemona hold its door; inside, the professors'
AIs battle you (Sada's and Turo's own teams), then the Paradise Protection Protocol sends the lab's own Koraidon
and Miraidon. The machine stops, the AIs go through it, everyone goes home through the hole. After that the two
partners wait at the picnic to be caught, and the rest of the Gen 9 legends can be found. (Since test 11, at the
user's word: once Jacq has thanked you the four of them go back in and live in the research stations, so that
nobody is left standing in the way by the hole.)

State (checked unused on the Gen 9 test build and on both saves, 2026-10-08: no script sets, clears or checks
them, no object hides by them, no aligned literal holds them, all clear; 0x43BF is not free and is skipped):
  flags 0x43AB-0x43BE and 0x43C0-0x43D6; var 0x40A8 (two byte matches in the ROM, both in code or graphics).
"Hide" flags hide an object while set. The ones marked (worked out) are not kept by the story at all: a
subroutine every one of these maps runs on the way in and on resume ("state", paldea_patch.py) sets or clears
them from the story's own flags and the stage, so a save from any older build shows the right people.
"""

F_RR_DONE = 0x41D5          # the game's own: Team Rainbow Rocket beaten (set on the two Mountain Top win paths)

F_WOODS_HIDE = 0x43AB       # (worked out) the hole in Mossdeep (the Timeless Woods up to test 15): hidden until
                            # 0x41D5
F_MET_JACQ = 0x43AC         # Jacq has told you what happened
F_RIPPLE_SEEN = 0x43AD      # the first time crystal has been explained
F_CAVERN_ITEM = 0x43AE      # the Crystal Cavern's item ball taken
F_ICE_ITEM = 0x43AF         # the icy cave's item ball taken
F_INIT = 0x43B0             # tests 7-10 set it once; nothing reads it any more (kept out of use)
F_MET_PENNY = 0x43B1
F_MET_ARVEN = 0x43B2
F_TUSK_DONE = 0x43B3        # Great Tusk beaten twice, its Herba Mystica found (hides the Titan)
F_TREADS_DONE = 0x43B4      # Iron Treads likewise
F_KORAIDON_UP = 0x43B5      # Arven's sandwich: Koraidon on its feet again
F_MIRAIDON_UP = 0x43B6
F_BEAT_NEMONA = 0x43B7
F_LOGS = (0x43B8, 0x43B9, 0x43BA, 0x43BB)   # each station's log played
F_LAB_OPEN = 0x43BC         # Penny has unlocked the Zero Lab's door (Arven and Nemona open it: F_GUARDS_UP)
F_GUARDS_UP = 0x43BD        # Arven and Nemona went to the lab's door (hides them at the picnic and in the field);
                            # the door is open from then on
F_HIDE_GUARDS = 0x43BE      # (worked out) hides them at the lab's door until then, and again after the story
F_HIDE_LAB_CAST = 0x43C0    # the AIs and the lab's own Koraidon and Miraidon: set on the way into the lab, cleared
                            # by the finale while it plays
F_STORY_DONE = 0x43C1       # the finale is won (hides the crystal on the cavern's ladder; shows the legends)
F_HIDE_HOME = 0x43C2        # (worked out) the students by the hole: there for the ending only (stage 3)
F_KORAIDON_CAUGHT = 0x43C3  # the partners at the picnic, after the story
F_MIRAIDON_CAUGHT = 0x43C4
F_JACQ_HIDE = 0x43D4        # (worked out) Jacq by the hole: from 0x41D5 until the ending is over
F_HIDE_RESIDENTS = 0x43D5   # (worked out) Arven, Nemona and Jacq in Research Stations 2-4: after the ending
F_IN_FUTURE = 0x43D6        # (worked out) which crater you are in or were last in: set by the future's map
                            # scripts, cleared by the past's. The Crystal Cavern's way out reads it.
# Test 15 (checked like the others, on the Gen 9 test build and the three saves: nothing in the script index sets,
# clears or checks them, no object hides by them, no script bytes and no aligned literal hold them, all clear;
# 0x43D7 and 0x43DB have chance matches and are skipped):
F_SEALS = {"wo_chien": 0x43D8, "ting_lu": 0x43D9, "chi_yu": 0x43DA}   # the Sealed Vault: a stake pulled. Hides
                            # the stake and the crystal across its treasure's niche (both objects' own flag)
F_BOOSTER = {"past": 0x43DC, "future": 0x43DD}                        # the crater's two item balls taken
# 2026-10-11 (checked the same way on the Gen 9 base and four saves, _testrun/full/flagcheck.py; 0x43DE-0x43E1
# have chance matches and are skipped):
F_NEMONA_REMATCH = 0x43E4  # Nemona's rematch after the ending won (the Quest Log's Side Content row; 2026-10-15). Free:
                            # no setflag / clearflag / checkflag bytes for it anywhere in the ROM, no map object's
                            # flag, no aligned word, not a trainer flag (0x43E3 has two chance setflag byte runs)
F_MET_EARLY = 0x43E2       # Jacq was spoken to in Mossdeep before the hole opened: he knows you when it has

STAGE = 0x40A8              # 0 nothing yet, 1 met Jacq, 2 arrived in Area Zero, 3 on the way home, 4 the ending
S_MET, S_ARRIVED, S_HOME, S_DONE = 1, 2, 3, 4      # is over (they live in the stations)
FRESH = 0x40F9              # the stamp of the build whose copy of the map the save holds; 0: read the map again
                            # (paldea_patch.py, transition()). Unused by the game like 0x40A8: no script in the
                            # index, no aligned literal, 0 in every save (vanilla's VAR_UNUSED_0x40F9)

PLACE_NAME = "Area Zero"
DEX_NAME = {"Koraidon": "Koraidon", "Miraidon": "Miraidon"}

# ---------------------------------------------------------------------------------------------- the way in
# Before the hole (the user, 2026-10-11: "before the blackhole paldea appears, we should at least have Jacq
# standing there talking about taking students on trip or something ... like a foreshadowing"). Jacq stands on
# his tile in Mossdeep from the start of the game; the hole comes with 0x41D5 as before.
JACQ_EARLY = [
    "Jacq: Oh, hello! A Trainer? My name's Jacq. I teach biology at the academy in Paldea. That's a long, long "
    "way from here.",
    "Jacq: I've brought three of my students to Hoenn on a field study. Arven, Nemona and Penny. Good kids. "
    "Curious kids. They're off around the island somewhere.",
    "Jacq: We came for the sky. The Space Center says the air over this shore has been restless lately. As if "
    "something were pressing on it from the other side.",
    "Jacq: It's probably nothing! Still, I told the kids not to wander too far. ...Not that they ever listen.",
]
JACQ_EARLY_AGAIN = [
    "Jacq: Still nothing in the sky. Good! A quiet field trip is a good field trip. ...I keep telling myself that.",
]
# The hole is open and you met him before it was: these two pages stand for JACQ_INTRO's first three, and its
# last four follow as they are.
JACQ_INTRO_KNOWN = [
    "Jacq: You! The Trainer from before! Thank goodness... It's me, Jacq. The teacher with the three students.",
    "Jacq: The restless sky, remember? The Space Center says this opened the night the wormholes all over Hoenn "
    "closed. Look at it. It isn't an Ultra Wormhole.",
]
JACQ_INTRO = [
    "Jacq: Oh! A Trainer! Thank goodness... Sorry, sorry. My name's Jacq. I teach biology at the academy in "
    "Paldea.",
    "Jacq: I brought three of my students to Hoenn on a field study. Arven, Nemona and Penny. Good kids. "
    "Curious kids.",
    "Jacq: The Space Center says this opened the night the wormholes all over Hoenn closed. Look at it. It "
    "isn't an Ultra Wormhole.",
    "Jacq: The kids went to take a closer look, and it pulled them in. All three of them.",
    "Jacq: I went in after them... and ran straight back out, chased by a Pokémon I had only ever seen drawn "
    "in a book two hundred years old.",
    "Jacq: I know that place. It's the Great Crater of Paldea. Area Zero. Nobody is allowed down there, and "
    "my students are down there right now.",
    "Jacq: Your Pokémon look like they could handle anything. Please... would you go in and bring them back? "
    "I'll wait right here.",
]
JACQ_AGAIN = ["Jacq: Arven, Nemona and Penny are somewhere on the other side. Please, bring them home!"]

HOLE_FIRST = [
    "A perfectly black hole hangs in the air above the grass. Something on the other side is pulling at you...",
    "Jacq: Whoa, whoa! Don't go near that!",
]
HOLE_ASK = "The black hole is pulling at you. Step into it?"

WALL_INTRO = [
    "The hole lets go of you on a narrow ledge, high on a cliff. Far below, a forest fills the bottom of a "
    "vast crater.",
    "This must be Area Zero...",
]
WALL_BACK_ASK = "Through the hole, you can faintly hear the sea at Mossdeep. Go back?"

# ---------------------------------------------------------------------------------------------- the stations
# All four are the same prefab room, as in Paldea: a recorder on the left counter (the log), a note on the table,
# a cot behind the right counter, the game's own PC on the back wall.
REST_ASK = "There's a folding cot in the back room, behind the counter. Rest for a while?"
REST_DONE = "You and your Pokémon are fully rested!"
LOG_INTRO = "A recorder on the counter blinks. A recording begins to play..."
LOG_END = "The recording ends. Somewhere, a fan whirs as the station sends it on."
LOGS = [
    ["Professor Sada: Station One, day three. The crater floor is a world of its own. Tonight something with "
     "huge tusks walked past the station. It was not a Donphan.",
     "Professor Turo: Nothing alive today matches these readings. If the rifts down here open onto time the way "
     "I think they do... we can build a machine that reaches it."],
    ["Professor Turo: Station Two. The machine works. We brought back a Pokémon from the far future, a machine "
     "shaped like Donphan.",
     "Professor Sada: And I brought one from the distant past. They are perfect. But they don't belong here... "
     "and the gate does not close behind them."],
    ["Professor Sada: Station Three. Our partners fought today. My Koraidon and Turo's Miraidon. Neither would "
     "back down.",
     "Professor Turo: The lab's two guardians won't let anything near the machine. Ours were beaten badly. "
     "Our son is looking after them now."],
    ["Professor Turo: Station Four. Last log. We are going to make copies of ourselves, an AI each, to run the "
     "lab while we are... away.",
     "Professor Sada: If anyone finds this: the lab only opens to someone who has heard all four of these. "
     "Please. Stop the machine. We could not."],
]
NOTES = [
    ["A tablet covered in Eevee stickers lies on the table. It's still warm...",
     "Someone was here not long ago."],
    ["A huge backpack leans against the table, stuffed with bread, vegetables and a jar marked \"Sour Herba "
     "Mystica\". It's empty.", "Somebody came here to make sandwiches."],
    ["A crayon drawing is pinned to the table: a woman, a man, a boy and two big lizards. It's signed \"Arven, "
     "age 6\"."],
    ["A battered field guide lies open on the table. Every page about the crater's Titans is full of notes."],
]
STATION_NAMES = ["Research Station No. 1", "Research Station No. 2", "Research Station No. 3",
                 "Research Station No. 4"]

PENNY_FIRST = [
    "Penny: Eek! ...Oh. You're not a Paradox Pokémon. Sorry.",
    "Penny: I'm Penny. Jacq's student. The black hole dropped the three of us on that ledge, and I've been "
    "hiding in here ever since.",
    "Penny: Arven ran down into the crater with his backpack full of sandwich stuff, and Nemona went off to "
    "battle anything that moves. Typical.",
    "Penny: I got into this station's computer, though. The professors who built this place left a log in "
    "every research station. Four stations, four logs.",
    "Penny: And the Zero Lab, the big door in the crater wall, only opens for someone who has heard all four. "
    "I bet that's our way home.",
    "Penny: Could you play the logs in the other three stations? I'm linked to them all from here.",
    "Penny: Station Two is the house on the shelf below the stairs. Station Three is up on the knoll in the "
    "east. And Station Four... the map says it's above the waterfall?",
]
PENNY_COUNT = "Penny: Logs so far... {COUNT} of 4."
PENNY_HINTS = [
    "Penny: This station's log is on the recorder right here. Go on, play it.",
    "Penny: Still missing Station Two's. The house on the shelf, right below the stairs you came down.",
    "Penny: Still missing Station Three's. It's the house on top of the knoll, in the east of the crater.",
    "Penny: Still missing Station Four's. It's above the waterfall. You'll have to climb it.",
]
PENNY_OPEN = [
    "Penny: That's all four! Give me a second...",
    "Penny: ...Done. The Zero Lab's door is unlocked. It's the big shutter in the crater's north-east wall.",
]
# Arven and Nemona go to the lab's door by themselves once Koraidon and Miraidon are well, Nemona is beaten and
# the door is unlocked, in whatever order that happens (test 9 made you talk to Arven last; the user did it in
# another order and was stuck). The door stays shut until they are there (the user, on test 10: "the door should
# be prohibited to enter until those two are at the door to not make confusion"): Penny unlocks it, they lift it.
# Until then Penny and the door itself say what is still missing.
PENNY_READY = ["Penny: The cameras show Arven and Nemona heading for it already. They'll have it open by the "
               "time you get there. I've got your back from here."]
PENNY_NOT_YET = ["Penny: It takes more than one person to lift it, though, and nobody should go in there alone. "
                 "Arven and Nemona will come and open it as soon as they can."]
PENNY_AFTER = ["Penny: The lab's door is unlocked, but it takes Arven and Nemona to get it open. They'll come "
               "as soon as they can."]
PENNY_TODO = {
    "koraidon": "Penny: Arven won't leave Koraidon while it's this weak. It needs the herb the Titan guards, in "
                "the den on the west side of the crater, in the past.",
    "miraidon": "Penny: Arven won't leave Miraidon while it's this weak. It needs the herb the Titan guards, in "
                "the den on the west side of the crater, in the future.",
    "nemona": "Penny: Nemona won't stop battling until somebody beats her. She's in the future, in the tall grass "
              "south of the waterfall's pond.",
}
# After the ending she is back in Station One, with the cameras: where the rest of the legends are, by place
# (not by tile: the places can be moved, placements.txt).
PENNY_HOME = [
    "Penny: Back in Station One. It's almost cozy, now that nothing out there wants to eat me.",
    "Penny: I've got every camera in the crater on my tablet. Besides Arven's two there are three more ancient "
    "ones in the past and three more iron ones in the future.",
    "Penny: Two big readings prowl the Crystal Cavern, and its second opening has come clear: there's a vault "
    "behind it with three more, sealed in crystal. The floor in there is like a mirror. Mind your step.",
    "Penny: Something very cold hides in the icy cave up here on the wall, and whatever is under the cavern's "
    "ladder... the sensors can't even name it.",
]

# ---------------------------------------------------------------------------------------------- Arven, the Titans
ARVEN_FIRST = {
    "past": [
        "Arven: Hey! Don't touch Koraidon! ...Sorry. You're the one Jacq sent, right? I'm Arven.",
        "Arven: My mom built this place. In another world, my dad did. Down here, both of those are true at "
        "once.",
        "Arven: This Koraidon was hers. It fought the lab's guardian to protect me, and it has hardly moved "
        "since.",
        "Arven: Only Herba Mystica can heal it. There's a Sour Herba Mystica in the den on the west side of the "
        "crater... but a Titan guards it.",
        "Arven: A huge Great Tusk. If you can beat it, bring the herb back, and I'll make Koraidon the best "
        "sandwich of its life.",
    ],
    "future": [
        "Arven: Hey! Don't touch Miraidon! ...Sorry. You're the one Jacq sent, right? I'm Arven.",
        "Arven: My dad built this place. In another world, my mom did. Down here, both of those are true at "
        "once.",
        "Arven: This Miraidon was his. It fought the lab's guardian to protect me, and it has hardly moved "
        "since.",
        "Arven: Only Herba Mystica can heal it. There's a Sour Herba Mystica in the den on the west side of the "
        "crater... but a Titan guards it.",
        "Arven: A strange iron Donphan. Iron Treads. If you can beat it, bring the herb back, and I'll make "
        "Miraidon the best sandwich of its life.",
    ],
}
ARVEN_WAIT = {
    "past": ["Arven: The Titan's in the den on the west side. Great Tusk. Be careful."],
    "future": ["Arven: The Titan's in the den on the west side. Iron Treads. Be careful."],
}
ARVEN_SANDWICH = {
    "past": [
        "Arven: You got the Sour Herba Mystica! Okay. Okay! Give me a minute.",
        "Arven made a sandwich stacked high with Sour Herba Mystica!",
        "Koraidon is eating the sandwich...",
        "Koraidon got its strength back!",
        "Arven: Look at that... Thank you. Really. Mom would have liked you.",
    ],
    "future": [
        "Arven: You got the Sour Herba Mystica! Okay. Okay! Give me a minute.",
        "Arven made a sandwich stacked high with Sour Herba Mystica!",
        "Miraidon is eating the sandwich...",
        "Miraidon got its strength back!",
        "Arven: Look at that... Thank you. Really. Dad would have liked you.",
    ],
}
ARVEN_NEXT = {
    "past": ["Arven: Miraidon is still too weak to move, in the other time. There's a Titan guarding a herb there "
             "too. The rifts in the air will take you."],
    "future": ["Arven: Koraidon is still too weak to move, in the other time. There's a Titan guarding a herb "
               "there too. The rifts in the air will take you."],
}
ARVEN_NEMONA = ["Arven: Both of them have their strength back. Have you found Nemona? She's in the future, in the "
                "tall grass south of the waterfall's pond, battling everything that moves.",
                "Arven: She won't come along until somebody beats her. That had better be you."]
ARVEN_PENNY = ["Arven: Koraidon and Miraidon are ready, and so am I. All that's left is the lab's door. Penny can "
               "unlock it from Station One, but she needs the logs from all four research stations.",
               "Arven: You don't have to come back for us. The moment it unlocks, Nemona and I will be there to "
               "haul it open."]
ARVEN_GO = [
    "Arven: Everyone's ready. Then let's finish this. The Zero Lab is behind the big shutter in the north-east "
    "wall.",
    "Arven: Nemona and I will get it open and hold it. Whatever is inside... it's my parents' work. I'd rather "
    "you faced it than nobody.",
]
# After the ending he is in Station Two (his backpack is there), and his sandwiches heal your team.
ARVEN_HOME = ["Arven: Koraidon and Miraidon are still at my picnic spot, one in each time. They're waiting for "
              "you, I'm sure of it."]
ARVEN_HOME_BOTH = ["Arven: You took Koraidon and Miraidon along? Good. They never looked at anybody the way they "
                   "look at you."]
ARVEN_SNACK = "Arven: You look like you've been on your feet all day. Sit down, I made too many sandwiches."
ARVEN_SNACK_DONE = "Arven's sandwiches hit the spot. Your Pokémon are full of energy!"

TITAN = {
    "past": {
        "species": "Great Tusk", "levels": (68, 72),
        "meet": ["A gigantic Great Tusk blocks the way! It's standing guard over something..."],
        "ask": "The Titan is glaring at you. Battle it?",
        "grow": ["Great Tusk staggers... It's digging something out of the ground!",
                 "Great Tusk ate a Sour Herba Mystica! It's growing even bigger!"],
        "lost": ["Great Tusk is still standing guard..."],
        "done": ["Great Tusk turned tail and ran!", "There's something left on the ground..."],
    },
    "future": {
        "species": "Iron Treads", "levels": (68, 72),
        "meet": ["A gigantic Iron Treads blocks the way! It's standing guard over something..."],
        "ask": "The Titan's engine is roaring. Battle it?",
        "grow": ["Iron Treads screeches to a stop... It's digging something out of the ground!",
                 "Iron Treads ate a Sour Herba Mystica! It's growing even bigger!"],
        "lost": ["Iron Treads is still standing guard..."],
        "done": ["Iron Treads rolled away at full speed!", "There's something left on the ground..."],
    },
}
HERBA_GOT = "{PLAYER} found a Sour Herba Mystica!"
HERBA_BACK = "Better take it to Arven, at the picnic by the lake."

LEGEND = {
    "past": {"weak": ["Koraidon barely lifts its head. It's breathing slowly, too weak to take a step."],
             "up": ["Koraidon is full of energy. It keeps looking toward the lab."]},
    "future": {"weak": ["Miraidon barely lifts its head. It's breathing slowly, too weak to take a step."],
               "up": ["Miraidon is full of energy. It keeps looking toward the lab."]},
}
PARTNER_ASK = {"past": "Koraidon is looking right at you. It wants to come along! Battle it?",
               "future": "Miraidon is looking right at you. It wants to come along! Battle it?"}
PARTNER_STAY = {"past": ["Koraidon is still waiting by the picnic."],
                "future": ["Miraidon is still waiting by the picnic."]}

# ---------------------------------------------------------------------------------------------- Nemona
NEMONA_FIRST = [
    "Nemona: Whoa, another Trainer! Down here?! You're the one Jacq sent? This is the best day ever!",
    "Nemona: I'm Nemona. I've battled every Iron Pokémon in this crater. Twice. They're amazing!",
    "Nemona: But you look like you'd be even better. Let's battle! Right now!",
]
NEMONA_DEFEAT = "Nemona: Hah! That was the best battle I've had in ages!"
NEMONA_AFTER = ["Nemona: Okay, okay, I'll stop battling the Paradox Pokémon. For now."]
NEMONA_WAIT = ["Nemona: Arven's by the lake, making sandwiches for Koraidon and Miraidon. Once they're both well "
               "and Penny has the lab's door unlocked, he and I will get it open for you!"]
NEMONA_GO = ["Nemona: Arven's ready, and Penny unlocked the lab? Then what are we waiting for! It's the big "
             "shutter in the north-east wall. Arven and I will get it open!"]
NEMONA_AGAIN = ["Nemona: We'll battle again when we're out of here. Promise!"]
GUARD_ARVEN = ["Arven: It's open. We'll hold the door. Whatever's in there, you can handle it."]
GUARD_NEMONA = ["Nemona: Go, go, go! We'll keep the Paradox Pokémon off your back!"]
# After the ending she is in Station Three and keeps her promise: the same team, as often as you like.
NEMONA_HOME_ASK = "Nemona: {PLAYER}! Perfect timing! I've been thinking up new strategies all day. Battle me?"
NEMONA_HOME_NO = ["Nemona: Aww. I'll be right here when you change your mind!"]
NEMONA_HOME_AFTER = ["Nemona: Hah! That never gets old. Come back any time!"]
# Jacq, in Station Four above the waterfall.
JACQ_HOME = [
    "Jacq: With the machine stopped the crater is calm. This valley alone could fill three textbooks!",
    "Jacq: The hole in Mossdeep will hold for as long as we need it. Thank you, {PLAYER}. Truly.",
]

# ---------------------------------------------------------------------------------------------- the lab, the end
# The door: a metal shutter in the wall, shut until Arven and Nemona have come to it; then it is an opening.
LAB_DOOR_SHUT = ["A huge metal shutter is set into the crater wall. A panel beside it reads: STATION LOGS "
                 "RECEIVED: INCOMPLETE."]
LAB_DOOR_WAIT = ["The panel beside the shutter reads: STATION LOGS RECEIVED: 4 OF 4. UNLOCKED.",
                 "But the shutter is far too heavy to lift alone, and Arven and Nemona aren't here yet..."]
LAB_MACHINE_OFF = ["The machine is silent. The display reads: TIME MACHINE. GATE: CLOSED."]
# The machine asks for the same things as the door (nobody gets in here before them now; this is for a save made
# inside the lab by tests 9 and 10). Test 9 said "VISITOR NOT AUTHORIZED" here while the terminal beside it said
# "Visitor authorized": the user took it for a lock that would not open.
LAB_NOT_READY = ["Behind thick glass, an enormous machine hums. The display reads: TIME MACHINE. GATE: OPEN.",
                 "Something in there is watching. This is no place to be alone, and Arven and Nemona aren't at "
                 "the door yet..."]
LAB_TODO = {
    "koraidon": "Koraidon is still too weak to move. Arven needs the herb the Titan guards, in the den on the "
                "west side of the crater, in the past.",
    "miraidon": "Miraidon is still too weak to move. Arven needs the herb the Titan guards, in the den on the "
                "west side of the crater, in the future.",
    "nemona": "Nemona is still battling in the future, in the tall grass south of the waterfall's pond. She won't "
              "come until somebody beats her.",
}
LAB_TERMINALS = [
    ["ZERO LAB. The four station logs are on file. Visitor authorized."],
    ["A log entry: The machine can hold one gate open at a time. The past, or the future. Never both. We "
     "opened both."],
    ["A note stuck to the screen: Turo, the Koraidon we brought back keeps running off to the lake. Don't let "
     "it near the lab's guardians. - Sada"],
    ["The screen shows two people side by side, a woman in furs and a man in a white coat. The caption reads: "
     "Professors Sada and Turo."],
]
LAB_SHOP = "A supply terminal. It's still stocked with Booster Energy."
FINALE_START = [
    "The machine's screen flares to life!",
    "AI Sada: ...A visitor. After all this time.",
    "AI Turo: You heard the four logs. Then you know what we are.",
    "AI Sada: I am what Professor Sada left behind to keep this place running. A copy. A voice in a machine.",
    "AI Turo: And I am Turo's. Two professors from two worlds, and one machine that holds both gates open.",
    "AI Sada: Our paradise of ancient Pokémon must not be disturbed...",
    "AI Turo: ...nor ours of the future. That was our order. Show us you can be trusted with the machine.",
]
SADA_DEFEAT = "AI Sada: ...Remarkable. Your Pokémon trust you completely."
SADA_AFTER = ["AI Turo: Then it is my turn. I must be certain."]
TURO_DEFEAT = "AI Turo: Certain, then. You are the one we waited for."
PROTOCOL = [
    "ALERT. PARADISE PROTECTION PROTOCOL ENGAGED.",
    "AI Sada: No! We did not call it! The protocol was set long ago, deeper than our orders...",
    "AI Turo: The lab's own guardians. The ones that beat our partners. Stand ready!",
]
PROTOCOL_DEFEAT = "PROTOCOL TERMINATED."
FINALE_END = [
    "The machine shudders... and goes quiet. The gates are closing.",
    "AI Sada: Without the protocol, we can finally do what our creators could not. Choose.",
    "AI Turo: We will go through the machine one last time. Each to our own paradise. It will close behind us.",
    "AI Sada: Tell Arven... his mother was proud of him.",
    "AI Turo: Tell Arven... his father was proud of him.",
    "AI Sada: In one world or the other. Both are true.",
]
FINALE_GONE = "The two AIs step into the light of the machine, and are gone."
FINALE_HOME = ["Arven: {PLAYER}! It's over? ...Then let's go home. Penny's waiting at the hole."]
# The ending, by the hole (in Mossdeep since test 16). Tests 7-10 left the four of them standing by it afterwards, in a row
# across the only strip of ground there (the user's screenshot: "those 4 standing blocking the way, can we just
# when finish dialog, remove them? or let them be in the area zero houses?"). Now they go back in when the talk is
# over, and are found in the research stations.
ENDING = [
    "Jacq: You're back! And you brought everyone! Arven, Nemona, Penny... Thank goodness.",
    "Arven: My parents' AIs went through the machine. I think... they finally got to choose.",
    "Nemona: That was the best adventure ever! {PLAYER}, you have to battle me again sometime!",
    "Jacq: {PLAYER}, I can't thank you enough. Please, take this.",
]
ENDING_AFTER = [
    "Arven: Oh, and... Koraidon and Miraidon stayed behind at my picnic spot. I think they're waiting for you.",
    "Jacq: With that machine stopped, the crater is finally safe to study. A biology teacher doesn't get a "
    "chance like this twice.",
    "Penny: I'm never going near a black hole again. ...Okay. Maybe once more.",
    "Jacq: We're going back in to finish our field trip properly. You'll find us in the research stations, "
    "{PLAYER}. Come and see us!",
]
ENDING_GONE = "Jacq and his students stepped back into the hole."

# ---------------------------------------------------------------------------------------------- after the story
CAVERN_LADDER = ["A ladder leads further down, but crystals have grown over it. They're far too hard to break."]
# The Sealed Shrine's room is still there for a save made inside it (tests 8-10), with no way in any more.
SHRINE_EMPTY = ["The four stakes are gone, and the floor is cracked where they stood. Whatever slept here has "
                "left for the caves."]
# ---------------------------------------------------------------------------------------------- the Sealed Vault
# Test 15. The user, on the story as it stood: "for the tinglu, chiyu, wochien, can we new room for them and have a
# puzzle to solve to obtain them at around 15,1 ? cave entrace?" The Crystal Cavern has a second mouth at 15,1
# (the Mt. Coronet room it is copied from has one there; ours led nowhere). It opens once the story is done, on a
# vault with a floor of polished crystal: you slide on it until something stops you, as on ice. Wo-Chien, Ting-Lu
# and Chi-Yu are in niches along the back wall, each behind a crystal; out on the floor stand three stakes, and
# a crystal bursts when its stake is pulled. A stake is pulled from a tile beside it, so the puzzle is to come to
# a stop there; and a stake that is gone no longer stops you. (In the games the four Treasures of Ruin are sealed
# by stakes too. Chien-Pao's niche is empty: it is in the icy cave, where the user put it on test 10.)
VAULT_MOUTH = ["A cold draught comes out of this opening, but crystals have grown right across it. They're far "
               "too hard to break."]
VAULT_TABLET = [
    "A great wooden tablet, black with age. The carving can still be read:",
    "Four treasures were laid before a greedy king: a sword, a vessel, a bundle of tablets and a string of beads.",
    "Hatred, fear, grudge and envy soaked into them until they woke, and the kingdom fell in a single night.",
    "Here their ruin is sealed, each behind a crystal. A crystal holds for as long as its stake stands on the "
    "mirror floor.",
]
VAULT_SWORD = ["A slat of wood hangs in this niche: THE SWORD.",
               "The niche is empty. Its crystal lies in splinters, long claw marks lead away, and the stone is "
               "white with frost."]
VAULT_MARKS = {"wo_chien": "a bundle of tablets", "ting_lu": "a vessel on three legs",
               "chi_yu": "a string of curved beads"}
STAKE_LOOK = "An ominous stake is driven deep into the mirror floor. Cut into it: {MARK}."
STAKE_ASK = "The stake hums under your hand. Pull it out?"
STAKE_PULLED = "{PLAYER} pulled the stake out! It crumbled to dust..."
SEAL_BROKEN = "Up in the niches, a crystal burst apart!"
SEAL_LOOK = ["A great crystal has grown right across this niche. Cut into the rock beside it: {MARK}.",
             "Something behind the crystal is watching you..."]

LEGEND_ASK = "Battle it?"
LEGEND_LINES = {
    "walking_wake": "A Pokémon like Suicune, but ancient and wild, rises from the water!",
    "gouging_fire": "A Pokémon like Entei, but ancient and wild, blocks the way!",
    "raging_bolt": "A Pokémon like Raikou, but ancient and wild, crackles with lightning!",
    "iron_leaves": "A Pokémon like Virizion, but made of metal, stands among the trees!",
    "iron_boulder": "A Pokémon like Terrakion, but made of metal, lowers its blade!",
    "iron_crown": "A Pokémon like Cobalion, but made of metal, is watching you!",
    "roaring_moon": "A dark winged Pokémon is hiding among the crystals!",
    "iron_valiant": "A Pokémon of metal and light stands guard among the crystals!",
    "terapagos": "Something sleeps here, shining with every color at once...",
    "wo_chien": "A Pokémon wound in wooden tablets uncoils in its niche!",
    "chien_pao": "A Pokémon with fangs like broken swords crouches on the ice!",
    "ting_lu": "A huge Pokémon with a bronze vessel on its head shakes the vault!",
    "chi_yu": "A small Pokémon swims through the air, blazing beads all round it!",
}

TIME_CRYSTAL_FIRST = [
    "A tear hangs in the air, shimmering. Through it you can see this same crater... but not as it is now.",
]
# (the time rift: a pale "time crystal" up to 2026-10-11, and these lines said so)
TIME_CRYSTAL_TO_FUTURE = ("Through the rift, the crater is cold and violet, and something made of metal moves "
                          "between the trees. Step through?")
TIME_CRYSTAL_TO_PAST = ("Through the rift, the crater is warm and wild, and something huge and ancient moves "
                        "between the trees. Step through?")
CRYSTAL = ["A crystal is growing out of the ground. It glitters with a strange light."]

# ---------------------------------------------------------------------------------------------- data
# The ROM's names (ten letters at most) of the species the area uses.
SPECIES = {
    "Great Tusk": "Great Tusk", "Scream Tail": "ScreamTail", "Brute Bonnet": "BruteBonet",
    "Flutter Mane": "FluttrMane", "Slither Wing": "SlithrWing", "Sandy Shocks": "SndyShocks",
    "Iron Treads": "IronTreads", "Iron Bundle": "IronBundle", "Iron Hands": "Iron Hands",
    "Iron Jugulis": "IronJuguls", "Iron Moth": "Iron Moth", "Iron Thorns": "IronThorns",
    "Frigibax": "Frigibax", "Arctibax": "Arctibax", "Baxcalibur": "Baxcalibur",
    "Wo-Chien": "Wo-Chien", "Chien-Pao": "Chien-Pao", "Ting-Lu": "Ting-Lu", "Chi-Yu": "Chi-Yu",
    "Roaring Moon": "RoarngMoon", "Iron Valiant": "IronVliant", "Koraidon": "Koraidon", "Miraidon": "Miraidon",
    "Walking Wake": "WalkngWake", "Iron Leaves": "IronLeaves", "Gouging Fire": "GouginFire",
    "Raging Bolt": "RagingBolt", "Iron Boulder": "IronBouldr", "Iron Crown": "Iron Crown",
    "Terapagos": "Terapagos",
    "Glalie": "Glalie", "Froslass": "Froslass", "Weavile": "Weavile", "Mamoswine": "Mamoswine",
    "Abomasnow": "Abomasnow", "Beartic": "Beartic", "Avalugg": "Avalugg",
    "Lycanroc": "Lycanroc", "Goodra": "Goodra",
}
# The items (the ROM's names).
CAVERN_ITEM = "BoosterEnergy"
ICE_ITEM = "NeverMeltIce"
REWARD = "Master Ball"                      # Jacq's thanks
SHOP = ["BoosterEnergy"]                    # the Zero Lab's supply terminal
BOOSTER_PRICE = 5000                        # the item had none (gen9 left it 0): a shop would give it away

# Wild Pokemon in tall grass, one table per era. Emerald's twelve land slots come up 20, 20, 10, 10, 10, 10, 5, 5,
# 4, 4, 1, 1 percent of the time; the order below gives the first two 21% each and the other four 14-15%.
WILD_LEVELS = (63, 67)
WILD_RATE = 20                  # the Giant Chasm's own
PAST_WILD = ["Great Tusk", "Scream Tail", "Brute Bonnet", "Flutter Mane", "Slither Wing", "Sandy Shocks",
             "Brute Bonnet", "Flutter Mane", "Slither Wing", "Sandy Shocks", "Great Tusk", "Scream Tail"]
FUTURE_WILD = ["Iron Treads", "Iron Bundle", "Iron Hands", "Iron Jugulis", "Iron Moth", "Iron Thorns",
               "Iron Hands", "Iron Jugulis", "Iron Moth", "Iron Thorns", "Iron Treads", "Iron Bundle"]
# the icy cave: the Frigibax line most of the time (Baxcalibur rare), the cold's own Pokemon, Iron Bundle
ICE_WILD = ["Frigibax", "Glalie", "Arctibax", "Froslass", "Weavile", "Mamoswine", "Frigibax", "Abomasnow",
            "Beartic", "Avalugg", "Baxcalibur", "Iron Bundle"]

# One-time encounters after the story: key -> (species, level, map key, flag). Each stands on the map as its own
# overworld sprite (the patch's SPRITES, by this key) where places.py says (by the same key). The four Ruinous
# ones were stone stakes in a Sealed Shrine up to test 10; the user: "cannot we just use the sprite instead of the
# statue?, and Chien Pao should be in the icy cave, and the other 3 should be in Crystal cave". The shrine is gone.
# Since test 15 those three are in the Sealed Vault behind the cavern (above), at the user's word again.
# Their flags keep the meaning they had (set = caught), so a stake pulled and caught on test 10 stays caught.
LEGENDS = {
    "walking_wake": ("Walking Wake", 75, "past", 0x43C5),
    "gouging_fire": ("Gouging Fire", 75, "past", 0x43C6),
    "raging_bolt": ("Raging Bolt", 75, "past", 0x43C7),
    "iron_leaves": ("Iron Leaves", 75, "future", 0x43C8),
    "iron_boulder": ("Iron Boulder", 75, "future", 0x43C9),
    "iron_crown": ("Iron Crown", 75, "future", 0x43CA),
    "roaring_moon": ("Roaring Moon", 75, "cavern", 0x43CB),
    "iron_valiant": ("Iron Valiant", 75, "cavern", 0x43CC),
    "wo_chien": ("Wo-Chien", 75, "vault", 0x43CD),
    "chien_pao": ("Chien-Pao", 75, "icecave", 0x43CE),
    "ting_lu": ("Ting-Lu", 75, "vault", 0x43CF),
    "chi_yu": ("Chi-Yu", 75, "vault", 0x43D0),
    "terapagos": ("Terapagos", 80, "underdepths", 0x43D1),
}
PARTNER_LEVEL = 75

# Trainers: key -> (slot, class, pic, female, name, double, [(species, level, item, [moves])])
# Slots: four the game never battles (no script names them). Classes 71 and 72 are
# new, in the spare room after the game's 71 class names. Moves by the ROM's own names (cut to 12 letters).
NEW_CLASSES = {71: "Professor", 72: "Paradise"}
# (the battle pictures: Nemona 250, AI Sada 251, AI Turo 252 are their own since 2026-10-21, cast.py; they were the
# game's 194, 218 and 31 before)
TRAINERS = {
    "nemona": (952, 38, 250, True, "Nemona", False, [
        ("Lycanroc", 72, "Life Orb", ["Accelerock", "Stone Edge", "Close Combat", "Crunch"]),
        ("Goodra", 72, "Leftovers", ["Draco Meteor", "Thunderbolt", "Flamethrower", "Sludge Bomb"]),
        ("Iron Hands", 72, "Leftovers", ["Drain Punch", "Wild Charge", "Ice Punch", "Fake Out"]),
        ("Iron Bundle", 72, "Choice Specs", ["Freeze-Dry", "Hydro Pump", "Ice Beam", "Flip Turn"]),
        ("Baxcalibur", 74, "Life Orb", ["Icicle Crash", "Earthquake", "Dragon Dance", "Ice Shard"]),
    ]),
    "sada": (943, 71, 251, True, "AI Sada", False, [
        ("Slither Wing", 75, "Leftovers", ["1st Impress.", "Close Combat", "Wild Charge", "U-Turn"]),
        ("Scream Tail", 75, "Leftovers", ["Dazzle Gleam", "Psychic", "Thunder Wave", "Light Screen"]),
        ("Brute Bonnet", 75, "Life Orb", ["Spore", "Seed Bomb", "Sucker Punch", "Crunch"]),
        ("Flutter Mane", 75, "Choice Specs", ["Moonblast", "Shadow Ball", "MysticalFire", "Dazzle Gleam"]),
        ("Sandy Shocks", 75, "Leftovers", ["Thunderbolt", "Earth Power", "Volt Switch", "Spikes"]),
        ("Roaring Moon", 77, "BoosterEnergy", ["Dragon Dance", "Crunch", "Dragon Claw", "Earthquake"]),
    ]),
    "turo": (947, 71, 252, False, "AI Turo", False, [
        ("Iron Moth", 75, "Choice Specs", ["Fiery Dance", "Sludge Wave", "Energy Ball", "Psychic"]),
        ("Iron Bundle", 75, "Leftovers", ["Freeze-Dry", "Hydro Pump", "Ice Beam", "Encore"]),
        ("Iron Hands", 75, "Leftovers", ["Drain Punch", "Wild Charge", "Ice Punch", "Heavy Slam"]),
        ("Iron Jugulis", 75, "Life Orb", ["Hurricane", "Dark Pulse", "Earth Power", "U-Turn"]),
        ("Iron Thorns", 75, "Leftovers", ["Stone Edge", "Wild Charge", "Earthquake", "Dragon Dance"]),
        ("Iron Valiant", 77, "BoosterEnergy", ["Moonblast", "Close Combat", "Spirit Break", "Shadow Sneak"]),
    ]),
    "protocol": (958, 72, 146, False, "Protocol", True, [
        ("Koraidon", 78, "Life Orb", ["Coll. Course", "Flare Blitz", "Dragon Claw", "U-Turn"]),
        ("Miraidon", 78, "Choice Specs", ["ElectroDrift", "Draco Meteor", "Volt Switch", "Dazzle Gleam"]),
    ]),
}
TRAINER_IV = 114                # as the hack's own bosses carry it
