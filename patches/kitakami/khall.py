"""Kitakami Hall's inside, drawn for Kitakami (2026-10-17; the user: "can u redesign the interior hall to match the
theme? or maybe something unique for this theme kitakami"). No room of the game is Japanese (the hack's "wooden"
rooms are a cave's tiles or Sinnoh's houses), so the Hall is new art, as the torii, the lanterns and the bridge in
the town are (kart.py), and its own tileset is made from the picture (cells, palettes, metatiles: build()).

  the back wall    dark wooden pillars, shoji paper between them, a teal-bordered scroll in the middle
  the stage        tatami, raised, the width of the hall: the three masks (Wellspring, Hearthflame, Cornerstone)
                   in glass cases on it, a paper lantern at each end; its wooden front has a gold plaque under each
                   mask (they are read: kpeople). From the morning the Loyal Three wake, the cases are smashed and
                   empty (ON_LOAD swaps those tiles: SWAPS)
  the floor        planks; a red carpet from the door to the stage; teal cushions (zabuton) in two rows a side for
                   the festival's audience; a standing paper lamp (andon) each side of the door
  the door         the mat at the bottom (behaviour 0x65: walk down to leave), dark wall either side

13 x 15 tiles. Every tile's picture is drawn here at the pixel; build() cuts it into the game's 8 x 8 cells (the
same cell flipped is one cell), packs the colours into palette rows 6-12 and makes the metatiles: one per kind of
tile, a bottom layer and a top layer (the lamps' heads are drawn over you).
"""
import struct

W, H = 13, 15
DOOR = (6, 14)
CASES = (3, 6, 9)                     # the masks' cases: x, rows 3 (the glass and the mask) and 4 (the pedestal)
PLAQUES = [(3, 6), (6, 6), (9, 6)]    # their plaques on the stage's front (read from the floor below)
MASK_NAMES = ("Wellspring", "Hearthflame", "Cornerstone")

# ---- the colours (multiples of 8: the GBA keeps 5 bits a channel)
C = {
    "out": (40, 24, 16), "wd1": (72, 44, 24), "wd2": (104, 64, 36), "wd3": (136, 88, 48), "wd4": (176, 120, 64),
    "fl1": (200, 152, 96), "fl2": (176, 128, 80), "fl3": (152, 104, 64), "fl4": (216, 176, 120),
    "pp1": (248, 240, 216), "pp2": (224, 208, 176), "pp3": (192, 176, 144),
    "tt1": (192, 192, 112), "tt2": (160, 160, 88), "tt3": (216, 216, 144), "tb1": (32, 64, 56), "tb2": (56, 96, 88),
    "rd1": (200, 40, 40), "rd2": (136, 24, 32), "rd3": (232, 96, 80),
    "gd1": (232, 192, 96), "gd2": (176, 136, 56), "gd3": (248, 232, 160),
    "tl1": (56, 168, 152), "tl2": (32, 112, 104), "tl3": (136, 216, 200),
    "bl1": (64, 112, 208), "bl2": (40, 72, 152), "bl3": (144, 184, 240),
    "or1": (240, 144, 48), "gy1": (160, 160, 152), "gy2": (104, 104, 96), "gy3": (208, 208, 200),
    "gl1": (216, 240, 248), "gl2": (168, 208, 224), "ink": (48, 40, 40), "glow": (248, 216, 128),
    "blk": (8, 8, 8),
}


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.px[y][x] = c

    def dot(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def hline(self, x0, x1, y, c): self.rect(x0, y, x1, y, c)
    def vline(self, x, y0, y1, c): self.rect(x, y0, x, y1, c)

    def outline(self, x0, y0, x1, y1, c="out"):
        """a dark line round what is drawn in the box (on its clear pixels)"""
        old = [row[:] for row in self.px]
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if old[y][x] is None and any(0 <= x + dx < self.w and 0 <= y + dy < self.h and
                                             x0 <= x + dx <= x1 and y0 <= y + dy <= y1 and old[y + dy][x + dx]
                                             for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    self.px[y][x] = c


def planks(cv, x0, y0, w, h):
    """the floor: boards running across, 8 px wide, joints staggered"""
    for y in range(y0, y0 + h):
        row = (y - y0) // 8
        for x in range(x0, x0 + w):
            c = "fl1" if row % 2 == 0 else "fl2"
            yy = (y - y0) % 8
            if yy == 7:
                c = "fl3"
            elif yy == 0:
                c = "fl4" if row % 2 == 0 else "fl1"
            joint = (x - x0 + (16 if row % 2 else 0)) % 32
            if joint == 0 and yy != 7:
                c = "fl3"
            cv.px[y][x] = c


def tatami(cv, x0, y0, w, h):
    """the stage's mats: straw, a dark teal cloth border, the weave in lines"""
    cv.rect(x0, y0, x0 + w - 1, y0 + h - 1, "tt1")
    for y in range(y0, y0 + h):
        if (y - y0) % 3 == 2:
            cv.hline(x0, x0 + w - 1, y, "tt2")
    for y in range(y0, y0 + h):
        if (y - y0) % 6 == 0:
            cv.hline(x0, x0 + w - 1, y, "tt3")
    for mx in range(x0, x0 + w, 32):                    # each mat 32 x 24, its border cloth
        cv.vline(mx, y0, y0 + h - 1, "tb1")
        cv.vline(mx + 1, y0, y0 + h - 1, "tb2")
    for my in range(y0, y0 + h, 24):
        cv.hline(x0, x0 + w - 1, my, "tb1")
        cv.hline(x0, x0 + w - 1, my + 1, "tb2")


def pillar(cv, x, y0, y1):
    """a square wooden post, 6 px, lit from the left"""
    cv.rect(x, y0, x + 5, y1, "wd2")
    cv.vline(x, y0, y1, "wd3")
    cv.vline(x + 1, y0, y1, "wd4")
    cv.vline(x + 5, y0, y1, "wd1")


def shoji(cv, x0, y0, x1, y1):
    """paper between a wooden frame, the lattice in squares"""
    cv.rect(x0, y0, x1, y1, "pp1")
    for y in range(y0, y1 + 1):
        if (y - y0) % 8 == 7:
            cv.hline(x0, x1, y, "wd2")
    for x in range(x0, x1 + 1):
        if (x - x0) % 8 == 7:
            cv.vline(x, y0, y1, "wd2")
    cv.hline(x0, x1, y1, "pp3")
    cv.rect(x0, y0, x1, y0, "wd1")


def mask(cv, cx, cy, kind):
    """one of Ogerpon's masks, 12 x 11, its middle at (cx, cy): Wellspring blue, Hearthflame red, Cornerstone stone"""
    a, b, c = {"Wellspring": ("bl1", "bl2", "bl3"), "Hearthflame": ("rd1", "rd2", "or1"),
               "Cornerstone": ("gy1", "gy2", "gy3")}[kind]
    x0, y0 = cx - 6, cy - 5
    face = ["..AAAAAAAA..", ".AACAAAACAA.", "AACCAAAACCAA", "AAAAAAAAAAAA", "AIIAAAAAAIIA", "AIIAAAAAAIIA",
            "AAAAABBAAAAA", ".AAAAAAAAAA.", ".ABBAAAABBA.", "..AABBBBAA..", "...AAAAAA..."]
    for y, row in enumerate(face):
        for x, ch in enumerate(row):
            if ch != ".":
                cv.dot(x0 + x, y0 + y, {"A": a, "B": b, "C": c, "I": "ink"}[ch])
    if kind == "Wellspring":                            # its fins / Hearthflame its horns / Cornerstone its crown
        for d in (-7, 6):
            cv.dot(cx + d, cy - 2, "bl3"); cv.dot(cx + d, cy - 1, "bl1"); cv.dot(cx + d, cy, "bl2")
    elif kind == "Hearthflame":
        for d in (-5, 4):
            cv.dot(cx + d, cy - 6, "or1"); cv.dot(cx + d + (1 if d > 0 else 0), cy - 7, "gd1")
    else:
        cv.hline(cx - 3, cx + 2, cy - 6, "gy3"); cv.dot(cx - 4, cy - 7, "gy1"); cv.dot(cx + 3, cy - 7, "gy1")


def case(cv, x, y, kind, broken=False):
    """a mask in a glass case on a red-lacquered pedestal: 16 x 32, its top-left at (x, y)"""
    cv.rect(x + 2, y + 18, x + 13, y + 29, "rd2")       # the pedestal
    cv.rect(x + 3, y + 18, x + 12, y + 28, "rd1")
    cv.vline(x + 3, y + 18, y + 28, "rd3")
    cv.hline(x + 1, x + 14, y + 17, "gd2")
    cv.hline(x + 1, x + 14, y + 16, "gd1")
    cv.hline(x + 2, x + 13, y + 30, "out")
    cv.rect(x + 6, y + 21, x + 9, y + 24, "gd1")        # a gold crest on its front
    cv.dot(x + 7, y + 22, "gd3")
    if not broken:
        cv.rect(x + 1, y + 1, x + 14, y + 15, "gl1")    # the glass, a frame of wood
        cv.rect(x + 2, y + 2, x + 13, y + 14, "gl2")
        for k in range(5):
            cv.dot(x + 3 + k, y + 3 + k, "gl1")
        mask(cv, x + 8, y + 8, kind)
        cv.rect(x + 1, y + 1, x + 14, y + 1, "wd2")
        cv.vline(x + 1, y + 1, y + 15, "wd2")
        cv.vline(x + 14, y + 1, y + 15, "wd2")
    else:
        cv.vline(x + 1, y + 6, y + 15, "wd2")          # the frame left, the glass gone: shards
        cv.vline(x + 14, y + 9, y + 15, "wd2")
        cv.rect(x + 1, y + 6, x + 3, y + 6, "wd2")
        for (sx, sy) in ((3, 12), (5, 14), (9, 13), (11, 15), (12, 11), (7, 15), (4, 9)):
            cv.dot(x + sx, y + sy, "gl1")
            cv.dot(x + sx + 1, y + sy, "gl2")
        cv.hline(x + 4, x + 11, y + 15, "gy2")          # the empty stand
    cv.outline(x, y, x + 15, y + 31)


def lantern(cv, x, y):
    """a paper lantern on a stand (the stage's ends), 16 x 32"""
    cv.rect(x + 3, y + 2, x + 12, y + 17, "rd1")
    cv.rect(x + 4, y + 4, x + 11, y + 15, "glow")
    cv.rect(x + 5, y + 5, x + 10, y + 14, "gd3")
    for yy in (y + 6, y + 10, y + 14):
        cv.hline(x + 3, x + 12, yy, "rd2")
    cv.rect(x + 2, y + 1, x + 13, y + 2, "out")
    cv.rect(x + 2, y + 17, x + 13, y + 18, "out")
    cv.rect(x + 7, y + 19, x + 8, y + 29, "wd2")
    cv.rect(x + 4, y + 29, x + 11, y + 30, "wd1")
    cv.outline(x, y, x + 15, y + 31)


def andon(cv, x, y):
    """a standing paper lamp by the door, 16 x 32: a paper box in a wooden frame on legs"""
    cv.rect(x + 3, y + 6, x + 12, y + 22, "wd1")
    cv.rect(x + 4, y + 7, x + 11, y + 21, "glow")
    cv.rect(x + 5, y + 9, x + 10, y + 19, "pp1")
    cv.hline(x + 4, x + 11, y + 14, "wd2")
    cv.rect(x + 2, y + 4, x + 13, y + 5, "wd2")
    cv.vline(x + 3, y + 23, y + 29, "wd1"); cv.vline(x + 12, y + 23, y + 29, "wd1")
    cv.outline(x, y, x + 15, y + 31)


def cushion(cv, x, y):
    """a teal zabuton, square, a tassel at each corner"""
    cv.rect(x + 2, y + 4, x + 13, y + 13, "tl2")
    cv.rect(x + 2, y + 3, x + 13, y + 11, "tl1")
    cv.rect(x + 4, y + 5, x + 10, y + 8, "tl3")
    for (tx, ty) in ((2, 3), (13, 3), (2, 13), (13, 13)):
        cv.dot(x + tx, y + ty, "gd1")
    cv.outline(x, y, x + 15, y + 15)


def scroll(cv, x0, y0, x1, y1):
    """the hanging scroll: teal mounting, paper, the legend's three crests and a line of brush writing"""
    cv.rect(x0, y0, x1, y1, "tl2")
    cv.rect(x0 + 2, y0 + 1, x1 - 2, y1 - 2, "tl1")
    cv.rect(x0 + 4, y0 + 3, x1 - 4, y1 - 4, "pp1")
    cv.rect(x0 - 1, y0, x1 + 1, y0 + 1, "wd1")         # the rods
    cv.rect(x0 - 1, y1 - 1, x1 + 1, y1, "wd1")
    mid = (x0 + x1) // 2
    for k, col in enumerate(("rd1", "or1", "bl1")):     # three crests: Okidogi, Munkidori, Fezandipiti
        cx = mid - 9 + 9 * k
        cv.rect(cx - 2, y0 + 7, cx + 2, y0 + 11, col)
        cv.dot(cx, y0 + 9, "pp1")
    for yy in range(y0 + 15, y1 - 6, 3):                 # the writing, in a column down the middle
        cv.hline(mid - 1, mid + 1, yy, "ink")
    cv.dot(mid, y1 - 6, "rd1")


def carpet(cv, x0, y0, x1, y1):
    cv.rect(x0, y0, x1, y1, "rd1")
    cv.vline(x0, y0, y1, "gd2"); cv.vline(x0 + 1, y0, y1, "gd1")
    cv.vline(x1, y0, y1, "gd2"); cv.vline(x1 - 1, y0, y1, "gd1")
    for y in range(y0, y1 + 1, 8):
        cv.dot((x0 + x1) // 2, y + 3, "rd3")
        cv.dot((x0 + x1) // 2 + 1, y + 4, "rd2")


def draw(broken=False):
    """(bottom layer, top layer) of the whole hall: rows of colour names (None: clear), 13 x 15 tiles"""
    pw, ph = W * 16, H * 16
    lo, hi = Canvas(pw, ph, "blk"), Canvas(pw, ph, None)
    # the floor, the carpet
    planks(lo, 16, 7 * 16, 11 * 16, 7 * 16)
    carpet(lo, 6 * 16 + 1, 7 * 16, 6 * 16 + 14, 14 * 16 - 1)
    # the back wall: the beam, pillars, shoji, the scroll
    lo.rect(0, 0, pw - 1, 47, "wd1")
    lo.rect(0, 0, pw - 1, 5, "wd2"); lo.hline(0, pw - 1, 1, "wd3"); lo.hline(0, pw - 1, 5, "gd2")
    lo.hline(0, pw - 1, 6, "out")
    for (a, b) in ((22, 74), (122, 186 - 2)):
        shoji(lo, a, 10, b, 43)
    scroll(lo, 82, 8, 126, 46)
    for x in (16, 76, 128, 186):
        pillar(lo, x, 7, 47)
    lo.hline(0, pw - 1, 47, "out")
    # the side walls (the hall's dark wood, a pillar at the edge of the floor)
    for x0 in (0, 12 * 16):
        lo.rect(x0, 48, x0 + 15, ph - 1, "wd1")
        for y in range(48, ph, 16):
            lo.hline(x0, x0 + 15, y, "wd2")
        pillar(lo, x0 + (10 if x0 == 0 else 0), 48, ph - 17)
    # the stage: tatami, its wooden front, the plaques
    tatami(lo, 16, 48, 11 * 16, 48)
    lo.rect(16, 96, 12 * 16 - 1, 111, "wd2")
    lo.hline(16, 12 * 16 - 1, 96, "gd1"); lo.hline(16, 12 * 16 - 1, 97, "gd2")
    lo.hline(16, 12 * 16 - 1, 111, "out")
    for x in range(16, 12 * 16, 16):
        lo.vline(x, 98, 110, "wd1")
    for (px, py) in PLAQUES:
        lo.rect(px * 16 + 4, 100, px * 16 + 11, 106, "gd1")
        lo.rect(px * 16 + 5, 101, px * 16 + 10, 105, "gd2")
        lo.hline(px * 16 + 6, px * 16 + 9, 103, "gd3")
    # on the stage: the cases, the lanterns
    for x, kind in zip(CASES, MASK_NAMES):
        sub = Canvas(16, 32, None)
        case(sub, 0, 0, kind, broken)
        for y in range(32):
            for xx in range(16):
                if sub.px[y][xx]:
                    lo.px[48 + y][x * 16 + xx] = sub.px[y][xx]
    for x in (1, 11):
        sub = Canvas(16, 32, None)
        lantern(sub, 0, 0)
        for y in range(32):
            for xx in range(16):
                if sub.px[y][xx]:
                    lo.px[48 + y][x * 16 + xx] = sub.px[y][xx]
    # the cushions, the lamps by the door (their heads over you)
    for y in (9, 11):
        for x in (2, 3, 4, 8, 9, 10):
            sub = Canvas(16, 16, None)
            cushion(sub, 0, 0)
            for yy in range(16):
                for xx in range(16):
                    if sub.px[yy][xx]:
                        lo.px[y * 16 + yy][x * 16 + xx] = sub.px[yy][xx]
    for x in (1, 11):
        sub = Canvas(16, 32, None)
        andon(sub, 0, 0)
        for yy in range(32):
            for xx in range(16):
                if sub.px[yy][xx]:
                    (hi if yy < 16 else lo).px[12 * 16 - 16 + yy][x * 16 + xx] = sub.px[yy][xx]
    # the front wall and the door
    lo.rect(0, 14 * 16, pw - 1, ph - 1, "wd1")
    lo.hline(0, pw - 1, 14 * 16, "out")
    lo.hline(0, pw - 1, 14 * 16 + 1, "wd3")
    mx = DOOR[0] * 16
    lo.rect(mx, 14 * 16, mx + 15, ph - 1, "rd2")
    lo.rect(mx + 2, 14 * 16 + 2, mx + 13, ph - 3, "rd1")
    lo.rect(mx + 4, 14 * 16 + 5, mx + 11, ph - 6, "gd1")
    lo.rect(mx + 5, 14 * 16 + 6, mx + 10, ph - 7, "rd1")
    return lo.px, hi.px


# what you can walk on: 0 yes, 1 no (the walls, the stage, its front, the cushions, the lamps' feet)
def collision():
    out = [[1] * W for _ in range(H)]
    for y in range(7, 14):
        for x in range(1, 12):
            out[y][x] = 0
    for y in (9, 11):
        for x in (2, 3, 4, 8, 9, 10):
            out[y][x] = 1
    for x in (1, 11):
        out[12][x] = 1
    out[DOOR[1]][DOOR[0]] = 0
    return out


BEH_DOOR = 0x65                       # the mat: walk down to leave (as the old Hall's)
NORMAL, COVERED = 0x0000, 0x1000      # layer types: the top layer drawn over people / both layers under them
FIRST_CELL = 512                      # a secondary set's cells are numbered from 512
MAX_CELLS = 504                       # (the last 8 of the sheet: where the game draws an opening door)
ROWS = range(6, 13)                   # the secondary set's palette rows
ELEVATION = 3


class Built:
    pass


def _quarters(pic, x0, y0):
    """the four 8 x 8 cells of the 16 x 16 tile at (x0, y0), as rows of colour names"""
    return [[row[x0 + 8 * (q % 2):x0 + 8 * (q % 2) + 8] for row in pic[y0 + 8 * (q // 2):y0 + 8 * (q // 2) + 8]]
            for q in range(4)]


def build():
    """The hall as the game has it: the secondary tileset's cells (4bpp), palettes (16 rows), metatiles and attributes,
    the map's blocks, and the case tiles' smashed versions [(x, y, block)]. Asserts the cells and colours fit."""
    lo, hi = draw()
    lo_b, hi_b = draw(broken=True)
    coll = collision()
    tiles = {}                                          # (bottom cells, top cells, attribute) -> metatile index
    order = []

    def tile_of(lo_, hi_, x, y):
        bot = _quarters(lo_, 16 * x, 16 * y)
        top = _quarters(hi_, 16 * x, 16 * y)
        has_top = any(c for q in top for row in q for c in row)
        beh = BEH_DOOR if (x, y) == DOOR else 0
        key = (tuple(tuple(map(tuple, q)) for q in bot), tuple(tuple(map(tuple, q)) for q in top),
               (NORMAL if has_top else COVERED) | beh)
        if key not in tiles:
            tiles[key] = len(order)
            order.append(key)
        return tiles[key]

    grid = [[tile_of(lo, hi, x, y) for x in range(W)] for y in range(H)]
    swaps = [(x, y, tile_of(lo_b, hi_b, x, y)) for x in CASES for y in (3, 4)]
    black = [["blk"] * 16 for _ in range(16)]           # what the game draws past the walls (the map's border)
    black_tile = tile_of(black, [[None] * 16 for _ in range(16)], 0, 0)
    # the palettes: every cell's colours in one row of 15 (colour 0 is clear)
    sets = []
    for bot, top, attr in order:
        for q in bot + top:
            s = frozenset(c for row in q for c in row if c)
            if s and s not in sets:
                sets.append(s)
    rows = []
    for s in sorted(sets, key=len, reverse=True):
        fits = [r for r in rows if len(r | s) <= 15]
        if not any(s <= r for r in rows):
            if fits:
                best = max(fits, key=lambda r: len(r & s))
                best |= s
            else:
                rows.append(set(s))
    assert len(rows) <= len(ROWS), "the hall needs %d palette rows; a secondary set has %d" % (len(rows), len(ROWS))
    row_of = {}
    pals = [[0] * 16 for _ in range(16)]
    for k, r in enumerate(rows):
        for i, c in enumerate(sorted(r)):
            rgb = C[c]
            pals[ROWS[0] + k][i + 1] = (rgb[0] >> 3) | (rgb[1] >> 3) << 5 | (rgb[2] >> 3) << 10
    index = {}                                          # (row, colour) -> index in that row

    def place(s):
        k = next(k for k, r in enumerate(rows) if s <= r)
        return k

    for k, r in enumerate(rows):
        for i, c in enumerate(sorted(r)):
            index[k, c] = i + 1
    cells, cell_of = [bytes(32)], {bytes(32): (0, False, False)}     # cell 0: clear

    def cell(q):
        s = frozenset(c for row in q for c in row if c)
        if not s:
            return 0, 0, False, False
        k = place(s)
        px = [[index[k, c] if c else 0 for c in row] for row in q]
        variants = [(px, False, False), ([r[::-1] for r in px], True, False), (px[::-1], False, True),
                    ([r[::-1] for r in px[::-1]], True, True)]
        for p, hf, vf in variants:
            raw = bytes((p[y][2 * i] | p[y][2 * i + 1] << 4) for y in range(8) for i in range(4))
            if raw in cell_of:
                n, f1, f2 = cell_of[raw]
                return k, n, hf != f1, vf != f2
        raw = bytes((px[y][2 * i] | px[y][2 * i + 1] << 4) for y in range(8) for i in range(4))
        cell_of[raw] = (len(cells), False, False)
        cells.append(raw)
        return k, len(cells) - 1, False, False

    metas, attrs = [], []
    for bot, top, attr in order:
        for q in bot + top:
            k, n, hf, vf = cell(q)
            metas.append((FIRST_CELL + n) | hf << 10 | vf << 11 | (ROWS[0] + k) << 12)
        attrs.append(attr)
    assert len(cells) <= MAX_CELLS, "the hall needs %d cells; there is room for %d" % (len(cells), MAX_CELLS)
    assert len(order) <= 512
    b = Built()
    b.cells = b"".join(cells)
    b.pals, b.metatiles = pals, struct.pack("<%dH" % len(metas), *metas)
    b.attrs = attrs + [0] * (512 - len(attrs))
    b.blocks = [[(512 + grid[y][x]) | coll[y][x] << 10 | ELEVATION << 12 for x in range(W)] for y in range(H)]
    b.swaps = [(x, y, (512 + t) | coll[y][x] << 10 | ELEVATION << 12) for (x, y, t) in swaps]
    b.border = [(512 + black_tile) | 1 << 10] * 4
    b.counts = (len(order), len(cells), len(rows))
    return b


def install(blob, built):
    """the hall's tileset into blob -> its key (as tileset.install: compressed cells, palettes, metatiles,
    attributes, then its 24 bytes)"""
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "paldea"))
    import tiles as PT
    pt = blob.put(("khall", "cells"), PT.lz_comp(built.cells))
    pp = blob.put(("khall", "palettes"), struct.pack("<256H", *[c for row in built.pals for c in row]))
    pm = blob.put(("khall", "metatiles"), built.metatiles)
    pa = blob.put(("khall", "attributes"), struct.pack("<512H", *built.attrs))
    blob.put(("tileset", "khall"), struct.pack("<BBHIIIII", 1, 1, 0, pt, pp, pm, pa, 0))
    return ("tileset", "khall")


def preview(path, scale=3, people=()):
    """the hall as a picture (people: [(x, y, RGBA array)] drawn standing on their tiles)"""
    from PIL import Image
    lo, hi = draw()
    im = Image.new("RGB", (W * 16, H * 16))
    for y in range(H * 16):
        for x in range(W * 16):
            im.putpixel((x, y), C[lo[y][x]])
    import numpy as np
    for (tx, ty, arr) in people:
        sp = Image.fromarray(arr)
        im.paste(sp, (tx * 16 + 8 - sp.width // 2, ty * 16 + 16 - sp.height), sp)
    for y in range(H * 16):
        for x in range(W * 16):
            if hi[y][x]:
                im.putpixel((x, y), C[hi[y][x]])
    im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)


if __name__ == "__main__":
    import sys
    preview(sys.argv[1] if len(sys.argv) > 1 else "hall.png")
