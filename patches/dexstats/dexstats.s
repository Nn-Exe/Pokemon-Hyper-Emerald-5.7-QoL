@ R: base stats on the Pokedex's INFO page (Hyper Emerald v5.7).
@ The INFO page shows a small "[R] Stats" tab where its two boxes meet, on the right. R shows a 256x64 panel over the
@ description box - "Base stats" and the total in its title strip, then HP / Atk / Def and SpA / SpD / Spe in two
@ columns, each with its number and a bar (a light track, the bar's colour by the stat: red, orange, yellow, green,
@ teal; full at 200) - and R again takes it away. It stays on while Up / Down go through the Pokemon, and is off
@ again when a Pokemon is opened from the list. (The first build, 2026-10-16, showed it only while R was held: the
@ user, "it works but it is hard to keep holding".)
@
@ HOOK. Task_HandleInfoScreenInput (0x080BEDF4) runs once a frame while the INFO page is up. Its first four
@ instructions (push {r4, r5, lr}; sub sp, #4; lsls r0, r0, #24; lsrs r0, r0, #24: 8 bytes, nothing pc-relative)
@ are an 8-byte jump to `stub` now, which calls `body` (r0 = the task) and then does those four and goes on at
@ 0x080BEDFC. The two words that hold the function's address (the task's func, and IsInfoScreenScrolling's
@ comparison) are untouched.
@
@ STATE. On or off: the INFO task's data[15] (the task keeps its data[] through a scroll - StartInfoScreenScroll sets
@ flags on the same task - and CreateTask clears it when a Pokemon is opened from the list; the page uses data[0..5]).
@ Everything else lives in the tab, a 64x32 sprite whose callback (tab_cb) is how it is found again (no RAM of ours):
@   data0 heartbeat (body sets 3 every frame, tab_cb counts it down: when the INFO page stops running - a scroll,
@   AREA / CRY / SIZE, B - the tab and the panel are gone three frames later)
@   data1..data4 the panel's four pieces' sprite ids + 1 (0: no panel)      data5 the species drawn (0xFFFF: none)
@ The panel is four 64x64 sprites (screen x -8..247: the first 8 columns are off screen), made, drawn and shown in
@ the same frame; the tab is in front of them.
@
@ TEXT. As lmoveinfo does: AddWindow (never put on a tilemap) on the bg of window 0, the frame unpacked into its
@ pixels, the lines printed over it with the small narrow font (colour 0 = transparent, the frame stays), the bars
@ drawn with FillWindowPixelRect, the 32x8 tiles copied row by row into the four pieces' tiles, RemoveWindow.
.thumb

stub:
    push {r0, lr}
    bl body
    pop {r0, r1}
    mov lr, r1
    push {r4, r5, lr}           @ Task_HandleInfoScreenInput's own first four instructions
    sub sp, #4
    lsls r0, r0, #24
    lsrs r0, r0, #24
    ldr r3, litA_back
    bx r3

@ body(r0 = the INFO page's task)
body:
    push {r4, r5, r6, r7, lr}
    lsls r0, r0, #24
    lsrs r0, r0, #24
    lsls r6, r0, #2             @ r6 = &gTasks[task].data[15]: gTasks + task * 40 + 8 + 30
    adds r6, r6, r0
    lsls r6, r6, #3
    ldr r1, litA_gtasks
    adds r6, r6, r1
    adds r6, #38
    bl find_tab
    cmp r0, #0
    bne bd_tab
    bl make_tab
    cmp r0, #0
    beq bd_ret
bd_tab:
    adds r4, r0, #0             @ r4 = the tab
    movs r0, #3
    strh r0, [r4, #0x2E]        @ heartbeat
    ldr r0, litA_gmain
    ldrh r0, [r0, #0x2E]        @ newKeys
    lsrs r0, r0, #8             @ R
    movs r1, #1
    ands r0, r1
    beq bd_state
    ldrh r0, [r6]
    movs r1, #1
    eors r0, r1
    strh r0, [r6]               @ on <-> off
    movs r0, #SE_DEX_PAGE
    ldr r3, litA_playse
    bl call3
bd_state:
    ldrh r0, [r6]
    cmp r0, #0
    bne bd_on
    ldrh r0, [r4, #0x30]        @ off: no panel
    cmp r0, #0
    beq bd_ret
    adds r0, r4, #0
    bl kill_panel
    b bd_ret
bd_on:
    ldr r0, litA_item
    ldr r0, [r0]                @ sPokedexListItem
    ldrh r0, [r0]               @ its National Dex number
    ldr r3, litA_dex2sp
    bl call3
    lsls r0, r0, #16
    lsrs r5, r0, #16            @ r5 = the species
    cmp r5, #0
    beq bd_ret
    ldrh r0, [r4, #0x30]
    cmp r0, #0
    bne bd_have
    adds r0, r4, #0
    bl make_panel
    cmp r0, #0
    beq bd_ret
bd_have:
    ldrh r0, [r4, #0x38]
    cmp r0, r5
    beq bd_ret
    adds r0, r4, #0
    adds r1, r5, #0
    bl render
    cmp r0, #0
    bne bd_drawn
    adds r0, r4, #0             @ no window to draw in: no panel
    bl kill_panel
    b bd_ret
bd_drawn:
    strh r5, [r4, #0x38]
bd_ret:
    pop {r4, r5, r6, r7, pc}

@ find_tab() -> r0 = the tab's sprite, or 0 (leaf)
find_tab:
    ldr r0, litA_gsprites
    movs r1, #64
    ldr r3, litA_tabcb
ft_loop:
    adds r2, r0, #0
    adds r2, #0x3E
    ldrb r2, [r2]
    lsls r2, r2, #31            @ inUse
    beq ft_next
    ldr r2, [r0, #0x1C]
    cmp r2, r3
    beq ft_ret
ft_next:
    adds r0, #0x44
    subs r1, #1
    bne ft_loop
    movs r0, #0
ft_ret:
    bx lr

@ sprite_ptr(r0 = id) -> r0 = &gSprites[id] (leaf, r0 r1)
sprite_ptr:
    lsls r1, r0, #4
    adds r1, r1, r0
    lsls r1, r1, #2
    ldr r0, litA_gsprites
    adds r0, r0, r1
    bx lr

@ make_tab() -> r0 = the tab's sprite, or 0 (then nothing of ours is left)
make_tab:
    push {r4, lr}
    ldr r0, litA_palstruct
    ldr r3, litA_loadspal
    bl call3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #0xFF
    beq mt_none                 @ no sprite palette free
    ldr r0, litA_tabsheet
    ldr r3, litA_loadsheet
    bl call3
    ldr r0, litA_tabtpl
    movs r1, #TAB_CX
    movs r2, #TAB_CY
    movs r3, #0                 @ subpriority 0: in front of the panel
    bl create
    cmp r0, #64
    bhs mt_fail
    bl sprite_ptr
    adds r4, r0, #0
    adds r0, #0x40
    ldrh r0, [r0]               @ sheetTileStart: 0xFFFF when the sheet did not load
    ldr r1, litA_ffff
    cmp r0, r1
    beq mt_failsprite
    movs r0, #0
    strh r0, [r4, #0x30]        @ no panel
    strh r0, [r4, #0x32]
    strh r0, [r4, #0x34]
    strh r0, [r4, #0x36]
    strh r1, [r4, #0x38]        @ nothing drawn
    adds r0, r4, #0
    pop {r4, pc}
mt_failsprite:
    adds r0, r4, #0
    ldr r3, litA_destroysprite
    bl call3
mt_fail:
    ldr r0, litA_tagtab
    ldr r3, litA_freetiles
    bl call3
    ldr r0, litA_tagpal
    ldr r3, litA_freepal
    bl call3
mt_none:
    movs r0, #0
    pop {r4, pc}

@ make_panel(r0 = the tab) -> r0 = 1 when the four pieces exist (nothing drawn yet: body renders them in the same
@ frame, before they are ever shown), 0 (then no piece is left)
make_panel:
    push {r4, r5, r6, r7, lr}
    adds r6, r0, #0             @ r6 = the tab
    ldr r4, litA_sheets         @ the four sheets
    movs r5, #4
mp_sheet:
    adds r0, r4, #0
    ldr r3, litA_loadsheet
    bl call3
    adds r4, #8
    subs r5, #1
    bne mp_sheet
    ldr r4, litA_tpls           @ r4 = the template, r5 = the piece, r7 = x
    movs r5, #0
    movs r7, #PIECE_X0
mp_piece:
    adds r0, r4, #0
    adds r1, r7, #0
    movs r2, #PANEL_CY
    movs r3, #1                 @ subpriority 1: behind the tab
    bl create
    cmp r0, #64
    bhs mp_fail
    push {r0}                   @ its id
    bl sprite_ptr
    adds r2, r0, #0
    adds r2, #0x40
    ldrh r2, [r2]               @ sheetTileStart: 0xFFFF when its sheet did not load
    ldr r3, litA_ffff
    cmp r2, r3
    beq mp_failsprite
    pop {r1}
    adds r1, #1                 @ id + 1 into the tab's data(1 + piece)
    lsls r2, r5, #1
    adds r2, #0x30
    strh r1, [r6, r2]
    adds r4, #24
    adds r7, #64
    adds r5, #1
    cmp r5, #4
    bne mp_piece
    ldr r0, litA_ffff
    strh r0, [r6, #0x38]        @ nothing drawn yet
    movs r0, #1
    pop {r4, r5, r6, r7, pc}
mp_failsprite:
    pop {r1}
    ldr r3, litA_destroysprite  @ (r0 = the sprite)
    bl call3
mp_fail:
    adds r0, r6, #0
    bl kill_panel
    movs r0, #0
    pop {r4, r5, r6, r7, pc}

@ create(r0 = template, r1 = x, r2 = y, r3 = subpriority) -> r0 = CreateSprite's id
create:
    push {r4, lr}
    ldr r4, litA_createsprite
    bl call4
    lsls r0, r0, #24
    lsrs r0, r0, #24
    pop {r4, pc}

@ kill_panel(r0 = the tab): the four pieces and their tiles gone
kill_panel:
    push {r4, r5, lr}
    adds r4, r0, #0
    movs r5, #0x30
kp_loop:
    ldrh r0, [r4, r5]
    cmp r0, #0
    beq kp_next
    subs r0, #1
    bl sprite_ptr
    ldr r3, litA_destroysprite
    bl call3
    movs r0, #0
    strh r0, [r4, r5]
kp_next:
    adds r5, #2
    cmp r5, #0x38
    bne kp_loop
    ldr r0, litA_ffff
    strh r0, [r4, #0x38]
    ldr r4, litA_tags           @ the pieces' sheets
    movs r5, #4
kp_tiles:
    ldrh r0, [r4]
    ldr r3, litA_freetiles
    bl call3
    adds r4, #2
    subs r5, #1
    bne kp_tiles
    pop {r4, r5, pc}

@ tab_cb(r0 = the tab): its callback - the heartbeat
tab_cb:
    push {r4, lr}
    adds r4, r0, #0
    movs r1, #0x2E
    ldrsh r0, [r4, r1]
    subs r0, #1
    strh r0, [r4, #0x2E]
    cmp r0, #0
    bgt tc_ret
    adds r0, r4, #0             @ the INFO page is not running any more: neither are we
    bl kill_panel
    ldr r0, litA_tagtab
    ldr r3, litA_freetiles
    bl call3
    ldr r0, litA_tagpal
    ldr r3, litA_freepal
    bl call3
    adds r0, r4, #0
    ldr r3, litA_destroysprite
    bl call3
tc_ret:
    pop {r4, pc}

call3:
    bx r3
call4:
    bx r4

.align 2
litA_back:          .word 0x080BEDFD    @ Task_HandleInfoScreenInput after its first four instructions
litA_gtasks:        .word 0x03005E00    @ gTasks (40 bytes a task, data[] from +8)
litA_gmain:         .word 0x030022C0
litA_item:          .word 0x02039B54    @ sPokedexListItem
litA_dex2sp:        .word 0x0806D40D    @ NationalPokedexNumToSpecies
litA_playse:        .word 0x080A37A5    @ PlaySE
litA_gsprites:      .word 0x02020630
litA_tabcb:         .word tab_cb + 1
litA_palstruct:     .word PALSTRUCT_ADDR
litA_tabsheet:      .word TABSHEET_ADDR
litA_tabtpl:        .word TABTPL_ADDR
litA_sheets:        .word SHEETS_ADDR
litA_tpls:          .word TPLS_ADDR
litA_tags:          .word TAGS_ADDR
litA_tagtab:        .word TAG_TAB
litA_tagpal:        .word TAG_PAL
litA_ffff:          .word 0x0000FFFF
litA_loadsheet:     .word 0x080084F9    @ LoadSpriteSheet
litA_loadspal:      .word 0x08008745    @ LoadSpritePalette
litA_createsprite:  .word 0x08006DF5    @ CreateSprite
litA_destroysprite: .word 0x080070E9    @ DestroySprite
litA_freetiles:     .word 0x08008569    @ FreeSpriteTilesByTag
litA_freepal:       .word 0x0800884D    @ FreeSpritePaletteByTag

@ render(r0 = the tab, r1 = species) -> r0 = 1 drawn, 0 not (no window free)
@ frame: [sp] .. [sp+15] the printer's arguments (pr), [sp+16] the window template (8 bytes), [sp+24] the stats,
@ [sp+28] the piece counter, [sp+32..47] a number string
render:
    push {r4, r5, r6, r7, lr}
    sub sp, #48
    adds r4, r0, #0
    adds r5, r1, #0
    ldr r0, litB_wintpl         @ the template, with window 0's bg
    ldr r1, [r0]
    str r1, [sp, #16]
    ldr r1, [r0, #4]
    str r1, [sp, #20]
    ldr r0, litB_gwindows
    ldrb r0, [r0]               @ window 0's bg (0xFF when it is not in use: then bg 0)
    cmp r0, #3
    bls rn_bg
    movs r0, #0
rn_bg:
    add r1, sp, #16
    strb r0, [r1]
    adds r0, r1, #0
    ldr r3, litB_addwindow
    bl call3b
    lsls r0, r0, #24
    lsrs r6, r0, #24            @ r6 = the window
    cmp r6, #0xFF
    bne rn_win
    movs r0, #0
    b rn_ret
rn_win:
    lsls r0, r6, #1
    adds r0, r0, r6
    lsls r0, r0, #2
    ldr r1, litB_gwindows
    adds r0, r0, r1
    ldr r7, [r0, #8]            @ r7 = its pixels
    ldr r0, litB_panellz
    adds r1, r7, #0
    ldr r3, litB_lz77wram
    bl call3b                   @ the frame
    ldr r0, litB_basestats
    ldr r0, [r0]
    lsls r1, r5, #3             @ species * 28
    subs r1, r1, r5
    lsls r1, r1, #2
    adds r0, r0, r1
    str r0, [sp, #24]
    @ "Base stats"
    movs r0, #TITLE_X
    movs r1, #TEXT_Y
    ldr r2, litB_coltitle
    ldr r3, litB_stitle
    bl pr
    @ "Total N", right-aligned
    ldr r0, [sp, #24]
    ldrb r1, [r0, #0]
    ldrb r2, [r0, #1]
    adds r1, r1, r2
    ldrb r2, [r0, #2]
    adds r1, r1, r2
    ldrb r2, [r0, #3]
    adds r1, r1, r2
    ldrb r2, [r0, #4]
    adds r1, r1, r2
    ldrb r2, [r0, #5]
    adds r1, r1, r2
    ldr r0, litB_stotal         @ "Total " into the string buffer, then the number
    add r2, sp, #32
st_copy:
    ldrb r3, [r0]
    cmp r3, #0xFF
    beq st_num
    strb r3, [r2]
    adds r0, #1
    adds r2, #1
    b st_copy
st_num:
    ldr r0, litB_convert
    mov ip, r0
    adds r0, r2, #0
    movs r2, #0
    movs r3, #4
    bl callip
    add r0, sp, #32
    bl width
    movs r1, #TOTAL_RIGHT
    subs r0, r1, r0
    movs r1, #TEXT_Y
    ldr r2, litB_coltitle
    add r3, sp, #32
    bl pr
    @ the six stats
    movs r5, #0                 @ r5 = k
rn_stat:
    @ label
    adds r0, r5, #0
    bl stat_xy                  @ r0 = x, r1 = y
    lsls r2, r5, #2
    ldr r3, litB_labels
    ldr r3, [r3, r2]
    ldr r2, litB_collabel
    bl pr
    @ the value, right-aligned
    ldr r0, litB_order
    ldrb r0, [r0, r5]
    ldr r1, [sp, #24]
    ldrb r1, [r1, r0]
    str r1, [sp, #28]           @ the value
    ldr r0, litB_convert
    mov ip, r0
    add r0, sp, #32
    movs r2, #0
    movs r3, #3
    bl callip
    add r0, sp, #32
    bl width
    push {r0}
    adds r0, r5, #0
    bl stat_xy
    pop {r2}
    adds r0, #NUM_RIGHT
    subs r0, r0, r2
    ldr r2, litB_colvalue
    add r3, sp, #32
    bl pr
    @ the track
    adds r0, r5, #0
    bl stat_xy
    adds r2, r0, #0
    adds r2, #BAR_X             @ x
    adds r3, r1, #0
    adds r3, #BAR_Y             @ y
    movs r0, #BAR_W
    str r0, [sp]
    movs r0, #BAR_H
    str r0, [sp, #4]
    ldr r0, litB_fillrect
    mov ip, r0
    adds r0, r6, #0
    movs r1, #TRACK_FILL
    bl callip
    @ the bar: min(value, 200) * 60 / 200 = (min * 615) >> 11 (the same for 0..200)
    ldr r0, [sp, #28]
    cmp r0, #BAR_FULL
    bls rn_len
    movs r0, #BAR_FULL
rn_len:
    ldr r1, litB_615
    muls r0, r1
    lsrs r0, r0, #11
    cmp r0, #0
    beq rn_next
    str r0, [sp]                @ width
    movs r0, #BAR_H
    str r0, [sp, #4]
    ldr r0, [sp, #28]           @ the colour by the value
    ldr r1, litB_bands
rn_band:
    ldrb r2, [r1]
    cmp r2, #0
    beq rn_col
    cmp r0, r2
    blo rn_col
    adds r1, #2
    b rn_band
rn_col:
    ldrb r1, [r1, #1]           @ the colour index, twice in the fill byte
    lsls r0, r1, #4
    orrs r1, r0
    push {r1}
    adds r0, r5, #0
    bl stat_xy
    adds r2, r0, #0
    adds r2, #BAR_X
    adds r3, r1, #0
    adds r3, #BAR_Y
    pop {r1}
    ldr r0, litB_fillrect
    mov ip, r0
    adds r0, r6, #0
    bl callip
rn_next:
    adds r5, #1
    cmp r5, #6
    bne rn_stat
    @ the window's 32x8 tiles, a row at a time, into the four pieces (8 tiles of each row to a piece)
    movs r5, #0                 @ piece
rn_piece:
    lsls r0, r5, #1             @ the tab's data(1 + piece): the piece's id + 1
    adds r0, #0x30
    ldrh r0, [r4, r0]
    subs r0, #1
    bl sprite_ptrb
    adds r0, #0x40
    ldrh r0, [r0]               @ sheetTileStart
    lsls r0, r0, #5
    ldr r1, litB_objvram
    adds r1, r0, r1             @ r1 = the piece's tiles
    lsls r0, r5, #8
    adds r0, r7, r0             @ r0 = the window's first row, this piece's 8 tiles
    movs r2, #8
    str r2, [sp, #28]           @ rows left
rn_row:
    push {r0, r1}
    bl copy256
    pop {r0, r1}
    movs r2, #1
    lsls r2, r2, #10
    adds r0, r0, r2             @ the window's next row: 32 tiles on
    movs r2, #1
    lsls r2, r2, #8
    adds r1, r1, r2             @ the piece's next row: 8 tiles on
    ldr r2, [sp, #28]
    subs r2, #1
    str r2, [sp, #28]
    bne rn_row
    adds r5, #1
    cmp r5, #4
    bne rn_piece
    adds r0, r6, #0
    ldr r3, litB_removewindow
    bl call3b
    movs r0, #1
rn_ret:
    add sp, #48
    pop {r4, r5, r6, r7, pc}

@ stat_xy(r0 = k) -> r0 = the label's x, r1 = the row's y (leaf, r0 r1 r2)
stat_xy:
    movs r1, #COL1_X
    cmp r0, #3
    blo sx_col
    subs r0, #3
    movs r1, #COL2_X
sx_col:
    lsls r0, r0, #1
    ldr r2, litB_rowsy
    ldrb r2, [r2, r0]
    adds r0, r1, #0
    adds r1, r2, #0
    bx lr

@ copy256(r0 = src, r1 = dst): 64 words (leaf)
copy256:
    movs r2, #64
c2_loop:
    ldmia r0!, {r3}
    stmia r1!, {r3}
    subs r2, #1
    bne c2_loop
    bx lr

@ sprite_ptrb(r0 = id) -> r0 = &gSprites[id] (leaf)
sprite_ptrb:
    lsls r1, r0, #4
    adds r1, r1, r0
    lsls r1, r1, #2
    ldr r0, litB_gsprites
    adds r0, r0, r1
    bx lr

@ width(r0 = string) -> r0 = its width in pixels, small narrow font
width:
    push {r4, lr}
    adds r1, r0, #0
    movs r0, #FONT
    movs r2, #0
    ldr r4, litB_strwidth
    bl call4b
    pop {r4, pc}

@ pr(r0 = x, r1 = y, r2 = colours, r3 = string): one line into window r6, small narrow font, drawn at once
pr:
    push {r4, lr}
    sub sp, #20
    str r2, [sp, #8]
    str r3, [sp, #16]
    movs r2, #0
    str r2, [sp]
    str r2, [sp, #4]
    movs r2, #0xFF              @ TEXT_SKIP_DRAW
    str r2, [sp, #12]
    adds r2, r0, #0
    adds r3, r1, #0
    adds r0, r6, #0
    movs r1, #FONT
    ldr r4, litB_addtext4
    bl call4b
    add sp, #20
    pop {r4, pc}

call3b:
    bx r3
call4b:
    bx r4
callip:
    bx ip

.align 2
litB_wintpl:        .word WINTPL_ADDR
litB_addwindow:     .word 0x08003381    @ AddWindow
litB_removewindow:  .word 0x08003575    @ RemoveWindow
litB_gwindows:      .word 0x02020004    @ gWindows (12 bytes: the template, then the pixels)
litB_panellz:       .word PANELLZ_ADDR
litB_lz77wram:      .word 0x082E7091    @ LZ77UnCompWram
litB_basestats:     .word 0x080001BC    @ the ROM header's word for the base stats table (28 bytes a species:
                                        @ HP, Attack, Defense, Speed, Sp. Atk, Sp. Def first)
litB_coltitle:      .word COLTITLE_ADDR
litB_collabel:      .word COLLABEL_ADDR
litB_colvalue:      .word COLVALUE_ADDR
litB_stitle:        .word STITLE_ADDR
litB_stotal:        .word STOTAL_ADDR
litB_labels:        .word LABELS_ADDR
litB_order:         .word ORDER_ADDR
litB_rowsy:         .word ROWSY_ADDR
litB_bands:         .word BANDS_ADDR
litB_615:           .word 615
litB_fillrect:      .word 0x08003B65    @ FillWindowPixelRect
litB_objvram:       .word 0x06010000
litB_gsprites:      .word 0x02020630
litB_addtext4:      .word 0x08199EED    @ AddTextPrinterParameterized4
litB_convert:       .word 0x08008CC1    @ ConvertIntToDecimalStringN
litB_strwidth:      .word 0x08005ED9    @ GetStringWidth
