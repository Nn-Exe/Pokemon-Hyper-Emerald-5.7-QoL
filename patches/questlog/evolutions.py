"""The Quest Log's Evolutions chapter: every evolution in the ROM's own table, one list per region.

The table (EVOS) is 40 bytes a species: five {method u16, parameter u16, target u16, extra u16}. The method's low byte
is the method; a high byte (0x3F / 0xFF) marks a baby whose egg needs an incense, named in `extra`. Methods 250-255
are Mega Evolutions, Primal Reversion and form changes, not evolutions - left out. Measured in this ROM 2026-09-30.

Rows are grouped by the region of the Pokemon that evolves (its National Dex number) and sorted by it. A row shows
"<name> -> <evolution>" and the method; while that Pokemon has not been seen, "???" (row_status in questlog.s).
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "journal"))
import journal_patch as J

EVOS = 0x00F387C0                       # the evolution table (found by Bulbasaur's "level 16 -> Ivysaur" row)
SPNAMES = 0x144                         # ROM header: the species names (11 bytes a name)
NATDEX = 0x00F50370                     # species - 1 -> National Dex number
NSPECIES = 1200                         # species 0..1199 (the names table and species.json agree)
FONTW = 0x006542E4                      # the normal font's glyph widths
ARROW = 0x7C                            # the font's right arrow
HISUIAN_PILL = 753
EEVEE, EEVEE_EVOS = 133, 0x01F0B4A0     # Eevee has ten: GetEvolutionTargetSpecies (0x09F0534C) reads this table
ROMDATA = os.path.join(HERE, "..", "..", "tools", "romdata", "out")
REGIONS = [("Kanto", 1, 151), ("Johto", 152, 251), ("Hoenn", 252, 386), ("Sinnoh", 387, 493),
           ("Unova", 494, 649), ("Kalos", 650, 721), ("Alola", 722, 809), ("Galar", 810, 905)]
ROW_W = 221                             # the list: the name from x 13, the tag ends at x 234, 6 px apart
PANE_W = 158                            # the info panel's text column
MAX_ROWS = 99                           # the header's count (the Journal's u8dec) has two digits: a longer
                                        # region is split in two (Kanto 1 / Kanto 2)

DEC = {v: k for k, v in J.ENC.items()}


def width(rom, b):
    return sum(rom[FONTW + x] for x in b)


def text_of(b):
    return "".join(DEC.get(x, "") for x in b)


def names(rom):
    base = struct.unpack_from("<I", rom, SPNAMES)[0] - 0x08000000
    return lambda sp: bytes(rom[base + 11 * sp:base + 11 * sp + 11]).split(b"\xff")[0]


def item_name(rom, i):
    return text_of(bytes(rom[J.ITEMS + 44 * i:J.ITEMS + 44 * i + 14]).split(b"\xff")[0])


def natdex(rom, sp):
    return struct.unpack_from("<H", rom, NATDEX + 2 * (sp - 1))[0]


def article(word):
    return "an" if word[:1].upper() in "AEIOU" else "a"


def method(rom, lo, p, pre, target, moves, places, spname, x=0):
    """(short tag, alternative shorter tag, full sentence) for one evolution."""
    I = item_name(rom, p) if p else ""
    lv = "Lv. %d" % p
    if lo == 1:
        return "Friendship", "Friendship", "Level it up while it is very friendly toward you."
    if lo == 2:
        return "Friendship, day", "Friend., day", "Level it up while it is very friendly toward you, during the day."
    if lo == 3:
        return "Friendship, night", "Friend., night", "Level it up while it is very friendly toward you, at night."
    if lo in (4, 13):
        return lv, lv, "It evolves when it reaches level %d." % p
    if lo == 5:
        return "Trade", "Trade", "Trade it to another player."
    if lo == 6 and p == HISUIAN_PILL:           # the Verdanturf seller: held, it works at the usual level
        return I, I, "Let it hold %s %s when it reaches the level it would normally evolve at." % (article(I), I)
    if lo == 6:                                  # GetEvolutionTargetSpecies (0x09F0534C): only in a real trade
        return "Trade + " + I, "Trade + item", "Trade it while it holds %s %s." % (article(I), I)
    if lo == 7:
        return I, I, "Use %s %s on it." % (article(I), I)
    if lo in (8, 9, 10):
        how = {8: "higher than", 9: "equal to", 10: "lower than"}[lo]
        tag = {8: "Atk high", 9: "Atk = Def", 10: "Def high"}[lo]
        return "%s, %s" % (lv, tag), lv, "It evolves at level %d when its Attack is %s its Defense." % (p, how)
    if lo in (11, 12):
        if p == 30:                                                     # Toxel: its nature decides the form
            return lv + ", nature", lv, "It evolves at level %d. Its nature decides which form it takes." % p
        return lv + ", random", lv, ("It evolves at level %d. Whether it becomes Silcoon or Cascoon depends on "
                                     "the Pokémon itself." % p)
    if lo == 14:
        return lv + ", space", lv, ("It appears when Nincada evolves at level %d, if the party has a free "
                                    "space and there is a Poké Ball in the Bag." % p)
    if lo == 15:
        return "Beauty", "Beauty", "Level it up while its Beauty is high (feed it Pokéblocks)."
    if lo == 16:
        M = moves.get(p, "a move")
        return "Knows " + M, "Move", "Level it up while it knows %s." % M
    if lo == 17:
        P = places.get(p, "a special place")
        return P, "Place", "Level it up at %s." % P
    if lo in (18, 19, 30):
        when = {18: ("day", "during the day"), 19: ("night", "at night"), 30: ("dusk", "in the evening")}[lo]
        return "%s, %s" % (lv, when[0]), lv, "It evolves when it reaches level %d %s." % (p, when[1])
    if lo in (20, 21):
        when = ("day", "during the day") if lo == 20 else ("night", "at night")
        return "%s, %s" % (I, when[0]), I, "Level it up %s while it holds %s %s." % (when[1], article(I), I)
    if lo in (22, 23):
        g = "male" if lo == 22 else "female"
        return "%s, %s" % (lv, g), lv, "A %s one evolves when it reaches level %d." % (g, p)
    if lo == 24:
        return lv + ", rain", lv, "It evolves when it reaches level %d while it is raining." % p
    if lo == 25:
        S = text_of(spname(p))
        return "With " + S, "Party", "Level it up with %s %s in your party." % (article(S), S)
    if lo == 26:
        return lv + ", Dark", lv, "It evolves at level %d with a Dark-type Pokémon in your party." % p
    if lo == 29:                                 # Sylveon: parameter = a type (Fairy is 23 here)
        T = TYPES.get(p, "a")
        return "Friend., %s move" % T, "Friendship", ("Level it up while it is very friendly toward you and knows "
                                                      "a %s-type move." % T)
    if lo == 33:                                 # Glaceon: the place is in the extra field
        P = places.get(x, "a special place")
        return P, "Place", "Level it up at %s." % P
    if lo in (27, 28):
        g = "male" if lo == 27 else "female"
        return "%s, %s" % (I, g), I, "Use %s %s on a %s one." % (article(I), I, g)
    return "Special", "Special", "It evolves in a special way."


BASESTATS = 0x1BC                       # ROM header: base stats (28 bytes a species, types at +6 / +7)
TYPES = {0: "Normal", 1: "Fighting", 2: "Flying", 3: "Poison", 4: "Ground", 5: "Rock", 6: "Bug", 7: "Ghost",
         8: "Steel", 10: "Fire", 11: "Water", 12: "Grass", 13: "Electric", 14: "Psychic", 15: "Ice", 16: "Dragon",
         17: "Dark", 23: "Fairy"}         # this hack's numbering (Fairy is 23)
# regional forms by National Dex number (a form of one of these is that region's); Meowth has two, told by type
ALOLA = {19, 20, 26, 27, 28, 37, 38, 50, 51, 52, 53, 74, 75, 76, 88, 89, 103, 105}
GALAR = {52, 77, 78, 79, 80, 83, 110, 122, 144, 145, 146, 199, 222, 263, 264, 554, 555, 562, 618}
HISUI = {58, 59, 100, 101, 157, 211, 215, 503, 549, 570, 571, 628, 705, 706, 713, 724}
GMAX_ITEM = 702                         # Wishing Piece: the hack's Gigantamax item (method 251 like Mega Stones)
DETAIL_W = 210                          # the detail page's text width
DETAIL_MAX = 0x2C0                      # open_detail lays the text out in V+0x100..V+0x400


def types_of(rom, sp):
    base = struct.unpack_from("<I", rom, BASESTATS)[0] - 0x08000000
    a, b = rom[base + 28 * sp + 6], rom[base + 28 * sp + 7]
    return (TYPES.get(a, "?"),) if a == b else (TYPES.get(a, "?"), TYPES.get(b, "?"))


SKIP = 0x13                             # FC 13 x: the text printer jumps to x px from the text's start
PANEL_COL = 92                          # the panel: "Ivysaur" | "Lv. 16"
DETAIL_COL = 128                        # the detail page: "Bulbasaur -> Ivysaur" | "Lv. 16"
DETAIL_TEXT_W = 222


def form_change(rom, lo, p, moves, nm):
    """(the form's name, how) for methods 250-253: ("Mega Charizard X", "Charizardite X")."""
    I = item_name(rom, p)
    if lo == 250:
        return "Ultra " + nm, "Ultra Burst"
    if lo == 252:
        return "Mega " + nm, moves.get(p, "a move")
    if lo == 253:
        return "Primal " + nm, I
    if p == GMAX_ITEM:
        return "G-Max " + nm, I
    if I.endswith(("X", "Y")) and I[-2:-1] != " ":      # "CharizarditeX" -> "Mega Charizard X"
        return "Mega %s %s" % (nm, I[-1]), I[:-1] + " " + I[-1]
    return "Mega " + nm, I


def families(rom):
    """[(region, [family, ...])]; a family is {root, dex, title, tag, rows [(depth, from, to, how, how_short)],
    pic}."""
    spname = names(rom)
    moves = {int(k): (v["name"] if isinstance(v, dict) else v)
             for k, v in json.load(open(os.path.join(ROMDATA, "moves.json"), encoding="utf-8")).items()}
    places = {int(k): v["name"] for k, v in
              json.load(open(os.path.join(ROMDATA, "mapsections.json"), encoding="utf-8")).items()}
    dex = {sp: natdex(rom, sp) for sp in range(1, NSPECIES)}
    first = {}                                           # National Dex number -> its base species
    for sp in range(1, NSPECIES):
        first.setdefault(dex[sp], sp)

    def region_of(sp):
        d, ts = dex[sp], types_of(rom, sp)
        regions = [r for r, st in (("Alola", ALOLA), ("Galar", GALAR), ("Hisui", HISUI)) if d in st]
        if d == 52:                                      # Meowth: Alolan Dark, Galarian Steel
            regions = ["Alola"] if "Dark" in ts else ["Galar"]
        return regions[0] if len(regions) == 1 else None

    ADJ = {"Alola": "Alolan", "Galar": "Galarian", "Hisui": "Hisuian"}

    def label(sp):
        """ "Vulpix", "Alolan Vulpix", or "Wormadam (Bug/Steel)" for another form that shares the name"""
        nm = text_of(spname(sp))
        base = first[dex[sp]]
        if sp == base or types_of(rom, sp) == types_of(rom, base):
            return nm
        r = region_of(sp)
        return ADJ[r] + " " + nm if r else "%s (%s)" % (nm, "/".join(types_of(rom, sp)))

    edges, forms, incoming, reverts = {}, {}, set(), set()
    for sp in range(1, NSPECIES):
        o, n = (EEVEE_EVOS, 10) if sp == EEVEE else (EVOS + 40 * sp, 5)
        for k in range(n):
            m, p, t, x = struct.unpack_from("<HHHH", rom, o + 8 * k)
            lo = m & 0xFF
            if not m or not 0 < t < NSPECIES:
                continue
            if lo == 255:                                # a form's way back to its base (the Gigantamax slots
                reverts.add(sp)                          # 252-276, National Dex 0): covered by the base's family
                continue
            if lo >= 250:
                forms.setdefault(sp, []).append((t, lo, p))
                continue
            short, shorter, sentence = method(rom, lo, p, sp, t, moves, places, spname, x)
            if m >> 8 in (0x3F, 0xFF):                   # a baby: its Egg needs an incense
                sentence += " To get its Egg, a parent must hold %s %s." % (article(item_name(rom, x)),
                                                                            item_name(rom, x))
            edges.setdefault(sp, []).append((t, short, shorter))
            incoming.add(t)
    roots = [sp for sp in range(1, NSPECIES)
             if (sp in edges or sp in forms) and sp not in incoming and sp not in reverts]
    fam = {}
    for r in roots:
        fam.setdefault(dex[r], []).append(r)
    out = []
    for d, rs in fam.items():
        rs.sort(key=lambda r: (r != first.get(d), r))
        rows, seen, kinds = [], set(), []

        def walk(sp, depth):
            src = label(sp)
            for t, short, shorter in edges.get(sp, []):
                key = (src, label(t), short)
                if key in seen:                          # reads the same as one already listed (Burmy's cloaks)
                    continue
                seen.add(key)
                rows.append((depth, src, label(t), short, shorter, t, sp))
                if t != sp and t not in rs:
                    walk(t, depth + 1)
            for t, lo, p in forms.get(sp, []):
                name, how = form_change(rom, lo, p, moves, src)
                key = (src, name, how)
                if key in seen:
                    continue
                seen.add(key)
                rows.append((depth, src, name, how, how, t, sp))
                kinds.append(name.split()[0])            # Mega / G-Max / Primal / Ultra

        for r in rs:
            walk(r, 0)
            reg = region_of(r) if r != rs[0] else None
            if reg:
                kinds.append(reg)
        if not rows:
            continue
        root = rs[0]
        # the row: the main line (first branch at every stage), "+N" for the other branches
        chain, sp = [text_of(spname(root))], root
        while edges.get(sp):
            sp = edges[sp][0][0]
            chain.append(label(sp))
        nevo = len(rows) - sum(1 for r in rows if r[2].split()[0] in ("Mega", "G-Max", "Primal", "Ultra"))
        extra = [k for k in ("Mega", "G-Max", "Primal", "Ultra", "Alola", "Galar", "Hisui") if k in kinds]
        tag = ""                                         # (no tag on the row: the table names Megas and forms)
        out.append({"root": root, "dex": d, "chain": chain, "nevo": nevo, "tag": tag, "rows": rows,
                    "pic": root})
    regions = []
    for name, lo, hi in REGIONS:
        fs = sorted((f for f in out if lo <= f["dex"] <= hi), key=lambda f: f["dex"])
        if len(fs) > MAX_ROWS:
            cut = len(fs) // 2
            regions += [(name + " 1", fs[:cut]), (name + " 2", fs[cut:])]
        elif fs:
            regions.append((name, fs))
    assert sum(len(f) for _, f in regions) == len(out), "a family outside every region"
    return regions


rows = families                                          # the patcher's name for the chapter's rows

ARROWB = bytes((0, ARROW, 0))


def row_title(rom, f):
    """ "Bulbasaur -> Ivysaur -> Venusaur", shortened to fit beside the tag ("Eevee -> Vaporeon +9")."""
    room = ROW_W - (width(rom, J.enc(f["tag"])) + 6 if f["tag"] else 0)
    names = [J.enc(n) for n in f["chain"]]
    total = f["nevo"]                                    # evolutions only: Megas and forms show as the tag
    for keep in range(len(names), 0, -1):
        shown = keep - 1                                 # evolutions named in the title
        more = total - shown
        t = ARROWB.join(names[:keep]) + (J.enc(" +%d" % more) if more > 0 else b"")
        if width(rom, t) <= room:
            return t
    return names[0]


def cell(rom, text, fallback, w):
    b = J.enc(text)
    if width(rom, b) <= w:
        return b
    b = J.enc(fallback)
    if width(rom, b) <= w:
        return b
    while width(rom, b + J.enc("…")) > w and len(b) > 1:
        b = b[:-1]
    return b + J.enc("…")


UP = 0x79                               # the font's up arrow: "Lv" + UP + "16" as in SoulGold's "Lv^16"
SMALLW = 0x00633AE4                     # the small narrow font's glyph widths (font 8: matches its text on screen)
LINES = 9                               # the right box: every line of a family on one page
LINE_Y0, LINE_DY = 35, 10              # the glyphs' ink is 10 rows: a line only covers the empty foot of the one above
RIGHT_X = 83                            # the right box's first text column
RIGHT_END = 236
INDENT, BALL_W = 6, 10
LIST_W = 70                             # the left list's text width


def swidth(rom, b):
    return sum(rom[SMALLW + x] for x in b)


def how_bytes(how):
    """A method as the page writes it: "Lv. 16" -> "Lv^16" (the font's up arrow)."""
    return J.enc(how).replace(J.enc("Lv. "), J.enc("Lv") + bytes((UP,)))


def swrap(rom, b, w):
    out, cur = [], b""
    for word in b.split(b"\x00"):
        cand = word if not cur else cur + b"\x00" + word
        if swidth(rom, cand) <= w or not cur:
            cur = cand
        else:
            out.append(cur)
            cur = word
    out.append(cur)
    return out


def page_lines(rom, f):
    """[(x, ball, text)]: one line per Pokemon a family reaches, its methods merged ("Glaceon: Ice Stone/Ancient
    Tomb"), indented by stage; a line too wide continues under its text."""
    merged = {}
    order = []
    for depth, src, dst, how, how2, t, sp in f["rows"]:
        k = (depth, dst)
        if k not in merged:
            merged[k] = []
            order.append(k)
        if how not in merged[k]:
            merged[k].append(how)
    out = []
    for depth, dst in order:
        hows = merged[(depth, dst)]
        x = RIGHT_X + INDENT * depth
        w = RIGHT_END - x - BALL_W
        text = J.enc(dst) + J.enc(": ") + b"/".join(how_bytes(h) for h in hows).replace(b"/", J.enc("/"))
        if len(hows) == 1:
            text += J.enc(".")
        lines = swrap(rom, text, w)
        out.append((x, 1, lines[0]))
        out += [(x + BALL_W, 0, l) for l in lines[1:]]
    return out


def icons_of(f):
    seen, out = set(), []
    for sp in [f["root"]] + [x for r in f["rows"] for x in (r[6], r[5])]:   # sources too: Alolan Vulpix
        if sp not in seen:
            seen.add(sp)
            out.append(sp)
    return out[:10]


def all_families(rom):
    """Every family, in National Dex order of its first Pokemon (the regions joined)."""
    return sorted((f for _, fs in families(rom) for f in fs), key=lambda f: f["dex"])


def blob(base, rom, wrap_px, pane, locw):
    """{EVOALL: the table}, then the table (16 bytes a family: {dex u16, 0, list name, hint, record}); a record is
    {icons u8, lines u8, x0 u8, dx u8, species u16 x 10, lines 9 x {x, y, ball, 0, text}}.
    Returns (bytes, 1, [("Evolutions", families)])."""
    fs = all_families(rom)
    d = bytearray(4)
    strings = {}

    def string(b):
        if b not in strings:
            strings[b] = len(d)
            d.extend(b)
        return base + strings[b]

    def put(b):
        while len(d) % 4:
            d.append(0)
        a = base + len(d)
        d.extend(b)
        return a

    hint = pane("You have not seen this Pokémon yet.")
    tab = bytearray(16 * len(fs))
    for i, f in enumerate(fs):
        lines = page_lines(rom, f)
        assert len(lines) <= LINES, "%s needs %d lines" % (f["chain"][0], len(lines))
        recl = b""
        for k, (x, ball, t) in enumerate(lines):
            recl += struct.pack("<BBBBI", x, LINE_Y0 + LINE_DY * k, ball, 0, string(t + b"\xff"))
        recl += b"\xff" * (8 * (LINES - len(lines)))
        ic = icons_of(f)
        dx = min(30, 212 // max(1, len(ic) - 1)) if len(ic) > 1 else 0
        x0 = 120 - dx * (len(ic) - 1) // 2
        rec = struct.pack("<BBBB", len(ic), len(lines), x0, dx) + struct.pack("<10H", *(ic + [0] * (10 - len(ic))))
        listname = J.enc("%03d " % f["dex"]) + J.enc(f["chain"][0])
        assert swidth(rom, listname) <= LIST_W, listname
        struct.pack_into("<HHIII", tab, 16 * i, f["dex"], 0, string(listname + b"\xff"), string(hint),
                         put(rec + recl))
    struct.pack_into("<I", d, 0, put(bytes(tab)))
    return bytes(d), 1, [("Evolutions", len(fs))]


def chapter_name(region):
    """ "Kanto 1" -> "Kanto Evolutions 1", "Johto" -> "Johto Evolutions" """
    base, _, part = region.partition(" ")
    return base + " Evolutions" + (" " + part if part else "")


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    for name, fs in families(rom):
        print(name, len(fs))
        for f in fs[:4]:
            print("   ", text_of(row_title(rom, f).replace(bytes((ARROW,)), b">")), "|", f["tag"])
            for r in f["rows"]:
                print("        %s -> %s | %s" % (r[1], r[2], r[3]))
