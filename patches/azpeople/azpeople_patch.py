"""Area Zero's people, redrawn after references the user found (Hyper Emerald v5.7):
python azpeople_patch.py <in.gba> <out.gba>          (after castlefence, before kitakami)

The user (2026-10-22) sent screenshots of Pokemon Essentials art of Paldea's people - battle pictures of Nemona,
Arven, Penny, Jacq, Sada, Turo and the two AIs, walking sheets of Nemona, Sada and Turo - as "accurate reference for
sprites of Paldea npcs"; without the files, "redraw", and for the size "u decide". The art was recovered from the
screenshots (_testrun/paldea/people/refs/extract.py) and the new pictures made from it
(_testrun/paldea/people/redraw: redraw.py, draw3.py, finalize.py; NOTES, *Area Zero's people, after the
references*): walkers 32 x 32 in the references' style for all six (Nemona, AI Sada, AI Turo from their sheets;
Jacq and Arven drawn over Turo's, Penny over Nemona's), battle pictures 250-252 (Nemona, AI Sada, AI Turo) brought to
64 x 64. The pictures are sprites/*.png, made into what the game reads by make.py.

What changes, on top of paldea's cast (patches/paldea/cast.py, whose pictures it checks first):
  * the six entries of the hack's sprite table (174-178, 180): 32 x 32 (size 0x200, the OAM and subsprite tables
    the hack's 32 x 32 people use, 0x0850951C / 0x085095F4), and the new frames; tags, palette slot, shadow,
    walking animations as they were;
  * the four palettes (tags 0x1141-0x1144: Arven + Penny, Nemona + Jacq, AI Sada, AI Turo), rewritten in place where
    the field palette table (the word at 0x0808E8BC) has them;
  * battle pictures 250-252: new compressed pictures and palettes, their table entries pointed at them (the tables
    found through their entries, where paldea left them).
Space: 0x09E24000..0x09E2E000 (the hack's zero run 0x09E10044..0x09F00000, blank in its own ROM; no code word points
in; NOTES gives the read watch). The old pictures stay where paldea put them, unused.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, "sprites")
OLD = os.path.join(HERE, "..", "paldea", "sprites")          # paldea's pictures, as the cast installed them
sys.path.insert(0, os.path.join(HERE, "..", "paldea"))
sys.path.insert(0, os.path.join(HERE, "..", "speciesx"))
import tiles as TL                                            # paldea's LZ77
import speciesx_patch as SX                                   # is_pointer

FREE, FREE_END = 0x01E24000, 0x01E2E000
BASE = 0x08000000 + FREE
EXT_TABLE_WORD = 0x014A2C10                                  # the hack's own sprite table (graphics 0x4E)
PAL_TABLE_WORD = 0x0008E8BC                                  # the field palette table (Area Zero's copy, or later)
PEOPLE = {"nemona": (174, 0x1142), "arven": (175, 0x1141), "penny": (176, 0x1141), "jacq": (177, 0x1142),
          "sada": (178, 0x1143), "turo": (180, 0x1144)}
GROUP = {0x1141: "A", 0x1142: "B", 0x1143: "C", 0x1144: "D"}
OLD_PAL = {0x1141: "arven", 0x1142: "nemona", 0x1143: "sada", 0x1144: "turo"}
BATTLE = {"nemona": 250, "sada": 251, "turo": 252}
OAM_16x32, SUB_16x32, OAM_32, SUB_32, ANIMS = 0x08509514, 0x085095A0, 0x0850951C, 0x085095F4, 0x08509100
FRAMES = 9


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def load(path, size=None):
    b = open(path, "rb").read()
    assert size is None or len(b) == size, path
    return b


def battle_tables(rom):
    """(pictures, palettes) tables: where an entry n of 250-252 is {picture, 0x800, n} and the palettes follow"""
    found = []
    for k in range(0, len(rom) - 4, 4):
        v = u32(rom, k)
        if not 0x08000000 <= v < 0x0A000000:
            continue
        t = v - 0x08000000
        if t + 8 * 253 > len(rom):
            continue
        if all(u16(rom, t + 8 * n + 4) == 0x800 and u16(rom, t + 8 * n + 6) == n for n in (250, 251, 252)) and \
                all(u16(rom, t + 8 * 253 + 8 * n + 4) == n for n in (250, 251, 252)):
            found.append(t)
    found = sorted(set(found))
    assert len(found) == 1, "the trainer picture tables: %s" % ["%08X" % (0x08000000 + t) for t in found]
    return found[0], found[0] + 8 * 253


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    ext = u32(rom, EXT_TABLE_WORD) - 0x08000000
    pt = u32(rom, PAL_TABLE_WORD) - 0x08000000

    # ---- what is there now is paldea's cast
    for key, (slot, tag) in PEOPLE.items():
        e = ext + 0x24 * slot
        assert struct.unpack_from("<HHHHhh", rom, e) == (0xFFFF, tag, 0x11FF, 0x100, 16, 32), \
            "sprite entry %d is not Area Zero's %s as the cast made it" % (slot, key)
        assert (u32(rom, e + 0x10), u32(rom, e + 0x14), u32(rom, e + 0x18)) == (OAM_16x32, SUB_16x32, ANIMS)
        frames = u32(rom, e + 0x1C) - 0x08000000
        old = load(os.path.join(OLD, key + ".4bpp"), FRAMES * 0x100)
        for f in range(FRAMES):
            p, size = struct.unpack_from("<IH", rom, frames + 8 * f)
            assert size == 0x100 and rom[p - 0x08000000:p - 0x08000000 + 0x100] == old[0x100 * f:0x100 * (f + 1)], \
                "%s's frame %d is not the cast's" % (key, f)
    rows = {}
    i = 0
    while u16(rom, pt + 8 * i + 4) != 0x11FF:
        rows.setdefault(u16(rom, pt + 8 * i + 4), u32(rom, pt + 8 * i) - 0x08000000)
        i += 1
        assert i < 512
    for tag, key in OLD_PAL.items():
        assert rom[rows[tag]:rows[tag] + 32] == load(os.path.join(OLD, key + ".gbapal"), 32), "palette %04X" % tag
    pics, pals = battle_tables(rom)
    for key, n in BATTLE.items():
        assert TL.lz(rom, u32(rom, pics + 8 * n) - 0x08000000)[:0x800] == load(os.path.join(OLD, key + "_battle.4bpp")), \
            "battle picture %d is not the cast's" % n
        assert TL.lz(rom, u32(rom, pals + 8 * n) - 0x08000000)[:32] == load(os.path.join(OLD, key + "_battle.gbapal"))

    # ---- the space
    assert set(rom[FREE:FREE_END]) == {0}, "target region not blank"
    for k in range(0, len(rom) - 3, 4):
        v = u32(rom, k)
        if BASE <= v < 0x08000000 + FREE_END:
            assert not SX.is_pointer(rom, k), "%08X points into the target" % (0x08000000 + k)

    # ---- the blob: frames, frame lists, the battle pictures and palettes
    blob, at = bytearray(), {}

    def put(name, data, align=4):
        while len(blob) % align:
            blob.append(0)
        at[name] = BASE + len(blob)
        blob.extend(data)

    for key in PEOPLE:
        put(("frames", key), load(os.path.join(SPR, key + "_walk.4bpp"), FRAMES * 0x200))
    for key in PEOPLE:
        p = at[("frames", key)]
        put(("list", key), b"".join(struct.pack("<IHH", p + 0x200 * f, 0x200, 0) for f in range(FRAMES)))
    for key in BATTLE:
        pic = load(os.path.join(SPR, key + "_battle.4bpp"), 0x800)
        pal = load(os.path.join(SPR, key + "_battle.gbapal"), 32)
        cp, cq = TL.lz_comp(pic), TL.lz_comp(pal)
        assert TL.lz(cp, 0) == pic and TL.lz(cq, 0)[:32] == pal
        put(("pic", key), cp)
        put(("pal", key), cq)
    assert FREE + len(blob) <= FREE_END, "the pictures do not fit: %d bytes" % len(blob)
    rom[FREE:FREE + len(blob)] = blob

    # ---- the entries, the palettes, the battle tables
    for key, (slot, tag) in PEOPLE.items():
        e = ext + 0x24 * slot
        struct.pack_into("<Hhh", rom, e + 6, 0x200, 32, 32)
        struct.pack_into("<II", rom, e + 0x10, OAM_32, SUB_32)
        struct.pack_into("<I", rom, e + 0x1C, at[("list", key)])
    for tag, g in GROUP.items():
        rom[rows[tag]:rows[tag] + 32] = load(os.path.join(SPR, "pal_%s.gbapal" % g), 32)
    for key, n in BATTLE.items():
        struct.pack_into("<I", rom, pics + 8 * n, at[("pic", key)])
        struct.pack_into("<I", rom, pals + 8 * n, at[("pal", key)])
    open(outp, "wb").write(rom)
    print("azpeople: %08X..%08X (%d bytes): six walkers 32x32, four palettes, battle pictures 250-252" % (
        BASE, BASE + len(blob), len(blob)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
