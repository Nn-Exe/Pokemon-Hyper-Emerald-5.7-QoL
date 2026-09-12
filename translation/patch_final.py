"""Final patcher: deterministic allocation + drop shifted-dup addresses + strict gate."""
import sys, json, glob, struct, re, collections, bisect as _bis
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
sys.path.insert(0, sp)
from inserter import encode_string

ROM_IN = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba"
ROM_OUT = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper Emerald v5.7 - Full English.gba"
FONT_LO, FONT_HI = 0xE3CF64, 0xF18F64
orig = open(ROM_IN, 'rb').read()
data = bytearray(orig)
n = len(orig)

wl = {}
for f in (r"\worklist2.json", r"\worklist3f.json"):
    d = json.load(open(sp + f, encoding='utf-8'))
    for t, addrs in d.items():
        wl.setdefault(t, set()).update(addrs)
trans = {}
for f in sorted(glob.glob(sp + r"\translations\trans_*.json")):
    trans.update(json.load(open(f, encoding='utf-8')))

# ---- eligibility (quality) ----
PART = set('的了是我你他她它们在有不就吗呢啊吧和与被给到要会能可这那什么没很才请谢对进出来去说想看知道让为着从但如果因所以还也都把等就已经再最好多少大小新旧前后上下里外中间东西南北左右开关门路山水火电风雨日月年天时分秒些个只条张片块')
PUNCT = set('。,!?、:…')
NAME_BANKS = {0x31, 0x32, 0x33, 0x5B, 0x155, 0x160, 0x161, 0x1D2, 0x1D3, 0x1D7, 0x1D8, 0x2E, 0x2F, 0x30}
def text_quality(t):
    hz = [c for c in t if '一' <= c <= '鿿']
    if not hz: return False
    if '[?' in t: return False
    freq = collections.Counter(hz)
    if len(hz) > 8 and freq.most_common(1)[0][1] / len(hz) > 0.3: return False
    has_p = any(c in PART for c in hz) or any(c in PUNCT for c in t) or '\\p' in t or '\\n' in t
    if not has_p: return False
    if len(hz) >= 12:
        pd = sum(1 for c in hz if c in PART) / len(hz)
        if pd < 0.10 and not any(c in PUNCT for c in t): return False
    return True
def eligible(zh, addrs):
    if any(a < 0x1DC000 for a in addrs): return False
    if text_quality(zh): return True
    hz = sum(1 for c in zh if '一' <= c <= '鿿')
    if 2 <= hz <= 14 and '[?' not in zh and all((a >> 16) in NAME_BANKS for a in addrs): return True
    return False

# ---- extents over ALL worklist addresses (for shifted-dup detection) ----
all_addrs = set()
for t, addrs in wl.items(): all_addrs.update(addrs)
def extent_end(a):
    e = a
    while e < n and orig[e] != 0xFF: e += 1
    return e
ext_end_all = {a: extent_end(a) for a in all_addrs}
sorted_all = sorted(all_addrs)
# an address B is a shifted-dup if some A < B has A.start<B<A.end
def is_shifted(a):
    i = _bis.bisect_left(sorted_all, a) - 1
    while i >= 0:
        pa = sorted_all[i]
        if ext_end_all[pa] > a:
            return True
        # earlier starts could still cover a only if their extent reaches; extents are contiguous text so one back is enough in practice, but check a few
        if a - pa > 1000: break
        i -= 1
    return False

kept = {}
drop_q = drop_shift = 0
for zh, addrs in wl.items():
    en = trans.get(zh, '').strip()
    if not en or en == '@@SKIP@@': continue
    if not eligible(zh, addrs):
        drop_q += 1; continue
    good_addrs = [a for a in addrs if not is_shifted(a)]
    n_shift = len(addrs) - len(good_addrs)
    drop_shift += n_shift
    if good_addrs:
        kept[zh] = (sorted(good_addrs), en)
print(f"kept {len(kept)} | dropped quality {drop_q} | dropped shifted addrs {drop_shift}")

# ---- static ptr structures ----
aligned_targets = set()
for off in range(0, n-3, 4):
    v = struct.unpack_from('<I', orig, off)[0]
    if 0x08000000 <= v < 0x0A000000:
        t = v - 0x08000000
        if 0 < t < n: aligned_targets.add(t)
accepted_addrs = set()
for zh, (addrs, en) in kept.items(): accepted_addrs.update(addrs)
ext_cache = {a: extent_end(a) - a + 1 for a in accepted_addrs}
def has_internal(a):
    for x in range(a+1, a+ext_cache[a]):
        if x in aligned_targets or x in accepted_addrs: return True
    return False
internal_cache = {a: has_internal(a) for a in accepted_addrs}
_ivals = sorted((a, a + ext_cache[a]) for a in accepted_addrs)
_starts = [x[0] for x in _ivals]
def in_accepted_extent(x):
    i = _bis.bisect_right(_starts, x) - 1
    return i >= 0 and _ivals[i][0] <= x < _ivals[i][1]
def occ_ok(occ):
    if FONT_LO <= occ < FONT_HI: return False
    if occ < 0x1DC000: return False       # never touch low-ROM code / fixed-data pointer literals
    if in_accepted_extent(occ): return False
    if occ % 4 == 0: return True
    if orig[occ-2:occ] == b'\x0f\x00': return True
    if orig[occ-1] == 0x67: return True
    if orig[occ-1] in (0x08, 0x09): return True
    if occ+5 < n and orig[occ+4] == 0x09 and orig[occ+5] <= 0x0A: return True
    if occ+7 < n and orig[occ+7] in (0x08, 0x09): return True
    return False

inplace = []; repoint = []
for zh, (addrs, en) in kept.items():
    enc = encode_string(en) + b'\xff'
    for a in addrs:
        if len(enc) <= ext_cache[a] and not internal_cache[a]:
            inplace.append((a, enc))
        else:
            repoint.append((a, enc))
print("in-place:", len(inplace), "repoint:", len(repoint))

# ---- deterministic pool + allocation ----
pool = []
for m in re.finditer(rb'\xff{2048,}', orig):
    s, e = m.start()+8, m.end()-8
    if e <= FONT_LO or s >= FONT_HI:
        if e - s >= 512: pool.append([s, min(e, 0x1FFFF00)])
pool.sort()
placed = {}
def place(b):
    if b in placed: return placed[b]
    for reg in pool:
        if reg[1] - reg[0] >= len(b):
            off = reg[0]; reg[0] = (reg[0] + len(b) + 3) & ~3
            placed[b] = off
            return off
    raise MemoryError("pool exhausted")
# DETERMINISTIC: sort by (len desc, bytes)
for b in sorted({bytes(enc) for _, enc in repoint}, key=lambda x: (-len(x), x)):
    place(b)
print("placed unique:", len(placed), "| pool used",
      sum((STAT_used := 0) for _ in [0]) or (sum(e0 - s0 for (s0, e0) in
      [(m.start()+8, min(m.end()-8, 0x1FFFF00)) for m in re.finditer(rb'\xff{2048,}', orig)
       if (m.end()-8) <= FONT_LO or (m.start()+8) >= FONT_HI]) ) // 1024, "KB avail")

# ---- write ----
for b, off in placed.items(): data[off:off+len(b)] = b
for a, enc in inplace:
    data[a:a+len(enc)] = enc
    for k in range(a+len(enc), a+ext_cache[a]): data[k] = 0xFF
stats = dict(ptrw=0, occ_rej=0, noptr=0)
for a, enc in repoint:
    newoff = placed[bytes(enc)]
    oldptr = struct.pack('<I', 0x08000000 + a)
    newptr = struct.pack('<I', 0x08000000 + newoff)
    wrote = 0
    i = orig.find(oldptr)
    while i != -1:
        if occ_ok(i):
            data[i:i+4] = newptr; wrote += 1
        else:
            stats['occ_rej'] += 1
        i = orig.find(oldptr, i+1)
    stats['ptrw'] += wrote
    if wrote == 0: stats['noptr'] += 1
print(stats)
open(ROM_OUT, 'wb').write(data)
print("wrote", ROM_OUT)
