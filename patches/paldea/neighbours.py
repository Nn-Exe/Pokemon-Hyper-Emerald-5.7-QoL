"""neighbours.py rom tile...   how the game's own maps (the General primary tileset) put tiles next to each of these:
for each tile, the commonest tiles above, below, left and right of it, and its commonest collision / height."""
import struct, sys, collections
import numpy as np

rom = open(sys.argv[1], "rb").read()
u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
LAYOUTS, COUNT, GENERAL = 0x00CFD124, 845, 0x083DF704
want = [int(a) for a in sys.argv[2:]]
near = {t: {d: collections.Counter() for d in "ULDR"} for t in want}
how = {t: collections.Counter() for t in want}
maps = {t: collections.Counter() for t in want}
for k in range(COUNT):
    lay = u32(LAYOUTS + 4 * k) - 0x08000000
    if not 0 <= lay < len(rom) - 24 or u32(lay + 16) != GENERAL:
        continue
    w, h, data = u32(lay), u32(lay + 4), u32(lay + 12) - 0x08000000
    if not (0 < w <= 256 and 0 < h <= 256):
        continue
    a = np.frombuffer(rom, "<u2", w * h, data).reshape(h, w)
    ids = a & 0x3FF
    for t in want:
        ys, xs = np.nonzero(ids == t)
        for y, x in zip(ys, xs):
            how[t][(int(a[y, x]) >> 10) & 3, int(a[y, x]) >> 12] += 1
            maps[t][k + 1] += 1
            for d, (dx, dy) in zip("ULDR", ((0, -1), (-1, 0), (0, 1), (1, 0))):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    near[t][d][int(ids[ny, nx])] += 1
for t in want:
    n = sum(how[t].values())
    print("tile %d: %d uses in %d layouts (most in layout %s); collision/height %s" % (
        t, n, len(maps[t]), maps[t].most_common(2), how[t].most_common(3)))
    for d, name in zip("ULDR", ("above", "left ", "below", "right")):
        print("    %s: %s" % (name, "  ".join("%d x%d" % c for c in near[t][d].most_common(7))))
