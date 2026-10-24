"""Makes the field sprites Kitakami installs. Run once, after changing a picture:  python -I convert.py

  carmine / kieran / briar .4bpp, .gbapal
      The three new people, as the user approved them on the Mac (2026-10-14, "happy with sprites"): each is one of
      the game's own walking sprites repainted by rom/unreleased/kitakami/kit/chars/ow.py (Carmine from 183, Kieran
      from 81, Briar from 27). Nine 16x32 frames each, in the order the game's walking animations count them
      (0 down, 1 up, 2 left, 3-8 the steps), and a 16-colour palette of its own. ow.py reads the game's sprites
      from rom/ (or HE_ROM).
  statue_okidogi / statue_munkidori / statue_fezandipiti .4bpp, statue.gbapal
      The Loyal Three's statues at Loyalty Plaza: pokeemerald-expansion's walking sprites (src/<name>_overworld.png
      and _normal.pal, rh-hideout/pokeemerald-expansion graphics/pokemon/<name>/, fetched 2026-10-16; drawn by that
      project's credited artists), their front (down) frame only, 32x32, in stone: every colour turned to one of 15
      greys by its brightness, so the three share one palette.
  preview.png
      Everything above, to look at.

The patch reads only the .4bpp and .gbapal files (ksprites.py), so it needs no imaging library.
"""
import os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
KIT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "rom", "unreleased", "kitakami", "kit", "chars"))
PEOPLE = {"carmine": "Carmine", "kieran": "Kieran", "briar": "Briar"}
STATUES = ("okidogi", "munkidori", "fezandipiti")
# stone: 15 greys from the outline to the brightest face, a little warm (index 0 stays see-through)
STONE = [(0, 0, 0)] + [(40 + 13 * k, 40 + 13 * k, 44 + 12 * k) for k in range(15)]


def gba(c):
    return (c[0] >> 3) | (c[1] >> 3) << 5 | (c[2] >> 3) << 10


def palbytes(cols):
    return b"".join(gba(c).to_bytes(2, "little") for c in cols)


def tiles(px, w, h):
    """px[y][x] colour indices -> 4bpp tiles, row by row of tiles (the order OAM reads a sprite's tiles)."""
    out = bytearray()
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[ty + y][tx + x] | px[ty + y][tx + x + 1] << 4)
    return bytes(out)


def people():
    sys.path.insert(0, KIT)
    import ow                                                # reads the ROM's sprites
    res = ow.build()
    out = {}
    for key, name in PEOPLE.items():
        frames, pal, _, _ = res[name]
        assert len(frames) == 9 and len(pal) == 16, name
        assert all(len(f) == 32 and all(len(r) == 16 for r in f) for f in frames), name
        out[key] = (b"".join(tiles(f, 16, 32) for f in frames), palbytes(pal), frames, pal)
    return out


LIVE = ("ogerpon", "okidogi", "munkidori", "fezandipiti", "pecharunt")   # (Pecharunt: Part 2, 2026-10-17)
STANDING = (0, 2, 4)                         # down, up, left


def sheet(name):
    """(the 192x32 sheet's pixels, its 16 colours) after checking it is what the expansion's files say"""
    im = Image.open(os.path.join(SRC, name + "_overworld.png"))
    assert im.mode == "P" and im.size == (192, 32), name
    lines = open(os.path.join(SRC, name + "_overworld_normal.pal")).read().split()
    assert lines[:3] == ["JASC-PAL", "0100", "16"], name
    v = list(map(int, lines[3:51]))
    pal = [tuple(v[3 * i:3 * i + 3]) for i in range(16)]
    p = im.getpalette()[:48]
    assert [tuple(p[3 * i:3 * i + 3]) for i in range(16)] == pal, "%s: the sheet's colours are not the .pal's" % name
    return im.load(), pal


def live(name):
    """the walking sprite's three standing frames (down, up, left), in its own colours: Ogerpon and the Loyal Three
    on the map (the festival, the plaza, the hunt)"""
    data, pal = sheet(name)
    frames = [[[data[32 * f + x, y] for x in range(32)] for y in range(32)] for f in STANDING]
    return b"".join(tiles(px, 32, 32) for px in frames), palbytes(pal), frames, pal


def statue(name):
    im = Image.open(os.path.join(SRC, name + "_overworld.png"))
    assert im.mode == "P" and im.size == (192, 32), name
    lines = open(os.path.join(SRC, name + "_overworld_normal.pal")).read().split()
    assert lines[:3] == ["JASC-PAL", "0100", "16"], name
    v = list(map(int, lines[3:51]))
    pal = [tuple(v[3 * i:3 * i + 3]) for i in range(16)]
    p = im.getpalette()[:48]
    assert [tuple(p[3 * i:3 * i + 3]) for i in range(16)] == pal, "%s: the sheet's colours are not the .pal's" % name
    grey = [0] + [1 + round((0.30 * r + 0.59 * g + 0.11 * b) / 255 * 14) for (r, g, b) in pal[1:]]
    data = im.load()
    px = [[grey[data[x, y]] if data[x, y] else 0 for x in range(32)] for y in range(32)]   # frame 0: down
    return tiles(px, 32, 32), px


def battle_pictures():
    """carmine_battle / kieran_battle .4bpp (64x64) and .gbapal: the approved battle pictures (kit/chars/tp.py:
    Carmine from trainer picture 87, Kieran from 232, repainted)"""
    sys.path.insert(0, KIT)
    import tp
    out = {}
    for key, fn in (("carmine", tp.carmine), ("kieran", tp.kieran)):
        px, pal = fn()
        assert len(px) == 64 and all(len(r) == 64 for r in px) and len(pal) == 16, key
        out[key] = (tiles(px, 64, 64), palbytes(pal), px, pal)
    return out


def main():
    pv = []
    for key, (pic, pal, px, cols) in battle_pictures().items():
        open(os.path.join(HERE, key + "_battle.4bpp"), "wb").write(pic)
        open(os.path.join(HERE, key + "_battle.gbapal"), "wb").write(pal)
        pv.append((key + "_battle", [px], cols, 64, 64))
    for key, (pic, pal, frames, cols) in people().items():
        open(os.path.join(HERE, key + ".4bpp"), "wb").write(pic)
        open(os.path.join(HERE, key + ".gbapal"), "wb").write(pal)
        pv.append((key, frames, cols, 16, 32))
    for name in LIVE:
        pic, pal, frames, cols = live(name)
        open(os.path.join(HERE, name + ".4bpp"), "wb").write(pic)
        open(os.path.join(HERE, name + ".gbapal"), "wb").write(pal)
        pv.append((name, frames, cols, 32, 32))
    for name in STATUES:
        pic, px = statue(name)
        open(os.path.join(HERE, "statue_%s.4bpp" % name), "wb").write(pic)
        pv.append(("statue_" + name, [px], STONE, 32, 32))
    open(os.path.join(HERE, "statue.gbapal"), "wb").write(palbytes(STONE))
    # the preview: every frame, 4x, on the town's grass green
    Z = 4
    W = 4 + max(len(f) * (w * Z + 4) for _, f, _, w, h in pv)
    H = 4 + sum(h * Z + 22 for *_, h in pv)
    sheet = Image.new("RGB", (W, H), (112, 192, 96))
    y = 4
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for key, frames, cols, w, h in pv:
        d.text((4, y), key, fill=(0, 0, 0))
        for k, px in enumerate(frames):
            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            for yy in range(h):
                for xx in range(w):
                    if px[yy][xx]:
                        im.putpixel((xx, yy), tuple(cols[px[yy][xx]]) + (255,))
            im = im.resize((w * Z, h * Z), Image.NEAREST)
            sheet.paste(im, (4 + k * (w * Z + 4), y + 16), im)
        y += h * Z + 22
    sheet.save(os.path.join(HERE, "preview.png"))
    print("wrote", ", ".join(k for k, *_ in pv), "and preview.png")


if __name__ == "__main__":
    main()
