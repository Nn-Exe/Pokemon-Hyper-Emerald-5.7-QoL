"""Story ROM = conversation-only build PLUS the 663 code/table-loaded story strings.
Repoints high-ROM references (safe zone, 660/663). For strings with low-ROM code refs (3),
uses in-place if English fits; otherwise skips that string's low-ROM ref (rewrites only high refs).
Same safe free-space allocator + audit as patch_conv."""
import sys, json, glob, struct, re, collections, bisect as _bis
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
sys.path.insert(0, sp)
from inserter import encode_string

ROM_IN = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba"
ROM_OUT = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper Emerald v5.7 - Story English (experimental).gba"
FONT_LO, FONT_HI = 0xE3CF64, 0xF18F64
MARGIN = 768; MEGA = 0x1F82521; MAXREFS = 6
orig = open(ROM_IN, 'rb').read(); n=len(orig)
data = bytearray(orig)

def safe_text(en):
    if not en or en=='@@SKIP@@': return False
    if en.endswith(('\\p','\\n','\\l')): return False
    if en.count('[')!=en.count(']'): return False
    return True

# --- build addr->english: conversation (worklist + gap + gap2) + story ---
wl={}
for f in (r"\worklist2.json", r"\worklist3f.json"):
    d=json.load(open(sp+f,encoding='utf-8'))
    for t,a in d.items(): wl.setdefault(t,set()).update(a)
trans={}
for f in sorted(glob.glob(sp+r"\translations\trans_*.json")): trans.update(json.load(open(f,encoding='utf-8')))
addr_en={}
for zh,a in wl.items():
    en=trans.get(zh,'').strip()
    if safe_text(en):
        for x in a: addr_en[x]=en
gapn=0
for f in sorted(glob.glob(sp+r"\gaptrans\gap_*.json"))+sorted(glob.glob(sp+r"\gap2trans\gap2_*.json")):
    for a_hex,en in json.load(open(f,encoding='utf-8')).items():
        if safe_text((en or '').strip()): addr_en[int(a_hex,16)]=en.strip(); gapn+=1
storyn=0; story_addrs=set()
for f in sorted(glob.glob(sp+r"\storytrans\story_*.json")):
    for a_hex,en in json.load(open(f,encoding='utf-8')).items():
        if safe_text((en or '').strip()):
            addr_en[int(a_hex,16)]=en.strip(); storyn+=1; story_addrs.add(int(a_hex,16))
print(f"addr->english: {len(addr_en)} (conv gap {gapn}, story {storyn})")

# --- loadpointer targets (conversation path) ---
lp_targets=collections.defaultdict(list)
i=0
while True:
    i=orig.find(b'\x0f\x00',i)
    if i==-1: break
    v=struct.unpack_from('<I',orig,i+2)[0]
    if 0x08000000<=v<0x0A000000:
        t=v-0x08000000
        if 0<t<n: lp_targets[t].append(i+2)
    i+=1

# --- all pointer occurrences by value (for story high-ROM repointing) ---
val2occ=collections.defaultdict(list)
for occ in range(0,n-3):
    v=struct.unpack_from('<I',orig,occ)[0]
    if 0x08000000<=v<0x0A000000:
        t=v-0x08000000
        if 0<t<n: val2occ[v].append(occ)

# --- safe free-space pool (audited method: ALIGNED targets only, matches verified patch_conv) ---
_at=set()
for off in range(0, n-3, 4):
    v=struct.unpack_from('<I', orig, off)[0]
    if 0x08000000<=v<0x0A000000:
        t=v-0x08000000
        if 0<t<n: _at.add(t)
targets_list=sorted(_at)
def count_refs(s,e):
    lo=_bis.bisect_left(targets_list,s); hi=_bis.bisect_right(targets_list,e); return hi-lo
def safe_gaps(s,e):
    lo=_bis.bisect_left(targets_list,s-MARGIN); hi=_bis.bisect_right(targets_list,e)
    forbid=sorted((max(s,targets_list[i]-4),min(e,targets_list[i]+MARGIN)) for i in range(lo,hi))
    gaps=[];cur=s
    for fs,fe in forbid:
        if fs>cur: gaps.append([cur,fs])
        cur=max(cur,fe)
    if cur<e: gaps.append([cur,e])
    return gaps
pool=[]
for m in re.finditer(rb'\xff{64,}',orig):
    s,e=m.start(),m.end()
    if (e<=FONT_LO or s>=FONT_HI) and s<MEGA and count_refs(s,e)<=MAXREFS:
        for gs,ge in safe_gaps(s,e):
            if ge-gs>=16: pool.append([gs,ge])
pool.sort()
print("SAFE pool KB:", sum(e-s for s,e in pool)//1024)
placed={}
def place(b):
    if b in placed: return placed[b]
    for reg in pool:
        if reg[1]-reg[0]>=len(b):
            off=reg[0]; reg[0]=reg[0]+len(b)+1; placed[b]=off; return off
    return None
def extent_len(a):
    e=a
    while e<n and orig[e]!=0xFF: e+=1
    return e-a+1

stats=collections.Counter()

# (1) conversation via loadpointer (as patch_conv)
for t,occs in lp_targets.items():
    if t not in addr_en or t in story_addrs: continue
    enc=encode_string(addr_en[t])+b'\xff'; ext=extent_len(t)
    lo=_bis.bisect_left(targets_list,t+1); hi=_bis.bisect_left(targets_list,t+ext)
    internal=hi>lo
    if len(enc)<=ext and not internal:
        data[t:t+len(enc)]=enc
        for k in range(t+len(enc),t+ext): data[k]=0xFF
        stats['conv_inplace']+=1; continue
    off=place(bytes(enc))
    if off is None: stats['conv_nospace']+=1; continue
    data[off:off+len(enc)]=enc
    np_=struct.pack('<I',0x08000000+off)
    for po in occs:
        if po>=0x1DC000: data[po:po+4]=np_; stats['conv_rw']+=1
    stats['conv_reloc']+=1

# (2) story strings: repoint HIGH-ROM occs; low-ROM only via in-place-if-fits
import os
STORY_LIMIT = int(os.environ.get('STORY_LIMIT', '100000'))
STORY_MODE = os.environ.get('STORY_MODE', 'both')   # both | reloc | inplace
_story_sorted = sorted(story_addrs)[:STORY_LIMIT]
for t in _story_sorted:
    enc=encode_string(addr_en[t])+b'\xff'; ext=extent_len(t)
    occs=val2occ.get(0x08000000+t,[])
    lows=[o for o in occs if o<0x1DC000]; his=[o for o in occs if o>=0x1DC000]
    lo=_bis.bisect_left(targets_list,t+1); hi=_bis.bisect_left(targets_list,t+ext)
    internal=hi>lo
    # if fits in-place and no internal target: in-place covers ALL refs (low+high) safely
    if len(enc)<=ext and not internal:
        if STORY_MODE in ('both','inplace'):
            data[t:t+len(enc)]=enc
            for k in range(t+len(enc),t+ext): data[k]=0xFF
            stats['story_inplace']+=1
        continue
    if STORY_MODE=='inplace': continue
    # else relocate + rewrite HIGH-ROM refs only (low-ROM code refs left pointing to original)
    # only rewrite occurrences that look like GENUINE pointers: 4-aligned AND in a real
    # pointer context (a neighboring aligned slot is also a valid ROM pointer, i.e. a table/
    # literal pool), to avoid coincidental 4-byte matches in code/data.
    def genuine(o):
        if o % 4 != 0: return False
        for d in (-4, 4, -8, 8):
            q = o + d
            if 0 <= q <= n-4:
                w = struct.unpack_from('<I', orig, q)[0]
                if 0x08000000 <= w < 0x0A000000 and (w-0x08000000) < n:
                    return True
        return False
    his_ok = [o for o in his if genuine(o)]
    if not his_ok:
        stats['story_no_genuine_ref']+=1; continue
    off=place(bytes(enc))
    if off is None: stats['story_nospace']+=1; continue
    data[off:off+len(enc)]=enc
    np_=struct.pack('<I',0x08000000+off)
    for o in his_ok: data[o:o+4]=np_; stats['story_rw_hi']+=1
    if len(his_ok) < len(his): stats['story_ref_dropped']+= (len(his)-len(his_ok))
    if lows: stats['story_lowref_left']+=1
    stats['story_reloc']+=1

print(dict(stats))
# safety asserts
low=sum(1 for i in range(0,0x1DC000) if data[i]!=orig[i] and not (FONT_LO<=i<FONT_HI))
print("low-ROM code changes (must be 0):", low)
viol=0
for b,off in placed.items():
    lo=_bis.bisect_left(targets_list,off); hi=_bis.bisect_right(targets_list,off+len(b))
    viol+=hi-lo
print("placed overlapping pointer target (must be 0):", viol)
open(ROM_OUT,'wb').write(data)
print("wrote", ROM_OUT)
