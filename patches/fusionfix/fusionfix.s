@ The Pokemon kept inside a fusion: three ways the slot could say "taken" for good (Hyper Emerald v5.7). Thumb-1.
@
@ A fusion keeps the Pokemon that goes inside whole (100 bytes) in the saved overflow stream:
@   0x0203D5E0  Solgaleo / Lunala inside Necrozma    N-Solarizer, N-Lunarizer   routine 0x09F00F58 (callasm
@   0x0203D644  Glastrier / Spectrier inside Calyrex Unity Reins                trampoline 0x08C60D30)
@   0x0203D800  Reshiram / Zekrom inside Kyurem      DNA Splicers               routine 0x08FD7020
@ Asked to fuse while its slot is taken, each routine answers "Multiple fusions are not allowed!". Three things
@ left a slot taken with no fused Pokemon to split:
@   1. v1.5's Hyper Training used the byte 0x0203D600 - the low byte of the first slot's species - as scratch and
@      rewrote its low six bits on every look at the EV-IV Display or an IV judge. With nothing stored the
@      species then reads 1-63 ("taken"); with Solgaleo (844) or Lunala (845) stored it reads something in
@      832-895, and the split - which wants exactly the partner's species - is refused with the same line.
@   2. NEW GAME (the original game's) does not empty the slots: started over a save with a fusion in it, the new
@      game inherits the stored Pokemon and can never fuse.
@   3. The fused Pokemon is gone (released, or case 2 on a save made before this patch).
@
@ fx_entry  the Necrozma / Calyrex trampoline's word now points here; fx_dna the DNA Splicers script's callasm.
@           Each puts its slot right and goes on to the game's routine with lr as it came.
@ fx_newgame  chained in front of ClearBag (NewGameInitData only): the three slots are emptied.

@ ---- N-Solarizer / N-Lunarizer / Unity Reins ----
fx_entry:
    push {r4, r5, lr}
    bl fx_chosen
    adds r5, r0, #0             @ the chosen Pokemon's species
    ldr r4, fx_slot
    movs r1, #0x54
    ldrb r0, [r4, r1]           @ the stored Pokemon's level
    cmp r0, #0
    bne fe_stored
    strh r0, [r4, #0x20]        @ 1. nothing stored (as a split or a new game leaves it): the species is 0
    b fe_calyrex
fe_stored:
    ldr r2, fx_duskmane
    subs r1, r5, r2             @ 0 Dusk Mane, 1 Dawn Wings
    cmp r1, #1
    bhi fe_fuse
    ldrh r0, [r4, #0x20]        @ 1. a split: 844 / 845 with the low six bits rewritten reads 832..895 -
    lsrs r0, r0, #6             @    it is this form's partner, the only Pokemon the slot ever takes
    cmp r0, #13
    bne fe_go
    ldr r2, fx_solgaleo
    adds r1, r1, r2             @ 844 Solgaleo, 845 Lunala
    strh r1, [r4, #0x20]
    b fe_go
fe_fuse:
    ldr r2, fx_necrozma
    cmp r5, r2
    bne fe_calyrex
    adds r0, r4, #0             @ 3. a fusion is asked for and the slot is taken
    adr r1, fx_forms_necrozma
    bl fx_drop_orphan
    b fe_go
fe_calyrex:
    ldr r2, fx_calyrex
    cmp r5, r2
    bne fe_go
    adds r0, r4, #0
    adds r0, #100               @ Calyrex's slot follows Necrozma's
    adr r1, fx_forms_calyrex
    bl fx_drop_orphan
fe_go:
    pop {r4, r5}
    pop {r3}
    mov lr, r3
    ldr r0, fx_fusion
    bx r0

@ ---- DNA Splicers: the player chooses Reshiram or Zekrom, Kyurem is found in the party ----
fx_dna:
    push {r4, lr}
    bl fx_chosen
    ldr r1, fx_reshiram
    subs r0, r0, r1             @ 0 Reshiram, 1 Zekrom
    cmp r0, #1
    bhi fd_go
    ldr r0, fx_kyurem_slot
    adr r1, fx_forms_kyurem
    bl fx_drop_orphan
fd_go:
    pop {r4}
    pop {r3}
    mov lr, r3
    ldr r0, fx_dna_routine
    bx r0

@ fx_chosen -> r0 = the species of the party Pokemon var 0x8004 names (0 when it names none)
fx_chosen:
    ldr r1, fx_var8004
    ldrh r1, [r1]
    movs r0, #0
    cmp r1, #5
    bhi fc_ret
    movs r2, #100
    muls r1, r2, r1
    ldr r2, fx_party
    adds r1, r1, r2
    ldrh r0, [r1, #0x20]
fc_ret:
    bx lr

@ fx_drop_orphan(r0 = slot, r1 = the forms that hold what is in it, a 0-ended list of words)
@ A Pokemon is stored (level not 0) and the player has none of the forms - the game's own "does the player have
@ this species" (0x09F03738: party, the 14 PC boxes, both Day Care places; it is what decides whether Littleroot
@ hands a lost legend out again) - so nothing can ever be split to give it back: the slot is emptied.
fx_drop_orphan:
    push {r4, r5, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    movs r1, #0x54
    ldrb r0, [r4, r1]
    cmp r0, #0
    beq do_ret
do_next:
    ldr r0, [r5]
    cmp r0, #0
    beq do_drop
    ldr r3, fx_owned
    bl fx_call3
    cmp r0, #0
    bne do_ret                  @ the player has it: the slot is its
    adds r5, #4
    b do_next
do_drop:
    movs r1, #100
do_zero:
    subs r1, #1
    strb r0, [r4, r1]
    bne do_zero
do_ret:
    pop {r4, r5, pc}
fx_call3:
    bx r3

@ ---- NEW GAME: ClearBag's trampoline comes here first ----
fx_newgame:
    ldr r0, fx_slot
    movs r1, #200               @ Necrozma's slot and Calyrex's after it
    movs r2, #0
fn_a:
    subs r1, #1
    strb r2, [r0, r1]
    bne fn_a
    ldr r0, fx_kyurem_slot
    movs r1, #100
fn_b:
    subs r1, #1
    strb r2, [r0, r1]
    bne fn_b
    ldr r0, fx_clearbag
    bx r0
PAD
fx_slot:            .word 0x0203D5E0            @ inside Necrozma; Calyrex's slot is the next 100 bytes
fx_kyurem_slot:     .word 0x0203D800
fx_var8004:         .word 0x020375E0            @ gSpecialVar_0x8004: the party slot the player chose
fx_party:           .word 0x020244EC            @ gPlayerParty
fx_necrozma:        .word 853
fx_duskmane:        .word 1068
fx_solgaleo:        .word 844
fx_calyrex:         .word 1098
fx_reshiram:        .word 696
fx_owned:           .word 0x09F03739            @ r0 = species -> 1 if the player has one
fx_fusion:          .word 0x09F00F59            @ the game's Necrozma / Calyrex routine
fx_dna_routine:     .word 0x08FD7021            @ the game's Kyurem routine
fx_clearbag:        .word CLEARBAG_ADDR         @ what ClearBag's trampoline pointed at
fx_forms_necrozma:  .word 1068                  @ Dusk Mane
fx_fn_dawnwings:    .word 1069
fx_fn_ultra_a:      .word 1070                  @ Ultra Necrozma, from either (in battle only)
fx_fn_ultra_b:      .word 1090
fx_fn_end:          .word 0
fx_forms_calyrex:   .word 1099                  @ Ice Rider
fx_fc_shadow:       .word 1100
fx_fc_end:          .word 0
fx_forms_kyurem:    .word 995                   @ White Kyurem
fx_fk_black:        .word 996
fx_fk_end:          .word 0
