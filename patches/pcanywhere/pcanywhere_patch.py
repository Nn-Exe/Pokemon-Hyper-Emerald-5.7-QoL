"""PC in the SELECT popup (Hyper Emerald v5.7). Apply after the trainerhide build.
usage: python pcanywhere_patch.py <in.gba> <out.gba>

Press SELECT in the overworld, then B: the PC opens - Someone's / Lanette's PC (Pokemon storage), your own PC
(item storage, mailbox), Hall of Fame, Log off - the game's own menus. No item is needed. In the popup the d-pad
still uses your registered key items and SELECT closes it. The popup now always opens (also with zero or one
registered item), and shows a "B PC" line under the four slots.

Why a copy of the PC script: the game's PC script (0x08271D92) starts with special 0xD9 (DoPCTurnOnEffect) and its
Log off branch runs special 0xDA (DoPCTurnOffEffect). Both redraw the map tile the player is facing as a switched
on/off PC - right in front of a real PC, but a solid PC tile in your path anywhere else. The menu part of that script
is copied into free space with every jump relocated, and the boot-up and log-off steps become just the PC sounds.
Real PCs are untouched.

Changes to keyreg (the 4-slot popup): two branches made unconditional (always show the popup), the draw call
retargeted to a 5-line draw, and the popup task literal retargeted to a task that adds B = PC. Everything else is
new code and data in free space. No save data is used.
"""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD9DE8
BASE = 0x08000000 + FREE
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)

# ---- keyreg patch points (file offsets) and the bytes expected there ----
KR_COUNT0_BNE = 0xFD8EBE      # cmp r6,#0 ; bne have   -> b have   (show popup with zero items)
KR_COUNT1_BNE = 0xFD8EE4      # cmp r6,#1 ; bne popup  -> b popup  (show popup with one item)
KR_DRAW_BL = 0xFD8EF6         # bl draw_popup -> bl new_draw
KR_TASK_LIT = 0xFD9134        # .word popup_task|1 -> new_task|1
KR_EXPECT = {0xFD8EBC: "002e04d1", 0xFD8EE2: "012e03d1", 0xFD8EF6: "00f028f8", 0xFD9134: "dd8ffd08",
             0xFD91C4: "0001010e090f8000", 0xFD91CC: "797c7a7b"}
TEMPLATE = bytes([0, 1, 1, 14, 11, 15]) + struct.pack("<H", 0x80)   # bg0, x1, y1, 14x11 tiles, palette 15, base 0x80

# ---- vanilla PC script ----
PC_SCRIPT = 0x271D92
BLOCKS = {
    "main":    (0x271DAC, 0x271DBC),   # message "Which PC should be accessed?"; special 0x109; waitstate; goto access
    "access":  (0x271DBC, 0x271DF9),   # copyvar 0x8000, RESULT; switch -> storage / player / hof / logoff
    "player":  (0x271DF9, 0x271E0E),   # "Accessed <player>'s PC"; special 0xFD (PlayerPC); goto main
    "storage": (0x271E0E, 0x271E35),   # Someone's/Lanette's PC; special 0x3F (storage system); goto main
    "hof":     (0x271E54, 0x271E6A),   # checkflag; special 0x10A (Hall of Fame PC); goto access
}
OLD_LOGOFF = 0x271E47
EXPECTED = bytes.fromhex(
    "69160480000025d9002f04000f005a262708090405ac1d270802676f262708662509012705bc1d2708021900800d8021008000000601"
    "0e1e270821008001000601f91d270821008002000601541e270821008003000601471e27082100807f000601471e2708022f02000f00"
    "c2262708090425fd002705ac1d2708022f02002bab080700351e27082bab0807013e1e27080f00a32627080904253f002705ac1d2708"
    "020f008c2627080904030f00d426270809040316048000002f030025da006b022b64080600471e27082f0200250a012705bc1d270802")
LOCKALL, PLAYSE, GOTO, RELEASEALL, END = 0x69, 0x2F, 0x05, 0x6B, 0x02
SE_PC_ON, SE_PC_OFF = 4, 3
JUMP_OPS = {0x04: 1, 0x05: 1, 0x06: 2, 0x07: 2}
SIZES = {0x02: 1, 0x03: 1, 0x04: 5, 0x05: 5, 0x06: 6, 0x07: 6, 0x09: 2, 0x0F: 6, 0x19: 5, 0x21: 5, 0x25: 3, 0x27: 1,
         0x2B: 3, 0x2F: 3, 0x66: 1, 0x67: 5}


def pc_script_copy(rom, base):
    entry = bytes((LOCKALL, PLAYSE, SE_PC_ON, 0, GOTO)) + b"\0\0\0\0"
    order = ["main", "access", "player", "storage", "hof"]
    offs, pos = {}, len(entry)
    for name in order:
        offs[name] = pos
        pos += BLOCKS[name][1] - BLOCKS[name][0]
    new_addr = {0x08000000 + BLOCKS[n][0]: base + offs[n] for n in order}
    new_addr[0x08000000 + OLD_LOGOFF] = base + pos
    script = bytearray(entry)
    struct.pack_into("<I", script, 5, new_addr[0x08000000 + BLOCKS["main"][0]])
    for name in order:
        a, b = BLOCKS[name]
        blk = bytearray(rom[a:b])
        i = 0
        while i < len(blk):
            op = blk[i]
            assert op in SIZES, "unexpected command 0x%02X in %s" % (op, name)
            if op in JUMP_OPS:
                o = i + JUMP_OPS[op]
                target = struct.unpack_from("<I", blk, o)[0]
                if target in new_addr:
                    struct.pack_into("<I", blk, o, new_addr[target])
                else:
                    assert target in (0x08271E35, 0x08271E3E), "jump to %08X would leave the copy" % target
            i += SIZES[op]
        assert i == len(blk), "block %s does not end on a command boundary" % name
        script += blk
    script += bytes((PLAYSE, SE_PC_OFF, 0, RELEASEALL, END))
    assert b"\x25\xd9\x00" not in script and b"\x25\xda\x00" not in script
    return bytes(script)


def thumb(src, addr):
    code = bytes(ks.asm(src, addr)[0])
    bad = [i for i in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, addr) if i.size == 4 and i.mnemonic != "bl"]
    assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
    return code


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert bytes(rom[PC_SCRIPT:PC_SCRIPT + len(EXPECTED)]) == EXPECTED, "PC script differs from the analysed one"
    for off, hx in KR_EXPECT.items():
        assert rom[off:off + len(hx) // 2].hex() == hx, "keyreg bytes at %X differ (expected %s)" % (off, hx)

    src = open(os.path.join(HERE, "pcanywhere.s"), encoding="ascii").read()

    def code_for(t, p, s):
        return thumb(src.replace("TEMPLATE_ADDR", "0x%08X" % t).replace("PCLINE_ADDR", "0x%08X" % p)
                        .replace("PCSCRIPT_ADDR", "0x%08X" % s), BASE)

    code = code_for(BASE, BASE, BASE)
    code_len = (len(code) + 3) & ~3
    template_addr = BASE + code_len
    pcline = bytes((0xBC, 0x00, 0xCA, 0xBD, 0xFF))            # "B PC"
    pcline_addr = template_addr + len(TEMPLATE)
    script_addr = (pcline_addr + len(pcline) + 3) & ~3
    script = pc_script_copy(rom, script_addr)
    code = code_for(template_addr, pcline_addr, script_addr)
    assert (len(code) + 3) & ~3 == code_len

    ins = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, BASE))
    new_draw = BASE
    new_task = next(i.address for i in ins if i.mnemonic == "push" and i.op_str == "{r4, r5, r6, r7, lr}")

    blob = bytearray(code) + bytes(code_len - len(code)) + TEMPLATE + pcline
    blob += bytes(script_addr - (BASE + len(blob))) + script
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob

    rom[KR_COUNT0_BNE:KR_COUNT0_BNE + 2] = thumb("b 0x08FD8ECA", 0x08000000 + KR_COUNT0_BNE)
    rom[KR_COUNT1_BNE:KR_COUNT1_BNE + 2] = thumb("b 0x08FD8EEE", 0x08000000 + KR_COUNT1_BNE)
    bl = bytes(ks.asm("bl 0x%08X" % new_draw, 0x08000000 + KR_DRAW_BL)[0])
    assert len(bl) == 4
    rom[KR_DRAW_BL:KR_DRAW_BL + 4] = bl
    struct.pack_into("<I", rom, KR_TASK_LIT, new_task | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X (draw %08X, task %08X), PC script copy %d bytes @%08X, end %08X" % (
        len(code), BASE, new_draw, new_task, len(script), script_addr, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
