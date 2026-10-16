-- On test 15 (the way in still in the Timeless Woods): a save made in Mossdeep City at the top of the stairs down
-- to the strip by the sea, Team Rainbow Rocket beaten. test_mossdeep_old_load.lua continues it on test 16.
STEPS = {
  {"setup", fresh = true, set = {0x41D5}, stage = 0},
  {"warp", 0, 6, 66, 31},
  {"expect", "nothing_of_area_zero_here_yet", map = 6, gone = {30, 31, 32, 33, 34}},
  {"menutop"},
  {"press", "START", 90},
  {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15}, {"press", "DOWN", 15},
  {"press", "A", 60}, {"mash", "save", 6},
  {"finish"},
}
