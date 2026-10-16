"""mapinfo.py <rom> g.n [g.n ...]: a map's people (local id, position, script, hide flag), doors (position -> map)
and triggers (position, var == value, script), from the ROM's map headers (table 0x08A54698 + group)."""
import struct, sys, json, os
rom = open(sys.argv[1], "rb").read()
B = 0x08000000
u8 = lambda a: rom[a - B]
u16 = lambda a: struct.unpack_from("<H", rom, a - B)[0]
s16 = lambda a: struct.unpack_from("<h", rom, a - B)[0]
u32 = lambda a: struct.unpack_from("<I", rom, a - B)[0]
NAMES = {}
try:
    for m in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "romdata", "out", "maps.json"))):
        NAMES[(m["group"], m["num"])] = m["mapsec"]
except Exception:
    pass


def header(g, n):
    return u32(u32(0x08A54698 + 4 * g) + 4 * n)


def info(g, n):
    h = header(g, n)
    ev = u32(h + 4)
    no, nw, nc, nb = u8(ev), u8(ev + 1), u8(ev + 2), u8(ev + 3)
    po, pw, pc, pb = u32(ev + 4), u32(ev + 8), u32(ev + 12), u32(ev + 16)
    lay = u32(h)
    out = {"name": NAMES.get((g, n), "?"), "size": (u32(lay), u32(lay + 4)), "people": [], "doors": [], "triggers": [], "signs": []}
    for i in range(no):
        o = po + 24 * i
        out["people"].append(dict(local=u8(o), gfx=u8(o + 1), x=s16(o + 4), y=s16(o + 6), move=u8(o + 9),
                                  trainer=u8(o + 0xC), script="%08X" % u32(o + 0x10), flag="%04X" % u16(o + 0x14)))
    for i in range(nw):
        o = pw + 8 * i
        out["doors"].append(dict(x=s16(o), y=s16(o + 2), to="%d.%d" % (u8(o + 7), u8(o + 6)), warp=u8(o + 5)))
    for i in range(nc):
        o = pc + 16 * i
        out["triggers"].append(dict(x=s16(o), y=s16(o + 2), var="%04X" % u16(o + 6), value=u16(o + 8), script="%08X" % u32(o + 12)))
    for i in range(nb):
        o = pb + 12 * i
        out["signs"].append(dict(x=s16(o), y=s16(o + 2), kind=u8(o + 5), data="%08X" % u32(o + 8)))
    return out


if __name__ == "__main__":
    for a in sys.argv[2:]:
        g, n = map(int, a.split("."))
        m = info(g, n)
        print("== %d.%d %s %dx%d" % (g, n, m["name"], *m["size"]))
        for p in m["people"]:
            print("  person %(local)d at %(x)d,%(y)d gfx %(gfx)d trainer %(trainer)d script %(script)s hide %(flag)s" % p)
        for p in m["doors"]:
            print("  door at %(x)d,%(y)d -> %(to)s (warp %(warp)d)" % p)
        for p in m["triggers"]:
            print("  trigger at %(x)d,%(y)d if var %(var)s == %(value)d: %(script)s" % p)
        for p in m["signs"]:
            print("  sign at %(x)d,%(y)d kind %(kind)d data %(data)s" % p)
