"""Hyper Training shows up (Hyper Emerald v5.7): python hypertrain_patch.py in.gba out.gba

Reported: after hyper training on Champion Island "the IV doesn't show 31, it keeps showing the old value".
The training itself works. The hyper trainer (map 35/28, object 18, script 0x09812758) marks each trained stat
with a bit in the spare byte mon+0x1E - bit 1 HP, 2 Atk, 3 Def, 4 Spe, 5 SpA, 6 SpD, mapped by testing each bit
alone - and the hack's CalculateMonStats counts a trained stat as IV 31 (Gardevoir: max HP 272 -> 289, IV 14).
The IV itself is never rewritten, as in the official games, so breeding and Hidden Power keep the original.
What was wrong:
  * the EV-IV Display item and the IV judges print the raw IV, so a trained stat kept its old number;
  * the stats only moved on the next recalculation - the trainer said to deposit the Pokemon in the PC,
    but depositing changes nothing (checked: the box copy keeps the bits and the old IVs); it is the
    withdraw that recalculates.

This patch:
  * repoints the GetMonData the EV-IV Display loads its Pokemon with (literal 0x0968A65C, used only by that
    loader) and the one the IV judges' helper 0x08FF0001 calls (the word 0x08FF0028 its stub 0x08FF0020
    jumps through; the helper's only IV users are the three judges) to ht_getmondata, which returns 31 for a
    trained IV field and passes every other field through;
  * keeps the EV-IV screen's Hidden Power type honest: it builds the type from the IVs it loaded (bit 0 of
    each, 0x0968A07A..0x0968A0B1), which would now be 31s - the first test showed Dragon turn into Dark.
    ht_getmondata records each real IV's low bit (EWRAM 0x0203D600) and a 10-byte trampoline at 0x0968A07A
    hands those to the calculation instead;
  * runs CalculateMonStats on the trained Pokemon straight after the training (the trainer's success path at
    0x09812840 now goes through a new script that calls ht_recalc, then rejoins it);
  * replaces the trainer's closing line, which told you to deposit it, with one that says it is done.

Order: independent of the other patches; apply at the end of the chain.
"""
import os, re, struct, sys
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "journal"))
import journal_patch as J

FREE = 0x00F54300                       # in the verified run 0x08F53700..0x08F54AA0, after naturefix
B = 0x08000000
BASE = B + FREE
GETMONDATA = 0x0806A519

EVIV_LIT = 0x0168A65C                   # EV-IV Display's loader 0x0968A42C: ldr r6,[pc,#0x21c] at 0x0968A43C
EVIV_LDR = 0x0168A43C
JUDGE_STUB = 0x00FF0020                 # ldr r2,[pc,#4]; bx r2; <pad>; .word GetMonData
JUDGE_LIT = 0x00FF0028
HPTYPE_AT = 0x0168A07A                  # the EV-IV screen's Hidden Power parity bits, 0x0968A07A..0x0968A0B1
HPTYPE_OLD = bytes.fromhex("02233a7b520013400422797b89000a4013430122f97a0a4013430822b97bc9000a40"
                           "13431022f97b09010a4013432022397c49010a401343")   # r3 = the six low bits

SCRIPT_AT = 0x01812840                  # both cap paths goto here
SCRIPT_OLD = bytes.fromhex("0f005c298109" "0903" "980108" "980008" "0f009a298109" "0904")
DONE_TEXT_PTR = SCRIPT_AT + 16          # the loadword's pointer to "complete! ... deposit it on the PC"
DONE = ("The hyper training is complete!", "Its trained stats are maxed out!")


def thumb(src, addr):
    """Assemble; reject Thumb-2 (a pool-twin with nops keeps the linear sweep going). keystone pads an .align with
    a Thumb-2 nop (00 BF): allowed only straight after a return, where it never runs."""
    ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
    code = bytes(ks.asm(src, addr)[0])
    twin = bytes(ks.asm(re.sub(r"^(\s*\w+:)\s*\.word\s+.*$", r"\1 mov r8, r8\n    mov r8, r8", src, flags=re.M), addr)[0])
    assert len(twin) == len(code), "pool twin differs in size"
    dis = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(twin, addr))
    assert sum(i.size for i in dis) == len(twin), "disassembly stopped early"
    assert not [i for i in dis if i.size == 4 and i.mnemonic != "bl"], "Thumb-2 encoding emitted"
    for k, i in enumerate(dis):
        if i.mnemonic == "nop":
            assert dis[k - 1].mnemonic == "bx", "a Thumb-2 nop at %08X that can run" % i.address
    return code, dis


def build(inp, outp):
    rom = bytearray(open(inp, "rb").read())
    assert rom[0xAC:0xB0] == b"BPEE" and len(rom) == 0x2000000
    assert struct.unpack_from("<I", rom, EVIV_LIT)[0] == GETMONDATA, "EV-IV Display's GetMonData literal moved"
    h = struct.unpack_from("<H", rom, EVIV_LDR)[0]
    assert (h & 0xF800) == 0x4800 and ((B + EVIV_LDR + 4) & ~3) + (h & 0xFF) * 4 == B + EVIV_LIT, \
        "the EV-IV loader does not load that literal"
    users = [o for o in range(EVIV_LIT - 1020, EVIV_LIT, 2)
             if (struct.unpack_from("<H", rom, o)[0] & 0xF800) == 0x4800
             and ((B + o + 4) & ~3) + (struct.unpack_from("<H", rom, o)[0] & 0xFF) * 4 == B + EVIV_LIT]
    assert users == [EVIV_LDR], "the literal has other users: %s" % ["%08X" % (B + u) for u in users]
    assert rom[JUDGE_STUB:JUDGE_STUB + 4].hex() == "014a1047", "the judges' GetMonData stub changed"
    assert struct.unpack_from("<I", rom, JUDGE_LIT)[0] == GETMONDATA, "the judges' stub no longer calls GetMonData"
    assert bytes(rom[SCRIPT_AT:SCRIPT_AT + len(SCRIPT_OLD)]) == SCRIPT_OLD, "the trainer's success path changed"
    assert bytes(rom[HPTYPE_AT:HPTYPE_AT + len(HPTYPE_OLD)]) == HPTYPE_OLD, "the EV-IV Hidden Power code changed"
    assert (B + HPTYPE_AT) % 4 == 2 and (B + HPTYPE_AT + 6) % 4 == 0   # the 10-byte trampoline's word lands aligned

    code, dis = thumb(open(os.path.join(HERE, "hypertrain.s"), encoding="ascii").read(), BASE)
    funcs = [i.address for i in dis if i.mnemonic == "push"]
    assert len(funcs) == 2, "expected 2 functions, found %d" % len(funcs)
    getmon, recalc = funcs
    d = bytearray(code)
    while len(d) % 4:
        d.append(0)
    script = B + FREE + len(d)
    # callasm ht_recalc; loadword 0, "I'll take your Pokemon..."; goto back to its callstd
    d += bytes((0x23,)) + struct.pack("<I", recalc | 1)
    d += rom[SCRIPT_AT:SCRIPT_AT + 6]
    d += bytes((0x05,)) + struct.pack("<I", B + SCRIPT_AT + 6)
    text = B + FREE + len(d)
    assert all(len(l) <= 34 for l in DONE)
    d += J.enc(DONE[0]) + b"\xfe" + J.enc(DONE[1]) + b"\xff"
    end = FREE + len(d)
    assert end <= 0x00F54AA0, "outside the verified run"
    assert set(rom[FREE:end]) == {0xFF}, "target region not free"
    rom[FREE:end] = d

    struct.pack_into("<I", rom, EVIV_LIT, getmon | 1)
    struct.pack_into("<I", rom, JUDGE_LIT, getmon | 1)
    # ldr r3,[pc,#4]; bx r3; mov r8,r8; .word ht_hptype - the rest of the old parity code never runs
    rom[HPTYPE_AT:HPTYPE_AT + 6] = bytes.fromhex("014b1847c046")
    struct.pack_into("<I", rom, HPTYPE_AT + 6, BASE | 1)
    rom[SCRIPT_AT] = 0x05                                   # goto the new script (its 6th byte never runs)
    struct.pack_into("<I", rom, SCRIPT_AT + 1, script)
    struct.pack_into("<I", rom, DONE_TEXT_PTR, text)
    open(outp, "wb").write(rom)
    print("ht_hptype %08X, ht_getmondata %08X, ht_recalc %08X, script %08X, text %08X; %d bytes @%08X..%08X" % (
        BASE | 1, getmon | 1, recalc | 1, script, text, len(d), B + FREE, B + end))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
