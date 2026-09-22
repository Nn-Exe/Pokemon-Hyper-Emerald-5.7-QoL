"""Species names still in Chinese, rewritten in English in place (Hyper Emerald v5.7). Apply after berrynum.

    python patches/speciesnames/speciesnames_patch.py in.gba out.gba

The species name table (ROM header 0x144) has fixed 11-byte entries: up to 10 characters and a terminator.
Each fix asserts the entry still holds the Chinese name it replaces, then writes the English one padded with
terminators. Nothing is repointed.

  1025  爱娜莫洛斯 -> Enamorus    (Fairy/Flying, 74/115/70/106/135/80; the Lv 70 one at the Moonbow Dome)

Still Chinese, left for later: 990-993, four Galar-fossil species (化石雷鸟, 化石巨龙, 化石鳃鱼, 化石海兽), whose
English names do not fit 10 characters as they stand.
"""
import struct, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavchain"))
from dexnavchain_patch import text

FIXES = {
    1025: (bytes.fromhex("010d09be09a0091f0cab"), "Enamorus"),
}


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    names = struct.unpack_from("<I", rom, 0x144)[0] - 0x08000000
    for sp, (old, new) in FIXES.items():
        o = names + sp * 11
        assert bytes(rom[o:o + len(old)]) == old, "species %d is not the Chinese name this patch expects" % sp
        enc = text(new)
        assert len(enc) <= 11, "%s does not fit" % new
        rom[o:o + 11] = enc + b"\xff" * (11 - len(enc))
        print("species %d -> %s" % (sp, new))
    open(outp, "wb").write(rom)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
