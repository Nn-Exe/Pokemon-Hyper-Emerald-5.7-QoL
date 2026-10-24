"""Makes Area Zero's people (the map sprites and the battle pictures). Run once, after changing a drawing:
    python people.py <a Hyper Emerald ROM>        (rom/ will do: only the game's own pictures are read from it)

  people_map.py, people_battle.py
      The drawings (approved by the user 2026-10-21): each person over one of the game's own sprites.
  <person>.4bpp, <person>.gbapal
      The map sprite: nine 16x32 frames (down, up, left standing; down, down, up, up, left, left walking, as the
      game's walking animations count them), each the GBA's 4bpp tiles in the order a sprite reads them; 16
      colours. Arven and Penny have the same palette, and so do Nemona and Jacq (one palette tag each pair).
  <person>_battle.4bpp, <person>_battle.gbapal
      The battle picture, 64x64 (not compressed here: the patch compresses it). Nemona, AI Sada, AI Turo.
  people_preview.png
      Everything above, to look at.

The patch reads only the .4bpp and .gbapal files (people.py in the patch's folder), so it needs no imaging library.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import romgfx as RG

MAP_PEOPLE = ("nemona", "arven", "penny", "jacq", "sada", "turo")
BATTLE_PEOPLE = ("nemona", "sada", "turo")


def gba(c):
    return (c[0] >> 3) | (c[1] >> 3) << 5 | (c[2] >> 3) << 10


def tiles(px, w, h):
    """rows of colour indices -> 4bpp tiles, row by row of tiles"""
    out = bytearray()
    for ty in range(0, h, 8):
        for tx in range(0, w, 8):
            for y in range(ty, ty + 8):
                for x in range(tx, tx + 8, 2):
                    out.append(px[y][x] & 15 | (px[y][x + 1] & 15) << 4)
    return bytes(out)


def palette(colours):
    assert len(colours) == 16
    return b"".join(struct.pack("<H", gba(c)) for c in colours)


def make():
    import people_map as PM
    import people_battle as PB
    made = {}
    for key in MAP_PEOPLE:
        name, (base, rule, drawn), pal = PM.CHARS[key]
        frames = PM.paint(base, rule, drawn)
        cols = [PM.hexc(c) for c in pal]
        assert all(max(max(r) for r in f) < 16 for f in frames)
        pic = b"".join(tiles(f, 16, 32) for f in frames)
        assert len(pic) == 9 * 0x100
        for k, f in enumerate(frames):                    # read back as the game will
            assert RG.indices(pic[0x100 * k:0x100 * (k + 1)], 16, 32) == f, (key, k)
        made[key] = ("map", frames, cols, pic, palette(cols))
    for key in BATTLE_PEOPLE:
        px, cols = PB.PICS[key][2]()
        pic = tiles(px, 64, 64)
        assert len(pic) == 0x800 and RG.indices(pic, 64, 64) == px, key
        made[key + "_battle"] = ("battle", px, cols, pic, palette(cols))
    return made


def preview(made, out):
    from PIL import Image, ImageDraw
    Z = 4
    im = Image.new("RGB", (9 * (16 * Z + 4) + 2 * (64 * 3 + 8) + 30, len(MAP_PEOPLE) * (32 * Z + 8) + 8), (112, 192, 160))
    d = ImageDraw.Draw(im)
    for r, key in enumerate(MAP_PEOPLE):
        _, frames, cols, _, _ = made[key]
        y = 4 + r * (32 * Z + 8)
        for k, f in enumerate(frames):
            p = RG.image(f, cols).resize((16 * Z, 32 * Z), Image.NEAREST)
            im.paste(p, (4 + k * (16 * Z + 4), y), p)
        d.text((4, y), key, fill=(0, 0, 0))
    for r, key in enumerate(BATTLE_PEOPLE):
        _, px, cols, _, _ = made[key + "_battle"]
        p = RG.image(px, cols).resize((64 * 3, 64 * 3), Image.NEAREST)
        x, y = 9 * (16 * Z + 4) + 20, 4 + r * (64 * 3 + 8)
        d.rectangle([x, y, x + 64 * 3, y + 64 * 3], fill=(208, 216, 224))
        im.paste(p, (x, y), p)
    im.save(out)


if __name__ == "__main__":
    RG.load(sys.argv[1])
    made = make()
    for key, (kind, _, _, pic, pal) in made.items():
        with open(os.path.join(HERE, key + ".4bpp"), "wb") as f:
            f.write(pic)
        with open(os.path.join(HERE, key + ".gbapal"), "wb") as f:
            f.write(pal)
    for a, b in (("arven", "penny"), ("nemona", "jacq")):
        assert made[a][4] == made[b][4], "%s and %s share a palette tag: their palettes must be the same" % (a, b)
    preview(made, os.path.join(HERE, "people_preview.png"))
    print("people: %s" % ", ".join(sorted(made)))
