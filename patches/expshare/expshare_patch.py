"""Exp. Share on/off (Hyper Emerald v5.7). Apply after eggmoves.
usage: python expshare_patch.py <in.gba> <out.gba>

The Exp. Share (key item 182) gives experience to the whole party for as long as it is in the Bag - the hack's
experience code (0x09D5AB80, 0x09D5AC22, 0x09D5ACE6, 0x09D5B018) asks CheckBagHasItem(182, 1) - and there was
no way to turn it off. Now using it (from the Bag, or SELECT once registered) switches it off and on, with a
message, as in the modern games. It starts on, so nothing changes for anyone who does not use it.

* The four checks load CheckBagHasItem from two pool words only they use (0x09D5AE40, 0x09D5B094); both now
  point at share_check (expshare.s), which is CheckBagHasItem except that the Exp. Share counts as absent
  while flag 0x433D is set.
* Item 182's field-use routine becomes item_use (flip the flag, say "The Exp. Share was turned off/on."), it
  becomes registrable to SELECT, and its description says it can be switched.
* Flag 0x433D: no script references it, no code literal holds it, clear in all 34 saves checked.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import sinnohmap_patch as SM                    # text encoder and the Thumb check

FREE = 0x00FF5B00                               # in the unreferenced 0xFF run 0x08FF5A18..0x08FFD5A0
BASE = 0x08000000 + FREE
ITEMS, ITEM_SIZE = 0x00FC2C7C, 44
EXP_SHARE, OFF_FLAG = 182, 0x433D
POOL_WORDS = (0x09D5AE40, 0x09D5B094)
CHECK_SITES = (0x09D5AB80, 0x09D5AC22, 0x09D5ACE6, 0x09D5B018)   # the ldr r3 of each check
CHECKBAG = 0x080D6725
CANT_USE = 0x080FE821

CHARS = dict(SM.CHARS)
CHARS.update({",": 0xB8, "!": 0xAB, "/": 0xBA})


def text(s, pause=False):
    return bytes(CHARS[c] for c in s) + (bytes((0xFC, 0x09)) if pause else b"") + b"\xFF"


def lines(ls):
    return b"\xFE".join(bytes(CHARS[c] for c in l) for l in ls) + b"\xFF"


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    for w in POOL_WORDS:
        assert struct.unpack_from("<I", rom, o(w))[0] == CHECKBAG, "%08X is not CheckBagHasItem" % w
    # each check site loads one of the two words, and nothing else loads them
    for w in POOL_WORDS:
        users = [a for a in range(o(w) - 1020, o(w), 2)
                 if (struct.unpack_from("<H", rom, a)[0] & 0xF800) == 0x4800
                 and ((a + 4) & ~3) + (struct.unpack_from("<H", rom, a)[0] & 0xFF) * 4 == o(w)]
        assert all(0x08000000 + a in CHECK_SITES for a in users), "%08X has other readers" % w
    e = ITEMS + EXP_SHARE * ITEM_SIZE
    assert bytes(rom[e:e + 11]) == text("Exp. Share"), "item 182 is not the Exp. Share"
    assert rom[e + 26] == 5 and struct.unpack_from("<I", rom, e + 28)[0] == CANT_USE, "the Exp. Share already does something"

    src = open(os.path.join(HERE, "expshare.s"), encoding="ascii").read()
    src = src.replace("EXP_SHARE", str(EXP_SHARE)).replace("OFF_FLAG", "0x%04X" % OFF_FLAG)

    def data_blob(base):
        d = bytearray(); a = {}
        def put(name, b, align=1):
            while len(d) % align: d.append(0)
            a[name] = base + len(d); d.extend(b)
        put("STR_ON", text("The Exp. Share was turned on.", pause=True))
        put("STR_OFF", text("The Exp. Share was turned off.", pause=True))
        put("DESC", lines(["Gives the whole", "party Exp. Use it", "to turn it on/off."]))
        return bytes(d), a

    def assemble(addrs):
        s = src
        for k, v in addrs.items():
            s = s.replace(k + "_ADDR", "0x%08X" % v)
        return SM.thumb(s, BASE)

    _, dummy = data_blob(BASE)
    code, dis = assemble(dummy)
    code_len = (len(code) + 3) & ~3
    data, addrs = data_blob(BASE + code_len)
    code, dis = assemble(addrs)
    assert (len(code) + 3) & ~3 == code_len
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    assert len(funcs) == 2, "expected share_check and item_use, found %d functions" % len(funcs)
    share_check, item_use = funcs[0] | 1, funcs[1] | 1

    blob = bytes(code) + bytes(code_len - len(code)) + data
    end = FREE + len(blob)
    assert end <= 0x00FFD5A0 and set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    for w in POOL_WORDS:
        struct.pack_into("<I", rom, o(w), share_check)
    struct.pack_into("<I", rom, e + 28, item_use)          # Use: switch it
    struct.pack_into("<I", rom, e + 20, addrs["DESC"])
    rom[e + 25] = 1                                        # can be registered to SELECT, like the Sinnoh Map
    open(outp, "wb").write(rom)
    print("share_check %08X, item_use %08X, end %08X; flag 0x%04X" % (share_check, item_use, 0x08000000 + end, OFF_FLAG))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
