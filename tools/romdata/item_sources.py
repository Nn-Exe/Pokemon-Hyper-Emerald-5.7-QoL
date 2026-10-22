"""Where items come from, read from every script a map can run. Shared by the guide's location tools
(tools/build_tm_locations.py, tools/build_mega_stones.py).

    import item_sources
    found, flags = item_sources.scan({item id, ...})

`found` maps (item, group, num, kind) to a source: its kind, its place name and what the kind adds.
  ball     finditem on an object: setorcopyvar 0x8000, <item>; setorcopyvar 0x8001, <n>; callstd 1. `spot` is
           "group-num-x-y", the tile it lies on, and names the picture tools/build_spot_maps.py draws of it.
           `flags` has the object's hide flag under the same key, so a caller can tell one pick-up that sits on
           two maps. An object walled in on all four sides is left out: nobody can face it (the fifteen spare
           Plates parked in the filler of Solaceon Ruins)
  unseen   the same on an object whose sprite has no pixel in it. None in v5.7: see sprite() before believing one
  given    giveitem: the same with callstd 0. `text` is the script's first lines, for whoever writes the note;
           `spot` too when an object gives it. A giver sealed inside solid tiles is left out as well
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
COUNTER = 0x80                                             # metatile behaviour: talk across it
GRAPHICS = 0x505620                                        # object graphics: a pointer to each id's info
EXTENDED, EXTENDED_ID = 0x39CF00, 0x4E                     # the hack's own sprites, 36 bytes of info each
OBJECT = re.compile(r"object (\d+) \(local \d+, gfx \d+, at (\d+),(\d+), flag ([0-9A-F]{4})\)")


def template(m, index):
    """The 24 bytes of a map's object: local id, graphics, -, extended graphics, x, y, ..., script, flag."""
    ev = int(m["events"], 16) - S.BASE
    o = R.u32(ev + 4) - S.BASE + 24 * index
    return rom[o:o + 24]


def sprite(gfx, ext):
    """Offset of the graphics info an object is drawn with, or None when the game decides at run time.

    Graphics 0x4E is not a sprite of its own in this hack: the routine at 0x094A2BCE sends it to the table at
    0x0839CF00, indexed by the template's fourth byte (vanilla leaves that byte unused). Every Mega Stone
    (0x18, a round stone), every TM lying about (0x3C, a ball of its own) and most of the hack's people use
    it. Read through the vanilla table alone, id 0x4E is an empty frame, which is how these were once taken for
    invisible."""
    if gfx == EXTENDED_ID:
        return EXTENDED + 36 * ext
    info = R.u32(GRAPHICS + 4 * gfx) if gfx < 240 else 0      # 240 and up are set by variables at run time
    return info - S.BASE if S.inrom(info) else None


def frame(gfx, ext, which=0):
    """(width, height, palette tag, 4bpp pixels) of one frame of an object's sprite, or None."""
    info = sprite(gfx, ext)
    if info is None or not S.inrom(R.u32(info + 0x1C)):
        return None
    images = R.u32(info + 0x1C) - S.BASE + 8 * which
    data, size = R.u32(images), R.u16(images + 4)
    if not S.inrom(data) or not size:
        return None
    return R.u16(info + 8), R.u16(info + 10), R.u16(info + 2), rom[data - S.BASE:data - S.BASE + size]


def blank(gfx, ext):
    """True for an object nobody can see: its sprite's first frame has no pixel in it."""
    f = frame(gfx, ext)
    return f is not None and not any(f[3])


def connected(m):
    """True for a map that other maps border (routes and towns); a room or a cave floor has only its warps."""
    links = R.u32(int(m["header"], 16) - S.BASE + 12)
    return S.inrom(links) and 0 < R.u32(links - S.BASE) < 64


def walled_in(m, x, y, itself=False):
    """True when nobody can face what is at x,y: none of the four tiles around it can be stood on, and none is a
    counter with a tile to stand on behind it. With `itself`, the tile has to be solid too: an object parked
    inside a wall, as the hack leaves a good many (plates in the filler of Solaceon Ruins, Lucas and X on a
    cliff face of Ever Grande City, Serena in a wall of a Rustboro flat)."""
    lay = int(m["layout"], 16) - S.BASE
    wide, high, data = R.u32(lay), R.u32(lay + 4), R.u32(lay + 12) - S.BASE

    def blocked(tx, ty):
        if not (0 <= tx < wide and 0 <= ty < high):
            return not connected(m)                        # a neighbouring map's tile: cannot tell, so not ruled out
        return R.u16(data + (ty * wide + tx) * 2) >> 10 & 3 != 0

    def counter(tx, ty):
        if not (0 <= tx < wide and 0 <= ty < high):
            return False
        tile = R.u16(data + (ty * wide + tx) * 2) & 0x3FF
        tileset = R.u32(lay + (16 if tile < 512 else 20)) - S.BASE
        return R.u16(R.u32(tileset + 0x10) - S.BASE + 2 * (tile % 512)) & 0xFF == COUNTER

    def open_side(dx, dy):
        return not blocked(x + dx, y + dy) or (counter(x + dx, y + dy) and not blocked(x + 2 * dx, y + 2 * dy))
    return not any(open_side(dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) and (not itself or blocked(x, y))


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
    (34, 75): "Rocket Hideout · under the Mauville Game Corner",
    (35, 25): "Champion Island · shop",
    # four islands share the name: each is the island of one Tapu's trial
    (35, 43): "Strange Island · Tapu Bulu's",
    (35, 44): "Strange Island · Tapu Koko's",
    (35, 46): "Strange Island · Tapu Lele's",
    (35, 47): "Strange Island · Tapu Fini's",
    (37, 82): "Oreburgh City · Gym",
    (37, 83): "Eterna City · Gym",
    (37, 84): "Hearthome City · Gym",
    (37, 89): "Canalave City · Gym",
    (37, 90): "Snowpoint City · Gym",
    (37, 91): "Pastoria City · Gym",
    (37, 92): "Sunyshore City · Gym",
    (37, 93): "Veilstone City · Gym",
    # rooms the hack added, named by the sign beside their door (Floaroma Town 36/4 at 17,34; Hearthome City 36/7
    # at 27,13); three Solaceon doors and one in the Moonbow Dome all lead into the same house
    (37, 10): "Floaroma Town · Pretty Petal Flower Shop",
    (37, 22): "Solaceon Town · house",
    (37, 100): "Hearthome City · Pokémon Contest Hall",
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
            spot, unseen, parked, sealed = {}, False, False, False
            if obj:
                x, y = int(obj.group(2)), int(obj.group(3))
                t = template(m, int(obj.group(1)))
                spot = {"spot": "%d-%d-%d-%d" % (m["group"], m["num"], x, y)}
                unseen, parked, sealed = blank(t[1], t[3]), walled_in(m, x, y), walled_in(m, x, y, itself=True)
            for k, (pc, op, a) in enumerate(ins):
                if op == 0x1A and S.u16_(a) == 0x8000 and S.u16_(a, 2) in wanted:
                    std = next((a2[0] for _, op2, a2 in ins[k + 1:k + 4] if op2 == 0x09), None)
                    if std == FIND and not parked:
                        key = add(S.u16_(a, 2), m, "unseen" if unseen else "ball", **spot)
                        if obj and obj.group(4) != "0000":
                            flags[key] = obj.group(4)
                    elif std == OBTAIN and not sealed:
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
