/* gen9abil: the abilities that keep something for later: Cud Chew (a Berry eaten again), Opportunist (the foes'
 * stat boosts, copied), Tera Shell (its type matchups at full HP). */
#include "g9.h"

#define POCKET_BERRIES 4
#define MOVE_FLING 374

u8 get_battle_bank(u8 code);
void atk6A_remove_item(void);
void atk07_final_dmg_calc(void);
u8 change_stats(u8 bank, u8 bits, const void *bs_unable);
u16 type_effectiveness_calc(u16 move, u8 move_type, u8 atk, u8 def, u8 effects_handling);
extern const u8 BS_G9_CUD_CHEW[], BS_G9_OPPORTUNIST[], BS_G9_TERA_SHELL[];

static u8 is_berry(u16 item)
{
    const u8 *items = *(const u8 **)0x080001C8;          /* the item table, from the ROM's header */
    return item && items[44 * item + 0x1A] == POCKET_BERRIES;
}

/* ------------------------------------------------------------------------------------------------ Cud Chew */
/* command 0x6A: a battler's item is used up. A Berry, with Cud Chew: eaten again at the end of the next turn */
void w_atk6A_remove_item(void)
{
    u8 bank = get_battle_bank(gBattlescriptCurrInstr[1]);
    u16 item = gBattleMons[bank].item;
    atk6A_remove_item();
    if (is_berry(item) && gBattleMons[bank].hp && check_ability(bank, ABILITY_CUD_CHEW)) {
        G9->cud[bank] = 2;
        G9->cud_item[bank] = item;
    }
}

/* switch_id 1, the turn's end, for its holder */
u8 g9_cud_chew(u8 bank)
{
    if (!G9->cud[bank] || --G9->cud[bank])
        return FALSE;
    u16 item = G9->cud_item[bank];
    G9->cud_item[bank] = 0;
    if (!is_berry(item) || !gBattleMons[bank].hp || !has_ability_effect(bank, 0))
        return FALSE;
    gLastUsedItem = item;
    gBattlerAttacker = gBattlerTarget = bank;   /* the Berry routine eats for the attacker (the target after Fling) */
    bs_execute(BS_G9_CUD_CHEW);
    return TRUE;
}

/* ---------------------------------------------------------------------------------------------- Opportunist */
/* every real stat change: a boost a foe of an Opportunist gets is counted for it */
u8 w_change_stats(u8 bank, u8 bits, const void *bs_unable)
{
    u8 stat = STAT_CHANGER & 7;
    s8 before = gBattleMons[bank].statStages[stat];
    u8 r = change_stats(bank, bits, bs_unable);
    s8 gain = gBattleMons[bank].statStages[stat] - before;
    if (gain > 0 && (bits & 2) && !G9->opp_active) {
        for (u32 h = 0; h < gBattlersCount; h++) {
            if (GetBattlerSide(h) != GetBattlerSide(bank) && is_bank_present(h) && g9_has(h, ABILITY_OPPORTUNIST)) {
                u8 n = G9->opp[h][stat] + gain;
                G9->opp[h][stat] = n > 6 ? 6 : n;
            }
        }
    }
    return r;
}

/* after an action (switch_id 6): a holder with boosts to copy copies them */
static u8 g9_opportunist_poll(void)
{
    for (u32 i = 0; i < gBattlersCount; i++) {
        u8 h = gBattlerByTurnOrder[i];
        u32 any = 0;
        for (u32 s = 1; s < 8; s++)
            any |= G9->opp[h][s];
        if (!any)
            continue;
        if (!is_bank_present(h) || !g9_has(h, ABILITY_OPPORTUNIST)) {
            for (u32 s = 0; s < 8; s++)
                G9->opp[h][s] = 0;
            continue;
        }
        gBattlerAttacker = h;
        SCR_ACTIVE = h;
        bs_execute(BS_G9_OPPORTUNIST);
        RecordAbilityBattle(h, ABILITY_OPPORTUNIST);
        return TRUE;
    }
    return FALSE;
}

/* the script's loop: the next stat to raise in STAT_CHANGER, or jump to the word after the callasm when done */
void g9_asm_opportunist(void)
{
    u8 h = gBattlerAttacker;
    for (u32 s = 1; s < 8; s++) {
        if (G9->opp[h][s]) {
            STAT_CHANGER = (G9->opp[h][s] << 4) | s;
            G9->opp[h][s] = 0;
            G9->opp_active = 1;
            gBattlescriptCurrInstr += 4;
            return;
        }
    }
    G9->opp_active = 0;
    const u8 *p = gBattlescriptCurrInstr;
    gBattlescriptCurrInstr = (u8 *)(p[0] | p[1] << 8 | p[2] << 16 | p[3] << 24);
}

/* ----------------------------------------------------------------------------------------------- Tera Shell */
/* at full HP every hit is not very effective (x0.5) where it would be neutral or better; all the hits of a move
 * that hits more than once, when the first one found it at full HP */
u16 w_type_effectiveness_calc(u16 move, u8 move_type, u8 atk, u8 def, u8 effects_handling)
{
    u16 r = type_effectiveness_calc(move, move_type, atk, def, effects_handling);
    u8 full = gBattleMons[def].hp == gBattleMons[def].maxHP;
    if (r >= 64 && MOVE_SPLIT(move) != 2 && (full || (G9->shell[def] == 2 && gMultiHitCounter)) &&
        g9_has_mold(def, atk, ABILITY_TERA_SHELL)) {
        r = 32;
        gMoveResultFlags = (gMoveResultFlags & ~0x02) | 0x04;     /* not super effective: not very effective */
        if (effects_handling && !G9->shell[def])
            G9->shell[def] = 1;
    }
    return r;
}

/* command 7, the damage's last adjustments: the message, before the hit is shown (once a move) */
void w_atk07_final_dmg_calc(void)
{
    const u8 *before = gBattlescriptCurrInstr;
    atk07_final_dmg_calc();
    u8 t = gBattlerTarget;
    if (gBattlescriptCurrInstr == before || !G9->shell[t])
        return;                                     /* it waits for the screen, or nothing to say */
    u8 more = gMultiHitCounter > 1;
    if (G9->shell[t] == 1) {
        gLastUsedAbility = ABILITY_TERA_SHELL;
        RecordAbilityBattle(t, ABILITY_TERA_SHELL);
        bs_push_current(BS_G9_TERA_SHELL);
    }
    G9->shell[t] = more ? 2 : 0;
}

/* ------------------------------------------------------------------------------------------------ the rest */
/* a Pokemon comes in: nothing of the one before carries over */
void g9_clear_bank(u8 bank)
{
    G9->paradox[bank] = 0;
    G9->cud[bank] = 0;
    G9->cud_item[bank] = 0;
    G9->shell[bank] = 0;
    for (u32 s = 0; s < 8; s++)
        G9->opp[bank][s] = 0;
    g9_commander_switched_in(bank);
}

/* an action is over (switch_id 6 found nothing of the engine's to do) */
u8 g9_after_action(void)
{
    for (u32 b = 0; b < 4; b++)
        G9->shell[b] = 0;
    g9_commander_poll();
    return g9_opportunist_poll();
}
