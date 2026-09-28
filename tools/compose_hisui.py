"""Stitch the hack's Hisui into one image, from the game's own map data.

Hisui here is five 50x50 areas and a small temple map, all under the one map section "Hisui Region". Unlike
Sinnoh they carry no connection data - you move between them on Mingyao's Braviary - so there are no offsets to
stitch by. They are laid out by Legends: Arceus' geography instead. Mingyao's menu (list 137) names them; its
warps say which map is which:

    37/103 Deertrack Heights   (Obsidian Fieldlands)      west
    37/104 Prelude Beach       (Obsidian Fieldlands)      south-west, on the coast
    37/105 Firespit Island     (Cobalt Coastlands)        east
    37/106 Coronet Highlands                              centre
    37/107 Snowfall Hot Spring (Alabaster Icelands)       north
    37/108 the temple where you meet Volo, reached from Coronet Highlands' summit (40,38)

usage: python compose_hisui.py <out.png> [--scale 16|8] [--labels]
       python compose_hisui.py <out.png> --reference <hisui map picture, 1280x720> [--size N]

--reference places each area's render (N px square, default 160) on top of a picture of Hisui (the Legends:
Arceus world map) where that area is: the Icelands' snow peaks, Mt. Coronet and its summit, the Coastlands'
volcano island, the Fieldlands by the village and the lake.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_world as R

T = 50                                   # an area is 50x50 metatiles
GAP = 4                                  # metatiles of sea between areas
# (map num, name, x, y) in metatiles on the canvas
PLACES = [
    (107, "Snowfall Hot Spring", 1 * (T + GAP), 0),
    (108, "Temple (Coronet summit)", 2 * (T + GAP), 18),
    (103, "Deertrack Heights", 0, 1 * (T + GAP)),
    (106, "Coronet Highlands", 1 * (T + GAP), 1 * (T + GAP)),
    (105, "Firespit Island", 2 * (T + GAP), 1 * (T + GAP)),
    (104, "Prelude Beach", 0, 2 * (T + GAP)),
]
SEA = (40, 80, 150)

# centres on the 1280x720 Legends: Arceus map
ON_REFERENCE = {
    107: (470, 130),        # Snowfall Hot Spring - Alabaster Icelands, the snow peaks
    108: (650, 262),        # the temple - Mt. Coronet's cloud-capped summit
    106: (650, 420),        # Coronet Highlands - Mt. Coronet
    105: (1070, 190),       # Firespit Island - the volcano island off the Cobalt Coastlands
    103: (285, 455),        # Deertrack Heights - Obsidian Fieldlands, by the lake
    104: (482, 598),        # Prelude Beach - Obsidian Fieldlands, the south coast
}


def on_reference(out, ref, size):
    base = Image.open(ref).convert("RGB")
    d = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("arialbd.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    for num, name, _, _ in PLACES:
        im = Image.fromarray(R.Layout(R.ptr(R.header(37, num))).render())
        w = size if im.width >= im.height else size * im.width // im.height
        h = size * im.height // im.width if im.width >= im.height else size
        if num == 108:                                   # the temple is small: keep it small
            w, h = size * 3 // 4, size * 3 // 4 * im.height // im.width
        im = im.resize((w, h), Image.LANCZOS)
        cx, cy = ON_REFERENCE[num]
        x, y = cx - w // 2, cy - h // 2
        d.rectangle([x - 4, y - 4, x + w + 3, y + h + 3], fill=(60, 40, 20))
        d.rectangle([x - 2, y - 2, x + w + 1, y + h + 1], fill=(250, 240, 210))
        base.paste(im, (x, y))
        box = d.textbbox((0, 0), name, font=font)
        tw = box[2] - box[0]
        tx, ty = cx - tw // 2, y + h + 6
        d.rectangle([tx - 5, ty - 3, tx + tw + 5, ty + box[3] - box[1] + 5], fill=(60, 40, 20))
        d.text((tx, ty), name, fill=(250, 240, 210), font=font)
    base.save(out)
    print("wrote %s %dx%d" % (out, base.width, base.height))


def main():
    out = sys.argv[1]
    if "--reference" in sys.argv:
        size = int(sys.argv[sys.argv.index("--size") + 1]) if "--size" in sys.argv else 160
        return on_reference(out, sys.argv[sys.argv.index("--reference") + 1], size)
    scale = int(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 16
    labels = "--labels" in sys.argv
    tiles = {}
    for num, name, x, y in PLACES:
        L = R.Layout(R.ptr(R.header(37, num)))
        tiles[num] = Image.fromarray(L.render())
    w = max(x * 16 + tiles[n].width for n, _, x, y in PLACES)
    h = max(y * 16 + tiles[n].height for n, _, x, y in PLACES)
    canvas = Image.new("RGB", (w, h), SEA)
    for num, name, x, y in PLACES:
        canvas.paste(tiles[num], (x * 16, y * 16))
    if labels:
        d = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype("arialbd.ttf", 26)
        except OSError:
            font = ImageFont.load_default()
        for num, name, x, y in PLACES:
            im = tiles[num]
            d.rectangle([x * 16, y * 16, x * 16 + im.width - 1, y * 16 + im.height - 1], outline=(255, 255, 255), width=3)
            tx, ty = x * 16 + 10, y * 16 + 8
            box = d.textbbox((tx, ty), name, font=font)
            d.rectangle([box[0] - 6, box[1] - 4, box[2] + 6, box[3] + 4], fill=(0, 0, 0))
            d.text((tx, ty), name, fill=(255, 255, 255), font=font)
    if scale != 16:
        canvas = canvas.resize((canvas.width * scale // 16, canvas.height * scale // 16), Image.LANCZOS)
    canvas.save(out)
    print("wrote %s %dx%d" % (out, canvas.width, canvas.height))


if __name__ == "__main__":
    main()
