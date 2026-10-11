"""Where items come from, read from every script a map can run. Shared by the guide's location tools
(tools/build_tm_locations.py, tools/build_mega_stones.py).

    import item_sources
    found, flags = item_sources.scan({item id, ...})

`found` maps (item, group, num, kind) to a source: its kind, its place name and what the kind adds.
  ball     finditem: setorcopyvar 0x8000, <item>; setorcopyvar 0x8001, <n>; callstd 1. `flags` has the object's
           hide flag under the same key, so a caller can tell one ball that sits on two maps
  unseen   a finditem whose object has a blank sprite: nothing shows on the map, the player has to face the
           tile and press A. The hack's author hid every Mega Stone and half the TMs this way, on object
           graphics 78 (256 item balls use 59, the ball; 130 pick-ups use 78). The Itemfinder does not see these.
           `spot` is "group-num-x-y", the tile, and names the picture tools/build_spot_maps.py draws of it
  given    giveitem: the same with callstd 0. `text` is the script's first lines, for whoever writes the note;
           `spot` too when the object that gives it cannot be seen
  prize    additem; `coins` from the removecoins before it (the Game Corner's counter)
  shop     a pokemart list; `price` from the item table
  hidden   a hidden-item bg event
  wild     setwildbattle with the item: the scripted Pokémon holds it (`species`, `level`)
A script that no map runs does not count; the ROM keeps many (item balls the hack's author moved, Prof. Elm's
reward for showing him the Kanto starters' Mega Stones, which nothing calls any more). Other callstds after a
0x8000 write are not items: callstd 8 registers a rematch and its number is a trainer's.

Places: pret's names for the maps vanilla Emerald has (map_names.json), the map section's name for the hack's own
maps, PLACES where neither says enough. Run dump_maps.py first if the ROM changed (it writes out/maps.json).
"""
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import romlib as R                                         # noqa: E402
import scripts as S                                        # noqa: E402

rom = R.rom
ITEMS = R.u32(0x1C8) - S.BASE                              # the item table: 44 bytes an item, price at +16
OBTAIN, FIND = 0, 1                                        # callstd numbers: giveitem, finditem
HIDDEN_ITEM = 7                                            # bg event kind
GRAPHICS = 0x505620                                        # object graphics: info pointers; +0x1C the frame table
OBJECT = re.compile(r"object \d+ \(local \d+, gfx (\d+), at (\d+),(\d+), flag ([0-9A-F]{4})\)")
_blank = {}


def blank(gfx):
    """True for object graphics whose first frame has no pixel in it: an object nobody can see."""
    if gfx not in _blank:
        _blank[gfx] = False
        info = R.u32(GRAPHICS + 4 * gfx) if gfx < 240 else 0        # 240 and up are set by variables at run time
        if S.inrom(info) and S.inrom(R.u32(info - S.BASE + 0x1C)):
            frames = R.u32(info - S.BASE + 0x1C) - S.BASE
            data, size = R.u32(frames), R.u16(frames + 4)
            _blank[gfx] = S.inrom(data) and size > 0 and not any(rom[data - S.BASE:data - S.BASE + size])
    return _blank[gfx]


def unreleased(group, num):
    """maps the release does not use (as UNRELEASED_TRAINERS in build_site_data.py)"""
    return (group == 37 and num >= 122) or (group == 34 and num >= 96)


def item_name(i):
    return R.decode(ITEMS + 44 * i, 14)[0]


def price(i):
    return R.u16(ITEMS + 44 * i + 16)


# ---------------- place names ----------------
VANILLA = json.load(open(os.path.join(HERE, "map_names.json"), encoding="utf-8"))["groups"]
SPLIT = re.compile(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z][a-z])|(?<=[A-Z])(?=[A-Z][a-z])")
WORDS = {"Pokemon": "Pokémon", "Mt": "Mt.", "SS": "S.S."}
POSSESSIVE = re.compile(r"\b(Brendan|May|Birch|Wally|Wanda|Steven|Scott|Cozmo|Cutter|Maniac|Master|Briney|Lanette)s\b")
PLACES = {
    (25, 42): "S.S. Tidal · lower deck",
    (25, 43): "S.S. Tidal · cabins",
    (0, 51): "Route 126 · underwater",
    (24, 103): "Marine Cave · the last room",
    (24, 105): "Terra Cave · the last room",
    (29, 1): "Trick House · the last room",
    # the hack's second Route 106 map lies west of Dewford Town; its cave has a door to a room on either side
    (34, 68): "Route 106 · west of Dewford Town",
    (34, 69): "Granite Cave · the cave west of Dewford Town",
    (34, 71): "Granite Cave · the cave west of Dewford Town, right-hand room",
    (34, 73): "Granite Cave · the cave west of Dewford Town, left-hand room",
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


# ---------------- the scan ----------------
def scan(wanted):
    found = {}            # (item, group, num, kind) -> source
    flags = {}            # the same key -> an item ball's object flag

    def add(item, m, kind, **extra):
        key = (item, m["group"], m["num"], kind)
        if key not in found:
            found[key] = dict(kind=kind, place=place(m), **extra)
        return key

    for m in R.load("maps.json"):
        if unreleased(m["group"], m["num"]):
            continue
        for src, sc in S.entry_points(m):
            ins, _ = S.walk(sc)
            ins.sort()
            obj = OBJECT.match(src)
            spot = {}
            if obj and blank(int(obj.group(1))):
                spot = {"spot": "%d-%d-%s-%s" % (m["group"], m["num"], obj.group(2), obj.group(3))}
            for k, (pc, op, a) in enumerate(ins):
                if op == 0x1A and S.u16_(a) == 0x8000 and S.u16_(a, 2) in wanted:
                    std = next((a2[0] for _, op2, a2 in ins[k + 1:k + 4] if op2 == 0x09), None)
                    if std == FIND:
                        key = add(S.u16_(a, 2), m, "unseen" if spot else "ball", **spot)
                        if obj and obj.group(4) != "0000":
                            flags[key] = obj.group(4)
                    elif std == OBTAIN:
                        add(S.u16_(a, 2), m, "given", text=S.summarise(sc)["text"][:3], **spot)
                elif op == 0x44 and S.u16_(a) in wanted:
                    coins = next((S.u16_(a2) for _, op2, a2 in reversed(ins[max(0, k - 8):k]) if op2 == 0xB5), None)
                    add(S.u16_(a), m, "prize", coins=coins)
                elif op == 0x86:
                    o, items = struct.unpack_from("<I", a)[0] - S.BASE, []
                    while R.u16(o) and len(items) < 200:
                        items.append(R.u16(o))
                        o += 2
                    for it in items:
                        if it in wanted:
                            add(it, m, "shop", price=price(it))
                elif op == 0xB6 and S.u16_(a, 3) in wanted:
                    add(S.u16_(a, 3), m, "wild", species=S.u16_(a), level=a[2])
        ev = int(m["events"], 16) - S.BASE if m.get("events") else 0
        if ev > 0 and S.inrom(R.u32(ev + 16)):
            for i in range(rom[ev + 3]):
                o = R.u32(ev + 16) - S.BASE + 12 * i
                if rom[o + 5] == HIDDEN_ITEM and R.u16(o + 8) in wanted:
                    add(R.u16(o + 8), m, "hidden")
    return found, flags
