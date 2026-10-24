"""The relearner's list worked out from the ROM's tables, against what test_eggrelearn.lua logged.

    python -I check_lists.py <rom> <log> [--levelup-only]      compare every "rN:" / "cN:" pair in the log
    python -I check_lists.py <rom> --names Pikachu Azumarill ...  species numbers by name

The level-up part is the hack's own rule (0x09D6A93E: the learnset at 0x09AF0D00's pointer, 3 bytes an entry, up to
the Pokemon's level, not known, not twice, at most 24); then the egg moves: the species', each species it evolved
from (the evolution table at 0x0806D140's pointer: the first species with an entry whose target is it and whose
method's low byte is at most 0xF9, at most 8 steps), then the species the game's egg routine (0x09F00600) gives,
with its hard-wired cases (the patch asks it only when the species evolved from nothing; the lists come out the
same for every species); each once, none known, at most 64 in all. --levelup-only: the list of the game without
the patch."""
import re, struct, sys

B = 0x08000000


def tables(rom):
    u16 = lambda a: struct.unpack_from("<H", rom, a - B)[0]
    u32 = lambda a: struct.unpack_from("<I", rom, a - B)[0]
    evo, learn, egg, names = u32(0x0806D140), u32(0x09D6A9D4), u32(0x080703F0), u32(B + 0x144)
    lists, cur, i = {}, None, 0
    while u16(egg + 2 * i) != 0xFFFF:
        v = u16(egg + 2 * i)
        if v > 20000:
            cur = v - 20000
            lists.setdefault(cur, [])
        else:
            lists[cur].append(v)
        i += 1
    return u16, u32, evo, learn, lists, names


def name_of(rom, names, s):
    chars = {0: " ", 0xAE: "-", 0xB4: "'", 0xAD: ".", 0x1B: "e"}
    for i in range(26):
        chars[0xBB + i], chars[0xD5 + i] = chr(65 + i), chr(97 + i)
    raw = rom[names - B + 11 * s:names - B + 11 * s + 11].split(b"\xff")[0]
    return "".join(chars.get(b, "?") for b in raw)


def expected(rom, species, level, known, levelup_only=False):
    u16, u32, evo, learn, lists, _ = tables(rom)
    out = []
    p = u32(learn + 4 * species)
    k = 0
    while True:
        a = p - B + 3 * k
        m, lv = rom[a] | rom[a + 1] << 8, rom[a + 2]
        if m == 0 or lv == 0xFF:
            break
        if lv <= level and m not in known and len(out) <= 0x17 and m not in out:
            out.append(m)
        k += 1
    if levelup_only:
        return out

    def preevo(s):
        for j in range(1, 0x580):
            for e in range(5):
                a = evo + 40 * j + 8 * e
                if u16(a + 4) == s and rom[a - B] <= 0xF9:
                    return j
        return 0

    def base(s):
        if ((s - 0x20B) & 0xFFFF) <= 1 or s == 0x87 or s == 0x2F1:
            return 0x85
        if s == 0x21F:
            return 0x21E
        if s == 0x443:
            return 0x9B
        while preevo(s):
            s = preevo(s)
        return s

    def add(s):
        for m in lists.get(s, []):
            if len(out) < 64 and m not in known and m not in out:
                out.append(m)

    s, steps = species, 8
    while True:
        add(s)
        steps -= 1
        if not steps:
            break
        q = preevo(s)
        if not q:
            break
        s = q
    add(base(species))
    return out


def main():
    rom = open(sys.argv[1], "rb").read()
    if sys.argv[2] == "--names":
        names = tables(rom)[5]
        want = [n.lower() for n in sys.argv[3:]]
        for s in range(1, 0x580):
            nm = name_of(rom, names, s)
            if nm.lower() in want:
                print(s, nm)
        return
    lv_only = "--levelup-only" in sys.argv
    log = open(sys.argv[2], encoding="utf-8").read().splitlines()
    names = tables(rom)[5]
    mon, bad, n = {}, 0, 0
    for line in log:
        m = re.match(r"([rc]\d+): species (\d+) lv (\d+) moves (\d+) (\d+) (\d+) (\d+)", line)
        if m:
            mon[m.group(1)] = (int(m.group(2)), int(m.group(3)), [int(x) for x in m.group(4, 5, 6, 7)])
            continue
        m = re.match(r"([rc]\d+): list (\d+): ?(.*)", line)
        if m:
            sp, lv, known = mon[m.group(1)]
            got = [int(x) for x in m.group(3).split()]
            exp = expected(rom, sp, lv, [k for k in known if k], lv_only) + [0xFFFE]   # Cancel: LIST_CANCEL & 0xFFFF
            n += 1
            ok = got == exp and int(m.group(2)) == len(exp)
            bad += not ok
            print("%s %-4s %4d %-12s lv%3d: %2d moves%s" % ("ok " if ok else "BAD", m.group(1), sp,
                  name_of(rom, names, sp), lv, len(exp) - 1, "" if ok else "\n   got %s\n   exp %s" % (got, exp)))
        m = re.match(r"(c\d+): count (\d+)", line)
        if m:
            sp, lv, known = mon[m.group(1)]
            exp = len(expected(rom, sp, lv, [k for k in known if k], lv_only))
            ok = int(m.group(2)) == exp
            bad += not ok
            n += 1
            print("%s %-4s count %d, expected %d" % ("ok " if ok else "BAD", m.group(1), int(m.group(2)), exp))
    print("%d checked, %d bad" % (n, bad))


if __name__ == "__main__":
    main()
