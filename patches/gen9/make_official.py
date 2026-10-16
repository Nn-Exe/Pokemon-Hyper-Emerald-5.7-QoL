"""Rebuild official.json: the official Scarlet/Violet data of the species gen9_patch.py adds, from PokeAPI.
usage: python make_official.py            (needs the network; not needed to build the ROM)

For each entry of gen9_data.SPECIES it fetches pokeapi.co/api/v2/pokemon/<key> and .../pokemon-species/<species>
and keeps what the patcher uses: base stats, types, EV yield, abilities (with which one is hidden), base
experience, height and weight, catch rate, base friendship, gender rate, growth rate, egg groups, hatch counter,
colour, genus, the Scarlet and Violet Pokedex texts, and the scarlet-violet move lists by method (level-up with
its level and order, machine, tutor, egg).
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen9_data as D

API = "https://pokeapi.co/api/v2/"
STAT = {"hp": "hp", "attack": "atk", "defense": "def", "special-attack": "spa", "special-defense": "spd", "speed": "spe"}
SPECIES_OF = {"ogerpon-wellspring-mask": "ogerpon", "ogerpon-hearthflame-mask": "ogerpon",
              "ogerpon-cornerstone-mask": "ogerpon", "terapagos-terastal": "terapagos"}


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "hyper-emerald-en-qol/gen9"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    out = {}
    for key, *_ in D.SPECIES:
        p = get("pokemon/" + key)
        s = get("pokemon-species/" + SPECIES_OF.get(key, key))
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
        out[key] = {
            "dex": s["id"], "types": [t["type"]["name"] for t in sorted(p["types"], key=lambda t: t["slot"])],
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
        print(key, out[key]["stats"], len(out[key]["levelup"]), "level-up moves")
    ordered = sorted(out.items(), key=lambda kv: (kv[1]["dex"], kv[0]))
    with open(os.path.join(HERE, "official.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n" + ",\n".join(" %s: %s" % (json.dumps(k), json.dumps(v, ensure_ascii=False, separators=(",", ":")))
                                    for k, v in ordered) + "\n}\n")
    print("wrote official.json: %d species" % len(out))


if __name__ == "__main__":
    main()
