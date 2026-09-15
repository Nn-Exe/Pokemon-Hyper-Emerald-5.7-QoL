@ PC anywhere (Hyper Emerald v5.7): hold B and press SELECT in the overworld to open the PC menu.
@ Chained in front of the field-input hooks at ProcessPlayerFieldInput (trampoline literal 0x0809C018).
@ Entered with r0 = input struct, lr = caller; must preserve r0 when passing through.
.thumb
pc_hook:
    push {r0, lr}
    ldr r1, lit_gmain
    ldrh r2, [r1, #0x2E]        @ gMain.newKeys
    movs r3, #4                 @ SELECT_BUTTON
    tst r2, r3
    beq ph_pass
    ldrh r2, [r1, #0x2C]        @ gMain.heldKeys
    movs r3, #2                 @ B_BUTTON
    tst r2, r3
    beq ph_pass
    ldr r0, lit_script
    ldr r3, lit_setupscript
    bl call3                    @ ScriptContext1_SetupScript(pc_script)
    pop {r0}
    pop {r1}
    movs r0, #1                 @ handled -> caller locks controls and runs the script
    bx r1
ph_pass:
    pop {r0}
    pop {r1}
    mov lr, r1
    ldr r1, lit_next_hook
    bx r1

call3:
    bx r3

.align 2
lit_gmain:        .word 0x030022C0
lit_script:       .word SCRIPT_ADDR
lit_setupscript:  .word 0x08098EF9
lit_next_hook:    .word NEXT_HOOK
