"""Where everybody and everything of Kitakami stands, kept in a text file anyone can edit (as Area Zero's places.py).

The user, 2026-10-17, on Kitakami test 6: "I want to edit placement myself". So no position of a person, a sign or a
place in the story is written in the patch any more: kitakami_patch.py takes them from load(), which reads the
placements file named on the command line (the user's own is beside the test builds: roms/test-kitakami) and fills
in whatever it leaves out from THINGS below, and apply() hands them to the modules that build (kworld, kpeople,
kchapters). kpeople.layout_report then refuses a build in which something stands in a wall, on top of something
else, in a doorway, or in the way, at any moment of the story. editor.py is the same with a mouse.

A line is "name = x, y" or "name = x, y, facing" (up, down, left or right). Tiles are the map's own: x across, y down,
from 0 at the top left.

Not in here: the ground (the town's design is kworld.py's), doors, the market's stalls, the Pokemon Center's nurse,
and Briar in Mossdeep City (Area Zero's map: its own placements.txt).
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))

# The file's sections, and the map each is about (map keys as kitakami_patch.py names them)
SECTIONS = [
    ("town", "Mossui Town: people", "mossui"),
    ("signs", "Mossui Town: signs and the bus stop", "mossui"),
    ("story", "Mossui Town: the story", "mossui"),
    ("part2", "Mossui Town: Part 2 (Mochi Mayhem)", "mossui"),
    ("hall", "Kitakami Hall", "hall"),
    ("family", "Carmine and Kieran's house", "family"),
    ("home1", "the old woman's house", "home1"),
    ("home2", "the old couple's house", "home2"),
]
MAP_OF = {key: m for key, title, m in SECTIONS}
TITLE_OF = {key: title for key, title, m in SECTIONS}
FACINGS = ("up", "down", "left", "right")

# The moments of the story, for the editor's "show what is there at" list (kchapters' stages, and the two scenes
# with the most people in them).
MOMENTS = [
    ("s0", "arrival: Carmine at the bus stop"),
    ("s1", "chapter 1: the caretaker's task"),
    ("s2", "chapter 2: signboard 1"),
    ("s3", "chapter 2: signboard 2"),
    ("s4", "chapter 2: signboard 3"),
    ("s5", "chapter 2: Kieran at Loyalty Plaza"),
    ("s6", "chapter 3: the festival (evening)"),
    ("s7", "chapter 4: night, Grandpa's story"),
    ("s8", "chapter 5: the morning, Kieran with the mask"),
    ("wake", "chapter 6: the Loyal Three wake (the scene)"),
    ("s9", "chapter 7: the hunt"),
    ("s10", "chapter 8: Ogerpon waits"),
    ("s11", "after the story"),
    ("p12", "Part 2: Kieran's letter, the market"),
    ("p13", "Part 2: the villagers dancing"),
    ("p14", "Part 2: the grandparents before the Hall"),
    ("p15", "Part 2: Arven and Penny dancing"),
    ("p16", "Part 2: Nemona and Pecharunt at the plaza"),
    ("p17", "Part 2: the morning after"),
]
ALL = tuple(k for k, t in MOMENTS)
BEFORE_WAKE = ("s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "wake")
HIDING = ("s9", "s11", "p17")        # the Loyal Three until caught (away from the town on Part 2's night)

# id, section, name in the file, kind, the moments it is there, where it stands unless the file says otherwise
# ((x, y) or (x, y, facing)), a note for the file. Kinds: person, statue, mon (a Pokemon), sign, board (a legend
# signboard: its roof on the tile above), spot (a tile something happens on; nobody stands there).
THINGS = [
    # ---- Mossui's people (kpeople.TOWN)
    ("briar", "town", "Briar", "person", ALL, (22, 46, "right"), "at the bus stop; her bus takes you back to Mossdeep"),
    ("elder", "town", "the elder", "person", ALL, (35, 11, "up"), "Loyalty Plaza, before the statues"),
    ("organiser", "town", "the organiser", "person", ALL, (22, 35, "down"), "at the market's gate"),
    ("vendor_apples", "town", "apple stall vendor", "person", ALL, (19, 39, "down"),
     "the stalls' vendors stand in the gap of their goods row; shops from the festival on"),
    ("vendor_masks", "town", "mask stall vendor", "person", ALL, (28, 39, "down"), ""),
    ("vendor_mochi", "town", "mochi stall vendor", "person", ALL, (19, 44, "down"), ""),
    ("vendor_rice", "town", "rice ball stall vendor", "person", ALL, (28, 44, "down"), ""),
    ("farmer", "town", "apple farmer", "person", ALL, (14, 35, "left"), ""),
    ("mother", "town", "mother", "person", ALL, (33, 33, "right"), ""),
    ("child", "town", "child", "person", ALL, (34, 33, "left"), ""),
    ("lanterns", "town", "lantern maker", "person", ALL, (21, 7, "right"), ""),
    ("hiker", "town", "hiker", "person", ALL, (19, 7, "right"), ""),
    ("carver", "town", "mask carver", "person", ALL, (10, 32, "down"), ""),
    ("okidogi", "town", "statue of Okidogi", "statue", BEFORE_WAKE, (33, 9, "down"),
     "stone until chapter 6; the Loyal Three wake where their statues stand"),
    ("munkidori", "town", "statue of Munkidori", "statue", BEFORE_WAKE, (35, 9, "down"), ""),
    ("fezandipiti", "town", "statue of Fezandipiti", "statue", BEFORE_WAKE, (37, 9, "down"), ""),

    # ---- signs and the bus stop (kworld draws the signs; kpeople reads them)
    ("arrive", "signs", "where Briar's bus leaves you", "spot", ALL, (23, 46), "and where she brings you back"),
    ("sign_hall", "signs", "Kitakami Hall's sign", "sign", ALL, (16, 24), ""),
    ("sign_shrine", "signs", "Loyalty Plaza's sign", "sign", ALL, (31, 24), ""),
    ("sign_pond", "signs", "the pond's sign", "sign", ALL, (28, 13), ""),
    ("sign_bus", "signs", "the bus stop's sign", "sign", ALL, (25, 46), ""),
    ("legend_1", "signs", "signboard 1", "board", ALL, (9, 37),
     "the legend, part 1; its roof is drawn on the tile above it"),
    ("legend_2", "signs", "signboard 2", "board", ALL, (38, 37), "the legend, part 2"),
    ("legend_3", "signs", "signboard 3", "board", ALL, (26, 6),
     "the legend, part 3 (at 25,5 until 2026-10-17: its roof would have been in the wood's maples)"),

    # ---- the story (kchapters.POS, STORY_OBJECTS and the scenes)
    ("carmine_bus", "story", "Carmine at the bus stop", "person", ("s0",), (24, 45, "down"),
     "chapter 1: talk to her for her battle"),
    ("kieran_s0", "story", "Kieran before the battle", "person", ("s0",), (20, 30, "down"), ""),
    ("kieran_runs_in", "story", "Kieran runs in from", "spot", ("s0",), (23, 41),
     "after Carmine's battle he walks 2 tiles down from here"),
    ("kieran_hall", "story", "Kieran below the Hall", "person", ("s1",), (13, 26, "down"),
     "until the caretaker has given you the task"),
    ("kieran_board1", "story", "Kieran at signboard 1", "person", ("s2",), (10, 36, "left"), ""),
    ("kieran_board2", "story", "Kieran at signboard 2", "person", ("s3",), (37, 36, "right"), ""),
    ("kieran_board3", "story", "Kieran at signboard 3", "person", ("s4",), (27, 5, "left"), ""),
    ("kieran_plaza", "story", "Kieran at Loyalty Plaza", "person", ("s5",), (36, 11, "up"),
     "talking to him there turns the day to evening"),
    ("evening", "story", "where evening finds you", "spot", ("s6",), (23, 32), "you stand here as the festival begins"),
    ("carmine_fest", "story", "Carmine at the festival", "person", ("s6",), (25, 35, "down"), ""),
    ("ogerpon_fest", "story", "Ogerpon at the festival", "mon", ("s6",), (24, 41, "up"),
     "she runs 4 tiles up to you, then 6 tiles down and away"),
    ("kieran_angry", "story", "Kieran with the mask", "person", ("s8", "wake"), (34, 11, "up"),
     "his battle; then the Loyal Three wake"),
    ("carmine_runs_in", "story", "Carmine runs in from", "spot", ("wake",), (36, 16),
     "as the Loyal Three wake she walks 4 tiles up from here"),
    ("ogerpon", "story", "Ogerpon at the plaza", "mon", ("wake", "s10"), (35, 10, "down"),
     "as the Loyal Three wake, and where she waits for the finale"),
    ("carmine_hunt", "story", "Carmine during the hunt", "person", ("s9",), (36, 13, "left"), ""),
    ("kieran_hunt", "story", "Kieran during the hunt", "person", ("s9",), (34, 13, "right"), ""),
    ("carmine_final", "story", "Carmine at the finale", "person", ("s10",), (37, 10, "left"), ""),
    ("kieran_final", "story", "Kieran at the finale", "person", ("s10",), (33, 10, "right"), ""),
    ("live_okidogi", "story", "Okidogi's hiding place", "mon", HIDING, (42, 10, "left"),
     "the hunt, and after the story until it is caught"),
    ("live_munkidori", "story", "Munkidori's hiding place", "mon", HIDING, (28, 10, "down"), ""),
    ("live_fezandipiti", "story", "Fezandipiti's hiding place", "mon", HIDING, (17, 14, "down"), ""),

    # ---- Part 2, Mochi Mayhem (kchapters.P2POS)
    ("p2_kieran_market", "part2", "Kieran in the market", "person", ("p12", "p13"), (26, 41, "left"),
     "Part 2 begins: talk to him (Briar gives you his letter after the story)"),
    ("p2_arven_wait", "part2", "Arven waiting", "person", ("p12", "p13", "p14"), (19, 41, "right"), ""),
    ("p2_nemona_wait", "part2", "Nemona in the market", "person", ("p12",), (20, 41, "right"),
     "she goes off for mochi when Kieran has told you"),
    ("p2_penny_wait", "part2", "Penny waiting", "person", ("p12", "p13", "p14"), (27, 41, "left"), ""),
    ("p2_carmine_dance", "part2", "Carmine dancing", "person", ("p12", "p13", "p14", "p15"), (27, 33, "down"), ""),
    ("p2_kieran_hall", "part2", "Kieran below the Hall", "person", ("p14",), (14, 19, "left"), ""),
    ("p2_grandpa", "part2", "Grandpa before the Hall", "person", ("p14",), (10, 16, "right"),
     "the grandparents: one battle"),
    ("p2_grandma", "part2", "Grandma before the Hall", "person", ("p14",), (14, 16, "left"), ""),
    ("p2_kieran_friends", "part2", "Kieran by Arven and Penny", "person", ("p15",), (24, 36, "down"), ""),
    ("p2_arven_dance", "part2", "Arven dancing", "person", ("p15",), (21, 40, "right"), ""),
    ("p2_penny_dance", "part2", "Penny dancing", "person", ("p15",), (26, 40, "left"), ""),
    ("p2_pecha_market", "part2", "Pecharunt over the market", "mon", ("p15",), (24, 38),
     "it shows itself once Arven and Penny are beaten, then flies to the plaza"),
    ("p2_kieran_plaza", "part2", "Kieran at the plaza", "person", ("p16",), (33, 12, "right"), ""),
    ("p2_carmine_plaza", "part2", "Carmine at the plaza", "person", ("p16",), (37, 12, "left"), ""),
    ("p2_nemona_plaza", "part2", "Nemona at the plaza", "person", ("p16",), (36, 11, "down"),
     "her battle, then Pecharunt's"),
    ("p2_pecharunt", "part2", "Pecharunt at the plaza", "mon", ("p16",), (36, 10, "down"), ""),
    ("p2_kieran_after", "part2", "Kieran the morning after", "person", ("p17",), (25, 45, "left"), ""),
    ("p2_carmine_after", "part2", "Carmine the morning after", "person", ("p17",), (24, 45, "down"), ""),

    # ---- the insides
    ("caretaker", "hall", "the caretaker", "person", ALL, (7, 7, "down"), "the trip's task (chapter 1)"),
    ("grandpa", "family", "Grandpa", "person", ALL, (6, 2, "down"), ""),
    ("home_carmine", "family", "Carmine at home", "person", ALL, (8, 3, "left"), "once you have met her"),
    ("old_woman", "home1", "the old woman", "person", ALL, (6, 3, "down"), ""),
    ("old_man2", "home2", "the old man", "person", ALL, (2, 3, "down"), ""),
    ("old_woman2", "home2", "the old woman", "person", ALL, (6, 3, "down"), ""),
]
BY_ID = {t[0]: t for t in THINGS}
SECTION_OF = {t[0]: t[1] for t in THINGS}
NAME_OF = {t[0]: t[2] for t in THINGS}
KIND_OF = {t[0]: t[3] for t in THINGS}
WHEN_OF = {t[0]: tuple(t[4]) for t in THINGS}
DEFAULTS = {t[0]: tuple(t[5]) for t in THINGS}
NOTE_OF = {t[0]: t[6] for t in THINGS}
FACES = {tid for tid, v in DEFAULTS.items() if len(v) == 3}      # the things that face a way
# the scenes' walks: id -> (direction, tiles) from that thing's tile; the moments they happen in
WALKS = {"kieran_runs_in": (("down", 2),), "ogerpon_fest": (("up", 4), ("down", 6)),
         "carmine_runs_in": (("up", 4),)}


class Values(dict):
    """The positions read from a file (id -> (x, y) or (x, y, facing))"""
    notes = ()


HEAD = """\
# Kitakami: where everybody and everything stands.
#
# TO MOVE SOMETHING
#   Double-click "edit placements.bat": the maps open in your browser; drag things where you want them, then
#   press "Save and rebuild". Or change this file by hand:
#   1. Change the numbers after a name: x, y (and a facing - up, down, left or right - for a person).
#      x counts tiles across from the left edge, y down from the top, both from 0.
#   2. Save this file and double-click "rebuild.bat". It makes a new ROM from this file.
#      If something stands in a wall, in a doorway, on top of something else or in the way at any moment of
#      the story, it says so and changes nothing.
#
# A line that starts with # is a note. To put everything back the way it was, delete this file and run
# rebuild.bat: it writes a fresh one.
"""


class PlacementError(Exception):
    """Something in the file cannot be read; the message says which line and why."""


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def fmt(v):
    return "%2d, %2d" % v[:2] + (", %s" % v[2] if len(v) == 3 else "")


def text(values=None):
    """The file's text for these positions (the defaults for whatever is missing)."""
    values = dict(DEFAULTS, **(values or {}))
    out = [HEAD]
    width = max(len(t[2]) for t in THINGS)
    for key, title, m in SECTIONS:
        out.append("\n[%s]" % title)
        for tid, sec, name, kind, when, default, note in THINGS:
            if sec == key:
                line = "%s = %s" % (name.ljust(width), fmt(values[tid]))
                out.append(line + ("        # " + note if note else ""))
    return "\n".join(out) + "\n"


def parse(src, where="placements"):
    """{id: (x, y) or (x, y, facing)} from the file's text. Names are matched without regard to case or spacing;
    what the text leaves out keeps its default (and is told in .notes)."""
    sections = {norm(title): key for key, title, m in SECTIONS}
    names = {(t[1], norm(t[2])): t[0] for t in THINGS}
    values = Values(DEFAULTS)
    sec, said = None, set()
    for n, raw in enumerate(src.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.fullmatch(r"\[(.+)\]", line)
        if m:
            sec = sections.get(norm(m.group(1)))
            if sec is None:
                raise PlacementError("%s, line %d: there is no section [%s]. The sections are: %s." % (
                    where, n, m.group(1).strip(), ", ".join("[%s]" % t for k, t, ms in SECTIONS)))
            continue
        if "=" not in line:
            raise PlacementError("%s, line %d: \"%s\" is not \"name = x, y\"." % (where, n, line))
        if sec is None:
            raise PlacementError("%s, line %d: \"%s\" comes before any [section]." % (where, n, line))
        name, val = [s.strip() for s in line.split("=", 1)]
        tid = names.get((sec, norm(name)))
        if tid is None:
            known = ", ".join(t[2] for t in THINGS if t[1] == sec)
            raise PlacementError("%s, line %d: [%s] has nothing called \"%s\". It has: %s." % (
                where, n, TITLE_OF[sec], name, known))
        m = re.fullmatch(r"(-?\d+)\s*,\s*(-?\d+)\s*(?:,\s*([a-zA-Z]+))?", val)
        if not m:
            raise PlacementError("%s, line %d: \"%s\" should be two numbers, x and y, with a comma%s: \"%s = %s\"." % (
                where, n, val, " (and a facing)" if tid in FACES else "", name, fmt(DEFAULTS[tid])))
        x, y, face = int(m.group(1)), int(m.group(2)), m.group(3)
        if tid in FACES:
            face = norm(face) if face else DEFAULTS[tid][2]
            if face not in FACINGS:
                raise PlacementError("%s, line %d: \"%s\" is not a facing. A facing is up, down, left or right." % (
                    where, n, m.group(3)))
            values[tid] = (x, y, face)
        else:
            if face:
                raise PlacementError("%s, line %d: %s does not face a way: \"%s = %d, %d\"." % (where, n, name, name,
                                                                                            x, y))
            values[tid] = (x, y)
        said.add(tid)
    new = [t for t in THINGS if t[0] not in said]
    if new and said:
        values.notes = ["New since this file was written, standing where the build puts them: %s." % ", ".join(
            "%s (%s)" % (t[2], TITLE_OF[t[1]]) for t in new)]
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


def apply(values):
    """The positions into the modules that build (call before kworld.mossui and kpeople.make)."""
    import kworld as WD
    import kpeople as KP
    import kchapters as KC
    v = dict(DEFAULTS, **values)
    for key in ("briar", "elder", "organiser", "vendor_apples", "vendor_masks", "vendor_mochi", "vendor_rice",
                "farmer", "mother", "child", "lanterns", "hiker", "carver", "okidogi", "munkidori", "fezandipiti"):
        KP.TOWN[key] = v[key]
    KP.TOWN["carmine"] = v["carmine_bus"]
    KP.TOWN["kieran"] = v["kieran_s0"]
    KP.ARRIVE = v["arrive"]
    for key in ("sign_hall", "sign_shrine", "sign_pond", "sign_bus"):
        KP.SIGN_AT[key] = v[key]
    WD.TOWN_SIGNS[:] = [v[k] for k in ("sign_hall", "sign_shrine", "sign_pond", "sign_bus")]
    WD.LEGEND_SIGNS[:] = [v["legend_%d" % k] for k in (1, 2, 3)]
    pos = {0: {"carmine": v["carmine_bus"], "kieran": v["kieran_s0"]}, 1: {"kieran": v["kieran_hall"]},
           2: {"kieran": v["kieran_board1"]}, 3: {"kieran": v["kieran_board2"]}, 4: {"kieran": v["kieran_board3"]},
           5: {"kieran": v["kieran_plaza"]}, 6: {"carmine": v["carmine_fest"]}, 7: {},
           8: {"kieran": v["kieran_angry"]}, 9: {"carmine": v["carmine_hunt"], "kieran": v["kieran_hunt"]},
           10: {"carmine": v["carmine_final"], "kieran": v["kieran_final"]}, 11: {}}
    KC.POS.clear()
    KC.POS.update(pos)
    so = KC.STORY_OBJECTS
    for key in ("ogerpon", "ogerpon_fest", "live_okidogi", "live_munkidori", "live_fezandipiti"):
        sprite, x, y, face, flag = so[key]
        so[key] = (sprite, v[key][0], v[key][1], v[key][2], flag)
    for k in KC.L3:                                     # the Loyal Three wake where their statues stand
        sprite, x, y, face, flag = so["wake_" + k]
        so["wake_" + k] = (sprite, v[k][0], v[k][1], face, flag)
    KC.P2POS.clear()
    KC.P2POS.update({
        12: {"kieran": v["p2_kieran_market"], "carmine": v["p2_carmine_dance"], "arven2": v["p2_arven_wait"],
             "nemona2": v["p2_nemona_wait"], "penny2": v["p2_penny_wait"]},
        13: {"kieran": v["p2_kieran_market"], "carmine": v["p2_carmine_dance"], "arven2": v["p2_arven_wait"],
             "penny2": v["p2_penny_wait"]},
        14: {"kieran": v["p2_kieran_hall"], "carmine": v["p2_carmine_dance"], "arven2": v["p2_arven_wait"],
             "penny2": v["p2_penny_wait"], "grandpa2": v["p2_grandpa"], "grandma2": v["p2_grandma"]},
        15: {"kieran": v["p2_kieran_friends"], "carmine": v["p2_carmine_dance"], "arven2": v["p2_arven_dance"],
             "penny2": v["p2_penny_dance"]},
        16: {"kieran": v["p2_kieran_plaza"], "carmine": v["p2_carmine_plaza"], "nemona2": v["p2_nemona_plaza"],
             "pecharunt": v["p2_pecharunt"]},
        17: {"kieran": v["p2_kieran_after"], "carmine": v["p2_carmine_after"]}})
    KC.P2_PECHA_MARKET = v["p2_pecha_market"]
    for key, at in (("arven2", "p2_arven_wait"), ("penny2", "p2_penny_wait"), ("nemona2", "p2_nemona_wait"),
                    ("pecharunt", "p2_pecharunt"), ("grandpa2", "p2_grandpa"), ("grandma2", "p2_grandma")):
        sprite, x, y, face, flag = so[key]
        so[key] = (sprite, v[at][0], v[at][1], v[at][2], flag)
    KC.KIERAN_RUNS_IN = v["kieran_runs_in"]
    KC.CARMINE_RUNS_IN = v["carmine_runs_in"]
    KC.EVENING_AT = v["evening"]
    KC.FAMILY_CARMINE = v["home_carmine"]
    KP.ROOM_PEOPLE.clear()
    KP.ROOM_PEOPLE.update({
        "hall": [("caretaker",) + v["caretaker"]],
        "family": [("grandpa",) + v["grandpa"], ("home_carmine",) + v["home_carmine"]],
        "home1": [("old_woman",) + v["old_woman"]],
        "home2": [("old_man2",) + v["old_man2"], ("old_woman2",) + v["old_woman2"]],
    })
    return v


if __name__ == "__main__":
    import sys
    print(text(load(sys.argv[1] if len(sys.argv) > 1 else None)))
