@ Pokedex numbers 960 and up, and numbers of four digits (gen9rest, Hyper Emerald v5.7). See gen9rest_patch.py.
@
@ The hack keeps the seen and caught flags in SaveBlock1 + 0x560 / + 0x5D8, 120 bytes each: numbers 0-959.
@ Numbers 960 and up are kept in the save's overflow stream (EWRAM the hack's save code writes into every
@ sector's tail and reads back): EXT_ADDR holds a marker word, then 32 bytes seen and 32 caught (numbers
@ 960-1215). Those 68 bytes were never written by anything (bagslots' measurements, and this patch's): an old save
@ may hold whatever EWRAM held there, so they count only once the marker is MAGIC. Until then a number 960+
@ reads as not seen; the first time one is set, the area is cleared and the marker written. No hook on loading.
.thumb

@ dex_flag(r0 = number, r1 = mode) -> r0. Mode 0 seen?, 1 caught? (caught and seen), 2 set seen, 3 set caught
@ (and seen); anything else 0. Takes the place of the hack's routine at 0x09257950 (an 8-byte jump at its start)
@ and does for numbers below 960 exactly what it did: byte n >> 3, the mask from its table (entry n & 7, four
@ bytes apart), the same answers.
dex_flag:
    push {r4, r5, r6, lr}
    movs r4, r0
    movs r5, r1
    ldr r3, l_masks
    movs r2, #7
    ands r2, r0
    lsls r2, r2, #2
    ldrb r6, [r3, r2]               @ r6 = the mask
    ldr r3, l_limit
    cmp r4, r3
    bhs df_ext
    lsrs r4, r4, #3
    ldr r3, l_sb1
    ldr r3, [r3]
    adds r4, r3, r4
    ldr r1, l_seen_at
    adds r1, r4, r1                 @ r1 = the seen byte
    ldr r2, l_caught_at
    adds r2, r4, r2                 @ r2 = the caught byte
    b df_mode
df_ext:
    subs r4, r4, r3                 @ the number from 960
    ldr r3, l_ext_count
    cmp r4, r3
    bhs df_zero                     @ past the area: nothing
    ldr r0, l_ext
    ldr r1, [r0]
    ldr r2, l_magic
    cmp r1, r2
    beq df_ext_ready
    cmp r5, #2                      @ not set up yet: a question gets "no"
    blo df_zero
    cmp r5, #3
    bhi df_zero
    movs r1, #0                     @ the first write: clear the 64 bytes, then the marker
    movs r3, #16
df_clear:
    adds r0, #4
    str r1, [r0]
    subs r3, #1
    bne df_clear
    ldr r0, l_ext
    str r2, [r0]
df_ext_ready:
    lsrs r4, r4, #3
    ldr r1, l_ext
    adds r1, #4
    adds r1, r1, r4                 @ the seen byte
    movs r2, r1
    adds r2, #32                    @ the caught byte
df_mode:
    cmp r5, #0
    beq df_get_seen
    cmp r5, #1
    beq df_get_caught
    cmp r5, #2
    beq df_set_seen
    cmp r5, #3
    beq df_set_caught
df_zero:
    movs r0, #0
    pop {r4, r5, r6, pc}
df_get_caught:
    ldrb r0, [r2]
    ands r0, r6
    beq df_zero
df_get_seen:
    ldrb r0, [r1]
    ands r0, r6
    beq df_zero
df_one:
    movs r0, #1
    pop {r4, r5, r6, pc}
df_set_caught:
    ldrb r0, [r2]
    orrs r0, r6
    strb r0, [r2]
df_set_seen:
    ldrb r0, [r1]
    orrs r0, r6
    strb r0, [r1]
    b df_one

@ dex_clear(): the hack's own clearing of both arrays (New Game), then the marker off, so the area is cleared
@ the first time a number 960+ is set. Reached through the word the game's ClearPokedexFlags jumps by.
dex_clear:
    push {r4, lr}
    ldr r3, l_orig_clear
    bl call_r3
    ldr r0, l_ext
    movs r1, #0
    str r1, [r0]
    pop {r4, pc}

@ conv_dexnum(r0 = dest, r1 = value, r2 = mode, r3 = digits): ConvertIntToDecimalStringN with four digits for
@ 1000 and up. The Pokedex page and the summary screen print the number with three ("No. 025"); 1000 would come
@ out as "A00". Reached from a 16-byte jump in the game's dead copy of the old flag routine.
conv_dexnum:
    push {r4}
    ldr r4, l_thousand
    cmp r1, r4
    blo cd_go
    movs r3, #4
cd_go:
    ldr r4, l_convert
    mov ip, r4
    pop {r4}
    bx ip

@ conv_dexnum_sum: the same for the summary screen, whose box has no room for "No" and four digits: from 1000 the
@ "No" it has just copied into SUMMARY_NO (and appends the number to) is emptied, so it shows "1000" as the
@ Pokedex list does.
conv_dexnum_sum:
    push {r4}
    ldr r4, l_thousand
    cmp r1, r4
    blo cs_go
    movs r3, #0xFF
    ldr r4, l_summary_no
    strb r3, [r4]
    movs r3, #4
cs_go:
    ldr r4, l_convert
    mov ip, r4
    pop {r4}
    bx ip

@ dex_digits(r0 = the 6-byte text "{NO}000", r1 = number): the digits the Pokedex list shows. Below 1000 as the
@ game did (bytes 2-4); 1000 and up four digits in place of the "No" mark (bytes 0-3, then the end).
dex_digits:
    push {r4, r5, r6, lr}
    movs r4, r0
    movs r5, r1
    ldr r3, l_thousand
    cmp r5, r3
    bhs dd_four
    movs r0, r5
    movs r1, #100
    ldr r3, l_div
    bl call_r3
    adds r0, #0xA1
    strb r0, [r4, #2]
    movs r0, r5
    movs r1, #100
    ldr r3, l_mod
    bl call_r3
    movs r6, r0
    movs r1, #10
    ldr r3, l_div
    bl call_r3
    adds r0, #0xA1
    strb r0, [r4, #3]
    movs r0, r6
    movs r1, #10
    ldr r3, l_mod
    bl call_r3
    adds r0, #0xA1
    strb r0, [r4, #4]
    pop {r4, r5, r6, pc}
dd_four:
    movs r0, r5
    ldr r1, l_thousand
    ldr r3, l_div
    bl call_r3
    adds r0, #0xA1
    strb r0, [r4, #0]
    movs r0, r5
    ldr r1, l_thousand
    ldr r3, l_mod
    bl call_r3
    movs r5, r0                     @ below 1000 now
    movs r1, #100
    ldr r3, l_div
    bl call_r3
    adds r0, #0xA1
    strb r0, [r4, #1]
    movs r0, r5
    movs r1, #100
    ldr r3, l_mod
    bl call_r3
    movs r6, r0
    movs r1, #10
    ldr r3, l_div
    bl call_r3
    adds r0, #0xA1
    strb r0, [r4, #2]
    movs r0, r6
    movs r1, #10
    ldr r3, l_mod
    bl call_r3
    adds r0, #0xA1
    strb r0, [r4, #3]
    movs r0, #0xFF
    strb r0, [r4, #4]
    pop {r4, r5, r6, pc}

call_r3:
    bx r3
    PAD1
l_masks:        .word 0x0832A328        @ the hack's mask table (n & 7, four bytes apart)
l_limit:        .word 960
l_sb1:          .word 0x03005D8C        @ gSaveBlock1Ptr
l_seen_at:      .word 0x00000560
l_caught_at:    .word 0x000005D8
l_ext_count:    .word 256
l_ext:          .word EXT_ADDR
l_magic:        .word MAGIC
l_orig_clear:   .word ORIG_CLEAR
l_thousand:     .word 1000
l_convert:      .word 0x08008CC1        @ ConvertIntToDecimalStringN
l_summary_no:   .word 0x02021CC4        @ the summary's "No" (it appends the number from 0x02021DC4)
l_div:          .word 0x082E7B69        @ the game's division (CreateMonDexNum's own)
l_mod:          .word 0x082E7BE1        @ and remainder
