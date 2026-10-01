"""Takes the Rare Candy NPC (candynpc) back out of Petalburg City's Poke Mart (map 8/6).

999 Rare Candies for a single "yes" made levelling pointless, so he goes. This runs at the end of the
chain and undoes candynpc on the built ROM rather than dropping candynpc from the middle of the chain:
every later patch was built and tested with its bytes in place, and its block sits just before
naturefix / hypertrain / hmfree in the same free run (0x08F53700..0x08F54AA0).

Why the Mart keeps 5 objects instead of going back to its original 4: the hack saves the map's object
events in SaveBlock1 (NOTES, RARE CANDY NPC), so a game saved inside the Mart reloads with him standing
on (5,6). Talking to him looks his template up by localId among the map's first objectEventCount
entries; with the count back at 4 nothing is found and the game takes a script pointer from address
0x10 (BIOS open bus, 0xE3A02004) and runs garbage. So entry 5 stays, moved far off the map (it never
comes into view, so it never spawns again), and its script becomes a lone `end`: on such a save the
leftover NPC does nothing when spoken to and is gone once the player leaves the Mart.

Everything else candynpc wrote (the rest of the script and its four texts) goes back to 0xFF. The given
flag 0x433F is left alone; nothing reads it any more.

usage: python nocandynpc_patch.py <in.gba> <out.gba>
"""
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "candynpc"))
import candynpc_patch as candy  # noqa: E402  (its layout constants and text encoder)

OFF_MAP = (-100, -100)                  # far outside the 8/6 map, so the object never comes into view
END = 0x02                              # script opcode `end`
LAST_TEXT = "Come back if you want them."   # candynpc lays its texts out q, done, again, deny


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000, "not the expected ROM"

    objs_addr = 0x08000000 + candy.FREE
    assert rom[candy.EVENTS] == candy.COUNT + 1, "map 8/6 does not have candynpc's 5 objects"
    assert struct.unpack_from("<I", rom, candy.EVENTS + 4)[0] == objs_addr, "8/6 objects are not candynpc's copy"
    count = candy.COUNT * candy.OBJ_SIZE
    assert rom[candy.FREE:candy.FREE + count] == rom[candy.OBJS:candy.OBJS + count], "copied objects differ"

    obj5 = candy.FREE + count
    script_off = obj5 + candy.OBJ_SIZE
    assert rom[obj5] == candy.LOCAL_ID and struct.unpack_from("<hh", rom, obj5 + 4) == candy.TILE, "not the NPC"
    assert struct.unpack_from("<I", rom, obj5 + 16)[0] == 0x08000000 + script_off, "NPC script pointer moved"
    head = bytes((0x6A, 0x5A, 0x2B)) + struct.pack("<H", candy.GIVEN_FLAG)
    assert rom[script_off:script_off + len(head)] == head, "NPC script is not candynpc's"

    last = candy.text(LAST_TEXT)
    at = rom.find(last, script_off, candy.FREE + 0x200)
    assert at > 0, "candynpc's texts not found"
    end = at + len(last)
    assert set(rom[end:end + 16]) == {0xFF}, "something follows candynpc's block"

    struct.pack_into("<hh", rom, obj5 + 4, *OFF_MAP)
    rom[script_off] = END
    rom[script_off + 1:end] = b"\xFF" * (end - script_off - 1)
    open(outp, "wb").write(rom)
    print("8/6 object %d -> %s, script @0x%08X is now `end`; freed 0x%08X..0x%08X (%d bytes)" % (
        candy.LOCAL_ID, OFF_MAP, 0x08000000 + script_off, 0x08000000 + script_off + 1, 0x08000000 + end,
        end - script_off - 1))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
