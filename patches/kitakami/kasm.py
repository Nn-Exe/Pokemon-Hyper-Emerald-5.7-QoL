"""Kitakami's two pieces of code (Thumb, assembled with keystone).

  * The festival's evening. The hack tints the screen by the hour (NOTES, *DAY/NIGHT*): its routine at 0x08CFE3E0
    reads gLocalTime's hour (`ldr r0, =0x03005CF4; ldrb r1, [r0, #6]` at 0x08CFE3EA) and picks a colour mask from
    it (17-18: orange). Those two instructions become `bl kit_hour`, which gives the same hour, or 18 while the
    Festival of Masks runs (F_PLAZA set, F_TRUTH clear) and you stand in Mossui Town. Every other map, and Mossui
    before and after the festival, keep the clock's hour; the Option menu's Day/Night Off still turns all tinting off.
    kit_hour is 0x08FEF580..: the top of the free unreferenced run 0x08FED3C8..0x08FEF600 (the skill's list; all
    0xFF and no real pointer into it, checked 2026-10-16), within a `bl`'s reach of the hook (the blob is not).
    The routine was entered by a jump and keeps nothing in lr (the daynight patch's `bl tint_gate` at 0x08CFE452
    relies on the same).
  * Grandpa changes Ogerpon's mask (callnative): kit_mask looks through the party for an Ogerpon (species
    1228-1231: Teal, Wellspring, Hearthflame, Cornerstone, read from the ROM's types), gives the first one the
    species in VAR 0x8004 with SetMonData and recalculates its stats (CalculateMonStats), and puts 1 in VAR_RESULT
    (0 if there is none). Party data is unencrypted in this hack (species at +0x20). It lives in the blob.
"""
import struct
import keystone

HOOK = 0x00CFE3EA
HOOK_WAS = bytes.fromhex("37488179")               # ldr r0, [pc, #0xdc]; ldrb r1, [r0, #6]
LOCALTIME_LIT, LOCALTIME = 0x00CFE4C8, 0x03005CF4
HOUR_AT, HOUR_END = 0x08FEF580, 0x08FEF600
SB1, SB2 = 0x03005D8C, 0x03005D90
PARTY = 0x020244EC
VAR_8004, VAR_RESULT = 0x020375E0, 0x020375F0       # gSpecialVars (the table at 0x081DBA0C)
SET_MON_DATA, CALC_STATS = 0x0806ACAD, 0x08068D0D
MON_DATA_SPECIES = 11
OGERPON = (1228, 1231)
EVENING = 18
# The tint leaves BG palettes 12-15 alone (its mask 0xFFFF0FFF, loaded at 0x08CFE474: NOTES, *Day/night*); Kitakami's
# tileset keeps market colours in row 12, so at night the paving, the awnings and the goods stayed bright (the user,
# 2026-10-17: "when at night, the floor is too bright"). kit_bgmask: a bl over `mov r8, r7; ldr r7, =0xFFFF0FFF`
# (0x08CFE472; 0x08CFE476 is a branch target, left alone) gives Mossui the mask 0xFFFF1FFF, every other map the old.
# Its room: 0x08FEF540..0x08FEF580, below kit_hour, in the free run from 0x08FEE88C (all 0xFF, no word points in).
HOOK2, HOOK2_WAS = 0x00CFE472, bytes.fromhex("b846234f")
MASK_LIT, MASK_WAS, MASK_MOSSUI = 0x00CFE504, 0xFFFF0FFF, 0xFFFF1FFF
BGMASK_AT, BGMASK_END = 0x08FEF540, 0x08FEF580
NIGHT = 22                                          # Part 2's night (Mochi Mayhem)


def flag_byte(f):
    """(SaveBlock pointer, offset, bit) of an extended flag (NOTES, *The hack's extended flags*)"""
    i = (f - 0x4000) >> 3
    if i <= 0x33: return SB1, 0x988 + i, f & 7
    if i <= 0x67: return SB1, 0x3B24 + i - 0x34, f & 7
    if i <= 0x9B: return SB2, 0x5C + i - 0x68, f & 7
    return SB2, 0x28 + i - 0x9C, f & 7


def asm(src, at):
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_THUMB)
    code, _ = ks.asm(src, at)
    return bytes(code)


def check_thumb(code, at):
    """no 4-byte instruction but bl, and no `nop` (keystone's 00 BF, undefined on the GBA) anywhere"""
    for k in range(0, len(code) - 1, 2):
        assert code[k:k + 2] != bytes([0x00, 0xBF]), "a nop (00 BF) at +%d" % k
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    for ins in md.disasm(code, at):
        if ins.size == 4 and not ins.mnemonic.startswith("bl"):
            raise AssertionError("a 4-byte instruction at %X: %s %s" % (ins.address, ins.mnemonic, ins.op_str))


def hour_code(group, num, windows):
    """kit_hour: in Mossui (group, num), the hour of the first window whose first flag is set and second clear
    (windows: [(on, off, hour)]: the festival's evening, Part 2's night), else the real hour"""
    src = """
    kit_hour:
        ldr r0, =%(lt)d
        ldrb r1, [r0, #6]
        ldr r0, =%(sb1)d
        ldr r0, [r0]
        ldrb r2, [r0, #4]
        cmp r2, #%(g)d
        bne done
        ldrb r2, [r0, #5]
        cmp r2, #%(n)d
        bne done
        ldr r0, =%(sb2)d
        ldr r0, [r0]
    """ % dict(lt=LOCALTIME, sb1=SB1, sb2=SB2, g=group, n=num)
    for k, (on, off, hour) in enumerate(windows):
        o_sb, o_off, o_bit = flag_byte(on)
        f_sb, f_off, f_bit = flag_byte(off)
        assert o_sb == f_sb == SB2, "the flags are not in SaveBlock2 (the code reads them there)"
        src += """
        ldr r3, =%(ooff)d
        ldrb r2, [r0, r3]
        movs r3, #%(omask)d
        tst r2, r3
        beq next%(k)d
        ldr r3, =%(foff)d
        ldrb r2, [r0, r3]
        movs r3, #%(fmask)d
        tst r2, r3
        bne next%(k)d
        movs r1, #%(hour)d
        b done
    next%(k)d:
    """ % dict(ooff=o_off, omask=1 << o_bit, foff=f_off, fmask=1 << f_bit, hour=hour, k=k)
    for pad in ("", "        mov r8, r8\n"):      # (the literal pool 4-aligned without keystone's 00 BF)
        code = asm(src + """
    done:
        bx lr
    """ + pad, HOUR_AT)
        if bytes([0x00, 0xBF]) not in [code[k:k + 2] for k in range(0, len(code), 2)]:
            break
    check_thumb(code, HOUR_AT)
    assert len(code) <= HOUR_END - HOUR_AT, "kit_hour is %d bytes" % len(code)
    return code


def bl(frm, to):
    off = to - (frm + 4)
    assert -0x400000 <= off < 0x400000 and not off & 1, "bl out of reach"
    return struct.pack("<HH", 0xF000 | ((off >> 12) & 0x7FF), 0xF800 | ((off >> 1) & 0x7FF))


def mask_code(at):
    src = """
    kit_mask:
        push {r4-r6, lr}
        ldr r4, =%(party)d
        movs r5, #6
    look:
        ldrh r0, [r4, #0x20]
        ldr r1, =%(first)d
        subs r0, r0, r1
        cmp r0, #%(span)d
        bls found
        adds r4, #100
        subs r5, #1
        bne look
        movs r1, #0
        b out
    found:
        mov r0, r4
        movs r1, #%(sp)d
        ldr r2, =%(v8004)d
        ldr r3, =%(set)d
        bl call_r3
        mov r0, r4
        ldr r3, =%(calc)d
        bl call_r3
        movs r1, #1
    out:
        ldr r0, =%(res)d
        strh r1, [r0]
        pop {r4-r6}
        pop {r0}
        bx r0
    call_r3:
        bx r3
    """ % dict(party=PARTY, first=OGERPON[0], span=OGERPON[1] - OGERPON[0], sp=MON_DATA_SPECIES, v8004=VAR_8004,
               set=SET_MON_DATA, calc=CALC_STATS, res=VAR_RESULT)
    code = asm(src, at)
    check_thumb(code, at)
    return code


def check(rom):
    assert bytes(rom[HOOK:HOOK + 4]) == HOOK_WAS, "the tint routine's hour read changed (0x08CFE3EA)"
    assert struct.unpack_from("<I", rom, LOCALTIME_LIT)[0] == LOCALTIME, "the tint routine's clock literal changed"
    lo, hi = HOUR_AT - 0x08000000, HOUR_END - 0x08000000
    assert set(rom[lo:hi]) == {0xFF}, "0x%08X..0x%08X is not free" % (HOUR_AT, HOUR_END)
    assert bytes(rom[HOOK2:HOOK2 + 4]) == HOOK2_WAS, "the tint's mask load (0x08CFE472) is not what it was"
    assert struct.unpack_from("<I", rom, MASK_LIT)[0] == MASK_WAS, "the tint's palette mask is not 0xFFFF0FFF"
    lo, hi = BGMASK_AT - 0x08000000, BGMASK_END - 0x08000000
    assert set(rom[lo:hi]) == {0xFF}, "0x%08X..0x%08X is not free" % (BGMASK_AT, BGMASK_END)


def bgmask_code(group, num):
    """kit_bgmask: mov r8, r7 (the replaced instruction), then r7 = the palette mask: Mossui's, else the game's"""
    src = """
    kit_bgmask:
        mov r8, r7
        push {r0, r1}
        ldr r7, =%(was)d
        ldr r0, =%(sb1)d
        ldr r0, [r0]
        ldrb r1, [r0, #4]
        cmp r1, #%(g)d
        bne out
        ldrb r1, [r0, #5]
        cmp r1, #%(n)d
        bne out
        ldr r7, =%(mossui)d
    out:
        pop {r0, r1}
        bx lr
    """ % dict(was=MASK_WAS, sb1=SB1, g=group, n=num, mossui=MASK_MOSSUI)
    for pad in ("", "        mov r8, r8\n"):
        code = asm(src + pad, BGMASK_AT)
        if bytes([0x00, 0xBF]) not in [code[k:k + 2] for k in range(0, len(code), 2)]:
            break
    check_thumb(code, BGMASK_AT)
    assert len(code) <= BGMASK_END - BGMASK_AT, "kit_bgmask is %d bytes" % len(code)
    return code


def install_bgmask(rom, group, num):
    code = bgmask_code(group, num)
    lo = BGMASK_AT - 0x08000000
    rom[lo:lo + len(code)] = code
    rom[HOOK2:HOOK2 + 4] = bl(0x08000000 + HOOK2, BGMASK_AT)
    return len(code)


def install_hour(rom, group, num, windows):
    code = hour_code(group, num, windows)
    lo = HOUR_AT - 0x08000000
    rom[lo:lo + len(code)] = code
    rom[HOOK:HOOK + 4] = bl(0x08000000 + HOOK, HOUR_AT)
    return len(code)
