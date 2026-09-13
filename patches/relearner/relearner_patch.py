"""In-party move relearner (Hyper Emerald v5.7). Apply after the second text pass (patch_remaining.py).
usage: python relearner_patch.py <in.gba> <out.gba>
Changes: (1) copy of the 33-entry party-menu action table + new entry 33 {"Moves", cursor_moves} in free space,
the three code literals that point at the table repointed; (2) the CANCEL append at 0x081B3518 replaced by a
trampoline into builder_hook; (3) code + text in free space. Nothing else is touched."""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD9B00                     # after L-repel (ends 0xFD9AFB)
BASE = 0x08000000 + FREE
TABLE = 0x615C08                      # sCursorOptions (33 entries of {text ptr, func ptr})
TABLE_LITERALS = (0x1B32F8, 0x1B37C8, 0x1B37F8)
HOOK = 0x1B3518                       # ldr r0,=internal ... movs r2,#2 ; bl AppendToList  (16 bytes)
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def gen3(s):
    out = bytearray()
    for c in s:
        if 'A' <= c <= 'Z': out.append(0xBB + ord(c) - 65)
        elif 'a' <= c <= 'z': out.append(0xD5 + ord(c) - 97)
        elif c == ' ': out.append(0)
        else: raise ValueError(c)
    out.append(0xFF)
    return bytes(out)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE"
    for lit in TABLE_LITERALS:
        assert struct.unpack_from("<I", rom, lit)[0] == 0x08000000 + TABLE, "table literal @%x unexpected" % lit
    assert rom[HOOK:HOOK + 16] == bytes.fromhex("07480168081c0f3017310222edf60efa"), "CANCEL append bytes unexpected"
    assert rom[TABLE:TABLE + 8] == struct.pack("<II", 0x085E96B6, 0x081B37FD), "table head unexpected"
    src = open(os.path.join(HERE, "relearner.s"), encoding="ascii").read()

    def assemble(cb2_addr):
        code = bytes(ks.asm(src.replace("CB2_MOVES_ADDR", "0x%08X" % cb2_addr), BASE)[0])
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        bad = [i for i in md.disasm(code, BASE) if i.size == 4 and i.mnemonic != "bl"]
        assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
        syms = {}
        for i in md.disasm(code, BASE):
            pass
        return code
    # symbol offsets: assemble label-only probes by re-assembling prefixes is clumsy; locate by instruction pattern instead
    code = assemble(BASE)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    ins = list(md.disasm(code, BASE))
    # cursor_moves starts at the first "push {r4, lr}"; cb2_moves starts at the ldr right after the "bx r0" that ends it
    cursor = next(i.address for i in ins if i.mnemonic == "push" and i.op_str == "{r4, lr}")
    bx_r0 = next(i.address for i in ins if i.address > cursor and i.mnemonic == "bx" and i.op_str == "r0")
    cb2 = bx_r0 + 2
    code = assemble(cb2 | 1)
    assert list(md.disasm(code, BASE))[0].address == BASE
    # layout: code | text | table(34 entries)
    text_off = (len(code) + 3) & ~3
    text = gen3("Moves")
    table_off = (text_off + len(text) + 3) & ~3
    table = bytes(rom[TABLE:TABLE + 33 * 8]) + struct.pack("<II", BASE + text_off, (cursor | 1))
    blob = bytearray(code) + b"\0" * (text_off - len(code)) + text + b"\0" * (table_off - text_off - len(text)) + table
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    for lit in TABLE_LITERALS:
        struct.pack_into("<I", rom, lit, BASE + table_off)
    # trampoline: ldr r3,[pc,#0] ; bx r3 ; .word builder_hook|1 ; 4x nop
    rom[HOOK:HOOK + 16] = bytes.fromhex("004b1847") + struct.pack("<I", BASE | 1) + bytes.fromhex("c046c046c046c046")
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, cursor_moves %08X, cb2_moves %08X, table @%08X, end %08X" % (len(code), BASE, cursor, cb2, BASE + table_off, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
