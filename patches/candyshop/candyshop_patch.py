"""Lilycove Dept. Store decoration clerk (map 13/20, obj 4, script 0x0822000A) -> Rare Candy shop at 1 yen.
usage: python candyshop_patch.py <in.gba> <out.gba>"""
import struct, sys
RARE_CANDY = 68
def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0x22000A:0x220016] == bytes.fromhex("6a5a67212a27086688240022"), "clerk script not as expected"
    assert struct.unpack_from("<H", rom, 0x220024)[0] == 66, "decoration list not as expected"
    assert struct.pack("<I", 0x08220024) not in rom[:0x220000] + rom[0x220040:], "list referenced elsewhere"
    rom[0x220012] = 0x86                                   # pokemartdecoration2 -> pokemart
    struct.pack_into("<HH", rom, 0x220024, RARE_CANDY, 0)  # item list: Rare Candy, end
    base = 0xFC2C7C
    assert struct.unpack_from("<H", rom, base + RARE_CANDY * 44 + 16)[0] == 4800
    struct.pack_into("<H", rom, base + RARE_CANDY * 44 + 16, 1)   # price 4800 -> 1
    open(outp, "wb").write(rom)
    print("patched: clerk sells Rare Candy at 1")
if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
