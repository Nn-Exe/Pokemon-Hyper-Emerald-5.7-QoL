"""bfs.py <rom> g.n x0,y0 x1,y1: the walker's rules offline (collision, water, ledges, elevation, people) - path or
the reachable set's edge"""
import sys
from collections import deque
sys.argv, args = [sys.argv[0], sys.argv[1]], sys.argv[2:]
import mapinfo as MI
u16 = MI.u16; u32 = MI.u32
g, n = map(int, args[0].split(".")); sx, sy = map(int, args[1].split(",")); tx, ty = map(int, args[2].split(","))
h = MI.header(g, n); lay = u32(h); w, ht, mp = u32(lay), u32(lay + 4), u32(lay + 12); prim, sec = u32(lay + 16), u32(lay + 20)
def blk(x, y): return u16(mp + 2 * (y * w + x))
def beh(b):
    mt = b & 0x3FF; ts = prim if mt < 512 else sec
    return u16(u32(ts + 16) + 2 * (mt if mt < 512 else mt - 512)) & 0xFF
ppl = {(p['x'], p['y']) for p in MI.info(g, n)['people']}
WATER = {0x10, 0x11, 0x12, 0x14, 0x15, 0x17, 0x19, 0x1A}
start = (sx, sy); z0 = (blk(sx, sy) >> 12) & 15
q = deque([(start, z0)]); prev = {start: None}
while q:
    (x, y), ce = q.popleft()
    if (x, y) == (tx, ty): break
    for dx, dy, led in ((1, 0, 0x38), (-1, 0, 0x39), (0, -1, 0x3A), (0, 1, 0x3B)):
        nx, ny = x + dx, y + dy
        if not (0 <= nx < w and 0 <= ny < ht) or (nx, ny) in prev: continue
        b = blk(nx, ny); bh = beh(b)
        if 0x38 <= bh <= 0x3B:
            if bh == led:
                jx, jy = nx + dx, ny + dy
                if 0 <= jx < w and 0 <= jy < ht and not (blk(jx, jy) >> 10) & 3 and (jx, jy) not in prev:
                    prev[(jx, jy)] = (x, y); q.append(((jx, jy), ce))
            continue
        if (nx, ny) != (tx, ty) and ((b >> 10) & 3 or (nx, ny) in ppl or bh in WATER or 0x60 <= bh <= 0x6F): continue
        te = (b >> 12) & 15
        if (nx, ny) != (tx, ty) and not (ce in (0, 15) or te in (0, 15) or ce == te): continue
        prev[(nx, ny)] = (x, y); q.append(((nx, ny), ce if te == 15 else te))
if (tx, ty) in prev:
    p = []; c = (tx, ty)
    while c: p.append(c); c = prev[c]
    print("path of", len(p) - 1, "steps:", p[::-1][:40])
else:
    print("NO PATH; reachable:", len(prev), "tiles; min y reached:", min(y for x, y in prev))
    print("z grid:")
    for y in range(ht):
        print("%3d %s" % (y, "".join("%X" % ((blk(x, y) >> 12) & 15) for x in range(w))))
