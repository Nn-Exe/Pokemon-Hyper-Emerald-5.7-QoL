@ Registered key items as a ring around the player (Hyper Emerald v5.7), after Brilliant Diamond / Shining Pearl.
@ SELECT: four boxes above, right of, below and left of the player hold the registered items' Bag icons (a grey box
@ for an empty direction), the PC sits in the middle with arrows and an A badge. D-pad uses that item, A opens the
@ PC, B or SELECT closes - the same as the text popup it replaces (pcanywhere), whose use_item, PC script and
@ unfreeze/unlock it calls.
@
@ NO PC HERE. In the map sections listed at NOPC (Rainbow Castle, Allearth Forest, Giant Chasm, Spear Pillar, the
@ Distortion World, Mt. Silver) the centre is drawn with a red cross and A only buzzes; the text popup's A buzzes
@ too. Always, story or not. A real PC on those maps is a map script and never comes here.
@
@ PALETTES. On the field the first 12 sprite palettes are reserved for the people on the map and the rest is mostly
@ taken by weather and field effects; the ring needs 1 + one per registered item. The field is frozen while the ring
@ is up, so it borrows palette slots that no sprite in use points at (from 15 down), saving each one's tag and both
@ its colour buffers, and puts all three back when it closes. If there are not enough, the text popup opens instead.
@ The icons come from AddItemIconSprite; its palette load finds the slot already tagged (gReservedSpritePaletteCount
@ is 0 for the few calls that create the sprites, so a tag in any slot is found) and so uses the colours loaded
@ there with LoadCompressedPalette.
@
@ ring_open replaces keyreg's `bl new_draw` (called after the field is locked and frozen); what it returns goes into
@ the task's data[0]: 0x100 | the centre sprite's id for the ring, else the text window's id. ring_task is the
@ popup's task; for a text popup it simply runs pcanywhere's task. The ring's state block (Alloc) hangs off the
@ centre sprite's data[0..1].
@ state: +0 u8 ids[9] (boxes up/right/down/left, centre, icons up/right/down/left; 0xFF none)  +9 u8 slots
@  +10 u8 slot[5] (slot[0] the ring's own)  +16 u16 old tag[5]  +32 saved unfaded[5][32]  +192 saved faded[5][32]
.thumb

@ ring_open() -> r0
ring_open:
    push {r4, r5, r6, r7, lr}
    movs r5, #1                 @ palettes wanted: the ring's, then one per registered item
    movs r6, #0
ro_count:
    adds r0, r6, #0
    bl slot_item
    cmp r0, #0
    beq ro_cnext
    adds r5, #1
ro_cnext:
    adds r6, #1
    cmp r6, #4
    blo ro_count
    ldr r0, litA_statesize
    ldr r3, litA_alloczeroed
    bl call3
    adds r4, r0, #0
    cmp r4, #0
    beq ro_text
    bl free_slots
    cmp r0, r5
    bhs ro_ring
    adds r0, r4, #0             @ not enough palettes on this map: the text popup
    ldr r3, litA_free
    bl call3
ro_text:
    ldr r3, litA_newdraw
    bl call3
    b ro_ret
ro_ring:
    strb r5, [r4, #9]
    bl borrow
    bl build
    ldrb r0, [r4, #4]
    cmp r0, #64
    blo ro_up
    adds r0, r4, #0             @ no sprite for the centre: undo it all, the text popup
    bl ring_close
    b ro_text
ro_up:
    movs r1, #1
    lsls r1, r1, #8
    orrs r0, r1
ro_ret:
    pop {r4, r5, r6, r7, pc}

@ slot_item(r0 = direction 0-3) -> r0 = the item registered there, or 0
slot_item:
    ldr r1, litA_sb1ptr
    ldr r1, [r1]
    cmp r0, #0
    bne si_extra
    ldr r0, litA_496
    adds r0, r0, r1
    ldrh r0, [r0]
    bx lr
si_extra:
    lsls r0, r0, #1
    adds r0, r0, r1
    ldr r1, litA_9c0
    adds r0, r0, r1
    ldrh r0, [r0]
    bx lr

@ blocked() -> r0 = non-zero when the map's section is in NOPC (leaf: r0-r2 only)
blocked:
    ldr r0, litA_mapheader
    ldrb r0, [r0, #0x14]        @ gMapHeader.regionMapSectionId
    ldr r1, litA_nopc
bk_loop:
    ldrb r2, [r1]
    cmp r2, #0xFF
    beq bk_no
    adds r1, #1
    cmp r2, r0
    bne bk_loop
    movs r0, #1
    bx lr
bk_no:
    movs r0, #0
    bx lr

@ free_slots(r4 = state, r5 = how many) -> r0 = how many palette slots no sprite in use points at were found
@ (into state slot[], from 15 down)
free_slots:
    push {r4, r5, r6, r7, lr}
    sub sp, #16
    movs r0, #0
    str r0, [sp]
    str r0, [sp, #4]
    str r0, [sp, #8]
    str r0, [sp, #12]
    ldr r6, litA_gsprites
    movs r7, #0
fs_sprite:
    adds r0, r6, #0
    adds r0, #0x3E
    ldrb r0, [r0]
    lsls r0, r0, #31            @ inUse
    beq fs_next
    ldrb r0, [r6, #5]
    lsrs r0, r0, #4             @ its palette
    movs r1, #1
    mov r2, sp
    strb r1, [r2, r0]
fs_next:
    adds r6, #0x44
    adds r7, #1
    cmp r7, #64
    blo fs_sprite
    movs r7, #15
    movs r6, #0
fs_pick:
    mov r2, sp
    ldrb r0, [r2, r7]
    cmp r0, #0
    bne fs_skip
    adds r1, r4, #0
    adds r1, #10
    strb r7, [r1, r6]
    adds r6, #1
    cmp r6, r5
    bhs fs_done
fs_skip:
    subs r7, #1
    bpl fs_pick
fs_done:
    adds r0, r6, #0
    add sp, #16
    pop {r4, r5, r6, r7, pc}

@ borrow(r4 = state): each slot's tag and colours saved, our tag in its place; the ring's palette into slot[0]
borrow:
    push {r4, r5, r6, r7, lr}
    movs r5, #0
bw_loop:
    ldrb r0, [r4, #9]
    cmp r5, r0
    bhs bw_pal
    adds r0, r4, #0
    adds r0, #10
    ldrb r6, [r0, r5]           @ the slot
    ldr r0, litA_paltags
    lsls r1, r6, #1
    ldrh r2, [r0, r1]
    lsls r3, r5, #1
    adds r3, r3, r4
    strh r2, [r3, #16]          @ old tag
    ldr r2, litA_tag_pal0
    adds r2, r2, r5
    strh r2, [r0, r1]           @ ours
    lsls r7, r6, #5             @ the slot's 32 bytes
    ldr r0, litA_unfaded
    adds r0, r0, r7
    lsls r1, r5, #5
    adds r1, #32
    adds r1, r4, r1
    bl copy32
    ldr r0, litA_faded
    adds r0, r0, r7
    lsls r1, r5, #5
    adds r1, #192
    adds r1, r4, r1
    bl copy32
    adds r5, #1
    b bw_loop
bw_pal:
    ldr r0, litA_ringpal
    ldrb r1, [r4, #10]
    lsls r1, r1, #4
    adds r1, #0xFF
    adds r1, #1                 @ 0x100 + slot * 16
    movs r2, #32
    ldr r3, litA_loadpalette
    bl call3
    pop {r4, r5, r6, r7, pc}

@ copy32(r0 = src, r1 = dst): 32 bytes, a halfword at a time (palette RAM mirrors are halfword-safe)
copy32:
    movs r2, #0
c32_loop:
    ldrh r3, [r0, r2]
    strh r3, [r1, r2]
    adds r2, #2
    cmp r2, #32
    blo c32_loop
    bx lr

call3:
    bx r3
call6:
    bx r6

.align 2
litA_statesize:  .word 352
litA_alloczeroed: .word 0x08000B4D
litA_free:       .word 0x08000B61
litA_newdraw:    .word NEWDRAW_ADDR
litA_sb1ptr:     .word 0x03005D8C
litA_496:        .word 0x496
litA_9c0:        .word 0x9C0
litA_gsprites:   .word 0x02020630
litA_paltags:    .word 0x03000CF0           @ sSpritePaletteTags
litA_tag_pal0:   .word 0x5E90
litA_unfaded:    .word 0x02037914           @ gPlttBufferUnfaded + 0x200: the sprite palettes
litA_faded:      .word 0x02037D14           @ gPlttBufferFaded + 0x200
litA_ringpal:    .word RINGPAL_ADDR
litA_loadpalette: .word 0x080A1939
litA_mapheader:  .word 0x02037318           @ gMapHeader
litA_nopc:       .word NOPC_ADDR

@ build(r4 = state): the boxes, the icons and the centre
build:
    push {r4, r5, r6, r7, lr}
    sub sp, #8
    ldr r0, litB_boxsheet
    ldr r3, litB_loadsheet
    bl call3b
    ldr r0, litB_emptysheet
    ldr r3, litB_loadsheet
    bl call3b
    bl blocked                  @ the centre: the PC, or the PC crossed out
    ldr r1, litB_centresheet
    cmp r0, #0
    beq bd_centre
    ldr r1, litB_centrexsheet
bd_centre:
    adds r0, r1, #0
    ldr r3, litB_loadsheet
    bl call3b
    ldr r0, litB_reserved       @ tags in every slot are found while we make the sprites
    ldrb r1, [r0]
    str r1, [sp]
    movs r1, #0
    strb r1, [r0]
    movs r0, #1
    str r0, [sp, #4]            @ the next icon's palette: slot[1], slot[2], ...
    movs r5, #0                 @ direction
bd_dir:
    adds r0, r5, #0
    bl slot_item
    adds r7, r0, #0             @ r7 = item or 0
    ldr r0, litB_emptytpl
    cmp r7, #0
    beq bd_box
    ldr r0, litB_boxtpl
bd_box:
    ldr r1, litB_boxx
    ldrb r1, [r1, r5]
    ldr r2, litB_boxy
    ldrb r2, [r2, r5]
    movs r3, #2                 @ behind the icon
    ldr r6, litB_createsprite
    bl call6b
    strb r0, [r4, r5]
    movs r0, #0xFF
    adds r1, r4, r5
    strb r0, [r1, #5]           @ no icon yet
    cmp r7, #0
    beq bd_next
    ldr r0, [sp, #4]            @ which borrowed slot
    adds r1, r4, #0
    adds r1, #10
    ldrb r6, [r1, r0]
    adds r0, r7, #0             @ its colours: the icon's own palette into that slot
    movs r1, #1
    ldr r3, litB_iconpicpal
    bl call3b
    lsls r1, r6, #4
    adds r1, #0xFF
    adds r1, #1
    movs r2, #32
    ldr r3, litB_loadcomppal
    bl call3b
    ldr r0, litB_tag_icon0      @ AddItemIconSprite(tiles tag, palette tag, item)
    adds r0, r0, r5
    ldr r1, litB_tag_pal0
    ldr r2, [sp, #4]
    adds r1, r1, r2
    adds r2, r7, #0
    ldr r3, litB_additemicon
    bl call3b
    adds r1, r4, r5
    strb r0, [r1, #5]
    cmp r0, #64
    bhs bd_used
    movs r1, #0x44              @ over its box, in front (priority 0), the 24x24 icon centred
    muls r1, r0, r1
    ldr r0, litB_gsprites
    adds r0, r0, r1
    ldr r1, litB_boxx
    ldrb r1, [r1, r5]
    adds r1, #4
    strh r1, [r0, #0x20]
    ldr r1, litB_boxy
    ldrb r1, [r1, r5]
    adds r1, #4
    strh r1, [r0, #0x22]
    ldrb r1, [r0, #5]
    movs r2, #0x0C
    bics r1, r2
    strb r1, [r0, #5]
bd_used:
    ldr r0, [sp, #4]
    adds r0, #1
    str r0, [sp, #4]
bd_next:
    adds r5, #1
    cmp r5, #4
    blo bd_dir
    ldr r0, litB_centretpl
    movs r1, #CENTRE_X
    movs r2, #CENTRE_Y
    movs r3, #1
    ldr r6, litB_createsprite
    bl call6b
    strb r0, [r4, #4]
    cmp r0, #64
    bhs bd_done
    movs r1, #0x44              @ the state's address in the centre sprite's data[0..1]
    muls r1, r0, r1
    ldr r0, litB_gsprites
    adds r0, r0, r1
    adds r0, #0x2E
    strh r4, [r0]
    lsrs r1, r4, #16
    strh r1, [r0, #2]
bd_done:
    ldr r0, litB_reserved
    ldr r1, [sp]
    strb r1, [r0]
    add sp, #8
    pop {r4, r5, r6, r7, pc}

@ ring_close(r0 = state): every sprite and sheet gone, the borrowed palettes back as they were, the state freed
ring_close:
    push {r4, r5, r6, r7, lr}
    adds r4, r0, #0
    movs r5, #0
rc_sprites:
    ldrb r0, [r4, r5]
    cmp r0, #64
    bhs rc_snext
    movs r1, #0x44
    muls r0, r1, r0
    ldr r1, litB_gsprites
    adds r0, r0, r1
    ldr r3, litB_destroysprite
    bl call3b
rc_snext:
    adds r5, #1
    cmp r5, #9
    blo rc_sprites
    movs r5, #0
rc_tags:
    ldr r0, litB_tag_box
    adds r0, r0, r5
    ldr r3, litB_freetiles
    bl call3b
    adds r5, #1
    cmp r5, #7                  @ box, empty box, centre, icons 0-3
    blo rc_tags
    movs r5, #0
rc_pal:
    ldrb r0, [r4, #9]
    cmp r5, r0
    bhs rc_free
    adds r0, r4, #0
    adds r0, #10
    ldrb r6, [r0, r5]
    lsls r1, r5, #1
    adds r1, r1, r4
    ldrh r2, [r1, #16]
    ldr r0, litB_paltags
    lsls r1, r6, #1
    strh r2, [r0, r1]           @ the old tag
    lsls r7, r6, #5
    lsls r0, r5, #5
    adds r0, #32
    adds r0, r4, r0
    ldr r1, litB_unfaded
    adds r1, r1, r7
    bl copy32
    lsls r0, r5, #5
    adds r0, #192
    adds r0, r4, r0
    ldr r1, litB_faded
    adds r1, r1, r7
    bl copy32
    adds r5, #1
    b rc_pal
rc_free:
    adds r0, r4, #0
    ldr r3, litB_free
    bl call3b
    pop {r4, r5, r6, r7, pc}

@ ring_task(r0 = task id): the popup's task
ring_task:
    push {r4, r5, r6, r7, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24            @ r4 = task id
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, litB_gtasks
    adds r5, r1, r0
    adds r5, #8                 @ r5 = data
    ldrh r0, [r5]
    movs r1, #1
    lsls r1, r1, #8
    tst r0, r1
    bne rt_ring
    ldr r0, litB_gmain          @ a text popup: pcanywhere's task runs it, but not its A here
    ldrh r1, [r0, #0x2E]
    movs r0, #1
    tst r0, r1
    beq rt_text
    bl blocked
    cmp r0, #0
    bne rt_buzz
rt_text:
    adds r0, r4, #0
    ldr r3, litB_newtask
    bl call3b
    b rt_ret
rt_ring:
    ldrh r0, [r5, #2]           @ data[1]: nothing on the frame the task was made
    cmp r0, #0
    bne rt_input
    movs r0, #1
    strh r0, [r5, #2]
    b rt_ret
rt_input:
    ldr r0, litB_gmain
    ldrh r1, [r0, #0x2E]        @ newKeys
    movs r6, #0
    movs r0, #0x40              @ UP
    tst r0, r1
    bne rt_dir
    movs r6, #1
    movs r0, #0x10              @ RIGHT
    tst r0, r1
    bne rt_dir
    movs r6, #2
    movs r0, #0x80              @ DOWN
    tst r0, r1
    bne rt_dir
    movs r6, #3
    movs r0, #0x20              @ LEFT
    tst r0, r1
    bne rt_dir
    movs r0, #1                 @ A: the PC
    tst r0, r1
    bne rt_pc
    movs r0, #6                 @ B or SELECT: close
    tst r0, r1
    beq rt_ret
    bl rt_close
    ldr r3, litB_unfreeze
    bl call3b
    ldr r3, litB_unlock
    bl call3b
    b rt_ret
rt_dir:
    adds r0, r6, #0
    bl slot_item
    adds r7, r0, #0
    cmp r7, #0
    beq rt_ret                  @ nothing registered there
    bl rt_close
    adds r0, r7, #0
    ldr r3, litB_useitem
    bl call3b
    b rt_ret
rt_pc:
    bl blocked
    cmp r0, #0
    beq rt_open
rt_buzz:
    movs r0, #32                @ SE_FAILURE: no PC here, the ring stays up
    ldr r3, litB_playse
    bl call3b
    b rt_ret
rt_open:
    bl rt_close
    ldr r0, litB_pcscript
    ldr r3, litB_setupscript
    bl call3b                   @ the PC menu; its releaseall unfreezes and unlocks when you log off
rt_ret:
    pop {r4, r5, r6, r7, pc}

@ rt_close(r4 = task id, r5 = its data): the ring down, the task gone
rt_close:
    push {lr}
    ldrh r0, [r5]
    lsls r0, r0, #24
    lsrs r0, r0, #24            @ the centre sprite: the state's address is in its data[0..1]
    movs r1, #0x44
    muls r0, r1, r0
    ldr r1, litB_gsprites
    adds r0, r0, r1
    adds r0, #0x2E
    ldrh r2, [r0]
    ldrh r1, [r0, #2]
    lsls r1, r1, #16
    orrs r1, r2
    adds r0, r1, #0
    bl ring_close
    adds r0, r4, #0
    ldr r3, litB_destroytask
    bl call3b
    pop {pc}

call3b:
    bx r3
call6b:
    bx r6

.align 2
litB_boxsheet:     .word BOXSHEET_ADDR
litB_emptysheet:   .word EMPTYSHEET_ADDR
litB_centresheet:  .word CENTRESHEET_ADDR
litB_loadsheet:    .word 0x080084F9
litB_reserved:     .word 0x0300301C         @ gReservedSpritePaletteCount
litB_emptytpl:     .word EMPTYTPL_ADDR
litB_boxtpl:       .word BOXTPL_ADDR
litB_centretpl:    .word CENTRETPL_ADDR
litB_boxx:         .word BOXX_ADDR
litB_boxy:         .word BOXY_ADDR
litB_createsprite: .word 0x08006DF5
litB_iconpicpal:   .word 0x081AFFFD         @ GetItemIconPicOrPalette(item, 1 = palette)
litB_loadcomppal:  .word 0x080A18F5         @ LoadCompressedPalette
litB_tag_icon0:    .word 0x5E83
litB_tag_pal0:     .word 0x5E90
litB_tag_box:      .word 0x5E80
litB_additemicon:  .word 0x081AFE71
litB_gsprites:     .word 0x02020630
litB_destroysprite: .word 0x080070E9
litB_freetiles:    .word 0x08008569         @ FreeSpriteTilesByTag
litB_paltags:      .word 0x03000CF0
litB_unfaded:      .word 0x02037914
litB_faded:        .word 0x02037D14
litB_free:         .word 0x08000B61
litB_gtasks:       .word 0x03005E00
litB_newtask:      .word NEWTASK_ADDR
litB_gmain:        .word 0x030022C0
litB_unfreeze:     .word 0x080984F5         @ ScriptUnfreezeObjectEvents
litB_unlock:       .word 0x08098E61         @ UnlockPlayerFieldControls
litB_useitem:      .word USEITEM_ADDR
litB_pcscript:     .word PCSCRIPT_ADDR
litB_setupscript:  .word 0x08098EF9
litB_destroytask:  .word 0x080A909D
litB_centrexsheet: .word CENTREXSHEET_ADDR
litB_playse:       .word 0x080A37A5
