"""Coloured stat names in battle messages (Hyper Emerald v5.7). Apply after the relearner patch.
usage: python statcolor_patch.py <in.gba> <out.gba>
Battle text builds "X's Attack rose!" from gStatNamesTable (0x085CBE00, 8 string pointers: HP, Attack, Defense,
Speed, Sp. Atk, Sp. Def, Accuracy, Evasiveness). This writes new copies of the 7 stat strings wrapped in text-colour
control codes (FC 01 <idx> name FC 01 01) into free space and repoints those table entries.
The battle text box palette (LZ block @0x08C004E0, 64 bytes = banks 0-1) still carries vanilla's unused blue-grey
box shades at entries 3, 4, 7, 8 (the hack's green box art uses 10-15; text is fg 1 white / shadow 6). A copy of
that palette with those four entries recoloured is placed in free space and the three battle_bg loaders
(literals @0x35AE0, 0x36430, 0x38EF8) are repointed to it; other users of the palette keep the original.
Colours: Attack red(2), Defense orange(3), Speed light green(13), Sp. Atk pink(4), Sp. Def blue(7),
Accuracy/Evasiveness yellow(8). Data only - no code changes."""
import struct, sys

FREE = 0x00FD9CA0                     # after the relearner blob (ends 0xFD9C9C)
BASE = 0x08000000 + FREE
TABLE = 0x5CBE00
NAMES = ["HP", "Attack", "Defense", "Speed", "Sp. Atk", "Sp. Def", "Accuracy", "Evasiveness"]
COLORS = {1: 2, 2: 3, 3: 13, 4: 4, 5: 7, 6: 8, 7: 8}   # stat index -> palette entry
RESTORE = 1                                            # battle message fg colour (white)
PAL_LZ = 0xC004E0
PAL_LITERALS = (0x35AE0, 0x36430, 0x38EF8)
PAL_HEAD = bytes.fromhex("0000ff7f1f008a4d2d5eff7f6d393a6b283d09294b434b434b43ee574b43693e")
NEW_ENTRIES = {3: 0x1A9F, 4: 0x69FF, 7: 0x7ECC, 8: 0x23BF}   # orange, pink, blue, yellow (BGR555)


def gen3(s):
    out = bytearray()
    for c in s:
        if 'A' <= c <= 'Z': out.append(0xBB + ord(c) - 65)
        elif 'a' <= c <= 'z': out.append(0xD5 + ord(c) - 97)
        elif c == ' ': out.append(0)
        elif c == '.': out.append(0xAD)
        else: raise ValueError(c)
    return bytes(out)


def lz_decode(src, o):
    size = struct.unpack_from('<I', src, o)[0] >> 8
    out = bytearray(); i = o + 4
    while len(out) < size:
        flags = src[i]; i += 1
        for b in range(8):
            if len(out) >= size: break
            if flags & (0x80 >> b):
                v = (src[i] << 8) | src[i + 1]; i += 2
                ln = (v >> 12) + 3; disp = (v & 0xFFF) + 1
                for _ in range(ln): out.append(out[-disp])
            else: out.append(src[i]); i += 1
    return bytes(out)


def lz_store(data):
    """LZ77 (type 0x10) container with every byte stored literally."""
    out = bytearray(struct.pack('<I', 0x10 | (len(data) << 8)))
    for i in range(0, len(data), 8):
        out.append(0); out += data[i:i + 8]
    while len(out) % 4: out.append(0)
    return bytes(out)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE"
    for k, name in enumerate(NAMES):
        p = struct.unpack_from("<I", rom, TABLE + 4 * k)[0] - 0x08000000
        assert rom[p:p + len(gen3(name)) + 1] == gen3(name) + b"\xff", "stat table entry %d is not %r" % (k, name)
    pal = lz_decode(rom, PAL_LZ)
    assert pal[:32] == PAL_HEAD, "battle textbox palette unexpected"
    for lit in PAL_LITERALS:
        assert struct.unpack_from("<I", rom, lit)[0] == 0x08000000 + PAL_LZ, "palette literal @%x unexpected" % lit
    # strings
    blob = bytearray(); ptrs = {}
    for k, idx in sorted(COLORS.items()):
        ptrs[k] = BASE + len(blob)
        blob += bytes([0xFC, 0x01, idx]) + gen3(NAMES[k]) + bytes([0xFC, 0x01, RESTORE]) + b"\xff"
    while len(blob) % 4: blob.append(0)
    # palette copy
    newpal = bytearray(pal)
    for e, v in NEW_ENTRIES.items(): struct.pack_into('<H', newpal, e * 2, v)
    pal_addr = BASE + len(blob)
    blob += lz_store(bytes(newpal))
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    for k, a in ptrs.items(): struct.pack_into("<I", rom, TABLE + 4 * k, a)
    for lit in PAL_LITERALS: struct.pack_into("<I", rom, lit, pal_addr)
    assert lz_decode(rom, pal_addr - 0x08000000) == bytes(newpal)
    open(outp, "wb").write(rom)
    print("stat strings @%08X, palette @%08X, end %08X" % (BASE, pal_addr, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
