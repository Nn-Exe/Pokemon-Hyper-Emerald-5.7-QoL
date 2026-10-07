@ L: move info in battle (Hyper Emerald v5.7).
@ While the move menu is up a small "[L] Move Info" tag sits above it on the left. Holding L slides a 128x64 panel in
@ from the left with the highlighted move's name, Power, Accuracy, Physical / Special / Status, Contact or not,
@ Priority and its effect chance; it follows the cursor and slides back out when L is let go.
@
@ HOOK. HandleInputChooseMove (0x08057BFC) already jumps into the hack's own code after its prologue
@ (0x08057C04: ldr r0,[pc]; bx r0; .word 0x09D0A8C1). That word now points at `entry`, which runs `body` once a
@ frame and then goes on to the hack's code. lr is already on the stack there and r0-r3 are free.
@
@ SPRITES. The tag is one 64x32 sprite whose callback (hud_cb) is also how it is found again (no RAM of our own):
@ its data[] holds the state. data0 is a heartbeat `body` sets to 3 every frame; hud_cb counts it down, so when the
@ move menu stops running (a move chosen, B, the target cursor, the move-swap screen) everything of ours is gone
@ three frames later with no hook on any of those exits. The panel is two 64x64 sprites; hud_cb slides them.
@   data0 heartbeat  data1 L held  data2 / data3 panel sprite id + 1 (0 = none)  data4 move shown  data5 x offset
@
@ TEXT. As the healthbox does: AddWindow on bg 0 (never put on the tilemap), the frame's pixels unpacked into its
@ buffer, the lines printed over it with the small narrow font (colour 0 = transparent, so the frame stays), the
@ 16x8 tiles copied row by row into the two sprites' tiles in OBJ VRAM, RemoveWindow.
.thumb

entry:
    bl body
    ldr r0, litA_hack
    bx r0

body:
    push {r4, r5, r6, r7, lr}
    bl find_hud
    cmp r0, #0
    bne b_have
    bl make_hud
    cmp r0, #0
    beq b_ret
b_have:
    adds r4, r0, #0             @ r4 = the tag's sprite
    movs r0, #3
    strh r0, [r4, #0x2E]        @ heartbeat
    ldr r0, litA_gmain
    ldrh r0, [r0, #0x2C]        @ heldKeys
    lsrs r0, r0, #9             @ L
    movs r1, #1
    ands r0, r1
    strh r0, [r4, #0x30]
    cmp r0, #0
    beq b_ret
    ldr r0, litA_active
    ldrb r0, [r0]
    ldr r1, litA_cursor
    ldrb r1, [r1, r0]
    lsls r2, r0, #9
    ldr r3, litA_moveinfo
    adds r2, r2, r3
    lsls r1, r1, #1
    ldrh r5, [r2, r1]           @ r5 = the highlighted move
    ldrh r0, [r4, #0x32]
    cmp r0, #0
    bne b_panel
    adds r0, r4, #0
    bl make_panel
    cmp r0, #0
    beq b_ret
b_panel:
    ldrh r0, [r4, #0x36]
    cmp r0, r5
    beq b_ret
    strh r5, [r4, #0x36]
    adds r0, r4, #0
    adds r1, r5, #0
    bl render
b_ret:
    pop {r4, r5, r6, r7, pc}

@ find_hud() -> r0 = the tag's sprite, or 0 (leaf)
find_hud:
    ldr r0, litA_gsprites
    movs r1, #64
    ldr r3, litA_hudcb
fh_loop:
    adds r2, r0, #0
    adds r2, #0x3E
    ldrb r2, [r2]
    lsls r2, r2, #31            @ inUse
    beq fh_next
    ldr r2, [r0, #0x1C]
    cmp r2, r3
    beq fh_ret
fh_next:
    adds r0, #0x44
    subs r1, #1
    bne fh_loop
    movs r0, #0
fh_ret:
    bx lr

@ sprite_ptr(r0 = id) -> r0 = &gSprites[id] (leaf, r0 r1)
sprite_ptr:
    lsls r1, r0, #4
    adds r1, r1, r0
    lsls r1, r1, #2
    ldr r0, litA_gsprites
    adds r0, r0, r1
    bx lr

@ make_hud() -> r0 = the tag's sprite, or 0
make_hud:
    push {r4, lr}
    ldr r0, litA_hudsheet
    ldr r3, litA_loadsheet
    bl call3
    ldr r0, litA_palstruct
    ldr r3, litA_loadspal
    bl call3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #0xFF
    beq mh_fail                 @ no sprite palette free
    ldr r0, litA_hudtpl
    movs r1, #HUD_X
    movs r2, #HUD_Y
    movs r3, #2
    ldr r4, litA_createsprite
    bl call4
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #64
    bhs mh_fail
    bl sprite_ptr
    pop {r4, pc}
mh_fail:
    ldr r0, litA_taghud
    ldr r3, litA_freetiles
    bl call3
    ldr r0, litA_taghud
    ldr r3, litA_freepal
    bl call3
    movs r0, #0
    pop {r4, pc}

@ make_panel(r0 = tag sprite) -> r0 = 1 when both halves exist (off screen to the left, nothing drawn yet)
make_panel:
    push {r4, r5, r6, lr}
    adds r4, r0, #0
    ldr r0, litA_sheeta
    ldr r3, litA_loadsheet
    bl call3
    ldr r0, litA_sheetb
    ldr r3, litA_loadsheet
    bl call3
    ldr r0, litA_tpla
    movs r1, #96
    rsbs r1, r1, #0             @ x = 32 - 128
    movs r2, #PANEL_Y
    movs r3, #1
    ldr r6, litA_createsprite
    bl call6
    lsls r0, r0, #24
    lsrs r5, r0, #24
    cmp r5, #64
    bhs mp_fail
    ldr r0, litA_tplb
    movs r1, #32
    rsbs r1, r1, #0             @ x = 96 - 128
    movs r2, #PANEL_Y
    movs r3, #1
    ldr r6, litA_createsprite
    bl call6
    lsls r0, r0, #24
    lsrs r6, r0, #24
    cmp r6, #64
    bhs mp_failb
    adds r5, #1
    strh r5, [r4, #0x32]
    adds r6, #1
    strh r6, [r4, #0x34]
    ldr r0, litA_ffff
    strh r0, [r4, #0x36]        @ nothing drawn
    movs r0, #128
    rsbs r0, r0, #0
    strh r0, [r4, #0x38]        @ offset -128
    movs r0, #1
    pop {r4, r5, r6, pc}
mp_failb:
    adds r0, r5, #0
    bl sprite_ptr
    ldr r3, litA_destroysprite
    bl call3
mp_fail:
    ldr r0, litA_taga
    ldr r3, litA_freetiles
    bl call3
    ldr r0, litA_tagb
    ldr r3, litA_freetiles
    bl call3
    movs r0, #0
    pop {r4, r5, r6, pc}

@ kill_panel(r0 = tag sprite): both halves and their tiles gone
kill_panel:
    push {r4, lr}
    adds r4, r0, #0
    ldrh r0, [r4, #0x32]
    cmp r0, #0
    beq kp_b
    subs r0, #1
    bl sprite_ptr
    ldr r3, litA_destroysprite
    bl call3
kp_b:
    ldrh r0, [r4, #0x34]
    cmp r0, #0
    beq kp_free
    subs r0, #1
    bl sprite_ptr
    ldr r3, litA_destroysprite
    bl call3
kp_free:
    movs r0, #0
    strh r0, [r4, #0x32]
    strh r0, [r4, #0x34]
    ldr r0, litA_taga
    ldr r3, litA_freetiles
    bl call3
    ldr r0, litA_tagb
    ldr r3, litA_freetiles
    bl call3
    pop {r4, pc}

@ hud_cb(r0 = the tag's sprite): its callback - the heartbeat and the slide
hud_cb:
    push {r4, r5, r6, lr}
    adds r4, r0, #0
    movs r1, #0x2E
    ldrsh r0, [r4, r1]
    subs r0, #1
    strh r0, [r4, #0x2E]
    cmp r0, #0
    bgt hc_alive
    adds r0, r4, #0             @ the move menu is gone: so are we
    bl kill_panel
    ldr r0, litA_taghud
    ldr r3, litA_freetiles
    bl call3
    ldr r0, litA_taghud
    ldr r3, litA_freepal
    bl call3
    adds r0, r4, #0
    ldr r3, litA_destroysprite
    bl call3
    b hc_ret
hc_alive:
    ldrh r0, [r4, #0x32]
    cmp r0, #0
    beq hc_ret
    movs r1, #0x38
    ldrsh r5, [r4, r1]          @ offset: -128 hidden .. 0 shown
    ldrh r0, [r4, #0x30]
    cmp r0, #0
    beq hc_out
    adds r5, #SLIDE
    cmp r5, #0
    ble hc_set
    movs r5, #0
    b hc_set
hc_out:
    subs r5, #SLIDE
    movs r0, #128
    cmn r5, r0
    bgt hc_set                  @ still on screen
    adds r0, r4, #0
    bl kill_panel
    b hc_ret
hc_set:
    strh r5, [r4, #0x38]
    ldrh r0, [r4, #0x32]
    subs r0, #1
    bl sprite_ptr
    adds r1, r5, #0
    adds r1, #32
    strh r1, [r0, #0x20]
    ldrh r0, [r4, #0x34]
    subs r0, #1
    bl sprite_ptr
    adds r1, r5, #0
    adds r1, #96
    strh r1, [r0, #0x20]
hc_ret:
    pop {r4, r5, r6, pc}

call3:
    bx r3
call4:
    bx r4
call6:
    bx r6

.align 2
litA_hack:          .word 0x09D0A8C1    @ the hack's own continuation of HandleInputChooseMove
litA_gmain:         .word 0x030022C0
litA_active:        .word 0x02024064    @ gActiveBattler
litA_cursor:        .word 0x020244B0    @ gMoveSelectionCursor
litA_moveinfo:      .word 0x02023068    @ the chosen Pokemon's move list
litA_gsprites:      .word 0x02020630
litA_hudcb:         .word hud_cb + 1
litA_hudsheet:      .word HUDSHEET_ADDR
litA_sheeta:        .word SHEETA_ADDR
litA_sheetb:        .word SHEETB_ADDR
litA_palstruct:     .word PALSTRUCT_ADDR
litA_hudtpl:        .word HUDTPL_ADDR
litA_tpla:          .word TPLA_ADDR
litA_tplb:          .word TPLB_ADDR
litA_taghud:        .word TAG_HUD
litA_taga:          .word TAG_A
litA_tagb:          .word TAG_B
litA_ffff:          .word 0x0000FFFF
litA_loadsheet:     .word 0x080084F9    @ LoadSpriteSheet
litA_loadspal:      .word 0x08008745    @ LoadSpritePalette
litA_createsprite:  .word 0x08006DF5
litA_destroysprite: .word 0x080070E9
litA_freetiles:     .word 0x08008569    @ FreeSpriteTilesByTag
litA_freepal:       .word 0x0800884D    @ FreeSpritePaletteByTag

@ render(r0 = tag sprite, r1 = move): the panel's pixels for that move, into the two halves' tiles
@ frame: [sp+20] the move's data, then the row counter; [sp+24..35] a number string
render:
    push {r4, r5, r6, r7, lr}
    sub sp, #36
    adds r4, r0, #0
    adds r5, r1, #0
    ldr r0, litB_wintpl
    ldr r3, litB_addwindow
    bl call3b
    lsls r0, r0, #24
    lsrs r6, r0, #24            @ r6 = the window
    cmp r6, #0xFF
    bne rn_win
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
    lsls r0, r5, #3
    lsls r1, r5, #2
    adds r0, r0, r1
    ldr r1, litB_moves
    adds r0, r0, r1
    str r0, [sp, #20]           @ gBattleMoves[move]
    @ the name
    lsls r0, r5, #3
    lsls r1, r5, #2
    adds r0, r0, r1
    adds r3, r0, r5             @ move * 13
    ldr r0, litB_names
    adds r3, r3, r0
    movs r0, #6
    movs r1, #TITLE_Y
    ldr r2, litB_coltitle
    bl pr
    @ Power
    movs r0, #6
    movs r1, #ROW1_Y
    ldr r2, litB_collabel
    ldr r3, litB_spower
    bl pr
    ldr r0, [sp, #20]
    ldrb r0, [r0, #1]
    movs r1, #0
    bl number
    adds r3, r0, #0
    movs r0, #COL_V1
    movs r1, #ROW1_Y
    ldr r2, litB_colvalue
    bl pr
    @ Accuracy
    movs r0, #COL_2
    movs r1, #ROW1_Y
    ldr r2, litB_collabel
    ldr r3, litB_sacc
    bl pr
    ldr r0, [sp, #20]
    ldrb r0, [r0, #3]
    movs r1, #0
    bl number
    adds r3, r0, #0
    movs r0, #COL_V2
    movs r1, #ROW1_Y
    ldr r2, litB_colvalue
    bl pr
    @ Physical / Special / Status
    ldr r0, [sp, #20]
    ldrb r0, [r0, #10]
    cmp r0, #2
    bls rn_cat
    movs r0, #2
rn_cat:
    lsls r0, r0, #3
    ldr r1, litB_cats           @ {string, colours} per category
    adds r1, r1, r0
    ldr r3, [r1]
    ldr r2, [r1, #4]
    movs r0, #6
    movs r1, #ROW2_Y
    bl pr
    @ contact
    ldr r0, [sp, #20]
    ldrb r0, [r0, #8]
    ldr r3, litB_scontact
    lsls r0, r0, #31
    bne rn_contact
    ldr r3, litB_snocontact
rn_contact:
    movs r0, #COL_2
    movs r1, #ROW2_Y
    ldr r2, litB_colvalue
    bl pr
    @ Priority
    movs r0, #6
    movs r1, #ROW3_Y
    ldr r2, litB_collabel
    ldr r3, litB_sprio
    bl pr
    ldr r0, [sp, #20]
    movs r1, #7
    ldrsb r0, [r0, r1]
    bl signed
    adds r3, r0, #0
    movs r0, #COL_VP
    movs r1, #ROW3_Y
    ldr r2, litB_colvalue
    bl pr
    @ effect chance
    movs r0, #COL_2
    movs r1, #ROW3_Y
    ldr r2, litB_collabel
    ldr r3, litB_seffect
    bl pr
    ldr r0, [sp, #20]
    ldrb r0, [r0, #5]
    movs r1, #0x5B              @ "%"
    bl number
    adds r3, r0, #0
    movs r0, #COL_V2
    movs r1, #ROW3_Y
    ldr r2, litB_colvalue
    bl pr
    @ the 16x8 tiles of the window, row by row, into the two 8x8-tile sprites
    ldrh r0, [r4, #0x34]
    subs r0, #1
    bl sprite_ptrb
    adds r0, #0x40
    ldrh r0, [r0]               @ sheetTileStart
    lsls r0, r0, #5
    ldr r1, litB_objvram
    adds r5, r0, r1             @ r5 = half B's tiles (the move id is not needed any more)
    ldrh r0, [r4, #0x32]
    subs r0, #1
    bl sprite_ptrb
    adds r0, #0x40
    ldrh r0, [r0]
    lsls r0, r0, #5
    ldr r1, litB_objvram
    adds r4, r0, r1             @ r4 = half A's tiles (nor the tag sprite)
    movs r0, #8
    str r0, [sp, #20]           @ rows left
rn_row:
    adds r0, r7, #0
    adds r1, r4, #0
    bl copy256
    movs r0, #1
    lsls r0, r0, #8
    adds r0, r0, r7
    adds r1, r5, #0
    bl copy256
    movs r0, #1
    lsls r0, r0, #8
    adds r4, r4, r0
    adds r5, r5, r0
    lsls r0, r0, #1
    adds r7, r7, r0             @ the next row of the window: 16 tiles on
    ldr r0, [sp, #20]
    subs r0, #1
    str r0, [sp, #20]
    bne rn_row
    adds r0, r6, #0
    ldr r3, litB_removewindow
    bl call3b
rn_ret:
    add sp, #36
    pop {r4, r5, r6, r7, pc}

@ copy256(r0 = src, r1 = dst): 64 words
copy256:
    movs r2, #64
c2_loop:
    ldmia r0!, {r3}
    stmia r1!, {r3}
    subs r2, #1
    bne c2_loop
    bx lr

@ sprite_ptrb(r0 = id) -> r0 = &gSprites[id]
sprite_ptrb:
    lsls r1, r0, #4
    adds r1, r1, r0
    lsls r1, r1, #2
    ldr r0, litB_gsprites
    adds r0, r0, r1
    bx lr

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

@ number(r0 = value, r1 = suffix character or 0) -> r0 = "N" + suffix, or "---" for 0 (in the caller's frame)
number:
    push {r4, r5, r6, lr}
    adds r5, r1, #0
    cmp r0, #0
    bne nb_num
    ldr r0, litB_sdash
    pop {r4, r5, r6, pc}
nb_num:
    adds r1, r0, #0
    add r4, sp, #40             @ the caller's [sp+24] (16 bytes pushed here)
    adds r0, r4, #0
    movs r2, #0
    movs r3, #3
    ldr r6, litB_convert
    bl call6b                   @ ConvertIntToDecimalStringN(dst, value, left align, 3) -> the terminator
    cmp r5, #0
    beq nb_ret
    strb r5, [r0]
    movs r1, #0xFF
    strb r1, [r0, #1]
nb_ret:
    adds r0, r4, #0
    pop {r4, r5, r6, pc}

@ signed(r0 = signed value) -> r0 = "+N", "-N" or "0" (in the caller's frame)
signed:
    push {r4, r5, lr}
    add r4, sp, #36
    adds r5, r4, #0
    cmp r0, #0
    beq sg_num
    bgt sg_plus
    rsbs r0, r0, #0
    movs r1, #0xAE              @ "-"
    b sg_sign
sg_plus:
    movs r1, #0x2E              @ "+"
sg_sign:
    strb r1, [r5]
    adds r5, #1
sg_num:
    adds r1, r0, #0
    adds r0, r5, #0
    movs r2, #0
    movs r3, #3
    ldr r5, litB_convert
    bl call5b
    adds r0, r4, #0
    pop {r4, r5, pc}

call3b:
    bx r3
call4b:
    bx r4
call5b:
    bx r5
call6b:
    bx r6

.align 2
litB_wintpl:        .word WINTPL_ADDR
litB_addwindow:     .word 0x08003381
litB_removewindow:  .word 0x08003575
litB_gwindows:      .word 0x02020004
litB_panellz:       .word PANELLZ_ADDR
litB_lz77wram:      .word 0x082E7091    @ LZ77UnCompWram
litB_moves:         .word 0x09D86419    @ gBattleMoves (12 bytes: power +1, accuracy +3, effect chance +5,
                                        @ priority +7, flags +8 (bit 0 contact), split +10: 0 physical 1 special 2 status)
litB_names:         .word 0x09D30258    @ gMoveNames (13 bytes)
litB_coltitle:      .word COLTITLE_ADDR
litB_collabel:      .word COLLABEL_ADDR
litB_colvalue:      .word COLVALUE_ADDR
litB_spower:        .word SPOWER_ADDR
litB_sacc:          .word SACC_ADDR
litB_sprio:         .word SPRIO_ADDR
litB_seffect:       .word SEFFECT_ADDR
litB_scontact:      .word SCONTACT_ADDR
litB_snocontact:    .word SNOCONTACT_ADDR
litB_sdash:         .word SDASH_ADDR
litB_cats:          .word CATS_ADDR
litB_objvram:       .word 0x06010000
litB_gsprites:      .word 0x02020630
litB_addtext4:      .word 0x08199EED    @ AddTextPrinterParameterized4
litB_convert:       .word 0x08008CC1    @ ConvertIntToDecimalStringN
