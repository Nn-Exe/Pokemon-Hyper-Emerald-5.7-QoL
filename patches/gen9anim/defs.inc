@ the battle animation commands (the game's own, 0x00..0x2F) and the values of the names anims.s uses
.macro loadparticle loadparticleID
.byte 0x0
.hword \loadparticleID
.endm
.macro unloadparticle unloadparticleID
.byte 0x1
.hword \unloadparticleID
.endm
.macro launchtemplate launchtemplatePtr launchtemplatePriority launchtemplateArgsNo launchtemplatearg0 launchtemplatearg1 launchtemplatearg2 launchtemplatearg3 launchtemplatearg4 launchtemplatearg5 launchtemplatearg6 launchtemplatearg7 launchtemplatearg8
.byte 0x2
.word \launchtemplatePtr
.byte \launchtemplatePriority
.byte \launchtemplateArgsNo
.hword \launchtemplatearg0
.hword \launchtemplatearg1
.hword \launchtemplatearg2
.hword \launchtemplatearg3
.hword \launchtemplatearg4
.hword \launchtemplatearg5
.hword \launchtemplatearg6
.hword \launchtemplatearg7
.hword \launchtemplatearg8
.endm
.macro launchtask launchtaskPtr launchtaskPriority launchtaskArgsNo launchtaskarg0 launchtaskarg1 launchtaskarg2 launchtaskarg3 launchtaskarg4 launchtaskarg5 launchtaskarg6 launchtaskarg7 launchtaskarg8
.byte 0x3
.word \launchtaskPtr
.byte \launchtaskPriority
.byte \launchtaskArgsNo
.hword \launchtaskarg0
.hword \launchtaskarg1
.hword \launchtaskarg2
.hword \launchtaskarg3
.hword \launchtaskarg4
.hword \launchtaskarg5
.hword \launchtaskarg6
.hword \launchtaskarg7
.hword \launchtaskarg8
.endm
.macro pause pause_cmdToWait
.byte 0x4
.byte \pause_cmdToWait
.endm
.macro waitanimation
.byte 0x5
.endm
.macro endanimation
.byte 0x8
.endm
.macro pokespritetoBG animABank
.byte 0xA
.byte \animABank
.endm
.macro pokespritefromBG animBBank
.byte 0xB
.byte \animBBank
.endm
.macro setblends setblends_value
.byte 0xC
.hword \setblends_value
.endm
.macro resetblends
.byte 0xD
.endm
.macro call call_cmd_ptr
.byte 0xE
.word \call_cmd_ptr
.endm
.macro return
.byte 0xF
.endm
.macro setarg setargID setargValue
.byte 0x10
.byte \setargID
.hword \setargValue
.endm
.macro choosetwoturnanim choosetwoturnanim1 choosetwoturnanim2
.byte 0x11
.word \choosetwoturnanim1
.word \choosetwoturnanim2
.endm
.macro goto goto_cmdPtr
.byte 0x13
.word \goto_cmdPtr
.endm
.macro loadBG1 loadBG1ID
.byte 0x14
.byte \loadBG1ID
.endm
.macro loaddefaultBG
.byte 0x15
.endm
.macro waitforBG
.byte 0x16
.endm
.macro waitfortransparentBG
.byte 0x17
.endm
.macro loadBG2 loadBG2ID
.byte 0x18
.byte \loadBG2ID
.endm
.macro playsound2 playsound2ID playsound2Unkown
.byte 0x19
.hword \playsound2ID
.byte \playsound2Unkown
.endm
.macro playsoundpanchange anim1BsongID anim1BArg3 anim1BArg4 anim1BArg5 anim1BArg6
.byte 0x1B
.hword \anim1BsongID
.byte \anim1BArg3
.byte \anim1BArg4
.byte \anim1BArg5
.byte \anim1BArg6
.endm
.macro soundcomplex anim1Carg1 anim1Carg2 anim1Carg3 anim1Carg4
.byte 0x1C
.hword \anim1Carg1
.byte \anim1Carg2
.byte \anim1Carg3
.byte \anim1Carg4
.endm
.macro playsound3 anim1Darg1 anim1Darg2 anim1Darg3
.byte 0x1D
.hword \anim1Darg1
.byte \anim1Darg2
.byte \anim1Darg3
.endm
.macro launchsoundtask launchsoundtaskPtr launchsoundtaskArgsNo launchsoundtaskarg0 launchsoundtaskarg1 launchsoundtaskarg2 launchsoundtaskarg3 launchsoundtaskarg4 launchsoundtaskarg5 launchsoundtaskarg6 launchsoundtaskarg7
.byte 0x1F
.word \launchsoundtaskPtr
.byte \launchsoundtaskArgsNo
.hword \launchsoundtaskarg0
.hword \launchsoundtaskarg1
.hword \launchsoundtaskarg2
.hword \launchsoundtaskarg3
.hword \launchsoundtaskarg4
.hword \launchsoundtaskarg5
.hword \launchsoundtaskarg6
.hword \launchsoundtaskarg7
.endm
.macro jumpifargmatches jumpifargmatchesargID jumpifargmatchesValue jumpifargmatchesPtr
.byte 0x21
.byte \jumpifargmatchesargID
.hword \jumpifargmatchesValue
.word \jumpifargmatchesPtr
.endm
.macro leftbankBG_over_partnerBG anim28Bank
.byte 0x28
.byte \anim28Bank
.endm
.macro bankBG_over_partnerBG
.byte 0x29
.endm
.macro objtemplate objtemplatetiletag objtemplatepaltag objtemplateoam objtemplateimageanim objtemplategfx objtemplaterotscale objtemplatecallback
.hword \objtemplatetiletag
.hword \objtemplatepaltag
.word \objtemplateoam
.word \objtemplateimageanim
.word \objtemplategfx
.word \objtemplaterotscale
.word \objtemplatecallback
.endm
    .equ AnimTask_BlendColorCycle, 0x08115A05
    .equ AnimTask_ShakeMon, 0x080D51AD
    .equ AnimTask_StartSlidingBg, 0x08117661
    .equ JUMP_KICK_ANIM, 0x82d216e
    .equ PAL_ATK, 0x2
    .equ PAL_DEF, 0x4
    .equ SPIT_UP_ANIM, 0x82d49eb
    .equ TEMPL_0x857fe28, 0x857fe28
    .equ TEMPL_0x85923a8, 0x85923a8
    .equ TEMPL_0x8597358, 0x8597358
    .equ TEMPL_0x85973a0, 0x85973a0
    .equ UNSET_SCROLLING_BG, 0x82d7cdd
    .equ gBattlerAttacker, 0x0
    .equ gBattlerTarget, 0x1
    .equ side_attacker, 0x2
    .equ side_target, 0x3
    .equ v_creator_callback, 0x09D4520D
