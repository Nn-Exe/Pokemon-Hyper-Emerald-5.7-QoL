/* gen9abil: the abilities that act when a move is about to hit (switch_id 3), when it has hit (4: the target's,
 * 10: the attacker's), and the status conditions some of them keep away (the engine's cant_... routines). */
#include "g9.h"

#define TYPE_FIRE 10
#define TYPE_GROUND 4
#define MOVE_GRASSY_TERRAIN 580
#define STATUS3_CHARGED_UP 0x200
#define MOVEEFFECT_TOXIC 0x80

u8 affected_by_substitute(u8 bank);
u8 w_findability_in_table(u16 ability, const u16 *table);
void check_weather_trio(void);
u8 cant_poison(u8 atk, u8 def, u8 self_inflicted);
u8 cant_become_burned(u8 bank, u8 self_inflicted);
u8 cant_fall_asleep(u8 bank, u8 self_inflicted);
u8 cant_become_paralyzed(u8 bank, u8 self_inflicted);
u8 cant_become_freezed(u8 bank, u8 self_inflicted);
u8 cant_become_confused(u8 bank, u8 atk);
void moveeffect_set_status(u8 bank, u32 flag, u8 string_id);
void atk84_jumpifcannotsleep(void);
extern u8 gBattleChosenBg;
extern const u16 gMummyForbidden[];             /* the abilities Mummy cannot replace (the engine's list) */
extern const u8 BS_MOVE_HP_DRAIN[], BS_MOVE_USELESS[], BS_IMMUNE_STAT_RAISE[], BS_IMMUNE[];
extern const u8 BS_DEF_ABILITY_CHANGES_DEF_STAT[], BS_MUMMY[], BS_GRASSY_SURGE[], BS_ATK_ABILITY_STATUS[];
extern const u8 BS_MOVE_EFFECT_CONFUSION[];

static const u16 wind_moves[] = {16, 18, 59, 177, 196, 239, 257, 314, 542, 572, 584, 910, 924, 925, 926, 948, 0xFFFF};

u8 g9_wind_move(u16 move)
{
    return find_move_in_table(move, wind_moves);
}

static u8 target_lost_hp(void)                  /* the engine's own test: the target took damage this turn */
{
    return *(u32 *)(gSpecialStatuses[gBattlerTarget] + 4) != 0;
}

static u8 move_worked(void)
{
    return !(gMoveResultFlags & 0x29);            /* missed, not affected, failed */
}

static u8 hp_half_drop(u8 bank)
{
    u16 max = gBattleMons[bank].maxHP;
    u16 before = *(u16 *)(gNewBattleStruct + 0x30 * bank + 0x10);
    return gBattleMons[bank].hp <= max / 2 && before > max / 2;
}

/* switch_id 3: the move is about to hit bank; an ability that takes it in instead */
u8 g9_absorb(u8 bank, u16 move)
{
    if (!move || bank == gBattlerAttacker || !has_ability_effect(bank, 1))
        return FALSE;
    u8 adder = (gProtectStructs[gBattlerAttacker][2] >> 3) & 1;
    u8 type = get_attacking_move_type();
    u8 changer = 0;
    switch (gLastUsedAbility) {
    case ABILITY_GOOD_AS_GOLD:
        return g9_good_as_gold(bank, move);
    case ABILITY_EARTH_EATER:                   /* as Water Absorb: a quarter of its HP back */
        if (type != TYPE_GROUND)
            return FALSE;
        if ((gBattleMons[bank].hp && gBattleMons[bank].hp == gBattleMons[bank].maxHP) || NB_HEAL_BLOCK(bank)) {
            gBattlescriptCurrInstr = (u8 *)BS_MOVE_USELESS + adder;
        } else {
            s32 heal = gBattleMons[bank].maxHP >> 2;
            gBattleMoveDamage = -(heal ? heal : 1);
            gBattlescriptCurrInstr = (u8 *)BS_MOVE_HP_DRAIN + adder;
        }
        return TRUE;
    case ABILITY_WELL_BAKED_BODY:               /* Fire moves: Defense +2 */
        if (type == TYPE_FIRE)
            changer = 0x20 + STAT_DEF;
        break;
    case ABILITY_WIND_RIDER:                    /* wind moves: Attack +1 */
        if (g9_wind_move(move))
            changer = 0x10 + STAT_ATK;
        break;
    }
    if (!changer)
        return FALSE;
    gBattlescriptCurrInstr = (u8 *)(can_change_stat(bank, 1, changer) ? BS_IMMUNE_STAT_RAISE : BS_IMMUNE) + adder;
    return TRUE;
}

/* switch_id 4: the move has hit bank (the target); its own ability answers */
u8 g9_on_hit(u8 bank, u16 move)
{
    if (!has_ability_effect(bank, 0) || !move_worked())
        return FALSE;
    if (gProtectStructs[bank][1] & 1)           /* it hit itself in confusion: no ability answers */
        return FALSE;
    u8 lost = target_lost_hp();
    u16 hp = gBattleMons[bank].hp;
    u8 sub = affected_by_substitute(bank);
    u8 damaging = MOVE_SPLIT(move) != 2;
    u8 type = get_attacking_move_type();
    u8 atk = gBattlerAttacker;
    u8 atk_there = is_bank_present(atk);

    switch (gLastUsedAbility) {
    case ABILITY_LINGERING_AROMA:               /* as Mummy, with its own name */
        if (atk_there && lost && !sub && does_move_make_contact(move, atk) &&
            gBankAbilities[atk] != ABILITY_LINGERING_AROMA &&
            !w_findability_in_table(gBankAbilities[atk], gMummyForbidden)) {
            gBankAbilities[atk] = ABILITY_LINGERING_AROMA;
            nbs_set(0xE8, 0, 2, atk);
            check_weather_trio();
            bs_push_current(BS_MUMMY);
            return TRUE;
        }
        break;
    case ABILITY_THERMAL_EXCHANGE:              /* hit by a Fire move: Attack +1 */
        if (hp && gBattleMons[bank].statStages[STAT_ATK] != 12 && type == TYPE_FIRE && lost && damaging && !sub) {
            STAT_CHANGER = 0x10 + STAT_ATK;
            bs_push_current(BS_DEF_ABILITY_CHANGES_DEF_STAT);
            return TRUE;
        }
        break;
    case ABILITY_SEED_SOWER:                    /* hit: Grassy Terrain */
        if (!NB_GRASSY_TERRAIN() && lost && damaging && !sub) {
            reset_terrains(gNewBattleStruct + 0xD4);
            u8 turns = terrains_get_turns(bank);
            nbs_set(0xD5, 1, 4, turns);
            nbs_set(0xDA, 0, 4, 5);
            if (turns > 5 && GetBattlerSide(bank) == 0)
                nbs_set(0xDA, 0, 4, turns);
            if (gBattleChosenBg != 0x1C)
                gBattleChosenBg = 0x19;
            NB_VAR1 = MOVE_GRASSY_TERRAIN;
            SCR_ACTIVE = bank;
            bs_execute(BS_GRASSY_SURGE);
            return TRUE;
        }
        break;
    case ABILITY_ANGER_SHELL: {                 /* falls below half: Atk, Sp. Atk, Speed +1, Def, Sp. Def -1 */
        s8 *st = gBattleMons[bank].statStages;
        if (hp && (st[STAT_DEF] > 0 || st[STAT_SPDEF] > 0 || st[STAT_SPEED] != 12 || st[STAT_SPATK] != 12 ||
                   st[STAT_ATK] != 12) && hp_half_drop(bank) && lost && damaging && !NB_SHEER_FORCE_BONUS() &&
            gMultiHitCounter <= 1 && !sub) {
            nbs_set(0xE8, 0, 2, bank);
            bs_push_current(BS_G9_ANGER_SHELL);
            return TRUE;
        }
        break;
    }
    case ABILITY_ELECTROMORPHOSIS:              /* hit: charged, its next Electric move doubled */
        if (hp && !(gStatuses3[bank] & STATUS3_CHARGED_UP) && lost && damaging && !sub) {
            gStatuses3[bank] |= STATUS3_CHARGED_UP;
            bs_push_current(BS_G9_CHARGE);
            return TRUE;
        }
        break;
    case ABILITY_WIND_POWER:                    /* hit by a wind move: charged */
        if (hp && !(gStatuses3[bank] & STATUS3_CHARGED_UP) && lost && g9_wind_move(gCurrentMove) && !sub) {
            gStatuses3[bank] |= STATUS3_CHARGED_UP;
            bs_push_current(BS_G9_CHARGE);
            return TRUE;
        }
        break;
    case ABILITY_TOXIC_DEBRIS: {                /* hit by a physical move: Toxic Spikes on the attacker's side */
        u8 side = GetBattlerSide(gBattlerTarget) ^ 1;
        u32 at = 0xC0 + 9 * side + 2;
        if (!nbs_get(at, 3, 1) && MOVE_SPLIT(gCurrentMove) == 0 && lost && !sub) {
            if (nbs_get(at, 2, 1))
                nbs_set(at, 3, 1, 1);           /* a second layer: badly poisons */
            else
                nbs_set(at, 2, 1, 1);
            bs_push_current(BS_G9_TOXIC_DEBRIS);
            return TRUE;
        }
        break;
    }
    }
    return FALSE;
}

/* switch_id 10: the attacker's ability, its move having hit */
u8 g9_after_hit(u8 bank, u16 move)
{
    if (!has_ability_effect(bank, 0) || !move_worked() || !gBattleMons[gBattlerAttacker].hp || !target_lost_hp())
        return FALSE;
    if (gProtectStructs[bank][1] & 1)
        return FALSE;
    if (gLastUsedAbility == ABILITY_TOXIC_CHAIN) {
        u8 def = gBattlerTarget;
        if (g9_has_mold(def, gBattlerAttacker, 0x13))    /* Shield Dust */
            return FALSE;
        if (gBattleMons[def].hp && !cant_poison(bank, def, 0) && get_battle_rng(100) < 30) {
            NB_MOVE_EFFECT = MOVEEFFECT_TOXIC;
            bs_push_current(BS_ATK_ABILITY_STATUS);
            return TRUE;
        }
    }
    return FALSE;
}

/* ------------------------------------------------------------------------- the status conditions kept away */
/* 4 is the engine's "its ability does not allow it", which comes before Safeguard (5) and the terrains */
static u8 kept_away(u8 r, u8 bank, u8 burn)
{
    if (r == 0 || r >= 5) {
        if (g9_has(bank, ABILITY_PURIFYING_SALT) || (burn && g9_has(bank, ABILITY_THERMAL_EXCHANGE)))
            return 4;
    }
    return r;
}

u8 w_cant_poison(u8 atk, u8 def, u8 self_inflicted)
{
    return kept_away(cant_poison(atk, def, self_inflicted), def, 0);
}

u8 w_cant_become_burned(u8 bank, u8 self_inflicted)
{
    return kept_away(cant_become_burned(bank, self_inflicted), bank, 1);
}

u8 w_cant_fall_asleep(u8 bank, u8 self_inflicted)
{
    return kept_away(cant_fall_asleep(bank, self_inflicted), bank, 0);
}

u8 w_cant_become_paralyzed(u8 bank, u8 self_inflicted)
{
    return kept_away(cant_become_paralyzed(bank, self_inflicted), bank, 0);
}

u8 w_cant_become_freezed(u8 bank, u8 self_inflicted)
{
    return kept_away(cant_become_freezed(bank, self_inflicted), bank, 0);
}

/* command 0x84 (Yawn and the like): Purifying Salt keeps sleep away as Insomnia does */
void w_atk84_jumpifcannotsleep(void)
{
    if (g9_has_mold(gBattlerTarget, gBattlerAttacker, ABILITY_PURIFYING_SALT)) {
        gLastUsedAbility = ABILITY_PURIFYING_SALT;
        RecordAbilityBattle(gBattlerTarget, ABILITY_PURIFYING_SALT);
        MULTISTRING = 2;
        const u8 *p = gBattlescriptCurrInstr + 1;
        gBattlescriptCurrInstr = (u8 *)(p[0] | p[1] << 8 | p[2] << 16 | p[3] << 24);
        return;
    }
    atk84_jumpifcannotsleep();
}

/* a move gives a status: Poison Puppeteer confuses whoever it poisons */
void w_moveeffect_set_status(u8 bank, u32 flag, u8 string_id)
{
    moveeffect_set_status(bank, flag, string_id);
    if (check_ability(gBattlerAttacker, ABILITY_POISON_PUPPETEER) &&
        (flag == STATUS1_POISON || flag == STATUS1_TOXIC) && !cant_become_confused(bank, gBattlerAttacker)) {
        gBattleMons[bank].status2 = (gBattleMons[bank].status2 & ~STATUS2_CONFUSION) | (2 + get_battle_rng(4));
        /* after the status's own message: the confusion script is what that one returns to */
        bs_push(BS_MOVE_EFFECT_CONFUSION, gBattlescriptCurrInstr);
    }
}
