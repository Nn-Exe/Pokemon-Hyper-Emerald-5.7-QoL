import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import *
GMAPGROUPS=0xA54698; NGROUPS=38
secs=load('mapsections.json')
def header_ok(h):
    if h is None or h+0x1C>len(rom) or h%4: return False
    lay=ptr(h); ev=ptr(h+4)
    if lay is None or (ev is None and u32(h+4)!=0): return False
    w=u32(lay); hh=u32(lay+4)
    return 1<=w<=1000 and 1<=hh<=1000
gstarts=[ptr(GMAPGROUPS+4*g) for g in range(NGROUPS)]
maps=[]; groups_info=[]
for g in range(NGROUPS):
    gs=gstarts[g]
    nxt=min([x for x in gstarts if x>gs], default=None)
    n=0
    while True:
        o=gs+4*n
        if nxt is not None and o>=nxt: break
        h=ptr(o)
        if not header_ok(h): break
        lay=ptr(h); ev=ptr(h+4); scr=ptr(h+8); con=ptr(h+0xC)
        sec=rom[h+0x14]
        maps.append({'group':g,'num':n,'header':hex(0x8000000+h),'mapsec_id':sec,'mapsec':secs.get(str(sec),{}).get('name','?'),
                     'mapType':rom[h+0x17],'weather':rom[h+0x16],'music':u16(h+0x10),'layoutId':u16(h+0x12),'cave':rom[h+0x15],
                     'flags':rom[h+0x1A],'battleType':rom[h+0x1B],'width':u32(lay),'height':u32(lay+4),
                     'layout':hex(0x8000000+lay),'events':hex(0x8000000+ev) if ev is not None else None,'scripts':hex(0x8000000+scr) if scr else None})
        n+=1
    groups_info.append({'group':g,'array':hex(0x8000000+gs),'count':n})
print(json.dumps(groups_info))
print('total maps', len(maps))
save('maps.json', maps)
# sanity: map 13/20
m=[x for x in maps if x['group']==13 and x['num']==20][0]
print('13/20:', m)
ev=int(m['events'],16)-0x8000000
nobj=rom[ev]; objs=ptr(ev+4)
print('objs',nobj, 'obj4 script', hex(u32(objs+24*4+16)))
from collections import Counter
print(Counter(x['mapsec'] for x in maps).most_common(12))
