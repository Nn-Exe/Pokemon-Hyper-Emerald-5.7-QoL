@ Auto-run toggle (R button in the overworld) for Hyper Emerald v5.7.
@ Flag byte: SaveBlock1+0x31 (vanilla struct padding between flashLevel and mapLayoutId; verified 0 in saves, unreferenced).
@ Hook 1: PlayerNotOnBikeMoving run decision @0x0808AF70 (replaced 0x0808AF70..0x0808AFAF) -> run_hook.
@ Hook 2: ProcessPlayerFieldInput entry @0x0809C014 -> toggle_hook (re-executes prologue, resumes @0x0809C01C).
.thumb
    b run_hook                  @ BASE+0
    b toggle_hook               @ BASE+2

@ entered with r5 = direction, r6 = heldKeys, r4 = &gPlayerAvatar; function epilogue at 0x0808AFB6 pops r4-r6,lr
run_hook:
    movs r0, #2                 @ B_BUTTON
    ands r0, r6
    lsrs r0, r0, #1             @ 0/1
    ldr r1, lit_sb1ptr
    ldr r1, [r1]
    movs r2, #0x31
    ldrb r1, [r1, r2]           @ auto-run flag
    eors r0, r1
    beq rh_walk
    movs r0, #0x8C
    lsls r0, r0, #4             @ this hack's running-shoes flag (0x8C0)
    ldr r3, lit_flagget
    bl call3
    lsls r0, r0, #24
    beq rh_walk
    ldr r2, lit_objevents
    ldrb r1, [r4, #5]           @ gPlayerAvatar.objectEventId
    lsls r0, r1, #3
    adds r0, r0, r1
    lsls r0, r0, #2
    adds r0, r0, r2
    ldrb r0, [r0, #0x1E]        @ currentMetatileBehavior
    ldr r3, lit_runningdisallowed
    bl call3
    cmp r0, #0
    bne rh_walk
    adds r0, r5, #0
    ldr r3, lit_playerrun
    bl call3                    @ PlayerRun(direction)
    ldrb r1, [r4]
    movs r0, #0x80
    orrs r0, r1
    strb r0, [r4]               @ PLAYER_AVATAR_FLAG_DASH
    b rh_ret
rh_walk:
    adds r0, r5, #0
    ldr r3, lit_playerwalk
    bl call3                    @ PlayerGoSpeed1(direction)
rh_ret:
    ldr r0, lit_epilogue
    bx r0

@ ProcessPlayerFieldInput entry: original prologue = push {r4,r5,r6,lr}; sub sp,#8; adds r5,r0,#0; ldr r0,=0x020375F2
toggle_hook:
    push {r4, r5, r6, lr}
    sub sp, #8
    adds r5, r0, #0
    ldr r0, lit_gmain
    ldrh r0, [r0, #0x2E]        @ newKeys
    movs r1, #1
    lsls r1, r1, #8             @ R_BUTTON
    tst r0, r1
    beq th_done
    ldr r0, lit_sb1ptr
    ldr r0, [r0]
    movs r3, #0x31
    ldrb r1, [r0, r3]
    movs r2, #1
    eors r1, r2
    strb r1, [r0, r3]
    movs r0, #5                 @ SE_SELECT on
    cmp r1, #0
    bne th_se
    movs r0, #3                 @ SE_... off (different click)
th_se:
    ldr r3, lit_playse
    bl call3
th_done:
    ldr r0, lit_sv_result_hi    @ re-execute original 4th instruction: ldr r0, =0x020375F2
    ldr r1, lit_resume
    bx r1

call3:
    bx r3

.align 2
lit_sb1ptr:            .word 0x03005D8C
lit_flagget:           .word 0x0809D791
lit_objevents:         .word 0x02037350
lit_runningdisallowed: .word 0x0811A1DD
lit_playerrun:         .word 0x0808B781
lit_playerwalk:        .word 0x0808B721
lit_epilogue:          .word 0x0808AFB7
lit_gmain:             .word 0x030022C0
lit_playse:            .word 0x080A37A5
lit_sv_result_hi:      .word 0x020375F2
lit_resume:            .word 0x0809C01D
