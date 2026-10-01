"""DexNav: list only what the game uses on this map (Hyper Emerald v5.7). Apply after dexnav (anywhere later).
usage: python dexnavscan_patch.py <in.gba> <out.gba>

The DexNav's find_header (patches/dexnav) looked the current map up by group/number in two tables: the hack's
encounter table 0x08E17D50 and 0x08553894, taken at the time for "a seven-city extra table". 0x08553894 is the
Battle Pyramid's table (gBattlePyramidWildMonHeaders): StandardWildEncounter and SweetScentWildEncounter read it
only when the map layout is the Pyramid floor (0x169), indexed by the challenge number; its seven entries carry
leftover map numbers 0/1..0/7 - Slateport, Mauville, Rustboro, Fortree, Lilycove, Mossdeep, Sootopolis - so those
cities showed a Land list (the Bulbasaur / Charmander / Squirtle lines) the game never gives there, and a DexNav
search could make one appear (Mauville has grass and no encounters at all). Also, in Altering Cave the game adds
VAR 0x403E to the header index (nine sets), which find_header ignored.
Now find's `bl find_header` (0x08FDA7A2, its only caller) goes to map_header (dexnavscan.s), which returns the
header GetCurrentMapWildMonHeaderId (0x080B4CF8) picks - the same call every wild encounter makes - for table 0,
and nothing for table 1.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavseen"))
import sinnohmap_patch as SM                    # the Thumb check
from dexnavseen_patch import bl, bl_target

FREE = 0x00FF6C80                               # in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, after dexnavseen
FREE_END = 0x00FF7700                           # (..0x08FF6C46); a data word happens to read 0x08FF7703
BASE = 0x08000000 + FREE

FIND_CALL, FIND_HEADER = 0x08FDA7A2, 0x08FDA760
GET_HEADER_ID, ITS_TABLE_LIT = 0x080B4CF8, 0x080B4D48
DEXNAV_TABLES = 0x08FDA934                      # find_header's two table words
PYRAMID = 0x08553894


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    headers = u32(ITS_TABLE_LIT)
    assert at(GET_HEADER_ID, "70b50024") and headers == 0x08E17D50, "GetCurrentMapWildMonHeaderId changed"
    assert u32(DEXNAV_TABLES) == headers and u32(DEXNAV_TABLES + 4) == PYRAMID, "the DexNav's tables moved"
    assert at(FIND_CALL - 6, "0098022843d2"), "find's table loop changed"      # ldr r0, [sp]; cmp r0, #2; bhs
    assert bl_target(rom, FIND_CALL) == FIND_HEADER and at(FIND_HEADER, "10b58000"), "find does not call find_header"
    calls = []
    for k in range(0, len(rom) - 4, 2):
        x, y = struct.unpack_from("<HH", rom, k)
        if x & 0xF800 == 0xF000 and y & 0xF800 == 0xF800 and bl_target(rom, 0x08000000 + k) == FIND_HEADER:
            calls.append(0x08000000 + k)
    assert calls == [FIND_CALL], "find_header has other callers: %s" % ["%08X" % c for c in calls]

    src = open(os.path.join(HERE, "dexnavscan.s"), encoding="ascii").read().replace("HEADERS_ADDR", "0x%08X" % headers)
    code, dis = SM.thumb(src, BASE)
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code
    rom[o(FIND_CALL):o(FIND_CALL) + 4] = bl(FIND_CALL, BASE)
    open(outp, "wb").write(rom)
    print("map_header %08X..%08X; find's call %08X -> map_header (was find_header %08X)"
          % (BASE, 0x08000000 + end, FIND_CALL, FIND_HEADER))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
