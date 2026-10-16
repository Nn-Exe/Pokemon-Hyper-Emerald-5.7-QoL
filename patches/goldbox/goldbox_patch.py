"""The gold healthbox keeps its palette (Hyper Emerald v5.7). Apply after shinyfade, anywhere before zhtext.
usage: python goldbox_patch.py <in.gba> <out.gba>

A report (2026-10-13): "the shiny box sometimes still disappear". Two things were wrong with the gold healthbox
of a shiny Pokemon (shinybox, in the v1.4 base; shinyfade since 2026-10-09), both found by playing battles with
every battler shiny and looking at each box on every frame (_testrun/shinybox2):

1. The gold palette sat in a sprite palette slot that was never claimed: every frame shinybox took "the highest
   slot from 15 down whose tag is free" and painted the gold there. The game's own allocator hands out the lowest
   free slot, so the two met whenever an animation needed every slot that was left. In a double battle three are
   left (the hack keeps a ball palette per battler loaded, and our type badges take one): a move whose animation
   loads three palettes - Fire Punch, Ice Punch, ThunderPunch, Absorb, Mega Drain, Leech Seed's drain every
   turn, Thunderbolt, Thunder Wave, Razor Leaf, Sing, Poison Sting ... 52 of the first 118 moves - loaded its
   third over the gold, and every gold box on screen took that animation's colours (grey, mostly) for the two
   or three seconds it ran. In a single battle five slots are left and it does not happen.
2. A status icon on a gold box had the wrong colour: PAR green on the foe, SLP pure blue on yours. The game
   writes the colour of a battler's status icon into the palette its box is on, at index 12 + battler; the gold
   palette was written whole from the ROM every frame, so those four indexes went back to the placeholders the
   palette is stored with (blue, green, red, violet).

What this does (goldbox.s):
  * The gold slot is claimed with a tag of its own (0x5E63) while a shiny battler's box is on screen, and given
    back when none is. It is a copy of the stock healthbox palette as it is at that moment, with colour 2 gold;
    a battler's status colour is carried between the two palettes, whichever its box is on.
  * The game must never go without a palette because of ours. LoadSpritePalette and AllocSpritePalette (both
    replaced whole, same code) ask make_room when no slot is free: the type badges give up theirs first (they
    are hidden, and come back when two slots are free again), then the gold (the boxes go back to the stock
    palette). Before this an animation that wanted a fourth palette in a double battle simply did not get it.
  * typeicons' two pool words: its call to shiny_boxes goes to gold_pass, its LoadSpritePalette to ti_load.
    shinybox's shiny_boxes and paint and shinyfade's paint2 are no longer called; they stay where they are.
Code: 0x08FEE400.., in the blank run 0x08FED3C8..0x08FEF600 (the Quest Log ends 4 KB before it, objpal's
allocator starts 3 KB after it).
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

FREE, FREE_END = 0x00FEE400, 0x00FEEA00         # (words that read, by chance, as addresses just outside it: a
                                                # Chinese text zhtext replaces later reads 0x08FEE20B, sound data
                                                # 0x08FEEA03)
BASE = 0x08000000 + FREE
GOLDTAG, TITAG, GOLDCOLOUR = 0x5E63, 0x5E62, 0x1F5F
OAM_BUFFER = 0x030022F8                         # gMain (0x030022C0) + 0x38: what LoadOam (0x08007188) copies to OAM
SHINY_ODDS = 8

# the game's allocator, as it is in the hack's own ROM too
LOADPAL, LOADPAL_WAS = 0x08008744, "30b5051ca88800f05bf80006040eff2c"
ALLOCPAL, ALLOCPAL_WAS = 0x080087D4, "10b50004040c064800f012f80006020e"
INDEXOF, INDEXOF_WAS = 0x08008804, "00b50004020c064801780f2911d8054b"
DOLOAD, DOLOAD_WAS = 0x080087BC, "00b5090480225204891809 0c202299f0b5f8".replace(" ", "")
TRAMP = bytes.fromhex("004b1847")               # ldr r3, [pc, #0]; bx r3; .word   (both functions start on a word)
# typeicons (in the v1.4 base): its pool
TI_SHINYBOXES, SHINYBOXES = 0x08FDAB5C, 0x08FDA0C3
TI_LOADPAL = 0x08FDAB74
TI_TAG, TI_BADGECB, BADGECB = 0x08FDAB7C, 0x08FDAB80, 0x08FDA9CB
BOX_PAL = 0x08C11B9C                            # the stock healthbox palette (tag 0xD6FF)


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (
        addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    assert not [i for i in dis if i.mnemonic == "nop"], "a Thumb-2 nop (00 BF) slipped in: use mov r8, r8"
    return code, dis


def assemble():
    src = open(os.path.join(HERE, "goldbox.s"), encoding="ascii").read()
    for name, value in (("GOLDTAG", GOLDTAG), ("TITAG", TITAG), ("GOLDCOLOUR", GOLDCOLOUR), ("OAM_BUFFER", OAM_BUFFER),
                        ("BADGECB", BADGECB), ("SHINY_ODDS", SHINY_ODDS)):
        src = re.sub(r"\b%s\b" % name, "0x%X" % value, src)
    # each pool is on a word: PADA / PADB / PADC are nothing or one mov r8, r8 (the assembler's own padding
    # would be the Thumb-2 nop the check below refuses)
    for pads in range(8):
        s = src
        for k, name in enumerate(("PADA", "PADB", "PADC")):
            s = s.replace(name, "    mov r8, r8" if pads >> k & 1 else "")
        try:
            code, dis = thumb(s, BASE)
            break
        except AssertionError as e:
            if "nop" not in str(e):
                raise
    else:
        raise AssertionError("goldbox's pools")
    # the four entries: four branches, to four functions that begin with a push
    heads = dis[:4]
    assert [i.mnemonic for i in heads] == ["b"] * 4, "expected the four entries first"
    targets = [int(i.op_str.lstrip("#"), 16) for i in heads]
    at = {i.address: i for i in dis}
    assert all(at[t].mnemonic == "push" and "lr" in at[t].op_str for t in targets), "an entry does not reach a function"
    assert len(set(targets)) == 4 and targets[0] == BASE + 8
    return code, targets


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert at(LOADPAL, LOADPAL_WAS), "LoadSpritePalette is not as expected (already applied?)"
    assert at(ALLOCPAL, ALLOCPAL_WAS), "AllocSpritePalette is not as expected"
    assert at(INDEXOF, INDEXOF_WAS), "IndexOfSpritePaletteTag is not as expected"
    assert at(DOLOAD, DOLOAD_WAS), "DoLoadSpritePalette is not as expected"
    assert u32(0x08008780) == 0x0000FFFF and u32(0x08008784) == 0x03000CF0, "LoadSpritePalette's pool"
    assert u32(0x08008824) == 0x0300301C and u32(0x08008828) == 0x03000CF0, "IndexOfSpritePaletteTag's pool"
    # the battle frame: BattleMainCB2 -> shinybox's stub -> typeicons' entry -> (shiny_boxes, badges)
    assert at(0x08038420, "004b1847b1a0fd08"), "BattleMainCB2 does not go through shinybox's stub"
    assert at(0x08FDA0B0, "00b581b0444b00f084f800f07ffc434b1847f0b5"), "shinybox's stub is not as typeicons left it"
    assert u32(TI_SHINYBOXES) == SHINYBOXES, "typeicons does not call shiny_boxes (already applied?)"
    assert u32(TI_LOADPAL) == LOADPAL | 1, "typeicons' LoadSpritePalette word moved"
    assert u32(TI_TAG) == TITAG and u32(TI_BADGECB) == BADGECB, "typeicons' tag or badge callback moved"
    assert at(BADGECB & ~1, "7047"), "typeicons' badge_cb is not bx lr"
    # LoadOam: gMain + 0x38 is the buffer the vertical blank copies to OAM
    assert at(0x0800719A, "101c3830e021c904") and u32(0x080071AC) == 0x030022C0 and OAM_BUFFER == 0x030022C0 + 0x38, "LoadOam"
    # the palette the gold is made from: colour 2 is the box fill (white), 12-15 the status placeholders
    pal = struct.unpack_from("<16H", rom, o(BOX_PAL))
    assert pal[2] == 0x7FFF and pal[12:16] == (0x7C00, 0x03E0, 0x001F, 0x7E4D), "the healthbox palette changed"

    code, (gold_pass, load_pal, alloc_pal, ti_load) = assemble()
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:FREE_END]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + FREE_END, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code
    struct.pack_into("<I", rom, o(TI_SHINYBOXES), BASE | 1)            # entry_gold
    struct.pack_into("<I", rom, o(TI_LOADPAL), (BASE + 6) | 1)         # entry_ti
    rom[o(LOADPAL):o(LOADPAL) + 8] = TRAMP + struct.pack("<I", (BASE + 2) | 1)      # entry_load
    rom[o(ALLOCPAL):o(ALLOCPAL) + 8] = TRAMP + struct.pack("<I", (BASE + 4) | 1)    # entry_alloc
    open(outp, "wb").write(rom)
    print("goldbox: %08X..%08X (gold_pass %08X, LoadSpritePalette %08X, AllocSpritePalette %08X, ti_load %08X); "
          "gold tag %04X" % (BASE, 0x08000000 + end, gold_pass, load_pal, alloc_pal, ti_load, GOLDTAG))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
