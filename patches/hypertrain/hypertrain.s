@ Hyper Training shows up (Hyper Emerald v5.7).
@
@ The Champion Island hyper trainer marks a stat as trained by setting a bit in the spare byte mon+0x1E:
@ bit 1 HP, 2 Atk, 3 Def, 4 Spe, 5 SpA, 6 SpD (the IV fields 0x27..0x2C in order, so bit = field - 0x26).
@ The hack's CalculateMonStats already treats a trained stat as IV 31, but the real IV is left alone - as in
@ the official games, so breeding and Hidden Power keep the original. What was missing:
@   * anything that PRINTS IVs read the raw value, so a trained stat still showed its old IV;
@   * the stats only changed on the next recalculation (a PC withdraw), not after the training.
@
@ ht_getmondata replaces GetMonData for two readers only - the EV-IV Display screen and the IV judges'
@ helper - and returns 31 for a trained IV field; every other field passes straight through. It also keeps
@ each real IV's low bit in SCRATCH, because the EV-IV screen works out the Hidden Power type from the IVs
@ it loaded: ht_hptype, reached from a trampoline in that calculation (0x0968A07A), hands it the real bits,
@ so the type shown stays the one the Pokemon really has.
@ ht_recalc is a callasm for the trainer's script: CalculateMonStats(&gPlayerParty[VAR_0x8004]).
.thumb

@ ht_hptype: from the trampoline at 0x0968A07A - r3 = the real IVs' low bits (HP bit 0 .. SpD bit 5), then
@ back to 0x0968A0B2, where the screen goes on to turn them into a type. r1/r2 are dead there.
ht_hptype:
    ldr r3, lit_scratch
    ldrb r3, [r3]
    movs r2, #0x3F              @ six bits only: EWRAM is not zeroed, bits 6-7 hold whatever was there
    ands r3, r2
    ldr r2, lit_hpret
    bx r2

@ ht_getmondata(r0 = mon, r1 = field, r2 = data) -> GetMonData, but a hyper-trained IV reads 31
ht_getmondata:
    push {r4, r5, r6, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    ldr r3, lit_getmondata
    bl call3
    adds r1, r5, #0
    subs r1, #0x27              @ the six IV fields: k = 0 HP .. 5 SpD
    cmp r1, #5
    bhi gm_ret
    ldr r6, lit_scratch         @ keep the real IV's low bit as bit k, for the Hidden Power type
    ldrb r2, [r6]
    movs r3, #1
    lsls r3, r1
    bics r2, r3
    movs r5, #1
    ands r5, r0
    lsls r5, r1
    orrs r2, r5
    strb r2, [r6]
    ldrb r2, [r4, #0x1E]        @ the training bits: bit k + 1
    adds r1, #1
    lsrs r2, r1
    movs r3, #1
    tst r2, r3
    beq gm_ret
    movs r0, #31
gm_ret:
    pop {r4, r5, r6}
    pop {r1}
    bx r1

@ ht_recalc(): callasm - the trained stats take effect at once
ht_recalc:
    push {lr}
    ldr r0, lit_var8004
    ldrh r0, [r0]
    movs r1, #100
    muls r0, r1
    ldr r1, lit_party
    adds r0, r0, r1
    ldr r3, lit_calcstats
    bl call3
    pop {r0}
    bx r0

call3:
    bx r3

.align 2
lit_getmondata:     .word 0x0806A519    @ GetMonData
lit_calcstats:      .word 0x08068D0D    @ CalculateMonStats (the hack's: honours the training bits)
lit_var8004:        .word 0x020375E0    @ gSpecialVar_0x8004
lit_party:          .word 0x020244EC    @ gPlayerParty
lit_scratch:        .word 0x0203D600    @ 1 byte, EWRAM measured free (hyper-emerald-patch skill)
lit_hpret:          .word 0x0968A0B3    @ the EV-IV screen, just after its parity bits
