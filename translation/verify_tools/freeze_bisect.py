"""Freeze bisect on deterministic planning. First classifies content vs pointer, then bisects."""
import sys, json, glob, struct, re, collections, bisect as _bis, os, subprocess, time, hashlib
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
sp = r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"
sys.path.insert(0, sp)
from inserter import encode_string

ROM_IN = r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba"
FONT_LO, FONT_HI = 0xE3CF64, 0xF18F64
orig = open(ROM_IN, 'rb').read(); n = len(orig)

wl = {}
for f in (r"\worklist2.json", r"\worklist3f.json"):
    d = json.load(open(sp + f, encoding='utf-8'))
    for t, addrs in d.items(): wl.setdefault(t, set()).update(addrs)
trans = {}
for f in sorted(glob.glob(sp + r"\translations\trans_*.json")): trans.update(json.load(open(f, encoding='utf-8')))

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
    if not en or en=='@@SKIP@@' or not eligible(zh,addrs): continue
    good=[a for a in addrs if not is_shifted(a)]
    if good: kept[zh]=(sorted(good),en)
aligned_targets=set()
for off in range(0,n-3,4):
    v=struct.unpack_from('<I',orig,off)[0]
    if 0x08000000<=v<0x0A000000:
        t=v-0x08000000
        if 0<t<n: aligned_targets.add(t)
accepted=set()
for zh,(addrs,en) in kept.items(): accepted.update(addrs)
ext_cache={a:ext_end(a)-a+1 for a in accepted}
def has_internal(a):
    for x in range(a+1,a+ext_cache[a]):
        if x in aligned_targets or x in accepted: return True
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
inplace=[]; repoint=[]
for zh,(addrs,en) in kept.items():
    enc=encode_string(en)+b'\xff'
    for a in addrs:
        if len(enc)<=ext_cache[a] and not internal_cache[a]: inplace.append((a,enc))
        else: repoint.append((a,enc))
pool=[]
for m in re.finditer(rb'\xff{2048,}',orig):
    s,e=m.start()+8,m.end()-8
    if e<=FONT_LO or s>=FONT_HI:
        if e-s>=512: pool.append([s,min(e,0x1FFFF00)])
pool.sort()
placed={}
def place(b):
    if b in placed: return placed[b]
    for reg in pool:
        if reg[1]-reg[0]>=len(b):
            off=reg[0]; reg[0]=(reg[0]+len(b)+3)&~3; placed[b]=off; return off
    raise MemoryError
for b in sorted({bytes(enc) for _,enc in repoint},key=lambda x:(-len(x),x)): place(b)
rewrites=[]
for a,enc in sorted(repoint):
    newoff=placed[bytes(enc)]
    oldptr=struct.pack('<I',0x08000000+a); newptr=struct.pack('<I',0x08000000+newoff)
    i=orig.find(oldptr)
    while i!=-1:
        if occ_ok(i): rewrites.append((i,newptr))
        i=orig.find(oldptr,i+1)
print("rewrites:",len(rewrites),"inplace:",len(inplace),"placed:",len(placed))

def build(count, path, with_inplace=True):
    data=bytearray(orig)
    for b,off in placed.items(): data[off:off+len(b)]=b
    if with_inplace:
        for a,enc in inplace:
            data[a:a+len(enc)]=enc
            for k in range(a+len(enc),a+ext_cache[a]): data[k]=0xFF
    for occ,np_ in rewrites[:count]:
        data[occ:occ+4]=np_
    open(path,'wb').write(data)

MGBA=None
for c in glob.glob(os.environ['TEMP']+r"\mgba-dev\*\mGBA.exe"): MGBA=c
LUA=sp+r"\fz.lua"
_luabase = sp.replace('\\','/')
open(LUA,'w').write('''local base="__BASE__"
local frame=0
local hb=io.open(base.."/fz_hb.txt","w")
local dirs={6,7,5,4}
callbacks:add("frame",function()
 frame=frame+1
 emu:clearKeys(0x3FF)
 if frame<300 then
  if frame%30<6 then emu:addKey(3) end
  if frame%30>=15 and frame%30<21 then emu:addKey(0) end
 else
  local c=frame%90
  if c<10 then emu:addKey(0)
  elseif c<40 then emu:addKey(dirs[((frame//90)%4)+1])
  elseif c<50 then emu:addKey(0)
  elseif c<70 then emu:addKey(dirs[((frame//45)%4)+1])
  elseif c<76 then emu:addKey(6) end
 end
 if frame%60==0 then hb:write(frame.."\\n"); hb:flush() end
 if frame>=8800 and frame%40==0 and frame<=17000 then
  emu:screenshot(base.."/fz_shots/f"..string.format("%06d",frame)..".png")
 end
end)'''.replace('__BASE__', _luabase))

os.makedirs(sp+r"\fz_shots", exist_ok=True)
def run_and_check(path):
    for f in glob.glob(sp+r"\fz_shots\*.png"): os.remove(f)
    if os.path.exists(sp+r"\fz_hb.txt"): os.remove(sp+r"\fz_hb.txt")
    sav=path[:-4]+".sav"
    if os.path.exists(sav): os.remove(sav)
    ps=('$e=(Get-ChildItem "$env:TEMP\\mgba-dev" -Recurse -Filter mGBA.exe)[0].FullName;'
        '$p=Start-Process -FilePath $e -ArgumentList @("--script","%s","-l","0","-1","%s") -PassThru;'
        'Start-Sleep -Seconds 285; if(-not $p.HasExited){Stop-Process -Id $p.Id -Force}' % (LUA, path))
    subprocess.run(["powershell","-NoProfile","-Command",ps],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    time.sleep(1)
    hb=0
    try: hb=int(open(sp+r"\fz_hb.txt").read().split()[-1])
    except: pass
    import re as _re
    def fno(f): return int(_re.findall(r'f0*(\d+)', f.split('\\')[-1])[0])
    shots=sorted(glob.glob(sp+r"\fz_shots\*.png"))
    # analyze only post-cutscene frames (>=9600): frozen=1 distinct, clean=many (calibrated)
    post=[hashlib.md5(Image.open(f).convert('RGB').tobytes()).hexdigest() for f in shots if fno(f)>=9600]
    dpost=len(set(post))
    hard = hb < 9000                       # never reached cutscene -> hard freeze
    soft = (len(post)>=10 and dpost<=2)    # reached but perfectly static -> soft freeze
    clean = (dpost>=5)
    if hard or soft: frozen=True
    elif clean: frozen=False
    else: frozen=None                      # inconclusive
    return frozen, hb, len(shots), dpost

# Step 0: harness self-test — placed-only build MUST run clean (baseline == original behavior)
print("== self-test: placed-only (must NOT freeze; validates harness) ==")
build(0, sp+r"\fz_cur.gba", with_inplace=False)
fr0,hb0,ns0,u0=run_and_check(sp+r"\fz_cur.gba")
print(f"  self-test: frozen={fr0} hb={hb0} shots={ns0} distinctPost={u0}")
if hb0 < 5000 or ns0 == 0:
    print("HARNESS ERROR: emulator/lua not producing output on a known-good build. Aborting."); sys.exit(2)
if fr0 is not False:
    print(f"HARNESS ERROR: placed-only build not detected clean (frozen={fr0}). Detector needs tuning. Aborting."); sys.exit(2)
print("  self-test OK (harness produces output and baseline runs clean)")

# Step 1: classify — count=0 with in-place (content only)
print("\n== classify: strings+inplace, NO rewrites ==")
build(0, sp+r"\fz_cur.gba", with_inplace=True)
fr,hb,ns,uniq=run_and_check(sp+r"\fz_cur.gba")
print(f"  content-only: frozen={fr} hb={hb} shots={ns} uniqLate={uniq}")
if fr:
    # in-place is the cause; retest without inplace
    print("== content-only froze; test placed-only (no inplace, no rewrites) ==")
    build(0, sp+r"\fz_cur.gba", with_inplace=False)
    fr2,hb2,ns2,u2=run_and_check(sp+r"\fz_cur.gba")
    print(f"  placed-only(no inplace): frozen={fr2} hb={hb2} shots={ns2} uniqLate={u2}")
    print("CONCLUSION:", "IN-PLACE writes cause freeze" if not fr2 else "PLACED strings alone cause freeze (unexpected)")
    sys.exit(0)

# Step 2: bisect pointer rewrites
print("\n== count=0 clean; verifying full set freezes ==")
build(len(rewrites), sp+r"\fz_cur.gba")
frF,hbF,_,_=run_and_check(sp+r"\fz_cur.gba")
print(f"  full: frozen={frF} hb={hbF}")
if not frF:
    print("Full set did NOT freeze in this harness — autoplay path variance. Aborting bisect."); sys.exit(0)
def robust_test(count):
    build(count, sp+r"\fz_cur.gba")
    fr,hb,ns,uq=run_and_check(sp+r"\fz_cur.gba")
    if fr is None:  # inconclusive -> retry once
        build(count, sp+r"\fz_cur.gba")
        fr,hb,ns,uq=run_and_check(sp+r"\fz_cur.gba")
        if fr is None: fr=False  # give up -> treat as clean (conservative: keeps bisect moving)
    return fr,hb,ns,uq
lo,hi=0,len(rewrites)
while hi-lo>1:
    mid=(lo+hi)//2
    fr,hb,ns,uq=robust_test(mid)
    print(f"  test({mid}): frozen={fr} hb={hb} distinctPost={uq}")
    if fr: hi=mid
    else: lo=mid
occ,np_=rewrites[lo]
print("CULPRIT rewrite idx",lo,"at",hex(occ),"->",np_.hex())
json.dump({"idx":lo,"occ":occ}, open(sp+r"\freeze_culprit.json","w"))
