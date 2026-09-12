"""Enumerate ALL loadpointer dialogue targets, decode, and measure translation coverage."""
import struct, json, glob, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
orig = open(r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba", 'rb').read()
n = len(orig)

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
LEADS=set(range(1,0x1F))-{6,0x1B}
def hz(l,s):
    if s>0xF6: return None
    o=adj(l)*247+s
    return gb[o] if o<len(gb) else None
std={0x00:' '}
for i in range(10): std[0xA1+i]=chr(48+i)
for i in range(26): std[0xBB+i]=chr(65+i)
for i in range(26): std[0xD5+i]=chr(97+i)
std.update({0xAB:'!',0xAC:'?',0xAD:'.',0xAE:'-',0xB8:',',0xB4:"'",0xBA:'/',0x1B:'e'})
SGL={0x37:'。',0x3b:',',0x3c:'!',0x3d:'?',0x3e:':',0x3a:'、'}

def decode(t, maxlen=2500):
    i=t; out=[]; nh=0
    while i<n and i-t<maxlen:
        b=orig[i]
        if b==0xFF: return ''.join(out), nh
        if b in LEADS:
            c=hz(b,orig[i+1]); out.append(c if c else '·');
            if c and '一'<=c<='鿿': nh+=1
            i+=2; continue
        if b==0xFD: out.append('[BUF]'); i+=2; continue
        if b==0xFC: out.append('[FC]'); i+=2; continue
        if b in (0xF8,0xF9): i+=2; continue
        if b in (0xFE,0xFB,0xFA,0xF7): out.append(' '); i+=1; continue
        out.append(std.get(b, SGL.get(b,''))); i+=1
    return ''.join(out), nh

# all loadpointer targets
lp = collections.OrderedDict()
i=0
while True:
    i=orig.find(b'\x0f\x00', i)
    if i==-1: break
    v=struct.unpack_from('<I',orig,i+2)[0]
    if 0x08000000<=v<0x0A000000:
        t=v-0x08000000
        if 0<t<n: lp.setdefault(t, []).append(i+2)
    i+=1
print("distinct loadpointer targets:", len(lp))

# decode each; classify chinese
chinese = {}
for t in lp:
    txt, nh = decode(t)
    if nh >= 1:  # has at least 1 hanzi = untranslated-or-mixed dialogue
        chinese[t] = txt
print("loadpointer targets containing Chinese:", len(chinese))
tot_hz = sum(sum(1 for c in txt if '一'<=c<='鿿') for txt in chinese.values())
print("total Chinese chars in loadpointer dialogue:", tot_hz)

# how many do we ALREADY translate? our current addr_en via worklist
wl={}
for f in (r"\worklist2.json", r"\worklist3f.json"):
    d=json.load(open(sp+f,encoding='utf-8'))
    for tt,a in d.items(): wl.setdefault(tt,set()).update(a)
trans={}
for f in sorted(glob.glob(sp+r"\translations\trans_*.json")): trans.update(json.load(open(f,encoding='utf-8')))
def safe(en):
    return en and en!='@@SKIP@@' and not en.endswith(('\\p','\\n','\\l')) and en.count('[')==en.count(']')
addr_en=set()
for zh,a in wl.items():
    if safe(trans.get(zh,'').strip()):
        addr_en |= a

covered = sum(1 for t in chinese if t in addr_en)
missing = [t for t in chinese if t not in addr_en]
print(f"\nof {len(chinese)} Chinese loadpointer strings:")
print(f"  already translated (addr in our set): {covered}")
print(f"  MISSING (never translated): {len(missing)}")
missing_hz = sum(sum(1 for c in chinese[t] if '一'<=c<='鿿') for t in missing)
print(f"  missing Chinese chars: {missing_hz}")

# save the missing set for translation
out = {hex(t): chinese[t] for t in missing}
json.dump(out, open(sp + r"\lp_missing.json", 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
# sample
print("\nsample missing dialogue:")
for t in missing[:12]:
    print(f"  {t:#x}: {chinese[t][:60]}")
