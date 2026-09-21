"""Convert a region-map picture into GBA background data (4bpp tiles + tilemap + palettes).

usage: python make_region_map.py <in.png> <out-prefix> [--colors 24] [--width 240] [--height 160]
                                 [--bpp 8] [--base 112]

--bpp 8 writes an 8bpp (256-colour) background, which is what this game's own region map uses. In 8bpp a
tile may use any colour, so the 16-colour-per-tile rule disappears and the picture keeps all its shades.
--base sets the first palette index used, so the data can sit in a spare slice of the 256-colour bank
(the game's Hoenn map occupies 112..159) and leave the rest of the screen's colours alone.

Steps, in order:
  1. Fit the picture to the screen. Extra rows are removed one at a time, always the row that differs
     least from its neighbour, so the pixels stay crisp instead of being resampled. Extra width is
     padded with the picture's own background colour.
  2. Reduce to N colours (median cut, no dithering) and drop to the GBA's 5 bits per channel.
  3. Group the tiles' colours into palettes of 15, best fit first. A tile can only use one palette, so
     this is what really limits the picture, not the number of tiles. Fifteen, not sixteen: on a GBA
     background colour 0 is TRANSPARENT and shows the backdrop through it, so the colours start at 1 and
     index 0 is left unused. Using it paints scattered backdrop-coloured holes over the picture.
  4. Deduplicate 8x8 tiles, reusing a tile when it matches another flipped horizontally or vertically.
  5. Write tiles, a 32x32 tilemap and a 16-palette block, each raw and LZ77-compressed the way the
     game's own graphics are stored.

It then renders the result back from those files and checks it matches, so a clean run means what you
see in the preview is exactly what the hardware would draw.
"""
import os, struct, sys
import numpy as np
from PIL import Image

BG_TILES, BG_PALS = 512, 16
COLORS_PER_PAL = 15            # index 0 is transparent on a background, so colours live at 1..15


def fit(im, W, H):
    a = np.asarray(im.convert("RGB")).astype(int)
    h, w = a.shape[:2]
    while h > H:                                    # drop the flattest row
        d = np.abs(np.diff(a, axis=0)).sum(axis=(1, 2))
        y = int(np.argmin(d))
        a = np.delete(a, y, axis=0); h -= 1
    if h < H:
        a = np.pad(a, ((0, H - h), (0, 0), (0, 0)), mode="edge"); h = H
    if w < W:                                       # centre it on its own background colour
        vals, counts = np.unique(a.reshape(-1, 3), axis=0, return_counts=True)
        bg = vals[counts.argmax()]
        left = (W - w) // 2
        out = np.tile(bg, (H, W, 1)).astype(int)
        out[:, left:left + w] = a
        a = out
    elif w > W:
        a = a[:, (w - W) // 2:(w - W) // 2 + W]
    return Image.fromarray(a.astype(np.uint8))


def pack_palettes(tiles):
    pals = []
    for _, cs in sorted(tiles, key=lambda t: -len(t[1])):
        best = None
        for i, p in enumerate(pals):
            u = len(p | cs)
            if u <= COLORS_PER_PAL and (best is None or u - len(p) < best[0]): best = (u - len(p), i)
        if best: pals[best[1]] |= cs
        else: pals.append(set(cs))
    assert len(pals) <= BG_PALS, "needs %d palettes, the hardware has %d - use fewer colours" % (len(pals), BG_PALS)
    return pals


MIN_DISP = 2            # see below: LZ77UnCompVram cannot follow a back-reference of distance 1


def lz77(data):
    """GBA LZ77 (compression type 1), the format LZ77UnCompVram expects.

    Back-references must be at least MIN_DISP bytes back. The BIOS routine that unpacks straight into
    video memory can only write there a halfword at a time, so the byte it just produced is still in its
    own buffer, not yet in VRAM. A distance-1 reference - the obvious way to encode a run of one repeated
    byte - reads that unwritten byte back as zero, and long flat areas come out full of holes. This is
    invisible when unpacking to normal memory, so it only shows up on hardware."""
    out = bytearray(struct.pack("<I", (len(data) << 8) | 0x10))
    pos = 0
    while pos < len(data):
        flags_at = len(out); out.append(0); flags = 0
        for bit in range(8):
            if pos >= len(data): break
            best_len, best_dist = 0, 0
            start = max(0, pos - 0x1000)
            for back in range(start, pos - MIN_DISP + 1):
                if data[back] != data[pos]: continue
                n = 0
                while n < 18 and pos + n < len(data) and data[back + n] == data[pos + n]: n += 1
                if n > best_len: best_len, best_dist = n, pos - back
            if best_len >= 3:
                out.append(((best_len - 3) << 4) | ((best_dist - 1) >> 8))
                out.append((best_dist - 1) & 0xFF)
                flags |= 0x80 >> bit
                pos += best_len
            else:
                out.append(data[pos]); pos += 1
        out[flags_at] = flags
    while len(out) % 4: out.append(0)
    return bytes(out)


def eight_bpp(im, q5, W, H, prefix, base):
    """256-colour background: one flat palette, no per-tile colour limit."""
    cols = sorted({tuple(c) for c in q5.reshape(-1, 3)})
    assert base + len(cols) <= 256, "colours do not fit in the palette bank at base %d" % base
    lut = {c: base + i for i, c in enumerate(cols)}
    tiles, tmap, seen = [], [], {}
    for ty in range(H // 8):
        for tx in range(W // 8):
            t = q5[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            px = np.array([[lut[tuple(t[y, x])] for x in range(8)] for y in range(8)], np.uint8)
            for hf in (0, 1):
                for vf in (0, 1):
                    v = px[::-1, :] if vf else px
                    v = v[:, ::-1] if hf else v
                    if v.tobytes() in seen:
                        tmap.append(seen[v.tobytes()] | (hf << 10) | (vf << 11)); break
                else: continue
                break
            else:
                seen[px.tobytes()] = len(tiles); tmap.append(len(tiles)); tiles.append(px)
    assert len(tiles) <= BG_TILES, "needs %d tiles, a character block holds %d at 8bpp" % (len(tiles), BG_TILES)
    print("8bpp: %d colours at palette index %d, %d tiles of %d" % (len(cols), base, len(tiles), BG_TILES))
    tile_bytes = b"".join(px.tobytes() for px in tiles)
    map_bytes = bytearray()
    for row in range(32):
        for col in range(32):
            i = row * (W // 8) + col
            map_bytes += struct.pack("<H", tmap[i] if col < W // 8 and row < H // 8 else 0)
    pal_bytes = bytearray()
    for c in cols:
        pal_bytes += struct.pack("<H", c[0] | (c[1] << 5) | (c[2] << 10))
    for name, blob in (("tiles.8bpp", tile_bytes), ("tilemap8.bin", bytes(map_bytes)), ("palette8.pal", bytes(pal_bytes))):
        open(prefix + "." + name, "wb").write(blob)
        comp = lz77(blob)
        open(prefix + "." + name + ".lz", "wb").write(comp)
        print("  %-14s %6d bytes raw, %6d compressed" % (name, len(blob), len(comp)))
    out = np.zeros((H, W, 3), np.uint8)
    for row in range(H // 8):
        for col in range(W // 8):
            e = tmap[row * (W // 8) + col]
            px = tiles[e & 0x3FF].copy()
            if e & 0x400: px = px[:, ::-1]
            if e & 0x800: px = px[::-1, :]
            for y in range(8):
                for x in range(8):
                    c = cols[px[y, x] - base]
                    out[row * 8 + y, col * 8 + x] = ((c[0] << 3) | (c[0] >> 2), (c[1] << 3) | (c[1] >> 2), (c[2] << 3) | (c[2] >> 2))
    want = np.vectorize(lambda c: (c << 3) | (c >> 2))(q5).astype(np.uint8)
    assert (out == want).all(), "round-trip mismatch"
    Image.fromarray(out).save(prefix + ".preview.png")
    Image.fromarray(out).resize((W * 3, H * 3), Image.NEAREST).save(prefix + ".preview3x.png")
    print("round-trip verified")


def main():
    src, prefix = sys.argv[1], sys.argv[2]
    def arg(name, default):
        return int(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default
    ncol, W, H = arg("--colors", 24), arg("--width", 240), arg("--height", 160)
    bpp, base = arg("--bpp", 4), arg("--base", 0)
    assert bpp in (4, 8)

    im = fit(Image.open(src), W, H)
    im = im.quantize(colors=ncol, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    q5 = np.asarray(im).astype(int) >> 3
    print("%s -> %dx%d (%dx%d tiles), %d colours"
          % (os.path.basename(src), W, H, W // 8, H // 8, len({tuple(c) for c in q5.reshape(-1, 3)})))

    if bpp == 8:
        return eight_bpp(im, q5, W, H, prefix, base)

    grid = []
    for ty in range(H // 8):
        for tx in range(W // 8):
            t = q5[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8]
            grid.append((t, frozenset(map(tuple, t.reshape(-1, 3)))))
    pals = pack_palettes(grid)
    print("palettes: %d of %d (%s colours each)" % (len(pals), BG_PALS, ", ".join(str(len(p)) for p in pals)))

    order = [sorted(p) for p in pals]
    tiles, tmap = [], []
    seen = {}
    for t, cs in grid:
        pi = next(i for i, p in enumerate(pals) if cs <= p)
        lut = {c: k + 1 for k, c in enumerate(order[pi])}     # 1..15; 0 stays transparent
        px = np.array([[lut[tuple(t[y, x])] for x in range(8)] for y in range(8)], np.uint8)
        for hf in (0, 1):
            for vf in (0, 1):
                v = px[::-1, :] if vf else px
                v = v[:, ::-1] if hf else v
                key = (pi, v.tobytes())
                if key in seen:
                    tmap.append(seen[key] | (hf << 10) | (vf << 11) | (pi << 12)); break
            else: continue
            break
        else:
            seen[(pi, px.tobytes())] = len(tiles)
            tmap.append(len(tiles) | (pi << 12))
            tiles.append(px)
    assert len(tiles) <= BG_TILES, "needs %d tiles, one character block holds %d" % (len(tiles), BG_TILES)
    print("tiles: %d of %d" % (len(tiles), BG_TILES))

    tile_bytes = bytearray()
    for px in tiles:
        for y in range(8):
            for x in range(0, 8, 2):
                tile_bytes.append(px[y, x] | (px[y, x + 1] << 4))
    map_bytes = bytearray()
    for row in range(32):
        for col in range(32):
            i = row * (W // 8) + col
            map_bytes += struct.pack("<H", tmap[i] if col < W // 8 and row < H // 8 else 0)
    # the commonest colour becomes the backdrop, so anything transparent still reads as sea
    vals, counts = np.unique(q5.reshape(-1, 3), axis=0, return_counts=True)
    back = tuple(int(v) for v in vals[counts.argmax()])
    pal_bytes = bytearray()
    for i in range(BG_PALS):
        for k in range(16):
            if k == 0: c = back
            else: c = order[i][k - 1] if i < len(order) and k - 1 < len(order[i]) else (0, 0, 0)
            pal_bytes += struct.pack("<H", c[0] | (c[1] << 5) | (c[2] << 10))

    for name, blob in (("tiles.4bpp", tile_bytes), ("tilemap.bin", map_bytes), ("palette.pal", pal_bytes)):
        open(prefix + "." + name, "wb").write(blob)
        comp = lz77(bytes(blob))
        open(prefix + "." + name + ".lz", "wb").write(comp)
        print("  %-14s %6d bytes raw, %6d compressed" % (name, len(blob), len(comp)))

    # render it back exactly as the hardware would, and check
    out = np.zeros((H, W, 3), np.uint8)
    for row in range(H // 8):
        for col in range(W // 8):
            e = tmap[row * (W // 8) + col]
            px = tiles[e & 0x3FF].copy()
            if e & 0x400: px = px[:, ::-1]
            if e & 0x800: px = px[::-1, :]
            pal = order[e >> 12]
            for y in range(8):
                for x in range(8):
                    c = pal[px[y, x] - 1] if px[y, x] else back
                    out[row * 8 + y, col * 8 + x] = ((c[0] << 3) | (c[0] >> 2), (c[1] << 3) | (c[1] >> 2), (c[2] << 3) | (c[2] >> 2))
    want = np.vectorize(lambda c: (c << 3) | (c >> 2))(q5).astype(np.uint8)
    assert (out == want).all(), "round-trip mismatch"
    Image.fromarray(out).save(prefix + ".preview.png")
    Image.fromarray(out).resize((W * 3, H * 3), Image.NEAREST).save(prefix + ".preview3x.png")
    print("round-trip verified; wrote %s.preview.png" % os.path.basename(prefix))


if __name__ == "__main__":
    main()
