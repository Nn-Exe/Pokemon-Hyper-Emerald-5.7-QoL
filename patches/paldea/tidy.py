"""Puts the right piece on every edge of the crater's painted ground: terraces, dirt paths, puddles.

A map is drawn from pieces that only fit together one way: a terrace's top left corner is one tile, its rim
another, the place where the rim meets a side a third. Painted by hand, tile by tile, an edge ends up with a piece
that almost fits, and "almost" shows: a sand-coloured corner on the grass, a path's border running through its
middle, a puddle with a gap in its rim. The user, after painting on test 12: "maybe you need to bake everything
balance like corner of each tiles, don't make graphical glitch". So the shape is taken from what is painted, and
every piece is worked out again from the shape, by the rules world.py draws the map with:

  terraces  a tile's level comes from its height (3 the floor, 5 and 7 the terraces); a raised tile with lower
            ground beside it gets the piece its place asks for (world.terrace_kind), with that piece's own walking
            and the terrace's height. A terrace piece left where no edge is any more becomes grass. Steps stay
            where they are; so does anything that is not ground (a tree, a boulder, a house).
  paths     every tile of the dirt family gets the piece its neighbours ask for (world.edge_piece).
  puddles   likewise, from the nine pieces of the game's puddles.

Lakes and ponds are left alone: their shore is drawn on the tiles below the water, and a pond may only widen
going down. Only the crater has these families; the wall and the rooms are not touched. Trees are not put right
either, but cut_trees() finds the ones painting has cut in half, and the editor says so.

Whatever the map was built with and nobody painted is left alone if it is not of these families' own pieces
(the entrance's mound is the Giant Chasm's, rock on rock, and keeps its rock pieces), and on the map as built
nothing changes at all.

crater(blocks, drawn, levels, dirt) changes `blocks` in place and returns what it changed. editor.py's "Tidy the
edges" button and the `count` it shows after a check both come here.
"""
import world as W

STEP, GROUND, WALL = W.LEVEL_STEP, W.GROUND, W.WALL_LEVEL
STAIRS = W.TERRACE["stairs"]
PIECES = set(W.TERRACE.values()) - {STAIRS}
TERRACE_ALL = PIECES | set(W.OLD_TERRACE)               # (the old ones: taken for a terrace's piece, never put)
PLAIN = set(W.PLAIN) | {W.TALL}                         # ground an edge may be drawn over
DIRT_ALL = set(W.DIRT.values())
# the game's puddles (behaviour 0x16: walked through, with a splash and a reflection): layout 536 has a large one
PUDDLE = {"tl": 200, "t": 431, "tr": 201, "l": 216, "c": 319, "r": 210, "bl": 208, "b": 217, "br": 209}
PUDDLE_ALL = set(PUDDLE.values()) | {202, 218}          # (202 and 218: joins of two puddles, never put)
HEIGHTS = {GROUND + STEP * k: k for k in range(0, 5)}   # a height the map uses for a level: 3, 5, 7, 9, 11


def levels_now(blocks, drawn, levels):
    """The level of every tile with the paint on: as sketched where nothing was painted, and where something
    was, by the height it was painted with (a terrace's piece or ground you can walk on; a piece taken from the
    list has no height worth reading, and keeps the sketch's level)."""
    out = [list(r) for r in levels]
    for y, row in enumerate(blocks):
        for x, v in enumerate(row):
            if v == drawn[y][x] or levels[y][x] >= WALL:
                continue
            t, solid, h = v & 0x3FF, (v >> 10) & 3, v >> 12
            if h in HEIGHTS and (not solid or t in TERRACE_ALL) and not (t in TERRACE_ALL and h == GROUND):
                out[y][x] = HEIGHTS[h]
    return out


def crater(blocks, drawn, levels, dirt=frozenset()):
    """blocks: the crater's ground with the paint on (changed in place); drawn: the ground as built; levels: the
    level of every tile as built (world.crater_levels); dirt: the tiles the sketch has a path on
    (world.crater_dirt). Returns [(x, y, block before, block after)]."""
    h, w = len(blocks), len(blocks[0])
    lv = levels_now(blocks, drawn, levels)
    changed = []

    def put(x, y, v):
        if blocks[y][x] != v:
            changed.append((x, y, blocks[y][x], v))
            blocks[y][x] = v

    tile = lambda x, y: blocks[y][x] & 0x3FF if 0 <= x < w and 0 <= y < h else -1
    level = lambda x, y: lv[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]
    # terraces
    for y in range(h):
        for x in range(w):
            L, t = lv[y][x], tile(x, y)
            if L >= WALL or t == STAIRS:
                continue
            kind = None
            if L > 0:
                hi = lambda dx, dy: level(x + dx, y + dy) >= L
                if (hi(0, -1) or hi(0, 1)) and (hi(-1, 0) or hi(1, 0)):     # (one tile wide or tall: no pieces)
                    kind = W.terrace_kind(hi)
            # a terrace's piece: one of the family, or an old one that somebody painted (the mound's are built)
            piece = t in PIECES or (t in W.OLD_TERRACE and blocks[y][x] != drawn[y][x])
            if kind and (piece or t in PLAIN):
                put(x, y, W.blk(W.TERRACE[kind], 0 if kind in W.TERRACE_WALK else 1, GROUND + STEP * L))
            elif not kind and piece:
                put(x, y, W.blk(W.GRASS, 0, GROUND + STEP * L))
    # dirt paths and puddles: the piece changes, the walking and the height stay
    # (a path goes on under a terrace's edge that was drawn over it: its pieces beside the edge say so)
    under = {xy for xy in dirt if drawn[xy[1]][xy[0]] & 0x3FF not in DIRT_ALL}
    for family, table, piece in ((DIRT_ALL, W.DIRT, W.edge_piece), (PUDDLE_ALL, PUDDLE, puddle_piece)):
        if family is DIRT_ALL:
            test = lambda x, y: tile(x, y) in DIRT_ALL or ((x, y) in under and blocks[y][x] == drawn[y][x])
        else:
            test = lambda x, y: tile(x, y) in family
        for y in range(h):
            for x in range(w):
                if tile(x, y) in family:
                    p = piece(test, x, y, table)
                    if p is not None:
                        put(x, y, blocks[y][x] & 0xFC00 | p)
    return changed


def puddle_piece(test, x, y, table):
    """A puddle's piece for (x, y); None for a puddle one tile wide or tall (the game has no pieces for those)."""
    n, s_, wl, e = test(x, y - 1), test(x, y + 1), test(x - 1, y), test(x + 1, y)
    if not (n or s_) or not (wl or e):
        return None
    row = "t" if not n else "b" if not s_ else ""
    col = "l" if not wl else "r" if not e else ""
    return table[row + col or "c"]


def count(blocks, drawn, levels, dirt=frozenset()):
    """How many tiles crater() would change, without changing any."""
    return len(crater([list(r) for r in blocks], drawn, levels, dirt))


# A tree is two tiles wide and three tall: a top (on grass, over tall grass or against the wall), a middle, a
# trunk; where one stands two rows below another they share a row. The left halves (the right is the next number):
TREE_TOPS = {W.TREE_TOP[k][0] for k in W.TREE_TOP}
TREE_MID, TREE_OVER, TREE_TRUNK = W.TREE_MID[0], W.TREE_OVERLAP[0], W.TREE_TRUNK[0]
TREE_LEFT = TREE_TOPS | {TREE_MID, TREE_OVER, TREE_TRUNK}


def tree_faults(blocks):
    """The tiles of trees that lack the tile a tree has beside, above or below them (the map's edge counts as
    having it)."""
    h, w = len(blocks), len(blocks[0])
    t = lambda x, y: blocks[y][x] & 0x3FF if 0 <= x < w and 0 <= y < h else None
    out = set()
    for y in range(h):
        for x in range(w):
            v = t(x, y)
            left = v if v in TREE_LEFT else v - 1 if v - 1 in TREE_LEFT else None
            if left is None:
                continue
            lx = x if v == left else x - 1
            if t(lx, y) not in (left, None) or t(lx + 1, y) not in (left + 1, None):
                out.add((x, y))
                continue
            up, dn = t(lx, y - 1), t(lx, y + 1)
            if left in TREE_TOPS:
                ok = dn in (TREE_MID, None)
            elif left == TREE_MID:
                ok = (up in TREE_TOPS or up in (TREE_OVER, None)) and dn in (TREE_TRUNK, TREE_OVER, None)
            elif left == TREE_OVER:
                ok = up in (TREE_MID, None) and dn in (TREE_MID, None)
            else:
                ok = up in (TREE_MID, None)
            if not ok:
                out.add((x, y))
    return out


def cut_trees(blocks, drawn):
    """The tree tiles that painting has left without their other half or their rows above and below: what was
    not so on the map as built. (Nothing is put right here: the tree's missing part could be anything.)"""
    return sorted(tree_faults(blocks) - tree_faults(drawn))
