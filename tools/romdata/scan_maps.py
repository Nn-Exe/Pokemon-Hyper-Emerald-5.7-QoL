# Structural scan for map headers -> map group arrays -> gMapGroups
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import *
N=len(rom)//4
W=struct.unpack('<%dI'%N, rom)
LO=0x08000000; HI=0x08000000+len(rom)
def vp(v): return LO<=v<HI
def layout_ok(o):
    if o+24>len(rom) or o%4: return False
    w=u32(o); h=u32(o+4)
    if not (1<=w<=400 and 1<=h<=400): return False
    return all(vp(u32(o+8+4*k)) for k in range(4))
def events_ok(o):
    if o+20>len(rom) or o%4: return False
    return all(vp(u32(o+4+4*k)) or u32(o+4+4*k)==0 for k in range(4))
headers=set()
for i in range(N-6):
    p0=W[i]
    if not vp(p0): continue
    p1=W[i+1]
    if not vp(p1): continue
    p2=W[i+2]; p3=W[i+3]
    if not (vp(p2) or p2==0) or not (vp(p3) or p3==0): continue
    if not layout_ok(p0-LO): continue
    if not events_ok(p1-LO): continue
    headers.add(i*4)
print('candidate headers', len(headers))
hset=set(LO+h for h in headers)
# words pointing to headers
refs=[i for i in range(N) if W[i] in hset]
print('refs to headers', len(refs))
# group into runs of consecutive words
runs=[]; cur=[refs[0]]
for r in refs[1:]:
    if r==cur[-1]+1: cur.append(r)
    else: runs.append(cur); cur=[r]
runs.append(cur)
runs=[r for r in runs if len(r)>=1]
print('runs', len(runs), 'sizes', sorted([len(r) for r in runs], reverse=True)[:40])
runstart=set(LO+r[0]*4 for r in runs)
# gMapGroups: array of pointers to run starts
grefs=[i for i in range(N) if W[i] in runstart]
gruns=[]; cur=[grefs[0]]
for r in grefs[1:]:
    if r==cur[-1]+1: cur.append(r)
    else: gruns.append(cur); cur=[r]
gruns.append(cur)
gruns.sort(key=len, reverse=True)
for g in gruns[:5]:
    print('gMapGroups candidate @', hex(g[0]*4), 'len', len(g))
best=gruns[0]
json.dump({'gMapGroups':best[0]*4,'ngroups':len(best),'group_ptrs':[W[i]-LO for i in best],
           'runs':{hex(LO+r[0]*4):len(r) for r in runs}}, open(os.path.join(OUT,'_mapscan.json'),'w'), indent=1)
