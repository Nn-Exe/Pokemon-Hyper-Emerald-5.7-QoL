"""Re-decode the 240 real missing loadpointer strings with FULL tokens (for re-insertion)."""
import json, struct, sys
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
            sub=orig[i+1]; na=EXT_ARGS.get(sub,0)
            out.append(f'[FC{bytes(orig[i+1:i+2+na]).hex().upper()}]'); i+=2+na; continue
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

real = json.load(open(sp + r"\lp_real_missing.json", encoding='utf-8'))
# re-decode each address with full tokens
proper = {}
for a_hex in real:
    a = int(a_hex, 16)
    proper[a_hex] = decode(a)
json.dump(proper, open(sp + r"\missing_proper.json", 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print("re-decoded:", len(proper))
# show the Galar one
for a,t in proper.items():
    if '影分身' in t or '勒尔' in t:
        print(f"\n{a}: {t}")
