@ Both bikes at once (Hyper Emerald v5.7).
@ The game gives you one bike and Rydel swaps it. Once you own either bike, this hands you the other one,
@ so both sit in the Key Items pocket: using (or registering) one switches straight to that bike, because
@ both items share the same field-use routine and differ only by their secondary id (Mach 0, Acro 1).
@
@ Hooked into CB2_Overworld, so it takes effect on an existing save as soon as you are back on the map.
@ It grants nothing before you own a bike, and does nothing at all once you own both.
.thumb

hook:
    push {r4, lr}
    bl grant
    ldr r0, lit_palfade         @ the four instructions the trampoline replaced
    ldrb r0, [r0, #7]
    lsrs r0, r0, #7
    ldr r3, lit_back
    bx r3

grant:
    push {r4, r5, lr}
    ldr r0, lit_mach
    movs r1, #1
    ldr r3, lit_hasitem
    bl call3
    adds r4, r0, #0             @ owns the Mach Bike?
    ldr r0, lit_acro
    movs r1, #1
    ldr r3, lit_hasitem
    bl call3
    adds r5, r0, #0             @ owns the Acro Bike?
    cmp r4, #0
    beq g_no_mach
    cmp r5, #0
    bne g_ret                   @ owns both: nothing to do
    ldr r0, lit_acro            @ has Mach only -> give Acro
    b g_add
g_no_mach:
    cmp r5, #0
    beq g_ret                   @ owns neither: too early in the game, leave it alone
    ldr r0, lit_mach            @ has Acro only -> give Mach
g_add:
    movs r1, #1
    ldr r3, lit_additem
    bl call3
g_ret:
    pop {r4, r5, pc}

call3:
    bx r3

.align 2
lit_palfade: .word 0x02037FD4    @ gPaletteFade
lit_back:    .word 0x08085E65    @ CB2_Overworld + 8 (after the four replayed instructions)
lit_hasitem: .word 0x080D6725    @ CheckBagHasItem(itemId, count)
lit_additem: .word 0x080D6929    @ AddBagItem(itemId, count)
lit_mach:    .word 0x00000103     @ Mach Bike = 259
lit_acro:    .word 0x00000110     @ Acro Bike = 272
