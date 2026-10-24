/* gen9abil's link: its code at BASE (build.py writes it in), and the addresses of what it uses in Hyper Emerald
 * (the engine's routines and scripts at 0x09D00000.., the game's RAM). A routine's address has its Thumb bit set.
 * gen9abil_patch.py checks each routine's first bytes before it writes anything (EXPECT). */
OUTPUT_ARCH(arm)
SECTIONS {
    . = BASE;
    .text : { KEEP(*(.text.w_*)) KEEP(*(.text.g9_asm_*)) *(.text*) *(.glue_7*) *(.v4_bx) *(.rodata*) KEEP(*(.rodata.strings)) }
    .data : { *(.data*) *(.bss*) *(COMMON) }
    /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.note*) *(.ARM.exidx*) }
}

/* the game's RAM */
gBattleTypeFlags        = 0x02022FEC;
gBattleChosenBg         = 0x02022FF1;
gBattleTextBuff1        = 0x02022F58;
gActiveBattler          = 0x02024064;
gBattlersCount          = 0x0202406C;
gBattlerPartyIndexes    = 0x0202406E;
gBattlerByTurnOrder     = 0x0202407E;
gBattleMons             = 0x02024084;
gCurrentMove            = 0x020241EA;
gBattleMoveDamage       = 0x020241F0;
gLastUsedItem           = 0x02024208;
gBattlerAttacker        = 0x0202420B;
gBattlerTarget          = 0x0202420C;
gBattlerFainted         = 0x0202420D;
gEffectBattler          = 0x0202420E;
gAbsentBattlerFlags     = 0x02024210;
gMultiHitCounter        = 0x02024212;
gBattlescriptCurrInstr  = 0x02024214;
gNewBattleStruct        = 0x02024218;
gMoveResultFlags        = 0x0202427C;
gHitMarker              = 0x02024280;
gStatuses3              = 0x020242AC;
gDisableStructs         = 0x020242BC;
gBattleCommunication    = 0x02024332;
gBattleOutcome          = 0x0202433A;
gProtectStructs         = 0x0202433C;
gSpecialStatuses        = 0x0202437C;
gBattleWeather          = 0x020243CC;
gBattleWeatherWord      = 0x020243CC;
gWeatherDuration        = 0x020243F8;
gBattleScripting        = 0x02024474;
gBattleStuff            = 0x0202449C;
gBattleResults          = 0x03005D10;
gBankAbilities          = 0x0203F000;
gLastUsedAbility        = 0x0203F008;
gChosenActionByBattler  = 0x0202421C;
gChosenMoveByBattler    = 0x02024274;
gBattleSpritesDataPtr   = 0x020244D0;
gBattlerSpriteIds       = 0x020241E4;
gSprites                = 0x02020630;

/* the routines are in he_syms.s, as Thumb symbols */

/* the battle engine's scripts and data */
BS_PRINT_DEF_ABILITY        = 0x09D06D73;
BS_PRINT_SCR_ACTIVE_ABILITY = 0x09D06D7A;
BS_PRINT_ATK_ABILITY        = 0x09D06D81;
BS_ELECTRIC_SURGE_TAIL      = 0x09D06FE8;   /* Electric Surge's script after its ability line */
BS_DROUGHT_TAIL             = 0x09D07274;   /* Drought's script after its ability line */
gEngineMoves                = 0x09D86419;
gMummyForbidden             = 0x09D79E58;   /* the abilities Mummy cannot replace */
BS_MOVE_EFFECT_CONFUSION    = 0x082DB3E6;   /* the game's: confused by a move's effect */
BS_MOVE_HP_DRAIN            = 0x082DB56E;   /* the game's: a move absorbed for HP (Water Absorb) */
BS_MOVE_USELESS             = 0x082DB591;   /* the game's: ... made the move useless */
BS_NOT_AFFECTED             = 0x082D9F2E;   /* the game's: It doesn't affect ... */
BS_CHANGE_DEF_STAT          = 0x09D06E08;
BS_CHANGE_ATK_STAT_SELFINFLICTED = 0x09D06DD0;
BS_DOWNLOAD                 = 0x09D071ED;   /* an entry ability's own stat change (Download, Intrepid Sword) */
BS_ENDTURN                  = 0x082D8A4E;   /* the game's: the move's end */
BS_DEF_ABILITY_CHANGES_DEF_STAT = 0x09D06DEC;
BS_CHANGE_DEF_STAT_SELFINFLICTED = 0x09D06DF2;
BS_GRASSY_SURGE             = 0x09D0700C;
BS_ATK_ABILITY_STATUS       = 0x09D070FF;
BS_MUMMY                    = 0x09D0711E;
BS_IMMUNE_STAT_RAISE        = 0x09D074E1;   /* a move taken in: a stat up */
BS_IMMUNE                   = 0x09D074F0;   /* a move taken in, the stat already at its top */
