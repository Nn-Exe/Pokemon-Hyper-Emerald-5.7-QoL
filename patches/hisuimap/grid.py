"""Per-square area maps for the region map's free cursor (patches/hisuimap).

The map screen used to know one square per place; to name whatever square a free-moving cursor is on, each region
needs a 30 x 20 grid of keys (map section in Sinnoh, map number in Hisui; 0xFF = nothing). It is worked out from the
region's own picture and place table:

* Sinnoh: every 8x8 square is classed by its colours - a town (the map's red), a road (its oranges), a lake (cyan
  inside the land) or nothing (land, mountain, sea). Each connected block of town squares goes to the town whose
  point is on it or nearest. Then every place's point spreads along road and lake squares, all at once, one square
  per step: a road square belongs to the place that reaches it first, i.e. the nearest along the road network, so a
  route owns the road between the towns at its ends.
* Hisui: no roads, only regions of one island - every land square goes to the nearest place (the temple keeps only
  its own square), the sea stays empty.

`python grid.py` draws both grids over their pictures (grid_sinnoh.png, grid_hisui.png) for checking.
"""
import json, os, struct
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 30, 20


def lz77(b):
    assert b[0] == 0x10
    n = int.from_bytes(b[1:4], "little")
    i, out = 4, bytearray()
    while len(out) < n:
        f = b[i]
        i += 1
        for k in range(8):
            if len(out) >= n:
                break
            if f & (0x80 >> k):
                x = (b[i] << 8) | b[i + 1]
                i += 2
                for _ in range((x >> 12) + 3):
                    out.append(out[-((x & 0xFFF) + 1)])
            else:
                out.append(b[i])
                i += 1
    return bytes(out)


def picture(prefix):
    """The region's picture as 240x160 RGB rows, from the same files the patch installs."""
    t = lz77(open(prefix + ".tiles.4bpp.lz", "rb").read())
    m = lz77(open(prefix + ".tilemap.bin.lz", "rb").read())
    p = open(prefix + ".palette.pal", "rb").read()
    pal = [struct.unpack_from("<H", p, 2 * i)[0] for i in range(len(p) // 2)]
    rgb = lambda c: ((c & 31) * 8, ((c >> 5) & 31) * 8, ((c >> 10) & 31) * 8)
    px = [[None] * 240 for _ in range(160)]
    for ty in range(H):
        for tx in range(W):
            e = struct.unpack_from("<H", m, 2 * (ty * 32 + tx))[0]
            ti, hf, vf, pn = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1, e >> 12
            for y in range(8):
                for x in range(8):
                    sx, sy = (7 - x if hf else x), (7 - y if vf else y)
                    v = t[ti * 32 + sy * 4 + sx // 2]
                    v = (v >> 4) if sx & 1 else v & 15
                    px[ty * 8 + y][tx * 8 + x] = rgb(pal[pn * 16 + v])
    return px


def cells(px, test):
    return [[sum(1 for y in range(8) for x in range(8) if test(px[cy * 8 + y][cx * 8 + x])) for cx in range(W)]
            for cy in range(H)]


TOWN = lambda c: c == (200, 88, 112)
ROAD = lambda c: c[0] == 248 and 150 <= c[1] <= 210 and c[2] <= 115
LAKE = lambda c: c in ((136, 224, 224), (88, 240, 208))
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def sinnoh_grid(places):
    """places: {mapsec: (x, y, name)} -> grid[y][x] = mapsec or 0xFF"""
    px = picture(os.path.join(HERE, "..", "sinnohmap", "sinnoh"))
    town, road, lake = cells(px, TOWN), cells(px, ROAD), cells(px, LAKE)
    grid = [[0xFF] * W for _ in range(H)]
    kind = [["" for _ in range(W)] for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if town[y][x] >= 12:
                kind[y][x] = "town"
            elif road[y][x] >= 16:
                kind[y][x] = "road"
            elif lake[y][x] >= 16:
                kind[y][x] = "lake"
    towns = {k: v for k, v in places.items() if any(w in v[2] for w in ("City", "Town", "League"))}
    seen = set()
    for y in range(H):                                   # each block of town squares -> the nearest town
        for x in range(W):
            if kind[y][x] != "town" or (x, y) in seen:
                continue
            comp, q = [], deque([(x, y)])
            seen.add((x, y))
            while q:
                a, b = q.popleft()
                comp.append((a, b))
                for dx, dy in N4:
                    n = (a + dx, b + dy)
                    if 0 <= n[0] < W and 0 <= n[1] < H and n not in seen and kind[n[1]][n[0]] == "town":
                        seen.add(n)
                        q.append(n)
            best = min(towns.items(), key=lambda kv: min(abs(kv[1][0] - a) + abs(kv[1][1] - b) for a, b in comp))
            if min(abs(best[1][0] - a) + abs(best[1][1] - b) for a, b in comp) <= 2:
                for a, b in comp:
                    grid[b][a] = best[0]
    q = deque()                                          # every place spreads along the roads at once
    for k, (x, y, _) in places.items():
        if grid[y][x] == 0xFF or k not in towns:
            if grid[y][x] == 0xFF:
                grid[y][x] = k
                q.append((x, y))
        if k in towns:                                   # towns spread from every square they own
            for b in range(H):
                for a in range(W):
                    if grid[b][a] == k:
                        q.append((a, b))
    while q:
        a, b = q.popleft()
        for dx, dy in N4:
            x, y = a + dx, b + dy
            if 0 <= x < W and 0 <= y < H and grid[y][x] == 0xFF and kind[y][x] in ("road", "lake"):
                grid[y][x] = grid[b][a]
                q.append((x, y))
    return grid, px


def hisui_grid(places, alone=(108,)):
    """places: {map number: (x, y, name)} -> grid; the sea (the picture's blues) stays empty"""
    px = picture(os.path.join(HERE, "hisui"))
    sea = cells(px, lambda c: c[2] > c[0] + 40 and c[2] > c[1] - 10)
    grid = [[0xFF] * W for _ in range(H)]
    spread = {k: v for k, v in places.items() if k not in alone}
    for y in range(H):
        for x in range(W):
            if sea[y][x] < 40:
                grid[y][x] = min(spread.items(), key=lambda kv: (kv[1][0] - x) ** 2 + (kv[1][1] - y) ** 2)[0]
    for k in alone:
        x, y, _ = places[k]
        grid[y][x] = k
    return grid, px


def pack(grid):
    return bytes(grid[y][x] for y in range(H) for x in range(W))


def sinnoh_places():
    loc = json.load(open(os.path.join(HERE, "..", "sinnohmap", "locations.json")))
    return {int(k): (v["x"], v["y"], v["name"]) for k, v in loc.items()}


if __name__ == "__main__":
    import colorsys, sys
    from PIL import Image, ImageDraw
    sys.path.insert(0, HERE)
    import hisuimap_patch as HP
    for name, (grid, px), places in (
            ("sinnoh",) + (sinnoh_grid(sinnoh_places()), sinnoh_places()),
            ("hisui",) + (hisui_grid({p[0]: (p[2], p[3], p[1]) for p in HP.PLACES}), {p[0]: (p[2], p[3], p[1]) for p in HP.PLACES})):
        im = Image.new("RGB", (240, 160))
        for y in range(160):
            for x in range(240):
                im.putpixel((x, y), px[y][x])
        im = im.resize((960, 640), Image.NEAREST)
        d = ImageDraw.Draw(im, "RGBA")
        keys = sorted(set(v for row in grid for v in row if v != 0xFF))
        for y in range(H):
            for x in range(W):
                k = grid[y][x]
                if k == 0xFF:
                    continue
                h = (keys.index(k) * 0.618) % 1
                r, g, b = colorsys.hsv_to_rgb(h, 0.8, 1.0)
                d.rectangle([x * 32, y * 32, x * 32 + 31, y * 32 + 31], fill=(int(r * 255), int(g * 255), int(b * 255), 110))
        for k, (x, y, n) in places.items():
            d.rectangle([x * 32 + 10, y * 32 + 10, x * 32 + 21, y * 32 + 21], outline=(0, 0, 0))
            d.text((x * 32 + 1, y * 32 + 1), str(k), fill=(0, 0, 0))
        im.save(sys.argv[1] + "_" + name + ".png" if len(sys.argv) > 1 else "grid_%s.png" % name)
        print(name, "%d squares named, %d places" % (sum(v != 0xFF for row in grid for v in row), len(keys)))
