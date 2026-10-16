"""The move menu's sprite sheet is loaded once, not on every opening (Hyper Emerald v5.7). Apply anywhere
before zhtext.
usage: python sheetonce_patch.py <in.gba> <out.gba>

Found behind the gold healthbox reports (2026-10-13). A bug of the original hack, in its own untouched ROM too:
every time the move menu opens in a battle, its routine at 0x09D6077C destroys the sprite it shows there
(callback 0x09D605E1) and makes it again - DestroySprite, LoadSpritePalette, LoadCompressedSpriteSheet of one of
four 32-tile sheets (0x09D77CF4.. : tags 0x2346, 0x2345, 0x2347, 0x2348), CreateSprite. Nothing ever frees the
sheet, and LoadSpriteSheet does not look whether a tag is loaded: each opening took another 32 of the 1,024
sprite tiles. A single battle starts with about 540 free, a double one with about 430 and two menus a turn, so
after some seven turns of a double battle (seventeen of a single one) none were left, and from then on a move
animation's sheet did not fit: its sprites were drawn from tile 0 on, pieces of the healthbox in the animation's
colours (Fire Punch's flames as cream blocks, Celebrate's confetti as yellow bars).

The routine's call goes through a pool word (0x09D60848, loaded by the one instruction at 0x09D607F8); it now
points at load_once (sheetonce.s), which loads the sheet only if no sheet with that tag is loaded. Each of the
four tags has one picture, so the one already there is the right one.
Code: 48 bytes at 0x08FEE100, in the blank run 0x08FED3C8..0x08FEF600 before goldbox.
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

FREE, FREE_END = 0x00FEE100, 0x00FEE140
BASE = 0x08000000 + FREE
POOL, LOADER = 0x09D60848, 0x08034531            # the routine's word for LoadCompressedSpriteSheet
SITE = 0x09D607F8                               # ldr r3, [pc, #0x4c]; bl (bx r3)
SHEETS = 0x09D77CF4                             # four {data, u16 size, u16 tag}


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    assert not [i for i in dis if i.mnemonic == "nop"], "a Thumb-2 nop (00 BF) slipped in: use mov r8, r8"
    return code, dis


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert u32(POOL) == LOADER, "the routine's pool word is not LoadCompressedSpriteSheet (already applied?)"
    assert at(SITE, "134b00f005fa0123"), "the routine's call is not as expected"      # ldr r3; bl; movs r3, #1
    assert at(0x09D60C08, "1847"), "the routine's veneer is not bx r3"
    assert at(0x09D6077C, "f7b52b4c2078"), "the routine's start changed"
    # the one instruction that loads the word
    users = []
    for a in range(POOL - 1024, POOL, 2):
        w = struct.unpack_from("<H", rom, o(a))[0]
        if w & 0xF800 == 0x4800 and ((a + 4) & ~3) + (w & 0xFF) * 4 == POOL:
            users.append(a)
    assert users == [SITE], "the pool word has other users: %s" % ["%08X" % a for a in users]
    assert at(0x08034530, "30b582b0041c2068") and at(0x08008620, "00b5"), "the game's sheet functions changed"
    tags = [struct.unpack_from("<IHH", rom, o(SHEETS) + 8 * k) for k in range(4)]
    assert [t[1] for t in tags] == [0x400] * 4 and len({t[2] for t in tags}) == 4 and len({t[0] for t in tags}) == 4, \
        "the four sheets are not four pictures with four tags: %s" % tags

    src = open(os.path.join(HERE, "sheetonce.s"), encoding="ascii").read()
    code, dis = thumb(src, BASE)
    assert dis[0].mnemonic == "push" and struct.unpack_from("<3I", code, len(code) - 12) == (0x08008621, LOADER, 0xFFFF)
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:FREE_END]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + FREE_END, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code
    struct.pack_into("<I", rom, o(POOL), BASE | 1)
    open(outp, "wb").write(rom)
    print("sheetonce: load_once %08X..%08X; the move menu's sheets (tags %s) are loaded once (pool word %08X)" % (
        BASE, 0x08000000 + end, ", ".join("%04X" % t[2] for t in tags), POOL))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
