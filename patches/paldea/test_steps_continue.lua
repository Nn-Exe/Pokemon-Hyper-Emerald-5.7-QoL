-- Continue from the user's own save (no setup), made in the Timeless Woods at 24,13 next to the hole of test
-- 15 and before (test 11's came from their last save state on test 10, state_to_save.lua). Since test 16 the way
-- in is in Mossdeep City: the save's copy of the woods holds the hole, so the woods are read again (story.FRESH)
-- and are the game's own (their eight objects; nothing of ours). Then to Mossdeep, in through the hole, to Penny.
STEPS = {
  {"shot", "continued"},
  {"expect", "the_woods_as_the_game_has_them", map = 34067, stage = 4, pos = {24, 13}, on = {0x43C2},
   off = {0x43D5}, gone = {9, 10, 11, 12, 13}},
  {"walk", 19, 13, "on", "look_round"}, {"shot", "woods"},
  {"walk", 27, 13, "on", "look_east"}, {"shot", "woods_east"},
  {"warp", 0, 6, 66, 31},
  {"expect", "the_hole_in_mossdeep", map = 6, on = {0x43D4}, here = {31}, gone = {30, 32, 33, 34}},
  {"walk", 68, 33, "on", "to_hole"}, {"face", "UP"}, {"a"}, {"mash", "hole", 35089},
  {"shot", "wall"},
  {"walk", 11, 20, "on", "ladder"}, {"step", "UP", 1}, {"mash", "station1", 35092},
  {"expect", "penny_home", here = {1}},
  {"walk", 8, 5, "on", "to_penny"}, {"face", "UP"}, {"shot", "penny"}, {"a"}, {"mash", "penny_home", 35092},
  {"walk", 9, 8, "on", "s1_exit"}, {"step", "DOWN", 1}, {"mash", "s1_out", 35089},
  {"walk", 14, 14, "on", "back_up"}, {"face", "UP"}, {"a"}, {"mash", "back", 6},
  {"expect", "home_in_mossdeep", map = 6, pos = {68, 33}},
  {"finish"},
}
