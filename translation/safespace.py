import struct, re
orig = open(r"c:\Users\nonth\Desktop\Works & Productivity\gba-trans\Hyper EMR LA v5.7 bugfix 2.gba", 'rb').read()
n = len(orig)
FONT_LO, FONT_HI = 0xE3CF64, 0xF18F64

# raw free runs (>=64 FF), excluding font
runs = []
for m in re.finditer(rb'\xff{64,}', orig):
    s, e = m.start(), m.end()
    if e <= FONT_LO or s >= FONT_HI:
        runs.append((s, e))
raw = sum(e-s for s,e in runs)
print(f"raw FF runs>=64 (non-font): {len(runs)} regions, {raw//1024}KB")

# all pointer targets anywhere in ROM
targets = set()
for off in range(0, n-3, 4):
    v = struct.unpack_from('<I', orig, off)[0]
    if 0x08000000 <= v < 0x0A000000:
        t = v - 0x08000000
        if 0 < t < n: targets.add(t)
tsorted = sorted(targets)
import bisect

# For each free run, subtract a forbidden window [T-4, T+MARGIN] for each pointer target T
# that lands in or near the run. MARGIN = generous max read length from a pointer.
MARGIN = 260
def safe_gaps(s, e):
    # collect targets in [s-4, e]
    lo = bisect.bisect_left(tsorted, s-4)
    hi = bisect.bisect_right(tsorted, e)
    forbid = []
    for i in range(lo, hi):
        T = tsorted[i]
        forbid.append((max(s, T-4), min(e, T+MARGIN)))
    # merge forbid, subtract from [s,e]
    forbid.sort()
    gaps = []
    cur = s
    for fs, fe in forbid:
        if fs > cur:
            gaps.append((cur, fs))
        cur = max(cur, fe)
    if cur < e:
        gaps.append((cur, e))
    return gaps

total_safe = 0
safe_regions = []
for s, e in runs:
    for gs, ge in safe_gaps(s, e):
        if ge - gs >= 16:   # usable chunk
            safe_regions.append((gs, ge))
            total_safe += ge - gs
print(f"SAFE allocatable (no pointer targets within {MARGIN}B): {total_safe//1024}KB in {len(safe_regions)} chunks")

# how much do we need?
import json, glob, collections, sys
sys.path.insert(0, r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad")
from inserter import encode_string
wl = {}
for f in (r"\worklist2.json", r"\worklist3f.json"):
    d = json.load(open(r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad"+f, encoding='utf-8'))
    for t, addrs in d.items(): wl.setdefault(t, set()).update(addrs)
trans = {}
for f in sorted(glob.glob(r"C:\Users\nonth\AppData\Local\Temp\claude\c--Users-nonth-Desktop-Works---Productivity-gba-trans\f184de21-699d-4c79-a35b-04f41a1fd6c9\scratchpad\translations\trans_*.json")):
    trans.update(json.load(open(f, encoding='utf-8')))
uniq = set()
for zh in wl:
    en = trans.get(zh,'').strip()
    if en and en != '@@SKIP@@':
        try: uniq.add(bytes(encode_string(en)+b'\xff'))
        except Exception: pass
need = sum(len(b) for b in uniq)
print(f"unique translated strings: {len(uniq)}, total bytes needed: {need//1024}KB")
print(f"\nverdict: safe space {'SUFFICIENT' if total_safe>=need else 'INSUFFICIENT'} ({total_safe//1024}KB vs {need//1024}KB needed)")
