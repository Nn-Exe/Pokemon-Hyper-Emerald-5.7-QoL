"""Gold healthbox: fade with the rest of the screen (Hyper Emerald v5.7). Apply after shinybox (anywhere later).
usage: python shinyfade_patch.py <in.gba> <out.gba>

shinybox (in the v1.4 base ROM) repaints every shiny Pokemon's healthbox each battle frame, and its paint wrote
the 16 gold colours into palette RAM and both palette buffers each time. The game's fades work in those buffers,
so every frame of a fade was undone for that one palette: the gold box stayed at full brightness while the screen
went to black around it - on the way into the Bag or the party, and when a battle ends.
shiny_boxes' `bl paint` (0x08FDA15E, its only caller) now goes to paint2 (shinyfade.s): the gold stays in the
unfaded buffer, and goes into the faded one only while the stock healthbox palette is shown unfaded too. Nothing
else in the blob changes; the old paint stays where it is, unused.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavseen"))
import sinnohmap_patch as SM                    # the Thumb check
from dexnavseen_patch import bl, bl_target

FREE = 0x00FF7640                               # in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, after dexnavabil
FREE_END = 0x00FF7700                           # (..0x08FF7634); a data word happens to read 0x08FF7703
BASE = 0x08000000 + FREE

PAINT_BL, PAINT = 0x08FDA15E, 0x08FDA188        # shiny_boxes: sb_apply: bl paint
GOLDPAL_LIT = 0x08FDA1C4                        # shinybox's first literal: its gold palette


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    # shinybox as it was built
    assert at(PAINT, "30b5a1880905090d3203"), "shinybox's paint moved"         # push {r4,r5,lr}; ldrh r1,[r4,#4]; ...
    assert at(PAINT_BL - 2, "3e1c"), "shiny_boxes changed"                      # sb_gold: adds r6, r7, #0
    assert bl_target(rom, PAINT_BL) == PAINT, "shiny_boxes does not call paint (already applied?)"
    calls = []
    for k in range(0x00FDA0B0, 0x00FDA1C4, 2):
        x, y = struct.unpack_from("<HH", rom, k)
        if x & 0xF800 == 0xF000 and y & 0xF800 == 0xF800 and bl_target(rom, 0x08000000 + k) == PAINT:
            calls.append(0x08000000 + k)
    assert calls == [PAINT_BL], "paint has other callers: %s" % ["%08X" % c for c in calls]
    assert at(GOLDPAL_LIT - 2, "1847"), "shinybox's pool moved"                 # callr3: bx r3
    goldpal = u32(GOLDPAL_LIT)
    assert 0x08000000 <= goldpal < 0x0A000000 and u32(GOLDPAL_LIT + 4) == 0x080069C1, "shinybox's literals changed"

    src = open(os.path.join(HERE, "shinyfade.s"), encoding="ascii").read().replace("GOLDPAL_ADDR", "0x%08X" % goldpal)
    code, dis = SM.thumb(src, BASE)
    funcs = [i.address for i in dis if i.mnemonic == "push" and "lr" in i.op_str]
    assert len(funcs) == 2 and funcs[0] == BASE, "expected paint2 and gold_into"
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code
    rom[o(PAINT_BL):o(PAINT_BL) + 4] = bl(PAINT_BL, BASE)
    open(outp, "wb").write(rom)
    print("paint2 %08X..%08X (shiny_boxes' call %08X, was paint %08X); gold palette %08X"
          % (BASE, 0x08000000 + end, PAINT_BL, PAINT, goldpal))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
