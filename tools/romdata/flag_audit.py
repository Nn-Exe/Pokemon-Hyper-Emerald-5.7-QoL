"""Every flag a script sets, what it is for, and whether the Journal covers it.

    python tools/romdata/flag_audit.py            (after scripts.py has built out/script_index.json)

Writes out/flag_audit.json and prints a summary. Each flag-setting script is put in one kind:
  encounter  a static / scripted wild battle (legendaries, set-piece Pokemon)
  gift       givemon: a Pokemon handed to you
  item       an item ball or an item given (object gfx 59, or giveitem)
  trainer    a trainer battle
  event      anything else: story beats, NPCs appearing or leaving, doors opening
Flags that are set in one script and checked in another are joined into chains, so a quest spread over several
maps comes out as one group.
"""
import collections, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, os.path.join(HERE, "..", "..", "patches", "journal"))
import steps as S

ITEM_BALL_GFX = 59
SYSTEM = range(0x860, 0x900)            # badges, pokedex, system flags: not content of their own


def num(f):
    return int(f, 16) if isinstance(f, str) else f


def journal_flags():
    out = {}
    for n, (h, st, body) in enumerate(S.STEPS, 1):
        for f in st["flags"]:
            out.setdefault(f, n)
        for f, _, _ in st.get("members", []):
            out.setdefault(f, n)
    return out


def kind(r):
    m = re.search(r"gfx (\d+)", r["source"])
    if r["wild"]:
        return "encounter"
    if r["mons"]:
        return "gift"
    if r["items"] or (m and int(m.group(1)) == ITEM_BALL_GFX):
        return "item"
    if r["trainers"]:
        return "trainer"
    return "event"


def main():
    idx = json.load(open(os.path.join(OUT, "script_index.json")))
    species = json.load(open(os.path.join(OUT, "species.json")))
    items = json.load(open(os.path.join(OUT, "items.json")))
    jf = journal_flags()

    def sp(n):
        return species.get(str(n), "#%d" % n)

    def it(n):
        v = items[n] if isinstance(items, list) and n < len(items) else items.get(str(n)) if isinstance(items, dict) else None
        if isinstance(v, dict):
            v = v.get("name")
        return v or "item %d" % n

    setters = collections.defaultdict(list)
    checkers = collections.defaultdict(list)
    for i, r in enumerate(idx):
        for f in r["set"]:
            setters[num(f)].append(i)
        for f in r["check"]:
            checkers[num(f)].append(i)

    flags = {}
    for f, who in setters.items():
        if f < 0x20 or f in SYSTEM:
            continue
        kinds = collections.Counter(kind(idx[i]) for i in who)
        k = next(k for k in ("encounter", "gift", "item", "trainer", "event") if kinds[k])
        flags[f] = {
            "flag": "0x%04X" % f, "kind": k, "journal": jf.get(f),
            "maps": sorted({idx[i]["map"] for i in who}),
            "checked_on": sorted({idx[i]["map"] for i in checkers.get(f, [])} - {idx[i]["map"] for i in who}),
            "wild": sorted({"%s Lv%d" % (sp(s), l) for i in who for s, l in idx[i]["wild"]}),
            "mons": sorted({"%s Lv%d" % (sp(s), l) for i in who for s, l in idx[i]["mons"]}),
            "items": sorted({it(n) for i in who for n, _ in idx[i]["items"]}),
            "text": next((t for i in who for t in idx[i]["text"]), "")[:240],
            "entries": [idx[i]["entry"] for i in who],
        }

    # chains: flags joined when one script sets one and checks (or sets) another
    parent = {f: f for f in flags}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in idx:
        fs = [num(f) for f in r["set"] + r["check"] if num(f) in flags]
        for a in fs[1:]:
            parent[find(a)] = find(fs[0])
    chains = collections.defaultdict(list)
    for f in flags:
        chains[find(f)].append(f)

    groups = []
    for root, fs in chains.items():
        fs.sort()
        maps = sorted({m for f in fs for m in flags[f]["maps"]})
        groups.append({
            "flags": ["0x%04X" % f for f in fs],
            "maps": maps,
            "journal": sorted({flags[f]["journal"] for f in fs if flags[f]["journal"]}),
            "kinds": dict(collections.Counter(flags[f]["kind"] for f in fs)),
            "encounters": sorted({w for f in fs for w in flags[f]["wild"]}),
            "gifts": sorted({w for f in fs for w in flags[f]["mons"]}),
        })
    groups.sort(key=lambda g: (-len(g["flags"]), g["maps"]))

    problems = [{"map": r["map"], "source": r["source"], "entry": r["entry"], "problem": r["problems"]}
                for r in idx if r["problems"]]
    out = {"flags": [flags[f] for f in sorted(flags)], "chains": groups, "problems": problems}
    json.dump(out, open(os.path.join(OUT, "flag_audit.json"), "w"), indent=1, ensure_ascii=False)

    c = collections.Counter(v["kind"] for v in flags.values())
    cj = collections.Counter(v["kind"] for v in flags.values() if v["journal"])
    print("%d flags set by scripts (temp and system flags left out)" % len(flags))
    for k in ("encounter", "gift", "item", "trainer", "event"):
        print("  %-9s %4d   in the Journal: %d" % (k, c[k], cj[k]))
    print("%d chains; %d touch the Journal; %d scripts stop at an unknown command" % (
        len(groups), sum(1 for g in groups if g["journal"]), len(problems)))


if __name__ == "__main__":
    main()
