"""Gen 9 in the official National Dex order - for the Whole Gen 9 TEST build only (after gen9rest).

    python -I gen9dex_patch.py <whole Gen 9 build> <out.gba>

The user (2026-10-15): "for order of pokedex, reorder only gen9, don't touch the original rom since I don't wanna
risk bugs, also beaware of area zero implementation". gen9 numbered its 38 slots 906-940 (the hack's flags stopped at
959 then) and gen9rest its 85 from 941; the 120 Gen 9 Pokemon all had numbers other than their own. gen9rest made room
to 1032, so now each gets its official number (Sprigatito 906 ... Pecharunt 1025). Numbers 1-905 and the main game
(rom/, which has no gen9rest) are not touched.

What holds a Pokedex number, and what this patch does to it:
  * SpeciesToNationalPokedexNum's table (literal 0x0806D448): slots 1200-1326 get their official numbers (Ogerpon's
    masks share Ogerpon's; Paldean Wooper and the Tauros breeds keep 194 / 128). NationalPokedexNumToSpecies searches
    that table: nothing else to change.
  * the Pokedex entries (gen9rest's 1,040-entry table; 32 bytes each, indexed by number): rows 906-1025 moved.
  * the three order tables (height, name, weight; gen9rest's): every number 906-1032 in them renamed. They are sorted
    by what the entry says, which moves with the Pokemon, so their order stays right.
  * Area Zero's Legends rows (paldea/journal_az.py: {number, 0, name, hint, where}, the table at the literal
    0x08FEB23C): Koraidon, Miraidon, the four Treasures of Ruin and Terapagos renamed. Their order among themselves is
    the same in both numberings (both follow the Dex), and they stay after every older legend.
  * the marks in saves: gen9dex.s. A save made before (the main game's, a test build's) has its Gen 9 seen / caught
    marks in the old numbers; the first time the game asks for a mark they are moved (gen9dex.s says how), and
    dexext's marker word becomes NEW so it happens once. A save moved on cannot go back to the main game's numbers:
    the main game would show Gen 9 marks on the wrong Pokemon.
Nothing else stores a number: DexNav, the summary, the Pokedex list and counts, the Quest Log ask
SpeciesToNationalPokedexNum or the flag routine as they run.

And one thing seen while testing it: the Pokedex page (and the new-entry page after a catch, the same routine) printed
"{NO}{CLEAR 1}" and then the number, four digits from 1000 (gen9rest's conv_dexnum), with the name at x 132: the last
digit ran into the name ("No1014Okidogi"). From 1000 the digits now go where "{NO}{CLEAR 1}" was, as the list and the
summary already show them ("1014 Okidogi"); below 1000 nothing changes. page_num below, reached by the word of the
page's veneer (0x080C066C) that pointed at conv_dexnum, and going on to it.
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(REPO, "patches", "gen9"), os.path.join(REPO, "patches", "gen9rest")]
import gen9_data as A
import gen9rest_data as D

B = 0x08000000
NATDEX_LIT = 0x0806D448
ENTRY_WORDS = [0x080BFA20, 0x080BFADC, 0x080C02F8, 0x080C0328, 0x080C062C, 0x080C0650, 0x080C0660, 0x081DB48C]
ORDER_WORDS = [0x09257FA0, 0x09257FA4, 0x09257FA8]       # height, name, weight
ORDER_N = 1032
LEG_LIT, LEG_PAGE = 0x08FEB23C, 0x08FEC5EC + 8 * 4         # Area Zero's Legends table; the chapter's row count
DEX_FLAG_JUMP = 0x09257950                               # the hack's GetSetPokedexFlag: gen9rest's 8-byte jump
DEXEXT = (0x09C28594, 0x09C2872C)                        # gen9rest's dexext code (dex_flag first)
OLD_MAGIC, NEW_MAGIC = 0x39584544, 0x41584544            # "DEX9" -> "DEXA"
CODE_AT = 0x09C28800                                     # zero-filled, after dexext (nothing points in)
PAGE_VENEER = 0x080C066C                                 # the Pokedex page's call of conv_dexnum: a 16-byte veneer
PAGE_NO = 0x085E8D4F                                     # "{NO}{CLEAR 1}", copied in front of the page's number
PAGE_AT = CODE_AT + 0x3C0                                # page_num, after the marks' code
PAGE_SRC = """
    push {r4}
    ldr r4, l_thousand
    cmp r1, r4
    blo pn_go
    subs r0, #5                     @ from 1000: the digits over "{NO}{CLEAR 1}" (5 bytes)
pn_go:
    ldr r4, l_conv
    mov ip, r4
    pop {r4}
    bx ip
    PAD1
l_thousand: .word 1000
l_conv:     .word CONV_DEXNUM
"""
FIRST, OLD_COUNT = 906, 127                              # old numbers 906-1032


def u16(rom, a): return struct.unpack_from("<H", rom, a - B)[0]
def u32(rom, a): return struct.unpack_from("<I", rom, a - B)[0]


def official_numbers():
    """slot -> official number for every Gen 9 slot (1200-1326)."""
    o9 = json.load(open(os.path.join(REPO, "patches", "gen9", "official.json"), encoding="utf-8"))
    o9r = json.load(open(os.path.join(REPO, "patches", "gen9rest", "official.json"), encoding="utf-8"))
    out = {}
    for i, (key, name, crest, icon, share) in enumerate(A.SPECIES):
        k = key if key in o9 else key.split("-")[0]
        out[A.FIRST_SLOT + i] = o9[k]["dex"] if not key.startswith("ogerpon") else o9["ogerpon"]["dex"]
    for i, t in enumerate(D.SPECIES):
        key, form_of = t[0], t[4]
        out[D.FIRST_SLOT + i] = None if form_of else o9r[key]["dex"]   # forms keep their numbers
    return out


def thumb(src, base):
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(src, base)[0])
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, base))
    return code, dis


def assemble(base, fill):
    src = open(os.path.join(HERE, "gen9dex.s"), encoding="ascii").read()
    for k, v in fill.items():
        src = re.sub(r"\b%s\b" % k, v, src)
    for pad in ("", "    mov r8, r8"):
        code, dis = thumb(src.replace("    PAD1", pad), base)
        pool = code.find(struct.pack("<I", 0x0203DA00))
        if pool % 4 == 0:
            break
    else:
        raise AssertionError("the literal pool will not align")
    # the safety checks of the project's patchers: no 4-byte instruction but bl, no Thumb-2 nop, every push counted
    body = dis[:[i.address for i in dis].index(base + pool) if base + pool in [i.address for i in dis] else len(dis)]
    for i in body:
        assert i.size == 2 or i.mnemonic == "bl", "%08X %s %s" % (i.address, i.mnemonic, i.op_str)
        assert not (i.bytes == b"\x00\xbf"), "a Thumb-2 nop"
    return code, pool


def main(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    natdex = u32(rom, NATDEX_LIT)
    dexof = lambda s: u16(rom, natdex + 2 * (s - 1))
    # the build this goes on: gen9's 38 at 906-940, gen9rest's 85 from 941, dexext's jump and marker as gen9rest left them
    assert dexof(1200) == 906 and dexof(1237) == 940 and dexof(1238) == 941 and dexof(1322) == 1025, "not the numbering it expects"
    assert rom[DEX_FLAG_JUMP - B:DEX_FLAG_JUMP - B + 4] == bytes.fromhex("004b1847") and u32(rom, DEX_FLAG_JUMP + 4) == DEXEXT[0] | 1
    magic_at = [a for a in range(DEXEXT[0], DEXEXT[1], 4) if u32(rom, a) == OLD_MAGIC]
    assert len(magic_at) == 1, magic_at
    assert set(rom[CODE_AT - B:CODE_AT - B + 0x400]) == {0}
    # the page's veneer (push {r0}; ldr r0, [pc, #8]; mov ip, r0; pop {r0}; bx ip; mov r8, r8; .word conv_dexnum)
    # and the text in front of the number
    assert rom[PAGE_VENEER - B:PAGE_VENEER - B + 12] == bytes.fromhex("01b40248844601bc6047c046")
    conv_dexnum = u32(rom, PAGE_VENEER + 12)
    assert DEXEXT[0] < conv_dexnum < DEXEXT[1] and conv_dexnum & 1, "%08X" % conv_dexnum
    assert rom[PAGE_NO - B:PAGE_NO - B + 6] == bytes.fromhex("f908fc1101ff"), "the page's \"No\" text"

    new_of = official_numbers()
    old_to_new = {}
    for slot, new in new_of.items():
        if new is None:
            continue
        old = dexof(slot)
        assert old_to_new.setdefault(old, new) == new, (slot, old, new)
    assert sorted(old_to_new) == list(range(906, 1026)) and sorted(old_to_new.values()) == list(range(906, 1026)), \
        "the renumbering is not one Gen 9 number for one"
    m = lambda n: old_to_new.get(n, n)

    # 1. SpeciesToNationalPokedexNum's table
    for slot, new in new_of.items():
        if new is not None:
            struct.pack_into("<H", rom, natdex - B + 2 * (slot - 1), new)
    # 2. the entries
    E = u32(rom, ENTRY_WORDS[0])
    assert all(u32(rom, w) == E for w in ENTRY_WORDS)
    old_rows = {n: bytes(rom[E - B + 32 * n:E - B + 32 * n + 32]) for n in old_to_new}
    for old, new in old_to_new.items():
        rom[E - B + 32 * new:E - B + 32 * new + 32] = old_rows[old]
    # 3. the order tables
    for w in ORDER_WORDS:
        t = u32(rom, w)
        vals = list(struct.unpack_from("<%dH" % ORDER_N, rom, t - B))
        assert sorted(v for v in vals if v) == list(range(1, 1026)), "order table %08X" % t
        struct.pack_into("<%dH" % ORDER_N, rom, t - B, *[m(v) for v in vals])
    # 3b. A to Z: gen9rest put the Gen 9 names in by Python's string order, where "-" comes before every letter and
    # digit; the game's own order is its character codes (digits 0xA1.., "-" 0xAE, letters 0xBB..: "PORYGON2" then
    # "PORYGON-Z", "HO-OH" before "HOUNDOOM"), so Chi-Yu, Wo-Chien and Houndstone stood one place off. The Gen 9
    # numbers are taken out and put back by the game's codes, case folded; numbers 1-905 keep their places (the
    # hack's own few out of order - Nidoran, the species it appended after Zubat - are left as they are).
    names = u32(rom, 0x08000144)
    first = {}
    for s in range(1, 1408):
        n = dexof(s)
        if n and n not in first:
            first[n] = s
    def gkey(n):
        raw = bytes(rom[names - B + 11 * first[n]:names - B + 11 * first[n] + 11]).split(b"\xff")[0]
        return bytes((c - 0x1A if 0xD5 <= c <= 0xEE else c) for c in raw)
    t = u32(rom, ORDER_WORDS[1])
    vals = [v for v in struct.unpack_from("<%dH" % ORDER_N, rom, t - B) if v]
    order = [v for v in vals if not 906 <= v <= 1025]
    for n in sorted(range(906, 1026), key=gkey):
        at_ = next((x for x, v in enumerate(order) if gkey(v) > gkey(n)), len(order))
        order.insert(at_, n)
    assert sorted(order) == list(range(1, 1026))
    struct.pack_into("<%dH" % ORDER_N, rom, t - B, *(order + [0] * (ORDER_N - len(order))))
    # 4. Area Zero's Legends rows
    leg, rows = u32(rom, LEG_LIT), rom[LEG_PAGE - B + 1]
    renamed = []
    for i in range(rows):
        n = u16(rom, leg + 16 * i)
        if n in old_to_new:
            struct.pack_into("<H", rom, leg - B + 16 * i, old_to_new[n])
            renamed.append((n, old_to_new[n]))
    assert len(renamed) == 7, renamed
    assert [b for a, b in renamed] == sorted(b for a, b in renamed), "Area Zero's legends out of order"
    # 5. the marks: the map, the code, the jump, dexext's marker
    table = struct.pack("<%dH" % OLD_COUNT, *[old_to_new.get(FIRST + i, 0) for i in range(OLD_COUNT)])
    fill = {"NEW_MAGIC": "0x%08X" % NEW_MAGIC, "DEX_FLAG": "0x%08X" % (DEXEXT[0] | 1), "OLD_COUNT": str(OLD_COUNT),
            "MAP_ADDR": "0x%08X" % CODE_AT}
    code, pool = assemble(CODE_AT + 0x100, dict(fill, MAP_ADDR="0x%08X" % CODE_AT))
    assert len(table) <= 0x100
    rom[CODE_AT - B:CODE_AT - B + len(table)] = table
    rom[CODE_AT - B + 0x100:CODE_AT - B + 0x100 + len(code)] = code
    struct.pack_into("<I", rom, DEX_FLAG_JUMP - B + 4, (CODE_AT + 0x100) | 1)
    # 6. the page's number from 1000
    assert CODE_AT + 0x100 + len(code) <= PAGE_AT
    for pad in ("", "    mov r8, r8"):
        page, dis = thumb(PAGE_SRC.replace("CONV_DEXNUM", "0x%08X" % conv_dexnum).replace("    PAD1", pad), PAGE_AT)
        lit = page.find(struct.pack("<I", 1000))
        if lit % 4 == 0:
            break
    assert all(i.size == 2 and i.bytes != b"\x00\xbf" for i in dis if i.address < PAGE_AT + lit)
    rom[PAGE_AT - B:PAGE_AT - B + len(page)] = page
    struct.pack_into("<I", rom, PAGE_VENEER - B + 12, PAGE_AT | 1)
    struct.pack_into("<I", rom, magic_at[0] - B, NEW_MAGIC)
    open(outp, "wb").write(rom)
    print("gen9dex: 127 slots renumbered (%d Gen 9 numbers), entries %08X, order tables, Legends %s, "
          "marks moved by %08X (map %08X), marker %08X -> %08X at %08X, page number %08X"
          % (len(old_to_new), E, ", ".join("%d->%d" % r for r in renamed), CODE_AT + 0x100, CODE_AT,
             OLD_MAGIC, NEW_MAGIC, magic_at[0], PAGE_AT))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
