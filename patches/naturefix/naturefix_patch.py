"""Nature display fix (Hyper Emerald v5.7). Apply at the end of the chain.

GetNature (0x0806D070) computes `personality % 25` and ignores the hack's nature override at mon+0x1F, so
a Mint - or the party editor - moves the stats but the summary's "Nature:" line keeps showing the old
nature (verified: writing 5 = Bold left the summary on Impish, personality % 25 = 8).

This repoints the whole 24-byte GetNature at a stub that returns the non-zero override when there is one
and otherwise runs the original code. Zero stays "no override", which is what the Mint's "None" cell
writes, so untouched Pokemon display exactly as before. The Mint's list has no Quirky: its last
cell, 24, is Hardy, so 24 displays as Hardy (nature 0); both are neutral, so the stats agree.

usage: python naturefix_patch.py <in.gba> <out.gba>
"""
import os, re, struct, sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00F54200                       # in the same verified run as candynpc (partyedit is not applied here)
BASE = 0x08000000 + FREE
HOOK = 0x6D070                          # GetNature
ORIG = bytes.fromhex("00b500210022fdf74ffa19217af2b0fd0006000e02bc0847")   # 24 bytes
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 nop\n    nop", src, flags=re.M), addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code, dis


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000, "not the expected ROM"
    assert bytes(rom[HOOK:HOOK + 24]) == ORIG, "GetNature is not the function this patch expects"
    code, _ = thumb(open(os.path.join(HERE, "naturefix.s"), encoding="ascii").read(), BASE)
    end = FREE + len(code)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = code
    # ldr r3,[pc,#0] ; bx r3 ; .word hook|1 ; nops, filling all 24 original bytes
    patch = bytes.fromhex("004b1847") + struct.pack("<I", BASE | 1)
    rom[HOOK:HOOK + 24] = patch + b"\xC0\x46" * ((24 - len(patch)) // 2)
    open(outp, "wb").write(rom)
    print("GetNature -> %08X (%d bytes of stub, %d original bytes replaced)" % (BASE | 1, len(code), 24))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
