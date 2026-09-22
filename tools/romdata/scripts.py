"""Walk every map's event scripts and index what they do with flags, vars, battles, items and text.

    set HE_ROM=<the patched build>
    python tools/romdata/scripts.py                  -> out/script_index.json (every entry point, summarised)
    python tools/romdata/scripts.py flag 0x867       -> where a flag is set, cleared and checked
    python tools/romdata/scripts.py var 0x4050       -> where a var is set and compared
    python tools/romdata/scripts.py map 11 3         -> every script on a map, with the text it shows
    python tools/romdata/scripts.py text Roxanne     -> scripts whose text mentions a word
    python tools/romdata/scripts.py at 0x0987CD9D    -> walk one script from any address

Command lengths are pret's pokeemerald (asm/macros/event.inc). This hack keeps the vanilla command table at
0x081DB67C, 227 commands plus the terminator, so nothing custom needs describing. The table below was checked
against pret by parsing its macros; the one hand error that check found (hidemoneybox takes two bytes) is fixed.

A walk follows goto / call / goto_if / call_if and a trainer battle's continue-script, and stops at end,
return, a standard-script goto or anything it does not recognise, which it reports. Standard scripts
(callstd) are not entered: they are the shared message and item boxes, not story.
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import rom, decode, load, save, OUT

OPLEN = {0x00:0,0x01:0,0x02:0,0x03:0,0x04:4,0x05:4,0x06:5,0x07:5,0x08:1,0x09:1,0x0A:2,0x0B:2,0x0C:0,0x0D:0,
 0x0E:1,0x0F:5,0x10:2,0x11:5,0x12:5,0x13:5,0x14:2,0x15:8,0x16:4,0x17:4,0x18:4,0x19:4,0x1A:4,0x1B:2,0x1C:2,
 0x1D:5,0x1E:5,0x1F:5,0x20:8,0x21:4,0x22:4,0x23:4,0x24:4,0x25:2,0x26:4,0x27:0,0x28:2,0x29:2,0x2A:2,0x2B:2,
 0x2C:4,0x2D:0,0x2E:0,0x2F:2,0x30:0,0x31:2,0x32:0,0x33:3,0x34:2,0x35:0,0x36:2,0x37:1,0x38:1,0x39:7,0x3A:7,
 0x3B:7,0x3C:2,0x3D:7,0x3E:7,0x3F:7,0x40:7,0x41:7,0x42:4,0x43:0,0x44:4,0x45:4,0x46:4,0x47:4,0x48:2,0x49:4,
 0x4A:4,0x4B:2,0x4C:2,0x4D:2,0x4E:2,0x4F:6,0x50:8,0x51:2,0x52:4,0x53:2,0x54:4,0x55:2,0x56:4,0x57:6,0x58:4,
 0x59:4,0x5A:0,0x5B:3,0x5D:0,0x5E:0,0x5F:0,0x60:2,0x61:2,0x62:2,0x63:6,0x64:2,0x65:3,0x66:0,0x67:4,0x68:0,
 0x69:0,0x6A:0,0x6B:0,0x6C:0,0x6D:0,0x6E:2,0x6F:4,0x70:5,0x71:5,0x72:0,0x73:4,0x74:4,0x75:4,0x76:0,0x77:1,
 0x78:4,0x79:14,0x7A:2,0x7B:4,0x7C:2,0x7D:3,0x7E:1,0x7F:3,0x80:3,0x81:3,0x82:3,0x83:3,0x84:3,0x85:5,0x86:4,
 0x87:4,0x88:4,0x89:2,0x8A:3,0x8B:0,0x8C:0,0x8D:0,0x8E:0,0x8F:2,0x90:5,0x91:5,0x92:5,0x93:3,0x94:2,0x95:3,
 0x96:2,0x97:1,0x98:2,0x99:2,0x9A:1,0x9B:4,0x9C:2,0x9D:3,0x9E:2,0x9F:2,0xA0:0,0xA1:4,0xA2:8,0xA3:0,0xA4:2,
 0xA5:0,0xA6:1,0xA7:2,0xA8:5,0xA9:4,0xAA:8,0xAB:2,0xAC:4,0xAD:4,0xAE:0,0xAF:4,0xB0:4,0xB1:7,0xB2:0,0xB3:2,
 0xB4:2,0xB5:2,0xB6:5,0xB7:0,0xB8:4,0xB9:4,0xBA:4,0xBB:5,0xBC:5,0xBD:4,0xBE:4,0xBF:5,0xC0:2,0xC1:2,0xC2:2,
 0xC3:1,0xC4:7,0xC5:0,0xC6:3,0xC7:1,0xC8:4,0xC9:0,0xCA:0,0xCB:0,0xCC:5,0xCD:2,0xCE:2,0xCF:0,0xD0:2,0xD1:7,
 0xD2:3,0xD3:2,0xD4:0,0xD5:2,0xD6:0,0xD7:7,0xD8:0,0xD9:0,0xDA:0,0xDB:4,0xDC:1,0xDD:3,0xDE:3,0xDF:4,0xE0:7,
 0xE1:3,0xE2:5}
# trainerbattle: type, trainer, local id, then this many pointers; the Nth (1-based) is an event script
TB_PTRS = {0: 2, 1: 3, 2: 3, 3: 1, 4: 3, 5: 2, 6: 4, 7: 3, 8: 4, 9: 2, 10: 2, 11: 2, 12: 2}
TB_SCRIPT = {1: 3, 2: 3, 6: 4, 8: 4}
WARPS = (0x39, 0x3A, 0x3B, 0x3D, 0xD1, 0xD7, 0xE0)
# a warp ends the script: the map changes under it, so whatever follows never runs (several of this hack's
# scripts end with a warp and no `end` at all)
STOP = (0x02, 0x03, 0x05, 0x08, 0x0C, 0x0D, 0x24, 0xB9) + WARPS
BASE = 0x08000000


def u8(o): return rom[o]
def u16(o): return struct.unpack_from("<H", rom, o)[0]
def u32(o): return struct.unpack_from("<I", rom, o)[0]
def inrom(p): return BASE <= p < BASE + len(rom)


def text_at(p, limit=240):
    if not inrom(p): return None
    try:
        s = decode(p - BASE, maxlen=600)[0]
    except Exception:
        return None
    if not s: return None
    s = s.replace("\n", " ")
    return s if len(s) <= limit else s[:limit] + "..."


def walk(entry, limit=4000):
    """Every reachable instruction from `entry`, as (addr, opcode, arg bytes), plus problems met."""
    seen, out, problems, todo = set(), [], [], [entry]
    while todo and len(out) < limit:
        pc = todo.pop()
        while True:
            if not inrom(pc) or pc in seen: break
            seen.add(pc)
            o = pc - BASE
            op = rom[o]
            if op == 0x5C:
                kind = rom[o + 1]
                if kind not in TB_PTRS:
                    problems.append("%08X: trainerbattle type %d unknown" % (pc, kind)); break
                n = 5 + 4 * TB_PTRS[kind]
                args = bytes(rom[o + 1:o + 1 + n])
                out.append((pc, op, args))
                if kind in TB_SCRIPT:
                    todo.append(struct.unpack_from("<I", args, 5 + 4 * (TB_SCRIPT[kind] - 1))[0])
                pc += 1 + n
                continue
            if op not in OPLEN:
                problems.append("%08X: unknown opcode %02X" % (pc, op)); break
            n = OPLEN[op]
            args = bytes(rom[o + 1:o + 1 + n])
            out.append((pc, op, args))
            if op in (0x04, 0x05):
                todo.append(struct.unpack_from("<I", args, 0)[0])
            elif op in (0x06, 0x07):
                todo.append(struct.unpack_from("<I", args, 1)[0])
            if op in STOP: break
            pc += 1 + n
    return out, problems


def summarise(entry):
    ins, problems = walk(entry)
    s = {"entry": "%08X" % entry, "set": [], "clear": [], "check": [], "setvar": [], "cmpvar": [],
         "trainers": [], "items": [], "mons": [], "wild": [], "warps": [], "specials": [], "text": [],
         "problems": problems}
    for pc, op, a in sorted(ins):
        if op == 0x29: s["set"].append(u16_(a))
        elif op == 0x2A: s["clear"].append(u16_(a))
        elif op == 0x2B: s["check"].append(u16_(a))
        elif op == 0x16: s["setvar"].append([u16_(a), u16_(a, 2)])
        elif op == 0x21: s["cmpvar"].append([u16_(a), u16_(a, 2)])
        elif op == 0x5C: s["trainers"].append(u16_(a, 1))
        elif op == 0x44: s["items"].append([u16_(a), u16_(a, 2)])
        # giveitem / finditem: copyvarifnotzero VAR_0x8000, <item> (a constant below 0x4000), then callstd
        elif op == 0x1A and u16_(a) == 0x8000 and u16_(a, 2) < 0x4000: s["items"].append([u16_(a, 2), 1])
        elif op == 0x79: s["mons"].append([u16_(a), a[2]])
        elif op == 0xB6: s["wild"].append([u16_(a), a[2]])
        elif op in WARPS: s["warps"].append([a[0], a[1]])
        elif op == 0x25: s["specials"].append(u16_(a))
        elif op in (0x67, 0x0F):
            p = struct.unpack_from("<I", a, 0 if op == 0x67 else 1)[0]
            t = text_at(p)
            if t and (op == 0x67 or a[0] == 0): s["text"].append(t)
    for k in ("set", "clear", "check", "specials", "trainers"):
        s[k] = sorted(set(s[k]))
    return s


def u16_(a, off=0): return struct.unpack_from("<H", a, off)[0]


def entry_points(m):
    """(source description, script address) for everything on a map that can run a script."""
    out = []
    ev = int(m["events"], 16) if m.get("events") else 0
    if ev and inrom(ev):
        e = ev - BASE
        nobj, nwarp, ncoord, nbg = rom[e], rom[e + 1], rom[e + 2], rom[e + 3]
        objs, coords, bgs = u32(e + 4), u32(e + 12), u32(e + 16)
        for i in range(nobj if inrom(objs) else 0):
            o = objs - BASE + i * 0x18
            sc = u32(o + 0x10)
            if inrom(sc):
                out.append(("object %d (local %d, gfx %d, at %d,%d, flag %04X)" % (
                    i, rom[o], rom[o + 1], u16(o + 4), u16(o + 6), u16(o + 0x14)), sc))
        for i in range(ncoord if inrom(coords) else 0):
            o = coords - BASE + i * 0x10
            sc = u32(o + 12)
            if inrom(sc):
                out.append(("trigger at %d,%d (var %04X == %d)" % (u16(o), u16(o + 2), u16(o + 6), u16(o + 8)), sc))
        for i in range(nbg if inrom(bgs) else 0):
            o = bgs - BASE + i * 0x0C
            if rom[o + 5] <= 4:                       # 0-4 are scripted signs; hidden items use other kinds
                sc = u32(o + 8)
                if inrom(sc):
                    out.append(("sign at %d,%d" % (u16(o), u16(o + 2)), sc))
    ms = int(m["scripts"], 16) if m.get("scripts") else 0
    if ms and inrom(ms):
        o = ms - BASE
        for _ in range(12):
            kind = rom[o]
            if kind == 0: break
            p = u32(o + 1)
            if kind in (2, 4) and inrom(p):          # tables of (var, value, script)
                t = p - BASE
                for _ in range(40):
                    var = u16(t)
                    if var == 0: break
                    sc = u32(t + 4)
                    if inrom(sc):
                        out.append(("map script type %d (var %04X == %d)" % (kind, var, u16(t + 2)), sc))
                    t += 8
            elif inrom(p):
                out.append(("map script type %d" % kind, p))
            o += 5
    return out


def build_index():
    maps = load("maps.json")
    idx = []
    for m in maps:
        name = "%s (%d/%d)" % (m.get("mapsec") or "?", m["group"], m["num"])
        for src, sc in entry_points(m):
            s = summarise(sc)
            s["map"] = name; s["group"] = m["group"]; s["num"] = m["num"]; s["source"] = src
            idx.append(s)
    save("script_index.json", idx)
    return idx


def names():
    """Optional pret names for vanilla flags and vars, if pret's headers are to hand (HE_PRET=<dir>)."""
    d = os.environ.get("HE_PRET")
    fl, va = {}, {}
    if d:
        import re
        env = {}
        for fn, dst in (("flags.h", fl), ("vars.h", va)):
            p = os.path.join(d, fn)
            if not os.path.exists(p): continue
            for line in open(p, encoding="utf-8", errors="replace"):
                mm = re.match(r"#define\s+(\w+)\s+(.+?)(\s*//.*)?$", line.strip())
                if not mm: continue
                expr = mm.group(2)
                try:
                    v = eval(expr, {}, env)
                    env[mm.group(1)] = v
                    if isinstance(v, int) and mm.group(1).startswith(("FLAG_", "VAR_")):
                        dst.setdefault(v, mm.group(1))
                except Exception:
                    pass
    return fl, va


def show(s, fl, va, full=False):
    def f(x): return "%04X%s" % (x, " " + fl[x] if x in fl else "")
    def v(x): return "%04X%s" % (x, " " + va[x] if x in va else "")
    print("== %s | %s | %s" % (s["map"], s["source"], s["entry"]))
    for k, lab in (("set", "set"), ("clear", "clear"), ("check", "check")):
        if s[k]: print("   %-6s %s" % (lab, ", ".join(f(x) for x in s[k])))
    if s["setvar"]: print("   setvar " + ", ".join("%s=%d" % (v(a), b) for a, b in s["setvar"]))
    if s["cmpvar"]: print("   cmpvar " + ", ".join("%s==%d" % (v(a), b) for a, b in s["cmpvar"]))
    for k in ("trainers", "items", "mons", "wild", "warps", "specials"):
        if s[k]: print("   %-8s %s" % (k, s[k]))
    for t in (s["text"] if full else s["text"][:3]):
        print("   > " + t)
    if s["problems"]: print("   !! " + "; ".join(s["problems"]))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    fl, va = names()
    if not a:
        idx = build_index()
        print("indexed %d entry points on %d maps -> %s" % (len(idx), len(set(s["map"] for s in idx)),
                                                          os.path.join(OUT, "script_index.json")))
        bad = [s for s in idx if s["problems"]]
        print("%d walks stopped at something unrecognised" % len(bad))
        sys.exit()
    idx = load("script_index.json")
    cmd = a[0]
    if cmd == "flag":
        x = int(a[1], 0)
        for s in idx:
            if x in s["set"] or x in s["clear"] or x in s["check"]:
                tag = "+".join(k for k in ("set", "clear", "check") if x in s[k])
                print("[%s]" % tag, end=" "); show(s, fl, va)
    elif cmd == "var":
        x = int(a[1], 0)
        for s in idx:
            if any(p[0] == x for p in s["setvar"] + s["cmpvar"]): show(s, fl, va)
    elif cmd == "map":
        g, n = int(a[1]), int(a[2])
        for s in idx:
            if s["group"] == g and s["num"] == n: show(s, fl, va, full=True)
    elif cmd == "text":
        w = " ".join(a[1:]).lower()
        for s in idx:
            if any(w in t.lower() for t in s["text"]): show(s, fl, va)
    elif cmd == "at":
        s = summarise(int(a[1], 16)); s["map"] = "?"; s["source"] = "direct"; show(s, fl, va, full=True)
