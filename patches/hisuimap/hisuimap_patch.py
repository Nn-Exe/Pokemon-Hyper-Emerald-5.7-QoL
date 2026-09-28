"""Hisui on the Sinnoh Map (Hyper Emerald v5.7). Apply after the hypertrain build.
usage: python hisuimap_patch.py <in.gba> <out.gba>

Used anywhere in Hisui, the Sinnoh Map now shows a Hisui town map instead of saying there is no map: a
marker on the area you are in, the D-pad hops between the six places, A on a red square flies you there
with Mingyao's own Braviary script (the same one her menu runs), B leaves. Everywhere else it is the Sinnoh
Map exactly as before.

The screen is patches/sinnohmap's, rebuilt as regionmap.s to draw from a region record instead of fixed
addresses, and installed here as new code; the item's field-use pointer moves to it. Sinnoh's picture,
location table and courier table are NOT copied: the record points at them where the sinnohmap build put
them (found by content and checked), so the leaguefly patch's edit to that courier table still applies.
The old screen code stays in the ROM, unused; its overworld stub, which hands you the item, is still live.

Hisui is five 50x50 maps and the temple, 37/103..108, all in map section 104, so its tables are keyed by map
number instead of section (the patch checks nothing else uses 104). Its places and fly blocks:

    37/107 Snowfall Hot Spring   Mingyao 0x0989AE6F      37/103 Deertrack Heights   Mingyao 0x0989AE4D
    37/106 Coronet Highlands     Mingyao 0x0989AE80      37/104 Prelude Beach       Mingyao 0x0989AE3C
    37/105 Firespit Island       Mingyao 0x0989AE5E      37/108 Temple of Sinnoh    on foot, no fly

Each Mingyao block is `showmonpic Braviary; waitbuttonpress; hidemonpic; warp 37.<map> 1` with no flag check,
so every red square works from anywhere in Hisui, as her menu does: her Braviary appears, A, and you are there.

Also: the two destinations her menu (multichoice 137) still showed in Chinese are now "Deertrack Heights"
and "Snowfall Hot Spring".

The picture comes from tools/make_hisui_townmap.py (drawn in the Sinnoh map's palette from a Legends: Arceus
map) through tools/make_region_map.py: hisui.tiles.4bpp.lz, hisui.tilemap.bin.lz, hisui.palette.pal.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import sinnohmap_patch as SM                    # its text encoder, assembler check, marker tile and tables

FREE = 0x00FF3000                               # in the unreferenced 0xFF run 0x08FF2574..0x08FFD5A0
BASE = 0x08000000 + FREE
OLD = (0x08FDBC8C, 0x08FDE494)                  # the sinnohmap blob
ITEM = SM.ITEMS + SM.TOWN_MAP * 44
HISUI_SEC = 104
CURSOR_TILE = 511                               # last tile of BG1's character block: past either picture
CURSOR_VRAM = 0x06004000 + CURSOR_TILE * 32
CURSOR_ENTRY = CURSOR_TILE | (SM.CURSOR_PAL << 12)

# (map number, name, tile x, tile y, Mingyao's block or None), tiles as tools/make_hisui_townmap.py places them
PLACES = [
    (107, "Snowfall Hot Spring", 10, 4, 0x0989AE6F),
    (108, "Temple of Sinnoh", 15, 7, None),         # reached on foot from Coronet Highlands' summit
    (106, "Coronet Highlands", 15, 9, 0x0989AE80),
    (105, "Firespit Island", 26, 5, 0x0989AE5E),
    (103, "Deertrack Heights", 6, 12, 0x0989AE4D),
    (104, "Prelude Beach", 10, 14, 0x0989AE3C),
]

MINGYAO_LIST = 0x098031A8                       # multichoice 137: five {text, id} entries
MINGYAO_FIX = {1: (0x098365E1, "Deertrack Heights"), 3: (0x098365F3, "Snowfall Hot Spring")}


def u32(rom, a):
    return struct.unpack_from("<I", rom, a - 0x08000000)[0]


def find_once(rom, blob, what):
    lo, hi = OLD[0] - 0x08000000, OLD[1] - 0x08000000
    i = rom.find(blob, lo, hi)
    assert i >= 0, "the sinnohmap blob has no %s" % what
    assert rom.find(blob, i + 1, hi) < 0, "the sinnohmap blob has two copies of %s" % what
    return 0x08000000 + i


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000

    old_use = u32(rom, 0x08000000 + ITEM + 28)
    assert OLD[0] <= old_use < OLD[1], "the Sinnoh Map does not open the sinnohmap screen (%08X)" % old_use

    # Sinnoh: everything the old screen drew from, where it already is
    sd = os.path.join(HERE, "..", "sinnohmap")
    s_pal = find_once(rom, open(os.path.join(sd, "sinnoh.palette.pal"), "rb").read()[:13 * 32], "palette")
    tiles_lz = open(os.path.join(sd, "sinnoh.tiles.4bpp.lz"), "rb").read()
    s_tiles = find_once(rom, tiles_lz, "tile data")
    s_map = find_once(rom, open(os.path.join(sd, "sinnoh.tilemap.bin.lz"), "rb").read(), "tilemap")
    placed = {int(k): (v["x"], v["y"]) for k, v in json.load(open(os.path.join(sd, "locations.json"))).items()}
    placed.update(SM.INDOOR)
    s_loc = find_once(rom, b"".join(bytes((k, x, y)) for k, (x, y) in sorted(placed.items())) + b"\xFF", "location table")
    s_courier = find_once(rom, struct.pack("<BBHI", *((SM.COURIER[0][0], 0) + SM.COURIER[0][1:])), "courier table")
    assert rom[s_courier - 0x08000000 + 8 * len(SM.COURIER)] == 0xFF, "the courier table changed length"
    assert HISUI_SEC not in placed, "section %d is on the Sinnoh map" % HISUI_SEC

    hisui_tiles = open(os.path.join(HERE, "hisui.tiles.4bpp.lz"), "rb").read()
    for lz in (tiles_lz, hisui_tiles):
        n = (struct.unpack_from("<I", lz, 0)[0] >> 8) // 32
        assert n <= CURSOR_TILE, "%d tiles would run into the marker tile" % n

    # every Mingyao block: showmonpic, waitbuttonpress, hidemonpic, warp 37.<its map> - and nothing checked first
    for num, _, _, _, block in PLACES:
        if block is None: continue
        b = block - 0x08000000
        assert rom[b] == 0x75 and rom[b + 5:b + 7] == b"\x6D\x76", "Mingyao's block %08X changed" % block
        assert tuple(rom[b + 7:b + 10]) == (0x39, 37, num), "Mingyao's block %08X no longer warps to 37.%d" % (block, num)
    for i, (ptr, _) in MINGYAO_FIX.items():
        assert u32(rom, MINGYAO_LIST + 8 * i) == ptr, "Mingyao's option %d is not the untranslated text" % i

    def data_blob(base):
        d = bytearray(); a = {}
        def put(name, b, align=1):
            while len(d) % align: d.append(0)
            a[name] = base + len(d); d.extend(b)
        put("BGTEMPLATES", struct.pack("<HHHH", 0x01F0, 0, 0x11C5, 0), 4)   # BG0 text (map 31), BG1 map (char 1, map 28)
        put("WINTEMPLATES", bytes((0, 1, 0, 28, 2, 15)) + struct.pack("<H", 1)
                           + bytes((0, 1, 18, 28, 2, 15)) + struct.pack("<H", 57)
                           + bytes((0xFF, 0, 0, 0, 0, 0)) + struct.pack("<H", 0), 4)
        tp = [0] * 16
        tp[1], tp[2], tp[3] = 0x18C6, 0x7FFF, 0x4210     # box fill, text, shadow
        put("TEXTPAL", struct.pack("<16H", *tp), 4)
        put("COLORS_NORM", bytes((1, 2, 3)), 4)
        put("COLORS_DIM", bytes((1, 3, 1)), 4)
        cp = [0] * 16
        cp[1], cp[2] = 0x7FFF, 0x001F                    # marker white, corners red
        put("CURPAL", struct.pack("<16H", *cp), 4)
        put("CURTILE", SM.cursor_tile(), 4)
        put("STR_NOMAP", SM.text("No map for this region.")[:-1] + bytes((0xFC, 0x09, 0xFF)), 4)
        for num, name, _, _, _ in PLACES:
            put("NAME_%d" % num, SM.text(name))
        for i, (_, name) in MINGYAO_FIX.items():
            put("MINGYAO_%d" % i, SM.text(name))
        put("H_PAL", open(os.path.join(HERE, "hisui.palette.pal"), "rb").read()[:13 * 32], 4)
        put("H_TILES", hisui_tiles, 4)
        put("H_MAP", open(os.path.join(HERE, "hisui.tilemap.bin.lz"), "rb").read(), 4)
        put("H_LOC", b"".join(bytes((n, x, y)) for n, _, x, y, _ in PLACES) + b"\xFF")
        put("H_FLY", b"".join(struct.pack("<BBHI", n, 0, 0, blk) for n, _, _, _, blk in PLACES if blk) + b"\xFF", 4)
        put("H_NAMES", b"".join(struct.pack("<B3xI", n, a["NAME_%d" % n]) for n, *_ in PLACES) + b"\xFF", 4)
        put("REGION_SINNOH", struct.pack("<6I", s_pal, s_tiles, s_map, s_loc, s_courier, 0), 4)
        put("REGION_HISUI", struct.pack("<6I", a["H_PAL"], a["H_TILES"], a["H_MAP"], a["H_LOC"], a["H_FLY"], a["H_NAMES"]), 4)
        return bytes(d), a

    src = open(os.path.join(HERE, "regionmap.s"), encoding="ascii").read()
    src = src.replace("HISUI_SEC", str(HISUI_SEC))
    src = src.replace("CURSOR_VRAM", "0x%08X" % CURSOR_VRAM).replace("CURSOR_ENTRY", "0x%08X" % CURSOR_ENTRY)

    def assemble(addrs):
        s = src
        for k, v in sorted(addrs.items(), key=lambda kv: -len(kv[0])):     # longest first
            s = s.replace(k + "_ADDR", "0x%08X" % v)
        return SM.thumb(s, BASE)

    names = ("CB2_INIT", "CB2_MAIN", "VBLANK", "TASK", "WAIT_TASK", "FLY_CB", "FLY_TASK")
    _, ddum = data_blob(BASE)
    code, dis = assemble(dict(ddum, **{k: BASE for k in names}))
    code_len = (len(code) + 3) & ~3
    data, daddrs = data_blob(BASE + code_len)
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    # item_use, wait_task, where, cur_slot, cb2_init, cb2_main, vblank, copy_words, task,
    # snap, courier_for, fly_target, fly_cb, fly_task, slot_at, draw_name, print
    assert len(funcs) == 17, "unexpected function layout: %d pushes" % len(funcs)
    caddrs = {"CB2_INIT": funcs[4] | 1, "CB2_MAIN": funcs[5] | 1, "VBLANK": funcs[6] | 1, "TASK": funcs[8] | 1,
              "WAIT_TASK": funcs[1] | 1, "FLY_CB": funcs[12] | 1, "FLY_TASK": funcs[13] | 1}
    item_use = funcs[0] | 1
    code, _ = assemble(dict(daddrs, **caddrs))
    assert (len(code) + 3) & ~3 == code_len

    blob = bytearray(code) + bytes(code_len - len(code)) + data
    while len(blob) % 4: blob.append(0)
    end = FREE + len(blob)
    assert end <= 0x00FFD5A0 and set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    struct.pack_into("<I", rom, ITEM + 28, item_use)                  # the Sinnoh Map opens the new screen
    for i in MINGYAO_FIX:
        struct.pack_into("<I", rom, MINGYAO_LIST - 0x08000000 + 8 * i, daddrs["MINGYAO_%d" % i])
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X (item_use %08X, was %08X; cb2_init %08X), data @%08X, end %08X"
          % (len(code), BASE, item_use, old_use, caddrs["CB2_INIT"], BASE + code_len, 0x08000000 + end))
    print("  Sinnoh from the old blob: palette %08X tiles %08X tilemap %08X places %08X couriers %08X"
          % (s_pal, s_tiles, s_map, s_loc, s_courier))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
