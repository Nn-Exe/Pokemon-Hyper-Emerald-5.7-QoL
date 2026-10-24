"""A wild Pokemon keeps the item it was given before the battle (Hyper Emerald v5.7). Apply after gen9journal,
before kitakami (anywhere in the chain works: no other step touches these bytes).
usage: python wilditem_patch.py <in.gba> <out.gba>

A report (2026-10-18): "Light ball is not attached to pikachu when fighting him in the abandoned ship. An Oran berry
is in its place." The Pikachu (Abandoned Ship 24/56, object 2, script 0x098B96CB) is a scripted wild battle:
`setwildbattle 25, 34, 0xCA` - Lv 34 holding item 202, the Light Ball. Then, as every battle is set up, the game's
SetWildMonHeldItem (0x0806EA68, called from 0x080369E4 and from the hack's 0x08FF10C0) rolls the wild Pokemon's
item without looking whether it holds one: unless the battle is a trainer's, a legendary one, the Pyramid's or the
Pike's (gBattleTypeFlags & 0x302008), 45 in 100 it leaves the item, 50 gives the species' common item, 5 the rare
one (with Compound Eyes - in this hack also abilities 28 and 105 - in the lead: 20 / 60 / 20). Pikachu's two are
Oran Berry (common) and Light Ball (rare), base stats +12 / +14 at 0x09AC0000 + 25 * 28: so the Light Ball became
an Oran Berry about half the time. A species with no wild items lost the script's item to nothing 55 in 100.
Vanilla Emerald never gives a scripted Pokemon an item, so it never showed there; this hack has 48 such battles
(tools/romdata/scan_static.py: the Z-Crystal Pokemon of the Secret Bases, Giratina's Griseous Orb, Area Zero's
Leftovers, Kitakami's Black Sludge, ...). DexNav's rolled item (dexnavchain's apply_extras, mon +0x22) was
overwritten the same way: NOTES had "the game's own wild held-item roll still runs after ours".

What this does (wilditem.s): at 0x0806EA7C, right after the battle-type test, where the function was about to call
Random16, an 8-byte trampoline goes to keep_item: a Pokemon that already holds an item goes to the function's end
(0x0806EB90), any other gets the roll as before (Random16 is called there, and it goes on at 0x0806EA84). Ordinary
wild Pokemon are made with no item, so for them nothing changes.
Code: 0x08FF9800.. (60 bytes; 0x08FF9800..0x08FF9900 kept), inside the blank run 0x08FF8CEE..0x08FFD5A0: blank in
the hack's own ROM too, and no word anywhere in the game reads as an address inside it at any byte offset
(_testrun/space/kitakami_space.py, 2026-10-18).
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

FREE, FREE_END = 0x00FF9800, 0x00FF9900
BASE = 0x08000000 + FREE
SITE = 0x0806EA7C                                # bl Random16; lsls r0, #16; lsrs r0, #16 (4-aligned)
SITE_WAS = "00f0a6fd0004000c"
FUNC, FUNC_WAS = 0x0806EA68, "f0b5474680b41f4800681f490840002800d089e0"   # prologue + the battle-type test
TAIL, TAIL_WAS = 0x0806EB90, "08bc9846f0bc01bc0047"                        # pop r8, r4-r7, pc
POOL, POOL_WAS = 0x0806EAEC, "ec2f02020820300044470202"                    # gBattleTypeFlags, 0x302008, gEnemyParty
TRAMP = bytes.fromhex("004b1847")                # ldr r3, [pc, #0]; bx r3; .word


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
    return code


def assemble():
    src = open(os.path.join(HERE, "wilditem.s"), encoding="ascii").read()
    for pad in ("", "    mov r8, r8"):       # the pool on a word without the assembler's own (Thumb-2) padding
        try:
            return thumb(src.replace("PADA", pad), BASE)
        except AssertionError as e:
            if "nop" not in str(e):
                raise
    raise AssertionError("wilditem's pool")


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert at(SITE, SITE_WAS), "SetWildMonHeldItem's call to Random16 is not as expected (already applied?)"
    assert at(FUNC, FUNC_WAS), "SetWildMonHeldItem's prologue / battle-type test is not as expected"
    assert at(TAIL, TAIL_WAS), "SetWildMonHeldItem's end is not as expected"
    assert at(POOL, POOL_WAS), "SetWildMonHeldItem's pool is not as expected"
    assert at(0x0806EB6E, "0c21fcf79cf8"), "SetWildMonHeldItem no longer sets field 12 (the held item)"

    code = assemble()
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:FREE_END]) == {0xFF}, "target region not free"
    for m in re.finditer(rb"(?s).[\x98\x99]\xff\x08", bytes(rom)):     # at any byte offset, not only words
        v = struct.unpack_from("<I", rom, m.start())[0]
        assert not BASE <= v < 0x08000000 + FREE_END, "%08X reads as an address in the target (%08X)" % (
            0x08000000 + m.start(), v)
    rom[FREE:end] = code
    rom[o(SITE):o(SITE) + 8] = TRAMP + struct.pack("<I", BASE | 1)
    open(outp, "wb").write(rom)
    print("wilditem: %08X..%08X, trampoline at %08X" % (BASE, 0x08000000 + end, SITE))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
