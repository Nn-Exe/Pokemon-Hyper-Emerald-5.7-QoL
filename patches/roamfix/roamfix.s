@ roamfix: the roaming Pokemon's region from its species, before either of the hack's two routines that move it.
@ The hack tells a Sinnoh roamer (Tornadus 694, Thundurus 695) from a Hoenn one (Latias, Latios) by the map group
@ in sRoamerLocation (0x0203BC86: 0x24 = Sinnoh, 0 = Hoenn), which is not in the save: after Continue it is 0 and
@ the storm roams Hoenn. set_stub and move_stub stand in the game's two trampolines (0x08161D04, 0x08161D58) in
@ front of the hack's RoamerMoveToOtherLocationSet and RoamerMove; both take no arguments, so r0-r3 are free.
@ PAD is a mov r8, r8 or nothing, so that the pool starts on a word.
set_stub:
    push {lr}
    bl fix_region
    pop {r3}
    mov lr, r3
    ldr r3, set_lit
    bx r3
move_stub:
    push {lr}
    bl fix_region
    pop {r3}
    mov lr, r3
    ldr r3, move_lit
    bx r3

@ an active roamer of species 694 or 695 is in Sinnoh: the map group 0x24 (the routines then pick from the Sinnoh
@ table: 0x09F0AACC, 27 routes)
fix_region:
    ldr r0, sb1_lit
    ldr r0, [r0]
    ldr r1, roamer_lit
    adds r0, r0, r1
    ldrb r1, [r0, #0x13]
    cmp r1, #0
    beq out
    ldrh r1, [r0, #8]
    ldr r2, tornadus_lit
    cmp r1, r2
    beq sinnoh
    adds r2, #1
    cmp r1, r2
    bne out
sinnoh:
    ldr r0, loc_lit
    movs r1, #0x24
    strb r1, [r0]
out:
    bx lr
PAD
set_lit: .word SET_ADDR
move_lit: .word MOVE_ADDR
sb1_lit: .word 0x03005D8C
roamer_lit: .word 0x31DC
tornadus_lit: .word 694
loc_lit: .word 0x0203BC86
