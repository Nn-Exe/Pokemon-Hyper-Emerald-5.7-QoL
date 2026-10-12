"""Where every Mega Stone is found, for the guide's Mega Stones list.

usage: HE_ROM=<patched rom> python tools/build_mega_stones.py
writes site/src/data/megastones.json; run tools/romdata/dump_tables.py and dump_maps.py first if the ROM changed
(tools/romdata/out/species.json and maps.json).

The stones are the items the evolution table asks for (0x08F387C0: method 251 is a Mega Evolution by held item,
253 a Primal Reversion), in National Dex order of the Pokémon. tools/romdata/item_sources.py finds what hands each
one over and names the place; each comes with its tile, which tools/build_spot_maps.py draws (a stone lies on
the ground as a small round stone: extended sprite 0x18). How a gift is earned is in NOTES, written from the script's dialogue: the build
stops on a gift without a note and on a stone without a source. The Wishing Piece is left out, as in forms.py: it
has a row for Charizard and nothing in the game gives it.
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "romdata"))
import romlib as R                                         # noqa: E402
import forms as F                                          # noqa: E402
import item_sources as I                                   # noqa: E402
from display_names import item_name                        # noqa: E402
from species_display import display_name                  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
rom = R.rom
DATA = os.path.join(HERE, "..", "site", "src", "data")
MEGA, PRIMAL = 251, 253

# (stone, group, num): how the gift is earned
NOTES = {
    ("Flygonite", 35, 53): "Touch the sealed Flygon and battle it (Lv 70): it vanishes and leaves the stone behind.",
    ("Metagrossite", 24, 107): "Steven, after you battle him here once New Team Magma is dealt with.",
    ("Blue Orb", 24, 103): "Archie leaves it behind when you beat him in front of Kyogre.",   # the orb object in
    ("Red Orb", 24, 105): "Maxie leaves it behind when you beat him in front of Groudon.",    # each room is walled in
    ("Final Meteor", 24, 85): "Zinnia, once Rayquaza has chosen you at the top of the Sky Pillar. Rayquaza also "
                              "Mega Evolves without it, if it knows Dragon Ascent.",
}

species = R.load("species.json")


def mon(sid):
    return display_name(sid, species[str(sid)])


def stone(i):
    return item_name(i, I.item_name(i))


# ---------------- the stones ----------------
stones = {}             # item -> [(species, form it turns into, method)]
for sid in range(1, F.NSPECIES):
    o, n = (F.EEVEE_EVOS, 10) if sid == F.EEVEE else (F.EVOS + 40 * sid, 5)
    for k in range(n):
        method, item, to, _ = struct.unpack_from("<HHHH", rom, o + 8 * k)
        if method & 0xFF in (MEGA, PRIMAL) and 0 < item < 800 and 0 < to < F.NSPECIES and item != F.WISHING_PIECE:
            stones.setdefault(item, [])
            if (sid, to, method & 0xFF) not in stones[item] and not any(t == to for _, t, _ in stones[item]):
                stones[item].append((sid, to, method & 0xFF))

found, flags = I.scan(set(stones))

# ---------------- what each source says ----------------
ORDER = {"gift": 0, "ball": 1, "unseen": 2, "hidden": 3, "wild": 4}
problems, used = [], set()
for (item, g, n, kind), s in found.items():
    if kind == "given":
        note = NOTES.get((stone(item), g, n))
        if not note:
            problems.append("%s at %s (%d/%d) is a gift with no note in NOTES; its script says:\n      %s"
                            % (stone(item), s["place"], g, n, "\n      ".join(t[:160] for t in s["text"])))
            continue
        used.add((stone(item), g, n))
        del s["text"]
        s["kind"], s["how"] = "gift", note
    elif kind == "wild":
        s["how"] = "Held by the Lv %d %s you battle here." % (s.pop("level"), mon(s.pop("species")))
    elif kind not in ORDER:
        problems.append("%s at %s: a %r source this list has no words for" % (stone(item), s["place"], kind))
for key, flag in flags.items():
    twins = [found[k]["place"] for k, f in flags.items() if f == flag and k[0] == key[0] and k != key]
    if twins:
        found[key]["how"] = "The same item as at %s: once it is picked up in one place, it is gone from both." \
                            % " and ".join(twins)
for k in sorted(set(NOTES) - used):
    print("note not used (the ROM has no such gift any more): %s %d/%d" % k)

out = []
for item in sorted(stones, key=lambda i: (F.natdex(rom, stones[i][0][0]), i)):
    srcs = sorted((s for (it, *_), s in found.items() if it == item and s["kind"] in ORDER),
                  key=lambda s: (ORDER[s["kind"]], s["place"]))
    if not srcs:
        problems.append("%s has no source at all" % stone(item))
    out.append({"item": item, "name": stone(item), "primal": stones[item][0][2] == PRIMAL,
                "mons": [{"sid": sid, "to": to} for sid, to, _ in stones[item]], "sources": srcs})

if problems:
    sys.exit("\n".join(problems))
json.dump(out, open(os.path.join(DATA, "megastones.json"), "w", encoding="utf-8"), ensure_ascii=False,
          separators=(",", ":"))
count = {}
for t in out:
    for s in t["sources"]:
        count[s["kind"]] = count.get(s["kind"], 0) + 1
print("megastones.json: %d stones and orbs, %d sources (%s)" % (len(out), sum(count.values()),
      ", ".join("%d %s" % (count[k], k) for k in sorted(count, key=ORDER.get))))
