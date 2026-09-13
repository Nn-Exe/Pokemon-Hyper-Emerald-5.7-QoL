@ In-party move relearner (Hyper Emerald v5.7).
@ Adds a "Moves" option to the party menu's field action list (new entry 33 in a relocated copy of the
@ 33-entry sCursorOptions table). Choosing it closes the party menu and opens the game's own Move Relearner
@ screen (CB2_InitLearnMove 0x081606A1, party slot in gSpecialVar_0x8004) - the same screen the Fallarbor
@ tutor uses, including the hack's replacement move-list builder. No Heart Scale is consumed.
@ builder_hook is entered via `ldr r3,[pc]; bx r3` planted at 0x081B3518 (the CANCEL append in
@ SetPartyMonFieldSelectionActions); it appends MOVES (if there is room in actions[8]) then CANCEL and
@ returns to the function epilogue at 0x081B3528.
.thumb
builder_hook:
    ldr r0, lit_internal
    ldr r1, [r0]
    ldrb r2, [r1, #0x17]        @ numActions
    cmp r2, #7
    bhs bh_cancel               @ 4 field moves + summary/switch/item: no room for one more before CANCEL
    adds r0, r1, #0
    adds r0, #0xF               @ actions[]
    adds r1, #0x17              @ &numActions
    movs r2, #33                @ MENU_MOVES (new table entry)
    ldr r3, lit_append
    bl call3
bh_cancel:
    ldr r0, lit_internal
    ldr r1, [r0]
    adds r0, r1, #0
    adds r0, #0xF
    adds r1, #0x17
    movs r2, #2                 @ MENU_CANCEL1
    ldr r3, lit_append
    bl call3
    ldr r3, lit_return
    bx r3

cursor_moves:                   @ (u8 taskId) - mirrors CursorCb_Summary 0x081B37FC
    push {r4, lr}
    lsls r4, r0, #24
    lsrs r4, r4, #24
    movs r0, #5
    ldr r3, lit_playse
    bl call3                    @ PlaySE(SE_SELECT)
    ldr r0, lit_internal
    ldr r1, [r0]
    ldr r0, lit_cb2_moves
    str r0, [r1, #4]            @ sPartyMenuInternal->exitCallback = cb2_moves
    adds r0, r4, #0
    ldr r3, lit_close
    bl call3                    @ Task_ClosePartyMenu(taskId)
    pop {r4}
    pop {r0}
    bx r0

cb2_moves:                      @ main callback after the party menu has faded out
    ldr r0, lit_party
    ldrb r0, [r0, #9]           @ gPartyMenu.slotId
    ldr r1, lit_var8004
    strh r0, [r1]               @ gSpecialVar_0x8004 = slot
    ldr r0, lit_cb2_learn
    bx r0                       @ CB2_InitLearnMove (returns to the field on exit)

call3:
    bx r3

.align 2
lit_internal:   .word 0x0203CEC4
lit_append:     .word 0x080A0945
lit_return:     .word 0x081B3529
lit_playse:     .word 0x080A37A5
lit_cb2_moves:  .word CB2_MOVES_ADDR
lit_close:      .word 0x081B12C1
lit_party:      .word 0x0203CEC8
lit_var8004:    .word 0x020375E0
lit_cb2_learn:  .word 0x081606A1
