"""DexNav: the bar names the ability the Pokemon will have (Hyper Emerald v5.7). Apply after dexnavchain (anywhere
later).
usage: python dexnavabil_patch.py <in.gba> <out.gba>

The search (patches/dexnavchain, in the v1.4 base ROM) read a species' abilities from the base stats, +22 and +23,
twice: reroll() to decide whether there is a second slot to roll for, hud_text() to print the name on the bar's
second line. Those two bytes are leftovers - the game reads three u16 a species at 0x097A0000 (two regular, one
hidden) through GetAbilityBySpecies, 0x0806B694 -> 0x09D73A80. So the bar showed "-------" for the 55 wild species
whose bytes are 0 (the Gen 8 ones), another ability's name for some 130 more (Blaze on Bulbasaur, Protean on Riolu),
and 46 species with two abilities only ever came with the first.
Two `bl`s inside the dexnavchain blob now go to dexnavabil.s, each checked against the bytes around it and the
target it had: reroll's `bl basestats` (0x08FDE996) to slots_hook, and the `bl scopy` of hud_text's ability line
(0x08FDED6A) to name_hook. Nothing else in the blob changes. The hidden ability is still not given.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavseen"))
import sinnohmap_patch as SM                    # the Thumb check
from dexnavseen_patch import bl, bl_target

FREE = 0x00FF75D0                               # in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, after namingkb's
FREE_END = 0x00FF7700                           # table (..0x08FF75CC); a data word happens to read 0x08FF7703
BASE = 0x08000000 + FREE

SLOT_BL, BASESTATS = 0x08FDE996, 0x08FDEA62     # reroll: ldrh r0, [r4, #2]; bl basestats
NAME_BL, SCOPY = 0x08FDED6A, 0x08FDEE6E         # hud_text: ... adds r0, r5, #0; bl scopy
HUD_TEXT, STATE = 0x08FDED00, 0x0203A660
GET_ABILITY, ITS_ROUTINE, ITS_TABLE_LIT = 0x0806B694, 0x09D73A80, 0x09D73A94
NAMES_HEADER = 0x080001C0


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)
    ldr_value = lambda a: u32(((a + 4) & ~3) + (struct.unpack_from("<H", rom, o(a))[0] & 0xFF) * 4)

    # the game's own lookup, and the table it indexes
    assert at(GET_ABILITY, "004b1847") and u32(GET_ABILITY + 4) == ITS_ROUTINE | 1, "GetAbilityBySpecies is not the hack's trampoline"
    assert at(ITS_ROUTINE, "03225043034b41184900c85a"), "the hack's ability lookup changed"    # table[3 * species + slot]
    abilities = u32(ITS_TABLE_LIT)
    assert 0x08000000 <= abilities < 0x0A000000 and 0x08000000 <= u32(NAMES_HEADER) < 0x0A000000

    # the search's code as dexnavchain built it
    assert at(BASESTATS, "00b51c214843") and at(SCOPY, "10b50024102c"), "basestats / scopy moved"
    assert at(SLOT_BL - 2, "6088") and at(SLOT_BL + 4, "817dc27d002a05d08a4203d0"), "reroll's ability roll changed"
    assert bl_target(rom, SLOT_BL) == BASESTATS, "reroll does not call basestats (already applied?)"
    assert at(NAME_BL - 22, "6088") and bl_target(rom, NAME_BL - 20) == BASESTATS, "hud_text's ability line changed"
    assert at(NAME_BL - 16, "e1794018807d0d214843") and at(NAME_BL - 4, "4118281c"), "hud_text's ability line changed"
    assert ldr_value(NAME_BL - 6) == u32(NAMES_HEADER), "the bar's ability names are not the header's"
    assert bl_target(rom, NAME_BL) == SCOPY, "hud_text's ability line does not call scopy (already applied?)"
    assert at(HUD_TEXT, "f0b5") and ldr_value(HUD_TEXT + 2) == STATE, "the search's state moved"

    def assemble(pairs):
        src = open(os.path.join(HERE, "dexnavabil.s"), encoding="ascii").read()
        for k, v in (("ABILITIES_ADDR", abilities), ("ONE_ADDR", pairs - 22), ("TWO_ADDR", pairs - 20),
                     ("STATE_ADDR", STATE), ("SCOPY_ADDR", SCOPY | 1)):
            src = src.replace(k, "0x%08X" % v)
        return SM.thumb(src, BASE)

    code, _ = assemble(BASE)
    pairs = BASE + ((len(code) + 3) & ~3)
    code2, dis = assemble(pairs)
    assert len(code2) == len(code)
    funcs = [i.address for i in dis if i.mnemonic == "push" and "lr" in i.op_str]
    assert len(funcs) == 2, "expected slots_hook and name_hook, found %d" % len(funcs)
    slots_hook, name_hook = funcs
    blob = bytearray(code2) + b"\x00" * (pairs - BASE - len(code2)) + bytes((1, 0, 1, 2))
    end = FREE + len(blob)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = blob

    rom[o(SLOT_BL):o(SLOT_BL) + 4] = bl(SLOT_BL, slots_hook)
    rom[o(NAME_BL):o(NAME_BL) + 4] = bl(NAME_BL, name_hook)
    open(outp, "wb").write(rom)
    print("slots_hook %08X (reroll's call %08X, was basestats), name_hook %08X (hud_text's call %08X, was scopy); "
          "abilities %08X; end %08X" % (slots_hook, SLOT_BL, name_hook, NAME_BL, abilities, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
