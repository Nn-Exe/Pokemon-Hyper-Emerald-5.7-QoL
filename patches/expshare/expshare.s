@ Exp. Share on/off (Hyper Emerald v5.7).
@ The hack's Exp. Share is a key item that works for the whole party while it is in the Bag: its experience
@ code asks CheckBagHasItem(Exp. Share, 1) at four places. Those calls now come to share_check, which answers
@ exactly as CheckBagHasItem does, except that the Exp. Share counts as absent while OFF_FLAG is set.
@ Using the item flips OFF_FLAG and says which way it went. The flag starts clear: on, as before.
.thumb

@ share_check(r0 = item, r1 = count) -> r0 = CheckBagHasItem(item, count), and 0 for a switched-off Exp. Share
share_check:
    push {r4, lr}
    adds r4, r0, #0
    ldr r3, lit_hasitem
    bl callr3
    cmp r0, #0
    beq sc_ret
    cmp r4, #EXP_SHARE
    bne sc_ret
    ldr r0, lit_offflag
    ldr r3, lit_flagget
    bl callr3
    movs r1, #1
    eors r0, r1                 @ in the Bag: on unless the flag is set
sc_ret:
    pop {r4}
    pop {r1}
    bx r1

@ ItemUseOutOfBattle_ExpShare(r0 = taskId): flip, then the message the way the game's key items show one -
@ expanded into gStringVar4 first; over the Bag, or on the field when used from SELECT.
item_use:
    push {r4, r5, lr}
    lsls r0, r0, #24
    lsrs r4, r0, #24
    lsls r1, r4, #2
    adds r1, r1, r4
    lsls r1, r1, #3
    ldr r0, lit_gtasks
    adds r5, r1, r0
    ldr r0, lit_offflag
    ldr r3, lit_flagget
    bl callr3
    cmp r0, #0
    beq iu_turnoff
    ldr r0, lit_offflag
    ldr r3, lit_flagclear
    bl callr3
    ldr r1, lit_str_on
    b iu_say
iu_turnoff:
    ldr r0, lit_offflag
    ldr r3, lit_flagset
    bl callr3
    ldr r1, lit_str_off
iu_say:
    ldr r0, lit_strvar4
    ldr r3, lit_expand
    bl callr3
    movs r1, #0xE
    ldrsh r0, [r5, r1]          @ data[3]: 1 when used from the field
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

callr3:
    bx r3
callr4:
    bx r4

.align 2
lit_hasitem:     .word 0x080D6725    @ CheckBagHasItem
lit_flagget:     .word 0x0809D791
lit_flagset:     .word 0x0809D741
lit_flagclear:   .word 0x0809D769
lit_offflag:     .word OFF_FLAG
lit_gtasks:      .word 0x03005E00
lit_strvar4:     .word 0x02021FC4
lit_expand:      .word 0x08008EE1    @ StringExpandPlaceholders
lit_bagmsg:      .word 0x081ABB4D    @ message over the Bag
lit_bagmsgcb:    .word 0x081ABBBD
lit_fieldmsg:    .word 0x081978ED    @ message on the field
lit_fieldmsgcb:  .word 0x080FD1F9
lit_str_on:      .word STR_ON_ADDR
lit_str_off:     .word STR_OFF_ADDR
