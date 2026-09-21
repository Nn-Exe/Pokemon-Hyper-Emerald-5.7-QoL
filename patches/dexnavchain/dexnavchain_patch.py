"""DexNav search and chain (Hyper Emerald v5.7). Apply after the sinnohmap build.

On the DexNav screen the cursor picks a species and A starts tracking it; a bar at the top of the field
says what you are hunting, and the next wild Pokemon of that map is that species. Catching or defeating it
raises the chain, which improves the next one's odds (shiny rerolls, perfect IVs shown as stars, and an egg
move). Running, losing or leaving the map ends the chain.

ROM changes, all of them pointers - no game routine is rewritten:
  * the word the hack's CreateWildMon trampoline jumps through (0x080B4E6C) now points at our stub, which
    calls that same routine and only chooses what to ask it for;
  * the overworld hook the earlier patches installed is chained through ours;
  * the DexNav screen's task pointer, inside our own dexnav blob, points at a task that calls the original
    and adds the cursor and A.
Everything else is new code and data in free space. Nothing is written to the save.

The DexNav blob is re-assembled here from patches/dexnav and checked byte for byte against the ROM, which
is what makes its internal addresses (task, draw_page, find) safe to call.
"""
import struct, sys, os, re
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "dexnav"))
import dexnav_patch

FREE = 0x00FDE4A0                       # after the Sinnoh map blob (ends 0x08FDE494), free to 0x08FE0000
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

STATE = 0x0203A660                      # 32 bytes of state, then 96 of text scratch.  Verified untouched by
SCRATCH = STATE + 32                    # the game: see docs/NOTES.md (pattern test through battles + save)

WILD_TRAMPOLINE = 0x0B4E68              # CreateWildMon: ldr r2,[pc,#0]; bx r2; .word <hack's own>
WILD_TARGET = 0x0B4E6C
OW_HOOK = 0x085E5C                      # CB2_Overworld's first instruction, already a trampoline
OW_TARGET = 0x085E60

# The font has no star (0x70-0x7F is only the four arrows), so the bar carries its own 8x8 tiles: one lit
# for a star earned, one grey for a star not earned. 4bpp, two pixels per byte, low nibble first.
STAR_ART = ("...#....",          # drawn into the bar's second tile row, level with the name
            "#######.",
            ".#####..",
            "..###...",
            ".##.##..",
            "........",
            "........",
            "........")


BAR_BLACK = 10                          # the palette slot we keep black; see black_slot() in the source


def star_tile(ink):
    """One 8x8 tile, 4bpp. The background is the bar's own black, not transparent - these tiles are
    written straight over the window's buffer, so anything left at index 0 would show the map through."""
    out = bytearray()
    for row in STAR_ART:
        for x in range(0, 8, 2):
            lo = ink if row[x] == "#" else BAR_BLACK
            hi = ink if row[x + 1] == "#" else BAR_BLACK
            out.append(lo | (hi << 4))
    return bytes(out)

CHARS = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARS.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({" ": 0x00, ".": 0xAD, "-": 0xAE, "/": 0xBA, "!": 0xAB, "'": 0xB4})


def text(s, raw=b""):
    return raw + bytes(CHARS[c] for c in s) + bytes([0xFF])


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 nop\n    nop", src, flags=re.M), addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (
        addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code, dis


def dexnav_symbols(rom):
    """The DexNav screen's own addresses, proven by rebuilding its blob and comparing with the ROM."""
    code, code_len, data, data_base, daddrs, funcs, menu_callback, caddrs = dexnav_patch.assemble_blob()
    blob = bytes(code) + bytes(code_len - len(code)) + data
    assert bytes(rom[dexnav_patch.FREE:dexnav_patch.FREE + len(blob)]) == blob, (
        "the DexNav blob in this ROM is not the one patches/dexnav builds - apply dexnav first, "
        "and do not edit dexnav.s without rebuilding from it")
    names = ("menu_callback", "cb2_init", "cb2_main", "vblank", "task", "page_count", "draw_page",
             "print", "u8dec", "find_header", "find", "fill_scratch")
    assert len(funcs) == len(names)
    return dict(zip(names, funcs))


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    dn = dexnav_symbols(rom)

    # the hack's CreateWildMon sits behind a trampoline; we step in front of what it jumps to
    assert bytes(rom[WILD_TRAMPOLINE:WILD_TRAMPOLINE + 4]) == bytes.fromhex("004a1047"), \
        "CreateWildMon is not the trampoline this patch expects"
    createwild = struct.unpack_from("<I", rom, WILD_TARGET)[0]
    assert createwild & 1 and 0x08000000 <= createwild < 0x0A000000, "CreateWildMon target looks wrong"
    assert createwild != BASE | 1, "already applied"

    # and chain onto the overworld hook the earlier patches left
    assert bytes(rom[OW_HOOK:OW_HOOK + 4]) == bytes.fromhex("004b1847"), "overworld hook is not ours"
    prevhook = struct.unpack_from("<I", rom, OW_TARGET)[0]
    assert prevhook & 1 and 0x08000000 <= prevhook < 0x0A000000, "overworld hook target looks wrong"

    # the DexNav screen's task pointer, in our own blob: exactly one literal holds it
    task_word = struct.pack("<I", dn["task"] | 1)
    dn_end = dexnav_patch.FREE + 0x1000
    hits = [i for i in range(dexnav_patch.FREE, dn_end, 4) if bytes(rom[i:i + 4]) == task_word]
    assert len(hits) == 1, "expected one reference to the DexNav task, found %d" % len(hits)
    task_literal = hits[0]

    def data_blob(base):
        d = bytearray()
        addrs = {}
        def put(name, b, align=1):
            while len(d) % align: d.append(0)
            addrs[name] = base + len(d); d.extend(b)
        # bg0, left 1, top 1, 28x4, palette 15, tiles at 0x240..0x2B0.  On the field BG0's tiles start at
        # VRAM 0x06008000 and the map's own tilemaps begin at 0x0600E000, which is tile 0x300 - anything
        # from there up scribbles over the map itself.  Below that, the field keeps its message window at
        # 0x194..0x200, the location popup at 0x107..0x125 and the standard frame at 0x214, so 0x240 is
        # clear of all of them with room to spare.
        put("WINTEMPLATE", bytes((0, 1, 1, 28, 4, 15)) + struct.pack("<H", 0x240), 4)
        put("COLORS_HUD", bytes((10, 1, 2)), 4)         # our black slot, white text, grey shadow
        put("COLORS_CUR", bytes((1, 4, 3)), 4)          # on the list window: its white bg, header colour
        put("STR_CURSOR", bytes((0x7C, 0xFF)), 4)       # the right arrow the key item popup uses
        put("STARTILES", star_tile(1) + star_tile(2), 4)   # white when earned, grey when not
        put("BLACK", struct.pack("<H", 0x0000), 4)
        return bytes(d), addrs

    src = open(os.path.join(HERE, "dexnavchain.s"), encoding="ascii").read()
    fixed = {
        "PREVHOOK": prevhook, "CREATEWILD": createwild, "STATE": STATE, "SCRATCH": SCRATCH,
        "DN_TASK": dn["task"] | 1, "DN_DRAWPAGE": dn["draw_page"] | 1, "DN_FIND": dn["find"] | 1,
    }

    def assemble(data_addrs):
        s = src
        for k, v in sorted(list(fixed.items()) + list(data_addrs.items()), key=lambda kv: -len(kv[0])):
            s = s.replace(k + "_ADDR", "0x%08X" % v)
        return thumb(s, BASE)

    _, dummy = data_blob(BASE)
    code, dis = assemble(dummy)
    code_len = (len(code) + 3) & ~3
    data, daddrs = data_blob(BASE + code_len)
    code, dis = assemble(daddrs)
    assert (len(code) + 3) & ~3 == code_len

    funcs = [i.address for i in dis if i.mnemonic == "push"]
    order = ("ow_stub", "ow_tick", "after_battle", "dn_task", "cur_index", "row_count", "draw_cursor",
             "arm_search", "reroll", "basestats", "eggpick", "rndmod", "wild_hook", "is_shiny",
             "apply_extras", "hud_draw", "hud_text", "stars", "black_slot", "prnt", "scopy", "dec3",
             "hud_live", "hud_remove", "icon_gone", "hud_refresh")
    assert len(funcs) == len(order), "unexpected function layout: %d pushes, expected %d" % (
        len(funcs), len(order))
    sym = dict(zip(order, funcs))
    assert sym["ow_stub"] == BASE, "ow_stub must be first"

    blob = bytearray(code) + bytes(code_len - len(code)) + data
    while len(blob) % 4: blob.append(0)
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    struct.pack_into("<I", rom, WILD_TARGET, sym["wild_hook"] | 1)
    struct.pack_into("<I", rom, OW_TARGET, sym["ow_stub"] | 1)
    struct.pack_into("<I", rom, task_literal, sym["dn_task"] | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, data @%08X, end %08X" % (len(code), BASE, BASE + code_len, 0x08000000 + end))
    print("  wild_hook %08X (was %08X), ow_stub %08X (chains to %08X), dn_task %08X (was %08X @%08X)" % (
        sym["wild_hook"] | 1, createwild, sym["ow_stub"] | 1, prevhook, sym["dn_task"] | 1,
        dn["task"] | 1, 0x08000000 + task_literal))
    print("  state %08X, scratch %08X" % (STATE, SCRATCH))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
