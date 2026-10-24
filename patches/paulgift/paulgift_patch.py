"""Paul no longer gives a second EV-IV Display (Hyper Emerald v5.7). Apply after keytrainers, before kitakami.
usage: python -I paulgift_patch.py <in.gba> <out.gba>

A player's report (2026-10-20): "since you start with the EV-IV display, after beating Paul in Fortree he gives you
another one, which does nothing." The new-game PC holds one (the table at 0x0837F790: NOTES, *The Shiny Charm is not
in the PC*), and Paul's rematch in Fortree City (0/4, the trigger at 22,11, script 0x0987D721) ends with "I'll give
you this. I don't need it anymore……" and `giveitem` EV-IV Display (650) x1. The original v5.7 bugfix 2 has the
same bytes. The user: "paul doesn't need to give again".

The line and the gift are 20 bytes after his post-battle speech's closemessage: loadword 0 + callstd 4 at
0x0987D775, then copyvarifnotzero 0x8000 650, copyvarifnotzero 0x8001 1, callstd 0 at 0x0987D77D..0x0987D788. A
`goto 0x0987D789` over the first of them goes straight on to him flying off; his flags 0x42AF and 0x42B1 are set
after that as before. Nothing in the ROM points into the 20 bytes (no word, aligned or not), so the 15 left behind
the goto are never read. The string stays where it is, unused.
"""
import struct, sys

B = 0x08000000
LINE = 0x0987D775                       # loadword 0, "I'll give you this. ..." / callstd 4
AFTER = 0x0987D789                      # applymovement 10: Paul flies off
TEXT = 0x0987D7AF
WAS = bytes.fromhex("0f00afd78709" "0904" "1a00808a02" "1a01800100" "0900")


def patch(rom):
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = LINE - B
    assert len(WAS) == AFTER - LINE
    assert bytes(rom[o:o + len(WAS)]) == WAS, "Paul's gift is not what it was (already applied?)"
    assert struct.unpack_from("<I", rom, o + 2)[0] == TEXT
    assert rom[o - 1] == 0x68, "no closemessage before his line"
    assert bytes(rom[AFTER - B:AFTER - B + 2]) == b"\x4f\x0a", "not applymovement 10 after the gift"
    rom[o:o + 5] = b"\x05" + struct.pack("<I", AFTER)


def main(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    patch(rom)
    open(outp, "wb").write(rom)
    print("paulgift: goto 0x%08X at 0x%08X (no second EV-IV Display)" % (AFTER, LINE))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
