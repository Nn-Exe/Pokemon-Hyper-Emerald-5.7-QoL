"""The Gen 9 moves' own battle animations (Hyper Emerald v5.7). Apply after gen9abil, before kitakami.
usage: python -I gen9anim_patch.py <in.gba> <out.gba>

Until now each Gen 9 move played the animation of an older move it was made from (gen9's and gen9rest's templates:
Kowtow Cleave Night Slash's, Make It Rain Pay Day's...). Each now plays its own (anims.s, assembled by build.py into
gen9anim.bin at BASE): the engine's animation table (0x09D0AB00, a word a move, read through the literal at
0x080A3A44) gets the new script's address for each Gen 9 move, found by its name in the move name table.

The scripts use the game's own commands, sprite templates, tasks and scripts (defs.inc). Before anything is written
each of those is checked here: a task is a Thumb address in the game's code or the engine's, a script the scripts call or go to
is one the animation table already points at or starts with a command, a sprite template has its tags and its
pointers where the game keeps them.
Space: 0x09E38000..0x09E3C000 in the zero run 0x09E10044..0x09E40000 (NOTES, *The Gen 9 abilities work in battle*:
watched, no reads; gen9abil 0x09E33000..0x09E38000 below it, Kitakami from 0x09E40000): all zero, and no aligned
word in the ROM holds an address in it (checked here).
"""
import hashlib, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen9anim_data as D

B = 0x08000000
BASE, SPACE_END = 0x09E38000, 0x09E3C000
TABLE_LITERAL, TABLE = 0x080A3A44, 0x09D0AB00
BLANK = 0x09D0BB18                  # what the table holds for an id with no animation
FIRST, LAST = 938, 985              # the Gen 9 moves (gen9: 938-947, gen9rest: 948-985)
NAMES_HEADER = 0x148
CHARS = {" ": 0x00, ".": 0xAD, "-": 0xAE, "'": 0xB4}
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({chr(ord("A") + i): 0xBB + i for i in range(26)})
CHARS.update({chr(ord("a") + i): 0xD5 + i for i in range(26)})


def u16(rom, a):
    return struct.unpack_from("<H", rom, a - B)[0]


def u32(rom, a):
    return struct.unpack_from("<I", rom, a - B)[0]


def in_rom(v):
    return B <= v < B + 0x2000000


def read_sym():
    syms, meta = {}, {}
    for line in open(os.path.join(HERE, "gen9anim.sym")):
        k, v = line.split()
        if k.startswith("@"):
            meta[k[1:]] = v
        else:
            syms[k] = int(v, 16)
    return syms, meta


def outside_refs():
    """the game's own addresses the scripts use: (what, address), from anims.s and defs.inc"""
    equ = {}
    for line in open(os.path.join(HERE, "defs.inc")):
        m = re.match(r"\s*\.equ\s+(\w+),\s*(0x[0-9A-Fa-f]+)", line)
        if m:
            equ[m.group(1)] = int(m.group(2), 16)
    refs = set()
    for line in open(os.path.join(HERE, "anims.s")):
        p = line.split()
        if not p or p[0] not in ("launchtask", "launchtemplate", "call", "goto", "objtemplate"):
            continue
        args = [equ.get(a, a) for a in p[1:]]
        def num(a):
            return a if isinstance(a, int) else (int(a, 16) if re.fullmatch(r"0x[0-9a-fA-F]+", a) else None)
        if p[0] == "launchtask":
            refs.add(("task", num(args[0])))
        elif p[0] == "launchtemplate":
            refs.add(("template", num(args[0])))
        elif p[0] in ("call", "goto"):
            refs.add(("script", num(args[0])))
        else:                                       # tile tag, palette tag, oam, anims, images, affine, callback
            for a in args[2:6]:
                refs.add(("data", num(a)))
            refs.add(("task", num(args[6])))
    return sorted((k, v) for k, v in refs if v is not None and v >= B)


def check_refs(rom):
    table = {u32(rom, TABLE + 4 * k) for k in range(1030)}
    words = None
    for kind, a in outside_refs():
        if BASE <= a < SPACE_END:
            continue                                # one of ours
        if kind == "task" and 0x09D00000 <= a < 0x09E00000:
            # a routine of the engine's (a sprite's callback): one of the game's own sprite templates or scripts
            # names it too, so it is the routine it should be (Happy Hour's coins: 0x09D4520D)
            if words is None:
                words = {struct.unpack_from("<I", rom, o)[0] for o in range(0x1D00000, 0x1D80000, 4)}
            assert a in words, "engine routine %08X: nothing of the game's uses it" % a
        assert in_rom(a), "%s %08X is not in the ROM" % (kind, a)
        if kind == "task":
            assert a & 1 and (B <= a < 0x08200000 or 0x09D38000 <= a < 0x09D78000), "task %08X: not code" % a
        elif kind == "script":
            assert a in table or rom[a - B] < 0x30, "script %08X: not an animation script" % a
        elif kind == "template":
            t0, t1 = u16(rom, a), u16(rom, a + 2)
            ptrs = [u32(rom, a + 4 + 4 * k) for k in range(5)]
            assert (t0 == 0 or 0x2710 <= t0 < 0x2900) and in_rom(ptrs[0]) and in_rom(ptrs[4] & ~1) and \
                ptrs[4] & 1, "template %08X: %s" % (a, [hex(t0), hex(t1)] + [hex(x) for x in ptrs])
        elif kind == "data":
            assert a == 0 or in_rom(a), "data %08X" % a


def find_moves(rom):
    names = u32(rom, B + NAMES_HEADER) - B
    found = {}
    for name, count, script in D.ANIMS:
        enc = bytes(CHARS[c] for c in name) + b"\xff"
        ids = [i for i in range(FIRST, LAST + 1) if bytes(rom[names + 13 * i:names + 13 * i + len(enc)]) == enc]
        assert len(ids) == count, "%s: ids %s, expected %d" % (name, ids, count)
        for i in ids:
            found[i] = script
    assert sorted(found) == list(range(FIRST, LAST + 1)), "the Gen 9 moves are not %d..%d" % (FIRST, LAST)
    return found


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    syms, meta = read_sym()
    blob = open(os.path.join(HERE, "gen9anim.bin"), "rb").read()
    assert hashlib.sha1(blob).hexdigest() == meta["sha1"], "gen9anim.bin is not the build gen9anim.sym describes"
    assert BASE + len(blob) <= SPACE_END
    assert u32(rom, TABLE_LITERAL) == TABLE, "the animation table is not where the engine reads it"
    assert set(rom[BASE - B:SPACE_END - B]) == {0}, "gen9anim's space is not blank"
    held = [B + o for o in range(0, len(rom), 4) if BASE <= struct.unpack_from("<I", rom, o)[0] < SPACE_END]
    assert not held, "words point into gen9anim's space: %s" % ["%08X" % a for a in held]
    check_refs(rom)
    moves = find_moves(rom)
    for i, script in sorted(moves.items()):
        was = u32(rom, TABLE + 4 * i)
        assert in_rom(was) and was != BLANK and not BASE <= was < SPACE_END, "move %d's animation: %08X" % (i, was)
    rom[BASE - B:BASE - B + len(blob)] = blob
    for i, script in sorted(moves.items()):
        struct.pack_into("<I", rom, TABLE - B + 4 * i, syms[script])
    open(outp, "wb").write(rom)
    print("gen9anim: %08X..%08X, the animations of moves %d-%d (%d scripts)" % (
        BASE, BASE + len(blob), FIRST, LAST, len(set(moves.values()))))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
