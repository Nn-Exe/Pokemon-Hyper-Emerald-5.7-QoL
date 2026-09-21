@ DexNav search and chain (Hyper Emerald v5.7), after Pokemon Unbound's DexNav.
@ On the DexNav screen a cursor picks a species and A starts tracking it. Back on the field a bar at the
@ bottom says what you are hunting, and the next wild Pokemon of that map is that species. Every one of
@ them you meet raises that species' Search Level (kept in flash, see sl_open), which sets the odds of an
@ egg move, a held item and perfect IVs (the stars on the bar) and adds shiny rolls. Catching or defeating
@ it raises the chain: +1 level per five links, and extra shiny rolls on the 50th and 100th. Running,
@ losing, or it fleeing ends the chain. Nothing the game already does is rewritten - the Pokemon is still
@ made by the hack's own CreateWildMon, we only ask it for our species and level and reroll it.
.thumb

@ state block at STATE_ADDR:
@  +0  u16 magic     +2  u16 species   +4  u16 chain     +6  u8 level    +7  u8 ability slot
@  +8  u8  stars (0-3; 4 = all six IVs perfect, drawn as three gold stars)     +9  u8  flags     +10 u8 map group  +11 u8 map num  +12 u16 egg move
@  +14 u8  window    +15 u8  min lv    +16 u8 max lv     +17 u8 tick     +18 u8 icon sprite
@  +20 u32 window tile buffer          +24 u16 search level of the species  +26 u16 held item
@  +28 u8 patch x   +29 u8 patch y (map coordinates + 7)   +30 u8 its field effect   +31 u8 shake pause
@ flags: bit0 = tracking, bit1 = the wild Pokemon just fought was one of ours, bit2 = the patch's encounter
@ is being made, bit3 = a patch is out, bits 4-5 = section (0 land, 1 water, 2 Rock Smash, 3 fishing),
@ bit6 = inside the per-step encounter check,
@ bit7 = just registered on the DexNav screen: go straight back to the field, not the start menu
@ The chain breaks the way it does in ORAS: run, lose, it flees, you leave the map, or you get into any
@ other battle (a trainer, a scripted Pokemon) while hunting.

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
    movs r0, #2                 @ a battle we did not seed has come and gone (gBattleResults names its foe,
    tst r0, r5                  @ and we zero that after every battle we score): the chain is over
    bne ot_nofoe
    ldr r0, litA_lastfoe
    ldrh r1, [r0]
    cmp r1, #0
    beq ot_nofoe
    movs r0, #0xFF              @ the field went down with that battle: forget the window and the icon
    strb r0, [r4, #14]
    strb r0, [r4, #18]
    bl chain_reset
    b ot_ret
ot_nofoe:
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
ot_left:                        @ off the hunting ground: as in ORAS, leaving the area ends the search
    bl chain_break
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
    bl patch_tick
    ldrb r0, [r4, #14]
    cmp r0, #0xFF
    bne ot_live
    bl hud_draw
    b ot_ret
ot_live:
    ldrb r0, [r4, #17]
    adds r0, #1
    strb r0, [r4, #17]
    movs r1, #3
    tst r0, r1
    bne ot_ret
    bl hud_arrow                @ where the patch is from here, every 4 frames as you move
    ldrb r0, [r4, #17]
    movs r1, #15
    tst r0, r1
    bne ot_ret
    bl hud_refresh              @ something may have drawn over our tiles; put them back
ot_ret:
    pop {r4, r5, pc}

@ after_battle(): the battle we seeded has ended, and gBattleOutcome still holds how.
after_battle:
    push {r4, r5, r6, lr}
    ldr r4, litA_state
    ldr r0, litA_outcome
    ldrb r6, [r0]
    cmp r6, #0                  @ zero while a battle is still being set up or fought: not ours to score yet
    beq ab_ret
    ldrb r5, [r4, #9]
    movs r1, #2
    bics r5, r1
    strb r5, [r4, #9]
    ldr r1, litA_lastfoe        @ gBattleResults.lastOpponentSpecies. Not the enemy party: a catch empties
    ldrh r1, [r1]               @ that before we get here, and the catch would go uncounted
    ldrh r2, [r4, #2]
    cmp r1, r2                  @ a trainer, or something else that got in first: a different battle,
    bne ab_break                @ which breaks the chain
    ldrh r0, [r4, #24]          @ met once more, whatever the outcome: the search level goes up, and to flash
    ldr r1, litA_999
    cmp r0, r1
    bhs ab_scored
    adds r1, r0, #1
    strh r1, [r4, #24]
    ldrh r0, [r4, #2]
    bl sl_set
ab_scored:
    cmp r6, #1                  @ won
    beq ab_win
    cmp r6, #7                  @ caught
    beq ab_win
ab_break:                       @ ran, lost, it fled, or another battle: the chain is over, the hunt goes on
    bl chain_reset
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
    ldrb r0, [r4, #9]           @ the patch was used up: a new one comes when the field is back
    movs r1, #0x0C
    bics r0, r1
    strb r0, [r4, #9]
    ldr r0, litA_lastfoe        @ scored: clear the foe so the tick can tell a battle that was not ours
    movs r1, #0
    strh r1, [r0]
    movs r0, #0xFF              @ the field went down with the battle: forget the window and the icon
    strb r0, [r4, #14]
    strb r0, [r4, #18]
ab_ret:
    pop {r4, r5, r6, pc}

@ chain_break(): leaving the map. Chain to 0, stop tracking, bar down. The search level stays.
chain_break:
    push {r4, lr}
    ldr r4, litA_state
    movs r0, #0
    strh r0, [r4, #4]
    ldrb r0, [r4, #9]
    movs r1, #0x0F              @ tracking, seeded, forced and the patch
    bics r0, r1
    strb r0, [r4, #9]
    ldr r0, litA_lastfoe
    movs r1, #0
    strh r1, [r0]
    ldrb r0, [r4, #14]
    cmp r0, #0xFF
    beq cb_ret
    bl hud_remove
cb_ret:
    pop {r4, pc}

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
litA_lastfoe:       .word 0x03005D30            @ gBattleResults (0x03005D10) + 0x20, cleared per battle
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
    bne dt_alive
    ldr r1, litB_state          @ it has just left for the start menu: after a registration, the field
    ldrb r0, [r1, #9]           @ instead, so the bar is the next thing you see
    movs r2, #0x80
    tst r0, r2
    beq dt_ret
    bics r0, r2
    strb r0, [r1, #9]
    ldr r0, litB_cb2return
    ldr r3, litB_setcb2
    bl callr3
    b dt_ret
dt_alive:
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
    bl draw_hint
    bl draw_levels
    movs r0, #0x99
    bl border
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
    movs r0, #0x11              @ only the border moves: the page, icons and all, stays as drawn
    bl border
    ldrh r0, [r4, #2]
    subs r0, #1
    strh r0, [r4, #2]
    b dt_moved
dt_down:
    bl row_count
    subs r0, #1
    ldrh r1, [r4, #2]
    cmp r1, r0
    bhs dt_ret
    movs r0, #0x11
    bl border
    ldrh r1, [r4, #2]
    adds r1, #1
    strh r1, [r4, #2]
dt_moved:
    movs r0, #5
    ldr r3, litB_playse
    bl callr3
    movs r0, #0x99
    bl border
    bl draw_hint
    b dt_ret
dt_pick:
    bl cur_index
    ldr r3, litB_find
    bl callr3
    cmp r0, #0
    beq dt_ret
    ldr r2, litB_state          @ A on the species already registered: unregister it
    ldrb r3, [r2, #9]
    movs r0, #1
    tst r3, r0
    beq dt_arm
    ldr r1, litB_scratch
    ldrh r0, [r1]
    ldrh r3, [r2, #2]
    cmp r0, r3
    bne dt_arm
    bl chain_break
    b dt_leave
dt_arm:
    ldr r1, litB_scratch
    ldrh r0, [r1]               @ species
    ldrb r3, [r1, #4]           @ section: land, water, Rock Smash, fishing
    ldrb r2, [r1, #3]           @ top of its level range
    ldrb r1, [r1, #2]           @ bottom
    bl arm_search
dt_leave:
    ldr r1, litB_state
    ldrb r0, [r1, #9]
    movs r2, #0x80
    orrs r0, r2
    strb r0, [r1, #9]
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

@ border(r4 = data, r0 = fill: 0x99 red, 0x11 the list's white): a 2-pixel frame around the selected row.
@ Rows are 20 pixels tall; the frame runs from just before the name (x 36) to the window's right edge, clear
@ of the icons, which can reach into the row above or below.
border:
    push {r4, r5, r6, lr}
    sub sp, #8
    adds r6, r0, #0
    ldr r0, litB_ffff           @ an empty map has no rows to frame
    ldr r3, litB_find
    bl callr3
    cmp r1, #0
    beq bd_ret
    ldr r0, litB_red            @ the screen's palette has no red: entry 9 of palette 15 is unused
    movs r1, #0xF9
    movs r2, #2
    ldr r3, litB_loadpalette
    bl callr3
    ldrh r0, [r4, #2]
    movs r1, #20
    muls r0, r1
    adds r5, r0, #0             @ top of the row
    movs r0, #2                 @ top edge
    str r0, [sp, #4]
    movs r0, #188
    str r0, [sp]
    movs r0, #1
    adds r1, r6, #0
    movs r2, #36
    adds r3, r5, #0
    ldr r4, litB_fillrect
    bl callr4
    movs r0, #2                 @ bottom edge
    str r0, [sp, #4]
    movs r0, #188
    str r0, [sp]
    movs r0, #1
    adds r1, r6, #0
    movs r2, #36
    adds r3, r5, #0
    adds r3, #18
    bl callr4
    movs r0, #20                @ left edge
    str r0, [sp, #4]
    movs r0, #2
    str r0, [sp]
    movs r0, #1
    adds r1, r6, #0
    movs r2, #36
    adds r3, r5, #0
    bl callr4
    movs r0, #20                @ right edge
    str r0, [sp, #4]
    movs r0, #2
    str r0, [sp]
    movs r0, #1
    adds r1, r6, #0
    movs r2, #222
    adds r3, r5, #0
    bl callr4
    movs r0, #1
    movs r1, #2                 @ the tiles only
    ldr r3, litB_copywindow
    bl callr3
bd_ret:
    add sp, #8
    pop {r4, r5, r6, pc}

@ draw_hint(r4 = data): "A: Register" in the header, where the page draw put the screen's title - or
@ "A: Unregister" when the cursor is on the species being hunted.
draw_hint:
    push {r4, r5, r6, lr}
    sub sp, #0x14
    ldr r5, litB_str_hint
    ldr r2, litB_state
    ldrb r3, [r2, #9]
    movs r0, #1
    tst r3, r0
    beq dh_draw
    bl cur_index
    ldr r3, litB_find
    bl callr3
    cmp r0, #0
    beq dh_draw
    ldr r1, litB_scratch
    ldrh r0, [r1]
    ldr r2, litB_state
    ldrh r3, [r2, #2]
    cmp r0, r3
    bne dh_draw
    ldr r5, litB_str_unreg
dh_draw:
    movs r0, #16                @ the header band again, all but the page number, and the place name back
    str r0, [sp, #4]            @ on it: the page draw's "DexNav" title is gone, and a long name no longer
    movs r0, #194               @ runs into the hint
    str r0, [sp]
    movs r0, #0
    movs r1, #0x44              @ the header band's colour
    movs r2, #0
    movs r3, #0
    ldr r4, litB_fillrect
    bl callr4
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    ldr r0, litB_colors_hint
    str r0, [sp, #8]
    movs r0, #0
    str r0, [sp, #0xC]
    ldr r0, litB_strvar1        @ the page draw left the place name here
    str r0, [sp, #0x10]
    movs r0, #0
    movs r1, #1
    movs r2, #6
    movs r3, #0
    ldr r4, litB_printer4
    bl callr4
    movs r0, #1                 @ the hint ends just short of the page number
    adds r1, r5, #0
    movs r2, #190
    ldr r3, litB_rightalign
    bl callr3
    adds r6, r0, #0
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    ldr r0, litB_colors_hint
    str r0, [sp, #8]
    movs r0, #0
    str r0, [sp, #0xC]
    str r5, [sp, #0x10]
    movs r0, #0
    movs r1, #1
    adds r2, r6, #0
    movs r3, #0
    ldr r4, litB_printer4
    bl callr4
    add sp, #0x14
    pop {r4, r5, r6, pc}

@ cb2_return(): CB2_ReturnToFieldWithOpenMenu without the start menu - the field comes back, fades in and
@ hands the controls back (FieldCB_ReturnToFieldNoScript).
cb2_return:
    push {lr}
    ldr r3, litB_clearvblank
    bl callr3
    ldr r0, litB_fieldcb
    ldr r1, litB_nomenu
    str r1, [r0]
    ldr r3, litB_returnfield
    bl callr3
    pop {pc}

@ arm_search(r0 = species, r1 = min level, r2 = max level)
arm_search:
    push {r4, r5, r6, lr}
    adds r6, r3, #0
    cmp r6, #3                  @ a fishing species is hunted like a water one: a ripple you surf onto,
    bne as_section              @ not a bite on the rod
    movs r6, #1
as_section:
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
    movs r3, #0x7E              @ a fresh start: no patch, nothing seeded, this section
    bics r5, r3
    movs r3, #1
    orrs r5, r3
    lsls r3, r6, #4
    orrs r5, r3
    strb r5, [r4, #9]
    movs r3, #0xFF
    strb r3, [r4, #14]
    ldr r0, litB_lastfoe        @ whatever was fought before this hunt began is not a break
    movs r1, #0
    strh r1, [r0]
    ldrh r0, [r4, #2]           @ what this species has earned so far, from flash
    bl sl_get
    strh r0, [r4, #24]
    bl reroll
    pop {r4, r5, r6, pc}

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
litB_lastfoe:       .word 0x03005D30
litB_sb1ptr:        .word 0x03005D8C
litB_ffff:          .word 0x0000FFFF
litB_colors_hint:   .word COLORS_HINT_ADDR
litB_str_hint:      .word STR_HINT_ADDR
litB_str_unreg:     .word STR_UNREG_ADDR
litB_strvar1:       .word 0x02021CC4            @ gStringVar1: the place name, from the page draw
litB_rightalign:    .word 0x081DB369            @ GetStringRightAlignXOffset(font, str, width)
litB_red:           .word RED_ADDR
litB_loadpalette:   .word 0x080A1939
litB_fillrect:      .word 0x08003B65            @ FillWindowPixelRect(win, fill, x, y, w, h)
litB_copywindow:    .word 0x08003659
litB_setcb2:        .word 0x08000541            @ SetMainCallback2
litB_cb2return:     .word CB2_RETURN_ADDR
litB_clearvblank:   .word 0x0808631D            @ FieldClearVBlankHBlankCallbacks
litB_fieldcb:       .word 0x03005DAC            @ gFieldCallback
litB_nomenu:        .word 0x080AF6D5            @ FieldCB_ReturnToFieldNoScript
litB_returnfield:   .word 0x080860C9            @ CB2_ReturnToField

@ ---- what the next one will be ---------------------------------------------------------------------
@ reroll(): level, ability, stars, egg move and held item for the next encounter. Everything the bar shows
@ is settled here, so what you read is what you will meet.
reroll:
    push {r4, r5, r6, lr}
    ldr r4, litC_state
    ldrb r0, [r4, #16]
    ldrb r1, [r4, #15]
    subs r0, r0, r1
    adds r0, #1
    bl rndmod
    ldrb r1, [r4, #15]
    adds r5, r0, r1             @ somewhere in the slot's own range
    ldrh r0, [r4, #4]           @ +1 per five links, back to +0 every hundred
rr_mod:
    cmp r0, #100
    blo rr_div
    subs r0, #100
    b rr_mod
rr_div:
    movs r1, #0
rr_div5:
    cmp r0, #5
    blo rr_lvadd
    subs r0, #5
    adds r1, #1
    b rr_div5
rr_lvadd:
    adds r0, r5, r1
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
    ldrh r0, [r4, #24]          @ the search level picks a row of Unbound's odds: 0-4, 5-9, 10-24, 25-49,
    ldr r1, litC_slbreaks       @ 50-99, 100+
    movs r6, #0
rr_bk:
    cmp r6, #5
    bhs rr_row
    ldrb r2, [r1, r6]
    cmp r0, r2
    blo rr_row
    adds r6, #1
    b rr_bk
rr_row:
    lsls r6, r6, #3
    ldr r1, litC_slodds
    adds r6, r6, r1             @ r6 = row: egg %, item %, then the chances of 3, 2 and 1 perfect IVs
    movs r0, #200               @ stars: how many IVs will be 31. Out of 200, so half Unbound's odds.
    bl rndmod
    ldrb r1, [r6, #2]
    movs r2, #3
    cmp r0, r1
    blo rr_sset
    ldrb r3, [r6, #3]
    adds r1, r1, r3
    movs r2, #2
    cmp r0, r1
    blo rr_sset
    ldrb r3, [r6, #4]
    adds r1, r1, r3
    movs r2, #1
    cmp r0, r1
    blo rr_sset
    movs r2, #0
rr_sset:
    ldrh r0, [r4, #4]           @ and the chain caps them: under 10 one star at most, under 20 two
    movs r1, #1
    cmp r0, #10
    blo rr_cap
    movs r1, #2
    cmp r0, #20
    blo rr_cap
    movs r1, #3
rr_cap:
    cmp r2, r1
    bls rr_capped
    adds r2, r1, #0
rr_capped:
    strb r2, [r4, #8]
    movs r0, #250               @ and one time in 500, whatever the level or chain: all six perfect
    lsls r0, r0, #1
    bl rndmod
    cmp r0, #0
    bne rr_nojackpot
    movs r0, #4
    strb r0, [r4, #8]
rr_nojackpot:
    movs r0, #0                 @ egg move
    strh r0, [r4, #12]
    movs r0, #100
    bl rndmod
    ldrb r1, [r6]
    cmp r0, r1
    bhs rr_item
    ldrh r0, [r4, #2]
    bl eggpick
    strh r0, [r4, #12]
rr_item:
    movs r0, #0                 @ held item, one of the two the species can carry in the wild
    strh r0, [r4, #26]
    movs r0, #100
    bl rndmod
    ldrb r1, [r6, #1]
    cmp r0, r1
    bhs rr_ret
    ldrh r0, [r4, #2]
    bl basestats
    ldrh r6, [r0, #12]          @ the common one
    ldrh r5, [r0, #14]          @ the rare one, one time in five when there are both
    cmp r5, #0
    beq rr_itset
    cmp r6, #0
    beq rr_itrare
    movs r0, #5
    bl rndmod
    cmp r0, #0
    bne rr_itset
rr_itrare:
    adds r6, r5, #0
rr_itset:
    strh r6, [r4, #26]
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
litC_slbreaks:      .word SLBREAKS_ADDR
litC_slodds:        .word SLODDS_ADDR

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
    ldrb r0, [r4, #9]           @ land and water: only the shaking patch's own encounter is ours
    movs r1, #4
    tst r1, r0
    bne wh_ours
    lsrs r0, r0, #4
    movs r1, #3
    ands r0, r1
    ldr r1, [sp, #16]           @ who asked: lr at entry, straight through the trampoline
    cmp r0, #3
    bne wh_rock
    ldr r2, litD_fishret        @ fishing: every bite
    cmp r1, r2
    bne wh_plain
    b wh_ours
wh_rock:
    cmp r0, #2
    bne wh_plain
    ldr r2, litD_trygenret      @ Rock Smash: TryGenerateWildMon, but not from a step in the grass
    cmp r1, r2
    bne wh_plain
    ldrb r0, [r4, #9]
    movs r1, #0x40
    tst r1, r0
    bne wh_plain
wh_ours:
    ldrh r6, [r4, #2]           @ ours instead
    ldrb r7, [r4, #6]
    ldrh r1, [r4, #24]          @ shiny rolls from the search level: 6 per level to 100, 2 per level to
    adds r0, r1, #0             @ 200, 1 per level beyond, /32 - 26 extra at 255, 49 at 999 (about 1.2%)
    cmp r0, #100                @ before the Shiny Charm, which the hack applies inside every roll
    bls wh_sl1
    movs r0, #100
wh_sl1:
    movs r2, #6
    muls r0, r2
    adds r5, r0, #0
    adds r0, r1, #0
    subs r0, #100
    ble wh_sl3
    cmp r0, #100
    bls wh_sl2
    movs r0, #100
wh_sl2:
    lsls r0, r0, #1
    adds r5, r5, r0
    adds r0, r1, #0
    subs r0, #200
    ble wh_sl3
    adds r5, r5, r0
wh_sl3:
    lsrs r5, r5, #5
    ldrh r0, [r4, #4]           @ and the 50th and 100th of a chain get a burst of their own
    adds r0, #1
    cmp r0, #50
    bne wh_c100
    adds r5, #5
wh_c100:
    cmp r0, #100
    bne wh_rolls
    adds r5, #10
wh_rolls:
    adds r5, #1
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

@ apply_extras(): the 31s the stars stand for, the ability slot, the egg move, the held item, then stats.
apply_extras:
    push {r4, r5, r6, r7, lr}
    ldr r4, litD_state
    ldr r5, litD_enemyparty
    ldrb r6, [r4, #8]           @ one 31 per star
    cmp r6, #0
    beq ae_ability
    cmp r6, #4                  @ the gold three: every one of the six
    bne ae_count
    movs r6, #6
ae_count:
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
    ldrh r0, [r4, #12]          @ the egg move replaces the first move, as in Unbound
    cmp r0, #0
    beq ae_item
    strh r0, [r5, #0x2C]
    movs r1, #12
    muls r0, r1
    ldr r1, litD_movetable
    adds r0, r0, r1
    ldrb r0, [r0, #4]           @ its PP
    movs r1, #0x34
    strb r0, [r5, r1]
ae_item:
    ldrh r0, [r4, #26]
    cmp r0, #0
    beq ae_stats
    strh r0, [r5, #0x22]        @ held item, right after the species
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
litD_fishret:       .word 0x080B504F            @ return into GenerateFishingWildMon
litD_trygenret:     .word 0x080B501B            @ return into TryGenerateWildMon

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
    bl hud_frame
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
    movs r3, #136               @ centre of the bar: tile rows 15-18, the bottom of the screen
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
    ldr r5, litE_scratch        @ and the species' search level. The printer draws at once, so the
    adds r5, #40                @ level's scratch is free again
    movs r0, #0xCD              @ "SL "
    strb r0, [r5]
    movs r0, #0xC6
    strb r0, [r5, #1]
    movs r0, #0
    strb r0, [r5, #2]
    adds r1, r5, #3
    ldrh r0, [r4, #24]
    bl dec3
    movs r1, #0xFF
    strb r1, [r0]
    ldr r3, litE_scratch
    adds r3, #40
    movs r0, #190
    movs r2, #17
    bl prnt
    bl hud_arrow
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
    cmp r6, #4                  @ all six perfect: three gold stars
    bne st_normal
    adds r0, #64
    b st_full
st_normal:
    cmp r7, r6
    blo st_full
    adds r0, #32
st_full:
    adds r1, r7, #4             @ the icon covers the first four tiles; row 1 lines up with the name
    adds r1, #28                @ the bar is 28 tiles wide
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
@ We keep one of them black for the bar and the next red for the stars, and rewrite them on every draw
@ because a new map reloads them.
black_slot:
    push {lr}
    ldr r0, litE_black
    movs r1, #250               @ palette 15, entries 10-12: the bar's black, the stars' red and gold
    movs r2, #6
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
@ hud_arrow(): one arrow, top right of the bar, for the way to the patch from where the player stands: left or
@ right until the player is in its column, then up or down. The font's own arrows. Blank without a patch.
hud_arrow:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    ldr r4, litE_state
    bl hud_live
    cmp r0, #0
    beq ha_ret
    movs r0, #16                @ clear the corner, in the bar's black
    str r0, [sp, #4]
    movs r0, #36
    str r0, [sp]
    ldrb r0, [r4, #14]
    movs r1, #0xAA
    movs r2, #188
    movs r3, #0
    ldr r5, litE_fillrect
    bl callr5
    ldr r5, litE_scratch
    adds r5, #40                @ the level's scratch: printed at once, so free
    adds r7, r5, #0
    ldrb r0, [r4, #9]
    movs r1, #8                 @ a patch out?
    tst r0, r1
    beq ha_end
    bl player_xy
    adds r6, r1, #0             @ player y
    ldrb r1, [r4, #28]
    subs r0, r1, r0             @ dx
    beq ha_vert
    movs r2, #0x7C              @ right arrow (movs sets the flags too: compare again before the sign test)
    cmp r0, #0
    bgt ha_hput
    rsbs r0, r0, #0
    movs r2, #0x7B              @ left arrow
ha_hput:
    strb r2, [r7]
    adds r7, #1
    b ha_end                    @ sideways first; up or down once lined up
ha_vert:
    ldrb r1, [r4, #29]
    subs r0, r1, r6             @ dy
    beq ha_end
    movs r2, #0x7A              @ down arrow
    cmp r0, #0
    bgt ha_vput
    rsbs r0, r0, #0
    movs r2, #0x79              @ up arrow
ha_vput:
    strb r2, [r7]
    adds r7, #1
ha_end:
    movs r0, #0xFF
    strb r0, [r7]
    cmp r7, r5
    beq ha_copy
    movs r0, #212               @ the bar's top right corner
    movs r2, #1
    adds r3, r5, #0
    bl prnt
ha_copy:
    ldrb r0, [r4, #14]
    movs r1, #2                 @ the tiles only
    ldr r3, litE_copywindow
    bl callr3
ha_ret:
    add sp, #8
    pop {r4, r5, r6, r7, pc}

callr5:
    bx r5

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
    bl hud_frame
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

@ hud_frame(): the menus' bold white frame (the Yes/No box's) around the bar, into BG0's tilemap buffer.
@ Called through the frame's own window function rather than DrawStdWindowFrame, which would also paint the
@ bar white. In this hack that function takes its tile and palette from two globals the Draw* wrappers fill
@ first, so we fill them the same way: the standard frame's tiles at 0x214, palette 14. (The message box's
@ own frame, 0x200/15, is this hack's translucent blue one and takes whatever palette 15 holds.)
hud_frame:
    push {lr}
    ldr r0, litE_frametile
    ldr r1, litE_0x214
    strh r1, [r0]
    movs r1, #14
    strb r1, [r0, #2]
    ldr r0, litE_state
    ldrb r0, [r0, #14]
    ldr r1, litE_dlgframe
    ldr r3, litE_callwinfunc
    bl callr3
    pop {pc}

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
litE_dlgframe:      .word 0x08197F19            @ WindowFunc_DrawStdFrame (DrawStdWindowFrame 0x08197E80)
litE_0x214:         .word 0x00000214
litE_callwinfunc:   .word 0x08004059            @ CallWindowFunction
litE_frametile:     .word 0x0203CD9C            @ u16 frame tile, then u8 palette at +2
litE_clearstd:      .word 0x08198071            @ ClearStdWindowAndFrame: window and its 1-tile frame
litE_fillwindow:    .word 0x08003C49
litE_printer4B:     .word 0x08199EED
litE_putwindow:     .word 0x0800378D
litE_copywindow:    .word 0x08003659
litE_fillrect:      .word 0x08003B65            @ FillWindowPixelRect
litE_gwindows:      .word 0x02020004
litE_speciesnames:  .word 0x08000144
litE_abilitynames:  .word 0x09D03068

@ ---- search levels, kept in flash ------------------------------------------------------------------
@ Flash sector 30 is the Trainer Hill's e-Reader sector: only an e-Reader card ever writes it, so on every
@ save seen here it is still blank. We keep {u16 species, u16 level} entries there, through the game's
@ own special-sector read and write (sentinel 0xB39D, staging in gSaveDataBuffer), so the main save
@ sectors are never touched. Byte 0 stays 0: the Trainer Hill reads it as its trainer count and rejects
@ anything outside 1-8, so it can never take our data for a hill. A sector holding someone else's data
@ (the sentinel but not our tag) is left alone: search levels then simply stay 0.
@ layout, from D = gSaveDataBuffer + 4:  +0 u8 0   +4 u32 tag   +8 entries, 1000 of them

@ sl_open() -> r0 = D with the sector in it, or 0 if the sector is not ours to use
sl_open:
    push {r4, lr}
    ldr r4, litF_d
    movs r0, #30
    adds r1, r4, #0             @ it copies the sector down onto D, which is where it already is
    ldr r3, litF_readspecial
    bl callr3
    cmp r0, #1
    bne so_blank                @ no sentinel: blank or garbage, and ours to set up
    ldr r0, [r4, #4]
    ldr r1, litF_tag
    cmp r0, r1
    bne so_foreign
    ldrb r0, [r4]
    cmp r0, #0
    bne so_foreign
    b so_ok
so_blank:
    movs r0, #0
    movs r2, #0
    ldr r3, litF_dsize
so_wipe:
    str r0, [r4, r2]
    adds r2, #4
    cmp r2, r3
    blo so_wipe
    ldr r1, litF_tag
    str r1, [r4, #4]
so_ok:
    adds r0, r4, #0
    pop {r4, pc}
so_foreign:
    movs r0, #0
    pop {r4, pc}

@ sl_slot(r0 = D, r1 = species, r2 = claim) -> r0 = its entry; with claim, a free one if it has none yet
sl_slot:
    push {r4, r5, r6, lr}
    adds r4, r0, #0
    adds r4, #8
    ldr r3, litF_entbytes
    adds r5, r4, r3
    movs r6, #0
ss_loop:
    cmp r4, r5
    bhs ss_end
    ldrh r3, [r4]
    cmp r3, r1
    beq ss_found
    cmp r3, #0
    bne ss_next
    cmp r6, #0
    bne ss_next
    adds r6, r4, #0
ss_next:
    adds r4, #4
    b ss_loop
ss_found:
    adds r0, r4, #0
    b ss_ret
ss_end:
    movs r0, #0
    cmp r2, #0
    beq ss_ret
    adds r0, r6, #0
    cmp r0, #0
    beq ss_ret
    strh r1, [r0]
    movs r3, #0
    strb r3, [r0, #2]
    strb r3, [r0, #3]
ss_ret:
    pop {r4, r5, r6, pc}

@ sl_get(r0 = species) -> r0 = its search level
sl_get:
    push {r4, lr}
    adds r4, r0, #0
    bl sl_open
    cmp r0, #0
    beq sg_ret
    adds r1, r4, #0
    movs r2, #0
    bl sl_slot
    cmp r0, #0
    beq sg_ret
    ldrh r0, [r0, #2]
sg_ret:
    pop {r4, pc}

@ sl_set(r0 = species, r1 = level): into the sector and straight back to flash
sl_set:
    push {r4, r5, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    bl sl_open
    cmp r0, #0
    beq sx_ret
    adds r1, r4, #0
    movs r2, #1
    bl sl_slot
    cmp r0, #0
    beq sx_ret
    strh r5, [r0, #2]
    movs r0, #30
    ldr r1, litF_d
    ldr r3, litF_writespecial
    bl callr3
sx_ret:
    pop {r4, r5, pc}

.align 2
@ ---- pool F ----
litF_d:             .word 0x0203ABC0            @ gSaveDataBuffer (0x0203ABBC) + 4
litF_readspecial:   .word 0x081535DD            @ TryReadSpecialSaveSector
litF_writespecial:  .word 0x08153635            @ TryWriteSpecialSaveSector
litF_tag:           .word 0x4C535844            @ "DXSL"
litF_dsize:         .word 0x00000FFC
litF_entbytes:      .word 4000                  @ 1000 entries: +8..+0xFA8, clear of the 0xFFC copied

@ ---- the shaking patch ------------------------------------------------------------------------------
@ Land and water hunts put a patch near the player: shaking grass, shaking long grass, a hole in the sand,
@ water surfacing or dust on a cave floor - vanilla's own field effects 19-22 and 10. Stepping onto it
@ starts the hunted battle; other tiles give the map's normal Pokemon, which, as in ORAS, is another battle
@ and resets the chain. Leave the patch off screen and the chain resets too; a new patch comes either way.

@ chain_reset(): chain to 0, patch gone, next one rerolled. The hunt itself goes on.
chain_reset:
    push {r4, lr}
    ldr r4, litG_state
    movs r0, #0
    strh r0, [r4, #4]
    ldrb r0, [r4, #9]
    movs r1, #0x0E              @ seeded, forced, patch
    bics r0, r1
    strb r0, [r4, #9]
    ldr r0, litG_lastfoe
    movs r1, #0
    strh r1, [r0]
    bl reroll
    pop {r4, pc}

@ player_xy() -> r0 = x, r1 = y: the player's tile, or the one being stepped onto (map coordinates + 7)
player_xy:
    push {lr}
    ldr r2, litG_avatar
    ldrb r2, [r2, #5]           @ gPlayerAvatar.objectEventId
    movs r3, #0x24
    muls r2, r3
    ldr r3, litG_objects
    adds r2, r2, r3
    ldrh r0, [r2, #0x10]        @ currentCoords
    ldrh r1, [r2, #0x12]
    pop {pc}

@ on_patch() -> r0 = 1 when the player has just stepped onto the patch of a live hunt
on_patch:
    push {r4, lr}
    ldr r4, litG_state
    ldrh r0, [r4]
    ldr r1, litG_magic
    cmp r0, r1
    bne op_no
    ldrb r0, [r4, #9]
    movs r1, #9                 @ tracking, with a patch out
    ands r0, r1
    cmp r0, #9
    bne op_no
    bl player_xy
    ldrb r2, [r4, #28]
    cmp r0, r2
    bne op_no
    ldrb r2, [r4, #29]
    cmp r1, r2
    bne op_no
    movs r0, #1
    pop {r4, pc}
op_no:
    movs r0, #0
    pop {r4, pc}

@ step_hook(r0 = the tile's behaviour): in front of the per-step encounter check (the hack's own, reached
@ through the trampoline at 0x0809CBE8). On the patch it starts the hunted battle itself - past Repel, as
@ the DexNav does. Anywhere else the check runs as ever, with bit6 up so wild_hook can tell a step in the
@ grass from Rock Smash. lr is live here: it is pushed, and the original is called, not jumped to.
step_hook:
    push {r4, r5, lr}
    adds r4, r0, #0
    bl on_patch
    cmp r0, #0
    bne sh_force
    ldr r5, litG_state
    ldrb r0, [r5, #9]
    movs r1, #0x40
    orrs r0, r1
    strb r0, [r5, #9]
    adds r0, r4, #0
    ldr r3, litG_prevstep
    bl callr3
    ldrb r1, [r5, #9]
    movs r2, #0x40
    bics r1, r2
    strb r1, [r5, #9]
    pop {r4, r5, pc}
sh_force:
    ldr r0, litG_immunity       @ what the check does after an encounter: no immunity steps, this tile
    movs r1, #0
    strb r1, [r0]
    strh r4, [r0, #2]
    bl force_battle
    movs r0, #1
    pop {r4, r5, pc}

@ force_battle(): make the hunted Pokemon through the CreateWildMon trampoline, so wild_hook dresses it,
@ and start the battle the way StandardWildEncounter does.
force_battle:
    push {r4, lr}
    ldr r4, litG_state
    ldrb r0, [r4, #9]
    movs r1, #4
    orrs r0, r1
    strb r0, [r4, #9]
    ldrh r0, [r4, #2]
    ldrb r1, [r4, #6]
    ldr r3, litG_createwild
    bl callr3
    ldrb r0, [r4, #9]
    movs r1, #0x0C              @ made, and the patch is used up
    bics r0, r1
    strb r0, [r4, #9]
    ldr r3, litG_startwild
    bl callr3
    pop {r4, pc}

@ patch_tick(): from the overworld tick, only while hunting on the hunt's map with the field free.
patch_tick:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    ldr r4, litG_state
    ldrb r0, [r4, #9]
    lsrs r0, r0, #4
    movs r1, #3
    ands r0, r1
    cmp r0, #2
    blo pt_go
    b pt_ret                    @ Rock Smash and fishing have no patch
pt_go:
    bl player_xy
    adds r6, r0, #0
    adds r7, r1, #0
    ldrb r0, [r4, #9]
    movs r1, #8
    tst r0, r1
    bne pt_have
    b pt_spawn
pt_have:
    ldrb r0, [r4, #28]          @ still on screen? 7 tiles either side, 5 up or down
    subs r0, r6, r0
    asrs r1, r0, #31
    eors r0, r1
    subs r0, r0, r1
    cmp r0, #7
    bhi pt_away
    ldrb r0, [r4, #29]
    subs r0, r7, r0
    asrs r1, r0, #31
    eors r0, r1
    subs r0, r0, r1
    cmp r0, #5
    bhi pt_away
    ldrb r0, [r4, #31]          @ a pause between shakes
    cmp r0, #0
    beq pt_shake
    subs r0, #1
    strb r0, [r4, #31]
    b pt_ret
pt_shake:                       @ on a timer, not the active list: standing in tall grass keeps the player's
    bl fx_args                  @ own rustle (the same effect) in that list the whole time. Every one of
    ldrb r0, [r4, #30]          @ these ends by itself once its animation has played.
    ldr r3, litG_fxstart
    bl callr3
    movs r0, #40
    strb r0, [r4, #31]
    b pt_ret
pt_away:                        @ walked off and left it: as in ORAS the search is over and the chain with
    bl chain_break              @ it. The patch does not follow you; register again from the DexNav.
    b pt_ret
pt_spawn:
    movs r5, #24                @ a few random tries a frame until one lands on the right kind of tile
ps_try:
    movs r0, #11
    bl rndmod
    subs r0, #5
    str r0, [sp]
    movs r0, #5                 @ 3 rows up to 1 down: below that the bar covers the screen
    bl rndmod
    subs r0, #3
    str r0, [sp, #4]
    ldr r0, [sp]                @ at least two steps away
    asrs r1, r0, #31
    eors r0, r1
    subs r0, r0, r1
    adds r2, r0, #0
    ldr r0, [sp, #4]
    asrs r1, r0, #31
    eors r0, r1
    subs r0, r0, r1
    adds r0, r0, r2
    cmp r0, #2
    blo ps_next
    ldr r0, [sp]
    adds r0, r6, r0
    cmp r0, #255
    bhi ps_next
    ldr r1, [sp, #4]
    adds r1, r7, r1
    cmp r1, #255
    bhi ps_next
    strb r0, [r4, #28]
    strb r1, [r4, #29]
    bl tile_ok                  @ somewhere the player could actually step
    cmp r0, #0
    beq ps_next
    ldrb r0, [r4, #28]
    ldrb r1, [r4, #29]
    ldr r3, litG_behaviorat
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    str r0, [sp]                @ the tile's behaviour
    ldrb r1, [r4, #9]
    movs r2, #0x10
    tst r1, r2
    beq ps_land
    ldr r3, litG_iswater
    bl callr3
    cmp r0, #0
    beq ps_next
    movs r0, #5                 @ a ripple, as a puddle makes (vanilla's water surfacing never ends here)
    b ps_found
ps_land:
    ldr r3, litG_island
    bl callr3
    cmp r0, #0
    beq ps_next
    ldr r0, [sp]
    ldr r3, litG_istall
    bl callr3
    movs r1, #4                 @ the grass rustle, drawn in this hack's own grass colours
    cmp r0, #0
    bne ps_fx
    ldr r0, [sp]
    ldr r3, litG_islong
    bl callr3
    movs r1, #17                @ the long grass rustle
    cmp r0, #0
    bne ps_fx
    ldr r0, [sp]
    ldr r3, litG_issand
    bl callr3
    movs r1, #10                @ sand: dust (vanilla's sand hole draws a blue box here and never ends)
    cmp r0, #0
    bne ps_fx
    movs r1, #10                @ anything else, a cave floor say: dust
ps_fx:
    adds r0, r1, #0
ps_found:
    strb r0, [r4, #30]
    movs r0, #0
    strb r0, [r4, #31]
    ldrb r0, [r4, #9]
    movs r1, #8
    orrs r0, r1
    strb r0, [r4, #9]
    ldrh r0, [r4, #2]           @ it announces itself: the hunted species' cry, centred
    movs r1, #0
    ldr r3, litG_cry
    bl callr3
    b pt_ret
ps_next:
    subs r5, #1
    bne ps_try
pt_ret:
    add sp, #8
    pop {r4, r5, r6, r7, pc}

@ fx_args(): gFieldEffectArguments for the patch. The grass rustles (4, 17) are the ones the game plays
@ under a walker, and keep checking that walker: we name the player, who is never on the patch, so each
@ plays once through and stops. The others take a subpriority in [2] instead.
fx_args:
    push {r4, r5, lr}
    ldr r4, litG_state
    ldr r5, litG_fxargs
    ldrb r0, [r4, #28]
    str r0, [r5]
    ldrb r0, [r4, #29]
    str r0, [r5, #4]
    movs r0, #2
    str r0, [r5, #12]           @ priority, level with the player
    movs r0, #0
    str r0, [r5, #28]           @ [7] play the whole animation
    movs r0, #0x80
    str r0, [r5, #8]            @ subpriority, for the others
    ldrb r0, [r4, #30]
    cmp r0, #5
    bne fa_notripple
    adds r0, r5, #0             @ the ripple wants screen pixels; the others convert map coordinates
    adds r1, r5, #4             @ themselves with this same call
    movs r2, #8
    movs r3, #12
    ldr r4, litG_mappos
    bl callr4
    movs r0, #151               @ as the game gives it under a walker
    str r0, [r5, #8]
    b fa_ret
fa_notripple:
    cmp r0, #4
    beq fa_grass
    cmp r0, #17
    bne fa_ret
fa_grass:
    ldr r2, litG_avatar
    ldrb r2, [r2, #5]
    movs r3, #0x24
    muls r2, r3
    ldr r3, litG_objects
    adds r2, r2, r3
    ldrb r0, [r2, #11]          @ [2] elevation
    movs r1, #15
    ands r0, r1
    str r0, [r5, #8]
    ldrb r0, [r2, #8]           @ [4] localId << 8 | mapNum, [5] mapGroup: the player
    lsls r0, r0, #8
    ldrb r1, [r2, #9]
    orrs r0, r1
    str r0, [r5, #16]
    ldrb r0, [r2, #10]
    str r0, [r5, #20]
    ldr r2, litG_sb1ptr         @ [6] mapNum << 8 | mapGroup of the map we are on
    ldr r2, [r2]
    ldrb r0, [r2, #5]
    lsls r0, r0, #8
    ldrb r1, [r2, #4]
    orrs r0, r1
    str r0, [r5, #24]
fa_ret:
    pop {r4, r5, pc}

@ tile_ok(r0 = x, r1 = y) -> r0 = 1 if the player could stand there: inside this map (not the strip a
@ connection or the border fills around it), passable, at the player's height (or a height-0/15 tile, which
@ joins levels), with no object on it - rocks and boulders are objects - and not ice or another tile that
@ slides you along. Cave floors pass the encounter test almost everywhere, which is why this is needed.
tile_ok:
    push {r4, r5, r6, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    ldr r2, litG_layout         @ gBackupMapLayout: width and height include 7 tiles each side (8 on the right)
    cmp r4, #7
    blt to_no
    ldr r3, [r2]
    subs r3, #8
    cmp r4, r3
    bge to_no
    cmp r5, #7
    blt to_no
    ldr r3, [r2, #4]
    subs r3, #7
    cmp r5, r3
    bge to_no
    adds r0, r4, #0
    adds r1, r5, #0
    ldr r3, litG_collision
    bl callr3
    cmp r0, #0
    bne to_no
    adds r0, r4, #0
    adds r1, r5, #0
    ldr r3, litG_elevation
    bl callr3
    cmp r0, #0
    beq to_level
    cmp r0, #15
    beq to_level
    adds r6, r0, #0
    ldr r2, litG_avatar
    ldrb r2, [r2, #5]
    movs r3, #0x24
    muls r2, r3
    ldr r3, litG_objects
    adds r2, r2, r3
    ldrb r0, [r2, #11]          @ the player's current elevation
    movs r1, #15
    ands r0, r1
    cmp r0, r6
    bne to_no
to_level:
    adds r0, r4, #0
    adds r1, r5, #0
    ldr r3, litG_objat
    bl callr3
    cmp r0, #16                 @ OBJECT_EVENTS_COUNT: nobody there
    bne to_no
    adds r0, r4, #0
    adds r1, r5, #0
    ldr r3, litG_behaviorat
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    ldr r3, litG_forced
    bl callr3
    cmp r0, #0
    bne to_no
    movs r0, #1
    pop {r4, r5, r6, pc}
to_no:
    movs r0, #0
    pop {r4, r5, r6, pc}

@ draw_levels(r4 = data): each row's Search Level, "SL n" between the name and the level range, in the small
@ font and the frame's red (entry 9, which border() loads); nothing where it is still 0. The flash sector is read once for the whole page.
draw_levels:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x18
    ldrh r0, [r4]
    lsls r5, r0, #3
    subs r5, r5, r0             @ page * 7
    bl sl_open
    str r0, [sp, #0x14]
    cmp r0, #0
    beq dl_ret
    movs r6, #0
dl_row:
    cmp r6, #7
    bhs dl_ret
    adds r0, r5, r6
    ldr r3, litG_find
    bl callr3
    cmp r0, #0
    beq dl_ret
    ldr r1, litG_rowscratch
    ldrh r1, [r1]               @ the row's species
    ldr r0, [sp, #0x14]
    movs r2, #0
    bl sl_slot
    cmp r0, #0
    beq dl_next
    ldrh r0, [r0, #2]
    cmp r0, #0
    beq dl_next
    ldr r7, litG_text
    movs r1, #0xCD              @ "SL "
    strb r1, [r7]
    movs r1, #0xC6
    strb r1, [r7, #1]
    movs r1, #0
    strb r1, [r7, #2]
    adds r1, r7, #3
    bl dec3
    movs r1, #0xFF
    strb r1, [r0]
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    ldr r0, litG_colors_list
    str r0, [sp, #8]
    movs r0, #0
    str r0, [sp, #0xC]
    str r7, [sp, #0x10]
    movs r0, #0                 @ right-aligned, ending just short of "Lv."
    adds r1, r7, #0
    movs r2, #133
    ldr r3, litG_rightalign
    bl callr3
    adds r2, r0, #0
    movs r0, #20
    muls r0, r6
    adds r3, r0, #4             @ level with the name, the small font sitting a little lower
    movs r0, #1                 @ the list window
    movs r1, #0                 @ the small font
    ldr r7, litG_printer4
    bl callr7
dl_next:
    adds r6, #1
    b dl_row
dl_ret:
    add sp, #0x18
    pop {r4, r5, r6, r7, pc}

callr7:
    bx r7

.align 2
@ ---- pool G ----
litG_state:         .word STATE_ADDR
litG_magic:         .word 0x00004E44
litG_lastfoe:       .word 0x03005D30
litG_avatar:        .word 0x02037590            @ gPlayerAvatar
litG_sb1ptr:        .word 0x03005D8C
litG_objects:       .word 0x02037350            @ gObjectEvents, 0x24 each
litG_prevstep:      .word PREVSTEP_ADDR         @ the hack's CheckStandardWildEncounter
litG_immunity:      .word 0x020375D4            @ sWildEncounterImmunitySteps, then sPrevMetatileBehavior
litG_createwild:    .word 0x080B4E69            @ CreateWildMon's trampoline, which leads to wild_hook
litG_startwild:     .word 0x080B0699            @ BattleSetup_StartWildBattle
litG_mappos:        .word 0x080930E1            @ SetSpritePosToOffsetMapCoords
litG_fxstart:       .word 0x080B5B19            @ FieldEffectStart
litG_fxargs:        .word 0x02038C08            @ gFieldEffectArguments: x, y, subpriority, priority
litG_behaviorat:    .word 0x080882BD            @ MapGridGetMetatileBehaviorAt
litG_iswater:       .word 0x08089559            @ MetatileBehavior_IsWaterWildEncounter
litG_island:        .word 0x0808952D            @ MetatileBehavior_IsLandWildEncounter
litG_istall:        .word 0x08089449            @ MetatileBehavior_IsTallGrass
litG_islong:        .word 0x0808945D            @ MetatileBehavior_IsLongGrass
litG_issand:        .word 0x08088E81            @ MetatileBehavior_IsSandOrDeepSand
litG_layout:        .word 0x03005DC0            @ gBackupMapLayout {width, height, map}
litG_collision:     .word 0x080881B1            @ MapGridGetCollisionAt
litG_elevation:     .word 0x08088145            @ MapGridGetElevationAt
litG_objat:         .word 0x0808D575            @ GetObjectEventIdByXY
litG_forced:        .word 0x0808904D            @ MetatileBehavior_IsForcedMovementTile (ice among them)
litG_cry:           .word 0x080A3275            @ PlayCry_Normal(species, pan)
litG_find:          .word DN_FIND_ADDR          @ the DexNav's own row lookup
litG_rowscratch:    .word 0x02021DC4            @ gStringVar2, where it leaves the row
litG_text:          .word SCRATCH_ADDR
litG_colors_list:   .word COLORS_LIST_ADDR
litG_printer4:      .word 0x08199EED            @ AddTextPrinterParameterized4
litG_rightalign:    .word 0x081DB369            @ GetStringRightAlignXOffset(font, str, width)
