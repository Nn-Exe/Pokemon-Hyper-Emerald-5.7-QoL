"""Kitakami's people, the way in, and the story's wiring (2026-10-16). What they say and the flags: kstory.py. The
story's scripts: kchapters.py. Sprites: ksprites.py. Trainers: ktrainers.py. Code: kasm.py.

  * Mossui Town: Briar at the bus stop, Carmine and Kieran (where the story puts them: kchapters.POS), the elder
    at Loyalty Plaza before the Loyal Three's stone statues, the festival's organiser at the market gate, a vendor
    in each of the four stalls (in the gap of its goods row, as Slateport's vendors stand: kworld.market; shops
    from the festival on), six villagers; Ogerpon and the Loyal Three alive when the story shows them. Seven signs
    (the four town signs and the legend's three boards, read with Kieran in chapter 2).
  * The insides: the caretaker in Kitakami Hall, the Mask Hall (the trip's task), Grandpa (the true story; Ogerpon's
    masks after the story) and Carmine in the family house, the old woman, the old couple. (The Pokemon Center's
    nurse is kinteriors.py's. The hotel floors and your room's bed went on 2026-10-17: the Hall is one floor.)
  * Every position is the placements file's (kplaces.py: kplaces.apply sets TOWN, SIGN_AT, ROOM_PEOPLE, ARRIVE and
    kchapters' before make()); the values below are the build's own when no file is named.
  * Mossdeep City: Briar beside the hole once Area Zero's ending is over (Jacq's tile: he has gone back in by then),
    who takes you to the bus stop in Mossui; in Mossui she takes you back. Mossdeep's people and map scripts are Area
    Zero's (paldea), copied with her added: our ON_TRANSITION and ON_RESUME work out whether she is there, then go
    on to Area Zero's, which go on to Mossdeep's own.
  * Saves made on an older build hold the old copy of a map's people. Area Zero's answer is a stamp (var 0x40F9):
    a map's ON_TRANSITION writes the build's stamp, its ON_RESUME compares it, and on a mismatch its ON_FRAME
    warps you onto the tile you stand on, which reads the map again. Kitakami's maps do the same with a stamp of
    their own, and Area Zero's stamp in its scripts (30 places) becomes ours too, so that a save made in Mossdeep
    before Briar existed gets her. Mossui's and the family house's ON_TRANSITION / ON_RESUME also work out who
    stands where for the story's stage (kchapters.state_*).
"""
import struct, zlib
import kstory as KS
import ksprites as KSP
import kchapters as KC
import khall as KH

MOSSDEEP = (0, 6)
MOSSDEEP_HEADER = 0x00482560
AZ_OBJS = 34                                   # Mossdeep's 29 and Area Zero's five (Jacq 30, the hole 31, ...)
JACQ = (30, (70, 32), 0x43D4)                  # local, tile, hide flag: Jacq by the hole until the ending is over
BRIAR_LOCAL = 35
BRIAR_MOSSDEEP_BACK = (70, 33)                 # where her bus brings you back: below her, in front of the hole's
                                               # strip (the ending's students stand there only during the ending)
AZ_SCRIPTS = (0x01FBC400, 0x01FD2A00)          # Area Zero's blob (paldea FREE): its stamp is written in there
MT = {"down": 0x08, "up": 0x07, "left": 0x09, "right": 0x0A}
VAR_X, VAR_Y = 0x8004, 0x8005
MUS_HEAL = 368                                 # the healing fanfare (paldea_patch.py)
RESUME_PAUSED_WEATHER = 0x080AEE84             # vanilla's: GetSavedWeather, then SetCurrentAndNextWeather (no change)
RESUME_PAUSED_WEATHER_WAS = "30b5fff791ff0006040e0f2c0ed10548faf7a6f9"
STAMP_SALT = 2                                 # one more whenever who stands where changes without the stamp's
                                               # inputs (below) changing

ARRIVE = (23, 46)                              # the bus stop: where Briar's bus leaves you
# Mossui Town: key -> (x, y, facing). Vendors stand in the gap of their stall's goods row (kworld.market), the
# statues on the plaza. Carmine and Kieran's places here are stage 0's (kchapters.POS moves them).
TOWN = {
    "briar": (22, 46, "right"), "carmine": (24, 45, "down"), "kieran": (20, 30, "down"),
    "elder": (35, 11, "up"),
    "okidogi": (33, 9, "down"), "munkidori": (35, 9, "down"), "fezandipiti": (37, 9, "down"),
    "organiser": (22, 35, "down"),
    "vendor_apples": (19, 39, "down"), "vendor_masks": (28, 39, "down"),     # in their stalls' gaps
    "vendor_mochi": (19, 44, "down"), "vendor_rice": (28, 44, "down"),
    "farmer": (14, 35, "left"), "mother": (33, 33, "right"), "child": (34, 33, "left"),
    "lanterns": (21, 7, "right"), "hiker": (19, 7, "right"), "carver": (10, 32, "down"),
}
VENDORS = ("vendor_apples", "vendor_masks", "vendor_mochi", "vendor_rice")
STATUE_KEYS = ("okidogi", "munkidori", "fezandipiti")
SIGN_AT = {"sign_hall": (16, 24), "sign_shrine": (31, 24), "sign_pond": (28, 13), "sign_bus": (25, 46)}
ROOM_PEOPLE = {                                # room -> [(key, x, y, facing)]
    "hall": [("caretaker", 7, 7, "down")],     # in the Mask Hall, before its stage
    "family": [("grandpa", 6, 2, "down"), ("home_carmine",) + KC.FAMILY_CARMINE],
    "home1": [("old_woman", 6, 3, "down")],
    "home2": [("old_man2", 2, 3, "down"), ("old_woman2", 6, 3, "down")],   # where Lavaridge's couple stand
}
FLAG_OF = {"carmine": KS.H_CARMINE, "kieran": KS.H_KIERAN, "elder": KS.H_ELDER,
           "okidogi": KS.H_STATUES, "munkidori": KS.H_STATUES, "fezandipiti": KS.H_STATUES}


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def az_stamp(rom):
    """Area Zero's stamp and where its scripts write (setvar 0x40F9) and compare it: (stamp, [offsets])."""
    lo, hi = AZ_SCRIPTS
    sets, cmps = [], []
    seen = set()
    b = bytes(rom[lo:hi])
    k = 0
    while True:
        k = b.find(b"\xF9\x40", k + 1)
        if k < 1:
            break
        op = b[k - 1]
        if op in (0x16, 0x21):
            v = struct.unpack_from("<H", b, k + 2)[0]
            if op == 0x16 and v == 0:
                continue                        # setvar 0x40F9, 0: a refresh asked for
            seen.add(v)
            (sets if op == 0x16 else cmps).append(lo + k + 2)
    assert len(seen) == 1 and sets and cmps, "Area Zero's stamp is not one value in its scripts: %s" % sorted(seen)
    return seen.pop(), sets + cmps


class People:
    def __init__(self, rom, enc_box):
        self.rom, self.box = rom, enc_box
        self.scripts, self.texts, self.moves, self.marts = [], {}, {}, {}

    def text(self, key, s):
        if key not in self.texts:
            self.texts[key] = self.box(self.rom, s)
        return ("text", key)

    def new(self, name):
        from lib import Script
        s = Script(name)
        self.scripts.append(s)
        return s

    def say_all(self, s, prefix, lines):
        for k, line in enumerate(lines):
            s.raw(0x0F, 0x00); s.ptr(self.text("%s_%d" % (prefix, k), line)); s.raw(0x09, 0x04)

    def sign_all(self, s, prefix, lines):
        for k, line in enumerate(lines):
            s.raw(0x0F, 0x00); s.ptr(self.text("%s_%d" % (prefix, k), line)); s.raw(0x09, 0x03)

    def ask(self, s, key, line):
        s.raw(0x0F, 0x00); s.ptr(self.text(key, line)); s.raw(0x09, 0x05)

    def talk(self, name, lines):
        s = self.new(name)
        s.lock(); s.faceplayer(); self.say_all(s, name, lines); s.release(); s.end()
        return name

    def look(self, name, lines):
        """a thing that does not turn to you (a statue)"""
        s = self.new(name)
        s.lockall(); self.say_all(s, name, lines); s.releaseall(); s.end()
        return name

    def sign(self, name, lines):
        s = self.new(name)
        s.lockall(); self.sign_all(s, name, lines); s.releaseall(); s.end()
        return name


def elevation(blocks, x, y):
    z = blocks[y][x] >> 12
    return 3 if z in (0, 1, 15) else z


def stamp_of(az, legend_signs):
    sig = repr((az, STAMP_SALT, sorted(TOWN.items()), sorted(ROOM_PEOPLE.items()), sorted(SIGN_AT.items()),
                sorted(KC.P2POS.items()), KC.P2_PECHA_MARKET,
                legend_signs, ARRIVE, BRIAR_MOSSDEEP_BACK, KS.F_BRIAR_HIDE, sorted(KC.STORY_OBJECTS.items()),
                sorted(KC.POS.items()), KC.KIERAN_RUNS_IN, KC.CARMINE_RUNS_IN, KC.EVENING_AT))
    s = zlib.crc32(sig.encode()) & 0xFFFF
    return s if s not in (0, az) else (s ^ 0x5A5A) or 1


def check(rom):
    """Mossdeep is as Area Zero left it."""
    h = MOSSDEEP_HEADER
    ev = u32(rom, h + 4) - 0x08000000
    assert rom[ev] == AZ_OBJS, "Mossdeep has %d people, not Area Zero's %d" % (rom[ev], AZ_OBJS)
    objs = u32(rom, ev + 4) - 0x08000000
    locals_ = sorted(rom[objs + 24 * k] for k in range(AZ_OBJS))
    assert locals_ == list(range(1, AZ_OBJS + 1)), "Mossdeep's people are not numbered 1-%d" % AZ_OBJS
    local, xy, flag = JACQ
    o = objs + 24 * (local - 1)
    assert rom[o] == local and struct.unpack_from("<hh", rom, o + 4) == xy and u16(rom, o + 20) == flag, \
        "Jacq is not at %d, %d in Mossdeep, where Kitakami's Briar takes his place after Area Zero's ending: put him " \
        "back there in Area Zero's placements.txt" % xy
    ms = u32(rom, h + 8) - 0x08000000
    kinds = []
    while rom[ms + 5 * len(kinds)]:
        kinds.append(rom[ms + 5 * len(kinds)])
    assert sorted(kinds) == [2, 3, 5], "Mossdeep's map scripts are not Area Zero's three (%s)" % kinds
    az_stamp(rom)


def make(rom, blob, M, mossui, rooms, marks, town_blocks, numbers, legend_signs, enc_box, ids, trainer_ids,
         mask_code):
    """Objects, signs and map scripts onto the Kitakami maps (before maps.install), scripts and texts and Mossdeep's
    new events into `blob`. ids: species and items by name ("item:<name>"); trainer_ids: key -> trainer row;
    mask_code: kasm.mask_code. -> a function to call on the ROM after the blob is written (Mossdeep's header, the
    stamp in Area Zero's scripts, the sprite entries) and the People."""
    P = People(rom, enc_box)
    assert bytes(rom[RESUME_PAUSED_WEATHER - 0x08000000:RESUME_PAUSED_WEATHER - 0x08000000 + 20]).hex() ==         RESUME_PAUSED_WEATHER_WAS, "ResumePausedWeather (0x080AEE84) is not what it was"
    az, sites = az_stamp(rom)
    stamp = stamp_of(az, legend_signs)
    ARR = ARRIVE
    # kit_mask in the blob (position-independent Thumb); callnative takes its address + 1
    pm = blob.put(("kmask",), mask_code(0x08000000))
    blob.addr[("kmask_thumb",)] = pm + 1
    C = KC.Chapters(P, rom, ids, numbers, ("kmask_thumb",))

    # ---------------------------------------------------------------- Mossui's people and the story's objects
    local = 0
    for key in TOWN:
        local += 1
        KC.MOSSUI_LOCALS[key] = local
    for key in KC.STORY_OBJECTS:
        local += 1
        KC.MOSSUI_LOCALS[key] = local
    s = P.new("k_briar_town")
    s.lock(); s.faceplayer()
    s.if_set(KS.F_P2_START, "back")                         # Part 2: Kieran's letter, once the story is over
    s.if_unset(KS.F_OGERPON, "back")
    P.say_all(s, "k_briar_letter", KS.BRIAR_LETTER)
    P.say_all(s, "k_briar_p2_here", KS.BRIAR_P2_HERE)
    s.closemessage()
    s.fade(1)
    s.setflag(KS.F_P2_START)
    s.call(("script", "k_state_mossui"))
    for k in ("kieran", "carmine", "arven2", "nemona2", "penny2"):
        s.addobject(KC.MOSSUI_LOCALS[k])
    s.fade(0)
    s.release(); s.end()
    s.here("back")
    P.ask(s, "k_briar_back_ask", KS.BRIAR_BACK_ASK); s.if_yes("go")
    s.raw(0x0F, 0x00); s.ptr(P.text("k_briar_back_no", KS.BRIAR_BACK_NO)); s.raw(0x09, 0x04)
    s.release(); s.end()
    s.here("go")
    s.raw(0x0F, 0x00); s.ptr(P.text("k_briar_back_yes", KS.BRIAR_BACK_YES)); s.raw(0x09, 0x04)
    s.closemessage(); s.warp(*MOSSDEEP, *BRIAR_MOSSDEEP_BACK); s.end()

    scripts = {"briar": "k_briar_town", "carmine": C.carmine(trainer_ids), "kieran": C.kieran(trainer_ids),
               "elder": C.elder(), "organiser": C.phased("k_organiser", KS.ORGANISER_PHASES)}
    for k in STATUE_KEYS:
        scripts[k] = P.look("k_statue_" + k, KS.STATUES[k])
    for k in VENDORS:
        scripts[k] = C.vendor(k, {n: ids["item:" + n] for n in sum(KS.SHOPS.values(), [])})
    for k in KS.VILLAGER_PHASES:
        scripts[k] = C.phased("k_" + k, KS.VILLAGER_PHASES[k]) if k not in ("farmer", "mother") else None
    scripts["farmer"] = C.villager_p2("farmer", KS.VILLAGER_PHASES["farmer"], KS.F_P2_SHIGE, KS.SHIGE_P2,
                                      KS.SHIGE_DEFEAT, KS.SHIGE_P2_AFTER, KS.F_P2_AYA)
    scripts["mother"] = C.villager_p2("mother", KS.VILLAGER_PHASES["mother"], KS.F_P2_AYA, KS.AYA_P2,
                                      KS.AYA_DEFEAT, KS.AYA_P2_AFTER, KS.F_P2_SHIGE)
    for key, (x, y, face) in TOWN.items():
        if key in ("briar", "carmine", "kieran"):
            obj = M.Obj(KC.MOSSUI_LOCALS[key], x, y, scripts[key], gfx=KS.EXT, ext=KSP.slot(key), face=face,
                        flag=FLAG_OF.get(key, 0), elevation=elevation(town_blocks, x, y))
        elif key in STATUE_KEYS:
            obj = M.Obj(KC.MOSSUI_LOCALS[key], x, y, scripts[key], gfx=KS.EXT, ext=KSP.slot(key), face=face,
                        flag=FLAG_OF[key], elevation=elevation(town_blocks, x, y))
        else:
            obj = M.Obj(KC.MOSSUI_LOCALS[key], x, y, scripts[key], gfx=KS.GFX[key], face=face,
                        flag=FLAG_OF.get(key, 0), elevation=elevation(town_blocks, x, y))
        mossui.objs.append(obj)
    story_scripts = {"ogerpon": C.ogerpon(trainer_ids), "ogerpon_fest": C.nothing()}
    for k in KC.L3:
        story_scripts["live_" + k] = C.loyal(k)
        story_scripts["wake_" + k] = "k_nothing"
    story_scripts.update({
        "arven2": C.friend_p2("arven", KS.ARVEN_P2_WAIT, KS.ARVEN_P2, KS.ARVEN_DEFEAT, KS.F_P2_ARVEN, KS.F_P2_PENNY),
        "penny2": C.friend_p2("penny", KS.PENNY_P2_WAIT, KS.PENNY_P2, KS.PENNY_DEFEAT, KS.F_P2_PENNY, KS.F_P2_ARVEN),
        "nemona2": C.nemona_p2(trainer_ids["nemona2"], ids), "pecharunt": C.pecharunt_p2(ids)})
    story_scripts["grandpa2"] = story_scripts["grandma2"] = C.elders_p2()
    for key, (sprite, x, y, face, flag) in KC.STORY_OBJECTS.items():
        gfx, ext = (sprite, 0) if isinstance(sprite, int) else (KS.EXT, KSP.slot(sprite))
        mossui.objs.append(M.Obj(KC.MOSSUI_LOCALS[key], x, y, story_scripts[key], gfx=gfx, ext=ext,
                                 face=face, flag=flag, elevation=elevation(town_blocks, x, y)))
    signs = dict(SIGN_AT)
    for k, xy in enumerate(legend_signs):
        signs["legend_%d" % (k + 1)] = xy
    for key, (x, y) in signs.items():
        if key.startswith("legend_"):
            mossui.bg(x, y, C.board(int(key[-1]) - 1, KS.SIGNS[key]))
        else:
            mossui.bg(x, y, P.sign("k_" + key, KS.SIGNS[key]))
    # Carmine sees you one step up from where Briar's bus leaves you (KC.carmine_spots)
    spot = (ARR[0], ARR[1] - 1)
    mossui.coord(spot[0], spot[1], KC.VAR_SPOT, 0, C.carmine_spots(spot))

    # ---------------------------------------------------------------- the insides
    room_scripts = {"caretaker": C.caretaker(), "grandpa": C.grandpa(), "home_carmine": C.home_carmine(),
                    "old_woman": C.before_after("k_old_woman", KS.OLD_WOMAN, KS.OLD_WOMAN_AFTER),
                    "old_man2": C.before_after("k_old_man2", KS.OLD_MAN2, KS.OLD_COUPLE_AFTER),
                    "old_woman2": C.before_after("k_old_woman2", KS.OLD_WOMAN2, KS.OLD_COUPLE_AFTER)}
    for room, people in ROOM_PEOPLE.items():
        m = rooms[room]
        for (key, x, y, face) in people:
            if key == "home_carmine":
                obj = M.Obj(len(m.objs) + 1, x, y, room_scripts[key], gfx=KS.EXT, ext=KSP.slot("carmine"),
                            face=face, flag=KS.H_HOME_CARMINE, elevation=elevation(m.blocks, x, y))
            else:
                obj = M.Obj(len(m.objs) + 1, x, y, room_scripts[key], gfx=KS.GFX[key], face=face,
                            flag=KS.H_P2_HOME if key == "grandpa" else 0, elevation=elevation(m.blocks, x, y))
            m.objs.append(obj)

    # the Mask Hall: the plaques under the cases; the cases smashed from the morning the Loyal Three wake
    hall = rooms["hall"]
    for k, ((x, y), name) in enumerate(zip(KH.PLAQUES, KH.MASK_NAMES)):
        hall.bg(x, y, C.plaque(k, name))
    s = P.new("k_load_hall")
    s.if_unset(KS.F_WAKE, "whole")
    for (x, y, block) in hall.swaps:
        s.setmetatile(x, y, block)
    s.here("whole"); s.end()
    hall.on_load = "k_load_hall"

    # ---------------------------------------------------------------- every Kitakami map: the stamp (and the stage)
    state = {"mossui": C.state_mossui(), "family": C.state_family()}
    for m in [mossui] + list(rooms.values()):
        g, n = numbers[m.key]
        s = P.new("k_tr_" + m.key)
        if m.key in state:
            s.call(("script", state[m.key]))
        s.setvar(KS.FRESH, stamp); s.end()
        s = P.new("k_res_" + m.key)
        if m.key == "mossui":
            # The hack carries a battle's weather onto the map when it ends (0x09D494AC, called at 0x09D49690; its own
            # ROM does it too: sun -> Drought 0x0C, rain, sand, hail). Mossui has none of its own (its evening and
            # night are palettes), so the map's is put back as the field comes back (2026-10-20, the user: Carmine's
            # Ninetales with Drought left "the overworld sunlight ... affect first impression of the town map").
            # resetweather (0xA3) sets the saved weather to the map's; then ResumePausedWeather, which the field has
            # just run with the battle's, again: the weather is set outright before the weather task first draws it.
            # Not doweather (0xA5): that starts a change while the field fades in from the battle, and the fade
            # never ends - the town stayed black behind Kieran's lines (the user's screenshot, 2026-10-20).
            s.raw(0xA3); s.callnative(RESUME_PAUSED_WEATHER | 1)
        if m.key == "pc":
            # what every Pokemon Center's ON_RESUME does (CableClub_OnResume 0x08277C30: special InitUnionRoom): the
            # nurse reads the Union Room name buffer after healing (special 0x01A5); left as it was, it held junk and
            # she said "It appears as if <junk> is playing right now" - Chinese and spaces, or a crash (2026-10-17)
            s.special(0x01A4)
        if m.key in state:
            s.call(("script", state[m.key]))
        s.compare(KS.FRESH, stamp); s.goto_if(1, "ok"); s.setvar(KS.FRESH, 0); s.here("ok"); s.end()
        s = P.new("k_ref_" + m.key)
        s.lockall(); s.setvar(KS.FRESH, stamp)
        s.getplayerxy(VAR_X, VAR_Y); s.warpsilent(g, n, VAR_X, VAR_Y); s.raw(0x27)
        s.releaseall(); s.end()
        assert m.on_transition is None and m.on_resume is None and not m.on_frame, m.key
        m.on_transition, m.on_resume = "k_tr_" + m.key, "k_res_" + m.key
        m.on_frame = [(KS.FRESH, 0, "k_ref_" + m.key)]

    # ---------------------------------------------------------------- Mossdeep: Briar, the way in
    g, n = numbers["mossui"]
    s = P.new("k_briar_mossdeep")
    s.lock(); s.faceplayer()
    s.if_set(KS.F_P2_START, "again")                        # Part 2: Kieran's letter, once the story is over
    s.if_unset(KS.F_OGERPON, "first")
    P.say_all(s, "k_briar_letter", KS.BRIAR_LETTER)
    P.ask(s, "k_briar_p2_ask", KS.BRIAR_P2_ASK); s.if_yes("p2_go")
    s.raw(0x0F, 0x00); s.ptr(P.text("k_briar_no", KS.BRIAR_NO)); s.raw(0x09, 0x04)
    s.release(); s.end()
    s.here("p2_go")
    s.setflag(KS.F_P2_START)
    s.goto("go")
    s.here("first")
    s.if_set(KS.F_MET_BRIAR, "again")
    P.say_all(s, "k_briar_intro", KS.BRIAR_INTRO)
    s.setflag(KS.F_MET_BRIAR)
    P.ask(s, "k_briar_ask", KS.BRIAR_ASK); s.goto("answer")
    s.here("again")
    P.ask(s, "k_briar_ask_again", KS.BRIAR_ASK_AGAIN)
    s.here("answer")
    s.if_yes("go")
    s.raw(0x0F, 0x00); s.ptr(P.text("k_briar_no", KS.BRIAR_NO)); s.raw(0x09, 0x04)
    s.release(); s.end()
    s.here("go")
    s.raw(0x0F, 0x00); s.ptr(P.text("k_briar_yes", KS.BRIAR_YES)); s.raw(0x09, 0x04)
    s.closemessage(); s.warp(g, n, *ARR); s.end()

    h = MOSSDEEP_HEADER
    ev = u32(rom, h + 4) - 0x08000000
    objs = u32(rom, ev + 4) - 0x08000000
    ms = u32(rom, h + 8) - 0x08000000
    entries = {rom[ms + 5 * k]: u32(rom, ms + 5 * k + 1) for k in range(3)}
    s = P.new("k_md_state")                     # Briar: there once Area Zero's ending is over
    s.setflag(KS.F_BRIAR_HIDE)
    s.if_var(KS.AZ_STAGE, KS.AZ_DONE, "show"); s.ret()
    s.here("show"); s.clearflag(KS.F_BRIAR_HIDE); s.ret()
    s = P.new("k_md_transition"); s.call(("script", "k_md_state")); s.goto(entries[3])
    s = P.new("k_md_resume"); s.call(("script", "k_md_state")); s.goto(entries[5])
    jl, jxy, jflag = JACQ
    jacq = objs + 24 * (jl - 1)
    briar = struct.pack("<BBBBhhBBBBHHIHH", BRIAR_LOCAL, KS.EXT, 0, KSP.slot("briar"), jxy[0], jxy[1], rom[jacq + 8],
                        MT["left"], 0, 0, 0, 0, 0, KS.F_BRIAR_HIDE, 0)
    po = blob.put(("k_md", "objs"), bytes(rom[objs:objs + 24 * AZ_OBJS]) + briar)
    blob.ref(("script", "k_briar_mossdeep"), po - blob.base + 24 * AZ_OBJS + 16)
    pe = blob.put(("k_md", "events"), bytes([AZ_OBJS + 1]) + bytes(rom[ev + 1:ev + 4]) + struct.pack("<I", 0) +
                  bytes(rom[ev + 8:ev + 20]))
    blob.ref(("k_md", "objs"), pe - blob.base + 4)
    pmap = blob.put(("k_md", "mapscripts"), struct.pack("<BIBIBI", 3, 0, 2, entries[2], 5, 0) + b"\0", 1)
    blob.ref(("script", "k_md_transition"), pmap - blob.base + 1)
    blob.ref(("script", "k_md_resume"), pmap - blob.base + 11)

    # ---------------------------------------------------------------- into the blob
    from lib import moves as movebytes
    KSP.put(rom, blob)
    for key, b in P.texts.items():
        blob.put(("text", key), b, 1)
    for key, spec in P.moves.items():
        blob.put(("move", key), movebytes(spec), 1)
    for key, items in P.marts.items():
        blob.put(("mart", key), b"".join(struct.pack("<H", i) for i in items) + b"\0\0", 2)
    for s in P.scripts:
        blob.put_script(s)

    def finish(rom):
        struct.pack_into("<II", rom, h + 4, blob.addr[("k_md", "events")], blob.addr[("k_md", "mapscripts")])
        for o in sites:
            struct.pack_into("<H", rom, o, stamp)
        KSP.install(rom, blob)
        return stamp, az, len(sites)
    return finish, P


NAMES = {"briar": "Briar", "carmine": "Carmine", "kieran": "Kieran", "elder": "the elder", "organiser": "the organiser",
         "vendor_apples": "the apple stall vendor", "vendor_masks": "the mask stall vendor",
         "vendor_mochi": "the mochi stall vendor", "vendor_rice": "the rice ball stall vendor",
         "farmer": "the apple farmer", "mother": "the mother", "child": "the child", "lanterns": "the lantern maker",
         "hiker": "the hiker", "carver": "the mask carver", "okidogi": "the statue of Okidogi",
         "munkidori": "the statue of Munkidori", "fezandipiti": "the statue of Fezandipiti", "ogerpon": "Ogerpon",
         "ogerpon_fest": "Ogerpon", "live_okidogi": "Okidogi", "live_munkidori": "Munkidori",
         "live_fezandipiti": "Fezandipiti", "wake_okidogi": "Okidogi", "wake_munkidori": "Munkidori",
         "wake_fezandipiti": "Fezandipiti", "caretaker": "the caretaker", "grandpa": "Grandpa",
         "home_carmine": "Carmine", "old_woman": "the old woman", "old_man2": "the old man",
         "old_woman2": "the old woman", "arven2": "Arven", "penny2": "Penny", "nemona2": "Nemona",
         "pecharunt": "Pecharunt", "grandpa2": "Grandpa", "grandma2": "Grandma"}
STEP = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def walk_tiles(start, steps):
    """the tiles a scripted walk passes, in order: steps = ((direction, n), ...)"""
    x, y = start
    out = []
    for d, n in steps:
        dx, dy = STEP[d]
        for _ in range(n):
            x, y = x + dx, y + dy
            out.append((x, y))
    return out


def layout_report(rom, mossui, rooms, town_blocks, W, marks, legend_signs):
    """What the people do to the town, at every stage of the story and in its scenes: every tile reachable before
    is reachable with that stage's people standing (but their own), everyone stands on ground you can walk to (a
    vendor in the gap of a stall), nobody on another's tile, everyone can be talked to and every sign read, nobody
    stands in or before a doorway or on a sign, at most six palettes on one screen; the scenes' walks (Kieran and
    Carmine running in, Ogerpon at the festival) go over open ground nobody stands on; the bus stop and where
    evening finds you are ground you can walk to; no sign or signboard's roof on a doorway. In the rooms: everyone
    on a floor tile you can walk to, off the mats, with a tile beside them to talk from. Since 2026-10-17 the
    positions are the placements file's (kplaces.py), so these are what the editor's "Check" says."""
    problems = []
    b = town_blocks
    hh, ww = len(b), len(b[0])
    name = lambda k: NAMES.get(k, k)
    on_map = lambda x, y: 0 <= x < ww and 0 <= y < hh
    doors = {(x, y) for (x, y, *_) in mossui.warps}
    signs = {(bx, by) for (bx, by, *_) in mossui.bgs}
    every = list(TOWN.values()) + [v[1:3] for v in KC.STORY_OBJECTS.values()] + \
        [v[:2] for st in KC.POS.values() for v in st.values()] + list(signs) + list(legend_signs) + \
        [v[:2] for st in KC.P2POS.values() for v in st.values()] + \
        [ARRIVE, KC.EVENING_AT, KC.KIERAN_RUNS_IN, KC.CARMINE_RUNS_IN, KC.P2_PECHA_MARKET]
    for v in every:
        x, y = v[:2]
        if not on_map(x, y):
            problems.append("%d,%d is off the map (Mossui is %d x %d: x 0-%d, y 0-%d)" % (x, y, ww, hh, ww - 1, hh - 1))
    if problems:
        return problems, 0
    before = W.reach(b, ARRIVE)
    if len(before) < 100:
        problems.append("where Briar's bus leaves you (%d,%d) is not ground you can walk from" % tuple(ARRIVE))
        return problems, 0
    gaps = set(map(tuple, marks.get("vendors", [])))
    for (bx, by) in signs:
        if (bx, by) in doors or (bx, by - 1) in doors:
            problems.append("a sign at %d,%d stands in a doorway or right in front of one" % (bx, by))
    for k, (x, y) in enumerate(legend_signs):
        if y < 1 or (x, y - 1) in doors:
            problems.append("signboard %d at %d,%d: its roof (the tile above) would be on a door" % (k + 1, x, y))
    if len(signs) < len(SIGN_AT) + len(legend_signs):
        problems.append("two signs are on one tile")
    if tuple(KC.EVENING_AT) not in before:
        problems.append("where evening finds you (%d,%d) is not ground you can walk to" % tuple(KC.EVENING_AT))
    by_key = {k: o for k, o in zip(list(TOWN) + list(KC.STORY_OBJECTS), mossui.objs)}
    fixed = [k for k in TOWN if k not in ("carmine", "kieran")]
    statues_until = 9
    scenes = []
    for st in range(18):
        beaten_sets = [()] if st != 9 else [(), ("okidogi",), ("okidogi", "munkidori")]
        for beaten in beaten_sets:
            keys = {k: (by_key[k].x, by_key[k].y) for k in fixed
                    if not (k in STATUE_KEYS and st >= statues_until)}
            keys.update(KC.visible(st, beaten=beaten))
            scenes.append(("stage %d%s" % (st, " beaten %s" % (beaten,) if beaten else ""), keys, None))
    # the scenes' moments with the most people: the wake (statues alive, Ogerpon, Carmine run in), the festival
    cx, cy = KC.CARMINE_RUNS_IN
    wake = {k: (by_key[k].x, by_key[k].y) for k in fixed if k not in STATUE_KEYS and k != "elder"}
    wake.update({"kieran": tuple(KC.POS[8]["kieran"][:2]), "carmine": (cx, cy - 4),
                 "ogerpon": tuple(KC.STORY_OBJECTS["ogerpon"][1:3])})
    wake.update({"wake_" + k: tuple(KC.STORY_OBJECTS["wake_" + k][1:3]) for k in KC.L3})
    kx, ky = wake["kieran"]
    scenes.append(("the wake scene", wake, [(kx + dx, ky + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]))
    ox, oy = KC.STORY_OBJECTS["ogerpon_fest"][1:3]
    fest = {k: (by_key[k].x, by_key[k].y) for k in fixed}
    fest.update({"carmine": tuple(KC.POS[6]["carmine"][:2]), "ogerpon_fest": (ox, oy - 4)})
    fx, fy = fest["carmine"]
    scenes.append(("the festival scene", fest, [(fx + dx, fy + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]))
    # the walks: (what, its start, the tiles it passes, the people there then, the one walking)
    stage0 = {k: (by_key[k].x, by_key[k].y) for k in fixed}
    stage0.update(KC.visible(0))
    st6 = {k: (by_key[k].x, by_key[k].y) for k in fixed}
    st6.update(KC.visible(6))
    # Carmine sees you one step up from where Briar's bus leaves you (KC.carmine_spots): she stands next to that tile,
    # and it is the only way on from the bus stop (else she could be walked past)
    spot = (ARRIVE[0], ARRIVE[1] - 1)
    cx, cy = KC.POS[0]["carmine"][:2]
    if spot not in before:
        problems.append("one step up from where Briar's bus leaves you (%d,%d) is not ground you can walk to: Carmine "
                        "stops you there" % spot)
    elif abs(cx - spot[0]) + abs(cy - spot[1]) != 1:
        problems.append("Carmine at the bus stop (%d,%d) must stand next to %d,%d, one step up from where Briar's bus "
                        "leaves you: she stops you there" % (cx, cy, spot[0], spot[1]))
    else:
        bus_stop = W.reach(b, ARRIVE, blocked=set(map(tuple, stage0.values())) | {spot})
        if len(bus_stop) * 2 > len(before):           # (with the user's placements: a pocket of 10 tiles of 1,256)
            far = max(bus_stop, key=lambda t: abs(t[0] - ARRIVE[0]) + abs(t[1] - ARRIVE[1]))
            problems.append("from where Briar's bus leaves you there is a way into the town that does not pass %d,%d "
                            "(to %d,%d, ...): Carmine could be walked past" % (spot[0], spot[1], far[0], far[1]))
    walks = [("Kieran running in after Carmine's battle", KC.KIERAN_RUNS_IN, (("down", 2),), stage0, "kieran"),
             ("Ogerpon at the festival", (ox, oy), (("up", 4), ("down", 6)), st6, "ogerpon_fest"),
             ("Carmine running in as the Loyal Three wake", KC.CARMINE_RUNS_IN, (("up", 4),), wake, "carmine")]
    for what, start, steps, there, who in walks:
        others = {tuple(xy): k for k, xy in there.items() if k != who}
        for (x, y) in [tuple(start)] + walk_tiles(start, steps):
            if not on_map(x, y) or (x, y) not in before:
                problems.append("%s: %d,%d on the way is not ground you can walk on" % (what, x, y))
                break
            if (x, y) in others:
                problems.append("%s: %s stands at %d,%d on the way" % (what, name(others[x, y]), x, y))
                break
    flee = {k: (by_key[k].x, by_key[k].y) for k in fixed if k not in STATUE_KEYS}
    flee.update(KC.visible(15))
    flee["pecharunt"] = tuple(KC.P2_PECHA_MARKET)
    scenes.append(("stage 15", flee, None))             # (Part 2: the moment Pecharunt shows over the market)
    worst_all = 0
    for label, keys, centres in scenes:
        keys = {k: tuple(v) for k, v in keys.items()}
        stand = set(keys.values())
        seen = {}
        for k, xy in keys.items():
            if xy in seen:
                problems.append("%s: %s and %s are both at %d,%d" % (label, name(seen[xy]), name(k), xy[0], xy[1]))
            seen[xy] = k
        after = W.reach(b, ARRIVE, blocked=stand)
        lost = before - after - stand
        if lost:
            problems.append("%s: tiles no longer reachable: %s" % (label, sorted(lost)[:8]))
        for k, (x, y) in keys.items():
            if (x, y) not in before and (x, y) not in gaps:
                problems.append("%s: %s at %d,%d does not stand on ground you can walk to" % (label, name(k), x, y))
            if (x, y) in doors or (x, y + 1) in doors or (x, y - 1) in doors:
                problems.append("%s: %s stands in or before a doorway at %d,%d" % (label, name(k), x, y))
            if (x, y) in signs:
                problems.append("%s: %s stands on a sign at %d,%d" % (label, name(k), x, y))
            near = [(x + dx, y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
            if not any(t in after for t in near) and not k.startswith(("wake_", "ogerpon_fest")):
                problems.append("%s: %s at %d,%d cannot be reached to talk to" % (label, name(k), x, y))
        for (bx, by) in signs:
            if not any((bx + dx, by + dy) in after for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                problems.append("%s: the sign at %d,%d cannot be read" % (label, bx, by))
        worst, where, kinds = 0, None, {}
        tag = {k: KSP.tag_of(rom, by_key[k].gfx, by_key[k].ext) for k in keys}
        for (cx, cy) in [c for c in (centres or after) if c in after] or (centres or list(after)):
            near = {}
            for k, (x, y) in keys.items():
                if abs(x - cx) <= 9 and abs(y - cy) <= 7:
                    near.setdefault(tag[k], []).append(name(k))
            if len(near) > worst:
                worst, where, kinds = len(near), (cx, cy), near
        if worst > 6:
            problems.append("%s: %d kinds of colours on one screen, more than the game can show (around %d,%d): %s" % (
                label, worst, where[0], where[1], "; ".join(" + ".join(v) for t, v in sorted(kinds.items()))))
        worst_all = max(worst_all, worst)
    for key, m in rooms.items():
        mats = [(x, y) for (x, y, *_) in m.warps]
        if not mats:
            continue
        stand = {(o.x, o.y) for o in m.objs}
        room_reach = W.reach(m.blocks, mats[0], blocked=stand)
        seen = set()
        for o in m.objs:
            who = "%s (%s)" % (name(o_key(key, o)), key)
            if not (0 <= o.x < m.w and 0 <= o.y < m.h):
                problems.append("%s at %d,%d is off the room (x 0-%d, y 0-%d)" % (who, o.x, o.y, m.w - 1, m.h - 1))
                continue
            if (o.x, o.y) in seen:
                problems.append("%s: two people at %d,%d" % (key, o.x, o.y))
            seen.add((o.x, o.y))
            if key == "pc":
                continue
            v = m.blocks[o.y][o.x]
            if (v >> 10) & 3:
                problems.append("%s stands on a tile nobody can walk on (%d,%d)" % (who, o.x, o.y))
            if (o.x, o.y) in mats:
                problems.append("%s stands on the door mat at %d,%d" % (who, o.x, o.y))
            near = [(o.x + dx, o.y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
            if not any(t in room_reach for t in near):
                problems.append("%s at %d,%d cannot be reached to talk to" % (who, o.x, o.y))
        for (bx, by, *_) in m.bgs:
            if not any((bx + dx, by + dy) in room_reach for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))):
                problems.append("%s: the sign or plaque at %d,%d cannot be read: someone stands in front of it" % (
                    key, bx, by))
        lost = W.reach(m.blocks, mats[0]) - room_reach - stand
        if lost and key != "pc":
            problems.append("%s: its people shut off tiles %s" % (key, sorted(lost)[:6]))
    return problems, worst_all


def o_key(room, o):
    """the placements' name of a room's object (by its place in ROOM_PEOPLE)"""
    people = ROOM_PEOPLE.get(room, [])
    return people[o.local - 1][0] if 0 < o.local <= len(people) else "object %d" % o.local
