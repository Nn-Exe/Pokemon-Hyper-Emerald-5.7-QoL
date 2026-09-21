"""Sinnoh map screen (Hyper Emerald v5.7). Apply after the newsfix build.
usage: python sinnohmap_patch.py <in.gba> <out.gba>

The Town Map key item, which this hack has but never made do anything, is renamed Sinnoh Map in place
(same 14-byte field, nothing repointed) and opens our own screen: the Sinnoh
picture drawn from free space, a blinking marker on the area you are in, its name in a box, B to leave.
You are handed the item the first time you reach the overworld.

Nothing the Hoenn region map or Fly depend on is touched: not gRegionMapEntries, not the region map's
graphics, not its code. The picture, palettes, location table and code are new bytes in free space. The
only existing bytes that change are the Town Map's field-use pointer in the item table and the overworld
trampoline (already ours, from the both-bikes patch, re-chained so both run).

The start menu would have been the nicer home, but its action list is exactly nine bytes and the game
appends to it without a bounds check, so a tenth entry corrupts the variable that follows it.

Data comes from tools/make_region_map.py: 4bpp tiles and a 32x32 tilemap, LZ77-compressed exactly the way
the game stores its own backgrounds, decompressed straight into video memory when the screen opens.
"""
import json, os, re, struct, sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FDBC8C
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

OW_HOOK = 0x085E5C                          # CB2_Overworld, trampolined by the both-bikes patch
ITEMS = 0xFC2C7C
TOWN_MAP = 361
VRAM_TILES = 0x06004000                     # BG1 character base 1
CURSOR_PAL = 13                             # the map can use 0..12, so the marker sits above them

CHARS = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARS.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({" ": 0x00, ".": 0xAD, "-": 0xAE, "'": 0xB4})

# The couriers' own table, read off their shared script (0x0987CD9D): for each town, the flag they check
# before agreeing to take you there, and the block of THEIR script that does the fade and the warp.
# We run that block; we never warp on our own.
COURIER = [  # mapsec, visited flag, script block
    (111, 0x4194, 0x0987CE7E), (112, 0x4195, 0x0987D038), (91, 0x4196, 0x0987D051), (92, 0x4197, 0x0987D06A),
    (93, 0x4198, 0x0987D083), (95, 0x4199, 0x0987D09C), (96, 0x419A, 0x0987D0B5), (53, 0x419B, 0x0987D0CE),
    (98, 0x42E3, 0x0987D0E7), (94, 0x42E4, 0x0987D100), (143, 0x42E5, 0x0987D119), (144, 0x42E6, 0x0987D132),
    (145, 0x42E7, 0x0987D14B), (146, 0x42E8, 0x0987D164), (127, 0x42E9, 0x0987D17D), (97, 0x42EA, 0x0987D196)]

# Areas that are indoors, so they never appear on the rendered surface. Placed next to the place they
# belong to, so the map still opens and points somewhere sensible while you are inside.
INDOOR = {127: (12, 10), 133: (12, 9), 147: (3, 17), 148: (22, 15), 149: (11, 3), 160: (8, 9),
          122: (1, 12), 128: (8, 14), 134: (9, 16), 169: (7, 15), 179: (18, 15), 167: (23, 13),
          166: (9, 9), 126: (23, 12), 150: (12, 11)}


def text(s, raw=b""):
    return raw + bytes(CHARS[c] for c in s) + bytes([0xFF])


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 nop\n    nop", src, flags=re.M), addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code, dis


def cursor_tile():
    """8x8, 4bpp: a hollow square, colour 1 with colour 2 corners."""
    px = [[0] * 8 for _ in range(8)]
    for i in range(8):
        px[0][i] = px[7][i] = px[i][0] = px[i][7] = 1
    for y, x in ((0, 0), (0, 7), (7, 0), (7, 7)):
        px[y][x] = 2
    out = bytearray()
    for y in range(8):
        for x in range(0, 8, 2):
            out.append(px[y][x] | (px[y][x + 1] << 4))
    return bytes(out)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000

    # the both-bikes patch must already be in: chain ahead of the stub its trampoline points at
    assert rom[OW_HOOK:OW_HOOK + 4] == bytes.fromhex("004b1847"), "the overworld hook is not ours"
    bike_stub = struct.unpack_from("<I", rom, OW_HOOK + 4)[0]
    assert 0x08FD0000 <= bike_stub < 0x08FE0000, "unexpected overworld stub %08X" % bike_stub

    e = ITEMS + TOWN_MAP * 44
    raw = rom[e:e + 14]
    raw = raw[:raw.index(0xFF)] if 0xFF in raw else raw
    name = "".join(chr(65 + c - 0xBB) if 0xBB <= c <= 0xD4 else chr(97 + c - 0xD5) if 0xD5 <= c <= 0xEE
                   else " " for c in raw).strip()
    assert name.startswith("Town Map"), "item %d is %r, expected the Town Map" % (TOWN_MAP, name)
    new_name = text("Sinnoh Map")                       # 11 bytes of the field's 14: renamed in place
    assert struct.unpack_from("<I", rom, e + 28)[0] == 0x080FE821, "the Town Map already does something"
    assert rom[e + 26] == 5, "the Town Map is not a key item"

    tiles_lz = open(os.path.join(HERE, "sinnoh.tiles.4bpp.lz"), "rb").read()
    map_lz = open(os.path.join(HERE, "sinnoh.tilemap.bin.lz"), "rb").read()
    pal = open(os.path.join(HERE, "sinnoh.palette.pal"), "rb").read()[:13 * 32]
    ntiles = (struct.unpack_from("<I", tiles_lz, 0)[0] >> 8) // 32
    assert ntiles <= 500, "too many tiles for one character block: %d" % ntiles

    # every courier block must still start "checkflag <its flag>" and warp into map group 36
    for sec, flag, block in COURIER:
        b = block - 0x08000000
        assert rom[b] == 0x2B and struct.unpack_from("<H", rom, b + 1)[0] == flag, "courier block %08X changed" % block
        assert rom[b + 14] == 0x39 and rom[b + 15] == 36, "courier block %08X no longer warps into Sinnoh" % block
    courier_bytes = b"".join(struct.pack("<BBHI", sec, 0, flag, block) for sec, flag, block in COURIER) + bytes([0xFF])

    loc = json.load(open(os.path.join(HERE, "locations.json")))
    table_bytes = bytearray()
    placed = {}
    for sec, v in sorted(loc.items(), key=lambda kv: int(kv[0])):
        placed[int(sec)] = (v["x"], v["y"])
    placed.update(INDOOR)
    for sec, (x, y) in sorted(placed.items()):
        assert 0 <= sec < 0xFF and 0 <= x < 30 and 0 <= y < 20, "bad location entry %s" % sec
        table_bytes += bytes((sec, x, y))
    table_bytes += b"\xFF"

    def data_blob(base):
        d = bytearray(); a = {}
        def put(name, b, align=1):
            while len(d) % align: d.append(0)
            a[name] = base + len(d); d.extend(b)
        put("BGTEMPLATES", struct.pack("<HHHH", 0x01F0, 0, 0x11C5, 0), 4)   # BG0 text (map 31), BG1 map (char 1, map 28)
        # two name boxes, one along the top and one along the bottom; the screen shows whichever
        # is not sitting on top of the marker
        put("WINTEMPLATES", bytes((0, 1, 0, 28, 2, 15)) + struct.pack("<H", 1)
                           + bytes((0, 1, 18, 28, 2, 15)) + struct.pack("<H", 57)
                           + bytes((0xFF, 0, 0, 0, 0, 0)) + struct.pack("<H", 0), 4)
        tp = [0] * 16
        tp[1] = 0x18C6          # box fill: near-black
        tp[2] = 0x7FFF          # text: white
        tp[3] = 0x4210          # shadow
        put("TEXTPAL", struct.pack("<16H", *tp), 4)
        put("COLORS_NORM", bytes((1, 2, 3)), 4)
        put("COLORS_DIM", bytes((1, 3, 1)), 4)          # greyed: a courier town you have not reached
        put("COURIER", courier_bytes, 4)
        cp = [0] * 16
        cp[1] = 0x7FFF          # marker: white
        cp[2] = 0x001F          # corners: red
        put("CURPAL", struct.pack("<16H", *cp), 4)
        put("CURTILE", cursor_tile(), 4)
        put("MAPPAL", pal, 4)
        put("MAPTILES", tiles_lz, 4)
        put("MAPTILEMAP", map_lz, 4)
        put("LOCTABLE", bytes(table_bytes), 4)
        put("STR_NOMAP", text("No map for this region.")[:-1] + bytes((0xFC, 0x09, 0xFF)), 4)
        return bytes(d), a

    src = open(os.path.join(HERE, "sinnohmap.s"), encoding="ascii").read()

    def assemble(code_addrs, data_addrs):
        s = src
        s = s.replace("CURSOR_VRAM", "0x%08X" % (VRAM_TILES + ntiles * 32))
        s = s.replace("CURSOR_ENTRY", "0x%08X" % (ntiles | (CURSOR_PAL << 12)))
        s = s.replace("BIKE_STUB", "0x%08X" % bike_stub)
        # longest first: TASK_ADDR would otherwise eat the tail of WAIT_TASK_ADDR
        for k, v in sorted(list(code_addrs.items()) + list(data_addrs.items()), key=lambda kv: -len(kv[0])):
            s = s.replace(k + "_ADDR", "0x%08X" % v)
        return thumb(s, BASE)

    dummy = {k: BASE for k in ("CB2_INIT", "CB2_MAIN", "VBLANK", "TASK", "WAIT_TASK", "FLY_CB", "FLY_TASK")}
    _, ddum = data_blob(BASE)
    code, dis = assemble(dummy, ddum)
    code_len = (len(code) + 3) & ~3
    data, daddrs = data_blob(BASE + code_len)
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    # ow_stub, item_use, wait_task, cur_slot, cb2_init, cb2_main, vblank, copy_words, task,
    # snap, courier_for, fly_target, fly_cb, fly_task, slot_at, draw_name, print
    assert len(funcs) == 17, "unexpected function layout: %d pushes" % len(funcs)
    caddrs = {"CB2_INIT": funcs[4] | 1, "CB2_MAIN": funcs[5] | 1, "VBLANK": funcs[6] | 1,
              "TASK": funcs[8] | 1, "WAIT_TASK": funcs[2] | 1, "FLY_CB": funcs[12] | 1, "FLY_TASK": funcs[13] | 1}
    item_use = funcs[1] | 1
    code, _ = assemble(caddrs, daddrs)
    assert (len(code) + 3) & ~3 == code_len

    blob = bytearray(code) + bytes(code_len - len(code)) + data
    while len(blob) % 4: blob.append(0)
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    assert len(new_name) <= 14, "%r does not fit the item name field" % new_name
    rom[e:e + 14] = new_name + bytes(14 - len(new_name))  # same field, same length, nothing repointed
    struct.pack_into("<I", rom, e + 28, item_use)         # and it now opens our screen
    struct.pack_into("<I", rom, OW_HOOK + 4, BASE | 1)     # and the overworld hands it to you
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X (item_use %08X, cb2_init %08X, task %08X), data @%08X"
          % (len(code), BASE, item_use, caddrs["CB2_INIT"], caddrs["TASK"], BASE + code_len))
    print("  %d map tiles, %d locations, chaining to the both-bikes stub at %08X, end %08X"
          % (ntiles, len(placed), bike_stub, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
