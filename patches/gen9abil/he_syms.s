@ The routines gen9abil calls in Hyper Emerald: the game's own, then the battle engine's (0x09D00000..). Marked as
@ Thumb code, so that the linker calls them with bl (or a Thumb-to-Thumb long branch for the game's far ones).
    .syntax unified
    .thumb
    .global GetBattlerSide
    .thumb_set GetBattlerSide, 0x080A6A30
    .global check_field_for_ability
    .thumb_set check_field_for_ability, 0x09D459B4
    .global has_ability_effect_inalternate
    .thumb_set has_ability_effect_inalternate, 0x09D45A0C
    .global has_ability_effect
    .thumb_set has_ability_effect, 0x09D45AEC
    .global weather_abilities_effect
    .thumb_set weather_abilities_effect, 0x09D45B84
    .global mimicry_change
    .thumb_set mimicry_change, 0x09D458E8
    .global ability_battle_effects
    .thumb_set ability_battle_effects, 0x09D45F8C
    .global can_change_stat
    .thumb_set can_change_stat, 0x09D4524C
    .global get_battle_rng
    .thumb_set get_battle_rng, 0x09D4539C
    .global check_ability
    .thumb_set check_ability, 0x09D497E8
    .global bs_push
    .thumb_set bs_push, 0x09D4B048
    .global bs_push_current
    .thumb_set bs_push_current, 0x09D4B06C
    .global bs_execute
    .thumb_set bs_execute, 0x09D4B0A4
    .global get_attacking_move_type
    .thumb_set get_attacking_move_type, 0x09D4B164
    .global percent_chance
    .thumb_set percent_chance, 0x09D4B2B0
    .global is_bank_present
    .thumb_set is_bank_present, 0x09D5B0D4
    .global apply_modifier
    .thumb_set apply_modifier, 0x09D5E2E2
    .global apply_statboost
    .thumb_set apply_statboost, 0x09D5E32C
    .global get_speed
    .thumb_set get_speed, 0x09D5E3F0
    .global find_move_in_table
    .thumb_set find_move_in_table, 0x09D5F070
    .global does_move_make_contact
    .thumb_set does_move_make_contact, 0x09D5F094
    .global apply_base_power_modifiers
    .thumb_set apply_base_power_modifiers, 0x09D5F0CC
    .global get_attack_stat
    .thumb_set get_attack_stat, 0x09D5F8A0
    .global get_def_stat
    .thumb_set get_def_stat, 0x09D5FCA8
    .global damage_calc
    .thumb_set damage_calc, 0x09D5FF3C
    .global photon_geyser_special
    .thumb_set photon_geyser_special, 0x09D6199C
    .global reset_terrains
    .thumb_set reset_terrains, 0x09D67CF4
    .global terrains_get_turns
    .thumb_set terrains_get_turns, 0x09D67D1C
    .global get_item_effect
    .thumb_set get_item_effect, 0x09D68700
    .global RecordAbilityBattle
    .thumb_set RecordAbilityBattle, 0x09D73AB0
    .global affected_by_substitute
    .thumb_set affected_by_substitute, 0x09D6A330
    .global findability_in_table
    .thumb_set findability_in_table, 0x09D66EE0
    .global check_weather_trio
    .thumb_set check_weather_trio, 0x09D6224C
    .global cant_poison
    .thumb_set cant_poison, 0x09D4B950
    .global cant_become_burned
    .thumb_set cant_become_burned, 0x09D4BC04
    .global cant_fall_asleep
    .thumb_set cant_fall_asleep, 0x09D4BA44
    .global cant_become_paralyzed
    .thumb_set cant_become_paralyzed, 0x09D4BB54
    .global cant_become_freezed
    .thumb_set cant_become_freezed, 0x09D4BCB8
    .global cant_become_confused
    .thumb_set cant_become_confused, 0x09D5A300
    .global moveeffect_set_status
    .thumb_set moveeffect_set_status, 0x09D58438
    .global atk84_jumpifcannotsleep
    .thumb_set atk84_jumpifcannotsleep, 0x09D54074
    .global is_of_type
    .thumb_set is_of_type, 0x09D4B1C4
    .global check_ability_with_mold
    .thumb_set check_ability_with_mold, 0x09D61934
    .global get_first_to_strike
    .thumb_set get_first_to_strike, 0x09D499F4
    .global atkB2_set_perishsong
    .thumb_set atkB2_set_perishsong, 0x0805385C
    .global get_battle_bank
    .thumb_set get_battle_bank, 0x09D4AFD8
    .global atk6A_remove_item
    .thumb_set atk6A_remove_item, 0x09D57E9C
    .global change_stats
    .thumb_set change_stats, 0x09D6C698
    .global type_effectiveness_calc
    .thumb_set type_effectiveness_calc, 0x09D4B6D4
    .global atk07_final_dmg_calc
    .thumb_set atk07_final_dmg_calc, 0x09D6A3F8
    .global can_switch
    .thumb_set can_switch, 0x09D4F308
    .global atk8F_forcerandomswitch
    .thumb_set atk8F_forcerandomswitch, 0x0805112C
