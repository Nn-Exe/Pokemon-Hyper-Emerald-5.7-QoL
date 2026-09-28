"""One-off: cut the eight Sinnoh badges out of a picture of Platinum's badge case (4 x 2, dark grey panel) and
write sinnoh.png, a 256x32 RGBA sheet of 32x32 cells (Coal, Forest, Cobble, Fen, Relic, Mine, Icicle, Beacon),
each badge scaled to fit 30x30 and centred. The panel and the grey halo around each slot are found by a flood
fill from the panel (greys only), which stops at every badge's bright rim.
    python extract_sinnoh.py <badge case picture> [out.png]
"""
import sys
from collections import deque
import numpy as np
from PIL import Image


def main():
    im = Image.open(sys.argv[1]).convert("RGB")
    out_path = sys.argv[2] if len(sys.argv) > 2 else "sinnoh.png"
    a = np.asarray(im).astype(int)
    H, W, _ = a.shape
    grey = lambda p: max(abs(p[0] - p[1]), abs(p[1] - p[2]), abs(p[0] - p[2])) < 14 and 60 <= p[0] <= 150
    bg = np.zeros((H, W), bool)
    seed = (H // 5, W // 25)                        # just inside the panel's top-left corner
    q = deque([seed]); bg[seed] = True
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and not bg[ny, nx] and grey(a[ny, nx]):
                bg[ny, nx] = True; q.append((ny, nx))
    fg = ~bg
    lab = np.zeros((H, W), int); boxes = []; n = 0
    for y in range(H):
        for x in range(W):
            if fg[y, x] and not lab[y, x]:
                n += 1; q = deque([(y, x)]); lab[y, x] = n; pts = []
                while q:
                    cy, cx = q.popleft(); pts.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and fg[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n; q.append((ny, nx))
                ys = [p[0] for p in pts]; xs = [p[1] for p in pts]
                area = (max(ys) - min(ys)) * (max(xs) - min(xs))
                if len(pts) > 500 and area < H * W // 8:      # a badge, not the panel's frame or the button
                    boxes.append((min(ys), min(xs), max(ys), max(xs), n))
    assert len(boxes) == 8, "found %d badges" % len(boxes)
    mid = sum(b[0] for b in boxes) / 8
    boxes.sort(key=lambda b: (b[0] > mid, b[1]))           # top row left to right, then the bottom row
    sheet = Image.new("RGBA", (256, 32), (0, 0, 0, 0))
    for k, (y0, x0, y1, x1, lb) in enumerate(boxes):
        arr = np.asarray(im.crop((x0, y0, x1 + 1, y1 + 1)).convert("RGBA")).copy()
        arr[..., 3] = np.where(lab[y0:y1 + 1, x0:x1 + 1] == lb, 255, 0)
        c = Image.fromarray(arr.astype(np.uint8))
        s = 30 / max(c.size)
        c = c.resize((max(1, round(c.size[0] * s)), max(1, round(c.size[1] * s))), Image.LANCZOS)
        sheet.paste(c, (k * 32 + (32 - c.size[0]) // 2, (32 - c.size[1]) // 2), c)
    sheet.save(out_path)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
