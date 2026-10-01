"""Convert the ROM-mined tables (tools/romdata/*.py output) into the guide site's data files.

usage: python tools/build_site_data.py [<romdata_dir>]
writes site/src/data/{wild,trainers,static,species,items,forms}.json

Every Pokémon carries its species id (`sid`), every held item its item id and every trainer their picture id,
so the site can cut the right cell out of the sprite atlases (tools/build_sprites.py) without a name lookup.
Names go through tools/romdata/species_display.py and display_names.py: the ROM's own tables are cut to 10-13
characters and name every alternate form after its base species.
"""
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "romdata"))
from species_display import FORMS, display_name  # noqa: E402
from display_names import item_name, move_name  # noqa: E402

OUT = os.path.join(HERE, "..", "site", "src", "data")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "romdata", "out")
N_SPECIES = 1200


def load(name):
    return json.load(open(os.path.join(SRC, name), encoding="utf-8"))


def dump(name, obj):
    json.dump(obj, open(os.path.join(OUT, name), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))


species = load("species.json")
items = load("items.json")


def sp_name(sid, name):
    return display_name(sid, name)


def sp_id(sid):
    """the atlas cell: 0 (blank) for ids outside the species table"""
    return sid if 0 < sid < N_SPECIES else 0


def region_of(group):
    if group <= 33:
        return "hoenn"
    if group == 36:
        return "sinnoh"
    if group == 37:
        return "hisui"
    return "other"


def trainer_name(name):
    return "(untranslated name)" if name.startswith("{CN") else name


# ---------------- wild ----------------
raw = load("wild.json")
count = defaultdict(int)
for m in raw:
    count[m["mapsec"]] += 1
seen = defaultdict(int)
wild = []


def slot(s):
    return {"sid": sp_id(s["species_id"]), "species": sp_name(s["species_id"], s["species"]),
            "min": min(s["minLevel"], s["maxLevel"]), "max": max(s["minLevel"], s["maxLevel"]), "pct": s["slot%"]}


for m in raw:
    name = m["mapsec"] or "(unnamed area)"
    seen[name] += 1
    note = ""
    if count[name] > 1:
        note = "Area %d of %d" % (seen[name], count[name])

    def block(b):
        if not b or not b.get("slots"):
            return None
        return {"rate": b.get("encounterRate"), "slots": [slot(s) for s in b["slots"]]}

    fish = None
    if m.get("fishing") and m["fishing"].get("slots"):
        fish = {"rate": m["fishing"].get("encounterRate")}
        for rod in ("Old", "Good", "Super"):
            sl = [s for s in m["fishing"]["slots"] if s.get("rod") == rod]
            if sl:
                fish[rod.lower()] = {"slots": [slot(s) for s in sl]}
    wild.append({"map": name, "group": m["group"], "num": m["num"], "region": region_of(m["group"]),
                 "note": note, "land": block(m.get("land")), "water": block(m.get("water")),
                 "rock": block(m.get("rock")), "fish": fish})

order = {"hoenn": 0, "sinnoh": 1, "hisui": 2, "other": 3}
wild.sort(key=lambda w: (order[w["region"]], w["group"], w["num"]))

# ---------------- trainers ----------------
trainers = load("trainers.json")
battles = load("trainer_battles_by_map.json")
where = defaultdict(set)
for b in battles:
    mm = re.sub(r"^\d+/\d+ ", "", b["map"])
    if mm:
        where[b["trainer_id"]].add(mm)


# Items 754-767 are trainer-only copies of ordinary held items and have no icon of their own:
# show the icon of the item they copy.
_first_id = {}
for _k, _v in items.items():
    if 0 < int(_k) < 754:
        _first_id.setdefault(item_name(int(_k), _v["name"]), int(_k))


def icon_id(item_id, name):
    return _first_id.get(name, item_id) if item_id >= 754 else item_id


def party(t, full=True):
    out = []
    for p in t["party"]:
        e = {"sid": sp_id(p["species_id"]), "species": sp_name(p["species_id"], p["species"]), "level": p["level"]}
        if full and p.get("item_id"):
            e["item"] = item_name(p["item_id"], p["item"])
            e["itemId"] = icon_id(p["item_id"], e["item"])
        if full and p.get("moves"):
            e["moves"] = [move_name(mv) for mv in p["moves"] if mv and mv != "------------"]
        out.append(e)
    return out


def entry(t, label=None):
    lv = [p["level"] for p in t["party"]]
    base = {"id": t["id"], "cls": t["class"], "name": trainer_name(t["name"]), "label": label, "pic": t["pic"]}
    if t["id"] in PLACEHOLDER_IDS:
        base.update({"lv": [50, 50], "double": True,
                     "where": ", ".join(sorted(where.get(t["id"], []))) or "Sinnoh League", "party": [],
                     "tip": PLACEHOLDER_TIP})
        return base
    base.update({"lv": [min(lv), max(lv)] if lv else None, "double": bool(t.get("double")),
                 "where": ", ".join(sorted(where.get(t["id"], []))), "party": party(t)})
    return base


def by_name(names, classes=None):
    res = []
    for t in trainers:
        if t.get("invalid") or not t["party"]:
            continue
        if t["name"] in names and (t["class"] in classes if classes else t["class"] in BOSS_CLASSES):
            res.append(t)
    res.sort(key=lambda t: (names.index(t["name"]), max(p["level"] for p in t["party"]), t["id"]))
    return res


GROUPS = [
    ("hoenn-gyms", "Hoenn Gym Leaders",
     "In badge order. Rematch teams (higher levels) come from the post-game rematch system.",
     ["Roxanne", "Brawly", "Wattson", "Flannery", "Norman", "Winona", "Tate & Liza", "Juan"], ["Leader"]),
    ("hoenn-league", "Hoenn Elite Four & Champion", "Ever Grande City. Wallace is the Champion in this hack.",
     ["Sidney", "Phoebe", "Glacia", "Drake", "Wallace"], ["Elite Four", "Champion"]),
    ("rivals", "Rivals", "", ["May", "Brendan", "Wally"], None),
    ("aqua-magma", "Team Aqua & Team Magma", "",
     ["Archie", "Maxie", "Matt", "Shelly", "Tabitha", "Courtney"], None),
    ("steven", "Steven", "Former Champion; fought at Meteor Falls in the post-game and again on his island.",
     ["Steven"], None),
    ("sinnoh-gyms", "Sinnoh Gym Leaders",
     "All eight Sinnoh gyms are level-50 rules battles and can be taken in any order.",
     ["Roark", "Gardenia", "Maylene", "Wake", "Fantina", "Byron", "Candice", "Volkner"], None),
    ("sinnoh-league", "Sinnoh Elite Four & Champion", "", ["Aaron", "Bertha", "Flint", "Lucian", "Cynthia"], None),
    ("volo", "Lost Artifacts: Volo", "The final boss of the Hisui epilogue.", ["Volo"], None),
    ("villains", "Villain bosses", "Rainbow Rocket and the other evil-team leaders met in the post-game.",
     ["Giovanni", "Cyrus", "God Cyrus", "Ghetsis", "Lysandre", "Lusamine", "Faba", "Archer", "Ariana", "Petrel", "Proton",
      "Jupiter", "Mars", "Saturn", "Zinzolin", "Xerosic", "Malva", "Blaise", "Amber"], None),
    ("champions", "Champions & heroes from other regions",
     "Ultimate League, World Championship island and rematch bosses.",
     ["Red", "Leon", "Blue", "Lance", "Alder", "Iris", "Diantha", "Ash", "Serena", "N", "Paul", "Koga", "Zinnia",
      "Gold", "Ethan", "Kris", "Lyra", "Silver", "Lucas", "Dawn", "Barry", "Hilda", "Black", "Nate", "Rosa", "Hugh",
      "Bianca", "X", "Trace", "Chase", "Elaine", "Elio", "Selene", "Gladion", "Hala", "Olivia", "Nanu", "Hapu",
      "Victor", "Gloria", "Hop", "Marnie", "Bea", "Allister", "Avery", "Klara", "Larry", "Sapphire", "Riley", "Marley",
      "Jasmine", "Karen", "Lorelei", "Valerie", "Alain", "Wudan", "Yanshan", "Yolgz", "Demon Soul"], None),
    ("interpol", "International Police", "", ["Anabel"], ["PkMn Trainer"]),
]

# classes that mark a real story character rather than a route trainer who shares the name
BOSS_CLASSES = {"PkMn Trainer", "Champion", "Leader", "Elite Four", "Team Magma", "Team Rainbow", "Salon Maiden",
                "Dragon Tamer", "PkMn Tamer", "Lady", "PkMn Breeder♀", "Scientist", "TeamGalactic", "Team Plasma",
                "Team Flare", "Team Rocket", "Lorekeeper", "Magma Admin", "Aqua Admin", "Magma Leader", "Aqua Leader"}
PLACEHOLDER_IDS = {1131, 1132, 1133, 1134, 1135}
# Trainer slots that are not part of the published game: the site documents the public release only.
UNRELEASED_TRAINERS = {943, 947, 952}
trainers = [t for t in trainers if t["id"] not in UNRELEASED_TRAINERS]
PLACEHOLDER_TIP = ("The ROM's trainer table only holds a placeholder team for this battle; the hack builds the real "
                   "level-50 team when the fight starts (the League lobby monitor shows it before each match).")

groups = []
used = set()
for key, title, intro, names, classes in GROUPS:
    members = [entry(t) for t in by_name(names, classes)]
    members = [m for m in members if m["id"] not in used]
    for m in members:
        used.add(m["id"])
    if members:
        groups.append({"key": key, "title": title, "intro": intro, "trainers": members})

allt = []
for t in trainers:
    if t.get("invalid") or not t["party"]:
        continue
    allt.append({"id": t["id"], "cls": t["class"], "name": trainer_name(t["name"]), "pic": t["pic"],
                 "double": bool(t.get("double")), "where": ", ".join(sorted(where.get(t["id"], []))),
                 "party": party(t, full=False)})

# ---------------- static encounters ----------------
st = load("static_encounters.json")
uniq = {}
for s in st:
    mm = re.sub(r"^\d+/\d+ ", "", s["map"])
    g = int(s["map"].split("/")[0])
    if not 0 < s["species_id"] < N_SPECIES:
        continue                      # a script that sets a variable species; nothing to show
    key = (mm, s["species_id"], s["level"])
    if key in uniq:
        continue
    row = {"map": mm, "region": region_of(g), "sid": s["species_id"],
           "species": sp_name(s["species_id"], s["species"]), "level": s["level"]}
    if s.get("item_id"):
        row["item"] = item_name(s["item_id"], s["item"])
        row["itemId"] = icon_id(s["item_id"], row["item"])
    uniq[key] = row
static = sorted(uniq.values(), key=lambda s: (order[s["region"]], s["map"], -s["level"]))

# ---------------- name -> id tables for the guide pages ----------------
species_ids = {}
for k, v in species.items():
    sid = int(k)
    if 0 < sid < N_SPECIES:
        species_ids.setdefault(sp_name(sid, v), sid)     # the first (base) id wins a shared name
item_ids = {}
for k, v in items.items():
    iid = int(k)
    if 0 < iid < 769 and v["name"] not in ("------------", "??????"):
        item_ids.setdefault(item_name(iid, v["name"]), iid)

os.makedirs(OUT, exist_ok=True)
dump("wild.json", wild)
dump("trainers.json", {"groups": groups, "all": allt})
dump("static.json", static)
dump("species.json", species_ids)
dump("forms.json", sorted(FORMS))      # ids that are an alternate form of another species
dump("items.json", item_ids)
print("wild areas:", len(wild), "| boss groups:", len(groups), "with", sum(len(g["trainers"]) for g in groups),
      "entries | all trainers:", len(allt), "| static:", len(static), "| species names:", len(species_ids),
      "| item names:", len(item_ids))
