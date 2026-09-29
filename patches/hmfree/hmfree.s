@ Field moves without a Pokemon that can learn them (Hyper Emerald v5.7).
@
@ OBSTACLES. The hack's field-move routine 0x08FF1BA0 (callasm'd by the Cut, Strength, Rock Smash, Surf,
@ Waterfall, Dive and Rock Climb scripts with the move in VAR_0x8004) returns in VAR_0x8004 the first party
@ Pokemon that can learn the move, or 6. An 8-byte trampoline at its entry sends it to fm_entry, which runs the
@ original unchanged (fm_orig replays the 8 bytes the trampoline covers) and only when it found nobody, and the
@ move is one of the eight HM moves, and that HM is in the Bag, answers with the first non-egg Pokemon instead.
@ Badges are not looked at here: the scripts and the field code check them before calling. The trampoline is
@ on the function's first instruction, so lr is live: fm_entry pushes it before any bl.
@
@ PARTY MENU. pm_hook is the first link in the field-action builder chain (trampoline at 0x081B3518, the CANCEL
@ append; then partyedit's hook, then the relearner's). It offers Fly (HM02 + badge 6) and, on a dark map that
@ Flash has not lit, Flash (HM05 + badge 2), each only when the list has room and does not already hold it.
@ Tail site: the caller's return address is already on the stack, so bl may clobber lr here.
.thumb

@ ============================================================================================ party menu
pm_hook:
    movs r0, #24                @ field-move action 0x13 + 5 = Fly
    ldr r1, lit_hm02
    ldr r2, lit_badge6
    bl offer
    ldr r0, lit_mapheader
    ldrb r0, [r0, #0x15]        @ gMapHeader.cave: 1 = dark until Flash
    cmp r0, #1
    bne pm_chain
    ldr r0, lit_flag_flash
    ldr r3, lit_flagget
    bl call3
    cmp r0, #0
    bne pm_chain                @ already lit
    movs r0, #20                @ field-move action 0x13 + 1 = Flash
    ldr r1, lit_hm05
    ldr r2, lit_badge2
    bl offer
pm_chain:
    ldr r3, lit_prev
    bx r3

@ offer(r0 = action, r1 = HM item, r2 = badge flag): append the action if there is room for it and CANCEL, it
@ is not in the list yet, the badge is set and the HM is in the Bag
offer:
    push {r4, r5, r6, r7, lr}
    adds r5, r0, #0
    adds r6, r1, #0
    adds r7, r2, #0
    ldr r4, lit_internal
    ldr r4, [r4]                @ sPartyMenuInternal
    ldrb r0, [r4, #0x17]        @ numActions
    cmp r0, #7
    bhs off_out
    movs r1, #0
off_scan:
    cmp r1, r0
    bhs off_new
    adds r2, r4, #0
    adds r2, #0xF               @ actions[]
    ldrb r2, [r2, r1]
    cmp r2, r5
    beq off_out                 @ it knows the move: the game listed it already
    adds r1, #1
    b off_scan
off_new:
    adds r0, r7, #0
    ldr r3, lit_flagget
    bl call3
    cmp r0, #0
    beq off_out
    adds r0, r6, #0
    movs r1, #1
    ldr r3, lit_checkbag
    bl call3
    cmp r0, #0
    beq off_out
    adds r0, r4, #0
    adds r0, #0xF
    adds r1, r4, #0
    adds r1, #0x17
    adds r2, r5, #0
    ldr r3, lit_append
    bl call3
off_out:
    pop {r4, r5, r6, r7}
    pop {r0}
    bx r0

@ ============================================================================================= obstacles
fm_entry:
    push {r4, lr}
    ldr r0, lit_var8004
    ldrh r4, [r0]               @ the move, before the original replaces it with a slot
    bl fm_orig
    ldr r0, lit_var8004
    ldrh r0, [r0]
    cmp r0, #6
    bne fm_out                  @ a Pokemon that can learn it: keep the hack's choice
    ldr r1, lit_hm_moves
    movs r2, #0
fm_find:
    lsls r3, r2, #1
    ldrh r3, [r1, r3]
    cmp r3, r4
    beq fm_found
    adds r2, #1
    cmp r2, #8
    blo fm_find
    b fm_out                    @ not an HM move (Rock Climb): unchanged
fm_found:
    ldr r0, lit_hm01
    adds r0, r0, r2             @ HM01 + index
    movs r1, #1
    ldr r3, lit_checkbag
    bl call3
    cmp r0, #0
    beq fm_out
    bl first_mon
    ldr r1, lit_var8004
    strh r0, [r1]
fm_out:
    pop {r4}
    pop {r0}
    bx r0

fm_orig:                        @ the 8 bytes under the trampoline, then on into the original at 0x08FF1BA8
    push {r4, r5, r6, r7, lr}
    ldr r5, lit_var8004
    ldrh r5, [r5]
    ldr r7, lit_movetable
    ldr r3, lit_resume
    bx r3

@ first_mon() -> r0 = the first party slot holding a Pokemon that is not an egg, or 6
first_mon:
    push {r4, r5, lr}
    movs r5, #0
fmn_loop:
    movs r0, #100
    muls r0, r5
    ldr r4, lit_party
    adds r4, r4, r0
    adds r0, r4, #0
    movs r1, #0xB               @ species
    movs r2, #0
    ldr r3, lit_getmondata
    bl call3
    cmp r0, #0
    beq fmn_none                @ the party ends here
    adds r0, r4, #0
    movs r1, #0x2D              @ isEgg
    movs r2, #0
    ldr r3, lit_getmondata
    bl call3
    cmp r0, #0
    beq fmn_done
    adds r5, #1
    cmp r5, #6
    blo fmn_loop
fmn_none:
    movs r5, #6
fmn_done:
    adds r0, r5, #0
    pop {r4, r5}
    pop {r1}
    bx r1

call3:
    bx r3

.align 2
lit_hm01:       .word 498
lit_hm02:       .word 499
lit_hm05:       .word 502
lit_badge2:     .word 0x868
lit_badge6:     .word 0x86C
lit_flag_flash: .word 0x888             @ FLAG_SYS_USE_FLASH
lit_mapheader:  .word 0x02037318        @ gMapHeader
lit_internal:   .word 0x0203CEC4        @ sPartyMenuInternal
lit_append:     .word 0x080A0945        @ AppendToList
lit_flagget:    .word 0x0809D791        @ FlagGet
lit_checkbag:   .word 0x080D6725        @ CheckBagHasItem
lit_getmondata: .word 0x0806A519
lit_party:      .word 0x020244EC
lit_var8004:    .word 0x020375E0
lit_movetable:  .word 0x09E0FE80        @ the hack's TM/HM move list, what 0x08FF1BA6 loads into r7
lit_resume:     .word 0x08FF1BA9
lit_prev:       .word PREV_ADDR
lit_hm_moves:   .word HM_MOVES_ADDR
