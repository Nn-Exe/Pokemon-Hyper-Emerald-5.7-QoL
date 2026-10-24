@ Pokemon icons keep their own colours in the evening and at night (Hyper Emerald v5.7). See iconnight_patch.py.
@
@ The hack tints the screen for the hour in TransferPlttBuffer: its routine at 0x08CFE3E0 copies gPlttBufferFaded
@ to palette RAM with some colour channels halved, for BG palettes 0-11 and every sprite palette (the mask
@ 0xFFFF0FFF; BG 12-15 are the message boxes, the DexNav bar among them). The DexNav bar's Pokemon icon is a
@ sprite, so it took the night's colours on the bar's untinted black: Sunkern dark blue at 23:00, red at 19:00.
@
@ The routine leaves through one word, tinted or not: 0x08CFE4D4 = 0x080A19E7, back into TransferPlttBuffer.
@ icon_untint is put there: every sprite palette slot whose tag is a Pokemon icon palette's (0xDAC0..0xDAC5)
@ gets its 16 colours from gPlttBufferFaded again, as they are before the tint; then back. Entered with r0 = this
@ address and r1 = 0x80000200 (both loaded again there); r2-r7 hold TransferPlttBuffer's values and are kept.
.thumb

icon_untint:
    push {r2, r3, r4, r5}
    ldr r2, lit_tags                @ sSpritePaletteTags: the tag of each sprite palette slot
    ldr r3, lit_faded               @ gPlttBufferFaded's sprite palettes: the slot's colours before the tint
    ldr r4, lit_pltt                @ palette RAM's sprite palettes: what the screen shows
    movs r5, #16
iu_slot:
    ldrh r0, [r2]
    ldr r1, lit_icontag
    subs r0, r0, r1
    cmp r0, #5
    bhi iu_next                     @ (unsigned: a tag below 0xDAC0 is far above 5 too)
    movs r0, #0
iu_copy:
    ldr r1, [r3, r0]
    str r1, [r4, r0]
    adds r0, #4
    cmp r0, #32
    blt iu_copy
iu_next:
    adds r2, #2
    adds r3, #32
    adds r4, #32
    subs r5, #1
    bne iu_slot
    pop {r2, r3, r4, r5}
    ldr r0, lit_back
    bx r0

PADA
.align 2
lit_tags:    .word 0x03000CF0
lit_faded:   .word 0x02037D14
lit_pltt:    .word 0x05000200
lit_icontag: .word 0x0000DAC0
lit_back:    .word 0x080A19E7
