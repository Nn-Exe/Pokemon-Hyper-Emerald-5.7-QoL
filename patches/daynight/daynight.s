@ Day/Night: On / Off in the Option menu (Hyper Emerald v5.7). Thumb-1 only.
@ Four routines, assembled one after another by daynight_patch.py (it splits this file at the "@@" lines and
@ fills in DRAW_ADDR). The setting is bit 4 of SaveBlock2+0x15 (the options byte's unused half): 1 = Off.

@@ gate
@ Called from the hack's tint routine (0x08CFE452) in place of `ldr r0, =0x02021685; ldrb r1, [r0]`, which is
@ followed by `cmp r1, #0; bne <plain copy>`. Returns r1 != 0 when the tint must be skipped: the hack's own
@ "no tint now" byte, or this option. lr is free there (TransferPlttBuffer pushed it); r0 is reloaded after.
tint_gate:
    ldr r0, g_dnsflag
    ldrb r1, [r0]
    cmp r1, #0
    bne tg_ret
    ldr r1, g_sb2
    ldr r1, [r1]
    ldrb r1, [r1, #0x15]
    movs r0, #0x10
    ands r1, r0
tg_ret:
    bx lr
g_dnsflag:          .word 0x02021685
g_sb2:              .word 0x03005D90            @ gSaveBlock2Ptr

@@ draw
@ dn_draw(): "On" and "Off" on the menu's 7th row, the chosen one in red - the game's own strings and
@ DrawOptionMenuChoice, placed as on the Battle Scene row.
dn_draw:
    push {r4, r5, r6, lr}
    ldr r1, d_sb2
    ldr r1, [r1]
    ldrb r1, [r1, #0x15]
    lsrs r1, r1, #4
    movs r5, #1
    ands r5, r1                 @ r5 = 1 when the tint is off
    ldr r4, d_drawchoice
    movs r3, #1
    eors r3, r5
    ldr r0, d_str_on
    movs r1, #104
    movs r2, #96
    bl d_call4
    movs r0, #1                 @ the font
    ldr r1, d_str_off
    movs r2, #198
    ldr r3, d_rightalign
    bl d_call3                  @ GetStringRightAlignXOffset(font, text, 198)
    lsls r1, r0, #24
    lsrs r1, r1, #24
    ldr r0, d_str_off
    movs r2, #96
    adds r3, r5, #0
    bl d_call4
    pop {r4, r5, r6, pc}
d_call3:
    bx r3
d_call4:
    bx r4
    mov r8, r8                  @ pad: the literals must sit on a 4-byte boundary (no .align: keystone pads with a Thumb-2 hint)
d_sb2:              .word 0x03005D90
d_drawchoice:       .word 0x080BAB69            @ DrawOptionMenuChoice(text, x, y, style)
d_rightalign:       .word 0x081DB369            @ GetStringRightAlignXOffset
d_str_on:           .word 0x085EE5F4            @ gText_BattleSceneOn
d_str_off:          .word 0x085EE5FD            @ gText_BattleSceneOff

@@ tail
@ DrawOptionMenuTexts calls this (through a veneer) where it called CopyWindowToVram(1, 3) after printing the
@ row labels: the row's choices are drawn first, then the window is copied as before.
texts_tail:
    push {r4, lr}
    ldr r3, t_draw
    bl t_call3
    movs r0, #1
    movs r1, #3
    ldr r3, t_copywin
    bl t_call3
    pop {r4, pc}
t_call3:
    bx r3
    mov r8, r8                  @ pad
t_draw:             .word DRAW_ADDR
t_copywin:          .word 0x08003659            @ CopyWindowToVram

@@ case6
@ Task_OptionMenuProcessInput branches here (through a veneer) for the 7th row, where it used to return. Left or
@ right flips the bit in the save at once - the menu saves every other row on the way out and has no way to
@ leave without saving, so this is the same - and redraws the two words. Ends in the task's own tail, which
@ copies the window when sArrowPressed is set and returns.
case6:
    ldr r1, c_gmain
    ldrh r1, [r1, #0x2E]        @ newKeys
    movs r2, #0x30              @ RIGHT | LEFT
    tst r1, r2
    beq c6_done
    ldr r1, c_sb2
    ldr r1, [r1]
    ldrb r0, [r1, #0x15]
    movs r2, #0x10
    eors r0, r2
    strb r0, [r1, #0x15]
    ldr r1, c_arrow
    movs r2, #1
    strb r2, [r1]
    ldr r3, c_draw
    bl c_call3
c6_done:
    ldr r3, c_tail
c_call3:
    bx r3
    mov r8, r8                  @ pad
c_gmain:            .word 0x030022C0
c_sb2:              .word 0x03005D90
c_arrow:            .word 0x02039B48            @ sArrowPressed
c_draw:             .word DRAW_ADDR
c_tail:             .word 0x080BAA47            @ Task_OptionMenuProcessInput's common tail
