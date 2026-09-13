@ PC item storage sort (Hyper Emerald v5.7). START in the Withdraw/Toss item list sorts the 50 PC item slots
@ (gSaveBlock1->pcItems @ +0x498, plain {u16 id, u16 qty}), cycling type -> name -> amount like the bag sort.
@ Entered from ItemStorage_ProcessInput @0x0816C30C: the pool literal (0x16C354, was &gMain) now holds hook|1
@ and the `ldrh r1,[r0,#0x2E]` @0x0816C31E became `bx r0`. Entry state: r4 = &gTasks[taskId], r5 = taskId.
@ Pass-through re-executes the ldrh with r0 = &gMain and resumes at 0x0816C320.
.thumb
hook:
    ldr r0, lit_gmain
    ldrh r1, [r0, #0x2E]        @ gMain.newKeys
    movs r2, #8                 @ START_BUTTON
    ands r2, r1
    beq pass
    adds r0, r5, #0
    bl pc_sort
    ldr r0, lit_epilogue        @ ProcessInput epilogue: pop {r4,r5,r6}; pop {r0}; bx r0
    bx r0
pass:
    ldr r2, lit_resume
    bx r2

@ pc_sort(taskId): sort pcItems, rebuild the list names, re-init the list via FinishItemSwap(taskId, TRUE)
pc_sort:
    push {r4, r5, r6, r7, lr}
    mov r4, r8
    push {r4}
    adds r4, r0, #0             @ taskId
    ldr r0, lit_pageinfo
    ldrb r7, [r0, #5]           @ gPlayerPCItemPageInfo.count (items + Cancel)
    subs r7, #1                 @ N = item count
    cmp r7, #2
    blo ps_done
    ldr r0, lit_sb1ptr
    ldr r5, [r0]
    ldr r0, lit_pcitems_off
    adds r5, r5, r0             @ r5 = pcItems
    movs r0, #1                 @ already sorted by name? -> amount
    bl is_sorted
    cmp r0, #0
    bne ps_mode2
    movs r0, #0                 @ already sorted by type? -> name
    bl is_sorted
    cmp r0, #0
    bne ps_mode1
    movs r0, #0
    b ps_set
ps_mode2:
    movs r0, #2
    b ps_set
ps_mode1:
    movs r0, #1
ps_set:
    mov r8, r0
    bl insertion_sort
    ldr r0, lit_storage
    ldr r0, [r0]
    ldr r1, lit_swapidx_off
    movs r2, #0xFF
    strb r2, [r0, r1]           @ sItemStorageMenu->swapIdx = none (keeps the cursor where it is)
    ldr r3, lit_rebuild
    bl call3                    @ rebuild list item names from pcItems
    adds r0, r4, #0
    movs r1, #1
    ldr r3, lit_finishswap
    bl call3                    @ FinishItemSwap(taskId, wasCanceled=TRUE): PlaySE, destroy + re-init list
ps_done:
    pop {r4}
    mov r8, r4
    pop {r4, r5, r6, r7, pc}

call3:
    bx r3

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
    subs r6, r4, #1
ins_inner:
    cmp r6, #0
    blt ins_place
    lsls r0, r6, #2
    adds r0, r0, r5
    mov r1, sp
    bl cmp_gt
    cmp r0, #0
    beq ins_place
    lsls r0, r6, #2
    adds r0, r0, r5
    ldr r1, [r0]
    str r1, [r0, #4]
    subs r6, #1
    b ins_inner
ins_place:
    adds r6, #1
    lsls r0, r6, #2
    adds r0, r0, r5
    ldr r1, [sp]
    str r1, [r0]
    adds r4, #1
    b ins_outer
ins_done:
    add sp, #4
    pop {r4, r5, r6, pc}

@ cmp_gt(&a r0, &b r1), mode r8 -> r0=1 if a must come after b
cmp_gt:
    push {r4, r5, lr}
    mov r4, r8
    cmp r4, #0
    beq by_id
    cmp r4, #1
    beq by_name
    ldrh r2, [r0, #2]           @ by amount (descending); PC quantities are not encrypted
    ldrh r3, [r1, #2]
    cmp r2, r3
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
    adds r0, r0, r2
    muls r1, r3, r1
    adds r1, r1, r2
name_loop:
    ldrb r4, [r0]
    ldrb r5, [r1]
    cmp r4, #0xD5               @ fold a-z onto A-Z
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
    cmp r4, #0xFF
    beq ret0
    adds r0, #1
    adds r1, #1
    b name_loop
ret1:
    movs r0, #1
    pop {r4, r5, pc}
ret0:
    movs r0, #0
    pop {r4, r5, pc}

.align 2
lit_gmain:       .word 0x030022C0
lit_epilogue:    .word 0x0816C39F
lit_resume:      .word 0x0816C321
lit_pageinfo:    .word 0x0203BCB8
lit_sb1ptr:      .word 0x03005D8C
lit_pcitems_off: .word 0x498
lit_storage:     .word 0x0203BCC4
lit_swapidx_off: .word 0x666
lit_rebuild:     .word 0x0816BD05
lit_finishswap:  .word 0x0816C5A1
lit_itemtab:     .word 0x08FC2C7C
