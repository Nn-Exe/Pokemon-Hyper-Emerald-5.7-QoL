"""Egg moves: room for every one (Hyper Emerald v5.7). Apply after flyicons.
usage: python eggmoves_patch.py <in.gba> <out.gba>

Inheritance itself already follows the modern rule in this hack, checked in the emulator (test_eggmoves.lua):
the mother's egg moves are given by the hack's replacement InheritIVs (0x08070260 -> 0x09F00B08, which picks
the female or the non-Ditto parent at 0x09F007F8 and runs 0x09F009A4), the father's by vanilla BuildEggMoveset
(0x08070470) - so mother, father and either parent in a Ditto pair all pass them.

What was broken is the buffer the egg's list is read into. GetEggMoves (0x080703C8) copies up to 16 moves
(`cmp r2, #0xF` at 0x08070446) into sHatchedEggEggMoves (0x02024A38), which holds 10 (BuildEggMoveset clears
exactly 10: `cmp r6, #9` at 0x080704BA). Moves 11-16 spilled over the mother's move list and the next
variable, and a species' 17th egg move was never read at all - Turtwig's Tickle could not be passed.

The list now goes to a 32-move buffer at EWRAM 0x02031C00 (64 bytes, measured unused by
dexnavchain/test_scratch_ram.lua): the three words that name the old buffer (BuildEggMoveset's pool
0x08070580 and the hack's 0x09F00A60, 0x09F01CA0) are repointed, and both limits become 32. The longest list
in the table is 17.

Two lists had no species. The table is species + 20000, then that species' moves; where Mr. Mime's and Mime
Jr.'s markers belong the hack has a move id (53 Flamethrower, 107 Minimize), so their five egg moves (Hypnosis,
Fake Out, Confuse Ray, Power Split, Tickle - Sword/Shield's list) ran on from the species before: Goldeen and
Bonsly could be bred with them, and with Flamethrower / Minimize, while Mr. Mime and Mime Jr. had none. The two
words become the markers, which leaves Goldeen and Bonsly with exactly Sword/Shield's lists. Found by comparing
every list with the official games (_testrun/report/eggcheck.py, eggmissing.py).
"""
import struct, sys

OLD_BUF, NEW_BUF, SLOTS = 0x02024A38, 0x02031C00, 32
BUF_WORDS = (0x08070580, 0x09F00A60, 0x09F01CA0)
CLEAR_CMP = 0x080704BA                          # cmp r6, #9   -> cmp r6, #31 (clear the whole buffer)
COPY_CMP = 0x08070446                           # cmp r2, #0xF -> cmp r2, #31 (copy up to 32)
TABLE, TABLE_END = 0x09D78128, 0x09D7973C
# (address, the move id written there, the species it should mark, the species whose list it ran on from)
MARKERS = ((0x09D78478, 53, 122, 118), (0x09D78E40, 107, 492, 491))
MIME_MOVES = (95, 252, 109, 471, 321)           # Hypnosis, Fake Out, Confuse Ray, Power Split, Tickle


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    for w in BUF_WORDS:
        assert struct.unpack_from("<I", rom, o(w))[0] == OLD_BUF, "%08X no longer names the egg-move buffer" % w
    everywhere = [i for i in range(0, len(rom) - 3, 4) if struct.unpack_from("<I", rom, i)[0] == OLD_BUF]
    assert sorted(0x08000000 + i for i in everywhere) == sorted(BUF_WORDS), "other readers of the buffer: %s" % everywhere
    assert bytes(rom[o(CLEAR_CMP):o(CLEAR_CMP) + 2]) == bytes((0x09, 0x2E)), "the clear loop changed"
    assert bytes(rom[o(COPY_CMP):o(COPY_CMP) + 2]) == bytes((0x0F, 0x2A)), "the copy limit changed"

    # the two markers written as moves
    u16 = lambda a: struct.unpack_from("<H", rom, o(a))[0]
    words = [u16(a) for a in range(TABLE, TABLE_END, 2)]
    for addr, move, species, before in MARKERS:
        assert u16(addr) == move, "%08X is not move %d" % (addr, move)
        assert 20000 + species not in words, "species %d already has a list" % species
        back = addr - 2
        while u16(back) < 20000:
            back -= 2
        assert u16(back) == 20000 + before, "%08X is not in species %d's list" % (addr, before)
        assert tuple(u16(addr + 2 + 2 * i) for i in range(5)) == MIME_MOVES and u16(addr + 12) > 20000, \
            "the five moves after %08X changed" % addr
        struct.pack_into("<H", rom, o(addr), 20000 + species)

    # the longest list must fit
    longest, run = 0, 0
    for a in range(o(TABLE), o(TABLE_END), 2):
        v = struct.unpack_from("<H", rom, a)[0]
        run = 0 if v > 20000 else run + 1
        longest = max(longest, run)
    assert longest <= SLOTS, "a species has %d egg moves" % longest

    for w in BUF_WORDS:
        struct.pack_into("<I", rom, o(w), NEW_BUF)
    rom[o(CLEAR_CMP)] = SLOTS - 1
    rom[o(COPY_CMP)] = SLOTS - 1
    open(outp, "wb").write(rom)
    print("egg-move buffer %08X -> %08X (%d moves); longest list in the table: %d; %d species markers restored"
          % (OLD_BUF, NEW_BUF, SLOTS, longest, len(MARKERS)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
