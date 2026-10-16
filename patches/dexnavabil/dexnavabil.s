@ DexNav: the bar names the ability the Pokemon will have (Hyper Emerald v5.7).
@ The search (patches/dexnavchain) took a species' abilities from the two bytes in the base stats, +22 and +23, to
@ choose the slot and to print its name. Those bytes are leftovers. The game reads three u16 a species at
@ ABILITIES_ADDR - two regular abilities, then the hidden one - through GetAbilityBySpecies (0x0806B694 ->
@ 0x09D73A80), and that is what a Pokemon's slot bit means. Two of the search's own `bl`s come here instead.
.thumb

@ slots_hook(r0 = species) -> r0: in place of reroll's `bl basestats`. reroll reads the bytes at +22 and +23 of
@ what comes back and rolls for the second slot when the second is neither 0 nor the first - it only compares
@ them. So it is handed one of two constant pairs: 1, 2 for a species with two different abilities, 1, 0 for one
@ with a single ability. r2 and r3 come back as they went in, as from basestats.
slots_hook:
    push {r2, r3, lr}
    movs r1, #6
    muls r0, r1
    ldr r1, lit_abilities
    adds r0, r0, r1
    ldrh r1, [r0]
    ldrh r2, [r0, #2]
    ldr r0, lit_one
    cmp r2, #0
    beq sl_ret
    cmp r2, r1
    beq sl_ret
    ldr r0, lit_two
sl_ret:
    pop {r2, r3, pc}

@ name_hook(r0 = the bar's scratch, r1 = the name the base-stats byte chose) -> r0 = end: in place of hud_text's
@ `bl scopy` for the ability line. r1 is dropped: the name copied is the one of table[species][slot], the slot
@ being what reroll() settled on and apply_extras() writes into the Pokemon (state +7). The id is 16 bits (the
@ hack's run past 255), and the names are found through the ROM header, as the game finds them.
name_hook:
    push {r4, lr}
    adds r4, r0, #0
    ldr r3, lit_state
    ldrh r0, [r3, #2]
    movs r1, #3
    muls r0, r1
    ldrb r1, [r3, #7]
    adds r0, r0, r1
    lsls r0, r0, #1
    ldr r1, lit_abilities
    ldrh r0, [r1, r0]
    movs r1, #13
    muls r0, r1
    ldr r1, lit_names
    ldr r1, [r1]
    adds r1, r0, r1
    adds r0, r4, #0
    ldr r3, lit_scopy
    bl callr3
    pop {r4, pc}

callr3:
    bx r3

.align 2
lit_abilities: .word ABILITIES_ADDR     @ the table GetAbilityBySpecies indexes (read from its own literal)
lit_one:       .word ONE_ADDR           @ 22 bytes before the pair 1, 0
lit_two:       .word TWO_ADDR           @ 22 bytes before the pair 1, 2
lit_state:     .word STATE_ADDR
lit_names:     .word 0x080001C0         @ ROM header: the ability names, 13 bytes each
lit_scopy:     .word SCOPY_ADDR
