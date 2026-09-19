@ DexNav screen (Hyper Emerald v5.7): start menu -> DexNav lists every wild Pokemon of the current map
@ (Land / Water / Rock / Fish, unique species with level ranges and icons), 7 per page, LEFT/RIGHT or L/R
@ to page, B to return to the start menu. Read-only: it only reads the encounter tables and save location.
@ Entered exactly like the Pokedex from the start menu, left via CB2_ReturnToFieldWithOpenMenu.
@ Three literal pools (A/B/C) because Thumb-1 pc-relative loads only reach 1020 bytes forward.
.thumb

@ ---- start menu -----------------------------------------------------------------------------------
@ Replaces the tail of BuildNormalStartMenu: "movs r0,#7; bl AddStartMenuAction; pop {r0}" (the return
@ address is on the stack). Adds our action (index 13 of the copied table) before Exit.
menu_stub:
    ldr r0, lit_flag_dex        @ FLAG_SYS_POKEDEX_GET: no Pokedex yet, no DexNav
    ldr r3, lit_flagget
    bl callr3
    lsls r0, r0, #24
    beq ms_exit
    movs r0, #13
    ldr r3, lit_addaction
    bl callr3
ms_exit:
    movs r0, #7
    ldr r3, lit_addaction
    bl callr3
    pop {r0}
    bx r0

@ bool8 StartMenuDexNavCallback(void): mirror of StartMenuPokedexCallback
menu_callback:
    push {lr}
    ldr r0, lit_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    beq mc_go
    movs r0, #0                 @ fade still running
    pop {pc}
mc_go:
    ldr r3, lit_rainsound
    bl callr3
    ldr r3, lit_removeextra
    bl callr3
    ldr r3, lit_cleanupfield
    bl callr3
    ldr r0, lit_cb2_init
    ldr r3, lit_setcb2
    bl callr3
    movs r0, #1
    pop {pc}

@ ---- screen ---------------------------------------------------------------------------------------
cb2_init:
    push {r4, r5, lr}
    sub sp, #0xC
    movs r0, #0
    ldr r3, lit_setvblank
    bl callr3
    movs r0, #0                 @ REG_DISPCNT = 0
    movs r1, #0
    ldr r3, lit_setgpureg
    bl callr3
    movs r0, #0
    ldr r3, lit_resetbgs
    bl callr3
    movs r0, #0
    ldr r1, lit_bgtemplate
    movs r2, #1
    ldr r3, lit_initbgs
    bl callr3
    movs r0, #0x80
    lsls r0, r0, #4             @ 0x800 byte tilemap buffer
    ldr r3, lit_alloczeroed
    bl callr3
    adds r4, r0, #0
    movs r0, #0
    adds r1, r4, #0
    ldr r3, lit_setbgtilemap
    bl callr3
    ldr r3, lit_resetpalfade
    bl callr3
    ldr r3, lit_resetsprites
    bl callr3
    ldr r3, lit_freespritepals
    bl callr3
    ldr r3, lit_resettasks
    bl callr3
    ldr r3, lit_deactprinters
    bl callr3
    ldr r0, lit_wintemplates
    ldr r3, lit_initwindows
    bl callr3
    ldr r0, lit_textpal
    movs r1, #0xF0
    movs r2, #0x20
    ldr r3, lit_loadpalette
    bl callr3
    ldr r0, lit_backdrop
    movs r1, #0
    movs r2, #2
    ldr r3, lit_loadpalette
    bl callr3
    movs r0, #0                 @ REG_DISPCNT = OBJ on, 1D mapping (BG0 added by ShowBg)
    ldr r1, lit_dispcnt
    ldr r3, lit_setgpureg
    bl callr3
    movs r0, #0
    ldr r3, lit_showbg
    bl callr3
    ldr r0, lit_task
    movs r1, #0
    ldr r3, lit_createtask
    bl callr3
    lsls r0, r0, #24
    lsrs r5, r0, #24            @ task id
    bl task_data                @ r0 = &data[0]
    movs r1, #0
    strh r1, [r0]               @ data[0] = page
    strh r1, [r0, #4]           @ data[2] = state
    strh r4, [r0, #6]           @ data[3..4] = tilemap buffer
    lsrs r1, r4, #16
    strh r1, [r0, #8]
    movs r0, #0
    bl draw_page
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #16
    movs r3, #0
    ldr r4, lit_beginfade
    bl callr4                   @ fade in from black
    ldr r0, lit_vblank
    ldr r3, lit_setvblank
    bl callr3
    ldr r0, lit_cb2_main
    ldr r3, lit_setcb2
    bl callr3
    add sp, #0xC
    pop {r4, r5, pc}

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

@ task_data: r5 = task id -> r0 = &gTasks[r5].data[0]; clobbers r1
task_data:
    lsls r1, r5, #2
    adds r1, r1, r5
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r0, r0, r1
    adds r0, #8
    bx lr

@ Task_DexNav(r0 = taskId)
task:
    push {r4, r5, r6, lr}
    sub sp, #4
    lsls r0, r0, #24
    lsrs r5, r0, #24
    ldr r0, lit_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    bne t_ret                   @ fading: ignore input
    bl task_data
    adds r4, r0, #0
    ldrh r0, [r4, #4]
    cmp r0, #0
    bne t_leave
    ldr r0, lit_gmain
    ldrh r6, [r0, #0x2E]        @ newKeys
    movs r0, #2                 @ B
    tst r0, r6
    bne t_exit
    ldr r0, lit_key_right       @ RIGHT | R
    tst r0, r6
    bne t_next
    ldr r0, lit_key_left        @ LEFT | L
    tst r0, r6
    bne t_prev
    b t_ret
t_next:
    bl page_count               @ r0 = pages
    cmp r0, #2
    blo t_ret
    ldrh r1, [r4]
    adds r1, #1
    cmp r1, r0
    blo t_setpage
    movs r1, #0
    b t_setpage
t_prev:
    bl page_count
    cmp r0, #2
    blo t_ret
    ldrh r1, [r4]
    cmp r1, #0
    bne t_dec
    adds r1, r0, #0
t_dec:
    subs r1, #1
t_setpage:
    strh r1, [r4]
    movs r0, #5                 @ SE_SELECT
    ldr r3, lit_playse
    bl callr3
    ldrh r0, [r4]
    bl draw_page
    b t_ret
t_exit:
    movs r0, #5
    ldr r3, lit_playse
    bl callr3
    movs r0, #1
    strh r0, [r4, #4]           @ state = leaving
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #0
    movs r3, #16
    ldr r4, lit_beginfade
    bl callr4                   @ fade out to black
    b t_ret
t_leave:
    ldr r3, lit_freewindows
    bl callr3
    ldrh r0, [r4, #6]
    ldrh r1, [r4, #8]
    lsls r1, r1, #16
    orrs r0, r1
    ldr r3, lit_free
    bl callr3                   @ tilemap buffer
    adds r0, r5, #0
    ldr r3, lit_destroytask
    bl callr3
    ldr r0, lit_returnfield
    ldr r3, lit_setcb2
    bl callr3
t_ret:
    add sp, #4
    pop {r4, r5, r6, pc}

@ page_count -> r0 = number of pages (at least 1)
page_count:
    push {lr}
    ldr r0, lit_ffffA
    bl find                     @ r1 = total entries
    adds r0, r1, #6
    bl udiv7
    cmp r0, #0
    bne pc_ret
    movs r0, #1
pc_ret:
    pop {pc}

@ udiv7: r0 = r0 / 7 (small values)
udiv7:
    movs r1, #0
ud_loop:
    cmp r0, #7
    blo ud_done
    subs r0, #7
    adds r1, #1
    b ud_loop
ud_done:
    adds r0, r1, #0
    bx lr

callr3:
    bx r3
callr4:
    bx r4

.align 2
@ ---- pool A: menu, cb2, task ----
lit_addaction:       .word 0x0809F4B1
lit_flagget:         .word 0x0809D791
lit_flag_dex:        .word 0x00000861
lit_palfade:         .word 0x02037FD4
lit_rainsound:       .word 0x080AC379
lit_removeextra:     .word 0x0809F775
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
lit_returnfield:     .word 0x08086195
lit_playse:          .word 0x080A37A5
lit_gtasks:          .word 0x03005E00
lit_gmain:           .word 0x030022C0
lit_dispcnt:         .word 0x00001040    @ OBJ on, 1D mapping
lit_key_right:       .word 0x00000110    @ RIGHT | R
lit_key_left:        .word 0x00000220    @ LEFT | L
lit_ffffA:           .word 0x0000FFFF
lit_cb2_init:        .word CB2_INIT_ADDR
lit_cb2_main:        .word CB2_MAIN_ADDR
lit_vblank:          .word VBLANK_ADDR
lit_task:            .word TASK_ADDR
lit_bgtemplate:      .word BGTEMPLATE_ADDR
lit_wintemplates:    .word WINTEMPLATES_ADDR
lit_textpal:         .word TEXTPAL_ADDR
lit_backdrop:        .word BACKDROP_ADDR

@ draw_page(r0 = page): header + up to 7 rows with icons
draw_page:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x14               @ [sp,#0..#8] outgoing stack args, [sp,#0x10] page
    str r0, [sp, #0x10]         @ page
    ldr r3, lit_resetspritesB
    bl callr3
    ldr r3, lit_freespritepalsB
    bl callr3
    ldr r3, lit_loadiconpals
    bl callr3
    movs r0, #0
    movs r1, #0x44              @ header band: colour 4
    ldr r3, lit_fillwindow
    bl callr3
    movs r0, #1
    movs r1, #0x11              @ list: colour 1
    ldr r3, lit_fillwindow
    bl callr3
    @ header: map name
    ldr r3, lit_getmapsec
    bl callr3
    lsls r0, r0, #16
    lsrs r1, r0, #16
    ldr r0, lit_strvar1
    movs r2, #0
    ldr r3, lit_getmapname
    bl callr3
    movs r0, #0
    movs r1, #6
    movs r2, #0
    ldr r3, lit_strvar1
    ldr r4, lit_colors_hdr
    bl print
    movs r0, #0
    movs r1, #98
    movs r2, #0
    ldr r3, lit_str_dexnav
    ldr r4, lit_colors_hdr
    bl print
    @ "p/n" on the right
    ldr r0, [sp, #0x10]
    adds r0, #1
    ldr r1, lit_strvar4
    bl u8dec
    movs r1, #0xBA              @ '/'
    strb r1, [r0]
    adds r4, r0, #1
    bl page_count
    adds r1, r4, #0
    bl u8dec
    movs r1, #0xFF
    strb r1, [r0]
    movs r0, #0
    movs r1, #196
    movs r2, #0
    ldr r3, lit_strvar4
    ldr r4, lit_colors_hdr
    bl print
    @ rows
    ldr r0, lit_ffffB
    bl find
    cmp r1, #0
    bne dp_rows
    movs r0, #1
    movs r1, #8
    movs r2, #8
    ldr r3, lit_str_none
    ldr r4, lit_colors_norm
    bl print
    b dp_flush
dp_rows:
    movs r7, #0                 @ row
dp_row:
    cmp r7, #7
    bhs dp_flush
    ldr r0, [sp, #0x10]
    lsls r1, r0, #3
    subs r1, r1, r0             @ page*7
    adds r0, r1, r7
    bl find
    cmp r0, #0
    beq dp_flush
    ldr r6, lit_scratchB        @ [0] species u16, [2] min, [3] max, [4] section
    lsls r5, r7, #4
    lsls r0, r7, #2
    adds r5, r5, r0             @ row*20
    adds r5, #2                 @ text y in the list window
    @ icon: CreateMonIcon(species, SpriteCB_MonIcon, 24, 28 + row*20, 0, 0, TRUE)
    ldrh r0, [r6]
    ldr r1, lit_iconcb
    movs r2, #24
    lsls r3, r7, #4
    lsls r4, r7, #2
    adds r3, r3, r4
    adds r3, #28
    movs r4, #0
    str r4, [sp]                @ subpriority
    str r4, [sp, #4]            @ personality
    movs r4, #1
    str r4, [sp, #8]            @ handleDeoxys
    ldr r4, lit_createmonicon
    bl callr4
    @ species name straight from the table in ROM
    ldrh r0, [r6]
    movs r1, #11
    muls r0, r1, r0
    ldr r1, lit_speciesnames
    ldr r1, [r1]
    adds r3, r0, r1
    movs r0, #1
    movs r1, #40
    adds r2, r5, #0
    ldr r4, lit_colors_norm
    bl print
    @ "Lv." min [ "-" max ]
    ldr r1, lit_strvar4
    movs r0, #0xC6              @ L
    strb r0, [r1]
    movs r0, #0xEA              @ v
    strb r0, [r1, #1]
    movs r0, #0xAD              @ .
    strb r0, [r1, #2]
    adds r1, #3
    ldrb r0, [r6, #2]
    bl u8dec
    ldrb r1, [r6, #2]
    ldrb r2, [r6, #3]
    cmp r1, r2
    beq dp_lvend
    movs r1, #0xAE              @ -
    strb r1, [r0]
    adds r1, r0, #1
    ldrb r0, [r6, #3]
    bl u8dec
dp_lvend:
    movs r1, #0xFF
    strb r1, [r0]
    movs r0, #1
    movs r1, #136
    adds r2, r5, #0
    ldr r3, lit_strvar4
    ldr r4, lit_colors_norm
    bl print
    @ section name, in the section's own colour
    ldrb r0, [r6, #4]
    lsls r0, r0, #2
    ldr r3, lit_sectionnames
    ldr r3, [r3, r0]
    ldr r4, lit_sectioncolors
    ldr r4, [r4, r0]
    movs r0, #1
    movs r1, #192
    adds r2, r5, #0
    bl print
    adds r7, #1
    b dp_row
dp_flush:
    movs r0, #0
    ldr r3, lit_putwindow
    bl callr3
    movs r0, #1
    ldr r3, lit_putwindow
    bl callr3
    movs r0, #0
    movs r1, #3
    ldr r3, lit_copywindow
    bl callr3
    movs r0, #1
    movs r1, #3
    ldr r3, lit_copywindow
    bl callr3
    add sp, #0x14
    pop {r4, r5, r6, r7, pc}

@ print(r0 = window, r1 = x, r2 = y, r3 = string, r4 = colours) via AddTextPrinterParameterized4
print:
    push {r4, r5, lr}
    sub sp, #0x14
    movs r5, #0
    str r5, [sp]                @ letter spacing
    str r5, [sp, #4]            @ line spacing
    str r4, [sp, #8]            @ colours
    str r5, [sp, #0xC]          @ speed: instant
    str r3, [sp, #0x10]         @ string
    adds r3, r2, #0
    adds r2, r1, #0
    movs r1, #1                 @ FONT_NORMAL
    ldr r4, lit_addtextprinter4
    bl callr4
    add sp, #0x14
    pop {r4, r5, pc}

@ u8dec(r0 = value 0..255, r1 = dst) -> r0 = dst after the digits (no terminator)
u8dec:
    push {r4, lr}
    movs r2, #0
d100:
    cmp r0, #100
    blo d10s
    subs r0, #100
    adds r2, #1
    b d100
d10s:
    movs r3, #0
d10:
    cmp r0, #10
    blo dout
    subs r0, #10
    adds r3, #1
    b d10
dout:
    cmp r2, #0
    beq d_tens
    adds r4, r2, #0
    adds r4, #0xA1
    strb r4, [r1]
    adds r1, #1
    b d_wr10
d_tens:
    cmp r3, #0
    beq d_wr1
d_wr10:
    adds r4, r3, #0
    adds r4, #0xA1
    strb r4, [r1]
    adds r1, #1
d_wr1:
    adds r4, r0, #0
    adds r4, #0xA1
    strb r4, [r1]
    adds r0, r1, #1
    pop {r4, pc}

.align 2
@ ---- pool B: draw_page, print ----
lit_resetspritesB:   .word 0x08006975
lit_freespritepalsB: .word 0x0800870D
lit_loadiconpals:    .word 0x080D2F05
lit_fillwindow:      .word 0x08003C49
lit_getmapsec:       .word 0x08085C59
lit_getmapname:      .word 0x0812456D
lit_strvar1:         .word 0x02021CC4
lit_strvar4:         .word 0x02021FC4
lit_scratchB:        .word 0x02021DC4    @ gStringVar2, scratch while the screen is open
lit_iconcb:          .word 0x080D3015
lit_createmonicon:   .word 0x080D2CC5
lit_speciesnames:    .word 0x08000144    @ ROM header pointer to the 960-entry name table
lit_putwindow:       .word 0x0800378D
lit_copywindow:      .word 0x08003659
lit_addtextprinter4: .word 0x08199EED
lit_ffffB:           .word 0x0000FFFF
lit_colors_hdr:      .word COLORS_HDR_ADDR
lit_colors_norm:     .word COLORS_NORM_ADDR
lit_sectioncolors:   .word SECTIONCOLORS_ADDR
lit_str_dexnav:      .word STR_DEXNAV_ADDR
lit_str_none:        .word STR_NONE_ADDR
lit_sectionnames:    .word SECTIONNAMES_ADDR

@ find_header(r0 = table index 0/1) -> r0 = header for the current map, or 0
find_header:
    push {r4, lr}
    lsls r0, r0, #2
    ldr r1, lit_tables
    ldr r4, [r1, r0]
    ldr r0, lit_sb1ptr
    ldr r0, [r0]
    ldrb r2, [r0, #4]           @ mapGroup
    ldrb r3, [r0, #5]           @ mapNum
fh_loop:
    ldrb r0, [r4]
    ldrb r1, [r4, #1]
    cmp r0, #0xFF
    bne fh_cmp
    cmp r1, #0xFF
    beq fh_none
fh_cmp:
    cmp r0, r2
    bne fh_next
    cmp r1, r3
    bne fh_next
    adds r0, r4, #0
    pop {r4, pc}
fh_next:
    adds r4, #20
    b fh_loop
fh_none:
    movs r0, #0
    pop {r4, pc}

@ find(r0 = unique index i) -> r0 = 1 and scratch filled, or r0 = 0; r1 = entries counted so far
@ Walks both header tables, all four sections, skipping species already listed in the same section.
find:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x14
    adds r4, r0, #0             @ target
    movs r5, #0                 @ count
    movs r0, #0
    str r0, [sp]                @ table index
f_tbl:
    ldr r0, [sp]
    cmp r0, #2
    bhs f_notfound
    bl find_header
    adds r6, r0, #0
    cmp r6, #0
    beq f_next_tbl
    movs r0, #0
    str r0, [sp, #4]            @ section
f_sec:
    ldr r0, [sp, #4]
    cmp r0, #4
    bhs f_next_tbl
    lsls r1, r0, #2
    adds r1, r6, r1
    ldr r1, [r1, #4]            @ WildPokemonInfo*
    cmp r1, #0
    beq f_next_sec
    ldr r1, [r1, #4]            @ entries
    str r1, [sp, #0x10]
    ldr r2, lit_counts
    ldrb r2, [r2, r0]
    str r2, [sp, #0xC]          @ n
    movs r0, #0
    str r0, [sp, #8]            @ k
f_ent:
    ldr r0, [sp, #8]
    ldr r1, [sp, #0xC]
    cmp r0, r1
    bhs f_next_sec
    ldr r7, [sp, #0x10]
    lsls r1, r0, #2
    adds r7, r7, r1             @ &entries[k]
    ldrh r3, [r7, #2]           @ species
    cmp r3, #0
    beq f_next_ent
    ldr r1, [sp, #0x10]
    movs r2, #0
f_dup:
    ldr r0, [sp, #8]
    cmp r2, r0
    bhs f_uniq
    lsls r0, r2, #2
    adds r0, r1, r0
    ldrh r0, [r0, #2]
    cmp r0, r3
    beq f_next_ent              @ listed already
    adds r2, #1
    b f_dup
f_uniq:
    cmp r5, r4
    bne f_count
    ldr r0, [sp, #0x10]
    ldr r1, [sp, #0xC]
    adds r2, r3, #0
    ldr r3, [sp, #4]
    bl fill_scratch
    movs r0, #1
    adds r1, r5, #0
    b f_ret
f_count:
    adds r5, #1
f_next_ent:
    ldr r0, [sp, #8]
    adds r0, #1
    str r0, [sp, #8]
    b f_ent
f_next_sec:
    ldr r0, [sp, #4]
    adds r0, #1
    str r0, [sp, #4]
    b f_sec
f_next_tbl:
    ldr r0, [sp]
    adds r0, #1
    str r0, [sp]
    b f_tbl
f_notfound:
    movs r0, #0
    adds r1, r5, #0
f_ret:
    add sp, #0x14
    pop {r4, r5, r6, r7, pc}

@ fill_scratch(r0 = entries, r1 = n, r2 = species, r3 = section): level range over every slot of that species
fill_scratch:
    push {r4, r5, r6, r7, lr}
    movs r4, #0xFF              @ min
    movs r5, #0                 @ max
    movs r6, #0
fs_loop:
    cmp r6, r1
    bhs fs_done
    lsls r7, r6, #2
    adds r7, r0, r7
    ldrh r7, [r7, #2]
    cmp r7, r2
    bne fs_next
    lsls r7, r6, #2
    adds r7, r0, r7
    ldrb r7, [r7]               @ min
    cmp r7, r4
    bhs fs_max
    adds r4, r7, #0
fs_max:
    lsls r7, r6, #2
    adds r7, r0, r7
    ldrb r7, [r7, #1]           @ max
    cmp r7, r5
    bls fs_next
    adds r5, r7, #0
fs_next:
    adds r6, #1
    b fs_loop
fs_done:
    ldr r0, lit_scratchC
    strh r2, [r0]
    strb r4, [r0, #2]
    strb r5, [r0, #3]
    strb r3, [r0, #4]
    pop {r4, r5, r6, r7, pc}

.align 2
@ ---- pool C: find, find_header, fill_scratch ----
lit_sb1ptr:          .word 0x03005D8C
lit_scratchC:        .word 0x02021DC4
lit_tables:          .word TABLES_ADDR
lit_counts:          .word COUNTS_ADDR
