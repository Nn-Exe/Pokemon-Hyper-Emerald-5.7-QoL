@ Oval Charm (Hyper Emerald v5.7): the Day Care's egg roll, with the charm's odds.
@ TryProduceOrHatchEgg (vanilla) does, once every 256 steps with two compatible Pokemon in the Day Care:
@     if (GetDaycareCompatibilityScore(daycare) > Random() * 100 / 0xFFFF) TriggerPendingDaycareEgg();
@ The patch turns that spot into one call to egg_roll and a branch on its answer. egg_roll makes the same
@ roll, but with the Oval Charm in the Bag the score goes 20 -> 40, 50 -> 80, 70 -> 88 (the main games'
@ numbers). A score of 0 - two Pokemon that cannot breed - stays 0.
.thumb

@ egg_roll(r0 = daycare) -> r0 = 1 when an Egg should appear now
egg_roll:
    push {r4, lr}
    ldr r3, lit_compat
    bl callr3                   @ GetDaycareCompatibilityScore: 0 / 20 / 50 / 70
    lsls r4, r0, #24
    lsrs r4, r4, #24
    cmp r4, #0
    beq er_roll
    ldr r0, lit_oval
    movs r1, #1
    ldr r3, lit_hasitem         @ CheckBagHasItem(Oval Charm, 1)
    bl callr3
    lsls r0, r0, #24
    beq er_roll
    movs r0, #40
    cmp r4, #20
    beq er_set
    movs r0, #80
    cmp r4, #50
    beq er_set
    movs r0, #88
er_set:
    adds r4, r0, #0
er_roll:
    ldr r3, lit_random
    bl callr3
    lsls r0, r0, #16
    lsrs r0, r0, #16
    movs r1, #100
    muls r0, r1
    ldr r1, lit_ffff
    ldr r3, lit_udiv
    bl callr3
    movs r1, #0
    cmp r4, r0
    bls er_ret
    movs r1, #1
er_ret:
    adds r0, r1, #0
    pop {r4}
    pop {r1}
    bx r1

callr3:
    bx r3

.align 2
lit_compat:     .word 0x08070D4D    @ GetDaycareCompatibilityScore
lit_hasitem:    .word 0x080D6725    @ CheckBagHasItem
lit_random:     .word 0x0806F5CD    @ Random
lit_udiv:       .word 0x082E7B69    @ __udivsi3, as the vanilla roll calls it
lit_ffff:       .word 0x0000FFFF
lit_oval:       .word OVAL_CHARM
