/* made by build.py from gen9abil_data.py (FORBIDDEN): the Gen 9 abilities each of the engine's lists of
 * untouchable abilities gets */
static const u16 g9_forbid_0[] = {0x10C, 0x110, 0x111, 0x128, 0x129, 0x12A, 0x12B, 0x12C, 0x10E, 0xFFFF};
static const u16 g9_forbid_1[] = {0x10C, 0x129, 0xFFFF};
static const u16 g9_forbid_2[] = {0x10C, 0x110, 0x111, 0x128, 0x129, 0x12A, 0x12B, 0x12C, 0x10E, 0xFFFF};
static const u16 g9_forbid_3[] = {0x10C, 0x128, 0x129, 0xFFFF};
static const struct { const u16 *list, *extra; } g9_forbid[] = {
    {(const u16 *)0x09D79E36, g9_forbid_0},
    {(const u16 *)0x09D79E1A, g9_forbid_1},
    {(const u16 *)0x09D79E74, g9_forbid_2},
    {(const u16 *)0x09D79E58, g9_forbid_3},
};
