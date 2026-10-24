"""Every tile of every map that Continue would walk you off: a door behaviour (the game's own lists, read from
MetatileBehavior_IsDoor / _IsNonAnimDoor) on a tile that has no warp event and that you can stand on (collision 0).
python -I scan_doors.py rom.gba
Before contexit, Continue on any of them walked you one step (the way you face; down off an animated door).
8aeca761 (and the hack's own v5.7 bugfix 2): 164 tiles (163), Petalburg Woods' 26,42 / 27,42 / 36,42 / 37,42 among them."""
import sys, struct

rom = open(sys.argv[1], 'rb').read()
def u8(a): return rom[a & 0x1FFFFFF]
def u16(a): return struct.unpack_from('<H', rom, a & 0x1FFFFFF)[0]
def u32(a): return struct.unpack_from('<I', rom, a & 0x1FFFFFF)[0]

def cmp_values(fn, n):
    """the immediates of the first n `cmp r0, #imm` (0x28xx) in a behaviour test"""
    out, a = [], fn
    while len(out) < n and a < fn + 0x40:
        h = u16(a)
        if h >> 8 == 0x28:
            out.append(h & 0xFF)
        a += 2
    return out

# vanilla addresses (pokeemerald.sym); the code is checked by its shape
DOOR = cmp_values(0x08088EFC, 2)
NONANIM = cmp_values(0x08088F58, 3)
print('IsDoor', [hex(v) for v in DOOR], 'IsNonAnimDoor', [hex(v) for v in NONANIM])
# gMapGroups: the literal of Overworld_GetMapHeaderByGroupAndId (0x08084A90, 0x18 bytes)
groups = None
for a in range(0x08084A90, 0x08084AA8, 2):
    pass
for k in range(0x08084A90, 0x08084AA8 + 4, 4):
    v = u32(k)
    if 0x08000000 <= v < 0x0A000000 and u32(v) and 0x08000000 <= u32(v) < 0x0A000000:
        groups = v
print('gMapGroups', hex(groups))

def ok(p): return 0x08000000 <= p < 0x0A000000

def headers():
    lists = []
    while ok(u32(groups + 4 * len(lists))) and len(lists) < 64:
        lists.append(u32(groups + 4 * len(lists)))
    starts = sorted(set(lists) | {groups})
    for g, gp in enumerate(lists):
        end = min([s for s in starts if s > gp] or [gp + 4 * 256])
        for n in range((end - gp) // 4):
            h = u32(gp + 4 * n)
            if not ok(h) or not ok(u32(h)):
                break
            yield g, n, h

count = 0
for g, n, h in headers():
    lay, ev = u32(h), u32(h + 4)
    w, hh = u32(lay), u32(lay + 4)
    if not (0 < w < 512 and 0 < hh < 512):
        continue
    data, prim, sec = u32(lay + 12), u32(lay + 16), u32(lay + 20)
    if not (ok(data) and ok(prim) and ok(sec)):
        continue
    def attrs(ts):
        return u32(ts + 16) if ts else 0
    pa, sa = attrs(prim), attrs(sec)
    warps = set()
    if ok(ev):
        wc, wp = u8(ev + 1), u32(ev + 8)
        if not ok(wp): wc = 0
        for i in range(wc):
            warps.add((u16(wp + 8 * i), u16(wp + 8 * i + 2)))
    hits = []
    for y in range(hh):
        for x in range(w):
            v = u16(data + 2 * (y * w + x))
            mt, col = v & 0x3FF, (v >> 10) & 3
            beh = u16((pa if mt < 512 else sa) + 2 * (mt if mt < 512 else mt - 512)) & 0xFF
            if (beh in DOOR or beh in NONANIM) and (x, y) not in warps and col == 0:
                hits.append((x, y, mt, beh))
    if hits:
        count += len(hits)
        print(f'{g}/{n} header {h:08X} {w}x{hh}:', ', '.join(f'({x},{y}) mt {mt:03X} beh {b:02X}' for x, y, mt, b in hits))
print('tiles:', count)
