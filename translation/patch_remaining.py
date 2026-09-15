"""Remaining-text pass: relocate English translations for still-referenced Chinese strings into safe free space
and repoint the verified pointer occurrences. Apply on top of the feature build (after lrepel).
usage: python patch_remaining.py <in.gba> <out.gba>
Inputs (same folder): plan_remaining.json (from plan_remaining.py), translations/trans_27_remaining.json and
overrides_remaining.json (exact-zh keyed, take precedence over the plan's existing translation).
Safety rules (each one fixed a real bug in earlier passes):
 - only write into 0xFF runs >= 64 bytes with no aligned pointer target within MARGIN bytes, not the font,
   not the mega expansion region, not the feature-patch area, not runs with > MAXREFS inbound refs
 - never touch a byte below 0x1DC000; only rewrite pointer occurrences the plan verified (aligned table pointer,
   loadpointer arg, trainerbattle arg), and only if they still hold the old pointer
 - drop translations that end in a control code or have unbalanced brackets (can hang the text engine)
 - a string that does not fit its box (dex 4 lines, table n lines, name width) is left Chinese and reported"""
import sys, os, json, struct, re, bisect, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from inserter import encode_string
FONT_LO, FONT_HI = 0xE3CF64, 0xF18F64
MEGA = 0x1F82521
FEAT = (0xFD8000, 0xFE0000)
MARGIN, MAXREFS = 768, 6

def lz_blob_ranges(orig):
    """(start, end) of every LZ77 (type 0x10) blob the ROM references from an aligned pointer, sorted.
    Cached next to this file because the scan is slow; delete translation/lz_blobs.json to rebuild it."""
    cache = os.path.join(HERE, 'lz_blobs.json')
    if os.path.exists(cache):
        return [tuple(r) for r in json.load(open(cache))]
    n = len(orig)

    def clen(o):
        if orig[o] != 0x10: return None
        size = struct.unpack_from('<I', orig, o)[0] >> 8
        if not (32 <= size <= 0x20000): return None
        out = 0; i = o + 4
        try:
            while out < size:
                flags = orig[i]; i += 1
                for b in range(8):
                    if out >= size: break
                    if flags & (0x80 >> b):
                        v = (orig[i] << 8) | orig[i + 1]; i += 2
                        ln = (v >> 12) + 3; disp = (v & 0xFFF) + 1
                        if disp > out: return None
                        out += ln
                    else: i += 1; out += 1
        except IndexError: return None
        return i - o
    starts = set()
    for o in range(0, n - 3, 4):
        v = struct.unpack_from('<I', orig, o)[0]
        if 0x08000000 < v < 0x08000000 + n and orig[v - 0x08000000] == 0x10: starts.add(v - 0x08000000)
    ranges = []
    for t in sorted(starts):
        L = clen(t)
        if L: ranges.append((t, t + L))
    json.dump(ranges, open(cache, 'w'))
    return ranges


def load_json(p, default):
    p = os.path.join(HERE, p)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default

def wrap_fixed(en, width, maxlines, widen=0):
    """table/dex style: lines joined by \n only. Returns bytes (no FF) or None if it cannot fit."""
    for w in range(width, width + widen + 1, 2):
        b = encode_string(en, w).replace(b'\xfb', b'\xfe').replace(b'\xfa', b'\xfe')
        if b.count(b'\xfe') + 1 <= maxlines: return b
    return None

def safe_text(en):
    if en.endswith('\p') or en.endswith('\n') or en.endswith('\l'): return False
    return en.count('[') == en.count(']')

def build(inp, outp):
    orig = open(inp, 'rb').read(); n = len(orig); data = bytearray(orig)
    assert orig[0xAC:0xB0] == b'BPEE'
    plan = load_json('plan_remaining.json', None); assert plan, 'run plan_remaining.py first'
    extra = {}
    for f in ('translations/trans_27_remaining.json', 'translations/trans_28_remaining.json', 'overrides_remaining.json'):
        extra.update(load_json(f, {}))
    hz = lambda t: ''.join(c for c in t if '一' <= c <= '鿿')
    extra_hz = {hz(k): v for k, v in extra.items()}
    # ---- aligned pointer targets (free-space safety) ----
    targets = set()
    for off in range(0, n - 3, 4):
        v = struct.unpack_from('<I', orig, off)[0]
        if 0x08000000 <= v < 0x0A000000 and 0 < v - 0x08000000 < n: targets.add(v - 0x08000000)
    tl = sorted(targets)
    pool = []
    for m in re.finditer(rb'\xff{64,}', orig):
        s, e = m.start(), m.end()
        if not (e <= FONT_LO or s >= FONT_HI) or s >= MEGA or (e > FEAT[0] and s < FEAT[1]): continue
        lo = bisect.bisect_left(tl, s - MARGIN); hi = bisect.bisect_right(tl, e)
        if bisect.bisect_right(tl, e) - bisect.bisect_left(tl, s) > MAXREFS: continue
        forbid = sorted((max(s, tl[i] - 4), min(e, tl[i] + MARGIN)) for i in range(lo, hi))
        cur = s
        for fs, fe in forbid:
            if fs - cur >= 16: pool.append([cur, fs])
            cur = max(cur, fe)
        if e - cur >= 16: pool.append([cur, e])
    pool.sort()
    print("safe pool: %d KB in %d chunks" % (sum(e - s for s, e in pool) // 1024, len(pool)))
    # ---- encode ----
    jobs = []; report = collections.defaultdict(list); stats = collections.Counter()
    for s in plan:
        en = extra.get(s['zh']) or extra_hz.get(hz(s['zh'])) or s.get('en')
        if not en or en == '@@SKIP@@': stats['no translation' if not en else 'skip'] += 1; continue
        en = en.strip()
        if not safe_text(en): stats['unsafe text'] += 1; report['unsafe'].append(s['zh']); continue
        fmt = s['fmt']
        if fmt['kind'] == 'dialogue': enc = encode_string(en, fmt['width'])
        elif fmt['kind'] == 'dex': enc = wrap_fixed(en, 42, 4, widen=4)
        else: enc = wrap_fixed(en, fmt['width'], fmt['lines'], widen=0)
        if enc is None:
            stats['overflow'] += 1; report['overflow'].append({'addr': '%08x' % (0x08000000 + s['target']), 'fmt': fmt, 'zh': s['zh'], 'en': en}); continue
        jobs.append((s, enc + b'\xff'))
    # ---- place (deterministic, deduped) ----
    placed = {}
    def place(b):
        if b in placed: return placed[b]
        for reg in pool:
            if reg[1] - reg[0] >= len(b):
                off = reg[0]; reg[0] += len(b) + 1; placed[b] = off; return off
        return None
    unplaced = 0
    for b in sorted({b for _, b in jobs}, key=lambda x: (-len(x), x)):
        if place(b) is None: unplaced += 1
    for b, off in placed.items():
        assert set(data[off:off + len(b)]) == {0xFF}; data[off:off + len(b)] = b
    # ---- repoint ----
    DEX_LO, DEX_HI = 0x1250000, 0x1250000 + 960 * 32
    lz_ranges = lz_blob_ranges(orig)
    lz_starts = [a for a, _ in lz_ranges]

    def in_compressed(o):
        """inside an LZ77 blob? its byte stream is arbitrary, so it can hold a pointer's 4 bytes by chance;
        rewriting one corrupts every byte decoded after it (see patches/gfxfix)"""
        i = bisect.bisect_right(lz_starts, o) - 1
        return i >= 0 and lz_ranges[i][0] <= o < lz_ranges[i][1]

    def structural(o):
        """an aligned occurrence with no other ROM pointer within +-48 bytes is probably a coincidence in data,
        unless it sits in the Pokedex table or is a script argument"""
        if in_compressed(o): return False
        if DEX_LO <= o < DEX_HI or orig[o - 2:o] == bytes((0x0F, 0)) or (o >= 10 and orig[o - 10] == 0x5C) or (o >= 6 and orig[o - 6] == 0x5C): return True
        return any(0x08000000 <= struct.unpack_from('<I', orig, o + 4 * k)[0] < 0x0A000000 for k in range(-12, 13) if k)
    for s, b in jobs:
        if b not in placed: stats['unplaced'] += 1; continue
        newp = struct.pack('<I', 0x08000000 + placed[b]); oldp = struct.pack('<I', 0x08000000 + s['target'])
        for o in s['occ']:
            assert o >= 0x1DC000
            if orig[o:o + 4] != oldp: stats['occ changed'] += 1; continue
            if not structural(o): stats['occ skipped (lone pointer)'] += 1; continue
            data[o:o + 4] = newp; stats['pointers rewritten'] += 1
        stats['strings translated'] += 1
    # ---- verify ----
    assert data[:0x1DC000] == orig[:0x1DC000], 'low ROM changed'
    viol = sum(1 for b, off in placed.items() if bisect.bisect_right(tl, off + len(b)) > bisect.bisect_left(tl, off))
    assert viol == 0, 'placed string overlaps a pointer target'
    changed = sum(1 for i in range(n) if data[i] != orig[i])
    # every changed byte must lie inside a placed string or a rewritten pointer occurrence
    allowed = bytearray(n)
    for b, off in placed.items(): allowed[off:off + len(b)] = b'' * len(b)
    for s, b in jobs:
        for o in s['occ']:
            if structural(o): allowed[o:o + 4] = b''
    stray = [i for i in range(n) if data[i] != orig[i] and not allowed[i]]
    assert not stray, 'stray changes at %s' % ['%07x' % i for i in stray[:5]]
    print("stats:", dict(stats), "| unique strings placed:", len(placed), "unplaced:", unplaced, "| bytes changed:", changed)
    json.dump(report, open(os.path.join(HERE, 'remaining_report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    open(outp, 'wb').write(data)

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
