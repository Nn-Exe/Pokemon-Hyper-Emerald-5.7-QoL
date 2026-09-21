"""Gold healthbox for shiny Pokemon on either side (Hyper Emerald v5.7). Apply after the pcanywhere build.
usage: python shinybox_patch.py <in.gba> <out.gba>

A shiny Pokemon gets a gold healthbox, like the SoulSilver style hacks: a wild one, a trainer's, and your
own (added 2026-09-21; until then the player's side was skipped).

How: the two halves of a healthbox are ordinary sprites that all share OBJ palette 4, so the colour cannot
be changed per box by editing that palette. Instead a copy of the healthbox palette, with the fill colours
turned gold, is written into a spare OBJ palette slot and a shiny battler's two box sprites are pointed at it.
The work is done once per battle frame from a hook in BattleMainCB2, so it survives the box being rebuilt
and undoes itself the moment the boxes are gone.

Facts this relies on (all verified in-game with tools/test-harness/shiny_probe*.lua):
  gSprites            0x02020630, stride 0x44; callback +0x1C, data[] +0x2E, flags +0x3E
  healthbox body      callback = SpriteCallbackDummy 0x08007429, data[5] = right half, data[6] = battler
  gBattleMons         0x02024084, stride 0x58; personality +0x48, otId +0x54
  sSpritePaletteTags  0x03000CF0 (16 entries, 0xFFFF = free); slots 10-15 are free in battle
  healthbox palette   sSpritePalettes_HealthBoxHealthBar @0x0832C128 -> 0x08C11B9C, loaded into OBJ slot 4
Only slots 8 and up are ever used: the low slots hold reserved palettes that carry no tag.
"""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FDA0B0
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

HOOK = 0x038420                       # BattleMainCB2
HOOK_EXPECT = "00b581b0cef7ccfa"      # push {lr}; sub sp,#4; bl 0x080069C0
PAL_SRC = 0xC11B9C                    # stock healthbox palette (16 colours)
PAL_EXPECT = "00002925ff7f5a67ee3508216d298410e71c9f037f4a287f007ce0031f004d7e"
GOLD = {2: 0x1F5F}                    # index 2 is the box fill; everything else stays stock
SHINY_ODDS = 8                        # the hack's own shiny threshold (vanilla value, verified in-game)


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    bad = [i for i in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, addr) if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert rom[HOOK:HOOK + 8].hex() == HOOK_EXPECT, "BattleMainCB2 prologue differs: %s" % rom[HOOK:HOOK + 8].hex()
    assert rom[PAL_SRC:PAL_SRC + 32].hex() == PAL_EXPECT, "healthbox palette differs"

    gold = bytearray(rom[PAL_SRC:PAL_SRC + 32])
    for i, colour in GOLD.items():
        struct.pack_into("<H", gold, i * 2, colour)

    src = open(os.path.join(HERE, "shinybox.s"), encoding="ascii").read()
    src = src.replace("SHINY_ODDS", str(SHINY_ODDS))
    code = thumb(src.replace("GOLDPAL_ADDR", "0x%08X" % BASE), BASE)
    code_len = (len(code) + 3) & ~3
    gold_addr = BASE + code_len
    code = thumb(src.replace("GOLDPAL_ADDR", "0x%08X" % gold_addr), BASE)
    assert (len(code) + 3) & ~3 == code_len

    blob = bytearray(code) + bytes(code_len - len(code)) + gold
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    rom[HOOK:HOOK + 4] = thumb("ldr r3, [pc, #0]\nbx r3", 0x08000000 + HOOK)
    struct.pack_into("<I", rom, HOOK + 4, BASE | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, gold palette @%08X, end %08X" % (len(code), BASE, gold_addr, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
