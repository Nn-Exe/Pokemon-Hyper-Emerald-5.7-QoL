@ DexNav: list what the game itself would use on this map (Hyper Emerald v5.7).
@ map_header replaces the DexNav's find_header in its one call (find, once per table index). For index 0 it asks
@ the game's own GetCurrentMapWildMonHeaderId - the function every wild encounter goes through: the first entry
@ of the hack's table for this map, plus VAR 0x403E's set in Altering Cave - and returns that header; for index 1
@ (the Battle Pyramid's table, which the DexNav had been matching by map number) and for a map with no encounters
@ it returns 0, so find skips it.
.thumb

map_header:
    push {r4, lr}
    cmp r0, #0
    bne mh_none
    ldr r3, lit_getheaderid
    bl callr3
    lsls r0, r0, #16
    lsrs r0, r0, #16
    ldr r1, lit_ffff
    cmp r0, r1
    beq mh_none                 @ HEADER_NONE: nothing lives here
    movs r1, #20
    muls r0, r1, r0
    ldr r1, lit_headers
    adds r0, r0, r1
    pop {r4, pc}
mh_none:
    movs r0, #0
    pop {r4, pc}

callr3:
    bx r3

.align 2
lit_getheaderid: .word 0x080B4CF9       @ GetCurrentMapWildMonHeaderId
lit_ffff:        .word 0x0000FFFF
lit_headers:     .word HEADERS_ADDR     @ the table it indexes (read from its own literal)
