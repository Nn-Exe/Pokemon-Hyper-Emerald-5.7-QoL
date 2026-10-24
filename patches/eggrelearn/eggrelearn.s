@ Egg moves in the Move Relearner (Hyper Emerald v5.7). See eggrelearn_patch.py.
@
@ The relearner's list was GetMoveRelearnerMoves' (0x0806E0B4 -> the hack's 0x09D6A9D9): the level-up moves up to
@ the Pokemon's level that it does not know, at most 24, in sMoveRelearnerStruct (0x0203BC34), which has the vanilla
@ room: 25 moves at +0x12 and 25 menu items at +0x48. collect puts the egg moves after them: those of the Pokemon's
@ species and of each species it evolved from (walked back as the game's egg species routine walks); when it evolved
@ from nothing in the table, of the species that routine (0x09F00600, mode 0) gives: the Eeveelutions, Manaphy and
@ Hisuian Typhlosion are hard-wired there. Each move once, none the Pokemon knows, at most 64 in all.
@ The struct is allocated 0x320 bytes (patched at both sites), with 65 menu items at +0x118. create_list is
@ CreateLearnableMovesList (0x08161280) and selected_move GetCurrentSelectedMove (0x08161054), the only two readers
@ of the items; count_moves is GetNumberOfRelearnableMoves (the word at 0x0806E260), which the Fallarbor tutor's
@ party screen asks for ABLE / NOT ABLE and "no move to teach".
.thumb

@ CreateLearnableMovesList(void), entered from its first instruction (a trampoline there)
create_list:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x90                   @ sp: the moves (64 halfwords); sp + 0x80: the nickname
    ldr r4, lit_struct
    ldr r4, [r4]                    @ sMoveRelearnerStruct
    movs r0, #0x44
    ldrb r0, [r4, r0]               @ partyMon
    movs r1, #100
    muls r0, r1, r0
    ldr r5, lit_party
    adds r5, r5, r0                 @ the Pokemon
    adds r0, r5, #0
    mov r1, sp
    bl collect
    adds r6, r0, #0                 @ how many moves
    ldr r7, lit_items
    adds r7, r4, r7                 @ the menu items, +0x118
    movs r2, #0
cl_item:
    cmp r2, r6
    bhs cl_cancel
    lsls r0, r2, #1
    mov r1, sp
    ldrh r0, [r1, r0]               @ the move
    lsls r1, r2, #3
    adds r1, r7, r1
    str r0, [r1, #4]                @ .id = the move, as the game's own list has it
    movs r3, #13
    muls r0, r3, r0
    ldr r3, lit_names
    ldr r3, [r3]                    @ gMoveNames, from the ROM header (gen9 moved them)
    adds r0, r3, r0
    str r0, [r1]                    @ .name
    adds r2, #1
    b cl_item
cl_cancel:
    adds r0, r5, #0
    movs r1, #2                     @ MON_DATA_NICKNAME
    add r2, sp, #0x80
    ldr r3, lit_getmondata
    bl call_r3
    ldr r0, lit_strvar1
    add r1, sp, #0x80
    ldr r3, lit_copynick            @ StringCopy_Nickname(gStringVar1, nickname)
    bl call_r3
    lsls r1, r6, #3
    adds r1, r7, r1
    ldr r0, lit_cancel
    str r0, [r1]                    @ Cancel, id LIST_CANCEL (-2)
    movs r0, #2
    rsbs r0, r0, #0
    str r0, [r1, #4]
    adds r6, #1
    movs r0, #0x88
    lsls r0, r0, #1
    strb r6, [r4, r0]               @ numMenuChoices (+0x110)
    adds r0, r7, #0
    adds r1, r6, #0
    ldr r3, lit_loadlist            @ LoadMoveRelearnerMovesList(items, n): the list menu's template
    bl call_r3
    ldr r1, lit_showcount
    strb r0, [r4, r1]               @ numToShowAtOnce (+0x111)
    add sp, #0x90
    pop {r4, r5, r6, r7}
    pop {r0}
    bx r0

@ GetCurrentSelectedMove(void): the id of the item under the cursor, from +0x118 (the game's read +0x48)
selected_move:
    ldr r0, lit_struct
    ldr r2, [r0]
    ldr r1, lit_menustate
    ldrh r0, [r1, #2]               @ listRow
    ldrh r1, [r1]                   @ listOffset
    adds r0, r0, r1
    lsls r0, r0, #3
    adds r2, r2, r0
    ldr r1, lit_items_id
    ldr r0, [r2, r1]
    bx lr

@ GetNumberOfRelearnableMoves(mon), from the word at 0x0806E260: the length of the list
count_moves:
    push {lr}
    sub sp, #0x80
    mov r1, sp
    bl collect
    add sp, #0x80
    pop {r1}
    bx r1

@ collect(mon, moves) -> how many: the level-up moves (GetMoveRelearnerMoves), then the egg moves
collect:
    push {r4, r5, r6, r7, lr}
    mov r7, r8
    push {r7}
    adds r4, r0, #0                 @ the Pokemon
    adds r5, r1, #0                 @ the list
    ldr r3, lit_levelup             @ GetMoveRelearnerMoves: the hack's, at most 24
    bl call_r3
    adds r6, r0, #0                 @ how many so far
    ldrh r7, [r4, #0x20]            @ the species
    movs r0, #8
    mov r8, r0                      @ at most 8 steps back
co_chain:
    adds r0, r7, #0
    bl add_egg
    mov r0, r8
    subs r0, #1
    mov r8, r0
    beq co_base
    adds r0, r7, #0
    bl preevo
    cmp r0, #0
    beq co_base
    adds r7, r0, #0
    b co_chain
co_base:
    ldrh r0, [r4, #0x20]
    cmp r0, r7
    bne co_done                     @ it evolved from something: the game's routine walks the same way
    movs r1, #0                     @ mode 0: no random pick
    ldr r3, lit_eggspecies          @ the species the game hatches for it: its hard-wired cases
    bl call_r3
    bl add_egg
co_done:
    adds r0, r6, #0
    pop {r7}
    mov r8, r7
    pop {r4, r5, r6, r7}
    pop {r1}
    bx r1

@ add_egg(species): its egg moves (GetEggMoves' table: species + 20000, then its moves) onto the list r5 (count r6),
@ but not one the Pokemon r4 knows, one listed already, or past 64
add_egg:
    push {r7, lr}
    ldr r1, lit_marker
    adds r0, r0, r1                 @ the species' marker
    ldr r1, lit_eggtable
    ldr r1, [r1]                    @ the table, from GetEggMoves' literal (gen9egg moved it)
ae_find:
    ldrh r2, [r1]
    adds r1, #2
    cmp r2, r0
    beq ae_move
    ldr r3, lit_end
    cmp r2, r3
    bne ae_find
    pop {r7, pc}
ae_move:
    ldrh r7, [r1]
    adds r1, #2
    ldr r3, lit_marker
    cmp r7, r3
    bhi ae_done                     @ the next species' marker, or the table's end
    cmp r6, #64
    bhs ae_done
    ldrh r3, [r4, #0x2C]            @ the four moves it knows
    cmp r3, r7
    beq ae_move
    ldrh r3, [r4, #0x2E]
    cmp r3, r7
    beq ae_move
    ldrh r3, [r4, #0x30]
    cmp r3, r7
    beq ae_move
    ldrh r3, [r4, #0x32]
    cmp r3, r7
    beq ae_move
    movs r2, #0
ae_dup:
    cmp r2, r6
    bhs ae_add
    lsls r3, r2, #1
    ldrh r3, [r5, r3]
    cmp r3, r7
    beq ae_move
    adds r2, #1
    b ae_dup
ae_add:
    lsls r3, r6, #1
    strh r7, [r5, r3]
    adds r6, #1
    b ae_move
ae_done:
    pop {r7, pc}

@ preevo(species) -> a species that evolves into it, or 0. The rule of the game's egg species routine
@ (0x09F00628..0x09F00650): species 1..0x57F, five entries of 8 bytes each, the target at +4, the method's low
@ byte at most 0xF9 (above that: Mega Evolutions and form changes); the first one found. The five entries are
@ unrolled: a whole scan is most of the time this takes.
preevo:
    push {r4, r5, lr}
    ldr r1, lit_evoptr
    ldr r1, [r1]                    @ gEvolutionTable, through the literal the game's routine reads
    adds r1, #40                    @ species 1
    movs r4, #1
    ldr r5, lit_last
pe_species:
    ldrh r3, [r1, #4]
    cmp r3, r0
    beq pe_e0
pe_1:
    ldrh r3, [r1, #12]
    cmp r3, r0
    beq pe_e1
pe_2:
    ldrh r3, [r1, #20]
    cmp r3, r0
    beq pe_e2
pe_3:
    ldrh r3, [r1, #28]
    cmp r3, r0
    beq pe_e3
pe_4:
    ldrh r3, [r1, #36]
    cmp r3, r0
    beq pe_e4
pe_next:
    adds r1, #40
    adds r4, #1
    cmp r4, r5
    bls pe_species
    movs r0, #0
    pop {r4, r5, pc}
pe_e0:                              @ the target matches: the method's low byte decides
    ldrb r3, [r1]
    cmp r3, #0xF9
    bls pe_found
    b pe_1
pe_e1:
    ldrb r3, [r1, #8]
    cmp r3, #0xF9
    bls pe_found
    b pe_2
pe_e2:
    ldrb r3, [r1, #16]
    cmp r3, #0xF9
    bls pe_found
    b pe_3
pe_e3:
    ldrb r3, [r1, #24]
    cmp r3, #0xF9
    bls pe_found
    b pe_4
pe_e4:
    movs r3, #32
    ldrb r3, [r1, r3]
    cmp r3, #0xF9
    bls pe_found
    b pe_next
pe_found:
    adds r0, r4, #0
    pop {r4, r5, pc}

call_r3:
    bx r3

PADA
.align 2
lit_struct:     .word 0x0203BC34
lit_menustate:  .word 0x0203BC38
lit_party:      .word 0x020244EC
lit_items:      .word 0x00000118
lit_items_id:   .word 0x0000011C
lit_showcount:  .word 0x00000111
lit_names:      .word 0x08000148
lit_getmondata: .word 0x0806A519
lit_strvar1:    .word 0x02021CC4
lit_copynick:   .word 0x08008B11
lit_cancel:     .word 0x085E8CF0
lit_loadlist:   .word 0x081D28C9
lit_levelup:    .word 0x0806E0B5
lit_eggspecies: .word 0x09F00601
lit_marker:     .word 20000
lit_end:        .word 0x0000FFFF
lit_eggtable:   .word 0x080703F0
lit_evoptr:     .word 0x0806D140
lit_last:       .word 0x0000057F
