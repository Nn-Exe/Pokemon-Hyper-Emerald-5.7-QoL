"""The key-item ring's sprites (patches/keyring), drawn here: a 32x32 box for a registered item, the same box greyed
for an empty direction, and a 64x64 centre - a small PC in a box, four arrows pointing at the boxes and an A-button
badge. One 16-colour palette for all three. `python art.py out.png` writes a preview."""
import struct, sys

RGB = [(0, 0, 0), (248, 248, 248), (80, 128, 216), (40, 64, 144), (208, 208, 216), (152, 152, 160), (88, 88, 96),
       (24, 24, 32), (64, 160, 232), (168, 216, 248), (224, 56, 48), (48, 48, 56), (32, 40, 72)]
T, WHITE, BLUE, DKBLUE, LTGREY, GREY, DKGREY, BLACK, SCREEN, SCREEN_LT, RED, BADGE, SHADOW = range(13)


def rounded_box(px, x0, y0, x1, y1, outline, border, fill, shadow=None):
    def inside(x, y, a0, b0, a1, b1, r):
        if x < a0 or x > a1 or y < b0 or y > b1:
            return False
        cx = a0 + r if x < a0 + r else (a1 - r if x > a1 - r else x)
        cy = b0 + r if y < b0 + r else (b1 - r if y > b1 - r else y)
        return (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r
    for y in range(len(px)):
        for x in range(len(px[0])):
            if shadow is not None and inside(x - 1, y - 1, x0, y0, x1, y1, 4) and not inside(x, y, x0, y0, x1, y1, 4):
                px[y][x] = shadow
            if inside(x, y, x0, y0, x1, y1, 4):
                px[y][x] = outline
            if inside(x, y, x0 + 1, y0 + 1, x1 - 1, y1 - 1, 3):
                px[y][x] = border
            if inside(x, y, x0 + 3, y0 + 3, x1 - 3, y1 - 3, 2):
                px[y][x] = fill


def box(empty=False):
    px = [[T] * 32 for _ in range(32)]
    if empty:
        rounded_box(px, 1, 1, 29, 29, DKGREY, GREY, LTGREY, SHADOW)
    else:
        rounded_box(px, 1, 1, 29, 29, DKBLUE, BLUE, WHITE, SHADOW)
    return px


def centre(blocked=False):
    px = [[T] * 64 for _ in range(64)]
    rounded_box(px, 18, 18, 45, 45, DKBLUE, BLUE, WHITE, SHADOW)

    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px[y][x] = c
    # the PC: a monitor on a stand, a Poke Ball on its screen
    rect(22, 22, 41, 37, BLACK)
    rect(23, 23, 40, 36, GREY)
    rect(23, 23, 40, 23, LTGREY)
    rect(25, 25, 38, 34, BLACK)
    rect(26, 26, 37, 33, SCREEN)
    rect(26, 26, 30, 27, SCREEN_LT)
    for y in range(27, 33):                         # the ball, 6x6
        for x in range(29, 35):
            dx, dy = x - 31.5, y - 29.5
            if dx * dx + dy * dy <= 9.5:
                px[y][x] = RED if y < 30 else WHITE
                if y == 30 or dx * dx + dy * dy > 6.5:
                    px[y][x] = BLACK
    px[30][31] = px[30][32] = WHITE
    rect(29, 38, 34, 39, DKGREY)
    rect(26, 40, 37, 41, BLACK)
    rect(27, 40, 36, 40, DKGREY)
    if blocked:                                     # a red cross over the PC, dark-edged
        for y in range(20, 44):
            for x in range(20, 44):
                dx, dy = x - 31.5, y - 31.5
                d = min(abs(dx - dy), abs(dx + dy))
                if d <= 2.2:
                    px[y][x] = RED
                elif d <= 3.6:
                    px[y][x] = BLACK
    # the four arrows, white with a dark outline, between the centre and the boxes
    for k in range(5):
        for d in range(-k, k + 1):
            for (x, y) in ((31 + d, 9 + k), (32 + d, 9 + k), (31 + d, 54 - k), (32 + d, 54 - k),
                           (9 + k, 31 + d), (9 + k, 32 + d), (54 - k, 31 + d), (54 - k, 32 + d)):
                px[y][x] = DKBLUE if abs(d) == k or k == 4 else WHITE
    # the A badge, bottom right of the box
    for y in range(64):
        for x in range(64):
            dx, dy = x - 44.5, y - 44.5
            if dx * dx + dy * dy <= 42:
                px[y][x] = BLACK if dx * dx + dy * dy > 30 else BADGE
    for (x, y) in ((44, 41), (45, 41), (43, 42), (46, 42), (43, 43), (46, 43), (43, 44), (44, 44), (45, 44), (46, 44),
                   (43, 45), (46, 45), (43, 46), (46, 46), (43, 47), (46, 47)):
        px[y][x] = WHITE
    return px


def tiles(px):
    """1D-mapped 4bpp tiles, row of tiles by row of tiles."""
    h, w = len(px), len(px[0])
    out = bytearray()
    for ty in range(h // 8):
        for tx in range(w // 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[ty * 8 + y][tx * 8 + x] | (px[ty * 8 + y][tx * 8 + x + 1] << 4))
    return bytes(out)


def palette():
    c = [(r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10) for r, g, b in RGB]
    return struct.pack("<16H", *(c + [0] * (16 - len(c))))


if __name__ == "__main__":
    from PIL import Image
    im = Image.new("RGB", (32 * 2 + 64 * 2 + 24, 64), (60, 150, 60))
    for ox, p in ((0, box()), (40, box(True)), (80, centre()), (152, centre(True))):
        for y in range(len(p)):
            for x in range(len(p[0])):
                if p[y][x]:
                    im.putpixel((ox + x, y), RGB[p[y][x]])
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else "preview.png")
