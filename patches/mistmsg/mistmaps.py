"""mistmaps.py <rom> - every map whose header weather is one of the given kinds, with where to land on it.
Prints a table and writes mistmaps.txt (in the current folder; test_mistmaps.lua reads it as LISTFILE): "group num x y weather name" per map (x, y: the first warp's tile, or the
middle of the map when it has none)."""
import json, os, struct, sys

rom = open(sys.argv[1], "rb").read()
WANT = {int(w) for w in (sys.argv[2] if len(sys.argv) > 2 else "6,9,10,14").split(",")}
u8 = lambda a: rom[a - 0x08000000]
u16 = lambda a: struct.unpack_from("<H", rom, a - 0x08000000)[0]
u32 = lambda a: struct.unpack_from("<I", rom, a - 0x08000000)[0]
ok = lambda v: 0x08000000 <= v < 0x0A000000

# gMapGroups from Overworld_GetMapHeaderByGroupAndId's literal (0x08084A90: ldr r2, =gMapGroups)
fn = 0x08084A90
groups = None
for a in range(fn, fn + 0x18, 2):
    op = u16(a)
    if op & 0xF800 == 0x4800:
        v = u32(((a + 4) & ~3) + (op & 0xFF) * 4)
        if ok(v):
            groups = v
            break
names = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools", "romdata", "map_names.json")))["groups"]
gptrs = []
k = 0
while ok(u32(groups + 4 * k)) and k < 80:
    gptrs.append(u32(groups + 4 * k))
    k += 1
print("gMapGroups %08X, %d groups" % (groups, len(gptrs)))
out = []
total = 0
for g, gp in enumerate(gptrs):
    nxt = sorted(p for p in gptrs + [groups] if p > gp)
    limit = (nxt[0] - gp) // 4 if nxt else 400
    for m in range(min(limit, 400)):
        h = u32(gp + 4 * m)
        if not ok(h) or not ok(u32(h)) or not ok(u32(h + 4)):
            break
        total += 1
        weather, cave, mtype = u8(h + 0x16), u8(h + 0x15), u8(h + 0x17)
        if weather not in WANT:
            continue
        layout, events = u32(h), u32(h + 4)
        w, hgt = u32(layout), u32(layout + 4)
        nwarps = u8(events + 1)
        warps = u32(events + 8)
        if nwarps and ok(warps):
            x, y = u16(warps), u16(warps + 2)
        else:
            x, y = w // 2, hgt // 2
        nm = names[g][m] if g < len(names) and m < len(names[g]) else "(hack's own %d/%d)" % (g, m)
        out.append((g, m, x, y, weather, nm, cave, mtype, nwarps))
print("%d maps in all; with weather %s: %d" % (total, sorted(WANT), len(out)))
for g, m, x, y, wt, nm, cave, mtype, nw in out:
    print("  %2d/%-3d weather %2d  cave %d  type %d  warps %2d  land (%d, %d)  %s" % (g, m, wt, cave, mtype, nw, x, y, nm))
open("mistmaps.txt", "w").write("".join("%d %d %d %d %d %s\n" % (g, m, x, y, wt, nm.replace(" ", "_")) for g, m, x, y, wt, nm, *_ in out))
