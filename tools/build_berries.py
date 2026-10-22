"""Where to get every Berry, for the guide's Berries page.

usage: HE_ROM=<patched rom> HE_ROMDATA_OUT=<folder of the romdata dumps> python tools/build_berries.py
writes site/src/data/berries.json; run the romdata dumps first (dump_tables, dump_maps, scan_wild; scripts.py
for its index is not needed).

The berries are the items in the Bag's Berries pocket (pocket 4 of the item table). Where each comes from:
  trees      every map object that runs the berry tree script (0x082742F9) is a tree; its tree id is the object's
             trainer-range field (+14). A New Game plants 80 of the ids with the script command setberrytree
             (0x8A: id, berry, stage) in one run of 80 commands (0x0827149D): berry type n is item 132 + n, stage 5
             is ripe. The rest start as soft soil. Checked against a New Game in mGBA: all 128 slots of the save
             block's berry trees (+0x169C) held exactly what that run plants (_testrun/berries). Trees on two maps
             can share an id, and so one plot of soil: picking one empties the other.
  scripts    tools/romdata/item_sources.py: item balls, gifts, shop lists, hidden items, scripted Pokemon.
  daily      NPCs whose script does `random N`, adds a base to the result and gives that item: one of N berries.
             A flag in 0x920-0x95F is cleared every day (ClearDailyFlags, 0x0809D3A0), so such a gift comes
             back the next day.
  held       wild Pokemon (tools/romdata/out/wild.json) whose base stats name the berry as a held item: the
             first of the two is held 50% of the time, the second 5%, both the same: always.
How a gift is earned is in NOTES, written from the script; the build stops on a gift without one.
"""
import json
import os
import re
import struct
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "romdata"))
import romlib as R                                          # noqa: E402
import scripts as S                                         # noqa: E402
import item_sources as I                                    # noqa: E402
import tables                                               # noqa: E402
from display_names import item_name                        # noqa: E402
from species_display import display_name                  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DATA = os.path.join(HERE, "..", "site", "src", "data")
rom = R.rom
T = tables.of(rom)
ITEMS = R.u32(0x1C8) - S.BASE
BERRY_POCKET = 4
TREE_SCRIPT = 0x082742F9
SETBERRYTREE, RIPE = 0x8A, 5
FIRST_BERRY, EMERALD_BERRIES = 133, 43             # Cheri .. Enigma; berry type n = item 132 + n
DAILY = range(0x920, 0x960)
assert struct.unpack_from("<I", rom, 0x001DB67C + 4 * SETBERRYTREE)[0] == 0x0809B71D, "setberrytree moved"
# ClearDailyFlags: memset(SaveBlock1 + 0x1394, 0, 8) - the flags from 0x920 (0x1270 + 0x920 / 8) for 64
assert R.u32(0x0009D3BC) == 0x1394 and rom[0x0009D3AC:0x0009D3AE] == bytes.fromhex("0822"), "ClearDailyFlags moved"

# ---------------- how each gift is earned (from the scripts) ----------------
# (group, num, x, y) of the giver: what they ask. A "daily" giver's note is followed by the berries it picks from.
BLENDER = ("She gives a Pecha Berry to a player with a Pokéblock Case, room in it and no Berries at all; once a "
           "day.")
NOTES = {
    (0, 19, 37, 6): "A man by the berry trees shares one with you, once.",
    (37, 22, 6, 14): "Five, once, from a man whose wife has slept since a visit to the Lost Tower, when she wakes "
                     "(he thanks the Lunar Feather you carry).",
    (37, 100, 6, 25): BLENDER,
    (13, 4, 26, 5): BLENDER + " She is not there on every visit: the lobby decides as you walk in.",
    (31, 0, 7, 4): None,                                    # the Berry Master's wife: the saying, per berry (below)
    (26, 46, 2, 3): None,                                   # Scott: two gifts, told apart by the berry
    (0, 2, 32, 15): "The lady whose Skitty the men in black took into the casino: bring it back and she heals your "
                    "team and gives you Jaboca, Rowap, Kee and Maranga, once.",
}
SCOTT = {173: "Scott, for your first Silver Symbol.", 174: "Scott, once you hold all seven Gold Symbols."}
WIFE_NOTE = "The Berry Master’s wife, once, for the good saying “%s” (two Easy Chat words she asks for)."
DAILY_NOTES = {
    (31, 0, 4, 4): "The Berry Master, once a day: two Berries, one from each list.",
    (31, 0, 7, 4): "The Berry Master’s wife, once a day, for any saying you tell her.",
    (0, 7, 9, 43): "Kiri, a girl in Sootopolis City, once a day: two Berries, one from each list.",
    (0, 26, 23, 8): "A girl by the berry trees, once a day.",
    (0, 29, 27, 42): "A Berry Crush fan, once a day.",
    (0, 5, 54, 5): "A man who says a Berry suits you, once a day.",
    (17, 1, 11, 6): "The youngest of the flower-shop sisters, once a day.",
}
# The wife's five good sayings: the routine 0x0811BF40 compares the two Easy Chat words you give her with this
# table and puts 1-5 (0 for any other saying) in VAR_0x8004, which her script turns into a berry. Easy Chat
# words: group << 9 | index; the groups' word lists at EC_GROUPS ({records, u16 count, u16 count}, a record
# {text, order, enabled}); groups 0 and 21 are Pokemon, the index being the species.
WIFE = (31, 0, 7, 4)
SAYINGS, SAYINGS_LITERAL = 0x0059776C, 0x0011BF60
EC_GROUPS, EC_SPECIES = 0x0059D004, (0, 21)
assert R.u32(SAYINGS_LITERAL) == S.BASE + SAYINGS, "the good-saying table moved"


def ec_word(w):
    group, index = w >> 9, w & 0x1FF
    if group in EC_SPECIES:
        return display_name(index, species[str(index)])
    records = R.u32(EC_GROUPS + 8 * group) - S.BASE
    return R.decode(R.u32(records + 12 * index) - S.BASE, 20)[0]


# trees that some days are not there: a script on their map sets the object's flag (the build stops on one
# without a note)
TREE_NOTES = {
    (0, 45): "On Mirage Island, which is there only on some days: on the others Route 130's map script hides "
             "everything on it.",
}
# a gift that cannot be had in normal play
NOT_A_SOURCE = {
    (8, 1, 4, 2): "Dad gives an Enigma Berry only to a save that holds an e-Reader Berry (special 0x35 checks the "
                  "save's e-Reader data, 0x080E162C), which no part of the game itself gives.",
}

maps = R.load("maps.json")
species = R.load("species.json")
by_map = {(m["group"], m["num"]): m for m in maps}


def name(i):
    return item_name(i, I.item_name(i))


def text(p):
    s = R.decode(p, 300)[0].replace("{55}{56}{57}{58}{59}", "Pokéblock")     # the font's POKéBLOCK glyphs
    s = re.sub(r"\{[^}]*\}", " ", s.replace("\n", " "))
    return re.sub(r"\s+([.,;])", r"\1", re.sub(r"\s+", " ", s)).strip()


def number(i):
    """the No. the Berries pocket prints (patches/berrynum carries the hack's own on after Enigma's No43)"""
    if i < FIRST_BERRY + EMERALD_BERRIES:
        return i - FIRST_BERRY + 1
    return 44 + i - 704 if i <= 727 else 68 + i - 762


# ---------------- the berries ----------------
berry_items = [i for i in range(1, T.items) if rom[ITEMS + 44 * i + 26] == BERRY_POCKET]
first_of = {}
for i in berry_items:
    first_of.setdefault(name(i), i)
copies = [i for i in berry_items if first_of[name(i)] != i]       # items 762-765: the same names again
berries = [i for i in berry_items if i not in copies]

# ---------------- trees ----------------
runs = []
pos = 0
while True:
    j = rom.find(bytes([SETBERRYTREE]), pos)
    if j < 0:
        break
    n = 0
    while rom[j + 4 * n] == SETBERRYTREE and rom[j + 4 * n + 2] <= EMERALD_BERRIES and rom[j + 4 * n + 3] <= 7:
        n += 1
    if n >= 10:
        runs.append((j, n))
        pos = j + 4 * n
    else:
        pos = j + 1
assert len(runs) == 1, "the New Game planting script: %s" % runs
start, count = runs[0]
planted = {}
for k in range(count):
    _, tree, berry, stage = rom[start + 4 * k:start + 4 * k + 4]
    assert stage == RIPE and tree not in planted
    planted[tree] = FIRST_BERRY + berry - 1

trees = []                                  # (map, x, y, tree id)
for m in maps:
    e = m.get("events")
    if not e:
        continue
    ev = (int(e, 16) if isinstance(e, str) else e) - S.BASE
    objs = R.u32(ev + 4)
    if not S.inrom(objs):
        continue
    for k in range(rom[ev]):
        o = objs - S.BASE + 24 * k
        if R.u32(o + 16) != TREE_SCRIPT:
            continue
        x, y = struct.unpack_from("<hh", rom, o + 4)
        if I.unreleased(m["group"], m["num"]) or I.walled_in(m, x, y):
            continue
        trees.append((m, x, y, R.u16(o + 14), R.u16(o + 20)))
maps_of_id = defaultdict(set)
set_on = {}                                 # the flags a map's own scripts set
for m, x, y, tid, flag in trees:
    if flag and (m["group"], m["num"]) not in set_on:
        set_on[(m["group"], m["num"])] = {f for _, e in S.entry_points(m) for f in S.summarise(e)["set"]}
for m, x, y, tid, flag in trees:
    maps_of_id[tid].add((m["group"], m["num"]))

sources = defaultdict(list)
groups = {}
problems = []
for m, x, y, tid, flag in trees:
    item = planted.get(tid)
    if not item:
        continue
    gn = (m["group"], m["num"])
    if flag and flag in set_on[gn] and gn not in TREE_NOTES:
        problems.append("the %s tree on %s (%d,%d) hides by flag %#x, which the map's scripts set: no TREE_NOTES"
                        % (name(item), I.place(m), x, y, flag))
    key = (item, m["group"], m["num"])
    twins = sorted({I.place(by_map[gn]) for gn in maps_of_id[tid] if gn != (m["group"], m["num"])})
    if key not in groups:
        groups[key] = {"kind": "tree", "place": I.place(m), "spot": "%d-%d-%d-%d" % (m["group"], m["num"], x, y),
                       "count": 0, "twins": []}
        if gn in TREE_NOTES and flag:
            groups[key]["how"] = TREE_NOTES[gn]
            groups[key]["spot"] = None      # (on Mirage Island the map's own tiles are sea: the land comes with it)
        sources[item].append(groups[key])
    groups[key]["count"] += 1
    groups[key]["twins"] = sorted(set(groups[key]["twins"]) | set(twins))

# ---------------- the wife's sayings: her script's branch on VAR_0x8004 -> the berry it gives ----------------
wife_says = {}
for desc, entry in S.entry_points(by_map[WIFE[:2]]):
    if ", at %d,%d," % WIFE[2:] not in desc:
        continue
    ins = sorted(S.walk(entry)[0])
    for k, (pc, op, a) in enumerate(ins):
        if op == 0x21 and S.u16_(a) == 0x8004 and 1 <= S.u16_(a, 2) <= 5 and ins[k + 1][1] == 0x06:
            target = struct.unpack_from("<I", ins[k + 1][2], 1)[0]
            item = next(S.u16_(a2, 2) for pc2, op2, a2 in ins if pc2 >= target and op2 == 0x1A
                        and S.u16_(a2) == 0x8000 and S.u16_(a2, 2) < 0x4000)
            words = struct.unpack_from("<HH", rom, SAYINGS + 4 * (S.u16_(a, 2) - 1))
            wife_says[item] = " ".join(ec_word(w) for w in words)
assert len(wife_says) == 5, "the wife's sayings: %s" % wife_says

# ---------------- what scripts hand over ----------------
found, flags = I.scan(set(berries))
ORDER = {"ball": 1, "hidden": 1, "unseen": 1, "given": 2, "wild": 2, "prize": 3, "shop": 4}
for (item, g, n, kind), src in sorted(found.items(), key=lambda kv: (ORDER.get(kv[0][3], 9), kv[0][1:3])):
    if kind == "shop":
        sources[item].append({"kind": "shop", "place": src["place"], "price": src["price"]})
    elif kind in ("ball", "hidden", "unseen"):
        sources[item].append({"kind": "ball" if kind != "hidden" else "hidden", "place": src["place"],
                              "spot": src.get("spot")})
    elif kind == "given":
        gx = tuple(int(v) for v in src["spot"].split("-"))
        if gx in NOT_A_SOURCE:
            continue
        if gx not in NOTES:
            problems.append("%s from %s (%s) has no note in NOTES; its script says:\n      %s"
                            % (name(item), src["place"], src["spot"], "\n      ".join(src.get("text", [])[:3])))
            continue
        sources[item].append({"kind": "gift", "place": src["place"], "spot": src["spot"],
                              "how": NOTES[gx] or (WIFE_NOTE % wife_says[item] if gx == WIFE else SCOTT[item])})
    else:
        problems.append("%s at %s: a %r source this page has no words for" % (name(item), src["place"], kind))

# ---------------- the daily gifts: random N + base, given ----------------
OBJ = re.compile(r"object \d+ \(local \d+, gfx \d+, at (\d+),(\d+),")
daily = {}
for m in maps:
    if I.unreleased(m["group"], m["num"]):
        continue
    for desc, entry in S.entry_points(m):
        hit = OBJ.match(desc)
        if not hit:
            continue
        x, y = int(hit[1]), int(hit[2])
        ins, _ = S.walk(entry)
        ins.sort()
        flags_seen = {S.u16_(a) for pc, op, a in ins if op in (0x29, 0x2B)}
        for k, (pc, op, a) in enumerate(ins):
            if op != 0x8F:
                continue
            spread, base, given = S.u16_(a), 0, False
            for pc2, op2, a2 in ins[k + 1:k + 6]:
                if op2 == 0x17 and S.u16_(a2) == 0x800D:
                    base += S.u16_(a2, 2)
                elif op2 == 0x1A and S.u16_(a2) == 0x8000 and S.u16_(a2, 2) == 0x800D:
                    given = True
                    break
            items = list(range(base, base + spread))
            if not given or not set(items) <= set(berries):
                continue
            if I.walled_in(m, x, y, itself=True):
                continue
            key = (m["group"], m["num"], x, y, pc)
            if key in daily:
                continue
            gx = key[:4]
            if gx not in DAILY_NOTES:
                problems.append("%s gives one of %s at random; no note in DAILY_NOTES: %s"
                                % (I.place(m), ", ".join(map(name, items)), S.summarise(entry)["text"][:2]))
                continue
            if not flags_seen & set(DAILY):
                problems.append("%s (%d,%d): a random berry with no daily flag; DAILY_NOTES says once a day"
                                % (I.place(m), x, y))
            daily[key] = {"kind": "daily", "place": I.place(m), "spot": "%d-%d-%d-%d" % gx, "how": DAILY_NOTES[gx],
                          "of": items}
for d in daily.values():
    for item in d["of"]:
        sources[item].append(d)

# ---------------- held by wild Pokemon ----------------
stats = T.table["base stats"]
wild_areas = defaultdict(set)
for a in R.load("wild.json"):
    for k in ("land", "water", "rock", "fishing"):
        for s in (a.get(k) or {}).get("slots", []):
            wild_areas[s["species_id"]].add(a["mapsec"])
held = defaultdict(list)
for sid in sorted(wild_areas):
    one, two = struct.unpack_from("<HH", rom, stats + 28 * sid + 12)
    for item, rate in ((one, "50%"), (two, "5%")):
        if item in berries and not (item == two and rate == "5%" and one == two):
            held[item].append({"sid": sid, "name": display_name(sid, species[str(sid)]),
                               "rate": "always" if one == two else rate})
for item, mons in held.items():
    seen, uniq = set(), []
    for x in mons:
        if (x["name"], x["rate"]) not in seen:
            seen.add((x["name"], x["rate"]))
            uniq.append(x)
    sources[item].append({"kind": "held", "mons": uniq})

# ---------------- out ----------------
out = []
for i in berries:
    if not sources[i]:
        problems.append("%s has no source at all" % name(i))
    kinds = {s["kind"]: n for n, s in enumerate(sources[i])}
    rank = {"tree": 0, "ball": 1, "hidden": 1, "gift": 2, "daily": 3, "shop": 4, "held": 5}
    out.append({"item": i, "no": number(i), "name": name(i), "emerald": i < FIRST_BERRY + EMERALD_BERRIES,
                "desc": text(R.u32(ITEMS + 44 * i + 20) - S.BASE),
                "sources": sorted(sources[i], key=lambda s: rank[s["kind"]])})
if problems:
    sys.exit("\n".join(problems))
json.dump({"berries": out, "trees": len(trees), "planted": len(planted),
           "copies": [{"item": i, "name": name(i)} for i in copies], "daily": list(daily.values()),
           "lists": {"%d" % i: name(i) for d in daily.values() for i in d["of"]}},
          open(os.path.join(DATA, "berries.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
kinds = defaultdict(int)
for b in out:
    for k in {s["kind"] for s in b["sources"]}:
        kinds[k] += 1
print("berries.json: %d berries (%d copies left out) | %d trees (%d ids planted at New Game) | berries from: %s"
      % (len(out), len(copies), len(trees), len(planted), ", ".join("%s %d" % kv for kv in sorted(kinds.items()))))
