"""Draw the Oval Charm's Bag icon from the Shiny Charm's (item 119): same string, bead and tassel, with the
star gem replaced by an oval, egg-shaped one in warm colours. ovalcharm_patch.py imports draw(), pack() and
palette(); run on its own it prints the icon's colour indices and can save an 8x preview:
    python make_icon.py <rom.gba> [preview.png]
"""
import os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))

ICONS = 0x00FCBFF4
SHINY_CHARM = 119
# 0 transparent, 1/7 string, 2..4 gem dark/mid/light, 5 bead, 6 highlight, 8 outline
PAL = [(176, 176, 176), (240, 128, 160), (184, 88, 48), (240, 160, 72), (248, 208, 136), (248, 216, 80),
       (248, 248, 232), (200, 72, 112), (48, 48, 48)] + [(0, 0, 0)] * 7
CX, CY, RX, RY = 15.5, 11.5, 4.2, 5.0       # the gem: taller than wide, like an Egg


def unlz(rom, off):
    assert rom[off] == 0x10
    n = struct.unpack_from("<I", rom, off)[0] >> 8
    out = bytearray(); i = off + 4
    while len(out) < n:
        flags = rom[i]; i += 1
        for b in range(8):
            if len(out) >= n: break
            if flags & (0x80 >> b):
                v = rom[i] << 8 | rom[i + 1]; i += 2
                cnt, disp = (v >> 12) + 3, (v & 0xFFF) + 1
                for _ in range(cnt): out.append(out[-disp])
            else:
                out.append(rom[i]); i += 1
    return bytes(out)


def grid_of(px):
    g = [[0] * 24 for _ in range(24)]
    for t in range(9):
        for y in range(8):
            for x in range(8):
                g[t // 3 * 8 + y][t % 3 * 8 + x] = (px[t * 32 + y * 4 + x // 2] >> ((x & 1) * 4)) & 15
    return g


def pack(g):
    out = bytearray()
    for t in range(9):
        for y in range(8):
            for x in range(0, 8, 2):
                out.append(g[t // 3 * 8 + y][t % 3 * 8 + x] | g[t // 3 * 8 + y][t % 3 * 8 + x + 1] << 4)
    return bytes(out)


def draw(rom):
    pic = struct.unpack_from("<I", rom, ICONS + SHINY_CHARM * 8)[0] - 0x08000000
    g = grid_of(unlz(rom, pic))
    gem = {(x, y) for y in range(24) for x in range(24) if g[y][x] in (2, 3, 4, 6)}
    # the star: its colours, and the outline pixels that only border it
    near = lambda x, y, s: any((x + dx, y + dy) in s for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    string = {(x, y) for y in range(24) for x in range(24) if g[y][x] in (1, 5, 7)}
    for y in range(24):
        for x in range(24):
            if (x, y) in gem or (g[y][x] == 8 and near(x, y, gem) and not near(x, y, string)):
                g[y][x] = 0
    for y in range(24):
        for x in range(24):
            d = ((x + 0.5 - CX) / RX) ** 2 + ((y + 0.5 - CY) / RY) ** 2
            if d <= 1:
                lx, ly = (x + 0.5 - CX) / RX, (y + 0.5 - CY) / RY       # light from the top left
                shade = lx * 0.6 + ly * 0.8
                g[y][x] = 4 if shade < -0.45 else 3 if shade < 0.35 else 2
    body = {(x, y) for y in range(24) for x in range(24) if g[y][x] in (2, 3, 4)}
    for y in range(24):                                                 # outline: whatever touches the gem
        for x in range(24):
            if (x, y) not in body and g[y][x] not in (1, 5, 7) and any(
                    (x + dx, y + dy) in body for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 8
    for x, y in ((13, 9), (14, 9), (13, 10)):                           # the shine
        g[y][x] = 6
    return g


def palette():
    return b"".join(struct.pack("<H", (r >> 3) | (gg >> 3) << 5 | (b >> 3) << 10) for r, gg, b in PAL)


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    g = draw(rom)
    for row in g: print("".join("%X" % v if v else "." for v in row))
    if len(sys.argv) > 2:
        from PIL import Image
        im = Image.new("RGB", (24, 24))
        for y in range(24):
            for x in range(24):
                im.putpixel((x, y), PAL[g[y][x]] if g[y][x] else (255, 0, 255))
        im.resize((192, 192), Image.NEAREST).save(sys.argv[2])
