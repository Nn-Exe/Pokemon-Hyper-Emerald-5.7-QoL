"""Both bikes at once (Hyper Emerald v5.7). Apply after the typeeff build.
usage: python bothbikes_patch.py <in.gba> <out.gba>

Vanilla gives you one bike and Rydel in Rustboro swaps it for the other. This hands you the second bike the
moment you are in the overworld owning the first, so both live in the Key Items pocket at once - use or
register either one to switch to that bike (the two items share a field-use routine and differ only by a
secondary id: Mach 0, Acro 1). Works on an existing save; nothing is given before you own a bike, and once
you own both the check does nothing.

ROM change: the first four instructions of CB2_Overworld (0x08085E5C, through the gPaletteFade read)
become a jump to new code in free space, which replays them and returns. An absolute jump because free space
is 16 MB away, out of bl range.
"""
import struct, sys, os, re
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FDBC2C
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

HOOK = 0x085E5C
HOOK_EXPECT = "10b50948c079c009"    # push {r4,lr}; ldr r0,[pc,#0x24]; ldrb r0,[r0,#7]; lsrs r0,r0,#7
ITEMS = 0xFC2C7C                    # item table, 44-byte entries
MACH, ACRO = 259, 272


def item_name(rom, i):
    b = rom[ITEMS + i * 44:ITEMS + i * 44 + 14]
    out = ""
    for c in b:
        if c == 0xFF: break
        out += chr(ord('A') + c - 0xBB) if 0xBB <= c <= 0xD4 else chr(ord('a') + c - 0xD5) if 0xD5 <= c <= 0xEE else " "
    return out.strip()


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 nop\n    nop", src, flags=re.M), addr)[0])
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert rom[HOOK:HOOK + 8].hex() == HOOK_EXPECT, "CB2_Overworld prologue differs: %s" % rom[HOOK:HOOK + 8].hex()
    for i, want in ((MACH, "Mach Bike"), (ACRO, "Acro Bike")):
        got = item_name(rom, i)
        assert got == want, "item %d is %r, expected %r" % (i, got, want)
        e = ITEMS + i * 44
        assert struct.unpack_from("<I", rom, e + 28)[0] == 0x080FD299, "bike %d has an unexpected field-use routine" % i
        assert struct.unpack_from("<I", rom, e + 40)[0] == (0 if i == MACH else 1), "bike %d secondary id differs" % i

    src = open(os.path.join(HERE, "bothbikes.s"), encoding="ascii").read()
    code = thumb(src, BASE)
    end = FREE + len(code)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = code

    rom[HOOK:HOOK + 4] = bytes.fromhex("004b1847")            # ldr r3, [pc, #0]; bx r3
    struct.pack_into("<I", rom, HOOK + 4, BASE | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, end %08X" % (len(code), BASE, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
