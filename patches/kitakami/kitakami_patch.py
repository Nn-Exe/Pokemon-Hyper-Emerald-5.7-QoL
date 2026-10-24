"""Kitakami: Mossui Town, for the Ogerpon story (Hyper Emerald v5.7).
usage: python kitakami_patch.py <in.gba> <out.gba> [placements.txt]

Where everybody and everything stands is kplaces.py's (since 2026-10-17, the user: "I want to edit placement
myself"): a placements file named on the command line (written from the built-in positions if it is not there yet),
the built-in positions with none. A build in which something stands where it cannot is refused (Problems).

Applied on top of the finished game (rom/: the main chain + speciesx + gen9 + paldea), the way summitfix is: it
needs nothing of the Crest ROM, so it builds on any machine. The story the user approved is
rom/unreleased/kitakami/STORY.md. Kitakami is one town (the user, 2026-10-16: "remove road and remove oni
mountain, keep only town"; the same day, "the den is unneccesary"); its rooms are kinteriors.py's, its wild
Pokemon kwild.py's. No people (but the nurse) or way in yet (tests warp there).

What it writes, all in 0x09E40000..0x09E80000 (2026-10-16; the Mac's 0x09B40000..0x09C00000 is gen9rest's since the
whole of Gen 9 went in): the middle of the zero run 0x09E10044..0x09F00000, the same in the hack's own ROM (after
the forms table, before the hack's code at 0x09F00000); no header word or code literal points in (speciesx's
is_pointer test) and nothing in the repo names an address in the run - _testrun/space/kitakami_space.py:
  * Kitakami's secondary tileset (tileset.py);
  * Mossui Town after the last map of group 35 (Area Zero's are 89-105), then its rooms (kworld.py draws the town);
  * the layout table and group 35's table, copied with the new entries (paldea's maps.py, pointed at the tables
    the ROM has now: Area Zero's copies);
  * the name of map section 187 (Route 225 of Sinnoh: no map uses it, the region map places it at 0,0): "Mossui
    Town" - its entry points at a new string, as Area Zero did with 186 (187's string is shared with 200's).
"""
import hashlib, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "paldea"))
import tileset as T
import kworld as WD
import kinteriors as KI
import kwild as KW
import kpeople as KP
import ksprites as KSP
import kstory as KS
import ktrainers as KT
import kasm as KA
import kplaces as KPL
import kjournal as KJ
import maps as M                                       # patches/paldea/maps.py
from lib import Blob, enc, box                         # patches/paldea/lib.py

FREE, FREE_END = 0x01E40000, 0x01E80000
GROUP = 35
LAYOUT_REFS = M.LAYOUT_REFS
MAPSEC_TABLE = 0x005A147C
MAPSECS = {"mossui": (187, "Mossui Town")}
MAPSEC_WAS = {187: "Route 225"}
MUSIC = 545                                            # Bellchime Trail's
MAP_TYPE = 1                                           # a town: outdoors, so the hour colours it
SOURCE = (35, 74)                                      # the header the new ones start from (Bellchime Trail)
BORDER = [WD.W.blk(m, 1) for m in WD.MAPLE_BORDER]
# The hack's guard on buying (docs/NOTES, gen9rest's test 2): the buy step jumps through 0x080E0F00 to 0x096FFF00,
# which checks the item bought and every item of the shop's list against a bitmap of the items a shop may sell -
# byte 0x09E0FE5F - (item >> 3), bit item & 7; its one literal is at 0x096FFF88 - and resets the game when one is
# not in it. Sweet Apple and Tart Apple are not (test 6's story run: buying at the apple stall reset the game).
SHOP_BITS_WORD, SHOP_BITS_TOP = 0x016FFF88, 0x01E0FE5F


def shop_allowed(rom, item):
    return (rom[SHOP_BITS_TOP - (item >> 3)] >> (item & 7)) & 1


def allow_shop_items(rom, item_ids):
    """give the stalls' items their bits in the hack's shop bitmap; returns the ones that needed it"""
    assert u32(rom, SHOP_BITS_WORD) == 0x08000000 + SHOP_BITS_TOP, "the shop guard's bitmap moved"
    given = []
    for item in item_ids:
        if not shop_allowed(rom, item):
            rom[SHOP_BITS_TOP - (item >> 3)] |= 1 << (item & 7)
            given.append(item)
    return given


def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def decode(rom, o):
    out = ""
    while rom[o] != 0xFF and len(out) < 30:
        b = rom[o]; o += 1
        out += chr(65 + b - 0xBB) if 0xBB <= b <= 0xD4 else chr(97 + b - 0xD5) if 0xD5 <= b <= 0xEE else \
            str(b - 0xA1) if 0xA1 <= b <= 0xAA else " " if b == 0 else "?"
    return out


def name_id(rom, table, size, count, name, what, skip=()):
    """the entry called `name` in one of the ROM's name tables (its pointer in the ROM header at `table`): the
    first, where a name is there twice (the hack's held items have a second copy), that is not in `skip`"""
    t = u32(rom, table) - 0x08000000
    want = enc(name) + b"\xFF"
    first = None
    for i in range(count):
        e = rom[t + size * i:t + size * i + size]
        if e[:len(want)] == want or (len(want) == size + 1 and e == want[:size]):
            if i not in skip:
                return i
            first = i if first is None else first
    if first is not None:
        return first
    raise AssertionError("no %s %r in this ROM" % (what, name))


# The hack's battle-form table: {u16 species, u16 form, u16 item}, 0xFEFE ends; item 0xEFEF marks a Gigantamax form
# (tools/romdata/forms.py). A Gigantamax slot has its Pokemon's name and comes first for 21 of them: "Appletun" is 270
# (Gigantamax) and 1143, "Flapple" 269 and 1142. Until 2026-10-24 Kieran's two came out as the Gigantamax slots and
# showed the Gigantamax pictures in battle.
BATTLE_FORMS, GMAX_MARK = 0x00C9A3B0, 0xEFEF


def gmax_slots(rom):
    u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
    assert (u16(BATTLE_FORMS + 24), u16(BATTLE_FORMS + 26), u16(BATTLE_FORMS + 28)) == (3, 254, GMAX_MARK), \
        "the battle-form table moved"
    out, o = set(), BATTLE_FORMS
    while u16(o) != 0xFEFE:
        if u16(o + 4) == GMAX_MARK:
            out.add(u16(o + 2))
        o += 6
    assert {269, 270} <= out, "Flapple's and Appletun's Gigantamax slots are not where they were"
    return out


def lookups(rom):
    gmax = gmax_slots(rom)
    sp = lambda n: name_id(rom, 0x144, 11, 1300, n, "species", gmax)
    mv = lambda n: name_id(rom, 0x148, 13, 1030, n, "move")
    it = lambda n: name_id(rom, 0x1C8, 44, 1000, n, "item")
    return sp, mv, it


def layout_table(rom):
    """where the layout table is now, and the highest layout id group 35's maps name (Area Zero's are the last:
    846-862). Scanning every group would read past a group's end into the next one's table."""
    at = {u32(rom, r) for r in LAYOUT_REFS}
    assert len(at) == 1, "the layout table references disagree: %s" % at
    garr, n = M.group_count(rom, GROUP)
    top = max(struct.unpack_from("<H", rom, u32(rom, garr + 4 * k) - 0x08000000 + 18)[0] for k in range(n))
    return at.pop() - 0x08000000, top


class Problems(Exception):
    """things in the placements that would not work in the game: .lines says what, in plain words"""
    def __init__(self, lines):
        Exception.__init__(self, "; ".join(lines))
        self.lines = lines


def grouped(problems):
    """The checks' lines with one line for a thing wrong at many moments of the story: "<what> (at: <moments>)"."""
    import re
    titles = dict(KPL.MOMENTS)
    label_of = {"the wake scene": "wake", "the festival scene": "festival"}
    order, by_msg = [], {}
    for p in problems:
        m = re.match(r"(stage (\d+)(?: beaten .*?)?|the wake scene|the festival scene): (.*)$", p)
        if not m:
            key, when = p, None
        else:
            st = m.group(2)
            key, when = m.group(3), (("p" if int(st) >= 12 else "s") + st) if st else label_of[m.group(1)]
        if key not in by_msg:
            by_msg[key] = []
            order.append(key)
        if when and when not in by_msg[key]:
            by_msg[key].append(when)
    out = []
    every = [k for k, t in KPL.MOMENTS]
    for key in order:
        when = by_msg[key]
        if not when:
            out.append(key)
        elif all(k in when for k in every):
            out.append("%s (the whole story)" % key)
        else:
            idx = sorted(every.index(w) for w in when if w in every)
            names = [titles[every[i]] for i in idx]
            if len(idx) >= 3 and idx == list(range(idx[0], idx[-1] + 1)):
                names = ["from %s to %s" % (titles[every[idx[0]]], titles[every[idx[-1]]])]
            if "festival" in when:
                names.append("the festival's scene")
            out.append("%s (at: %s)" % (key, "; ".join(names)))
    return out


def build(inp, outp, placements=None, told=None, signs=True):
    """placements: a placements file (kplaces), or None for the built-in positions; told: a dict to fill with what
    the editor needs (the maps' numbers, sizes and blocks, the town's marks, the positions used); signs=False: the
    town's signs are not drawn (the editor's picture of the ground)"""
    values = KPL.load(placements) if placements else KPL.Values(KPL.DEFAULTS)
    used = KPL.apply(values)
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    # the finished game, with Area Zero in it, and this not applied yet
    lay_at, lay_n = layout_table(rom)
    garr, n35 = M.group_count(rom, GROUP)
    assert n35 == 106, "group 35 has %d maps: expected Area Zero's 106 (apply on top of rom/)" % n35
    assert lay_n == 862, "the layout table names %d layouts: expected 862 (Area Zero's)" % lay_n
    assert not any(rom[FREE:FREE_END]), "0x%08X..0x%08X is not empty: applied already?" % (FREE + 0x08000000, FREE_END + 0x08000000)
    for sec, was in MAPSEC_WAS.items():
        assert decode(rom, u32(rom, MAPSEC_TABLE + 8 * sec + 4) - 0x08000000) == was, "map section %d moved" % sec
    M.LAYOUTS, M.LAYOUT_COUNT = lay_at, lay_n          # paldea's maps.py: the tables as the ROM has them now
    KSP.check(rom)                                     # the sprite entries and palette tags it takes are free
    KP.check(rom)                                      # Mossdeep is as Area Zero left it
    KA.check(rom)                                      # the tint routine's hour read; kit_hour's room
    KJ.check(rom)                                      # the Quest Log's Legends as gen9journal left them
    species_id, move_id, item_id = lookups(rom)
    KT.check(rom, species_id, move_id, item_id)        # the trainer rows, the picture tables' references
    for name, n in KS.OGERPON_SPECIES.items():
        assert name_id(rom, 0x144, 11, 1300, "Ogerpon", "species") <= n <= 1231, name

    blob = Blob(0x08000000 + FREE)
    town, ov, marks = WD.mossui(rom, signs=signs)
    bad = sorted({(x, y + 1 - part[1]) for (x, y), (kind, what) in ov.items() if kind == "art"
                  for piece, part, ground in [what] if piece == "legend board" and not T.can_hold(rom, ground)})
    board_problems = ["signboard %d at %d,%d stands where something else is drawn (a tree, a roof, a fence, water's "
                      "edge...): it needs plain ground, and so does the tile above it for its roof" % (
                          WD.LEGEND_SIGNS.index(xy) + 1 if xy in WD.LEGEND_SIGNS else 0, xy[0], xy[1]) for xy in bad]
    if bad:                                             # drawn as plain signs, so the rest can still be checked
        town, ov, marks = WD.mossui(rom, signs=signs, plain=bad)
    built = T.build(rom, WD.needed((town, ov, WD.TEAL)), WD.art_used(ov))
    tkey = T.install(blob, built)
    b = WD.finish(town, ov, WD.TEAL, built.ids)

    names = {}
    for key, (sec, name) in MAPSECS.items():
        names[sec] = blob.put(("name", key), enc(name) + b"\xFF", 1)
    mossui = M.Map("mossui", SOURCE, len(b[0]), len(b), b, border=BORDER, music=MUSIC, weather=0,
                   mapsec=MAPSECS["mossui"][0], map_type=MAP_TYPE, popup=True, tilesets=(T.GENERAL, tkey))
    rooms = KI.make(rom, blob, M, MAPSECS["mossui"][0])
    door = {k: v[0] for k, v in marks.items() if k != "homes"}
    KI.wire(rooms, mossui, marks["homes"], door)
    KI.people(rooms, M)
    blob.addr[("script", KI.NURSE)] = KI.NURSE           # a script of the game's own: the address itself
    maps = [mossui] + list(rooms.values())
    numbers = M.numbers(rom, maps, {m.key: GROUP for m in maps})
    ids = {n: species_id(n) for n in KS.L3_SPECIES.values()}
    ids["Okidogi"] = species_id("Okidogi")
    ids["Pecharunt"] = species_id(KS.PECHARUNT)                 # Part 2
    for n in [KS.L3_ITEM] + sum(KS.SHOPS.values(), []):
        ids["item:" + n] = item_id(n)
    trainers = KT.put(rom, blob, enc, species_id, move_id, item_id)
    journal = KJ.put(rom, blob, KS.LEVEL, KS.P2_LEVEL)    # Kitakami's five: counted Legends rows
    finish, people = KP.make(rom, blob, M, mossui, rooms, marks, b, numbers, WD.LEGEND_SIGNS, box, ids,
                             {k: KT.row(k) for k in KT.TRAINERS}, KA.mask_code)
    problems, palettes = KP.layout_report(rom, mossui, rooms, b, WD.W, marks, WD.LEGEND_SIGNS)
    problems = grouped(board_problems + problems)
    if problems and signs:
        raise Problems(problems)
    if told is not None:
        told["values"], told["marks"], told["notes"] = used, marks, list(values.notes)
        told["maps"] = {m.key: {"w": m.w, "h": m.h, "blocks": [list(r) for r in m.blocks]} for m in maps}
        told["problems"] = problems
    known = {}
    KW.check(rom)
    lt, gas = M.install(rom, blob, maps, {m.key: GROUP for m in maps}, known)
    assert all(known[k] == numbers[k] for k in numbers), "the maps' numbers moved between the scripts and install"
    wild_key = KW.install(rom, blob, enc, known)
    h = blob.addr[("header", "mossui")] - blob.base     # bikes and running outdoors; the name shown on entry
    blob.data[h + 26] = 0x01 | 0x04 | 0x08
    data = blob.link()
    assert FREE + len(data) <= FREE_END, "Kitakami outgrew its space (%d bytes)" % len(data)
    rom[FREE:FREE + len(data)] = data
    M.repoint_tables(rom, lt, gas)
    KW.repoint(rom, blob.addr[wild_key])
    for sec, addr in names.items():
        struct.pack_into("<I", rom, MAPSEC_TABLE + 8 * sec + 4, addr)
    stamp, az, nsites = finish(rom)
    KT.install(rom, blob, trainers)
    legends = journal(rom)
    KA.install_bgmask(rom, *numbers["mossui"])          # the night tint over palette 12 too (the market)
    hour = KA.install_hour(rom, *numbers["mossui"], [(KS.F_PLAZA, KS.F_TRUTH, KA.NIGHT),
                                                     (KS.F_P2_START, KS.F_PECHARUNT, KA.NIGHT)])
    sold = sorted({ids["item:" + n] for n in sum(KS.SHOPS.values(), [])})
    given = allow_shop_items(rom, sold)
    assert all(shop_allowed(rom, i) for i in sold)
    if told is not None:
        for k, v in known.items():
            told["maps"][k]["map"] = v
    open(outp, "wb").write(rom)
    print("Stalls: %d items; the shop guard's bitmap now allows %s" % (
        len(sold), ", ".join("%s (%d)" % (n, ids["item:" + n]) for n in sorted({n for v in KS.SHOPS.values() for n in v})
                             if ids["item:" + n] in given) or "nothing new"))
    print("Story: trainers %s; battle pictures %s (the picture tables copied); the festival's evening: "
          "kit_hour %d bytes at 0x%08X, bl at 0x%08X" % (", ".join("%s %d" % (k, KT.row(k)) for k in KT.TRAINERS),
                                                          ", ".join("%s %d" % (k, trainers[k][1][3]) for k in KT.TRAINERS),
                                                          hour, KA.HOUR_AT, 0x08000000 + KA.HOOK))
    print("People: %d in Mossui, %d inside, %d signs, %d scripts, %d texts; at most %d palettes a screen; stamp "
          "%04X (Area Zero's %04X, rewritten in %d places); Briar in Mossdeep as object %d" % (
              len(mossui.objs), sum(len(r.objs) for r in rooms.values()), len(mossui.bgs), len(people.scripts),
              len(people.texts), palettes, stamp, az, nsites, KP.BRIAR_LOCAL))
    past = sorted(v for v in built.ids.values() if v >= T.FIRST)
    print("Kitakami: %d bytes at 0x%08X; maps %s; tileset: ours %d-%d, %d drawn tiles in base numbers no map uses, "
          "%d numbers and %d cells left, rows %s" % (
        len(data), 0x08000000 + FREE, ", ".join("%s %d/%d" % (m.key, *known[m.key]) for m in maps),
        past[0], past[-1], len(built.ids) - len(past), built.numbers_left, built.free_cells_left, built.rows))
    print("sha1", hashlib.sha1(rom).hexdigest())


if __name__ == "__main__":
    try:
        build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    except Problems as e:
        print("Nothing was built. %d thing%s to put right:" % (len(e.lines), "s" * (len(e.lines) > 1)))
        for line in e.lines:
            print("  - " + line)
        sys.exit(1)
