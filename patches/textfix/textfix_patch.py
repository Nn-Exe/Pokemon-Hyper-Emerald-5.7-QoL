"""Text fixes in place (Hyper Emerald v5.7): same-length word swaps and re-laid-out lines.
usage: python textfix_patch.py <in.gba> <out.gba>

Each fix replaces a word inside one of the game's own texts with another of exactly the same length, so nothing
moves and no pointer changes. The patcher checks the old bytes at the address and that the word occurs nowhere else.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
from inserter import ENC

FIXES = [
    # (address, old, new, where)
    (0x098208B4, "emmited", "emitted", "Sky Pillar summit, the meteorite reacting to Rayquaza (script 0x0982060F)"),
]

# Texts laid out again in place: the same words, new line breaks, never longer than before (the rest of the old
# text's bytes become 0xFF). Each is (address, its lines now, its lines after, where); a line is (text, the break
# after it: 0xFE new line, 0xFA scroll, 0xFB new page, 0xFF end).
RELAYOUT = [
    (0x0983D5AE,
     [("This icy rock is emanating energy.", 0xFE), ("Certain Pokémon may react to it.  We have been chosen and gathered", 0xFE),
      ("together to change the world.", 0xFA), ("We cannot lose!", 0xFF)],
     [("This icy rock is emanating energy.", 0xFE), ("Certain Pokémon may react to it.", 0xFB),
      ("We have been chosen and gathered", 0xFE), ("together to change the world.", 0xFB), ("We cannot lose!", 0xFF)],
     "Shoal Cave's icy rock sign: two sentences ran into one line too long for the box"),
]


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    enc = lambda s: bytes(ENC[c] for c in s)
    for addr, old, new, where in FIXES:
        a, b = enc(old), enc(new)
        assert len(a) == len(b), "%r -> %r changes the length" % (old, new)
        o = addr - 0x08000000
        assert bytes(rom[o:o + len(a)]) == a, "%08X does not read %r" % (addr, old)
        assert rom.count(a) == 1, "%r occurs more than once" % old
        rom[o:o + len(b)] = b
        print("%08X %r -> %r  (%s)" % (addr, old, new, where))
    for addr, old, new, where in RELAYOUT:
        a = b"".join(enc(t) + bytes([sep]) for t, sep in old)
        b = b"".join(enc(t) + bytes([sep]) for t, sep in new)
        assert len(b) <= len(a), "%08X: the new layout is longer" % addr
        o = addr - 0x08000000
        assert bytes(rom[o:o + len(a)]) == a, "%08X is not the text expected" % addr
        rom[o:o + len(a)] = b + bytes([0xFF]) * (len(a) - len(b))
        print("%08X laid out again  (%s)" % (addr, where))
    open(outp, "wb").write(rom)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
