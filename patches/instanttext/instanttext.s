@ Instant text (Hyper Emerald v5.7): a 4th Text Speed, "Instant", after Slow / Mid / Fast.
@
@ PRINTING. run_printers replaces RunTextPrinters (8-byte trampoline on its first instruction; a whole
@ replacement, so it pushes lr itself before any bl). It is the game's loop over the 32 printers, plus: when the
@ player's speed (GetPlayerTextSpeed, which answers MID while gTextFlags.forceMidTextSpeed is set) is Instant and
@ the printer runs at the fastest speed (textSpeed 0 - Instant's delay is Fast's), it keeps calling RenderFont in
@ the same frame for as long as it prints a glyph. A wait of any kind - {PAUSE}, the button arrow, a scroll, the
@ end - returns something else and stops the burst, so pages, prompts and pauses behave as before. The window is
@ copied to VRAM once after a burst instead of once per glyph (one DMA request each would flood the queue).
@ Printers started with a slower explicit speed keep it.
@
@ OPTION MENU. draw_speed replaces TextSpeed_DrawChoices (8-byte trampoline): the four words at fixed x
@ positions from XS_ADDR (computed by the patcher from the font's widths), the selected one red.
.thumb

run_printers:
    push {r4, r5, r6, r7, lr}
    mov r2, r9
    mov r3, r8
    push {r2, r3}
    ldr r0, lit_disable
    ldrb r0, [r0]               @ gDisableTextPrinters
    cmp r0, #0
    bne rp_ret
    ldr r3, lit_get_speed
    bl callr3
    movs r7, #0                 @ r7: the player's speed is Instant
    cmp r0, #3
    bne rp_start
    movs r7, #1
rp_start:
    ldr r5, lit_printers        @ sTextPrinters[0], 0x24 bytes each
    movs r6, #0
rp_next:
    ldrb r0, [r5, #0x1B]        @ .active
    cmp r0, #0
    beq rp_step
    movs r0, #0
    mov r8, r0                  @ r8: glyphs printed in this burst, not copied to VRAM yet
    ldr r0, lit_cap
    mov r9, r0                  @ r9: glyphs left before the burst yields to the next frame
rp_render:
    adds r0, r5, #0
    ldr r3, lit_render_font
    bl callr3
    lsls r4, r0, #16
    lsrs r4, r4, #16
    cmp r4, #1                  @ RENDER_FINISH
    beq rp_finish
    cmp r4, #3                  @ RENDER_UPDATE
    beq rp_callback
    cmp r4, #0                  @ RENDER_PRINT
    bne rp_flush
    cmp r7, #0
    beq rp_copy
    ldrb r0, [r5, #0x1D]        @ .textSpeed
    cmp r0, #0
    bne rp_copy
    movs r0, #1
    mov r8, r0
    b rp_callback
rp_copy:
    ldrb r0, [r5, #4]           @ .printerTemplate.windowId
    movs r1, #2                 @ COPYWIN_GFX
    ldr r3, lit_copy_win
    bl callr3
rp_callback:
    ldr r3, [r5, #0x10]         @ .callback(printer, cmd), as the game does for PRINT and UPDATE
    cmp r3, #0
    beq rp_more
    adds r0, r5, #0
    adds r1, r4, #0
    bl callr3
rp_more:
    cmp r4, #0                  @ only a printed glyph goes on
    bne rp_flush
    mov r0, r8
    cmp r0, #0
    beq rp_flush                @ not a burst
    ldrb r0, [r5, #0x1B]
    cmp r0, #0
    beq rp_flush                @ the callback stopped the printer
    mov r0, r9
    subs r0, #1
    mov r9, r0
    bne rp_render
    b rp_flush
rp_finish:
    movs r0, #0
    strb r0, [r5, #0x1B]
rp_flush:
    mov r0, r8
    cmp r0, #0
    beq rp_step
    ldrb r0, [r5, #4]
    movs r1, #2
    ldr r3, lit_copy_win
    bl callr3
rp_step:
    adds r5, #0x24
    adds r6, #1
    cmp r6, #32
    blo rp_next
rp_ret:
    pop {r2, r3}
    mov r9, r2
    mov r8, r3
    pop {r4, r5, r6, r7}
    pop {r0}
    bx r0

@ TextSpeed_DrawChoices(r0 = selection): Slow, Mid, Fast, Instant on the Text Speed row (y 0)
draw_speed:
    push {r4, r5, r6, lr}
    lsls r4, r0, #24
    lsrs r4, r4, #24
    movs r5, #0
ds_loop:
    lsls r0, r5, #2
    ldr r1, lit_names
    ldr r0, [r1, r0]
    ldr r1, lit_xs
    ldrb r1, [r1, r5]
    movs r2, #0
    movs r3, #0
    cmp r4, r5
    bne ds_draw
    movs r3, #1                 @ selected: the red style
ds_draw:
    ldr r6, lit_draw_choice
    bl callr6
    adds r5, #1
    cmp r5, #4
    blo ds_loop
    pop {r4, r5, r6}
    pop {r0}
    bx r0

callr3:
    bx r3
callr6:
    bx r6

.align 2
lit_disable:     .word 0x03002F84       @ gDisableTextPrinters
lit_printers:    .word 0x020201B0       @ sTextPrinters
lit_get_speed:   .word 0x08197965       @ GetPlayerTextSpeed
lit_render_font: .word 0x08004819       @ RenderFont
lit_copy_win:    .word 0x08003659       @ CopyWindowToVram
lit_cap:         .word 1024
lit_draw_choice: .word 0x080BAB69       @ DrawOptionMenuChoice(text, x, y, style)
lit_names:       .word NAMES_ADDR
lit_xs:          .word XS_ADDR
