"""A clock on the Start menu (Hyper Emerald v5.7): python startclock_patch.py in.gba out.gba

Asked 2026-10-22, with a picture of a Start menu clock ("Thu. 10:29 AM (DAY)"): "can we have time table next
to R journey when press start menu?"

A framed box with the day of the week and the 12-hour time, "Thu 10:29 AM", on the Quest Log's "[R] Journal" box's
row, to its right (the Journal's box is (1,1) 8 x 2, its frame tiles 0-9; ours (11,1) 9 x 2, frame 10-20; the Start
menu's frame starts at 21). At the top left without the Journal; under the Safari Zone's or the Battle Pyramid's
window there (those are 9 and 10-12 wide: no room beside them). The time is the game's own clock (RtcCalcLocalTime
0x0802F588: the cartridge clock less the offset the player set, gLocalTime 0x03005CF8); the day of the week is the
clock's day count (gLocalTime.days + the offset's days = the game's day count, 1 = Saturday 1 January 2000: the
cartridge clock's Thursday 22 Oct 2026 is day 9792) + 5, mod 7. It is redrawn when the minute changes, and goes down
with the Journal's box (A, B, START, and R with the Journal).
2026-10-23 (the user, with a picture of the box under the Journal's: "remove the evening, whatever, and move into the
same row as R Journey"): the time of day ("(Evening)", by the hack's tint hours) is gone and the box moved up beside
the Journal's; it was under it (y 5) before.

How: startclock.s, chained in front of the Quest Log's two hooks, both words: InitStartMenuStep's step-3 entry
(0x0809F8C4) and HandleStartMenuInput's trampoline word (0x0809FAC8). The window: BG0, palette 15, base block 64
(BG0 tiles 24-262 are unused while the menu is up: the menu takes 313-452, the Journal box 8-23, the Safari window
8-43, the Pyramid's 8-55, the map-name popup 263-292). State: 0x02039E48..0x02039E7F (the scratch test's 64 bytes
at 0x02039E40, after the Quest Log's 8). Code and data at 0x09E3BC00 (eshot's proven stretch, kept free for this).
"""
import os, re, struct, sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "paldea"))
import lib                                         # the game's charset and the font's widths

B = 0x08000000
SPACE, SPACE_END = 0x09E3BC00, 0x09E3C000
SCRATCH, SCRATCH_END = 0x02039E48, 0x02039E80
CASE3_ENTRY = 0x0809F8C4                           # InitStartMenuStep's jump table, step 3
HSI = 0x0809FAC4                                   # HandleStartMenuInput: ldr r3, [pc, #0]; bx r3; .word
QUESTLOG = (0x08FEA000, 0x08FED3C8)                # the Quest Log's code, whose hooks these are now
CALLED = {0x0802F588: "10b5074c", 0x08008CC0: "f0b54746", 0x082E7BE0: "002958d0", 0x080D6724: "f0b50004",
          0x080FC0A0: "00b50348", 0x081A9E40: "00b50348", 0x08003380: "f0b55746", 0x0800378C: "10b587b0",
          0x081973FC: "30b50c1c", 0x08003C48: "30b581b0", 0x080045D0: "f0b54746", 0x08003658: "70b583b0",
          0x08198070: "30b50c1c", 0x08003574: "f0b50006", 0x081999BC: "0006000e"}
BASE_BLOCK, X = 64, 2
PLACES = ((1, 1), (11, 1), (1, 7))                 # (left, top): no Journal / beside the Journal's box / under the
                                                   # Safari or Pyramid window (show_clock's r5: 0, 1, 2)
JOURNAL_BOX = bytes((0, 1, 1, 8, 2, 15)) + struct.pack("<H", 8)    # the Quest Log's WIDGET_TEMPLATE: (1,1) 8 x 2
MENU_FRAME_X = 21                                  # the Start menu's frame (its window is at x 22)
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    assert not [i for i in dis if i.size == 4 and i.mnemonic != "bl"], "Thumb-2 encoding emitted"
    return code, dis


def u32(rom, a):
    return struct.unpack_from("<I", rom, a - B)[0]


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    for a, want in CALLED.items():
        assert rom[a - B:a - B + 4].hex() == want, "the routine at %08X" % a
    qcase3 = u32(rom, CASE3_ENTRY)
    assert QUESTLOG[0] <= qcase3 < QUESTLOG[1] and qcase3 % 2 == 0, "step 3 is not the Quest Log's: %08X" % qcase3
    assert rom[HSI - B:HSI - B + 4].hex() == "004b1847", "HandleStartMenuInput's trampoline"
    qhsi = u32(rom, HSI + 4)
    assert QUESTLOG[0] <= qhsi < QUESTLOG[1] and qhsi & 1, "HandleStartMenuInput is not the Quest Log's: %08X" % qhsi

    # the texts and the box's width: the widest line, in the normal font
    width = max(lib.width(rom, lib.enc("%s %d:%02d %s" % (d, h, m, ap)))
                for d in DAYS for h in range(1, 13) for m in range(60) for ap in ("AM", "PM"))
    w_tiles = (X + width + 2 + 7) // 8
    for left, top in PLACES:
        assert left + w_tiles < MENU_FRAME_X, "the box at x %d would reach the Start menu" % left
    jb = [o + B for o in range(QUESTLOG[0] - B, QUESTLOG[1] - B) if rom[o:o + 8] == JOURNAL_BOX]
    assert len(jb) == 1, "the Journal's box is not the (1,1) 8 x 2 one: %s" % jb
    # (a frame takes the tile on each side: the Journal's right edge is tile left + width, ours left - 1)
    assert PLACES[1][0] - 1 > JOURNAL_BOX[1] + JOURNAL_BOX[3], "the box would cover the Journal's frame"
    assert PLACES[1][1] == JOURNAL_BOX[2]
    assert BASE_BLOCK + 2 * w_tiles <= 263

    # the space and the scratch
    assert set(rom[SPACE - B:SPACE_END - B]) == {0}, "the space is not blank"
    held = [B + o for o in range(0, len(rom), 4) if SPACE <= struct.unpack_from("<I", rom, o)[0] < SPACE_END]
    assert not held, "words point into the space: %s" % ["%08X" % a for a in held]
    held = [B + o for o in range(0, len(rom), 4) if SCRATCH <= struct.unpack_from("<I", rom, o)[0] < SCRATCH_END]
    assert not held, "words point into the scratch: %s" % ["%08X" % a for a in held]

    src = open(os.path.join(HERE, "startclock.s"), encoding="ascii").read()
    def assemble(data_at):
        s = src.replace("QCASE3", "0x%08X" % (qcase3 | 1)).replace("QHSI", "0x%08X" % qhsi)
        for k, v in data_at.items():
            s = re.sub(r"\b%s\b" % k, "0x%08X" % v, s)
        for pad in ("", "    mov r8, r8"):
            code, dis = thumb(s.replace("PAD", pad), SPACE)
            if not [i for i in dis if i.mnemonic == "nop"]:
                return code, dis
        raise AssertionError("could not pad the literal pool without a Thumb-2 nop")
    names = ("TEMPLATES", "DAYS", "AM", "PM")
    code, dis = assemble({n: SPACE for n in names})
    data_at, at = {}, (SPACE + len(code) + 3) & ~3
    templates = b"".join(bytes((0, left, top, w_tiles, 2, 15)) + struct.pack("<H", BASE_BLOCK) for left, top in PLACES)
    days = b"".join(lib.enc(d) + b"\xff" for d in DAYS)
    assert len(days) == 28
    data = [("TEMPLATES", templates), ("DAYS", days), ("AM", lib.enc(" AM") + b"\xff"), ("PM", lib.enc(" PM") + b"\xff")]
    blob = b""
    for n, d in data:
        data_at[n] = at + len(blob)
        blob += d
        blob += b"\0" * (-len(blob) % 4)
    code2, dis = assemble(data_at)
    assert len(code2) == len(code)
    assert at + len(blob) <= SPACE_END
    # case3_clock first (an even address, entered in Thumb), hsi_clock right after its five instructions
    assert [i.mnemonic for i in dis[:5]] == ["push", "bl", "pop", "ldr", "bx"], "case3_clock"
    hsi_clock = dis[5].address
    assert [i.mnemonic for i in dis[5:9]] == ["push", "bl", "pop", "mov"], "hsi_clock"

    rom[SPACE - B:SPACE - B + len(code2)] = code2
    rom[at - B:at - B + len(blob)] = blob
    struct.pack_into("<I", rom, CASE3_ENTRY - B, SPACE)
    struct.pack_into("<I", rom, HSI + 4 - B, hsi_clock | 1)
    open(outp, "wb").write(rom)
    print("startclock: code %08X..%08X, data ..%08X; box %d x 2 tiles (widest line %d px), base block %d"
          % (SPACE, SPACE + len(code2), at + len(blob), w_tiles, width, BASE_BLOCK))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
