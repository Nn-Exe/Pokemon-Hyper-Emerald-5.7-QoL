"""Move effectiveness indicator (Hyper Emerald v5.7). Apply after the typeicons build.
usage: python typeeff_patch.py <in.gba> <out.gba>

In battle, the move list's "Type/xxx" line gains the damage multiplier of the highlighted move against the
opposing Pokemon - x0, x.25, x.5, x1, x2, x4 - updated as the cursor moves. Status moves show nothing.

It reads the hack's own type chart (19x19 at 0x09D76E88, values 0/5/10/20, with type ids over 22 packed down
by 5 so Fairy 23 -> 18), found by watching which code reads the defender's types during an attack, so the
numbers match what the game actually does. Abilities (Levitate, Wonder Guard), items and inverse battles are
not taken into account - it is a type chart readout, like the SoulSilver-style hacks.

ROM change: the tail of MoveSelectionDisplayMoveType (0x08059C02: bl BattlePutTextOnWindow / pop {r4,r5,r6} /
pop {r0} / bx r0, 10 bytes) becomes an absolute jump to new code in free space, which ends with that same
epilogue. An absolute jump rather than a bl because the free space is 16 MB away, well out of bl range.
"""
import struct, sys, os, re
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FDB9E4
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

HOOK = 0x059C02
HOOK_EXPECT = "f5f0f3fe" + "70bc" + "01bc" + "0047"      # bl 0x814F9EC; pop {r4,r5,r6}; pop {r0}; bx r0
HOOK2 = 0x05783C                                         # HandleInputChooseTarget, after the cursor args
HOOK2_EXPECT = "e2f7f4f9" + "0024" + "1248"              # bl 0x8039C28; movs r4,#0; ldr r0,[pc,#0x48]
CHART = 0x09D76E88
CHART_SPOT = {(0, 7): 0, (11, 10): 20, (10, 11): 5, (0, 0): 10, (18, 16): 20, (16, 18): 0, (14, 17): 0}

# "x<mult> " prefixes (they go before the "PP" label), in the order the code indexes them
DIGIT = {c: 0xA1 + i for i, c in enumerate("0123456789")}
RED, ORANGE, GREEN, YELLOW, BLACK, DEFAULT = 1, 3, 5, 6, 7, 12   # entries of the move box's palette (BG 5)
def txt(s, colour):
    out = bytearray((0xFC, 0x01, colour, 0xB9))          # set colour, multiplication sign
    for ch in s:
        out.append(DIGIT[ch] if ch.isdigit() else 0xAD)  # '.' is 0xAD
    return bytes(out) + bytes([0xFC, 0x01, DEFAULT, 0x00, 0xFF])   # restore, space, terminator
SUFFIXES = [txt("0", BLACK), txt(".25", YELLOW), txt(".5", YELLOW), txt("1", GREEN),
            txt("2", ORANGE), txt("4", RED), bytes([0xFF])]


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(__import__("re").sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 nop\n    nop", src, flags=8), addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert rom[HOOK:HOOK + 10].hex() == HOOK_EXPECT, "MoveSelectionDisplayMoveType tail differs: %s" % rom[HOOK:HOOK + 10].hex()
    assert rom[HOOK2:HOOK2 + 8].hex() == HOOK2_EXPECT, "HandleInputChooseTarget differs: %s" % rom[HOOK2:HOOK2 + 8].hex()
    for (a, d), want in CHART_SPOT.items():
        got = rom[CHART - 0x08000000 + a * 19 + d]
        assert got == want, "type chart at (%d,%d) is %d, expected %d" % (a, d, got, want)

    src = open(os.path.join(HERE, "typeeff.s"), encoding="ascii").read()
    code = thumb(src.replace("STRTAB_ADDR", "0x%08X" % BASE), BASE)
    code_len = (len(code) + 3) & ~3
    tab_addr = BASE + code_len
    data = bytearray(struct.pack("<7I", *[0] * 7))
    pos = len(data)
    addrs = []
    for s in SUFFIXES:
        addrs.append(tab_addr + pos); data += s; pos = len(data)
    struct.pack_into("<7I", data, 0, *addrs)
    code = thumb(src.replace("STRTAB_ADDR", "0x%08X" % tab_addr), BASE)
    assert (len(code) + 3) & ~3 == code_len
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, BASE))
    pushes = [i.address for i in dis if i.mnemonic == "push" and i.op_str == "{r4, r5, r6, r7, lr}"]
    stub = pushes[1]                       # main, stub, build_pp, effect
    print("  stub (target hook) at %08X" % stub)

    blob = bytearray(code) + bytes(code_len - len(code)) + data
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    rom[HOOK:HOOK + 6] = bytes.fromhex("014b18 47c046".replace(" ", ""))   # ldr r3,[pc,#4]; bx r3; nop
    struct.pack_into("<I", rom, HOOK + 6, BASE | 1)
    rom[HOOK2:HOOK2 + 4] = bytes.fromhex("004b1847")                       # ldr r3,[pc,#0]; bx r3
    struct.pack_into("<I", rom, HOOK2 + 4, stub | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, suffix table @%08X, end %08X" % (len(code), BASE, tab_addr, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
