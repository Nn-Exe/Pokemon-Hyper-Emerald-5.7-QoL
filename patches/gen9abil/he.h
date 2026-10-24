/* Hyper Emerald v5.7's battle engine, as gen9abil's C code sees it: types, the RAM it reads and writes, and the
 * engine routines it calls. Every address is HE's own, read from the ROM (the engine sits at 0x09D00000; its RAM
 * pointers at 0x02024218 and 0x0203F000..); he.ld gives the routines' addresses to the linker. Field offsets are
 * the ones HE's code uses (each one checked in the routines that read it, see gen9abil_patch.py's EXPECT). */
#ifndef HE_H
#define HE_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed char s8;
typedef signed short s16;
typedef signed int s32;
typedef u8 bool8;
#define TRUE 1
#define FALSE 0
#define NULL ((void *)0)

/* ---------------------------------------------------------------------------------------------- the battlers */
struct BattleMon {                  /* gBattleMons[4], 0x58 each (the game's own layout) */
    u16 species;                    /* +0x00 */
    u16 attack, defense, speed, spAttack, spDefense;   /* +0x02 .. +0x0A */
    u16 moves[4];                   /* +0x0C */
    u32 ivs;                        /* +0x14 */
    s8 statStages[8];               /* +0x18: HP, Atk, Def, Spe, SpA, SpD, Acc, Eva; 6 is neutral */
    u8 ability;                     /* +0x20: the low byte only; the engine's own is gBankAbilities */
    u8 type1, type2, unk23;         /* +0x21 */
    u8 pp[4];                       /* +0x24 */
    u16 hp;                         /* +0x28 */
    u8 level, friendship;           /* +0x2A */
    u16 maxHP;                      /* +0x2C */
    u16 item;                       /* +0x2E */
    u8 nickname[11];                /* +0x30 */
    u8 ppBonuses;                   /* +0x3B */
    u8 otName[8];                   /* +0x3C */
    u32 experience;                 /* +0x44 */
    u32 personality;                /* +0x48 */
    u32 status1;                    /* +0x4C */
    u32 status2;                    /* +0x50 */
    u32 otId;                       /* +0x54 */
};
#define STAT_ATK 1
#define STAT_DEF 2
#define STAT_SPEED 3
#define STAT_SPATK 4
#define STAT_SPDEF 5
#define STAT_ACC 6
#define STAT_EVASION 7

#define STATUS1_SLEEP       0x07
#define STATUS1_POISON      0x08
#define STATUS1_BURN        0x10
#define STATUS1_FREEZE      0x20
#define STATUS1_PARALYSIS   0x40
#define STATUS1_TOXIC       0x80
#define STATUS1_ANY         0xFF
#define STATUS2_CONFUSION   0x07
#define STATUS2_SUBSTITUTE  0x01000000
#define STATUS2_TRANSFORMED 0x00200000

extern struct BattleMon gBattleMons[4];
extern u16 gBankAbilities[4];       /* 0x0203F000: the ability each battler has now, 16 bits */
extern u16 gLastUsedAbility;        /* 0x0203F008 */
extern u8 gBattlersCount;
extern u8 gActiveBattler;
extern u8 gBattlerAttacker, gBattlerTarget, gBattlerFainted, gEffectBattler;
extern u8 gBattlerByTurnOrder[4];
extern u8 gBattlerPartyIndexes[8];  /* u16 each in the game; read them with partyIndex() */
extern u16 gCurrentMove;
extern s32 gBattleMoveDamage;
extern u32 gHitMarker;
extern u8 gMoveResultFlags;
extern u16 gBattleWeather;
extern u8 *gBattlescriptCurrInstr;
extern u8 gBattleCommunication[8];  /* [3] the move effect, [5] the multistring chooser */
extern u8 gBattleTypeFlags[4];
extern u8 gAbsentBattlerFlags;
extern u8 gMultiHitCounter;
extern u8 gBattleTextBuff1[16];
extern u32 gStatuses3[4];
extern u8 gBattleScripting[0x28];   /* +0x17 the battler a script names (BS_SCR_ACTIVE), +0x1A the stat changer */
extern u8 gProtectStructs[4][16];
extern u8 gSpecialStatuses[4][0x14];   /* 0x14 bytes each in this engine; +4 the damage taken this turn */
extern u8 gDisableStructs[4][0x1C];
extern u8 gBattleResults[0x40];     /* +0 our Pokemon fainted, +1 the other side's */
extern u8 *gNewBattleStruct;        /* 0x02024218: the engine's battle state, 0x118 bytes (more: see G9) */
extern u16 gLastUsedItem;
extern u8 gBattleOutcome;

#define SCR_ACTIVE (gBattleScripting[0x17])
#define STAT_CHANGER (gBattleScripting[0x1A])
#define MULTISTRING (gBattleCommunication[5])
#define DOUBLE_BATTLE (gBattleTypeFlags[0] & 1)

static inline u8 partyIndex(u8 b) { return ((u16 *)gBattlerPartyIndexes)[b]; }

/* bit n of the engine's state: byte off, bit pos, width w (a field may run over a byte's end) */
static inline u32 nbs_get(u32 off, u32 pos, u32 w) {
    u8 *p = gNewBattleStruct + off;
    u32 v = p[0] | (pos + w > 8 ? p[1] << 8 : 0);
    return (v >> pos) & ((1u << w) - 1);
}
static inline void nbs_set(u32 off, u32 pos, u32 w, u32 val) {
    u8 *p = gNewBattleStruct + off;
    u32 m = ((1u << w) - 1) << pos;
    u32 v = p[0] | (pos + w > 8 ? p[1] << 8 : 0);
    v = (v & ~m) | ((val << pos) & m);
    p[0] = v;
    if (pos + w > 8)
        p[1] = v >> 8;
}
/* each battler's part: 0x30 bytes from 0 */
#define NB_HEAL_BLOCK(b)        nbs_get(0x30 * (b) + 1, 3, 3)
#define NB_GASTRO_ACID(b)       nbs_get(0x30 * (b) + 2, 6, 1)
#define NB_JUST_SWITCHED_IN(b)  nbs_get(0x30 * (b) + 2, 2, 1)
/* each side's: 9 bytes from 0xC0 */
#define NB_TOXIC_SPIKES(s)      nbs_get(0xC0 + 9 * (s) + 2, 2, 1)
#define NB_TOXIC_SPIKES2(s)     nbs_get(0xC0 + 9 * (s) + 2, 3, 1)
#define NB_TAILWIND(s)          nbs_get(0xC0 + 9 * (s) + 3, 5, 3)
/* the field's, from 0xD4 */
#define NB_GRASSY_TERRAIN()     nbs_get(0xD5, 1, 4)
#define NB_ELECTRIC_TERRAIN()   nbs_get(0xD5, 5, 4)
#define NB_TERRAIN_RECORD()     nbs_get(0xDA, 0, 4)
#define NB_WEATHER_RECORD       (gNewBattleStruct[0xD8])
#define NB_MOVE_EFFECT          (*(u16 *)(gNewBattleStruct + 0xDC))
#define NB_VAR1                 (*(u16 *)(gNewBattleStruct + 0xEA))
#define NB_VAR2                 (*(u16 *)(gNewBattleStruct + 0xEC))
#define NB_SHEER_FORCE_BONUS()  nbs_get(0xF5, 3, 1)

#define WEATHER_SUN_ANY 0x0060          /* harsh sunlight (from a move or an ability), and the extreme sun */
#define SUN_WEATHER (gBattleWeather & 0x860)

/* ------------------------------------------------------------------------------------- the engine's routines */
u8 ability_battle_effects(u8 switch_id, u8 bank, u16 ability_to_check, u8 special, u16 move);
u8 has_ability_effect(u8 bank, u8 mold_breaker);
u8 has_ability_effect_inalternate(u8 bank, u16 ability, u8 atk, u16 move, u8 mold_breaker, u8 acid);
u8 check_ability(u8 bank, u16 ability);
u8 weather_abilities_effect(void);
u8 get_item_effect(u8 bank, u8 check_negating);
u8 is_bank_present(u8 bank);
u8 percent_chance(u8 percent);
u32 get_battle_rng(u32 limit);
void bs_push_current(const void *script);
void bs_execute(const void *script);
void bs_push(const void *ret, const void *script);
u8 can_change_stat(u8 bank, u8 raise, u8 stat_changer);
u8 does_move_make_contact(u16 move, u8 atk);
u8 find_move_in_table(u16 move, const u16 *table);
u16 apply_statboost(u16 stat, u8 stage);
u32 apply_modifier(u16 modifier, u32 value);
u8 get_attacking_move_type(void);
u8 photon_geyser_special(u16 move);
void reset_terrains(u8 *field);
u8 terrains_get_turns(u8 bank);
void RecordAbilityBattle(u8 bank, u16 ability);
u16 get_attack_stat(u16 move, u8 move_type, u8 atk, u8 def);
u16 get_def_stat(u16 move, u8 atk, u8 def);
u16 apply_base_power_modifiers(u16 move, u8 move_type, u8 atk, u8 def, u16 base_power, u8 setflag);
void damage_calc(u16 move, u8 move_type, u8 atk, u8 def, u16 chained_effect, u8 setflag);
u16 get_speed(u8 bank, s8 stat_buffs, u8 check_side);

/* the game's own (far: the linker makes the veneers) */
u8 GetBattlerSide(u8 bank);

/* the engine's battle scripts (he.ld) */
extern const u8 BS_PRINT_DEF_ABILITY[], BS_PRINT_SCR_ACTIVE_ABILITY[], BS_PRINT_ATK_ABILITY[];

/* the engine's move table: 12 bytes a move; +10 0 physical, 1 special, 2 status */
extern const u8 gEngineMoves[];
#define MOVE_SPLIT(m) (gEngineMoves[12 * (m) + 10])

#endif
