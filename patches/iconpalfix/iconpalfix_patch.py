"""The DexNav search bar's icon in its own colours (Hyper Emerald v5.7).
usage: python iconpalfix_patch.py <in.gba> <out.gba>

Reported 2026-10-15 on the whole Gen 9 test ("dexnav scan, sometimes mostly the pokemon img color is kinda
inverted especially on gen9"); the fault is the main game's as well. The bar (dexnavchain) loads its icon's
palette with LoadMonIconPalette (0x080D2F28; the bar is its only user in the ROM: one literal, 0x08FDF034) and
makes the icon with CreateMonIcon. LoadMonIconPalette still has vanilla Emerald's clamp - a species above 412
(NUM_SPECIES) is taken as species 260 (INVALID_ICON_SPECIES), whose icon palette is 1 - while CreateMonIcon and
FreeMonIconPalette read the real species (the hack removed their clamps). So for every species above 412 whose
icon palette is 0 or 2 (all of Gen 9 is above 412) the bar loaded palette 1 under its own tag, the icon (asking
for a tag nobody loaded) drew with that slot's colours, and the palette was never freed. Measured on Route 102:
Nymble (palette 0) in the slot tagged 0xDAC1 (palette 1).
Fix: the clamp's `bls` becomes `b` - the real species, as the other two functions do. Two bytes.
"""
import struct, sys

SITE = 0x000D2F34
FUNC = 0x000D2F28
# push {r4,lr}; lsls r0,r0,#16; lsrs r1,r0,#16; movs r0,#0xCE; lsls r0,r0,#1; cmp r1,r0; bls +2; movs r1,#0x82; lsls r1,r1,#1
ORIG = "10b50004010cce2040008142" + "01d9" + "82214900"
NEW = "01e0"                                     # b 0x080D2F3A


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert rom[FUNC:FUNC + len(ORIG) // 2] == bytes.fromhex(ORIG), "LoadMonIconPalette is not what it was (applied already?)"
    # the palette-id table it reads is the one the ROM header names (whatever species patch moved it)
    assert struct.unpack_from("<I", rom, FUNC + 0x38)[0] == struct.unpack_from("<I", rom, 0x13C)[0], "its palette-id table"
    rom[SITE:SITE + 2] = bytes.fromhex(NEW)
    open(outp, "wb").write(rom)
    print("iconpalfix: LoadMonIconPalette (0x080D2F28) takes the real species above 412 (0x080D2F34: bls -> b)")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
