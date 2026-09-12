"""L button = quick repel prompt (Hyper Emerald v5.7). Apply on top of the build that has the AutoRun hook.
usage: python lrepel_patch.py <in.gba> <out.gba>
Hook: literal at 0x0809C018 (ProcessPlayerFieldInput entry trampoline, currently -> auto-run hook) -> l_hook,
which falls through to the previous hook. Script + strings + code in free space."""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD9A40                     # after AutoRun code (ends 0xFD9A1C)
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
HACK_USE_REPEL_NATIVE = 0x083D7781    # hack's own: CreateTask(ItemUseOutOfBattle_Repel, 0x50)


def gen3(s):
    cm = {' ': 0, '.': 0xAD, '?': 0xAC, '!': 0xAB, "'": 0xB4}
    out = bytearray()
    i = 0
    while i < len(s):
        if s.startswith("{STR_VAR_1}", i): out += b"\xfd\x02"; i += 11; continue
        c = s[i]
        if 'A' <= c <= 'Z': out.append(0xBB + ord(c) - 65)
        elif 'a' <= c <= 'z': out.append(0xD5 + ord(c) - 97)
        elif c in cm: out.append(cm[c])
        else: raise ValueError(c)
        i += 1
    out.append(0xFF)
    return bytes(out)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE"
    assert rom[0x9C014:0x9C018] == bytes.fromhex("004b1847"), "field-input trampoline not present (AutoRun patch missing?)"
    prev_hook = struct.unpack_from("<I", rom, 0x9C018)[0]
    assert prev_hook & 1 and 0x08F00000 < prev_hook < 0x09000000, "unexpected previous hook %08x" % prev_hook
    src = open(os.path.join(HERE, "lrepel.s"), encoding="ascii").read()
    # layout: code | repel list | script | text
    text = gen3("Use the {STR_VAR_1}?")
    def layout(code_len):
        off = BASE + ((code_len + 3) & ~3)
        repels = off; off += 8                    # 84,83,86,0 (u16)
        script = off
        # 6a lock ; 0f 00 <text> ; 09 05 ; 21 0d80 0100 ; 06 01 <no> ; 23 <native> ; 02 ; no: 6c ; 02
        s = bytearray(b"\x6a")
        s += b"\x0f\x00" + struct.pack("<I", 0)   # text ptr placeholder (patched below)
        s += b"\x09\x05"
        s += b"\x21\x0d\x80\x00\x00"           # compare VAR_RESULT, 0 (No) -> goto no-branch
        s += b"\x06\x01" + struct.pack("<I", 0)   # no-branch placeholder
        s += b"\x23" + struct.pack("<I", HACK_USE_REPEL_NATIVE)
        s += b"\x02"
        no_off = len(s)
        s += b"\x6c\x02"
        text_addr = script + ((len(s) + 3) & ~3)
        struct.pack_into("<I", s, 3, text_addr)
        struct.pack_into("<I", s, 16, script + no_off)          # goto_if ptr sits at bytes 16..19
        blob = struct.pack("<HHHH", 84, 83, 86, 0) + bytes(s) + b"\0" * (((len(s) + 3) & ~3) - len(s)) + text
        return repels, script, blob
    code = bytes(ks.asm(src.replace("REPELS_ADDR", "0x%08X" % BASE).replace("SCRIPT_ADDR", "0x%08X" % BASE).replace("NEXT_HOOK", "0x%08X" % prev_hook), BASE)[0])
    repels, script, blob = layout(len(code))
    code = bytes(ks.asm(src.replace("REPELS_ADDR", "0x%08X" % repels).replace("SCRIPT_ADDR", "0x%08X" % script).replace("NEXT_HOOK", "0x%08X" % prev_hook), BASE)[0])
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    bad = [i for i in md.disasm(code, BASE) if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    full = code + b"\0" * (((len(code) + 3) & ~3) - len(code)) + blob
    end = FREE + len(full)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = full
    struct.pack_into("<I", rom, 0x9C018, BASE | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, script @%08X, end %08X; chained -> %08X" % (len(code), BASE, script, 0x08000000 + end, prev_hook))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
