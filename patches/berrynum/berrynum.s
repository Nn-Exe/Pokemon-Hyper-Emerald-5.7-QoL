@ Berry numbers in the Bag (Hyper Emerald v5.7).
@ The Berries pocket prints each berry as "No" + (item id - 132) in two digits, which is right for the 43
@ vanilla berries (Cheri 133 = No01 ... Enigma 175 = No43). The hack's own berries are items 704-727 (Occa ...
@ Maranga) and 762-765, so they came out as 572-633, and a two-digit field shows a "?" for a tens digit above
@ 9: "No?2". Here they continue the list instead: Occa = No44 ... Maranga = No67, then 762-765 = No68-71.
@
@ Four places print that number, and all are hooked where they compute it:
@   hack:  the hack's own item-name routine, in two identical copies (the original ROM has both): 0x08FD5E20 and
@          0x08FD7D3C, "No + number + name" when the open pocket is Berries. The Bag's list rows come from these.
@          Their code at 0x08FD5E32 / 0x08FD7D4E (subs r1,#0x84; movs r3,#2; movs r2,#2; ldr r0,=gStringVar1;
@          ldr r6,=ConvertIntToDecimalStringN) is a 10-byte trampoline now; we replay it and go back to the bl
@          (a bx r6 veneer) right after, at 0x08FD5E3C / 0x08FD7D58.
@   list:  0x081C540C, the game's own "No + number + name" for anything in the Berries pocket (other lists). Its
@          code at 0x081C5422 (ldr r0,=gStringVar1; adds r1,r4,#0; subs r1,#0x84; movs r2,#2; movs r3,#2) is a
@          10-byte trampoline now; we replay it and go back to its bl ConvertIntToDecimalStringN at 0x081C542C.
@   name:  the Bag's item-name routine, berry case, 0x081AB420 (ldr r0,=gStringVar1; adds r1,r5,#0;
@          subs r1,#0x84; movs r2,#2) is an 8-byte trampoline; back to 0x081AB428, which sets r3 itself.
@ All three functions return through the stack, so lr is dead where we come in and the bl below costs nothing.
.thumb

@ the hack's routine, both copies: item id in r1. r3 must come back as 2, so the jump home goes through r12.
hack_hook:
    ldr r2, lit_back_hack
    b hack_common
hack2_hook:
    ldr r2, lit_back_hack2
hack_common:
    mov r12, r2
    bl number
    ldr r0, lit_strvar1
    ldr r6, lit_convert
    movs r2, #2
    movs r3, #2
    bx r12

@ vanilla list routine: item id in r4. r3 must come back as 2, so the jump home goes through r12.
list_hook:
    adds r1, r4, #0
    bl number
    ldr r0, lit_strvar1
    ldr r2, lit_back_list
    mov r12, r2
    movs r2, #2
    movs r3, #2
    bx r12

@ item-name routine: item id in r5; 0x081AB428 sets r3 itself.
name_hook:
    adds r1, r5, #0
    bl number
    ldr r0, lit_strvar1
    movs r2, #2
    ldr r3, lit_back_name
    bx r3

@ number(r1 = item id) -> r1 = the number to show. Uses r2.
number:
    ldr r2, lit_first_new
    cmp r1, r2
    bcc n_vanilla
    ldr r2, lit_second_new
    cmp r1, r2
    bcc n_new
    subs r1, r1, r2
    adds r1, #68                @ 762-765: after Maranga (No67)
    bx lr
n_new:
    ldr r2, lit_first_new
    subs r1, r1, r2
    adds r1, #44                @ Occa: after Enigma (No43)
    bx lr
n_vanilla:
    subs r1, #0x84              @ the game's own rule: Cheri (133) = No01
    bx lr
PAD
.align 2
lit_strvar1:        .word 0x02021CC4    @ gStringVar1
lit_first_new:      .word 704           @ Occa Berry
lit_second_new:     .word 762           @ the first of the four after Maranga
lit_convert:        .word 0x08008CC1    @ ConvertIntToDecimalStringN
lit_back_hack:      .word 0x08FD5E3D    @ bl (bx r6) in the hack's routine, first copy
lit_back_hack2:     .word 0x08FD7D59    @ the same in the second copy
lit_back_list:      .word 0x081C542D    @ bl ConvertIntToDecimalStringN in the list routine
lit_back_name:      .word 0x081AB429    @ movs r3,#2 in the item-name routine
