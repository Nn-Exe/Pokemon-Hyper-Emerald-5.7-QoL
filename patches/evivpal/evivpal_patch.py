"""EV-IV Display: every picture in its own colours (Hyper Emerald v5.7). Apply anywhere.
usage: python evivpal_patch.py <in.gba> <out.gba>

A bug of the hack's own, in the untouched ROM too. On the EV-IV Display (item 650) the D-pad goes from one party
Pokemon to the next, and some came up in the colours of the one before. The screen makes the new picture first and
lets the old picture's task remove the old one afterwards, and it asked the game for the palette by tag. The
hack's palette tables (0x08F25520, shiny 0x08F27AA0; 8 bytes a species, the tag at +4) give species 1-439 their
own number and all 760 after that tag 1 or tag 0 (shiny 501 / 500). LoadSpritePalette does not load a tag that is
loaded, so from one Pokemon past No. 439 to another with the same tag - or from Bulbasaur - the picture kept the
colours of the last one.
The routine that makes the picture (0x0968A6C0..0x0968A743, one caller, no pointer to it) is rewritten in place
(evivpal.s): it passes a palette slot and no tag, alternating 15 and 14, so the two pictures that exist for a
moment each have their own. Nothing else in the ROM changes; the tables are left as they are.
"""
import hashlib, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavseen"))
import sinnohmap_patch as SM                    # the Thumb check
from dexnavseen_patch import bl_target

PIC, PIC_END = 0x0968A6C0, 0x0968A744           # the routine with its literals; the next routine starts at the end
PIC_SHA1 = "d6cfdc80a91fc7134ae0fb3362edfa78ce84757d"
CALLER = 0x0968A750                             # the display's "show this Pokemon": bl pic
STATE, SLIDE_TASK = 0x0203FFF0, 0x09689590
CREATE_PIC, PRESERVE = 0x0818D7D8, 0x080AC3F8   # CreateMonPicSprite_HandleDeoxys, PreservePaletteInWeather


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert hashlib.sha1(rom[o(PIC):o(PIC_END)]).hexdigest() == PIC_SHA1, "the display's picture routine is not the hack's (already applied?)"
    assert bl_target(rom, CALLER) == PIC and at(PIC_END, "5823f0b5"), "the routine's caller or its neighbour changed"
    for k in range(0, len(rom) - 4, 2):
        x, y = struct.unpack_from("<HH", rom, k)
        if x & 0xF800 == 0xF000 and y & 0xF800 == 0xF800 and PIC <= bl_target(rom, 0x08000000 + k) < PIC_END:
            assert 0x08000000 + k == CALLER or PIC <= 0x08000000 + k < PIC_END, "%08X calls into the routine too" % (0x08000000 + k)
    for k in range(0, len(rom), 4):
        assert not PIC <= struct.unpack_from("<I", rom, k)[0] < PIC_END + 1, "%08X points into the routine" % (0x08000000 + k)
    assert at(CREATE_PIC, "f0b5474680b485b0") and at(PRESERVE, "30b5041c2406240e"), "the game's picture routines moved"
    # what the new code reads: the state pointer, +4 the slide task (the task that task[+0xC] is the sprite of)
    assert u32(0x0968A7B0) == STATE and at(0x0968A770, "3871") and u32(0x0968A7B8) == SLIDE_TASK | 1, "the display's state changed"   # strb r0, [r7, #4]
    assert at(0x0968A79E, "9481"), "the slide task does not keep its sprite in data[2]"          # strh r4, [r2, #0xc]

    src = open(os.path.join(HERE, "evivpal.s"), encoding="ascii").read()
    code, dis = SM.thumb(src, PIC)
    assert len(code) <= PIC_END - PIC, "the new routine is %d bytes, the old one %d" % (len(code), PIC_END - PIC)
    pad = PIC_END - PIC - len(code)
    assert pad % 2 == 0
    rom[o(PIC):o(PIC_END)] = code + bytes.fromhex("c046") * (pad // 2)      # mov r8, r8: never reached
    open(outp, "wb").write(rom)
    print("pic %08X..%08X rewritten in place (%d bytes, %d of padding); called from %08X"
          % (PIC, PIC_END, len(code), pad, CALLER))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
