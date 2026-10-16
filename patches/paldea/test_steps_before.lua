-- Before Team Rainbow Rocket is beaten: Mossdeep City as the game has it but for Jacq, who stands on his tile from
-- the start since 2026-10-11 (no hole, no students: test_jacq_early.lua has his talk), and the Timeless Woods as
-- the game has them (their own eight objects, Nanu's crystal).
STEPS = {
  {"setup", clear = {0x41D5, 0x43AC}, stage = 0},
  {"warp", 0, 6, 66, 31},
  {"expect", "mossdeep_with_jacq_alone", map = 6, here = {30}, gone = {31, 32, 33, 34}},
  {"shot", "mossdeep_before"},
  {"walk", 68, 33, "on", "on_the_strip"}, {"shot", "the_strip_before"},
  {"warp", 34, 67, 18, 13},
  {"expect", "woods_as_the_game_has_them", map = 34067, gone = {9, 10, 11, 12, 13}},
  {"shot", "woods_before"},
  {"finish"},
}
