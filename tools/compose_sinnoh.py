"""Stitch the hack's Sinnoh into one image.

Sinnoh's overworld is two connection-clusters (the game links them through indoor maps, which carry no
connection data): the west around Twinleaf/Jubilife/Canalave, and the centre-east around Oreburgh/Eterna/
Veilstone/Sunyshore. Each cluster is placed exactly by its own connection offsets; the two are joined at the
one place the story crosses, Route 203 east of Jubilife into Oreburgh (through Oreburgh Gate), with the gate's
width as the only hand-picked number.

usage: python compose_sinnoh.py <out.png> [--scale 16|8] [--labels]
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_world as R

# (seed map, offset in metatiles). The west and east clusters are joined exactly: Route 203's warp into
# Oreburgh Gate sits at its local (56,11), the gate runs from its own (2,15) to (25,16), and comes out in
# Oreburgh City at (5,8) - so Oreburgh's origin is Route 203's origin + (74,4). The northern cluster reaches
# the rest only through Mt. Coronet's floors, which carry no usable surface offset, so it is placed by
# geography: Route 216's east end just north of Route 211's north end.
CLUSTERS = [((36, 0), (0, 0)), ((36, 3), (236, -70)), ((36, 12), (430, -267))]

DIGITS = {0xA1 + i: str(i) for i in range(10)}


def secname(i):
    p = R.ptr(0x5A147C + 8 * i + 4)
    out = ""
    for c in R.rom[p:p + 24]:
        if c == 0xFF: break
        if 0xBB <= c <= 0xD4: out += chr(65 + c - 0xBB)
        elif 0xD5 <= c <= 0xEE: out += chr(97 + c - 0xD5)
        elif c in DIGITS: out += DIGITS[c]
        elif c == 0x00: out += " "
        elif c == 0xAD: out += "."
        elif c == 0xB4: out += "'"
        else: out += "?"
    return out.strip()


def main():
    out = sys.argv[1]
    scale = int(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 16
    want_labels = "--labels" in sys.argv

    parts = []
    for seed, (dx, dy) in CLUSTERS:
        placed = R.walk(seed)
        xs = [x for x, y, L in placed.values()]; ys = [y for x, y, L in placed.values()]
        ox, oy = min(xs), min(ys)
        for (g, n), (x, y, L) in placed.items():
            parts.append((g, n, x - ox + dx, y - oy + dy, L))
        print("cluster %d/%d: %d maps" % (seed[0], seed[1], len(placed)))

    x0 = min(p[2] for p in parts); y0 = min(p[3] for p in parts)
    W = max(p[2] + p[4].w for p in parts) - x0
    H = max(p[3] + p[4].h for p in parts) - y0
    print("world %d x %d metatiles -> %d x %d px" % (W, H, W * scale, H * scale))

    canvas = np.zeros((H * scale, W * scale, 3), np.uint8)
    for i, (g, n, x, y, L) in enumerate(sorted(parts, key=lambda p: (p[3], p[2]))):
        img = L.render()
        if scale != 16:
            img = np.asarray(Image.fromarray(img).resize((L.w * scale, L.h * scale), Image.LANCZOS))
        py, px = (y - y0) * scale, (x - x0) * scale
        canvas[py:py + img.shape[0], px:px + img.shape[1]] = img
        print("  %2d/%-3d %-22s" % (g, n, secname(R.u8(R.header(g, n) + 20))), flush=True)

    im = Image.fromarray(canvas)
    del canvas
    im.save(out)
    print("wrote %s (%d x %d)" % (out, im.width, im.height))

    if want_labels:
        lab = im.copy()
        d = ImageDraw.Draw(lab)
        try:
            font = ImageFont.truetype("arialbd.ttf", max(16, scale * 3))
            font_small = ImageFont.truetype("arial.ttf", max(12, scale * 2))
        except Exception:
            font = font_small = ImageFont.load_default()
        for g, n, x, y, L in parts:
            name = secname(R.u8(R.header(g, n) + 20))
            if not name: continue
            f = font_small if name.startswith("Route") else font
            cx = ((x - x0) + L.w / 2) * scale
            cy = ((y - y0) + L.h / 2) * scale
            box = d.textbbox((cx, cy), name, font=f, anchor="mm")
            d.rectangle([box[0] - 6, box[1] - 4, box[2] + 6, box[3] + 4], fill=(0, 0, 0))
            d.text((cx, cy), name, font=f, fill=(255, 255, 255), anchor="mm")
        p = out.replace(".png", "-labelled.png")
        lab.save(p)
        print("wrote %s" % p)


if __name__ == "__main__":
    main()
