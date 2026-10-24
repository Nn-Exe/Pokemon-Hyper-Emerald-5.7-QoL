/* gen9abil: Commander. In a double battle, Tatsugiri goes into its partner Dondozo's mouth: Dondozo's five stats
 * go up two stages, and until Dondozo faints or leaves, Tatsugiri is out of the battle (it does nothing, nothing can
 * hit it) and Dondozo cannot switch out or be forced out.
 *
 * "Out of the battle" is the game's own absent bit (gAbsentBattlerFlags), the one an empty spot in a double battle
 * has: the game then chooses no action for it, moves pass over it or turn to its partner, and the turn's end effects
 * leave it alone. Its picture is hidden the way the engine hides a caught Pokemon. */
#include "g9.h"

#define SPECIES_DONDOZO   1309
#define SPECIES_TATSUGIRI 1310

struct BattleSpriteInfo {           /* the engine's per-battler sprite state, 4 bytes each */
    u16 flags;                      /* bit 0: invisible */
    u16 transformSpecies;
};
struct BattleGraphics { struct BattleSpriteInfo (*info)[4]; };
extern struct BattleGraphics *gBattleSpritesDataPtr;   /* 0x020244D0 */
extern u8 gBattlerSpriteIds[4];                        /* 0x020241E4 */
extern u8 gSprites[][0x44];                            /* 0x02020630: +0x3E bit 2 invisible */
extern const u8 BS_G9_COMMANDER[];

u8 can_switch(u8 bank);
void atk8F_forcerandomswitch(void);

static void sprite_hidden(u8 bank, u8 hidden)
{
    u16 *f = &(*gBattleSpritesDataPtr->info)[bank].flags;
    *f = hidden ? (*f | 1) : (*f & ~1);
    u8 id = gBattlerSpriteIds[bank];
    if (id < 64)
        gSprites[id][0x3E] = hidden ? (gSprites[id][0x3E] | 4) : (gSprites[id][0x3E] & ~4);
}

/* Tatsugiri (tats) goes into its partner */
static void command(u8 tats)
{
    u8 don = tats ^ 2;
    G9->inside[tats] = 1;
    gAbsentBattlerFlags |= 1 << tats;
    sprite_hidden(tats, TRUE);
    gLastUsedAbility = ABILITY_COMMANDER;
    SCR_ACTIVE = gEffectBattler = tats;
    gBattlerTarget = don;
    RecordAbilityBattle(tats, ABILITY_COMMANDER);
    bs_execute(BS_G9_COMMANDER);
}

/* it comes out again: its partner fainted or left */
static void release(u8 tats)
{
    G9->inside[tats] = 0;
    gAbsentBattlerFlags &= ~(1 << tats);
    sprite_hidden(tats, FALSE);
}

static u8 can_command(u8 tats)
{
    u8 don = tats ^ 2;
    return DOUBLE_BATTLE && !G9->inside[tats] && !G9->inside[don] &&
           gBattleMons[tats].hp && gBattleMons[don].hp && is_bank_present(tats) && is_bank_present(don) &&
           gBattleMons[don].species == SPECIES_DONDOZO &&
           gBankAbilities[tats] == ABILITY_COMMANDER && has_ability_effect(tats, 0);
}

/* switch_id 24 for the one coming in: a Tatsugiri beside a Dondozo, or a Dondozo beside a Tatsugiri */
u8 g9_commander_entry(u8 bank)
{
    if (can_command(bank)) {
        command(bank);
        return TRUE;
    }
    if (gBattleMons[bank].species == SPECIES_DONDOZO && can_command(bank ^ 2)) {
        command(bank ^ 2);
        return TRUE;
    }
    return FALSE;
}

/* a Pokemon comes in: if it took the place of a Dondozo with a Tatsugiri inside, Tatsugiri comes out */
void g9_commander_switched_in(u8 bank)
{
    if (G9->inside[bank ^ 2])
        release(bank ^ 2);
    G9->inside[bank] = 0;
}

/* the battler inside the battler bank, + 1, or 0 */
u8 g9_commanded(u8 bank)
{
    return G9->inside[bank ^ 2] && DOUBLE_BATTLE ? (bank ^ 2) + 1 : 0;
}

/* the switch menu, and the engine's own checks: Dondozo with a commander stays */
u8 w_can_switch(u8 bank)
{
    if (g9_commanded(bank))
        return 0;
    return can_switch(bank);
}

/* after an action (switch_id 6): a Tatsugiri whose Dondozo fainted comes out. Not as it faints: the move that
 * knocked Dondozo out may go on to the others (a spread move), and Tatsugiri was not there for it */
void g9_commander_poll(void)
{
    for (u32 b = 0; b < 4; b++)
        if (G9->inside[b] && !gBattleMons[b ^ 2].hp)
            release(b);
}

/* command 0x8F (Roar, Whirlwind...): not on a Dondozo with a commander; its word after the command is where the
 * script goes when the move fails */
void w_atk8F_forcerandomswitch(void)
{
    if (g9_commanded(gBattlerTarget)) {
        const u8 *p = gBattlescriptCurrInstr + 1;
        gBattlescriptCurrInstr = (u8 *)(p[0] | p[1] << 8 | p[2] << 16 | p[3] << 24);
        return;
    }
    atk8F_forcerandomswitch();
}
