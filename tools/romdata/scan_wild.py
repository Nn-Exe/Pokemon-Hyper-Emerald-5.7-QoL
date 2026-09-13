# Locate gWildMonHeaders structurally and dump wild.json / wild_by_species.json
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import *
maps=load('maps.json'); species=load('species.json')
mapidx={(m['group'],m['num']):m for m in maps}
def info_ok(o):
    if o is None or o+8>len(rom): return False
    if rom[o]>100 or rom[o+1:o+4]!=b'\0\0\0': return False
    return ptr(o+4) is not None
def entry_ok(o):
    if rom[o+2:o+4]!=b'\0\0': return False
    ps=[u32(o+4+4*k) for k in range(4)]
    if all(p==0 for p in ps): return False
    for p in ps:
        if p==0: continue
        if not valid_ptr(p) or not info_ok(p-0x8000000): return False
    return True
# Structural scan (first run of this script) found runs at 0x8E17E18/0x8E18458/0x8E1878C; the code references
# (0xB4D48,0xB5438,0xB54D8,0xB5560,0xB567C) point at 0x08E17D50 = the real table start.
base=0x8E17D50-0x8000000
print('code refs to base:', [hex(p) for p in find_ptrs_to(base)])
n=0; entries=[]; odd=[]
while True:
    o=base+20*n
    if rom[o]==0xFF and rom[o+1]==0xFF: break
    if not entry_ok(o): odd.append(hex(0x8000000+o))
    entries.append(o); n+=1
    if n>1000: break
print('gWildMonHeaders @', hex(0x8000000+base), 'entries', n, 'terminator @', hex(0x8000000+base+20*n), 'odd entries', odd)
LAND=[20,20,10,10,10,10,5,5,4,4,1,1]; WATER=[60,30,5,4,1]; ROCK=[60,30,5,4,1]; FISH=[70,30,60,20,20,40,40,15,4,1]
FISHROD=['Old']*2+['Good']*3+['Super']*5
def slots(info, rates, rods=None):
    if info is None: return None
    rate=rom[info]; arr=ptr(info+4)
    if arr is None: return {'encounterRate':rate,'slots':[],'error':'bad slot pointer'}
    out=[]
    for k,r in enumerate(rates):
        e=arr+4*k
        sid=u16(e+2)
        d={'species_id':sid,'species':species.get(str(sid),'?%d'%sid),'minLevel':rom[e],'maxLevel':rom[e+1],'slot%':r}
        if rods: d['rod']=rods[k]
        out.append(d)
    return {'encounterRate':rate,'slots':out}
wild=[]; bad=0
for o in entries:
    g,nm=rom[o],rom[o+1]
    m=mapidx.get((g,nm))
    rec={'group':g,'num':nm,'mapsec':m['mapsec'] if m else '?','mapsec_id':m['mapsec_id'] if m else None,'header':hex(0x8000000+o),
         'land':slots(ptr(o+4),LAND),'water':slots(ptr(o+8),WATER),'rock':slots(ptr(o+12),ROCK),'fishing':slots(ptr(o+16),FISH,FISHROD)}
    for k in ('land','water','rock','fishing'):
        if rec[k]:
            for s in rec[k]['slots']:
                if not (1<=s['minLevel']<=s['maxLevel']<=100) or not (1<=s['species_id']<=1199): bad+=1
    wild.append(rec)
print('slot sanity failures', bad)
save('wild.json', wild)
# extra 7-entry table referenced from 0xB5398/0xB5628 (city land encounters)
xb=0x553894; extra=[]
k=0
while not (rom[xb+20*k]==0xFF and rom[xb+20*k+1]==0xFF):
    o=xb+20*k; g,nm=rom[o],rom[o+1]; m=mapidx.get((g,nm))
    extra.append({'group':g,'num':nm,'mapsec':m['mapsec'] if m else '?','header':hex(0x8000000+o),'land':slots(ptr(o+4),LAND),'water':slots(ptr(o+8),WATER),'rock':slots(ptr(o+12),ROCK),'fishing':slots(ptr(o+16),FISH,FISHROD)})
    k+=1
save('wild_extra_0x08553894.json', extra)
bys={}
for rec in wild:
    loc='%s (%d/%d)'%(rec['mapsec'],rec['group'],rec['num'])
    for k in ('land','water','rock','fishing'):
        if not rec[k]: continue
        for s in rec[k]['slots']:
            bys.setdefault(s['species'],[]).append({'location':loc,'method':k+(' '+s['rod']+' Rod' if k=='fishing' else ''),'levels':'%d-%d'%(s['minLevel'],s['maxLevel']),'slot%':s['slot%']})
# merge duplicates per species/location/method
for sp_,lst in bys.items():
    merged={}
    for e in lst:
        key=(e['location'],e['method'])
        if key in merged:
            merged[key]['slot%']+=e['slot%']
            lo=min(int(merged[key]['levels'].split('-')[0]),int(e['levels'].split('-')[0])); hi=max(int(merged[key]['levels'].split('-')[1]),int(e['levels'].split('-')[1]))
            merged[key]['levels']='%d-%d'%(lo,hi)
        else: merged[key]=dict(e)
    bys[sp_]=list(merged.values())
save('wild_by_species.json', dict(sorted(bys.items())))
print('species with wild locations', len(bys))
