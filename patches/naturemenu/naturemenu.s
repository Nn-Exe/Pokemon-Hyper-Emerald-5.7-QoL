@ In-party nature changer (Hyper Emerald v5.7).
@ Adds a "Nature" option to the party menu next to "Moves". Choosing it stores the party slot in VAR_0x8004,
@ drops a token in VAR_0x8006 and closes the menu. The next time the player has field control the chained
@ field-input hook consumes the token and runs a script that shows the game's own nature list (multichoice 0x7C)
@ and calls the hack's nature routine (0x08FF0E01) - the same one the Mint NPC in the Trainer's School uses.
@ That routine writes the nature into the unused byte at mon+0x1F (bit 7 preserved) and recalculates the stats.
.thumb

@ --- party menu: field-action builder, entered via the trampoline at 0x081B3518 -------------------------------
builder_hook:
    ldr r0, lit_internal
    ldr r1, [r0]
    ldrb r2, [r1, #0x17]        @ numActions
    cmp r2, #7
    bhs bh_cancel               @ actions[] holds 8; leave room for CANCEL
    adds r0, r1, #0
    adds r0, #0xF
    adds r1, #0x17
    movs r2, #33                @ MENU_MOVES (relearner entry)
    ldr r3, lit_append
    bl call3
    ldr r0, lit_internal
    ldr r1, [r0]
    ldrb r2, [r1, #0x17]
    cmp r2, #7
    bhs bh_cancel
    adds r0, r1, #0
    adds r0, #0xF
    adds r1, #0x17
    movs r2, #34                @ MENU_NATURE (new entry)
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

@ --- party menu: "Nature" chosen (u8 taskId) ------------------------------------------------------------------
cursor_nature:
    push {r4, lr}
    lsls r4, r0, #24
    lsrs r4, r4, #24
    movs r0, #5
    ldr r3, lit_playse
    bl call3                    @ PlaySE(SE_SELECT)
    ldr r0, lit_party
    ldrb r0, [r0, #9]           @ gPartyMenu.slotId
    ldr r1, lit_var8004
    strh r0, [r1]               @ VAR_0x8004 = slot (the nature routine reads its low byte)
    ldr r3, lit_token
    strh r3, [r1, #4]           @ VAR_0x8006 = pending token, picked up by the field hook
    adds r0, r4, #0
    ldr r3, lit_close
    bl call3                    @ Task_ClosePartyMenu
    pop {r4}
    pop {r0}
    bx r0

@ --- field input hook: run the nature script once, then chain on ----------------------------------------------
@ Entered via `ldr r3,[pc]; bx r3` at 0x0809C014 with r0 = input struct, lr = caller. Must preserve r0.
field_hook:
    push {r0, lr}
    ldr r1, lit_var8004
    ldrh r2, [r1, #4]           @ VAR_0x8006
    ldr r3, lit_token
    cmp r2, r3
    bne fh_pass
    movs r2, #0
    strh r2, [r1, #4]           @ consume the token
    ldr r0, lit_script
    ldr r3, lit_setupscript
    bl call3                    @ ScriptContext1_SetupScript(nature_script)
    pop {r0}
    pop {r1}
    movs r0, #1                 @ handled -> caller locks controls and runs the script
    bx r1
fh_pass:
    pop {r0}
    pop {r1}
    mov lr, r1
    ldr r1, lit_next_hook       @ L-repel hook (expects entry state)
    bx r1

@ --- callnative target: validate the multichoice result and apply it ------------------------------------------
apply_nature:
    push {lr}
    ldr r0, lit_specials
    ldrh r1, [r0, #24]          @ where this engine's multichoice leaves the choice (0xFF while open)
    cmp r1, #24
    bls ap_ok
    ldrh r1, [r0, #26]          @ fall back to VAR_RESULT's usual slot
    cmp r1, #24
    bhi ap_skip                 @ 0x7F = B pressed, 0xFF = nothing chosen
ap_ok:
    strh r1, [r0, #10]          @ VAR_0x8005 = nature
    ldr r3, lit_native
    bl call3                    @ hack routine: mon[VAR_0x8004].nature = VAR_0x8005, recalculate stats
ap_skip:
    pop {r0}
    bx r0

call3:
    bx r3

.align 2
lit_internal:     .word 0x0203CEC4
lit_append:       .word 0x080A0945
lit_return:       .word 0x081B3529
lit_playse:       .word 0x080A37A5
lit_party:        .word 0x0203CEC8
lit_var8004:      .word 0x020375E0
lit_token:        .word 0x00004E01
lit_close:        .word 0x081B12C1
lit_script:       .word SCRIPT_ADDR
lit_setupscript:  .word 0x08098EF9
lit_next_hook:    .word NEXT_HOOK
lit_specials:     .word 0x020375D8
lit_native:       .word 0x08FF0E01
