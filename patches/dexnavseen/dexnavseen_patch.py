"""DexNav: unseen species stay hidden (Hyper Emerald v5.7). Apply after dexnav and dexnavchain (anywhere later).
usage: python dexnavseen_patch.py <in.gba> <out.gba>

On the DexNav screen a species the Pokedex has not seen is a black shadow named "?????", the hint in the header
reads "Not seen yet" instead of "A: Register", and A on it plays the failure buzz and keeps the screen open.
On a map with no wild Pokemon the hint is left empty (it said "A: Register" over "No wild Pokemon on this map").
Seeing it once - in any battle, as for the Pokedex - lifts all of that. The DexNav code is in the v1.4 base ROM
(patches/dexnav, patches/dexnavchain), so this patch hooks it instead of rebuilding it: four `bl`s, each checked
against the bytes and call target it replaces (dexnavseen.s says what each hook does).
Seen = GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_GET_SEEN): the hack's routine, one bit per dex
number at SaveBlock1+0x560, set by the battle's HandleSetPokedexFlag. A species with no dex number is never hidden.
The shadow is a 16-colour sprite palette, all black but the transparent colour 0, loaded under its own tag next to
the six mon-icon palettes the page draw loads, and put into the icon sprite's OAM.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
import sinnohmap_patch as SM                    # the Thumb check
from inserter import ENC

FREE = 0x00FF6B00                               # in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, after fastsurf
FREE_END = 0x00FF7700                           # (..0x08FF6AB4); a data word happens to read 0x08FF7703
BASE = 0x08000000 + FREE
SHADOW_TAG = 0x5E64                             # typeicons uses 0x5E62 (battle only); mon icons 0xDAC0..0xDAC5

# (site, what is there now, what it calls, the hook that replaces it)
ICON_BL, CALLR4 = 0x08FDA610, 0x08FDA464        # draw_page: ldr r4, =CreateMonIcon; bl callr4
NAME_BL, PRINT = 0x08FDA628, 0x08FDA6AA         # draw_page: ... ldr r4, =colours; bl print
ARM_BL, ARM_SEARCH = 0x08FDE708, 0x08FDE89A     # dt_arm: ... ldrb r1, [r1, #2]; bl arm_search
HINT_AT = 0x08FDE7F8                            # draw_hint: ldr r2, =state; ldrb r3, [r2, #9]
CUR_INDEX, DN_EXIT = 0x08FDE738, 0x08FDE734
FIND, SCRATCH, STATE = 0x08FDA791, 0x02021DC4, 0x0203A660


def bl(src, dst):
    off = (dst & ~1) - (src + 4)
    assert -0x400000 <= off < 0x400000 and off % 2 == 0, "bl out of range %08X -> %08X" % (src, dst)
    off = (off >> 1) & 0x3FFFFF
    return struct.pack("<HH", 0xF000 | (off >> 11), 0xF800 | (off & 0x7FF))


def bl_target(rom, src):
    x, y = struct.unpack_from("<HH", rom, src - 0x08000000)
    assert x & 0xF800 == 0xF000 and y & 0xF800 == 0xF800, "%08X is not a bl" % src
    off = ((x & 0x7FF) << 12) | ((y & 0x7FF) << 1)
    if off & 0x400000:
        off -= 0x800000
    return src + 4 + off


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)
    enc = lambda s: bytes(ENC[c] for c in s)
    ldr_value = lambda a: u32(((a + 4) & ~3) + (struct.unpack_from("<H", rom, o(a))[0] & 0xFF) * 4)

    # the DexNav's code as dexnav / dexnavchain built it
    assert at(ICON_BL - 6, "01240294") and ldr_value(ICON_BL - 2) == 0x080D2CC5 and bl_target(rom, ICON_BL) == CALLR4
    assert at(CALLR4, "2047"), "callr4 moved"
    assert at(NAME_BL - 10, "4318012028212a1c") and bl_target(rom, NAME_BL) == PRINT and at(PRINT, "30b585b0")
    assert ldr_value(0x08FDA5EC) == SCRATCH, "the page draw's scratch (r6) moved"
    assert at(ARM_BL - 8, "08880b79ca788978") and bl_target(rom, ARM_BL) == ARM_SEARCH and at(ARM_SEARCH, "70b51e1c")
    assert at(HINT_AT - 4, "85b0") and ldr_value(HINT_AT) == STATE and at(HINT_AT + 2, "537a01200342")
    assert at(CUR_INDEX, "00b52088c100091a60884018") and at(DN_EXIT, "01b070bd")
    assert ldr_value(0x08FDE6DA) == FIND and ldr_value(0x08FDE6FE) == SCRATCH and ldr_value(0x08FDE6E4) == STATE
    assert at(0x080C0664, "004b1847") and u32(0x080C0668) == 0x09257951, "GetSetPokedexFlag is not the hack's trampoline"
    assert u32(0x0806D4BC) == 0x08F50370, "SpeciesToNationalPokedexNum's table moved"

    unknown = enc("?????") + b"\xFF"
    unseen = enc("Not seen yet") + b"\xFF"
    blank = b"\xFF"

    def assemble(shadow, s_unknown, s_unseen, s_blank):
        src = open(os.path.join(HERE, "dexnavseen.s"), encoding="ascii").read()
        for k, v in (("FIND_ADDR", FIND), ("SCRATCH_ADDR", SCRATCH), ("STATE_ADDR", STATE), ("DN_EXIT_ADDR", DN_EXIT | 1),
                     ("SHADOW_ADDR", shadow), ("STR_UNKNOWN_ADDR", s_unknown), ("STR_UNSEEN_ADDR", s_unseen), ("STR_BLANK_ADDR", s_blank),
                     ("PRINT_ADDR", PRINT), ("CUR_INDEX_ADDR", CUR_INDEX), ("ARM_SEARCH_ADDR", ARM_SEARCH)):
            src = src.replace(k, "0x%08X" % v)
        return SM.thumb(src, BASE)

    code, _ = assemble(BASE, BASE, BASE, BASE)
    data = BASE + ((len(code) + 3) & ~3)
    shadow, pal = data, data + 8
    s_unknown = pal + 32
    s_unseen = s_unknown + len(unknown)
    s_blank = s_unseen + len(unseen)
    code2, dis = assemble(shadow, s_unknown, s_unseen, s_blank)
    assert len(code2) == len(code)
    funcs = [i.address for i in dis if i.mnemonic == "push" and "lr" in i.op_str]
    assert len(funcs) == 5, "expected icon_hook, name_hook, hint_pick, arm_hook and is_seen, found %d" % len(funcs)
    icon_hook, name_hook, hint_pick, arm_hook, is_seen = funcs
    blob = bytearray(code2) + b"\x00" * (data - BASE - len(code2))
    blob += struct.pack("<IHH", pal, SHADOW_TAG, 0)
    blob += struct.pack("<16H", *([0] * 16))    # colour 0 is transparent; 1-15 black
    blob += unknown + unseen + blank
    end = FREE + len(blob)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = blob

    rom[o(ICON_BL):o(ICON_BL) + 4] = bl(ICON_BL, icon_hook)
    rom[o(NAME_BL):o(NAME_BL) + 4] = bl(NAME_BL, name_hook)
    rom[o(ARM_BL):o(ARM_BL) + 4] = bl(ARM_BL, arm_hook)
    rom[o(HINT_AT):o(HINT_AT) + 4] = bl(HINT_AT, hint_pick)
    open(outp, "wb").write(rom)
    print("icon_hook %08X, name_hook %08X, hint_pick %08X, arm_hook %08X, is_seen %08X; shadow palette %08X (tag %04X), "
          "end %08X" % (icon_hook, name_hook, hint_pick, arm_hook, is_seen, pal, SHADOW_TAG, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
