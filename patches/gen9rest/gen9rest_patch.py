"""The rest of Gen 9 (Hyper Emerald v5.7): the 85 Pokemon gen9 did not add, Paldean Wooper and the three Paldean
Tauros, placed in the wild over Hoenn. A TEST build: it goes on top of the working ROM (after gen9 and paldea).
usage: python gen9rest_patch.py <in.gba> <out.gba> <Crest_v1.0.F.gba>

What it does, in order (each step asserts that what it changes is what it expects):
  1. The species tables, 1,280 -> 1,408 slots: the 23 tables speciesx moved are moved again, the same way (every
     word that points at one is a code literal, counted; the four field words into the base stats; the species
     count at its nine code sites). 89 slots are needed; 42 were free.
  2. The Pokemon (slots 1238-1326): as gen9 does it - the official Scarlet/Violet data (official.json, from
     PokeAPI), Crest's pictures, palettes, icons and cries. Pokedex numbers 941-1025 for the 85; the forms take
     Wooper's and Tauros's.
  3. 38 new moves (ids 948-985), each a copy of a move the game has that works the same way (gen9rest_data).
  4. 22 new abilities, each an alias of one the game has (gen9's convention and its alias list, made longer).
  5. Six evolution items (770-775) with Crest's pictures, sold by the Lilycove clerk who sells the others.
  6. Evolutions, including new ones for Primeape, Girafarig, Dunsparce, Bisharp, Applin and Duraludon, and the
     moves those ask for in their level-up lists.
  7. The wild slots of gen9rest_data.WILD.
  8. The Pokedex: numbers up to 1032 (the hack stops at 960) - dexext.s; the entries table, three order tables
     and the screen's list made longer; the number printed with four digits from 1000.
Free space: zero-filled ROM 0x09AC0000..0x09D00000 (the hack's own ROM has zeros there and no code points in).
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "speciesx"))
sys.path.insert(0, os.path.join(HERE, "..", "gen9"))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import speciesx_patch as SX
import gen9_patch as G9
import gen9_data as D9
import sinnohmap_patch as SM
import gen9rest_data as D

A = lambda o: 0x08000000 + o
NEW_N = 1408
GROW_AT = 0x01AC0000                             # the species tables, 1,408 entries each
SPACE, SPACE_END = 0x01B00000, 0x01D00000        # everything else
DEX_MAX = 1032                                   # the Pokedex's list: numbers 0..1032
DEX_ENTRIES_N = 1040
EXT_ADDR, MAGIC = 0x0203DA00, 0x39584544         # "DEX9": marker, then 32 bytes seen, 32 caught
EXT_END = EXT_ADDR + 68
STREAM_FREE = (0x0203D908, 0x0203DADC)           # the overflow stream's free margin (bagslots; its MARKER follows)

TYPES = dict(D9.TYPES)
CATEGORY = {"physical": 0, "special": 1, "status": 2}

# the Pokedex (NOTES, "The rest of Gen 9"): the hack's routines and its 960
DEX_FLAG = 0x01257950                            # GetSetPokedexFlag (the hack's)
DEX_FLAG_START = "70b51e4b0d000821"              # push {r4-r6,lr}; ldr r3,=__umodsi3; movs r5,r1; movs r1,#8
CLEAR_WORD, ORIG_CLEAR = 0x00084394, 0x092579D9  # ClearPokedexFlags' jump word -> the hack's clearing
DEX_ENTRIES_OLD = 0x01250000
DEX_ENTRY_WORDS = [0x0BFA20, 0x0BFADC, 0x0C02F8, 0x0C0328, 0x0C062C, 0x0C0650, 0x0C0660, 0x1DB48C]
# movs rX,#0xF0 ... lsls rX,rX,#2 (960): (movs, lsls)
DEX_960 = [(0x1257B96, 0x1257B9E), (0x1257C18, 0x1257C1A), (0x1257C96, 0x1257C98), (0x1257D3C, 0x1257D3E),
           (0x1257D96, 0x1257D98), (0x1257F40, 0x1257F46), (0x1257F5E, 0x1257F66), (0x1257F70, 0x1257F76),
           (0x1257F8C, 0x1257F8E), (0x1257FE0, 0x1257FE4), (0x1258168, 0x125816C)]
LIST_ALLOC, LIST_FILL = 0x1257914, 0x125791C     # pool words: the list's second buffer (0x8FC), the blank fill (961)
NATIONAL_COUNT = 0x0C080C                        # GetNationalPokedexCount: numbers 1..this+1 (0x3BF)
ORDER_WORDS = {0x1257FA0: (0x1258580, "height"), 0x1257FA4: (0x1259480, "name"), 0x1257FA8: (0x1258D00, "weight")}
VENEER, VENEER_END = 0x0C066C, 0x0C068C          # two jumps in the dead body of the game's old flag routine
DEAD_END = 0x0C07F0
CONVERT = 0x08008CC0                             # ConvertIntToDecimalStringN
# "No. 025": the Pokedex page (-> conv_dexnum) and the summary screen (-> conv_dexnum_sum)
CONVERT_SITES = {0x0C025E: ("conv_dexnum", 0x0C066C), 0x1C2662: ("conv_dexnum_sum", 0x0C067C)}
SUMMARY_NO_LITERAL = 0x1C26A0                    # the summary's "No" buffer, loaded at 0x081C264E
DIGITS_AT, DIGITS_END = 0x0BD194, 0x0BD1CC       # CreateMonDexNum's three digits
DIGITS_ORIG = ("01ac301c64212af2e5fca130a07001ad301c64212af21afd041c2404240c201c0a212af2d7fca130e870"
               "01ad201c0a212af20cfda1302871")

MART_SCRIPT, MART_LIST = 0x00F55BF9, 0x09865D20  # the Lilycove clerk's evolution items (pokemart's list)
# The hack's own guard on buying (test 1 reset the game on every purchase from that clerk): the buy step jumps
# through 0x080E0F00 to 0x096FFF00, which checks the item bought and EVERY item of the shop's list against a
# bitmap of the items a shop may sell - byte 0x09E0FE5F - (item >> 3), bit item & 7 (check at 0x096FFF64) -
# and jumps to 0 (a reset) when one is not in it. Its one literal is at 0x096FFF88; the reset at 0x096FFF60 is
# the only "movs r0,#0; bx r0" in the ROM. The new items get their bits.
SHOP_GUARD_HOOK, SHOP_GUARD = 0x000E0F00, 0x016FFF00
SHOP_BITS_WORD, SHOP_BITS_TOP = 0x016FFF88, 0x01E0FE5F
# Using an item from the Bag: PokemonUseItemEffects (0x0806BD28) knows only items 13-178 (gItemEffectTable,
# 0x0831E58C, 166 entries) and says "won't have any effect" past it (test 1: none of the new items evolved
# anything). evoitems.s takes the place of the lookup at 0x0806BE70 (8 bytes; 16 replaced, the rest skipped).
USE_FUNC, USE_FUNC_END = 0x0006BD28, 0x0006CD6C
USE_HOOK, USE_HOOK_ORIG = 0x0006BE70, "2004000ca5283bd80549a00040180068"
EFFECT_TABLE = 0x0031E58C


def thumb(src, base):
    """assemble with the literal pool on a 4-byte boundary (PAD1 is a mov r8,r8 or nothing)"""
    for pad in (False, True):
        s = src.replace("    PAD1\n", "    mov r8, r8\n" if pad else "")
        try:
            code, dis = SM.thumb(s, base)
        except Exception:
            continue
        ok = True
        lits = {int(x, 0) for x in re.findall(r"\.word\s+(\S+)", s)}
        for i in dis:
            if i.mnemonic == "ldr" and "pc" in i.op_str:
                t = ((i.address + 4) & ~3) + (int(i.op_str.split("#")[1].rstrip("]"), 16) if "#" in i.op_str else 0) - base
                if t + 4 > len(code) or struct.unpack_from("<I", code, t)[0] not in lits:
                    ok = False
        if ok:
            return code, dis
    raise AssertionError("does not assemble with its pool aligned")


def bl(frm, to):
    off = (to - (frm + 4)) >> 1
    assert -(1 << 21) <= off < (1 << 21), "bl out of reach"
    return struct.pack("<HH", 0xF000 | (off >> 11) & 0x7FF, 0xF800 | off & 0x7FF)


def bl_target(rom, o):
    hi, lo = struct.unpack_from("<HH", rom, o)
    if hi & 0xF800 != 0xF000 or lo & 0xF800 != 0xF800:
        return None
    off = ((hi & 0x7FF) << 11) | (lo & 0x7FF)
    if off & 0x200000:
        off -= 0x400000
    return A(o) + 4 + 2 * off


def z_power(power, cat):
    if cat == 2:
        return 0
    for limit, z in ((55, 100), (65, 120), (75, 140), (85, 160), (95, 175), (100, 180), (110, 185), (125, 190),
                     (130, 195)):
        if power <= limit:
            return z
    return 200


def max_power(power, cat, type_):
    if cat == 2:
        return 0
    weak = type_ in ("fighting", "poison")
    for limit, a, b in ((40, 90, 70), (50, 100, 75), (60, 110, 80), (70, 120, 85), (100, 130, 90), (140, 140, 95)):
        if power <= limit:
            return b if weak else a
    return 100 if weak else 150


def build(inp, outp, crest_path):
    with open(inp, "rb") as f:
        rom = bytearray(f.read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    crest = G9.Crest(crest_path)
    official = json.load(open(os.path.join(HERE, "official.json"), encoding="utf-8"))
    mvdata = json.load(open(os.path.join(HERE, "moves.json"), encoding="utf-8"))
    u8 = lambda o: rom[o]
    u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    at = lambda o, hexs: bytes(rom[o:o + len(hexs) // 2]) == bytes.fromhex(hexs)
    words = list(struct.unpack_from("<%dI" % (len(rom) // 4), rom))

    # ---- the ROM: gen9 is in (its alias list, its moves), this patch is not
    old = SX.layout()
    assert u32(0x1BC) == A(old["base stats"]), "the species tables are not where speciesx put them (applied already?)"
    assert u32(0x1C0) != A(G9.ABILITY_NAMES), "gen9 is not applied"
    assert not any(rom[GROW_AT:SPACE_END]), "the target region is not empty"
    for i, v in enumerate(words):
        if A(GROW_AT) <= v < A(SPACE_END):
            assert not SX.is_pointer(rom, 4 * i), "%08X points into the target region" % A(4 * i)

    pos = [SPACE]

    def put(data, align=4):
        o = (pos[0] + align - 1) & ~(align - 1)
        assert o + len(data) <= SPACE_END, "out of space"
        rom[o:o + len(data)] = data
        pos[0] = o + len(data)
        return A(o)

    report = []

    # ================================================================ 1. the species tables, longer
    targets = {A(old[t[0]]): t for t in SX.TABLES}
    refs = {v: [] for v in targets}
    for i, v in enumerate(words):
        if v in refs:
            refs[v].append(4 * i)
    lay, p = {}, GROW_AT
    for name, _, size, expect, minus_one, zero in SX.TABLES:
        base = old[name]
        hold = refs[A(base)]
        assert len(hold) == expect and all(SX.is_pointer(rom, k) for k in hold), "%s: %d words" % (name, len(hold))
        blank = bytes(size) if zero else bytes(rom[base:base + size])
        if name == "names":
            blank = b"\xff" + bytes(10)
        data = bytes(rom[base:base + size * SX.NEW_N]) + blank * (NEW_N - SX.NEW_N)
        rom[p:p + len(data)] = data
        for k in hold:
            struct.pack_into("<I", rom, k, A(p))
        if name == "base stats":
            for k, field in SX.FIELD_WORDS:
                assert u32(k) == A(base + field), "base stats field word %08X" % A(k)
                struct.pack_into("<I", rom, k, A(p + field))
        lay[name] = p
        p = (p + len(data) + 3) & ~3
    assert p <= SPACE
    for o, was, how in SX.COUNT_SITES:
        if how == "imm8<<3":
            assert rom[o] == SX.NEW_N >> 3, "count site %08X" % A(o)
            rom[o] = NEW_N >> 3
        else:
            want = SX.NEW_N - (1 if how == "count-1" else 0)
            assert u32(o) == want, "count site %08X" % A(o)
            struct.pack_into("<I", rom, o, NEW_N - (1 if how == "count-1" else 0))
    assert NEW_N % 8 == 0 and NEW_N >> 3 < 256 and NEW_N - 277 <= 1200
    assert not any(rom[G9.ABILITY_TABLE + 6 * 1238:G9.ABILITY_TABLE + 6 * NEW_N]), "the ability table is not free past 1237"
    report.append("species tables: %d x 23 at %08X..%08X" % (NEW_N, A(GROW_AT), A(p)))
    size_of = {t[0]: t[2] for t in SX.TABLES}

    def row(table, slot, data):
        assert len(data) == size_of[table], table
        rom[lay[table] + len(data) * slot:lay[table] + len(data) * (slot + 1)] = data

    # ---- the game's names: species, moves, abilities, items
    CH = {v: k for k, v in G9.CHARS.items() if len(k) == 1}

    def decode(o, n):
        s = ""
        for b in rom[o:o + n]:
            if b == 0xFF:
                break
            s += CH.get(b, "?")
        return s

    names_at = lay["names"]
    natdex_at = lay["national dex no."]
    species_name = lambda s: decode(names_at + 11 * s, 11)
    natdex = lambda s: u16(natdex_at + 2 * (s - 1))

    def species_slot(name, nat):
        hits = [s for s in range(1, SX.NEW_N) if species_name(s) == name and natdex(s) == nat]
        assert hits, "no %s (%d)" % (name, nat)
        return hits[0]

    MOVE_NAMES = u32(0x148) - 0x08000000
    MOVE_DATA = u32(0x1CC) - 0x08000000
    assert MOVE_DATA == G9.MOVE_DATA
    move_by = {}
    for m in range(1, D.FIRST_MOVE):
        nm = decode(MOVE_NAMES + 13 * m, 13)
        if nm.strip("-").strip():
            move_by.setdefault(G9.norm(nm), m)
    assert not any(rom[MOVE_DATA + 12 * D.FIRST_MOVE:MOVE_DATA + 12 * 1024]), "move ids from 948 are not blank"
    assert decode(MOVE_NAMES + 13 * 947, 13) == "Glaive Rush", "gen9's last move is not 947"
    ABIL_NAMES, ABIL_TEXT = u32(0x1C0) - 0x08000000, u32(0x1C4) - 0x08000000
    abil_by = {}
    for a in range(1, D9.ABILITY_COUNT):
        nm = decode(ABIL_NAMES + 13 * a, 13)
        if nm.strip("-").strip():
            abil_by.setdefault(G9.norm(nm), a)
    ITEMS = u32(0x1C8) - 0x08000000
    item_by = {}
    for i in range(1, 800):
        item_by.setdefault(decode(ITEMS + 44 * i, 14), i)

    def old_move(name):
        m = move_by.get(G9.norm(name))
        assert m, "no move %s" % name
        return m

    # ================================================================ 3. new moves
    new_move, move_rows = {}, []
    texts_tab = None
    # gen9's longer description table: find it by its first 64 bytes, the old table's
    old_head = bytes(rom[G9.MOVE_TEXT:G9.MOVE_TEXT + 64])
    hits = [k for k in range(0x01A10000, 0x01AB8110, 4) if rom[k:k + 64] == old_head]
    assert len(hits) == 1, "gen9's move description table: %s" % hits
    texts_tab = hits[0]
    def find_once(needle):
        k = bytes(rom).find(needle, 0x01A10000, 0x01AB8110)
        assert k > 0 and bytes(rom).find(needle, k + 1, 0x01AB8110) < 0, "gen9's copy of a power table"
        return k
    ZP = find_once(bytes(rom[G9.Z_POWER:G9.Z_POWER + 938]))
    MP = find_once(bytes(rom[G9.MAX_POWER:G9.MAX_POWER + 938]))
    for i, (key, name, template, changes, anim, words_) in enumerate(D.NEW_MOVES):
        m = D.FIRST_MOVE + i
        off_key = key if key in mvdata else key.rsplit("-", 1)[0]
        o = mvdata[off_key]
        t = old_move(template)
        r = bytearray(rom[MOVE_DATA + 12 * t:MOVE_DATA + 12 * t + 12])
        type_ = changes.get("type", o["type"])
        cat = CATEGORY[o["category"]]
        power = changes.get("power", o["power"] or 0)
        r[1], r[2], r[4], r[10] = power, TYPES[type_], o["pp"], cat
        r[3] = 0 if o["accuracy"] is None else o["accuracy"]
        for field, idx in (("chance", 5), ("target", 6), ("priority", 7), ("flags", 8), ("stat", 9)):
            if field in changes:
                r[idx] = changes[field]
        assert len(name) <= 12 and max(map(len, words_.split("\n"))) <= 30 and words_.count("\n") <= 1, key
        rom[MOVE_DATA + 12 * m:MOVE_DATA + 12 * m + 12] = r
        rom[MOVE_NAMES + 13 * m:MOVE_NAMES + 13 * m + 13] = G9.text(name) + bytes(12 - len(name))
        struct.pack_into("<I", rom, texts_tab + 4 * (m - 1), put(G9.text(words_.rstrip("\n")), 1))
        script = u32(G9.MOVE_ANIMS + 4 * old_move(anim))
        assert script != G9.DEFAULT_ANIM and u32(G9.MOVE_ANIMS + 4 * m) == G9.DEFAULT_ANIM
        struct.pack_into("<I", rom, G9.MOVE_ANIMS + 4 * m, script)
        rom[ZP + m], rom[MP + m] = z_power(power, cat), max_power(power, cat, type_)
        new_move[key] = m
        move_rows.append("  %d %-12s like %-12s %s" % (m, name, template, bytes(r).hex()))
    assert D.FIRST_MOVE + len(D.NEW_MOVES) <= 1024

    def move(official_name, species=None):
        official_name = D.MOVE_BY_SPECIES.get((official_name, species), official_name)
        official_name = D9.MOVE_BY_SPECIES.get((official_name, species), official_name)
        if official_name in new_move:
            return new_move[official_name]
        if official_name in D.MOVES_LEFT_OUT or official_name in D9.MOVES_NOT_IN_GAME and \
                official_name not in new_move:
            return None
        if official_name in {k for k, *_ in D9.NEW_MOVES}:
            return D9.FIRST_MOVE + [k for k, *_ in D9.NEW_MOVES].index(official_name)
        m = move_by.get(G9.norm(D9.MOVE_NAMES.get(official_name, official_name)))
        assert m, "%s: not in the game and not listed" % official_name
        return m

    # ================================================================ 4. abilities
    alias_pairs = []
    ability_id = {}
    for key, (name, base_name) in D.ABILITY_ALIAS.items():
        base = abil_by.get(G9.norm(base_name))
        assert base, "no ability %s" % base_name
        blank = bytes(rom[ABIL_NAMES + 13 * 1000:ABIL_NAMES + 13 * 1001])
        ident = next(256 * k + base for k in range(1, 7)
                     if 256 * k + base < D9.ABILITY_COUNT and
                     bytes(rom[ABIL_NAMES + 13 * (256 * k + base):ABIL_NAMES + 13 * (256 * k + base) + 13]) == blank)
        assert len(name) <= 12
        rom[ABIL_NAMES + 13 * ident:ABIL_NAMES + 13 * ident + 13] = G9.text(name) + bytes(12 - len(name))
        struct.pack_into("<I", rom, ABIL_TEXT + 4 * ident, u32(ABIL_TEXT + 4 * base))   # what it does here
        ability_id[key] = ident
        alias_pairs.append((ident, base))
    # gen9's alias list: find it, make a longer copy, repoint gen9.s's one word
    old_pairs = sorted((i, b) for i, _, b, _ in D9.ABILITY_ALIAS.values())
    blob = b"".join(struct.pack("<HH", a, b) for a, b in old_pairs) + bytes(4)
    hits = [k for k in range(0x01A10000, 0x01AB8110, 4) if rom[k:k + len(blob)] == blob]
    assert len(hits) == 1, "gen9's alias list"
    holders = [4 * i for i, v in enumerate(words) if v == A(hits[0])]
    assert len(holders) == 1, "gen9.s's alias word"
    new_map = put(b"".join(struct.pack("<HH", a, b) for a, b in old_pairs + sorted(alias_pairs)) + bytes(4))
    struct.pack_into("<I", rom, holders[0], new_map)

    def ability(name):
        if name in ability_id:
            return ability_id[name]
        if name in D9.ABILITY_EXISTING:
            return D9.ABILITY_EXISTING[name]
        if name in D9.ABILITY_ALIAS:
            return D9.ABILITY_ALIAS[name][0]
        a = abil_by.get(G9.norm(D.ABILITY_NAMES.get(name, name)))
        assert a, "ability %s" % name
        return a

    # ================================================================ 5. items
    tmpl = {"stone": item_by["Thunder Stone"], "held": item_by["Razor Claw"]}
    item_id = {}
    crest_items = {}
    for k in range(1, 900):
        nm = G9.norm("".join(CH.get(b, "") for b in crest.d[G9.CREST_ITEMS + 40 * k:G9.CREST_ITEMS + 40 * k + 14].split(b"\xff")[0]))
        crest_items.setdefault(nm, k)
    for key, (ident, name, crest_name, kind, price, words_) in D.ITEMS.items():
        rowo = ITEMS + 44 * ident
        assert decode(rowo, 14) == "New Item", "item %d is not an unused slot" % ident
        src = ITEMS + 44 * tmpl[kind]
        rom[rowo:rowo + 44] = rom[src:src + 44]
        assert len(name) <= 13 and words_.count("\n") <= 2 and max(map(len, words_.split("\n"))) <= 18
        rom[rowo:rowo + 14] = G9.text(name) + bytes(13 - len(name))
        struct.pack_into("<HHBB", rom, rowo + 14, ident, price, 0, 0)      # no hold effect (Razor Claw's is not it)
        struct.pack_into("<I", rom, rowo + 20, put(G9.text(words_), 1))
        icon = G9.ITEM_ICONS + 8 * ident
        if crest_name.startswith("game:"):
            mine = G9.ITEM_ICONS + 8 * item_by[crest_name[5:]]
            rom[icon:icon + 8] = rom[mine:mine + 8]                     # this game's own picture
        else:
            ck = crest_items.get(G9.norm(crest_name))
            assert ck, "Crest has no %s" % crest_name
            pic = G9.lz_dec(crest.d, crest.ptr(G9.CREST_ITEM_ICONS + 8 * ck))
            pal = G9.lz_dec(crest.d, crest.ptr(G9.CREST_ITEM_ICONS + 8 * ck + 4))
            pal += bytes(32 - len(pal))                                 # some hold fewer than 16 colours
            assert len(pic) == 288 and len(pal) == 32
            struct.pack_into("<II", rom, icon, put(G9.lz_comp(pic)), put(G9.lz_comp(pal)))
        item_id[key] = ident
    # the shop: a longer copy of the Lilycove clerk's list
    assert u32(MART_SCRIPT) == MART_LIST and rom[MART_SCRIPT - 1] == 0x86
    lst = MART_LIST - 0x08000000
    items_now = []
    while u16(lst + 2 * len(items_now)):
        items_now.append(u16(lst + 2 * len(items_now)))
    assert item_by["Razor Claw"] in items_now and len(items_now) == 19
    other = [k for k in range(len(rom) - 4) if rom[k] == 0x86 and u32(k + 1) == MART_LIST]
    assert other == [MART_SCRIPT - 1], "the list has other shops: %s" % other
    new_list = put(struct.pack("<%dH" % (len(items_now) + len(item_id) + 1), *(items_now + sorted(item_id.values()) + [0])))
    struct.pack_into("<I", rom, MART_SCRIPT, new_list)
    # the hack's guard on buying: the new items may be sold
    assert u32(SHOP_GUARD_HOOK) == A(SHOP_GUARD) | 1 and u32(SHOP_BITS_WORD) == A(SHOP_BITS_TOP), "the shop guard moved"
    assert at(SHOP_GUARD + 0x60, "0020004707220240c008") and at(SHOP_GUARD_HOOK - 4, "00480047"), \
        "the shop guard's check changed"
    sellable = lambda i: (rom[SHOP_BITS_TOP - (i >> 3)] >> (i & 7)) & 1
    assert all(sellable(i) for i in items_now), "the clerk's own items are not all allowed: wrong bitmap"
    assert not sellable(item_by["Master Ball"]) and not sellable(item_by["Rare Candy"]), "wrong bitmap"
    for i in item_id.values():
        assert not sellable(i), "item %d is allowed already" % i
        rom[SHOP_BITS_TOP - (i >> 3)] |= 1 << (i & 7)
    assert all(sellable(i) for i in items_now + list(item_id.values()))
    # used from the Bag: evoitems.s in place of PokemonUseItemEffects' effect lookup
    use_items = sorted(item_id[k] for k, v in D.ITEMS.items() if v[3] == "stone")
    assert use_items == list(range(use_items[0], use_items[-1] + 1)) and use_items[0] > 178, use_items
    thunder = item_by["Thunder Stone"]
    stone = u32(EFFECT_TABLE + 4 * (thunder - 13))
    assert at(USE_HOOK, USE_HOOK_ORIG) and USE_HOOK % 4 == 0 and u32(USE_HOOK + 0x20) == A(EFFECT_TABLE), \
        "PokemonUseItemEffects' lookup changed"
    assert rom[stone - 0x08000000:stone - 0x08000000 + 6] == bytes([0, 0, 0, 0, 0x80, 0]), "the Thunder Stone's effect"
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    for ins in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(bytes(rom[USE_FUNC:USE_FUNC_END]), A(USE_FUNC)):
        if ins.mnemonic.startswith("b") and ins.op_str.startswith("#"):
            assert not A(USE_HOOK) < int(ins.op_str[1:], 16) < A(USE_HOOK + 0x10), "a branch into the replaced lookup"
    src = open(os.path.join(HERE, "evoitems.s"), encoding="ascii").read()
    for k, v in {"FIRST": use_items[0], "LAST": use_items[-1], "STONE": "0x%08X" % stone}.items():
        src = re.sub(r"\b%s\b" % k, str(v), src)
    ie_base = put(bytes(len(thumb(src, 0x09B00000)[0])))
    ie_code, _ = thumb(src, ie_base)
    rom[ie_base - 0x08000000:ie_base - 0x08000000 + len(ie_code)] = ie_code
    rom[USE_HOOK:USE_HOOK + 8] = bytes.fromhex("00490847") + struct.pack("<I", ie_base | 1)     # ldr r1,[pc]; bx r1

    def item(name):
        return item_id[name] if name in item_id else item_by[name]

    # ================================================================ 2. the Pokemon
    first = D.FIRST_SLOT
    slot_of = {key: first + i for i, (key, *_r) in enumerate(D.SPECIES)}
    assert first + len(D.SPECIES) <= NEW_N
    for name in ("base stats", "names", "evolutions"):
        o = lay[name] + size_of[name] * first
        assert set(rom[o:o + size_of[name] * len(D.SPECIES)]) <= ({0, 0xFF} if name == "names" else {0}), name
    used_cries = set(range(251)) | {u16(G9.CRY_IDS + 2 * (s - 277)) for s in range(277, D.FIRST_SLOT)} | \
        {u16(G9.GMAX_CRY_IDS + 2 * k) for k in range(25)}
    free_cries = [i for i in range(388, 1200) if i not in used_cries]
    assert len(free_cries) >= len(D.SPECIES)
    icon_palettes = [struct.unpack_from("<16H", rom, u32(G9.ICON_PALETTES + 8 * k) - 0x08000000) for k in range(3)]
    # the evolution levels, for moves at level 0 (learnt on evolving here: at the level it evolves at)
    evolves_at = {}
    for src, method, what, dst in D.EVOLUTIONS:
        if method in (4, 18, 19):
            evolves_at[dst] = what
    dex = D.FIRST_DEX - 1
    dex_of, left_out = {}, set()
    species_rows = []
    for i, (key, api, name, crest_id, form_of) in enumerate(D.SPECIES):
        slot, o, notes = first + i, official[key], []
        assert len(name) <= 10
        st = o["stats"]
        types = [TYPES[t] for t in o["types"]]
        b = bytearray(28)
        b[0:6] = bytes([st["hp"], st["atk"], st["def"], st["spe"], st["spa"], st["spd"]])
        b[6], b[7], b[8], b[9] = types[0], types[-1], o["catch"], min(255, o["exp"])
        ev = o["ev"]
        struct.pack_into("<H", b, 10, sum(ev.get(k, 0) << 2 * n for n, k in enumerate(("hp", "atk", "def", "spe", "spa", "spd"))))
        b[16] = 255 if o["gender_rate"] < 0 else min(254, max(0, o["gender_rate"] * 32 - 1))
        b[17], b[18], b[19] = o["hatch"], o["friendship"], D9.GROWTH[D.GROWTH_FIX.get(key, o["growth"])]
        groups = [D9.EGG_GROUPS[g] for g in o["egg_groups"]]
        b[20], b[21] = groups[0], groups[-1]
        b[25] = D9.COLORS[o["color"]] | (crest.d[crest.info + G9.CREST_INFO * crest_id + 31] & 0x80)
        row("base stats", slot, bytes(b))
        row("names", slot, G9.text(name) + bytes(10 - len(name)))
        front, back = crest.picture(crest.front, crest_id), crest.picture(crest.back, crest_id)
        row("front pictures", slot, struct.pack("<IHH", put(G9.lz_comp(front)), 0x800, 1))
        row("back pictures", slot, struct.pack("<IHH", put(G9.lz_comp(back)), 0x800, 1))
        row("palettes", slot, struct.pack("<IHH", put(G9.lz_comp(crest.palette(crest.pal, crest_id))), 1, 0))
        row("shiny palettes", slot, struct.pack("<IHH", put(G9.lz_comp(crest.palette(crest.shiny, crest_id))), 501, 0))
        row("front coordinates", slot, G9.coordinates(front))
        row("back coordinates", slot, G9.coordinates(back))
        row("elevation", slot, bytes([crest.d[G9.CREST_ELEVATION + crest_id]]))
        icon, pal = crest.icon_of(crest_id)
        if pal > 2:
            icon, pal = G9.fit_icon(icon, crest.icon_palette(pal), icon_palettes)
            notes.append("icon redrawn")
        row("icons", slot, struct.pack("<I", put(icon)))
        row("icon palette ids", slot, bytes([pal]))
        cry = free_cries[i]
        wave = put(crest.cry(crest_id))
        for table, kind in ((G9.CRY, 0x20), (G9.CRY_REVERSE, 0x30)):
            rom[table + 12 * cry:table + 12 * cry + 12] = bytes([kind, 0x3C, 0, 0]) + struct.pack("<I", wave) + bytes([0xFF, 0, 0xFF, 0])
        struct.pack_into("<H", rom, G9.CRY_IDS + 2 * (slot - 277), cry)
        if form_of:
            n = natdex(species_slot(form_of, {"Wooper": 194, "Tauros": 128}[form_of]))
        else:
            dex += 1
            n = dex
        dex_of[key] = n
        struct.pack_into("<H", rom, natdex_at + 2 * (slot - 1), n)
        regular = [ability(a) for a, hidden in o["abilities"] if not hidden]
        hidden = [ability(a) for a, hidden in o["abilities"] if hidden]
        struct.pack_into("<HHH", rom, G9.ABILITY_TABLE + 6 * slot, regular[0], regular[-1], (hidden or regular)[0])
        lv_moves = [(lv or evolves_at.get(key, 1), mv) for lv, mv in o["levelup"]] + D.EXTRA_LEVELUP.get(key, [])
        lv_moves.sort(key=lambda x: x[0])
        levelup = bytearray()
        for level, mv in lv_moves:
            m = move(mv, key)
            if m is None:
                left_out.add(mv)
            else:
                levelup += struct.pack("<HB", m, level)
        struct.pack_into("<I", rom, lay["level-up pointers"] + 4 * slot, put(bytes(levelup) + b"\x00\x00\xff", 1))
        can = {move(mv, key) for mv in [m for _, m in o["levelup"]] + o["machine"] + o["tutor"] + o["egg"]} - {None}
        tm = sum(1 << k for k, m in enumerate([u16(G9.TM_LIST + 2 * j) for j in range(G9.TM_COUNT)]) if m in can)
        tutor = sum(1 << k for k, m in enumerate([u16(G9.TUTOR_LIST + 2 * j) for j in range(G9.TUTOR_COUNT)]) if m in can)
        row("TM/HM bits", slot, tm.to_bytes(16, "little"))
        row("tutor bits", slot, tutor.to_bytes(16, "little"))
        species_rows.append("  %4d %-10s dex %4d cry %4d level-up %2d TM %2d tutor %2d %s" % (
            slot, name, n, cry, len(levelup) // 3, bin(tm).count("1"), bin(tutor).count("1"), " ".join(notes)))
    assert dex == 1025, "the last number is %d" % dex

    # ================================================================ 6. evolutions
    def species_by_key(key):
        if key in slot_of:
            return slot_of[key]
        nat = official[key]["dex"]
        return species_slot(key.capitalize(), nat)

    evo_rows = []
    for src, method, what, dst in D.EVOLUTIONS:
        s, t = species_by_key(src), species_by_key(dst)
        if method in (4, 18, 19):
            param = what
        elif method in (7, 20, 21):
            param = item(what)
        elif method == 16:
            param = new_move[what]
        base = lay["evolutions"] + 40 * s
        free = next(k for k in range(5) if u16(base + 8 * k) == 0)
        struct.pack_into("<HHHH", rom, base + 8 * free, method, param, t, 0)
        evo_rows.append("%s(%d) -%d/%d-> %s(%d)" % (src, s, method, param, dst, t))
        # the game works the level out again from the experience on evolving: a line must share its group
        assert rom[lay["base stats"] + 28 * s + 19] == rom[lay["base stats"] + 28 * t + 19], \
            "%s and %s are in different experience groups" % (src, dst)
    # the moves those ask for, taught where Scarlet/Violet teaches them
    for key, level, mv in D.TEACH_OLD:
        s = species_by_key(key)
        lp = lay["level-up pointers"] + 4 * s
        src = u32(lp) - 0x08000000
        entries = []
        k = src
        while not (u16(k) == 0 and u8(k + 2) == 0xFF):
            entries.append((u16(k), u8(k + 2)))
            k += 3
            assert len(entries) < 80 and 0 < entries[-1][0] < 1024 and entries[-1][1] <= 100, "%s's moves" % key
        assert all(m != new_move[mv] for m, _ in entries)
        entries.append((new_move[mv], level))
        entries.sort(key=lambda e: e[1])
        struct.pack_into("<I", rom, lp, put(b"".join(struct.pack("<HB", m, lv) for m, lv in entries) + b"\x00\x00\xff", 1))

    # ================================================================ 7. the wild
    WILD = 0x00E17D50
    nhead = 0
    while not (rom[WILD + 20 * nhead] == 0xFF and rom[WILD + 20 * nhead + 1] == 0xFF):
        nhead += 1
    KIND_AT = {"land": 4, "water": 8, "rock": 12, "fish": 16}
    NSLOTS = {"land": 12, "water": 5, "rock": 5, "fish": 10}
    RATES = {"land": [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1], "water": [60, 30, 5, 4, 1], "rock": [60, 30, 5, 4, 1],
             "fish": [70, 30, 60, 20, 20, 40, 40, 15, 4, 1]}
    ROD = {k: ["Old"] * 2 + ["Good"] * 3 + ["Super"] * 5 for k in ("fish",)}
    arrays, where = {}, {}
    for h in range(nhead):
        for kind, ko in KIND_AT.items():
            info = u32(WILD + 20 * h + ko)
            if info:
                arr = u32(info - 0x08000000 + 4) - 0x08000000
                arrays.setdefault(arr, []).append((h, kind))
                for j in range(NSLOTS[kind]):
                    where.setdefault(u16(arr + 4 * j + 2), set()).add((h, kind))
    wild_rows = []
    taken = set()
    for key, h, kind, want, was in D.WILD:
        info = u32(WILD + 20 * h + KIND_AT[kind]) - 0x08000000
        arr = u32(info + 4) - 0x08000000
        assert arrays[arr] == [(h, kind)], "table %d %s shares its slots: %s" % (h, kind, arrays[arr])
        rod = lambda j: ROD.get(kind, [""] * 12)[j]
        best = None
        for j in range(NSLOTS[kind]):
            if (arr, j) in taken:
                continue
            sp = u16(arr + 4 * j + 2)
            if species_name(sp) != was:
                continue
            twins = [x for x in range(NSLOTS[kind]) if x != j and u16(arr + 4 * x + 2) == sp and rod(x) == rod(j)
                     and (arr, x) not in taken]
            others = len(where[sp] - {(h, kind)})
            ok = twins or others >= 3
            if ok:
                score = (abs(RATES[kind][j] - want) + (0 if twins else 3), -others)
                if best is None or score < best[0]:
                    best = (score, j, sp, twins, others)
        assert best, "%s: no safe slot of %s in table %d %s" % (key, was, h, kind)
        _, j, sp, twins, others = best
        taken.add((arr, j))
        lo, hi = rom[arr + 4 * j], rom[arr + 4 * j + 1]
        struct.pack_into("<H", rom, arr + 4 * j + 2, slot_of[key])
        if not twins:
            where[sp].discard((h, kind))
        wild_rows.append("  %-28s table %3d %-5s slot %2d (%2d%%) Lv %d-%d, was %s%s" % (
            key, h, kind, j, RATES[kind][j], lo, hi, was, " (a second slot)" if twins else " (in %d other places)" % others))

    # ================================================================ 8. the Pokedex
    # 8a. the entries, a longer table
    e_old = DEX_ENTRIES_OLD
    assert [k for k, v in enumerate(words) if v == A(e_old) and SX.is_pointer(rom, 4 * k)] == [w // 4 for w in DEX_ENTRY_WORDS]
    placeholder = bytes(rom[e_old + 32 * 959:e_old + 32 * 960])
    assert placeholder[:5] == G9.text("Seed")
    table = bytearray(rom[e_old:e_old + 32 * 960]) + placeholder * (DEX_ENTRIES_N - 960)
    for i, (key, api, name, crest_id, form_of) in enumerate(D.SPECIES):
        if form_of:
            continue
        o, n = official[key], dex_of[key]
        e = 32 * n
        assert bytes(table[e:e + 32]) == placeholder or n < 960 and table[e:e + 5] == G9.text("Seed"), n
        category = D.GENUS.get(key, o["genus"].replace(" Pokémon", ""))
        assert len(category) <= 11, category
        texts = [D.DEX_TEXT[key]] if key in D.DEX_TEXT else [o["flavor"][v] for v in ("scarlet", "violet") if v in o["flavor"]]
        words_ = next((w for w in (G9.wrap(t_, G9.DEX_WIDTH, G9.DEX_LINES) for t_ in texts) if w), None)
        assert words_, "%s: no Pokedex text fits" % key
        table[e:e + 12] = G9.text(category) + bytes(11 - len(category))
        struct.pack_into("<HHI", table, e + 12, o["height"], o["weight"], put(G9.text(words_), 1))
    new_entries = put(bytes(table))
    for w in DEX_ENTRY_WORDS:
        struct.pack_into("<I", rom, w, new_entries)
    E = new_entries - 0x08000000

    # 8b. the order tables: every number 1..1025 once, old ones in their order, the new ones put in by the key
    def first_species_named(n):
        for s in range(1, NEW_N):
            if natdex(s) == n:
                return species_name(s)
        return ""
    key_of = {"height": lambda n: u16(E + 32 * n + 12), "weight": lambda n: u16(E + 32 * n + 14),
              "name": lambda n: first_species_named(n).upper()}
    for word, (tab, what) in ORDER_WORDS.items():
        assert u32(word) == A(tab)
        vals = struct.unpack_from("<960H", rom, tab)
        order = []
        for v in vals:
            if 1 <= v <= 905 and v not in order:
                order.append(v)
        missing = [n for n in range(1, 906) if n not in order] + list(range(906, 1026))
        k_ = key_of[what]
        for n in missing:
            kn = k_(n)
            at_ = next((x for x, v in enumerate(order) if k_(v) > kn), len(order))
            order.insert(at_, n)
        assert sorted(order) == list(range(1, 1026))
        order += [0] * (DEX_MAX - len(order))
        struct.pack_into("<I", rom, word, put(struct.pack("<%dH" % DEX_MAX, *order)))

    # 8c. the 960s
    for mo, lo_ in DEX_960:
        assert rom[mo] == 0xF0 and rom[mo + 1] & 0xF8 == 0x20, "%08X is not movs #0xF0" % A(mo)
        rd = rom[mo + 1] & 7
        ls = u16(lo_)
        assert ls == (2 << 6) | (rd << 3) | rd, "%08X is not lsls r%d,r%d,#2" % (A(lo_), rd, rd)
        rom[mo] = DEX_MAX >> 3
        struct.pack_into("<H", rom, lo_, (3 << 6) | (rd << 3) | rd)
    assert DEX_MAX % 8 == 0 and DEX_MAX >> 3 < 256
    assert u32(LIST_ALLOC) == 0x8FC and u32(LIST_FILL) == 0x3C1 and u32(LIST_FILL - 4) == 0x182
    struct.pack_into("<I", rom, LIST_ALLOC, (DEX_MAX + 1 - 386) * 4 + 4)
    struct.pack_into("<I", rom, LIST_FILL, DEX_MAX + 1)
    assert u32(NATIONAL_COUNT) == 0x3BF
    struct.pack_into("<I", rom, NATIONAL_COUNT, 1024)

    # 8d. dexext.s: the flags, the New Game clearing, the four-digit numbers
    for i, v in enumerate(words):
        if STREAM_FREE[0] <= v < STREAM_FREE[1]:
            assert not SX.is_pointer(rom, 4 * i), "%08X points into the stream's free margin" % A(4 * i)
    assert at(DEX_FLAG, DEX_FLAG_START), "the hack's flag routine changed"
    assert u32(CLEAR_WORD) == ORIG_CLEAR and at(CLEAR_WORD - 4, "00480047"), "ClearPokedexFlags' jump changed"
    assert at(DIGITS_AT, DIGITS_ORIG), "CreateMonDexNum's digits changed"
    for site in CONVERT_SITES:
        assert bl_target(rom, site) == CONVERT and at(site - 4, "02220323"), "%08X" % A(site)
    assert u32(SUMMARY_NO_LITERAL) == 0x02021CC4 and at(0x1C264E, "144e"), "the summary's No buffer"
    # the veneer's room: the game's old flag routine after its jump - nothing reaches it
    assert at(0x0C0664, "004b1847") and u32(0x0C0668) == 0x09257951
    for o in range(0x0000000, 0x01DB680, 2):
        t = bl_target(rom, o)
        if t is not None:
            assert not (A(VENEER) <= t < A(DEAD_END)), "%08X calls into the dead body" % A(o)
    # words: none points at the 16 bytes rewritten (four words of sound data hold 0x080C0700-0x080C0704 by chance)
    for i, v in enumerate(words):
        assert not (A(VENEER) <= v & ~1 < A(VENEER_END)), "%08X points into the veneer's room" % A(4 * i)
    src = open(os.path.join(HERE, "dexext.s"), encoding="ascii").read()
    fill = {"EXT_ADDR": "0x%08X" % EXT_ADDR, "MAGIC": "0x%08X" % MAGIC, "ORIG_CLEAR": "0x%08X" % ORIG_CLEAR}
    for k, v in fill.items():
        src = re.sub(r"\b%s\b" % k, v, src)
    probe = thumb(src, 0x09B00000)[0]
    base = put(bytes(len(probe)))
    code, dis = thumb(src, base)
    rom[base - 0x08000000:base - 0x08000000 + len(code)] = code
    pushes = [i.address for i in dis if i.mnemonic == "push"]
    entry = dict(zip(("dex_flag", "dex_clear", "conv_dexnum", "conv_dexnum_sum", "dex_digits"), pushes))
    assert pushes[0] == base and len(pushes) == 5
    rom[DEX_FLAG:DEX_FLAG + 8] = bytes.fromhex("004b1847") + struct.pack("<I", entry["dex_flag"] | 1)
    struct.pack_into("<I", rom, CLEAR_WORD, entry["dex_clear"] | 1)
    for site, (func, ven_at) in CONVERT_SITES.items():
        ven = ("push {r0}\n ldr r0, [pc, #8]\n mov ip, r0\n pop {r0}\n bx ip\n mov r8, r8\n"
               " .word 0x%08X\n" % (entry[func] | 1))
        vcode, _ = SM.thumb(ven, A(ven_at))
        assert len(vcode) == 16 and VENEER <= ven_at and ven_at + 16 <= VENEER_END
        rom[ven_at:ven_at + 16] = vcode
        rom[site:site + 4] = bl(A(site), A(ven_at))
    blk = ("add r0, sp, #4\n adds r1, r6, #0\n ldr r3, [pc, #8]\n bl bxr3\n b done\nbxr3:\n bx r3\n"
           " mov r8, r8\n .word 0x%08X\n" % (entry["dex_digits"] | 1))
    filler = (DIGITS_END - DIGITS_AT)
    trial, _ = SM.thumb(blk.replace("b done", "b 0x%08X" % A(DIGITS_END)), A(DIGITS_AT))
    assert len(trial) <= filler
    rom[DIGITS_AT:DIGITS_END] = trial + bytes.fromhex("c046") * ((filler - len(trial)) // 2)

    with open(outp, "wb") as f:
        f.write(rom)
    print("\n".join(report))
    print("\n".join(species_rows))
    print("moves:\n" + "\n".join(move_rows))
    print("left out of the lists: %s" % ", ".join(sorted(left_out)))
    print("evolutions: " + "; ".join(evo_rows))
    print("wild:\n" + "\n".join(wild_rows))
    print("abilities: %s" % ", ".join("%s %d" % kv for kv in sorted(ability_id.items())))
    print("items: %s; the Lilycove list %08X" % (", ".join("%s %d" % kv for kv in item_id.items()), new_list))
    print("Pokedex: entries %08X (%d), dexext %08X..%08X %s" % (new_entries, DEX_ENTRIES_N, base, base + len(code),
          ", ".join("%s %08X" % kv for kv in entry.items())))
    print("gen9rest: data %08X..%08X" % (A(SPACE), A(pos[0])))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3])
