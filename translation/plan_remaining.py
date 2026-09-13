"""Filter corpus_remaining.json to real text, infer the display format of each string from its English
table neighbours, attach existing translations, and list what still needs translating.
usage: python plan_remaining.py <rom.gba>  -> plan_remaining.json, missing_corpus.json"""
import json, glob, sys, struct, collections, re
sys.stdout.reconfigure(encoding='utf-8')
rom = open(sys.argv[1], 'rb').read(); n = len(rom)
corp = json.load(open('corpus_remaining.json', encoding='utf-8'))
DEX_LO, DEX_HI = 0x1250000, 0x1250000 + 960 * 32
COMMON = set('的了是我你他她它们在有不就吗呢吧和与被给到要会能可这那什么没很才请谢对进出来去说想看知道让为着从但如果因所以还也都把等已经再最好多少大小新前后上下里外中东西南北左右门路山水火风日月年天时候些个只被用作全身体力量长得发生变成种类经常非常之而其于时使以及成为如果当由于像同一起都能够将它们的')
PUN = set('。,!?、:…')
def hz(t): return [c for c in t if '一' <= c <= '鿿']
def quality(t, verified=False):
    h = hz(t)
    if len(h) < 3: return False
    body = re.sub(r'\[[^\]]*\]|\[pnl]', '', t)
    other = sum(1 for c in body if c.isalnum() and not ('一' <= c <= '鿿'))
    if other > len(h) * 0.5: return False
    if re.search(r'  +', body.strip()) and len(re.findall(r'  +', body)) > 1: return False
    fr = collections.Counter(h)
    if len(h) > 8 and fr.most_common(1)[0][1] / len(h) > 0.3: return False
    com = sum(1 for c in h if c in COMMON)
    if not verified and com == 0 and '[BUF' not in t: return False
    if not verified and len(h) < 8 and '  ' in body.strip(): return False
    if len(h) >= 12 and com / len(h) < 0.08: return False
    return True
WHITELIST = {0x57f53c, 0x5b8cff, 0x5b8d0c, 0x5b8d19, 0x5b8d83, 0x610d50, 0x623b94, 0x623cbd, 0x9c10a0, 0x9c10c0, 0x16062a8}   # short names + dex #802 reviewed by hand
def structural_ok(s):
    t = s['target']
    if any(rom[t + k] == 0x0F and rom[t + k + 1] == 0 and rom[t + k + 5] in (8, 9) for k in range(0, 10)): return False   # msgbox/script header
    if rom[t:t + 3] == bytes(3): return False                                                                          # padding before real text
    if all(k == 'aligned' for k in s['kinds']):
        o = s['occ'][0]; dense = 0
        for k in range(-12, 13):
            if k == 0: continue
            v = struct.unpack_from('<I', rom, o + 4 * k)[0]
            if 0x08000000 <= v < 0x0A000000: dense += 1
        if dense == 0: return False                                                                                       # lone pointer in non-pointer data
    return True
good = [s for s in corp if s['target'] in WHITELIST or (quality(s['zh'], any(k != 'aligned' for k in s['kinds'])) and structural_ok(s))]
print("quality-pass:", len(good), "of", len(corp))

# ---- format inference from English neighbours in the same pointer table ----
cm = {0: ' ', 0xFE: '\n', 0xFA: '\n', 0xFB: '\n'}
for k in range(26): cm[0xBB + k] = chr(65 + k); cm[0xD5 + k] = chr(97 + k)
for k in range(10): cm[0xA1 + k] = chr(48 + k)
for k in (0xAD, 0xB8, 0xAB, 0xAC, 0xB4, 0xAE, 0xB0, 0xF0, 0x5C, 0x5D, 0xB5, 0xB6, 0x1B, 0x06, 0xBA, 0xB1, 0xB2, 0xB7, 0x2E): cm.setdefault(k, '.')
def en_stats(off):
    """if the string at off is English, return (maxwidth, nlines, uses_page) else None"""
    if not (0 < off < n): return None
    i = off; s = ''; letters = 0; pages = 0
    while i < n and rom[i] != 0xFF and i - off < 600:
        c = rom[i]
        if c == 0xFD: s += 'XXXXXXX'; i += 2; continue
        if c == 0xFC: i += 2; continue
        if c == 0xFB: pages += 1
        if c not in cm: return None
        if 0xBB <= c <= 0xEE: letters += 1
        s += cm[c]; i += 1
    if letters < 6: return None
    lines = s.split('\n')
    return (max(len(l) for l in lines), len(lines) if not pages else max(len(p.split('\n')) for p in s.split('\n')) , pages)
ptr = lambda o: struct.unpack_from('<I', rom, o)[0] - 0x08000000 if 0 <= o < n - 3 else -1
def infer(occ):
    """find the pointer table containing occ: try strides 4..64, walk contiguously while the slot holds a ROM
    pointer (to any text: English measured, Chinese counted), and take the max width/lines over ALL English entries."""
    best = None
    for stride in range(4, 68, 4):
        hits = []; cnt = 0
        for direction in (-1, 1):
            k = direction
            while abs(k) <= 1200:
                o = occ + k * stride
                if not (0 <= o < n - 3): break
                v = struct.unpack_from('<I', rom, o)[0]
                if not (0x08000000 <= v < 0x0A000000): break
                cnt += 1
                st = en_stats(v - 0x08000000)
                if st: hits.append(st)
                k += direction
        if best is None or len(hits) > len(best[1]) or (len(hits) == len(best[1]) and cnt > best[2]): best = (stride, hits, cnt)
    stride, hits, cnt = best
    if len(hits) < 3: return None
    return {'stride': stride, 'n': len(hits), 'width': max(h[0] for h in hits), 'lines': max(h[1] for h in hits), 'pages': any(h[2] for h in hits)}

tr = {}
for f in sorted(glob.glob('translations/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    if isinstance(d, dict): tr.update(d)
byhz = {}
for k, v in tr.items(): byhz.setdefault(''.join(hz(k)), v)
bufs = lambda t: sorted(re.findall(r'\[BUF[0-9A-F]{2}\]', t.upper()))
plan = []; miss = []; fmtc = collections.Counter()
for s in good:
    o = s['occ'][0]
    if DEX_LO <= o < DEX_HI and (o - DEX_LO) % 32 == 16: fmt = {'kind': 'dex', 'width': 42, 'lines': 4, 'pages': False}
    elif any(k.startswith('trainerbattle') or k == 'loadpointer' for k in s['kinds']): fmt = {'kind': 'dialogue', 'width': 34, 'lines': 0, 'pages': True}
    else:
        f = infer(o)
        if f is None: fmt = {'kind': 'dialogue', 'width': 34, 'lines': 0, 'pages': True}
        elif f['pages'] or f['lines'] == 0: fmt = {'kind': 'dialogue', 'width': max(34, min(f['width'], 40)), 'lines': 0, 'pages': True}
        else:
            src_lines = s['zh'].count(chr(10)) + 1
            if f['width'] < 24 and (src_lines >= 2 or len(hz(s['zh'])) > 12): fmt = {'kind': 'dialogue', 'width': 34, 'lines': 0, 'pages': True}
            else: fmt = {'kind': 'table', 'width': f['width'], 'lines': max(f['lines'], src_lines), 'pages': False, 'stride': f['stride'], 'n': f['n']}
    fmtc[(fmt['kind'], fmt['width'], fmt['lines'])] += 1
    en = byhz.get(''.join(hz(s['zh'])))
    if en is not None and en != '@@SKIP@@' and bufs(en) != bufs(s['zh']): en = None   # token mismatch -> retranslate
    s['fmt'] = fmt; s['en'] = en
    plan.append(s)
    if en is None: miss.append(s)
print("formats:", sorted(fmtc.items(), key=lambda x: -x[1])[:15])
print("with translation:", len(plan) - len(miss), "skip:", sum(1 for s in plan if s['en'] == '@@SKIP@@'), "missing:", len(miss), "missing hanzi:", sum(len(hz(s['zh'])) for s in miss))
print("missing by region:", collections.Counter("%08x" % (0x08000000 + (s['target'] >> 16 << 16)) for s in miss).most_common(15))
json.dump(plan, open('plan_remaining.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump([{'addr': '%08x' % (0x08000000 + s['target']), 'kinds': s['kinds'], 'fmt': s['fmt'], 'zh': s['zh']} for s in miss], open('missing_corpus.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
for s in miss: print(" %08x %-14s %-28s %s" % (0x08000000 + s['target'], '+'.join(s['kinds'])[:14], "%(kind)s w%(width)d l%(lines)d" % s['fmt'], s['zh'][:100].replace('\n', ' ')))
