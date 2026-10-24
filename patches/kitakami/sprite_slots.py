"""sprite_slots.py <rom>: which entries of the hack's sprite table (0x0839CF00, 0x24 each, drawn by an object with
graphics 0x4E and the entry in its template's fourth byte) any map object uses, and which entries look blank (a
16x32 placeholder like the four Area Zero reused: 127, 212, 225, 227) - candidates for Kitakami's people.

For every map of every group: its objects (24 bytes each) with graphics 0x4E -> the entry. Also counted: every
script command createvobject (0xAA, graphics id then...) and every literal 0x4E-with-entry pair is NOT searched -
see the notes printed at the end."""
import collections, hashlib, struct, sys

rom = open(sys.argv[1], "rb").read()
u16 = lambda o: struct.unpack_from("<H", rom, o)[0]
u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
ok = lambda p: 0x08000000 <= p < 0x0A000000
MAP_GROUPS, EXT = 0x00A54698, 0x0039CF00

# every map: groups until the pointers stop being ROM addresses
groups = []
g = 0
while ok(u32(MAP_GROUPS + 4 * g)):
    groups.append(u32(MAP_GROUPS + 4 * g) - 0x08000000); g += 1
starts = sorted(set(groups))
use = collections.Counter(); where = collections.defaultdict(list); vanilla = collections.Counter()
nmaps = 0
for gi, ga in enumerate(groups):
    nxt = min([s for s in starts if s > ga], default=None)
    n = 0
    while True:
        o = ga + 4 * n
        if nxt is not None and o >= nxt: break
        h = u32(o)
        if not ok(h): break
        h -= 0x08000000
        if not ok(u32(h)): break
        ev = u32(h + 4)
        if ok(ev):
            ev -= 0x08000000
            cnt, objs = rom[ev], u32(ev + 4)
            if cnt and ok(objs):
                objs -= 0x08000000
                for k in range(cnt):
                    gfx, ext = rom[objs + 24 * k + 1], rom[objs + 24 * k + 3]
                    if gfx == 0x4E:
                        use[ext] += 1; where[ext].append("%d/%d" % (gi, n))
                    else:
                        vanilla[gfx] += 1
        n += 1; nmaps += 1
print("groups %d, maps %d" % (len(groups), nmaps))

pics = collections.Counter()
entries = []
for i in range(256):
    e = rom[EXT + 0x24 * i:EXT + 0x24 * i + 0x24]
    if e == b"\x0F" * 0x24:
        entries.append((i, None)); continue
    tile, pal, refl, size, w, h = struct.unpack_from("<HHHHhh", e, 0)
    images = struct.unpack_from("<I", e, 0x1C)[0]
    first = None
    if ok(images):
        fp, fs = struct.unpack_from("<IH", rom, images - 0x08000000)
        if ok(fp):
            first = hashlib.sha1(rom[fp - 0x08000000:fp - 0x08000000 + fs]).hexdigest()[:10]
            blank = not any(rom[fp - 0x08000000:fp - 0x08000000 + fs])
    entries.append((i, (pal, size, w, h, images, first, blank if first else None)))
    if first: pics[first] += 1

unused = []
for i, info in entries:
    if info is None:
        continue
    pal, size, w, h, images, first, blank = info
    if use[i] == 0:
        unused.append(i)
print("entries no map object uses: %d" % len(unused))
for i in unused:
    pal, size, w, h, images, first, blank = entries[i][1]
    print("  %3d  %dx%d pal %04X images %08X first frame %s%s%s" % (
        i, w, h, pal, images, first, "  BLANK PICTURE" if blank else "",
        "  (same picture as %d other entries)" % (pics[first] - 1) if pics[first] > 1 else ""))
print("filler (0x0F) entries:", [i for i, info in entries if info is None])
