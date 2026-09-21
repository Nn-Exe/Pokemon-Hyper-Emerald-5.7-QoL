@ R opens the DexNav; Auto Run moves to the Option menu (Hyper Emerald v5.7). Apply after dexnavchain.
@ R used to toggle auto-run in the field. It now opens the DexNav straight from the field, and B or a
@ registration there comes straight back. Auto Run takes the Option menu's Button Mode row: that row keeps
@ saving into optionsButtonMode (SaveBlock2+0x13), with 0 for Off and 4 for On. The game only acts on that
@ byte when it is exactly 1 (LR) or 2 (L=A), so 4 behaves as Normal everywhere else.
.thumb

@ ---- R in the field ---------------------------------------------------------------------------------
@ r_hook(r0 = FieldInput*): the ProcessPlayerFieldInput trampoline used to lead to auto-run's toggle; it
@ leads here now. Re-executes the prologue it replaced (push {r4-r6,lr}; sub sp,#8; r5 = input), then
@ either opens the DexNav and returns TRUE - the caller locks the field controls, as for the start menu -
@ or resumes the original at its 4th instruction.
r_hook:
    push {r4, r5, r6, lr}
    sub sp, #8
    adds r5, r0, #0
    ldr r0, lit_gmain
    ldrh r0, [r0, #0x2E]        @ newKeys
    movs r1, #1
    lsls r1, r1, #8             @ R
    tst r0, r1
    beq rh_resume
    ldr r1, lit_avatar
    ldrb r1, [r1, #3]           @ tileTransitionState: standing, or at the centre of a tile, as for START
    cmp r1, #1
    beq rh_resume
    ldr r0, lit_flag_dex        @ no Pokedex yet, no DexNav - the start menu's own rule
    ldr r3, lit_flagget
    bl call3
    cmp r0, #0
    beq rh_resume
    bl open_dexnav
    movs r0, #1
    add sp, #8
    pop {r4, r5, r6, pc}
rh_resume:
    ldr r0, lit_sv_result_hi    @ the original 4th instruction: ldr r0, =0x020375F2
    ldr r1, lit_resume
    bx r1

@ open_dexnav(): fade out, then hand over through the DexNav's own start-menu callback. Bit 7 of the
@ hunt's flags sends its exit back to the field instead of the start menu.
open_dexnav:
    push {r4, lr}
    sub sp, #4
    ldr r0, lit_state
    ldrb r1, [r0, #9]
    movs r2, #0x80
    orrs r1, r2
    strb r1, [r0, #9]
    movs r0, #5                 @ SE_SELECT
    ldr r3, lit_playse
    bl call3
    ldr r3, lit_freezeobjs
    bl call3
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #0
    movs r3, #16
    ldr r4, lit_beginfade
    bl call4
    ldr r0, lit_task_open
    movs r1, #80
    ldr r3, lit_createtask
    bl call3
    add sp, #4
    pop {r4, pc}

@ task_open(r0 = taskId): the DexNav's callback waits out the fade and switches to its screen
task_open:
    push {r4, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    ldr r3, lit_menucb
    bl call3
    cmp r0, #0
    beq to_ret
    adds r0, r4, #0
    ldr r3, lit_destroytask
    bl call3
to_ret:
    pop {r4, pc}

@ ---- the Option menu ---------------------------------------------------------------------------------
@ opt_input(r0 = selection) -> r0: stands in for ButtonMode_ProcessInput. Left or right flips 0 / 4.
opt_input:
    push {lr}
    lsls r0, r0, #24
    lsrs r0, r0, #24
    ldr r1, lit_gmain
    ldrh r1, [r1, #0x2E]
    movs r2, #0x30              @ RIGHT | LEFT
    tst r1, r2
    beq oi_ret
    cmp r0, #4
    beq oi_off
    movs r0, #4
    b oi_arrow
oi_off:
    movs r0, #0
oi_arrow:
    ldr r1, lit_arrow           @ sArrowPressed: the menu copies the window to VRAM when it is set
    movs r2, #1
    strb r2, [r1]
oi_ret:
    pop {pc}

@ opt_draw(r0 = selection): stands in for ButtonMode_DrawChoices. "Off" on the left, "On" on the right,
@ the chosen one in red - the game's own On/Off strings and DrawOptionMenuChoice.
opt_draw:
    push {r4, r5, lr}
    lsls r0, r0, #24
    lsrs r0, r0, #24
    movs r5, #0
    cmp r0, #4
    bne od_go
    movs r5, #1
od_go:
    movs r3, #1
    eors r3, r5
    ldr r0, lit_str_off
    movs r1, #104
    movs r2, #64                @ the Button Mode row
    ldr r4, lit_drawchoice
    bl call4
    adds r3, r5, #0
    ldr r0, lit_str_on
    movs r1, #184
    movs r2, #64
    bl call4
    pop {r4, r5, pc}

call3:
    bx r3
call4:
    bx r4

.align 2
lit_gmain:          .word 0x030022C0
lit_avatar:         .word 0x02037590            @ gPlayerAvatar
lit_flag_dex:       .word 0x00000861            @ FLAG_SYS_POKEDEX_GET
lit_flagget:        .word 0x0809D791
lit_sv_result_hi:   .word 0x020375F2
lit_resume:         .word 0x0809C01D
lit_state:          .word STATE_ADDR
lit_playse:         .word 0x080A37A5
lit_freezeobjs:     .word 0x08097495            @ FreezeObjectEvents
lit_beginfade:      .word 0x080A1AD5            @ BeginNormalPaletteFade
lit_task_open:      .word TASK_OPEN_ADDR
lit_createtask:     .word 0x080A8FB1
lit_destroytask:    .word 0x080A909D
lit_menucb:         .word MENUCB_ADDR           @ the DexNav's start-menu callback
lit_arrow:          .word 0x02039B48            @ sArrowPressed
lit_str_off:        .word 0x085EE5FD            @ gText_BattleSceneOff
lit_str_on:         .word 0x085EE5F4            @ gText_BattleSceneOn
lit_drawchoice:     .word 0x080BAB69            @ DrawOptionMenuChoice(text, x, y, style)
