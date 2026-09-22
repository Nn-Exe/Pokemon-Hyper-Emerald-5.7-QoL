"""Sinnoh Map fly to the League door (Hyper Emerald v5.7): python leaguefly_patch.py in.gba out.gba

The Ride Pokemon courier has TWO "Sinnoh League" stops: the Pokemon Center by the Victory Road entrance
(flag 0x42EA, set on arriving there) and the League building's door (flag 0x42EB, set by the trigger at the
far end of Victory Road). The Sinnoh Map keys its fly table by map section, and both are section 97, so it
only ever offered the first. This adds a three-command script that picks the door once 0x42EB is set, else
the Pokemon Center, and points the map's section-97 entry at it. Data only: no code changes.
"""
import struct, sys

ENTRY = 0x00FDC574                      # the Sinnoh Map's courier entry for section 97 {97, 0, flag, block}
ENTRY_BYTES = bytes.fromhex("6100ea4296d18709")
PC_BLOCK, DOOR_BLOCK = 0x0987D196, 0x0987D1AF
FREE = 0x00FEFF00                       # end of the unreferenced 0xFF run 0x08FE9074..0x08FF0000


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert bytes(rom[ENTRY:ENTRY + 8]) == ENTRY_BYTES, "the Sinnoh Map's League entry is not as expected"

    # both courier blocks: checkflag <flag>; goto_if_unset ...; call ...; warp 36.14 (x, y)
    for block, flag, xy in ((PC_BLOCK, 0x42EA, (10, 35)), (DOOR_BLOCK, 0x42EB, (14, 6))):
        b = block - 0x08000000
        assert rom[b] == 0x2B and struct.unpack_from("<H", rom, b + 1)[0] == flag, "courier block %08X changed" % block
        assert bytes(rom[b + 14:b + 17]) == bytes((0x39, 36, 14)), "courier block %08X no longer warps to 36.14" % block
        assert struct.unpack_from("<hh", rom, b + 18) == xy

    script = (bytes((0x2B,)) + struct.pack("<H", 0x42EB)           # checkflag 0x42EB (reached the far end of Victory Road)
              + bytes((0x06, 0x01)) + struct.pack("<I", DOOR_BLOCK)  # goto_if_set -> the League door
              + bytes((0x05,)) + struct.pack("<I", PC_BLOCK))      # goto -> the Pokemon Center
    assert set(rom[FREE:FREE + len(script)]) == {0xFF}, "target region not free"
    rom[FREE:FREE + len(script)] = script
    struct.pack_into("<I", rom, ENTRY + 4, 0x08000000 + FREE)
    open(outp, "wb").write(rom)
    print("chooser script %d bytes @%08X; section 97 now runs it" % (len(script), 0x08000000 + FREE))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
