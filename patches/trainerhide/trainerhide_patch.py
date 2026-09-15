"""Hide the trainers you listed in hidden.json (Hyper Emerald v5.7). Apply after the mintskip build.
usage: python trainerhide_patch.py <in.gba> <out.gba> [hidden.json]

Pick trainers with trainers.py, then add one entry per trainer to hidden.json:
    {"map": "34/82", "object": 1, "trainer_id": 1234, "name": "Grunt"}
("trainers.py <rom> --map NAME --json" prints entries you can copy.)

How a trainer is hidden: its object stays in the map's object list (so every other object keeps its number and
no cutscene breaks), but its position is moved far outside the map, and its trainer sight is switched off. The
game only creates objects near the camera, so it never appears, never spots you and can't be talked to. Nothing
in the save changes; its trainer flag stays unset, exactly as if you had never met it. Removing the entry from
hidden.json and rebuilding brings it back.

Every entry is checked before writing: the object must exist and still run a trainerbattle for the same trainer id,
so a typo cannot hide the wrong object.
"""
import struct, sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trainers import Rom, GROUPS

HIDDEN_X = HIDDEN_Y = 0x2000                # far outside any map; never inside the camera window


def build(inp, outp, list_path=None):
    list_path = list_path or os.path.join(HERE, "hidden.json")
    entries = json.load(open(list_path, encoding="utf-8"))
    rom = Rom(inp)
    data = bytearray(rom.b)
    done = 0
    for ent in entries:
        g, m = map(int, ent["map"].split("/"))
        hp = rom.header(g, m)
        assert hp is not None, "map %s does not exist" % ent["map"]
        ev = rom.ptr(hp + 4); objs = rom.ptr(ev + 4)
        k = int(ent["object"])
        assert objs and 0 <= k < rom.b[ev], "map %s has no object %d" % (ent["map"], k)
        e = objs + 24 * k
        s = rom.ptr(e + 16)
        assert s and rom.b[s] == 0x5C, "map %s object %d is not a trainer" % (ent["map"], k)
        tid = rom.u16(s + 2)
        assert tid == int(ent["trainer_id"]), "map %s object %d is trainer %d, hidden.json says %s" % (
            ent["map"], k, tid, ent["trainer_id"])
        struct.pack_into("<hh", data, e + 4, HIDDEN_X, HIDDEN_Y)   # position
        struct.pack_into("<HH", data, e + 12, 0, 0)                # trainer type none, sight range 0
        done += 1
        print("hid %s object %d: %s (trainer %d)" % (ent["map"], k, ent.get("name", "?"), tid))
    open(outp, "wb").write(data)
    print("wrote %s: %d trainer%s hidden" % (outp, done, "" if done == 1 else "s"))


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print(__doc__); sys.exit(1)
    build(*sys.argv[1:])
