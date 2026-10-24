/* gen9abil: the numbers. Each wrapper runs the engine's own routine, then applies what the Gen 9 abilities change
 * as a modifier of its result (a 4.12 fixed-point factor, chained the way the engine chains its own). These
 * routines are also asked while the engine thinks ahead (the AI, turn order): nothing here writes. */
#include "g9.h"

#define MOVE_PSYSHOCK 473
#define MOVE_PSYSTRIKE 540
#define MOVE_SECRET_SWORD 548
#define MOVE_NIGHT_SHADE 101
#define TYPE_ROCK 5
#define TYPE_GHOST 7

static u16 chain(u16 mod, u16 by)
{
    return (mod * by + 0x800) >> 12;
}

static u8 fainted_allies(u8 bank)
{
    return gBattleResults[GetBattlerSide(bank) ? 1 : 0];
}

/* the attacking stat */
u16 w_get_attack_stat(u16 move, u8 move_type, u8 atk, u8 def)
{
    u16 stat = get_attack_stat(move, move_type, atk, def);
    u8 split = g9_split(move);
    u16 mod = 0x1000;

    if (has_ability_effect(atk, 0)) {
        switch (gBankAbilities[atk]) {
        case ABILITY_PROTOSYNTHESIS:
        case ABILITY_QUARK_DRIVE:
            if (G9->paradox[atk]) {
                u8 best = g9_highest_stat(atk);
                if ((split == 1 && best == STAT_SPATK) || (split == 0 && best == STAT_ATK))
                    mod = chain(mod, 0x14CD);
            }
            break;
        case ABILITY_SUPREME_OVERLORD: {
            u8 n = fainted_allies(atk);
            mod = chain(mod, n < 6 ? 0x1000 + 0x19A * n : 0x1800);
            break;
        }
        }
    }
    /* the Ruin abilities lower everyone's but their own holder's */
    if ((split == 1 && g9_field_has(ABILITY_VESSEL_OF_RUIN) && !check_ability(atk, ABILITY_VESSEL_OF_RUIN)) ||
        (split == 0 && g9_field_has(ABILITY_TABLETS_OF_RUIN) && !check_ability(atk, ABILITY_TABLETS_OF_RUIN)))
        mod = chain(mod, 0xC00);
    if (mod != 0x1000)
        stat = apply_modifier(mod, stat);
    return stat;
}

/* the stat the hit is taken on */
u16 w_get_def_stat(u16 move, u8 atk, u8 def)
{
    u16 stat = get_def_stat(move, atk, def);
    u8 split = g9_split(move);
    u8 chosen = (split == 0 || move == MOVE_PSYSTRIKE || move == MOVE_PSYSHOCK || move == MOVE_SECRET_SWORD) ? 0 : 1;
    if (nbs_get(0xD4, 3, 3))                        /* Wonder Room */
        chosen ^= 1;
    u16 mod = 0x1000;

    if ((split == 1 && g9_field_has(ABILITY_BEADS_OF_RUIN) && !check_ability(def, ABILITY_BEADS_OF_RUIN)) ||
        (split == 0 && g9_field_has(ABILITY_SWORD_OF_RUIN) && !check_ability(def, ABILITY_SWORD_OF_RUIN)))
        mod = chain(mod, 0xC00);
    if ((g9_has_mold(def, atk, ABILITY_PROTOSYNTHESIS) || g9_has_mold(def, atk, ABILITY_QUARK_DRIVE)) &&
        G9->paradox[def]) {
        u8 best = g9_highest_stat(def);
        if ((best == STAT_DEF && chosen == 0) || (best == STAT_SPDEF && chosen == 1))
            mod = chain(mod, 0x14CD);
    }
    if (mod != 0x1000)
        stat = apply_modifier(mod, stat);
    return stat;
}

/* the move's power */
u16 w_apply_base_power_modifiers(u16 move, u8 move_type, u8 atk, u8 def, u16 power, u8 setflag)
{
    power = apply_base_power_modifiers(move, move_type, atk, def, power, setflag);
    u16 mod = 0x1000;
    if (has_ability_effect(atk, 0)) {
        switch (gBankAbilities[atk]) {
        case ABILITY_ROCKY_PAYLOAD:
            if (move_type == TYPE_ROCK)
                mod = chain(mod, 0x1800);
            break;
        case ABILITY_ORICHALCUM_PULSE:              /* with a Utility Umbrella too */
            if (weather_abilities_effect() && SUN_WEATHER)
                mod = chain(mod, 0x14CD);
            break;
        case ABILITY_HADRON_ENGINE:
            if (NB_ELECTRIC_TERRAIN())
                mod = chain(mod, 0x14CD);
            break;
        }
    }
    if (mod != 0x1000)
        power = apply_modifier(mod, power);
    return power;
}

/* the damage, once worked out: Purifying Salt halves Ghost-type hits */
void w_damage_calc(u16 move, u8 move_type, u8 atk, u8 def, u16 chained_effect, u8 setflag)
{
    damage_calc(move, move_type, atk, def, chained_effect, setflag);
    if (gBattleMoveDamage > 0 && move_type == TYPE_GHOST && move != MOVE_NIGHT_SHADE &&
        g9_has_mold(def, atk, ABILITY_PURIFYING_SALT)) {
        s32 d = apply_modifier(0x800, gBattleMoveDamage);
        gBattleMoveDamage = d ? d : 1;
    }
}

/* speed: Protosynthesis and Quark Drive when Speed is the best stat */
u16 w_get_speed(u8 bank, s8 stat_buffs, u8 check_side)
{
    u16 speed = get_speed(bank, stat_buffs, check_side);
    if (g9_paradox_on(bank) && g9_highest_stat(bank) == STAT_SPEED)
        speed = speed * 3 / 2;
    return speed;
}
