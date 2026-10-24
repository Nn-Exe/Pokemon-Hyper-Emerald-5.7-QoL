"""Kitakami's drawn pieces (new art, 2026-10-15): a torii, a stone lantern and a red bridge, as index pictures with
one palette, cut into the 16x16 tiles the tileset makes metatiles of.

  torii         5 x 4 tiles. It stands on plain ground (the dirt path's middle piece or grass), its pillars in the
                outer columns; rows 0-1 (the beams) are drawn above people, so you pass under the gate; the pillars'
                lower two tiles stop you. The middle three columns of rows 2-3 are empty: plain ground.
  stone lantern 1 x 2 tiles (a toro): its foot stops you, its top is walked behind (as a tree's crown is).
  bridge        2 tiles wide, drawn whole (no ground shows through it): its north end, a middle piece repeated, its
                south end. You walk on it over the pond.

The colours are the paper lanterns' where they can be (tileset.lantern_cells), so the gates and the bridge cost the
palette no new red; the rest is gold, the stone's greys and the lamp's glow.
"""

# the palette: index -> colour. 1-6 are the paper lanterns' own colours.
RED, RED_D, BLACK, RED_L, WOOD, WOOD_D = 1, 2, 3, 4, 5, 6
GOLD, BLACK_L, STONE_L, STONE_M, STONE_D, GLOW, GLOW_W, OUT = 7, 8, 9, 10, 11, 12, 13, 14
COLOURS = {RED: (216, 48, 48), RED_D: (128, 32, 40), BLACK: (48, 32, 32), RED_L: (248, 168, 112),
           WOOD: (160, 104, 56), WOOD_D: (104, 64, 32),
           GOLD: (232, 192, 96), BLACK_L: (96, 80, 80), STONE_L: (216, 216, 208), STONE_M: (168, 168, 160),
           STONE_D: (112, 112, 112), GLOW: (248, 200, 96), GLOW_W: (255, 248, 216), OUT: (72, 40, 40)}


def canvas(w, h):
    return [[0] * w for _ in range(h)]


def rect(p, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p[y][x] = c


def outline(p, c=OUT):
    """a dark line round every drawn shape (on the clear pixels beside it), as the game's own pieces have"""
    h, w = len(p), len(p[0])
    out = [row[:] for row in p]
    for y in range(h):
        for x in range(w):
            if p[y][x] == 0 and any(0 <= x + dx < w and 0 <= y + dy < h and p[y + dy][x + dx]
                                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out[y][x] = c
    return out


def torii():
    """80 x 64, seen from the front: the black top beam with its ends turned up, the red beam under it, the
    plaque, the tie beam through the pillars, the pillars on black feet"""
    p = canvas(80, 64)
    for x0 in (6, 68):                                  # the pillars, lit from the left
        rect(p, x0, 10, x0 + 5, 57, RED)
        rect(p, x0, 10, x0, 57, RED_L)
        rect(p, x0 + 4, 10, x0 + 5, 57, RED_D)
        rect(p, x0 - 1, 57, x0 + 6, 62, BLACK)          # the feet
        rect(p, x0 - 1, 57, x0 + 6, 57, BLACK_L)
    rect(p, 2, 21, 77, 25, RED)                         # the tie beam (nuki), through the pillars
    rect(p, 2, 21, 77, 21, RED_L)
    rect(p, 2, 25, 77, 25, RED_D)
    rect(p, 3, 9, 76, 12, RED)                          # the beam under the top (shimaki)
    rect(p, 3, 12, 76, 12, RED_D)
    rect(p, 1, 4, 78, 8, BLACK)                         # the top beam (kasagi), its ends turned up
    rect(p, 1, 4, 78, 4, BLACK_L)
    rect(p, 0, 2, 3, 5, BLACK); rect(p, 76, 2, 79, 5, BLACK)
    rect(p, 0, 1, 1, 2, BLACK); rect(p, 78, 1, 79, 2, BLACK)
    rect(p, 0, 2, 2, 2, BLACK_L); rect(p, 77, 2, 79, 2, BLACK_L)
    rect(p, 35, 11, 44, 21, GOLD)                       # the plaque (gakuzuka): a gold frame, dark inside
    rect(p, 37, 13, 42, 19, BLACK)
    rect(p, 38, 14, 41, 18, OUT)
    return outline(p)


def stone_lantern():
    """16 x 32: the jewel on top, the roof with its corners turned up, the lit box, the post, the base"""
    p = canvas(16, 32)
    rect(p, 7, 1, 8, 3, STONE_M); p[1][7] = STONE_L    # the jewel
    for y, (a, b) in zip(range(4, 10), ((5, 10), (4, 11), (3, 12), (2, 13), (1, 14), (1, 14))):
        rect(p, a, y, b, y, STONE_M)
        p[y][a] = STONE_L
    rect(p, 1, 9, 14, 9, STONE_D)
    p[7][0] = STONE_M; p[7][15] = STONE_M               # the corners turned up
    rect(p, 4, 10, 11, 16, STONE_M)                     # the lit box
    rect(p, 4, 10, 4, 16, STONE_L)
    rect(p, 6, 11, 9, 15, GLOW)
    rect(p, 7, 12, 8, 14, GLOW_W)
    rect(p, 3, 17, 12, 18, STONE_D)                     # its platform
    rect(p, 3, 17, 12, 17, STONE_M)
    rect(p, 6, 19, 9, 26, STONE_M)                      # the post
    rect(p, 6, 19, 6, 26, STONE_L)
    rect(p, 9, 19, 9, 26, STONE_D)
    rect(p, 3, 27, 12, 28, STONE_M)                     # the base
    rect(p, 2, 29, 13, 30, STONE_D)
    rect(p, 3, 27, 12, 27, STONE_L)
    return outline(p)


def legend_board():
    """16 x 32, the legend's signboards (the user, 2026-10-17: "can the signboard be something unique from normal
    signboard, its hard to tell"): a notice board of dark wood under a little red shingle roof, a sheet of paper
    on it with lines of writing and a red seal, on two posts"""
    p = canvas(16, 32)
    rect(p, 3, 1, 12, 2, BLACK)                         # the ridge, its ends turned up
    rect(p, 3, 1, 12, 1, BLACK_L)
    rect(p, 1, 0, 2, 1, BLACK); rect(p, 13, 0, 14, 1, BLACK)
    for y, (a, b) in zip(range(3, 8), ((2, 13), (1, 14), (0, 15), (0, 15), (0, 15))):
        rect(p, a, y, b, y, RED_D if y % 2 == 0 else RED)          # the shingles, row on row
        p[y][a] = RED_L
    rect(p, 0, 8, 15, 8, BLACK)                         # the eave's shadow
    for x0 in (2, 12):                                  # the posts, from under the roof to the ground
        rect(p, x0, 9, x0 + 1, 30, WOOD)
        rect(p, x0 + 1, 9, x0 + 1, 30, WOOD_D)
        rect(p, x0 - 1, 30, x0 + 2, 31, BLACK)          # their feet
    rect(p, 1, 10, 14, 23, WOOD_D)                      # the board
    rect(p, 1, 10, 14, 10, WOOD)
    rect(p, 3, 12, 12, 21, GLOW_W)                      # the paper on it
    for y in (13, 15, 17):                              # lines of writing
        for x in range(4, 12):
            if (x + y) % 5:
                p[y][x] = BLACK_L
    rect(p, 4, 19, 8, 19, BLACK_L)
    rect(p, 10, 19, 11, 20, RED)                        # the seal
    return outline(p)


def bridge(n_mid=1):
    """32 wide: the north end (16 rows), n_mid middle pieces, the south end; no clear pixel, the pond does not show
    through it. Red rails along both sides with a post at every end, plank floor between."""
    h = 16 * (2 + n_mid)
    p = canvas(32, h)
    for y in range(h):                                  # the planks, across
        rect(p, 4, y, 27, y, WOOD_D if y % 4 == 3 else WOOD)
    for y in range(0, h, 4):
        p[y][5] = WOOD_D if y % 8 == 0 else p[y][5]
    for x0 in (0, 28):                                  # the rails
        rect(p, x0, 0, x0 + 3, h - 1, RED)
        rect(p, x0, 0, x0, h - 1, OUT)
        rect(p, x0 + 3, 0, x0 + 3, h - 1, OUT)
        rect(p, x0 + 1, 0, x0 + 1, h - 1, RED_L)
    for yp in (0, h - 6):                               # the posts at each end, capped
        for x0 in (0, 27):
            rect(p, x0, yp, x0 + 4, yp + 5, RED_D)
            rect(p, x0 + 1, yp + 1, x0 + 3, yp + 4, RED)
            rect(p, x0 + 1, yp + 1, x0 + 3, yp + 1, GOLD)
    for yp in range(16 + 6, h - 16, 16):                # a post halfway down each middle piece
        for x0 in (0, 27):
            rect(p, x0, yp, x0 + 4, yp + 3, RED_D)
            rect(p, x0 + 1, yp + 1, x0 + 3, yp + 2, RED)
    return p


def tiles(pic, w, h):
    """the picture cut into w x h tiles of 16 x 16 -> {(col, row): 16x16 picture}"""
    return {(c, r): [row[16 * c:16 * c + 16] for row in pic[16 * r:16 * r + 16]] for r in range(h) for c in range(w)}


def empty(t):
    return not any(v for row in t for v in row)


# Every tile of every piece: name -> {(col, row): (picture, attribute, blocked)}. The attribute's top bits are the
# layer type: 0 draws the top layer over people (you pass behind or under), 1 draws both under them (you stand in
# front). A tile with nothing drawn is not listed: the ground stays as it is.
NORMAL, COVERED = 0x0000, 0x1000


def pieces():
    out = {}
    t = tiles(torii(), 5, 4)
    out["torii"] = {}
    for (c, r), pic in t.items():
        if empty(pic):
            continue
        pillar = c in (0, 4)
        out["torii"][(c, r)] = (pic, COVERED if r == 3 else NORMAL, pillar and r >= 2)
    s = tiles(stone_lantern(), 1, 2)
    out["stone lantern"] = {(0, 0): (s[(0, 0)], NORMAL, False), (0, 1): (s[(0, 1)], COVERED, True)}   # (its top
                                                        # is walked behind, as a tree's crown is)
    b = tiles(bridge(1), 2, 3)
    out["bridge"] = {k: (pic, COVERED, False) for k, pic in b.items()}
    s = tiles(legend_board(), 1, 2)                     # as the stone lantern: its roof walked behind, its board
    out["legend board"] = {(0, 0): (s[(0, 0)], NORMAL, False), (0, 1): (s[(0, 1)], COVERED, True)}   # stops you
    return out


SIZE = {"torii": (5, 4), "stone lantern": (1, 2), "bridge": (2, 3), "legend board": (1, 2)}
