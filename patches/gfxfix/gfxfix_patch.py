"""Restore compressed graphics the translation passes overwrote (Hyper Emerald v5.7 EN+QoL).
usage: python gfxfix_patch.py <in.gba> <out.gba> [original.gba]
Apply last, on top of the movefix build. The optional original ROM is only used to double-check the restored bytes.

Root cause: the text passes repointed every 4-byte occurrence of a Chinese string's pointer. Inside LZ77-compressed
graphics the byte stream is arbitrary, so 23 places happened to hold the exact 4 bytes of such a pointer and were
rewritten to the relocated English string. LZ77 is a stream format: one altered byte corrupts everything decoded
after it, so a 4-byte "pointer" in the middle of a tileset garbles most of that tileset's tiles.

Visible damage this fixes:
  0x08DF4628  map secondary tileset, 23 maps incl. Rustboro City (0/3): 80% of the tiles decoded wrong
  0x08C9B828  map secondary tileset, 35 maps (town/route interiors): 18% wrong
  19 more blobs in the hack's expansion area (sprites, portraits and menu graphics)
The English strings are untouched: each of them keeps its genuine pointer site elsewhere, and the rewritten
occurrences here were coincidences that no code reads as a pointer.

Every original value below was read from the original ROM (sha1 f785bed9...) and is asserted before writing."""
import struct, sys

# pointer occurrence -> (value the translation left there, original value)
FIXES = {
    0x0B4C850: (0x08B9AC30, 0x09889900),
    0x0C05C78: (0x08B8C9EB, 0x09872275),
    0x0C21198: (0x08B8B050, 0x0989A0DF),
    0x0C211A0: (0x08BA9A60, 0x0988889C),
    0x0C9CEC8: (0x08BD41AC, 0x085CCCDD),
    0x0CB99C8: (0x08B9AC30, 0x09889900),
    0x0DF4C4C: (0x08BAA6B7, 0x0988BB37),
    0x11CBFA4: (0x08BD4740, 0x0960428B),
    0x11CBFE0: (0x08B84B81, 0x09836509),
    0x11CDEE8: (0x08BB31BF, 0x09609091),
    0x11E86D8: (0x08B87399, 0x09892445),
    0x120F184: (0x08B8B4F1, 0x0988E700),
    0x121F37C: (0x08B814E4, 0x09899998),
    0x1228144: (0x08B83908, 0x098A0221),
    0x12614E0: (0x08B7F8D8, 0x09894AAA),
    0x1299F58: (0x08B854FE, 0x082C0608),
    0x12AAEE8: (0x08B84296, 0x09884110),
    0x1414C6C: (0x08BCE626, 0x09609001),
    0x1459750: (0x08BA8DEC, 0x082BD1A0),
    0x1477644: (0x08BB6F68, 0x09554322),
    0x14FFB00: (0x08B89409, 0x09886800),
    0x15ED276: (0x08329B87, 0x082124F7),
    0x15FB700: (0x08B8D374, 0x098978FF),
}


def build(inp, outp, original=None):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    orig = open(original, "rb").read() if original else None
    for off, (cur, want) in sorted(FIXES.items()):
        have = struct.unpack_from("<I", rom, off)[0]
        assert have == cur, "at %07X: found %08X, expected the translation's %08X" % (off, have, cur)
        if orig is not None:
            assert struct.unpack_from("<I", orig, off)[0] == want, "original mismatch at %07X" % off
        struct.pack_into("<I", rom, off, want)
    open(outp, "wb").write(rom)
    print("wrote %s: %d graphics bytes restored in %d blobs" % (outp, 4 * len(FIXES), len(FIXES)))


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print(__doc__); sys.exit(1)
    build(*sys.argv[1:])
