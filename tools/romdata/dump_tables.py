# Dumps species.json, items.json, moves.json, mapsections.json, trainer_classes.json
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import *
SPECIES=0xF2B790; ITEMS=0xFC2C7C; MOVES=0x9D30258-0x8000000; MAPSEC=0x5A147C; CLASSES=0x30FCD4
species={}
for i in range(0,1200):
    s=decode(SPECIES+11*i,11)[0].strip()
    species[i]=s
save('species.json', species)
items={}
k=0; bad=0
while k<800:
    e=ITEMS+44*k
    s=decode(e,14)[0]
    d=u32(e+20)
    ok = (is_clean(s) or s=='' or '{3D}' in s or s.count('{CN')>0)
    if not ok:
        bad+=1
        if bad>=3:
            for kk in range(k-bad+1,k): items.pop(kk,None)
            break
    else: bad=0
    items[k]={'name':s.strip(),'id_field':u16(e+14),'price':u16(e+16),'pocket':rom[e+26]}
    k+=1
print('items', k)
save('items.json', items)
moves={i:decode(MOVES+13*i,13)[0].strip() for i in range(0,937)}
save('moves.json', moves)
secs={}
for i in range(213):
    e=MAPSEC+8*i
    secs[i]={'name':decode(ptr(e+4),40)[0],'x':rom[e],'y':rom[e+1],'w':rom[e+2],'h':rom[e+3]}
save('mapsections.json', secs)
classes={i:decode(CLASSES+13*i,13)[0].strip() for i in range(71)}
save('trainer_classes.json', classes)
