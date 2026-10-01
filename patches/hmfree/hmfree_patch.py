"""Field moves without a Pokemon that can learn them (Hyper Emerald v5.7). Apply last.

From PR #2 (@anibalribeiro) on the public repo; taken on its own, without the party editor and the TM shop, so the
party-menu hook chains to whatever the builder trampoline points at (the relearner's hook, or partyedit's).

* Obstacles: the hack's field-move routine 0x08FF1BA0 (Cut, Strength, Rock Smash, Surf, Waterfall, Dive and
  Rock Climb scripts) gets an 8-byte trampoline at its entry. The new code runs the original, and when no party
  Pokemon can learn the move, the move is an HM move and that HM is in the Bag, it names the first non-egg
  Pokemon instead. Badges are still checked where the game checks them. Rock Climb has no HM and is unchanged.
* Party menu: a new first link in the field-action builder chain (trampoline at 0x081B3518, currently
  the relearner's hook, or partyedit's when that is in) offers Flash with HM05 + badge 2 on a dark map not yet
  lit. (The PR also offered Fly on every Pokemon with HM02 + badge 6; taken out 2026-09-30 at the user's request -
  the ride pager and the map fly you. A Pokemon that knows Fly still shows it, as in the game.)

New code and an 8-entry move table in free space; nothing written to the save or to EWRAM.

usage: python hmfree_patch.py <in.gba> <out.gba>
"""
import os, re, struct, sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0xF54500                         # the run 0x08F53700..0x08F54AA0, where tmshop's list would end (..0x08F544E6)
BASE = 0x08000000 + FREE
FM = 0xFF1BA0                           # the hack's field-move routine
FM_HEAD = bytes.fromhex("f0b51f4d2d881f4f")   # push {r4-r7,lr}; ldr r5,[pc]; ldrh r5,[r5]; ldr r7,[pc]
FM_LITS = {0xFF1C20: 0x020375E0, 0xFF1C24: 0x09E0FE80}
HOOK = 0x1B3518                         # builder trampoline: ldr r3,[pc]; bx r3; .word
KNOWN_HEADS = {0x08FD9B01: "the relearner's builder_hook", 0x08F53901: "partyedit's builder_hook"}
MOVETABLE = 0x1E0FE80                   # 128 moves: TM01-120, HM01-08
HM_MOVES = (15, 19, 57, 70, 148, 249, 127, 291)   # Cut Fly Surf Strength Flash RockSmash Waterfall Dive
HM01 = 498
ITEMS_PTR = 0x1C8
CODE_SYMS = ("offer", "fm_entry", "fm_orig", "first_mon")   # functions with a `push`, in order
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (
        addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    assert not any(i.bytes == b"\x00\xbf" for i in dis), "nop (00 BF) emitted"
    return code, dis


def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000, "not the 32 MB BPEE ROM"
    assert rom[FM:FM + 8] == FM_HEAD, "field-move routine at %08X changed" % (0x08000000 + FM)
    for o, v in FM_LITS.items():
        assert u32(rom, o) == v, "literal @%08X is %08X, expected %08X" % (0x08000000 + o, u32(rom, o), v)
    assert rom[HOOK:HOOK + 4] == bytes.fromhex("004b1847"), "builder trampoline missing"
    prev = u32(rom, HOOK + 4)                  # chain, never replace: run whoever is there after pm_hook
    assert prev in KNOWN_HEADS, "builder chain starts at %08X, not a hook this patch knows" % prev
    items = u32(rom, ITEMS_PTR) - 0x08000000
    for k, mv in enumerate(HM_MOVES):
        assert struct.unpack_from("<H", rom, MOVETABLE + (120 + k) * 2)[0] == mv, "HM%02d is not move %d" % (k + 1, mv)
        name = bytes(rom[items + (HM01 + k) * 44:][:5])
        assert name == bytes((0xC2, 0xC7, 0x00, 0xA1, 0xA2 + k)), "item %d is not HM%02d" % (HM01 + k, k + 1)

    src = open(os.path.join(HERE, "hmfree.s"), encoding="ascii").read()

    def assemble(addrs):
        s = src
        for k, v in addrs.items():
            s = s.replace(k + "_ADDR", "0x%08X" % v)
        return thumb(s, BASE)

    code, dis = assemble({"PREV": prev, "HM_MOVES": 0})
    prologues = [i.address for i in dis if i.mnemonic == "push"]
    assert len(prologues) == len(CODE_SYMS), "unexpected layout: %d prologues" % len(prologues)
    sym = dict(zip(CODE_SYMS, prologues))
    code_len = (len(code) + 3) & ~3
    table_addr = BASE + code_len
    code2, _ = assemble({"PREV": prev, "HM_MOVES": table_addr})
    assert len(code2) == len(code), "code length changed between passes"

    blob = code2 + bytes(code_len - len(code2)) + b"".join(struct.pack("<H", m) for m in HM_MOVES)
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    rom[FM:FM + 8] = bytes.fromhex("004b1847") + struct.pack("<I", sym["fm_entry"] | 1)
    struct.pack_into("<I", rom, HOOK + 4, BASE | 1)
    open(outp, "wb").write(rom)
    print("code %d B @%08X, HM moves @%08X, end %08X" % (len(code2), BASE, table_addr, 0x08000000 + end))
    print("   pm_hook        %08X  (builder chain -> %08X, %s)" % (BASE | 1, prev, KNOWN_HEADS[prev]))
    for n, a in sym.items():
        print("   %-14s %08X" % (n, a | 1))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    build(sys.argv[1], sys.argv[2])
