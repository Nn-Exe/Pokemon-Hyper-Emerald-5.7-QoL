"""Rare Candy NPC in Petalburg City's Poke Mart (map 8/6).

The hack soft-resets on any mart list it does not own (BuyMenuTryMakePurchase 0x080E0EDC jumps to
0x096FFF00, which only understands the hack's own list pointers), so a Rare Candy *shop* is out. Instead
this puts a person in the Mart who offers 999 Rare Candies once.

The Mart's event block (0x0852F304) has its 4-object array (0x0852F294) sitting flush against the warp
array (0x0852F2F4), so there is no spare slot. This copies the array into verified free space with a 5th
entry, points the events struct at the copy and bumps nobj to 5. The new object is a clone of object 1
(so its elevation/movement/trainer fields are known-good) with a new localId, position and script.

Nothing here is Thumb: the NPC's whole behaviour is one vanilla script, written next to the array.

    lock, faceplayer
    checkflag GIVEN        -> if set, "already given" and stop
    loadword 0, TEXT_Q ; callstd 5 (yes/no)
    compare VAR_RESULT, 0  -> on No, stop
    giveitem 68, 999       (68 = Rare Candy; 999 is the bag cap this build ships)
    setflag GIVEN
    "enjoy" message, release, end

Script opcodes used, each confirmed against a real script in the ROM:
    lock 0x6A (the Mart clerk's own script starts 6A 5A), faceplayer 0x5A,
    checkflag 0x2B <u16> (sinnohmap's courier blocks), setflag 0x29 <u16>,
    loadword 0x0F 00 <ptr4>, callstd 0x09 <type> (5 = yes/no, 4 = plain),
    compare 0x21 <var u16> <value u16>, goto_if 0x06 <cond> <ptr4>,
    giveitem 0x44 <item u16> <amount u16>, release 0x6C, end 0x02.

The flag: 0x4F1F. It is not one of the 2159 flags any script in the ROM references via setflag/clearflag/
checkflag, which is the best available evidence that it is free.

usage: python candynpc_patch.py <in.gba> <out.gba>
"""
import struct, sys

FREE = 0x00F53700                       # 5024 bytes of all-FF, zero inbound pointers (verified)
EVENTS = 0x052F304                       # map 8/6 MapEvents struct: nobj at +0, objects ptr at +4
OBJS = 0x052F294                         # the 4-object array itself
COUNT = 4
OBJ_SIZE = 24
RARE_CANDY = 68
CANDY_COUNT = 999                       # 0x03E7, the bag cap this build ships
GIVEN_FLAG = 0x4F1F
TILE = (8, 5)                            # one tile right of where it was first placed
LOCAL_ID = 5                             # the map's objects use 1-4
OBJ1 = bytes.fromhex("0213000009000400030a000000000000e87d200800000000")

CHARS = {c: 0xBB + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}
CHARS.update({c: 0xD5 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")})
CHARS.update({str(i): 0xA1 + i for i in range(10)})
CHARS.update({" ": 0x00, "?": 0xAC, ".": 0xAD, "!": 0xAB, ",": 0xB8})


def text(s):
    return bytes(CHARS[c] for c in s) + b"\xFF"


def build_script(script_addr, text_addrs):
    """Assemble the NPC's script; `text_addrs` gives the address of each string."""
    s = bytearray()
    at = {}
    s += bytes((0x6A, 0x5A))                                  # lock, faceplayer
    s += bytes((0x2B,)) + struct.pack("<H", GIVEN_FLAG)       # checkflag
    s += bytes((0x06, 0x01)) + b"\0\0\0\0"
    at["again"] = len(s) - 4
    s += bytes((0x0F, 0x00)) + b"\0\0\0\0"                    # loadword 0, question
    at["q"] = len(s) - 4
    s += bytes((0x09, 0x05))                                  # callstd MSGBOX_YESNO
    s += bytes((0x21, 0x0D, 0x80, 0x00, 0x00))                # compare VAR_RESULT, 0
    s += bytes((0x06, 0x01)) + b"\0\0\0\0"                    # goto_if eq -> deny
    at["deny"] = len(s) - 4
    s += bytes((0x44,)) + struct.pack("<HH", RARE_CANDY, CANDY_COUNT)   # giveitem
    s += bytes((0x29,)) + struct.pack("<H", GIVEN_FLAG)       # setflag
    s += bytes((0x0F, 0x00)) + b"\0\0\0\0"                    # loadword 0, "enjoy"
    at["done"] = len(s) - 4
    s += bytes((0x09, 0x04, 0x6C, 0x02))                      # callstd 4, release, end
    again = len(s)
    s += bytes((0x0F, 0x00)) + struct.pack("<I", text_addrs["again"])
    s += bytes((0x09, 0x04, 0x6C, 0x02))
    deny = len(s)
    s += bytes((0x0F, 0x00)) + struct.pack("<I", text_addrs["deny"])
    s += bytes((0x09, 0x04, 0x6C, 0x02))
    for key, off in (("q", at["q"]), ("done", at["done"])):
        struct.pack_into("<I", s, off, text_addrs[key])
    struct.pack_into("<I", s, at["again"], script_addr + again)
    struct.pack_into("<I", s, at["deny"], script_addr + deny)
    return bytes(s)


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
    script_addr = 0x08000000 + script_off
    strings = {"q": text("Want 999 Rare Candies?"),
               "done": text("Here you go!"),
               "again": text("I have already given you my stash."),
               "deny": text("Come back if you want them.")}
    # the script's length does not depend on the text addresses, so lay the texts out first
    text_addrs, cursor = {}, script_off + len(build_script(script_addr, {k: 0 for k in strings}))
    cursor = (cursor + 3) & ~3
    for key in ("q", "done", "again", "deny"):
        text_addrs[key] = 0x08000000 + cursor
        cursor += len(strings[key])
    script = build_script(script_addr, text_addrs)
    struct.pack_into("<I", new, 16, script_addr)

    end = cursor
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:FREE + COUNT * OBJ_SIZE] = old
    rom[FREE + COUNT * OBJ_SIZE:script_off] = bytes(new)
    rom[script_off:script_off + len(script)] = script
    pos = (script_off + len(script) + 3) & ~3
    for key in ("q", "done", "again", "deny"):
        rom[pos:pos + len(strings[key])] = strings[key]
        pos += len(strings[key])
    rom[EVENTS] = COUNT + 1
    struct.pack_into("<I", rom, EVENTS + 4, 0x08000000 + FREE)
    open(outp, "wb").write(rom)
    print("objects -> 0x%08X (%d entries); new object localId=%d gfx=%d at %s" % (
        0x08000000 + FREE, COUNT + 1, LOCAL_ID, new[1], TILE))
    print("script @0x%08X (%d bytes), texts to 0x%08X; flag 0x%04X, %d candies" % (
        script_addr, len(script), 0x08000000 + end, GIVEN_FLAG, CANDY_COUNT))
    print("  script bytes:", script.hex())


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
