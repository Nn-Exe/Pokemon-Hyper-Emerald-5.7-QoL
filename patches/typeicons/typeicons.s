@ Type badges beside the opponent's healthbox (Hyper Emerald v5.7).
@ Runs once per battle frame, chained from the shinybox hook (its "bl shiny_boxes" now lands on `entry`).
@ For each opponent healthbox body it keeps up to two 16x16 badge sprites (type 1 / type 2) 80px to the
@ right, following the box's position and visibility, showing gBattleMons types (so Soak/Protean etc. show).
@ Badge sprites are recognised by their unique callback (badge_cb); data[6] = battler, data[7] = slot,
@ data[0] = type currently shown. Only OAM/sprite state is written; nothing else in the game is touched.
.thumb

entry:
    push {lr}
    ldr r3, lit_shinyboxes
    bl callr3                   @ the call this replaced
    bl badges
    pop {pc}

badge_cb:
    bx lr

badges:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x20               @ [0x00] badge[k][s] x4, [0x10] body[k] x2, [0x18] type scratch
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    str r0, [sp, #8]
    str r0, [sp, #0xC]
    str r0, [sp, #0x10]
    str r0, [sp, #0x14]
    @ our palette loaded? (tag in sSpritePaletteTags)
    ldr r0, lit_tags
    movs r1, #0
pal_scan:
    lsls r2, r1, #1
    ldrh r2, [r0, r2]
    ldr r3, lit_ourtag
    cmp r2, r3
    beq pal_ok
    adds r1, #1
    cmp r1, #16
    blo pal_scan
    ldr r0, lit_palstruct
    ldr r3, lit_loadspritepal
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #16
    blo pal_ok
    b b_ret                     @ no free palette slot: try again next frame
pal_ok:
    @ ---- pass 1: collect our badges and the opponent healthbox bodies ----
    ldr r4, lit_sprites
    movs r5, #0
p1_loop:
    ldrh r0, [r4, #0x3E]
    movs r1, #1
    tst r1, r0
    beq p1_next
    ldr r0, [r4, #0x1C]
    ldr r1, lit_badgecb
    cmp r0, r1
    bne p1_body
    ldrh r1, [r4, #0x3A]        @ battler
    ldrh r2, [r4, #0x3C]        @ slot
    lsrs r1, r1, #1
    cmp r1, #2
    bhs p1_next
    cmp r2, #2
    bhs p1_next
    lsls r1, r1, #1
    adds r1, r1, r2
    lsls r1, r1, #2
    add r1, sp
    str r4, [r1]
    b p1_next
p1_body:
    ldr r1, lit_dummycb
    cmp r0, r1
    bne p1_next
    ldrh r0, [r4, #4]
    lsrs r0, r0, #12
    cmp r0, #4
    beq p1_b2
    cmp r0, #10
    blo p1_next
p1_b2:
    ldrh r0, [r4, #0x38]        @ data[5] must be the HP bar sprite
    cmp r0, #64
    bhs p1_next
    lsls r1, r0, #6
    lsls r2, r0, #2
    adds r1, r1, r2
    ldr r2, lit_sprites
    adds r0, r1, r2
    ldr r0, [r0, #0x1C]
    ldr r1, lit_barcb
    cmp r0, r1
    bne p1_next
    ldrh r1, [r4, #0x3A]        @ battler: opponents are odd
    movs r0, #1
    tst r0, r1
    beq p1_next
    cmp r1, #4
    bhs p1_next
    lsrs r1, r1, #1
    lsls r1, r1, #2
    adds r1, #0x10
    add r1, sp
    str r4, [r1]
p1_next:
    adds r4, #0x44
    adds r5, #1
    cmp r5, #64
    blo p1_loop
    @ ---- pass 2: per opponent box, per slot ----
    movs r7, #0                 @ k: battler 2k+1
p2_loop:
    cmp r7, #2
    blo p2_body
    b b_ret
p2_body:
    lsls r0, r7, #2
    adds r0, #0x10
    add r0, sp
    ldr r6, [r0]                @ body sprite or 0
    movs r5, #0                 @ slot
p2_slot:
    cmp r5, #2
    bhs p2_next
    lsls r0, r7, #1
    adds r0, r0, r5
    lsls r0, r0, #2
    add r0, sp
    ldr r4, [r0]                @ badge sprite or 0
    cmp r6, #0
    beq p2_hide                 @ no box on screen: keep any badge hidden
    lsls r0, r7, #1
    adds r0, #1                 @ battler
    lsls r1, r0, #6
    lsls r2, r0, #4
    adds r1, r1, r2
    lsls r2, r0, #3
    adds r1, r1, r2             @ * 0x58
    ldr r2, lit_battlemons
    adds r1, r1, r2
    ldrh r0, [r1]               @ species
    push {r1}
    bl caught
    pop {r1}
    cmp r0, #0
    beq p2_hide                 @ not caught yet: keep its types hidden
    adds r1, #0x21
    ldrb r2, [r1]               @ type1
    ldrb r3, [r1, #1]           @ type2
    cmp r5, #0
    beq p2_have_type
    cmp r3, r2
    beq p2_hide                 @ single-typed: no second badge
    adds r2, r3, #0
p2_have_type:
    cmp r2, #24
    bhs p2_hide                 @ no glyph for this type id
    cmp r4, #0
    bne p2_update
    str r2, [sp, #0x18]
    ldr r0, lit_template
    movs r1, #0
    movs r2, #0
    movs r3, #0
    ldr r4, lit_createsprite
    bl callr4
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #64
    bhs p2_slot_next            @ no sprite slot: try next frame
    lsls r1, r0, #6
    lsls r2, r0, #2
    adds r1, r1, r2
    ldr r2, lit_sprites
    adds r4, r1, r2
    lsls r0, r7, #1
    adds r0, #1
    strh r0, [r4, #0x3A]        @ data[6] = battler
    strh r5, [r4, #0x3C]        @ data[7] = slot
    movs r0, #0xFF
    strh r0, [r4, #0x2E]        @ data[0] = type shown (none yet)
    ldr r2, [sp, #0x18]
p2_update:
    ldrh r0, [r6, #0x20]        @ follow the box: x + 68 (16x16 sprite centre; badge's left edge at box.x + 60,
    adds r0, #68                @ overlapping the box's slanted tail like SoulGold; badges draw above the box)
    strh r0, [r4, #0x20]
    ldrh r0, [r6, #0x22]        @ y - 6 (slot 0) / y + 5 (slot 1): 11px pitch for the 8x12 badges
    subs r0, #6
    cmp r5, #0
    beq p2_y
    adds r0, #11
p2_y:
    strh r0, [r4, #0x22]
    ldrh r0, [r6, #0x3E]        @ visibility follows the box (bit 2)
    movs r1, #4
    ands r0, r1
    ldrh r1, [r4, #0x3E]
    movs r3, #4
    bics r1, r3
    orrs r1, r0
    strh r1, [r4, #0x3E]
    ldrh r0, [r4, #0x2E]
    cmp r0, r2
    beq p2_slot_next            @ already showing this type
    strh r2, [r4, #0x2E]
    adds r3, r4, #0
    adds r3, #0x2A
    strb r2, [r3]               @ animNum = type  (anim n = image n)
    movs r0, #0
    strb r0, [r3, #1]           @ animCmdIndex
    strb r0, [r3, #2]           @ animDelayCounter
    ldrh r0, [r4, #0x3E]
    movs r1, #0x80
    lsls r1, r1, #3             @ animBeginning
    orrs r0, r1
    lsls r1, r1, #2             @ animEnded
    bics r0, r1
    strh r0, [r4, #0x3E]        @ AnimateSprites copies the new image into the badge's tiles
    b p2_slot_next
p2_hide:
    cmp r4, #0
    beq p2_slot_next
    ldrh r0, [r4, #0x3E]
    movs r1, #4
    orrs r0, r1
    strh r0, [r4, #0x3E]
p2_slot_next:
    adds r5, #1
    b p2_slot
p2_next:
    adds r7, #1
    b p2_loop
b_ret:
    add sp, #0x20
    pop {r4, r5, r6, r7, pc}

@ caught: r0 = species -> r0 = 1 when its Pokedex entry is caught, else 0
caught:
    push {r4, r5, r6, r7, lr}
    ldr r3, lit_tonatdex
    bl callr3
    lsls r0, r0, #16
    lsrs r0, r0, #16
    movs r1, #1                 @ FLAG_GET_CAUGHT
    ldr r3, lit_dexflag
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    pop {r4, r5, r6, r7, pc}

callr3:
    bx r3
callr4:
    bx r4

.align 2
lit_shinyboxes:     .word 0x08FDA0C3
lit_tags:           .word 0x03000CF0
lit_sprites:        .word 0x02020630
lit_battlemons:     .word 0x02024084
lit_tonatdex:       .word 0x0806D4A5    @ SpeciesToNationalPokedexNum
lit_dexflag:        .word 0x080C0665    @ GetSetPokedexFlag(dexNum, case)
lit_dummycb:        .word 0x08007429
lit_barcb:          .word 0x080728B5
lit_loadspritepal:  .word 0x08008745
lit_createsprite:   .word 0x08006DF5
lit_ourtag:         .word OURTAG
lit_badgecb:        .word BADGECB_ADDR
lit_template:       .word TEMPLATE_ADDR
lit_palstruct:      .word PALSTRUCT_ADDR
