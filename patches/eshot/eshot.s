@ eshot: a routine for the battle engine's script command 0x83 (its table of routines; the command calls one with the
@ script pointer already past its three bytes): `83 nnnn <pointer>` jumps to the pointer when rain falls on the
@ attacker, and steps over the pointer otherwise. Rain: gBattleWeather & 0x1007 (rain, downpour, lasting rain,
@ heavy rain: the engine's own mask, e.g. Swift Swim's at 0x09D5E4B0), the weather in effect (the engine's
@ 0x09D45B84: 0 while Cloud Nine or Air Lock is out) and the attacker not holding a Utility Umbrella (hold effect
@ 164, read as the Power Herb routine reads its own: 0x09D68700 with 1).
rain_jump:
    push {r4, lr}
    ldr r4, lit_instr
    ldr r3, lit_weather
    ldrh r3, [r3]
    ldr r2, lit_rain
    tst r3, r2
    beq skip
    bl #0x09D45B84
    cmp r0, #0
    beq skip
    ldr r0, lit_attacker
    ldrb r0, [r0]
    movs r1, #1
    bl #0x09D68700
    cmp r0, #164
    beq skip
    ldr r0, [r4]
    bl #0x09D3809A
    str r0, [r4]
    pop {r4, pc}
skip:
    ldr r3, [r4]
    adds r3, #4
    str r3, [r4]
    pop {r4, pc}
PAD
.align 2
lit_instr:          .word 0x02024214    @ gBattlescriptCurrInstr
lit_weather:        .word 0x020243CC    @ gBattleWeather
lit_rain:           .word 0x00001007
lit_attacker:       .word 0x0202420B    @ gBattlerAttacker
