-- The festival's apple stall, bought from one press at a time (the story test's game reset there, 2026-10-16).
STEPS = {
  {"setup", set = {0x43EB, 0x43ED, 0x43F2, 0x43F8, 0x43F9, 0x43FC}},   -- up to the festival (the stalls are shops)
  {"warp", 35, 106, 19, 41},
  {"walk", 19, 40, "on", "to_stall"}, {"face", "UP"},
  {"a"}, {"wait", 90}, {"shot", "greeting"},
  {"press", "A", 90}, {"shot", "mart_open"},
  {"press", "A", 90}, {"shot", "picked"},
  {"press", "A", 90}, {"shot", "quantity"},
  {"press", "A", 30}, {"shot", "confirm_10"}, {"wait", 10}, {"shot", "confirm_20"}, {"wait", 10}, {"shot", "confirm_30"},
  {"wait", 30}, {"shot", "confirm_60"},
  {"press", "A", 20}, {"shot", "after_a_20"}, {"wait", 20}, {"shot", "after_a_40"}, {"wait", 40}, {"shot", "after_a_80"},
  {"press", "A", 60}, {"shot", "more_1"},
  {"press", "B", 60}, {"shot", "more_2"},
  {"press", "B", 60}, {"shot", "more_3"},
  {"press", "B", 60}, {"shot", "more_4"},
  {"finish"},
}
