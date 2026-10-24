"""Kitakami: what people say before the story starts, the flags the town keeps, and who wears which sprite.

The story the user approved is rom/unreleased/kitakami/STORY.md (2026-10-14, the scenes "as written"; the town alone
since 2026-10-16, the den's scenes at Loyalty Plaza). This is the people milestone (2026-10-16, the user: "do it",
to "the people and the way in"): everyone stands where STORY.md's "Mossui's people" puts them and says their
arrival lines; Briar takes you there from Mossdeep and back. The chapters (Carmine's battle, the signboards with
Kieran, the festival, ...) are the next milestones. The wording is mine; the user has not read it in the game.

Lines are wrapped to the message box by lib.box(); a named speaker starts the line, as the hack's own lines do.
{PLAYER} is the player's name.

State (checked free on rom/ 8462fa6f and the user's newest saves, 2026-10-16, _testrun/kitakami/flagcheck_k.py: no
setflag / clearflag / checkflag bytes for them anywhere in the ROM, no aligned word, no map object hides by them,
clear in every save; 0x43E5-0x43E7 and 0x43EA have chance matches and are skipped; 0x43EB and 0x43ED are free too,
kept for the chapters):
"""

F_BRIAR_HIDE = 0x43E8       # (worked out) Briar beside the hole in Mossdeep: shown once Area Zero's ending is over
F_MET_BRIAR = 0x43E9        # Briar has told you about the trip
# The story (2026-10-16, the user: "All 8 chapters", "Lv 70-75"). Its state is flags only: a var that no script
# names can still be set by the hack's code (0x406A and 0x407C looked free and the Journal reads them), while a flag
# is only ever reached through the flag commands, which a search finds. Chosen from the free ones
# _testrun/kitakami/freecheck.py lists for the whole extended range (87 of them on rom/ 8462fa6f).
F_CARMINE = 0x43EB          # Carmine beaten at the bus stop (chapter 1); Kieran has said sorry
F_TASK = 0x43ED             # the caretaker has set the trip's task: the three signboards
F_BOARD = (0x43F2, 0x43F8, 0x43F9)   # each signboard read with Kieran there (in order)
F_PLAZA = 0x43FC            # Kieran showed you Loyalty Plaza: the Festival of Masks begins (night)
F_MASK = 0x43FE             # Ogerpon ran into you at the festival and dropped the Teal Mask
F_TRUTH = 0x440B            # Grandpa told the true story, mended the mask overnight, and Kieran took it
F_WAKE = 0x440C             # Kieran beaten at the plaza; the Loyal Three woke, took the masks: the hunt
F_BEAT = {"okidogi": 0x441B, "munkidori": 0x4337, "fezandipiti": 0x4346}   # each beaten in the hunt: its mask back
F_KIERAN3 = 0x4347          # Kieran beaten for Ogerpon (chapter 8)
F_MASKS = 0x434A            # Ogerpon's four masks battled
F_OGERPON = 0x4352          # Ogerpon caught: the story is over
F_GONE = {"okidogi": 0x4356, "munkidori": 0x4359, "fezandipiti": 0x435D}   # after the story: caught or knocked out
# "hide" flags, worked out from the ones above every time Mossui or the family house is come into or come back to
H_CARMINE, H_KIERAN, H_STATUES, H_OGERPON = 0x4364, 0x436B, 0x436E, 0x436F
H_LIVE = {"okidogi": 0x4370, "munkidori": 0x4373, "fezandipiti": 0x4374}
H_WAKE, H_FEST, H_HOME_CARMINE, H_ELDER = 0x4375, 0x4376, 0x4379, 0x437C
FLAG_NO_BALLS, FLAG_NO_WHITEOUT = 0x272, 0x273     # the hack's Totem flags (Area Zero's Titans use them)
GET_OUTCOME, VAR_RESULT, VAR_8004 = 183, 0x800D, 0x8004
B_WON, B_LOST, B_RAN, B_CAUGHT = 1, 2, 4, 7
MUS_ITEM = 370
OGERPON_SPECIES = {"Teal": 1228, "Wellspring": 1229, "Hearthflame": 1230, "Cornerstone": 1231}   # by their types
MASK_OF = {"okidogi": "Cornerstone", "munkidori": "Wellspring", "fezandipiti": "Hearthflame"}    # STORY.md, 8
L3_SPECIES = {"okidogi": "Okidogi", "munkidori": "Munkidori", "fezandipiti": "Fezndipiti"}        # the ROM's names
L3_NAME = {"okidogi": "Okidogi", "munkidori": "Munkidori", "fezandipiti": "Fezandipiti"}
LEVEL = 75                  # the Loyal Three and Ogerpon (the user: Lv 70-75); Carmine 70-71, Kieran 72-75
L3_ITEM = "Black Sludge"
AZ_STAGE, AZ_DONE = 0x40A8, 4                          # Area Zero's stage var: 4, the ending is over (story.py)
FRESH = 0x40F9                                         # the map-copy stamp var Area Zero keeps (story.py FRESH)

# ---- who wears what. The new people: the hack's sprite table (graphics 0x4E + the entry), ksprites.py. The rest:
# the game's own sprites (main table, 0x08505620), picked from the hack's townsfolk so that the town draws with
# few palettes (tags 0x1105 and 0x1106 for nearly everyone; the hack hands out six object palettes a screen).
EXT = 0x4E
GFX = {
    "elder": 21, "organiser": 27, "vendor_apples": 44, "vendor_masks": 20, "vendor_mochi": 19, "vendor_rice": 31,
    "farmer": 36, "mother": 26, "child": 56, "lanterns": 15, "hiker": 48, "carver": 39,
    "caretaker": 14, "grandpa": 29, "old_woman": 22, "old_man2": 73, "old_woman2": 30,
}

# ---------------------------------------------------------------------------------------------- Briar, the way in
BRIAR_INTRO = [
    "Briar: Oh! You must be {PLAYER}! I'm Briar. I teach at Blueberry Academy, all the way over in Unova.",
    "Briar: Jacq told me everything! The hole by the sea, Area Zero, the professors... He hasn't stopped talking "
    "about you.",
    "Briar: I'm taking a few of my students on a school trip to Kitakami. It's a little village up in the "
    "mountains, and its Festival of Masks is coming up.",
    "Briar: Old legends, ogres, masks... It's exactly my kind of history! And there's one seat left on the bus.",
]
BRIAR_ASK = "Briar: Would you like to come along to Kitakami?"
BRIAR_ASK_AGAIN = "Briar: Ready to come to Kitakami? There's still a seat on the bus!"
BRIAR_YES = "Briar: Wonderful! The bus is waiting. All aboard!"
BRIAR_NO = "Briar: No rush! I'll be right here whenever you're ready."
BRIAR_BACK_ASK = "Briar: Shall we take the bus back to Mossdeep?"
BRIAR_BACK_YES = "Briar: Off we go! Kitakami will be right here when you come back."
BRIAR_BACK_NO = "Briar: Take your time! Every corner of Kitakami has a story in it."

# ---------------------------------------------------------------------------------------------- Mossui Town
CARMINE = [
    "Carmine: Hmph. Another outsider come to gawk at our festival?",
    "Carmine: The Festival of Masks belongs to Kitakami. Don't go poking around where you're not wanted.",
]
KIERAN = [
    "Kieran: Oh! Um... hi. Sorry if my sister was rude to you. That's just how Carmine is.",
    "Kieran: I'm Kieran. Have you heard about the ogre of Kitakami? Everyone says it was a monster...",
    "Kieran: ...but I've always felt a little sorry for it. Nobody ever tells the story from its side.",
]
ELDER = [
    "Okidogi, Munkidori and Fezandipiti. The Loyal Three. Long ago they drove the ogre out of Kitakami.",
    "I come to give them thanks every morning. Without them, who knows what that ogre would have done to us?",
]
STATUES = {
    "okidogi": ["A stone statue of Okidogi, one of the Loyal Three. Its arms look strong enough to crush a "
                "boulder."],
    "munkidori": ["A stone statue of Munkidori, one of the Loyal Three. Its sharp eyes seem to follow you."],
    "fezandipiti": ["A stone statue of Fezandipiti, one of the Loyal Three. Even in stone, its feathers look "
                    "graceful."],
}
ORGANISER = [
    "The Festival of Masks is nearly here! Everyone in Mossui puts on a mask and comes down to the market.",
    "The stalls are still being set up, so come back for the festival. You won't regret it!",
]
VENDORS = {
    "vendor_apples": ["Still stacking the apples! At the festival I'll have Sweet Apples and Tart Apples, fresh "
                      "from the trees up the valley."],
    "vendor_masks": ["Masks of the Loyal Three, carved by hand! ...The ogre's mask? Nobody would buy one of "
                     "those."],
    "vendor_mochi": ["Kitakami mochi, soft and sweet! Folks say one bite makes you feel stronger. I'll have plenty "
                     "at the festival."],
    "vendor_rice": ["Rice balls and grilled skewers, the taste of the festival! The grill isn't lit yet, though. "
                    "Come back hungry!"],
}
VILLAGERS = {
    "farmer": ["I grow rice in the paddies here and apples up the valley. When the maples turn red, the harvest "
               "is in."],
    "mother": ["My little one is scared of the ogre stories. I keep telling her the Loyal Three protect us."],
    "child": ["Is the ogre coming back? ...Mama says no. But I still don't go near the woods at night."],
    "lanterns": ["I make the paper lanterns for the festival. When they're all lit, the whole market glows red!"],
    "hiker": ["I came over the mountains to see the festival. Funny thing... I'm sure I heard something big moving "
              "in the woods last night."],
    "carver": ["I carve masks for the festival. Every child wants a Loyal Three mask. Nobody ever asks for the "
               "ogre's."],
}
SIGNS = {
    "sign_hall": ["KITAKAMI HALL. The Mask Hall, where the treasures of the Loyal Three are kept."],
    "sign_shrine": ["LOYALTY PLAZA. In thanks to the Loyal Three, the heroes of Kitakami."],
    "sign_pond": ["MOSSUI POND. Please keep to the bridge."],
    "sign_bus": ["MOSSUI TOWN. Home of the Festival of Masks. Bus stop."],
    "legend_1": ["THE LEGEND OF THE LOYAL THREE, part 1 of 3.",
                 "Long ago, an ogre came down from the mountains and ran wild through Kitakami, smashing and "
                 "stealing whatever it found."],
    "legend_2": ["THE LEGEND OF THE LOYAL THREE, part 2 of 3.",
                 "Three brave Pokémon stood up to the ogre: mighty Okidogi, clever Munkidori and graceful "
                 "Fezandipiti. Together they drove it back into the mountains."],
    "legend_3": ["THE LEGEND OF THE LOYAL THREE, part 3 of 3.",
                 "The three heroes fell in that battle. The village honours them as the Loyal Three, and keeps "
                 "their treasures in Kitakami Hall to this day."],
}

# ---------------------------------------------------------------------------------------------- the insides
CARETAKER = [
    "Welcome to Kitakami Hall! The students from Blueberry Academy are in town for the festival.",
    "This is the Mask Hall. The Loyal Three's masks go on show here, on the stage, for the festival.",
]
# the Mask Hall's plaques, under the three cases on the stage (khall.PLAQUES): before the Loyal Three wake, after
# (the cases smashed), after the story (the masks went home)
PLAQUES = {
    "Wellspring": ["THE WELLSPRING MASK.", "Treasure of the Loyal Three. Kept in Kitakami Hall since the day they drove "
                   "the ogre from the village."],
    "Hearthflame": ["THE HEARTHFLAME MASK.", "Treasure of the Loyal Three. Worn by the leader of the Festival of "
                    "Masks, in their honour."],
    "Cornerstone": ["THE CORNERSTONE MASK.", "Treasure of the Loyal Three. Said to be as hard as the mountain it was "
                    "carved from."],
}
PLAQUE_SMASHED = ["The glass is smashed. The case is empty."]
PLAQUE_AFTER = ["The case is empty. A new card on it says: \"Returned to Ogerpon, its true owner.\""]
GRANDPA = [
    "Grandpa: Welcome, welcome! Make yourself at home. Carmine and Kieran are my grandchildren.",
    "Grandpa: My family has made the masks for the festival for longer than anyone can remember. It's a fine "
    "tradition.",
]
OLD_WOMAN = [
    "My grandmother used to say the masks up in Kitakami Hall were never the Loyal Three's to begin with.",
    "She called them \"a gift\". A gift to whom, I never found out. Funny thing to say, isn't it?",
]
OLD_MAN2 = ["My wife's family has an odd old tale. A little purple Pokémon that turned up one festival and handed "
            "out mochi."]
OLD_WOMAN2 = ["Now, now, dear, it's only a story. ...Though the mochi part does sound lovely."]

# =============================================================================================== the story
# Chapters as STORY.md has them (the user approved them as written, 2026-10-14; the town alone and the den's scenes
# at Loyalty Plaza, 2026-10-16). Phases for the people who stay in the town: A before the festival, B the festival
# and the morning after, C while the Loyal Three are loose, D after the story.

# ---- chapter 1: Carmine at the bus stop, Kieran, the task
CARMINE_BATTLE = [
    "Carmine: Hmph. Another outsider come to gawk at our festival?",
    "Carmine: The Festival of Masks belongs to Kitakami. If you want to poke around here, you'll have to get past "
    "me first!",
]
CARMINE_DEFEAT = "Carmine: Wh-what?! You're actually strong..."
CARMINE_LOST = ["Carmine: Hah! Not so tough after all. Come back when you can keep up."]
KIERAN_ARRIVES = [
    "Kieran: Carmine! You can't just battle every visitor who gets off the bus!",
    "Carmine: I can if they're nosy outsiders.",
    "Kieran: Sorry about my sister... I'm Kieran. You must be the Trainer Ms. Briar told us about.",
    "Kieran: The caretaker at Kitakami Hall has the task for the school trip. It's up the steps behind the torii, "
    "on the hill.",
    "Carmine: Whatever. Don't get lost, outsider.",
]
KIERAN_TO_HALL = ["Kieran: The caretaker at Kitakami Hall has the task for the trip. It's the big teal building on "
                  "the hill!"]
CARETAKER_TASK = [
    "Ah, you're the guest Ms. Briar told me about! She left the trip's task with me.",
    "Long ago, our village wrote the legend of the Loyal Three on three signboards. Find all three and read them "
    "in order.",
    "Kieran said he would go with you. He's waiting by the first signboard, in the rice fields to the west.",
]
CARETAKER_REMIND = ["The three signboards: the west rice fields, the east rice fields, and the top of the avenue. "
                    "Kieran will show you."]
CARETAKER_FESTIVAL = ["The Festival of Masks! Everyone in Mossui wears a mask tonight. Enjoy it!"]
CARETAKER_MORNING = ["What a festival that was! I'm still finding confetti under the seats."]
CARETAKER_MASKS_GONE = [
    "The masks! The three masks in the Mask Hall are gone! Someone smashed the case in the night!",
    "The Loyal Three's treasures, stolen... Who would do such a thing?",
]
CARETAKER_AFTER = ["Kieran told us the truth about the masks. From now on, the Mask Hall will tell Ogerpon's story, "
                   "not the Loyal Three's."]

# ---- chapter 2: the signboards with Kieran
KIERAN_AT_BOARD = ["Kieran: This is the first signboard! Go on, read it."]
KIERAN_AT_BOARD_2 = ["Kieran: Here's the second one! Read it, read it!"]
KIERAN_AT_BOARD_3 = ["Kieran: This is the last signboard. Go on."]
BOARD_TALK = [
    ["Kieran: The ogre came down from the mountains... but I always wonder why. Nobody does something like that for "
     "no reason, right?",
     "Kieran: The next signboard is in the rice fields on the east side. I'll race you!"],
    ["Kieran: Mighty Okidogi, clever Munkidori, graceful Fezandipiti. Everyone loves them. Nobody ever carved a "
     "mask for the ogre.",
     "Kieran: The last one is at the top of the avenue, past the pond. Come on!"],
    ["Kieran: \"The three heroes fell in that battle.\" ...So the ogre won? Then why does everyone call it the "
     "villain?",
     "Kieran: There's somewhere I want to show you. Meet me at Loyalty Plaza, by the red trees!"],
]
KIERAN_PLAZA = [
    "Kieran: These are the Loyal Three. Everyone in Mossui comes here to thank them.",
    "Kieran: But I keep thinking about the ogre. Chased out of its home, all alone... and nobody ever asked for its "
    "side of the story.",
    "Kieran: ...Sorry. That's weird, isn't it? Carmine says I'm obsessed.",
    "Kieran: Oh! It's getting dark already. The Festival of Masks starts tonight! You'll come, won't you?",
]
EVENING = "Night fell over Mossui, and the lanterns of the Festival of Masks were lit."

# ---- chapter 3: the Festival of Masks
CARMINE_FESTIVAL = [
    "Carmine: Oh. It's you. Grandpa says I have to show you around the festival, so... welcome. I guess.",
    "Carmine: Everyone wears a mask tonight. Even the stalls are selling them. It's the only night of the year this "
    "village is any fun.",
]
CARMINE_HUH = "Carmine: Huh? What's that little one doing here?"
OGERPON_BUMP = "A small Pokémon in a teal mask ran straight into you! Its mask clattered to the ground..."
GOT_MASK = "You picked up the mask. It's chipped along one edge."
CARMINE_AFTER_BUMP = [
    "Carmine: Was that... a Pokémon? Wearing a festival mask? I've never seen one like it.",
    "Carmine: And that mask looks old. Really old. Grandpa will know what it is. Come to our house, it's on the "
    "street west of the market!",
]
KIERAN_MISSING = ["Kieran isn't at the festival."]

# ---- chapter 4: the true story
GRANDPA_TRUTH = [
    "Grandpa: That mask... where did you find it? A masked Pokémon dropped it? At the festival?",
    "Grandpa: Then it's true. My family made this mask, long ago. Let me tell you the story the signboards don't "
    "tell.",
    "Grandpa: A man and his Pokémon once came to Kitakami from far away. The villagers were afraid of them, and "
    "kept their distance.",
    "Grandpa: My ancestor, a mask-maker, made them four masks so they could join the Festival of Masks like anyone "
    "else: Teal, Wellspring, Hearthflame and Cornerstone.",
    "Grandpa: But three Pokémon wanted those masks for themselves. They stole three of them, and the man was lost "
    "in the struggle.",
    "Grandpa: His Pokémon flew into a fury and struck the thieves down. The villagers saw only an ogre... and drove "
    "her out.",
    "Grandpa: And the three thieves? The village named them heroes. The Loyal Three. The \"treasures\" in the Hall "
    "are the masks they stole.",
    "Carmine: So the ogre... was the good one all along?",
    "Grandpa: I believe so. This is her Teal Mask. Leave it with me tonight, and I'll mend that chip.",
]
NIGHT_PASSES = "Grandpa worked on the mask long into the night..."
GRANDPA_MORNING = [
    "Grandpa: There! Good as new. ...Hm? Where did I put it? It was right here on the table!",
    "Carmine: Kieran! He was listening at the door. He's wanted to meet the ogre his whole life...",
    "Carmine: He'll have gone to Loyalty Plaza. He always goes there when he's upset. Go! I'll catch up!",
]
GRANDPA_KIERAN = ["Grandpa: Kieran has taken the mask to Loyalty Plaza, I'm sure of it. Please, bring him home."]
GRANDPA_HUNT = ["Grandpa: The Loyal Three, awake again after all these years... Bring those masks back to her, "
                "please. They were always hers."]

# ---- chapter 5 and 6: Kieran, and the Loyal Three wake
KIERAN_ANGRY = [
    "Kieran: You met her. The ogre. At the festival... and you didn't tell me.",
    "Kieran: You knew I wanted to meet her more than anything! I'm keeping this mask. If I have it, she'll come to "
    "me!",
    "Kieran: You want it back? Then battle me!",
]
KIERAN_DEFEAT = "Kieran: ...No. No, no, no!"
KIERAN_LOST = ["Kieran: Go away! This mask is mine now."]
WAKE = [
    "The ground is shaking!",
    "The statues of the Loyal Three are... moving!",
]
ELDER_FLEES = "The Loyal Three have come back?! Heroes, have you come to protect us?"
OGERPON_COMES = "Kieran: The ogre...! She's here! She came for her mask!"
CORNERED = "Okidogi, Munkidori and Fezandipiti closed in on the masked Pokémon!"
CARMINE_RUNS_IN = [
    "Carmine: Kieran! {PLAYER}! Someone broke into the Mask Hall! The three masks are gone!",
    "Carmine: Wait... those three took them! Don't just stand there, help her!",
]
DRIVE_OFF = "You, Carmine and Kieran stood beside the masked Pokémon. The Loyal Three backed away, and fled into the town!"
MASK_GIVEN = [
    "Kieran: Here... this is yours. I'm sorry.",
    "The masked Pokémon turned away from Kieran. It's looking at you.",
    "Kieran handed you the Teal Mask, and you held it out to the Pokémon.",
    "Ogerpon put on the Teal Mask!",
]
OGERPON_LEAVES = "Ogerpon gave a happy cry, and ran off toward the woods."
KIERAN_HURT = "Kieran: ...She didn't even look at me."
CARMINE_HUNT = [
    "Carmine: Those three ran off with the stolen masks. One went past the shrine's red trees, one toward the pond, "
    "and one up the Hall's hill.",
    "Carmine: If we get the masks back, Ogerpon might come back too. Go on, I'll look after my brother.",
]
CARMINE_HUNT_AGAIN = ["Carmine: One went past the shrine's red trees, one toward the pond, and one up the Hall's hill. "
                      "Get those masks back!"]
KIERAN_HUNT = ["Kieran: This is all my fault... Please, get her masks back."]

# ---- chapter 7: the hunt
L3_MEET = {
    "okidogi": "Okidogi is guarding the Cornerstone Mask! It flexes its huge arms...",
    "munkidori": "Munkidori is hunched over the Wellspring Mask by the pond. Its eyes snap open!",
    "fezandipiti": "Fezandipiti is preening on the hill, the Hearthflame Mask at its feet!",
}
L3_ASK = "Battle it for the mask?"
L3_WON = {k: "%s dropped the %s Mask and fled!" % (n, MASK_OF[k]) for k, n in L3_NAME.items()}
L3_GOT = {k: "You got the %s Mask back!" % MASK_OF[k] for k in L3_NAME}
L3_LOST = "It's still guarding the mask."
ALL_MASKS = "You have all three of Ogerpon's masks! Ogerpon should be waiting at Loyalty Plaza."

# ---- chapter 8: Ogerpon
KIERAN_WAITS = ["Kieran: She's waiting for you. Not me."]
CARMINE_WAITS = ["Carmine: Go on. She's been waiting for you."]
FINAL_MASKS = [
    "You held out the three masks. Ogerpon took them back, one by one... She looks so happy!",
    "Ogerpon looked up at you. She wants to come with you!",
]
KIERAN_FINAL = [
    "Kieran: No! She should be MY partner! I've waited my whole life to meet her!",
    "Kieran: Battle me! If I win, she comes with me!",
]
KIERAN_FINAL_DEFEAT = "Kieran: Why... why can't I ever win?"
KIERAN_FINAL_LOST = ["Kieran: See? She belongs with me."]
KIERAN_GIVES_UP = ["Carmine: Kieran... she chose.", "Kieran: ...Fine. Fine!"]
OGERPON_TEST = "Ogerpon raised her club. She wants to see your strength for herself, in every mask she has!"
# the party is healed before each of these (six battles in a row: the first story run ran out of PP in the fifth)
REST = "Your team caught its breath. "
MASK_ON = {name: REST + "Ogerpon put on the %s Mask!" % name for name in OGERPON_SPECIES}
OGERPON_STILL = "Ogerpon is waiting for you to try again."
OGERPON_READY = REST + "Ogerpon put the Teal Mask back on. She's ready to come with you!"
OGERPON_NOT_CAUGHT = "Ogerpon is still here, waiting for you."
ENDING = [
    "Kieran: ...I'm going home.",
]
ENDING_AFTER = [
    "Carmine: Kieran! ...He'll lock himself in his room again. Ugh.",
    "Carmine: Thanks, {PLAYER}. For Ogerpon, and... everything. Grandpa can change her mask for you. Come by the "
    "house.",
    "Carmine: And those three are still hiding in town. Without the masks they're just Pokémon. Maybe you can catch "
    "them.",
]

# ---- after the story
L3_AFTER = {
    "okidogi": "Okidogi is sulking in the corner. Without the mask, it doesn't look so tough.",
    "munkidori": "Munkidori is dozing by the pond again.",
    "fezandipiti": "Fezandipiti is preening alone on the hill.",
}
GRANDPA_MASKS_ASK = "Grandpa: Shall I change Ogerpon's mask?"
GRANDPA_WHICH = {name: "Grandpa: The %s Mask?" % name for name in OGERPON_SPECIES}
GRANDPA_DONE = "Grandpa: There! It suits her."
GRANDPA_NO_OGERPON = "Grandpa: Bring Ogerpon with you, and I'll change her mask."
GRANDPA_LATER = "Grandpa: Come back any time."
CARMINE_HOME = {
    "A": ["Carmine: What? This is my house. Grandpa's the one who wants visitors, not me."],
    "D": ["Carmine: Kieran's locked himself in the back room. He won't even come out to eat.",
          "Carmine: He'll be fine. ...He has to be."],
}

# ---- the town, by phase
ELDER_PHASES = {
    "A": ELDER,
    "C": ["The statues... the Loyal Three came back to life? And they stole the masks? Heroes don't steal..."],
    "D": ["Kieran told us what really happened long ago. All these years, we gave thanks to thieves. I am ashamed."],
}
ORGANISER_PHASES = {
    "A": ORGANISER,
    "B": ["The Festival of Masks is on! Grab a mask from the stalls and enjoy the night!"],
    "C": ["With those three on the loose, I'm glad the festival is over..."],
    "D": ["Next year, the festival will honour Ogerpon too. It's the least we can do."],
}
VILLAGER_PHASES = {
    "farmer": {"A": VILLAGERS["farmer"],
               "B": ["The paddies look lovely under the lanterns, don't they?"],
               "C": ["Something big trampled my rice this morning! It had huge arms..."],
               "D": ["An ogre who was a hero all along... I'll be telling my grandkids that one."]},
    "mother": {"A": VILLAGERS["mother"],
               "B": ["Look at my little one in her mask! Isn't she adorable?"],
               "C": ["We're staying close to home until those three are caught."],
               "D": ["My little one wants an Ogerpon mask now. The stall sold out in an hour!"]},
    "child": {"A": VILLAGERS["child"],
              "B": ["I'm wearing a Loyal Three mask! Rawr!"],
              "C": ["The statues walked away! I saw them!"],
              "D": ["The ogre's name is Ogerpon! I want to meet her!"]},
    "lanterns": {"A": VILLAGERS["lanterns"],
                 "B": ["See? Every lantern lit. The whole market glows red!"],
                 "C": ["I'll keep a few lanterns burning tonight. Nobody wants to be in the dark with those three about."],
                 "D": ["Next year I'll make a teal lantern. For Ogerpon."]},
    "hiker": {"A": VILLAGERS["hiker"],
              "B": ["What a festival! I'm glad I made the climb."],
              "C": ["Told you I heard something in the woods!"],
              "D": ["So the thing in the woods was Ogerpon? Ha! What a story to take home."]},
    "carver": {"A": VILLAGERS["carver"],
               "B": ["Every child in a Loyal Three mask tonight. I carved most of them!"],
               "C": ["The Loyal Three, thieves? I've carved their faces my whole life..."],
               "D": ["I'm carving my first ogre mask. Ogerpon's, I mean. It's harder than it looks."]},
}
VENDOR_OPEN = {
    "vendor_apples": "Candy apples! Sweet and tart, fresh from the valley!",
    "vendor_mochi": "Festival mochi! One bite and you'll feel stronger!",
    "vendor_rice": "Rice balls and skewers! Just the thing for a hungry Trainer!",
}
VENDOR_BYE = "Come again!"
VENDOR_MASKS_PHASES = {
    "A": VENDORS["vendor_masks"],
    "B": ["Loyal Three masks! Okidogi, Munkidori, Fezandipiti, take your pick!"],
    "C": ["Nobody wants a Loyal Three mask today. Can't think why."],
    "D": ["Ogerpon masks? Sold out! I'm carving more as fast as I can."],
}
SHOPS = {
    "vendor_apples": ["Sweet Apple", "Tart Apple"],
    "vendor_mochi": ["HP Up", "Protein", "Iron", "Calcium", "Zinc", "Carbos"],
    "vendor_rice": ["Hyper Potion", "Max Potion", "Full Heal", "Revive"],
}
OLD_WOMAN_AFTER = ["\"A gift\"... Grandmother meant the masks were a gift to that Pokémon. Now I understand."]
OLD_COUPLE_AFTER = ["Ogerpon... and the masks were hers all along? My, my. Kitakami will never be the same."]

# =============================================================================================== Part 2: Mochi Mayhem
# The epilogue of Scarlet / Violet's DLC (the user, 2026-10-17: "do it", after "what is the last entry pokemon?"),
# in Mossui alone as Part 1 is: Kieran's letter (Briar, after the story), Carmine dancing, Nemona gone for mochi,
# two villagers, Kieran's grandparents at the Hall, Arven and Penny, Nemona at Loyalty Plaza with Pecharunt. As the
# official one (Serebii's Mochi Mayhem page, read 2026-10-17); its friends from Paldea are Area Zero's.
# Flags: free by _testrun/kitakami/freecheck.py on the Kitakami build (2026-10-17), the 0x437D-0x439D run.
F_P2_START = 0x437D         # Briar gave you Kieran's letter: Part 2 has begun (Mossui at night until it is over)
F_P2_KIERAN = 0x4381        # Kieran met you in the market; Nemona went off for mochi
F_P2_SHIGE, F_P2_AYA = 0x4382, 0x4385      # the two villagers beaten (the farmer, the mother)
F_P2_ELDERS = 0x4386        # Kieran's grandparents beaten before Kitakami Hall
F_P2_ARVEN, F_P2_PENNY = 0x438B, 0x438D    # Arven and Penny beaten in the market (then Pecharunt flees)
F_P2_NEMONA = 0x438E        # Nemona beaten at Loyalty Plaza
F_PECHARUNT = 0x4390        # Pecharunt caught: everyone is themselves again
H_P2_ARVEN, H_P2_PENNY, H_P2_NEMONA, H_P2_PECHA = 0x4391, 0x4395, 0x439B, 0x439C
H_P2_ELDERS = 0x439D        # the grandparents before the Hall (and Grandpa away from home meanwhile: H_P2_HOME)
H_P2_HOME = 0x439F
PECHARUNT = "Pecharunt"     # (species 1237, National Dex 1025: the ROM's)
P2_LEVEL = 82               # Pecharunt; the trainers 76-82 (official 79-88; Part 1 ends at 75)

MOCHI_CHATTER = ["Mochi... mochi... Have you got any mochi?"]
# (the villagers, the grandparents, Arven and Penny are woken by talking, not battled: the user, 2026-10-17, "remove
# unncessary battle" - only Nemona's and Pecharunt's are left; each one's *_DEFEAT line is what they say on waking)
P2_SNAP = "You called out, again and again... At last they blinked, as if waking from a dream."
BRIAR_LETTER = [
    "Briar: There you are! A letter came for you, from Kieran. Let me read it to you...",
    "\"Strange things are happening in Kitakami. Carmine isn't herself, and people say there's a curse.\"",
    "\"Please come back, and bring your friends from Paldea. I've written to them too. - Kieran\"",
]
BRIAR_P2_ASK = "Briar: Arven, Nemona and Penny are on their way already! Shall we go to Kitakami?"
BRIAR_P2_HERE = ["Briar: Arven, Nemona and Penny just got off the bus. They're in the market with Kieran!"]
MOCHI_HINT = ["Someone left a little peach-shaped plush at my stall... Oh! And Ms. Briar was looking for you. "
              "Something about a letter."]
KIERAN_P2_MEET = [
    "Kieran: You came! Thank you... Arven, Nemona, Penny, you too.",
    "Kieran: It's Carmine. For days she's done nothing but dance and talk about mochi. And she's not the only one.",
    "Kieran: The villagers say it's a curse. The festival's long over, but people dance in the streets all night...",
    "Nemona: Mochi, huh? I'll go and get us some from the stall! Back in a sec!",
    "Kieran: Wait, Nemona! ...She's gone. Let's look around. The apple farmer and the mother were acting strange too.",
]
KIERAN_P2_VILLAGERS = ["Kieran: The apple farmer by the paddies, and the mother on the street. Something's wrong "
                       "with them."]
KIERAN_P2_HALL = ["Kieran: Grandpa and Grandma went up to Kitakami Hall... dancing! Hurry!"]
KIERAN_P2_FRIENDS = ["Kieran: Arven and Penny ate some mochi... Now they're dancing too! They're right there!"]
KIERAN_P2_PLAZA = ["Kieran: That peach-shaped Pokémon went to Loyalty Plaza. Nemona's up there with it!"]
KIERAN_P2_AFTER = ["Kieran: Everyone's back to normal. ...Carmine and I are going back to Blueberry Academy.",
                   "Kieran: Next time, let's battle at the League Club. I'll be stronger. Promise."]
CARMINE_P2 = ["Carmine: Mochi, mochi, mochi! Want some? It's sooo good!"]
CARMINE_P2_AFTER = ["Carmine: Ugh, my head... I can't remember a thing since that mochi. Thanks for snapping me "
                    "out of it, outsider. ...I mean, friend."]
SHIGE_P2 = ["Mochi... more mochi... A little peach gave me mochi! Mochi, mochi..."]
SHIGE_DEFEAT = "Mochi... huh? What am I doing out here?"
SHIGE_P2_AFTER = ["I don't know what came over me. A little purple Pokémon handed me a mochi, and then..."]
AYA_P2 = ["Mochi mochi! The sweetest mochi in Kitakami! Want to dance? Dance with me!"]
AYA_DEFEAT = "Ow... where did my mochi go?"
AYA_P2_AFTER = ["I saw Kieran's grandparents going up to Kitakami Hall. With a whole box of mochi..."]
ELDERS_P2 = ["Grandpa: Mochi... Grandma's mochi... the finest in all Kitakami...",
             "Grandma: Dance with us, dear! Round and round! Hee hee!"]
ELDERS_DEFEAT = "Grandpa: Oh my... Why are we out here in the middle of the night?"
ELDERS_P2_AFTER = ["Grandma: Someone left a box of mochi at our door. We shouldn't have eaten it...",
                   "Grandpa: Go on, child. I heard Arven shouting down in the market."]
ARVEN_P2 = ["Arven: Mochi... the perfect sandwich filling... Mochi!"]
ARVEN_DEFEAT = "Arven: Huh...? Why do I taste peaches?"
PENNY_P2 = ["Penny: Mochi... Eevee wants mochi... everyone wants mochi..."]
PENNY_DEFEAT = "Penny: Wh-what happened? Was I... dancing?"
FRIEND_P2_AFTER = {"arven": ["Arven: Ugh. Go on, we'll catch up. Don't let that thing get away!"],
                   "penny": ["Penny: That Pokémon... it was floating right over us. Go!"]}
PECHA_FLEES = ["A little Pokémon with a peach-shaped shell was floating over the market!",
               "Kieran: That's it! That's what's giving everyone mochi! ...It's going to Loyalty Plaza!"]
NEMONA_P2 = ["Nemona: Mochi... and a battle! The best of both! Come on, let's go all out!"]
NEMONA_P2_DEFEAT = "Nemona: Whoa... what was I doing? Was that... mochi?"
PECHA_BATTLE = "The peach-shaped Pokémon trembled... then it came at you!"
PECHA_WEAK = ["The peach-shaped Pokémon is worn out!", "Kieran: Now! Catch it before it gets away!"]
PECHA_CAUGHT = "You caught Pecharunt!"
PECHA_NO_ROOM = ["There's no room for it: your party and your boxes are full.",
                 "Kieran: It's too tired to go anywhere. Make some room and come back!"]
PECHA_STILL = ["Pecharunt is too tired to move."]
PECHA_LOST = ["Pecharunt is still here, trembling."]
P2_ENDING = [
    "Kieran: Look... everyone's waking up!",
    "Nemona: That was the strangest battle ever. I loved it!",
    "Kieran: So it was Pecharunt that fed the Loyal Three its mochi, long ago... That's why they did what they did.",
    "Kieran: Everyone's going home to sleep. Thank you. I'll see you at the bus stop in the morning.",
]
ARVEN_P2_WAIT = ["Arven: Kieran told us everything. Something smells sweet around here... too sweet."]
PENNY_P2_WAIT = ["Penny: A curse? Curses aren't real. ...Right?"]
NEMONA_P2_WAIT = ["Nemona: Kitakami! New Trainers, new Pokémon! I want to battle everyone!"]
