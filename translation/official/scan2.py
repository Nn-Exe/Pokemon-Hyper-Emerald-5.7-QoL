"""Every Chinese string something in the ROM still points at.   python scan2.py <rom> <out.json>
A candidate is the target of a pointer (any alignment) that decodes, up to its 0xFF, as text of the hack's
encoding with at least one hanzi. Kept when the hanzi are mostly common ones (GB2312 level 1, as real text is; random
bytes are not) and the pointer looks structural: an aligned word, or a script argument (loadpointer / message /
trainerbattle ...), or the target follows a terminator. Output: address, pointers, decoded text, flags."""
import json, struct, sys
import numpy as np
import scan as S

LEVEL1 = 3755                                  # GB2312 level-1 hanzi come first in the table


def parse(rom, t, limit=900):
    """(end, hanzi, level1, other_chars) if rom[t:] is hack text up to 0xFF, else None"""
    i, hz, l1, oth = t, 0, 0, 0
    n = len(rom)
    while i < n and i - t < limit:
        c = rom[i]
        if c == 0xFF:
            return i, hz, l1, oth
        if c in (0xF7, 0xF8, 0xF9, 0xFD):
            i += 2
        elif c == 0xFC:
            if i + 1 >= n:
                return None
            k = {1: 1, 2: 1, 3: 1, 4: 3, 5: 1, 6: 1, 8: 1, 0x0B: 2, 0x0C: 1, 0x0D: 1, 0x0E: 1, 0x10: 2, 0x11: 1, 0x12: 1,
                 0x13: 1, 0x14: 1}.get(rom[i + 1], 0)
            i += 2 + k
        elif c in S.LEADS and i + 1 < n and rom[i + 1] <= 0xF6:
            o = S.adj(c) * 247 + rom[i + 1]
            if o >= len(S.GB) or S.GB[o] == "?":
                return None
            hz += 1
            l1 += o < LEVEL1
            i += 2
        elif (0xA1 <= c <= 0xEE) or c in (0x00, 0xFE, 0xFA, 0xFB, 0x1B, 0x06, 0x2D, 0x2E, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
                                          0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x51, 0x52, 0x5B, 0x5C, 0x5D, 0x79, 0x7A, 0x7B, 0x7C,
                                          0x85, 0x86, 0xF0, 0xEF):
            oth += 1
            i += 1
        else:
            return None
    return None


def main(rompath, outpath):
    rom = open(rompath, "rb").read()
    n = len(rom)
    a = np.frombuffer(rom, dtype=np.uint8)
    ptrs = {}
    for k in range(4):
        m = (n - k) // 4
        v = a[k:k + m * 4].view("<u4")
        idx = np.nonzero((v >= 0x08000000) & (v < 0x08000000 + n))[0]
        for j in idx:
            ptrs.setdefault(int(v[j]) - 0x08000000, []).append(int(j) * 4 + k)
    out = []
    for t, where in ptrs.items():
        if t < 0x100000 or t >= n - 2:
            continue
        r = parse(rom, t)
        if not r:
            continue
        end, hz, l1, oth = r
        if hz < 1:
            continue
        aligned = [w for w in where if w % 4 == 0]
        script = [w for w in where if (w >= 2 and rom[w - 2:w] == b"\x0f\x00") or (w >= 1 and rom[w - 1] in (0x67, 0x5C, 0x85))]
        after_term = rom[t - 1] in (0xFF, 0x00)
        text, _ = S.dec(rom[t:end])
        out.append({"a": "%08X" % (0x08000000 + t), "len": end - t + 1, "hz": hz, "l1": l1, "oth": oth,
                    "aligned": ["%08X" % (0x08000000 + w) for w in aligned][:12],
                    "other": ["%08X" % (0x08000000 + w) for w in where if w % 4][:12], "script": len(script),
                    "after_term": after_term, "zh": text})
    out.sort(key=lambda e: e["a"])
    json.dump(out, open(outpath, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(out), "candidates")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
