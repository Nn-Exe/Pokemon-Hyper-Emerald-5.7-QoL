@ The new evolution items work when used from the Bag (gen9rest, Hyper Emerald v5.7). See gen9rest_patch.py.
@
@ The game's PokemonUseItemEffects (0x0806BD28) looks an item's effect up in gItemEffectTable (0x0831E58C,
@ items 13-178) and answers "it won't have any effect" for any item past 178. Every item the hack made to be
@ used for evolving is inside that range; the new ones (770-774) are not. item_effect takes the place of the
@ lookup (an 8-byte jump at 0x0806BE70; r4 = item - 13, the item at [sp, #0xC], r1 free) and does exactly what
@ the game did for every item, except that FIRST..LAST get the Thunder Stone's effect: an evolution item.
.thumb

item_effect:
    lsls r0, r4, #16
    lsrs r0, r0, #16
    cmp r0, #0xA5
    bhi ie_new
    ldr r1, l_table                 @ the game's own lookup
    lsls r0, r4, #2
    adds r0, r0, r1
    ldr r0, [r0]
    ldr r1, l_resume
    bx r1
ie_new:
    ldr r1, [sp, #0xC]              @ the item
    ldr r0, l_first
    cmp r1, r0
    blo ie_none
    ldr r0, l_last
    cmp r1, r0
    bhi ie_none
    ldr r0, l_stone
    ldr r1, l_resume
    bx r1
ie_none:
    ldr r1, l_none                  @ "it won't have any effect", as before
    bx r1
    PAD1
l_table:    .word 0x0831E58C        @ gItemEffectTable (item - 13)
l_resume:   .word 0x0806BE81        @ cmp r0, #0: on with the effect in r0
l_none:     .word 0x0806BEF1        @ return TRUE
l_first:    .word FIRST
l_last:     .word LAST
l_stone:    .word STONE             @ the Thunder Stone's effect
