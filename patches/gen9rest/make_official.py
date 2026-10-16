"""Rebuild official.json and moves.json for gen9rest: the official Scarlet/Violet data of the Pokemon gen9rest adds,
and of every Scarlet/Violet move they learn, from PokeAPI.
usage: python make_official.py            (needs the network; not needed to build the ROM)

Species: as gen9/make_official.py (base stats, types, EV yield, abilities with the hidden one, base experience,
height, weight, catch rate, friendship, gender rate, growth rate, egg groups, hatch counter, colour, genus, the
Scarlet and Violet Pokedex texts, the scarlet-violet move lists by method). A key that is a species name takes
that species' default form; a form key (wooper-paldea...) is fetched as it is.
Moves: for each move any of them learns in Scarlet/Violet: type, power, accuracy, PP, priority, category, target,
the meta block (ailment, chances, drain, healing, hits, crit rate, flinch, stat changes) and the effect text.
Primeape, Girafarig, Dunsparce, Bisharp, Applin and Duraludon are fetched too (their evolution moves).
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen9rest_data as D

API = "https://pokeapi.co/api/v2/"
STAT = {"hp": "hp", "attack": "atk", "defense": "def", "special-attack": "spa", "special-defense": "spd", "speed": "spe"}


def get(path):
    for attempt in range(5):
        try:
            req = urllib.request.Request(API + path, headers={"User-Agent": "hyper-emerald-en-qol/gen9rest"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:                       # the API is busy now and then
            if attempt == 4:
                raise
            time.sleep(2 + 3 * attempt)


def species_entry(key, species_name):
    s = get("pokemon-species/" + species_name)
    pk = key if key != species_name else next(v["pokemon"]["name"] for v in s["varieties"] if v["is_default"])
    p = get("pokemon/" + pk)
    levelup, other = [], {"machine": [], "tutor": [], "egg": []}
    for m in p["moves"]:
        for d in m["version_group_details"]:
            if d["version_group"]["name"] != "scarlet-violet":
                continue
            how = d["move_learn_method"]["name"]
            if how == "level-up":
                levelup.append((d["level_learned_at"], d.get("order") or 0, m["move"]["name"]))
            elif how in other:
                other[how].append(m["move"]["name"])
    flavor = {}
    for f in s["flavor_text_entries"]:
        if f["language"]["name"] == "en" and f["version"]["name"] in ("scarlet", "violet"):
            flavor[f["version"]["name"]] = " ".join(f["flavor_text"].split())
    return {
        "pokemon": pk, "dex": s["id"],
        "types": [t["type"]["name"] for t in sorted(p["types"], key=lambda t: t["slot"])],
        "stats": {STAT[x["stat"]["name"]]: x["base_stat"] for x in p["stats"]},
        "ev": {STAT[x["stat"]["name"]]: x["effort"] for x in p["stats"] if x["effort"]},
        "abilities": [[a["ability"]["name"], a["is_hidden"]] for a in sorted(p["abilities"], key=lambda a: a["slot"])],
        "exp": p["base_experience"], "height": p["height"], "weight": p["weight"], "catch": s["capture_rate"],
        "friendship": s["base_happiness"], "gender_rate": s["gender_rate"], "growth": s["growth_rate"]["name"],
        "egg_groups": [g["name"] for g in s["egg_groups"]], "hatch": s["hatch_counter"], "color": s["color"]["name"],
        "genus": next(g["genus"] for g in s["genera"] if g["language"]["name"] == "en"), "flavor": flavor,
        "levelup": [[lv, name] for lv, _, name in sorted(levelup)],
        "machine": sorted(other["machine"]), "tutor": sorted(other["tutor"]), "egg": sorted(other["egg"]),
    }


def move_entry(name):
    m = get("move/" + name)
    meta = m.get("meta") or {}
    eff = next((e["short_effect"] for e in m["effect_entries"] if e["language"]["name"] == "en"), "")
    flav = [f["flavor_text"] for f in m["flavor_text_entries"]
            if f["language"]["name"] == "en" and f["version_group"]["name"] == "scarlet-violet"]
    return {
        "id": m["id"], "type": m["type"]["name"], "power": m["power"], "accuracy": m["accuracy"], "pp": m["pp"],
        "priority": m["priority"], "category": m["damage_class"]["name"], "target": m["target"]["name"],
        "generation": m["generation"]["name"],
        "ailment": (meta.get("ailment") or {}).get("name"), "ailment_chance": meta.get("ailment_chance"),
        "category_meta": (meta.get("category") or {}).get("name"), "crit_rate": meta.get("crit_rate"),
        "drain": meta.get("drain"), "healing": meta.get("healing"), "flinch": meta.get("flinch_chance"),
        "min_hits": meta.get("min_hits"), "max_hits": meta.get("max_hits"), "stat_chance": meta.get("stat_chance"),
        "stat_changes": [[s["stat"]["name"], s["change"]] for s in m.get("stat_changes", [])],
        "effect": " ".join(eff.split()), "text": " ".join(flav[0].split()) if flav else "",
    }


def main():
    out = {}
    keys = [(k, sp) for k, sp, *_ in D.SPECIES] + [(k, k) for k in D.EVOLVE_FROM_OLD]
    for key, sp in keys:
        out[key] = species_entry(key, sp)
        print(key, out[key]["pokemon"], out[key]["stats"], len(out[key]["levelup"]), "level-up moves", flush=True)
    with open(os.path.join(HERE, "official.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n" + ",\n".join(" %s: %s" % (json.dumps(k), json.dumps(v, ensure_ascii=False, separators=(",", ":")))
                                    for k, v in out.items()) + "\n}\n")
    names = sorted({mv for o in out.values() for mv in [m for _, m in o["levelup"]] + o["machine"] + o["tutor"] + o["egg"]})
    moves = {}
    for n in names:
        moves[n] = move_entry(n)
    with open(os.path.join(HERE, "moves.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n" + ",\n".join(" %s: %s" % (json.dumps(k), json.dumps(v, ensure_ascii=False, separators=(",", ":")))
                                    for k, v in moves.items()) + "\n}\n")
    print("wrote official.json: %d species; moves.json: %d moves" % (len(out), len(moves)))


if __name__ == "__main__":
    main()
