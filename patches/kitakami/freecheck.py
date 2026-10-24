"""freecheck.py <rom> <first flag hex> <last flag hex> [var hex ...]: which flags in a range are free by Area Zero's
checks (story.py: no setflag / clearflag / checkflag bytes for it anywhere in the ROM, no aligned word holds it, no
map object hides by it, clear in the saves), in one pass; and for vars: no setvar / addvar / compare / copyvar /
setorcopyvar bytes for it, no aligned word, 0 in the saves. Also: not the trainer flag of a trainer the game has
(ids above 0x357 use id + 0x40C9)."""
import re, struct, sys, os
rom = open(sys.argv[1], "rb").read()
u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
ok = lambda a: 0x08000000 <= a < 0x08000000 + len(rom) - 0x40
lo, hi = int(sys.argv[2], 16), int(sys.argv[3], 16)
vars_ = [int(v, 16) for v in sys.argv[4:]]

after = {}
for op in (0x29, 0x2A, 0x2B):
    for m in re.finditer(re.escape(bytes([op])), rom):
        o = m.start() + 1
        if o + 2 <= len(rom):
            after.setdefault(u16(o), 0)
            after[u16(o)] += 1
varcmd = {}
for op in (0x16, 0x17, 0x18, 0x19, 0x1A, 0x21, 0x22):     # setvar addvar subvar copyvar setorcopyvar compare_var_to_value compare_var_to_var
    for m in re.finditer(re.escape(bytes([op])), rom):
        o = m.start() + 1
        if o + 2 <= len(rom):
            varcmd[u16(o)] = varcmd.get(u16(o), 0) + 1
            if op in (0x19, 0x1A, 0x22) and o + 4 <= len(rom):
                varcmd[u16(o + 2)] = varcmd.get(u16(o + 2), 0) + 1
aligned = set(u32(o) for o in range(0, len(rom) - 3, 4))
hides = set()
g = 0
groups = []
while ok(u32(0x00A54698 + 4 * g)):
    groups.append(u32(0x00A54698 + 4 * g) - 0x08000000); g += 1
starts = sorted(set(groups))
for ga in groups:
    nxt = min([s for s in starts if s > ga], default=None)
    n = 0
    while nxt is None or ga + 4 * n < nxt:
        h = u32(ga + 4 * n)
        if not ok(h): break
        ev = u32(h - 0x08000000 + 4)
        if ok(ev):
            ev -= 0x08000000; objs = u32(ev + 4)
            if rom[ev] and ok(objs):
                for k in range(min(rom[ev], 64)):
                    hides.add(u16(objs - 0x08000000 + 24 * k + 20))
        n += 1

ROOT = os.path.dirname(os.path.abspath(__file__))
while not os.path.isdir(os.path.join(ROOT, "roms")) and os.path.dirname(ROOT) != ROOT:   # gba-trans: the saves
    ROOT = os.path.dirname(ROOT)
SAVES = [os.path.join(ROOT, "roms", "test-paldea", "Hyper Emerald - Area Zero (my placements 25).sav"),
         os.path.join(ROOT, "roms", "test-paldea", "Hyper Emerald - Area Zero (my placements 24).sav"),
         os.path.join(ROOT, "roms", "current", "Pokemon Hyper Emerald v5.7 - Full English Modern.sav")]


def newest_slot(d):
    best = None
    for slot in range(2):
        for k in range(14):
            o = slot * 14 * 4096 + k * 4096
            sid, chk, sig, idx = struct.unpack_from("<HHII", d, o + 0xFF4)
            if sig == 0x08012025 and (best is None or idx > best[0]):
                best = (idx, slot)
    return best[1] if best else None


def sections(d, slot):
    out = {}
    for k in range(14):
        o = slot * 14 * 4096 + k * 4096
        sid = u16_(d, o + 0xFF4)
        out[sid] = d[o:o + 4096]
    return out


def u16_(d, o): return struct.unpack_from("<H", d, o)[0]


def saveblocks(path):
    d = open(path, "rb").read()
    s = newest_slot(d)
    sec = sections(d, s)
    sb2 = sec[0][:0xF2C]
    sb1 = b"".join(sec[i][:0xF80] for i in range(1, 5))
    return sb1, sb2


def flag_bit(sb1, sb2, f):
    i = (f - 0x4000) >> 3
    if i <= 0x33: b = sb1[0x988 + i]
    elif i <= 0x67: b = sb1[0x3B24 + i - 0x34]
    elif i <= 0x9B: b = sb2[0x5C + i - 0x68]
    else: b = sb2[0x28 + i - 0x9C]
    return (b >> (f & 7)) & 1


blocks = [saveblocks(p) for p in SAVES if os.path.exists(p)]
free = []
for f in range(lo, hi + 1):
    why = []
    if after.get(f): why.append("flag cmd %d" % after[f])
    if f in aligned: why.append("aligned word")
    if f in hides: why.append("hides an object")
    tid = f - 0x40C9
    if 0x357 < tid < 1355: why.append("trainer %d's flag" % tid)
    if any(flag_bit(a, b, f) for a, b in blocks): why.append("set in a save")
    if not why: free.append(f)
print("free flags in %04X-%04X: %d" % (lo, hi, len(free)))
print(" ".join("%04X" % f for f in free))
for v in vars_:
    why = []
    if varcmd.get(v): why.append("var cmds %d" % varcmd[v])
    if v in aligned: why.append("aligned word")
    vals = [u16_(a, 0x139C + (v - 0x4000) * 2) for a, b in blocks]
    if any(vals): why.append("non-zero in saves %s" % vals)
    print("var %04X: %s" % (v, "FREE" if not why else "; ".join(why)))
