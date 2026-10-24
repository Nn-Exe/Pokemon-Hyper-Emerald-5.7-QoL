@ gmaxicon: a Gigantamax mark on the summary screen - the Max Mushroom's item icon (item 87), made smaller by the
@ patcher, at the right end of the nickname's row (or, for a nickname too long for it, at the bottom right of the
@ picture), for a Pokemon whose Gigantamax bit is set (mon +0x4E bit 7:
@ the Max Soup cook's, read by the hack's Gigantamax table walk 0x08FF1858). The summary's CreateCaughtBallSprite
@ (0x081C4A08, r0 = the summary's own copy of the Pokemon it shows, sMonSummaryScreen + 0xC) runs for every Pokemon
@ the screen shows; its first 8 bytes (push {r4, lr}; movs r1, #0x26; bl GetMonData) are a trampoline to stub, which
@ replays them in a frame of the routine's own that returns here, then puts the mark up or takes it down.

stub:
    push {r5, lr}
    adds r5, r0, #0             @ the Pokemon
    ldr r3, lit_ret
    mov lr, r3
    push {r4, lr}               @ the routine's own frame (the caller's r4), returning to ret_here
    movs r1, #0x26
    ldr r3, lit_getmondata
    bl callr3
    ldr r3, lit_back            @ on in the routine, after its GetMonData
    bx r3
ret_here:
    adds r0, r5, #0
    bl gmax_update
    pop {r5}
    pop {r0}
    bx r0

callr3:
    bx r3
callr4:
    bx r4

@ gmax_update(r0 = the Pokemon): a mark of ours already up goes (found by its callback, so nothing is kept anywhere),
@ its tiles and palette with it; a new one when the bit is set
gmax_update:
    push {r4, r5, r6, lr}
    adds r5, r0, #0
    movs r6, #0
gu_scan:
    movs r4, #0x44
    muls r4, r6
    ldr r0, lit_gsprites
    adds r4, r4, r0
    adds r0, r4, #0
    adds r0, #0x3E
    ldrb r0, [r0]
    lsls r0, r0, #31            @ inUse
    beq gu_next
    ldr r0, [r4, #0x1C]         @ sprite->callback
    ldr r1, lit_cb
    cmp r0, r1
    bne gu_next
    adds r0, r4, #0
    ldr r3, lit_destroysprite
    bl callr3
gu_next:
    adds r6, #1
    cmp r6, #64
    blo gu_scan
    ldr r0, lit_tag
    ldr r3, lit_freetiles
    bl callr3
    ldr r0, lit_tag
    ldr r3, lit_freepal
    bl callr3
    adds r0, r5, #0
    adds r0, #0x4E
    ldrb r0, [r0]
    lsls r0, r0, #24
    bpl gu_ret                  @ no Gigantamax bit
    ldr r0, lit_sheet
    ldr r3, lit_loadsheet
    bl callr3
    ldr r0, lit_palette
    ldr r3, lit_loadpal
    bl callr3
    @ where: on the name row at the panel's right edge when the nickname (mon +8, up to 10 letters, 0xFF ends; its
    @ width from the normal font's own table, as the summary prints it from x 8) leaves room, else in the picture's
    @ bottom right corner - the mark never covers a name
    adds r1, r5, #0
    adds r1, #8                 @ (adds rD, rN, #imm takes 0-7 in Thumb-1)
    movs r2, #0                 @ the nickname's width
    movs r3, #0
nw_loop:
    ldrb r0, [r1, r3]
    cmp r0, #0xFF
    beq nw_done
    ldr r4, lit_widths
    ldrb r0, [r4, r0]
    adds r2, r2, r0
    adds r3, #1
    cmp r3, #10
    blo nw_loop
nw_done:
    movs r1, #ROW_X
    movs r6, #ROW_Y
    cmp r2, #MAX_NAME
    bls nw_place
    movs r1, #ICON_X
    movs r6, #ICON_Y
nw_place:
    adds r2, r6, #0
    ldr r0, lit_template
    movs r3, #0
    ldr r4, lit_createsprite
    bl callr4
    cmp r0, #64
    bhs gu_ret
    movs r1, #0x44
    muls r1, r0
    ldr r2, lit_gsprites
    adds r1, r1, r2
    strh r5, [r1, #0x2E]        @ data[0], data[1]: the Pokemon it marks
    lsrs r0, r5, #16
    strh r0, [r1, #0x30]
gu_ret:
    pop {r4, r5, r6, pc}

@ the mark's callback: hidden while that Pokemon (the summary's copy) has no Gigantamax bit - another one or an egg
@ is shown - or while the summary's picture of it is hidden
gmax_cb:
    ldrh r1, [r0, #0x2E]
    ldrh r2, [r0, #0x30]
    lsls r2, r2, #16
    orrs r1, r2
    adds r1, #0x4E
    ldrb r1, [r1]
    movs r3, #1                 @ hide
    lsls r1, r1, #24
    bpl cb_set
    ldr r1, lit_summary
    ldr r1, [r1]
    cmp r1, #0
    beq cb_set
    ldr r2, lit_monid
    ldrb r1, [r1, r2]           @ the picture's sprite id
    cmp r1, #64
    bhs cb_set
    movs r2, #0x44
    muls r2, r1
    ldr r1, lit_gsprites
    adds r1, r1, r2
    adds r1, #0x3E
    ldrb r1, [r1]
    lsrs r1, r1, #2             @ its invisible bit
    movs r3, #1
    ands r3, r1
cb_set:
    adds r0, #0x3E
    ldrb r1, [r0]
    movs r2, #4
    bics r1, r2
    lsls r3, r3, #2
    orrs r1, r3
    strb r1, [r0]
    bx lr

PAD
.align 2
lit_ret:            .word RET_HERE
lit_getmondata:     .word 0x0806A519
lit_back:           .word 0x081C4A11
lit_gsprites:       .word 0x02020630
lit_cb:             .word GMAX_CB
lit_destroysprite:  .word 0x080070E9
lit_tag:            .word TAG
lit_freetiles:      .word 0x08008569        @ FreeSpriteTilesByTag
lit_freepal:        .word 0x0800884D        @ FreeSpritePaletteByTag
lit_sheet:          .word SHEET
lit_loadsheet:      .word 0x080084F9        @ LoadSpriteSheet
lit_palette:        .word PALETTE
lit_loadpal:        .word 0x08008745        @ LoadSpritePalette
lit_template:       .word TEMPLATE
lit_createsprite:   .word 0x08006DF5        @ CreateSprite
lit_widths:         .word 0x086542E4        @ the normal font's glyph widths
lit_summary:        .word 0x0203CF1C        @ sMonSummaryScreen
lit_monid:          .word 0x000040D3        @ its picture's sprite id (the ball's is +0x40D4)
