import struct, json, glob, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
orig = open(r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba", 'rb').read()
n = len(orig)

# encode target hanzi to (lead,second) to locate the string in ROM
gb=[]
for hi in range(0xB0,0xF8):
    for lo in range(0xA1,0xFF):
        try: gb.append(bytes([hi,lo]).decode('gb2312'))
        except Exception: gb.append('�')
def adj(l):
    a=l-1
    if l>6: a-=1
    if l>0x1B: a-=1
    return a
LEADS=[l for l in range(1,0x1F) if l not in (6,0x1B)]
rev={}
for l in LEADS:
    for s in range(0xF7):
        o=adj(l)*247+s
        if o<len(gb): rev.setdefault(gb[o], bytes([l,s]))
def enc(txt):
    b=b''
    for ch in txt:
        if ch not in rev: return None
        b+=rev[ch]
    return b

# distinctive substring
target = "好喜欢猫猫"
pat = enc(target)
print("pattern for", target, ":", pat.hex(' ') if pat else "CANNOT ENCODE")
hits=[]
if pat:
    i=orig.find(pat)
    while i!=-1: hits.append(i); i=orig.find(pat,i+1)
print("hits:", [hex(h) for h in hits])

for h in hits:
    s=h
    while s>0 and orig[s-1]!=0xFF: s-=1
    print(f"\nstring start: {s:#x}")
    # loadpointer to it?
    val=0x08000000+s; p=struct.pack('<I',val)
    lps=[]
    i=0
    while True:
        i=orig.find(b'\x0f\x00',i)
        if i==-1: break
        if orig.find(p, i+2, i+6)==i+2 or struct.unpack_from('<I',orig,i+2)[0]==val: lps.append(i+2)
        i+=1
    # simpler: all pointer occurrences
    allp=[]; j=orig.find(p)
    while j!=-1: allp.append((j, orig[j-2:j]==b'\x0f\x00')); j=orig.find(p,j+1)
    print("  pointer occurrences:", [(hex(o), 'LOADPTR' if lp else 'other') for o,lp in allp])

    # decode
    def hz(l,ss):
        if ss>0xF6: return None
        o=adj(l)*247+ss
        return gb[o] if o<len(gb) else None
    txt=''; k=s
    while k<s+120 and orig[k]!=0xFF:
        b=orig[k]
        if b in LEADS: c=hz(b,orig[k+1]); txt+=c if c else '?'; k+=2; continue
        if b in (0xFD,0xFC,0xF8,0xF9): txt+='{x}'; k+=2; continue
        k+=1
    hzs=[c for c in txt if '一'<=c<='鿿']
    fr=collections.Counter(hzs)
    toprep = fr.most_common(1)[0][1]/len(hzs) if hzs else 0
    print(f"  decoded: {txt[:50]}")
    print(f"  hanzi={len(hzs)} top-char-repetition={toprep:.0%}  (filter drops if >30% and >6 hanzi)")

    # is it in lp_missing / lp_real_missing / gaptrans?
    for fn in ("lp_missing.json","lp_real_missing.json"):
        d=json.load(open(sp+"\\"+fn,encoding='utf-8'))
        print(f"  in {fn}: {hex(s) in d}")
    # translated anywhere?
    trans={}
    for f in sorted(glob.glob(sp+r"\translations\trans_*.json")): trans.update(json.load(open(f,encoding='utf-8')))
    gap={}
    for f in sorted(glob.glob(sp+r"\gaptrans\gap_*.json")): gap.update(json.load(open(f,encoding='utf-8')))
    print("  in gaptrans (addr-keyed):", hex(s) in gap, '->', repr(gap.get(hex(s),'')[:50]))
