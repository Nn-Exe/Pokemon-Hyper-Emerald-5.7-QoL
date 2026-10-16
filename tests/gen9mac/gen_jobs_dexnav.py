"""Jobs for test_dexnavall.lua: the DexNav search for every new wild Pokemon where it lives.

    python gen_jobs_dexnav.py <build.gba> <save> <jobs.json>

gen9rest's 45 placements (patches/gen9rest/wild_results.txt: land and water on the tile the wild test met each
one, fishing ones hunted from the nearest open water - a fishing Pokemon is hunted from the water), and each
different Pokemon of Area Zero's three wild tables (35/90, 35/91, 35/95). Use the "(DexNav open)" build: it
registers unseen Pokemon (the only difference from the build itself)."""
import json, re, struct, sys, os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__)) + "/"
G9 = REPO + "/patches/gen9rest/"
ROM, SAV, OUTJ = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3]
rom = open(ROM, "rb").read()
u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
WILD = 0x00E17D50
LAND_B = [0x02, 0x03, 0x24, 0x08, 0x0B, 0x06, 0x0C, 0x09]
WATER_B = [0x10, 0x12, 0x15]                     # pond, deep and ocean water: surfable, with wild Pokemon


def layout(g, n):
    h = u32(u32(0xA54698 + 4 * g) - 0x08000000 + 4 * n) - 0x08000000
    lay = u32(h) - 0x08000000
    w, ht, mp = u32(lay), u32(lay + 4), u32(lay + 12) - 0x08000000
    pa, sa = u32(u32(lay + 16) - 0x08000000 + 0x10) - 0x08000000, u32(u32(lay + 20) - 0x08000000 + 0x10) - 0x08000000
    def beh(x, y):
        if not (0 <= x < w and 0 <= y < ht):
            return None, 1
        blk = u16(mp + 2 * (y * w + x))
        mt = blk & 0x3FF
        attr = u16(pa + 2 * mt if mt < 512 else sa + 2 * (mt - 512))
        return attr & 0xFF, (blk >> 10) & 3
    return w, ht, beh


def tile(g, n, kinds, near=None, open_=False):
    w, ht, beh = layout(g, n)
    cx, cy = near if near else (w // 2, ht // 2)
    for x, y in sorted(((x, y) for y in range(ht) for x in range(w)), key=lambda p: abs(p[0] - cx) + abs(p[1] - cy)):
        b, col = beh(x, y)
        if col or b not in kinds:
            continue
        if open_ and not all(beh(x + dx, y + dy)[0] in kinds and not beh(x + dx, y + dy)[1]
                             for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)):
            continue
        return x, y


# a start of our own where the wild test's tile leaves the patch out of reach: in Mirage Tower (24/97) the patch
# came up in the corridor above, whose only way in is a 0x60 tile the player cannot walk onto
START = {(24, 97): (7, 1)}
jobs = []
def job(name, g, n, x, y, sp, kind):
    jobs.append({"name": name, "rom": ROM, "sav": SAV, "lua": HERE + "test_dexnavall.lua",
                 "env": {"G": g, "N": n, "X": x, "Y": y, "SP": sp, "KIND": kind, "TAG": name}, "timeout": 900})

for line in open(G9 + "wild_results.txt", encoding="utf-8-sig"):
    m = re.match(r"(\S+)\s+.*?table\s+(\d+)\s+(\w+)\s+slot\s+(\d+): MET species (\d+) lv \d+ \(want \d+ lv (\d+)-(\d+)\).*\[tile (\d+),(\d+)", line)
    if not m:
        continue
    key, h, kind, j, sp, lo, hi, x, y = m.groups()
    h, x, y = int(h), int(x), int(y)
    g, n = rom[WILD + 20 * h], rom[WILD + 20 * h + 1]
    if (g, n) in START:
        x, y = START[(g, n)]
    if kind == "fish":
        x, y = tile(g, n, WATER_B, near=(x, y), open_=True) or tile(g, n, WATER_B, near=(x, y))
    job("dn_%s_%d_%d" % (key, g, n), g, n, x, y, int(sp), kind)

i = 0
while rom[WILD + 20 * i] != 0xFF:                # Area Zero
    o = WILD + 20 * i
    g, n = rom[o], rom[o + 1]
    if g == 35 and n in (90, 91, 95) and u32(o + 4):
        arr = u32(u32(o + 4) - 0x08000000 + 4) - 0x08000000
        x, y = tile(g, n, LAND_B)
        for sp in sorted({u16(arr + 4 * j + 2) for j in range(12)}):
            job("dn_az_%d_%d_%d" % (g, n, sp), g, n, x, y, sp, "land")
    i += 1
json.dump(jobs, open(OUTJ, "w"), indent=1)
print(len(jobs), "jobs")
