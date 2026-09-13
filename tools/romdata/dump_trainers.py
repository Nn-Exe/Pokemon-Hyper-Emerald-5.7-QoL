import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import *
T=0x10019F8
def name_ok(nm):
    return is_clean(nm) or nm=='' or (nm.count('{CN')>0 and all(ch.isalnum() or ch in " .'&-!?" for ch in __import__('re').sub(r'\{CN[0-9A-F]{4}\}','',nm)))
def entry_valid(i):
    e=T+40*i
    nm=decode(e+4,12)[0]; p=u32(e+36); ps=rom[e+32]; fl=rom[e]
    if not name_ok(nm): return False
    if ps>6 or fl>3: return False
    if ps==0: return p==0 or valid_ptr(p)
    if not valid_ptr(p): return False
    pp=p-0x8000000; esz=16 if fl&1 else 8
    for k in range(ps):
        m=pp+esz*k
        if not (1<=u16(m+2)<=100 and 1<=u16(m+4)<=1199): return False
    return True
last=0; junk=[]
for i in range(0,4000):
    if entry_valid(i): last=i
    else:
        junk.append(i)
        if len(junk)>=80 and junk[-80]==i-79: break
NT=last+1
print('trainer table extent: last valid index', last, 'invalid slots before it', [j for j in junk if j<last])
species=load('species.json')
items=load('items.json')
moves=load('moves.json')
classes=load('trainer_classes.json')
def sp(i): return species.get(str(i), '?%d'%i)
def it(i): return '' if i==0 else items.get(str(i),{}).get('name','?item%d'%i)
def mv(i): return '' if i==0 else moves.get(str(i),'?move%d'%i)
out=[]
warn=[]
for i in range(NT):
    e=T+40*i
    if not entry_valid(i):
        out.append({'id':i,'invalid':True,'class_id':rom[e+1],'class':'','name':decode(e+4,12)[0],'party':[],'party_size':0,'double':0,'items':[]})
        continue
    flags=rom[e]; cls=rom[e+1]; music=rom[e+2]; pic=rom[e+3]
    name=decode(e+4,12)[0].strip()
    titems=[u16(e+16+2*k) for k in range(4)]
    dbl=rom[e+24]; ai=u32(e+28); psize=rom[e+32]; pp=ptr(e+36)
    party=[]
    if pp is not None:
        # vanilla layout: bit0 custom moves -> 16-byte entries, bit1 held item at +6
        esz = 16 if flags&1 else 8
        for k in range(psize):
            m=pp+esz*k
            itm = u16(m+6) if flags&2 else 0
            mvs = [u16(m+8+2*j) for j in range(4)] if flags&1 else []
            mon={'iv':u16(m),'level':u16(m+2),'species_id':u16(m+4),'species':sp(u16(m+4)),
                 'item_id':itm,'item':it(itm),'moves':[mv(x) for x in mvs],'move_ids':mvs}
            if not (1<=mon['level']<=100) or not (1<=mon['species_id']<=1199): warn.append((i,name,k,mon['level'],mon['species_id']))
            party.append(mon)
    out.append({'id':i,'class_id':cls,'class':classes.get(str(cls),'?'),'name':name,'party_flags':flags,'gender_music':music,'pic':pic,
                'items':[it(x) for x in titems if x],'double':dbl,'ai_flags':ai,'party_size':psize,'party_ptr':hex(0x8000000+pp) if pp is not None else None,'party':party,'dead_party':bool(pp is not None and psize>0 and rom[pp:pp+16*psize]==b'\0'*16*psize)})
save('trainers.json', out)
print('trainers', len(out), 'warnings', len(warn)); print(warn[:20])
print('dead parties (all-zero data):', sum(1 for t in out if t.get('dead_party')))
