"""Messages in the mist (Hyper Emerald v5.7). Apply anywhere.
usage: python mistmsg_patch.py <in.gba> <out.gba>

A bug of the hack's own, in the untouched ROM too. Its field message box is see-through. ShowFieldMessage's task is
chosen at 0x08DEDF2E: the hack's own (0x08DEDE7A), unless the flash level is not 0 (a cave that needs Flash) or
its option byte (SaveBlock2 + 0xE68) is set - then the game's Task_DrawFieldMessage and a plain box. The hack's
task calls 0x08DEDE42, which puts WIN0 over the box and writes BLDCNT 0x1E41 / BLDALPHA 0x0710 straight into the
registers; when the message goes away 0x08DEDED4 writes 0x1E40 / 0x080C back.
BLDALPHA is shared with the weather's see-through sprites. In mist (fog: weather 6 and 9, Rusturf Tunnel for one;
the underwater haze: 10, and 14 on the underwater maps) the fog turned nearly solid for as long as a message was
up and the map was gone; and
0x080C is the fog's own setting, so after any message ash and sandstorm (16 / 0) and the underwater haze (4 / 16)
were drawn with the fog's until the map was loaded again.
Changes, all inside that blob (the same bytes in the original ROM) but for the new code (mistmsg.s):
  * the flash-level test in the task chooser (0x08DEDF34) and in the routine that puts the text colours in front
    of a message (0x08DEDF04): both load gSaveBlock1Ptr from one literal (0x08DEE028, used by nothing else), which
    now holds plain_box, and their `ldr r5, [r5]; adds r5, #0x30; ldrb r5, [r5]` becomes a `bl` to the blob's own
    `bx r5` and a no-op. plain_box answers as the flash level did, and "plain" in mist too (GetCurrentWeather 6, 9,
    10 or 14: the weathers whose sprites are see-through at less than full strength, but for the clouds of the one
    cloudy map; ash and sandstorm draw theirs at full strength);
  * the end-of-message routine's `ldr r2, =0x080C1E40; movs r1, #0xf0; str r2, [r3, #0x10]` (0x08DEDEE4) becomes
    `bl restore; movs r1, #0xf0`: BLDCNT / BLDALPHA from the game's copy of the registers (0x03000868).
The hack's older copies of the same code (0x094A2C34, 0x09811A.., 0x09F004..) are dead and left alone.
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
sys.path.insert(0, os.path.join(HERE, "..", "dexnavseen"))
import sinnohmap_patch as SM                    # the Thumb check
from dexnavseen_patch import bl

FREE = 0x00FF7704                               # in the unreferenced 0xFF run 0x08FF6600..0x08FFD5A0, between the two
FREE_END = 0x00FF7784                           # data words that happen to read 0x08FF7703 and 0x08FF7785
BASE = 0x08000000 + FREE

HOOK, HOOK_TARGET = 0x080981BC, 0x08DEDF2F      # ShowFieldMessage's CreateTask: ldr r0, =chooser; bx r0
CHOOSER, EXPANDER = 0x08DEDF34, 0x08DEDF04      # ldr r5, =gSaveBlock1Ptr; ldr r5, [r5]; adds r5, #0x30; ldrb r5, [r5]; cmp r5, #0; bne
SB1_LIT = 0x08DEE028
VENEER_R5 = 0x08DEDFA2                          # bx r5
CLOSE, CLOSE_WRITE, CLOSE_LIT = 0x08DEDED4, 0x08DEDEE4, 0x08DEE01C
GET_WEATHER = 0x080AC30C


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    o = lambda a: a - 0x08000000
    u32 = lambda a: struct.unpack_from("<I", rom, o(a))[0]
    at = lambda a, hexs: bytes(rom[o(a):o(a) + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    def loaders(lit):
        """the pc-relative ldr's in the blob that read this literal"""
        out = []
        for a in range(0x08DEDE1E, 0x08DEDFA4, 2):
            op = struct.unpack_from("<H", rom, o(a))[0]
            if op & 0xF800 == 0x4800 and ((a + 4) & ~3) + (op & 0xFF) * 4 == lit:
                out.append(a)
        return out

    # the hack's message box code, as it is
    assert at(HOOK, "00480047") and u32(HOOK + 4) == HOOK_TARGET, "ShowFieldMessage does not go to the hack's task chooser"
    assert at(CHOOSER, "3c4d2d6830352d78002d06d1") and at(EXPANDER, "484d2d6830352d78002d06d1"), \
        "the flash-level tests changed (already applied?)"
    assert u32(SB1_LIT) == 0x03005D8C and loaders(SB1_LIT) == [EXPANDER, CHOOSER], "the gSaveBlock1Ptr literal has other users"
    assert at(VENEER_R5, "2847"), "the blob's bx r5 moved"
    assert at(CLOSE, "ff22444b196810b500f010fee03a1a72") and at(CLOSE_WRITE, "4d4af0211a61"), \
        "the end-of-message routine changed (already applied?)"
    assert u32(CLOSE_LIT) == 0x080C1E40 and loaders(CLOSE_LIT) == [CLOSE_WRITE], "the routine's register constant changed"
    assert u32(0x08DEDFA4) == 0x04000040 and u32(0x08DEDFF4) == 0x07101E41, "the blob's data changed"
    assert at(GET_WEATHER, "0248da21c90040180078704754840302"), "GetCurrentWeather changed"

    src = open(os.path.join(HERE, "mistmsg.s"), encoding="ascii").read()
    code, dis = SM.thumb(src, BASE)
    funcs = [i.address for i in dis if i.mnemonic == "push" and "lr" in i.op_str]
    assert len(funcs) == 1 and dis[0].address == BASE and dis[0].mnemonic == "ldr", "expected restore first, then plain_box"
    restore, plain_box = BASE, funcs[0]
    end = FREE + len(code)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not BASE <= v < 0x08000000 + end, "%08X already points into the target (%08X)" % (0x08000000 + k, v)
    rom[FREE:end] = code

    struct.pack_into("<I", rom, o(SB1_LIT), plain_box | 1)
    for site in (CHOOSER, EXPANDER):            # ldr r5, =plain_box (as it stands); bl <bx r5>; mov r8, r8
        rom[o(site + 2):o(site + 8)] = bl(site + 2, VENEER_R5) + bytes.fromhex("c046")
    rom[o(CLOSE_WRITE):o(CLOSE_WRITE) + 6] = bl(CLOSE_WRITE, restore) + bytes.fromhex("f021")    # ...; movs r1, #0xf0
    open(outp, "wb").write(rom)
    print("restore %08X, plain_box %08X, end %08X; flash-level tests at %08X and %08X, the register write at %08X"
          % (restore, plain_box, 0x08000000 + end, CHOOSER, EXPANDER, CLOSE_WRITE))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
