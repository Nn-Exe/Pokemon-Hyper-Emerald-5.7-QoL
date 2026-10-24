"""Kitakami's insides (milestone 2): rooms of the game's own, cropped out of the maps that hold them, and every
door wired both ways.

  Kitakami Hall     one floor, the Mask Hall: drawn for Kitakami (khall.py, 2026-10-17: the user, "can u redesign
                    the interior hall to match the theme?"): shoji and dark wood, a tatami stage with the three masks
                    in glass cases, a red carpet, cushions; its own tileset. (Until 2026-10-17 the top floor of a
                    hotel - lobby, rooms, your room with a bed - then that floor alone, 37/102's pillared hall: the
                    user, "we need only one floor".) Its music and header are still 37/102's.
  the family house  the green tatami room (37/102, top right): Carmine, Kieran and their grandfather
  two homes         a Lavaridge house (4/3): the old woman's, the old couple's (the user cut the town to what is
                    used, 2026-10-15: no festival hall, two homes instead of seven)
  the Pokemon Center Petalburg's (8/4), its nurse and her script the game's own (0x082079FC)

(The Dreaded Den, a cave of Seafloor Cavern's 24/35, went on 2026-10-16: the user, "the den is unneccesary".)

The Hall has its blues turned teal (the user: Kitakami Hall teal): copies of its two tilesets with the palettes
changed; no other map sees them.
"""
import colorsys, struct
import khall as KH

MAP_GROUPS = 0x00A54698
GENERAL = 0x083DF704                                   # the General tileset (the hall's first one)

# key: (source map, crop x0 y0 x1 y1 or None (the whole map), teal?, music or None (the source's), map type)
ROOMS = {
    "hall":     ((37, 102), (26, 10, 37, 25), True, None, 8),
    "family":   ((37, 102), (26, 0, 37, 6), False, None, 8),
    "pc":       ((8, 4), None, False, None, 8),
}
HOMES = 2
for k in range(HOMES):
    ROOMS["home%d" % (k + 1)] = ((4, 3), None, False, None, 8)

# the doors, as (x, y) in the room after cropping
MATS = {"hall": [(6, 14)], "family": [(5, 5), (6, 5)], "pc": [(6, 8), (7, 8)]}
for k in range(HOMES):
    MATS["home%d" % (k + 1)] = [(3, 7), (4, 7)]
NURSE = 0x082079FC                                     # Petalburg's nurse: setvar 0x800B 1, the game's nurse script


def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def header_of(rom, g, n):
    return u32(rom, u32(rom, MAP_GROUPS + 4 * g) - 0x08000000 + 4 * n) - 0x08000000


def blocks(rom, g, n, crop=None):
    lay = u32(rom, header_of(rom, g, n)) - 0x08000000
    w, h, d = u32(rom, lay), u32(rom, lay + 4), u32(rom, lay + 12) - 0x08000000
    b = [list(struct.unpack_from("<%dH" % w, rom, d + 2 * w * y)) for y in range(h)]
    if crop:
        x0, y0, x1, y1 = crop
        b = [row[x0:x1 + 1] for row in b[y0:y1 + 1]]
    return b


def music_of(rom, g, n):
    return struct.unpack_from("<H", rom, header_of(rom, g, n) + 16)[0]


def teal_hue(v):
    """a hotel colour as Kitakami Hall has it: its blues turned teal"""
    r, g, b = ((v & 31) / 31, (v >> 5 & 31) / 31, (v >> 10 & 31) / 31)
    h, s, val = colorsys.rgb_to_hsv(r, g, b)
    if s > 0.2 and 0.52 <= h <= 0.72:
        h = 0.47
    r, g, b = colorsys.hsv_to_rgb(h, s, val)
    return int(round(r * 31)) | int(round(g * 31)) << 5 | int(round(b * 31)) << 10


def teal_copy(rom, blob, addr):
    """blob key of a copy of the tileset at addr with its palettes' blues turned teal"""
    key = ("tileset", addr, "kitakami teal")
    if key in blob.addr:
        return key
    o = addr - 0x08000000
    ts = bytearray(rom[o:o + 24])
    pals = struct.unpack_from("<256H", rom, u32(rom, o + 8) - 0x08000000)
    pk = blob.put(("palettes", addr, "kitakami teal"), struct.pack("<256H", *[teal_hue(v) for v in pals]))
    struct.pack_into("<I", ts, 8, 0)
    p = blob.put(key, bytes(ts))
    blob.ref(("palettes", addr, "kitakami teal"), p - blob.base + 8)
    return key


def make(rom, blob, M, mapsec_town):
    """the rooms as paldea's maps.Map, keyed by name, their warps set (the outdoor side is wired by wire())"""
    out = {}
    for key, (src, crop, teal, music, mtype) in ROOMS.items():
        if key == "hall":                               # drawn for Kitakami: its own tileset (khall)
            built = KH.build()
            m = M.Map(key, src, KH.W, KH.H, built.blocks, border=built.border, music=music_of(rom, *src), weather=0,
                      mapsec=mapsec_town,
                      map_type=mtype, popup=False, tilesets=(GENERAL, KH.install(blob, built)))
            m.swaps = built.swaps                       # the cases smashed (kpeople: ON_LOAD from F_WAKE on)
            out[key] = m
            continue
        b = blocks(rom, *src, crop=crop)
        sets = None
        if teal:
            lay = u32(rom, header_of(rom, *src)) - 0x08000000
            sets = (teal_copy(rom, blob, u32(rom, lay + 16)), teal_copy(rom, blob, u32(rom, lay + 20)))
        m = M.Map(key, src, len(b[0]), len(b), b, music=music if music is not None else music_of(rom, *src),
                  weather=0, mapsec=mapsec_town, map_type=mtype, popup=False, tilesets=sets)
        out[key] = m
    return out


def wire(rooms, mossui, homes_doors, doors):
    """Every door both ways. doors: Mossui's door tiles by name; homes_doors: the homes' doors."""
    R = rooms
    # Mossui's warps, in this order (a warp names the other map's warp by its number)
    order = [("hall", doors["hall door"]), ("family", doors["family door"])] + \
            [("home%d" % (k + 1), d) for k, d in enumerate(homes_doors)] + [("pc", doors["center door"])]
    for i, (key, (x, y)) in enumerate(order):
        mossui.warp(x, y, key, 0)
        for (mx, my) in MATS[key]:
            R[key].warp(mx, my, "mossui", i)


def people(rooms, M):
    """milestone 2: the Pokemon Center's nurse only (the game's own nurse script)"""
    rooms["pc"].objs.append(M.Obj(1, 7, 2, None, gfx=58, face="down", elevation=3))
    rooms["pc"].objs[-1].script = NURSE
