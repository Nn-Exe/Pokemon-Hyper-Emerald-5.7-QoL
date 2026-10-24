"""The new pictures of Area Zero's people as the game reads them (2026-10-22): sprites/<name>.png (indexed, colour 0
see-through; made by _testrun/paldea/people/redraw: redraw.py, draw3.py, finalize.py) -> sprites/<name>.4bpp and the
palettes sprites/pal_<A-D>.gbapal, <name>_battle.gbapal. python -I make.py

Walkers: nine 32 x 32 frames side by side, each four tiles by four, row by row (the order a 32 x 32 object's tiles are
read in). Battle pictures: 64 x 64, eight tiles by eight. Palettes: 16 colours, 15-bit; colour 0 is never drawn.
"""
import os, struct
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, "sprites")
WALKERS = {"nemona": "B", "jacq": "B", "arven": "A", "penny": "A", "sada": "C", "turo": "D"}
BATTLE = ("nemona", "sada", "turo")


def gba(c):
    return (c[0] >> 3) | (c[1] >> 3) << 5 | (c[2] >> 3) << 10


def tiles(px, w, h, x0=0):
    out = bytearray()
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            for y in range(ty, ty + 8):
                for x in range(tx, tx + 8, 2):
                    out.append(px[y][x0 + x] & 15 | (px[y][x0 + x + 1] & 15) << 4)
    return bytes(out)


def load(name):
    im = Image.open(os.path.join(SPR, name + ".png"))
    assert im.mode == "P", name
    w, h = im.size
    data = list(im.getdata())
    px = [data[y * w:(y + 1) * w] for y in range(h)]
    pal = im.getpalette()[:48]
    cols = [tuple(pal[3 * i:3 * i + 3]) for i in range(16)]
    assert max(max(r) for r in px) <= 15, name
    return px, w, h, cols


def palette(cols):
    return b"".join(struct.pack("<H", gba(c)) for c in cols)


def main():
    pals = {}
    for key, group in WALKERS.items():
        px, w, h, cols = load(key + "_walk")
        assert (w, h) == (32 * 9, 32), key
        data = b"".join(tiles(px, 32, 32, 32 * f) for f in range(9))
        assert len(data) == 9 * 0x200
        open(os.path.join(SPR, key + "_walk.4bpp"), "wb").write(data)
        p = palette(cols)
        assert pals.setdefault(group, p) == p, "%s does not share palette %s's colours" % (key, group)
    for group, p in pals.items():
        open(os.path.join(SPR, "pal_%s.gbapal" % group), "wb").write(p)
    for key in BATTLE:
        px, w, h, cols = load(key + "_battle")
        assert (w, h) == (64, 64), key
        open(os.path.join(SPR, key + "_battle.4bpp"), "wb").write(tiles(px, 64, 64))
        open(os.path.join(SPR, key + "_battle.gbapal"), "wb").write(palette(cols))
    print("made: %s; palettes %s" % (", ".join(sorted(WALKERS) + [k + "_battle" for k in BATTLE]), sorted(pals)))


if __name__ == "__main__":
    main()
