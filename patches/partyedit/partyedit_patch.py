"""Party Pokemon editor (Hyper Emerald v5.7). Apply after the candynpc build.

Adds an "Edit" action to the party menu's field action list that opens a screen for changing the selected
Pokemon's nature, IVs and EVs. The action table was already relocated once by the relearner to 0x08FD9B8C
(34 entries, entry 33 = "Moves"); this relocates it again with a 35th entry and repoints the three code
literals that read it. The builder trampoline at 0x081B3518 is repointed at our hook, which appends EDIT
and then jumps to the relearner's own hook, so Moves keeps working.

Everything else is new Thumb-1 code and data in free space. No game routine is rewritten and nothing is
stored in the save: the screen edits gPlayerParty in place and calls CalculateMonStats.

usage: python partyedit_patch.py <in.gba> <out.gba>
"""
import os, re, struct, sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00F53900                       # after candynpc (0x08F53700..0x08F53851)
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

TABLE = 0x0FD9B8C                       # relocated sCursorOptions, 34 x {text*, cursor_cb*}
HOOK = 0x1B3518                         # relearner's trampoline: ldr r3,[pc];bx r3;.word 0x08FD9B01
HOOK_WORD = 0x08FD9B01
LITS = (0x1B32F8, 0x1B37C8, 0x1B37F8)
EDITS = 34

CODE_SYMS = ("cursor_edit", "cb2_edit", "cb2_init", "cb2_main", "vblank", "task",
             "value_of", "nat_name", "print", "u8dec", "draw_edit", "apply_delta")   # functions with a `push`

CHARS = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARS.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({" ": 0x00, ".": 0xAD, "-": 0xAE, "/": 0xBA})


def text(s, tail=b"\xFF"):
    return bytes(CHARS[c] for c in s) + tail


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 nop\n    nop", src, flags=re.M), addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early at %08X" % (
        addr + sum(i.size for i in dis))
    bad = [i for i in dis if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code, dis


def data_blob(base, sym):
    """Everything the code addresses by name, laid out at `base`."""
    d = bytearray()
    addrs = {}

    def put(name, b, align=1):
        while len(d) % align:
            d.append(0)
        addrs[name] = base + len(d)
        d.extend(b)

    put("BGTEMPLATE", struct.pack("<HH", 0x31F0, 0), 4)   # bg0, char 0, map 31, priority 3
    put("WINTEMPLATES", bytes((0, 1, 0, 26, 16, 15)) + struct.pack("<H", 1)
        + bytes((0xFF, 0, 0, 0, 0, 0)) + struct.pack("<H", 0), 4)
    pal = [0] * 16
    pal[1] = 0x7FFF      # white text
    pal[2] = 0x18C6      # dark window body
    pal[3] = 0x5AD6      # grey shadow
    pal[4] = 0x5140      # teal band
    pal[5] = 0x26A6      # green
    pal[6] = 0x001F      # red
    pal[7] = 0x03FF      # yellow
    put("TEXTPAL", struct.pack("<16H", *pal), 4)
    put("BACKDROP", struct.pack("<H", 0x2D07), 4)
    put("COLORS_HDR", bytes((5, 2, 3)), 4)
    put("COLORS_NORM", bytes((1, 2, 3)), 4)
    put("COLORS_HL", bytes((7, 2, 3)), 4)
    put("IVSHIFT", bytes((0, 5, 10, 20, 25, 15)), 4)     # display order HP,Atk,Def,SpA,SpD,Spe
    put("EVOFF", bytes((0, 1, 2, 4, 5, 3)), 4)           # EV bytes are HP,Atk,Def,Spe,SpA,SpD
    # the number scratch buffer is NOT here: it must be writable, so it lives in EWRAM (see partyedit.s)
    put("STR_EDIT", text("Edit "), 4)
    put("STR_EVTOTAL", text("EV total"), 4)
    labels_iv = ["Nature", "HP IV", "Atk IV", "Def IV", "SpA IV", "SpD IV", "Spe IV"]
    labels_ev = ["HP EV", "Atk EV", "Def EV", "SpA EV", "SpD EV", "Spe EV"]
    for i, s in enumerate(labels_iv):
        put("IVLBL%d" % i, text(s), 4)
    for i, s in enumerate(labels_ev):
        put("EVLBL%d" % i, text(s), 4)
    put("LABELS_IV", struct.pack("<7I", *[addrs["IVLBL%d" % i] for i in range(7)]), 4)
    put("LABELS_EV", struct.pack("<6I", *[addrs["EVLBL%d" % i] for i in range(6)]), 4)
    put("MENU_EDIT", text("Edit"), 4)
    return bytes(d), addrs


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000, "not the expected ROM"
    assert rom[HOOK:HOOK + 4] == bytes.fromhex("004b1847"), "builder hook is not the relearner's trampoline"
    assert struct.unpack_from("<I", rom, HOOK + 4)[0] == HOOK_WORD, "builder hook does not point at the relearner"
    for lit in LITS:
        assert struct.unpack_from("<I", rom, lit)[0] == 0x08000000 + TABLE, "action table literal @%X unexpected" % lit
    old_table = bytes(rom[TABLE:TABLE + 34 * 8])
    assert struct.unpack_from("<I", rom, TABLE + 33 * 8)[0] >= 0x08000000, "entry 33 is not populated"

    src = open(os.path.join(HERE, "partyedit.s"), encoding="ascii").read()

    def assemble(addrs):
        s = src
        for k, v in sorted(addrs.items(), key=lambda kv: -len(kv[0])):
            s = s.replace(k + "_ADDR", "0x%08X" % v)
        return thumb(s, BASE)

    # every ADDR placeholder the source mentions, so pass 1 can stub them all
    _, data_names = data_blob(BASE, {})
    all_names = list(data_names) + ["CB2_EDIT", "CB2_INIT", "CB2_MAIN", "VBLANK", "TASK"]

    # pass 1: stub addresses, just to learn the function layout and the code length. The code uses
    # labels for its internal calls, so only the .word lines care about these values.
    code, dis = assemble({n: 0x00000001 for n in all_names})
    prologues = [i.address for i in dis if i.mnemonic == "push"]
    assert len(prologues) == len(CODE_SYMS), \
        "unexpected function layout: %d prologues, expected %d" % (len(prologues), len(CODE_SYMS))
    sym = dict(zip(CODE_SYMS, prologues))
    sym["builder_hook"] = BASE
    assert dis[0].address == BASE and dis[0].mnemonic == "ldr", "builder_hook must start the blob"
    code_len = (len(code) + 3) & ~3

    # pass 2: real addresses
    data, daddrs = data_blob(BASE + code_len, sym)
    code_addrs = {"CB2_EDIT": sym["cb2_edit"] | 1, "CB2_INIT": sym["cb2_init"] | 1,
                  "CB2_MAIN": sym["cb2_main"] | 1, "VBLANK": sym["vblank"] | 1, "TASK": sym["task"] | 1}
    code_addrs.update(daddrs)
    code2, dis2 = assemble(code_addrs)
    assert (len(code2) + 3) & ~3 == code_len, "code length changed between passes"

    blob = bytearray(code2) + bytes(code_len - len(code2)) + data
    while len(blob) % 4:
        blob.append(0)
    table_off = len(blob)
    blob += old_table + struct.pack("<II", daddrs["MENU_EDIT"], sym["cursor_edit"] | 1)

    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    for lit in LITS:
        struct.pack_into("<I", rom, lit, BASE + table_off)
    rom[HOOK:HOOK + 8] = bytes.fromhex("004b1847") + struct.pack("<I", BASE | 1)

    open(outp, "wb").write(rom)
    print("code %d B @%08X  data @%08X  builder_hook %08X" % (len(code2), BASE, BASE + code_len, BASE | 1))
    for n, a in sorted(sym.items()):
        print("   %-14s %08X" % (n, a | 1))
    print("  table -> %08X (35 entries, entry 34 = 'Edit')  end %08X" % (BASE + table_off, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
