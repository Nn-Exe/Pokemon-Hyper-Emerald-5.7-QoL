"""Add START-button bag sorting to a Hyper Emerald v5.7 ROM (any build).
usage: python bagsort_patch.py <in.gba> <out.gba>
Hook: Task_BagMenu_HandleInput 0x081ABD84 (literal pool 0x1ABDB4 -> hook addr, ldrh -> bx r0).
New code + strings land at FREE (verified 0xFF and unreferenced in all builds)."""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD8C00                     # file offset for new code
BASE = 0x08000000 + FREE
POOL = 0x1ABDB4
HOOK_INSN = 0x1ABD86
STRINGS = ["Sorted by type.", "Sorted by name.", "Sorted by amount."]


def enc(s):
    out = bytearray()
    for c in s:
        if 'A' <= c <= 'Z': out.append(0xBB + ord(c) - 65)
        elif 'a' <= c <= 'z': out.append(0xD5 + ord(c) - 97)
        elif '0' <= c <= '9': out.append(0xA1 + ord(c) - 48)
        elif c == ' ': out.append(0x00)
        elif c == '.': out.append(0xAD)
        else: raise ValueError(c)
    out.append(0xFF)
    return bytes(out)


def assemble(strtab_addr):
    src = open(os.path.join(HERE, "bagsort.s")).read().replace("STRTAB_ADDR", "0x%08X" % strtab_addr)
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    code, n = ks.asm(src, BASE)
    return bytes(code)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE"
    assert struct.unpack_from("<I", rom, POOL)[0] == 0x030022C0, "hook pool not vanilla (already patched?)"
    assert struct.unpack_from("<H", rom, HOOK_INSN)[0] == 0x8DC1, "hook insn not vanilla"
    code = assemble(BASE)                       # pass 1: learn size
    size = (len(code) + 3) & ~3
    strtab = BASE + size
    strs = [enc(s) for s in STRINGS]
    ptrs = []
    off = strtab + 4 * len(strs)
    for s in strs:
        ptrs.append(off)
        off += len(s)
    code = assemble(strtab)                     # pass 2: real string table address
    assert (len(code) + 3) & ~3 == size
    blob = bytearray(code) + b"\0" * (size - len(code))
    for p in ptrs:
        blob += struct.pack("<I", p)
    for s in strs:
        blob += s
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    struct.pack_into("<I", rom, POOL, BASE | 1)
    struct.pack_into("<H", rom, HOOK_INSN, 0x4700)  # bx r0
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, strings @%08X, end %08X" % (len(code), BASE, strtab, 0x08000000 + end))
    return BASE, len(code), strtab


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
