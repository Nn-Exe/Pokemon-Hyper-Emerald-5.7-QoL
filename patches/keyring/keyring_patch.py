"""Registered key items as a ring around the player, after Brilliant Diamond / Shining Pearl (Hyper Emerald v5.7).
Apply after keyreg and pcanywhere (anywhere later).
usage: python keyring_patch.py <in.gba> <out.gba>

SELECT used to open a text window (keyreg's popup, redrawn by pcanywhere: four "arrow item" lines and "A PC"). Now
four boxes around the player hold the registered items' Bag icons, the PC is in the middle; the keys are the same.
Two words change in keyreg: its `bl new_draw` (0x08FD8EF6) -> ring_open, and its popup task literal (0x08FD9134)
-> ring_task. The text popup stays as the fallback (a map with too few free sprite palettes; see keyring.s).
In the NOPC map sections the centre shows the PC crossed out and A only buzzes (the text popup's A too).
Code at 0x08FF6D00 (within bl range of keyreg), art and tables at 0x09FDA800 (after dexnavui).
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavseen"))
import art
import sinnohmap_patch as SM                    # the Thumb check
from dexnavseen_patch import bl, bl_target

CODE_FREE, CODE_END = 0x00FF6D00, 0x00FF7700    # the 0xFF run after dexnavscan; a data word reads 0x08FF7703
DATA_FREE, DATA_END = 0x01FDA800, 0x01FDD000    # after dexnavui, inside the pointer-free window 0x09FD8000..0x09FDD000
CODE, DATA = 0x08000000 + CODE_FREE, 0x08000000 + DATA_FREE

DRAW_CALL, NEW_DRAW = 0x08FD8EF6, 0x08FD9DE8    # keyreg's `bl draw_popup`, pointed at pcanywhere's new_draw
TASK_LIT, NEW_TASK = 0x08FD9134, 0x08FD9E7E     # keyreg's popup task literal, pcanywhere's new_task
USE_ITEM, PC_SCRIPT = 0x08FD9F36, 0x08FD9FFC    # pcanywhere's use_item and its PC script copy
CENTRE = (120, 74)                              # the player's body, on the field
BOXES = [(120, 34), (162, 74), (120, 114), (78, 74)]    # up, right, down, left - keyreg's slot order
NOPC = (64, 115, 110, 133, 119, 66)             # map sections without the ring's PC: Rainbow Castle,
                                                # Allearth Forest, Giant Chasm, Spear Pillar, Distortion World, Mt. Silver
TAG_BOX, TAG_EMPTY, TAG_CENTRE, TAG_PAL0 = 0x5E80, 0x5E81, 0x5E82, 0x5E90


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert bl_target(rom, DRAW_CALL) == NEW_DRAW, "keyreg's popup no longer draws pcanywhere's text window"
    assert u32(TASK_LIT) == NEW_TASK | 1, "keyreg's popup task is not pcanywhere's"
    assert at(NEW_DRAW, "70b585b0") and at(NEW_TASK, "f0b5") and at(USE_ITEM, "10b5041c"), "pcanywhere moved"
    assert rom[o(PC_SCRIPT)] == 0x69, "pcanywhere's PC script copy moved"      # lockall
    for a, pro in ((0x081AFE70, "f0b584b0"), (0x081AFFFC, "00b50004"), (0x080A18F4, "70b50c1c"),
                   (0x08008568, "f0b54746"), (0x080070E8, "f0b5051c"), (0x080084F8, "70b5051c"),
                   (0x08006DF4, "f0b581b0"), (0x080A1938, "70b5061c")):
        assert at(a, pro), "%08X is not the function the ring expects" % a

    # ---- the data ----
    data, addr = bytearray(), {}

    def put(name, blob, align=4):
        while len(data) % align:
            data.append(0)
        addr[name] = DATA + len(data)
        data.extend(blob)

    put("RINGPAL", art.palette())
    put("BOXTILES", art.tiles(art.box()))
    put("EMPTYTILES", art.tiles(art.box(empty=True)))
    put("CENTRETILES", art.tiles(art.centre()))
    put("OAM32", bytes.fromhex("0000008000000000"))         # 32x32, priority 0
    put("OAM64", bytes.fromhex("000000c000000000"))         # 64x64, priority 0
    put("BOXSHEET", struct.pack("<IHH", addr["BOXTILES"], 512, TAG_BOX))
    put("EMPTYSHEET", struct.pack("<IHH", addr["EMPTYTILES"], 512, TAG_EMPTY))
    put("CENTRESHEET", struct.pack("<IHH", addr["CENTRETILES"], 2048, TAG_CENTRE))
    dummy = (0x082EC69C, 0, 0x082EC6A8, 0x08007429)         # gDummySpriteAnimTable, -, affine, SpriteCallbackDummy
    put("BOXTPL", struct.pack("<HHI4I", TAG_BOX, TAG_PAL0, addr["OAM32"], *dummy))
    put("EMPTYTPL", struct.pack("<HHI4I", TAG_EMPTY, TAG_PAL0, addr["OAM32"], *dummy))
    put("CENTRETPL", struct.pack("<HHI4I", TAG_CENTRE, TAG_PAL0, addr["OAM64"], *dummy))
    put("BOXX", bytes(x for x, _ in BOXES), 1)
    put("BOXY", bytes(y for _, y in BOXES), 1)
    put("CENTREXTILES", art.tiles(art.centre(blocked=True)))
    put("CENTREXSHEET", struct.pack("<IHH", addr["CENTREXTILES"], 2048, TAG_CENTRE))
    put("NOPC", bytes(NOPC) + b"\xff", 1)
    end_data = DATA_FREE + len(data)
    assert end_data <= DATA_END and set(rom[DATA_FREE:end_data]) == {0xFF}, "data region not free"

    # ---- the code ----
    src = open(os.path.join(HERE, "keyring.s"), encoding="ascii").read()
    subst = dict(("%s_ADDR" % k, v) for k, v in addr.items())
    subst.update({"NEWDRAW_ADDR": NEW_DRAW | 1, "NEWTASK_ADDR": NEW_TASK | 1, "USEITEM_ADDR": USE_ITEM | 1,
                  "PCSCRIPT_ADDR": PC_SCRIPT, "CENTRE_X": CENTRE[0], "CENTRE_Y": CENTRE[1]})
    for k in sorted(subst, key=len, reverse=True):
        v = subst[k]
        src = src.replace(k, "0x%X" % v if v > 255 else "%d" % v)
    code, dis = SM.thumb(src, CODE)
    end_code = CODE_FREE + len(code)
    assert end_code <= CODE_END and set(rom[CODE_FREE:end_code]) == {0xFF}, "code region not free"
    for lo, hi in ((CODE, 0x08000000 + end_code), (DATA, 0x08000000 + end_data)):
        for k in range(0, len(rom), 4):
            v = struct.unpack_from("<I", rom, k)[0]
            assert not lo <= v < hi, "%08X already points into %08X..%08X" % (0x08000000 + k, lo, hi)
    funcs = [i.address for i in dis if i.mnemonic == "push" and "lr" in i.op_str]
    names = ["ring_open", "free_slots", "borrow", "build", "ring_close", "ring_task", "rt_close"]
    assert len(funcs) == len(names), "expected %d functions, found %d" % (len(names), len(funcs))
    labels = dict(zip(names, funcs))
    rom[CODE_FREE:end_code] = code
    rom[DATA_FREE:end_data] = data
    rom[o(DRAW_CALL):o(DRAW_CALL) + 4] = bl(DRAW_CALL, labels["ring_open"])
    struct.pack_into("<I", rom, o(TASK_LIT), labels["ring_task"] | 1)
    open(outp, "wb").write(rom)
    print("ring_open %08X, ring_task %08X; code %08X..%08X, data %08X..%08X"
          % (labels["ring_open"], labels["ring_task"], CODE, 0x08000000 + end_code, DATA, 0x08000000 + end_data))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
