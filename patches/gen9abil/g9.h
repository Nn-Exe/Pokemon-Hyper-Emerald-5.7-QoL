/* gen9abil: the Gen 9 abilities' ids, gen9abil's own state, and what its files share. */
#ifndef G9_H
#define G9_H
#include "he.h"
#include "strings.h"                /* S_... string ids, made by build.py from gen9abil_data.py */

#define ABILITY_SHARPNESS        0x04F
#define ABILITY_LINGERING_AROMA  0x101
#define ABILITY_SEED_SOWER       0x102
#define ABILITY_THERMAL_EXCHANGE 0x103
#define ABILITY_ANGER_SHELL      0x105
#define ABILITY_PURIFYING_SALT   0x106
#define ABILITY_WELL_BAKED_BODY  0x107
#define ABILITY_WIND_RIDER       0x108
#define ABILITY_GUARD_DOG        0x109
#define ABILITY_ROCKY_PAYLOAD    0x10A
#define ABILITY_WIND_POWER       0x10B
#define ABILITY_ZERO_TO_HERO     0x10C
#define ABILITY_COMMANDER        0x10E
#define ABILITY_ELECTROMORPHOSIS 0x10F
#define ABILITY_PROTOSYNTHESIS   0x110
#define ABILITY_QUARK_DRIVE      0x111
#define ABILITY_GOOD_AS_GOLD     0x113
#define ABILITY_VESSEL_OF_RUIN   0x114
#define ABILITY_SWORD_OF_RUIN    0x115
#define ABILITY_TABLETS_OF_RUIN  0x116
#define ABILITY_BEADS_OF_RUIN    0x117
#define ABILITY_ORICHALCUM_PULSE 0x118
#define ABILITY_HADRON_ENGINE    0x119
#define ABILITY_OPPORTUNIST      0x11A
#define ABILITY_CUD_CHEW         0x11B
#define ABILITY_SUPREME_OVERLORD 0x11C
#define ABILITY_COSTAR           0x11E
#define ABILITY_TOXIC_DEBRIS     0x11F
#define ABILITY_ARMOR_TAIL       0x120
#define ABILITY_EARTH_EATER      0x121
#define ABILITY_MYCELIUM_MIGHT   0x122
#define ABILITY_TOXIC_CHAIN      0x123
#define ABILITY_SUPERSWEET_SYRUP 0x124
#define ABILITY_HOSPITALITY      0x126
#define ABILITY_MINDS_EYE        0x127
#define ABILITY_EMBODY_ASPECT    0x128
#define ABILITY_TERA_SHIFT       0x129
#define ABILITY_TERA_SHELL       0x12A
#define ABILITY_TERAFORM_ZERO    0x12B
#define ABILITY_POISON_PUPPETEER 0x12C
#define IS_GEN9_ABILITY(a) ((a) >= 0x101 && (a) <= 0x12C)

#define ITEM_EFFECT_HEAT_ROCK      0x72
#define ITEM_EFFECT_BOOSTER_ENERGY 0xAB    /* given to item 769 by the patcher */

/* gen9abil's state lives right after the engine's own 0x118 bytes: the patcher makes the battle's allocation
 * bigger, so it is cleared when a battle starts and freed when it ends. G9_STATE_SIZE bytes. */
struct G9State {
    u8 paradox[4];              /* bit 0 on by the sun / the terrain, bit 1 on by a Booster Energy */
    u8 syrup[2];                /* each side: party slots whose Supersweet Syrup has been used this battle */
    u8 tw_step;                 /* g9_asm_tailwind: who answers next */
    u8 opp_active;              /* an Opportunist is copying: its own boosts are not counted */
    u8 cud[4];                  /* Cud Chew: turn ends to go before its Berry is eaten again */
    u16 cud_item[4];            /* ... and that Berry */
    u8 opp[4][8];               /* Opportunist: the stages to copy, by stat */
    u8 shell[4];                /* Tera Shell: 1 it took this hit's types, 2 its message is shown */
    u8 inside[4];               /* Commander: this Tatsugiri is inside its partner */
};
#define G9_STATE_SIZE 0x40
_Static_assert(sizeof(struct G9State) <= G9_STATE_SIZE, "G9State is bigger than its allocation");
#define G9 ((struct G9State *)(gNewBattleStruct + 0x118))
#define PARADOX_ENV 1
#define PARADOX_ITEM 2

/* the battle scripts (scripts.s) */
extern const u8 BS_G9_RUIN[], BS_G9_PROTO_SUN[], BS_G9_QUARK_TERRAIN[], BS_G9_BOOSTER_PROTO[], BS_G9_BOOSTER_QUARK[];
extern const u8 BS_G9_END_PROTO[], BS_G9_END_QUARK[];
extern const u8 BS_G9_ORICHALCUM[], BS_G9_ORICHALCUM_ON[], BS_G9_HADRON[], BS_G9_HADRON_ON[], BS_G9_OVERLORD[];
extern const u8 BS_G9_ANGER_SHELL[], BS_G9_CHARGE[], BS_G9_TOXIC_DEBRIS[];

/* g9.c */
u8 g9_has(u8 bank, u16 ability);
u8 g9_has_mold(u8 def, u8 atk, u16 ability);
u8 g9_field_has(u16 ability);
u8 g9_highest_stat(u8 bank);
u8 g9_paradox_on(u8 bank);
u8 g9_split(u16 move);

/* hit.c */
u8 g9_wind_move(u16 move);
u8 g9_absorb(u8 bank, u16 move);
u8 g9_on_hit(u8 bank, u16 move);
u8 g9_after_hit(u8 bank, u16 move);

/* moves.c */
u8 g9_good_as_gold(u8 bank, u16 move);

/* entry.c */
u8 g9_entry_others(u8 bank);

/* commander.c */
u8 g9_commander_entry(u8 bank);
void g9_commander_switched_in(u8 bank);
void g9_commander_poll(void);

/* state.c */
u8 g9_cud_chew(u8 bank);
void g9_clear_bank(u8 bank);
u8 g9_after_action(void);

#endif
