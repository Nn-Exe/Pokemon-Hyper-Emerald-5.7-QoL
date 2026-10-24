"""R: base stats on the Pokedex's INFO page (Hyper Emerald v5.7). In the main chain, before zhtext.
usage: python dexstats_patch.py <in.gba> <out.gba>

The user (2026-10-16): "would it be possible to redesign the pokedex to display stats of each pokemon like a number +
graph?", then, of the three ways offered (a panel on a button, a page in place of CRY or SIZE, a fifth page): "let do
the easiest one first"; and after the first build (shown while R was held): "it is hard to keep holding, can we make as
another page, or something indicate to press R??". A "[R] Stats" tab sits on the INFO page; R shows a panel over the
description box - "Base stats" and the total, then the six stats in two columns, each a number and a bar - and R again
takes it away; it stays on through Up / Down. The stats are read as the page runs, from the
table the ROM header's word 0x1BC names, so the panel shows whatever the build has (Gen 9 too, on the whole build).

One hook: an 8-byte jump at Task_HandleInfoScreenInput's head (0x080BEDF4, 4-aligned; its first four instructions
have nothing pc-relative and are done again by the stub). See dexstats.s for how it works.

Space: code and data in 0x09FDD000..0x09FDF000, in the 0xFF run the hack's own ROM has from 0x09F82519 to its end:
after fusionfix (0x09FDCD00..0x09FDCE38), before paldea's Journal block (0x09FE1000, which wants 0x80 blank bytes in
front of it). Checked here: all 0xFF, and no word of the ROM header or literal that code loads points into it.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "hisuimap"))
sys.path.insert(0, os.path.join(HERE, "..", "speciesx"))
import importlib.util
_spec = importlib.util.spec_from_file_location("ds_art", os.path.join(HERE, "art.py"))
art = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(art)
_spec = importlib.util.spec_from_file_location("lmi_patch", os.path.join(HERE, "..", "lmoveinfo", "lmoveinfo_patch.py"))
LMI = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LMI)
import sinnohmap_patch as SM                    # the Thumb check
import speciesx_patch as SX                     # is_pointer: a word of the header or a literal that code loads

B = 0x08000000
FREE, FREE_END = 0x09FDD000, 0x09FDF000
HOOK = 0x080BEDF4                               # Task_HandleInfoScreenInput
HOOK_WAS = "30b581b00006000e"                   # push {r4, r5, lr}; sub sp, #4; lsls r0, r0, #24; lsrs r0, r0, #24
TAG_A, TAG_B, TAG_C, TAG_D, TAG_TAB, TAG_PAL = 0x5EC0, 0x5EC1, 0x5EC2, 0x5EC3, 0x5EC4, 0x5EC0
CONST = {"PIECE_X0": 24, "PANEL_CY": 94 + 32,   # the pieces' centres: x 24, 88, 152, 216 (left -8), y rows 94..157
         "FONT": 8,                             # the small narrow font
         "TITLE_X": art.TITLE_X, "TEXT_Y": art.TEXT_Y, "TOTAL_RIGHT": art.TOTAL_RIGHT,
         "COL1_X": art.COLS_X[0], "COL2_X": art.COLS_X[1], "NUM_RIGHT": art.NUM_RIGHT,
         "BAR_X": art.BAR_X, "BAR_Y": art.BAR_Y, "BAR_W": art.BAR_W, "BAR_H": art.BAR_H,
         "BAR_FULL": art.BAR_FULL, "TRACK_FILL": art.TRACK * 17, "TAG_PAL": TAG_PAL, "TAG_TAB": TAG_TAB,
         "TAB_CX": art.TAB_X + 32, "TAB_CY": art.TAB_Y + 16,  # the 64x32 tab's centre
         "SE_DEX_PAGE": 109}
LABELS = ("HP", "Atk", "Def", "SpA", "SpD", "Spe")
ORDER = (0, 1, 2, 4, 5, 3)                      # the base stats' bytes: HP, Attack, Defense, Speed, Sp. Atk, Sp. Def
FUNCS = ((0x080084F8, "70b5051c"), (0x08006DF4, "f0b581b0"), (0x080070E8, "f0b5051c"), (0x08008568, "f0b54746"),
         (0x08003380, "f0b55746"), (0x08199EEC, "70b54e46"), (0x08003574, "f0b50006"), (0x082E7090, "11df7047"),
         (0x08008744, "30b5051c"), (0x0800884C, "00b50004"), (0x08008CC0, "f0b54746"))


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - B
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert at(HOOK, HOOK_WAS), "Task_HandleInfoScreenInput's head is not what this patch expects (applied already?)"
    words = struct.unpack_from("<%dI" % (len(rom) // 4), rom)
    assert [B + 4 * k for k, v in enumerate(words) if v == HOOK | 1] == [0x080BE9EC, 0x080BEDAC], \
        "the INFO page's task is named by other words than Task_LoadInfoScreen's and IsInfoScreenScrolling's"
    for a, pro in FUNCS:
        # (goldbox, earlier in the chain, put an 8-byte jump at LoadSpritePalette's head: its own, same job)
        ok = at(a, pro) or (a == 0x08008744 and at(a, "004b1847") and 0x08FEE400 <= u32(a + 4) < 0x08FEE88C)
        assert ok, "%08X is not the function this patch expects" % a
    # NationalPokedexNumToSpecies: a jump into the hack's own (it knows the extended Pokedex); called at its address
    assert at(0x0806D40C, "00490847") and u32(0x0806D410) & 1, "NationalPokedexNumToSpecies is not the hack's jump"
    stats = u32(0x080001BC) - B
    assert bytes(rom[stats + 28:stats + 34]) == bytes((45, 49, 49, 45, 65, 65)), "the header's base stats are not Bulbasaur's"

    # ---- the data (after the code: its size is known once the code is assembled with placeholders) ----
    def layout(data_at):
        data, addr = bytearray(), {}

        def put(name, blob, align=4):
            while len(data) % align:
                data.append(0)
            addr[name] = data_at + len(data)
            data.extend(blob)

        frame = art.tiles(art.frame())
        assert len(frame) == 8192
        put("PANELLZ", LMI.lz(frame))
        put("PAL", art.palette())
        put("PALSTRUCT", struct.pack("<IHH", addr["PAL"], TAG_PAL, 0))
        # the pieces' tiles are drawn over before they are ever shown, so any 2048 readable bytes do as the source
        put("SHEETS", b"".join(struct.pack("<IHH", addr["PANELLZ"], 2048, t) for t in (TAG_A, TAG_B, TAG_C, TAG_D)))
        put("TAGS", struct.pack("<4H", TAG_A, TAG_B, TAG_C, TAG_D))
        put("TABGFX", art.tiles(art.tab()))
        put("TABSHEET", struct.pack("<IHH", addr["TABGFX"], 1024, TAG_TAB))
        put("OAMTAB", bytes.fromhex("004000c000000000"))        # 64x32, priority 0
        put("OAM64", bytes.fromhex("000000c000000000"))         # 64x64, priority 0
        put("WINTPL", struct.pack("<BBBBBBH", 0, 0, 0, 32, 8, 0, 0))   # 32x8 tiles; the bg is window 0's
        put("COLTITLE", bytes([0, art.WHITE, art.SHADOW]), 1)  # {background (0 = leave the frame), text, shadow}
        put("COLLABEL", bytes([0, art.DKGREY, art.LTGREY]), 1)
        put("COLVALUE", bytes([0, art.BLACK, art.LTGREY]), 1)
        put("STITLE", LMI.enc("Base stats"), 1)
        put("STOTAL", LMI.enc("Total "), 1)
        for k, s in enumerate(LABELS):
            put("SL%d" % k, LMI.enc(s), 1)
        put("LABELS", struct.pack("<6I", *(addr["SL%d" % k] for k in range(6))))
        put("ORDER", bytes(ORDER), 1)
        put("ROWSY", bytes(v for y in art.ROWS_Y for v in (y, 0)), 1)
        bands = bytearray()
        for lim, col in art.BANDS:
            bands += bytes((0 if lim > 255 else lim, col))
        assert bands[-2] == 0, "the last band is the default"
        put("BANDS", bytes(bands), 1)
        put("TPLS", bytes(24 * 4))                      # the pieces'
        put("TABTPL", bytes(24))                        # filled once tab_cb's address is known
        return data, addr

    src0 = open(os.path.join(HERE, "dexstats.s"), encoding="ascii").read()

    def assemble(addr):
        subst = dict(("%s_ADDR" % k, v) for k, v in addr.items())
        subst.update(CONST)
        src = src0
        for k in sorted(subst, key=len, reverse=True):
            v = subst[k]
            src = src.replace(k, "0x%X" % v if v > 255 else "%d" % v)
        return SM.thumb(src, FREE)

    _, addr0 = layout(FREE + 0x800)
    code, dis = assemble(addr0)
    data_at = (FREE + len(code) + 0xFF) & ~0xFF
    data, addr = layout(data_at)
    code, dis = assemble(addr)
    assert data_at >= FREE + len(code)
    funcs = [i.address for i in dis if i.mnemonic == "push" and "lr" in i.op_str]
    names = ["stub", "stub_replay", "body", "make_tab", "make_panel", "create", "kill_panel", "tab_cb", "render",
             "width", "pr"]
    assert len(funcs) == len(names), "expected %d pushes with lr, found %d" % (len(names), len(funcs))
    labels = dict(zip(names, funcs))
    assert labels["stub"] == FREE
    dummy = (0x082EC69C, 0, 0x082EC6A8)              # gDummySpriteAnimTable, no images, the dummy affine table
    tpl = lambda tag, oam, cb: struct.pack("<HHI4I", tag, TAG_PAL, addr[oam], dummy[0], dummy[1], dummy[2], cb)
    tpls = b"".join(tpl(t, "OAM64", 0x08007429) for t in (TAG_A, TAG_B, TAG_C, TAG_D))     # SpriteCallbackDummy
    k = addr["TPLS"] - data_at
    data[k:k + len(tpls)] = tpls
    k = addr["TABTPL"] - data_at
    data[k:k + 24] = tpl(TAG_TAB, "OAMTAB", labels["tab_cb"] | 1)

    end = data_at + len(data)
    assert end <= FREE_END, "%d bytes: more than the space" % (end - FREE)
    assert set(rom[o(FREE):o(FREE_END)]) == {0xFF}, "the space is not blank"
    real = [B + 4 * i for i, v in enumerate(words) if FREE <= v < FREE_END and SX.is_pointer(rom, 4 * i)]
    assert not real, "pointers into the space: %s" % ["%08X" % a for a in real]
    rom[o(FREE):o(FREE) + len(code)] = code
    rom[o(data_at):o(end)] = data
    rom[o(HOOK):o(HOOK) + 8] = bytes.fromhex("004b1847") + struct.pack("<I", FREE | 1)   # ldr r3, [pc]; bx r3
    open(outp, "wb").write(rom)
    print("dexstats: hook %08X -> stub %08X; body %08X, render %08X, tab_cb %08X; code %08X..%08X, data %08X..%08X"
          % (HOOK, FREE, labels["body"], labels["render"], labels["tab_cb"], FREE, FREE + len(code), data_at, end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
