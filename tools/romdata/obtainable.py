"""Can the player get everything the guide's family lists show? An audit, to run after a new ROM.

    HE_ROM=<patched rom> python tools/romdata/obtainable.py [-v]

For every Pokémon and form in site/src/data/pokedex.json it looks for a way to it - a wild encounter, a scripted
battle, a gift, an egg, an evolution, a form change (tools/romdata/forms.py) - and checks that what the way needs
is itself there: the item a form or an evolution asks for has a source, the move is one the Pokémon learns, the
other half of a fusion can be had. It prints what it found no way to, and exits 1 if that is anything but the
forms forms.TRAINER_ONLY already keeps off the lists.

Where it looks (so "no source found" means only this much):
  items    giveitem / finditem in any script (setorcopyvar 0x8000, item; setorcopyvar 0x8001, n; callstd), the
           script index's additem, mart lists (pokemart), what wild Pokémon hold, and the Battle Points prizes
           the Exchange Service Corner names ("You've chosen a Max Mushroom.")
  Pokémon  wild.json, static.json (scripted battles), givemon in scripts, the Quest Log's Legends chapter
           (patches/questlog/legends.py, places read from the scripts) and the Legendary Locations guide
           (site/src/data/legendaries.ts: its 'community' entries come from player guides, not from the scripts)
It does not play the game: a way that exists here can still be blocked by something it cannot see.
Run tools/build_pokedex.py and tools/build_site_data.py first.
"""
import collections
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import romlib as R                                         # noqa: E402
import forms as F                                          # noqa: E402
from display_names import item_name as item_display        # noqa: E402

rom = R.rom
u16, u32 = R.u16, R.u32
VERBOSE = "-v" in sys.argv
DATA = os.path.join(HERE, "..", "..", "site", "src", "data")
OUT = os.path.join(HERE, "out")
EVOS, EEVEE, EEVEE_EVOS = 0x00F387C0, 133, 0x01F0B4A0
ITEMS = u32(0x1C8) - 0x08000000
MAX_MUSHROOM = 87
MANAPHY, PHIONE = 543, 542          # Manaphy's egg is a Phione (the egg routine, 0x09F0069A)


def load(folder, name):
    return json.load(open(os.path.join(folder, name), encoding="utf-8"))


dex = load(DATA, "pokedex.json")
species = dex["species"]
by = {s["sid"]: s for s in species}
TMS = dex["tm"]


def iname(i):
    return item_display(i, R.decode(ITEMS + 44 * i, 14)[0]) if 0 < i < 769 else "item %d" % i


# ---------------- where items come from ----------------
item_src = collections.defaultdict(set)
for m in re.finditer(rb"\x1a\x00\x80(..)\x1a\x01\x80(..)\x09(.)", rom, re.S):
    it = struct.unpack("<H", m.group(1))[0]
    if 0 < it < 769:
        item_src[it].add("script gift / item ball")
script_index = load(OUT, "script_index.json")
for e in script_index:
    for it, n in e["items"]:
        if 0 < it < 769:
            item_src[it].add("script (additem)")
for m in re.finditer(rb"\x86(....)", rom, re.S):          # pokemart <list>: u16 items, 0 ends
    p = struct.unpack("<I", m.group(1))[0]
    if not 0x08000000 <= p < 0x08000000 + len(rom) or p & 1:
        continue
    o, lst = p - 0x08000000, []
    while len(lst) < 60:
        v = u16(o)
        if v == 0:
            break
        if not 0 < v < 769:
            lst = []
            break
        lst.append(v)
        o += 2
    if 2 <= len(lst) < 60 and u16(o) == 0:
        for it in lst:
            item_src[it].add("mart")
for s in species:
    for it in s["items"]:
        item_src[it["id"]].add("held by wild " + s["name"])
by_item_name = {}
for i in range(1, 769):
    by_item_name.setdefault(R.decode(ITEMS + 44 * i, 14)[0], i)
for m in re.finditer(re.escape(bytes([0xD3, 0xE3, 0xE9])), rom):          # "You've chosen a ..."
    txt = R.decode(m.start(), 80)[0].replace(chr(10), " ")
    mm = re.match(r"You.ve chosen (?:a |an |the )?(.+?)\. ?Is that correct", txt)
    if mm and mm.group(1) in by_item_name:
        item_src[by_item_name[mm.group(1)]].add("Battle Points prize")

# ---------------- where Pokémon come from ----------------
direct = collections.defaultdict(set)
for m in load(DATA, "wild.json"):
    for key in ("land", "water", "rock"):
        for sl in (m.get(key) or {}).get("slots", []):
            direct[sl["sid"]].add("wild")
    for rod in (m.get("fish") or {}).values():
        if isinstance(rod, dict):
            for sl in rod.get("slots", []):
                direct[sl["sid"]].add("wild")
for e in load(DATA, "static.json"):
    direct[e["sid"]].add("scripted battle")
for e in script_index:
    for sp, lv in e["mons"]:
        direct[sp].add("gift (script)")
for m in re.finditer(rb"\x79(..)([\x01-\x64])(..)\x00{9}", rom, re.S):    # givemon species, level, item, 0...
    direct[struct.unpack("<H", m.group(1))[0]].add("gift (givemon)")
ids_by_name = {k.lower(): v for k, v in load(DATA, "species.json").items()}
legends = open(os.path.join(DATA, "legendaries.ts"), encoding="utf-8").read()
for block in re.finditer(r"mons: \[(.*?)\],.*?source: '(\w+)'", legends, re.S):
    for a, b in re.findall(r"'([^']*)'|\"([^\"]*)\"", block.group(1)):
        sid = ids_by_name.get((a or b).lower())
        if sid:
            direct[sid].add("legendary guide (%s)" % block.group(2))
sys.path.append(os.path.join(HERE, "..", "..", "patches", "questlog"))
from legends import LEGENDS                                # noqa: E402  (the Quest Log's Legends chapter)
first_of = {}
for s in species:
    if s["dex"]:
        first_of.setdefault(s["dex"], s["sid"])
for number, name, hint, where in LEGENDS:
    if number in first_of:
        direct[first_of[number]].add("Legends chapter: " + where.split(".")[0])

# ---------------- what follows from what ----------------
learn = {s["sid"]: {m for _, m in s["levelUp"]} | {TMS[i]["move"] for i in s["tm"]} | set(s["egg"]) for s in species}
links = F.links(rom, lambda sid: by[sid]["name"] if sid in by else "species %d" % sid,
                lambda i: "ITEM#%d" % i, lambda m: "MOVE#%d" % m, lambda ab: None)
partner = {(b, f): o for b, f, it, o in F.FUSIONS}
have = {sid: "; ".join(sorted(v)) for sid, v in direct.items() if sid in by}
why_not = {}
changed = True
while changed:
    changed = False
    if MANAPHY in have and PHIONE in by and PHIONE not in have:
        have[PHIONE] = "egg from Manaphy"
        changed = True
    for s in species:
        for e in s.get("evo", []):
            if e["to"] in have and s["sid"] not in have and "Undiscovered" not in by[e["to"]]["eggGroups"]:
                have[s["sid"]] = "egg from " + by[e["to"]]["name"]
                changed = True
            if s["sid"] in have and e["to"] in by and e["to"] not in have:
                have[e["to"]] = "evolve %s (%s)" % (s["name"], e["how"])
                changed = True
    for ln in links:
        a, b = ln["from"], ln["to"]
        if a not in by or b not in by or b in have:
            continue
        if a not in have:
            why_not[b] = "its base %s has no way" % by[a]["name"]
            continue
        items = [int(x) for x in re.findall(r"ITEM#(\d+)", ln["how"])]
        moves = [int(x) for x in re.findall(r"MOVE#(\d+)", ln["how"])]
        why = ""
        if moves and not any(mv in learn[a] for mv in moves):
            why = "%s does not learn the move (id %s) by level, TM or egg" % (by[a]["name"], moves)
        elif ln["kind"] == "gmax" and not item_src.get(MAX_MUSHROOM):
            why = "no source found for the Max Mushroom"
        elif items and not any(item_src.get(i) for i in items):
            why = "no source found for " + " / ".join(iname(i) for i in items)
        elif ln["kind"] == "fusion" and partner.get((a, b)) not in have:
            why = "the other half, %s, has no way" % by[partner[(a, b)]]["name"]
        if why:
            why_not[b] = why
        else:
            have[b] = "%s of %s (%s)" % (ln["kind"], by[a]["name"],
                                         re.sub(r"ITEM#(\d+)", lambda m: iname(int(m.group(1))),
                                                re.sub(r"MOVE#(\d+)", lambda m: "move %s" % m.group(1), ln["how"])))
            why_not.pop(b, None)
            changed = True

# ---------------- report ----------------
names_seen = set()
missing, expected = [], []
for s in species:
    key = (s["dex"], s["name"])
    if s["sid"] in have:
        names_seen.add(key)
for s in species:
    if s["sid"] in have or (s["dex"], s["name"]) in names_seen:      # (a second slot of something that has a way)
        continue
    (expected if s["sid"] in F.TRAINER_ONLY else missing).append(s)
print("Pokémon and forms with a way to them: %d of %d" % (len(species) - len(missing) - len(expected), len(species)))
print("kept off the lists (forms.TRAINER_ONLY), no way found, as expected: %s"
      % (", ".join(s["name"] for s in expected) or "none"))
print("NO WAY FOUND, and still on the lists: %d" % len(missing))
for s in missing:
    print("  %-34s #%03d  %s" % (s["name"], s["dex"], why_not.get(s["sid"], "nothing leads to it")))
stale = [by[sid]["name"] for sid in F.TRAINER_ONLY if sid in have]
if stale:
    print("in forms.TRAINER_ONLY although a way exists: %s" % ", ".join("%s (%s)" % (n, have[sid]) for n, sid in
                                                                       zip(stale, [s for s in F.TRAINER_ONLY if s in have])))
trigger = sorted({int(x) for ln in links for x in re.findall(r"ITEM#(\d+)", ln["how"])})
evo_items = collections.defaultdict(list)
for s in species:
    o, n = (EEVEE_EVOS, 10) if s["sid"] == EEVEE else (EVOS + 40 * s["sid"], 5)
    for k in range(n):
        m, p, t, x = struct.unpack_from("<HHHH", rom, o + 8 * k)
        if (m & 0xFF) in (6, 7, 20, 21, 27, 28) and t in by and 0 < p < 769:
            evo_items[p].append("%s -> %s" % (s["name"], by[t]["name"]))
no_item = [i for i in trigger + sorted(evo_items) if not item_src.get(i)]
print("items that forms need: %d, that evolutions need: %d; with no source found: %s"
      % (len(trigger), len(evo_items), ", ".join(iname(i) for i in no_item) or "none"))
if VERBOSE:
    for i in trigger + sorted(evo_items):
        print("  %-18s %s" % (iname(i), ", ".join(sorted(item_src.get(i, []))[:3]) or "NO SOURCE FOUND"))
    for s in species:
        if s["sid"] in have and s["form"] != "Standard":
            print("  %-34s %s" % (s["name"], have[s["sid"]]))
sys.exit(1 if missing or no_item or stale else 0)
