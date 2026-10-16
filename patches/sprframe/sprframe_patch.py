"""A sprite's picture frame that does not exist is no longer copied (Hyper Emerald v5.7). Apply anywhere before
zhtext.
usage: python sprframe_patch.py <in.gba> <out.gba>

A player's report (v1.8, Pizza Boy A): "Hisui Region visual glitch - it gets fixed only after I battle a pokemon,
then again it is cooked again": the ground of Prelude Beach (37/104) in blue and green stripes, the player and
most people gone.

A bug of the hack's own. A sprite that is not drawn from a sheet gets the picture of animation frame n copied
from images[n] = {address, size} (the game's RequestSpriteFrameImageCopy 0x08007488 queues it,
ProcessSpriteCopyRequests 0x0800742C does the copies in the vertical blank with the BIOS's CpuSet). Some of the
hack's wandering wild Pokemon have a picture table shorter than the animation table they are given: the one at
sea off Prelude Beach (local id 8, graphics 78 / 0x23: record 0x0839D3EC) has 3 pictures at 0x092979F4 and the
7-frame walking table 0x085090B0. Frames 3 to 6 read what lies after the table: {0xFFFFFFFF, 0xFFFF},
{0xFFFFFFFF, 0xFFFF}, {0, 0}, {0x22BB0000, 0xB000}. A second one on the same map (local id 13, graphics 78 / 0x36,
on the sand by 25,21) reads {0x05300200, 0x0B90} and {0xE0FF28E0, 0xE039}.

Such a copy starts at the Pokemon's own picture and runs on: over every sprite's pictures after it, round the end
of sprite memory (0x06018000 - 0x0601FFFF is sprite memory again) over every sprite's pictures before it, and from
0x06020000, which is 0x06000000 again, over the first cells of the map's first tileset. The sprites heal as each
next changes its frame (people who stand still do not); the tileset is loaded once per field and stays as it is
until a battle, a menu or a door rebuilds the field.

Which of them are made depends on the BIOS: a real one (and mGBA's) refuses a CpuSet whose source starts or ends
below 0x02000000, which stops the two 0xFFFF ones and the 0xE039 one. Measured in mGBA: the 0xB000 one turns
every sprite on screen to stripes (1008 of the 1024 sprite cells changed), the 0x0B90 one copies palette memory
over the Pokemon and its neighbours (92 cells of coloured noise). An emulator with BIOS code of its own that does
not refuse makes them all, and the 65,534-byte one from sprite cell T ends 32 * T - 2 bytes into the tileset: the
report's picture is BB 00 FF 00 (what that emulator answers for memory that is not there) in the tileset's first
0xB7E bytes - cell 92 - to the byte (_testrun/tornadus: forensic.py, simulate.py, inverse.py, ticks.py).
Seven of Hisui's wandering Pokemon are like this (_testrun/sprframe/survey.py): 37/103 local 15, 37/104 locals 8
and 13, 37/105 locals 4, 6 and 15, 37/106 local 6.

The fix: the 8 bytes of ProcessSpriteCopyRequests that load the size and call CpuSet (0x08007454) jump to a guard
(sprframe.s) that makes the copy only if the address is in RAM or the ROM (0x02, 0x03, 0x08, 0x09), the size is
1 to 0x1000 bytes and the copy ends inside sprite memory; anything else is dropped and the sprite keeps the
picture it had (those Pokemon glide in a standing picture, which is all they have). Every real picture in the
game passes: the largest is 64 x 64, 0x800 bytes.
Code: 60 bytes at 0x08FEFA20, in the unreferenced 0xFF run after roamfix (0x08FEF758..0x08FEFE00).
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

PROCESS = 0x0800742C                            # ProcessSpriteCopyRequests
PROCESS_WAS = bytes.fromhex("f0b51348007800281ed0")   # push {r4-r7, lr}; ldr r0, =flag; ldrb r0, [r0]; cmp r0, #0; beq
SITE = 0x08007454                               # ldrh r2, [r2, #8]; lsrs r2, r2, #1; bl CpuSet (0x082E7084)
SITE_WAS = bytes.fromhex("12895208dff214fe")
BACK = 0x0800745D                               # ldrb r1, [r5]: the request is counted off
CPUSET, CPUSET_WAS = 0x082E7084, bytes.fromhex("0bdf7047")   # swi 0x0B; bx lr
REQUESTS = 0x02021838                           # sSpriteCopyRequests: {address, where, u16 size}, 12 bytes each
TRAMP = bytes.fromhex("004b1847")               # ldr r3, [pc, #0]; bx r3; .word   (0x08007454 is on a word)
FREE, FREE_END = 0x00FEFA20, 0x00FEFAE0         # (words in graphics data happen to read 0x08FEFA07 and 0x08FEFAF0)
SHORT_TABLE = 0x092979F4                        # the picture table the report came from: 3 pictures, then not


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


def assemble(base):
    src = open(os.path.join(HERE, "sprframe.s"), encoding="ascii").read()
    for pad in ("", "    mov r8, r8"):
        code, dis = thumb(src.replace("PAD", pad).replace("BACK_ADDR", hex(BACK)), base)
        if (len(code) - 8) % 4 == 0:
            break
    else:
        raise AssertionError("sprframe's pool")
    assert struct.unpack_from("<2I", code, len(code) - 8) == (0x06018000, BACK)
    svc = [i.address for i in dis if i.mnemonic in ("svc", "swi")]
    assert len(svc) == 1 and dis[0].mnemonic == "ldrh", "expected the guard: ldrh first, one svc"
    return code, svc[0]


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, b: bytes(rom[o(a):o(a) + len(b)]) == b

    assert at(PROCESS, PROCESS_WAS), "ProcessSpriteCopyRequests is not as expected"
    assert at(SITE, SITE_WAS), "the copy in ProcessSpriteCopyRequests changed (already applied?)"
    assert at(CPUSET, CPUSET_WAS), "CpuSet is not swi 0x0B"
    assert u32(0x08007484) == REQUESTS and u32(0x08007480) == REQUESTS - 3, "the request table moved"
    # the case this was written for is still there: three pictures of 0x200 bytes, then no picture
    assert [struct.unpack_from("<IHH", rom, o(SHORT_TABLE) + 8 * k) for k in range(4)][:3] == [
        (0x09F6F998, 0x200, 0), (0x09F6FB98, 0x200, 0), (0x09F6FD98, 0x200, 0)], "the short picture table changed"
    assert u32(SHORT_TABLE + 24) == 0xFFFFFFFF, "the short picture table has a fourth picture now"

    base = 0x08000000 + FREE
    code, svc = assemble(base)
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not base <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code
    rom[o(SITE):o(SITE) + 8] = TRAMP + struct.pack("<I", base | 1)
    open(outp, "wb").write(rom)
    print("sprframe: guard %08X (the copy itself at %08X), end %08X; ProcessSpriteCopyRequests goes through it at %08X" % (
        base, svc, 0x08000000 + end, SITE))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
