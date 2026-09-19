"""Version number 5.5 -> 5.7 (Hyper Emerald v5.7). Apply anywhere in the chain.
usage: python version_patch.py <in.gba> <out.gba>

The options screen and the Hall of Fame / mode banner still read "Ultra Emerald v5.5" - the hack's own
text was never updated for the 5.7 release. Every one of those strings is plain Gen 3 text, so the fix is
one byte per string: '5' (0xA6) -> '7' (0xA8) in the last digit. No pointer, no length, no code changes.

Only "5.5" preceded by "Emerald" within 10 bytes is touched, which skips the coincidental 0xA6 0xAD 0xA6
that occurs inside compressed graphics at 0x00E95143.
"""
import re, sys

FIVE, DOT, SEVEN = 0xA6, 0xAD, 0xA8
EMERALD = bytes((0xBF, 0xE1, 0xD9, 0xE6, 0xD5, 0xE0, 0xD8))   # "Emerald"
EXPECT = 14


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    hits = [m.start() for m in re.finditer(re.escape(bytes((FIVE, DOT, FIVE))), bytes(rom))
            if EMERALD in rom[max(0, m.start() - 10):m.start()]]
    assert len(hits) == EXPECT, "expected %d version strings, found %d" % (EXPECT, len(hits))
    for h in hits:
        rom[h + 2] = SEVEN
    open(outp, "wb").write(rom)
    print("version 5.5 -> 5.7 at %d strings: %s" % (len(hits), ", ".join("%07X" % h for h in hits)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
