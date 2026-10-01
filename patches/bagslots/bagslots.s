@ Items pocket 100 -> 200 slots (Hyper Emerald v5.7).
@ The hack packs all five pockets back to back from EWRAM 0x0203D030 (0x08FD7EA4, reached through
@ SetBagItemsPointers) and saves them in the spare bytes at the end of each save sector (the "overflow stream",
@ 0x0203CF64-0x0203DE00). Growing the Items pocket in place would move the other four pockets on every existing
@ save, so the Items pocket moves instead: to NEW_ITEMS, 200 slots that end exactly where the stream ends.
@ A save made before this patch still holds its Items in the old place; migrate copies them over once and sets
@ MARKER - after the boot-time load, and also whenever the pocket table is set up, because an emulator save state
@ from before this patch brings back the old memory without that load (the game re-runs the setup after a battle
@ and on map loads; the Bag looked empty until a restart). A new game sets MARKER at once (ClearBag), so it is never
@ taken for an old save.
.thumb

@ SetBagItemsPointers: the hack's layout first (every pocket where it was), then Items to the new place
set_ptrs:
    push {r4, lr}
    ldr r3, lit_orig_ptrs
    bl callr3
    ldr r0, lit_pockets
    ldr r1, lit_new
    str r1, [r0]                @ gBagPockets[ITEMS].itemSlots
    movs r1, #NEW_COUNT
    strb r1, [r0, #4]           @ .capacity (u8; the Bag's row count is a u8 too, Cancel included)
    bl migrate                  @ a pre-patch save state skipped the boot-time load: migrate here (at boot the load
    pop {r4}                    @ that follows rewrites MARKER and the Items from the save anyway)
    pop {r0}
    bx r0

@ CopySaveSlotData(r0 = sector id, r1 = locations) - the hack's loader reads the whole slot and the stream;
@ then an old save's Items are copied to the new place, once
load_slot:
    push {r4, lr}
    ldr r3, lit_orig_load
    bl callr3
    adds r4, r0, #0
    cmp r0, #1                  @ SAVE_STATUS_OK
    bne ls_ret
    bl migrate
ls_ret:
    adds r0, r4, #0
    pop {r4}
    pop {r1}
    bx r1

@ migrate: unless MARKER is set, the old 100 slots into the new pocket, the other 100 emptied, MARKER set
migrate:
    push {r4, r5, lr}
    ldr r0, lit_marker
    ldr r1, [r0]
    ldr r2, lit_magic
    cmp r1, r2
    beq mg_ret
    str r2, [r0]
    ldr r0, lit_old
    ldr r1, lit_new
    movs r2, #0
    movs r3, #OLD_COUNT
    lsls r3, r3, #2             @ bytes of the old pocket
mg_copy:
    ldr r5, [r0, r2]            @ slot words as saved: id and the key-encrypted quantity together
    str r5, [r1, r2]
    adds r2, #4
    cmp r2, r3
    blo mg_copy
    movs r3, #NEW_COUNT
    lsls r3, r3, #2
    movs r5, #0
mg_zero:
    str r5, [r1, r2]            @ the slots the old pocket did not have
    adds r2, #4
    cmp r2, r3
    blo mg_zero
mg_ret:
    pop {r4, r5}
    pop {r0}
    bx r0

@ ClearBag (NewGameInitData only): the game's own loop over the five pockets, then the old Items area is
@ emptied and MARKER set, so this game's save is never migrated
clear_bag:
    push {r4, r5, lr}
    movs r4, #0
    ldr r5, lit_pockets
cb_loop:
    lsls r1, r4, #3
    adds r1, r5, r1
    ldr r0, [r1]
    ldrb r1, [r1, #4]
    ldr r3, lit_clearslots
    bl callr3
    adds r4, #1
    cmp r4, #5
    blo cb_loop
    ldr r1, lit_old
    movs r2, #0
    movs r3, #OLD_COUNT
    lsls r3, r3, #2
    movs r0, #0
cb_zero:
    str r0, [r1, r2]
    adds r2, #4
    cmp r2, r3
    blo cb_zero
    ldr r0, lit_marker
    ldr r2, lit_magic
    str r2, [r0]
    pop {r4, r5}
    pop {r0}
    bx r0

callr3:
    bx r3

.align 2
lit_orig_ptrs:  .word ORIG_PTRS_ADDR
lit_orig_load:  .word ORIG_LOAD_ADDR
lit_pockets:    .word 0x02039DD8
lit_new:        .word NEW_ADDR
lit_old:        .word OLD_ADDR
lit_marker:     .word MARKER_ADDR
lit_magic:      .word MAGIC_ADDR
lit_clearslots: .word 0x080D6C7D
