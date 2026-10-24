"""The console in your room in the Quest Log: a Side Content row for each of its four cartridges (Hyper Emerald v5.7).
usage: python -I consolequest_patch.py <in.gba> <out.gba>

The user (2026-10-23), after asking what the console in the player's room is for: "include in the side quest, 4
quests".

The console (NOTES, *The console's cartridges*): both rooms' consoles (1/1's sign at 3,1, script 0x0987B8A8; 1/3's at
5,1, 0x098806C3) say "It's a Nintendo GameCube..." and, once Team Rainbow Rocket is beaten (0x41D5) and Elio on
Steven's Island has given you three cartridges (0x42F3), go on to one menu (0x0988F782): Rainbow R., Ultra A. and
Friends, and HP League once Ash's challenge is done (0x4302: the cartridge the red-haired passerby drops). A cartridge
is a run of battles at Lv50; win them all and it shows "GAME CLEAR" and ends as the Hall of Fame does (0x082298E9 /
0x082298F5: setrespawn, special 0x113, the Hall of Fame's own lines). Lose one and it is "GAME OVER". Nothing in the
game marked a cartridge as cleared.

Now each cartridge's call to 0x09882738 (the routine that clears the run's hide flags, the line before "GAME CLEAR")
calls a stub that sets that cartridge's flag and goes on to the routine, so the flag is set before the Hall of Fame
saves the game. The GAME OVER path (its own call at 0x09882B6C) sets nothing.
Flags (patches/kitakami/freecheck.py on build 46 and the user's saves: no flag command's bytes anywhere in the ROM,
no aligned word, no object hides by them, clear in every save; not trainer flags): 0x43A4 Rainbow R., 0x43A8
Ultra A., 0x43A9 Friends, 0x416B HP League. Checked again here, on the input.

Quest Log: Side Content gets the four rows after "The note's sender" (row 44, 0x4303: the HP League cartridge comes
with that note), Area Zero's ten after them; the chapter's rows and count 55 -> 59, the Badges page (the same table,
after Side Content's rows) four rows on. New row and panel tables, as gen9journal makes them; SIDES_LIT and PANES[3]
repointed. A row: {marks, flag, name, text, text}; a panel: {kind, 0, picture, location, text, text}.

Space: 0x09E22000..0x09E24000 (kept): the original hack's zero run 0x09E10044..0x09F00000 (the read watch of
2026-10-17: 14 runs, 0 reads), just below azpeople's claim (from 0x09E24000). Blank, and no aligned word of the
ROM reads as an address anywhere in 0x09E21200..0x09E24000 (between 0x09E2E000 and 0x09E33000, the first place
tried, seven chance words in pictures did). Checked here: all zero, no aligned word points in.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(REPO, "patches", "paldea"), os.path.join(REPO, "patches", "journal")]
import journal_patch as J
import journal_az as JAZ
from lib import Blob

B = 0x08000000
FREE, FREE_END = 0x09E22000, 0x09E24000
CONSOLES = (0x0987B8B8, 0x098806D3)                     # each room's goto_if to the menu script
MENU_SCRIPT = 0x0988F782
MENU = 0x0988F7DF                                       # compare 0x4004 == k; goto_if == -> cartridge k (11 bytes each)
CLEAR_HIDES = 0x09882738                                # clearflag 0x264, 0x268, 0x273, 0x274, 0x276, 0x278, 0x27F; return
CLEAR_HIDES_BYTES = bytes.fromhex("2a64022a68022a73022a74022a76022a78022a7f0203")
GAME_CLEAR = 0x09882FF9                                 # "GAME CLEAR" is displayed on the screen...
GAME_OVER_CALL = 0x09882B6C                             # the lost run's call to CLEAR_HIDES (left as it is)
TRAINERS = 0x090019F8                                   # gTrainers, 40 bytes a trainer: +3 its picture, +4 its name

# (menu result, entry, the call before GAME CLEAR, flag, the run's last trainer, row name, text, picture)
CARTS = [
    (0, 0x09882666, 0x09882B3F, 0x43A4, (1116, "Giovanni"), "Cartridge: Rainbow R.",
     "Elio's cartridge for the console in your room: beat him on Steven's Island after Team Rainbow Rocket. Bring "
     "six Pokémon, all at Lv50: six double battles, three tag battles, then Giovanni. Win and your team enters the "
     "Hall of Fame.", True),
    (1, 0x09882B87, 0x09882C1C, 0x43A8, (881, "Leon"), "Cartridge: Ultra A.",
     "Elio's cartridge for the console in your room. Nine Champions in a row, all at Lv50, team order fixed. "
     "Except on Standard, the Gym's rules apply. Win and your team enters the Hall of Fame.", True),
    (2, 0x09882C45, 0x09882CF0, 0x43A9, (857, "Red"), "Cartridge: Friends",
     "Elio's cartridge for the console in your room. Nine famous Trainers from other regions in a row, all at Lv50, "
     "team order fixed. Except on Standard, the Gym's rules apply. Win and your team enters the Hall of Fame.", True),
    (3, 0x09882D19, 0x09882D9A, 0x416B, (899, "Yanshan"), "Cartridge: HP League",
     "the red-haired passerby drops it after Ash's challenge: a cartridge for the console in your room. Seven "
     "battles, all at Lv50, team order fixed. Except on Standard, the Gym's rules apply. Win and your team enters "
     "the Hall of Fame.", False),        # (who waits in it is the surprise: no picture)
]
WHERE = "Littleroot Town"

PAGES, PANES, SIDES_LIT = 0x08FEC5EC, 0x08FED35C, 0x08FEB230
SIDE_PAGE, BADGE_PAGE = 6, 7
SIDE_ROWS, BADGE_ROWS = 55, 8
AFTER_FLAG = 0x4303                                     # "The note's sender"
PANE_TEXT_W = 158
MAP_GROUPS = 0x08A54698


def u16(rom, a): return struct.unpack_from("<H", rom, a - B)[0]
def u32(rom, a): return struct.unpack_from("<I", rom, a - B)[0]


def hidden_by(rom):
    """every flag a map object hides by (its template's +20), on every map of every group"""
    ok = lambda a: B <= a < B + len(rom) - 0x40
    groups, g = [], 0
    while ok(u32(rom, MAP_GROUPS + 4 * g)):
        groups.append(u32(rom, MAP_GROUPS + 4 * g)); g += 1
    starts, out = sorted(set(groups)), set()
    for ga in groups:
        nxt = min([s for s in starts if s > ga], default=None)
        n = 0
        while nxt is None or ga + 4 * n < nxt:
            h = u32(rom, ga + 4 * n)
            if not ok(h):
                break
            ev = u32(rom, h + 4)
            if ok(ev) and rom[ev - B] and ok(u32(rom, ev + 4)):
                objs = u32(rom, ev + 4)
                for k in range(min(rom[ev - B], 64)):
                    out.add(u16(rom, objs + 24 * k + 20))
            n += 1
    return out


def check(rom):
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    for a in CONSOLES:
        assert u32(rom, a) == MENU_SCRIPT, "the console at %08X does not go to the menu" % a
    assert bytes(rom[CLEAR_HIDES - B:CLEAR_HIDES - B + len(CLEAR_HIDES_BYTES)]) == CLEAR_HIDES_BYTES
    calls = [m.start() + B for m in re.finditer(re.escape(b"\x04" + struct.pack("<I", CLEAR_HIDES)), rom)]
    assert calls == sorted([c for _, _, c, *_ in CARTS] + [GAME_OVER_CALL]), \
        "the calls to %08X are %s" % (CLEAR_HIDES, ["%08X" % c for c in calls])
    for k, (res, entry, site, flag, (tid, tname), name, text, pic) in enumerate(CARTS):
        m = MENU + 11 * k
        assert rom[m - B] == 0x21 and u16(rom, m + 1) == 0x4004 and u16(rom, m + 3) == res
        assert rom[m + 5 - B:m + 7 - B] == b"\x06\x01" and u32(rom, m + 7) == entry, "menu %d" % res
        assert rom[site + 5 - B] == 0x67 and u32(rom, site + 6) == GAME_CLEAR, "no GAME CLEAR after %08X" % site
        last = b"\x16\x15\x80" + struct.pack("<H", tid)                # setvar 0x8015, the last trainer
        assert rom.find(last, entry - B, site - B) > 0, "%s is not in cartridge %d" % (tname, res)
        t = TRAINERS + 40 * tid
        assert bytes(rom[t + 4 - B:t + 5 + len(tname) - B]) == J.enc(tname) + b"\xff", "trainer %d" % tid
    # the flags: free (patches/kitakami/freecheck.py's tests that need no save)
    wordlist = struct.unpack_from("<%dI" % (len(rom) // 4), rom)
    words = set(wordlist)
    hides = hidden_by(rom)
    for flag in (c[3] for c in CARTS):
        for op in (0x29, 0x2A, 0x2B):
            assert rom.find(bytes([op]) + struct.pack("<H", flag)) < 0, "%02X %04X is in the ROM" % (op, flag)
        assert flag not in words and flag not in hides, "flag %04X is in use" % flag
        assert not 0x357 < flag - 0x40C9 < 1459, "flag %04X is a trainer's" % flag
    # the Quest Log as gen9journal left it
    p = PAGES - B
    assert tuple(rom[p + 8 * SIDE_PAGE:p + 8 * SIDE_PAGE + 4]) == (0, SIDE_ROWS, SIDE_ROWS, 3), "Side Content's page"
    assert tuple(rom[p + 8 * BADGE_PAGE:p + 8 * BADGE_PAGE + 4]) == (SIDE_ROWS, BADGE_ROWS, BADGE_ROWS, 3), "Badges"
    sides, sidep = u32(rom, SIDES_LIT), u32(rom, PANES + 12)
    flags = [u16(rom, sides + 16 * i + 2) for i in range(SIDE_ROWS + BADGE_ROWS)]
    assert AFTER_FLAG in flags[:SIDE_ROWS] and not {c[3] for c in CARTS} & set(flags)
    for w in (sides, sidep):
        assert wordlist.count(w) == 1, "a second word points at %08X" % w
    assert set(rom[FREE - B:FREE_END - B]) == {0}, "the space is not blank"
    assert not [w for w in words if FREE <= w < FREE_END], "a word points into the space"
    return sides, sidep, flags.index(AFTER_FLAG) + 1


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    sides, sidep, at = check(rom)
    blob = Blob(FREE)
    h = lambda v: struct.pack("<H", v)
    stubs = [blob.put(("stub", c[0]), b"\x29" + h(c[3]) + b"\x05" + struct.pack("<I", CLEAR_HIDES), 1) for c in CARTS]

    locw = PANE_TEXT_W - JAZ.px(rom, "Location:") - 3
    assert JAZ.px(rom, WHERE) <= locw
    loc = blob.put("loc", J.enc(WHERE) + b"\xff", 1)
    rows, panes = [], []
    for res, entry, site, flag, (tid, tname), name, text, pic in CARTS:
        assert len(name) <= 24, name
        name_p = blob.put(("name", res), J.enc(name) + b"\xff", 1)
        text_p = blob.put(("text", res), JAZ.pane("%s: %s" % (WHERE, text)), 1)
        lines = JAZ.wrap_px(rom, text[:1].upper() + text[1:], PANE_TEXT_W, 3)
        panel = blob.put(("panel", res), b"\xfe".join(J.enc(l) for l in lines) + b"\xff", 1)
        rows.append(struct.pack("<HHIII", 0, flag, name_p, text_p, text_p))
        kind, pid = (2, rom[TRAINERS + 40 * tid + 3 - B]) if pic else (0, 0)
        panes.append(struct.pack("<BBHIII", kind, 0, pid, loc, panel, panel))
    n = SIDE_ROWS + BADGE_ROWS
    old = [bytes(rom[sides - B + 16 * i:sides - B + 16 * (i + 1)]) for i in range(n)]
    oldp = [bytes(rom[sidep - B + 16 * i:sidep - B + 16 * (i + 1)]) for i in range(n)]
    sides_new = blob.put("rows", b"".join(old[:at] + rows + old[at:]), 4)
    sidep_new = blob.put("panes", b"".join(oldp[:at] + panes + oldp[at:]), 4)

    data = blob.link()
    assert FREE + len(data) <= FREE_END, "%d bytes: more than the space" % len(data)
    rom[FREE - B:FREE - B + len(data)] = data
    for c, stub in zip(CARTS, stubs):
        struct.pack_into("<I", rom, c[2] + 1 - B, stub)                # call stub (was: call CLEAR_HIDES)
    struct.pack_into("<I", rom, SIDES_LIT - B, sides_new)
    struct.pack_into("<I", rom, PANES + 12 - B, sidep_new)
    p = PAGES - B
    rom[p + 8 * SIDE_PAGE + 1] += len(rows)
    rom[p + 8 * SIDE_PAGE + 2] += len(rows)
    rom[p + 8 * BADGE_PAGE] += len(rows)
    open(outp, "wb").write(rom)
    print("consolequest: %d cartridges set %s at GAME CLEAR (stubs %s); Side Content %d -> %d rows (after row %d) "
          "@%08X, panels @%08X; %d bytes @%08X..%08X" % (
              len(CARTS), "/".join("%04X" % c[3] for c in CARTS), "/".join("%08X" % s for s in stubs), SIDE_ROWS,
              SIDE_ROWS + len(rows), at - 1, sides_new, sidep_new, len(data), FREE, FREE + len(data)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
