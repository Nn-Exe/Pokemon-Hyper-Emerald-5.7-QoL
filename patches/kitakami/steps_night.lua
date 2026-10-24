-- The market at night (2026-10-17, the user: "when at night, the floor is too bright"): the festival's night (Part
-- 1: F_PLAZA, F_TRUTH clear) and Part 2's (F_P2_START), with kit_bgmask tinting BG palette 12 in Mossui; then the
-- Pokemon Center's outside in the day for comparison (no Part flags: the real hour).
STEPS = {
  {"setup", set = {0x43EB, 0x43ED, 0x43F2, 0x43F8, 0x43F9, 0x43FC}},
  {"warp", 35, 106, 23, 40}, {"wait", 90}, {"shot", "festival_night_market"},
  {"warp", 35, 106, 23, 33}, {"wait", 60}, {"shot", "festival_night_gate"},
  {"setup", set = {0x43FE, 0x440B, 0x440C, 0x441B, 0x4337, 0x4346, 0x4347, 0x434A, 0x4352, 0x437D}},
  {"warp", 35, 106, 23, 40}, {"wait", 90}, {"shot", "part2_night_market"},
  {"finish"},
}
