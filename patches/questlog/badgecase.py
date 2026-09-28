"""The Badges chapter's badge case: 32x32 art for Sinnoh's eight badges, as the Quest Log's case view shows them
(Hoenn's are on the Trainer Card already).

Each badge sits in a 4x4-tile window of its own with its own BG palette, laid out as the window's tile buffer
(row-major tiles, 4bpp). Palette: 0 unused (transparent), 1-11 the badge, 12 the case panel's colour (every
pixel around the badge, so the window blends into the panel - a transparent pixel would show the backdrop), 13
and 14 a not-yet-earned badge's silhouette (fill, outline), 15 the white sparkle an earned badge carries.

The art: badges/sinnoh.png, cut from a picture of Platinum's badge case (badges/extract_sinnoh.py).
"""
import os, struct
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PANEL = (36, 52, 84)                    # the Quest Log's card colour (PAL[13])
SIL_FILL, SIL_EDGE, SPARKLE = (22, 32, 56), (66, 88, 128), (248, 248, 248)
ART_COLOURS = 11

SPARK_BIG = ["..W..", "..W..", "WWWWW", "..W..", "..W.."]
SPARK_SMALL = [".W.", "WWW", ".W."]


def gba(c):
    return tuple((v >> 3) << 3 for v in c)


def sinnoh():
    im = np.asarray(Image.open(os.path.join(HERE, "badges", "sinnoh.png")).convert("RGBA"))
    out = []
    for b in range(8):
        cell = im[:, 32 * b:32 * b + 32]
        out.append([[tuple(int(v) for v in cell[y, x, :3]) if cell[y, x, 3] >= 128 else None for x in range(32)]
                    for y in range(32)])
    return out


def badge(px):
    """(art tiles, silhouette tiles, palette bytes) for one 32x32 grid of colours / None."""
    opaque = [(y, x) for y in range(32) for x in range(32) if px[y][x] is not None]
    cols = sorted({gba(px[y][x]) for y, x in opaque})
    if len(cols) > ART_COLOURS:                                  # median cut down to the art's 11 slots
        img = Image.new("RGB", (len(opaque), 1))
        img.putdata([px[y][x] for y, x in opaque])
        q = img.quantize(colors=ART_COLOURS, method=Image.MEDIANCUT, dither=Image.NONE)
        qp = q.getpalette()[:3 * ART_COLOURS]
        idx = list(q.get_flattened_data() if hasattr(q, "get_flattened_data") else q.getdata())
        cols = [gba(tuple(qp[3 * i:3 * i + 3])) for i in range(ART_COLOURS)]
        art_of = {p: idx[k] + 1 for k, p in enumerate(opaque)}
    else:
        lut = {c: k + 1 for k, c in enumerate(cols)}
        art_of = {(y, x): lut[gba(px[y][x])] for y, x in opaque}
    pal = [(0, 0, 0)] + cols + [(0, 0, 0)] * (ART_COLOURS - len(cols)) + [PANEL, SIL_FILL, SIL_EDGE, SPARKLE]
    assert len(pal) == 16
    art = [[12] * 32 for _ in range(32)]
    sil = [[12] * 32 for _ in range(32)]
    mask = {p for p in opaque}
    for (y, x), v in art_of.items():
        art[y][x] = v
        edge = any((y + dy, x + dx) not in mask for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        sil[y][x] = 14 if edge else 13
    for shape, (oy, ox) in ((SPARK_BIG, (3, 4)), (SPARK_SMALL, (19, 20))):   # the polish sparkle, top left
        for dy, row in enumerate(shape):
            for dx, ch in enumerate(row):
                if ch == "W":
                    art[oy + dy][ox + dx] = 15
    return tiles(art), tiles(sil), b"".join(struct.pack("<H", (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10)
                                              for r, g, b in pal)


def tiles(g):
    out = bytearray()
    for ty in range(4):
        for tx in range(4):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(g[ty * 8 + y][tx * 8 + x] | g[ty * 8 + y][tx * 8 + x + 1] << 4)
    return bytes(out)


def all_badges(rom=None):
    """8 x (art, silhouette, palette), in badge order."""
    return [badge(px) for px in sinnoh()]


def preview(rom, path):
    """The case as the screen shows it: earned on the top row, silhouettes below."""
    bs = all_badges(rom)
    img = Image.new("RGB", (8 * 40, 2 * 40), PANEL)
    for k, (art, sil, pal) in enumerate(bs):
        p = [struct.unpack_from("<H", pal, 2 * i)[0] for i in range(16)]
        p = [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in p]
        for row, data in ((0, art), (1, sil)):
            for t in range(16):
                for y in range(8):
                    for x in range(8):
                        v = (data[t * 32 + y * 4 + x // 2] >> ((x & 1) * 4)) & 15
                        img.putpixel(((k % 8) * 40 + 4 + (t % 4) * 8 + x,
                                      row * 40 + 4 + (t // 4) * 8 + y), p[v])
    img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(path)


if __name__ == "__main__":
    import sys
    preview(open(sys.argv[1], "rb").read(), sys.argv[2])
