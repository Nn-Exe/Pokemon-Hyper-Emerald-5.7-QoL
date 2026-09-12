"""Add an R-button auto-run toggle to Hyper Emerald v5.7 (apply on top of the QuickBall build).
usage: python autorun_patch.py <in.gba> <out.gba>
"""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD9960                     # after QuickBall (ends 0xFD9944)
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def asm(src, addr):
    code, n = ks.asm(src, addr)
    return bytes(code)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE"
    code = asm(open(os.path.join(HERE, "autorun.s"), encoding="ascii").read(), BASE)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    bad = [i for i in md.disasm(code, BASE) if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    end = FREE + len(code)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = code
    # hook 1: run decision block 0x808AF70..0x808AFAF -> ldr r0,[pc,#0x38]; bx r0 ; ... ; .word run_hook|1 @0x808AFAC
    assert rom[0x8AF70:0x8AF78] == bytes.fromhex("02200640002e1bd0"), "run decision block not vanilla"
    assert struct.unpack_from("<I", rom, 0x8AFAC)[0] == 0x02037350
    blk = asm("ldr r0, [pc, #0x38]\n bx r0", 0x0808AF70)
    rom[0x8AF70:0x8AF70 + len(blk)] = blk
    rom[0x8AF74:0x8AFAC] = b"\xc0\x46" * ((0x8AFAC - 0x8AF74) // 2)   # nops
    struct.pack_into("<I", rom, 0x8AFAC, BASE | 1)
    # hook 2: ProcessPlayerFieldInput entry
    assert rom[0x9C014:0x9C01C] == bytes.fromhex("70b582b0051c4e48"), "ProcessPlayerFieldInput head not vanilla"
    # r0 is the function argument (input struct ptr) -> trampoline must use a scratch register: ldr r3,[pc,#0]; bx r3
    rom[0x9C014:0x9C01C] = bytes.fromhex("004b1847") + struct.pack("<I", (BASE + 2) | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, end %08X" % (len(code), BASE, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
