"""The wild test's cases, read from the ROM: for every new Pokemon in the wild tables, its map, kind, slot, rod,
levels, and up to four tiles of that map to stand on (land: grass / cave floor kinds; water: water kinds), each a
different behaviour, nearest the map's centre first. python -I wildplan.py <rom.gba> <cases.txt>"""
import struct, sys
rom = open(sys.argv[1], "rb").read()
u8 = lambda o: rom[o]
u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
o8 = lambda v: v - 0x08000000
WILD, GROUPS = 0x00E17D50, 0x00A54698
LAND_B = [0x02, 0x03, 0x24, 0x08, 0x0B, 0x06, 0x0C, 0x09]
WATER_B = [0x10, 0x15, 0x12, 0x11, 0x14, 0x19, 0x13]
names = o8(u32(0x144))
CH = {0xA1 + i: c for i, c in enumerate("0123456789!?.-・…“”‘’♂♀¥,×/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")}
nm = lambda s: "".join(CH.get(b, "?") for b in rom[names + 11 * s:names + 11 * s + 11].split(b"\xff")[0])
KINDS = {"land": (4, 12), "water": (8, 5), "rock": (12, 5), "fish": (16, 10)}


def tiles(g, n, want):
    h = o8(u32(o8(u32(GROUPS + 4 * g)) + 4 * n))
    lay = o8(u32(h))
    w, ht, mp = u32(lay), u32(lay + 4), o8(u32(lay + 12))
    prim, sec = o8(u32(lay + 16)), o8(u32(lay + 20))
    pa, sa = o8(u32(prim + 0x10)), o8(u32(sec + 0x10))
    found = {}
    cx, cy = w // 2, ht // 2
    cells = sorted(((x, y) for y in range(ht) for x in range(w)), key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
    for x, y in cells:
        blk = u16(mp + 2 * (y * w + x))
        mt, coll = blk & 0x3FF, (blk >> 10) & 3
        if coll:
            continue
        attr = u16(pa + 2 * mt) if mt < 512 else u16(sa + 2 * (mt - 512))
        b = attr & 0xFF
        if b in want and b not in found:
            found[b] = (x, y)
    return [(b, found[b]) for b in want if b in found]


sys.path.insert(0, r"C:\Users\nonth\Desktop\Works & Productivity\gba-trans\hyper-emerald\hyper-emerald-en-qol\patches\gen9rest")
import gen9rest_data as D
slot_of = {k: D.FIRST_SLOT + i for i, (k, *_r) in enumerate(D.SPECIES)}
lines, seen = [], set()
for key, h, kind, _rate, was in D.WILD:
    o = WILD + 20 * h
    g, n = rom[o], rom[o + 1]
    at, count = KINDS[kind]
    arr = o8(u32(o8(u32(o + at)) + 4))
    sp = slot_of[key]
    slots = [j for j in range(count) if u16(arr + 4 * j + 2) == sp]
    assert len(slots) == 1, (key, h, kind, slots)
    j = slots[0]
    lo, hi = rom[arr + 4 * j], rom[arr + 4 * j + 1]
    rod = (0 if j < 2 else 1 if j < 5 else 2) if kind == "fish" else -1
    cand = tiles(g, n, LAND_B if kind == "land" else WATER_B) if kind != "fish" else [(0, (5, 5))]
    tl = ";".join("%d,%d,%02X" % (x, y, b) for b, (x, y) in cand[:4]) or "NONE"
    lines.append("%s|%s|%d|%d|%d|%s|%d|%d|%d|%d|%d|%s" % (key, nm(sp), sp, g, n, kind, j, rod, lo, hi, h, tl))
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
