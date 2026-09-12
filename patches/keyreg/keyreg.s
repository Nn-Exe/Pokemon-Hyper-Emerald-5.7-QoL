@ Multi-register key items (4 slots, dpad popup on SELECT) for Hyper Emerald v5.7.
@ Slot 0 = vanilla SaveBlock1->registeredItem (+0x496); slots 1..3 = SaveBlock1 +0x9C2/+0x9C4/+0x9C6
@ (vanilla unused_9C2[6], verified unreferenced in this hack).
.thumb

@ entry jump table: BASE+0 usereg, +2 reg_toggle, +4 is_registered, +6 bike_swap
    b usereg
    b reg_toggle
    b is_registered
    b bike_swap

@ ================= UseRegisteredKeyItemOnField replacement (hooked at 0x081AD520) =================
usereg:
    push {r4, r5, r6, r7, lr}
    ldr r3, lit_inunionroom
    bl call3
    cmp r0, #1
    beq ur_ret0
    ldr r3, lit_inpyramid
    bl call3
    lsls r0, r0, #24
    bne ur_ret0
    ldr r3, lit_inpike
    bl call3
    lsls r0, r0, #24
    bne ur_ret0
    ldr r3, lit_inmultipartner
    bl call3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #1
    beq ur_ret0
    ldr r3, lit_hidemapname
    bl call3
    movs r0, #0
    movs r1, #0
    movs r2, #0
    ldr r3, lit_changebgy
    bl call3
    movs r5, #0                 @ i
    movs r6, #0                 @ count
    movs r7, #0                 @ last valid item
ur_vloop:
    adds r0, r5, #0
    bl slot_ptr
    adds r4, r0, #0
    ldrh r0, [r4]
    cmp r0, #0
    beq ur_vnext
    movs r1, #1
    ldr r3, lit_checkbaghas
    bl call3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #1
    beq ur_vok
    movs r0, #0                 @ item no longer in bag -> unregister
    strh r0, [r4]
    b ur_vnext
ur_vok:
    adds r6, #1
    ldrh r7, [r4]
ur_vnext:
    adds r5, #1
    cmp r5, #4
    blo ur_vloop
    cmp r6, #0
    bne ur_have
    ldr r0, lit_noregscript     @ "an item can be registered to SELECT" message
    ldr r3, lit_setupscript
    bl call3
    b ur_ret1
ur_have:
    ldr r3, lit_lockcontrols
    bl call3
    ldr r3, lit_freezeobjs
    bl call3
    ldr r3, lit_playerfreeze
    bl call3
    ldr r3, lit_stopavatar
    bl call3
    cmp r6, #1
    bne ur_popup
    adds r0, r7, #0             @ exactly one registered: use it directly (vanilla behaviour)
    bl use_item
    b ur_ret1
ur_popup:
    movs r0, #5
    ldr r3, lit_playse
    bl call3
    bl draw_popup
    adds r4, r0, #0             @ window id
    ldr r0, lit_popup_task
    movs r1, #1
    ldr r3, lit_createtask
    bl call3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    lsls r1, r0, #2
    adds r1, r1, r0
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r1, r1, r0
    strh r4, [r1, #8]           @ data[0] = window id
ur_ret1:
    movs r0, #1
    pop {r4, r5, r6, r7, pc}
ur_ret0:
    movs r0, #0
    pop {r4, r5, r6, r7, pc}

@ use_item(r0=item): gSpecialVar_ItemId = item; task = CreateTask(ItemId_GetFieldFunc(item), 8); data[3] = 1
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

@ draw_popup() -> r0 = window id. Draws std frame window listing the 4 slots with dpad arrows.
draw_popup:
    push {r4, r5, r6, lr}
    sub sp, #0x14
    ldr r0, lit_template
    ldr r3, lit_addwindow
    bl call3
    lsls r0, r0, #24
    lsrs r4, r0, #24            @ r4 = window id
    ldr r0, lit_drawstdframe
    mov r12, r0
    adds r0, r4, #0
    movs r1, #1
    ldr r2, lit_214
    movs r3, #14
    bl callip                   @ DrawStdFrameWithCustomTileAndPalette(win, TRUE, 0x214, 14)
    ldr r5, lit_strvar4         @ r5 = write pointer (gStringVar4)
    movs r6, #0                 @ slot index
dp_loop:
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
    beq dp_empty
    adds r1, r5, #0
    ldr r3, lit_copyitemname
    bl call3                    @ CopyItemName(item, dst)
    b dp_adv
dp_empty:
    adds r0, r5, #0
    ldr r1, lit_emptytext
    ldr r3, lit_stringcopy
    bl call3                    @ StringCopy(dst, "------")
dp_adv:
    ldrb r0, [r5]
    cmp r0, #0xFF
    beq dp_term
    adds r5, #1
    b dp_adv
dp_term:
    movs r0, #0xFE              @ newline
    strb r0, [r5]
    adds r5, #1
    adds r6, #1
    cmp r6, #4
    blo dp_loop
    subs r5, #1
    movs r0, #0xFF              @ final terminator
    strb r0, [r5]
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
    bl callip                   @ AddTextPrinterParameterized4(win, FONT_NORMAL, 4, 2, 0, 0, colors, 0, str)
    adds r0, r4, #0
    add sp, #0x14
    pop {r4, r5, r6, pc}

@ popup_task(r0=taskId): wait for dpad (pick slot) or B/SELECT (cancel)
popup_task:
    push {r4, r5, r6, r7, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24            @ taskId
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r1, r1, r0
    ldrh r0, [r1, #0xA]         @ data[1]: 0 on the creation frame (SELECT still counts as new) -> arm and wait
    cmp r0, #0
    bne pt_input
    movs r0, #1
    strh r0, [r1, #0xA]
    b pt_ret
pt_input:
    ldr r0, lit_gmain
    ldrh r5, [r0, #0x2e]        @ newKeys
    movs r6, #0xFF              @ selection
    movs r0, #0x40              @ UP
    tst r0, r5
    beq pt_k1
    movs r6, #0
    b pt_act
pt_k1:
    movs r0, #0x10              @ RIGHT
    tst r0, r5
    beq pt_k2
    movs r6, #1
    b pt_act
pt_k2:
    movs r0, #0x80              @ DOWN
    tst r0, r5
    beq pt_k3
    movs r6, #2
    b pt_act
pt_k3:
    movs r0, #0x20              @ LEFT
    tst r0, r5
    beq pt_k4
    movs r6, #3
    b pt_act
pt_k4:
    movs r0, #6                 @ B or SELECT -> cancel
    tst r0, r5
    beq pt_ret
    movs r7, #0
    b pt_close
pt_act:
    adds r0, r6, #0
    bl slot_ptr
    ldrh r7, [r0]               @ chosen item
    cmp r7, #0
    beq pt_ret                  @ empty slot: ignore keypress
pt_close:
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r1, r1, r0
    ldrh r5, [r1, #8]           @ window id
    adds r0, r5, #0
    movs r1, #1
    ldr r3, lit_clearstdwin
    bl call3                    @ ClearStdWindowAndFrameToTransparent(win, TRUE)
    adds r0, r5, #0
    ldr r3, lit_removewindow
    bl call3
    adds r0, r4, #0
    ldr r3, lit_destroytask
    bl call3
    cmp r7, #0
    beq pt_cancel
    adds r0, r7, #0
    bl use_item
    b pt_ret
pt_cancel:
    ldr r3, lit_unfreeze
    bl call3                    @ ScriptUnfreezeObjectEvents
    ldr r3, lit_unlock
    bl call3                    @ UnlockPlayerFieldControls
pt_ret:
    pop {r4, r5, r6, r7, pc}

@ ================= bag-side helpers =================
@ slot_ptr(r0=i) -> r0 = &slot[i] (u16). clobbers r1 only.
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
    adds r0, r0, r1             @ SB1 + 0x9C0 + 2*i
    bx lr

@ is_registered(r0=item) -> r0 = 1/0. preserves r2, r3, r4-r7.
is_registered:
    push {r2, r3, r4, r5, lr}
    adds r4, r0, #0
    cmp r4, #0
    beq ir_no
    movs r5, #0
ir_loop:
    adds r0, r5, #0
    bl slot_ptr
    ldrh r0, [r0]
    cmp r0, r4
    beq ir_yes
    adds r5, #1
    cmp r5, #4
    blo ir_loop
ir_no:
    movs r0, #0
    pop {r2, r3, r4, r5, pc}
ir_yes:
    movs r0, #1
    pop {r2, r3, r4, r5, pc}

@ reg_toggle(): item = gSpecialVar_ItemId; if registered -> clear that slot, else -> first empty slot (or slot 3 if full)
reg_toggle:
    push {r4, r5, r6, lr}
    ldr r0, lit_itemid
    ldrh r4, [r0]
    movs r5, #0
    movs r6, #0xFF
rt_loop:
    adds r0, r5, #0
    bl slot_ptr
    ldrh r1, [r0]
    cmp r1, r4
    beq rt_clear
    cmp r1, #0
    bne rt_next
    cmp r6, #0xFF
    bne rt_next
    adds r6, r5, #0
rt_next:
    adds r5, #1
    cmp r5, #4
    blo rt_loop
    cmp r6, #0xFF
    bne rt_set
    movs r6, #3
rt_set:
    adds r0, r6, #0
    bl slot_ptr
    strh r4, [r0]
    pop {r4, r5, r6, pc}
rt_clear:
    movs r1, #0
    strh r1, [r0]
    pop {r4, r5, r6, pc}

@ bike_swap(): replacement for hack fn 0x080D6EDC - swap Mach(0x103)<->Acro(0x110) in every slot
bike_swap:
    push {r4, r5, lr}
    movs r5, #0
bs_loop:
    adds r0, r5, #0
    bl slot_ptr
    ldrh r1, [r0]
    ldr r2, lit_103
    cmp r1, r2
    bne bs_1
    adds r2, #0xD
    strh r2, [r0]
    b bs_next
bs_1:
    adds r3, r2, #0
    adds r3, #0xD
    cmp r1, r3
    bne bs_next
    strh r2, [r0]
bs_next:
    adds r5, #1
    cmp r5, #4
    blo bs_loop
    pop {r4, r5, pc}

call3:
    bx r3
callip:
    bx r12

.align 2
lit_template:       .word TEMPLATE_ADDR
lit_arrows:         .word ARROWS_ADDR
lit_colors:         .word COLORS_ADDR
lit_emptytext:      .word EMPTY_ADDR
lit_popup_task:     .word popup_task + 1
lit_sb1ptr:         .word 0x03005D8C
lit_496:            .word 0x496
lit_9c0:            .word 0x9C0
lit_itemid:         .word 0x0203CE7C
lit_103:            .word 0x103
lit_gtasks:         .word 0x03005E00
lit_gmain:          .word 0x030022C0
lit_strvar4:        .word 0x02021FC4
lit_214:            .word 0x214
lit_inunionroom:    .word 0x08018005
lit_inpyramid:      .word 0x081A9E41
lit_inpike:         .word 0x081A80A9
lit_inmultipartner: .word 0x0813994D
lit_hidemapname:    .word 0x080D4975
lit_changebgy:      .word 0x08001FB9
lit_checkbaghas:    .word 0x080D6725
lit_noregscript:    .word 0x082736B3
lit_setupscript:    .word 0x08098EF9
lit_lockcontrols:   .word 0x08098E55
lit_freezeobjs:     .word 0x08097495
lit_playerfreeze:   .word 0x0808B865
lit_stopavatar:     .word 0x0808BCF5
lit_getfieldfunc:   .word 0x080D75D9
lit_createtask:     .word 0x080A8FB1
lit_playse:         .word 0x080A37A5
lit_addwindow:      .word 0x08003381
lit_drawstdframe:   .word 0x08197E81
lit_copyitemname:   .word 0x080D6645
lit_stringcopy:     .word 0x08008BA1
lit_addtextprinter4: .word 0x08199EED
lit_clearstdwin:    .word 0x08198071
lit_removewindow:   .word 0x08003575
lit_destroytask:    .word 0x080A909D
lit_unfreeze:       .word 0x080984F5
lit_unlock:         .word 0x08098E61
