"""A different random sequence on every power-on (Hyper Emerald v5.7). Apply after rbutton and daynight.
usage: python rngseed_patch.py <in.gba> <out.gba>

Pokemon Emerald never seeds its random number generator: gRngValue (0x03005D80) is 0 at power-on and the game steps
it once a frame (VBlankIntr) and whenever it needs a number (Random 0x0806F5CC, which also counts the steps in
sRandCount 0x020249C0). Everything random - a static or wild Pokemon's nature, IVs, shininess and ability, a
battle's hits and misses - is therefore set by how many frames have passed since the power switch. Every soft reset
starts the count again from zero, so resetting for a static Pokemon (Rayquaza and the other legends) samples the
same short stretch of the same sequence over and over, and whatever is not in that stretch cannot come up.
(pret/pokeemerald has the fix behind BUGFIX: seed from the RTC in AgbMain.)

The patch: AgbMain's `bl RtcInit` (0x080003DA) calls rng_seed instead (rngseed.s, at 0x08FF7320), which runs
RtcInit and then sets gRngValue from the cartridge clock - date and time to the second, hashed - so each power-on
starts at a different place. On a cartridge or emulator without a clock the game's default date is read and the
start is fixed, as before. Nothing else changes: the RNG still steps once a frame and per use. A save state still
brings back the RNG it was made with (that is the emulator restoring everything).

The bl reaches only 4 MB, so it goes through an 8-byte veneer in the dead body of ButtonMode_DrawChoices
(0x080BB030; rbutton put a trampoline at the function's head, 0x080BB028, and nothing else enters it).
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import sinnohmap_patch as SM                    # the Thumb check

FREE, FREE_END = 0x00FF7320, 0x00FF7700         # after daynight (..0x08FF7316), in the unreferenced 0xFF run
CALL = 0x000003DA                               # AgbMain: bl RtcInit
RTCINIT = 0x0802F21C
VENEER = 0x000BB030                             # ButtonMode_DrawChoices' dead body, after rbutton's trampoline


def bl(site, target):
    off = target - (site + 4)
    assert abs(off) < 0x400000 and off % 2 == 0
    return struct.pack("<HH", 0xF000 | ((off >> 12) & 0x7FF), 0xF800 | ((off >> 1) & 0x7FF))


def build(inp, outp):
    with open(inp, "rb") as f:
        rom = bytearray(f.read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    at = lambda o, hexs: bytes(rom[o:o + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert bytes(rom[CALL:CALL + 4]) == bl(0x08000000 + CALL, RTCINIT), "AgbMain does not call RtcInit there"
    assert at(0x0002F21C, "30b50a4d00202880") and at(0x0002F288, "10b5021c05480188"), "RtcInit / RtcGetInfo moved"
    assert at(0x0006F5CC, "064a11680648484306494018"), "Random is not the game's LCG"
    assert at(VENEER - 8, "004b1847"), "rbutton's trampoline is not at ButtonMode_DrawChoices"
    assert at(VENEER, "0006000e69460022"), "ButtonMode_DrawChoices' body is not the dead original"

    with open(os.path.join(HERE, "rngseed.s"), encoding="ascii") as f:
        src = f.read()
    base = 0x08000000 + FREE
    code, dis = SM.thumb(src, base)
    words = {int(w, 16) for w in re.findall(r"\.word\s+(0x[0-9A-Fa-f]+)", src)}
    for i in dis:                               # each pc-relative load must land on one of the literals
        if i.mnemonic == "ldr" and "pc" in i.op_str:
            t = ((i.address + 4) & ~3) + (int(i.op_str.split("#")[1].rstrip("]"), 16) if "#" in i.op_str else 0) - base
            assert struct.unpack_from("<I", code, t)[0] in words, "a load misses its literal"
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not base <= v < 0x08000000 + end, "%08X already points into the target" % (0x08000000 + k)
    rom[FREE:end] = code
    rom[VENEER:VENEER + 8] = bytes.fromhex("004b1847") + struct.pack("<I", base | 1)
    rom[CALL:CALL + 4] = bl(0x08000000 + CALL, 0x08000000 + VENEER)
    with open(outp, "wb") as f:
        f.write(rom)
    print("rngseed: rng_seed %08X..%08X, veneer %08X, AgbMain's call at %08X" % (base, 0x08000000 + end,
                                                                                 0x08000000 + VENEER, 0x08000000 + CALL))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
