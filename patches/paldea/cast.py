"""Area Zero's people in pictures of their own (2026-10-21). Up to then they wore the game's own people: Jacq
main sprite 9, Arven 37, Nemona 20, Penny 58, AI Sada 202, AI Turo 46, and in battle Nemona picture 194, AI Sada
218, AI Turo 31. The user: "can u custom draw npcs in paldea area zero? rightnow reusing npcs make the game look
cheap", then "both overworld sprites and in battle scene"; on the mock-up sheet: "everything is great". The
drawings are in sprites/ (people_map.py, people_battle.py; people.py writes the .4bpp and .gbapal files read here).

  * Map sprites: six entries of the hack's sprite table (0x0839CF00 + 0x24 * n, drawn by an object with graphics
    0x4E and n in its template's fourth byte) that no object of any map uses (174-178, 180: the hack's own unused
    people; patches/kitakami/sprite_slots.py lists them). Each is a copy of the main table's entry for the sprite
    it was drawn over (its OAM, subsprites, walking animations and shadow), with our nine frames and our palette
    tag: they walk and turn like any person. Palette slot 2 is "by tag" to the hack, as for Area Zero's other
    sprites (mons.py).
  * Palettes: four tags after Area Zero's and Kitakami's (0x1141-0x1144), rows in Area Zero's copy of the field
    palette table (mons.put). Arven and Penny share one, Nemona and Jacq the other: in Mossdeep's ending all four
    stand by the hole next to the town's own people (palettes 0x1103, 0x1105, 0x1106) and the hole (0x1119), and
    the game has six palettes for the objects in sight (check.py's PALETTES). AI Sada and AI Turo have one each.
  * The pictures go in the sprite block, which since this patch runs on to the end of the ROM (0x09FFC000 ..
    0x0A000000 added: blank in the hack's own ROM, whose last used byte is 0x09F82518; no word of code or of the
    header points into it; the 49 words elsewhere whose value falls in it are bytes of pictures, tunes and texts,
    46 of them in the hack's own ROM at the same place: proof in NOTES, *Area Zero's people*).
  * Battle pictures 250-252 (Nemona, AI Sada, AI Turo), drawn over pictures 114, 100 and 187. A trainer picture is
    four tables of 250 entries, back to back (0x0901BE90 pictures {LZ77 picture, 0x800, tag}, 0x0901C660 palettes
    {LZ77 palette, tag}, 0x0901CE30 animations, 0x0901D218 coordinates {size, y offset}): copied here longer,
    still back to back, and the 6, 18, 3 and 8 words of code that hold their addresses point at the copies (the
    Quest Log's portraits among them). Ours take the animations and coordinates of the pictures they were drawn
    over, and their own numbers as tags (as vanilla). Kitakami copies the tables again after this patch and finds
    them through the same words (ktrainers.py).
"""
import os, struct

import tiles as TL

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITES = os.path.join(HERE, "sprites")

MAIN_TABLE = 0x00505620
PAL_END_TAG = 0x11FF
SLOT_BY_TAG = 2
FRAMES = 9
# key -> (slot in the hack's sprite table, palette tag, the main table's sprite it was drawn over)
PEOPLE = {
    "nemona": (174, 0x1142, 14), "arven": (175, 0x1141, 25), "penny": (176, 0x1141, 85),
    "jacq": (177, 0x1142, 96), "sada": (178, 0x1143, 202), "turo": (180, 0x1144, 172),
}
WAS = {   # the six entries as they were (2026-10-21): the hack's unused people
    174: "ffff0411ff11000110002000a201000814955008a095500800915008a8d72609a8c62e08",
    175: "ffff0511ff11000110002000a201000814955008a095500800915008b0d72609a8c62e08",
    176: "ffff0f11ff11000110002000a201000814955008a095500800915008b8d72609a8c62e08",
    177: "ffff0611ff11000110002000a201000814955008a095500800915008c4d72609a8c62e08",
    178: "ffff0511ff11000110002000a201000814955008a095500800915008ccd72609a8c62e08",
    180: "ffff0511ff11000110002000a201000814955008a095500800915008dcd72609a8c62e08",
}

PIC_TABLE, PAL_TABLE, ANIM_TABLE, COORD_TABLE, NPICS = 0x0101BE90, 0x0101C660, 0x0101CE30, 0x0101D218, 250
REFS = {"pics": 6, "pals": 18, "anims": 3, "coords": 8}
# key -> (picture number, the picture it was drawn over)
BATTLE = {"nemona": (250, 114), "sada": (251, 100), "turo": (252, 187)}


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def sprite(key):
    """(graphics, ext) of a person's object"""
    return 0x4E, PEOPLE[key][0]


def tags():
    """slot -> palette tag (for check.py's count of palettes in sight)"""
    return {slot: tag for slot, tag, base in PEOPLE.values()}


def load(name, size):
    b = open(os.path.join(SPRITES, name), "rb").read()
    assert len(b) == size, "sprites/%s is not one people.py made" % name
    return b


def main_at(rom, n): return u32(rom, MAIN_TABLE + 4 * n) - 0x08000000


def map_uses(rom):
    """every entry of the hack's sprite table that an object of a map uses (patches/kitakami/ksprites.py's scan)"""
    used, groups, g = set(), [], 0
    while 0x08000000 <= u32(rom, 0x00A54698 + 4 * g) < 0x0A000000:
        groups.append(u32(rom, 0x00A54698 + 4 * g) - 0x08000000)
        g += 1
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


def refs(rom, addr):
    """the words of code that hold `addr` (a table's address)"""
    word, out, k = struct.pack("<I", 0x08000000 + addr), [], 0
    while True:
        k = rom.find(word, k)
        if k < 0:
            return out
        if k % 4 == 0:
            out.append(k)
        k += 1


def check(rom, ext_table, field_tags, own_tags):
    """What this patch takes is as it was. field_tags: the tags in the code's field palette table; own_tags: Area
    Zero's other sprites' tags."""
    for slot, was in WAS.items():
        e = ext_table - 0x08000000 + 0x24 * slot
        assert rom[e:e + 0x24].hex() == was, "sprite entry %d is not the unused person it was" % slot
    used = map_uses(rom)
    assert not used & set(WAS), "a map's object uses sprite entry %s" % sorted(used & set(WAS))
    for key, (slot, tag, base) in PEOPLE.items():
        assert tag not in field_tags and tag not in own_tags and tag != PAL_END_TAG, "palette tag %04X is in use" % tag
        assert struct.unpack_from("<Hhh", rom, main_at(rom, base) + 6) == (0x100, 16, 32), "sprite %d is not 16x32" % base
        load(key + ".4bpp", FRAMES * 0x100)
    for key, (slot, tag, base) in PEOPLE.items():          # people who share a tag share their colours
        for other, (s2, t2, b2) in PEOPLE.items():
            if t2 == tag:
                assert load(key + ".gbapal", 32) == load(other + ".gbapal", 32), (key, other)
    # the battle pictures' tables: where the hack left them, back to back, and only these words hold their addresses
    for name, addr in (("pics", PIC_TABLE), ("pals", PAL_TABLE), ("anims", ANIM_TABLE), ("coords", COORD_TABLE)):
        assert len(refs(rom, addr)) == REFS[name], "the trainer %s table has other references now" % name
    assert PAL_TABLE == PIC_TABLE + 8 * NPICS and ANIM_TABLE == PAL_TABLE + 8 * NPICS
    assert COORD_TABLE == ANIM_TABLE + 4 * NPICS
    used_tags = {u16(rom, PIC_TABLE + 8 * i + 6) for i in range(NPICS)} | {u16(rom, PAL_TABLE + 8 * i + 4) for i in range(NPICS)}
    for key, (n, base) in BATTLE.items():
        assert n not in used_tags, "trainer picture tag %d is in use" % n
        assert TL.lz(rom, u32(rom, PIC_TABLE + 8 * base) - 0x08000000)[:0x800], "picture %d" % base
        load(key + "_battle.4bpp", 0x800)
        load(key + "_battle.gbapal", 32)
    assert sorted(n for n, b in BATTLE.values()) == list(range(NPICS, NPICS + len(BATTLE)))


def palette_rows():
    """[(tag, the key its palette goes in under)]: the field palette table's rows for the people (mons.put)"""
    rows = []
    for key, (slot, tag, base) in PEOPLE.items():
        if (tag, ("person pal", tag)) not in rows:
            rows.append((tag, ("person pal", tag)))
    return rows


def put_sprites(blob):
    """the pictures, their frame tables and the four palettes, into the sprite block"""
    for key, (slot, tag, base) in PEOPLE.items():
        p = blob.put(("person", key), load(key + ".4bpp", FRAMES * 0x100))
        blob.put(("person frames", key), b"".join(struct.pack("<IHH", p + 0x100 * f, 0x100, 0) for f in range(FRAMES)))
        if ("person pal", tag) not in blob.addr:
            blob.put(("person pal", tag), load(key + ".gbapal", 32))


def install_sprites(rom, blob, ext_table):
    """after the sprite block is in the ROM: the six entries"""
    for key, (slot, tag, base) in PEOPLE.items():
        e = bytearray(rom[main_at(rom, base):main_at(rom, base) + 0x24])
        struct.pack_into("<HHH", e, 0, 0xFFFF, tag, PAL_END_TAG)
        e[12] = SLOT_BY_TAG | (e[12] & 0x30)              # its shadow; it walks and turns to face you
        struct.pack_into("<I", e, 0x1C, blob.addr[("person frames", key)])
        o = ext_table - 0x08000000 + 0x24 * slot
        rom[o:o + 0x24] = e


def put_pictures(rom, blob):
    """the battle pictures (compressed) and the four tables, longer, back to back"""
    n = NPICS + len(BATTLE)
    by_number = {num: (key, base) for key, (num, base) in BATTLE.items()}
    for key in BATTLE:
        pic, pal = load(key + "_battle.4bpp", 0x800), load(key + "_battle.gbapal", 32)
        cp, cq = TL.lz_comp(pic), TL.lz_comp(pal)
        assert TL.lz(cp, 0) == pic and TL.lz(cq, 0)[:32] == pal
        blob.put(("tpic", key), cp)
        blob.put(("tpal", key), cq)
    pics = bytearray(rom[PIC_TABLE:PIC_TABLE + 8 * NPICS]) + bytes(8 * len(BATTLE))
    pals = bytearray(rom[PAL_TABLE:PAL_TABLE + 8 * NPICS]) + bytes(8 * len(BATTLE))
    anims = bytearray(rom[ANIM_TABLE:ANIM_TABLE + 4 * NPICS])
    coords = bytearray(rom[COORD_TABLE:COORD_TABLE + 4 * NPICS])
    for num in range(NPICS, n):
        key, base = by_number[num]
        struct.pack_into("<HH", pics, 8 * num + 4, 0x800, num)
        struct.pack_into("<HH", pals, 8 * num + 4, num, 0)
        anims += rom[ANIM_TABLE + 4 * base:ANIM_TABLE + 4 * base + 4]
        coords += rom[COORD_TABLE + 4 * base:COORD_TABLE + 4 * base + 4]
    t = blob.put(("ttables",), bytes(pics + pals + anims + coords))
    for num in range(NPICS, n):
        key, base = by_number[num]
        blob.ref(("tpic", key), t - blob.base + 8 * num)
        blob.ref(("tpal", key), t - blob.base + 8 * n + 8 * num)


def install_pictures(rom, blob):
    """after the blob is in the ROM: the code reads the longer tables"""
    n = NPICS + len(BATTLE)
    t = blob.addr[("ttables",)]
    new = {"pics": t, "pals": t + 8 * n, "anims": t + 16 * n, "coords": t + 20 * n}
    for name, old in (("pics", PIC_TABLE), ("pals", PAL_TABLE), ("anims", ANIM_TABLE), ("coords", COORD_TABLE)):
        words = refs(rom, old)
        assert len(words) == REFS[name]
        for w in words:
            struct.pack_into("<I", rom, w, new[name])
