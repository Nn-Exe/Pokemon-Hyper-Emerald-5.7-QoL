-- Run on the build with the built-in positions: a save made in the crater (the past), mid-story, by Arven's
-- picnic, for test_refresh_load.lua to continue from on a build whose placements.txt moved things there.
local MID = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2}        -- Team Rainbow Rocket beaten; Jacq, Penny, Arven met
STEPS = {
  {"setup", fresh = true, set = MID, stage = 2},
  {"warp", 35, 90, 36, 41},
  {"expect", "as_built", map = 35090, pos = {36, 41}, at = {{19, 37, 43}, {20, 39, 42}, {13, 36, 39}, {14, 46, 38}}},
  {"shot", "before_saving"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"shot", "menu_save"},
  {"press", "A", 60}, {"mash", "save", 35090},
  {"finish"},
}
