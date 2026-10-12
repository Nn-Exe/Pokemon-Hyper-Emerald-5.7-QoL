"""Draw where each pick-up of the guide's location lists lies: the map around its tile, with the object on it.

usage: HE_ROM=<the release's rom> python tools/build_spot_maps.py        (needs numpy and Pillow)
reads site/src/data/*.json for sources with a `spot` (tools/build_tm_locations.py, build_mega_stones.py and
build_guide_items.py write them; run those first)
writes site/public/spots/<spot>.webp and site/src/data/spots.json

A spot is "group-num-x-y": a map and a tile (tools/romdata/item_sources.py). Its picture is the map around that
tile, 21 x 15 metatiles drawn from the map's own tilesets by tools/render_world.py, with a frame around the tile
and, when an object stands on it, that object's sprite as the game draws it (item_sources.sprite: the hack's
extended sprites included; other people and objects are left out). A map smaller than the picture is drawn whole,
so spots.json gives each picture's size. Pictures no source names any more are removed.
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "romdata"))
import render_world as W                                   # noqa: E402
import romlib as R                                         # noqa: E402
import item_sources as I                                   # noqa: E402

DATA = os.path.join(HERE, "..", "site", "src", "data")
OUT = os.path.join(HERE, "..", "site", "public", "spots")
LISTS = ("tms.json", "megastones.json", "guide-items.json")
ACROSS, DOWN = 21, 15                                      # metatiles in a picture
WHITE, RED = (255, 255, 255), (232, 36, 64)
PALETTES = 0x50BBC8                                        # object palettes: {pointer, tag, -} each


def spots_in(node, into):
    if isinstance(node, dict):
        if isinstance(node.get("spot"), str):
            into.add(node["spot"])
        for v in node.values():
            spots_in(v, into)
    elif isinstance(node, list):
        for v in node:
            spots_in(v, into)
    return into


spots = set()
for name in LISTS:
    path = os.path.join(DATA, name)
    if os.path.exists(path):
        spots_in(json.load(open(path, encoding="utf-8")), spots)

by_map = {(m["group"], m["num"]): m for m in R.load("maps.json")}
drawn = {}


def palette(tag):
    o = PALETTES
    while I.S.inrom(R.u32(o)):
        if R.u16(o + 4) == tag:
            p = R.u32(o) - I.S.BASE
            return [((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)
                    for c in (R.u16(p + 2 * k) for k in range(16))]
        o += 8
    return None


def object_at(m, x, y):
    """(graphics, extended graphics) of the map's object on a tile, or None."""
    ev = int(m["events"], 16) - I.S.BASE
    for index in range(I.rom[ev]):
        t = I.template(m, index)
        if (t[4] | t[5] << 8, t[6] | t[7] << 8) == (x, y):
            return t[1], t[3]
    return None


def stamp(cut, px, py, gfx, ext):
    """Draw an object's first frame standing on the tile at px,py: centred on it, feet on its lower edge."""
    f = I.frame(gfx, ext)
    pal = palette(f[2]) if f else None
    if not pal:
        return
    wide, high, _, data = f
    for tile in range(len(data) // 32):
        tx, ty = tile % (wide // 8) * 8, tile // (wide // 8) * 8
        for k in range(64):
            b = data[tile * 32 + k // 2]
            colour = b >> 4 if k & 1 else b & 15
            x, y = px + 8 - wide // 2 + tx + k % 8, py + 16 - high + ty + k // 8
            if colour and 0 <= x < cut.shape[1] and 0 <= y < cut.shape[0]:
                cut[y, x] = pal[colour]


def picture(group, num, x, y):
    if (group, num) not in drawn:
        drawn[(group, num)] = W.Layout(W.ptr(W.header(group, num))).render()
    img = drawn[(group, num)]
    high, wide = img.shape[0] // 16, img.shape[1] // 16
    assert 0 <= x < wide and 0 <= y < high, "the tile %d,%d is off map %d/%d (%d x %d)" % (x, y, group, num, wide, high)
    x0 = min(max(0, x - ACROSS // 2), max(0, wide - ACROSS))
    y0 = min(max(0, y - DOWN // 2), max(0, high - DOWN))
    cut = img[y0 * 16:(y0 + DOWN) * 16, x0 * 16:(x0 + ACROSS) * 16].copy()
    px, py = (x - x0) * 16, (y - y0) * 16
    for grow, colour in ((4, WHITE), (3, RED), (2, RED), (1, RED)):     # a red frame around the tile, edged white
        a, b = max(0, py - grow), min(cut.shape[0], py + 16 + grow)
        c, d = max(0, px - grow), min(cut.shape[1], px + 16 + grow)
        cut[a:b, [c, d - 1]] = colour
        cut[[a, b - 1], c:d] = colour
    who = object_at(by_map[(group, num)], x, y)
    if who:
        stamp(cut, px, py, *who)
    return Image.fromarray(cut)


os.makedirs(OUT, exist_ok=True)
sizes = {}
for spot in sorted(spots, key=lambda s: [int(v) for v in s.split("-")]):
    im = picture(*(int(v) for v in spot.split("-")))
    im.save(os.path.join(OUT, spot + ".webp"), "WEBP", lossless=True, method=6)
    sizes[spot] = [im.width, im.height]
stale = [f for f in os.listdir(OUT) if f.endswith(".webp") and f[:-5] not in sizes]
for f in stale:
    os.remove(os.path.join(OUT, f))
json.dump(sizes, open(os.path.join(DATA, "spots.json"), "w", encoding="utf-8"), separators=(",", ":"))
total = sum(os.path.getsize(os.path.join(OUT, s + ".webp")) for s in sizes)
print("spots: %d pictures on %d maps, %d bytes in all; %d old ones removed" % (len(sizes), len(drawn), total, len(stale)))
