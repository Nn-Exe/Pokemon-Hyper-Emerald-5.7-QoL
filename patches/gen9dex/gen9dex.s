@ gen9dex (Whole Gen 9 test build only): the Pokedex marks of a save made before the Gen 9 renumbering, moved to the
@ official numbers the first time the game asks for one. See gen9dex_patch.py.
@
@ Before: Gen 9 at 906-1025 in the order of the two patches (gen9's 35 numbers 906-940, gen9rest's 85 941-1025). Now:
@ the official 906-1025. Marks for numbers below 960 are in SaveBlock1 + 0x560 (seen) / + 0x5D8 (caught), bit n;
@ 960 and up in gen9rest's area EXT (a marker word, 32 bytes seen, 32 caught, bit n - 960). gen9rest's marker said
@ "DEX9" (the area holds marks); this patch makes dexext's own marker NEW, so a save whose marker is not NEW has its
@ Gen 9 marks in the old numbers: OLD ("DEX9", a test build's save: the area counts) or anything else (the main
@ game's save, or New Game: the area holds nothing). The marks of the old numbers 906-1032 are read, the new
@ numbers' bits cleared (906-959 in SaveBlock1, the whole area), the marker set to NEW, and each old mark written at
@ its new number. Numbers below 906 are never touched.
.thumb

@ dexmig_entry: the hack's GetSetPokedexFlag (0x09257950) jumps here now (r0 = number, r1 = mode); lr is the
@ caller's, kept on the stack across the call.
dexmig_entry:
    push {r0, r1, r2, r3, lr}
    ldr r2, l_ext
    ldr r2, [r2]
    ldr r3, l_new
    cmp r2, r3
    beq dm_go
    bl migrate
dm_go:
    pop {r0, r1, r2, r3}
    pop {r3}
    mov lr, r3
    ldr r3, l_dexflag
    bx r3

@ migrate(): the marks moved, see above.
migrate:
    push {r4, r5, r6, r7, lr}
    sub sp, #32                     @ old marks: bits 0-127 seen at sp, caught at sp + 16 (number 906 + i)
    movs r0, #0
    mov r1, sp
    movs r2, #8
mg_zero:
    str r0, [r1]
    adds r1, #4
    subs r2, #1
    bne mg_zero
    movs r4, #0
mg_read:
    movs r5, #0                     @ 0 seen, 1 caught
mg_read2:
    ldr r0, l_first
    adds r0, r0, r4
    movs r1, r5
    bl get_old
    cmp r0, #0
    beq mg_read3
    mov r0, sp
    lsls r1, r5, #4
    adds r0, r0, r1
    movs r1, r4
    bl tbit_set
mg_read3:
    adds r5, #1
    cmp r5, #2
    blo mg_read2
    adds r4, #1
    cmp r4, #OLD_COUNT
    blo mg_read
    @ clear the new numbers' bits: 906-959 in both SaveBlock1 arrays, the whole area
    ldr r4, l_first
mg_clr:
    movs r0, r4
    movs r1, #0
    bl clear_sb1
    movs r0, r4
    movs r1, #1
    bl clear_sb1
    adds r4, #1
    ldr r0, l_limit
    cmp r4, r0
    blo mg_clr
    ldr r0, l_ext
    ldr r1, l_new
    str r1, [r0]
    movs r1, #0
    movs r2, #16
mg_clr2:
    adds r0, #4
    str r1, [r0]
    subs r2, #1
    bne mg_clr2
    @ each old mark at its new number
    movs r4, #0
mg_write:
    ldr r6, l_map
    lsls r0, r4, #1
    ldrh r6, [r6, r0]               @ the new number, 0 = none
    cmp r6, #0
    beq mg_next
    movs r5, #0
mg_write2:
    mov r0, sp
    lsls r1, r5, #4
    adds r0, r0, r1
    movs r1, r4
    bl tbit_get
    cmp r0, #0
    beq mg_write3
    movs r0, r6
    movs r1, r5
    bl set_new
mg_write3:
    adds r5, #1
    cmp r5, #2
    blo mg_write2
mg_next:
    adds r4, #1
    cmp r4, #OLD_COUNT
    blo mg_write
    add sp, #32
    pop {r4, r5, r6, r7, pc}

@ tbit_set(r0 = bits, r1 = i) / tbit_get(r0, r1) -> r0
tbit_set:
    lsrs r2, r1, #3
    adds r0, r0, r2
    movs r2, #7
    ands r1, r2
    movs r2, #1
    lsls r2, r1
    ldrb r3, [r0]
    orrs r3, r2
    strb r3, [r0]
    bx lr
tbit_get:
    lsrs r2, r1, #3
    adds r0, r0, r2
    movs r2, #7
    ands r1, r2
    ldrb r0, [r0]
    lsrs r0, r1
    movs r2, #1
    ands r0, r2
    bx lr

@ byte_of(r0 = number, r1 = 0 seen / 1 caught, r2 = 1: the area counts) -> r0 = the byte's address or 0, r1 = mask
byte_of:
    push {r4, lr}
    movs r4, r0
    movs r3, #7
    ands r3, r0
    movs r0, #1
    lsls r0, r3
    mov ip, r0                      @ the mask
    ldr r3, l_limit
    cmp r4, r3
    bhs bo_ext
    lsrs r4, r4, #3
    ldr r0, l_sb1
    ldr r0, [r0]
    adds r0, r0, r4
    ldr r3, l_seen_at
    cmp r1, #0
    beq bo_sb1
    ldr r3, l_caught_at
bo_sb1:
    adds r0, r0, r3
    b bo_out
bo_ext:
    cmp r2, #0
    beq bo_none
    subs r4, r4, r3
    cmp r4, #255
    bhi bo_none
    movs r3, #7                     @ the bit within the area is (number - 960) & 7
    ands r3, r4
    movs r0, #1
    lsls r0, r3
    mov ip, r0
    lsrs r4, r4, #3
    ldr r0, l_ext
    adds r0, #4
    adds r0, r0, r4
    cmp r1, #0
    beq bo_out
    adds r0, #32
    b bo_out
bo_none:
    movs r0, #0
bo_out:
    mov r1, ip
    pop {r4, pc}

@ get_old(r0 = number, r1 = which) -> r0: the mark as the save has it (the area only with the OLD marker)
get_old:
    push {r4, lr}
    ldr r2, l_ext
    ldr r2, [r2]
    ldr r3, l_old
    movs r4, #0
    cmp r2, r3
    bne go_1
    movs r4, #1
go_1:
    movs r2, r4
    bl byte_of
    cmp r0, #0
    beq go_out
    ldrb r0, [r0]
    ands r0, r1
    beq go_out
    movs r0, #1
go_out:
    pop {r4, pc}

@ clear_sb1(r0 = number below 960, r1 = which)
clear_sb1:
    push {lr}
    movs r2, #0
    bl byte_of
    cmp r0, #0
    beq cs_out
    ldrb r2, [r0]
    bics r2, r1
    strb r2, [r0]
cs_out:
    pop {pc}

@ set_new(r0 = number, r1 = which): the area counts (its marker is NEW by now)
set_new:
    push {lr}
    movs r2, #1
    bl byte_of
    cmp r0, #0
    beq sn_out
    ldrb r2, [r0]
    orrs r2, r1
    strb r2, [r0]
sn_out:
    pop {pc}

    PAD1
l_ext:          .word 0x0203DA00
l_new:          .word NEW_MAGIC
l_old:          .word 0x39584544        @ "DEX9", gen9rest's marker
l_dexflag:      .word DEX_FLAG
l_first:        .word 906
l_limit:        .word 960
l_sb1:          .word 0x03005D8C
l_seen_at:      .word 0x00000560
l_caught_at:    .word 0x000005D8
l_map:          .word MAP_ADDR
