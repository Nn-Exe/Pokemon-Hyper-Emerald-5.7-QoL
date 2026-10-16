-- The ground as painted (ground.txt), in the game. Run on the build _testrun/paldea/make_painted.py makes: a
-- boulder painted on the grass at 36,40 of the crater, the boulder at 41,8 (the hanging valley) painted over
-- with grass, a floor tile of the research stations made solid at 6,5. The game must hold those tiles in both
-- times and in every station; walking goes round the new boulder and over the old one's place.
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
local PAINTED = {{36, 40, 0x34E0}, {41, 8, 0x3001}}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 90, 35, 41},
  {"expect", "painted_past", map = 35090, blocks = PAINTED},
  {"shot", "new_boulder"},
  {"walk", 37, 39, "on", "round_the_boulder"}, {"expect", "round", pos = {37, 39}},
  {"walk", 37, 40, "on", "past_the_boulder"}, {"shot", "beside_the_boulder"},
  {"warp", 35, 90, 40, 8},
  {"shot", "old_boulder_gone"},
  {"walk", 41, 8, "on", "where_the_boulder_was"}, {"expect", "on_it", pos = {41, 8}},
  {"warp", 35, 91, 35, 41},
  {"expect", "painted_future", map = 35091, blocks = PAINTED},
  {"shot", "new_boulder_future"},
  {"warp", 35, 93, 8, 6},
  {"expect", "station2", map = 35093, blocks = {{6, 5, 0x3601}}},
  {"walk", 5, 5, "on", "round_the_floor_tile"}, {"expect", "round2", pos = {5, 5}},
  {"warp", 35, 98, 8, 6},
  {"expect", "station4", map = 35098, blocks = {{6, 5, 0x3601}}},
  {"finish"},
}
