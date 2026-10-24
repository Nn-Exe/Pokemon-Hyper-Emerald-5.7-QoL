"""Kitakami's own secondary tileset: the Bellchime / Lavaridge set (0x083DF794) in Kitakami's colours, with the
homes in their own colour, Slateport's market pieces made a festival's, and paper lanterns.

The base is the hack's Lavaridge set, which Bellchime Trail, the Bell Tower's roof and Lavaridge share: 441
metatiles (512-952), its picture sheet full (504 of 512 cells; the last 8 are where the game draws an opening
door), palette rows 6-12. Kitakami gets a copy, so those places keep what they have:

  * colours (the user's picks, 2026-10-14): row 9 (the pagoda's and the halls' red wood) teal, row 10 (the pink
    volcanic rock) grey stone; row 11, the maples' and the conifers' reds and oranges, as they are (it was turned
    green until the user asked for the woods red and orange, 2026-10-15);
  * the homes: the longhouse metatiles again from 953 on, the same picture cells, their row-9 entries moved to a
    row of their own in slate grey (the user: "slate grey is preferred"); Kitakami Hall and the festival hall keep
    the teal ones;
  * the market (the user: "a market street to mimic the japanese festival"): Slateport's market pieces (its set
    0x083DF764), their cells copied into ours and their colours packed into free rows; the awnings' stripes, the
    floor and its curb are colours of the General set's rows 5, 1 and 0 there, so those entries become cells of
    ours too, recoloured red and white, and warm stone;
  * two lantern metatiles (new art, drawn here) over the market's floor;
  * the torii, the stone lanterns and the bridge (kart.py), each tile a metatile of its own over the ground it
    stands on (the ground's picture moved into the bottom layer, the art's in the top one).

What the maps do not use of the base is given up to make room: the cells only they used take the new pictures,
and their numbers take the drawn pieces (ours from 953 on are nearly all taken). build() checks that the maps use
nothing given up.
"""
import colorsys, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "paldea"))
import tiles as PT                                   # lz, lz_comp, Set
sys.path.insert(0, HERE)
import kart                                          # the torii, the stone lantern, the bridge

GENERAL = 0x083DF704
BASE = 0x083DF794                                    # the hack's Lavaridge set (Bellchime Trail, the Bell Tower)
BASE_COUNT = 441
SLATEPORT = 0x083DF764
FIRST = 512 + BASE_COUNT                             # 953: the first number of ours
CELLS = 504                                          # 512 less the 8 the game keeps for an opening door

LONGHOUSE = [824, 825, 828, 832, 833, 836, 840, 841, 844, 848, 849, 850, 851, 852, 871, 879, 887, 895]
MARKET = [514,                                       # the floor
          629, 630, 631, 637, 639, 645, 646, 647,    # its edge: corners and sides
          624, 534, 626, 632, 542, 634, 611, 612,    # the gate: its awning, its poles
          549, 535, 557, 543, 573, 620,              # a stall on the left edge: posts and awning
          533, 551, 541, 559, 619, 575, 633,         # ... on the right edge
          524, 539, 540, 547, 548, 830, 831, 836]    # goods: a pot, baskets, crates, flowers
# General-row colours the market's pieces draw with that become Kitakami's own (row, index): new colour
MARKET_RECOLOUR = {(5, 8): (216, 56, 56),           # the awnings' cyan stripes -> festival red
                   (5, 10): (248, 240, 228),         # the cream stripes -> white
                   (5, 5): (200, 184, 160),          # a pale shade at the awning's edge
                   (1, 2): (228, 216, 192),          # the floor: warm stone
                   (1, 3): (196, 180, 152),          # ... its shade
                   (0, 2): (236, 226, 204),          # the curb round it
                   (0, 3): (176, 160, 132)}


def rgb(v): return ((v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3)
def c555(r, g, b): return (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10


def hsv_map(v, fn):
    r, g, b = [c / 255 for c in rgb(v)]
    h, s, val = colorsys.rgb_to_hsv(r, g, b)
    h, s, val = fn(h, s, val)
    r, g, b = colorsys.hsv_to_rgb(h % 1, max(0, min(1, s)), max(0, min(1, val)))
    return c555(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def teal(h, s, v):  return (0.47, min(1, s * 0.95), min(1, v * 1.05)) if s > 0.15 else (h, s, v)
def stone(h, s, v): return (0.09, s * 0.30, v * 0.92)
def slate(h, s, v): return (0.62, s * 0.35, v * 0.85) if s > 0.15 else (h, s, v)
KITAKAMI_ROWS = {9: teal, 10: stone}


def lantern_cells():
    """The lantern: a red paper lantern on a wooden post, two metatiles tall, as 16x16 index pictures (0: see-
    through) with its own few colours. -> (top 16x16, bottom 16x16, colours {index: (r, g, b)})"""
    R, RD, CAP, HL, WOOD, WOODD = 1, 2, 3, 4, 5, 6
    cols = {R: (216, 48, 48), RD: (128, 32, 40), CAP: (48, 32, 32), HL: (248, 168, 112),
            WOOD: (160, 104, 56), WOODD: (104, 64, 32)}
    top = [[0] * 16 for _ in range(16)]
    bot = [[0] * 16 for _ in range(16)]
    for y in range(16):
        top[y][7], top[y][8] = WOOD, WOODD
    for y in range(13):
        bot[y][7], bot[y][8] = WOOD, WOODD
    for y in (13, 14):
        for x in range(6, 10):
            bot[y][x] = WOODD
    for x in range(4, 12):
        top[2][x] = WOODD
    shape = {4: (6, 9), 5: (5, 10), 6: (4, 11), 7: (4, 11), 8: (4, 11), 9: (4, 11), 10: (4, 11), 11: (4, 11),
             12: (5, 10), 13: (6, 9)}
    for y, (x0, x1) in shape.items():
        for x in range(x0, x1 + 1):
            top[y][x] = CAP if y in (4, 13) else RD if (y in (5, 12) or x in (x0, x1) or y in (7, 10)) else R
    for y in (6, 8, 9):
        top[y][6] = HL
    return top, bot, cols


def quadrant_cell(pic, qx, qy):
    """the 8x8 quadrant (qx, qy) of a 16x16 index picture as a 4bpp cell (32 bytes)"""
    out = bytearray()
    for y in range(8):
        row = pic[qy * 8 + y][qx * 8:qx * 8 + 8]
        for x in range(0, 8, 2):
            out.append(row[x] | row[x + 1] << 4)
    return bytes(out)


def can_hold(rom, ground):
    """Can a drawn piece stand on this ground (a metatile number, "floor" for the market's paving, None for none)?
    A General metatile whose top layer covers each quarter whole or not at all (grass, dirt, the paths); not one of
    the secondary set's, nor one with something standing on it (a tree's foot, a fence) - the editor's check."""
    if ground is None or ground == "floor":
        return True
    if ground >= 512:
        return False
    gen = PT.Set(rom, GENERAL)
    e = struct.unpack_from("<8H", rom, gen.metas + 16 * ground)
    for q in range(4):
        n = sum(1 for byte in gen.raw(e[4 + q] & 0x3FF) for v in (byte & 15, byte >> 4) if v)
        if n not in (0, 64):
            return False
    return True


class Built:
    """What build() makes: the tileset's parts and where each piece of ours went."""


def build(rom, needed, art=()):
    """needed: the base's metatiles (512-952) the maps draw with; art: the drawn pieces' tiles the maps use, as
    (piece, (col, row), the General metatile under it). -> Built: cells (512 x 32 bytes), metatiles (16 bytes each,
    512-...), attrs (512 halfwords), pals (16 rows x 16), ids {('home', base), ('market', theirs), ('lantern', 0 / 1),
    ('art', (piece, (col, row), ground)): ours}."""
    base, gen, sp = PT.Set(rom, BASE), PT.Set(rom, GENERAL), PT.Set(rom, SLATEPORT)
    needed = set(needed)

    def pixels(cell):
        s = set()
        for byte in cell:
            s.add(byte & 15); s.add(byte >> 4)
        s.discard(0)
        return s

    assert all(512 <= m < FIRST for m in needed), "not a metatile of the base set: %s" % sorted(m for m in needed if not 512 <= m < FIRST)

    # the base's rows in Kitakami's colours; the rows the maps need, and those left free
    pals = [list(r) for r in base.pals]
    for r, fn in KITAKAMI_ROWS.items():
        pals[r] = [pals[r][0]] + [hsv_map(v, fn) for v in pals[r][1:]]
    need_rows, need_cells, need_idx = set(), set(), {}
    for m in needed | set(LONGHOUSE):                  # (the homes are the longhouse's pieces: its cells and its
        for v in base.metatile(m):                     # colours outside row 9 must stay too)
            t, r = v & 0x3FF, v >> 12
            if t >= 512:
                need_cells.add(t)
            if 6 <= r <= 12:
                need_rows.add(r)
                need_idx.setdefault(r, set()).update(pixels(base.cell(t) if t >= 512 else gen.raw(t)))
    free_rows = [r for r in (6, 7, 8, 10, 11, 12, 9) if r not in need_rows]
    assert len(free_rows) >= 3, "the maps use rows %s of the base: no room for the homes and the market" % sorted(need_rows)

    out = Built()
    ids, nxt = {}, [FIRST]

    def new_id(key):
        ids[key] = nxt[0]; nxt[0] += 1
        return ids[key]

    metas = {}                                        # our number -> 8 entries
    attrs = list(struct.unpack_from("<%dH" % BASE_COUNT, rom, base.attrs)) + [0] * (512 - BASE_COUNT)
    # the hall's lower right corner (719) has under it the bottom of a Bellchime maple that grows behind the pagoda
    # there; Kitakami's has grass, as its lower left corner (750) has: 750's bottom layer mirrored
    lo = base.metatile(750)[:4]
    metas[719] = [lo[1] ^ 0x400, lo[0] ^ 0x400, lo[3] ^ 0x400, lo[2] ^ 0x400] + list(base.metatile(719)[4:])

    # ---- the homes: the longhouse's metatiles again, row 9 -> the homes' row, the same cells
    home_row = free_rows.pop(0)
    pals[home_row] = [base.pals[9][0]] + [hsv_map(v, slate) for v in base.pals[9][1:]]
    for m in LONGHOUSE:
        k = new_id(("home", m))
        metas[k] = [(v & 0x0FFF) | home_row << 12 if v >> 12 == 9 else v for v in base.metatile(m)]
        attrs[k - 512] = base.attr(m)

    # ---- the market and the lanterns: every entry that needs a cell of ours, and the colours it draws with
    uses = []                                         # {cell, pal (16 colours), idx, key: (our id, entry)}
    plain = {}                                        # (our id, entry) -> (cell bytes or a General cell number, row)

    for m in MARKET:
        k = new_id(("market", m))
        attrs[k - 512] = sp.attr(m)
        for e, v in enumerate(sp.metatile(m)):
            t, r = v & 0x3FF, v >> 12
            cell = sp.cell(t) if t >= 512 else gen.raw(t)
            idx = pixels(cell)
            if 6 <= r <= 12:
                uses.append({"cell": cell, "pal": list(sp.pals[r]), "idx": idx, "key": (k, e), "flip": v & 0x0C00})
            elif r <= 5 and any((r, i) in MARKET_RECOLOUR for i in idx):
                pal = list(gen.pals[r])
                for i in idx:
                    if (r, i) in MARKET_RECOLOUR:
                        pal[i] = c555(*MARKET_RECOLOUR[(r, i)])
                uses.append({"cell": cell, "pal": pal, "idx": idx, "key": (k, e), "flip": v & 0x0C00})
            else:
                plain[(k, e)] = (t if t < 512 else sp.cell(t), r, v & 0x0C00)
    # the lanterns: the floor's bottom layer (as the market's floor has it) under a lantern's picture
    top, bot, lcols = lantern_cells()
    lpal = [0] * 16
    for i, c in lcols.items():
        lpal[i] = c555(*c)
    floor_k = ids[("market", 514)]
    for n, pic in enumerate((top, bot)):
        k = new_id(("lantern", n))
        attrs[k - 512] = sp.attr(514) & 0x0FFF | 0x1000   # both layers under people ("covered"): a post south
                                                      # of you must not be drawn over your head
        for e in range(4):                           # layer 0: the floor, as the market's floor tile draws it
            src = [u for u in uses if u["key"] == (floor_k, e)]
            if src:
                uses.append(dict(src[0], key=(k, e)))
            else:
                plain[(k, e)] = plain[(floor_k, e)]
        for e in range(4):                           # layer 1: the lantern
            cell = quadrant_cell(pic, e % 2, e // 2)
            idx = pixels(cell)
            if idx:
                uses.append({"cell": cell, "pal": lpal, "idx": idx, "key": (k, 4 + e), "flip": 0})
            else:
                plain[(k, 4 + e)] = (0, 0, 0)        # nothing drawn

    # ---- the drawn pieces (kart.py): each tile with the ground under it, numbered with base metatiles the maps
    # do not use (Kitakami's set is a copy: no other map sees those numbers)
    gmetas = lambda m: struct.unpack_from("<8H", rom, gen.metas + 16 * m)
    drawn_px = lambda t: sum(1 for byte in gen.raw(t) for n in (byte & 15, byte >> 4) if n)

    def ground_bottom(m):
        """General metatile m's picture, in the bottom layer alone: per quarter, its bottom layer where its top
        one draws nothing, its top layer where that covers the quarter (grass draws its picture on top)"""
        e, out_ = gmetas(m), []
        for q in range(4):
            lo, hi = e[q], e[4 + q]
            n = drawn_px(hi & 0x3FF)
            assert n in (0, 64), "metatile %d draws part of a quarter on top: no ground for a drawn piece" % m
            out_.append(hi if n else lo)
        return out_

    pool = [m for m in range(512, FIRST) if m not in needed and m not in LONGHOUSE]
    apal = [0] * 16
    for i, c in kart.COLOURS.items():
        apal[i] = c555(*c)
    drawn = kart.pieces()
    for key in sorted(art, key=repr):
        piece, part, ground = key
        pic, attr, _ = drawn[piece][part]
        assert pool, "no metatile number left for the drawn pieces"
        k = pool.pop(0)
        ids[("art", key)] = k
        attrs[k - 512] = attr
        whole = all(v for row in pic for v in row)    # a piece drawn whole (the bridge) needs no ground
        if whole:
            for e in range(4):
                plain[(k, 4 + e)] = (0, 0, 0)
        elif ground == "floor":                       # on the market's paving (the shrines' courts): its bottom
            for e in range(4):                        # layer, as the paper lanterns have it
                src = [u for u in uses if u["key"] == (floor_k, e)]
                if src:
                    uses.append(dict(src[0], key=(k, e)))
                else:
                    plain[(k, e)] = plain[(floor_k, e)]
        else:
            for e, v in enumerate(ground_bottom(ground)):
                plain[(k, e)] = (v & 0x3FF, v >> 12, v & 0x0C00)
        for e in range(4):
            cell = quadrant_cell(pic, e % 2, e // 2)
            idx = pixels(cell)
            slot = e if whole else 4 + e
            if idx:
                uses.append({"cell": cell, "pal": apal, "idx": idx, "key": (k, slot), "flip": 0})
            else:
                plain[(k, slot)] = (0, 0, 0)

    # ---- the colours: each use's colours in one row; a source palette's uses together when they fit
    held = {r: [None] * 16 for r in free_rows}
    spare_rows = [r for r in (12, 10, 11) if r in need_rows and len(need_idx.get(r, ())) < 15]
    for r in spare_rows:                             # the colours the maps draw with stay where they are
        held[r] = [pals[r][i] if i in need_idx[r] else None for i in range(16)]
        held[r][0] = None
    pack_rows = free_rows + spare_rows
    groups = {}
    for u in uses:
        u["cols"] = {u["pal"][i] for i in u["idx"]}
        groups.setdefault(tuple(u["pal"]), []).append(u)

    def fit(row, cols):
        at, new = {}, []
        for c in cols:
            if c in row[1:]:
                at[c] = row.index(c, 1)
        empty = [i for i in range(1, 16) if row[i] is None]
        for c in sorted(cols):
            if c in at:
                continue
            if not empty:
                return None
            i = empty.pop(0); at[c] = i; new.append((i, c))
        return at, new

    def place(us, cols):
        best = None
        for r in pack_rows:
            got = fit(held[r], cols)
            if got and (best is None or len(got[1]) < len(best[2])):
                best = (r, got[0], got[1])
        if best is None:
            return False
        r, at, new = best
        for i, c in new:
            held[r][i] = c
        for u in us:
            u["row"], u["at"] = r, at
        return True

    for key, us in sorted(groups.items(), key=lambda kv: -len(set().union(*[u["cols"] for u in kv[1]]))):
        if place(us, set().union(*[u["cols"] for u in us])):
            continue
        for u in sorted(us, key=lambda u: -len(u["cols"])):
            assert place([u], u["cols"]), "the market's colours do not fit in rows %s" % pack_rows
    rows_used = sorted(r for r in free_rows if any(c is not None for c in held[r][1:]))
    for r in rows_used:
        pals[r] = [base.pals[r][0]] + [c if c is not None else 0 for c in held[r][1:]]
    for r in spare_rows:                             # the maps' colours as they were, the market's in the gaps
        pals[r] = [pals[r][i] if (i == 0 or i in need_idx[r]) else (held[r][i] if held[r][i] is not None else 0)
                   for i in range(16)]
    rows_used = sorted(set(rows_used) | {r for r in spare_rows if any(held[r][i] is not None and i not in need_idx[r]
                                                                      for i in range(1, 16))})

    # ---- the cells: the ones the maps need stay; each new picture goes into one no needed metatile uses
    sheet = bytearray(base.cells[:CELLS * 32].ljust(CELLS * 32, b"\0"))
    free = [512 + i for i in range(CELLS) if 512 + i not in need_cells]
    placed = {}

    def cell_number(c):
        if c not in placed:
            assert free, "Kitakami's set ran out of picture cells"
            n = free.pop(0)
            sheet[(n - 512) * 32:(n - 512) * 32 + 32] = c
            placed[c] = n
        return placed[c]

    entries = {}
    for u in uses:
        to = [0] * 16
        for i in u["idx"]:
            to[i] = u["at"][u["pal"][i]]
        cell = bytes(to[b & 15] | to[b >> 4] << 4 for b in u["cell"])
        entries[u["key"]] = cell_number(cell) | u["flip"] | u["row"] << 12
    for key, (t, r, flip) in plain.items():
        n = t if isinstance(t, int) else cell_number(t)
        entries[key] = n | flip | r << 12
    for (_, m), k in ids.items():
        if k not in metas:
            metas[k] = [entries[(k, e)] for e in range(8)]

    top_id = nxt[0] - 1
    assert top_id <= 1023
    table = bytearray(rom[base.metas:base.metas + 16 * BASE_COUNT]) + bytes(16 * (top_id + 1 - FIRST))
    for k, e in metas.items():
        struct.pack_into("<8H", table, 16 * (k - 512), *e)
    out.cells = bytes(sheet)
    out.metatiles = bytes(table)
    out.attrs = attrs
    out.pals = pals
    out.ids = ids
    out.free_cells_left = len(free)
    out.numbers_left = (1023 - top_id) + len(pool)  # ours past the base's, and base numbers no map uses
    out.rows = {"needed": sorted(need_rows), "homes": home_row, "market": rows_used,
                "colours left": sum(1 for r in pack_rows for c in held[r][1:] if c is None)}
    out.given_up = sorted(m for m in range(512, FIRST) if m not in needed and any(
        (v & 0x3FF) in placed.values() for v in base.metatile(m)))
    return out


def install(blob, built):
    """The tileset into blob: its 24 bytes, the cells (compressed), palettes, metatiles, attributes. -> its key."""
    pt = blob.put(("kitakami", "cells"), PT.lz_comp(built.cells))
    pp = blob.put(("kitakami", "palettes"), struct.pack("<256H", *[c for row in built.pals for c in row]))
    pm = blob.put(("kitakami", "metatiles"), built.metatiles)
    pa = blob.put(("kitakami", "attributes"), struct.pack("<512H", *built.attrs))
    blob.put(("tileset", "kitakami"), struct.pack("<BBHIIIII", 1, 1, 0, pt, pp, pm, pa, 0))
    return ("tileset", "kitakami")
