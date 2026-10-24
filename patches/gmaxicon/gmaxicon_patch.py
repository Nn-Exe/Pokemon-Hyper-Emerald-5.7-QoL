"""A Gigantamax mark on the summary screen (Hyper Emerald v5.7): python gmaxicon_patch.py in.gba out.gba

Asked 2026-10-23, with a mock-up of the summary's first page (a small mushroom at the bottom right of the picture):
"for pokemon that already gained Gmax, can we dispaly icon like a mushroom in the pokemon detail ... I know that this
game might use ribbon as as marked"; of a first mushroom drawn here: "that mushroom design is stupid, cannot we use
this attached img? I think it is the item max mushroom" (the game's own Max Mushroom icon, item 87); of that icon at
its own 24 x 24: "smaller", "too big".

The mark is the hack's own: the Max Soup cook on Champion Island (35/28, script 0x098A7425: 3 Max Mushrooms, item 87,
the party's first Pokemon, callasm 0x08C60581) sets bit 7 of the Pokemon's byte +0x4E - in Emerald's ribbon word
(+0x4C), the Country Ribbon's bit, which nothing else in the game gives - and the Gigantamax table walk (0x08FF1858,
item 0xEFEF) reads it in battle. The cook gives it to any Pokemon ("if you give soup to a Pokemon that can only
Dynamax, the form won't change"), so the mark shows the soup, on any Pokemon that has had it.

The picture: item 87's icon and palette read from the ROM (the table at 0x08FCBFF4 the Bag's icons come from: LZ77,
24 x 24 4bpp and 16 colours), brought to SIZE x SIZE by taking the source pixel under each new pixel's middle (so
every pixel keeps one of the icon's own colours), in the bottom right of a 16 x 16 sprite.

The summary's CreateCaughtBallSprite (0x081C4A08) runs for every Pokemon the screen shows (from 0x081BFD56 and
0x081C07F6, both with r0 = sMonSummaryScreen + 0xC, its copy of the Pokemon); an 8-byte trampoline there leads to
gmaxicon.s, which replays the routine's first two instructions, lets it make the ball, then takes an old mark down
(found by its callback) and puts one up when the bit is set: the 16 x 16 sprite (tile and palette tag TAG,
priority 0) centred at ROW, the right end of the nickname's row, when the nickname (its width from the font's own
table) ends at least 2 px before it, else at ICON, the picture's bottom right corner: the mark never covers a name. Its callback hides it while the summary's
copy of the Pokemon has no bit (another one, an egg) or while the picture is hidden.
Space: 0x09E3AD00..0x09E3AFF0, in gen9abil's proven stretch (gen9anim's part ends at 0x09E3ACD0, eshot's tables start
at 0x09E3B000 and the word for its routine table holds 0x09E3AFF4), checked blank and unreferenced here.
"""
import os, re, struct, sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
B = 0x08000000
SPACE, SPACE_END = 0x09E3AD00, 0x09E3AFF0         # (eshot's routine-table word holds 0x09E3AFF4: its table - 12)
SITE = 0x081C4A08                       # CreateCaughtBallSprite: push {r4, lr}; movs r1, #0x26; bl GetMonData
SITE_BYTES = "10b52621" + "a5f684fd"
AFTER = "0004000c"                      # lsls r0, r0, #16; lsrs r0, r0, #16 (the routine goes on here, 0x081C4A10)
CALLERS = {0x081BFD50: "024800680c3004f0", 0x081C07F0: "024800680c3004f0"}   # ldr r0, =sMonSummaryScreen; ldr; adds #0xc
CALLED = {0x08006DF4: "f0b581b0", 0x080070E8: "f0b5051c", 0x080084F8: "70b5051c", 0x08008568: "f0b54746",
          0x08008744: "004b1847", 0x0800884C: "00b50004"}  # CreateSprite, DestroySprite, LoadSpriteSheet,
                                                            # FreeSpriteTilesByTag, LoadSpritePalette, FreeSpritePaletteByTag
ITEM_ICONS = 0x08FCBFF4                 # item -> {LZ77 24 x 24 picture, LZ77 palette}
ITEM, ITEM_NAME = 87, "Max Mushroom"
SIZE = 14
TAG = 0x47A1
ICON = (64, 88)                         # the sprite's centre: its bottom right (72, 96) is the picture frame's
ROW = (70, 103)                         # on the nickname's row: the icon at x 64..77, y 97..110 (panel inside to x 78)
NAME_X = 8                              # the nickname is printed from x 8, rows 96..111 (measured on a screenshot)
MAX_NAME = ROW[0] + 8 - SIZE - 2 - NAME_X   # the widest nickname the row takes: 2 px clear of the icon
GLYPH_W = 0x086542E4                    # the normal font's glyph widths ("Blaziken" 44 px, as on the screen)
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    assert not [i for i in dis if i.size == 4 and i.mnemonic != "bl"], "Thumb-2 encoding emitted"
    return code, dis


def u32(rom, a):
    return struct.unpack_from("<I", rom, a - B)[0]


def lz77(rom, a):
    o = a - B
    assert rom[o] == 0x10
    size = rom[o + 1] | rom[o + 2] << 8 | rom[o + 3] << 16
    out, i = bytearray(), o + 4
    while len(out) < size:
        flags = rom[i]; i += 1
        for b in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> b):
                n, d = (rom[i] >> 4) + 3, ((rom[i] & 0xF) << 8 | rom[i + 1]) + 1
                i += 2
                for _ in range(n):
                    out.append(out[-d])
            else:
                out.append(rom[i]); i += 1
    return bytes(out[:size])                             # a last copy can run past the end


def picture(rom):
    """item 87's icon as SIZE x SIZE in the bottom right of 16 x 16: 4 tiles of 4bpp (1D order), and its palette"""
    pix, pal = lz77(rom, u32(rom, ITEM_ICONS + 8 * ITEM)), lz77(rom, u32(rom, ITEM_ICONS + 8 * ITEM + 4))
    assert len(pix) == 9 * 32 and len(pal) == 32, "the icon is not 24 x 24 4bpp with 16 colours"
    def src(x, y):                                       # the icon's 3 x 3 tiles, row by row
        t = (y // 8) * 3 + x // 8
        v = pix[t * 32 + (y % 8) * 4 + (x % 8) // 2]
        return v & 0xF if x % 2 == 0 else v >> 4
    img = [[0] * 16 for _ in range(16)]
    off = 16 - SIZE
    for y in range(SIZE):
        for x in range(SIZE):
            img[off + y][off + x] = src(int((x + 0.5) * 24 / SIZE), int((y + 0.5) * 24 / SIZE))
    tiles = b""
    for ty in (0, 8):
        for tx in (0, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    tiles += bytes([img[ty + y][tx + x] | img[ty + y][tx + x + 1] << 4])
    return tiles, pal, img


def write_png(img, pal, path):
    try:
        from PIL import Image
    except ImportError:
        return
    cols = [struct.unpack_from("<H", pal, 2 * k)[0] for k in range(16)]
    im = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            c = cols[img[y][x]]
            im.putpixel((x, y), (0, 0, 0, 0) if img[y][x] == 0 else ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3, 255))
    im.resize((128, 128), Image.NEAREST).save(path)


def build(inp, outp, png=None):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert rom[SITE - B:SITE - B + 8].hex() == SITE_BYTES, "CreateCaughtBallSprite's start"
    assert rom[SITE + 8 - B:SITE + 12 - B].hex() == AFTER, "CreateCaughtBallSprite after its GetMonData"
    for a, want in CALLERS.items():
        assert rom[a - B:a - B + 8].hex() == want, "the call at %08X" % a
    for a, want in CALLED.items():
        assert rom[a - B:a - B + 4].hex() == want, "the routine at %08X" % a
    items = u32(rom, B + 0x1C8)
    name = bytes(0xBB + ord(c) - 65 if c.isupper() else 0xD5 + ord(c) - 97 if c.islower() else 0 for c in ITEM_NAME)
    assert rom[items - B + 44 * ITEM:items - B + 44 * ITEM + len(name)] == name, "item 87's name"
    assert u32(rom, 0x081B0034) == ITEM_ICONS, "the item icon table the game reads (GetItemIconPicOrPalette)"
    assert set(rom[SPACE - B:SPACE_END - B]) == {0}, "the space is not blank"
    held = [B + o for o in range(0, len(rom), 4) if SPACE <= struct.unpack_from("<I", rom, o)[0] < SPACE_END]
    assert not held, "words point into the space: %s" % ["%08X" % a for a in held]
    tiles, pal, img = picture(rom)

    src = open(os.path.join(HERE, "gmaxicon.s"), encoding="ascii").read()
    assert [rom[GLYPH_W - B + c] for c in (0xBB, 0xDD, 0x00)] == [6, 4, 3], "the font's widths (A, i, space)"
    src = (src.replace("ICON_X", str(ICON[0])).replace("ICON_Y", str(ICON[1])).replace("TAG", "0x%04X" % TAG)
           .replace("ROW_X", str(ROW[0])).replace("ROW_Y", str(ROW[1])).replace("MAX_NAME", str(MAX_NAME)))

    def assemble(data_at):
        s = src
        for k, v in data_at.items():
            s = re.sub(r"\b%s\b" % k, "0x%08X" % v, s)
        for pad in ("", "    mov r8, r8"):
            code, dis = thumb(s.replace("PAD", pad), SPACE)
            if not [i for i in dis if i.mnemonic == "nop"]:
                return code, dis
        raise AssertionError("could not pad the literal pool without a Thumb-2 nop")
    names = ("RET_HERE", "GMAX_CB", "TEMPLATE", "SHEET", "PALETTE")
    code, dis = assemble({n: SPACE for n in names})
    ret_here = [i.address for i in dis if i.mnemonic == "adds" and i.op_str == "r0, r5, #0"][0]
    cb = [i.address for i in dis if i.mnemonic == "ldrh" and i.op_str == "r1, [r0, #0x2e]"][0]
    at = (SPACE + len(code) + 3) & ~3
    layout, blob = {}, b""
    def put(name, data):
        nonlocal blob
        blob += b"\0" * (-len(blob) % 4)
        layout[name] = at + len(blob)
        blob += data
    put("TILES", tiles)
    put("PAL", pal)
    put("OAM", bytes((0, 0, 0, 0x40, 0, 0, 0, 0)))          # 16 x 16 square, priority 0
    put("ANIM", struct.pack("<II", 0x00010000, 0x0000FFFF))   # frame 0 for 1, end
    put("AFFANIM", struct.pack("<II", 0x00007FFF, 0))         # end
    put("ANIMS", struct.pack("<I", layout["ANIM"]))
    put("AFFANIMS", struct.pack("<I", layout["AFFANIM"]))
    put("SHEET", struct.pack("<IHH", layout["TILES"], len(tiles), TAG))
    put("PALETTE", struct.pack("<IHH", layout["PAL"], TAG, 0))
    put("TEMPLATE", struct.pack("<HHIIIII", TAG, TAG, layout["OAM"], layout["ANIMS"], 0, layout["AFFANIMS"], cb | 1))
    code2, dis2 = assemble({"RET_HERE": ret_here | 1, "GMAX_CB": cb | 1, "TEMPLATE": layout["TEMPLATE"],
                            "SHEET": layout["SHEET"], "PALETTE": layout["PALETTE"]})
    assert len(code2) == len(code)
    assert at + len(blob) <= SPACE_END, "the space is too small"
    assert [i.mnemonic for i in dis2[:2]] == ["push", "adds"], "stub first"

    rom[SPACE - B:SPACE - B + len(code2)] = code2
    rom[at - B:at - B + len(blob)] = blob
    rom[SITE - B:SITE - B + 8] = bytes.fromhex("004b1847") + struct.pack("<I", SPACE | 1)
    open(outp, "wb").write(rom)
    if png:
        write_png(img, pal, png)
    print("gmaxicon: code %08X..%08X, data ..%08X; item %d's icon at %d x %d, centred at %s on the name row "
          "(nicknames up to %d px), else at %s; tag %04X"
          % (SPACE, SPACE + len(code2), at + len(blob), ITEM, SIZE, SIZE, ROW, MAX_NAME, ICON, TAG))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
