"""patch_final3: SAFE free-space allocation (avoid referenced regions + pointer-target margins).
Keeps: eligibility/quality filter, shifted-dup removal, low-ROM occ guard, deterministic alloc."""
import sys, json, glob, struct, re, collections, bisect as _bis
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
sys.path.insert(0, sp)
from inserter import encode_string

ROM_IN = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba"
ROM_OUT = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper Emerald v5.7 - Full English.gba"
FONT_LO, FONT_HI = 0xE3CF64, 0xF18F64
MARGIN = 768          # bytes after a pointer target to keep clear (covers fixed-length struct reads)
MEGA = 0x1F82521      # reserved expansion mega-region start (exclude entirely)
MAXREFS = 6           # exclude free runs with more inbound pointer refs than this

orig = open(ROM_IN, 'rb').read(); n = len(orig)
data = bytearray(orig)

wl = {}
for f in (r"\worklist2.json", r"\worklist3f.json"):
    d = json.load(open(sp + f, encoding='utf-8'))
    for t, addrs in d.items(): wl.setdefault(t, set()).update(addrs)
trans = {}
for f in sorted(glob.glob(sp + r"\translations\trans_*.json")): trans.update(json.load(open(f, encoding='utf-8')))

# ---- all pointer targets (for both free-space safety and occ gating) ----
targets_set = set(); targets_list = []
for off in range(0, n-3, 4):
    v = struct.unpack_from('<I', orig, off)[0]
    if 0x08000000 <= v < 0x0A000000:
        t = v - 0x08000000
        if 0 < t < n: targets_set.add(t)
targets_list = sorted(targets_set)

# ---- eligibility ----
PART = set('的了是我你他她它们在有不就吗呢啊吧和与被给到要会能可这那什么没很才请谢对进出来去说想看知道让为着从但如果因所以还也都把等就已经再最好多少大小新旧前后上下里外中间东西南北左右开关门路山水火电风雨日月年天时分秒些个只条张片块')
PUNCT = set('。,!?、:…')
NAME_BANKS = {0x31,0x32,0x33,0x5B,0x155,0x160,0x161,0x1D2,0x1D3,0x1D7,0x1D8,0x2E,0x2F,0x30}
def text_quality(t):
    hz=[c for c in t if '一'<=c<='鿿']
    if not hz or '[?' in t: return False
    fr=collections.Counter(hz)
    if len(hz)>8 and fr.most_common(1)[0][1]/len(hz)>0.3: return False
    if not (any(c in PART for c in hz) or any(c in PUNCT for c in t) or '\\p' in t or '\\n' in t): return False
    if len(hz)>=12 and sum(1 for c in hz if c in PART)/len(hz)<0.10 and not any(c in PUNCT for c in t): return False
    return True
def eligible(zh, addrs):
    if any(a < 0x1DC000 for a in addrs): return False
    if text_quality(zh): return True
    hz=sum(1 for c in zh if '一'<=c<='鿿')
    if 2<=hz<=14 and '[?' not in zh and all((a>>16) in NAME_BANKS for a in addrs): return True
    return False
def safe_text(en):
    if en.endswith('\\p') or en.endswith('\\n') or en.endswith('\\l'): return False
    if en.count('[')!=en.count(']'): return False
    return True
all_addrs=set()
for t,addrs in wl.items(): all_addrs.update(addrs)
def ext_end(a):
    e=a
    while e<n and orig[e]!=0xFF: e+=1
    return e
ext_end_all={a:ext_end(a) for a in all_addrs}
sorted_all=sorted(all_addrs)
def is_shifted(a):
    i=_bis.bisect_left(sorted_all,a)-1
    while i>=0:
        pa=sorted_all[i]
        if ext_end_all[pa]>a: return True
        if a-pa>1000: break
        i-=1
    return False
kept={}
for zh,addrs in wl.items():
    en=trans.get(zh,'').strip()
    if not en or en=='@@SKIP@@' or not eligible(zh,addrs) or not safe_text(en): continue
    good=[a for a in addrs if not is_shifted(a)]
    if good: kept[zh]=(sorted(good),en)
print("kept:",len(kept))

accepted=set()
for zh,(addrs,en) in kept.items(): accepted.update(addrs)
ext_cache={a:ext_end(a)-a+1 for a in accepted}
def has_internal(a):
    for x in range(a+1,a+ext_cache[a]):
        if x in targets_set or x in accepted: return True
    return False
internal_cache={a:has_internal(a) for a in accepted}
_iv=sorted((a,a+ext_cache[a]) for a in accepted); _st=[x[0] for x in _iv]
def in_accepted_extent(x):
    i=_bis.bisect_right(_st,x)-1
    return i>=0 and _iv[i][0]<=x<_iv[i][1]
def occ_ok(occ):
    if FONT_LO<=occ<FONT_HI: return False
    if occ<0x1DC000: return False
    if in_accepted_extent(occ): return False
    if occ%4==0: return True
    if orig[occ-2:occ]==b'\x0f\x00': return True
    if orig[occ-1]==0x67: return True
    if orig[occ-1] in (0x08,0x09): return True
    if occ+5<n and orig[occ+4]==0x09 and orig[occ+5]<=0x0A: return True
    if occ+7<n and orig[occ+7] in (0x08,0x09): return True
    return False

# ---- SAFE free-space pool (GLOBAL pointer margins, cross-run) ----
raw_runs=[]
for m in re.finditer(rb'\xff{64,}', orig):
    s,e=m.start(),m.end()
    if (e<=FONT_LO or s>=FONT_HI) and s < MEGA:     # exclude font + mega expansion region
        raw_runs.append((s,e))
def count_refs(s,e):
    lo=_bis.bisect_left(targets_list,s); hi=_bis.bisect_right(targets_list,e)
    return hi-lo
# For each candidate run, subtract [T-4, T+MARGIN] for EVERY target T (anywhere) that overlaps
# the run's window. This closes the cross-run gap: a target just before a run still reserves
# bytes inside it.
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
    if count_refs(s,e) > MAXREFS:      # skip reserved/high-density runs entirely
        continue
    for gs,ge in safe_gaps(s,e):
        if ge-gs>=16: pool.append([gs,ge])
pool.sort()
poolcap=sum(e-s for s,e in pool)
print(f"SAFE pool: {poolcap//1024}KB in {len(pool)} chunks (mega-region + high-density runs excluded, global margins)")

# ---- plan ----
inplace=[]; repoint=[]
for zh,(addrs,en) in kept.items():
    enc=encode_string(en)+b'\xff'
    for a in addrs:
        if len(enc)<=ext_cache[a] and not internal_cache[a]: inplace.append((a,enc))
        else: repoint.append((a,enc))
need=sum(len(b) for b in {bytes(e) for _,e in repoint})
print(f"in-place: {len(inplace)} | repoint: {len(repoint)} | unique bytes needed: {need//1024}KB")

placed={}
def place(b):
    if b in placed: return placed[b]
    for reg in pool:
        if reg[1]-reg[0]>=len(b):
            off=reg[0]; reg[0]=(reg[0]+len(b)+1)  # +1 gap; no forced align (safe gaps are byte-granular)
            placed[b]=off; return off
    return None
unplaced=0
for b in sorted({bytes(e) for _,e in repoint},key=lambda x:(-len(x),x)):
    if place(b) is None: unplaced+=1
print("placed:",len(placed),"| could-not-place:",unplaced)

# ---- write ----
for b,off in placed.items(): data[off:off+len(b)]=b
for a,enc in inplace:
    data[a:a+len(enc)]=enc
    for k in range(a+len(enc),a+ext_cache[a]): data[k]=0xFF
stats=dict(ptrw=0,occ_rej=0,noptr=0,skip_unplaced=0)
for a,enc in repoint:
    key=bytes(enc)
    if key not in placed: stats['skip_unplaced']+=1; continue
    newoff=placed[key]
    oldptr=struct.pack('<I',0x08000000+a); newptr=struct.pack('<I',0x08000000+newoff)
    wrote=0; i=orig.find(oldptr)
    while i!=-1:
        if occ_ok(i): data[i:i+4]=newptr; wrote+=1
        else: stats['occ_rej']+=1
        i=orig.find(oldptr,i+1)
    stats['ptrw']+=wrote
    if wrote==0: stats['noptr']+=1
print(stats)
# safety asserts
bad=0
for i in range(0,0x1DC000):
    if data[i]!=orig[i] and not (FONT_LO<=i<FONT_HI): bad+=1
print("low-ROM changed bytes (must be 0):", bad)
# verify no write landed on a pointer target
viol=0
for b,off in placed.items():
    lo=_bis.bisect_left(targets_list,off); hi=_bis.bisect_right(targets_list,off+len(b))
    viol += hi-lo
print("placed strings overlapping a pointer target (must be 0):", viol)
open(ROM_OUT,'wb').write(data)
print("wrote",ROM_OUT)
