"""audit_moves.py <patched.gba> <original.gba>: every applymovement in the original must keep its pointer and movement bytes"""
import sys, re, struct
rom=open(sys.argv[1],'rb').read(); orig=open(sys.argv[2],'rb').read(); N=len(rom)
def mv_len(d,t):
    for k in range(64):
        if d[t+k]==0xFE: return k+1
        if d[t+k]>=0xA0: return 0
    return 0
bad=0; n=0
for m in re.finditer(rb'[\x4f\x50][\x00-\xff][\x00-\xff][\x00-\xff]{3}[\x08\x09]', orig):
    po=m.start()+3; ov=struct.unpack_from('<I',orig,po)[0]; ot=ov-0x8000000
    if ot>=N: continue
    ml=mv_len(orig,ot)
    if not ml: continue
    n+=1
    if struct.unpack_from('<I',rom,po)[0]!=ov: bad+=1; print('pointer changed at %08x' % (0x8000000+po))
    if rom[ot:ot+ml]!=orig[ot:ot+ml]: bad+=1; print('movement bytes changed at %08x' % ov)
print('applymovement refs checked:', n, '| problems:', bad)
