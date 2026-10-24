@ A wild Pokemon keeps the item it was given before the battle (Hyper Emerald v5.7). See wilditem_patch.py.
@
@ The game's SetWildMonHeldItem (0x0806EA68) runs as every battle is set up and, unless the battle is a trainer's
@ or a legendary one, gives gEnemyParty[0] one of its species' two wild items or leaves it as it is: 45 in 100
@ nothing changes, 50 the common item, 5 the rare one (20 / 60 / 20 with Compound Eyes and two more abilities in
@ the lead). It never looks whether the Pokemon holds something already, so the item a script gave it
@ (setwildbattle's third word: the Abandoned Ship's Pikachu and its Light Ball) or DexNav's rolled one was
@ replaced more than half the time - with the species' common item, or with nothing when the species has none.
@
@ keep_item is entered from 0x0806EA7C, where the function was about to draw its number (Random16) once the
@ battle type had passed; the prologue has run, so lr is on the stack and r0-r3 are free. A Pokemon that holds an
@ item goes straight to the function's end; any other is rolled for as before.
.thumb

keep_item:
    ldr r0, lit_party           @ gEnemyParty[0]
    movs r1, #12                @ MON_DATA_HELD_ITEM
    movs r2, #0
    ldr r3, lit_getmondata
    bl call_r3
    cmp r0, #0
    bne ki_keep
    ldr r3, lit_random          @ what 0x0806EA7C..0x0806EA83 did: r0 = Random16()
    bl call_r3
    lsls r0, r0, #16
    lsrs r0, r0, #16
    ldr r3, lit_roll
    bx r3
ki_keep:
    ldr r3, lit_end
    bx r3
call_r3:
    bx r3

PADA
.align 2
lit_party:      .word 0x02024744
lit_getmondata: .word 0x0806A519
lit_random:     .word 0x0806F5CD
lit_roll:       .word 0x0806EA85
lit_end:        .word 0x0806EB91
