"""Every move tutor in the game: who teaches what, where, for what price and after which quest, for the guide's
Move Tutors page.

usage: HE_ROM=<patched rom> HE_ROMDATA_OUT=<folder of the romdata dumps> python tools/build_tutors.py
writes site/src/data/tutors.json (run tools/romdata/dump_maps.py and dump_tables.py for the ROM first)

How the game teaches (every address asserted below):
  the list    GetTutorMove (0x081B2360) jumps to the hack's 0x08FD7C08, which reads u16 moves at 0x08FD80B8: 127
              tutor moves, 0xFFFF after. Which Pokemon can learn tutor move n: bit n of its 16-byte row in the
              species' tutor table (tools/romdata/tables.py, "tutor bits"), read by the hack's bit test 0x08FD7C7C.
  teaching    special 0x1DD (ChooseMonForMoveTutor, 0x081B892C: the party menu in tutor mode) teaches tutor move
              VAR_0x8005. A script sets it one of three ways:
                - setvar VAR_0x8005, n: one move (Emerald's own tutors, and some of the hack's);
                - setvar VAR_0x8004, list; callnative 0x08FE3821 shows a menu of the six moves of that list (table
                  0x08C9A550, 6 tutor numbers a list, repeats allowed); callnative 0x08FE386D puts the choice in
                  VAR_0x8005;
                - the Battle Frontier's two tutors: a scrolling menu (special 0x1BE), VAR_0x8004 = which tutor,
                  VAR_0x8005 = the choice, callnative 0x08FF19E1 reads the tutor number from 0x08C9A530 (11 bytes a
                  tutor); the Battle Points are VAR_0x8008, set per choice.
              Chase's partner moves go another way: a grid menu (multichoice table 0x09700000, {list, count}), the
              player picks a Pokemon (special 0xA2) and the move to replace (special 0xDF), and callnative 0x0981E531
              writes move VAR_0x8007 into that slot if the Pokemon's species is VAR_0x8006 (no tutor bits). The
              menu (0x0982CCC2) sets VAR_0x8006 to Let's Go Pikachu, adds 1 (Let's Go Eevee) from a choice on, and
              adds the first move's id to the choice; partner_menu() reads it.
  price       removemoney after a successful teach (the hack's tutors: VAR_RESULT is not 0), shards taken with
              removeitem before the menu, or the Frontier's Battle Points.
A script is followed path by path with the values of the variables it sets (a comparison that is true on a path
fixes the variable there), so each tutor's moves and price come from the ROM. Who the tutor is and what they ask
is in NOTES, written from the script; the build stops on a tutor without one.
"""
import json
import os
import struct
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "romdata"))
import romlib as R                                          # noqa: E402
import scripts as S                                         # noqa: E402
import item_sources as I                                    # noqa: E402
import tables                                               # noqa: E402
from display_names import item_name, move_name             # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DATA = os.path.join(HERE, "..", "site", "src", "data")
rom = R.rom
T = tables.of(rom)
B = S.BASE

TUTOR_SPECIAL = 0x1DD
TUTORS = 0x00FD80B8
MENUS, MENU_SIZE = 0x00C9A550, 6
FRONTIER, FRONTIER_SIZE = 0x00C9A530, 11
NATIVE_MENU, NATIVE_PICK, NATIVE_FRONTIER = 0x08FE3821, 0x08FE386D, 0x08FF19E1
NATIVE_PARTNER, MULTICHOICE, CHOOSE_MON = 0x0981E531, 0x01700000, 0xA2
VAR_RESULT, V4, V5, V8 = 0x800D, 0x8004, 0x8005, 0x8008
assert R.u32(0x001B2360) == 0x47084900 and R.u32(0x001B2364) == 0x08FD7C09, "GetTutorMove is not the hack's"
assert R.u32(0x00FD7C14) == 0x08FD8060 and rom[0x00FD7C0E:0x00FD7C10] == bytes.fromhex("5823"), \
    "the hack's GetTutorMove reads elsewhere"                 # (0x08FD8060 + 0x58 is the list)
assert R.u32(0x001DBA64 + 4 * TUTOR_SPECIAL) == 0x081B892D and rom[0x001B8940] == 0x0C, "special 0x1DD moved"
assert R.u32(0x00FE3820 + 0x44) == B + MENUS and R.u32(0x00FE3820 + 0x48) == B + TUTORS, "the menu native moved"
assert R.u32(0x00FF19F8) == B + FRONTIER, "the Frontier native moved"
# the partner native: gPlayerParty + 0x20 (species) + 100 * VAR_0x8004, the special vars, gMoveNames (header 0x148),
# gStringVar1, gBattleMoves (header 0x1CC); result in VAR_0x8008 (0 wrong species, 1 knows it, 2 taught)
assert [R.u32(0x0181E5A8 + 4 * k) for k in range(5)] == [0x0202450C, 0x020375E0, 0x08000148, 0x02021CC4,
                                                          0x080001CC], "the partner-move native is not the one read"

tutor_moves = []
while R.u16(TUTORS + 2 * len(tutor_moves)) != 0xFFFF:
    tutor_moves.append(R.u16(TUTORS + 2 * len(tutor_moves)))


def mname(m):
    return move_name(R.decode(T.move_names + 13 * m, 13)[0])


def iname(i):
    return item_name(i, R.decode(R.u32(0x1C8) - B + 44 * i, 14)[0])


# ---------------- who each tutor is and what they ask (from their scripts) ----------------
# The Frontier tutors' step after a lesson (0x082656C6) is cut short in the original hack too: where Emerald has
# copyvar VAR_0x8004, VAR_0x8008 / special TakeFrontierBattlePoints (19 04 80 08 80 25 CB 01, as the hack's other
# Battle Point scripts have it), it has 19 04 80 08, so the next bytes are read as part of the copyvar, the special
# never runs and the branch back to the right tutor's menu uses a stale comparison. Tested in mGBA on the v2.0 game
# (_testrun/tutors/bp): 100 Battle Points before the step, 100 after, and the Swimmer's menu came up for the Beauty.
FRONTIER_NOTE = ("You need the Battle Points shown beside a move to choose it, but they are not taken (the original "
                 "hack’s script lost that line), and after a lesson the Swimmer’s menu comes back.")
# entry script -> (who, how). The script is the key: one tutor stands in several places when the hack reuses it.
NOTES = {
    # Emerald's own tutors, one move each, free, as often as you like
    0x082C7F7E: ("A girl who loves tricks", "Free, as often as you like."),
    0x082C81EE: ("A Fighting-type Trainer who cannot beat the Mossdeep Gym", "Free, as often as you like."),
    0x082C804E: ("A fan of a hero in a Tonkatsu film", "Free, as often as you like."),
    0x082C80B6: ("A student who read a botany book", "Free, as often as you like."),
    0x082C7FE6: ("A fan of deceiving opponents", "Free, as often as you like."),
    0x082C7F16: ("A Trainer who forgot something important", "Free, as often as you like."),
    0x082C811E: ("The husband of the coin-trick woman", "Free, as often as you like."),
    0x082C8186: ("A man who knows a move that makes every battle random", "Free, as often as you like."),
    0x09809EBF: ("A man enjoying the sea breeze", "Free, as often as you like."),
    # the hack's free menus
    0x09812FAA: ("A reward for Trainers who came through Victory Road", "Free."),
    0x098342EE: ("A helper for the World Championship", "Free."),
    # ¥5,000 a move, after a favour
    0x0984F890: ("A man who lost his Gold Bottle Cap",
                 "Bring him his own Gold Bottle Cap: the item ball in the Timeless Woods (another Gold Bottle Cap "
                 "will not do; he keeps it). Then ¥5,000 a move."),
    0x0984E805: ("An old man watching the moon",
                 "Give him a “red envelope” of ¥10,000 ten times without leaving Slateport City (he counts them in a "
                 "temporary variable, which leaving the city clears). Then ¥5,000 a move."),
    0x09852823: ("A man watching the sea",
                 "Three tasks: all eight Hoenn Badges, every Trick House puzzle, and the ten red envelopes for his "
                 "brother, the old man watching the moon in Slateport City. Then ¥5,000 a move."),
    0x0984EB46: ("A boy who lost his Net Ball", "Bring him a Net Ball. Then ¥5,000 a move."),
    0x0984EEF4: ("A man in the hot spring", "Bring him 20 Soda Pops and 5 Lemonades. Then ¥5,000 a move."),
    0x0984EF6E: ("A girl whose boyfriend is challenging the League",
                 "Take her letter to her boyfriend in the Pokémon League’s lobby at Ever Grande City. Then ¥5,000 "
                 "a move."),
    0x0984EF0C: ("A boy who wants to start a fashion trend",
                 "Bring him the six scarves: Silk, Red, Blue, Pink, Green and Yellow Scarf. Then ¥5,000 a move."),
    0x0984DF2F: ("An old traveller who never found a Moon Stone", "Bring him a Moon Stone. Then ¥5,000 a move."),
    0x0984F275: ("A shipbuilder who cannot focus",
                 "Ask his friend in the Mossdeep Space Center how the rocket is coming along, and tell him. Then "
                 "¥5,000 a move."),
    0x0984E287: ("A man who dreamed of an odd purple rock",
                 "Bring him the rock: an Eviolite. Then ¥5,000 a move."),
    0x0984E2C3: ("An explorer who fell through the floor",
                 "Bring him 15 Escape Ropes. Then ¥5,000 a move (“a discount”)."),
    0x0984E2DB: ("A sailor whose Machoke died at work",
                 "Take Machoke’s urn to its tombstone on Mt. Pyre, 5F. Then ¥5,000 a move."),
    0x0984F8A8: ("A Trainer whose Bag was stolen",
                 "Get the Bag back from the thief resting under a tree in the Battle Frontier’s eastern part. Then "
                 "¥5,000 a move."),
    0x0983D778: ("A lover of glasswork",
                 "Bring her the five glass flutes: Blue, Yellow, Red, Black and White Flute. Then ¥5,000 a move."),
    0x0984E659: ("Prof. Birch’s assistant, researching Mega energy",
                 "Talk to her once to hear what she is doing. Then ¥5,000 a move."),
    0x0985348A: ("The Dragon Elder",
                 "Have the Draco Plate with you (the “proof of the Dragon God’s approval”). Then ¥5,000 a move."),
    # shards, paid before the menu
    0x098644CF: ("A Red Shard fan", "6 Red Shards a move, paid before you choose (no refund if you quit)."),
    0x09853329: ("A Blue Shard collector", "6 Blue Shards a move, paid before you choose (no refund if you quit)."),
    0x09864599: ("A Green Shard lover", "9 Green Shards a move, paid before you choose (no refund if you quit)."),
    0x09864651: ("A Yellow Shard collector",
                 "9 Yellow Shards a move, paid before you choose (no refund if you quit)."),
    # Battle Points
    0x08265255: ("The old Beauty", FRONTIER_NOTE),
    0x08265445: ("The old Swimmer", FRONTIER_NOTE),
    # the story's own
    # Chase: 0x4170 (Elaine beaten on Route 104) and not 0x4171 -> his battle (sets 0x4171) instead of the menu
    0x0981E5D8: ("Chase, from Kanto",
                 "Free, as often as you like, but only for the partner Pokémon: the first four moves for Let’s Go "
                 "Pikachu, the other nine for Let’s Go Eevee. You pick the Pokémon and the move it forgets. Once "
                 "you have beaten Elaine on Route 104, he battles you first."),
    # the same menu; the house's door (36/3, 24,6) is a locked-door object hidden by 0x4171 (Chase beaten)
    0x098B0C7C: ("Chase again, with Elaine",
                 "The house’s door is locked until you have battled Chase in Fortree City (he battles you once you "
                 "have beaten Elaine on Route 104). Then the same partner moves, free, as often as you like."),
    # shown by the room's map script (0x098359DB) while 0x4161 (Maxie beaten in Terra Cave) or 0x41A6 (Yanshan
    # beaten on Steven's Island; his lesson here clears it) is set; his removeobject is undone on every entry
    0x0981DEE8: ("Yanshan, the strongest man in Team Magma",
                 "He waits here once you have beaten Maxie in Terra Cave (or Yanshan himself on Steven’s Island). "
                 "Beat him and he teaches V-Create, free, then leaves. After Maxie he is back each time you come "
                 "into the room, for another battle and another lesson."),
    0x0981D31B: ("Zinnia’s grandmother",
                 "After the Delta Episode, once you and Rayquaza have saved Hoenn from the meteor, she reteaches "
                 "Dragon Ascent (to Rayquaza). Free."),
    0x098C66B9: ("Keldeo’s teacher", "Free, for Keldeo; Secret Sword changes its form."),
    0x09810309: ("A keeper of ancient moves", "Free, for Meloetta."),
    # Firespit Island: after Volo (0x4315) she checks the party (special 0x149, VAR_0x8004 = slot) for Tornadus,
    # Thundurus and Landorus (species 694/899, 695/900, 698/901), then a wild Enamorus (species 1023) Lv 50; any
    # outcome but running (special 0xB7 == 4) sets 0x4319, and from then on she offers menu 21
    0x0989D84D: ("Cogita",
                 "After Volo, come with Tornadus, Thundurus and Landorus in your party (either form): she calls "
                 "Enamorus and you battle it (Lv 50). Once that battle is over, caught or knocked out (not if you "
                 "run), she teaches these, free, as often as you like. Rei (Mingyao) at the Deertrack Heights base "
                 "camp flies you here."),
    # Champion Island: shown once the base camp report (0x431E) is in (the 35/6 trigger at 7,16 clears 0x4325);
    # teaches menu 21 while 0x4319 is clear and 0x41D5 (Team Rainbow Rocket beaten) is set; with 0x4319 she talks
    # and leaves (sets 0x4325)
    0x098C202D: ("Cogita",
                 "She is here once Volo is beaten and you have heard Rei and Cogita’s news at base camp in Hisui. "
                 "She teaches these, free, once Team Rainbow Rocket is beaten, but only until you have battled "
                 "Enamorus with her on Firespit Island: after that she talks and leaves, and the Cogita on "
                 "Firespit Island teaches the same moves."),
}
# the guide's sections: the story's own tutors (one move for one Pokemon, or a reward at the end of a story) apart
STORY = {0x0981DEE8, 0x0981D31B, 0x098C66B9, 0x09810309, 0x0989D84D, 0x098C202D, 0x0981E5D8, 0x098B0C7C}
GROUP = {"free": "free", "money": "favour", "items": "shards", "bp": "frontier"}

# ---------------- following a script with the values it sets ----------------
COND_EQ, COND_NE = 1, 5
TRACK = {V4, V5, V8, 0x400D, 0x400E, 0x8000, VAR_RESULT}


def follow(entry):
    """[(kind, value, pay)] for every way the script reaches special 0x1DD. kind: fixed (value = tutor number),
    menu (value = list), frontier (value = (tutor, choice)); pay: {money, items, bp}."""
    events, seen = [], set()
    todo = [(entry, (), {}, None)]          # pc, call stack, vars, event the next removemoney belongs to
    steps = 0
    while todo and steps < 60000:
        pc, stack, var, ev = todo.pop()
        last_cmp = None
        while steps < 60000:
            steps += 1
            key = (pc, stack[-1:] if stack else (), tuple(sorted((str(k), repr(v)) for k, v in var.items())),
                   ev is None)
            if key in seen or not S.inrom(pc):
                break
            seen.add(key)
            o = pc - B
            op = rom[o]
            if op == 0x5C:                  # trainerbattle: on into its continue-script, if it has one
                kind = rom[o + 1]
                if kind not in S.TB_PTRS:
                    break
                n = 5 + 4 * S.TB_PTRS[kind]
                if kind in S.TB_SCRIPT:
                    pc = struct.unpack_from("<I", rom, o + 1 + 5 + 4 * (S.TB_SCRIPT[kind] - 1))[0]
                    continue
                pc += 1 + n
                continue
            if op not in S.OPLEN:
                break
            a = rom[o + 1:o + 1 + S.OPLEN[op]]
            nxt = pc + 1 + S.OPLEN[op]
            u = lambda k=0: struct.unpack_from("<H", a, k)[0]       # noqa: E731
            if op in (0x02,) or op in S.WARPS:
                break
            if op == 0x03:                  # return
                if not stack:
                    break
                pc, stack = stack[-1], stack[:-1]
                continue
            if op == 0x05:
                pc = struct.unpack_from("<I", a)[0]
                continue
            if op == 0x04:
                pc, stack = struct.unpack_from("<I", a)[0], stack + (nxt,)
                continue
            if op in (0x06, 0x07):
                cond, target = a[0], struct.unpack_from("<I", a, 1)[0]
                taken, fall = dict(var), dict(var)
                decided = None
                if last_cmp and last_cmp[0] in var:
                    v, k = var[last_cmp[0]], last_cmp[1]
                    if isinstance(v, int) and cond in (COND_EQ, COND_NE):
                        decided = (v == k) == (cond == COND_EQ)
                    elif cond == COND_EQ:                           # true on the taken path: fix the value there
                        for name, val in var.items():
                            if val == v:
                                taken[name] = k
                    elif cond == COND_NE:
                        for name, val in var.items():
                            if val == v:
                                fall[name] = k
                elif last_cmp and cond == COND_EQ and last_cmp[0] in TRACK:
                    taken[last_cmp[0]] = last_cmp[1]
                last_cmp = None
                if op == 0x06:
                    if decided is not False:
                        todo.append((target, stack, taken, ev))
                    if decided is True:
                        break
                    pc, var = nxt, fall
                else:
                    if decided is not False:
                        todo.append((target, stack + (nxt,), taken, ev))
                    if decided is True:
                        break
                    pc, var = nxt, fall
                continue
            if op == 0x21:                  # compare var, value
                last_cmp = (u(0), u(2))
            elif op == 0x2B:
                last_cmp = None
            elif op == 0x16 and u(0) in TRACK:
                var = {**var, u(0): u(2)}
            elif op == 0x17 and u(0) in TRACK:
                var = {**var, u(0): var[u(0)] + u(2) if isinstance(var.get(u(0)), int) else ("?", pc)}
            elif op == 0x19 and u(0) in TRACK:
                var = {**var, u(0): var.get(u(2), ("var", u(2)))}
            elif op == 0x1A and u(0) in TRACK:
                var = {**var, u(0): var.get(u(2), ("var", u(2))) if u(2) >= 0x4000 else u(2)}
            elif op in (0x25, 0x26):
                sid = u(0) if op == 0x25 else u(2)
                if op == 0x25 and sid == TUTOR_SPECIAL and ev is None:     # (a lesson after a lesson: the
                    v5 = var.get(V5)                                         # same tutor's menu again, or not)
                    if isinstance(v5, int):
                        events.append(["fixed", v5, {}])
                    elif isinstance(v5, tuple) and v5[0] == "menu":
                        events.append(["menu", v5[1], {}])
                    elif isinstance(v5, tuple) and v5[0] == "frontier":
                        events.append(["frontier", v5[1], {"bp": var.get(V8)}])
                    else:
                        events.append(["unknown", repr(v5), {}])
                    for k, val in var.items():
                        if k == "paid":
                            events[-1][2]["items"] = list(val)
                    ev = len(events) - 1
                var = {**var, VAR_RESULT: ("result", pc)}
            elif op == 0x23:
                native = struct.unpack_from("<I", a)[0]
                if native == NATIVE_PICK and isinstance(var.get(V4), int):
                    var = {**var, V5: ("menu", var[V4])}
                elif native == NATIVE_FRONTIER and isinstance(var.get(V4), int) and isinstance(var.get(V5), int):
                    var = {**var, V5: ("frontier", (var[V4], var[V5]))}
                var = {**var, VAR_RESULT: ("result", pc)}
            elif op == 0x91 and ev is not None:                     # removemoney after a teach
                events[ev][2]["money"] = struct.unpack_from("<I", a)[0]
            elif op == 0x45 and ev is None:                         # removeitem before the teach
                var = {**var, "paid": tuple(var.get("paid", ())) + ((u(0), u(2)),)}
            elif op == 0x27:
                var = {**var, VAR_RESULT: ("result", pc)}
            pc = nxt
    return events


def partner_menu(ins):
    """[(move, species)] of Chase's grid menu: setvar VAR_0x8006, species; multichoicegrid list; copyvar
    VAR_0x8007, VAR_RESULT; the cancel choice; below a choice it stays, from it on addvar VAR_0x8006, 1; then
    addvar VAR_0x8007, first move on both paths"""
    starts = [pc for pc, op, a in ins if op == 0x16 and struct.unpack_from("<H", a)[0] == 0x8006
              and rom[pc - B + 5] == 0x71]
    assert len(starts) == 1, "partner menu: %d starts" % len(starts)
    o = starts[0] - B
    species, lst = R.u16(o + 3), rom[o + 5 + 3]
    o += 11
    assert rom[o:o + 5] == bytes.fromhex("1907800d80"), "partner menu: no copyvar VAR_0x8007, VAR_RESULT"
    assert rom[o + 5] == 0x21 and R.u16(o + 6) == VAR_RESULT and rom[o + 10:o + 12] == bytes.fromhex("0601")
    cancel = R.u16(o + 8)
    o += 16
    assert rom[o] == 0x21 and R.u16(o + 1) == VAR_RESULT and rom[o + 5:o + 7] == bytes.fromhex("0600")
    split, low = R.u16(o + 3), R.u32(o + 7) - B
    o += 11
    assert rom[o:o + 6] == bytes.fromhex("170680010000"), "partner menu: no addvar VAR_0x8006, 1"
    o += 6
    assert rom[o] == 0x17 and R.u16(o + 1) == 0x8007 and rom[low:low + 5] == rom[o:o + 5]
    first = R.u16(o + 3)
    entries = R.u32(MULTICHOICE + 8 * lst), rom[MULTICHOICE + 8 * lst + 4]
    assert entries[1] == cancel + 1 and "Cancel" in R.decode(R.u32(entries[0] - B + 8 * cancel) - B, 40)[0]
    return [(first + i, species if i < split else species + 1) for i in range(cancel)]


# ---------------- the rooms: a shared interior is named by the doors that lead to the tutor's part of it ----------
maps = [m for m in R.load("maps.json") if m.get("events")]
by_map = {(m["group"], m["num"]): m for m in maps}


def events_of(m):
    e = m["events"]
    return (int(e, 16) if isinstance(e, str) else e) - B


def warps(m):
    ev = events_of(m)
    p = R.u32(ev + 8)
    return [struct.unpack_from("<hhBBBB", rom, p - B + 8 * k) for k in range(rom[ev + 1])] if S.inrom(p) else []


GENERIC = {"Sinnoh Region", "Hisui Region"}
all_warps = {(m["group"], m["num"]): warps(m) for m in maps}


SHORT = {"Hisui Region": "Hisui", "Sinnoh Region": "Sinnoh"}
# Hisui's maps all carry the section "Hisui Region"; this one is named by the game's Hisui map (A on Firespit
# Island flies to 37/105) and by Mingyao's fly menu
NAMED = {(37, 105): "Hisui · Firespit Island",
         (37, 116): "Oreburgh City · house"}           # one room, its door at Oreburgh City (36/3) 24,6


def place_of(m, x, y):
    """the place; a room of a shared interior (several rooms stacked in one map, its section "Sinnoh Region") is
    named by where its own way out leads"""
    if (m["group"], m["num"]) in NAMED:
        return [NAMED[(m["group"], m["num"])]]
    name = I.place(m)
    if name not in GENERIC:
        return [name]
    own = all_warps[(m["group"], m["num"])]
    if not own:
        return [SHORT.get(name, name)]
    wx, wy, _, _, num, group = min(own, key=lambda w: abs(w[0] - x) + abs(w[1] - y))
    out = I.place(by_map[(group, num)]) if (group, num) in by_map else name
    return ["%s · house" % SHORT.get(out, out)]


# ---------------- every tutor ----------------
OBJ = __import__("re").compile(r"object \d+ \(local \d+, gfx \d+, at (\d+),(\d+),")
found = defaultdict(lambda: {"places": [], "events": None})
problems = []
for m in maps:
    if I.unreleased(m["group"], m["num"]):
        continue
    for desc, entry in S.entry_points(m):
        hit = OBJ.match(desc)
        if not hit:
            continue
        ins, _ = S.walk(entry)
        partner = (any(op == 0x23 and struct.unpack_from("<I", a)[0] == NATIVE_PARTNER for pc, op, a in ins)
                   and any(op in (0x25, 0x26) and S.u16_(a) == CHOOSE_MON for pc, op, a in ins))
        if not partner and not any(op == 0x25 and S.u16_(a) == TUTOR_SPECIAL for pc, op, a in ins):
            continue
        x, y = int(hit[1]), int(hit[2])
        if I.walled_in(m, x, y, itself=True):
            continue
        t = found[entry]
        if t["events"] is None:
            t["events"] = [["partner", partner_menu(ins), {}]] if partner else follow(entry)
        for p in place_of(m, x, y):
            t["places"].append({"place": p, "spot": "%d-%d-%d-%d" % (m["group"], m["num"], x, y)})

tutors = []
taught_by = defaultdict(list)
for entry, t in sorted(found.items(), key=lambda kv: min(p["spot"] for p in kv[1]["places"])):
    if entry not in NOTES:
        problems.append("tutor script %#010x at %s has no note in NOTES" % (entry, t["places"][0]["place"]))
        continue
    who, how = NOTES[entry]
    moves, pay, bp, only = [], {}, {}, {}
    for kind, value, paid in t["events"]:
        if kind == "partner":                # the moves are on the tutor list; the species check is the native's
            nums = [tutor_moves.index(mv) for mv, sp in value]
            only.update({tutor_moves.index(mv): sp for mv, sp in value})
        elif kind == "fixed":
            nums = [value]
        elif kind == "menu":
            nums = list(rom[MENUS + MENU_SIZE * value:MENUS + MENU_SIZE * value + MENU_SIZE])
        elif kind == "frontier":
            tutor, choice = value
            nums = [rom[FRONTIER + FRONTIER_SIZE * tutor + choice]]
            bp[nums[0]] = paid.get("bp")
        else:
            problems.append("%s at %s: the move it teaches is not known on one path (%s)"
                            % (who, t["places"][0]["place"], value))
            continue
        for n in nums:
            if n not in moves:
                moves.append(n)
        if paid.get("money"):
            pay["money"] = paid["money"]
        for item, qty in paid.get("items", []):
            pay.setdefault("items", {})[item] = qty
    frontier_rows = {value[0] for kind, value, _ in t["events"] if kind == "frontier"}
    if len(frontier_rows) == 1:              # the Frontier menu's order
        row_ = rom[FRONTIER + FRONTIER_SIZE * frontier_rows.pop():][:FRONTIER_SIZE - 1]
        moves.sort(key=lambda n: list(row_).index(n))
    seen_p, places = set(), []
    for p in t["places"]:
        if p["place"] not in seen_p:
            seen_p.add(p["place"])
            places.append(p)
    tid = len(tutors)
    row = {"id": tid, "who": who, "how": how, "places": places,
           "moves": [{"n": n, "move": tutor_moves[n], "name": mname(tutor_moves[n]),
                      **({"bp": bp[n]} if n in bp else {}), **({"only": only[n]} if n in only else {})}
                     for n in moves]}
    if pay.get("money"):
        row["pay"] = {"kind": "money", "amount": pay["money"]}
    elif pay.get("items"):
        (item, qty), = pay["items"].items()
        row["pay"] = {"kind": "items", "item": item, "itemName": iname(item), "amount": qty}
    elif bp:
        row["pay"] = {"kind": "bp"}
    else:
        row["pay"] = {"kind": "free"}
    row["group"] = "story" if entry in STORY else GROUP[row["pay"]["kind"]]
    tutors.append(row)
    for n in moves:
        taught_by[n].append(tid)

if problems:
    sys.exit("\n".join(problems))
moves_out = [{"n": n, "move": m, "name": mname(m), "tutors": taught_by.get(n, [])} for n, m in enumerate(tutor_moves)]
json.dump({"tutors": tutors, "moves": moves_out}, open(os.path.join(DATA, "tutors.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
kinds = defaultdict(int)
for t in tutors:
    kinds[t["pay"]["kind"]] += 1
print("tutors.json: %d tutors (%s) | %d of %d tutor moves taught by someone"
      % (len(tutors), ", ".join("%s %d" % kv for kv in sorted(kinds.items())),
         sum(1 for x in moves_out if x["tutors"]), len(moves_out)))
