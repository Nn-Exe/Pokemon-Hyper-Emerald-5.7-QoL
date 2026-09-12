"""Add 4-slot key item registration (SELECT -> dpad popup) to a Hyper Emerald v5.7 ROM.
usage: python keyreg_patch.py <in.gba> <out.gba>    (input may already carry the BagSort patch)
Hooks (all verified vanilla-Emerald layout in this hack):
  0x081AD520 UseRegisteredKeyItemOnField -> replaced (entry jump)
  0x081AD20C ItemMenu_Register toggle     -> reg_toggle
  0x081AC950 context menu REGISTER/DESELECT choice -> is_registered
  0x081AB66C bag list "SELECT" marker     -> is_registered
  0x080D6EDC hack's Mach/Acro bike swap   -> bike_swap (all slots)
Storage: SB1+0x496 (vanilla) + SB1+0x9C2/0x9C4/0x9C6 (vanilla unused bytes)."""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD8E40                     # file offset for new code (after BagSort code, ends 0xFD8E22)
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def asm(src, addr):
    code, n = ks.asm(src, addr)
    return bytes(code)


def gen3(s):
    out = bytearray()
    for c in s:
        if c == '-': out.append(0xAE)
        elif c == ' ': out.append(0x00)
        elif 'A' <= c <= 'Z': out.append(0xBB + ord(c) - 65)
        elif 'a' <= c <= 'z': out.append(0xD5 + ord(c) - 97)
        else: raise ValueError(c)
    out.append(0xFF)
    return bytes(out)


DATA = [  # (placeholder, bytes) appended after code, 4-aligned each
    ("TEMPLATE_ADDR", bytes([0, 1, 1, 14, 9, 15]) + struct.pack("<H", 0x80)),  # bg0, left1, top1, 14x9, pal15, base 0x80
    ("ARROWS_ADDR", bytes([0x79, 0x7C, 0x7A, 0x7B])),                          # up right down left glyphs
    ("COLORS_ADDR", bytes([0, 2, 3, 0])),                                       # transparent bg, dark gray, light gray
    ("EMPTY_ADDR", gen3("------")),
]

# in-place snippets: addr -> (expected original bytes, replacement asm, expected end addr)
HOOKS = {
    0x1AD20C: (bytes.fromhex("07480068074a"),
               """ldr r0, [pc, #0x20]
                  bl 0x081AD214
                  b 0x081AD23A
                  bx r0
                  nop
                  nop
                  nop
                  nop
                  nop
                  nop
                  nop""", 0x1AD224),
    0x1AC950: (bytes.fromhex("134800681349"),
               """ldr r1, [pc, #0x50]
                  ldr r2, [pc, #0x54]
                  ldrh r0, [r2]
                  bl 0x081AC960
                  cmp r0, #0
                  beq 0x081AC96C
                  b 0x081AC962
                  bx r1""", 0x1AC962),
    0x1AB66C: (bytes.fromhex("0d4800680d49"),
               """ldr r1, [pc, #0x38]
                  adds r0, r6, #0
                  bl 0x081AB67C
                  cmp r0, #0
                  beq 0x081AB696
                  b 0x081AB67E
                  nop
                  bx r1""", 0x1AB67E),
}


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE"
    src0 = open(os.path.join(HERE, "keyreg.s"), encoding="utf-8").read()

    def sub(src, addrs):
        for k, v in addrs.items():
            src = src.replace(k, "0x%08X" % v)
        return src

    code = asm(sub(src0, {k: BASE for k, _ in DATA}), BASE)   # pass 1: size
    size = (len(code) + 3) & ~3
    addrs = {}
    off = BASE + size
    blob_data = bytearray()
    for name, b in DATA:
        addrs[name] = off
        pad = b + b"\0" * ((-len(b)) & 3)
        blob_data += pad
        off += len(pad)
    code = asm(sub(src0, addrs), BASE)                        # pass 2
    assert (len(code) + 3) & ~3 == size
    blob = bytearray(code) + b"\0" * (size - len(code)) + blob_data
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    syms = {"usereg": BASE, "reg_toggle": BASE + 2, "is_registered": BASE + 4, "bike_swap": BASE + 6}

    # UseRegisteredKeyItemOnField entry: ldr r0,[pc,#0] ; bx r0 ; .word usereg|1
    assert rom[0x1AD520:0x1AD522] == b"\xf0\xb5", "0x1AD520 not vanilla"
    rom[0x1AD520:0x1AD528] = bytes.fromhex("00480047") + struct.pack("<I", syms["usereg"] | 1)
    for addr, (orig, snippet, endaddr) in HOOKS.items():
        assert rom[addr:addr + len(orig)] == orig, "hook site %x not vanilla" % addr
        b = asm(snippet, 0x08000000 + addr)
        assert addr + len(b) == endaddr, "snippet size mismatch at %x (%d)" % (addr, len(b))
        rom[addr:addr + len(b)] = b
    # repurposed literal pool slots (each verified single-use)
    for pool in (0x1AD230, 0x1AC9A4, 0x1AB6A8):
        assert struct.unpack_from("<I", rom, pool)[0] == 0x496, "pool %x not vanilla" % pool
    struct.pack_into("<I", rom, 0x1AD230, syms["reg_toggle"] | 1)
    struct.pack_into("<I", rom, 0x1AC9A4, syms["is_registered"] | 1)
    struct.pack_into("<I", rom, 0x1AB6A8, syms["is_registered"] | 1)
    # bike swap fn 0x080D6EDC: ldr r0,[pc,#0] ; bx r0 ; .word bike_swap|1
    assert rom[0xD6EDC:0xD6EE0] == bytes.fromhex("00b50648"), "bike fn not vanilla"
    rom[0xD6EDC:0xD6EE4] = bytes.fromhex("00480047") + struct.pack("<I", syms["bike_swap"] | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, data @%08X, end %08X" % (len(code), BASE, addrs["TEMPLATE_ADDR"], 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
