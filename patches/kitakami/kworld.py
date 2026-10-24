"""Kitakami's outdoor map: Mossui Town, the whole of Kitakami here.

Drawn as Area Zero's are: a sketch painted with the General set's pieces by patches/paldea/world.py (grass, trees,
ponds, dirt, terraces with steps), then the buildings stamped in from the Bellchime / Lavaridge set (Kitakami's
own copy: tileset.py). The designs are the ones the user approved on 2026-10-14 (mock-ups and the scripts that drew
them: rom/unreleased/kitakami/): Mossui laid out like Ecruteak City (SoulGold), cut down to what is used
(revision 5, 2026-10-15), then set in a valley of red maples with a torii at its hall and its shrine (revision 6,
2026-10-15): see mossui(). The Kitakami Road and Oni Mountain went on 2026-10-16 (the user: "remove road and
remove oni mountain, keep only town"); what the story had on them is in the town now (revision 7), but for the
Dreaded Den, which went too (the user: "the den is unneccesary").

A design returns (blocks, overlay, marks): blocks as the game stores them (metatile | collision << 10 | height
<< 12) with the base set's numbers; the overlay names the tiles that are pieces of ours (the market's, the
lanterns, the drawn pieces), which finish() turns into our numbers once tileset.build() has given them out, with the
homes' longhouse pieces moved to the homes' slate-grey copies. Marks: named places (doors, people), x, y.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "paldea"))
import world as W                                       # paint(), Sketch, stamp(), crop(), blk()
sys.path.insert(0, HERE)
import kart                                             # the torii, the stone lantern, the bridge

MAP_GROUPS = 0x00A54698


def b(mt, coll=1, elev=3): return W.blk(mt, coll, elev)
def rowv(ids, coll=1): return [b(m, coll) for m in ids]


def source(rom, g, n):
    """the blocks of an existing map"""
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    hdr = u32(u32(MAP_GROUPS + 4 * g) - 0x08000000 + 4 * n) - 0x08000000
    lay = u32(hdr) - 0x08000000
    w, h, data = u32(lay), u32(lay + 4), u32(lay + 12) - 0x08000000
    return [list(struct.unpack_from("<%dH" % w, rom, data + 2 * w * y)) for y in range(h)]


# ---- pieces of the Bellchime / Lavaridge set (numbers read off 35/74 and 0/12)
A_ROW = [734, 735, 845, 756, 757]                       # a floor of the pagoda: its eave
B_ROW = [742, 743, 837, 710, 711]                       # ... its wall
BASE1 = [750, 751, 845, 718, 719]
BASE2 = [758, 759, 853, 726, 727]                       # the door: 853
CAP = [824, 825, 825, 825, 828]                         # the top: a longhouse's ridge (stands in for new art)
LONGHOUSE = {824, 825, 828, 832, 833, 836, 840, 841, 844, 848, 849, 850, 851, 852, 871, 879, 887, 895}
SIGN = 27                                               # (General) a wooden notice board


def pagoda(floors=2):
    rows = [rowv(CAP)] + [rowv(r) for _ in range(floors) for r in (A_ROW, B_ROW)] + [rowv(BASE1), rowv(BASE2)]
    rows[-1][2] = b(853, 0)
    return rows


def longhouse(w=5, door=2, right=(828, 836, 844, 852)):
    top = [824] + [825] * (w - 2) + [right[0]]
    roof = [832] + [833] * (w - 2) + [right[1]]
    eave = [840] + [841] * (w - 2) + [right[2]]
    wall = [848] + [850 if i % 2 else 851 for i in range(w - 2)] + [right[3]]
    if door is not None:
        wall[door] = 849
    rows = [rowv(top), rowv(roof), rowv(eave), rowv(wall)]
    if door is not None:
        rows[3][door] = b(849, 0)
    return rows


def plaza(w, h):
    rows = []
    for y in range(h):
        if y == 0: ids = [808] + [809] * (w - 2) + [810]
        elif y == h - 1: ids = [816] + [817] * (w - 2) + [818]
        else: ids = [813] + [797] * (w - 2) + [821]
        rows.append(rowv(ids, 0))
    return rows


def on(out, chunk, dx, dy):
    """stamp, keeping the height of the ground under each tile (a building on a terrace)"""
    for y, row in enumerate(chunk):
        for x, v in enumerate(row):
            if v is not None:
                out[dy + y][dx + x] = (v & 0x0FFF) | (out[dy + y][dx + x] & 0xF000)


def center(rom):
    return W.crop(source(rom, 0, 0), 17, 12, 21, 15)    # Petalburg's Pokemon Center: General pieces only (5 x 4)


# ---- the market's pieces (Slateport's set: tileset.MARKET)
FLOOR = 514
EDGE = {"tl": 629, "t": 630, "tr": 631, "l": 637, "r": 639, "bl": 645, "b": 646, "br": 647}
GATE = [[624, 534, 534, 534, 534, 626], [632, 542, 542, 542, 542, 634], [611, None, None, None, None, 612]]
GOODS = [[524, 539], [548, 830], [540, 548], [831, 547]]   # either side of the vendor's gap (below)


# ---- the woods: the hack's Lavaridge set's red maples and conifers, put together as the game's own maps put them
# (read off Bellchime Trail 35/74, the maple orchard of 36/57 and Route 112 0/27, 2026-10-15). A maple is two tiles
# wide; its crown row and its body row repeat every two rows, each tree's crown drawn in front of the bottom of the
# tree above it:
#   688 696  a crown with open ground above it (walked behind)   658 659  a crown in front of the tree above
#   704 705  the body                                            715 705  the body after a tree on its left
#   838 839  the body's left and right sides, on the grass beside it (walked on)
#   656 657  the bottom, on the grass below the last row
# A conifer is one tile wide: 538 its tip (walked behind), 521 a tip in front of the conifer above, 537 its bottom.
# The set's other tree pieces stand on rock (grey or pink where Kitakami has grass): not used.
MAPLE_CROWN, MAPLE_CROWN_UNDER = (688, 696), (658, 659)
MAPLE_BODY, MAPLE_BODY_AFTER = (704, 705), (715, 705)
MAPLE_SIDE_L, MAPLE_SIDE_R, MAPLE_BOTTOM = 838, 839, (656, 657)
CONIFER_TIP, CONIFER_TIP_UNDER, CONIFER_BOTTOM = 538, 521, 537
MAPLE_BORDER = [658, 659, 715, 705]                     # the wood beyond the map's edges (the layout's border:
                                                        # the game draws it at even x, odd x / even y, odd y)


def put(out, x, y, mt, coll=1):
    """a metatile at (x, y) on the ground's height (a tree on the hall's hill stands as high as the hill)"""
    out[y][x] = mt | coll << 10 | (out[y][x] & 0xF000)


def wood(out, cells):
    """Maples on every cell of `cells` (the crown's left tile: even x, even y), grown together into one wood that
    goes on past the map's edges (its border)."""
    h, w = len(out), len(out[0])
    tree = lambda x, y: (x, y) in cells or x < 0 or y < 0 or x >= w or y >= h
    taken = {(x + dx, y + dy) for (x, y) in cells for dx in (0, 1) for dy in (0, 1)}
    for (x, y) in sorted(cells):
        assert x % 2 == 0 and y % 2 == 0, "a maple of the wood off its grid at %d,%d" % (x, y)
        above, left, right, below = tree(x, y - 2), tree(x - 2, y), tree(x + 2, y), tree(x, y + 2)
        for k in (0, 1):
            put(out, x + k, y, (MAPLE_CROWN_UNDER if above else MAPLE_CROWN)[k], 1 if above else 0)
            put(out, x + k, y + 1, (MAPLE_BODY_AFTER if left else MAPLE_BODY)[k])
            if not below:
                put(out, x + k, y + 2, MAPLE_BOTTOM[k])
        if not left and (x - 1, y + 1) not in taken:
            put(out, x - 1, y + 1, MAPLE_SIDE_L, 0)
        if not right and (x + 2, y + 1) not in taken:
            put(out, x + 2, y + 1, MAPLE_SIDE_R, 0)


def maple(out, x, y, tall=False):
    """a maple standing alone, its crown's left tile at (x, y): 2 x 2, or (tall) 4 x 3 with its body and sides"""
    for k in (0, 1):
        put(out, x + k, y, MAPLE_CROWN[k], 0)
    if tall:
        y += 1
        put(out, x - 1, y, MAPLE_SIDE_L, 0); put(out, x + 2, y, MAPLE_SIDE_R, 0)
        for k in (0, 1):
            put(out, x + k, y, MAPLE_BODY[k])
    for k in (0, 1):
        put(out, x + k, y + 1, MAPLE_BOTTOM[k])


def conifers(out, x, y, n=1):
    """a column of n conifers, the first one's tip at (x, y)"""
    put(out, x, y, CONIFER_TIP, 0)
    for k in range(1, n):
        put(out, x, y + k, CONIFER_TIP_UNDER)
    put(out, x, y + n, CONIFER_BOTTOM)


_PIECES = {}


def drawn(out, ov, piece, x, y):
    """a drawn piece (kart.py), its top-left tile at (x, y), over the ground there: the General piece painted, or
    the market's paving (a shrine's court); a piece drawn whole, the bridge, over none (it is walked on at the
    ground's height, over the pond too)"""
    if not _PIECES:
        _PIECES.update(kart.pieces())
    for (c, r), (pic, attr, blocked) in _PIECES[piece].items():
        v = out[y + r][x + c]
        if v & 0x3FF in W.DECOR + (W.FLOWERS,):         # the grass's odd tufts and flowers: plain grass under it
            v = v & 0xFC00 | W.GRASS
        whole = all(p for row in pic for p in row)
        ground = None if whole else "floor" if ov.get((x + c, y + r)) == ("market", FLOOR) else v & 0x3FF
        ov[(x + c, y + r)] = ("art", (piece, (c, r), ground))
        out[y + r][x + c] = (v & 0x3FF) | (1 if blocked else 0) << 10 | (3 if whole else v >> 12) << 12


def art_used(*overlays):
    """the drawn pieces' tiles the maps use, for tileset.build()"""
    return {what for ov in overlays for (kind, what) in ov.values() if kind == "art"}


def paving(out, ov, x0, y0, w, h):
    """Slateport's market floor (warm stone, Kitakami's) over a rectangle, its curb round it; walked on"""
    for yy in range(h):
        for xx in range(w):
            k = ("tl" if xx == 0 else "tr" if xx == w - 1 else "t") if yy == 0 else \
                ("bl" if xx == 0 else "br" if xx == w - 1 else "b") if yy == h - 1 else \
                ("l" if xx == 0 else "r" if xx == w - 1 else None)
            ov[(x0 + xx, y0 + yy)] = ("market", EDGE[k] if k else FLOOR)
            out[y0 + yy][x0 + xx] = b(1, 0)


def market(out, ov, mx, my, mw, mh):
    """the festival market: a paved street with two stalls a side, paper lanterns in the aisle, its gate over
    the way in at the top. A stall's goods row has a gap of floor in its middle where its vendor stands, under the
    awning, and is talked to from the street below: as Slateport's market has its vendors (0/1: the gaps at 5,43
    and 11,43; 2026-10-16, after vendors standing behind the goods were hidden by the awning). -> the gaps."""
    paving(out, ov, mx, my, mw, mh)
    for gy, row in enumerate(GATE):
        for xx, v in enumerate(row):
            if v is not None:
                ov[(mx + 4 + xx, my - 3 + gy)] = ("market", v)
    for (x, y) in ((mx + 4, my - 1), (mx + 9, my - 1)):
        out[y][x] = (out[y][x] & 0xF3FF) | 1 << 10      # the gate's poles' feet stop you
    k = 0
    gaps = []
    for sy in (my + 2, my + 7):
        mid = lambda g: [g[0], FLOOR, g[1]]
        left = [[549, 534, 534, 534, 535], [557, 633, 633, 633, 543], [573] + mid(GOODS[k]) + [620]]
        right = [[533, 534, 534, 534, 551], [541, 633, 633, 633, 559], [619] + mid(GOODS[k + 1]) + [575]]
        k += 2
        for (sx, st) in ((mx, left), (mx + mw - 5, right)):
            for yy, row in enumerate(st):
                for xx, v in enumerate(row):
                    ov[(sx + xx, sy + yy)] = ("market", v); out[sy + yy][sx + xx] = b(1, 1)
            gaps.append((sx + 2, sy + 2))
        for lx in (mx + 5, mx + mw - 6):
            ov[(lx, sy + 1)] = ("lantern", 0); ov[(lx, sy + 2)] = ("lantern", 1)
            out[sy + 1][lx] = b(1, 1); out[sy + 2][lx] = b(1, 1)
    return gaps


TEAL = [(10, 8, 14, 14)]                                # Kitakami Hall: its pieces stay teal
HOMES_AT = [(5, 26), (38, 26)]                          # the two homes (door: x+2, y+3): the old woman, the old couple
# The signs (placements: kplaces.apply sets these from the file before mossui() draws). The town's four are the
# General set's notice board; the legend's three signboards are drawn pieces of ours (kart.legend_board, since
# 2026-10-17: the user, "can the signboard be something unique from normal signboard"), their roof on the tile above.
TOWN_SIGNS = [(16, 24), (31, 24), (28, 13), (25, 46)]   # the hall's, the shrine's, the pond's, the bus stop's
LEGEND_SIGNS = [(9, 37), (38, 37), (26, 6)]             # the legend's three signboards: the west fields, the east
                                                        # fields, the end of the north path


def mossui(rom, signs=True, plain=()):
    """Mossui Town, revision 7: the town of revision 5 (the user, 2026-10-15: "organized and useful") in a valley of
    red maples (revision 6; the user: "outstanding design ... fantasy!!!", and of the first try at it: every tree
    whole, the border all red and orange, every tile placed with care), and since the road and Oni Mountain went
    (2026-10-16) the whole story in it: the three signboards, the Loyal Three's places (the Dreaded Den went too,
    the same day). 48 x 50:

      the wood     two maples deep all round, closed at the top; the bus stop is a clearing in it at the bottom
                   (x 22-25, y 46-47)
      the avenue   x 23-24 from the wood's edge at the top down to the bus stop: between two stone lanterns (the
                   third signboard at its top end), over the pond on a red bridge, across the street, through the
                   market's gate and the market
      the hall     Kitakami Hall on its hill in the north-west, its forecourt with two stone lanterns, steps down the
                   hill's face, a torii in a court paved as the market is, below them
      the shrine   Loyalty Plaza in a grove of red conifers in the north-east, the same torii and court below it
      the street   y 30-31: the old woman's house and Carmine and Kieran's (the larger) on the west, the Pokemon
                   Center and the old couple's on the east, every door onto it
      the south    the market down the middle, rice paddies either side
      the story    signboards 1 and 2 amid the west and east paddies, 3 at the top end of the avenue;
                   Munkidori asleep by the pond, Okidogi in the corner behind the shrine's grove, Fezandipiti on
                   the hall's hill (marks only: the people are a later milestone)"""
    w, h = 48, 50
    s = W.Sketch(w, h)
    path = lambda xs, ys: [s.put(x, y, ":") for y in ys for x in xs]
    path((23, 24), range(5, 8))                         # the avenue's top end, up to the wood
    s.rect(20, 8, 8, 5, "~")                            # the pond (the bridge: x 23-24, y 8-13)
    path((23, 24), range(13, 30))
    s.terrace(6, 6, 18, 17, stairs=(11, 12, 13), level=1)   # the hall's hill
    path((11, 12, 13), range(14, 19))                   # from the hall's door down the steps
    s.rect(9, 19, 7, 6, ":")                            # the hall's court, paved below (the torii: x 10-14, y 20-23)
    path((11, 12, 13), range(25, 30))
    path((34, 35, 36), range(11, 19))                   # from the plaza
    s.rect(32, 19, 7, 6, ":")                           # the shrine's court
    path((34, 35, 36), range(25, 30))
    path(range(6, 42), (30, 31))                        # the street
    path((23, 24), range(32, 35))                       # under the market's gate
    s.rect(17, 35, 14, 11, ":")                         # the market (paved below: the paths run into it)
    for (x0, y0) in ((5, 34), (10, 34), (5, 39), (10, 39), (34, 34), (39, 34), (34, 39), (39, 39)):
        s.rect(x0, y0, 4, 2, "~")                       # the rice paddies
    for (x, y) in ((8, 7), (15, 7), (19, 9), (28, 9), (19, 24), (28, 24), (6, 27), (41, 27), (16, 33), (31, 33),
                   (8, 44), (39, 44), (15, 40), (32, 40), (5, 18), (42, 18)):
        s.put(x, y, "*")
    out, marks = W.paint(s.text(), s.levels, s.stairs)
    for x, piece in ((23, W.DIRT["l"]), (24, W.DIRT["r"])):  # the path runs on to the bridge: no grass edge
        out[7][x] = b(piece, 0)

    # ---- the wood
    cells = {(x, y) for x in range(0, w, 2) for y in range(0, h, 2)
             if (x < 4 or x >= w - 4 or y < 4 or y >= h - 4) and not (y == h - 4 and 22 <= x <= 25)}
    wood(out, cells)

    # ---- the hall, the shrine, the houses
    on(out, pagoda(2), 10, 8)                           # Kitakami Hall: its door (12, 14)
    W.stamp(out, plaza(7, 4), 32, 8)                    # Loyalty Plaza (the statues are people)
    W.stamp(out, longhouse(7, 3), 15, 26)               # Carmine and Kieran's house
    for (x, y) in HOMES_AT:
        W.stamp(out, longhouse(5, 2), x, y)
    W.stamp(out, center(rom), 28, 26)                   # the Pokemon Center
    ov = {}
    vendors = market(out, ov, 17, 35, 14, 11)         # the stalls' gaps, where their vendors stand
    paving(out, ov, 9, 19, 7, 6)                        # the courts of the hall's torii and the shrine's
    paving(out, ov, 32, 19, 7, 6)

    # ---- trees in the town: maples on the hill and along the avenue, the shrine's conifers
    for (x, y, tall) in ((7, 8, 0), (16, 8, 0), (7, 11, 0), (16, 11, 0),            # on the hill
                         (20, 15, 1), (26, 15, 1), (20, 20, 1), (26, 20, 1),        # the avenue
                         (6, 19, 1), (6, 23, 0), (17, 19, 0), (40, 19, 1), (40, 23, 0), (29, 19, 0),
                         (15, 37, 0), (31, 37, 0), (15, 42, 0), (31, 42, 0), (6, 43, 0), (11, 43, 0),
                         (35, 43, 0), (40, 43, 0)):
        maple(out, x, y, tall)
    for x in range(30, 41):                             # the grove round the plaza: one column of conifers each,
        top = 5 if x % 2 == 0 else 6                    # every other one a row lower, the outer ones down its sides
        conifers(out, x, top, {30: 13, 31: 12, 39: 12, 40: 13}.get(x, 7) - top)
    for x in (32, 38):                                  # along the way down from it
        conifers(out, x, 12, 4)

    # ---- the torii, the stone lanterns, the bridge
    drawn(out, ov, "torii", 10, 20)
    drawn(out, ov, "torii", 33, 20)
    for (x, y) in ((9, 15), (15, 15), (33, 12), (37, 12), (22, 6), (25, 6)):
        drawn(out, ov, "stone lantern", x, y)
    drawn(out, ov, "bridge", 23, 8)
    for y in range(11, 13):                             # the bridge's middle piece again, to the south end
        for c in (0, 1):
            ov[(23 + c, y)] = ov[(23 + c, 10)]
            out[y][23 + c] = out[10][23 + c]
    for c in (0, 1):                                    # the south end
        ov[(23 + c, 13)] = ("art", ("bridge", (c, 2), None))
        out[13][23 + c] = b(out[13][23 + c] & 0x3FF, 0)
    if signs:                                           # (signs=False: the ground alone, for the editor's map)
        for (x, y) in TOWN_SIGNS:
            out[y][x] = b(SIGN, 1)
        for (x, y) in LEGEND_SIGNS:
            if (x, y) in plain:                         # (where the board cannot stand: a plain sign, so that the
                out[y][x] = b(SIGN, 1)                  # editor's check can go on and say what else is wrong)
            else:
                drawn(out, ov, "legend board", x, y - 1)     # the board on (x, y), its roof on the tile above

    marks = {"bus stop": [(23, 47)], "hall door": [(12, 14)], "family door": [(18, 29)], "center door": [(30, 29)],
             "homes": [(x + 2, y + 3) for (x, y) in HOMES_AT], "gate": [(23, 34)], "vendors": vendors,
             "signboard 1": [LEGEND_SIGNS[0]], "signboard 2": [LEGEND_SIGNS[1]], "signboard 3": [LEGEND_SIGNS[2]],
             "munkidori": [(28, 10)], "okidogi": [(42, 10)], "fezandipiti": [(17, 14)]}
    return out, ov, marks



def needed(*designs):
    """the base set's metatiles (512 on) the designs draw with, as they will be drawn (the homes' and the market's
    pieces are ours: not the base's)"""
    out = set()
    for blocks, ov, teal in designs:
        for y, row in enumerate(blocks):
            for x, v in enumerate(row):
                m = v & 0x3FF
                if (x, y) in ov or m < 512:
                    continue
                if m in LONGHOUSE and not any(a <= x <= c and b_ <= y <= d for (a, b_, c, d) in teal):
                    continue
                out.add(m)
    return out


def finish(blocks, ov, teal, ids):
    """our numbers in: the overlay's pieces, and the homes' longhouse pieces (outside `teal`) as the homes' copies"""
    out = []
    for y, row in enumerate(blocks):
        new = []
        for x, v in enumerate(row):
            m, rest = v & 0x3FF, v & 0xFC00
            if (x, y) in ov:
                kind, what = ov[(x, y)]
                m = ids[(kind, what)]
            elif m in LONGHOUSE and not any(a <= x <= c and b_ <= y <= d for (a, b_, c, d) in teal):
                m = ids[("home", m)]
            new.append(m | rest)
        out.append(new)
    return out
