"""News Tracker freeze fix (Hyper Emerald v5.7). Apply after the npcnames build.
usage: python newsfix_patch.py <in.gba> <out.gba>

Using the News Tracker key item froze the game: the roaming Latios/Latias message drew its first line and
then the game sat there with the music still playing.

Cause, one stray byte in the message string at 0x09F0AB84:

    ... on [Route].  FC 09  09  FF
                     |      |   `- terminator
                     |      `- stray byte
                     `- EXT_CTRL_CODE_PAUSE_UNTIL_PRESS, which takes NO argument

0x09 is a lead byte of this hack's two-byte Chinese encoding, so the text engine read `09 FF` as one
character and swallowed the terminator. The string never ended, the message box never reported itself
finished, and the task waiting on it (0x08121F3C, which polls the field message box) spun forever. Audio
is interrupt-driven, so the music kept playing - exactly what a "frozen but still humming" game looks like.

The fix turns the stray byte into a second terminator, leaving `FC 09 FF` - the same ending the item's own
"No news received" message already uses. One byte, no repointing, no free space.

The bug is in the original Chinese ROM too (the bytes here are identical to it), so it is the hack's, not
the translation's. It is the only string in the ROM with this shape.

The same message also printed its region name in Chinese, because the two names the routine picks between
were never translated. They are rewritten here in place: the routine reaches them as base 0x09F0AB48 plus a
fixed offset, nothing points at the padding around them, and both English names fit.
"""
import sys

FIX = 0x1F0ABB8                                     # the stray byte
EXPECT = bytes.fromhex("04fd04adfc0909ff")          # ...{VAR04} . FC 09 09 FF
AFTER = bytes.fromhex("04fd04adfc09ffff")

ENC = {}
for i in range(26): ENC[chr(65 + i)] = 0xBB + i
for i in range(26): ENC[chr(97 + i)] = 0xD5 + i

# base 0x09F0AB48 + 0x2C and + 0x34, picked by whether the roamer is in map group 0
NAMES = [(0x1F0AB74, "03e40fc1ff", "Hoenn", 8),     # offset, expected Chinese bytes, English, bytes available
         (0x1F0AB7C, "0bcf0121ff", "Sinnoh", 8)]


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    got = bytes(rom[FIX - 6:FIX + 2])
    assert got == EXPECT, "message tail is %s, expected %s" % (got.hex(), EXPECT.hex())
    rom[FIX] = 0xFF
    assert bytes(rom[FIX - 6:FIX + 2]) == AFTER

    for off, want, name, room in NAMES:
        got = bytes(rom[off:off + len(want) // 2]).hex()
        assert got == want, "region name at %08X is %s, expected %s" % (0x08000000 + off, got, want)
        enc = bytes(ENC[c] for c in name) + bytes([0xFF])
        assert len(enc) <= room, "%r does not fit" % name
        rom[off:off + room] = enc + bytes(room - len(enc))
        print("  region name at %08X -> %r" % (0x08000000 + off, name))

    open(outp, "wb").write(rom)
    print("News Tracker message terminated at %08X (09 -> FF)" % (0x08000000 + FIX))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
