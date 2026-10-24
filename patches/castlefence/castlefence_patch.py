"""Rainbow Castle: the trap's fence no longer shuts you out when you come back (Hyper Emerald v5.7).
usage: python castlefence_patch.py <in.gba> <out.gba>

A player's report (2026-10-22): "during the rainbow rocket castle mission, there are two kirlia to warp u back town,
on the second inner kirlia, if u have not completed the castle mission and warp back, the fence is locked as
softlock ... you'll get stuck and won't be able to go back in to fight Rainbow Rocket!!", with a screenshot: the
player between a railing and the way out.

The castle (NOTES, *Rainbow Castle: the fence*): EV Training Cave (35/49) -> the entrance hall 35/3 -> the first floor
34/82 -> the hub 34/83 -> 35/4 -> 35/5 (the inner Kirlia, which teleports you to Pacifidlog with no check) -> 34/93.
In 34/82 the Pawn's trap (the triggers at (12..14, 18), once: flag 0x41EA) moves you north and raises a fence on row
15 (setmetatile at x 5, 6, 12, 13, 14, 20, 21: 0x297 / 0x269, impassable), and its on-load script (0x09866A65)
raises it again on every load while the castle is not beaten (0x41D5 clear) and the trap has sprung (0x41EA set).
Back from Pacifidlog you come in by the entrance hall, south of the fence, and cannot pass it: the only ways on are
the entrance hall's Kirlia (out again) and the Blue-Haired Passerby's restart (35/49, 500,000, every castle flag
cleared). The hub's and 34/89's gates open with progress and stay open, so they do not shut anyone out.

Now the on-load script (34/82's map-script table entry 0x08A399D5 points to a new one) raises the fence only when you
are north of it (getplayerxy: y <= 15), as everyone is after the trap; coming in from the south it stays open and
you walk on to the hub, where the castle's progress is kept. A save already stuck there is free the next time the map
loads. The trap itself, and the fence it raises, are unchanged.
Script: 0x09E3C200.. (after mintquirky's, in the space its notes prove blank and unread; ..0x09E3C240 kept).
"""
import struct, sys

FREE, FREE_END = 0x01E3C200, 0x01E3C240
BASE = 0x08000000 + FREE
TABLE_ENTRY = 0x08A399D5                       # 34/82's map scripts: type 1 (on load) -> the old script
OLD_SCRIPT = 0x09866A65
OLD_BYTES = bytes.fromhex("2bd5410601864985092bea41060086498509")    # checkflag 0x41D5; goto_if set -> end;
                                                                      # checkflag 0x41EA; goto_if unset -> end
FENCE = 0x09866A77                             # its setmetatiles (row 15) and end
FENCE_BYTES = bytes.fromhex("a205000f0097020100a206000f0069020100")
END = 0x09854986                               # releaseall; end
FENCE_ROW = 15
TEMP_X, TEMP_Y = 0x400E, 0x400F                # scratch for getplayerxy (temp vars; 34/82's triggers use 0x400A)


def script():
    p = lambda a: struct.pack("<I", a)
    h = lambda v: struct.pack("<H", v)
    return (b"\x2b" + h(0x41D5) + b"\x06\x01" + p(END)                # checkflag 0x41D5; goto_if set -> end
            + b"\x2b" + h(0x41EA) + b"\x06\x00" + p(END)              # checkflag 0x41EA; goto_if unset -> end
            + b"\x42" + h(TEMP_X) + h(TEMP_Y)                         # getplayerxy
            + b"\x21" + h(TEMP_Y) + h(FENCE_ROW)                      # compare y, 15
            + b"\x06\x02" + p(END)                                    # goto_if > -> end: south of the fence
            + b"\x05" + p(FENCE))                                     # goto the fence


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    assert rom[o(TABLE_ENTRY) - 1] == 1 and struct.unpack_from("<I", rom, o(TABLE_ENTRY))[0] == OLD_SCRIPT, \
        "34/82's on-load script is not the one expected"
    assert bytes(rom[o(OLD_SCRIPT):o(OLD_SCRIPT) + len(OLD_BYTES)]) == OLD_BYTES
    assert o(OLD_SCRIPT) + len(OLD_BYTES) == o(FENCE)
    assert bytes(rom[o(FENCE):o(FENCE) + len(FENCE_BYTES)]) == FENCE_BYTES
    assert bytes(rom[o(END):o(END) + 2]) == b"\x6b\x02"
    assert rom.count(struct.pack("<I", OLD_SCRIPT)) == 1, "the old script is reached from elsewhere too"
    s = script()
    assert FREE + len(s) <= FREE_END and set(rom[FREE:FREE_END]) == {0x00}, "target region not blank"
    rom[FREE:FREE + len(s)] = s
    struct.pack_into("<I", rom, o(TABLE_ENTRY), BASE)
    open(outp, "wb").write(rom)
    print("castlefence: 34/82's on-load script %08X..%08X (the fence only when you are north of row %d)" % (
        BASE, BASE + len(s), FENCE_ROW))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
