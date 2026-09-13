"""Build the corpus of still-referenced Chinese strings for the remaining-text pass.
usage: python build_corpus.py <rom.gba> <out_corpus.json> [original.gba]
The original (untranslated) ROM is used for the "pointer into the middle" test: earlier translation passes moved
loadpointer targets out of scripts, so only the original still shows that a candidate is really a script header.
Output: list of {"target": rom_offset, "occ": [pointer occurrence offsets], "kind": ..., "zh": text in spec token format}
Only pointer occurrences that pass the safety rules (>= 0x1DC000 and aligned / loadpointer / trainerbattle arg)
are kept; strings with no safe occurrence are dropped."""
import struct, sys, json, collections
sys.stdout.reconfigure(encoding='utf-8')
rom = open(sys.argv[1], 'rb').read(); n = len(rom)
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
PUNCT = {0x37: '。', 0x38: '—', 0x39: '~', 0x3A: '、', 0x3B: ',', 0x3C: '!', 0x3D: '?', 0x3E: ':', 0x35: '=', 0x36: ';',
         0x2D: '&', 0x2E: '+', 0x34: '[Lv]', 0x5B: '%', 0x5C: '(', 0x5D: ')', 0x51: '¿', 0x52: '¡', 0xF0: ':', 0x00: ' ',
         0xB0: '…', 0xAD: '.', 0xB8: ',', 0xAB: '!', 0xAC: '?', 0xAE: '-', 0xB4: "'", 0xBA: '/', 0xFE: '\n', 0xFA: '\l', 0xFB: '\p'}
for k in range(26): PUNCT[0xBB + k] = chr(65 + k); PUNCT[0xD5 + k] = chr(97 + k)
PUNCT.update({0xB1: '“', 0xB2: '”', 0xB3: '‘', 0xB5: '♂', 0xB6: '♀', 0xB7: '$', 0xB9: '×', 0xAF: '·'})
for k in range(10): PUNCT[0xA1 + k] = chr(48 + k)
def dec(o):
    out = ''; i = o; hanzi = 0
    while i < n and rom[i] != 0xFF and i - o < 800:
        c = rom[i]
        if c in LEADS and i + 1 < n and rom[i + 1] <= 0xF6:
            k = adj(c) * 247 + rom[i + 1]; out += gb[k] if k < len(gb) else '�'; i += 2; hanzi += 1
        elif c == 0xFD: out += '[BUF%02X]' % rom[i + 1]; i += 2
        elif c == 0xFC:
            ln = {0x01: 3, 0x02: 3, 0x03: 3, 0x04: 5, 0x05: 3, 0x06: 3, 0x07: 2, 0x08: 3, 0x09: 2, 0x0A: 2, 0x0B: 4, 0x0C: 3, 0x0D: 3, 0x0E: 3, 0x0F: 2, 0x10: 4, 0x11: 3, 0x12: 3, 0x13: 3, 0x14: 3, 0x15: 2, 0x16: 2, 0x17: 2, 0x18: 2}.get(rom[i + 1], 3)
            out += '[FC' + rom[i + 1:i + ln].hex().upper() + ']'; i += ln
        elif c == 0xF8: out += '[F8%02X]' % rom[i + 1]; i += 2
        elif c == 0xF9: out += '[F9%02X]' % rom[i + 1]; i += 2
        elif c == 0xF7: out += '[F7]'; i += 1
        elif c in PUNCT: out += PUNCT[c]; i += 1
        else: out += '[?%02X]' % c; i += 1
    return (out, hanzi, i)

# pointer occurrences (byte granular)
def scan(data):
    d = collections.defaultdict(list)
    for o in range(0, len(data) - 3):
        v = struct.unpack_from('<I', data, o)[0]
        if 0x08000000 < v < 0x08000000 + len(data): d[v - 0x08000000].append(o)
    return d
occs = scan(rom)
orig_rom = open(sys.argv[3], 'rb').read() if len(sys.argv) > 3 else rom
orig_occs = scan(orig_rom) if len(sys.argv) > 3 else occs
isptr = lambda o: 0 <= o < n - 3 and rom[o + 3] in (0x08, 0x09)
def meaningful(data, occ_list):
    """pointer occurrences that are structurally pointers (aligned word, loadpointer arg, trainerbattle arg);
    byte-granular hits inside other text are coincidences"""
    ip = lambda o: 0 <= o < len(data) - 3 and data[o + 3] in (0x08, 0x09)
    for o in occ_list:
        if o % 4 == 0: return True
        if o >= 2 and data[o - 2] == 0x0F and data[o - 1] == 0: return True
        if o >= 6 and data[o - 6] == 0x5C and data[o - 5] <= 9 and ip(o + 4): return True
        if o >= 10 and data[o - 10] == 0x5C and data[o - 9] <= 9 and ip(o - 4): return True
    return False

def occ_kind(o):
    if o < 0x1DC000: return None
    if rom[o - 2:o] == b'\x0f\x00': return 'loadpointer'
    if o >= 6 and rom[o - 6] == 0x5C and rom[o - 5] <= 9 and isptr(o + 4): return 'trainerbattle_intro'
    if o >= 10 and rom[o - 10] == 0x5C and rom[o - 9] <= 9 and isptr(o - 4): return 'trainerbattle_defeat'
    if o % 4 == 0: return 'aligned'
    return None

out = []
for t in sorted(occs):
    c = rom[t]
    # string must start with hanzi / space / punctuation / buffer, and contain >= 3 hanzi, end in FF, no undecodable bytes
    if not (c in LEADS or c in (0x00, 0xFD, 0xFC, 0x3B, 0x3C, 0x3D, 0x3E, 0x37, 0xB0, 0xB1) or 0xA1 <= c <= 0xAA): continue
    text, hanzi, end = dec(t)
    if hanzi < 3 or end >= n or rom[end] != 0xFF or '[?' in text or '�' in text: continue
    kinds = {}
    for o in occs[t]:
        k = occ_kind(o)
        if k: kinds[o] = k
    if not kinds: continue
    # a pointer into the middle of the extent means this is a script/struct, not a text string
    # strings referenced from the Pokedex entry table are text by construction; skip the inside-pointer test for them
    dex_ref = any(0x1250000 <= o < 0x1250000 + 960 * 32 and (o - 0x1250000) % 32 == 16 for o in occs[t])
    if not dex_ref and any((x in occs and meaningful(rom, occs[x])) or (x in orig_occs and meaningful(orig_rom, orig_occs[x])) for x in range(t + 1, end + 1)): continue
    out.append({'target': t, 'end': end, 'occ': sorted(kinds), 'kinds': sorted(set(kinds.values())), 'zh': text})
json.dump(out, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print("corpus strings:", len(out), collections.Counter('+'.join(s['kinds']) for s in out))
