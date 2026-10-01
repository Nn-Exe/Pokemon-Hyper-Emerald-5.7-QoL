"""The DexNav screen, redrawn after Pokemon Unbound's (Hyper Emerald v5.7). Apply after dexnav, dexnavchain,
dexnavseen and dexnavscan.
usage: python dexnavui_patch.py <in.gba> <out.gba>

The DexNav's start-menu callback (the START menu's DexNav and R in the field both go through it) sets its screen's
CB2 from one literal, 0x08FDA514; that literal now points at this screen's init (dexnavui.s). The old list screen
stays in the ROM, unused. Screen 0 shows Water (5 cells) over Land (6x2), screen 1 Rock Smash (5) over Fishing
(5x2) - a map's encounter header has 12 / 5 / 5 / 10 slots, so two screens always hold everything. The art is
drawn by art.py and cut into 4bpp tiles here; the type labels are the summary screen's own sheet and palettes.
Everything is written to 0x09FD8000.. (a 20 KB stretch of 0xFF with no pointer into it).
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavseen"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
import art
import sinnohmap_patch as SM                    # the Thumb check
from dexnavseen_patch import bl_target
from inserter import ENC

FREE, FREE_END = 0x01FD8000, 0x01FDD000
BASE = 0x08000000 + FREE

CB2_INIT_LIT, OLD_CB2_INIT = 0x08FDA514, 0x08FDA267    # in the DexNav's pool: what its menu callback sets
MENU_CALLBACK = 0x08FDA238
FIND, FIND_CALL, OLD_FIND_HEADER = 0x08FDA790, 0x08FDA7A2, 0x08FDA760
ARM_SEARCH, CHAIN_BREAK, SL_GET, CB2_RETURN = 0x08FDE89A, 0x08FDE5CC, 0x08FDF10A, 0x08FDE884
STATE = 0x0203A660
RING_TAG, SHADOW_TAG = 0x5E65, 0x5E64
SECTION_ORDER = ("land", "water", "rock", "fish")      # find()'s habitat numbers 0-3


def enc(s):
    return bytes(ENC[c] for c in s)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    # what this screen stands on
    assert u32(CB2_INIT_LIT) == OLD_CB2_INIT, "the DexNav's menu callback no longer sets the old screen"
    assert at(MENU_CALLBACK, "00b5") and at(OLD_CB2_INIT - 1, "30b5"), "the DexNav blob moved"
    refs = [k for k in range(0, len(rom), 4) if struct.unpack_from("<I", rom, k)[0] == OLD_CB2_INIT]
    assert refs == [o(CB2_INIT_LIT)], "the old screen's init has other users: %s" % refs
    assert at(FIND, "f0b585b0041c"), "find moved"
    assert bl_target(rom, FIND_CALL) != OLD_FIND_HEADER, "dexnavscan is not applied: the Battle Pyramid's table would come back"
    assert at(ARM_SEARCH, "70b51e1c") and at(CHAIN_BREAK, "10b50a4c"), "arm_search / chain_break moved"
    assert at(SL_GET, "10b5041c") and at(CB2_RETURN, "00b5"), "sl_get / cb2_return moved"
    assert u32(0x0861CFBC) == 0x090D0000 and u32(0x0861CFC4) == 0x75327532, "the summary's type labels moved"
    for a, pro in ((0x08001944, "f0b5"), (0x080019FC, "10b5"), (0x080039DC, "f0b5"), (0x08006DF4, "f0b5"),
                   (0x080084F8, "70b5"), (0x08034530, "30b5"), (0x080A18F4, "70b5"), (0x08008CC0, "f0b5"),
                   (0x081DB35C, "00b5"), (0x0812456C, "30b5"), (0x08008744, "30b5"), (0x08003B64, "70b5"),
                   (0x08001D04, "70b5"), (0x08001E7C, "70b5")):
        assert at(a, pro), "%08X is not the function this screen expects" % a

    # ---- the data -------------------------------------------------------------------------------------
    tiles, maps, ntiles = art.tiles_and_maps()
    data = bytearray()
    addr = {}

    def put(name, blob, align=4):
        while len(data) % align:
            data.append(0)
        addr[name] = len(data)                  # offset for now; made absolute once the code's size is known
        data.extend(blob)

    put("TILES", tiles)
    put("MAP0", maps[0])
    put("MAP1", maps[1])
    put("ARTPAL", art.palette())
    textpal = [(0, 0, 0), (248, 248, 248), (64, 64, 72), (48, 48, 56), (200, 200, 208), (168, 168, 176), (144, 144, 152)]
    put("TEXTPAL", struct.pack("<16H", *([art.bgr555(c) for c in textpal] + [0] * 9)))
    put("HABPAL", b"".join(art.colours3(art.HABITAT[s]) for s in SECTION_ORDER))
    put("BTNPAL", b"".join(art.colours3(art.BUTTON[k]) for k in ("go", "stop", "off")))
    put("XMARK", art.x_mark())
    ring, ringpal = art.cursor_sprite()
    put("RINGTILES", ring)
    put("RINGPALDATA", ringpal)
    put("SHADOWDATA", bytes(32))                # colour 0 transparent, 1-15 black
    put("RINGOAM", bytes.fromhex("0000008000040000"))       # 32x32, priority 1
    put("BGTPL", struct.pack("<2I", 0x000001F0, 0x000021E9))
    put("WINTPL", bytes([0, 0, 0, 30, 20, 15]) + struct.pack("<H", 1) + bytes([0xFF, 0, 0, 0, 0, 0, 0, 0]))
    xs, ys = [], []
    for screen in (0, 1):
        cells = art.layout(screen)[2]
        cells += [(0, 0)] * (17 - len(cells))
        xs += [c[0] for c in cells]
        ys += [c[1] for c in cells]
    put("SLOTX", bytes(xs), 1)
    put("SLOTY", bytes(ys), 1)
    put("SECA", bytes([1, 2]), 1)               # the top box: water / Rock Smash
    put("SECB", bytes([0, 3]), 1)               # the bottom box: land / fishing
    put("COLSB", bytes([6, 5]), 1)
    put("SECBASE", bytes([16, 64, 84, 104]), 1)
    put("SECCAP", bytes([12, 5, 5, 10]), 1)
    put("C_LIGHT", bytes([0, 1, 2]), 1)
    put("C_DARK", bytes([0, 3, 4]), 1)
    put("C_DIM", bytes([0, 6, 4]), 1)
    strings = {"S_WATER": "WATER", "S_LAND": "LAND", "S_ROCK": "ROCK SMASH", "S_FISH": "FISHING",
               "S_SPECIES": "SPECIES", "S_TYPE": "TYPE", "S_SL": "SEARCH LV.", "S_LEVEL": "LEVEL", "S_CHAIN": "CHAIN",
               "S_TAB0": "Water & Land", "S_TAB1": "Rock & Fishing", "S_UNKNOWN": "?????", "S_HUNTING": "Hunting: ",
               "S_OFF": "SEARCH", "S_TITLE": "DexNav"}
    for k, v in strings.items():
        put(k, enc(v) + b"\xFF", 1)
    put("S_GO", enc("SEARCH ") + b"\xF8\x00\xFF", 1)       # F8 00: the A button's icon
    put("S_STOP", enc("STOP ") + b"\xF8\x00\xFF", 1)
    fixups = []                                 # (offset in data, name): words that hold another item's address

    def ptrs(name, names):
        put(name, bytes(4 * len(names)))
        for i, n in enumerate(names):
            fixups.append((addr[name] + 4 * i, n))

    ptrs("MAPS", ["MAP0", "MAP1"])
    ptrs("BOXNAMES", ["S_WATER", "S_LAND", "S_ROCK", "S_FISH"])
    ptrs("BTNWORDS", ["S_GO", "S_STOP", "S_OFF"])
    put("LABELS", bytes(40))
    for i, (_, bar, _, _) in enumerate(art.ROWS):
        fixups.append((addr["LABELS"] + 8 * i, ["S_SPECIES", "S_TYPE", "S_SL", "S_LEVEL", "S_CHAIN"][i]))
        struct.pack_into("<I", data, addr["LABELS"] + 8 * i + 4, bar - 1)
    put("RINGSHEET", bytes(8))                  # SpriteSheet {tiles, 512, tag}
    fixups.append((addr["RINGSHEET"], "RINGTILES"))
    struct.pack_into("<HH", data, addr["RINGSHEET"] + 4, 512, RING_TAG)
    put("RINGPAL", bytes(8))                    # SpritePalette {colours, tag}
    fixups.append((addr["RINGPAL"], "RINGPALDATA"))
    struct.pack_into("<H", data, addr["RINGPAL"] + 4, RING_TAG)
    put("SHADOWPAL", bytes(8))
    fixups.append((addr["SHADOWPAL"], "SHADOWDATA"))
    struct.pack_into("<H", data, addr["SHADOWPAL"] + 4, SHADOW_TAG)
    put("RINGTPL", bytes(24))                   # SpriteTemplate
    struct.pack_into("<HH", data, addr["RINGTPL"], RING_TAG, RING_TAG)
    fixups.append((addr["RINGTPL"] + 4, "RINGOAM"))
    struct.pack_into("<IIII", data, addr["RINGTPL"] + 8, 0x082EC69C, 0, 0x082EC6A8, 0x08007429)

    # ---- the code ---------------------------------------------------------------------------------------
    rows = art.ROWS
    consts = {
        "PANEL_X": art.PANEL_X, "PANEL_W": art.PANEL_W, "PANEL_IN_X": art.PANEL_X + 1, "PANEL_IN_W": art.PANEL_W - 2,
        "LABEL_X": art.PANEL_X + 4, "VALUE_X": art.PANEL_X + 4,
        "VAL1_Y": rows[0][2], "VAL3_Y": rows[2][2], "VAL4_Y": rows[3][2], "VAL5_Y": rows[4][2],
        "VAL1_TEXT_Y": rows[0][2] - 2, "VAL3_TEXT_Y": rows[2][2] - 2, "VAL4_TEXT_Y": rows[3][2] - 2,
        "VAL5_TEXT_Y": rows[4][2] - 2,
        "BTN_IN_X": art.PANEL_X + 2, "BTN_IN_Y": art.BUTTON_Y + 1, "BTN_IN_W": art.PANEL_W - 4,
        "BTN_IN_H": art.BUTTON_H - 2, "BTN_TEXT_Y": art.BUTTON_Y - 1,
        "TYPE_Y": rows[1][2] + rows[1][3] // 2, "TYPE1_X": art.PANEL_X + 2 + 16, "TYPE2_X": art.PANEL_X + 2 + 16 + 34,
        "TYPE_ONE_X": art.PANEL_X + art.PANEL_W // 2,
        "BOXA_TEXT_X": art.BOX_X + 5, "BOXA_TEXT_Y": art.BOXA_Y - 1,
        "BOXB_TEXT_X": art.BOX_X + 5, "BOXB_TEXT_Y": art.BOXB_Y - 1,
        "TAB0_X0": art.TAB0_X0, "TAB1_X0": art.TAB1_X0, "TAB_W": art.TAB_W, "TAB_TEXT_Y": art.TAB_Y - 1,
        "VAL_H": 13,
        "FIND_ADDR": FIND | 1, "ARMSEARCH_ADDR": ARM_SEARCH | 1, "CHAINBREAK_ADDR": CHAIN_BREAK | 1,
        "SLGET_ADDR": SL_GET | 1, "CB2RETURN_ADDR": CB2_RETURN | 1, "TILES_SIZE": len(tiles),
    }

    def assemble(data_base):
        src = open(os.path.join(HERE, "dexnavui.s"), encoding="ascii").read()
        names = sorted(list(consts) + ["%s_ADDR" % k for k in addr], key=len, reverse=True)
        for k in names:
            if k in consts:
                v = consts[k]
            else:
                v = data_base + addr[k[:-5]]
            src = src.replace(k, "0x%X" % v if v > 255 else "%d" % v)
        return SM.thumb(src, BASE)

    code, _ = assemble(BASE)
    data_base = BASE + ((len(code) + 3) & ~3)
    code2, dis = assemble(data_base)
    assert len(code2) == len(code)
    for off, name in fixups:
        struct.pack_into("<I", data, off, data_base + addr[name])
    blob = bytearray(code2) + b"\x00" * (data_base - BASE - len(code2)) + data
    end = FREE + len(blob)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = blob
    ui_init = BASE | 1                           # the first function in dexnavui.s
    assert dis[0].mnemonic == "push"
    struct.pack_into("<I", rom, o(CB2_INIT_LIT), ui_init)
    open(outp, "wb").write(rom)
    print("ui_init %08X; code %d bytes, data %d bytes (%d art tiles) at %08X..%08X"
          % (ui_init, len(code2), len(data), ntiles, BASE, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
