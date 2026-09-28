"""Red squares on the Hoenn Fly map for every place you can fly to (Hyper Emerald v5.7). Apply after ovalcharm.
usage: python flyicons_patch.py <in.gba> <out.gba>

The Fly map marks towns with the dots the region map draws, and "special areas" with a red-outlined square
sprite: CreateSpecialAreaFlyTargetIcons (vanilla) walks sRedOutlineFlyDestinations, pairs of {flag, map
section} ended by {0xFFFF, MAPSEC_NONE 0xD5}, and draws the square for each pair whose flag is set. In this
hack that table (0x085A1F18) still holds only the Battle Frontier.

The hack lets you fly to more places than that. Its GetMapsecType (0x08123D58) reads a flag per map section
from 0x08C4CFA0 and allows Fly when it is set; besides the towns those are the Battle Frontier (0x8A8),
Champion Island (0x419C), Southern Island (0x8A9), Strange Island (0x4178) and Steven's Island (0x4150). The
last four could be flown to but showed nothing, so players did not know.

This writes a longer table in free space - the same flag the Fly check uses for each place, so a square
appears exactly when A would fly you there - and repoints the one word that reads it (0x08124CAC). The
list is read from the hack's own flag table, not typed in, and each is checked to be a special area (not
a town, which has its own dot).
"""
import struct, sys

FREE = 0x00FF5A00                               # in the unreferenced 0xFF run 0x08FF591A..0x08FFD5A0
OLD_TABLE = 0x085A1F18
TABLE_LITERAL = 0x08124CAC
FLY_FLAGS = 0x08C4CFA0                          # the hack's GetMapsecType: u16 flag per map section
MAPSEC_NONE = 0xD5
LAST_TOWN = 0x0F                                # Littleroot .. Ever Grande: the region map draws their dots
SPECIAL = {0x3A: "Battle Frontier", 0x45: "Champion Island", 0x49: "Southern Island",
           0x71: "Strange Island", 0x9E: "Steven's Island"}


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    assert struct.unpack_from("<I", rom, o(TABLE_LITERAL))[0] == OLD_TABLE, "the Fly map reads another table"
    assert bytes(rom[o(OLD_TABLE):o(OLD_TABLE) + 8]) == bytes.fromhex("a8083a00ffffd500"), "the table changed"
    assert struct.unpack_from("<I", rom, 0x123D9C)[0] == FLY_FLAGS, "GetMapsecType reads another table"

    pairs = []
    for sec in range(MAPSEC_NONE):
        flag = struct.unpack_from("<H", rom, o(FLY_FLAGS) + sec * 2)[0]
        if flag in (0, 0xFFFF) or sec <= LAST_TOWN:
            continue
        assert sec in SPECIAL, "section 0x%X (flag 0x%X) can be flown to and is not known here" % (sec, flag)
        pairs.append((flag, sec))
    assert pairs[0] == (0x8A8, 0x3A), "the Battle Frontier should stay first"
    table = b"".join(struct.pack("<HH", f, s) for f, s in pairs) + struct.pack("<HH", 0xFFFF, MAPSEC_NONE)

    assert set(rom[FREE:FREE + len(table)]) == {0xFF}, "target region not free"
    rom[FREE:FREE + len(table)] = table
    struct.pack_into("<I", rom, o(TABLE_LITERAL), 0x08000000 + FREE)
    open(outp, "wb").write(rom)
    print("table @%08X: %s" % (0x08000000 + FREE, ", ".join("%s (flag 0x%X)" % (SPECIAL[s], f) for f, s in pairs)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
