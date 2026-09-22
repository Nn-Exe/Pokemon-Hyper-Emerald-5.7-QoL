"""Sinnoh League attendant, still in Chinese (Hyper Emerald v5.7): python leaguetext_patch.py in.gba out.gba

In the Elite Four hall (map 34/30, map section "Test of Heart") an attendant heals your team after each Elite Four
win and lets you pick the next door. Her heal line and the four door names of that menu were never translated;
her welcome and "Please choose the next door." were. This writes English copies into free space and points the
script and the menu at them. It also fixes Lucian's name in his line after a lost battle: "Wusong" is his Chinese
name (悟松) romanised. That one is done in place, since both names are 6 letters.

ROM changes: the message pointer of `message` at 0x0987549D (the only reference to the old text); the four text
pointers of multichoice list 126 (0x09876B14: {text, unused} rows; the hack's list table is at 0x09700000); 6
bytes of text at 0x08B41CF9. The new strings are at FREE. Order-independent: it touches nothing another patch does.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "journal"))
import journal_patch as J

FREE = 0x00FF2460                       # in the unreferenced 0xFF run 0x08FF2454..0x08FFD5A0
B = 0x08000000

HEAL_AT = 0x0187549D                    # message 0x09875BFF; waitmessage; playfanfare (the heal jingle)
HEAL_OLD = 0x09875BFF
# the attendant is "Attendant" in her translated welcome (0x08B8185F), so the same here
HEAL = ("Attendant: Good work out there!", "Allow me to restore your Pokémon.")

LIST = 0x01876B14                       # multichoice 126 (multichoice 20, 4, 126, ignoreB at 0x098754BF)
LIST_ENTRY = 0x01700000 + 126 * 8
# the doors on the hall's top wall, left to right (x 4, 8, 18, 22; the Champion's door is x 13):
# 左一 / 左二 / 右二 / 右一, "left one, left two, right two, right one", counted from the outer walls
DOORS = [(0x09876B3D, "左一", "Far left"), (0x09876B44, "左二", "Left"),
         (0x09876B4B, "右二", "Right"), (0x09876B52, "右一", "Far right")]
DOOR_BYTES = {"左一": "112b0f0bff", "左二": "112b03a3ff", "右二": "0f8003a3ff", "右一": "0f800f0bff"}

LUCIAN_AT = 0x00B41CF9                  # "Wusong: You certainly have keen battle instincts..." (0x09875986 points here)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000

    assert rom[HEAL_AT] == 0x67 and struct.unpack_from("<I", rom, HEAL_AT + 1)[0] == HEAL_OLD, \
        "the heal message is not where expected (already applied?)"
    assert rom[HEAL_AT + 5] == 0x66, "waitmessage does not follow the heal message"
    assert struct.unpack_from("<IB", rom, LIST_ENTRY) == (B + LIST, 4), "multichoice 126 moved"
    for k, (old, zh, _) in enumerate(DOORS):
        assert struct.unpack_from("<I", rom, LIST + 8 * k)[0] == old, "door %d's pointer moved" % k
        assert rom[old - B:old - B + 5].hex() == DOOR_BYTES[zh], "door %d is not %s" % (k, zh)
    assert bytes(rom[LUCIAN_AT:LUCIAN_AT + 7]) == J.enc("Wusong:"), "Lucian's line does not start with Wusong"

    d = bytearray()
    assert all(len(l) <= 34 for l in HEAL)
    heal = B + FREE + len(d)
    d += J.enc(HEAL[0]) + b"\xfe" + J.enc(HEAL[1]) + b"\xff"
    doors = []
    for _, _, en in DOORS:
        doors.append(B + FREE + len(d))
        d += J.enc(en) + b"\xff"
    assert set(rom[FREE:FREE + len(d)]) == {0xFF}, "target region not free"
    assert FREE + len(d) <= 0x00FFD5A0
    rom[FREE:FREE + len(d)] = d

    struct.pack_into("<I", rom, HEAL_AT + 1, heal)
    for k, p in enumerate(doors):
        struct.pack_into("<I", rom, LIST + 8 * k, p)
    rom[LUCIAN_AT:LUCIAN_AT + 6] = J.enc("Lucian")
    open(outp, "wb").write(rom)
    print("strings %d bytes @%08X..%08X: heal %08X, doors %s; Lucian fixed @%08X" % (
        len(d), B + FREE, B + FREE + len(d), heal, " ".join("%08X" % p for p in doors), B + LUCIAN_AT))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
