@ The Yes answer of the repel prompts (Hyper Emerald v5.7): "The Repel ended... Use another?" and the L quick repel.
@ use_repel is called with callnative from the new Yes script. It applies gSpecialVar_ItemId the way the hack's
@ Task_UseRepel (0x080FE164) does - VarSet(0x4021, item << 8 | holdEffectParam) - and then calls RemoveUsedItem
@ (RemoveBagItem(item, 1), the item's name into gStringVar2). The script plays the sound and prints the message
@ itself, so the player stays locked until the repel is on.
.thumb
use_repel:
    push {r4, lr}
    ldr r4, lit_itemid
    ldrh r0, [r4]
    ldr r3, lit_param
    bl call3                    @ ItemId_GetHoldEffectParam(item) = the steps
    ldrh r1, [r4]
    lsls r1, r1, #8
    orrs r1, r0                 @ (item << 8) | steps
    ldr r0, lit_var
    ldr r3, lit_varset
    bl call3                    @ VarSet(0x4021, ...)
    ldr r3, lit_removeused
    bl call3                    @ RemoveUsedItem
    pop {r4}
    pop {r0}
    bx r0

call3:
    bx r3

.align 2
lit_itemid:     .word 0x0203CE7C
lit_param:      .word 0x080D7501
lit_var:        .word 0x4021
lit_varset:     .word 0x0809D6B1
lit_removeused: .word 0x080FE059
