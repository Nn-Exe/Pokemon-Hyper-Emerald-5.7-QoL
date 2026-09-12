"""Add R-button quick Poke Ball throw (tap = throw, hold + LEFT/RIGHT = change default ball) with a
bottom-left ball-icon + "R" badge widget to Hyper Emerald v5.7.
usage: python quickball_patch.py <in.gba> <out.gba>   (input: BagSort + MultiRegister build)
Hooks:
  0x0805758C  literal of the action-menu trampoline (hack hook 0x09D0A9E5) -> r_handler (falls through)
  0x0031C568  player controller command table [21] CONTROLLER_OPENBAG (hack wrapper 0x09D52A1D) -> quick_item
  0x0805748C  PlayerBufferExecCompleted entry -> hide_hook (hides widget, resumes original at +8)
"""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD9200                     # after MultiRegister code (ends 0xFD91DC)
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def asm(src, addr):
    code, n = ks.asm(src, addr)
    return bytes(code)


def gen3(s):
    out = bytearray()
    for c in s:
        if c == ' ': out.append(0x00)
        elif 'A' <= c <= 'Z': out.append(0xBB + ord(c) - 65)
        elif 'a' <= c <= 'z': out.append(0xD5 + ord(c) - 97)
        else: raise ValueError(c)
    return bytes(out)


def lz_literal(data):
    """GBA LZ77 stream with no back-references (valid input for LZ77UnCompWram)."""
    out = bytearray(b"\x10" + len(data).to_bytes(3, "little"))
    for i in range(0, len(data), 8):
        chunk = data[i:i + 8]
        out += b"\x00" + chunk
    return bytes(out)


badge = open(os.path.join(HERE, "rbadge.bin"), "rb").read()


def box_gfx():
    """32x32 white rounded box: color 1 outline, 3 fill (shares the badge palette)."""
    pix = [[0] * 32 for _ in range(32)]
    r = 4
    for y in range(32):
        for x in range(32):
            dx = max(r - x, x - (31 - r), 0)
            dy = max(r - y, y - (31 - r), 0)
            if dx * dx + dy * dy <= r * r:
                pix[y][x] = 3
    for y in range(32):
        for x in range(32):
            if pix[y][x] == 3:
                edge = any((ny < 0 or ny > 31 or nx < 0 or nx > 31 or pix[ny][nx] == 0)
                           for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)))
                if edge: pix[y][x] = 1
    out = bytearray()
    for ty in range(4):
        for tx in range(4):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(pix[ty * 8 + y][tx * 8 + x] | (pix[ty * 8 + y][tx * 8 + x + 1] << 4))
    return bytes(out)
RGFX, RPAL = badge[:128], badge[128:160]
DATA = [  # placeholder -> bytes (each padded to 4)
    ("LINE2_ADDR", bytes([0xF8, 0x0B]) + gen3(" change") + b"\xff"),
    ("RGFX_ADDR", RGFX),
    ("RPAL_ADDR", lz_literal(RPAL)),
    ("ROAM_ADDR", bytes.fromhex("0000004000000000")),               # 16x16 square, priority 0
    ("RTEMPLATE_ADDR", None),                                         # filled once ROAM_ADDR known
    ("BOXGFX_ADDR", box_gfx()),
    ("BOXOAM_ADDR", bytes.fromhex("0000008000000000")),               # 32x32 square, priority 0
    ("BOXTEMPLATE_ADDR", None),
]


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE"
    src0 = open(os.path.join(HERE, "quickball.s"), encoding="ascii").read()

    def layout(code_len):
        addrs = {}
        off = BASE + ((code_len + 3) & ~3)
        blobs = bytearray()
        for name, b in DATA:
            if name == "RTEMPLATE_ADDR":
                b = struct.pack("<HHIIIII", 0x5E5F, 0x5E5F, addrs["ROAM_ADDR"], 0x08614FF0, 0, 0x082EC6A8, 0x08007429)
            if name == "BOXTEMPLATE_ADDR":
                b = struct.pack("<HHIIIII", 0x5E60, 0x5E5F, addrs["BOXOAM_ADDR"], 0x08614FF0, 0, 0x082EC6A8, 0x08007429)
            addrs[name] = off
            pad = b + b"\0" * ((-len(b)) & 3)
            blobs += pad
            off += len(pad)
        return addrs, blobs

    def sub(src, addrs):
        for k, v in addrs.items():
            src = src.replace(k, "0x%08X" % v)
        return src

    code = asm(sub(src0, {k: BASE for k, _ in DATA}), BASE)
    addrs, blobs = layout(len(code))
    code2 = asm(sub(src0, addrs), BASE)
    assert len(code2) == len(code)
    blob = bytearray(code2) + b"\0" * (((len(code2) + 3) & ~3) - len(code2)) + blobs
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    # hooks
    assert struct.unpack_from("<I", rom, 0x5758C)[0] == 0x09D0A9E5, "action-menu trampoline literal unexpected"
    assert rom[0x57588:0x5758C] == bytes.fromhex("00480047")
    struct.pack_into("<I", rom, 0x5758C, BASE | 1)
    assert struct.unpack_from("<I", rom, 0x31C568)[0] == 0x09D52A1D, "controller table[21] unexpected"
    struct.pack_into("<I", rom, 0x31C568, (BASE + 2) | 1)
    assert rom[0x5748C:0x57494] == bytes.fromhex("10b581b00e490f4c"), "PlayerBufferExecCompleted head unexpected"
    rom[0x5748C:0x57494] = bytes.fromhex("00480047") + struct.pack("<I", (BASE + 4) | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X, data @%08X, end %08X" % (len(code2), BASE, addrs["LINE2_ADDR"], 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
