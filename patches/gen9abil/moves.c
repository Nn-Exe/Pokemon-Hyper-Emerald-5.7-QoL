/* gen9abil: the abilities that decide whether a move works at all, or when it goes: Good as Gold, Armor Tail,
 * Mycelium Might, Guard Dog. */
#include "g9.h"

#define TYPE_GHOST 7
#define MOVE_CURSE 174
#define ABILITY_SUCTION_CUPS 0x15
#define ABILITY_STALL 0x64
#define ABILITY_MOLD_BREAKER 0x68
#define ABILITY_QUEENLY_MAJESTY 0xD6
#define STATUS3_PERISH_SONG 0x20

u8 is_of_type(u8 bank, u8 type);
u8 check_ability_with_mold(u8 bank, u8 atk, u16 ability);
u8 get_first_to_strike(u8 bank1, u8 bank2, u8 ignore_priority);
void atkB2_set_perishsong(void);
extern u8 check_field_for_ability(u16 ability, u8 side_to_ignore, u8 mold);
extern u8 gChosenActionByBattler[4];
extern u16 gChosenMoveByBattler[4];
extern const u8 BS_G9_NOT_AFFECTED_ABILITY[];

/* status moves another Pokemon uses on it: the ones Magic Coat reflects, but not the hazards, and these */
static const u16 gold_extra[] = {893, 927, 774, 215, 336, 270, 607, 597, 285, 384, 385, 391, 646, 144, 102, 166,
                                 220, 176, 513, 272, 471, 470, 244, 375, 516, 119, 382, 652, 495, 511, 367, 888,
                                 170, 199, 171, 262, 298, 582, 754, 760, 271, 415, 0xFFFF};
static const u16 gold_not[] = {446, 191, 390, 564, 0xFFFF};       /* Stealth Rock, Spikes, Toxic Spikes, Sticky Web */

/* Good as Gold: called where the engine asks the target's ability about the move (switch_id 3) */
u8 g9_good_as_gold(u8 bank, u16 move)
{
    if (bank == gBattlerAttacker)
        return FALSE;
    if (((gEngineMoves[12 * move + 8] & 0x04) && !find_move_in_table(move, gold_not)) ||
        find_move_in_table(move, gold_extra) || (move == MOVE_CURSE && is_of_type(gBattlerAttacker, TYPE_GHOST))) {
        gBattlescriptCurrInstr = (u8 *)BS_G9_NOT_AFFECTED_ABILITY;
        return TRUE;
    }
    return FALSE;
}

/* Perish Song: Good as Gold is not affected (as Soundproof); counted as already counting down for the command */
void w_atkB2_set_perishsong(void)
{
    u8 marked = 0;
    for (u32 i = 0; i < gBattlersCount; i++) {
        if (!(gStatuses3[i] & STATUS3_PERISH_SONG) && g9_has_mold(i, gBattlerAttacker, ABILITY_GOOD_AS_GOLD)) {
            gStatuses3[i] |= STATUS3_PERISH_SONG;
            marked |= 1 << i;
        }
    }
    atkB2_set_perishsong();
    for (u32 i = 0; i < gBattlersCount; i++)
        if (marked & (1 << i))
            gStatuses3[i] &= ~STATUS3_PERISH_SONG;
}

/* Armor Tail keeps priority moves off its side as Queenly Majesty does: asked about Queenly Majesty, the field
 * check also finds it */
u8 w_check_field_for_ability(u16 ability, u8 side_to_ignore, u8 mold)
{
    u8 r = check_field_for_ability(ability, side_to_ignore, mold);
    if (!r && ability == ABILITY_QUEENLY_MAJESTY)
        r = check_field_for_ability(ABILITY_ARMOR_TAIL, side_to_ignore, mold);
    return r;
}

/* Guard Dog cannot be forced out, as Suction Cups (Roar, Whirlwind, Dragon Tail, Circle Throw, the AI) */
u8 w_check_ability_with_mold(u8 bank, u8 atk, u16 ability)
{
    if (check_ability_with_mold(bank, atk, ability))
        return TRUE;
    if (ability == ABILITY_SUCTION_CUPS && check_ability_with_mold(bank, atk, ABILITY_GUARD_DOG)) {
        gLastUsedAbility = ABILITY_GUARD_DOG;
        return TRUE;
    }
    return FALSE;
}

/* Mycelium Might: its status moves get past the target's ability as Mold Breaker's do. The engine's own test is
 * asked with Mold Breaker in the attacker's place, so the same abilities are passed over. */
u8 w_has_ability_effect_inalternate(u8 bank, u16 ability, u8 atk, u16 move, u8 mold, u8 acid)
{
    if (mold && bank != atk && atk < 4 && gBankAbilities[atk] == ABILITY_MYCELIUM_MIGHT && MOVE_SPLIT(move) == 2) {
        gBankAbilities[atk] = ABILITY_MOLD_BREAKER;
        u8 r = has_ability_effect_inalternate(bank, ability, atk, move, mold, acid);
        gBankAbilities[atk] = ABILITY_MYCELIUM_MIGHT;
        return r;
    }
    return has_ability_effect_inalternate(bank, ability, atk, move, mold, acid);
}

/* and they go last among moves of the same priority, as Stall's do */
static u8 mycelium_status_move(u8 bank)
{
    return gBankAbilities[bank] == ABILITY_MYCELIUM_MIGHT && gChosenActionByBattler[bank] == 0 &&
           MOVE_SPLIT(gChosenMoveByBattler[bank]) == 2 && has_ability_effect(bank, 0);
}

u8 w_get_first_to_strike(u8 bank1, u8 bank2, u8 ignore_priority)
{
    u8 m1 = 0, m2 = 0;
    if (!ignore_priority) {                     /* moves only; both holding it: Speed decides, as without it */
        m1 = mycelium_status_move(bank1);
        m2 = mycelium_status_move(bank2);
        if (m1 && m2)
            m1 = m2 = 0;
    }
    if (m1)
        gBankAbilities[bank1] = ABILITY_STALL;
    if (m2)
        gBankAbilities[bank2] = ABILITY_STALL;
    u8 r = get_first_to_strike(bank1, bank2, ignore_priority);
    if (m1)
        gBankAbilities[bank1] = ABILITY_MYCELIUM_MIGHT;
    if (m2)
        gBankAbilities[bank2] = ABILITY_MYCELIUM_MIGHT;
    return r;
}

/* ------------------------------------------------------------------------- the lists of untouchable abilities */
#include "forbid.h"
u8 findability_in_table(u16 ability, const u16 *table);

/* the engine asks whether an ability is on one of its lists (Skill Swap, Role Play, Trace, Entrainment, Gastro
 * Acid, Mummy...); some of its routines reach a list from a nearby address plus an offset, so the Gen 9 ones are
 * added here, by the list's own address */
u8 w_findability_in_table(u16 ability, const u16 *table)
{
    if (findability_in_table(ability, table))
        return TRUE;
    for (u32 i = 0; i < sizeof(g9_forbid) / sizeof(g9_forbid[0]); i++)
        if (g9_forbid[i].list == table)
            return findability_in_table(ability, g9_forbid[i].extra);
    return FALSE;
}
