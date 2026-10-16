"""Labelled pictures of Area Zero's maps, with the tile numbers along their edges:
python -I map_guide.py <rom built by paldea_patch.py> <outdir> [placements.txt]

Each map is drawn from the built ROM (its own blocks, its tinted tilesets, everything that stands on it, hidden
things too); the names come from places.py (the same positions the ROM was built with: name the same placements
file) and from world.py's marks for doors and mouths. Gold: there during the story; cyan: after it; green: a way
in or out. x runs along the top and bottom edges, y down the sides: the numbers placements.txt wants."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont

GOLD, CYAN, GREEN = (255, 225, 60), (110, 220, 255), (120, 255, 140)
try:
    FONT = ImageFont.truetype("arialbd.ttf", 20); TITLE = ImageFont.truetype("arialbd.ttf", 30)
    SMALL = ImageFont.truetype("arialbd.ttf", 12)
except OSError:
    FONT = TITLE = SMALL = ImageFont.load_default()
S = 2                                             # picture pixels per game pixel
EDGE = 26                                         # the rulers' width


class Rom:
    """What the pictures need from a built ROM."""

    def __init__(self, path):
        os.environ["HE_ROM"] = path
        import importlib
        import render_world as R
        import mons as MN
        self.R = R = importlib.reload(R)                      # it reads its ROM (HE_ROM) when it is loaded
        R.Layout.cache.clear()
        self.rom = open(path, "rb").read()
        self.pals = MN.palettes(self.rom)                     # by tag, from the palette table the ROM's code uses

    def u16(self, o): return struct.unpack_from("<H", self.rom, o)[0]
    def u32(self, o): return struct.unpack_from("<I", self.rom, o)[0]

    def ground(self, g, n):
        """The map without anything on it: RGB array."""
        R = self.R
        return R.Layout(R.ptr(R.header(g, n))).render()

    def atlas(self, g, n, ids):
        """The metatiles in `ids` as the map's own tilesets draw them, for the editor's painting: RGBA, 512 x 512,
        metatile i at column i % 32, row i // 32, 16 pixels each; what is not asked for is left clear."""
        R = self.R
        lay = R.Layout(R.ptr(R.header(g, n)))
        out = np.zeros((512, 512, 4), np.uint8)
        for mid in ids:
            y, x = (mid // 32) * 16, (mid % 32) * 16
            out[y:y + 16, x:x + 16, :3] = lay.metatile(mid)
            out[y:y + 16, x:x + 16, 3] = 255
        return out

    def sprite(self, gfx, ext):
        """Frame 0 of an object's picture, RGBA, from the main sprite table or the hack's own (gfx 0x4E + ext)."""
        info = (self.u32(0x014A2C10) - 0x08000000 + 0x24 * ext) if gfx == 0x4E \
            else self.u32(0x00505620 + 4 * gfx) - 0x08000000
        tag = self.u16(info + 2)
        w, h = struct.unpack_from("<hh", self.rom, info + 8)
        fp = self.u32(self.u32(info + 0x1C) - 0x08000000) - 0x08000000
        px = np.zeros((h, w, 4), np.uint8)
        pal = self.pals.get(tag)
        for t in range((w // 8) * (h // 8)):
            tx, ty = t % (w // 8), t // (w // 8)
            for yy in range(8):
                for xx in range(8):
                    b = self.rom[fp + t * 32 + yy * 4 + xx // 2]
                    c = (b >> 4) if xx & 1 else (b & 15)
                    if c and pal:
                        v = pal[c]
                        px[ty * 8 + yy, tx * 8 + xx] = ((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8, 255)
        return px

    def objects(self, g, n):
        """(x, y, gfx, ext) of every person or thing the map places (hidden ones too)."""
        ev = self.u32(self.R.header(g, n) + 4) - 0x08000000
        cnt, po = self.rom[ev], self.u32(ev + 4) - 0x08000000
        return [(struct.unpack_from("<h", self.rom, po + 24 * i + 4)[0],
                 struct.unpack_from("<h", self.rom, po + 24 * i + 6)[0],
                 self.rom[po + 24 * i + 1], self.rom[po + 24 * i + 3]) for i in range(cnt)]


KEYS = ("wall", "past", "future", "station1", "station2", "cavern", "icecave", "lab", "station3", "station4",
        "shrine", "underdepths", "vault")         # in the order paldea_patch.py numbers them


def numbers():
    import paldea_patch as P
    num = {k: (P.GROUP, P.GROUP_COUNT + i) for i, k in enumerate(KEYS)}
    num["mossdeep"] = P.MOSSDEEP
    return num


def plan(placements=None):
    """map key -> [(x, y, label, colour)]: what places.py puts there (the crystals are drawn, not named)."""
    import places as PL
    at = PL.load(placements)
    names = {("past", "legend"): "Koraidon", ("future", "legend"): "Miraidon",
             ("past", "titan"): "Titan: Great Tusk", ("future", "titan"): "Titan: Iron Treads",
             ("station1", "resident"): "Penny", ("station2", "resident"): "Arven (after the ending)",
             ("station3", "resident"): "Nemona (after the ending)", ("station4", "resident"): "Jacq (after the ending)"}
    labels = {k: [] for k in KEYS + ("mossdeep",)}
    for tid, sec, name, kind, when, default, note in PL.THINGS:
        if isinstance(default, list):
            continue
        for mkey in PL.MAPS_OF[sec]:
            # ("after" is not said in the Sealed Vault: nothing there is to be had before, and its niches are close)
            text = names.get((mkey, tid), name) + (" (after)" if when == "after" and sec != "vault" else "")
            if when in ("ending", "finale"):                  # there for that scene only, and gone after it
                text = "%s (only in the %s)" % (text.replace("ending: ", ""), when)
            labels[mkey].append((at[tid][0], at[tid][1], text, CYAN if when == "after" else GOLD))
    return labels


def terrain(rom_path):
    """Doors and mouths, from world.py's own marks: map key -> [(x, y, label, colour)]."""
    import paldea_patch as P
    import world as W
    rom = bytearray(open(rom_path, "rb").read())              # a built ROM: the pieces world.py copies from are
    _, wm = W.wall(P.blocks_of(rom, P.CLIFF_LAYOUT))          # as they are in the game
    _, cm = W.crater(P.blocks_of(rom, P.CHASM_LAYOUT), P.blocks_of(rom, P.PETAL_LAYOUT))
    one = lambda k: cm[k][0]
    crater = [(*one("mouth"), "up to the wall", GREEN), (*one("L"), "the Zero Lab's door", GREEN),
              (*one("door2"), "Station No. 2", GREEN), (*one("door3"), "Station No. 3", GREEN),
              (*one("door4"), "Station No. 4 (climb the waterfall)", GREEN), (*one("cave"), "the Crystal Cavern", GREEN)]
    station = [(9, 8, "the way out", GREEN), (*P.STATION_COT[1], "a cot: rest", GOLD), (5, 1, "the game's PC", GOLD)]
    return {
        "mossdeep": [(66, 32, "stairs up", GREEN), (69, 32, "the game's item ball", GREEN)],
        "wall": [(*wm["hole"], "the hole back", GOLD), (*wm["arrive"], "you land here", GOLD),
                 (*wm["down"], "down into the crater", GREEN), (*wm["station"], "Station No. 1: Penny", GREEN),
                 (*wm["ice"], "the icy cave", GREEN)],
        "past": crater, "future": crater,
        "station1": station, "station2": station, "station3": station, "station4": station,
        "cavern": [(3, 1, "the way out", GREEN), (*P.CAVERN_LADDER, "down to the Underdepths (after)", CYAN),
                   (*P.CAVERN_MOUTH2, "into the Sealed Vault (after)", CYAN)],
        "vault": [(*W.VAULT_DOOR, "the way out", GREEN)],
        "icecave": [(6, 8, "the way out", GREEN)],
        "lab": [(7, 14, "the way out", GREEN), (*P.LAB_MACHINE_XY, "the machine: the finale", GOLD),
                (*P.LAB_SHOP_XY, "Booster Energy shop", GOLD)],
        "shrine": [(8, 12, "the way out (there is no way in any more)", GREEN)],
        "underdepths": [(12, 21, "the way out", GREEN)],
    }


TITLES = {"mossdeep": "Mossdeep City, after Team Rainbow Rocket", "wall": "Area Zero, the wall",
          "past": "Area Zero, the crater in the past", "future": "Area Zero, the crater in the future",
          "station1": "Research Station No. 1", "station2": "Research Station No. 2",
          "station3": "Research Station No. 3", "station4": "Research Station No. 4",
          "cavern": "The Crystal Cavern", "icecave": "The icy cave", "lab": "The Zero Lab",
          "shrine": "The old Sealed Shrine, empty", "underdepths": "The Underdepths",
          "vault": "The Sealed Vault"}
ORDER = ("mossdeep", "wall", "past", "future", "station1", "station2", "station3", "station4", "cavern", "vault",
         "icecave", "lab", "underdepths")         # (the old shrine is not drawn: nothing leads to it)


def with_objects(rom, g, n, skip=(59, 82), faded=()):
    """The map with everything that stands on it. faded: tiles whose people are there for a scene only (the
    ending, the finale): drawn see-through, so the picture does not say they stand in the way."""
    base = rom.ground(g, n).copy()
    for x, y, gfx, ext in rom.objects(g, n):
        if gfx in skip:                                       # item balls and the like: left out
            continue
        spr = rom.sprite(gfx, ext)
        sh, sw = spr.shape[:2]
        ox, oy = x * 16 + 8 - sw // 2, y * 16 + 16 - sh
        a = 0.45 if (x, y) in faded else 1.0
        for yy in range(sh):
            for xx in range(sw):
                if spr[yy, xx, 3] and 0 <= oy + yy < base.shape[0] and 0 <= ox + xx < base.shape[1]:
                    base[oy + yy, ox + xx] = (a * spr[yy, xx, :3] + (1 - a) * base[oy + yy, ox + xx]).astype(base.dtype)
    return base


def ruled(img, w, h, x0=0, y0=0, s=S):
    """The picture with a faint tile grid on it and the tile numbers round it (x0, y0: the map's tile at the
    picture's top left corner; s: picture pixels a game pixel)."""
    T = 16 * s
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for x in range(w + 1):
        d.line([(x * T, 0), (x * T, img.height)], fill=(255, 255, 255, 70 if (x + x0) % 5 == 0 else 26))
    for y in range(h + 1):
        d.line([(0, y * T), (img.width, y * T)], fill=(255, 255, 255, 70 if (y + y0) % 5 == 0 else 26))
    img = Image.alpha_composite(img.convert("RGBA"), over).convert("RGB")
    page = Image.new("RGB", (img.width + 2 * EDGE, img.height + 2 * EDGE), (18, 18, 28))
    page.paste(img, (EDGE, EDGE))
    d = ImageDraw.Draw(page)
    for x in range(w):
        t = str(x + x0)
        tw = d.textlength(t, font=SMALL)
        col = (255, 255, 255) if (x + x0) % 5 == 0 else (150, 150, 165)
        for yy in (6, EDGE + img.height + 6):
            d.text((EDGE + x * T + (T - tw) / 2, yy), t, fill=col, font=SMALL)
    for y in range(h):
        t = str(y + y0)
        tw = d.textlength(t, font=SMALL)
        col = (255, 255, 255) if (y + y0) % 5 == 0 else (150, 150, 165)
        for xx in (EDGE - tw - 4, EDGE + img.width + 4):
            d.text((xx, EDGE + y * T + (T - 13) / 2), t, fill=col, font=SMALL)
    return page


def draw(rom, g, n, title, labels, window=None, s=S, faded=()):
    """window: (x0, y0, x1, y1), the part of the map to draw (all of it when None); s: picture pixels a game
    pixel; faded: tiles of people there for a scene only (with_objects)."""
    base = with_objects(rom, g, n, faded=faded)
    h, w = base.shape[0] // 16, base.shape[1] // 16
    x0, y0, x1, y1 = window or (0, 0, w, h)
    size = "%d x %d tiles" % (w, h) if window is None else "x %d-%d, y %d-%d" % (x0, x1 - 1, y0, y1 - 1)
    base = base[y0 * 16:y1 * 16, x0 * 16:x1 * 16]
    labels = [(x, y, text, col) for x, y, text, col in labels if x0 <= x < x1 and y0 <= y < y1]
    img = Image.fromarray(base)
    img = ruled(img.resize((img.width * s, img.height * s), Image.NEAREST), x1 - x0, y1 - y0, x0, y0, s)
    pad = max(0, (1100 - img.width) // 2)
    top = 50
    page = Image.new("RGB", (img.width + 2 * pad, img.height + top), (18, 18, 28))
    page.paste(img, (pad, top))
    d = ImageDraw.Draw(page)
    d.text((10, 8), "%s   (%s)" % (title, size), fill=(255, 255, 255), font=TITLE)
    taken = []
    centre = lambda x, y: (((x - x0) * 16 + 8) * s + pad + EDGE, ((y - y0) * 16 + 8) * s + top + EDGE)
    rings = [centre(x, y) for x, y, text, col in labels]
    for x, y, text, col in labels:
        cx, cy = centre(x, y)
        for r in (15, 17):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
        text = "%s  %d,%d" % (text, x, y)
        tw = d.textlength(text, font=FONT)
        # the name goes to the right of its ring, else to the left, else under or over it, else a line lower or
        # higher on either side: the first place that stays on the page and runs across no other ring or name
        def bad(tx, ty):
            if tx < 0 or tx + tw > page.width or ty < top - 20:
                return 1000
            rung = sum(1 for ox, oy in rings if (ox, oy) != (cx, cy)
                       and tx < ox + 17 and ox - 17 < tx + tw and ty < oy + 17 and oy - 17 < ty + 24)
            named = sum(1 for ox, oy, ow in taken if abs(ty - oy) < 22 and tx < ox + ow and ox < tx + tw)
            return rung + named
        tries = [(cx + 22, cy - 12), (cx - 22 - tw, cy - 12), (cx - tw / 2, cy + 19), (cx - tw / 2, cy - 43)]
        tries += [(sx, cy - 12 + dy) for dy in (22, -22, 44, -44, 66, -66, 88, -88)
                  for sx in (cx + 22, cx - 22 - tw)]
        tx, ty = min(tries, key=lambda t: (bad(*t), tries.index(t)))
        taken.append((tx, ty, tw))
        if abs(ty - (cy - 12)) > 30:                         # far from its ring: a line back to it
            ex = tx if tx > cx else tx + tw
            d.line([(cx, cy), (ex, ty + 12)], fill=col, width=2)
        d.text((tx, ty), text, fill=col, font=FONT, stroke_width=3, stroke_fill=(0, 0, 0))
    return page


def main(rom_path, out, placements=None):
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".png"):
            os.remove(os.path.join(out, f))
    rom = Rom(rom_path)
    num, labels, land = numbers(), plan(placements), terrain(rom_path)
    import places as PL
    at = PL.load(placements)
    faded = {}                                            # map key -> tiles of people there for a scene only
    for tid, sec, name, kind, when, default, note in PL.THINGS:
        if when in ("ending", "finale"):
            for mkey in PL.MAPS_OF[sec]:
                faded.setdefault(mkey, set()).add(tuple(at[tid]))
    made = []
    for k, key in enumerate(ORDER):
        g, n = num[key]
        title = TITLES[key] if key == "mossdeep" else "%s (%d/%d)" % (TITLES[key], g, n)
        window, s = None, S
        if key == "mossdeep":
            # the city is big and ours is one corner of it: that corner, closer up, round wherever they stand
            h, w = (v // 16 for v in rom.ground(g, n).shape[:2])
            xs, ys = [l[0] for l in labels[key]], [l[1] for l in labels[key]]
            window = (max(0, min(xs) - 8), max(0, min(ys) - 5), min(w, max(xs) + 9), min(h, max(ys) + 6))
            s = 3 if (window[2] - window[0]) * 48 <= 1600 else S
        p = draw(rom, g, n, title, land.get(key, []) + labels[key], window, s, faded.get(key, ()))
        name = os.path.join(out, "%02d %s.png" % (k + 1, TITLES[key]))
        p.save(name)
        made.append(name)
    return made


if __name__ == "__main__":
    for name in main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None):
        print(name)
