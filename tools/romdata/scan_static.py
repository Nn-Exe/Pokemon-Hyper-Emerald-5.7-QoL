# Heuristic scan of map scripts for setwildbattle (0xB6) and trainerbattle (0x5C) commands
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import *
maps=load('maps.json'); species=load('species.json'); items=load('items.json'); trainers=load('trainers.json')
# script command argument sizes (vanilla Emerald), used to walk scripts linearly
# argument byte counts, vanilla Emerald script command table (0x00-0xC9); unknown/higher opcodes stop the walk
CMD={0x00:0,0x01:0,0x02:0,0x03:0,0x04:4,0x05:4,0x06:5,0x07:5,0x08:1,0x09:1,0x0A:2,0x0B:2,0x0C:0,0x0D:0,0x0E:1,0x0F:5,0x10:2,0x11:5,0x12:5,0x13:5,0x14:2,0x15:8,0x16:4,0x17:4,0x18:4,0x19:4,0x1A:4,0x1B:2,0x1C:2,0x1D:5,0x1E:5,0x1F:5,0x20:8,0x21:4,0x22:4,0x23:4,0x24:4,0x25:2,0x26:4,0x27:0,0x28:2,0x29:2,0x2A:2,0x2B:2,0x2C:4,0x2D:0,0x2E:0,0x2F:2,0x30:0,0x31:2,0x32:0,0x33:3,0x34:2,0x35:0,0x36:2,0x37:1,0x38:1,0x39:7,0x3A:7,0x3B:7,0x3C:2,0x3D:7,0x3E:7,0x3F:7,0x40:7,0x41:7,0x42:4,0x43:0,0x44:4,0x45:4,0x46:4,0x47:4,0x48:2,0x49:4,0x4A:4,0x4B:2,0x4C:2,0x4D:2,0x4E:2,0x4F:6,0x50:8,0x51:2,0x52:4,0x53:2,0x54:4,0x55:2,0x56:4,0x57:6,0x58:4,0x59:4,0x5A:0,0x5B:3,0x5C:0,0x5D:0,0x5E:0,0x5F:0,0x60:2,0x61:2,0x62:2,0x63:6,0x64:2,0x65:3,0x66:0,0x67:4,0x68:0,0x69:0,0x6A:0,0x6B:0,0x6C:0,0x6D:0,0x6E:2,0x6F:4,0x70:5,0x71:5,0x72:0,0x73:4,0x74:4,0x75:4,0x76:0,0x77:1,0x78:4,0x79:14,0x7A:4,0x7B:2,0x7C:3,0x7D:1,0x7E:3,0x7F:3,0x80:3,0x81:3,0x82:3,0x83:3,0x84:5,0x85:4,0x86:4,0x87:4,0x88:2,0x89:3,0x8A:0,0x8B:0,0x8C:0,0x8D:0,0x8E:2,0x8F:5,0x90:5,0x91:5,0x92:3,0x93:0,0x94:3,0x95:2,0x96:1,0x97:2,0x98:2,0x99:1,0x9A:4,0x9B:2,0x9C:3,0x9D:2,0x9E:2,0x9F:0,0xA0:4,0xA1:7,0xA2:0,0xA3:2,0xA4:0,0xA5:1,0xA6:2,0xA7:4,0xA8:3,0xA9:9,0xAA:2,0xAB:4,0xAC:4,0xAD:0,0xAE:4,0xAF:4,0xB0:5,0xB1:0,0xB2:2,0xB3:2,0xB4:2,0xB5:0,0xB6:5,0xB7:0,0xB8:4,0xB9:4,0xBA:4,0xBB:5,0xBC:5,0xBD:4,0xBE:5,0xBF:5,0xC0:3,0xC1:0,0xC2:3,0xC3:1,0xC4:7,0xC5:0,0xC6:3,0xC7:1,0xC8:4,0xC9:0}
def tb_len(kind):
    # trainerbattle: kind u8, trainer u16, local u16, then pointers depending on kind
    # opcode1 + kind1 + trainer2 + localid2 = 6, then pointers per kind
    return 6+4*{0:2,1:3,2:3,3:1,4:3,5:2,6:4,7:3,8:3,9:2}.get(kind,2)
END={0x02,0x03,0x05,0x08,0x0D,0x24,0xB8}  # end, return, goto, killscript
found=[]; tfound=[]
seen=set()
def walk(scr, mapinfo, depth=0):
    if scr is None or scr in seen or depth>200: return
    seen.add(scr)
    o=scr; n=0
    while n<600 and o<len(rom):
        c=rom[o]
        if c==0xB6:
            found.append({'map':mapinfo,'script':hex(0x8000000+scr),'at':hex(0x8000000+o),'species_id':u16(o+1),'species':species.get(str(u16(o+1)),'?'),'level':rom[o+3],'item_id':u16(o+4),'item':items.get(str(u16(o+4)),{}).get('name','')})
            o+=6
        elif c==0x5C:
            kind=rom[o+1]; tid=u16(o+2)
            t=trainers[tid] if tid<len(trainers) and not trainers[tid].get('invalid') else None
            tfound.append({'map':mapinfo,'script':hex(0x8000000+scr),'trainer_id':tid,'trainer':(t['class']+' '+t['name']) if t else '?','levels':[m['level'] for m in t['party']] if t else []})
            L=tb_len(kind)
            if kind in (1,2,4,6,7,8):
                walk(ptr(o+L-4), mapinfo, depth+1)
            o+=L
        elif c in (0x04,0x05,0x06,0x07):
            # call/goto/call_if/goto_if: follow
            pa=o+1 if c in (0x04,0x05) else o+2
            tgt=ptr(pa)
            if tgt is not None: walk(tgt, mapinfo, depth+1)
            if c in END: break
            o+=1+CMD[c]
        elif c in CMD:
            if c in END:
                break
            o+=1+CMD[c]
        else: break
        n+=1
for m in maps:
    mi='%d/%d %s'%(m['group'],m['num'],m['mapsec'])
    ev=m['events']
    if ev:
        e=int(ev,16)-0x8000000
        nobj=rom[e]; nwarp=rom[e+1]; ncoord=rom[e+2]; nbg=rom[e+3]
        objs=ptr(e+4); coords=ptr(e+12); bgs=ptr(e+16)
        if objs and nobj<100:
            for k in range(nobj): walk(ptr(objs+24*k+16), mi)
        if coords and ncoord<100:
            for k in range(ncoord): walk(ptr(coords+16*k+12), mi)
        if bgs and nbg<100:
            for k in range(nbg):
                b=bgs+12*k
                if rom[b+4]<5: walk(ptr(b+8), mi)
    if m['scripts']:
        s=int(m['scripts'],16)-0x8000000
        # map script table: {u8 type, ptr}; type 2/4 -> table of {u16 var,u16 val, ptr} ending with 0
        for k in range(20):
            t=rom[s+5*k]
            if t==0: break
            p=ptr(s+5*k+1)
            if p is None: break
            if t in (2,4):
                for j in range(50):
                    q=p+8*j
                    if u16(q)==0 and u16(q+2)==0 and u32(q+4)==0: break
                    walk(ptr(q+4), mi)
            else: walk(p, mi)
save('static_encounters.json', found)
save('trainer_battles_by_map.json', tfound)
print('setwildbattle hits', len(found), 'trainerbattle hits', len(tfound))
with open(os.path.join(OUT,'static_encounters.md'),'w',encoding='utf-8') as f:
    f.write('# Scripted (static) wild battles — setwildbattle scan\n\nHeuristic walk of every map\'s object/coord/bg event scripts and map scripts (call/goto followed). Duplicates collapsed per map.\n\n')
    f.write('| Map (group/num) | Map section | Species | Level | Held item | Script |\n|---|---|---|---|---|---|\n')
    seenrow=set()
    for r in sorted(found, key=lambda r:(r['map'],r['species'])):
        key=(r['map'],r['species_id'],r['level'])
        if not (1<=r['species_id']<=1199) or not (1<=r['level']<=100): continue
        if r['item_id']==0: r['item']=''
        if key in seenrow: continue
        seenrow.add(key)
        g,rest=r['map'].split(' ',1)
        f.write('| %s | %s | %s (#%d) | %d | %s | %s |\n'%(g,rest,r['species'],r['species_id'],r['level'],r['item'],r['script']))
    f.write('\n\n# Trainer battles found in map scripts (trainerbattle command)\n\n| Map | Section | Trainer | Levels |\n|---|---|---|---|\n')
    seenrow=set()
    for r in sorted(tfound, key=lambda r:(r['map'],r['trainer_id'])):
        key=(r['map'],r['trainer_id'])
        if not r['levels']: continue
        if key in seenrow: continue
        seenrow.add(key)
        g,rest=r['map'].split(' ',1)
        f.write('| %s | %s | %s (#%d) | %s |\n'%(g,rest,r['trainer'],r['trainer_id'],','.join(map(str,r['levels']))))
print('wrote static_encounters.md')
