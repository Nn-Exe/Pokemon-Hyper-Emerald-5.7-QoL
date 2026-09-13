"""Audit: which Chinese-encoded strings are still REFERENCED in a build, grouped by how they are reached.
usage: python audit_chinese.py <rom.gba> [--dump out.txt]
Heuristic: a string = run of >=3 valid hanzi pairs (hack encoding), optional punctuation/control codes, ending in 0xFF;
counted only if some pointer (any alignment) targets its start or start-2/-1 (leading spaces)."""
import struct, sys, bisect, collections
sys.stdout.reconfigure(encoding='utf-8')
rom = open(sys.argv[1], 'rb').read()
dump = open(sys.argv[3], 'w', encoding='utf-8') if len(sys.argv) > 3 and sys.argv[2] == '--dump' else None

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
LEADS = set(l for l in range(1, 0x1F) if l not in (6, 0x1B))
PUNCT = {0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0xFE, 0xFA, 0xFB, 0x00, 0xB0, 0xF0, 0x2D, 0x2E, 0x34, 0x5B, 0x5C, 0x5D, 0x51, 0x52}
def dec(b):
    out = ''; i = 0
    while i < len(b):
        c = b[i]
        if c == 0xFF: break
        if c in LEADS and i + 1 < len(b) and b[i + 1] <= 0xF6:
            o = adj(c) * 247 + b[i + 1]; out += gb[o] if o < len(gb) else '?'; i += 2
        elif c in (0xFD, 0xFC): out += '{%02x%02x}' % (c, b[i + 1] if i + 1 < len(b) else 0); i += 2
        else: out += {0x37: '。', 0x3B: '，', 0x3C: '！', 0x3D: '？', 0x3E: '：', 0xFE: '\\n', 0xFA: '\\l', 0xFB: '\\p', 0x00: ' '}.get(c, '[%02x]' % c); i += 1
    return out

# 1. all pointer occurrences (byte-aligned) into ROM, with their context byte pair
ptrs = collections.defaultdict(list)
for o in range(0, len(rom) - 3):
    v = struct.unpack_from('<I', rom, o)[0]
    if 0x08000000 < v < 0x08000000 + len(rom): ptrs[v - 0x08000000].append(o)

# 2. candidate strings: scan for hanzi runs
n = len(rom); i = 0; found = []
while i < n - 6:
    c = rom[i]
    if c in LEADS and rom[i + 1] <= 0xF6 and rom[i + 2] in LEADS and rom[i + 3] <= 0xF6 and rom[i + 4] in LEADS and rom[i + 5] <= 0xF6:
        s = i
        # walk back over leading punctuation/spaces/buffer codes and earlier hanzi
        while s > 0 and (rom[s - 1] in PUNCT or (s >= 2 and rom[s - 2] in LEADS and rom[s - 1] <= 0xF6)): s -= 1
        e = s; hanzi = 0
        while e < n and rom[e] != 0xFF and e - s < 600:
            if rom[e] in LEADS and e + 1 < n and rom[e + 1] <= 0xF6: hanzi += 1; e += 2
            elif rom[e] in PUNCT: e += 1
            elif rom[e] in (0xFD, 0xFC): e += 2
            else: break
        if e < n and rom[e] == 0xFF and hanzi >= 3:
            refs = []
            for d in (0, -1, -2):
                for o in ptrs.get(s + d, []): refs.append((o, rom[o - 2:o]))
            if refs: found.append((s, e, hanzi, refs))
            i = e + 1; continue
    i += 1

cats = collections.Counter(); samples = collections.defaultdict(list)
for s, e, hanzi, refs in found:
    kinds = set()
    for o, ctx in refs:
        if ctx == b'\x0f\x00': kinds.add('dialogue (loadpointer)')
        elif len(ctx) == 2 and ctx[1] == 0x5c or (o >= 6 and rom[o - 6] == 0x5C) or (o >= 10 and rom[o - 10] == 0x5C): kinds.add('trainer battle text')
        elif (o % 4) == 0: kinds.add('table/code pointer (aligned)')
        else: kinds.add('other unaligned pointer')
    k = ' + '.join(sorted(kinds)); cats[k] += 1
    if len(samples[k]) < 6: samples[k].append((s, dec(rom[s:e])[:70]))
    if dump: dump.write('%08x %s | %s\n' % (0x08000000 + s, k, dec(rom[s:e])))
print("referenced Chinese strings (>=3 hanzi):", sum(cats.values()))
for k, c in cats.most_common():
    print("  %4d  %s" % (c, k))
    for s, t in samples[k]: print("          %08x  %s" % (0x08000000 + s, t))
