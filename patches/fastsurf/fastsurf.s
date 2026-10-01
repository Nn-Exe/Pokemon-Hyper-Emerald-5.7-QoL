@ Faster surfing (Hyper Emerald v5.7): hold B while surfing to go at the Mach Bike's top speed.
@
@ PlayerNotOnBikeMoving's surfing branch (0x0808AF5A: adds r0, r5, #0; bl PlayerWalkFast; b epilogue) becomes
@ ldr r0, =surf_hook; bx r0, with the literal in the dead nops auto-run left behind in the same function. Like
@ auto-run's run_hook it is entered with r4 = &gPlayerAvatar, r5 = direction, r6 = heldKeys, and leaves through
@ the function's epilogue (pop {r4-r6, pc}). The rule is the running one: B held XOR Auto Run -> PlayerWalkFaster
@ (4 px a frame), else the game's PlayerWalkFast (2 px). Collisions, ledges, getting off onto land and currents are
@ decided before this branch and are not touched.
.thumb

surf_hook:
    movs r0, #2                 @ B_BUTTON
    ands r0, r6
    lsrs r0, r0, #1
    ldr r1, lit_sb1ptr
    ldr r1, [r1, #4]            @ gSaveBlock2Ptr (it follows gSaveBlock1Ptr)
    ldrb r1, [r1, #0x13]        @ optionsButtonMode: 0, or 4 = Auto Run
    lsrs r1, r1, #2
    eors r0, r1
    ldr r3, lit_walk_fast
    beq sh_go
    ldr r3, lit_walk_faster
sh_go:
    adds r0, r5, #0
    bl call3
    ldr r0, lit_epilogue
    bx r0
call3:
    bx r3

.align 2
lit_sb1ptr:      .word 0x03005D8C       @ gSaveBlock1Ptr
lit_walk_fast:   .word 0x0808B739       @ PlayerWalkFast
lit_walk_faster: .word 0x0808B769       @ PlayerWalkFaster
lit_epilogue:    .word 0x0808AFB7       @ PlayerNotOnBikeMoving: pop {r4, r5, r6}; pop {r0}; bx r0
