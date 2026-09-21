"""Disassemble Thumb out of the ROM, resolving pc-relative literals.

    python tools/disasm.py <hex file offset> <hex byte count> [rom.gba]

Offsets are file offsets, printed as 0x08000000 + offset so they match the addresses used everywhere else
in this project. Literal loads get the word they point at appended, which is what makes a linear read of
unknown game code tractable:

    08085E5C ldr    r3, [pc, #0]               ; =08FDE4A1
"""
import struct, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

if len(sys.argv) < 3:
    sys.exit(__doc__)

rom = open(sys.argv[3] if len(sys.argv) > 3 else "rom.gba", "rb").read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
a = int(sys.argv[1], 16)
n = int(sys.argv[2], 16)
for i in md.disasm(rom[a:a + n], 0x08000000 + a):
    lit = ""
    if i.mnemonic == "ldr" and "[pc" in i.op_str and "#" in i.op_str:
        off = int(i.op_str.split("#")[1].rstrip("]"), 0)
        o = ((i.address + 4) & ~3) + off - 0x08000000
        if 0 <= o < len(rom) - 4:
            lit = "   ; =%08X" % struct.unpack_from("<I", rom, o)[0]
    print("   %08X %-6s %-24s%s" % (i.address, i.mnemonic, i.op_str, lit))
