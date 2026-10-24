@ startclock: a framed clock box on the Start menu, beside the Quest Log's "[R] Journal" box - "Thu 10:29 AM".
@ The day, hour and minute are the game's own clock (RtcCalcLocalTime: the cartridge clock less the offset the
@ player set). (Until 2026-10-23 it also said the time of day, "(Day)", under the Journal's box: the user, "remove
@ the evening, whatever, and move into the same row as R Journey".)
@ Two words are chained, both of them the Quest Log's own hooks: InitStartMenuStep's step 3 (the jump table entry
@ 0x0809F8C4, entered in Thumb at an even address by `mov pc`) and HandleStartMenuInput's trampoline word
@ (0x0809FAC8: its first instruction, so lr is live). Ours run first, then the Quest Log's as before.
@ State in EWRAM scratch (0x02039E48, after the Quest Log's 8 bytes of the 64 measured free): a magic word, the
@ window id, the minute drawn, the template used, the hour drawn, then the text.

case3_clock:
    push {lr}
    bl show_clock
    pop {r0}
    ldr r0, lit_qcase3
    bx r0

hsi_clock:
    push {lr}
    bl clock_tick
    pop {r3}
    mov lr, r3
    ldr r3, lit_qhsi
    bx r3

callr3:
    bx r3

@ has_journal -> r0 = 1 when the Journal is in the Bag (the Quest Log's own test)
has_journal:
    push {lr}
    ldr r0, lit_journal
    movs r1, #1
    ldr r3, lit_hasitem
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    pop {r1}
    bx r1

@ show_clock: the box, on the Journal's row to its right (x 11), under the Safari / Pyramid window (y 7), or at the
@ top left without the Journal (templates 1, 2, 0)
show_clock:
    push {r4, r5, lr}
    bl clock_remove             @ never two
    movs r5, #2
    ldr r3, lit_safari
    bl callr3
    lsls r0, r0, #24
    bne sc_add
    ldr r3, lit_pyramid
    bl callr3
    lsls r0, r0, #24
    bne sc_add
    movs r5, #0
    bl has_journal
    cmp r0, #0
    beq sc_add
    movs r5, #1
sc_add:
    lsls r0, r5, #3
    ldr r1, lit_templates
    adds r0, r0, r1
    ldr r3, lit_addwindow
    bl callr3
    lsls r0, r0, #24
    lsrs r4, r0, #24
    cmp r4, #0xFF
    beq sc_ret
    ldr r0, lit_scratch
    ldr r1, lit_magic
    str r1, [r0]
    strb r4, [r0, #4]
    movs r1, #0xFF
    strb r1, [r0, #5]           @ no minute drawn yet
    strb r5, [r0, #6]
    adds r0, r4, #0
    ldr r3, lit_putwin
    bl callr3
    adds r0, r4, #0
    movs r1, #0
    ldr r3, lit_drawframe
    bl callr3
    bl clock_draw
sc_ret:
    pop {r4, r5, pc}

@ clock_tick: every frame the menu waits for a key. A, B or START (and R with the Journal: the Quest Log opens)
@ take the box down, as the Journal's goes; otherwise the time, redrawn when it changes
clock_tick:
    push {r4, lr}
    ldr r0, lit_scratch
    ldr r1, [r0]
    ldr r2, lit_magic
    cmp r1, r2
    bne ct_ret
    ldr r4, lit_gmain
    ldrh r1, [r4, #0x2E]
    movs r0, #0xB
    tst r0, r1
    bne ct_remove
    ldr r0, lit_rkey
    tst r0, r1
    beq ct_draw
    bl has_journal
    cmp r0, #0
    beq ct_draw
ct_remove:
    bl clock_remove
    b ct_ret
ct_draw:
    bl clock_draw
ct_ret:
    pop {r4, pc}

@ clock_draw: the time now; when its hour or minute is not the one drawn, the text at scratch + 8, then the window
clock_draw:
    push {r4, r5, r6, r7, lr}
    sub sp, #12
    ldr r3, lit_rtccalc
    bl callr3
    ldr r6, lit_scratch
    ldr r7, lit_localtime
    ldrb r0, [r7, #3]           @ minute
    ldrb r1, [r6, #5]
    ldrb r2, [r7, #2]           @ hour
    ldrb r3, [r6, #7]
    cmp r0, r1
    bne cd_new
    cmp r2, r3
    beq cd_ret
cd_new:
    strb r0, [r6, #5]
    strb r2, [r6, #7]
    adds r5, r6, #0
    adds r5, #8
    @ the day of the week: (the clock's day + the offset's day + 5) mod 7, 0 = Sunday (the game's day count: 1 =
    @ Saturday 1 January 2000; measured: the cartridge clock's 22 Oct 2026, a Thursday, is day 9792)
    movs r1, #0
    ldrsh r0, [r7, r1]
    ldr r1, lit_sb2
    ldr r1, [r1]
    movs r2, #0x98
    ldrsh r1, [r1, r2]
    adds r0, r0, r1
    ldr r1, lit_bias
    adds r0, r0, r1
    movs r1, #7
    ldr r3, lit_umod
    bl callr3
    lsls r0, r0, #2
    ldr r1, lit_days
    adds r1, r1, r0
    adds r0, r5, #0
    bl copy
    movs r1, #0                 @ " "
    strb r1, [r0]
    adds r5, r0, #1
    @ the hour, 12-hour
    ldrb r4, [r7, #2]
    adds r1, r4, #0
    cmp r1, #12
    blo cd_h12
    subs r1, #12
cd_h12:
    cmp r1, #0
    bne cd_hnz
    movs r1, #12
cd_hnz:
    adds r0, r5, #0
    movs r2, #0                 @ left-aligned
    movs r3, #2
    ldr r6, lit_convint
    bl callr6
    movs r1, #0xF0              @ ":"
    strb r1, [r0]
    adds r0, #1
    ldrb r1, [r7, #3]
    movs r2, #2                 @ leading zeros
    movs r3, #2
    ldr r6, lit_convint
    bl callr6
    ldr r1, lit_am
    cmp r4, #12
    blo cd_ampm
    ldr r1, lit_pm
cd_ampm:
    bl copy
    @ into the window
    ldr r6, lit_scratch
    ldrb r0, [r6, #4]
    movs r1, #0x11
    ldr r3, lit_fillwin
    bl callr3
    movs r0, #0                 @ y
    str r0, [sp]
    movs r0, #0xFF              @ TEXT_SKIP_DRAW
    str r0, [sp, #4]
    movs r0, #0
    str r0, [sp, #8]
    ldrb r0, [r6, #4]
    movs r1, #1
    adds r2, r6, #0
    adds r2, #8
    movs r3, #2
    ldr r6, lit_addtext
    bl callr6
    ldr r6, lit_scratch
    ldrb r0, [r6, #4]
    movs r1, #2
    ldr r3, lit_copywin
    bl callr3
cd_ret:
    add sp, #12
    pop {r4, r5, r6, r7, pc}

callr6:
    bx r6

@ copy: r0 = dest, r1 = the text (0xFF-terminated), the 0xFF too -> r0 = where the 0xFF went
copy:
    ldrb r2, [r1]
    strb r2, [r0]
    cmp r2, #0xFF
    beq cp_done
    adds r0, #1
    adds r1, #1
    b copy
cp_done:
    bx lr

@ clock_remove: take the box down, if it is up and gWindows still holds our template at its id
clock_remove:
    push {r4, r5, lr}
    ldr r5, lit_scratch
    ldr r0, [r5]
    ldr r1, lit_magic
    cmp r0, r1
    bne cr_ret
    movs r0, #0
    str r0, [r5]
    ldrb r4, [r5, #4]
    cmp r4, #32                 @ WINDOWS_MAX
    bhs cr_ret
    ldrb r1, [r5, #6]
    cmp r1, #2
    bhi cr_ret
    lsls r1, r1, #3
    ldr r2, lit_templates
    adds r1, r1, r2
    lsls r0, r4, #1
    adds r0, r0, r4
    lsls r0, r0, #2
    ldr r2, lit_gwindows
    adds r0, r0, r2
    ldr r2, [r0]
    ldr r3, [r1]
    cmp r2, r3
    bne cr_ret
    ldr r2, [r0, #4]
    ldr r3, [r1, #4]
    cmp r2, r3
    bne cr_ret
    adds r0, r4, #0
    movs r1, #0
    ldr r3, lit_clearframe
    bl callr3
    adds r0, r4, #0
    movs r1, #2
    ldr r3, lit_copywin
    bl callr3
    adds r0, r4, #0
    ldr r3, lit_removewin
    bl callr3
    movs r0, #0
    ldr r3, lit_schedcopy
    bl callr3
cr_ret:
    pop {r4, r5, pc}

PAD
.align 2
lit_qcase3:         .word QCASE3            @ the Quest Log's step 3 (Thumb)
lit_qhsi:           .word QHSI              @ the Quest Log's HandleStartMenuInput stub (Thumb)
lit_journal:        .word 0x0000016B
lit_hasitem:        .word 0x080D6725        @ CheckBagHasItem
lit_safari:         .word 0x080FC0A1        @ GetSafariZoneFlag
lit_pyramid:        .word 0x081A9E41        @ InBattlePyramid
lit_templates:      .word TEMPLATES
lit_addwindow:      .word 0x08003381
lit_scratch:        .word 0x02039E48
lit_magic:          .word 0x4B4F4C43        @ "CLOK"
lit_putwin:         .word 0x0800378D
lit_drawframe:      .word 0x081973FD        @ DrawStdWindowFrame
lit_gmain:          .word 0x030022C0
lit_rkey:           .word 0x00000100
lit_rtccalc:        .word 0x0802F589        @ RtcCalcLocalTime
lit_localtime:      .word 0x03005CF8        @ gLocalTime: s16 days, s8 hours, minutes, seconds
lit_sb2:            .word 0x03005D90        @ gSaveBlock2Ptr (+0x98: localTimeOffset)
lit_bias:           .word 70005             @ 7 x 10000 (keeps it positive) + 5 (day 1 a Saturday)
lit_umod:           .word 0x082E7BE1        @ __umodsi3
lit_days:           .word DAYS
lit_convint:        .word 0x08008CC1        @ ConvertIntToDecimalStringN
lit_am:             .word AM
lit_pm:             .word PM
lit_fillwin:        .word 0x08003C49        @ FillWindowPixelBuffer
lit_addtext:        .word 0x080045D1        @ AddTextPrinterParameterized
lit_copywin:        .word 0x08003659        @ CopyWindowToVram
lit_gwindows:       .word 0x02020004
lit_clearframe:     .word 0x08198071        @ ClearStdWindowAndFrameToTransparent
lit_removewin:      .word 0x08003575
lit_schedcopy:      .word 0x081999BD        @ ScheduleBgCopyTilemapToVram
