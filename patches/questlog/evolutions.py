"""The Quest Log's Evolutions chapter: every evolution in the ROM's own table and every other form a Pokemon takes,
one list for all regions.

The table (EVOS) is 40 bytes a species: five {method u16, parameter u16, target u16, extra u16}. The method's low byte
is the method; a high byte (0x3F / 0xFF) marks a baby whose egg needs an incense, named in `extra`. Methods 250-255
are Mega Evolutions, Primal Reversion and form changes. Measured in this ROM 2026-09-30.

The forms come from tools/romdata/forms.py, the list the guide site's Pokedex uses, so a family's page shows what its
page on the site shows: evolutions, Mega Evolution, Gigantamax, the forms a held item, a move, an ability or a Bag
item brings about, and under "Other forms" the ones nothing in the game turns it into (regional forms that do not
evolve, gift and costume forms). A form the player cannot get at all (forms.TRAINER_ONLY: Eternamax Eternatus) is
left out. A family with more than nine lines runs on to a second or third page.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "journal"))
import journal_patch as J
sys.path.append(os.path.join(HERE, "..", "..", "tools", "romdata"))   # last: that folder has a dis.py of its own
import forms as F                                        # every form change the ROM knows, and what a species is
from species_display import FORMS as NAMED_FORMS, display_name
from display_names import item_name as item_display, move_name as move_display

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
    """the item's name as the guide site prints it: the 14-character table cuts some ("RevengerArmor")"""
    return item_display(i, text_of(bytes(rom[J.ITEMS + 44 * i:J.ITEMS + 44 * i + 14]).split(b"\xff")[0]))


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


MOVE_NAMES = 0x148                      # ROM header: the move names (13 bytes a name)
OTHER = "Other forms"                   # the line above the forms nothing in the game turns it into
KINDS = ("Mega", "G-Max", "Primal", "Ultra")


def short_name(name):
    """The site's name, cut where the page's line is short: "Gigantamax Venusaur" -> "G-Max Venusaur"."""
    return name.replace("Gigantamax ", "G-Max ")


def families(rom):
    """[(region, [family, ...])]; a family is {root, dex, chain, nevo, tag, rows [(depth, from, to, how,
    how_short, target species, source species)], others [species], label, pic}. A row is an evolution or a form
    change; `others` are the forms that share a National Dex number with a member and that nothing turns it into."""
    spname = names(rom)
    moves = {int(k): move_display(v["name"] if isinstance(v, dict) else v)
             for k, v in json.load(open(os.path.join(ROMDATA, "moves.json"), encoding="utf-8")).items()}
    places = {int(k): v["name"] for k, v in
              json.load(open(os.path.join(ROMDATA, "mapsections.json"), encoding="utf-8")).items()}
    exists = {sp for sp in range(1, NSPECIES) if F.is_species(rom, sp, NAMED_FORMS)} - set(F.TRAINER_ONLY)
    dex = {sp: F.natdex(rom, sp) for sp in range(1, NSPECIES)}
    for sp in exists:                                    # a Gigantamax slot has no number: its species' one
        if not dex[sp] and sp not in F.NO_NUMBER:
            dex[sp] = next((dex[o] for o in range(1, NSPECIES) if o != sp and dex[o] and spname(o) == spname(sp)), 0)
    first = {}                                           # National Dex number -> its base species
    for sp in range(1, NSPECIES):
        if sp in exists and dex[sp]:
            first.setdefault(dex[sp], sp)

    def full(sp):
        return display_name(sp, text_of(spname(sp)))

    def label(sp):
        """the name the guide site prints, cut short: "Alolan Vulpix", "Wormadam (Sandy Cloak)", "G-Max Charizard" """
        return short_name(full(sp))

    links = F.links(rom, full, lambda i: item_name(rom, i), lambda m: moves.get(m, "a move"), lambda ab: None)
    edges, forms, incoming, reverts = {}, {}, set(), set()
    for ln in links:
        if ln["from"] in exists and ln["to"] in exists:
            forms.setdefault(ln["from"], []).append((ln["to"], ln["short"]))
            incoming.add(ln["to"])
    for sp in range(1, NSPECIES):
        if sp not in exists:
            continue
        o, n = (EEVEE_EVOS, 10) if sp == EEVEE else (EVOS + 40 * sp, 5)
        for k in range(n):
            m, p, t, x = struct.unpack_from("<HHHH", rom, o + 8 * k)
            lo = m & 0xFF
            if not m or t not in exists:
                continue
            if lo == 255:                                # a form's way back to its base (the Gigantamax slots
                reverts.add(sp)                          # 252-276): covered by the base's family
                continue
            if lo >= 250:                                # Mega Evolution and the like: forms.py reads these rows
                continue
            short, shorter, sentence = method(rom, lo, p, sp, t, moves, places, spname, x)
            edges.setdefault(sp, []).append((t, short, shorter))
            incoming.add(t)
    member = set()                                       # in some family's tree

    def collect(sp):
        if sp in member:
            return
        member.add(sp)
        for t, _, _ in edges.get(sp, []):
            collect(t)
        for t, _ in forms.get(sp, []):
            collect(t)

    roots = [sp for sp in sorted(exists) if sp not in incoming and sp not in reverts]
    growing = [r for r in roots if edges.get(r) or forms.get(r)]        # the ones something comes of
    for r in growing:
        collect(r)
    fam = {}
    for r in growing:
        if dex[r]:
            fam.setdefault(dex[r], []).append(r)
    out = []
    for d, rs in fam.items():
        rs.sort(key=lambda r: (r != first.get(d), r))
        base = first.get(d)
        # the page is headed by the number's own species; when only a form of it evolves (Basculin: the
        # White-Striped one), that form gets a line of its own with its evolutions under it
        root = base if base is not None and (base in rs or base not in member) else rs[0]
        rows, seen, kinds, inside = [], set(), [], {root}

        def walk(sp, depth):
            src = label(sp)
            inside.add(sp)
            for t, short, shorter in edges.get(sp, []):
                key = (src, label(t), short)
                if key in seen:                          # reads the same as one already listed (Burmy's cloaks)
                    continue
                seen.add(key)
                rows.append((depth, src, label(t), short, shorter, t, sp))
                if t != sp and t not in rs and t not in inside:
                    walk(t, depth + 1)
            for t, how in forms.get(sp, []):
                name = label(t)
                key = (src, name, how)
                if key in seen:
                    continue
                seen.add(key)
                rows.append((depth, src, name, how, how, t, sp))
                kinds.append(name.split()[0])            # Mega / G-Max / Primal / Ultra
                if t not in inside:                      # a form of a form: Ash-Greninja, Ultra Necrozma
                    walk(t, depth + 1)

        for r in rs:
            if r in inside and r != root:
                continue
            if r == root:
                walk(r, 0)
            else:                                        # Alolan Vulpix: its own line, then what comes of it
                rows.append((0, label(root), label(r), "", "", r, root))
                walk(r, 1)
        # the row: the main line (first branch at every stage), "+N" for the other branches
        chain, sp, walked = [label(root)], root, {root}
        while edges.get(sp) and edges[sp][0][0] not in walked:
            sp = edges[sp][0][0]
            walked.add(sp)
            chain.append(label(sp))
        nevo = len(rows) - sum(1 for r in rows if r[2].split()[0] in KINDS)
        out.append({"root": root, "dex": d, "chain": chain, "nevo": nevo, "tag": "", "rows": rows, "others": [],
                    "inside": inside, "numbers": {dex[sp] for sp in inside if dex[sp]}, "label": label, "pic": root})
    # The forms nothing leads to (regional forms that do not evolve, gift and costume forms) go under "Other forms"
    # in the family that holds their number; where no family does, the species and its forms make a page.
    home = {}
    for f in out:
        for n in f["numbers"]:
            home.setdefault(n, f)
    loose = {}
    for sp in sorted(exists):
        if sp in member or not dex[sp] or any(sp in f["inside"] for f in out):
            continue
        if dex[sp] in home:
            f = home[dex[sp]]
            if label(sp) not in {label(o) for o in f["inside"] | set(f["others"])}:    # (Enamorus has a second slot)
                f["others"].append(sp)
        elif label(sp) not in {label(o) for o in loose.get(dex[sp], [])}:
            loose.setdefault(dex[sp], []).append(sp)
    for d, sps in loose.items():
        if len(sps) < 2:
            continue                                     # a Pokemon alone: nothing to list
        sps.sort(key=lambda sp: (sp != first.get(d), sp))
        out.append({"root": sps[0], "dex": d, "chain": [label(sps[0])], "nevo": 0, "tag": "", "rows": [],
                    "others": sps[1:], "inside": {sps[0]}, "numbers": {d}, "label": label, "pic": sps[0]})
    regions = []
    for name, lo, hi in REGIONS:
        fs = sorted((f for f in out if lo <= f["dex"] <= hi), key=lambda f: f["dex"])
        if len(fs) > MAX_ROWS:
            parts = -(-len(fs) // MAX_ROWS)
            size = -(-len(fs) // parts)
            regions += [("%s %d" % (name, k + 1), fs[k * size:(k + 1) * size]) for k in range(parts)]
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
    """[(x, ball, text, species or None)]: one line per Pokemon a family reaches, its methods merged ("Glaceon: Ice
    Stone/Ancient Tomb"), indented by stage; a line too wide continues under its text. Then "Other forms" and one
    line for each."""
    merged = {}
    order = []
    for depth, src, dst, how, how2, t, sp in f["rows"]:
        k = (depth, dst)
        if k not in merged:
            merged[k] = ([], t)
            order.append(k)
        if how not in merged[k][0]:
            merged[k][0].append(how)
    out = []
    for depth, dst in order:
        hows, t = merged[(depth, dst)]
        x = RIGHT_X + INDENT * min(depth, 3)
        w = RIGHT_END - x - BALL_W
        hows = [h for h in hows if h]
        text = J.enc(dst)
        if hows:                                         # (none: a regional form heading its own evolutions)
            text += J.enc(": ") + b"/".join(how_bytes(h) for h in hows).replace(b"/", J.enc("/"))
        if len(hows) == 1:
            text += J.enc(".")
        lines = swrap(rom, text, w)
        out.append((x, 1, lines[0], t))
        out += [(x + BALL_W, 0, l, None) for l in lines[1:]]
    if f["others"]:
        if out:
            out.append((RIGHT_X, 0, J.enc(OTHER), None))
        for sp in f["others"]:
            lines = swrap(rom, J.enc(f["label"](sp)), RIGHT_END - RIGHT_X - BALL_W)
            out.append((RIGHT_X, 1, lines[0], sp))
            out += [(RIGHT_X + BALL_W, 0, l, None) for l in lines[1:]]
    return out


def pages_of(lines):
    """The lines in pages of LINES at most: a line is not parted from what it runs on to, and the "Other forms"
    heading not from the first of them."""
    heading = J.enc(OTHER)
    pages, cur = [], []
    i = 0
    while i < len(lines):
        group = [lines[i]]
        i += 1
        if group[0][2] == heading and not group[0][1] and i < len(lines):     # the heading: with the form under it
            group.append(lines[i])
            i += 1
        while i < len(lines) and not lines[i][1] and lines[i][2] != heading:  # and the rest of a long line
            group.append(lines[i])
            i += 1
        if len(cur) + len(group) > LINES and cur:
            pages.append(cur)
            cur = []
        cur += group
    if cur:
        pages.append(cur)
    assert all(len(p) <= LINES for p in pages), "a line longer than the page"
    return pages


def icons_of(f, page):
    """the root, then the Pokemon this page's lines name (ten at most)"""
    seen, out = set(), []
    for sp in [f["root"]] + [t for _, _, _, t in page if t is not None]:
        if sp not in seen:
            seen.add(sp)
            out.append(sp)
    return out[:10]


def all_families(rom):
    """Every family, in National Dex order of its first Pokemon (the regions joined)."""
    return sorted((f for _, fs in families(rom) for f in fs), key=lambda f: f["dex"])


def list_pages(rom):
    """[(family, page number from 1, pages, its lines)]: what the list shows, in order."""
    out = []
    for f in all_families(rom):
        pages = pages_of(page_lines(rom, f))
        for k, page in enumerate(pages):
            out.append((f, k + 1, len(pages), page))
    return out


def list_name(rom, f, k):
    """ "025 Pikachu", and "025 Pikachu 2" for a family's second page; a name too wide for the list is cut."""
    head = J.enc("%03d " % f["dex"])
    tail = J.enc(" %d" % k) if k > 1 else b""
    whole = J.enc(f["chain"][0])
    name = whole
    if swidth(rom, head + name + tail) > LIST_W:
        dots = J.enc("…")
        while swidth(rom, head + name + dots + tail) > LIST_W and len(name) > 1:
            name = name[:-1]
        name += dots
    return head + name + tail


def blob(base, rom, wrap_px, pane, locw):
    """{EVOALL: the table}, then the table (16 bytes a list row: {dex u16, 0, list name, hint, record}); a record is
    {icons u8, lines u8, x0 u8, dx u8, species u16 x 10, then `lines` x {x, y, ball, 0, text}}. A family with more
    than nine lines has a row for each of its pages.
    Returns (bytes, 1, [("Evolutions", rows)])."""
    rows = list_pages(rom)
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
    tab = bytearray(16 * len(rows))
    for i, (f, k, of, lines) in enumerate(rows):
        recl = b""
        for n, (x, ball, t, _) in enumerate(lines):
            recl += struct.pack("<BBBBI", x, LINE_Y0 + LINE_DY * n, ball, 0, string(t + b"\xff"))
        # (only the lines it has: evo_draw reads `lines` of them, and the rows' records need not be one size)
        ic = icons_of(f, lines)
        dx = min(30, 212 // max(1, len(ic) - 1)) if len(ic) > 1 else 0
        x0 = 120 - dx * (len(ic) - 1) // 2
        rec = struct.pack("<BBBB", len(ic), len(lines), x0, dx) + struct.pack("<10H", *(ic + [0] * (10 - len(ic))))
        listname = list_name(rom, f, k)
        assert swidth(rom, listname) <= LIST_W, listname
        struct.pack_into("<HHIII", tab, 16 * i, f["dex"], 0, string(listname + b"\xff"), string(hint),
                         put(rec + recl))
    struct.pack_into("<I", d, 0, put(bytes(tab)))
    return bytes(d), 1, [("Evolutions", len(rows))]


def chapter_name(region):
    """ "Kanto 1" -> "Kanto Evolutions 1", "Johto" -> "Johto Evolutions" """
    base, _, part = region.partition(" ")
    return base + " Evolutions" + (" " + part if part else "")


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    want = [a.lower() for a in sys.argv[2:]]
    rows = list_pages(rom)
    fams = all_families(rom)
    print("%d families, %d list rows, %d with more than one page, most lines on a page %d" % (
        len(fams), len(rows), sum(1 for f, k, of, _ in rows if k == 2), max(len(l) for _, _, _, l in rows)))
    for i, (f, k, of, lines) in enumerate(rows):
        title = text_of(list_name(rom, f, k))
        if want and not any(x in title.lower() for x in want):
            continue
        print("%4d  %s   icons %s" % (i, title, [f["label"](sp) for sp in icons_of(f, lines)]))
        for x, ball, t, _ in lines:
            print("          %s%s%s" % (" " * ((x - RIGHT_X) // 3), "o " if ball else "  ", text_of(t)))
