"""The Pokedex stats panel's art (patches/dexstats): a 256x64 frame - four 64x64 sprites, the first 8 columns off
screen to the left - laid over the INFO page's description box (screen x 4..235, y 94..157): a white rounded box with
a navy title strip; the game prints the text and draws the bars over it. `python art.py out.png` writes a preview
with sample stats drawn the way dexstats.s draws them."""
import os, struct, sys

T, WHITE, BLUE, DKBLUE, LTGREY, GREY, DKGREY, BLACK, SHADOW, TRACK, C_RED, C_ORANGE, C_YELLOW, C_GREEN, C_TEAL, \
    BADGE = range(16)
RGB = [(0, 0, 0), (248, 248, 248), (80, 128, 216), (40, 64, 144), (208, 208, 216), (152, 152, 160), (88, 88, 96),
       (24, 24, 32), (32, 40, 72), (220, 224, 232), (232, 72, 64), (240, 144, 48), (224, 196, 40), (88, 184, 72),
       (48, 168, 200), (48, 48, 56)]
W, H = 256, 64
LEFT = 8                        # the art's column 0 is screen x -8
BOX = (LEFT + 4, 0, LEFT + 235, 63)     # the frame, in art pixels (screen x 4..235, the panel's rows 0..63)
TITLE = (4, 14)                 # the navy strip's rows
# where dexstats.s prints and draws (art pixels): the title, then two columns of three rows
TITLE_X, TOTAL_RIGHT, TEXT_Y = LEFT + 10, LEFT + 228, 3
ROWS_Y = (19, 33, 47)           # each row's text top
COLS_X = (LEFT + 10, LEFT + 122)    # each column's label
NUM_RIGHT = 44                  # the number's right edge, from the label
BAR_X, BAR_W, BAR_Y, BAR_H = 48, 60, 3, 6   # the bar, from the label; its top below the row's text top; height
BAR_FULL = 200                  # a stat of this or more fills the bar
# the bar's colour by the stat (the first limit it is below): red, orange, yellow, green, teal
BANDS = ((50, C_RED), (80, C_ORANGE), (110, C_YELLOW), (140, C_GREEN), (256, C_TEAL))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "keyring"))
import importlib.util
_spec = importlib.util.spec_from_file_location("kr_art", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                       "..", "keyring", "art.py"))
KR = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(KR)
tiles = KR.tiles                # 1D 4bpp tiles, a row of tiles at a time: the same order as a window's pixels


def palette():
    c = [(r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10) for r, g, b in RGB]
    return struct.pack("<16H", *(c + [0] * (16 - len(c))))


# The tab, "[R] Stats", in the top-left 41x14 of a 64x32 sprite; on screen its top-left is (194, 84), where the
# INFO page's two boxes meet on the right. lmoveinfo's L tag's look: a dark pill, a white key, the letters in white.
TAB_X, TAB_Y = 194, 84
GLYPH = {  # 7 rows each
    "R": ["1110", "1001", "1001", "1110", "1010", "1001", "1001"],
    "S": ["0111", "1000", "1000", "0110", "0001", "0001", "1110"],
    "t": ["010", "010", "111", "010", "010", "010", "001"],
    "a": ["0000", "0000", "0110", "0001", "0111", "1001", "0111"],
    "s": ["0000", "0000", "0111", "1000", "0110", "0001", "1110"],
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


def tab():
    px = [[T] * 64 for _ in range(32)]
    w = 41
    for y in range(14):
        for x in range(w):
            if (x in (0, w - 1) and y in (0, 1, 12, 13)) or (x in (1, w - 2) and y in (0, 13)):
                continue
            edge = y in (0, 13) or x in (0, w - 1) or (x in (1, w - 2) and y in (1, 12))
            px[y][x] = BLACK if edge else BADGE
    for y in range(2, 12):                          # the R key
        for x in range(3, 13):
            if x in (3, 12) and y in (2, 11):
                continue
            px[y][x] = WHITE
    text(px, 6, 3, "R", DKBLUE)
    end = text(px, 16, 3, "Stats", WHITE)
    assert end <= w - 2, end
    return px


def frame():
    px = [[T] * W for _ in range(H)]
    x0, y0, x1, y1 = BOX
    KR.rounded_box(px, x0, y0, x1, y1, DKBLUE, BLUE, WHITE)
    for y in range(*TITLE):
        for x in range(x0 + 3, x1 - 2):
            px[y][x] = DKBLUE
    return px


if __name__ == "__main__":
    from PIL import Image, ImageDraw
    px = frame()
    # the bars of a sample (Charizard: 78 84 78 109 85 100), as the code draws them: a track, then the colour
    sample = (78, 84, 78, 109, 85, 100)
    for k, v in enumerate(sample):
        x = COLS_X[k // 3] + BAR_X
        y = ROWS_Y[k % 3] + BAR_Y
        n = min(v, BAR_FULL) * BAR_W // BAR_FULL
        col = next(c for lim, c in BANDS if v < lim)
        for yy in range(y, y + BAR_H):
            for xx in range(x, x + BAR_W):
                px[yy][xx] = TRACK
            for xx in range(x, x + n):
                px[yy][xx] = col
    im = Image.new("RGB", (240, 160), (90, 90, 100))
    t = tab()
    for y in range(14):
        for x in range(41):
            if t[y][x]:
                im.putpixel((TAB_X + x, TAB_Y + y), RGB[t[y][x]])
    for y in range(H):
        for x in range(LEFT, W):
            if px[y][x] and x - LEFT < 240:
                im.putpixel((x - LEFT, 94 + y), RGB[px[y][x]])
    d = ImageDraw.Draw(im)
    d.text((TITLE_X - LEFT, 94 + TEXT_Y - 1), "Base stats", fill=RGB[WHITE])
    d.text((TOTAL_RIGHT - LEFT - 50, 94 + TEXT_Y - 1), "Total 534", fill=RGB[WHITE])
    for k, (lab, v) in enumerate(zip(("HP", "Atk", "Def", "SpA", "SpD", "Spe"), sample)):
        x = COLS_X[k // 3] - LEFT
        y = 94 + ROWS_Y[k % 3]
        d.text((x, y), lab, fill=RGB[DKGREY])
        d.text((x + NUM_RIGHT - 16, y), str(v), fill=RGB[BLACK])
    im.resize((960, 640), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else "preview.png")
