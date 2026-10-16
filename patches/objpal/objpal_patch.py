"""Objects' sprite palettes given back (Hyper Emerald v5.7). Apply anywhere before zhtext.
usage: python objpal_patch.py <in.gba> <out.gba>

A bug of the hack's own. The hack gives an object (a person, a Pokemon, an item ball) its sprite palette by tag
(0x094A356A, called from its two hooks at 0x094A3356 and 0x094A3362: spawning an object, and changing an object's
graphics): the slot 4-9 that holds the tag already, else an empty one, else slot 10 whatever is in it. Nothing is
given back until the field is loaded again (a warp, a battle, a menu that leaves the field). So on one visit to a
map six kinds of thing get a slot of their own and every kind after that gets slot 10, which is no good at all:
something of the hack's writes it again (the reflections: it held a copy of slot 4's colours) and the eighth kind
takes its tag from the seventh. Whatever stands there in slot 10 shows borrowed colours. Found by a player of the
Area Zero test build (Walking Wake, above a waterfall, in a crystal's colours after a walk past six other kinds);
in the game itself eight maps have more than six kinds (35/49, 37/104, 35/87, 35/40, 35/8, 34/94, 26/40, 34/42).

The new allocator (objpal.s) takes slot 10 only when every slot 4-9 is drawn with by a sprite in use: a thing that
has gone out of sight has no sprite, so its slot is given to the next kind that comes. Up to six kinds on screen
at once (the screen and its margin, where objects are kept) always have their own colours.

  * the hack's function: its first 10 bytes become a jump to ours (`ldr r3, [pc, #4]; bx r3; mov r8, r8; .word`:
    it is 2 past a word; r3 is free at a call), the rest is left as it is and no longer runs;
  * ours (132 bytes) at 0x08FEF600, in the unreferenced 0xFF run 0x08FED3C8..0x08FEFE00 (the Quest Log's blob
    ends at 0x08FED3C8 and may grow, berrynum starts at 0x08FEFE00); nothing points into it, in this ROM and in
    the Gen 9 and Area Zero test builds made from it.

`applied(rom)` says where the allocator is when a ROM has it already: patches/paldea/objpal.py, which brought the
same fix to the Area Zero test build first, then leaves it as it is.
"""
import os, re, struct, sys

from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

ALLOC = 0x094A356A                              # the hack's allocator (r0 = tag -> r0 = slot)
ALLOC_WAS = bytes.fromhex("70b50a4e31000500")   # push {r4-r6, lr}; ldr r6, =tags; movs r1, r6; movs r5, r0
JUMP = bytes.fromhex("014b1847c046")            # ldr r3, [pc, #4]; bx r3; mov r8, r8; then the word
CALLERS = (0x094A3356, 0x094A3362)              # its two bl
TAGS = 0x03000CF0                               # sSpritePaletteTags
SPRITES = 0x02020630                            # gSprites
LOAD = 0x0808E91D                               # the hack's: load a tag's palette into a slot (r0 = tag, r1 = slot)
LOAD_WAS = bytes.fromhex("10b50c1c0004000c2406240e")   # push {r4, lr}; adds r4, r1, #0; tag and slot to u16 / u8
FREE, FREE_END = 0x00FEF600, 0x00FEF6E0         # (words in graphics data happen to read 0x08FEF6EB and on)


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
    return code, dis


def assemble(base):
    """objpal.s at `base` (a word): its pool of four words starts on a word, a mov r8, r8 in front if need be."""
    assert base % 4 == 0
    src = open(os.path.join(HERE, "objpal.s"), encoding="ascii").read()
    for pad in ("", "    mov r8, r8"):
        s = src.replace("PAD", pad).replace("TAGS_ADDR", hex(TAGS)).replace("LOAD_ADDR", hex(LOAD)) \
            .replace("SPRITES_ADDR", hex(SPRITES))
        code, dis = thumb(s, base)
        if (len(code) - 16) % 4 == 0:
            break
    else:
        raise AssertionError("objpal's pool")
    assert struct.unpack_from("<4I", code, len(code) - 16) == (TAGS, 0xFFFF, LOAD, SPRITES)
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    assert funcs == [base], "expected one function with a push, at the start"
    return code


def applied(rom):
    """The allocator's address if this ROM has the fix (the hack's function jumps to it), else None."""
    o = ALLOC - 0x08000000
    if bytes(rom[o:o + 6]) != JUMP:
        return None
    at = struct.unpack_from("<I", rom, o + 6)[0] & ~1
    code = assemble(at)
    assert bytes(rom[at - 0x08000000:at - 0x08000000 + len(code)]) == code, "a jump at the allocator, but not to objpal"
    return at


def check_site(rom):
    """The hack's allocator and its callers as this patch expects them."""
    o = ALLOC - 0x08000000
    assert bytes(rom[o:o + 8]) == ALLOC_WAS, "the hack's palette allocator is not as expected (already applied?): %s" % (
        bytes(rom[o:o + 8]).hex())
    for c in CALLERS:
        h1, h2 = struct.unpack_from("<HH", rom, c - 0x08000000)
        off = ((h1 & 0x7FF) << 12) | ((h2 & 0x7FF) << 1)
        off -= 0x800000 if off & 0x400000 else 0
        assert h1 & 0xF800 == 0xF000 and h2 & 0xF800 == 0xF800 and c + 4 + off == ALLOC, \
            "%08X does not call the allocator" % c
    assert struct.unpack_from("<I", rom, o + 0x2E)[0] == TAGS, "the allocator's table is not sSpritePaletteTags"
    assert struct.unpack_from("<I", rom, o + 0x36)[0] == LOAD, "the allocator does not load with %08X" % LOAD
    assert bytes(rom[LOAD - 1 - 0x08000000:LOAD - 1 - 0x08000000 + 12]) == LOAD_WAS, "the palette loader changed"


def point(rom, at):
    """The hack's allocator jumps to ours at `at`."""
    o = ALLOC - 0x08000000
    assert ALLOC % 4 == 2
    rom[o:o + 10] = JUMP + struct.pack("<I", at | 1)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    check_site(rom)
    base = 0x08000000 + FREE
    code = assemble(base)
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not base <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code
    point(rom, base)
    assert applied(rom) == base
    open(outp, "wb").write(rom)
    print("objpal: the allocator %08X..%08X (%d bytes), the hack's %08X jumps to it" % (
        base, 0x08000000 + end, len(code), ALLOC))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
