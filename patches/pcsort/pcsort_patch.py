"""PC item storage sort (Hyper Emerald v5.7). Apply after the statcolor patch.
usage: python pcsort_patch.py <in.gba> <out.gba>
Hook: ItemStorage_ProcessInput 0x0816C30C - pool literal @0x16C354 (&gMain) -> hook|1, ldrh @0x16C31E -> bx r0.
Code in free space; no data or save-format changes (the sort reorders the existing 50 PC item slots in place)."""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD9D60                     # after the statcolor blob (ends 0xFD9D50)
BASE = 0x08000000 + FREE
POOL = 0x16C354
HOOK_INSN = 0x16C31E


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE"
    assert struct.unpack_from("<I", rom, POOL)[0] == 0x030022C0, "hook pool not vanilla (already patched?)"
    assert struct.unpack_from("<H", rom, HOOK_INSN)[0] == 0x8DC1, "hook insn not vanilla (ldrh r1,[r0,#0x2e])"
    assert rom[0x16C39E:0x16C3A4] == bytes.fromhex("70bc01bc0047"), "epilogue bytes unexpected"
    assert rom[0x16C320:0x16C324] == bytes.fromhex("04200840"), "resume bytes unexpected"
    src = open(os.path.join(HERE, "pcsort.s"), encoding="ascii").read()
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    code = bytes(ks.asm(src, BASE)[0])
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    bad = [i for i in md.disasm(code, BASE) if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    end = FREE + len(code)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = code
    struct.pack_into("<I", rom, POOL, BASE | 1)
    struct.pack_into("<H", rom, HOOK_INSN, 0x4700)      # bx r0
    open(outp, "wb").write(rom)
    print("pcsort code %d bytes @%08X..%08X" % (len(code), BASE, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
