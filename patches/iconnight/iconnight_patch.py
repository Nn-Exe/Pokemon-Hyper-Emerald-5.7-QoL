"""Pokemon icons keep their own colours in the evening and at night (Hyper Emerald v5.7). Apply after contexit,
before kitakami (anywhere in the chain works: no other step touches these bytes; kitakami hooks the same tint
routine at 0x08CFE3EA and 0x08CFE472, not its way out).
usage: python iconnight_patch.py <in.gba> <out.gba>

A report (2026-10-21): "sprites are still buggy in dexnav (sunkern spearow)", from Route 104, where both are in the
grass (slots 5 and 7). On the user's save the DexNav screen and the search bar were right at noon; from 17:00 on the
bar's icon was not: Sunkern red-orange at 19:00, dark blue at 23:00, on the bar's untinted black
(_testrun/dnstars, test_dnlook.lua with HOUR=).

Why: the hack tints the screen for the hour inside TransferPlttBuffer (NOTES, *Day/Night*): its routine at
0x08CFE3E0 copies gPlttBufferFaded to palette RAM with colour channels halved, for the palettes of the mask
0xFFFF0FFF - BG 0-11 and every sprite palette; BG 12-15 (the message boxes, the DexNav bar's window) are left
alone. The bar's Pokemon icon is a sprite with a Pokemon icon palette (LoadMonIconPalette: tag 0xDAC0 + the
species' icon palette, gMonIconPaletteTable 0x0857C540), so it was tinted while its box was not. The DexNav screen
itself is not tinted.

What this does (iconnight.s): the routine's one way out, tinted or not, is the word 0x08CFE4D4 = 0x080A19E7 (back
into TransferPlttBuffer; no other word of the ROM holds it). It points to icon_untint, which copies the 16 colours of
every sprite palette slot tagged 0xDAC0..0xDAC5 from gPlttBufferFaded to palette RAM again, as they were before the
tint, then goes back. Icons are never part of the world, so this is right wherever one is drawn; everything else
is tinted as before.
Code: 0x08FFA200.. (0x08FFA200..0x08FFA300 kept), after contexit's, in the same blank run (see contexit_patch.py).
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

FREE, FREE_END = 0x00FFA200, 0x00FFA300
BASE = 0x08000000 + FREE
LIT, LIT_WAS = 0x08CFE4D4, 0x080A19E7            # the tint routine's way back into TransferPlttBuffer
EXPECT = [
    # TransferPlttBuffer: unless the transfer is held, DMA3 from gPlttBufferFaded to 0x05000000, the hack's jump
    # (ldr r1, =0x08CFE3E1; bx r1); back at 0x080A19E6
    (0x080A19C0, "30b5114c217a8025281c08400006030e002b16d10d49a022d2040d48016042600c4908478068"),
    (0x080A1A08, "d47f0302147b0302d4000004e1e3cf08e47f0302"),   # its pool: gPaletteFade, gPlttBufferFaded, ...
    (0x08CFE406, "ffbc314932480047"),            # the tint's end: pop {r0-r7}; ldr r1, =0x80000200; ldr r0, =<LIT>
    # GetSpritePaletteTagByPaletteNum: slot n's tag is the halfword at 0x03000CF0 + 2n
    (0x0800883C, "00060249c00d401800887047f00c0003"),
    # LoadMonIconPalettes: the six of gMonIconPaletteTable (0x0857C540)
    (0x080D2F04, "30b50024064de000401935f719fc601c0006040e052cf6d930bc01bc0047000040c55708"),
]
ICON_TABLE, ICON_TAG = 0x0857C540, 0xDAC0


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
    src = open(os.path.join(HERE, "iconnight.s"), encoding="ascii").read()
    for pad in ("", "    mov r8, r8"):       # the pool on a word without the assembler's own (Thumb-2) padding
        try:
            return thumb(src.replace("PADA", pad), BASE)
        except AssertionError as e:
            if "nop" not in str(e):
                raise
    raise AssertionError("iconnight's pool")


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    for a, hexs in EXPECT:
        assert bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs), \
            "the game's code at %08X is not as expected" % a
    tags = [struct.unpack_from("<H", rom, o(ICON_TABLE) + 8 * i + 4)[0] for i in range(6)]
    assert tags == [ICON_TAG + i for i in range(6)], "the icon palettes' tags are %s" % tags
    lit = struct.unpack_from("<I", rom, o(LIT))[0]
    assert lit == LIT_WAS, "the tint routine's way out is %08X (already applied?)" % lit
    held = [0x08000000 + m.start() for m in re.finditer(re.escape(struct.pack("<I", LIT_WAS)), bytes(rom))]
    assert held == [LIT], "the way back is held elsewhere too: %s" % ["%08X" % a for a in held]

    code = assemble()
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:FREE_END]) == {0xFF}, "target region not free"
    for m in re.finditer(rb"(?s).[\xa2-\xa3]\xff\x08", bytes(rom)):     # at any byte offset, not only words
        v = struct.unpack_from("<I", rom, m.start())[0]
        assert not BASE <= v < 0x08000000 + FREE_END, "%08X reads as an address in the target (%08X)" % (
            0x08000000 + m.start(), v)
    rom[FREE:end] = code
    struct.pack_into("<I", rom, o(LIT), BASE | 1)
    open(outp, "wb").write(rom)
    print("iconnight: %08X..%08X, the tint's way out at %08X" % (BASE, 0x08000000 + end, LIT))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
