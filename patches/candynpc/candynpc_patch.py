"""Rare Candy NPC in Petalburg City's Poke Mart (map 8/6).

The hack soft-resets on any mart list it does not own (BuyMenuTryMakePurchase 0x080E0EDC jumps to
0x096FFF00, which only understands the hack's own list pointers), so a Rare Candy *shop* is out. Instead
this puts a person in the Mart who hands one out, repeatably.

The Mart's event block (0x0852F304) has its 4-object array (0x0852F294) sitting flush against the warp
array (0x0852F2F4), so there is no spare slot. This copies the array into verified free space with a 5th
entry, points the events struct at the copy and bumps nobj to 5. The new object is a clone of object 1 (a
stationary shopper, so its elevation/movement/trainer fields are known-good) with a new localId, position
and script.

No Thumb: the NPC's whole behaviour is the 9-byte vanilla script
    lock(69) faceplayer(5A) giveitem(44) <item:u16> <amount:u16> release(6B) end(02)
written next to the relocated array.

usage: python candynpc_patch.py <in.gba> <out.gba>
"""
import struct, sys

FREE = 0x00F53700                       # 5024 bytes of all-FF, zero inbound pointers (verified)
EVENTS = 0x052F304                       # map 8/6 MapEvents struct: nobj at +0, objects ptr at +4
OBJS = 0x052F294                         # the 4-object array itself
COUNT = 4
OBJ_SIZE = 24
RARE_CANDY = 68
TILE = (7, 5)                            # open floor between the two shoppers
LOCAL_ID = 5                             # the map's objects use 1-4
OBJ1 = bytes.fromhex("0213000009000400030a000000000000e87d200800000000")


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000, "not the expected ROM"
    assert rom[EVENTS] == COUNT, "map 8/6 object count unexpected: %d" % rom[EVENTS]
    assert struct.unpack_from("<I", rom, EVENTS + 4)[0] == 0x08000000 + OBJS, "object array pointer unexpected"
    assert rom[OBJS + OBJ_SIZE:OBJS + 2 * OBJ_SIZE] == OBJ1, "object 1 is not the template this patch expects"
    for i in range(COUNT):
        assert rom[OBJS + i * OBJ_SIZE] not in (0, LOCAL_ID), "localId clash on object %d" % i

    old = bytes(rom[OBJS:OBJS + COUNT * OBJ_SIZE])

    new = bytearray(OBJ1)
    new[0] = LOCAL_ID
    struct.pack_into("<h", new, 4, TILE[0])
    struct.pack_into("<h", new, 6, TILE[1])

    script_off = FREE + (COUNT + 1) * OBJ_SIZE
    script = bytes((0x69, 0x5A, 0x44)) + struct.pack("<HH", RARE_CANDY, 1) + bytes((0x6B, 0x02))
    struct.pack_into("<I", new, 16, 0x08000000 + script_off)

    end = script_off + len(script)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"

    rom[FREE:FREE + COUNT * OBJ_SIZE] = old
    rom[FREE + COUNT * OBJ_SIZE:script_off] = bytes(new)
    rom[script_off:end] = script
    rom[EVENTS] = COUNT + 1
    struct.pack_into("<I", rom, EVENTS + 4, 0x08000000 + FREE)
    open(outp, "wb").write(rom)
    print("objects -> 0x%08X (%d entries, was %d); new object localId=%d gfx=%d at %s; script @0x%08X: %s"
          % (0x08000000 + FREE, COUNT + 1, COUNT, LOCAL_ID, new[1], TILE, 0x08000000 + script_off, script.hex()))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
