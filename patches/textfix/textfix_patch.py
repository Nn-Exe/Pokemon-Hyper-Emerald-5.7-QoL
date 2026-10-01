"""Same-length text fixes, in place (Hyper Emerald v5.7). Apply last.
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
    open(outp, "wb").write(rom)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
