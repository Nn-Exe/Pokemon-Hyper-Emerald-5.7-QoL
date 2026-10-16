"""A map with the 7 tiles the game keeps past each of its edges, drawn as the game fills them:
python -I margins.py <built rom> <outdir> [group,num ...]        (Area Zero's maps unless some are named)

The screen shows 7 tiles either side of you and 5 above and below, so wherever the ground comes nearer than that
to a map's edge you see past it. What is there: the 7 rows or columns nearest the edge of every map joined to
that side (a connection: maps.py, world.beyond), and the map's border block (2 x 2 tiles, again and again) where
no map is joined. The red line is the map's own edge. Look at this before handing a map over: a border block
cannot go on with a cliff that runs out through the side, nor with a wood that stands a row off (test 14).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import numpy as np
from PIL import Image, ImageDraw

M = 7                                             # MAP_OFFSET: the tiles kept past each edge (one more on the east)
SOUTH, NORTH, WEST, EAST = 1, 2, 3, 4


def picture(rw, g, n):
    """(image, text) for map g/n of the ROM render_world has open."""
    hd = rw.header(g, n)
    lo = rw.ptr(hd)
    lay = rw.Layout(lo)
    w, h = lay.w, lay.h
    grid = [[None] * (w + 2 * M + 1) for _ in range(h + 2 * M)]
    for y in range(h):
        for x in range(w):
            grid[y + M][x + M] = rw.u16(lay.data + 2 * (y * w + x))
    border = [rw.u16(rw.ptr(lo + 8) + 2 * i) for i in range(4)]
    cons = rw.connections(hd)
    for d, off, cg, cn in cons:                    # FillSouthConnection and its kin, in the vanilla source
        cl = rw.Layout(rw.ptr(rw.header(cg, cn)))
        at = lambda x, y: rw.u16(cl.data + 2 * (y * cl.w + x))
        if d in (SOUTH, NORTH):
            for i in range(M):
                sy, gy = (i, h + M + i) if d == SOUTH else (cl.h - M + i, i)
                for cx in range(cl.w):
                    if 0 <= off + M + cx < w + 2 * M + 1 and 0 <= sy < cl.h:
                        grid[gy][off + M + cx] = at(cx, sy)
        elif d in (WEST, EAST):
            for i in range(M if d == WEST else M + 1):
                sx, gx = (cl.w - M + i, i) if d == WEST else (i, w + M + i)
                for cy in range(cl.h):
                    if 0 <= off + M + cy < h + 2 * M and 0 <= sx < cl.w:
                        grid[off + M + cy][gx] = at(sx, cy)
    img = np.zeros(((h + 2 * M) * 16, (w + 2 * M + 1) * 16, 3), np.uint8)
    for gy, row in enumerate(grid):
        for gx, v in enumerate(row):
            if v is None:                          # nothing joined here: the border block, in step with the map
                v = border[((gx + 1) & 1) + 2 * ((gy + 1) & 1)]
            img[gy * 16:gy * 16 + 16, gx * 16:gx * 16 + 16] = lay.metatile(v & 0x3FF)
    im = Image.fromarray(img)
    ImageDraw.Draw(im).rectangle((M * 16 - 1, M * 16 - 1, (M + w) * 16, (M + h) * 16), outline=(255, 0, 0))
    names = {SOUTH: "south", NORTH: "north", WEST: "west", EAST: "east"}
    joined = ", ".join("%s %d/%d at %d" % (names.get(d, d), cg, cn, off) for d, off, cg, cn in cons) or "none"
    return im, "%d/%d %dx%d  joined: %s  border %s" % (g, n, w, h, joined, " ".join("%04X" % b for b in border))


def main(argv):
    if len(argv) < 3:
        print(__doc__.split("\n\n")[0])
        return 2
    import map_guide as MG
    rw = MG.Rom(argv[1]).R
    os.makedirs(argv[2], exist_ok=True)
    if len(argv) > 3:
        maps = [tuple(int(v) for v in a.split(",")) for a in argv[3:]]
    else:
        num = MG.numbers()
        maps = [num[k] for k in ("mossdeep",) + MG.KEYS]
    for g, n in maps:
        im, text = picture(rw, g, n)
        im.save(os.path.join(argv[2], "margins_%d_%d.png" % (g, n)))
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
