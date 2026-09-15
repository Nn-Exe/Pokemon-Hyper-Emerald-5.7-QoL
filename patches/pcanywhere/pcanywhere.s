@ PC in the SELECT key-item popup (Hyper Emerald v5.7).
@ SELECT opens the popup (always, now); d-pad uses a registered item, A opens the PC, B or SELECT closes it.
@ Replaces keyreg's draw_popup (called from usereg) and popup_task (via its literal); keyreg itself is untouched
@ apart from that call, that literal and two branches.
.thumb

@ new_draw() -> r0 = window id. Four registered slots as before, plus an "A PC" line.
new_draw:
    push {r4, r5, r6, lr}
    sub sp, #0x14
    ldr r0, lit_template
    ldr r3, lit_addwindow
    bl call3
    lsls r0, r0, #24
    lsrs r4, r0, #24            @ window id
    ldr r0, lit_drawstdframe
    mov r12, r0
    adds r0, r4, #0
    movs r1, #1
    ldr r2, lit_214
    movs r3, #14
    bl callip                   @ DrawStdFrameWithCustomTileAndPalette(win, TRUE, 0x214, 14)
    ldr r5, lit_strvar4
    movs r6, #0
nd_loop:
    ldr r0, lit_arrows
    ldrb r0, [r0, r6]
    strb r0, [r5]
    movs r0, #0
    strb r0, [r5, #1]
    adds r5, #2
    adds r0, r6, #0
    bl slot_ptr
    ldrh r0, [r0]
    cmp r0, #0
    beq nd_empty
    adds r1, r5, #0
    ldr r3, lit_copyitemname
    bl call3                    @ CopyItemName(item, dst)
    b nd_adv
nd_empty:
    adds r0, r5, #0
    ldr r1, lit_emptytext
    ldr r3, lit_stringcopy
    bl call3
nd_adv:
    ldrb r0, [r5]
    cmp r0, #0xFF
    beq nd_term
    adds r5, #1
    b nd_adv
nd_term:
    movs r0, #0xFE              @ newline
    strb r0, [r5]
    adds r5, #1
    adds r6, #1
    cmp r6, #4
    blo nd_loop
    adds r0, r5, #0
    ldr r1, lit_pcline
    ldr r3, lit_stringcopy
    bl call3                    @ "A PC" + terminator
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    str r0, [sp, #0xC]
    ldr r0, lit_colors
    str r0, [sp, #8]
    ldr r0, lit_strvar4
    str r0, [sp, #0x10]
    ldr r0, lit_addtextprinter4
    mov r12, r0
    adds r0, r4, #0
    movs r1, #1
    movs r2, #4
    movs r3, #2
    bl callip
    adds r0, r4, #0
    add sp, #0x14
    pop {r4, r5, r6, pc}

@ new_task(r0 = taskId): d-pad -> item, A -> PC, B/SELECT -> cancel
new_task:
    push {r4, r5, r6, r7, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r1, r1, r0
    ldrh r0, [r1, #0xA]         @ data[1]: 0 on the creation frame -> arm and wait
    cmp r0, #0
    bne nt_input
    movs r0, #1
    strh r0, [r1, #0xA]
    b nt_ret
nt_input:
    ldr r0, lit_gmain
    ldrh r5, [r0, #0x2E]        @ newKeys
    movs r0, #0x40              @ UP
    tst r0, r5
    beq nt_k1
    movs r6, #0
    b nt_act
nt_k1:
    movs r0, #0x10              @ RIGHT
    tst r0, r5
    beq nt_k2
    movs r6, #1
    b nt_act
nt_k2:
    movs r0, #0x80              @ DOWN
    tst r0, r5
    beq nt_k3
    movs r6, #2
    b nt_act
nt_k3:
    movs r0, #0x20              @ LEFT
    tst r0, r5
    beq nt_k4
    movs r6, #3
    b nt_act
nt_k4:
    movs r0, #1                 @ A -> PC
    tst r0, r5
    beq nt_k5
    movs r7, #0
    mvns r7, r7                 @ r7 = -1 marks "PC"
    b nt_close
nt_k5:
    movs r0, #6                 @ B or SELECT -> cancel
    tst r0, r5
    beq nt_ret
    movs r7, #0
    b nt_close
nt_act:
    adds r0, r6, #0
    bl slot_ptr
    ldrh r7, [r0]
    cmp r7, #0
    beq nt_ret                  @ empty slot: ignore
nt_close:
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r1, r1, r0
    ldrh r5, [r1, #8]           @ window id
    adds r0, r5, #0
    movs r1, #1
    ldr r3, lit_clearstdwin
    bl call3
    adds r0, r5, #0
    ldr r3, lit_removewindow
    bl call3
    adds r0, r4, #0
    ldr r3, lit_destroytask
    bl call3
    cmp r7, #0
    beq nt_cancel
    adds r0, r7, #1
    beq nt_pc
    adds r0, r7, #0
    bl use_item
    b nt_ret
nt_pc:
    ldr r0, lit_pcscript
    ldr r3, lit_setupscript
    bl call3                    @ the PC menu (its releaseall unfreezes and unlocks when you log off)
    b nt_ret
nt_cancel:
    ldr r3, lit_unfreeze
    bl call3
    ldr r3, lit_unlock
    bl call3
nt_ret:
    pop {r4, r5, r6, r7, pc}

@ use_item(r0 = item): gSpecialVar_ItemId = item; data[3] of CreateTask(ItemId_GetFieldFunc(item), 8) = 1
use_item:
    push {r4, lr}
    adds r4, r0, #0
    ldr r1, lit_itemid
    strh r4, [r1]
    adds r0, r4, #0
    ldr r3, lit_getfieldfunc
    bl call3
    movs r1, #8
    ldr r3, lit_createtask
    bl call3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    lsls r1, r0, #2
    adds r1, r1, r0
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r1, r1, r0
    movs r0, #1
    strh r0, [r1, #0xE]
    pop {r4, pc}

@ slot_ptr(r0 = i) -> r0 = &slot[i]; clobbers r1
slot_ptr:
    ldr r1, lit_sb1ptr
    ldr r1, [r1]
    cmp r0, #0
    bne sp_extra
    ldr r0, lit_496
    adds r0, r0, r1
    bx lr
sp_extra:
    lsls r0, r0, #1
    adds r0, r0, r1
    ldr r1, lit_9c0
    adds r0, r0, r1
    bx lr

call3:
    bx r3
callip:
    bx r12

.align 2
lit_template:        .word TEMPLATE_ADDR
lit_pcline:          .word PCLINE_ADDR
lit_pcscript:        .word PCSCRIPT_ADDR
lit_arrows:          .word 0x08FD91CC
lit_colors:          .word 0x08FD91D0
lit_emptytext:       .word 0x08FD91D4
lit_sb1ptr:          .word 0x03005D8C
lit_496:             .word 0x496
lit_9c0:             .word 0x9C0
lit_itemid:          .word 0x0203CE7C
lit_gtasks:          .word 0x03005E00
lit_gmain:           .word 0x030022C0
lit_strvar4:         .word 0x02021FC4
lit_214:             .word 0x214
lit_setupscript:     .word 0x08098EF9
lit_getfieldfunc:    .word 0x080D75D9
lit_createtask:      .word 0x080A8FB1
lit_addwindow:       .word 0x08003381
lit_drawstdframe:    .word 0x08197E81
lit_copyitemname:    .word 0x080D6645
lit_stringcopy:      .word 0x08008BA1
lit_addtextprinter4: .word 0x08199EED
lit_clearstdwin:     .word 0x08198071
lit_removewindow:    .word 0x08003575
lit_destroytask:     .word 0x080A909D
lit_unfreeze:        .word 0x080984F5
lit_unlock:          .word 0x08098E61
