@ EV-IV Display: every picture in its own colours (Hyper Emerald v5.7).
@ The display (the hack's own screen, item 650) makes the next Pokemon's picture before the task of the one on
@ screen has removed it, and asked for the palette by its tag. The hack's palette tables give species 1-439 a tag
@ of their own and every one after that the same two: 1 or 0 (501 / 500 shiny). With the old picture's tag still
@ loaded, a new picture with the same tag was told "already loaded" and came up in the old one's colours.
@ pic takes the place of the routine that makes the picture (0x0968A6C0, called from one place), in its own bytes.
@ It asks for a palette slot instead of a tag: 15, or 14 when the picture on screen has 15 - so the two that exist
@ for a moment never share one. The game's own picture code loads the colours there (the Pokedex's way).
.thumb

@ pic(r0 = species, r1 = OT id, r2 = personality, r3 = x, [sp] = y) -> r0 = the picture's sprite, or 64
pic:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x14
    ldr r4, lit_state           @ the picture on screen: the sprite its slide task holds (data[2])
    ldr r4, [r4]
    ldrb r4, [r4, #4]
    movs r5, #40
    muls r4, r5
    ldr r5, lit_gtasks
    adds r4, r4, r5
    ldrh r4, [r4, #0xC]
    movs r6, #15
    cmp r4, #64                 @ (nothing yet, the first time: whatever is there is not a sprite on slot 15)
    bhs pic_slot
    movs r5, #0x44
    muls r4, r5
    ldr r5, lit_gsprites
    adds r4, r4, r5
    ldrb r4, [r4, #5]
    lsrs r4, r4, #4
    cmp r4, #15
    bne pic_slot
    movs r6, #14
pic_slot:
    ldr r4, [sp, #0x28]         @ CreateMonPicSprite_HandleDeoxys(species, otId, personality, TRUE, x, y, slot, no tag)
    str r3, [sp]
    str r4, [sp, #4]
    str r6, [sp, #8]
    ldr r4, lit_ffff
    str r4, [sp, #0xC]
    movs r3, #1
    ldr r4, lit_createpic
    bl pic_callr4
    adds r4, r0, #0
    adds r0, r6, #0             @ as the routine did for the slot the tag had: PreservePaletteInWeather(16 + slot)
    adds r0, #0x10
    ldr r3, lit_preserve
    bl pic_callr3
    ldr r3, lit_ffff
    cmp r4, r3
    bne pic_ok
    movs r4, #0x40              @ no picture: MAX_SPRITES, as before
pic_ok:
    lsls r0, r4, #24
    lsrs r0, r0, #24
    add sp, #0x14
    pop {r4, r5, r6, r7, pc}

pic_callr3:
    bx r3
pic_callr4:
    bx r4

.align 2
lit_state:      .word 0x0203FFF0        @ the display's state: a pointer; +4 the slide task of the picture on screen
lit_gtasks:     .word 0x03005E00
lit_gsprites:   .word 0x02020630
lit_ffff:       .word 0x0000FFFF
lit_createpic:  .word 0x0818D7D9        @ CreateMonPicSprite_HandleDeoxys
lit_preserve:   .word 0x080AC3F9        @ PreservePaletteInWeather
