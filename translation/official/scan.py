"""Which official Emerald texts are Chinese in the hack, and still referenced?  python scan.py <rom> <out.json>
For every labelled Emerald text: the hack's bytes at the same address are compared with the official bytes.
  same        - still the official English (nothing to do)
  zh          - the hack wrote Chinese there; `ref` = some pointer in the ROM still targets it;
                `tail_ok` = after the Chinese string's terminator the official text's own bytes are still there
                (so the whole official extent is this string's and can be written over)
  other       - changed to something that is not Chinese text (hack English, or data)"""
import json, struct, sys
import numpy as np
import vanilla as V

GB = []
for hi in range(0xB0, 0xF8):
    for lo in range(0xA1, 0xFF):
        try:
            GB.append(bytes([hi, lo]).decode("gb2312"))
        except Exception:
            GB.append("?")
LEADS = set(l for l in range(1, 0x1F) if l not in (6, 0x1B))


def adj(l):
    a = l - 1
    if l > 6:
        a -= 1
    if l > 0x1B:
        a -= 1
    return a


PUN = {0x37: "。", 0x38: "—", 0x39: "~", 0x3A: "、", 0x3B: "，", 0x3C: "！", 0x3D: "？", 0x3E: "：", 0xFE: "\\n", 0xFA: "\\l",
       0xFB: "\\p", 0x00: " ", 0xB0: "…", 0xAB: "!", 0xAC: "?", 0xAD: ".", 0xB8: ",", 0xAE: "-", 0xB4: "'", 0xF0: ":",
       0x5C: "(", 0x5D: ")", 0x5B: "%", 0x2E: "+", 0x2D: "&", 0x34: "Lv", 0xB1: "“", 0xB2: "”", 0xB3: "‘", 0xBA: "/",
       0x85: "<", 0x86: ">", 0x35: "=", 0x36: ";"}


def dec(b):
    """hack text bytes (no terminator) -> readable, and the number of hanzi"""
    out, i, hz = "", 0, 0
    while i < len(b):
        c = b[i]
        if c in (0xF7, 0xF8, 0xF9) and i + 1 < len(b):     # dynamic placeholder / button glyph / extra symbol: 2 bytes
            out += "{%02X%02X}" % (c, b[i + 1])
            i += 2
        elif c in LEADS and i + 1 < len(b) and b[i + 1] <= 0xF6:
            o = adj(c) * 247 + b[i + 1]
            out += GB[o] if o < len(GB) else "?"
            hz += 1
            i += 2
        elif c == 0xFD and i + 1 < len(b):
            out += "{FD%02X}" % b[i + 1]
            i += 2
        elif c == 0xFC and i + 1 < len(b):
            n = {1: 1, 2: 1, 3: 1, 4: 3, 5: 1, 6: 1, 8: 1, 0x0B: 2, 0x0C: 1, 0x0D: 1, 0x0E: 1, 0x10: 2, 0x11: 1, 0x12: 1,
                 0x13: 1, 0x14: 1}.get(b[i + 1], 0)
            out += "{FC" + b[i + 1:i + 2 + n].hex().upper() + "}"
            i += 2 + n
        elif 0xBB <= c <= 0xD4:
            out += chr(65 + c - 0xBB); i += 1
        elif 0xD5 <= c <= 0xEE:
            out += chr(97 + c - 0xD5); i += 1
        elif 0xA1 <= c <= 0xAA:
            out += chr(48 + c - 0xA1); i += 1
        elif c == 0x1B:
            out += "é"; i += 1
        else:
            out += PUN.get(c, "[%02X]" % c); i += 1
    return out, hz


def pointer_targets(rom):
    """sorted unique values of every 4-byte window (any alignment) that looks like a ROM pointer"""
    a = np.frombuffer(rom, dtype=np.uint8)
    vals = []
    for k in range(4):
        n = (len(a) - k) // 4
        v = a[k:k + n * 4].view("<u4")
        vals.append(v[(v >= 0x08000000) & (v < 0x0A000000)])
    return np.unique(np.concatenate(vals))


def main(rompath, outpath):
    rom = open(rompath, "rb").read()
    targets = pointer_targets(rom)
    entries, _ = V.load()
    seen, res, stats = set(), [], {"same": 0, "zh": 0, "zh_ref": 0, "other": 0}
    for e in entries:
        a, raw = e["addr"], e["raw"]
        if (a, e["name"]) in seen:
            continue
        seen.add((a, e["name"]))
        o = a - 0x08000000
        cur = rom[o:o + len(raw)]
        if cur == raw:
            stats["same"] += 1
            continue
        end = cur.find(b"\xff")
        body = cur if end < 0 else cur[:end]
        text, hz = dec(body)
        ref = bool(np.isin(np.uint32(a), targets))
        if hz >= 1 and end >= 0:
            tail_ok = cur[end + 1:] == raw[end + 1:]
            stats["zh"] += 1
            stats["zh_ref"] += ref
            res.append({"addr": "%08X" % a, "name": e["name"], "src": e["src"], "zh": text, "en": e["text"], "len": len(raw),
                        "zhlen": end + 1, "ref": ref, "tail_ok": tail_ok, "kind": "zh"})
        else:
            stats["other"] += 1
            res.append({"addr": "%08X" % a, "name": e["name"], "src": e["src"], "zh": text[:80], "en": e["text"], "len": len(raw),
                        "ref": ref, "kind": "other", "hz": hz, "terminated": end >= 0})
    json.dump(res, open(outpath, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(stats)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
