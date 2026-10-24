"""A fainted Pokemon stays fainted when its stats change (Hyper Emerald v5.7): python hpcalc_patch.py in.gba out.gba

Found 2026-10-22 while checking the EV items at the 510 cap (NOTES, *EVs from battles stopped at 509*).

The hack has its own CalculateMonStats (0x09F038D8, behind the trampoline at 0x08068D0C). When the max HP changes it
sets HP to HP + (new max - old max) as a u16 and anything above the new max to the new max. So a fainted Pokemon
whose max HP rises (HP Up, a Rare Candy) came back with the difference (0/293 -> 2/295), and one whose max HP falls
(a Pomeg Berry) wrapped round to full HP, fainted or at 1 HP (0/338 -> 335/335, 1/340 -> 338/338).

The game's own routine is still in the ROM behind the trampoline (0x08068FAC..0x08068FF0): a new Pokemon (old max 0)
gets the new max, a fainted one keeps 0, any other HP + (new max - old max), with no floor (Emerald's Pomeg
glitch). This patch does the same in the hack's routine, with a floor of 1 HP: the 40 bytes 0x09F03A5C..0x09F03A84,
the path taken when the max HP changes (an unchanged max keeps the HP, as before; Shedinja's max is 1 there too).
In place, in the hack's own code: no free space. A bug of the original hack (its ROM has the same bytes).
"""
import sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

AT = 0x01F03A5C
END = 0x01F03A84
# r0 = the old max HP (GetMonData 0x3A), r1 = 0x39, r2 = 0, r4 = [r7] = the new max; after: [sp+0x16] = HP, r4 points
# at it, r3 = HP, for the cap at 0x09F03A84 (newMax < HP: HP = newMax) and the SetMonData calls after it
OLD = bytes.fromhex("244b404600f054f83c8800222418214b3a21404600f04cf82404240c231a04aa"
                    "1b041b0c941d2380")
SRC = """
    adds r4, r0, #0
    ldr r3, [pc, #0x90]
    mov r0, r8
    bl #0x09F03B0C
    cmp r4, #0
    beq newmon
    cmp r0, #0
    beq store
    ldrh r3, [r7]
    adds r0, r0, r3
    subs r0, r0, r4
    bgt store
    movs r0, #1
    b store
newmon:
    ldrh r0, [r7]
store:
    add r2, sp, #0x10
    adds r4, r2, #6
    strh r0, [r4]
    adds r3, r0, #0
"""
POOL = 0x01F03AF0                    # the routine's literal for GetMonData, which `ldr r3, [pc, #0x90]` reads
CALL_R3 = 0x01F03B0C                 # bx r3
AFTER = bytes.fromhex("3a889a4200d22280")   # 0x09F03A84: ldrh r2, [r7]; cmp r2, r3; bhs; strh r2, [r4]
TRAMPOLINE = 0x00068D0C              # ldr r1, [pc, #0]; bx r1; .word 0x09F038D9


def u32(rom, a):
    return int.from_bytes(rom[a:a + 4], "little")


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert bytes(rom[TRAMPOLINE:TRAMPOLINE + 8]) == bytes.fromhex("00490847d938f009"), "CalculateMonStats is not the hack's"
    assert bytes(rom[AT:END]) == OLD, "the HP update is not as expected"
    assert bytes(rom[END:END + len(AFTER)]) == AFTER, "the HP cap is not as expected"
    assert u32(rom, POOL) == 0x0806A519, "the GetMonData literal is not where expected"
    assert bytes(rom[CALL_R3:CALL_R3 + 2]) == bytes.fromhex("1847")
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(SRC, 0x08000000 + AT)[0])
    assert len(code) == END - AT, len(code)
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, 0x08000000 + AT))
    assert sum(i.size for i in dis) == len(code)
    assert all(i.size == 2 or i.mnemonic == "bl" for i in dis), "a 32-bit instruction slipped in"
    assert [i for i in dis if i.mnemonic == "ldr"][0].op_str == "r3, [pc, #0x90]"
    rom[AT:END] = code
    open(outp, "wb").write(rom)
    print("HP on a stat change: fainted stays 0, new gets full, else HP + difference, at least 1 (0x%08X, %d bytes)"
          % (0x08000000 + AT, len(code)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
