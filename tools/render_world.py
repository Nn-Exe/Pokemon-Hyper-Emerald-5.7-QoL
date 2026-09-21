"""Render a whole region of Hyper Emerald as one image, straight from the ROM's map data.

Walks the map-connection graph from a seed map, places every connected outdoor map on a common grid,
then draws each one metatile by metatile (tileset tiles + palettes + metatile definitions).

usage: python render_world.py <group> <num> <out.png> [--maxpx N] [--grid]
"""
import os, struct, sys
import numpy as np
from PIL import Image, ImageDraw

ROM = os.environ.get("HE_ROM") or "C:/Users/nonth/Desktop/Works & Productivity/gba-trans/roms/current/Pokemon Hyper Emerald v5.7 - Full English Modern.gba"
rom = open(ROM, "rb").read()
MASTER = 0xA54698                 # gMapGroups
NUM_TILES_IN_PRIMARY = 512
NUM_METATILES_IN_PRIMARY = 512
NUM_PALS_IN_PRIMARY = 6


def u8(o): return rom[o]
def u16(o): return struct.unpack_from("<H", rom, o)[0]
def u32(o): return struct.unpack_from("<I", rom, o)[0]
def s32(o): return struct.unpack_from("<i", rom, o)[0]
def ptr(o):
    v = u32(o)
    return v - 0x08000000 if 0x08000000 <= v < 0x08000000 + len(rom) else None


RAW_TILES = 512 * 32          # a tileset half never needs more than this


def lz77(off):
    """GBA LZ77 (header byte 0x10). A few of this hack's tilesets are stored raw with the
    compressed flag still set, so anything without the header is read as raw tile data."""
    if rom[off] != 0x10:
        return rom[off:off + RAW_TILES]
    size = u32(off) >> 8
    out = bytearray()
    p = off + 4
    while len(out) < size:
        flags = rom[p]; p += 1
        for bit in range(8):
            if len(out) >= size: break
            if flags & (0x80 >> bit):
                b1, b2 = rom[p], rom[p + 1]; p += 2
                n = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                start = len(out) - disp
                if start < 0: return bytes(out) + bytes(size - len(out))
                for k in range(n): out.append(out[start + k])
            else:
                out.append(rom[p]); p += 1
    return bytes(out[:size])


def tileset(tp):
    """(tiles bytes, palettes as 16x16 RGB array, metatiles offset, is_secondary); never raises."""
    try:
        return _tileset(tp)
    except Exception as e:
        print("   tileset %08X unreadable (%s), drawn blank" % (0x08000000 + tp, e))
        return b"", np.zeros((16, 16, 3), np.uint8), None, 0


def _tileset(tp):
    comp, sec = u8(tp), u8(tp + 1)
    tiles_o, pal_o, meta_o = ptr(tp + 4), ptr(tp + 8), ptr(tp + 12)
    tiles = lz77(tiles_o) if comp else rom[tiles_o:tiles_o + 0x8000]
    pal = np.zeros((16, 16, 3), np.uint8)
    for p in range(16):
        for c in range(16):
            v = u16(pal_o + (p * 16 + c) * 2)
            pal[p, c] = ((v & 31) << 3 | (v & 31) >> 2, (v >> 5 & 31) << 3 | (v >> 5 & 31) >> 2,
                         (v >> 10 & 31) << 3 | (v >> 10 & 31) >> 2)
    return tiles, pal, meta_o, sec


def tile_pixels(tiles, idx):
    """8x8 array of palette indices for tile idx (4bpp, 32 bytes each)."""
    o = idx * 32
    if o + 32 > len(tiles): return np.zeros((8, 8), np.uint8)
    b = np.frombuffer(tiles, np.uint8, 32, o)
    px = np.empty((8, 8), np.uint8)
    px[:, 0::2] = (b & 0xF).reshape(8, 4)
    px[:, 1::2] = (b >> 4).reshape(8, 4)
    return px


class Layout:
    """One map layout: its size, tile data and the pair of tilesets, with a metatile image cache."""
    cache = {}

    def __init__(self, lay):
        self.w, self.h = u32(lay), u32(lay + 4)
        self.data = ptr(lay + 12)
        self.prim_o, self.sec_o = ptr(lay + 16), ptr(lay + 20)
        key = (self.prim_o, self.sec_o)
        if key not in Layout.cache:
            Layout.cache[key] = self._build()
        self.meta_img = Layout.cache[key]

    def _build(self):
        prim = tileset(self.prim_o) if self.prim_o else None
        sec = tileset(self.sec_o) if self.sec_o else None
        pal = np.zeros((16, 16, 3), np.uint8)
        if prim is not None: pal[:NUM_PALS_IN_PRIMARY] = prim[1][:NUM_PALS_IN_PRIMARY]
        if sec is not None: pal[NUM_PALS_IN_PRIMARY:13] = sec[1][NUM_PALS_IN_PRIMARY:13]
        return {"prim": prim, "sec": sec, "pal": pal, "img": {}}

    def metatile(self, mid):
        """16x16 RGB image of metatile mid (cached per tileset pair)."""
        c = self.meta_img
        if mid in c["img"]: return c["img"][mid]
        prim, sec, pal = c["prim"], c["sec"], c["pal"]
        if mid < NUM_METATILES_IN_PRIMARY:
            ts, meta_o, base = prim, prim[2] if prim else None, 0
        else:
            ts, meta_o, base = sec, sec[2] if sec else None, NUM_METATILES_IN_PRIMARY
        out = np.zeros((16, 16, 3), np.uint8)
        if meta_o is None:
            c["img"][mid] = out; return out
        out[:, :] = pal[0, 0]
        e = meta_o + (mid - base) * 16
        for layer in range(2):                      # bottom, then top over it
            for q in range(4):
                v = u16(e + (layer * 4 + q) * 2)
                tid, xf, yf, p = v & 0x3FF, v >> 10 & 1, v >> 11 & 1, v >> 12 & 0xF
                src = prim if tid < NUM_TILES_IN_PRIMARY else sec
                if src is None: continue
                px = tile_pixels(src[0], tid if tid < NUM_TILES_IN_PRIMARY else tid - NUM_TILES_IN_PRIMARY)
                if xf: px = px[:, ::-1]
                if yf: px = px[::-1, :]
                y0, x0 = (q // 2) * 8, (q % 2) * 8
                mask = px != 0                      # colour 0 is transparent on both layers
                out[y0:y0 + 8, x0:x0 + 8][mask] = pal[p][px[mask]]
        c["img"][mid] = out
        return out

    def render(self):
        img = np.zeros((self.h * 16, self.w * 16, 3), np.uint8)
        for y in range(self.h):
            row = self.data + y * self.w * 2
            for x in range(self.w):
                mid = u16(row + x * 2) & 0x3FF
                img[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = self.metatile(mid)
        return img


def header(g, n):
    gp = ptr(MASTER + 4 * g)
    return ptr(gp + 4 * n) if gp is not None else None


def connections(h):
    cp = ptr(h + 12)
    if cp is None: return []
    cnt = u32(cp); cl = ptr(cp + 4)
    if cl is None or not (0 < cnt < 64): return []
    return [(u8(cl + i * 12), s32(cl + i * 12 + 4), u8(cl + i * 12 + 8), u8(cl + i * 12 + 9)) for i in range(cnt)]


def walk(seed, limit=400):
    """BFS over map connections. Returns {(g,n): (x, y, Layout)} in metatile units."""
    placed, queue = {}, [(seed, 0, 0)]
    while queue and len(placed) < limit:
        (g, n), x, y = queue.pop(0)
        if (g, n) in placed: continue
        h = header(g, n)
        if h is None: continue
        lay = ptr(h)
        if lay is None: continue
        L = Layout(lay)
        if not (1 <= L.w <= 500 and 1 <= L.h <= 500): continue
        placed[(g, n)] = (x, y, L)
        for d, off, cg, cn in connections(h):
            if (cg, cn) in placed or d not in (1, 2, 3, 4): continue
            ch = header(cg, cn)
            if ch is None: continue
            cl = ptr(ch)
            if cl is None: continue
            cw, chh = u32(cl), u32(cl + 4)
            if d == 1:   nx, ny = x + off, y + L.h          # south
            elif d == 2: nx, ny = x + off, y - chh          # north
            elif d == 3: nx, ny = x - cw, y + off           # west
            else:        nx, ny = x + L.w, y + off          # east
            queue.append(((cg, cn), nx, ny))
    return placed


def main():
    g, n, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    maxpx = int(sys.argv[sys.argv.index("--maxpx") + 1]) if "--maxpx" in sys.argv else 0
    placed = walk((g, n))
    xs = [x for x, y, L in placed.values()]; ys = [y for x, y, L in placed.values()]
    x0, y0 = min(xs), min(ys)
    W = max(x + L.w for x, y, L in placed.values()) - x0
    H = max(y + L.h for x, y, L in placed.values()) - y0
    print("%d maps placed, world %d x %d metatiles (%d x %d px)" % (len(placed), W, H, W * 16, H * 16))
    groups = sorted({k[0] for k in placed})
    print("map groups reached:", groups)
    canvas = np.zeros((H * 16, W * 16, 3), np.uint8)
    for i, ((mg, mn), (x, y, L)) in enumerate(sorted(placed.items())):
        img = L.render()
        py, px = (y - y0) * 16, (x - x0) * 16
        canvas[py:py + img.shape[0], px:px + img.shape[1]] = img
        if i % 20 == 0: print("  %d/%d rendered" % (i, len(placed)), flush=True)
    im = Image.fromarray(canvas)
    im.save(out)
    print("wrote %s (%d x %d)" % (out, im.width, im.height))
    if maxpx and max(im.size) > maxpx:
        s = maxpx / max(im.size)
        small = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        p = out.replace(".png", "-preview.png")
        small.save(p)
        print("wrote %s (%d x %d)" % (p, small.width, small.height))
    # where each map landed, for labelling later
    with open(out.replace(".png", "-maps.txt"), "w", encoding="utf-8") as f:
        for (mg, mn), (x, y, L) in sorted(placed.items()):
            f.write("%d/%-4d x=%4d y=%4d w=%3d h=%3d mapsec=%d\n" % (mg, mn, x - x0, y - y0, L.w, L.h, u8(header(mg, mn) + 20)))


if __name__ == "__main__":
    main()
