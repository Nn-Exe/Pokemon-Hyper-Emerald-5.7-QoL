-- A save in the crater (the past) at the west edge, below the cliff: the place where the map's end shows most.
-- test_edges_load.lua continues from it, on the build it was made on and on a later one. A save keeps the tiles
-- round you as the game held them, the ones past the map's edge too.
local DONE = {0x41D5, 0x43AC, 0x43AD, 0x43B1, 0x43B2, 0x43B3, 0x43B4, 0x43B5, 0x43B6, 0x43B7, 0x43B8, 0x43B9,
              0x43BA, 0x43BB, 0x43BC, 0x43BD, 0x43BE, 0x43C0, 0x43C1}
STEPS = {
  {"setup", fresh = true, set = DONE, stage = 4},
  {"warp", 35, 90, 4, 16},
  {"expect", "at_the_edge", map = 35090, pos = {4, 16}},
  {"shot", "before_saving"},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 35090},
  {"finish"},
}
