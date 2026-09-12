"""Regenerate corpus/decoded/worklist with fixed grammar (F8/F9 take 1 arg)."""
import sys, json, collections, re, struct
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
ROM = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba"
data = open(ROM, "rb").read()
n = len(data)

gb_hanzi = []
for hi in range(0xB0, 0xF8):
    for lo in range(0xA1, 0xFF):
        try: gb_hanzi.append(bytes([hi,lo]).decode('gb2312'))
        except UnicodeDecodeError: gb_hanzi.append('�')

def adj(lead):
    a = lead-1
    if lead>6: a-=1
    if lead>0x1B: a-=1
    return a

def hz(lead, second):
    if second > 0xF6: return None
    o = adj(lead)*247 + second
    return gb_hanzi[o] if o < len(gb_hanzi) else None

std = {0x00:' '}
for i in range(10): std[0xA1+i]=chr(48+i)
for i in range(26): std[0xBB+i]=chr(65+i)
for i in range(26): std[0xD5+i]=chr(97+i)
std.update({0xAB:'!',0xAC:'?',0xAD:'.',0xAE:'-',0xB8:',',0xB0:'…',0xB1:'“',0xB2:'”',0xB3:'‘',0xB4:"'",0xBA:'/',0xAF:'·',0xA0:'%',0xB7:'$',0xB9:'×',0xB5:'♂',0xB6:'♀'})
SGL = {0x37:'。',0x38:'—',0x39:'~',0x3a:'、',0x3b:',',0x3c:'!',0x3d:'?',0x3e:':',
       0x35:'=',0x36:';',0x2d:'&',0x2e:'+',0x34:'[Lv]',0x5c:'(',0x5d:')',0x51:'¿',0x52:'¡',
       0x06:'É',0x1b:'é',0x5b:'%'}
LEADS = set(range(0x01,0x1F)) - {0x06, 0x1B}
EXT_ARGS = {0x01:1,0x02:1,0x03:1,0x04:3,0x05:1,0x06:1,0x08:1,0x09:0,0x0A:0,0x0B:2,0x0C:1,0x0D:1,0x0E:1,0x0F:0,0x10:2,0x11:1,0x12:1,0x13:1,0x14:1,0x15:0,0x16:0,0x17:0}

def parse(t, maxlen=3000):
    i = t; out = []; nh = 0; ns = 0
    while i < n and i-t < maxlen:
        b = data[i]
        if b == 0xFF:
            return out, i-t, nh, ns
        if b in LEADS:
            if i+1 >= n: return None
            c = hz(b, data[i+1])
            out.append(c if c else f'[?{b:02x}{data[i+1]:02x}]')
            if c: nh += 1
            else: ns += 1
            i += 2; continue
        if b == 0xFD:
            out.append(f'[BUF{data[i+1]:02X}]'); i += 2; continue
        if b == 0xFC:
            sub = data[i+1]; na = EXT_ARGS.get(sub, 0)
            out.append(f'[FC{bytes(data[i+1:i+2+na]).hex().upper()}]'); i += 2+na; continue
        if b in (0xF8, 0xF9):
            out.append(f'[{b:02X}{data[i+1]:02X}]'); i += 2; continue
        if b == 0xFE: out.append('\\n'); i += 1; continue
        if b == 0xFB: out.append('\\p'); i += 1; continue
        if b == 0xFA: out.append('\\l'); i += 1; continue
        if b == 0xF7: out.append('[F7]'); i += 1; continue
        if b in std: out.append(std[b]); i += 1; continue
        if b in SGL: out.append(SGL[b]); i += 1; continue
        if 0x1F <= b <= 0x7F: out.append(f'[S{b:02x}]'); ns += 1; i += 1; continue
        return None
    return None

targets = set()
for off in range(0, n-3, 4):
    v = struct.unpack_from('<I', data, off)[0]
    if 0x08000000 <= v < 0x0A000000:
        t = v - 0x08000000
        if 0 < t < n: targets.add(t)

def lvl1_ratio(t):
    c1=tot=0
    for c in t:
        if '一' <= c <= '鿿':
            tot+=1
            try:
                b=c.encode('gb2312')
                if 0xB0 <= b[0] <= 0xD7: c1+=1
            except Exception: pass
    return (c1/tot if tot else 0), tot

GOOD_BANKS = set(list(range(0x1E,0x35)) + [0x67, 0x155, 0x160, 0x161] + list(range(0x180,0x18D)) + list(range(0x1D0,0x1D9)))

work = {}
all_decoded = {}
for t in sorted(targets):
    r = parse(t)
    if r is None: continue
    toks, length, nh, ns = r
    if nh < 1: continue
    txt = ''.join(toks)
    all_decoded[t] = txt
    ratio, tot = lvl1_ratio(txt)
    if tot < 1: continue
    has_struct = bool(re.search(r'[。,!?、~—:]|\\n|\\p', txt))
    has_unk = '[?' in txt or '[S' in txt
    bank = t >> 16
    score = ratio + (0.15 if has_struct else 0) - (0.25 if has_unk else 0)
    if bank in GOOD_BANKS:
        ok = score >= 0.75 or (tot >= 4 and ratio >= 0.8)
    else:
        ok = (score >= 0.95 and tot >= 4) or (has_struct and ratio >= 0.92 and tot >= 6 and not has_unk)
    if ok and ns <= max(2, nh//4):
        work[t] = txt

by_text = collections.defaultdict(list)
for a, t in work.items():
    by_text[t].append(a)
print("strings:", len(work), "unique:", len(by_text))
print("hanzi volume:", sum(sum(1 for c in t if '一'<=c<='鿿') for t in by_text))

json.dump({t: addrs for t, addrs in sorted(by_text.items(), key=lambda kv: min(kv[1]))},
          open(sp + r"\worklist2.json", "w", encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump({hex(a): t for a, t in all_decoded.items()},
          open(sp + r"\all_decoded2.json", "w", encoding='utf-8'), ensure_ascii=False, indent=0)
print("saved")
