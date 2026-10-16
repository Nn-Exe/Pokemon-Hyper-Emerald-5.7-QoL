-- How the game hands out sprite palettes while you walk about (the hack: by tag, six slots and a spare): is a
-- slot given back when the last thing of its colour has gone out of sight, or only when the map is left?
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 90, 36, 46}, {"pals", "picnic"},
  {"walk", 22, 46, "on", "west_along_the_lake"}, {"pals", "lake_west"},
  {"walk", 12, 45, "on", "sw"}, {"pals", "sw"},
  {"warp", 35, 90, 12, 36}, {"pals", "den_side"},
  {"walk", 9, 35, "on", "den"}, {"pals", "den"},
  {"warp", 35, 90, 26, 35}, {"pals", "mesa"},
  {"walk", 34, 33, "on", "east_of_mesa"}, {"pals", "east_of_mesa"},
  {"warp", 35, 90, 44, 22}, {"pals", "ne_terrace"},
  {"warp", 35, 91, 36, 46}, {"pals", "future_picnic"},
  {"walk", 30, 26, "act", "north"}, {"pals", "future_north"},
  {"warp", 35, 94, 10, 6}, {"pals", "cavern"},
  {"warp", 35, 101, 8, 15}, {"pals", "vault_door"},
  {"slide", "UP"}, {"pals", "vault_dais"}, {"shot", "vault_dais"},
  {"finish"},
}
