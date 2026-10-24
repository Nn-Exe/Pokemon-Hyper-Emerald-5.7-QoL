"""Cheren's Mint list: Quirky in, in the usual order, inside the screen (Hyper Emerald v5.7).
usage: python mintquirky_patch.py <in.gba> <out.gba>

A player's report (2026-10-22): "The Mint table that Cheren uses to change natures is missing the 'Quirky' nature ...
there's a space with the word 'None' that reverses the action of the Mint ... the table box extends beyond the game
screen limit ... so maybe use replace 'None' with 'Quirky'". The user chose: the 5x5 grid, Quirky in None's place,
no undo (choosing the Pokemon's own nature does the same), names cut to fit.

The offer (script 0x0984A658, both Mint people: Rustboro's school 11/4 and Jubilife 37/77) shows multichoicegrid 0x7C
(5 columns) and hands the slot to 0x08FF0E00, which writes it to mon + 0x1F (bits 0-6) and recalculates the stats.
The list was None, Lonely .. Careful, Hardy: 0 = no Mint, 24 = Hardy (naturefix shows 24 as Hardy). Quirky had no
value: the stats code (0x09F038BC, 0x09F03930) takes the byte as the nature's number, so anything over 24 would
give a wrong nature. And the grid sizes each column by its widest name ((w + 9) / 8 + 1 tiles): "Adamnt" (36 px)
made 6-tile columns, 5 x 6 + the frame = 32 tiles on a 30-tile screen, so the right edge was off it.

Now:
  * the list (its 25 entries' texts): Hardy .. Quirky in the natures' own order, slot = nature, every name at most
    30 px (5-tile columns: 27 tiles with the frame): Lonly, Adamt, Nauty, Docil, Relax, Impsh, Serio, Modst, Bashf,
    Gentl, Caref, Quirk, the other 13 whole;
  * the script's callasm -> mint_apply: slot 0 (Hardy) is written as 24, slot 24 (Quirky) as 25, then 0x08FF0E00;
  * the byte 25 reaches the stats as 24 (bl mint_r3 / mint_r0 at the two places that read it), and GetNature
    (0x0806D070's word, naturefix's stub before) shows 24 as Hardy and 25 as Quirky. Saves with 24 keep "Hardy".
Code and texts: 0x09E3C000..0x09E3C10C (0x09E3C000..0x09E3C200 kept), inside 4 MB of the stats code for its bl's.
Blank since the original hack (its zero run 0x09E10044..0x09F00000); blank today from gen9anim's end (0x09E3ACD0)
to kitakami (0x09E40000); no word in the ROM reads as an address in 0x09E3C000..0x09E3C400 (15 chance words in
pictures and data point elsewhere in the gap, none a code literal).
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

FREE, FREE_END = 0x01E3C000, 0x01E3C200
BASE = 0x08000000 + FREE
LIST, LIST_N = 0x0984A9B8, 25                 # multichoice 0x7C's entries {text, unused word}
TABLE_7C = 0x097003E0                          # the multichoice table's entry 0x7C
CALLASM = 0x0984A68B                           # callasm 0x08FF0E01 in the offer
GETNATURE_WORD, NATUREFIX_STUB = 0x0806D074, 0x08F54201
R0_SITE, R3_SITE = 0x09F038C4, 0x09F03930
EXPECT = [
    (0x09F038BC, "10b5c37f5a0602d05806400e10bd"),        # getter: ldrb r3,[r0,#0x1f]; lsls; beq; lsls r0; lsrs r0; pop
    (0x09F03926, "4346db7f5a0600d17ee05b065b0e9946"),    # CalculateMonStats: ...; lsls r3; lsrs r3; mov sb, r3
    (0x0806D070, "004b18470142f508"),                    # GetNature: ldr r3, =naturefix's stub; bx r3
    (CALLASM, "23010eff08"),
    (TABLE_7C, "b8a984091900007c"),
    (0x08FF0E00, "f0b5094800786421484308494018"),        # the hack's apply routine
]
OLD_NAMES = ["None", "Lonely", "Brave", "Adamnt", "Naugh", "Bold", "Docile", "Relaxd", "Impish", "Lax", "Timid",
             "Hasty", "Serio", "Jolly", "Naive", "Modest", "Mild", "Quiet", "Bashfl", "Rash", "Calm", "Gentle",
             "Sassy", "Carefl", "Hardy"]
NAMES = ["Hardy", "Lonly", "Brave", "Adamt", "Nauty", "Bold", "Docil", "Relax", "Impsh", "Lax", "Timid", "Hasty",
         "Serio", "Jolly", "Naive", "Modst", "Mild", "Quiet", "Bashf", "Rash", "Calm", "Gentl", "Sassy", "Caref",
         "Quirk"]
WIDTHS = 0x086542E4                            # the field font's glyph widths


def enc(s):
    out = bytearray()
    for c in s:
        if "A" <= c <= "Z": out.append(0xBB + ord(c) - 65)
        elif "a" <= c <= "z": out.append(0xD5 + ord(c) - 97)
        else: raise ValueError(c)
    return bytes(out)


def dec(rom, a):
    s, o = "", a - 0x08000000
    while rom[o] != 0xFF:
        b = rom[o]
        s += chr(65 + b - 0xBB) if 0xBB <= b < 0xD5 else chr(97 + b - 0xD5) if 0xD5 <= b < 0xEF else "?"
        o += 1
    return s


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (
        addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    assert not [i for i in dis if i.mnemonic == "nop"], "a Thumb-2 nop (00 BF) slipped in: use mov r8, r8"
    return code


def bl(site, target):
    off = target - (site + 4)
    assert -0x400000 <= off < 0x400000 and not off & 1
    return struct.pack("<HH", 0xF000 | ((off >> 12) & 0x7FF), 0xF800 | ((off >> 1) & 0x7FF))


def pooled(src, addr):
    """thumb(), with or without a mov r8, r8 before each pool: .align must not pad with the assembler's 00 BF"""
    for pad in ("", "    mov r8, r8\n"):
        try:
            return thumb(src.replace("    .align 2", pad + "    .align 2"), addr)
        except AssertionError as e:
            if "nop" not in str(e):
                raise
    raise AssertionError("no padding keeps the pools on a word without a Thumb-2 nop")


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    for a, hexs in EXPECT:
        assert bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs), \
            "the game's code or data at %08X is not as expected" % a
    old = [dec(rom, struct.unpack_from("<I", rom, o(LIST) + 8 * k)[0]) for k in range(LIST_N)]
    assert old == OLD_NAMES, "the Mint list is %s" % old
    held = [0x08000000 + m.start() for m in re.finditer(re.escape(struct.pack("<I", NATUREFIX_STUB)), bytes(rom))]
    assert held == [GETNATURE_WORD], "naturefix's stub is reached from elsewhere too: %s" % held
    for n in NAMES:
        w = sum(rom[o(WIDTHS) + b] for b in enc(n))
        assert w <= 30, "%s is %d px: the grid would not fit" % (n, w)

    blob, at = bytearray(), {}
    src = open(os.path.join(HERE, "mintquirky.s"), encoding="ascii").read()
    for part in re.split(r"^@@@ ", src, flags=re.M)[1:]:   # each function on its own, at the next word
        name, body = part.split("\n", 1)
        at[name.strip()] = BASE + len(blob)
        blob += pooled(body, BASE + len(blob))
        while len(blob) % 4: blob.append(0)
    assert list(at) == ["mint_r3", "mint_r0", "get_nature", "mint_apply"]
    texts = []
    for n in NAMES:
        texts.append(BASE + len(blob))
        blob += enc(n) + b"\xFF"
    end = FREE + len(blob)
    assert end <= FREE_END and set(rom[FREE:FREE_END]) == {0x00}, "target region not blank"
    for m in re.finditer(rb"(?s).[\xc0-\xc1]\xe3\x09", bytes(rom)):        # at any byte offset, not only words
        v = struct.unpack_from("<I", rom, m.start())[0]
        assert not BASE <= v < 0x08000000 + FREE_END, "%08X reads as an address in the target (%08X)" % (
            0x08000000 + m.start(), v)
    rom[FREE:end] = blob

    for k, t in enumerate(texts):
        struct.pack_into("<I", rom, o(LIST) + 8 * k, t)
    struct.pack_into("<I", rom, o(CALLASM) + 1, at["mint_apply"] | 1)
    struct.pack_into("<I", rom, o(GETNATURE_WORD), at["get_nature"] | 1)
    rom[o(R0_SITE):o(R0_SITE) + 4] = bl(R0_SITE, at["mint_r0"])
    rom[o(R3_SITE):o(R3_SITE) + 4] = bl(R3_SITE, at["mint_r3"])
    open(outp, "wb").write(rom)
    print("mintquirky: %08X..%08X (%s); list texts from %08X" % (
        BASE, 0x08000000 + end, ", ".join("%s %08X" % kv for kv in at.items()), texts[0]))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
