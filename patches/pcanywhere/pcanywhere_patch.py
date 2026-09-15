"""PC anywhere (Hyper Emerald v5.7). Apply after the trainerhide build.
usage: python pcanywhere_patch.py <in.gba> <out.gba>

Hold B and press SELECT in the overworld to open the PC: Someone's / Lanette's PC (Pokemon storage), your own PC
(item storage, mailbox), Hall of Fame, Log off - the game's own menus.

Why a copy of the PC script: the game's PC script (0x08271D92) starts with special 0xD9 (DoPCTurnOnEffect) and its
Log off branch runs special 0xDA (DoPCTurnOffEffect). Both redraw the map tile the player is facing as a switched
on/off PC, which is right in front of a real PC but would stamp a solid PC tile into the path anywhere else. This
patch copies the menu part of that script into free space - same messages, same specials for the storage system,
player PC and Hall of Fame, same "Accessed Someone's/Lanette's PC" subroutines - with every internal jump
relocated to the copy, and replaces the boot-up and log-off steps with just the PC sounds. The original script is
untouched, so real PCs behave as before.

Changes: the field-input trampoline literal now points at our hook (which passes through to the previous chain
head), plus code and the script copy in free space.
"""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD9DE8
BASE = 0x08000000 + FREE
FIELD_LITERAL = 0x9C018
PC_SCRIPT = 0x271D92
# vanilla blocks (file offsets) of the PC menu: [start, end)
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
JUMP_OPS = {0x04: 1, 0x05: 1, 0x06: 2, 0x07: 2}     # opcode -> offset of the pointer operand
SIZES = {0x02: 1, 0x03: 1, 0x04: 5, 0x05: 5, 0x06: 6, 0x07: 6, 0x09: 2, 0x0F: 6, 0x19: 5, 0x21: 5, 0x25: 3, 0x27: 1,
         0x2B: 3, 0x2F: 3, 0x66: 1, 0x67: 5}


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert bytes(rom[PC_SCRIPT:PC_SCRIPT + len(EXPECTED)]) == EXPECTED, "PC script differs from the analysed one"
    assert rom[FIELD_LITERAL - 4:FIELD_LITERAL] == bytes.fromhex("004b1847"), "field-input trampoline missing"
    prev = struct.unpack_from("<I", rom, FIELD_LITERAL)[0]
    assert prev & 1 and 0x08F00000 < prev < 0x09000000, "unexpected field hook %08X" % prev

    src = open(os.path.join(HERE, "pcanywhere.s"), encoding="ascii").read()

    def assemble(script_addr):
        code = bytes(Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(
            src.replace("SCRIPT_ADDR", "0x%08X" % script_addr).replace("NEXT_HOOK", "0x%08X" % prev), BASE)[0])
        bad = [i for i in Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(code, BASE) if i.size == 4 and i.mnemonic != "bl"]
        assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
        return code

    code_len = (len(assemble(BASE)) + 3) & ~3
    script_base = BASE + code_len
    # lay out: entry | main | access | player | storage | hof | logoff
    entry = bytes((LOCKALL, PLAYSE, SE_PC_ON, 0, GOTO)) + b"\0\0\0\0"
    order = ["main", "access", "player", "storage", "hof"]
    offs = {"entry": 0}
    pos = len(entry)
    for name in order:
        offs[name] = pos
        pos += BLOCKS[name][1] - BLOCKS[name][0]
    offs["logoff"] = pos
    logoff = bytes((PLAYSE, SE_PC_OFF, 0, RELEASEALL, END))
    new_addr = {0x08000000 + BLOCKS[n][0]: script_base + offs[n] for n in order}
    new_addr[0x08000000 + OLD_LOGOFF] = script_base + offs["logoff"]

    script = bytearray(entry)
    struct.pack_into("<I", script, 5, new_addr[0x08000000 + BLOCKS["main"][0]])
    for name in order:
        a, b = BLOCKS[name]
        blk = bytearray(rom[a:b])
        i = 0
        while i < len(blk):                                  # relocate every jump inside the copied block
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
    script += logoff
    assert b"\x25\xd9\x00" not in script and b"\x25\xda\x00" not in script, "PC on/off effect left in the copy"

    code = assemble(script_base)
    blob = code + bytes(code_len - len(code)) + bytes(script)
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    struct.pack_into("<I", rom, FIELD_LITERAL, BASE | 1)
    open(outp, "wb").write(rom)
    print("hook %d bytes @%08X -> chains to %08X; PC script copy %d bytes @%08X; end %08X" % (
        len(code), BASE, prev, len(script), script_base, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
