"""New maps: layouts, events, map scripts, connections and headers, appended to a map group and to the layout
table. (Copied from an earlier patch of this project, which used it in play; connections are new here.)

The engine finds a map's layout through gMapLayouts[layoutId - 1] (0x08CFD124, read at 0x080849CC, 0x081AA17C
and 0x08F47728) and the map through gMapGroups[group][num] (0x08A54698). Both tables are followed by filler, so
they are copied into the blob with the new entries appended and their pointers repointed.
"""
import struct
from lib import Blob

MAP_GROUPS = 0x00A54698
LAYOUTS = 0x00CFD124
LAYOUT_COUNT = 845
LAYOUT_REFS = (0x000849CC, 0x001AA17C, 0x00F47728)

# a connection's direction (vanilla): which edge of the map the other map lies along
CONNECT = {"south": 1, "north": 2, "west": 3, "east": 4}
# object movement types (vanilla)
MT = {"none": 0x00, "look": 0x01, "up": 0x07, "down": 0x08, "left": 0x09, "right": 0x0A, "invisible": 0x4C}


class Obj:
    def __init__(self, local, x, y, script, gfx=0x4E, ext=0, face="down", flag=0, elevation=4, trainer=0, sight=0):
        self.__dict__.update(locals()); del self.__dict__["self"]


class Map:
    def __init__(self, key, source, w, h, blocks, border=None, music=None, weather=0, mapsec=None, map_type=None,
                 tilesets=None, cave=0, popup=False):
        self.key, self.source, self.w, self.h, self.blocks = key, source, w, h, blocks
        self.popup = popup                                  # show the place name on entry (header +0x1A bit 3)
        self.border = border
        self.tilesets = tilesets                            # (primary, secondary): blob keys, or None for the source's
        self.cave = cave                                    # 1: dark until lit (Flash / setflashlevel)
        self.music, self.weather, self.mapsec, self.map_type = music, weather, mapsec, map_type
        self.objs, self.warps, self.coords, self.bgs = [], [], [], []
        self.on_load = self.on_transition = self.on_resume = None   # script names
        self.on_frame = []                                  # (var, value, script name)
        self.connections = []                               # (side, offset, map key): see connect()
        self.group = self.num = None

    def connect(self, side, offset, dest_key):
        """Another map lies along this side ("north", "south", "west", "east"), its first column (north, south)
        or row (west, east) `offset` tiles from this map's. The game copies the 7 tiles of it nearest the edge
        (8 on the east) into what it keeps of this map past its edge, and draws them when you come near:
        FillNorthConnection and its three kin in the vanilla source. A strip at offset -7 along the north or
        south, 15 wider than this map, takes the corners too."""
        self.connections.append((side, offset, dest_key))

    def warp(self, x, y, dest_key, dest_warp, elevation=0):
        self.warps.append((x, y, elevation, dest_warp, dest_key))

    def coord(self, x, y, var, value, script, elevation=0):
        self.coords.append((x, y, elevation, var, value, script))

    def bg(self, x, y, script, elevation=0):
        self.bgs.append((x, y, elevation, script))


def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def group_count(rom, group):
    garr = u32(rom, MAP_GROUPS + 4 * group) - 0x08000000
    n = 0
    while 0x08000000 <= u32(rom, garr + 4 * n) < 0x0A000000:
        n += 1
    return garr, n


def numbers(rom, maps, groups):
    """(group, num) for each map: groups[key], numbers after the group's last. A warp stores the map number as a
    signed byte and 127 is MAP_DYNAMIC, so a group holds at most 127 maps (0-126)."""
    out, nxt = {}, {}
    for m in maps:
        g = groups[m.key]
        if g not in nxt:
            nxt[g] = group_count(rom, g)[1]
        out[m.key] = (g, nxt[g]); nxt[g] += 1
        assert out[m.key][1] < 127, "group %d is full (map %s would be %d)" % (g, m.key, out[m.key][1])
    return out


def install(rom, blob, maps, groups, known):
    """Lay the maps into blob and point the tables at them. `known` maps a map key to (group, num) for warps to
    existing maps; the new maps go to groups[key], numbers after the group's last."""
    for m, (key, gn) in zip(maps, numbers(rom, maps, groups).items()):
        m.group, m.num = gn
        known[m.key] = gn
    layout_ids = {}
    for k, m in enumerate(maps):
        src_hdr = u32(rom, u32(rom, MAP_GROUPS + 4 * m.source[0]) - 0x08000000 + 4 * m.source[1]) - 0x08000000
        src_lay = u32(rom, src_hdr) - 0x08000000
        data = blob.put(("mapdata", m.key), b"".join(struct.pack("<H", v) for row in m.blocks for v in row))
        border = m.border or [u32(rom, src_lay + 8)]      # a list of 4 blocks, or the source's border pointer
        if len(border) == 4:
            bptr = blob.put(("border", m.key), struct.pack("<4H", *border))
        else:
            bptr = border[0]
        lay = struct.pack("<iiIIII", m.w, m.h, bptr, data, u32(rom, src_lay + 16), u32(rom, src_lay + 20))
        lay += bytes(rom[src_lay + 24:src_lay + 28])
        layout_ids[m.key] = LAYOUT_COUNT + 1 + k
        pl = blob.put(("layout", m.key), lay)
        if m.tilesets:
            for i, key in enumerate(m.tilesets):
                blob.ref(key, pl - blob.base + 16 + 4 * i)
        # events
        ev = bytearray()
        objs = b""
        for o in m.objs:
            objs += struct.pack("<BBBBhhBBBBHHIHH", o.local, o.gfx, 0, o.ext, o.x, o.y, o.elevation, MT[o.face],
                                0, 0, o.trainer, o.sight, 0, o.flag, 0)
        pobjs = blob.put(("objs", m.key), objs) if objs else 0
        for i, o in enumerate(m.objs):
            if o.script:
                blob.ref(("script", o.script), pobjs - blob.base + 24 * i + 16)
        warps = b"".join(struct.pack("<hhBBBB", x, y, el, dw, *(known[dk][::-1]))
                         for x, y, el, dw, dk in m.warps)
        pwarps = blob.put(("warps", m.key), warps) if warps else 0
        coords = b"".join(struct.pack("<hhBBHHHI", x, y, el, 0, var, val, 0, 0) for x, y, el, var, val, s in m.coords)
        pcoords = blob.put(("coords", m.key), coords) if coords else 0
        for i, c in enumerate(m.coords):
            blob.ref(("script", c[5]), pcoords - blob.base + 16 * i + 12)
        bgs = b"".join(struct.pack("<hhBBHI", x, y, el, 0, 0, 0) for x, y, el, s in m.bgs)
        pbgs = blob.put(("bgs", m.key), bgs) if bgs else 0
        for i, b in enumerate(m.bgs):
            blob.ref(("script", b[3]), pbgs - blob.base + 12 * i + 8)
        blob.put(("events", m.key), struct.pack("<BBBBIIII", len(m.objs), len(m.warps), len(m.coords), len(m.bgs),
                                                pobjs, pwarps, pcoords, pbgs))
        # map scripts
        ms = []
        if m.on_frame:
            tab = b"".join(struct.pack("<HHI", var, val, 0) for var, val, s in m.on_frame) + b"\0\0"
            pt = blob.put(("frametab", m.key), tab)
            for i, (var, val, s) in enumerate(m.on_frame):
                blob.ref(("script", s), pt - blob.base + 8 * i + 4)
            ms.append((2, ("frametab", m.key)))
        if m.on_load:
            ms.append((1, ("script", m.on_load)))
        if m.on_transition:
            ms.append((3, ("script", m.on_transition)))
        if m.on_resume:
            ms.append((5, ("script", m.on_resume)))
        pms = 0
        if ms:
            pms = blob.put(("mapscripts", m.key), b"".join(struct.pack("<BI", t, 0) for t, _ in ms) + b"\0", 1)
            for i, (t, key) in enumerate(ms):
                blob.ref(key, pms - blob.base + 5 * i + 1)
        # connections: the list (12 bytes each: side, offset, group, number), then its count and pointer
        pcon = 0
        if m.connections:
            plist = blob.put(("connections", m.key), b"".join(
                struct.pack("<B3xiBB2x", CONNECT[side], offset, *known[dk]) for side, offset, dk in m.connections))
            pcon = blob.put(("connected", m.key), struct.pack("<iI", len(m.connections), plist))
        # header: the source's, with our layout, events, scripts, music, weather, and our connections or none
        hdr = bytearray(rom[src_hdr:src_hdr + 28])
        struct.pack_into("<IIII", hdr, 0, blob.addr[("layout", m.key)], blob.addr[("events", m.key)], pms, pcon)
        struct.pack_into("<H", hdr, 18, layout_ids[m.key])
        if m.music is not None:
            struct.pack_into("<H", hdr, 16, m.music)
        if m.mapsec is not None:
            hdr[20] = m.mapsec
        hdr[21] = m.cave
        hdr[22] = m.weather
        if m.map_type is not None:
            hdr[23] = m.map_type
        hdr[26] = 0x00                                    # no bike, no Escape Rope / Dig, no running shoes flag,
        hdr[26] |= 0x04                                   # ... running allowed; no map-name popup
        if m.popup:
            hdr[26] |= 0x08                               # ... unless asked for (Paldea)
        blob.put(("header", m.key), bytes(hdr))
    # the two tables, copied with the new entries
    old_layouts = bytes(rom[LAYOUTS:LAYOUTS + 4 * LAYOUT_COUNT])
    lt = blob.put(("table", "layouts"), old_layouts + bytes(4 * len(maps)))
    for k, m in enumerate(maps):
        blob.ref(("layout", m.key), lt - blob.base + 4 * (LAYOUT_COUNT + k))
    gas = {}
    for g in sorted(set(m.group for m in maps)):
        garr, n = group_count(rom, g)
        mine = [m for m in maps if m.group == g]
        ga = blob.put(("table", "group%d" % g), bytes(rom[garr:garr + 4 * n]) + bytes(4 * len(mine)))
        for m in mine:
            blob.ref(("header", m.key), ga - blob.base + 4 * m.num)
        gas[g] = ga
    return lt, gas


def repoint_tables(rom, lt, gas):
    for lit in LAYOUT_REFS:
        assert u32(rom, lit) == 0x08000000 + LAYOUTS, "layout table reference at %X moved" % lit
        struct.pack_into("<I", rom, lit, lt)
    for g, ga in gas.items():
        struct.pack_into("<I", rom, MAP_GROUPS + 4 * g, ga)
