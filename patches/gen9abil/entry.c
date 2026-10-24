/* gen9abil: the entry abilities that act on the others (Supersweet Syrup, Hospitality, Costar), and Wind Rider /
 * Wind Power with Tailwind. Routines whose name starts with g9_asm_ are called from battle scripts (the engine's
 * callasm command; gen9abil_data.CALLASM gives their numbers). */
#include "g9.h"

#define MOVE_TAILWIND 366
#define STATUS3_CHARGED_UP 0x200

extern u8 *gBattleStuff;                        /* 0x0202449C: +0xD8 the Pokemon whose Intimidate is running */
extern const u8 BS_DOWNLOAD[], BS_G9_SYRUP[], BS_G9_HOSPITALITY[], BS_G9_COSTAR[];
extern const u8 BS_G9_TW_RIDER_ATK[], BS_G9_TW_RIDER_DEF[], BS_G9_TW_POWER_ATK[], BS_G9_TW_POWER_DEF[];

static u8 foe_present(u8 bank)
{
    return is_bank_present(bank ^ 1) || (DOUBLE_BATTLE && is_bank_present(bank ^ 3));
}

/* switch_in's part for these; returns TRUE when a script was started */
u8 g9_entry_others(u8 bank)
{
    u8 side = GetBattlerSide(bank);
    u8 ally = bank ^ 2;
    switch (gLastUsedAbility) {
    case ABILITY_SUPERSWEET_SYRUP: {            /* the foes' evasion -1, the first time it comes in */
        u8 bit = 1 << partyIndex(bank);
        if ((G9->syrup[side] & bit) || !foe_present(bank))
            return FALSE;
        G9->syrup[side] |= bit;
        gBattleStuff[0xD8] = bank;
        gBattlerAttacker = bank;
        bs_execute(BS_G9_SYRUP);
        return TRUE;
    }
    case ABILITY_HOSPITALITY:                   /* its partner gets a quarter of its HP back */
        if (DOUBLE_BATTLE && is_bank_present(ally) && gBattleMons[ally].hp != gBattleMons[ally].maxHP) {
            s32 heal = gBattleMons[ally].maxHP / 4;
            gBattleMoveDamage = -(heal ? heal : 1);
            gBattlerAttacker = bank;
            gBattlerTarget = ally;
            bs_execute(BS_G9_HOSPITALITY);
            return TRUE;
        }
        return FALSE;
    case ABILITY_COSTAR:                        /* copies its partner's stat stages */
        if (DOUBLE_BATTLE && is_bank_present(ally)) {
            gBattlerAttacker = bank;
            gBattlerTarget = ally;
            bs_execute(BS_G9_COSTAR);
            return TRUE;
        }
        return FALSE;
    case ABILITY_WIND_RIDER:                    /* a tailwind on its side: Attack +1 */
        if (NB_TAILWIND(side)) {
            STAT_CHANGER = 0x10 + STAT_ATK;
            gBattlerAttacker = bank;
            bs_execute(BS_DOWNLOAD);
            return TRUE;
        }
        return FALSE;
    }
    return FALSE;
}

/* Tailwind's script, once its message is shown: its user, then its partner, answer it. Called again after each
 * answer (the script it pushes returns to this callasm) until no one is left. */
void g9_asm_tailwind(void)
{
    u8 atk = gBattlerAttacker;
    while (G9->tw_step < 2) {
        u8 step = G9->tw_step++;
        u8 b = step ? atk ^ 2 : atk;
        if (step && (!DOUBLE_BATTLE || !is_bank_present(b) || g9_has_mold(b, atk, ABILITY_GOOD_AS_GOLD)))
            continue;
        const u8 *script = NULL;
        if (g9_has(b, ABILITY_WIND_RIDER)) {
            if (step)
                gBattlerTarget = b;
            if (can_change_stat(b, 1, 0x10 + STAT_ATK))
                script = step ? BS_G9_TW_RIDER_DEF : BS_G9_TW_RIDER_ATK;
        } else if (g9_has(b, ABILITY_WIND_POWER) && !(gStatuses3[b] & STATUS3_CHARGED_UP)) {
            gStatuses3[b] |= STATUS3_CHARGED_UP;
            if (step)
                gBattlerTarget = b;
            script = step ? BS_G9_TW_POWER_DEF : BS_G9_TW_POWER_ATK;
        }
        if (script) {
            bs_push(gBattlescriptCurrInstr - 3, script);
            return;
        }
    }
    G9->tw_step = 0;
}
