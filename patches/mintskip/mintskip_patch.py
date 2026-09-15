"""Skip the Mint quiz (Hyper Emerald v5.7). Apply after the gfxfix build.
usage: python mintskip_patch.py <in.gba> <out.gba>

The Gym Leader from Unova in the Rustboro Trainer's School (map 11/4, object 7 at (6,3)) hands out Galar Mints
that change a Pokemon's nature, but only after you answer a run of random true/false questions. His script:

    0984AB8D  lock; faceplayer
    0984AB8F  compare VAR_4001, 15          <- quiz progress
    0984AB94  goto_if EQ -> 0984A658        <- the Mint offer
    0984AB9A  compare VAR_4001, 1
    0984AB9F  call_if NE -> 098472F3        (first-time introduction)
    0984ABA5  msgbox "Next is a series of true/false questions..." (yes/no)
    0984ABB2  goto_if EQ -> 0984A69C        (declined)
    0984ABB8  call 09847302                 <- the quiz itself
    0984ABBD  compare VAR_4001, 15
    0984ABC2  goto_if EQ -> 0984A658        <- the Mint offer again
    0984ABC8  release; end

This patch replaces the first compare+goto_if (11 bytes) with an unconditional `goto 0984A658` plus padding, so
talking to him always opens "Do you need a Mint?" -> pick a nature -> pick a Pokemon -> done, and it stays
repeatable. The quiz branch is simply never reached any more; nothing else in the script changes, the Mint flow
itself is the hack's own, and no save data or code is touched (11 bytes of script data in the hack's own region).
"""
import struct, sys

SCRIPT = 0x184AB8F                      # file offset of `compare VAR_4001, 15`
MINT_OFFER = 0x0984A658
OLD = bytes.fromhex("21014 00f000601 58a68409".replace(" ", ""))   # compare VAR_4001,15 ; goto_if EQ, 0984A658
GOTO = 0x05
NOP = 0x00


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert rom[SCRIPT - 2:SCRIPT] == bytes((0x6A, 0x5A)), "script does not start with lock; faceplayer"
    assert rom[SCRIPT:SCRIPT + len(OLD)] == OLD, "quiz gate is not the expected compare+goto_if"
    assert struct.unpack_from("<I", rom, SCRIPT + 7)[0] == MINT_OFFER, "gate does not jump to the Mint offer"
    new = bytes((GOTO,)) + struct.pack("<I", MINT_OFFER) + bytes((NOP,)) * (len(OLD) - 5)
    rom[SCRIPT:SCRIPT + len(OLD)] = new
    open(outp, "wb").write(rom)
    print("wrote %s: Mint quiz gate at %08X replaced with goto %08X (%d bytes)" % (
        outp, 0x08000000 + SCRIPT, MINT_OFFER, len(OLD)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
