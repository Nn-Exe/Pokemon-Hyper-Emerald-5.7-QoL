"""L: move info in battle (Hyper Emerald v5.7). Apply anywhere after the base build (it touches one word).
usage: python lmoveinfo_patch.py <in.gba> <out.gba>

While you choose a move, a small "[L] Move Info" tag sits above the move box. Hold L and a panel slides in from the
left with the highlighted move's name, Power, Accuracy, Physical / Special / Status, whether it makes contact, its
Priority and its effect chance; it follows the cursor and slides away when L is let go.

One word changes: HandleInputChooseMove (0x08057BFC) already jumps into the hack's own code at 0x08057C04
(ldr r0,[pc]; bx r0; .word 0x09D0A8C1); that word now points at our entry, which runs once a frame and then goes
on to 0x09D0A8C1. Code at 0x09FDBCA8 (after keyring's data, in the pointer-free window 0x09FD8000..0x09FDD000),
art and strings at 0x09FDC400. See lmoveinfo.s for how it works.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "hisuimap"))
import importlib.util
_spec = importlib.util.spec_from_file_location("lmi_art", os.path.join(HERE, "art.py"))
art = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(art)
import sinnohmap_patch as SM                    # the Thumb check
from grid import lz77 as unlz                   # the decompressor, to check ours

CODE_FREE, CODE_END = 0x01FDBCA8, 0x01FDC400    # after keyring's data, in the pointer-free window 0x09FD8000..0x09FDD000
DATA_FREE, DATA_END = 0x01FDC400, 0x01FDD000    # (every call is absolute, so the code need not be near anything)
CODE, DATA = 0x08000000 + CODE_FREE, 0x08000000 + DATA_FREE

HOOK_INSN, HOOK_LIT, HACK = 0x08057C04, 0x08057C08, 0x09D0A8C1
MOVES, NAMES = 0x09D86419, 0x09D30258
TAG_HUD, TAG_A, TAG_B = 0x5EB0, 0x5EB1, 0x5EB2
CONST = {"HUD_X": 34, "HUD_Y": 113,             # the 64x32 tag: its top-left at (2, 97), just above the move box
         "PANEL_Y": 79,                         # the panel: rows 47..110
         "SLIDE": 16, "FONT": 8,                # 8 frames in or out; the small narrow font
         "TITLE_Y": 3, "ROW1_Y": 18, "ROW2_Y": 31, "ROW3_Y": 44,
         "COL_V1": 46, "COL_VP": 53, "COL_2": 71, "COL_V2": 99,
         "TAG_HUD": TAG_HUD, "TAG_A": TAG_A, "TAG_B": TAG_B}
CH = {" ": 0x00, ".": 0xAD, "-": 0xAE, "+": 0x2E, "%": 0x5B}


def enc(s):
    out = bytearray()
    for c in s:
        if "A" <= c <= "Z":
            out.append(0xBB + ord(c) - 65)
        elif "a" <= c <= "z":
            out.append(0xD5 + ord(c) - 97)
        elif "0" <= c <= "9":
            out.append(0xA1 + ord(c) - 48)
        else:
            out.append(CH[c])
    return bytes(out) + b"\xff"


def lz(data):
    """GBA LZ77 (type 0x10), greedy. For LZ77UnCompWram, which copies a byte at a time (any distance works)."""
    out = bytearray(b"\x10" + len(data).to_bytes(3, "little"))
    i = 0
    while i < len(data):
        flag_at = len(out)
        out.append(0)
        for k in range(8):
            if i >= len(data):
                break
            best, dist = 0, 0
            for d in range(1, min(i, 0x1000) + 1):
                n = 0
                while n < 18 and i + n < len(data) and data[i + n - d] == data[i + n]:
                    n += 1
                if n > best:
                    best, dist = n, d
                    if n == 18:
                        break
            if best >= 3:
                out[flag_at] |= 0x80 >> k
                out += bytes([((best - 3) << 4) | ((dist - 1) >> 8), (dist - 1) & 0xFF])
                i += best
            else:
                out.append(data[i])
                i += 1
    while len(out) % 4:
        out.append(0)
    assert unlz(bytes(out)) == bytes(data)
    return bytes(out)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert at(0x08057BFC, "f0b54746 80b4 0020 0048 0047"), "HandleInputChooseMove's head is not the hack's"
    assert u32(HOOK_LIT) == HACK, "the move menu's hook word is %08X, not the hack's 0x09D0A8C1" % u32(HOOK_LIT)
    assert at(HACK - 1, "55f05cff"), "the hack's move-menu code moved"          # bl 0x09D6077C
    for a, pro in ((0x080084F8, "70b5051c"), (0x08006DF4, "f0b581b0"), (0x080070E8, "f0b5051c"),
                   (0x08008568, "f0b54746"), (0x08003380, "f0b55746"), (0x08199EEC, "70b54e46"),
                   (0x08003574, "f0b50006"), (0x082E7090, "11df7047"), (0x08008744, "30b5051c"),
                   (0x0800884C, "00b50004"), (0x08008CC0, "f0b54746")):
        assert at(a, pro), "%08X is not the function this patch expects" % a
    assert rom[o(NAMES) + 13:o(NAMES) + 18] == enc("Pound")[:5], "the move names moved"
    tackle = rom[o(MOVES) + 33 * 12:o(MOVES) + 34 * 12]
    assert (tackle[1], tackle[3], tackle[8] & 1, tackle[10]) == (40, 100, 1, 0), "gBattleMoves is not where expected"
    flame = rom[o(MOVES) + 53 * 12:o(MOVES) + 54 * 12]
    assert (flame[1], flame[5], flame[8] & 1, flame[10]) == (90, 10, 0, 1), "gBattleMoves' layout differs"

    # ---- the data ----
    data, addr = bytearray(), {}

    def put(name, blob, align=4):
        while len(data) % align:
            data.append(0)
        addr[name] = DATA + len(data)
        data.extend(blob)

    hud = art.tiles(art.hud())
    put("HUDGFX", hud)
    put("PANELLZ", lz(art.tiles(art.panel())))
    put("PAL", art.palette())
    put("PALSTRUCT", struct.pack("<IHH", addr["PAL"], TAG_HUD, 0))
    put("HUDSHEET", struct.pack("<IHH", addr["HUDGFX"], 1024, TAG_HUD))
    # the halves' tiles are drawn over as soon as they exist, so any 2048 readable bytes do as their source
    put("SHEETA", struct.pack("<IHH", addr["HUDGFX"], 2048, TAG_A))
    put("SHEETB", struct.pack("<IHH", addr["HUDGFX"], 2048, TAG_B))
    put("OAMHUD", bytes.fromhex("004000c000000000"))        # 64x32, priority 0
    put("OAM64", bytes.fromhex("000000c000000000"))         # 64x64, priority 0
    put("WINTPL", struct.pack("<BBBBBBH", 0, 0, 0, 16, 8, 0, 0))    # bg 0, 16x8 tiles, never put on the tilemap
    put("COLTITLE", bytes([0, art.WHITE, art.SHADOW]), 1)   # {background (0 = leave the frame), text, shadow}
    put("COLLABEL", bytes([0, art.DKGREY, art.LTGREY]), 1)
    put("COLVALUE", bytes([0, art.BLACK, art.LTGREY]), 1)
    put("COLPHYS", bytes([0, art.RED, art.LTGREY]), 1)
    put("COLSPEC", bytes([0, art.BLUE, art.LTGREY]), 1)
    put("COLSTAT", bytes([0, art.GREY, art.LTGREY]), 1)
    for name, s in (("SPOWER", "Power"), ("SACC", "Acc."), ("SPRIO", "Priority"), ("SEFFECT", "Eff."),
                    ("SCONTACT", "Contact"), ("SNOCONTACT", "No contact"), ("SDASH", "---"),
                    ("SPHYS", "Physical"), ("SSPEC", "Special"), ("SSTAT", "Status")):
        put(name, enc(s), 1)
    put("CATS", struct.pack("<6I", addr["SPHYS"], addr["COLPHYS"], addr["SSPEC"], addr["COLSPEC"],
                            addr["SSTAT"], addr["COLSTAT"]))
    for name in ("HUDTPL", "TPLA", "TPLB"):                 # filled once hud_cb's address is known
        put(name, bytes(24))

    # ---- the code ----
    src = open(os.path.join(HERE, "lmoveinfo.s"), encoding="ascii").read()
    subst = dict(("%s_ADDR" % k, v) for k, v in addr.items())
    subst.update(CONST)
    for k in sorted(subst, key=len, reverse=True):
        v = subst[k]
        src = src.replace(k, "0x%X" % v if v > 255 else "%d" % v)
    code, dis = SM.thumb(src, CODE)
    funcs = [i.address for i in dis if i.mnemonic == "push" and "lr" in i.op_str]
    names = ["body", "make_hud", "make_panel", "kill_panel", "hud_cb", "render", "pr", "number", "signed"]
    assert len(funcs) == len(names), "expected %d functions, found %d" % (len(names), len(funcs))
    labels = dict(zip(names, funcs))
    dummy = (0x082EC69C, 0, 0x082EC6A8)                     # gDummySpriteAnimTable, no images, the dummy affine table
    tpl = lambda tag, oam, cb: struct.pack("<HHI4I", tag, TAG_HUD, addr[oam], dummy[0], dummy[1], dummy[2], cb)
    for name, blob in (("HUDTPL", tpl(TAG_HUD, "OAMHUD", labels["hud_cb"] | 1)),
                       ("TPLA", tpl(TAG_A, "OAM64", 0x08007429)),       # SpriteCallbackDummy
                       ("TPLB", tpl(TAG_B, "OAM64", 0x08007429))):
        k = addr[name] - DATA
        data[k:k + 24] = blob

    end_code, end_data = CODE_FREE + len(code), DATA_FREE + len(data)
    print("code %d bytes, data %d bytes" % (len(code), len(data)))
    assert end_code <= CODE_END and set(rom[CODE_FREE:end_code]) == {0xFF}, "code region not free"
    assert end_data <= DATA_END and set(rom[DATA_FREE:end_data]) == {0xFF}, "data region not free"
    for lo, hi in ((CODE, 0x08000000 + end_code), (DATA, 0x08000000 + end_data)):
        for k in range(0, len(rom), 4):
            v = struct.unpack_from("<I", rom, k)[0]
            assert not lo <= v < hi, "%08X already points into %08X..%08X" % (0x08000000 + k, lo, hi)
    rom[CODE_FREE:end_code] = code
    rom[DATA_FREE:end_data] = data
    struct.pack_into("<I", rom, o(HOOK_LIT), CODE | 1)
    open(outp, "wb").write(rom)
    print("entry %08X, hud_cb %08X, render %08X; code %08X..%08X, data %08X..%08X"
          % (CODE, labels["hud_cb"], labels["render"], CODE, 0x08000000 + end_code, DATA, 0x08000000 + end_data))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
