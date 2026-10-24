"""Kitakami's field sprites: Carmine, Kieran and Briar (the user's approved repaints, walking like any person), and
the Loyal Three's stone statues at Loyalty Plaza (one front frame each, one shared stone palette). The pictures are
sprites/*.4bpp and *.gbapal (made by sprites/convert.py).

Where they go (2026-10-16):
  * Entries of the hack's sprite table (0x0839CF00 + 0x24 * n, drawn by graphics 0x4E with n in the object
    template's fourth byte; one code path reads the table, the lookup at 0x094A2BCE, and n comes from the template).
    Area Zero took the table's filler end and its blank entries; none is spare. Taken here: six entries that no
    object of any of the game's 939 maps uses (_testrun/kitakami/sprite_slots.py): 236, 237, 239 - an inanimate
    copy of 228, 229, 235 (the same pictures and palettes) - and 228, 229, 235, unused too. The story's Pokemon
    alive (Ogerpon, the Loyal Three: pokeemerald-expansion's walking sprites, three standing frames) take 230, 238
    (one picture in two palettes, both unused) and 205, 206 (two of the hack's unused people). Before taking them the
    patch checks that each still holds what it held on 2026-10-16 and that no map object uses it.
  * The people's entries are copies of the game's own entries for the sprites they were painted from (main table
    183, 81, 27: their OAM, subsprites, walking animations, shadow), with our pictures and palette tags; the
    statues' are copies of the hack's 32x32 Suicune (73) with the animation table of a thing that keeps still (28).
    Palette slot 2 is "by tag" to the hack, as for Area Zero's (paldea/mons.py).
  * Palettes, under tags 0x1138-0x113B, in a longer copy of the field palette table the code reads now (Area
    Zero's copy, which ends in tag 0x11FF): the three code words that hold its address point at ours.
"""
import os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(HERE, "sprites")

EXT_LIT, EXT_TABLE = 0x014A2C10, 0x0839CF00
MAIN_TABLE = 0x00505620
PAL_REFS = (0x0008E8BC, 0x0008E950, 0x0008E9A8)
PAL_END_TAG = 0x11FF
LIKE_32, LIKE_STILL = 73, 28
SLOT_BY_TAG = 2
STEPS = 9                                   # the frames the walking animations count

# key -> (picture file, entry, palette tag, what the entry is copied from)
PEOPLE = {"carmine": ("carmine", 236, 0x1138, 183), "kieran": ("kieran", 237, 0x1139, 81),
          "briar": ("briar", 239, 0x113A, 27)}
STATUES = {"okidogi": ("statue_okidogi", 228, 0x113B), "munkidori": ("statue_munkidori", 229, 0x113B),
           "fezandipiti": ("statue_fezandipiti", 235, 0x113B)}
# the story's Pokemon on the map, alive (3 standing frames: they turn to face you, as Area Zero's legends)
LIVE = {"ogerpon": ("ogerpon", 230, 0x113C), "live_okidogi": ("okidogi", 238, 0x113D),
        "live_munkidori": ("munkidori", 205, 0x113E), "live_fezandipiti": ("fezandipiti", 206, 0x113F),
        "pecharunt": ("pecharunt", 204, 0x1140)}     # Part 2 (2026-10-17): another of the hack's unused people
FRAME_ORDER = (0, 1, 2, 0, 0, 1, 1, 2, 2)  # the walking animations' frames 0-8 from our down, up, left
# Area Zero's people in sprites of their own (patches/paldea/cast.py, 2026-10-21: the user, "reusing npcs make the
# game look cheap"): Part 2's Nemona wears hers (Arven's and Penny's made seven palettes in the market: kchapters).
# Entries and palette tags Area Zero takes (it comes first in the chain); check() makes sure they are there:
# key -> (entry, palette tag)
AZ_PEOPLE = {"az_nemona": (174, 0x1142)}
PALETTES = {0x1138: "carmine", 0x1139: "kieran", 0x113A: "briar", 0x113B: "statue", 0x113C: "ogerpon",
            0x113D: "okidogi", 0x113E: "munkidori", 0x113F: "fezandipiti", 0x1140: "pecharunt"}
WAS = {   # the six entries as they were (2026-10-16)
    228: "ffff0a11ff110001100020001401000014955008a09550080091500800634309a8c62e08",
    229: "ffff0611ff110001100020001401000014955008a09550080091500880d24409a8c62e08",
    235: "ffff0a11ff110001100020005400000814955008a09550080091500800ef4409a8c62e08",
    236: "ffff0a11ff110001100020005400000814955008a09550080091500800634309a8c62e08",
    237: "ffff0611ff110001100020005400000814955008a09550080091500880d24409a8c62e08",
    239: "ffff0a11ff110001100020005400000814955008a09550080091500800ef4409a8c62e08",
    230: "ffff0b11ff110001100020001401000014955008a09550080091500800eb4409a8c62e08",
    238: "ffff0a11ff110001100020005400000814955008a09550080091500800eb4409a8c62e08",
    205: "ffff0b11ff11000110002000a201000814955008a095500800915008245c2909a8c62e08",
    206: "ffff0611ff110001100020000001000814955008a0955008009150082c5c2909a8c62e08",
    204: "ffff0511ff11000110002000a201000814955008a09550080091500898542909a8c62e08",   # (2026-10-17)
}


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def ext_at(n): return EXT_TABLE - 0x08000000 + 0x24 * n
def main_at(rom, n): return u32(rom, MAIN_TABLE + 4 * n) - 0x08000000


def load(name):
    return open(os.path.join(SPRITES, name + ".4bpp"), "rb").read()


def pal_table(rom):
    """(where the code's field palette table is, its rows up to the end mark)"""
    at = {u32(rom, r) for r in PAL_REFS}
    assert len(at) == 1, "the field palette table's three references disagree"
    t = at.pop() - 0x08000000
    for i in range(256):
        if u16(rom, t + 8 * i + 4) == PAL_END_TAG:
            return t, i
    raise AssertionError("the field palette table has no end mark (0x11FF)")


def map_uses(rom):
    """every hack sprite entry a map object uses"""
    used = set()
    g = 0
    groups = []
    while 0x08000000 <= u32(rom, 0x00A54698 + 4 * g) < 0x0A000000:
        groups.append(u32(rom, 0x00A54698 + 4 * g) - 0x08000000); g += 1
    starts = sorted(set(groups))
    for ga in groups:
        nxt = min([s for s in starts if s > ga], default=None)
        n = 0
        while nxt is None or ga + 4 * n < nxt:
            h = u32(rom, ga + 4 * n)
            if not 0x08000000 <= h < 0x0A000000:
                break
            ev = u32(rom, h - 0x08000000 + 4)
            if 0x08000000 <= ev < 0x0A000000:
                ev -= 0x08000000
                objs = u32(rom, ev + 4)
                if rom[ev] and 0x08000000 <= objs < 0x0A000000:
                    for k in range(rom[ev]):
                        o = objs - 0x08000000 + 24 * k
                        if rom[o + 1] == 0x4E:
                            used.add(rom[o + 3])
            n += 1
    return used


def check(rom):
    assert u32(rom, EXT_LIT) == EXT_TABLE, "the hack's sprite table moved"
    t, rows = pal_table(rom)
    have = {u16(rom, t + 8 * i + 4) for i in range(rows)}
    for key, (n, tag) in AZ_PEOPLE.items():
        # 16 x 32 as the cast made it, or 32 x 32 since azpeople (2026-10-22: redrawn after the user's references)
        assert u16(rom, ext_at(n) + 2) == tag and tag in have and \
            struct.unpack_from("<Hhh", rom, ext_at(n) + 6) in ((0x100, 16, 32), (0x200, 32, 32)), \
            "sprite entry %d is not Area Zero's %s (patches/paldea/cast.py): build Area Zero first" % (n, key[3:])
    for n, was in WAS.items():
        assert rom[ext_at(n):ext_at(n) + 0x24].hex() == was, "sprite entry %d is not what it was" % n
    used = map_uses(rom)
    assert not used & set(WAS), "a map object uses sprite entry %s" % sorted(used & set(WAS))
    t, rows = pal_table(rom)
    tags = {u16(rom, t + 8 * i + 4) for i in range(rows)}
    assert not tags & set(PALETTES), "palette tag %s is in use" % sorted(tags & set(PALETTES))
    for key, (name, n, tag, base) in PEOPLE.items():
        e = main_at(rom, base)
        assert struct.unpack_from("<Hhh", rom, e + 6) == (0x100, 16, 32), "sprite %d is not 16x32" % base
        assert len(load(name)) == STEPS * 0x100, name
    assert struct.unpack_from("<Hhh", rom, ext_at(LIKE_32) + 6) == (0x200, 32, 32), "sprite entry %d" % LIKE_32
    assert rom[ext_at(LIKE_STILL) + 12] & 0x40, "sprite entry %d animates now" % LIKE_STILL
    for name, n, tag in STATUES.values():
        assert len(load(name)) == 0x200, name
    for name, n, tag in LIVE.values():
        assert len(load(name)) == 3 * 0x200, name


def put(rom, blob):
    """The pictures, frame tables, palettes and the longer palette table into `blob`."""
    for key, (name, n, tag, base) in PEOPLE.items():
        p = blob.put(("kpic", key), load(name))
        blob.put(("kframes", key), b"".join(struct.pack("<IHH", p + 0x100 * f, 0x100, 0) for f in range(STEPS)))
    for key, (name, n, tag) in STATUES.items():
        p = blob.put(("kpic", key), load(name))
        blob.put(("kframes", key), struct.pack("<IHH", p, 0x200, 0) * STEPS)
    for key, (name, n, tag) in LIVE.items():
        p = blob.put(("kpic", key), load(name))
        blob.put(("kframes", key), b"".join(struct.pack("<IHH", p + 0x200 * f, 0x200, 0) for f in FRAME_ORDER))
    for tag, name in PALETTES.items():
        blob.put(("kpal", tag), open(os.path.join(SPRITES, name + ".gbapal"), "rb").read())
    t, rows = pal_table(rom)
    old = bytes(rom[t:t + 8 * rows])
    tab = blob.put(("kpaltable",), old + bytes(8 * len(PALETTES)) + struct.pack("<IHH", 0, PAL_END_TAG, 0))
    for k, tag in enumerate(PALETTES):
        o = tab - blob.base + len(old) + 8 * k
        struct.pack_into("<H", blob.data, o + 4, tag)
        blob.ref(("kpal", tag), o)


def install(rom, blob):
    """After the blob is written: the six entries, and the code's palette table."""
    still = u32(rom, ext_at(LIKE_STILL) + 0x18)
    for key, (name, n, tag, base) in PEOPLE.items():
        e = bytearray(rom[main_at(rom, base):main_at(rom, base) + 0x24])
        struct.pack_into("<HHH", e, 0, 0xFFFF, tag, PAL_END_TAG)
        e[12] = SLOT_BY_TAG | (e[12] & 0x30)           # its shadow; animates (walks, turns to face you)
        struct.pack_into("<I", e, 0x1C, blob.addr[("kframes", key)])
        rom[ext_at(n):ext_at(n) + 0x24] = e
    for key, (name, n, tag) in STATUES.items():
        e = bytearray(rom[ext_at(LIKE_32):ext_at(LIKE_32) + 0x24])
        struct.pack_into("<HHH", e, 0, 0xFFFF, tag, PAL_END_TAG)
        e[12] = SLOT_BY_TAG | (e[12] & 0x30) | 0x40       # inanimate: a statue does not turn
        e[13] = 0                                         # no footprints
        struct.pack_into("<II", e, 0x18, still, blob.addr[("kframes", key)])
        rom[ext_at(n):ext_at(n) + 0x24] = e
    std = u32(rom, ext_at(LIKE_32) + 0x18)
    for key, (name, n, tag) in LIVE.items():
        e = bytearray(rom[ext_at(LIKE_32):ext_at(LIKE_32) + 0x24])
        struct.pack_into("<HHH", e, 0, 0xFFFF, tag, PAL_END_TAG)
        e[12] = SLOT_BY_TAG | (e[12] & 0x30)              # turns to face you (the standard animations)
        e[13] = 0
        struct.pack_into("<II", e, 0x18, std, blob.addr[("kframes", key)])
        rom[ext_at(n):ext_at(n) + 0x24] = e
    for r in PAL_REFS:
        struct.pack_into("<I", rom, r, blob.addr[("kpaltable",)])


def slot(key):
    for group in (PEOPLE, STATUES, LIVE):
        if key in group:
            return group[key][1]
    if key in AZ_PEOPLE:
        return AZ_PEOPLE[key][0]
    raise KeyError(key)


def tag_of(rom, gfx, ext):
    """the palette tag an object draws with (for counting palettes a screen)"""
    if gfx == 0x4E:
        for key, v in list(PEOPLE.items()) + list(STATUES.items()) + list(LIVE.items()):
            if v[1] == ext:
                return v[2]
        return u16(rom, ext_at(ext) + 2)
    return u16(rom, main_at(rom, gfx) + 2)
