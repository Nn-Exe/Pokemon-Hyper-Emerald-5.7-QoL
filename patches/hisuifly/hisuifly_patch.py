"""Flying from the Hisui map again, once Volo's part of the story is over (Hyper Emerald v5.7):
python hisuifly_patch.py in.gba out.gba

hisuimap took flying off the Hisui map on 2026-10-08 (HISUI_FLY = False): Mingyao's fly blocks check nothing, so A on
a red square took you anywhere in Hisui ahead of the story. The user, 2026-10-22: "can we add it back but make sure
it check if we already completed Hisui quest at finding Volo but before skitty Cat".

The map's fly table already gives each place a flag that must be set (fly_target refuses without it, draw_name greys
the name), as Sinnoh's courier table does. This puts the five places back, each needing flag 0x431E. Data only.

Why 0x431E, read from the ROM (tools/romdata/scripts.py, dis.py): Volo's script in 37/108 sets 0x4315 when he is
beaten and sends you to Coronet Highlands; 0x431E is the trigger at base camp (37/104, 12,19) where Rei and Cogita
tell you the news, the Journal's "Volo is beaten. Return to base camp" step. Mingyao's own menu (multichoice 137)
opens at Coronet Highlands (0x0989B177) and at base camp (0x0989A9FC) only once 0x431E is set - before it, at
Coronet Highlands she flies you straight to base camp - and at the other three after 0x4315. So from 0x431E on her
menu takes you anywhere from every one of her spots, and the map offers nothing she does not. The Kitty / nameless
stone steps (0x4322, 0x4323) come after it.
"""
import struct, sys

H_FLY = 0x00FF544C                      # hisuimap's fly table: {key u8, pad, flag u16, block u32} x5, then 0xFF
REGION_FLY = 0x00FF54D8                 # REGION_HISUI's fly word (the record's fifth), the table's one pointer
FLAG = 0x431E                           # Rei and Cogita's report at base camp, after Volo
# (key = map number in group 37, Mingyao's block, the warp id it uses), in the table's order
PLACES = [(107, 0x0989AE6F, 0), (106, 0x0989AE80, 0), (105, 0x0989AE5E, 0), (103, 0x0989AE4D, 0),
          (104, 0x0989AE3C, 1)]


def table(first_key, flag):
    t = b"".join(struct.pack("<BBHI", n, 0, flag, blk) for n, blk, _ in PLACES) + b"\xFF"
    return bytes((first_key,)) + t[1:]


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    old = table(0xFF, 0)                                     # hisuimap with HISUI_FLY = False
    assert bytes(rom[H_FLY:H_FLY + len(old)]) == old, "the Hisui map's fly table is not hisuimap's no-fly one"
    word = struct.pack("<I", 0x08000000 + H_FLY)
    assert struct.unpack_from("<I", rom, REGION_FLY)[0] == 0x08000000 + H_FLY
    assert rom.count(word) == 1, "something else points at the fly table"
    for n, blk, warp in PLACES:                              # showmonpic 0x428 1 4; waitbuttonpress; hidemonpic;
        b = blk - 0x08000000                                 # warp 37.<n> <warp>
        assert bytes(rom[b:b + 12]) == bytes((0x75, 0x28, 0x04, 0x01, 0x04, 0x6D, 0x76, 0x39, 37, n, warp, 0)), \
            "Mingyao's block %08X changed" % blk
    new = table(PLACES[0][0], FLAG)
    rom[H_FLY:H_FLY + len(new)] = new
    open(outp, "wb").write(rom)
    print("Hisui map: %d fly stops back @%08X, each needing flag 0x%04X" % (len(PLACES), 0x08000000 + H_FLY, FLAG))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
