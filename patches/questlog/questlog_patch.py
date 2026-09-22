"""Quest Log (Hyper Emerald v5.7): python questlog_patch.py in.gba out.gba

Needs the Journal (patches/journal) already applied. Using the Journal then opens a checklist screen instead
of the one-line message: one chapter a page (Hoenn, Post-game, Sinnoh, Lost Artifacts), a tick on what is
done, an arrow on the current objective, a diamond on side objectives, and "???" for what is still ahead.
A on a row shows the objective's full text; L/R turn the chapter; B goes back to the field.

The rows are the Journal's own step table and its own routines, so the two can never disagree: this patch
rebuilds the Journal blob from patches/journal, checks the ROM holds exactly that, and calls into it.

The Start menu gets a small "[R] Journal" box at the top left, and R there opens the Quest Log.

ROM changes: item 363's field-use pointer (the Journal's message routine stays, unused); an 8-byte trampoline
at HandleStartMenuInput's entry; entry 3 of InitStartMenuStep's jump table. Everything else is new code and
data in free space. Nothing is written to the save.
"""
import struct, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "journal"))
import journal_patch as J
import steps as S
from legends import LEGENDS
from keyitems import KEYITEMS
from sidecontent import SIDE

FREE = 0x00FEA000                       # in the unreferenced 0xFF run 0x08FE9074..0x08FF0000
BASE = 0x08000000 + FREE

WIDGET_W = 8                            # tiles
HSI = 0x0009FAC4                        # HandleStartMenuInput
HSI_BYTES = "10b52a4ce18d4020"          # push {r4,lr}; ldr r4,=gMain; ldrh r1,[r4,#0x2E]; movs r0,#0x40
STEP_TABLE = 0x0009F8B8                 # InitStartMenuStep's jump table; entry 3 shows the Safari window
SIDE_FREE = 0x01F9C000                  # the Side Content chapter's table and texts, after the Key Items'
KEY_FREE = 0x01F9A000                   # the Key Items chapter's table and texts, after the Legends' 40 KB
LEG_FREE = 0x01F90000                   # the Legends chapter's names and texts: in the 0xFF run at the ROM's
                                        # end (0x09F82519..), well clear of 0x09FE0000, which code points at

NPAGES = 7                              # the four Journal chapters, Legends, Key Items, Side Content
PAGES = [(S.HOENN, "Hoenn"), (S.POST, "Post-game"), (S.SINNOH, "Sinnoh"), (S.LOST, "Lost Artifacts")]


def rgb(r, g, b):
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


# palette 15, window colours; entry 0 is also loaded as the backdrop
PAL = [0] * 16
PAL[0] = PAL[1] = rgb(248, 240, 216)    # paper
PAL[2] = rgb(64, 56, 48)                # text
PAL[3] = rgb(216, 204, 176)             # text shadow
PAL[4] = rgb(248, 216, 128)             # selection bar
PAL[5] = rgb(168, 160, 144)             # text still ahead
PAL[6] = rgb(40, 160, 72)               # tick
PAL[7] = rgb(208, 56, 40)               # current
PAL[8] = rgb(56, 88, 128)               # header and footer bars
PAL[9] = rgb(248, 248, 248)             # bar text
PAL[10] = rgb(24, 40, 72)               # bar text shadow
PAL[11] = rgb(96, 88, 72)               # box and diamond outlines
PAL[12] = rgb(232, 224, 200)            # shadow of the text still ahead; progress bar track
PAL[13] = rgb(36, 52, 84)               # the chapter grid's backdrop
PAL[14] = rgb(248, 192, 48)             # gold: the selected card's border, Legends
PAL[15] = rgb(144, 96, 200)             # purple: Lost Artifacts

# {bg, fg, shadow, 0}: normal, normal selected, current, current selected, ahead, ahead selected, bars,
# complete (the grid's green count)
COLORS = [(1, 2, 3), (4, 2, 3), (1, 7, 3), (4, 7, 3), (1, 5, 12), (4, 5, 12), (8, 9, 10), (1, 6, 12)]

CHARS = {".": 0, "B": 11, "G": 6, "R": 7, "D": 5, "W": 9, "K": 2, "S": 8, "P": 15, "Y": 14, "N": 11,
         "V": 10, "L": 12}

# the chapter grid: a label, an accent colour and a 16x16 icon per chapter
GRID = [
    ("Hoenn", 6, """
.....GGGGG......
...GGGGGGGGG....
..GGGWWGGGGGG...
..GGWWGGGGGGG...
.GGGGGGGGGGGGG..
.GGGGGGGGGGGGG..
.GGGGGGGGGGGGG..
..GGGGGGGGGGG...
...GGGGGGGGG....
.....GGGGG......
.......NN.......
.......NN.......
.......NN.......
.....NNNNNN.....
................
................"""),
    ("Post-game", 7, """
.......RR.......
.......RR.......
......RRRR......
......RRRR......
RRRRRRRWRRRRRRR.
.RRRRRWWRRRRRR..
..RRRRRRRRRRR...
...RRRRRRRRR....
...RRRRRRRRR....
..RRRRR.RRRRR...
..RRRR...RRRR...
.RRR.......RRR..
.RR.........RR..
................
................
................"""),
    ("Sinnoh", 8, """
................
................
.....W..........
....WWW.........
...WWSWW........
..WSSSSSW...W...
.SSSSSSSSS.WWW..
SSSSSSSSSSWWSWW.
SSSSSSSSSSSSSSSS
SSSSSSSSSSSSSSSS
SSSSSSSSSSSSSSSS
SSSSSSSSSSSSSSSS
................
................
................
................"""),
    ("Artifacts", 15, """
....PPPPPPPP....
...PPPPPPPPPP...
..PPPPPPPPPPPP..
..PPWWWWWWWWPP..
..PPPPPPPPPPPP..
..PPWWWWWWPPPP..
..PPPPPPPPPPPP..
..PPWWWWWWWWPP..
..PPPPPPPPPPPP..
..PPWWWWWPPPPP..
..PPPPPPPPPPPP..
..PPPPPPPPPPPP..
..PPPPPPPPPPPP..
................
................
................"""),
    ("Legends", 14, """
................
................
.Y.....Y.....Y..
.YY...YYY...YY..
.YYY.YYYYY.YYY..
.YYYYYYYYYYYYY..
.YYYYYRRRYYYYY..
.YYYYRRWRRYYYY..
.YYYYYRRRYYYYY..
.YYYYYYYYYYYYY..
.YYYYYYYYYYYYY..
................
................
................
................
................"""),
    ("Key Items", 11, """
................
...YYYY.........
..YY..YY........
..Y....Y........
..Y....Y........
..YY..YY........
...YYYYYYYYYYYY.
..........Y.Y.Y.
..........Y.Y...
................
................
................
................
................
................
................"""),
    ("Side Quests", 10, """
..VVVVVVVVVVVV..
.VVVVVVVVVVVVVV.
.VVVVVVWWVVVVVV.
.VVVVVVWWVVVVVV.
.VVVVVVWWVVVVVV.
.VVVVVVWWVVVVVV.
.VVVVVVVVVVVVVV.
.VVVVVVWWVVVVVV.
.VVVVVVVVVVVVVV.
..VVVVVVVVVVVV..
.....VVV........
....VVV.........
...VV...........
................
................
................"""),
]

ICON_DONE = """
................
................
..............GG
.............GG.
..BBBBBBBBBBGG..
..B........GGB..
..B.......GG.B..
..B.GG...GG..B..
..B..GG.GG...B..
..B...GGG....B..
..B....G.....B..
..B..........B..
..BBBBBBBBBBBB..
................
................
................
"""
ICON_CURRENT = """
................
................
................
....RR..........
....RRRR........
....RRRRRR......
....RRRRRRRR....
....RRRRRRRRRR..
....RRRRRRRRRR..
....RRRRRRRR....
....RRRRRR......
....RRRR........
....RR..........
................
................
................
"""
ICON_SIDE = """
................
................
................
.......BB.......
......B..B......
.....B....B.....
....B......B....
...B........B...
...B........B...
....B......B....
.....B....B.....
......B..B......
.......BB.......
................
................
................
"""
ICON_BOX = """
................
................
................
................
..DDDDDDDDDDDD..
..D..........D..
..D..........D..
..D..........D..
..D..........D..
..D..........D..
..D..........D..
..D..........D..
..DDDDDDDDDDDD..
................
................
................
"""
UP = """
........
...BB...
..BBBB..
.BBBBBB.
BBBBBBBB
........
........
........
"""
LEFT = """
....W...
...WW...
..WWW...
.WWWW...
.WWWW...
..WWW...
...WW...
....W...
"""


def grid(art):
    rows = [r for r in art.strip("\n").split("\n")]
    return [[CHARS[c] for c in r] for r in rows]


def tiles(g):
    """4bpp, 8x8 tiles row by row, two pixels a byte with the left one in the low nibble."""
    h, w = len(g), len(g[0])
    assert h % 8 == 0 and w % 8 == 0
    out = bytearray()
    for ty in range(h // 8):
        for tx in range(w // 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(g[ty * 8 + y][tx * 8 + x] | (g[ty * 8 + y][tx * 8 + x + 1] << 4))
    return bytes(out)


def flip_v(g):
    return g[::-1]


def flip_h(g):
    return [r[::-1] for r in g]


def dimmed(g):
    return [[5 if v == 11 else v for v in r] for r in g]


def thumb(src, addr):
    """journal_patch.thumb's checks, except that keystone pads a code-section .align with a Thumb-2 nop
    (00 BF): allowed here only straight after a return or an unconditional branch, where it never runs."""
    import re
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    code = bytes(J.ks.asm(src, addr)[0])
    twin = bytes(J.ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                          addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (
        addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    for k, i in enumerate(dis):
        if i.mnemonic == "nop":
            p = dis[k - 1]
            ends = p.mnemonic == "bx" or p.mnemonic == "b" or (p.mnemonic == "pop" and "pc" in p.op_str)
            assert ends, "a Thumb-2 nop at %08X that can run: use mov r8, r8" % i.address
    return code, dis


def s(text):
    return J.enc(text) + b"\xff"


def data_blob(base, sym, table):
    d = bytearray()
    a = {}

    def put(name, b, align=4):
        while len(d) % align:
            d.append(0)
        a[name] = base + len(d)
        d.extend(b)

    put("BGTEMPLATES", struct.pack("<I", 0x01F0))                       # BG0: char base 0, map 31
    put("WINTEMPLATES", bytes((0, 0, 0, 30, 2, 15)) + struct.pack("<H", 1)      # header
                        + bytes((0, 0, 2, 30, 16, 15)) + struct.pack("<H", 61)  # list / detail pane
                        + bytes((0, 0, 18, 30, 2, 15)) + struct.pack("<H", 541) # footer
                        + bytes((0xFF, 0, 0, 0, 0, 0)) + struct.pack("<H", 0))
    put("PAL", struct.pack("<16H", *PAL))
    put("COLORS", b"".join(bytes(c) + b"\x00" for c in COLORS))
    a["COLHEAD"] = a["COLORS"] + 24
    side = grid(ICON_SIDE)
    box = grid(ICON_BOX)
    seen = [[11 if v == 5 else v for v in r] for r in box]
    # by status - 1: done, current, side left behind, side ahead, ahead, legend seen, legend not seen yet
    # ... legend not seen yet, key item not got yet
    put("ICONS", b"".join(tiles(g) for g in (grid(ICON_DONE), grid(ICON_CURRENT), side, dimmed(side),
                                              box, seen, box, box)))
    # by status: colour set (0 normal, 8 current, 16 dim) and whether the row shows its title
    put("STCOLOR", bytes((0, 0, 8, 0, 16, 16, 0, 16, 16)))
    put("STSHOW", bytes((0, 1, 1, 1, 0, 0, 1, 0, 1)))
    put("UPICON", tiles(grid(UP)))
    put("DOWNICON", tiles(flip_v(grid(UP))))
    put("LEFTICON", tiles(grid(LEFT)))
    put("RIGHTICON", tiles(flip_h(grid(LEFT))))

    # chapters: {first step, rows, objectives, 0, name}; the last page also holds the closing row
    names = {}
    for _, title in PAGES:
        put("NAME_" + title, s(title), 1)
        names[title] = a["NAME_" + title]
    heads = [h for h, _, _ in S.STEPS]
    rows = b""
    first = 0
    for i, (header, title) in enumerate(PAGES):
        n = heads.count(header)
        assert heads[first:first + n] == [header] * n, "%s objectives are not one run" % title
        extra = 1 if i == len(PAGES) - 1 else 0
        rows += struct.pack("<BBBBI", first, n + extra, n, 0, names[title])
        first += n
    assert first == len(S.STEPS)
    put("NAME_Legends", s("Legends"), 1)
    assert len(LEGENDS) <= 99, "the header counts with two digits"
    rows += struct.pack("<BBBBI", 0, len(LEGENDS), len(LEGENDS), 1, a["NAME_Legends"])   # type 1: Legends
    put("NAME_Keys", s("Key Items"), 1)
    assert len(KEYITEMS) <= 99
    rows += struct.pack("<BBBBI", 0, len(KEYITEMS), len(KEYITEMS), 2, a["NAME_Keys"])    # type 2: Key Items
    put("NAME_Side", s("Side Content"), 1)
    assert len(SIDE) <= 99
    rows += struct.pack("<BBBBI", 0, len(SIDE), len(SIDE), 3, a["NAME_Side"])            # type 3: Side Content
    assert len(rows) // 8 == NPAGES and NPAGES <= 9, "the grid has 9 tiles"
    put("PAGES", rows)

    ptrs = []
    for t in list(S.TITLES) + [S.FINAL_TITLE]:
        put("T", s(t), 1)
        ptrs.append(a["T"])
    put("TITLES", struct.pack("<%dI" % len(ptrs), *ptrs))
    put("QQQ", s("???"), 1)
    put("HINTLIST", s("A: Read   B: Back   L/R: Chapter"), 1)
    put("HINTGRID", s("A: Open   B: Close"), 1)
    put("QLTITLE", s("Quest Log"), 1)
    assert len(GRID) == NPAGES
    put("ACCENT", bytes(c for _, c, _ in GRID), 1)
    # the selected card's flashing border: gold to deep orange and back, 16 steps (never close to the card)
    gold, white = (248, 200, 56), (232, 96, 24)
    steps = [abs(8 - k) / 8.0 for k in range(16)]              # 1 .. 0 .. 1
    put("PULSE", struct.pack("<16H", *(rgb(*[int(w + (g - w) * t) for g, w in zip(gold, white)]) for t in steps)))
    put("GICONS", b"".join(tiles(grid(art)) for _, _, art in GRID))
    gnames = []
    for label, _, _ in GRID:
        put("GN", s(label), 1)
        gnames.append(a["GN"])
    put("GNAMES", struct.pack("<%dI" % len(gnames), *gnames))
    put("HINTMORE", s("A: Next page   B: Back"), 1)
    put("HINTLAST", s("A/B: Back"), 1)
    # the Start menu box: where the Safari Zone's ball count goes ({bg, left, top, width, height, palette, base})
    put("WIDGET_TEMPLATE", bytes((0, 1, 1, WIDGET_W, 2, 15)) + struct.pack("<H", 0x08))
    put("WIDGET_LABEL", b"\xf8\x03" + s(" Journal"), 1)          # the R-button icon, then the name
    while len(d) % 4:
        d.append(0)
    a.update({"STEPS": table, "STEPDONE": sym["step_done"] | 1, "APPEND": sym["append"] | 1,
              "GROUPTAIL": sym["group_tail"] | 1, "U8DEC": sym["u8dec"] | 1, "LEGENDS": 0x08000000 + LEG_FREE,
              "LEGSIL": 0x08000000 + LEG_FREE + 16 * len(LEGENDS),
              "LEGSILDIM": 0x08000000 + LEG_FREE + 16 * len(LEGENDS) + 128 * len(LEGENDS),
              "KEYS": 0x08000000 + KEY_FREE, "SIDES": 0x08000000 + SIDE_FREE})
    return bytes(d), a


def pane(text):
    """A legend text laid out for the detail pane: lines joined by plain line breaks (8 fit a page)."""
    return b"\xfe".join(J.enc(l) for l in J.wrap(text)) + b"\xff"


NATDEX = 0x00F50370                     # SpeciesToNationalPokedexNum's table (species - 1 -> dex no.)
ICON_TABLE = 0x00F2A020                 # GetMonIconTiles' table: species -> 32x32 4bpp icon (2 frames)


def icon_pixels(rom, species):
    p = struct.unpack_from("<I", rom, ICON_TABLE + 4 * species)[0] - 0x08000000
    px = [[0] * 32 for _ in range(32)]
    for t in range(16):
        for y in range(8):
            for x in range(8):
                b = rom[p + t * 32 + y * 4 + x // 2]
                px[(t // 4) * 8 + y][(t % 4) * 8 + x] = (b >> 4) if x & 1 else (b & 15)
    return px


def silhouette(px, colour):
    """The icon's first frame cropped to the Pokemon, shrunk to fit 16x16 (sitting on the bottom), one colour."""
    ys = [y for y in range(32) if any(px[y])]
    xs = [x for x in range(32) if any(px[y][x] for y in range(32))]
    y0, y1, x0, x1 = min(ys), max(ys) + 1, min(xs), max(xs) + 1
    w, h = x1 - x0, y1 - y0
    sc = max(w, h, 16) / 16.0
    nw, nh = max(1, round(w / sc)), max(1, round(h / sc))
    out = [[0] * 16 for _ in range(16)]
    ox, oy = (16 - nw) // 2, 16 - nh
    for y in range(nh):
        for x in range(nw):
            sx0 = x0 + int(x * sc)
            sx1 = min(x1, max(x0 + int((x + 1) * sc), sx0 + 1))
            sy0 = y0 + int(y * sc)
            sy1 = min(y1, max(y0 + int((y + 1) * sc), sy0 + 1))
            tot = (sy1 - sy0) * (sx1 - sx0)
            cov = sum(1 for yy in range(sy0, sy1) for xx in range(sx0, sx1) if px[yy][xx])
            if tot and cov * 3 >= tot:                  # a third of the pixels under it: keeps thin wings
                out[oy + y][ox + x] = colour
    return out


def sides_blob(base):
    """{0, flag u16, name, where, where} per row, then the strings (the hint slot repeats "where")."""
    d = bytearray(16 * len(SIDE))
    for i, (flag, name, where) in enumerate(SIDE):
        ptrs = []
        for t in (s(name), pane(where)):
            assert t.count(b"\xfe") < 8, "too long for one page: %r" % t
            ptrs.append(base + len(d))
            d.extend(t)
        struct.pack_into("<HHIII", d, 16 * i, 0, flag, ptrs[0], ptrs[1], ptrs[1])
    while len(d) % 4:
        d.append(0)
    return bytes(d)


def keys_blob(base, rom):
    """{item u16, flag u16, name, hint, where} per key item, then the strings. Checks each id is a key item."""
    n = len(KEYITEMS)
    d = bytearray(16 * n)
    for i, (item, flag, name, hint, where) in enumerate(KEYITEMS):
        assert rom[J.ITEMS + item * 44 + 0x1A] == 5, "item %d (%s) is not in the Key Items pocket" % (item, name)
        ptrs = []
        for t in (s(name), pane(hint), pane(where)):
            assert t.count(b"\xfe") < 8, "too long for one page: %r" % t
            ptrs.append(base + len(d))
            d.extend(t)
        struct.pack_into("<HHIII", d, 16 * i, item, flag, *ptrs)
    while len(d) % 4:
        d.append(0)
    return bytes(d)


def legends_blob(base, rom):
    """{dex u16, 0 u16, name, hint, where} per legend, then a dark and a dim silhouette per legend (128 bytes
    each, 16x16 4bpp), then the strings."""
    dex2sp = {}
    for sp in range(1, 1300):
        dex2sp.setdefault(struct.unpack_from("<H", rom, NATDEX + 2 * (sp - 1))[0], sp)
    n = len(LEGENDS)
    d = bytearray(16 * n)
    icons = [icon_pixels(rom, dex2sp[dex]) for dex, *_ in LEGENDS]
    d += b"".join(tiles(silhouette(px, 2)) for px in icons)     # text colour
    d += b"".join(tiles(silhouette(px, 5)) for px in icons)     # the dim "still ahead" colour
    for i, (dex, name, hint, where) in enumerate(LEGENDS):
        ptrs = []
        for t in (s(name), pane(hint), pane(where)):
            assert t.count(b"\xfe") < 8, "too long for one page: %r" % t
            ptrs.append(base + len(d))
            d.extend(t)
        struct.pack_into("<HHIII", d, 16 * i, dex, 0, *ptrs)
    while len(d) % 4:
        d.append(0)
    return bytes(d)


def journal_in(rom):
    """Rebuild the Journal the way patches/journal makes it and insist the ROM holds exactly that."""
    prevhook = struct.unpack_from("<I", rom, J.OW_TARGET)[0]
    assert prevhook == J.BASE | 1, "the Journal is not applied (overworld hook does not point at it)"
    probe, _, _, _ = J.layout(0)
    # the Journal's own chain target is the one literal a rebuild cannot know: read it back
    diff = [i for i in range(len(probe)) if probe[i] != rom[J.FREE + i]]
    assert diff and diff[-1] - diff[0] < 4, "the Journal in this ROM is not the one patches/journal builds"
    at = diff[0] & ~3
    target = struct.unpack_from("<I", rom, J.FREE + at)[0]
    blob, sym, table, _ = J.layout(target)
    assert bytes(rom[J.FREE:J.FREE + len(blob)]) == blob, "the Journal in this ROM differs from patches/journal"
    return sym, table


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert len(S.TITLES) == len(S.STEPS) and len(S.STEPS) + 1 <= 0x88 and NPAGES <= 9
    assert all(len(t) <= 24 for t in S.TITLES + [S.FINAL_TITLE])

    sym, table = journal_in(rom)
    assert bytes(rom[HSI:HSI + 8]).hex() == HSI_BYTES, "HandleStartMenuInput is not the vanilla one"
    assert struct.unpack_from("<I", rom, STEP_TABLE + 12)[0] == 0x0809F90C, "Start menu step 3 moved"
    e = J.ITEMS + J.ITEM * 44
    assert struct.unpack_from("<I", rom, e + 0x1C)[0] == sym["item_use"] | 1, \
        "item 363 does not use the Journal's routine (already applied?)"

    src = open(os.path.join(HERE, "questlog.s"), encoding="ascii").read()

    def assemble(addrs):
        t = src.replace("#NPAGES", "#%d" % NPAGES).replace("#NLAST", "#%d" % (NPAGES - 1))
        for k, v in sorted(addrs.items(), key=lambda kv: -len(kv[0])):   # longest first
            t = t.replace(k + "_ADDR", "0x%08X" % v)
        return thumb(t, BASE)

    code_names = ("CB2_INIT", "CB2_MAIN", "VBLANK", "TASK", "WAIT_TASK", "MENU_CB")
    _, dummy = data_blob(BASE, sym, table)
    code, dis = assemble(dict(dummy, **{k: BASE for k in code_names}))
    code_len = (len(code) + 3) & ~3
    data, daddrs = data_blob(BASE + code_len, sym, table)

    order = ("item_use", "wait_task", "cb2_init", "cb2_main", "vblank", "se_select", "compute", "page_sel",
             "print", "show", "draw_list", "draw_header", "draw_footer", "open_detail", "draw_detail", "task",
             "hsi", "menu_cb", "case3", "has_journal", "show_widget", "widget_remove", "row_status", "row_title", "ext_entry",
             "draw_grid", "grid_count", "rect", "corners", "grid_input", "grid_pulse")
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    assert len(funcs) == len(order), "unexpected function layout: %d pushes, expected %d" % (len(funcs), len(order))
    f = dict(zip(order, funcs))
    caddrs = {"CB2_INIT": f["cb2_init"] | 1, "CB2_MAIN": f["cb2_main"] | 1, "VBLANK": f["vblank"] | 1,
              "TASK": f["task"] | 1, "WAIT_TASK": f["wait_task"] | 1, "MENU_CB": f["menu_cb"] | 1}
    code, _ = assemble(dict(daddrs, **caddrs))
    assert (len(code) + 3) & ~3 == code_len

    blob = bytearray(code) + bytes(code_len - len(code)) + data
    end = FREE + len(blob)
    assert end <= 0x00FF0000
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    leg = legends_blob(0x08000000 + LEG_FREE, rom)
    assert LEG_FREE + len(leg) <= KEY_FREE, "the Legends data runs into the Key Items'"
    keys = keys_blob(0x08000000 + KEY_FREE, rom)
    assert set(rom[KEY_FREE:KEY_FREE + len(keys)]) == {0xFF}, "Key Items region not free"
    assert KEY_FREE + len(keys) <= 0x01FA0000, "outside the checked window"
    rom[KEY_FREE:KEY_FREE + len(keys)] = keys
    assert KEY_FREE + len(keys) <= SIDE_FREE, "the Key Items data runs into the Side Content's"
    sides = sides_blob(0x08000000 + SIDE_FREE)
    assert set(rom[SIDE_FREE:SIDE_FREE + len(sides)]) == {0xFF}, "Side Content region not free"
    assert SIDE_FREE + len(sides) <= 0x01FA0000, "outside the checked window"
    rom[SIDE_FREE:SIDE_FREE + len(sides)] = sides
    assert set(rom[LEG_FREE:LEG_FREE + len(leg)]) == {0xFF}, "Legends region not free"
    rom[LEG_FREE:LEG_FREE + len(leg)] = leg
    struct.pack_into("<I", rom, e + 0x1C, f["item_use"] | 1)
    rom[HSI:HSI + 4] = bytes.fromhex("004b1847")                   # ldr r3,[pc,#0]; bx r3
    struct.pack_into("<I", rom, HSI + 4, f["hsi"] | 1)
    assert f["case3"] % 2 == 0
    struct.pack_into("<I", rom, STEP_TABLE + 12, f["case3"])       # reached by mov pc: stays in Thumb
    open(outp, "wb").write(rom)

    print("code %d bytes @%08X, data @%08X, end %08X (%d bytes)" % (len(code), BASE, BASE + code_len,
                                                                   0x08000000 + end, len(blob)))
    print("  Side Content: %d rows, %d bytes @%08X" % (len(SIDE), len(sides), 0x08000000 + SIDE_FREE))
    print("  Key Items: %d rows, %d bytes @%08X" % (len(KEYITEMS), len(keys), 0x08000000 + KEY_FREE))
    print("  Legends: %d rows, %d bytes @%08X" % (len(LEGENDS), len(leg), 0x08000000 + LEG_FREE))
    print("  item_use %08X, cb2_init %08X, task %08X; Journal step_done %08X, steps %08X" % (
        f["item_use"] | 1, caddrs["CB2_INIT"], caddrs["TASK"], sym["step_done"] | 1, table))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
