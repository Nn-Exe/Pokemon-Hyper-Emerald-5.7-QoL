"""Reading the game's own pictures out of a Hyper Emerald ROM, for people.py (the drawings start from them).

load(path) first. The map sprites come from the main sprite table (0x08505620: a pointer to a 0x24-byte info per
sprite: palette tag, size, frames), the trainer pictures from the hack's picture and palette tables as the hack
left them (0x0901BE90 and 0x0901C660, 8 bytes an entry; Area Zero and Kitakami copy them longer, but these bytes
stay as they were).
"""
import struct

ROM = b""
GFX_PTRS = 0x08505620
TRAINER_PICS, TRAINER_PALS = 0x0101BE90, 0x0101C660
OBJ_PAL_REF = 0x0008E8BC                   # the word of code that holds the field palette table's address


def load(path):
    global ROM
    ROM = open(path, "rb").read()
    assert ROM[0xAC:0xB0] == b"BPEE", "%s is not Hyper Emerald" % path


def u16(o): return struct.unpack_from("<H", ROM, o)[0]
def u32(o): return struct.unpack_from("<I", ROM, o)[0]
def off(p): return p - 0x08000000


def lz77(o):
    assert ROM[o] == 0x10, hex(o)
    size = ROM[o + 1] | ROM[o + 2] << 8 | ROM[o + 3] << 16
    out = bytearray()
    o += 4
    while len(out) < size:
        flags = ROM[o]
        o += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = ROM[o], ROM[o + 1]
                o += 2
                n, d = (b1 >> 4) + 3, ((b1 & 15) << 8 | b2) + 1
                for _ in range(n):
                    out.append(out[-d])
            else:
                out.append(ROM[o])
                o += 1
    return bytes(out)


def pal(data):
    return [((v & 31) << 3, (v >> 5 & 31) << 3, (v >> 10 & 31) << 3) for v in struct.unpack("<16H", data[:32])]


def indices(data, w, h):
    """4bpp tiles -> rows of colour indices"""
    px = [[0] * w for _ in range(h)]
    t = 0
    for ty in range(h // 8):
        for tx in range(w // 8):
            for y in range(8):
                for x in range(8):
                    b = data[t * 32 + y * 4 + x // 2]
                    px[ty * 8 + y][tx * 8 + x] = (b >> 4) if x & 1 else (b & 15)
            t += 1
    return px


def trainer_pic(i):
    p, q = u32(TRAINER_PICS + 8 * i), u32(TRAINER_PALS + 8 * i)
    return indices(lz77(off(p)), 64, 64), pal(lz77(off(q)))


def obj_pal(tag):
    o = off(u32(OBJ_PAL_REF))
    while True:
        p, t = u32(o), u16(o + 4)
        if t == 0x11FF:
            return None
        if t == tag:
            return pal(ROM[off(p):off(p) + 32])
        o += 8


def map_sprite(gid):
    """(the nine frames of main sprite gid as rows of indices, its colours)"""
    o = off(u32(off(GFX_PTRS) + 4 * gid))
    tag, w, h, images = u16(o + 2), u16(o + 8), u16(o + 10), u32(o + 0x1C)
    frames = []
    for k in range(9):
        im = off(images) + 8 * k
        data, size = u32(im), u16(im + 4)
        assert size == w * h // 2 == 0x100, "sprite %d is not 16x32" % gid
        frames.append(indices(ROM[off(data):off(data) + size], w, h))
    return frames, obj_pal(tag)


def image(px, colours):
    """rows of indices -> an RGBA picture (index 0 see-through)"""
    from PIL import Image
    h, w = len(px), len(px[0])
    im = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            c = px[y][x]
            im.putpixel((x, y), (0, 0, 0, 0) if c == 0 else tuple(colours[c]) + (255,))
    return im
