@ DexNav screen, redrawn after Pokemon Unbound's (Hyper Emerald v5.7).
@ Two screens: 0 = Water (5) over Land (6x2), 1 = Rock Smash (5) over Fishing (5x2); L/R switch, the D-pad
@ moves a red ring between the Pokemon, A searches (or stops the search on the one being hunted), B leaves.
@ The right-hand panel shows the Pokemon under the ring: name, type labels, Search Level, level range, chain.
@ Layers: BG1 = the art (tiles + one of two tilemaps, patches/dexnavui/art.py), BG0 = one full-screen window
@ for every word, number and the X of an empty slot (transparent elsewhere), sprites = the icons, the ring and
@ the two type labels (the summary screen's sheet and palettes). The data - which Pokemon live here, what
@ registering does - is the old DexNav's: find (the map's own encounter header, dexnavscan), arm_search /
@ chain_break (dexnavchain), sl_get (the Search Level in flash); leaving works like the old screen: to the
@ field when state bit 7 is set (opened with R, or a search was just started or stopped), else to the start menu.
@
@ ui block (AllocZeroed, freed on the way out; its address in the task's data[0..1]):
@  +0 u32 BG0 tilemap buffer   +4 u8 screen   +5 u8 row   +6 u8 col   +7 u8 has a cursor
@  +8 u8 ring sprite   +9 u8 type sprite 1   +10 u8 type sprite 2   +11 u8 the shadow palette's slot
@  +12 u8 count[4] (land, water, rock, fish)   +16 entries {u16 species, u8 min, u8 max}: land 12 at +16,
@  water 5 at +64, rock 5 at +84, fish 10 at +104   +144 text[64]
@ rows: 0 = the top box (5 cells), 1 and 2 = the bottom box (6 or 5 cells each)
.thumb

@ ================================================================ the CB2 the DexNav's menu callback sets
ui_init:
    push {r4, r5, r6, lr}
    sub sp, #0x10
    movs r0, #0
    ldr r3, litA_setvblank
    bl callr3
    movs r0, #0
    movs r1, #0
    ldr r3, litA_setgpureg
    bl callr3                   @ DISPCNT = 0 while we build
    movs r0, #0
    ldr r3, litA_resetbgs
    bl callr3
    movs r0, #0
    ldr r1, litA_bgtpl
    movs r2, #2
    ldr r3, litA_initbgs
    bl callr3                   @ BG0 text (map 31, priority 0), BG1 art (chars 2, map 30, priority 2)
    movs r5, #0                 @ both scrolled to 0,0: the field leaves its own offsets in the registers
ui_scroll:
    adds r0, r5, #0
    movs r1, #0
    movs r2, #0
    ldr r3, litA_changebgx
    bl callr3
    adds r0, r5, #0
    movs r1, #0
    movs r2, #0
    ldr r3, litA_changebgy
    bl callr3
    adds r5, #1
    cmp r5, #2
    blo ui_scroll
    movs r0, #0xD0
    ldr r3, litA_alloczeroed
    bl callr3
    adds r4, r0, #0             @ r4 = ui from here on
    movs r0, #0x80
    lsls r0, r0, #4
    ldr r3, litA_alloczeroed
    bl callr3
    str r0, [r4]
    adds r1, r0, #0
    movs r0, #0
    ldr r3, litA_setbgtilemap
    bl callr3
    ldr r3, litA_resetpalfade
    bl callr3
    ldr r3, litA_resetsprites
    bl callr3
    ldr r3, litA_freespritepals
    bl callr3
    ldr r3, litA_resettasks
    bl callr3
    ldr r3, litA_deactprinters
    bl callr3
    ldr r0, litA_wintpl
    ldr r3, litA_initwindows
    bl callr3
    movs r0, #1                 @ the art's tiles into BG1's char block
    ldr r1, litA_tiles
    ldr r2, litA_tilesize
    movs r3, #0
    ldr r5, litA_loadbgtiles
    bl callr5
    ldr r0, litA_artpal
    movs r1, #0
    movs r2, #32
    ldr r3, litA_loadpalette
    bl callr3
    ldr r0, litA_textpal
    movs r1, #0xF0
    movs r2, #32
    ldr r3, litA_loadpalette
    bl callr3
    bl build_lists
    movs r0, #0                 @ start on the screen that has something, the first if both or neither do
    strb r0, [r4, #4]
    ldrb r0, [r4, #12]
    ldrb r1, [r4, #13]
    orrs r0, r1
    bne ui_screen
    ldrb r0, [r4, #14]
    ldrb r1, [r4, #15]
    orrs r0, r1
    beq ui_screen
    movs r0, #1
    strb r0, [r4, #4]
ui_screen:
    bl draw_screen
    movs r0, #0
    ldr r1, litA_dispcnt
    ldr r3, litA_setgpureg
    bl callr3                   @ OBJ on, 1D mapping; ShowBg adds the BGs
    movs r0, #0
    ldr r3, litA_showbg
    bl callr3
    movs r0, #1
    ldr r3, litA_showbg
    bl callr3
    ldr r0, litA_task
    movs r1, #0
    ldr r3, litA_createtask
    bl callr3
    bl task_data
    strh r4, [r0]
    lsrs r1, r4, #16
    strh r1, [r0, #2]
    movs r1, #0
    strh r1, [r0, #4]           @ data[2] = 0: running, 1: fading out
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #16
    movs r3, #0
    ldr r5, litA_beginfade
    bl callr5                   @ fade in from black
    ldr r0, litA_vblank
    ldr r3, litA_setvblank
    bl callr3
    ldr r0, litA_cb2main
    ldr r3, litA_setcb2
    bl callr3
    add sp, #0x10
    pop {r4, r5, r6, pc}

cb2_main:
    push {lr}
    ldr r3, litA_runtasks
    bl callr3
    ldr r3, litA_animsprites
    bl callr3
    ldr r3, litA_buildoam
    bl callr3
    ldr r3, litA_tilemapcopies
    bl callr3
    ldr r3, litA_updatepalfade
    bl callr3
    pop {pc}

vblank:
    push {lr}
    ldr r3, litA_loadoam
    bl callr3
    ldr r3, litA_spritecopies
    bl callr3
    ldr r3, litA_transferpltt
    bl callr3
    pop {pc}

@ task_data(r0 = task id) -> r0 = &gTasks[id].data[0]
task_data:
    lsls r0, r0, #24
    lsrs r0, r0, #24
    lsls r1, r0, #2
    adds r1, r1, r0
    lsls r1, r1, #3
    ldr r0, litA_gtasks
    adds r0, r0, r1
    adds r0, #8
    bx lr

@ build_lists(r4 = ui): every Pokemon find() gives, into its habitat's list
build_lists:
    push {r4, r5, r6, lr}
    movs r5, #0
bl_loop:
    adds r0, r5, #0
    ldr r3, litA_find
    bl callr3                   @ 1 and the scratch filled, or 0 past the last
    cmp r0, #0
    beq bl_done
    ldr r1, litA_scratch
    ldrb r2, [r1, #4]           @ habitat 0-3
    cmp r2, #3
    bhi bl_next
    adds r3, r4, #0
    adds r3, #12
    ldrb r6, [r3, r2]           @ how many it has so far
    ldr r0, litA_seccap
    ldrb r0, [r0, r2]
    cmp r6, r0
    bhs bl_next
    adds r0, r6, #1
    strb r0, [r3, r2]
    ldr r0, litA_secbase
    ldrb r0, [r0, r2]
    lsls r6, r6, #2
    adds r0, r0, r6
    adds r0, r4, r0
    ldrh r2, [r1]
    strh r2, [r0]
    ldrb r2, [r1, #2]
    strb r2, [r0, #2]
    ldrb r2, [r1, #3]
    strb r2, [r0, #3]
bl_next:
    adds r5, #1
    cmp r5, #40
    blo bl_loop
bl_done:
    pop {r4, r5, r6, pc}

callr3:
    bx r3
callr5:
    bx r5
callr6:
    bx r6

.align 2
litA_setvblank:      .word 0x080006F1
litA_setgpureg:      .word 0x080010B5
litA_resetbgs:       .word 0x080017BD
litA_initbgs:        .word 0x080017E9
litA_changebgx:      .word 0x08001D05
litA_changebgy:      .word 0x08001E7D
litA_bgtpl:          .word BGTPL_ADDR
litA_alloczeroed:    .word 0x08000B4D
litA_setbgtilemap:   .word 0x08002251
litA_resetpalfade:   .word 0x080A1A75
litA_resetsprites:   .word 0x08006975
litA_freespritepals: .word 0x0800870D
litA_resettasks:     .word 0x080A8F51
litA_deactprinters:  .word 0x080045B1
litA_wintpl:         .word WINTPL_ADDR
litA_initwindows:    .word 0x080031C1
litA_tiles:          .word TILES_ADDR
litA_tilesize:       .word TILES_SIZE
litA_loadbgtiles:    .word 0x08001945
litA_artpal:         .word ARTPAL_ADDR
litA_textpal:        .word TEXTPAL_ADDR
litA_loadpalette:    .word 0x080A1939
litA_dispcnt:        .word 0x00001040
litA_showbg:         .word 0x08001B31
litA_task:           .word ui_task + 1
litA_createtask:     .word 0x080A8FB1
litA_beginfade:      .word 0x080A1AD5
litA_vblank:         .word vblank + 1
litA_cb2main:        .word cb2_main + 1
litA_setcb2:         .word 0x08000541
litA_runtasks:       .word 0x080A910D
litA_animsprites:    .word 0x080069C1
litA_buildoam:       .word 0x08006A0D
litA_tilemapcopies:  .word 0x081999D1
litA_updatepalfade:  .word 0x080A1A1D
litA_loadoam:        .word 0x08007189
litA_spritecopies:   .word 0x0800742D
litA_transferpltt:   .word 0x080A19C1
litA_gtasks:         .word 0x03005E00
litA_find:           .word FIND_ADDR
litA_scratch:        .word 0x02021DC4
litA_seccap:         .word SECCAP_ADDR
litA_secbase:        .word SECBASE_ADDR

@ ================================================================ the task: input, and leaving
ui_task:
    push {r4, r5, r6, lr}
    sub sp, #4
    lsls r0, r0, #24
    lsrs r5, r0, #24            @ r5 = task id
    ldr r0, litB_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    beq ut_awake
    b ut_ret                    @ fading: nothing
ut_awake:
    adds r0, r5, #0
    bl task_data
    adds r6, r0, #0             @ r6 = data
    ldrh r4, [r6]
    ldrh r0, [r6, #2]
    lsls r0, r0, #16
    orrs r4, r0                 @ r4 = ui
    ldrh r0, [r6, #4]
    cmp r0, #0
    beq ut_input
    b ut_leave                  @ the fade out is over
ut_input:
    ldr r0, litB_gmain
    ldrh r1, [r0, #0x2E]        @ newKeys
    movs r0, #2
    tst r0, r1
    bne ut_b
    movs r0, #1
    tst r0, r1
    bne ut_a
    movs r0, #3
    lsls r0, r0, #8             @ L | R
    tst r0, r1
    bne ut_page
    movs r0, #0xF0              @ the D-pad
    tst r0, r1
    beq ut_ret
    adds r0, r1, #0
    bl move_cursor
    cmp r0, #0
    beq ut_ret
    movs r0, #5                 @ SE_SELECT
    ldr r3, litB_playse
    bl callr3
    bl draw_panel
    b ut_ret
ut_page:
    ldrb r0, [r4, #4]
    movs r1, #1
    eors r0, r1
    strb r0, [r4, #4]
    movs r0, #5
    ldr r3, litB_playse
    bl callr3
    bl draw_screen
    b ut_ret
ut_a:
    ldrb r0, [r4, #7]
    cmp r0, #0
    beq ut_ret
    ldrb r0, [r4, #5]
    ldrb r1, [r4, #6]
    bl entry_at
    cmp r0, #0
    beq ut_ret
    str r1, [sp]                @ habitat
    adds r2, r0, #0             @ r2 = the entry
    ldr r3, litB_state
    ldrb r1, [r3, #9]
    lsls r1, r1, #31
    beq ut_arm                  @ no search going
    ldrh r1, [r3, #2]
    ldrh r0, [r2]
    cmp r0, r1
    bne ut_arm
    ldr r3, litB_chainbreak     @ A on the one being hunted: stop, as the old screen did
    bl callr3
    b ut_leaving
ut_arm:
    push {r2}
    ldrh r0, [r2]
    bl is_seen
    pop {r2}
    cmp r0, #0
    bne ut_go
    movs r0, #32                @ SE_FAILURE: not seen yet
    ldr r3, litB_playse
    bl callr3
    b ut_ret
ut_go:
    ldrh r0, [r2]               @ arm_search(species, min, max, habitat)
    ldrb r1, [r2, #2]
    ldr r3, [sp]
    ldrb r2, [r2, #3]
    ldr r5, litB_armsearch
    bl callr5
ut_leaving:
    ldr r1, litB_state          @ to the field, not the start menu
    ldrb r0, [r1, #9]
    movs r2, #0x80
    orrs r0, r2
    strb r0, [r1, #9]
ut_b:
    movs r0, #5
    ldr r3, litB_playse
    bl callr3
    movs r0, #1
    strh r0, [r6, #4]
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #0
    movs r3, #16
    ldr r5, litB_beginfade
    bl callr5                   @ fade out to black
    b ut_ret
ut_leave:
    ldr r3, litB_freewindows
    bl callr3
    ldr r0, [r4]
    ldr r3, litB_free
    bl callr3                   @ the BG0 tilemap buffer
    adds r0, r4, #0
    ldr r3, litB_free
    bl callr3                   @ ui
    adds r0, r5, #0
    ldr r3, litB_destroytask
    bl callr3
    ldr r1, litB_state
    ldrb r0, [r1, #9]
    movs r2, #0x80
    tst r0, r2
    beq ut_menu
    bics r0, r2
    strb r0, [r1, #9]
    ldr r0, litB_cb2return      @ the field, controls back, no start menu
    b ut_setcb2
ut_menu:
    ldr r0, litB_returnmenu     @ CB2_ReturnToFieldWithOpenMenu
ut_setcb2:
    ldr r3, litB_setcb2
    bl callr3
ut_ret:
    add sp, #4
    pop {r4, r5, r6, pc}

@ move_cursor(r0 = newKeys, r4 = ui) -> r0 = 1 if the ring moved
move_cursor:
    push {r4, r5, r6, r7, lr}
    adds r7, r0, #0
    ldrb r0, [r4, #7]
    cmp r0, #0
    beq mc_no
    ldrb r5, [r4, #5]           @ row
    ldrb r6, [r4, #6]           @ col
    movs r0, #0x20
    tst r0, r7
    bne mc_left
    movs r0, #0x10
    tst r0, r7
    bne mc_right
    movs r0, #0x40
    tst r0, r7
    bne mc_up
    movs r0, #0x80
    tst r0, r7
    bne mc_down
    b mc_no
mc_left:
    cmp r6, #0
    beq mc_no
    subs r6, #1
    b mc_set
mc_right:
    adds r0, r5, #0
    bl occ
    adds r1, r6, #1
    cmp r1, r0
    bhs mc_no
    adds r6, #1
    b mc_set
mc_up:
    cmp r5, #0
    beq mc_no
    subs r5, #1
    adds r0, r5, #0
    bl occ
    cmp r0, #0
    bne mc_pick
    b mc_up
mc_down:
    cmp r5, #2
    bhs mc_no
    adds r5, #1
    adds r0, r5, #0
    bl occ
    cmp r0, #0
    bne mc_pick
    b mc_down
mc_pick:                        @ the same column, or the row's last Pokemon if it is shorter
    subs r0, #1
    cmp r6, r0
    bls mc_set
    adds r6, r0, #0
mc_set:
    strb r5, [r4, #5]
    strb r6, [r4, #6]
    movs r0, #1
    pop {r4, r5, r6, r7, pc}
mc_no:
    movs r0, #0
    pop {r4, r5, r6, r7, pc}

@ cursor_first(r4 = ui): the ring on the first Pokemon of this screen, or no ring
cursor_first:
    push {r4, r5, lr}
    movs r5, #0
cf_loop:
    adds r0, r5, #0
    bl occ
    cmp r0, #0
    bne cf_found
    adds r5, #1
    cmp r5, #3
    blo cf_loop
    movs r0, #0
    strb r0, [r4, #7]
    pop {r4, r5, pc}
cf_found:
    strb r5, [r4, #5]
    movs r0, #0
    strb r0, [r4, #6]
    movs r0, #1
    strb r0, [r4, #7]
    pop {r4, r5, pc}

@ row_cols(r0 = row, r4 = ui) -> r0 = cells in that row
row_cols:
    cmp r0, #0
    bne rc_b
    movs r0, #5
    bx lr
rc_b:
    ldrb r0, [r4, #4]
    ldr r1, litB_colsb
    ldrb r0, [r1, r0]
    bx lr

@ occ(r0 = row, r4 = ui) -> r0 = how many Pokemon that row has
occ:
    push {r5, lr}
    ldrb r1, [r4, #4]           @ screen
    cmp r0, #0
    bne oc_b
    ldr r2, litB_seca
    ldrb r2, [r2, r1]
    adds r2, r4, r2
    ldrb r0, [r2, #12]
    cmp r0, #5
    bls oc_ret
    movs r0, #5
    b oc_ret
oc_b:
    ldr r2, litB_colsb
    ldrb r5, [r2, r1]           @ cells per row
    ldr r2, litB_secb
    ldrb r2, [r2, r1]
    adds r2, r4, r2
    ldrb r2, [r2, #12]          @ the habitat's count
    cmp r0, #1
    bne oc_row2
    adds r0, r2, #0
    cmp r0, r5
    bls oc_ret
    adds r0, r5, #0
    b oc_ret
oc_row2:
    movs r0, #0
    cmp r2, r5
    bls oc_ret
    subs r0, r2, r5
    cmp r0, r5
    bls oc_ret
    adds r0, r5, #0
oc_ret:
    pop {r5, pc}

@ entry_at(r0 = row, r1 = col, r4 = ui) -> r0 = &entry (0 for an empty cell), r1 = its habitat
entry_at:
    push {r5, r6, lr}
    adds r5, r0, #0
    adds r6, r1, #0
    bl occ
    cmp r6, r0
    bhs ea_none
    ldrb r1, [r4, #4]
    cmp r5, #0
    bne ea_b
    ldr r2, litB_seca
    ldrb r2, [r2, r1]
    adds r0, r6, #0
    b ea_ent
ea_b:
    ldr r2, litB_colsb
    ldrb r0, [r2, r1]
    subs r3, r5, #1
    muls r0, r3, r0
    adds r0, r0, r6
    ldr r2, litB_secb
    ldrb r2, [r2, r1]
ea_ent:
    ldr r3, litB_secbase
    ldrb r3, [r3, r2]
    lsls r0, r0, #2
    adds r0, r0, r3
    adds r0, r4, r0
    adds r1, r2, #0
    pop {r5, r6, pc}
ea_none:
    movs r0, #0
    pop {r5, r6, pc}

@ slot_xy(r0 = row, r1 = col, r4 = ui) -> r0 = x, r1 = y of the cell's centre
slot_xy:
    ldrb r2, [r4, #4]
    cmp r0, #0
    beq sx_have
    ldr r3, litB_colsb
    ldrb r3, [r3, r2]
    subs r0, #1
    muls r0, r3, r0
    adds r1, r1, r0
    adds r1, #5
sx_have:                        @ r1 = slot index
    movs r0, #17
    muls r0, r2, r0
    adds r1, r1, r0
    ldr r3, litB_slotx
    ldrb r0, [r3, r1]
    ldr r3, litB_sloty
    ldrb r1, [r3, r1]
    bx lr

@ is_seen(r0 = species) -> r0 = 1 if the Pokedex has seen it (or it has no dex number)
is_seen:
    push {r4, lr}
    ldr r3, litB_tonational
    bl callr3b
    cmp r0, #0
    beq is_yes
    movs r1, #0                 @ FLAG_GET_SEEN
    ldr r3, litB_dexflag
    bl callr3b
    lsls r0, r0, #24
    beq is_ret
is_yes:
    movs r0, #1
is_ret:
    pop {r4, pc}

callr3b:
    bx r3

.align 2
litB_palfade:     .word 0x02037FD4
litB_gmain:       .word 0x030022C0
litB_playse:      .word 0x080A37A5
litB_state:       .word 0x0203A660
litB_chainbreak:  .word CHAINBREAK_ADDR
litB_armsearch:   .word ARMSEARCH_ADDR
litB_beginfade:   .word 0x080A1AD5
litB_freewindows: .word 0x08003605
litB_free:        .word 0x08000B61
litB_destroytask: .word 0x080A909D
litB_cb2return:   .word CB2RETURN_ADDR
litB_returnmenu:  .word 0x08086195
litB_setcb2:      .word 0x08000541
litB_colsb:       .word COLSB_ADDR
litB_seca:        .word SECA_ADDR
litB_secb:        .word SECB_ADDR
litB_secbase:     .word SECBASE_ADDR
litB_slotx:       .word SLOTX_ADDR
litB_sloty:       .word SLOTY_ADDR
litB_tonational:  .word 0x0806D4A5
litB_dexflag:     .word 0x080C0665

@ ================================================================ drawing a whole screen
@ draw_screen(r4 = ui): sprites, colours, art and words for this screen, then the panel for the first Pokemon
draw_screen:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x14
    ldr r3, litC_resetsprites
    bl callr3c
    ldr r3, litC_freespritepals
    bl callr3c
    ldr r3, litC_loadiconpals
    bl callr3c
    ldr r0, litC_shadowpal
    ldr r3, litC_loadspritepal
    bl callr3c
    strb r0, [r4, #11]
    ldr r0, litC_ringsheet
    ldr r3, litC_loadsheet
    bl callr3c
    ldr r0, litC_ringpal
    ldr r3, litC_loadspritepal
    bl callr3c
    ldr r0, litC_typesheet
    ldr r3, litC_loadcompsheet
    bl callr3c
    ldr r0, litC_typepal
    movs r1, #0xE8
    lsls r1, r1, #1             @ 0x1D0: OBJ palettes 13-15, where the summary screen puts them
    movs r2, #0x60
    ldr r3, litC_loadcomppal
    bl callr3c
    ldrb r5, [r4, #4]           @ screen
    ldr r0, litC_seca           @ the habitats' colours: the top box into 5-7, the bottom one into 8-10
    ldrb r0, [r0, r5]
    movs r1, #6
    muls r0, r1, r0
    ldr r1, litC_habpal
    adds r0, r0, r1
    movs r1, #5
    movs r2, #6
    ldr r3, litC_loadpalette
    bl callr3c
    ldr r0, litC_secb
    ldrb r0, [r0, r5]
    movs r1, #6
    muls r0, r1, r0
    ldr r1, litC_habpal
    adds r0, r0, r1
    movs r1, #8
    movs r2, #6
    ldr r3, litC_loadpalette
    bl callr3c
    movs r0, #1                 @ this screen's tilemap
    lsls r1, r5, #2
    ldr r2, litC_maps
    ldr r1, [r2, r1]
    movs r2, #0x80
    lsls r2, r2, #4
    movs r3, #0
    ldr r6, litC_loadbgtilemap
    bl callr6c
    movs r0, #0
    movs r1, #0
    ldr r3, litC_fillwindow
    bl callr3c                  @ the text layer: all transparent
    bl draw_words
    movs r6, #0                 @ row
ds_row:
    cmp r6, #3
    bhs ds_done
    movs r7, #0                 @ col
ds_col:
    adds r0, r6, #0
    bl row_cols
    cmp r7, r0
    bhs ds_nextrow
    adds r0, r6, #0
    adds r1, r7, #0
    bl entry_at
    str r0, [sp, #0x10]
    adds r0, r6, #0
    adds r1, r7, #0
    bl slot_xy
    ldr r5, [sp, #0x10]
    cmp r5, #0
    beq ds_x
    adds r2, r0, #0             @ CreateMonIcon(species, SpriteCB_MonIcon, x, y, 0, 0, TRUE)
    adds r3, r1, #0
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    movs r0, #1
    str r0, [sp, #8]
    ldrh r0, [r5]
    str r0, [sp, #0xC]
    ldr r1, litC_iconcb
    ldr r5, litC_createmonicon
    bl callr5c
    ldr r1, [sp, #0xC]
    bl shadow
    b ds_nextcol
ds_x:
    subs r0, #8
    subs r1, #8
    bl blit_x
ds_nextcol:
    adds r7, #1
    b ds_col
ds_nextrow:
    adds r6, #1
    b ds_row
ds_done:
    ldr r0, litC_ringtpl        @ the ring and the two type labels
    movs r1, #0
    movs r2, #0
    movs r3, #0
    ldr r5, litC_createsprite
    bl callr5c
    strb r0, [r4, #8]
    ldr r0, litC_typetpl
    movs r1, #0
    movs r2, #0
    movs r3, #0
    bl callr5c
    strb r0, [r4, #9]
    ldr r0, litC_typetpl
    movs r1, #0
    movs r2, #0
    movs r3, #0
    bl callr5c
    strb r0, [r4, #10]
    bl cursor_first
    bl draw_panel
    movs r0, #0
    ldr r3, litC_putwindow
    bl callr3c
    movs r0, #0
    movs r1, #3
    ldr r3, litC_copywindow
    bl callr3c
    add sp, #0x14
    pop {r4, r5, r6, r7, pc}

@ shadow(r0 = sprite id, r1 = species, r4 = ui): an unseen Pokemon's icon in the all-black palette
shadow:
    push {r4, r5, lr}
    adds r5, r0, #0
    cmp r5, #64
    bhs sh_ret
    adds r0, r1, #0
    bl is_seen
    cmp r0, #0
    bne sh_ret
    ldrb r0, [r4, #11]
    cmp r0, #0xFF
    beq sh_ret
    lsls r0, r0, #4
    movs r1, #0x44
    muls r1, r5, r1
    ldr r2, litC_gsprites
    adds r1, r1, r2
    ldrb r2, [r1, #5]
    movs r3, #0x0F
    ands r2, r3
    orrs r2, r0
    strb r2, [r1, #5]
sh_ret:
    pop {r4, r5, pc}

@ blit_x(r0 = x, r1 = y): the 16x16 X of an empty cell into the text layer
blit_x:
    push {r4, lr}
    sub sp, #0x18
    str r0, [sp, #8]            @ destX
    str r1, [sp, #12]           @ destY
    movs r0, #16
    str r0, [sp]                @ the bitmap's width
    str r0, [sp, #4]            @ and height
    str r0, [sp, #16]           @ the rectangle's width
    str r0, [sp, #20]           @ and height
    movs r0, #0                 @ BlitBitmapRectToWindow(0, xmark, 0, 0, 16, 16, x, y, 16, 16)
    ldr r1, litC_xmark
    movs r2, #0
    movs r3, #0
    ldr r4, litC_blit
    bl callr4c
    add sp, #0x18
    pop {r4, pc}

callr3c:
    bx r3
callr4c:
    bx r4
callr5c:
    bx r5
callr6c:
    bx r6

.align 2
litC_resetsprites:   .word 0x08006975
litC_freespritepals: .word 0x0800870D
litC_loadiconpals:   .word 0x080D2F05
litC_shadowpal:      .word SHADOWPAL_ADDR
litC_loadspritepal:  .word 0x08008745
litC_ringsheet:      .word RINGSHEET_ADDR
litC_loadsheet:      .word 0x080084F9
litC_ringpal:        .word RINGPAL_ADDR
litC_typesheet:      .word 0x0861CFBC
litC_loadcompsheet:  .word 0x08034531
litC_typepal:        .word 0x08D97B84
litC_loadcomppal:    .word 0x080A18F5
litC_seca:           .word SECA_ADDR
litC_secb:           .word SECB_ADDR
litC_habpal:         .word HABPAL_ADDR
litC_loadpalette:    .word 0x080A1939
litC_maps:           .word MAPS_ADDR
litC_loadbgtilemap:  .word 0x080019FD
litC_fillwindow:     .word 0x08003C49
litC_iconcb:         .word 0x080D3015
litC_createmonicon:  .word 0x080D2CC5
litC_ringtpl:        .word RINGTPL_ADDR
litC_createsprite:   .word 0x08006DF5
litC_typetpl:        .word 0x0861CFC4
litC_putwindow:      .word 0x0800378D
litC_copywindow:     .word 0x08003659
litC_gsprites:       .word 0x02020630
litC_xmark:          .word XMARK_ADDR
litC_blit:           .word 0x080039DD

@ ================================================================ words
@ print_n / print_s(r0 = x, r1 = y, r2 = string, r3 = colours): the normal / the small font, speed
@ TEXT_SKIP_DRAW - the caller copies the window to VRAM once it has drawn everything
print_n:
    push {r4, r5, lr}
    movs r5, #1
    b pr_go
print_s:
    push {r4, r5, lr}
    movs r5, #0
pr_go:
    sub sp, #0x14
    str r2, [sp, #0x10]         @ string
    movs r2, #0xFF
    str r2, [sp, #0xC]          @ TEXT_SKIP_DRAW
    str r3, [sp, #8]            @ colours
    movs r2, #0
    str r2, [sp]
    str r2, [sp, #4]
    adds r2, r0, #0             @ x
    adds r3, r1, #0             @ y
    movs r0, #0                 @ the window
    adds r1, r5, #0             @ font
    ldr r4, litD_printer4
    bl callr4d
    add sp, #0x14
    pop {r4, r5, pc}

@ clear(r0 = x, r1 = y, r2 = w, r3 = h): that part of the text layer back to transparent
clear:
    push {r4, lr}
    sub sp, #8
    str r2, [sp]
    str r3, [sp, #4]
    adds r2, r0, #0
    adds r3, r1, #0
    movs r0, #0
    movs r1, #0
    ldr r4, litD_fillrect
    bl callr4d                  @ FillWindowPixelRect(0, 0, x, y, w, h)
    add sp, #8
    pop {r4, pc}

@ draw_words(r4 = ui): the place name, the boxes' and the panel's labels, the two tabs
draw_words:
    push {r4, r5, r6, lr}
    ldr r3, litD_getmapsec      @ the place, right-aligned in the top bar
    bl callr3d
    lsls r0, r0, #16
    lsrs r1, r0, #16
    adds r0, r4, #0
    adds r0, #144
    movs r2, #0
    ldr r3, litD_getmapname
    bl callr3d
    movs r0, #1
    adds r1, r4, #0
    adds r1, #144
    movs r2, #236
    ldr r3, litD_rightalign
    bl callr3d
    adds r2, r4, #0
    adds r2, #144
    movs r1, #0
    ldr r3, litD_c_light
    bl print_n
    ldrb r5, [r4, #4]           @ the boxes' names
    lsls r5, r5, #3
    ldr r6, litD_boxnames       @ {top, bottom} per screen
    ldr r2, [r6, r5]
    movs r0, #BOXA_TEXT_X
    movs r1, #BOXA_TEXT_Y
    ldr r3, litD_c_light
    bl print_s
    adds r5, #4
    ldr r2, [r6, r5]
    movs r0, #BOXB_TEXT_X
    movs r1, #BOXB_TEXT_Y
    ldr r3, litD_c_light
    bl print_s
    movs r5, #0                 @ the panel's labels: {string, y} x5
dw_label:
    cmp r5, #5
    bhs dw_tabs
    lsls r0, r5, #3
    ldr r6, litD_labels
    adds r6, r6, r0
    ldr r2, [r6]
    ldr r1, [r6, #4]
    movs r0, #LABEL_X
    ldr r3, litD_c_light
    bl print_s
    adds r5, #1
    b dw_label
dw_tabs:
    ldrb r5, [r4, #4]
    ldr r3, litD_c_dark         @ tab 0: the one we are on is dark, the other dim
    cmp r5, #0
    beq dw_t0
    ldr r3, litD_c_dim
dw_t0:
    ldr r2, litD_tab0
    movs r0, #TAB0_X0
    bl tab_x
    movs r1, #TAB_TEXT_Y
    bl print_s
    ldr r3, litD_c_dark
    cmp r5, #1
    beq dw_t1
    ldr r3, litD_c_dim
dw_t1:
    ldr r2, litD_tab1
    movs r0, #TAB1_X0
    bl tab_x
    movs r1, #TAB_TEXT_Y
    bl print_s
    pop {r4, r5, r6, pc}

@ tab_x(r0 = the tab's left edge, r2 = its word, r3 = colours) -> r0 = x that centres the word; r2, r3 kept
tab_x:
    push {r2, r3, r4, lr}
    adds r4, r0, #0
    movs r0, #0                 @ the small font
    adds r1, r2, #0
    movs r2, #TAB_W
    ldr r3, litD_centeralign
    bl callr3d
    adds r0, r0, r4
    pop {r2, r3, r4, pc}

callr3d:
    bx r3
callr4d:
    bx r4

.align 2
litD_printer4:   .word 0x08199EED
litD_fillrect:   .word 0x08003B65
litD_getmapsec:  .word 0x08085C59
litD_getmapname: .word 0x0812456D
litD_rightalign: .word 0x081DB369
litD_c_light:    .word C_LIGHT_ADDR
litD_c_dark:     .word C_DARK_ADDR
litD_c_dim:      .word C_DIM_ADDR
litD_boxnames:   .word BOXNAMES_ADDR
litD_labels:     .word LABELS_ADDR
litD_tab0:       .word S_TAB0_ADDR
litD_tab1:       .word S_TAB1_ADDR
litD_centeralign: .word 0x081DB35D

@ ================================================================ the panel
@ draw_panel(r4 = ui): everything about the Pokemon under the ring (or nothing), the button, the hunt line
draw_panel:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    movs r0, #PANEL_IN_X        @ clear the value areas, the button's word and the top bar's left
    movs r1, #VAL1_Y
    movs r2, #PANEL_IN_W
    movs r3, #VAL_H
    bl clear
    movs r0, #PANEL_IN_X
    movs r1, #VAL3_Y
    movs r2, #PANEL_IN_W
    movs r3, #VAL_H
    bl clear
    movs r0, #PANEL_IN_X
    movs r1, #VAL4_Y
    movs r2, #PANEL_IN_W
    movs r3, #VAL_H
    bl clear
    movs r0, #PANEL_IN_X
    movs r1, #VAL5_Y
    movs r2, #PANEL_IN_W
    movs r3, #12
    bl clear
    movs r0, #BTN_IN_X
    movs r1, #BTN_IN_Y
    movs r2, #BTN_IN_W
    movs r3, #BTN_IN_H
    bl clear
    movs r0, #0
    movs r1, #0
    movs r2, #140
    movs r3, #16
    bl clear
    movs r5, #0                 @ r5 = the entry under the ring, or 0
    ldrb r0, [r4, #7]
    cmp r0, #0
    beq dp_ring
    ldrb r0, [r4, #5]
    ldrb r1, [r4, #6]
    bl entry_at
    adds r5, r0, #0
dp_ring:
    ldrb r0, [r4, #8]           @ the ring: on the cell, or hidden
    bl sprite_ptr
    adds r6, r0, #0
    cmp r5, #0
    beq dp_noring
    ldrb r0, [r4, #5]
    ldrb r1, [r4, #6]
    bl slot_xy
    strh r0, [r6, #0x20]
    strh r1, [r6, #0x22]
    adds r0, r6, #0
    movs r1, #1
    bl show
    b dp_types
dp_noring:
    adds r0, r6, #0
    movs r1, #0
    bl show
dp_types:
    ldrb r0, [r4, #9]           @ both type labels hidden until we know better
    bl sprite_ptr
    movs r1, #0
    bl show
    ldrb r0, [r4, #10]
    bl sprite_ptr
    movs r1, #0
    bl show
    movs r7, #2                 @ r7 = the button: 0 go, 1 stop, 2 off
    cmp r5, #0
    bne dp_have
    b dp_button
dp_have:
    ldrh r0, [r5]
    bl is_seen
    adds r6, r0, #0             @ r6 = seen
    ldr r2, litE_unknown        @ SPECIES
    cmp r6, #0
    beq dp_name
    ldrh r0, [r5]
    movs r1, #11
    muls r0, r1, r0
    ldr r2, litE_namesptr
    ldr r2, [r2]
    adds r2, r2, r0
dp_name:
    movs r0, #VALUE_X
    movs r1, #VAL1_TEXT_Y
    ldr r3, litE_c_dark
    bl print_n
    cmp r6, #0                  @ TYPE: the summary screen's labels, for a Pokemon seen
    beq dp_level
    ldrh r0, [r5]
    movs r1, #28
    muls r0, r1, r0
    ldr r1, litE_statsptr
    ldr r1, [r1]
    adds r0, r0, r1
    ldrb r6, [r0, #6]           @ type 1
    ldrb r7, [r0, #7]           @ type 2
    ldrb r0, [r4, #9]
    adds r1, r6, #0
    movs r2, #TYPE_ONE_X
    cmp r6, r7
    beq dp_t1
    movs r2, #TYPE1_X
dp_t1:
    bl set_type
    cmp r6, r7
    beq dp_t2done
    ldrb r0, [r4, #10]
    adds r1, r7, #0
    movs r2, #TYPE2_X
    bl set_type
dp_t2done:
    movs r6, #1                 @ seen, still
dp_level:
    adds r0, r4, #0             @ LEVEL: "min" or "min-max"
    adds r0, #144
    ldrb r1, [r5, #2]
    bl dec_str
    ldrb r1, [r5, #2]
    ldrb r2, [r5, #3]
    cmp r1, r2
    beq dp_lvend
    movs r1, #0xAE              @ -
    strb r1, [r0]
    adds r0, #1
    ldrb r1, [r5, #3]
    bl dec_str
dp_lvend:
    movs r1, #0xFF
    strb r1, [r0]
    adds r2, r4, #0
    adds r2, #144
    movs r0, #VALUE_X
    movs r1, #VAL4_TEXT_Y
    ldr r3, litE_c_dark
    bl print_n
    ldrh r0, [r5]               @ SEARCH LV.: from flash
    ldr r3, litE_slget
    bl callr3e
    adds r1, r0, #0
    adds r0, r4, #0
    adds r0, #144
    bl dec_str
    movs r1, #0xFF
    strb r1, [r0]
    adds r2, r4, #0
    adds r2, #144
    movs r0, #VALUE_X
    movs r1, #VAL3_TEXT_Y
    ldr r3, litE_c_dark
    bl print_n
    movs r7, #0                 @ CHAIN: the hunt's, if this is the Pokemon being hunted
    movs r1, #0
    ldr r3, litE_state
    ldrb r0, [r3, #9]
    lsls r0, r0, #31
    beq dp_chain
    ldrh r0, [r3, #2]
    ldrh r2, [r5]
    cmp r0, r2
    bne dp_chain
    ldrh r1, [r3, #4]
    movs r7, #1                 @ the button says STOP
dp_chain:
    adds r0, r4, #0
    adds r0, #144
    bl dec_str
    movs r1, #0xFF
    strb r1, [r0]
    adds r2, r4, #0
    adds r2, #144
    movs r0, #VALUE_X
    movs r1, #VAL5_TEXT_Y
    ldr r3, litE_c_dark
    bl print_n
    cmp r7, #1
    beq dp_button
    movs r7, #0
    cmp r6, #0
    bne dp_button
    movs r7, #2                 @ not seen: nothing to search
dp_button:
    movs r0, #6                 @ its colours into 13-15
    muls r0, r7, r0
    ldr r1, litE_btnpal
    adds r0, r0, r1
    movs r1, #13
    movs r2, #6
    ldr r3, litE_loadpalette
    bl callr3e
    lsls r0, r7, #2
    ldr r1, litE_btnwords
    ldr r6, [r1, r0]
    movs r0, #1
    adds r1, r6, #0
    movs r2, #PANEL_W
    ldr r3, litE_centeralign
    bl callr3e
    adds r0, #PANEL_X
    movs r1, #BTN_TEXT_Y
    adds r2, r6, #0
    ldr r3, litE_c_light
    bl print_n
    ldr r3, litE_state          @ the top bar's left: what is being hunted, or the screen's name
    ldrb r0, [r3, #9]
    lsls r0, r0, #31
    bne dp_hunt
    ldr r2, litE_title
    movs r0, #4
    movs r1, #0
    ldr r3, litE_c_light
    bl print_n
    b dp_copy
dp_hunt:
    ldrh r0, [r3, #2]
    movs r1, #11
    muls r0, r1, r0
    ldr r1, litE_namesptr
    ldr r1, [r1]
    adds r1, r1, r0
    adds r0, r4, #0
    adds r0, #144
    ldr r2, litE_hunting
    push {r1}
    adds r1, r2, #0
    ldr r3, litE_strcpy
    bl callr3e                  @ "Hunting: "
    pop {r1}
    ldr r3, litE_strcpy
    bl callr3e                  @ + the name (StringCopy returns the end)
    adds r2, r4, #0
    adds r2, #144
    movs r0, #4
    movs r1, #0
    ldr r3, litE_c_light
    bl print_n
dp_copy:
    movs r0, #0
    movs r1, #2
    ldr r3, litE_copywindow
    bl callr3e
    add sp, #8
    pop {r4, r5, r6, r7, pc}

@ sprite_ptr(r0 = sprite id) -> r0 = &gSprites[id]
sprite_ptr:
    movs r1, #0x44
    muls r0, r1, r0
    ldr r1, litE_gsprites
    adds r0, r0, r1
    bx lr

@ show(r0 = sprite, r1 = visible)
show:
    adds r0, #0x3E
    ldrb r2, [r0]
    movs r3, #4                 @ invisible
    bics r2, r3
    cmp r1, #0
    bne sw_set
    orrs r2, r3
sw_set:
    strb r2, [r0]
    bx lr

@ set_type(r0 = sprite id, r1 = type, r2 = x): that type's label, its palette, shown at (x, TYPE_Y)
set_type:
    push {r4, r5, r6, lr}
    adds r5, r1, #0
    adds r6, r2, #0
    bl sprite_ptr
    adds r4, r0, #0
    strh r6, [r4, #0x20]
    movs r0, #TYPE_Y
    strh r0, [r4, #0x22]
    adds r0, r4, #0
    adds r1, r5, #0
    ldr r3, litE_startanim
    bl callr3e
    ldr r0, litE_typepals
    ldrb r0, [r0, r5]
    lsls r0, r0, #4
    ldrb r1, [r4, #5]
    movs r2, #0x0F
    ands r1, r2
    orrs r1, r0
    strb r1, [r4, #5]
    adds r0, r4, #0
    movs r1, #1
    bl show
    pop {r4, r5, r6, pc}

@ dec_str(r0 = dst, r1 = value 0-9999) -> r0 = the end of the digits (no terminator)
dec_str:
    push {r4, lr}
    push {r0}
    movs r2, #0                 @ STR_CONV_MODE_LEFT_ALIGN
    movs r3, #4
    ldr r4, litE_ctod
    ldr r0, litE_1000
    cmp r1, r0
    bhs ds3
    movs r3, #3
    cmp r1, #100
    bhs ds3
    movs r3, #2
    cmp r1, #10
    bhs ds3
    movs r3, #1
ds3:
    pop {r0}
    bl callr4e                  @ ConvertIntToDecimalStringN(dst, value, STR_CONV_MODE_LEFT_ALIGN, digits)
    pop {r4, pc}

callr3e:
    bx r3
callr4e:
    bx r4

.align 2
litE_unknown:      .word S_UNKNOWN_ADDR
litE_namesptr:     .word 0x08000144
litE_c_dark:       .word C_DARK_ADDR
litE_c_light:      .word C_LIGHT_ADDR
litE_statsptr:     .word 0x080001BC
litE_slget:        .word SLGET_ADDR
litE_state:        .word 0x0203A660
litE_btnpal:       .word BTNPAL_ADDR
litE_loadpalette:  .word 0x080A1939
litE_btnwords:     .word BTNWORDS_ADDR
litE_centeralign:  .word 0x081DB35D
litE_hunting:      .word S_HUNTING_ADDR
litE_title:        .word S_TITLE_ADDR
litE_strcpy:       .word 0x08008BA1
litE_copywindow:   .word 0x08003659
litE_gsprites:     .word 0x02020630
litE_startanim:    .word 0x080081A9
litE_typepals:     .word 0x09D381A4
litE_ctod:         .word 0x08008CC1
litE_1000:         .word 1000
