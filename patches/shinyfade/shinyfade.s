@ Gold healthbox: fade with the rest of the screen (Hyper Emerald v5.7).
@ shinybox's paint (patches/shinybox, in the v1.4 base) wrote the gold palette into palette RAM and both palette
@ buffers on every battle frame. A fade works in those buffers, so the write undid it frame after frame: the gold
@ box stayed fully lit while everything else went to black - opening the Bag or the party, at the end of a battle.
@ paint2 takes paint's place (shiny_boxes' one `bl paint`). It keeps the gold in the unfaded buffer, which is what
@ a fade starts from, and puts it in the faded buffer only while the stock box palette (tag 0xD6FF) is shown
@ unfaded itself - so the gold box is exactly as faded as the plain one beside it. Palette RAM is left to the
@ game's own VBlank transfer.
.thumb

@ paint2(r4 = the box sprite, r6 = the palette slot it gets, r7 = the gold slot); r4-r7 come back as they were
paint2:
    push {r4, r5, r6, r7, lr}
    ldrh r1, [r4, #4]
    lsls r1, r1, #20
    lsrs r1, r1, #20
    lsls r2, r6, #12
    orrs r1, r2
    strh r1, [r4, #4]
    cmp r6, r7
    bne p2_ret                  @ back on the stock palette: nothing to load
    lsls r5, r7, #5             @ slot * 32
    ldr r6, lit_goldpal
    ldr r0, lit_unfaded
    adds r0, r0, r5
    bl gold_into
    ldr r0, lit_tags            @ where the stock box palette is
    ldr r1, lit_boxtag
    movs r2, #0
p2_find:
    ldrh r3, [r0]
    cmp r3, r1
    beq p2_stock
    adds r0, #2
    adds r2, #1
    cmp r2, #16
    blo p2_find
    b p2_show                   @ nowhere: nothing to go by
p2_stock:
    lsls r2, r2, #5
    ldr r0, lit_unfaded
    adds r0, r0, r2
    ldr r1, lit_faded
    adds r1, r1, r2
    movs r2, #0
p2_same:
    ldrh r3, [r0, r2]
    ldrh r4, [r1, r2]
    cmp r3, r4
    bne p2_ret                  @ a fade has the box palettes, ours with them: leave it to the fade
    adds r2, #2
    cmp r2, #32
    blo p2_same
p2_show:
    ldr r0, lit_faded
    adds r0, r0, r5
    bl gold_into
p2_ret:
    pop {r4, r5, r6, r7, pc}

@ gold_into(r0 = a palette's 16 colours in a buffer, r6 = the gold palette): every colour that is not the gold's
gold_into:
    push {r4, lr}
    movs r2, #0
gi_loop:
    ldrh r3, [r6, r2]
    ldrh r4, [r0, r2]
    cmp r3, r4
    beq gi_next
    strh r3, [r0, r2]
gi_next:
    adds r2, #2
    cmp r2, #32
    blo gi_loop
    pop {r4, pc}

.align 2
lit_goldpal:    .word GOLDPAL_ADDR
lit_unfaded:    .word 0x02037914        @ gPlttBufferUnfaded + 0x200 (OBJ half)
lit_faded:      .word 0x02037D14        @ gPlttBufferFaded   + 0x200
lit_tags:       .word 0x03000CF0        @ sSpritePaletteTags
lit_boxtag:     .word 0x0000D6FF        @ the healthbox palette's tag
