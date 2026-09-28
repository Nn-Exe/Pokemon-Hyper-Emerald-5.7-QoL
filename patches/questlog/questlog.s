@ Quest Log (Hyper Emerald v5.7).
@ Using the Journal opens a screen of its own: every objective of one chapter as a checklist - a tick for
@ done, an arrow for the current one, a diamond for side objectives, "???" for what is still ahead. L/R or
@ Left/Right turn the chapter, Up/Down pick a row, A opens the row's full objective text, B goes back.
@
@ Nothing is decided here that the Journal does not decide: the rows come from the Journal's step table and
@ its own step_done / group_tail / append / u8dec, and the current row is the one the Journal would show.
@ Nothing is written to the save.
@
@ State: one AllocZeroed block. +0x000 BG0 tilemap buffer (0x800), then V:
@   V+0 page   V+1 top row   V+2 selected row   V+3 mode (0 list, 1 detail, 2 leaving)
@   V+4 detail page   V+5 detail pages   V+6 current step   V+7 first step after the last done anchor
@   V+0x08 detail page starts (8 words)   V+0x40 status per step (1 done, 2 current, 3 side quest left
@   behind, 4 side quest ahead, 5 ahead)   V+0xC8 the grid's done count per chapter   V+0xE0 scratch for
@   numbers   V+0xF0 a colour triple   V+0x100 the detail text   V+0x400 a picture (0x2000)
@   V+0x2400 its palette
@ Two more chapters are not the Journal's: Legends (the legendary and mythical Pokemon in National Dex order,
@ status from the Pokedex) and Key Items (ticked when in the Bag or its "got it" flag is set). A PAGES entry's
@ byte 3 says which: 0 Journal, 1 Legends, 2 Key Items (status 8: not got yet, but named), 3 Side Content
@ (ticked by its flag; also named). V+3 mode 3 is the chapter grid the log opens on. Both use 16-byte entries {id, flag, name, hint, where}.
.thumb

@ ---- the item --------------------------------------------------------------------------------------
@ ItemUseOutOfBattle_QuestLog(r0 = taskId): the Sinnoh Map's shape - from the Bag, the bag opens our screen
@ once it has faded out; from the field (SELECT), fade the field, then a task switches over.
item_use:
    push {r4, r5, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, iu_gtasks
    adds r5, r1, r0
    movs r1, #0xE
    ldrsh r0, [r5, r1]          @ data[3]: 1 when used from the field
    cmp r0, #1
    beq iu_field
    ldr r0, iu_bagmenu
    ldr r1, [r0]
    ldr r0, iu_cb2init
    str r0, [r1]                @ gBagMenu->newScreenCallback
    adds r0, r4, #0
    ldr r3, iu_closebag
    bl callr3
    pop {r4, r5, pc}
iu_field:
    ldr r0, iu_fieldcb
    ldr r1, iu_noscript
    str r1, [r0]
    movs r0, #1
    movs r1, #0
    ldr r3, iu_fadescreen
    bl callr3
    ldr r0, iu_waittask
    str r0, [r5]                @ this task now waits for the fade
    pop {r4, r5, pc}

@ Task_OpenQuestLogOnField(r0 = taskId)
wait_task:
    push {r4, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    ldr r0, iu_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    bne wt_ret
    ldr r3, iu_cleanupfield
    bl callr3
    ldr r0, iu_cb2init
    ldr r3, iu_setcb2
    bl callr3
    adds r0, r4, #0
    ldr r3, iu_destroytask
    bl callr3
wt_ret:
    pop {r4, pc}

callr3:
    bx r3
callr4:
    bx r4
callr5:
    bx r5
callr7:
    bx r7

.align 2
iu_gtasks:          .word 0x03005E00
iu_bagmenu:         .word 0x0203CE54    @ gBagMenu
iu_cb2init:         .word CB2_INIT_ADDR
iu_closebag:        .word 0x081AB8F9    @ Task_FadeAndCloseBagMenu
iu_fieldcb:         .word 0x03005DAC    @ gFieldCallback
iu_noscript:        .word 0x080AF6D5    @ FieldCB_ReturnToFieldNoScript
iu_fadescreen:      .word 0x080ABCD1
iu_waittask:        .word WAIT_TASK_ADDR
iu_palfade:         .word 0x02037FD4
iu_cleanupfield:    .word 0x08085D35    @ CleanupOverworldWindowsAndTilemaps
iu_setcb2:          .word 0x08000541
iu_destroytask:     .word 0x080A909D

@ ---- screen setup ----------------------------------------------------------------------------------
cb2_init:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    movs r0, #0
    ldr r3, ci_setvblank
    bl callr3
    movs r0, #0
    movs r1, #0
    ldr r3, ci_setgpureg
    bl callr3
    movs r0, #0
    ldr r3, ci_resetbgs
    bl callr3
    movs r0, #0
    ldr r1, ci_bgtemplates
    movs r2, #1
    ldr r3, ci_initbgs
    bl callr3
    ldr r0, ci_allocsize
    ldr r3, ci_alloczeroed
    bl callr3
    adds r7, r0, #0
    movs r0, #0
    adds r1, r7, #0
    ldr r3, ci_setbgtilemap
    bl callr3
    ldr r3, ci_resetpalfade
    bl callr3
    ldr r3, ci_resetsprites
    bl callr3
    ldr r3, ci_freespritepals
    bl callr3
    ldr r3, ci_resettasks
    bl callr3
    ldr r3, ci_deactprinters
    bl callr3
    ldr r0, ci_wintemplates
    ldr r3, ci_initwindows
    bl callr3
    ldr r0, ci_pal
    movs r1, #0xF0
    movs r2, #0x20
    ldr r3, ci_loadpalette
    bl callr3
    ldr r0, ci_pal              @ its first colour doubles as the backdrop
    movs r1, #0
    movs r2, #2
    ldr r3, ci_loadpalette
    bl callr3
    ldr r0, ci_mbpal            @ palette 14: the Master Ball's own colours (see draw_list)
    movs r1, #0xE0
    movs r2, #0x20
    ldr r3, ci_loadpalette
    bl callr3
    movs r0, #0
    ldr r1, ci_dispcnt
    ldr r3, ci_setgpureg
    bl callr3
    movs r0, #0
    ldr r3, ci_showbg
    bl callr3
    movs r0, #0x10              @ BG0HOFS
    movs r1, #0
    ldr r3, ci_setgpureg
    bl callr3
    movs r0, #0x12              @ BG0VOFS
    movs r1, #0
    ldr r3, ci_setgpureg
    bl callr3
    movs r0, #0x50              @ BLDCNT: no blending left over from the field
    movs r1, #0
    ldr r3, ci_setgpureg
    bl callr3
    movs r4, #0x80
    lsls r4, r4, #4
    adds r4, r7, r4             @ V
    adds r0, r4, #0
    bl compute
    ldrb r0, [r4, #6]           @ open on the chapter holding the current objective
    ldr r1, ci_pages
    movs r2, #0
ci_pg:
    cmp r2, #3
    beq ci_pgdone
    ldrb r3, [r1]
    ldrb r5, [r1, #1]
    adds r3, r3, r5
    cmp r0, r3
    blo ci_pgdone
    adds r1, #8
    adds r2, #1
    b ci_pg
ci_pgdone:
    strb r2, [r4]
    adds r0, r4, #0
    bl page_sel
    ldr r0, ci_task
    movs r1, #0
    ldr r3, ci_createtask
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    lsls r1, r0, #2
    adds r1, r1, r0
    lsls r1, r1, #3
    ldr r0, ci_gtasks
    adds r0, r0, r1
    str r7, [r0, #8]            @ data[0..1] = the block, freed on the way out
    movs r0, #3                 @ open on the chapter grid, the current chapter selected
    strb r0, [r4, #3]
    adds r0, r4, #0
    bl grid_count
    adds r0, r4, #0
    bl draw_header
    adds r0, r4, #0
    bl draw_grid
    adds r0, r4, #0
    bl draw_footer
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #16
    movs r3, #0
    ldr r5, ci_beginfade
    bl callr5
    ldr r0, ci_vblank
    ldr r3, ci_setvblank
    bl callr3
    ldr r0, ci_cb2main
    ldr r3, ci_setcb2
    bl callr3
    add sp, #8
    pop {r4, r5, r6, r7, pc}

.align 2
ci_setvblank:       .word 0x080006F1
ci_setgpureg:       .word 0x080010B5
ci_resetbgs:        .word 0x080017BD
ci_bgtemplates:     .word BGTEMPLATES_ADDR
ci_initbgs:         .word 0x080017E9
ci_allocsize:       .word 0x00002C40    @ tilemap 0x800, then V: state, texts, picture 0x2000, palette
ci_alloczeroed:     .word 0x08000B4D
ci_setbgtilemap:    .word 0x08002251
ci_resetpalfade:    .word 0x080A1A75
ci_resetsprites:    .word 0x08006975
ci_freespritepals:  .word 0x0800870D
ci_resettasks:      .word 0x080A8F51
ci_deactprinters:   .word 0x080045B1
ci_initwindows:     .word 0x080031C1
ci_wintemplates:    .word WINTEMPLATES_ADDR
ci_pal:             .word PAL_ADDR
ci_mbpal:           .word MBPAL_ADDR
ci_loadpalette:     .word 0x080A1939
ci_dispcnt:         .word 0x00000040
ci_showbg:          .word 0x08001B31
ci_pages:           .word PAGES_ADDR
ci_task:            .word TASK_ADDR
ci_createtask:      .word 0x080A8FB1
ci_gtasks:          .word 0x03005E00
ci_beginfade:       .word 0x080A1AD5
ci_vblank:          .word VBLANK_ADDR
ci_cb2main:         .word CB2_MAIN_ADDR
ci_setcb2:          .word 0x08000541

cb2_main:
    push {lr}
    ldr r3, cm_runtasks
    bl callr3
    ldr r3, cm_animsprites
    bl callr3
    ldr r3, cm_buildoam
    bl callr3
    ldr r3, cm_dotilemapcopies
    bl callr3
    ldr r3, cm_updatepalfade
    bl callr3
    pop {pc}

vblank:
    push {lr}
    ldr r3, cm_loadoam
    bl callr3
    ldr r3, cm_spritecopies
    bl callr3
    ldr r3, cm_transferpltt
    bl callr3
    pop {pc}

@ se_select: the menu click
se_select:
    push {lr}
    movs r0, #5
    ldr r3, cm_playse
    bl callr3
    pop {pc}

.align 2
cm_runtasks:        .word 0x080A910D
cm_animsprites:     .word 0x080069C1
cm_buildoam:        .word 0x08006A0D
cm_dotilemapcopies: .word 0x081999D1
cm_updatepalfade:   .word 0x080A1A1D
cm_loadoam:         .word 0x08007189
cm_spritecopies:    .word 0x0800742D
cm_transferpltt:    .word 0x080A19C1
cm_playse:          .word 0x080A37A5

@ ---- the rows' status ------------------------------------------------------------------------------
@ compute(r0 = V): the Journal's own rule - start after the last anchor that is done, the current objective
@ is the first one from there that is not - then a status per step for the list.
compute:
    push {r4, r5, r6, r7, lr}
    adds r7, r0, #0
    ldr r4, cp_steps
    movs r5, #0                 @ i
    movs r6, #0                 @ start
cp_p1:
    ldrb r0, [r4]
    cmp r0, #0xFF
    beq cp_p1done
    adds r0, r4, #0
    ldr r3, cp_stepdone
    bl callr3
    adds r1, r7, r5
    adds r1, #0x40
    strb r0, [r1]               @ 1 done / 0 not, for now
    cmp r0, #0
    beq cp_p1next
    ldrb r0, [r4, #1]
    cmp r0, #0
    beq cp_p1next
    adds r6, r5, #1
cp_p1next:
    adds r4, #16
    adds r5, #1
    b cp_p1
cp_p1done:                      @ r5 = number of steps
    adds r2, r6, #0
cp_p2:
    cmp r2, r5
    beq cp_p2done
    adds r1, r7, r2
    adds r1, #0x40
    ldrb r0, [r1]
    cmp r0, #0
    beq cp_p2done
    adds r2, #1
    b cp_p2
cp_p2done:
    strb r2, [r7, #6]           @ current (= number of steps once everything is done)
    strb r6, [r7, #7]
    ldr r4, cp_steps
    movs r3, #0
cp_p3:
    cmp r3, r5
    beq cp_final
    adds r1, r7, r3
    adds r1, #0x40
    ldrb r0, [r1]
    cmp r0, #0
    bne cp_next                 @ done
    ldrb r0, [r4, #1]           @ anchor?
    cmp r0, #0
    beq cp_na
    cmp r3, r6
    blo cp_w1                   @ an anchor before a later one that is done: passed, as the Journal sees it
cp_na:
    cmp r3, r2
    beq cp_w2
    blo cp_w3
    cmp r0, #0
    beq cp_w4
    movs r0, #5
    b cp_w
cp_w4:
    movs r0, #4
    b cp_w
cp_w3:
    movs r0, #3
    b cp_w
cp_w2:
    movs r0, #2
    b cp_w
cp_w1:
    movs r0, #1
cp_w:
    strb r0, [r1]
cp_next:
    adds r4, #16
    adds r3, #1
    b cp_p3
cp_final:                       @ the last row: the "everything is done" text
    adds r1, r7, r5
    adds r1, #0x40
    movs r0, #5
    cmp r2, r5
    bne cp_fw
    movs r0, #2
cp_fw:
    strb r0, [r1]
    pop {r4, r5, r6, r7, pc}

@ page_sel(r0 = V): select the current objective when it is on this chapter, else the first row, and scroll
@ so the selection sits near the middle
page_sel:
    push {r4, lr}
    adds r4, r0, #0
    ldrb r0, [r4]
    lsls r0, r0, #3
    ldr r1, cp_pages
    adds r0, r0, r1
    ldrb r1, [r0]               @ first
    ldrb r2, [r0, #1]           @ rows
    ldrb r3, [r0, #3]           @ the Legends chapter: no current row
    cmp r3, #0
    bne ps_zero
    ldrb r3, [r4, #6]
    cmp r3, r1
    blo ps_zero
    subs r3, r3, r1
    cmp r3, r2
    blo ps_have
ps_zero:
    movs r3, #0
ps_have:
    strb r3, [r4, #2]
    subs r3, #1
    subs r2, #LROWS             @ the last top row that still fills the list
    cmp r2, #0
    bge ps_max
    movs r2, #0
ps_max:
    cmp r3, r2
    ble ps_min
    adds r3, r2, #0
ps_min:
    cmp r3, #0
    bge ps_top
    movs r3, #0
ps_top:
    strb r3, [r4, #1]
    pop {r4, pc}

.align 2
cp_steps:           .word STEPS_ADDR
cp_stepdone:        .word STEPDONE_ADDR
cp_pages:           .word PAGES_ADDR

@ ---- drawing ---------------------------------------------------------------------------------------
@ print(r0 = window, r1 = x, r2 = y, r3 = string; [sp] = colours): drawn into the window's buffer only,
@ the caller copies the window when it is complete
print:
    push {r4, r5, lr}
    ldr r4, [sp, #12]
    sub sp, #0x14
    movs r5, #0
    str r5, [sp]
    str r5, [sp, #4]
    str r4, [sp, #8]
    movs r5, #0xFF              @ TEXT_SKIP_DRAW
    str r5, [sp, #0xC]
    str r3, [sp, #0x10]
    adds r3, r2, #0
    adds r2, r1, #0
    movs r1, #1
    ldr r4, dr_addtext4
    bl callr4
    add sp, #0x14
    pop {r4, r5, pc}

@ show(r0 = window): put it on the map and copy it all to video memory
show:
    push {r4, lr}
    adds r4, r0, #0
    ldr r3, dr_putwin
    bl callr3
    adds r0, r4, #0
    movs r1, #3
    ldr r3, dr_copywin
    bl callr3
    pop {r4, pc}

@ draw_list(r0 = V): the chapter as an Unbound-style mission log - four dark rows (a arrow on the selected one,
@ the name, a coloured status tag on the right), a divider with scroll arrows, then the info panel for the
@ selected row (draw_pane): a portrait, "Location:" and a short text. List-window coordinates: rows y 0-79 (five),
@ the panel 80-143 with the portrait flush under the list and the scroll arrows in its top right corner. Frame: [sp] [sp+4] call args, +8 selected?, +12 row, +16 status, +20 name x.
draw_list:
    push {r4, r5, r6, r7, lr}
    sub sp, #24
    adds r4, r0, #0
    movs r0, #1
    movs r1, #0xDD              @ the dark backdrop
    ldr r7, dr_fillwin
    bl callr7
    ldrb r0, [r4]
    lsls r0, r0, #3
    ldr r6, dr_pages
    adds r6, r6, r0
    movs r5, #0                 @ screen row
dl_row:
    cmp r5, #LROWS
    bne dl_r1
    b dl_marks
dl_r1:
    ldrb r0, [r4, #1]
    adds r0, r0, r5             @ row in the chapter
    ldrb r1, [r6, #1]
    cmp r0, r1
    blo dl_r2
    b dl_marks
dl_r2:
    str r0, [sp, #12]
    movs r2, #0
    ldrb r1, [r4, #2]
    cmp r0, r1
    bne dl_ns
    movs r0, #8                 @ the selected row: a lighter band and a arrow
    str r0, [sp]
    movs r0, #0
    lsls r1, r5, #4
    movs r2, #240
    movs r3, #15
    bl rect
    movs r0, #8
    str r0, [sp]
    str r0, [sp, #4]
    movs r0, #1
    ldr r1, dr_arrow
    movs r2, #3
    lsls r3, r5, #4
    adds r3, #4
    ldr r7, dr_blit
    bl callr7
    movs r2, #1
dl_ns:
    str r2, [sp, #8]
    movs r0, #10                @ a hairline under the row
    str r0, [sp]
    movs r0, #0
    lsls r1, r5, #4
    adds r1, #15
    movs r2, #240
    movs r3, #1
    bl rect
    adds r0, r4, #0
    ldr r1, [sp, #12]
    bl row_status
    str r0, [sp, #16]
    ldr r1, dr_namefg           @ the name: white, or grey while it is still "???"
    ldrb r1, [r1, r0]
    bl dl_colours
    str r0, [sp]
    adds r0, r4, #0
    ldr r1, [sp, #12]
    bl row_title
    adds r3, r0, #0
    movs r0, #1
    movs r1, #13
    str r1, [sp, #20]
    lsls r2, r5, #4
    bl print
    ldrb r0, [r6, #3]           @ Side Content: a red star after the name when its Pokemon is always shiny
    cmp r0, #3
    bne dl_tag
    adds r0, r4, #0
    ldr r1, [sp, #12]
    bl ext_entry
    ldrh r1, [r0]               @ marks, bit 0: shiny
    lsls r1, r1, #31
    beq dl_tag
    ldr r1, [r0, #4]
    movs r0, #1
    movs r2, #0
    ldr r7, dr_strwidth
    bl callr7
    ldr r2, [sp, #20]
    adds r2, r2, r0
    adds r2, #3
    movs r0, #8
    str r0, [sp]
    movs r0, #16
    str r0, [sp, #4]
    movs r0, #1
    ldr r1, dr_star
    lsls r3, r5, #4
    ldr r7, dr_blit
    bl callr7
dl_tag:
    ldr r0, [sp, #16]           @ the status tag, right-aligned
    lsls r0, r0, #2
    ldr r1, dr_tags
    ldr r7, [r1, r0]
    movs r0, #1
    adds r1, r7, #0
    movs r2, #0
    ldr r3, dr_strwidth
    bl callr3
    movs r1, #234
    subs r1, r1, r0
    str r1, [sp, #20]
    ldr r0, [sp, #16]
    ldr r1, dr_tagfg
    ldrb r1, [r1, r0]
    bl dl_colours
    str r0, [sp]
    movs r0, #1
    ldr r1, [sp, #20]
    lsls r2, r5, #4
    adds r3, r7, #0
    bl print
    adds r5, #1
    b dl_row
dl_marks:
    adds r0, r4, #0             @ the panel first: the arrows sit in its top right corner
    bl draw_pane
    ldrb r0, [r4, #1]
    cmp r0, #0
    beq dl_nou
    movs r0, #8
    str r0, [sp]
    str r0, [sp, #4]
    movs r0, #1
    ldr r1, dr_upicon
    movs r2, #214
    movs r3, #82
    ldr r7, dr_blit
    bl callr7
dl_nou:
    ldrb r0, [r4, #1]
    adds r0, #LROWS
    ldrb r1, [r6, #1]
    cmp r0, r1
    bhs dl_nod
    movs r0, #8
    str r0, [sp]
    str r0, [sp, #4]
    movs r0, #1
    ldr r1, dr_downicon
    movs r2, #226
    movs r3, #82
    ldr r7, dr_blit
    bl callr7
dl_nod:
    movs r0, #1
    bl show
    movs r0, #3                 @ the portrait on top of the panel
    bl show
    add sp, #24
    pop {r4, r5, r6, r7, pc}

@ dl_colours(r1 = foreground colour; [sp+12+8] of draw_list = selected?) -> r0 = a colour triple in scratch:
@ {background: 8 selected / 13 not, r1, shadow 10}. Called from draw_list only: reads its frame.
dl_colours:
    add r0, sp, #8              @ draw_list's frame (no push here)
    ldr r2, [r0]                @ selected?
    movs r3, #13
    cmp r2, #0
    beq dlc_bg
    movs r3, #8
dlc_bg:
    adds r0, r4, #0
    adds r0, #0xF0              @ V+0xF0: three bytes
    strb r3, [r0]
    strb r1, [r0, #1]
    movs r2, #10
    strb r2, [r0, #2]
    bx lr

@ draw_pane(r0 = V): the info panel for the selected row
draw_pane:
    push {r4, r5, r6, r7, lr}
    sub sp, #16
    adds r4, r0, #0
    movs r0, #13                @ the panel, y 80-143
    str r0, [sp]
    movs r0, #0
    movs r1, #80
    movs r2, #240
    movs r3, #64
    bl rect
    movs r0, #8                 @ a line between the list and the text
    str r0, [sp]
    movs r0, #76
    movs r1, #80
    movs r2, #164
    movs r3, #1
    bl rect
    movs r0, #9                 @ the portrait's white frame (window 3 inside shows the cream backdrop)
    str r0, [sp]
    movs r0, #7
    movs r1, #79
    movs r2, #66
    movs r3, #65
    bl rect
    adds r0, r4, #0
    ldrb r1, [r4, #2]
    bl row_status
    adds r6, r0, #0             @ status
    adds r0, r4, #0
    ldrb r1, [r4, #2]
    bl pane_entry
    adds r5, r0, #0             @ {kind, silhouette?, id, location, text, hidden text}
    cmp r6, #4                  @ a Journal step still ahead: no picture, "???"
    beq dp_hidden
    cmp r6, #5
    beq dp_hidden
    ldrb r0, [r5]
    ldrb r2, [r5, #1]           @ always a silhouette unless ... (the Gotta catch 'em all row: until status 9)
    cmp r2, #0
    beq dp_notmb
    movs r2, #1
    cmp r6, #9
    bne dp_pic
    movs r2, #0
    b dp_pic
dp_notmb:
    cmp r6, #7                  @ a legend not seen yet: its silhouette
    bne dp_pic
    movs r2, #1
dp_pic:
    ldrh r1, [r5, #2]
    adds r3, r4, #0
    bl portrait
    ldr r7, [r5, #4]            @ the location...
    ldr r6, [r5, #8]            @ ...and the text
    ldrb r0, [r4]               @ (a legend not seen yet: "???" and its hint)
    lsls r0, r0, #3
    ldr r1, dp_pages
    adds r0, r0, r1
    ldrb r0, [r0, #3]
    cmp r0, #1
    bne dp_text
    adds r0, r4, #0
    ldrb r1, [r4, #2]
    bl row_status
    cmp r0, #7
    bne dp_text
    ldr r7, dp_qqq
    ldr r6, [r5, #12]
    b dp_text
dp_hidden:
    movs r0, #0
    movs r1, #0
    movs r2, #0
    adds r3, r4, #0
    bl portrait
    ldr r7, dp_qqq
    ldr r6, dp_qqq
dp_text:
    ldr r0, dp_colgold          @ "Location:" in gold, the place in white
    str r0, [sp]
    movs r0, #1
    movs r1, #80
    movs r2, #81
    ldr r3, dp_loclabel
    bl print
    movs r0, #1
    ldr r1, dp_loclabel
    movs r2, #0
    ldr r3, dp_strwidth
    bl callr3
    adds r0, #83
    str r0, [sp, #8]
    ldr r0, dp_colwhite
    str r0, [sp]
    movs r0, #1
    ldr r1, [sp, #8]
    movs r2, #81
    adds r3, r7, #0
    bl print
    ldr r0, dp_colwhite
    str r0, [sp]
    movs r0, #1
    movs r1, #80
    movs r2, #97
    adds r3, r6, #0
    bl print
    add sp, #16
    pop {r4, r5, r6, r7, pc}

@ pane_entry(r0 = V, r1 = row in the chapter) -> r0 = the row's 16-byte panel entry. The Journal chapters
@ index one table by step (first + row); Legends, Key Items have one table each, and Side Content and
@ Badges share one (Badges start at their chapter's first row).
pane_entry:
    ldrb r2, [r0]
    lsls r2, r2, #3
    ldr r3, dp_pages
    adds r2, r2, r3
    ldrb r3, [r2, #3]
    lsls r3, r3, #2
    ldr r0, dp_panes
    ldr r0, [r0, r3]            @ PANES[type]
    ldrb r2, [r2]
    adds r1, r1, r2             @ by first + row: the Journal's steps, and Badges after Side Content
pe_row:
    lsls r1, r1, #4
    adds r0, r0, r1
    bx lr

@ portrait(r0 = kind 0 none / 1 Pokemon / 2 trainer / 3 item, r1 = id, r2 = silhouette?, r3 = V): the picture
@ into window 3 (8x8 tiles, BG palette 13), from the LZ77 data the game's own tables point at: decompressed into
@ V+0x400 (up to 0x2000 bytes: Castform keeps its four forms in one), the palette into V+0x2400. Kind 0 leaves the box empty (the cream backdrop).
portrait:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    adds r4, r0, #0
    adds r5, r1, #0
    adds r6, r2, #0
    movs r7, #0x80
    lsls r7, r7, #3
    adds r7, r3, r7             @ V+0x400
    movs r0, #3
    movs r1, #0
    ldr r3, pt_fillwin
    bl callr3
    cmp r4, #0
    beq pt_done
    lsls r0, r5, #3             @ the table entry {picture, palette}
    ldr r1, pt_monpics
    cmp r4, #1
    beq pt_pic
    ldr r1, pt_trpics
    cmp r4, #2
    beq pt_pic
    ldr r1, pt_items
pt_pic:
    ldr r0, [r1, r0]
    adds r1, r7, #0
    ldr r3, pt_lz77
    bl callr3
    cmp r4, #3
    beq pt_icon
    ldr r0, pt_gwindows         @ a 64x64 picture is laid out like the window's own tiles: copy it in
    ldr r1, [r0, #44]           @ gWindows[3].tileData
    adds r0, r7, #0
    movs r2, #0x80
    lsls r2, r2, #4             @ 2048 bytes
pt_copy:
    ldr r3, [r0]
    str r3, [r1]
    adds r0, #4
    adds r1, #4
    subs r2, #4
    bne pt_copy
    b pt_pal
pt_icon:
    movs r0, #24                @ an item icon: 24x24 in the middle
    str r0, [sp]
    str r0, [sp, #4]
    movs r0, #3
    adds r1, r7, #0
    movs r2, #20
    movs r3, #20
    ldr r4, pt_blit
    bl callr4
    movs r4, #3
pt_pal:
    ldr r0, pt_silpal           @ a silhouette: every colour dark
    cmp r6, #0
    bne pt_loadpal
    lsls r0, r5, #3
    ldr r1, pt_monpals
    cmp r4, #1
    beq pt_palent
    ldr r1, pt_trpals
    cmp r4, #2
    beq pt_palent
    ldr r1, pt_items
    adds r1, #4
pt_palent:
    ldr r0, [r1, r0]
    movs r1, #0x80
    lsls r1, r1, #6
    adds r1, r7, r1             @ V+0x2400
    ldr r3, pt_lz77
    bl callr3
    movs r0, #0x80
    lsls r0, r0, #6
    adds r0, r7, r0
pt_loadpal:
    movs r1, #0xD0              @ BG palette 13
    movs r2, #32
    ldr r3, pt_loadpalette
    bl callr3
pt_done:
    add sp, #8
    pop {r4, r5, r6, r7, pc}

.align 2
pt_fillwin:         .word 0x08003C49
pt_monpics:         .word MONPICS_ADDR
pt_trpics:          .word TRPICS_ADDR
pt_items:           .word ITEMICONS_ADDR
pt_monpals:         .word MONPALS_ADDR
pt_trpals:          .word TRPALS_ADDR
pt_lz77:            .word 0x082E7091    @ LZ77UnCompWram
pt_gwindows:        .word 0x02020004
pt_blit:            .word 0x080039A5
pt_silpal:          .word SILPAL_ADDR
pt_loadpalette:     .word 0x080A1939
dp_pages:           .word PAGES_ADDR
dp_panes:           .word PANES_ADDR
dp_qqq:             .word QQQ_ADDR
dp_colgold:         .word COLGOLD_ADDR
dp_colwhite:        .word COLWHITE_ADDR
dp_loclabel:        .word LOCLABEL_ADDR
dp_strwidth:        .word 0x08005ED9

.align 2
dr_addtext4:        .word 0x08199EED    @ AddTextPrinterParameterized4
dr_putwin:          .word 0x0800378D
dr_copywin:         .word 0x08003659
dr_fillwin:         .word 0x08003C49    @ FillWindowPixelBuffer
dr_fillrect:        .word 0x08003B65    @ FillWindowPixelRect
dr_blit:            .word 0x080039A5    @ BlitBitmapToWindow
dr_pages:           .word PAGES_ADDR
dr_upicon:          .word GUPICON_ADDR
dr_downicon:        .word GDOWNICON_ADDR
dr_arrow:           .word RIGHTICON_ADDR
dr_namefg:          .word NAMEFG_ADDR
dr_tagfg:           .word TAGFG_ADDR
dr_tags:            .word TAGS_ADDR
dr_strwidth:        .word 0x08005ED9    @ GetStringWidth
dr_star:            .word STAR_ADDR

@ draw_header(r0 = V): the chapter with arrows to the others and done/total, or in the detail view the
@ objective's title and which page of it this is
draw_header:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    adds r4, r0, #0
    movs r0, #0
    movs r1, #0x88
    ldr r7, dh_fillwin
    bl callr7
    ldrb r0, [r4, #3]
    cmp r0, #3
    bne dh_notgrid
    ldr r0, dh_colhead          @ the grid: just the title
    str r0, [sp]
    movs r0, #0
    movs r1, #8
    movs r2, #0
    ldr r3, dh_qltitle
    bl print
    b dh_show
dh_notgrid:
    cmp r0, #1
    bne dh_list
    b dh_detail
dh_list:
    ldrb r5, [r4]
    lsls r6, r5, #3
    ldr r0, dh_pages
    adds r6, r6, r0
    cmp r5, #0
    beq dh_noleft
    movs r0, #8
    str r0, [sp]
    str r0, [sp, #4]
    movs r0, #0
    ldr r1, dh_lefticon
    movs r2, #4
    movs r3, #4
    ldr r7, dh_blit
    bl callr7
dh_noleft:
    ldr r0, dh_colhead
    str r0, [sp]
    movs r0, #0
    movs r1, #16
    movs r2, #0
    ldr r3, [r6, #4]
    bl print
    cmp r5, #NLISTLAST
    beq dh_noright
    movs r0, #1
    ldr r1, [r6, #4]
    movs r2, #0
    ldr r7, dh_strwidth
    bl callr7
    adds r2, r0, #0
    adds r2, #20
    movs r0, #8
    str r0, [sp]
    str r0, [sp, #4]
    movs r0, #0
    ldr r1, dh_righticon
    movs r3, #4
    ldr r7, dh_blit
    bl callr7
dh_noright:
    ldrb r7, [r6, #1]           @ every row: only status 1 counts, which the closing rows never have
    movs r5, #0                 @ done
    movs r6, #0
dh_cnt:
    cmp r6, r7
    beq dh_cntd
    adds r0, r4, #0
    adds r1, r6, #0
    bl row_status
    cmp r0, #1
    bne dh_cn
    adds r5, #1
dh_cn:
    adds r6, #1
    b dh_cnt
dh_cntd:
    ldrb r7, [r4]               @ the total shown: the rows that count (not the Journal's or Legends' closing row)
    lsls r7, r7, #3
    ldr r0, dh_pages
    adds r7, r7, r0
    ldrb r7, [r7, #2]
    adds r0, r4, #0
    adds r0, #0xE0
    adds r1, r5, #0
    adds r5, r0, #0
    ldr r3, dh_u8dec
    bl callr3
    movs r1, #0xBA              @ '/'
    strb r1, [r0]
    adds r0, #1
    adds r1, r7, #0
    ldr r3, dh_u8dec
    bl callr3
    movs r1, #0xFF
    strb r1, [r0]
    b dh_right
dh_detail:
    adds r0, r4, #0
    ldrb r1, [r4, #2]
    bl row_title
    adds r3, r0, #0
    ldr r0, dh_colhead
    str r0, [sp]
    movs r0, #0
    movs r1, #8
    movs r2, #0
    bl print
    ldrb r1, [r4, #5]
    cmp r1, #1
    bls dh_show
    adds r0, r4, #0
    adds r0, #0xE0
    adds r5, r0, #0
    ldrb r1, [r4, #4]
    adds r1, #1
    ldr r3, dh_u8dec
    bl callr3
    movs r1, #0xBA
    strb r1, [r0]
    adds r0, #1
    ldrb r1, [r4, #5]
    ldr r3, dh_u8dec
    bl callr3
    movs r1, #0xFF
    strb r1, [r0]
dh_right:                       @ r5 = the number text, right-aligned
    movs r0, #1
    adds r1, r5, #0
    movs r2, #0
    ldr r7, dh_strwidth
    bl callr7
    movs r1, #232
    subs r1, r1, r0
    ldr r0, dh_colhead
    str r0, [sp]
    movs r0, #0
    movs r2, #0
    adds r3, r5, #0
    bl print
dh_show:
    movs r0, #0
    bl show
    add sp, #8
    pop {r4, r5, r6, r7, pc}

.align 2
dh_fillwin:         .word 0x08003C49
dh_pages:           .word PAGES_ADDR
dh_lefticon:        .word LEFTICON_ADDR
dh_righticon:       .word RIGHTICON_ADDR
dh_blit:            .word 0x080039A5
dh_colhead:         .word COLHEAD_ADDR
dh_strwidth:        .word 0x08005ED9    @ GetStringWidth
dh_u8dec:           .word U8DEC_ADDR
dh_qltitle:         .word QLTITLE_ADDR

@ draw_footer(r0 = V): the buttons that do something right now
draw_footer:
    push {r4, r5, lr}
    sub sp, #8
    adds r4, r0, #0
    ldrb r0, [r4, #3]           @ the list: no footer, the info panel reaches the bottom
    cmp r0, #0
    beq df_ret
    movs r0, #2
    movs r1, #0x88
    ldr r5, df_fillwin
    bl callr5
    ldr r3, df_hintgrid
    ldrb r0, [r4, #3]
    cmp r0, #3
    beq df_p
    ldr r3, df_hintlist
    cmp r0, #1
    bne df_p
    ldr r3, df_hintlast
    ldrb r0, [r4, #4]
    adds r0, #1
    ldrb r1, [r4, #5]
    cmp r0, r1
    bhs df_p
    ldr r3, df_hintmore
df_p:
    ldr r0, df_colfoot
    str r0, [sp]
    movs r0, #2
    movs r1, #8
    movs r2, #0
    bl print
    movs r0, #2
    bl show
df_ret:
    add sp, #8
    pop {r4, r5, pc}

@ open_detail(r0 = V): the selected objective's text as the Journal would say it - its message, and for a
@ group the progress line and what is missing - laid out for the pane: the "<chapter> - Next objective:"
@ line is dropped, every line break and scroll becomes a plain new line, and 8 lines make a page.
open_detail:
    push {r4, r5, r6, r7, lr}
    adds r4, r0, #0
    ldrb r0, [r4]
    lsls r0, r0, #3
    ldr r1, df_pages
    adds r0, r0, r1
    ldrb r0, [r0, #3]
    cmp r0, #0
    beq od_step
    adds r0, r4, #0
    ldrb r1, [r4, #2]
    bl row_status
    adds r5, r0, #0
    adds r0, r4, #0
    ldrb r1, [r4, #2]
    bl ext_entry
    adds r1, r0, #0
    adds r0, r5, #0
    ldr r2, [r1, #8]            @ the hint while you have not met it / got it
    cmp r0, #7
    beq od_leg
    ldr r2, [r1, #12]           @ where it is, once seen
od_leg:
    adds r0, r2, #0
    b od_go
od_step:
    ldrb r0, [r4]
    lsls r0, r0, #3
    ldr r1, df_pages
    ldrb r0, [r1, r0]
    ldrb r1, [r4, #2]
    adds r5, r0, r1
    lsls r5, r5, #4
    ldr r0, df_steps
    adds r5, r5, r0             @ the step (the terminator row for the closing text)
    ldr r0, df_strvar4
    ldr r1, [r5, #8]
    ldr r3, df_append
    bl callr3
    ldrb r1, [r5]
    cmp r1, #2
    bne od_term
    adds r1, r0, #0
    adds r0, r5, #0
    ldr r3, df_grouptail
    bl callr3
od_term:
    movs r1, #0xFF
    strb r1, [r0]
    ldr r0, df_strvar4
od_skip:
    ldrb r1, [r0]
    adds r0, #1
    cmp r1, #0xFE
    beq od_go
    cmp r1, #0xFF
    bne od_skip
    subs r0, #1
od_go:
    movs r1, #0x80
    lsls r1, r1, #1
    adds r1, r4, r1             @ out
    adds r6, r4, #0
    adds r6, #8
    str r1, [r6]
    movs r7, #1                 @ pages
    movs r5, #1                 @ lines on this page
od_loop:
    ldrb r2, [r0]
    adds r0, #1
    cmp r2, #0xFF
    beq od_end
    cmp r2, #0xFA
    blo od_char
    cmp r2, #0xFB
    bls od_nl
    cmp r2, #0xFE
    beq od_nl
od_char:
    strb r2, [r1]
    adds r1, #1
    b od_loop
od_nl:
    cmp r5, #8
    blo od_line
    movs r2, #0xFF
    strb r2, [r1]
    adds r1, #1
    cmp r7, #8
    beq od_fin
    adds r6, #4
    str r1, [r6]
    adds r7, #1
    movs r5, #1
    b od_loop
od_line:
    movs r2, #0xFE
    strb r2, [r1]
    adds r1, #1
    adds r5, #1
    b od_loop
od_end:
    strb r2, [r1]
od_fin:
    strb r7, [r4, #5]
    movs r0, #0
    strb r0, [r4, #4]
    movs r0, #1
    strb r0, [r4, #3]
    pop {r4, r5, r6, r7, pc}

@ draw_detail(r0 = V)
draw_detail:
    push {r4, lr}
    sub sp, #8
    adds r4, r0, #0
    movs r0, #1
    movs r1, #0x11
    ldr r3, df_fillwin
    bl callr3
    ldrb r0, [r4, #4]
    lsls r0, r0, #2
    adds r0, r4, r0
    ldr r3, [r0, #8]
    ldr r0, df_colnorm
    str r0, [sp]
    movs r0, #1
    movs r1, #8
    movs r2, #0
    bl print
    movs r0, #1
    bl show
    adds r0, r4, #0
    bl draw_header
    adds r0, r4, #0
    bl draw_footer
    add sp, #8
    pop {r4, pc}

.align 2
df_fillwin:         .word 0x08003C49
df_hintlist:        .word HINTLIST_ADDR
df_hintgrid:        .word HINTGRID_ADDR
df_hintmore:        .word HINTMORE_ADDR
df_hintlast:        .word HINTLAST_ADDR
df_colfoot:         .word COLHEAD_ADDR
df_colnorm:         .word COLORS_ADDR
df_pages:           .word PAGES_ADDR
df_steps:           .word STEPS_ADDR
df_strvar4:         .word 0x02021FC4
df_append:          .word APPEND_ADDR
df_grouptail:       .word GROUPTAIL_ADDR

@ ---- input ------------------------------------------------------------------------------------------
@ Task_QuestLog(r0 = taskId)
task:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    lsls r0, r0, #24
    lsrs r5, r0, #24
    lsls r1, r5, #2
    adds r1, r1, r5
    lsls r1, r1, #3
    ldr r0, tk_gtasks
    adds r0, r0, r1
    ldr r6, [r0, #8]            @ the block
    movs r4, #0x80
    lsls r4, r4, #4
    adds r4, r6, r4             @ V
    ldr r0, tk_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    beq tk_1
    b tk_ret                    @ fading: no input
tk_1:
    ldrb r0, [r4, #3]
    cmp r0, #2
    bne tk_2
    ldr r3, tk_freewindows
    bl callr3
    adds r0, r6, #0
    ldr r3, tk_free
    bl callr3
    adds r0, r5, #0
    ldr r3, tk_destroytask
    bl callr3
    ldr r0, tk_returnfield
    ldr r3, tk_setcb2
    bl callr3
    b tk_ret
tk_2:
    ldr r1, tk_gmain
    ldrh r6, [r1, #0x2E]        @ newKeys
    ldrh r7, [r1, #0x30]        @ newAndRepeatedKeys, so holding Up/Down keeps going
    cmp r0, #4
    bne tk_nocase
    adds r0, r4, #0             @ the badge case: its cursor frame pulses like the grid's
    bl grid_pulse
    adds r0, r4, #0
    adds r1, r6, #0
    adds r2, r7, #0
    bl case_input
    b tk_ret
tk_nocase:
    cmp r0, #3
    bne tk_notgrid
    adds r0, r4, #0
    bl grid_pulse
    adds r0, r4, #0
    adds r1, r6, #0
    adds r2, r7, #0
    bl grid_input
    b tk_ret
tk_notgrid:
    cmp r0, #1
    bne tk_list
    movs r0, #1                 @ detail: A turns the page, or goes back after the last
    tst r0, r6
    beq tk_db
    ldrb r0, [r4, #4]
    adds r0, #1
    ldrb r1, [r4, #5]
    cmp r0, r1
    bhs tk_back
    strb r0, [r4, #4]
    bl se_select
    adds r0, r4, #0
    bl draw_detail
    b tk_ret
tk_db:
    movs r0, #2
    tst r0, r6
    bne tk_back
    b tk_ret
tk_back:
    movs r0, #0
    strb r0, [r4, #3]
    bl se_select
    adds r0, r4, #0
    bl draw_header
    adds r0, r4, #0
    bl draw_list
    adds r0, r4, #0
    bl draw_footer
    b tk_ret
tk_list:
    movs r0, #0x40              @ Up
    tst r0, r7
    beq tk_down
    ldrb r0, [r4, #2]
    cmp r0, #0
    beq tk_ret1
    subs r0, #1
    strb r0, [r4, #2]
    ldrb r1, [r4, #1]
    cmp r0, r1
    bhs tk_moved
    strb r0, [r4, #1]
tk_moved:
    bl se_select
    adds r0, r4, #0
    bl draw_list
tk_ret1:
    b tk_ret
tk_down:
    movs r0, #0x80              @ Down
    tst r0, r7
    beq tk_page
    ldrb r0, [r4]
    lsls r0, r0, #3
    ldr r1, tk_pages
    adds r1, r1, r0
    ldrb r1, [r1, #1]
    ldrb r0, [r4, #2]
    adds r0, #1
    cmp r0, r1
    bhs tk_ret1
    strb r0, [r4, #2]
    ldrb r1, [r4, #1]
    adds r1, #LROWS
    cmp r0, r1
    blo tk_moved
    subs r0, #LROWS - 1
    strb r0, [r4, #1]
    b tk_moved
tk_page:
    ldr r0, tk_keysleft         @ Left or L
    tst r0, r6
    beq tk_right
    ldrb r0, [r4]
    cmp r0, #0
    beq tk_ret1
    subs r0, #1
    b tk_newpage
tk_right:
    ldr r0, tk_keysright        @ Right or R
    tst r0, r6
    beq tk_a
    ldrb r0, [r4]
    cmp r0, #NLISTLAST          @ Badges is a case, not a list: R stops at Side Content
    beq tk_ret1
    adds r0, #1
tk_newpage:
    strb r0, [r4]
    adds r0, r4, #0
    bl page_sel
    bl se_select
    adds r0, r4, #0
    bl draw_header
    adds r0, r4, #0
    bl draw_list
    b tk_ret
tk_a:
    movs r0, #1
    tst r0, r6
    beq tk_b
    adds r0, r4, #0
    ldrb r1, [r4, #2]
    bl row_status
    cmp r0, #4                  @ a Journal step still ahead: nothing to read yet
    beq tk_ret
    cmp r0, #5
    beq tk_ret
    bl se_select
    adds r0, r4, #0
    bl open_detail
    adds r0, r4, #0
    bl draw_detail
    b tk_ret
tk_b:
    movs r0, #2                 @ B: back to the chapter grid
    tst r0, r6
    beq tk_ret
    bl se_select
    movs r0, #3
    strb r0, [r4, #3]
    adds r0, r4, #0
    bl grid_count
    adds r0, r4, #0
    bl draw_header
    adds r0, r4, #0
    bl draw_grid
    adds r0, r4, #0
    bl draw_footer
tk_ret:
    add sp, #8
    pop {r4, r5, r6, r7, pc}

.align 2
tk_gtasks:          .word 0x03005E00
tk_palfade:         .word 0x02037FD4
tk_freewindows:     .word 0x08003605
tk_free:            .word 0x08000B61
tk_destroytask:     .word 0x080A909D
tk_returnfield:     .word 0x080860C9    @ CB2_ReturnToField, honouring gFieldCallback
tk_setcb2:          .word 0x08000541
tk_gmain:           .word 0x030022C0
tk_pages:           .word PAGES_ADDR
tk_keysleft:        .word 0x00000220
tk_keysright:       .word 0x00000110
tk_beginfade:       .word 0x080A1AD5

@ ---- the Start menu --------------------------------------------------------------------------------
@ A small framed box at the top left of the Start menu, "[R] Journal", where the Safari Zone shows its ball
@ count; R while the menu is up opens the Quest Log, and B there brings the menu back, as the Pokedex does.
@ The box is only drawn when neither the Safari nor the Battle Pyramid window wants that corner, and only
@ with the Journal in the Bag. Its window id sits in EWRAM scratch behind a magic word, and is only ever
@ removed when gWindows still holds our template there.

@ HandleStartMenuInput's first instruction (8-byte trampoline, so lr is live): replay its prologue first,
@ which saves lr, then look at the keys, then carry on into it with r0/r1/r4 as it left them.
hsi:
    push {r4, lr}
    ldr r4, sm_gmain
    ldrh r1, [r4, #0x2E]
    ldr r0, sm_rkey
    tst r0, r1
    beq hs_notr
    bl has_journal
    cmp r0, #0
    beq hs_cont
    movs r0, #5
    ldr r3, sm_playse
    bl callr3
    bl widget_remove
    ldr r0, sm_menucb
    ldr r1, sm_opencb
    str r1, [r0]                @ gMenuCallback: the menu task runs ours from the next frame
    movs r0, #1
    movs r1, #0
    ldr r3, sm_fadescreen
    bl callr3
    movs r0, #0                 @ FALSE: the menu stays up while the screen fades
    pop {r4}
    pop {r1}
    bx r1
hs_notr:
    movs r0, #0xB               @ A, B or START: whatever happens next, the box goes first
    tst r0, r1
    beq hs_cont
    bl widget_remove
hs_cont:
    ldrh r1, [r4, #0x2E]
    movs r0, #0x40
    ldr r3, sm_hsiback
    bx r3

@ the menu callback R installs: StartMenuPokedexCallback's shape
menu_cb:
    push {lr}
    ldr r0, sm_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    bne mc_wait
    ldr r3, sm_rainstop
    bl callr3
    ldr r3, sm_removeextra
    bl callr3
    ldr r3, sm_cleanupfield
    bl callr3
    ldr r0, sm_fieldcb2
    ldr r1, sm_openstartmenu
    str r1, [r0]                @ back from the Quest Log: the field reopens the Start menu
    ldr r0, sm_cb2init
    ldr r3, sm_setcb2
    bl callr3
    movs r0, #1
    pop {r1}
    bx r1
mc_wait:
    movs r0, #0
    pop {r1}
    bx r1

@ InitStartMenuStep's step 3 (the Safari / Pyramid windows) now starts here, reached by its jump table
case3:
    push {lr}
    bl show_widget
    pop {r0}
    ldr r0, sm_case3
    bx r0

.align 2
sm_gmain:           .word 0x030022C0
sm_rkey:            .word 0x00000100
sm_playse:          .word 0x080A37A5
sm_menucb:          .word 0x03005DF4    @ gMenuCallback
sm_opencb:          .word MENU_CB_ADDR
sm_fadescreen:      .word 0x080ABCD1
sm_hsiback:         .word 0x0809FACD    @ HandleStartMenuInput, after the 8 bytes the trampoline took
sm_palfade:         .word 0x02037FD4
sm_rainstop:        .word 0x080AC379    @ PlayRainStoppingSoundEffect
sm_removeextra:     .word 0x0809F775    @ RemoveExtraStartMenuWindows
sm_cleanupfield:    .word 0x08085D35
sm_fieldcb2:        .word 0x03005DB0    @ gFieldCallback2
sm_openstartmenu:   .word 0x080AF6A5    @ FieldCB_ReturnToFieldOpenStartMenu
sm_cb2init:         .word CB2_INIT_ADDR
sm_setcb2:          .word 0x08000541
sm_case3:           .word 0x0809F90D

@ has_journal -> r0 = 1 when the Journal is in the Bag
has_journal:
    push {lr}
    ldr r0, sw_item
    movs r1, #1
    ldr r3, sw_hasitem
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    pop {r1}
    bx r1

show_widget:
    push {r4, lr}
    sub sp, #12
    bl widget_remove            @ never two
    ldr r3, sw_safari
    bl callr3
    lsls r0, r0, #24
    bne sw_ret
    ldr r3, sw_pyramid
    bl callr3
    lsls r0, r0, #24
    bne sw_ret
    bl has_journal
    cmp r0, #0
    beq sw_ret
    ldr r0, sw_template
    ldr r3, sw_addwindow
    bl callr3
    lsls r0, r0, #24
    lsrs r4, r0, #24
    cmp r4, #0xFF
    beq sw_ret
    ldr r0, sw_scratch
    ldr r1, sw_magic
    str r1, [r0]
    strb r4, [r0, #4]
    adds r0, r4, #0
    ldr r3, sw_putwin
    bl callr3
    adds r0, r4, #0
    movs r1, #0
    ldr r3, sw_drawframe
    bl callr3
    adds r0, r4, #0
    movs r1, #0x11
    ldr r3, sw_fillwin
    bl callr3
    movs r0, #0                 @ y
    str r0, [sp]
    movs r0, #0xFF              @ TEXT_SKIP_DRAW
    str r0, [sp, #4]
    movs r0, #0
    str r0, [sp, #8]
    adds r0, r4, #0
    movs r1, #1
    ldr r2, sw_label
    movs r3, #2
    ldr r4, sw_addtext
    bl callr4
    ldr r0, sw_scratch
    ldrb r0, [r0, #4]
    movs r1, #2
    ldr r3, sw_copywin
    bl callr3
sw_ret:
    add sp, #12
    pop {r4, pc}

@ widget_remove: take the box down, if it is up
widget_remove:
    push {r4, r5, lr}
    ldr r5, sw_scratch
    ldr r0, [r5]
    ldr r1, sw_magic
    cmp r0, r1
    bne wr_ret
    movs r0, #0
    str r0, [r5]
    ldrb r4, [r5, #4]
    cmp r4, #32                 @ WINDOWS_MAX
    bhs wr_ret
    lsls r0, r4, #1             @ gWindows[id].window must still be our template
    adds r0, r0, r4
    lsls r0, r0, #2
    ldr r1, sw_gwindows
    adds r0, r0, r1
    ldr r1, sw_template
    ldr r2, [r0]
    ldr r3, [r1]
    cmp r2, r3
    bne wr_ret
    ldr r2, [r0, #4]
    ldr r3, [r1, #4]
    cmp r2, r3
    bne wr_ret
    adds r0, r4, #0
    movs r1, #0
    ldr r3, sw_clearframe
    bl callr3
    adds r0, r4, #0
    movs r1, #2
    ldr r3, sw_copywin
    bl callr3
    adds r0, r4, #0
    ldr r3, sw_removewin
    bl callr3
    movs r0, #0
    ldr r3, sw_schedcopy
    bl callr3
wr_ret:
    pop {r4, r5, pc}

.align 2
sw_item:            .word 0x0000016B
sw_hasitem:         .word 0x080D6725    @ CheckBagHasItem
sw_safari:          .word 0x080FC0A1    @ GetSafariZoneFlag
sw_pyramid:         .word 0x081A9E41    @ InBattlePyramid
sw_template:        .word WIDGET_TEMPLATE_ADDR
sw_addwindow:       .word 0x08003381
sw_scratch:         .word 0x02039E40    @ magic word + window id (EWRAM measured free)
sw_magic:           .word 0x474F4C51    @ "QLOG"
sw_putwin:          .word 0x0800378D
sw_drawframe:       .word 0x081973FD    @ DrawStdWindowFrame
sw_fillwin:         .word 0x08003C49
sw_label:           .word WIDGET_LABEL_ADDR
sw_addtext:         .word 0x080045D1    @ AddTextPrinterParameterized
sw_copywin:         .word 0x08003659
sw_gwindows:        .word 0x02020004
sw_clearframe:      .word 0x08198071    @ ClearStdWindowAndFrameToTransparent
sw_removewin:       .word 0x08003575
sw_schedcopy:       .word 0x081999BD    @ ScheduleBgCopyTilemapToVram

@ ---- rows --------------------------------------------------------------------------------------------
@ row_status(r0 = V, r1 = row in the chapter) -> r0 = status. Journal chapters: the computed status
@ (1 done, 2 current, 3 side left behind, 4 side ahead, 5 ahead). Legends: from the Pokedex, through the
@ game's own GetSetPokedexFlag (the hack's expanded dex): 1 caught, 6 seen, 7 not seen yet.
row_status:
    push {r4, lr}
    ldrb r2, [r0]
    lsls r2, r2, #3
    ldr r3, rs_pages
    adds r2, r2, r3
    ldrb r3, [r2, #3]
    cmp r3, #0
    bne rs_legend
    ldrb r2, [r2]
    adds r0, r0, r2
    adds r0, r0, r1
    adds r0, #0x40
    ldrb r0, [r0]
    pop {r4, pc}
rs_legend:
    cmp r3, #2
    beq rs_key
    cmp r3, #3
    beq rs_side
    cmp r1, #0                  @ the first row, "Gotta catch 'em all!": 9 once every legend is caught, else 7
    beq rs_all
    lsls r1, r1, #4
    ldr r2, rs_legends
    ldrh r4, [r2, r1]           @ National Dex number
    adds r0, r4, #0
    movs r1, #1                 @ FLAG_GET_CAUGHT
    ldr r3, rs_dexflag
    bl callr3
    lsls r0, r0, #24
    beq rs_notcaught
    movs r0, #1
    pop {r4, pc}
rs_notcaught:
    adds r0, r4, #0
    movs r1, #0                 @ FLAG_GET_SEEN
    ldr r3, rs_dexflag
    bl callr3
    lsls r0, r0, #24
    beq rs_unseen
    movs r0, #6
    pop {r4, pc}
rs_unseen:
    movs r0, #7
    pop {r4, pc}
rs_all:
    bl legend_all
    cmp r0, #0
    beq rs_unseen
    movs r0, #9
    pop {r4, pc}
rs_key:                         @ Key Items: in the Bag, or its "got it" flag (for items that leave the Bag)
    lsls r1, r1, #4
    ldr r2, rs_keys
    adds r4, r2, r1
    ldrh r0, [r4]
    movs r1, #1
    ldr r3, rs_hasitem
    bl callr3
    lsls r0, r0, #24
    bne rs_have
    ldrh r0, [r4, #2]
    cmp r0, #0
    beq rs_nothave
    ldr r3, rs_flagget
    bl callr3
    lsls r0, r0, #24
    bne rs_have
rs_nothave:                     @ not got yet: still named, dimmed, and A says where to get it
    movs r0, #8
    pop {r4, pc}
rs_have:
    movs r0, #1
    pop {r4, pc}
rs_side:                        @ Side Content and Badges: its script's own flag
    ldrb r2, [r2]               @ the chapter's first row in the shared table (Badges come after Side Content)
    adds r1, r1, r2
    lsls r1, r1, #4
    ldr r2, rs_sides
    adds r4, r2, r1
    ldrh r0, [r4, #2]
    ldr r3, rs_flagget
    bl callr3
    lsls r0, r0, #24
    beq rs_nothave
    ldrh r0, [r4]               @ marks bits 1-15: a second flag that must be set too (Snivy), or 0
    lsrs r0, r0, #1
    beq rs_have
    ldr r3, rs_flagget
    bl callr3
    lsls r0, r0, #24
    bne rs_have
    b rs_nothave

@ row_title(r0 = V, r1 = row in the chapter) -> r0 = what the row says: its title, or "???"
row_title:
    push {r4, r5, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    bl row_status
    ldr r1, rt_stshow
    ldrb r1, [r1, r0]
    cmp r1, #0
    beq rt_qqq
    ldrb r0, [r4]
    lsls r0, r0, #3
    ldr r1, rs_pages
    adds r0, r0, r1
    ldrb r1, [r0, #3]
    cmp r1, #0
    bne rt_legend
    ldrb r0, [r0]
    adds r0, r0, r5
    lsls r0, r0, #2
    ldr r1, rt_titles
    ldr r0, [r1, r0]
    pop {r4, r5, pc}
rt_legend:
    adds r0, r4, #0
    adds r1, r5, #0
    bl ext_entry
    ldr r0, [r0, #4]
    pop {r4, r5, pc}
rt_qqq:
    ldr r0, rt_qqqs
    pop {r4, r5, pc}

@ ext_entry(r0 = V, r1 = row) -> r0 = the row's 16-byte entry in the Legends or Key Items table
ext_entry:
    push {lr}
    ldrb r2, [r0]
    lsls r2, r2, #3
    ldr r3, rs_pages
    adds r2, r2, r3
    ldrb r3, [r2, #3]
    ldrb r2, [r2]               @ the chapter's first row: 0, except Badges (after Side Content in one table)
    adds r1, r1, r2
    lsls r1, r1, #4
    ldr r0, rs_legends
    cmp r3, #1
    beq ee_ret
    ldr r0, rs_keys
    cmp r3, #2
    beq ee_ret
    ldr r0, rs_sides
ee_ret:
    adds r0, r0, r1
    pop {r1}
    bx r1

@ legend_all() -> r0 = 1 when the Pokemon of every Legends row (1..NLEG; row 0 is this one) is caught, else 0
legend_all:
    push {r4, r5, lr}
    movs r4, #1
    ldr r5, rs_legends
la_loop:
    lsls r0, r4, #4
    ldrh r0, [r5, r0]           @ National Dex number
    movs r1, #1                 @ FLAG_GET_CAUGHT
    ldr r3, rs_dexflag
    bl callr3
    lsls r0, r0, #24
    beq la_ret
    adds r4, #1
    cmp r4, #NLEG
    bls la_loop
    movs r0, #1
la_ret:
    pop {r4, r5, pc}

.align 2
rs_pages:           .word PAGES_ADDR
rs_keys:            .word KEYS_ADDR
rs_sides:           .word SIDES_ADDR
rs_hasitem:         .word 0x080D6725    @ CheckBagHasItem
rs_flagget:         .word 0x0809D791    @ FlagGet (knows the hack's 0x4000+ flags)
rs_legends:         .word LEGENDS_ADDR
rs_dexflag:         .word 0x080C0665    @ GetSetPokedexFlag (a trampoline into the hack's own)
rt_stshow:          .word STSHOW_ADDR
rt_titles:          .word TITLES_ADDR
rt_qqqs:            .word QQQ_ADDR

@ ---- the chapter grid ------------------------------------------------------------------------------
@ draw_grid(r0 = V): a card per chapter on a dark backdrop, three across: a colour stripe and an icon in the
@ chapter's colour, its name, and done/total at the top right (green once complete), from the counts
@ grid_count saved. The selected card gets a gold border. V+0 is the cursor.
@ Frame: [sp] [sp+4] call args, +8 x, +12 y, +16 cursor, +20 done, +24 rows, +28 accent colour
draw_grid:
    push {r4, r5, r6, r7, lr}
    sub sp, #32
    adds r4, r0, #0
    ldrb r0, [r4]
    str r0, [sp, #16]
    movs r0, #1
    movs r1, #0xAA              @ the backdrop, colour 10 (the darkest navy)
    ldr r7, dg_fillwin
    bl callr7
    movs r5, #0
dg_loop:
    cmp r5, #NPAGES
    bne dg_cell
    b dg_done
dg_cell:
    adds r0, r5, #0             @ column, row
    movs r1, #0
dg_div:
    cmp r0, #3
    blo dg_divd
    subs r0, #3
    adds r1, #1
    b dg_div
dg_divd:
    movs r2, #79                @ x = 3 + column * 79
    muls r2, r0, r2
    adds r2, #3
    str r2, [sp, #8]
    movs r2, #42                @ y = 3 + row * 42
    muls r2, r1, r2
    adds r2, #3
    str r2, [sp, #12]
    ldr r0, dg_accent
    ldrb r0, [r0, r5]
    str r0, [sp, #28]
    ldr r0, [sp, #16]
    cmp r0, r5
    bne dg_card
    movs r0, #4                 @ selected: a border two pixels wide in colour 4, which grid_pulse cycles
    str r0, [sp]
    ldr r0, [sp, #8]
    subs r0, #2
    ldr r1, [sp, #12]
    subs r1, #2
    movs r2, #80
    movs r3, #43
    bl rect
dg_card:
    movs r0, #13                @ the card, dark navy like the list
    str r0, [sp]
    ldr r0, [sp, #8]
    ldr r1, [sp, #12]
    movs r2, #76
    movs r3, #39
    bl rect
    movs r2, #10                @ round it: the corners take the colour behind the card
    ldr r0, [sp, #16]
    cmp r0, r5
    bne dg_round
    movs r2, #4
dg_round:
    ldr r0, [sp, #8]
    ldr r1, [sp, #12]
    bl corners
    ldr r0, [sp, #28]           @ the colour stripe down the left
    str r0, [sp]
    ldr r0, [sp, #8]
    ldr r1, [sp, #12]
    adds r1, #3
    movs r2, #3
    movs r3, #33
    bl rect
    movs r0, #16                @ the icon
    str r0, [sp]
    str r0, [sp, #4]
    lsls r1, r5, #7
    ldr r0, dg_icons
    adds r1, r1, r0
    movs r0, #1
    ldr r2, [sp, #8]
    adds r2, #7
    ldr r3, [sp, #12]
    adds r3, #3
    ldr r7, dg_blit
    bl callr7
    ldr r0, dg_gcol             @ the name, white
    str r0, [sp]
    lsls r3, r5, #2
    ldr r0, dg_gnames
    ldr r3, [r0, r3]
    movs r0, #1
    ldr r1, [sp, #8]
    adds r1, #7
    ldr r2, [sp, #12]
    adds r2, #17
    bl print
    lsls r0, r5, #3             @ rows, and the done count grid_count saved
    ldr r1, dg_pages
    adds r0, r0, r1
    ldrb r0, [r0, #2]
    str r0, [sp, #24]
    adds r0, r4, r5
    adds r0, #0xC8
    ldrb r6, [r0]
    str r6, [sp, #20]
    adds r0, r4, #0             @ "done/rows"
    adds r0, #0xE0
    adds r1, r6, #0
    ldr r3, dg_u8dec
    bl callr3
    movs r1, #0xBA
    strb r1, [r0]
    adds r0, #1
    ldr r1, [sp, #24]
    ldr r3, dg_u8dec
    bl callr3
    movs r1, #0xFF
    strb r1, [r0]
    movs r0, #1                 @ right-aligned at the top right
    adds r1, r4, #0
    adds r1, #0xE0
    movs r2, #0
    ldr r7, dg_strwidth
    bl callr7
    adds r6, r0, #0
    ldr r0, dg_gcol
    adds r0, #4                 @ the count: grey
    ldr r1, [sp, #20]
    ldr r2, [sp, #24]
    cmp r1, r2
    bne dg_cntcol
    adds r0, #4                 @ complete: green
dg_cntcol:
    str r0, [sp]
    movs r0, #1
    ldr r1, [sp, #8]
    adds r1, #72
    subs r1, r1, r6
    ldr r2, [sp, #12]
    adds r2, #3
    adds r3, r4, #0
    adds r3, #0xE0
    bl print
    adds r5, #1
    b dg_loop
dg_done:
    movs r0, #1
    bl show
    movs r0, #2                 @ the footer sits on the list window's last two rows: back on top
    bl show
    add sp, #32
    pop {r4, r5, r6, r7, pc}

@ grid_count(r0 = V): count every chapter's done rows once, into V+0xC8.., when the grid is entered - moving
@ the cursor only redraws. Borrows V+0 (row_status reads the chapter from it) and puts it back.
grid_count:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    adds r4, r0, #0
    ldrb r0, [r4]
    str r0, [sp]
    movs r5, #0
gc2_loop:
    cmp r5, #NPAGES
    beq gc2_done
    strb r5, [r4]
    lsls r0, r5, #3
    ldr r1, dg_pages
    adds r0, r0, r1
    ldrb r0, [r0, #1]           @ every row: only status 1 counts, which the closing rows never have
    str r0, [sp, #4]
    movs r6, #0
    movs r7, #0
gc2_row:
    ldr r0, [sp, #4]
    cmp r7, r0
    beq gc2_save
    adds r0, r4, #0
    adds r1, r7, #0
    bl row_status
    cmp r0, #1
    bne gc2_next
    adds r6, #1
gc2_next:
    adds r7, #1
    b gc2_row
gc2_save:
    adds r0, r4, r5
    adds r0, #0xC8
    strb r6, [r0]
    adds r5, #1
    b gc2_loop
gc2_done:
    ldr r0, [sp]
    strb r0, [r4]
    add sp, #8
    pop {r4, r5, r6, r7, pc}

@ rect(r0 = x, r1 = y, r2 = w, r3 = h; [sp] = colour 0-15): fill a rectangle of the list window
rect:
    push {r4, r5, lr}
    ldr r4, [sp, #12]
    sub sp, #8
    str r2, [sp]
    str r3, [sp, #4]
    adds r3, r1, #0
    adds r2, r0, #0
    lsls r1, r4, #4
    orrs r1, r4
    movs r0, #1
    ldr r4, rc_fillrect
    bl callr4
    add sp, #8
    pop {r4, r5, pc}

@ corners(r0 = x, r1 = y, r2 = colour): round a 76 x 39 card by painting its corner pixels
corners:
    push {r4, r5, lr}
    sub sp, #4
    adds r4, r0, #0
    adds r5, r1, #0
    str r2, [sp]
    adds r0, r4, #0
    adds r1, r5, #0
    movs r2, #1
    movs r3, #1
    bl rect
    adds r0, r4, #0
    adds r0, #75
    adds r1, r5, #0
    movs r2, #1
    movs r3, #1
    bl rect
    adds r0, r4, #0
    adds r1, r5, #0
    adds r1, #38
    movs r2, #1
    movs r3, #1
    bl rect
    adds r0, r4, #0
    adds r0, #75
    adds r1, r5, #0
    adds r1, #38
    movs r2, #1
    movs r3, #1
    bl rect
    add sp, #4
    pop {r4, r5, pc}

.align 2
rc_fillrect:        .word 0x08003B65    @ FillWindowPixelRect

@ card_border(r0 = V, r1 = card, r2 = colour): the 2 px frame around one card and its rounded corners - all
@ that changes when the cursor moves. Redrawing every card took 12 frames (FillWindowPixelRect is per pixel);
@ this is four thin rects and four pixels.
card_border:
    push {r4, r5, r6, lr}
    sub sp, #8
    adds r6, r2, #0
    adds r0, r1, #0             @ card -> column, row
    movs r1, #0
cb_div:
    cmp r0, #3
    blo cb_divd
    subs r0, #3
    adds r1, #1
    b cb_div
cb_divd:
    movs r2, #79                @ x = 3 + column * 79
    muls r2, r0, r2
    adds r4, r2, #3
    movs r2, #42                @ y = 3 + row * 42
    muls r2, r1, r2
    adds r5, r2, #3
    str r6, [sp]
    subs r0, r4, #2             @ top
    subs r1, r5, #2
    movs r2, #80
    movs r3, #2
    bl rect
    str r6, [sp]
    subs r0, r4, #2             @ bottom
    adds r1, r5, #0
    adds r1, #39
    movs r2, #80
    movs r3, #2
    bl rect
    str r6, [sp]
    subs r0, r4, #2             @ left
    adds r1, r5, #0
    movs r2, #2
    movs r3, #39
    bl rect
    str r6, [sp]
    adds r0, r4, #0             @ right
    adds r0, #76
    adds r1, r5, #0
    movs r2, #2
    movs r3, #39
    bl rect
    adds r0, r4, #0             @ the corners take the frame's colour
    adds r1, r5, #0
    adds r2, r6, #0
    bl corners
    add sp, #8
    pop {r4, r5, r6, pc}

@ grid_input(r0 = V, r1 = newKeys, r2 = newAndRepeatedKeys)
grid_input:
    push {r4, r5, r6, lr}
    sub sp, #8
    adds r4, r0, #0
    adds r5, r1, #0
    adds r6, r2, #0
    ldrb r0, [r4]
    movs r1, #0x10              @ Right
    tst r1, r6
    beq gi_left
    cmp r0, #NLAST
    beq gi_ret
    adds r0, #1
    b gi_move
gi_left:
    movs r1, #0x20
    tst r1, r6
    beq gi_down
    cmp r0, #0
    beq gi_ret
    subs r0, #1
    b gi_move
gi_down:
    movs r1, #0x80
    tst r1, r6
    beq gi_up
    adds r0, #3
    cmp r0, #NPAGES
    bhs gi_ret
    b gi_move
gi_up:
    movs r1, #0x40
    tst r1, r6
    beq gi_a
    cmp r0, #3
    blo gi_ret
    subs r0, #3
gi_move:                        @ only the two frames change: the cards themselves are already drawn
    ldrb r6, [r4]
    strb r0, [r4]
    adds r5, r0, #0
    bl se_select
    adds r0, r4, #0
    adds r1, r6, #0
    movs r2, #13                @ the backdrop: erase the frame the cursor left
    bl card_border
    adds r0, r4, #0
    adds r1, r5, #0
    movs r2, #4                 @ the selected frame, which grid_pulse cycles
    bl card_border
    movs r0, #1
    bl show
    b gi_ret
gi_a:
    movs r1, #1                 @ A: open the chapter
    tst r1, r5
    beq gi_b
    ldrb r0, [r4]
    cmp r0, #NLAST              @ the last card, Badges: the badge case instead of a list
    bne gi_list
    bl se_select
    adds r0, r4, #0
    bl case_open
    b gi_ret
gi_list:
    ldr r0, gp_pal              @ colour 4 back to the lists' selection bar
    adds r0, #8
    movs r1, #0xF4
    movs r2, #2
    ldr r3, gp_loadpal
    bl callr3
    bl se_select
    adds r0, r4, #0
    bl page_sel
    movs r0, #0
    strb r0, [r4, #3]
    adds r0, r4, #0
    bl draw_header
    adds r0, r4, #0
    bl draw_list
    adds r0, r4, #0
    bl draw_footer
    b gi_ret
gi_b:
    movs r1, #2                 @ B: close the Quest Log
    tst r1, r5
    beq gi_ret
    bl se_select
    movs r0, #2
    strb r0, [r4, #3]
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #0
    movs r3, #16
    ldr r4, dg_beginfade
    bl callr4
gi_ret:
    add sp, #8
    pop {r4, r5, r6, pc}

.align 2
dg_fillwin:         .word 0x08003C49
dg_fillrect:        .word 0x08003B65
dg_gcol:            .word GCOL_ADDR
dg_pages:           .word PAGES_ADDR
dg_u8dec:           .word U8DEC_ADDR
dg_beginfade:       .word 0x080A1AD5
dg_accent:          .word ACCENT_ADDR
dg_icons:           .word GICONS_ADDR
dg_gnames:          .word GNAMES_ADDR
dg_blit:            .word 0x080039A5
dg_strwidth:        .word 0x08005ED9

@ grid_pulse(r0 = V): the selected card's border flashes - every 4 frames palette 15 colour 4 steps through
@ a gold-white-gold cycle (16 steps, PULSE). Only the palette changes: nothing is redrawn. V+0xD0 counts frames.
grid_pulse:
    push {r4, lr}
    adds r4, r0, #0
    adds r4, #0xD0
    ldrb r1, [r4]
    adds r1, #1
    strb r1, [r4]
    movs r2, #3
    tst r1, r2
    bne gp_ret
    lsrs r1, r1, #2
    movs r2, #15
    ands r1, r2
    lsls r1, r1, #1
    ldr r0, gp_pulse
    adds r0, r0, r1
    movs r1, #0xF4
    movs r2, #2
    ldr r3, gp_loadpal
    bl callr3
gp_ret:
    pop {r4, pc}

.align 2
gp_pulse:           .word PULSE_ADDR
gp_pal:             .word PAL_ADDR
gp_loadpal:         .word 0x080A1939    @ LoadPalette

@ ---- the badge case ------------------------------------------------------------------------------------
@ The Badges card opens a case like the DS one, not a list (mode 4): Sinnoh's eight badges (Hoenn's are on the
@ Trainer Card) on a dark panel, four across, in colour with a sparkle once earned, a silhouette before. Each badge is a 4x4-tile
@ window of its own with its own BG palette (1-8, which nothing else here uses), so every badge keeps its
@ colours; the panel, the cursor frame and the line of text under the badges are window 1. The D-pad moves
@ the frame, B goes back to the grid.
@ V+0xD5 cursor 0-7, V+0xD8..0xDF the badge windows' ids.

@ case_open(r0 = V): make the eight badge windows, then draw the case
case_open:
    push {r4, r5, lr}
    adds r4, r0, #0
    movs r0, #4
    strb r0, [r4, #3]
    movs r5, #0
co_win:
    lsls r0, r5, #3
    ldr r1, bc_wintpl
    adds r0, r0, r1
    ldr r3, bc_addwin
    bl callr3
    adds r1, r4, r5
    adds r1, #0xD8
    strb r0, [r1]
    adds r5, #1
    cmp r5, #8
    bne co_win
    adds r0, r4, #0
    bl case_draw
    pop {r4, r5, pc}

@ case_entry(r0 = V, r1 = slot 0-7) -> r0 = that badge's 32-byte entry:
@ {flag u16, 0, art, silhouette, palette, name, earned text, not-yet text, 0}
case_entry:
    lsls r2, r1, #5
    ldr r0, bc_case
    adds r0, r0, r2
    bx lr

@ case_draw(r0 = V): the whole case - header, panel, the eight badges, the frame, the text, the footer
case_draw:
    push {r4, r5, r6, r7, lr}
    sub sp, #16
    adds r4, r0, #0
    movs r0, #0                 @ header: "Sinnoh Badges", earned/8 at the right
    movs r1, #0x88
    ldr r3, bc_fillwin
    bl callr3
    ldr r0, bc_colhead
    str r0, [sp]
    movs r0, #0
    movs r1, #8
    movs r2, #0
    ldr r3, bc_title
    bl print
    movs r6, #0                 @ earned
    movs r7, #0
cd_cnt:
    adds r0, r4, #0
    adds r1, r7, #0
    bl case_entry
    ldrh r0, [r0]
    ldr r3, bc_flagget
    bl callr3
    lsls r0, r0, #24
    beq cd_cn
    adds r6, #1
cd_cn:
    adds r7, #1
    cmp r7, #8
    bne cd_cnt
    adds r0, r4, #0
    adds r0, #0xE0
    adds r1, r6, #0
    ldr r3, bc_u8dec
    bl callr3
    movs r1, #0xBA              @ "/8"
    strb r1, [r0]
    movs r1, #0xA9
    strb r1, [r0, #1]
    movs r1, #0xFF
    strb r1, [r0, #2]
    movs r0, #1
    adds r1, r4, #0
    adds r1, #0xE0
    movs r2, #0
    ldr r3, bc_strwidth
    bl callr3
    movs r1, #232
    subs r1, r1, r0
    ldr r0, bc_colhead
    str r0, [sp]
    movs r0, #0
    movs r2, #0
    adds r3, r4, #0
    adds r3, #0xE0
    bl print
    movs r0, #0
    bl show
    movs r0, #1                 @ window 1: the backdrop, then the panel with rounded corners
    movs r1, #0xAA
    ldr r3, bc_fillwin
    bl callr3
    movs r0, #13
    str r0, [sp]
    movs r0, #8
    movs r1, #4
    movs r2, #224
    movs r3, #112
    bl rect
    movs r0, #10
    str r0, [sp]
    movs r0, #8
    movs r1, #4
    movs r2, #1
    movs r3, #1
    bl rect
    movs r0, #10
    str r0, [sp]
    movs r0, #231
    movs r1, #4
    movs r2, #1
    movs r3, #1
    bl rect
    movs r0, #10
    str r0, [sp]
    movs r0, #8
    movs r1, #115
    movs r2, #1
    movs r3, #1
    bl rect
    movs r0, #10
    str r0, [sp]
    movs r0, #231
    movs r1, #115
    movs r2, #1
    movs r3, #1
    bl rect
    movs r5, #0                 @ the badges: art or silhouette into each window, its palette to BG 1 + slot
cd_badge:
    adds r0, r4, #0
    adds r1, r5, #0
    bl case_entry
    adds r6, r0, #0
    ldrh r0, [r6]
    ldr r3, bc_flagget
    bl callr3
    lsls r0, r0, #24
    ldr r0, [r6, #8]            @ not yet: the silhouette
    beq cd_src
    ldr r0, [r6, #4]            @ earned: the badge
cd_src:
    adds r1, r4, r5
    adds r1, #0xD8
    ldrb r1, [r1]
    lsls r2, r1, #1
    adds r2, r2, r1
    lsls r2, r2, #2             @ gWindows[id] (12 bytes each)
    ldr r3, bc_gwindows
    adds r2, r2, r3
    ldr r1, [r2, #8]            @ .tileData
    movs r2, #0x80
    lsls r2, r2, #2             @ 512 bytes
cd_copy:
    ldr r3, [r0]
    str r3, [r1]
    adds r0, #4
    adds r1, #4
    subs r2, #4
    bne cd_copy
    ldr r0, [r6, #12]
    adds r1, r5, #1
    lsls r1, r1, #4
    movs r2, #32
    ldr r3, bc_loadpal
    bl callr3
    adds r5, #1
    cmp r5, #8
    bne cd_badge
    adds r0, r4, #0
    movs r1, #0xD5
    ldrb r1, [r4, r1]
    movs r2, #4                 @ the frame in colour 4, which grid_pulse cycles
    bl case_frame
    adds r0, r4, #0
    bl case_text
    adds r0, r4, #0
    bl case_show
    movs r0, #2                 @ footer
    movs r1, #0x88
    ldr r3, bc_fillwin
    bl callr3
    ldr r0, bc_colhead
    str r0, [sp]
    movs r0, #2
    movs r1, #8
    movs r2, #0
    ldr r3, bc_hint
    bl print
    movs r0, #2
    bl show
    add sp, #16
    pop {r4, r5, r6, r7, pc}

.align 2
bc_case:            .word CASE_ADDR
bc_wintpl:          .word CASEWIN_ADDR
bc_addwin:          .word 0x08003381    @ AddWindow
bc_fillwin:         .word 0x08003C49    @ FillWindowPixelBuffer
bc_colhead:         .word COLHEAD_ADDR
bc_title:           .word CASETITLE_ADDR
bc_strwidth:        .word 0x08005ED9    @ GetStringWidth
bc_flagget:         .word 0x0809D791    @ FlagGet
bc_u8dec:           .word U8DEC_ADDR
bc_gwindows:        .word 0x02020004
bc_loadpal:         .word 0x080A1939    @ LoadPalette
bc_hint:            .word HINTCASE_ADDR

@ case_show(r0 = V): window 1, then the badge windows and the footer on top of it (they share the tilemap of
@ BG0, and window 1 reaches down under the footer)
case_show:
    push {r4, r5, lr}
    adds r4, r0, #0
    movs r0, #1
    bl show
    movs r5, #0
csh_loop:
    adds r0, r4, r5
    adds r0, #0xD8
    ldrb r0, [r0]
    bl show
    adds r5, #1
    cmp r5, #8
    bne csh_loop
    movs r0, #2
    bl show
    pop {r4, r5, pc}

@ case_frame(r0 = V, r1 = slot, r2 = colour): the 2 px frame 3 px outside a badge. Slot -> column, row; the
@ badge windows sit at tiles x 2 + 7 * column, y 4 + 6 * row, i.e. window 1 pixels 16 + 56c, 16 + 48r.
case_frame:
    push {r4, r5, r6, lr}
    sub sp, #8
    adds r6, r2, #0
    movs r0, #3
    ands r0, r1
    lsrs r1, r1, #2
    movs r2, #56
    muls r0, r2, r0
    adds r0, #13
    adds r4, r0, #0
    movs r2, #48
    muls r1, r2, r1
    adds r1, #13
    adds r5, r1, #0
    str r6, [sp]
    adds r0, r4, #0             @ top
    adds r1, r5, #0
    movs r2, #38
    movs r3, #2
    bl rect
    str r6, [sp]
    adds r0, r4, #0             @ bottom
    adds r1, r5, #0
    adds r1, #36
    movs r2, #38
    movs r3, #2
    bl rect
    str r6, [sp]
    adds r0, r4, #0             @ left
    adds r1, r5, #0
    movs r2, #2
    movs r3, #38
    bl rect
    str r6, [sp]
    adds r0, r4, #0             @ right
    adds r0, #36
    adds r1, r5, #0
    movs r2, #2
    movs r3, #38
    bl rect
    add sp, #8
    pop {r4, r5, r6, pc}

@ case_text(r0 = V): under the badges, the selected one: its name (gold) and who you won it from (white), or
@ before it is earned the name and its Gym, both dim
case_text:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    adds r4, r0, #0
    movs r0, #13
    str r0, [sp]
    movs r0, #12
    movs r1, #98
    movs r2, #216
    movs r3, #15
    bl rect
    adds r0, r4, #0
    movs r1, #0xD5
    ldrb r1, [r4, r1]
    bl case_entry
    adds r5, r0, #0
    ldrh r0, [r5]
    ldr r3, bi_flagget
    bl callr3
    lsls r0, r0, #24
    ldr r6, bi_colgold
    ldr r7, [r5, #20]
    bne ct_print
    ldr r6, bi_coldim
    ldr r7, [r5, #24]
ct_print:
    str r6, [sp]
    movs r0, #1
    movs r1, #16
    movs r2, #98
    ldr r3, [r5, #16]
    bl print
    movs r0, #1
    ldr r1, [r5, #16]
    movs r2, #0
    ldr r3, bi_strwidth
    bl callr3
    adds r0, #22
    adds r1, r0, #0
    ldr r0, bi_coldim
    cmp r6, r0
    beq ct_col
    ldr r0, bi_colwhite
ct_col:
    str r0, [sp]
    movs r0, #1
    movs r2, #98
    adds r3, r7, #0
    bl print
    add sp, #8
    pop {r4, r5, r6, r7, pc}

@ case_input(r0 = V, r1 = newKeys, r2 = newAndRepeatedKeys)
case_input:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    adds r4, r0, #0
    adds r5, r1, #0
    adds r6, r2, #0
    movs r0, #0xD5
    ldrb r7, [r4, r0]
    adds r0, r7, #0
    movs r1, #0x10              @ Right, within the row
    tst r1, r6
    beq bi_left
    movs r1, #3
    ands r1, r7
    cmp r1, #3
    beq bi_keys
    adds r0, #1
    b bi_move
bi_left:
    movs r1, #0x20
    tst r1, r6
    beq bi_down
    movs r1, #3
    ands r1, r7
    cmp r1, #0
    beq bi_keys
    subs r0, #1
    b bi_move
bi_down:
    movs r1, #0x80
    tst r1, r6
    beq bi_up
    cmp r7, #4
    bhs bi_keys
    adds r0, #4
    b bi_move
bi_up:
    movs r1, #0x40
    tst r1, r6
    beq bi_keys
    cmp r7, #4
    blo bi_keys
    subs r0, #4
bi_move:
    movs r1, #0xD5
    strb r0, [r4, r1]
    bl se_select
    adds r0, r4, #0
    adds r1, r7, #0
    movs r2, #13                @ the colour of the panel: the old frame goes
    bl case_frame
    adds r0, r4, #0
    movs r1, #0xD5
    ldrb r1, [r4, r1]
    movs r2, #4
    bl case_frame
    adds r0, r4, #0
    bl case_text
    adds r0, r4, #0
    bl case_show
    b bi_ret
bi_keys:
    movs r0, #2                 @ B: the badge windows go, back to the grid
    tst r0, r5
    beq bi_ret
    bl se_select
    movs r5, #0
bi_rm:
    adds r0, r4, r5
    adds r0, #0xD8
    ldrb r0, [r0]
    ldr r3, bi_removewin
    bl callr3
    adds r5, #1
    cmp r5, #8
    bne bi_rm
    movs r0, #3
    strb r0, [r4, #3]
    adds r0, r4, #0
    bl grid_count
    adds r0, r4, #0
    bl draw_header
    adds r0, r4, #0
    bl draw_grid
    adds r0, r4, #0
    bl draw_footer
bi_ret:
    add sp, #8
    pop {r4, r5, r6, r7, pc}

.align 2
bi_flagget:         .word 0x0809D791
bi_strwidth:        .word 0x08005ED9
bi_colgold:         .word COLGOLD_ADDR
bi_coldim:          .word COLDIM_ADDR
bi_colwhite:        .word COLWHITE_ADDR
bi_removewin:       .word 0x08003575    @ RemoveWindow
