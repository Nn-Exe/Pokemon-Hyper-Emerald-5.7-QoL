@ L button = quick repel (Hyper Emerald v5.7). Chained in front of the auto-run hook at ProcessPlayerFieldInput.
@ Entered via `ldr r3,[pc]; bx r3` at 0x0809C014 with r0 = input struct, lr = caller. Must preserve r0 on pass-through.
@ L pressed + no repel active + a repel in the bag (Max 84 > Super 83 > Repel 86): set gSpecialVar_ItemId,
@ run SCRIPT (ask yes/no -> hack's own use-repel routine 0x083D7781), return 1 (caller locks controls).
.thumb
l_hook:
    push {r0, r4, r5, lr}
    ldr r1, lit_gmain
    ldrh r1, [r1, #0x2E]        @ newKeys
    movs r2, #2
    lsls r2, r2, #8             @ L_BUTTON 0x200
    tst r1, r2
    beq lh_pass
    ldr r0, lit_repelvar
    ldr r3, lit_varget
    bl call3                    @ VarGet(0x4021)
    lsls r0, r0, #24
    bne lh_pass                 @ repel already active (low byte = steps)
    ldr r5, lit_repels          @ 84, 83, 86, 0
lh_next:
    ldrh r4, [r5]
    cmp r4, #0
    beq lh_pass
    adds r0, r4, #0
    movs r1, #1
    ldr r3, lit_checkbaghas
    bl call3
    lsls r0, r0, #24
    bne lh_found
    adds r5, #2
    b lh_next
lh_found:
    ldr r1, lit_itemid
    strh r4, [r1]               @ gSpecialVar_ItemId = chosen repel
    adds r0, r4, #0
    ldr r1, lit_strvar1
    ldr r3, lit_copyitemname
    bl call3                    @ CopyItemName(item, gStringVar1)
    ldr r0, lit_script
    ldr r3, lit_setupscript
    bl call3                    @ ScriptContext_SetupScript(script)
    pop {r0, r4, r5}
    pop {r1}
    movs r0, #1                 @ handled -> caller locks controls and runs the script
    bx r1
lh_pass:
    pop {r0, r4, r5}
    pop {r1}
    mov lr, r1
    ldr r1, lit_next_hook       @ auto-run toggle hook (expects entry state)
    bx r1

call3:
    bx r3

.align 2
lit_gmain:        .word 0x030022C0
lit_repelvar:     .word 0x4021
lit_varget:       .word 0x0809D695
lit_repels:       .word REPELS_ADDR
lit_checkbaghas:  .word 0x080D6725
lit_itemid:       .word 0x0203CE7C
lit_strvar1:      .word 0x02021CC4
lit_copyitemname: .word 0x080D6645
lit_script:       .word SCRIPT_ADDR
lit_setupscript:  .word 0x08098EF9
lit_next_hook:    .word NEXT_HOOK
