"""The DexNav screen's background art, drawn here and cut into GBA tiles (patches/dexnavui).

Two screens share one tile set and one 16-colour palette: screen 0 = a 5-slot box (Water) over a 6x2 box (Land),
screen 1 = a 5-slot box (Rock Smash) over a 5x2 box (Fishing). The boxes are drawn in palette entries 5-7 and 8-10,
which the screen code reloads with each habitat's colours, and the SEARCH button in 13-15 (green / red / grey).
Everything that changes - words, numbers, icons, the X of an empty slot, the cursor - is drawn over this at run
time. `python art.py out.png` writes a preview of both screens.
"""
import struct, sys

W, H = 240, 160
TOP_H = 16

# palette entries (colour 0 is the backdrop, never seen: every pixel of the art is opaque)
BACK, STRIPE_A, STRIPE_B, BLACK, WHITE = 0, 1, 2, 3, 4
BOXA, BOXA_LT, BOXA_DK = 5, 6, 7
BOXB, BOXB_LT, BOXB_DK = 8, 9, 10
RED, RED_DK = 11, 12
BTN, BTN_LT, BTN_DK = 13, 14, 15

RGB = {
    BACK: (40, 88, 192), STRIPE_A: (72, 128, 232), STRIPE_B: (48, 96, 208), BLACK: (24, 24, 32), WHITE: (248, 248, 248),
    BOXA: (56, 168, 232), BOXA_LT: (144, 216, 248), BOXA_DK: (24, 96, 168),
    BOXB: (88, 184, 56), BOXB_LT: (168, 224, 120), BOXB_DK: (40, 112, 32),
    RED: (224, 48, 48), RED_DK: (152, 24, 24),
    BTN: (72, 192, 72), BTN_LT: (152, 232, 144), BTN_DK: (32, 120, 40),
}
# the habitats' box colours (main, light, dark), loaded into 5-7 / 8-10
HABITAT = {
    "water": ((56, 168, 232), (144, 216, 248), (24, 96, 168)),
    "land": ((88, 184, 56), (168, 224, 120), (40, 112, 32)),
    "rock": ((184, 128, 64), (224, 184, 120), (112, 72, 32)),
    "fish": ((152, 96, 216), (200, 160, 240), (96, 48, 160)),
}
# the SEARCH button: can search / the one being hunted (STOP) / nothing to search
BUTTON = {
    "go": ((72, 192, 72), (152, 232, 144), (32, 120, 40)),
    "stop": ((224, 64, 48), (248, 160, 136), (144, 24, 16)),
    "off": ((152, 152, 160), (208, 208, 216), (96, 96, 104)),
}

# geometry (pixels) - the screen code uses the same numbers (the patcher passes them in)
CELL_W, CELL_H = 24, 30
BOX_X = 6
BOXA_Y = 18                  # header bar top; body below it
BOXB_Y = 66
HEAD_H = 11
BODY_A_H = 4 + CELL_H + 2    # border 2 + pad 1.. = 36
BODY_B_H = 4 + 2 * CELL_H + 2
PANEL_X, PANEL_W = 164, 72
BUTTON_Y, BUTTON_H = 17, 15
PANEL_Y = 34
# the panel's rows: (label bar top, value area top, value area height)
ROWS = [("SPECIES", 35, 46, 13), ("TYPE", 59, 70, 18), ("SEARCH LV.", 88, 99, 13), ("LEVEL", 112, 123, 13),
        ("CHAIN", 136, 147, 12)]
BAR_H = 11
PANEL_BOTTOM = 159
TAB_Y, TAB_H = 144, 14
TAB0_X0, TAB1_X0, TAB_W = BOX_X, BOX_X + 78, 74


def box_width(cols):
    return 4 + 4 + cols * CELL_W        # 2-px border each side, 2-px padding each side


def slot_centres(cols, rows, y_body):
    """Centres of the icon cells, row-major."""
    out = []
    for r in range(rows):
        for c in range(cols):
            out.append((BOX_X + 4 + CELL_W * c + CELL_W // 2, y_body + 2 + 1 + CELL_H * r + CELL_H // 2))
    return out


def layout(screen):
    """(box A cols, box B cols) and the slot centres: box A's 5, then box B's row-major."""
    b_cols = 6 if screen == 0 else 5
    a = slot_centres(5, 1, BOXA_Y + HEAD_H)
    b = slot_centres(b_cols, 2, BOXB_Y + HEAD_H)
    return 5, b_cols, a + b


def draw(screen):
    px = [[BACK] * W for _ in range(H)]

    def rect(x0, y0, x1, y1, c):            # inclusive
        for y in range(max(0, y0), min(H - 1, y1) + 1):
            for x in range(max(0, x0), min(W - 1, x1) + 1):
                px[y][x] = c

    for y in range(H):                      # the stripes: 2 rows light, 2 rows dark
        for x in range(W):
            px[y][x] = STRIPE_A if (y // 2) % 2 == 0 else STRIPE_B
    rect(0, 0, W - 1, TOP_H - 1, BLACK)     # the top bar

    def box(y_head, cols, rows, main, lt, dk):
        x0, x1 = BOX_X, BOX_X + box_width(cols) - 1
        yb = y_head + HEAD_H
        yb1 = yb + 4 + rows * CELL_H + 2 - 1
        # header bar: outline, light top line, dark bottom line, a notch of the box colour down into the body
        rect(x0, y_head, x1 - 16, y_head + HEAD_H - 1, main)
        rect(x0, y_head, x1 - 16, y_head, lt)
        rect(x0, y_head + HEAD_H - 1, x1 - 16, y_head + HEAD_H - 1, dk)
        for k in range(HEAD_H):              # a slanted end on the header
            rect(x1 - 16 + 1, y_head + k, x1 - 16 + (HEAD_H - k), y_head + k, main if 0 < k < HEAD_H - 1 else (lt if k == 0 else dk))
        # body: border 2 px, the inner white
        rect(x0, yb, x1, yb1, main)
        rect(x0, yb1, x1, yb1, dk)
        rect(x0 + 2, yb + 2, x1 - 2, yb1 - 2, WHITE)
        rect(x0 + 2, yb + 2, x1 - 2, yb + 2, lt)
        rect(x0, yb, x0, yb1, dk)
        rect(x1, yb, x1, yb1, dk)

    box(BOXA_Y, 5, 1, BOXA, BOXA_LT, BOXA_DK)
    box(BOXB_Y, 6 if screen == 0 else 5, 2, BOXB, BOXB_LT, BOXB_DK)

    # SEARCH button: a pill with a black outline
    bx0, bx1, by0, by1 = PANEL_X, PANEL_X + PANEL_W - 1, BUTTON_Y, BUTTON_Y + BUTTON_H - 1
    rect(bx0 + 2, by0, bx1 - 2, by1, BLACK)
    rect(bx0 + 1, by0 + 1, bx1 - 1, by1 - 1, BLACK)
    rect(bx0, by0 + 2, bx1, by1 - 2, BLACK)
    rect(bx0 + 2, by0 + 1, bx1 - 2, by1 - 1, BTN)
    rect(bx0 + 1, by0 + 2, bx1 - 1, by1 - 2, BTN)
    rect(bx0 + 3, by0 + 2, bx1 - 3, by0 + 3, BTN_LT)
    rect(bx0 + 2, by1 - 2, bx1 - 2, by1 - 1, BTN_DK)

    # the info panel: black outline, white inside, a red bar per label
    rect(PANEL_X, PANEL_Y, PANEL_X + PANEL_W - 1, PANEL_BOTTOM, BLACK)
    rect(PANEL_X + 1, PANEL_Y + 1, PANEL_X + PANEL_W - 2, PANEL_BOTTOM - 1, WHITE)
    for _, bar, _, _ in ROWS:
        rect(PANEL_X + 1, bar, PANEL_X + PANEL_W - 2, bar + BAR_H - 1, RED)
        rect(PANEL_X + 1, bar + BAR_H - 1, PANEL_X + PANEL_W - 2, bar + BAR_H - 1, RED_DK)

    # the two tabs, bottom left: black outline, white inside (the words are drawn by the code)
    for tx0, tx1 in ((TAB0_X0, TAB0_X0 + TAB_W - 1), (TAB1_X0, TAB1_X0 + TAB_W - 1)):
        rect(tx0 + 1, TAB_Y, tx1 - 1, TAB_Y + TAB_H - 1, BLACK)
        rect(tx0, TAB_Y + 1, tx1, TAB_Y + TAB_H - 2, BLACK)
        rect(tx0 + 1, TAB_Y + 1, tx1 - 1, TAB_Y + TAB_H - 2, WHITE)
    return px


def tiles_and_maps():
    """One tile set for both screens (deduplicated, with flips) and a 32x32 tilemap for each."""
    tiles, index, maps = [], {}, []
    for screen in (0, 1):
        px = draw(screen)
        m = [0] * (32 * 32)
        for ty in range(20):
            for tx in range(30):
                t = tuple(px[ty * 8 + y][tx * 8 + x] for y in range(8) for x in range(8))
                found = None
                for hf in (0, 1):
                    for vf in (0, 1):
                        v = tuple(t[(7 - y if vf else y) * 8 + (7 - x if hf else x)] for y in range(8) for x in range(8))
                        if v in index:
                            found = (index[v], hf, vf)
                            break
                    if found:
                        break
                if not found:
                    index[t] = len(tiles)
                    tiles.append(t)
                    found = (index[t], 0, 0)
                n, hf, vf = found
                m[ty * 32 + tx] = n | (hf << 10) | (vf << 11)          # palette 0
        maps.append(m)
    raw = bytearray()
    for t in tiles:
        for i in range(0, 64, 2):
            raw.append(t[i] | (t[i + 1] << 4))
    return bytes(raw), [struct.pack("<1024H", *m) for m in maps], len(tiles)


def bgr555(rgb):
    r, g, b = rgb
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def palette():
    return struct.pack("<16H", *[bgr555(RGB[i]) for i in range(16)])


def colours3(triple):
    return struct.pack("<3H", *[bgr555(c) for c in triple])


def x_mark():
    """16x16, 4bpp in the text palette (colour 5 = the grey of an empty slot), as rows for BlitBitmapRectToWindow."""
    px = [[0] * 16 for _ in range(16)]
    for i in range(2, 14):
        for d in (0, 1):
            for (x, y) in ((i + d, i), (15 - i - d, i)):
                if 0 <= x < 16:
                    px[y][x] = 5
    out = bytearray()
    for ty in range(2):                       # tiled layout, as windows store their pixels
        for tx in range(2):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[ty * 8 + y][tx * 8 + x] | (px[ty * 8 + y][tx * 8 + x + 1] << 4))
    return bytes(out)


def cursor_sprite():
    """32x32 ring (4bpp, 16 tiles in 1D order) and its palette: 1 red, 2 dark red, 3 white."""
    px = [[0] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            dx, dy = abs(x - 15.5), abs(y - 15.5)
            edge = max(dx, dy)
            corner = dx > 11 and dy > 11 and (dx - 11) ** 2 + (dy - 11) ** 2 > 20
            if corner:
                continue
            if 13.5 <= edge <= 15.5:
                px[y][x] = 1 if edge < 15 else 2
    out = bytearray()
    for ty in range(4):
        for tx in range(4):
            for y in range(8):
                for x in range(0, 8, 2):
                    out.append(px[ty * 8 + y][tx * 8 + x] | (px[ty * 8 + y][tx * 8 + x + 1] << 4))
    pal = struct.pack("<16H", 0, bgr555((232, 40, 40)), bgr555((136, 16, 16)), bgr555((248, 248, 248)), *([0] * 12))
    return bytes(out), pal


if __name__ == "__main__":
    from PIL import Image
    im = Image.new("RGB", (W * 2 + 8, H), (0, 0, 0))
    for screen in (0, 1):
        px = draw(screen)
        pal = dict(RGB)
        if screen == 1:
            for k, c in zip((BOXA, BOXA_LT, BOXA_DK), HABITAT["rock"]): pal[k] = c
            for k, c in zip((BOXB, BOXB_LT, BOXB_DK), HABITAT["fish"]): pal[k] = c
        for y in range(H):
            for x in range(W):
                im.putpixel((screen * (W + 8) + x, y), pal[px[y][x]])
        for (cx, cy) in layout(screen)[2]:
            for d in range(-6, 7):
                im.putpixel((screen * (W + 8) + cx + d, cy + d), (160, 160, 160))
                im.putpixel((screen * (W + 8) + cx + d, cy - d), (160, 160, 160))
    t, maps, n = tiles_and_maps()
    print("%d tiles (%d bytes)" % (n, len(t)))
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else "preview.png")
