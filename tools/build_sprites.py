"""Cut the guide site's sprite atlases out of the ROM: Pokémon menu icons, trainer front pictures, item icons.

usage: HE_ROM=<patched rom> python tools/build_sprites.py
writes site/public/sprites/{mon,trainer,item}.png, site/public/sprites/front/<species>.png (and <species>s.png,
the shiny colours), site/public/sprites/front-<n>.webp (the same pictures on sheets, for the Pokédex index) and
site/src/data/sprites.json

One atlas per kind, one cell per table index (species id, trainer pic id, item id), so the site addresses a
sprite as (id % cols, id // cols) and never needs a name lookup. Needs Pillow.
"""
import json
import os
import struct
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROM_PATH = os.environ.get("HE_ROM") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not ROM_PATH:
    sys.exit("set HE_ROM=<path to the patched ROM>")
OUT_IMG = os.path.join(HERE, "..", "site", "public", "sprites")
OUT_DATA = os.path.join(HERE, "..", "site", "src", "data")

rom = open(ROM_PATH, "rb").read()
assert rom[0xAC:0xB0] == b"BPEE", "not the expected ROM"

ICON_TABLE = 0x00F2A020     # species -> 32x64 4bpp icon, two frames (GetMonIconTiles' table)
ICON_PALIDX = 0x00F2B2E0    # species -> icon palette 0-5
ICON_PALS = 0x0057C540      # gMonIconPaletteTable: {palette pointer, tag} x 6
TRAINER_PICS = 0x0101BE90   # {LZ77 64x64 4bpp, u16 size, u16 tag} x 250 (found by a table scan; 8 bytes each)
TRAINER_PALS = 0x0101C660   # {LZ77 palette, u16 tag, pad} x 250, referenced from the vanilla trainer-pic code
ITEM_ICONS = 0x00FCBFF4     # item -> {LZ77 24x24 4bpp, LZ77 palette}
N_SPECIES, N_TRAINER_PICS, N_ITEMS = 1200, 250, 769


def u32(o):
    return struct.unpack_from("<I", rom, o)[0]


def off(p):
    return p - 0x08000000


def valid(p):
    return 0x08000000 <= p < 0x08000000 + len(rom)


def lz77(o):
    assert rom[o] == 0x10, "not LZ77 at %#x" % o
    size = rom[o + 1] | rom[o + 2] << 8 | rom[o + 3] << 16
    out = bytearray()
    o += 4
    while len(out) < size:
        flags = rom[o]
        o += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = rom[o], rom[o + 1]
                o += 2
                n = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                for _ in range(n):
                    out.append(out[-disp])
            else:
                out.append(rom[o])
                o += 1
    return bytes(out[:size])


def palette(raw):
    cols = []
    for i in range(16):
        c = raw[2 * i] | raw[2 * i + 1] << 8
        r, g, b = c & 31, c >> 5 & 31, c >> 10 & 31
        cols.append((r << 3 | r >> 2, g << 3 | g >> 2, b << 3 | b >> 2, 0 if i == 0 else 255))
    return cols


def tiles(data, w, h, pal):
    """4bpp 8x8 tiles, row-major, to an RGBA image of w x h pixels."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for t in range((w // 8) * (h // 8)):
        tx, ty = (t % (w // 8)) * 8, (t // (w // 8)) * 8
        for y in range(8):
            for x in range(8):
                b = data[t * 32 + y * 4 + x // 2]
                px[tx + x, ty + y] = pal[b >> 4 if x & 1 else b & 15]
    return im


def atlas(cells, size, cols):
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * size, rows * size), (0, 0, 0, 0))
    for i, im in enumerate(cells):
        if im is not None:
            sheet.paste(im, ((i % cols) * size, (i // cols) * size))
    return sheet


def save(sheet, name):
    path = os.path.join(OUT_IMG, name)
    colours = sheet.getcolors(maxcolors=256)
    if colours is not None:             # few enough colours: a palette PNG is a third of the size
        sheet = sheet.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    sheet.save(path, optimize=True)
    return os.path.getsize(path)


os.makedirs(OUT_IMG, exist_ok=True)
os.makedirs(OUT_DATA, exist_ok=True)
meta = {}

# ---- Pokémon menu icons (first frame) ----
icon_pals = [palette(rom[off(u32(ICON_PALS + 8 * i)):][:32]) for i in range(6)]
cells, have = [], []
for sid in range(N_SPECIES):
    p = u32(ICON_TABLE + 4 * sid)
    if sid == 0 or not valid(p):
        cells.append(None)
        continue
    im = tiles(rom[off(p):off(p) + 512], 32, 32, icon_pals[rom[ICON_PALIDX + sid] % 6])
    cells.append(im)
    have.append(sid)
size = save(atlas(cells, 32, 40), "mon.png")
meta["mon"] = {"file": "mon.png", "cell": 32, "cols": 40, "count": N_SPECIES}
print("mon icons: %d species, %d bytes" % (len(have), size))

# ---- trainer front pictures ----
cells = []
for pic in range(N_TRAINER_PICS):
    p, q = u32(TRAINER_PICS + 8 * pic), u32(TRAINER_PALS + 8 * pic)
    try:
        cells.append(tiles(lz77(off(p)), 64, 64, palette(lz77(off(q)))))
    except (AssertionError, IndexError):
        cells.append(None)
size = save(atlas(cells, 64, 16), "trainer.png")
meta["trainer"] = {"file": "trainer.png", "cell": 64, "cols": 16, "count": N_TRAINER_PICS}
print("trainer pics: %d, %d bytes" % (sum(c is not None for c in cells), size))

# ---- item icons ----
cells = []
for item in range(N_ITEMS):
    p, q = u32(ITEM_ICONS + 8 * item), u32(ITEM_ICONS + 8 * item + 4)
    try:
        cells.append(tiles(lz77(off(p)), 24, 24, palette(lz77(off(q)))))
    except (AssertionError, IndexError):
        cells.append(None)
size = save(atlas(cells, 24, 32), "item.png")
meta["item"] = {"file": "item.png", "cell": 24, "cols": 32, "count": N_ITEMS}
print("item icons: %d, %d bytes" % (sum(c is not None for c in cells), size))

# ---- front pictures, normal and shiny: one small file a species, for the Pokédex ----
# (64x64 with a palette of its own each, so a sheet could not share colours; a page shows one or two)
FRONT_PICS = u32(0x128) - 0x08000000        # ROM header: {LZ77 64x64 4bpp, u16 size, u16 tag}
FRONT_PALS = u32(0x130) - 0x08000000        # {LZ77 palette, u16 tag, pad}
SHINY_PALS = u32(0x134) - 0x08000000
front_dir = os.path.join(OUT_IMG, "front")
os.makedirs(front_dir, exist_ok=True)
dex_file = os.path.join(OUT_DATA, "pokedex.json")
wanted = ([sp["sid"] for sp in json.load(open(dex_file, encoding="utf-8"))["species"]]
          if os.path.exists(dex_file) else range(1, N_SPECIES))
written = total = 0
normal = {}                                 # species -> its picture in true colour, for the sheets below
for sid in wanted:
    try:
        pixels = lz77(off(u32(FRONT_PICS + 8 * sid)))[:2048]
        for suffix, table in (("", FRONT_PALS), ("s", SHINY_PALS)):
            pal = palette(lz77(off(u32(table + 8 * sid))))
            if not suffix:
                normal[sid] = tiles(pixels, 64, 64, pal)
            # keep colour 0 see-through: a palette image with index 0 transparent
            flat = Image.new("P", (64, 64))
            flat.putpalette([c for col in pal for c in col[:3]])
            flat.putdata([pixels[(y // 8 * 8 + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2] >> (4 if x & 1 else 0) & 15
                          for y in range(64) for x in range(64)])
            path = os.path.join(front_dir, "%d%s.png" % (sid, suffix))
            flat.save(path, optimize=True, transparency=0)
            total += os.path.getsize(path)
        written += 1
    except (AssertionError, IndexError, struct.error):
        continue
meta["front"] = {"dir": "front", "cell": 64, "count": written}
print("front pictures: %d species x 2 (normal, shiny), %d bytes" % (written, total))

# ---- the same pictures on sheets, for the Pokédex index: a cell a species in the index's order, 200 to a
# sheet. A card each would be a request each, over a thousand for one visitor who scrolls the index, and a
# host the site is also on counts requests; this way the index asks for six files.
SHEET, SHEET_COLS = 200, 20
order = [sid for sid in wanted if sid in normal]
for name in os.listdir(OUT_IMG):
    if name.startswith("front-") and name.endswith(".webp"):
        os.remove(os.path.join(OUT_IMG, name))
sheets, total = [], 0
for k in range(0, len(order), SHEET):
    name = "front-%d.webp" % (k // SHEET)
    path = os.path.join(OUT_IMG, name)
    atlas([normal[sid] for sid in order[k:k + SHEET]], 64, SHEET_COLS).save(path, lossless=True, quality=100, method=6)
    sheets.append(name)
    total += os.path.getsize(path)
meta["frontSheet"] = {"files": sheets, "cell": 64, "cols": SHEET_COLS, "per": SHEET, "order": order}
print("front picture sheets: %d, %d bytes" % (len(sheets), total))

json.dump(meta, open(os.path.join(OUT_DATA, "sprites.json"), "w", encoding="utf-8"), indent=1)
