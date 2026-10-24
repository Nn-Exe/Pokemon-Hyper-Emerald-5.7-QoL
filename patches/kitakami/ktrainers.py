"""Kitakami's trainers: Carmine (the bus stop) and Kieran (Loyalty Plaza, twice), with the battle pictures the user
approved (sprites/carmine_battle, kieran_battle: kit/chars/tp.py's repaints of trainer pictures 87 and 232).

  * Trainer rows 1358, 1359, 1360: the trainer table (0x090019F8, 40 bytes a row) ends in a hundred blank rows
    (1355-1454; nothing points into them: checked 2026-10-16), room the hack's author left as the move table has.
    Their trainer flags (ids above 0x357: id + 0x40C9, NOTES *Trainer flags*) are 0x4617-0x4619, free by Area
    Zero's checks (_testrun/kitakami/freecheck.py). Battles are `trainerbattle 3` (no intro; the flag is set at the
    end and never checked) with flag 0x273 on, so that a loss is not a white-out: the script reads the outcome and
    lets you try again (Kitakami has no place to come round in).
  * Class 33 "School Kid": Carmine and Kieran are Blueberry Academy students, and the class table has no spare row
    (73 on is not blank).
  * Battle pictures after the last the game has (250 and 251 up to 2026-10-21; 253 and 254 since Area Zero's people
    have 250-252 of their own: patches/paldea/cast.py). A trainer picture is four tables of entries, back to back
    (250 as the hack left them, 253 as Area Zero leaves them): the pictures
    (0x0901BE90, {LZ77 picture, 0x800, tag}), the palettes (0x0901C660, {LZ77 palette, tag}), the animations
    (0x0901CE30, a pointer each: gTrainerFrontAnimsPtrTable) and the coordinates (0x0901D218, {size, y offset, 0, 0}:
    gTrainerFrontPicCoords). All four are copied with ours after them; the 6, 18, 3 and 8 code words that hold their
    addresses (all real pointers by speciesx's is_pointer; nothing points into their middle) point at the copies.
    The tables are found through those words (REF_AT), not at a fixed address: Area Zero, earlier in the chain,
    copies them first (2026-10-21).
    Ours take the animations and coordinates of the pictures they were painted from (87, 232). Tags 250, 251 (as
    vanilla: a picture's tag is its number; checked unused). (The first build copied only the first two: the battle
    hung on a black screen, its sprite reading entry 250 of the animation table, past its end.)
  * Teams (mine; the official ones' Pokemon are not all in this game: no Dipplin, Poltchageist or Sinistcha):
    Carmine Lv 70-71, Kieran Lv 72-73 and Lv 74-75 with the Applin family and Incineroar.
"""
import os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
TRAINERS_TABLE = 0x010019F8
# the four tables of trainer pictures: the first of the code words that hold each address (all of a kind must
# agree), and how many words there are of each kind
REF_AT = {"pics": 0x0005DF78, "pals": 0x0005B784, "anims": 0x0006A1BC, "coords": 0x0005B614}
REFS = {"pics": 6, "pals": 18, "anims": 3, "coords": 8}
PAINTED_FROM = {"carmine": 87, "kieran": 232}       # ours, in this order after the game's last picture
AZ_NEMONA_ROW = 952                                  # Area Zero's Nemona: Part 2's Nemona wears her battle picture
SCHOOL_KID = 33
TRAINER_IV = 114
# key -> (row, picture, female, name, [(species, level, item, [moves])])
TRAINERS = {
    "carmine": (1358, "carmine", True, "Carmine", [
        ("Ninetales", 70, "Life Orb", ["Flamethrower", "Extrasensory", "Will-O-Wisp", "Nasty Plot"]),
        ("Ariados", 70, "Focus Sash", ["Megahorn", "Poison Jab", "Sucker Punch", "Toxic Spikes"]),
        ("Mabosstiff", 71, "Sitrus Berry", ["Crunch", "Psychic Fang", "Play Rough", "Wild Charge"]),
    ]),
    "kieran2": (1359, "kieran", False, "Kieran", [
        ("Appletun", 72, "Leftovers", ["Apple Acid", "Dragon Pulse", "Giga Drain", "Recover"]),
        ("Flapple", 73, "Life Orb", ["Grav Apple", "Dragon Claw", "Acrobatics", "Dragon Dance"]),
    ]),
    "kieran3": (1360, "kieran", False, "Kieran", [
        ("Appletun", 74, "Leftovers", ["Apple Acid", "Dragon Pulse", "Giga Drain", "Recover"]),
        ("Incineroar", 74, "Sitrus Berry", ["Flare Blitz", "Knock Off", "Fake Out", "U-Turn"]),
        ("Flapple", 75, "Life Orb", ["Grav Apple", "Dragon Claw", "Acrobatics", "Dragon Dance"]),
    ]),
}
# Part 2, Mochi Mayhem (2026-10-17): Nemona at Loyalty Plaza, before Pecharunt - the one trainer battle of Part 2 (the
# user: "remove unncessary battle"; the villagers', the grandparents', Arven's and Penny's went: they are woken by
# talking). Her team after the official one where this game has the Pokemon, Lv 80-82 (official 86-87). Row 1378:
# its trainer flag 0x462B free by freecheck.py. Her picture as in Area Zero (the game's 194 up to 2026-10-21, then
# Area Zero's own: whatever row 952 has). Entries: (row, picture: our key, the game's number or ("as row", row),
# female, name, team, class).
EXPERT, OLD_COUPLE, CHAMPION = 10, 56, 38
TRAINERS.update({
    "nemona2": (1378, ("as row", AZ_NEMONA_ROW), True, "Nemona", [
        ("Lycanroc", 80, "Life Orb", ["Accelerock", "Stone Edge", "Close Combat", "Crunch"]),
        ("Goodra", 80, "Leftovers", ["Draco Meteor", "Thunderbolt", "Flamethrower", "Sludge Bomb"]),
        ("Kommo-o", 81, "Life Orb", ["Close Combat", "Dragon Claw", "Poison Jab", "Dragon Dance"]),
        ("Pawmot", 81, "Focus Sash", ["Wild Charge", "Close Combat", "Ice Punch", "Mach Punch"]),
        ("Meowscarda", 82, "Life Orb", ["Leaf Blade", "Knock Off", "U-Turn", "Sucker Punch"]),
    ], CHAMPION),
})


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def lz_comp(data):
    """BIOS LZ77, greedy, never a distance of 1 (gen9_patch.py's)."""
    data, n = bytes(data), len(data)
    out = bytearray([0x10, n & 0xFF, n >> 8 & 0xFF, n >> 16 & 0xFF])
    seen, i = {}, 0

    def remember(pos):
        if pos + 3 <= n:
            seen.setdefault(data[pos:pos + 3], []).append(pos)

    while i < n:
        flag_at, flags = len(out), 0
        out.append(0)
        for bit in range(8):
            if i >= n:
                break
            best, dist, most = 0, 0, min(18, n - i)
            if most >= 3:
                for j in reversed(seen.get(data[i:i + 3], ())):
                    if i - j > 4096:
                        break
                    if i - j < 2:
                        continue
                    k = 3
                    while k < most and data[j + k] == data[i + k]:
                        k += 1
                    if k > best:
                        best, dist = k, i - j
                        if k == most:
                            break
            if best >= 3:
                flags |= 0x80 >> bit
                d = dist - 1
                out += bytes([(best - 3) << 4 | d >> 8, d & 0xFF])
                for p in range(i, i + best):
                    remember(p)
                i += best
            else:
                out.append(data[i])
                remember(i)
                i += 1
        out[flag_at] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def lz_dec(d, o=0):
    size = d[o + 1] | d[o + 2] << 8 | d[o + 3] << 16
    out, o = bytearray(), o + 4
    while len(out) < size:
        flags = d[o]; o += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                n, disp = (d[o] >> 4) + 3, ((d[o] & 0xF) << 8 | d[o + 1]) + 1
                o += 2
                for _ in range(n):
                    out.append(out[-disp])
            else:
                out.append(d[o]); o += 1
    return bytes(out)


def refs(rom, addr):
    import sys
    sys.path.insert(0, os.path.join(HERE, "..", "speciesx"))
    import speciesx_patch as SX
    word = struct.pack("<I", 0x08000000 + addr)
    out, k = [], 0
    while True:
        k = rom.find(word, k)
        if k < 0:
            return out
        if k % 4 == 0:
            assert SX.is_pointer(rom, k), "a word that reads as the table's address at %08X is not a pointer" % k
            out.append(k)
        k += 1


def tables(rom):
    """({name: file offset} of the four tables the code reads now, how many pictures they hold)"""
    t = {}
    for name, at in REF_AT.items():
        t[name] = u32(rom, at) - 0x08000000
    n = (t["pals"] - t["pics"]) // 8
    assert t["pals"] == t["pics"] + 8 * n and t["anims"] == t["pals"] + 8 * n and t["coords"] == t["anims"] + 4 * n, \
        "the trainer picture tables are not back to back"
    return t, n


def numbers(rom):
    """our pictures' numbers: after the last the game has"""
    t, n = tables(rom)
    return {key: n + k for k, key in enumerate(PAINTED_FROM)}


def picture(rom, pic):
    """a TRAINERS entry's picture -> its number"""
    if isinstance(pic, str):
        return numbers(rom)[pic]
    if isinstance(pic, tuple):
        assert pic[0] == "as row"
        return rom[TRAINERS_TABLE + 40 * pic[1] + 3]
    return pic


NEMONA_N = 0xC8                                      # "N" in the game's text: row 952's name starts with it


def check(rom, species_id, move_id, item_id):
    for key, t in TRAINERS.items():
        row, pic, female, name, team = t[:5]
        e = TRAINERS_TABLE + 40 * row
        assert not any(rom[e:e + 28]) and not any(rom[e + 29:e + 40]), "trainer row %d is not blank" % row
        for sp, lv, item, moves in team:
            species_id(sp); item_id(item)
            for m in moves:
                move_id(m)
    t, n = tables(rom)
    for name, addr in t.items():
        assert len(refs(rom, addr)) == REFS[name], "the trainer %s table has other references now" % name
    for i in range(n):
        assert 0x08000000 <= u32(rom, t["anims"] + 4 * i) < 0x0A000000, "animation %d" % i
        assert 0x08000000 <= u32(rom, t["pics"] + 8 * i) < 0x0A000000, "picture %d" % i
    tags = {u16(rom, t["pics"] + 8 * i + 6) for i in range(n)} | {u16(rom, t["pals"] + 8 * i + 4) for i in range(n)}
    assert not tags & set(numbers(rom).values()), "trainer picture tag %s is in use" % sorted(numbers(rom).values())
    az = rom[TRAINERS_TABLE + 40 * AZ_NEMONA_ROW + 3]
    assert 250 <= az < n and rom[TRAINERS_TABLE + 40 * AZ_NEMONA_ROW + 4] == NEMONA_N, \
        "trainer row %d is not Area Zero's Nemona in a picture of her own (picture %d)" % (AZ_NEMONA_ROW, az)


def put(rom, blob, enc, species_id, move_id, item_id):
    """the pictures, the longer tables, the parties; -> {key: (row, 40-byte entry, party key)} for install()"""
    t, npics = tables(rom)
    nums = numbers(rom)
    for key in PAINTED_FROM:
        pic = open(os.path.join(HERE, "sprites", key + "_battle.4bpp"), "rb").read()
        pal = open(os.path.join(HERE, "sprites", key + "_battle.gbapal"), "rb").read()
        assert lz_dec(lz_comp(pic)) == pic and lz_dec(lz_comp(pal)) == pal
        blob.put(("tpic", key), lz_comp(pic))
        blob.put(("tpal", key), lz_comp(pal))
    old_pics = bytes(rom[t["pics"]:t["pics"] + 8 * npics])
    old_pals = bytes(rom[t["pals"]:t["pals"] + 8 * npics])
    tp = blob.put(("ktrainer", "pics"), old_pics + bytes(8 * len(PAINTED_FROM)))
    tq = blob.put(("ktrainer", "pals"), old_pals + bytes(8 * len(PAINTED_FROM)))
    anims = bytes(rom[t["anims"]:t["anims"] + 4 * npics]) + b"".join(
        rom[t["anims"] + 4 * PAINTED_FROM[k]:t["anims"] + 4 * PAINTED_FROM[k] + 4] for k in PAINTED_FROM)
    coords = bytes(rom[t["coords"]:t["coords"] + 4 * npics]) + b"".join(
        rom[t["coords"] + 4 * PAINTED_FROM[k]:t["coords"] + 4 * PAINTED_FROM[k] + 4] for k in PAINTED_FROM)
    blob.put(("ktrainer", "anims"), anims)
    blob.put(("ktrainer", "coords"), coords)
    for k, key in enumerate(PAINTED_FROM):
        n = nums[key]
        assert n == npics + k
        struct.pack_into("<HH", blob.data, tp - blob.base + 8 * n + 4, 0x800, n)
        blob.ref(("tpic", key), tp - blob.base + 8 * n)
        struct.pack_into("<HH", blob.data, tq - blob.base + 8 * n + 4, n, 0)
        blob.ref(("tpal", key), tq - blob.base + 8 * n)
    entries = {}
    for key, tr in TRAINERS.items():
        row, pic, female, name, team = tr[:5]
        cls = tr[5] if len(tr) > 5 else SCHOOL_KID
        party = b"".join(struct.pack("<HHHH4H", TRAINER_IV, lv, species_id(sp), item_id(item),
                                     *[move_id(m) for m in moves]) for sp, lv, item, moves in team)
        blob.put(("party", key), party)
        nm = enc(name) + b"\xFF"
        e = bytearray(40)
        e[0], e[1], e[2], e[3] = 3, cls, 0x80 if female else 0, picture(rom, pic)
        e[4:4 + len(nm)] = nm
        struct.pack_into("<III", e, 24, 0, 0xFF, len(team))
        entries[key] = (row, e, ("party", key))
    return entries


def install(rom, blob, entries):
    t, n = tables(rom)
    for name, addr in t.items():
        for r in refs(rom, addr):
            struct.pack_into("<I", rom, r, blob.addr[("ktrainer", name)])
    for key, (row, e, pk) in entries.items():
        struct.pack_into("<I", e, 36, blob.addr[pk])
        o = TRAINERS_TABLE + 40 * row
        rom[o:o + 40] = e


def row(key): return TRAINERS[key][0]
