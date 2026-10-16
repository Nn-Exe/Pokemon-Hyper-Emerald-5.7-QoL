"""Tornadus and Thundurus stay in Sinnoh after Continue (Hyper Emerald v5.7). Apply anywhere before zhtext.
usage: python roamfix_patch.py <in.gba> <out.gba>

A bug of the hack's own. The Valley Windworks researcher (36/54, script 0x0987A93F) starts a roaming Pokemon with
the game's InitRoamer special (299) and gSpecialVar_0x8004 = 2 (Tornadus, species 694) or 3 (Thundurus, 695): the
hack's CreateInitialRoamerMon (0x09F06118) puts it on one of the 27 Sinnoh routes of its own table (0x09F0AACC,
six bytes a row as the game's Hoenn table 0x085CEC30: the route, then the routes it moves on to) and writes the
map group 0x24 into sRoamerLocation (0x0203BC86: group, map). That group byte is all that says "Sinnoh": the
hack's RoamerMoveToOtherLocationSet (0x09F062D0) and RoamerMove (0x09F06340) pick the Sinnoh table when it is not
0, the News Tracker (item 695, 0x09F063F0) names the region by it, and IsRoamerAt (0x08161DE8) compares it with
the map you are on. sRoamerLocation is not in the save. After Continue it is 0, the first move picks from the
Hoenn table, and from then on the storm roams Hoenn: the tracker says "in Hoenn on Route 130", and that is where
it is met, while the researcher, the Quest Log and the guide say Sinnoh.

Measured (test_roamfix.lua, the game's late-game save): started by the researcher it is on a Sinnoh route, the
tracker names that route, it is met there one battle in four (Lv 40) and moves on; after a save, a reset and
Continue the same roamer is at 0/45, "in Hoenn on Route 130".

The fix: the two words the game's trampolines hold (0x08161D04 -> RoamerMoveToOtherLocationSet, 0x08161D58 ->
RoamerMove) point at two stubs (roamfix.s) that first write the group 0x24 if the roamer is active and its species
is 694 or 695, then go on to the hack's routines. Continue moves the roamer once (that is how it came to be on a
Hoenn route at once), so from the first frame after loading it is on a Sinnoh route again. Latias and Latios are
not touched. The save is not touched.
Code: 88 bytes at 0x08FEF700, in the unreferenced 0xFF run after objpal (0x08FEF684..0x08FEFE00).
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

SET_TRAMP, SET_FN = 0x08161D00, 0x09F062D1      # ldr r0, [pc, #0]; bx r0; .word -> RoamerMoveToOtherLocationSet
MOVE_TRAMP, MOVE_FN = 0x08161D54, 0x09F06341    # the same -> RoamerMove
TRAMP = bytes.fromhex("00480047")
SET_WAS = bytes.fromhex("f0b5474680b4134c")     # push {r4-r7, lr}; mov r7, r8; push {r7}; ldr r4, =sRoamerLocation
MOVE_WAS = bytes.fromhex("f0b54746224c80b4")    # push {r4-r7, lr}; mov r7, r8; ldr r4, =Random; push {r7}
CREATE = 0x09F06118                             # the hack's CreateInitialRoamerMon: species 0x2B6 / 0x2B7, group 0x24
FREE, FREE_END = 0x00FEF700, 0x00FEF7F0         # (words in graphics data happen to read 0x08FEF6F9 and 0x08FEF7F8)


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (
        addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    assert not [i for i in dis if i.mnemonic == "nop"], "a Thumb-2 nop (00 BF) slipped in: use mov r8, r8"
    return code, dis


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, b: bytes(rom[o(a):o(a) + len(b)]) == b

    # the game's two trampolines into the hack's routines, and those routines, as they are
    assert at(SET_TRAMP, TRAMP) and u32(SET_TRAMP + 4) == SET_FN, "RoamerMoveToOtherLocationSet's trampoline changed (already applied?)"
    assert at(MOVE_TRAMP, TRAMP) and u32(MOVE_TRAMP + 4) == MOVE_FN, "RoamerMove's trampoline changed (already applied?)"
    assert at(SET_FN - 1, SET_WAS) and at(MOVE_FN - 1, MOVE_WAS), "the hack's roamer routines changed"
    # the species and the group the fix goes by: what the hack's CreateInitialRoamerMon writes for modes 2 and 3
    # (movs r3, #0x24; mov r2, r8; strb r3, [r2]; ldr r3, =species: mode 3 at 0x09F0625A, mode 2 at 0x09F06266)
    assert at(0x09F0625A, bytes.fromhex("242342461370194b")) and at(0x09F06266, bytes.fromhex("242342461370174b")),         "the hack's Tornadus / Thundurus branches changed"
    assert u32(0x09F062C8) == 0x2B7 and u32(0x09F062CC) == 0x2B6, "the roamers' species are not 695 and 694"
    assert u32(0x09F06274) == 0x0203BC86 and u32(0x09F0633C) == 0x09F0AAC8 and u32(0x09F063E0) == 0x09F0AAC8,         "sRoamerLocation or the Sinnoh table moved"

    base = 0x08000000 + FREE
    src = open(os.path.join(HERE, "roamfix.s"), encoding="ascii").read()
    for pad in ("", "    mov r8, r8"):
        s = src.replace("PAD", pad).replace("SET_ADDR", hex(SET_FN)).replace("MOVE_ADDR", hex(MOVE_FN))
        code, dis = thumb(s, base)
        if (len(code) - 24) % 4 == 0:
            break
    else:
        raise AssertionError("roamfix's pool")
    assert struct.unpack_from("<6I", code, len(code) - 24) == (SET_FN, MOVE_FN, 0x03005D8C, 0x31DC, 694, 0x0203BC86)
    pushes = [i.address for i in dis if i.mnemonic == "push"]
    assert len(pushes) == 2 and pushes[0] == base, "expected the two stubs, set_stub first"
    set_stub, move_stub = pushes
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not base <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code
    struct.pack_into("<I", rom, o(SET_TRAMP + 4), set_stub | 1)
    struct.pack_into("<I", rom, o(MOVE_TRAMP + 4), move_stub | 1)
    open(outp, "wb").write(rom)
    print("roamfix: set_stub %08X, move_stub %08X, end %08X; the trampolines at %08X and %08X go through them" % (
        set_stub, move_stub, 0x08000000 + end, SET_TRAMP, MOVE_TRAMP))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
