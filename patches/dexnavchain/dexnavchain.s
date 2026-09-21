@ DexNav search and chain (Hyper Emerald v5.7).
@ On the DexNav screen a cursor picks a species and A starts tracking it. Back on the field a bar at the
@ top says what you are hunting, and the next wild Pokemon of that map is that species. Catching or
@ defeating it raises the chain, which shortens the odds on the next one: more shiny rerolls, a better
@ chance of perfect IVs (the stars on the bar) and of an egg move. Running, losing, or leaving the map
@ ends it. Nothing the game already does is rewritten - the Pokemon is still made by the hack's own
@ CreateWildMon, we only ask it for our species and level and reroll it, and the screen is still DexNav's.
.thumb

@ state block at STATE_ADDR:
@  +0  u16 magic     +2  u16 species   +4  u16 chain     +6  u8 level    +7  u8 ability slot
@  +8  u8  stars     +9  u8  flags     +10 u8 map group  +11 u8 map num  +12 u16 egg move
@  +14 u8  window    +15 u8  min lv    +16 u8 max lv     +17 u8 tick     +18 u8 icon sprite
@  +20 u32 window tile buffer
@ flags: bit0 = tracking, bit1 = the wild Pokemon just fought was one of ours

@ ---- overworld hook, chained in front of the one the earlier patches installed ----------------------
ow_stub:
    push {r4, r5}
    mov r4, lr                  @ the hook sits on CB2_Overworld's first instruction: lr is still live
    bl ow_tick
    mov lr, r4
    pop {r4, r5}
    ldr r3, litA_prevhook
    bx r3

@ ow_tick(): every overworld frame, so it stays a handful of compares unless something changed.
ow_tick:
    push {r4, r5, lr}
    ldr r4, litA_state
    ldrh r0, [r4]
    ldr r1, litA_magic
    cmp r0, r1
    beq ot_valid
    movs r0, #0                 @ RAM comes up as anything: stamp it and start clean
    movs r2, #0
ot_wipe:
    strb r0, [r4, r2]
    adds r2, #1
    cmp r2, #32
    blo ot_wipe
    strh r1, [r4]
    movs r0, #0xFF
    strb r0, [r4, #14]
    strb r0, [r4, #18]
    b ot_ret
ot_valid:
    ldrb r5, [r4, #9]
    movs r0, #2
    tst r0, r5
    beq ot_check
    bl after_battle
    ldrb r5, [r4, #9]
ot_check:
    movs r0, #1
    tst r0, r5
    bne ot_armed
    ldrb r0, [r4, #14]
    cmp r0, #0xFF
    beq ot_ret
    bl hud_remove
    b ot_ret
ot_armed:
    ldr r0, litA_sb1ptr
    ldr r0, [r0]
    ldrb r1, [r0, #4]
    ldrb r2, [r4, #10]
    cmp r1, r2
    bne ot_left
    ldrb r1, [r0, #5]
    ldrb r2, [r4, #11]
    cmp r1, r2
    beq ot_same
ot_left:                        @ off the hunting ground - a Pokemon Centre, say. The hunt is not lost,
    ldrb r0, [r4, #14]          @ it is only parked: the bar goes away and comes back, chain and all,
    cmp r0, #0xFF               @ when you walk back onto the map you were hunting on.
    beq ot_ret
    bl hud_remove
    b ot_ret
ot_same:
    ldr r0, litA_lock           @ a menu, a message, a Pokenav call or a script owns the screen
    ldrb r0, [r0]
    cmp r0, #0
    beq ot_free
    ldrb r0, [r4, #14]          @ take the bar down and hand back its window and memory until they are
    cmp r0, #0xFF               @ done, so nothing of ours is in the way of whatever they draw
    beq ot_ret
    bl hud_remove
    b ot_ret
ot_free:
    ldrb r0, [r4, #14]
    cmp r0, #0xFF
    bne ot_live
    bl hud_draw
    b ot_ret
ot_live:
    ldrb r0, [r4, #17]
    adds r0, #1
    strb r0, [r4, #17]
    movs r1, #15
    tst r0, r1
    bne ot_ret
    bl hud_refresh              @ something may have drawn over our tiles; put them back
ot_ret:
    pop {r4, r5, pc}

@ after_battle(): the battle we seeded has ended, and gBattleOutcome still holds how.
after_battle:
    push {r4, r5, lr}
    ldr r4, litA_state
    ldr r0, litA_outcome
    ldrb r0, [r0]
    cmp r0, #0                  @ zero while a battle is still being set up or fought: not ours to score yet
    beq ab_ret
    ldrb r5, [r4, #9]
    movs r1, #2
    bics r5, r1
    strb r5, [r4, #9]
    ldr r1, litA_enemyparty     @ whatever we just fought is still sitting in the enemy party
    ldrh r1, [r1, #0x20]
    ldrh r2, [r4, #2]
    cmp r1, r2                  @ a trainer, or something else that interrupted: it is not the hunt,
    bne ab_hud                  @ so it neither counts for the chain nor breaks it
    cmp r0, #1                  @ won
    beq ab_win
    cmp r0, #7                  @ caught
    beq ab_win
    movs r0, #0                 @ ran, lost, or it fled: the chain is over
    strh r0, [r4, #4]
    movs r0, #1
    bics r5, r0
    strb r5, [r4, #9]
    b ab_hud
ab_win:
    ldrh r0, [r4, #4]
    ldr r1, litA_999
    cmp r0, r1
    bhs ab_roll
    adds r0, #1
    strh r0, [r4, #4]
ab_roll:
    bl reroll                   @ decide the next one now, so the bar can show it
ab_hud:
    movs r0, #0xFF              @ the field went down with the battle: forget the window and the icon
    strb r0, [r4, #14]
    strb r0, [r4, #18]
ab_ret:
    pop {r4, r5, pc}

callr3:
    bx r3
callr4:
    bx r4
callr6:
    bx r6

.align 2
@ ---- pool A ----
litA_prevhook:      .word PREVHOOK_ADDR
litA_state:         .word STATE_ADDR
litA_magic:         .word 0x00004E44
litA_sb1ptr:        .word 0x03005D8C
litA_outcome:       .word 0x0202433A
litA_lock:          .word 0x03000F2C            @ the byte LockPlayerFieldControls sets
litA_enemyparty:    .word 0x02024744
litA_999:           .word 0x000003E7

@ ---- the DexNav screen, with a cursor and A to start tracking ---------------------------------------
@ dn_task(r0 = taskId): stands in for the DexNav task. The original still does everything we are not
@ changing - the fade, B to leave, L/R to page - so it runs first and we only add our part.
dn_task:
    push {r4, r5, r6, lr}
    sub sp, #4
    lsls r0, r0, #24
    lsrs r5, r0, #24
    adds r0, r5, #0
    ldr r3, litB_origtask
    bl callr3
    movs r0, #0x28
    muls r0, r5
    ldr r1, litB_gtasks
    adds r4, r0, r1
    ldrb r0, [r4, #4]           @ still alive? the original destroys it on the way out
    cmp r0, #0
    beq dt_ret
    adds r4, #8                 @ r4 = data[0]
    ldrh r0, [r4, #4]           @ data[2] = state, non-zero once it is leaving
    cmp r0, #0
    bne dt_ret
    ldr r0, litB_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    bne dt_ret
    ldrh r0, [r4]
    ldrh r1, [r4, #10]          @ data[5] = the page our cursor was drawn for, +1
    subs r1, #1
    cmp r0, r1
    beq dt_input
    adds r1, r0, #1
    strh r1, [r4, #10]
    movs r1, #0
    strh r1, [r4, #2]           @ data[1] = cursor row
    bl draw_cursor
    b dt_ret
dt_input:
    ldr r0, litB_gmain
    ldrh r6, [r0, #0x2E]        @ newKeys
    movs r0, #0x40              @ UP
    tst r0, r6
    bne dt_up
    movs r0, #0x80              @ DOWN
    tst r0, r6
    bne dt_down
    movs r0, #1                 @ A
    tst r0, r6
    bne dt_pick
    b dt_ret
dt_up:
    ldrh r0, [r4, #2]
    cmp r0, #0
    beq dt_ret
    subs r0, #1
    strh r0, [r4, #2]
    b dt_moved
dt_down:
    bl row_count
    subs r0, #1
    ldrh r1, [r4, #2]
    cmp r1, r0
    bhs dt_ret
    adds r1, #1
    strh r1, [r4, #2]
dt_moved:
    movs r0, #5
    ldr r3, litB_playse
    bl callr3
    ldrh r0, [r4]
    ldr r3, litB_drawpage
    bl callr3                   @ the screen's own page draw, then our cursor on top of it
    bl draw_cursor
    b dt_ret
dt_pick:
    bl cur_index
    ldr r3, litB_find
    bl callr3
    cmp r0, #0
    beq dt_ret
    ldr r1, litB_scratch
    ldrh r0, [r1]               @ species
    ldrb r2, [r1, #3]           @ top of its level range
    ldrb r1, [r1, #2]           @ bottom
    bl arm_search
    movs r0, #5
    ldr r3, litB_playse
    bl callr3
    movs r0, #1
    strh r0, [r4, #4]           @ state = leaving; the original task takes it from here
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #0
    movs r3, #16
    ldr r4, litB_beginfade
    bl callr4
dt_ret:
    add sp, #4
    pop {r4, r5, r6, pc}

@ cur_index(r4 = data) -> r0 = page*7 + cursor
cur_index:
    push {lr}
    ldrh r0, [r4]
    lsls r1, r0, #3
    subs r1, r1, r0
    ldrh r0, [r4, #2]
    adds r0, r0, r1
    pop {pc}

@ row_count(r4 = data) -> r0 = how many rows this page has (1..7)
row_count:
    push {r4, r5, lr}
    adds r5, r4, #0
    ldr r0, litB_ffff
    ldr r3, litB_find
    bl callr3                   @ r1 = entries on this map
    ldrh r0, [r5]
    lsls r2, r0, #3
    subs r2, r2, r0
    subs r1, r1, r2
    cmp r1, #7
    ble rc_clamp
    movs r1, #7
rc_clamp:
    adds r0, r1, #0
    cmp r0, #1
    bge rc_ret
    movs r0, #1
rc_ret:
    pop {r4, r5, pc}

@ draw_cursor(r4 = data): the arrow beside the selected row, just clear of the icon.
draw_cursor:
    push {r4, r5, lr}
    sub sp, #0x14
    ldrh r0, [r4, #2]
    movs r1, #20
    muls r0, r1
    adds r0, #2                 @ the rows sit at row*20 + 2
    adds r5, r0, #0
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    ldr r0, litB_colors_cur
    str r0, [sp, #8]
    movs r0, #0
    str r0, [sp, #0xC]
    ldr r0, litB_str_cursor
    str r0, [sp, #0x10]
    movs r0, #1                 @ the list window
    movs r1, #1                 @ font 1
    movs r2, #32
    adds r3, r5, #0
    ldr r4, litB_printer4
    bl callr4
    add sp, #0x14
    pop {r4, r5, pc}

@ arm_search(r0 = species, r1 = min level, r2 = max level)
arm_search:
    push {r4, r5, lr}
    ldr r4, litB_state
    ldrh r3, [r4, #2]
    cmp r3, r0
    beq as_keep
    movs r3, #0
    strh r3, [r4, #4]           @ another species means a fresh chain
as_keep:
    strh r0, [r4, #2]
    strb r1, [r4, #15]
    strb r2, [r4, #16]
    ldr r3, litB_sb1ptr
    ldr r3, [r3]
    ldrb r5, [r3, #4]
    strb r5, [r4, #10]
    ldrb r5, [r3, #5]
    strb r5, [r4, #11]
    ldrb r5, [r4, #9]
    movs r3, #1
    orrs r5, r3
    strb r5, [r4, #9]
    movs r3, #0xFF
    strb r3, [r4, #14]
    bl reroll
    pop {r4, r5, pc}

.align 2
@ ---- pool B ----
litB_origtask:      .word DN_TASK_ADDR
litB_drawpage:      .word DN_DRAWPAGE_ADDR
litB_find:          .word DN_FIND_ADDR
litB_scratch:       .word 0x02021DC4            @ gStringVar2, where the screen leaves the row it found
litB_gtasks:        .word 0x03005E00
litB_gmain:         .word 0x030022C0
litB_palfade:       .word 0x02037FD4
litB_playse:        .word 0x080A37A5
litB_beginfade:     .word 0x080A1AD5
litB_printer4:      .word 0x08199EED
litB_state:         .word STATE_ADDR
litB_sb1ptr:        .word 0x03005D8C
litB_ffff:          .word 0x0000FFFF
litB_colors_cur:    .word COLORS_CUR_ADDR
litB_str_cursor:    .word STR_CURSOR_ADDR

@ ---- what the next one will be ---------------------------------------------------------------------
@ reroll(): level, ability, stars and egg move for the next encounter. Everything the bar shows is settled
@ here, so what you read is what you will meet.
reroll:
    push {r4, r5, r6, lr}
    ldr r4, litC_state
    ldrb r0, [r4, #16]
    ldrb r1, [r4, #15]
    subs r0, r0, r1
    adds r0, #1
    bl rndmod
    ldrb r1, [r4, #15]
    adds r0, r0, r1             @ somewhere in the slot's own range
    ldrh r1, [r4, #4]
    lsrs r1, r1, #3             @ a mild push upward as the chain grows
    cmp r1, #5
    bls rr_lvadd
    movs r1, #5
rr_lvadd:
    adds r0, r0, r1
    cmp r0, #100
    bls rr_lvok
    movs r0, #100
rr_lvok:
    strb r0, [r4, #6]
    ldrh r0, [r4, #2]           @ ability: slot two only if the species really has a second one
    bl basestats
    ldrb r1, [r0, #22]
    ldrb r2, [r0, #23]
    cmp r2, #0
    beq rr_ab0
    cmp r2, r1
    beq rr_ab0
    movs r0, #2
    bl rndmod
    b rr_abset
rr_ab0:
    movs r0, #0
rr_abset:
    strb r0, [r4, #7]
    ldrh r0, [r4, #4]           @ stars: three means at least four 31s. Luck, never a promise.
    lsrs r0, r0, #1
    cmp r0, #14
    bls rr_t3
    movs r0, #14
rr_t3:
    adds r0, #1
    adds r5, r0, #0             @ per cent chance of three
    movs r0, #100
    bl rndmod
    cmp r0, r5
    blo rr_s3
    adds r1, r5, r5
    adds r1, r1, r5
    cmp r0, r1
    blo rr_s2
    lsls r1, r5, #2
    adds r1, r1, r5
    adds r1, r1, r5
    cmp r0, r1
    blo rr_s1
    movs r0, #0
    b rr_sset
rr_s3:
    movs r0, #3
    b rr_sset
rr_s2:
    movs r0, #2
    b rr_sset
rr_s1:
    movs r0, #1
rr_sset:
    strb r0, [r4, #8]
    movs r0, #0                 @ egg move: a quiet extra, up to three in five on a long chain
    strh r0, [r4, #12]
    ldrh r0, [r4, #4]
    adds r1, r0, r0
    adds r1, r1, r0
    cmp r1, #60
    bls rr_egch
    movs r1, #60
rr_egch:
    adds r5, r1, #0
    movs r0, #100
    bl rndmod
    cmp r0, r5
    bhs rr_ret
    ldrh r0, [r4, #2]
    bl eggpick
    strh r0, [r4, #12]
rr_ret:
    pop {r4, r5, r6, pc}

@ basestats(r0 = species) -> r0 = its 28-byte entry
basestats:
    push {lr}
    movs r1, #28
    muls r0, r1
    ldr r1, litC_basestats
    ldr r1, [r1]
    adds r0, r0, r1
    pop {pc}

@ eggpick(r0 = species) -> r0 = one of its egg moves, or 0
eggpick:
    push {r4, r5, r6, lr}
    ldr r1, litC_eggoff
    adds r5, r0, r1             @ the marker this species would have
    ldr r4, litC_eggtable
    ldr r6, litC_ffffC
ep_scan:
    ldrh r0, [r4]
    cmp r0, r6
    beq ep_none
    cmp r0, r5
    beq ep_found
    adds r4, #2
    b ep_scan
ep_found:
    adds r4, #2
    adds r5, r4, #0
    movs r1, #0
ep_count:
    ldrh r0, [r5]
    cmp r0, r6
    beq ep_take
    ldr r2, litC_eggoff
    cmp r0, r2
    bhi ep_take
    adds r1, #1
    adds r5, #2
    b ep_count
ep_take:
    cmp r1, #0
    beq ep_none
    adds r0, r1, #0
    bl rndmod
    lsls r0, r0, #1
    adds r0, r4, r0
    ldrh r0, [r0]
    b ep_ret
ep_none:
    movs r0, #0
ep_ret:
    pop {r4, r5, r6, pc}

@ rndmod(r0 = n) -> r0 = Random() % n
rndmod:
    push {r4, lr}
    adds r4, r0, #0
    cmp r4, #1
    bls rm_zero
    ldr r3, litC_random
    bl callr3
    lsls r0, r0, #16
    lsrs r0, r0, #16
    adds r1, r4, #0
    ldr r3, litC_umod
    bl callr3
    b rm_ret
rm_zero:
    movs r0, #0
rm_ret:
    pop {r4, pc}

.align 2
@ ---- pool C ----
litC_state:         .word STATE_ADDR
litC_basestats:     .word 0x080001BC            @ ROM header pointer to the base stats
litC_eggtable:      .word 0x09D78128
litC_eggoff:        .word 0x00004E20            @ the table marks a species as species + 20000
litC_ffffC:         .word 0x0000FFFF
litC_random:        .word 0x0806F5CD
litC_umod:          .word 0x082E7BE1

@ ---- the wild Pokemon itself -----------------------------------------------------------------------
@ wild_hook(r0 = species, r1 = level): sits in front of the hack's CreateWildMon. With a hunt on for this
@ map it asks for our species and level, reruns the whole thing for a shiny as often as the chain has
@ earned, and then writes in the IVs, ability and egg move that reroll() promised.
wild_hook:
    push {r4, r5, r6, r7, lr}
    adds r6, r0, #0
    adds r7, r1, #0
    ldr r4, litD_state
    ldrh r0, [r4]
    ldr r1, litD_magic
    cmp r0, r1
    bne wh_plain
    ldrb r0, [r4, #9]
    movs r1, #1
    tst r1, r0
    beq wh_plain
    ldr r0, litD_sb1ptr
    ldr r0, [r0]
    ldrb r1, [r0, #4]
    ldrb r2, [r4, #10]
    cmp r1, r2
    bne wh_plain
    ldrb r1, [r0, #5]
    ldrb r2, [r4, #11]
    cmp r1, r2
    bne wh_plain
    ldrh r6, [r4, #2]           @ ours instead
    ldrb r7, [r4, #6]
    ldrh r0, [r4, #4]
    lsrs r0, r0, #2             @ one more shiny roll per four links
    cmp r0, #11
    bls wh_rolls
    movs r0, #11
wh_rolls:
    adds r5, r0, #1
wh_try:
    adds r0, r6, #0
    adds r1, r7, #0
    ldr r3, litD_createwild
    bl callr3
    subs r5, #1
    cmp r5, #0
    beq wh_made
    bl is_shiny
    cmp r0, #0
    beq wh_try
wh_made:
    bl apply_extras
    ldr r0, litD_outcome        @ the last battle's result is still standing here until the engine clears
    movs r1, #0                 @ it; zero it now so the tick cannot score that one twice against this
    strb r1, [r0]               @ encounter while the battle is still coming up
    ldrb r0, [r4, #9]
    movs r1, #2
    orrs r0, r1
    strb r0, [r4, #9]           @ this battle is ours to score
    b wh_ret
wh_plain:
    adds r0, r6, #0
    adds r1, r7, #0
    ldr r3, litD_createwild
    bl callr3
wh_ret:
    pop {r4, r5, r6, r7, pc}

@ is_shiny() -> r0, by the game's own test, on the Pokemon just made
is_shiny:
    push {lr}
    ldr r2, litD_enemyparty
    ldr r1, [r2]
    ldr r0, [r2, #4]
    ldr r3, litD_isshiny
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    pop {pc}

@ apply_extras(): the 31s the stars stand for, the ability slot, the egg move, then stats to match.
apply_extras:
    push {r4, r5, r6, r7, lr}
    ldr r4, litD_state
    ldr r5, litD_enemyparty
    ldrb r6, [r4, #8]
    cmp r6, #0
    beq ae_ability
    adds r6, #1                 @ one star -> two 31s, two -> three, three -> four
    movs r0, #6
    bl rndmod
    adds r7, r0, #0             @ start somewhere, then walk: never the same stat twice
ae_iv:
    cmp r6, #0
    beq ae_ability
    adds r1, r7, r7
    adds r1, r1, r1
    adds r1, r1, r7             @ five bits per stat
    ldr r3, [r5, #0x48]
    movs r0, #31
    lsls r0, r1
    orrs r3, r0
    str r3, [r5, #0x48]
    adds r7, #1
    cmp r7, #6
    blo ae_next
    movs r7, #0
ae_next:
    subs r6, #1
    b ae_iv
ae_ability:
    ldr r3, [r5, #0x48]
    ldr r0, litD_abilitybit
    bics r3, r0
    ldrb r1, [r4, #7]
    cmp r1, #0
    beq ae_abstore
    orrs r3, r0
ae_abstore:
    str r3, [r5, #0x48]
    ldrh r0, [r4, #12]          @ the egg move goes in the fourth slot
    cmp r0, #0
    beq ae_stats
    strh r0, [r5, #0x32]
    movs r1, #12
    muls r0, r1
    ldr r1, litD_movetable
    adds r0, r0, r1
    ldrb r0, [r0, #4]           @ its PP
    movs r1, #0x37
    strb r0, [r5, r1]
ae_stats:
    adds r0, r5, #0
    ldr r3, litD_calcstats
    bl callr3
    pop {r4, r5, r6, r7, pc}

.align 2
@ ---- pool D ----
litD_state:         .word STATE_ADDR
litD_magic:         .word 0x00004E44
litD_sb1ptr:        .word 0x03005D8C
litD_createwild:    .word CREATEWILD_ADDR
litD_enemyparty:    .word 0x02024744
litD_isshiny:       .word 0x0806EBD1
litD_calcstats:     .word 0x08068D0D
litD_movetable:     .word 0x09D86419
litD_abilitybit:    .word 0x80000000
litD_outcome:       .word 0x0202433A

@ ---- the bar on the field --------------------------------------------------------------------------
hud_draw:
    push {r4, r5, r6, lr}
    sub sp, #0x14
    bl black_slot
    ldr r4, litE_state
    ldr r0, litE_wintemplate
    ldr r3, litE_addwindow
    bl callr3
    lsls r0, r0, #24
    lsrs r5, r0, #24
    cmp r5, #0xFF
    beq hd_ret
    strb r5, [r4, #14]
    movs r0, #12
    muls r0, r5
    ldr r1, litE_gwindows
    adds r0, r0, r1
    ldr r0, [r0, #8]
    str r0, [r4, #20]           @ remember the buffer, to tell later whether the window is still ours
    adds r0, r5, #0
    movs r1, #0xAA              @ solid black, from the spare slot we keep filled
    ldr r3, litE_fillwindow
    bl callr3
    bl hud_text
    bl icon_gone                @ never stack a second icon on top of one still standing
    ldrh r0, [r4, #2]           @ the species icon, over the left of the bar
    ldr r3, litE_loadiconpal
    bl callr3
    ldrh r0, [r4, #2]
    ldr r1, litE_iconcb
    movs r2, #24
    movs r3, #24
    movs r6, #0
    str r6, [sp]
    str r6, [sp, #4]
    movs r6, #1
    str r6, [sp, #8]
    ldr r6, litE_createmonicon
    bl callr6
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #64                 @ no free sprite: the bar simply goes without its icon
    bhs hd_ret
    strb r0, [r4, #18]
    movs r1, #0x44
    muls r0, r1
    ldr r1, litE_gsprites
    adds r0, r0, r1
    ldrb r1, [r0, #5]           @ priority 0, so it sits on top of the bar rather than behind it
    movs r2, #0xC
    bics r1, r2
    strb r1, [r0, #5]
hd_ret:
    add sp, #0x14
    pop {r4, r5, r6, pc}

@ hud_text(): both lines, out of the state block. It uses our own scratch rather than gStringVar4, since
@ a field message may well be on screen when the bar is redrawn.
hud_text:
    push {r4, r5, r6, r7, lr}
    ldr r4, litE_state
    ldrb r7, [r4, #14]
    ldr r5, litE_scratch
    ldrh r0, [r4, #2]
    movs r1, #11
    muls r0, r1
    ldr r1, litE_speciesnames
    ldr r1, [r1]
    adds r1, r0, r1
    adds r0, r5, #0
    bl scopy
    movs r1, #0xFF
    strb r1, [r0]
    ldr r3, litE_scratch
    movs r0, #62                @ icon, then the three star tiles, then the name
    movs r2, #1
    bl prnt
    ldr r5, litE_scratch        @ "Lv." and the level, on the same line
    adds r5, #40
    movs r0, #0xC6
    strb r0, [r5]
    movs r0, #0xEA
    strb r0, [r5, #1]
    movs r0, #0xAD
    strb r0, [r5, #2]
    adds r1, r5, #3
    ldrb r0, [r4, #6]
    bl dec3
    movs r1, #0xFF
    strb r1, [r0]
    ldr r3, litE_scratch
    adds r3, #40
    movs r0, #150
    movs r2, #1
    bl prnt
    ldr r5, litE_scratch        @ second line: the ability it will have
    adds r5, #64
    ldrh r0, [r4, #2]
    bl basestats
    ldrb r1, [r4, #7]
    adds r0, r0, r1
    ldrb r0, [r0, #22]
    movs r1, #13
    muls r0, r1
    ldr r1, litE_abilitynames
    adds r1, r0, r1
    adds r0, r5, #0
    bl scopy
    movs r1, #0xFF
    strb r1, [r0]
    ldr r3, litE_scratch
    adds r3, #64
    movs r0, #42
    movs r2, #17
    bl prnt
    ldr r5, litE_scratch        @ and the chain, which is what the hunt is about
    adds r5, #88
    movs r0, #0xC8
    strb r0, [r5]
    movs r0, #0xE3
    strb r0, [r5, #1]
    movs r0, #0xAD
    strb r0, [r5, #2]
    adds r1, r5, #3
    ldrh r0, [r4, #4]
    bl dec3
    movs r1, #0xFF
    strb r1, [r0]
    ldr r3, litE_scratch
    adds r3, #88
    movs r0, #150
    movs r2, #17
    bl prnt
    bl stars
    adds r0, r7, #0
    ldr r3, litE_putwindow
    bl callr3
    adds r0, r7, #0
    movs r1, #3
    ldr r3, litE_copywindow
    bl callr3
    pop {r4, r5, r6, r7, pc}

@ stars(): the rating, three tiles written straight into the window's own buffer. The font has no star,
@ so we carry the two 8x8 tiles ourselves - lit for earned, grey for not.
stars:
    push {r4, r5, r6, r7, lr}
    ldr r4, litE_state
    ldrb r0, [r4, #14]
    movs r1, #12
    muls r0, r1
    ldr r1, litE_gwindows
    adds r0, r0, r1
    ldr r5, [r0, #8]
    cmp r5, #0
    beq st_ret
    ldrb r6, [r4, #8]
    movs r7, #0
st_loop:
    cmp r7, #3
    bhs st_ret
    ldr r0, litE_startiles
    cmp r7, r6
    blo st_full
    adds r0, #32
st_full:
    adds r1, r7, #4             @ the icon covers the first four tiles; row 1 lines up with the name
    adds r1, #28
    lsls r1, r1, #5
    adds r1, r5, r1
    movs r2, #0
st_copy:
    ldrb r3, [r0, r2]
    strb r3, [r1, r2]
    adds r2, #1
    cmp r2, #32
    blo st_copy
    adds r7, #1
    b st_loop
st_ret:
    pop {r4, r5, r6, r7, pc}

@ black_slot(): the text palette has no black, but entries 10-12 are three identical spare whites.
@ We keep one of them black for the bar, and rewrite it on every draw because a new map reloads them.
black_slot:
    push {lr}
    ldr r0, litE_black
    movs r1, #250               @ palette 15, entry 10
    movs r2, #2
    ldr r3, litE_loadpalette
    bl callr3
    pop {pc}

@ prnt(r0 = x, r2 = y, r3 = string) into the bar
prnt:
    push {r4, r5, r6, lr}
    sub sp, #0x14
    adds r5, r0, #0
    adds r6, r2, #0
    ldr r0, litE_state
    ldrb r4, [r0, #14]
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    ldr r0, litE_colors_hud
    str r0, [sp, #8]
    movs r0, #0
    str r0, [sp, #0xC]
    str r3, [sp, #0x10]
    adds r0, r4, #0
    movs r1, #1
    adds r2, r5, #0
    adds r3, r6, #0
    ldr r4, litE_printer4B
    bl callr4
    add sp, #0x14
    pop {r4, r5, r6, pc}

@ scopy(r0 = dst, r1 = src) -> r0 = end of dst; stops at the terminator and never runs away
scopy:
    push {r4, lr}
    movs r4, #0
sc_loop:
    cmp r4, #16
    bhs sc_ret
    ldrb r2, [r1, r4]
    cmp r2, #0xFF
    beq sc_ret
    strb r2, [r0, r4]
    adds r4, #1
    b sc_loop
sc_ret:
    adds r0, r0, r4
    pop {r4, pc}

@ dec3(r0 = 0..999, r1 = dst) -> r0 = end
dec3:
    push {r4, r5, r6, lr}
    adds r4, r1, #0
    adds r5, r0, #0
    movs r6, #0
    movs r1, #100
    cmp r5, r1
    blo d3_tens
    movs r0, #0
d3_h:
    cmp r5, r1
    blo d3_hput
    subs r5, r5, r1
    adds r0, #1
    b d3_h
d3_hput:
    adds r0, #0xA1
    strb r0, [r4, r6]
    adds r6, #1
d3_tens:
    movs r1, #10
    cmp r6, #0
    bne d3_t
    cmp r5, r1
    blo d3_ones
d3_t:
    movs r0, #0
d3_tl:
    cmp r5, r1
    blo d3_tput
    subs r5, r5, r1
    adds r0, #1
    b d3_tl
d3_tput:
    adds r0, #0xA1
    strb r0, [r4, r6]
    adds r6, #1
d3_ones:
    adds r0, r5, #0
    adds r0, #0xA1
    strb r0, [r4, r6]
    adds r6, #1
    adds r0, r4, r6
    pop {r4, r5, r6, pc}

@ hud_live() -> r0 = 1 while the window at our id is still the one we made
hud_live:
    push {r4, lr}
    ldr r4, litE_state
    ldrb r0, [r4, #14]
    cmp r0, #0xFF
    beq hl_no
    movs r1, #12
    muls r0, r1
    ldr r1, litE_gwindows
    adds r0, r0, r1
    ldr r0, [r0, #8]
    cmp r0, #0
    beq hl_no
    ldr r1, [r4, #20]
    cmp r0, r1
    bne hl_no
    movs r0, #1
    b hl_ret
hl_no:
    movs r0, #0
hl_ret:
    pop {r4, pc}

hud_remove:
    push {r4, r5, lr}
    ldr r4, litE_state
    bl hud_live
    cmp r0, #0
    beq hr_forget
    ldrb r5, [r4, #14]
    adds r0, r5, #0
    movs r1, #1
    ldr r3, litE_clearstd
    bl callr3
    adds r0, r5, #0
    ldr r3, litE_removewindow
    bl callr3
hr_forget:
    movs r0, #0xFF
    strb r0, [r4, #14]
    bl icon_gone
    pop {r4, r5, pc}

@ icon_gone(): take our icon sprite down, but only if that slot is still the sprite we made.
icon_gone:
    push {r4, r5, lr}
    ldr r4, litE_state
    ldrb r0, [r4, #18]
    cmp r0, #64
    bhs ig_forget
    movs r1, #0x44
    muls r0, r1
    ldr r1, litE_gsprites
    adds r5, r0, r1
    ldr r0, [r5, #0x1C]
    ldr r1, litE_iconcb
    cmp r0, r1
    bne ig_forget
    adds r0, r5, #0
    ldr r3, litE_destroysprite
    bl callr3
    ldrh r0, [r4, #2]
    ldr r3, litE_freeiconpal
    bl callr3
ig_forget:
    movs r0, #0xFF
    strb r0, [r4, #18]
    pop {r4, r5, pc}

@ hud_refresh(): the tiles again in case something drew over them, or a fresh bar if the window is gone.
hud_refresh:
    push {r4, r5, lr}
    ldr r4, litE_state
    bl hud_live
    cmp r0, #0
    bne hf_put
    movs r0, #0xFF
    strb r0, [r4, #14]
    bl hud_draw
    b hf_ret
hf_put:
    bl black_slot
    ldrb r5, [r4, #14]
    adds r0, r5, #0
    ldr r3, litE_putwindow
    bl callr3
    adds r0, r5, #0
    movs r1, #3
    ldr r3, litE_copywindow
    bl callr3
hf_ret:
    pop {r4, r5, pc}

.align 2
@ ---- pool E ----
litE_state:         .word STATE_ADDR
litE_scratch:       .word SCRATCH_ADDR
litE_wintemplate:   .word WINTEMPLATE_ADDR
litE_colors_hud:    .word COLORS_HUD_ADDR
litE_startiles:     .word STARTILES_ADDR
litE_loadiconpal:   .word 0x080D2F29            @ LoadMonIconPalette, just this species' palette
litE_freeiconpal:   .word 0x080D2F69
litE_createmonicon: .word 0x080D2CC5
litE_iconcb:        .word 0x080D3015            @ SpriteCB_MonIcon
litE_gsprites:      .word 0x02020630
litE_black:         .word BLACK_ADDR
litE_loadpalette:   .word 0x080A1939
litE_destroysprite: .word 0x080070E9
litE_addwindow:     .word 0x08003381
litE_removewindow:  .word 0x08003575
litE_clearstd:      .word 0x08198071
litE_fillwindow:    .word 0x08003C49
litE_printer4B:     .word 0x08199EED
litE_putwindow:     .word 0x0800378D
litE_copywindow:    .word 0x08003659
litE_gwindows:      .word 0x02020004
litE_speciesnames:  .word 0x08000144
litE_abilitynames:  .word 0x09D03068
