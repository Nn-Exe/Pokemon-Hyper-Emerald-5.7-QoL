@ Gold healthbox for a shiny opponent (Hyper Emerald v5.7).
@ Hooked into BattleMainCB2 (0x08038420), so it runs once per battle frame and re-applies itself.
@ Only OBJ palette RAM / the palette buffers and one OAM field per box sprite are written.
@
@ A healthbox is three sprites: the body (callback SpriteCallbackDummy, data[5] = its HP bar sprite,
@ data[6] = battler), the right half (callback 0x08072925, data[5] = the body) and the HP bar itself
@ (callback 0x080728B5, palette 5). Body and right half share the healthbox palette; the bar is left alone.
.thumb

@ Replaces "push {lr}; sub sp,#4; bl 0x080069C0" at 0x08038420, then continues at 0x08038428.
hook:
    push {lr}
    sub sp, #4
    ldr r3, lit_cb2_call
    bl callr3                   @ the bl the trampoline overwrote
    bl shiny_boxes
    ldr r3, lit_cb2_back
    bx r3

shiny_boxes:
    push {r4, r5, r6, r7, lr}
    movs r7, #0
    mvns r7, r7                 @ r7 = -1: no spare palette slot yet
    ldr r0, lit_tags
    movs r1, #15
fs_loop:
    lsls r2, r1, #1
    adds r2, r2, r0
    ldrh r2, [r2]
    ldr r3, lit_ffff
    cmp r2, r3
    bne fs_next                 @ tag set: slot is in use
    adds r7, r1, #0
    b fs_done
fs_next:
    subs r1, #1
    cmp r1, #10                 @ stay well clear of the reserved low slots
    bhs fs_loop
fs_done:
    cmp r7, #0
    blt sb_ret                  @ nothing spare: leave every box as it is
    ldr r4, lit_sprites
    movs r5, #0
sb_loop:
    ldrh r0, [r4, #0x3E]
    movs r1, #1
    tst r1, r0
    beq sb_next                 @ sprite not in use
    ldrh r0, [r4, #4]
    lsrs r0, r0, #12
    cmp r0, #4
    beq sb_pal_ok               @ stock healthbox palette
    cmp r0, #10
    blo sb_next                 @ neither stock nor one of ours
sb_pal_ok:
    ldr r0, [r4, #0x1C]
    ldr r1, lit_bodycb
    cmp r0, r1
    beq sb_body
    ldr r1, lit_rightcb
    cmp r0, r1
    bne sb_next
    ldrh r0, [r4, #0x38]        @ right half: data[5] = the body sprite
    bl sprite_ptr
    cmp r0, #0
    beq sb_next
    ldrh r6, [r0, #0x3A]        @ battler from the body
    b sb_have_battler
sb_body:
    ldrh r0, [r4, #0x38]        @ body: data[5] = its HP bar sprite
    bl sprite_ptr
    cmp r0, #0
    beq sb_next
    ldr r0, [r0, #0x1C]
    ldr r1, lit_barcb
    cmp r0, r1
    bne sb_next                 @ not a healthbox after all
    ldrh r6, [r4, #0x3A]
sb_have_battler:
    cmp r6, #4
    bhs sb_next
    movs r0, #1
    tst r0, r6
    beq sb_next                 @ even battler ids are the player's side
    lsls r0, r6, #6
    lsls r1, r6, #4
    adds r0, r0, r1
    lsls r1, r6, #3
    adds r0, r0, r1             @ battler * 0x58
    ldr r1, lit_battlemons
    adds r0, r0, r1
    ldr r1, [r0, #0x48]         @ personality
    ldr r2, [r0, #0x54]         @ otId
    eors r1, r2
    lsrs r2, r1, #16
    eors r1, r2
    lsls r1, r1, #16
    lsrs r1, r1, #16
    cmp r1, #SHINY_ODDS
    blo sb_gold
    movs r6, #4                 @ not shiny: back to the stock palette. gBattleMons is still blank
    b sb_apply                  @ while the boxes are built, so this undoes that frame.
sb_gold:
    adds r6, r7, #0
sb_apply:
    bl paint
sb_next:
    adds r4, #0x44
    adds r5, #1
    cmp r5, #64
    blo sb_loop
sb_ret:
    pop {r4, r5, r6, r7, pc}

@ sprite_ptr: r0 = sprite index -> r0 = &gSprites[index], or 0 if out of range / not in use.
sprite_ptr:
    cmp r0, #64
    bhs spr_none
    lsls r1, r0, #6
    lsls r2, r0, #2
    adds r1, r1, r2             @ * 0x44
    ldr r2, lit_sprites
    adds r0, r1, r2
    ldrh r1, [r0, #0x3E]
    movs r2, #1
    tst r2, r1
    beq spr_none
    bx lr
spr_none:
    movs r0, #0
    bx lr

@ paint: r4 = sprite, r6 = palette slot for it, r7 = the gold slot.
paint:
    push {r4, r5, lr}
    ldrh r1, [r4, #4]
    lsls r1, r1, #20
    lsrs r1, r1, #20
    lsls r2, r6, #12
    orrs r1, r2
    strh r1, [r4, #4]
    cmp r6, r7
    bne pg_ret                  @ restoring the stock palette: nothing to load
    lsls r0, r7, #5             @ slot * 32
    ldr r1, lit_objpal
    adds r1, r1, r0             @ palette RAM
    ldr r2, lit_unfaded
    adds r2, r2, r0             @ gPlttBufferUnfaded (what a fade recomputes from)
    ldr r3, lit_faded
    adds r3, r3, r0             @ gPlttBufferFaded (what the VBlank transfer copies)
    ldr r0, lit_goldpal
    movs r4, #16
pg_copy:
    ldrh r5, [r0]
    strh r5, [r1]
    strh r5, [r2]
    strh r5, [r3]
    adds r0, #2
    adds r1, #2
    adds r2, #2
    adds r3, #2
    subs r4, #1
    bne pg_copy
pg_ret:
    pop {r4, r5, pc}

callr3:
    bx r3

.align 2
lit_goldpal:     .word GOLDPAL_ADDR
lit_cb2_call:    .word 0x080069C1
lit_cb2_back:    .word 0x08038429
lit_tags:        .word 0x03000CF0
lit_sprites:     .word 0x02020630
lit_battlemons:  .word 0x02024084
lit_objpal:      .word 0x05000200
lit_unfaded:     .word 0x02037914    @ gPlttBufferUnfaded + 0x200 (OBJ half)
lit_faded:       .word 0x02037D14    @ gPlttBufferFaded   + 0x200
lit_bodycb:      .word 0x08007429    @ SpriteCallbackDummy (healthbox body)
lit_rightcb:     .word 0x08072925    @ right half of the box
lit_barcb:       .word 0x080728B5    @ HP bar (never repainted)
lit_ffff:        .word 0x0000FFFF
