"""mapgrid.py <rom> g.n: the whole map as text - # wall, ~ water, D door, > < ^ v ledges (the way they jump),
. walkable, digits = people (local id mod 10), with each row's number; elevation as a second grid with -z."""
import struct, sys
sys.path.insert(0, '.')
import mapinfo as MI
rom = MI.rom
B = 0x08000000
u16 = MI.u16; u32 = MI.u32
g, n = map(int, sys.argv[2].split("."))
h = MI.header(g, n)
lay = u32(h)
w, ht, mp = u32(lay), u32(lay + 4), u32(lay + 12)
prim, sec = u32(lay + 16), u32(lay + 20)
def beh(mt):
    ts = prim if mt < 512 else sec
    return u16(u32(ts + 16) + 2 * (mt if mt < 512 else mt - 512)) & 0xFF
info = MI.info(g, n)
ppl = {(p["x"], p["y"]): p["local"] for p in info["people"]}
doors = {(p["x"], p["y"]) for p in info["doors"]}
LED = {0x38: ">", 0x39: "<", 0x3A: "^", 0x3B: "v"}
WATER = {0x10, 0x11, 0x12, 0x14, 0x15, 0x17, 0x19, 0x1A}
print("== %d.%d %s %dx%d" % (g, n, info["name"], w, ht))
print("     " + "".join(str(x // 10 % 10) for x in range(w)))
print("     " + "".join(str(x % 10) for x in range(w)))
for y in range(ht):
    row = []
    for x in range(w):
        b = u16(mp + 2 * (y * w + x)); bh = beh(b & 0x3FF)
        c = "."
        if (b >> 10) & 3: c = "#"
        if bh in LED: c = LED[bh]
        if bh in WATER: c = "~"
        if bh in (0x02, 0x03) and c == ".": c = ","
        if (x, y) in doors: c = "D"
        if (x, y) in ppl: c = str(ppl[(x, y)] % 10)
        row.append(c)
    print("%4d %s" % (y, "".join(row)))
if "-z" in sys.argv:
    for y in range(ht):
        print("z%3d %s" % (y, "".join("%X" % ((u16(mp + 2 * (y * w + x)) >> 12) & 0xF) for x in range(w))))
