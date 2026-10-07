@ Seed the RNG from the cartridge clock at power-on (Hyper Emerald v5.7). Thumb-1 only.
@ rng_seed replaces AgbMain's `bl RtcInit` (0x080003DA, through a veneer): it runs RtcInit as before, reads the
@ clock into sRtc with RtcGetInfo (the game's own default date when there is no clock), and hashes year, month, day,
@ weekday, hour, minute and second into gRngValue. Emerald never seeds it, so every power-on started from 0.
rng_seed:
    push {r4, lr}
    ldr r3, l_rtcinit
    bl call3
    ldr r0, l_srtc
    ldr r3, l_rtcgetinfo
    bl call3
    ldr r0, l_srtc
    ldr r1, [r0]                @ year, month, day, weekday (BCD)
    ldr r2, [r0, #4]            @ hour, minute, second, status
    lsls r2, r2, #8             @ the status byte out
    ldr r3, l_k1
    muls r2, r3, r2
    eors r1, r2
    ldr r3, l_k2
    muls r1, r3, r1
    lsrs r2, r1, #15
    eors r1, r2
    ldr r0, l_rng
    str r1, [r0]
    pop {r4, pc}
call3:
    bx r3
    mov r8, r8                  @ pad: the literals on a 4-byte boundary
l_rtcinit:          .word 0x0802F21D            @ RtcInit
l_rtcgetinfo:       .word 0x0802F289            @ RtcGetInfo(struct SiiRtcInfo *)
l_srtc:             .word 0x03000DC0            @ sRtc
l_k1:               .word 0x9E3779B1
l_k2:               .word 0x85EBCA6B
l_rng:              .word 0x03005D80            @ gRngValue
