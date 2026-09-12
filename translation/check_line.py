"""Verify that a Chinese line (as seen on screen) is translated in the English builds.
usage: python check_line.py "在时空歪曲危机中"   (punctuation optional; use a distinctive run of hanzi)
Finds the line in the original ROM, walks back to the message start, finds every loadpointer to it
(pointers target the first non-space byte), and reports where each build's pointer goes."""
import struct, sys, os
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
orig = open(os.path.join(ROOT, "Hyper EMR LA v5.7 bugfix 2.gba"), 'rb').read()
BUILDS = ["Hyper Emerald v5.7 - Full English.gba",
          "Hyper Emerald v5.7 - Story English (experimental).gba",
          "Hyper Emerald v5.7 - Story + Sinnoh Warp.gba",
          "Hyper Emerald v5.7 - Full English + BagSort + MultiRegister + QuickBall + AutoRun.gba"]
builds = {b: open(os.path.join(ROOT, b), 'rb').read() for b in BUILDS if os.path.exists(os.path.join(ROOT, b))}

gb = []
for hi in range(0xB0, 0xF8):
    for lo in range(0xA1, 0xFF):
        try: gb.append(bytes([hi, lo]).decode('gb2312'))
        except Exception: gb.append('�')
def adj(l):
    a = l - 1
    if l > 6: a -= 1
    if l > 0x1B: a -= 1
    return a
LEADS = [l for l in range(1, 0x1F) if l not in (6, 0x1B)]
rev = {}
for l in LEADS:
    for s in range(0xF7):
        o = adj(l) * 247 + s
        if o < len(gb): rev.setdefault(gb[o], bytes([l, s]))
PUNCT = {0x37: '。', 0x38: '—', 0x39: '~', 0x3A: '、', 0x3B: '，', 0x3C: '！', 0x3D: '？', 0x3E: '：', 0xFE: '\\n', 0xFA: '\\l', 0xFB: '\\p', 0x00: ' ', 0xB0: '…'}
def dec_cn(b):
    out = ''; i = 0
    while i < len(b):
        c = b[i]
        if c == 0xFF: break
        if c in LEADS and i + 1 < len(b) and b[i + 1] <= 0xF6:
            o = adj(c) * 247 + b[i + 1]; out += gb[o] if o < len(gb) else '?'; i += 2
        elif c in (0xFD, 0xFC): out += '{%02x%02x}' % (c, b[i + 1]); i += 2
        else: out += PUNCT.get(c, '[%02x]' % c); i += 1
    return out
cm = {0: ' ', 0xAD: '.', 0xAE: '-', 0xB8: ',', 0xB4: "'", 0xAB: '!', 0xAC: '?', 0xB3: '"', 0xB2: '"', 0xFE: '\\n', 0xFA: '\\l', 0xFB: '\\p', 0x1B: 'é', 0xB0: '…', 0xF0: ':'}
for k in range(26): cm[0xBB + k] = chr(65 + k); cm[0xD5 + k] = chr(97 + k)
for k in range(10): cm[0xA1 + k] = str(k)
def dec_en(b):
    out = ''
    for c in b:
        if c == 0xFF: break
        out += cm.get(c, '[%02x]' % c)
    return out

txt = ''.join(ch for ch in sys.argv[1] if ch in rev)
pat = b''.join(rev[ch] for ch in txt)
hits = []; i = orig.find(pat)
while i != -1: hits.append(i); i = orig.find(pat, i + 1)
if not hits:
    print("NOT FOUND in original ROM (try a shorter / different run of characters)"); sys.exit()
seen = set()
for h in hits:
    s = h
    while s > 0 and orig[s - 1] != 0xFF: s -= 1
    e = orig.find(b'\xff', h)
    print("\n=== message @%08x ===" % (0x08000000 + s))
    print("CN:", dec_cn(orig[s:e])[:300])
    sites = []
    for d in range(0, 8):
        p = struct.pack('<I', 0x08000000 + s + d); j = orig.find(p)
        while j != -1: sites.append((j, d)); j = orig.find(p, j + 1)
    if not sites: print("  no pointers found to this message (may be referenced by a table/command; check manually)")
    for j, d in sites:
        ov = struct.unpack_from('<I', orig, j)[0]
        print("  pointer @%08x (to start+%d, cmd bytes %s):" % (0x08000000 + j, d, orig[j - 2:j].hex()))
        for name, b in builds.items():
            nv = struct.unpack_from('<I', b, j)[0]
            if nv == ov: print("     [%s] UNCHANGED -> still Chinese" % name)
            else:
                t = nv - 0x08000000; print("     [%s] -> %08x  EN: %s" % (name, nv, dec_en(b[t:t + 200])))
