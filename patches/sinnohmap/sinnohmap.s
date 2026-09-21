@ Sinnoh map screen (Hyper Emerald v5.7).
@ A screen of its own: it draws our Sinnoh picture on BG1 straight from free space, blinks a marker on the
@ area you are standing in and names it in a box. B goes back. Nothing the Hoenn region map or Fly use is
@ touched - not gRegionMapEntries, not its graphics, not its code.
@
@ Opened with the Town Map key item, which the hack already has but never made do anything. The start menu
@ could not take another line: its action list is exactly nine bytes and the game appends without checking,
@ so a tenth entry writes over the variable after it.
.thumb

@ ---- overworld hook --------------------------------------------------------------------------------
@ Chains ahead of the both-bikes stub: hands you the Town Map once, then lets that stub run as before.
@ NOTE: this hook is at a function's FIRST instruction, so lr still holds its live return address and the
@ prologue that saves it has not run yet. Our bl calls would destroy it, and the function would later
@ return into nowhere - so lr is kept in r4 and put back before chaining on.
ow_stub:
    push {r4, r5}
    mov r4, lr
    ldr r0, litA_townmap
    movs r1, #1
    ldr r3, litA_hasitem
    bl callr3
    lsls r0, r0, #24
    bne ow_done
    ldr r0, litA_townmap
    movs r1, #1
    ldr r3, litA_additem
    bl callr3
ow_done:
    mov lr, r4
    pop {r4, r5}
    ldr r3, litA_bikestub
    bx r3

@ ---- the item --------------------------------------------------------------------------------------
@ ItemUseOutOfBattle_SinnohMap(r0 = taskId): the shape the Pokeblock Case uses, which is how this game
@ opens a screen from an item - one path when the bag is up, another when it is used straight from the field.
item_use:
    push {r4, r5, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, litA_gtasksB
    adds r5, r1, r0
    bl cur_slot                 @ standing somewhere this map covers?
    cmp r0, #0
    beq iu_nomap
    movs r1, #0xE
    ldrsh r0, [r5, r1]          @ data[3]: 1 when used from the field
    cmp r0, #1
    beq iu_field
    ldr r0, litA_bagmenu
    ldr r1, [r0]
    ldr r0, litA_cb2_init
    str r0, [r1]                @ the bag opens our screen once it has faded out
    adds r0, r4, #0
    ldr r3, litA_closebag
    bl callr3
    pop {r4, r5, pc}
@ Nothing to show here. Exactly what the game's own key items do (the Coin Case is the model): expand the
@ text into gStringVar4 first and hand the message routine THAT buffer, not a pointer into the ROM. The
@ message then behaves like every other one, waiting on A or B instead of closing itself.
iu_nomap:
    ldr r0, litA_strvar4
    ldr r1, litA_str_nomap
    ldr r3, litA_expand
    bl callr3
    movs r1, #0xE
    ldrsh r0, [r5, r1]
    cmp r0, #1
    beq iu_nomap_field
    adds r0, r4, #0
    movs r1, #1
    ldr r2, litA_strvar4
    ldr r3, litA_bagmsgcb
    ldr r4, litA_bagmsg
    bl callr4
    pop {r4, r5, pc}
iu_nomap_field:
    adds r0, r4, #0
    ldr r1, litA_strvar4
    ldr r2, litA_fieldmsgcb
    ldr r3, litA_fieldmsg
    bl callr3
    pop {r4, r5, pc}

iu_field:
    ldr r0, litA_fieldcb
    ldr r1, litA_returnnoscript
    str r1, [r0]
    movs r0, #1
    movs r1, #0
    ldr r3, litA_fadescreen
    bl callr3
    ldr r0, litA_waittask
    str r0, [r5]                @ this task now waits for the fade
    pop {r4, r5, pc}

@ Task_OpenSinnohMapOnField(r0 = taskId)
wait_task:
    push {r4, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    ldr r0, litA_palfadeB
    ldrb r1, [r0, #7]
    movs r0, #0x80
    ands r0, r1
    cmp r0, #0
    bne wt_ret
    ldr r3, litA_cleanupfield
    bl callr3
    ldr r0, litA_cb2_init
    ldr r3, litA_setcb2
    bl callr3
    adds r0, r4, #0
    ldr r3, litA_destroytask
    bl callr3
wt_ret:
    pop {r4}
    pop {r0}
    bx r0

@ cur_slot -> r0 = address of the {mapsec, x, y} entry for where you are, or 0 when off the map
cur_slot:
    push {r4, r5, lr}
    ldr r3, litA_getmapsec
    bl callr3
    lsls r0, r0, #16
    lsrs r5, r0, #16
    ldr r4, litA_loctable
cs_loop:
    ldrb r0, [r4]
    cmp r0, #0xFF
    beq cs_none
    cmp r0, r5
    beq cs_found
    adds r4, #3
    b cs_loop
cs_none:
    movs r0, #0
    pop {r4, r5, pc}
cs_found:
    adds r0, r4, #0
    pop {r4, r5, pc}


.align 2
@ A second pool: Thumb pc-relative loads only reach 1020 bytes, and the screen code below
@ pushes the main pool out of range of everything up here.
litA_additem:         .word 0x080D6929
litA_bagmenu:         .word 0x0203CE54    @ gBagMenu -> newScreenCallback
litA_bagmsg:          .word 0x081ABB4D    @ message over the bag
litA_bagmsgcb:        .word 0x081ABBBD
litA_bikestub:        .word BIKE_STUB
litA_cb2_init:        .word CB2_INIT_ADDR
litA_cleanupfield:    .word 0x08085D35
litA_closebag:        .word 0x081AB8F9    @ Task_FadeAndCloseBagMenu
litA_destroytask:     .word 0x080A909D
litA_fadescreen:      .word 0x080ABCD1
litA_fieldcb:         .word 0x03005DAC    @ gFieldCallback
litA_fieldmsg:        .word 0x081978ED    @ message on the field
litA_fieldmsgcb:      .word 0x080FD1F9
litA_getmapsec:       .word 0x08085C59
litA_gtasksB:         .word 0x03005E00
litA_hasitem:         .word 0x080D6725
litA_loctable:        .word LOCTABLE_ADDR
litA_palfadeB:        .word 0x02037FD4
litA_returnnoscript:  .word 0x080AF6D5
litA_setcb2:          .word 0x08000541
litA_str_nomap:       .word STR_NOMAP_ADDR
litA_strvar4:         .word 0x02021FC4
litA_expand:          .word 0x08008EE1    @ StringExpandPlaceholders
litA_townmap:         .word 0x00000169    @ Town Map
litA_waittask:        .word WAIT_TASK_ADDR

@ ---- screen ----------------------------------------------------------------------------------------
cb2_init:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x14
    movs r0, #0
    ldr r3, litC_setvblank
    bl callr3
    movs r0, #0
    movs r1, #0
    ldr r3, litC_setgpureg
    bl callr3
    movs r0, #0
    ldr r3, litC_resetbgs
    bl callr3
    movs r0, #0
    ldr r1, litC_bgtemplates
    movs r2, #2
    ldr r3, litC_initbgs
    bl callr3
    movs r0, #0x80
    lsls r0, r0, #4             @ 0x800: tilemap buffer for the text background
    ldr r3, litC_alloczeroed
    bl callr3
    adds r7, r0, #0             @ kept until the end, to hand to the task
    movs r0, #0
    adds r1, r7, #0
    ldr r3, litC_setbgtilemap
    bl callr3
    ldr r3, litC_resetpalfade
    bl callr3
    ldr r3, litC_resetsprites
    bl callr3
    ldr r3, litC_freespritepals
    bl callr3
    ldr r3, litC_resettasks
    bl callr3
    ldr r3, litC_deactprinters
    bl callr3
    ldr r0, litC_wintemplates
    ldr r3, litC_initwindows
    bl callr3
    @ palettes: the map's ten, then the marker, then the text box
    ldr r0, litC_mappal
    movs r1, #0
    movs r2, #0xD0
    lsls r2, r2, #1             @ 416 bytes = palettes 0..12 for the map
    ldr r3, litC_loadpalette
    bl callr3
    ldr r0, litC_curpal
    movs r1, #0xD0              @ palette 13, clear of the map's
    movs r2, #0x20
    ldr r3, litC_loadpalette
    bl callr3
    ldr r0, litC_textpal
    movs r1, #0xF0              @ palette 15
    movs r2, #0x20
    ldr r3, litC_loadpalette
    bl callr3
    @ the map itself, decompressed straight into video memory
    ldr r0, litC_maptiles
    ldr r1, litC_vram_tiles
    ldr r3, litC_lz77vram
    bl callr3
    ldr r0, litC_maptilemap
    ldr r1, litC_vram_map
    ldr r3, litC_lz77vram
    bl callr3
    ldr r0, litC_curtile         @ the marker tile sits just past the map's own tiles
    ldr r1, litC_vram_cursor
    movs r2, #8
    bl copy_words
    movs r0, #0
    ldr r1, litC_dispcnt
    ldr r3, litC_setgpureg
    bl callr3
    movs r0, #0
    ldr r3, litC_showbg
    bl callr3
    movs r0, #1
    ldr r3, litC_showbg
    bl callr3
    @ nothing carries over from whatever screen we came from
    movs r0, #0x10
    movs r1, #0
    ldr r3, litC_setgpureg
    bl callr3
    movs r0, #0x12
    movs r1, #0
    ldr r3, litC_setgpureg
    bl callr3
    movs r0, #0x14
    movs r1, #0
    ldr r3, litC_setgpureg
    bl callr3
    movs r0, #0x16
    movs r1, #0
    ldr r3, litC_setgpureg
    bl callr3
    @ where the marker goes, and which name box would not sit on top of it
    bl cur_slot
    cmp r0, #0
    beq ci_nocursor
    ldrb r1, [r0, #1]           @ column
    ldrb r2, [r0, #2]           @ row
    lsls r0, r2, #5
    adds r1, r1, r0             @ cell = row * 32 + column
    cmp r2, #10
    bhs ci_boxtop
    movs r0, #1                 @ marker up north: box along the bottom
    b ci_havebox
ci_boxtop:
    movs r0, #0                 @ marker down south: box along the top
    b ci_havebox
ci_nocursor:
    ldr r1, litC_offscreen       @ park it outside the visible 30 x 20
    movs r0, #1
ci_havebox:
    str r1, [sp, #0x10]
    str r0, [sp, #0xC]
    @ task, with where the marker goes
    ldr r0, litC_task
    movs r1, #0
    ldr r3, litC_createtask
    bl callr3
    lsls r0, r0, #24
    lsrs r5, r0, #24
    bl task_data
    adds r6, r0, #0
    movs r0, #0
    strh r0, [r6]               @ data[0] = blink timer
    strh r0, [r6, #6]           @ data[3] = state
    ldr r1, [sp, #0x10]
    strh r1, [r6, #2]           @ data[1] = cell
    lsls r0, r1, #1
    ldr r2, litC_vram_map
    adds r0, r0, r2
    ldrh r0, [r0]
    strh r0, [r6, #4]           @ data[2] = what the map draws there normally
    strh r7, [r6, #8]           @ data[4..5] = the tilemap buffer, to free on the way out
    lsrs r0, r7, #16
    strh r0, [r6, #10]
    ldr r0, [sp, #0xC]
    strh r0, [r6, #12]          @ data[6] = which name box is on screen
    adds r4, r6, #0
    bl draw_name
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #16
    movs r3, #0
    ldr r4, litC_beginfade
    bl callr4
    ldr r0, litC_vblank
    ldr r3, litC_setvblank
    bl callr3
    ldr r0, litC_cb2_main
    ldr r3, litC_setcb2
    bl callr3
    add sp, #0x14
    pop {r4, r5, r6, r7, pc}


.align 2
@ Third pool. The screen setup is long enough that the main pool at the end is out of a
@ Thumb load's 1020-byte reach from up here.
litC_alloczeroed:     .word 0x08000B4D
litC_beginfade:       .word 0x080A1AD5
litC_bgtemplates:     .word BGTEMPLATES_ADDR
litC_cb2_main:        .word CB2_MAIN_ADDR
litC_createtask:      .word 0x080A8FB1
litC_curpal:          .word CURPAL_ADDR
litC_curtile:         .word CURTILE_ADDR
litC_deactprinters:   .word 0x080045B1
litC_dispcnt:         .word 0x00000040    @ 1D sprite mapping; ShowBg adds the background bits
litC_freespritepals:  .word 0x0800870D
litC_initbgs:         .word 0x080017E9
litC_initwindows:     .word 0x080031C1
litC_loadpalette:     .word 0x080A1939
litC_lz77vram:        .word 0x082E708D
litC_mappal:          .word MAPPAL_ADDR
litC_maptilemap:      .word MAPTILEMAP_ADDR
litC_maptiles:        .word MAPTILES_ADDR
litC_offscreen:       .word 0x000003FF
litC_resetbgs:        .word 0x080017BD
litC_resetpalfade:    .word 0x080A1A75
litC_resetsprites:    .word 0x08006975
litC_resettasks:      .word 0x080A8F51
litC_setbgtilemap:    .word 0x08002251
litC_setcb2:          .word 0x08000541
litC_setgpureg:       .word 0x080010B5
litC_setvblank:       .word 0x080006F1
litC_showbg:          .word 0x08001B31
litC_task:            .word TASK_ADDR
litC_textpal:         .word TEXTPAL_ADDR
litC_vblank:          .word VBLANK_ADDR
litC_vram_cursor:     .word CURSOR_VRAM
litC_vram_map:        .word 0x0600E000    @ BG1 screen base 28
litC_vram_tiles:      .word 0x06004000    @ BG1 character base 1
litC_wintemplates:    .word WINTEMPLATES_ADDR

cb2_main:
    push {lr}
    ldr r3, lit_runtasks
    bl callr3
    ldr r3, lit_animsprites
    bl callr3
    ldr r3, lit_buildoam
    bl callr3
    ldr r3, lit_dotilemapcopies
    bl callr3
    ldr r3, lit_updatepalfade
    bl callr3
    pop {pc}

vblank:
    push {lr}
    ldr r3, lit_loadoam
    bl callr3
    ldr r3, lit_spritecopies
    bl callr3
    ldr r3, lit_transferpltt
    bl callr3
    pop {pc}

@ task_data: r5 = task id -> r0 = &gTasks[r5].data[0]
task_data:
    lsls r1, r5, #2
    adds r1, r1, r5
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r0, r0, r1
    adds r0, #8
    bx lr

@ copy_words(r0 = src, r1 = dst, r2 = word count)
copy_words:
    push {r4}
cw_loop:
    cmp r2, #0
    beq cw_ret
    ldr r4, [r0]
    str r4, [r1]
    adds r0, #4
    adds r1, #4
    subs r2, #1
    b cw_loop
cw_ret:
    pop {r4}
    bx lr

@ Task_SinnohMap(r0 = taskId)
task:
    push {r4, r5, r6, lr}
    sub sp, #4
    lsls r0, r0, #24
    lsrs r5, r0, #24
    bl task_data
    adds r4, r0, #0
    @ blink the marker whatever else is going on
    ldrh r0, [r4]
    adds r0, #1
    strh r0, [r4]
    movs r1, #0x10
    tst r1, r0
    beq tk_off
    ldr r0, lit_cursor_entry
    b tk_write
tk_off:
    ldrh r0, [r4, #4]
tk_write:
    ldrh r1, [r4, #2]
    lsls r1, r1, #1
    ldr r2, lit_vram_map
    adds r1, r1, r2
    strh r0, [r1]
    ldr r0, lit_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    bne tk_ret                  @ fading: no input
    ldrh r0, [r4, #6]
    cmp r0, #0
    bne tk_leave
    ldr r0, lit_gmain
    ldrh r6, [r0, #0x30]        @ newAndRepeatedKeys, so holding a direction keeps going
    movs r7, #0
    movs r0, #0x10              @ RIGHT
    tst r0, r6
    beq tk_kleft
    movs r7, #1
tk_kleft:
    movs r0, #0x20
    tst r0, r6
    beq tk_kup
    movs r7, #2
tk_kup:
    movs r0, #0x40
    tst r0, r6
    beq tk_kdown
    movs r7, #3
tk_kdown:
    movs r0, #0x80
    tst r0, r6
    beq tk_move
    movs r7, #4
tk_move:
    cmp r7, #0
    beq tk_input
    adds r0, r7, #0
    ldrh r1, [r4, #2]
    bl snap                     @ r0 = the next place that way, or where we already are
    ldrh r1, [r4, #2]
    cmp r0, r1
    beq tk_input
    adds r7, r0, #0
    ldrh r0, [r4, #4]           @ put the old square back the way the map draws it
    lsls r2, r1, #1
    ldr r3, lit_vram_map
    adds r2, r2, r3
    strh r0, [r2]
    strh r7, [r4, #2]           @ and remember the new one
    lsls r0, r7, #1
    ldr r2, lit_vram_map
    adds r0, r0, r2
    ldrh r0, [r0]
    strh r0, [r4, #4]
    bl draw_name
    movs r0, #5                 @ SE_SELECT
    ldr r3, lit_playse
    bl callr3
tk_input:
    ldr r0, lit_gmain
    ldrh r6, [r0, #0x2E]        @ newKeys
    movs r0, #1                 @ A: fly there, if the courier would
    tst r0, r6
    beq tk_notA
    bl fly_target               @ r0 = the courier's script block for the marked town, or 0
    cmp r0, #0
    beq tk_ret
    ldr r1, lit_flyscratch
    str r0, [r1]
    movs r0, #5
    ldr r3, lit_playse
    bl callr3
    movs r0, #2
    strh r0, [r4, #6]           @ state = leaving, then flying
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #0
    movs r3, #16
    ldr r4, lit_beginfade
    bl callr4
    b tk_ret
tk_notA:
    movs r0, #2                 @ B
    tst r0, r6
    beq tk_ret
    movs r0, #5
    ldr r3, lit_playse
    bl callr3
    movs r0, #1
    strh r0, [r4, #6]           @ state = leaving
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #0
    movs r3, #16
    ldr r4, lit_beginfade
    bl callr4
    b tk_ret
tk_leave:
    ldr r3, lit_freewindows
    bl callr3
    ldrh r0, [r4, #8]
    ldrh r1, [r4, #10]
    lsls r1, r1, #16
    orrs r0, r1
    ldr r3, lit_free
    bl callr3
    ldrh r6, [r4, #6]           @ state 2 = flying: the field runs the courier's script on arrival
    adds r0, r5, #0
    ldr r3, lit_destroytask
    bl callr3
    cmp r6, #2
    bne tk_go
    ldr r0, lit_fieldcbB
    ldr r1, lit_flycb
    str r1, [r0]
tk_go:
    ldr r0, lit_returnfield     @ back to the field, honouring gFieldCallback
    ldr r3, lit_setcb2
    bl callr3
tk_ret:
    add sp, #4
    pop {r4, r5, r6, pc}

@ snap(r0 = direction 1 right / 2 left / 3 up / 4 down, r1 = cell) -> r0 = the nearest place that way.
@ Free tile-by-tile movement would spend most of its time over squares with no name, because we hold a
@ point per area rather than the per-tile section map the Hoenn map uses. Hopping between places keeps a
@ name on screen at every step, which is the whole point of moving the marker.
snap:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    str r1, [sp]                @ best so far = where we are
    movs r2, #0x7F
    lsls r2, r2, #8
    str r2, [sp, #4]            @ best score
    adds r7, r0, #0             @ direction
    movs r5, #31
    ands r5, r1                 @ column
    lsrs r6, r1, #5             @ row
    ldr r4, lit_loctableC
sn_loop:
    ldrb r0, [r4]
    cmp r0, #0xFF
    beq sn_done
    ldrb r2, [r4, #1]           @ x
    ldrb r3, [r4, #2]           @ y
    subs r0, r2, r5             @ dx
    subs r1, r3, r6             @ dy
    cmp r7, #1
    beq sn_right
    cmp r7, #2
    beq sn_left
    cmp r7, #3
    beq sn_up
    b sn_down
sn_right:
    cmp r0, #0
    ble sn_next
    b sn_scorex
sn_left:
    cmp r0, #0
    bge sn_next
    rsbs r0, r0, #0
    b sn_scorex
sn_up:
    cmp r1, #0
    bge sn_next
    rsbs r1, r1, #0
    b sn_scorey
sn_down:
    cmp r1, #0
    ble sn_next
    b sn_scorey
sn_scorex:                      @ along the press, then how far off the line
    cmp r1, #0
    bge sn_sx2
    rsbs r1, r1, #0
sn_sx2:
    lsls r0, r0, #2
    adds r0, r0, r1
    lsls r0, r0, #1
    adds r0, r0, r1             @ favour staying on the same row
    b sn_test
sn_scorey:
    cmp r0, #0
    bge sn_sy2
    rsbs r0, r0, #0
sn_sy2:
    lsls r1, r1, #2
    adds r1, r1, r0
    lsls r1, r1, #1
    adds r0, r1, r0
sn_test:
    ldr r1, [sp, #4]
    cmp r0, r1
    bhs sn_next
    str r0, [sp, #4]
    lsls r0, r3, #5
    adds r0, r0, r2
    str r0, [sp]
sn_next:
    adds r4, #3
    b sn_loop
sn_done:
    ldr r0, [sp]
    add sp, #8
    pop {r4, r5, r6, r7, pc}

@ courier_for(r0 = mapsec) -> r0 = the courier table entry {mapsec u8, pad, flag u16, block u32}, or 0
courier_for:
    push {r4, lr}
    ldr r4, lit_courier
cf_loop:
    ldrb r1, [r4]
    cmp r1, #0xFF
    beq cf_none
    cmp r1, r0
    beq cf_found
    adds r4, #8
    b cf_loop
cf_none:
    movs r0, #0
    pop {r4, pc}
cf_found:
    adds r0, r4, #0
    pop {r4, pc}

@ fly_target(r4 = task data) -> r0 = the courier's script block for the marked town when it would take
@ you there (its "visited" flag is set), else 0. Same flag, same block: nothing the courier would refuse.
fly_target:
    push {r4, r5, lr}
    ldrh r0, [r4, #2]
    movs r1, #31
    ands r1, r0
    lsrs r0, r0, #5
    adds r5, r0, #0
    adds r0, r1, #0
    adds r1, r5, #0
    bl slot_at
    cmp r0, #0
    beq ft_none
    ldrb r0, [r0]               @ mapsec
    bl courier_for
    cmp r0, #0
    beq ft_none
    adds r5, r0, #0
    ldrh r0, [r5, #2]           @ the town's visited flag
    ldr r3, lit_flagget
    bl callr3
    lsls r0, r0, #24
    beq ft_none
    ldr r0, [r5, #4]            @ its script block
    pop {r4, r5, pc}
ft_none:
    movs r0, #0
    pop {r4, r5, pc}

@ Runs on the field once we are back: let the normal no-script arrival happen, then a task waits for the
@ fade and starts the courier's block exactly as if you had just said yes to the courier.
fly_cb:
    push {lr}
    ldr r3, lit_returnnoscriptB
    bl callr3
    ldr r0, lit_flytask
    movs r1, #0
    ldr r3, lit_createtaskB
    bl callr3
    pop {pc}

fly_task:
    push {r4, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    ldr r0, lit_palfadeC
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    bne fl_ret
    ldr r0, lit_flyscratch
    ldr r0, [r0]
    ldr r3, lit_setupscript
    bl callr3                   @ ScriptContext1_SetupScript: also locks the player, as its callers expect
    adds r0, r4, #0
    ldr r3, lit_destroytaskB
    bl callr3
fl_ret:
    pop {r4}
    pop {r0}
    bx r0

@ slot_at(r0 = column, r1 = row) -> r0 = our {mapsec, x, y} entry there, or 0
slot_at:
    push {r4, r5, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    ldr r2, lit_loctableB
sa_loop:
    ldrb r0, [r2]
    cmp r0, #0xFF
    beq sa_none
    ldrb r0, [r2, #1]
    cmp r0, r4
    bne sa_next
    ldrb r0, [r2, #2]
    cmp r0, r5
    beq sa_found
sa_next:
    adds r2, #3
    b sa_loop
sa_none:
    movs r0, #0
    pop {r4, r5, pc}
sa_found:
    adds r0, r2, #0
    pop {r4, r5, pc}

@ draw_name(r4 = &gTasks[].data[0]): name whatever the marker is sitting on
draw_name:
    push {r4, r5, r6, lr}
    ldrh r5, [r4, #12]          @ window
    adds r0, r5, #0
    movs r1, #0x11
    ldr r3, lit_fillwindowB
    bl callr3
    ldrh r0, [r4, #2]
    movs r1, #31
    ands r1, r0
    lsrs r0, r0, #5
    adds r6, r0, #0
    adds r0, r1, #0
    adds r1, r6, #0
    bl slot_at
    cmp r0, #0
    beq dn_show                 @ nothing there: an empty box
    ldrb r6, [r0]               @ mapsec
    ldr r0, lit_strvar1B
    adds r1, r6, #0
    movs r2, #0
    ldr r3, lit_getmapnameB
    bl callr3
    ldr r4, lit_colors_normB
    adds r0, r6, #0
    bl courier_for
    cmp r0, #0
    beq dn_print                @ not a courier stop: plain name
    ldrh r0, [r0, #2]
    ldr r3, lit_flaggetB
    bl callr3
    lsls r0, r0, #24
    bne dn_print                @ visited: plain name
    ldr r4, lit_colors_dim      @ not yet: greyed, the courier would not take you
dn_print:
    adds r0, r5, #0
    movs r1, #4
    movs r2, #1
    ldr r3, lit_strvar1B
    bl print
dn_show:
    adds r0, r5, #0
    ldr r3, lit_putwindowB
    bl callr3
    adds r0, r5, #0
    movs r1, #3
    ldr r3, lit_copywindowB
    bl callr3
    pop {r4, r5, r6, pc}

@ print(r0 = window, r1 = x, r2 = y, r3 = string, r4 = colours)
print:
    push {r4, r5, lr}
    sub sp, #0x14
    movs r5, #0
    str r5, [sp]
    str r5, [sp, #4]
    str r4, [sp, #8]
    str r5, [sp, #0xC]
    str r3, [sp, #0x10]
    adds r3, r2, #0
    adds r2, r1, #0
    movs r1, #1
    ldr r4, lit_addtextprinter4
    bl callr4
    add sp, #0x14
    pop {r4, r5, pc}

callr3:
    bx r3
callr4:
    bx r4

.align 2
lit_palfade:         .word 0x02037FD4
lit_cleanupfield:    .word 0x08085D35
lit_setcb2:          .word 0x08000541
lit_setvblank:       .word 0x080006F1
lit_setgpureg:       .word 0x080010B5
lit_resetbgs:        .word 0x080017BD
lit_initbgs:         .word 0x080017E9
lit_alloczeroed:     .word 0x08000B4D
lit_free:            .word 0x08000B61
lit_setbgtilemap:    .word 0x08002251
lit_resetpalfade:    .word 0x080A1A75
lit_resetsprites:    .word 0x08006975
lit_freespritepals:  .word 0x0800870D
lit_resettasks:      .word 0x080A8F51
lit_deactprinters:   .word 0x080045B1
lit_initwindows:     .word 0x080031C1
lit_loadpalette:     .word 0x080A1939
lit_showbg:          .word 0x08001B31
lit_createtask:      .word 0x080A8FB1
lit_destroytask:     .word 0x080A909D
lit_beginfade:       .word 0x080A1AD5
lit_runtasks:        .word 0x080A910D
lit_animsprites:     .word 0x080069C1
lit_buildoam:        .word 0x08006A0D
lit_dotilemapcopies: .word 0x081999D1
lit_updatepalfade:   .word 0x080A1A1D
lit_loadoam:         .word 0x08007189
lit_spritecopies:    .word 0x0800742D
lit_transferpltt:    .word 0x080A19C1
lit_freewindows:     .word 0x08003605
lit_returnfield:     .word 0x080860C9
lit_playse:          .word 0x080A37A5
lit_fillwindow:      .word 0x08003C49
lit_putwindow:       .word 0x0800378D
lit_copywindow:      .word 0x08003659
lit_addtextprinter4: .word 0x08199EED
lit_getmapsec:       .word 0x08085C59
lit_getmapname:      .word 0x0812456D
lit_lz77vram:        .word 0x082E708D
lit_strvar1:         .word 0x02021CC4
lit_gtasks:          .word 0x03005E00
lit_gmain:           .word 0x030022C0
lit_dispcnt:         .word 0x00000040    @ 1D sprite mapping; ShowBg adds the background bits
lit_vram_tiles:      .word 0x06004000    @ BG1 character base 1
lit_vram_map:        .word 0x0600E000    @ BG1 screen base 28
lit_vram_cursor:     .word CURSOR_VRAM
lit_cursor_entry:    .word CURSOR_ENTRY
lit_offscreen:       .word 0x000003FF
lit_cb2_init:        .word CB2_INIT_ADDR
lit_cb2_main:        .word CB2_MAIN_ADDR
lit_vblank:          .word VBLANK_ADDR
lit_task:            .word TASK_ADDR
lit_bikestub:        .word BIKE_STUB
lit_townmap:         .word 0x00000169    @ Town Map
lit_hasitem:         .word 0x080D6725
lit_additem:         .word 0x080D6929
lit_gtasksB:         .word 0x03005E00
lit_bagmenu:         .word 0x0203CE54    @ gBagMenu -> newScreenCallback
lit_closebag:        .word 0x081AB8F9    @ Task_FadeAndCloseBagMenu
lit_fieldcb:         .word 0x03005DAC    @ gFieldCallback
lit_returnnoscript:  .word 0x080AF6D5
lit_fadescreen:      .word 0x080ABCD1
lit_palfadeB:        .word 0x02037FD4
lit_waittask:        .word WAIT_TASK_ADDR
lit_bagmsg:          .word 0x081ABB4D    @ message over the bag
lit_bagmsgcb:        .word 0x081ABBBD
lit_fieldmsg:        .word 0x081978ED    @ message on the field
lit_fieldmsgcb:      .word 0x080FD1F9
lit_str_nomap:       .word STR_NOMAP_ADDR
lit_bgtemplates:     .word BGTEMPLATES_ADDR
lit_wintemplates:    .word WINTEMPLATES_ADDR
lit_textpal:         .word TEXTPAL_ADDR
lit_mappal:          .word MAPPAL_ADDR
lit_curpal:          .word CURPAL_ADDR
lit_curtile:         .word CURTILE_ADDR
lit_maptiles:        .word MAPTILES_ADDR
lit_maptilemap:      .word MAPTILEMAP_ADDR
lit_loctable:        .word LOCTABLE_ADDR
lit_colors_norm:     .word COLORS_NORM_ADDR
lit_loctableB:       .word LOCTABLE_ADDR
lit_loctableC:       .word LOCTABLE_ADDR
lit_fillwindowB:     .word 0x08003C49
lit_putwindowB:      .word 0x0800378D
lit_copywindowB:     .word 0x08003659
lit_getmapnameB:     .word 0x0812456D
lit_strvar1B:        .word 0x02021CC4
lit_colors_normB:    .word COLORS_NORM_ADDR
lit_colors_dim:      .word COLORS_DIM_ADDR
lit_courier:         .word COURIER_ADDR
lit_flagget:         .word 0x0809D791
lit_flaggetB:        .word 0x0809D791
lit_flyscratch:      .word 0x02022F2C    @ tail of gDisplayedStringBattle: idle outside battle
lit_fieldcbB:        .word 0x03005DAC
lit_flycb:           .word FLY_CB_ADDR
lit_flytask:         .word FLY_TASK_ADDR
lit_returnnoscriptB: .word 0x080AF6D5
lit_createtaskB:     .word 0x080A8FB1
lit_destroytaskB:    .word 0x080A909D
lit_palfadeC:        .word 0x02037FD4
lit_setupscript:     .word 0x08098EF9    @ ScriptContext1_SetupScript
