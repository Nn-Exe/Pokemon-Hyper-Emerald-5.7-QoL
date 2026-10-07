"""The leftover Chinese text, in English (Hyper Emerald v5.7). Apply at the end of the chain.
usage: python zhtext_patch.py <in.gba> <out.gba>

official.json  Official Pokemon Emerald texts the hack translated to Chinese where they stood (link and wireless
               menus, the trade screen, Berry Blender, Battle Tower apprentices, Mystery Gift, map landmarks...). Each
               entry is the text's own address `a`, the length `n` of the official text there (its slot), `zh` the bytes
               the hack has there now, and `t` the official English in this project's casing ("Pokémon", "Trainer").
               The hack zero-filled the rest of each slot, so the English goes back into the same slot and nothing
               has to be re-pointed. Made by translation/official/ from the pret/pokeemerald source and symbol file.
hack.json      The hack's own texts (not in Emerald): `a` the string's address, `zh` its bytes, `t` the English, and
               either `n` (write in place: it fits) or `p` (the pointers to move to a new copy in free space).
               Trainer intro and defeat lines, shop and menu lines, battle-engine strings, and the names that sit
               inside tables: the hack's trainers, items, Trainer Hill, the apprentices (`table` says which).
"higher"       A code change. "{mon}'s {stat} can't go higher!" takes its last word from the hack's battle engine,
               which reads it at anchor + 0xE inside a block of 5-byte words ("rose", "rose", ...). "higher" does not
               fit there, so the two instructions that form that address call an 8-byte stub that loads the address of
               a new string instead. ("lower" is Emerald's own text and was never Chinese.)
effects        The other code change. "{side}'s {effect} effect: N turn(s) remaining." takes the effect's name (Swamp,
               Sea of Fire, Rainbow, and the four G-Max ones) from 5-byte slots - two hanzi each - that the engine
               reaches as a literal plus a small constant. The names go to 16-byte slots after the stub, and each
               literal (and two of the constants) is changed so the same instructions form the new addresses.
cityzoom.lz    One graphic. The PokeNav's zoomed city maps label their buildings ("POKeMON CENTER", "POKe MART",
               "POKeMON GYM", "BATTLE TENT", "POKeMON CONTEST") with sprites cut from one 64x64 sheet, which the hack
               redrew in Chinese at a new address. Emerald's own sheet (from the pret source, re-compressed) goes back
               into Emerald's slot for it - which the hack left unused - and the sprite sheet points there again.

Every entry is checked against the ROM before it is written: the bytes at `a` must be `zh` (or already the English).
Text syntax is pokeemerald's ({PLAYER}, {STR_VAR_1}, \\n \\l \\p ...), encoded with charmap.json.
"""
import json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "charmap.json"), encoding="utf-8") as f:
    CM = json.load(f)
CHARS = {k: bytes(v) for k, v in CM["chars"].items()}
NAMES = {k: bytes(v) for k, v in CM["names"].items()}
TEXT, TEXT_END = 0x01FD2A00, 0x01FD6F00         # moved texts: an unused, pointer-free run after the hack's own data
STUB = 0x01FDCC00                               # the "higher" stub + string: after lmoveinfo's data, within bl reach
HIGHER_SITE, HIGHER_LIT = 0x01D4AA14, 0x01D4AAEC
ZOOM_SHEET, ZOOM_SLOT, ZOOM_SIZE, ZOOM_HACK = 0x006230F8, 0x00DC9208, 0x2C0, 0x08FA5490   # sCityZoomTextSpriteSheet
SLOTS = STUB + 0x10                             # the field-effect names, 16 bytes each
# name, the literal its code loads into r1, that literal's value, the `ldr r1` that reads it, and the `adds r1, #n`
# after it: (site, old n, new n) or None
EFFECTS = (
    ("Swamp",       0x01D4DE8C, 0x09D76F88, 0x01D4DE28, (0x01D4DE2C, 0x76, 0x76)),
    ("Sea of Fire", 0x01D4E22C, 0x09D76F88, 0x01D4DF4A, (0x01D4DF4E, 0x7B, 0x7B)),
    ("Rainbow",     0x01D4E240, 0x09D77008, 0x01D4E014, None),
    ("Wildfire",    0x01D4E908, 0x09D77008, 0x01D4E664, (0x01D4E668, 0x05, 0x05)),
    ("Vine Lash",   0x01D4E908, 0x09D77008, 0x01D4E770, (0x01D4E774, 0x0A, 0x15)),
    ("Cannonade",   0x01D4E908, 0x09D77008, 0x01D4E882, (0x01D4E886, 0x0F, 0x25)),
    ("Volcalith",   0x01D4EA7C, 0x09D77008, 0x01D4E9CA, (0x01D4E9CE, 0x14, 0x14)),
)


def encode(s):
    """pokeemerald text syntax -> bytes, with the 0xFF terminator"""
    out, i = bytearray(), 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            out += CHARS[s[i:i + 2]]
            i += 2
        elif c == "{":
            j = s.index("}", i)
            for tok in s[i + 1:j].split():
                if tok in NAMES:
                    out += NAMES[tok]
                elif re.match(r"^(0x[0-9A-Fa-f]+|\d+)$", tok):
                    out.append(int(tok, 0))
                else:
                    raise ValueError("unknown {%s} in %r" % (tok, s))
            i = j + 1
        else:
            out += CHARS[c]
            i += 1
    return bytes(out) + b"\xff"


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def build(inp, outp):
    with open(inp, "rb") as f:
        rom = bytearray(f.read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    done = already = 0
    problems = []

    for e in load("official.json"):
        o, n, zh, new = int(e["a"], 16) - 0x08000000, e["n"], bytes.fromhex(e["zh"]), encode(e["t"])
        assert len(new) <= n, "%s: %d bytes do not fit the %d-byte slot" % (e["a"], len(new), n)
        slot = bytes(rom[o:o + n])
        if slot[:len(new)] == new and not any(slot[len(new):]):
            already += 1
        elif slot[:len(zh)] == zh and not (set(slot[len(zh):]) - {0x00, 0xFF}):
            rom[o:o + n] = new + bytes(n - len(new))
            done += 1
        else:
            problems.append(e["a"])

    if set(rom[TEXT:TEXT_END]) == {0xFF}:                       # not on a ROM that already has the texts
        no_inbound(rom, TEXT, TEXT_END)
    pos, placed = TEXT, {}
    for e in load("hack.json"):
        o, zh, new = int(e["a"], 16) - 0x08000000, bytes.fromhex(e["zh"]), encode(e["t"])
        cur = bytes(rom[o:o + len(zh)])
        if "n" in e:                                            # in place
            assert len(new) <= e["n"], "%s: %d bytes do not fit the %d-byte slot" % (e["a"], len(new), e["n"])
            if bytes(rom[o:o + len(new)]) == new:
                already += 1
            elif cur == zh:
                rom[o:o + len(new)] = new
                done += 1
            else:
                problems.append(e["a"])
        else:                                                   # a new copy, the listed pointers moved to it
            ptrs = [int(p, 16) - 0x08000000 for p in e["p"]]
            old = struct.pack("<I", int(e["a"], 16))
            if cur != zh or any(bytes(rom[p:p + 4]) != old for p in ptrs):
                moved = [struct.unpack_from("<I", rom, p)[0] - 0x08000000 for p in ptrs]
                if len(set(moved)) == 1 and bytes(rom[moved[0]:moved[0] + len(new)]) == new:
                    already += 1
                else:
                    problems.append(e["a"])
                continue
            if new not in placed:                               # the same line is said in several places
                assert pos + len(new) <= TEXT_END, "out of free space for hack.json"
                assert set(rom[pos:pos + len(new)]) == {0xFF}, "free space at %08X is not free" % (0x08000000 + pos)
                rom[pos:pos + len(new)] = new
                placed[new] = pos
                pos += len(new)
            for p in ptrs:
                struct.pack_into("<I", rom, p, 0x08000000 + placed[new])
            done += 1

    assert not problems, "%d entries do not match this ROM: %s" % (len(problems), problems[:10])
    higher(rom)
    effects(rom)
    cityzoom(rom)
    with open(outp, "wb") as f:
        f.write(rom)
    print("zhtext: %d texts written, %d already English; moved texts at %08X..%08X, stub at %08X"
          % (done, already, 0x08000000 + TEXT, 0x08000000 + pos, 0x08000000 + STUB))


def no_inbound(rom, lo, hi):
    """free space is only free if no aligned word in the ROM points into it"""
    for top in range((0x08000000 + lo) >> 16, ((0x08000000 + hi - 1) >> 16) + 1):
        pat, i = struct.pack("<H", top), 0
        while True:
            i = rom.find(pat, i)
            if i < 0:
                break
            w = i - 2
            if w % 4 == 0 and not lo <= w < hi:
                v = struct.unpack_from("<I", rom, w)[0] - 0x08000000
                assert not lo <= v < hi, "a pointer at %08X reaches into %08X" % (0x08000000 + w, 0x08000000 + v)
            i += 1


def cityzoom(rom):
    """the zoomed city maps' labels: Emerald's sheet back in its own slot, the sprite sheet pointed at it"""
    with open(os.path.join(HERE, "cityzoom.lz"), "rb") as f:
        data = f.read()
    assert data[:4] == bytes.fromhex("10000800") and len(data) <= ZOOM_SIZE
    here = struct.unpack_from("<I", rom, ZOOM_SHEET)[0]
    if here == 0x08000000 + ZOOM_SLOT and bytes(rom[ZOOM_SLOT:ZOOM_SLOT + len(data)]) == data:
        return
    assert here == ZOOM_HACK and struct.unpack_from("<H", rom, ZOOM_SHEET + 4)[0] == 0x800, "the label sheet is not as expected"
    assert rom[ZOOM_SLOT] == 0x10 and rom.find(struct.pack("<I", 0x08000000 + ZOOM_SLOT)) < 0, "Emerald's slot is in use"
    rom[ZOOM_SLOT:ZOOM_SLOT + ZOOM_SIZE] = data + bytes(ZOOM_SIZE - len(data))
    struct.pack_into("<I", rom, ZOOM_SHEET, 0x08000000 + ZOOM_SLOT)


def loads(rom, lit):
    """every `ldr rX, [pc, #n]` that reads the literal at `lit`"""
    out = []
    for a in range(lit - 1020, lit, 2):
        h = struct.unpack_from("<H", rom, a)[0]
        if h >> 11 == 0b01001 and ((a + 4) & ~3) + (h & 0xFF) * 4 == lit:
            out.append(a)
    return out


def effects(rom):
    """the seven field-effect names: new 16-byte slots, the literals (and two added constants) re-aimed at them"""
    block = b"".join(encode(name).ljust(16, b"\xff") for name, *_ in EFFECTS)
    new_lit = {}
    for i, (name, lit, old, site, add) in enumerate(EFFECTS):
        want = 0x08000000 + SLOTS + 16 * i - (add[2] if add else 0)
        assert new_lit.setdefault(lit, want) == want, "%s: its literal is shared and the offsets do not agree" % name
    if all(struct.unpack_from("<I", rom, lit)[0] == v for lit, v in new_lit.items()) \
            and bytes(rom[SLOTS:SLOTS + len(block)]) == block:
        return
    for name, lit, old, site, add in EFFECTS:
        assert struct.unpack_from("<I", rom, lit)[0] == old, "%s: the literal at %08X is not as expected" % (name, 0x08000000 + lit)
        assert site in loads(rom, lit) and rom[site + 1] == 0x49, "%s: no `ldr r1` at %08X" % (name, 0x08000000 + site)
        if add:
            assert bytes(rom[add[0]:add[0] + 2]) == bytes([add[1], 0x31]), "%s: the `adds r1` is not as expected" % name
    for lit in new_lit:                         # nobody else may be reading these literals
        mine = sorted(site for _, l, _, site, _ in EFFECTS if l == lit)
        assert loads(rom, lit) == mine, "the literal at %08X has other readers" % (0x08000000 + lit)
    assert set(rom[SLOTS:SLOTS + len(block) + 8]) == {0xFF}, "the names' space is not free"
    no_inbound(rom, SLOTS, SLOTS + len(block))
    rom[SLOTS:SLOTS + len(block)] = block
    for lit, v in new_lit.items():
        struct.pack_into("<I", rom, lit, v)
    for name, lit, old, site, add in EFFECTS:
        if add:
            rom[add[0]] = add[2]


def higher(rom):
    """won't go "higher": bl to a stub that returns the new string's address in r4 (lr is saved by the function)"""
    text = encode("higher")
    stub = bytes.fromhex("004c7047") + struct.pack("<I", 0x08000000 + STUB + 8) + text     # ldr r4,[pc,#0]; bx lr; .word
    off = STUB - (HIGHER_SITE + 4)
    assert STUB % 4 == 0 and abs(off) < 0x400000
    bl = struct.pack("<HH", 0xF000 | ((off >> 12) & 0x7FF), 0xF800 | ((off >> 1) & 0x7FF))
    if bytes(rom[HIGHER_SITE:HIGHER_SITE + 4]) == bl and bytes(rom[STUB:STUB + len(stub)]) == stub:
        return
    assert bytes(rom[HIGHER_SITE:HIGHER_SITE + 6]) == bytes.fromhex("354c0e340be0"), "the stat-word code is not as expected"
    assert struct.unpack_from("<I", rom, HIGHER_LIT)[0] == 0x09D749E4
    assert set(rom[STUB:STUB + 0x10]) == {0xFF}, "the stub's space is not free"
    no_inbound(rom, STUB, STUB + len(stub))
    rom[STUB:STUB + len(stub)] = stub
    rom[HIGHER_SITE:HIGHER_SITE + 4] = bl                     # the `b` that follows stays


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
