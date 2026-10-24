"""Kitakami's story, all eight chapters (2026-10-16, the user: "All 8 chapters", battles at "Lv 70-75"). The scenes
are STORY.md's, in the town alone, the Dreaded Den's at Loyalty Plaza. What people say: kstory.py.

Stages (worked out from the story's flags, never kept):
   s0  arrival: Carmine at the bus stop (talk: her battle; then Kieran comes, says sorry, sends you to the Hall)
   s1  F_CARMINE: Kieran below the Hall's torii; the caretaker sets the task (F_TASK)
   s2-s4  the signboards in order, Kieran waiting by the next one; each read with him there sets F_BOARD[k]
   s5  Kieran at Loyalty Plaza: the statues, his feelings for the ogre; evening falls (F_PLAZA) and the town is the
       festival's (the evening colours: kasm.py)
   s6  the festival: Carmine at the market gate; Ogerpon runs into you, drops the Teal Mask (F_MASK); the stalls are
       shops from now on
   s7  night: Grandpa's true story at the family house; the mask mended overnight, then gone (F_TRUTH)
   s8  Kieran at the plaza with the mask: his battle; the Loyal Three wake, Ogerpon comes, Carmine runs in, the
       three are driven off with the masks, Ogerpon takes the Teal Mask from you (F_WAKE)
   s9  the hunt: Okidogi behind the shrine's grove, Munkidori by the pond, Fezandipiti on the Hall's hill, each a
       wild battle (no Poke Balls, no white-out) for its mask (F_BEAT)
   s10 Ogerpon waits at the plaza: Kieran's battle for her (F_KIERAN3), Ogerpon in all four masks (F_MASKS), then
       a wild battle to catch her (F_OGERPON)
   s11 after: the Loyal Three can be caught where they hide (caught or knocked out: gone, F_GONE); Grandpa changes
       Ogerpon's mask (kasm.kit_mask); Kieran has locked himself in.
Every story battle is fought with flag 0x273 on (a loss is no white-out: you are healed and can try again).
"""
import kstory as KS
import ksprites as KSP

MOSSUI_LOCALS = {}          # key -> local id (filled by objects())
POS = {    # stage -> {key: (x, y, facing)} for the two who move about (worked out on every way in)
    0: {"carmine": (24, 45, "down"), "kieran": (20, 30, "down")},
    1: {"kieran": (13, 26, "down")},
    2: {"kieran": (10, 36, "left")},
    3: {"kieran": (37, 36, "right")},
    4: {"kieran": (27, 5, "left")},
    5: {"kieran": (36, 11, "up")},
    6: {"carmine": (25, 35, "down")},
    7: {},
    8: {"kieran": (34, 11, "up")},
    9: {"carmine": (36, 13, "left"), "kieran": (34, 13, "right")},
    10: {"carmine": (37, 10, "left"), "kieran": (33, 10, "right")},
    11: {},
}
# the rest of the story's objects in Mossui (they are shown or not by the stage; positions fixed)
STORY_OBJECTS = {
    "ogerpon": ("ogerpon", 35, 10, "down", KS.H_OGERPON),
    "live_okidogi": ("live_okidogi", 42, 10, "left", KS.H_LIVE["okidogi"]),
    "live_munkidori": ("live_munkidori", 28, 10, "down", KS.H_LIVE["munkidori"]),
    "live_fezandipiti": ("live_fezandipiti", 17, 14, "down", KS.H_LIVE["fezandipiti"]),
    "wake_okidogi": ("live_okidogi", 33, 9, "right", KS.H_WAKE),
    "wake_munkidori": ("live_munkidori", 35, 9, "down", KS.H_WAKE),
    "wake_fezandipiti": ("live_fezandipiti", 37, 9, "left", KS.H_WAKE),
    "ogerpon_fest": ("ogerpon", 24, 41, "up", KS.H_FEST),
    # Part 2 (a number: the main table's sprite)
    "arven2": (67, 19, 41, "right", KS.H_P2_ARVEN), "penny2": (70, 27, 41, "left", KS.H_P2_PENNY),
    "nemona2": ("az_nemona", 20, 41, "right", KS.H_P2_NEMONA), "pecharunt": ("pecharunt", 35, 10, "down", KS.H_P2_PECHA),
    "grandpa2": (29, 10, 16, "right", KS.H_P2_ELDERS), "grandma2": (22, 14, 16, "left", KS.H_P2_ELDERS),
}
L3 = ("okidogi", "munkidori", "fezandipiti")
# Part 2, Mochi Mayhem (2026-10-17): stages 12-17 (worked out from F_P2_* as 0-11 are); who stands where at each
# (kplaces: placements). The objects of Part 2 are STORY_OBJECTS too: Nemona in Area Zero's own sprite (since
# 2026-10-21, ksprites.AZ_PEOPLE; the game's 20 before), Arven and Penny in the game's 67 and 70 (Area Zero's own
# sprites for them, one palette between the two, made seven palettes in the market at stages 12 and 15: their stand-
# ins share the mother's and child's), Kieran's grandparents in the game's (29, 22); Pecharunt our sprite entry 204. The Loyal Three keep away from
# the town for the night (p12-p16: six palettes at the plaza) and are back where they hide the morning after.
#   p12  Briar gave you Kieran's letter: Kieran and the three in the market, Carmine dancing on the street
#   p13  Kieran has told you; Nemona went off for mochi: the farmer (Shige) and the mother (Aya), woken by talking
#   p14  the grandparents dance before Kitakami Hall (woken); Kieran waits below the Hall's steps
#   p15  Arven and Penny ate the mochi: woken in the market; then Pecharunt flies to the plaza
#   (since 2026-10-17 the only battles are Nemona's and Pecharunt's: the user, "remove unncessary battle")
#   p16  Nemona and Pecharunt at Loyalty Plaza: her battle, then Pecharunt's (won: it is yours: givemon)
#   p17  the morning after: Kieran and Carmine at the bus stop; the three have gone home
P2POS = {
    12: {"kieran": (26, 41, "left"), "carmine": (27, 33, "down"), "arven2": (19, 41, "right"),
         "nemona2": (20, 41, "right"), "penny2": (27, 41, "left")},
    13: {"kieran": (26, 41, "left"), "carmine": (27, 33, "down"), "arven2": (19, 41, "right"),
         "penny2": (27, 41, "left")},
    14: {"kieran": (14, 19, "left"), "carmine": (27, 33, "down"), "arven2": (19, 41, "right"),
         "penny2": (27, 41, "left"), "grandpa2": (10, 16, "right"), "grandma2": (14, 16, "left")},
    15: {"kieran": (24, 36, "down"), "carmine": (27, 33, "down"), "arven2": (21, 40, "right"),
         "penny2": (26, 40, "left")},
    16: {"kieran": (33, 12, "right"), "carmine": (37, 12, "left"), "nemona2": (36, 11, "down"),
         "pecharunt": (36, 10, "down")},
    17: {"kieran": (25, 45, "left"), "carmine": (24, 45, "down")},
}
P2_PECHA_MARKET = (24, 38)     # where Pecharunt shows itself over the market once Arven and Penny are beaten
P2_HIDE = {"arven2": KS.H_P2_ARVEN, "penny2": KS.H_P2_PENNY, "nemona2": KS.H_P2_NEMONA, "pecharunt": KS.H_P2_PECHA,
           "grandpa2": KS.H_P2_ELDERS, "grandma2": KS.H_P2_ELDERS, "carmine": KS.H_CARMINE, "kieran": KS.H_KIERAN}
SE_PIN = 21
# Carmine sees you one step up from where Briar's bus leaves you (2026-10-20, the user: "Carmine should automatically
# see u and start battle when the player step up 1 step ... alert emote"): a coord event on that tile while this var
# is 0. A temp var (0x4000-0x400F are cleared on every map load); state_mossui sets it to 1 once she is beaten, and
# her script checks the flag itself too (the story's state stays flags only: see kstory).
VAR_SPOT = 0x4009
OPPOSITE = {"down": "up", "up": "down", "left": "right", "right": "left"}
MT = {"down": 0x08, "up": 0x07, "left": 0x09, "right": 0x0A}
MASKS = ("Teal", "Wellspring", "Hearthflame", "Cornerstone")
FAMILY_CARMINE = (8, 3, "left")
# the scenes' starting tiles (kplaces: placements): Kieran runs in after Carmine's battle (2 tiles down), Carmine as
# the Loyal Three wake (4 tiles up); where you stand when evening falls
KIERAN_RUNS_IN = (23, 41)
CARMINE_RUNS_IN = (36, 16)
EVENING_AT = (23, 32)


def stage_of(flags):
    """the stage a set of story flags means (for the checks)"""
    f = set(flags)
    if KS.F_OGERPON in f: return 11
    if KS.F_WAKE in f: return 10 if all(KS.F_BEAT[k] in f for k in L3) else 9
    for st, fl in ((8, KS.F_TRUTH), (7, KS.F_MASK), (6, KS.F_PLAZA), (5, KS.F_BOARD[2]), (4, KS.F_BOARD[1]),
                   (3, KS.F_BOARD[0]), (2, KS.F_TASK), (1, KS.F_CARMINE)):
        if fl in f: return st
    return 0


def visible(stage, beaten=(), gone=()):
    """{key: (x, y)} of the story's movable objects shown at a stage (for the layout checks)"""
    out = {k: tuple(v[:2]) for k, v in (P2POS if stage >= 12 else POS)[stage].items()}
    if stage == 10:
        out["ogerpon"] = STORY_OBJECTS["ogerpon"][1:3]
    for k in L3:
        if (stage == 9 and k not in beaten) or (stage in (11, 17) and k not in gone):
            out["live_" + k] = STORY_OBJECTS["live_" + k][1:3]
    return out


class Chapters:
    def __init__(self, P, rom, ids, numbers, mask_key):
        self.P, self.rom, self.ids, self.numbers, self.mask_key = P, rom, ids, numbers, mask_key
        self.L = MOSSUI_LOCALS

    # ---- small helpers on top of People
    def say(self, s, key, line):
        s.raw(0x0F, 0x00); s.ptr(self.P.text(key, line)); s.raw(0x09, 0x04)

    def lines(self, s, key, lines):
        self.P.say_all(s, key, lines)

    def place(self, s, local, x, y, face):
        s.raw(0x63); s.h(local, x, y)                                      # setobjectxyperm
        s.raw(0x65); s.h(local); s.raw(MT[face])                           # setobjectmovementtype

    def mv(self, s, local, key, spec):
        self.P.moves[key] = spec
        s.move(local, key)

    def tbattle(self, s, trainer, key, defeat):
        """trainerbattle 3 (no intro; the defeat text), with flag 0x273 on: a loss is no white-out"""
        s.setflag(KS.FLAG_NO_WHITEOUT)
        s.raw(0x5C, 0x03); s.h(trainer, 0); s.ptr(self.P.text(key, defeat))
        s.clearflag(KS.FLAG_NO_WHITEOUT)

    def outcome(self, s):
        s.specialvar(KS.VAR_RESULT, KS.GET_OUTCOME)

    def phase(self, s, name, phases):
        """branch on the story's phase: A before the festival, B the festival and the morning after, C the Loyal
        Three loose, D after the story; a phase not given says the one before it"""
        s.if_set(KS.F_PECHARUNT, "phase_D")                # (Part 2 over: as after the story)
        s.if_set(KS.F_P2_START, "phase_M")                 # Part 2: everyone wants mochi
        for p, flag in (("D", KS.F_OGERPON), ("C", KS.F_WAKE), ("B", KS.F_PLAZA)):
            s.if_set(flag, "phase_" + p)
        said = "A"
        for p in "ABCD":
            if p in phases:
                said = p
            s.here("phase_" + p)
            self.lines(s, "%s_%s" % (name, said), phases[said])
            s.release(); s.end()
        s.here("phase_M")
        if "M" in phases:
            self.lines(s, "%s_M" % name, phases["M"])
        else:
            self.lines(s, "k_mochi_chatter", KS.MOCHI_CHATTER)
        s.release(); s.end()

    # ---- the stage worked out: Mossui's ON_TRANSITION and ON_RESUME call this
    def state_mossui(self):
        s = self.P.new("k_state_mossui")
        L = self.L
        s.setvar(VAR_SPOT, 0)                               # Carmine's coord event: on until she is beaten
        s.if_unset(KS.F_CARMINE, "spot"); s.setvar(VAR_SPOT, 1); s.here("spot")
        for f in (KS.H_CARMINE, KS.H_KIERAN, KS.H_OGERPON, KS.H_WAKE, KS.H_FEST) + tuple(KS.H_LIVE.values()) + \
                (KS.H_P2_ARVEN, KS.H_P2_PENNY, KS.H_P2_NEMONA, KS.H_P2_PECHA, KS.H_P2_ELDERS):
            s.setflag(f)
        s.clearflag(KS.H_STATUES); s.clearflag(KS.H_ELDER)
        s.if_unset(KS.F_WAKE, "statues"); s.setflag(KS.H_STATUES); s.here("statues")
        s.if_set(KS.F_P2_START, "p2")
        s.if_set(KS.F_OGERPON, "s11")
        s.if_set(KS.F_WAKE, "s9")
        for st, fl in ((8, KS.F_TRUTH), (7, KS.F_MASK), (6, KS.F_PLAZA), (5, KS.F_BOARD[2]), (4, KS.F_BOARD[1]),
                       (3, KS.F_BOARD[0]), (2, KS.F_TASK), (1, KS.F_CARMINE)):
            s.if_set(fl, "s%d" % st)
        for st in range(0, 9):
            s.here("s%d" % st)
            for key, (x, y, face) in POS[st].items():
                self.place(s, L[key], x, y, face)
                s.clearflag(KS.H_CARMINE if key == "carmine" else KS.H_KIERAN)
            s.ret()
        s.here("s9")                                        # the hunt, or (all three beaten) Ogerpon waiting
        for k in L3:
            s.if_unset(KS.F_BEAT[k], "hunt")
        for key, (x, y, face) in POS[10].items():
            self.place(s, L[key], x, y, face)
        s.clearflag(KS.H_CARMINE); s.clearflag(KS.H_KIERAN); s.clearflag(KS.H_OGERPON)
        s.ret()
        s.here("hunt")
        for key, (x, y, face) in POS[9].items():
            self.place(s, L[key], x, y, face)
        s.clearflag(KS.H_CARMINE); s.clearflag(KS.H_KIERAN)
        for k in L3:
            s.if_set(KS.F_BEAT[k], "hunt_" + k); s.clearflag(KS.H_LIVE[k]); s.here("hunt_" + k)
        s.ret()
        s.here("s11")
        for k in L3:
            s.if_set(KS.F_GONE[k], "after_" + k); s.clearflag(KS.H_LIVE[k]); s.here("after_" + k)
        s.ret()
        # Part 2
        s.here("p2")
        s.if_set(KS.F_PECHARUNT, "p17")
        s.if_unset(KS.F_P2_ARVEN, "p2a"); s.if_set(KS.F_P2_PENNY, "p16"); s.here("p2a")
        s.if_set(KS.F_P2_ELDERS, "p15")
        s.if_unset(KS.F_P2_SHIGE, "p2b"); s.if_set(KS.F_P2_AYA, "p14"); s.here("p2b")
        s.if_set(KS.F_P2_KIERAN, "p13")
        s.goto("p12")
        for st in range(12, 18):
            s.here("p%d" % st)
            for key, (x, y, face) in P2POS[st].items():
                self.place(s, L[key], x, y, face)
                s.clearflag(P2_HIDE[key])
            if st == 17:                                    # the Loyal Three back where they hide
                for k in L3:
                    s.if_set(KS.F_GONE[k], "p2l_" + k); s.clearflag(KS.H_LIVE[k]); s.here("p2l_" + k)
            s.ret()
        return "k_state_mossui"

    def state_family(self):
        s = self.P.new("k_state_family")
        s.setflag(KS.H_HOME_CARMINE)
        s.clearflag(KS.H_P2_HOME)                           # Grandpa: at home, but out dancing in Part 2 (p12-p14)
        s.if_unset(KS.F_P2_START, "home")
        s.if_set(KS.F_P2_ELDERS, "home")
        s.setflag(KS.H_P2_HOME)
        s.here("home")
        s.if_set(KS.F_PECHARUNT, "show")
        s.if_set(KS.F_P2_START, "out")                      # Carmine is in town, dancing
        s.if_set(KS.F_OGERPON, "show")
        s.if_set(KS.F_TRUTH, "out")
        s.if_set(KS.F_MASK, "show")
        s.if_set(KS.F_PLAZA, "out")
        s.if_set(KS.F_CARMINE, "show")
        s.here("out"); s.ret()
        s.here("show"); s.clearflag(KS.H_HOME_CARMINE); s.ret()
        return "k_state_family"

    def refresh_people(self, s):
        """after a step of the story inside a visit: the stage's people worked out, and the ones it shows put on the
        map now (addobject spawns a person whose flag is clear)"""
        s.call(("script", "k_state_mossui"))

    # ---- chapter 1: Carmine at the bus stop
    def carmine(self, ids):
        P, L = self.P, self.L
        s = P.new("k_carmine")
        s.lock(); s.faceplayer()
        s.if_set(KS.F_P2_START, "p2")
        s.if_set(KS.F_OGERPON, "bye")
        s.if_set(KS.F_WAKE, "hunt")
        s.if_set(KS.F_MASK, "bye")
        s.if_set(KS.F_PLAZA, "festival")
        s.if_unset(KS.F_CARMINE, "battle")
        s.here("bye"); s.release(); s.end()
        s.here("battle"); s.goto(("script", "k_carmine_fight"))
        # the festival: Ogerpon runs into you
        s.here("festival")
        self.lines(s, "k_carmine_festival", KS.CARMINE_FESTIVAL); s.closemessage()
        s.clearflag(KS.H_FEST); s.addobject(L["ogerpon_fest"])
        self.mv(s, L["ogerpon_fest"], "k_fest_run", "fast up*4")
        s.playse(SE_PIN); self.mv(s, L["carmine"], "k_carmine_alarm", "!")
        self.say(s, "k_carmine_huh", KS.CARMINE_HUH); s.closemessage()
        s.cry(KS.OGERPON_SPECIES["Teal"])
        self.say(s, "k_ogerpon_bump", KS.OGERPON_BUMP); s.closemessage()
        self.mv(s, L["ogerpon_fest"], "k_fest_flee", "!, fast down*6")
        s.removeobject(L["ogerpon_fest"])
        s.playfanfare(KS.MUS_ITEM); self.say(s, "k_got_mask", KS.GOT_MASK); s.waitfanfare()
        self.lines(s, "k_carmine_after_bump", KS.CARMINE_AFTER_BUMP); s.closemessage()
        s.setflag(KS.F_MASK)
        s.fade(1); s.removeobject(L["carmine"]); s.fade(0)
        s.release(); s.end()
        # the hunt, Ogerpon waiting
        s.here("hunt")
        for k in L3:
            s.if_unset(KS.F_BEAT[k], "hunting")
        self.lines(s, "k_carmine_waits", KS.CARMINE_WAITS); s.release(); s.end()
        s.here("hunting")
        self.lines(s, "k_carmine_hunt_again", KS.CARMINE_HUNT_AGAIN); s.release(); s.end()
        s.here("p2")
        s.if_set(KS.F_PECHARUNT, "p2_after")
        self.lines(s, "k_carmine_p2", KS.CARMINE_P2); s.release(); s.end()
        s.here("p2_after"); self.lines(s, "k_carmine_p2_after", KS.CARMINE_P2_AFTER); s.release(); s.end()
        self.carmine_fight(ids)
        return "k_carmine"

    def carmine_fight(self, ids):
        """the battle at the bus stop: from talking to her (k_carmine) or from her seeing you (k_carmine_spots)"""
        P, L = self.P, self.L
        s = P.new("k_carmine_fight")
        self.lines(s, "k_carmine_battle", KS.CARMINE_BATTLE); s.closemessage()
        self.tbattle(s, ids["carmine"], "k_carmine_defeat", KS.CARMINE_DEFEAT)
        self.outcome(s); s.if_var(KS.VAR_RESULT, KS.B_WON, "lost", cond=5)
        self.place(s, L["kieran"], *KIERAN_RUNS_IN, "down")
        s.clearflag(KS.H_KIERAN); s.addobject(L["kieran"])
        self.mv(s, L["kieran"], "k_kieran_runs_in", "walk down*2")
        self.lines(s, "k_kieran_arrives", KS.KIERAN_ARRIVES); s.closemessage()
        s.setflag(KS.F_CARMINE)
        s.fade(1); s.removeobject(L["carmine"]); s.removeobject(L["kieran"]); self.refresh_people(s); s.fade(0)
        s.release(); s.end()
        s.here("lost")
        s.heal(); self.lines(s, "k_carmine_lost", KS.CARMINE_LOST); s.release(); s.end()
        return "k_carmine_fight"

    def carmine_spots(self, spot):
        """the coord event on `spot`, one step up from where Briar's bus leaves you: until she is beaten Carmine sees
        you there - SE_PIN and "!", she turns to you, you to her - and her battle begins. She stands next to the
        tile (kpeople.layout_report checks it, and that the tile is the only way on from the bus stop)."""
        P, L = self.P, self.L
        s = P.new("k_carmine_spots")
        s.lockall()
        s.if_set(KS.F_CARMINE, "done")
        (cx, cy, _), (tx, ty) = POS[0]["carmine"], spot
        toward = "right" if tx > cx else "left" if tx < cx else "down" if ty > cy else "up"
        s.playse(SE_PIN); self.mv(s, L["carmine"], "k_carmine_spots_alarm", "!")
        self.mv(s, L["carmine"], "k_carmine_spots_turn", "face " + toward)
        self.mv(s, 0xFF, "k_carmine_spots_you", "face " + OPPOSITE[toward])
        s.goto(("script", "k_carmine_fight"))
        s.here("done"); s.setvar(VAR_SPOT, 1); s.releaseall(); s.end()
        return "k_carmine_spots"

    # ---- Kieran: chapters 1, 2, 5 and 8
    def kieran(self, ids):
        P, L = self.P, self.L
        s = P.new("k_kieran")
        s.lock(); s.faceplayer()
        s.if_set(KS.F_P2_START, "p2")
        s.if_set(KS.F_OGERPON, "bye")
        s.if_set(KS.F_WAKE, "hunt")
        s.if_set(KS.F_TRUTH, "angry")
        s.if_set(KS.F_PLAZA, "bye")
        s.if_set(KS.F_BOARD[2], "plaza")
        for k in (1, 0):
            s.if_set(KS.F_BOARD[k], "board%d" % (k + 2))
        s.if_set(KS.F_TASK, "board1")
        s.if_set(KS.F_CARMINE, "hall")
        self.lines(s, "k_kieran", KS.KIERAN); s.release(); s.end()
        s.here("bye"); s.release(); s.end()
        s.here("hall"); self.lines(s, "k_kieran_hall", KS.KIERAN_TO_HALL); s.release(); s.end()
        for n, lines in ((1, KS.KIERAN_AT_BOARD), (2, KS.KIERAN_AT_BOARD_2), (3, KS.KIERAN_AT_BOARD_3)):
            s.here("board%d" % n); self.lines(s, "k_kieran_board%d" % n, lines); s.release(); s.end()
        # chapter 2's end: Loyalty Plaza, then evening
        s.here("plaza")
        self.lines(s, "k_kieran_plaza", KS.KIERAN_PLAZA)
        self.say(s, "k_evening", KS.EVENING); s.closemessage()
        s.setflag(KS.F_PLAZA)
        s.fade(1)
        g, n = self.numbers["mossui"]
        s.warpsilent(g, n, *EVENING_AT); s.raw(0x27)
        s.release(); s.end()
        # chapters 5 and 6: his battle, then the Loyal Three wake
        s.here("angry")
        self.lines(s, "k_kieran_angry", KS.KIERAN_ANGRY); s.closemessage()
        self.tbattle(s, ids["kieran2"], "k_kieran_defeat", KS.KIERAN_DEFEAT)
        self.outcome(s); s.if_var(KS.VAR_RESULT, KS.B_WON, "lost", cond=5)
        s.shake()
        self.say(s, "k_wake_0", KS.WAKE[0]); s.closemessage()
        s.playse(SE_PIN); self.mv(s, L["elder"], "k_elder_alarm", "!")
        self.say(s, "k_elder_flees", KS.ELDER_FLEES); s.closemessage()
        s.fade(1)
        s.removeobject(L["elder"])
        for k in L3:
            s.removeobject(L[k])                           # the statues (they share H_STATUES)
        s.clearflag(KS.H_WAKE)
        for k in L3:
            s.addobject(L["wake_" + k])
        s.fade(0)
        s.cry(self.ids["Okidogi"])
        self.say(s, "k_wake_1", KS.WAKE[1]); s.closemessage()
        s.clearflag(KS.H_OGERPON); s.addobject(L["ogerpon"])
        s.cry(KS.OGERPON_SPECIES["Teal"])
        s.playse(SE_PIN); self.mv(s, L["kieran"], "k_kieran_alarm", "!")
        self.say(s, "k_ogerpon_comes", KS.OGERPON_COMES); s.closemessage()
        self.say(s, "k_cornered", KS.CORNERED); s.closemessage()
        self.place(s, L["carmine"], *CARMINE_RUNS_IN, "up")
        s.clearflag(KS.H_CARMINE); s.addobject(L["carmine"])
        self.mv(s, L["carmine"], "k_carmine_runs_in", "walk up*4")
        self.lines(s, "k_carmine_runs_in", KS.CARMINE_RUNS_IN); s.closemessage()
        self.say(s, "k_drive_off", KS.DRIVE_OFF); s.closemessage()
        s.fade(1)
        for k in L3:
            s.removeobject(L["wake_" + k])
        s.fade(0)
        self.lines(s, "k_mask_given", KS.MASK_GIVEN); s.closemessage()
        s.cry(KS.OGERPON_SPECIES["Teal"])
        self.say(s, "k_ogerpon_leaves", KS.OGERPON_LEAVES); s.closemessage()
        s.fade(1); s.removeobject(L["ogerpon"]); s.fade(0)
        self.say(s, "k_kieran_hurt", KS.KIERAN_HURT)
        self.lines(s, "k_carmine_hunt", KS.CARMINE_HUNT); s.closemessage()
        s.setflag(KS.F_WAKE)
        self.refresh_people(s)
        for k in L3:
            s.addobject(L["live_" + k])
        s.release(); s.end()
        s.here("lost")
        s.heal(); self.lines(s, "k_kieran_lost", KS.KIERAN_LOST); s.release(); s.end()
        s.here("hunt")
        for k in L3:
            s.if_unset(KS.F_BEAT[k], "hunting")
        self.lines(s, "k_kieran_waits", KS.KIERAN_WAITS); s.release(); s.end()
        s.here("hunting"); self.lines(s, "k_kieran_hunt", KS.KIERAN_HUNT); s.release(); s.end()
        # Part 2: where the night has got to
        s.here("p2")
        s.if_set(KS.F_PECHARUNT, "p2_after")
        s.if_unset(KS.F_P2_ARVEN, "p2_x"); s.if_set(KS.F_P2_PENNY, "p2_plaza"); s.here("p2_x")
        s.if_set(KS.F_P2_ELDERS, "p2_friends")
        s.if_unset(KS.F_P2_SHIGE, "p2_y"); s.if_set(KS.F_P2_AYA, "p2_hall"); s.here("p2_y")
        s.if_set(KS.F_P2_KIERAN, "p2_villagers")
        self.lines(s, "k_kieran_p2_meet", KS.KIERAN_P2_MEET); s.closemessage()
        s.fade(1); s.removeobject(L["nemona2"]); s.setflag(KS.F_P2_KIERAN); self.refresh_people(s); s.fade(0)
        s.release(); s.end()
        for label, key, lines in (("p2_villagers", "k_kieran_p2_villagers", KS.KIERAN_P2_VILLAGERS),
                                  ("p2_hall", "k_kieran_p2_hall", KS.KIERAN_P2_HALL),
                                  ("p2_friends", "k_kieran_p2_friends", KS.KIERAN_P2_FRIENDS),
                                  ("p2_plaza", "k_kieran_p2_plaza", KS.KIERAN_P2_PLAZA),
                                  ("p2_after", "k_kieran_p2_after", KS.KIERAN_P2_AFTER)):
            s.here(label); self.lines(s, key, lines); s.release(); s.end()
        return "k_kieran"

    # ---- chapter 2: a signboard read with Kieran there
    def board(self, k, sign_lines):
        P, L = self.P, self.L
        name = "k_legend_%d" % (k + 1)
        s = P.new(name)
        s.lockall()
        P.sign_all(s, name, sign_lines)
        s.if_set(KS.F_BOARD[k], "done")
        s.if_unset(KS.F_TASK, "done")
        if k:
            s.if_unset(KS.F_BOARD[k - 1], "done")
        self.lines(s, "k_board_talk_%d" % k, KS.BOARD_TALK[k]); s.closemessage()
        s.fade(1)
        s.removeobject(L["kieran"]); s.setflag(KS.F_BOARD[k]); self.refresh_people(s)
        s.fade(0)
        s.here("done"); s.releaseall(); s.end()
        return name

    # ---- chapter 7: the hunt; after the story, the catch
    def loyal(self, k):
        P, L = self.P, self.L
        sp = self.ids[KS.L3_SPECIES[k]]
        item = self.ids["item:" + KS.L3_ITEM]
        s = P.new("k_live_" + k)
        s.lock(); s.faceplayer()
        s.cry(sp)
        s.if_set(KS.F_OGERPON, "after")
        self.say(s, "k_l3_meet_" + k, KS.L3_MEET[k])
        P.ask(s, "k_l3_ask", KS.L3_ASK); s.closemessage()
        s.if_yes("fight"); s.release(); s.end()
        s.here("fight")
        s.setflag(KS.FLAG_NO_BALLS); s.setflag(KS.FLAG_NO_WHITEOUT)
        s.wildbattle(sp, KS.LEVEL, item); s.dowildbattle()
        s.clearflag(KS.FLAG_NO_BALLS); s.clearflag(KS.FLAG_NO_WHITEOUT)
        self.outcome(s); s.if_var(KS.VAR_RESULT, KS.B_WON, "lost", cond=5)
        self.say(s, "k_l3_won_" + k, KS.L3_WON[k]); s.closemessage()
        s.fade(1); s.removeobject(L["live_" + k]); s.fade(0)
        s.playfanfare(KS.MUS_ITEM); self.say(s, "k_l3_got_" + k, KS.L3_GOT[k]); s.waitfanfare()
        s.setflag(KS.F_BEAT[k])
        for j in L3:
            s.if_unset(KS.F_BEAT[j], "out")
        self.say(s, "k_all_masks", KS.ALL_MASKS)
        self.refresh_people(s); s.addobject(L["ogerpon"])
        s.here("out"); s.release(); s.end()
        s.here("lost")
        s.if_var(KS.VAR_RESULT, KS.B_LOST, "stays", cond=5); s.heal()
        s.here("stays"); self.say(s, "k_l3_lost", KS.L3_LOST); s.release(); s.end()
        s.here("after")
        self.say(s, "k_l3_after_" + k, KS.L3_AFTER[k]); s.closemessage()
        s.setflag(KS.FLAG_NO_WHITEOUT)
        s.wildbattle(sp, KS.LEVEL, item); s.dowildbattle()
        s.clearflag(KS.FLAG_NO_WHITEOUT)
        self.outcome(s)
        s.if_var(KS.VAR_RESULT, KS.B_CAUGHT, "gone")
        s.if_var(KS.VAR_RESULT, KS.B_WON, "gone")
        s.if_var(KS.VAR_RESULT, KS.B_LOST, "free", cond=5); s.heal()
        s.here("free"); s.release(); s.end()
        s.here("gone")
        s.setflag(KS.F_GONE[k]); s.fade(1); s.removeobject(L["live_" + k]); s.fade(0); s.release(); s.end()
        return "k_live_" + k

    # ---- chapter 8: Ogerpon
    def ogerpon(self, ids):
        P, L = self.P, self.L
        s = P.new("k_ogerpon")
        s.lock(); s.faceplayer()
        s.cry(KS.OGERPON_SPECIES["Teal"])
        s.if_set(KS.F_MASKS, "catch")
        s.if_set(KS.F_KIERAN3, "masks")
        self.lines(s, "k_final_masks", KS.FINAL_MASKS); s.closemessage()
        s.playse(SE_PIN); self.mv(s, L["kieran"], "k_kieran_alarm2", "!")
        self.lines(s, "k_kieran_final", KS.KIERAN_FINAL); s.closemessage()
        self.tbattle(s, ids["kieran3"], "k_kieran_final_defeat", KS.KIERAN_FINAL_DEFEAT)
        self.outcome(s); s.if_var(KS.VAR_RESULT, KS.B_WON, "lost_kieran", cond=5)
        s.setflag(KS.F_KIERAN3)
        self.lines(s, "k_kieran_gives_up", KS.KIERAN_GIVES_UP)
        s.here("masks")
        self.say(s, "k_ogerpon_test", KS.OGERPON_TEST); s.closemessage()
        for name in MASKS:
            sp = KS.OGERPON_SPECIES[name]
            s.heal()                                   # KS.REST: six battles in a row otherwise
            self.say(s, "k_mask_on_" + name, KS.MASK_ON[name]); s.closemessage()
            s.cry(sp)
            s.setflag(KS.FLAG_NO_BALLS); s.setflag(KS.FLAG_NO_WHITEOUT)
            s.wildbattle(sp, KS.LEVEL); s.dowildbattle()
            s.clearflag(KS.FLAG_NO_BALLS); s.clearflag(KS.FLAG_NO_WHITEOUT)
            self.outcome(s); s.if_var(KS.VAR_RESULT, KS.B_WON, "lost_masks", cond=5)
        s.setflag(KS.F_MASKS)
        s.here("catch")
        s.heal()
        self.say(s, "k_ogerpon_ready", KS.OGERPON_READY); s.closemessage()
        s.setflag(KS.FLAG_NO_WHITEOUT)
        s.wildbattle(KS.OGERPON_SPECIES["Teal"], KS.LEVEL); s.dowildbattle()
        s.clearflag(KS.FLAG_NO_WHITEOUT)
        self.outcome(s); s.if_var(KS.VAR_RESULT, KS.B_CAUGHT, "not_caught", cond=5)
        s.setflag(KS.F_OGERPON)
        s.fade(1); s.removeobject(L["ogerpon"]); s.fade(0)
        self.lines(s, "k_ending", KS.ENDING); s.closemessage()
        s.fade(1); s.removeobject(L["kieran"]); s.fade(0)
        self.lines(s, "k_ending_after", KS.ENDING_AFTER); s.closemessage()
        s.fade(1); s.removeobject(L["carmine"]); self.refresh_people(s)
        for k in L3:
            s.addobject(L["live_" + k])
        s.fade(0)
        s.release(); s.end()
        s.here("lost_kieran")
        s.heal(); self.lines(s, "k_kieran_final_lost", KS.KIERAN_FINAL_LOST); s.release(); s.end()
        s.here("lost_masks")
        s.if_var(KS.VAR_RESULT, KS.B_LOST, "masks_wait", cond=5); s.heal()
        s.here("masks_wait"); self.say(s, "k_ogerpon_still", KS.OGERPON_STILL); s.release(); s.end()
        s.here("not_caught")
        s.if_var(KS.VAR_RESULT, KS.B_LOST, "catch_wait", cond=5); s.heal()
        s.here("catch_wait"); self.say(s, "k_ogerpon_not_caught", KS.OGERPON_NOT_CAUGHT); s.release(); s.end()
        return "k_ogerpon"

    # ---- the family house: Grandpa (chapter 4; the masks after the story), Carmine
    def grandpa(self):
        P = self.P
        s = P.new("k_grandpa")
        s.lock(); s.faceplayer()
        s.if_set(KS.F_PECHARUNT, "masks")
        s.if_set(KS.F_P2_ELDERS, "p2")
        s.if_set(KS.F_OGERPON, "masks")
        s.if_set(KS.F_WAKE, "hunt")
        s.if_set(KS.F_TRUTH, "kieran")
        s.if_set(KS.F_MASK, "truth")
        self.lines(s, "k_grandpa", KS.GRANDPA); s.release(); s.end()
        s.here("truth")
        self.lines(s, "k_grandpa_truth", KS.GRANDPA_TRUTH)
        self.say(s, "k_night", KS.NIGHT_PASSES); s.closemessage()
        s.fade(1); s.delay(60); s.fade(0)
        self.lines(s, "k_grandpa_morning", KS.GRANDPA_MORNING)
        s.setflag(KS.F_TRUTH)
        s.release(); s.end()
        s.here("kieran"); self.lines(s, "k_grandpa_kieran", KS.GRANDPA_KIERAN); s.release(); s.end()
        s.here("hunt"); self.lines(s, "k_grandpa_hunt", KS.GRANDPA_HUNT); s.release(); s.end()
        s.here("masks")
        P.ask(s, "k_grandpa_masks_ask", KS.GRANDPA_MASKS_ASK); s.if_yes("which")
        self.say(s, "k_grandpa_later", KS.GRANDPA_LATER); s.release(); s.end()
        s.here("which")
        for name in MASKS:
            P.ask(s, "k_grandpa_which_" + name, KS.GRANDPA_WHICH[name])
            s.if_yes("wear_" + name)
        self.say(s, "k_grandpa_later", KS.GRANDPA_LATER); s.release(); s.end()
        for name in MASKS:
            s.here("wear_" + name)
            s.setvar(KS.VAR_8004, KS.OGERPON_SPECIES[name]); s.goto("wear")
        s.here("wear")
        s.raw(0x23); s.ptr(self.mask_key)                   # callnative kit_mask
        s.if_var(KS.VAR_RESULT, 1, "none", cond=5)
        s.closemessage(); s.fade(1); s.delay(30); s.fade(0)
        self.say(s, "k_grandpa_done", KS.GRANDPA_DONE); s.release(); s.end()
        s.here("none"); self.say(s, "k_grandpa_none", KS.GRANDPA_NO_OGERPON); s.release(); s.end()
        s.here("p2"); self.lines(s, "k_elders_p2_after", KS.ELDERS_P2_AFTER); s.release(); s.end()
        return "k_grandpa"

    # ---- people of the town by phase
    def phased(self, name, phases):
        s = self.P.new(name)
        s.lock(); s.faceplayer()
        self.phase(s, name, phases)
        return name

    def elder(self):
        return self.phased("k_elder", KS.ELDER_PHASES)

    def vendor(self, key, rom_items):
        P = self.P
        name = "k_" + key
        if key == "vendor_masks":
            return self.phased(name, KS.VENDOR_MASKS_PHASES)
        s = P.new(name)
        s.lock(); s.faceplayer()
        if key == "vendor_mochi":                           # after the story: the plush, and Briar's letter (Part 2)
            s.if_set(KS.F_P2_START, "open")
            s.if_set(KS.F_OGERPON, "hint")
        s.if_set(KS.F_PLAZA, "open")
        self.lines(s, name, KS.VENDORS[key]); s.release(); s.end()
        if key == "vendor_mochi":
            s.here("hint"); self.lines(s, "k_mochi_hint", KS.MOCHI_HINT)
        s.here("open")
        self.say(s, name + "_open", KS.VENDOR_OPEN[key])
        P.marts[key] = [rom_items[n] for n in KS.SHOPS[key]]
        s.pokemart(key)
        self.say(s, "k_vendor_bye", KS.VENDOR_BYE); s.release(); s.end()
        return name

    def caretaker(self):
        s = self.P.new("k_caretaker")
        s.lock(); s.faceplayer()
        s.if_set(KS.F_OGERPON, "after")
        s.if_set(KS.F_WAKE, "gone")
        s.if_set(KS.F_TRUTH, "morning")
        s.if_set(KS.F_PLAZA, "festival")
        s.if_set(KS.F_TASK, "remind")
        s.if_set(KS.F_CARMINE, "task")
        self.lines(s, "k_caretaker", KS.CARETAKER); s.release(); s.end()
        s.here("task"); self.lines(s, "k_caretaker_task", KS.CARETAKER_TASK); s.setflag(KS.F_TASK); s.release(); s.end()
        for label, key, lines in (("remind", "k_caretaker_remind", KS.CARETAKER_REMIND),
                                  ("festival", "k_caretaker_festival", KS.CARETAKER_FESTIVAL),
                                  ("morning", "k_caretaker_morning", KS.CARETAKER_MORNING),
                                  ("gone", "k_caretaker_gone", KS.CARETAKER_MASKS_GONE),
                                  ("after", "k_caretaker_after", KS.CARETAKER_AFTER)):
            s.here(label); self.lines(s, key, lines); s.release(); s.end()
        return "k_caretaker"

    # ---- Part 2: Mochi Mayhem
    def pecha_battle(self, s, ids):
        """Pecharunt's battle (no Poke Balls, no white-out); won, it is yours (givemon: the official catch is
        certain); no room, or not won: it stays where it is"""
        P, L = self.P, self.L
        sp = ids["Pecharunt"]
        self.say(s, "k_pecha_battle", KS.PECHA_BATTLE); s.closemessage()
        s.cry(sp)
        s.setflag(KS.FLAG_NO_BALLS); s.setflag(KS.FLAG_NO_WHITEOUT)
        s.wildbattle(sp, KS.P2_LEVEL); s.dowildbattle()
        s.clearflag(KS.FLAG_NO_BALLS); s.clearflag(KS.FLAG_NO_WHITEOUT)
        self.outcome(s); s.if_var(KS.VAR_RESULT, KS.B_WON, "pecha_lost", cond=5)
        self.lines(s, "k_pecha_weak", KS.PECHA_WEAK); s.closemessage()
        s.raw(0x79); s.h(sp); s.raw(KS.P2_LEVEL); s.h(0); s.raw(0, 0, 0, 0, 0, 0, 0, 0, 0)     # givemon
        s.if_var(KS.VAR_RESULT, 2, "pecha_noroom")
        s.playfanfare(KS.MUS_ITEM); self.say(s, "k_pecha_caught", KS.PECHA_CAUGHT); s.waitfanfare(); s.closemessage()
        s.setflag(KS.F_PECHARUNT)
        s.fade(1)
        for k in ("pecharunt", "nemona2"):
            s.removeobject(L[k])
        s.fade(0)
        self.lines(s, "k_p2_ending", KS.P2_ENDING); s.closemessage()
        s.fade(1)
        for k in ("kieran", "carmine"):
            s.removeobject(L[k])
        self.refresh_people(s)
        s.fade(0)
        s.release(); s.end()
        s.here("pecha_noroom"); self.lines(s, "k_pecha_noroom", KS.PECHA_NO_ROOM); s.release(); s.end()
        s.here("pecha_lost")
        s.if_var(KS.VAR_RESULT, KS.B_LOST, "pecha_stays", cond=5); s.heal()
        s.here("pecha_stays"); self.lines(s, "k_pecha_lost", KS.PECHA_LOST); s.release(); s.end()

    def wake(self, s, name, intro, woke):
        """someone under the mochi's spell, woken by talking (Part 2 has no battle but Nemona's and Pecharunt's)"""
        self.lines(s, name, intro); s.closemessage()
        self.say(s, "k_p2_snap", KS.P2_SNAP); s.closemessage()
        self.say(s, name + "_woke", woke)

    def villager_p2(self, key, phases, beat, intro, woke, after, other):
        """the farmer (Shige) and the mother (Aya): their phases, but in Part 2 woken from the mochi's spell once
        Kieran has told you; the second one woken sends Kieran to the Hall"""
        P, L = self.P, self.L
        name = "k_" + key
        s = P.new(name)
        s.lock(); s.faceplayer()
        s.if_set(KS.F_PECHARUNT, "normal")
        s.if_set(beat, "after")
        s.if_set(KS.F_P2_KIERAN, "fight")
        s.here("normal")
        self.phase(s, name, phases)
        s.here("after"); self.lines(s, name + "_p2_after", after); s.release(); s.end()
        s.here("fight")
        self.wake(s, name + "_p2", intro, woke)
        s.setflag(beat)
        self.lines(s, name + "_p2_after", after); s.closemessage()
        s.if_unset(other, "done")
        s.fade(1); s.removeobject(L["kieran"]); self.refresh_people(s); s.fade(0)
        s.here("done"); s.release(); s.end()
        return name

    def elders_p2(self):
        """Kieran's grandparents before Kitakami Hall (p14): woken, then home"""
        P, L = self.P, self.L
        s = P.new("k_elders_p2")
        s.lock(); s.faceplayer()
        self.wake(s, "k_elders_p2", KS.ELDERS_P2, KS.ELDERS_DEFEAT)
        self.lines(s, "k_elders_p2_after", KS.ELDERS_P2_AFTER); s.closemessage()
        s.setflag(KS.F_P2_ELDERS)
        s.fade(1)
        for k in ("grandpa2", "grandma2", "kieran"):
            s.removeobject(L[k])
        self.refresh_people(s)
        s.fade(0)
        s.release(); s.end()
        return "k_elders_p2"

    def friend_p2(self, key, wait, intro, woke, beat, other):
        """Arven and Penny: waiting with Kieran (p12-p14), under the mochi's spell in the market (p15): woken; the
        second one woken shows Pecharunt over the market, which flies to the plaza (p16)"""
        P, L = self.P, self.L
        name = "k_%s_p2" % key
        s = P.new(name)
        s.lock(); s.faceplayer()
        s.if_set(beat, "after")
        s.if_set(KS.F_P2_ELDERS, "fight")
        self.lines(s, name + "_wait", wait); s.release(); s.end()
        s.here("after"); self.lines(s, name + "_after", KS.FRIEND_P2_AFTER[key]); s.release(); s.end()
        s.here("fight")
        self.wake(s, name, intro, woke); s.closemessage()
        s.setflag(beat)
        s.if_unset(other, "one")
        x, y = P2_PECHA_MARKET
        self.place(s, L["pecharunt"], x, y, "down")
        s.clearflag(KS.H_P2_PECHA); s.addobject(L["pecharunt"])
        s.cry(self.ids["Pecharunt"])
        self.lines(s, "k_pecha_flees", KS.PECHA_FLEES); s.closemessage()
        s.fade(1)
        for k in ("pecharunt", "arven2", "penny2", "kieran", "carmine"):
            s.removeobject(L[k])
        self.refresh_people(s)
        s.fade(0)
        s.release(); s.end()
        s.here("one"); self.lines(s, name + "_after", KS.FRIEND_P2_AFTER[key]); s.release(); s.end()
        return name

    def nemona_p2(self, trainer, ids):
        """Nemona: eager in the market (p12); at Loyalty Plaza with Pecharunt (p16): her battle, then Pecharunt's"""
        P = self.P
        s = P.new("k_nemona_p2")
        s.lock(); s.faceplayer()
        s.if_set(KS.F_P2_ARVEN, "plaza")
        self.lines(s, "k_nemona_p2_wait", KS.NEMONA_P2_WAIT); s.release(); s.end()
        s.here("plaza")
        s.if_set(KS.F_P2_NEMONA, "pecha")
        self.lines(s, "k_nemona_p2", KS.NEMONA_P2); s.closemessage()
        self.tbattle(s, trainer, "k_nemona_p2_defeat", KS.NEMONA_P2_DEFEAT)
        self.outcome(s); s.if_var(KS.VAR_RESULT, KS.B_WON, "lost", cond=5)
        s.setflag(KS.F_P2_NEMONA)
        s.here("pecha")
        self.pecha_battle(s, ids)
        s.here("lost"); s.heal(); s.release(); s.end()
        return "k_nemona_p2"

    def pecharunt_p2(self, ids):
        """Pecharunt at the plaza: behind Nemona until she is beaten; then its battle (again, if not won)"""
        P = self.P
        s = P.new("k_pecharunt")
        s.lock()
        s.if_set(KS.F_P2_NEMONA, "battle")
        self.lines(s, "k_pecha_still", KS.PECHA_STILL); s.release(); s.end()
        s.here("battle")
        self.pecha_battle(s, ids)
        return "k_pecharunt"

    def plaque(self, k, name):
        """a plaque under a mask's case in the Mask Hall: the mask; from the morning the Loyal Three wake, the case
        smashed; after the story, returned to Ogerpon"""
        P = self.P
        key = "k_plaque_%d" % k
        s = P.new(key)
        s.lockall()
        s.if_set(KS.F_OGERPON, "after")
        s.if_set(KS.F_WAKE, "smashed")
        P.sign_all(s, key, KS.PLAQUES[name]); s.releaseall(); s.end()
        s.here("smashed"); P.sign_all(s, "k_plaque_smashed", KS.PLAQUE_SMASHED); s.releaseall(); s.end()
        s.here("after"); P.sign_all(s, "k_plaque_after", KS.PLAQUE_AFTER); s.releaseall(); s.end()
        return key

    def home_carmine(self):
        s = self.P.new("k_home_carmine")
        s.lock(); s.faceplayer()
        s.if_set(KS.F_OGERPON, "after")
        self.lines(s, "k_home_carmine_A", KS.CARMINE_HOME["A"]); s.release(); s.end()
        s.here("after"); self.lines(s, "k_home_carmine_D", KS.CARMINE_HOME["D"]); s.release(); s.end()
        return "k_home_carmine"

    def before_after(self, name, before, after):
        s = self.P.new(name)
        s.lock(); s.faceplayer()
        s.if_set(KS.F_OGERPON, "after")
        self.lines(s, name + "_A", before); s.release(); s.end()
        s.here("after"); self.lines(s, name + "_D", after); s.release(); s.end()
        return name

    def nothing(self):
        s = self.P.new("k_nothing"); s.end()
        return "k_nothing"
