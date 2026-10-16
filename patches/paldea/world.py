"""Area Zero's maps, drawn new from a text sketch with the tiles the game's own maps use (no copied layout).

A sketch is one character per tile. paint() turns it into blocks (metatile | collision << 10 | height << 12, as
the game stores them), with the rules read off the maps that share the tilesets:

  General + Petalburg (the crater; the rules are the Giant Chasm's 34/79 and Route 102's 0/17):
    ^  the land above the crater (113, blocked)       n  the crater's north wall, its face (121, blocked)
    .  grass (1; now and then 399 / 437 / 4)          ,  tall grass (13: wild Pokemon)
    ~  water (a lake: 176 177 178 / 184 161 186, the shore below it on the grass row: 203 204 205)
    :  dirt (464-466 / 472-474 / 480-482)              o  a boulder (224)     b  a bush (6)     s  a stump (7)
    =  the land above, walked on (113: the rim at a lookout)
    T  a tree's top-left corner: a tree is 2 wide and 3 tall, its top row walkable (462 463; 454 455 over tall
       grass; 494 495 over the wall), then 470 471 and a trunk 484 485. A tree two rows below another shares its
       row: 468 469. Trees stand on even columns.
  Marks: any other letter is grass with a name on it (a person, a ripple, a door), returned by paint().
  Heights: a level per tile beside the sketch (Sketch.poly / cut / raise_ / terrace, then tidy); paint() draws
  every edge between levels with the Hisui maps' terrace pieces, slanting sides as staircases of them.
"""
import random
from collections import defaultdict

GRASS, TALL = 1, 13
DECOR = (399, 437, 399, 437, 4)
FLOWERS = 4
PLATEAU, NORTH_FACE = 113, 121
LAKE = {"tl": 176, "t": 177, "tr": 178, "l": 184, "c": 161, "r": 186, "bl": 203, "b": 204, "br": 205,
        "in_tl": 192, "in_tr": 194}
DIRT = {"tl": 464, "t": 465, "tr": 466, "l": 472, "c": 473, "r": 474, "bl": 480, "b": 481, "br": 482,
        "in_tl": 456, "in_tr": 457, "in_br": 458, "in_bl": 459}
# A terrace's pieces: the family the game's own maps build grass terraces from (read off every layout with the
# General tileset: what stands above, below and beside each piece; the hack's Hisui map, layout 826, uses it most).
#   108 153 153 129      the rim (153, walked on) between the two top corners
#   116  .   .  137      the sides
#   124 100 100 145      the face (100) between the two round ends
# Where the edge turns inwards: 140 (a rim from the left meets a side from above), 139 (its mirror), 132 (a face
# from the left meets a side going down), 131 (its mirror).
# Tests 1-12 had 136 / 138 for the top corners and 122 / 125 for the ends: the same shapes drawn for ROCK around
# them, each with a sand-coloured corner on the grass, and 124 / 145 (the ends) where 131 / 132 belong. The user
# found it by hand on test 12, corner by corner ("maybe you need to bake everything balance like corner of each
# tiles, don't make graphical glitch"); OLD_TERRACE is what tidy.py still takes for a terrace's piece.
TERRACE = {"tl": 108, "t": 153, "tr": 129, "l": 116, "r": 137, "bl": 124, "b": 100, "br": 145, "stairs": 207,
           "in_ne": 139, "in_nw": 140, "in_se": 131, "in_sw": 132}
OLD_TERRACE = (136, 138, 122, 125, 104, 106, 107, 109)
TERRACE_WALK = ("t", "in_ne", "in_nw")      # the rim along a terrace's top is walked on; sides and faces are rock
WALL_LEVEL = 9                              # the crater's wall (and the woods) count as higher than any terrace: none
                                            # edges against them
TREE_TOP = {"grass": (462, 463), "tall": (454, 455), "wall": (494, 495)}
TREE_MID, TREE_OVERLAP, TREE_TRUNK = (470, 471), (468, 469), (484, 485)
BOULDER, BUSH, STUMP = 224, 6, 7
GROUND = 3                                   # the crater floor's height
LEVEL_STEP = 2                               # a terrace is two heights up per level (5, 7, 9): the game draws people
                                             # at an even height in front of the top layer (tree tops), at odd ones
                                             # behind it, as on the floor


def blk(mt, coll, elev=3):
    return mt | coll << 10 | elev << 12


def edge_piece(test, x, y, table):
    """The piece of a lake or of a dirt path for the tile (x, y), by which of its neighbours are the same stuff
    (test). A lake has no pieces for its bottom edge: its shore is drawn on the grass below it."""
    n, s_, wl, e = test(x, y - 1), test(x, y + 1), test(x - 1, y), test(x + 1, y)
    if not n:
        return table["tl"] if not wl else table["tr"] if not e else table["t"]
    if not s_ and "bl" in table and table is DIRT:
        return table["bl"] if not wl else table["br"] if not e else table["b"]
    if not wl:
        return table["l"]
    if not e:
        return table["r"]
    if not test(x - 1, y - 1):
        return table["in_tl"]
    if not test(x + 1, y - 1):
        return table["in_tr"]
    if table is DIRT and not test(x + 1, y + 1):
        return table["in_br"]
    if table is DIRT and not test(x - 1, y + 1):
        return table["in_bl"]
    return table["c"]


def terrace_kind(hi):
    """Which of a terrace's pieces a raised tile is, by which tiles round it are as high (hi(dx, dy)): "tl", "t",
    ... as TERRACE names them, or None for a tile inside the terrace."""
    n, s_, wl, e = hi(0, -1), hi(0, 1), hi(-1, 0), hi(1, 0)
    if not s_:
        return "bl" if not wl else "br" if not e else "b"
    if not n:
        return "tl" if not wl else "tr" if not e else "t"
    if not wl:
        return "l"
    if not e:
        return "r"
    if not hi(1, -1):
        return "in_ne"
    if not hi(-1, -1):
        return "in_nw"
    if not hi(1, 1):
        return "in_se"
    if not hi(-1, 1):
        return "in_sw"
    return None


def paint(sketch, levels=None, stairs=(), seed=7, decor=0.10):
    """levels: a height per tile (0 the crater floor, 1 a terrace, 2 a terrace on a terrace). A tile whose
    neighbour is lower is an edge, drawn as the Hisui camp (37/103) draws its terraces: a rim along the top (153,
    walked on), rock sides (116, 137), corners (136, 138), a rock face along the bottom (100) with round ends (122,
    125), inner corners (139, 140 above, 124, 145 below), and wooden steps (207, height 0) where `stairs` says. A
    terrace's tiles stand LEVEL_STEP heights higher per level (3 the floor). A slanting edge is a staircase of
    those pieces, one tile per step."""
    rows = sketch.strip().split()
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, "^") for r in rows]
    h = len(rows)
    rnd = random.Random(seed)
    at = lambda x, y: rows[y][x] if 0 <= x < w and 0 <= y < h else "^"
    out = [[0] * w for _ in range(h)]
    lv = [[(levels[y][x] if levels else 0) for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if rows[y][x] in "^n":
                lv[y][x] = WALL_LEVEL
    # outside the map: the same height as the nearest tile inside (no edges along the map's border)
    level = lambda x, y: lv[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]
    elev = [[GROUND + LEVEL_STEP * lv[y][x] if lv[y][x] < WALL_LEVEL else GROUND for x in range(w)] for y in range(h)]
    stairs = set(stairs)
    marks = defaultdict(list)
    trees = []
    for y in range(h):
        for x in range(w):
            if rows[y][x] == "T":
                assert x % 2 == 0, "tree at %d,%d: trees stand on even columns" % (x, y)
                trees.append((x, y))
    water = lambda x, y: at(x, y) == "~"
    dirt = lambda x, y: at(x, y) == ":"

    for y in range(h):
        for x in range(w):
            c = rows[y][x]
            z = elev[y][x]
            if c == "^":
                out[y][x] = blk(PLATEAU, 1)
            elif c == "n":
                out[y][x] = blk(NORTH_FACE, 1)
            elif c == ",":
                out[y][x] = blk(TALL, 0, z)
            elif c == "~":
                if water(x, y + 1):                           # a lake may only widen going down (no pieces for
                    for dx in (-1, 1):                        # an inner corner at its bottom)
                        assert not (water(x + dx, y) and not water(x + dx, y + 1)), \
                            "the lake narrows downwards at %d,%d" % (x + dx, y)
                out[y][x] = blk(edge_piece(water, x, y, LAKE), 0, 1)
            elif c == ":":
                out[y][x] = blk(edge_piece(dirt, x, y, DIRT), 0, z)
            elif c == "o":
                out[y][x] = blk(BOULDER, 1, z)
            elif c == "b":
                out[y][x] = blk(BUSH, 1, z)
            elif c == "s":
                out[y][x] = blk(STUMP, 1, z)
            elif c == "=":
                out[y][x] = blk(PLATEAU, 0, z)
            else:                                             # grass, a tree's anchor, or a mark
                if water(x, y - 1):                           # the lake's shore, on the grass below it
                    assert not water(x - 1, y) and not water(x + 1, y), "water beside the shore at %d,%d" % (x, y)
                    k = "bl" if not water(x - 1, y - 1) else "br" if not water(x + 1, y - 1) else "b"
                    out[y][x] = blk(LAKE[k], 0, z)
                else:
                    mt = GRASS
                    if c == "*":
                        mt = FLOWERS
                    elif c in ".T" and rnd.random() < decor:
                        mt = rnd.choice(DECOR)
                    out[y][x] = blk(mt, 0, z)
                if c not in ".T*":
                    marks[c].append((x, y))
    # trees, column pair by column pair, so that one stacked two rows below another shares a row with it
    by_col = defaultdict(set)
    for x, y in trees:
        by_col[x].add(y)
    for x, starts in by_col.items():
        for y in sorted(starts):
            nxt = at(x + 1, y)                                # what the tree's top row stands on: the sketch
            bg = "tall" if nxt == "," else "wall" if nxt in "^n" else "grass"   # keeps it in the 2nd column
            top = TREE_TOP[bg]
            if (y - 2) in starts:                             # the tree above ends on this row: they share it
                pair, coll = TREE_OVERLAP, 1
            else:
                pair, coll = top, 1 if bg == "wall" else 0
            for k in (0, 1):
                if 0 <= y < h:
                    out[y][x + k] = blk(pair[k], coll, elev[y][x + k])
            if y + 1 < h:
                for k in (0, 1):
                    out[y + 1][x + k] = blk(TREE_MID[k], 1, elev[y + 1][x + k])
            if y + 2 < h and (y + 2) not in starts:
                for k in (0, 1):
                    out[y + 2][x + k] = blk(TREE_TRUNK[k], 1, elev[y + 2][x + k])
    # terraces last: every raised tile with a lower neighbour is an edge, over whatever the sketch had there
    for y in range(h):
        for x in range(w):
            L = lv[y][x]
            if L == 0 or L >= WALL_LEVEL:
                continue
            hi = lambda dx, dy: level(x + dx, y + dy) >= L
            assert hi(0, -1) or hi(0, 1), "terrace one tile tall at %d,%d" % (x, y)
            assert hi(-1, 0) or hi(1, 0), "terrace one tile wide at %d,%d" % (x, y)
            k = terrace_kind(hi)
            if k is None:
                continue
            if (x, y) in stairs:
                assert k == "b", "steps at %d,%d are not on a terrace's face" % (x, y)
                out[y][x] = blk(TERRACE["stairs"], 0, 0)
            else:
                out[y][x] = blk(TERRACE[k], 0 if k in TERRACE_WALK else 1, elev[y][x])
    for x, y in stairs:
        assert out[y][x] & 0x3FF == TERRACE["stairs"], "steps at %d,%d are not on a face" % (x, y)
    problems = edge_problems(lv)
    assert not problems, "terrace edges the pieces cannot draw cleanly: " + "; ".join(problems[:12])
    return out, dict(marks)


FACE_RUN, RIM_RUN = 3, 2    # the shortest face (bottom edge) and rim (top edge) a step may leave: a face one tile
                            # long is drawn as a round end beside an inner corner, which reads as a loose boulder
                            # (the user's screenshot of test 6); a rim one tile long as a stray corner


def edge_problems(lv):
    """Every face or rim of a terrace shorter than FACE_RUN / RIM_RUN tiles, on one level and one row."""
    h, w = len(lv), len(lv[0])
    level = lambda x, y: lv[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]
    out = []
    for y in range(h):
        for name, dy, need in (("face", 1, FACE_RUN), ("rim", -1, RIM_RUN)):
            x = 0
            while x < w:
                L = lv[y][x]
                edge = lambda xx: lv[y][xx] == L and level(xx, y + dy) < L
                if 0 < L < WALL_LEVEL and edge(x):
                    x0 = x
                    while x < w and edge(x):
                        x += 1
                    if x - x0 < need:
                        out.append("%s of %d at x %d-%d, y %d (level %d)" % (name, x - x0, x0, x - 1, y, L))
                else:
                    x += 1
    return out


class Sketch:
    """A sketch drawn with rectangles: text() gives what paint() reads, `levels` the height of every tile (raised
    with raise_() / terrace()), `stairs` the steps, `marks` the named places."""

    def __init__(self, w, h, fill="."):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]
        self.levels = [[0] * w for _ in range(h)]
        self.stairs = []
        self.marks = defaultdict(list)                    # named places, kept apart from the ground under them

    def mark(self, name, x, y):
        self.marks[name].append((x, y))
        return self

    def raise_(self, x0, y0, x1, y1, level=1):
        """Tiles x0..x1, y0..y1 at height `level` at least: overlapping rectangles make one terrace of any shape."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.levels[y][x] = max(self.levels[y][x], level)
        return self

    def terrace(self, x0, y0, x1, y1, stairs=(), level=1):
        """A rectangle raised to `level` (rim, sides and face included: x0..x1, y0..y1), steps up its face (the
        bottom row) at the columns given."""
        self.raise_(x0, y0, x1, y1, level)
        for sx in stairs:
            self.stairs.append((sx, y1))
        return self

    def poly(self, pts, level=1, op=max):
        """The tiles whose centres are inside the polygon (its corners on tile corners: (4, 7) is tile 4,7's top
        left) raised to `level` at least (op=min: lowered to it at most). Slanting sides become staircases."""
        for y in range(min(p[1] for p in pts), max(p[1] for p in pts)):
            cy = y + 0.5
            cuts = sorted(x1 + (cy - y1) * (x2 - x1) / (y2 - y1)
                          for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]) if (y1 > cy) != (y2 > cy))
            for a, b in zip(cuts[::2], cuts[1::2]):
                for x in range(max(0, int(a - 0.5) - 1), min(self.w, int(b + 0.5) + 1)):
                    if a < x + 0.5 < b:
                        self.levels[y][x] = op(self.levels[y][x], level)
        return self

    def cut(self, pts, level=0):
        """The polygon's tiles lowered to `level` at most."""
        return self.poly(pts, level, min)

    def blob(self, x0, y0, x1, y1, level=1, tl=0, tr=0, bl=0, br=0):
        """Tiles x0..x1, y0..y1 raised to `level`, each corner cut as a staircase as many rows deep as asked: the
        top corners two tiles per row (rims of two), the bottom ones three (faces of three), the shortest steps
        the pieces draw cleanly."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                dt, db, dl, dr = y - y0, y1 - y, x - x0, x1 - x
                if (dt < tl and dl < RIM_RUN * (tl - dt)) or (dt < tr and dr < RIM_RUN * (tr - dt)) or \
                        (db < bl and dl < FACE_RUN * (bl - db)) or (db < br and dr < FACE_RUN * (br - db)):
                    continue
                self.levels[y][x] = max(self.levels[y][x], level)
        return self

    def tidy(self):
        """Lower every raised tile that would be one tile wide or tall (no pieces for those) until none is left."""
        lv, w, h = self.levels, self.w, self.h
        changed = True
        while changed:
            changed = False
            for y in range(h):
                for x in range(w):
                    L = lv[y][x]
                    if L == 0 or L >= WALL_LEVEL:
                        continue
                    hi = lambda dx, dy: lv[min(max(y + dy, 0), h - 1)][min(max(x + dx, 0), w - 1)] >= L
                    if not (hi(0, -1) or hi(0, 1)) or not (hi(-1, 0) or hi(1, 0)):
                        lv[y][x] -= 1
                        changed = True
        return self

    def step(self, x, y):
        """Steps at (x, y): the tile must end up on a terrace's face."""
        self.stairs.append((x, y))
        return self

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.g[yy][xx] = c
        return self

    def trees(self, x, y, w, h, bg="."):
        """A wood: trees on every even column of the rectangle, every second row from its top; the last tree's
        trunk is the rectangle's bottom row (h odd), its top row stays walkable."""
        assert x % 2 == 0 and w % 2 == 0 and h % 2 == 1 and h >= 3, (x, y, w, h)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.g[yy][xx] = bg
        for yy in range(y, y + h - 2, 2):
            for xx in range(x, x + w, 2):
                self.g[yy][xx] = "T"
        return self

    def put(self, x, y, c):
        self.g[y][x] = c
        return self

    def text(self):
        return "\n".join("".join(r) for r in self.g)


def stamp(out, chunk, dx, dy):
    for y, row in enumerate(chunk):
        for x, v in enumerate(row):
            if v is not None:
                out[dy + y][dx + x] = v


def crop(blocks, x0, y0, x1, y1):
    return [row[x0:x1 + 1] for row in blocks[y0:y1 + 1]]


def walkable(v):
    return (v >> 10) & 3 == 0


def reach(b, start, blocked=()):
    """Every tile reachable on foot from start, with the game's height rule: 1 is water (Surf, not walked here),
    15 keeps the height you had, 0 resets it (stairs), any other must match."""
    h, w = len(b), len(b[0])
    seen = set()
    q = [(start[0], start[1], b[start[1]][start[0]] >> 12)]
    blocked = set(blocked)
    while q:
        x, y, e = q.pop()
        if (x, y, e) in seen:
            continue
        seen.add((x, y, e))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h) or (nx, ny) in blocked:
                continue
            v = b[ny][nx]
            if not walkable(v):
                continue
            z = v >> 12
            if z == 1:
                continue
            ne = e if z == 15 else 0 if z == 0 else z
            if e not in (0, 15) and z not in (0, 15) and z != e:
                continue
            q.append((nx, ny, ne))
    return {(x, y) for x, y, e in seen}


# ---------------------------------------------------------------------------------------------------- the crater
# The north wall's stairs and cave mouth, as the Giant Chasm (34/79) has them: x 42-52, y 0-8 there (its mouth at
# 47,4, stairs 46-48 x 7-8). Two of its tree tops (494 495 at 44-45,8) become wall. Its floor is height 3 there;
# here it takes the height of the shelf it opens onto.
ALCOVE_SRC = (42, 0, 52, 8)
# The floor is sketched in its own coordinates (crater_floor, 52x44: the wall's face in rows 3-6); the map puts
# TOP rows above it, where the waterfall comes from (the hanging valley). The constants up to the valley's are
# the floor's; crater() moves them down by TOP. Who stands where is not here: places.py (the map's coordinates).
CRATER_W, FLOOR_H, TOP = 52, 44, 8
CRATER_H = FLOOR_H + TOP
ALCOVE_AT = (9, 0)                          # the mouth lands at (14, 4), the stairs at 13-15 x 7-8
LAB_MOUTH = (44, 6)                         # mouths in the wall, each its top (159) above it: the Zero Lab's door
CAVE_MOUTH = (6, 6)                         # and the Crystal Cavern's
# The research stations: a house of Petalburg City (0/0) x 8-13, y 14-18, its door (647, height 0) in the middle of
# its bottom row. No. 2 on the shelf, No. 3 on the knoll.
STATION_SRC = (8, 14, 13, 18)
STATION2_AT, STATION3_AT = (20, 8), (40, 23)
door_of = lambda at: (at[0] + 2, at[1] + 4)
STATION2_DOOR, STATION3_DOOR = door_of(STATION2_AT), door_of(STATION3_AT)
# A waterfall down the north wall into a pond, as Route 119 (0/34) builds its falls: a river on the land above
# (400 368 402), the lip (187 179 188), the falling water (185), the splash (376 193 377) in the pond's top row.
# All of it is water (height 1, open): the game's Waterfall climbs it, and coming down it carries you. At the top a
# ledge (x 27-31, row 2) runs to Research Station No. 4, a mouth in a little cliff (rows 0-1).
FALL_X = 32                                 # its three columns: 32-34
POND = (30, 7, 7, 5)                        # x, y, w, h
# (the splash: 193 across. 376 and 377, Route 119's ends of it, each carry a bank; here the falls come down into
# the middle of a pond's top row, and the banks stood in the water. The user painted them over on test 12.)
RIVER, LIP, DROP, SPLASH = (400, 368, 402), (187, 179, 188), (185, 185, 185), (193, 193, 193)
# The hanging valley (map coordinates): a meadow on the rim with trees all round, a spring at its north end
# (the pool's top edge, 392 393 394) feeding the river down to the falls' lip, Research Station No. 4 (a house
# like the others), tall grass, crystals; its south row is the rim itself (113, walked on) above the wall.
VALLEY = (24, 3, 41, 9)                     # x0, y0, x1, y1 of its meadow; the rim is row 10
STATION4_AT = (25, 4)
STATION4_DOOR = door_of(STATION4_AT)
SPRING_Y = 4                                # the river's first row; its lip is the wall's first row (TOP + 3)
POOL_TOP = (392, 393, 394)
PLAIN = (GRASS, FLOWERS) + DECOR             # ground a rock may be put on


def rock(blocks, x, y):
    """A boulder on (x, y) if that is plain grass (paldea_patch.py puts one behind each 64x64 Pokemon: the sprite
    covers whoever stands there). Done on the painted map, not in the sketch, so that the two eras keep the same
    ground whatever stands on it. True if it was put."""
    v = blocks[y][x]
    if v & 0x3FF not in PLAIN or (v >> 10) & 3:
        return False
    blocks[y][x] = blk(BOULDER, 1, v >> 12)
    return True


def crater_sketch():
    """The whole map: the floor (crater_floor) moved down by TOP; above it the rim's woods and the hanging valley
    the waterfall comes from."""
    f = crater_floor()
    s = Sketch(CRATER_W, CRATER_H)
    for y in range(FLOOR_H):
        s.g[y + TOP] = list(f.g[y])
        s.levels[y + TOP] = list(f.levels[y])
    s.stairs = [(x, y + TOP) for x, y in f.stairs]
    for k, v in f.marks.items():
        s.marks[k] = [(x, y + TOP) for x, y in v]
    s.rect(0, 0, CRATER_W, TOP, "^")
    s.trees(0, 0, 20, 7, "^").trees(46, 0, 6, 7, "^")             # the rim's woods
    s.trees(20, 0, 4, 11, "^").trees(42, 0, 4, 11, "^")           # the valley's sides
    s.trees(24, 0, 18, 3, "^")                                    # its back
    vx0, vy0, vx1, vy1 = VALLEY
    s.rect(vx0, vy0, vx1 - vx0 + 1, vy1 - vy0 + 1, ".")
    s.rect(vx0, vy1 + 1, vx1 - vx0 + 1, 1, "=")                   # the rim, a lookout over the crater
    s.rect(36, 3, 5, 4, ",")                                      # tall grass east of the spring
    for x, y in ((29, 9), (31, 9), (37, 8), (39, 7), (24, 8), (35, 3)):
        s.put(x, y, "*")
    for x, y in ((41, 8), (36, 9)):
        s.put(x, y, "o")
    return s


def crater_floor():
    """The crater: a shelf under the north wall where you come down (Research Station No. 2 on it, the Crystal
    Cavern's mouth at its west end), the west slope below it with the den on it (the Titan between two crystals),
    the mesa in the middle with the dais (a time crystal), the valley round them; in the north-east a waterfall's
    pond, the Zero Lab's door and a terrace with a platform (the other time crystal); the knoll in the east with
    Research Station No. 3 on top; the lake in the south, the picnic place and the legend on its east shore.
    Terraces are cut-corner blocks (Sketch.blob): every face at least three tiles long, every rim two."""
    W, H = CRATER_W, FLOOR_H
    s = Sketch(W, H)
    s.rect(0, 0, W, 3, "^").rect(0, 3, W, 4, "n")                    # the land above, the wall's face
    tree = lambda x, y, bg=".": s.trees(x, y, 2, 3, bg)

    # ---- woods west, east and south (higher than any terrace: no edge is drawn against them)
    s.trees(0, 5, 4, 39, "n").trees(48, 5, 4, 39, "n").trees(4, 39, 44, 5)
    for y in range(7, 39):
        for x in (0, 1, 2, 3, 48, 49, 50, 51):
            if s.g[y][x] == "n":
                s.g[y][x] = "."
    s.trees(4, 35, 4, 5).trees(44, 33, 4, 7)                         # the woods reach in at the south corners
    for y in range(7, H):
        for x in range(W):
            if x < 4 or x >= 48 or y >= 39 or (x < 8 and y >= 35) or (x >= 44 and y >= 33):
                s.levels[y][x] = WALL_LEVEL

    # ---- heights
    s.blob(4, 7, 18, 33, 1, br=2)                                    # the west slope
    s.blob(4, 7, 27, 14, 2, br=1)                                    # the shelf
    s.blob(10, 13, 18, 16, 2, bl=1, br=1)                            # its lobe, down from the stairs
    s.blob(4, 23, 13, 30, 2, tr=2, br=1)                             # the den
    s.blob(21, 18, 33, 29, 1, tl=2, tr=2, bl=1, br=1)                # the mesa
    s.blob(22, 21, 31, 25, 2, tl=1, tr=1, bl=1, br=1)                # the dais
    s.blob(39, 10, 47, 18, 1, tl=1, bl=1)                            # the north-east terrace
    s.blob(41, 11, 47, 15, 2, tl=1, bl=1)                            # its platform
    s.blob(34, 21, 47, 31, 1, tl=2, bl=2)                            # the knoll
    s.blob(38, 22, 46, 29, 2, tl=1, bl=1, br=1)                      # its top, Station No. 3 on it
    for x, y in ((7, 14), (23, 14), (14, 16), (14, 32), (8, 30), (26, 29), (26, 25), (44, 18), (45, 15),
                 (42, 31), (42, 29)):
        s.step(x, y)
    s.tidy()

    # ---- water: the pond under the waterfall, the lake in the south (wider going down)
    px, py, pw, ph = POND
    s.rect(px, py, pw, ph, "~")
    s.rect(21, 31, 9, 1, "~").rect(19, 32, 13, 1, "~").rect(17, 33, 17, 4, "~")

    # ---- dirt paths: down from the stairs, along the shelf to the station, down the west slope, through the
    # valley and up to the lab; the picnic place
    s.rect(13, 9, 3, 7, ":").rect(15, 13, 9, 1, ":")
    s.rect(14, 17, 2, 15, ":")
    s.rect(22, 15, 3, 2, ":").rect(24, 16, 14, 2, ":").rect(37, 8, 2, 8, ":").rect(39, 8, 6, 2, ":")
    s.rect(36, 34, 5, 4, ":")

    # ---- tall grass
    for x, y, w, h in ((5, 9, 6, 4), (5, 17, 8, 5), (15, 21, 3, 9), (19, 19, 2, 9), (22, 26, 3, 2),
                       (34, 17, 4, 4), (35, 24, 3, 5), (40, 33, 4, 5), (8, 35, 4, 3), (30, 19, 2, 1)):
        s.rect(x, y, w, h, ",")

    # ---- trees, rocks, flowers
    for x, y, bg in ((28, 8, "."), (46, 7, "."), (34, 13, "."), (14, 35, "."), (42, 36, "."),
                     (6, 18, ","), (10, 19, ","), (34, 18, ",")):
        tree(x, y, bg)
    for x, y in ((6, 24), (12, 27), (5, 29), (31, 21), (20, 20), (40, 17), (36, 23), (17, 30), (32, 30),
                 (24, 19), (16, 25)):
        s.put(x, y, "o")
    for x, y in ((9, 8), (18, 9), (26, 9), (24, 27), (28, 27), (39, 20), (45, 13), (35, 31), (22, 37), (30, 38),
                 (12, 37), (46, 27), (20, 16), (37, 12)):
        s.put(x, y, "*")

    return s


def crater_levels():
    """The level of every tile of the crater as it is sketched (0 the floor, 1 and 2 the terraces, WALL_LEVEL the
    wall and the land above it): what tidy.py needs to draw a terrace's edges again."""
    s = crater_sketch()
    rows = s.text().split()
    return [[WALL_LEVEL if rows[y][x] in "^n" else s.levels[y][x] for x in range(s.w)] for y in range(s.h)]


def crater_dirt():
    """The tiles the crater's sketch has a dirt path on. Not all of them show dirt: a terrace's edge is drawn over
    the path where it goes through one, and the path's pieces beside it are still those of a path that goes on."""
    rows = crater_sketch().text().split()
    return {(x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == ":"}


def crater(chasm_blocks, petalburg_blocks):
    """The crater's blocks and named places, the same for both eras (tints apart)."""
    s = crater_sketch()
    b, marks = paint(s.text(), s.levels, s.stairs)
    marks.update({k: list(v) for k, v in s.marks.items()})
    down = lambda xy: (xy[0], xy[1] + TOP)

    def height(x, y):
        L = s.levels[y][x]
        return GROUND if L >= WALL_LEVEL else GROUND + LEVEL_STEP * L

    def lay(chunk, x0, y0, floor):
        """A copied piece, its walkable floor (height 3 where it came from) at `floor`."""
        for y, row in enumerate(chunk):
            for x, v in enumerate(row):
                if v >> 12 == 3 and not (v >> 10) & 3:
                    v = v & 0xFFF | floor << 12
                b[y0 + y][x0 + x] = v

    sx0, sy0, sx1, sy1 = ALCOVE_SRC
    chunk = [list(r) for r in crop(chasm_blocks, sx0, sy0, sx1, sy1)]
    for y, row in enumerate(chunk):
        for x, v in enumerate(row):
            if v & 0x3FF in (494, 495):
                row[x] = blk(NORTH_FACE, 1)
    ax, ay = down(ALCOVE_AT)
    mx = ax + 47 - sx0
    lay(chunk, ax, ay, height(mx, ay + 9))
    for mx_, my in (down(LAB_MOUTH), down(CAVE_MOUTH)):
        b[my - 1][mx_] = blk(159, 1)
        b[my][mx_] = blk(167, 0, 0)
    x0, y0, x1, y1 = STATION_SRC
    for at in (down(STATION2_AT), down(STATION3_AT), STATION4_AT):
        dx, dy = door_of(at)
        lay(crop(petalburg_blocks, x0, y0, x1, y1), *at, height(dx, dy + 1))
        assert b[dy][dx] & 0x3FF == 647, "a station's door is not where it should be"
    # the waterfall, all of it open water: the spring and the river across the valley, the lip on the wall's first
    # row, the falling water down the other three, the splash in the pond's top row
    lip = TOP + 3
    for k in range(3):
        b[SPRING_Y][FALL_X + k] = blk(POOL_TOP[k], 0, 1)
        for y in range(SPRING_Y + 1, lip):
            b[y][FALL_X + k] = blk(RIVER[k], 0, 1)
        b[lip][FALL_X + k] = blk(LIP[k], 0, 1)
        for y in (lip + 1, lip + 2, lip + 3):
            b[y][FALL_X + k] = blk(DROP[k], 0, 1)
        b[POND[1] + TOP][FALL_X + k] = blk(SPLASH[k], 0, 1)
    marks["mouth"] = [(mx, ay + 4)]
    marks["L"] = [down(LAB_MOUTH)]
    marks["cave"] = [down(CAVE_MOUTH)]
    marks["door2"] = [down(STATION2_DOOR)]
    marks["door3"] = [down(STATION3_DOOR)]
    marks["door4"] = [STATION4_DOOR]
    woods_on(b)
    return b, marks


# ------------------------------------------------------------------------------------ past the crater's edges
# The screen shows 7 tiles either side of you and 5 above and below, and the crater's ground comes within 4 tiles
# of its sides and 3 of its top: you see up to 3 tiles past the edge. There the game draws the map's border
# block, 2 x 2 tiles again and again. That can go on with one wood; it cannot go on with the land above and the
# wall's face, which run out through both sides, nor with the rim's wood, which stands a row off the wood below.
# Up to test 13 the cliff stopped dead against trees at both ends, the rim's trees jumped half a tree at the
# edge, and a strip of the land above showed over the top row (the user: "increase the border of the map, cuz
# right now it got cut off when ran on the border").
# So the game is given what lies past each edge: four strips, maps of their own that nobody enters, joined to the
# crater the way a route is joined to the next (maps.py: connections). Nothing in the crater moves: every x, y
# is what it was. Each strip goes on with what the map ends in, in step with it: beyond() below.
MARGIN = 7                                   # the tiles past a map's edge the game keeps, on every side


def woods_on(b):
    """The crater's first and last rows as rows of a wood that goes on: the tree tops along the top (drawn against
    the land above) and the trunks along the bottom become the row two trees share, one standing two rows below
    the other. Past the edge the next row of middles follows."""
    for y, was in ((0, TREE_TOP["wall"]), (len(b) - 1, TREE_TRUNK)):
        for x, v in enumerate(b[y]):
            if v & 0x3FF in was:
                b[y][x] = blk(TREE_OVERLAP[was.index(v & 0x3FF)], 1, v >> 12)


def shut(v):
    """A block as scenery: nobody stands on it."""
    return (v & 0x3FF) | (1 << 10) | (v & 0xF000)


def beyond(b):
    """What the game draws past the edges of a map that ends in woods: {side: (rows of blocks, offset)}, the
    offset being where the strip lies along that edge (a connection's). Every row goes on to the west and east as
    it ends, and every column to the north and south: its last two tiles again and again (a tree is two tiles
    wide, and two rows of a wood are a row of middles and a shared row; the land above and the wall's face are
    the same all along). The corners belong to the north and south strips. All of it is shut."""
    h, w = len(b), len(b[0])
    assert w % 2 == 0 and h % 2 == 0, "the edge's two tiles would fall out of step"
    at = lambda x, y: shut(b[y if 0 <= y < h else (y & 1) if y < 0 else h - 2 + (y & 1)]
                            [x if 0 <= x < w else (x & 1) if x < 0 else w - 2 + (x & 1)])
    across = range(-MARGIN, w + MARGIN + 1)      # the game keeps one column more on the east
    return {"north": ([[at(x, y) for x in across] for y in range(-MARGIN, 0)], -MARGIN),
            "south": ([[at(x, y) for x in across] for y in range(h, h + MARGIN)], -MARGIN),
            "west": ([[at(x, y) for x in range(-MARGIN, 0)] for y in range(h)], 0),
            "east": ([[at(x, y) for x in range(w, w + MARGIN + 1)] for y in range(h)], 0)}


# ------------------------------------------------------------------------------------------- the Sealed Vault
# General + the Snowpoint Temple's tileset, the pieces of the temple's rooms (36/75-79; the last one is where
# Regigigas sleeps): walls two tiles thick (898 898 on the left, 896 896 on the right, 891 905 892 along the top,
# the snow ledge 889 along the bottom), a wall's free end 904 906, floor 901 (903 with ice below it, 911 with ice
# above), ICE 909 (behaviour 0x20: a step onto it goes on until something stops it), an ice boulder 899 standing
# on it, a patch of snow 655 lying on it (you stop ON a patch, BEFORE a boulder), the way out 902 (a floor tile
# that leaves southwards). 897 is the snow outside. The room is drawn new: five niches along the back wall, each
# one tile wide with a wall two tiles thick between, a dais of floor below them, the mirror floor (13 x 9), a
# strip of floor along the bottom, and the way out in the bottom wall below it. The way out is one tile right of
# the middle column on purpose: that column is clear from the strip up to the dais, the way back down from the
# niches, and an arrow warp takes you out the moment you stand on it holding its direction. At the column's foot
# a slide down while holding Down carried you out of the room (the first build had the way out there). Tinted
# like the Crystal Cavern it is entered from, the ice is the cavern's polished crystal. Who and what stands in it
# is places.py's; the boulders and patches are ground (they can be painted), and check.py plays the sliding
# through.
VAULT_SRC = (36, 79)
VAULT_W, VAULT_H = 17, 18
VAULT_NICHES = (2, 5, 8, 11, 14)            # the niches' columns
VAULT_DAIS, VAULT_STRIP = 5, 15             # the rows of floor above and below the mirror floor
VAULT_FIELD = (2, 6, 14, 14)                # the mirror floor: x0, y0, x1, y1
VAULT_DOOR = (9, 16)
VP = {"tl": 891, "top": 905, "tr": 892, "left": 898, "right": 896, "end_l": 904, "end_r": 906, "ledge": 889,
      "out": 897, "floor": 901, "dais": 903, "strip": 911, "door": 902, "ice": 909, "rock": 899, "patch": 655}
ICE = 0x20                                  # the behaviour of a tile you slide on
# The puzzle as it is built: the boulders and patches here, the stakes in places.py. It was found by a search
# over layouts, each played through (vault_search.py; NOTES, *Test 15*): the middle column is clear (straight up
# from the strip to the dais and straight back), no stake can be run into by one slide from the dais or the
# strip, no place traps you, and it takes eleven slides at the least. The stake of the Tablets (9,9) and of the
# Beads (12,9) can be reached from the start; the stake of the Vessel (5,11) only by the row it stands in, from
# 13,11, which is come to from 13,7, and that only by the slide that follows pulling the stake of the Beads: from
# 12,10 you slide on over where it stood, up to 12,7.
VAULT_ROCKS = [(2, 13), (5, 7), (5, 14), (6, 14), (9, 7), (9, 13), (12, 6), (12, 13), (13, 6), (13, 12), (13, 14),
               (14, 7)]
VAULT_PATCHES = [(2, 8), (3, 10), (9, 12)]


def vault():
    """The Sealed Vault's blocks and named places."""
    wall = lambda k: blk(VP[k], 1, 1)
    floor = lambda k: blk(VP[k], 0)
    w, h = VAULT_W, VAULT_H
    b = [[wall("out")] * w for _ in range(h)]
    b[0] = [wall("tl")] + [wall("top")] * (w - 2) + [wall("tr")]
    b[1][0], b[1][w - 1] = wall("left"), wall("right")
    for x in range(1, w - 1):                   # each niche's own top: a corner, the wall above it, a corner
        b[1][x] = wall("top" if x in VAULT_NICHES else "tl" if x + 1 in VAULT_NICHES else "tr")
    for y in range(2, VAULT_STRIP + 1):
        b[y][0] = b[y][1] = wall("left")
        b[y][w - 2] = b[y][w - 1] = wall("right")
    x0, y0, x1, y1 = VAULT_FIELD
    for y in range(2, VAULT_DAIS):              # the niches, and the walls between them down to their free ends
        for x in range(x0, x1 + 1):
            if x in VAULT_NICHES:
                b[y][x] = floor("floor")
            elif x - 1 in VAULT_NICHES:
                b[y][x] = wall("right" if y < VAULT_DAIS - 1 else "end_l")
            else:
                b[y][x] = wall("left" if y < VAULT_DAIS - 1 else "end_r")
    for x in range(x0, x1 + 1):
        b[VAULT_DAIS][x] = floor("dais")
        for y in range(y0, y1 + 1):
            b[y][x] = floor("ice")
        b[VAULT_STRIP][x] = floor("strip")
    b[h - 2] = [wall("left")] + [wall("ledge")] * (w - 2) + [wall("right")]
    b[h - 1] = [wall("ledge")] * w
    b[VAULT_DOOR[1]][VAULT_DOOR[0]] = floor("door")       # (in the bottom wall, beside the middle column)
    for x, y in VAULT_ROCKS:
        b[y][x] = wall("rock")
    for x, y in VAULT_PATCHES:
        b[y][x] = floor("patch")
    return b, {"door": [VAULT_DOOR]}


# ---------------------------------------------------------------------------------------------------- the wall
# General + NavelRock, the pieces of the unused cliff 34/27: sky (900, 908), the summit (rows 6-9 there), rock seen
# from above (529, blocked), the rock face (537), a ledge (540 | 529 ... | 539, the lip under it 536 | 537 | 538), a
# ladder (516, height 0), a cave mouth (523 524 525 / 531 532 533, the middle one walkable, height 0), boulders.
WALL_W, WALL_H = 27, 30
SUMMIT_SRC = (0, 4, 26, 9)                   # 34/27's sky, summit and the summit's foot, whole width
FACE, ROCK, LADDER = 537, 529, 516
LEDGE_L, LEDGE_R, LIP_L, LIP_R = 540, 539, 536, 538
MOUTH = ((523, 524, 525), (531, 532, 533))
WALL_LEDGES = (14, 20, 26)                   # ledge floors: where you land, the middle one, the bottom one
WALL_LEDGE_X = (6, 20)                       # each ledge from its left cap to its right cap
WALL_MOUTHS = {"hole": (13, 12), "station": (10, 18), "ice": (15, 18), "down": (17, 24)}   # top-left of each 3x2
WALL_LADDERS = ((8, 15, 19), (19, 15, 19), (13, 21, 25))   # x, first row, last row
WALL_ROCKS = ((7, 14), (7, 26), (9, 26))                   # off every way through


def wall(cliff_blocks):
    """The wall: a short climb down. Returns (blocks, marks): marks name the mouths' walkable tiles, the
    arrival, and the ledges' left ends."""
    W, H = WALL_W, WALL_H
    b = [[blk(FACE, 1)] * W for _ in range(H)]
    sx0, sy0, sx1, sy1 = SUMMIT_SRC
    stamp(b, crop(cliff_blocks, sx0, sy0, sx1, sy1), 0, 0)          # rows 0-5
    for y in (6, 7, 8):
        for x in range(W):
            b[y][x] = blk(ROCK, 1)
    x0, x1 = WALL_LEDGE_X
    for ly in WALL_LEDGES:
        for x in range(W):
            b[ly][x] = blk(FACE, 1)
            if ly + 1 < H:
                b[ly + 1][x] = blk(ROCK, 1) if x < x0 or x > x1 else blk(FACE, 1)
        b[ly][x0] = blk(LEDGE_L, 1)
        b[ly][x1] = blk(LEDGE_R, 1)
        for x in range(x0 + 1, x1):
            b[ly][x] = blk(ROCK, 0)
        if ly + 1 < H:
            b[ly + 1][x0] = blk(LIP_L, 1)
            b[ly + 1][x1] = blk(LIP_R, 1)
    for x, ya, yb in WALL_LADDERS:
        for y in range(ya, yb + 1):
            b[y][x] = blk(LADDER, 0, 0)
    marks = {}
    for name, (mx, my) in WALL_MOUTHS.items():
        for k in range(3):
            b[my][mx + k] = blk(MOUTH[0][k], 1)
            b[my + 1][mx + k] = blk(MOUTH[1][k], 1)
        b[my + 1][mx + 1] = blk(MOUTH[1][1], 0, 0)
        marks[name] = (mx + 1, my + 1)
    for x, y in WALL_ROCKS:
        b[y][x] = blk(514, 1)
    hx, hy = marks["hole"]
    marks["arrive"] = (hx, hy + 1)
    return b, marks
