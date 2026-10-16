"""Gen 9 legendaries, mythicals, Paradox Pokemon and the Baxcalibur line: 38 new species (Hyper Emerald v5.7).
usage: python gen9_patch.py <in.gba> <out.gba> <Crest_v1.0.F.gba> [--no-effects]

Apply after speciesx (it writes into the slots that patch makes, 1200-1237). Nothing in the game hands these
Pokemon out yet: this patch makes them exist, complete, and working in battle.

Where each thing comes from:
  official.json     stats, types, abilities, level-up moves, what each can learn, Pokedex text: the official
                    Scarlet/Violet data (PokeAPI; make_official.py rebuilds the file, not needed to build).
  the Crest ROM     pictures, palettes, icons and cries. Crest is a pokeemerald-expansion build, so these are that
                    project's community sprites and the games' own cries, already in GBA format. The ROM is not
                    in this repository; the third argument names it (sha1 checked).
  gen9_data.py      slots, names, and how each ability is carried over.

What a species gets: base stats, name, front and back picture, both palettes, icon, where the pictures sit,
cry, a Pokedex number (906-940) with its entry, abilities, level-up moves, TM/HM and tutor bits, and for the
Baxcalibur line evolutions and egg moves.

Moves: the engine's own, plus the seven signature moves Crest has too (gen9_data.NEW_MOVES: Collision Course,
Electro Drift, Ruination, Ivy Cudgel, Hydro Steam, Psyblade, Glaive Rush; ids 938-947, Ivy Cudgel being one id
for each of Ogerpon's four types). The engine's move data and animation tables were made for 1,024 and 1,030
moves and are written in place; the names, the descriptions and the Z-Move / Max Move power tables end at the
last move with other data behind them, so they move to free space with 1,024 entries (63 words repointed).
Scarlet/Violet moves that are in neither game (gen9_data.MOVES_NOT_IN_GAME) are left out of the lists.

Booster Energy: item 769, one of the game's unused "New Item" slots, with Crest's picture of it.

Abilities: the ability name and text tables are 342 entries with code right behind them, so they move to free
space with 1,793 entries (ten words repointed) and the new names go in.

gen9.s then makes all of it work (its header has the rules), through six hooks:
  - the two places the engine reads a species' ability (0x09D00110, 0x09D73A9C): an ability shown under its own
    name but standing on one the engine has (Orichalcum Pulse on Drought, Hadron Engine on Electric Surge...)
    is swapped for that ability the moment the Pokemon enters battle or the engine looks one up;
  - two entries of the engine's command table (0x09D7717C), each running the engine's own routine too:
    5, the damage calculation (the abilities, and what the new moves do beyond a plain hit); 0, a battler
    starts on a move (the mark Glaive Rush left on it comes off);
  - entry 24 of the engine's second table of routines (0x09D79EAC, which battle scripts call by number): the
    damage of moves that do a set amount, where the engine goes by the move's number (Ruination);
  - the first eight bytes of the engine's speed routine (0x09D5E3F0), for the Speed half of Protosynthesis and
    Quark Drive.
--no-effects leaves gen9.s out (species, names, moves and the item, none of the rules): the tests' control.

Free space: zero-filled ROM at 0x09A10000 (see speciesx_patch.py and NOTES on the zero-filled regions).
"""
import hashlib, itertools, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                         # python -I (for the Crest ROM) leaves the script's folder out
sys.path.insert(0, os.path.join(HERE, "..", "speciesx"))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import speciesx_patch as SX                      # the table layout, and which words count as code
import sinnohmap_patch as SM                     # the Thumb check
import gen9_data as D

CREST_SHA1 = "e892062af4a74e9dafdba45a64f4f644da558de4"
CREST_CRY, CREST_ELEVATION, CREST_INFO = 0x101D3D8, 0x03A890C, 36     # found by content; asserted below
CREST_ITEMS, CREST_ITEM_ICONS = 0x0EB686C, 0x0F70A30                  # 40 bytes an item; {picture, palette}
SPACE, SPACE_END = 0x01A10000, 0x01B00000        # 0x09A10000..0x09B00000, zero-filled

# the engine's move tables: 938 moves (0-937) in each
MOVE_NAMES_AT, MOVE_TEXT, MOVE_DATA, MOVE_ANIMS = 0x01D30258, 0x01D2AD00, 0x01D86419, 0x01D0AB00
Z_POWER, MAX_POWER, OLD_MOVES = 0x01D8A838, 0x01D86050, 938     # a byte a move, read with the move a Z-Move or
MOVE_NAME_WORDS, MOVE_TEXT_WORDS, Z_POWER_WORDS, MAX_POWER_WORDS = 58, 2, 2, 1     # Max Move was made from
DEFAULT_ANIM = 0x09D0BB18                        # what the animation table holds for ids nobody uses
ITEMS, ITEM_ICONS = 0x00FC2C7C, 0x00FCBFF4       # 44 bytes an item; {picture, palette}, both compressed

ABILITY_TABLE = 0x017A0000                       # three u16 a species
ABILITY_NAMES, ABILITY_TEXT, OLD_ABILITIES = 0x01D03068, 0x01D00218, 342
ABILITY_NAME_WORDS, ABILITY_TEXT_WORDS = 8, 2
DEX_ENTRIES = 0x01250000                         # 32 bytes a number
CRY, CRY_REVERSE, CRY_IDS = 0x00F484E0, 0x00F4BD20, 0x00F4FA10
GMAX_CRY_IDS = 0x0032A920                        # the cry ids of species 252-276 (the hack's own routine)
TM_LIST, TM_COUNT = 0x01E0FE80, 128
TUTOR_LIST, TUTOR_COUNT = 0x00FD80B8, 127
EGG_MOVES, EGG_END, EGG_BOUND = 0x01D78128, 0x01D7973C, 0x00070464
ICON_PALETTES = 0x0057C540
DEX_WIDTH, DEX_LINES = 38, 4

CHARS = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARS.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({" ": 0x00, "!": 0xAB, "?": 0xAC, ".": 0xAD, "-": 0xAE, "…": 0xB0, "“": 0xB1, "”": 0xB2,
              "‘": 0xB3, "’": 0xB4, "'": 0xB4, ",": 0xB8, "/": 0xBA, ":": 0xF0, "é": 0x1B, "%": 0x5B,
              "(": 0x5C, ")": 0x5D, "\n": 0xFE, "—": 0xAE, "–": 0xAE})


def text(s):
    return bytes(CHARS[c] for c in s) + b"\xff"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def wrap(s, width, lines):
    out, cur = [], ""
    for word in s.split():
        if cur and len(cur) + 1 + len(word) > width:
            out.append(cur)
            cur = word
        else:
            cur = (cur + " " + word) if cur else word
    out.append(cur)
    return "\n".join(out) if len(out) <= lines and max(map(len, out)) <= width else None


def lz_dec(d, o):
    assert d[o] == 0x10
    size = d[o + 1] | d[o + 2] << 8 | d[o + 3] << 16
    out, o = bytearray(), o + 4
    while len(out) < size:
        flags = d[o]
        o += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                n, disp = (d[o] >> 4) + 3, ((d[o] & 0xF) << 8 | d[o + 1]) + 1
                o += 2
                for _ in range(n):
                    out.append(out[-disp])
            else:
                out.append(d[o])
                o += 1
    return bytes(out[:size])


def lz_comp(data):
    """BIOS LZ77, greedy, never a distance of 1 (LZ77UnCompVram cannot read one back)."""
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


def pixels(pic):
    """64x64 4bpp tiles -> rows of colour indexes"""
    rows = [[0] * 64 for _ in range(64)]
    for t in range(64):
        for y in range(8):
            for x in range(8):
                b = pic[t * 32 + y * 4 + x // 2]
                rows[t // 8 * 8 + y][t % 8 * 8 + x] = b >> 4 if x & 1 else b & 15
    return rows


def coordinates(pic):
    """{size, y offset, 0, 0} as the game's own tables hold them: the picture's box in tiles, and how far it
    floats above the bottom of its 64x64 frame"""
    rows = pixels(pic)
    ys = [y for y in range(64) if any(rows[y])]
    xs = [x for x in range(64) if any(rows[y][x] for y in range(64))]
    w, h = xs[-1] - xs[0] + 1, ys[-1] - ys[0] + 1
    return bytes([((w + 7) // 8) << 4 | (h + 7) // 8, 63 - ys[-1], 0, 0])


def rgb(c):
    return (c & 31, c >> 5 & 31, c >> 10 & 31)


def fit_icon(icon, source, palettes):
    """An icon drawn with a palette this game does not have, redrawn with the closest of the three it has."""
    use = [0] * 16
    for b in icon:
        use[b & 15] += 1
        use[b >> 4] += 1
    best = None
    for index, pal in enumerate(palettes):
        remap, err = [0] * 16, 0
        for c in range(1, 16):
            if use[c]:
                near = min(range(1, 16), key=lambda k: sum((a - b) ** 2 for a, b in zip(rgb(source[c]), rgb(pal[k]))))
                remap[c] = near
                err += use[c] * sum((a - b) ** 2 for a, b in zip(rgb(source[c]), rgb(pal[near])))
        if best is None or err < best[0]:
            best = (err, index, remap)
    err, index, remap = best
    return bytes(remap[b & 15] | remap[b >> 4] << 4 for b in icon), index


class Crest:
    """The few tables of Crest v1.0.F this patch reads (a pokeemerald-expansion build: the ROM header at
    0x128-0x1BC still names the picture, palette, icon and species tables)."""
    def __init__(self, path):
        with open(path, "rb") as f:
            self.d = f.read()
        assert hashlib.sha1(self.d).hexdigest() == CREST_SHA1, "not Crest_v1.0.F.gba"
        h = lambda o: struct.unpack_from("<I", self.d, o)[0] - 0x08000000
        self.front, self.back, self.pal, self.shiny, self.icon = h(0x128), h(0x12C), h(0x130), h(0x134), h(0x138)
        self.icon_pal_id, self.icon_pals, self.info = h(0x13C), h(0x140), h(0x1BC)
        assert self.d[self.info + CREST_INFO:self.info + CREST_INFO + 6] == bytes([45, 49, 49, 45, 65, 65])
        assert self.d[CREST_CRY:CREST_CRY + 4] == bytes([0x20, 0x3C, 0, 0]) and self.d[CREST_ELEVATION + 12] == 10

    def ptr(self, o):
        v = struct.unpack_from("<I", self.d, o)[0]
        return v - 0x08000000 if 0x08000000 <= v < 0x08000000 + len(self.d) else None

    def picture(self, table, s):
        return lz_dec(self.d, self.ptr(table + 8 * s))[:2048]

    def palette(self, table, s):
        raw = lz_dec(self.d, self.ptr(table + 8 * s))
        return raw + bytes(32 - len(raw))                    # some hold fewer than 16 colours

    def icon_of(self, s):
        o = self.ptr(self.icon + 4 * s)
        return self.d[o:o + 1024], self.d[self.icon_pal_id + s]

    def icon_palette(self, k):
        o = self.ptr(self.icon_pals + 8 * k)
        return struct.unpack_from("<16H", self.d, o)

    def cry(self, s):
        """the species' cry sample (m4a WaveData, compressed), whole"""
        tone = self.d[CREST_CRY + 12 * (s - 1):CREST_CRY + 12 * s]
        assert tone[:4] == bytes([0x20, 0x3C, 0, 0]) and tone[8:] == bytes([0xFF, 0, 0xFF, 0])
        o = struct.unpack_from("<I", tone, 4)[0] - 0x08000000
        kind, _, freq, loop, size = struct.unpack_from("<HHIII", self.d, o)
        assert kind == 1 and loop == 0, "cry is not a compressed one-shot sample"
        n = 16 + (size // 64) * 33 + ((1 + (size % 64 + 1) // 2) if size % 64 else 0)
        return self.d[o:o + n] + bytes(-n % 4)

    def item_icon(self, item, name):
        """an item's picture (24x24, 4bpp) and palette, decompressed"""
        row = CREST_ITEMS + 40 * item
        assert self.d[row:row + len(name) + 1] == text(name), "Crest's item %d is not %s" % (item, name)
        pic = lz_dec(self.d, self.ptr(CREST_ITEM_ICONS + 8 * item))
        pal = lz_dec(self.d, self.ptr(CREST_ITEM_ICONS + 8 * item + 4))
        assert len(pic) == 288 and len(pal) == 32
        return pic, pal


def build(inp, outp, crest_path, effects=True):
    with open(inp, "rb") as f:
        rom = bytearray(f.read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    crest = Crest(crest_path)
    with open(os.path.join(HERE, "official.json"), encoding="utf-8") as f:
        official = json.load(f)
    u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    lay = SX.layout()
    size_of = {t[0]: t[2] for t in SX.TABLES}

    # ---- speciesx is in, this patch is not
    for hdr, name in ((0x128, "front pictures"), (0x12C, "back pictures"), (0x130, "palettes"),
                      (0x134, "shiny palettes"), (0x138, "icons"), (0x13C, "icon palette ids"), (0x144, "names"),
                      (0x1BC, "base stats")):
        assert u32(hdr) == 0x08000000 + lay[name], "apply speciesx first (%s is not where it puts it)" % name
    assert u32(0x1C0) == 0x08000000 + ABILITY_NAMES and u32(0x1C4) == 0x08000000 + ABILITY_TEXT, "already applied"
    assert not any(rom[SPACE:SPACE_END]), "the target region is not empty"
    first, last = D.FIRST_SLOT, D.FIRST_SLOT + len(D.SPECIES) - 1
    assert last < SX.NEW_N - 1
    for name in ("base stats", "names", "evolutions", "TM/HM bits"):
        o = lay[name] + size_of[name] * first
        assert set(rom[o:o + size_of[name] * len(D.SPECIES)]) <= ({0, 0xFF} if name == "names" else {0}), \
            "slots %d-%d are not blank (%s)" % (first, last, name)
    moving = {0x08000000 + t: [] for t in (ABILITY_NAMES, ABILITY_TEXT, MOVE_NAMES_AT, MOVE_TEXT, Z_POWER, MAX_POWER)}
    for i, v in enumerate(struct.unpack_from("<%dI" % (len(rom) // 4), rom)):
        if 0x08000000 + SPACE <= v < 0x08000000 + SPACE_END:
            assert not SX.is_pointer(rom, i * 4), "%08X points into the target region" % (0x08000000 + i * 4)
        elif v in moving:
            moving[v].append(i * 4)                          # every word that holds a table this patch moves

    pos = [SPACE]

    def put(data, align=4):
        o = (pos[0] + align - 1) & ~(align - 1)
        assert o + len(data) <= SPACE_END
        rom[o:o + len(data)] = data
        pos[0] = o + len(data)
        return 0x08000000 + o

    def row(table, slot, data):
        assert len(data) == size_of[table], table
        rom[lay[table] + len(data) * slot:lay[table] + len(data) * (slot + 1)] = data

    # ---- the ability name and text tables, longer
    def repoint(old, new, expect, what):
        at = moving[0x08000000 + old]
        assert len(at) == expect and all(SX.is_pointer(rom, k) for k in at), "%s: %s" % (what, ["%08X" % (0x08000000 + k) for k in at])
        for k in at:
            struct.pack_into("<I", rom, k, new)

    empty = put(b"\xff", 1)
    names = bytearray(rom[ABILITY_NAMES:ABILITY_NAMES + 13 * OLD_ABILITIES])
    names += (b"\xff" + bytes(12)) * (D.ABILITY_COUNT - OLD_ABILITIES)
    texts = list(struct.unpack_from("<%dI" % OLD_ABILITIES, rom, ABILITY_TEXT)) + [empty] * (D.ABILITY_COUNT - OLD_ABILITIES)
    blank_name = bytes(rom[ABILITY_NAMES + 13 * 257:ABILITY_NAMES + 13 * 258])
    new_abilities = [(i, n, t, b) for i, n, b, t in D.ABILITY_ALIAS.values()] + [(i, n, t, None) for i, n, t in D.ABILITY_NEW.values()]
    for ident, name, words_, base in sorted(new_abilities):
        assert ident >= OLD_ABILITIES or bytes(names[13 * ident:13 * ident + 13]) == blank_name, "ability id %d is taken" % ident
        assert base is None or ident == 256 + base, "an alias is 256 + its base"
        assert len(name) <= 12
        names[13 * ident:13 * ident + 13] = text(name) + bytes(12 - len(name))
        if words_ is None:
            texts[ident] = texts[base]                       # it does what its base does: the base's own text
        else:
            assert max(map(len, words_.split("\n"))) <= 27 and words_.count("\n") <= 1
            texts[ident] = put(text(words_), 1)
    repoint(ABILITY_NAMES, put(bytes(names)), ABILITY_NAME_WORDS, "ability names")
    repoint(ABILITY_TEXT, put(struct.pack("<%dI" % len(texts), *texts)), ABILITY_TEXT_WORDS, "ability texts")
    ability_id = dict(D.ABILITY_EXISTING)
    ability_id.update({k: v[0] for k, v in D.ABILITY_ALIAS.items()})
    ability_id.update({k: v[0] for k, v in D.ABILITY_NEW.items()})

    # ---- moves by name: the engine's own, and the new ones by their key
    move_names = u32(0x148) - 0x08000000
    assert move_names == MOVE_NAMES_AT, "the move names are not where they were"
    by_norm = {}
    for m in range(1, 937):
        raw = bytes(rom[move_names + 13 * m:move_names + 13 * m + 13]).split(b"\xff")[0]
        nm = "".join({v: k for k, v in CHARS.items() if len(k) == 1}.get(b, "?") for b in raw)
        if nm.strip("-"):
            by_norm.setdefault(norm(nm), m)
    new_move = {row[0]: D.FIRST_MOVE + i for i, row in enumerate(D.NEW_MOVES)}

    def move(official_name, species=None):
        official_name = D.MOVE_BY_SPECIES.get((official_name, species), official_name)
        if official_name in new_move:
            return new_move[official_name]
        if official_name in D.MOVES_NOT_IN_GAME:
            return None
        m = by_norm.get(norm(D.MOVE_NAMES.get(official_name, official_name)))
        assert m, "%s: not in the game under that name, and not listed as missing" % official_name
        return m

    tm_moves = [u16(TM_LIST + 2 * i) for i in range(TM_COUNT)]
    tutor_moves = [u16(TUTOR_LIST + 2 * i) for i in range(TUTOR_COUNT)]
    assert all(0 < m < 937 for m in tm_moves + tutor_moves), "the TM or tutor list moved"

    # ---- cry ids nobody uses
    used = set(range(251)) | {u16(CRY_IDS + 2 * (s - 277)) for s in range(277, SX.OLD_N)} | \
        {u16(GMAX_CRY_IDS + 2 * k) for k in range(25)}
    free_cries = [i for i in range(388, SX.OLD_N) if i not in used]
    assert max(used) == 387 and len(free_cries) >= len(D.SPECIES), "cry ids are not laid out as expected"

    icon_palettes = [struct.unpack_from("<16H", rom, u32(ICON_PALETTES + 8 * k) - 0x08000000) for k in range(3)]
    slot_of = {key: first + i for i, (key, *_rest) in enumerate(D.SPECIES)}
    report, dex, missing_moves = [], D.FIRST_DEX - 1, set()
    for i, (key, name, crest_id, crest_icon, same_dex) in enumerate(D.SPECIES):
        slot, o, notes = first + i, official[key], []
        assert len(name) <= 10
        st = o["stats"]

        # base stats: 28 bytes (the ability bytes at +22, +23, +26 are not what the game reads: left 0)
        types = [D.TYPES[t] for t in o["types"]]
        b = bytearray(28)
        b[0:6] = bytes([st["hp"], st["atk"], st["def"], st["spe"], st["spa"], st["spd"]])
        b[6], b[7], b[8], b[9] = types[0], types[-1], o["catch"], min(255, o["exp"])
        ev = o["ev"]
        struct.pack_into("<H", b, 10, sum(ev.get(k, 0) << 2 * n for n, k in enumerate(("hp", "atk", "def", "spe", "spa", "spd"))))
        b[16] = 255 if o["gender_rate"] < 0 else min(254, max(0, o["gender_rate"] * 32 - 1))
        b[17], b[18], b[19] = o["hatch"], o["friendship"], D.GROWTH[o["growth"]]
        groups = [D.EGG_GROUPS[g] for g in o["egg_groups"]]
        b[20], b[21] = groups[0], groups[-1]
        b[25] = D.COLORS[o["color"]] | (crest.d[crest.info + CREST_INFO * crest_id + 31] & 0x80)     # + "do not flip"
        row("base stats", slot, bytes(b))
        row("names", slot, text(name) + bytes(10 - len(name)))

        # pictures and palettes (tags as the hack gives every species it added: 1, and 501 for the shiny one)
        front, back = crest.picture(crest.front, crest_id), crest.picture(crest.back, crest_id)
        row("front pictures", slot, struct.pack("<IHH", put(lz_comp(front)), 0x800, 1))
        row("back pictures", slot, struct.pack("<IHH", put(lz_comp(back)), 0x800, 1))
        row("palettes", slot, struct.pack("<IHH", put(lz_comp(crest.palette(crest.pal, crest_id))), 1, 0))
        row("shiny palettes", slot, struct.pack("<IHH", put(lz_comp(crest.palette(crest.shiny, crest_id))), 501, 0))
        row("front coordinates", slot, coordinates(front))
        row("back coordinates", slot, coordinates(back))
        row("elevation", slot, bytes([crest.d[CREST_ELEVATION + crest_id]]))

        icon, pal = crest.icon_of(crest_icon)
        if pal > 2:                                           # Crest has six icon palettes, this game three
            icon, new = fit_icon(icon, crest.icon_palette(pal), icon_palettes)
            notes.append("icon redrawn from Crest's palette %d with palette %d" % (pal, new))
            pal = new
        row("icons", slot, struct.pack("<I", put(icon)))
        row("icon palette ids", slot, bytes([pal]))

        # cry
        cry = free_cries[i]
        wave = put(crest.cry(crest_id))
        for table, kind in ((CRY, 0x20), (CRY_REVERSE, 0x30)):
            rom[table + 12 * cry:table + 12 * cry + 12] = bytes([kind, 0x3C, 0, 0]) + struct.pack("<I", wave) + bytes([0xFF, 0, 0xFF, 0])
        struct.pack_into("<H", rom, CRY_IDS + 2 * (slot - 277), cry)

        # Pokedex
        if not same_dex:
            dex += 1
            e = DEX_ENTRIES + 32 * dex
            assert rom[e:e + 5] == text("Seed") and u32(e + 16) == 0x0855D389, "dex entry %d is not a placeholder" % dex
            category = o["genus"].replace(" Pokémon", "")
            assert len(category) <= 11
            words_ = next((w for w in (wrap(o["flavor"][v], DEX_WIDTH, DEX_LINES) for v in ("scarlet", "violet")) if w), None)
            assert words_, "%s: no dex text fits %d lines of %d" % (key, DEX_LINES, DEX_WIDTH)
            rom[e:e + 12] = text(category) + bytes(11 - len(category))
            struct.pack_into("<HHI", rom, e + 12, o["height"], o["weight"], put(text(words_), 1))
        struct.pack_into("<H", rom, lay["national dex no."] + 2 * (slot - 1), dex)

        # abilities: two regular slots, then the hidden one (a single ability fills all three, as the hack does)
        regular = [ability_id[a] for a, hidden in o["abilities"] if not hidden]
        hidden = [ability_id[a] for a, hidden in o["abilities"] if hidden]
        struct.pack_into("<HHH", rom, ABILITY_TABLE + 6 * slot, regular[0], regular[-1], (hidden or regular)[0])

        # moves
        levelup = bytearray()
        for level, mv in o["levelup"]:
            m = move(mv, key)
            if m is None:
                missing_moves.add(mv)
            else:
                levelup += struct.pack("<HB", m, level)
        struct.pack_into("<I", rom, lay["level-up pointers"] + 4 * slot, put(bytes(levelup) + b"\x00\x00\xff", 1))
        can = {move(mv, key) for mv in [m for _, m in o["levelup"]] + o["machine"] + o["tutor"] + o["egg"]} - {None}
        tm = sum(1 << n for n, m in enumerate(tm_moves) if m in can)
        tutor = sum(1 << n for n, m in enumerate(tutor_moves) if m in can)
        row("TM/HM bits", slot, tm.to_bytes(16, "little"))
        row("tutor bits", slot, tutor.to_bytes(16, "little"))
        report.append("  %4d %-10s dex %d  cry %d  level-up %2d  TM/HM %3d  tutor %2d%s" % (
            slot, name, dex, cry, len(levelup) // 3, bin(tm).count("1"), bin(tutor).count("1"),
            ("  | " + "; ".join(notes)) if notes else ""))

    # ---- the Baxcalibur line: evolutions (method 4, by level) and Frigibax's egg moves
    for src, level, dst in D.EVOLUTIONS:
        row("evolutions", slot_of[src], struct.pack("<HHHH", 4, level, slot_of[dst], 0) + bytes(32))
    assert u16(EGG_END) == 0xFFFF and u32(EGG_BOUND) == (EGG_END - EGG_MOVES) // 2 - 1, "the egg move list changed"
    eggs = [20000 + slot_of["frigibax"]] + sorted(m for m in map(move, official["frigibax"]["egg"]) if m)
    assert set(rom[EGG_END + 2:EGG_END + 2 * len(eggs) + 4]) == {0xFF}, "no room after the egg move list"
    struct.pack_into("<%dH" % (len(eggs) + 1), rom, EGG_END, *eggs, 0xFFFF)
    struct.pack_into("<I", rom, EGG_BOUND, u32(EGG_BOUND) + len(eggs))

    moves_line = install_moves(rom, put, repoint, by_norm, empty)
    item_line = install_item(rom, put, crest)
    blob = ""
    if effects:
        blob = install_effects(rom, put, slot_of, new_move, lambda name: by_norm[norm(name)])

    with open(outp, "wb") as f:
        f.write(rom)
    print("\n".join(report))
    print("gen9: %d species in slots %d-%d, dex %d-%d; %d abilities named" % (
        len(D.SPECIES), first, last, D.FIRST_DEX, dex, len(new_abilities)))
    print("gen9: " + moves_line)
    print("gen9: Scarlet/Violet moves left out of the lists: %s" % ", ".join(sorted(missing_moves)))
    print("gen9: " + item_line)
    print("gen9: data %08X..%08X%s" % (0x08000000 + SPACE, 0x08000000 + pos[0], blob))


def install_moves(rom, put, repoint, by_norm, empty):
    """gen9_data.NEW_MOVES. The data and the animation table have room and are written in place; the names, the
    descriptions and the two power tables get a longer copy in free space. Returns a line for the summary."""
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    is_rom = lambda v: 0x08000000 <= v < 0x0A000000
    old, count, first = OLD_MOVES, D.MOVE_COUNT, D.FIRST_MOVE
    row = lambda m: bytes(rom[MOVE_DATA + 12 * m:MOVE_DATA + 12 * m + 12])
    assert first == old and first + len(D.NEW_MOVES) <= count
    assert u32(0x1CC) == 0x08000000 + MOVE_DATA, "the move data is not where it was"
    assert bytes(rom[MOVE_NAMES_AT + 13 * (old - 1):MOVE_NAMES_AT + 13 * old - 1]) == text("Petal Dance"), "not 938 moves"
    # the rows the new ones are modelled on: a plain hit, Super Fang, a high critical-hit ratio without contact
    assert row(33) == bytes.fromhex("002800642300000033000009"), "Tackle's data changed"
    assert row(162) == bytes.fromhex("0101005a0a00000013000009"), "Super Fang's data changed"
    assert row(444) == bytes.fromhex("006405500500000072000009"), "Stone Edge's data changed"
    assert not any(rom[MOVE_DATA + 12 * old:MOVE_DATA + 12 * count]), "move data: ids 938 on are not blank"
    assert all(u32(MOVE_ANIMS + 4 * m) == DEFAULT_ANIM for m in range(old, count)), "animations: ids 938 on are in use"
    assert is_rom(u32(MOVE_TEXT + 4 * (old - 1))) and not is_rom(u32(MOVE_TEXT + 4 * old)), "descriptions: not 938 entries"

    names = bytearray(rom[MOVE_NAMES_AT:MOVE_NAMES_AT + 13 * old]) + (b"\xff" + bytes(12)) * (count - old)
    texts = list(struct.unpack_from("<%dI" % old, rom, MOVE_TEXT)) + [empty] * (count - 1 - old)     # [move - 1]
    z_power = bytearray(rom[Z_POWER:Z_POWER + old]) + bytes(count - old)       # the first 938 as they read today
    max_power = bytearray(rom[MAX_POWER:MAX_POWER + old]) + bytes(count - old)
    for i, (key, name, type_, special, power, accuracy, pp, effect, flags, like, z, mx, words_) in enumerate(D.NEW_MOVES):
        m = first + i
        assert len(name) <= 12 and max(map(len, words_.split("\n"))) <= 30 and words_.count("\n") <= 1, key
        names[13 * m:13 * m + 13] = text(name) + bytes(12 - len(name))
        texts[m - 1] = put(text(words_), 1)
        rom[MOVE_DATA + 12 * m:MOVE_DATA + 12 * m + 12] = bytes(
            [effect, power, D.TYPES[type_], accuracy, pp, 0, 0, 0, flags, 0, special, 9])
        script = u32(MOVE_ANIMS + 4 * by_norm[norm(like)])
        assert is_rom(script) and script != DEFAULT_ANIM, "%s has no animation to lend" % like
        struct.pack_into("<I", rom, MOVE_ANIMS + 4 * m, script)
        z_power[m], max_power[m] = z, mx
    repoint(MOVE_NAMES_AT, put(bytes(names)), MOVE_NAME_WORDS, "move names")
    repoint(MOVE_TEXT, put(struct.pack("<%dI" % len(texts), *texts)), MOVE_TEXT_WORDS, "move descriptions")
    repoint(Z_POWER, put(bytes(z_power)), Z_POWER_WORDS, "Z-Move power")
    repoint(MAX_POWER, put(bytes(max_power)), MAX_POWER_WORDS, "Max Move power")
    return "%d moves, ids %d-%d; the name, description and two power tables moved (%d words repointed)" % (
        len(D.NEW_MOVES), first, first + len(D.NEW_MOVES) - 1,
        MOVE_NAME_WORDS + MOVE_TEXT_WORDS + Z_POWER_WORDS + MAX_POWER_WORDS)


def install_item(rom, put, crest):
    """Booster Energy into an unused item slot. Returns a line for the summary."""
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    item, name, words_ = D.BOOSTER_ENERGY, D.BOOSTER_NAME, D.BOOSTER_TEXT
    row, icon = ITEMS + 44 * item, ITEM_ICONS + 8 * item
    assert u32(0x1C8) == 0x08000000 + ITEMS, "the item table is not where it was"
    blank = text("New Item") + bytes(5) + struct.pack("<HHBBIBBBBIII", item, 0, 0, 0, 0x0857FEA0, 0, 0, 1, 4,
                                                          0x080FE821, 0, 0) + bytes(4)
    assert bytes(rom[row:row + 44]) == blank, "item %d is not an unused slot" % item
    assert bytes(rom[icon:icon + 8]) == bytes(rom[icon + 8:icon + 16]), "item %d has a picture of its own" % item
    assert len(lz_dec(rom, u32(icon) - 0x08000000)) == 288, "item pictures are not 24x24"
    assert len(name) <= 13 and words_.count("\n") <= 2
    rom[row:row + 14] = text(name) + bytes(13 - len(name))
    struct.pack_into("<I", rom, row + 20, put(text(words_), 1))
    pic, pal = crest.item_icon(D.CREST_BOOSTER_ENERGY, name)
    struct.pack_into("<II", rom, icon, put(lz_comp(pic)), put(lz_comp(pal)))
    return "item %d is %s" % (item, name)


ENTER, LOOKUP, SPEED = 0x01D00110, 0x01D73A9C, 0x01D5E3F0
ENTER_CALLERS = 0x01D000F8                       # the two stubs that are ENTER's only callers
COMMANDS = 0x01D7717C                            # the engine's command table, 251 entries
COMMAND_0, COMMAND_5 = COMMANDS, COMMANDS + 4 * 5
ROUTINES, ROUTINE_CALL = 0x01D79EAC, 0x01D686CC  # its second table, 220 entries, and the command that calls one
FIXED_DAMAGE = ROUTINES + 4 * 24                 # the damage of Super Fang, Seismic Toss... by the move's number
STATE = 0x0203F130                               # 8 bytes of EWRAM measured free (the skill file has the map)


IN_EFFECT, HOLD_EFFECT, MOVE_TYPE = 0x01D45AEC, 0x01D68700, 0x01D4B164      # three of the engine's own helpers
WEATHER_UMBRELLA = 0x01D5FFF0                    # where the engine's weather modifier asks for the target's item
UMBRELLA = 0xA4                                  # the Utility Umbrella's hold effect


def install_effects(rom, put, slot_of, new_move, old_move):
    """gen9.s and its six hooks. Returns a line for the summary."""
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    at = lambda o, hexs: bytes(rom[o:o + len(hexs) // 2]) == bytes.fromhex(hexs)
    assert at(ENTER, "344909784900" + "3b4a88527047"), "the engine's store-the-ability helper changed"
    assert at(ENTER_CALLERS, "66f076fe00f008f83e49084766f070fe00f002f83c490847"), "its two callers changed"
    assert at(LOOKUP, "03225043024b41184900585a7047c0460000" + "7a09"), "the engine's ability lookup changed"
    # movs r3,#0x58; push {r4-r7,lr}; sub sp,#0x14; str r2,[sp] | movs r2,r3
    assert at(SPEED, "5823f0b585b00092" + "1a00"), "the engine's speed routine changed"
    # push {r4,lr}; ...; ldr r1,=0x09D79EA0; lsls r2,r3,#2; adds r3,r1,r2; ldr r3,[r3,#12]: entry n is at +12+4n
    assert at(ROUTINE_CALL, "10b5074801688b784a781b0203311343016004499a008b18db68") and \
        u32(ROUTINE_CALL + 0x24) == 0x08000000 + ROUTINES - 12, "the engine's call-a-routine command changed"
    # the helpers gen9.s calls, as the engine itself calls them: is the ability in effect (battler, 0), the hold
    # effect an item has now (battler, 1), the type the move in use has now ()
    assert at(IN_EFFECT, "37b5074c0d004100"), "the engine's ability-in-effect test changed"
    assert at(HOLD_EFFECT, "5822424370b5224b"), "the engine's hold-effect routine changed"
    assert at(MOVE_TYPE, "10b5124b1b68dc7c"), "the engine's move-type routine changed"
    assert at(WEATHER_UMBRELLA, "0121300008f084fb" + "%02x28" % UMBRELLA), "the engine's weather modifier changed"
    # the four Ruin abilities are (stat + 2) * 256 in the order Attack, Defense, Sp. Atk, Sp. Def
    assert [D.ABILITY_NEW[k][0] for k in ("tablets-of-ruin", "sword-of-ruin", "vessel-of-ruin", "beads-of-ruin")] == \
        [(stat + 2) << 8 for stat in range(4)], "gen9.s works the Ruin abilities out from the stat"
    old_cancel, old_damage, old_fixed = u32(COMMAND_0), u32(COMMAND_5), u32(FIXED_DAMAGE)
    assert old_fixed == 0x09D63DFD, "routine 24 of the battle engine is not its fixed-damage calculation"
    assert old_damage == 0x09D6046D, "command 5 of the battle engine is not its damage calculation"
    assert old_cancel == 0x09D5783D, "command 0 of the battle engine is not what it was"

    pairs = sorted((ident, base) for ident, _, base, _ in D.ABILITY_ALIAS.values())
    table = put(b"".join(struct.pack("<HH", a, b) for a, b in pairs) + bytes(4))
    with open(os.path.join(HERE, "gen9.s"), encoding="ascii") as f:
        src = f.read()
    fill = {"MAP_ADDR": "0x%08X" % table, "ORIG_DAMAGE": "0x%08X" % old_damage,
            "ORIG_CANCEL": "0x%08X" % old_cancel, "ORIG_FIXED": "0x%08X" % old_fixed,
            "RUINATION": str(new_move["ruination"]),
            "SPEED_RESUME": "0x%08X" % (0x08000000 + SPEED + 8 | 1), "STATE": "0x%08X" % STATE,
            "KORAIDON": str(slot_of["koraidon"]), "MIRAIDON": str(slot_of["miraidon"]),
            "DROUGHT": str(D.ABILITY_ALIAS["orichalcum-pulse"][2]),
            "ELECTRIC_SURGE": str(D.ABILITY_ALIAS["hadron-engine"][2]),
            "IN_EFFECT": "0x%08X" % (0x08000000 + IN_EFFECT | 1),
            "HOLD_EFFECT": "0x%08X" % (0x08000000 + HOLD_EFFECT | 1),
            "MOVE_TYPE": "0x%08X" % (0x08000000 + MOVE_TYPE | 1), "UMBRELLA": str(UMBRELLA),
            # moves whose stats are not their category's (the engine's own exceptions)
            "BODY_PRESS": str(old_move("Body Press")), "FOUL_PLAY": str(old_move("Foul Play")),
            "PSYSHOCK": str(old_move("Psyshock")), "PSYSTRIKE": str(old_move("Psystrike")),
            "SECRET_SWORD": str(old_move("Secret Sword")),
            "PROTO": str(D.ABILITY_NEW["protosynthesis"][0]), "QUARK": str(D.ABILITY_NEW["quark-drive"][0]),
            "COLLISION_COURSE": str(new_move["collision-course"]), "ELECTRO_DRIFT": str(new_move["electro-drift"]),
            "HYDRO_STEAM": str(new_move["hydro-steam"]), "PSYBLADE": str(new_move["psyblade"]),
            "GLAIVE_RUSH": str(new_move["glaive-rush"]), "BOOSTER": str(D.BOOSTER_ENERGY)}
    for k, v in sorted(fill.items(), key=lambda kv: -len(kv[0])):
        src = re.sub(r"\b%s\b" % k, v, src)
    n_pools = len(re.findall(r"^    PAD\d$", src, flags=re.M))

    def assemble(base, pads):
        """each literal pool must start on a 4-byte boundary: with the wrong padding the assembler reaches it
        with a wide (Thumb-2) load, which SM.thumb refuses, or a load misses its word"""
        s = src
        for k, pad in enumerate(pads):
            s = s.replace("    PAD%d\n" % (k + 1), "    mov r8, r8\n" if pad else "")
        try:
            code, dis = SM.thumb(s, base)
        except Exception:                                    # the assembler's own error, or SM.thumb's check
            return None, None
        literals = {int(x, 0) for x in re.findall(r"\.word\s+(\S+)", s)}
        for i in dis:                                        # every pc-relative load lands on one of the literals
            if i.mnemonic == "ldr" and "pc" in i.op_str:
                t = ((i.address + 4) & ~3) + (int(i.op_str.split("#")[1].rstrip("]"), 16) if "#" in i.op_str else 0) - base
                if t + 4 > len(code) or struct.unpack_from("<I", code, t)[0] not in literals:
                    return None, None
        return code, dis

    probe = 0x09A00000
    pads = next((p for p in itertools.product((False, True), repeat=n_pools) if assemble(probe, p)[0]), None)
    assert pads is not None, "gen9.s does not assemble with its literal pools on 4-byte boundaries"
    base = put(bytes(len(assemble(probe, pads)[0])))
    code, dis = assemble(base, pads)
    assert code
    rom[base - 0x08000000:base - 0x08000000 + len(code)] = code
    order = ("g9_enter", "g9_lookup", "g9_damage", "g9_cancel", "g9_fixed", "g9_speed")      # then the rest
    pushes = [i.address for i in dis if i.mnemonic == "push"]
    assert pushes[0] == base and len(pushes) == 15, "gen9.s: functions are not where they are counted to be"
    entry = dict(zip(order, pushes))

    for site, name in ((ENTER, "g9_enter"), (LOOKUP, "g9_lookup"), (SPEED, "g9_speed")):
        assert site % 4 == 0
        rom[site:site + 8] = bytes.fromhex("004b1847") + struct.pack("<I", entry[name] | 1)     # ldr r3,[pc]; bx r3
    for site, name in ((COMMAND_0, "g9_cancel"), (COMMAND_5, "g9_damage"), (FIXED_DAMAGE, "g9_fixed")):
        struct.pack_into("<I", rom, site, entry[name] | 1)
    return "; gen9.s %08X..%08X (%s), %d aliases" % (
        base, base + len(code), ", ".join("%s %08X" % (k[3:], entry[k]) for k in order), len(pairs))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    build(args[0], args[1], args[2], effects="--no-effects" not in sys.argv)
