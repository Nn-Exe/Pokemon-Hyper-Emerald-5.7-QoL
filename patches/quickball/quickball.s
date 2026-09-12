@ Quick ball throw (R button) in wild battles for Hyper Emerald v5.7.
@ Tap R at the FIGHT/BAG/POKEMON/RUN menu = throw Poke Balls pocket slot 0.
@ Hold R = show "R <ball> xN / <> change"; LEFT/RIGHT rotate the pocket (new default); release = no throw.
@ Hooked in front of the hack's own action-menu prologue hook (literal @0x0805758C), and in the player
@ controller table entry 21 (choose item @0x31C568) to bypass the bag when a quick throw is pending.
@ State lives in gSpecialVar_ItemId: 0x2000 = R mode, 0x4000 = cycled, 0x8000|ball = quick throw pending.
.thumb
    b r_handler                 @ BASE+0
    b quick_item                @ BASE+2
    b hide_hook                 @ BASE+4

r_handler:
    push {r4, r5, r6, r7, lr}
    bl widget_sync              @ show ball icon + R badge while the menu is up (if throw allowed)
    ldr r4, lit_itemid
    ldrh r5, [r4]               @ state
    ldr r0, lit_gmain
    ldrh r6, [r0, #0x2C]        @ heldKeys
    ldrh r7, [r0, #0x2E]        @ newKeys
    movs r0, #0x20
    lsls r0, r0, #8             @ 0x2000 mode active?
    tst r0, r5
    beq rh_idle
    movs r0, #1
    lsls r0, r0, #8             @ R_BUTTON 0x100
    tst r0, r6
    beq rh_release
    movs r0, #0xFF              @ bump hold counter (low byte of state)
    ands r0, r5
    cmp r0, #0xFF
    beq rh_nobump
    adds r5, #1
    strh r5, [r4]
rh_nobump:
    movs r0, #0x10              @ DPAD_RIGHT
    tst r0, r7
    beq rh_chk_left
    movs r0, #1
    bl rotate_pocket
    b rh_cycled
rh_chk_left:
    movs r0, #0x20              @ DPAD_LEFT
    tst r0, r7
    beq rh_done
    movs r0, #0
    bl rotate_pocket
rh_cycled:
    movs r0, #0x40
    lsls r0, r0, #8             @ 0x4000 cycled
    orrs r5, r0
    strh r5, [r4]
    movs r0, #5
    ldr r3, lit_playse
    bl call3
    bl show_ball_text
    bl widget_refresh
    b rh_done
rh_release:
    movs r0, #0x40
    lsls r0, r0, #8
    tst r0, r5
    bne rh_restore              @ cycled: just restore prompt
    movs r0, #0xFF
    ands r0, r5
    cmp r0, #30                 @ held >= 30 frames: peek only, no throw
    bhs rh_restore
    bl can_throw
    cmp r0, #0
    beq rh_restore
    movs r1, #0x80
    lsls r1, r1, #8
    orrs r0, r1                 @ ball | 0x8000 = quick throw pending
    strh r0, [r4]
    movs r0, #5
    ldr r3, lit_playse
    bl call3
    movs r0, #1                 @ BUFFER_B
    movs r1, #1                 @ B_ACTION_USE_ITEM
    movs r2, #0
    ldr r3, lit_emit2
    bl call3                    @ BtlController_EmitTwoReturnValues
    ldr r3, lit_execcompleted
    bl call3                    @ PlayerBufferExecCompleted
    b rh_done
rh_restore:
    movs r0, #0
    strh r0, [r4]
    bl restore_prompt
    b rh_done
rh_idle:
    movs r0, #1
    lsls r0, r0, #8
    tst r0, r7                  @ R newly pressed?
    beq rh_passthru
    bl can_throw
    cmp r0, #0
    beq rh_passthru
    movs r0, #0x20
    lsls r0, r0, #8
    strh r0, [r4]               @ mode on, not cycled
    bl show_ball_text
rh_done:
    pop {r4, r5, r6, r7, pc}
rh_passthru:
    pop {r4, r5, r6, r7}
    pop {r0}
    mov lr, r0
    ldr r0, lit_hackhook        @ continue into the hack's prologue hook -> vanilla handler
    bx r0

@ can_throw() -> r0 = ball item id (pocket slot 0) if a quick throw is allowed, else 0
can_throw:
    push {r4, lr}
    ldr r0, lit_battletype
    ldr r0, [r0]
    ldr r1, lit_denymask
    ands r0, r1
    bne ct_no                   @ trainer/safari/link/double/frontier/etc.
    ldr r0, lit_bagpockets
    ldr r1, [r0, #8]            @ Poke Balls pocket slots
    ldrh r4, [r1]
    cmp r4, #0
    beq ct_no
    adds r0, r1, #2
    ldr r3, lit_getqty
    bl call3
    cmp r0, #0
    beq ct_no
    ldr r3, lit_storagefull
    bl call3                    @ IsPlayerPartyAndPokemonStorageFull
    lsls r0, r0, #24
    bne ct_no
    adds r0, r4, #0
    pop {r4, pc}
ct_no:
    movs r0, #0
    pop {r4, pc}

@ rotate_pocket(r0: 1 = first->end, 0 = last->front) over the N non-empty ball slots
rotate_pocket:
    push {r4, r5, r6, r7, lr}
    adds r7, r0, #0
    ldr r0, lit_bagpockets
    ldr r5, [r0, #8]
    ldrb r6, [r0, #12]          @ capacity
    movs r4, #0
rp_count:
    cmp r4, r6
    bhs rp_counted
    lsls r0, r4, #2
    ldrh r0, [r5, r0]
    cmp r0, #0
    beq rp_counted
    adds r4, #1
    b rp_count
rp_counted:
    cmp r4, #2
    blo rp_ret
    cmp r7, #0
    beq rp_left
    ldr r6, [r5]                @ tmp = slots[0]
    movs r1, #0
rp_r_loop:
    adds r2, r1, #1
    cmp r2, r4
    bhs rp_r_done
    lsls r0, r2, #2
    ldr r0, [r5, r0]
    lsls r3, r1, #2
    str r0, [r5, r3]            @ slots[i] = slots[i+1]
    adds r1, #1
    b rp_r_loop
rp_r_done:
    lsls r0, r1, #2
    str r6, [r5, r0]            @ slots[N-1] = tmp
    b rp_ret
rp_left:
    subs r1, r4, #1
    lsls r0, r1, #2
    ldr r6, [r5, r0]            @ tmp = slots[N-1]
rp_l_loop:
    cmp r1, #0
    beq rp_l_done
    subs r2, r1, #1
    lsls r0, r2, #2
    ldr r0, [r5, r0]
    lsls r3, r1, #2
    str r0, [r5, r3]            @ slots[i] = slots[i-1]
    subs r1, #1
    b rp_l_loop
rp_l_done:
    str r6, [r5]
rp_ret:
    pop {r4, r5, r6, r7, pc}

@ show_ball_text(): gStringVar4 = "{R} <name>x<n>\n{<>} change" -> prompt window
show_ball_text:
    push {r4, r5, lr}
    ldr r4, lit_strvar4
    movs r0, #0xF8
    strb r0, [r4]
    movs r0, #3                 @ R button glyph
    strb r0, [r4, #1]
    movs r0, #0
    strb r0, [r4, #2]
    adds r4, #3
    ldr r0, lit_bagpockets
    ldr r0, [r0, #8]
    ldrh r0, [r0]
    adds r1, r4, #0
    ldr r3, lit_copyitemname
    bl call3                    @ CopyItemName(ball, dst)
sbt_adv:
    ldrb r0, [r4]
    cmp r0, #0xFF
    beq sbt_1
    adds r4, #1
    b sbt_adv
sbt_1:
    movs r0, #0xEC              @ 'x'
    strb r0, [r4]
    adds r4, #1
    ldr r0, lit_bagpockets
    ldr r0, [r0, #8]
    adds r0, #2
    ldr r3, lit_getqty
    bl call3
    adds r1, r0, #0
    ldr r0, lit_int2str
    mov r12, r0
    adds r0, r4, #0
    movs r2, #0                 @ left align
    movs r3, #3
    bl callip                   @ ConvertIntToDecimalStringN(dst, n, 0, 3)
sbt_adv2:
    ldrb r0, [r4]
    cmp r0, #0xFF
    beq sbt_2
    adds r4, #1
    b sbt_adv2
sbt_2:
    movs r0, #0xFE
    strb r0, [r4]               @ newline
    adds r0, r4, #1
    ldr r1, lit_line2
    ldr r3, lit_stringcopy
    bl call3
    ldr r0, lit_strvar4
    movs r1, #1                 @ B_WIN_ACTION_PROMPT
    ldr r3, lit_puttext
    bl call3
    pop {r4, r5, pc}

restore_prompt:
    push {lr}
    ldr r0, lit_whatwill
    ldr r3, lit_expandbattle
    bl call3
    ldr r0, lit_dispstr
    movs r1, #1
    ldr r3, lit_puttext
    bl call3
    pop {pc}

@ quick_item: player controller "choose item" entry. If a quick throw is pending, skip the bag.
quick_item:
    push {r4, lr}
    ldr r4, lit_itemid
    ldrh r0, [r4]
    lsrs r1, r0, #15
    beq qi_normal
    lsls r0, r0, #17
    lsrs r0, r0, #17            @ ball id
    strh r0, [r4]
    movs r1, #1
    ldr r3, lit_removebagitem
    bl call3                    @ RemoveBagItem(ball, 1)
    ldrh r1, [r4]
    movs r0, #1
    ldr r3, lit_emit1
    bl call3                    @ BtlController_EmitOneReturnValue(BUFFER_B, ball)
    ldr r3, lit_execcompleted
    bl call3
    pop {r4, pc}
qi_normal:
    pop {r4}
    pop {r0}
    mov lr, r0
    ldr r0, lit_origchooseitem
    bx r0

call3:
    bx r3
callip:
    bx r12

.align 2
lit_itemid:         .word 0x0203CE7C
lit_gmain:          .word 0x030022C0
lit_playse:         .word 0x080A37A5
lit_emit2:          .word 0x08034159
lit_execcompleted:  .word 0x0805748D
lit_hackhook:       .word 0x09D0A9E5
lit_battletype:     .word 0x02022FEC
lit_denymask:       .word 0x0FFF8BFB
lit_bagpockets:     .word 0x02039DD8
lit_getqty:         .word 0x080D6555
lit_storagefull:    .word 0x0806B8B1
lit_strvar4:        .word 0x02021FC4
lit_copyitemname:   .word 0x080D6645
lit_int2str:        .word 0x08008CC1
lit_line2:          .word LINE2_ADDR
lit_stringcopy:     .word 0x08008BA1
lit_puttext:        .word 0x0814F9ED
lit_whatwill:       .word 0x085CC9F3
lit_expandbattle:   .word 0x0814E6F1
lit_dispstr:        .word 0x02022E2C
lit_removebagitem:  .word 0x080D6AA5
lit_emit1:          .word 0x080341BD
lit_origchooseitem: .word 0x09D52A1D

@ ================= bottom-left widget: ball item icon + "R" badge =================
@ sprites are tagged by setting their callback to my_cb; found by scanning gSprites.
my_cb:
    bx lr

@ sprite_ptr(r0=id) -> r0 = &gSprites[id]
sprite_ptr:
    lsls r1, r0, #4
    adds r1, r1, r0
    lsls r1, r1, #2
    ldr r0, lit2_gsprites
    adds r0, r0, r1
    bx lr

@ widget_present() -> r0 = 1 if any of my sprites exist
widget_present:
    push {r4, r5, lr}
    ldr r4, lit2_gsprites
    movs r5, #0
wp_loop:
    movs r1, #0x3E
    ldrb r0, [r4, r1]
    movs r1, #1
    tst r0, r1
    beq wp_next
    ldr r0, [r4, #0x1C]
    ldr r1, lit2_mycb
    cmp r0, r1
    beq wp_yes
wp_next:
    adds r4, #0x44
    adds r5, #1
    cmp r5, #64
    blo wp_loop
    movs r0, #0
    pop {r4, r5, pc}
wp_yes:
    movs r0, #1
    pop {r4, r5, pc}

widget_sync:
    push {lr}
    bl widget_present
    cmp r0, #0
    bne wsy_ret
    bl widget_show
wsy_ret:
    pop {pc}

widget_refresh:
    push {lr}
    bl widget_hide
    bl widget_show
    pop {pc}

widget_show:
    push {r4, r5, lr}
    sub sp, #8
    bl can_throw
    cmp r0, #0
    beq ws_ret
    adds r2, r0, #0             @ ball item id
    ldr r0, lit2_tagball
    adds r1, r0, #0
    ldr r3, lit2_additemicon
    bl call3b                   @ AddItemIconSprite(tag, tag, item)
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #0x40
    beq ws_badge
    bl sprite_ptr
    movs r1, #20
    strh r1, [r0, #0x20]        @ x
    movs r1, #90
    strh r1, [r0, #0x22]        @ y
    movs r1, #0
    strh r1, [r0, #0x24]
    strh r1, [r0, #0x26]
    ldrh r1, [r0, #4]
    ldr r2, lit2_c00
    bics r1, r2                 @ oam priority 0 (above text box)
    strh r1, [r0, #4]
    movs r1, #1
    movs r2, #0x43
    strb r1, [r0, r2]           @ subpriority 1 (box is 2 = behind, badge 0 = front)
    ldr r1, lit2_mycb
    str r1, [r0, #0x1C]
ws_badge:
    ldr r0, lit2_boxgfx         @ white box sheet {gfx, 512 | tag<<16}
    str r0, [sp]
    ldr r0, lit2_boxsheethi
    str r0, [sp, #4]
    mov r0, sp
    ldr r3, lit2_loadsheet
    bl call3b
    ldr r0, lit2_rgfx
    str r0, [sp]
    ldr r0, lit2_sheethi        @ size 128 | tag<<16
    str r0, [sp, #4]
    mov r0, sp
    ldr r3, lit2_loadsheet
    bl call3b                   @ LoadSpriteSheet
    ldr r0, lit2_rpal
    str r0, [sp]
    ldr r0, lit2_tagr
    str r0, [sp, #4]
    mov r0, sp
    ldr r3, lit2_loadcpal
    bl call3b                   @ LoadCompressedSpritePalette
    ldr r0, lit2_boxtemplate
    movs r1, #16
    movs r2, #86
    movs r3, #2
    ldr r4, lit2_createsprite
    bl call4b                   @ box sprite (behind)
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #0x40
    beq ws_badge2
    bl sprite_ptr
    ldr r1, lit2_mycb
    str r1, [r0, #0x1C]
ws_badge2:
    ldr r0, lit2_rtemplate
    movs r1, #16
    movs r2, #64
    movs r3, #0
    ldr r4, lit2_createsprite
    bl call4b                   @ R badge (front)
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #0x40
    beq ws_ret
    bl sprite_ptr
    ldr r1, lit2_mycb
    str r1, [r0, #0x1C]
ws_ret:
    add sp, #8
    pop {r4, r5, pc}

widget_hide:
    push {r4, r5, lr}
    ldr r4, lit2_gsprites
    movs r5, #0
wh_loop:
    movs r1, #0x3E
    ldrb r0, [r4, r1]
    movs r1, #1
    tst r0, r1
    beq wh_next
    ldr r0, [r4, #0x1C]
    ldr r1, lit2_mycb
    cmp r0, r1
    bne wh_next
    adds r0, r4, #0
    ldr r3, lit2_freeoam
    bl call3b                   @ FreeSpriteOamMatrix
    adds r0, r4, #0
    ldr r3, lit2_destroysprite
    bl call3b                   @ DestroySprite
wh_next:
    adds r4, #0x44
    adds r5, #1
    cmp r5, #64
    blo wh_loop
    ldr r0, lit2_tagball
    ldr r3, lit2_freetiles
    bl call3b
    ldr r0, lit2_tagball
    ldr r3, lit2_freepal
    bl call3b
    ldr r0, lit2_tagr
    ldr r3, lit2_freetiles
    bl call3b
    ldr r0, lit2_tagr
    ldr r3, lit2_freepal
    bl call3b
    ldr r0, lit2_tagbox
    ldr r3, lit2_freetiles
    bl call3b
    pop {r4, r5, pc}

@ hide_hook: entry of PlayerBufferExecCompleted (0x0805748C); hides widget then resumes the original at +8
hide_hook:
    push {r4, lr}
    sub sp, #4
    bl widget_hide
    ldr r1, lit2_ctrlfuncs
    ldr r4, lit2_activebattler
    ldr r0, lit2_execcont
    bx r0

call3b:
    bx r3
call4b:
    bx r4

.align 2
lit2_gsprites:      .word 0x02020630
lit2_mycb:          .word my_cb + 1
lit2_tagball:       .word 0x5E5E
lit2_tagr:          .word 0x5E5F
lit2_sheethi:       .word 0x5E5F0080
lit2_c00:           .word 0xC00
lit2_additemicon:   .word 0x081AFE71
lit2_loadsheet:     .word 0x080084F9
lit2_loadcpal:      .word 0x0803458D
lit2_createsprite:  .word 0x08006DF5
lit2_freeoam:       .word 0x080075F5
lit2_destroysprite: .word 0x080070E9
lit2_freetiles:     .word 0x08008569
lit2_freepal:       .word 0x0800884D
lit2_rgfx:          .word RGFX_ADDR
lit2_rpal:          .word RPAL_ADDR
lit2_rtemplate:     .word RTEMPLATE_ADDR
lit2_boxgfx:        .word BOXGFX_ADDR
lit2_boxsheethi:    .word 0x5E600200
lit2_tagbox:        .word 0x5E60
lit2_boxtemplate:   .word BOXTEMPLATE_ADDR
lit2_ctrlfuncs:     .word 0x03005D60
lit2_activebattler: .word 0x02024064
lit2_execcont:      .word 0x08057495
