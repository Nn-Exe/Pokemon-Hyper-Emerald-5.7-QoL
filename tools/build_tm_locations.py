"""Where every TM and HM is found, for the guide's TMs & HMs page.

usage: HE_ROM=<patched rom> python tools/build_tm_locations.py
writes site/src/data/tms.json; run tools/build_pokedex.py first (it writes the TM list this reads), and
tools/romdata/dump_maps.py if the ROM changed (tools/romdata/out/maps.json).

It walks every script a map can run (tools/romdata/scripts.py: objects, triggers, signs and map scripts, through
their branches) and keeps whatever hands over a TM or HM:
  finditem / giveitem   setorcopyvar 0x8000, <item>; setorcopyvar 0x8001, <n>; callstd 1 (on the ground) or 0 (given)
  additem               the Game Corner's prizes, with the coins the removecoins before it takes
  pokemart              a shop's list, with the price from the item table
and the hidden items (bg events), though none of those is a TM in v5.7. A script that no map runs does not count:
the ROM keeps a few that hand out TMs the hack's author moved elsewhere.

Places: pret's names for the maps vanilla Emerald has (tools/romdata/map_names.json), the map section's name for
the hack's own maps, PLACES where neither says enough. How each gift is earned is in NOTES, written from the
script's dialogue: the build stops on a gift without a note, so a new ROM cannot slip one in unexplained.
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "romdata"))
import romlib as R                                         # noqa: E402
import scripts as S                                        # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
rom = R.rom
DATA = os.path.join(HERE, "..", "site", "src", "data")
ITEMS = R.u32(0x1C8) - S.BASE                              # the item table: 44 bytes an item, price at +16
OBTAIN, FIND = 0, 1                                        # callstd numbers: giveitem, finditem
HIDDEN_ITEM = 7                                            # bg event kind


def unreleased(group, num):
    """maps the release does not use (as UNRELEASED_TRAINERS in build_site_data.py)"""
    return (group == 37 and num >= 122) or (group == 34 and num >= 96)


# ---------------- place names ----------------
VANILLA = json.load(open(os.path.join(HERE, "romdata", "map_names.json"), encoding="utf-8"))["groups"]
SPLIT = re.compile(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z][a-z])|(?<=[A-Z])(?=[A-Z][a-z])")
WORDS = {"Pokemon": "Pokémon", "Mt": "Mt.", "SS": "S.S."}
POSSESSIVE = re.compile(r"\b(Brendan|May|Birch|Wally|Steven|Cozmo|Cutter|Maniac|Briney|Lanette)s\b")
PLACES = {
    (25, 43): "S.S. Tidal · cabins",
    (0, 51): "Route 126 · underwater",
    (29, 1): "Trick House · the last room",
    (35, 25): "Champion Island · shop",
    (37, 82): "Oreburgh City · Gym",
    (37, 83): "Eterna City · Gym",
    (37, 84): "Hearthome City · Gym",
    (37, 89): "Canalave City · Gym",
    (37, 90): "Snowpoint City · Gym",
    (37, 91): "Pastoria City · Gym",
    (37, 92): "Sunyshore City · Gym",
    (37, 93): "Veilstone City · Gym",
}


def words(part):
    return POSSESSIVE.sub(r"\1's", " ".join(WORDS.get(w, w) for w in SPLIT.sub(" ", part).split()))


def place(m):
    g, n = m["group"], m["num"]
    if (g, n) in PLACES:
        return PLACES[(g, n)]
    if g < len(VANILLA) and n < len(VANILLA[g]):
        first, *rest = VANILLA[g][n].split("_")
        name = words(first) + (" · " + " ".join(words(p) for p in rest) if rest else "")
        squash = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())            # noqa: E731
        if m["mapsec"] and squash(m["mapsec"]) not in squash(name):
            print("check: %d/%d is %r in vanilla but its map section is %r" % (g, n, name, m["mapsec"]))
        return name
    return m["mapsec"] or "%d/%d" % (g, n)


# ---------------- how each gift is earned (from the scripts' dialogue) ----------------
# (label, group, num): (kind, text). kind: gym (a Gym Leader's prize), gift, trade.
FAN_CLUB = "The Pokémon Fan Club Chairman’s younger brother, on holiday in a Pacifidlog house, gives it when the "
NOTES = {
    ("TM01", 7, 3): ("gift", FAN_CLUB + "first Pokémon in your party is unfriendly to you (friendship under 50). "
                             "One TM a day."),
    ("TM100", 7, 3): ("gift", FAN_CLUB + "first Pokémon in your party is very friendly (friendship 150 or more). "
                              "One TM a day."),
    ("TM06", 12, 5): ("gift", "An old woman hides a coin in one hand: guess right three times running "
                              "(Right, Right, Left)."),
    ("TM12", 0, 38): ("gift", "A girl who loves Grass types, if you have a Grass-type Pokémon with you."),
    ("TM13", 4, 1): ("gym", "Flannery’s prize for beating her."),
    ("TM15", 20, 0): ("gift", "The Fossil Maniac’s little brother."),
    ("TM16", 0, 29): ("gift", "A man whose Pokémon knows nothing but Screech."),
    ("TM21", 13, 13): ("gift", "A sleepy man in a house."),
    ("TM23", 9, 7): ("gift", "The Team Aqua Grunt you beat in Rusturf Tunnel, begging to be forgiven."),
    ("TM30", 24, 10): ("gift", "Steven, when you deliver the Letter to him."),
    ("TM31", 6, 0): ("gift", "A woman in the Battle Tent lobby."),
    ("TM36", 15, 0): ("gym", "Juan’s prize for beating him."),
    ("TM39", 8, 1): ("gym", "Norman’s prize for beating him."),
    ("TM41", 0, 19): ("gift", "Someone who wishes they had help at work."),
    ("TM42", 3, 3): ("gym", "Brawly’s prize for beating him."),
    ("TM43", 15, 5): ("gift", "A man who spent thirty years in Sootopolis perfecting it."),
    ("TM44", 14, 0): ("gym", "Tate and Liza’s prize for beating them."),
    ("TM45", 0, 26): ("gift", "Gladion, after you battle him by the tree where he was making a Secret Base."),
    ("TM47", 9, 2): ("gift", "A man in the Battle Tent lobby."),
    ("TM48", 11, 3): ("gym", "Roxanne’s prize for beating her."),
    ("TM52", 12, 1): ("gym", "Winona’s prize for beating her."),
    ("TM56", 3, 4): ("gift", "A trendy man in the hall, who cannot believe you do not know U-turn."),
    ("TM59", 25, 43): ("gift", "A nervous man in one of the cabins."),
    ("TM70", 29, 1): ("gift", "The Trick Master’s reward for the fifth puzzle."),
    ("TM78", 12, 7): ("gift", "A man whose Wingull brings it back from an errand."),
    ("TM79", 5, 6): ("trade", "Prof. Cozmo, for the Meteorite Team Magma took from Meteor Falls."),
    ("TM79", 37, 52): ("trade", "Tatara, for the same Meteorite, if you did not give it to Prof. Cozmo."),
    ("TM80", 0, 2): ("gift", "Wattson, once you have shut down the generator in New Mauville for him."),
    ("TM82", 10, 0): ("gym", "Wattson’s prize for beating him."),
    ("TM96", 0, 6): ("gift", "A boy near Steven’s house: say you want it."),
    ("TM103", 0, 8): ("gift", "Lucas, the Trainer from Sinnoh: beat him in his second practice battle."),
    ("TM103", 37, 91): ("gym", "Crasher Wake’s prize for beating him."),
    ("TM104", 37, 83): ("gym", "Gardenia’s prize for beating her."),
    ("TM105", 37, 92): ("gym", "Volkner’s prize for beating him."),
    ("TM106", 37, 93): ("gym", "Maylene’s prize for beating her."),
    ("TM109", 37, 82): ("gym", "Roark’s prize for beating him."),
    ("TM111", 37, 90): ("gym", "Candice’s prize for beating her."),
    ("TM113", 11, 15): ("gift", "Serena, who dances here: win her performance battle."),
    ("TM114", 37, 84): ("gym", "Fantina’s prize for beating her."),
    ("TM119", 0, 8): ("gift", "X, the Kalos Champion: beat him a second time."),
    ("TM119", 37, 89): ("gym", "Byron’s prize for beating him."),
    ("HM01", 11, 11): ("gift", "The Cutter, who can tell a skilled Trainer at a glance."),
    ("HM02", 0, 34): ("gift", "May or Brendan, after your battle on Route 119."),
    ("HM03", 8, 0): ("gift", "Wally’s father, after you have won Norman’s Balance Badge."),
    ("HM04", 24, 4): ("gift", "Wanda’s boyfriend, once you have smashed the boulder between them."),
    ("HM05", 24, 7): ("gift", "A Hiker at the entrance."),
    ("HM06", 10, 2): ("gift", "The Rock Smash Guy."),
    ("HM07", 0, 7): ("gift", "Wallace, after Groudon and Kyogre are calmed."),
    ("HM08", 14, 7): ("gift", "Steven, in his house, after you fight Team Magma beside him at the Space Center."),
}
# shops that sell TMs: (group, num) -> when it opens, if not from the start
SHOPS = {
    (13, 19): None,
    (35, 25): "after you beat Champion Cynthia",
}


# ---------------- what the ROM has ----------------
def item_name(i):
    return R.decode(ITEMS + 44 * i, 14)[0]


def price(i):
    return R.u16(ITEMS + 44 * i + 16)


machines = json.load(open(os.path.join(DATA, "pokedex.json"), encoding="utf-8"))["tm"]
item_of = {}
for i in range(1, 800):
    mm = re.fullmatch(r"(TM|HM) ?(\d+)", item_name(i))
    if mm:
        item_of.setdefault("%s%02d" % (mm.group(1), int(mm.group(2))), i)
label_of = {item_of[t["label"]]: t["label"] for t in machines}
assert len(label_of) == len(machines), "a TM or HM has no item"

found = {}            # (label, group, num, kind) -> source
flags = {}            # the same key -> an item ball's object flag


def add(label, m, kind, **extra):
    key = (label, m["group"], m["num"], kind)
    if key not in found:
        found[key] = dict(kind=kind, place=place(m), **extra)
    return key


maps = R.load("maps.json")
for m in maps:
    if unreleased(m["group"], m["num"]):
        continue
    for src, sc in S.entry_points(m):
        ins, _ = S.walk(sc)
        ins.sort()
        for k, (pc, op, a) in enumerate(ins):
            if op == 0x1A and S.u16_(a) == 0x8000 and S.u16_(a, 2) in label_of:
                std = next((a2[0] for _, op2, a2 in ins[k + 1:k + 4] if op2 == 0x09), None)
                if std == FIND:
                    key = add(label_of[S.u16_(a, 2)], m, "ball")
                    hit = re.search(r"flag ([0-9A-F]{4})", src)
                    if src.startswith("object") and hit and hit.group(1) != "0000":
                        flags[key] = hit.group(1)
                elif std == OBTAIN:
                    add(label_of[S.u16_(a, 2)], m, "given", text=S.summarise(sc)["text"][:3])
                # other callstds after a 0x8000 write are not items (trainer ids, say)
            elif op == 0x44 and S.u16_(a) in label_of:
                coins = next((S.u16_(a2) for _, op2, a2 in reversed(ins[max(0, k - 8):k]) if op2 == 0xB5), None)
                add(label_of[S.u16_(a)], m, "prize", coins=coins)
            elif op == 0x86:
                o, items = struct.unpack_from("<I", a)[0] - S.BASE, []
                while R.u16(o) and len(items) < 200:
                    items.append(R.u16(o))
                    o += 2
                for it in items:
                    if it in label_of:
                        add(label_of[it], m, "shop", price=price(it))
    ev = int(m["events"], 16) - S.BASE if m.get("events") else 0
    if ev > 0 and S.inrom(R.u32(ev + 16)):
        for i in range(rom[ev + 3]):
            o = R.u32(ev + 16) - S.BASE + 12 * i
            if rom[o + 5] == HIDDEN_ITEM and R.u16(o + 8) in label_of:
                add(label_of[R.u16(o + 8)], m, "hidden")

# ---------------- what each source says ----------------
problems, used = [], set()
for (label, g, n, kind), s in found.items():
    if kind == "given":
        note = NOTES.get((label, g, n))
        if not note:
            problems.append("%s at %s (%d/%d) is a gift with no note in NOTES; its script says:\n      %s"
                            % (label, s["place"], g, n, "\n      ".join(t[:160] for t in s["text"])))
            continue
        used.add((label, g, n))
        del s["text"]
        s["kind"], s["how"] = note
    elif kind == "shop":
        if (g, n) not in SHOPS:
            problems.append("%s is sold at %s (%d/%d), a shop missing from SHOPS" % (label, s["place"], g, n))
        if SHOPS.get((g, n)):
            s["how"] = SHOPS[(g, n)]
    elif kind == "prize" and s.get("coins"):
        s["how"] = "A Game Corner prize."
# one ball on two maps: an object flag both share is set by whichever is picked up
for key, flag in flags.items():
    twins = [found[k]["place"] for k, f in flags.items() if f == flag and k[0] == key[0] and k != key]
    if twins:
        found[key]["how"] = "The same ball as at %s: once it is picked up in one place, it is gone from both." \
                            % " and ".join(twins)
for k in sorted(set(NOTES) - used):
    print("note not used (the ROM has no such gift any more): %s %d/%d" % k)

# free before bought, and a shop that is open from the start before one that is not
ORDER = {"gym": 0, "gift": 1, "trade": 2, "ball": 3, "hidden": 4, "prize": 5, "shop": 6}
out = []
for t in machines:
    srcs = sorted((s for (label, *_), s in found.items() if label == t["label"] and s["kind"] in ORDER),
                  key=lambda s: (ORDER[s["kind"]], s["kind"] == "shop" and "how" in s, s["place"]))
    if not srcs:
        problems.append("%s (%s) has no source at all" % (t["label"], item_name(item_of[t["label"]])))
    out.append({"label": t["label"], "item": item_of[t["label"]], "sources": srcs})

if problems:
    sys.exit("\n".join(problems))
json.dump(out, open(os.path.join(DATA, "tms.json"), "w", encoding="utf-8"), ensure_ascii=False,
          separators=(",", ":"))
count = {}
for t in out:
    for s in t["sources"]:
        count[s["kind"]] = count.get(s["kind"], 0) + 1
print("tms.json: %d TMs and HMs, %d sources (%s)" % (len(out), sum(count.values()),
      ", ".join("%d %s" % (count[k], k) for k in sorted(count, key=ORDER.get))))
