@ Bag sort for Hyper Emerald v5.7 (Emerald BPEE base). THUMB, assembled at BASE.
@ Entered from Task_BagMenu_HandleInput @0x081ABD84 via hijacked literal pool + bx r0.
@ Register state at entry (from handler): r5=&gBagPosition r6=&taskData r7=&pos r8=&pos2 r9=taskId, sp has 4-byte local.
.thumb
hook:
    ldr r0, lit_gmain
    ldrh r1, [r0, #0x2e]        @ gMain.newKeys
    movs r0, #8                 @ START_BUTTON
    ands r0, r1
    beq orig_path
    ldr r3, lit_canswap         @ same gate as Move item: field/battle bag, pocket != TM/Berry
    bl call3
    cmp r0, #0
    bne do_sort
orig_path:                      @ re-execute the instructions the hook replaced
    ldr r0, lit_gmain
    ldrh r1, [r0, #0x2e]
    movs r0, #4                 @ SELECT_BUTTON
    ands r0, r1
    lsls r0, r0, #16
    lsrs r0, r0, #16
    mov r10, r0
    cmp r0, #0
    beq to_e10
    ldr r2, lit_ret_d97
    bx r2
to_e10:
    ldr r2, lit_ret_e11
    bx r2

do_sort:
    ldr r4, lit_bagpos
    ldrb r0, [r4, #5]           @ gBagPosition.pocket
    lsls r0, r0, #3
    ldr r1, lit_bagpockets
    adds r4, r0, r1             @ r4 = &gBagPockets[pocket]
    ldr r5, [r4]                @ r5 = itemSlots
    ldrb r6, [r4, #4]           @ capacity
    movs r7, #0                 @ r7 = N = leading non-empty slots
count_loop:
    cmp r7, r6
    bhs count_done
    lsls r0, r7, #2
    ldrh r0, [r5, r0]
    cmp r0, #0
    beq count_done
    adds r7, #1
    b count_loop
count_done:
    movs r0, #1                 @ already sorted by name? -> next mode amount
    bl is_sorted
    cmp r0, #0
    bne mode2
    movs r0, #0                 @ already sorted by type(id)? -> next mode name
    bl is_sorted
    cmp r0, #0
    bne mode1
    movs r0, #0                 @ otherwise (unsorted / amount-sorted) -> type
    b setmode
mode2:
    movs r0, #2
    b setmode
mode1:
    movs r0, #1
setmode:
    mov r8, r0
    bl insertion_sort
    mov r2, r9                  @ gTasks[taskId].data[1] = 0x7F00 so CancelItemSwap keeps cursor
    lsls r3, r2, #2
    adds r3, r3, r2
    lsls r3, r3, #3
    ldr r1, lit_taskdata
    adds r1, r1, r3
    movs r0, #0x7F
    lsls r0, r0, #8
    strh r0, [r1, #2]
    mov r0, r9
    ldr r3, lit_cancelswap      @ rebuilds list from pocket data, restores handler
    bl call3
    movs r0, #5                 @ PlaySE(SE_SELECT)
    ldr r3, lit_playse
    bl call3
    movs r0, #1                 @ FillWindowPixelBuffer(WIN_DESCRIPTION, 0)
    movs r1, #0
    ldr r3, lit_fillwin
    bl call3
    sub sp, #0x14               @ BagMenu_Print(1, 1, str, 3, 1, 0, 0, 0, 0)
    movs r0, #1
    str r0, [sp]
    movs r1, #0
    str r1, [sp, #4]
    str r1, [sp, #8]
    str r1, [sp, #12]
    str r1, [sp, #16]
    mov r2, r8
    lsls r2, r2, #2
    ldr r3, lit_strtab
    ldr r2, [r3, r2]
    movs r0, #1
    movs r1, #1
    movs r3, #3
    ldr r4, lit_print
    bl call4
    add sp, #0x14
    ldr r0, lit_exit            @ handler epilogue
    bx r0

call3:
    bx r3
call4:
    bx r4

@ is_sorted(mode r0): r5=slots r7=N. sets r8=mode. returns r0=1 if no adjacent pair out of order
is_sorted:
    push {r4, lr}
    mov r8, r0
    movs r4, #0
is_loop:
    adds r0, r4, #1
    cmp r0, r7
    bhs is_yes
    lsls r0, r4, #2
    adds r0, r0, r5
    adds r1, r0, #4
    bl cmp_gt
    cmp r0, #0
    bne is_no
    adds r4, #1
    b is_loop
is_yes:
    movs r0, #1
    pop {r4, pc}
is_no:
    movs r0, #0
    pop {r4, pc}

@ insertion_sort: r5=slots r7=N r8=mode. stable.
insertion_sort:
    push {r4, r5, r6, lr}
    sub sp, #4
    movs r4, #1
ins_outer:
    cmp r4, r7
    bhs ins_done
    lsls r0, r4, #2
    adds r0, r0, r5
    ldr r0, [r0]
    str r0, [sp]                @ key = slots[i]
    subs r6, r4, #1             @ j = i-1
ins_inner:
    cmp r6, #0
    blt ins_place
    lsls r0, r6, #2
    adds r0, r0, r5             @ &slots[j]
    mov r1, sp                  @ &key
    bl cmp_gt
    cmp r0, #0
    beq ins_place
    lsls r0, r6, #2
    adds r0, r0, r5
    ldr r1, [r0]
    str r1, [r0, #4]            @ slots[j+1] = slots[j]
    subs r6, #1
    b ins_inner
ins_place:
    adds r6, #1
    lsls r0, r6, #2
    adds r0, r0, r5
    ldr r1, [sp]
    str r1, [r0]                @ slots[j+1] = key
    adds r4, #1
    b ins_outer
ins_done:
    add sp, #4
    pop {r4, r5, r6, pc}

@ cmp_gt(&a r0, &b r1), mode r8 -> r0=1 if a must come after b
cmp_gt:
    push {r4, r5, r6, lr}
    mov r4, r8
    cmp r4, #0
    beq by_id
    cmp r4, #1
    beq by_name
    adds r5, r1, #2             @ by amount (descending), via GetBagItemQuantity (decrypts)
    adds r0, r0, #2
    ldr r3, lit_getqty
    bl call3
    adds r6, r0, #0
    adds r0, r5, #0
    ldr r3, lit_getqty
    bl call3
    cmp r6, r0
    blo ret1
    b ret0
by_id:
    ldrh r0, [r0]
    ldrh r1, [r1]
    cmp r0, r1
    bhi ret1
    b ret0
by_name:
    ldrh r0, [r0]
    ldrh r1, [r1]
    ldr r2, lit_itemtab
    movs r3, #44
    muls r0, r3, r0
    adds r0, r0, r2             @ name a
    muls r1, r3, r1
    adds r1, r1, r2             @ name b
name_loop:
    ldrb r4, [r0]
    ldrb r5, [r1]
    cmp r4, #0xD5               @ fold a-z (0xD5..0xEE) onto A-Z (0xBB..0xD4)
    blo f1
    cmp r4, #0xEE
    bhi f1
    subs r4, #0x1A
f1:
    cmp r5, #0xD5
    blo f2
    cmp r5, #0xEE
    bhi f2
    subs r5, #0x1A
f2:
    cmp r4, r5
    bhi ret1
    blo ret0
    cmp r4, #0xFF               @ equal so far; both terminated -> equal
    beq ret0
    adds r0, #1
    adds r1, #1
    b name_loop
ret1:
    movs r0, #1
    pop {r4, r5, r6, pc}
ret0:
    movs r0, #0
    pop {r4, r5, r6, pc}

.align 2
lit_gmain:      .word 0x030022C0
lit_ret_d97:    .word 0x081ABD97
lit_ret_e11:    .word 0x081ABE11
lit_canswap:    .word 0x081AC2C1
lit_bagpos:     .word 0x0203CE58
lit_bagpockets: .word 0x02039DD8
lit_taskdata:   .word 0x03005E08
lit_cancelswap: .word 0x081AC591
lit_playse:     .word 0x080A37A5
lit_fillwin:    .word 0x08003C49
lit_strtab:     .word STRTAB_ADDR
lit_print:      .word 0x081AE0BD
lit_exit:       .word 0x081ABEB3
lit_getqty:     .word 0x080D6555
lit_itemtab:    .word 0x08FC2C7C
