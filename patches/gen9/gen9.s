@ Gen 9 signature abilities, signature moves and Booster Energy (Hyper Emerald v5.7). Thumb-1 only. Names in
@ capitals are filled in by gen9_patch.py.
@
@ The battle engine keeps each battler's ability as a 16-bit id at 0x0203F000 + 2 * battler (the byte in
@ gBattleMons is its low half) and looks abilities up in two places:
@   0x09D00110  stores the ability of the Pokemon coming in (r0, from the species table) for gActiveBattler
@   0x09D73A9C  species, slot -> ability, for everything else the engine wants to know
@ g9_enter and g9_lookup take their place. An "alias" ability (Orichalcum Pulse, id 256 + Drought) is handed to
@ the engine as the ability it stands on, so the engine does everything that ability does; the summary screen
@ reads the species table through the game's own lookup and shows the alias's name and text.
@
@ Whether an ability is in effect is the engine's own question (0x09D45AEC: not under Gastro Acid, no
@ Neutralizing Gas about), asked every time: g9_abil.
@
@ Three routines the engine reaches through a table of pointers run the engine's own and add to it.
@
@ g9_damage, command 5 (the damage calculation; the engine works out type effectiveness in it too), scales
@ gBattleMoveDamage. Whole multiples come first, so that less is lost to rounding:
@   Hydro Steam        in harsh sunlight, unless its user holds a Utility Umbrella: where the engine has just
@                      halved it (a Water move, the target without that umbrella)           x 3, else x 3/2
@   Psyblade           on Electric Terrain                                                  x 3/2
@   Collision Course, Electro Drift   super effective                                       x 4/3
@   Glaive Rush        the target used it and has not started on a move since               x 2
@   Orichalcum Pulse   Koraidon with Drought attacking with its Attack in harsh sunlight    x 4/3
@   Hadron Engine      Miraidon with Electric Surge attacking with its Sp. Atk on Electric Terrain   x 4/3
@   the Ruin four      ability (stat + 2) * 256 lowers that stat of everyone else: Tablets Attack, Sword
@                      Defense, Vessel Sp. Atk, Beads Sp. Def. Another battler has the one for the stat the hit
@                      is taken on and the target does not                                  x 4/3
@                      another has the one for the attacking stat and its owner does not    x 3/4
@   Protosynthesis     in sun / Quark Drive on Electric Terrain / either with a Booster Energy: the best of the
@                      holder's Attack, Defense, Sp. Atk, Sp. Def and Speed (the first of them on a tie)
@                      it is the attacking stat                                             x 13/10
@                      it is the stat the hit is taken on                                   x 10/13
@                      Speed: nothing here, see g9_speed
@ and it marks the user of a Glaive Rush that is about to land (the command only runs once the move has hit).
@ A stat times k is the damage times k but for rounding.
@ Which stats a move uses is its category, with the engine's own exceptions: Body Press attacks with the user's
@ Defense, Foul Play with the target's Attack, Psyshock / Psystrike / Secret Sword are taken on Defense.
@
@ g9_cancel, command 0 (a battler starts on a move): Glaive Rush's mark comes off that battler, and every
@ battler's Booster Energy is looked at (below).
@
@ g9_fixed, entry 24 of the engine's second table (0x09D79EAC; the script of effect 1 calls it): the damage of
@ the moves that do a set amount. The engine picks the amount by the move's number (Super Fang, Seismic Toss...)
@ and gives a move it does not know 1; Ruination gets what it gives Super Fang, half the target's HP.
@
@ g9_speed wraps the engine's speed routine (0x09D5E3F0: battler -> its speed, 16 callers): x 3/2 when
@ Protosynthesis or Quark Drive is working and Speed is the holder's best stat.
@
@ Booster Energy (item BOOSTER). Asking is separate from using. g9_boosted, which the damage and the speed
@ routines ask, only reads: the ability works in its sun / terrain, or when the holder has used a Booster
@ Energy since it came in, or holds one now. The engine asks for speeds and damage while it thinks ahead, with
@ other Pokemon put into a battler's place for a moment: nothing may be written there. g9_booster does the
@ using, and runs only when a real move starts (g9_cancel): a holder whose ability the sun / terrain is not
@ already carrying loses the item, in gBattleMons and in the party, and keeps the boost until it leaves. A
@ holder that comes in under sun keeps its item. No message is shown.
@
@ State, 8 bytes of EWRAM at STATE: +0..3 a Booster Energy was used by this battler, +4..7 Glaive Rush's mark.
@ g9_enter clears both for the battler coming in, which is before anything reads them.
@
@ Where this is not the official rule: stat stages are not counted when picking the best stat; a Booster Energy
@ is used at the first move after its holder comes in, not on entry (its boost is there from the start);
@ Embargo and Magic Room do not stop it; attacks on a Glaive Rush user are not made sure to hit; an attacker's
@ Mold Breaker does not get past Tablets or Vessel of Ruin; Orichalcum Pulse and Hadron Engine are Drought and
@ Electric Surge to Skill Swap, Trace and Role Play, and Protosynthesis and Quark Drive can be copied by them;
@ moves that choose their category when used (Photon Geyser) go by the category in their data; and damage the
@ engine works out elsewhere (confusion, Future Sight, the AI's estimates) is untouched.

@ ---------------------------------------------------------------------------------------------- the hooks
g9_enter:                           @ r0 = ability from the species table; returns it as the engine should see it
    push {lr}
    bl g9_base
    ldr r1, l_active
    ldrb r1, [r1]
    ldr r2, l_state                 @ coming in: no Booster Energy used yet, no Glaive Rush behind it
    movs r3, #0
    strb r3, [r2, r1]
    adds r2, #4
    strb r3, [r2, r1]
    lsls r1, r1, #1
    ldr r2, l_abil16
    strh r0, [r1, r2]
    pop {pc}

g9_lookup:                          @ r0 = species, r1 = ability slot (0, 1, or 2 the hidden one)
    push {lr}
    movs r2, #3
    muls r0, r2, r0
    adds r1, r0, r1
    lsls r1, r1, #1
    ldr r3, l_table
    ldrh r0, [r3, r1]
    bl g9_base
    pop {pc}

g9_base:                            @ r0 = ability -> the ability it stands on, or itself (r1, r2 used)
    ldr r2, l_map
g9_base_next:
    ldrh r1, [r2]
    cmp r1, #0
    beq g9_base_done
    cmp r1, r0
    beq g9_base_hit
    adds r2, #4
    b g9_base_next
g9_base_hit:
    ldrh r0, [r2, #2]
g9_base_done:
    bx lr

g9_damage:
    push {r4, r5, r6, r7, lr}
    ldr r3, l_orig
    bl g9_call3
    ldr r0, l_damage
    ldr r4, [r0]                    @ r4 = the damage the engine worked out
    cmp r4, #1
    bgt g9_scaled
    b g9_out
g9_scaled:
    ldr r0, l_attacker
    ldrb r5, [r0]                   @ r5 = attacker
    ldrb r6, [r0, #1]               @ r6 = target
    ldr r0, l_move
    ldrh r0, [r0]
    movs r1, #12
    muls r0, r1, r0
    ldr r1, l_moves
    adds r0, r0, r1
    ldrb r7, [r0, #10]              @ r7 = 0 physical, 1 special
    cmp r7, #1
    bls g9_stats
    b g9_out

    @ ---- which stats this move uses (0 Attack, 1 Defense, 2 Sp. Atk, 3 Sp. Def):
    @      [sp] the attacking stat, [sp, #4] the stat the hit is taken on, [sp, #8] whose attacking stat it is
g9_stats:
    sub sp, #12
    lsls r0, r7, #1
    str r0, [sp]
    adds r0, #1
    str r0, [sp, #4]
    str r5, [sp, #8]
    ldr r0, l_move
    ldrh r0, [r0]
    ldr r1, l_body_press
    cmp r0, r1
    bne g9_not_press
    movs r1, #1                     @ Body Press: the user's Defense
    str r1, [sp]
    b g9_moves
g9_not_press:
    ldr r1, l_foul_play
    cmp r0, r1
    bne g9_not_foul
    str r6, [sp, #8]                @ Foul Play: the target's Attack
    b g9_moves
g9_not_foul:
    ldr r1, l_psyshock
    cmp r0, r1
    beq g9_on_defense
    ldr r1, l_psystrike
    cmp r0, r1
    beq g9_on_defense
    ldr r1, l_secret_sword
    cmp r0, r1
    bne g9_moves
g9_on_defense:
    movs r1, #1                     @ special moves that are taken on Defense
    str r1, [sp, #4]

    @ ---- the moves
g9_moves:
    ldr r0, l_move
    ldrh r0, [r0]
    ldr r1, l_hydro_steam
    cmp r0, r1
    bne g9_not_steam
    bl g9_sun
    cmp r0, #0
    beq g9_rushed
    adds r0, r5, #0                 @ not for a user under a Utility Umbrella
    bl g9_umbrella
    cmp r0, #0
    bne g9_rushed
    ldr r3, l_move_type             @ the engine has halved it when it is a Water move (it can be made another
    bl g9_call3                     @ type) and the target holds no Utility Umbrella
    cmp r0, #11
    bne g9_steam_half
    adds r0, r6, #0
    bl g9_umbrella
    cmp r0, #0
    bne g9_steam_half
    movs r0, #3
    movs r1, #1
    bl g9_scale
    b g9_rushed
g9_steam_half:
    movs r0, #3
    movs r1, #2
    bl g9_scale
    b g9_rushed
g9_not_steam:
    ldr r1, l_psyblade
    cmp r0, r1
    bne g9_not_psyblade
    bl g9_electric
    cmp r0, #0
    beq g9_rushed
    movs r0, #3
    movs r1, #2
    bl g9_scale
    b g9_rushed
g9_not_psyblade:
    ldr r2, l_result
    ldrb r2, [r2]                   @ gMoveResultFlags, as the engine's calculation leaves them
    ldr r1, l_collision
    cmp r0, r1
    beq g9_course
    ldr r1, l_drift
    cmp r0, r1
    beq g9_course
    ldr r1, l_glaive
    cmp r0, r1
    bne g9_rushed
    movs r1, #0x29                  @ Glaive Rush: missed, does not affect the target, failed -> no mark
    tst r2, r1
    bne g9_rushed
    ldr r0, l_state
    adds r0, #4
    movs r1, #1
    strb r1, [r0, r5]
    b g9_rushed
g9_course:
    movs r1, #2                     @ super effective
    tst r2, r1
    beq g9_rushed
    movs r0, #4
    movs r1, #3
    bl g9_scale

    @ ---- the target used Glaive Rush and has not started on a move since
g9_rushed:
    ldr r0, l_state
    adds r0, #4
    ldrb r0, [r0, r6]
    cmp r0, #0
    beq g9_pulse
    movs r0, #2
    movs r1, #1
    bl g9_scale

    @ ---- Orichalcum Pulse, Hadron Engine: the user's own Attack / Sp. Atk
g9_pulse:
    ldr r0, [sp, #8]
    cmp r0, r5
    bne g9_ruin
    adds r0, r5, #0
    bl g9_mon
    ldrh r1, [r0]
    ldr r2, l_koraidon
    cmp r1, r2
    bne g9_not_koraidon
    ldr r0, [sp]
    cmp r0, #0
    bne g9_ruin
    adds r0, r5, #0
    bl g9_abil
    cmp r0, #DROUGHT
    bne g9_ruin
    bl g9_sun
    cmp r0, #0
    beq g9_ruin
    movs r0, #4
    movs r1, #3
    bl g9_scale
    b g9_ruin
g9_not_koraidon:
    ldr r2, l_miraidon
    cmp r1, r2
    bne g9_ruin
    ldr r0, [sp]
    cmp r0, #2
    bne g9_ruin
    adds r0, r5, #0
    bl g9_abil
    cmp r0, #ELECTRIC_SURGE
    bne g9_ruin
    bl g9_electric
    cmp r0, #0
    beq g9_ruin
    movs r0, #4
    movs r1, #3
    bl g9_scale

    @ ---- the four Ruin abilities
g9_ruin:
    ldr r0, [sp, #4]                @ the stat the hit is taken on, lowered: more damage
    adds r0, #2
    lsls r0, r0, #8
    adds r1, r6, #0
    bl g9_others_have
    cmp r0, #0
    beq g9_ruin_attack
    movs r0, #4
    movs r1, #3
    bl g9_scale
g9_ruin_attack:
    ldr r0, [sp]                    @ the attacking stat, lowered: less damage
    adds r0, #2
    lsls r0, r0, #8
    ldr r1, [sp, #8]
    bl g9_others_have
    cmp r0, #0
    beq g9_best_stat
    movs r0, #3
    movs r1, #4
    bl g9_scale

    @ ---- Protosynthesis, Quark Drive
g9_best_stat:
    ldr r0, [sp, #8]
    bl g9_boosted
    ldr r1, [sp]
    cmp r0, r1
    bne g9_defender
    movs r0, #13
    movs r1, #10
    bl g9_scale
g9_defender:
    adds r0, r6, #0
    bl g9_boosted
    ldr r1, [sp, #4]
    cmp r0, r1
    bne g9_store
    movs r0, #10
    movs r1, #13
    bl g9_scale
g9_store:
    ldr r0, l_damage
    str r4, [r0]
    add sp, #12
g9_out:
    pop {r4, r5, r6, r7, pc}

g9_cancel:
    push {r4, lr}
    ldr r0, l_attacker
    ldrb r0, [r0]
    cmp r0, #3
    bhi g9_cancel_boosters
    ldr r1, l_state
    adds r1, #4
    movs r2, #0
    strb r2, [r1, r0]
g9_cancel_boosters:                 @ a real move is starting: any Booster Energy that should be used by now
    movs r4, #0
g9_cancel_next:
    ldr r0, l_count
    ldrb r0, [r0]
    cmp r4, r0
    bhs g9_cancel_on
    adds r0, r4, #0
    bl g9_booster
    adds r4, #1
    b g9_cancel_next
g9_cancel_on:
    ldr r3, l_orig_cancel
    bl g9_call3
    pop {r4, pc}

g9_fixed:
    push {lr}
    ldr r3, l_orig_fixed
    bl g9_call3
    ldr r0, l_move
    ldrh r0, [r0]
    ldr r1, l_ruination
    cmp r0, r1
    bne g9_fixed_out
    ldr r0, l_attacker
    ldrb r0, [r0, #1]
    adds r2, r0, #0                 @ r2 = the target
    bl g9_mon
    ldrh r0, [r0, #0x28]            @ its HP
    movs r1, #0x30
    muls r2, r1, r2
    ldr r1, l_field
    ldr r1, [r1]
    adds r1, r1, r2
    adds r1, #0x28
    ldrb r1, [r1, #3]               @ the engine's own rule for Super Fang: a quarter when these two bits of
    lsls r1, r1, #29                @ the target's entry in its battle struct are set, else half
    lsrs r1, r1, #30
    beq g9_fixed_half
    lsrs r0, r0, #1
g9_fixed_half:
    lsrs r0, r0, #1
    bne g9_fixed_store
    movs r0, #1
g9_fixed_store:
    ldr r1, l_damage
    str r0, [r1]
g9_fixed_out:
    pop {pc}

g9_speed:                           @ r0 = battler (r1, r2 are the routine's own): its speed
    push {r4, r5, lr}
    adds r4, r0, #0
    bl g9_speed_engine
    adds r5, r0, #0
    adds r0, r4, #0
    bl g9_boosted
    cmp r0, #4
    bne g9_speed_done
    lsrs r0, r5, #1
    adds r5, r5, r0
    lsls r5, r5, #16
    lsrs r5, r5, #16
g9_speed_done:
    adds r0, r5, #0
    pop {r4, r5, pc}

g9_speed_engine:                    @ the routine's first four instructions, which the jump to g9_speed replaced,
    movs r3, #0x58                  @ then on into it (r2 is free once it is stored: the next one writes it)
    push {r4, r5, r6, r7, lr}
    sub sp, #0x14
    str r2, [sp]
    ldr r2, l_speed_resume
    bx r2
    PAD1
l_active:           .word 0x02024064            @ gActiveBattler
l_state:            .word STATE
l_abil16:           .word 0x0203F000            @ the engine's 16-bit ability of each battler
l_table:            .word 0x097A0000            @ three abilities a species
l_map:              .word MAP_ADDR
l_orig:             .word ORIG_DAMAGE           @ the engine's damage command
l_damage:           .word 0x020241F0            @ gBattleMoveDamage
l_attacker:         .word 0x0202420B            @ gBattlerAttacker, gBattlerTarget
l_move:             .word 0x020241EA            @ gCurrentMove
l_moves:            .word 0x09D86419            @ move data, 12 bytes; +10 physical / special / status
l_koraidon:         .word KORAIDON
l_miraidon:         .word MIRAIDON
l_hydro_steam:      .word HYDRO_STEAM
l_psyblade:         .word PSYBLADE
l_result:           .word 0x0202427C            @ gMoveResultFlags
l_collision:        .word COLLISION_COURSE
l_drift:            .word ELECTRO_DRIFT
l_glaive:           .word GLAIVE_RUSH
l_body_press:       .word BODY_PRESS
l_foul_play:        .word FOUL_PLAY
l_psyshock:         .word PSYSHOCK
l_psystrike:        .word PSYSTRIKE
l_secret_sword:     .word SECRET_SWORD
l_move_type:        .word MOVE_TYPE             @ the engine: the type the move in use has right now
l_count:            .word 0x0202406C            @ gBattlersCount
l_orig_cancel:      .word ORIG_CANCEL           @ the engine's command 0
l_orig_fixed:       .word ORIG_FIXED            @ the engine's fixed-damage routine
l_ruination:        .word RUINATION
l_field:            .word 0x02024218            @ -> the engine's battle struct
l_speed_resume:     .word SPEED_RESUME          @ the speed routine, past its first four instructions

@ --------------------------------------------------------------------------------------------- the helpers
g9_scale:                           @ r4 = r4 * r0 / r1, at least 1
    push {lr}
    muls r0, r4, r0
    ldr r3, m_udiv
    bl g9_call3
    adds r4, r0, #0
    bne g9_scale_done
    movs r4, #1
g9_scale_done:
    pop {pc}

g9_abil:                            @ r0 = battler -> its ability, or 0 while the engine holds it suppressed
    push {r4, lr}
    adds r4, r0, #0
    movs r1, #0
    ldr r3, m_in_effect
    bl g9_call3
    cmp r0, #0
    beq g9_abil_done
    lsls r0, r4, #1
    ldr r1, m_abil16
    ldrh r0, [r1, r0]
g9_abil_done:
    pop {r4, pc}

g9_mon:                             @ r0 = battler -> its gBattleMons entry (r1 used)
    movs r1, #0x58
    muls r0, r1, r0
    ldr r1, m_mons
    adds r0, r0, r1
    bx lr

g9_party:                           @ r0 = battler -> its Pokemon in its side's party
    ldr r1, m_positions
    ldrb r1, [r1, r0]
    lsls r0, r0, #1
    ldr r2, m_party_index
    ldrh r0, [r2, r0]
    movs r2, #100
    muls r0, r2, r0
    ldr r2, m_player_party
    lsls r1, r1, #31                @ bit 0 of the position: the opponent's side
    beq g9_party_found
    ldr r2, m_enemy_party
g9_party_found:
    adds r0, r0, r2
    bx lr

g9_umbrella:                        @ r0 = battler -> 1 when its held item works as a Utility Umbrella
    push {lr}
    movs r1, #1
    ldr r3, m_hold_effect
    bl g9_call3
    cmp r0, #UMBRELLA
    beq g9_umbrella_yes
    movs r0, #0
    pop {pc}
g9_umbrella_yes:
    movs r0, #1
    pop {pc}

g9_sun:                             @ non-zero in harsh sunlight that no Cloud Nine or Air Lock cancels
    push {lr}
    ldr r0, m_weather
    ldrh r0, [r0]
    ldr r1, m_sun_bits
    ands r0, r1
    beq g9_sun_done
    ldr r3, m_weather_on
    bl g9_call3
g9_sun_done:
    pop {pc}

g9_electric:                        @ non-zero on Electric Terrain
    ldr r0, m_field
    ldr r0, [r0]
    adds r0, #0xD4
    ldr r0, [r0]
    ldr r1, m_electric_bits
    ands r0, r1
    bx lr

g9_others_have:                     @ r0 = ability, r1 = battler: 1 when r1 does not have it and another battler
    push {r4, r5, r6, lr}           @ on the field does
    adds r4, r0, #0
    adds r5, r1, #0
    adds r0, r5, #0
    bl g9_abil
    cmp r0, r4
    beq g9_others_no
    movs r6, #0
g9_others_loop:
    ldr r0, m_count
    ldrb r0, [r0]
    cmp r6, r0
    bhs g9_others_no
    cmp r6, r5
    beq g9_others_next
    ldr r0, m_absent
    ldrb r0, [r0]
    lsrs r0, r6
    movs r1, #1
    tst r0, r1
    bne g9_others_next
    adds r0, r6, #0
    bl g9_mon
    ldrh r0, [r0, #0x28]
    cmp r0, #0
    beq g9_others_next
    adds r0, r6, #0
    bl g9_abil
    cmp r0, r4
    beq g9_others_yes
g9_others_next:
    adds r6, #1
    b g9_others_loop
g9_others_yes:
    movs r0, #1
    pop {r4, r5, r6, pc}
g9_others_no:
    movs r0, #0
    pop {r4, r5, r6, pc}

g9_weathered:                       @ r0 = battler -> 1 when its Protosynthesis has its sun or its Quark Drive
    push {lr}                       @ its terrain, 0 when it has one of the two without, 0xFF when neither
    bl g9_abil
    ldr r1, m_proto
    cmp r0, r1
    bne g9_weathered_quark
    bl g9_sun
    b g9_weathered_on
g9_weathered_quark:
    ldr r1, m_quark
    cmp r0, r1
    bne g9_weathered_none
    bl g9_electric
g9_weathered_on:
    cmp r0, #0
    beq g9_weathered_done
    movs r0, #1
g9_weathered_done:
    pop {pc}
g9_weathered_none:
    movs r0, #0xFF
    pop {pc}

g9_boosted:                         @ r0 = battler -> its best stat (0 Attack, 1 Defense, 2 Sp. Atk, 3 Sp. Def,
    push {r4, r5, lr}               @ 4 Speed) when Protosynthesis or Quark Drive is working for it, else 0xFF.
    adds r4, r0, #0                 @ Reads only: the engine asks while it thinks ahead.
    bl g9_weathered
    cmp r0, #1
    beq g9_boosted_best
    cmp r0, #0
    bne g9_boosted_none
    ldr r5, m_state                 @ no sun / terrain: a Booster Energy it has used since it came in,
    ldrb r0, [r5, r4]
    cmp r0, #0
    bne g9_boosted_best
    adds r0, r4, #0                 @ or one it holds (g9_booster uses it up when the next move starts)
    bl g9_mon
    ldrh r1, [r0, #0x2E]
    ldr r2, m_booster
    cmp r1, r2
    bne g9_boosted_none
g9_boosted_best:
    adds r0, r4, #0
    bl g9_mon
    ldrh r1, [r0, #2]               @ Attack
    movs r2, #0
    ldrh r3, [r0, #4]               @ Defense
    cmp r3, r1
    bls g9_boosted_spa
    adds r1, r3, #0
    movs r2, #1
g9_boosted_spa:
    ldrh r3, [r0, #8]               @ Sp. Atk
    cmp r3, r1
    bls g9_boosted_spd
    adds r1, r3, #0
    movs r2, #2
g9_boosted_spd:
    ldrh r3, [r0, #10]              @ Sp. Def
    cmp r3, r1
    bls g9_boosted_spe
    adds r1, r3, #0
    movs r2, #3
g9_boosted_spe:
    ldrh r3, [r0, #6]               @ Speed
    cmp r3, r1
    bls g9_boosted_done
    movs r2, #4
g9_boosted_done:
    adds r0, r2, #0
    pop {r4, r5, pc}
g9_boosted_none:
    movs r0, #0xFF
    pop {r4, r5, pc}

g9_booster:                         @ r0 = battler: its Booster Energy is used up when that is what its
    push {r4, r5, lr}               @ Protosynthesis / Quark Drive is working on. Called when a real move
    adds r4, r0, #0                 @ starts, never from a question the engine asks.
    bl g9_mon
    adds r5, r0, #0
    ldrh r1, [r5, #0x28]            @ fainted
    cmp r1, #0
    beq g9_booster_done
    ldrh r1, [r5, #0x2E]
    ldr r2, m_booster
    cmp r1, r2
    bne g9_booster_done
    ldr r1, m_state
    ldrb r1, [r1, r4]
    cmp r1, #0
    bne g9_booster_done             @ it has used one already: this is another, kept
    adds r0, r4, #0
    bl g9_weathered
    cmp r0, #0
    bne g9_booster_done             @ the sun / terrain carries it, or it has neither ability: kept
    movs r1, #0
    strh r1, [r5, #0x2E]            @ used up: in battle
    ldr r1, m_state
    movs r2, #1
    strb r2, [r1, r4]
    adds r0, r4, #0
    bl g9_party
    movs r1, #0
    strh r1, [r0, #0x22]            @ and in the party
g9_booster_done:
    pop {r4, r5, pc}

g9_call3:
    bx r3
    PAD2
m_udiv:             .word 0x082E7B69            @ __udivsi3
m_in_effect:        .word IN_EFFECT             @ the engine: battler, 0 -> 0 while its ability is suppressed
m_hold_effect:      .word HOLD_EFFECT           @ the engine: battler, 1 -> the hold effect its item has now
m_abil16:           .word 0x0203F000
m_mons:             .word 0x02024084            @ gBattleMons, 0x58 bytes; +0 species, +0x28 HP, +0x2E item
m_positions:        .word 0x02024076            @ gBattlerPositions
m_party_index:      .word 0x0202406E            @ gBattlerPartyIndexes
m_player_party:     .word 0x020244EC            @ gPlayerParty, 100 bytes a Pokemon; +0x22 item
m_enemy_party:      .word 0x02024744            @ gEnemyParty
m_weather:          .word 0x020243CC            @ gBattleWeather
m_sun_bits:         .word 0x00000860            @ sun: temporary, permanent, Desolate Land
m_weather_on:       .word 0x09D45B85            @ 1 unless Cloud Nine or Air Lock is on the field
m_field:            .word 0x02024218            @ -> the engine's battle struct; +0xD4 field effects
m_electric_bits:    .word 0x0001E000            @ Electric Terrain's turn counter
m_count:            .word 0x0202406C            @ gBattlersCount
m_absent:           .word 0x02024210            @ gAbsentBattlerFlags
m_proto:            .word PROTO
m_quark:            .word QUARK
m_state:            .word STATE
m_booster:          .word BOOSTER
