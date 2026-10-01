"""Faster surfing: hold B while surfing (Hyper Emerald v5.7). Apply after autorun (anywhere after it in the chain).
usage: python fastsurf_patch.py <in.gba> <out.gba>

PlayerNotOnBikeMoving (0x0808AF00) sends a surfing player that is free to move to PlayerWalkFast - running speed,
8 frames a tile - whatever the keys. Its surfing branch now goes to surf_hook (fastsurf.s), which uses the Mach
Bike's PlayerWalkFaster (4 frames a tile) when B is held, or when Auto Run is on and B is not: the same rule as
running on foot. The branch is 8 bytes at a 2-aligned address, too short for a trampoline, so it becomes
`ldr r0, [pc, #0x18]; bx r0` and the literal goes into the 0x38 bytes of nops that auto-run's patch left dead in
this function (0x0808AF74.., after its own `ldr r0, =run_hook; bx r0`). Both surfing sprites (gfx 2 and 92) use
sAnimTable_Surfing 0x08509388, whose GO_FASTER animations (12-15) are there.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import sinnohmap_patch as SM                    # the Thumb check

FREE = 0x00FF6A80                               # in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, after instanttext
FREE_END = 0x00FF7700                           # (0x08FF6900..0x08FF6A32); a data word happens to read 0x08FF7703
BASE = 0x08000000 + FREE

SURF_BRANCH = 0x0808AF5A                        # adds r0, r5, #0; bl PlayerWalkFast; b 0x0808AFB6
SURF_LIT = 0x0808AF74                           # in auto-run's dead nops
AUTORUN_JUMP = 0x0808AF70                       # ldr r0, [pc, #0x38]; bx r0 -> auto-run's run_hook
SURF_GFX_STATE = 3                              # PLAYER_AVATAR_STATE_SURFING
PLAYER_GFX_IDS, GFX_INFOS, SURF_ANIMS = 0x084974F8, 0x08505620, 0x08509388


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    # ldr r4, =gPlayerAvatar; ldrb r1, [r4]; movs r0, #8 (SURFING); ands; cmp; beq -> then the branch itself
    assert at(0x0808AF4E, "054c217808200840002806d0") and u32(0x0808AF64) == 0x02037590, "the surfing test moved"
    assert at(SURF_BRANCH, "281c00f0ecfb29e0"), "the surfing branch is not `adds; bl PlayerWalkFast; b epilogue`"
    assert at(AUTORUN_JUMP, "0e480047") and u32(0x0808AFAC) == 0x08FD9961, "auto-run's hook is not in this function"
    assert at(SURF_LIT, "c046c046"), "the dead nops are gone"
    assert at(0x0808AFB6, "70bc01bc0047"), "the epilogue moved"
    # both surfing sprites have the faster walking animations
    for g in rom[o(PLAYER_GFX_IDS) + 2 * SURF_GFX_STATE:o(PLAYER_GFX_IDS) + 2 * SURF_GFX_STATE + 2]:
        anims = u32(u32(GFX_INFOS + 4 * g) + 0x18)
        assert anims == SURF_ANIMS, "surfing gfx %d has another animation table (%08X)" % (g, anims)
    assert all(0x08000000 <= u32(SURF_ANIMS + 4 * i) < 0x0A000000 for i in range(12, 16))

    src = open(os.path.join(HERE, "fastsurf.s"), encoding="ascii").read()
    code, dis = SM.thumb(src, BASE)
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code

    ldr = 0x4800 | ((SURF_LIT - ((SURF_BRANCH + 4) & ~3)) >> 2)
    rom[o(SURF_BRANCH):o(SURF_BRANCH) + 4] = struct.pack("<HH", ldr, 0x4700)     # ldr r0, =surf_hook; bx r0
    struct.pack_into("<I", rom, o(SURF_LIT), BASE | 1)
    open(outp, "wb").write(rom)
    print("surf_hook %08X..%08X, branch %08X -> literal %08X" % (BASE, 0x08000000 + end, SURF_BRANCH, SURF_LIT))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
