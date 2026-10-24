@ gen9abil: the battle scripts the Gen 9 abilities run, in the engine's script language (the game's battle script
@ commands; 0x83 is the engine's call into its table of routines). String ids S_... come from strings.inc.
    .include "strings.inc"
    .section .rodata.scripts, "a"

    .macro printstring id
    .byte 0x10
    .hword \id
    .endm
    .macro waitmessage t
    .byte 0x12
    .hword \t
    .endm
    .macro printfromtable table
    .byte 0x13
    .word \table
    .endm
    .macro goto to
    .byte 0x28
    .word \to
    .endm
    .macro pause t
    .byte 0x39
    .hword \t
    .endm
    .macro waitanimation
    .byte 0x0A
    .endm
    .macro return
    .byte 0x3C
    .endm
    .macro end3
    .byte 0x3F
    .endm
    .macro call to
    .byte 0x41
    .word \to
    .endm
    .macro playanimation bank, anim, arg
    .byte 0x45, \bank, \anim
    .word \arg
    .endm
    .macro removeitem bank
    .byte 0x6A, \bank
    .endm
    .macro setbyte at, value
    .byte 0x2E
    .word \at
    .byte \value
    .endm
    .macro waitstate
    .byte 0x3A
    .endm

    .equ STAT_CHANGER_AT, 0x0202448E
    .equ TARGET_AT, 0x0202420C
    .equ ABILITY_GUARD_DOG_ID, 0x109
    .include "callasm.inc"

    .macro callasm index
    .byte 0x83
    .hword \index
    .endm
    .macro addbyte at, value
    .byte 0x2F
    .word \at
    .byte \value
    .endm

    .equ BANK_TARGET, 0
    .equ BANK_ATTACKER, 1
    .equ BANK_SCRIPTING, 10
    .equ ANIM_HELD_ITEM, 7

@ ---------------------------------------------------------------------- the Ruin four, on entering
    .global BS_G9_RUIN
BS_G9_RUIN:
    pause 0x10
    call BS_PRINT_SCR_ACTIVE_ABILITY
    printfromtable g9_ruin_strings
    waitmessage 0x40
    end3

@ ---------------------------------------------------------------------- Protosynthesis, Quark Drive
@ the multistring chooser holds the boosted stat - 1
    .global BS_G9_PROTO_SUN
BS_G9_PROTO_SUN:
    pause 0x10
    printstring S_PROTO_SUN
    goto g9_paradox_stat

    .global BS_G9_QUARK_TERRAIN
BS_G9_QUARK_TERRAIN:
    pause 0x10
    printstring S_QUARK_TERRAIN
    goto g9_paradox_stat

    .global BS_G9_BOOSTER_PROTO
BS_G9_BOOSTER_PROTO:
    playanimation BANK_SCRIPTING, ANIM_HELD_ITEM, 0
    waitanimation
    removeitem BANK_SCRIPTING
    pause 0x20
    printstring S_BOOSTER_PROTO
    goto g9_paradox_stat

    .global BS_G9_BOOSTER_QUARK
BS_G9_BOOSTER_QUARK:
    playanimation BANK_SCRIPTING, ANIM_HELD_ITEM, 0
    waitanimation
    removeitem BANK_SCRIPTING
    pause 0x20
    printstring S_BOOSTER_QUARK
g9_paradox_stat:
    waitmessage 0x40
    printfromtable g9_paradox_strings
    waitmessage 0x40
    end3

    .global BS_G9_END_PROTO
BS_G9_END_PROTO:
    printstring S_END_PROTO
    waitmessage 0x40
    end3

    .global BS_G9_END_QUARK
BS_G9_END_QUARK:
    printstring S_END_QUARK
    waitmessage 0x40
    end3

@ ---------------------------------------------------------------------- hit
@ Anger Shell: the target's own five stats, as the engine's self-inflicted change (a stat already at its end is
@ passed over by the change routine)
    .global BS_G9_ANGER_SHELL
BS_G9_ANGER_SHELL:
    waitstate
    call BS_PRINT_DEF_ABILITY
    setbyte STAT_CHANGER_AT, 0x92
    call BS_CHANGE_DEF_STAT_SELFINFLICTED
    setbyte STAT_CHANGER_AT, 0x95
    call BS_CHANGE_DEF_STAT_SELFINFLICTED
    setbyte STAT_CHANGER_AT, 0x11
    call BS_CHANGE_DEF_STAT_SELFINFLICTED
    setbyte STAT_CHANGER_AT, 0x13
    call BS_CHANGE_DEF_STAT_SELFINFLICTED
    setbyte STAT_CHANGER_AT, 0x14
    call BS_CHANGE_DEF_STAT_SELFINFLICTED
    return

@ Electromorphosis, Wind Power: charged
    .global BS_G9_CHARGE
BS_G9_CHARGE:
    call BS_PRINT_DEF_ABILITY
    printstring S_CHARGE
    waitmessage 0x40
    return

@ Toxic Debris
    .global BS_G9_TOXIC_DEBRIS
BS_G9_TOXIC_DEBRIS:
    pause 0x10
    call BS_PRINT_DEF_ABILITY
    printstring S_TOXIC_DEBRIS
    waitmessage 0x40
    return

@ ---------------------------------------------------------------------- Orichalcum Pulse, Hadron Engine
    .global BS_G9_ORICHALCUM
BS_G9_ORICHALCUM:
    call BS_PRINT_SCR_ACTIVE_ABILITY
    printstring S_ORICHALCUM
    waitmessage 0x40
    goto BS_DROUGHT_TAIL                @ "The sunlight turned harsh!", the animation, Castform

    .global BS_G9_ORICHALCUM_ON
BS_G9_ORICHALCUM_ON:
    call BS_PRINT_SCR_ACTIVE_ABILITY
    printstring S_ORICHALCUM_ON
    waitmessage 0x40
    end3

    .global BS_G9_HADRON
BS_G9_HADRON:
    call BS_PRINT_SCR_ACTIVE_ABILITY
    printstring S_HADRON
    waitmessage 0x40
    goto BS_ELECTRIC_SURGE_TAIL         @ the terrain's animation and message, Terrain Seeds

    .global BS_G9_HADRON_ON
BS_G9_HADRON_ON:
    call BS_PRINT_SCR_ACTIVE_ABILITY
    printstring S_HADRON_ON
    waitmessage 0x40
    end3

@ ---------------------------------------------------------------------- Supreme Overlord
    .global BS_G9_OVERLORD
BS_G9_OVERLORD:
    pause 0x10
    call BS_PRINT_SCR_ACTIVE_ABILITY
    printstring S_OVERLORD
    waitmessage 0x40
    end3

@ ---------------------------------------------------------------------- moves
@ Good as Gold: as the engine's "It doesn't affect..." with the target's ability shown first
    .global BS_G9_NOT_AFFECTED_ABILITY
BS_G9_NOT_AFFECTED_ABILITY:
    .byte 0x02                          @ attackstring
    .byte 0x03                          @ ppreduce
    call BS_PRINT_DEF_ABILITY
    goto BS_NOT_AFFECTED

@ Intimidate's stat change for each target (its loop calls this in place of the engine's own): Guard Dog's
@ Attack goes up instead
    .global BS_G9_INTIMIDATE_STAT
BS_G9_INTIMIDATE_STAT:
    .byte 0x1E, BANK_TARGET             @ jumpifability target, Guard Dog, no Mold Breaker
    .hword ABILITY_GUARD_DOG_ID
    .byte 0
    .word g9_guard_dog
    goto BS_CHANGE_DEF_STAT
g9_guard_dog:
    call BS_PRINT_DEF_ABILITY
    setbyte STAT_CHANGER_AT, 0x11
    goto BS_CHANGE_DEF_STAT

@ ---------------------------------------------------------------------- entry: the others
@ Supersweet Syrup: Intimidate's loop over the foes (the engine's commands), evasion -1
    .global BS_G9_SYRUP
BS_G9_SYRUP:
    callasm 150                         @ every target behind a substitute: nothing
    .word g9_syrup_end
    pause 0x20
    setbyte TARGET_AT, 0
    call BS_PRINT_ATK_ABILITY
    printstring S_SYRUP
    waitmessage 0x40
    .byte 0x70, BANK_ATTACKER           @ recordability
g9_syrup_loop:
    .byte 0xE1                          @ the next foe, or done
    .word g9_syrup_end
    callasm 26                          @ behind a substitute: the next one
    .word g9_syrup_next
    setbyte STAT_CHANGER_AT, 0x97
    call BS_CHANGE_DEF_STAT
g9_syrup_next:
    addbyte TARGET_AT, 1
    goto g9_syrup_loop
g9_syrup_end:
    end3

@ Hospitality: gBattleMoveDamage holds the heal (negative), the target is the partner
    .global BS_G9_HOSPITALITY
BS_G9_HOSPITALITY:
    call BS_PRINT_ATK_ABILITY
    .byte 0x35                          @ orword gHitMarker, through a substitute
    .word 0x02024280, 0x100
    .byte 0x0B, BANK_TARGET             @ graphicalhpupdate
    .byte 0x0C, BANK_TARGET             @ datahpupdate
    printstring S_HOSPITALITY
    waitmessage 0x40
    end3

@ Costar: the partner's stat stages (the game's Psych Up command)
    .global BS_G9_COSTAR
BS_G9_COSTAR:
    pause 0x10
    call BS_PRINT_SCR_ACTIVE_ABILITY
    .byte 0xBD                          @ copyfoestats
    .word g9_costar_end
    printstring 0x9C                    @ "... copied ...'s stat changes!"
    waitmessage 0x40
g9_costar_end:
    end3

@ ---------------------------------------------------------------------- Tailwind
@ Tailwind's script goes here once its message is shown (in place of its last goto)
    .global BS_G9_TAILWIND
BS_G9_TAILWIND:
    callasm G9_ASM_TAILWIND
    goto BS_ENDTURN

    .global BS_G9_TW_RIDER_ATK
BS_G9_TW_RIDER_ATK:
    call BS_PRINT_ATK_ABILITY
    call BS_CHANGE_ATK_STAT_SELFINFLICTED
    return

    .global BS_G9_TW_RIDER_DEF
BS_G9_TW_RIDER_DEF:
    call BS_PRINT_DEF_ABILITY
    call BS_CHANGE_DEF_STAT_SELFINFLICTED
    return

    .global BS_G9_TW_POWER_ATK
BS_G9_TW_POWER_ATK:
    call BS_PRINT_ATK_ABILITY
    printstring S_CHARGE_ATK
    waitmessage 0x40
    return

    .global BS_G9_TW_POWER_DEF
BS_G9_TW_POWER_DEF:
    call BS_PRINT_DEF_ABILITY
    printstring S_CHARGE
    waitmessage 0x40
    return

@ ---------------------------------------------------------------------- the abilities that keep something
@ Cud Chew: the Berry in gLastUsedItem, eaten as Bug Bite eats one (the engine's routines 158 and 117: its effect,
@ then what eating a Berry sets off)
    .global BS_G9_CUD_CHEW
BS_G9_CUD_CHEW:
    pause 0x10
    call BS_PRINT_ATK_ABILITY
    callasm 158
    callasm 117
    end3

@ Opportunist: the attacker copies the stages gen9abil kept for it, one stat at a time
    .global BS_G9_OPPORTUNIST
BS_G9_OPPORTUNIST:
    pause 0x10
    call BS_PRINT_ATK_ABILITY
g9_opportunist_loop:
    callasm G9_ASM_OPPORTUNIST          @ the next stat in the stat changer, or done
    .word g9_opportunist_end
    call BS_CHANGE_ATK_STAT_SELFINFLICTED
    goto g9_opportunist_loop
g9_opportunist_end:
    end3

@ Commander: the scripting battler is Tatsugiri, the target its Dondozo; Dondozo's five stats +2 (the engine's
@ routines 153 and 154: several stats in one, as its moves do)
    .global BS_G9_COMMANDER
BS_G9_COMMANDER:
    pause 0x10
    call BS_PRINT_SCR_ACTIVE_ABILITY
    printstring S_COMMANDER
    waitmessage 0x40
    callasm 153
    .byte BANK_TARGET | 0x40, 0x1F, 0x20  @ the target, self-inflicted; Attack..Sp. Def; +2
    .word g9_commander_end
    callasm 154
    .word BS_CHANGE_DEF_STAT_SELFINFLICTED
    .byte 0x1F, 0x20
g9_commander_end:
    end3

@ Tera Shell: before the hit is shown
    .global BS_G9_TERA_SHELL
BS_G9_TERA_SHELL:
    call BS_PRINT_DEF_ABILITY
    printstring S_TERA_SHELL
    waitmessage 0x40
    return

@ ---------------------------------------------------------------------- string tables
    .balign 2
g9_ruin_strings:
    .hword S_TABLETS, S_SWORD, S_VESSEL, S_BEADS
g9_paradox_strings:
    .hword S_PARADOX_ATK, S_PARADOX_DEF, S_PARADOX_SPEED, S_PARADOX_SPATK, S_PARADOX_SPDEF
