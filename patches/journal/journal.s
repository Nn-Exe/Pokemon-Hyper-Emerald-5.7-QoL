@ Journal key item (Hyper Emerald v5.7).
@ Use it from the Bag (or SELECT once registered) and it says what to do next in the story. The objective is
@ worked out from story flags every time: find the last "anchor" step that is done, then show the first
@ step after it that is not. The step table (patches/journal/steps.py) holds the flags and the text; this
@ code only walks it. Nothing is written to the save.
@
@ The item is the Fame Checker (363), a FireRed leftover the hack never gives out, uses or sells.
.thumb

@ ---- overworld hook --------------------------------------------------------------------------------
@ Chains ahead of the previous overworld stub: hands you the Journal once, then lets the chain run on.
@ This hook is at CB2_Overworld's FIRST instruction, so lr is still the caller's live return address:
@ keep it in r4 across our calls and put it back before chaining (see docs/NOTES.md, SINNOH MAP SCREEN).
ow_stub:
    push {r4, r5}
    mov r4, lr
    ldr r0, lit_item
    movs r1, #1
    ldr r3, lit_hasitem
    bl callr3
    lsls r0, r0, #24
    bne ow_done
    ldr r0, lit_item
    movs r1, #1
    ldr r3, lit_additem
    bl callr3
ow_done:
    mov lr, r4
    pop {r4, r5}
    ldr r3, lit_prevhook
    bx r3

@ ---- the item --------------------------------------------------------------------------------------
@ ItemUseOutOfBattle_Journal(r0 = taskId). gTasks[taskId].data[3] is 1 when used from the field (SELECT)
@ and 0 from the Bag. Both paths are the game's own "message about a key item" routines, handed
@ gStringVar4, exactly as the Coin Case does.
item_use:
    push {r4, r5, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    bl build
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r5, r1, r0
    movs r1, #0xE
    ldrsh r0, [r5, r1]
    cmp r0, #1
    beq iu_field
    adds r0, r4, #0
    movs r1, #1
    ldr r2, lit_strvar4
    ldr r3, lit_bagmsgcb
    ldr r4, lit_bagmsg
    bl callr4
    pop {r4, r5, pc}
iu_field:
    adds r0, r4, #0
    ldr r1, lit_strvar4
    ldr r2, lit_fieldmsgcb
    ldr r3, lit_fieldmsg
    bl callr3
    pop {r4, r5, pc}

@ build: the objective message into gStringVar4
build:
    push {r4, r5, r6, r7, lr}
    ldr r4, lit_steps
    movs r5, #0                 @ index
    movs r6, #0                 @ where the search starts: one past the last anchor that is done
b_anchors:
    ldrb r0, [r4]
    cmp r0, #0xFF
    beq b_search
    ldrb r0, [r4, #1]
    cmp r0, #0
    beq b_anext
    adds r0, r4, #0
    bl step_done
    cmp r0, #0
    beq b_anext
    adds r6, r5, #1
b_anext:
    adds r4, #16
    adds r5, #1
    b b_anchors
b_search:
    ldr r4, lit_steps
    lsls r0, r6, #4
    adds r4, r4, r0
b_sloop:
    ldrb r0, [r4]
    cmp r0, #0xFF
    beq b_emit                  @ the terminator's text says everything is done
    adds r0, r4, #0
    bl step_done
    cmp r0, #0
    beq b_emit
    adds r4, #16
    b b_sloop
b_emit:
    ldr r0, lit_strvar4
    ldr r1, [r4, #8]
    bl append
    adds r7, r0, #0
    ldrb r0, [r4]
    cmp r0, #2
    bne b_end
    adds r0, r4, #0
    adds r1, r7, #0
    bl group_tail
    adds r7, r0, #0
b_end:
    movs r0, #0xFC              @ wait for a button on the last page, then end: the key-item message routines
    strb r0, [r7]               @ close the box the moment the text is printed, so without this the final
    movs r0, #0x09              @ page vanished before it could be read (the Sinnoh Map's message does the same)
    strb r0, [r7, #1]
    movs r0, #0xFF
    strb r0, [r7, #2]
    pop {r4, r5, r6, r7}
    pop {r0}
    bx r0

@ step_done(r0 = step) -> r0 = 1 when done.  Step: +0 mode (0 any, 1 all, 2 group), +1 anchor, +2 flag
@ count, +4 flags (u16s), +8 text, +12 group.  A group is done when one of its flags is set (a later event
@ that proves it) or when every member is.
step_done:
    push {r4, r5, r6, r7, lr}
    adds r4, r0, #0
    ldrb r5, [r4]
    ldrb r6, [r4, #2]
    ldr r7, [r4, #4]
    cmp r5, #1
    beq sd_all
sd_any:
    cmp r6, #0
    beq sd_anynone
    ldrh r0, [r7]
    bl flag
    cmp r0, #0
    bne sd_yes
    adds r7, #2
    subs r6, #1
    b sd_any
sd_anynone:
    cmp r5, #2
    bne sd_no
    adds r0, r4, #0
    bl group_count
    cmp r0, r1
    beq sd_yes
    b sd_no
sd_all:
    cmp r6, #0
    beq sd_yes
    ldrh r0, [r7]
    bl flag
    cmp r0, #0
    beq sd_no
    adds r7, #2
    subs r6, #1
    b sd_all
sd_yes:
    movs r0, #1
    b sd_ret
sd_no:
    movs r0, #0
sd_ret:
    pop {r4, r5, r6, r7}
    pop {r1}
    bx r1

@ group_count(r0 = step) -> r0 = weight done, r1 = weight in all.  Group: +0 label, +4 member count,
@ +5 list_all, then 8-byte members: +0 flag, +2 weight, +4 text.
group_count:
    push {r4, r5, r6, r7, lr}
    ldr r4, [r0, #12]
    ldrb r5, [r4, #4]
    adds r4, #8
    movs r6, #0
    movs r7, #0
gc_loop:
    cmp r5, #0
    beq gc_done
    ldrb r0, [r4, #2]
    adds r7, r7, r0
    ldrh r0, [r4]
    bl flag
    cmp r0, #0
    beq gc_next
    ldrb r0, [r4, #2]
    adds r6, r6, r0
gc_next:
    adds r4, #8
    subs r5, #1
    b gc_loop
gc_done:
    adds r0, r6, #0
    adds r1, r7, #0
    pop {r4, r5, r6, r7}
    pop {r2}
    bx r2

@ group_tail(r0 = step, r1 = write pointer) -> r0 = write pointer.  A new page: "<label> <done>/<all>",
@ then the members still missing - every one (list_all), or only the first in table order. Each goes on
@ a line of its own: the first under the progress line (newline), the rest scrolling up (0xFA).
group_tail:
    push {r4, r5, r6, r7, lr}
    adds r4, r0, #0
    adds r7, r1, #0
    bl group_count
    adds r5, r0, #0
    adds r6, r1, #0
    movs r0, #0xFB
    strb r0, [r7]
    adds r7, #1
    ldr r3, [r4, #12]
    ldr r1, [r3]
    adds r0, r7, #0
    bl append
    movs r1, #0
    strb r1, [r0]
    adds r0, #1
    adds r1, r5, #0
    bl u8dec
    movs r1, #0xBA              @ '/'
    strb r1, [r0]
    adds r0, #1
    adds r1, r6, #0
    bl u8dec
    adds r7, r0, #0
    ldr r4, [r4, #12]
    ldrb r5, [r4, #4]
    ldrb r6, [r4, #5]           @ bit 0: list every missing member; bit 1: one is written already
    adds r4, #8
gt_loop:
    cmp r5, #0
    beq gt_done
    ldrh r0, [r4]
    bl flag
    cmp r0, #0
    bne gt_next
    movs r0, #0xFE
    movs r1, #2
    tst r6, r1
    beq gt_sep
    movs r0, #0xFA
gt_sep:
    strb r0, [r7]
    adds r7, #1
    orrs r6, r1
    adds r0, r7, #0
    ldr r1, [r4, #4]
    bl append
    adds r7, r0, #0
    movs r0, #1
    tst r6, r0
    beq gt_done
gt_next:
    adds r4, #8
    subs r5, #1
    b gt_loop
gt_done:
    adds r0, r7, #0
    pop {r4, r5, r6, r7}
    pop {r1}
    bx r1

@ append(r0 = write pointer, r1 = 0xFF-terminated text) -> r0 = write pointer (no terminator written)
append:
    push {lr}
ap_loop:
    ldrb r2, [r1]
    cmp r2, #0xFF
    beq ap_done
    strb r2, [r0]
    adds r0, #1
    adds r1, #1
    b ap_loop
ap_done:
    pop {r1}
    bx r1

@ u8dec(r0 = write pointer, r1 = 0-99) -> r0 = write pointer
u8dec:
    push {lr}
    cmp r1, #10
    blt ud_one
    movs r2, #0xA1
ud_tens:
    subs r1, #10
    adds r2, #1
    cmp r1, #10
    bge ud_tens
    strb r2, [r0]
    adds r0, #1
ud_one:
    adds r1, #0xA1
    strb r1, [r0]
    adds r0, #1
    pop {r1}
    bx r1

@ flag(r0 = flag id) -> r0 = 0 / 1.  FlagGet knows the hack's own 0x4000+ flags (its GetFlagAddr).
flag:
    push {lr}
    ldr r3, lit_flagget
    bl callr3
    lsls r0, r0, #24
    lsrs r0, r0, #24
    pop {r1}
    bx r1

callr3:
    bx r3
callr4:
    bx r4

.align 2
lit_item:           .word 0x0000016B    @ the Fame Checker's slot, now the Journal
lit_hasitem:        .word 0x080D6725    @ CheckBagHasItem
lit_additem:        .word 0x080D6929    @ AddBagItem
lit_prevhook:       .word PREVHOOK_ADDR
lit_gtasks:         .word 0x03005E00
lit_strvar4:        .word 0x02021FC4    @ gStringVar4, 1000 bytes
lit_bagmsg:         .word 0x081ABB4D    @ DisplayItemMessage (over the Bag)
lit_bagmsgcb:       .word 0x081ABBBD    @ CloseItemMessage
lit_fieldmsg:       .word 0x081978ED    @ DisplayItemMessageOnField
lit_fieldmsgcb:     .word 0x080FD1F9    @ Task_CloseCantUseKeyItemMessage
lit_flagget:        .word 0x0809D791
lit_steps:          .word STEPS_ADDR
