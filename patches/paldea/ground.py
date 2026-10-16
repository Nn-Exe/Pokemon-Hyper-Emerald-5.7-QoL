"""The ground of Area Zero's maps where the user has changed it, kept in a text file beside placements.txt.

The user, on test 11: "apart from placement, can I change tiles layout everything myself? like Hex app. I cannot
use Hex app" (Hex Maniac Advance does not open this ROM). So the placement editor (editor.py) also paints: every
map's tiles can be changed with the mouse, and what was changed is written to ground.txt, one tile a word:

    x,y:block      block = metatile | collision << 10 | height << 12, in hex, as the game stores a map

Only the tiles that differ from the map as the patch draws it are in the file (world.py still draws the wall and
the crater, and the rooms are still copied from the game's own; the file is laid over that). paldea_patch.py reads
it through load(); check.py then refuses a build in which a door was painted over, something stands in a wall or
ground can no longer be reached.

A section is a map, or the maps that share one ground: the crater is the same in both times (a time crystal puts
you on the same tile in the other), and the four research stations are one room. Mossdeep City (the way in;
the Timeless Woods up to test 15) is the game's own map and is not in here.
"""
import os, re

SECTIONS = [
    ("wall", "the wall", ["wall"]),
    ("crater", "crater, both times", ["past", "future"]),
    ("stations", "research stations", ["station1", "station2", "station3", "station4"]),
    ("cavern", "Crystal Cavern", ["cavern"]),
    ("vault", "Sealed Vault", ["vault"]),
    ("icecave", "icy cave", ["icecave"]),
    ("lab", "Zero Lab", ["lab"]),
    ("underdepths", "Underdepths", ["underdepths"]),
]
MAPS_OF = {key: maps for key, title, maps in SECTIONS}
TITLE_OF = {key: title for key, title, maps in SECTIONS}
SECTION_OF = {m: key for key, title, maps in SECTIONS for m in maps}
NAME = "ground.txt"

HEAD = """\
# Area Zero: the ground where you changed it with the editor ("edit placements.bat", "Paint the ground").
#
# One word a tile: x,y:block. The block is the game's own number for a map tile, in hex (which tile it is, whether
# you can walk on it, how high it is). The editor writes this file; there is no need to edit it by hand.
# To get a map's ground back as it was, delete its lines (or the whole file) and run rebuild.bat.
"""


class GroundError(Exception):
    """Something in the file cannot be read; the message says which line and why."""


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def text(values):
    """The file's text: {section: {(x, y): block}}."""
    out = [HEAD]
    for key, title, maps in SECTIONS:
        cells = values.get(key) or {}
        if not cells:
            continue
        out.append("\n[%s]" % title)
        words = ["%d,%d:%04X" % (x, y, v) for (x, y), v in sorted(cells.items(), key=lambda c: (c[0][1], c[0][0]))]
        for k in range(0, len(words), 10):
            out.append(" ".join(words[k:k + 10]))
    return "\n".join(out) + "\n"


def parse(src, where=NAME):
    sections = {norm(title): key for key, title, maps in SECTIONS}
    values, sec = {}, None
    for n, raw in enumerate(src.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.fullmatch(r"\[(.+)\]", line)
        if m:
            sec = sections.get(norm(m.group(1)))
            if sec is None:
                raise GroundError("%s, line %d: there is no map [%s]. The maps are: %s." % (
                    where, n, m.group(1).strip(), ", ".join("[%s]" % t for k, t, ms in SECTIONS)))
            values.setdefault(sec, {})
            continue
        if sec is None:
            raise GroundError("%s, line %d: \"%s\" comes before any [map]." % (where, n, line))
        for word in line.split():
            m = re.fullmatch(r"(\d+),(\d+):([0-9A-Fa-f]{1,4})", word)
            if not m:
                raise GroundError("%s, line %d: \"%s\" is not x,y:block." % (where, n, word))
            values[sec][int(m.group(1)), int(m.group(2))] = int(m.group(3), 16)
    return {k: v for k, v in values.items() if v}


def load(path=None):
    """{section: {(x, y): block}}: nothing when no file is named or it is not there."""
    if path is None or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig") as f:
        return parse(f.read(), os.path.basename(path))


def lay(changes, by_key):
    """Lays the changes over the maps (by_key: map key -> an object with w, h and blocks). Tiles off a map are
    left out (a map that has since become smaller): returned as [(section, x, y)]."""
    off = []
    for sec, cells in changes.items():
        for key in MAPS_OF[sec]:
            m = by_key[key]
            for (x, y), v in cells.items():
                if 0 <= x < m.w and 0 <= y < m.h:
                    m.blocks[y][x] = v
                elif key == MAPS_OF[sec][0]:
                    off.append((sec, x, y))
    return off


if __name__ == "__main__":
    import sys
    print(text(load(sys.argv[1] if len(sys.argv) > 1 else None)))
