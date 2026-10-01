"""Repel prompt fixes (Hyper Emerald v5.7). Apply after lrepel (anywhere after it in the chain).
usage: python repelfix_patch.py <in.gba> <out.gba>

When a repel runs out, UpdateRepelCounter (0x080B5870) runs the hack's script 0x083D7700: lock, and if the bag still
has that repel, the yes/no "The Repel ended... Use another?" at 0x083D7720. Two flaws in it:

* No: the subroutine `end`s - the whole script stops before the parent's `release`, so the people on screen stay
  frozen until they scroll away. The No path now reads `release; end` (two bytes in the padding behind it).
* Yes: `callnative 0x083D7781; end` starts the bag's repel task (ItemUseOutOfBattle_Repel) and ends the script,
  which hands the controls back while the task waits for the spray sound: the player walks a few steps with no
  repel before it is applied (a wild battle can start in between). The Yes path is now a script that does it all
  while the player is still locked: callnative use_repel (repelfix.s: VarSet + RemoveUsedItem); playse SE_REPEL;
  message "{PLAYER} used the {STR_VAR_2}." (gText_PlayerUsedVar2, which waits for a press itself); waitmessage;
  waitse; release; end. The L quick repel's Yes path (lrepel, 0x08FD9AE8) used the same callnative and now goes
  to the same script.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import sinnohmap_patch as SM                    # the Thumb check

FREE = 0x00FF7200                               # in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, after keyring's
FREE_END = 0x00FF7700                           # code (..0x08FF717C); a data word happens to read 0x08FF7703
BASE = 0x08000000 + FREE

PROMPT = 0x083D7700                             # lock; checkitem 0x800E,1; call_if >= 0x083D7720; call sign; release
YESNO = 0x083D7720                              # loadword; callstd 5; closemessage; compare; goto_if_eq YES; end
NO_END = 0x083D7734
YES = 0x083D7760                                # callnative 0x083D7781; end
LREPEL = 0x08FD9AD4                             # the L quick repel's script
LREPEL_YES = 0x08FD9AE8
TEXT = 0x085E9080                               # "{PLAYER} used the\n{STR_VAR_2}.{PAUSE_UNTIL_PRESS}"
SE_REPEL = 0x2F


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert u32(0x080B58C0) == PROMPT, "UpdateRepelCounter does not run the prompt script"
    assert at(PROMPT, "6a470e800100" "210d800100" "0704" + struct.pack("<I", YESNO).hex() +
              "04" + struct.pack("<I", 0x082A4B2A).hex() + "6c02"), "the prompt script moved"
    assert at(YESNO, "0f00" + struct.pack("<I", 0x083D7740).hex() + "0905" "68" "210d800100" "0601" +
              struct.pack("<I", YES).hex() + "02"), "the yes/no subroutine moved"
    assert NO_END == YESNO + 20 and set(rom[o(NO_END) + 1:o(0x083D7740)]) == {0}, "no padding behind the No path"
    assert at(YES, "23" + struct.pack("<I", 0x083D7781).hex() + "02") and set(rom[o(YES) + 6:o(0x083D7780)]) == {0}
    assert at(LREPEL, "6a0f00" + struct.pack("<I", 0x08FD9AF0).hex() + "0905" "210d800000" "0601" +
              struct.pack("<I", 0x08FD9AEE).hex() + "23" + struct.pack("<I", 0x083D7781).hex() + "02" "6c02"), \
        "the L quick repel's script is not the one expected"
    assert at(TEXT, "fd0100e9e7d9d800e8dcd9fefd03adfc09ff"), "gText_PlayerUsedVar2 moved"
    for a, head in ((0x080D7500, "10b50004000c064c"), (0x0809D6B0, "10b50004000c0904"), (0x080FE058, "10b5104c2088")):
        assert at(a, head), "%08X is not the expected function" % a
    for a in (NO_END + 1, YES + 6):             # nothing jumps into the bytes about to be used
        for k in range(0, len(rom), 4):
            assert u32(0x08000000 + k) != a, "%08X points at %08X" % (0x08000000 + k, a)

    src = open(os.path.join(HERE, "repelfix.s"), encoding="ascii").read()
    code, dis = SM.thumb(src, BASE)
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code

    rom[o(NO_END):o(NO_END) + 2] = b"\x6c\x02"                                     # release; end
    yes = (b"\x23" + struct.pack("<I", BASE | 1) +                                 # callnative use_repel
           bytes([0x2F, SE_REPEL, 0]) +                                            # playse SE_REPEL
           b"\x67" + struct.pack("<I", TEXT) +                                     # message
           b"\x66\x30\x6c\x02")                                                    # waitmessage; waitse; release; end
    assert YES + len(yes) <= 0x083D7780
    rom[o(YES):o(YES) + len(yes)] = yes
    rom[o(LREPEL_YES):o(LREPEL_YES) + 5] = b"\x05" + struct.pack("<I", YES)        # goto the same script
    open(outp, "wb").write(rom)
    print("use_repel %08X..%08X; No path %08X: release; Yes script %08X (%d bytes); L repel Yes %08X -> goto" % (
        BASE, 0x08000000 + end, NO_END, YES, len(yes), LREPEL_YES))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
