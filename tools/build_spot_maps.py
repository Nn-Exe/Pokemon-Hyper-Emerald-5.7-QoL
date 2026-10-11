"""Draw the tile of every pick-up nobody can see, for the guide's TMs page and its Mega Stones list.

usage: HE_ROM=<patched rom> python tools/build_spot_maps.py        (needs numpy and Pillow)
reads site/src/data/tms.json and megastones.json (run tools/build_tm_locations.py and build_mega_stones.py first)
writes site/public/spots/<spot>.webp and site/src/data/spots.json

A spot is "group-num-x-y": a map and the tile an unseen object stands on (tools/romdata/item_sources.py). Its
picture is the map around that tile, 21 x 15 metatiles drawn from the map's own tilesets by tools/render_world.py
(no people, no item balls), with a frame around the tile. A map smaller than the picture is drawn whole, so
spots.json gives each picture's size. Pictures no source names any more are removed.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_world as W                                   # noqa: E402

DATA = os.path.join(HERE, "..", "site", "src", "data")
OUT = os.path.join(HERE, "..", "site", "public", "spots")
ACROSS, DOWN = 21, 15                                      # metatiles in a picture
WHITE, RED = (255, 255, 255), (232, 36, 64)

spots = set()
for name in ("tms.json", "megastones.json"):
    for entry in json.load(open(os.path.join(DATA, name), encoding="utf-8")):
        spots.update(s["spot"] for s in entry["sources"] if "spot" in s)

maps = {}


def picture(group, num, x, y):
    if (group, num) not in maps:
        maps[(group, num)] = W.Layout(W.ptr(W.header(group, num))).render()
    img = maps[(group, num)]
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
print("spots: %d pictures on %d maps, %d bytes in all; %d old ones removed" % (len(sizes), len(maps), total, len(stale)))
