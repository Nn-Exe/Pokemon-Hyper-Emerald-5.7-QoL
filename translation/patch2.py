"""Final unified patcher: worklist2 (aligned corpus) + worklist3f (delta), context-gated repointing."""
import sys, json, glob, struct
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
sys.path.insert(0, sp)
from inserter import encode_string

ROM_IN = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba"
ROM_OUT = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper Emerald v5.7 - Full English.gba"

FREE_START = 0x1F82530
FREE_END   = 0x1FFFF00
FONT_LO, FONT_HI = 0xE3CF64, 0xF18F64

orig = open(ROM_IN, 'rb').read()
data = bytearray(orig)
n = len(data)

wl = {}
for f, src in ((r"\worklist2.json", 'main'), (r"\worklist3f.json", 'delta')):
    d = json.load(open(sp + f, encoding='utf-8'))
    for t, addrs in d.items():
        wl.setdefault(t, set()).update(addrs)
print("total unique texts:", len(wl))

trans = {}
for f in sorted(glob.glob(sp + r"\translations\trans_*.json")):
    trans.update(json.load(open(f, encoding='utf-8')))
print("translations:", len(trans))

# extent + internal-target computation needs the target set (aligned+unaligned would be huge; use accepted addrs only for internal check + aligned targets)
aligned_targets = set()
for off in range(0, n-3, 4):
    v = struct.unpack_from('<I', orig, off)[0]
    if 0x08000000 <= v < 0x0A000000:
        t = v - 0x08000000
        if 0 < t < n: aligned_targets.add(t)
accepted_addrs = set()
for t, addrs in wl.items(): accepted_addrs.update(addrs)

def extent_of(a):
    e = a
    while e < n and orig[e] != 0xFF: e += 1
    return e - a + 1

def has_internal(a, ext):
    for x in range(a+1, a+ext):
        if x in aligned_targets or x in accepted_addrs:
            return True
    return False

# interval index of accepted string extents (occurrences inside them must not be rewritten)
import bisect
_ivals = sorted((a, a + extent_of(a)) for a in accepted_addrs)
_starts = [x[0] for x in _ivals]
def in_accepted_extent(x):
    i = bisect.bisect_right(_starts, x) - 1
    return i >= 0 and _ivals[i][0] <= x < _ivals[i][1]

def occ_ok(occ):
    """context gate for pointer rewrite"""
    if FONT_LO <= occ < FONT_HI or occ >= FREE_START: return False
    if in_accepted_extent(occ): return False
    if occ % 4 == 0: return True
    pre2 = bytes(orig[occ-2:occ])
    if pre2 == b'\x0f\x00': return True
    if orig[occ-1] == 0x67: return True          # preparemsg
    if orig[occ-1] in (0x08, 0x09): return True  # follows another pointer (array)
    if occ+4 < n and orig[occ+4] == 0x09 and orig[occ+5] <= 0x0A: return True  # callstd follows
    if occ+7 < n and orig[occ+7] in (0x08, 0x09): return True  # another pointer follows
    return False

alloc = FREE_START
placed = {}
def place(b):
    global alloc
    if b in placed: return placed[b]
    off = alloc
    if off + len(b) >= FREE_END: raise MemoryError("free space exhausted")
    data[off:off+len(b)] = b
    placed[b] = off
    alloc = (off + len(b) + 3) & ~3
    return off

stats = dict(texts=0, skip=0, missing=0, inplace=0, repoint=0, ptrw=0, occ_rej=0, noptr=0)
log = open(sp + r"\patch2_log.txt", 'w', encoding='utf-8')

for zh, addrs in wl.items():
    en = trans.get(zh)
    if en is None:
        stats['missing'] += 1; log.write(f"MISSING\t{zh[:70]}\n"); continue
    en = en.strip()
    if en == '@@SKIP@@' or not en:
        stats['skip'] += 1; continue
    enc = encode_string(en) + b'\xff'
    stats['texts'] += 1
    for a in sorted(addrs):
        ext = extent_of(a)
        if len(enc) <= ext and not has_internal(a, ext):
            data[a:a+len(enc)] = enc
            for k in range(a+len(enc), a+ext): data[k] = 0xFF
            stats['inplace'] += 1
            continue
        newoff = place(enc)
        oldptr = struct.pack('<I', 0x08000000 + a)
        newptr = struct.pack('<I', 0x08000000 + newoff)
        wrote = 0
        i = orig.find(oldptr)
        while i != -1:
            if occ_ok(i):
                data[i:i+4] = newptr
                wrote += 1
            else:
                stats['occ_rej'] += 1
            i = orig.find(oldptr, i+1)
        stats['ptrw'] += wrote
        stats['repoint'] += 1
        if wrote == 0:
            stats['noptr'] += 1
            log.write(f"NOPTR\t{hex(a)}\t{zh[:60]}\n")

print(stats)
print("free used:", (alloc-FREE_START)//1024, "KB /", (FREE_END-FREE_START)//1024, "KB")
open(ROM_OUT, 'wb').write(data)
log.close()
manifest = {off: b.hex() for b, off in list(placed.items())[:0]}  # keep small
json.dump({'alloc_end': alloc, 'placed_count': len(placed),
           'samples': [[off, len(b)] for b, off in sorted(placed.items(), key=lambda kv: kv[1])[:12]]},
          open(sp + r"\patch2_manifest.json", 'w'))
print("wrote", ROM_OUT)
