"""List the trainers on one map, with warnings, so you can choose which to hide (Hyper Emerald v5.7).

usage:
  python trainers.py <rom.gba> --map "Route 110"        every map with that name (routes, caves, their floors)
  python trainers.py <rom.gba> --map 0/25               one map by group/number
  python trainers.py <rom.gba> --sav "my save.sav"      the map your in-game save was made on

Each trainer gets a verdict:
  SAFE   plain trainer: battle, then nothing else happens.
  CHECK  harmless to hide, but worth a look (double battle, rematch trainer).
  RISKY  do not hide unless you know the story around it: a boss class, a battle that continues into a script,
         an object the story shows/hides with a flag, or an object another script moves or removes (a cutscene).

To hide trainers, add entries to hidden.json next to this file and run trainerhide_patch.py.
"""
import struct, sys, os, json, argparse

GROUPS = 0xA54698              # gMapGroups
TRAINERS = 0x10019F8           # gTrainers (40 bytes each)
CLASS_NAMES = 0x30FCD4         # gTrainerClassNames (13 bytes each)
SECTION_NAMES = 0x5A147C       # region map entries (8 bytes, name pointer at +4)
BOSS_WORDS = ("Leader", "Elite", "Champion", "Admin", "Boss", "Rival", "Frontier", "Brain")
BATTLE_TYPES = {0: "single", 1: "single, continues into a script", 2: "single, continues into a script",
                3: "single, no intro", 4: "double", 5: "rematch", 6: "double, continues into a script",
                7: "double rematch", 8: "double, continues into a script"}
CONTINUES = {1, 2, 6, 8}
# script commands that take an object's local id as their first argument
OBJECT_COMMANDS = {0x4F: "applymovement", 0x50: "applymovementat", 0x51: "waitmovement", 0x52: "waitmovementat",
                   0x53: "removeobject", 0x54: "removeobjectat", 0x55: "addobject", 0x56: "addobjectat",
                   0x57: "setobjectxy", 0x58: "showobjectat", 0x59: "hideobjectat", 0x5B: "turnobject",
                   0x63: "setobjectxyperm", 0x64: "copyobjectxytoperm", 0x65: "setobjectmovementtype"}

# command sizes (Emerald script engine) for the post-battle decoder; unknown opcode -> treated as "complex"
SIZES = {0x00: 1, 0x01: 1, 0x02: 1, 0x03: 1, 0x04: 5, 0x05: 5, 0x06: 6, 0x07: 6, 0x08: 2, 0x09: 2, 0x0A: 3, 0x0B: 3,
         0x0F: 6, 0x16: 5, 0x17: 5, 0x18: 5, 0x19: 5, 0x1A: 5, 0x21: 5, 0x22: 5, 0x23: 5, 0x25: 3, 0x26: 5, 0x27: 1,
         0x28: 3, 0x29: 3, 0x2A: 3, 0x2B: 3, 0x2F: 3, 0x30: 1, 0x31: 3, 0x32: 1, 0x33: 4, 0x34: 3, 0x35: 1, 0x36: 3,
         0x39: 8, 0x44: 5, 0x4F: 7, 0x51: 3, 0x53: 3, 0x55: 3, 0x5A: 1, 0x5B: 4, 0x66: 1, 0x67: 5, 0x68: 1, 0x69: 1,
         0x6A: 1, 0x6B: 1, 0x6C: 1, 0x6D: 1, 0x97: 2}
STATE_CHANGES = {0x29: "setflag", 0x2A: "clearflag", 0x39: "warp", 0x44: "additem", 0x53: "removeobject",
                 0x55: "addobject", 0x23: "callnative", 0x25: "special", 0x26: "specialvar", 0x04: "call",
                 0x05: "goto", 0x06: "goto_if", 0x07: "call_if"}
CONTINUE_PTR = {1: 14, 2: 14, 6: 18, 8: 18}   # offset of the post-battle script pointer inside trainerbattle

CHARS = {0x00: ' ', 0xAD: '.', 0xB8: ',', 0xB4: "'", 0xAE: '-', 0x1B: 'e', 0x06: 'E', 0x53: 'PK', 0x54: 'MN',
         0xB5: '(m)', 0xB6: '(f)', 0xAB: '!', 0xAC: '?'}
for k in range(26): CHARS[0xBB + k] = chr(65 + k); CHARS[0xD5 + k] = chr(97 + k)
for k in range(10): CHARS[0xA1 + k] = chr(48 + k)


class Rom:
    def __init__(self, path):
        self.b = open(path, "rb").read()
        assert self.b[0xAC:0xB0] == b"BPEE", "not a BPEE ROM"
        self.n = len(self.b)
        starts = [self.u32(GROUPS + 4 * g) - 0x08000000 for g in range(64)]
        valid = [s for s in starts if 0 < s < self.n]
        self.group_start = starts
        self.counts = {}
        for g, s in enumerate(starts):
            if not (0 < s < self.n): break
            later = sorted(x for x in valid if x > s)
            self.counts[g] = (later[0] - s) // 4 if later else 160

    def u8(self, o): return self.b[o]
    def u16(self, o): return struct.unpack_from("<H", self.b, o)[0]
    def s16(self, o): return struct.unpack_from("<h", self.b, o)[0]
    def u32(self, o): return struct.unpack_from("<I", self.b, o)[0] if 0 <= o <= self.n - 4 else 0
    def ptr(self, o):
        v = self.u32(o)
        return v - 0x08000000 if 0x08000000 < v < 0x08000000 + self.n else None

    def text(self, o, lim=16):
        s = ""
        for i in range(lim):
            c = self.b[o + i]
            if c == 0xFF: break
            s += CHARS.get(c, "")
        return s.strip()

    def maps(self):
        for g, cnt in self.counts.items():
            for m in range(cnt):
                hp = self.ptr(self.group_start[g] + 4 * m)
                if hp is None or self.ptr(hp) is None or self.ptr(hp + 4) is None: continue
                lay = self.ptr(hp)
                if not (1 <= self.u32(lay) <= 256 and 1 <= self.u32(lay + 4) <= 256): continue
                ev = self.ptr(hp + 4)
                if self.b[ev] > 64 or self.b[ev + 3] > 64: continue
                yield g, m, hp

    def header(self, g, m):
        return self.ptr(self.group_start[g] + 4 * m)

    def section_name(self, hp):
        p = self.ptr(SECTION_NAMES + 8 * self.b[hp + 0x14] + 4)
        return self.text(p, 24) if p else "?"

    def scripts_of_map(self, hp):
        ev = self.ptr(hp + 4); out = []
        objs = self.ptr(ev + 4)
        for k in range(self.b[ev] if objs else 0):
            s = self.ptr(objs + 24 * k + 16)
            if s: out.append((("object", k), s))
        coords = self.ptr(ev + 12)
        for k in range(self.b[ev + 2] if coords else 0):
            s = self.ptr(coords + 16 * k + 12)
            if s: out.append((("coord", k), s))
        bgs = self.ptr(ev + 16)
        for k in range(self.b[ev + 3] if bgs else 0):
            s = self.ptr(bgs + 12 * k + 8)
            if s and self.b[bgs + 12 * k + 5] < 5: out.append((("sign", k), s))
        ms = self.ptr(hp + 8)
        if ms:
            i = ms
            while self.b[i] != 0 and i - ms < 64:
                p = self.ptr(i + 1)
                if p:
                    out.append((("mapscript", self.b[i]), p))
                    if self.b[i] in (2, 4):          # tables of {var, value, script}
                        j = p
                        while self.u16(j) != 0 and j - p < 128:
                            q = self.ptr(j + 4)
                            if q: out.append((("mapscript", self.b[i]), q))
                            j += 8
                i += 5
        return out

    def flag_users(self):
        """how many object events in the whole game use each hide flag (cached)"""
        if not hasattr(self, "_flags"):
            self._flags = {}
            for g, m, hp in self.maps():
                ev = self.ptr(hp + 4); objs = self.ptr(ev + 4)
                for k in range(self.b[ev] if objs else 0):
                    fl = self.u16(objs + 24 * k + 20)
                    if fl: self._flags[fl] = self._flags.get(fl, 0) + 1
        return self._flags

    def after_battle(self, sp):
        """what the post-battle script does: [] = messages only, else a list of state-changing commands"""
        found = []
        i = sp
        for _ in range(60):
            op = self.b[i]
            if op in (0x02, 0x03): return found
            if op not in SIZES: return found + ["unknown command 0x%02X" % op]
            if op in STATE_CHANGES: found.append(STATE_CHANGES[op])
            elif op in (0x16, 0x17, 0x18, 0x19, 0x1A) and 0x4000 <= self.u16(i + 1) < 0x8000:
                found.append("sets a story variable")
            elif op == 0x09 and self.b[i + 1] in (0, 1): found.append("gives an item")
            if op in (0x05, 0x08): return found
            i += SIZES[op]
        return found + ["long script"]

    def trainers(self, g, m, hp):
        ev = self.ptr(hp + 4); objs = self.ptr(ev + 4)
        others = self.scripts_of_map(hp)
        rows = []
        for k in range(self.b[ev] if objs else 0):
            e = objs + 24 * k
            s = self.ptr(e + 16)
            if not s or self.b[s] != 0x5C: continue
            local_id = self.b[e]
            btype = self.b[s + 1]
            tid = self.u16(s + 2)
            t = TRAINERS + 40 * tid
            cls = self.text(CLASS_NAMES + 13 * self.b[t + 1], 13)
            name = self.text(t + 4, 12)
            flag = self.u16(e + 20)
            x, y = self.s16(e + 4), self.s16(e + 6)
            warnings = []
            notes = []
            if any(w in cls for w in BOSS_WORDS): warnings.append("boss class")
            if btype in CONTINUE_PTR:
                cp = self.ptr(s + CONTINUE_PTR[btype])
                what = sorted(set(self.after_battle(cp))) if cp else ["unreadable"]
                serious = [w for w in what if w not in ("special", "specialvar", "callnative")]
                if serious: warnings.append("after the battle its script does: " + ", ".join(what))
                elif what: notes.append("after the battle it calls a game routine (usually phone/rematch registration)")
                else: notes.append("after the battle: a message only")
            if flag:
                shared = self.flag_users().get(flag, 0)
                if shared >= 3:
                    notes.append("vanishes together with %d other objects when the story sets flag 0x%X" % (shared - 1, flag))
                else:
                    warnings.append("the story shows/hides it on its own (flag 0x%X)" % flag)
            notes = []
            if btype in (4, 7): notes.append("double battle")
            if btype in (5, 7): notes.append("rematch")
            verdict = "RISKY" if warnings else ("CHECK" if notes else "SAFE")
            rows.append(dict(map="%d/%d" % (g, m), object=k, local_id=local_id, trainer_id=tid, trainer_class=cls,
                             name=name, x=x, y=y, battle=BATTLE_TYPES.get(btype, "type %d" % btype),
                             verdict=verdict, why="; ".join(warnings + notes)))
        return rows


def map_from_sav(path):
    d = open(path, "rb").read(); best = None
    for slot in (0, 1):
        for s in range(14):
            o = slot * 0xE000 + s * 0x1000
            if o + 0x1000 > len(d): continue
            if struct.unpack_from("<I", d, o + 0xFF8)[0] == 0x08012025 and struct.unpack_from("<H", d, o + 0xFF4)[0] == 1:
                c = struct.unpack_from("<I", d, o + 0xFFC)[0]
                if best is None or c > best[0]: best = (c, o)
    assert best, "no save block found in %s" % path
    return d[best[1] + 4], d[best[1] + 5]


def select_maps(rom, args):
    if args.sav:
        g, m = map_from_sav(args.sav)
        return [(g, m, rom.header(g, m))]
    if "/" in args.map and args.map.replace("/", "").isdigit():
        g, m = map(int, args.map.split("/"))
        return [(g, m, rom.header(g, m))]
    want = args.map.lower()
    exact = [(g, m, hp) for g, m, hp in rom.maps() if rom.section_name(hp).lower() == want]
    if exact: return exact
    return [(g, m, hp) for g, m, hp in rom.maps() if want in rom.section_name(hp).lower()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom")
    ap.add_argument("--map", help='map name like "Route 110", or group/number like 0/25')
    ap.add_argument("--sav", help="use the map an in-game save was made on")
    ap.add_argument("--json", action="store_true", help="print JSON entries ready to paste into hidden.json")
    args = ap.parse_args()
    if not (args.map or args.sav): ap.error("give --map or --sav")
    rom = Rom(args.rom)
    maps = select_maps(rom, args)
    if not maps:
        sys.exit("no map named %r (use the name shown on the in-game map screen, or group/number)" % args.map)
    rows = []
    for g, m, hp in maps:
        rows += rom.trainers(g, m, hp)
    if args.json:
        print(json.dumps([{k: r[k] for k in ("map", "object", "trainer_id", "trainer_class", "name", "x", "y")}
                          for r in rows], indent=2))
        return
    for g, m, hp in maps:
        mine = [r for r in rows if r["map"] == "%d/%d" % (g, m)]
        print("\n%s  (map %d/%d)  %d trainer%s" % (rom.section_name(hp), g, m, len(mine), "" if len(mine) == 1 else "s"))
        for r in mine:
            print("  object %-2d %-6s %-14s %-12s at (%d,%d)  %s%s" % (
                r["object"], r["verdict"], r["trainer_class"], r["name"], r["x"], r["y"], r["battle"],
                ("  -- " + r["why"]) if r["why"] else ""))


if __name__ == "__main__":
    main()
