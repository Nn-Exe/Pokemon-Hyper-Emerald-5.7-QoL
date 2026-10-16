@ sprframe: a sprite's picture is copied into sprite memory only if it can be one.
@ ProcessSpriteCopyRequests (0x0800742C) hands every queued {address, where, size} to the BIOS's CpuSet. A request
@ comes from images[frame number] of the sprite's picture table; a table with fewer pictures than the sprite's
@ animations show gives whatever lies after it in the ROM. guard stands in the 8 bytes at 0x08007454
@ (ldrh r2, [r2, #8]; lsrs r2, r2, #1; bl CpuSet) and goes back to 0x0800745C.
@ In: r0 = address, r1 = where in sprite memory, r2 = the request; r4-r7 are the loop's and are left alone.
@ PAD is a mov r8, r8 or nothing, so that the pool starts on a word.
guard:
    ldrh r2, [r2, #8]           @ the size in bytes
    lsrs r3, r0, #24            @ where the picture is: 02 EWRAM, 03 IWRAM, 08 and 09 the ROM; nothing else
    cmp r3, #2
    beq region_ok
    cmp r3, #3
    beq region_ok
    cmp r3, #8
    beq region_ok
    cmp r3, #9
    bne skip
region_ok:
    cmp r2, #0
    beq skip
    movs r3, #0x10              @ the largest picture a sprite has is 64 x 64 (0x800 bytes); twice that is let by
    lsls r3, r3, #8
    cmp r2, r3
    bhi skip
    adds r3, r1, r2             @ and it has to end inside sprite memory
    push {r4}
    ldr r4, end_lit
    cmp r3, r4
    pop {r4}
    bhi skip
    lsrs r2, r2, #1
    svc 0x0B                    @ CpuSet(address, where, halfwords): a 16-bit copy, as the game's CpuCopy16
skip:
    ldr r3, back_lit
    bx r3
PAD
end_lit: .word 0x06018000
back_lit: .word BACK_ADDR
