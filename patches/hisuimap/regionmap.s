@ Region map screen (Hyper Emerald v5.7): the Sinnoh Map screen, made to show whichever region you are in.
@ Grown out of patches/sinnohmap/sinnohmap.s and replaces its screen: the Sinnoh Map item now opens this one.
@ Nothing the old screen drew is copied - its picture, location table and courier table stay where the
@ sinnohmap build put them (the leaguefly patch edits that courier table in place) and a region record
@ points at them. Hisui has a record of its own: its picture, its six places, Mingyao's Braviary blocks.
@
@ The one real difference between the regions is the key. In Sinnoh every area has its own map section, so
@ the tables are keyed by section, as before. In Hisui all six maps share section 104, so there they are keyed
@ by map number (37/103..108; the patch checks no other map uses that section).
@
@ Region record: +0 palettes, +4 tiles (LZ77), +8 tilemap (LZ77), +12 location table {key, x, y}...0xFF,
@ +16 fly table {key, pad, flag, script block}...0xFF (flag 0 = always), +20 names {key, pad[3], text}...0xFF
@ or 0 to name places by their map section, +24 a 30x20 grid: the key of the place each square belongs to, or
@ 0xFF (grid.py works it out from the picture).
@
@ The CURSOR moves freely, a square at a time (and on while a direction is held), as on the Hoenn map: a red box
@ sprite, the name box naming the place its square belongs to, A flying there when the courier would. The blinking
@ marker stays on where you are. Task data: [0] blink timer, [1] the marker's cell, [2] what the map draws there,
@ [3] state, [4..5] the text tilemap buffer, [6] the name box on screen (0 top, 1 bottom), [7] the cursor's cell
@ (row * 32 + column), [8] its sprite, [9] the place the name box shows, [10] frames to the next step while a
@ direction is held (a step on the press, 12 frames' pause, then one every 4 - the game's own key repeat waits 40).
.thumb

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
    bl cur_slot                 @ standing somewhere a map covers?
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

@ where -> r0 = the region record for where you are, r1 = the key its tables use here
where:
    push {r4, lr}
    ldr r3, litA_getmapsec
    bl callr3
    lsls r0, r0, #16
    lsrs r1, r0, #16
    cmp r1, #HISUI_SEC
    bne wh_sinnoh
    ldr r0, litA_sb1ptr
    ldr r0, [r0]
    ldrb r1, [r0, #5]           @ Hisui: the map number
    ldr r0, litA_hisui
    pop {r4, pc}
wh_sinnoh:
    ldr r0, litA_sinnoh
    pop {r4, pc}

@ cur_slot -> r0 = address of the {key, x, y} entry for where you are, or 0 when off the map
cur_slot:
    push {r4, r5, lr}
    bl where
    adds r5, r1, #0
    ldr r4, [r0, #12]
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
litA_bagmenu:         .word 0x0203CE54    @ gBagMenu -> newScreenCallback
litA_bagmsg:          .word 0x081ABB4D    @ message over the bag
litA_bagmsgcb:        .word 0x081ABBBD
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
litA_hisui:           .word REGION_HISUI_ADDR
litA_palfadeB:        .word 0x02037FD4
litA_returnnoscript:  .word 0x080AF6D5
litA_sb1ptr:          .word 0x03005D8C    @ gSaveBlock1Ptr: location.mapNum at +5
litA_setcb2:          .word 0x08000541
litA_sinnoh:          .word REGION_SINNOH_ADDR
litA_str_nomap:       .word STR_NOMAP_ADDR
litA_strvar4:         .word 0x02021FC4
litA_expand:          .word 0x08008EE1    @ StringExpandPlaceholders
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
    bl where
    adds r6, r0, #0             @ this region's record, until the picture is in
    @ palettes: the map's, then the marker, then the text box
    ldr r0, [r6, #0]
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
    ldr r0, litC_cursheet       @ the red box that moves over the map
    ldr r3, litC_loadsheet
    bl callr3
    ldr r0, litC_curspal
    ldr r3, litC_loadspritepal
    bl callr3
    @ the map itself, decompressed straight into video memory
    ldr r0, [r6, #4]
    ldr r1, litC_vram_tiles
    ldr r3, litC_lz77vram
    bl callr3
    ldr r0, [r6, #8]
    ldr r1, litC_vram_map
    ldr r3, litC_lz77vram
    bl callr3
    ldr r0, litC_curtile         @ the marker tile: the last one of the block, past either map's tiles
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
    ldr r0, [sp, #0x10]         @ the cursor starts on the marker, or mid-map when you are off it
    ldr r1, litC_offscreen
    cmp r0, r1
    bne ci_curset
    ldr r0, litC_midcell
ci_curset:
    strh r0, [r6, #14]          @ data[7] = the cursor's cell
    ldr r0, litC_curtpl
    movs r1, #0
    movs r2, #0
    movs r3, #0
    ldr r5, litC_createsprite
    bl callr5
    strh r0, [r6, #16]          @ data[8] = its sprite
    adds r4, r6, #0
    bl place_cursor
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
litC_dispcnt:         .word 0x00001040    @ sprites on, 1D mapping; ShowBg adds the background bits
litC_freespritepals:  .word 0x0800870D
litC_initbgs:         .word 0x080017E9
litC_initwindows:     .word 0x080031C1
litC_loadpalette:     .word 0x080A1939
litC_lz77vram:        .word 0x082E708D
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
litC_cursheet:        .word CURSHEET_ADDR
litC_curspal:         .word CURSPAL_ADDR
litC_curtpl:          .word CURTPL_ADDR
litC_loadsheet:       .word 0x080084F9    @ LoadSpriteSheet
litC_loadspritepal:   .word 0x08008745    @ LoadSpritePalette
litC_createsprite:    .word 0x08006DF5
litC_midcell:         .word 335           @ row 10, column 15

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

@ Task_RegionMap(r0 = taskId)
task:
    push {r4, r5, r6, r7, lr}
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
    ldrh r6, [r0, #0x2C]        @ heldKeys
    ldrh r1, [r0, #0x2E]        @ newKeys
    movs r0, #0xF0
    ands r6, r0                 @ the directions held
    beq tk_input
    ands r1, r0
    bne tk_first                @ just pressed: a step now, then a pause before it runs on
    ldrh r0, [r4, #20]          @ data[10]: frames to the next step while held
    subs r0, #1
    strh r0, [r4, #20]
    bgt tk_input
    movs r0, #4                 @ held: a square every 4 frames
    b tk_count
tk_first:
    movs r0, #12
tk_count:
    strh r0, [r4, #20]
    ldrh r0, [r4, #14]          @ data[7] = the cursor's cell
    movs r1, #31
    ands r1, r0                 @ column
    lsrs r2, r0, #5             @ row
    movs r0, #0x10              @ RIGHT
    tst r0, r6
    beq tk_kleft
    cmp r1, #29
    bhs tk_kleft
    adds r1, #1
tk_kleft:
    movs r0, #0x20              @ LEFT
    tst r0, r6
    beq tk_kup
    cmp r1, #0
    beq tk_kup
    subs r1, #1
tk_kup:
    movs r0, #0x40              @ UP
    tst r0, r6
    beq tk_kdown
    cmp r2, #0
    beq tk_kdown
    subs r2, #1
tk_kdown:
    movs r0, #0x80              @ DOWN
    tst r0, r6
    beq tk_move
    cmp r2, #19
    bhs tk_move
    adds r2, #1
tk_move:
    lsls r2, r2, #5
    adds r1, r1, r2             @ the new cell
    ldrh r0, [r4, #14]
    cmp r0, r1
    beq tk_input
    strh r1, [r4, #14]
    bl cursor_moved
tk_input:
    ldr r0, lit_gmain
    ldrh r6, [r0, #0x2E]        @ newKeys
    movs r0, #1                 @ A: fly there, if the courier would
    tst r0, r6
    beq tk_notA
    bl fly_target               @ r0 = the script block that takes you to the marked place, or 0
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
    ldrh r6, [r4, #6]           @ state 2 = flying: the field runs the fly script on arrival
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
    pop {r4, r5, r6, r7, pc}

@ courier_for(r0 = key) -> r0 = this region's fly entry {key u8, pad, flag u16, block u32}, or 0
courier_for:
    push {r4, r5, lr}
    adds r5, r0, #0
    bl where
    ldr r4, [r0, #16]
cf_loop:
    ldrb r1, [r4]
    cmp r1, #0xFF
    beq cf_none
    cmp r1, r5
    beq cf_found
    adds r4, #8
    b cf_loop
cf_none:
    movs r0, #0
    pop {r4, r5, pc}
cf_found:
    adds r0, r4, #0
    pop {r4, r5, pc}

@ fly_target(r4 = task data) -> r0 = the script block for the place under the cursor when it would take you there
@ (no flag, or its "visited" flag is set), else 0. Same flag, same block: nothing the courier would refuse.
fly_target:
    push {r4, r5, lr}
    ldrh r0, [r4, #14]          @ the cursor's square
    bl key_at
    cmp r0, #0xFF
    beq ft_none
    bl courier_for
    cmp r0, #0
    beq ft_none
    adds r5, r0, #0
    ldrh r0, [r5, #2]           @ the place's visited flag
    cmp r0, #0
    beq ft_go                   @ none: Mingyao takes you anywhere
    ldr r3, lit_flagget
    bl callr3
    lsls r0, r0, #24
    beq ft_none
ft_go:
    ldr r0, [r5, #4]            @ its script block
    pop {r4, r5, pc}
ft_none:
    movs r0, #0
    pop {r4, r5, pc}

@ Runs on the field once we are back: let the normal no-script arrival happen, then a task waits for the
@ fade and starts the fly block exactly as if you had just said yes to the courier.
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

@ key_at(r0 = cell) -> r0 = the key of the place that square belongs to in this region's grid, or 0xFF
key_at:
    push {r4, lr}
    movs r1, #31
    ands r1, r0                 @ column
    lsrs r0, r0, #5             @ row
    cmp r1, #30
    bhs ka_none
    cmp r0, #20
    bhs ka_none
    movs r2, #30
    muls r0, r2, r0
    adds r4, r0, r1
    bl where
    ldr r0, [r0, #24]           @ the grid, 30 x 20
    ldrb r0, [r0, r4]
    pop {r4, pc}
ka_none:
    movs r0, #0xFF
    pop {r4, pc}

@ cursor_moved(r4 = task data): the box on its new cell, the name box out of its way (top rows -> bottom box,
@ bottom rows -> top box), the name redrawn when the square belongs to another place
cursor_moved:
    push {r4, r5, lr}
    bl place_cursor
    ldrh r0, [r4, #14]
    lsrs r0, r0, #5             @ row
    ldrh r5, [r4, #12]          @ the box on screen: 0 top, 1 bottom
    cmp r5, #0
    bne cm_bottom
    cmp r0, #3
    bhs cm_name
    b cm_swap
cm_bottom:
    cmp r0, #16
    bls cm_name
cm_swap:
    adds r0, r5, #0
    ldr r3, lit_clearwintilemap
    bl callr3
    movs r0, #1
    eors r5, r0
    strh r5, [r4, #12]
    b cm_draw
cm_name:
    ldrh r0, [r4, #14]
    bl key_at
    ldrh r1, [r4, #18]          @ data[9] = the place the box shows
    cmp r0, r1
    beq cm_ret
cm_draw:
    bl draw_name
cm_ret:
    pop {r4, r5, pc}

@ place_cursor(r4 = task data): the box sprite centred on the cursor's 8x8 square
place_cursor:
    ldrh r0, [r4, #16]          @ data[8] = the sprite
    cmp r0, #64
    bhs pc_ret
    movs r1, #0x44
    muls r0, r1, r0
    ldr r1, lit_gsprites
    adds r0, r0, r1
    ldrh r1, [r4, #14]
    movs r2, #31
    ands r2, r1
    lsls r2, r2, #3
    adds r2, #4
    strh r2, [r0, #0x20]
    lsrs r1, r1, #5
    lsls r1, r1, #3
    adds r1, #4
    strh r1, [r0, #0x22]
pc_ret:
    bx lr

@ draw_name(r4 = &gTasks[].data[0]): name the place the cursor's square belongs to
draw_name:
    push {r4, r5, r6, r7, lr}
    ldrh r5, [r4, #12]          @ window
    adds r0, r5, #0
    movs r1, #0x11
    ldr r3, lit_fillwindowB
    bl callr3
    ldrh r0, [r4, #14]          @ the cursor's square
    bl key_at
    strh r0, [r4, #18]          @ data[9]: the place the box shows now
    cmp r0, #0xFF
    beq dn_show                 @ nothing there: an empty box
    adds r6, r0, #0             @ key
    bl where
    ldr r7, [r0, #20]           @ the region's own names, if it has them
    cmp r7, #0
    bne dn_named
    ldr r0, lit_strvar1B        @ none: the map section's name
    adds r1, r6, #0
    movs r2, #0
    ldr r3, lit_getmapnameB
    bl callr3
    ldr r7, lit_strvar1B
    b dn_colour
dn_named:
    ldrb r0, [r7]
    cmp r0, #0xFF
    beq dn_show
    cmp r0, r6
    beq dn_namefound
    adds r7, #8
    b dn_named
dn_namefound:
    ldr r7, [r7, #4]
dn_colour:
    ldr r4, lit_colors_normB
    adds r0, r6, #0
    bl courier_for
    cmp r0, #0
    beq dn_print                @ not a fly stop: plain name
    ldrh r0, [r0, #2]
    cmp r0, #0
    beq dn_print                @ no flag to earn: plain name
    ldr r3, lit_flaggetB
    bl callr3
    lsls r0, r0, #24
    bne dn_print                @ visited: plain name
    ldr r4, lit_colors_dim      @ not yet: greyed, the courier would not take you
dn_print:
    adds r0, r5, #0
    movs r1, #4
    movs r2, #1
    adds r3, r7, #0
    bl print
dn_show:
    adds r0, r5, #0
    ldr r3, lit_putwindowB
    bl callr3
    adds r0, r5, #0
    movs r1, #3
    ldr r3, lit_copywindowB
    bl callr3
    pop {r4, r5, r6, r7, pc}

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
callr5:
    bx r5

.align 2
lit_palfade:         .word 0x02037FD4
lit_setcb2:          .word 0x08000541
lit_free:            .word 0x08000B61
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
lit_addtextprinter4: .word 0x08199EED
lit_gtasks:          .word 0x03005E00
lit_gmain:           .word 0x030022C0
lit_vram_map:        .word 0x0600E000    @ BG1 screen base 28
lit_cursor_entry:    .word CURSOR_ENTRY
lit_fillwindowB:     .word 0x08003C49
lit_putwindowB:      .word 0x0800378D
lit_copywindowB:     .word 0x08003659
lit_getmapnameB:     .word 0x0812456D
lit_strvar1B:        .word 0x02021CC4
lit_colors_normB:    .word COLORS_NORM_ADDR
lit_colors_dim:      .word COLORS_DIM_ADDR
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
lit_gsprites:        .word 0x02020630
lit_clearwintilemap: .word 0x080038A5    @ ClearWindowTilemap
lit_setupscript:     .word 0x08098EF9    @ ScriptContext1_SetupScript
