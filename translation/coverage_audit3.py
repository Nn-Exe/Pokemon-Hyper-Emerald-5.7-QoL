"""True distinct leftover dialogue count: strict real dialogue, starting at a real boundary
(after 0xFF), not inside any covered string's extent. Then find what opcodes load them."""
import struct, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
orig = open(r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba", 'rb').read()
new  = open(r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper Emerald v5.7 - Full English.gba", 'rb').read()
n=len(orig)
gb=[]
for hi in range(0xB0,0xF8):
    for lo in range(0xA1,0xFF):
        try: gb.append(bytes([hi,lo]).decode('gb2312'))
        except Exception: gb.append('�')
def adj(l):
    a=l-1
    if l>6:a-=1
    if l>0x1B:a-=1
    return a
LEADS=set(range(0x01,0x1F))-{0x06,0x1B}
def hz(l,s):
    if s>0xF6: return None
    o=adj(l)*247+s
    return gb[o] if o<len(gb) else None
PART=set('的了是我你他她它们在有不就吗呢啊吧和与到要会能可这那什么没很才请谢对来去说想看知道让为但如果因所以还也都把等')
_l1c={}
def l1(c):
    if c in _l1c: return _l1c[c]
    try: r=0xB0<=c.encode('gb2312')[0]<=0xD7
    except Exception: r=False
    _l1c[c]=r; return r
def strict(t, maxlen=1200):
    i=t; hzs=[]
    while i<n and i-t<maxlen:
        b=orig[i]
        if b==0xFF: break
        if b in LEADS:
            c=hz(b,orig[i+1]);
            if c: hzs.append(c)
            i+=2; continue
        if b in (0xFD,0xFC,0xF8,0xF9): i+=2; continue
        i+=1
    if len(hzs)<5 or len(hzs)>200: return False
    if sum(1 for c in hzs if l1(c))/len(hzs)<0.90: return False
    mc=1;cur=1;prev=None
    for c in hzs:
        if c==prev:cur+=1;mc=max(mc,cur)
        else:cur=1
        prev=c
    if mc>=4: return False
    if len({c for c in hzs if c in PART})<2: return False
    if collections.Counter(hzs).most_common(1)[0][1]/len(hzs)>0.35: return False
    return True

ref=collections.defaultdict(list)
for occ in range(0,n-3):
    v=struct.unpack_from('<I',orig,occ)[0]
    if 0x08000000<=v<0x0A000000:
        t=v-0x08000000
        if 0<t<n: ref[t].append(occ)

# covered strings and their extents
def extent(t):
    e=t
    while e<n and orig[e]!=0xFF: e+=1
    return e
covered_extents=[]
real=[t for t in ref if strict(t)]
for t in real:
    if any(new[o:o+4]!=orig[o:o+4] for o in ref[t]):
        covered_extents.append((t, extent(t)))
covered_extents.sort()
cs=[x[0] for x in covered_extents]
import bisect
def inside_covered(a):
    i=bisect.bisect_right(cs,a)-1
    return i>=0 and covered_extents[i][0]<=a<covered_extents[i][1]

# TRUE leftover: strict real, starts at boundary (orig[t-1]==0xFF), not covered, not inside covered extent
true_left=[]
for t in real:
    if any(new[o:o+4]!=orig[o:o+4] for o in ref[t]): continue   # covered
    if t>0 and orig[t-1]!=0xFF: continue                         # mid-string (shifted dup)
    if inside_covered(t): continue
    true_left.append(t)
print("TRUE distinct leftover dialogue (real boundary, not covered, not shifted-dup):", len(true_left))
tot_hz=0
for t in true_left:
    i=t
    while orig[i]!=0xFF and i-t<1200: i+=1
print("that's the honest 'missed dialogue' number.")

# categorize by loadpointer vs other
lp=[t for t in true_left if any(orig[o-2:o]==b'\x0f\x00' for o in ref[t])]
oth=[t for t in true_left if t not in lp]
print(f"  via loadpointer (should add, easy): {len(lp)}")
print(f"  via other opcode only (blind spot): {len(oth)}")

def dec(t):
    i=t;s=''
    while i<n and i-t<70:
        b=orig[i]
        if b==0xFF:break
        if b in LEADS: c=hz(b,orig[i+1]); s+=c if c else '?'; i+=2; continue
        if b in (0xFD,0xFC,0xF8,0xF9): s+='{x}'; i+=2; continue
        if b in (0xFE,0xFB,0xFA): s+=' '; i+=1; continue
        s+='.'; i+=1
    return s
print("\nsample TRUE leftover (real dialogue still Chinese):")
for t in true_left[:20]:
    haslp = any(orig[o-2:o]==b'\x0f\x00' for o in ref[t])
    print(f"  {t:#x} {'LP' if haslp else 'other'}: {dec(t)}")
import json
json.dump([hex(t) for t in true_left], open(r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad\true_leftover.json","w"))
