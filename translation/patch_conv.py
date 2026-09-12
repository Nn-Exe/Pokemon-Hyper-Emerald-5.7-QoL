"""Conversation-only patcher: rewrite ONLY loadpointer (0F 00) dialogue targets.
Safest possible: loadpointer = guaranteed text load; targets = exactly what the game shows;
free space = audited-safe (no referenced regions); no table/coincidental/aligned rewrites."""
import sys, json, glob, struct, re, collections, bisect as _bis
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
sys.path.insert(0, sp)
from inserter import encode_string

ROM_IN = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba"
ROM_OUT = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper Emerald v5.7 - Full English.gba"
FONT_LO, FONT_HI = 0xE3CF64, 0xF18F64
MARGIN = 768
MEGA = 0x1F82521
MAXREFS = 6

orig = open(ROM_IN, 'rb').read(); n = len(orig)
data = bytearray(orig)

# ---- translations keyed by chinese text ----
wl = {}
for f in (r"\worklist2.json", r"\worklist3f.json"):
    d = json.load(open(sp + f, encoding='utf-8'))
    for t, addrs in d.items(): wl.setdefault(t, set()).update(addrs)
trans = {}
for f in sorted(glob.glob(sp + r"\translations\trans_*.json")): trans.update(json.load(open(f, encoding='utf-8')))

# ---- addr -> english  (from worklist addresses, using the game-authoritative address as-is) ----
def safe_text(en):
    if not en or en=='@@SKIP@@': return False
    if en.endswith('\\p') or en.endswith('\\n') or en.endswith('\\l'): return False
    if en.count('[')!=en.count(']'): return False
    return True
addr_en = {}
for zh, addrs in wl.items():
    en = trans.get(zh, '').strip()
    if not safe_text(en): continue
    for a in addrs:
        addr_en[a] = en
# merge address-keyed gap translations (strings my original extraction missed)
gapn = 0
for f in sorted(glob.glob(sp + r"\gaptrans\gap_*.json")) + sorted(glob.glob(sp + r"\gap2trans\gap2_*.json")):
    d = json.load(open(f, encoding='utf-8'))
    for a_hex, en in d.items():
        en = (en or '').strip()
        if safe_text(en):
            addr_en[int(a_hex, 16)] = en; gapn += 1
print("addresses with usable English:", len(addr_en), f"(+{gapn} from gap fill)")

# ---- find ALL loadpointer occurrences: 0F 00 <ptr 08/09> ----
# target addr -> list of occ offsets (the ptr bytes are at occ, i.e. right after 0F 00)
lp_targets = collections.defaultdict(list)
i = 0
while True:
    i = orig.find(b'\x0f\x00', i)
    if i == -1: break
    po = i + 2
    if po + 4 <= n:
        v = struct.unpack_from('<I', orig, po)[0]
        if 0x08000000 <= v < 0x0A000000:
            t = v - 0x08000000
            if 0 < t < n:
                lp_targets[t].append(po)
    i += 1
print("distinct loadpointer targets:", len(lp_targets))

# which loadpointer targets do we have english for?
todo = {t: addr_en[t] for t in lp_targets if t in addr_en}
print("loadpointer dialogue strings we can translate:", len(todo))

# ---- pointer targets set (for free-space safety) ----
targets_list = []
for off in range(0, n-3, 4):
    v = struct.unpack_from('<I', orig, off)[0]
    if 0x08000000 <= v < 0x0A000000:
        t = v - 0x08000000
        if 0 < t < n: targets_list.append(t)
targets_list = sorted(set(targets_list))

# ---- SAFE free-space pool (same audited method as patch_final3) ----
raw_runs=[]
for m in re.finditer(rb'\xff{64,}', orig):
    s,e=m.start(),m.end()
    if (e<=FONT_LO or s>=FONT_HI) and s < MEGA: raw_runs.append((s,e))
def count_refs(s,e):
    lo=_bis.bisect_left(targets_list,s); hi=_bis.bisect_right(targets_list,e); return hi-lo
def safe_gaps(s,e):
    lo=_bis.bisect_left(targets_list, s-MARGIN); hi=_bis.bisect_right(targets_list, e)
    forbid=sorted((max(s,targets_list[i]-4), min(e,targets_list[i]+MARGIN)) for i in range(lo,hi))
    gaps=[]; cur=s
    for fs,fe in forbid:
        if fs>cur: gaps.append([cur,fs])
        cur=max(cur,fe)
    if cur<e: gaps.append([cur,e])
    return gaps
pool=[]
for s,e in raw_runs:
    if count_refs(s,e) > MAXREFS: continue
    for gs,ge in safe_gaps(s,e):
        if ge-gs>=16: pool.append([gs,ge])
pool.sort()
print(f"SAFE pool: {sum(e-s for s,e in pool)//1024}KB in {len(pool)} chunks")

# ---- in-place if fits within the string's own extent (no relocation needed) ----
def extent_len(a):
    e=a
    while e<n and orig[e]!=0xFF: e+=1
    return e-a+1  # include terminator

placed={}
def place(b):
    if b in placed: return placed[b]
    for reg in pool:
        if reg[1]-reg[0]>=len(b):
            off=reg[0]; reg[0]=reg[0]+len(b)+1; placed[b]=off; return off
    return None

stats=dict(inplace=0, reloc=0, lp_rewrites=0, nospace=0, lowrom_skip=0)
# process each translatable loadpointer target
for t in sorted(todo):
    en = todo[t]
    enc = encode_string(en) + b'\xff'
    ext = extent_len(t)
    # does any accepted string boundary lie inside? for in-place we just need enc<=ext and no
    # pointer target strictly inside (t, t+len). Check for internal pointer targets:
    lo=_bis.bisect_left(targets_list, t+1); hi=_bis.bisect_left(targets_list, t+ext)
    internal = hi>lo
    occs = lp_targets[t]
    if len(enc) <= ext and not internal:
        # in-place: overwrite, pad to extent with 0xFF
        data[t:t+len(enc)] = enc
        for k in range(t+len(enc), t+ext): data[k]=0xFF
        stats['inplace']+=1
        continue
    # relocate to safe free space, rewrite the loadpointer(s)
    off = place(bytes(enc))
    if off is None: stats['nospace']+=1; continue
    data[off:off+len(enc)] = enc
    newptr = struct.pack('<I', 0x08000000+off)
    for po in occs:
        if po < 0x1DC000:   # never touch low-ROM (shouldn't happen for script data, but guard)
            stats['lowrom_skip']+=1; continue
        data[po:po+4] = newptr
        stats['lp_rewrites']+=1
    stats['reloc']+=1
print(stats)

# ---- safety asserts ----
low=sum(1 for i in range(0,0x1DC000) if data[i]!=orig[i] and not (FONT_LO<=i<FONT_HI))
print("low-ROM code changes (must be 0):", low)
viol=0
for b,off in placed.items():
    lo=_bis.bisect_left(targets_list,off); hi=_bis.bisect_right(targets_list,off+len(b))
    viol+=hi-lo
print("placed strings overlapping a pointer target (must be 0):", viol)
open(ROM_OUT,'wb').write(data)
print("wrote", ROM_OUT)
