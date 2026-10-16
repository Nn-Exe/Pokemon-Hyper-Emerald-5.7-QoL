@ Messages in the mist (Hyper Emerald v5.7).
@ The hack draws its field message box see-through: its message task puts a window over the box and writes BLDCNT
@ 0x1E41 / BLDALPHA 0x0710 into the registers, and when the message goes away BLDCNT 0x1E40 / BLDALPHA 0x080C,
@ constants both. BLDALPHA is also what the weather's own see-through sprites are drawn with, so
@   - in mist (fog, weather 6 and 9; the underwater haze, 10 and 14 - 14 is the one the underwater maps use) the
@     whole fog turned nearly solid for as long as a message was up, and the map was gone behind it;
@   - after any message the weather was left on 12 / 8, the fog's numbers: right in fog, wrong for ash and
@     sandstorm (16 / 0) and for the underwater haze (4 / 16), until the map was loaded again.
@ The hack already falls back to the game's plain message box where its own cannot work: in a cave that needs Flash
@ (the flash level), and when its option says so. plain_box is asked in place of the flash level in the two places
@ that decide - which task draws the box, and which text colours go in front of the message - and answers "plain"
@ in mist as well. restore is the end-of-message routine's register write: what the game last set, from its copy.
.thumb

@ restore(r3 = 0x04000040): BLDCNT and BLDALPHA back to what SetGpuReg last gave them
restore:
    ldr r2, lit_regcopy
    ldr r2, [r2]
    str r2, [r3, #0x10]
    bx lr

@ plain_box() -> r5: not 0 for the plain box (a cave that needs Flash, as before, or mist). r0-r3 are kept: both
@ callers have theirs loaded.
plain_box:
    push {r0, r1, r2, r3, lr}
    ldr r5, lit_sb1
    ldr r5, [r5]
    adds r5, #0x30
    ldrb r5, [r5]               @ gSaveBlock1Ptr->flashLevel
    cmp r5, #0
    bne pb_ret
    ldr r3, lit_getweather
    bl pb_callr3
    cmp r0, #6                  @ WEATHER_FOG_HORIZONTAL
    beq pb_mist
    cmp r0, #9                  @ WEATHER_FOG_DIAGONAL
    beq pb_mist
    cmp r0, #10                 @ WEATHER_UNDERWATER
    beq pb_mist
    cmp r0, #14                 @ WEATHER_UNDERWATER_BUBBLES: the underwater maps
    bne pb_ret
pb_mist:
    movs r5, #1
pb_ret:
    pop {r0, r1, r2, r3, pc}
pb_callr3:
    bx r3

.align 2
lit_regcopy:    .word 0x03000868        @ sGpuRegBuffer + 0x50: the game's copy of BLDCNT, then BLDALPHA
lit_sb1:        .word 0x03005D8C        @ gSaveBlock1Ptr
lit_getweather: .word 0x080AC30D        @ GetCurrentWeather
