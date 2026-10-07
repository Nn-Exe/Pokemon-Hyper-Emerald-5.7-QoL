"""An English naming keyboard (Hyper Emerald v5.7). Apply before zhtext.
usage: python namingkb_patch.py <in.gba> <out.gba>

The naming screen (nicknames, the player's name, PC boxes) still had the hack's Chinese keyboard: three pages of
4 x 12 keys that are simply its character set in code order - "0-9, punctuation, A-V", "W-Z, a-z, PK MN ...", and
a page of Chinese characters (L / R leaf through more of them) - with the page button reading 小写 / 其他 / 大写
and the B button 回退.

How the hack's keyboard works (its routines at 0x094A3378..0x094A3810, hooked into Emerald's naming_screen.c):
* page_ptr (0x094A35B8): keyboard 0 and 1 are rows of text in ROM, 0x0862B810 + 0xC4 * id; keyboard 2 is built in
  RAM (sNamingScreen + 0x1900) by 0x094A35D8 from a two-byte start code.
* a ROM page is 4 rows of 0x31 bytes: 12 cells of `FC 11 n c` ({CLEAR n} pixels, then the key's character) and
  0xFF. The cursor moves 12 px a key (0x094A36A8: x = 0x1D + 12 * column), the first key starts 3 px in.
* GetCharAtKeyboardPos (0x094A36EC) returns 0xFF00 | c from a ROM page, or the two-byte code from the RAM page;
  PrintKeyboardKeys (0x094A3626) prints the four rows, 0x31 or (RAM page) 0x1A bytes apart.
* Emerald's order is unchanged: the screen opens on keyboard 1 ("UPPER"), SELECT goes to 0 ("lower"), then 2
  ("others"); the button names the page SELECT goes to next.

The patch:
* three new pages (KEYS below) in free space, and page_ptr's literal (0x094A35D4) pointed at them; its
  `cmp r0, #2; bne` taken always, so keyboard 2 is a ROM page like the others. The old rows at 0x0862B810 are
  left alone (Emerald's Easy Chat keyboard strings were there; its pointers still point at them).
* the same `bne` -> `b` in GetCharAtKeyboardPos, twice in PrintKeyboardKeys, and in the L and R handlers
  (0x094A37AC / 0x094A37C8: no more leafing through Chinese pages); the screen's setup no longer builds the RAM
  page (0x094A3380: `strh; bl` -> nops).
* the four sprite sheets the hack redrew in Chinese are Emerald's again (pret/pokeemerald's
  graphics/naming_screen/*.png as 4bpp, in this folder): the BACK button and the page names UPPER / lower / others.
  Every other sheet of the screen is still byte-identical to Emerald's.

A blank key types a space, as in Emerald. Names already saved are untouched (a Chinese nickname still shows).
"""
import hashlib, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
from inserter import ENC

FREE, FREE_END = 0x00FF7380, 0x00FF7700         # after rngseed (..0x08FF7368), in the unreferenced 0xFF run
FONTW = 0x006542E4                              # the normal font's glyph widths
ROW, PAGE, PITCH, FIRST = 0x31, 0xC4, 12, 3
OLD_TABLE, TABLE_LIT = 0x0862B810, 0x094A35D4
PAGE_PTR = (0x094A35B8, "022804d1044b1868c8235b0102e0c4235843024bc0187047949f0302")
ALWAYS = (                                      # `cmp rX, #2; bne` -> `b`: (address of the cmp, its four bytes)
    (0x094A35B8, "022804d1"),                   # page_ptr
    (0x094A36FC, "022e05d1"),                   # GetCharAtKeyboardPos
    (0x094A3636, "022c01d1"),                   # PrintKeyboardKeys: the window id kept beside the RAM page
    (0x094A3658, "022c01d1"),                   # PrintKeyboardKeys: the row size
    (0x094A37B2, "022807d1"),                   # R: next Chinese page
    (0x094A37CE, "02281dd1"),                   # L: previous Chinese page
)
SETUP = (0x094A3378, "022000f01df90121018000f029f970bd")     # movs r0,#2; bl page_ptr; movs r1,#1; strh; bl build; pop
SHEETS = (                                      # (file, address, sha1 of the hack's Chinese sheet)
    ("back_button.4bpp", 0x08DD3C84, "afa3f2b3d6db3885768b3137445690e78b48b8ea"),
    ("page_swap_upper.4bpp", 0x08DD4044, "ad5acfc2fcd6ae7ef8f519ae55378208ef736289"),
    ("page_swap_lower.4bpp", 0x08DD40E4, "ef513294c0ee637a9a5feaa08dc90e3a5ecb8000"),
    ("page_swap_others.4bpp", 0x08DD4184, "b6e57f25c904895bc9390c519559a13a6d6b75cb"),
)
GLYPHS = {"①": 0x53, "②": 0x54, "③": 0x55, "④": 0x56}    # the game's PK, MN, PO, Ke glyphs (not in the text table)
LETTERS = ["ABCDEFGHIJKL", "MNOPQRSTUVWX", "YZ  .,!?-’♂♀", "0123456789  "]
KEYS = {                                        # keyboard id -> four rows of twelve keys (" " = a space key)
    1: LETTERS,
    0: [r.lower() for r in LETTERS],
    2: ["0123456789  ", "!?.,-/…·‘’“”", "♂♀×%()$     ", "①②③④        "],
}


def code(ch):
    return GLYPHS[ch] if ch in GLYPHS else ENC[ch]


def row(rom, keys):
    assert len(keys) == 12
    out, x = bytearray(), 0
    for i, ch in enumerate(keys):
        c = code(ch)
        w = rom[FONTW + c]
        start = FIRST + PITCH * i + max(0, (6 - w) // 2)          # narrow glyphs sit in the middle of their key
        assert 0 <= start - x < 256 and w <= PITCH
        out += bytes((0xFC, 0x11, start - x, c))
        x = start + w
    return bytes(out) + b"\xff"


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert at(*PAGE_PTR) and u32(TABLE_LIT) == OLD_TABLE, "page_ptr is not the routine expected"
    assert at(*SETUP), "the screen's setup of the Chinese page moved"
    for a, hexs in ALWAYS:
        assert at(a, hexs), "%08X is not `cmp #2; bne`" % a
    old = bytes(rom[o(OLD_TABLE):o(OLD_TABLE) + 2 * PAGE])
    assert all(old[r * ROW + ROW - 1] == 0xFF and old[r * ROW:r * ROW + 2] == b"\xfc\x11" for r in range(8)), \
        "the old key rows are not 12 `FC 11 n c` cells"
    for name, a, sha in SHEETS:
        new = open(os.path.join(HERE, name), "rb").read()
        assert hashlib.sha1(rom[o(a):o(a) + len(new)]).hexdigest() == sha, "%s is not the hack's sheet" % name
        rom[o(a):o(a) + len(new)] = new

    table = b"".join(row(rom, r) for k in (0, 1, 2) for r in KEYS[k])
    assert len(table) == 3 * PAGE
    end = FREE + len(table)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not 0x08000000 + FREE <= v < 0x08000000 + end, "%08X already points into the target" % (0x08000000 + k)
    rom[FREE:end] = table
    struct.pack_into("<I", rom, o(TABLE_LIT), 0x08000000 + FREE)
    for a, _ in ALWAYS:
        rom[o(a) + 3] = 0xE0                                       # bne -> b (all forward, short)
    rom[o(SETUP[0]) + 8:o(SETUP[0]) + 14] = b"\xc0\x46" * 3        # strh r1, [r0]; bl build -> nops
    open(outp, "wb").write(rom)
    print("key pages %08X..%08X (lower, UPPER, others); %d branches always taken; %d sheets from Emerald" % (
        0x08000000 + FREE, 0x08000000 + end, len(ALWAYS), len(SHEETS)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
