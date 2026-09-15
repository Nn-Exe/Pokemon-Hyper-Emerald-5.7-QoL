"""Pick the grunts that no script touches, then hide a share of them per floor (Hyper Emerald v5.7).
usage: python strict_select.py <rom.gba> --maps "Giant Chasm,Rainbow Castle,Allearth Forest" [--share 0.7] [--write]

A grunt qualifies only if ALL of these hold:
  * trainers.py gives no warning (not RISKY) and it is a plain battle (single or single without intro)
  * no reachable script anywhere in the game runs checktrainerflag / settrainerflag / cleartrainerflag on its id
  * no reachable script checks, sets or clears flag 0x500+id (the vanilla trainer-flag slot)
  * its trainer id is used by exactly one trainerbattle in reachable scripts
  * no reachable script of its map moves, removes, adds or turns its object
  * what its own script does after the battle is messages only
"Reachable" = decoded from every map's object, coordinate, sign and map-script entry points, following
goto/call/goto_if/call_if and post-battle scripts. Map scripts that cannot be fully decoded are also scanned byte by
byte for object references, so an undecodable script cannot hide a reference.
With --write the selection is saved to hidden.json.
"""
import sys, os, json, struct, argparse
from collections import OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trainers import Rom, SIZES, TB_SIZES, OBJECT_COMMANDS, CONTINUE_PTR

STATEFUL = {0x04, 0x05, 0x06, 0x07, 0x23, 0x24, 0x25, 0x26, 0x29, 0x2A, 0x39, 0x3A, 0x3B, 0x3D, 0x44, 0x45, 0x53, 0x55,
            0x61, 0x62, 0x79, 0x90, 0x91}


def decode_all(rom):
    """returns (commands, undecodable_starts): commands = list of (addr, opcode, map) for every reachable command"""
    seeds = []
    for g, m, hp in rom.maps():
        for who, sp in rom.scripts_of_map(hp):
            seeds.append((sp, "%d/%d" % (g, m)))
    seen = set()
    commands = []
    undecodable = defaultdict(list)
    stack = list(seeds)
    while stack:
        start, mp = stack.pop()
        i = start
        for _ in range(4000):
            if (i, mp) in seen or not (0 <= i < rom.n - 1): break
            seen.add((i, mp))
            op = rom.b[i]
            if op == 0x5C:
                bt = rom.b[i + 1]
                size = TB_SIZES.get(bt)
                if size is None:
                    undecodable[mp].append(i); break
                commands.append((i, op, mp))
                if bt in CONTINUE_PTR:
                    cp = rom.ptr(i + CONTINUE_PTR[bt])
                    if cp: stack.append((cp, mp))
                i += size
                continue
            size = SIZES.get(op)
            if size is None:
                undecodable[mp].append(i); break
            commands.append((i, op, mp))
            if op in (0x04, 0x05):
                t = rom.ptr(i + 1)
                if t: stack.append((t, mp))
            elif op in (0x06, 0x07):
                t = rom.ptr(i + 2)
                if t: stack.append((t, mp))
            if op in (0x02, 0x03, 0x05, 0x08, 0x0C, 0x0D): break
            i += size
    return commands, undecodable


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom")
    ap.add_argument("--maps", required=True)
    ap.add_argument("--share", type=float, default=0.7)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    rom = Rom(args.rom)
    names = [x.strip() for x in args.maps.split(",")]
    commands, undecodable = decode_all(rom)
    print("decoded %d reachable script commands; maps with an undecodable script: %d" % (len(commands), len(undecodable)))

    trainer_flag_cmds = defaultdict(list)       # trainer id -> commands
    flag_cmds = defaultdict(list)               # flag -> commands
    battles = defaultdict(set)                  # trainer id -> command addresses
    object_cmds = defaultdict(list)             # (map, local id) -> commands
    for addr, op, mp in commands:
        if op in (0x60, 0x61, 0x62): trainer_flag_cmds[rom.u16(addr + 1)].append((addr, op, mp))
        elif op in (0x29, 0x2A, 0x2B): flag_cmds[rom.u16(addr + 1)].append((addr, op, mp))
        elif op == 0x5C: battles[rom.u16(addr + 2)].add(addr)
        elif op in OBJECT_COMMANDS: object_cmds[(mp, rom.b[addr + 1] if rom.b[addr + 2] == 0 else -1)].append((addr, op))

    floors = OrderedDict()
    report = []
    for g, m, hp in rom.maps():
        if rom.section_name(hp) not in names: continue
        mp = "%d/%d" % (g, m)
        ev = rom.ptr(hp + 4); objs = rom.ptr(ev + 4)
        own = {k: rom.ptr(objs + 24 * k + 16) for k in range(rom.b[ev] if objs else 0)}
        raw_scripts = [sp for who, sp in rom.scripts_of_map(hp)] if undecodable.get(mp) else []
        for t in rom.trainers(g, m, hp):
            if t["name"] != "Grunt": continue
            tid, k, lid = t["trainer_id"], t["object"], t["local_id"]
            s = own[k]
            why = []
            if t["verdict"] == "RISKY": why.append(t["why"])
            bt = rom.b[s + 1]
            if bt not in (0, 3): why.append("battle type %d" % bt)
            if trainer_flag_cmds.get(tid): why.append("a script checks/sets its trainer flag")
            if flag_cmds.get(0x500 + tid): why.append("a script uses flag 0x%X" % (0x500 + tid))
            if len(battles.get(tid, ())) != 1: why.append("trainer id used by %d battles" % len(battles.get(tid, ())))
            refs = [a for a, op in object_cmds.get((mp, lid), [])
                    if not (s <= a < s + 64)]
            if refs: why.append("a script moves/removes its object")
            for sp in raw_scripts:
                if sp == s: continue
                seg = rom.b[sp:sp + 700]
                if any(seg[i] in OBJECT_COMMANDS and seg[i + 1] == lid and seg[i + 2] == 0 for i in range(len(seg) - 2)):
                    why.append("possible object reference in an undecodable script"); break
            # its own script after the battle
            tail = s + TB_SIZES[bt]
            i = tail
            for _ in range(40):
                op = rom.b[i]
                if op in (0x02, 0x03): break
                size = SIZES.get(op)
                if size is None: why.append("undecodable tail"); break
                if op in STATEFUL: why.append("its own script does something after the battle (0x%02X)" % op); break
                i += size
            t["exclude"] = why
            report.append(t)
            if not why: floors.setdefault(mp, []).append(t)

    eligible = sum(len(v) for v in floors.values())
    print("grunts on %s: %d, strictly script-free: %d" % (", ".join(names), len(report), eligible))
    for t in report:
        if t["exclude"]:
            print("  keep (excluded) %s object %d at (%d,%d): %s" % (t["map"], t["object"], t["x"], t["y"], "; ".join(t["exclude"])))
    hide = []
    for mp, lst in floors.items():
        lst.sort(key=lambda x: x["object"])
        n = len(lst); k = int(round(args.share * n)); keep_n = n - k
        keep = set()
        if keep_n > 0:
            step = n / keep_n
            keep = {int(step * j + step / 2) for j in range(keep_n)}
        chosen = [t for j, t in enumerate(lst) if j not in keep]
        print("  floor %s: %d eligible, hiding %d: %s" % (mp, n, len(chosen),
              ", ".join("object %d (%d,%d)" % (t["object"], t["x"], t["y"]) for t in chosen)))
        hide += chosen
    print("total: hiding %d of %d eligible grunts" % (len(hide), eligible))
    if args.write:
        json.dump([{"map": t["map"], "object": t["object"], "trainer_id": t["trainer_id"],
                    "name": "%s %s" % (t["trainer_class"], t["name"]), "x": t["x"], "y": t["y"]} for t in hide],
                  open(os.path.join(HERE, "hidden.json"), "w", encoding="utf-8"), indent=2)
        print("wrote hidden.json")


if __name__ == "__main__":
    main()
