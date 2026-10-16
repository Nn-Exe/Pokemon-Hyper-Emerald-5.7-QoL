"""Room for new species: the species tables grow from 1,200 to 1,280 slots (Hyper Emerald v5.7).
usage: python speciesx_patch.py <in.gba> <out.gba>

Apply LAST in the chain, after zhtext (which still writes species names into the old table), and before gen9.
It adds no Pokemon by itself: slots 1200-1279 are blank until another patch fills them.

Why: the hack has no free slot (1199 is the only blank one) and every species table is exactly 1,200 entries long
with the next table starting on the following byte. Twenty-three tables sit between 0x08F186E0 and 0x08F53700,
twenty of them too short (step 3 has the other three); the level-up pointers, the TM/HM and the move-tutor bit
tables are elsewhere and just as full.

What it does:
  1. copies each table to free space with 1,280 entries (the new ones blank) and rewrites every aligned word in
     the ROM that held the old table's address. The old tables stay where they are, untouched, so anything that
     still pointed at one would go on reading the same data for species below 1200;
  2. raises the species count where code holds it: nine sites, listed in COUNT_SITES;
  3. leaves alone what is already long enough: the two cry tables (indexed by cry id, ids from 388 up are unused),
     the species -> cry id table (indexed by species - 277, so it reaches 1476), and the ability table at
     0x097A0000 (zeros follow it; whoever adds a species writes its row there).

A word that equals a table address is only rewritten when it is the ROM header's or a literal that code loads
(inside CODE, with a pc-relative ldr in front of it that reads it). One match is neither, 0x09750000 inside
graphics data: it is left alone (NOT_POINTERS). Anything else stops the patcher, to be looked at.

The new tables go into zero-filled ROM, 0x0968D000 onward. This hack's upper 16 MB was padded with 0x00, not 0xFF:
megabytes of it between the author's own blocks, which sit at round addresses (0x09250000 dex entries, 0x09750000
tutor bits, 0x097A0000 abilities, 0x09D00000 the battle engine). NOTES, "Species tables: 1,200 -> 1,280", has how
the region was checked.
"""
import struct, sys

OLD_N, NEW_N = 1200, 1280
DEST, DEST_END = 0x0168D000, 0x016FFF00          # 0x0968D000..0x096FFF00, zero-filled

# name: (file offset, bytes an entry, words that point at it, indexed by species - 1, new entries are zero)
TABLES = [
    ("base stats",        0x0F186E0, 28, 74, False, True),
    ("front pictures",    0x0F20A20, 8, 43, False, False),
    ("back pictures",     0x0F22FA0, 8, 15, False, False),
    ("palettes",          0x0F25520, 8, 6, False, False),
    ("shiny palettes",    0x0F27AA0, 8, 3, False, False),
    ("icons",             0x0F2A020, 4, 3, False, False),
    ("icon palette ids",  0x0F2B2E0, 1, 13, False, True),
    ("names",             0x0F2B790, 11, 131, False, True),
    ("evolutions",        0x0F387C0, 40, 7, False, True),
    ("front coordinates", 0x0F44340, 4, 15, False, False),
    ("back coordinates",  0x0F45600, 4, 11, False, False),
    ("front anim ids",    0x0F468C0, 1, 4, True, True),
    ("anim delays",       0x0F46D70, 1, 2, True, True),
    ("footprints",        0x0F47220, 4, 1, False, False),
    ("elevation",         0x0F4F560, 1, 4, False, True),
    ("national dex no.",  0x0F50370, 2, 2, True, True),
    ("hoenn to national", 0x0F50CD0, 2, 2, False, True),
    ("hoenn dex no.",     0x0F51630, 2, 2, True, True),
    ("back anim sets",    0x0F51F90, 1, 1, False, True),
    ("front anim tables", 0x0F52440, 4, 5, False, False),
    ("level-up pointers", 0x1D89578, 4, 14, False, False),
    ("TM/HM bits",        0x0FCD8F4, 16, 4, False, True),
    ("tutor bits",        0x1750000, 16, 1, True, True),      # rows 0..1198; other data starts at row 1199
]
# base stats is the one table code also addresses by field: (file offset of the word, field offset)
FIELD_WORDS = [(0x06EB7C, 12), (0x06EBA0, 14), (0x070A08, 17), (0x070AA4, 17)]
# where a word equal to a table address is a literal of some code
CODE = [(0x0000000, 0x01DB680),      # the game's own code (its scripts and text follow, up to 0x082E7000)
        (0x02E7000, 0x02EA000),      # and its library routines
        (0x0FD5000, 0x0FFE000),      # the hack's item code and this project's blobs
        (0x1257000, 0x1259000),      # the hack's Pokedex code
        (0x1510000, 0x1512000),      # the hack's icon sprite code
        (0x1D00000, 0x1D8B000),      # the battle engine
        (0x1F00000, 0x1F10000),      # the hack's field code
        (0x1F80000, 0x2000000)]      # this project's blobs in the ROM's tail
# a word that equals a table address and is not a pointer: (file offset, table)
NOT_POINTERS = {0x12A14DC: "tutor bits"}          # 0x09750000 inside graphics data
# (file offset, what the bytes are now, how the count is held)
COUNT_SITES = [
    (0x0FD5D60, "9624e400", "imm8<<3"),    # compat bit test: species above the count learn nothing
    (0x0FD7C7C, "9624e400", "imm8<<3"),    # its twin, the one CanMonLearnTMHM and the tutors use
    (0x12582BA, "9625", "imm8<<3"),        # egg species: walk back through the evolution table (lsls is 3 insns on)
    (0x1D00210, "af040000", "count-1"),    # after a battle: which species a Mega goes back to
    (0x1D45370, "af040000", "count-1"),    # pre-evolution search
    (0x1F006DC, "af040000", "count-1"),    # pre-evolution search
    (0x1F01C80, "af040000", "count-1"),    # pre-evolution search
    (0x00DE860, "b0040000", "count"),      # SanitizeSpecies
    (0x1257F18, "b0040000", "count"),      # dex number -> species
]


def in_code(o):
    return any(lo <= o < hi for lo, hi in CODE)


def loaded_by_code(rom, off):
    """Is the word at this file offset a literal some `ldr rX, [pc, #n]` just before it loads? Words that only
    happen to look like an address (script bytes, sound data, compressed graphics) are not."""
    for back in range(2, 1026, 2):
        if off - back < 0:
            break
        insn = struct.unpack_from("<H", rom, off - back)[0]
        if insn >> 11 == 0b01001 and ((off - back + 4) & ~3) + (insn & 0xFF) * 4 == off:
            return True
    return False


def is_pointer(rom, off):
    """a word of the ROM header (0x100-0x1FF), or a literal of code"""
    return 0x100 <= off < 0x200 or (in_code(off) and loaded_by_code(rom, off))


def layout():
    """table name -> its file offset once the patch is in (gen9_patch.py writes its rows through this)"""
    pos, out = DEST, {}
    for name, old, size, expect, minus_one, zero in TABLES:
        out[name] = pos
        pos = (pos + size * NEW_N + 3) & ~3
    assert pos <= DEST_END
    return out


def build(inp, outp):
    with open(inp, "rb") as f:
        rom = bytearray(f.read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]

    # ---- the ROM is the one this was written for, and the patch is not there yet
    for hdr, name in ((0x128, "front pictures"), (0x12C, "back pictures"), (0x130, "palettes"),
                      (0x134, "shiny palettes"), (0x138, "icons"), (0x13C, "icon palette ids"), (0x144, "names"),
                      (0x1BC, "base stats")):
        old = next(t[1] for t in TABLES if t[0] == name)
        assert u32(hdr) == 0x08000000 + old, "%s is not at %08X: already applied, or another ROM" % (name, 0x08000000 + old)
    assert bytes(rom[0x0F186E0 + 28:0x0F186E0 + 34]) == bytes([45, 49, 49, 45, 65, 65]), "base stats: not Bulbasaur"
    assert u32(0x1B2390) == 0x09750000, "the tutor table's pointer moved"
    assert u32(0x06B698) == 0x09D73A81, "the ability lookup is not hooked where it was"
    assert not any(rom[0x17A0000 + 6 * OLD_N:0x17A0000 + 6 * NEW_N]), "something follows the ability table"
    assert NEW_N % 8 == 0 and NEW_N >> 3 < 256 and NEW_N - 277 <= OLD_N, "the count sites cannot hold this count"
    assert not any(rom[DEST:DEST_END]), "the target region is not empty"
    words = {}                                           # table address -> where the ROM holds it
    for i, v in enumerate(struct.unpack_from("<%dI" % (len(rom) // 4), rom)):
        if 0x08F00000 <= v < 0x08F60000 or v in (0x09D89578, 0x08FCD8F4, 0x09750000):
            words.setdefault(v, []).append(i * 4)
        elif 0x08000000 + DEST <= v < 0x08000000 + DEST_END:     # no code loads an address inside the target
            assert not is_pointer(rom, i * 4), "%08X points into the target region" % (0x08000000 + i * 4)

    for k, name in NOT_POINTERS.items():
        assert not is_pointer(rom, k), "%08X is listed as data and looks like a literal" % (0x08000000 + k)

    # ---- copy, lengthen, repoint
    where, moved, total = layout(), [], 0
    for name, old, size, expect, minus_one, zero in TABLES:
        base = 0x08000000 + old
        refs = [k for k in words.get(base, []) if NOT_POINTERS.get(k) != name]
        stray = [k for k in refs if not is_pointer(rom, k)]
        assert not stray, "%s: %s hold its address and are not in code" % (name, ["%08X" % (0x08000000 + k) for k in stray])
        assert len(refs) == expect, "%s: %d words point at it, %d expected" % (name, len(refs), expect)
        keep = OLD_N - 1 if minus_one else OLD_N
        blank = bytes(size) if zero else bytes(rom[old:old + size])
        if name == "names":
            blank = b"\xff" + bytes(10)
        new = where[name]
        data = bytes(rom[old:old + size * keep]) + blank * (NEW_N - keep)
        rom[new:new + len(data)] = data
        pos = new + len(data)
        for k in refs:
            struct.pack_into("<I", rom, k, 0x08000000 + new)
        if name == "base stats":
            inside = sorted(k for v, ks in words.items() if base < v < base + size for k in ks if is_pointer(rom, k))
            assert inside == [k for k, _ in FIELD_WORDS], "base stats: field words are not the known four"
            for k, field in FIELD_WORDS:
                assert u32(k) == base + field
                struct.pack_into("<I", rom, k, 0x08000000 + new + field)
            total += len(FIELD_WORDS)
        total += len(refs)
        moved.append((name, base, 0x08000000 + new, size))

    # ---- the species count
    for off, was, how in COUNT_SITES:
        assert bytes(rom[off:off + len(was) // 2]) == bytes.fromhex(was), "count site %08X changed" % (0x08000000 + off)
        if how == "imm8<<3":
            rom[off] = NEW_N >> 3
        else:
            struct.pack_into("<I", rom, off, NEW_N - (1 if how == "count-1" else 0))
    assert bytes(rom[0x12582C0:0x12582C2]) == bytes.fromhex("ed00"), "the egg-species loop's shift moved"

    with open(outp, "wb") as f:
        f.write(rom)
    for name, was, now, size in moved:
        print("  %-18s %08X -> %08X  (%d x %d)" % (name, was, now, size, NEW_N))
    print("speciesx: %d tables at %08X..%08X, %d words repointed, the count %d -> %d at %d sites" % (
        len(moved), 0x08000000 + DEST, 0x08000000 + pos, total, OLD_N, NEW_N, len(COUNT_SITES)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
