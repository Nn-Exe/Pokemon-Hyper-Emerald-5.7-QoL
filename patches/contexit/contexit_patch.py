"""Continue no longer walks you off a tile that only looks like a door (Hyper Emerald v5.7). Apply after paulgift,
before kitakami (anywhere in the chain works: no other step touches these bytes).
usage: python contexit_patch.py <in.gba> <out.gba>

A report (2026-10-21): "I entered the Petalburg Woods and saved my game (didn't take a single step). I reloaded the
save, now I'm stuck inside of a tree." The woods' ways in from Route 104 are two tiles deep: the warps (26,43)/(27,43)
and (36,43)/(37,43) on the map's last row, and above each a second row with the same behaviour, 0x6E (deep south
warp), and no warp. Coming in you land on the warp and the game walks you one step up, onto that second row. A tap
on Left there turns you against the trees without a step. Save, Continue: you stand inside the tree at (25,42),
height 1 among tiles of height 3, and cannot move at all (_testrun/woods: steps_woods.lua with TURN=LEFT).

Why: after Continue the game's field callback is FieldCB_FadeTryShowMapPopup (0x08086204), which ends in
FieldCB_WarpExitFadeFromBlack (0x080AF3C8) and so in SetUpWarpExitTask (0x080AF334), the routine that takes you
out of a door after a warp. Standing on a non-animated door / water door / deep south warp it makes
Task_ExitNonAnimDoor: one step the way you face, as a forced movement, through walls and trees. Vanilla's maps
never let you stand on such a tile (only the warp you came by is one, and the game walks you off it), so after
Continue it never did anything; vanilla's Petalburg Woods is drawn differently. This hack's maps have 163 such
tiles with no warp that can be stood on (_testrun/woods/scan_doors.py: the woods' four, Rustboro, the Trick
House's rooms, Hisui, ...); the hack's own ROM has the same woods. Facing up the step lands on the path
(26,41), so most saves there only moved one tile.

What this does (contexit.s): CB2_ContinueSavedGame's literal for that callback (0x08086314 = 0x08086205; no other
word of the ROM holds it) points to cont_cb, which does what the callback did - the map's name, music, the fade in,
the field locked - but makes SetUpWarpExitTask's task only when one of the map's warp events is on your tile, and
Task_ExitNonDoor (no step) otherwise. Warps themselves never come here (they use FieldCB_DefaultWarpExit).
Code: 0x08FFA100.. (0x08FFA100..0x08FFA200 kept), inside the blank run 0x08FF9838..0x08FFD5A0 after wilditem: blank
in the hack's own ROM too, and no word anywhere in the game reads as an address inside 0x08FFA0F8..0x08FFA400 at
any byte offset (the nearest below: 0x08FFA0F7, at 0x080F2C5D, an odd address in code; the patcher checks its own
window again; iconnight takes 0x08FFA200..0x08FFA300). Read watchpoints on the game without it:
_testrun/space/contexit_watch.ps1.
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

FREE, FREE_END = 0x00FFA100, 0x00FFA200
BASE = 0x08000000 + FREE
LIT, LIT_WAS = 0x08086314, 0x08086205            # CB2_ContinueSavedGame: gFieldCallback = FieldCB_FadeTryShowMapPopup
EXPECT = [
    # CB2_ContinueSavedGame's end: ldr r0, =gFieldCallback; ldr r1, =<LIT>; str r1, [r0]; ...; CB2_ReturnToField
    (0x080862F8, "0548064901600648fff7c2fd"),
    # FieldCB_FadeTryShowMapPopup: the map's name (showMapName, SecretBaseMapPopupEnabled, ShowMapNamePopup), then
    # bl FieldCB_WarpExitFadeFromBlack; its literal gMapHeader
    (0x08086204, "00b50948817ef8200840082807d162f043ff0006000e012801d14ef0e1fa29f0d1f801bc0047000018730302"),
    # FieldCB_WarpExitFadeFromBlack: OnTrainerHillEReaderChallengeFloor, Overworld_PlaySpecialMapMusic,
    # FadeInFromBlack, SetUpWarpExitTask, LockPlayerFieldControls
    (0x080AF3C8, "00b527f1b3f8002801d1d6f7d7f9fff763fefff7abffe9f739fd01bc0047"),
    # SetUpWarpExitTask: PlayerGetDestCoords, MapGridGetMetatileBehaviorAt, IsDoor -> Task_ExitDoor, IsNonAnimDoor
    # -> Task_ExitNonAnimDoor, else Task_ExitNonDoor (0x080AF611), CreateTask(func, 10)
    (0x080AF334, "10b581b06c4602346846211cdcf7b4fb68460021405e0022a15ed8f7b5ff0006040e201cd9f7d0fd0006000e012803d1"
                 "00490ae039f40a08201cd9f7f3fd0006000e0649012800d10549081c0a21f9f715fe01b010bc01bc0047000011f60a08"
                 "51f50a08"),
    # PlayerGetDestCoords: gObjectEvents[gPlayerAvatar.objectEventId].currentCoords
    (0x0808BAAC, "30b5094d094c6379da00d21892005219128a02806279d000801880004019408a088030bc01bc0047507303029075"
                 "0302"),
    (0x080AF610, "30b50006050e0649a8004019c0004418"),       # Task_ExitNonDoor (FreezeObjectEvents, ...)
]


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
    return code


def assemble():
    src = open(os.path.join(HERE, "contexit.s"), encoding="ascii").read()
    for pad in ("", "    mov r8, r8"):       # the pool on a word without the assembler's own (Thumb-2) padding
        try:
            return thumb(src.replace("PADA", pad), BASE)
        except AssertionError as e:
            if "nop" not in str(e):
                raise
    raise AssertionError("contexit's pool")


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    for a, hexs in EXPECT:
        assert bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs), \
            "the game's code at %08X is not as expected" % a
    lit = struct.unpack_from("<I", rom, o(LIT))[0]
    assert lit == LIT_WAS, "CB2_ContinueSavedGame's callback literal is %08X (already applied?)" % lit
    held = [0x08000000 + m.start() for m in re.finditer(re.escape(struct.pack("<I", LIT_WAS)), bytes(rom))]
    assert held == [LIT], "the callback's address is held elsewhere too: %s" % ["%08X" % a for a in held]

    code = assemble()
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:FREE_END]) == {0xFF}, "target region not free"
    for m in re.finditer(rb"(?s).[\xa0-\xa1]\xff\x08", bytes(rom)):     # at any byte offset, not only words
        v = struct.unpack_from("<I", rom, m.start())[0]
        assert not BASE <= v < 0x08000000 + FREE_END, "%08X reads as an address in the target (%08X)" % (
            0x08000000 + m.start(), v)
    rom[FREE:end] = code
    struct.pack_into("<I", rom, o(LIT), BASE | 1)
    open(outp, "wb").write(rom)
    print("contexit: %08X..%08X, Continue's field callback at %08X" % (BASE, 0x08000000 + end, LIT))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
