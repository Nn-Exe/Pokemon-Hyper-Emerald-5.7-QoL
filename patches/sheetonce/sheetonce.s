@ The move menu's sprite sheet is loaded once (Hyper Emerald v5.7). See sheetonce_patch.py.
@ load_once takes the place of LoadCompressedSpriteSheet in the hack's routine at 0x09D6077C (its pool word
@ 0x09D60848): the sheet is loaded only if no sheet with its tag is loaded.
.thumb

@ load_once(r0 = {data, u16 size, u16 tag}) -> r0 = what LoadCompressedSpriteSheet gives, or the tile the sheet
@ already starts at (the caller uses neither)
load_once:
    push {r4, lr}
    adds r4, r0, #0
    ldrh r0, [r4, #6]
    ldr r3, lit_tilestart
    bl callr3                   @ GetSpriteTileStartByTag(tag): 0xFFFF if it is not loaded
    lsls r0, r0, #16
    lsrs r0, r0, #16
    ldr r1, lit_ffff
    cmp r0, r1
    bne lo_ret
    adds r0, r4, #0
    ldr r3, lit_load
    bl callr3
lo_ret:
    pop {r4, pc}
callr3:
    bx r3
    mov r8, r8

.align 2
lit_tilestart:  .word 0x08008621        @ GetSpriteTileStartByTag
lit_load:       .word 0x08034531        @ LoadCompressedSpriteSheet
lit_ffff:       .word 0x0000FFFF
