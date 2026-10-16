"""The time rift: what the craters' two time crystals are drawn as since 2026-10-12.  python -I rift.py

The user wanted something more unique than the pale crystal and chose "B, the wide rift" from three mock-ups
(rom/unreleased/time-rift): a 32x32 tear in the air with the other time seen through it, cold blue in the past
crater (the future shows through), warm amber in the future crater, with a 4-frame shimmer. Drawn here, not from a
picture file: this is the trial kit's rift_art.py, byte for byte.

Writes, beside this file: rift_cold.4bpp and rift_warm.4bpp (the same four frames, 0x200 bytes each; mons.py
stores what is the same once) and rift_cold.gbapal / rift_warm.gbapal.
Palette index 0 clear, 1 outline, 2 edge, 3 mid, 4 core, 5 the other era's sky, 6 its ground, 7 star / spark."""
import math, struct
ZIG = [0, 0, 1, 1, 2, 1, 0, -1, -1, -2, -1, 0, 1, 2, 2, 1, 0, 0, -1, -2, -2, -1, 0, 1, 1, 0, -1, -1, 0, 0, 0, 0]
COLD = [(0, 0, 0), (28, 20, 84), (84, 76, 220), (112, 204, 255), (240, 252, 255), (20, 24, 72), (96, 84, 200), (255, 255, 255)]
WARM = [(0, 0, 0), (92, 32, 8), (236, 116, 24), (255, 212, 96), (255, 250, 228), (255, 224, 144), (120, 152, 56), (255, 255, 255)]
FRAMES = 4


def frame(phase):
    px = [[0] * 32 for _ in range(32)]
    top, bot = 1, 27
    for y in range(top, bot + 1):
        t = (y - top) / (bot - top)
        cx = 15.5 + ZIG[(y + phase) % len(ZIG)] * 0.8
        hw = 0.8 + 7.0 * math.sin(math.pi * t) ** 0.85 + (0.8 if (y + phase) % 5 == 0 else 0) - (0.9 if (y + phase) % 7 == 3 else 0)
        for x in range(32):
            d = abs(x - cx)
            if d <= hw - 2.6: px[y][x] = 5 if t < 0.62 else 6
            elif d <= hw - 1.6: px[y][x] = 4
            elif d <= hw - 0.6: px[y][x] = 3
            elif d <= hw + 0.4: px[y][x] = 2
            elif d <= hw + 1.4: px[y][x] = 1
    for (x, y) in ((14, 8), (17, 11), (13, 13), (16, 6)):
        if px[y][x] == 5: px[y][x] = 7
    for i, (x, y) in enumerate(((4, 9), (27, 12), (6, 21), (26, 20), (9, 3), (23, 4), (3, 15), (28, 17))):
        px[y][x] = 3 if (i + phase) % 2 == 0 else 2
    for x in range(8, 24):
        for y in (29, 30):
            if (x + y) % 2 == 0 and abs(x - 15.5) <= (8 if y == 29 else 6): px[y][x] = 2
    return px


def to_4bpp(px):
    out = bytearray()
    for ty in range(4):
        for tx in range(4):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[ty * 8 + y][tx * 8 + x] | (px[ty * 8 + y][tx * 8 + x + 1] << 4))
    return bytes(out)


def pictures():
    return b"".join(to_4bpp(frame(p)) for p in range(FRAMES))


def gbapal(colours):
    c = colours + [(0, 0, 0)] * (16 - len(colours))
    return b"".join(struct.pack("<H", (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)) for r, g, b in c)


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    pics = pictures()
    assert len(pics) == 0x200 * FRAMES
    for name, colours in (("rift_cold", COLD), ("rift_warm", WARM)):
        open(os.path.join(here, name + ".4bpp"), "wb").write(pics)
        open(os.path.join(here, name + ".gbapal"), "wb").write(gbapal(colours))
    print("rift_cold / rift_warm: %d frames, %d bytes of pictures, two palettes" % (FRAMES, len(pics)))
