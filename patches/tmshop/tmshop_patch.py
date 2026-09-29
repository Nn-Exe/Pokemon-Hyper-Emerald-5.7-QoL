"""Every TM, and the ability items, at the Lilycove Department Store (Hyper Emerald v5.7). Apply after partyedit.

The TM clerk on the store's TM floor (map 13/19, object 5 at 9,6; script 0x0821FE2C) runs `pokemart 0x0830AD06`,
an 8-TM list. This writes a new list - the Ability Patch and the Ability Pill, then TM01-100 and TM109-120, in
number order - into free space and repoints the one word at 0x0821FE35 (the pokemart argument; nothing else
references the old list). His script, text and the TMs' prices are unchanged; the old list stays where it is.
The two ability items cost 0, and the purchase check below soft-resets on a total under 50 per item (a 0 price
did), so their price in the item table becomes 50. That is also what a shop pays back for one: 25.

The hack checks every purchase (BuyMenuTryMakePurchase -> 0x096FFF00): each item in the shop list must have its
bit set in a table read backwards from 0x09E0FE5F (bit i&7 of the byte at 0x09E0FE5F - (i>>3)), or it jumps to
address 0 - the soft reset that stopped the Rare Candy shop. Only that check reads the table. The TMs listed are
already in it (TM101-108 are not, so they are left out); the two ability items are not, and their bits are set.

usage: python tmshop_patch.py <in.gba> <out.gba>
"""
import struct, sys

ARG = 0x21FE35                          # pokemart's list argument in the clerk's script (unaligned)
OLD_LIST = 0x0830AD06
FREE = 0xF54400                         # after hypertrain (..0x08F543CD); hmfree starts at 0x08F54500
SELLABLE = 0x09E0FE5F                   # the hack's per-item "may be sold" bits, indexed backwards
ITEMS_PTR = 0x1C8                       # ROM header: item table, 44-byte entries
TM01, TM100, TM109, TM120 = 378, 477, 486, 497
TMS = list(range(TM01, TM100 + 1)) + list(range(TM109, TM120 + 1))
ABILITY_ITEMS = {741: "Ability Patch", 646: "Ability Pill"}
ABILITY_PRICE = 50                      # the lowest the purchase check lets through


def u16(rom, o): return struct.unpack_from("<H", rom, o)[0]
def u32(rom, o): return struct.unpack_from("<I", rom, o)[0]


def gen3(s):
    out = bytearray()
    for c in s:
        if "A" <= c <= "Z": out.append(0xBB + ord(c) - 65)
        elif "a" <= c <= "z": out.append(0xD5 + ord(c) - 97)
        elif c == " ": out.append(0)
        else: raise ValueError(c)
    return bytes(out) + b"\xFF"


def sellable_at(item):
    return SELLABLE - 0x08000000 - (item >> 3), 1 << (item & 7)


def sellable(rom, item):
    o, bit = sellable_at(item)
    return bool(rom[o] & bit)


def main(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000, "not the 32 MB BPEE ROM"
    assert rom[ARG - 1] == 0x86, "the clerk's script no longer has pokemart at %08X" % (0x08000000 + ARG - 1)
    assert u32(rom, ARG) == OLD_LIST, "pokemart list is %08X, expected %08X" % (u32(rom, ARG), OLD_LIST)

    items = u32(rom, ITEMS_PTR) - 0x08000000
    for i in TMS:
        e = items + i * 44
        name = bytes(rom[e:e + 3])
        assert name == bytes((0xCE, 0xC7, 0x00)), "item %d is not a TM (name starts %s)" % (i, name.hex())
        assert rom[e + 26] == 3, "item %d is not in the TM pocket" % i
        assert u16(rom, e + 16) > 0, "item %d has no price" % i
        assert sellable(rom, i), "item %d is not in the hack's sellable table: buying it would soft-reset" % i
    for i, name in ABILITY_ITEMS.items():
        e = items + i * 44
        want = gen3(name)
        assert bytes(rom[e:e + len(want)]) == want, "item %d is not the %s" % (i, name)
        assert not sellable(rom, i), "item %d is already sellable" % i
        assert u16(rom, e + 16) == 0, "item %d already has a price" % i

    wares = list(ABILITY_ITEMS) + TMS
    data = b"".join(struct.pack("<H", i) for i in wares) + b"\x00\x00"
    assert FREE + len(data) <= 0xF54500, "list runs into hmfree's space"
    assert all(b == 0xFF for b in rom[FREE:FREE + len(data)]), "target region is not free"
    rom[FREE:FREE + len(data)] = data
    struct.pack_into("<I", rom, ARG, 0x08000000 + FREE)
    for i in ABILITY_ITEMS:
        o, bit = sellable_at(i)
        rom[o] |= bit
        struct.pack_into("<H", rom, items + i * 44 + 16, ABILITY_PRICE)
    open(outp, "wb").write(rom)
    print("list @%08X..%08X (%d items), pokemart arg @%08X -> %08X, sellable bits set and price %d for %s" % (
        0x08000000 + FREE, 0x08000000 + FREE + len(data), len(wares), 0x08000000 + ARG, 0x08000000 + FREE, ABILITY_PRICE,
        ", ".join("%d @%08X" % (i, 0x08000000 + sellable_at(i)[0]) for i in ABILITY_ITEMS)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
