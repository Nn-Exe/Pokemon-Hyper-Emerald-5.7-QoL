/* gen9abil: the Gen 9 abilities in Hyper Emerald's battle engine.
 *
 * The engine already asks one routine about every ability at every point of a battle: ability_battle_effects
 * (switch_id, bank, ability_to_check, special, move), switch_id saying where the battle is (0 a Pokemon comes in,
 * 1 the turn ends, 3 a move is about to hit, 4 a move has hit, 6 the weather may have changed, 24 a Pokemon's own
 * entry ability...). An ability it does not know falls through every switch and does nothing. gen9abil stands in
 * front of it (w_ability_battle_effects; the patcher points every call at it): for a Gen 9 ability it does what that
 * ability does there, else it hands over to the engine. The engine's other routines that decide a number - attack,
 * defense, base power, speed, the final damage - are wrapped the same way in calc.c.
 */
#include "g9.h"

void mimicry_change(u8 count, u8 arg);
extern u8 gBattleChosenBg;          /* 0x02022FF1 */
extern u8 gWeatherDuration;         /* 0x020243F8 */
extern u32 gBattleWeatherWord;      /* 0x020243CC: the engine writes the weather as a word */
extern u8 check_field_for_ability(u16 ability, u8 side_to_ignore, u8 mold);

/* ------------------------------------------------------------------------------------------------ helpers */
u8 g9_has(u8 bank, u16 ability)
{
    return gBankAbilities[bank] == ability && has_ability_effect(bank, 0);
}

/* the defender's ability, unless the attacker's Mold Breaker gets past it */
u8 g9_has_mold(u8 def, u8 atk, u16 ability)
{
    u8 was = gBattlerAttacker;
    gBattlerAttacker = atk;
    u8 r = gBankAbilities[def] == ability && has_ability_effect(def, 1);
    gBattlerAttacker = was;
    return r;
}

/* someone on the field has it, working: 1 + that battler */
u8 g9_field_has(u16 ability)
{
    return check_field_for_ability(ability, 3, 0);
}

/* the best of Attack, Defense, Sp. Atk, Sp. Def and Speed with its stages; a tie goes to the first */
u8 g9_highest_stat(u8 bank)
{
    static const u8 order[5] = {STAT_ATK, STAT_DEF, STAT_SPATK, STAT_SPDEF, STAT_SPEED};
    const u16 *stats = &gBattleMons[bank].species;
    u16 best = 0;
    u8 id = 0;
    for (u32 i = 0; i < 5; i++) {
        u8 s = order[i];
        u16 v = apply_statboost(stats[s], gBattleMons[bank].statStages[s]);
        if (v > best) {
            best = v;
            id = s;
        }
    }
    return id;
}

/* physical 0 / special 1, as the engine's own stat routines work it out (Photon Geyser picks one) */
u8 g9_split(u16 move)
{
    return MOVE_SPLIT(move) & photon_geyser_special(move);
}

/* ---------------------------------------------------------------------------- Protosynthesis, Quark Drive */
static u8 is_paradox(u16 a)
{
    return a == ABILITY_PROTOSYNTHESIS || a == ABILITY_QUARK_DRIVE;
}

static u8 paradox_env(u8 bank)
{
    if (gBankAbilities[bank] == ABILITY_PROTOSYNTHESIS)
        return weather_abilities_effect() && SUN_WEATHER;
    return NB_ELECTRIC_TERRAIN() != 0;
}

static u8 booster(u8 bank)
{
    return get_item_effect(bank, 1) == ITEM_EFFECT_BOOSTER_ENERGY;
}

/* the boost is on now: the damage and speed routines ask this, and it only reads */
u8 g9_paradox_on(u8 bank)
{
    return is_paradox(gBankAbilities[bank]) && has_ability_effect(bank, 0) && G9->paradox[bank];
}

static void paradox_start(u8 bank, u8 by_env)
{
    u8 proto = gBankAbilities[bank] == ABILITY_PROTOSYNTHESIS;
    MULTISTRING = g9_highest_stat(bank) - 1;
    SCR_ACTIVE = bank;
    gActiveBattler = bank;
    if (by_env) {
        G9->paradox[bank] |= PARADOX_ENV;
        bs_execute(proto ? BS_G9_PROTO_SUN : BS_G9_QUARK_TERRAIN);
    } else {
        G9->paradox[bank] |= PARADOX_ITEM;
        bs_execute(proto ? BS_G9_BOOSTER_PROTO : BS_G9_BOOSTER_QUARK);
    }
}

/* it comes in: the sun / the terrain, else its Booster Energy, turns it on */
static u8 paradox_trigger(u8 bank)
{
    gLastUsedAbility = gBankAbilities[bank];
    if (!has_ability_effect(bank, 0) || !is_paradox(gLastUsedAbility) || G9->paradox[bank])
        return FALSE;
    u8 env = paradox_env(bank);
    if (!env && !booster(bank))
        return FALSE;
    paradox_start(bank, env);
    return TRUE;
}

/* the weather or the terrain may have changed: one battler at a time, turned on or off */
static u8 paradox_poll(void)
{
    for (u32 i = 0; i < gBattlersCount; i++) {
        u8 bank = gBattlerByTurnOrder[i];
        if (!is_bank_present(bank) || !is_paradox(gBankAbilities[bank]) || !has_ability_effect(bank, 0))
            continue;
        if (G9->paradox[bank] & PARADOX_ITEM)
            continue;                               /* a Booster Energy keeps it on until it leaves */
        u8 env = paradox_env(bank);
        gLastUsedAbility = gBankAbilities[bank];
        if (G9->paradox[bank] & PARADOX_ENV) {
            if (env)
                continue;
            if (booster(bank)) {                    /* the sun has gone: the Booster Energy takes over */
                paradox_start(bank, FALSE);
            } else {
                G9->paradox[bank] &= ~PARADOX_ENV;
                SCR_ACTIVE = bank;
                bs_execute(gBankAbilities[bank] == ABILITY_PROTOSYNTHESIS ? BS_G9_END_PROTO : BS_G9_END_QUARK);
            }
            return TRUE;
        }
        if (env || booster(bank)) {
            paradox_start(bank, env);
            return TRUE;
        }
    }
    return FALSE;
}

/* ------------------------------------------------------------------------------------------- coming in */
static u8 set_sun(u8 bank)
{
    /* as the engine's own Drought: not while any sun, heavy rain or strong winds are up */
    if (gBattleWeather & 0x3860)
        return FALSE;
    gBattleWeatherWord = 0x20;
    NB_WEATHER_RECORD = 5;
    if (get_item_effect(bank, 1) == ITEM_EFFECT_HEAT_ROCK) {
        gWeatherDuration = 8;
        if (GetBattlerSide(bank) == 0)
            NB_WEATHER_RECORD = 8;
    } else {
        gWeatherDuration = 5;
    }
    return TRUE;
}

static u8 set_electric_terrain(u8 bank)
{
    /* as the engine's own Electric Surge */
    if (NB_ELECTRIC_TERRAIN())
        return FALSE;
    reset_terrains(gNewBattleStruct + 0xD4);
    u8 turns = terrains_get_turns(bank);
    nbs_set(0xD5, 5, 4, turns);
    nbs_set(0xDA, 0, 4, 5);
    if (turns > 5 && GetBattlerSide(bank) == 0)
        nbs_set(0xDA, 0, 4, turns);
    mimicry_change(gBattlersCount, 0);
    if (gBattleChosenBg != 0x1C)
        gBattleChosenBg = 0x18;
    NB_VAR1 = 604;                                  /* Electric Terrain's move, for the animation */
    return TRUE;
}

/* switch_id 24: its own entry ability */
static u8 switch_in(u8 bank)
{
    SCR_ACTIVE = bank;
    switch (gLastUsedAbility) {
    case ABILITY_TABLETS_OF_RUIN:
    case ABILITY_SWORD_OF_RUIN:
    case ABILITY_VESSEL_OF_RUIN:
    case ABILITY_BEADS_OF_RUIN:
        MULTISTRING = (gLastUsedAbility == ABILITY_TABLETS_OF_RUIN) ? 0 :
                      (gLastUsedAbility == ABILITY_SWORD_OF_RUIN) ? 1 :
                      (gLastUsedAbility == ABILITY_VESSEL_OF_RUIN) ? 2 : 3;
        bs_execute(BS_G9_RUIN);
        return TRUE;
    case ABILITY_ORICHALCUM_PULSE:
        if (set_sun(bank)) {
            bs_execute(BS_G9_ORICHALCUM);
            return TRUE;
        }
        if (SUN_WEATHER) {
            bs_execute(BS_G9_ORICHALCUM_ON);
            return TRUE;
        }
        return FALSE;
    case ABILITY_HADRON_ENGINE:
        if (set_electric_terrain(bank)) {
            bs_execute(BS_G9_HADRON);
            return TRUE;
        }
        bs_execute(BS_G9_HADRON_ON);
        return TRUE;
    case ABILITY_SUPREME_OVERLORD:
        if (gBattleResults[GetBattlerSide(bank) ? 1 : 0]) {
            gBattlerAttacker = bank;
            bs_execute(BS_G9_OVERLORD);
            return TRUE;
        }
        return FALSE;
    case ABILITY_PROTOSYNTHESIS:
    case ABILITY_QUARK_DRIVE:
        return paradox_trigger(bank);
    }
    return g9_entry_others(bank);
}

/* --------------------------------------------------------------------------- the engine's ability routine */
#define STATUS3_INNER_SWITCH_LOCK 0x800000

u8 w_ability_battle_effects(u8 switch_id, u8 bank, u16 ability_to_check, u8 special, u16 move)
{
    u16 ability = special ? special : gBankAbilities[bank];
    u8 effect;

    if (switch_id == 0 && special != 0xFF)
        g9_clear_bank(bank);                        /* a Pokemon comes in: nothing of the one before carries over */

    /* Commander, for the one coming in (Tatsugiri, or the Dondozo it goes into); its entry lock stays for its own
     * entry ability, which the game asks for next */
    if (switch_id == 24 && (gStatuses3[bank] & STATUS3_INNER_SWITCH_LOCK) && g9_commander_entry(bank))
        return TRUE;

    if (IS_GEN9_ABILITY(ability)) {
        u16 curr = (move && move <= 0x3A8) ? move : gCurrentMove;     /* as the engine picks the move */
        switch (switch_id) {
        case 3:                                     /* about to be hit */
        case 4:                                     /* hit: the target's ability */
        case 10:                                    /* hit: the attacker's ability */
            gLastUsedAbility = ability;
            effect = switch_id == 3 ? g9_absorb(bank, curr) :
                     switch_id == 4 ? g9_on_hit(bank, curr) : g9_after_hit(bank, curr);
            if (effect) {
                RecordAbilityBattle(bank, ability);
                return effect;
            }
            break;
        case 1:                                     /* the turn ends */
            if (ability == ABILITY_PROTOSYNTHESIS && gBattleMons[bank].hp && has_ability_effect(bank, 0)) {
                gLastUsedAbility = ability;
                if (paradox_trigger(bank)) {
                    RecordAbilityBattle(bank, ability);
                    return TRUE;
                }
            }
            if (ability == ABILITY_CUD_CHEW) {
                gLastUsedAbility = ability;
                if (g9_cud_chew(bank)) {
                    RecordAbilityBattle(bank, ability);
                    return TRUE;
                }
            }
            break;
        case 24:                                    /* its own entry ability, once per entry */
            gLastUsedAbility = ability;
            effect = FALSE;
            if ((gStatuses3[bank] & STATUS3_INNER_SWITCH_LOCK) && has_ability_effect(bank, 0))
                effect = switch_in(bank);
            gStatuses3[bank] &= ~STATUS3_INNER_SWITCH_LOCK;
            if (effect)
                RecordAbilityBattle(bank, ability);
            return effect;
        }
    }

    effect = ability_battle_effects(switch_id, bank, ability_to_check, special, move);

    /* after the weather checks (Castform, Cherrim) found nothing to do: the Paradox abilities, Opportunist. The
     * game asks again after each one that did something, until none does. */
    if (switch_id == 6 && !effect)
        effect = paradox_poll();
    if (switch_id == 6 && !effect)
        effect = g9_after_action();
    return effect;
}
