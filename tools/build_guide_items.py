"""The Z-Crystals and the Plates, for the guide's Mega Stones & Key Items page.

usage: HE_ROM=<the release's rom> python tools/build_guide_items.py
writes site/src/data/guide-items.json; run tools/romdata/dump_tables.py and dump_maps.py first if the ROM changed.

Z-Crystals of the eighteen types: each is held by a Totem Pokémon, a scripted Lv 80 battle (setwildbattle with the
crystal) on a trigger of one of the 24 secret-base rooms (map group 25). A room is entered from the secret-base
spots of the routes: bg events of kind 8, whose id picks the room through the table at 0x0858CFE8 (four bytes a
group of ten ids, the first the room's map number). So each crystal lists its Totem and every spot that leads
to it. The other Z-Crystals and the Plates are found or given like any item: tools/romdata/item_sources.py finds
them, and NOTES says how a gift is earned, written from the script's dialogue (the build stops on a gift without
a note).

What the Totem scripts say, for the guide's text: nothing happens until flag 0x419D is set (Anabel, Steven's
Island, when you report back from the first Ultra Wormhole journey); Wishiwashi's room then asks "Want to battle
the Totem?", and winning sets 0x41A2, which the other seventeen wait for. The routine at 0x094A224C refuses the
battle ("Can't use some moves!") while a Pokémon in the party knows Destiny Bond, Perish Song, Pain Split or
Leech Seed. A win (battle outcome 1) hands the crystal over with finditem and sets the Totem's own flag; Selene
(Steven's Island 34/42) clears that flag again when the crystal is not in the Bag.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "romdata"))
import romlib as R                                         # noqa: E402
import item_sources as I                                   # noqa: E402
from display_names import item_name                        # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
rom = R.rom
DATA = os.path.join(HERE, "..", "site", "src", "data")
ROOMS = 25                                                 # the map group of the secret-base rooms
ROOM_OF = 0x58CFE8                                         # secret-base id // 10 -> {room's map number, -, x, y}
SECRET_BASE = 8                                            # bg event kind

# (item, group, num): (kind, how it is earned[, a place to print instead of the map's name])
NOTES = {
    ("Waterium Z", 34, 42): ("gift", "Selene hands it over if you beat the Totem and the crystal is not in your Bag."),
    ("Necrozium Z", 34, 94): ("gift", "Yours when Giovanni is beaten here and Necrozma's ritual is stopped."),
    ("Greninjium Z", 35, 8): ("gift", "ChipApartment, one of the hack's developers."),
    ("Kommonium Z", 35, 47): ("gift", "Hapu, once Tapu Fini has recognised you."),
    ("Lycanium Z", 35, 46): ("gift", "Olivia, once Tapu Lele has recognised you."),
    ("Aloraichium Z", 35, 44): ("gift", "Hala, once Tapu Koko has recognised you."),
    ("Solganium Z", 35, 44): ("gift", "Tapu Koko's final trial: yours after the battle with it (Lv 50), however it ends."),
    ("Lunalium Z", 35, 47): ("gift", "Tapu Fini's final trial: yours after the battle with it (Lv 50), however it ends."),
    ("Mewnium Z", 35, 46): ("gift", "Tapu Lele's final trial: yours after the battle with it (Lv 50), however it ends."),
    ("Mewnium Z", 26, 0): ("gift", "The same trial, where Tapu Lele stands in the Safari Zone."),
    ("Marshadium Z", 35, 43): ("gift", "Tapu Bulu's final trial: yours after the battle with it (Lv 50), however it ends."),
    ("Pikanium Z", 35, 41): ("trade", "Prof. Oak splits the Special Gem into this and the Eevium Z."),
    ("Eevium Z", 35, 41): ("trade", "Prof. Oak splits the Special Gem into the Pikanium Z and this."),
    ("Pikanium Z", 37, 13): ("trade", "Prof. Oak again, if he has not split the Special Gem yet."),
    ("Eevium Z", 37, 13): ("trade", "Prof. Oak again, if he has not split the Special Gem yet."),
    ("Pikanium Z", 37, 5): ("trade", "A researcher splits the Special Gem with a machine, into this and the Eevium Z."),
    ("Eevium Z", 37, 5): ("trade", "A researcher splits the Special Gem with a machine, into the Pikanium Z and this."),
    ("Pikashunium Z", 26, 40): ("gift", "Ash, after you beat him."),
    ("Decidium Z", 35, 41): ("gift", "Prof. Kukui, once Nanu has given you the Z-Power Ring."),
    ("Incinium Z", 35, 41): ("gift", "Prof. Kukui, once Nanu has given you the Z-Power Ring."),
    ("Primarium Z", 35, 41): ("gift", "Prof. Kukui, once Nanu has given you the Z-Power Ring."),
    ("Tapunium Z", 35, 40): ("gift", "Nanu, once every Tapu has recognised you."),
    ("Icicle Plate", 37, 94): ("gift", "A man sheltering from the blizzard dug it out of the snow long ago.",
                               "Route 217 · the hut"),
    ("Blank Plate", 37, 108): ("gift", "Beat Volo at the end of the Hisui story."),
    ("Legend Plate", 37, 108): ("gift", "Arceus, right after Volo: the eighteen plates become one."),
}

species = R.load("species.json")


def name(i):
    return item_name(i, I.item_name(i))


crystals = [i for i in range(1, 800) if re.search(r"[a-z]um ?Z$", I.item_name(i))]
plates = [i for i in range(1, 800) if I.item_name(i).endswith(" Plate")]
found, flags = I.scan(set(crystals) | set(plates))

# ---------------- the Totems ----------------
by_map = {(m["group"], m["num"]): m for m in R.load("maps.json")}
entrances = {}                # room's map number -> [(place, spot)]
for m in by_map.values():
    ev = int(m["events"], 16) - I.S.BASE if m.get("events") else 0
    if ev <= 0 or not I.S.inrom(R.u32(ev + 16)):
        continue
    for i in range(rom[ev + 3]):
        o = R.u32(ev + 16) - I.S.BASE + 12 * i
        if rom[o + 5] == SECRET_BASE:
            room = rom[ROOM_OF + 4 * (R.u32(o + 8) // 10)]
            entrances.setdefault(room, []).append(
                {"place": I.place(m), "spot": "%d-%d-%d-%d" % (m["group"], m["num"], R.u16(o), R.u16(o + 2))})

problems, totems, totem_keys = [], [], set()
for (item, g, n, kind), s in found.items():
    if kind == "wild" and g == ROOMS:
        totem_keys.add((item, g, n, kind))
        ways = sorted(entrances.get(n, []), key=lambda e: [int(v) for v in e["spot"].split("-")])
        if not ways:
            problems.append("%s: no secret-base spot leads to room %d/%d" % (name(item), g, n))
        totems.append({"item": item, "name": name(item), "sid": s["species"], "level": s["level"], "entrances": ways})
totems.sort(key=lambda t: t["item"])

# ---------------- everything else: found or given ----------------
ORDER = {"gift": 0, "trade": 1, "ball": 2, "unseen": 3, "hidden": 4, "wild": 5}
used = set()


def sources(item):
    out = []
    for key, s in found.items():
        it, g, n, kind = key
        if it != item or key in totem_keys:
            continue
        s = dict(s)
        if kind in ("given", "prize"):
            note = NOTES.get((name(item), g, n))
            if not note:
                problems.append("%s at %s (%d/%d) is given with no note in NOTES; its script says:\n      %s"
                                % (name(item), s["place"], g, n, "\n      ".join(t[:160] for t in s.get("text", []))))
                continue
            used.add((name(item), g, n))
            s = {"kind": note[0], "place": note[2] if len(note) > 2 else s["place"], "how": note[1]}
        elif kind not in ORDER:
            problems.append("%s at %s: a %r source this list has no words for" % (name(item), s["place"], kind))
            continue
        out.append(s)
    return sorted(out, key=lambda s: (ORDER[s["kind"]], s["place"]))


typed = {t["item"] for t in totems}
for t in totems:
    t["also"] = sources(t["item"])               # a second way to a Totem's crystal, where the game has one
others = [{"item": i, "name": name(i), "sources": sources(i)} for i in crystals if i not in typed]
plate_rows = [{"item": i, "name": name(i), "sources": sources(i)} for i in plates]
for row in others + plate_rows:
    if not row["sources"]:
        problems.append("%s has no source at all" % row["name"])
# two items one object hands over together (the Dread and Iron Plates): say so on both
for row in plate_rows + others:
    for s in row["sources"]:
        if "spot" in s:
            mates = [r["name"] for r in plate_rows + others
                     if r is not row and any(x.get("spot") == s["spot"] for x in r["sources"])]
            if mates:
                s["how"] = "Together with the %s." % " and the ".join(mates)
for k in sorted(set(NOTES) - used):
    print("note not used (the ROM has no such gift any more): %s %d/%d" % k)

if len(totems) != 18:
    problems.append("%d Totems found, not 18" % len(totems))
if problems:
    sys.exit("\n".join(problems))
json.dump({"totems": totems, "crystals": others, "plates": plate_rows},
          open(os.path.join(DATA, "guide-items.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("guide-items.json: %d Totems with %d ways in, %d other Z-Crystals, %d Plates"
      % (len(totems), sum(len(t["entrances"]) for t in totems), len(others), len(plate_rows)))
