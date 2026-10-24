@ mintquirky: Cheren's Mint list in the usual order with Quirky, and the Mint byte (mon + 0x1F, bits 0-6) read the
@ same way everywhere. The byte: 0 no Mint, 1-23 that nature, 24 Hardy (the old list's last entry), 25 Quirky (new).
@ The stats code takes the byte as the nature's number, so 25 must reach it as 24 (Quirky; 24 itself is neutral, as
@ Hardy is); the nature shown (GetNature) maps 24 to Hardy and 25 to Quirky.
@ Each "@@@ name" section is assembled on its own, at the next word (mintquirky_patch.py).

@@@ mint_r3
@ r3 = the Mint byte -> r3 = the nature the stats use. Flags change; nothing else does.
@ (CalculateMonStats, 0x09F03930, in place of `lsls r3, r3, #25; lsrs r3, r3, #25`)
    lsls r3, r3, #25
    lsrs r3, r3, #25
    cmp r3, #25
    bne r3_done
    movs r3, #24
r3_done:
    bx lr

@@@ mint_r0
@ The same from r3 into r0 (the stats code's nature getter, 0x09F038C4, in place of `lsls r0, r3, #25;
@ lsrs r0, r0, #25`)
    lsls r0, r3, #25
    lsrs r0, r0, #25
    cmp r0, #25
    bne r0_done
    movs r0, #24
r0_done:
    bx lr

@@@ get_nature
@ (r0 = mon) -> r0 = the nature shown. GetNature (0x0806D070) jumps here, lr still its caller's.
    push {lr}
    ldrb r1, [r0, #0x1f]
    movs r2, #0x7f
    ands r1, r2
    beq gn_own
    cmp r1, #24
    bne gn_not24
    movs r1, #0                 @ 24: Hardy
    b gn_ret
gn_not24:
    cmp r1, #25
    bne gn_ret
    movs r1, #24                @ 25: Quirky
gn_ret:
    adds r0, r1, #0
    pop {r1}
    bx r1
gn_own:                         @ no Mint: the personality's nature
    movs r1, #0
    movs r2, #0
    ldr r3, lit_getmondata
    bl gn_callr3
    movs r1, #25
    ldr r3, lit_umod
    bl gn_callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    pop {r1}
    bx r1
gn_callr3:
    bx r3
    .align 2
lit_getmondata: .word 0x0806A519
lit_umod:       .word 0x082E7BE1

@@@ mint_apply
@ The Mint script's callasm. VAR_0x8005 is the grid's slot, which is the nature's number (0 Hardy .. 24 Quirky); it
@ becomes the byte (Hardy 24, Quirky 25, the rest themselves) and the hack's own routine (0x08FF0E00) writes it and
@ recalculates the stats. lr is the script engine's: that routine returns there.
    ldr r0, lit_var8005
    ldrh r1, [r0]
    cmp r1, #0
    bne ma_not0
    movs r1, #24
    b ma_store
ma_not0:
    cmp r1, #24
    bne ma_store
    movs r1, #25
ma_store:
    strh r1, [r0]
    ldr r3, lit_apply
    bx r3
    .align 2
lit_var8005:    .word 0x020375E2
lit_apply:      .word 0x08FF0E01
