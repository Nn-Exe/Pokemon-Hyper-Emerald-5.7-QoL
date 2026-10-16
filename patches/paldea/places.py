"""Where everybody and everything of Area Zero stands, kept in a text file anyone can edit.

The user, on test 10: "actually can I edit the placement myself???". So no position of a person, a Pokemon, a
crystal or an item is written in the patch any more: paldea_patch.py takes them all from load(), which reads
the placements file named on the command line (the user's own is beside the test builds) and fills in whatever
it leaves out from THINGS below; with no file named, THINGS is all there is. check.py then refuses a build in which something stands in a wall, on top of something else or in
the way. Tiles are the map's own: the numbers along the edges of the pictures map_guide.py draws.

What is NOT in here is part of the ground and stays in world.py and in the rooms the game already has: doors,
cave mouths, stairs, the lab's machine and terminals, the stations' cot and PC.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))

# The file's sections, and which maps each is about (map keys as paldea_patch.py names them; "mossdeep" is the
# game's own Mossdeep City, 0/6).
SECTIONS = [
    ("mossdeep", "Mossdeep City", ["mossdeep"]),
    ("crater", "crater, both times", ["past", "future"]),
    ("past", "crater, past only", ["past"]),
    ("future", "crater, future only", ["future"]),
    ("stations", "research stations", ["station1", "station2", "station3", "station4"]),
    ("cavern", "Crystal Cavern", ["cavern"]),
    ("vault", "Sealed Vault", ["vault"]),
    ("icecave", "icy cave", ["icecave"]),
    ("lab", "Zero Lab", ["lab"]),
    ("underdepths", "Underdepths", ["underdepths"]),
]
MAPS_OF = {key: maps for key, title, maps in SECTIONS}
TITLE_OF = {key: title for key, title, maps in SECTIONS}

# Sprite sizes by kind: what the game's reflection rule and the picture tools need.
SIZE = {"person": (16, 32), "mon": (32, 32), "big": (64, 64), "crystal": (16, 32), "hole": (32, 32),
        "recorder": (16, 32), "note": (16, 16), "ball": (16, 16), "stake": (16, 32), "tablet": (32, 32),
        "sign": (16, 16), "rift": (32, 32)}

# When a thing is on the map: "story" until the finale, "after" from then on, "always" both; "finale" and "ending"
# are the two scenes (nobody walks round them). Two things may share a tile if they are never there together
# (the Titan and the legend that takes its den afterwards).
WHEN = {"story": {"story"}, "after": {"after"}, "always": {"story", "after"}, "finale": {"finale"},
        "ending": {"ending"}}

# id, section, name in the file, kind, when, where it stands unless the file says otherwise, a note for the file.
# A list of tiles makes a group (the crystals): any number of them.
THINGS = [
    # Mossdeep City (test 16): the strip of grass by the sea below the Space Center, where the user stood ("at where
    # I stand"); 69,32 is an item ball of the game's until it is picked up.
    ("jacq", "mossdeep", "Jacq", "person", "story", (70, 32), "until the ending; then he is in Research Station No. 4"),
    ("hole", "mossdeep", "black hole", "hole", "always", (68, 32), "you come back out on the tile below it"),
    ("end_penny", "mossdeep", "ending: Penny", "person", "ending", (67, 33), "only while the ending plays"),
    ("end_arven", "mossdeep", "ending: Arven", "person", "ending", (69, 33), ""),
    ("end_nemona", "mossdeep", "ending: Nemona", "person", "ending", (70, 33), ""),

    ("arven", "crater", "Arven", "person", "story", (37, 43), "his picnic, by the lake"),
    ("legend", "crater", "Koraidon / Miraidon", "big", "always", (39, 42),
     "Koraidon in the past, Miraidon in the future"),
    ("titan", "crater", "Titan", "mon", "story", (8, 34), "Great Tusk in the past, Iron Treads in the future"),
    ("guard_arven", "crater", "Arven at the lab's door", "person", "story", (43, 15),
     "once everything before the finale is done"),
    ("guard_nemona", "crater", "Nemona at the lab's door", "person", "story", (45, 15), ""),
    # (the two were "time crystal 1 / 2" and drawn as a pale crystal up to 2026-10-11: ALIASES reads the old names)
    ("time1", "crater", "time rift 1", "rift", "always", (26, 30), "takes you to the same tile in the other time"),
    ("time2", "crater", "time rift 2", "rift", "always", (45, 20), ""),
    ("crystals", "crater", "crystals", "crystal", "always",
     [(5, 34), (11, 34), (24, 31), (29, 31), (29, 21), (11, 18), (19, 37), (46, 21), (36, 34), (20, 23), (36, 39),
      (46, 38), (5, 42), (24, 4), (40, 9), (36, 7)], "red in the past, dark in the future"),

    ("walking_wake", "past", "Walking Wake", "mon", "after", (33, 7),
     "on the river above the waterfall: you surf up to it"),
    ("gouging_fire", "past", "Gouging Fire", "mon", "after", (8, 34), "the den, once the Titan is gone"),
    ("raging_bolt", "past", "Raging Bolt", "big", "after", (32, 32), ""),
    ("booster_past", "past", "item ball", "ball", "always", (4, 28), "Booster Energy"),

    ("nemona", "future", "Nemona", "person", "story", (36, 27), "until she is beaten and everyone is ready"),
    ("iron_leaves", "future", "Iron Leaves", "mon", "after", (30, 21), ""),
    ("iron_boulder", "future", "Iron Boulder", "mon", "after", (8, 34), "the den, once the Titan is gone"),
    ("iron_crown", "future", "Iron Crown", "mon", "after", (32, 32), ""),
    ("booster_future", "future", "item ball", "ball", "always", (41, 5), "Booster Energy; above the waterfall"),

    ("recorder", "stations", "recorder", "recorder", "always", (1, 3), "the log; it stands on the left counter"),
    ("note", "stations", "note", "note", "always", (2, 6), "the thing on the table"),
    ("resident", "stations", "resident", "person", "always", (8, 4),
     "Penny in No. 1; after the ending Arven in No. 2, Nemona in No. 3, Jacq in No. 4"),

    ("cavern_crystals", "cavern", "crystals", "crystal", "always",
     [(8, 2), (12, 2), (10, 4), (16, 8), (10, 10), (13, 11)], ""),
    ("cavern_item", "cavern", "item ball", "ball", "always", (7, 11), "Booster Energy"),
    ("roaring_moon", "cavern", "Roaring Moon", "mon", "after", (6, 4), ""),
    ("iron_valiant", "cavern", "Iron Valiant", "mon", "after", (16, 5), ""),

    # The Sealed Vault (test 15): three of the Ruinous four in niches along the back wall, a crystal across each
    # niche, and its stake out on the mirror floor. check.py plays the sliding through: every stake must be
    # reachable in some order, with no place to get stuck.
    ("vault_tablet", "vault", "great tablet", "tablet", "after", (8, 2), "the tale of the four treasures"),
    ("vault_sword", "vault", "the Sword's slat", "sign", "after", (5, 2),
     "the empty niche: Chien-Pao is in the icy cave"),
    ("wo_chien", "vault", "Wo-Chien", "mon", "after", (2, 2), "in its niche"),
    ("seal_wo_chien", "vault", "Wo-Chien's crystal", "crystal", "after", (2, 4),
     "closes the niche until the stake of the Tablets is pulled"),
    ("stake_wo_chien", "vault", "stake of the Tablets", "stake", "after", (9, 9),
     "on the mirror floor; pulled from a tile beside it"),
    ("ting_lu", "vault", "Ting-Lu", "mon", "after", (11, 2), ""),
    ("seal_ting_lu", "vault", "Ting-Lu's crystal", "crystal", "after", (11, 4), ""),
    ("stake_ting_lu", "vault", "stake of the Vessel", "stake", "after", (5, 11), ""),
    ("chi_yu", "vault", "Chi-Yu", "mon", "after", (14, 2), ""),
    ("seal_chi_yu", "vault", "Chi-Yu's crystal", "crystal", "after", (14, 4), ""),
    ("stake_chi_yu", "vault", "stake of the Beads", "stake", "after", (12, 9), ""),

    ("ice_crystals", "icecave", "crystals", "crystal", "always", [(2, 2), (10, 2), (8, 4), (3, 6), (9, 6)], ""),
    ("ice_item", "icecave", "item ball", "ball", "always", (6, 2), "Never-Melt Ice"),
    ("chien_pao", "icecave", "Chien-Pao", "mon", "after", (6, 4), ""),

    ("sada", "lab", "AI Sada", "person", "finale", (5, 4), "the finale: they appear when you touch the machine"),
    ("turo", "lab", "AI Turo", "person", "finale", (7, 4), ""),
    ("lab_koraidon", "lab", "the lab's Koraidon", "big", "finale", (4, 9), "you step back two tiles to face them"),
    ("lab_miraidon", "lab", "the lab's Miraidon", "big", "finale", (8, 9), ""),

    ("terapagos", "underdepths", "Terapagos", "mon", "after", (12, 15), ""),
]
# What may stand on a tile nobody can walk on: the recorder (a counter), the note (a table), and Terapagos, which
# lies in the Underdepths' pool of light.
ON_SOLID = {"recorder", "note", "terapagos"}
BY_ID = {t[0]: t for t in THINGS}
SECTION_OF = {t[0]: t[1] for t in THINGS}
NAME_OF = {t[0]: t[2] for t in THINGS}
KIND_OF = {t[0]: t[3] for t in THINGS}
WHEN_OF = {t[0]: WHEN[t[4]] for t in THINGS}
DEFAULTS = {t[0]: t[5] for t in THINGS}
# The Sealed Vault's three treasures: (the stake's id, the crystal's, the Pokemon's).
VAULT_SEALS = [("stake_" + k, "seal_" + k, k) for k in ("wo_chien", "ting_lu", "chi_yu")]
# A file written before something moved or came new is still read:
#  * MOVED: a thing that is in another section now. Its line in the old section is passed over (the tile was the
#    old map's) and the thing stands where the build puts it in the new one.
#  * GIVEN_UP: tiles a list gives up when the file has no section of that name yet. The crystal in front of the
#    Crystal Cavern's second mouth (15,2: every file had it, it was the build's own) stood where the way into
#    the Sealed Vault now is.
#  * RETIRED: a section whose map is no longer used. Its lines are passed over (their tiles were that map's) and
#    its things stand where the build puts them on the map that took its place: the way in was the Timeless
#    Woods up to test 15 and is Mossdeep City since test 16.
# What was done is told in the result's .notes, in plain words; rebuild.py then writes the file afresh.
#  * ALIASES: a thing that has another name now, in the same section. Its old line is read as the thing's own,
#    without a word: nothing moved. The file gets the new name the next time it is written (the editor's save).
MOVED = {("cavern", "wo-chien"): "wo_chien", ("cavern", "ting-lu"): "ting_lu", ("cavern", "chi-yu"): "chi_yu"}
ALIASES = {("crater", "time crystal 1"): "time1", ("crater", "time crystal 2"): "time2"}
GIVEN_UP = {"vault": {"cavern_crystals": [(15, 2)]}}
RETIRED = {"timeless woods": "mossdeep"}


class Values(dict):
    """The positions read from a file, and .notes: what an older file had that was passed over or is new."""
    notes = ()

HEAD = """\
# Area Zero: where everybody and everything stands.
#
# TO MOVE SOMETHING
#   1. Look at the pictures in the "map guide" folder: each map has its tile numbers along the edges
#      (x across the top, y down the side) and everything in this file drawn where it stands.
#   2. Change the two numbers after a name: x, y. Save this file.
#   3. Double-click "rebuild.bat". It makes the ROM again from this file and draws the pictures again.
#      If something stands in a wall, on water, on top of something else or in the way, it says so
#      and changes nothing.
#
# "crystals" is a list: add, move or take away as many as you like ("none" for no crystals at all).
# A line that starts with # is a note. To put everything back the way it was, delete this file and
# run rebuild.bat: it writes a fresh one.
"""


class PlacementError(Exception):
    """Something in the file cannot be read; the message says which line and why."""


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def text(values=None):
    """The file's text for these positions (the defaults for whatever is missing)."""
    values = dict(DEFAULTS, **(values or {}))
    out = [HEAD]
    width = max(len(t[2]) for t in THINGS)
    for key, title, maps in SECTIONS:
        out.append("\n[%s]" % title)
        for tid, sec, name, kind, when, default, note in THINGS:
            if sec != key:
                continue
            v = values[tid]
            if isinstance(default, list):
                tiles = "   ".join("%d,%d" % xy for xy in v) or "none"
                out.append("%s = %s" % (name.ljust(width), tiles) + ("        # " + note if note else ""))
            else:
                line = "%s = %2d, %2d" % (name.ljust(width), v[0], v[1])
                out.append(line + ("        # " + note if note else ""))
    return "\n".join(out) + "\n"


def parse(src, where="placements"):
    """{id: (x, y) or [(x, y), ...]} from the file's text. Names are matched without regard to case or spacing;
    what the text leaves out keeps its default."""
    sections = {norm(title): key for key, title, maps in SECTIONS}
    names = {(t[1], norm(t[2])): t[0] for t in THINGS}
    names.update(ALIASES)
    values = Values(DEFAULTS)
    sec = None
    said, in_file, notes = set(), set(), []
    retired = []                                     # (old title, section that took its place)
    for n, raw in enumerate(src.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.fullmatch(r"\[(.+)\]", line)
        if m:
            sec = sections.get(norm(m.group(1)))
            if sec is None and norm(m.group(1)) in RETIRED:
                sec = "retired"
                retired.append((m.group(1).strip(), RETIRED[norm(m.group(1))]))
                continue
            if sec is None:
                raise PlacementError("%s, line %d: there is no section [%s]. The sections are: %s." % (
                    where, n, m.group(1).strip(), ", ".join("[%s]" % t for k, t, ms in SECTIONS)))
            in_file.add(sec)
            continue
        if "=" not in line:
            raise PlacementError("%s, line %d: \"%s\" is not \"name = x, y\"." % (where, n, line))
        if sec is None:
            raise PlacementError("%s, line %d: \"%s\" comes before any [section]." % (where, n, line))
        if sec == "retired":                         # that map's tiles: passed over (said once, below)
            continue
        name, val = [s.strip() for s in line.split("=", 1)]
        tid = names.get((sec, norm(name)))
        if tid is None and (sec, norm(name)) in MOVED:
            now = MOVED[sec, norm(name)]
            notes.append("%s is in [%s] now, not in [%s]: its old line was passed over." % (
                NAME_OF[now], TITLE_OF[SECTION_OF[now]], TITLE_OF[sec]))
            continue
        if tid is None:
            known = ", ".join(t[2] for t in THINGS if t[1] == sec)
            raise PlacementError("%s, line %d: [%s] has nothing called \"%s\". It has: %s." % (
                where, n, TITLE_OF[sec], name, known))
        pairs = re.findall(r"(-?\d+)\s*,\s*(-?\d+)", val)
        rest = re.sub(r"(-?\d+)\s*,\s*(-?\d+)", "", val).strip(" ;")
        said.add(tid)
        if isinstance(DEFAULTS[tid], list) and not pairs and norm(rest) in ("", "none"):
            values[tid] = []                                 # a list may be empty: no crystals at all
            continue
        if rest or not pairs:
            raise PlacementError("%s, line %d: \"%s\" should be two numbers, x and y, with a comma: \"%s = 12, 34\"."
                                 % (where, n, val, name))
        tiles = [(int(x), int(y)) for x, y in pairs]
        if isinstance(DEFAULTS[tid], list):
            values[tid] = tiles
        elif len(tiles) != 1:
            raise PlacementError("%s, line %d: \"%s\" stands on one tile, but %d are given." % (
                where, n, name, len(tiles)))
        else:
            values[tid] = tiles[0]
    for sec, lists in GIVEN_UP.items():
        if sec in in_file:
            continue
        for tid, tiles in lists.items():
            gone = [t for t in tiles if t in values[tid]] if tid in said else []
            if gone:
                values[tid] = [t for t in values[tid] if t not in gone]
                notes.append("%s (%s): the one at %s was taken away. It stood where the way into the %s now is." % (
                    NAME_OF[tid], TITLE_OF[SECTION_OF[tid]], " and ".join("%d,%d" % t for t in gone), TITLE_OF[sec]))
    for old, now in retired:
        names_now = ", ".join(t[2] for t in THINGS if t[1] == now)
        notes.append("[%s] is no longer used: the way into Area Zero is in %s now. Its lines were passed over (their "
                     "tiles were the old map's); %s stand where the build puts them in [%s]." % (
                         old, TITLE_OF[now], names_now, TITLE_OF[now]))
    moved_in = {now for old, now in retired}
    new = [t for t in THINGS if t[0] not in said and t[1] not in moved_in]
    if new and said:
        where_new = sorted({TITLE_OF[t[1]] for t in new}, key=[s[1] for s in SECTIONS].index)
        notes.append("New since this file was written, standing where the build puts them: %s." % "; ".join(
            "[%s] %s" % (title, ", ".join(t[2] for t in new if TITLE_OF[t[1]] == title)) for title in where_new))
    values.notes = notes
    return values


def load(path=None):
    """The positions to build with: the defaults (THINGS) when no file is named; else the file's, and if the file
    is not there yet it is written from the defaults, so that there is one to edit."""
    if path is None:
        return Values(DEFAULTS)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text())
        return Values(DEFAULTS)
    with open(path, encoding="utf-8-sig") as f:
        return parse(f.read(), os.path.basename(path))


if __name__ == "__main__":
    import sys
    print(text(load(sys.argv[1] if len(sys.argv) > 1 else None)))
