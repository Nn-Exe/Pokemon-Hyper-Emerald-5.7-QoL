"""Pokedex descriptions that ran into the frame (Hyper Emerald v5.7). Apply after the hisuimap build.
usage: python dexdesc_patch.py <in.gba> <out.gba>

The Pokedex (the info page and the "registration completed" page after a catch) prints a description
centred on the 240-pixel screen: x = GetStringCenterAlignXOffset(font 1, text, 240), then one text printer
at y 95 (PrintMonInfo, 0x080C0314..0x080C0342). Two things broke that for some translated entries:

1. Five descriptions (national 562 Yamask, 722 Rowlet, 753 Fomantis, 755 Morelull, 802 Marshadow) had a line break
   written as 0xFA - "scroll, wait for a button" - instead of 0xFE, a plain new line. The page then stopped
   on a ▼, and the width measured for centring ran the lines on each side of the 0xFA together, well past
   240 pixels, so the text was placed at x 0, under the frame's left edge ("It" lost its "I").
   Each 0xFA becomes 0xFE.
2. Some lines were wider than any the hack's own English entries use (224 pixels at most), up to 231, which
   centres them only 4 pixels from the frame. Those descriptions are re-wrapped to 224 pixels, still in at
   most four lines (the page's room), by moving breaks between words.

Both only swap separator bytes (0x00 space, 0xFE new line) inside the existing strings: every string keeps
its length and its address, nothing is repointed.
"""
import struct, sys

TABLE = 0x01250000                  # the hack's Pokedex entries: 32 bytes each, description pointer at +16
ENTRIES = 960
GLYPH_W = 0x006542E4                # gFontNormalLatinGlyphWidths
MAX_W = 224                         # the widest line in the hack's own English descriptions
MAX_LINES = 4
SPACE, NEWLINE, SCROLL, END = 0x00, 0xFE, 0xFA, 0xFF


def width(rom, word):
    return sum(rom[GLYPH_W + c] for c in word)


def wrap(rom, words):
    """Greedy wrap at MAX_W -> list of lines (lists of words), or None if it needs more than MAX_LINES."""
    sw = rom[GLYPH_W + SPACE]
    lines, cur, cw = [], [], 0
    for wd in words:
        w = width(rom, wd)
        if cur and cw + sw + w > MAX_W:
            lines.append(cur); cur, cw = [], 0
        cw += (sw if cur else 0) + w
        cur.append(wd)
    lines.append(cur)
    return lines if len(lines) <= MAX_LINES and all(sum(width(rom, w) for w in l) + sw * (len(l) - 1) <= MAX_W for l in lines) else None


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert struct.unpack_from("<I", rom, 0x0C0314 + 0x14)[0] == 0x08000000 + TABLE, "PrintMonInfo reads another table"
    seen, scroll_fixed, rewrapped, left = set(), [], [], []
    for n in range(ENTRIES):
        p = struct.unpack_from("<I", rom, TABLE + n * 32 + 16)[0]
        if not 0x08000000 <= p < 0x0A000000 or p in seen:
            continue
        seen.add(p)
        o = p - 0x08000000
        e = rom.index(END, o)
        s = bytes(rom[o:e])
        assert all(c < 0xF7 or c in (NEWLINE, SCROLL) for c in s), "entry %d has other control codes" % n
        if SCROLL in s:
            s = s.replace(bytes((SCROLL,)), bytes((NEWLINE,)))
            scroll_fixed.append(n)
        lines = s.split(bytes((NEWLINE,)))
        if max(width(rom, l) for l in lines) > MAX_W:
            words = [w for w in s.replace(bytes((NEWLINE,)), bytes((SPACE,))).split(bytes((SPACE,))) if w]
            assert bytes((SPACE,)).join(words) == s.replace(bytes((NEWLINE,)), bytes((SPACE,))), \
                "entry %d has double spaces" % n
            new = wrap(rom, words)
            if new is None:
                left.append(n)
            else:
                s = bytes((NEWLINE,)).join(bytes((SPACE,)).join(l) for l in new)
                rewrapped.append(n)
        assert len(s) == e - o
        rom[o:e] = s
    open(outp, "wb").write(rom)
    print("0xFA -> 0xFE in %d descriptions: %s" % (len(scroll_fixed), scroll_fixed))
    print("re-wrapped to %d px: %d descriptions %s" % (MAX_W, len(rewrapped), rewrapped))
    if left:
        print("still wider than %d px (would need a 5th line): %s" % (MAX_W, left))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
