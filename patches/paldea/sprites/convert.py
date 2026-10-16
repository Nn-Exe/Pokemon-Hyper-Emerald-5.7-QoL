"""Makes the field sprites the patch installs. Run once, after changing a picture:  python -I convert.py

  src/<name>_overworld.png, src/<name>_overworld_normal.pal
      The Gen 9 Pokemon as they walk behind you in pokeemerald-expansion (rh-hideout/pokeemerald-expansion,
      graphics/pokemon/<name>/overworld.png and overworld_normal.pal, fetched 2026-10-08; drawn by that project's
      credited artists). A sheet is six square frames: down, down stepping, up, up stepping, left, left stepping;
      16 colours, the first see-through. Most are 32x32; Koraidon, Miraidon and Raging Bolt are 64x64.
  <name>.4bpp
      The three standing frames (down, up, left), each the GBA's 4bpp tiles in the order a sprite reads them.
      Nothing in Area Zero walks, so the stepping frames are left out.
  <name>.gbapal
      16 colours, 15 bits each.
  recorder.4bpp, recorder.gbapal
      The research stations' recorder, drawn here (16x32, one frame): a small tape machine that stands on a
      counter. The game has no machine among its own sprites.
  preview.png
      Everything above, to look at.

The patch reads only the .4bpp and .gbapal files (mons.py), so it needs no imaging library.
"""
import os, struct, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
STANDING = (0, 2, 4)                      # down, up, left

# the recorder: 16 wide, the rows from RECORDER_TOP down; the rest of the 16x32 is see-through
RECORDER_TOP = 12                          # its foot is on row 24: the counter top's front edge, one tile down
RECORDER = [
    "..KKKKKKKKKKKK..",
    ".KGGGGGGGGGGGGK.",
    ".KGGKKKGGKKKGGK.",
    ".KGKTWTKKTWTKGK.",
    ".KGKWKWKKWKWKGK.",
    ".KGKTWTKKTWTKGK.",
    ".KGGKKKGGKKKGGK.",
    ".KGGGGGGGGGGGGK.",
    ".KMMMMMMMMMMMMK.",
    ".KMRMSSSSSSMLMK.",
    ".KMMMSLLLLSMMMK.",
    ".KDDDDDDDDDDDDK.",
    "..KKKKKKKKKKKK..",
]
RECORDER_COLOURS = {                       # letter -> (index, colour)
    ".": (0, (0, 136, 136)), "K": (1, (40, 40, 56)), "G": (2, (208, 212, 224)), "W": (3, (248, 248, 248)),
    "M": (4, (152, 156, 176)), "D": (5, (96, 100, 124)), "S": (6, (32, 56, 72)), "L": (7, (104, 232, 136)),
    "R": (8, (240, 72, 56)), "T": (9, (136, 88, 56)),
}


def gba(c):
    return (c[0] >> 3) | (c[1] >> 3) << 5 | (c[2] >> 3) << 10


def tiles(px, w, h):
    """px[y][x] colour indices -> 4bpp tiles, row by row of tiles (the order OAM reads a sprite's tiles)."""
    out = bytearray()
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[ty + y][tx + x] | px[ty + y][tx + x + 1] << 4)
    return bytes(out)


def sheet(name):
    im = Image.open(os.path.join(SRC, name + "_overworld.png"))
    assert im.mode == "P", name
    w, h = im.size
    assert w == 6 * h and h in (32, 64), "%s: %dx%d is not six square frames" % (name, w, h)
    lines = open(os.path.join(SRC, name + "_overworld_normal.pal")).read().split()
    assert lines[:3] == ["JASC-PAL", "0100", "16"], name
    v = list(map(int, lines[3:51]))
    pal = [tuple(v[3 * i:3 * i + 3]) for i in range(16)]
    p = im.getpalette()[:48]
    assert [tuple(p[3 * i:3 * i + 3]) for i in range(16)] == pal, "%s: the sheet's colours are not the .pal's" % name
    data = im.load()
    frames = []
    for f in STANDING:
        px = [[data[f * h + x, y] for x in range(h)] for y in range(h)]
        assert max(max(r) for r in px) < 16
        frames.append(px)
    return h, frames, pal


def recorder():
    px = [[0] * 16 for _ in range(32)]
    for y, row in enumerate(RECORDER):
        assert len(row) == 16, row
        for x, c in enumerate(row):
            px[RECORDER_TOP + y][x] = RECORDER_COLOURS[c][0]
    pal = [(0, 0, 0)] * 16
    for i, c in RECORDER_COLOURS.values():
        pal[i] = c
    return px, pal


def picture(px, pal, scale):
    h, w = len(px), len(px[0])
    im = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            if px[y][x]:
                im.putpixel((x, y), pal[px[y][x]] + (255,))
    return im.resize((w * scale, h * scale), Image.NEAREST)


def main():
    names = sorted(f[:-len("_overworld.png")] for f in os.listdir(SRC) if f.endswith("_overworld.png"))
    shots = []
    for name in names:
        size, frames, pal = sheet(name)
        open(os.path.join(HERE, name + ".4bpp"), "wb").write(b"".join(tiles(px, size, size) for px in frames))
        open(os.path.join(HERE, name + ".gbapal"), "wb").write(b"".join(struct.pack("<H", gba(c)) for c in pal))
        shots.append((name, [picture(px, pal, 3) for px in frames]))
        print("%-13s %dx%d, 3 frames" % (name, size, size))
    px, pal = recorder()
    open(os.path.join(HERE, "recorder.4bpp"), "wb").write(tiles(px, 16, 32))
    open(os.path.join(HERE, "recorder.gbapal"), "wb").write(b"".join(struct.pack("<H", gba(c)) for c in pal))
    shots.append(("recorder", [picture(px, pal, 6)]))
    print("recorder      16x32, 1 frame")
    w = max(sum(i.width + 6 for i in ims) for _, ims in shots)
    h = sum(max(i.height for i in ims) + 6 for _, ims in shots)
    out = Image.new("RGB", (w, h), (72, 120, 80))
    y = 0
    for name, ims in shots:
        x = 0
        for i in ims:
            out.paste(i, (x, y), i); x += i.width + 6
        y += max(i.height for i in ims) + 6
    out.save(os.path.join(HERE, "preview.png"))


if __name__ == "__main__":
    main()
