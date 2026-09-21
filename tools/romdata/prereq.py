"""What has to be true for the game to set a flag: the conditions on the script path that reaches it.

    set HE_ROM=<the patched build>
    python tools/romdata/prereq.py 0x4158 [0x4159 ...]

For every script in out/script_index.json that sets the flag, this walks the script again keeping track of
branches: `checkflag F` then `goto_if` (condition 1 = taken when set, 0 = taken when clear), and
`compare_var_to_value` then `goto_if`. Each path that reaches `setflag` is reported with the conditions
it passed. It also reports what makes the script reachable at all: an object's hide flag (the object only
exists while that flag is clear), a trigger's or map script's var == value.

It is a reading aid, not a proof: calls are followed as if inlined, loops are cut, and a condition the
script tests on a register (specialvar results) shows up as a var test on VAR_RESULT (0x800D).
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romlib import rom, load
from scripts import OPLEN, TB_PTRS, TB_SCRIPT, BASE, inrom

COND = {0: "<", 1: "==", 2: ">", 3: "<=", 4: ">=", 5: "!="}


def paths_to(entry, target, max_paths=12, max_steps=3000, op_want=0x29):
    """Conditions along each path from `entry` to `setflag target` (or clearflag, with op_want=0x2A)."""
    found = []
    stack = [(entry, (), None, frozenset(), ())]
    steps = 0
    while stack and len(found) < max_paths and steps < max_steps:
        pc, conds, last, seen, callstack = stack.pop()
        while True:
            steps += 1
            if steps > max_steps or not inrom(pc) or pc in seen: break
            seen = seen | {pc}
            o = pc - BASE
            op = rom[o]
            if op == 0x5C:
                kind = rom[o + 1]
                if kind not in TB_PTRS: break
                n = 5 + 4 * TB_PTRS[kind]
                if kind in TB_SCRIPT:
                    p = struct.unpack_from("<I", rom, o + 1 + 5 + 4 * (TB_SCRIPT[kind] - 1))[0]
                    stack.append((p, conds + (("won trainer", struct.unpack_from("<H", rom, o + 2)[0]),), last, seen, callstack))
                pc += 1 + n
                continue
            if op not in OPLEN: break
            n = OPLEN[op]
            a = rom[o + 1:o + 1 + n]
            if op == op_want and struct.unpack_from("<H", a, 0)[0] == target:
                found.append(conds); break
            if op == 0x2B:
                last = ("flag", struct.unpack_from("<H", a, 0)[0])
            elif op == 0x21:
                last = ("var", struct.unpack_from("<H", a, 0)[0], struct.unpack_from("<H", a, 2)[0])
            elif op in (0x06, 0x07):
                cond, dest = a[0], struct.unpack_from("<I", a, 1)[0]
                if last:
                    taken = (last, cond, True); skipped = (last, cond, False)
                else:
                    taken = skipped = None
                stack.append((dest, conds + ((taken,) if taken else ()), last, seen,
                              callstack + ((pc + 1 + n),) if op == 0x07 else callstack))
                if skipped: conds = conds + (skipped,)
            elif op == 0x05:
                pc = struct.unpack_from("<I", a, 0)[0]; continue
            elif op == 0x04:
                callstack = callstack + (pc + 1 + n,)
                pc = struct.unpack_from("<I", a, 0)[0]; continue
            elif op == 0x03:
                if callstack:
                    pc = callstack[-1]; callstack = callstack[:-1]; continue
                break
            elif op in (0x02, 0x08, 0x0C, 0x0D, 0x24, 0xB9):
                break
            pc += 1 + n
    return found


def describe(c):
    if c[0] == "won trainer": return "beat trainer %d" % c[1]
    (kind, *rest), cond, taken = c
    if kind == "flag":
        f = rest[0]
        # after checkflag the result is 1 when set: cond 1 (==) is "set", cond 0 (<) is "clear"
        want_set = {1: True, 0: False, 5: False}.get(cond)
        if want_set is None: return "flag %04X ?%d" % (f, cond)
        if not taken: want_set = not want_set
        return "flag %04X %s" % (f, "SET" if want_set else "clear")
    v, val = rest
    op = COND[cond]
    if not taken:
        op = {"==": "!=", "!=": "==", "<": ">=", ">=": "<", ">": "<=", "<=": ">"}[op]
    return "var %04X %s %d" % (v, op, val)


def simplify(conds):
    out = []
    for c in conds:
        d = describe(c)
        if d not in out: out.append(d)
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    idx = load("script_index.json")
    args = sys.argv[1:]
    if args and args[0] == "clear":                 # who clears a flag: what makes a hidden NPC appear
        for arg in args[1:]:
            f = int(arg, 0)
            print("######## cleared: flag %04X" % f)
            for s in idx:
                if f not in s["clear"]: continue
                t = next((x for x in s["text"] if len(x) > 20), "")[:110]
                print("  %s | %s | %s" % (s["map"], s["source"], s["entry"]))
                print("     | " + t)
                for p in paths_to(int(s["entry"], 16), f, op_want=0x2A)[:3]:
                    print("     path: " + ("; ".join(simplify(p)) or "(unconditional)"))
        sys.exit()
    for arg in args:
        f = int(arg, 0)
        print("######## flag %04X" % f)
        for s in idx:
            if f not in s["set"]: continue
            print("  %s | %s | %s" % (s["map"], s["source"], s["entry"]))
            for p in paths_to(int(s["entry"], 16), f)[:4]:
                print("     path: " + ("; ".join(simplify(p)) or "(unconditional)"))
