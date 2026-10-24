"""preview.py <rom> <out.png>: Mossui Town drawn from the tileset tileset.build() makes - its own
cells, metatiles and palettes, the General set's for the primary half - exactly as the game reads them, so what
the patch writes can be looked at before it is in the game. Prints what the build used and has left."""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
import tileset as T, kworld as WD


def renderer(rom, built):
    gen = T.PT.Set(rom, T.GENERAL)
    gmeta = struct.unpack_from("<4096H", rom, struct.unpack_from("<I", rom, T.GENERAL - 0x08000000 + 12)[0] - 0x08000000)
    pal = np.zeros((16, 16, 3), np.uint8)
    for r in range(16):
        row = gen.pals[r] if r < 6 else built.pals[r]
        for c in range(16):
            v = row[c]
            pal[r, c] = ((v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3)
    cache = {}

    def cell(t):
        b = gen.raw(t) if t < 512 else built.cells[(t - 512) * 32:(t - 512) * 32 + 32]
        px = np.zeros((8, 8), np.uint8)
        for y in range(8):
            for x in range(8):
                v = b[y * 4 + x // 2]
                px[y, x] = (v >> 4) if x & 1 else (v & 15)
        return px

    def metatile(m):
        if m in cache:
            return cache[m]
        e = gmeta[16 * m // 2:16 * m // 2 + 8] if m < 512 else \
            struct.unpack_from("<8H", built.metatiles, 16 * (m - 512))
        out = np.zeros((16, 16, 3), np.uint8)
        out[:, :] = pal[0, 0]
        for k, v in enumerate(e):
            t, xf, yf, r = v & 0x3FF, v >> 10 & 1, v >> 11 & 1, v >> 12
            px = cell(t)
            if xf: px = px[:, ::-1]
            if yf: px = px[::-1, :]
            q = k % 4
            y0, x0 = (q // 2) * 8, (q % 2) * 8
            mask = px != 0
            out[y0:y0 + 8, x0:x0 + 8][mask] = pal[r][px[mask]]
        cache[m] = out
        return out

    def render(blocks):
        h, w = len(blocks), len(blocks[0])
        img = np.zeros((h * 16, w * 16, 3), np.uint8)
        for y in range(h):
            for x in range(w):
                img[y * 16:y * 16 + 16, x * 16:x * 16 + 16] = metatile(blocks[y][x] & 0x3FF)
        return Image.fromarray(img)
    return render


def build_all(rom):
    town, ov, marks = WD.mossui(rom)
    need = WD.needed((town, ov, WD.TEAL))
    built = T.build(rom, need, WD.art_used(ov))
    return built, WD.finish(town, ov, WD.TEAL, built.ids), marks, need


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    built, town, marks, need = build_all(rom)
    print("base metatiles the map uses: %d; rows: %s; cells left: %d; ours: %d (953-%d)" % (
        len(need), built.rows, built.free_cells_left, len(built.ids), 952 + len(built.ids)))
    img = renderer(rom, built)(town)
    img.save(sys.argv[2])
    print("wrote", sys.argv[2], img.size)
