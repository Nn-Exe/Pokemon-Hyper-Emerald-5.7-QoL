"""In-party nature changer (Hyper Emerald v5.7). Apply after the gfxfix build.
usage: python naturemenu_patch.py <in.gba> <out.gba>

Adds a "Nature" option to the party menu's action list, beside the relearner's "Moves". Choosing it stores the
party slot in VAR_0x8004, drops a token in VAR_0x8006 and closes the menu; the field-input hook consumes the token
on the next overworld frame and runs a script that shows the game's own nature list (multichoice 0x7C) and calls
our apply routine. That routine range-checks the choice (pressing B gives 0x7F) and hands it to the hack's nature
routine at 0x08FF0E01 - the same one the Mint NPC in the Rustboro Trainer's School uses - which writes the nature
into the unused byte at mon+0x1F (keeping bit 7) and recalculates the stats. No personality-value edit, so
shininess, ability, gender and the Pokemon's identity are untouched.

Changes: a 35-entry copy of the party option table (the relearner's 34 plus "Nature") with the three code literals
repointed, the field-action builder trampoline repointed to a builder that appends both options, and the
field-input trampoline chained in front of the L-repel hook. Everything else is new code in free space."""
import struct, sys, os
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = 0x00FD9DE8                       # after the movefix strings (free to 0xFE0000)
BASE = 0x08000000 + FREE
OLD_TABLE = 0x08FD9B8C                  # relearner's 34-entry table
TABLE_LITERALS = (0x1B32F8, 0x1B37C8, 0x1B37F8)
BUILDER_TRAMPOLINE = 0x1B3518           # ldr r3,[pc]; bx r3; .word relearner_builder|1
FIELD_LITERAL = 0x9C018                 # field-input trampoline target (currently the L-repel hook)
MULTICHOICE_NATURES = 0x7C              # list id the Mint NPC uses
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def gen3(s):
    out = bytearray()
    for c in s:
        if 'A' <= c <= 'Z': out.append(0xBB + ord(c) - 65)
        elif 'a' <= c <= 'z': out.append(0xD5 + ord(c) - 97)
        elif c == ' ': out.append(0)
        elif c == '?': out.append(0xAC)
        elif c == '!': out.append(0xAB)
        elif c == '.': out.append(0xAD)
        elif c == ',': out.append(0xB8)
        elif c == "'": out.append(0xB4)
        else: raise ValueError(c)
    out.append(0xFF)
    return bytes(out)


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    for lit in TABLE_LITERALS:
        assert struct.unpack_from("<I", rom, lit)[0] == OLD_TABLE, "table literal @%X is not the relearner's" % lit
    assert rom[BUILDER_TRAMPOLINE:BUILDER_TRAMPOLINE + 4] == bytes.fromhex("004b1847"), "builder trampoline missing"
    prev_builder = struct.unpack_from("<I", rom, BUILDER_TRAMPOLINE + 4)[0]
    assert prev_builder & 1 and 0x08F00000 < prev_builder < 0x09000000, "unexpected builder %08X" % prev_builder
    prev_field = struct.unpack_from("<I", rom, FIELD_LITERAL)[0]
    assert prev_field & 1 and 0x08F00000 < prev_field < 0x09000000, "unexpected field hook %08X" % prev_field
    # the hack's nature routine must still start with the sequence we analysed (reads VAR_0x8004 / VAR_0x8005)
    assert rom[0xFF0E00:0xFF0E06] == bytes.fromhex("f0b509480078"), "nature routine at 08FF0E00 changed"

    src = open(os.path.join(HERE, "naturemenu.s"), encoding="ascii").read()

    def assemble(script_addr):
        code = bytes(ks.asm(src.replace("SCRIPT_ADDR", "0x%08X" % script_addr)
                               .replace("NEXT_HOOK", "0x%08X" % prev_field), BASE)[0])
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        bad = [i for i in md.disasm(code, BASE) if i.size == 4 and i.mnemonic != "bl"]
        assert not bad, "Thumb-2 encoding emitted: %s" % [(i.mnemonic, i.op_str) for i in bad]
        return code

    code = assemble(BASE)                               # pass 1: learn the layout
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    ins = list(md.disasm(code, BASE))
    cursor = next(i.address for i in ins if i.mnemonic == "push" and i.op_str == "{r4, lr}")
    field = next(i.address for i in ins if i.mnemonic == "push" and i.op_str == "{r0, lr}")
    apply_fn = next(i.address for i in ins if i.mnemonic == "push" and i.op_str == "{lr}")

    name = gen3("Nature")
    prompt = gen3("Change to which nature?")
    done = gen3("Its nature changed!")
    code_len = (len(code) + 3) & ~3
    name_off = code_len
    prompt_off = name_off + len(name)
    done_off = prompt_off + len(prompt)
    table_off = (done_off + len(done) + 3) & ~3
    script_off = table_off + 35 * 8

    LOCK, MESSAGE, WAITMESSAGE, MULTICHOICE = 0x6A, 0x67, 0x66, 0x71
    CALLNATIVE, LOADWORD, CALLSTD, RELEASE, END = 0x23, 0x0F, 0x09, 0x6C, 0x02
    script = bytearray()
    script.append(LOCK)
    script.append(MESSAGE); script += struct.pack("<I", BASE + prompt_off)
    script.append(WAITMESSAGE)
    script += bytes((MULTICHOICE, 0, 0, MULTICHOICE_NATURES, 5))            # x, y, list, ignoreBPress
    native_at = len(script) + 1
    script.append(CALLNATIVE); script += struct.pack("<I", 0)
    script += bytes((LOADWORD, 0)); script += struct.pack("<I", BASE + done_off)
    script += bytes((CALLSTD, 4))
    script += bytes((RELEASE, END))

    code = assemble(BASE + script_off)                  # pass 2: real script address
    assert len(code) <= code_len
    struct.pack_into("<I", script, native_at, apply_fn | 1)

    table = bytearray(rom[OLD_TABLE - 0x08000000:OLD_TABLE - 0x08000000 + 34 * 8])
    assert struct.unpack_from("<I", table, 33 * 8 + 4)[0] & 1, "entry 33 is not the relearner's handler"
    table += struct.pack("<II", BASE + name_off, cursor | 1)

    blob = bytearray(code) + bytes(code_len - len(code)) + name + prompt + done
    blob += bytes(table_off - len(blob)) + table + script
    end = FREE + len(blob)
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = blob
    for lit in TABLE_LITERALS:
        struct.pack_into("<I", rom, lit, BASE + table_off)
    struct.pack_into("<I", rom, BUILDER_TRAMPOLINE + 4, BASE | 1)
    struct.pack_into("<I", rom, FIELD_LITERAL, field | 1)
    open(outp, "wb").write(rom)
    print("code %d bytes @%08X (cursor %08X, field %08X, apply %08X), table @%08X, script @%08X, end %08X" % (
        len(code), BASE, cursor, field, apply_fn, BASE + table_off, BASE + script_off, 0x08000000 + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
