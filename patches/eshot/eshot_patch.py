"""Electro Shot fires in its first turn in the rain (Hyper Emerald v5.7): python eshot_patch.py in.gba out.gba

Reported 2026-10-22: "from 1.9, i also found out that electro shot was not attacking in first turn during rain".

gen9rest made Electro Shot (move 982) from Meteor Beam: effect 71, the two-turn moves, whose script (0x09D0509C:
attackcanceler, then the engine's routine 84 at 0x09D63A64) jumps by the move's last data byte - 2 for Skull Bash,
Meteor Beam and Electro Shot: the charge message, the stat raise (byte 9: Sp. Atk +1), a Power Herb, else the
charging turn. Only kind 3 (Solar Beam, Solar Blade) looks at the weather. Routine 84 also picks the charge message by
the move's number, and Electro Shot is not in its list, so it showed whatever the last two-turn move left there
(Geomancy's "is absorbing power!").

As in Scarlet/Violet: the charge message (its own, "{attacker} absorbed electricity!"), Sp. Atk +1, and in the rain
the shot in the same turn - not with a Utility Umbrella, nor while Cloud Nine or Air Lock is out; a Power Herb is
not used up in the rain. Kind 2's pointer in routine 84's table points at a new script: Electro Shot goes its own
way, the other kind-2 moves on to the old script (unchanged). The rain check is a new routine of the engine's script
command 0x83 (eshot.s), the message a new battle string; both tables get longer copies, as gen9abil did (its two
tables are the ones in use: 342 strings from 0x17C, 222 routines).

Space: 0x09E3B000..0x09E3BC00 (the tables, the routine, the script, the text: about 2.6 KB) in the stretch gen9abil
took and proved (0x09E33000..0x09E3C000; gen9anim's part ends at 0x09E3ACD0): blank, and no word at a 4-byte boundary
anywhere in the ROM points into it (checked here).
"""
import os, re, struct, sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gen9abil"))
import gen9abil_data as G9                       # the counts of gen9abil's longer tables

B = 0x08000000
SPACE, SPACE_END = 0x09E3B000, 0x09E3BC00
CALLTABLE, STRTABLE, CODE, SCRIPT, TEXT = SPACE, SPACE + 0x380, SPACE + 0x900, SPACE + 0x980, SPACE + 0xA00

CALLASM_WORD = 0x09D686F0             # the 0x83 command reads routine n at [this word] + 12 + 4n
PLEDGE_WORD, CALLASM_ORIGINAL = 0x09D68524, 0x09D79EAC   # the engine's own table: get_move_from_pledge's word stays
STRINGS_WORD = 0x09D4A204             # battle strings from id 0x17C: [this word] + 4 (id - 0x17C)
FIRST_ID = 0x17C
N_STRINGS = G9.FIRST_STRING - FIRST_ID + len(G9.STRINGS)
N_ROUTINES = G9.CALLASM_FIRST + len(G9.CALLASM)

DISPATCH = 0x09D0509C                 # attackcanceler; 83 5400 (routine 84); six script pointers, by kind
DISPATCH_BYTES = bytes.fromhex("00835400")
KIND2_WORD, KIND2 = 0x09D050A8, 0x09D0513D
# jumpifstatus2 attacker, MULTIPLETURNS, SECOND; call CHARGE; 83 1900 (the stat change from byte 9); call STATMSG;
# 83 5500 SECOND (Power Herb); call SET_CHARGING; goto END
KIND2_BYTES = bytes.fromhex("1d01001000006551d009" "41e250d009" "831900" "41d06dd009" "8355006551d009"
                            "410a51d009" "284e8a2d08")
SECOND, CHARGE, STATMSG, SET_CHARGING, END = 0x09D05165, 0x09D050E2, 0x09D06DD0, 0x09D0510A, 0x082D8A4E
# ppreduce; printstring 0x130; attackanimation; waitanimation; printfromtable (the charge messages); waitmessage 0x40
CHARGE_BYTES = bytes.fromhex("03103001090a13de3dd709124000" "3c")
ROUTINES = {25: 0x09D627D1, 84: 0x09D63A65, 85: 0x09D63A19}      # stat change, the two-turn kinds, Power Herb
WEATHER_EFFECT = (0x09D45B84, bytes.fromhex("0022" "10b5" "0321" "0d20"))   # movs r2,#0; push; movs r1,#3; movs r0,#0xd
ITEM_EFFECT = (0x09D68700, bytes.fromhex("5822" "4243" "70b5"))             # movs r2,#0x58; muls; push
READ_PTR = (0x09D3809A, bytes.fromhex("0200" "d078"))                      # movs r2,r0; ldrb r0,[r2,#3]
UMBRELLA_EFFECT = 164
GCURRENTMOVE = 0x020241EA

CHARS = {" ": 0x00, "!": 0xAB, "\n": 0xFE}
CHARS.update({chr(ord("a") + i): 0xD5 + i for i in range(26)})
MESSAGE = b"\xFD\x0F" + bytes(CHARS[c] for c in " absorbed\nelectricity!") + b"\xFF"   # {attacker} absorbed / electricity!
ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)


def u16(rom, a):
    return struct.unpack_from("<H", rom, a - B)[0]


def u32(rom, a):
    return struct.unpack_from("<I", rom, a - B)[0]


def thumb(src, addr):
    """Assemble, and check for Thumb-2 on a twin whose pools are nops so the linear sweep never stops."""
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M),
                        addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    assert not [i for i in dis if i.size == 4 and i.mnemonic != "bl"], "Thumb-2 encoding emitted"
    return code, dis


def move_id(rom, name):
    names = u32(rom, B + 0x148)
    want = bytes(0xBB + ord(c) - 65 if c.isupper() else 0xD5 + ord(c) - 97 if c.islower() else 0 for c in name)
    ids = [i for i in range(1024) if bytes(rom[names - B + 13 * i:names - B + 13 * i + len(want) + 1]) == want + b"\xff"]
    assert len(ids) == 1, "%s: %s" % (name, ids)
    return ids[0]


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000

    # ---- Electro Shot and the two-turn script as gen9rest and the engine left them
    es = move_id(rom, "Electro Shot")
    row = bytes(rom[0x01D86419 + 12 * es:0x01D86419 + 12 * es + 12])
    assert row[0] == 71 and row[9] == 0x14 and row[11] == 2, "Electro Shot's data: %s" % row.hex()
    assert bytes(rom[DISPATCH - B:DISPATCH - B + 4]) == DISPATCH_BYTES, "the two-turn script's start"
    assert u32(rom, KIND2_WORD) == KIND2, "kind 2's script pointer"
    assert bytes(rom[KIND2 - B:KIND2 - B + len(KIND2_BYTES)]) == KIND2_BYTES, "kind 2's script"
    assert bytes(rom[CHARGE - B:CHARGE - B + len(CHARGE_BYTES)]) == CHARGE_BYTES, "the charging turn's script"
    for at, want in (WEATHER_EFFECT, ITEM_EFFECT, READ_PTR):
        assert bytes(rom[at - B:at - B + len(want)]) == want, "the routine at %08X" % at
    items = u32(rom, B + 0x1C8)
    umbrellas = [i for i in range(1000) if rom[items - B + 44 * i + 18] == UMBRELLA_EFFECT]
    assert len(umbrellas) == 1 and bytes(rom[items - B + 44 * umbrellas[0]:][:13]) == bytes.fromhex(
        "cfe8dde000cfe1d6e6d9e0e0d5"), "the Utility Umbrella's hold effect"

    # ---- the two tables in use (gen9abil's copies, back to back)
    calls = u32(rom, CALLASM_WORD) + 12
    strings = u32(rom, STRINGS_WORD)
    assert strings + 4 * N_STRINGS == calls, "the string table is not gen9abil's (%08X, %08X)" % (strings, calls)
    assert u32(rom, PLEDGE_WORD) == CALLASM_ORIGINAL - 12
    routines = [u32(rom, calls + 4 * k) for k in range(N_ROUTINES)]
    assert all(B <= r < B + len(rom) and r & 1 for r in routines), "a routine of the table is not code"
    for k, want in ROUTINES.items():
        assert routines[k] == want, "routine %d is %08X" % (k, routines[k])
    words = [u32(rom, strings + 4 * k) for k in range(N_STRINGS)]
    assert all(B <= p < B + len(rom) for p in words), "a string of the table is not in the ROM"
    for v, holder in ((calls - 12, CALLASM_WORD), (strings, STRINGS_WORD)):
        held = [B + m.start() for m in re.finditer(re.escape(struct.pack("<I", v)), bytes(rom)) if m.start() % 4 == 0]
        assert held == [holder], "%08X is held at %s" % (v, ["%08X" % h for h in held])

    # ---- the space
    assert set(rom[SPACE - B:SPACE_END - B]) == {0}, "the space is not blank"
    held = [B + o for o in range(0, len(rom), 4) if SPACE <= struct.unpack_from("<I", rom, o)[0] < SPACE_END]
    assert not held, "words point into the space: %s" % ["%08X" % a for a in held]

    # ---- the routine
    src = open(os.path.join(HERE, "eshot.s"), encoding="ascii").read()
    for pad in ("", "    mov r8, r8"):
        code, dis = thumb(src.replace("PAD", pad), CODE)
        if not [i for i in dis if i.mnemonic == "nop"]:
            break
    else:
        raise AssertionError("could not pad the literal pool without a Thumb-2 nop")
    assert CODE + len(code) <= SCRIPT

    # ---- the script: Electro Shot its own way, the other kind-2 moves to the old script
    string_id = FIRST_ID + N_STRINGS
    routine = N_ROUTINES
    p = struct.Struct("<I").pack
    es_at = SCRIPT + 17
    charge_at = es_at + 47
    script = (b"\x2A\x00" + p(GCURRENTMOVE) + struct.pack("<H", es) + p(es_at)    # jumpifhalfword ==, gCurrentMove
              + b"\x28" + p(KIND2))                                                # goto the old kind 2
    assert SCRIPT + len(script) == es_at
    es_script = (b"\x1D\x01" + p(0x1000) + p(SECOND)         # jumpifstatus2 attacker, MULTIPLETURNS: the second turn
                 + b"\x41" + p(charge_at)                    # call: the charging turn, with our message
                 + b"\x83\x19\x00"                           # Sp. Atk +1 (byte 9)
                 + b"\x41" + p(STATMSG)                      # its animation and message
                 + b"\x83" + struct.pack("<H", routine) + p(SECOND)    # rain on the attacker: the shot now
                 + b"\x83\x55\x00" + p(SECOND)               # a Power Herb: the shot now
                 + b"\x41" + p(SET_CHARGING)                 # else the charging turn
                 + b"\x28" + p(END))
    assert es_at + len(es_script) == charge_at
    charge = CHARGE_BYTES[:6] + b"\x10" + struct.pack("<H", string_id) + CHARGE_BYTES[11:]
    script += es_script + charge
    assert SCRIPT + len(script) <= TEXT and TEXT + len(MESSAGE) <= SPACE_END

    # ---- write
    def put(at, data):
        rom[at - B:at - B + len(data)] = data
    put(CALLTABLE, b"".join(p(r) for r in routines + [CODE | 1]))
    put(STRTABLE, b"".join(p(w) for w in words + [TEXT]))
    assert CALLTABLE + 4 * (N_ROUTINES + 1) <= STRTABLE and STRTABLE + 4 * (N_STRINGS + 1) <= CODE
    put(CODE, code)
    put(SCRIPT, script)
    put(TEXT, MESSAGE)
    struct.pack_into("<I", rom, CALLASM_WORD - B, CALLTABLE - 12)
    struct.pack_into("<I", rom, STRINGS_WORD - B, STRTABLE)
    struct.pack_into("<I", rom, KIND2_WORD - B, SCRIPT)
    open(outp, "wb").write(rom)
    print("eshot: Electro Shot (move %d) fires in the rain; routine %d at %08X, string %X, script %08X, %08X..%08X"
          % (es, routine, CODE, string_id, SCRIPT, SPACE, TEXT + len(MESSAGE)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
