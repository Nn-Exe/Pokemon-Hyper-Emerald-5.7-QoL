"""Granite Cave: no cracked floor that drops you into rock (Hyper Emerald v5.7): python granitefall_patch.py in.gba out.gba

Reported 2026-10-22 (two screenshots): "in granite cave, there is spot bug / Falling here will result in being
stuck inside the wall."

Granite Cave B1F (map 24/8) has 67 cracked floor tiles (block 0x322F: metatile 0x22F, behaviour 0xD2, elevation 3).
Its resume script (0x0822DC6E) sets the cracked-floor step callback and `setholewarp 24/9`: stepping on one at less
than the Mach Bike's top speed drops you to B2F (24/9) on the same x, y. Four of them are over rock there:
  (8, 1), (8, 2)  B2F 0x1610 / 0x1618: the rock spur from the north wall (the report's spot), elevation 1;
  (25, 6)         B2F 0x1608: the east wall's edge, elevation 1;
  (20, 3)         B2F 0x3650: a lone rock, elevation 3.
On the first three you land at elevation 1 among elevation-3 floor and cannot move; on the fourth you stand inside a
rock. Every part of B2F under them is reached from the cracked tiles beside them, so the four become plain floor
(0x3201, the floor around them): you walk over them, as over any floor. Every other map with a hole warp was checked
(24/16, 24/80, 24/82, 24/95, 24/96, 37/50): no cracked tile there lands on a blocked tile.
"""
import struct, sys

MAP_GROUPS = 0x00A54698
B = 0x08000000
B1F, B2F = (24, 8), (24, 9)
CRACKED, FLOOR = 0x322F, 0x3201
SPOTS = {(8, 1): 0x1610, (8, 2): 0x1618, (20, 3): 0x3650, (25, 6): 0x1608}     # B1F tile: the block below it on B2F
HOLE_SCRIPT = (0x0022DC6E, bytes.fromhex("a6074118 09ff0000 000002"))   # setstepcallback 7; setholewarp 24/9; end


def u32(rom, o):
    return struct.unpack_from("<I", rom, o)[0]


def blocks(rom, g, n):
    hdr = u32(rom, u32(rom, MAP_GROUPS + 4 * g) - B + 4 * n) - B
    lay = u32(rom, hdr) - B
    return u32(rom, lay), u32(rom, lay + 4), u32(rom, lay + 12) - B, lay


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    at, want = HOLE_SCRIPT
    assert bytes(rom[at:at + len(want)]) == want, "B1F's hole warp is not to 24/9"
    w, h, data, lay = blocks(rom, *B1F)
    w2, h2, data2, _ = blocks(rom, *B2F)
    assert (w, h, w2, h2) == (32, 26, 32, 26), "the two floors are not 32 x 26"
    held = [o for o in range(0, len(rom), 4) if u32(rom, o) == data + B]
    assert held == [lay + 12], "B1F's blocks are held elsewhere too: %s" % ["%08X" % (B + o) for o in held]
    for (x, y), below in SPOTS.items():
        assert struct.unpack_from("<H", rom, data + 2 * (y * w + x))[0] == CRACKED, "B1F (%d, %d)" % (x, y)
        assert struct.unpack_from("<H", rom, data2 + 2 * (y * w2 + x))[0] == below, "B2F (%d, %d)" % (x, y)
        struct.pack_into("<H", rom, data + 2 * (y * w + x), FLOOR)
    open(outp, "wb").write(rom)
    print("granitefall: Granite Cave B1F %s plain floor (blocks at %08X)" % (sorted(SPOTS), data + B))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
