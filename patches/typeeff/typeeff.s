@ Move effectiveness indicator (Hyper Emerald v5.7).
@ The battle move list shows the damage multiplier of the highlighted move in front of the PP count,
@ colour coded: x4 red, x2 orange, x1 green, x.5/x.25 yellow, x0 black. In a double battle it follows the
@ target cursor.
@
@ Two entry points, both reached by an absolute jump (free space is out of bl range):
@   main - replaces the tail of MoveSelectionDisplayMoveType (bl BattlePutTextOnWindow / pop / pop / bx),
@          so it ends with that epilogue. r0 = gDisplayedStringBattle, r1 = window (10) on entry.
@   stub - replaces "bl DrawTargetCursor / movs r4,#0 / ldr r0,=gBattlersCount" at the top of
@          HandleInputChooseTarget, replaying all three, so the readout follows the target being chosen.
@ Reads the move list, gBattleMoves, gBattleMons types and the hack's own type chart; writes the battle
@ display string and two spare colours in BG palette 5 (the move box's palette).
.thumb

main:
    push {r4, r5, r6, r7, lr}
    ldr r3, lit_putwindow
    bl call3                    @ the type line goes out unchanged (r0, r1 already set)
    movs r0, #1                 @ the opposing Pokemon
    bl build_pp
    pop {r4, r5, r6, r7}
    pop {r3}
    @ the epilogue of the function this hook replaced
    pop {r4, r5, r6}
    pop {r0}
    bx r0

stub:
    push {r4, r5, r6, r7, lr}
    ldr r0, lit_multicursor     @ rebuild the call's arguments: the trampoline's "ldr r3" landed on r3,
    ldrb r0, [r0]               @ which is the fourth one (bounce speed), and a stray speed makes the
    movs r1, #1                 @ target's healthbox swing wildly instead of ticking gently.
    movs r2, #15
    movs r3, #1
    ldr r4, lit_drawcursor
    bl call4                    @ DoBounceEffect(target, BOUNCE_MON, 15, 1), as the original did
    ldr r0, lit_multicursor
    ldrb r0, [r0]               @ gMultiUsePlayerCursor: the target being chosen
    bl build_pp
    pop {r4, r5, r6, r7}
    pop {r3}
    movs r4, #0                 @ replayed
    ldr r0, lit_battlerscount   @ replayed
    ldr r3, lit_targetback
    bx r3

@ build_pp(r0 = defender battler): "xN PP" into the PP label window
build_pp:
    push {r4, r5, r6, r7, lr}
    adds r7, r0, #0
    bl setpal
    adds r0, r7, #0
    bl effect                   @ r0 = multiplier in hundredths, or 0xFFFF for "do not show"
    ldr r1, lit_skip
    cmp r0, r1
    bne have
    movs r1, #6                 @ nothing to show: empty prefix
    b pick
have:
    movs r1, #0
    cmp r0, #0
    beq pick                    @ x0
    movs r1, #1
    cmp r0, #50
    blo pick                    @ x.25 or less
    movs r1, #2
    cmp r0, #50
    beq pick                    @ x.5
    movs r1, #3
    cmp r0, #100
    beq pick                    @ x1
    movs r1, #4
    cmp r0, #200
    beq pick                    @ x2
    movs r1, #5                 @ x4 or more
pick:
    lsls r1, r1, #2
    ldr r0, lit_strtab
    ldr r5, [r0, r1]
    ldr r0, lit_scratch
    adds r1, r5, #0
    ldr r3, lit_stringcopy
    bl call3                    @ StringCopy returns the terminator
    ldr r1, lit_pptext
    ldr r3, lit_stringcopy
    bl call3
    ldr r0, lit_scratch
    movs r1, #7
    ldr r3, lit_putwindow
    bl call3
    pop {r4, r5, r6, r7, pc}

@ setpal: green and yellow into the two spare slots (5, 6) of the move box's palette
setpal:
    ldr r0, lit_green
    ldr r1, lit_yellow
    ldr r2, lit_pltt
    strh r0, [r2]
    strh r1, [r2, #2]
    ldr r2, lit_unfaded
    strh r0, [r2]
    strh r1, [r2, #2]
    ldr r2, lit_faded
    strh r0, [r2]
    strh r1, [r2, #2]
    bx lr

@ effect(r0 = defender battler) -> r0 = hundredths (100 = neutral), or 0xFFFF when nothing should be shown
effect:
    push {r4, r5, r6, r7, lr}
    mov r12, r0                 @ defender battler
    ldr r0, lit_active
    ldrb r0, [r0]               @ gActiveBattler
    ldr r1, lit_cursor
    ldrb r1, [r1, r0]           @ move cursor for this battler
    lsls r2, r0, #9
    ldr r3, lit_moveinfo
    adds r2, r2, r3
    lsls r1, r1, #1
    adds r2, r2, r1
    ldrh r2, [r2]               @ move id
    lsls r4, r2, #3
    lsls r5, r2, #2
    adds r4, r4, r5             @ move * 12
    ldr r5, lit_movepower
    adds r5, r5, r4
    ldrb r0, [r5]               @ power
    cmp r0, #0
    beq no_show                 @ status move: effectiveness does not apply
    ldrb r4, [r5, #1]           @ type
    cmp r4, #22
    bls atk_ok
    subs r4, #5                 @ the chart packs types over 22 down by 5 (Fairy 23 -> 18)
atk_ok:
    movs r7, #100               @ accumulator
    mov r0, r12
    cmp r0, #4
    bhs eff_ret                 @ no such battler
    lsls r1, r0, #6
    lsls r2, r0, #4
    adds r1, r1, r2
    lsls r2, r0, #3
    adds r1, r1, r2             @ battler * 0x58
    ldr r5, lit_battlemons
    adds r5, r5, r1
    ldrh r0, [r5]               @ species
    ldr r3, lit_tonatdex
    bl call3
    lsls r0, r0, #16
    lsrs r0, r0, #16
    movs r1, #1                 @ FLAG_GET_CAUGHT
    ldr r3, lit_dexflag
    bl call3
    lsls r0, r0, #24
    cmp r0, #0
    beq no_show                 @ not caught yet: no multiplier either
    adds r5, #0x21              @ -> type1
    ldrb r6, [r5]
    adds r0, r6, #0
    bl apply
    ldrb r0, [r5, #1]           @ type2
    cmp r0, r6
    beq third                   @ same as type1: count once
    bl apply
third:
    ldr r0, lit_structptr
    ldr r0, [r0]
    lsrs r1, r0, #24
    cmp r1, #2
    bne eff_ret                 @ no battle struct: skip the third type
    mov r1, r12
    lsls r2, r1, #4
    lsls r3, r1, #5
    adds r2, r2, r3             @ battler * 0x30
    adds r0, r0, r2
    ldrb r0, [r0, #7]
    lsls r0, r0, #27
    lsrs r0, r0, #27            @ third type (5 bits), 9 when unused
    cmp r0, r6
    beq eff_ret
    ldrb r1, [r5, #1]
    cmp r0, r1
    beq eff_ret
    bl apply
eff_ret:
    adds r0, r7, #0
    pop {r4, r5, r6, r7, pc}
no_show:
    ldr r0, lit_skip
    pop {r4, r5, r6, r7, pc}

@ apply: r0 = defender type, r4 = attacking type index, r7 = accumulator
apply:
    push {r1, r2, r3, lr}
    cmp r0, #9
    beq ap_ret                  @ the "mystery" type never changes damage
    cmp r0, #22
    bls ap_ok
    subs r0, #5
ap_ok:
    lsls r1, r4, #4             @ attacker row: type * 19
    lsls r2, r4, #1
    adds r1, r1, r2
    adds r1, r1, r4
    adds r1, r1, r0
    ldr r2, lit_chart
    ldrb r1, [r2, r1]           @ 0, 5, 10 or 20
    cmp r1, #0
    bne ap_half
    movs r7, #0
    b ap_ret
ap_half:
    cmp r1, #5
    bne ap_super
    lsrs r7, r7, #1
    b ap_ret
ap_super:
    cmp r1, #20
    bne ap_ret
    lsls r7, r7, #1
ap_ret:
    pop {r1, r2, r3, pc}

call3:
    bx r3
call4:
    bx r4

.align 2
lit_active:        .word 0x02024064    @ gActiveBattler
lit_cursor:        .word 0x020244B0    @ gMoveSelectionCursor
lit_moveinfo:      .word 0x02023068    @ &gBattleBufferA[0][4]: the chosen Pokemon's move list
lit_movepower:     .word 0x09D8641A    @ gBattleMoves + 1 (power; type at +1 from here)
lit_battlemons:    .word 0x02024084
lit_tonatdex:      .word 0x0806D4A5    @ SpeciesToNationalPokedexNum
lit_dexflag:       .word 0x080C0665    @ GetSetPokedexFlag(dexNum, case)
lit_structptr:     .word 0x02024218
lit_chart:         .word 0x09D76E88    @ 19 x 19, values 0 / 5 / 10 / 20
lit_multicursor:   .word 0x03005D74    @ gMultiUsePlayerCursor
lit_battlerscount: .word 0x0202406C
lit_drawcursor:    .word 0x08039C29
lit_targetback:    .word 0x08057845
lit_stringcopy:    .word 0x08008BA1
lit_putwindow:     .word 0x0814F9ED
lit_pptext:        .word 0x085CCA6F    @ "PP"
lit_scratch:       .word 0x02022EAC    @ spare tail of gDisplayedStringBattle
lit_skip:          .word 0x0000FFFF
lit_pltt:          .word 0x050000AA    @ BG palette 5, entries 5 and 6
lit_unfaded:       .word 0x020377BE
lit_faded:         .word 0x02037BBE
lit_green:         .word 0x00002726
lit_yellow:        .word 0x0000037F
lit_strtab:        .word STRTAB_ADDR
