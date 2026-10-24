@ Continue no longer walks you off a tile that only looks like a door (Hyper Emerald v5.7). See contexit_patch.py.
@
@ After Continue the field callback is FieldCB_FadeTryShowMapPopup (0x08086204): the map's name, then
@ FieldCB_WarpExitFadeFromBlack (0x080AF3C8) - music, the fade in, SetUpWarpExitTask (0x080AF334), the field locked.
@ SetUpWarpExitTask is what takes you out of a door after a warp: on an animated door Task_ExitDoor (one step
@ down), on a non-animated door, water door or deep south warp Task_ExitNonAnimDoor (one step the way you face,
@ through anything), else Task_ExitNonDoor (no step). Vanilla's maps never let you stand on such a tile unless it is
@ the warp you came by, so after Continue it never did anything. This hack's maps have such tiles with no warp on
@ them (Petalburg Woods: the second row of each way in from Route 104): saved there facing a tree, Continue walked
@ you into the tree.
@
@ cont_cb is that callback with one difference: SetUpWarpExitTask only when a warp event is on your tile,
@ Task_ExitNonDoor otherwise. CB2_ContinueSavedGame's literal (0x08086314) points here.
.thumb

cont_cb:
    push {lr}
    ldr r0, lit_header              @ the map's name, as 0x08086206..0x08086220
    ldrb r1, [r0, #0x1A]
    movs r0, #0xF8
    ands r0, r1
    cmp r0, #8
    bne cc_exit
    ldr r3, lit_popup_ok            @ SecretBaseMapPopupEnabled
    bl call_r3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #1
    bne cc_exit
    ldr r3, lit_popup               @ ShowMapNamePopup
    bl call_r3
cc_exit:                            @ FieldCB_WarpExitFadeFromBlack, as 0x080AF3C8..0x080AF3E2
    ldr r3, lit_ereader             @ OnTrainerHillEReaderChallengeFloor
    bl call_r3
    cmp r0, #0
    bne cc_fade
    ldr r3, lit_music               @ Overworld_PlaySpecialMapMusic
    bl call_r3
cc_fade:
    ldr r3, lit_fadein              @ FadeInFromBlack
    bl call_r3
    bl on_warp
    cmp r0, #0
    beq cc_stay
    ldr r3, lit_setup               @ SetUpWarpExitTask: on a warp, as the game always did
    bl call_r3
    b cc_lock
cc_stay:
    ldr r0, lit_nondoor             @ CreateTask(Task_ExitNonDoor, 10): you stay on your tile
    movs r1, #10
    ldr r3, lit_createtask
    bl call_r3
cc_lock:
    ldr r3, lit_lock                @ LockPlayerFieldControls
    bl call_r3
    pop {r0}
    bx r0

@ r0 = 1 if one of the map's warp events is on your tile (at any height), else 0
on_warp:
    push {r4, lr}
    sub sp, #4
    mov r0, sp
    mov r1, sp
    adds r1, #2
    ldr r3, lit_destcoords          @ PlayerGetDestCoords(&x, &y): your tile, with the map's margin of 7
    bl call_r3
    mov r0, sp
    ldrh r1, [r0, #2]
    ldrh r0, [r0]
    subs r0, #7
    subs r1, #7
    ldr r2, lit_header
    ldr r2, [r2, #4]                @ gMapHeader.events
    ldrb r3, [r2, #1]               @ the number of warps
    ldr r2, [r2, #8]                @ the warps: x, y (16 bits each), then 4 bytes
ow_loop:
    cmp r3, #0
    beq ow_none
    ldrh r4, [r2]
    cmp r4, r0
    bne ow_next
    ldrh r4, [r2, #2]
    cmp r4, r1
    beq ow_found
ow_next:
    adds r2, #8
    subs r3, #1
    b ow_loop
ow_found:
    movs r0, #1
    b ow_end
ow_none:
    movs r0, #0
ow_end:
    add sp, #4
    pop {r4}
    pop {r1}
    bx r1
call_r3:
    bx r3

PADA
.align 2
lit_header:     .word 0x02037318
lit_popup_ok:   .word 0x080E909D
lit_popup:      .word 0x080D47E5
lit_ereader:    .word 0x081D6535
lit_music:      .word 0x08085785
lit_fadein:     .word 0x080AF0A1
lit_setup:      .word 0x080AF335
lit_nondoor:    .word 0x080AF611
lit_createtask: .word 0x080A8FB1
lit_lock:       .word 0x08098E55
lit_destcoords: .word 0x0808BAAD
