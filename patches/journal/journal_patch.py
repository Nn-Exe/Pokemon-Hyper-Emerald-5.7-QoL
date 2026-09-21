"""Journal key item (Hyper Emerald v5.7): python journal_patch.py in.gba out.gba

Turns the Fame Checker (item 363, a FireRed leftover the hack never gives out, uses or sells) into the
Journal, a key item that says what to do next in the story. The overworld hook hands it to you once, like
the Sinnoh Map. Using it (Bag, or SELECT once registered) shows "<part> - Next objective:" and the step,
plus a progress line and the missing members for parallel tasks (gyms, Plates, Tapu trials).
The steps, their flags and the text are in steps.py.

ROM changes, all pointers or table fields - no game routine is rewritten:
  * the overworld hook word (0x08085E60) now points at our stub, which chains to what was there;
  * item 363's name, description pointer and field-use pointer.
Everything else is new code and data in free space. Nothing is written to the save.
"""
import struct, sys, os, re
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "translation"))
import steps as S
from inserter import ENC, NORMALIZE

FREE = 0x00FE5400                       # in the unreferenced 0xFF run 0x08FE5284..0x08FF0000
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

OW_HOOK = 0x085E5C                      # CB2_Overworld's first instruction, already a trampoline
OW_TARGET = 0x085E60
ITEMS = 0x00FC2C7C                      # item table (ROM header 0x1C8), 44-byte entries
ITEM = 363
NAME = "Journal"
DESC = ("A notebook of your", "journey. Use it to", "see what to do next.")


def enc(s):
    for k, v in NORMALIZE.items():
        s = s.replace(k, v)
    out = bytearray()
    for ch in s:
        assert ch in ENC, "no glyph for %r in %r" % (ch, s)
        out.append(ENC[ch])
    return bytes(out)


def wrap(text, width=S.W):
    lines, cur = [], ""
    for word in text.split():
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    assert all(len(l) <= width for l in lines), lines
    return lines


def box(lines):
    """Lines for the 2-line message box: the second follows a newline, every later one scrolls up (0xFA),
    which waits for a button first - the same joins translation/inserter.py uses for all the game's text."""
    out = enc(lines[0])
    for i, l in enumerate(lines[1:]):
        out += (b"\xfe" if i == 0 else b"\xfa") + enc(l)
    return out + b"\xff"


def message(header, body):
    assert len(header) <= S.W
    return box([header] + wrap(body))


def member(text):
    """A member's lines, joined by scrolls; group_tail puts the right join in front of the first line."""
    ls = wrap(text)
    out = enc(ls[0])
    for l in ls[1:]:
        out += b"\xfa" + enc(l)
    return out + b"\xff"


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


def data_blob(base):
    """Texts, flag lists, groups, the step table and the item description, laid out from `base`.
    Returns (bytes, step table address, description address)."""
    d = bytearray()

    def put(b, align=1):
        while len(d) % align:
            d.append(0)
        a = base + len(d)
        d.extend(b)
        return a

    rows = []
    for header, st, body in S.STEPS:
        text = put(message(header, body))
        flags = put(b"".join(struct.pack("<H", f) for f in st["flags"]), 2) if st["flags"] else 0
        group = 0
        if st["mode"] == 2:
            label = put(enc(st["label"]) + b"\xff")
            mem = [(f, w, put(member(t))) for f, w, t in st["members"]]
            g = struct.pack("<IBBH", label, len(mem), 1 if st["list_all"] else 0, 0)
            g += b"".join(struct.pack("<HBBI", f, w, 0, t) for f, w, t in mem)
            group = put(g, 4)
        rows.append(struct.pack("<BBBBIII", st["mode"], 1 if st["anchor"] else 0, len(st["flags"]), 0,
                                flags, text, group))
    final = put(message(*S.FINAL))
    rows.append(struct.pack("<BBBBIII", 0xFF, 0, 0, 0, 0, final, 0))
    table = put(b"".join(rows), 4)
    assert all(len(l) <= 20 for l in DESC)
    desc = put(b"\xfe".join(enc(l) for l in DESC) + b"\xff")
    while len(d) % 4:
        d.append(0)
    return bytes(d), table, desc


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000

    assert bytes(rom[OW_HOOK:OW_HOOK + 4]) == bytes.fromhex("004b1847"), "overworld hook is not a trampoline"
    prevhook = struct.unpack_from("<I", rom, OW_TARGET)[0]
    assert prevhook & 1 and 0x08000000 <= prevhook < 0x0A000000, "overworld hook target looks wrong"
    assert prevhook != BASE | 1, "already applied"

    e = ITEMS + ITEM * 44
    assert bytes(rom[e:e + 13]) == enc("Fame Checker") + b"\xff", "item 363 is not the Fame Checker"
    assert struct.unpack_from("<H", rom, e + 0x0E)[0] == ITEM
    assert rom[e + 0x1A] == 5, "item 363 is not in the Key Items pocket"
    assert rom[e + 0x19] == 1, "item 363 is not registrable"
    assert struct.unpack_from("<I", rom, e + 0x1C)[0] == 0x080FE821, "item 363 already has a field use"

    src = open(os.path.join(HERE, "journal.s"), encoding="ascii").read()

    def assemble(steps_addr):
        s = src.replace("PREVHOOK_ADDR", "0x%08X" % prevhook).replace("STEPS_ADDR", "0x%08X" % steps_addr)
        return thumb(s, BASE)

    code, dis = assemble(BASE)
    code_len = (len(code) + 3) & ~3
    data, table, desc = data_blob(BASE + code_len)
    code, dis = assemble(table)
    assert (len(code) + 3) & ~3 == code_len

    funcs = [i.address for i in dis if i.mnemonic == "push"]
    order = ("ow_stub", "item_use", "build", "step_done", "group_count", "group_tail", "append", "u8dec", "flag")
    assert len(funcs) == len(order), "unexpected function layout: %d pushes, expected %d" % (len(funcs), len(order))
    sym = dict(zip(order, funcs))
    assert sym["ow_stub"] == BASE, "ow_stub must be first"

    blob = bytearray(code) + bytes(code_len - len(code)) + data
    end = FREE + len(blob)
    assert end <= 0x00FF0000
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    struct.pack_into("<I", rom, OW_TARGET, sym["ow_stub"] | 1)
    rom[e:e + 14] = (enc(NAME) + b"\xff").ljust(14, b"\x00")
    struct.pack_into("<I", rom, e + 0x14, desc)
    struct.pack_into("<I", rom, e + 0x1C, sym["item_use"] | 1)
    open(outp, "wb").write(rom)

    print("code %d bytes @%08X, data @%08X, end %08X (%d bytes)" % (len(code), BASE, BASE + code_len,
                                                                   0x08000000 + end, len(blob)))
    print("  ow_stub %08X (chains to %08X), item_use %08X, steps %08X (%d + terminator), desc %08X" % (
        sym["ow_stub"] | 1, prevhook, sym["item_use"] | 1, table, len(S.STEPS), desc))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
