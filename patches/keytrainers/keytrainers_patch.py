"""The key trainers' teams with Gen 9 Pokemon (Hyper Emerald v5.7). Apply after wilditem, before kitakami (no
other step touches these bytes: kitakami's nearest change is more than 64 bytes away).
usage: python -I keytrainers_patch.py <in.gba> <out.gba>

Luciano Fire (credit them: README, Credits) rebuilt the teams of 42 trainers - the eight Gym Leaders, the Elite
Four, Wallace, Archie, Maxie and Tabitha (both battles each), Brendan and May, Zinnia and 17 others - with Gen 9
Pokemon, on a copy of "(my placements 26)" (382cf97c...). Their file, the second they sent (e19e1e44..., 2026-10-20), is that ROM plus
549 changed bytes, all inside these 42 trainers' structs and parties (make_data.py stops on anything else).
keytrainers.json holds every changed party entry, old and new, raw and read out; and Danielle's (#650) class and
picture (Battle Girl 43 -> Lady 20, picture 64 -> 59). Each team stays where it was, at the same size: no free
space is used.

Every old byte is checked before it is written, so this stops on a game that differs where it writes (or already
has it). NOTES, *The key trainers' Gen 9 teams*.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRAINERS, SIZE = 0x010019F8, 40


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    data = json.load(open(os.path.join(HERE, "keytrainers.json"), encoding="utf-8"))
    u32 = lambda o: struct.unpack_from("<I", rom, o)[0]
    # the trainer table is still where the battle code reads it (vanilla's literal in BattleSetup, 0x0803587C)
    assert u32(0x0003587C) == 0x08000000 + TRAINERS, "gTrainers is not at 0x090019F8"
    entries = written = 0
    for t in data["trainers"]:
        e = TRAINERS + SIZE * t["id"]
        for s in t["struct"]:
            assert rom[e + s["offset"]] == s["old"], "trainer %d +%d: %d, not %d" % (t["id"], s["offset"], rom[e + s["offset"]], s["old"])
            rom[e + s["offset"]] = s["new"]
            written += 1
        for p in t["party"]:
            o = int(p["offset"], 16) - 0x08000000
            old, new = bytes.fromhex(p["old_bytes"]), bytes.fromhex(p["new_bytes"])
            assert u32(e + 36) - 0x08000000 <= o < u32(e + 36) - 0x08000000 + 16 * rom[e + 32], \
                "trainer %d: slot %d is not in its party" % (t["id"], p["slot"])
            assert bytes(rom[o:o + len(old)]) == old, "trainer %d (%s) slot %d: the game differs there (already applied?)" % (
                t["id"], t["name"], p["slot"])
            rom[o:o + len(new)] = new
            written += sum(1 for x, y in zip(old, new) if x != y)
            entries += 1
    open(outp, "wb").write(rom)
    print("%d trainers, %d party entries, %d bytes changed" % (len(data["trainers"]), entries, written))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
