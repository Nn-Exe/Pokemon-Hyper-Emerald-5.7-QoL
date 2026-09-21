"""DexNav screen (Hyper Emerald v5.7). Apply after the shinybox build.
usage: python dexnav_patch.py <in.gba> <out.gba>

Start menu -> DexNav: a screen listing every wild Pokemon of the map you are standing on - Land, Water,
Rock Smash and Fishing - as unique species with icon, level range and where they appear, seven per page.
LEFT/RIGHT (or L/R) page, B returns to the start menu with the cursor where it was. Read-only: it reads
the hack's encounter tables (0x08E17D50 and the seven-city extra table 0x08553894) and the save location.

ROM changes: the 13-entry start menu table is copied to free space with a 14th "DexNav" entry and the two
literals that reference it are repointed (same trick as the party menu relearner); the tail of
BuildNormalStartMenu (movs r0,#7 / bl AddStartMenuAction / pop) becomes a trampoline to a stub that adds
DexNav then Exit. Everything else is new code and data in free space. No save data is used.
"""
import struct, sys, os, re
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FDA218
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

MENU_TABLE = 0x510540                       # sStartMenuItems, 13 x {text*, func*}
MENU_TABLE_REFS = (0x09F818, 0x09FB78)      # literals -> repointed to the 14-entry copy
MENU_HOOKS = (0x09F524, 0x09F55E)           # tails of BuildNormalStartMenu and BuildSafariZoneStartMenu:
ADD_ACTION = 0x0809F4B0                     #   movs r0,#7; bl AddStartMenuAction; pop {r0}  (8 bytes)


def is_menu_tail(rom, site):
    """movs r0,#7 / bl AddStartMenuAction / pop {r0} at `site`?"""
    if rom[site:site + 2] != b"\x07\x20" or rom[site + 6:site + 8] != b"\x01\xbc":
        return False
    hi, lo = struct.unpack_from("<HH", rom, site + 2)
    if hi >> 11 != 0x1E or lo >> 11 != 0x1F:
        return False
    off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if off & 0x400000:
        off -= 0x800000
    return 0x08000000 + site + 2 + 4 + off == ADD_ACTION
MENU_ICON = bytes((0x01, 0xF7))              # the hack's Dex icon glyph, as on its own menu labels

CHARS = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARS.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({" ": 0x00, ".": 0xAD, "-": 0xAE, "/": 0xBA, "!": 0xAB, "'": 0xB4, "é": 0x1B})


def text(s, raw=b""):
    return raw + bytes(CHARS[c] for c in s) + b"\xFF"


def thumb(src, addr):
    """Assemble; check for Thumb-2 on a twin whose literal pools are nops (same size and layout, so the
    linear disassembly never stops at a pool word), and return (real bytes, twin disassembly)."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 nop\n    nop", src, flags=re.M), addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code, dis


def label_addr(code, base, push_ops):
    """address of the n-th function whose first instruction is `push_ops`."""
    return [i.address for i in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, base)
            if i.mnemonic == "push" and i.op_str == push_ops]


def assemble_blob():
    """Assemble the screen exactly as it is written into the ROM. Returns the code and data bytes with
    the addresses of everything another patch might want to call. Deterministic: the same source and the
    same BASE always give the same bytes, which is what lets patches/dexnavchain verify it against the ROM."""

    # ---- data blob (addresses fixed once the code length is known) ----
    def data_blob(base):
        d = bytearray()
        addrs = {}
        def put(name, b, align=1):
            while len(d) % align: d.append(0)
            addrs[name] = base + len(d); d.extend(b)
        put("BGTEMPLATE", struct.pack("<HH", 0x31F0, 0), 4)              # bg0, char 0, map 31, priority 3 (icons draw over it)
        put("WINTEMPLATES", bytes((0, 1, 0, 28, 2, 15)) + struct.pack("<H", 1)
                           + bytes((0, 1, 2, 28, 18, 15)) + struct.pack("<H", 57)
                           + bytes((0xFF, 0, 0, 0, 0, 0)) + struct.pack("<H", 0), 4)
        pal = [0] * 16
        pal[1] = 0x7FFF                                                  # white
        pal[2] = 0x18C6                                                  # near-black text
        pal[3] = 0x5AD6                                                  # grey shadow
        pal[4] = 0x5140                                                  # header band (dark teal)
        pal[5] = 0x26A6                                                  # Land: green
        pal[6] = 0x75E6                                                  # Water: blue
        pal[7] = 0x19B5                                                  # Rock: brown
        pal[8] = 0x6512                                                  # Fish: purple
        put("TEXTPAL", struct.pack("<16H", *pal), 4)
        put("BACKDROP", struct.pack("<H", 0x2D07), 4)                    # dark green backdrop
        put("COLORS_HDR", bytes((4, 1, 4)), 4)
        put("COLORS_NORM", bytes((1, 2, 3)), 4)
        put("COLORS_LAND", bytes((1, 5, 3)), 4); put("COLORS_WATER", bytes((1, 6, 3)), 4)
        put("COLORS_ROCK", bytes((1, 7, 3)), 4); put("COLORS_FISH", bytes((1, 8, 3)), 4)
        put("SECTIONCOLORS", struct.pack("<4I", addrs["COLORS_LAND"], addrs["COLORS_WATER"], addrs["COLORS_ROCK"], addrs["COLORS_FISH"]), 4)
        put("STR_DEXNAV", text("DexNav"), 4)
        put("STR_NONE", text("No wild Pokémon on this map."), 4)
        put("SEC_LAND", text("Land")); put("SEC_WATER", text("Water"))
        put("SEC_ROCK", text("Rock")); put("SEC_FISH", text("Fish"))
        put("SECTIONNAMES", struct.pack("<4I", addrs["SEC_LAND"], addrs["SEC_WATER"], addrs["SEC_ROCK"], addrs["SEC_FISH"]), 4)
        put("TABLES", struct.pack("<2I", 0x08E17D50, 0x08553894), 4)
        put("COUNTS", bytes((12, 5, 5, 10)), 4)
        put("MENU_LABEL", text("DexNav", MENU_ICON), 4)
        return bytes(d), addrs

    src = open(os.path.join(HERE, "dexnav.s"), encoding="ascii").read()

    def assemble(code_addrs, data_addrs):
        s = src
        for k, v in list(code_addrs.items()) + list(data_addrs.items()):
            s = s.replace(k + "_ADDR", "0x%08X" % v)
        return thumb(s, BASE)

    # pass 1: sizes and function positions
    dummy_code = {k: BASE for k in ("CB2_INIT", "CB2_MAIN", "VBLANK", "TASK")}
    _, dummy_data = data_blob(BASE)
    code, dis = assemble(dummy_code, dummy_data)
    code_len = (len(code) + 3) & ~3
    data_base = BASE + code_len
    data, daddrs = data_blob(data_base)
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    # function order in dexnav.s: menu_callback, cb2_init, cb2_main, vblank, task, page_count, draw_page, print,
    # u8dec, find_header, find, fill_scratch = 12 functions that start with push (pools never decode as one)
    assert len(funcs) == 12, "unexpected function layout: %d pushes" % len(funcs)
    caddrs = {"CB2_INIT": funcs[1] | 1, "CB2_MAIN": funcs[2] | 1, "VBLANK": funcs[3] | 1, "TASK": funcs[4] | 1}
    menu_callback = funcs[0] | 1
    code, _ = assemble(caddrs, daddrs)
    assert (len(code) + 3) & ~3 == code_len
    assert code[1] == 0x48, "menu_stub (ldr r0, [pc, ...]) is not first"   # the trampoline lands on it
    return code, code_len, data, data_base, daddrs, funcs, menu_callback, caddrs


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    for site in MENU_HOOKS:
        assert is_menu_tail(rom, site), "start menu builder tail at %X differs" % site
    for r in MENU_TABLE_REFS:
        assert struct.unpack_from("<I", rom, r)[0] == 0x08000000 + MENU_TABLE, "menu table literal moved"
    menu = bytes(rom[MENU_TABLE:MENU_TABLE + 13 * 8])
    for i in range(13):
        t, f = struct.unpack_from("<II", menu, i * 8)
        assert 0x08000000 <= t < 0x0A000000 and f & 1, "start menu table is not the expected shape"

    code, code_len, data, data_base, daddrs, funcs, menu_callback, caddrs = assemble_blob()
    blob = bytearray(code) + bytes(code_len - len(code)) + data
    while len(blob) % 4: blob.append(0)
    table_addr = BASE + len(blob)
    blob += menu + struct.pack("<II", daddrs["MENU_LABEL"], menu_callback)   # 14-entry start menu table
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    for r in MENU_TABLE_REFS:
        struct.pack_into("<I", rom, r, table_addr)
    for site in MENU_HOOKS:                                              # normal and Safari Zone menus
        if site % 4 == 0:
            rom[site:site + 4] = bytes.fromhex("004b1847")                # ldr r3,[pc,#0]; bx r3; .word
            struct.pack_into("<I", rom, site + 4, BASE | 1)
        else:                                                            # pc rounds down: literal goes at +6,
            assert rom[site + 8:site + 10] == b"\x00\x47", "no dead bx r0 after the tail at %X" % site
            rom[site:site + 6] = bytes.fromhex("014b1847c046")            # ldr r3,[pc,#4]; bx r3; nop; .word
            struct.pack_into("<I", rom, site + 6, BASE | 1)              # (eats the tail's own bx r0)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X (callback %08X, cb2_init %08X, task %08X), data @%08X, menu table @%08X, end %08X" % (
        len(code), BASE, menu_callback, caddrs["CB2_INIT"], caddrs["TASK"], data_base, table_addr, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
