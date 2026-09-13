import os
import struct, os, sys, json
# ROM to analyse: pass it with HE_ROM=<path> (env) — the patched English build, 32 MB, code BPEE.
ROM_PATH = os.environ.get("HE_ROM") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "rom.gba")
# JSON/markdown outputs go here (default: tools/romdata/out); feed that folder to tools/build_site_data.py
OUT = os.environ.get("HE_ROMDATA_OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
rom = open(ROM_PATH, 'rb').read()

# Gen 3 charmap (international)
CH = {}
for i,c in enumerate("0123456789!?.-・…“”‘’♂♀¥,×/ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"):
    CH[0xA1+i] = c
CH[0x00]=' '; CH[0xFE]='\n'; CH[0xB0]='…'; CH[0xAD]='.'; CH[0xAE]='-'
CH[0xAB]='!'; CH[0xAC]='?'; CH[0xB8]=','; CH[0xBA]='/'; CH[0xB4]="'"; CH[0xB3]="'"; CH[0xB1]='"'; CH[0xB2]='"'
CH[0xB5]='♂'; CH[0xB6]='♀'; CH[0xB7]='¥'; CH[0xB9]='×'
CH[0x1B]='é'; CH[0x5B]='&'; CH[0x35]='='; CH[0x36]=';'; CH[0x2D]='&'; CH[0x2E]='+'; CH[0x34]='%'; CH[0x3B]='('; CH[0x3C]=')'; CH[0x53]='Pk'; CH[0x54]='Mn';
CH[0xF0]=':'; CH[0xF1]='Ä'; CH[0xF2]='Ö'; CH[0xF3]='Ü'; CH[0xF4]='ä'; CH[0xF5]='ö'; CH[0xF6]='ü'
CH[0xF8]='↑'; CH[0xF9]='↓'; CH[0xFA]='←'; CH[0xFB]='→'
CH[0x5A]='Í'; CH[0x5C]='+'; CH[0x85]='<'; CH[0x86]='>'; CH[0x7F]=' '; CH[0xB3]="'"

def decode(off, maxlen=None, stop_at_ff=True):
    """decode gen3 string at offset; returns (str, endoffset)"""
    s=[]; i=off; n=0
    while i < len(rom):
        b=rom[i]
        if maxlen is not None and n>=maxlen: break
        if b==0xFF: i+=1; break
        if b==0xFC:
            # control code: FC xx (some have extra args)
            code=rom[i+1] if i+1<len(rom) else 0
            extra={0x01:1,0x02:1,0x03:1,0x04:3,0x05:1,0x06:1,0x08:1,0x0C:1,0x0D:1,0x0E:1,0x10:2,0x11:1,0x12:1,0x13:1,0x14:1,0x15:0,0x16:0,0x17:0,0x18:0,0x09:0,0x0A:0,0x0B:0,0x0F:0,0x07:0}.get(code,0)
            s.append('{FC%02X}'%code); i+=2+extra; n+=2+extra; continue
        if b==0xFD:
            code=rom[i+1] if i+1<len(rom) else 0
            names={0x01:'PLAYER',0x02:'STR_VAR_1',0x03:'STR_VAR_2',0x04:'STR_VAR_3',0x06:'RIVAL',0x07:'VERSION',0x08:'AQUA',0x09:'MAGMA',0x0A:'ARCHIE',0x0B:'MAXIE',0x0C:'KYOGRE',0x0D:'GROUDON'}
            s.append('{%s}'%names.get(code,'FD%02X'%code)); i+=2; n+=2; continue
        if b in CH: s.append(CH[b])
        elif 0x01<=b<=0x1E:
            s.append('{CN%02X%02X}'%(b, rom[i+1] if i+1<len(rom) else 0)); i+=2; n+=2; continue
        else: s.append('{%02X}'%b)
        i+=1; n+=1
    return ''.join(s), i

def is_clean(s):
    return len(s)>0 and all(ord(c)<128 or c in 'é♂♀…“”‘’¥×' for c in s) and '{' not in s

def encode(text):
    inv={v:k for k,v in CH.items() if len(v)==1}
    return bytes(inv[c] for c in text)

def u8(o): return rom[o]
def u16(o): return struct.unpack_from('<H', rom, o)[0]
def u32(o): return struct.unpack_from('<I', rom, o)[0]
def ptr(o):
    v=u32(o)
    if 0x08000000 <= v < 0x08000000+len(rom): return v-0x08000000
    return None
def valid_ptr(v): return 0x08000000 <= v < 0x08000000+len(rom)

def find_all(pat, start=0):
    res=[]; i=rom.find(pat, start)
    while i!=-1:
        res.append(i); i=rom.find(pat, i+1)
    return res

def find_ptrs_to(off):
    """aligned 4-byte words equal to 0x08000000+off"""
    pat=struct.pack('<I', 0x08000000+off)
    return [i for i in find_all(pat) if i%4==0]

def save(name, obj):
    with open(os.path.join(OUT,name),'w',encoding='utf-8') as f:
        json.dump(obj,f,indent=1,ensure_ascii=False)
    print('wrote',name)

def load(name):
    with open(os.path.join(OUT,name),'r',encoding='utf-8') as f:
        return json.load(f)
