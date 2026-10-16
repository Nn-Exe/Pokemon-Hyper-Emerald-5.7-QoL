"""Tiles for the craters taken from other maps of the game (test 19): the user on test 18, wanting to decorate
the map: "I need more tiles as well", and of the ways offered chose "pick from any map" for the two craters.

A map has two tilesets, 512 metatiles each (a metatile: the 16x16 tile a map is made of; eight 8x8 picture cells
in two layers, each with a palette row). The craters' are the game's General (primary; nearly every outdoor map of
the hack has it) and Petalburg's (secondary: 144 metatiles, 504 picture cells, palette rows 6-12). A metatile of
another map's secondary set can be had in the craters if its picture cells and its colours are put into the
craters' secondary set, so the craters get a secondary set of their own (both times share it; the tint is laid
over its palettes as over any other):

  * metatiles 512-655 are Petalburg's, as they were; 656-1023 are the ones taken, each with the number tiles.txt
    gives it for good (painted ground is kept by number: ground.py);
  * a taken metatile's cells of the primary set and its palette rows 0-5 need nothing (the same General); its
    cells of its own secondary set are copied into free cells of ours, and the colours it draws with from the
    palette rows 6-12 need a place in a row of ours. A row is 15 colours and a piece seldom uses all of its
    row's, so the colours are packed (build(): several source rows share one of ours, and the cells' pixels are
    renumbered to where their colours went);
  * there is only so much room. Petalburg's 144 metatiles use 254 of the 504 cells and all seven rows; the
    craters as built use 70 cells and two rows (9 and 12: the stations' houses), which leaves 433 cells and five
    rows, 75 colours. What a taken metatile needs is found first among what no Petalburg metatile uses, then by
    giving up Petalburg metatiles that are nowhere on the craters' ground (they leave the editor's list; one
    that is on the ground is never given up). The colours run out long before the cells do (a corner of Fortree
    City, its Pokemon Centre and a tree house: 29), so when they do not fit, shades one step apart, then two,
    share a colour (JOIN): only colours of different pieces, never two that are drawn together (a thatched
    roof's straw is shades a step apart). When that is not enough either, TilesError says what does not fit;
  * a taken tile does what it did where it came from (water, tall grass, a ledge, ice), with the walking and the
    height the editor paints it with. A door or a cave mouth is a picture only: the craters have no way through
    there. The places for a secret base are made plain (NO_USE).

The last 8 of the 512 cells are where the game draws an opening door (the stations' doors): never used.
A set's own animations (a sea's waves, a city's lights) do not come along: the taken tiles show their first frame.

tiles.txt, beside placements.txt and ground.txt (the editor writes it; "Take from another map"):

    [crater]
    656 = 35/45 713        # our number = the map it was taken from (group/number), its metatile there
"""
import os, re, struct

NAME = "tiles.txt"
MAP_GROUPS = 0x00A54698
GENERAL = 0x083DF704                    # the primary tileset of the craters and of the maps tiles can be taken from
BASE = 0x083DF71C                       # the craters' secondary tileset (Petalburg's)
BASE_COUNT = 144                        # its metatiles: 512-655
FIRST, LAST = 512 + BASE_COUNT, 1023    # the numbers taken metatiles get
CELLS = 504                             # picture cells to fill: 512 less the 8 of the door animations
ROW_ORDER = (6, 7, 8, 10, 11, 9, 12)    # the secondary's palette rows, in the order they are given to taken tiles
                                        # (9 and 12, the stations' houses', last)
JOIN = (0, 1, 2)                        # shades this many steps (of 32) apart may share a colour: tried in turn,
                                        # the first that lets every taken tile have its colours
NO_USE = set(range(0x90, 0x9E))        # what a taken tile does that it must not do in the craters: the places for
                                        # a secret base (a tree, a shrub, a dent in a cliff: Secret Power on one
                                        # looks for the base the map has there, and the craters have none). Such
                                        # a tile comes along as the picture it is and does nothing.
SECTIONS = {"crater": ["past", "future"]}
TITLE = {"crater": "crater"}

HEAD = """\
# Area Zero: tiles taken from other maps of the game, to paint the craters with.
# The editor writes this file ("Paint the ground" > "Take from another map"). A line is
#     our number = group/number of the map it was taken from, its tile number there
# Our numbers stay as they are for good: ground.txt keeps painted tiles by number.
# To give every taken tile up, delete this file (and what was painted with them shows as a blank tile:
# paint over it, or use the editor's "Put this map's ground back").
"""


class TilesError(Exception):
    """tiles.txt cannot be read, or what it asks for does not fit; .lines says why, in plain words."""

    def __init__(self, lines):
        self.lines = [lines] if isinstance(lines, str) else list(lines)
        Exception.__init__(self, "\n".join(self.lines))


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


# ------------------------------------------------------------------------------------------------ the file
def text(imports):
    """The file's text for {section: [(our number, group, map number, its metatile), ...]}."""
    out = [HEAD]
    for sec in SECTIONS:
        rows = sorted((imports or {}).get(sec, []))
        out.append("\n[%s]" % TITLE[sec])
        out += ["%d = %d/%d %d" % r for r in rows]
    return "\n".join(out) + "\n"


def parse(src, where=NAME):
    out = {sec: [] for sec in SECTIONS}
    sec = None
    names = {t.lower(): k for k, t in TITLE.items()}
    for n, raw in enumerate(src.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.fullmatch(r"\[(.+)\]", line)
        if m:
            sec = names.get(m.group(1).strip().lower())
            if sec is None:
                raise TilesError("%s, line %d: there is no section [%s]. The sections are: %s." % (
                    where, n, m.group(1).strip(), ", ".join("[%s]" % t for t in TITLE.values())))
            continue
        m = re.fullmatch(r"(\d+)\s*=\s*(\d+)\s*/\s*(\d+)\s+(\d+)", line)
        if not m or sec is None:
            raise TilesError("%s, line %d: \"%s\" is not \"our number = group/number tile\" under a [section]." % (
                where, n, line))
        ours, g, num, mid = (int(v) for v in m.groups())
        if not FIRST <= ours <= LAST:
            raise TilesError("%s, line %d: a taken tile's number is %d to %d, not %d." % (where, n, FIRST, LAST, ours))
        if not 512 <= mid <= 1023:
            raise TilesError("%s, line %d: tile %d of map %d/%d is of the game's General set, which the craters "
                             "have already: only a map's own tiles (512 to 1023) are taken." % (where, n, mid, g, num))
        if any(r[0] == ours for r in out[sec]):
            raise TilesError("%s, line %d: the number %d is given twice." % (where, n, ours))
        out[sec].append((ours, g, num, mid))
    return {sec: sorted(rows) for sec, rows in out.items()}


def load(path=None):
    """{section: [(our number, group, map number, its metatile)]}; no file: nothing taken."""
    if path is None or not os.path.exists(path):
        return {sec: [] for sec in SECTIONS}
    with open(path, encoding="utf-8-sig") as f:
        return parse(f.read(), os.path.basename(path))


# ------------------------------------------------------------------------------------------------ the ROM
def lz(rom, off):
    """GBA LZ77 (0x10). A few of the hack's tilesets are stored raw with the compressed flag set: no header, raw."""
    if rom[off] != 0x10:
        return bytes(rom[off:off + 512 * 32])
    size = u32(rom, off) >> 8
    out = bytearray()
    p = off + 4
    while len(out) < size:
        flags = rom[p]; p += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = rom[p], rom[p + 1]; p += 2
                start = len(out) - (((b1 & 0xF) << 8 | b2) + 1)
                if start < 0:
                    return bytes(out) + bytes(size - len(out))
                for k in range((b1 >> 4) + 3):
                    out.append(out[start + k])
            else:
                out.append(rom[p]); p += 1
    return bytes(out[:size])


def lz_comp(data):
    """BIOS LZ77, greedy, never a distance of 1 (LZ77UnCompVram cannot read one back): gen9_patch.lz_comp."""
    data, n = bytes(data), len(data)
    out = bytearray([0x10, n & 0xFF, n >> 8 & 0xFF, n >> 16 & 0xFF])
    seen, i = {}, 0

    def remember(pos):
        if pos + 3 <= n:
            seen.setdefault(data[pos:pos + 3], []).append(pos)

    while i < n:
        flag_at, flags = len(out), 0
        out.append(0)
        for bit in range(8):
            if i >= n:
                break
            best, dist, most = 0, 0, min(18, n - i)
            if most >= 3:
                for j in reversed(seen.get(data[i:i + 3], ())):
                    if i - j > 4096:
                        break
                    if i - j < 2:
                        continue
                    k = 3
                    while k < most and data[j + k] == data[i + k]:
                        k += 1
                    if k > best:
                        best, dist = k, i - j
                        if k == most:
                            break
            if best >= 3:
                flags |= 0x80 >> bit
                out += bytes([(best - 3) << 4 | (dist - 1) >> 8, (dist - 1) & 0xFF])
                for k in range(best):
                    remember(i + k)
                i += best
            else:
                out.append(data[i])
                remember(i)
                i += 1
        out[flag_at] = flags
    return bytes(out) + bytes(-len(out) % 4)


def header_of(rom, g, n):
    return u32(rom, u32(rom, MAP_GROUPS + 4 * g) - 0x08000000 + 4 * n) - 0x08000000


def tilesets_of(rom, g, n):
    """(primary, secondary) tileset addresses of a map."""
    lay = u32(rom, header_of(rom, g, n)) - 0x08000000
    return u32(rom, lay + 16), u32(rom, lay + 20)


class Set:
    """A secondary tileset as the ROM has it: its picture cells, palette rows, metatiles and attributes."""

    def __init__(self, rom, addr):
        o = addr - 0x08000000
        self.addr = addr
        tiles, pals, metas, attrs = (u32(rom, o + 4 + 4 * k) - 0x08000000 for k in range(4))
        self.cells = lz(rom, tiles) if rom[o] else bytes(rom[tiles:tiles + 512 * 32])
        self.pals = [struct.unpack_from("<16H", rom, pals + 32 * r) for r in range(16)]
        self.rom, self.metas, self.attrs = rom, metas, attrs

    def cell(self, t):                                      # the 32 bytes of picture cell t (512 on)
        b = self.cells[(t - 512) * 32:(t - 512) * 32 + 32]
        return b + bytes(32 - len(b))

    def raw(self, i):                                       # ...of cell i of the sheet (the primary set's: 0 on)
        b = self.cells[i * 32:i * 32 + 32]
        return b + bytes(32 - len(b))

    def metatile(self, mid):                                # its eight entries
        return struct.unpack_from("<8H", self.rom, self.metas + 16 * (mid - 512))

    def attr(self, mid):
        return u16(self.rom, self.attrs + 2 * (mid - 512))


class Custom:
    """The craters' own secondary set: what the build writes, and what the editor wants to know."""


def build(rom, imports, needed, where="the craters"):
    """The secondary set with `imports` [(our number, group, map number, its metatile)] in it. needed: Petalburg
    metatiles (512-655) that must stay as they are (the ones on the ground). Raises TilesError if it does not fit."""
    base = Set(rom, BASE)
    sets = {}
    need = {m - 512 for m in needed if 512 <= m < FIRST}
    refs, rows = [], []                                     # per Petalburg metatile: its cells (512 on), its rows
    for k in range(BASE_COUNT):
        e = base.metatile(512 + k)
        refs.append({v & 0x3FF for v in e if (v & 0x3FF) >= 512})
        rows.append({v >> 12 for v in e if 6 <= v >> 12 <= 12})
    need_rows = set().union(*[rows[k] for k in need]) if need else set()
    need_cells = set().union(*[refs[k] for k in need]) if need else set()

    # what each taken metatile needs: its entries, its attribute, the cells' pictures, the rows' colours
    taken, problems = [], []
    for ours, g, n, mid in sorted(imports):
        try:
            prim, sec = tilesets_of(rom, g, n)
        except (struct.error, IndexError):
            problems.append("tile %d: there is no map %d/%d." % (ours, g, n))
            continue
        if prim != GENERAL:
            problems.append("tile %d: map %d/%d is not drawn with the General set the craters have; its tiles "
                            "cannot be taken." % (ours, g, n))
            continue
        s = sets.get(sec) or sets.setdefault(sec, Set(rom, sec))
        attr = s.attr(mid)
        if attr & 0xFF in NO_USE:
            attr &= 0xFF00
        taken.append((ours, s, mid, s.metatile(mid), attr))
    if problems:
        raise TilesError(problems)

    gen = Set(rom, GENERAL)

    def pixels_used(cell):                                  # the colour indexes its 64 pixels use (not 0: see-through)
        out = set()
        for byte in cell:
            out.add(byte & 15)
            out.add(byte >> 4)
        out.discard(0)
        return out

    # The palette rows. A row holds 15 colours and a piece seldom uses them all (a corner of Fortree City: 29
    # colours in three rows), so the colours are packed: rows 0-5 are General's and the rows of Petalburg's that
    # the ground needs stay as they are (fixed: a cell whose colours one of them has costs nothing); the other
    # rows 6-12 start empty and take the colours the taken tiles use. A cell's pixels are renumbered to where its
    # colours ended up in its row, which makes it a cell of ours even when it was one of General's.
    # When they do not all fit, shades a step apart (of the 32 a colour's red, green and blue have: nothing the
    # eye tells apart) share a colour, then shades two steps apart (JOIN); only then is it too much. Only colours
    # of different pieces are joined, never two that are drawn together (pack()).
    fixed = {r: list(gen.pals[r]) for r in range(6)}
    fixed.update({r: list(base.pals[r]) for r in need_rows})
    free_rows = [r for r in ROW_ORDER if r not in need_rows]
    uses, groups = {}, {}                                    # (taken tile, entry) -> use; (set, its row) -> uses
    for ti, (ours, s, mid, entries, attr) in enumerate(taken):
        for k, v in enumerate(entries):
            t, r = v & 0x3FF, v >> 12
            if 6 <= r <= 12:
                cell = s.cell(t) if t >= 512 else gen.raw(t)
                idx = pixels_used(cell)
                u = {"cell": cell, "pal": s.pals[r], "idx": idx, "cols": {s.pals[r][i] for i in idx}, "ours": ours}
                uses[ti, k] = u
                groups.setdefault((s.addr, r), []).append(u)
    whole = lambda us: set().union(*[u["cols"] for u in us])
    apart = lambda p, q: max(abs((p >> sh & 31) - (q >> sh & 31)) for sh in (0, 5, 10))

    def pack(join, by_cell):
        """Every use its row ("row") and where each of its colours is there ("at"), with shades up to `join`
        steps apart sharing a colour; -> the free rows' colours by index (None: still empty), or None and the use
        that found no room. Colours that are drawn together never share one: the straw of a thatched roof is
        shades a step apart, and joined it was one flat colour. So what is placed together (a source row's
        colours, or with by_cell a cell's) gets a colour of the row each.
        A source row at a time keeps most cells as they are (the colours keep their indexes); a cell at a time
        packs tighter (two rows of a set mostly share colours, and a cell uses a few of its row's) and costs
        picture cells: every cell whose colours moved is one of ours."""
        held = {r: [None] * 16 for r in free_rows}

        def fit(row, cols, pal):
            """{colour: its index in the row} and the [(index, colour)] the row would have to take in for it;
            None: no room. A colour goes to itself, else to the nearest shade within `join` that no other of
            these has, else to an empty index: the one it had in its own palette if that is empty (a cell whose
            colours all keep their index stays as it is)."""
            at, new, used = {}, [], set()
            for c in sorted(cols):
                if c in row[1:]:
                    at[c] = row.index(c, 1)
                    used.add(at[c])
            for c in sorted(cols):
                if c in at or not join:
                    continue
                near = [(apart(q, c), i) for i, q in enumerate(row) if i and q is not None and i not in used]
                near = [n for n in near if n[0] <= join]
                if near:
                    at[c] = min(near)[1]
                    used.add(at[c])
            for c in sorted(cols):
                if c in at:
                    continue
                empty = [i for i in range(1, 16) if row[i] is None and i not in used]
                if not empty:
                    return None
                own = [i for i in empty if pal[i] == c]
                at[c] = (own or empty)[0]
                used.add(at[c])
                new.append((at[c], c))
            return at, new

        def place(cols, pal):
            """(row, where the colours are in it, what it takes in): a fixed row that has them all, else the
            used free row that has to take in the fewest, else an empty one; None if there is none."""
            for r in sorted(fixed):
                got = fit(fixed[r], cols, pal)
                if got:
                    return r, got[0], got[1]
            best = None
            for r in free_rows:
                if any(c is not None for c in held[r][1:]):
                    got = fit(held[r], cols, pal)
                    if got and (best is None or len(got[1]) < len(best[2])):
                        best = (r, got[0], got[1])
            if best:
                return best
            r = next((r for r in free_rows if not any(c is not None for c in held[r][1:])), None)
            got = fit(held[r], cols, pal) if r is not None else None
            return (r, got[0], got[1]) if got else None

        def put(us, cols):
            got = place(cols, us[0]["pal"])
            if got is None:
                return False
            row, at, new = got
            for i, c in new:
                held[row][i] = c
            for u in us:
                u["row"], u["at"] = row, at
            return True

        if by_cell:
            alike = {}                                       # the uses with the same colours of the same row
            for key, us in sorted(groups.items()):
                for u in us:
                    alike.setdefault((key, tuple(sorted(u["cols"]))), []).append(u)
            size = {key: len(whole(us)) for key, us in groups.items()}
            # a source row after the other (the one with the most colours first: its cells then find most of
            # their colours in one row of ours), and of a source row the cells with the most colours first
            for key, us in sorted(alike.items(), key=lambda kv: (-size[kv[0][0]], kv[0][0], -len(kv[0][1]), kv[0])):
                if not put(us, us[0]["cols"]):
                    return None, us[0]
            return held, None
        for key, us in sorted(groups.items(), key=lambda kv: (-len(whole(kv[1])), kv[0])):   # the biggest first
            if put(us, whole(us)):                           # a source row's colours together, when they fit
                continue
            for u in sorted(us, key=lambda u: -len(u["cols"])):   # else cell by cell
                if not put([u], u["cols"]):
                    return None, u
        return held, None

    def fill(join, by_cell):
        """The colours and the cells one way: -> (rows used, palettes, given up, drawn, cells, cell_of, held,
        wanted), or the TilesError that says what did not fit."""
        held, stuck = pack(join, by_cell)
        if held is None:
            maps = sorted({"%d/%d" % (g, n) for o, g, n, m in imports})
            return TilesError(
                "The tiles taken for %s use more colours than there is room for. A map's own tiles have seven sets of "
                "15 colours; %d %s in use by the houses on the ground, and the tiles taken from %s fill the rest. Tile "
                "%d needs colours that no longer fit. Remove taken tiles you have not painted with, or take fewer "
                "different kinds of things (pieces of one building share their colours)." % (
                    where, len(need_rows), "is" if len(need_rows) == 1 else "are", ", ".join(maps), stuck["ours"]))
        rows_used = [r for r in free_rows if any(c is not None for c in held[r][1:])]
        pals = [list(q) for q in base.pals]
        for r in rows_used:
            pals[r] = [base.pals[r][0]] + [c or 0 for c in held[r][1:]]
        # Petalburg metatiles that used a row now taken are given up
        given_up = {k for k in range(BASE_COUNT) if rows[k] & set(rows_used)}
        assert not given_up & need

        def content(ti, k, s, v):
            """What entry k of a taken tile draws with: (a General cell's number, None) or (None, the 32 bytes of a
            cell of ours), and its palette row."""
            t, r = v & 0x3FF, v >> 12
            u = uses.get((ti, k))
            if u is None:                                        # a row of General's (or none of the map's): as it is
                return (t, None, r) if t < 512 else (None, s.cell(t), r)
            to = [0] * 16
            for i in u["idx"]:
                to[i] = u["at"][u["pal"][i]]
            if all(to[i] == i for i in u["idx"]):
                return (t, None, u["row"]) if t < 512 else (None, u["cell"], u["row"])
            return None, bytes(to[byte & 15] | to[byte >> 4] << 4 for byte in u["cell"]), u["row"]

        # picture cells: each different one of the taken tiles needs a cell no Petalburg metatile still uses
        drawn, wanted = [], []                               # per taken tile its entries' contents; the cells, as met
        for ti, (ours, s, mid, entries, attr) in enumerate(taken):
            drawn.append([content(ti, k, s, v) for k, v in enumerate(entries)])
            for t, c, r in drawn[-1]:
                if c is not None and c not in wanted:
                    wanted.append(c)

        def free_cells():
            kept = set().union(*[refs[k] for k in range(BASE_COUNT) if k not in given_up])
            return [512 + i for i in range(CELLS) if 512 + i not in kept]

        free = free_cells()
        spare = [k for k in sorted(range(BASE_COUNT), reverse=True) if k not in need and k not in given_up]
        while len(wanted) > len(free) and spare:                 # give Petalburg metatiles up, the last first
            given_up.add(spare.pop(0))
            free = free_cells()
        if len(wanted) > len(free):
            return TilesError(
                "The tiles taken for %s need %d different picture cells, and the craters' own set has room for %d "
                "(504 in all, %d used by the houses on the ground). Remove taken tiles you have not painted with, or "
                "take fewer pieces." % (where, len(wanted), len(free), len(need_cells)))
        cells = bytearray(base.cells[:CELLS * 32].ljust(CELLS * 32, b"\0"))
        cell_of = {}
        for c, at in zip(wanted, free):
            cells[(at - 512) * 32:(at - 512) * 32 + 32] = c
            cell_of[c] = at
        return rows_used, pals, given_up, drawn, cells, cell_of, held, wanted

    # the ways, the gentlest first: the colours exact before shades are joined, a source row at a time before a
    # cell at a time. The first that has room for everything is it; if none has, the last one's reason is given
    # (the tightest way's: what is really missing).
    for join in JOIN:
        for by_cell in (False, True):
            got = fill(join, by_cell)
            if not isinstance(got, TilesError):
                break
        else:
            continue
        break
    else:
        raise got
    rows_used, pals, given_up, drawn, cells, cell_of, held, wanted = got

    out = Custom()
    top = max([ours for ours, *_ in taken], default=FIRST - 1)
    metas = bytearray(rom[base.metas:base.metas + 16 * BASE_COUNT]) + bytes(16 * (top + 1 - FIRST))
    attrs = list(struct.unpack_from("<%dH" % BASE_COUNT, rom, base.attrs)) + [0] * (512 - BASE_COUNT)
    out.beh, out.layer = {}, {}
    for (ours, s, mid, entries, attr), parts in zip(taken, drawn):
        new = [(t if c is None else cell_of[c]) | (v & 0x0C00) | r << 12 for v, (t, c, r) in zip(entries, parts)]
        struct.pack_into("<8H", metas, 16 * (ours - 512), *new)
        attrs[ours - 512] = attr
        out.beh[ours], out.layer[ours] = attr & 0xFF, attr >> 12
    out.cells = bytes(cells) + bytes(8 * 32)                 # (512 cells: the last 8 are the door's)
    out.tiles = lz_comp(bytes(cells))
    out.metatiles, out.attrs = bytes(metas), attrs
    out.pals = [c for q in pals for c in q]
    out.given_up = sorted(512 + k for k in given_up)
    out.imports = sorted(imports)
    # the room left, counting what could still be had by giving Petalburg metatiles up
    out.cells_used, out.cells_room = len(wanted), CELLS - len(need_cells)
    out.rows_used, out.rows_room = len(rows_used), len(ROW_ORDER) - len(need_rows)
    out.colours_free = sum(1 for r in free_rows for c in held[r][1:] if c is None)
    out.join = join                                          # shades this many steps apart share a colour
    out.by_cell = by_cell
    return out


def room(custom):
    """A line for the user: how much more can be taken."""
    n = len(custom.given_up)
    return "Room for taken tiles: %d of %d picture cells and %d of %d colours used%s.%s" % (
        custom.cells_used, custom.cells_room, 15 * custom.rows_room - custom.colours_free, 15 * custom.rows_room,
        " (shades too close to tell apart share a colour)" if custom.join else "",
        " %d tile%s of the craters' own set that %s nowhere on the ground left the list to make room." % (
            n, "" if n == 1 else "s", "is" if n == 1 else "are") if n else "")


# ------------------------------------------------------------------------------------------------ what to take from
def sources(rom, names):
    """The maps tiles can be taken from: [(group, number, name, width, height, secondary tileset)], those drawn
    with General and a secondary set that is not the craters' own. names: region map section -> its name."""
    out = []
    starts = []
    while len(starts) < 80 and 0x08000000 <= u32(rom, MAP_GROUPS + 4 * len(starts)) < 0x0A000000:
        starts.append(u32(rom, MAP_GROUPS + 4 * len(starts)))
    for g, garr in enumerate(starts):
        # a group's maps: pointers up to the next group's table (or to the first word that is no pointer)
        later = [s for s in starts if s > garr]
        count = 0
        while count < 400 and (not later or garr + 4 * count < min(later)) and \
                0x08000000 <= u32(rom, garr - 0x08000000 + 4 * count) < 0x0A000000:
            count += 1
        for n in range(count):
            hdr = u32(rom, garr - 0x08000000 + 4 * n) - 0x08000000
            if not 0 <= hdr < len(rom) - 28:
                continue
            lay = u32(rom, hdr) - 0x08000000
            if not 0 <= lay < len(rom) - 24:
                continue
            w, h = u32(rom, lay), u32(rom, lay + 4)
            prim, sec = u32(rom, lay + 16), u32(rom, lay + 20)
            if prim != GENERAL or sec == BASE or not 0x08000000 <= sec < 0x0A000000:
                continue
            if not (0 < w <= 200 and 0 < h <= 200):
                continue
            out.append((g, n, names.get(rom[hdr + 0x14], "?"), w, h, sec))
    return out


if __name__ == "__main__":
    import sys
    print(text(load(sys.argv[1] if len(sys.argv) > 1 else None)))
