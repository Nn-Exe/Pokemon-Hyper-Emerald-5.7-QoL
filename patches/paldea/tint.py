"""(Copied from an earlier patch of this project.) Tinted copies of the game's own tilesets, for Area Zero's places: the same tiles and metatiles, a new
palette. A tileset (24 bytes: compressed, secondary, pad, tiles, palettes, metatiles, attributes, callback) is copied
into the blob with its palettes pointer moved to a recoloured copy of its 16 palettes (0x200 bytes)."""
import struct

TINTS = {
    # (weights for luminance -> r, g, b), plus added, and how much of the tint replaces the colour
    # Area Zero (Paldea)
    "past":   ((1.10, 1.00, 0.55), (2, 1, 0), 0.55),    # the crater in the past: dry olive and gold
    "future": ((0.62, 0.55, 1.15), (1, 0, 3), 0.80),    # the crater in the future: cold violet
    "zero":   ((0.85, 1.00, 0.95), (0, 1, 1), 0.45),    # the wall between them: sand turned grey-green
    "crystal": ((0.78, 0.70, 1.15), (1, 1, 3), 0.62),   # the Crystal Cavern: rock lit violet by the crystals
    "ice":    ((0.80, 0.96, 1.18), (3, 4, 6), 0.78),    # the icy cave: frost on everything
    "tera":   ((0.62, 0.98, 1.22), (2, 4, 6), 0.86),    # the Underdepths: a chamber lit by a pool of crystal light
}


def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def recolour(v, tint):
    (wr, wg, wb), (ar, ag, ab), mix = TINTS[tint]
    r, g, b = v & 31, v >> 5 & 31, v >> 10 & 31
    lum = 0.30 * r + 0.59 * g + 0.11 * b
    out = []
    for c, w, a in ((r, wr, ar), (g, wg, ag), (b, wb, ab)):
        t = lum * w + a
        out.append(max(0, min(31, int(round(c * (1 - mix) + t * mix)))))
    return out[0] | out[1] << 5 | out[2] << 10


LAVA = [(40, 0, 0), (120, 16, 0), (200, 48, 0), (240, 104, 8), (255, 168, 24), (255, 224, 96), (255, 248, 184)]
LAVA_PAL = {"ember": 4}     # the general tileset's water palette: the Fallen Star's sea is lava


def lava(v):
    r, g, b = v & 31, v >> 5 & 31, v >> 10 & 31
    t = (0.30 * r + 0.59 * g + 0.11 * b) / 31 * (len(LAVA) - 1)
    i = min(int(t), len(LAVA) - 2); f = t - i
    c = [min(31, int(round((LAVA[i][k] * (1 - f) + LAVA[i + 1][k] * f) / 8))) for k in range(3)]
    return c[0] | c[1] << 5 | c[2] << 10


LAYER = 0xF000                 # a metatile attribute's layer type: 0 its second layer is drawn over people (the
COVERED = 0x1000               # map's top layer), 1 both its layers are under them ("covered")
HALF = 512                     # metatiles a tileset can have: the primary's are 0-511, the secondary's 512-1023


def layer(rom, layout, mid):
    """The layer type of metatile mid in the layout at ROM offset `layout`."""
    ts = u32(rom, layout + (16 if mid < HALF else 20)) - 0x08000000
    return struct.unpack_from("<H", rom, u32(rom, ts + 16) - 0x08000000 + 2 * (mid % HALF))[0] >> 12


def tileset(rom, blob, addr, tint, covered=()):
    """Blob key of a copy of the tileset at addr: tinted (None: its own colours), and with the metatiles in
    `covered` (numbers within this tileset) drawn wholly under people. One copy per tileset, tint and set."""
    covered = tuple(sorted(covered))
    key = ("tileset", addr, tint) + ((covered,) if covered else ())
    if key in blob.addr:
        return key
    o = addr - 0x08000000
    ts = bytearray(rom[o:o + 24])
    pk = ak = None
    if tint is not None:
        po = u32(rom, o + 8) - 0x08000000
        pals = struct.unpack_from("<256H", rom, po)
        pk = ("palettes", addr, tint)
        if pk not in blob.addr:
            new = [recolour(v, tint) for v in pals]
            if tint in LAVA_PAL and not rom[o + 1]:          # the primary tileset: its water palette becomes lava
                k = LAVA_PAL[tint]
                new[16 * k:16 * k + 16] = [lava(v) for v in pals[16 * k:16 * k + 16]]
            blob.put(pk, struct.pack("<256H", *new))
        struct.pack_into("<I", ts, 8, 0)
    if covered:
        # the whole attribute table is copied (a word a metatile; nothing says how many a tileset has, so room
        # for all 512: what lies past the last real one is never looked up)
        ao = u32(rom, o + 16) - 0x08000000
        ak = ("attributes", addr, covered)
        if ak not in blob.addr:
            attrs = list(struct.unpack_from("<%dH" % HALF, rom, ao))
            for k in covered:
                attrs[k] = attrs[k] & ~LAYER | COVERED
            blob.put(ak, struct.pack("<%dH" % HALF, *attrs))
        struct.pack_into("<I", ts, 16, 0)
    p = blob.put(key, bytes(ts))
    if pk:
        blob.ref(pk, p - blob.base + 8)
    if ak:
        blob.ref(ak, p - blob.base + 16)
    return key


def custom_secondary(blob, data, custom, tint, covered=()):
    """Blob key of the craters' own secondary tileset (tiles.py: Petalburg's with the tiles taken from other maps
    in it): its picture cells and metatiles go to `data` once (another blob, with room; both times share them),
    its attributes there once per `covered` (metatile numbers within the tileset, drawn under people), its
    palettes, tinted, and the 24-byte tileset itself to `blob`, where the maps' layouts point at it."""
    covered = tuple(sorted(covered))
    key = ("tileset", "custom", tint, covered)
    if key in blob.addr:
        return key
    tiles = data.addr.get(("custom", "tiles")) or data.put(("custom", "tiles"), custom.tiles, 4)
    metas = data.addr.get(("custom", "metatiles")) or data.put(("custom", "metatiles"), custom.metatiles, 4)
    ak = ("custom", "attributes", covered)
    if ak not in data.addr:
        attrs = list(custom.attrs)
        for k in covered:
            attrs[k] = attrs[k] & ~LAYER | COVERED
        data.put(ak, struct.pack("<%dH" % HALF, *attrs), 4)
    pk = ("palettes", "custom", tint)
    if pk not in blob.addr:
        blob.put(pk, struct.pack("<256H", *[v if tint is None else recolour(v, tint) for v in custom.pals]))
    p = blob.put(key, struct.pack("<BBHIIIII", 1, 1, 0, tiles, 0, metas, data.addr[ak], 0))
    blob.ref(pk, p - blob.base + 8)
    return key


def tilesets(rom, blob, source, tint, covered=()):
    """(primary, secondary) keys for a map copied from source (group, num). covered: metatile numbers as the map
    uses them (0-1023) that are to be drawn under people."""
    import maps as M
    hdr = u32(rom, u32(rom, M.MAP_GROUPS + 4 * source[0]) - 0x08000000 + 4 * source[1]) - 0x08000000
    lay = u32(rom, hdr) - 0x08000000
    return tuple(tileset(rom, blob, u32(rom, lay + 16 + 4 * i), tint,
                         [m % HALF for m in covered if m // HALF == i]) for i in range(2))
