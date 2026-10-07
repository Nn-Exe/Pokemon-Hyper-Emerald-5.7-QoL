"""What Chinese is left that the game can still reach?   python remain.py <rom> [out.txt]
1. official Emerald texts still Chinese at their own address (scan.py's test), referenced or not
2. strings a pointer reaches (any alignment) that read as real Chinese: mostly common hanzi (hanzi_freq.json, counted
   over the hack's genuine texts), reached by an aligned word or a script argument, starting after a terminator
3. the battle engine's offset-addressed block 0x09D74000..0x09D77000, scanned string by string"""
import json, struct, sys
import scan as S
import scan2 as S2
import vanilla as V
import gen_hack as G

import os
Z = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "patches", "zhtext")
GENUINE = set()                                        # hanzi seen in texts known to be real
for f in ("official.json", "hack.json"):
    for e in json.load(open(os.path.join(Z, f), encoding="utf-8")):
        z = bytes.fromhex(e["zh"])
        GENUINE |= {c for c in S.dec(z[:-1])[0] if "\u4e00" <= c <= "\u9fff"}
NOISE = set()                                          # hanzi whose two bytes are what small data values look like
for lead in S.LEADS:
    for second in range(0xF7):
        o = S.adj(lead) * 247 + second
        if o < len(S.GB) and S.GB[o] != "?" and (second < 0x30 or second in S.LEADS or lead < 3):
            NOISE.add(S.GB[o])


def hanzi(text):
    return [c for c in text if "\u4e00" <= c <= "\u9fff"]


def real(text, hz):
    h = hanzi(text)
    if not h or "[" in text:                           # no hanzi, or undecodable bytes: data
        return False
    if any(c not in GENUINE for c in h):
        return False
    clean = [c for c in h if c not in NOISE]
    return len(clean) >= max(1, len(h) // 2) and len(h) * 3 >= len(text.replace("\n", "").replace(" ", "")) 


def kind(rom, w):
    b = rom[max(0, w - 3):w]
    if b[-2:] == b"\x0f\x00":
        return "loadword"
    if b[-1:] == b"\x67":
        return "message"
    if b[-2:-1] == b"\x85" and b[-1] < 4:
        return "bufferstring"
    if G.trainer_arg(rom, w):
        return "trainerbattle"
    if w % 4 == 0:
        return "aligned"
    return "?"


def main(rompath, outpath=None):
    rom = open(rompath, "rb").read()
    lines = []
    # 1
    off = 0
    for e in V.load()[0]:
        o = e["addr"] - 0x08000000
        cur = rom[o:o + len(e["raw"])]
        if cur == e["raw"]:
            continue
        end = cur.find(b"\xff")
        if end < 0:
            continue
        text, hz = S.dec(cur[:end])
        if hz and real(text, hz):
            off += 1
            lines.append("official %08X %-50s %s" % (e["addr"], e["name"], text[:70]))
    # 2
    import numpy as np
    a = np.frombuffer(rom, dtype=np.uint8)
    n = len(rom)
    ptrs = {}
    for k in range(4):
        m = (n - k) // 4
        v = a[k:k + m * 4].view("<u4")
        idx = np.nonzero((v >= 0x08100000) & (v < 0x08000000 + n))[0]
        for j in idx:
            ptrs.setdefault(int(v[j]) - 0x08000000, []).append(int(j) * 4 + k)
    ref = 0
    for t in sorted(ptrs):
        r = S2.parse(rom, t)
        if not r or r[1] < 1:
            continue
        if rom[t - 1] not in (0xFF, 0x00):
            continue
        text, hz = S.dec(rom[t:r[0]])
        ks = [(w, kind(rom, w)) for w in ptrs[t]]
        ks.sort(key=lambda x: x[1] in ("?", "aligned"))
        strong = ks[0][1] not in ("?", "aligned")
        if not (real(text, hz) or (strong and "[" not in text)):
            continue
        ref += 1
        ctx = "" if strong else "   [" + rom[ks[0][0] - 8:ks[0][0] + 6].hex(" ") + "]"
        lines.append("pointer  %08X n=%d %-28s %s%s" % (0x08000000 + t, r[0] - t + 1, ",".join("%s@%08X" % (k, 0x08000000 + w) for w, k in ks[:3]), text, ctx))
    # 3
    eng = 0
    lo, hi = 0x01D74000, 0x01D77000
    i = lo
    while i < hi:
        j = rom.find(b"\xff", i)
        if j < 0 or j >= hi:
            break
        if j > i:
            r = S2.parse(rom, i)
            if r and r[0] == j and r[1] >= 1:
                text, hz = S.dec(rom[i:j])
                if real(text, hz):
                    eng += 1
                    lines.append("engine   %08X %s" % (0x08000000 + i, text[:80]))
        i = j + 1
    print("official still Chinese: %d; pointer-reached: %d; engine block: %d" % (off, ref, eng))
    if outpath:
        open(outpath, "w", encoding="utf-8").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
