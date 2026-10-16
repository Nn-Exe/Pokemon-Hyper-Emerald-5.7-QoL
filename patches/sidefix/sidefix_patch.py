"""Two side quests that could not be done, from the Quest Log recheck of 2026-10-14 (NOTES, *Side quests rechecked*).

    python sidefix_patch.py in.gba out.gba

1. The Magikarp gift. The "1230-year-old demon soul" in the top room of Steven's residence (Steven's Island 35/8,
   object at 7,7, script 0x0988F037: pay 1,996, beat trainer 1161, `givemon` Magikarp Lv1) checked and set flag
   0x4118 - which Dawn on Route 210 (0x0980977C) also sets after her first battle. Beat Dawn first and he only said
   his last line: no Magikarp. He now checks and sets 0x4552, his own trainer flag (a trainer above 0x357 has flag
   id + 0x40C9: 1161 + 0x40C9), which the battle sets anyway; Dawn keeps 0x4118. So a save that beat Dawn first can
   still get the Magikarp, and getting it no longer makes Dawn skip her first battle.
2. Blue's Galar team. Blue (Lilycove Museum 1F, 13/2, local 11, script 0x0980B0DE: beat her, nine Galar Pokemon
   Lv15) stood at 3,0 inside the top wall with movement type 76 (invisible); the tile in front of her is wall too
   and nothing moves her, so nobody could talk to her. She now stands on the floor below that spot (3,2), at the
   room's height (3), facing down (movement type 8). Two words of her lines: the Pokemon she gives are Galar ones,
   not "Kalos" ones (same length), and her junior is Lyra, as in her gift line and the rest of the game, not
   "Kotone" (2 bytes shorter: the rest of that string moves up).

Every site is checked before it is written; the patch is the same in the chain (after iconpalfix, before zhtext)
and on top of the finished game.
"""
import struct, sys

B = 0x08000000
SOUL_CHECK = 0x0988F039                 # checkflag 0x4118
SOUL_SET = 0x0988F08B                   # setflag 0x4118, after the givemon
SOUL_FLAG = 1161 + 0x40C9               # trainer 1161's flag
BLUE = 0x08A3EB54                       # 13/2's object template 10 (24 bytes)
BLUE_WAS = bytes.fromhex("0be70000") + struct.pack("<hhBB", 3, 0, 0, 76)
KALOS = 0x08B1443B                      # in her gift line 0x08B1439E
KOTONE = 0x0836E48E                     # in her line 0x0836E478 (her "no" to a rematch)
KOTONE_LINE = 0x0836E478

CH = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CH.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})


def enc(s): return bytes(CH[c] for c in s)


def patch(rom):
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = SOUL_CHECK - B
    assert rom[o:o + 3] == b"\x2b\x18\x41" and rom[o - 2:o] == b"\x69\x5a", "the demon soul's flag check moved"
    o = SOUL_SET - B
    assert rom[o:o + 3] == b"\x29\x18\x41" and rom[o - 4] == 0x31, "the demon soul's setflag moved"
    assert rom[0x0988F078 - B] == 0x79 and struct.unpack_from("<H", rom, 0x0988F079 - B)[0] == 129, "no Magikarp"
    assert SOUL_FLAG == 0x4552
    o = BLUE - B
    assert bytes(rom[o:o + 10]) == BLUE_WAS, "Blue's object is not where it was"
    assert struct.unpack_from("<I", rom, o + 16)[0] == 0x0980B0DE, "object 10 is not Blue"
    o = KALOS - B
    assert bytes(rom[o:o + 5]) == enc("Kalos")
    o, line = KOTONE - B, KOTONE_LINE - B
    end = rom.index(0xFF, line)
    assert bytes(rom[o:o + 6]) == enc("Kotone") and line < o < end and end - line == 280

    for a in (SOUL_CHECK, SOUL_SET):
        struct.pack_into("<H", rom, a - B + 1, SOUL_FLAG)
    struct.pack_into("<hhBB", rom, BLUE - B + 4, 3, 2, 3, 8)
    rom[KALOS - B:KALOS - B + 5] = enc("Galar")
    rest = bytes(rom[o + 6:end + 1])                # ", is traveling in Hoenn, too. ..." and the 0xFF
    new = enc("Lyra") + rest
    rom[o:end + 1] = new + b"\xff" * 2


def main(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    patch(rom)
    open(outp, "wb").write(rom)
    print("sidefix: demon soul on flag 0x%04X (0x%08X, 0x%08X); Blue at 3,2 facing down (0x%08X); Galar, Lyra"
          % (SOUL_FLAG, SOUL_CHECK, SOUL_SET, BLUE))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
