"""The Option menu's "Sound" row is the hack's EXP switch - say so (Hyper Emerald v5.7). Apply before zhtext.
usage: python expgain_patch.py <in.gba> <out.gba>

Reported: after switching Sound from Mono to Stereo no Pokemon gains experience until it is switched back.
The hack made that row its EXP switch and left Emerald's label on it:

* SetPokemonCryStereo (0x082E1810), which the row calls when it is changed and the game calls with the saved
  option when a save is loaded, is a trampoline to 0x09D45278: FlagSet(0x267) for Stereo, FlagClear(0x267) for
  Mono. It no longer touches the sound hardware at all - the row changes nothing you can hear.
* The hack's experience code skips the whole award when FlagGet(0x267) is set (0x09D5ACC0 and 0x09D5B00A, next
  to its checks of 0x276, the flag story scripts set for a battle that gives no experience).

So nothing is broken; the row only says the wrong thing. It now reads "Exp. Gain   On / Off":

* the row's name (sOptionMenuItemsNames[3], 0x0855C670) points at a new "Exp. Gain", written over the "Mono" /
  "Stereo" strings (0x085EE61D, 24 bytes, referenced by Sound_DrawChoices only);
* Sound_DrawChoices' two literals (0x080BAE54 / 58) point at the game's own "On" / "Off" (0x085EE5F4 / FD, the
  Battle Scene row's): the first choice (0, flag clear) is On, the second (1, flag set) is Off.

No code changes and nothing in the save changes: a save left on "Stereo" shows Off and still gives no experience
until it is switched On.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
from inserter import ENC

NAMES, ROW = 0x0855C664, 3                      # sOptionMenuItemsNames
OLD_LABEL = 0x085EE5B5                          # "Sound"
MONO, STEREO, STRINGS_END = 0x085EE61D, 0x085EE628, 0x085EE635
ON, OFF = 0x085EE5F4, 0x085EE5FD
DRAW_LITS = (0x080BAE54, 0x080BAE58)            # Sound_DrawChoices (0x080BAE08)
STEREO_FN, HACK_FN = 0x082E1810, 0x09D45278     # SetPokemonCryStereo -> the hack's flag routine
NO_EXP_FLAG = 0x267
EXP_LITS = (0x09D5AE6C, 0x09D5B090)             # the experience code's two `ldr r0, =0x267` words
FLAGGET, FLAGSET, FLAGCLEAR = 0x0809D791, 0x0809D741, 0x0809D769
LABEL = "Exp. Gain"
COLOR = "fc0106fc0307"                          # the colour prefix the choice strings carry


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)
    enc = lambda s: bytes(ENC[c] for c in s)

    # the row is the flag switch, and the flag is the one the experience code reads
    assert at(STEREO_FN, "00490847") and u32(STEREO_FN + 4) == HACK_FN | 1, "SetPokemonCryStereo is not the hack's"
    assert at(HACK_FN, "10b5002804d0") and u32(HACK_FN + 0x1C) == NO_EXP_FLAG and \
        u32(HACK_FN + 0x20) == FLAGSET and u32(HACK_FN + 0x24) == FLAGCLEAR, "the hack's routine is not the flag switch"
    for lit in EXP_LITS:
        assert u32(lit) == NO_EXP_FLAG, "the experience code does not read flag 0x267 at %08X" % lit
        assert FLAGGET in [u32(k) for k in range(lit - 0x40, lit + 0x40, 4)]
    # the texts
    assert u32(NAMES + 4 * ROW) == OLD_LABEL and at(OLD_LABEL, enc("Sound").hex() + "ff"), "row 3 is not Sound"
    assert at(MONO, COLOR + enc("Mono").hex() + "ff") and at(STEREO, COLOR + enc("Stereo").hex() + "ff")
    assert at(ON, COLOR + enc("On").hex() + "ff") and at(OFF, COLOR + enc("Off").hex() + "ff")
    assert (u32(DRAW_LITS[0]), u32(DRAW_LITS[1])) == (MONO, STEREO), "Sound_DrawChoices does not draw Mono / Stereo"
    for k in range(0, len(rom) - 3):            # nobody else reads the two strings
        v = struct.unpack_from("<I", rom, k)[0]
        assert not MONO <= v < STRINGS_END or 0x08000000 + k in DRAW_LITS, \
            "%08X also points at the Mono / Stereo strings" % (0x08000000 + k)

    label = enc(LABEL) + b"\xff"
    assert len(label) <= STRINGS_END - MONO
    rom[o(MONO):o(STRINGS_END)] = label + b"\xff" * (STRINGS_END - MONO - len(label))
    struct.pack_into("<I", rom, o(NAMES + 4 * ROW), MONO)
    struct.pack_into("<I", rom, o(DRAW_LITS[0]), ON)
    struct.pack_into("<I", rom, o(DRAW_LITS[1]), OFF)
    open(outp, "wb").write(rom)
    print('row %d: "Sound  Mono / Stereo" -> "%s  On / Off" (label @%08X; flag 0x%X set = Off = no experience)' % (
        ROW, LABEL, MONO, NO_EXP_FLAG))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
