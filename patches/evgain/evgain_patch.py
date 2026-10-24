"""EVs from battles no longer stop short of 510 (Hyper Emerald v5.7): python evgain_patch.py in.gba out.gba

Reported 2026-10-22: "Total EV sometimes stuck at 509 when I ev train my pokemon".

The battle engine's EV gain (0x09D5A880, called by getexp for each Pokemon that gets experience) adds a beaten
Pokemon's EVs one point at a time, stat by stat (HP, Attack, Defense, Speed, Sp. Atk, Sp. Def), and keeps a running
total that ends the whole routine when it reaches 510. A stat already at 252 takes no more, but the point was
counted in that running total all the same (0x09D5A9A0: `cmp r0, #0xFB; bhi` to the `adds r4, #1`). So every point
due to a full stat used up room the Pokemon did not use: with 509 in all and a Power Bracer held while Attack is at
252, the bracer's 8 Attack points "reached" 510 and the routine stopped before the Defense point the foe gave: 509
after every battle. The same without an item when a foe gives EVs in a full stat that comes before the one being
trained, and short of 509 the lost points are lost too (Attack 248 of 500 + 8 from the bracer: 4 counted twice).

The fix is the branch's target: a full stat now goes on to the next stat (0x09D5A9C0, the loop's `i++`), so the
running total is the real one. One byte, 0x09D5A9A2: 0x07 -> 0x0D. A bug of the original hack (its ROM has the
same bytes).
"""
import sys

AT = 0x01D5A9A0                         # cmp r0, #0xFB; bhi 0x09D5A9B4; add r3, sp, #0x18; adds r0, #1;
OLD = bytes.fromhex("fb2807d806ab0130")     # (then the SetMonData that adds the point, and adds r4, #1 at 0x09D5A9B4)
NEW = bytes.fromhex("fb280dd806ab0130")     # bhi 0x09D5A9C0: on to the next stat
NEXT = 0x01D5A9C0                       # ldr r3, [sp, #8]; adds r3, #1; str r3, [sp, #8]; cmp r3, #6
NEXT_BYTES = bytes.fromhex("029b0133029306")
COUNT = 0x01D5A9B4                      # adds r4, #1 (the running total)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert bytes(rom[AT:AT + len(OLD)]) == OLD, "the EV gain loop is not as expected"
    assert bytes(rom[NEXT:NEXT + len(NEXT_BYTES)]) == NEXT_BYTES, "the EV gain's next-stat step is not as expected"
    assert bytes(rom[COUNT:COUNT + 2]) == bytes.fromhex("0134")
    rom[AT:AT + len(NEW)] = NEW
    open(outp, "wb").write(rom)
    print("EV gain: a full stat goes on to the next stat (0x%08X: bhi -> 0x%08X)" % (0x08000000 + AT + 2,
                                                                                   0x08000000 + NEXT))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
