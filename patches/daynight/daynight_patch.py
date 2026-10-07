"""Day/Night: On / Off in the Option menu (Hyper Emerald v5.7). Apply after rbutton and repelfix.
usage: python daynight_patch.py <in.gba> <out.gba>

The hack colours the screen by the hour. It does it at the last moment: TransferPlttBuffer (0x080A19C0), which
copies the game's finished palettes to the screen every frame, jumps at 0x080A19E0 into the hack's routine
0x08CFE3E0. That routine picks a mask by gLocalTime's hour (before 4: every channel halved; 4-5: red and green
kept; 6-16: nothing; 17-18: red kept; 19-21: red and blue kept; 22 on: blue kept), stores the time of day 0-5 at
0x0203C000, and copies the 32 palettes itself, halving the channels outside the mask - unless the map is indoors
(map type 0, 4, 8, 9) or its own byte 0x02021685 says no, in which case it does the plain copy. The palettes in RAM
are never changed, only what reaches the screen.

Off makes that routine take its plain copy: the two instructions that read 0x02021685 call tint_gate, which also
answers "no" when bit 4 of SaveBlock2+0x15 is set. Nothing else changes - the clock, the time of day at 0x0203C000
and everything that depends on the hour (evolutions, events) run on - so On shows the right colours for the hour
again from the next frame.

The switch is the Option menu's 7th row, where "Cancel" was (B leaves and saves, as it always has; A no longer
does anything on that row):
* sOptionMenuItemsNames[6] -> "Day/Night";
* DrawOptionMenuTexts draws the row's On / Off after the labels (its CopyWindowToVram call goes through a veneer);
* Task_OptionMenuProcessInput: its "row above 5: return" branch goes to case6 (a veneer again), which flips the
  bit on Left / Right and redraws; the A-on-row-6 exit is taken out.
The two veneers sit in the body of ButtonMode_ProcessInput, dead since rbutton replaced that function with a
trampoline. The bit: all 21 accesses to SaveBlock2+0x14/0x15 in the ROM use bits 0-3 of 0x15 only (sound, battle
style, battle scene, region map zoom; the hack's 0x08C60F20 sets battle style), and the menu saves with bitfield
writes, so bit 4 is kept. New and old saves have it 0 = On.
"""
import os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sinnohmap"))
import sinnohmap_patch as SM                    # the Thumb check

FREE, FREE_END = 0x00FF7240, 0x00FF7700         # after repelfix, in the unreferenced 0xFF run
TINT_SITE = 0x00CFE452                          # ldr r0, =0x02021685; ldrb r1, [r0]; cmp r1, #0; bne plain
NAMES = 0x0055C664                              # sOptionMenuItemsNames[7]
A_EXIT = 0x000BA88C                             # cmp r0, #6; beq +0; b return; b exit
GT5 = 0x000BA934                                # cmp r1, #5; bls table; b return
TEXTS_BL = 0x000BB144                           # DrawOptionMenuTexts: bl CopyWindowToVram
BM_INPUT = 0x000BAFCC                           # ButtonMode_ProcessInput: rbutton's trampoline, then dead code
VENEERS = BM_INPUT + 8
LABEL = "Day/Night"


def text(s):
    out = bytearray()
    for ch in s:
        out.append(0xBB + ord(ch) - 65 if ch.isupper() else 0xD5 + ord(ch) - 97 if ch.islower() else {"/": 0xBA, " ": 0}[ch])
    return bytes(out) + b"\xff"


def bl(site, target):
    off = target - (site + 4)
    assert abs(off) < 0x400000 and off % 2 == 0
    return struct.pack("<HH", 0xF000 | ((off >> 12) & 0x7FF), 0xF800 | ((off >> 1) & 0x7FF))


def b(site, target):
    off = target - (site + 4)
    assert -2048 <= off < 2048 and off % 2 == 0
    return struct.pack("<H", 0xE000 | ((off >> 1) & 0x7FF))


def build(inp, outp):
    with open(inp, "rb") as f:
        rom = bytearray(f.read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    at = lambda o, hexs: bytes(rom[o:o + len(bytes.fromhex(hexs))]) == bytes.fromhex(hexs)

    assert at(TINT_SITE, "2848017800 29d9d1"), "the tint routine is not as expected"
    assert struct.unpack_from("<I", rom, TINT_SITE + 0xA2)[0] == 0x02021685
    assert at(0x000A19E0, "0c490847") and struct.unpack_from("<I", rom, 0x000A1A14)[0] == 0x08CFE3E1, "TransferPlttBuffer's hook"
    assert struct.unpack_from("<I", rom, NAMES + 24)[0] == 0x085EE5C1 and at(0x005EE5C1, "bdd5e2d7d9e0ff"), "the 7th row is not Cancel"
    assert at(A_EXIT, "062800d0e3e00ce0"), "Task_OptionMenuProcessInput: the A check"
    assert at(GT5, "052900d98fe0"), "Task_OptionMenuProcessInput: the row switch"
    assert at(TEXTS_BL - 4, "01200321" "48f788fa"), "DrawOptionMenuTexts"
    assert at(BM_INPUT, "004b1847") and at(VENEERS, "d18d102008400028" "0cd0012b06d8581c"), "ButtonMode_ProcessInput's dead body"

    with open(os.path.join(HERE, "daynight.s"), encoding="ascii") as f:
        chunks = re.split(r"^@@ (\w+)\n", f.read(), flags=re.M)
    src = dict(zip(chunks[1::2], chunks[2::2]))
    order = ("gate", "draw", "tail", "case6")
    addr, pos = {}, FREE
    for name in order:                          # every chunk's size is the same whatever DRAW_ADDR is
        addr[name] = 0x08000000 + pos
        pos += len(SM.thumb(src[name].replace("DRAW_ADDR", "0x08000001"), addr[name])[0])
        assert pos % 4 == 0, "%s: not a multiple of 4 bytes, its literals would be misaligned" % name
    blob = b""
    for name in order:
        code, dis = SM.thumb(src[name].replace("DRAW_ADDR", "0x%08X" % (addr["draw"] | 1)), addr[name])
        words = {int(w, 16) for w in re.findall(r"\.word\s+(0x[0-9A-Fa-f]+)", src[name].replace("DRAW_ADDR", "0x%08X" % (addr["draw"] | 1)))}
        for i in dis:                           # each pc-relative load must hit one of the chunk's own literals
            if i.mnemonic == "ldr" and "pc" in i.op_str:
                t = ((i.address + 4) & ~3) + (int(i.op_str.split("#")[1].rstrip("]"), 16) if "#" in i.op_str else 0) - addr[name]
                assert struct.unpack_from("<I", code, t)[0] in words, "%s: a load misses its literal" % name
        blob += code
    label = 0x08000000 + FREE + len(blob)
    blob += text(LABEL)
    end = FREE + len(blob)
    assert end <= FREE_END and set(rom[FREE:end]) == {0xFF}, "target region not free"
    for k in range(0, len(rom), 4):
        v = struct.unpack_from("<I", rom, k)[0]
        assert not 0x08000000 + FREE <= v < 0x08000000 + end, "%08X already points into the target" % (0x08000000 + k)
    rom[FREE:end] = blob

    rom[TINT_SITE:TINT_SITE + 4] = bl(0x08000000 + TINT_SITE, addr["gate"])
    struct.pack_into("<I", rom, NAMES + 24, label)
    rom[A_EXIT + 2:A_EXIT + 4] = bytes.fromhex("c046")                      # A on the 7th row: nothing
    v_tail, v_case6 = 0x08000000 + VENEERS, 0x08000000 + VENEERS + 8
    rom[VENEERS:VENEERS + 16] = (bytes.fromhex("004b1847") + struct.pack("<I", addr["tail"] | 1) +
                                 bytes.fromhex("004b1847") + struct.pack("<I", addr["case6"] | 1))
    rom[GT5 + 4:GT5 + 6] = b(0x08000000 + GT5 + 4, v_case6)
    rom[TEXTS_BL:TEXTS_BL + 4] = bl(0x08000000 + TEXTS_BL, v_tail)
    with open(outp, "wb") as f:
        f.write(rom)
    print("daynight: code %08X..%08X (gate %08X, draw %08X, tail %08X, case6 %08X), label %08X, veneers %08X" % (
        0x08000000 + FREE, 0x08000000 + end, addr["gate"], addr["draw"], addr["tail"], addr["case6"], label, v_tail))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
