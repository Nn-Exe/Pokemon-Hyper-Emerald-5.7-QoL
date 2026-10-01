@ DexNav: species you have not seen yet stay hidden (Hyper Emerald v5.7).
@ A species the Pokedex has not seen shows as a black shadow named "?????", the hint reads "Not seen yet", and A
@ on it buzzes instead of registering. Seen = GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_GET_SEEN),
@ the hack's own flags - a battle marks it, as for the Pokedex. Four `bl`s in the DexNav's code come here:
@   icon_hook  - the page draw's CreateMonIcon call (was `bl callr4`, r4 = CreateMonIcon)
@   name_hook  - the page draw's print of the species name (was `bl print`)
@   hint_pick  - draw_hint's `ldr r2, =state; ldrb r3, [r2, #9]`
@   arm_hook   - the A handler's `bl arm_search`
.thumb

@ icon_hook(r0 species, r1 callback, r2 x, r3 y, [sp] subpriority, [sp+4] personality, [sp+8] handleDeoxys;
@ r4 = CreateMonIcon): the icon as the game makes it, then, if unseen, drawn with the all-black palette
icon_hook:
    push {r4, r5, r6, lr}
    sub sp, #12
    ldr r5, [sp, #28]           @ the caller's three stack arguments, copied below our frame
    str r5, [sp]
    ldr r5, [sp, #32]
    str r5, [sp, #4]
    ldr r5, [sp, #36]
    str r5, [sp, #8]
    adds r6, r0, #0
    bl callr4                   @ CreateMonIcon -> sprite id
    adds r5, r0, #0
    cmp r5, #64                 @ MAX_SPRITES: no sprite was made
    bhs ih_ret
    adds r0, r6, #0
    bl is_seen
    cmp r0, #0
    bne ih_ret
    ldr r0, lit_shadow
    ldr r3, lit_loadspritepal
    bl callr3                   @ LoadSpritePalette -> its slot (the same one again if loaded), 0xFF if full
    cmp r0, #0xFF
    beq ih_ret
    lsls r0, r0, #4
    movs r1, #0x44
    muls r1, r5, r1
    ldr r2, lit_gsprites
    adds r1, r1, r2
    ldrb r2, [r1, #5]           @ oam attr2, high byte: the palette in bits 4-7
    movs r3, #0x0F
    ands r2, r3
    orrs r2, r0
    strb r2, [r1, #5]
ih_ret:
    adds r0, r5, #0
    add sp, #12
    pop {r4, r5, r6, pc}

@ name_hook(r0 window, r1 x, r2 y, r3 name, r4 colours): print, with "?????" for an unseen species. r6 is the
@ page draw's scratch, [0] = this row's species.
name_hook:
    push {r0, r1, r2, r3, r4, lr}
    ldrh r0, [r6]
    bl is_seen
    cmp r0, #0
    bne nh_print
    ldr r0, lit_str_unknown
    str r0, [sp, #12]
nh_print:
    pop {r0, r1, r2, r3, r4}
    bl PRINT_ADDR
    pop {pc}

@ hint_pick(r4 = the DexNav task's data, r5 = "A: Register"): on an unseen species that is not the one being
@ hunted, r5 = "Not seen yet" and r3 = 0, so draw_hint goes straight to drawing it; on a map with no Pokemon, r5 =
@ an empty string the same way; otherwise the two replaced instructions (r2 = state, r3 = its flags byte) and
@ draw_hint carries on as before.
hint_pick:
    push {r4, lr}
    bl CUR_INDEX_ADDR           @ r0 = page*7 + cursor
    ldr r3, lit_find
    bl callr3                   @ the row into the scratch; 0 if there is none
    cmp r0, #0
    beq hp_blank                @ no Pokemon on this map: nothing to register, no hint
    ldr r1, lit_scratch
    ldrh r0, [r1]
    ldr r2, lit_state
    ldrb r3, [r2, #9]
    lsls r3, r3, #31            @ bit 0: a hunt is on
    beq hp_check
    ldrh r3, [r2, #2]
    cmp r0, r3
    beq hp_orig                 @ the species being hunted: "A: Unregister", as before
hp_check:
    bl is_seen
    cmp r0, #0
    bne hp_orig
    ldr r5, lit_str_unseen
    movs r3, #0
    pop {r4, pc}
hp_blank:
    ldr r5, lit_str_blank
    movs r3, #0
    pop {r4, pc}
hp_orig:
    ldr r2, lit_state
    ldrb r3, [r2, #9]
    pop {r4, pc}

@ arm_hook(r0 species, r1 min level, r2 max level, r3 section): arm_search for a seen species; for an unseen one
@ the failure buzz and straight to dn_task's exit (add sp, #4; pop {r4-r6, pc}), past the leaving fade, so the
@ screen stays open. (Unregistering is decided before this call and is not affected.)
arm_hook:
    push {r0, r1, r2, r3, r4, lr}
    bl is_seen
    cmp r0, #0
    beq ah_refuse
    pop {r0, r1, r2, r3, r4}
    bl ARM_SEARCH_ADDR
    pop {pc}
ah_refuse:
    movs r0, #32                @ SE_FAILURE
    ldr r3, lit_playse
    bl callr3
    add sp, #24                 @ our r0-r4 and lr
    ldr r0, lit_dn_exit
    bx r0

@ is_seen(r0 = species) -> r0 = 1 if the Pokedex has seen it, or it has no dex number; else 0
is_seen:
    push {r4, lr}
    ldr r3, lit_tonational
    bl callr3
    cmp r0, #0
    beq is_yes
    movs r1, #0                 @ FLAG_GET_SEEN
    ldr r3, lit_dexflag
    bl callr3
    lsls r0, r0, #24
    beq is_ret
is_yes:
    movs r0, #1
is_ret:
    pop {r4, pc}

callr3:
    bx r3
callr4:
    bx r4

.align 2
lit_tonational:    .word 0x0806D4A5     @ SpeciesToNationalPokedexNum (the hack's table)
lit_dexflag:       .word 0x080C0665     @ GetSetPokedexFlag (a trampoline to the hack's 0x09257950)
lit_loadspritepal: .word 0x08008745     @ LoadSpritePalette
lit_gsprites:      .word 0x02020630
lit_playse:        .word 0x080A37A5
lit_find:          .word FIND_ADDR
lit_scratch:       .word SCRATCH_ADDR
lit_state:         .word STATE_ADDR
lit_dn_exit:       .word DN_EXIT_ADDR
lit_shadow:        .word SHADOW_ADDR
lit_str_unknown:   .word STR_UNKNOWN_ADDR
lit_str_unseen:    .word STR_UNSEEN_ADDR
lit_str_blank:     .word STR_BLANK_ADDR
