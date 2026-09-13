"""Convert the ROM-mined tables (tools/romdata/*.py output) into the guide site's data files.

usage: python tools/build_site_data.py <romdata_dir>
writes docs/data/wild.json, docs/data/trainers.json, docs/data/static.json
"""
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs", "data")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "romdata", "out")


def load(name):
    return json.load(open(os.path.join(SRC, name), encoding="utf-8"))


species = load("species.json")
base_names = {v for k, v in species.items() if int(k) < 994}


def sp_name(sid, name):
    if sid >= 994 and name in base_names:
        return name + " (alt. form)"
    if name.startswith("{CN"):
        return "(untranslated species #%d)" % sid
    return name


def region_of(group, mapsec):
    if group <= 33:
        return "hoenn"
    if group == 36:
        return "sinnoh"
    return "other"


# ---------------- wild ----------------
raw = load("wild.json")
count = defaultdict(int)
for m in raw:
    count[m["mapsec"]] += 1
seen = defaultdict(int)
wild = []
for m in raw:
    name = m["mapsec"] or "(unnamed area)"
    seen[name] += 1
    note = ""
    if count[name] > 1:
        note = "Area %d of %d (map %d/%d)" % (seen[name], count[name], m["group"], m["num"])
    if m["group"] == 37:
        note = (note + " · Hisui" if note else "Hisui")

    def block(b):
        if not b or not b.get("slots"):
            return None
        return {"rate": b.get("encounterRate"), "slots": [
            {"species": sp_name(s["species_id"], s["species"]), "min": min(s["minLevel"], s["maxLevel"]),
             "max": max(s["minLevel"], s["maxLevel"]), "pct": s["slot%"]} for s in b["slots"]]}

    fish = None
    if m.get("fishing") and m["fishing"].get("slots"):
        fish = {"rate": m["fishing"].get("encounterRate")}
        for rod in ("Old", "Good", "Super"):
            sl = [s for s in m["fishing"]["slots"] if s.get("rod") == rod]
            if sl:
                fish[rod.lower()] = {"slots": [
                    {"species": sp_name(s["species_id"], s["species"]), "min": min(s["minLevel"], s["maxLevel"]),
                     "max": max(s["minLevel"], s["maxLevel"]), "pct": s["slot%"]} for s in sl]}
    wild.append({"map": name, "group": m["group"], "num": m["num"], "region": region_of(m["group"], name),
                 "note": note, "land": block(m.get("land")), "water": block(m.get("water")),
                 "rock": block(m.get("rock")), "fish": fish})

order = {"hoenn": 0, "sinnoh": 1, "other": 2}
wild.sort(key=lambda w: (order[w["region"]], w["group"], w["num"]))

# ---------------- trainers ----------------
trainers = load("trainers.json")
battles = load("trainer_battles_by_map.json")
where = defaultdict(set)
for b in battles:
    mm = re.sub(r"^\d+/\d+ ", "", b["map"])
    if mm:
        where[b["trainer_id"]].add(mm)


def party(t):
    out = []
    for p in t["party"]:
        e = {"species": sp_name(p["species_id"], p["species"]), "level": p["level"]}
        if p.get("item_id"):
            e["item"] = p["item"]
        if p.get("moves"):
            e["moves"] = [mv for mv in p["moves"] if mv and mv != "------------"]
        out.append(e)
    return out


def entry(t, label=None):
    lv = [p["level"] for p in t["party"]]
    if t["id"] in PLACEHOLDER_IDS:
        return {"id": t["id"], "cls": t["class"], "name": t["name"], "label": label, "variant": "#%d · Lv 50 rules" % t["id"],
                "double": True, "where": ", ".join(sorted(where.get(t["id"], []))) or "Sinnoh League", "party": [],
                "tip": PLACEHOLDER_TIP}
    return {"id": t["id"], "cls": t["class"], "name": t["name"], "label": label,
            "variant": "#%d · Lv %d–%d" % (t["id"], min(lv), max(lv)) if lv else "#%d" % t["id"],
            "double": bool(t.get("double")), "where": ", ".join(sorted(where.get(t["id"], []))),
            "party": party(t)}


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
    ("Hoenn Gym Leaders", "In badge order. Rematch teams (higher levels) come from the post-game rematch system.",
     ["Roxanne", "Brawly", "Wattson", "Flannery", "Norman", "Winona", "Tate & Liza", "Juan"], ["Leader"]),
    ("Hoenn Elite Four & Champion", "Ever Grande City. Wallace is the Champion in this hack.",
     ["Sidney", "Phoebe", "Glacia", "Drake", "Wallace"], ["Elite Four", "Champion"]),
    ("Rivals", "", ["May", "Brendan", "Wally"], None),
    ("Team Aqua & Team Magma", "", ["Archie", "Maxie", "Matt", "Shelly", "Tabitha", "Courtney"], None),
    ("Steven", "Former Champion; fought at Meteor Falls in the post-game and again on his island.", ["Steven"], None),
    ("Sinnoh Gym Leaders", "All eight Sinnoh gyms are level-50 rules battles and can be taken in any order.",
     ["Roark", "Gardenia", "Maylene", "Wake", "Fantina", "Byron", "Candice", "Volkner"], None),
    ("Sinnoh Elite Four & Champion", "", ["Aaron", "Bertha", "Flint", "Lucian", "Cynthia"], None),
    ("Lost Artifacts: Volo", "The final boss of the Hisui epilogue.", ["Volo"], None),
    ("Villain bosses", "Rainbow Rocket and the other evil-team leaders met in the post-game.",
     ["Giovanni", "Cyrus", "Ghetsis", "Lysandre", "Lusamine", "Faba", "Archer", "Ariana", "Petrel", "Proton",
      "Jupiter", "Mars", "Saturn", "Zinzolin", "Xerosic", "Malva", "Blaise", "Amber"], None),
    ("Champions & heroes from other regions", "Ultimate League, World Championship island and rematch bosses.",
     ["Red", "Leon", "Blue", "Lance", "Alder", "Iris", "Diantha", "Ash", "Serena", "N", "Paul", "Koga", "Zinnia",
      "Gold", "Ethan", "Kris", "Lyra", "Silver", "Lucas", "Dawn", "Barry", "Hilda", "Black", "Nate", "Rosa", "Hugh",
      "Bianca", "X", "Trace", "Chase", "Elaine", "Elio", "Selene", "Gladion", "Hala", "Olivia", "Nanu", "Hapu",
      "Victor", "Gloria", "Hop", "Marnie", "Bea", "Allister", "Avery", "Klara", "Larry", "Sapphire", "Riley", "Marley",
      "Jasmine", "Karen", "Lorelei", "Valerie", "Alain", "Wudan", "Yanshan", "Yolgz", "Demon Soul"], None),
    ("International Police", "", ["Anabel"], ["PkMn Trainer"]),
]

# classes that mark a real story character rather than a route trainer who shares the name
BOSS_CLASSES = {"PkMn Trainer", "Champion", "Leader", "Elite Four", "Team Magma", "Team Rainbow", "Salon Maiden",
                "Dragon Tamer", "PkMn Tamer", "Lady", "PkMn Breeder♀", "Scientist", "TeamGalactic", "Team Plasma",
                "Team Flare", "Team Rocket", "Lorekeeper", "Magma Admin", "Aqua Admin", "Magma Leader", "Aqua Leader"}
PLACEHOLDER_IDS = {1131, 1132, 1133, 1134, 1135}
PLACEHOLDER_TIP = ("The ROM's trainer table only holds a placeholder team for this battle; the hack builds the real "
                   "level-50 team when the fight starts (the League lobby monitor shows it before each match).")

groups = []
used = set()
for title, intro, names, classes in GROUPS:
    members = [entry(t) for t in by_name(names, classes)]
    members = [m for m in members if m["id"] not in used]
    for m in members:
        used.add(m["id"])
    if members:
        groups.append({"title": title, "intro": intro, "trainers": members})

allt = []
for t in trainers:
    if t.get("invalid") or not t["party"]:
        continue
    name = t["name"] if not t["name"].startswith("{CN") else "(untranslated name)"
    allt.append({"cls": t["class"], "name": name, "party": [{"species": p["species"], "level": p["level"]} for p in party(t)]})

# ---------------- static encounters ----------------
st = load("static_encounters.json")
uniq = {}
for s in st:
    mm = re.sub(r"^\d+/\d+ ", "", s["map"])
    g = int(s["map"].split("/")[0])
    key = (mm, s["species"], s["level"])
    if key in uniq:
        continue
    uniq[key] = {"map": mm, "region": region_of(g, mm), "species": sp_name(s["species_id"], s["species"]),
                 "level": s["level"], "item": s["item"] if s.get("item_id") else ""}
static = sorted(uniq.values(), key=lambda s: (order[s["region"]], s["map"], -s["level"]))

os.makedirs(DOCS, exist_ok=True)
json.dump(wild, open(os.path.join(DOCS, "wild.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump({"groups": groups, "all": allt}, open(os.path.join(DOCS, "trainers.json"), "w", encoding="utf-8"),
          ensure_ascii=False, separators=(",", ":"))
json.dump(static, open(os.path.join(DOCS, "static.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("wild areas:", len(wild), "| boss groups:", len(groups), "with", sum(len(g["trainers"]) for g in groups),
      "entries | all trainers:", len(allt), "| static:", len(static))
