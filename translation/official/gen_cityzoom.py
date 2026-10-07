"""patches/zhtext/cityzoom.lz: the labels of the PokeNav's zoomed city maps ("POKeMON CENTER", "POKe MART", "POKeMON
GYM", "BATTLE TENT", "POKeMON CONTEST") as Emerald has them - graphics/pokenav/region_map/city_zoom_text.png from the
pret source, as 4bpp tiles, LZ77-compressed the way the GBA BIOS reads it.   python gen_cityzoom.py <outdir>"""
import os, sys
from PIL import Image
import vanilla as V

PNG = os.path.join(V.SRC, "graphics", "pokenav", "region_map", "city_zoom_text.png")


def tiles(path):
    im = Image.open(path)
    assert im.mode == "P" and im.size == (64, 64)
    px, out = im.load(), bytearray()
    for t in range(64):
        tx, ty = (t % 8) * 8, (t // 8) * 8
        for y in range(8):
            for x in range(0, 8, 2):
                out.append((px[tx + x, ty + y] & 15) | ((px[tx + x + 1, ty + y] & 15) << 4))
    return bytes(out)


def lz77(data):
    """greedy LZ77 (type 0x10): matches of 3..18 bytes, distance 2..4096 (distance 1 is unsafe for VRAM targets)"""
    out = bytearray([0x10, len(data) & 0xFF, (len(data) >> 8) & 0xFF, (len(data) >> 16) & 0xFF])
    i, n = 0, len(data)
    while i < n:
        flags, chunk = 0, bytearray()
        for bit in range(8):
            if i >= n:
                break
            best, dist = 0, 0
            for j in range(max(0, i - 4096), i - 1):
                k = 0
                while k < 18 and i + k < n and data[j + k] == data[i + k]:
                    k += 1
                if k > best:
                    best, dist = k, i - j
                    if k == 18:
                        break
            if best >= 3:
                flags |= 0x80 >> bit
                chunk += bytes([((best - 3) << 4) | ((dist - 1) >> 8), (dist - 1) & 0xFF])
                i += best
            else:
                chunk.append(data[i])
                i += 1
        out.append(flags)
        out += chunk
    return bytes(out)


def unlz(b):
    n = b[1] | (b[2] << 8) | (b[3] << 16)
    out, i = bytearray(), 4
    while len(out) < n:
        f = b[i]; i += 1
        for bit in range(8):
            if len(out) >= n:
                break
            if f & (0x80 >> bit):
                v = (b[i] << 8) | b[i + 1]; i += 2
                for _ in range((v >> 12) + 3):
                    out.append(out[-((v & 0xFFF) + 1)])
            else:
                out.append(b[i]); i += 1
    return bytes(out)


if __name__ == "__main__":
    raw = tiles(PNG)
    comp = lz77(raw)
    assert unlz(comp) == raw
    with open(os.path.join(sys.argv[1], "cityzoom.lz"), "wb") as f:
        f.write(comp)
    print("cityzoom.lz: %d bytes of tiles -> %d compressed" % (len(raw), len(comp)))
