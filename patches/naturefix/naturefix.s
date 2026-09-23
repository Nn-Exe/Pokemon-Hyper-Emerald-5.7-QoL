@ Nature display fix (Hyper Emerald v5.7).
@
@ The hack stores a nature OVERRIDE in the unused byte at mon+0x1F (bits 0-6) and its Mint writes it, but
@ GetNature (0x0806D070) still computes the nature the vanilla way as `personality % 25`. So a Mint - or
@ the party editor - changes the stats (CalculateMonStats does use GetNature) while the summary's
@ "Nature:" line keeps showing the old nature.
@
@ This replaces GetNature with a version that prefers a NON-ZERO override and otherwise falls through to
@ the original `personality % 25`. Zero is left meaning "no override", which is what the Mint's first grid
@ cell ("None") writes, so Pokemon that were never given a nature keep displaying exactly what they did.
@ r0 is the mon pointer at entry (every caller in the ROM passes one), and +0x1F sits inside the
@ BoxPokemon part, so it is valid for a party mon and a boxed one alike.
.thumb
getnature_hook:
    push {lr}
    ldrb r1, [r0, #0x1F]        @ override byte
    movs r2, #0x7F
    ands r1, r2                 @ bits 0-6 only
    cmp r1, #0
    beq gn_base                 @ 0 = no override: behave exactly as before
    cmp r1, #24                 @ the Mint's list (multichoice 0x7C) is None, Lonely .. Careful, Hardy:
    bne gn_ret                  @ its last cell, 24, is Hardy (nature 0) - there is no Quirky. Both are
    movs r1, #0                 @ neutral, so only the name changes.
gn_ret:
    adds r0, r1, #0
    pop {r1}
    bx r1
gn_base:
    movs r1, #0                 @ MON_DATA_PERSONALITY
    movs r2, #0
    ldr r3, lit_getmondata
    bl call3
    movs r1, #0x19              @ 25 natures
    ldr r3, lit_umodsi3
    bl call3                    @ __umodsi3
    lsls r0, r0, #0x18
    lsrs r0, r0, #0x18
    pop {r1}
    bx r1

call3:
    bx r3

.align 2
lit_getmondata: .word 0x0806A519
lit_umodsi3:    .word 0x082E7BE1
