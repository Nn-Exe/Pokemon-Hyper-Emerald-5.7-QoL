"""Item description fixes (Hyper Emerald v5.7). Apply last.
usage: python itemdesc_patch.py <in.gba> <out.gba>

TM75 (item 452) teaches Low Sweep - the TM table at 0x09E0FE80 (entry 74 = move 490), which the Bag's name, the
party menu's "can learn" check and the teaching itself all read - but its description was Bounce's: the item's
pointer (item + 20) is the same 0x08583197 as TM52's, which does teach Bounce. Every other TM's description matches
its move (checked all 128; the shared ones are moves with the same effect, e.g. Hyper Beam / Giga Impact).
The new text is the game's own Low Sweep line from the summary's move descriptions (0x09D2CD1E, "The user hits
the foe's legs, lowering its Speed."), broken into three lines that fit the Bag's description box (its lines are
<= ~105 px; the summary's two are 120 / 126 px).

2026-10-01, every TM/HM description read against its move (the TM table, the move's data at 0x09D86419 - power +1,
accuracy +3, effect chance +5 - and the summary's text). All the numbers were right; what was not:
* five texts shared by moves that do different things, so two or three TMs read the same (reported for TM08/09):
  Hyper Beam / Giga Impact, Solar Beam / Solar Blade, Giga Drain / Drain Punch / Draining Kiss, U-turn / Volt Switch
  / Flip Turn, Shadow Claw / Psycho Cut - each now says what it is. Draining Kiss also said "half the damage"; it
  heals 75%.
* Misty Explosion (TM118) never said the user faints; Attract (TM31) read as if the user could not attack;
  Will-O-Wisp (TM38) "always burns" (it is 85% accurate); Bullet Seed (TM50) "Hits hits"; Rock Blast (TM54) "for
  2 to 5 times"; Terrain Pulse (TM101) "type varies"; Swift (TM40) "Star-shaped".
Every new text goes to free space and the item's pointer is moved; the old texts stay where they are. After the
fixes no two of the 128 TMs and HMs share a description (asserted).
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
from inserter import ENC

FREE = 0x00FF6400                       # in the unreferenced 0xFF run 0x08FF5C35..0x08FFD5A0, after bagslots
FREE_END = 0x00FF6600                   # three data words point at 0x08FF6673.. - stay clear of them
FREE2, FREE2_END = 0x00FF8900, 0x00FF9400   # the rest: a stretch of the same run no word in the ROM points into
FONTW = 0x006542E4                      # the normal font's glyph widths (questlog_patch.FONTW)
MAX_PX = 102                            # the widest line among the game's own TM descriptions
TM_TABLE, TM01 = 0x01E0FE80, 378

FIXES = [
    # (item, its TM number, move it must teach, the description it has now, the new lines)
    (452, 75, 490, 0x08583197, ["The user hits the", "foe’s legs, lowering", "its Speed."]),
    # shared texts: "Powerful, but / needs recharging / the next turn."
    (385, 8, 63, 0x08582AFE, ["Fires a powerful", "beam. The user must", "rest next turn."]),
    (386, 9, 416, 0x08582AFE, ["Charges at the foe", "with all its power,", "then must rest."]),
    # "Absorbs sunlight in / the 1st turn, then / attacks next turn."
    (388, 11, 76, 0x085829B3, ["Absorbs sunlight in", "the 1st turn, then", "fires a beam next."]),
    (389, 12, 632, 0x085829B3, ["Absorbs sunlight in", "the 1st turn, then", "slashes next turn."]),
    # "User recovers half / the damage this / move inflicts." (Draining Kiss heals 75%)
    (405, 28, 202, 0x08582CDF, ["Drains nutrients.", "The user recovers", "half the damage."]),
    (440, 63, 409, 0x08582CDF, ["A draining punch.", "The user recovers", "half the damage."]),
    (464, 87, 577, 0x08582CDF, ["A draining kiss.", "The user recovers", "75% of the damage."]),
    # "After attacking, / the user switches / out."
    (433, 56, 369, 0x095522AA, ["Hits the foe, then", "rushes back to", "switch out."]),
    (457, 80, 521, 0x095522AA, ["An electric hit,", "then the user", "switches out."]),
    (480, 103, 889, 0x095522AA, ["Hits the foe with a", "flip, then the user", "switches out."]),
    # "A move that has a / high critical-hit / ratio."
    (442, 65, 421, 0x0955213B, ["Slashes with a", "shadowy claw. High", "critical-hit ratio."]),
    (446, 69, 427, 0x0955213B, ["Tears with psychic", "blades. High", "critical-hit ratio."]),
    # wrong or missing
    (495, 118, 879, 0x08582E1E, ["The user faints.", "Has 150 power in", "Misty Terrain."]),
    (408, 31, 213, 0x0858312D, ["Makes it tough for", "an opposite-gender", "foe to attack."]),
    (415, 38, 261, 0x095520DC, ["A sinister flame", "that burns the", "target."]),
    # typos
    (427, 50, 331, 0x08583058, ["Shoots seeds at", "the foe. Hits", "2 to 5 times."]),
    (431, 54, 350, 0x08583246, ["Hurls rocks at", "the foe. Hits", "2 to 5 times."]),
    (478, 101, 882, 0x09552C45, ["Power and type", "vary with the", "active Terrain."]),
    (417, 40, 129, 0x08582DEC, ["Fires star-shaped", "rays that", "never miss."]),
]
TMS_HMS = 128                           # TM01..TM120, HM01..HM08: items 378..505


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    items = u32(0x1C8) - 0x08000000
    enc = lambda s: bytes(ENC[c] for c in s)
    for start, stop in ((FREE, FREE_END), (FREE2, FREE2_END)):       # nothing may point into either window
        for k in range(0, len(rom), 4):
            v = struct.unpack_from("<I", rom, k)[0]
            assert not 0x08000000 + start <= v < 0x08000000 + stop, "%08X points into %08X..%08X (%08X)" % (
                0x08000000 + k, 0x08000000 + start, 0x08000000 + stop, v)
    blob, blob2 = bytearray(), bytearray()
    for item, tm, move, old_desc, lines in FIXES:
        e = items + 44 * item
        name = enc("TM %02d" % tm) + b"\xFF"
        assert bytes(rom[e:e + len(name)]) == name, "item %d is not TM%d" % (item, tm)
        assert u16(TM_TABLE + 2 * (item - TM01)) == move, "TM%d does not teach move %d" % (tm, move)
        assert u32(e + 20) == old_desc, "TM%d's description is not the one this fix expects" % tm
        for l in lines:
            w = sum(rom[FONTW + b] for b in enc(l))
            assert w <= MAX_PX, "%r is %d px, wider than the Bag's box" % (l, w)
        text = b"\xFE".join(enc(l) for l in lines) + b"\xFF"
        if FREE + len(blob) + len(text) <= FREE_END and not blob2:
            addr = 0x08000000 + FREE + len(blob)
            blob += text
        else:
            addr = 0x08000000 + FREE2 + len(blob2)
            blob2 += text
        struct.pack_into("<I", rom, e + 20, addr)
        print("TM%d (move %d): description -> %08X %r" % (tm, move, addr, " / ".join(lines)))
    for start, stop, b in ((FREE, FREE_END, blob), (FREE2, FREE2_END, blob2)):
        end = start + len(b)
        assert end <= stop and set(rom[start:end]) == {0xFF}, "target region not free"
        rom[start:end] = b
    descs = [u32(items + 44 * (TM01 + i) + 20) for i in range(TMS_HMS)]
    texts = [bytes(rom[d - 0x08000000:rom.index(0xFF, d - 0x08000000)]) for d in descs]
    assert len(set(descs)) == len(set(texts)) == TMS_HMS, "two TMs/HMs still share a description"
    open(outp, "wb").write(rom)
    print("%d bytes @%08X, %d bytes @%08X; the %d TM/HM descriptions are all different" % (
        len(blob), 0x08000000 + FREE, len(blob2), 0x08000000 + FREE2, TMS_HMS))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
