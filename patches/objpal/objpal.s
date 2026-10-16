@ objpal: an object's sprite palette slot by tag, in place of the hack's allocator (0x094A356A, which starts with a
@ jump here). r0 = the palette tag -> r0 = the slot (4-9; 10 only when every one of those is in use on screen).
@ 1. the slot that holds the tag already; 2. an empty one; 3. one that no sprite in use draws with;
@ 4. slot 10, as the hack did. Then the tag goes into sSpritePaletteTags and the hack's own routine loads the
@ palette (0x0808E91D: tag, slot). PAD is a mov r8, r8 or nothing, so that the pool starts on a word.
alloc:
    push {r4, r5, r6, r7, lr}
    movs r5, r0
    ldr r6, tags_lit
    ldr r7, ffff_lit
    movs r4, #4
have:
    lsls r3, r4, #1
    ldrh r3, [r6, r3]
    cmp r3, r5
    beq done
    adds r4, #1
    cmp r4, #10
    bne have
    movs r4, #4
empty:
    lsls r3, r4, #1
    ldrh r3, [r6, r3]
    cmp r3, r7
    beq take
    adds r4, #1
    cmp r4, #10
    bne empty
    movs r4, #4
unused:
    bl in_use
    cmp r0, #0
    beq take
    adds r4, #1
    cmp r4, #10
    bne unused
    movs r4, #10
take:
    lsls r3, r4, #1
    strh r5, [r6, r3]
    movs r0, r5
    movs r1, r4
    ldr r3, load_lit
    bl call_r3
done:
    movs r0, r4
    pop {r4, r5, r6, r7}
    pop {r3}
    bx r3
call_r3:
    bx r3

@ r4 = a slot -> r0 = 1 if a sprite in use draws with it (gSprites: 64 x 0x44 bytes; in use is bit 0 of the
@ halfword at +0x3E, the palette the top four bits of OAM attribute 2 at +4). Keeps r4.
in_use:
    ldr r0, sprites_lit
    movs r1, #64
    movs r3, #0x3E
next:
    ldrb r2, [r0, r3]
    lsls r2, r2, #31
    beq skip
    ldrh r2, [r0, #4]
    lsrs r2, r2, #12
    cmp r2, r4
    beq yes
skip:
    adds r0, #0x44
    subs r1, #1
    bne next
    movs r0, #0
    bx lr
yes:
    movs r0, #1
    bx lr
PAD
tags_lit: .word TAGS_ADDR
ffff_lit: .word 0xFFFF
load_lit: .word LOAD_ADDR
sprites_lit: .word SPRITES_ADDR
