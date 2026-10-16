-- Run on a build without taken tiles: a save in the crater (the past) on the terrace right below where tiles19's
-- build has the thatched house of Koga's Village, for test_tiles_load.lua to continue from on that build.
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 90, 26, 28},
  {"expect", "as_built", map = 35090, pos = {26, 28}, blocks = {{26, 27, 0x5001}}},
  {"shot", "before"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 35090},
  {"finish"},
}
