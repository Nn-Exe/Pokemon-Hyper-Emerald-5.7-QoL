@ The gold healthbox keeps its palette (Hyper Emerald v5.7). See goldbox_patch.py for the report and the why.
@
@ gold_pass takes the place of shinybox's shiny_boxes (typeicons calls it once per battle frame, after
@ AnimateSprites and before the OAM buffer is built). The gold palette lives in a sprite palette slot that is
@ CLAIMED with a tag of its own (GOLDTAG), so the game's allocator can no longer hand the slot to an animation;
@ it is a copy of the stock healthbox palette as it is now, with colour 2 (the box fill) gold; and the colour the
@ game writes for a battler's status icon (index 12 + battler, into whichever slot that box is on) is kept the
@ same in both palettes.
@ load_pal / alloc_pal are the game's LoadSpritePalette / AllocSpritePalette, whole, with one difference: when no
@ slot is free they ask make_room, which gives up one of OUR palettes - the type badges' first (the badges are
@ hidden until their palette can come back), then the gold (the boxes go back to the stock palette) - so the
@ game never goes without a palette because of them.
@ ti_load is what typeicons calls to load its palette when it is not loaded.
.thumb

entry_gold:  b gold_pass
entry_load:  b load_pal
entry_alloc: b alloc_pal
entry_ti:    b ti_load

@ ================================================================ once per battle frame
@ [sp, #0] the stock slot, [sp, #4] the gold slot or -1, [sp, #8] a shiny battler's box was seen, [sp, #12] body
gold_pass:
    push {r4, r5, r6, r7, lr}
    sub sp, #16
    ldr r0, litA_boxtag
    bl find_tag
    str r0, [sp, #0]
    cmp r0, #0
    bge gp_stock
    b gp_out                    @ no healthbox palette loaded: nothing to do
gp_stock:
    ldr r0, litA_goldtag
    bl find_tag
    str r0, [sp, #4]
    movs r0, #0
    str r0, [sp, #8]
    ldr r4, litA_sprites
    movs r5, #0
gp_loop:
    ldrh r0, [r4, #0x3E]
    movs r1, #1
    tst r1, r0
    bne gp_used
    b gp_next
gp_used:
    ldrh r0, [r4, #4]
    lsrs r7, r0, #12            @ r7 = the palette slot the sprite is on
    ldr r1, [sp, #0]
    cmp r7, r1
    beq gp_box
    cmp r7, #10                 @ (the gold slot, and the copy the level-up flash makes, are 10 or more)
    bhs gp_box
    b gp_next
gp_box:
    bl box_of                   @ r0 = battler or -1, r1 = 1 for a body
    cmp r0, #0
    bge gp_is
    b gp_next
gp_is:
    adds r6, r0, #0
    str r1, [sp, #12]
    ldr r0, [sp, #0]
    cmp r7, r0
    beq gp_known
    ldr r0, [sp, #4]
    cmp r7, r0
    beq gp_known
    @ on some other slot: the level-up flash copies the box palette and moves the box onto the copy
    adds r0, r6, #0
    bl is_shiny
    cmp r0, #0
    bne gp_gold                 @ a shiny battler's: straight back to the gold (which has its colours)
    lsls r0, r7, #1
    ldr r1, litA_tags
    ldrh r0, [r1, r0]
    ldr r1, litA_ffff
    cmp r0, r1
    beq gp_plain                @ nobody's slot: back to the stock palette
    b gp_next                   @ somebody's: the game put it there and takes it back itself
gp_known:
    ldr r0, [sp, #12]
    cmp r0, #0
    beq gp_test
    adds r0, r7, #0             @ a body: its status colour, from the slot it is on to the stock slot
    adds r1, r6, #0
    ldr r2, [sp, #0]
    bl carry
    ldr r2, [sp, #4]            @ ... and to the gold slot
    cmp r2, #0
    blt gp_test
    adds r0, r7, #0
    adds r1, r6, #0
    bl carry
gp_test:
    adds r0, r6, #0
    bl is_shiny
    cmp r0, #0
    beq gp_plain
gp_gold:
    movs r0, #1
    str r0, [sp, #8]
    ldr r0, [sp, #4]
    cmp r0, #0
    bge gp_set
    ldr r0, [sp, #0]
    bl claim
    str r0, [sp, #4]
    cmp r0, #0
    bge gp_set                  @ (no slot to be had: the box stays on the stock palette)
gp_plain:
    ldr r0, [sp, #0]
gp_set:
    ldrh r1, [r4, #4]
    lsls r1, r1, #20
    lsrs r1, r1, #20
    lsls r0, r0, #12
    orrs r1, r0
    strh r1, [r4, #4]
gp_next:
    adds r4, #0x44
    adds r5, #1
    cmp r5, #64
    bhs gp_end
    b gp_loop
gp_end:
    ldr r0, [sp, #4]
    cmp r0, #0
    blt gp_out
    ldr r1, [sp, #8]
    cmp r1, #0
    bne gp_keep
    lsls r0, r0, #1             @ no shiny battler: the slot goes back to the game
    ldr r1, litA_tags
    ldr r2, litA_ffff
    strh r2, [r1, r0]
    b gp_out
gp_keep:
    ldr r1, [sp, #0]
    bl maintain
gp_out:
    add sp, #16
    pop {r4, r5, r6, r7, pc}

@ box_of(r4 = a sprite in use) -> r0 = its battler if it is a healthbox body or right half, else -1;
@ r1 = 1 for a body. A healthbox is three sprites: the body (callback SpriteCallbackDummy, data[5] = its HP bar
@ sprite, data[6] = battler), the right half (callback 0x08072925, data[5] = the body) and the HP bar (callback
@ 0x080728B5, the bar palette).
box_of:
    push {lr}
    ldr r0, [r4, #0x1C]
    ldr r1, litA_bodycb
    cmp r0, r1
    beq bo_body
    ldr r1, litA_rightcb
    cmp r0, r1
    bne bo_none
    ldrh r0, [r4, #0x38]
    bl sprite_ptr
    cmp r0, #0
    beq bo_none
    ldrh r0, [r0, #0x3A]
    movs r1, #0
    b bo_check
bo_body:
    ldrh r0, [r4, #0x38]
    bl sprite_ptr
    cmp r0, #0
    beq bo_none
    ldr r0, [r0, #0x1C]
    ldr r1, litA_barcb
    cmp r0, r1
    bne bo_none
    ldrh r0, [r4, #0x3A]
    movs r1, #1
bo_check:
    cmp r0, #4
    blo bo_ret
bo_none:
    movs r0, #0
    mvns r0, r0
bo_ret:
    pop {pc}

@ is_shiny(r0 = battler) -> r0 = 1 if gBattleMons[battler] is there and shiny
is_shiny:
    lsls r1, r0, #6
    lsls r2, r0, #4
    adds r1, r1, r2
    lsls r2, r0, #3
    adds r1, r1, r2             @ battler * 0x58
    ldr r2, litA_battlemons
    adds r1, r1, r2
    movs r0, #0
    ldrh r2, [r1]               @ species: 0 while the battle is being set up
    cmp r2, #0
    beq is_ret
    ldr r2, [r1, #0x48]         @ personality
    ldr r3, [r1, #0x54]         @ otId
    eors r2, r3
    lsrs r3, r2, #16
    eors r2, r3
    lsls r2, r2, #16
    lsrs r2, r2, #16
    cmp r2, #SHINY_ODDS
    bhs is_ret
    movs r0, #1
is_ret:
    bx lr

@ find_tag(r0 = tag) -> r0 = its slot in sSpritePaletteTags, or -1
find_tag:
    ldr r1, litA_tags
    movs r2, #0
ft_loop:
    lsls r3, r2, #1
    ldrh r3, [r1, r3]
    cmp r3, r0
    beq ft_hit
    adds r2, #1
    cmp r2, #16
    blo ft_loop
    movs r2, #0
    mvns r2, r2
ft_hit:
    adds r0, r2, #0
    bx lr

@ sprite_ptr(r0 = sprite index) -> r0 = &gSprites[index], or 0 if out of range / not in use
sprite_ptr:
    cmp r0, #64
    bhs sp_none
    lsls r1, r0, #6
    lsls r2, r0, #2
    adds r1, r1, r2             @ * 0x44
    ldr r2, litA_sprites
    adds r0, r1, r2
    ldrh r1, [r0, #0x3E]
    movs r2, #1
    tst r2, r1
    beq sp_none
    bx lr
sp_none:
    movs r0, #0
    bx lr

PADA
.align 2
litA_boxtag:     .word 0x0000D6FF
litA_goldtag:    .word GOLDTAG
litA_tags:       .word 0x03000CF0
litA_ffff:       .word 0x0000FFFF
litA_sprites:    .word 0x02020630
litA_battlemons: .word 0x02024084
litA_bodycb:     .word 0x08007429
litA_rightcb:    .word 0x08072925
litA_barcb:      .word 0x080728B5

@ ================================================================ the two palettes
@ carry(r0 = from slot, r1 = battler, r2 = to slot): that battler's status colour (index 12 + battler), in
@ both buffers
carry:
    cmp r0, r2
    beq cy_ret
    push {r4, lr}
    adds r1, #12
    lsls r1, r1, #1
    lsls r0, r0, #5
    adds r0, r0, r1             @ from
    lsls r2, r2, #5
    adds r2, r2, r1             @ to
    ldr r3, litB_unfaded
    ldrh r4, [r3, r0]
    ldrh r1, [r3, r2]
    cmp r1, r4
    beq cy_faded
    strh r4, [r3, r2]
cy_faded:
    ldr r3, litB_faded
    ldrh r4, [r3, r0]
    ldrh r1, [r3, r2]
    cmp r1, r4
    beq cy_done
    strh r4, [r3, r2]
cy_done:
    pop {r4, pc}
cy_ret:
    bx lr

@ claim(r0 = the stock slot) -> r0 = the slot taken for the gold, or -1. The highest free one from 15 down to 10
@ (the game hands out the lowest), tagged, with the stock palette as it is now in both buffers.
claim:
    push {r4, r5, r6, lr}
    adds r5, r0, #0
    ldr r0, litB_tags
    movs r4, #15
cl_loop:
    lsls r1, r4, #1
    ldrh r1, [r0, r1]
    ldr r2, litB_ffff
    cmp r1, r2
    beq cl_take
    subs r4, #1
    cmp r4, #10
    bhs cl_loop
    movs r0, #0
    mvns r0, r0
    b cl_ret
cl_take:
    lsls r1, r4, #1
    ldr r2, litB_goldtag
    strh r2, [r0, r1]
    lsls r5, r5, #5
    lsls r6, r4, #5
    ldr r0, litB_unfaded
    bl cl_copy
    ldr r0, litB_faded
    bl cl_copy
    adds r0, r4, #0
cl_ret:
    pop {r4, r5, r6, pc}
cl_copy:                        @ (r0 = a buffer's OBJ half, r5 = from, r6 = to): 16 colours
    movs r2, #0
cc_loop:
    adds r1, r5, r2
    ldrh r3, [r0, r1]
    adds r1, r6, r2
    strh r3, [r0, r1]
    adds r2, #2
    cmp r2, #32
    blo cc_loop
    bx lr

@ maintain(r0 = the gold slot, r1 = the stock slot). Unfaded: the stock palette's colours 0-11 with the gold at 2
@ (12-15 are the status colours: carry). Faded: the same as its unfaded while the stock palette is shown as it
@ is; while a fade has the stock palette the gold slot is left to that fade, so the gold box is as dark as the
@ plain one beside it.
maintain:
    push {r4, r5, r6, r7, lr}
    lsls r4, r0, #5
    lsls r5, r1, #5
    ldr r6, litB_unfaded
    movs r2, #0
mt_copy:
    adds r0, r5, r2
    ldrh r3, [r6, r0]
    cmp r2, #4
    bne mt_c2
    ldr r3, litB_gold
mt_c2:
    adds r0, r4, r2
    ldrh r1, [r6, r0]
    cmp r1, r3
    beq mt_c3
    strh r3, [r6, r0]
mt_c3:
    adds r2, #2
    cmp r2, #24
    blo mt_copy
    ldr r7, litB_faded
    movs r2, #0
mt_same:
    adds r0, r5, r2
    ldrh r3, [r6, r0]
    ldrh r1, [r7, r0]
    cmp r3, r1
    bne mt_ret
    adds r2, #2
    cmp r2, #32
    blo mt_same
    movs r2, #0
mt_show:
    adds r0, r4, r2
    ldrh r3, [r6, r0]
    ldrh r1, [r7, r0]
    cmp r3, r1
    beq mt_s2
    strh r3, [r7, r0]
mt_s2:
    adds r2, #2
    cmp r2, #32
    blo mt_show
mt_ret:
    pop {r4, r5, r6, r7, pc}

PADB
.align 2
litB_unfaded:    .word 0x02037914        @ gPlttBufferUnfaded + 0x200 (the OBJ half)
litB_faded:      .word 0x02037D14        @ gPlttBufferFaded   + 0x200
litB_tags:       .word 0x03000CF0
litB_ffff:       .word 0x0000FFFF
litB_goldtag:    .word GOLDTAG
litB_gold:       .word GOLDCOLOUR

@ ================================================================ the game's allocator
@ LoadSpritePalette(r0 = {data, u16 tag}) -> r0 = slot, 0xFF if none
load_pal:
    push {r4, r5, lr}
    adds r5, r0, #0
    ldrh r0, [r5, #4]
    ldr r3, litC_indexof
    bl callr3
    lsls r0, r0, #24
    lsrs r4, r0, #24
    cmp r4, #0xFF
    bne lp_ret                  @ loaded already: its slot
    ldr r0, litC_ffff
    ldr r3, litC_indexof
    bl callr3
    lsls r0, r0, #24
    lsrs r4, r0, #24
    cmp r4, #0xFF
    bne lp_have
    bl make_room
    adds r4, r0, #0
    cmp r4, #0xFF
    beq lp_ret
lp_have:
    ldr r1, litC_tags
    lsls r0, r4, #1
    ldrh r2, [r5, #4]
    strh r2, [r1, r0]
    ldr r0, [r5]
    lsls r1, r4, #4
    ldr r3, litC_doload
    bl callr3
lp_ret:
    adds r0, r4, #0
    pop {r4, r5, pc}

@ AllocSpritePalette(r0 = tag) -> r0 = slot, 0xFF if none
alloc_pal:
    push {r4, lr}
    lsls r0, r0, #16
    lsrs r4, r0, #16
    ldr r0, litC_ffff
    ldr r3, litC_indexof
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    cmp r0, #0xFF
    bne ap_have
    bl make_room
    cmp r0, #0xFF
    beq ap_ret
ap_have:
    ldr r1, litC_tags
    lsls r2, r0, #1
    strh r4, [r1, r2]
ap_ret:
    pop {r4, pc}

@ make_room -> r0 = a slot one of our palettes gave up (its tag cleared), or 0xFF
make_room:
    push {r4, r5, r6, r7, lr}
    ldr r0, litC_titag          @ the type badges first: hidden until their palette is back (ti_load)
    bl find_tag
    cmp r0, #0
    blt mr_gold
    adds r7, r0, #0
    bl hide_badges
    adds r0, r7, #0
    movs r1, #16
    bl oam_fix                  @ (this frame's OAM is built already)
    b mr_free
mr_gold:
    ldr r0, litC_goldtag        @ then the gold: its boxes go back to the stock palette
    bl find_tag
    cmp r0, #0
    blt mr_none
    adds r7, r0, #0
    ldr r0, litC_boxtag
    bl find_tag
    cmp r0, #0
    bge mr_stock
    movs r0, #4
mr_stock:
    adds r6, r0, #0
    ldr r4, litC_sprites
    movs r5, #0
mr_loop:
    ldrh r0, [r4, #0x3E]
    movs r1, #1
    tst r1, r0
    beq mr_next
    ldrh r0, [r4, #4]
    lsrs r0, r0, #12
    cmp r0, r7
    bne mr_next
    bl box_of
    cmp r0, #0
    blt mr_next
    cmp r1, #0
    beq mr_move
    adds r1, r0, #0             @ a body: its status colour goes with it
    adds r0, r7, #0
    adds r2, r6, #0
    bl carry
mr_move:
    ldrh r0, [r4, #4]
    lsls r0, r0, #20
    lsrs r0, r0, #20
    lsls r1, r6, #12
    orrs r0, r1
    strh r0, [r4, #4]
mr_next:
    adds r4, #0x44
    adds r5, #1
    cmp r5, #64
    blo mr_loop
    adds r0, r7, #0
    adds r1, r6, #0
    bl oam_fix
mr_free:
    lsls r0, r7, #1
    ldr r1, litC_tags
    ldr r2, litC_ffff
    strh r2, [r1, r0]
    adds r0, r7, #0
    pop {r4, r5, r6, r7, pc}
mr_none:
    movs r0, #0xFF
    pop {r4, r5, r6, r7, pc}

@ ti_load(r0 = typeicons' {palette, tag}) -> r0 = its slot, or 0xFF with the badges hidden. Called by typeicons on
@ every battle frame its tag is not loaded. While a move animation has palettes loaded (tags 0x2710..0x2B0F) it
@ waits for two free slots, so that it does not take back, in the middle of the animation, the slot the animation
@ is about to ask for again; otherwise one free slot will do.
ti_load:
    push {r4, r5, r6, lr}
    adds r6, r0, #0
    ldr r0, litC_reserved
    ldrb r1, [r0]
    ldr r0, litC_tags
    ldr r3, litC_ffff
    movs r2, #0                 @ free slots
    movs r5, #1                 @ the least that will do
tl_count:
    cmp r1, #16
    bhs tl_counted
    lsls r4, r1, #1
    ldrh r4, [r0, r4]
    cmp r4, r3
    bne tl_c2
    adds r2, #1
    b tl_c3
tl_c2:
    push {r3}
    ldr r3, litC_animtags
    subs r4, r4, r3
    lsrs r4, r4, #10            @ 0 for a tag from 0x2710 up to 0x2B0F
    pop {r3}
    bne tl_c3
    movs r5, #2
tl_c3:
    adds r1, #1
    b tl_count
tl_counted:
    cmp r2, r5
    blo tl_hide
    adds r0, r6, #0
    bl load_pal
    adds r5, r0, #0
    cmp r5, #16
    bhs tl_hide
    ldr r4, litC_sprites        @ the badges there are go onto the slot it has now
    movs r6, #64
tl_loop:
    ldrh r0, [r4, #0x3E]
    movs r1, #1
    tst r1, r0
    beq tl_next
    ldr r0, [r4, #0x1C]
    ldr r1, litC_badgecb
    cmp r0, r1
    bne tl_next
    ldrh r0, [r4, #4]
    lsls r0, r0, #20
    lsrs r0, r0, #20
    lsls r1, r5, #12
    orrs r0, r1
    strh r0, [r4, #4]
tl_next:
    adds r4, #0x44
    subs r6, #1
    bne tl_loop
    adds r0, r5, #0
    pop {r4, r5, r6, pc}
tl_hide:
    bl hide_badges
    movs r0, #0xFF
    pop {r4, r5, r6, pc}

@ hide_badges: every type badge sprite (their callback is typeicons' badge_cb) invisible
hide_badges:
    push {r4, lr}
    ldr r0, litC_sprites
    ldr r4, litC_badgecb
    movs r1, #64
hb_loop:
    ldrh r2, [r0, #0x3E]
    movs r3, #1
    tst r3, r2
    beq hb_next
    ldr r3, [r0, #0x1C]
    cmp r3, r4
    bne hb_next
    movs r3, #4
    orrs r2, r3
    strh r2, [r0, #0x3E]
hb_next:
    adds r0, #0x44
    subs r1, #1
    bne hb_loop
    pop {r4, pc}

@ oam_fix(r0 = a palette slot, r1 = another slot, or 16): in the OAM buffer already built for this frame, every
@ sprite on the first slot goes onto the second, or is not drawn (16)
oam_fix:
    push {r4, r5, lr}
    ldr r2, litC_oam
    movs r3, #128
of_loop:
    ldrh r4, [r2, #4]
    lsrs r5, r4, #12
    cmp r5, r0
    bne of_next
    cmp r1, #16
    bhs of_hide
    lsls r4, r4, #20
    lsrs r4, r4, #20
    lsls r5, r1, #12
    orrs r4, r5
    strh r4, [r2, #4]
    b of_next
of_hide:
    ldrh r4, [r2]
    movs r5, #3
    lsls r5, r5, #8
    bics r4, r5
    movs r5, #2
    lsls r5, r5, #8             @ attribute 0 bits 8-9 = 2: not drawn
    orrs r4, r5
    strh r4, [r2]
of_next:
    adds r2, #8
    subs r3, #1
    bne of_loop
    pop {r4, r5, pc}

callr3:
    bx r3

PADC
.align 2
litC_indexof:    .word 0x08008805        @ IndexOfSpritePaletteTag
litC_doload:     .word 0x080087BD        @ DoLoadSpritePalette(data, slot * 16)
litC_tags:       .word 0x03000CF0        @ sSpritePaletteTags
litC_ffff:       .word 0x0000FFFF
litC_reserved:   .word 0x0300301C        @ gReservedSpritePaletteCount
litC_sprites:    .word 0x02020630
litC_oam:        .word OAM_BUFFER        @ gMain.oamBuffer
litC_boxtag:     .word 0x0000D6FF
litC_goldtag:    .word GOLDTAG
litC_titag:      .word TITAG
litC_badgecb:    .word BADGECB
litC_animtags:   .word 0x00002710        @ ANIM_TAGS_START: the move animations' sheets and palettes
