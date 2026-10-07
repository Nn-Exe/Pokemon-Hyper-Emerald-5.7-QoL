"""The L move-info sprites (patches/lmoveinfo), drawn here: the 64x32 "[L] Move Info" tag (its top 14 rows) and the
128x64 panel's empty frame (a white rounded box with a navy title strip; the game prints the text over it). They
share the key-item ring's palette. `python art.py out.png` writes a preview."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "keyring"))
import art as KR                                    # the ring's palette, rounded_box and tile packer

T, WHITE, BLUE, DKBLUE, LTGREY, GREY, DKGREY, BLACK, SCREEN, SCREEN_LT, RED, BADGE, SHADOW = range(13)
RGB = KR.RGB
palette, tiles = KR.palette, KR.tiles

GLYPH = {  # 7 rows each
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "o": ["0000", "0000", "0110", "1001", "1001", "1001", "0110"],
    "v": ["00000", "00000", "10001", "10001", "01010", "01010", "00100"],
    "e": ["0000", "0000", "0110", "1001", "1111", "1000", "0111"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "n": ["0000", "0000", "1110", "1001", "1001", "1001", "1001"],
    "f": ["011", "100", "111", "100", "100", "100", "100"],
    "L": ["1000", "1000", "1000", "1000", "1000", "1000", "1111"],
    " ": ["00", "00", "00", "00", "00", "00", "00"],
}


def text(px, x, y, s, colour):
    for ch in s:
        g = GLYPH[ch]
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == "1":
                    px[y + r][x + c] = colour
        x += len(g[0]) + 1
    return x


def hud():
    """64x32; the tag is rows 0-13: a dark pill, a white L key, "Move Info" in white."""
    px = [[T] * 64 for _ in range(32)]
    w = 61
    for y in range(14):
        for x in range(w):
            corner = (x in (0, w - 1) and y in (0, 1, 12, 13)) or (x in (1, w - 2) and y in (0, 13))
            if corner:
                continue
            edge = y in (0, 13) or x in (0, w - 1) or (x in (1, w - 2) and y in (1, 12))
            px[y][x] = BLACK if edge else BADGE
    for y in range(2, 12):                          # the L key
        for x in range(3, 13):
            if (x in (3, 12)) and (y in (2, 11)):
                continue
            px[y][x] = WHITE
    text(px, 6, 3, "L", DKBLUE)
    text(px, 16, 3, "Move Info", WHITE)
    return px


def panel():
    """128x64: the frame the text goes on. Title strip rows 3-14, a divider between the two columns."""
    px = [[T] * 128 for _ in range(64)]
    KR.rounded_box(px, 1, 1, 124, 60, DKBLUE, BLUE, WHITE, SHADOW)
    for y in range(4, 16):
        for x in range(4, 122):
            px[y][x] = DKBLUE
    for y in range(19, 56):
        px[y][66] = LTGREY
    return px


if __name__ == "__main__":
    from PIL import Image
    im = Image.new("RGB", (128 + 64 + 12, 64), (60, 150, 60))
    for ox, p in ((0, panel()), (136, hud())):
        for y in range(len(p)):
            for x in range(len(p[0])):
                if p[y][x]:
                    im.putpixel((ox + x, y), RGB[p[y][x]])
    im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else "preview.png")
