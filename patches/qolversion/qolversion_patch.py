"""QoL version in the Option screen's title (Hyper Emerald v5.7): python qolversion_patch.py in.gba out.gba

The Option screen's title bar reads "Ultra Emerald v5.7 (Standard)" - the hack's version and the save's
difficulty. This puts this patch set's own version in it as well:

    Ultra Emerald v5.7 +QoL1.5 (Standard)

One string per difficulty, reached through the table at 0x09F07DF4 (four words: Standard, Hard Mode,
Challenge, Lunatic). Each new string is built from the ROM's own bytes - its leading colour codes and its
mode name are copied, "+QoL<version>" is inserted before the mode - so nothing here hardcodes the hack's
wording. The originals stay where they are; only the four table words change, plus the new strings in free
space. "+QoL1.5" is written without an inner space because " +QoL 1.5 (Hard Mode)" runs past the window:
measured in mGBA, the longest of the four ends 6 px inside the box (the window's text area is x 24..225).

Apply late in the chain, after `version` has made these strings read 5.7.
"""
import os, struct, sys

QOL = "1.5"                             # this patch set's release
FREE = 0x00FF24C0                       # in the unreferenced 0xFF run 0x08FF2454.., after leaguetext's strings
TABLE = 0x01F07DF4                      # the Option screen's title, one word a difficulty
MODES = 4
B = 0x08000000

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "journal"))
import journal_patch as J

OPEN_PAREN = J.enc("(")[0]
MAXLEN = 38                             # what fits the window, from the mGBA measurements above


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    tag = J.enc("+QoL" + QOL + " ")
    d, ptrs = bytearray(), []
    for k in range(MODES):
        p = struct.unpack_from("<I", rom, TABLE + 4 * k)[0]
        assert B <= p < 0x0A000000, "title %d is not a pointer" % k
        o = p - B
        end = rom.index(0xFF, o)
        s = bytes(rom[o:end])
        assert J.enc("Emerald") in s and J.enc("5.7") in s, "title %d is not the version string" % k
        assert tag not in s, "already applied"
        i = s.index(OPEN_PAREN)                     # before the mode, e.g. "(Standard)"
        new = s[:i] + tag + s[i:]
        text = new[new.index(J.enc("Emerald")) - 6:]        # from "Ultra", for the length check
        assert len(text) <= MAXLEN, "%r is too long for the window" % text
        ptrs.append(B + FREE + len(d))
        d += new + b"\xff"
    assert set(rom[FREE:FREE + len(d)]) == {0xFF}, "target region not free"
    rom[FREE:FREE + len(d)] = d
    for k, p in enumerate(ptrs):
        struct.pack_into("<I", rom, TABLE + 4 * k, p)
    open(outp, "wb").write(rom)
    print("Option screen title: +QoL%s in %d difficulties, %d bytes @%08X..%08X" % (
        QOL, MODES, len(d), B + FREE, B + FREE + len(d)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
