"""Restore movement scripts that the translation passes mistook for text (Hyper Emerald v5.7 EN+QoL).
usage: python movefix_patch.py <in.gba> <out.gba> [original.gba]
Apply last, on top of the statcolor build. The optional original ROM is only used to double-check the restored bytes.

Root cause: `applymovement 0x000F, <movement>` assembles to 4F 0F 00 <ptr>, which is byte-identical to a
`loadword 0, <text>` (0F 00 <ptr>) preceded by 4F. The first text pass scanned for 0F 00 <ptr> to find dialogue,
so every applymovement on local object 15 was taken for a text load; the movement bytes decode as "Chinese"
and got a translation. Six of those pointers were redirected to relocated English text, and three movement
scripts (four references) were overwritten in place with English padded out to the old extent. Running such a
movement makes the object-event code index its action table with text bytes and jump to garbage:
mGBA reports "Jumped to invalid address 101C0CB4" in the new-game Mountain Top cutscene (map 34/66).
Second-pass casualties of the same kind: Slateport Contest Hall reception (map 9/3) and one vanilla script.
Two text loads that pointed into the middle of an in-place-translated string (Prof. Cozmo in the Mossdeep meteor
scene, "Would you like to battle with Treecko?" in Littleroot/Mossdeep) now get a clean relocated copy.
Every value below was read from the original ROM (sha1 f785bed9...) and is asserted before writing."""
import struct, sys

FREE = 0x00FD9D60                       # feature area, after the statcolor palette copy (ends 0xFD9D50)

# pointer occurrence -> (value the translation left there, original value)
PTR_FIXES = {
    0x0208ED0: (0x08B87C46, 0x08209068),  # Slateport City 9/3, Contest Hall receptionist walk-in
    0x02907FE: (0x082908B9, 0x0829082B),  # vanilla common script, face_player movement
    0x1828AEF: (0x08B14EB1, 0x09829105),  # Mountain Top 34/66 prologue (new game): Rainbow Rocket lineup
    0x186BC26: (0x08B14EB1, 0x09829105),  # same movement reused in Oreburgh City 37/82
    0x18832A4: (0x08B9225E, 0x09883DFA),  # Hearthome City 37/100 contest scene
    0x18831BC: (0x08B4E628, 0x09883EEB),  # Hearthome City 37/100 contest scene (Diantha)
    0x188319E: (0x08B480AC, 0x09883F59),  # Hearthome City 37/100 contest scene (Wallace)
    0x188315C: (0x08B4EE6E, 0x09884244),  # Hearthome City 37/100 contest scene (Diantha)
    0x1899BEB: (0x08B82F00, 0x0989A14D),  # Hisui, Rei/Cogita scene
}
# offset -> (bytes the translation left there, original movement bytes)
BYTE_FIXES = {
    0x181865C: (bytes.fromhex("fc0109cd"), bytes.fromhex("1815fe00")),                        # Mossdeep 14/9 meteor scene (Steven)
    0x1818B5E: (bytes.fromhex("cae6e3daad00bde3eee1e3f000"), bytes.fromhex("181818181818181818" "8f08fe00")),  # Mossdeep 14/9 / Steven's Island 35/41 (Zinnia)
    0x189A6D1: (bytes.fromhex("c9dcab00c6e3e3"), bytes.fromhex("5603fe005601fe")),             # Steven's Island 35/8 "everyone's here" scene
}
# text loads that point into the middle of an in-place English string: (string start, pointer occurrences, value they hold now)
TEXT_RELOC = [
    (0x1818B5E, [0x1817E9F, 0x181A2B2], 0x09818B6B),   # "Prof. Cozmo: Wha…What…? ..." (pointers skipped the old 13-byte movement)
    (0x1810B77, [0x1810B5B, 0x18B86FE], 0x09810B7F),   # "Would you like to battle with Treecko?" (pointers skipped an 8-byte prefix)
]


def build(inp, outp, original=None):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    orig = open(original, "rb").read() if original else None
    # 1) relocate the two truncated strings first (they are read from the still-English bytes)
    free = FREE
    for start, occs, cur in TEXT_RELOC:
        end = rom.index(b"\xff", start) + 1
        s = bytes(rom[start:end])
        assert 20 < len(s) < 200 and all(b <= 0xF0 or b >= 0xF7 for b in s), "unexpected string at %x" % start
        assert set(rom[free:free + len(s)]) == {0xFF}, "free space at %x is in use" % free
        rom[free:free + len(s)] = s
        for o in occs:
            assert struct.unpack_from("<I", rom, o)[0] == cur, "pointer at %x changed" % o
            struct.pack_into("<I", rom, o, 0x08000000 + free)
        free += (len(s) + 3) & ~3
    # 2) movement pointers back to the original scripts (those bytes were never touched)
    for o, (cur, want) in PTR_FIXES.items():
        assert struct.unpack_from("<I", rom, o)[0] == cur, "pointer at %x is %08x, expected %08x" % (o, struct.unpack_from("<I", rom, o)[0], cur)
        assert rom[o - 3] in (0x4F, 0x50), "not an applymovement at %x" % (o - 3)
        t = want - 0x08000000
        assert rom.index(b"\xfe", t) - t < 32 and all(b < 0xA0 for b in rom[t:rom.index(b"\xfe", t)]), "movement at %08x damaged" % want
        if orig: assert struct.unpack_from("<I", orig, o)[0] == want
        struct.pack_into("<I", rom, o, want)
    # 3) movement bytes overwritten in place
    for o, (cur, want) in BYTE_FIXES.items():
        assert rom[o:o + len(cur)] == cur, "bytes at %x differ from the expected translation output" % o
        if orig: assert orig[o:o + len(want)] == want
        rom[o:o + len(want)] = want
    open(outp, "wb").write(rom)
    print("wrote %s: %d pointers restored, %d movement scripts restored, %d strings relocated to %08x..%08x" % (
        outp, len(PTR_FIXES), len(BYTE_FIXES), len(TEXT_RELOC), 0x08000000 + FREE, 0x08000000 + free))


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4): print(__doc__); sys.exit(1)
    build(*sys.argv[1:])
