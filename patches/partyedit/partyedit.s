@ Party Pokemon editor (Hyper Emerald v5.7): party-menu action + editor screen.
@
@ ENTRY. builder_hook is entered from the trampoline at 0x081B3518 (the CANCEL append in
@ SetPartyMonFieldSelectionActions). It appends EDIT (table entry 34) when the action list has room, then
@ jumps to the relearner's own builder_hook at 0x08FD9B00, which appends MOVES (33) and CANCEL and resumes
@ the function at 0x081B3529. Chaining, not replacing, so Moves keeps working. TAIL site: the caller's
@ return address is already on the stack, so the `bl call3` helper may clobber lr.
@
@ SCREEN. Self-contained BG0 + window screen in the shape of the DexNav screen (patches/dexnav): own VBlank
@ callback, own palette, text via AddTextPrinterParameterized4, B returns to the field. Page 0 edits nature
@ and the six IVs, page 1 the six EVs; START switches page. Values are written straight into gPlayerParty
@ (this hack keeps party mons unencrypted and unshuffled) and CalculateMonStats is called after each change.
@
@ Several literal pools: Thumb-1 pc-relative `ldr` only reaches 1020 bytes, so each chunk of code is
@ followed by its own pool. Keystone fails the assembly if a pool ends up out of reach.
.thumb

@ =================================================================================================== entry
builder_hook:
    ldr r0, litA_internal
    ldr r1, [r0]
    ldrb r2, [r1, #0x17]        @ numActions
    cmp r2, #6
    bhs bh_chain                @ no room for one more
    adds r0, r1, #0
    adds r0, #0xF               @ actions[]
    adds r1, #0x17              @ &numActions
    movs r2, #34                @ MENU_EDIT
    ldr r3, litA_append
    bl call3
bh_chain:
    ldr r3, litA_prev
    bx r3

cursor_edit:                    @ (taskId) mirrors CursorCb_Summary 0x081B37FC
    push {r4, lr}
    lsls r4, r0, #24
    lsrs r4, r4, #24
    movs r0, #5
    ldr r3, litA_playse
    bl call3
    ldr r0, litA_internal
    ldr r1, [r0]
    ldr r0, litA_cb2_edit
    str r0, [r1, #4]            @ sPartyMenuInternal->exitCallback
    adds r0, r4, #0
    ldr r3, litA_close
    bl call3
    pop {r4}
    pop {r0}
    bx r0

cb2_edit:                       @ the party menu has faded out: stash the slot and switch to the screen
    push {lr}
    ldr r0, litA_party
    ldrb r0, [r0, #9]           @ gPartyMenu.slotId
    ldr r1, litA_var8004
    strh r0, [r1]               @ gSpecialVar_0x8004 = slot
    ldr r0, litA_cb2_init
    ldr r3, litA_setcb2
    bl call3
    pop {r0}
    bx r0

.align 2
litA_internal:  .word 0x0203CEC4
litA_append:    .word 0x080A0945
litA_prev:      .word 0x08FD9B01
litA_playse:    .word 0x080A37A5
litA_cb2_edit:  .word CB2_EDIT_ADDR
litA_close:     .word 0x081B12C1
litA_party:     .word 0x0203CEC8
litA_var8004:   .word 0x020375E0
litA_cb2_init:  .word CB2_INIT_ADDR
litA_setcb2:    .word 0x08000541
litA_calcstats: .word 0x08068D0D
litA_partybase: .word 0x020244EC
litA_gmain:     .word 0x030022C0

@ ================================================================================================= screen
cb2_init:
    push {r4, r5, lr}
    sub sp, #0xC
    movs r0, #0
    ldr r3, litB_setvblank
    bl call3
    movs r0, #0
    movs r1, #0
    ldr r3, litB_setgpureg
    bl call3                    @ REG_DISPCNT = 0
    movs r0, #0
    ldr r3, litB_resetbgs
    bl call3
    movs r0, #0
    ldr r1, litB_bgtemplate
    movs r2, #1
    ldr r3, litB_initbgs
    bl call3
    movs r0, #0x80
    lsls r0, r0, #4             @ 0x800-byte tilemap buffer
    ldr r3, litB_alloczeroed
    bl call3
    adds r4, r0, #0
    movs r0, #0
    adds r1, r4, #0
    ldr r3, litB_setbgtilemap
    bl call3
    ldr r3, litB_resetpalfade
    bl call3
    ldr r3, litB_resetsprites
    bl call3
    ldr r3, litB_freespritepals
    bl call3
    ldr r3, litB_resettasks
    bl call3
    ldr r3, litB_deactprinters
    bl call3
    ldr r0, litB_wintemplates
    ldr r3, litB_initwindows
    bl call3
    ldr r0, litB_textpal
    movs r1, #0xF0
    movs r2, #0x20
    ldr r3, litB_loadpalette
    bl call3                    @ palette 15
    ldr r0, litB_backdrop
    movs r1, #0
    movs r2, #2
    ldr r3, litB_loadpalette
    bl call3
    movs r0, #0
    ldr r1, litB_dispcnt
    ldr r3, litB_setgpureg
    bl call3                    @ OBJ on, 1D mapping
    movs r0, #0
    ldr r3, litB_showbg
    bl call3
    ldr r0, litB_task
    movs r1, #0
    ldr r3, litB_createtask
    bl call3
    lsls r0, r0, #24
    lsrs r5, r0, #24
    bl task_data
    movs r1, #0
    strh r1, [r0]               @ data[0] = page
    strh r1, [r0, #2]           @ data[1] = cursor row
    strh r1, [r0, #4]           @ data[2] = state (0 active, 1 leaving)
    strh r4, [r0, #6]           @ data[3..4] = tilemap buffer
    lsrs r1, r4, #16
    strh r1, [r0, #8]
    movs r0, #0
    movs r1, #0
    bl draw_edit
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #16
    movs r3, #0
    ldr r4, litB_beginfade
    bl call4                    @ fade in from black
    ldr r0, litB_vblank
    ldr r3, litB_setvblank
    bl call3
    ldr r0, litB_cb2_main
    ldr r3, litB_setcb2
    bl call3
    add sp, #0xC
    pop {r4, r5, pc}

cb2_main:
    push {lr}
    ldr r3, litB_runtasks
    bl call3
    ldr r3, litB_animsprites
    bl call3
    ldr r3, litB_buildoam
    bl call3
    ldr r3, litB_dotilemapcopies
    bl call3
    ldr r3, litB_updatepalfade
    bl call3
    pop {pc}

vblank:
    push {lr}
    ldr r3, litB_loadoam
    bl call3
    ldr r3, litB_spritecopies
    bl call3
    ldr r3, litB_transferpltt
    bl call3
    pop {pc}

@ task_data: r5 = task id -> r0 = &gTasks[r5].data[0]; clobbers r1
task_data:
    lsls r1, r5, #2
    adds r1, r1, r5
    lsls r1, r1, #3
    ldr r0, litB_gtasks
    adds r0, r0, r1
    adds r0, #8
    bx lr

@ Task_Edit(r0 = taskId)
task:
    push {r4, r5, r6, lr}
    sub sp, #4
    lsls r0, r0, #24
    lsrs r5, r0, #24
    ldr r0, litB_palfade
    ldrb r1, [r0, #7]
    movs r0, #0x80
    tst r0, r1
    bne t_ret                   @ fading: ignore input
    bl task_data
    adds r4, r0, #0
    ldrh r0, [r4, #4]
    cmp r0, #0
    bne t_leave
    ldr r0, litB_gmain
    ldrh r6, [r0, #0x2E]        @ newKeys
    movs r0, #2                 @ B (0x02)
    tst r0, r6
    bne t_exit
    ldr r0, litB_key_down       @ DOWN 0x80
    tst r0, r6
    bne t_down
    ldr r0, litB_key_up         @ UP 0x40
    tst r0, r6
    bne t_up
    movs r0, #0x10              @ RIGHT 0x10
    tst r0, r6
    bne t_right
    movs r0, #0x20              @ LEFT 0x20
    tst r0, r6
    bne t_left
    ldr r0, litB_key_r          @ R 0x100: +5
    tst r0, r6
    bne t_bigright
    ldr r0, litB_key_l          @ L 0x200: -5
    tst r0, r6
    bne t_bigleft
    movs r0, #8                 @ START 0x08: switch page
    tst r0, r6
    bne t_page
    b t_ret
t_page:
    ldrh r1, [r4]
    movs r0, #1
    eors r1, r0
    strh r1, [r4]
    movs r0, #0
    strh r0, [r4, #2]           @ back to the top row
    b t_redraw
t_down:
    bl row_max
    ldrh r1, [r4, #2]
    cmp r1, r0
    bhs t_ret
    adds r1, #1
    strh r1, [r4, #2]
    b t_redraw
t_up:
    ldrh r1, [r4, #2]
    cmp r1, #0
    beq t_ret
    subs r1, #1
    strh r1, [r4, #2]
    b t_redraw
t_right:
    movs r0, #1
    b t_change
t_left:
    movs r0, #1
    rsbs r0, r0, #0
    b t_change
t_bigright:
    movs r0, #5
    b t_change
t_bigleft:
    movs r0, #5
    rsbs r0, r0, #0
t_change:
    adds r2, r0, #0             @ delta
    ldrh r0, [r4]               @ page
    ldrh r1, [r4, #2]           @ row
    bl apply_delta
    cmp r0, #0
    beq t_ret
    movs r0, #5
    ldr r3, litB_playse
    bl call3
t_redraw:
    ldrh r0, [r4]
    ldrh r1, [r4, #2]
    bl draw_edit
    b t_ret
t_exit:
    movs r0, #5
    ldr r3, litB_playse
    bl call3
    movs r0, #1
    strh r0, [r4, #4]           @ state = leaving
    movs r0, #1
    rsbs r0, r0, #0
    movs r1, #0
    str r1, [sp]
    movs r2, #0
    movs r3, #16
    ldr r4, litB_beginfade
    bl call4
    b t_ret
t_leave:
    ldr r3, litB_freewindows
    bl call3
    ldrh r0, [r4, #6]
    ldrh r1, [r4, #8]
    lsls r1, r1, #16
    orrs r0, r1
    ldr r3, litB_free
    bl call3                    @ tilemap buffer
    adds r0, r5, #0
    ldr r3, litB_destroytask
    bl call3
    ldr r0, litB_returnfield
    ldr r3, litB_setcb2
    bl call3
t_ret:
    add sp, #4
    pop {r4, r5, r6, pc}

@ row_max(task data in r4) -> r0 = last selectable row on the current page
row_max:
    ldrh r0, [r4]
    cmp r0, #0
    bne rm_ev
    movs r0, #6                 @ page 0: Nature + six IVs
    bx lr
rm_ev:
    movs r0, #5                 @ page 1: six EVs
    bx lr

.align 2
litB_setvblank:      .word 0x080006F1
litB_setcb2:         .word 0x08000541
litB_setgpureg:      .word 0x080010B5
litB_resetbgs:       .word 0x080017BD
litB_initbgs:        .word 0x080017E9
litB_alloczeroed:    .word 0x08000B4D
litB_free:           .word 0x08000B61
litB_setbgtilemap:   .word 0x08002251
litB_resetpalfade:   .word 0x080A1A75
litB_resetsprites:   .word 0x08006975
litB_freespritepals: .word 0x0800870D
litB_resettasks:     .word 0x080A8F51
litB_deactprinters:  .word 0x080045B1
litB_initwindows:    .word 0x080031C1
litB_loadpalette:    .word 0x080A1939
litB_showbg:         .word 0x08001B31
litB_createtask:     .word 0x080A8FB1
litB_destroytask:    .word 0x080A909D
litB_beginfade:      .word 0x080A1AD5
litB_runtasks:       .word 0x080A910D
litB_animsprites:    .word 0x080069C1
litB_buildoam:       .word 0x08006A0D
litB_dotilemapcopies:.word 0x081999D1
litB_updatepalfade:  .word 0x080A1A1D
litB_loadoam:        .word 0x08007189
litB_spritecopies:   .word 0x0800742D
litB_transferpltt:   .word 0x080A19C1
litB_freewindows:    .word 0x08003605
litB_returnfield:    .word 0x080860C9    @ CB2_ReturnToField (the relearner's exit). NOT 0x08086195,
                                         @ which is ReturnToFieldWithOpenMenu and drops you into the START
                                         @ menu with the cursor on Pokedex.
litB_playse:         .word 0x080A37A5
litB_gtasks:         .word 0x03005E00
litB_gmain:          .word 0x030022C0
litB_palfade:        .word 0x02037FD4
litB_dispcnt:        .word 0x00001040
litB_key_down:       .word 0x00000080    @ GBA keys: A1 B2 SEL4 START8 RIGHT16 LEFT32 UP64 DOWN128
litB_key_up:         .word 0x00000040
litB_key_r:          .word 0x00000100
litB_key_l:          .word 0x00000200
litB_task:           .word TASK_ADDR
litB_vblank:         .word VBLANK_ADDR
litB_cb2_main:       .word CB2_MAIN_ADDR
litB_wintemplates:   .word WINTEMPLATES_ADDR
litB_textpal:        .word TEXTPAL_ADDR
litB_backdrop:       .word BACKDROP_ADDR
litB_bgtemplate:     .word BGTEMPLATE_ADDR
litB_fillwindow:     .word 0x08003C49
litB_putwindow:      .word 0x0800378D
litB_copywindow:     .word 0x08003659

@ ================================================================================================= drawing
@ mon_ptr() -> r0 = gPlayerParty + slot*100 ; slot = gSpecialVar_0x8004
mon_ptr:
    ldr r0, litC_var8004
    ldrh r0, [r0]
    movs r1, #100
    muls r0, r1, r0
    ldr r1, litC_partybase
    adds r0, r0, r1
    bx lr

@ species_name(r0 = species) -> r0 = name (ROM header 0x144 -> 11 bytes/entry)
species_name:
    ldr r1, litC_speciesptr
    ldr r1, [r1]
    movs r2, #11
    muls r0, r2, r0
    adds r0, r0, r1
    bx lr

@ value_of(r0 = mon, r1 = row, r2 = page) -> r0 = value
value_of:
    cmp r2, #0
    bne vo_ev
    cmp r1, #0
    bne vo_iv
    @ nature: the override, or the mon's own nature when there is none (override 0 = "unset", which is what
    @ the Mint's "None" writes). Showing the effective nature keeps this screen agreeing with the summary.
    ldrb r3, [r0, #0x1F]
    movs r2, #0x7F
    ands r3, r2
    cmp r3, #0
    beq vo_nat_pers
    adds r0, r3, #0
    bx lr
vo_nat_pers:
    push {lr}
    ldr r0, [r0, #0]            @ personality
    movs r1, #0x19              @ 25
    ldr r3, litD_umodsi3
    bl call3
    pop {pc}
vo_iv:
    subs r1, #1                 @ stat 0..5
    ldr r2, litC_ivshift
    ldrb r2, [r2, r1]
    ldr r0, [r0, #0x48]
    lsrs r0, r0, r2
    movs r3, #0x1F
    ands r0, r3
    bx lr
vo_ev:
    ldr r2, litC_evoff
    ldrb r2, [r2, r1]
    adds r0, #0x38
    ldrb r0, [r0, r2]
    bx lr

@ nat_name(r0 = nature 0..24, r1 = dst) -> r0 = dst past the name. Copies only the name: the game's
@ strings carry trailing FC control codes (the stat arrows), which do not belong in our column.
nat_name:
    push {r4, lr}
    ldr r2, litD_naturetable
    lsls r0, r0, #2
    ldr r2, [r2, r0]            @ pointer to the name
nn_loop:
    ldrb r3, [r2]
    cmp r3, #0xFC
    bhs nn_done                 @ FC (control) or FF (end): stop
    strb r3, [r1]
    adds r1, #1
    adds r2, #1
    b nn_loop
nn_done:
    adds r0, r1, #0
    pop {r4, pc}

@ print(r0 = window, r1 = x, r2 = y, r3 = string, r4 = colours) - AddTextPrinterParameterized4, speed 0
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
    ldr r4, litC_addtextprinter4
    bl call4
    add sp, #0x14
    pop {r4, r5, pc}

@ u8dec(r0 = value 0..255, r1 = dst) -> r0 = dst past the last digit (no terminator)
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

@ draw_edit(r0 = page, r1 = cursor row)
draw_edit:
    push {r4, r5, r6, r7, lr}
    sub sp, #0x10
    str r0, [sp, #0xC]          @ page
    str r1, [sp, #8]            @ cursor row
    movs r0, #0
    movs r1, #0x22              @ body fill: colour 2 (dark)
    ldr r3, litC_fillwindow
    bl call3
    bl mon_ptr
    adds r5, r0, #0             @ r5 = mon
    @ header: "Edit " + species name
    movs r0, #0
    movs r1, #8
    movs r2, #3
    ldr r3, litD_str_edit
    ldr r4, litD_colors_hdr
    bl print
    ldrh r0, [r5, #0x20]
    bl species_name
    adds r3, r0, #0
    movs r0, #0
    movs r1, #48
    movs r2, #3
    ldr r4, litD_colors_hdr
    bl print
    @ rows
    movs r6, #0
dr_loop:
    cmp r6, #7
    bhs dr_flush
    ldr r0, [sp, #0xC]
    cmp r0, #0
    bne dr_ev
    ldr r7, litD_labels_iv
    b dr_lbl
dr_ev:
    cmp r6, #6
    bhs dr_flush
    ldr r7, litD_labels_ev
dr_lbl:
    @ label
    lsls r0, r6, #2
    ldr r3, [r7, r0]
    movs r0, #0
    movs r1, #16
    lsls r2, r6, #4
    adds r2, #24
    ldr r4, litD_colors_norm
    ldr r0, [sp, #8]
    cmp r0, r6
    bne dr_lblp
    ldr r4, litD_colors_hl
dr_lblp:
    movs r0, #0
    bl print
    @ value: the nature row shows its NAME, every other row the number
    adds r0, r5, #0
    adds r1, r6, #0
    ldr r2, [sp, #0xC]
    bl value_of
    adds r4, r0, #0             @ value
    ldr r2, [sp, #0xC]
    cmp r2, #0                  @ page 0 ...
    bne dr_num
    cmp r6, #0                  @ ... and row 0 = nature
    bne dr_num
    adds r0, r4, #0
    ldr r1, litD_scratch
    bl nat_name
    b dr_valdone
dr_num:
    adds r0, r4, #0
    ldr r1, litD_scratch
    bl u8dec
dr_valdone:
    movs r1, #0xFF
    strb r1, [r0]
    movs r0, #0
    movs r1, #88                @ left enough for the longest nature + its arrows ("Naughty ^Atk vSp.A")
    lsls r2, r6, #4
    adds r2, #24
    ldr r3, litD_scratch
    ldr r4, litD_colors_norm
    ldr r0, [sp, #8]
    cmp r0, r6
    bne dr_valp
    ldr r4, litD_colors_hl
dr_valp:
    movs r0, #0
    bl print
    adds r6, #1
    b dr_loop
dr_flush:
    @ On the EV page, also show the running total (the game caps the six at 510).
    ldr r0, [sp, #0xC]
    cmp r0, #0
    beq dr_skip_total
    movs r0, #0
    movs r1, #16
    movs r2, #120
    ldr r3, litD_str_evtotal
    ldr r4, litD_colors_norm
    bl print
    adds r0, r5, #0
    adds r0, #0x38
    movs r1, #0                 @ sum
    movs r3, #0
dt_sum:
    ldrb r6, [r0, r3]
    adds r1, r1, r6
    adds r3, #1
    cmp r3, #6
    blo dt_sum
    adds r0, r1, #0
    ldr r1, litD_scratch
    bl u8dec
    movs r1, #0xBA              @ '/'
    strb r1, [r0]
    movs r1, #0xA6              @ '5'
    strb r1, [r0, #1]
    movs r1, #0xA2              @ '1'
    strb r1, [r0, #2]
    movs r1, #0xA1              @ '0'
    strb r1, [r0, #3]
    movs r1, #0xFF
    strb r1, [r0, #4]
    movs r0, #0
    movs r1, #120
    movs r2, #120
    ldr r3, litD_scratch
    ldr r4, litD_colors_norm
    bl print
dr_skip_total:
    movs r0, #0
    ldr r3, litC_putwindow
    bl call3
    movs r0, #0
    movs r1, #3
    ldr r3, litC_copywindow
    bl call3
    add sp, #0x10
    pop {r4, r5, r6, r7, pc}

@ apply_delta(r0 = page, r1 = row, r2 = delta) -> r0 = 1 if a value changed
apply_delta:
    push {r4, r5, r6, r7, lr}
    adds r5, r0, #0             @ page
    adds r6, r1, #0             @ row
    adds r7, r2, #0             @ delta
    bl mon_ptr
    adds r4, r0, #0             @ mon
    cmp r5, #0
    bne ad_ev
    cmp r6, #0
    bne ad_iv
    @ nature: mon+0x1F bits 0-6, bit 7 preserved
    ldrb r0, [r4, #0x1F]
    movs r1, #0x7F
    ands r1, r0
    adds r1, r1, r7
    cmp r1, #0
    bge ad_n0
    movs r1, #0
ad_n0:
    cmp r1, #24
    ble ad_n1
    movs r1, #24
ad_n1:
    movs r2, #0x80
    ands r2, r0
    orrs r1, r2
    strb r1, [r4, #0x1F]
    b ad_recalc
ad_iv:
    subs r6, #1                 @ stat 0..5
    ldr r1, litC_ivshift
    ldrb r1, [r1, r6]           @ shift (0,5,10,15,20,25)
    ldr r0, [r4, #0x48]         @ IV word
    movs r2, #0x1F
    lsls r2, r2, r1             @ field mask
    adds r3, r0, #0
    ands r3, r2
    lsrs r3, r1                 @ current value
    adds r3, r3, r7
    cmp r3, #0
    bge ad_i0
    movs r3, #0
ad_i0:
    cmp r3, #31
    ble ad_i1
    movs r3, #31
ad_i1:
    bics r0, r2
    lsls r3, r3, r1
    orrs r0, r3
    str r0, [r4, #0x48]
    b ad_recalc
ad_ev:
    ldr r1, litC_evoff
    ldrb r1, [r1, r6]
    adds r0, r4, #0
    adds r0, #0x38
    ldrb r2, [r0, r1]
    adds r2, r2, r7
    cmp r2, #0
    bge ad_e0
    movs r2, #0
ad_e0:
    cmp r2, #255
    ble ad_e1
    movs r2, #255
ad_e1:
    strb r2, [r0, r1]
ad_recalc:
    adds r0, r4, #0
    ldr r3, litE_calcstats
    bl call3                    @ CalculateMonStats(mon)
    movs r0, #1
    pop {r4, r5, r6, r7, pc}

.align 2
litC_var8004:        .word 0x020375E0
litC_partybase:      .word 0x020244EC
litC_speciesptr:     .word 0x08000144
litC_ivshift:        .word IVSHIFT_ADDR
litC_evoff:          .word EVOFF_ADDR
litC_addtextprinter4:.word 0x08199EED
litC_fillwindow:     .word 0x08003C49
litC_putwindow:      .word 0x0800378D
litC_copywindow:     .word 0x08003659
litC_colors_hdr:     .word COLORS_HDR_ADDR
litC_colors_norm:    .word COLORS_NORM_ADDR
litC_colors_hl:      .word COLORS_HL_ADDR
litD_str_edit:       .word STR_EDIT_ADDR
litD_str_evtotal:    .word STR_EVTOTAL_ADDR
litD_labels_iv:      .word LABELS_IV_ADDR
litD_labels_ev:      .word LABELS_EV_ADDR
litD_colors_hdr:     .word COLORS_HDR_ADDR
litD_colors_norm:    .word COLORS_NORM_ADDR
litD_colors_hl:      .word COLORS_HL_ADDR
@ 16 bytes of EWRAM scratch for the number strings: this is RAM, not ROM (writes to the blob are ignored).
litD_scratch:        .word 0x02039E40
litD_naturetable:    .word 0x0861CB50    @ 25 pointers, standard order Hardy..Quirky (referenced by
                                         @ code at 0x8073188 / 0x8167C7C / 0x81C31E8, so it is the live one)
litE_calcstats:      .word 0x08068D0D
litD_umodsi3:        .word 0x082E7BE1    @ __umodsi3, for personality % 25

call3:
    bx r3
call4:
    bx r4
