"""Extract code/table-loaded STORY dialogue (not loadpointer, not Pokedex): re-decode with
full tokens, dedupe shifted variants, keep only real-boundary starts. For the story ROM."""
import json, struct, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
orig = open(r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba", 'rb').read()
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
std={0x00:' '}
for i in range(10): std[0xA1+i]=chr(48+i)
for i in range(26): std[0xBB+i]=chr(65+i)
for i in range(26): std[0xD5+i]=chr(97+i)
std.update({0xAB:'!',0xAC:'?',0xAD:'.',0xAE:'-',0xB8:',',0xB0:'…',0xB1:'“',0xB2:'”',0xB3:'‘',0xB4:"'",0xBA:'/',0xAF:'·',0xA0:'%',0xB7:'$',0xB9:'×',0xB5:'♂',0xB6:'♀'})
SGL={0x37:'。',0x38:'—',0x39:'~',0x3a:'、',0x3b:',',0x3c:'!',0x3d:'?',0x3e:':',0x35:'=',0x36:';',0x2d:'&',0x2e:'+',0x34:'[Lv]',0x5c:'(',0x5d:')',0x51:'¿',0x52:'¡',0x06:'É',0x1b:'é',0x5b:'%'}
EXT_ARGS={0x01:1,0x02:1,0x03:1,0x04:3,0x05:1,0x06:1,0x08:1,0x09:0,0x0A:0,0x0B:2,0x0C:1,0x0D:1,0x0E:1,0x0F:0,0x10:2,0x11:1,0x12:1,0x13:1,0x14:1,0x15:0,0x16:0,0x17:0}
def decode(t, maxlen=2500):
    i=t; out=[]
    while i<n and i-t<maxlen:
        b=orig[i]
        if b==0xFF: return ''.join(out)
        if b in LEADS:
            c=hz(b,orig[i+1]); out.append(c if c else f'[?{b:02x}{orig[i+1]:02x}]'); i+=2; continue
        if b==0xFD: out.append(f'[BUF{orig[i+1]:02X}]'); i+=2; continue
        if b==0xFC:
            sub=orig[i+1]; na=EXT_ARGS.get(sub,0); out.append(f'[FC{bytes(orig[i+1:i+2+na]).hex().upper()}]'); i+=2+na; continue
        if b in (0xF8,0xF9): out.append(f'[{b:02X}{orig[i+1]:02X}]'); i+=2; continue
        if b==0xFE: out.append('\\n'); i+=1; continue
        if b==0xFB: out.append('\\p'); i+=1; continue
        if b==0xFA: out.append('\\l'); i+=1; continue
        if b==0xF7: out.append('[F7]'); i+=1; continue
        if b in std: out.append(std[b]); i+=1; continue
        if b in SGL: out.append(SGL[b]); i+=1; continue
        if 0x1F<=b<=0x7F: out.append(f'[S{b:02x}]'); i+=1; continue
        out.append(f'[?{b:02x}]'); i+=1
    return ''.join(out)
def extent(t):
    e=t
    while e<n and orig[e]!=0xFF: e+=1
    return e

conv = json.load(open(sp + r"\leftover_conv.json", encoding='utf-8'))  # {hex: hanzi-only text}
addrs = sorted(int(a,16) for a in conv)
# keep only real-boundary starts (preceded by 0xFF) -> distinct strings, drop shifted mid-string variants
boundary = [a for a in addrs if a>0 and orig[a-1]==0xFF]
# dedupe: drop any addr that lies inside an earlier kept string's extent
kept=[]
for a in boundary:
    if kept and a < extent(kept[-1]): continue
    kept.append(a)
print(f"leftover_conv: {len(conv)} | real-boundary: {len(boundary)} | distinct after dedupe: {len(kept)}")

proper = {hex(a): decode(a) for a in kept}
# drop ones that are still mostly junk tokens (very low real content)
def realish(t):
    hz=[c for c in t if '一'<=c<='鿿']
    if len(hz)<4: return False
    toks=t.count('[?')+t.count('[S')
    return toks < len(hz)   # more hanzi than junk tokens
proper = {a:t for a,t in proper.items() if realish(t)}
print("story strings to translate:", len(proper))
json.dump(proper, open(sp+r"\story_proper.json","w",encoding='utf-8'), ensure_ascii=False, indent=0)
import os
os.makedirs(sp+r"\storychunks", exist_ok=True)
items=list(proper.items()); CH=70; k=0
for i in range(0,len(items),CH):
    json.dump(dict(items[i:i+CH]), open(sp+rf"\storychunks\story_{k:02d}.json","w",encoding='utf-8'), ensure_ascii=False, indent=0)
    k+=1
print("chunks:", k)
for a,t in items[:8]: print(f"  {a}: {t[:55]}")
