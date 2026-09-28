"""Draw a Hisui town map in the Sinnoh Map's style, from a picture of Hisui (the Legends: Arceus world map).

The Sinnoh Map (patches/sinnohmap) shows a DS-style town map: teal sea with lighter shallows around every coast,
a dark-green coast ring, greens with lighter patches, khaki hills with olive outlines, red squares for the places
you can fly to. Everything here is drawn in exactly that palette (sampled from
sinnoh-map/sinnoh-townmap-nobattlezone.png) at the GBA screen size, with the detail read off the reference:

  * coastline, rivers and lakes from its water;
  * terrain tone - light green, green, golden khaki - from its colours, smoothed so no single pixel stands alone;
  * mountain ridges and forest clumps from its brush outlines (pixels darker than their surroundings), drawn as
    darker lines: dark green on grass, olive on khaki, grey on snow;
  * the Alabaster Icelands' snow from a traced region (the painting's snow is the same cream as its clouds), the
    clouds themselves from traced boxes, and a red tip on Firespit Island's volcano.

Points: Mingyao's five Braviary destinations (37/103-107) are fly points (red squares); the temple on Mt. Coronet's
summit (37/108) is reached on foot from Coronet Highlands, so it gets the small blue mark.

usage: python make_hisui_townmap.py <reference.png> <out dir>
writes hisui-townmap.png (240x160, what the GBA screen would show), hisui-townmap-x4.png (a labelled preview)
and hisui-locations.json (each point: map, name, kind, x/y in pixels and in 8x8 tiles).
"""
import json, os, sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 240, 160
CROP_X0, CROP_X1 = 60, 1220               # the island's width on the 1280x720 reference
PAD_Y = 5

SEA_DEEP, SEA_MID, SEA_NEAR = (0x17, 0x9f, 0xb7), (0x2f, 0xaf, 0xc8), (0x3f, 0xc8, 0xd8)
COAST_DARK, COAST_MID = (0x57, 0x8f, 0x08), (0x6f, 0xaf, 0x2f)
GRASS, GRASS_LIGHT = (0x87, 0xc8, 0x47), (0x9f, 0xd8, 0x5f)
KHAKI, OLIVE = (0xd0, 0xbf, 0x47), (0x8f, 0x9f, 0x1f)
SNOW, SNOW_LIGHT, ROCK = (0xe0, 0xe0, 0xe0), (0xf8, 0xf8, 0xf8), (0xaf, 0xaf, 0xaf)
WATER_IN = (0x3f, 0xc8, 0xd8)
RED, RED_DARK, RED_LIGHT = (0xf0, 0x67, 0x67), (0xbf, 0x37, 0x37), (0xf8, 0x9f, 0x9f)
BLUE, BLUE_DARK, BLUE_LIGHT = (0x6f, 0x87, 0xf8), (0x47, 0x5f, 0xd0), (0x9f, 0xb7, 0xf0)
OUTLINE = (0xe0, 0xe0, 0xe0)

# points on the reference (1280x720): (map, name, x, y, kind)
POINTS = [
    (107, "Snowfall Hot Spring", 470, 150, "fly"),     # Alabaster Icelands, below the snow peaks
    (108, "Temple", 640, 248, "place"),                 # Mt. Coronet's summit, on foot from Coronet Highlands
    (106, "Coronet Highlands", 650, 345, "fly"),       # the slopes of Mt. Coronet
    (105, "Firespit Island", 1070, 195, "fly"),        # the volcano island off the Cobalt Coastlands
    (103, "Deertrack Heights", 300, 462, "fly"),       # Obsidian Fieldlands, inland by the lake
    (104, "Prelude Beach", 458, 548, "fly"),           # Obsidian Fieldlands, the east-facing coast
]

CLOUDS_OVER_SEA = [(745, 8, 1045, 132), (1085, 118, 1195, 180), (65, 200, 300, 270), (995, 550, 1225, 640),
                   (0, 530, 310, 720)]                          # the last hides the south-west tip: sea
CLOUDS_OVER_LAND = [(555, 212, 705, 258)]                       # Mt. Coronet's cap
SNOW_POLY = [(375, 175), (395, 90), (440, 15), (525, 18), (610, 65), (670, 115), (735, 175), (715, 235),
             (625, 250), (540, 262), (450, 262), (385, 240)]   # Alabaster Icelands: snow where it is white
SNOW_LUM = 150
VOLCANO_TIP = (1072, 170)

SEA, LAND, INWATER = 0, 1, 2              # map classes
T_LIGHT, T_GREEN, T_KHAKI = 0, 1, 2       # land tones
RIDGE_FRACTION = 0.14                     # share of outline pixels in a screen pixel that makes it a ridge


def scale():
    return W / (CROP_X1 - CROP_X0)


def to_screen(x, y):
    s = scale()
    return int(round((x - CROP_X0) * s)), int(round(PAD_Y + y * s))


def box_mean(a, r):
    c = np.pad(a, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    h, w = a.shape
    y0 = np.clip(np.arange(h) - r, 0, h); y1 = np.clip(np.arange(h) + r + 1, 0, h)
    x0 = np.clip(np.arange(w) - r, 0, w); x1 = np.clip(np.arange(w) + r + 1, 0, w)
    s = c[y1][:, x1] - c[y0][:, x1] - c[y1][:, x0] + c[y0][:, x0]
    n = (y1 - y0)[:, None] * (x1 - x0)[None, :]
    return s / n


def read_reference(ref):
    a = np.asarray(ref, dtype=np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = (r * 3 + g * 6 + b) / 10.0
    water = (b > r + 35) & (g > r + 30) & (r < 140)
    for x0, y0, x1, y1 in CLOUDS_OVER_SEA:
        water[y0:y1, x0:x1] = True
    cloud_land = np.zeros_like(water)
    for x0, y0, x1, y1 in CLOUDS_OVER_LAND:
        keep = np.zeros((y1 - y0, x1 - x0), bool)
        keep[:, :max(0, 40 - x0)] = True
        water[y0:y1, x0:x1] &= keep
        cloud_land[y0:y1, x0:x1] = True
    outline = (lum < box_mean(lum, 10) - 26) & ~water & ~cloud_land
    # khaki only where the painting is clearly golden or brown; its yellow-greens stay green, as Sinnoh is
    tone = np.where(r > g + 12, T_KHAKI, np.where(lum > 172, T_LIGHT, T_GREEN))
    tone[cloud_land] = T_GREEN
    return water, outline, tone, lum


def downsample(water, outline, tone, lum):
    s = scale()
    m = np.full((H, W), SEA, np.uint8)
    t = np.full((H, W), T_GREEN, np.uint8)
    ridge = np.zeros((H, W), bool)
    light = np.zeros((H, W), np.float32)
    for ty in range(H):
        y0, y1 = int((ty - PAD_Y) / s), int((ty - PAD_Y + 1) / s)
        if y1 <= 0 or y0 >= water.shape[0]:
            continue
        y0, y1 = max(0, y0), min(water.shape[0], max(y1, y0 + 1))
        for tx in range(W):
            x0 = int(CROP_X0 + tx / s)
            x1 = max(int(CROP_X0 + (tx + 1) / s), x0 + 1)
            if water[y0:y1, x0:x1].mean() > 0.5:
                continue
            m[ty, tx] = LAND
            block = tone[y0:y1, x0:x1]
            t[ty, tx] = np.bincount(block.ravel(), minlength=3).argmax()
            ridge[ty, tx] = outline[y0:y1, x0:x1].mean() > RIDGE_FRACTION
            light[ty, tx] = lum[y0:y1, x0:x1].mean()
    return m, t, ridge, light


def neighbours(y, x):
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ny, nx = y + dy, x + dx
        if 0 <= ny < H and 0 <= nx < W:
            yield ny, nx


def components(mask):
    seen = np.zeros_like(mask)
    out = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                comp, q = [], deque([(y, x)])
                seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    comp.append((cy, cx))
                    for ny, nx in neighbours(cy, cx):
                        if mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                out.append(comp)
    return out


def split_water(m):
    """Open sea keeps its halo; water that is thin (rivers) or enclosed (lakes, marsh ponds) is inland water."""
    water = m == SEA
    core = np.zeros_like(water)
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            core[y, x] = water[y - 1:y + 2, x - 1:x + 2].all()
    opened = np.zeros_like(water)
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            opened[y, x] = core[y - 1:y + 2, x - 1:x + 2].any()
    for edge in (np.s_[0, :], np.s_[-1, :], np.s_[:, 0], np.s_[:, -1]):
        opened[edge] |= water[edge]
    m = m.copy()
    m[water & ~opened] = INWATER                       # rivers and narrow inlets
    for comp in components(m == SEA):
        if not any(y in (0, H - 1) or x in (0, W - 1) for y, x in comp):
            for y, x in comp:
                m[y, x] = INWATER                      # lakes
    for comp in components(m == INWATER):
        if len(comp) < 3:
            for y, x in comp:
                m[y, x] = LAND                         # a lone pixel of water is paint, not a pond
    for comp in components(m == LAND):
        if len(comp) < 6:
            for y, x in comp:
                m[y, x] = SEA                          # stray islets from the painting's texture
    return m


def mode_filter(t, land):
    out = t.copy()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if not land[y, x]:
                continue
            win = t[y - 1:y + 2, x - 1:x + 2][land[y - 1:y + 2, x - 1:x + 2]]
            out[y, x] = np.bincount(win, minlength=3).argmax()
    return out


def in_poly(poly, x, y):
    inside, j = False, len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def distance_to(mask):
    d = np.full((H, W), 999, np.int32)
    q = deque()
    for y in range(H):
        for x in range(W):
            if mask[y, x]:
                d[y, x] = 0
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for ny, nx in neighbours(y, x):
            if d[ny, nx] > d[y, x] + 1:
                d[ny, nx] = d[y, x] + 1
                q.append((ny, nx))
    return d


def paint(m, t, ridge, light):
    s = scale()
    img = np.zeros((H, W, 3), np.uint8)
    land = m == LAND
    t = mode_filter(mode_filter(t, land), land)
    dsea = distance_to(m != SEA)
    dland = distance_to(m == SEA)
    snow = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            snow[y, x] = in_poly(SNOW_POLY, CROP_X0 + (x + 0.5) / s, (y + 0.5 - PAD_Y) / s) and light[y, x] > SNOW_LUM
    bright = light > np.percentile(light[land], 70)
    for y in range(H):
        for x in range(W):
            c = m[y, x]
            if c == SEA:
                d = dsea[y, x]
                img[y, x] = SEA_NEAR if d <= 3 else SEA_MID if d <= 11 else SEA_DEEP
                continue
            if c == INWATER:
                img[y, x] = WATER_IN
                continue
            if dland[y, x] == 1:
                img[y, x] = COAST_DARK
                continue
            if dland[y, x] == 2:
                img[y, x] = COAST_MID
                continue
            if snow[y, x]:
                base = SNOW_LIGHT if bright[y, x] else SNOW
                img[y, x] = ROCK if ridge[y, x] else base
            elif t[y, x] == T_KHAKI:
                img[y, x] = OLIVE if ridge[y, x] else KHAKI
            else:
                base = GRASS_LIGHT if t[y, x] == T_LIGHT else GRASS
                img[y, x] = COAST_MID if ridge[y, x] else base
    # snow meets grass: a grey rim, as the Sinnoh map rims its khaki with olive
    out = img.copy()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if snow[y, x] and m[y, x] == LAND and any(m[ny, nx] == LAND and not snow[ny, nx] for ny, nx in neighbours(y, x)):
                out[y, x] = ROCK
    vx, vy = to_screen(*VOLCANO_TIP)
    for dx, dy, col in ((0, 0, RED), (-1, 1, RED_DARK), (0, 1, RED_DARK), (1, 1, RED_DARK)):
        if m[vy + dy, vx + dx] == LAND:
            out[vy + dy, vx + dx] = col
    return out


def marker(d, x, y, kind):
    """Fill exactly the 8x8 cell the point falls in, like the Sinnoh map's squares: the in-game marker is one
    background tile and blinks over that cell, so a square that straddled two cells would show half outside it."""
    x0, y0 = x // 8 * 8, y // 8 * 8
    fill, dark, light = (RED, RED_DARK, RED_LIGHT) if kind == "fly" else (BLUE, BLUE_DARK, BLUE_LIGHT)
    d.rectangle([x0, y0, x0 + 7, y0 + 7], fill=OUTLINE)
    d.rectangle([x0 + 1, y0 + 1, x0 + 6, y0 + 6], fill=dark)     # dark rim on the bottom and right
    d.rectangle([x0 + 1, y0 + 1, x0 + 5, y0 + 5], fill=fill)
    d.rectangle([x0 + 1, y0 + 1, x0 + 2, y0 + 2], fill=light)    # light corner, top left


def main():
    ref = Image.open(sys.argv[1]).convert("RGB")
    outdir = sys.argv[2]
    m, t, ridge, light = downsample(*read_reference(ref))
    m = split_water(m)
    img = Image.fromarray(paint(m, t, ridge, light))
    img.save(os.path.join(outdir, "hisui-townmap-nomarkers.png"))
    d = ImageDraw.Draw(img)
    pts = []
    for num, name, rx, ry, kind in POINTS:
        x, y = to_screen(rx, ry)
        marker(d, x, y, kind)
        pts.append({"map": "37/%d" % num, "name": name, "kind": kind, "x": x, "y": y, "tile_x": x // 8, "tile_y": y // 8})
    img.save(os.path.join(outdir, "hisui-townmap.png"))
    json.dump(pts, open(os.path.join(outdir, "hisui-locations.json"), "w"), indent=1)
    big = img.resize((W * 4, H * 4), Image.NEAREST)
    bd = ImageDraw.Draw(big)
    try:
        font = ImageFont.truetype("arialbd.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    for p in pts:
        label = "%s  (%d,%d)" % (p["name"], p["x"], p["y"])
        tx, ty = p["x"] * 4 + 28, p["y"] * 4 - 12
        box = bd.textbbox((tx, ty), label, font=font)
        if box[2] > W * 4 - 4:
            tx = p["x"] * 4 - 28 - (box[2] - box[0])
            box = bd.textbbox((tx, ty), label, font=font)
        bd.rectangle([box[0] - 5, box[1] - 3, box[2] + 5, box[3] + 3], fill=(40, 40, 40))
        bd.text((tx, ty), label, fill=(255, 255, 255), font=font)
    big.save(os.path.join(outdir, "hisui-townmap-x4.png"))
    colours = len({tuple(c) for c in np.asarray(img).reshape(-1, 3)})
    print("wrote hisui-townmap.png (%dx%d, %d colours), hisui-townmap-x4.png, hisui-locations.json" % (W, H, colours))
    for p in pts:
        print("  %-20s %s  %-5s screen (%3d,%3d)  tile (%2d,%2d)" % (p["name"], p["map"], p["kind"], p["x"], p["y"], p["tile_x"], p["tile_y"]))


if __name__ == "__main__":
    main()
