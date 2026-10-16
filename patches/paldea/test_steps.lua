-- The way in, walked: Mossdeep City after Team Rainbow Rocket (the strip of grass by the sea below the Space
-- Center, test 16), Jacq, the hole, the wall, Research Station No. 1, the icy cave (its item, a wild battle), back
-- home. Jacq 30, the hole 31 (Mossdeep's own objects are 1-29).
STEPS = {
  {"setup", fresh = true, set = {0x41D5}, stage = 0},
  {"warp", 0, 6, 66, 31},                                     -- at the top of the stairs down to the strip
  {"expect", "jacq_and_the_hole", map = 6, here = {30, 31}, gone = {32, 33, 34}},
  {"shot", "mossdeep"},
  {"walk", 68, 33, "on", "to_hole1"}, {"face", "UP"}, {"a"}, {"mash", "hole_first", 6},
  {"walk", 70, 32, "act", "to_jacq"}, {"face_to", 70, 32}, {"a"}, {"mash", "jacq", 6},
  {"walk", 68, 33, "on", "to_hole"}, {"face", "UP"}, {"a"}, {"mash", "hole", 35089},
  {"shot", "wall"},
  {"walk", 11, 20, "on", "ladder"},                           -- down to the middle ledge
  {"step", "UP", 1}, {"mash", "station1", 35092},             -- Research Station No. 1
  {"shot", "station1"},
  {"walk", 2, 5, "on", "s1_table"}, {"face", "DOWN"}, {"a"}, {"mash", "s1_note", 35092},
  {"walk", 9, 8, "on", "s1_exit"}, {"step", "DOWN", 1}, {"mash", "s1_out", 35089},
  {"shot", "ledge2"},
  {"walk", 16, 20, "on", "to_ice"}, {"step", "UP", 1}, {"mash", "icecave", 35095},
  {"shot", "icecave"},
  {"walk", 6, 3, "on", "ice_item"}, {"face", "UP"}, {"a"}, {"mash", "nevermelt", 35095},
  {"repel", 0},
  {"walk", 6, 5, "on", "ice_floor"}, {"wild", "wild_ice"},
  {"repel", 250},
  {"walk", 6, 8, "on", "ice_exit"}, {"step", "DOWN", 1}, {"mash", "ice_out", 35089},
  {"shot", "ledge2_again"},
  {"walk", 14, 14, "on", "back_up"}, {"face", "UP"}, {"a"}, {"mash", "back", 6},
  {"expect", "home_in_front_of_the_hole", map = 6, pos = {68, 33}},
  {"shot", "home"},
  {"walk", 70, 32, "act", "to_jacq2"}, {"face_to", 70, 32}, {"a"}, {"mash", "jacq2", 6},
  {"walk", 66, 31, "on", "up_the_stairs"},                    -- the way off the strip is free
  {"finish"},
}
