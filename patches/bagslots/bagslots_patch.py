"""Items pocket 100 -> 200 slots (Hyper Emerald v5.7). Apply last.
usage: python bagslots_patch.py <in.gba> <out.gba>

The Bag's pockets are the hack's own: 0x08FD7EA4 (SetBagItemsPointers' trampoline word 0x080D65F4) packs Items
100, Key Items 50, Poke Balls 32, TMs 130 and Berries 50 back to back from EWRAM 0x0203D030. They are saved in
the hack's "overflow stream": every save sector is filled to 0xFF0, and the bytes after the vanilla data carry
EWRAM 0x0203CF64 onward in sector order (writer 0x092582FC, loader 0x09258444, HandleReplaceSector patched at
0x08152B00) - 3,740 bytes, to 0x0203DE00. Right after the pockets the hack keeps stored Pokemon (0x0203D5E0,
0x0203D644, 0x0203D800) and flags (0x0203D900/904); the stream's last 1.2 KB have no reader at all.

* Items moves to NEW (200 slots = 800 bytes, ending exactly at the stream's end, in sector 13's spare bytes):
  set_ptrs runs the hack's layout, then points gBagPockets[0] there. The other pockets do not move.
* load_slot (CopySaveSlotData's word 0x08152E14) copies an old save's 100 slots over once, when MARKER is not
  set, and zeroes the other 100. The old copy stays where it was (an older build would still see it).
* clear_bag (ClearBag, called only by NewGameInitData) is the game's loop plus: empty the old area, set MARKER.
* The Bag's list buffers (the hack's allocator 0x08FD7F38) grow from ~150 rows to 202 / 202 names.
Limits: the pocket's capacity and the Bag's row count (Cancel included) are u8, so 254 is the ceiling.
Frontier/link saves (SAVE_LINK) write sectors 0-4 only; the Poke Balls, TMs and Berries pockets were already
past sector 4, and single-player makes those saves only mid-challenge, when the Bag cannot change.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import sinnohmap_patch as SM                    # the Thumb check

FREE = 0x00FF6000                               # in the unreferenced 0xFF run 0x08FF5C35..0x08FFD5A0 (after expshare)
FREE_END = 0x00FF6600                           # three data words point at 0x08FF6673.. - stay clear of them
BASE = 0x08000000 + FREE

POCKETS = 0x02039DD8
STREAM, STREAM_END = 0x0203CF64, 0x0203DE00
OLD, OLD_COUNT = 0x0203D030, 100
NEW_COUNT = 200
NEW = STREAM_END - NEW_COUNT * 4                # 0x0203DAE0
MARKER = NEW - 4                                # 0x0203DADC
MAGIC = 0x32474142                              # "BAG2"
FREE_STREAM = 0x0203D908                        # past the hack's last user (flags at 0x0203D900/904)

SETPTRS_WORD, ORIG_PTRS = 0x080D65F4, 0x08FD7EA5
LOAD_WORD, ORIG_LOAD = 0x08152E14, 0x09258445
WRITE_WORD, ORIG_WRITE = 0x081527A4, 0x092582FD
CLEARBAG = 0x080D7094
ALLOC = 0x08FD7F38
ALLOC_NAMES_LIT = 0x08FD7F60
LIST_ROWS = NEW_COUNT + 2                       # the rows + Cancel, one spare
ROW_BYTES, NAME_BYTES = 8, 24                   # ListMenuItem; LoadBagItemListBuffers' name stride
SLOT_LAYOUT_LDR = 0x08153196                    # UpdateSaveAddresses: ldr r2, =sSaveSlotLayout
# words that look like pointers into the new area but sit in compressed graphics (checked by hand)
KNOWN_DATA = {0x08D26000}


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u16 = lambda a: struct.unpack_from("<H", rom, o(a))[0]
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]

    # the hack's pocket layout, as this patch expects it
    assert u16(SETPTRS_WORD - 4) == 0x4800 and u16(SETPTRS_WORD - 2) == 0x4700, "SetBagItemsPointers is not a trampoline"
    assert u32(SETPTRS_WORD) == ORIG_PTRS, "SetBagItemsPointers no longer goes to the hack's layout"
    p = ORIG_PTRS - 1
    assert rom[o(p + 0x16):o(p + 0x1C)] == bytes.fromhex("1e2122006420"), "the Items pocket is not 100 slots"
    assert u32(p + 0x8C) == POCKETS and u32(p + 0x90) == OLD, "the pockets do not start at 0x0203D030"

    # the save's overflow stream: loader, writer, and its length from the save slot layout
    assert u16(LOAD_WORD - 4) == 0x4900 and u16(LOAD_WORD - 2) == 0x4708 and u32(LOAD_WORD) == ORIG_LOAD
    assert u16(WRITE_WORD - 4) == 0x4900 and u16(WRITE_WORD - 2) == 0x4708 and u32(WRITE_WORD) == ORIG_WRITE
    assert u32(0x09258424) == STREAM and u32(0x09258560) == STREAM, "the stream does not start at 0x0203CF64"
    ins = u16(SLOT_LAYOUT_LDR)
    assert ins >> 11 == 9
    layout = u32(((SLOT_LAYOUT_LDR + 4) & ~3) + (ins & 0xFF) * 4)
    sizes = [struct.unpack_from("<HH", rom, o(layout) + 4 * i)[1] for i in range(14)]
    assert STREAM + sum(0xFF0 - s for s in sizes) == STREAM_END, "the stream is not 3,740 bytes: %s" % sizes

    # nothing else knows the new area
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        if FREE_STREAM <= v < STREAM_END:
            assert 0x08000000 + k in KNOWN_DATA, "%08X points into the new area (%08X)" % (0x08000000 + k, v)

    # ClearBag: still the game's own
    assert rom[o(CLEARBAG):o(CLEARBAG) + 12] == bytes.fromhex("30b50024074de10049190868"), "ClearBag changed"
    assert u32(CLEARBAG + 0x24) == POCKETS

    # the Bag's list buffers (the hack's allocator): Alloc(0x9C << 3) rows, Alloc(0xE22) names
    assert rom[o(ALLOC):o(ALLOC) + 6] == bytes.fromhex("9c2070b5c000"), "the list allocator changed"
    assert u32(ALLOC_NAMES_LIT) == 0xE22 and u32(ALLOC + 0x20) == 0x08000B39
    ins = u16(ALLOC + 0x10)
    assert ins >> 11 == 9 and ((ALLOC + 0x10 + 4) & ~3) + (ins & 0xFF) * 4 == ALLOC_NAMES_LIT
    readers = [a for a in range(o(ALLOC_NAMES_LIT) - 1020, o(ALLOC_NAMES_LIT), 2)
               if u16(0x08000000 + a) >> 11 == 9
               and ((a + 4) & ~3) + (u16(0x08000000 + a) & 0xFF) * 4 == o(ALLOC_NAMES_LIT)]
    assert readers == [o(ALLOC + 0x10)], "the names size has other readers"
    rows = (LIST_ROWS * ROW_BYTES + 7) >> 3
    assert rows <= 0xFF
    names = (LIST_ROWS * NAME_BYTES + 0xFF) & ~0xFF

    src = open(os.path.join(HERE, "bagslots.s"), encoding="ascii").read()
    for k, v in (("ORIG_PTRS_ADDR", ORIG_PTRS), ("ORIG_LOAD_ADDR", ORIG_LOAD), ("NEW_ADDR", NEW),
                 ("OLD_ADDR", OLD), ("MARKER_ADDR", MARKER), ("MAGIC_ADDR", MAGIC)):
        src = src.replace(k, "0x%08X" % v)
    src = src.replace("#NEW_COUNT", "#%d" % NEW_COUNT).replace("#OLD_COUNT", "#%d" % OLD_COUNT)
    code, dis = SM.thumb(src, BASE)
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    assert len(funcs) == 3, "expected set_ptrs, load_slot and clear_bag, found %d functions" % len(funcs)
    set_ptrs, load_slot, clear_bag = (f | 1 for f in funcs)
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = code

    struct.pack_into("<I", rom, o(SETPTRS_WORD), set_ptrs)
    struct.pack_into("<I", rom, o(LOAD_WORD), load_slot)
    rom[o(CLEARBAG):o(CLEARBAG) + 8] = bytes.fromhex("004b1847") + struct.pack("<I", clear_bag)
    rom[o(ALLOC)] = rows
    struct.pack_into("<I", rom, o(ALLOC_NAMES_LIT), names)
    open(outp, "wb").write(rom)
    print("set_ptrs %08X, load_slot %08X, clear_bag %08X, end %08X; Items %d slots at %08X, marker %08X; "
          "list buffers %d rows / %d bytes of names"
          % (set_ptrs, load_slot, clear_bag, 0x08000000 + end, NEW_COUNT, NEW, MARKER, rows, names))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
